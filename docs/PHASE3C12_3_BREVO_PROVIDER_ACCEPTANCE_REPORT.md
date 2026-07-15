# Phase3C12.3 Brevo Provider Acceptance Report

**Date:** 2026-07-14  
**Result:** BLOCKED BY CONFIGURATION

## Environment Validation

The process environment was checked without reading or emitting any secret values.

| Required variable | Result |
|---|---|
| `BREVO_API_KEY` | MISSING |
| `BREVO_SENDER_EMAIL` | MISSING |
| `BREVO_SENDER_NAME` | MISSING |
| `BREVO_TEST_RECIPIENT` | MISSING |

C12.3 therefore did not construct a live credentialed request, did not instantiate the live Brevo transport, and did not send an email. No credential, token, sender identity, recipient, or secret was output.

## Acceptance Result

Live sandbox/test-provider acceptance is blocked because the required configuration and an explicit test recipient are absent. This is an expected safe stop, not a provider failure.

The adapter acceptance contract was verified using deterministic documented in-process response fixtures:

- 201 with a non-empty `messageId` maps to `SendResult.SUCCESS` and `ProviderStatus.ACCEPTED`;
- 401 maps to `AUTH_ERROR`;
- 429 maps to `RATE_LIMIT`;
- 400 maps to `VALIDATION_ERROR`;
- malformed success data maps to `UNKNOWN_ERROR`; and
- missing API key returns `MISSING_BREVO_API_KEY` before the HTTP client is called.

## Provider Behavior and Trace

The fixture success response confirms that the adapter extracts `messageId` into `SendResult.provider_message_id`. No CRM entity, Lead, DraftApproval, SendExecution, or ReplyEvent write was performed. The adapter alone was exercised.

Brevo transactional status lookup remains explicitly `NOT_SUPPORTED`; no status is fabricated.

## Webhook Decision

**Decision: Deferred.**

A future provider-event webhook may be required when delivery, bounce, or provider-originated reply signals need to become approved lifecycle inputs. It is not required for C12.3 adapter acceptance. A later design must define authentication, event deduplication, provider-message identity, retention boundaries, and the one-way mapping to C11 source records before implementation.

No webhook was implemented.

## Idempotency Notes

Current guarantee: local in-process idempotency by the pair of `send_execution_id` and `request_id`. Repeating the same pair returns the cached result without a second transport call.

Future requirement: durable distributed idempotency/lease ownership for multi-instance execution. No distributed lock or retry execution was introduced.

## Tests

Added `tests/test_phase3c12_3_brevo_acceptance.py`:

1. configuration validation with no credentials;
2. documented success fixture and message-ID extraction;
3. documented 401, 429, and 400 error fixtures;
4. no CRM side-effect path; and
5. frozen C10 lifecycle and test hashes.

| Verification | Result |
|---|---|
| C12.3 acceptance-fixture tests | PASS — 5/5 |
| C11.2–C11.5 + C12.1–C12.3 boundary tests | PASS — 51/51 |
| Extension suite | PASS — 65/65 |
| Connector suite, including C10 | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 suites, 382/382 tests |

Successful Regression Gate command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable 'C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

Evidence: `temp/test-results/regression-gate-20260714-190954-533.json`, UTC `2026-07-14T11:09:54.5055991Z`, overall status `PASS`.

## Risks

1. No live Brevo sandbox request or real response was verified because test configuration is absent.
2. Real provider acceptance still requires a designated test recipient and explicit non-production credentials.
3. Delivery/reply observability is deferred; `get_status` is explicitly unsupported and no webhook exists.
4. Local idempotency is not a multi-instance guarantee.
5. RISK-C11.3-001 remains deferred and unchanged.

## Scope Confirmation

No production email, customer data, CRM write, Lead workflow change, Opportunity automation, C10 lifecycle change, C11 entity/projection change, Worker, Queue, Scheduler, retry execution, webhook, or C13 work was introduced.

