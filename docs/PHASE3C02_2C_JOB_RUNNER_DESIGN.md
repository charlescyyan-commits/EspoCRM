# Phase3C02.2C-A — Acquisition Job Runner Design Audit

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Task:** Phase3C02.2C-A — Design Audit (read-only)  
**Verdict:** **GO** — No architectural blocker; single-session implementation viable

---

## 1. Executive Recommendation

**GO.** The chitu-connector package has a clean, isolated Worker Core that is ready to be driven by a thin CLI runner backed by an EspoCRM persistence adapter. No CRM extension modification is required for C02.2C. The runner can be implemented as a single new module (`runner.py`) plus an EspoCRM REST adapter (`espo_repository.py`) and a test file. All dependencies already exist in the codebase (Worker Core, Fake Provider, `ProspectingConnectorClient`-style REST pattern).

**Recommended implementation approach:**
1. Create `chitu-connector/chitu_connector/acquisition/runner.py` — argparse CLI entry point
2. Create `chitu-connector/chitu_connector/acquisition/espo_repository.py` — EspoCRM REST adapter implementing `AcquisitionStore`
3. Create `chitu-connector/tests/test_phase3c02_2c_job_runner.py` — integration tests
4. Zero modifications to existing files

**Exact files (all new):**
- `chitu-connector/chitu_connector/acquisition/runner.py`
- `chitu-connector/chitu_connector/acquisition/espo_repository.py`
- `chitu-connector/tests/test_phase3c02_2c_job_runner.py`
- `docs/PHASE3C02_2C_JOB_RUNNER_REPORT.md` (post-implementation)

**No unresolved architecture blocker. Ready for Phase3C02.2C implementation after commit separation.**

---

## 2. Existing Connector Entry Points

### 2.1 Package Structure

```
D:\EspoCRM-Production\
├── chitu_connector/                          # Workspace bridge (re-exports from chitu-connector/)
│   └── __init__.py                           # __path__ bridge to chitu-connector/chitu_connector/
├── chitu-connector/                          # Actual Python package
│   ├── pyproject.toml                        # setuptools, no console_scripts, no CLI deps
│   └── chitu_connector/
│       ├── __init__.py                       # "workspace package" docstring only
│       ├── acquisition/                      # Worker Core (C02.2B)
│       │   ├── __init__.py                   # Re-exports Worker, Provider, models
│       │   ├── worker.py                     # AcquisitionWorker + AcquisitionStore protocol
│       │   ├── provider.py                   # SearchProvider protocol
│       │   ├── models.py                     # All data contracts
│       │   ├── normalization.py              # Domain/name normalization
│       │   └── fake_provider.py              # DeterministicFakeProvider
│       ├── espocrm_sync/                     # Existing sync adapter
│       │   ├── real_client.py                # LocalEspoCRMClient (urllib + X-Api-Key / Espo-Authorization)
│       │   ├── connector_api.py              # ProspectingConnectorClient (urllib + X-Api-Key)
│       │   └── ...
│       └── vendored/                         # Domain contracts
└── crm-extension/                            # EspoCRM PHP extension (separate system)
```

### 2.2 Entry Point Analysis

| Aspect | Current State |
|--------|--------------|
| `pyproject.toml` `[project.scripts]` | **Not defined** — no console_scripts |
| `__main__.py` | **Does not exist** anywhere in chitu-connector |
| CLI framework dependency | **None** — no click, typer, fire, or argparse usage found |
| Existing CLI modules | **None** |
| How tests are run | `python -m pytest` directly against the package |
| How connector is used | Imported as a library by other Python code |

### 2.3 Configuration Loading

- **No unified config module.** Each component reads environment variables directly.
- `LocalEspoCRMClient.from_environment()` reads: `ESPOCRM_TEST_ENV`, `ESPOCRM_TEST_URL`, `ESPOCRM_TEST_API_KEY`, `ESPOCRM_TEST_USERNAME`, `ESPOCRM_ADMIN_USERNAME`, `ESPOCRM_TEST_PASSWORD`, `ESPOCRM_ADMIN_PASSWORD`
- `ProspectingConnectorClient.__init__()` takes `base_url`, `api_key`, `timeout_seconds` as constructor args
- No `.env` file loader, no configparser, no YAML config

### 2.4 HTTP Client Patterns

Two patterns exist, both using stdlib `urllib`:
1. **`LocalEspoCRMClient`** (`real_client.py`): Full EspoCRM REST client with CRUD, auth, preflight. Uses `urllib.request` with `X-Api-Key` or `Espo-Authorization` headers. Strictly localhost-only (`http://localhost:8080`).
2. **`ProspectingConnectorClient`** (`connector_api.py`): Narrow connector for `/Prospecting/sync/*` endpoints. Uses `urllib.request` with `X-Api-Key`.

### 2.5 Recommendation: Entry Point Design

**Use `python -m chitu_connector.acquisition.runner`** — module-based invocation. This is the simplest correct approach:

- **No `console_scripts` entry in `pyproject.toml`** — avoids modifying the package manifest
- **No `__main__.py`** — avoids hijacking the package's default behavior
- **No CLI framework dependency** — use stdlib `argparse` only
- **Consistent with existing patterns** — tests are already run via `python -m pytest`

Rationale: The runner is a developer/operator tool, not a user-facing CLI. Module invocation (`-m`) is the standard Python pattern for package-adjacent scripts. Adding console_scripts or a CLI framework would be over-engineering for a single-command tool.

---

## 3. Recommended Architecture

### 3.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│  CLI / Command Layer (runner.py)                         │
│  - argparse: --job-id, --provider, --dry-run, --output   │
│  - Reads env vars for EspoCRM connection                  │
│  - Formats and prints JSON result to stdout               │
│  - Sets exit code                                        │
│  - NO domain logic, NO HTTP calls, NO CRM writes          │
└──────────────────────┬──────────────────────────────────┘
                       │ constructs
