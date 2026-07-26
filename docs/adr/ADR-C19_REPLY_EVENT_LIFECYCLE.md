# ADR-C19: ReplyEvent Lifecycle — Provider Fact vs Work Triage

## Status

**Accepted** (WP0 design freeze — implementation gates remain for C19-WP1)

### Acceptance record

- Phase3C19 WP0 governance closure, 2026-07-26
- Independent audit input: `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` (待回复 semantic-gap finding)
- Acceptance documented in `docs/PHASE3C19_WP0_ADR_ACCEPTANCE_REPORT.md`
- Ready for C19-WP1 (Reply Center) implementation

## Date

2026-07-26

## Phase

Phase3C19 — Sales Daily Command Center (reply handling / action-center evolution)

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting module
- Phase3C19 WP0 governance closure

## Related

- C17 Command Center queue `c17AwaitingReply` (`ReplyEvent.replyStatus = SENT`) — read-only, frozen
- C18 SendExecution lifecycle ownership (`docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md`, marker `adr-c18-sendexecution-v1`) — ownership pattern this ADR mirrors
- `EmailLifecycleProjectionService` — Lead projection owner (unchanged by this ADR)
- Connector reply ingestion (`chitu-connector` reply tracking; `BrevoEmailEventSyncService` event mapping)

## Governance Marker

**`adr-c19-replyevent-v1`**

This marker must remain consistent across:

| Surface | Requirement |
| --- | --- |
| This ADR | Declares `adr-c19-replyevent-v1` as the C19 ReplyEvent lifecycle contract id |
| Metadata policy | C19 workflow/policy metadata for ReplyEvent triage must reference the same marker |
| Contract tests | Focused C19 tests must assert the marker string and the invariants in §8 |

No PHP, metadata, or tests are changed by this ADR (WP0 documentation only).

---

## 1. Purpose and Scope

### 1.1 Decision

Split `ReplyEvent` state into two strictly separated lifecycles, and freeze who may write each:

| Field class | Field | Meaning | Writer |
| --- | --- | --- | --- |
| **Provider fact** | `replyStatus` | What the email provider reported (`SENT` / `REPLIED` / `BOUNCED` / `UNSUBSCRIBED`) | **Ingress only** (`PostSyncReplyEvent`), immutable after create |
| **Work lifecycle** | `triageStatus` (new, additive) | Whether a human has handled the event (`OPEN` / `RESOLVED` / `IGNORED`) | **`ReplyTriageService` only** |

### 1.2 Problem being solved (audit evidence)

The C17 queue 待回复 (`c17AwaitingReply`) filters `replyStatus = SENT` — send-confirmation
events ("sent, customer has not replied"). Actual customer replies (`REPLIED`) had **no
queue on any surface**, and `ReplyEvent` had no handled-state, so no event-level work
queue could ever be triaged to empty. This ADR creates the missing work lifecycle
without corrupting the provider fact.

### 1.3 In Scope

- `triageStatus` additive field semantics and option set
- `ReplyTriageService` ownership and allowed triage transitions
- `PostSyncReplyEvent` ingress responsibilities (provider-fact write + triage initialization)
- `c19OpenReplies` server-side PrimaryFilter contract
- Authorization keys and mutation-boundary rules for triage writes

### 1.4 Out of Scope (Deferred)

- ReplyEvent ingestion internals (connector sync, webhook plumbing — C10/C14 boundaries)
- `Lead.peEmailReplyStatus` projection rules (owned by `EmailLifecycleProjectionService`, unchanged)
- Auto-triage / AI classification of replies
- Reply *composition* (sending an answer) — outreach draft pipeline, not this ADR
- Navigation, tabList, dashboard composition mechanics (C19-WP3 concern)
- ACL role redesign (beyond naming triage authorization keys)

---

## 2. Context

`ReplyEvent` is an immutable-per-event audit record ingested from provider webhooks.
`externalEventId` is unique per event; `replyStatus` options are `SENT`, `REPLIED`,
`BOUNCED`, `UNSUBSCRIBED`; `EmailLifecycleProjectionService` projects REPLIED/BOUNCED
onto `Lead.peEmailReplyStatus` (rank-based, idempotent).

C17/C18 established the governance pattern this ADR mirrors:

1. Server-side PrimaryFilters back all operational queues (no client-only `where`).
2. Queue surfaces are read-only composition; lifecycle fields have a **single owning service**.
3. Mutation of lifecycle fields requires an authorized save path guarded by a hook
   (SendExecution precedent: `SendExecutionStatusMutationGuard` + `StatusMutationSaveOption`).
