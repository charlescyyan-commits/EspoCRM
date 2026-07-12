# Phase3A30 — EspoCRM Native Sales Dashboard Report

**Date:** 2026-07-11  
**Scope:** Native EspoCRM dashboard configuration only. No custom frontend, React page, iframe, pipeline engine, CRM schema change, or core EspoCRM source modification was made.

## Result

The native dashboard template **`Chitu Native Sales Dashboard`** was created/updated in local EspoCRM and appended (rather than replacing any existing dashboard) for:

- `admin` (`admin` user type)
- `api_test` (`regular` user type)

The native EspoCRM deployment service correctly rejected the `chitu_ai_connector` API user as a dashboard recipient. This preserves EspoCRM's user-type boundary and does not give the integration account a UI dashboard.

## Native Dashlets

| Required view | Native dashlet | Native configuration |
|---|---|---|
| A Tier Leads | `Records` | `Lead` records with existing `peTierA` primary filter, ordered by `peOpportunityScoreV4` descending |
| Pending Follow Up | `Tasks` | Native Task dashlet with its built-in actual/pending follow-up filter and current-user visibility |
| Email Status Summary | `Records` | `Lead` records showing `peEmailStatus`, `peLastEmailDate`, and `peEmailCampaignName` |
| Open Opportunities | `Opportunities` | Native Opportunity dashlet with EspoCRM's native open-opportunity filter |
| Pipeline Value | `SalesPipeline` | Native sales-pipeline chart using `Opportunity.amount`, stage, and close date; date filter is `ever` |

The dashboard uses the native `Lead`, `Task`, and `Opportunity` ACL scopes exposed by each native dashlet. `peEstimatedValue` remains optional intelligence context; the pipeline chart correctly uses the CRM-owned native `amount` field.

## Persisted Dashboard Configuration

The following native dashboard IDs are present in both deployed user Preferences records:

```text
chitu-a-tier-leads        Records
chitu-pending-follow-up  Tasks
chitu-email-status-summary Records
chitu-open-opportunities Opportunities
chitu-pipeline-value     SalesPipeline
```

Each recipient preserved its existing blank/default layout item and now has all five requested dashlets. Re-running the deployment updates these same dashlet IDs, preventing duplicate dashlets.

## Fields And Metadata Changes

Phase3A30 added **no fields** and made **no custom metadata-file changes**. It consumes:

- Existing Lead primary filter `peTierA` (`peScoreTier = A`)
- Existing Lead email-status fields from Phase3A27
- Native Task, Opportunity, Records, and SalesPipeline dashlet metadata
- Native `DashboardTemplate.layout`, `DashboardTemplate.dashletsOptions`, and user `Preferences.dashboardLayout`/`Preferences.dashletsOptions` records

No database schema or migration was changed.

## Validation Evidence

### Runtime And Extension

| Check | Result |
|---|---|
| `espocrm` container | PASS — healthy on `http://localhost:8080` |
| `espocrm-db` container | PASS — healthy |
| Native dashboard template deployment | PASS — all five IDs persisted for `admin` and `api_test` |
| API-user dashboard deployment | PASS — native service rejected the API user type |

### API And CRM Data

Authenticated local API checks completed successfully under the existing test integration role:

| Data check | Result |
|---|---|
| A-tier Lead records (`peScoreTier = A`) | PASS — query works; current CRM count is `0` |
| Email-status Lead records | PASS — `4` records |
| Pending Task records | PASS — `6` open records |
| Open Opportunity records | PASS — `1` record |
| Native pipeline amount | PASS — `1` opportunity, total native `amount = 50000.0` |
| Lead/Task/Opportunity ACL | PASS — connector role has explicit `read=all`; native dashlets declare the corresponding ACL scopes |

### Regression Tests

Command:

```text
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client tests.test_espocrm_lifecycle_sync -v
```

Result: **PASS — 50 tests**. This includes the Phase3A28 Opportunity metadata and Phase3A29 lifecycle-sync regression coverage. Existing Lead sync remains unchanged.

### Browser Verification

| Check | Result |
|---|---|
| EspoCRM UI reachable | PASS — browser reached the native EspoCRM login page |
| Authenticated dashboard load | BLOCKED — no local UI username/password session was configured |
| Visual dashlet layout rendering | BLOCKED by the same missing authenticated UI session |
| Multi-user permission rendering | BLOCKED by the same missing authenticated UI session |

The browser check was not bypassed with API credentials, account changes, or a custom UI. To complete the remaining visual acceptance checks, sign in as `admin` and `api_test` in EspoCRM and verify each native dashlet is visible only when its `Lead`, `Task`, or `Opportunity` scope is readable.

## Files Changed

- `D:\Chitu-intelligence\docs\espocrm-extension\PHASE3A30_NATIVE_DASHBOARD_REPORT.md`

Temporary local deployment/inspection scripts were removed after validation and are not part of the deliverable.