┌──────────────────────▼──────────────────────────────────┐
│  Config (inline in runner, env-var based)                │
│  - ESPOCRM_BASE_URL, ESPOCRM_API_KEY                     │
│  - timeout, TLS verify                                   │
│  - NO provider credentials (fake only)                   │
└──────────────────────┬──────────────────────────────────┘
                       │ injects into
┌──────────────────────▼──────────────────────────────────┐
│  EspoCRM Persistence Adapter (espo_repository.py)        │
│  - Implements AcquisitionStore protocol                  │
│  - HTTP calls to EspoCRM REST API                        │
│  - claim_queued_job, update_search_job,                  │
│    has_prospect, create_prospect                         │
│  - NO provider logic, NO normalization, NO scoring       │
└──────────────────────┬──────────────────────────────────┘
                       │ injected into
┌──────────────────────▼──────────────────────────────────┐
│  Worker Core (worker.py — existing, UNCHANGED)           │
│  - AcquisitionWorker.execute_job(search_job_id)          │
│  - Calls store.claim_queued_job → provider.search        │
│    → normalize → dedup → store.create_prospect           │
│    → store.update_search_job                             │
│  - NO CLI, NO HTTP, NO EspoCRM knowledge                 │
└──────────────────────┬──────────────────────────────────┘
                       │ calls
┌──────────────────────▼──────────────────────────────────┐
│  Provider (fake_provider.py — existing, UNCHANGED)       │
│  - DeterministicFakeProvider                             │
│  - Network-free, deterministic                           │
│  - NO CRM writes, NO real search                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Result Formatter (inline in runner.py)                  │
│  - Converts JobExecutionResult → JSON stdout             │
│  - Adds timing, safe error context                       │
│  - NO status decisions, NO CRM knowledge                 │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Layer Responsibilities

| Layer | Input | Output | Network? | CRM Write? | Business Rules? |
|-------|-------|--------|:---:|:---:|:---:|
| CLI | `sys.argv` + env vars | JSON to stdout, exit code | No | No | No |
| Config | env vars | `EspoCRMRepository` constructor args | No | No | No |
| EspoCRM Adapter | method calls from Worker | HTTP responses to Worker | **Yes** | **Yes** | No |
| Worker Core | `search_job_id` | `JobExecutionResult` | No | Via store | Dedup, normalization |
| Provider | `SearchRequest` | `ProviderResult` | No (fake) | No | No |
| Result Formatter | `JobExecutionResult` + timing | JSON string | No | No | No |

---

## 4. CLI Contract

### 4.1 Command Form

```bash
python -m chitu_connector.acquisition.runner run-job \
    --job-id <SearchJob.id> \
    [--provider fake] \
    [--dry-run] \
    [--output json] \
    [--timeout 30] \
    [--verbose]
```

### 4.2 Parameters

| Parameter | Required | Default | Description |
|-----------|:---:|---------|-------------|
| `--job-id` | **Yes** | — | EspoCRM SearchJob ID to execute |
| `--provider` | No | `fake` | Provider name; only `fake` accepted in C02.2C |
| `--dry-run` | No | `False` | Fetch + validate job, print what WOULD happen, exit 0 without modifying CRM |
| `--output` | No | `json` | Output format; only `json` accepted in C02.2C (reserve `human` for future) |
| `--timeout` | No | `30` | HTTP request timeout in seconds |
| `--verbose` | No | `False` | Emit structured log events to stderr |

**Parameter justification:**
- `--provider fake` default: there is only one provider in scope; the flag exists for future `google`, `apify` etc.
- `--dry-run`: essential safety mechanism — validates the job is QUEUED and reachable without side effects
- `--output json`: machine-readability is the primary use case; `human` is deferred
- `--timeout`: protects against hung CRM connections
- `--verbose`: enables structured logging for debugging without polluting stdout JSON

### 4.3 Exit Codes

| Code | Meaning | When |
|:---:|---------|------|
| 0 | Success | Job completed (results written) or dry-run validation passed |
| 1 | Input error | Missing `--job-id`, invalid `--provider`, unknown flag |
| 2 | Config error | Missing `ESPOCRM_BASE_URL` or `ESPOCRM_API_KEY` |
| 3 | Job not claimable | Job not found, not QUEUED (already RUNNING/COMPLETED/FAILED/CANCELLED) |
| 4 | Provider failure (retryable) | Rate limit, transient provider error |
| 5 | Provider failure (non-retryable) | Invalid request, auth failure at provider |
| 6 | CRM read failure | Cannot fetch job, network error, 5xx from EspoCRM |
| 7 | CRM write failure | Cannot update job status, cannot create prospects |
| 8 | Unexpected error | Unhandled exception, process crash |

**Design rationale:**
- Exit code 0 for dry-run: the validation succeeded; "no side effects" is the expected outcome
- Exit code 3 for non-claimable: distinguished from CRM errors so scripts can skip these gracefully
- Exit codes 4/5 separated: scripts can retry code 4 but not code 5
- Exit codes 6/7 separated: distinguishes read vs write failures for debugging

### 4.4 Standard Output JSON Structure

```json
{
  "jobId": "abc123",
  "previousStatus": "QUEUED",
  "finalStatus": "COMPLETED",
  "provider": "DETERMINISTIC_FAKE",
  "resultCount": 3,
  "insertedCount": 2,
  "duplicateCount": 1,
  "rejectedCount": 0,
  "retryable": null,
  "errorCode": null,
  "errorSummary": null,
  "durationMs": 1234,
  "dryRun": false
}
```

**Excluded from output (by design):**
- API keys, Authorization headers
- Full raw provider payload
- Full exception tracebacks (safe error summary only)
- CRM user passwords
- Internal HTTP request/response bodies

### 4.5 Dry-Run Output

When `--dry-run` is specified:

