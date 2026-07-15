# Phase3C14.3.1C Result Adapter Implementation Report

## Result

**PASS WITH RISKS**

C14.3.1C implements the approved explicit result-command boundary:

```text
Safe provider result
  -> explicit result command
  -> connector result adapter
  -> SendExecution-only CRM result service
  -> existing SendExecution after-save hook
  -> EmailLifecycleProjectionService
  -> Lead projection
```

The Worker still returns its existing outcome to its caller. It has no CRM
import or write path. The adapter does not create `EmailEvent` or `ReplyEvent`;
Lead changes remain exclusively in the existing projection service.

The implementation is acceptance-oriented: the Python CLI uses a local
CRM-shaped fixture, while the new PHP service is the CRM-side
`SendExecution`-only writer for a future explicitly authorized runtime caller.
No HTTP endpoint, scheduler, webhook, durable result outbox, retry loop, or
real delivery path was added.

## Files Changed

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/send_execution_result_adapter.py` | Added safe command model, deterministic `result_id`, terminal-state adapter, compare-and-set repository seam, and in-memory acceptance repository. |
| `scripts/acceptance/phase3c14_3_1c_apply_result.py` | Added explicit fixture-only CLI command with structured safe JSON output. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionResultAdapterService.php` | Added CRM `SendExecution`-only terminal result writer. Saving it activates the existing projection hook. |
| `tests/test_phase3c14_3_1c_result_adapter.py` | Added connector result-model, state, idempotency, network, and Worker-isolation tests. |
| `crm-extension/tests/test_phase3c14_3_1c_result_adapter.py` | Added CRM service scope and terminal-transition static tests. |
| `crm-extension/tests/test_extension_skeleton.py` | Registered the approved new PHP service in the exact extension PHP inventory. |
| `docs/PHASE3C14_3_1C_RESULT_ADAPTER_IMPLEMENTATION_REPORT.md` | Added this record. |

The pre-existing `SendExecutionBridgeAdapterService.php` was deliberately not
changed. It belongs to an earlier C14.3.2 surface and has EmailEvent/retry
behavior that is outside the C14.3.1C command boundary.

## Result Command Schema

`SendExecutionResultCommand` contains exactly the approved safe terminal
result fields:

| Field | Rule |
|---|---|
| `execution_id` | Non-empty CRM SendExecution identity. |
| `provider_attempt_id` | Required for `SENT`; optional only at the B-1 result boundary for failures. |
| `normalized_status` | B-1 terminal enum: `SENT` or `FAILED`. |
| `failure_class` | Required for `FAILED`: `NETWORK`, `AUTH`, `VALIDATION`, `PROVIDER`, or `UNKNOWN`. |
| `error_code` | Required safe upper-case identifier for `FAILED`. |
| `occurred_at` | Timezone-aware terminal timestamp. |
| `result_id` | SHA-256 idempotency key over versioned terminal semantic values. |

The model constructs the existing B-1 `SendExecutionBridgeResult` during
validation, so it cannot invent a new result vocabulary or bypass B-1 terminal
rules. `result_id` deliberately excludes receive time; semantically identical
terminal results retain one stable key.

## State Transition Rules

| Current SendExecution | Incoming result | Outcome |
|---|---|---|
| `READY` | `SENT` | Apply `SENT`, set `providerMessageId`, clear failure context. |
| `READY` | `FAILED` | Apply `FAILED`, map failure class to `failureCategory`, set safe `lastError`, clear provider message id. |
| `SENT` | Same success result | `DUPLICATE_RESULT`; no save. |
| `FAILED` | Same failure class and safe code | `DUPLICATE_RESULT`; no save. |
| `SENT` / `FAILED` | Contradictory terminal result | `RESULT_CONFLICT`; no mutation. |
| `CREATED` / `CANCELLED` | Any result | `RESULT_NOT_APPLICABLE`; no mutation. |

There is no currently authorized higher-priority result type. Therefore a
`SENT -> FAILED` or `FAILED -> SENT` request is always a conflict, not a
transition. The in-memory acceptance repository makes the initial
`READY -> terminal` update atomic; the PHP service implements the same
terminal/duplicate/conflict semantics for a future explicit CRM caller.

## Idempotency Design

The adapter validates `result_id` against a deterministic SHA-256 key, then
uses `execution_id` plus terminal result values to classify replay:

- same terminal state and same stored values: no-op `DUPLICATE_RESULT`;
- conflicting terminal state or values: `RESULT_CONFLICT`;
- a `READY` record: one compare-and-set transition to the terminal record.

