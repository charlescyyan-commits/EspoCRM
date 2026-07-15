# Phase3C14.3.1B Implementation Plan

## Plan Status

BLOCKED PENDING ARCHITECTURE CONFIRMATION

This document is a planning artifact only. No implementation, queue job, worker invocation, CRM write, provider call, or real email was performed.

The requested end-to-end bridge cannot be implemented truthfully within the current constraints because the CRM persistence layer and C13 in-memory execution layer have no shared bridge point or complete approved delivery-content source.

## 1. Current SendExecution Flow

### CRM persistence and projection

```text
DraftApproval after-save
  -> EmailLifecycleProjectionHook
  -> EmailLifecycleProjectionService
  -> Lead peEmailStatus projection only

SendExecution after-save
  -> EmailLifecycleProjectionHook
  -> EmailLifecycleProjectionService
  -> Lead peEmailStatus projection only
```

CRM `DraftApproval` stores a draft ID, status, content hash, Lead link, and trace references. CRM `SendExecution` stores a unique `sendRequestId`, lifecycle status, provider trace fields, retry reservation fields, and links to DraftApproval and Lead.

Neither CRM entity contains the recipient, subject, body, or a connector-side draft snapshot reference that C13 can use to build a `SendExecutionWorkItem`.

### C13 execution flow

```text
InMemorySendExecutionQueue.enqueue(send_execution_id)
  -> QueueItem(QUEUED)
  -> SendExecutionWorker.process(queue_item)
  -> SendExecutionWorkStore.get(send_execution_id)
  -> READY SendExecutionWorkItem
  -> injected C12 ProviderAdapter.send()
  -> WorkExecutionStatus SENT or FAILED
  -> QueueItem COMPLETED or FAILED
```

C13 is an in-memory, process-local reference implementation. It has no CRM repository, consumer process, scheduler, daemon, or shared durable queue.

### Existing C10 flow is separate

`ControlledSendExecutionService` uses C10's `HumanApprovalRegistry`, `SendExecutionRegistry`, and the older `SendProviderAdapter` contract. It directly invokes its provider seam and is not connected to C13's Queue/Worker/C12 `ProviderAdapter` path.

It must remain unchanged.

## 2. Missing Bridge Point

The requested lifecycle needs all of the following, none of which currently exists:

1. **Approved content source:** C13 requires recipient, subject, body, and draft hash. CRM SendExecution has no such fields, and C11.4 DraftStore is in-memory only with no CRM lookup adapter.
2. **Cross-boundary invocation:** EspoCRM PHP hooks cannot enqueue into Python's process-local C13 queue. No bridge API, connector process, or queue transport is present.
3. **Result persistence adapter:** C13's WorkStore only updates an in-memory `SendExecutionWorkItem`; it cannot update the CRM SendExecution entity with SENT/FAILED, message ID, or failure category.
4. **Approval-state alignment:** CRM DraftApproval exposes `APPROVED`; C10's frozen human approval contract authorizes execution only from `READY_TO_SEND`. Treating CRM APPROVED as C10 READY_TO_SEND would change approval semantics unless separately approved.
5. **Provider boundary split:** C10's direct provider path is distinct from the C13/C12 worker provider contract. Reusing or replacing either path would violate the frozen-contract restriction.

## 3. Exact Files to Modify

### No safe implementation file set exists under the current constraints

A production-correct bridge would require a new approved persistence/runtime boundary, which is not authorized by this phase's constraints.

### Conditional minimal connector-side bridge, only after explicit confirmation

