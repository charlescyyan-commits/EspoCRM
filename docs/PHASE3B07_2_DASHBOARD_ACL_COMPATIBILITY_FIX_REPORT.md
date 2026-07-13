# Phase3B07.2 Dashboard ACL Compatibility Fix Report

## 1. Final Verdict

**PHASE3B07_2 STATUS: PASS**

**PHASE3B07 STATUS: PASS**

## 2. Scope

The phase changed only the canonical Prospecting Dashboard provisioning, directly related tests, extension version/package artifacts, and reports. Runtime validation was limited to `D:\EspoCRM-Test` and `http://localhost:8080`.

No Role ACL, field ACL, entity ACL, database schema, Connector, V1 contract, canonical score, workflow, research, proposal, email, Docker Compose, Railway, or production environment was changed.

## 3. Root Cause

The primary root cause was category **B**. Function `provisionOperationsDashboard` in `deployment/provisioning/phase3b07_provision_operations_dashboards.php` explicitly created the Sync Issues options with `orderBy=peLastSyncAt`.

This created category **E** at runtime: Admin, `manager_test`, and `sales_test` Preferences all persisted `phase3b07-sync-issues.orderBy=peLastSyncAt`.

The other audited categories were not the trigger:

- **A:** the ProspectingIntelligence dashlet default is `peOpportunityScoreV4`, not `peLastSyncAt`.
- **C:** `peSyncFailed` contributes the primary filter only; it does not set ordering.
- **D:** Lead clientDefs does not define the Dashboard's default sort.
- **F:** EspoCRM did not inherit this value from a list layout.
- **G:** `peLastSyncAt` was not a displayed Dashlet column; it was an explicit hidden sort option.

## 4. Affected Dashboard / Dashlet

- Dashboard tab: `Prospecting Operations`.
- Dashlet ID: `phase3b07-sync-issues`.
- Dashlet type: `ProspectingIntelligence` record list.
- Primary filter: `peSyncFailed`.
- Failing ordering: `peLastSyncAt DESC`.

## 5. Why peLastSyncAt Failed for Sales Manager

The existing Sales Manager and Sales User field ACL intentionally sets Lead `peLastSyncAt` to `read=no, edit=no`. Admin can use the technical field because Admin is not restricted by those sales-role field ACL rules. EspoCRM validates an `orderBy` field against field access before executing a list query, so Sales Manager received `Not access to order by field 'peLastSyncAt'.`

The fix does not open the field. A post-fix control request using `orderBy=peLastSyncAt` still returned HTTP `400` for Sales Manager.

## 6. Files Changed

- `deployment/provisioning/phase3b07_provision_operations_dashboards.php`
- `crm-extension/manifest.json`
- `crm-extension/tests/test_extension_skeleton.py`
- `deployment/prospecting-extension-1.7.1-alpha.zip`
- `deployment/prospecting-extension-1.7.1-alpha.zip.sha256`
- `docs/PHASE3B07_PRODUCTION_READINESS_OPERATIONS_REPORT.md`
- `docs/PHASE3B07_1_LOCAL_RUNTIME_RECOVERY_REPORT.md`
- `docs/PHASE3B07_2_DASHBOARD_ACL_COMPATIBILITY_FIX_REPORT.md`

## 7. Configuration Before / After

| Item | Before | After |
| --- | --- | --- |
| Sync Issues order | `peLastSyncAt DESC` | `modifiedAt DESC` |
| Sync Issues filter | `peSyncFailed` | `peSyncFailed` unchanged |
| Sales Manager Evidence/Feedback dashlets | Provisioned but unavailable by entity ACL | Omitted only from Manager layout/options |
| Admin Evidence/Feedback dashlets | Provisioned | Retained |
| Sales User Evidence/Feedback dashlets | Provisioned | Retained |
| Persisted B07 options | Overwritten individually, stale entries possible | Owned `phase3b07-*` options cleared and rebuilt idempotently |

`modifiedAt DESC` was selected because it is readable and sortable for Sales Manager, keeps recently changed sync problems first, does not reveal technical sync details, and does not change filter membership.

## 8. ACL Preservation Verification

Database verification after installation:

| Role | `peLastSyncAt.read` | `peLastSyncAt.edit` |
| --- | --- | --- |
| Sales Manager | `no` | `no` |
| Sales User | `no` | `no` |