```json
{
  "jobId": "abc123",
  "previousStatus": "QUEUED",
  "finalStatus": null,
  "provider": "DETERMINISTIC_FAKE",
  "resultCount": null,
  "insertedCount": null,
  "duplicateCount": null,
  "rejectedCount": null,
  "retryable": null,
  "errorCode": null,
  "errorSummary": null,
  "durationMs": 234,
  "dryRun": true,
  "claimable": true
}
```

Dry-run performs:
1. Fetch job from EspoCRM
2. Verify status == QUEUED
3. Print result
4. Exit 0

It does NOT: claim the job, call the provider, create prospects, or write any CRM data.

---

## 5. Persistence Adapter Contract

### 5.1 Design

`EspoCRMRepository` implements the existing `AcquisitionStore` protocol from `worker.py`. It wraps EspoCRM's standard REST API (`/api/v1/SearchJob/{id}`, `/api/v1/ProspectPool`).

The adapter uses the same HTTP pattern as `ProspectingConnectorClient`:
- `urllib.request` (no new dependency)
- `X-Api-Key` header
- JSON request/response bodies

### 5.2 Method Specifications

#### `fetch_job(job_id: str) -> dict | None`

| Property | Value |
|----------|-------|
| HTTP method | `GET` |
| Endpoint | `/api/v1/SearchJob/{job_id}` |
| Success code | 200 |
| Not found | 404 → return `None` |
| Returns | Full SearchJob record as dict, or `None` |
| Idempotent | Yes |
| Failure handling | Network error → raise `EspoCRMRepositoryError` |

#### `claim_queued_job(job_id: str, started_at: str) -> dict | None`

**This is the critical atomicity boundary.** The method must:

1. `GET /api/v1/SearchJob/{job_id}` — read current state
2. Verify `status == "QUEUED"`
3. `PUT /api/v1/SearchJob/{job_id}` with `{"status": "RUNNING", "startedAt": started_at}`
4. Return the updated job dict, or `None` if step 2 failed

| Property | Value |
|----------|-------|
| HTTP methods | `GET` → `PUT` |
| Race window | **Yes** — between GET and PUT, another runner could also GET QUEUED |
| Mitigation | Acceptable in C02.2C (single-runner manual invocation); document limitation |
| Returns | Updated job dict (with status=RUNNING), or `None` if not QUEUED |
| Idempotent | **No** — second call on same job returns `None` because status is now RUNNING |
| Failure handling | Network error on GET → raise; network error on PUT → raise; status ≠ QUEUED → return `None` |

**Race window assessment:**
- Standard EspoCRM REST API does NOT support conditional updates (no `If-Match` header, no `WHERE status = 'QUEUED'` in PUT)
- GET-then-PUT is the best available without a custom API action
- For C02.2C (manual single-runner invocation), the race window is academic
- For multi-runner production use, a custom `POST /SearchJob/{id}/claim` action should be implemented

#### `update_search_job(job_id: str, values: dict) -> None`

| Property | Value |
|----------|-------|
| HTTP method | `PUT` |
| Endpoint | `/api/v1/SearchJob/{job_id}` |
| Request body | `values` dict (status, completedAt, resultCount, acceptedCount, rejectedCount, prospectCount, errorMessage, failureReason) |
| Success codes | 200 |
| Idempotent | Yes (writing same COMPLETED values is safe) |
| Failure handling | Network error → raise `EspoCRMRepositoryError` |

#### `has_prospect(provider_name: str, normalized_domain: str) -> bool`

| Property | Value |
|----------|-------|
| HTTP method | `GET` |
| Endpoint | `/api/v1/ProspectPool` |
| Query params | `where[0][attribute]=source`, `where[0][value]={provider_name}`, `where[1][type]=contains`, `where[1][attribute]=website`, `where[1][value]={normalized_domain}`, `maxSize=1` |
| Returns | `True` if any record found, `False` otherwise |
| Idempotent | Yes |
| Performance note | `website` field does NOT have a unique index; this is a full-scan-on-text query. Acceptable for C02.2C volumes; index recommended before production |
| Failure handling | Network error → raise `EspoCRMRepositoryError` |

**Note on website matching:** The Worker constructs `website` as `https://{normalized_domain}`. The `has_prospect` query should use a `contains` filter on `website` matching the normalized domain. An exact match would fail because `website` stores the full `https://` URL. The current `externalProspectId` index is on the wrong field for domain dedup.

#### `create_prospect(values: dict) -> None`

| Property | Value |
|----------|-------|
| HTTP method | `POST` |
| Endpoint | `/api/v1/ProspectPool` |
| Request body | ProspectPool field values (see §7 field mapping) |
| Success code | 201 or 200 |
| Idempotent | **Not guaranteed** — same candidate posted twice creates duplicate records |
| Mitigation | `has_prospect` check before each `create_prospect` call |
| Failure handling | Network error → raise `EspoCRMRepositoryError`; 409 Conflict → escalate |

#### Methods NOT implemented in C02.2C

| Method | Reason |
|--------|--------|
| `release_or_recover_job` | Deferred to Recovery phase; C02.2C has no auto-retry |
| `get_existing_fingerprints` | Worker uses `has_prospect` per-candidate; batch fingerprint query is a future optimization |
| `mark_job_running` | Covered by `claim_queued_job` (combined atomic intent) |
| `mark_job_completed` | Covered by `update_search_job` |
| `mark_job_failed` | Covered by `update_search_job` |
| `upsert_prospect` | EspoCRM REST has no native upsert; `has_prospect` + `create_prospect` is the C02.2C pattern |

### 5.3 Conditional Update Analysis

**Current EspoCRM REST API capability:** Standard CRUD only. No field-level conditional update, no `PATCH` with preconditions, no `WHERE` clause on `PUT`.

