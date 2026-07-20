# Test Inventory

**Status:** Phase T01 Audit — compiled 2026-07-13 from live file scan

> **IMPORTANT:** Test counts are from the most recent Phase report or static scan, not fixed permanent values. Rerun tests to get current counts.

> **T02 entrypoint:** Run the current offline inventory through `scripts/testing/run-tests.ps1`. See [UNIFIED_TEST_ENTRYPOINTS.md](UNIFIED_TEST_ENTRYPOINTS.md) for suite mapping and exit codes.

> **T03 gate:** The core required subset is executed without reduction by `scripts/testing/run-regression-gate.ps1`; see [CORE_REGRESSION_GATE.md](CORE_REGRESSION_GATE.md).

> **T04 runtime harness:** `scripts/testing/run-runtime-tests.ps1` is a separate, disabled-by-default local REST harness. It is not part of the T03 gate; see [RUNTIME_TEST_HARNESS.md](RUNTIME_TEST_HARNESS.md) and [RUNTIME_TEST_ENVIRONMENT.md](RUNTIME_TEST_ENVIRONMENT.md).

---

## 1. Extension Tests (`crm-extension/tests/`)

### 1.1 `test_extension_skeleton.py`

| Field | Value |
|-------|-------|
| **Location** | `crm-extension/tests/test_extension_skeleton.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Entry command** | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **Approx. tests** | 26 test methods (Phase D01 verified: 40 individual assertions) |
| **Scope** | Extension skeleton static validation: manifest, directory structure, entity definitions (ResearchEvidence, Lead, Opportunity, SearchJob, ProspectPool, SalesFeedback, LearningSignal, EmailEvent), field models, layout sections, formula metadata, workflow hooks, connector routes, feedback loop, email workflow, prospecting workspace UI, operations filters, acquisition workspace, SearchStrategy discovery jobs, ACL provisioning scripts |
| **Main assertions** | Manifest version 1.9.6-alpha; 41 required directories exist; entityDefs surface/module parity for all entities; field type/default/option validations; contract field mapping consistency; PHP shell file inventory; forbidden entity access patterns (no `getEntity('Opportunity')` in sync service); formula rule presence; route endpoint parity; provisioning script content checks |
| **Dependencies** | Python 3 stdlib only; reads `manifest.json`, entityDefs, layouts, ACLs, PHP sources, routes, i18n, provisioning scripts, sync contract |
| **Runtime required** | None — fully static, no EspoCRM, no database, no network |
| **External system required** | None |
| **Side effects** | None — read-only |
| **Cleanup behavior** | N/A |
| **Current status** | ACTIVE |
| **Latest verified result** | Phase D01: all passing (2026-07-13). Historical counts: Phase 3B Final Summary reported 35 tests; Phase D01 updated to 40 assertions across 26 methods |
| **Evidence report** | [TEST_PLAN.md](TEST_PLAN.md), [developer/TESTING.md](../developer/TESTING.md) |

### 1.2 `test_phase3c02_search_strategy_foundation.py`

| Field | Value |
|-------|-------|
| **Location** | `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Entry command** | `python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v` |
| **Approx. tests** | 2 test methods |
| **Scope** | SearchStrategy entity metadata registration and UI baseline; surface/module parity |
| **Main assertions** | 14 fields present in entityDefs; `status.default = "DRAFT"`; `links.searchJobs` correct; scope metadata; detail/list layout parity; i18n labels; `app/layouts` module ownership; detail view JS references `'views/detail'`; entity/controller PHP shells exist |
| **Dependencies** | Python 3 stdlib; reads SearchStrategy entityDefs, ACL, layouts, i18n, client JS |
| **Runtime required** | None — fully static |
| **External system required** | None |
| **Side effects** | None |
| **Cleanup behavior** | N/A |
| **Current status** | ACTIVE |
| **Latest verified result** | Phase D01: 2/2 passing |
| **Evidence report** | [TEST_PLAN.md](TEST_PLAN.md) |

### 1.3 `__init__.py` (package init)

| Field | Value |
|-------|-------|
| **Location** | `crm-extension/tests/__init__.py` |
| **Language / framework** | Python 3 package init (empty) |
| **Entry command** | N/A — required for `python -m unittest crm-extension.tests.*` resolution |
| **Scope** | Package marker |
| **Current status** | ACTIVE |

---

## 2. Connector Tests (`chitu-connector/tests/`)

