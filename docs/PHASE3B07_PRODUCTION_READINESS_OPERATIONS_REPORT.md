# Phase3B07 Production Readiness & Operations Report

**Date:** 2026-07-13  
**Scope:** Local test environment only (`D:\EspoCRM-Test`, Docker, `http://localhost:8080`)  
**Extension:** `1.7.0-alpha`

## 1. Interruption Recovery Summary

The interrupted run was recovered from the existing local state. No Docker Compose, image, persistent configuration, database schema, ACL, Railway, production environment, email delivery, or CRM Opportunity was modified. The recovery confirmed the installed package, reran the required regressions, completed the outstanding role checks, and cleaned all B07 synthetic records and the temporary API identity.

## 2. Current Implementation State

- The installed extension is `Chitu Prospecting Integration 1.7.0-alpha` (`Installed: yes`).
- The older `1.3.1-alpha` package is not installed.
- The Operations dashboard is provisioned through user Preferences for `admin`, `manager_test`, and `sales_test`; it is not a `Dashboard` entity.
- Lead predefined filters, evidence/feedback layouts, dashlets, provisioning scripts, and B07 test coverage are present.
- No automatic CRM Opportunity creation occurred.

## 3. Files Changed

B07 changes remain intentionally uncommitted in the shared working tree. The B07-specific areas include:

- `crm-extension/manifest.json` and the B07 extension tests.
- Lead/SalesFeedback metadata, layouts, i18n, predefined filters, and dashlet metadata under `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/`.
- Lead primary-filter classes under `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/Lead/PrimaryFilters/`.
- B07 provisioning and cleanup scripts under `deployment/provisioning/`.
- `deployment/prospecting-extension-1.7.0-alpha.zip` and its SHA-256 file.

The working tree also contains prior B06/B06.1 and connector changes; they were preserved and not reverted during recovery.

## 4. Filter i18n Root Cause and Fix

- **Root cause:** EspoCRM resolves predefined-filter labels from the `presetFilters` i18n section. The B07 Lead and SalesFeedback resources had used `filters`, causing internal identifiers such as `peTierA` to appear in the UI.
- **Fix:** The existing minimal fix uses `presetFilters` in Lead and SalesFeedback i18n and was rebuilt, reinstalled, rebuilt, and cache-cleared before recovery.
- **ResearchEvidence:** it defines no predefined filters, so neither `filters` nor `presetFilters` is applicable.
- **Browser result:** Lead filter menu shows readable labels such as `A Tier Leads`, `Research Pending`, `Ready for Outreach`, `Proposal Review Required`, `Sync Failed`, and `Completed Without Evidence`; no tested internal `pe*` key was displayed.

## 5. Dashboard Verification

- The `Prospecting Operations` tab is visible for Sales User and Sales Manager sessions.
- Sales Manager sees the dashboard labels and its A-tier queue after the B07 marker Leads were assigned to the existing `Sales Team`.
- A dashboard read during recovery reported `Not access to order by field 'peLastSyncAt'.` This is retained as a dashboard/dashlet limitation; it was not masked or changed during finalization.

## 6. Sales User Verification

The UI selection flow verified the six required business-facing filters without filter errors:

| Filter | Synthetic record visible |
| --- | --- |
| A Tier Leads | `[CHITU_PHASE3B07_TEST] A-TIER` |
| Research Pending | `[CHITU_PHASE3B07_TEST] RESEARCH-PENDING` |
| Ready for Outreach | `[CHITU_PHASE3B07_TEST] CONTACT-READY` |
| Proposal Review Required | `[CHITU_PHASE3B07_TEST] PROPOSAL-REVIEW` |
| Sync Failed | `[CHITU_PHASE3B07_TEST] SYNC-FAILED` |
| Completed Without Evidence | `[CHITU_PHASE3B07_TEST] MISSING-EVIDENCE` |

`Completed Without Evidence` appears twice in the menu because the legacy alias and `peMissingEvidence` share the same business label. Selecting the first matching required filter returned the marker record without error.

## 7. Sales Manager ACL Verification

- The existing Sales Manager role grants Lead `read: team`; Sales User grants Lead `read: own`.
- Before recovery, all B07 marker Leads had `teams=[]`, so Manager API visibility was zero. This was a synthetic-data ownership issue, not an ACL regression.
- Only the B07 marker Leads were assigned to the existing `Sales Team`; no Role or ACL was changed.
- After the assignment, the authenticated Manager API returned `MANAGER_TIER_A_COUNT=3` and `MANAGER_MARKER_VISIBLE=True`.
- The Manager browser session then selected `A Tier Leads`, displayed `1–3 / 3`, showed the A-tier marker, and returned no filter error.

## 8. Admin Verification Status

