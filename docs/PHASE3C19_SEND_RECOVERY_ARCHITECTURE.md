# Phase3C19 Send Recovery Architecture

**Status:** Accepted design (WP2 implementation input; no code in WP0)
**Date:** 2026-07-26 (reconciled at WP0 from the earlier READ-ONLY audit draft)
**Implements:** `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` — governance marker **`adr-c18-sendexecution-v2`**
**Base contract:** `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md` (A1–A5, marker `adr-c18-sendexecution-v1`, unchanged)
**Baseline:** `9bbd44a` / `phase3c18-freeze`
**Scope:** Recovery paths for `FAILED` `SendExecution` records — Retry / Ignore / Cancel.

> **Reconciliation note (WP0):** an earlier draft of this document proposed Ignore as a
> reversible non-status marker (`ignoredAt`/`ignoredBy`/`ignoreReason`). ADR-C18-A6
> **rejected** that model and froze **Ignore = `CANCELLED` + `cancelReason`**.
> This version is the authoritative architecture; the as-built baseline inventory
> (§2) is preserved from the audit.

---

## 1. Objective

Design operator-facing recovery for `SendExecution` records in `FAILED` status:

```
FAILED
 |
 +-- Retry / Re-arm   FAILED → READY      (existing edge, sendExecution.retry)
 +-- Ignore           FAILED → CANCELLED  (existing edge, sendExecution.cancel, cancelReason=IGNORED)
 +-- Cancel           FAILED → CANCELLED  (existing edge, sendExecution.cancel, operator reason)
```

All three actions are **invocations of existing transitions** in
`SendExecutionTransitionService`. C19 adds **zero** status edges and **no
RecoveryService** (ADR-C18-A6 §A6.1/A6.2).

Answers the six audit questions: transition ownership, mutation boundary, required
services, required ACL, UI action constraints, audit logging.

---

## 2. Baseline Inventory (Audited, As-Built)

### 2.1 Status machine — already contains the Retry and Cancel edges

`crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionTransitionService.php`:

```php
public const ACTION_RETRY  = 'sendExecution.retry';
public const ACTION_CANCEL = 'sendExecution.cancel';

private const VALID_TRANSITIONS = [
    STATUS_CREATED   => [READY],
    STATUS_READY     => [SENT, FAILED, CANCELLED],
    STATUS_FAILED    => [READY, CANCELLED],
    STATUS_SENT      => [],          // terminal
    STATUS_CANCELLED => [],          // terminal
];

private const TRANSITION_ACTIONS = [
    ... STATUS_FAILED => [
        STATUS_READY     => ACTION_RETRY,    // FAILED → READY   = Retry / Re-arm
        STATUS_CANCELLED => ACTION_CANCEL,   // FAILED → CANCELLED = Cancel / Ignore
    ],
];
```

**Key finding:** the lifecycle matrix in ADR-C18 (A2) already includes `FAILED → READY`
and `FAILED → CANCELLED`. **C19 needs no new status edges.** Recovery is an
*entry-point, authorization, audit-field, and remediation* problem.

### 2.2 Existing guards around Retry

- `transition()` on `FAILED → READY` runs `assertRetryAllowed()`: `retryCount >= maxRetries` throws `BadRequest('SendExecution retry limit reached for maxRetries.')`.
- `applyProviderOutcome()` (connector path) promotes `CREATED`/`FAILED` to `READY` first with **skipAuthorization** and **skipRetryLimit** — reserved for the integration/bridge actor, not for operators.
- `transition()` writes `sentAt` on `→ SENT`; save uses `StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED`.
- `afterTransition($execution, $fromStatus, $toStatus)` exists as an **empty extension point** — the designated hook for the recovery action log (§4.6).

### 2.3 Mutation boundary — hardened, unchanged by C19

`Espo/Custom/Hooks/SendExecution/SendExecutionStatusMutationGuard.php` (BeforeSave):

- `status` / `sentAt` writes accepted only with the authorized save option.
- `sendRequestId` immutable after creation.
- Creation must start at `CREATED`; `SENT` / `CANCELLED` terminal.

A6 extends the *same* authorized save path to the cancel audit fields (§4.2) — the
guard's status/sentAt/sendRequestId rules are **byte-identical** to the C18 build.

### 2.4 Queue layer — read-only by design

`docs/PHASE3C18_WP2_CC2_OPERATIONAL_QUEUE_DESIGN.md` (Accepted):

