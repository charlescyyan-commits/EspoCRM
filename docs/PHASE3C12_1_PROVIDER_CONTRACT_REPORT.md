# Phase3C12.1 Provider Contract Report

**Date:** 2026-07-14  
**Result:** PASS WITH RISKS

## Interface Design

C12.1 adds a separate, offline `ProviderAdapter` protocol. It is parallel to the frozen C10.2 adapter and is not wired into C10/C11 lifecycle execution.

```text
DraftApproval -> SendExecution -> ProviderAdapter -> future external provider
```

The protocol defines:

- `send(SendRequest) -> SendResult`
- `get_status(provider_message_id) -> ProviderStatus`

No lifecycle transition, CRM mutation, retry execution, or provider configuration is performed.

## Request and Response Model

`SendRequest` includes `request_id`, `send_execution_id`, recipient, subject, body, metadata, `draft_hash`, and a timezone-aware `created_at`.

`SendResult` contains the explicit success flag, `SendResultStatus`, optional provider message ID, `ProviderStatus`, and a sanitized `ProviderError`. Result statuses are:

- `SUCCESS`
- `FAILED`
- `RETRYABLE_FAILURE`
- `PERMANENT_FAILURE`

The request's recipient, subject, body, and metadata are excluded from its representation. The fake adapter retains no request content after evaluating the contract.

## Error Taxonomy

| C12.1 provider error | C11.5 failureCategory |
|---|---|
| `AUTH_ERROR` | `AUTH` |
| `RATE_LIMIT` | `RATE_LIMIT` |
| `NETWORK_ERROR` | `NETWORK` |
| `VALIDATION_ERROR` | `VALIDATION` |
| `PROVIDER_ERROR` | `PROVIDER` |
| `UNKNOWN_ERROR` | `UNKNOWN` |

Timeout simulation produces `NETWORK_ERROR` and `RETRYABLE_FAILURE`. The mapping reserves persistence-compatible failure context only; it does not schedule or execute a retry.

## Fake Provider Behavior

`FakeProviderAdapter` is deterministic and network-free. It supports:

- success with a stable fake provider message ID;
- configurable sanitized failures, including authentication and rate-limit cases; and
- timeout simulation.

`external_request_count` is always zero. `get_status` reads only in-memory fake result state.

## Idempotency Boundary

The fake adapter keys a result by the pair of `send_execution_id` and `request_id`. Repeating the same identity returns the cached deterministic result and makes one logical fake send evaluation. Reusing either identity with a different partner returns a safe validation failure. This is a local contract guard only; no distributed lock is implemented.

## Security Notes

- No API key, token, credential, URL, webhook, or SMTP configuration exists.
- Metadata keys that appear to contain a secret are rejected.
- Content fields are redacted from request representation.
- Errors contain only a taxonomy category and safe code; no raw provider payload is retained.
- The module contains no network or logging dependency.

## Test Results

Added `tests/test_phase3c12_1_provider_contract.py`:

1. fake-provider success returns `SUCCESS`;
2. timeout returns `NETWORK_ERROR`;
3. auth failure returns `AUTH_ERROR`;
4. rate limit returns `RATE_LIMIT`;
5. duplicate request identity returns the deterministic cached result;
6. external request count remains zero and content is redacted; and
7. C10 source and test hashes remain frozen.

| Verification | Result |
|---|---|
| C12.1 provider-contract tests | PASS — 7/7 |
| C11.2–C11.5 + C12.1 boundary tests | PASS — 38/38 |
| Extension suite | PASS — 65/65 |
| Connector suite, including C10 | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 suites, 382/382 tests |

Successful Regression Gate command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable 'C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

Evidence: `temp/test-results/regression-gate-20260714-185934-218.json`, UTC `2026-07-14T10:59:34.2060546Z`, overall status `PASS`.

## Risks

1. This is a contract and fake implementation only. No real provider interoperability or credential/configuration path is validated.
2. Idempotency caching is process-local. A future multi-instance execution phase needs an explicitly approved durable coordination mechanism.
3. C10/C11 lifecycle and projection are deliberately not wired to call the new contract in this phase.
4. RISK-C11.3-001 remains deferred and is unchanged.

## Scope Confirmation

No Instantly integration, API key, email send, SMTP, webhook, Worker, Queue, Scheduler, retry execution, or C12 Worker implementation was introduced.