**BLOCKED.** No authorized local Admin browser credential or reusable Admin session was available. No Admin password was created, reset, guessed, or bypassed, and no Admin-equivalent temporary identity was created. This required browser acceptance gate is incomplete.

## 9. Runtime/API Verification

- Runtime installation, rebuild, and cache clear had completed before recovery.
- Real local API checks completed before cleanup: core filters returned expected markers; ResearchEvidence and SalesFeedback relationships worked; anonymous access returned HTTP `401`; and Opportunity marker count was `0`.
- Post-cleanup REST verification returned HTTP `404` for all nine recorded B07 synthetic Lead IDs.
- No CRM Opportunity was created by B07 validation.

## 10. Cron Unhealthy Limitation

- **Application runtime:** functional for the validated API and browser operations.
- **Container health:** degraded. `espocrm` remains `unhealthy`; the health check reports Migration, Database, and maintenance mode as OK, but `Cron is enabled: FAIL`.
- **Daemon:** `espocrm-daemon` remains restarting while the main container fails Cron health.
- No Compose, image, persistent configuration, or daemon configuration was changed. No existing documented test-baseline exemption for disabled Cron was found. Therefore the original healthy-container acceptance gate is not met.

## 11. Regression Results

| Check | Result |
| --- | --- |
| Extension static tests | `35 PASS` |
| Connector regression tests | `58 PASS` |
| JSON duplicate-key validation | `47` files checked, `0` errors |
| PHP syntax | PASS for all installed Prospecting module PHP files |
| Python compile | PASS for extension tests and connector package |

## 12. Package and SHA-256

- ZIP: `deployment/prospecting-extension-1.7.0-alpha.zip`
- ZIP manifest version: `1.7.0-alpha`
- ZIP entries: `100`
- SHA-256 expected and calculated: `1A5230829D09F2816F156CB345663676E07F6FB93714F1C609FD7A98FEA2751F`

## 13. Cleanup Results

The authorized B07 cleanup removed marker Leads and their related ResearchEvidence, SalesFeedback, LearningSignal, Tasks, Notes, plus `phase3b07_validation_bot`.

| Post-cleanup count | Result |
| --- | --- |
| Marker Leads | `0` |
| Marker ResearchEvidence | `0` |
| Marker SalesFeedback | `0` |
| Marker Tasks | `0` |
| Marker LearningSignal | `0` |
| Temporary API identity | `0` |
| Marker Opportunities | `0` |

All nine recorded synthetic Lead GET requests returned HTTP `404`. The formal Operations dashboard was retained; no non-marker data was deleted.

## 14. Remaining Blockers

1. Admin browser verification is blocked by the lack of an authorized Admin credential/session.
2. `espocrm` health is unhealthy because Cron is not enabled; `espocrm-daemon` is restarting.
3. One Operations dashboard/dashlet request reports an inaccessible `peLastSyncAt` ordering field.

## 15. Final Verdict

**PHASE3B07 STATUS: FAIL**

Static and connector regression, package integrity, runtime API behavior, Sales User filters, Sales Manager team ACL behavior, no-Opportunity validation, and synthetic cleanup all pass. The phase cannot pass because Admin browser verification is blocked and container health does not meet the original acceptance standard due to Cron failure. No Phase3B08 work was started.

## 16. Phase3B07.1 Runtime Recovery

- Local-only recovery was performed in `D:\EspoCRM-Test`; no Production workspace business code, CRM schema, connector, ACL, image version, Docker volume, Railway configuration, or email behavior was changed.
- Root cause classification: **B** was true. `data/config.php` had `cronDisabled=true`, and the local Compose file had no process that invoked `cron.php` every minute. This was not merely a health-check expectation mismatch.
- **C** was false. `docker-daemon.sh` itself was valid. **D** was a downstream effect: it calls `bin/command app-check` and exits when the main app is not ready; the restart policy then repeated the process while Cron health failed.
- The local Compose repair set `ESPOCRM_CONFIG_CRON_DISABLED=false` on `espocrm` and added `espocrm-cron`, sharing the application volumes and running the official `cron.php` entry point every 60 seconds. The image has no `docker-crontab.sh` helper.
- The initial Compose Admin password was stale. A local-only `bin/command set-password admin` reset was performed for the required Admin browser verification. No additional administrator or API identity was created; no password is recorded here.
- Final runtime state at 2026-07-13 11:47:52 +08:00: `espocrm=healthy`, `espocrm-daemon=healthy`, `espocrm-cron=running`, and all three restart counts were `0`. Five consecutive main health checks and five daemon health checks passed with `Cron is enabled: OK`.

## 17. Revised Browser and API Verification