**Entry command (full suite):**
```powershell
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

### 2.1 `test_espocrm_sync_adapter.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_sync_adapter.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 22 test methods across 6 test classes |
| **Scope** | Sync contract pipeline: contract validation (2), gate evaluation (9), mapper output (4), idempotency keys (2), mock client behavior (3), top-level adapter orchestration (2) |
| **Main assertions** | Valid payload passes structural validation; unknown fields rejected; all 9 gate rejection conditions verified; company/score mapping uses v4 fields; evidence references compact; same input yields same idempotency key; mock client simulates success/duplicate/validation error; adapter audit trail records READY → SYNCED; rejection does not call mock client |
| **Dependencies** | `chitu_connector.espocrm_sync`, `chitu_connector.vendored.*`, Python stdlib |
| **Runtime required** | None — fully mocked (`MockEspoCRMClient`, inline `build_source()` helpers) |
| **External system required** | None |
| **Side effects** | None |
| **Current status** | ACTIVE |
| **Latest verified result** | Phase C02.2C-R: 22/22 passing (also included in full connector 89/89) |

### 2.2 `test_espocrm_connector_api.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_connector_api.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 9 test methods |
| **Scope** | Connector REST client: API key/URL validation, lead/evidence/proposal routes, sequential pipeline ordering, gate rejection pre-checks, error propagation |
| **Main assertions** | Empty API key rejected; non-HTTP URL rejected; routes posted to correct paths with X-Api-Key header; sync_source runs validation → gate → lead → evidence → proposal in order; 6 gate rejection conditions prevent urlopen calls; lead/evidence/proposal failures stop pipeline |
| **Dependencies** | `chitu_connector.espocrm_sync.connector_api`, `unittest.mock.patch` |
| **Runtime required** | None — HTTP mocked via `patch("...urlopen")` |
| **Current status** | ACTIVE |

### 2.3 `test_phase3c02_2b_acquisition_worker_core.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 10 test methods |
| **Scope** | AcquisitionWorker core: DeterministicFakeProvider, state transitions, dedup, domain normalization, error classification, boundary isolation |
| **Main assertions** | Fake provider is deterministic and returns 3 candidates; QUEUED → COMPLETED with correct counts (3 results, 2 inserts, 1 duplicate); prospects created with correct queue/source/website/fingerprint; replay returns NOT_CLAIMED; cross-job dedup works; domain normalization strips protocol/www/port/path; empty result completes with 0 prospects; provider errors classified by retryability; non-QUEUED jobs not claimed; invalid candidates rejected; worker module has no CRM/sync/network imports |
| **Dependencies** | `chitu_connector.acquisition`, `hashlib`, Python stdlib |
| **Runtime required** | None — `MemoryAcquisitionStore` + `DeterministicFakeProvider`/`StaticProvider` |
| **Current status** | ACTIVE |
| **Evidence report** | [PHASE3C02_2B_WORKER_CORE_REVIEW.md](../PHASE3C02_2B_WORKER_CORE_REVIEW.md) |

### 2.4 `test_phase3c02_2b1_worker_persistence_hardening.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_phase3c02_2b1_worker_persistence_hardening.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 8 test methods |
| **Scope** | Persistence fault tolerance: claim conditions, claim persistence errors, provider/unexpected errors, partial persistence, completion/failure update errors, normalization exceptions |
| **Main assertions** | Non-QUEUED claim rejected without provider call; claim transport error returns structured CLAIM_FAILED; provider errors caught with correct stage/retryability; secrets stripped from error summaries; first prospect write failure is fail-fast (0 prospects, job FAILED); partial persistence (create_at=2) preserves 1 prospect and counts; completion write failure preserves all prospects; failure update failure sets uncertain final status; normalization exception caught without persisting exception text |
| **Dependencies** | `chitu_connector.acquisition`, Python stdlib |
| **Runtime required** | None — `FaultInjectionStore` + `SpyProvider` |
| **Current status** | ACTIVE |

### 2.5 `test_phase3c02_2c_job_runner.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_phase3c02_2c_job_runner.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 15 test methods across 2 classes (RunnerCliTests: 7, EspoRepositoryTests: 8) |
| **Scope** | CLI runner entry point and EspoCRM HTTP repository layer |
| **Main assertions** | Missing config fails before repository access; non-fake provider rejected before network; JSON output safe (no API key leaked); replay returns EXIT_NOT_CLAIMED; empty/provider-error modes use stable exit codes; partial persistence uses EXIT_PARTIAL_OR_UNCERTAIN; non-QUEUED jobs do not execute; fetch parses response/404; HTTP errors classified by retryability; claim writes RUNNING and confirms; update uses expected status+version; prospect lookup/create only sends known fields; boundary has no ChituSyncService/Apify/while True |
| **Dependencies** | `chitu_connector.acquisition`, `io`, `json`, `pathlib`, `urllib.error` |
| **Runtime required** | None — `MemoryRepository` + `FakeResponse` + `ScriptedOpener` |
| **Current status** | ACTIVE |
| **Evidence report** | [PHASE3C02_2C_JOB_RUNNER_REPORT.md](../PHASE3C02_2C_JOB_RUNNER_REPORT.md) |