- Queues are native server-side PrimaryFilters (`c18ReadyToSend` → `status = READY`, `c18FailedSend` → `status = FAILED`).
- §5.5: queues must not write `status`/`sentAt`/`sendRequestId`, must not supply `StatusMutationSaveOption`, must not invoke transition/adapter services.
- Operator prepare/retry/cancel **"must call `SendExecutionTransitionService` through authorized workflow entry points — not list field edits"**. C19-WP2 builds exactly those entry points.

### 2.5 Authorization precedent — Quote workflow

- `Services/WorkflowAuthorizationService.php`: stable action identifiers, `ACTION_OPTIONS` (`adminOnly`), role bindings from metadata `app.prospectingWorkflow` with logged fallback; checks ACL then action permission.
- API entry precedent: `Api/PostQuoteWorkflowAction.php` + `Resources/routes.json` route `POST /Prospecting/quote/:id/workflow/:action` → thin controller → command service → authorizer → owner transition service.
- `SendExecutionTransitionService::authorize()` today = `Acl::checkEntityEdit` + known action key + admin bypass; its own comment states role bindings land with metadata policy in a later WP — **C19-WP2 is that WP** (ADR-C18-A6 §7).

### 2.6 ACL provisioning reality (the tension WP2 resolves)

`deployment/provisioning/phase3c11_2_provision_persistence_acl.php` applies to
`DraftApproval`, `SendExecution`, `ReplyEvent`:

| Role | create | read | edit | delete |
| --- | --- | --- | --- | --- |
| Admin | yes | all | all | all |
| Integration Bot | yes | all | all | no |
| Sales Manager | no | all | **no** | no |
| Sales User | no | all | **no** | no |

With the current edit-gate, only Admin and Integration Bot could execute
`sendExecution.retry` / `sendExecution.cancel`. A6 §7 freezes the resolution: action
bindings decoupled from edit ACL (read ACL + `app.prospectingWorkflow` binding).

### 2.7 Audit / stream state

- `entityDefs/SendExecution.json`: **no `audited`, no `stream`** — audit trail and stream both off.
- `clientDefs/SendExecution.json`: controller/filterList/iconClass only — no custom UI actions yet.
- `scopes/SendExecution.json`: `entity`, `object`, `tab`, `acl: true`.

---

## 3. Recovery Model (A6 — frozen)

### 3.1 Action inventory

| Action | Stable identifier | Status effect | Terminal? | Retry-limit gate | Reason required? |
| --- | --- | --- | --- | --- | --- |
| **Retry / Re-arm** | `sendExecution.retry` | `FAILED → READY` (existing edge) | No | Yes — `assertRetryAllowed` (`retryCount < maxRetries`) | Optional (free text) |
| **Ignore** | `sendExecution.cancel` | `FAILED → CANCELLED` (existing edge) with `cancelReason` code **`IGNORED`** | **Yes** — CANCELLED is terminal | No | **Yes** |
| **Cancel** | `sendExecution.cancel` | `FAILED → CANCELLED` (existing edge), operator reason code (e.g. `ABANDONED`) | Yes | No | **Yes** |

### 3.2 Retry / Re-arm — reuse, don't rebuild

- Calls `SendExecutionTransitionService::transition($execution, READY, ACTION_RETRY, $reason)` — nothing new in the service.
- Record re-enters the `c18ReadyToSend` queue; `retryCount` increments per existing behavior; `maxRetries` gate already enforced.
- **Rejected:** connector-driven auto-retry via `applyProviderOutcome` (skipRetryLimit) — stays bridge policy, not operator recovery.

### 3.3 Ignore = CANCELLED + cancelReason (A6.5)

- Operator "Ignore" executes `transition($execution, CANCELLED, ACTION_CANCEL, $reason)` with reason code `IGNORED`.
- **No new status, no marker fields, no Unignore.** The earlier draft's reversible marker model was rejected at WP0 — see ADR-C18-A6 §4 for rationale (single source of truth; no guard fork; honest abandonment reporting).
- Consequence communicated in UI copy: **Ignore is permanent.** "Not now, maybe later" is expressed by leaving the record in the FAILED queue, not by a soft dismiss.
- Reporting distinguishes intent via `cancelReason` (`IGNORED` vs `ABANDONED` vs …), not via status.

### 3.4 Cancel — terminal, existing edge

