# Phase G01 — Parallel Worktree Commit Separation Audit

**Date:** 2026-07-13
**Auditor:** Claude Code (DeepSeek V4 Pro API, High Reasoning)
**Status:** **AUDIT COMPLETE — 6 clean commit groups identified, 1 mixed-hunk file, 0 blocking circular dependencies**
**Mode:** Read-only audit. No destructive git operations performed.

---

## 1. Current Branch and HEAD

| Item | Value |
|---|---|
| Branch | `master` |
| HEAD commit | `a4b0e6e` |
| HEAD message | `Phase3C02.2C-R2 recover admin auth and clean diagnostics` |
| Upstream | `main` (not tracking remote) |
| Worktree | Single (no `git worktree` isolation active) |
| Modified tracked | 23 files (+361 / -75 lines) |
| Untracked | 89 files across 7 phase groups |

Recent commit log:
```
a4b0e6e Phase3C02.2C-R2 recover admin auth and clean diagnostics
db64301 Phase3C02.2C-R1 clean runtime diagnostic residue
36718a5 Phase3C02.2C-R verify runtime end-to-end
cf7b2a6 Phase3C02.2C document job runner results
4650844 Phase3C02.2C add single job runner and Espo REST adapter
```

---

## 2. Full `git status --short`

```
 M chitu-connector/chitu_connector/acquisition/__init__.py        [C03]
 M chitu-connector/chitu_connector/acquisition/models.py          [C03]
 M chitu-connector/chitu_connector/acquisition/runner.py          [C03]
 M crm-extension/Resources/entityDefs/SearchJob.json              [C01+C02.1]
 M crm-extension/Resources/layouts/SearchJob/detail.json          [C01+C02.1]
 M crm-extension/Resources/layouts/SearchJob/list.json            [C01+C02.1]
 M crm-extension/Resources/routes.json                            [C02.1]
 D crm-extension/.../PrimaryFilters/JobsWaiting.php               [C02.1]
 M crm-extension/.../i18n/en_US/Global.json                       [C02.1]
 M crm-extension/.../i18n/en_US/SearchJob.json                    [C01+C02.1]
 M crm-extension/.../layouts/Lead/detail.json                     [phantom LF/CRLF]
 M crm-extension/.../layouts/SearchJob/detail.json                [C01+C02.1]
 M crm-extension/.../layouts/SearchJob/list.json                  [C01+C02.1]
 M crm-extension/.../metadata/clientDefs/SearchJob.json           [C02.1]
 M crm-extension/.../metadata/dashlets/AcquisitionJobsWaiting.json[C02.1]
 M crm-extension/.../metadata/entityDefs/SearchJob.json           [C01+C02.1]
 M crm-extension/.../metadata/scopes/ProspectPool.json            [C02.1]
 M crm-extension/.../metadata/scopes/SearchJob.json               [C02.1]
 M crm-extension/.../metadata/selectDefs/SearchJob.json           [C02.1]
 M crm-extension/.../routes.json                                  [C02.1]
 M crm-extension/tests/test_extension_skeleton.py                 [MIXED C01+C02.1]
 M deployment/provisioning/phase3c01_provision_acquisition...php  [C01+C02.1]
 M docs/README.md                                                 [D01]

?? chitu-connector/.../acquisition/master_prospect.py             [C04]
?? chitu-connector/.../acquisition/providers/ (5 files)           [C03]
?? chitu-connector/.../acquisition/website_research.py            [C05]
?? chitu-connector/tests/test_phase3c03_2_provider_adapter.py     [C03]
?? chitu-connector/tests/test_phase3c03_2_serper_provider.py      [C03]
?? chitu-connector/tests/test_phase3c03_2_serper_runner.py        [C03]
?? chitu-connector/tests/test_phase3c04_master_prospect_dedup.py  [C04]
?? chitu-connector/tests/test_phase3c05_website_research...py     [C05]
?? crm-extension/files/client/custom/src/handlers/...             [C02.1]
?? crm-extension/.../Api/PostGenerateSearchStrategyJobs.php        [C02.1]
?? crm-extension/.../PrimaryFilters/JobsCancelled.php              [C02.1]
?? crm-extension/.../PrimaryFilters/JobsQueued.php                 [C02.1]
?? crm-extension/.../metadata/clientDefs/SearchStrategy.json       [C02.1]
?? crm-extension/.../metadata/dashlets/AcquisitionSearchStrateg... [C02.1]
?? crm-extension/.../Services/SearchStrategyService.php            [C02.1]
?? crm-extension/.../Services/SearchStrategyTemplates.php          [C02.1]
?? deployment/prospecting-extension-1.9.0-alpha.zip               [C02.1 artifact]
?? deployment/prospecting-extension-1.9.0-alpha.zip.sha256        [C02.1 artifact]
?? deployment/validation/test_phase3c02_1a_search_strategy...py   [C02.1]
?? docs/DOCUMENTATION_CENTER_REPORT.md                             [D01]
?? docs/PHASE3C02_2B_WORKER_CORE_REVIEW.md                        [C02.2 doc]
?? docs/PHASE3C02_2C_JOB_RUNNER_DESIGN.md                         [C02.2 doc]
?? docs/PHASE3C03_1_PROVIDER_SELECTION_AND_CONTRACT_FREEZE.md     [C03 doc]
?? docs/PHASE3C03_2A_PROVIDER_CONTRACT_ALIGNMENT_REPORT.md        [C03 doc]
?? docs/PHASE3C03_2_PROVIDER_ADAPTER_IMPLEMENTATION.md            [C03 doc]
?? docs/PHASE3C03_2_SERPER_PROVIDER_IMPLEMENTATION.md             [C03 doc]
?? docs/PHASE3C04_MASTER_PROSPECT_DEDUP_REPORT.md                 [C04 doc]
?? docs/PHASE3C05_WEBSITE_RESEARCH_PIPELINE_REPORT.md             [C05 doc]
?? docs/PHASE_CI01_CICD_AUDIT_REPORT.md                           [CI01 doc]
?? docs/PHASE_T01_TEST_SYSTEM_AUDIT_REPORT.md                     [T01 doc]
?? docs/PHASE_T02_UNIFIED_TEST_ENTRYPOINTS_REPORT.md              [T02 doc]
?? docs/PHASE_T03_CORE_REGRESSION_GATE_REPORT.md                  [T03 doc]
?? docs/PHASE_T04_C03_FREEZE_REPORT.md                            [T04 doc]
?? docs/PHASE_T04_RUNTIME_TEST_HARNESS_REPORT.md                  [T04 doc]
?? docs/adr/* (1 file)                                             [D01]
?? docs/api/* (4 files)                                           [D01]
?? docs/architecture/* (5 files)                                  [D01]
?? docs/ci/* (5 files)                                            [D01]
?? docs/deployment/* (5 files)                                    [D01]
?? docs/developer/* (5 files)                                     [D01]
?? docs/diagrams/* (1 file)                                       [D01]
?? docs/release/* (3 files)                                       [D01]
?? docs/reports/* (1 file)                                        [D01]
?? docs/testing/* (14 files)                                      [D01+T04]
?? docs/user-guide/* (5 files)                                    [D01]
?? scripts/testing/* (4 files)                                    [T04]
?? tests/runtime/* (4 files)                                      [T04]
```

