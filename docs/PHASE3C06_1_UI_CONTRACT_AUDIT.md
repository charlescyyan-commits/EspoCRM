# Phase3C06.1 UI Contract Audit

**Mode:** Audit only — no production code, metadata, deployment package, runtime, database, or ACL was changed.  
**Scope:** Phase3U02 Native Prospecting UI Foundation and Phase3C06 Prospecting UI Foundation contracts as represented by the current repository.  
**Verdict:** **NEED MERGE**

## Executive Finding

There is no duplicate clientDefs file, no duplicate route registration, and no competing EspoCRM layout-resolution path in the current tree. The conflict is contractual rather than a broken metadata load:

- U02 owns the native `SearchJob` and `ProspectPool` presentation layouts and their entity clientDefs.
- C06 owns the custom `#ProspectingDashboard` and `#ProspectingSearch` scopes, controllers, templates, and safe queued-job creation UI.
- C06's original detail-layout/navigation wording has been superseded in the test suite by U02 (and, for Dashboard, later U03) without a single reconciled contract document.

The contracts must be merged into one ownership matrix before this UI can be declared fully coherent.

## Evidence Reviewed

- `docs/PHASE3U02_NATIVE_PROSPECTING_UI_FOUNDATION_REPORT.md`
- `docs/PHASE3C06_PROSPECTING_UI_FOUNDATION_REPORT.md`
- `crm-extension/tests/test_phase3c06_prospecting_ui_foundation.py`
- Current Prospecting scopes, clientDefs, layouts, i18n, dashboard/search templates, controllers, dashlets, and layout routing metadata.

No browser, Provider, Runtime, Worker, Queue, AI, CRM, or external service was called for this audit.

## 1. ClientDefs Audit

| Check | Result | Evidence |
| --- | --- | --- |
| Duplicate `clientDefs` scope files | PASS | The repository contains one clientDefs JSON file per Prospecting scope; no duplicate basename was found. |
| C06 custom-scope ownership | PASS | `ProspectingDashboard.json` and `ProspectingSearch.json` each define one controller and one icon, respectively `custom:controllers/prospecting-dashboard` and `custom:controllers/prospecting-search`. |
| U02 entity-scope ownership | PASS | U02 changes are confined to `SearchStrategy.json`, `SearchJob.json`, and `ProspectPool.json` clientDefs: filters, record-list views, relationship panel, and/or native action metadata. |
| Cross-phase clientDefs overwrite | PASS | C06 uses `ProspectingDashboard` and `ProspectingSearch`; U02 uses existing entity scopes. No two files define the same scope. |

**Conclusion:** clientDefs do not require a mechanical merge. Ownership should nevertheless be documented explicitly to prevent C06 from reintroducing entity-layout/clientDefs expectations that U02 owns.

## 2. Layout Ownership Audit

`metadata/app/layouts.json` routes `SearchJob`, `ProspectPool`, and `SearchStrategy` list/detail layouts to the Prospecting module. For both `SearchJob` and `ProspectPool`, the extension surface layout and module layout are byte-for-byte equivalent mirrors; they are not alternative layout definitions.

| Entity / Surface | Current authoritative content | Contract finding |
| --- | --- | --- |
| SearchJob detail | `Discovery Job`, `Execution`, `Ownership` | U02-native layout. The C06 test explicitly states that U02 panels supersede C06 draft panel names. |
| ProspectPool list | `name`, `website`, `country`, `source`, `researchStatus`, `createdAt` | U02-native list. No separate C06 list file exists. |
| ProspectPool detail | `Discovery Information`, `Pipeline`, `Notes and Ownership` | U02-native layout. |
| SearchStrategy detail | `Strategy Definition`, `Query Plan` | Frozen existing surface; neither U02 nor C06 should redefine it. |

### Layout Contract Conflict

**NEED MERGE.** The conflict is not a runtime collision; it is a source-of-truth conflict:

1. C06 originally describes a future uniform detail layout (`Overview`, `Research`, `Evidence`, `AI`, `CRM`) and a Prospect Pool presentation focused on Website Research / Trace / Summary / Evidence / AI / CRM placeholders.
2. U02.1 changed `test_phase3c06_prospecting_ui_foundation.py` to assert U02 panels instead. The current test comment explicitly says U02 panels supersede C06 draft panel names.
3. The U02 report says `Acquisition Pipeline` in its U02.1 explanation, while the actual layout and current C06 test use the label `Pipeline`. This is documentation/test terminology drift.

