# Test Reliability Risks

**Status:** Phase T01 Audit — 2026-07-13

> Documents reliability concerns found across the current test suite. Each finding includes severity, location, description, and recommendation. Findings are ordered by severity (most critical first).

---

## Severity Legend

| Level | Meaning |
|-------|---------|
| **CRITICAL** | Test could produce false positives, miss real failures, or cause data loss |
| **HIGH** | Test is fragile, environment-dependent, or has misleading assertions |
| **MEDIUM** | Test has structural issues that reduce confidence or maintainability |
| **LOW** | Minor concerns, documentation gaps, or style issues |
| **INFO** | Observations worth noting but not actionable risks |

---

## Findings

### R01 — Provisioning scripts contain hardcoded test credentials

| Field | Detail |
|-------|--------|
| **Severity** | **HIGH** |
| **Location** | `deployment/provisioning/phase3a33_provision_roles.php`, `phase3b03_provision_connector_test_user.php`, `phase3b04_provision_feedback_test_user.php`, `phase3b05a_provision_brevo_test_user.php`, `phase3b05b_provision_email_workflow_roles.php`, `phase3b05c_provision_email_feedback_roles.php`, `phase3b06_provision_workspace_roles.php`, `phase3b06_1_provision_connector_test_user.php` |
| **Description** | Multiple provisioning scripts contain hardcoded API keys (e.g., `phase3b03-local-test-api-key`, `phase3b04-local-test-api-key`) and user passwords (e.g., `SalesTest#2026`, `ManagerTest#2026`, `ResearchTest#2026`). While these are test-only credentials for disposable environments, they are committed to the repository and could be mistaken for production secrets. |
| **Risk** | Accidental use in non-test context; secret scanning tools will flag these; contributors may not realize they are test-only. |
| **Recommendation** | Migrate to environment variables with documented defaults in a `.env.example` file. Add `.env` to `.gitignore`. Add comment block at top of each script: `// TEST CREDENTIALS ONLY — NOT FOR PRODUCTION`. Consider `truffleHog` or `detect-secrets` pre-commit hook. |

### R02 — No automated cleanup verification after test runs

| Field | Detail |
|-------|--------|
| **Severity** | **HIGH** |
| **Location** | `deployment/validation/phase3c02_1_api_acl_acceptance.py` |
| **Description** | The acceptance script has a `--cleanup` mode but it is manual. If cleanup is not run (or fails silently), test marker records `[CHITU_PHASE3C02_TEST]` remain in the CRM database. There is no automated post-test residue check. |
| **Risk** | Accumulated test records over multiple runs; test data leakage into dashboards and reports; cleanup failure not detected. |
| **Recommendation** | T04 now supplies registry-only automatic cleanup for its own fixtures, with marker verification and a 404 residue audit. It still needs configured local-runtime evidence before this risk can be closed; a broad historical-marker scanner remains out of scope. |

### R03 — `test_espocrm_real_client.py` live tests are env-gated but not automatically skipped

| Field | Detail |
|-------|--------|
| **Severity** | **MEDIUM** |
| **Location** | `chitu-connector/tests/test_espocrm_real_client.py` |
| **Description** | The `LocalEspoCRMClient.from_environment()` method requires `ESPOCRM_TEST_ENV=true`. The unit tests (using `StubClient`) always pass. However, if someone sets `ESPOCRM_TEST_ENV=true` and runs the full connector suite, live tests will attempt to connect to CRM and create records. There is no `@unittest.skipIf` guard on the live tests. |
| **Risk** | Accidental live CRM writes during test runs; test suite hangs if CRM unreachable. |
| **Recommendation** | Add `@unittest.skipIf(not os.environ.get("ESPOCRM_TEST_ENV"), "Live CRM tests require ESPOCRM_TEST_ENV=true")` to live test methods. Consider separating live tests into a dedicated test file with `test_live_` prefix and exclude from default discovery. |

### R04 — Phase report test counts are stale and misleading

| Field | Detail |
|-------|--------|
| **Severity** | **MEDIUM** |
| **Location** | `docs/testing/ESPOCRM_SYNC_ADAPTER_TEST_REPORT_V1.md`, `ESPOCRM_SYNC_TEST_PLAN_V1.md`, `PHASE3A22B_REAL_SYNC_TEST_REPORT_V1.md`, `PHASE3A22B_RUNTIME_VERIFY_REPORT.md` |
| **Description** | Historical test reports in `docs/testing/` reference test counts (e.g., 12 extension tests, 219 engine tests, 20 adapter tests) that have been superseded by current counts (42 extension, 89 connector). These reports lack a clear "SUPERSEDED" banner. |
| **Risk** | Readers may cite outdated counts; confusion about current test coverage. |
| **Recommendation** | Add "⚠️ SUPERSEDED" banner at top of each historical report linking to the current TEST_INVENTORY.md. Or move to `docs/testing/archive/` directory. |

