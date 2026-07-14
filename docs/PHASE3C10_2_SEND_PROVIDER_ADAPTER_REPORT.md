# Phase3C10.2 — Send Provider Adapter Boundary Report

## Scope

This phase introduces a provider-agnostic, offline adapter boundary after the
C10.1 `READY_TO_SEND` state. It does not implement delivery. No SMTP, email
provider, credential, API key, CRM write, Lead update, Opportunity creation,
or workflow execution exists in this implementation.

## Contract

`SendProvider` is a protocol with a declared `provider_name` and a `submit`
method that receives a validated C10.0-B `SendRequest` and its reserved
`SendAttempt`. It returns `SendProviderResult`:

| Field | Source / purpose |
| --- | --- |
| `provider_name` | Declared provider identity; must match the request |
| `send_attempt_id` | Provider-owned trace identity |
| `idempotency_key` | Exact echo of C10.0-B request key |
| `request_version` | Exact echo of C10.0-B request version |
| `status` | `ACCEPTED`, `FAILED`, or `REJECTED` |
| `reason_code` | Optional stable provider-neutral reason |

The adapter returns `SendProviderAttemptResult`, which contains the reserved
C10.0-B `SendAttempt` and the unmodified provider result trace.

## C10.0-B integration and duplicate handling

`SendProviderAdapter.submit` calls `validate_send_request` and therefore
requires both `send_request_id` and `idempotency_key`, together with the full
C10.0-B request/version contract. Invalid requests are rejected before the
provider is called.

For a repeated idempotency key submitted through the same adapter instance,
the adapter returns the first `SendProviderAttemptResult` and does not call the
provider again. A provider-unavailable condition becomes a terminal `FAILED`
trace with reason `PROVIDER_UNAVAILABLE`; it still performs no delivery.

## Approval boundary

C10.2 does not approve a draft and does not inspect or mutate C10.1 approval
records. A future orchestration layer must require `READY_TO_SEND` before it
constructs a C10.0-B request for this adapter. This separation prevents an
adapter call from becoming automatic or AI approval.

## Validation

`test_phase3c10_2_send_provider_adapter.py` covers:

- valid request acceptance at the adapter boundary;
- duplicate idempotency handling without a second provider invocation;
- provider unavailability;
- invalid request rejection before provider invocation;
- exact provider result-trace preservation.

C10.0, C10.1, C09, and the repository Core Regression Gate are run separately
for the phase validation result.
