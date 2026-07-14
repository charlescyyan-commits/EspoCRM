# Regression Matrix

**Status:** Phase T01 Audit — 2026-07-13

> Maps functional areas to their minimal regression test sets. Each area lists what MUST run after a change, what should run CONDITIONALLY (depending on change scope), and what is OPTIONAL but beneficial.

> **T02 entrypoint:** `powershell -ExecutionPolicy Bypass -File scripts/testing/run-tests.ps1 regression` executes the currently required offline extension, connector/contract, worker, and static regression sets. Detailed mapping and exit codes are in [UNIFIED_TEST_ENTRYPOINTS.md](UNIFIED_TEST_ENTRYPOINTS.md).

> **T03 gate:** `powershell -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1` always runs that complete required set and produces a CI-ready JSON summary. Its path-to-impact mapping is maintained in `scripts/testing/regression-gate-map.json`.

> **T04 runtime harness:** `powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 all` is conditional on the documented local-only environment contract. It is intentionally separate from the T03 gate and is not CI-enabled.

---

## Change Area → Regression Map

### 1. Extension Metadata (`crm-extension/Resources/`, `crm-extension/files/`)

**What changes:** entityDefs, layouts, clientDefs, scopes, aclDefs, routes, i18n, formula, selectDefs, dashlets, app/layouts.json, manifest.json

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Extension skeleton (full) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **MANDATORY** | SearchStrategy foundation | `python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v` |
| **MANDATORY** | SearchStrategy detail view (if client files changed) | `python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v` |
| **CONDITIONAL** | Connector full suite (if routes or entityDefs affecting sync changed) | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **OPTIONAL** | Connector API client (if routes changed) | `python -m unittest chitu-connector.tests.test_espocrm_connector_api -v` |

**Rationale:** Extension metadata is the broadest change surface. Skeleton tests cover manifest, entity parity, field types, layout sections, routes, PHP inventory, and provisioning script content. SearchStrategy foundation covers the strategy entity specifically. Detail view test covers client JS artifacts.

---

### 2. Connector (`chitu-connector/`)

**What changes:** sync adapter, mapper, gate, contract, lifecycle, email lifecycle, feedback API, Brevo API, signal export, real client, connector API client

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Connector full suite | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **MANDATORY** | Extension skeleton (routes/contract tests) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **CONDITIONAL** | Live client safety (if real_client changed) | `python -m unittest chitu-connector.tests.test_espocrm_real_client -v` |
| **OPTIONAL** | Runtime acceptance (if contract shape changed) | `python deployment/validation/phase3c02_1_api_acl_acceptance.py` |

**Rationale:** Connector changes can break sync contract, gate logic, or CRM field mapping. Full connector suite is mandatory because modules are interdependent (mapper → gate → adapter → client). Extension skeleton catches route/metadata mismatches.

---

### 3. SearchStrategy / SearchJob / ProspectPool (`crm-extension/files/` acquisition entities)

**What changes:** entityDefs, services (SearchStrategyService, SearchStrategyTemplates), APIs (PostGenerateSearchStrategyJobs), Select filters, dashlets, provisioning scripts

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Extension skeleton (acquisition-specific tests) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **MANDATORY** | Worker core | `python -m unittest chitu-connector.tests.test_phase3c02_2b_acquisition_worker_core -v` |
| **MANDATORY** | Worker persistence hardening | `python -m unittest chitu-connector.tests.test_phase3c02_2b1_worker_persistence_hardening -v` |
| **MANDATORY** | Job runner | `python -m unittest chitu-connector.tests.test_phase3c02_2c_job_runner -v` |
| **CONDITIONAL** | Connector full suite (if entity models affect sync) | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **OPTIONAL** | Runtime ACL acceptance (if ACL changed) | `python deployment/validation/phase3c02_1_api_acl_acceptance.py` |
| **OPTIONAL** | Runtime generate-jobs (if service logic changed) | Manual: generate-jobs UI test per MANUAL_TESTS.md |

**Rationale:** Acquisition entities are coupled to worker/runner through SearchJob models and ProspectPool persistence. Worker tests validate the core job→prospect pipeline. Runner tests validate the CLI→repository→CRM path. Skeleton tests validate metadata parity and provisioning scripts.

---

### 4. Worker Core (`chitu_connector/acquisition/worker.py`)

**What changes:** AcquisitionWorker, job execution logic, provider interface, normalization, dedup

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Worker core | `python -m unittest chitu-connector.tests.test_phase3c02_2b_acquisition_worker_core -v` |
| **MANDATORY** | Worker persistence hardening | `python -m unittest chitu-connector.tests.test_phase3c02_2b1_worker_persistence_hardening -v` |
| **MANDATORY** | Job runner (integration path) | `python -m unittest chitu-connector.tests.test_phase3c02_2c_job_runner -v` |
| **CONDITIONAL** | Connector full suite (if models shared with sync changed) | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **OPTIONAL** | Runtime runner end-to-end | Manual: `python -m chitu_connector.acquisition.runner run-job --job-id <id> --provider fake` |

