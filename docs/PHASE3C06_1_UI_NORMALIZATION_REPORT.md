# Phase3C06.1-B UI Normalization Report

**Repository:** `D:\EspoCRM-Production`  
**Scope:** Dashboard and dashlet titles, navigation labels and ordering, translations, and UI-contract tests only.  
**Status:** **SOURCE PASS - RUNTIME DEPLOYMENT/CACHE UPDATE REQUIRED**

## Result

The Phase3U02/Phase3C06 presentation vocabulary is normalized without creating a new ownership boundary:

- `ProspectingDashboard` is labelled **Prospecting Operations**.
- The formerly duplicate `AcquisitionOverview` dashlet is labelled **Acquisition Overview**.
- Both Prospecting sidebars use this workflow order: **Search -> Search Jobs -> Prospect Pool -> Research Evidence**.
- Search Strategy remains reachable after that canonical sequence; its frozen U02 entity surface is not redefined.
- `Global.json` registers `ProspectingDashboard` and `ProspectingSearch` scope names and uses **Search Jobs** / **Prospect Pool** consistently for the native acquisition entities.

## Files Changed

| Area | Files | Change |
| --- | --- | --- |
| Scope and entity translations | `Resources/i18n/en_US/Global.json`, `ProspectingDashboard.json`, `ProspectingSearch.json`, `SearchJob.json`, `ProspectPool.json`, `SearchStrategy.json` | Canonical titles and business-facing translations. |
| Dashlets | `metadata/dashlets/AcquisitionOverview.json`, `AcquisitionDiscoveryJobs.json`, `AcquisitionLeadPool.json` | Titles changed to Acquisition Overview, Search Jobs, and Prospect Pool. |
| Navigation presentation | `files/client/custom/res/templates/prospecting/dashboard.tpl`, `search.tpl` | Dashboard title, labels, Research Evidence entry, and canonical navigation order. |
| UI contract tests | `tests/test_phase3c06_prospecting_ui_foundation.py`, `test_phase3u03_menu_empty_state.py` | Scope-name, title, vocabulary, and navigation-order expectations. |

## Ownership and Boundary Confirmation

- Phase3U02 retains ownership of `SearchJob` and `ProspectPool` layouts and entity clientDefs.
- No layout, entity definition, entity clientDef, migration, API, connector, worker, or runtime logic was changed by this phase.
- No production/customer data was accessed or changed.

## Validation

### Extension tests

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-tests.ps1 extension -PythonExecutable C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

**PASS - 57 tests passed, 0 failed, 0 skipped.**

### Browser smoke (Admin required)

Read-only navigation in the existing local authenticated EspoCRM session to `#ProspectingDashboard`, `#ProspectingSearch`, `#SearchJob`, `#ProspectPool`, and `#ResearchEvidence` completed without browser-visible error alerts. The native entity routes rendered, including the Research Evidence surface. The accessible browser UI did not expose a role name, so the session cannot be independently attested as Admin for this phase.

The local runtime is serving an older installed/cache-resolved Prospecting UI: it still renders **Prospecting Dashboard**, **Prospecting Search**, **Discovery Jobs**, and **Lead Pool**, and its dashboard sidebar lacks Research Evidence. Consequently, the required Admin browser validation is **DEFERRED / not passable** until the updated extension is installed, EspoCRM metadata/cache is rebuilt, and an Admin session is confirmed. No installation, cache rebuild, or runtime mutation was performed in this phase.

## Commit

No commit was created.
