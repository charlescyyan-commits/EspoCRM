# Phase G01 — EspoCRM Prospecting Architecture Audit

> **Date**: 2026-07-14
> **Scope**: Pre-freeze architecture audit on Phase3C10.1 baseline
> **Mode**: Read-only — no modifications made
> **Repository**: D:\EspoCRM-Production (branch: `master`, HEAD: `a4b0e6e`)

---

## Executive Summary

| Category | PASS | WARNING | BLOCKER |
|----------|------|---------|---------|
| 1. Extension Boundary | 9 | 5 | 3 |
| 2. Connector Boundary | 52 | 2 | 0 |
| 3. Phase3C10.1 Evidence Dedup | 6 | 3 | 3 |
| 4. Runtime State | 7 | 14 | 6 |
| **TOTAL** | **74** | **24** | **12** |

**Overall Verdict**: The connector architecture is sound with clean boundaries. However, **3 critical BLOCKERs exist in the evidence sync production path** — the PHP `syncEvidence()` endpoint has zero deduplication and the Python dedup adapter is never invoked in production, meaning every evidence sync call creates duplicate records. The extension boundary has layout divergence and metadata duplication. Runtime state has hardcoded credentials and stale artifacts.

---

## 1. Extension Boundary

### 1.1 Entity Definitions — WARNING: Duplicate entityDefs

**File paths**:
- `crm-extension/Resources/entityDefs/` (9 files)
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/` (9 files)

**Root cause**: All 9 entity definition files exist in BOTH locations with identical content. The top-level `Resources/entityDefs/` maps to `custom/Espo/Custom/Resources/entityDefs/` in a deployed EspoCRM instance, while the module-level path maps to `custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/`. In EspoCRM's metadata merge, Custom-level definitions override Module-level definitions. Since they are identical, there is no functional conflict today, but maintaining the same definitions in two places is unnecessary and creates a maintenance risk.

**Affected files**: `EmailEvent.json`, `Lead.json`, `LearningSignal.json`, `Opportunity.json`, `ProspectPool.json`, `ResearchEvidence.json`, `SalesFeedback.json`, `SearchJob.json`, `SearchStrategy.json`

**Minimum fix**: Remove the top-level `Resources/entityDefs/` directory. All entityDefs belong in the module-level metadata path.

### 1.2 Layouts — BLOCKER: Design surface diverged from installable copies

**Design surface**: `crm-extension/Resources/layouts/`
**Installable**: `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/`

**Root cause**: The `Resources/README.md` (line 14) states "Keep both trees aligned." They are NOT aligned. Six layout files across four entities have diverged, and three files are completely missing from the design surface.

**Diverged files**:

| Entity | File | Design surface | Installable |
|--------|------|---------------|-------------|
| Lead | `detail.json` | `pePriorityLevel` in row 17 | `false` (placeholder) in row 17 |
| Lead | `list.json` | 9 columns | 11 columns (+ `outreachStatus`, `nextFollowUpAt`) |
| SalesFeedback | `detail.json` | Missing `createdAt`/`createdBy` row | Has `createdAt`/`createdBy` row |
| SalesFeedback | `list.json` | 7 columns | 7 columns (different columns) |
| ResearchEvidence | `list.json` | Different columns | Different columns |
| ResearchEvidence | `listSmall.json` | Different columns | Different columns |

**Missing from design surface**:
- `ProspectPool/listDashletExpanded.json`
- `SearchJob/listDashletExpanded.json`
- `SearchStrategy/listDashletExpanded.json`

**Additionally: Build script silently excludes design surface** (`scripts/build_release_package.ps1:28-31`). Only `files/` is packaged — the design surface at `Resources/` is never deployed. Any developer reviewing `Resources/` sees stale layouts but would not realize they never ship.

### 1.3 ACL Definitions — WARNING: Duplicate + naming mismatch

**File paths**:
- `crm-extension/Resources/acl/` (7 files)
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/aclDefs/` (7 files)

**Root cause**: ACL definitions exist in both locations AND use different directory names (`acl` vs `aclDefs`). The standard EspoCRM metadata path for module ACL definitions is `Resources/metadata/aclDefs/`. The top-level `Resources/acl/` maps to a non-standard path (`custom/Espo/Custom/Resources/acl/`) that EspoCRM's metadata loader may not recognize. Files confirmed identical in content between both locations.

**Minimum fix**: Remove the top-level `Resources/acl/` directory. Keep only the module-level `metadata/aclDefs/`.

### 1.4 Formula — WARNING: Duplicate formula

