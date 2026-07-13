# Phase3C02.2C-R Runtime End-to-End Verification & Cleanup

## 1. Verdict

**BLOCKED.** The committed single-job runner completed the real local EspoCRM REST success flow, replay protection, and the retryable Fake-provider failure flow. Cleanup is blocked because the existing `chitu_ai_connector` API role returns HTTP 403 for `DELETE /SearchJob/{id}`. No alternate identity, database access, or ACL change was attempted.

## 2. Environment

- Production workspace: `D:\EspoCRM-Production`.
- Local runtime: `D:\EspoCRM-Test`, EspoCRM `10.0.1` on `http://127.0.0.1:8080`.
- Provider: deterministic in-process Fake provider only; no real provider or outbound network provider was used.
- Runner baseline: commit `4650844`.

## 3. Preconditions

- The runner, repository adapter, and their test were clean relative to the committed baseline before execution.
- Live `SearchJob` metadata exposes required `name`, `status`, counters, timestamps, failure fields, and optional `strategy` link; no strategy link is required.
- Live `ProspectPool` metadata exposes the worker payload fields and `searchJob` link.
- No `SearchStrategy` was created, and no batch/generate-jobs action was invoked.

## 4. Runtime Health

- `espocrm`, `espocrm-daemon`, and `espocrm-db` were healthy.
- `espocrm-cron` was running.
- The existing port mapping was `8080 -> 80`.

## 5. API Authentication

- Authenticated `GET /api/v1/App/user` as API user `chitu_ai_connector` (type `api`).
- The API key was read only from the existing process environment and was never logged or written to disk.

## 6. Marker

- Primary marker: `CHITU_PHASE3C02_2C_R_RUNTIME_TEST`.
- All diagnostic SearchJobs used the marker in both `name` and `source`.

## 7. SearchStrategy Creation

- Not required and not performed. The live `SearchJob` contract permits direct queued-job creation without a `SearchStrategy` link.

## 8. SearchJob Creation

- Created one direct queued success job with `keyword=fake:deterministic` and all required counters initialized to zero.
- Created one isolated queued failure job with `keyword=fake:retryable-error`.
- No scheduler, run-next, batch, daemon, or second concurrent runner was used.

## 9. CLI Contract

- Executed `python -m chitu_connector.acquisition.runner run-job --job-id <id> --provider fake --output json` against local REST.
- Base URL, API key, timeout, TLS flag, and `PYTHONPATH` were process-scoped and removed after each invocation.
- Success exit code was `0`; replay exit code was `3`; deterministic provider failure exit code was `4`.

## 10. First Run Result

- The success job was claimed from `QUEUED` and finished `COMPLETED`.
- Safe JSON result reported `resultCount=3`, `insertedCount=2`, `duplicateCount=1`, `rejectedCount=0`, `partialPersistence=false`, and `finalStatusUncertain=false`.

## 11. SearchJob Runtime State

- Success lifecycle: `QUEUED -> RUNNING -> COMPLETED` with both timestamps populated.
- Persisted success counters: `resultCount=3`, `acceptedCount=2`, `rejectedCount=0`, `prospectCount=2`.
- Failure lifecycle: `QUEUED -> RUNNING -> FAILED`, with `FAKE_TRANSIENT`, `retryable=true`, no accepted or prospect counts, and no unsafe error expansion.

## 12. ProspectPool Runtime Records

- The success job created exactly two linked `ProspectPool` records.
- Both have `source=DETERMINISTIC_FAKE`, `queue=DISCOVERY`, `status=WAITING`, `researchStatus=NOT_STARTED`, `qualificationStatus=PENDING`, and `crmPushStatus=NOT_READY`.
- Websites were normalized to `https://alpha-3d.example` and `https://beta-distributor.example`.
- Notes contain the acquisition fingerprint, normalized domain, and `raw_payload_sha256`; they contain neither raw payload data nor provider result URLs.

## 13. Dedup

- The deterministic provider returned three raw candidates.
- Two distinct normalized domains persisted; the repeated Alpha domain was counted as one duplicate.
- The successful job state and stored records agree with the `3 / 2 / 1 / 0` result contract.

## 14. Replay

- Re-running the exact CLI command for the completed job returned exit code `3` and JSON `status=NOT_CLAIMED`, `claimed=false`, `previousStatus=COMPLETED`, and `failureStage=CLAIM`.
- The job counters remained unchanged and the linked `ProspectPool` count remained two.

## 15. Failure Path

- The retryable Fake-provider job returned exit code `4` and JSON `status=FAILED`, `failureStage=PROVIDER`, `errorCode=FAKE_TRANSIENT`, and `retryable=true`.
- The job persisted `FAILED` with explicit safe failure fields and created zero `ProspectPool` records.

