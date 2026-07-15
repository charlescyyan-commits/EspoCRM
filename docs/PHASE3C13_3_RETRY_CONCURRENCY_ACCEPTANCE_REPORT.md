# Phase3C13.3 Retry & Concurrency Acceptance Report

## Result

PASS WITH RISKS

## Scope

This phase accepted the reliability boundaries of the existing C13.1 queue, C13.2 worker, and C12.1 FakeProviderAdapter. It adds no retry scheduler, retry worker, daemon, queue service, durable deployment, real Brevo call, or production send.

## Duplicate Safety

A READY execution processed once by `SendExecutionWorker` reaches:

```
READY -> SENT
QUEUED -> CLAIMED -> COMPLETED
```

A repeat `process()` call for the same queue item is rejected as `QUEUE_ITEM_NOT_QUEUED`. The provider call count remains one, and the execution remains `SENT`.

## Concurrency Result

Two in-process workers were released concurrently against the same `QueueItem`.

- Exactly one local claim succeeded.
- The other worker received a safe `QUEUE_ITEM_NOT_QUEUED` rejection.
- The FakeProviderAdapter recorded exactly one send call.
- The queue item reached `COMPLETED`.

The C13.1 `RLock` supplies atomicity only within the current process. No distributed lock was added.

## Failure Handling

The FakeProviderAdapter failure matrix was accepted without external requests:

| Provider category | Stored SendExecution failureCategory | Queue state |
|---|---|---|
| AUTH_ERROR | AUTH | FAILED |
| RATE_LIMIT | RATE_LIMIT | FAILED |
| NETWORK_ERROR | NETWORK | FAILED |
| VALIDATION_ERROR | VALIDATION | FAILED |
| PROVIDER_ERROR | PROVIDER | FAILED |
| UNKNOWN_ERROR | UNKNOWN | FAILED |

Each failure remains terminal. No retry, requeue, or `RETRYING` transition is performed.

## Retry Readiness

C11.5 reservation fields remain present and unchanged:

- `retryCount` default: `0`
- `maxRetries` default: `0`
- `nextRetryAt`: nullable datetime
- `lastError`: nullable text
- `failureCategory`: reserved enum

The status enum remains `CREATED`, `READY`, `SENT`, `FAILED`, and `CANCELLED`; it has no `RETRYING` value. This is readiness evidence only, not a retry implementation.

## State Protection

The acceptance tests confirm:

- terminal `COMPLETED` queue items cannot be claimed or completed again;
- `SENT` execution work views cannot be changed to a failure terminal state;
- no API exists to move `SENT -> READY` or `SENT -> QUEUED`;
- old/repeated processing cannot replace the final `SENT` or `COMPLETED` state.

## Crash Limitation

A deterministic post-claim execution-load exception is now contained by the worker:

```
CLAIMED -> FAILED (failureCategory=UNKNOWN)
```

The queue item is not left `CLAIMED` in the in-process simulation, and it is never marked `SENT`.

This does not provide durable crash recovery. A forced process termination cannot be recovered by this in-memory queue/store; a future durable implementation needs claim leases or an explicit recovery process. Neither was added in C13.3.

## Tests

New acceptance coverage: `tests/test_phase3c13_3_reliability_acceptance.py`.

1. Duplicate worker execution calls the provider once and preserves `SENT`.
2. Concurrent workers permit one claim and one provider call.
3. All six provider failure categories map to C11.5 values.
4. Retry reservation fields remain schema-only.
5. Illegal terminal transitions are blocked.
6. A post-claim exception settles the queue as `FAILED`.
7. Fake-provider path has zero external requests and C10 hashes remain frozen.

Verification completed on 2026-07-14:

- C13.3 focused acceptance: 7/7 PASS.
- C11-C13 boundary suite: 72/72 PASS.
- Extension suite: 65/65 PASS.
- Connector suite: 270/270 PASS.
- Full Regression Gate: 7/7 required suites PASS, 382/382 tests.
- Gate evidence: `temp/test-results/regression-gate-20260714-192534-310.json`.
- C10 lifecycle contract: unchanged.

## Risks

- Claim concurrency and crash containment are process-local only.
- Queue and execution work store are in-memory test/reference implementations, not durable CRM or queue-service adapters.
- There is no distributed idempotency, lease expiry, recovery daemon, scheduler, worker deployment, retry execution, or batch sending.
- C12.3 live Brevo credential acceptance remains pending; no real provider call was made.
- C11.3 risk RISK-C11.3-001 (multiple possible writers for Lead email projection fields) remains deferred and unchanged.

## Scope Confirmation

No C10 lifecycle, C11 entity/projection, or C12 ProviderAdapter contract changes were made. C14 was not started.

