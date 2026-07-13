# Phase3B07.1 Local Runtime Recovery Report

**Scope:** Local test environment only: `D:\EspoCRM-Test`, Docker, and `http://localhost:8080`.

**Final verdict:** **PHASE3B07_1 STATUS: FAIL**

## 1. Recovery Summary

Phase3B07 implementation was not reworked. This recovery changed only the local Docker runtime configuration required to restore Cron and daemon health. No Production business code, connector behavior, CRM schema, ACL, Docker image version, volume, Railway configuration, or email behavior was changed.

## 2. Runtime Root Cause

The failing main-container health check was not a test-environment exemption.

- `data/config.php` had `cronDisabled=true`.
- `D:\EspoCRM-Test\docker-compose.yml` had no Cron runner to invoke EspoCRM `cron.php` each minute.
- `docker-daemon.sh` first calls `bin/command app-check`; when Cron was disabled it logged `Waiting for the main container to be ready...` and exited successfully. Docker restart policy made this appear as a daemon restart loop.
- Therefore: Cron configuration failure was the root cause; daemon restart was a downstream readiness result, not a daemon command, database, or permission failure.

## 3. Local Configuration Change

Only `D:\EspoCRM-Test\docker-compose.yml` changed:

- Added `ESPOCRM_CONFIG_CRON_DISABLED: "false"` to `espocrm`.
- Added `espocrm-cron`, using the existing `espocrm/espocrm:10.0.1` image, `volumes_from: espocrm`, and a 60-second loop executing `/usr/local/bin/php /var/www/html/cron.php`.
- Recreated only `espocrm`, `espocrm-cron`, and `espocrm-daemon`. No Compose infrastructure, image, database, or volume was replaced or deleted.

The installed image does not contain `docker-crontab.sh`; the runner implements EspoCRM's documented requirement to execute `cron.php` every minute.

## 4. Container Health Verification

At 2026-07-13 11:47:52 +08:00:

| Container | State | Restarts | Result |
| --- | --- | ---: | --- |
| `espocrm` | `running (healthy)` | 0 | PASS |
| `espocrm-cron` | `running` | 0 | PASS |
| `espocrm-daemon` | `running (healthy)` | 0 | PASS |
| `espocrm-db` | `running (healthy)` | unchanged | PASS |

Five retained main-container health checks, one minute apart, and five daemon health checks, three minutes apart, all reported Migration, Database, maintenance state, and `Cron is enabled: OK`. Current `bin/command app-check` also passed. No application or daemon fatal log was found after recovery; the only 404 log entries were the intentional direct entity-list route observations noted below.

## 5. Admin Browser Verification

The existing Compose Admin credential was stale. The authorized local-only command `bin/command set-password admin` reset the local Admin password; its plaintext is not recorded.

Admin browser verification passed for:

- authenticated Web login;
- Prospecting Operations dashboard loading without an Admin dashboard error;
- readable predefined Lead filter labels;
- Lead detail `Sync Information`, `Opportunity Proposal`, `AI Research Evidence`, `Sales Feedback`, and `Learning Signals` sections;
- full Admin diagnostic fields without internal `pe*` filter-key labels.

ResearchEvidence and SalesFeedback panels are visible on Lead detail. Direct client routes `#ResearchEvidence/list`, `#SalesFeedback/list`, and `#LearningSignal/list` returned the application's 404 page; this existing UI route behavior was observed and not changed under the local-runtime-only scope.

## 6. Sales Role Smoke Verification

- **Sales User: PASS.** Login, Prospecting dashboard, and the visible business-facing Lead predefined filters passed. The filter menu displayed labels including A Tier Leads, Research Pending, Proposal Review Required, Sync Failed, and Missing Best First Product, not internal keys.
- **Sales Manager: FAIL.** The Prospecting Operations dashboard shows business labels and visible Leads, but its Sync Issues dashlet returns `Bad request: Not access to order by field 'peLastSyncAt'.` This is a dashboard sort/ACL compatibility error. It is not caused by absent ownership, and correcting it would exceed the authorized local runtime recovery scope.

## 7. API and Regression Validation

| Check | Result |
| --- | --- |
| Authenticated `GET /api/v1/App/user` | PASS |
| Authenticated `GET /api/v1/Lead?maxSize=1` | PASS |
| Extension static tests | `35 PASS` |
| Connector regression tests | `58 PASS` |
| JSON duplicate-key validation | `47` files, `0` errors |
| Installed extension PHP syntax | PASS |
| Python compile | PASS |
| ZIP manifest version | `1.7.0-alpha` |
| ZIP SHA-256 | `1A5230829D09F2816F156CB345663676E07F6FB93714F1C609FD7A98FEA2751F` PASS |

## 8. Cleanup and Opportunity Validation

No `[CHITU_PHASE3B07_1_TEST]` data, temporary API identity, or temporary dashboard was created in this recovery.

| Marker check | Result |
| --- | ---: |
| Lead | 0 |
| ResearchEvidence | 0 |
| SalesFeedback | 0 |
| Task | 0 |
| Opportunity | 0 |
| Temporary identity | 0 |

No Opportunity was created. The local database contains one unrelated pre-existing `[CHITU_PHASE3A29_TEST]` Opportunity; it was not a B07/B07.1 marker and was untouched.

## 9. Final Verdict

**PHASE3B07_1 STATUS: FAIL**

**PHASE3B07 STATUS: FAIL**

All runtime, Cron, daemon, Admin, API, regression, package, and cleanup gates now pass. The strict final acceptance remains FAIL because the Sales Manager's required Prospecting Operations dashboard still raises the `peLastSyncAt` ordering error. No Phase3B08 work was started.

## 10. Phase3B07.2 Resolution

The B07.1 runtime recovery result remains historically accurate: at that point the Sales Manager Dashboard still failed. Phase3B07.2 subsequently fixed the final blocker in the canonical Dashboard provisioning.

- Sync Issues changed from `peLastSyncAt DESC` to ACL-compatible `modifiedAt DESC` while retaining `peSyncFailed`.
- Sales Manager's `peLastSyncAt` field ACL remains `read=no, edit=no`; no Role or entity ACL was expanded.
- Sales Manager no longer receives unavailable ResearchEvidence/SalesFeedback dashlets; Admin and Sales User retain those permitted dashlets.
- Fresh Manager, Admin, and Sales User browser sessions loaded without Dashboard, API, or console errors.
- Browser access logs confirmed `orderBy=modifiedAt` and HTTP `200` for all three roles.
- `1.7.1-alpha`, full regression, package integrity, runtime health, and zero-residual cleanup all passed.

**REVISED PHASE3B07_1 STATUS: PASS**

**REVISED PHASE3B07 STATUS: PASS**

The original B07.1 FAIL verdict remains above as the pre-fix historical result. No Phase3B08 work was started.