4. A stable governance marker aligns ADR ↔ policy ↔ tests.

---

## 3. Lifecycle Ownership

### 3.1 Provider fact: `replyStatus`

| Rule | Decision |
| --- | --- |
| Writer | **Ingress only** — `PostSyncReplyEvent` (§5) |
| Mutability | **Immutable after create.** No service, UI, API, or formula may rewrite `replyStatus`; a contradicting provider event is a *new* ReplyEvent (new `externalEventId`) |
| Reads | Unrestricted (queues, projections, reporting) |

### 3.2 Work lifecycle: `triageStatus`

Additive field (C19-WP1): enum, `readOnly`, **null by default**.

| Value | Meaning |
| --- | --- |
| *(null)* | Non-actionable event — `replyStatus = SENT` confirmations are not work items |
| `OPEN` | Actionable event awaiting human handling |
| `RESOLVED` | Handled (reply sent, follow-up created, lead advanced — resolution detail is free text at action time) |
| `IGNORED` | Consciously dismissed (reason required) |

**Sole writer: `ReplyTriageService`.** Dashboards, queues, list views, formula, and raw
Record API patches must not write `triageStatus`.

### 3.3 Allowed triage transitions

```text
(null)   → OPEN        (ingress initialization only — never a service action)
OPEN     → RESOLVED    (replyEvent.resolve)
OPEN     → IGNORED     (replyEvent.ignore; reason required)
IGNORED  → OPEN        (replyEvent.reopen — undo a dismissal)
RESOLVED → OPEN        (replyEvent.reopen — e.g. customer replied again on same thread)
```

Terminal rules: none — triage is a work queue, not a legal lifecycle; reopen is legal
so the queue stays honest. Provider fact immutability (§3.1) is unaffected by reopen.

### 3.4 Triage initialization policy (ingress)

| `replyStatus` at ingress | Initial `triageStatus` | Rationale |
| --- | --- | --- |
| `REPLIED` | `OPEN` | Customer replied — highest-value work item |
| `BOUNCED` | `OPEN` | Contact data / deliverability problem needs triage |
| `UNSUBSCRIBED` | `OPEN` | Compliance suppression must be acknowledged |
| `SENT` | *(null)* | Send confirmation — monitoring signal, not work |

---

## 4. ReplyTriageService

New service (C19-WP1), mirroring the `SendExecutionTransitionService` ownership pattern:

| Concern | Rule |
| --- | --- |
| Responsibility | Sole writer of `triageStatus` (+ triage audit fields below) |
| Retry/limit logic | None — triage has no counters |
| Authorization | Action keys checked before write (§6); unauthorized → `Forbidden` |
| Save path | Authorized save option (e.g. `ReplyTriageSaveOption::TRIAGE_MUTATION_AUTHORIZED`) enforced by a BeforeSave guard; writes without the marker throw |
| Audit fields (additive, readOnly) | `triagedAt` (datetime), `triagedBy` (link User), `triageReason` (text, required for `IGNORED`, optional otherwise) |
| Extension point | `afterTriage($event, $from, $to, $action, $reason)` — structured action log, mirrors `afterTransition()` precedent |

**Rejected alternatives:**

- Reusing `EmailLifecycleProjectionService` for triage — projection is machine-owned, idempotent, and rank-based; human triage would corrupt its replay semantics.
- A `handled` boolean — loses who/when/why and cannot express IGNORED vs RESOLVED.
- Status mutation on `replyStatus` to mean "handled" — destroys provider fact; explicitly forbidden (§3.1).

---

## 5. PostSyncReplyEvent Ingress

New API action (C19-WP1): `POST /Prospecting/reply-event/sync` (thin API action class
`Api/PostSyncReplyEvent`, sibling pattern to the Quote workflow action route).

Responsibilities, in order:

1. **Authenticate/authorize** the integration actor (existing Integration Bot precedent; no new role design in this ADR).
2. **Validate + deduplicate** on `externalEventId` (unique index already exists); duplicate delivery → idempotent `200` with the existing record, no second write.
3. **Write provider fact**: create the ReplyEvent with `replyStatus`, `receivedAt`, `sendTraceReference`, `sendExecution`, `lead`, `eventMetadata` exactly as reported by the provider mapping (`email_replied → REPLIED`, etc.).
4. **Initialize triage** per §3.4 (set `triageStatus = OPEN` for actionable statuses through the authorized save path — ingress is the only non-service writer of `triageStatus`, and only at create time).
5. **Never** write Lead projection fields directly — `EmailLifecycleProjectionService` remains the projection owner (existing hook path).

