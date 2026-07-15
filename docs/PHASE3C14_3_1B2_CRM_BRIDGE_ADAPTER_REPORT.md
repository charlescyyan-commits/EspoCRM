# Phase3C14.3.1B-2 CRM Bridge Adapter Report

## Verdict

PASS WITH RISKS

The approved scope is implemented as an explicit connector-side CRM adapter.
It validates CRM-shaped SendExecution and DraftApproval records, validates a
connector-owned approved payload, and submits a C14.3.1B-1 bridge request.
It does not start the C13 Queue or Worker and cannot send mail.

## Files Changed

| File | Change |
|---|---|
| chitu-connector/chitu_connector/espocrm_sync/crm_send_execution_bridge_adapter.py | Added the CRM-shaped read repository protocol, approved payload protocol, adapter, safe outcomes, and in-memory test fixtures. |
| tests/test_phase3c14_3_1b2_crm_bridge_adapter.py | Added B-2 adapter boundary tests. |
| docs/PHASE3C14_3_1B2_ADAPTER_PLAN.md | Added the required pre-implementation plan. |
| docs/PHASE3C14_3_1B2_CRM_BRIDGE_ADAPTER_REPORT.md | Added this implementation and verification report. |

## Adapter Flow

    Explicit connector caller
      -> CRM SendExecution repository read
      -> CRM DraftApproval repository read
      -> ApprovedDeliveryPayloadSource read
      -> validate approval, readiness, draft id, content hash, and content presence
      -> SendExecutionBridgeRequest
      -> SendExecutionBridgeAdapter.enqueue

No PHP hook, Queue implementation, Worker call, Provider call, result callback,
Lead write, EmailEvent write, or ReplyEvent write occurs in this flow.

## Approved Payload Source

ApprovedDeliveryPayloadSource is the connector-owned injection boundary:

| Required value | Adapter source | Handling |
|---|---|---|
| recipient | ApprovedDeliveryPayload.recipient | Required, immediately converted to recipient_hash, never copied into the bridge request. |
| subject | ApprovedDeliveryPayload.subject | Required completeness check only; never copied into the bridge request. |
| body | ApprovedDeliveryPayload.body | Required completeness check only; never copied into the bridge request. |
| content hash | ApprovedDeliveryPayload.content_hash | Must equal DraftApproval.contentHash. |
| campaign reference | ApprovedDeliveryPayload.campaign_reference | Required opaque bridge request value. |
| draft id | ApprovedDeliveryPayload.draft_id | Must equal DraftApproval.draftId. |

The existing C11.4 InMemoryDraftStore was not changed or reused as an
operational source. No durable payload-source implementation exists yet.

## Trigger and Idempotency

The adapter is intentionally called explicitly only after:

    DraftApproval = APPROVED
    SendExecution = READY

It does not convert CRM APPROVED into C10 READY_TO_SEND. It does not add an
EspoCRM after-save hook because an in-process PHP hook cannot safely invoke the
Python process-local bridge or C13 in-memory Queue.

The CRM SendExecution record id is used as the B-1 execution_id. B-1 derives a
stable idempotency key from that identity. Repeated submission builds the same
request and receives the bridge adapter duplicate receipt rather than creating
another bridge submission.

## Failure Behavior

| Condition | Outcome | CRM mutation |
|---|---|---|
| Missing/not-ready execution or missing/non-approved approval | BLOCKED | None |
| Missing recipient, subject, body, campaign reference, or content/hash mismatch | BLOCKED | None |
| Bridge enqueue raises an exception | FAILED_SUBMISSION | None |
| First accepted request | SUBMITTED | None |
| Duplicate accepted request | DUPLICATE | None |

An adapter rejection or bridge exception cannot mark SendExecution SENT and
cannot change Lead status. C14.2B network terminal behavior and existing
failure classification were not changed.

## Tests

| Command | Result |
|---|---|
| C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_phase3c14_3_1b1_bridge_contract tests.test_phase3c14_3_1b2_crm_bridge_adapter | PASS: 14 tests |
| C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe crm-extension/tests/test_extension_skeleton.py | PASS: 38 tests |
| C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s chitu-connector/tests -p test_*.py | PASS: 270 tests |

B-2 coverage includes:

1. APPROVED DraftApproval plus READY SendExecution creates a bridge request.
2. Duplicate trigger uses the same idempotency key and returns duplicate.
3. Missing content blocks enqueue.
4. Missing recipient blocks enqueue.
5. Bridge failure leaves the CRM-shaped SendExecution READY, not SENT.
6. Non-approved and non-ready records are rejected before submission.
7. Adapter imports no Queue, Worker, Provider, Brevo, or HTTP dependency.

## Frozen Contract Verification

| Area | Touched? | Result |
|---|---|---|
| C10 lifecycle | No | No C10 source or state transition changed. |
| C11 persistence / projection | No | No entity, metadata, schema, projection, or Lead writer changed. |
| C12 ProviderAdapter / Brevo | No | No provider or transport source changed. |
| C13 Queue / Worker | No | No Queue or Worker source changed or invoked. |
| C14.2B terminal handling | No | No retry or failure-classification change. |

## Real Send Confirmation

No real send, Brevo call, Provider call, Worker execution, Queue job, CRM
write, Docker action, rebuild, cache clear, or database migration was executed.

## Risks and Next Recommended Phase

The adapter is safe but not operationally deployable yet because the
ApprovedDeliveryPayloadSource has only an in-memory fixture implementation and
the bridge has no approved cross-process runtime invocation owner.

Next, separately approve and implement a durable connector-owned approved
payload source plus an explicit invocation boundary. A later result adapter
must update only CRM SendExecution and leave Lead changes to the existing
EmailLifecycleProjectionService. Do not add an automatic PHP hook, retry, or
Worker-to-CRM direct write.