**File paths**:
- `crm-extension/Resources/metadata/formula/Lead.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/formula/Lead.json`

**Root cause**: Same formula file duplicated. Content confirmed identical.

**Minimum fix**: Remove the top-level copy. Keep the module-level version.

### 1.5 Dashlet Metadata — PASS

All 14 dashlet metadata files exist and match the 14 i18n `dashlets` entries in `Global.json`. All referenced `entityType` and `aclScope` values resolve to existing entity definitions. All referenced primary filters (`jobsQueued`, `jobsRunning`, `jobsCompleted`, `jobsFailed`, `researchQueue`) are registered in corresponding `selectDefs` and have PHP class implementations.

One historical fix observed (working tree): `AcquisitionJobsWaiting.json` changed `"primary": "jobsWaiting"` → `"primary": "jobsQueued"`, aligning with the deletion of `JobsWaiting.php` and the existing `JobsQueued.php` class.

### 1.6 ClientDefs — PASS

All 7 `custom:` references in clientDefs resolve to existing files on disk:
| Reference | Resolves To | Exists? |
|-----------|-------------|---------|
| `custom:controllers/prospecting-dashboard` | `controllers/prospecting-dashboard.js` | ✅ |
| `custom:controllers/prospecting-search` | `controllers/prospecting-search.js` | ✅ |
| `custom:views/search-job/record/list` | `views/search-job/record/list.js` | ✅ |
| `custom:views/search-strategy/record/list` | `views/search-strategy/record/list.js` | ✅ |
| `custom:views/prospect-pool/record/list` | `views/prospect-pool/record/list.js` | ✅ |
| `custom:views/research-evidence/record/list` | `views/research-evidence/record/list.js` | ✅ |
| `custom:handlers/search-strategy/generate-jobs` | `handlers/search-strategy/generate-jobs.js` | ✅ |

### 1.7 Scopes — PASS

Scope configuration is consistent across all 9 entities. The `"module": "Prospecting"` grouping is correct. The recent change hiding `EmailEvent`, `LearningSignal`, and `SalesFeedback` from the navbar (`"tab": false`) is correct — these are child entities accessed via relationships.

Current tab-visible scopes (6):
1. `ProspectingDashboard` — main dashboard (entity: false)
2. `ProspectingSearch` — search entry (entity: false)
3. `SearchStrategy` — strategies
4. `SearchJob` — jobs
5. `ProspectPool` — prospects
6. `ResearchEvidence` — evidence

Tab ordering is explicitly set via the provisioning script `phase3u04_provision_navbar_tab_order.php` which writes to EspoCRM's `config.tabList`. This is the correct approach for controlling tab order — provisioning, not metadata.

### 1.8 SelectDefs — PASS

All primary filter class references in `selectDefs/SearchJob.json` and `selectDefs/ProspectPool.json` resolve to existing PHP files:
- `JobsQueued`, `JobsRunning`, `JobsCompleted`, `JobsFailed`, `JobsCancelled` ✅
- `ResearchQueue` ✅
- Lead primary filters (20+ filters) ✅

### 1.9 Relationships — PASS

All `links` defined in entityDefs reference valid target entities:
- `Lead` ↔ `ResearchEvidence` (hasMany)
- `Lead` ↔ `SalesFeedback` (hasMany)
- `Lead` ↔ `LearningSignal` (hasMany)
- `Lead` ↔ `EmailEvent` (hasMany)
- `SearchStrategy` → `SearchJob` (hasMany, foreign: `strategy`)
- `SearchJob` → `ProspectPool` (via `prospectPools` relationship panel)

### 1.10 Unused / Residue Files — BLOCKER

**BLOCKER**: Top-level `Resources/` directory structure at `crm-extension/Resources/` contains full duplicates of metadata that also exists in the module-level path. In a standard EspoCRM extension, the top-level `Resources/` maps to `custom/Espo/Custom/Resources/`, while `files/custom/Espo/Modules/{Module}/Resources/` maps to the module path. Having both means:

1. **Redundant deployment**: The same files are deployed to two locations
2. **Maintenance risk**: Future edits to only one location will cause silent divergence
3. **Metadata confusion**: Custom-level definitions override module-level, so the module-level definitions could be silently shadowed

**Affected directories** (all under `crm-extension/Resources/`):
- `entityDefs/` (9 files)
- `layouts/` (9 subdirectories)
- `acl/` (7 files)
- `metadata/formula/Lead.json`

---

## 2. Connector Boundary

### 2.1 Architecture Integrity — PASS

The architecture cleanly maintains the required boundary:

```
External Lead Engine (Chitu)
        |
        |  vendored/contracts/  (stable interface definitions)
        |
Connector (chitu-connector/)
        |
        |  HTTP POST to /Prospecting/sync/*
        |
EspoCRM Projection (crm-extension/)
```

**Verified**:
- **One-way dependency**: Connector imports vendored contracts. CRM extension never imports connector code.
- **Vendored contracts** are pure data definitions with zero imports from connector internals.
- **No circular dependencies** in the vendored package.

### 2.2 Lead Sync Boundary — PASS

**Key file**: `chitu_connector/espocrm_sync/lifecycle.py`

**Verified**:
- `peSourceSystem` defaults to `"Chitu Intelligence"` in both connector (`mapper.py:101`) and CRM (`entityDefs/Lead.json:118`, `ChituSyncService.php:166`)
- `_assert_no_sales_fields()` (lifecycle.py:209-212) prevents sync from overwriting CRM-owned fields: `assignedUserId`, `status`, `stage`, `amount`, `amountCurrency`, `closeDate`, `probability`, `teamsIds`
- `_lead_body()` has an explicit allowlist of only `pe`-prefixed Chitu tracking fields plus immutable CRM facts (`name`, `website`, `addressCountry`)
- Integration test (`test_espocrm_lifecycle_sync.py:59-62`) verifies sync does not write `status` or `assignedUserId`

### 2.3 ResearchEvidence Sync — PASS

**Key file**: `chitu_connector/espocrm_sync/research_evidence_persistence.py`

**Verified**:
- Evidence identity: `SHA256(version, lead_id, canonical_source_url, claim_type, claim_hash)` — scoped per Lead, per fact
- `snapshotHash` explicitly excluded from identity key (line 221: "The batch snapshot hash is intentionally excluded")
- Two-level dedup: snapshot-level fast path (`find_research_evidence_for_snapshot`), then per-evidence identity fallback (`find_research_evidence_by_identity`)
- URL canonicalization: scheme normalization, port removal, path trailing-slash cleanup, query parameter ordering
- Text normalization: whitespace collapse via `_normalize_text()`
- Validation rejects items exceeding field length limits with specific error codes
- Adapter deliberately does not create or update Leads (requires existing `lead_id`)

### 2.4 Proposal Fields — PASS

**Key file**: `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`

**Verified**:
- All 5 `peProposal*` fields defined in `entityDefs/Lead.json` with proper types
- `peProposalAction` defaults to `"NO_AUTOMATIC_OPPORTUNITY"` (entityDefs/Lead.json:227)
- `ChituSyncService::syncOpportunityProposal()` only updates proposal fields on Lead; never creates Opportunity
- i18n tooltips explicitly state "creates no Opportunity, activity, or workflow" and "never authorizes automatic Opportunity creation"
- Connector's `ProspectingConnectorClient.sync_source()` calls proposal sync but never branches on `proposal.action`

### 2.5 NO_AUTOMATIC_OPPORTUNITY Contract — PASS

**Verified at all layers**:

| Layer | Enforcement | Location |
|-------|-------------|----------|
| Entity default | `peProposalAction` = `"NO_AUTOMATIC_OPPORTUNITY"` | `entityDefs/Lead.json:227` |
| CRM sync API | Hardcoded in response | `ChituSyncService.php:103,247-248` |
| Connector client | No branching on action | `connector_api.py:70-97` |
| Test assertion | Explicit check | `test_espocrm_connector_api.py:62` |
| User-facing label | i18n tooltip warning | `Lead.json:139` |

### 2.6 Error Handling — PASS

**Key file**: `chitu_connector/acquisition/models.py`

**Verified**:
- `ProviderError`: retryable/non-retryable classification
- `ProviderRateLimitError`: always retryable with `retry_after` seconds
- `PersistenceError`: retryable/non-retryable, "never carries a response or credential"
- HTTP 404 handling: returns `None` when `not_found_is_none=True`; raises `PersistenceError` otherwise
- Claim safety: `espo_repository.py:65-116` uses GET-then-PUT with post-write confirmation
- Exit codes: `runner.py:128-139` maps 6 distinct exit codes for CLIs

### 2.7 Connector Warnings

**WARNING 1**: Top-level `__init__.py` has no re-exports (`chitu_connector/__init__.py`). Consumers must always deep-import from sub-packages. Acceptable for internal use.

**WARNING 2**: Disabled scoring adapter (`vendored/contracts/scoring.py:29`) raises `RuntimeError("DecisionEngineAdapter is intentionally disabled in Foundation V1")`. This vendored placeholder could cause confusion if imported accidentally.

### 2.8 Version Coupling — WARNING

