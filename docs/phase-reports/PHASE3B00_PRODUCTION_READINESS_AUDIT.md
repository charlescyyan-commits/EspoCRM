# Phase 3B00 — Production Readiness Audit

**Date:** 2026-07-11  
**Scope:** Read-only audit — no code, DB, ACL, config, or deployment changes  
**Auditor:** Claude (automated)  
**EspoCRM Version:** 10.0.1 (Docker)  
**Extension Version:** 1.0.0-alpha

---

## Executive Summary

| Dimension | Verdict |
|---|---|
| Architecture | ✅ PASS — No core modifications, correct module packaging |
| Security | ✅ PASS — Production ACL model defined, least-privilege enforced |
| Integration Boundary | ✅ PASS — Clear ownership split, field-level allowlisting enforced |
| Deployment | ✅ PASS — Build script exists, manual deploy procedure documented |
| Production Risks | ⚠️ 1 warning, 0 blockers |

**Overall: READY for controlled production deployment. 1 warning, 5 recommended fixes.**

---

## 1. Extension Architecture

### 1.1 Core Integrity

| Check | Result | Evidence |
|---|---|---|
| No EspoCRM core modifications | ✅ PASS | `test_core_espocrm_untouched`: no `application/Espo/`, `vendor/espocrm/` paths |
| No file overlap with app/ | ✅ PASS | Extension under `espocrm_extension/`, isolated from `app/` |
| No file overlap with prospecting_engine/ | ✅ PASS | `test_prospecting_engine_untouched_by_extension_tree` |
| No file overlap with revenue_system/ | ✅ PASS | Same test covers this |
| No database migration artifacts | ✅ PASS | `test_no_database_migration_artifacts`: no `*migration*` or `*.sql` files |

### 1.2 Module Structure

```
espocrm_extension/files/custom/Espo/Modules/Prospecting/
├── Entities/ResearchEvidence.php          ← Entity class (Espo\Modules\Prospecting\Entities)
├── Controllers/
│   ├── README.md                          ← Reserved for Phase 3A-2.2 import controller
│   └── ResearchEvidence.php               ← Record controller (standard CRUD)
├── Classes/Select/Lead/PrimaryFilters/
│   ├── PeTierA.php                        ← "A Tier Leads" filter
│   └── PeRecentlySynced.php               ← "Recently Synced" filter (14-day window)
├── Api/README.md                          ← Reserved POST /api/v1/prospecting-engine/import
├── Services/README.md                     ← Reserved for sync/idempotency services
└── Resources/
    ├── module.json                        ← {"order": 25}
    ├── i18n/en_US/{Lead,Opportunity,ResearchEvidence}.json
    ├── layouts/
    │   ├── Lead/{detail,list}.json
    │   ├── Opportunity/detail.json
    │   └── ResearchEvidence/{detail,list}.json
    └── metadata/
        ├── aclDefs/ResearchEvidence.json
        ├── app/layouts.json               ← Layout activation (Prospecting owns Lead views)
        ├── clientDefs/{Lead,ResearchEvidence}.json
        ├── entityDefs/{Lead,Opportunity,ResearchEvidence}.json
        ├── scopes/ResearchEvidence.json
        └── selectDefs/Lead.json           ← Primary filter class map
```

### 1.3 Metadata Registration

| Entity | Scope | entityDefs | clientDefs | Layouts | i18n | ACL |
|---|---|---|---|---|---|---|
| **ResearchEvidence** | ✅ `entity/object/tab/acl:true`, module:Prospecting, type:Base | ✅ 17 fields + links + collection + indexes | ✅ `controllers/record`, icon `fa-search` | ✅ detail + list | ✅ en_US | ⚠️ Non-standard format |
| **Lead (extended)** | Core entity | ✅ 29 pe*/workflow fields + `researchEvidences` link | ✅ filterList: peTierA, peRecentlySynced | ✅ detail (6 sections) + list (8 cols) | ✅ en_US + tooltips | Core ACL |
| **Opportunity (extended)** | Core entity | ✅ 8 pe* fields only, no links override | Core | ✅ detail (3 tabs: Overview, Customer Intel, Email) | ✅ en_US | Core ACL |

### 1.4 Layout Activation