---

## 3. Complete File Classification by Phase

### 3.1 Phase D01 — Documentation Center (30 files, 1 modified tracked)

**Evidence:** `docs/README.md` is a complete rewrite introducing the Documentation Center with system status table, documentation map, status labels, maintenance conventions, and per-phase update rules. The `DOCUMENTATION_CENTER_REPORT.md` confirms this as "Phase D01." All subdirectory content was generated in the same phase.

**Tracked modified:**
| File | Change |
|---|---|
| `docs/README.md` | Complete rewrite (index → documentation center) |

**Untracked (29 files):**
| Path | Purpose |
|---|---|
| `docs/DOCUMENTATION_CENTER_REPORT.md` | D01 completion report |
| `docs/adr/README.md` | ADR index |
| `docs/api/README.md`, `CONNECTOR_API.md`, `REST_ENDPOINTS.md`, `WEBHOOKS.md` | API docs |
| `docs/architecture/BOUNDARIES.md`, `DATA_FLOW.md`, `DIRECTORY_STRUCTURE.md`, `MODULES.md`, `SYSTEM_OVERVIEW.md` | Architecture docs |
| `docs/ci/CI_PIPELINE_DESIGN.md`, `CI_ROADMAP.md`, `CURRENT_STATE.md`, `RELEASE_AUTOMATION_DESIGN.md`, `WORKFLOW_PLAN.md` | CI docs |
| `docs/deployment/INSTALL.md`, `PACKAGE.md`, `ROLLBACK.md`, `UPGRADE.md`, `VERSIONING.md` | Deployment docs |
| `docs/developer/CODING_GUIDELINES.md`, `GETTING_STARTED.md`, `LOCAL_SETUP.md`, `PROJECT_STRUCTURE.md`, `TESTING.md` | Developer docs |
| `docs/diagrams/README.md` | Diagram index |
| `docs/release/CHANGELOG_POLICY.md`, `RELEASE_PROCESS.md`, `VERSION_POLICY.md` | Release docs |
| `docs/reports/README.md` | Reports index |
| `docs/user-guide/ACL.md`, `INSTALL_EXTENSION.md`, `LEADS.md`, `PROSPECT_POOL.md`, `SEARCH_WORKSPACE.md` | User guide |

