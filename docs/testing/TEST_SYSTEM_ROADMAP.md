# Test System Roadmap

**Status:** Phase T01 Audit — 2026-07-13

> Defines subsequent phases (T02–T08) for building out the test system. Each phase has a goal, scope, likely files, dependencies, conflict risk assessment, recommended tools, and acceptance criteria. Phases are designed to be executed sequentially but some components can be parallelized (see §8).

---

## T02 — Unified Test Entrypoints

### Goal
Create a single, documented entrypoint for running all offline tests. Standardize PYTHONPATH, discovery, and output format. Do NOT rewrite business tests.

### Scope
- Create `run_all_tests.py` or `run_all_tests.ps1` at repo root
- Standardize PYTHONPATH handling (no manual `$env:PYTHONPATH` needed)
- Aggregate test output (pass/fail/skip counts, elapsed time)
- Add `--layer` filter (e.g., `--layer static`, `--layer unit`, `--layer all`)
- Update `docs/developer/TESTING.md` with new entrypoint
- Create `.python-version` or document Python version requirement
- Ensure all tests are discoverable from repo root with one command

### Files Likely Affected
- `run_all_tests.py` (NEW)
- `run_all_tests.ps1` (NEW)
- `docs/developer/TESTING.md` (UPDATE)
- `docs/testing/TEST_PLAN.md` (UPDATE)
- `docs/testing/REGRESSION.md` (UPDATE)

### Dependencies
- **None** — pure test infrastructure, no source changes

### Conflict Risk with Phase3C
**SAFE TO PARALLEL** — touches only test runner scripts and docs. Does not modify source, extension metadata, connector code, or deployment scripts.

### Recommended Tool
- Python with `unittest` discovery
- PowerShell for Windows-native entrypoint

### Recommended Model
- Haiku 4.5 (simple scripting, no deep analysis needed)

### Acceptance Criteria
- [ ] Single command runs all offline tests from repo root
- [ ] PYTHONPATH set automatically
- [ ] Exit code 0 when all pass, non-zero on failure
- [ ] Layer filter works (`--layer static` runs only skeleton + foundation + detail view)
- [ ] Output shows test count, pass/fail, and elapsed time
- [ ] All existing tests pass under new entrypoint

---

## T03 — Core Regression Gate

### Goal
Establish a formal regression gate for Extension, Connector, and Worker changes. Add targeted missing unit tests without rewriting existing suites.

### Scope
- Create `tests/` directory at repo root (currently missing)
- Add Python contracts for ACL role matrix (validateable offline)
- Add unit tests for SearchStrategyTemplates fingerprint logic
- Add unit tests for SearchStrategyService validation edge cases
- Add `@unittest.skipIf` guard to live real client tests
- Add `__init__.py` to `chitu-connector/tests/`
- Fix `crm-extension/tests/README.md` stale import path
- Add SUPERSEDED banners to historical test reports

### Files Likely Affected
- `tests/__init__.py` (NEW)
- `tests/test_acl_contract.py` (NEW)
- `tests/test_search_strategy_logic.py` (NEW)
- `chitu-connector/tests/__init__.py` (NEW)
- `chitu-connector/tests/test_espocrm_real_client.py` (UPDATE — skipIf)
- `crm-extension/tests/README.md` (UPDATE — fix command)
- `docs/testing/ESPOCRM_SYNC_ADAPTER_TEST_REPORT_V1.md` (UPDATE — banner)
- `docs/testing/ESPOCRM_SYNC_TEST_PLAN_V1.md` (UPDATE — banner)
- `docs/testing/PHASE3A22B_*` (UPDATE — banners)

### Dependencies
- T02 (unified entrypoints) — recommended but not strictly required

### Conflict Risk with Phase3C
**LOW RISK** — adds new test files in new `tests/` directory. Small edits to existing test files (skipIf, __init__.py). Does not modify source code, extension metadata, or deployment scripts. Phasing: must not add SearchStrategy logic tests that depend on unstable C03 behavior — only test stable C02.1/C02.2 logic.

### Recommended Tool
- Python `unittest`

### Recommended Model
- Sonnet 5 (logic validation requires careful analysis)

### Acceptance Criteria
- [ ] ACL contract tests validate role×scope×permission matrix offline
- [ ] SearchStrategy fingerprint/MAX_JOBS logic tested with edge cases
- [ ] Live real client tests auto-skipped without `ESPOCRM_TEST_ENV=true`
- [ ] Historical test reports clearly marked SUPERSEDED
- [ ] All existing tests still pass
- [ ] No source code modified (only tests + docs)

---

