# Phase3U02 — Native Prospecting UI Foundation Report

**Date:** 2026-07-13  
**Specification:** [PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md](PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md)  
**Verdict:** **PASS** — presentation metadata complete; U02.1 regression baseline aligned (38/38 skeleton + broader extension suite)

---

## 1. Executive Summary

Implemented **native entity-first** prospecting UI improvements per Phase3U01 Option A. All changes are **presentation metadata only**: layouts, filters, dashlets, scopes, clientDefs, selectDefs, i18n, and status label styling. No JavaScript was added. No backend services, routes, acquisition pipeline, or connector code was modified.

Users gain clearer navigation labels, SearchStrategy status filters, improved SearchJob and ProspectPool list columns, user-facing ProspectPool filters, and a **Prospecting Overview** dashlet definition for dashboard use.

---

## 2. Files Modified

### Created (11)

| File | Purpose |
|------|---------|
| `crm-extension/files/custom/.../Select/SearchStrategy/PrimaryFilters/StrategiesDraft.php` | Draft filter |
| `crm-extension/files/custom/.../Select/SearchStrategy/PrimaryFilters/StrategiesReady.php` | Ready filter |
| `crm-extension/files/custom/.../Select/SearchStrategy/PrimaryFilters/StrategiesActive.php` | Active filter (GENERATED + RUNNING) |
| `crm-extension/files/custom/.../Select/SearchStrategy/PrimaryFilters/StrategiesCompleted.php` | Completed filter |
| `crm-extension/files/custom/.../Select/ProspectPool/PrimaryFilters/ProspectsNew.php` | New prospects filter |
| `crm-extension/files/custom/.../Select/ProspectPool/PrimaryFilters/ProspectsAccepted.php` | Accepted filter |
| `crm-extension/files/custom/.../Select/ProspectPool/PrimaryFilters/ProspectsRejected.php` | Rejected filter |
| `crm-extension/files/custom/.../Select/ProspectPool/PrimaryFilters/ProspectsDuplicate.php` | Duplicate proxy filter |
| `crm-extension/files/custom/.../Select/ProspectPool/PrimaryFilters/ProspectsReadyForResearch.php` | Ready for Research filter |
| `crm-extension/files/custom/.../metadata/selectDefs/SearchStrategy.json` | SearchStrategy filter map |
| `crm-extension/files/custom/.../metadata/dashlets/AcquisitionOverview.json` | Prospecting Overview dashlet |

### Modified (22 presentation files)

| Area | Files |
|------|-------|
| Layouts (surface + module) | `SearchJob/list.json`, `SearchJob/detail.json`, `ProspectPool/list.json`, `ProspectPool/detail.json` |
| entityDefs presentation | `SearchStrategy.json`, `SearchJob.json` (status `style` only; surface + module) |
| scopes | `SearchStrategy.json`, `SearchJob.json` (`statusField`) |
| clientDefs | `SearchStrategy.json`, `SearchJob.json`, `ProspectPool.json` |
| selectDefs | `ProspectPool.json` |
| i18n | `Global.json`, `SearchStrategy.json`, `SearchJob.json`, `ProspectPool.json` |

---

## 3. Navigation Changes

- Added `scopeNames` / `scopeNamesPlural` in `Global.json`:
  - Search Strategies, Discovery Jobs, Lead Pool, AI Research Evidence
- Renamed user-facing labels (tabs use EspoCRM scope name translations)
- ProspectPool icon: `fas fa-address-book` (was `fas fa-layer-group`)
- **Deferred:** Dashboard tab rename to "Prospecting Home" in live CRM (requires provisioning script change — out of U02 deployment boundary)

---

## 4. SearchStrategy Improvements

- **List layout:** unchanged (already matched U01 recommendation)
- **Detail layout:** unchanged structure; tooltips added via i18n
- **Filters:** Draft, Ready, Active, Completed (`strategiesDraft`, `strategiesReady`, `strategiesActive`, `strategiesCompleted`)
- **Status colors:** `style` map on `status` field (presentation metadata)
- **scope `statusField`:** `status` for native status sidebar
- **clientDefs `filterList`:** four strategy filters
- Generate Jobs label: "Generate Discovery Jobs"

---

## 5. SearchJob Improvements

- **List columns added:** `startedAt`, `completedAt`, `errorMessage`
- **List column removed:** `source` (remains on detail as Provider)
- **Detail Execution panel:** added `failureReason` alongside `errorMessage`; `prospectCount` visible
- **Status colors:** QUEUED/RUNNING/COMPLETED/FAILED/CANCELLED styles
- **Labels:** Discovery Jobs, Finished At, Discovered Prospects relationship panel
- **scope `statusField`:** `status`

---

## 6. ProspectPool Improvements

- **List columns added:** `website`
- **List columns removed:** `qualificationStatus`, `crmPushStatus` (remain on detail)
- **Detail panel renamed:** "Raw Prospect" → "Discovery Information"
- **Labels:** Lead Pool, Provider Reference ID, Pipeline Stage, user-facing queue names
- **Filters added:** New, Accepted, Rejected, Duplicate, Ready for Research (plus existing queue filters retained)

---

## 7. Dashlet Implementation

**Created:** `AcquisitionOverview.json`

- Native `views/dashlets/abstract/record-list`
- Entity: SearchStrategy
- Title: Prospecting Overview
- Shows 5 recent strategies with name, status, product, generated job count
- **No custom JavaScript**

**Deferred:** Adding dashlet to provisioned dashboard layout (`phase3c01_provision_acquisition_workspace.php`) — deployment file change excluded from U02.

---

## 8. Filters Implemented

### SearchStrategy