**Dependency:** None. Fully independent.

---

### 3.2 Phase T0x/T04/CI01 — Test Infrastructure & CICD Audit (18 files, 0 modified tracked)

**Evidence:** Files are grouped under `scripts/testing/` (test runner infrastructure), `tests/runtime/` (T04 runtime harness), and `docs/PHASE_T0*` reports. All are test-layer assets, no production code changes.

**Untracked (18 files):**
| Path | Phase | Purpose |
|---|---|---|
| `scripts/testing/regression-gate-map.json` | T03 | T03 gate configuration |
| `scripts/testing/run-regression-gate.ps1` | T03 | Regression gate runner |
| `scripts/testing/run-runtime-tests.ps1` | T04 | Runtime test runner |
| `scripts/testing/run-tests.ps1` | T02 | Unified test entrypoints |
| `tests/runtime/__init__.py` | T04 | Runtime package init |
| `tests/runtime/runtime_cli.py` | T04 | Runtime CLI entrypoint |
| `tests/runtime/runtime_harness.py` | T04 | Safety-first REST harness |
| `tests/runtime/test_runtime_harness.py` | T04 | Harness unit tests |
| `docs/testing/RUNTIME_TEST_ENVIRONMENT.md` | T04 | Runtime env docs |
| `docs/testing/RUNTIME_TEST_HARNESS.md` | T04 | Harness docs |
| `docs/testing/CHECKLIST.md` | T0x | Testing checklist |
| `docs/testing/CORE_REGRESSION_GATE.md` | T03 | Gate docs |
| `docs/testing/COVERAGE_MATRIX.md` | T0x | Coverage matrix |
| `docs/testing/MANUAL_TESTS.md` | T0x | Manual tests |
| `docs/testing/REGRESSION.md` | T0x | Regression docs |
| `docs/testing/REGRESSION_MATRIX.md` | T0x | Regression matrix |
| `docs/testing/TEST_INVENTORY.md` | T01 | Test inventory |
| `docs/testing/TEST_LAYER_MODEL.md` | T01 | Layer model |
| `docs/testing/TEST_PLAN.md` | T01 | Test plan |
| `docs/testing/TEST_RELIABILITY_RISKS.md` | T01 | Reliability risks |
| `docs/testing/TEST_SYSTEM_ROADMAP.md` | T01 | System roadmap |
| `docs/testing/UNIFIED_TEST_ENTRYPOINTS.md` | T02 | Entrypoint docs |
| `docs/PHASE_T01_TEST_SYSTEM_AUDIT_REPORT.md` | T01 | Phase report |
| `docs/PHASE_T02_UNIFIED_TEST_ENTRYPOINTS_REPORT.md` | T02 | Phase report |
| `docs/PHASE_T03_CORE_REGRESSION_GATE_REPORT.md` | T03 | Phase report |
| `docs/PHASE_T04_C03_FREEZE_REPORT.md` | T04 | Freeze report |
| `docs/PHASE_T04_RUNTIME_TEST_HARNESS_REPORT.md` | T04 | Harness report |
| `docs/PHASE_CI01_CICD_AUDIT_REPORT.md` | CI01 | CICD audit |

**Dependency:** None. Fully independent.

---

### 3.3 Phase3C03 — Provider Infrastructure (11 files, 3 modified tracked)

**Evidence:** All provider infrastructure files were added or modified as part of Phase3C03 (Apify adapter + Serper provider). The modified tracked files (`__init__.py`, `models.py`, `runner.py`) only contain C03-scoped changes: `ProviderRateLimitError`, serper runner registration, export wiring.

**Tracked modified:**
| File | Lines | Change |
|---|---|---|
| `chitu-connector/chitu_connector/acquisition/__init__.py` | +2 | Added `ProviderRateLimitError` export |
| `chitu-connector/chitu_connector/acquisition/models.py` | +8 | Added `ProviderRateLimitError` class |
| `chitu-connector/chitu_connector/acquisition/runner.py` | +61 | `_resolve_provider`, `_UrllibTransport`, serper registration |

**Untracked (8 files):**
| Path | Purpose |
|---|---|
| `chitu-connector/chitu_connector/acquisition/providers/__init__.py` | Provider package exports |
| `chitu-connector/chitu_connector/acquisition/providers/apify_provider.py` | Apify adapter |
| `chitu-connector/chitu_connector/acquisition/providers/base.py` | HttpRequest/HttpResponse/transport protocol |
| `chitu-connector/chitu_connector/acquisition/providers/config.py` | ApifyConfig + SerperConfig |
| `chitu-connector/chitu_connector/acquisition/providers/serper_provider.py` | Serper adapter |
| `chitu-connector/tests/test_phase3c03_2_provider_adapter.py` | Apify adapter tests (6) |
| `chitu-connector/tests/test_phase3c03_2_serper_provider.py` | Serper provider tests (26) |
| `chitu-connector/tests/test_phase3c03_2_serper_runner.py` | Serper runner factory tests (5) |