## T04 — Runtime Test Harness

### Goal
Create a reusable local EspoCRM REST test harness with automated test data management and cleanup.

### Scope
- Create `tests/runtime/` directory with shared harness
- Unified test marker system (e.g., `[CHITU_T04_TEST]`)
- Session-based test data tracking (create→use→cleanup lifecycle)
- Mandatory cleanup assertion (tests fail if residue found)
- Configurable CRM target (env vars, not hardcoded)
- Refactor `phase3c02_1_api_acl_acceptance.py` to use shared harness
- Add offline test mode: verify harness logic without live CRM
- Add `--offline` flag that skips live tests

### Files Likely Affected
- `tests/runtime/__init__.py` (NEW)
- `tests/runtime/harness.py` (NEW)
- `tests/runtime/espo_client.py` (NEW)
- `tests/runtime/test_data_manager.py` (NEW)
- `tests/runtime/test_espocrm_rest_crud.py` (NEW)
- `tests/runtime/test_generate_jobs_api.py` (NEW)
- `tests/runtime/test_acl_acceptance.py` (NEW — refactored from deployment)
- `deployment/validation/phase3c02_1_api_acl_acceptance.py` (UPDATE — delegate to harness or deprecated)
- `docs/testing/TEST_PLAN.md` (UPDATE)

### Dependencies
- T02 (unified entrypoints) — required for clean integration
- Disposable EspoCRM instance (Docker recommended)
- Provisioning scripts must have been run on target CRM

### Conflict Risk with Phase3C
**LOW RISK** — new directory `tests/runtime/`. Touches deployment validation scripts but only to refactor (not change behavior). Does not modify core source code. The harness itself is C03-independent; only the test cases that target C03 behavior depend on C03 stability.

### Recommended Tool
- Python `unittest` + `urllib` (stdlib)
- Docker EspoCRM for disposable test instance

### Recommended Model
- Opus 4.8 (harness design requires careful architecture)

### Acceptance Criteria
- [ ] Shared harness provides: CRM client, test data manager, cleanup tracker
- [ ] Unified test marker across all runtime tests
- [ ] Cleanup runs automatically (not manual `--cleanup` flag)
- [ ] Tests fail if cleanup leaves residue
- [ ] `--offline` flag skips live tests
- [ ] All offline tests still pass
- [ ] Live tests pass against disposable CRM (documented setup)

---

## T05 — Browser Acceptance Tests

### Goal
Establish Playwright-based browser acceptance tests for critical UI workflows.

### Scope
- Install Playwright for Python
- Create `tests/browser/` directory
- Test 1: Lead detail view rendering (all sections, tabs, relationship panels)
- Test 2: SearchStrategy create → generate jobs → verify SearchJob list
- Test 3: Dashboard tile rendering (Prospecting Operations, Acquisition)
- Test 4: ACL visual enforcement (login as each role, verify menu visibility)
- Test 5: ProspectPool list filtering
- Reusable page objects for CRM entities
- Screenshot on failure for debugging

### Files Likely Affected
- `tests/browser/__init__.py` (NEW)
- `tests/browser/conftest.py` (NEW)
- `tests/browser/page_objects/` (NEW, multiple files)
- `tests/browser/test_lead_detail.py` (NEW)
- `tests/browser/test_search_strategy_workflow.py` (NEW)
- `tests/browser/test_dashboards.py` (NEW)
- `tests/browser/test_acl_visual.py` (NEW)
- `requirements-browser.txt` or `pyproject.toml` update (NEW dependency)
- `docs/testing/TEST_PLAN.md` (UPDATE)
- `docs/testing/MANUAL_TESTS.md` (UPDATE — mark automated tests)

### Dependencies
- T04 (runtime harness) — required for CRM state setup/cleanup
- Disposable EspoCRM with extension installed
- Playwright + browser binaries

### Conflict Risk with Phase3C
**SAFE TO PARALLEL** — entirely new directory. No existing files modified. Tests interact with CRM through browser, not source code. Phase3C changes to UI metadata would need corresponding test updates, but that's a natural dependency, not a conflict.

### Recommended Tool
- Playwright for Python (`playwright` package)
- pytest (better fixture/plugin support than unittest for browser tests)

### Recommended Model
- Opus 4.8 (browser test authoring requires precision)

### Acceptance Criteria
- [ ] 4 browser test suites covering critical workflows
- [ ] Page objects reusable across tests
- [ ] Screenshots captured on failure
- [ ] Tests runnable with single command
- [ ] Tests pass against disposable CRM with extension installed
- [ ] Does not modify existing source/test files

---

## T06 — Install / Upgrade / Rollback Tests

