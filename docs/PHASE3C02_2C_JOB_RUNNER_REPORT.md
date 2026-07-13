# Phase3C02.2C — Acquisition Single Job Runner & EspoCRM REST Persistence Adapter

## 1. Verdict

**CONDITIONAL PASS.** The single-job Fake Provider runner and EspoCRM REST
adapter are implemented and covered by offline tests. Shared-runtime validation
is **DEFERRED**; no credentials, Docker, browser, or diagnostic CRM data were
used in this phase.

## 2. Scope

This phase implements exactly one command:

```text
python -m chitu_connector.acquisition.runner run-job --job-id <SEARCH_JOB_ID>
```

It supports only `--provider fake` and `--output json|human`. It does not
implement batch execution, polling, scheduling, retry, daemon mode, a real
Provider, or multi-runner execution.

## 3. Preconditions

- Worker Core: `7db88c4`.
- Worker persistence hardening: `716e8da` and `b5b6277`.
- SearchStrategy foundation: `f294b50`.
- The adapter uses the hardened `AcquisitionStore` conditional-claim and
  conditional-update contract without changing Worker Core.

## 4. Files Changed

- `chitu-connector/chitu_connector/acquisition/espo_repository.py`
- `chitu-connector/chitu_connector/acquisition/runner.py`
- `chitu-connector/tests/test_phase3c02_2c_job_runner.py`
- `docs/PHASE3C02_2C_JOB_RUNNER_REPORT.md`

No CRM extension, 1A, SearchJob metadata, manifest, deployment archive,
ChituSyncService, email, research, scoring, or workflow file was changed.

## 5. CLI Contract

`run-job --job-id` is required. `fake` is the only accepted provider; another
provider is rejected before configuration loading or EspoCRM access. JSON is
the default stdout format and contains only safe result counters/status fields.
Human mode is a one-line summary. No logs or output include API-key or request
header values.

## 6. Configuration

| Variable | Required | Default |
| --- | --- | --- |
| `ESPOCRM_BASE_URL` | Yes | None |
| `ESPOCRM_API_KEY` | Yes | None |
| `ESPOCRM_TIMEOUT` | No | `30` seconds |
| `ESPOCRM_VERIFY_TLS` | No | `true` |

Missing/invalid configuration returns `CONFIG_ERROR` with exit code `2` before
repository construction or network access. URL, API key, and credentials are
never hard-coded or emitted.

## 7. EspoCRM Repository Contract

`EspoAcquisitionRepository` uses standard-library `urllib` only and implements:

1. `fetch_search_job` through `GET SearchJob/{id}`;
2. `claim_search_job` through read, conditional local check, `PUT RUNNING`, and
   post-write read confirmation;
3. `update_search_job` with expected status/version checks before write and a
   terminal-status confirmation read;
4. `has_prospect` through a `ProspectPool` source-plus-website query;
5. `create_prospect` through `POST ProspectPool` with a strict existing-field
   allowlist.

HTTP `401`/`403` are non-retryable. `429`, `5xx`, connection failures, and
timeouts are retryable. `404` is a normal `None` result only for SearchJob
fetch; malformed/non-object JSON is a safe non-retryable persistence error.
No response body, traceback, or credential is included in `PersistenceError`.

## 8. SearchJob Field Mapping

The adapter reads only existing fields: `id`, `status`, `keyword`, `country`,
`product`, `source`, `queryFingerprint`, `startedAt`, `completedAt`, counters,
failure fields, and `modifiedAt` as the optional version token.

The Worker writes only existing `SearchJob` fields: `status`, `startedAt`,
`completedAt`, `resultCount`, `acceptedCount`, `rejectedCount`,
`prospectCount`, `errorMessage`, and `failureReason`. No CRM metadata was
changed. `persona`, a persisted adapter result limit, a dedicated attempt count,
and server-enforced CAS/ETag are not currently available to this adapter.

## 9. Claim Semantics

The runner first fetches the target SearchJob. Only `QUEUED` reaches the Worker.
The adapter then performs GET-then-PUT `RUNNING`, re-reads the job, and only
returns a successful `ClaimResult` when the confirmed status is `RUNNING`.

This is correct only for the declared **single-runner MVP**. EspoCRM has no
dedicated claim action or confirmed ETag/If-Match contract here, so a theoretical
cross-process race window remains. The implementation does not claim atomicity,
does not use a database connection or local lock, and does not support two
Runners.

## 10. Single-Runner Limitation

The same process does not re-run a terminal job: a second invocation observes a
non-`QUEUED` status and exits `3` without provider or ProspectPool writes.
Multi-runner deployment requires a server-side conditional claim action or
server-enforced uniqueness/CAS and is out of scope.