Forbidden at ingress: rewriting `replyStatus` on an existing record, writing
`triageStatus` on an existing record, writing `SendExecution.status`, writing any Lead field.

---

## 6. Authorization Keys

Frozen action names for C19 implementation / authorizer bindings (Quote `WorkflowAuthorizationService` pattern; role bindings land in `app.prospectingWorkflow` metadata policy during C19-WP1):

| Action key | Transition | Reason required |
| --- | --- | --- |
| `replyEvent.resolve` | `OPEN → RESOLVED` | Optional |
| `replyEvent.ignore` | `OPEN → IGNORED` | **Yes** |
| `replyEvent.reopen` | `RESOLVED\|IGNORED → OPEN` | Optional |

Non-negotiables: `scopes.acl: true` stays; Record controller keeps native ACL; queues
never widen access; unauthorized attempts return `403 Forbidden`.

---

## 7. Queue Contract: `c19OpenReplies`

Server-side PrimaryFilter (C19-WP1), same integrity model as C18 WP2:

| Property | Value |
| --- | --- |
| Filter key | `c19OpenReplies` |
| Class | `Espo\Modules\Prospecting\Classes\Select\ReplyEvent\PrimaryFilters\C19OpenReplies` |
| Predicate | `triageStatus = OPEN` (single predicate — one field, per WP2 filter rule) |
| selectDefs | `primaryFilterClassNameMap` entry |
| clientDefs | Name-only `filterList` exposure; **no** client `where` |
| Command Center | Composed read-only in C19-WP3 as queue 已回复待处理 |
| Sort | `receivedAt` desc |

Relationship to existing filters: `c17AwaitingReply` (`replyStatus = SENT`) is **not**
replaced — it remains the "sent, awaiting customer reply" monitoring queue. The C17
queue title 待回复 should be re-titled at composition time (C19-WP3) so the two queues
are distinguishable: 已发送未回复 (monitoring) vs 已回复待处理 (work).

---

## 8. Invariants for Contract Tests (C19-WP1 gates)

1. Marker `adr-c19-replyevent-v1` present in metadata policy and contract tests.
2. `replyStatus` immutable after create (guard rejects rewrite attempts).
3. `triageStatus` writable only via `ReplyTriageService` + authorized save option, or by ingress at create time.
4. Triage transitions limited to the §3.3 matrix; action keys as §6.
5. `IGNORED` requires a reason; unauthorized actor → `Forbidden`, zero writes.
6. `c19OpenReplies` predicate is server-side, single-predicate, non-mutating; ACL narrowing preserved.
7. Ingress duplicate `externalEventId` is idempotent; no Lead-field writes at ingress.
8. No status/triage mutation from any dashboard, dashlet, queue, or list surface.

---

## 9. Consequences

**Positive**

- Customer replies become a triageable work queue without corrupting provider audit facts.
- The C17 semantic gap closes with zero changes to C17 frozen surfaces (re-title is composition, not filter change).
- Ownership pattern is identical to the proven C18 model — one mental model for operators and reviewers.

**Negative / costs**

- Two status fields on one entity require clear operator UX (provider fact label vs triage label in list/detail layouts).
- Reopen legality means triage is never "final"; reporting must treat `RESOLVED` as a work state, not a legal terminal.

**Follow-up (later WPs, not this ADR)**

- C19-WP1: field + service + guard + ingress + filter implementation.
- C19-WP3: Command Center composition (queue surfacing, re-titles).
- Deferred: auto-triage, reply drafting from the triage surface, unsubscribe-suppression automation.

---

## 10. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-26 | Split ReplyEvent state: `replyStatus` = immutable provider fact (ingress-owned); `triageStatus` = work lifecycle (`ReplyTriageService`-owned) |
| 2026-07-26 | Freeze `PostSyncReplyEvent` ingress responsibilities and triage initialization policy |
| 2026-07-26 | Freeze queue contract `c19OpenReplies` (`triageStatus = OPEN`, server-side, single predicate) |
| 2026-07-26 | Freeze governance marker `adr-c19-replyevent-v1` |
| 2026-07-26 | Accept ADR-C19 at WP0 — Ready for C19-WP1 |
