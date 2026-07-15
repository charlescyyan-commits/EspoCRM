# Phase3C14.3.1B-1 SendExecution Bridge Contract Report

## Verdict

PASS

This phase defines a connector-domain contract only. It neither invokes nor
changes the Queue, Worker, ProviderAdapter, Brevo transport, CRM runtime, or
Lead projection.

## Files Changed

| File | Change |
|---|---|
| chitu-connector/chitu_connector/espocrm_sync/send_execution_bridge.py | Added request/result contract, adapter protocol, deterministic in-memory fixture, validation, and stable idempotency function. |
| tests/test_phase3c14_3_1b1_bridge_contract.py | Added contract, isolation, idempotency, security, and terminal-error tests. |
| docs/PHASE3C14_3_1B1_BRIDGE_CONTRACT_REPORT.md | Added this implementation record. |

## Existing SendExecution Field Confirmation

The existing CRM metadata remains unchanged.

| Required concern | Existing field or representation | Result |
|---|---|---|
| Record identity | EspoCRM implicit record id | Present |
| Send request identity | sendRequestId | Present |
| Draft reference | Required draftApproval link; DraftApproval.draftId holds the draft reference | Indirect only |
| Recipient reference | None | Absent |
| Content reference or hash | None on SendExecution; DraftApproval.contentHash exists | Indirect only |
| Lifecycle status | status: CREATED, READY, SENT, FAILED, CANCELLED | Present |
| Timestamps | EspoCRM createdAt and modifiedAt | Present |

No CRM entity, metadata, or database schema field was added. The bridge request
therefore uses connector-side safe references only: recipient_hash and
content_hash.

## Contract Schema

### SendExecutionBridgeRequest

| Field | Rule |
|---|---|
| execution_id | Non-empty CRM SendExecution identity. |
| idempotency_key | SHA-256 of contract version plus execution_id; stable for the same execution. |
| content_hash | Required SHA-256 reference to the approved content snapshot. |
| recipient_hash | Required SHA-256 reference created at authorized ingress; raw recipient is not retained. |
| campaign_reference | Required opaque campaign or reference identifier. |
| created_at | Timezone-aware creation timestamp. |

### SendExecutionBridgeResult

| Field | Rule |
|---|---|
| execution_id | Identity of the enqueued request. |
| provider_attempt_id | Optional opaque provider correlation value. |
| normalized_status | Terminal SENT or FAILED. |
| error_class | Required for FAILED: NETWORK, AUTH, VALIDATION, PROVIDER, or UNKNOWN. |
| error_code | Required safe error identifier for FAILED. |
| occurred_at | Timezone-aware terminal timestamp. |

The result contract preserves the established terminal interpretation:
BREVO_NETWORK_ERROR to RETRYABLE_FAILURE to NETWORK to FAILED. It does not
choose, schedule, or execute a retry.

## Adapter and Fixture Boundary

SendExecutionBridgeAdapter has two operations:

1. enqueue(request) accepts a safe request exactly once by execution identity.
2. record_result(result) accepts one terminal result for a previously accepted request.

InMemorySendExecutionBridgeFixture is a deterministic unit-test double. It
stores objects in process memory only and has no imports from C13 Queue/Worker,
C12 ProviderAdapter, Brevo, HTTP clients, or CRM services.

## Security Review

- The request contains no raw recipient, subject, body, API key, secret, token,
  authorization header, or password field.
- A raw recipient can be supplied only to the transient hashing helper at an
  authorized ingress; it is never stored in the request or fixture.
- Error codes are constrained to non-secret upper-case identifiers, supporting
  BREVO_NETWORK_ERROR.
- No external call, CRM write, background job, queue item, or provider attempt
  can be produced by this contract module.

## Idempotency Design

- Key material is exactly the versioned contract namespace plus execution_id.
- The same execution receives the same opaque SHA-256 key on every construction.
- Distinct execution identities receive distinct keys.
- The in-memory fixture accepts the first request and reports subsequent
  equivalent submissions as duplicates without creating another record.

## Tests and Results

Command:

    C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_phase3c14_3_1b1_bridge_contract

Coverage:

1. Existing CRM field inventory is read and confirms no schema extension.
2. Same SendExecution produces the same key and duplicate fixture receipt.
3. Different SendExecution identities produce different keys.
4. Request payload schema excludes raw recipient and secrets.
5. BREVO_NETWORK_ERROR remains NETWORK and FAILED.
6. Malformed results are rejected.
7. Contract source has no C13, C12, Brevo, or HTTP dependency.

Validation results:

| Command | Result |
|---|---|
| C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_phase3c14_3_1b1_bridge_contract | PASS: 7 tests |
| C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s chitu-connector/tests -p test_*.py | PASS: 270 existing connector tests |

## Compatibility Check

| Frozen area | Touched? | Confirmation |
|---|---|---|
| C10 lifecycle | No | No C10 source or state-machine change. |
| C11 persistence/projection | No | No CRM entity, schema, or projection change. |
| C12 provider contract | No | No ProviderAdapter or Brevo change. |
| C13 Queue/Worker | No | No Queue or Worker change; the fixture is not a queue. |
| C14.2B terminal handling | No | Existing BREVO_NETWORK_ERROR terminal mapping is represented unchanged. |

## Remaining Work

The contract does not create an operational CRM-to-Queue bridge. A later,
separately approved phase must define the CRM-side approved payload source,
bridge adapter implementation, and result write adapter while preserving the
C14.3.1A single-writer projection rule. It must not make Worker write Lead,
EmailEvent, or ReplyEvent directly.