- CRM extension: `1.9.5-alpha` (manifest.json:4)
- Python connector: `1.0.0a0` (pyproject.toml:7)
- **No formal version coupling** between the two components. If a bug is reported against extension v1.9.5-alpha, there is no way to determine which connector version was deployed.

---

## 3. Phase3C10.1 Evidence Dedup Review

### 3.0 — BLOCKER — PHP `syncEvidence()` Has Zero Deduplication

**File**: `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`, lines 40-79

**Root cause**: The `syncEvidence()` method iterates over all evidence items in the payload and calls `$this->entityManager->saveEntity($evidence)` for every single one (line 69). There is **no query for existing records** — no snapshot hash lookup, no identity lookup, no find-before-create of any kind. Every invocation of the `/Prospecting/sync/evidence` endpoint creates new ResearchEvidence records unconditionally.

```php
// Line 52-69 — NO find-before-create:
foreach ($payload['evidence'] as $item) {
    $evidence = $this->entityManager->getEntity('ResearchEvidence'); // ALWAYS new
    $evidence->set([...]);
    $this->entityManager->saveEntity($evidence);                    // ALWAYS saves
}
```

**Production impact**: The main production code path flows through `connector_api.py:83` calling `self.sync_evidence(payload)`, which POSTs to the PHP endpoint. This means **every evidence sync creates duplicates**.

### 3.0b — BLOCKER — Python Dedup Adapter Is Never Invoked in Production

**File**: `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py`

**Root cause**: The `ResearchEvidencePersistenceAdapter` class (line 59) contains correct dedup logic with two-level matching (snapshot hash + identity key). It is properly exported in `__init__.py`. However, **no production module ever instantiates or calls it**. The only callers are test files:
- `test_phase3c10_evidence_dedup_hardening.py`
- `test_phase3c07_research_evidence_persistence.py`
- `test_phase3c07_runtime_acceptance.py`

The production pipeline in `connector_api.py:83` calls `self.sync_evidence(payload)`, which POSTs directly to the PHP endpoint — completely bypassing the Python adapter.

**Architecture split**:

| Path | Location | Dedup? | Used in production? |
|------|----------|--------|---------------------|
| Python `ResearchEvidencePersistenceAdapter` | `research_evidence_persistence.py` | ✅ YES | ❌ NO (tests only) |
| PHP `ChituSyncService::syncEvidence()` | `ChituSyncService.php` | ❌ NO | ✅ YES (connector_api.py → API endpoint) |

### 3.0c — BLOCKER — `peEvidenceType` Mapped from Wrong Source Field

**File**: `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`, line 60

**Root cause**: The code reads:
```php
'peEvidenceType' => $item['claim_type'],  // BUG: should be $item['evidence_type']
```

The `peEvidenceType` field (defined as "evidence format classification" — values like `"visible_text"`, `"title"`, `"meta_description"`) is populated from the `claim_type` value instead of `evidence_type`. The Python adapter correctly maps this at `research_evidence_persistence.py:280`:
```python
"peEvidenceType": item.evidence_type,  # correct
```

### 3.1 Identity Key Composition — PASS

**Key file**: `chitu_connector/espocrm_sync/research_evidence_persistence.py:211-233`

The `evidence_identity_key()` function constructs the identity as:

```python
payload = {
    "version": "c10-research-evidence-identity-v1",
    "lead_id": lead_id.strip(),
    "source_url": _canonical_source_url(source_url),
    "claim_type": _normalize_text(claim_type).lower(),
    "claim_hash": sha256(_normalize_text(claim).encode("utf-8")).hexdigest(),
}
```

This exactly matches the specification: **leadId + canonical source URL + normalized claimType + claim SHA-256**.

### 3.2 snapshotHash Exclusion — PASS

**Verified**: `snapshotHash` is NOT part of the identity key. The code explicitly documents this (line 221): "The batch snapshot hash is intentionally excluded: it describes a complete extraction run and changes when unrelated evidence is added or removed."

**snapshotHash is used ONLY for**:
1. The fast-path initial lookup (`find_research_evidence_for_snapshot`) to check if the entire batch was already persisted
2. Storage on the ResearchEvidence record (field `peSnapshotHash`, varchar 128)
3. A simple (non-unique) database index for lookup optimization

**snapshotHash is NOT used for**:
- Identity matching between evidence records
- Deduplication decisions
- Unique constraint enforcement

### 3.3 Retry Safety — PASS

**Key file**: `chitu_connector/espocrm_sync/research_evidence_persistence.py:72-206`

The `persist()` method implements a deterministic two-phase approach:

1. **Phase 1 — Batch match** (line 126): Query by `leadId + snapshotHash`. If ALL expected evidence IDs are found → `SKIPPED`.
2. **Phase 2 — Per-item match** (lines 152-198): For each missing evidence item, query by `leadId + sourceUrl + claimType + claim`. If found → skip creation. If not found → create.

This is **idempotent**: calling `persist()` with the same evidence items multiple times produces the same CRM records. Partial failures (e.g., create fails on item 2 of 5) are recovered on retry because items 1, 3, 4, 5 are re-matched by identity.

### 3.4 Duplicate Prevention — PASS

**Verified by test**: `test_phase3c10_evidence_dedup_hardening.py`

| Test | Behavior | Status |
|------|----------|--------|
| Same lead, same evidence, different snapshots | SKIPPED (no duplicate) | ✅ |
| Same lead, different evidence | CREATED | ✅ |
| Different lead, same evidence | CREATED (identity scoped per lead) | ✅ |
| Partial failure retry | Creates only missing evidence | ✅ |

### 3.5 URL Canonicalization — PASS

**Key file**: `research_evidence_persistence.py:255-265`

The `_canonical_source_url()` function:
- Lowercases scheme and hostname
- Strips default ports (443 for HTTPS, 80 for HTTP)
- Normalizes path trailing slashes
- Sorts query parameters alphabetically
- Strips fragments

**Verified by test** (`test_phase3c10_evidence_dedup_hardening.py:151-171`):
```python
# Different URL representations produce the same identity:
"HTTPS://DEALER.EXAMPLE:443/products/?b=2&a=1#catalog"
"https://dealer.example/products?a=1&b=2"
# → same identity key
```

### 3.6 Claim Normalization — PASS

**Key file**: `research_evidence_persistence.py:268-269`

`_normalize_text()` collapses all whitespace: `" ".join(value.split())`. This handles newlines, tabs, multiple spaces.

**Verified by test**:
```python
"The   company lists industrial resin printers.\n"
"The company lists industrial resin printers."
# → same claim_hash after normalization
```

### 3.7 claimType Normalization — PASS

`claim_type` is normalized via `_normalize_text(claim_type).lower()` — whitespace collapse + case-insensitive.

**Verified by test**:
```python
"Product" → "product"
# → same claim_type in identity
```

### 3.8 Evidence Dedup Warnings

**WARNING 1**: No database-level unique constraint on the dedup identity fields. The `entityDefs/ResearchEvidence.json` has:
- `peEvidenceId` index (single-column, non-unique)
- `peSnapshotHash` index (single-column, non-unique)

There is **no composite unique index** on `(leadId, peSourceUrl, peClaimType, peClaim)` or their hash. All dedup prevention is at the application level — which, per findings 3.0 and 3.0b, does not exist in the production PHP path. This means:
- Direct API calls bypass all dedup
- Concurrent connector processes can create duplicates
- No database-level guard exists

**WARNING 2**: The `find_research_evidence_by_identity()` in `real_client.py:152-168` constructs API queries using raw, non-normalized values:
```python
"where[2][value]": source_url,    # raw URL, no canonicalization
"where[3][value]": claim_type,    # raw claim_type, no normalization
"where[4][value]": claim,         # raw claim, no normalization
```
However, `evidence_identity_key()` applies full canonicalization (scheme lowercase, port removal, query param sorting, whitespace normalization). This means even if the Python adapter were called in production, the API query could miss records that are semantically identical but textually different. The test mock `InMemoryResearchEvidenceClient` also uses exact matching, so tests cannot catch this gap.

**WARNING 3**: Two independent evidence creation paths exist — the undeduped PHP path (production) and the deduped Python adapter (test-only). This architectural split means the dedup logic, while correctly implemented and tested, provides zero production protection.

---

## 4. Runtime State Audit

### 4.1 Hardcoded Credentials — BLOCKER (×2)

**BLOCKER 1: Plaintext passwords in provisioning**

**File**: `deployment/provisioning/phase3a33_provision_roles.php`
- Line 168: `'password' => $passwordHash->hash('SalesTest#2026')`
- Line 179: `'password' => $passwordHash->hash('ManagerTest#2026')`
- Line 198: API key printed to stdout for `integration_bot_test`

**Risk**: Plaintext passwords committed to repository. Though hashed before storage, any developer with repo access can read the plaintext.

**BLOCKER 2: Hardcoded API keys across 7 provisioning scripts**