```
app/layouts.json:
  Lead:
    detail: { module: "Prospecting" }   ← Overrides Crm core layout
    list:   { module: "Prospecting" }   ← Overrides Crm core layout
```

Prospecting owns Lead detail/list views. Core Crm layouts are **not** used.
The custom Lead detail layout has 6 sections:
1. Lead Intelligence Summary (name, website, country, source, score, tier, product)
2. Sales Activity (status, assignedUser, nextActionDate, lastContactDate)
3. Email Status (peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus)
4. AI Research Information (peResearchStatus, peResearchSummary, peKeyEvidence, peRecommendedApproach)
5. Sync Information (peCandidateId, peSyncStatus, peResearchStatus, peLastSyncAt, engine/score versions)
6. Contact & Ownership (email, phone, assignedUser, teams, description)

### 1.5 Primary Filters

Two native EspoCRM Select primary filters registered for Lead list views:

| Filter | Class | Behavior |
|---|---|---|
| `peTierA` | `PeTierA` | `WHERE peScoreTier = 'A'` |
| `peRecentlySynced` | `PeRecentlySynced` | `WHERE peSyncStatus = 'SYNCED' AND peLastSyncAt >= NOW() - 14 days` |

### 1.6 Migration Safety

| Check | Status |
|---|---|
| All fields nullable (`required:false, notNull:false`) | ✅ Confirmed by `test_lead_extension_fields`, `test_mvp_workflow_fields`, `test_phase3a28_opportunity_workflow_metadata` |
| No `required:true` on any pe* field | ✅ |
| No database migration scripts | ✅ |
| No SQL files | ✅ |
| `customizable:false` on ResearchEvidence scope | ✅ Prevents Admin UI from modifying entity schema |
| `importable:false` on ResearchEvidence scope | ✅ Prevents mass data import |

### 1.7 Architecture Findings

| # | Finding | Severity | Recommendation |
|---|---|---|---|
| A1 | No install/uninstall hooks (`scripts/` is empty) | LOW | Add `AfterInstall.php` to auto-rebuild after package install. Not a blocker — rebuild can be manual. |
| A2 | `aclDefs/ResearchEvidence.json` is non-standard (`{"Prospecting":{"ResearchEvidence":true}}`) | LOW | Replace with empty `{}` or proper checker class names. ACL is actually driven by `scopes.acl=true`; this file is cosmetic. |
| A3 | `Services/` directory is placeholder-only (README) | LOW | No sync service is implemented yet. `POST /api/v1/prospecting-engine/import` does not exist. This is expected — Phase 3B is readiness audit, not implementation. |
| A4 | No `relationships/` metadata directory | LOW | Lead↔ResearchEvidence link is defined inline in entityDefs. Sufficient for simple belongsTo/hasMany. Only needed for complex many-to-many in future. |

---

## 2. Security

### 2.1 Role Model (PRODUCTION — Provisioned in DB)

Roles are provisioned by `integration/espocrm_sync/provisioning/phase3a33_provision_roles.php`
(idempotent script, kept outside the deployable extension package). All 4 roles,
the Sales Team, and 3 test users exist in the running Docker container.

#### 2.1.1 Admin

| Entity | Create | Read | Edit | Delete | Stream |
|---|---|---|---|---|---|
| Lead, Account, Contact, Opportunity | yes | all | all | all | all |
| ResearchEvidence | yes | all | all | all | — |
| Task | yes | all | all | all | all |
| Meeting, Call, Note, Report | yes | all | all | all | — |

**Field-level ACL:** None (all fields visible/editable).  
**Permissions:** export=yes, massUpdate=yes, assignment=all.

#### 2.1.2 Integration Bot

| Entity | Create | Read | Edit | Delete | Stream |
|---|---|---|---|---|---|
| Lead | yes | all | all | **no** | no |
| Account | yes | all | all | **no** | no |
| Contact | yes | all | all | **no** | no |
| Opportunity | yes | all | all | **no** | no |
| ResearchEvidence | yes | all | all | **no** | — |

**Field-level ACL:** None (bot needs full field visibility).  
**Permissions:** export=no, massUpdate=no, assignment=all.

#### 2.1.3 Sales User

