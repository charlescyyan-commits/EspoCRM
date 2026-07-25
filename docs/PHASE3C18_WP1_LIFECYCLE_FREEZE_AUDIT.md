# Phase3C18 WP1 Lifecycle Ownership Freeze Audit

**Mode:** READ-ONLY FINAL AUDIT  
**Date:** 2026-07-26  
**Baseline HEAD:** `fcfbc551f0b7c1d12fa75d297bc2d92b853bb8cc`  
(`fcfbc55` — `phase3c18: add SendExecution mutation guard`)  
**ADR:** `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md` (**Accepted**)  
**Governance marker:** `adr-c18-sendexecution-v1`

---

## Verdict

**PASS — WP1 lifecycle ownership CLOSED**

SendExecution.status has a single CRM writer (`SendExecutionTransitionService`). Bridge/result adapters no longer mutate status. `SendExecutionStatusMutationGuard` rejects unauthorized lifecycle saves. The ADR transition matrix and governance marker are present in the ownership core and contract tests.

Residual ADR packaging/policy items (marker in metadata policy; additive `sentAt` entityDefs) are **deferred to WP2** and do not reopen dual ownership.

---

## WP1 Commit Chain (post-ADR accept)

| Commit | Message |
| --- | --- |
| `6ee62e0` | `phase3c18: accept SendExecution lifecycle ADR` |
| `33e3502` | `phase3c18: add SendExecution transition service foundation` |
| `5a9287f` | `phase3c18: migrate SendExecution adapters to transition service` |
| `fcfbc55` | `phase3c18: add SendExecution mutation guard` ← **audit baseline** |

---

## 1. SendExecution.status Mutations

**Search surface:** packaged PHP under `crm-extension/files`  
**Patterns:** `$…->set('status'`, `'status' =>` write payloads, `saveEntity` on SendExecution paths

| Writer | Result |
| --- | --- |
| `SendExecutionTransitionService::transition` | **SOLE writer** — `$execution->set('status', $targetStatus)` with `SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED` |
| `SendExecutionBridgeAdapterService` | **No status write** — reads status; hands off via `applyProviderOutcome` |
| `SendExecutionResultAdapterService` | **No status write** — reads status; calls `transitionService->transition` |
| `Controllers/SendExecution` (Record) | **No direct writer** — generic CRUD blocked for status by guard + `readOnly` metadata |
| `EmailLifecycleProjectionHook` / projection service | **Non-writer** — reads status; projects Lead only |
| Quote / Approval / Search* services | Unrelated entity status writes only |

**Conclusion:** Expected met — only `SendExecutionTransitionService` mutates `SendExecution.status`.

---

## 2. Adapter Status Mutation

| Adapter | Status mutation | Evidence |
| --- | --- | --- |
| `SendExecutionBridgeAdapterService` | **None** | Only `$execution->get('status')`; terminal outcomes via `handoffProviderOutcome` → `applyProviderOutcome` |
| `SendExecutionResultAdapterService` | **None** | Sets provider-trace fields only; status via `transitionTo` → `SendExecutionTransitionService` |

Negative contract: `test_adapters_cannot_write_status_directly` (C18 transition suite) asserts absence of `'status' => 'SENT'|'FAILED'` and `set('status'` in both adapters.

Provider-trace fields preserved on adapter paths: `providerName`, `providerMessageId`, `lastError`, `failureCategory`, `retryCount`.

---

## 3. Mutation Guard

**Class:** `Espo\Custom\Hooks\SendExecution\SendExecutionStatusMutationGuard`  
**Order:** `1000` (BeforeSave)

| Protection | Status | Evidence |
| --- | --- | --- |
| `status` | **Protected** | Unauthorized change → Forbidden; create must be `CREATED` |
| `sentAt` | **Protected** | In `LIFECYCLE_FIELDS`; create-time non-empty rejected; transition-owned write only with save marker |
| `sendRequestId` | **Immutable after create** | Explicit `isAttributeChanged('sendRequestId')` → Forbidden (even outside lifecycle path) |
| Terminal SENT / CANCELLED | **Protected** | Distinct Forbidden message for unauthorized terminal lifecycle mutation |
| Provider-trace / normal CRUD | **Preserved** | Guard returns early when lifecycle fields unchanged |

