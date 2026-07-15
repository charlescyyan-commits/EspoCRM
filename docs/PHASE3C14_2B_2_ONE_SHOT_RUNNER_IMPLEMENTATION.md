# Phase C14.2B.2 — One-shot Live Acceptance Runner Implementation

## Result

PASS WITH RISKS

A dedicated C14.2B runner now exists at:

`scripts/acceptance/phase3c14_2b_live_runner.py`

It is an explicit, one-shot operational entry point. Its default behavior is dry-run validation; no provider transport is constructed and no email can be sent unless an operator explicitly supplies `--execute-live`.

No live execution occurred during this implementation.

## Files Added

- `scripts/acceptance/phase3c14_2b_live_runner.py`
- `tests/test_phase3c14_2b_live_runner.py`
- `docs/PHASE3C14_2B_2_ONE_SHOT_RUNNER_IMPLEMENTATION.md`

## Runner Contract

### Default dry-run

```powershell
& <python> .\\scripts\\acceptance\\phase3c14_2b_live_runner.py --dry-run
```

`--dry-run` is optional because it is the default. This mode:

- validates the protected process environment;
- creates only an in-memory execution plan, not a queue item;
- prints the planned job ID plus the synthetic recipient before guard and configured recipient after guard;
- prints `MODE=DRY_RUN` and `LIVE_SEND=NOT_INVOKED`;
- does not construct `UrllibBrevoHttpClient`;
- does not construct a Queue, Worker, or Brevo adapter; and
- performs no HTTP request, CRM write, persistent queue write, or email send.

### Explicit live mode

```powershell
& <python> .\\scripts\\acceptance\\phase3c14_2b_live_runner.py --execute-live
```

This command was documented but not run in this phase. If separately authorized, it creates exactly one in-memory job and performs exactly one explicit path:

```text
InMemorySendExecutionQueue.enqueue(one synthetic SendExecution ID)
  -> SendExecutionWorker.process(one QueueItem)
  -> BrevoProviderAdapter.send(one SendRequest)
  -> UrllibBrevoHttpClient POST /smtp/email
```

The synthetic work item uses no CRM Lead, EmailEvent, customer data, or persisted record. It has a generated job/request identity, a `READY` status, and explicitly marked `[C14.2B TEST EMAIL]` content.

## Safety Controls

Before either dry-run planning or live execution, the runner requires:

| Environment variable | Requirement |
|---|---|
| `BREVO_ACCEPTANCE_MODE` | Exact lowercase value `true` |
| `BREVO_TEST_RECIPIENT` | Present and non-empty |
| `BREVO_API_KEY` | Present and non-empty |
| `BREVO_SENDER_EMAIL` | Present and non-empty |

If acceptance mode is anything other than exact `true`, the runner exits with `BREVO_ACCEPTANCE_MODE_NOT_TRUE` and prints `LIVE_SEND=NOT_INVOKED`.

If the test recipient is missing, it exits with `BREVO_TEST_RECIPIENT_MISSING` before it can construct the Queue, Worker, adapter, or HTTP transport. The Brevo adapter's existing final-boundary guard remains a second independent enforcement layer.

The original recipient is a fixed synthetic `.invalid` mailbox. The runner prints the original and resolved test recipient as required for the controlled acceptance record; it never prints API keys, sender credentials, body content, or raw provider responses.

There is no loop, batch collector, scheduler, retry, persistent queue, CRM action, Lead action, or EmailEvent action in the runner.

## Output

For a validated plan, the runner prints:

- `JOB_ID`
- `RECIPIENT_BEFORE_GUARD`
- `RECIPIENT_AFTER_GUARD`
- `PROVIDER_RESULT` after a live attempt
- `EXTERNAL_MESSAGE_ID` when Brevo returns one

The live result output is restricted to boolean/status fields, a safe error code, and the external message ID. It does not emit request content, credentials, or raw provider payloads.

## Verification

Offline command:

```text
<Codex bundled Python> -m unittest tests.test_phase3c14_2b_live_runner tests.test_phase3c12_2_brevo_adapter
```

Result:

```text
Ran 15 tests in 0.012s
OK
```

The runner tests verify:

1. Default mode is dry-run and does not construct the HTTP client.
2. `--execute-live` is blocked when acceptance mode is false.
3. `--execute-live` is blocked when acceptance mode is not exact lowercase `true`.
4. `--execute-live` is blocked when the test recipient is missing.

The C12.2 mock-HTTP adapter regression suite also passed. These tests use synthetic configuration and mock transports only. No real Brevo API call or email send occurred.

## Risks and Next Step

The runner is intentionally capable of a real provider call only when `--execute-live` is explicitly invoked in a protected process environment. C14.2B live acceptance therefore still requires a separate operator authorization and a fresh runtime preflight.

Known C13 limits remain unchanged: the queue and work store are process-local in-memory reference implementations, and there is no durable recovery or distributed idempotency. Those constraints are acceptable for one controlled, single-process acceptance request but not production dispatch.

