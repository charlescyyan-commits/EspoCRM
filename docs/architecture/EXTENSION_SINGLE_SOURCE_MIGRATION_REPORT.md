# EspoCRM Extension Single-Source Migration Report

**Date:** 2026-07-11  
**Status:** ✅ MIGRATION EXECUTED  
**Plan:** Plan A — Keep Modules/Prospecting, Remove Custom Overlay  
**Pre-migration snapshot:** `espocrm:pre-single-source-backup-20260711` (sha256: `c6e694e9`)

---

## 1. Pre-Migration State (Before)

### Dual-source conflict

| Location | PHP Classmap | Metadata Role |
|---|---|---|
| `custom/Espo/Modules/Prospecting/` | Shadowed (not resolved at runtime) | Base layer (merged first) |
| `custom/Espo/Custom/` | **Runtime winner** | Overlay (loaded last, wins on collision) |

### Classmap (before)

```
classmapEntities.php:    ResearchEvidence → Espo\Custom\Entities\ResearchEvidence
classmapControllers.php: ResearchEvidence → Espo\Custom\Controllers\ResearchEvidence
```

### Files duplicated (6 files)

```
Custom/Controllers/ResearchEvidence.php              ← removed
Custom/Entities/ResearchEvidence.php                 ← removed
Custom/Resources/metadata/entityDefs/Lead.json       ← removed
Custom/Resources/metadata/entityDefs/ResearchEvidence.json  ← removed
Custom/Resources/metadata/scopes/ResearchEvidence.json      ← removed
Custom/Resources/metadata/clientDefs/ResearchEvidence.json  ← removed
```

### Metadata drift (pre-migration)

Custom overlay silently stripped 13 metadata properties from Module definitions:
- 11 `tooltip: true` attributes on pe* fields (3 on ResearchEvidence, 8 on Lead)
- 2 `view: "views/fields/user"` on createdBy/modifiedBy fields

---

## 2. Pre-Migration Verification

### Module completeness confirmed

| Check | Result |
|---|---|
| ResearchEvidence entityDefs: all 10 required pe* fields | ✅ Present |
| ResearchEvidence entityDefs: `collection` block | ✅ Present |
| ResearchEvidence entityDefs: `indexes` block (peEvidenceId, peSnapshotHash) | ✅ Present |
| ResearchEvidence entityDefs: `lead` belongsTo link | ✅ Present |
| Lead entityDefs: all 8 pe* fields | ✅ Present |
| Lead entityDefs: `researchEvidences` hasMany link | ✅ Present |
| scopes: `module: "Prospecting"`, `type: "Base"`, `entity/object/tab/acl: true` | ✅ Present |
| layouts: detail.json + list.json | ✅ Present |
| i18n: Lead.json + ResearchEvidence.json (en_US) | ✅ Present |
| module.json: `{ "order": 25 }` | ✅ Present |

### Backup created

```
docker commit espocrm espocrm:pre-single-source-backup-20260711
→ sha256:c6e694e9532356b2dfefb420c16254bf639ab7cc39a1efbc32553cf785d90e0b
```

---

## 3. Migration Execution

### Step 1: Remove Custom overlay from Docker container

```bash
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Controllers/ResearchEvidence.php
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Entities/ResearchEvidence.php
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Resources/metadata/entityDefs/Lead.json
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Resources/metadata/scopes/ResearchEvidence.json
docker exec espocrm rm /var/www/html/custom/Espo/Custom/Resources/metadata/clientDefs/ResearchEvidence.json
```

Result: Only `.htaccess` (EspoCRM default) remains under `custom/Espo/Custom/`.

### Step 2: Remove Custom overlay from host source tree

```powershell
Remove-Item -Recurse -Force espocrm_extension/files/custom/Espo/Custom/
```

### Step 3: Rebuild EspoCRM

```bash
docker exec espocrm php command.php rebuild
```

Result: `Rebuild has been done.`

---

## 4. Post-Migration Verification

### 4.1 Classmap (after)

```
classmapEntities.php:    ResearchEvidence → Espo\Modules\Prospecting\Entities\ResearchEvidence  ✅
classmapControllers.php: ResearchEvidence → Espo\Modules\Prospecting\Controllers\ResearchEvidence  ✅
```

### 4.2 authenticate() + preflight()

```
authenticate(): PASS
preflight():    PASS
  Lead fields visible:              56
  ResearchEvidence fields visible:   17
```

### 4.3 Metadata Integrity

| Layer | Check | Result |
|---|---|---|
| **Scope** | `entity: true` | ✅ |
| | `object: true` | ✅ |
| | `tab: true` | ✅ |
| | `acl: true` | ✅ |
| | `module: "Prospecting"` | ✅ |
| | `type: "Base"` | ✅ |
| **Relationship** | `Lead.researchEvidences` → `hasMany ResearchEvidence` | ✅ |
| | `ResearchEvidence.lead` → `belongsTo Lead` (foreign: `lead`) | ✅ |
| **ResearchEvidence fields** | name | ✅ |
| | peEvidenceId | ✅ |
| | peClaim | ✅ |
| | peClaimType | ✅ |
| | peSourceUrl | ✅ |
| | peEvidenceText | ✅ |
| | peConfidence | ✅ |
| | peCapturedAt | ✅ |
| | peSchemaVersion | ✅ |
| | peSnapshotHash | ✅ |
| | lead (link) | ✅ |
| **Lead pe* fields** | peOpportunityScoreV4 | ✅ |
| | peScoreTier | ✅ |
| | peConfidence | ✅ |
| | peEvidenceCoverage | ✅ |
| | peBestFirstProduct | ✅ |
| | peQualificationStatus | ✅ |
| | peEngineVersion | ✅ |
| | peScoreRulesVersion | ✅ |