The live metadata is internally coherent and U02 is the effective owner. The written C06 contract must be reconciled to that decision; otherwise a future C06 follow-up can legitimately attempt to restore the discarded panels.

## 3. Dashboard Audit

| Surface | Owner / implementation | Finding |
| --- | --- | --- |
| `#ProspectingDashboard` | C06 custom non-entity scope, controller, and dashboard view/template | One route and one renderer; no duplicate controller registration found. |
| `AcquisitionOverview` | U02 dashlet definition backed by `SearchStrategy` and titled `Prospecting Overview` | No U02 provisioning placement was made, so it does not replace the C06 route. |
| `ProspectingSummary` / `ProspectingRecentDiscovery` | Later U03 dashlets and dashboard productization | These later files now shape the C06 dashboard template/test expectations. |

### Dashboard Contract Conflict

**NEED MERGE.** U02's `AcquisitionOverview` dashlet and the C06 dashboard route both use the user-facing title **Prospecting Overview**. This is not a route collision, because one is a dashlet and the other is a tab/view. It is an ownership and user-meaning collision if the dashlet is later provisioned beside or into the route.

There is also post-C06 contract drift: the C06 report still describes six read-only placeholder cards, while the current dashboard template and C06 test assert the U03 productized summary/recent-activity dashboard. A merged UI contract must name one Dashboard owner and state whether `AcquisitionOverview` remains an optional entity dashlet, is renamed, or is intentionally not provisioned.

## 4. Navigation Audit

| Check | Result | Evidence |
| --- | --- | --- |
| Duplicate scope registration | PASS | `ProspectingDashboard`, `ProspectingSearch`, `SearchStrategy`, `SearchJob`, and `ProspectPool` are distinct scopes. |
| Duplicate route registration | PASS | Each custom C06 route has one controller; entity routes remain native EspoCRM record routes. |
| Global entity navigation | PASS | U02 labels the existing entities Search Strategies, Discovery Jobs, and Lead Pool using `Global.json`; their scopes are `tab: true`. |
| C06 local sidebar | NEED MERGE | The dashboard template provides a second navigation surface: `Overview → Discover → Search Strategies → Discovery Jobs → Lead Pool`. |
| Naming/order alignment | NEED MERGE | C06 acceptance wording says Dashboard / Search / Search Jobs / Prospect Pool / Search Strategy, while the actual local sidebar uses Overview / Discover / Search Strategies / Discovery Jobs / Lead Pool. The global labels are again slightly different (`Prospecting Search`, singular `Discovery Job` scope name). |

The two navigation surfaces are intentional access paths, not duplicate EspoCRM menu metadata. They need one declared label vocabulary and workflow order so the global navigation, dashboard sidebar, browser acceptance report, and future ACL tests do not diverge.

## Required Contract Merge Decisions

No code change is part of this audit. Before any UI follow-up, record these decisions in a single authoritative UI contract:

1. **Layout owner:** U02 owns `SearchJob` and `ProspectPool` layouts, labels, and entity clientDefs; C06 must not define competing detail-panel/list-column expectations.
2. **Dashboard owner:** C06 owns the route and custom view. Decide whether U02's `AcquisitionOverview` remains an optional dashlet, receives a distinct title, or is provisioned as part of the same Dashboard experience.
3. **Navigation vocabulary and order:** choose one canonical sequence and labels for the native tabs and C06 sidebar. The current implemented sidebar is `Overview → Discover → Search Strategies → Discovery Jobs → Lead Pool`.
4. **Terminology cleanup:** select `Pipeline` or `Acquisition Pipeline` and use it consistently in U02 report text, C06 report text, layouts, and tests.
5. **Document/test alignment:** update the C06 report/contract to distinguish the original C06 foundation from the later U02/U03 presentation supersession; retain the test statement only after the owner decision is formally recorded.

## Boundary Confirmation

- No code, metadata, tests, provisioning scripts, Docker configuration, runtime components, Provider adapters, AI, CRM behavior, or public APIs were modified.
- No browser session or external call was used.
- This report is the only artifact created by this audit.

## Final Verdict

**NEED MERGE.** The current metadata will load deterministically and contains no duplicate clientDefs or route registrations. However, layout ownership has been superseded in tests without a unified C06/U02 contract, the dashboard has a same-named route/dashlet concept plus later U03 drift, and local/global navigation labels and order are not governed by one source of truth.
