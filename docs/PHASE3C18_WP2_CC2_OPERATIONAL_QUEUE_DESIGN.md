# Phase3C18 WP2 / CC-2 Operational Queue Design

**Status:** Accepted (design documentation closure)  
**Date:** 2026-07-26  
**Phase:** Phase3C18 — WP2 Command Center send-queue (CC-2)  
**Governance marker:** `adr-c18-sendexecution-v1`  
**Baseline (WP1 closed):** `2b4002e` / remote reconciliation complete  
**Related ADR:** `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md` (**Accepted**)  
**Related C17:** `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` — `SendExecution` Class B Outreach Center queue; CC-2 deferred from `v1.9.10-alpha` / `phase3c17-freeze`

---

## 1. Purpose

Freeze the **CC-2 SendExecution operational queue** design for C18 WP2 before further product expansion (dashboards, analytics, operator actions).

WP2.1 implements **server-side PrimaryFilters only**. Later WP2 packages may compose those filters into Command Center / Outreach Center surfaces without reopening lifecycle ownership.

---

## 2. Decision Summary

| Decision | Choice |
| --- | --- |
| Queue entity | `SendExecution` only |
| Queue mechanism | EspoCRM native **server-side** `PrimaryFilter` classes |
| READY queue | `status = READY` (`c18ReadyToSend` / `C18ReadyToSend`) |
| FAILED queue | `status = FAILED` (`c18FailedSend` / `C18FailedSend`) |
| Client filterList | **UI exposure only** — filter **names**; **no** client-only `where` |
| ACL | Remains active on Record select path (`scopes.acl: true`) |
| Status mutation | **Forbidden** from queues / filters / dashboards |
| Lifecycle owner | Unchanged: `SendExecutionTransitionService` only |
| Navigation | **No** tabList / center IA changes in WP2.1 |
| Dashboard | **Deferred** past WP2.1 |

---

## 3. Context and Constraints

### 3.1 From ADR-C18

- Command Center / Touch Center queues remain **read-only composition**.
- Operators must not patch `SendExecution.status` from list convenience paths.
- All status transitions remain behind `SendExecutionTransitionService`.
- Marker `adr-c18-sendexecution-v1` must stay consistent across design, policy, and tests.

### 3.2 From ADR-C17 (frozen)

- `SendExecution` is Outreach Center **Class B**: filtered list / failure-exception queue; not a new Class A top-level center entry in CC-2.
- C17 deferred **CC-2** as “SendExecution operational workflow / send-queue expansion” outside `1.9.10-alpha`.
- C18 WP2 opens that deferred boundary **without** mutating C17 freeze tags.

### 3.3 From C17 queue filter precedent

CC-1 / center queues established that operational filters must be backed by:

1. `selectDefs.primaryFilterClassNameMap` → PHP `PrimaryFilter`
2. Behavior verified server-side (not client-only filterList `where`)
3. ACL still applied by the Record controller / select pipeline

WP2 adopts the same integrity model. For CC-2, clientDefs **must not** duplicate `where` clauses (stricter than some C17 `filterList` entries that still carry mirrored `where` for parity). UI exposure is name-only; labels may live in i18n `presetFilters`.

---

## 4. Queue Inventory (Approved)

| Queue label | Filter key | Class | Server predicate | Operator intent |
| --- | --- | --- | --- | --- |
| Ready to Send | `c18ReadyToSend` | `C18ReadyToSend` | `status = READY` | Work list of executions prepared for provider send |
| Failed Send | `c18FailedSend` | `C18FailedSend` | `status = FAILED` | Exception / failure triage queue |

### Explicitly out of WP2.1 queue inventory

| Candidate | Disposition |
| --- | --- |
| `CREATED` list | Not an operational send queue; creation/prep owned by transition `CREATED → READY` |
| `SENT` list | Terminal success monitoring — deferred (analytics / later CC expansion) |
| `CANCELLED` list | Terminal abandonment — deferred |
| Combined multi-status filters | Rejected for WP2.1 — keep one status per PrimaryFilter |

---

## 5. Technical Design

### 5.1 Server PrimaryFilters

```text
crm-extension/files/custom/Espo/Modules/Prospecting/
  Classes/Select/SendExecution/PrimaryFilters/
    C18ReadyToSend.php   → where(['status' => 'READY'])
    C18FailedSend.php    → where(['status' => 'FAILED'])
```

- Implement `Espo\Core\Select\Primary\Filter`
- Apply only a status equality predicate
- Do **not** call `saveEntity`, set status, or bypass ACL

### 5.2 selectDefs mapping

```json
{
  "primaryFilterClassNameMap": {
    "c18ReadyToSend": "...\\PrimaryFilters\\C18ReadyToSend",
    "c18FailedSend": "...\\PrimaryFilters\\C18FailedSend"
  }
}
```

### 5.3 clientDefs UI exposure

```json
{
  "filterList": [
    { "name": "c18ReadyToSend" },
    { "name": "c18FailedSend" }
  ]
}
```

**Forbidden in WP2.1 clientDefs filter entries:** `"where": [...]` client-only predicates that could diverge from server PrimaryFilters.

### 5.4 ACL model

| Layer | Rule |
| --- | --- |
| `scopes/SendExecution.json` | `"acl": true` retained |
| Controller | Native `Record` — no skipAccessCheck / ACL bypass |
| Filters | Narrow result sets **after** ACL; never widen access |
| aclDefs / roles | **No redesign** in WP2.1 |

### 5.5 Lifecycle non-interference

Queues are **read paths**. They must not:

- Write `status`, `sentAt`, or `sendRequestId`
- Supply `StatusMutationSaveOption` markers
- Invoke transition / adapter services

Operator prepare / retry / cancel (if productized later) must call `SendExecutionTransitionService` through authorized workflow entry points — not list field edits.

---

## 6. Work Package Split

| WP | Scope | Status |
| --- | --- | --- |
| **WP2.1** | PrimaryFilters + selectDefs + name-only clientDefs (+ i18n labels) | Implementation package |
| **WP2.2+** (deferred) | Command Center / Outreach Center dashlet or governed links composing these filters; analytics; operator action buttons | Not this design’s implementation gate |
| **Not WP2** | Quote / Approval lifecycle, navigation tabList, release artifacts, C17 tag mutation | Forbidden |

---

## 7. Acceptance Criteria (Design)

1. Exactly two SendExecution operational PrimaryFilters: READY and FAILED.
2. Filtering is server-side via `primaryFilterClassNameMap`.
3. clientDefs exposes filter names without client-only `where`.
4. ACL remains active; filters do not bypass access control.
5. No status mutation introduced by queue surfaces.
6. Marker `adr-c18-sendexecution-v1` referenced on ownership-aligned filter contracts / tests.
7. No Quote, Approval, navigation, or artifact changes required to accept this design.

---

## 8. Test Expectations

Contract / behavior tests must assert:

- Filter predicates return the correct single status and exclude all others
- ACL narrowing is preserved (scope acl + no controller bypass + filters non-mutating)
- Governance marker `adr-c18-sendexecution-v1` remains present on the ownership core (and filter contract references)

---

## 9. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-25 | C17 freeze defers CC-2 send-queue expansion |
| 2026-07-26 | ADR-C18 Accepted — queues remain read-only; transition service owns status |
| 2026-07-26 | WP2 CC-2 design accepted: READY + FAILED server PrimaryFilters; no client-only where; no WP2.1 navigation/dashboard mutation |
| 2026-07-26 | This file closes the missing design documentation gate for WP2 |

---

*Documentation only. This file does not modify PHP, metadata, tests, navigation, or release artifacts.*
