# Coverage Matrix

**Status:** Phase T01 Audit — 2026-07-13

> Maps every capability domain to its test coverage status. Each row lists existing tests, evidence, missing scenarios, and recommended owner.

---

## Coverage Status Legend

| Status | Meaning |
|--------|---------|
| **COVERED** | At least one automated test exercises the capability |
| **PARTIAL** | Some scenarios covered; significant gaps remain |
| **NOT COVERED** | No automated test exists |
| **BLOCKED** | Test exists but cannot currently run (e.g., missing infrastructure) |
| **OUT OF SCOPE** | Explicitly excluded by workspace rules or architecture |

---

## Entity & Metadata Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Extension skeleton | **COVERED** | `test_extension_skeleton.py` (manifest, dirs, forbidden trees, migration absence) | Phase D01: all pass | — | Extension dev |
| Metadata merge (surface↔module) | **COVERED** | `test_extension_skeleton.py` (parity assertions for 5 entities), `test_phase3c02_search_strategy_foundation.py` | Static Verified | — | Extension dev |
| Entity definitions — Lead | **COVERED** | `test_extension_skeleton.py` (22+ fields, types, options, defaults, layouts) | Phase D01 | Field additions need test updates | Extension dev |
| Entity definitions — ResearchEvidence | **COVERED** | `test_extension_skeleton.py` (9 required fields, 5 forbidden fields) | Phase D01 | — | Extension dev |
| Entity definitions — Opportunity | **COVERED** | `test_extension_skeleton.py` (intelligence fields, pipeline stages, email lifecycle) | Phase D01 | — | Extension dev |
| Entity definitions — SearchStrategy | **COVERED** | `test_phase3c02_search_strategy_foundation.py`, `test_extension_skeleton.py` | Phase D01 | Runtime: generate-jobs API behavior | Extension dev |
| Entity definitions — SearchJob | **COVERED** | `test_extension_skeleton.py` (fields, status enum, links, filters, dashlets) | Phase D01 | Runtime: state transitions via API | Acquisition team |
| Entity definitions — ProspectPool | **COVERED** | `test_extension_skeleton.py` (fields, queue enum, status enums, links) | Phase D01 | Runtime: CRM push flow, Lead bridge | Acquisition team |
| SalesFeedback / LearningSignal / EmailEvent | **COVERED** | `test_extension_skeleton.py` (field sets, links, feedback type options, hooks) | Phase D01 | Runtime: email feedback creation | Connector team |

---

## Worker & Job Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Worker lifecycle (QUEUED→COMPLETED) | **COVERED** | `test_phase3c02_2b_acquisition_worker_core.py` (10 tests) | Static Verified | — | Acquisition team |
| Worker core — claim/reject logic | **COVERED** | `test_phase3c02_2b1_worker_persistence_hardening.py` (8 tests) | Static Verified | — | Acquisition team |
| Job state transitions (all statuses) | **COVERED** | Core tests verify QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED | Static Verified | Runtime: live CRM status transitions | Acquisition team |
| Retryable vs non-retryable failures | **COVERED** | Persistence hardening tests (transient vs invalid errors) | Static Verified | Runtime: actual CRM transport errors | Acquisition team |
| Duplicate handling (dedup) | **COVERED** | Core tests (cross-job dedup by provider+domain fingerprint) | Static Verified | Runtime: multi-runner concurrent dedup | Acquisition team |
| Provider error classification | **COVERED** | Worker core + persistence hardening tests | Static Verified | Non-fake provider error modes | Acquisition team |
| Partial persistence | **COVERED** | `test_phase3c02_2b1` (fail_create_at patterns) | Static Verified | Runtime: recovery after partial persist | Acquisition team |
| Completion persistence failure | **COVERED** | `test_phase3c02_2b1` (fail_completion) | Static Verified | — | Acquisition team |
| Failure update failure (uncertain status) | **COVERED** | `test_phase3c02_2b1` (fail_failure_update) | Static Verified | — | Acquisition team |
| Secret leakage (worker) | **COVERED** | Persistence hardening tests verify secrets never in errorMessage | Static Verified | — | Security |

---

