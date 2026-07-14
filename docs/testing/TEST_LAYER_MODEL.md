# Test Layer Model

**Status:** Phase T01 Audit — 2026-07-13

> Defines the recommended test layer architecture for the EspoCRM Production workspace. Each layer has a distinct responsibility, anti-scope, run frequency, and gate behavior. No actual test code is created in Phase T01.

---

## Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│ Layer 10: Security & Residue Checks                     │
│ (Secret scanning, cleanup verification)                 │
├─────────────────────────────────────────────────────────┤
│ Layer 9: Performance Tests                              │
│ (Latency, throughput, bulk operations)                  │
├─────────────────────────────────────────────────────────┤
│ Layer 8: Upgrade & Rollback Tests                       │
│ (Install→upgrade→verify; install→rollback→verify)       │
├─────────────────────────────────────────────────────────┤
│ Layer 7: Packaging & Installation Tests                 │
│ (ZIP validation, install smoke, rebuild)                │
├─────────────────────────────────────────────────────────┤
│ Layer 6: Browser Acceptance Tests                       │
│ (Playwright UI workflows, visual regression)            │
├─────────────────────────────────────────────────────────┤
│ Layer 5: Runtime REST Tests                             │
│ (Real EspoCRM API calls, test data with markers)        │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Integration Tests                              │
│ (Connector ↔ CRM, multi-module scenarios)               │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Contract Tests                                 │
│ (Sync contract schema, API contracts, ACL contracts)    │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Unit Tests                                     │
│ (Worker core, CLI runner, repository, sync adapter)     │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Static Validation                              │
│ (JSON structure, metadata parity, PHP inventory)        │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: Static Validation

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Validate extension metadata structure, JSON parity, PHP file inventory, route definitions, field models, layout sections, provisioning script content — all without executing any PHP or connecting to any system |
| **What NOT to test** | Runtime behavior, database queries, API responses, business logic, UI rendering, performance |
| **Run frequency** | Pre-commit, pre-build, CI on every push |
| **CRM required** | No |
| **Produces data** | No |
| **Must cleanup** | No |
| **Blocks next Phase on failure** | Yes — static validation failures block all further phases |
| **Current state** | **IMPLEMENTED** — `test_extension_skeleton.py` (26 methods, ~42 assertions), `test_phase3c02_search_strategy_foundation.py` (2 methods), `test_phase3c02_1a_search_strategy_detail.py` (2 methods) |
| **Recommended tool** | Python `unittest` (stdlib) |
| **Gap assessment** | Good coverage. Missing: JSON schema validation against EspoCRM entityDefs schema, automated i18n key coverage check |

---

## Layer 2: Unit Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Test business logic units in isolation: worker core, provider interaction, domain normalization, dedup, persistence error handling, sync adapter, mapper, gate evaluation, runner CLI, Espo repository HTTP layer |
| **What NOT to test** | Real CRM database, real network calls, real provider APIs, UI rendering, file system side effects beyond mocks |
| **Run frequency** | Pre-commit, CI on every push |
| **CRM required** | No |
| **Produces data** | No |
| **Must cleanup** | No |
| **Blocks next Phase on failure** | Yes — unit test failures block integration and above |
| **Current state** | **IMPLEMENTED** — 11 test files in `chitu-connector/tests/` (~86 test methods). Covers sync adapter, connector API, worker core, persistence hardening, job runner, lifecycle sync, email lifecycle, feedback API, Brevo API, signal export, real client safety |
| **Recommended tool** | Python `unittest` (stdlib) — current working tool; pytest acceptable as drop-in |
| **Gap assessment** | Good depth. Missing: unit tests for SearchStrategyTemplates logic, SearchStrategyService validation edge cases in isolation. Some tests at Layer 2 (e.g., connector API mocks) straddle Layer 3. |

---

## Layer 3: Contract Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Validate sync contract schema compliance, API contract shape (request/response schemas), ACL contract (who can do what), route contract (method+path+handler), idempotency contract |
| **What NOT to test** | Actual CRM data, actual HTTP latency, provider behavior |
| **Run frequency** | Pre-release, on contract changes |
| **CRM required** | No (schema-based); partial (live contract validation needs env) |
| **Produces data** | No |
| **Must cleanup** | No |
| **Blocks next Phase on failure** | Yes — contract violations block integration and acceptance |
| **Current state** | **PARTIALLY IMPLEMENTED** — Sync contract validation exists in `test_espocrm_sync_adapter.py` (ContractTests). Route parity tests in skeleton. Missing: ACL contract tests (permission matrix validatable without CRM), SearchStrategy generate-jobs request/response schema, ProspectPool CRUD contract |
| **Recommended tool** | Python `unittest` + JSON Schema validation, OpenAPI / contract-first design |
| **Gap assessment** | Sync contract well-covered. ACL and REST API contracts missing offline validation. |