Authorized path: only saves carrying  
`StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true`  
(supplied solely by `SendExecutionTransitionService`).

`entityDefs.SendExecution.fields.status.readOnly = true` (UI/controller friction; hook is the enforcement boundary).

---

## 4. Transition Matrix

Declared in `SendExecutionTransitionService::VALID_TRANSITIONS` — matches ADR §3.2:

| Edge | Present |
| --- | --- |
| `CREATED → READY` | Yes (`sendExecution.prepare`) |
| `READY → SENT` | Yes (`sendExecution.recordSent`) |
| `READY → FAILED` | Yes (`sendExecution.recordFailed`) |
| `READY → CANCELLED` | Yes (`sendExecution.cancel`) |
| `FAILED → READY` | Yes (`sendExecution.retry`; respects `maxRetries`) |
| `FAILED → CANCELLED` | Yes (`sendExecution.cancel`) |

Terminal: `SENT` / `CANCELLED` have empty outgoing sets.

Contract: `test_valid_transition_matrix_matches_adr`, `test_terminal_states_have_no_outgoing_transitions`, `test_invalid_transitions_are_not_declared`.

---

## 5. Governance Marker

| Surface | `adr-c18-sendexecution-v1` |
| --- | --- |
| ADR | Present (Accepted) |
| `SendExecutionTransitionService::GOVERNANCE_MARKER` | Present |
| Guard docblock | Present |
| C18 contract tests | Asserted |
| Metadata policy (`app/prospectingWorkflow.json`) | **Not yet embedded** — deferred WP2 |

No `maxAttempts` field under Prospecting metadata (A1 satisfied).

---

## 6. C18 Focused Tests

Command:

```text
python -m unittest
  crm-extension.tests.test_phase3c18_wp1_sendexecution_transition
  crm-extension.tests.test_phase3c18_wp1_sendexecution_mutation_guard
  -v
```

**Result:** `Ran 20 tests` — **OK** (11 transition + 9 mutation-guard).

---

## ADR §10 Gate Scorecard

| # | Gate | WP1 disposition |
| --- | --- | --- |
| 1 | Marker in metadata policy **and** contract tests | **Partial** — tests + service constant yes; metadata policy deferred WP2 |
| 2 | No `maxAttempts` / duplicate retry schema | **Met** |
| 3 | `FAILED → CANCELLED` under `sendExecution.cancel` | **Met** |
| 4 | Create → `CREATED`; READY only via transition service | **Met** (guard + matrix) |
| 5 | `sentAt` readOnly additive; `sendRequestId` immutable | **Partial** — immutability + transition write + guard yes; `sentAt` entityDefs packaging deferred WP2 |

---

## Explicit Non-Regression

| Area | Touched in WP1 ownership work? |
| --- | --- |
| Quote lifecycle | No |
| Approval lifecycle | No |
| Navigation / Command Center | No |
| ACL architecture / role tables | No (edit-ACL gate on transition service only; no new WAS bindings) |
| Release artifacts / tags | No |

---

## WP2 Handoff (not blockers for ownership freeze)

1. Embed `adr-c18-sendexecution-v1` in metadata workflow policy and bind `sendExecution.*` action roles (reuse `WorkflowAuthorizationService` patterns).
2. Package additive `sentAt` on `SendExecution` entityDefs as `readOnly`, transition-owned.
3. Optional: operator-facing prepare / cancel / retry entry points calling `SendExecutionTransitionService` (queues remain read-only).

---

## Final Statement

C18-WP1 **lifecycle ownership is frozen**: sole status writer, adapters migrated, mutation guard enforced, ADR matrix and marker present in the ownership core, C18 focused tests green. Proceed to WP2 for policy packaging and additive `sentAt` schema — not to reopen status ownership.

*Audit only. No PHP, metadata (beyond this report), tests, artifacts, or commits were modified by this task.*
