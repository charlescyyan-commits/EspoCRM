# Phase 3A-34 — Native Layout Activation Validation Report

**Date:** 2026-07-11  
**Target:** `http://localhost:8080` local EspoCRM only  
**Status:** COMPLETE (PASS)  
**Scope:** Lead layout activation / metadata visibility only

## 1. Verdict

Sales User (`sales_test`) now receives the Prospecting Lead detail layout (Intelligence Summary, AI Research, Email Status, Sync Information, Contact & Ownership) instead of the core Crm Overview/Details layout.

Root cause was **layout resolution**, not ACL, roles, or LayoutSets.

## 2. Root Cause

EspoCRM `LayoutProvider` resolves Lead layouts as follows:

1. `custom/Espo/Custom/Resources/layouts/Lead/*.json` (admin Layout Manager overrides)
2. Scope module for Lead = **Crm** → `application/Espo/Modules/Crm/Resources/layouts/Lead/detail.json`
3. Only if missing: reverse module list (would reach Prospecting)

Phase 3A-25B correctly shipped:

`custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json`

…but **never activated it**. Because Crm already owns `Lead/detail.json`, FileReader returned Overview/Details and never consulted Prospecting.

Confirmed pre-fix:

| Check | Result |
|---|---|
| Prospecting `Lead/detail.json` on disk | Present (custom panels) |
| Crm `Lead/detail.json` on disk | Present (Overview / Details) |
| `custom/Espo/Custom/.../Lead/detail.json` | Absent |
| `app.layouts.Lead` metadata | `null` |
| LayoutSet on users/teams | None |
| `LayoutProvider.get('Lead','detail')` | Core Overview / Details |

This matches Phase 3A-33 observation: Sales User saw standard layout while field ACL still enforced.

## 3. Fix Applied

Added extension metadata so Prospecting owns Lead detail/list layouts:

**File:** `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/layouts.json`

```json
{
  "Lead": {
    "detail": { "module": "Prospecting" },
    "list": { "module": "Prospecting" }
  }
}
```

Deployed into the running container, then:

- `php command.php clear-cache`
- `php command.php rebuild`

No Custom frontend, no core modification, no ACL model change, no sync/scoring/email changes.

## 4. Layout Assignment Audit

| Actor | LayoutSet | Resolved Lead detail |
|---|---|---|
| System / LayoutProvider | n/a | Prospecting panels |
| Admin | none | Same default (no LayoutSet) — provider PASS |
| Sales User (`sales_test`) | none | Prospecting panels — API + browser PASS |
| Sales Manager (`manager_test`) | none | Prospecting panels — API PASS |

Admin HTTP Basic auth against `/api/v1/Lead/layout/detail` returned 401 with the container’s declared `ESPOCRM_ADMIN_PASSWORD` (password drift on this instance). Layout assignment for Admin is still the shared default path: no role/team LayoutSet exists, so Admin receives the same Prospecting layout once authenticated in UI.

Expected panels after activation:

1. Lead Intelligence Summary  
2. Sales Activity  
3. Email Status  
4. AI Research Information  
5. Sync Information  
6. Contact & Ownership  

Core panels **Overview** / **Details** are no longer returned.

## 5. Browser Verification (`sales_test`)

Login: `sales_test` / `SalesTest#2026`  
Lead: seeded MatterHackers ACL UI seed (cleaned after verification)

| Section | Visible |
|---|---|
| Lead Intelligence Summary | PASS |
| AI Research Information | PASS |
| Email Status | PASS |
| Sync Information | PASS |
| Contact & Ownership | PASS |

### ACL field behavior on the activated layout (unchanged from 3A-33)

| Field group | Expectation | Observed |
|---|---|---|
| AI / research (`peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peResearchSummary`, …) | Readable, not editable by sales | Visible on detail (view mode) |
| Sync / technical (`peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peEngineVersion`, `peScoreRulesVersion`) | Hidden (`read=no`) | Absent from Sync Information panel / API payload |

Sync Information still renders for sales, but only with fields they may read (e.g. Research Status / Qualification / Evidence Coverage). Hidden sync fields do not leak.

## 6. Regression

| Suite | Result |
|---|---|
| `espocrm_extension.tests.test_extension_skeleton` (incl. new `test_phase3a34_lead_layout_activation_metadata`) | 18 PASS |
| `tests.test_espocrm_sync_adapter` + `tests.test_espocrm_real_client` (combined with skeleton) | **48 tests OK** |
| Sales User field ACL (`temp/_phase3a33_field_acl.py`) | PASS before cleanup |
| ACL model / Role permissions | Unchanged |
| Sync / scoring / email systems | Unchanged |
| Phase 3A-24 foundation | Unchanged |

Synthetic seed Lead/Opportunity removed after verification. Temporary client logout helper removed.

## 7. Modified / Added Files

| Path | Role |
|---|---|
| `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/layouts.json` | Activates Prospecting Lead detail/list |
| `espocrm_extension/tests/test_extension_skeleton.py` | Asserts `app.layouts.Lead` + custom section labels |
| `docs/espocrm-extension/PHASE3A34_LAYOUT_ACTIVATION_REPORT.md` | This report |

Runtime-only (not packaged): deploy/verify helpers under `temp/_phase3a34_*`.

## 8. Explicitly Not Done

- UI redesign / custom frontend / CSS  
- ACL model or field-permission changes  
- Sync / scoring / email engine changes  
- Phase 3A-24 foundation changes  
- Core EspoCRM file edits  

## 9. Completion

Native Lead detail layout activation is fixed and validated for Sales User without custom frontend or core modification. STOP condition not triggered.