**Evidence:** `LocalEspoCRMClient.update_record()` does a plain `PUT /api/v1/{entityType}/{id}` with body. No conditional mechanism exists in the existing client code or the EspoCRM standard REST API.

**Options for safe claim:**

| Option | Mechanism | C02.2C Viable? | Production Viable? |
|--------|-----------|:---:|:---:|
| A: GET + PUT | Read status, PUT if QUEUED | **Yes** | Race window exists |
| B: Custom claim action | `POST /SearchJob/{id}/claim` with server-side status check + update in one transaction | Overkill | **Yes** |
| C: Database lock | EspoCRM ORM-level lock | Not available via REST | Requires PHP code |
| D: Local file lock | `fcntl`/`msvcrt` lock file on runner host | Adds complexity | Only single-machine |

**Recommendation:** Option A for C02.2C. Document the race window as a known limitation. If a custom claim action is needed for production, create it as a separate task (C02.2C1 — EspoCRM Claim Action).

---

## 6. Job Claim Strategy

### 6.1 Claim Semantics

1. **Only QUEUED is claimable.** RUNNING, COMPLETED, FAILED, CANCELLED → `NOT_CLAIMED`
2. **Claim transitions status to RUNNING** and sets `startedAt`
3. **One runner at a time** — Claim failure blocks all downstream work (no Provider call, no ProspectPool writes)
4. **No auto-execute of terminal jobs** — COMPLETED/FAILED/CANCELLED cannot be re-executed without manual reset

### 6.2 Recommended Approach: GET-then-PUT (Option A)

```python
def claim_queued_job(self, job_id: str, started_at: str) -> dict | None:
    # Step 1: Read
    job = self._get(f"SearchJob/{job_id}")
    if job is None:
        return None  # Not found (404)
    if job.get("status") != "QUEUED":
        return None  # Not claimable
    
    # Step 2: Claim (race window here)
    self._put(f"SearchJob/{job_id}", {
        "status": "RUNNING",
        "startedAt": started_at,
    })
    
    # Step 3: Return updated state
    job["status"] = "RUNNING"
    job["startedAt"] = started_at
    return job
```

**Why this is acceptable for C02.2C:**
- Manual single-runner invocation → no concurrent claimers
- The Worker's `execute_job` already guards: if `claim_queued_job` returns `None`, it returns `NOT_CLAIMED` without side effects
- Even if two runners race, the second PUT overwrites the first's RUNNING with RUNNING (no data corruption)
- Both runners would call the Provider, but the `has_prospect` dedup prevents duplicate ProspectPool inserts

### 6.3 Future: Custom Claim Action (Option B, NOT in C02.2C)

If multi-runner production deployment requires true atomic claim:

```
POST /api/v1/SearchJob/{id}/claim
```

Server-side (PHP):
```php
// In claim action:
$job = $em->getEntity('SearchJob', $id);
if (!$job || $job->get('status') !== 'QUEUED') {
    return ResponseComposer::json(['claimed' => false, 'reason' => 'NOT_QUEUED']);
}
$job->set(['status' => 'RUNNING', 'startedAt' => $startedAt]);
$em->saveEntity($job);
return ResponseComposer::json(['claimed' => true, 'job' => $job->getValues()]);
```

**Defer to separate task C02.2C1 if needed.** The custom action requires:
- New `Api/PostSearchJobClaim.php`
- Route registration in `routes.json`
- ACL check on SearchJob edit
- Extension package rebuild

This is a ~1 session task. Not required for C02.2C MVP.

---

## 7. ProspectPool Field Mapping

### 7.1 Worker → ProspectPool Mapping

The Worker Core (`worker.py` lines 72-92) already constructs a dict for `create_prospect`. Here is the complete mapping against actual ProspectPool entity fields:

| Worker Dict Key | ProspectPool Field | Type | Exists? | Notes |
|-----------------|-------------------|------|:---:|-------|
| `name` | `name` | varchar(255) | **Yes** | `NormalizedCandidate.company_name` |
| `externalProspectId` | `externalProspectId` | varchar(128) | **Yes** | `NormalizedCandidate.provider_candidate_id` |
| `source` | `source` | varchar(100) | **Yes** | `NormalizedCandidate.provider_name` |
| `sourceUrl` | `sourceUrl` | url | **Yes** | `NormalizedCandidate.source_url` |
| `website` | `website` | url | **Yes** | `NormalizedCandidate.website` (e.g. `https://example.com`) |
| `country` | `country` | varchar(100) | **Yes** | `NormalizedCandidate.country` |
| `queue` | `queue` | enum | **Yes** | Hardcoded `"DISCOVERY"` |
| `status` | `status` | enum | **Yes** | Hardcoded `"WAITING"` |
| `researchStatus` | `researchStatus` | enum | **Yes** | Hardcoded `"NOT_STARTED"` |
| `qualificationStatus` | `qualificationStatus` | enum | **Yes** | Hardcoded `"PENDING"` |
| `crmPushStatus` | `crmPushStatus` | enum | **Yes** | Hardcoded `"NOT_READY"` |
| `searchJobId` | `searchJob` | link | **Yes** | BelongsTo relation; set via `searchJobId` foreign key |
| `note` | `note` | text | **Yes** | Acquisition metadata (see §7.2) |
| `assignedUserId` | `assignedUser` | link | **No** | Not set by Worker; defaults to API user or null |

### 7.2 Note Format

The Worker writes `note` as:
```
acquisition:v1 fingerprint={sha256} normalized_domain={domain} raw_payload_sha256={digest}
```

This is intentionally compact, machine-parseable, and contains no raw provider payload.

### 7.3 Missing Fields — Assessment