Sales Manager still has Lead `read=team`. No ACL provisioning script or Role record was changed. Admin retains full technical diagnostic access.

## 9. Static Test Results

| Check | Result |
| --- | --- |
| Extension tests | `35 PASS` |
| Connector regression | `58 PASS` |
| JSON parse and duplicate keys | `47` files, `0` errors |
| Installed Prospecting PHP syntax | PASS |
| Python compile | PASS |

Tests assert that canonical Sync Issues provisioning uses `modifiedAt`, contains no `peLastSyncAt`, retains the hidden field in role ACL source, preserves dashlet definitions, and applies the Manager-only compatible layout difference.

## 10. Runtime Verification

- Installed extension: `Chitu Prospecting Integration 1.7.1-alpha`.
- Rebuild: PASS.
- Cache clear: PASS.
- Canonical Dashboard reprovisioning: PASS for Admin, Sales Manager, and Sales User.
- `espocrm`: healthy.
- `espocrm-daemon`: healthy and stable.
- `espocrm-cron`: running.
- `bin/command app-check`: Migration, Database, maintenance state, and Cron all PASS.

## 11. API Verification

Sales Manager real API verification used the Dashboard's actual semantics:

- Entity: Lead.
- Primary filter: `peSyncFailed`.
- Ordering: `modifiedAt DESC`.
- Result: HTTP `200`; legal empty result (`total=0`).
- No forbidden field, unknown attribute, or invalid order error.

The browser access log independently recorded `manager_test` requesting the same filter and `orderBy=modifiedAt`, returning HTTP `200`. Admin and Sales User browser requests also returned `200` with the same ordering.

## 12. Sales Manager Browser Verification

PASS.

- Prospecting Operations loaded fully.
- Sync Issues showed a legal `No Data` state.
- No `peLastSyncAt` permission error.
- No API error, blank unavailable dashlet, infinite loading, modal error, internal filter key, or browser console error.
- Business-facing labels remained readable.

Sales Manager lacks ResearchEvidence and SalesFeedback entity ACL. The provisioning now omits only those two unavailable related-entity dashlets from Manager while retaining the rest of the formal Dashboard.

## 13. Admin Regression Verification

PASS.

- Prospecting Operations loaded without error.
- Sync Issues used `modifiedAt` and returned HTTP `200`.
- Recent Research Evidence and Recent Sales Feedback remained installed and rendered legal empty states.
- Admin technical diagnostic capability was preserved.

## 14. Sales User Regression Verification

PASS.

- Prospecting Operations loaded without Dashboard or console error.
- Sync Issues rendered a legal empty state.
- Recent Evidence and Feedback dashlets remained available under the existing `own` entity ACL.
- No technical field or internal `pe*` key was displayed.
- Field ACL was not expanded.

## 15. Package and SHA-256

- ZIP: `deployment/prospecting-extension-1.7.1-alpha.zip`.
- Manifest version: `1.7.1-alpha`.
- ZIP entries: `100`.
- SHA-256 file: `deployment/prospecting-extension-1.7.1-alpha.zip.sha256`.
- Expected/calculated SHA-256: `564091446761B4F0D4D330416AB28AA16C7AF704B1DC4C8CE2744C3CDAF5962F`.
- Existing `1.7.0-alpha` artifacts were not overwritten.

## 16. Cleanup Verification

No B07.2 synthetic records, API identity, temporary Dashboard, or other temporary artifact was required.

| Marker | Count |
| --- | ---: |
| Lead | 0 |
| ResearchEvidence | 0 |
| SalesFeedback | 0 |
| Task | 0 |
| Temporary identity | 0 |
| Opportunity | 0 |

No Opportunity was created and no email was sent.

## 17. Remaining Limitations

No remaining Phase3B07.2 acceptance blocker was found. The Manager-specific omission of two entity-inaccessible dashlets is an intentional ACL-compatible Dashboard configuration, not a hidden failure or ACL relaxation.

## 18. Revised Phase3B07 Verdict

The original Phase3B07 FAIL and Phase3B07.1 FAIL records remain in their historical sections. Phase3B07.2 fixed the final Dashboard ACL blocker and all required acceptance gates now pass.

**PHASE3B07_2 STATUS: PASS**

**PHASE3B07 STATUS: PASS**

No Phase3B08 work was started.