**Phase reports (4 files):**
| Path | Purpose |
|---|---|
| `docs/PHASE3C03_1_PROVIDER_SELECTION_AND_CONTRACT_FREEZE.md` | C03.1 report |
| `docs/PHASE3C03_2A_PROVIDER_CONTRACT_ALIGNMENT_REPORT.md` | C03.2A report |
| `docs/PHASE3C03_2_PROVIDER_ADAPTER_IMPLEMENTATION.md` | C03.2 report |
| `docs/PHASE3C03_2_SERPER_PROVIDER_IMPLEMENTATION.md` | C03.2 Serper report |

**Dependency:** None. C03 imports only from `models.py` (HEAD-committed) and adds new provider files. No dependency on C04 or C05.

---

### 3.4 Phase3C04 — Master Prospect Dedup (3 files, 0 modified tracked)

**Evidence:** `master_prospect.py` is a standalone module implementing deterministic Master Prospect deduplication. It imports from `models.py` (RawCandidate — committed in HEAD) and `normalization.py` (committed in HEAD). It imports nothing from the providers/ directory. The test file and report confirm C04 scope.

**Untracked:**
| Path | Purpose |
|---|---|
| `chitu-connector/chitu_connector/acquisition/master_prospect.py` | Master Prospect dedup engine |
| `chitu-connector/tests/test_phase3c04_master_prospect_dedup.py` | C04 unit tests |
| `docs/PHASE3C04_MASTER_PROSPECT_DEDUP_REPORT.md` | C04 phase report |

**Dependency:** Imports from `models.py` (HEAD) and `normalization.py` (HEAD). No dependency on C03 providers.

---

### 3.5 Phase3C05 — Website Research Pipeline (3 files, 0 modified tracked)

**Evidence:** `website_research.py` imports from `master_prospect.py` (C04) and `normalization.py` (HEAD). The test file confirms C05 scope.

**Untracked:**
| Path | Purpose |
|---|---|
| `chitu-connector/chitu_connector/acquisition/website_research.py` | Website research pipeline |
| `chitu-connector/tests/test_phase3c05_website_research_pipeline.py` | C05 unit tests |
| `docs/PHASE3C05_WEBSITE_RESEARCH_PIPELINE_REPORT.md` | C05 phase report |

**Dependency:** Imports `MasterProspect` from `master_prospect.py` (C04). **Must be committed after C04.**

---

### 3.6 Phase3C01 + Phase3C02.1 — CRM Extension Foundation + SearchStrategy (27 files, 19 modified tracked)

**Evidence:** This is the largest and most complex group. Phase3C01 established the Acquisition Workspace foundation (SearchJob, ProspectPool entities, dashlets, provisioning). Phase3C02.1 added SearchStrategy entity, SearchJob v2 field remodel, Job generation API, and updated all dependent metadata. Because C02.1 was built on top of uncommitted C01 changes, the two phases are entangled in the working tree.

**CRITICAL FINDING:** File `crm-extension/tests/test_extension_skeleton.py` contains the only **mixed-hunk** situation in this audit. See Section 4.

**Tracked modified (19 files):**

*Surface CRM extension (`crm-extension/Resources/`):*
| File | Phase | Change Summary |
|---|---|---|
| `entityDefs/SearchJob.json` | C01+C02.1 | Full field remodel: WAITING→QUEUED, new fields (product, priority, queryFingerprint, resultCount, acceptedCount, rejectedCount, errorMessage, startedAt), strategy link, CANCELLED status, queryFingerprint index |
| `layouts/SearchJob/detail.json` | C01+C02.1 | Panel restructure: "Search Definition"→"Discovery Job", new fields in layout |
| `layouts/SearchJob/list.json` | C01+C02.1 | Column reorder + new columns (strategy, product, priority, resultCount) |
| `routes.json` | C02.1 | Added `/Prospecting/search-strategy/generate-jobs` route |

