# Phase3C14.3.1D Failure Projection Hardening Report

## Result

**PASS WITH RISKS**

C14.3.1D freezes and verifies the existing explicit result-command boundary.
It adds no execution behavior and does not widen the authority of the Worker,
Queue, Provider, or CRM domain.  The checked terminal path remains:

```text
safe Provider result
  -> explicit result command
  -> SendExecution result adapter
  -> SendExecution save only
  -> existing SendExecution hook
  -> EmailLifecycleProjectionService
  -> Lead projection
```

All D checks use synthetic records and source-level boundary assertions. No
Provider request, Brevo request, Queue submission, CRM runtime write, or real
email send was performed.

## Files Modified

| File | Change |
|---|---|
| `tests/test_phase3c14_3_1d_failure_projection_hardening.py` | Added focused terminal-state, replay, out-of-order, network ambiguity, projection ownership, and safe-surface tests. |
| `docs/PHASE3C14_3_1D_FAILURE_PROJECTION_HARDENING_REPORT.md` | Added this D freeze and verification record. |

No production result-adapter, Worker, Queue, Provider, Brevo, retry, CRM
schema, entity, Lead projection, EmailEvent writer, or ReplyEvent writer was
changed in this phase.

## Invariants Verified

| Invariant | Evidence | Result |
|---|---|---|
| `READY -> SENT` is allowed | D focused test applies a success result to a synthetic `READY` record. | PASS |
| `READY -> FAILED` is allowed | D focused test applies a safe validation failure to a synthetic `READY` record. | PASS |
| `SENT -> FAILED` is forbidden | A late provider failure returns `RESULT_CONFLICT`; the terminal record and compare-and-set count remain unchanged. | PASS |
| `FAILED -> SENT` is forbidden | A late success result returns `RESULT_CONFLICT`; the failure record remains unchanged. | PASS |
| Same `result_id` replay is ignored | The first command is `APPLIED`; its replay is `DUPLICATE_RESULT`; only one compare-and-set occurs. | PASS |
| No duplicate event or projection source save | The explicit result adapter has no EmailEvent/ReplyEvent path. A duplicate terminal command does not perform a second source update, so the existing after-save projection hook has no second save to consume. | PASS |
| Old `FAILED` after `SENT` cannot roll back Lead | The source `SendExecution` remains `SENT` with zero result-adapter update. Existing C11 lifecycle tests verify projection ordering and unchanged-source behavior. | PASS |
| Network ambiguity remains non-retrying failure | `RETRYABLE_FAILURE -> NETWORK -> FAILED` is preserved as `BREVO_NETWORK_ERROR`, `NETWORK`, `FAILED`; the result boundary has no retry or enqueue call. | PASS |
| Lead ownership stays with projection service | Result adapter scope checks confirm no `peEmailStatus`, Lead lookup, EmailEvent, or ReplyEvent writer. The adapter saves only `$execution`; the existing hook invokes `EmailLifecycleProjectionService`. | PASS |

There is no approved higher-priority terminal-result class in C14.3.1. Until
one is designed and authorized, both contradictory terminal directions are
conflicts rather than transitions.

## Duplicate and Out-of-Order Handling

`result_id` is a deterministic SHA-256 key over the versioned terminal result
semantics. The connector acceptance repository performs the sole initial
`READY -> terminal` compare-and-set. After a terminal state exists:

- equal terminal values produce `DUPLICATE_RESULT` and no update;
- incompatible terminal values produce `RESULT_CONFLICT` and no update; and
- no adapter path creates EmailEvent, ReplyEvent, or directly writes Lead.

This means a repeated result cannot create a second adapter-side event or
source update. The existing projection service remains responsible for an
authorized SendExecution source update and itself skips unchanged projection
values.

## Network Ambiguity

The bounded result representation deliberately preserves only the safe
terminal classification:

```text
Provider outcome: RETRYABLE_FAILURE
  -> error class: NETWORK
  -> safe code: BREVO_NETWORK_ERROR
  -> SendExecution: FAILED / NETWORK / BREVO_NETWORK_ERROR
```