## 16. Side Effects

- Valid marker queries immediately before cleanup returned zero matching records in `SearchStrategy`, `Lead`, `Account`, `Contact`, `Opportunity`, and `ResearchEvidence`.
- The local EspoCRM access log for the runner window shows only `PUT /SearchJob/{id}` and `POST /ProspectPool` writes by `Python-urllib`; it contains no runner write to Lead, Account, Contact, Opportunity, ResearchEvidence, Email, queue, campaign, task, sync service, or mail endpoint.
- `Email`, `Campaign`, and `Task` marker queries were denied by the same API role (HTTP 403); `EmailQueue` is unavailable in this runtime (HTTP 404). These limitations are recorded rather than bypassed.

## 17. Cleanup

- Cleanup enumerated only SearchJobs with `source=CHITU_PHASE3C02_2C_R_RUNTIME_TEST` and only pools linked to those job IDs.
- The first verified marker SearchJob deletion returned HTTP 403.
- No alternate user, ACL modification, direct database deletion, or non-marker deletion was attempted. No diagnostic record was removed after this failure.

## 18. Cleanup Verification

- Residual marker SearchJobs: `6a54b54a4f14bb42b` (`COMPLETED`, two pools) and `6a54b5e1acdef5f80` (`FAILED`, zero pools).
- Residual marker ProspectPools, linked only to the completed marker job: `6a54b593305a7d93b` and `6a54b5930e1636ca4`.
- Cleanup verification is therefore incomplete. The data is synthetic, marker-scoped, and explicitly identifiable for an authorized cleanup run.

## 19. Code Fixes

- None. The runtime adapter and runner mapping worked against actual live fields without modification.

## 20. Tests/Static

- Phase3C02.2C runner/adapter unittest suite: `13/13` passed.
- Full connector unittest suite: `89/89` passed.
- `git show --check` for the committed Phase3C02.2C runtime files passed.
- No current diff exists in the runner, REST adapter, or their test file.

## 21. Git Commit

- This report is committed separately as the Phase3C02.2C-R evidence artifact. Its commit hash is supplied by the enclosing task handoff.
- No connector code, CRM metadata, extension package, or prior phase file is staged by this task.

## 22. Limitations

- The API user can create, read, and update the tested acquisition entities but cannot delete `SearchJob` records.
- Email, campaign, and task marker queries are ACL-denied; EmailQueue is not available in this local runtime.
- The initial marker query helper had a PowerShell interpolation error and produced only route 404s; it performed no write. All later runtime verification and cleanup queries used corrected URI construction.

## 23. Phase3C02.2C Closure Readiness

- **NO.** Functional REST-loop evidence is positive, but the required marker cleanup cannot complete under the available API role.
- Closure requires an authorized marker-only cleanup of the four residual IDs above, followed by zero-residue verification.

## 24. Phase3C03 Readiness

- **NO.** Do not start Phase3C03 until the marker residue is removed by an authorized identity and the cleanup verification is repeated.

## 25. Cleanup Retry (Phase3C02.2C-R1)

### Authentication Class Used

- Re-confirmed the existing `chitu_ai_connector` API identity only for read validation; it was deliberately not used for deletion because its SearchJob DELETE denial is the known blocker.
- Attempted the project’s existing local Playwright administrator UI login flow using the already-configured container administrator environment credentials, entirely in process memory.
- The existing login flow returned HTTP `401` from `App/user` and remained on the login page. It did not establish an administrator session, and no credential value, token, password, or authorization header was printed or persisted.

### Deleted IDs

- None. No DELETE request was issued without a verified legal administrator session.

### GET 404 Verification

- Not applicable: each target remains visible to the existing read-only integration identity as HTTP `200`.
- Remaining `ProspectPool` IDs: `6a54b593305a7d93b`, `6a54b5930e1636ca4`.
- Remaining `SearchJob` IDs: `6a54b54a4f14bb42b`, `6a54b5e1acdef5f80`.

### Marker Zero-Residue Verification

- Not achieved because the four verified marker-scoped diagnostic records remain.
- No broad marker deletion, ACL change, API-role change, schema change, database access, or new diagnostic data was used.

### Final Phase3C02 Closure Readiness

- **NO.** A valid administrator API key, verified administrator integration identity, or repaired existing administrator login credential is required solely to delete the four exact IDs and repeat the specified GET/search checks.

### Final Phase3C03 Readiness

- **NO.** Phase3C03 remains blocked until the exact runtime residue is removed and zero-residue verification succeeds.