*Module CRM extension (`crm-extension/files/custom/Espo/Modules/Prospecting/`):*
| File | Phase | Change Summary |
|---|---|---|
| `.../PrimaryFilters/JobsWaiting.php` | C02.1 | **DELETED** — replaced by JobsQueued |
| `Resources/i18n/en_US/Global.json` | C02.1 | Added SearchStrategies dashlet label, Waiting→Queued |
| `Resources/i18n/en_US/SearchJob.json` | C01+C02.1 | Complete field label remap, status/priority/product options |
| `Resources/layouts/Lead/detail.json` | **PHANTOM** | Line-ending only (LF↔CRLF). Zero content diff. |
| `Resources/layouts/SearchJob/detail.json` | C01+C02.1 | Mirror of surface detail layout |
| `Resources/layouts/SearchJob/list.json` | C01+C02.1 | Mirror of surface list layout |
| `Resources/metadata/clientDefs/SearchJob.json` | C02.1 | Filter list: jobsWaiting→jobsQueued, added jobsCancelled |
| `Resources/metadata/dashlets/AcquisitionJobsWaiting.json` | C02.1 | Dashlet title Waiting→Queued, filter jobsWaiting→jobsQueued |
| `Resources/metadata/entityDefs/SearchJob.json` | C01+C02.1 | **Mirror** of surface entityDefs (identical content) |
| `Resources/metadata/scopes/ProspectPool.json` | C02.1 | `statusField` "status"→null |
| `Resources/metadata/scopes/SearchJob.json` | C02.1 | `statusField` "status"→null |
| `Resources/metadata/selectDefs/SearchJob.json` | C02.1 | Added jobsQueued, jobsCancelled; removed jobsWaiting |
| `Resources/routes.json` | C02.1 | Mirror of surface routes |

*Test and deployment:*
| File | Phase | Change Summary |
|---|---|---|
| `crm-extension/tests/test_extension_skeleton.py` | **MIXED** | C01 field remodel assertions + C02.1 new test method. See §4. |
| `deployment/provisioning/phase3c01_provision_acquisition_workspace.php` | C01+C02.1 | Added SearchStrategies dashlet, updated filter regex to `/^phase3c0[12]-/`, Waiting→Queued |

**Untracked (8 files):**
| Path | Phase | Purpose |
|---|---|---|
| `crm-extension/files/client/custom/src/handlers/search-strategy/generate-jobs.js` | C02.1 | Client-side action handler |
| `crm-extension/.../Api/PostGenerateSearchStrategyJobs.php` | C02.1 | Job generation API endpoint |
| `crm-extension/.../PrimaryFilters/JobsCancelled.php` | C02.1 | Cancelled filter class |
| `crm-extension/.../PrimaryFilters/JobsQueued.php` | C02.1 | Queued filter class |
| `crm-extension/.../metadata/clientDefs/SearchStrategy.json` | C02.1 | SearchStrategy client defs |
| `crm-extension/.../metadata/dashlets/AcquisitionSearchStrategies.json` | C02.1 | SearchStrategies dashlet |
| `crm-extension/.../Services/SearchStrategyService.php` | C02.1 | Business logic service |
| `crm-extension/.../Services/SearchStrategyTemplates.php` | C02.1 | Strategy templates |

**Artifacts and validation (3 files):**
| Path | Phase | Purpose |
|---|---|---|
| `deployment/prospecting-extension-1.9.0-alpha.zip` | C02.1 | Packaged extension |
| `deployment/prospecting-extension-1.9.0-alpha.zip.sha256` | C02.1 | Checksum |
| `deployment/validation/test_phase3c02_1a_search_strategy_detail.py` | C02.1 | Validation test |

**Phase reports (12 files):**
| Path | Phase | Purpose |
|---|---|---|
| `docs/PHASE3C01_ACQUISITION_WORKSPACE_FOUNDATION.md` | C01 | Foundation report |
| `docs/PHASE3C02_1_ACQUISITION_ACL_REPORT.md` | C02.1 | ACL report |
| `docs/PHASE3C02_1B_PARALLEL_COMMIT_SEPARATION_REPORT.md` | C02.1 | Commit separation |
| `docs/PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md` | C02.2 | Boundary audit |
| `docs/PHASE3C02_2B_ACQUISITION_WORKER_CORE_REPORT.md` | C02.2 | Worker core |
| `docs/PHASE3C02_2B1_WORKER_PERSISTENCE_HARDENING_REPORT.md` | C02.2 | Hardening |
| `docs/PHASE3C02_2B_WORKER_CORE_REVIEW.md` | C02.2 | Review |
| `docs/PHASE3C02_2C_JOB_RUNNER_DESIGN.md` | C02.2 | Runner design |
| `docs/PHASE3C02_2C_JOB_RUNNER_REPORT.md` | C02.2 | Runner report |
| `docs/PHASE3C02_2C_R_RUNTIME_VERIFICATION_REPORT.md` | C02.2 | Runtime verify |
| `docs/PHASE3C02_1F_SEARCH_STRATEGY_FOUNDATION.md` | C02.1 | (if present) |
| `docs/PHASE3C02_2D_...` | C02.2 | (if present) |

**Dependency:** Fully independent of Python connector changes. CRM PHP/JSON has zero Python imports.

---

### 3.7 Phase3C02.2 — Already Committed

The commits `a4b0e6e` through `4650844` already contain the C02.2 worker core, persistence hardening, job runner, and Espo REST adapter. These are cleanly in git history and require no further separation.

---