| Field | In ProspectPool? | In Worker Output? | Blocks C02.2C? |
|-------|:---:|:---:|:---:|
| `persona` | **No** — ProspectPool has no persona field | No | **No** — SearchJob carries persona context |
| `product` | **No** — ProspectPool has no product field | No | **No** — SearchJob carries product context via `product` field |
| `strategyId` | **No** — ProspectPool has no direct strategy link | No | **No** — Navigable via `searchJob.strategy` |
| `duplicateCount` | **No** — no dedicated field | Returned in `JobExecutionResult` only | **No** — C02.2B intentionally left SearchJob metadata unchanged |
| `retryable` | **No** — no boolean field | Encoded in `failureReason` text | **No** — C02.2B chose text encoding over schema change |

### 7.4 Verdict

**Zero ProspectPool schema changes required for C02.2C.** All fields needed by the Worker already exist in the ProspectPool entity definition. The three "missing" fields (persona, product, strategyId) are navigable through the SearchJob relationship and do not need to be denormalized onto ProspectPool for the MVP runner.

---

## 8. Idempotency and Replay

### 8.1 Scenario Analysis

| Scenario | Protection Mechanism | Outcome |
|----------|---------------------|---------|
| **1. First execution** | Normal flow | Job QUEUED → RUNNING → COMPLETED; prospects inserted |
| **2. Provider success, partial write failure** | Each `create_prospect` is independent; `has_prospect` prevents re-insertion of already-written records | Some prospects saved, job marked FAILED; manual re-run picks up remaining |
| **3. Crash after write, before COMPLETED** | Job stays RUNNING; `claim_queued_job` returns `None` for RUNNING jobs | Job NOT_CLAIMED on re-run; manual status reset needed before retry |
| **4. Manual re-run of same job** | `claim_queued_job` returns `None` (status is COMPLETED, not QUEUED) | NOT_CLAIMED; no duplicate work |
| **5. Two runners on same job** | Both GET QUEUED; both PUT RUNNING; both call provider; `has_prospect` dedup prevents duplicate prospects | Job completes with same prospects; second runner wastes provider call |
| **6. Same candidate from different SearchJobs** | `has_prospect(source, domain)` returns `True` for second occurrence | Second occurrence counts as duplicate, not inserted |
| **7. Same candidate from different providers** | Different `provider_name` → different fingerprint; different `source` → different `has_prospect` lookup | **Both inserted** — by design; different provider identities |

### 8.2 Layer Responsibilities

| Layer | Idempotency Role |
|-------|-----------------|
| **Worker Core** | In-result dedup via `seen_fingerprints` set; cross-job dedup via `has_prospect` |
| **Persistence Adapter** | `claim_queued_job` state guard; `has_prospect` query |
| **CRM** | No unique constraint on `website`; `externalProspectId` index exists but not used for dedup |
| **Claim action** | State gate: only QUEUED → RUNNING |
| **Runner** | Exits cleanly if `NOT_CLAIMED` (exit code 3) |

### 8.3 Key Limitation

**The `has_prospect` query uses a text `contains` match on `website`**, not an indexed unique lookup. At high volumes, this becomes a performance bottleneck. For C02.2C volumes (single runner, manual invocation, tens of jobs), it's acceptable.

**Future improvement (NOT in C02.2C):** Add a `fingerprint` field to ProspectPool with a unique index, and use it for O(1) dedup.

---

## 9. Failure and Recovery Design

### 9.1 Failure Classification

| Failure Type | Job Final Status | `errorCode` | `retryable` | Prospects Written? | User Recovery |
|-------------|:---:|-------------|:---:|:---:|------|
| **retryable Provider failure** | FAILED | `FAKE_TRANSIENT` (example) | `true` | No (provider never returned) | Reset job to QUEUED, re-run |
| **non-retryable Provider failure** | FAILED | `FAKE_INVALID_REQUEST` (example) | `false` | No | Fix SearchStrategy, create new job |
| **Authentication failure** | FAILED | `ESPOCRM_AUTH` | `false` | No | Fix API key in env |
| **Rate limit** | FAILED | `RATE_LIMITED` | `true` | No | Wait, re-run |
| **CRM read failure** | N/A (runner exits) | — | Exit code 6 | N/A | Check CRM health, re-run |
| **CRM write failure (job update)** | Stays RUNNING | — | — | Possibly partial | Manual status reset, re-run |
| **CRM write failure (prospect)** | FAILED | `CRM_WRITE_ERROR` | `true` | Partial | Re-run; `has_prospect` prevents dupes |
| **Worker unexpected exception** | FAILED | `WORKER_ERROR` | `true` | Partial | Inspect logs, re-run |
| **Process interruption (SIGTERM/Ctrl+C)** | Stays RUNNING | — | — | Partial | Manual status reset, re-run |
| **RUNNING job left stale** | RUNNING (forever) | — | — | Unknown | Manual status reset — deferred to Recovery phase |

### 9.2 Recovery Rules (C02.2C)

1. **No automatic retry** — All retries are manual
2. **Prospects ARE retained** on partial failure — no rollback
3. **No transaction rollback** — CRM has no cross-entity transaction API
4. **Manual recovery for stale RUNNING jobs:**
   - User checks CRM for job state
   - If no prospects were written (prospectCount = 0), reset to QUEUED and re-run
   - If prospects were partially written, re-run; `has_prospect` prevents duplicates
   - User manually sets status back to QUEUED via EspoCRM UI or API
5. **Deferred to Recovery phase:**
   - Stale RUNNING job detection (timeout-based)
   - Automatic RUNNING → QUEUED rollback
   - Batch retry of FAILED retryable jobs
   - Dead letter queue for non-retryable failures

### 9.3 Runner Exit Behavior

```
┌─────────────┐
│  RUNNER START │
└──────┬──────┘
       │
       ▼
┌──────────────┐     exit 2 (config error)
│ Load config   │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 1 (input error)
│ Parse args    │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 6 (read failure)
│ Fetch job     │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 3 (NOT_CLAIMED)
│ Claim job     │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 4 or 5 (provider failure)
│ Run provider  │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 7 (write failure)
│ Write results │────────────────────■
└──────┬───────┘
       │
       ▼
┌──────────────┐     exit 0 (success)
│ Mark COMPLETE │────────────────────■
└──────────────┘
```

