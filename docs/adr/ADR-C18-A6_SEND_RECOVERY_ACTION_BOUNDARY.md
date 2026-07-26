# ADR-C18-A6: Send Recovery Action Boundary (Amendment A6 to ADR-C18)

## Status

**Accepted** (WP0 design freeze — implementation gates remain for C19-WP2)

### Acceptance record

- Phase3C19 WP0 governance closure, 2026-07-26
- Supersedes the recovery-model sections of the uncommitted draft audit of
  `docs/PHASE3C19_SEND_RECOVERY_ARCHITECTURE.md` (Ignore-as-marker proposal **rejected**; see §4)
- Acceptance documented in `docs/PHASE3C19_WP0_ADR_ACCEPTANCE_REPORT.md`
- Ready for C19-WP2 (Send Recovery) implementation

## Date

2026-07-26

## Phase

Phase3C19 — Send recovery operator actions (amendment to the C18 SendExecution lifecycle contract)

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting module
- Phase3C19 WP0 governance closure

## Related

- **Base ADR:** `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md` (A1–A5, marker `adr-c18-sendexecution-v1`) — **unchanged**; this amendment adds A6 only
- `SendExecutionTransitionService` — existing sole owner of `SendExecution.status`
- `docs/PHASE3C18_WP2_CC2_OPERATIONAL_QUEUE_DESIGN.md` — read-only queue integrity model
- Quote workflow precedent (`WorkflowAuthorizationService`, `Api/PostQuoteWorkflowAction`)

## Governance Marker

**`adr-c18-sendexecution-v2`**

| Marker | Scope |
| --- | --- |
| `adr-c18-sendexecution-v1` | A1–A5 invariants (status matrix, creation ownership, `maxRetries`, `sentAt`, guard) — **still mandatory, still asserted by existing C18 tests** |
| `adr-c18-sendexecution-v2` | **A6 additions only** — recovery entry-point boundary, sentAt remediation, cancel audit fields, Ignore semantics |

C19 recovery contract tests assert `adr-c18-sendexecution-v2`. Existing v1 assertions
must not be weakened. v2 does not rename, re-own, or reorder anything in v1.

No PHP, metadata, or tests are changed by this ADR (WP0 documentation only).

---

## 1. Purpose

Freeze the **operator recovery boundary** for `FAILED` `SendExecution` records —
Retry, Cancel, Ignore — as an amendment to ADR-C18, so C19-WP2 can implement
entry points without reopening lifecycle ownership.

Core finding that shapes A6: the as-built `SendExecutionTransitionService` **already
contains both recovery edges** (`FAILED → READY` under `sendExecution.retry`,
`FAILED → CANCELLED` under `sendExecution.cancel`) and the `maxRetries` gate. Recovery
is an *entry-point and audit-field* problem, not a state-machine problem.

---

## 2. A6 Decisions (Summary)

| # | Topic | Decision |
| --- | --- | --- |
| A6.1 | Retry / Cancel transitions | **Use existing transitions.** Zero new status edges, zero changes to `VALID_TRANSITIONS` / `TRANSITION_ACTIONS` |
| A6.2 | RecoveryService | **Forbidden.** No new lifecycle owner, no second state machine, no parallel recovery service |
| A6.3 | sentAt remediation | Transition-service-owned, idempotent, evidence-based backfill for historical `SENT` records missing `sentAt` |
| A6.4 | Cancel audit fields | Additive readOnly `cancelledAt`, `cancelledBy`, `cancelReason` — written only on `→ CANCELLED` by the transition service |
| A6.5 | Ignore semantics | **Ignore = `CANCELLED` + `cancelReason`.** Ignore is not a status and not a marker-field set; it invokes the existing `FAILED → CANCELLED` edge |

---

## 3. A6.1 / A6.2 — Existing Transitions Only; No RecoveryService

| Rule | Decision |
| --- | --- |
| Retry | `SendExecutionTransitionService.transition($execution, READY, ACTION_RETRY, $reason)` — existing edge, existing `assertRetryAllowed()` gate (`retryCount < maxRetries`) |
| Cancel | `transition($execution, CANCELLED, ACTION_CANCEL, $reason)` — existing edge; guard already makes `CANCELLED` terminal |
| Entry point | Thin workflow-action API + command delegation (Quote pattern) may **invoke** the transition service; it must not implement transition logic itself |
| **No RecoveryService** | Any class that owns recovery state, duplicates the transition matrix, or writes `status` outside `SendExecutionTransitionService` is **rejected**. The mutation guard (`SendExecutionStatusMutationGuard`) keeps its v1 rules verbatim |

---

## 4. A6.5 — Ignore = CANCELLED + cancelReason

**Decision:** operator "Ignore" of a `FAILED` record executes the existing
`FAILED → CANCELLED` transition under `sendExecution.cancel`, with a **required**
`cancelReason` whose reason code is `IGNORED` (free-text detail optional).

**Rejected alternative (earlier draft):** Ignore as a non-status marker
(`ignoredAt`/`ignoredBy`/`ignoreReason`, reversible Unignore). Rejected because it:

- Forks the truth about a failure into two places (status + marker) and forces every
  queue, report, and reconciliation query to know both