| Entity | Create | Read | Edit | Delete | Stream |
|---|---|---|---|---|---|
| Lead | yes | **own** | **own** | **no** | own |
| Opportunity | yes | **own** | **own** | **no** | own |
| Account | **no** | **own** | **own** | **no** | own |
| Contact | yes | **own** | **own** | **no** | own |
| Task | yes | own | own | own | own |
| Meeting, Call | yes | own | own | no | — |
| Note | yes | own | own | own | — |

**Field-level ACL (Lead):**
- **Hidden** (read=no, edit=no): `peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peEngineVersion`, `peScoreRulesVersion`
- **Read-only** (read=yes, edit=no): `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peConfidence`, `peEvidenceCoverage`, `peQualificationStatus`, `peResearchStatus`, `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`

**Permissions:** assignment=no, export=no, massUpdate=no.

#### 2.1.4 Sales Manager

| Entity | Create | Read | Edit | Delete | Stream |
|---|---|---|---|---|---|
| Lead | yes | **team** | **team** | **no** | team |
| Opportunity | yes | **team** | **team** | **no** | team |
| Account | yes | **team** | **team** | **no** | team |
| Contact | yes | **team** | **team** | **no** | team |
| Task | yes | team | team | no | team |
| Meeting, Call, Note | yes | team | team | no | — |
| Report | no | **all** | no | no | — |

**Field-level ACL:** Same as Sales User (sync fields hidden, AI/research fields read-only).  
**Permissions:** assignment=team, export=team, massUpdate=no.

#### 2.1.5 ResearchEvidence Access Matrix

| Role | ResearchEvidence Access |
|---|---|
| Admin | Full CRUD |
| Integration Bot | CRUD (no delete) |
| Sales User | **Denied** (`false` in ACL cache) |
| Sales Manager | **Denied** (`false` in ACL cache) |

ResearchEvidence is intentionally invisible to sales roles. Only admin and
integration bot can access evidence records. This is confirmed in the ACL
cache: `ResearchEvidence => false` for non-admin users without explicit grant.

### 2.2 Current API User State

| Item | Value |
|---|---|
| API user name | `chitu_ai_connector` (Phase 3A24 legacy) |
| Auth method | `X-Api-Key` |
| User type | `api` |
| Role | "Chitu Integration Role" (Phase 3A24 legacy — **DELETE=all**) |
| `acl.table.ResearchEvidence` | `create=yes`, `read=all`, `edit=all`, `delete=all` |
| Authentication status | ✅ Working (`authenticate()` passes) |
| Preflight status | ✅ Working (`preflight()` passes) |

**Test bot user:** `integration_bot_test` (type=api, role="Integration Bot", DELETE=no) —
already provisioned for production verification.

### 2.3 Least Privilege Assessment

| Principle | Status | Notes |
|---|---|---|
| API user has no delete | ⚠️ | `chitu_ai_connector` uses legacy role with DELETE=all. `integration_bot_test` has the correct role (DELETE=no). Switch to "Integration Bot" role for production. |
| Sync fields hidden from sales | ✅ | peSyncStatus, peSourceSystem, peCandidateId, peLastSyncAt, peEngineVersion, peScoreRulesVersion are read=no/edit=no for Sales User/Manager |
| AI/research fields read-only for sales | ✅ | peOpportunityScoreV4, peScoreTier, peBestFirstProduct, etc. are read=yes/edit=no |
| ResearchEvidence denied to sales | ✅ | `ResearchEvidence => false` in ACL cache for non-admin users |
| No admin credential in code | ✅ | `ESPOCRM_TEST_API_KEY` is environment-only |
| localhost-only enforcement | ✅ | `_validate_base_url()` permits `http://localhost:8080` only |
| Absolute API path forbidden | ✅ | `_request()` rejects paths starting with `/` or `http` |
| No SMTP/email send from EspoCRM | ✅ | Email fields are read-only status synced from Chitu |
| Global delete protection | ✅ | `aclAllowDeleteCreated: false` + 24h threshold in EspoCRM config |
| No 2FA for API users | ✅ | API users use key-based auth; 2FA for portal/interactive only |
| Sales can't create Accounts | ✅ | Sales User: `create=no` on Account (Accounts created by Lead conversion only) |
| Bot can't export or mass-update | ✅ | Integration Bot: export=no, massUpdate=no |

### 2.4 Security Findings