---

## 10. Configuration and Credential Boundary

### 10.1 Environment Variables

| Variable | Required | Default | Purpose |
|----------|:---:|---------|---------|
| `ESPOCRM_BASE_URL` | **Yes** | — | EspoCRM root URL, e.g. `http://localhost:8080` |
| `ESPOCRM_API_KEY` | **Yes** | — | EspoCRM API key for X-Api-Key auth |
| `ESPOCRM_TIMEOUT` | No | `30` | HTTP request timeout in seconds |
| `ESPOCRM_TLS_VERIFY` | No | `true` | TLS certificate verification (set `0` to disable for dev) |

**No provider credential environment variables** — Fake Provider requires none. When real providers are added, each will have its own env var prefix (e.g., `GOOGLE_API_KEY`, `APIFY_API_TOKEN`).

### 10.2 Configuration Loading

- No unified config module exists today
- Runner will read `os.environ` directly (consistent with `LocalEspoCRMClient.from_environment()`)
- No `.env` file loading (no `python-dotenv` dependency)
- Pass values as constructor args to `EspoCRMRepository`

```python
# In runner.py
def _load_config() -> dict:
    base_url = os.environ.get("ESPOCRM_BASE_URL")
    api_key = os.environ.get("ESPOCRM_API_KEY")
    if not base_url:
        raise ConfigError("ESPOCRM_BASE_URL is required")
    if not api_key:
        raise ConfigError("ESPOCRM_API_KEY is required")
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "timeout": int(os.environ.get("ESPOCRM_TIMEOUT", "30")),
        "tls_verify": os.environ.get("ESPOCRM_TLS_VERIFY", "1") != "0",
    }
```

### 10.3 Secret Sanitization

- **Logging must never include** `ESPOCRM_API_KEY`, `X-Api-Key` header values, or Authorization headers
- Error messages must redact API keys if they appear in URLs or response text
- `--verbose` debug output must mask header values
- `JobExecutionResult` and all JSON output must not contain credentials

### 10.4 Fake Provider Credential Boundary

`DeterministicFakeProvider` has **zero credential requirements** — it is network-free and deterministic. The runner must not pass any credentials to the provider constructor.

---

## 11. Logging Contract

### 11.1 Design

All log output goes to **stderr**. Stdout is reserved for the JSON result (machine-readable contract). Logging is enabled with `--verbose`.

### 11.2 Structured Events

Each event is a single JSON line to stderr with the prefix `[ACQUISITION]`:

```
[ACQUISITION] {"event":"RUNNER_STARTED","jobId":"abc123","provider":"DETERMINISTIC_FAKE","dryRun":false,"ts":"2026-07-13T12:00:00Z"}
```

| Event | Fields |
|-------|--------|
| `RUNNER_STARTED` | `jobId`, `provider`, `dryRun`, `ts` |
| `JOB_FETCHED` | `jobId`, `status`, `keyword`, `country`, `product`, `ts` |
| `JOB_CLAIMED` | `jobId`, `previousStatus`, `ts` |
| `JOB_NOT_CLAIMED` | `jobId`, `currentStatus`, `reason`, `ts` |
| `PROVIDER_STARTED` | `jobId`, `provider`, `keyword`, `country`, `ts` |
| `PROVIDER_COMPLETED` | `jobId`, `provider`, `resultCount`, `durationMs`, `ts` |
| `PROVIDER_FAILED` | `jobId`, `provider`, `errorCode`, `retryable`, `durationMs`, `ts` |
| `PROSPECT_INSERTED` | `jobId`, `name`, `domain`, `ts` |
| `PROSPECT_DUPLICATE` | `jobId`, `domain`, `reason`, `ts` |
| `PROSPECT_REJECTED` | `jobId`, `reason`, `ts` |
| `JOB_COMPLETED` | `jobId`, `resultCount`, `insertedCount`, `duplicateCount`, `rejectedCount`, `durationMs`, `ts` |
| `JOB_FAILED` | `jobId`, `errorCode`, `retryable`, `errorSummary`, `durationMs`, `ts` |
| `CRM_WRITE_ERROR` | `jobId`, `operation`, `statusCode`, `ts` |
| `RUNNER_FINISHED` | `jobId`, `exitCode`, `durationMs`, `ts` |

### 11.3 Excluded from All Log Output

- Secrets (API keys, tokens, passwords)
- Full HTTP request/response payloads
- Provider raw payload (`raw_payload` field)
- Contact privacy data (email addresses, phone numbers)
- Authorization headers
- Full exception tracebacks (safe error summary only)

### 11.4 Non-Verbose Mode

Without `--verbose`, the runner emits zero log output. Only the JSON result on stdout.

---

## 12. Test Plan

### 12.1 Test File

`chitu-connector/tests/test_phase3c02_2c_job_runner.py`

### 12.2 Test Categories

#### A. CLI Unit Tests

| Test | What It Verifies |
|------|-----------------|
| `test_missing_job_id_exits_1` | `run-job` without `--job-id` → exit code 1 |
| `test_invalid_provider_exits_1` | `--provider google` → exit code 1 (only `fake` allowed) |
| `test_missing_env_vars_exits_2` | No `ESPOCRM_BASE_URL` → exit code 2 |
| `test_dry_run_json_output` | `--dry-run` prints valid JSON with `dryRun: true` |
| `test_json_output_schema` | Output JSON has all required fields |
| `test_not_claimable_exit_3` | COMPLETED job → exit code 3 |
| `test_secrets_not_in_output` | JSON output contains no `apiKey`, `X-Api-Key` strings |

#### B. Adapter Contract Tests (with HTTP mock)