### R05 — `tests/README.md` in crm-extension references wrong import path

| Field | Detail |
|-------|--------|
| **Severity** | **MEDIUM** |
| **Location** | `crm-extension/tests/README.md` |
| **Description** | The README states: `python -m unittest espocrm_extension.tests.test_extension_skeleton -v` using the old `espocrm_extension` package name. Correct command is `python -m unittest crm-extension.tests.test_extension_skeleton -v`. |
| **Risk** | New contributors copy-pasting the wrong command will get import errors. |
| **Recommendation** | Update README to current package name. Consider removing redundant README (commands documented in `docs/testing/` and `docs/developer/TESTING.md`). |

### R06 — No `__init__.py` in chitu-connector tests directory

| Field | Detail |
|-------|--------|
| **Severity** | **LOW** |
| **Location** | `chitu-connector/tests/` |
| **Description** | The `chitu-connector/tests/` directory lacks `__init__.py`. Tests are discovered via `unittest discover` which works without it, but some IDEs and tools may not recognize it as a package. |
| **Risk** | IDE test runner may fail to discover tests; `python -m unittest chitu-connector.tests.test_*` syntax may not resolve. |
| **Recommendation** | Add empty `chitu-connector/tests/__init__.py` for consistency with `crm-extension/tests/__init__.py`. |

### R07 — Test assertions rely on fixed manifest version string

| Field | Detail |
|-------|--------|
| **Severity** | **LOW** |
| **Location** | `crm-extension/tests/test_extension_skeleton.py:239`, `test_phase3c02_search_strategy_foundation.py:68` |
| **Description** | Multiple tests assert `manifest["version"] == "1.9.5-alpha"`. This must be manually updated on every version bump, or tests will fail. |
| **Risk** | False negative on version bump — easy to forget. Not a safety issue (test correctly fails), but a maintenance friction point. |
| **Recommendation** | Acceptable as-is for a version-locked project. Consider extracting to a shared constant or reading from manifest and validating against a pattern (`r"\d+\.\d+\.\d+-alpha"`) instead of exact string. Do not skip the version test — it serves as a deliberate release checkpoint. |

### R08 — Connector tests use `unittest.mock.patch` on `urlopen` — fragile to import path changes

| Field | Detail |
|-------|--------|
| **Severity** | **LOW** |
| **Location** | `chitu-connector/tests/test_espocrm_connector_api.py`, `test_espocrm_feedback_api.py`, `test_espocrm_brevo_api.py`, `test_espocrm_feedback_signal_export.py` |
| **Description** | Tests patch `chitu_connector.espocrm_sync.connector_api.urlopen` (etc.) — if the import path of `urlopen` changes in the source module, the patch silently fails and tests make real HTTP calls. |
| **Risk** | Silent switch from mocked to real HTTP if source code is refactored to import `urlopen` differently. |
| **Recommendation** | Acceptable risk for current architecture (import paths stable). Consider adding a pre-test guard that verifies `urlopen` is patched before allowing test execution (e.g., assert `urlopen` is `MagicMock` at start of each test). |

### R09 — No test isolation between test files (shared global state via file system)

| Field | Detail |
|-------|--------|
| **Severity** | **LOW** |
| **Location** | All Python test files |
| **Description** | Extension skeleton tests read files from the working tree. If an uncommitted change exists (as currently: `M crm-extension/Resources/entityDefs/SearchJob.json` and others), test results reflect the dirty working tree, not the committed state. |
| **Risk** | Tests passing against dirty tree may fail after commit; false confidence from uncommitted changes. |
| **Recommendation** | Acceptable — this is by design (tests validate the working tree). Document that pre-commit regression must run against clean tree. Consider adding a pre-flight check: `git diff --exit-code crm-extension/` before running tests (opt-in, not default). |

### R10 — Live acceptance script has no timeout on individual API calls

