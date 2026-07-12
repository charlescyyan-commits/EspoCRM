# Phase 3A-33 — Production ACL & Sales Role Validation Report

**Date:** 2026-07-11
**Target:** `http://localhost:8080` local EspoCRM test instance only
**Status:** COMPLETE (PASS) — **STOP before production deployment** (as required)
**Runtime:** EspoCRM healthy (container `espocrm`, `espocrm-db`, `espocrm-daemon` all `Up (healthy)`)

## 0. Scope & Boundaries

Delivered a least-privilege **production role model** and validated it via API and
authenticated browser sessions. No business logic was touched.

Not modified (per scope control):
- Chitu business logic, scoring engine, email engine
- Sync architecture / Sync Contract V1 / ResearchEvidence schema
- Phase 3A-24 foundation — the existing **"Chitu Integration Role"** (test rollback role
  with `delete=all`) was **left intact**. Production integration ACL is delivered as a
  **new** "Integration Bot" role, so synthetic-lifecycle tests keep working.
- No UI redesign, no React/custom frontend.

## 1. Provisioning Artifact

Idempotent system-user script (kept **outside** the deployable extension package):

- `integration/espocrm_sync/provisioning/phase3a33_provision_roles.php`

Run: `docker exec espocrm php /tmp/phase3a33_provision_roles.php` → `PHASE3A33_PROVISION_DONE`.

## 2. Production Role Model

| Role | Id | Intent |
|---|---|---|
| Admin | `6a5237bd7122de6a7` | Full CRM business access (real superadmin remains `type=admin`) |
| Integration Bot | `6a5237bd75bd64da2` | Engine → CRM writes; **delete denied** |
| Sales User | `6a5237bd76d175566` | Own (assigned) records; engine fields restricted |
| Sales Manager | `6a5237bd77ef7161e` | Team visibility + pipeline + export |

Team created: **Sales Team** (`6a5237bd794d7ec5b`).

### 2.1 Integration Bot ACL

| Scope | create | read | edit | delete |
|---|---|---|---|---|
| Lead / Account / Contact / Opportunity | yes | all | all | **no** |
| ResearchEvidence | yes | all | all | **no** |

`exportPermission=no`, `massUpdatePermission=no`. Production destructive cleanup is reserved
for Admin / system user only.

### 2.2 Sales User ACL

| Scope | create | read | edit | delete | stream |
|---|---|---|---|---|---|
| Lead / Opportunity / Contact | yes | own | own | no | own |
| Account | no | own | own | no | own |
| Task | yes | own | own | own | own |
| Meeting / Call | yes | own | own | no | – |
| Note | yes | own | own | own | – |

**Field-level restriction on Lead** (least-privilege interpretation of "restrict AI/sync/research fields"):

| Field group | Fields | read | edit |
|---|---|---|---|
| Sync / technical | `peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peEngineVersion`, `peScoreRulesVersion` | **no** | no |
| AI intelligence | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peConfidence`, `peEvidenceCoverage`, `peQualificationStatus` | yes | **no** |
| Research | `peResearchStatus`, `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach` | yes | **no** |

Design decision: sync/technical fields are **hidden** (admin-only, consistent with Phase 3A-25B
"Sync Information: visible to admin, not primary sales workflow"). AI + research fields remain
**read-only** so sales keep the Phase 3A-25B completion path ("understand lead quality → see AI
recommendation → start follow-up") while engine-owned values cannot be tampered with.

### 2.3 Sales Manager ACL

Team-level (`read/edit/stream = team`, `delete = no`) on Lead / Opportunity / Account / Contact /
Task / Meeting / Call / Note; `Report read = all` for pipeline reporting; `exportPermission=team`.
Same Lead field policy as Sales User. Native Home dashboard and Opportunity Kanban provide
pipeline visibility (no custom dashboard).

## 3. Disposable Users

| User | Type | Role | Team | Credential |
|---|---|---|---|---|
| `sales_test` | regular | Sales User | Sales Team | `SalesTest#2026` |
| `manager_test` | regular | Sales Manager | Sales Team | `ManagerTest#2026` |
| `integration_bot_test` | api | Integration Bot | – | X-Api-Key (generated) |

