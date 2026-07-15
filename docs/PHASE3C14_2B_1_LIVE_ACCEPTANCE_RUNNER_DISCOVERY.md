# Phase C14.2B.1 — Live Acceptance Runner Discovery

## Discovery Verdict

BLOCKED

The C14 runtime configuration is reported ready by the operator, and the C14.2A.2 recipient guard is present. However, this repository has no existing production-safe C14.2B live acceptance runner, CLI command, queue consumer, or worker executable that can construct exactly one isolated Queue → Worker → BrevoProviderAdapter execution.

This phase performed discovery only. No queue item, worker, adapter send, HTTP request, CRM record, or email was created.

## Worker Entry Points

| Location | Entry point | Command / invocation | Required environment |
|---|---|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/worker_execution.py` | `SendExecutionWorker.process(queue_item, timestamp)` | Python API only; explicit one-item call | None at construction. A live call additionally requires the injected Brevo adapter configuration. |
| `chitu-connector/chitu_connector/espocrm_sync/queue_contract.py` | `InMemorySendExecutionQueue` | Python API only; no consumer loop | None |
| `scripts/acceptance/phase3c14_1_preflight.ps1` | C14.1 configuration check | `& .\\scripts\\acceptance\\phase3c14_1_preflight.ps1 -PythonExecutable <python>` | `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `BREVO_TEST_RECIPIENT` |
| `tests/test_phase3c13_2_worker_execution.py` | Offline worker fixture | Unit-test-only construction | Uses `FakeProviderAdapter`; no live credentials |
| `tests/test_phase3c12_2_brevo_adapter.py` | Mock Brevo fixture | Unit-test-only construction | Synthetic mapping only; no live credentials |

No `console_scripts` entry point, `__main__` module, argparse command, scheduled consumer, queue daemon, or production worker launcher was found for this execution layer. The only connector CLI located is the unrelated acquisition runner.

## Queue Contract

Queue creation is explicit:

```text
queue = InMemorySendExecutionQueue()
item = queue.enqueue(send_execution_id, created_at)
```

The queue item schema is:

| Field | Meaning |
|---|---|
| `queue_item_id` | Deterministic `queue:<send_execution_id>` identity |
| `send_execution_id` | One send-execution identity; duplicate enqueue returns the same item |
| `state` | `QUEUED`, `CLAIMED`, `COMPLETED`, or `FAILED` |
| `created_at`, `claimed_at`, `completed_at` | Timezone-aware lifecycle timestamps |
| `worker_id` | Claim owner |
| `failure_category` | Optional normalized terminal-failure classification |

Lifecycle:

```text
QUEUED -> CLAIMED -> COMPLETED
                 -> FAILED
```

Claiming is process-local atomicity through an `RLock`. The queue is in-memory only: it has no durable backlog, Redis/Celery integration, polling loop, retry scheduler, or batch consumer.

## Provider Invocation Path

The worker performs one explicit path:

```text
QueueItem
  -> SendExecutionWorker.process(item, timestamp)
  -> InMemorySendExecutionWorkStore.get(send_execution_id)
  -> READY-state validation
  -> _provider_request(execution)
  -> injected ProviderAdapter.send(request)
  -> settle work item and queue item
```

`_provider_request` maps the work item into the C12 `SendRequest`:

| SendRequest field | Source |
|---|---|
| `request_id` | `SendExecutionWorkItem.request_id` |
| `send_execution_id` | `SendExecutionWorkItem.send_execution_id` |
| `recipient` | `SendExecutionWorkItem.recipient` |
| `subject` / `body` | `SendExecutionWorkItem.subject` / `.body` |
| `draft_hash` | `SendExecutionWorkItem.draft_hash` |
| `created_at` | `SendExecutionWorkItem.created_at` |
| `metadata` | Fixed `{"source": "c13-worker"}` |

The default worker adapter is `FakeProviderAdapter`. A live path requires an explicit injection of:

```text
BrevoProviderAdapter(
  BrevoConfiguration.from_environment(),
  UrllibBrevoHttpClient(),
)
```

Only `BrevoProviderAdapter.send()` invokes the Brevo HTTP seam, using `POST /smtp/email`. In acceptance mode, its final payload uses `BREVO_TEST_RECIPIENT` instead of the work item's original recipient. If acceptance mode is enabled but that test recipient is absent, it returns a validation failure before HTTP.

## Existing Test Patterns

| Test file | Pattern | Network behavior |
|---|---|---|
| `tests/test_phase3c12_1_provider_contract.py` | `FakeProviderAdapter` contract and idempotency | None |
| `tests/test_phase3c12_2_brevo_adapter.py` | `MockBrevoHttpClient`, payload/error mapping, recipient guard | Mock only |
| `tests/test_phase3c12_3_brevo_acceptance.py` | Fixture response and message-ID extraction | Fixture only |
| `tests/test_phase3c13_1_queue_contract.py` | In-memory enqueue/claim/terminal transitions | None |
| `tests/test_phase3c13_2_worker_execution.py` | In-memory queue/store plus injected fake adapter | None |
| `tests/test_phase3c13_3_reliability_acceptance.py` | Duplicate/claim/failure reliability simulation | None |

These tests are valuable construction examples but are not live acceptance runners and must not be repurposed for live delivery.

## Recommended Safe Execution Method

There is no executable command to recommend yet.

Do not use a test module, an ad-hoc `python -c` invocation, or a generic interactive shell to perform the live test. Those approaches lack a reviewed one-shot contract and could accidentally vary identity, recipient, logging, or cleanup behavior.

The minimum-risk next step is a separately approved, dedicated C14.2B runner with all of these fixed controls:

1. It must require `BREVO_ACCEPTANCE_MODE=true` and the three existing Brevo variables before constructing any work item.
2. It must construct exactly one new in-memory queue and exactly one `READY` `SendExecutionWorkItem`.
3. It must use synthetic identifiers and explicitly marked `C14.2B TEST EMAIL` content, with no CRM Lead or EmailEvent input.
4. It must inject `BrevoProviderAdapter` with `UrllibBrevoHttpClient` only after configuration validation.
5. It must call `worker.process()` exactly once, report only safe identifiers/statuses, and terminate.
6. It must not loop, retry, schedule, persist CRM state, create batch work, or expose message body, recipient, or credentials.

Planned command shape after that runner is implemented and independently reviewed:

```powershell
& <python> scripts/acceptance/phase3c14_2b_live_acceptance.py --single-controlled-test
```

That file and command do not currently exist and therefore must not be executed.

## Safety Constraints

- Keep the current acceptance recipient guard enabled through `BREVO_ACCEPTANCE_MODE=true`.
- Do not pass a customer recipient into any C14.2B request.
- Do not call the generic C13 worker without the dedicated runner's one-shot checks.
- Do not use the existing C14.1 preflight as a send mechanism; it intentionally loads configuration only.
- Do not use unit tests as a live sender.
- Preserve the existing boundary: no CRM write, projection, EmailEvent lifecycle change, batch campaign, scheduler, queue daemon, or retry execution.

## Decision

C14.2B remains blocked on a reviewed, explicit one-shot runner. The current code provides safe lower-level seams, but no safe operational entry point for a real single-recipient request.