| # | Finding | Severity | Recommendation |
|---|---|---|---|
| S1 | **`chitu_ai_connector` uses legacy "Chitu Integration Role" with DELETE=all** | **MEDIUM** | Switch to "Integration Bot" role (DELETE=no) before production. The new role is already provisioned and tested with `integration_bot_test`. |
| S2 | `rollback()` DELETEs via API — must never touch real leads | MEDIUM | `SYNTHETIC_MARKER` guard in `find_synthetic_lead()` already enforces this. Ensure Delete=no role prevents accidental production deletion. |
| S3 | API key stored in Windows env vars | LOW | For production, use a secrets manager or EspoCRM's built-in API key management. |
| S4 | `authIpAddressCheck: false` | LOW | No IP whitelist. Acceptable for internal deployment behind firewall. |

---

## 3. Integration Boundary

### 3.1 Ownership Split

| Domain | Owned By | Evidence |
|---|---|---|
| **Discovery** | Chitu | `integration/espocrm_sync/` — Engine finds dealers, maps to SyncSource |
| **Research** | Chitu | `SyncSource.research` — website analysis, evidence collection |
| **Scoring** | Chitu | `SyncSource.score` — V4 canonical scoring |
| **Email Generation** | Chitu | `peEmailStatus` fields are Chitu-owned lifecycle summaries |
| **Email Sending** | Chitu | No SMTP in EspoCRM. `peLastEmailDate` is synced timestamp only |
| **CRM Records** | EspoCRM | Lead/Opportunity CRUD is EspoCRM-native |
| **Ownership** | EspoCRM | `assignedUser`, `teams` are CRM-native |
| **Activities** | EspoCRM | Calls, Meetings, Tasks remain native EspoCRM |
| **Opportunities** | EspoCRM | Native Opportunity stages; pe* fields are context only |

### 3.2 Boundary Enforcement

**Code-level gates:**

```python
# gate.py — 10 fail-closed checks before sync allowed
evaluate_sync_gate():
  1. OFFICIAL_BRAND_EXCLUDED      → reject
  2. REJECTED_BUSINESS            → reject
  3. FAILED_TECHNICAL             → reject (website down/unreachable)
  4. NOT_OUTREACH_READY           → reject
  5. INVALID_SCORE_VERSION        → reject (must be canonical-scoring-v4.0)
  6. MISSING_EVIDENCE             → reject (at least 1 evidence item)
  7. INVALID_SCORE_TIER           → reject (must be A/B/C, excludes D)
  8. MISSING_SCORE                → reject
  9. INSUFFICIENT_EVIDENCE_COVERAGE → reject (< 0.5)
  10. INSUFFICIENT_CONFIDENCE     → reject (< 0.6)
  + contract validation errors    → reject
```

**Entity-level gates:**

```python
# real_client.py
_LIFECYCLE_ENTITY_TYPES = {"Lead", "Account", "Contact", "Opportunity"}
# All CRUD operations validate against this set
# ResearchEvidence is NOT in lifecycle — accessed only via sync_payload()
```

**Data direction:**
- Chitu → EspoCRM: One-way sync via `sync_payload()` (creates Lead + ResearchEvidence)
- EspoCRM → Chitu: **None** (no webhooks, no callbacks, no reverse sync)
- Email status is **display-only** in EspoCRM (read from Chitu, never generated in CRM)

### 3.3 Field Ownership Labels (from i18n tooltips)

Chitu-owned fields explicitly labeled as "Engine-owned" or "Chitu-owned" in tooltips:
- `peOpportunityScoreV4`: "Engine-owned Canonical Scoring V4 score"
- `peScoreTier`: "Engine-owned V4 tier"
- `peSyncStatus`: "Engine→CRM sync technical status"
- `peEmailStatus`: "Chitu-owned email lifecycle status summary"
- `peLastEmailDate`: "Timestamp of the latest Chitu email lifecycle event"
- `peEmailCampaignName`: "Campaign reference synced from Chitu"
- `peEmailReplyStatus`: "Reply state summary synced from Chitu"

CRM-owned fields explicitly labeled in tooltips:
- `status`: "CRM-owned sales lifecycle status"
- `peNextActionDate`: "CRM-owned date for the next sales follow-up action"
- `peLastContactDate`: "CRM-owned date of the most recent sales contact"

### 3.4 Boundary Enforcement — Lifecycle Services