- Same edge as Ignore; reason code differentiates deliberate abandonment from dismissal.
- Guard already blocks any further mutation from `CANCELLED` — no new protection needed.
- READY-side cancellation exists in the matrix but is **not exposed** in C19 operator UI (separate product decision).

---

## 4. The Six Audit Questions — Answers (A6-aligned)

### 4.1 Transition ownership

**Unchanged: `SendExecutionTransitionService` is the sole owner of `status`.** C19 adds
zero status edges; recovery actions are invocations through a new authorized entry
point. **No RecoveryService** — no new lifecycle owner, no second state machine
(ADR-C18-A6 §A6.2).

### 4.2 Mutation boundary

Preserved verbatim, plus cancel audit fields riding the **existing** authorized save
option (no new save option):

| Boundary rule | C19 impact |
| --- | --- |
| `status` / `sentAt` only via authorized save option | Unchanged — retry/cancel go through `transition()` |
| `sendRequestId` immutable | Unchanged |
| Create starts at `CREATED`; `SENT`/`CANCELLED` terminal | Unchanged — Ignore/Cancel consume the terminal guarantee |
| `cancelledAt` / `cancelledBy` / `cancelReason` (additive, readOnly) | **New fields, old rule**: written only inside `→ CANCELLED` by the transition service; guard treats them as transition-owned alongside `sentAt` |
| Queues/filters/dashboards read-only | Unchanged — WP2 §5.5 not reopened |

Explicitly forbidden in C19 (WP2 §5.5 list plus): no raw `status` saveEntity from
API/UI/CLI convenience paths; no `nextRetryAt`/`retryCount` edits from UI; no list-view
inline editing of recovery-related fields.

### 4.3 Required services

All new components mirror the Quote workflow precedent (thin API action → command
delegation → authorizer → owner service). **None of them owns transitions.**

| Component | Type | Responsibility |
| --- | --- | --- |
| `Api/PostSendExecutionWorkflowAction.php` | New API action | Route `POST /Prospecting/send-execution/:id/workflow/:action` (registered in `Resources/routes.json`, sibling to the quote route). Extracts `id`, `action`, `reason`; delegates. Mirror of `PostQuoteWorkflowAction`. |
| Command delegation (e.g. `Services/SendExecutionWorkflowActionService.php`) | New command service | Loads entity, resolves action alias, calls authorizer, then invokes `TransitionService.transition(...)` for retry/cancel/ignore. **Contains no transition logic.** Returns small DTO (id, status, retryCount, cancelledAt) for UI refresh. Naming must not imply a lifecycle owner — it is an entry-point adapter, not a "RecoveryService" (A6.2). |
| `WorkflowAuthorizationService` extension | Extend existing | Register `sendExecution.retry` / `sendExecution.cancel` bindings in `app.prospectingWorkflow` (Ignore shares `sendExecution.cancel` — §3.3). |
| `SendExecutionTransitionService` | **Unchanged** for transitions | Gains only: (a) cancel audit field writes inside `→ CANCELLED`; (b) the sentAt remediation method (§4.3.1). |
| Mutation guard | Unchanged rules | Cancel audit fields whitelisted on the **same** authorized save option as `sentAt`. |

#### 4.3.1 sentAt remediation (A6.3)

- **Owner:** a dedicated remediation method on `SendExecutionTransitionService` (same class — no new service).
- **Target set:** `status = SENT AND sentAt IS NULL` only.
- **Evidence order:** (1) provider trace timestamp metadata, (2) matching `EmailEvent` SENT/DELIVERED `receivedAt` via `sendTraceReference`, (3) `modifiedAt` fallback (logged as fallback).
- **Idempotent:** records with `sentAt` are never rewritten; one audited log line per backfilled record.
- **Forbidden:** guessing from `createdAt`; writing non-SENT records; remediation outside the owning service.

### 4.4 Required ACL

Frozen by ADR-C18-A6 §7 (Option B of the earlier audit — **adopted**):

- Authorization = entity **read** ACL (queue visibility) + action binding from `app.prospectingWorkflow` — decoupled from the edit-ACL gate that sales roles fail today.
- Proposed binding matrix (frozen in WP2 metadata policy):

| Action | Sales User | Sales Manager | Integration Bot | Admin |
| --- | --- | --- | --- | --- |
| `sendExecution.retry` | — | ✅ | ✅ | ✅ (admin bypass) |
| `sendExecution.cancel` (incl. Ignore) | — | ✅ | ✅ | ✅ |

