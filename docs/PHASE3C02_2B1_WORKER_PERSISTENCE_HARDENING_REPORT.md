# Phase3C02.2B.1 — Worker Core Persistence Hardening

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Verdict:** **PASS** — Worker Core persistence boundaries are hardened offline and are ready for a narrowly scoped Runner/REST-adapter phase.

## 1. Scope

This follow-up hardens only the committed Phase3C02.2B Worker Core (`7db88c4`). It does not add a CLI, runner, EspoCRM REST adapter, real provider, CRM extension API, automatic retry, or shared-runtime interaction.

The reviewed scope was limited to the three blockers in `PHASE3C02_2B_WORKER_CORE_REVIEW.md`:

- **B01:** non-`ProviderError` failures escaped and could leave a job RUNNING;
- **B02:** partial ProspectPool persistence and failed completion writes had no explicit recovery result;
- **B03:** the Store protocol could not express conditional claim or CAS-ready updates.

## 2. Files Changed

- `chitu-connector/chitu_connector/acquisition/models.py`
- `chitu-connector/chitu_connector/acquisition/worker.py`
- `chitu-connector/chitu_connector/acquisition/__init__.py`
- `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py`
- `chitu-connector/tests/test_phase3c02_2b1_worker_persistence_hardening.py` (new)
- `docs/PHASE3C02_2B1_WORKER_PERSISTENCE_HARDENING_REPORT.md` (this report)

No `crm-extension`, manifest, deployment archive, provider, connector-sync, scoring, research, or email file was changed.

## 3. Error Model

`ProviderError` remains unchanged. A new `PersistenceError(code, safe_message, retryable)` represents Store/repository/REST persistence failures without carrying a response body, credential, or traceback.

Unexpected exceptions are caught at the Worker boundary and returned as `UNEXPECTED_WORKER_ERROR`, retryable by default. Their persisted summary is the exception class only, never `str(error)` or a traceback. Safe summaries are whitespace-normalized, limited to 240 characters, and suppress strings containing credential indicators such as authorization, bearer, token, secret, or password.

## 4. Claim Contract

`AcquisitionStore.claim_search_job()` replaces the implicit queued claim:

```python
claim_search_job(job_id, *, expected_status, started_at, expected_version=None) -> ClaimResult
```

`ClaimResult` reports `claimed`, the claimed job, previous/current status, a non-sensitive reason, and an optional version token. Store updates also accept `expected_status` and `expected_version`.

The Worker requests `expected_status="QUEUED"`; it does not perform a read-then-unconditional RUNNING update. The in-memory Store enforces the condition. A future adapter can implement the same contract with a dedicated claim action, If-Match/ETag, or best-effort compare-and-set.

Non-queued, missing, or conflicting jobs return a structured `NOT_CLAIMED` result and never call the Provider or write ProspectPool. A claim persistence failure returns `CLAIM_FAILED` with `claim_failed=True` and does not assume the job is RUNNING.

## 5. State Transition Rules

| Starting status | Worker action |
| --- | --- |
| `QUEUED` | Conditionally claim to `RUNNING`, then execute once. |
| `RUNNING` | `NOT_CLAIMED`; no Provider or ProspectPool action. |
| `COMPLETED` | `NOT_CLAIMED`; replay creates no duplicate records. |
| `FAILED` | `NOT_CLAIMED`; this phase performs no automatic retry. |
| `CANCELLED` | `NOT_CLAIMED`; no execution. |

After a successful claim, all failure paths make a best-effort conditional `RUNNING → FAILED` update. If that update fails, the execution result has `final_status_uncertain=True` and `failure_persistence_failed=True`; no exception escapes the Worker.

## 6. Partial Persistence Handling

ProspectPool persistence is explicitly **fail-fast**. On the first `create_prospect` failure, the Worker stops processing later candidates, retains accurate counts for completed inserts/duplicates/rejections, and attempts to mark the SearchJob FAILED.