| Test | What It Verifies |
|------|-----------------|
| `test_fetch_job_returns_dict` | `fetch_job` parses EspoCRM response correctly |
| `test_fetch_job_not_found_returns_none` | 404 → `None` |
| `test_claim_queued_job_success` | QUEUED job → status becomes RUNNING with `startedAt` |
| `test_claim_non_queued_returns_none` | RUNNING/COMPLETED/FAILED/CANCELLED → `None` |
| `test_update_search_job_writes_fields` | PUT sends correct JSON body |
| `test_has_prospect_true` | Matching source+domain → `True` |
| `test_has_prospect_false` | No match → `False` |
| `test_create_prospect_posts_body` | POST sends all required fields |
| `test_network_error_raises` | Connection refused → `EspoCRMRepositoryError` |
| `test_http_500_raises` | Server error → `EspoCRMRepositoryError` |

#### C. Worker Integration Tests (with in-memory store, no HTTP)

These are mostly covered by C02.2B tests. C02.2C adds:

| Test | What It Verifies |
|------|-----------------|
| `test_full_runner_pipeline_with_memory_store` | CLI args → config → store → worker → result formatter |
| `test_fake_provider_success_end_to_end` | Memory store + fake provider → COMPLETED with 2 prospects |
| `test_empty_result_completes` | `fake:empty` → COMPLETED, 0 prospects |
| `test_retryable_error_fails` | `fake:retryable-error` → FAILED, retryable=true, exit code 4 |
| `test_non_retryable_error_fails` | `fake:non-retryable-error` → FAILED, retryable=false, exit code 5 |
| `test_replay_rejected` | Second run on same job → NOT_CLAIMED, exit code 3 |
| `test_partial_write_recovery` | In-memory store simulates intermittent write failure |

#### D. Runtime Validation (NOT executed in this audit)

See §13.

---

## 13. Runtime Validation Plan

### 13.1 Purpose

Verify the runner against a real EspoCRM instance with actual SearchJob and ProspectPool records. **Not executed in this audit task.**

### 13.2 Validation Steps

1. **Setup (manual):**
   - Ensure EspoCRM is running with Prospecting extension installed
   - Set `ESPOCRM_BASE_URL` and `ESPOCRM_API_KEY` in environment
   - Create a test SearchStrategy via EspoCRM UI
   - Generate a SearchJob via "Generate Jobs" button
   - Note the SearchJob ID

2. **Dry-run verification:**
   ```bash
   python -m chitu_connector.acquisition.runner run-job --job-id <id> --dry-run
   ```
   - Expect: exit code 0, JSON with `"dryRun": true`, `"claimable": true`, `"previousStatus": "QUEUED"`

3. **Execution verification:**
   ```bash
   python -m chitu_connector.acquisition.runner run-job --job-id <id> --verbose
   ```
   - Expect: exit code 0, JSON with `"finalStatus": "COMPLETED"`, `"insertedCount": 2`
   - Verify in EspoCRM UI: SearchJob status = COMPLETED, ProspectPool has 2 new DISCOVERY records

4. **Replay rejection:**
   ```bash
   python -m chitu_connector.acquisition.runner run-job --job-id <id>
   ```
   - Expect: exit code 3, JSON with `"finalStatus": "NOT_CLAIMED"`

5. **Cleanup:**
   - Delete test ProspectPool records
   - Delete or reset test SearchJob

### 13.3 Validation Prerequisites

- EspoCRM test instance running
- Prospecting extension v1.9.0-alpha installed
- Integration Bot or Admin API key available
- No parallel tasks using the CRM instance

---

## 14. Exact Implementation File Boundary

### 14.1 New Files (C02.2C)

| File | Purpose | Lines (est.) |
|------|---------|:---:|
| `chitu-connector/chitu_connector/acquisition/runner.py` | CLI entry point, config loading, orchestration, result formatting | ~200 |
| `chitu-connector/chitu_connector/acquisition/espo_repository.py` | `EspoCRMRepository` implementing `AcquisitionStore` | ~200 |
| `chitu-connector/tests/test_phase3c02_2c_job_runner.py` | CLI tests + adapter contract tests + integration tests | ~300 |
| `docs/PHASE3C02_2C_JOB_RUNNER_REPORT.md` | Post-implementation report | ~150 |

### 14.2 Files That MAY Be Modified (With Justification)

| File | Change | Why |
|------|--------|-----|
| **None** | — | C02.2C is self-contained in new files |

### 14.3 Files That MUST NOT Be Modified

| File/Directory | Reason |
|----------------|--------|
| `chitu-connector/chitu_connector/acquisition/worker.py` | Worker Core (C02.2B scope) |
| `chitu-connector/chitu_connector/acquisition/models.py` | Data contracts (C02.2B scope) |
| `chitu-connector/chitu_connector/acquisition/provider.py` | Provider protocol (C02.2B scope) |
| `chitu-connector/chitu_connector/acquisition/normalization.py` | Normalization (C02.2B scope) |
| `chitu-connector/chitu_connector/acquisition/fake_provider.py` | Fake provider (C02.2B scope) |
| `chitu-connector/pyproject.toml` | Package manifest |
| `crm-extension/**` | CRM extension (separate system, separate tasks) |
| Existing test files | C02.2B tests |

### 14.4 If Safe Claim Requires CRM Extension Changes

If the race-window assessment (§6.2) is deemed unacceptable even for MVP:

**Split into two sub-tasks:**

| Task | Scope | Files |
|------|-------|-------|
| **C02.2C1** — EspoCRM Claim Action | Custom `POST /SearchJob/{id}/claim` API | `crm-extension/files/.../Api/PostSearchJobClaim.php`, `routes.json` |
| **C02.2C2** — CLI Runner Integration | Runner + adapter (uses claim action from C02.2C1) | `runner.py`, `espo_repository.py`, tests |

**Recommendation:** Proceed without splitting. The GET-then-PUT approach is correct for single-runner use. Add C02.2C1 only if multi-runner production deployment is imminent.