### Goal
Automate extension packaging validation, installation verification, upgrade path testing, and rollback confirmation.

### Scope
- ZIP structure validation (automated, not manual)
- Install test: build ZIP → install on disposable CRM → rebuild → verify entities/scopes/layouts
- Upgrade test: install N-1 version → upgrade to current → verify data preserved
- Rollback test: install current → create data → rollback to N-1 → verify state
- Uninstall test: uninstall extension → verify module files removed → verify entities gone
- SHA-256 automated verification against sidecar files

### Files Likely Affected
- `tests/packaging/__init__.py` (NEW)
- `tests/packaging/test_zip_structure.py` (NEW)
- `tests/packaging/test_install.py` (NEW)
- `tests/packaging/test_upgrade.py` (NEW)
- `tests/packaging/test_rollback.py` (NEW)
- `tests/packaging/test_uninstall.py` (NEW)
- `tests/packaging/test_sha256.py` (NEW)
- `tests/packaging/espo_docker.py` (NEW — Docker CRM management)
- `docs/deployment/INSTALL.md` (UPDATE)
- `docs/deployment/UPGRADE.md` (UPDATE)
- `docs/deployment/ROLLBACK.md` (UPDATE)
- `docs/testing/TEST_PLAN.md` (UPDATE)

### Dependencies
- T04 (runtime harness) — required for CRM API interaction
- Docker (for disposable EspoCRM instances)
- Previous extension versions for upgrade/rollback tests

### Conflict Risk with Phase3C
**SAFE TO PARALLEL** — entirely new directory. Tests interact with CRM through API + Docker, not source code. Depends on build artifacts being stable but does not modify them.

### Recommended Tool
- Python `unittest` + `zipfile` + `hashlib` (stdlib)
- Docker SDK for Python or `subprocess` for docker CLI
- EspoCRM Docker image

### Recommended Model
- Opus 4.8 (infrastructure-heavy, needs careful design)

### Acceptance Criteria
- [ ] ZIP structure validated automatically (manifest root, files/ dir, path slashes)
- [ ] Install test: builds, installs, verifies entities exist
- [ ] Upgrade test: N-1 → N upgrade preserves data
- [ ] Rollback test: N → N-1 rollback verified
- [ ] Uninstall test: cleanup confirmed
- [ ] SHA-256 verification automated
- [ ] All packaging tests pass before release

---

## T07 — Performance Baseline

### Goal
Establish and track performance baselines for critical operations.

### Scope
- List API baseline: Lead list (100, 500, 1000 records), filter application
- SearchJob CRUD baseline: create, list, update status, delete
- Bulk job generation: 1, 10, 20, 40 jobs timing
- Connector sync round-trip: lead + evidence + proposal
- Bulk prospect creation: 10, 50, 100 prospects
- Results stored as JSON baselines; compared on subsequent runs
- Advisory thresholds (not hard gates) for initial version

### Files Likely Affected
- `tests/performance/__init__.py` (NEW)
- `tests/performance/conftest.py` (NEW)
- `tests/performance/test_list_baseline.py` (NEW)
- `tests/performance/test_job_generation_baseline.py` (NEW)
- `tests/performance/test_sync_baseline.py` (NEW)
- `tests/performance/test_prospect_creation_baseline.py` (NEW)
- `tests/performance/baselines/` (NEW — JSON baseline files)
- `docs/testing/TEST_PLAN.md` (UPDATE)

### Dependencies
- T04 (runtime harness) — required for CRM API interaction
- Dedicated performance test CRM instance (not shared with other tests)
- Sufficient test data volume

### Conflict Risk with Phase3C
**SAFE TO PARALLEL** — new directory, no existing files modified. May surface performance issues in C03 code but does not change it.

### Recommended Tool
- Python `timeit` or `pytest-benchmark`
- JSON for baseline storage

### Recommended Model
- Sonnet 5 (measurement code is straightforward)

### Acceptance Criteria
- [ ] Baseline measurements captured for 4 core operations
- [ ] Baselines stored as versioned JSON files
- [ ] Comparison mode: `--compare` flag shows delta from last baseline
- [ ] Tests pass if within 20% of baseline (advisory, not blocking)
- [ ] Documented how to run and interpret results

---

## T08 — CI Test Gate

### Goal
Integrate stable tests into a CI pipeline. Tests must be fast, reliable, and side-effect-free.