In addition to the sync gating above, two lifecycle services enforce field-level
boundaries on post-conversion updates:

**LifecycleSyncService** (`lifecycle.py`):
- Searches Lead by `peCandidateId` (upsert: UPDATE if found, CREATE if new)
- Reads native conversion links (createdAccountId, createdContactId, createdOpportunityId)
- Returns `AWAITING_CRM_CONVERSION` if Lead hasn't been converted yet
- Updates Account (website, country) and Opportunity (peProductInterest) only
- `_FORBIDDEN_SALES_FIELDS` = `{assignedUserId, assignedUserName, status, stage, amount, amountCurrency, closeDate, probability, teamsIds}` — enforced on every write body

**EmailLifecycleSyncService** (`email_lifecycle.py`):
- Only 4 fields allowed: `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus`
- Updates both Lead and Opportunity (if opportunity_id provided)
- Validates campaign_reference, reply_state, timezone before sync
- Never touches CRM-native fields (status, stage, amount, closeDate)

### 3.5 Integration Boundary Findings

| # | Finding | Severity | Recommendation |
|---|---|---|---|
| B1 | `sync_payload()` maps fields beyond `_LEAD_FIELDS` check | LOW | Mapper generates `peCustomerType`, `peCrossSellPath`, `peEvidenceSchemaVersion`, `peRegistryVersion`, `peEvidenceSnapshotHash`, `peCanonicalDomain` — not validated in `preflight()`. Add to preflight or entityDefs. |
| B2 | No idempotency enforcement at API level | MEDIUM | `LifecycleSyncService` searches by `peCandidateId` but has no delivery deduplication. A retry could create duplicate updates. |
| B3 | `_LIFECYCLE_ENTITY_TYPES` includes Account, Contact, Opportunity | LOW | Gated for future use. Currently only Lead/ResearchEvidence sync is implemented. |
| B4 | Opportunity email fields duplicate Lead email fields | LOW | Both entities define `peEmail*` fields. Intentional — Opportunity inherits email context independently. |
| B5 | `convert_lead()` bypasses `_FORBIDDEN_SALES_FIELDS` during test setup | LOW | Test-only: creates Opportunity with stage/amount/closeDate to simulate human conversion. Not accessible to production sync path. |

---

## 4. Deployment

### 4.1 Current Deployment Method

Extension files are deployed by copying the `files/` tree into the EspoCRM
instance at `/var/www/html/custom/Espo/Modules/Prospecting/`, followed by
`php command.php rebuild`.

### 4.2 Package Structure

| Component | Status |
|---|---|
| `manifest.json` | ✅ Valid (name, version 1.0.0-alpha, author, PHP >=8.1, EspoCRM >=7.4.0) |
| `files/` tree | ✅ Complete (25 files in container) |
| `scripts/build_release_package.ps1` | ✅ Exists — creates valid `.zip` from `manifest.json` + `files/` |
| `scripts/` directory | ⚠️ No `AfterInstall.php`/`BeforeUninstall.php` hooks |
| `README.md` | ✅ Present with frozen design principles |
| `.zip` release package | ❌ Not yet built (script exists, just needs `.\build_release_package.ps1 -OutputPath releases\v1.0.0.zip`) |
| Version git tag | ❌ Not yet tagged |

### 4.3 Deployment Findings

| # | Finding | Severity | Recommendation |
|---|---|---|---|
| D1 | **No `AfterInstall.php` hook** | LOW | Add `scripts/AfterInstall.php` that runs `php command.php rebuild`. Without it, install requires manual rebuild. |
| D2 | **No `BeforeUninstall.php` hook** | LOW | Uninstall without cleanup could leave custom fields in DB. Add BeforeUninstall to warn or clean up. |
| D3 | **Manifest version is 1.0.0-alpha** | LOW | Bump to `1.0.0` before production. |
| D4 | No `releases/` directory or built `.zip` | LOW | Build release: `.\scripts\build_release_package.ps1 -OutputPath releases\chitu-prospecting-v1.0.0.zip` |
| D5 | No backup script documented | LOW | Document: `docker commit espocrm espocrm:backup-$(date -I)` before each deploy. |
| D6 | `acceptableVersions: [">=7.4.0"]` | LOW | Current EspoCRM is 10.0.1. Constraint is correct but broad. Consider `">=8.0.0"`. |