---

## 15. Proposed Task Size

**Single Codex session.** The total implementation scope is:

- 2 new Python modules (~400 lines total)
- 1 new test file (~300 lines)
- 1 documentation file (~150 lines)
- Zero modifications to existing files
- Zero CRM extension changes
- Zero new dependencies

**Estimated session time:** 1 Codex session (2-4 hours of focused work)

**Breakdown:**
| Activity | Effort |
|----------|:---:|
| Write `espo_repository.py` | 30 min |
| Write `runner.py` | 30 min |
| Write tests | 45 min |
| Run test suite | 15 min |
| Write implementation report | 30 min |
| **Total** | **~2.5 hours** |

---

## 16. Dependencies on Worker Core

### 16.1 What C02.2C Depends On

| Worker Core Component | How C02.2C Uses It |
|-----------------------|---------------------|
| `AcquisitionStore` protocol | `EspoCRMRepository` implements it |
| `AcquisitionWorker` class | Runner constructs and calls `execute_job()` |
| `SearchProvider` protocol | `DeterministicFakeProvider` satisfies it (unchanged) |
| `JobExecutionResult` dataclass | Runner formats it to JSON |
| `ProviderError` exception | Runner maps to exit codes 4/5 |
| `SearchRequest` dataclass | Worker constructs from job data; runner doesn't touch it |
| `NormalizedCandidate` dataclass | Worker internal; runner doesn't touch it |

### 16.2 Design Assumptions About Worker Core

| Assumption | Status | Risk if Wrong |
|-----------|:---:|------|
| `claim_queued_job` returns `None` for non-QUEUED jobs | **Verified** (C02.2B test) | Runner's NOT_CLAIMED handling already robust |
| `execute_job` never raises (catches ProviderError internally) | **Verified** (code review) | Runner catches unexpected exceptions as exit code 8 |
| `has_prospect` is called before every `create_prospect` | **Verified** (code review) | No duplicate CRM writes |
| Worker does not call EspoCRM directly | **Verified** (static scan in C02.2B) | No hidden network dependency |
| `JobExecutionResult` fields are stable | **Verified** (frozen dataclass) | JSON schema stable |

### 16.3 If C02.2B-R Finds Issues

The parallel task Phase3C02.2B-R may produce review findings about Worker Core. If issues are found:

- **Minor issues** (code style, docstring): Do not block C02.2C
- **Contract issues** (`AcquisitionStore` method signature change): Block C02.2C until resolved
- **Behavioral issues** (wrong status transition): Block C02.2C until resolved
- **Missing functionality** (no prospect dedup): Block C02.2C until resolved

This report is written against the current Worker Core as-is. Any changes made by C02.2B-R must be reflected in C02.2C's implementation.

---

## 17. Collision Check with Parallel Tasks

### 17.1 Active Parallel Tasks

| Task | Status | Files Touched | Collision Risk |
|------|--------|--------------|:---:|
| **Phase3C02.1B** — Git Commit Separation | In progress | Git operations only; no code changes | **None** |
| **Phase3C02.2B-R** — Worker Core Review | In progress | Review only; reads `acquisition/` files | **None** (reads only) |

### 17.2 Detailed Collision Analysis

| Resource | C02.1B | C02.2B-R | C02.2C (this design) | Safe? |
|----------|:---:|:---:|:---:|:---:|
| `acquisition/worker.py` | No | Read | Read (existing, not modified) | **Yes** |
| `acquisition/models.py` | No | Read | Read | **Yes** |
| `acquisition/provider.py` | No | Read | Read | **Yes** |
| `acquisition/fake_provider.py` | No | Read | Read | **Yes** |
| `acquisition/normalization.py` | No | Read | Read | **Yes** |
| `acquisition/__init__.py` | No | Read | Read (may need re-export) | **Yes** — C02.2C adds no exports |
| `chitu-connector/pyproject.toml` | No | No | No | **Yes** |
| `crm-extension/**` | No | No | No | **Yes** |
| `docs/**` | No | No | New file only | **Yes** |
| Git index / commits | **Write** | No | No write | **Yes** |

### 17.3 Sequencing Recommendation

1. C02.1B completes first (commit separation)
2. C02.2B-R findings are available before or during C02.2C implementation
3. C02.2C implements runner and adapter on clean commit base

**C02.2C does not need to wait for C02.2B-R.** It can proceed with the current Worker Core contract and adjust if the review mandates changes.

---

## 18. Go / No-Go Verdict

### GO

**Recommended implementation approach:**
1. Create `espo_repository.py` — EspoCRM REST adapter implementing `AcquisitionStore`
2. Create `runner.py` — argparse CLI with `run-job` subcommand
3. Create test file — CLI, adapter, and integration tests
4. All new files; zero modifications to existing code
5. Single Codex session scope

**Exact files to create:**
- `chitu-connector/chitu_connector/acquisition/runner.py`
- `chitu-connector/chitu_connector/acquisition/espo_repository.py`
- `chitu-connector/tests/test_phase3c02_2c_job_runner.py`

**No unresolved architecture blocker:**
- Worker Core is complete and tested (C02.2B PASS)
- CRM entities have all required fields (verified in §7)
- EspoCRM REST API supports all needed operations (GET/POST/PUT)
- Fake Provider is deterministic and network-free
- All layer boundaries defined (§3)
- All contracts specified (§4-§11)
- Test plan covers all scenarios (§12)

**Known limitation acknowledged:**
- GET-then-PUT claim has a theoretical race window; acceptable for single-runner C02.2C MVP
- `has_prospect` query uses non-indexed text match; acceptable for C02.2C volumes

**Ready for Phase3C02.2C implementation after commit separation (C02.1B).**

---

**Phase3C02.2C-A design audit complete. No code was modified, no runtime was affected, no data was created or deleted.**