- Requires a fourth mutation whitelist in the guard and a reversible dismissal flow
  whose audit value is lower than its complexity
- Hides permanent abandonment patterns: a record "ignored forever" is operationally
  indistinguishable from Cancel, but reports would still show it as actionable FAILED

**Consequences (accepted deliberately):**

- Ignore is **terminal** — there is no Unignore. Operators must be told this in the UI
  confirmation copy (implementation WP).
- Ignored-for-now-but-maybe-later is expressed by *not acting* (the record stays in the
  FAILED queue), not by a soft-dismiss marker.
- Reporting distinguishes abandonment intent via `cancelReason` (`IGNORED` vs other
  operator reasons), not via a separate status.

---

## 5. A6.4 — Cancel Audit Fields

Additive in C19-WP2 (`entityDefs` extension), all `readOnly`, all written **only** by
`SendExecutionTransitionService` inside the `→ CANCELLED` transition:

| Field | Type | Rule |
| --- | --- | --- |
| `cancelledAt` | datetime, null | Set at transition time; immutable afterwards |
| `cancelledBy` | link → User, null | Actor passed through the authorized entry point |
| `cancelReason` | text, null | **Required** for operator-initiated cancel/ignore; stores reason code (`IGNORED`, `ABANDONED`, …) plus free text |

These mirror the A4 `sentAt` rule: transition-owned, read-only, never editable via
record forms, and their writes ride the existing authorized save option
(`StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED`) — no new save
option is introduced by A6.

---

## 6. A6.3 — sentAt Remediation

A4 introduced `sentAt` additively; historical `SENT` records from before its rollout
may lack it. Remediation rules:

| Rule | Decision |
| --- | --- |
| Owner | `SendExecutionTransitionService` remediation path (same class; a dedicated remediation method, **not** a new service — consistent with A6.2) |
| Writes | Only `sentAt`, only on records whose `status = SENT` and `sentAt IS NULL`; rides the authorized save option |
| Evidence order | (1) provider trace fields (`providerMessageId` timestamp metadata where present), (2) matching `EmailEvent` SENT/DELIVERED `receivedAt` via `sendTraceReference`, (3) `modifiedAt` of the SENT transition as documented fallback |
| Idempotency | Re-running remediation changes nothing on records that already have `sentAt`; one audited log line per backfilled record |
| Forbidden | Guessing `sentAt` from `createdAt`; writing `sentAt` on non-SENT records; remediation from dashboards, queues, CLI convenience scripts outside the owning service |

---

## 7. Entry-Point Authorization (Boundary Record)

Authorization model is part of the action boundary and is recorded here so C19-WP2
does not re-litigate it:

- Entry point follows the **Quote pattern**: `POST /Prospecting/send-execution/:id/workflow/:action`
  → thin API action → command delegation → `WorkflowAuthorizationService` → `SendExecutionTransitionService`.
- Action-level role bindings are decoupled from entity edit ACL (Sales operators hold
  `edit: no` on `SendExecution` today): authorization = entity **read** ACL (queue
  visibility) **plus** action binding from `app.prospectingWorkflow` metadata policy.
- Proposed binding (frozen at implementation time in metadata policy, logged fallback
  per existing pattern): `sendExecution.retry` / `sendExecution.cancel` → Sales Manager,
  Integration Bot, Admin; operator UI offers Ignore only to roles bound for
  `sendExecution.cancel` (Ignore *is* Cancel — §4).
- Unauthorized → `403 Forbidden`, zero writes. UI visibility is never the gate.

---

## 8. Invariants for Contract Tests (C19-WP2 gates)

1. Marker `adr-c18-sendexecution-v2` present in metadata policy and recovery contract tests; v1 marker assertions unchanged.
2. `VALID_TRANSITIONS` byte-identical to the C18 build — zero new edges; no RecoveryService class exists.
3. Retry from `FAILED` respects `retryCount < maxRetries`; at-limit → `BadRequest`, no writes.
4. Ignore produces `status = CANCELLED` + `cancelReason` containing code `IGNORED`; subsequent mutation rejected by the guard (terminal).
5. Cancel/Ignore without reason → rejected; unauthorized actor → `Forbidden`, zero writes.
6. `cancelledAt` / `cancelledBy` / `cancelReason` writable only inside `→ CANCELLED` via the authorized save path.
7. sentAt remediation: writes only `SENT` + `sentAt IS NULL` records; idempotent on re-run; evidence order respected.
8. No recovery action from list, dashlet, queue, or Command Center surfaces (read-only WP2 rule intact).

---

## 9. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-26 | A6.1/A6.2: recovery reuses existing transitions; RecoveryService forbidden |
| 2026-07-26 | A6.5: Ignore = `CANCELLED` + `cancelReason` (marker-field Ignore rejected; terminal consequence accepted) |
| 2026-07-26 | A6.4: additive transition-owned `cancelledAt` / `cancelledBy` / `cancelReason` |
| 2026-07-26 | A6.3: sentAt remediation owned by transition service, evidence-based, idempotent |
| 2026-07-26 | Freeze marker `adr-c18-sendexecution-v2` (v1 retained for A1–A5) |
| 2026-07-26 | Accept A6 at WP0 — Ready for C19-WP2 |