---

## Layer 4: Integration Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Test connector ↔ CRM interaction through mocked CRM or disposable local instance: full sync pipeline (mock→CRM API), worker→repository→CRM, multi-module scenarios (sync + feedback + email), lifecycle state machine end-to-end |
| **What NOT to test** | Real search providers, production CRM, browser UI, performance |
| **Run frequency** | Pre-release, on connector or CRM entity changes |
| **CRM required** | Partial — disposable local instance or MockEspoCRMClient |
| **Produces data** | Yes (if using live disposable CRM) |
| **Must cleanup** | Yes — all test data must be removed via markers |
| **Blocks next Phase on failure** | Yes — integration failures block runtime acceptance |
| **Current state** | **PARTIALLY IMPLEMENTED** — `MockEspoCRMClient` exists for unit-level integration testing. Real client integration gated behind `ESPOCRM_TEST_ENV`. Live runner end-to-end planned but deferred (Phase C02.2C-R). Missing: disposable CRM integration suite, multi-phase workflow integration test |
| **Recommended tool** | Python `unittest` + disposable Docker EspoCRM container |
| **Gap assessment** | The MockEspoCRMClient is good for Layer 2 but doesn't replace real CRM integration. Need a disposable CRM test harness. |

---

## Layer 5: Runtime REST Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Execute real HTTP calls against a live EspoCRM REST API: CRUD operations, generate-jobs endpoint, route responses, error handling, auth rejection, rate limiting |
| **What NOT to test** | Browser UI, provider APIs, performance baselines |
| **Run frequency** | Pre-release, nightly (if automated CRM available) |
| **CRM required** | Yes — disposable or dedicated test EspoCRM instance |
| **Produces data** | Yes — test records with `[CHITU_TEST]` markers |
| **Must cleanup** | Yes — mandatory automated cleanup after each run |
| **Blocks next Phase on failure** | Yes — REST failures block browser acceptance and release |
| **Current state** | **PARTIALLY IMPLEMENTED** — `phase3c02_1_api_acl_acceptance.py` exists but requires manual CRM setup. No automated CRM provisioning. No nightly/CI runtime. Deferred as TBD in TEST_PLAN.md. |
| **Recommended tool** | Python `unittest` + EspoCRM REST API (stdlib `urllib` sufficient) |
| **Gap assessment** | Acceptance script is solid but blocked on CRM availability. Need: automated CRM provisioning, test data lifecycle management, non-interactive runner. |

---

## Layer 6: Browser Acceptance Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Drive actual browser workflows: login as different roles, navigate to Lead detail/ProspectPool/SearchStrategy, click generate-jobs, verify UI elements, check ACL visual enforcement, verify dashboard tiles |
| **What NOT to test** | API logic, backend business rules, performance, search provider quality |
| **Run frequency** | Pre-release, weekly |
| **CRM required** | Yes — disposable EspoCRM with extension installed |
| **Produces data** | Yes — creates visible CRM records |
| **Must cleanup** | Yes — test data removed after run |
| **Blocks next Phase on failure** | Yes — browser failures block release |
| **Current state** | **NOT IMPLEMENTED** — zero browser tests exist. Manual test procedures documented in MANUAL_TESTS.md but not automated. |
| **Recommended tool** | Playwright (Python or JS), Selenium |
| **Gap assessment** | Critical gap. All UI/UX verification currently manual. |

---

## Layer 7: Packaging & Installation Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Validate ZIP structure (manifest.json at root, files/ directory, forward-slash paths), verify build reproducibility, confirm install→rebuild→entity visibility, confirm uninstall cleanup |
| **What NOT to test** | Business logic, UI, performance |
| **Run frequency** | Pre-release only |
| **CRM required** | Yes — disposable EspoCRM for install/uninstall verification |
| **Produces data** | Yes — extension installation creates entities/fields |
| **Must cleanup** | Yes — uninstall and verify module files removed |
| **Blocks next Phase on failure** | Yes — packaging failures block release |
| **Current state** | **NOT IMPLEMENTED** — manual build process only (`build_release_package.ps1`). No automated ZIP validation, install verification, or uninstall check. |
| **Recommended tool** | Python `zipfile` + `unittest` for ZIP validation; Docker EspoCRM for install tests |
| **Gap assessment** | Significant gap. Every release currently relies on manual verification. |

---