## 11. ProspectPool Field Mapping

Worker candidates map only to existing fields: `name`, `externalProspectId`,
`source`, `sourceUrl`, `website`, `country`, `queue=DISCOVERY`, status fields,
`searchJobId`, and a safe digest-only note. The raw provider payload is not
persisted. `SearchStrategy` is not written because ProspectPool has no current
direct relation. No Lead, Account, Contact, Opportunity, ResearchEvidence, or
email record is created.

## 12. Idempotency

The Worker retains its in-job normalized-domain fingerprint dedupe. The REST
adapter additionally queries existing ProspectPool records by provider `source`
and normalized `website` before create. This is best-effort persistence
idempotency for a single runner; CRM currently has no dedicated fingerprint
field or unique constraint for this adapter to enforce across runners.

## 13. Error Classification

| Condition | Code/Result | Exit |
| --- | --- | --- |
| Missing configuration or invalid provider | `CONFIG_ERROR` / `INVALID_ARGUMENT` | 2 |
| Missing or non-queued job | `JOB_NOT_FOUND` / `JOB_NOT_QUEUED` | 3 |
| Claim/read/write persistence failure | `ESPO_READ_ERROR` / `ESPO_WRITE_ERROR` | 5 |
| Fake Provider failure | Worker provider code | 4 |
| Partial persistence or uncertain terminal status | Worker result flags | 6 |
| Unexpected runner failure | `UNEXPECTED_ERROR` | 1 |
| Completed (including empty result) | `COMPLETED` | 0 |

## 14. Exit Codes

Exit values are stable constants in `runner.py`: `0` success, `1` unexpected,
`2` input/config, `3` not claimable, `4` provider failure, `5` EspoCRM
persistence failure, and `6` partial/uncertain persistence.

## 15. Tests Added

`test_phase3c02_2c_job_runner.py` adds 13 offline tests for configuration,
provider rejection, JSON safety, success/empty/error/replay paths, partial
persistence, terminal-job rejection, REST fetch/error/claim/update behavior,
ProspectPool allowlisting, and static boundary checks.

## 16. Full Test Results

| Suite | Result |
| --- | --- |
| Phase3C02.2C runner/adapter | 13 passed |
| Phase3C02.2B worker core | 10 passed |
| Phase3C02.2B.1 hardening | 8 passed |
| Full connector suite | 89 passed |
| Extension structure suite | 38 passed |

## 17. Static Safety Checks

- Python compilation passed for both new modules and the new test.
- `git diff --check` passed.
- Forbidden-side-effect scan passed: no ChituSyncService, real provider,
  scheduler, daemon, batch command, Lead/Opportunity/ResearchEvidence action,
  or infinite loop appears in the new production files.
- Secret-assignment scan passed.
- No dependency was added.

## 18. Runtime Validation

**DEFERRED.** The unit tests use fake HTTP transport and in-memory persistence.
The shared `D:\EspoCRM-Test` runtime was not reserved for this task, and no API
key or diagnostic SearchJob was accessed. Consequently no CRM record was
created, updated, or cleaned up. A later isolated run must create one marked
`QUEUED` SearchJob, execute only the Fake Provider command, verify the
`QUEUED → RUNNING → COMPLETED` path plus replay rejection, and remove all
diagnostic SearchJob/ProspectPool records.

## 19. Runtime Cleanup

Not applicable: runtime validation was deferred and no runtime data exists from
this phase.

## 20. Side-Effect Boundary

The only allowed runtime network target is the configured EspoCRM REST base URL.
`DeterministicFakeProvider` remains network-free. The runner does not invoke
ChituSyncService, a real search provider, CRM sync routes, email, or a
background service.

## 21. Git Commit Result

Main implementation commit: `4650844 Phase3C02.2C add single job runner and Espo REST adapter`.
This report is committed separately after that implementation commit.

## 22. Known Limitations

- No real REST runtime exercise in this phase.
- No real Provider, provider credential, retry loop, recovery worker, or batch
  scheduler.
- GET-then-PUT claim has a theoretical race window.
- REST idempotency is best-effort; a database unique constraint or server-side
  action is required for multi-runner certainty.
- ProspectPool lacks a direct SearchStrategy relation and a dedicated persisted
  candidate fingerprint field.

## 23. Readiness for First Real Provider Adapter

**NO.** A real Provider adapter must wait for an isolated Fake Provider REST
runtime validation and a dedicated review of provider credentials, provider
rate limits, and multi-runner/claim guarantees. This phase deliberately leaves
those boundaries closed.