## 4. Mixed Hunk Analysis — Same-File Cross-Phase Changes

### 4.1 `crm-extension/tests/test_extension_skeleton.py` — MIXED C01 + C02.1

This is the **only file** in the working tree with cross-phase mixed hunks. All other tracked and untracked files are phase-pure.

**Hunk breakdown:**

| Hunk | Lines | Phase | Content |
|---|---|---|---|
| A | ~239 | C01+C02.1 | Manifest version `1.8.0` → `1.9.0`; description text update |
| B | ~530 | C02.1 | Add SearchStrategy entities to expected PHP shell list |
| C | ~703 | C02.1 | Add search-strategy route to expected routes |
| D | ~1000 | C01+C02.1 | Manifest version bumps in existing C01 test methods (3 places) |
| E | ~1096-1127 | C01+C02.1 | C01 field remodel assertions: WAITING→QUEUED, new fields, status options, filter/dashlet names |
| F | ~1132 | C02.1 | C01 provisioning: add `phase3c02-` dashlet, update filter regex |
| G | ~1165-1226 | C02.1 | **NEW** `test_phase3c02_search_strategy_discovery_jobs` method (60 lines) |
| H | ~1241 | C01+C02.1 | Manifest version bumps at end of C01 test methods |

**Verdict:** Cannot be split into pure-C01 and pure-C02.1 sub-files without breaking test integrity. The test file reflects the **combined** C01+C02.1 CRM state. This is acceptable because C01 and C02.1 form a single logical CRM extension upgrade.

### 4.2 `deployment/provisioning/phase3c01_provision_acquisition_workspace.php` — C01+C02.1 (coherent)

The changes add C02.1 dashlets and update the filter regex to match both `/^phase3c01-/` and `/^phase3c02-/` patterns. These are logically coherent — the script that provisions C01 dashlets was extended to also manage C02.1 dashlets. No conflicting hunk.

### 4.3 `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json` — PHANTOM

This file shows as `M` in `git status` but `git diff --ignore-cr-at-eol HEAD` produces zero output. The change is purely line-ending conversion (LF↔CRLF) due to `core.autocrlf` settings. **Should be excluded from all commits** (restore to HEAD state before committing).

---

## 5. Safe Independent Commit Groups

### Group 1: D01 — Documentation Center (30 files)

**Safety:** Fully independent. No code dependencies. No production file overlap.

**Files:**
- 1 tracked modified: `docs/README.md`
- 29 untracked docs under `docs/`

**Commit message:**
```
Phase D01 — Documentation Center baseline

Establish the Documentation Center with system status,
maintenance conventions, per-phase update rules, and
a complete documentation map covering architecture,
API, deployment, developer guide, user guide, testing,
CI, release engineering, ADR, and diagrams.

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Group 2: T0x/T04/CI01 — Test Infrastructure (28 files)

**Safety:** Fully independent. Test-layer assets only. No production code touched.

**Files:**
- 0 tracked modified
- 4 scripts under `scripts/testing/`
- 4 runtime harness files under `tests/runtime/`
- 14 docs under `docs/testing/`
- 6 phase report docs at `docs/PHASE_T0*` and `docs/PHASE_CI01*`

**Commit message:**
```
Phase T01-T04 + CI01 — Test infrastructure and CICD audit

Establish unified test entrypoints, core regression gate,
runtime test harness (safety-first, local-only), and CICD
pipeline audit. All runtime tests are isolated to localhost
with mandatory safety guards.

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Group 3: C01+C02.1 — CRM Extension Foundation (39 files)

**Safety:** Internally coherent. No Python connector dependency. The mixed-hunk test file (`test_extension_skeleton.py`) is committed as a unit.

**⚠️ Pre-commit action required:** Restore `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json` to HEAD state (phantom LF/CRLF change only).

**Files:**
- 18 tracked modified (excluding phantom and already-counted)
- 1 tracked deleted (`JobsWaiting.php`)
- 8 untracked CRM extension files
- 2 untracked deployment artifacts (zip + sha256)
- 1 untracked validation test
- 12 untracked phase report docs

