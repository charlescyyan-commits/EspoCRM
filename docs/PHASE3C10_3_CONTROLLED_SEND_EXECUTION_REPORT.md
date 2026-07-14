# Phase3C10.3 — Controlled Send Execution Report

## Scope

This phase adds offline orchestration only. `ControlledSendExecutionService`
reads the C10.1 approval state, creates a C10.0-B `SendRequest`, delegates to
the C10.2 `SendProviderAdapter`, and persists a state-only execution result.
It contains no SMTP, provider SDK, API key, email content, CRM write, Lead
update, Opportunity creation, or workflow execution.

## Approval and idempotency controls

Only an approval whose status is exactly `READY_TO_SEND` can create an
execution. Any other status returns `APPROVAL_NOT_READY` before a request is
created or a provider is called.

The service derives `draft_id` from the approval and generates the C10.0-B
idempotency key from that draft, the provided existing `lead_id`,
`send_request_id`, and provider name. Replaying the same request ID returns
the persisted execution and does not call the adapter again. After a `FAILED`
execution, a retry must use a new `send_request_id`; it therefore receives a
new C10.0-B idempotency key. A successfully `SENT` approval cannot create a
second execution.

## State machine

| From | To |
| --- | --- |
| `READY_TO_SEND` | `SUBMITTED` |
| `SUBMITTED` | `PROCESSING` |
| `PROCESSING` | `SENT` when provider result is `ACCEPTED` |
| `PROCESSING` | `FAILED` when provider result is `FAILED` or `REJECTED` |

All execution records are persisted in `InMemorySendExecutionRegistry`.

## Audit trace

Every accepted state transition appends `SendExecutionAuditTrace` with:

- `draft_id`
- `approval_id`
- `send_request_id`
- `send_attempt_id`
- provider
- provider result
- timestamp
- execution state

## Validation

`test_phase3c10_3_controlled_send_execution.py` covers approved execution,
non-approved rejection, duplicate prevention, provider acceptance, provider
failure, and retry using a new request ID. All providers in the tests are
local fake implementations with no external side effects.