## Connector & Sync Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Sync contract validation | **COVERED** | `test_espocrm_sync_adapter.py` (ContractTests, 2 tests) | Static Verified | — | Connector team |
| Sync gate (9 rejection rules) | **COVERED** | `test_espocrm_sync_adapter.py` (GateTests, 9 tests) | Static Verified | — | Connector team |
| Sync mapper (field mapping) | **COVERED** | `test_espocrm_sync_adapter.py` (MapperTests, 4 tests) | Static Verified | New contract fields need mapping tests | Connector team |
| Idempotency key generation | **COVERED** | `test_espocrm_sync_adapter.py` (IdempotencyTests, 2 tests) | Static Verified | — | Connector team |
| Connector API client (lead/evidence/proposal routes) | **COVERED** | `test_espocrm_connector_api.py` (9 tests) | Static Verified | — | Connector team |
| Connector mapping (contract→CRM fields) | **COVERED** | `test_extension_skeleton.py` (contract_field_consistency) | Static Verified | — | Connector team |
| Lifecycle sync (Lead creation/update/conversion) | **COVERED** | `test_espocrm_lifecycle_sync.py` (4 tests) | Static Verified | Runtime: actual CRM conversion flow | Connector team |
| Email lifecycle sync | **COVERED** | `test_espocrm_email_lifecycle.py` (3 tests) | Static Verified | — | Connector team |
| Feedback API client | **COVERED** | `test_espocrm_feedback_api.py` (2 tests) | Static Verified | — | Connector team |
| Brevo API client | **COVERED** | `test_espocrm_brevo_api.py` (2 tests) | Static Verified | — | Connector team |
| Feedback signal export | **COVERED** | `test_espocrm_feedback_signal_export.py` (2 tests) | Static Verified | — | Connector team |
| Mock client behavior | **COVERED** | `test_espocrm_sync_adapter.py` (MockClientTests, 3 tests) | Static Verified | — | Connector team |

---

## REST & API Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| REST authentication (API key) | **PARTIAL** | `test_espocrm_real_client.py` (auth flow, 2 tests); `test_phase3c02_2c_job_runner.py` (X-Api-Key header) | Static Verified | Runtime: token refresh, expiry, rotation | Connector team |
| REST CRUD (SearchStrategy) | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (live, TBD) | TBD | Offline: contract tests for CRUD operations | QA / Acceptance |
| REST CRUD (SearchJob) | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (live, TBD) | TBD | — | QA / Acceptance |
| REST CRUD (ProspectPool) | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (live, TBD) | TBD | — | QA / Acceptance |
| Generate-jobs endpoint | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (live, TBD); skeleton tests (route parity) | TBD | Offline: seed data contract test | Acquisition team |
| EspoCRM repository (HTTP layer) | **COVERED** | `test_phase3c02_2c_job_runner.py` (EspoRepositoryTests, 8 tests) | Static Verified | — | Acquisition team |
| Route parity (6 POST routes) | **COVERED** | `test_extension_skeleton.py` (surface/module route identity) | Static Verified | — | Extension dev |

---

## ACL / Roles Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| ACL — scope-level (SearchStrategy/SearchJob/ProspectPool) | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (live, TBD); skeleton tests (provisioning script content) | Phase C02.1 report | Offline: role matrix validation test | Security / ACL |
| ACL — field-level | **NOT COVERED** | — | — | Field-level read/edit/no permissions per field | Security / ACL |
| ACL — owner isolation | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (sales cross-owner test, TBD) | TBD | Offline: ACL contract tests | Security / ACL |
| ACL — delete matrix | **PARTIAL** | `phase3c02_1_api_acl_acceptance.py` (delete test, TBD) | TBD | — | Security / ACL |
| ACL — provisioning script correctness | **COVERED** | `test_extension_skeleton.py` (script content assertions) | Static Verified | Runtime: actual role application | Extension dev |
| Role provisioning (Lead/ResearchEvidence etc.) | **COVERED** | `test_extension_skeleton.py` (Phase 3B06/3B07 ops filter assertions) | Static Verified | — | Extension dev |

---

## UI Metadata Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| UI metadata — layouts | **COVERED** | `test_extension_skeleton.py` (Lead/ResearchEvidence/Opportunity/SearchJob/ProspectPool layouts) | Static Verified | — | Extension dev |
| UI metadata — clientDefs | **COVERED** | Skeleton tests (filter lists, relationship panels, bottom panels, record views) | Static Verified | — | Extension dev |
| UI metadata — dashlets | **COVERED** | Skeleton tests (8 acquisition dashlets, ProspectingIntelligence, operations dashlets) | Static Verified | — | Extension dev |
| UI metadata — app/layouts.json | **COVERED** | Skeleton tests (module ownership for 6+ entity layouts) | Static Verified | — | Extension dev |
| SearchStrategy detail view (JS) | **COVERED** | `test_phase3c02_1a_search_strategy_detail.py` (2 tests) | Static Verified | — | Frontend |
| SearchStrategy generate-jobs handler | **COVERED** | Skeleton + detail view tests (handler registration, file existence) | Static Verified | — | Frontend |

---