### 2.6 `test_espocrm_real_client.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_real_client.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 9 test methods |
| **Scope** | LocalEspoCRMClient safety sandbox: env gating, URL allowlisting, authentication, preflight, synthetic markers, field limiting |
| **Main assertions** | Remote HTTPS URLs rejected; `ESPOCRM_TEST_ENV=true` required; env vars read correctly; API key auth alternative; authentication uses App/user token; preflight validates Lead fields + ResearchEvidence fields + links; lead payloads synthetic-marked and field-limited; evidence payloads field-limited; absolute API paths rejected; lifecycle helpers reject non-CRM entities |
| **Dependencies** | `chitu_connector.espocrm_sync.real_client`, `unittest.mock.patch`, `os` |
| **Runtime required** | Locally: none (uses StubClient). Live CRM (gated behind `ESPOCRM_TEST_ENV=true`) |
| **Side effects** | None when mocked; would create records when run live (gated) |
| **Current status** | ACTIVE (env-gated for live path; mocked tests always safe) |

### 2.7 `test_espocrm_lifecycle_sync.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_lifecycle_sync.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 4 test methods |
| **Scope** | LifecycleSyncService: Lead creation, conversion updates, duplicate detection, broken link detection |
| **Main assertions** | New prospect creates Lead by peCandidateId; converted Lead updates all 4 entities but not sales fields; duplicate peCandidateId raises LifecycleConflictError before mutation; broken originalLeadId stops after Lead update |
| **Dependencies** | `chitu_connector.espocrm_sync.lifecycle`, Python stdlib |
| **Runtime required** | None — `InMemoryLifecycleClient` stub |
| **Current status** | ACTIVE |

### 2.8 `test_espocrm_email_lifecycle.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_email_lifecycle.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 3 test methods |
| **Scope** | EmailLifecycleSyncService: summary field sync, content exclusion, optional opportunity, input validation |
| **Main assertions** | Replied status writes 4 fields to Lead + Opportunity; sales fields never mutated; content-like fields excluded; opportunity optional; naive datetime rejected; over-length reply_state rejected |
| **Dependencies** | `chitu_connector.espocrm_sync.email_lifecycle`, Python stdlib |
| **Runtime required** | None — `InMemoryEmailLifecycleClient` stub |
| **Current status** | ACTIVE |

### 2.9 `test_espocrm_feedback_api.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_feedback_api.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 2 test methods |
| **Scope** | FeedbackConnectorClient: feedback payload posting, API key, validation |
| **Main assertions** | Posts to `/Prospecting/feedback/sync` with X-Api-Key; parses response fields; invalid feedback_type raises error; naive datetime rejected; missing fields rejected |
| **Dependencies** | `chitu_connector.espocrm_sync.feedback_api`, `unittest.mock.patch` |
| **Runtime required** | None — HTTP mocked |
| **Current status** | ACTIVE |

### 2.10 `test_espocrm_brevo_api.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_brevo_api.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 2 test methods |
| **Scope** | BrevoConnectorClient: event normalization, API key, duplicate detection |
| **Main assertions** | Normalizes Brevo event types; posts to `/Prospecting/brevo/email-event` with X-Api-Key; response includes duplicate flag; unknown event_type rejected; naive datetime rejected |
| **Dependencies** | `chitu_connector.espocrm_sync.brevo_api`, `unittest.mock.patch` |
| **Runtime required** | None — HTTP mocked |
| **Current status** | ACTIVE |

### 2.11 `test_espocrm_feedback_signal_export.py`