**Rationale:** Worker core is the heart of the acquisition pipeline. Three test files must pass: core logic (10 tests), persistence fault tolerance (8 tests), and CLI integration (15 tests). Runner tests verify the end-to-end path from CLI→repository→worker→provider→persist.

---

### 5. ACL / Roles (`deployment/provisioning/phase*_provision_*.php`, `crm-extension/Resources/acl/`)

**What changes:** role provisioning scripts, ACL definitions, permission matrices

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Extension skeleton (ACL provisioning script content) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **CONDITIONAL** | Runtime ACL acceptance (if scope-level permissions changed) | `python deployment/validation/phase3c02_1_api_acl_acceptance.py` |
| **OPTIONAL** | Manual dashboard ACL check | Manual: per MANUAL_TESTS.md Dashboard/Operations section |

**Rationale:** Skeleton tests validate provisioning script content (role names, scope lists, permission strings). Runtime acceptance validates actual API enforcement. Most ACL changes are scope-level additions; skeleton tests catch script regressions.

---

### 6. UI Metadata (`crm-extension/files/client/`, layouts, clientDefs, dashlets)

**What changes:** client-side JS, layout JSON, clientDefs, dashlet metadata, i18n labels

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Extension skeleton (layout sections, filter lists, dashlet configs, panel definitions, i18n keys) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **MANDATORY** | SearchStrategy detail view (if client views changed) | `python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v` |
| **CONDITIONAL** | SearchStrategy foundation (if strategy UI changed) | `python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v` |
| **OPTIONAL** | Browser acceptance (if user-visible changes) | **NOT IMPLEMENTED** — manual verification only |

**Rationale:** UI metadata changes are caught by skeleton layout/filter/dashlet tests. Detail view test specifically covers the SearchStrategy action handler pattern. Browser acceptance would be ideal but doesn't exist yet.

---

### 7. Packaging (`build_release_package.ps1`, ZIP artifacts)

**What changes:** build script, manifest version, file structure

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Extension skeleton (manifest + PHP inventory + directory structure) | `python -m unittest crm-extension.tests.test_extension_skeleton -v` |
| **MANDATORY** | Manual ZIP validation | Check ZIP root has only `manifest.json` + `files/`; paths use forward slashes; SHA-256 recorded |
| **CONDITIONAL** | Connector full suite (pre-release gate) | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **OPTIONAL** | Runtime install + rebuild | **NOT IMPLEMENTED** — manual verification only |

**Rationale:** Skeleton tests are the primary packaging gate. Manual ZIP validation is mandatory because no automated packaging test exists. Connector suite is conditional: run it pre-release but not required for a build-script-only change.

---

### 8. REST Adapter (`chitu_connector/acquisition/espo_repository.py`, `runner.py`)

**What changes:** EspoAcquisitionRepository, RunnerConfig, runner.main(), CLI args

| Priority | Tests | Command |
|----------|-------|---------|
| **MANDATORY** | Job runner (EspoRepositoryTests + RunnerCliTests) | `python -m unittest chitu-connector.tests.test_phase3c02_2c_job_runner -v` |
| **MANDATORY** | Worker persistence hardening (repository interaction) | `python -m unittest chitu-connector.tests.test_phase3c02_2b1_worker_persistence_hardening -v` |
| **CONDITIONAL** | Worker core (if repository interface changed) | `python -m unittest chitu-connector.tests.test_phase3c02_2b_acquisition_worker_core -v` |
| **CONDITIONAL** | Connector full suite (if shared HTTP patterns changed) | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` |
| **OPTIONAL** | Runtime runner end-to-end | Manual: fake provider job run against local CRM |

**Rationale:** The REST adapter is the bridge between Python runner and EspoCRM. Runner tests cover CLI, config, repository HTTP layer, claim/update semantics, and boundary isolation. Worker tests cover the repository interface contract.

---

## Quick-Reference: Complete Mandatory Regression

Run all mandatory tests for a pre-commit or pre-release gate:

```powershell
cd D:\EspoCRM-Production
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"

# Layer 1: Static Validation
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v
python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v

# Layer 2: Unit Tests
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

**Expected outcome:** ~136 test methods, 0 failures, 0 errors.

---

## Priority Definitions

| Level | Meaning | When to run |
|-------|---------|-------------|
| **MANDATORY** | Must pass before commit/release. Failure blocks. | Every commit, every PR, every release |
| **CONDITIONAL** | Must pass if the changed area overlaps. | When change touches shared interfaces or data models |
| **OPTIONAL** | Beneficial for confidence; not required. | Pre-release, or when specific risk indicators triggered |

---

## Related Documents

- [TEST_PLAN.md](TEST_PLAN.md) — test layer overview and categories
- [TEST_INVENTORY.md](TEST_INVENTORY.md) — complete test file catalog
- [COVERAGE_MATRIX.md](COVERAGE_MATRIX.md) — capability coverage status