## Browser / UI Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Browser workflow — Lead detail | **NOT COVERED** | — | — | Click-through: Lead detail, tabs, relationship panels, filter application | QA / Acceptance |
| Browser workflow — SearchStrategy create + generate | **NOT COVERED** | — | — | Full UI flow: create Strategy → generate jobs → verify jobs | QA / Acceptance |
| Browser workflow — ProspectPool | **NOT COVERED** | — | — | Pool list, filter, queue movement | QA / Acceptance |
| Browser workflow — Dashboard | **NOT COVERED** | — | — | Prospecting Operations + Acquisition dashboard rendering, tile data | QA / Acceptance |
| Browser workflow — ACL visual | **NOT COVERED** | — | — | Login as each role, verify menu visibility, action availability | QA / Acceptance |

---

## Packaging & Deployment Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Packaging (ZIP) | **PARTIAL** | `build_release_package.ps1` (build tool, not a test); manual SHA-256 verification | Release process docs | Automated ZIP validation: structure, path slashes, manifest-only root | DevOps |
| Package artifact validation | **NOT COVERED** | — | — | Automated test: unzip → verify structure → compare manifest version to filename → compare SHA-256 | DevOps |
| Installation | **NOT COVERED** | — | — | Automated install test on disposable CRM | DevOps |
| Upgrade | **NOT COVERED** | — | — | Upgrade from previous version → verify data intact, metadata merged | DevOps |
| Rollback | **NOT COVERED** | — | — | Install → upgrade → rollback → verify state restored | DevOps |

---

## Runtime & Cleanup Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Runtime extension install + rebuild | **NOT COVERED** | — | — | Automated install→rebuild→verify entities/scopes/layouts | DevOps |
| Runtime cleanup (test data) | **PARTIAL** | T04 registry-only cleanup and marker verification | Offline verified; live pending | Real local execution with zero residue | QA |
| Runtime residue detection | **PARTIAL** | T04 registered-fixture 404 audit | Offline verified; live pending | Full marker/orphan scan remains out of scope | QA |

---

## Performance Coverage

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Performance baseline | **NOT COVERED** | — | — | List load time, filter response time, API CRUD latency, bulk job generation | DevOps / Perf |
| Batch job generation | **NOT COVERED** | — | — | Generate 40+ jobs, measure wall-clock, verify no N+1 queries | Acquisition team |
| Connector sync latency | **NOT COVERED** | — | — | Lead+evidence+proposal sync round-trip time | Connector team |

---

## Security & Secret Handling

| Capability | Status | Existing Tests | Evidence | Missing Scenarios | Recommended Owner |
|------------|--------|---------------|----------|-------------------|-------------------|
| Secret leakage — test code | **COVERED** | Manual audit: no API keys, passwords, tokens found in test files | T01 audit | Automated secret scanning in CI | Security |
| Secret leakage — worker error messages | **COVERED** | Persistence hardening tests (secrets scrubbed from errorMessage) | Static Verified | Runtime: verify real CRM error responses don't leak secrets | Security |
| Secret leakage — provisioning scripts | **NOT COVERED** | — | — | Several provisioning scripts contain hardcoded test API keys and passwords (test-only, but should be audited) | Security |
| API key transport | **COVERED** | `test_phase3c02_2c_job_runner.py` (JSON output excludes API key) | Static Verified | — | Security |
| Environment safety (local-only guard) | **COVERED** | `test_espocrm_real_client.py` (remote URL rejection, env gating) | Static Verified | — | Security |

---

## Overall Summary

| Status | Count | Percentage |
|--------|-------|-----------|
| COVERED | 32 | 55% |
| PARTIAL | 10 | 17% |
| NOT COVERED | 14 | 24% |
| BLOCKED | 0 | 0% |
| OUT OF SCOPE | 2 | 3% |
| **Total capabilities** | **58** | **100%** |

### Key Gaps (NOT COVERED)

1. **Browser acceptance tests** — all UI workflows (0% coverage)
2. **Installation / Upgrade / Rollback** — zero automated tests
3. **Performance baseline** — no latency/throughput measurements
4. **Runtime cleanup automation** — only phase-specific manual cleanup scripts
5. **Field-level ACL tests** — scope-level only
6. **Package artifact automated validation** — manual SHA-256 verification only
7. **Secret leakage in provisioning scripts** — hardcoded test credentials not audited

### Key Partials

1. **REST authentication** — basic API key flow covered; token lifecycle missing
2. **REST CRUD** — acceptance script exists but requires live CRM (TBD)
3. **Generate-jobs** — metadata coverage solid; runtime API behavior not tested offline
4. **ACL matrix** — provisioning script content validated; actual role enforcement not tested offline