## Layer 8: Upgrade & Rollback Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Test upgrade path from N-1 version to current, verify data integrity after upgrade, verify metadata merge doesn't lose customizations, test rollback restores previous state |
| **What NOT to test** | New feature behavior (that's Layer 2-5), performance regression |
| **Run frequency** | Pre-release only |
| **CRM required** | Yes — disposable EspoCRM with previous version installed |
| **Produces data** | Yes — installs extensions, creates test data |
| **Must cleanup** | Yes — full instance teardown or rollback |
| **Blocks next Phase on failure** | Yes — upgrade/rollback failures block release |
| **Current state** | **NOT IMPLEMENTED** — no automated upgrade or rollback tests. Manual procedures referenced in deployment docs. |
| **Recommended tool** | Docker EspoCRM snapshots, Python orchestration |
| **Gap assessment** | Critical gap for production readiness. |

---

## Layer 9: Performance Tests

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Establish baseline latency/throughput for: List API (Lead, SearchJob, ProspectPool), filter application, bulk job generation (1-40 jobs), connector sync round-trip, batch prospect creation |
| **What NOT to test** | Search provider performance, browser rendering speed, network latency (external) |
| **Run frequency** | Pre-release, on significant entity/query changes |
| **CRM required** | Yes — dedicated performance test instance |
| **Produces data** | Yes — bulk test records |
| **Must cleanup** | Yes — remove all generated records |
| **Blocks next Phase on failure** | Conditional — regression from baseline blocks; absolute thresholds are advisory |
| **Current state** | **NOT IMPLEMENTED** — zero performance tests. |
| **Recommended tool** | Python `timeit`/`pytest-benchmark`, or `k6`/`locust` for API load |
| **Gap assessment** | Important for production planning but lower priority than Layers 1-5. |

---

## Layer 10: Security & Residue Checks

| Attribute | Value |
|-----------|-------|
| **Responsibility** | Scan for hardcoded secrets in source/test/provisioning files, verify test cleanup leaves no residue, verify API key handling, verify environment safety guards, check for privilege escalation paths in ACL |
| **What NOT to test** | Penetration testing, external vulnerability scanning, social engineering |
| **Run frequency** | Pre-commit (secret scanning), pre-release (full), post-test (residue) |
| **CRM required** | Partial — residue checks need CRM; secret scanning is offline |
| **Produces data** | No (scanning only) |
| **Must cleanup** | N/A |
| **Blocks next Phase on failure** | Yes — secret leakage or residue contamination blocks release |
| **Current state** | **PARTIALLY IMPLEMENTED** — Worker tests verify secrets scrubbed from error messages. LocalEspoCRMClient has env safety guards. Manual audit confirms no secrets in test files. Missing: automated secret scanning (truffleHog, git-secrets), automated residue check after test runs, provisioning script hardcoded credential audit |
| **Recommended tool** | `truffleHog`, `git-secrets`, or `detect-secrets`; custom residue scanner |
| **Gap assessment** | Good manual coverage. Needs automation for CI integration. Provisioning script credentials need environment variable migration. |

---

## Layer Interaction Rules

1. **Lower layers gate upper layers.** Layer N must pass before Layer N+1 is meaningful.
2. **Upper layers do not replace lower layers.** A browser test passing does not excuse a missing unit test.
3. **Mock fidelity increases with layers.** Layer 2 uses in-memory doubles; Layer 4 uses MockEspoCRMClient or disposable CRM; Layer 5 uses real REST API.
4. **Data side effects increase with layers.** Layers 1-3 produce zero data; Layers 4-5 produce test-marked data; Layers 6-8 produce visible data requiring cleanup.
5. **Run frequency decreases with layers.** Layer 1-2: every push; Layer 5: nightly; Layer 6: weekly; Layer 7-9: pre-release only.

---

## Current Implementation Status

| Layer | Status | Tests | Files |
|-------|--------|-------|-------|
| 1. Static Validation | **Implemented** | ~30 methods | 3 Python files |
| 2. Unit Tests | **Implemented** | ~86 methods | 11 Python files |
| 3. Contract Tests | **Partial** | ~22 methods (sync contract only) | 1 Python file |
| 4. Integration Tests | **Partial** | Mocked only; no disposable CRM harness | — |
| 5. Runtime REST Tests | **Partial** | 1 acceptance script (TBD) | 1 Python file |
| 6. Browser Acceptance | **Not Implemented** | 0 | — |
| 7. Packaging & Install | **Not Implemented** | 0 | — |
| 8. Upgrade & Rollback | **Not Implemented** | 0 | — |
| 9. Performance | **Not Implemented** | 0 | — |
| 10. Security & Residue | **Partial** | Manual only; no automated scanning | — |