| Field | Detail |
|-------|--------|
| **Severity** | **MEDIUM** |
| **Location** | `deployment/validation/phase3c02_1_api_acl_acceptance.py:74` |
| **Description** | `urlopen(request, timeout=20)` uses a fixed 20-second timeout. If CRM is slow or hung, the script blocks for 20 seconds per call × ~40 API calls = potentially 13+ minutes before failing. No retry logic. |
| **Risk** | Long CI runs; no clear diagnostic if CRM is slow vs. down. |
| **Recommendation** | Add configurable timeout via env var (`C02_API_TIMEOUT`). Add circuit breaker: if N consecutive calls timeout, abort early. Add progress logging so stuck calls are identifiable. |

### R11 — Worker tests use `MemoryAcquisitionStore` that doesn't match real CRM behavior

| Field | Detail |
|-------|--------|
| **Severity** | **INFO** |
| **Location** | `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py`, `test_phase3c02_2b1_worker_persistence_hardening.py` |
| **Description** | The `MemoryAcquisitionStore` and `FaultInjectionStore` are dict-backed stubs. They correctly model the repository interface but do not replicate EspoCRM's actual API behavior (version conflicts, partial updates, JSON field serialization, API key auth errors). |
| **Risk** | Tests passing against MemoryStore may fail against real EspoCRM due to unmodeled API behaviors. |
| **Recommendation** | Document as a known limitation. The `EspoAcquisitionRepository` tests in `test_phase3c02_2c_job_runner.py` partially mitigate this by testing the real HTTP layer with `ScriptedOpener`. For production confidence, layer on runtime end-to-end tests (Phase C02.2C-R path). |

### R12 — No test coverage for SearchStrategyTemplates or SearchStrategyService validation logic in isolation

| Field | Detail |
|-------|--------|
| **Severity** | **MEDIUM** |
| **Location** | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SearchStrategyService.php`, `SearchStrategyTemplates.php` |
| **Description** | The extension skeleton tests validate the PHP source code contains expected strings (product names, persona names, MAX_JOBS, validation error messages). They do not test the actual runtime behavior: what happens with edge-case inputs, how the 40-job limit interacts with persona combinations, whether fingerprint dedup correctly handles Unicode. |
| **Risk** | Logic errors in SearchStrategyService are only caught at runtime, not in offline tests. |
| **Recommendation** | Add Python unit tests that replicate the fingerprint generation and MAX_JOBS calculation logic (these are deterministic algorithms). Test edge cases: empty keywords, special characters, all 9 personas × variable product counts. |

### R13 — No test for route handler files (only existence, not content validity)

| Field | Detail |
|-------|--------|
| **Severity** | **LOW** |
| **Location** | `crm-extension/tests/test_extension_skeleton.py` |
| **Description** | Skeleton tests verify route JSON parity and that PHP handler files exist, but do not validate that the handler class names in routes.json match actual class declarations in the PHP files. |
| **Risk** | Route pointing to non-existent class (typo in actionClassName) passes static validation but fails at runtime. |
| **Recommendation** | Add PHP file content scan: for each route's `actionClassName`, verify the corresponding PHP file contains `class <ClassName>`. Low priority — rarely changes. |

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|-----------|
| CRITICAL | 0 | No critical issues found |
| HIGH | 2 | Hardcoded credentials in provisioning; no automated cleanup |
| MEDIUM | 5 | Env-gated live tests not auto-skipped; stale historical counts; wrong import path in README; no acceptance timeout; missing service logic unit tests |
| LOW | 4 | Missing __init__.py; fixed version string; mock fragility; route handler content not validated |
| INFO | 1 | MemoryStore != real CRM behavior |

### No Issues Found

The following were specifically checked and found to have **no problems**:

- ✅ **No fixed IDs** — test data uses generated or constant IDs (`job-001`, `candidate-1`, etc.), not database IDs
- ✅ **No order dependencies** — test methods are independent; no shared mutable state between tests
- ✅ **No exception swallowing** — exceptions are explicitly asserted or classified; no bare `except: pass`
- ✅ **No fake results masquerading as runtime verified** — documentation clearly labels "Static Verified" vs "Runtime Verified" vs "TBD"
- ✅ **No duplicate tests** — each test file covers distinct concerns; no copy-paste between suites
- ✅ **Test names match assertions** — method names accurately describe what they verify
- ✅ **No secret leakage in test code** — API keys, passwords, tokens are all test constants or env vars; error messages verified to scrub secrets
- ✅ **No dangerous privilege bypass** — tests use dedicated test roles/users; no admin credential sharing; real client tests reject remote URLs
- ✅ **No tests that can't run on clean environment** — all offline tests require only Python 3.12 + repo checkout

## Related Documents

- [TEST_INVENTORY.md](TEST_INVENTORY.md) — complete test file catalog
- [TEST_PLAN.md](TEST_PLAN.md) — test layer overview