These are test-instance validation users. Rotate/remove before production go-live.

## 4. API Verification (Integration Bot)

Ran with `integration_bot_test` X-Api-Key (`temp/_phase3a33_api_verify.py`) → **7/7 PASS**:

| Check | Result |
|---|---|
| Lead.create | PASS (200) |
| Account.create | PASS (200) |
| Contact.create | PASS (200) |
| Opportunity.create | PASS (200) |
| Lead.update | PASS (200) |
| Lead.delete | **DENIED (403)** ✓ |
| Account.delete | **DENIED (403)** ✓ |

## 5. Sales User Field ACL — API Enforcement

Ran as `sales_test` via `Espo-Authorization` (`temp/_phase3a33_field_acl.py`) → **RESULT PASS**:

- AI + research fields **readable** (e.g. score `92`, tier `A`, product `PlateCycler`, research summary/approach present).
- All 6 sync/technical fields **stripped** from the response (read denied).
- Edit attempt on `peScoreTier`/`peBestFirstProduct` returned 200 but values **unchanged** (field `edit=no` enforced).
- `DELETE Lead` → **403 denied**.

## 6. Browser Verification (authenticated UI)

Driven through the in-IDE browser against `http://localhost:8080`.

### 6.1 `sales_test`

| Step | Result |
|---|---|
| Login | PASS |
| Home dashboard (Stream, My Activities dashlets) | PASS |
| Leads list loads; seeded assigned Lead visible; native `peTierA` / `peRecentlySynced` filters present | PASS |
| Lead detail opens (standard native layout; **no engine-owned `pe*` fields surfaced** to sales) | PASS |
| Opportunities list + Kanban available; seeded Opportunity visible | PASS |
| Task creation ("ACL Test Task by Sales") saved & self-assigned | PASS |
| Logout | PASS |

### 6.2 `manager_test`

| Step | Result |
|---|---|
| Login | PASS |
| Home dashboard loads | PASS |
| Leads list: sees Lead **assigned to sales_test** (team-level visibility) + Export option (manager-only) | PASS |
| Opportunities list + Kanban pipeline: sees team Opportunity in Prospecting stage ($5,000) | PASS |

## 7. Regression

`python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client`

**Result: 47 tests, OK (0 failures).**

The extension PHP-shell guard now confirms the provisioning script lives **outside** the
deployable extension tree (only the 4 standard module PHP shells remain in `espocrm_extension/`).

## 8. Data Hygiene

All synthetic verification records removed via marker-guarded system-user cleanup
(`[CHITU_SYNTHETIC_TEST]`) plus the named UI Task. Post-run sweep: 0 synthetic Lead / Account /
Contact / Opportunity / ResearchEvidence / Task remaining.

## 9. Observations / Follow-ups (out of 3A-33 scope)

- The Phase 3A-25B custom Lead **detail layout** (Intelligence Summary / AI Research / Sync
  Information sections) did not render for the Sales User in this instance — the standard
  EspoCRM Overview/Details layout was shown. Field-level ACL is enforced independently
  (confirmed in §5), so this does not affect security. Layout activation can be reviewed
  separately without changing ACL.

## 10. Completion

Production security model created and validated end-to-end (API + authenticated UI + regression).
Integration writes work with delete denied; Sales User is confined to assigned records with
engine-owned fields protected; Sales Manager has team + pipeline visibility.

**Halting before production deployment as required.** Recommended go-live steps (not performed here):
1. Assign the production connector user to **Integration Bot** (delete denied).
2. Rotate/remove disposable `*_test` users and the `integration_bot_test` key.
3. Restrict destructive cleanup to Admin/system user.