If the decision is to implement an **offline/in-process connector bridge only** (not a CRM-triggered bridge and not an operational CRM lifecycle bridge), the minimum proposed files are:

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/send_execution_bridge.py` | New isolated in-memory coordinator that accepts an explicit approved snapshot and explicit C13 work input, enqueues once, invokes a supplied FakeProvider worker only in tests, and returns the result. It would not read/write CRM. |
| `tests/test_phase3c14_3_1b_send_execution_bridge.py` | New offline contract tests for one-time enqueue, duplicate suppression, terminal failure, and no real provider use. |
| `docs/PHASE3C14_3_1B_SEND_EXECUTION_BRIDGE_REPORT.md` | Implementation evidence, limitations, and regression result. |

This conditional option cannot satisfy the requested CRM `DraftApproval -> SendExecution -> provider result mapped back` lifecycle; it would only validate a connector-domain orchestration seam.

Any implementation that does satisfy the full requested lifecycle additionally needs a CRM/connector persistence adapter, an approved content retrieval boundary, and a controlled cross-process invocation model. Those are materially outside the declared constraints.

## 4. State Transition Map

### Requested target map

```text
CRM DraftApproval APPROVED
  -> CRM SendExecution CREATED
  -> CRM SendExecution READY
  -> QueueItem QUEUED
  -> QueueItem CLAIMED
  -> provider result
  -> CRM SendExecution SENT or FAILED
  -> QueueItem COMPLETED or FAILED
  -> existing Lead projection hook
```

### Current supported maps

| Layer | Supported transition |
|---|---|
| CRM DraftApproval | PENDING -> APPROVED or REJECTED |
| CRM SendExecution | CREATED, READY, SENT, FAILED, CANCELLED values are persisted; no CRM-to-C13 transition handler exists |
| C13 queue | QUEUED -> CLAIMED -> COMPLETED or FAILED |
| C13 work store | READY -> SENT or FAILED |
| C11 projection | CRM SendExecution save -> Lead projection only |
| C10 approval | APPROVED -> READY_TO_SEND, but only in the separate frozen in-memory registry |

The missing portions are CRM APPROVED to C10 READY_TO_SEND authority alignment, CRM SendExecution to C13 WorkItem materialization, and C13 result to CRM SendExecution persistence.

## 5. Idempotency Strategy

The existing components provide partial, non-overlapping protections:

| Boundary | Existing protection |
|---|---|
| CRM SendExecution | Unique `sendRequestId` index |
| C13 queue | One QueueItem per `send_execution_id` |
| C13 worker | A terminal/non-QUEUED QueueItem cannot be claimed again |
| C12 adapter | Request/execution identity cache in the adapter instance |
| C10 execution | Registry checks duplicate request and in-progress approval state |

A future bridge must use CRM `sendRequestId` as the stable bridge identity and preserve the C13 `send_execution_id` uniqueness. It must not create a second QueueItem following an ambiguous provider failure.

## 6. Failure Handling

No failure classification or retry behavior will be changed.

| Condition | Existing safe behavior |
|---|---|
| Queue claim/validation failure | Queue FAILED; no provider call |
| Provider failure | C13 WorkItem FAILED and QueueItem FAILED with existing C11.5 category mapping |
| Network/ambiguous failure | Existing `NETWORK` / terminal FAILED behavior; no automatic retry |
| C14.2B-specific ambiguity | Do not re-enqueue or resend automatically; provider receipt remains unproven without separate evidence |

Mapping a terminal worker result back to CRM SendExecution is currently impossible because C13 has no CRM persistence adapter. Adding one requires explicit architectural approval.

## 7. Test Plan

If the blocker is resolved by an approved bridge design, tests must use `FakeProviderAdapter` only and cover:

1. Approved input creates exactly one QueueItem.
2. A duplicate approved input returns the original queue identity and does not enqueue again.
3. Queue validation/failure never marks the work item SENT.
4. Provider failure maps through the existing `FailureCategory` unchanged and leaves QueueItem FAILED.
5. A simulated network/ambiguous result remains terminal FAILED with no re-enqueue or retry, preserving C14.2B behavior.
6. Existing C11 lifecycle projection tests remain unchanged and pass.
7. Existing C10 frozen hash checks, C12 tests, C13 tests, extension tests, and connector tests remain passing.

## Required Decision Before Implementation

Choose one of the following explicitly:

1. **Authorize a new CRM/connector persistence and invocation boundary** sufficient to retrieve approved draft content, enqueue C13 work, and persist results to CRM; or
2. **Authorize only an offline connector-domain bridge**, acknowledging it does not connect CRM DraftApproval/SendExecution to C13 operationally; or
3. **Defer C14.3.1B** until a durable DraftStore/CRM bridge and runtime ownership decision are approved.

Until one option is selected, implementation must not begin.