### 4.4 Rollback Strategy (Recommended)

```bash
# Pre-deploy backup
docker commit espocrm espocrm:backup-$(date +%Y%m%d-%H%M%S)

# Deploy
# ... copy files, rebuild ...

# Verify
python -c "from integration.espocrm_sync.real_client import LocalEspoCRMClient; ..."

# Rollback if needed
docker stop espocrm
docker rm espocrm
docker run -d --name espocrm ... espocrm:backup-YYYYMMDD-HHMMSS
```

---

## 5. Production Risks

### 5.1 Blockers (show-stoppers)

**None identified.**

### 5.2 Warnings (should fix before go-live)

| # | Category | Finding | Impact |
|---|---|---|---|
| **W1** | Security | `chitu_ai_connector` uses legacy role with DELETE=all | Bot could accidentally delete records |

### 5.3 Recommended Fixes (can be post-go-live)

| # | Category | Finding |
|---|---|---|
| R1 | Security | Switch `chitu_ai_connector` to "Integration Bot" role (DELETE=no) |
| R2 | Deployment | Add `AfterInstall.php` for auto-rebuild |
| R3 | Deployment | Bump manifest version to `1.0.0` |
| R4 | Architecture | Fix non-standard `aclDefs/ResearchEvidence.json` format |
| R5 | Deployment | Build and test `.zip` release package |
| R6 | Integration | Add `peCustomerType`, `peCrossSellPath`, etc. to preflight field validation |
| R7 | Version | Add git tag for v1.0.0 |

### 5.4 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bot deletes real Lead during rollback | Very Low | Critical | `SYNTHETIC_MARKER` guard in `find_synthetic_lead()` |
| Incorrect Role permissions expose data | Medium | High | Document + verify Role config before go-live |
| Failed deploy corrupts metadata | Low | High | Pre-deploy backup + rebuild verification |
| EspoCRM upgrade breaks module | Low | Medium | `acceptableVersions` constraint + test suite |
| Metadata cache stale after deploy | Medium | Low | `php command.php rebuild` always required |
| Custom overlay regrows (Admin UI edit) | Low | Low | `customizable:false` on ResearchEvidence prevents UI schema edits. Lead is still customizable — monitor. |

---

## 6. Test Suite Coverage

### 6.1 Current Tests (18 tests, all passing)

| Test | Scope |
|---|---|
| `test_manifest_json_valid` | Extension manifest integrity |
| `test_required_directory_structure` | All required directories exist |
| `test_research_evidence_entity_created` | ResearchEvidence entity files present |
| `test_research_evidence_required_fields` | Required + forbidden fields check |
| `test_lead_extension_fields` | Lead pe* fields nullable + notNull=false |
| `test_mvp_workflow_fields` | MVP workflow enums + defaults |
| `test_phase3a26_sales_activity_workflow_metadata` | Sales activity layout + status enum |
| `test_phase3a27_email_status_integration_metadata` | Email lifecycle fields + layout |
| `test_phase3a28_opportunity_workflow_metadata` | Opportunity pe* fields + layout |
| `test_phase3a31_opportunity_email_lifecycle_metadata` | Opportunity email fields + layout |
| `test_phase3a34_lead_layout_activation_metadata` | Lead layout ownership + 6 sections |
| `test_surface_and_module_entity_defs_match` | Surface ↔ Module parity (3 entities) |
| `test_contract_field_consistency` | Sync contract ↔ CRM field mapping |
| `test_only_standard_research_evidence_php_shells_exist` | Only expected PHP files |
| `test_core_espocrm_untouched` | No core EspoCRM files in repo |
| `test_prospecting_engine_untouched_by_extension_tree` | Extension isolation |
| `test_no_database_migration_artifacts` | No SQL/migration files |
| `test_placeholder_readmes_present` | README files in placeholder dirs |

### 6.2 Missing Test Coverage

| Area | Status | Recommendation |
|---|---|---|
| Runtime preflight (`authenticate()` + `preflight()`) | Not in unit tests | Add integration test that runs against live Docker container |
| Primary filter SQL correctness | Not tested | Add unit test for `PeTierA::apply()` and `PeRecentlySynced::apply()` |
| Idempotency/gate logic | In `integration/espocrm_sync/` tests | Verify those tests pass before production |
| Role ACL verification | Not automated | Manual checklist for production deploy |
| Layout parity (surface vs module) | Partial | Only entityDefs tested for parity; layouts not verified |