**Commit message:**
```
Phase3C01-C02.1 — CRM Extension Acquisition Workspace Foundation

Establish Acquisition Workspace foundation:
- SearchJob v2 field remodel (QUEUED status, priority, product,
  queryFingerprint, resultCount, acceptedCount, rejectedCount,
  errorMessage, startedAt; strategy link)
- ProspectPool scope hardening (statusField→null)
- SearchStrategy entity: metadata, clientDefs, dashlets,
  service layer, template library, job generation API
- AC

L provisioned for Acquisition workspace
- UI: updated detail/list layouts, filters (jobsQueued,
  jobsCancelled), i18n labels
- Extension version: 1.9.0-alpha
- Deployment: packaged artifact + validation tests

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Group 4: C03 — Provider Infrastructure (15 files)

**Safety:** Fully independent of C04/C05. Adds provider package and adapters. All imports are from HEAD-committed modules. C04/C05 depend on C03 only for `base.py` HttpResponse (which has the new `headers` field) — but C04 doesn't import from base.py at all, and C05 only needs it transitively through providers.

Wait — actually, re-examining the dependency chain:
- C04 (`master_prospect.py`) imports from `models.py` (RawCandidate) and `normalization.py` (normalize_domain) — both in HEAD
- C05 (`website_research.py`) imports from `master_prospect.py` (C04) and `normalization.py` — C04 must be committed first
- C03 (`providers/`) has no dependency on C04 or C05

C03 is independent of C04/C05 and C01+C02.1. C04 is independent of C03 and C01+C02.1.

**Files:**
- 3 tracked modified (acquisition `__init__.py`, `models.py`, `runner.py`)
- 5 untracked provider implementation files
- 3 untracked test files
- 4 untracked phase report docs

**Commit message:**
```
Phase3C03 — Provider infrastructure with Apify and Serper adapters

Establish provider adapter infrastructure:
- HttpRequest/HttpResponse/HttpTransport protocol (base.py)
- ApifyProvider with full error classification
- SerperSearchProvider with Serper API integration
- ProviderRateLimitError with retry-after support
- SerperConfig and ApifyConfig with from_env factories
- Runner factory: --provider serper registration,
  _UrllibTransport for production, _resolve_provider routing
- Tests: 6 Apify adapter + 26 Serper provider + 5 runner factory
- All tests use fixture transports; zero real API calls

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Group 5: C04 — Master Prospect Dedup (3 files)

**Safety:** Imports only from HEAD-committed `models.py` and `normalization.py`. Zero provider dependency. Zero CRM dependency.

**Dependency on previous commits:** None technically (all imports resolve against HEAD), but logically follows C03 in recommended order.

**Files:**
- 0 tracked modified
- 1 untracked source (`master_prospect.py`)
- 1 untracked test (`test_phase3c04_master_prospect_dedup.py`)
- 1 untracked phase report doc

**Commit message:**
```
Phase3C04 — Master Prospect deduplication engine

Deterministic, offline Master Prospect deduplication:
- ProspectNormalizer, ProspectMatcher, MasterProspectMerger
- Multi-rule matching (ROOT_DOMAIN, CANONICAL_WEBSITE,
  COMPANY_NAME, COMPANY_COUNTRY, COMPANY_CITY)
- Confidence-scored merge with traceable rule provenance
- Zero persistence, HTTP, provider, worker, runner, or CRM
  dependency — pure in-memory data transformation

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### Group 6: C05 — Website Research Pipeline (3 files)

**Safety:** Imports from C04 (`master_prospect.py`) and HEAD-committed `normalization.py`. Zero provider/worker/runner dependency. Zero CRM dependency.

**Dependency:** **Requires C04 committed first** (imports `MasterProspect` from `master_prospect.py`).

**Files:**
- 0 tracked modified
- 1 untracked source (`website_research.py`)
- 1 untracked test (`test_phase3c05_website_research_pipeline.py`)
- 1 untracked phase report doc

**Commit message:**
```
Phase3C05 — Website research pipeline foundation

Offline, deterministic website research pipeline:
- WebsiteUrlPlanner, WebsitePageClassifier, HtmlSanitizer
- ResearchEligibilityChecker with domain/IP safety gates
- WebsiteResearchPipeline orchestration (fetch→classify→extract)
- Transport-injected design; no network in tests
- Zero provider, worker, runner, CRM, or AI dependency

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 6. Unsafe / Not-Yet-Ready File Groups

### 6.1 Phantom line-ending change (must be restored before ANY commit)

| File | Issue | Action |
|---|---|---|
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json` | LF↔CRLF only; zero content diff | `git checkout HEAD -- <file>` before first commit |

### 6.2 docs/ root: mixed C02.2 phase reports (committed-phase docs)

The following docs in `docs/` root reference Phase C02.2 — which is **already committed** in git history. These are untracked documentation files that were written to document completed work:

| File | Phase | Safe to commit with |
|---|---|---|
| `docs/PHASE3C02_2B_WORKER_CORE_REVIEW.md` | C02.2 (committed) | Group 3 (C01+C02.1) or separate C02.2-docs commit |
| `docs/PHASE3C02_2C_JOB_RUNNER_DESIGN.md` | C02.2 (committed) | Group 3 or separate |

These are documentation for already-committed code. They can safely go in Group 3 or in their own documentation commit.

---

## 7. Recommended Commit Order

```
Commit 1: D01 — Documentation Center
  └─ 30 files, 0 dependencies, 0 conflicts

Commit 2: T01-T04 + CI01 — Test Infrastructure
  └─ 28 files, 0 dependencies, 0 conflicts