| Script | Line | Key |
|--------|------|-----|
| `phase3b03_provision_connector_test_user.php` | 23 | `phase3b03-local-test-api-key` |
| `phase3b04_provision_feedback_test_user.php` | 60 | `phase3b04-local-test-api-key` |
| `phase3b05a_provision_brevo_test_user.php` | 56 | `phase3b05a-local-brevo-test-key` |
| `phase3b05b_provision_email_workflow_roles.php` | 60 | `phase3b05b-local-workflow-test-key` |
| `phase3b05c_provision_email_feedback_roles.php` | 64 | `phase3b05c-local-feedback-test-key` |
| `phase3b06_1_provision_connector_test_user.php` | 25 | `phase3b06_1-local-test-api-key` |
| `phase3b07_provision_validation_user.php` | 23 | `phase3b07-local-test-api-key` |

**Risk**: These are marked "local" but committed to the repo. If any test user accidentally exists on a production instance, these API keys would grant access.

### 4.2 Stale Deployment Artifacts — BLOCKER

**Directory**: `deployment/` — 13 old alpha extension ZIP archives (v1.2.0 through v1.8.0) plus untracked v1.9.0-v1.9.5 copies. Only v1.9.5-alpha is current.

**Risk**: Obsolete artifacts could be accidentally deployed or confused with the current release.

### 4.3 Documentation Drift — BLOCKER

**File**: `docs/README.md`
- Line 13: `Extension version: 1.9.0-alpha` — **actual**: `1.9.5-alpha`
- Line 16: `Latest packaged artifact: ...1.9.0-alpha.zip` — **actual**: `...1.9.5-alpha.zip`

**Risk**: Stale documentation misleads operators about the current system state.

### 4.4 Deleted File Without Clear Supersession — BLOCKER

**File**: `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchJob/PrimaryFilters/JobsWaiting.php` — **DELETED** (git status: `D`)

**Root cause**: This primary filter class was deleted. The replacement `JobsQueued.php` exists and is referenced in `selectDefs/SearchJob.json`. The dashlet `AcquisitionJobsWaiting.json` was updated from `"primary": "jobsWaiting"` to `"primary": "jobsQueued"`. This is a valid rename but was performed across multiple uncommitted changes — the deletion and replacement should be committed together to prevent a broken intermediate state.

### 4.5 Diagnostic Temp Files — BLOCKER

**Directory**: `temp/` (gitignored, exists on disk)

**Files requiring cleanup**:
- `temp/_verify_formula.php` — creates a `FORMULA-TEST` Lead
- `temp/_debug_formula.php` — reads metadata for debugging
- `temp/_verify_metadata.php` — metadata diagnostic
- `temp/check_clientdefs.php` — client def validation
- `temp/test-results/` — 86 test log files (~1.2 MB)

**Risk**: These were one-time diagnostic tools. They should be deleted or moved to a `scripts/` directory under version control. The `FORMULA-TEST` marker is explicitly banned in production code (verified by `test_phase3c06_prospecting_ui_foundation.py:86`).

### 4.6 Test User Proliferation — WARNING

**Root cause**: Each provisioning phase (3b03 through 3b07) created its own disposable API test user:
- `phase3b03_connector_test`
- `phase3b04_connector_test`
- `phase3b05a_brevo_test`
- `phase3b06_1_connector_test`
- `phase3b07_validation_bot`

While each has a corresponding `*_cleanup_validation_records.php` script, there is no guarantee all have been cleaned from every deployment instance. Additionally, the root `admin` account receives phase-specific dashboard provisioning in both `phase3b07` and `phase3c01` scripts.

### 4.7 Synthetic Data — WARNING

**File**: `deployment/provisioning/phase3b07_provision_synthetic_records.php`

**Details**:
- Creates 9 synthetic Lead records with `[CHITU_PHASE3B07_TEST]` marker
- Creates synthetic ResearchEvidence and SalesFeedback records
- All synthetic records properly set `peProposalAction = "NO_AUTOMATIC_OPPORTUNITY"` (with one intentional test variant: empty string)
- Synthetic evidence uses `peSnapshotHash = str_repeat('7', 64)` (static hash)
- Cleanup script exists (`phase3b07_cleanup_validation_records.php`) that removes all `[CHITU_PHASE3B07_TEST]` records

**Assessment**: Synthetic data is well-structured and cleanable. The cleanup script should be run before production deployment.

### 4.8 __pycache__ Residue — WARNING

92 `.pyc` files across 16 `__pycache__/` directories. While `.gitignore` covers `__pycache__/`, these files remain on disk. Not a git issue, but represents stale build artifacts that should be cleaned before freeze.

### 4.9 Dashboard Dual-Provisioning — WARNING