This phase neither retries nor requeues and never turns an ambiguous timeout
into a resend decision. If the Provider may have accepted the request before a
timeout, delivery remains operationally ambiguous and must be resolved by a
separately approved reconciliation or evidence workflow.

## Security Review

The focused scan of the three result boundary surfaces found no occurrences of
API key, authorization header, bearer token, password, secret, recipient,
subject, or body markers:

- `send_execution_result_adapter.py`
- `SendExecutionResultAdapterService.php`
- `phase3c14_3_1c_apply_result.py`

The command/result model accepts only execution identity, provider attempt
identity, terminal status, safe failure class/code, occurrence time, and
deterministic result identity. It does not retain content, raw recipient,
credentials, authorization headers, Provider response payloads, or exception
detail.

## Tests

| Command | Result |
|---|---|
| `python -m unittest tests.test_phase3c14_3_1d_failure_projection_hardening tests.test_phase3c14_3_1c_result_adapter tests.test_phase3c14_3_1a_state_ownership` | PASS — 19 tests |
| C11/C12/C13/C14.3 focused lifecycle and regression suite | PASS — 99 tests |
| `python -m unittest discover -s crm-extension/tests -p test_*.py` | PASS — 75 tests |
| `python -m unittest discover -s chitu-connector/tests -p test_*.py` | PASS — 270 tests |
| `python -m py_compile tests/test_phase3c14_3_1d_failure_projection_hardening.py` | PASS |
| `python scripts/acceptance/phase3c14_3_1c_apply_result.py --help` | PASS — fixture-only command confirmed |
| Focused security marker scan | PASS — no matches |
| `git diff --check` | PASS — no whitespace errors in tracked changes; the working tree also contains unrelated pre-existing phase work. |

`python` is not on this machine's PATH, so the bundled workspace Python
runtime was used for each command above.

## Compatibility

| Boundary | Result | Evidence |
|---|---|---|
| C10 frozen modules | PASS | No C10 lifecycle, approval, idempotency, Provider, or scoring source changed. |
| C11 projection | PASS WITH RISKS | Result adapter saves only SendExecution; the existing projection service remains the Lead writer. The prior C11 cross-writer operational risk remains deferred. |
| C12 lifecycle | PASS | Existing Provider contract and Brevo classification tests pass unchanged. |
| C13 Worker | PASS | Worker, Queue, work store, and retry behavior were not changed; connector regression passed. |
| C14.2B Brevo handling | PASS | `BREVO_NETWORK_ERROR` retains the approved `RETRYABLE_FAILURE -> NETWORK -> FAILED` mapping, without automatic retry. |

## Remaining Risks

1. The C14.3.1C Python repository and explicit CLI are acceptance fixtures,
   not a durable production result transport. A process interruption can still
   lose a result before an authorized runtime caller submits it.
2. The PHP result service implements terminal/duplicate/conflict semantics,
   but is not yet connected to a production endpoint, scheduler, webhook, or
   durable inbox. This phase intentionally does not add one.
3. The PHP service recognizes equivalent replay from stored terminal values;
   a production-facing command path must carry and persist the deterministic
   `result_id` atomically before it can claim cross-process replay durability.
4. No higher-priority result policy exists. Contradictory terminal results are
   correctly blocked, but any future override must define priority, source
   authority, audit evidence, and projection semantics before implementation.

## C14.3 Freeze Readiness

**READY WITH RISKS** for a boundary/lifecycle freeze: the current contract
prevents forbidden terminal rollback, duplicate source update, direct Lead
write, retry side effect, and sensitive result-surface leakage within the
implemented C14.3.1 scope.

It is **not** ready to claim a durable production result ingestion path. The
next phase should be separately authorized, runtime-only synthetic acceptance
of the explicit CRM result service, followed by a narrowly designed durable
result inbox if cross-process delivery evidence is required. Do not add
automatic retries, resends, Worker writes, Provider changes, or real sends as
part of that work.