| Filter key | Label | Logic |
|------------|-------|-------|
| `strategiesDraft` | Draft | `status = DRAFT` |
| `strategiesReady` | Ready | `status = READY` |
| `strategiesActive` | Active | `status IN (GENERATED, RUNNING)` |
| `strategiesCompleted` | Completed | `status = COMPLETED` |

### ProspectPool

| Filter key | Label | Logic |
|------------|-------|-------|
| `prospectsNew` | New | `queue = DISCOVERY`, `status = WAITING` |
| `prospectsAccepted` | Accepted | `qualificationStatus = QUALIFIED` |
| `prospectsRejected` | Rejected | `qualificationStatus = REJECTED` |
| `prospectsDuplicate` | Duplicate | `queue = DISCOVERY`, `status = FAILED` |
| `prospectsReadyForResearch` | Ready for Research | `researchStatus = PENDING`, `qualificationStatus = QUALIFIED` |

Existing queue filters (`discoveryQueue`, etc.) retained.

---

## 9. Labels Updated

- Global scope names for acquisition entities
- SearchStrategy: Discovery Jobs Created, source plan friendly names
- SearchJob: Discovery Jobs, Provider, Finished At, Discovered Prospects
- ProspectPool: Lead Pool, Provider Reference ID, simplified queue labels
- Dashlet: Prospecting Overview

---

## 10. Metadata Validation

| Check | Result |
|-------|--------|
| JSON syntax (`crm-extension/**/*.json`, 123 files) | **PASS** (0 errors) |
| PHP syntax | **Skipped** — `php` CLI not available in environment |
| Surface/module entityDefs parity (SearchJob, SearchStrategy status style) | **PASS** (manual mirror) |
| Layout mirrors (Resources ↔ module) | **PASS** |

---

## 11. Test Results

### Before U02.1

| Suite | Result |
|-------|--------|
| `crm-extension.tests.test_phase3c02_search_strategy_foundation` | **PASS** (2/2) |
| `deployment.validation.test_phase3c02_1a_search_strategy_detail` | **PASS** (2/2) |
| `crm-extension.tests.test_extension_skeleton` | **PARTIAL** (36/38) |

### After U02.1

| Suite | Result |
|-------|--------|
| `crm-extension.tests.test_extension_skeleton` | **PASS** (38/38) |
| `crm-extension.tests.test_phase3c02_search_strategy_foundation` | **PASS** (2/2) |
| `deployment.validation.test_phase3c02_1a_search_strategy_detail` | **PASS** (2/2) |
| `python -m unittest discover -s crm-extension/tests -p "test_*.py"` | **PASS** (47/47) |
| JSON validation (`crm-extension/**/*.json`) | **PASS** (123 files, 0 errors) |
| PHP syntax | **Unavailable** — `php` CLI not on PATH |

---

## 11.1 Phase3U02.1 — UI Regression Baseline Alignment

**Objective:** Resolve stale test expectations introduced by approved U02 presentation-only files. No production metadata or business logic changed in U02.1.

### Test files changed

| File | Change |
|------|--------|
| `crm-extension/tests/test_extension_skeleton.py` | Exact SearchStrategy PrimaryFilter inventory + ProspectPool filterList/selectDefs expectations |
| `crm-extension/tests/test_phase3c06_prospecting_ui_foundation.py` | SearchJob/ProspectPool layout and i18n expectations aligned to U02 panels/labels |

### Why each expectation changed

1. **`test_only_standard_research_evidence_php_shells_exist`** — U02 added four presentation-only PrimaryFilter PHP classes under `Select/SearchStrategy/PrimaryFilters/`. Inventory now lists those four files exactly and asserts the directory contains only that set (strict equality, no open-ended allowance).
2. **`test_phase3c01_acquisition_workspace_foundation`** — U02 added ProspectPool business filters (`prospectsNew`, `prospectsAccepted`, `prospectsRejected`, `prospectsDuplicate`, `prospectsReadyForResearch`) ahead of the existing queue filters. Assertions now require the full ordered `filterList` and exact `selectDefs` key set; each class file is still verified to exist.
3. **`test_phase3c06_prospecting_ui_foundation` layout tests** — Parallel C06 draft panel/list expectations predated U02. Updated to U02 approved panels (`Discovery Job` / `Execution` / `Ownership`; `Discovery Information` / `Acquisition Pipeline`) and U02 list/i18n labels. Field-existence strictness retained.

### Strictness preserved

- Exact set equality for PHP inventory and filter keys (not weakened to subset/containment)
- SearchStrategy PrimaryFilters directory pinned to exactly four approved files
- ProspectPool filter order asserted as intentional UI order
- Layout field cells still must exist in entityDefs

### Production behavior

- **No** layouts, entityDefs, services, routes, providers, or runner changes in U02.1
- **Only** test expectation alignment

---

## 12. Boundary Confirmations

| Item | Changed? |
|------|----------|
| Backend contract changes | **NO** |
| Business logic changes (services, hooks, API) | **NO** |
| Acquisition pipeline changes | **NO** |
| Provider changes | **NO** |
| SearchJob lifecycle changes | **NO** |
| Database schema / new fields | **NO** |
| JavaScript added | **NO** |
| Deployment package / provisioning | **NO** (overview dashlet metadata only; layout provisioning deferred) |
| Git commit | **NO** |

---

## 13. Deferred to Later Phases

- Dashboard provisioning layout update (Prospecting Overview placement, "Prospecting Home" tab rename)
- Retry Job, Push to CRM, Mark Duplicate actions
- Accept/Reject mass actions with workflow guards
- Lead back-link from ProspectPool
- Runtime CRM UI verification (browser)
- Tab order customization beyond scope name labels

---

## 14. Architecture Alignment

Follows Phase3U01 recommendation:

**Native Entity-first UI + Acquisition Overview Dashlet** (metadata-only; zero custom JS views).