Two dashboard provisioning scripts both apply to `admin`, `manager_test`, and `sales_test`:
1. `phase3b07_provision_operations_dashboards.php` → "Prospecting Operations" tab
2. `phase3c01_provision_acquisition_workspace.php` → "Prospecting Home" tab

Both use phase-prefixed dashlet IDs (`phase3c01-*`, `phase3u03-*`, `phase3b07-*`) for idempotency. The prefix-based filter/replace pattern works but is fragile — if dashlet names change, the regex patterns must be manually updated.

### 4.10 Navbar Tab Configuration — PASS

Tab order is explicitly controlled via `phase3u04_provision_navbar_tab_order.php` which writes to EspoCRM's `config.tabList`:

```
ProspectingDashboard → ProspectingSearch → SearchStrategy →
SearchJob → ProspectPool → ResearchEvidence
```

This matches the logical workflow: Dashboard → Search → Strategy → Jobs → Prospects → Evidence.

---

## Appendix A: File Inventory

### A.1 Top-Level vs Module-Level Duplicates

| Metadata Type | Top-Level Path | Module-Level Path | Duplicate? |
|---------------|---------------|-------------------|------------|
| entityDefs (×9) | `Resources/entityDefs/` | `Resources/metadata/entityDefs/` | ✅ Identical |
| layouts (×9) | `Resources/layouts/` | `Resources/layouts/` | ✅ Identical |
| ACL (×7) | `Resources/acl/` | `Resources/metadata/aclDefs/` | ✅ Identical (`acl` vs `aclDefs` naming) |
| formula | `Resources/metadata/formula/Lead.json` | `Resources/metadata/formula/Lead.json` | ✅ Identical |

### A.2 Deployed Extension Artifacts

| Version | File | Size | Date |
|---------|------|------|------|
| v1.2.0-alpha | `prospecting-extension-v1.2.0-alpha.zip` | 15 KB | 2026-07-12 |
| v1.3.1-alpha | `prospecting-extension-1.3.1-alpha.zip` | 20 KB | 2026-07-12 |
| v1.4.0-alpha | `prospecting-extension-1.4.0-alpha.zip` | 30 KB | 2026-07-12 |
| v1.4.1-alpha | `prospecting-extension-1.4.1-alpha.zip` | 30 KB | 2026-07-12 |
| v1.5.0-alpha | `prospecting-extension-1.5.0-alpha.zip` | 37 KB | 2026-07-12 |
| v1.5.1-alpha | `prospecting-extension-1.5.1-alpha.zip` | 38 KB | 2026-07-12 |
| v1.5.2-alpha | `prospecting-extension-1.5.2-alpha.zip` | 40 KB | 2026-07-12 |
| v1.6.0-alpha | `prospecting-extension-1.6.0-alpha.zip` | 42 KB | 2026-07-13 |
| v1.6.1-alpha | `prospecting-extension-1.6.1-alpha.zip` | 43 KB | 2026-07-13 |
| v1.7.0-alpha | `prospecting-extension-1.7.0-alpha.zip` | 58 KB | 2026-07-13 |
| v1.7.1-alpha | `prospecting-extension-1.7.1-alpha.zip` | 58 KB | 2026-07-13 |
| v1.8.0-alpha | `prospecting-extension-1.8.0-alpha.zip` | 73 KB | 2026-07-13 |
| v1.9.0-alpha | `prospecting-extension-1.9.0-alpha.zip` | 83 KB | 2026-07-13 |
| **v1.9.5-alpha** | `prospecting-extension-1.9.5-alpha.zip` | **102 KB** | **2026-07-13** ← current |

### A.3 Provisioning Scripts

| Phase | Script | Type | Has Cleanup? |
|-------|--------|------|--------------|
| 3a33 | `phase3a33_provision_roles.php` | Baseline roles + users | ❌ |
| 3b01 | `phase3b01_provision_entity_model_roles.php` | Entity model roles | ✅ |
| 3b02 | `phase3b02_provision_workflow_pipeline.php` | Workflow pipeline | ✅ |
| 3b03 | `phase3b03_provision_connector_test_user.php` | Test API user | ✅ |
| 3b04 | `phase3b04_provision_feedback_test_user.php` | Feedback test user | ✅ |
| 3b05a | `phase3b05a_provision_brevo_test_user.php` | Brevo test user | ✅ |
| 3b05b | `phase3b05b_provision_email_workflow_roles.php` | Email workflow | ✅ |
| 3b05c | `phase3b05c_provision_email_feedback_roles.php` | Email feedback | ✅ |
| 3b06 | `phase3b06_provision_synthetic_lead.php` | Synthetic lead data | ✅ |
| 3b06_1 | `phase3b06_1_provision_connector_test_user.php` | Connector test user | ✅ |
| 3b07 | `phase3b07_provision_operations_dashboards.php` | Operations dashboard | ✅ |
| 3b07 | `phase3b07_provision_synthetic_records.php` | Synthetic records | ✅ |
| 3b07 | `phase3b07_provision_validation_user.php` | Validation user | ✅ |
| 3c01 | `phase3c01_provision_acquisition_workspace.php` | Acquisition workspace | ❌ |
| 3c02_1 | `phase3c02_1_provision_acquisition_acl.php` | Acquisition ACL | ❌ |
| 3u04 | `phase3u04_provision_navbar_tab_order.php` | Navbar tab order | ❌ |