`JobExecutionResult.partial_persistence` is true only when at least one ProspectPool record was confirmed written before the failure. The Worker does not delete confirmed records and does not pretend remote REST writes are transactional. Existing provider/domain deduplication remains the replay guard.

## 7. Completion and Failure Update Failures

If all ProspectPool writes succeed but `COMPLETED` persistence fails, the Worker preserves those records, sets `completion_persistence_failed=True`, and attempts a conditional FAILED update. A successful FAILED write returns `final_status="FAILED"`; a failed FAILED write returns `final_status=None` and `final_status_uncertain=True`.

## 8. JobExecutionResult Changes

The existing result fields are preserved. Added fields are:

- `error_summary`, `previous_status`, `final_status`, `provider`
- `partial_persistence`, `completion_persistence_failed`, `failure_persistence_failed`
- `final_status_uncertain`, `claim_failed`, `failure_stage`
- `started_at`, `completed_at`

These fields expose recoverable state to a future runner without becoming a large event object. Time values are execution metadata only and never participate in dedupe fingerprints.

## 9. Backward Compatibility

The deterministic fake Provider remains offline and preserves its ordinary, empty, retryable-error, and non-retryable-error modes. Existing result positional fields remain in their original order. The existing in-memory test Store was updated to the explicit conditional-claim/update contract.

## 10. Tests Added and Results

New fault-injection coverage verifies:

- conditional QUEUED claims and no Provider call after a rejected claim;
- claim persistence failure as a structured result;
- retryable/non-retryable `ProviderError` and generic unexpected-error handling;
- safe exception summarization;
- first-write and partial-write fail-fast behavior with accurate counts;
- completion-write failure without deleting written prospects;
- FAILED-update failure with an uncertain final status;
- normalization failure without an uncaught exception.

| Check | Result |
| --- | ---: |
| original C02.2B + new C02.2B.1 isolated tests | 18 passed |
| complete `chitu-connector` suite | 76 passed |
| CRM extension structural suite | 38 passed |
| Python compilation of changed source/tests | passed |
| production acquisition forbidden-side-effect scan | no matches |
| `git diff --check` | passed (line-ending warnings only) |

## 11. Static Safety and Side-Effect Boundary

Changed production acquisition files contain no network client, HTTP, SMTP, subprocess, real Provider, `ChituSyncService`, Lead, Opportunity, or ResearchEvidence reference. No credentials, full exception text, traceback, or raw provider payload are persisted. No shared EspoCRM runtime, Docker service, browser, or external Provider was accessed.

## 12. Blocker Resolution

| Blocker | Result |
| --- | --- |
| B01 — unhandled non-Provider errors | **Resolved.** All post-claim exceptions return structured failures and attempt a safe FAILED update. |
| B02 — partial persistence ambiguity | **Resolved.** Fail-fast semantics, exact counters, partial/completion/final-status flags, and confirmed-write preservation are implemented. |
| B03 — conditional claim/CAS gap | **Resolved at Worker Core protocol level.** `ClaimResult`, expected status, and optional version token reserve atomic/CAS semantics for the adapter. |

## 13. Remaining Limitations

This is still a single-runner Worker Core. It deliberately does not implement a REST adapter, actual distributed lock, ETag transport, lease/heartbeat, RUNNING timeout recovery, attempt counter, automatic FAILED-to-QUEUED retry, batch runner, CLI, or real Provider. The future adapter must realize the conditional contract against EspoCRM persistence.

## 14. Git Commit Result

Worker Core hardening, both Worker test files, and this initial report were committed by explicit path as `716e8da Phase3C02.2B.1 harden worker persistence boundaries`. No parallel `crm-extension`, C02.1A, C02.2B-R review, or C02.2C-A design file was included.

## 15. Readiness for Phase3C02.2C

**YES.** The Worker Core exposes the failure, claim, and persistence outcome information required by a minimal single-runner Runner/REST-adapter implementation. The adapter must implement the reserved conditional-claim/CAS behavior; multi-runner robustness remains a later concern.
