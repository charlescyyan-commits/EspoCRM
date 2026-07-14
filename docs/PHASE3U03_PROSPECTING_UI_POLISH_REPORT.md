# Phase3U03 — Prospecting UI Polish & Dashboard Productization Report

**Date:** 2026-07-13  
**Prior freeze:** Phase3U02 Native Prospecting UI Foundation — PASS / FROZEN  
**Browser baseline:** Phase3U02.2 — PASS WITH MINOR FINDINGS  
**Verdict:** **SOURCE AND REGRESSION PASS; BROWSER VALIDATION DEFERRED**

---

## 1. Changes Made

### Phase A — Presentation polish (earlier in U03)

| Area | Change |
|------|--------|
| Navigation declutter | `SalesFeedback` / `LearningSignal` / `EmailEvent` → `tab: false` |
| Module prominence | `module.json` order `25` → `15` |
| Layout polish | Hide `queryFingerprint`; ProspectPool business-first + Pipeline panel |
| Labels | Discovery Jobs / Lead Pool retained; job dashlet titles clarified |

### Phase B — Dashboard productization (this stage)

| Area | Change |
|------|--------|
| `#ProspectingDashboard` | Replaced placeholder/dev cards with **Prospecting Overview** workbench |
| Prospecting Summary | Live entity totals (0 + “No data available” when empty) — **no fake data** |
| Recent Discovery Activity | Latest Search Jobs: Name / Status / Created / Count |
| Home dashlets | New `ProspectingSummary` + `ProspectingRecentDiscovery` dashlets |
| Prospecting Home (C01) | Summary + Recent Discovery placed first |
| Prospecting Operations (B07) | Summary + Recent Discovery prepended above Lead ops dashlets |

C06 Search runtime contract unchanged (`QUEUED` only; no provider/worker calls).

---

## 2. Metadata / Client Files Changed

### New

| File | Purpose |
|------|---------|
| `metadata/dashlets/ProspectingSummary.json` | Summary dashlet definition |
| `metadata/dashlets/ProspectingRecentDiscovery.json` | Recent Search Jobs list dashlet |
| `client/.../views/dashlets/prospecting-summary.js` | Native count dashlet view |
| `client/.../templates/dashlets/prospecting-summary.tpl` | Summary empty-safe UI |
| `tests/test_phase3u03_dashboard_productization.py` | Presentation contract tests |

### Updated

| File | Purpose |
|------|---------|
| `client/.../views/prospecting/dashboard.js` | Load live ProspectPool/SearchJob counts + recent jobs |
| `client/.../templates/prospecting/dashboard.tpl` | Overview layout, summary, recent activity, empty states |
| `i18n/en_US/Global.json` | Dashlet labels |
| `i18n/en_US/ProspectingDashboard.json` | Tab label → Prospecting Overview |
| `deployment/provisioning/phase3c01_provision_acquisition_workspace.php` | Place new dashlets on Prospecting Home |
| `deployment/provisioning/phase3b07_provision_operations_dashboards.php` | Prepend overview dashlets |
| C06 / skeleton tests | Expectation alignment |

---

## 3. Navigation Changes

Sidebar on Prospecting Overview (productized order):

```text
Prospecting
  Overview
  Discover
  Search Strategies
  Discovery Jobs
  Lead Pool
```

Plus a short workflow reminder panel (plan → jobs → pool → research).

---

## 4. Dashlet Changes

### Prospecting Summary

| Metric | Source |
|--------|--------|
| Total Prospects | `ProspectPool` total |
| New This Week | `ProspectPool` `createdAt` last 7 days |
| Need Research | primary filter `prospectsReadyForResearch` |
| Research Completed | `researchStatus = COMPLETED` |
| High Priority | `SearchJob` `priority = P1` |

Empty: shows **0** and **No data available**. Never invents totals.

### Recent Discovery Activity

Native `record-list` on `SearchJob`:

- Name (link)
- Status
- Created (`createdAt`)
- Count (`resultCount`)

---

## 5. Sales User Impact

| Before | After |
|--------|-------|
| Placeholder “—” cards / opaque foundation copy | Business summary metrics from real entities |
| Home ops board led with formula-test Lead rows | Overview metrics + Discovery Jobs first; Lead ops moved below |
| Empty lists felt broken | Explicit empty states with next-step links |

Test Lead names such as `PHASE3B02 FORMULA-TEST` are **not generated** by U03. They may still appear in lower Lead-intelligence dashlets if those records exist in the DB; cleanup remains an environment data task.

---

## 6. Test Results

| Suite | Result |
|-------|--------|
| `python -m unittest discover -s crm-extension/tests -p "test_*.py"` | **PASS** (51/51) |
| Includes `test_phase3u03_dashboard_productization` | **PASS** (4/4) |
| JSON metadata | Valid |

Live CRM browser verify requires extension reinstall/rebuild into the test stack (source updated in repo; container may still serve prior package).

---

## 7. Deferred Items