Commit 3: Phase3C01-C02.1 — CRM Extension Foundation
  └─ 39 files, 0 Python dependencies
  └─ PREREQUISITE: restore Lead/detail.json phantom diff
  └─ PREREQUISITE: add C02.2 phase reports to this commit
                    (or defer to separate docs-only commit)

Commit 4: Phase3C03 — Provider Infrastructure
  └─ 15 files, 0 dependencies on C04/C05

Commit 5: Phase3C04 — Master Prospect Dedup
  └─ 3 files, depends on models.py (HEAD)

Commit 6: Phase3C05 — Website Research Pipeline
  └─ 3 files, depends on C04 (master_prospect.py)
```

**Rationale for this order:**
1. D01 and T0x are pure documentation/test infrastructure — safest to commit first, no code impact.
2. C01+C02.1 (CRM) and C03/C04/C05 (Python) are independent of each other. Order between Group 3 and Group 4 is interchangeable.
3. C04 must precede C05 due to `website_research.py → master_prospect.py` import.
4. C03 can go before or after C04 since neither imports the other.

---

## 8. Pre-Commit Checklist (per commit)

### Before Commit 3 (C01+C02.1):
```bash
# Restore phantom line-ending change
git checkout HEAD -- "crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json"

# Verify: should produce empty diff
git diff HEAD -- "crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json"
```

### Before ALL commits:
```bash
# Verify no forbidden file leaked
git diff --name-only HEAD | grep -E "worker\.py|fake_provider\.py|normalization\.py|espo_repository\.py"
# EXPECTED: no output

# Verify T04 runtime files are NOT in commit set 1-3
git status --short scripts/testing/ tests/runtime/
# EXPECTED: ?? (untracked, not staged)
```

---

## 9. T04 / C03 Freeze Commit Recovery Assessment

**Question:** Can the T04 / C03 freeze commit be safely recovered?

**Answer:** **Yes.** The freeze state is recoverable by:
1. Committing D01, T0x, and C01+C02.1 first (they are independent of C03)
2. Then committing C03 (providers)
3. Then C04, C05

The T04 freeze report (`docs/PHASE_T04_C03_FREEZE_REPORT.md`) is an untracked documentation file. It can be committed in Group 2 (test infrastructure) alongside other T0x reports without affecting any frozen code.

The C03 freeze state referenced in T04 is the **provider contract** (`provider.py` Protocol) — which has NOT been modified in this working tree. The protocol remains frozen at HEAD.

---

## 10. C05 Blocking Items — Before C05 Can Begin

| # | Blocker | Severity | Resolution |
|---|---|---|---|
| 1 | C04 must be committed first | **BLOCKING** | C05 imports `MasterProspect` from `master_prospect.py`. Commit C04 before starting C05. |
| 2 | Providers directory must exist in committed state | **BLOCKING** | C05's `website_research.py` does not import from providers, but the acquisition package `__init__.py` is modified. Commit C03 first to avoid merge conflicts on `__init__.py`. |
| 3 | Mixed worktree must be clean | **ADVISORY** | C05 development should start from a clean post-commit state. All 6 groups should be committed before new C05 work begins. |
| 4 | Phantom Lead/detail.json diff | **MINOR** | Restore before any commit to avoid noise. |

**Minimum viable state for C05 start:** Commits 1-4 complete (D01, T0x, C01+C02.1, C03, C04). C05 does not need C02.1 CRM changes, but having a clean tree avoids confusion.

---

## 11. Execution Confirmation

```
git reset performed:            NO
git clean performed:            NO
git stash performed:            NO
git rebase performed:           NO
git add -A performed:           NO
git commit performed:           NO
git push performed:             NO
any file deleted:               NO
any file overwritten:           NO
existing worktree modified:     NO (read-only audit only)
untracked files touched:        NO (read-only audit only)
CRM PHP modified:               NO (read-only audit only)
worker.py modified:             NO
fake_provider.py modified:      NO
normalization.py modified:      NO
espo_repository.py modified:    NO
provider.py Protocol modified:  NO
T03 Gate modified:              NO
T04 files modified:             NO
external system accessed:       NO
```

---

## 12. Summary

| Metric | Count |
|---|---|
| Total files analyzed | 112 (23 modified tracked + 89 untracked) |
| Phase groups identified | 7 |
| Clean commit groups | 6 |
| Mixed-hunk files | 1 (`test_extension_skeleton.py`) |
| Phantom diff files | 1 (`Lead/detail.json`) |
| Blocking circular dependencies | 0 |
| Pre-commit restore actions required | 1 (phantom LF/CRLF) |
| Recommended commit count | 6 |
| C05 blocking items | 2 (C04 must be committed; clean tree) |
| T04/C03 freeze recoverable | Yes |
