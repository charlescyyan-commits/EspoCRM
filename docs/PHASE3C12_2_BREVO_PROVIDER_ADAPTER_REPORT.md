# Phase3C12.2 Brevo Provider Adapter Report

**Date:** 2026-07-14  
**Result:** PASS WITH RISKS

## Adapter Design

C12.2 adds `BrevoProviderAdapter`, an implementation of the C12.1 `ProviderAdapter` contract. It remains separate from C10 lifecycle orchestration and C11 CRM projection.

```text
SendExecution -> ProviderAdapter -> BrevoProviderAdapter -> Brevo HTTP transport seam
```

No worker, queue, scheduler, retry executor, approval automation, Lead workflow, or CRM source-of-truth change was introduced.

## Brevo Mapping

The adapter maps an explicit C12.1 `SendRequest` to the Brevo transactional endpoint payload:

- endpoint path: `/smtp/email`;
- sender from configured environment values;
- recipient, subject, and HTML body from the request; and
- stable request, SendExecution, and draft-hash trace headers.

A successful 200/201/202 response requires a non-empty `messageId`. It returns `SendResult(success=True)` with `ProviderStatus.ACCEPTED`. A malformed success response is safely classified as `UNKNOWN_ERROR`.

`get_status` returns explicit `ProviderStatus.NOT_SUPPORTED`; this contract does not claim a Brevo transactional-message status-query endpoint.

## Configuration

`BrevoConfiguration.from_environment` reads only:

- `BREVO_API_KEY`
- `BREVO_SENDER_EMAIL`
- optional `BREVO_SENDER_NAME`

No key, sender, recipient, or secret is hardcoded. API keys are redacted from configuration representation. A missing API key returns a sanitized `VALIDATION_ERROR` with `MISSING_BREVO_API_KEY` before the HTTP seam is called.

## HTTP and Error Mapping

All HTTP behavior is isolated behind `BrevoHttpClient`. Tests inject a local mock; the optional `UrllibBrevoHttpClient` is explicit and was not instantiated during verification.

| Brevo signal | C12.1 error | Result status |
|---|---|---|
| 401 / 403 | `AUTH_ERROR` | `PERMANENT_FAILURE` |
| 429 | `RATE_LIMIT` | `RETRYABLE_FAILURE` |
| transport timeout | `NETWORK_ERROR` | `RETRYABLE_FAILURE` |
| 400 | `VALIDATION_ERROR` | `PERMANENT_FAILURE` |
| 5xx | `PROVIDER_ERROR` | `RETRYABLE_FAILURE` |
| malformed or other response | `UNKNOWN_ERROR` | safe failure |

C12.1 error categories remain mapped to C11.5 `SendExecution.failureCategory`; no retry is executed.

## Idempotency

The adapter caches completed results in process memory by the pair of `send_execution_id` and `request_id`. A duplicate pair returns the original deterministic result and avoids a second transport call. Cross-pair identity reuse returns a safe validation failure. This is not a distributed lock.

## Security

- No production API key or sender is present in source.
- No logging, print output, or raw provider response storage is introduced.
- Request content is not written to logs by the adapter.
- Sanitized errors contain only category and safe code.
- Mock HTTP is used for every test; no real provider request or email send occurred.

## Tests

Added `tests/test_phase3c12_2_brevo_adapter.py` with mock HTTP coverage for:

1. successful transactional send mapping;
2. 401 authentication failure;
3. 429 rate limit;
4. timeout/network failure;
5. malformed success response;
6. missing API key with zero HTTP calls;
7. duplicate identity and explicit unsupported status lookup; and
8. source security checks plus C10 frozen hashes.

| Verification | Result |
|---|---|
| C12.1 + C12.2 provider tests | PASS — 15/15 |
| C11.2–C11.5 + C12.1–C12.2 boundary tests | PASS — 46/46 |
| Extension suite | PASS — 65/65 |
| Connector suite, including C10 | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 suites, 382/382 tests |

Successful Regression Gate command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable 'C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

Evidence: `temp/test-results/regression-gate-20260714-190618-272.json`, UTC `2026-07-14T11:06:18.2583390Z`, overall status `PASS`.

## Risks

1. The real transport code is not integration-tested against Brevo and no production credentials are configured.
2. `get_status` is explicitly unsupported; delivery/reply state must continue to arrive through separately approved lifecycle inputs.
3. Idempotency caching is process-local and requires a future approved durable coordination design for multi-instance execution.
4. RISK-C11.3-001 remains deferred and is unchanged.

## Scope Confirmation

No production email, API key configuration, Instantly integration, webhook, Worker, Queue, Scheduler, retry execution, approval automation, Lead workflow change, C10 lifecycle change, C11 projection change, or C12.3 work was introduced.