| Item | Reason |
|------|--------|
| Global tabList rewrite | Not used: U03-B/C relies on native module order and existing scope tabs, avoiding a user-preferences mutation. |
| Empty states for non-business technical entities | Out of scope; all requested business Prospecting pages are covered. |
| Delete synthetic Lead test data | Data ops, not UI metadata |
| React/SPA redesign | Explicitly forbidden |

---

## 8. Boundary Confirmations

| Constraint | Status |
|------------|--------|
| C01–C05 business logic / providers / research pipeline | **Untouched** |
| C06 Search runtime contract (`QUEUED` only) | **Untouched** |
| No SPA / no core EspoCRM fork | **Confirmed** |
| No DB schema changes | **Confirmed** |
| No fake metrics | **Confirmed** |
| No git commit | **Confirmed** |

---

## 9. Architecture Alignment

```text
Native EspoCRM views + dashlets + provisioning placement
= sales Prospecting Overview workbench
```

**Phase 1 (Dashboard) complete.** Do not start unrelated U04 feature work unless requested.

---

## 10. Phase3U03-B/C Menu and Empty-State Completion

### Menu Changes

| Surface | Before (local browser runtime) | After (source contract) | Reason |
| --- | --- | --- | --- |
| Prospecting module prominence | Prospecting remained after Sales Pipeline in the loaded runtime menu. | `Resources/module.json` sets `order: 5`, ahead of the normal CRM/Sales groups. | Make Prospecting a primary business entry without hiding CRM modules. |
| Prospecting sidebar | Dashboard, Search, Search Jobs, Prospect Pool, Search Strategy; no Research Evidence entry. | Prospecting Operations, then Search -> Search Jobs -> Prospect Pool -> Research Evidence; Search Strategy remains reachable after the business sequence. | Align the navigation with the acquisition workflow while retaining the frozen Strategy surface. |
| Tab visibility | Not verifiable from the stale runtime package. | Dashboard, Search, Search Job, Prospect Pool, Research Evidence, and Search Strategy remain `tab: true`; Email Event, Learning Signal, and Sales Feedback remain hidden technical tabs. | Preserve ACL and URL behavior, expose business work, and avoid hiding required CRM modules. |

No global tab list, user preferences, role permissions, URLs, or Sales Pipeline metadata was changed.

### Empty State Changes

| Entity | Before | After |
| --- | --- | --- |
| Prospect Pool | Empty list could appear without actionable copy. | `No prospects yet. Start a discovery search to build your prospect pool.` |
| Search Jobs | Empty list could appear without actionable copy. | `No search jobs yet. Create your first search job.` |
| Search Strategy | Empty list could appear without next-step guidance. | `No search strategies configured. Create a strategy to start discovery.` |
| Website Research | Empty list could appear without an explanation. | `Website research results will appear after prospects are analyzed.` |

The existing native record-list empty-state views render these translations. No fake records, computed fields, filter changes, or non-native page were introduced.

### List Presentation

| List | Confirmed display order |
| --- | --- |
| Prospect Pool | Name, Website, Country, Source, Research Status, Created |
| Search Jobs | Name, Provider, Strategy, Status, Result Count, Created |

The source field remains the existing Provider-labelled field; no new calculated or persisted field was added.

### Browser Validation

| Persona | Result | Evidence |
| --- | --- | --- |
| Admin | **DEFERRED** | The available authenticated local session did not expose a role name in the accessible UI, and the loaded runtime is stale. It still shows Prospecting Dashboard, Lead Pool, and Discovery Jobs, and lacks the Research Evidence sidebar entry. |
| Sales User | **DEFERRED** | No authenticated Sales User session or credentials were available. No role, ACL, or user-preference mutation was attempted. |
| Route smoke | **PASS for loaded runtime only** | `#ProspectPool`, `#SearchJob`, `#SearchStrategy`, and `#ResearchEvidence` all rendered without visible alert errors. This does not validate the updated source labels or empty states. |

An updated test extension installation, EspoCRM metadata/cache rebuild, and separate confirmed Admin and Sales User sessions are required before browser acceptance can be marked PASS. Those actions were not taken because this phase forbids runtime changes and role/ACL changes.

### Regression

| Check | Result |
| --- | --- |
| Phase3U03 menu/empty-state + dashboard tests; Phase3C06 UI tests | **PASS - 17 tests** |
| Connector suite | **PASS - 86 tests** |
| Core Regression Gate | **PASS - Extension 57, Connector 86, Worker 31, Static 2; 5/5 required suites** |

### Final Boundary and Status

- C01 through C05, C06 UI/runtime contract, backend, API, schema, database, runtime, worker, queue, provider, AI, scoring, and CRM sync were not changed.
- No business module was hidden and no Sales Pipeline or ACL behavior was modified.
- No commit was created and no Phase3C07 work was started.

**Phase3U03 source and regression status: PASS. Browser acceptance status: DEFERRED. Therefore Phase3U03 is not marked fully frozen until the required runtime browser acceptance is completed.**
