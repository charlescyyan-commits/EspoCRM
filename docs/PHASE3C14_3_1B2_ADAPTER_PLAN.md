# Phase3C14.3.1B-2 CRM Bridge Adapter Plan

## Plan Status

IMPLEMENTATION APPROVED AS A CONTRACT-LEVEL CRM-SIDE ADAPTER ONLY.

The adapter will read CRM-shaped execution and approval records through an
injected repository seam, validate an injected approved delivery payload, and
submit only a C14.3.1B-1 bridge request. It will not add a PHP hook, invoke a
Queue implementation, call a Worker, or send mail.

## 1. Current SendExecution Lifecycle

CRM SendExecution already has:

- implicit record id and unique sendRequestId;
- status values CREATED, READY, SENT, FAILED, and CANCELLED;
- required DraftApproval and Lead links;
- provider trace and retry-reservation fields.

DraftApproval has draftId, status, and contentHash. It does not hold delivery
content. CRM has no recipient, subject, or body fields for this lifecycle.

The adapter entry condition is therefore:

    DraftApproval.status = APPROVED
    SendExecution.status = READY
    DraftApproval.draftId/contentHash = approved connector payload identity

CRM APPROVED is not translated to C10 READY_TO_SEND. CRM READY remains the
explicit bridge-entry condition.

## 2. Approved Payload Source

The approved delivery source will be an injected connector-side
ApprovedDeliveryPayloadSource protocol. Its payload contains:

| Value | Source and validation |
|---|---|
| recipient | Connector-side approved payload; must be non-empty and is immediately hashed for the B-1 request. |
| subject | Connector-side approved payload; must be non-empty, but is not copied to the B-1 request. |
| body | Connector-side approved payload; must be non-empty, but is not copied to the B-1 request. |
| content hash | Connector-side payload content_hash; must equal CRM DraftApproval.contentHash. |
| campaign reference | Connector-side approved payload; required opaque reference. |
| draft id | Connector-side payload; must equal CRM DraftApproval.draftId. |

This phase creates no durable payload store. The current C11.4 InMemoryDraftStore
is not a runtime source. Production binding of this protocol remains a later
explicitly approved prerequisite.

## 3. Bridge Trigger Point

The trigger is an explicit connector-side call after a CRM SendExecution record
already exists in READY state and its related DraftApproval is APPROVED.

No EspoCRM PHP after-save hook is introduced because it cannot safely invoke
the Python process-local bridge or C13 in-memory Queue. Triggering at
DraftApproval.APPROVED would also conflate that CRM decision with C10
READY_TO_SEND. Triggering after explicit SendExecution.READY verification
keeps the state boundary intact.

## 4. Idempotency Enforcement

- The CRM SendExecution id is the B-1 execution_id.
- B-1 derives the stable idempotency key from that id.
- Repeating the same adapter call rebuilds the same request and delegates
  duplicate recognition to SendExecutionBridgeAdapter.enqueue.
- The adapter keeps no queue state and cannot create a second Queue item.

## 5. Failure Behavior

| Condition | Adapter outcome |
|---|---|
| Missing CRM record, approval, or payload | BLOCKED; no bridge submission. |
| Approval not APPROVED or execution not READY | BLOCKED; no bridge submission. |
| Missing recipient, subject, body, campaign reference, or hash mismatch | BLOCKED; no bridge submission. |
| Bridge adapter exception | FAILED_SUBMISSION; no bridge submission outcome is claimed. |
| Accepted bridge request | SUBMITTED or DUPLICATE only; no CRM status mutation. |

In every rejection or bridge-failure case the adapter does not mark
SendExecution SENT, does not write a Lead field, and does not create or update
EmailEvent or ReplyEvent.

## Exact Files

| File | Change |
|---|---|
| chitu-connector/chitu_connector/espocrm_sync/crm_send_execution_bridge_adapter.py | New CRM-shaped repository and approved-payload protocols plus the contract-only adapter. |
| tests/test_phase3c14_3_1b2_crm_bridge_adapter.py | New unit tests using in-memory fixture implementations only. |
| docs/PHASE3C14_3_1B2_ADAPTER_PLAN.md | This plan. |
| docs/PHASE3C14_3_1B2_CRM_BRIDGE_ADAPTER_REPORT.md | Implementation evidence and verification. |

No Worker, Queue, Provider, Brevo, CRM entity metadata, PHP hook, database
schema, or production runtime file will be modified.

## Test Plan

1. APPROVED DraftApproval plus READY SendExecution submits one bridge request.
2. Duplicate trigger returns the same idempotency key and duplicate result.
3. Missing content blocks submission.
4. Missing recipient blocks submission.
5. Bridge failure never changes the CRM-shaped execution record to SENT.
6. Existing lifecycle projection and connector regression tests remain passing.
