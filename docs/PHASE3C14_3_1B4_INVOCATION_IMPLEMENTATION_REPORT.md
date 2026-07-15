# Phase3C14.3.1B-4 Explicit Invocation Implementation Report

## Result

**PASS WITH RISKS**

B-4 adds an explicit, operator/test-owned Python command path:

```text
Operator or test
  -> Python CLI with one execution_id
  -> ExplicitBridgeInvocationService.submit(execution_id)
  -> existing B-2 adapter.submit(execution_id)
  -> B-1 request validation
  -> existing C13 InMemorySendExecutionQueue.enqueue(...)
```

The command neither starts the Worker nor calls a Provider.  It is an
acceptance-only explicit command: the C13 queue and its duplicate ledger are
process-local, so they do not survive a separate CLI process exit or restart.
That known C13 limitation is why the result remains `PASS WITH RISKS`.

## Files Changed

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/explicit_bridge_invocation.py` | Added B-3-to-B-2 payload-source adapter, explicit invocation service, and B-1 adapter that submits to the existing C13 in-memory Queue. |
| `scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py` | Added an explicit fixture-only CLI entry point with structured JSON output and exit codes. |
| `tests/test_phase3c14_3_1b4_explicit_invocation.py` | Added B-4 invocation boundary tests. |
| `docs/PHASE3C14_3_1B4_INVOCATION_IMPLEMENTATION_REPORT.md` | Added this implementation record. |

## Command Usage

```powershell
& <python> scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py EXECUTION_ID `
  --fixture crm-fixture.json `
  --payload-db connector-payload.sqlite
```

The CLI requires a local CRM-shaped acceptance fixture and a B-3 SQLite
payload database.  It does not connect to EspoCRM, make HTTP requests, read
provider credentials, or write CRM state.

Its stdout is safe structured JSON only:

```json
{
  "execution_id": "...",
  "idempotency_key": "...",
  "reason_code": null,
  "retryable_submission_failure": false,
  "status": "SUBMITTED"
}
```

Exit codes are `0` for `SUBMITTED` or `DUPLICATE`, `1` for `BLOCKED`, and `2`
for `FAILED_SUBMISSION` or local configuration failure.  The output never
includes recipient, subject, body, API keys, authorization headers, or other
raw payload content.

## Invocation Flow and Validation

`ExplicitBridgeInvocationService` first validates the explicit execution id
using injected read-only boundaries:

1. `SendExecution` exists;
2. `SendExecution.status` is exactly `READY`;
3. a self-verifying B-3 payload snapshot exists for the execution; and
4. B-1's deterministic idempotency key matches the request immediately before
   the C13 Queue submission call.

Only then does the service delegate to the existing B-2 adapter.  B-2 retains
its approved-DraftApproval, draft identity, payload completeness, and content
hash checks.  In particular, `DraftApproval = APPROVED` by itself never calls
the invocation service and cannot trigger a queue submission.

`SqliteApprovedDeliveryPayloadSource` is the narrow B-3-to-B-2 composition
adapter.  In acceptance it uses an explicit read-only `draft_id ->
execution_id` mapping and returns the existing B-2 `ApprovedDeliveryPayload`
shape from a durable B-3 snapshot.  It is not a CRM runtime client or a
production discovery mechanism.

## Duplicate Protection

`QueueSubmissionBridgeAdapter` verifies B-1's stable key derived from
`execution_id` before it touches Queue.  Within one connector process it then
uses two protections:

- the B-1 in-memory receipt fixture returns `DUPLICATE` for a repeated
  execution; and
- the existing C13 Queue has one `QueueItem` identity per execution id.

The focused test proves first submission is `SUBMITTED`, the second is
`DUPLICATE`, and only one C13 queue item exists.

This is not a durable cross-restart guarantee: the queue and receipt ledger
are intentionally in-memory.  B-3 preserves the payload snapshot across a
restart, but B-4 does not add a persistent queue, scheduler, retry, or send
attempt ledger.

## Failure Behavior

If Queue is unavailable, its exception reaches the existing B-2 containment
boundary.  The final result is:

```text
status = FAILED_SUBMISSION
reason_code = BRIDGE_SUBMISSION_UNAVAILABLE
retryable_submission_failure = true
```

No CRM write capability exists in the invocation service or queue adapter.
Consequently the failure does not mark `SendExecution` as `SENT`, does not
alter `Lead`, and does not remove or modify the immutable B-3 snapshot.  An
operator may explicitly invoke the command again after Queue availability is
restored; this is an operator decision, not an automatic retry strategy.

## Tests

| Command | Result |
|---|---|
| `python -m py_compile chitu-connector/chitu_connector/espocrm_sync/explicit_bridge_invocation.py scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py tests/test_phase3c14_3_1b4_explicit_invocation.py` | PASS |
| `python scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py --help` | PASS |
| `python -m unittest tests.test_phase3c14_3_1b1_bridge_contract tests.test_phase3c14_3_1b2_crm_bridge_adapter tests.test_phase3c14_3_1b3_payload_snapshot tests.test_phase3c14_3_1b4_explicit_invocation` | PASS — 28 tests |
| `python -m unittest discover -s chitu-connector/tests -p test_*.py` | PASS — 270 tests |

B-4 coverage proves:

1. a valid execution is submitted once and creates one C13 in-memory queue
   item;
2. duplicate explicit submission returns `DUPLICATE` without a second item;
3. a missing durable snapshot is blocked before B-2 bridge or Queue call;
4. a non-`READY` execution is blocked before Queue submission;
5. Queue unavailability returns a retryable submission failure while the CRM
   execution remains `READY` and the snapshot remains present;
6. a content-hash mismatch is blocked by unchanged B-2 validation; and
7. the B-4 composition source imports no Worker, Provider, Brevo, HTTP, or
   transport module.

All verification uses synthetic fixture data, temporary SQLite files, and the
C13 in-memory Queue.  No Worker, Provider, Brevo, HTTP request, or real email
send was executed.

## Compatibility

| Area | Result | Evidence |
|---|---|---|
| C10 | PASS | No C10 module or lifecycle transition is imported or changed. CRM `APPROVED` is not mapped to C10 `READY_TO_SEND`. |
| C11 | PASS | No CRM entity, schema, metadata, PHP hook, Lead projection, Event writer, or CRM write path changed. |
| C12 | PASS | No Provider contract or implementation changed; B-4 does not import a Provider. |
| C13 | PASS WITH RISKS | The existing `InMemorySendExecutionQueue` is called through its current contract. No Queue source or Worker source is modified; state remains process-local. |
| C14.2B | PASS | No retry strategy, error classification, terminal network interpretation, Brevo code, or send behavior changed. |

## Scope Confirmation

| Question | Result |
|---|---|
| Was the Worker touched? | No. |
| Was the Queue implementation touched? | No; B-4 only invokes its existing `enqueue` and `get` contract. |
| Was CRM modified? | No. |
| Was a CRM schema/entity added? | No. |
| Was a Provider/Brevo/retry path modified? | No. |
| Was a real email sent? | No. |

## Next Recommended Phase

Proceed only with separately approved C14.3C result-adapter work: consume a
terminal Worker result and update CRM `SendExecution` only, leaving Lead
projection to the existing single writer.  Durable Queue/receipt state,
scheduler orchestration, retry policy, and real provider execution remain
separate future decisions.