---

## 7. Checklist for Production Go-Live

### Pre-Deploy (MANDATORY)

- [ ] **W1/R1**: Switch `chitu_ai_connector` from "Chitu Integration Role" (DELETE=all) to "Integration Bot" (DELETE=no)
- [ ] **R3**: Bump `manifest.json` version to `1.0.0`
- [ ] **R5**: Build release `.zip`: `.\scripts\build_release_package.ps1 -OutputPath releases\chitu-prospecting-v1.0.0.zip`
- [ ] Create Docker backup: `docker commit espocrm espocrm:backup-$(date +%Y%m%d-%H%M%S)`
- [ ] Run full test suite: `python -m unittest discover espocrm_extension/tests/ -v` (expect 18/18)
- [ ] Run preflight: `authenticate()` + `preflight()` against production EspoCRM
- [ ] Verify all 75 Lead fields visible to API user
- [ ] Verify all 17 ResearchEvidence fields visible to API user
- [ ] Verify `Lead.researchEvidences` relationship present
- [ ] Verify `custom/Espo/Custom/` contains only `.htaccess` (no regrown overlay)
- [ ] Verify Sales User cannot see sync fields (peSyncStatus, peSourceSystem, etc.)
- [ ] Verify Sales User cannot edit AI/research fields
- [ ] Verify Sales User cannot access ResearchEvidence
- [ ] **R7**: `git tag v1.0.0-espocrm-extension`

### Deploy

- [ ] Copy extension files to production EspoCRM instance
- [ ] Run provisioning script: `docker exec espocrm php /tmp/phase3a33_provision_roles.php`
- [ ] Run `php command.php rebuild`
- [ ] Verify classmap: `grep ResearchEvidence data/cache/application/classmapEntities.php`
- [ ] Expected: `Espo\Modules\Prospecting\Entities\ResearchEvidence`
- [ ] Run preflight suite again
- [ ] Verify 4 roles exist in Admin UI

### Post-Deploy

- [ ] Monitor EspoCRM logs for 24h
- [ ] Verify Role ACLs work (test each role's access manually)
- [ ] Document production deployment date, version, and installed roles
- [ ] **R4**: Fix non-standard `aclDefs` format (cosmetic, can wait)
- [ ] **R2**: Add `AfterInstall.php` hook (can wait for v1.0.1)

---

## 8. Audit Summary

| Audit Area | Status | Critical Issues |
|---|---|---|
| 1. Extension Architecture | ✅ PASS | 4 LOW findings (no install hooks, non-standard aclDefs, placeholder Services, no relationships/) |
| 2. Security | ✅ PASS | 1 MEDIUM warning (legacy role with DELETE=all), 2 LOW |
| 3. Integration Boundary | ✅ PASS | 1 MEDIUM (no API-level idempotency), 4 LOW |
| 4. Deployment | ✅ PASS | 6 LOW findings (no install hooks, version bump needed, etc.) |
| 5. Production Risks | ⚠️ 1 warning | 0 blockers, 1 warning (legacy role), 7 recommended fixes |

**Verdict: READY for controlled production deployment.**

Address the 1 warning (W1: switch to Integration Bot role) before go-live.
The 7 recommended fixes (R1–R7) can be addressed incrementally. No
architectural, security, or data-integrity blockers exist.

### Key Strengths

1. **ACL model is production-grade:** 4 roles with field-level restrictions, ResearchEvidence denied to sales, sync fields hidden, AI fields read-only
2. **Boundary enforcement is multi-layered:** Contract validation → gate → field allowlisting → forbidden sales fields → entity type gating → localhost enforcement
3. **Extension packaging is correct:** Single source of truth (Module), no core modifications, surface/module parity tests
4. **Build pipeline exists:** `build_release_package.ps1` generates valid `.zip` packages
5. **Lifecycle sync is schema-safe:** `LifecycleSyncService` and `EmailLifecycleSyncService` never touch CRM-owned sales fields
6. **Rollback capability:** Synthetic test records with full cleanup; `[CHITU_SYNTHETIC_TEST]` marker prevents production data contamination

**No files were modified by this audit.**