This prevents repeated application from performing another SendExecution
update. The command adapter has no EmailEvent or ReplyEvent path. It never
writes Lead directly; only a real source-record save invokes the existing
`EmailLifecycleProjectionService`, which already skips unchanged projections.

## Network Error Handling

`BREVO_NETWORK_ERROR` remains exactly within the existing contract:

```text
RETRYABLE_FAILURE -> NETWORK -> FAILED
```

The result command records `SendExecution.status = FAILED`,
`failureCategory = NETWORK`, and `lastError = BREVO_NETWORK_ERROR`. It does
not increment retry state, create a queue item, retry, requeue, resend, or
create a provider message id. Delivery truth remains unknown when a timeout
could have occurred after provider acceptance.

## Security Review

- accepted and emitted values are limited to safe identifiers, status, class,
  and timestamp;
- raw recipient, subject, body, provider response payload, credentials,
  authorization headers, tokens, and network exception details are absent;
- the connector result adapter imports no Worker, Queue, Provider, Brevo,
  HTTP, EmailEvent, or ReplyEvent module;
- the CRM service loads and saves only `SendExecution`; it has no direct Lead,
  EmailEvent, ReplyEvent, Provider, or retry code; and
- the CLI is fixture-only and makes no network request or CRM write.

## Tests

| Command | Result |
|---|---|
| `python -m unittest tests.test_phase3c14_3_1c_result_adapter` | PASS — 8 tests |
| `python -m unittest discover -s crm-extension/tests -p test_phase3c14_3_1c_result_adapter.py` | PASS — 3 tests |
| `python -m py_compile ...send_execution_result_adapter.py ...phase3c14_3_1c_apply_result.py` | PASS |
| `python scripts/acceptance/phase3c14_3_1c_apply_result.py --help` | PASS |
| C11 lifecycle + C14.3.1A/B-1/B-2/B-3/B-4/C focused suite | PASS — 48 tests |
| `python -m unittest discover -s crm-extension/tests -p test_*.py` | PASS — 75 tests |
| `python -m unittest discover -s chitu-connector/tests -p test_*.py` | PASS — 270 tests |

Focused coverage proves:

1. success updates only the SendExecution-shaped record to `SENT`;
2. failure maps safe class/code into `FAILED` context;
3. duplicate results are ignored without a second compare-and-set;
4. a failure cannot downgrade a prior `SENT` state;
5. `BREVO_NETWORK_ERROR` stays `FAILED/NETWORK` without retry behavior;
6. Worker imports contain no CRM result adapter, event, or EspoCRM dependency;
7. the result adapter contains no Worker, Queue, Provider, Brevo, Event, or
   transport dependency; and
8. the CRM service has no direct Lead/Event/Reply/retry path.

All C14.3.1C-specific tests use synthetic records and fixture data. No Worker
execution, Provider call, Brevo request, HTTP request, or real email send
occurred during this phase. The broader focused suite retains B-4's existing
in-memory Queue coverage without changing Queue implementation or adding a
queue action to C14.3.1C.

## Compatibility

| Boundary | Result | Evidence |
|---|---|---|
| C10 | PASS | No C10 lifecycle, approval, idempotency, provider, or scoring source changed. |
| C11 | PASS WITH RISKS | Only a new SendExecution source writer is added; existing after-save projection remains the sole Lead-status writer. The existing C11 cross-writer risk remains deferred. |
| C12 | PASS | Existing B-1 safe terminal vocabulary is reused; no Provider contract changed. |
| C13 | PASS | Worker, Queue, work-store, and retry behavior are unchanged. |
| C14.2B | PASS | Network result preserves `RETRYABLE_FAILURE -> NETWORK -> FAILED`; no automatic resend. |

## Scope Confirmation

| Question | Result |
|---|---|
| Was Worker modified? | No. |
| Was Provider/Brevo modified? | No. |
| Was Queue modified or a duplicate item created? | No. |
| Was CRM schema or an entity created? | No. |
| Was EmailEvent created? | No. |
| Was ReplyEvent created? | No. |
| Was Lead written directly? | No. |
| Was a real email sent? | No. |

## Risks and Next Recommendation

The explicit CLI is an acceptance fixture, not a production CRM integration.
The current C13 result and queue state remain process-local, so a process crash
can lose result evidence before an operator/runtime captures the safe command.
The PHP service is prepared for an explicitly approved CRM caller but has not
been wired to an HTTP endpoint, webhook, scheduler, or production command.

Next, only if separately approved, run a CRM Test runtime acceptance phase for
the explicit result adapter: invoke the CRM service with a synthetic terminal
result, verify the existing SendExecution after-save projection, and stop. Do
not add automatic callback delivery, persistent queues, retries, or real
provider execution as part of that acceptance work.