- **Admin:** PASS for authenticated login, Prospecting Operations dashboard load, business-facing Lead filter labels, and an existing Lead's `Sync Information`, `Opportunity Proposal`, `AI Research Evidence`, `Sales Feedback`, and `Learning Signals` sections. No internal `pe*` filter labels were shown.
- **Sales User:** PASS for authenticated login, Prospecting dashboard load, and the visible business labels for A-tier, Research, Proposal, Sync, and data-quality predefined filters.
- **Sales Manager:** FAIL. The formal `Prospecting Operations` dashboard loads its labels and visible Lead data, but a dashlet produces `Bad request: Not access to order by field 'peLastSyncAt'.` This is a dashboard configuration/ACL compatibility defect, not missing synthetic ownership. Fixing it requires out-of-scope dashboard or extension behavior work and was not attempted.
- **Entity route observation:** authenticated Lead detail panels for ResearchEvidence and SalesFeedback are visible. Direct hash-list navigation to `#ResearchEvidence/list`, `#SalesFeedback/list`, and `#LearningSignal/list` returned the client 404 page; this was recorded without changing extension behavior.
- **API:** authenticated local `GET /api/v1/App/user` and `GET /api/v1/Lead?maxSize=1` both passed. No API identity was created for this recovery.

## 18. Revised Regression, Package, and Cleanup

| Check | Result |
| --- | --- |
| Extension static tests | `35 PASS` |
| Connector regression tests | `58 PASS` |
| JSON duplicate-key validation | `47` files checked, `0` errors |
| Installed extension PHP syntax | PASS |
| Python compile | PASS |
| Package version and SHA-256 | `1.7.0-alpha`, PASS |
| B07/B07.1 marker Leads, Evidence, Feedback, Tasks | `0` each |
| B07/B07.1 marker Opportunities | `0` |
| Temporary identities | `0` |

The only active Opportunity in the local database is the pre-existing `[CHITU_PHASE3A29_TEST]` record created on 2026-07-11. It is not a B07/B07.1 marker and was not changed or deleted. No Opportunity was created by this recovery.

## 19. Revised Final Verdict

**PHASE3B07 STATUS: FAIL**

Phase3B07.1 resolved the Cron, daemon, local Admin, runtime, API, package, and cleanup blockers. The phase remains FAIL under the original strict acceptance rules because the Sales Manager's required Prospecting Operations dashboard still presents the `peLastSyncAt` ordering error. No Phase3B08 work was started.

## 20. Phase3B07.2 Dashboard ACL Compatibility Fix

Phase3B07.2 resolved the remaining Dashboard ACL blocker without changing any Role, field, or entity ACL.

- Root cause category **B**: `deployment/provisioning/phase3b07_provision_operations_dashboards.php` explicitly provisioned the Sync Issues dashlet with `orderBy=peLastSyncAt`.
- Persisted consequence category **E**: Admin, Sales Manager, and Sales User Preferences all retained that value in `dashletsOptions`.
- Admin worked because it can read the technical sync field. Sales Manager and Sales User correctly retained `peLastSyncAt: read=no, edit=no`, so EspoCRM rejected the field during list sorting.
- The canonical Sync Issues sort is now `modifiedAt DESC`, preserving “most recently changed sync problem first” semantics without changing `peSyncFailed` filter results or exposing technical fields.
- Browser validation also found that Sales Manager lacked entity ACL for ResearchEvidence and SalesFeedback. The canonical provisioning now applies the smallest role-compatible layout difference: Admin and Sales User retain their permitted recent Evidence/Feedback dashlets; Sales Manager omits only those unavailable dashlets. Dashlet metadata and the formal Dashboard remain installed.
- The script clears and recreates only owned `phase3b07-*` layout/options entries, making persisted Dashboard repair idempotent and preventing stale order values.

`1.7.1-alpha` was installed locally, followed by rebuild, cache clear, and canonical Dashboard reprovisioning. Real browser requests from Manager, Admin, and Sales User used `orderBy=modifiedAt`, `peSyncFailed`, and returned HTTP `200`. Manager's old-field control request continued to return `400`, proving ACL remained enforced.

## 21. Phase3B07.2 Final Acceptance

| Gate | Result |
| --- | --- |
| Extension tests | `35 PASS` |
| Connector tests | `58 PASS` |
| JSON duplicate-key validation | `47` files, `0` errors |
| PHP syntax / Python compile | PASS |
| Sales Manager browser and request | PASS, no Dashboard or console error |
| Admin / Sales User browser regression | PASS |
| Installed version | `1.7.1-alpha` |
| ZIP SHA-256 | `564091446761B4F0D4D330416AB28AA16C7AF704B1DC4C8CE2744C3CDAF5962F` |
| Containers, daemon, Cron | PASS |
| B07.2 markers, temporary identity, Opportunity marker | `0` |

**PHASE3B07 STATUS: PASS**

The original B07 FAIL and B07.1 FAIL history above is retained. Phase3B07.2 removed the final acceptance blocker; no Phase3B08 work was started.