| Field | Value |
|-------|-------|
| **Location** | `chitu-connector/tests/test_espocrm_feedback_signal_export.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Approx. tests** | 2 test methods |
| **Scope** | FeedbackSignalExportClient: signal fetch and field mapping |
| **Main assertions** | Fetches from `/LearningSignal?` with X-Api-Key; maps rows to signal objects; empty API key rejected; missing response fields rejected |
| **Dependencies** | `chitu_connector.espocrm_sync.feedback_signal_export`, `unittest.mock.patch` |
| **Runtime required** | None — HTTP mocked |
| **Current status** | ACTIVE |

---

## 3. Deployment Validation (`deployment/validation/`)

### 3.1 `test_phase3c02_1a_search_strategy_detail.py`

| Field | Value |
|-------|-------|
| **Location** | `deployment/validation/test_phase3c02_1a_search_strategy_detail.py` |
| **Language / framework** | Python 3.12, `unittest.TestCase` (stdlib) |
| **Entry command** | `python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v` |
| **Approx. tests** | 2 test methods |
| **Scope** | Offline SearchStrategy detail view JS validation |
| **Main assertions** | detail.js references `'views/detail'`; no `recordViews` in clientDefs; generateJobs action handler configured correctly; handler file exists |
| **Dependencies** | Reads `crm-extension/files/client/custom/src/views/search-strategy/detail.js` and clientDefs |
| **Runtime required** | None — static |
| **Side effects** | None |
| **Current status** | ACTIVE |

### 3.2 `phase3c02_1_api_acl_acceptance.py`

| Field | Value |
|-------|-------|
| **Location** | `deployment/validation/phase3c02_1_api_acl_acceptance.py` |
| **Language / framework** | Python 3.12, custom acceptance runner (stdlib only) |
| **Entry command** | `python deployment/validation/phase3c02_1_api_acl_acceptance.py` (requires env vars) |
| **Approx. tests** | 1 integrated flow with 7 validation stages |
| **Scope** | Live API ACL acceptance: CRUD, generate-jobs, boundaries, delete matrix, owner isolation, cleanup |
| **Main assertions** | 4 actors can list/create/read/update all 3 entity types; generate-jobs yields 10 unique QUEUED jobs; duplicate call returns 0 generated/10 existing; missing/invalid fields return 400; maximum job cardinality returns 400; admin-only delete (others 403); owner isolation (sales cannot read manager-owned strategy); cleanup removes all marker records |
| **Dependencies** | Python 3 stdlib + `urllib`; requires 4 API key env vars + running EspoCRM |
| **Runtime required** | YES — running EspoCRM with provisioned test users |
| **Side effects** | Creates and deletes `[CHITU_PHASE3C02_TEST]` records |
| **Cleanup behavior** | `--cleanup` mode removes all marker records and verifies zero residuals |
| **Current status** | ACTIVE (TBD — requires live CRM) |

---

## 4. Provisioning Scripts (Validation-Adjacent)

26 PHP provisioning scripts in `deployment/provisioning/` — while not formal tests, several contain embedded validation checks:

| Script | Validation | Phase |
|--------|-----------|-------|
| `phase3b02_provision_workflow_pipeline.php` | Asserts `outreachStatus` options match expected pipeline; Lead formula contains `CONTACT_READY`; Opportunity stages correct | 3B02 |
| `phase3c02_1_provision_acquisition_acl.php` | Verifies ACL provisioning writes for 3 scopes × 4 roles | 3C02.1 |

All provisioning scripts are idempotent (use upsert patterns), but none use transactional rollback. Cleanup scripts delete by `[CHITU_PHASE*_TEST]` marker prefix.

---

## 5. Build Validation

| Item | Type | Status |
|------|------|--------|
| `build_release_package.ps1` | PowerShell build script | ACTIVE (not a test, but production validated) |
| SHA-256 sidecar files (6 versions) | Integrity hash | Manual verification only; no automated script |
| `test_manifest_json_valid` in skeleton | Static assertion | ACTIVE (validates manifest structure) |

---

## 6. Summary

| Category | Files | Tests (approx) | CRM Required | Side Effects |
|----------|-------|----------------|--------------|--------------|
| Extension skeleton | 2 Python files | 28 methods (~42 assertions) | No | None |
| Connector unit | 11 Python files | ~86 methods | No | None |
| Connector live (gated) | 1 Python file | 9 methods (mocked) | Only in live mode | Only in live mode |
| Deployment validation (static) | 1 Python file | 2 methods | No | None |
| Deployment acceptance (live) | 1 Python file | 1 flow | Yes | Creates/deletes test records |
| Provisioning (validation-adjacent) | 26 PHP files | 2 with assertions | Yes | Creates/updates roles, users, dashboards |
| **Total** | **16 test files** | **~136+ test methods** | — | — |

### Test Count Note

- Phase D01 verified: Extension 42 assertions, Connector 89 assertions = **131 total**
- Phase T01 static scan: ~136 test methods found across all locations
- Some methods contain multiple assertions (e.g., `test_extension_skeleton.py` 26 methods ≈ 40+ assertions)
- Historical counts from earlier phases (35 / 58 / etc.) are **superseded** — see phase reports for provenance

### Not Found

- PHP test files (PHPUnit, Pest): **none anywhere in repository**
- Browser/UI test framework (Playwright, Selenium): **none**
- Installation/upgrade/rollback automated tests: **none**
- Performance/load tests: **none**
- CI/CD pipeline configuration: **none**
- Test fixtures as data files: **none** (all inline in test files)
- Secret scanning / leakage tests: **none** (but test code manually verified clean)