- Ignore/Cancel are manager-gated because both are **terminal** under A6.5 — the earlier
  draft's low-risk-reversible justification for Sales User no longer applies.
- Non-negotiables: `scopes.acl: true` stays; Record controller keeps native ACL; queues
  never widen access; unauthorized → `403 Forbidden`, never silent success.

### 4.5 UI action constraints

- **Placement: detail-view action menu only** (SendExecution record detail dropdown), modeled on the Quote command flow (button → POST workflow route → refresh). **No list-row buttons, no inline edits, no dashlet actions.**
- Visibility rules (client convenience; server is the real gate):
  - `Retry` — `status = FAILED` **and** `retryCount < maxRetries`.
  - `Cancel` / `Ignore` — `status = FAILED` only; not from `SENT`/`CANCELLED`.
  - Confirmation copy for Ignore must state **permanence** (terminal, §3.3); reason prompt required for Cancel and Ignore; optional for Retry.
- No retry/cancel/status controls on dashlets, queue lists, or Command Center surfaces — verified by the existing mutation-boundary smoke checklist.

### 4.6 Audit logging requirements

1. **Cancel audit fields (A6.4):** `cancelledAt` / `cancelledBy` / `cancelReason` — the audit record for every abandonment; reason mandatory so the row answers "why".
2. **`audited: true` on SendExecution entityDefs** (additive WP2 metadata) — Espo-native field history for `status`, `retryCount`, cancel fields. `stream` optional.
3. **Structured action log via `afterTransition()`** — the existing empty extension point: log `{entityId, from, to, action, actor, reason, retryCount}` per recovery action.
4. **sentAt remediation log** — one line per backfilled record including the evidence source used (§4.3.1).

Test expectations (WP2 contract suite):

- Retry from FAILED under limit → `READY`, log row present; at limit → `BadRequest`, zero writes.
- Ignore → `CANCELLED` + `cancelReason` code `IGNORED`; subsequent mutation rejected by guard.
- Cancel/Ignore without reason → rejected; unauthorized actor → `Forbidden`, zero writes.
- sentAt remediation writes only `SENT`+NULL records; idempotent on re-run; evidence order respected.
- Markers `adr-c18-sendexecution-v2` (recovery suite) and `adr-c18-sendexecution-v1` (existing suite) both asserted.

---

## 5. Decision Summary

| # | Question | Decision |
| --- | --- | --- |
| 1 | Transition ownership | `SendExecutionTransitionService` only; zero new status edges |
| 2 | Mutation boundary | Guard rules unchanged; cancel audit fields ride the existing authorized save option |
| 3 | Required services | Quote-pattern API action + command delegation + authorizer extension; **no RecoveryService**; transition service gains only cancel-field writes + sentAt remediation |
| 4 | Required ACL | Read ACL + `app.prospectingWorkflow` action bindings; Retry/Cancel/Ignore → Sales Manager + Integration Bot + Admin |
| 5 | UI action constraints | Detail-view menu only; reason required for Cancel/Ignore; Ignore confirmation states permanence; server is the only gate |
| 6 | Audit logging | Cancel audit fields + `audited: true` + `afterTransition()` log + remediation log |

---

## 6. Explicitly Out of Scope for C19-WP2

- Auto-retry / backoff scheduling via `nextRetryAt` (bridge policy, separate WP).
- READY-side cancellation UI (edge exists; product decision deferred).
- Connector / `applyProviderOutcome` changes.
- Navigation, tabList, dashboard composition (WP3), Quote/Approval workflows, ACL redesign beyond the action-binding decision.
- Any change to WP2 queue PrimaryFilters (`c18ReadyToSend` / `c18FailedSend` stay byte-identical — Ignore needs no filter change because ignored records become `CANCELLED` and simply leave the FAILED queue).

## 7. Open Questions for the Implementation WP

1. `app.prospectingWorkflow` metadata version bump and fallback-role behavior for the recovery actions (log-and-fallback pattern already established).
2. Reason-code enum set for `cancelReason` (`IGNORED`, `ABANDONED`, `DUPLICATE`, `OTHER` — frozen in WP2 metadata).
3. Stream enablement — audit-only vs audit+feed.

---

*Architecture design implementing ADR-C18-A6. WP0 modifies no PHP, metadata, tests, navigation, ACL configuration, or release artifacts.*