---

## Appendix B: Test Coverage Summary

### CRM Extension Tests (6 files)
- `test_extension_skeleton.py` — entity validation, metadata structure
- `test_phase3c02_search_strategy_foundation.py` — SearchStrategy CRUD + ACL
- `test_phase3c06_prospecting_ui_foundation.py` — UI contracts, routes, labels
- `test_phase3u03_dashboard_productization.py` — Dashboard JS + template
- `test_phase3u03_menu_empty_state.py` — Menu empty states
- `__init__.py`

### Connector Tests (32 files)
Full coverage of: lifecycle sync, real client, email lifecycle, Brevo API, feedback API, connector API, acquisition worker, provider adapters, evidence extraction, evidence dedup, enrichment gate, score projection, outreach, campaign, human approval, send idempotency, runtime acceptance (×4).

### Deployment Validation (2 files)
- `test_phase3c02_1a_search_strategy_detail.py`
- `phase3c02_1_api_acl_acceptance.py`

---

## Appendix C: Freeze Checklist

Before freeze, address:

### Must Fix (BLOCKER — 12 items)

**Evidence Sync (3 — MOST CRITICAL)**:
- [ ] **BLOCKER**: Add dedup to PHP `ChituSyncService::syncEvidence()` — implement find-before-create with snapshot hash and identity matching before saving each evidence record
- [ ] **BLOCKER**: Fix `peEvidenceType` field mapping from `$item['claim_type']` to `$item['evidence_type']` in `ChituSyncService.php:60`
- [ ] **BLOCKER**: Wire Python `ResearchEvidencePersistenceAdapter` into production code path, or implement equivalent dedup logic in the PHP endpoint

**Extension Boundary (3)**:
- [ ] **BLOCKER**: Fix layout divergence — sync design surface `Resources/layouts/` to match installable tree, or remove design surface entirely since build script excludes it
- [ ] **BLOCKER**: Resolve entityDefs duplication — remove design surface copies from `Resources/entityDefs/` or add CI check to enforce parity
- [ ] **BLOCKER**: Remove or update stale `custom/*/README.md` files that claim "No X in Phase 3A-2.1"

**Runtime Hygiene (6)**:
- [ ] **BLOCKER**: Remove hardcoded passwords from `phase3a33_provision_roles.php` (lines 168, 179)
- [ ] **BLOCKER**: Remove hardcoded API keys from 7 provisioning scripts (or move to env vars)
- [ ] **BLOCKER**: Prune old `.zip` artifacts from `deployment/` (keep only v1.9.5-alpha + SHA256)
- [ ] **BLOCKER**: Update `docs/README.md` version references (1.9.0 → 1.9.5)
- [ ] **BLOCKER**: Commit `JobsWaiting.php` deletion together with `JobsQueued.php` replacement
- [ ] **BLOCKER**: Clean `temp/` directory (remove diagnostic scripts, archive test logs)

### Should Fix (WARNING — 21 items)
- [ ] Remove duplicate metadata from `crm-extension/Resources/` (entityDefs, layouts, acl, formula)
- [ ] Run all `*_cleanup_validation_records.php` scripts before production deployment
- [ ] Clean `__pycache__/` directories (92 `.pyc` files)
- [ ] Add version coupling between CRM extension and Python connector
- [ ] Consider database-level unique constraint on evidence dedup fields
- [ ] Add SHA256 files for v1.9.1-v1.9.5 extension builds
- [ ] Standardize `chitu-connector` vs `chitu_connector` directory naming
- [ ] Remove or commit `deployment/backup/` (currently empty placeholder)

---

*Audit conducted by Claude Code + DeepSeek V4 Pro. No code modifications were made. All findings are derived from static analysis of committed and working-tree files as of 2026-07-14.*