### Scope
- CI configuration (GitHub Actions or similar)
- Gate 1 (every push): Layer 1 + Layer 2 (static + unit, ~2 min)
- Gate 2 (PR): Layer 1 + 2 + 3 (static + unit + contract, ~3 min)
- Gate 3 (release): Layer 1-5 (static + unit + contract + integration + runtime, needs CRM)
- Secret scanning hook (pre-commit or CI)
- Test result reporting (JUnit XML for CI ingestion)
- Coverage reporting (optional, informational only)

### Files Likely Affected
- `.github/workflows/test.yml` (NEW — or equivalent CI config)
- `.github/workflows/release.yml` (NEW)
- `.pre-commit-config.yaml` (NEW — secret scanning)
- `run_all_tests.py` (UPDATE — JUnit XML output)
- `docs/testing/TEST_PLAN.md` (UPDATE)
- `docs/deployment/INSTALL.md` (UPDATE)

### Dependencies
- T02 (unified entrypoints) — required
- T03 (core regression gate) — required
- T04 (runtime harness) — required for Gate 3
- T07 (performance baseline) — optional, informational gate

### Conflict Risk with Phase3C
**WAIT FOR PHASE3C** — CI configuration is infrastructure-only and technically safe to add now, but the test content it gates (especially runtime) should wait for C03 stabilization. CI config can be drafted early but not activated until C03 code is stable.

### Recommended Tool
- GitHub Actions (preferred, repo is on a Git hosting platform)
- `truffleHog` or `detect-secrets` for secret scanning
- JUnit XML for test reporting

### Recommended Model
- Haiku 4.5 (CI YAML authoring)

### Acceptance Criteria
- [ ] Push gate: Layer 1 + 2 pass in under 3 minutes
- [ ] PR gate: Layers 1-3 pass in under 5 minutes
- [ ] Release gate: documented (not necessarily automated; needs CRM)
- [ ] Secret scanning blocks commits with credentials
- [ ] CI status visible in PR/commit UI
- [ ] Test failures produce actionable output (not just "1 test failed")

---

## Phase Sequencing

```
T01 (audit) ──► T02 (entrypoints) ──► T03 (regression gate) ──► T04 (runtime harness)
                                                                   │
                                                                   ├──► T05 (browser)
                                                                   ├──► T06 (install/upgrade)
                                                                   ├──► T07 (performance)
                                                                   └──► T08 (CI gate)
```

T02 and T03 can partially overlap. T04 is the prerequisite for T05, T06, T07, and T08. T05, T06, and T07 can run in parallel after T04.

---

## Parallel Conflict Analysis (with Phase3C)

### SAFE TO PARALLEL

| Work | Rationale |
|------|-----------|
| T02 — Unified Test Entrypoints | Pure test infrastructure. No source, metadata, or deployment changes. |
| T05 — Browser Acceptance | New directory. Page objects reference stable UI metadata only (not C03 behavior). |
| T06 — Install/Upgrade/Rollback | New directory. Tests packaging + install mechanics, not C03 business logic. |
| T07 — Performance Baseline | New directory. Measures existing operations, does not change behavior. |

### LOW RISK

| Work | Rationale |
|------|-----------|
| T03 — Core Regression Gate | Adds new test files. Small safe edits to existing tests. Must not test unstable C03 behavior. |
| T04 — Runtime Test Harness | New directory. Refactors acceptance script. Harness is C03-independent; only specific test cases depend on C03 stability. |

### WAIT FOR PHASE3C

| Work | Rationale |
|------|-----------|
| T08 — CI Test Gate (runtime portion) | CI config is infrastructure-safe, but the runtime gate requires stable C03 behavior. Draft CI early; activate after C03 stabilization. |
| Tests targeting SearchStrategy generate-jobs runtime behavior | C03 may change service logic, fingerprint format, or template rules. |
| Tests targeting ProspectPool→Lead bridge | Not yet implemented. Testing it would test nothing. |
| Tests targeting multi-runner concurrent claim safety | C02.2B/2C MVP is single-runner. Multi-runner not yet designed. |

### Key Principle
**Do not test unstable C03 business behavior in advance.** T02–T07 should test only:
1. Test infrastructure (harnesses, entrypoints, CI config)
2. Stable C01/C02.1/C02.2 behavior (already implemented and verified)
3. Packaging, installation, upgrade mechanics (independent of business logic)

---

## Related Documents

- [TEST_INVENTORY.md](TEST_INVENTORY.md) — what exists now
- [COVERAGE_MATRIX.md](COVERAGE_MATRIX.md) — what's covered and what's missing
- [TEST_LAYER_MODEL.md](TEST_LAYER_MODEL.md) — layer architecture
- [TEST_RELIABILITY_RISKS.md](TEST_RELIABILITY_RISKS.md) — known issues