### 4.4 Extension Tests

```
test_contract_field_consistency ...................... ok
test_core_espocrm_untouched ......................... ok
test_lead_extension_fields .......................... ok
test_manifest_json_valid ............................ ok
test_no_database_migration_artifacts ................ ok
test_only_standard_research_evidence_php_shells_exist  ok
test_placeholder_readmes_present .................... ok
test_prospecting_engine_untouched_by_extension_tree . ok
test_required_directory_structure ................... ok
test_research_evidence_entity_created ............... ok
test_research_evidence_required_fields .............. ok
test_surface_and_module_entity_defs_match ........... ok

Ran 12 tests in 0.082s — OK
```

---

## 5. Changes Summary

### Files removed from container (6)
1. `custom/Espo/Custom/Controllers/ResearchEvidence.php`
2. `custom/Espo/Custom/Entities/ResearchEvidence.php`
3. `custom/Espo/Custom/Resources/metadata/entityDefs/Lead.json`
4. `custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json`
5. `custom/Espo/Custom/Resources/metadata/scopes/ResearchEvidence.json`
6. `custom/Espo/Custom/Resources/metadata/clientDefs/ResearchEvidence.json`

### Host files removed
- `espocrm_extension/files/custom/Espo/Custom/` (entire subtree)

### Files modified (1)
- `espocrm_extension/tests/test_extension_skeleton.py` — removed Custom PHP file expectations

### Files NOT touched
- All 15 files under `custom/Espo/Modules/Prospecting/` — **unchanged**
- `manifest.json` — unchanged
- `Resources/` (design-surface copies) — unchanged
- `integration/espocrm_sync/` — unchanged
- No business logic, API auth, or sync code modified

---

## 6. Metadata Improvement

The migration automatically restored 13 previously-stripped metadata properties:

| File | Property | Count | Effect |
|---|---|---|---|
| `entityDefs/ResearchEvidence.json` | `tooltip: true` | 3 fields | UI tooltips restored for peEvidenceId, peClaimType, peEvidenceText |
| `entityDefs/ResearchEvidence.json` | `view: "views/fields/user"` | 2 fields | User field views restored for createdBy, modifiedBy |
| `entityDefs/Lead.json` | `tooltip: true` | 8 fields | UI tooltips restored for all pe* Lead fields |
| `scopes/ResearchEvidence.json` | `module: "Prospecting"` | 1 | Module ownership correctly attributed |
| `scopes/ResearchEvidence.json` | `statusField: null` | 1 | Explicit status field declaration restored |

---

## 7. Rollback Procedure

If migration needs to be reversed:

```bash
# 1. Restore Docker container from backup
docker stop espocrm
docker rm espocrm
docker run -d --name espocrm ... espocrm:pre-single-source-backup-20260711
# (reconnect to network and volume mounts as needed)

# 2. Restore host source tree
git checkout -- espocrm_extension/files/custom/Espo/Custom/
git checkout -- espocrm_extension/tests/test_extension_skeleton.py

# 3. Rebuild
docker exec espocrm php command.php rebuild
```

---

## 8. Single Source of Truth — Final State

```
custom/Espo/Modules/Prospecting/          ← SOLE SOURCE OF TRUTH
├── Api/README.md
├── Controllers/
│   ├── README.md
│   └── ResearchEvidence.php              ← Espo\Modules\Prospecting\Controllers
├── Entities/
│   └── ResearchEvidence.php              ← Espo\Modules\Prospecting\Entities
├── Services/README.md
└── Resources/
    ├── module.json                       ← {"order": 25}
    ├── i18n/en_US/{Lead,ResearchEvidence}.json
    ├── layouts/ResearchEvidence/{detail,list}.json
    └── metadata/
        ├── aclDefs/ResearchEvidence.json
        ├── clientDefs/ResearchEvidence.json
        ├── entityDefs/{Lead,ResearchEvidence}.json
        └── scopes/ResearchEvidence.json
```

**No ResearchEvidence files exist under `custom/Espo/Custom/`.**

---

## 9. Preflight Gate Status

| Gate | Pre-migration | Post-migration |
|---|---|---|
| `authenticate()` | PASS | PASS |
| `preflight()` | PASS (with stripped metadata) | PASS (with full metadata) |
| Lead fields count | 56 | 56 |
| ResearchEvidence fields count | 17 | 17 |
| ACL visibility | OK | OK |
| Metadata drift | 13 properties stripped | **0 properties stripped** |

---

## 10. Conclusion

✅ **Single-source migration complete.** The EspoCRM extension now has one
canonical location for ResearchEvidence: `custom/Espo/Modules/Prospecting/`.

- 6 duplicate Custom overlay files removed
- Classmap resolves to `Espo\Modules\Prospecting\*`
- 13 previously-stripped metadata properties restored
- All 12 extension tests pass
- `authenticate()` + `preflight()` pass unchanged
- Pre-migration Docker snapshot available for rollback
- No business logic, sync code, or API authentication modified
