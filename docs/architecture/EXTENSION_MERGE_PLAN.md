# EspoCRM Extension Dual-Source Merge Plan

**Date:** 2026-07-11  
**Scope:** Read-only audit — no files modified, moved, deleted, or rebuilt  
**Status:** ANALYSIS COMPLETE; MIGRATION DESIGNED (not executed)

---

## 1. Audit Summary

The EspoCRM Prospecting extension currently exists in **two locations** inside the
Docker container (`espocrm`), creating a split-brain that was intentionally
constructed during Phase 3A-2.1 but is now a maintenance and correctness risk.

| Location | Role | PHP classes win? | Metadata merge position |
|---|---|---|---|
| `custom/Espo/Modules/Prospecting/` | Module package (canonical) | Second (shadowed) | Base layer |
| `custom/Espo/Custom/` | Overlay (runtime winner) | **First** | Overlay (last, wins on collision) |

**Runtime resolution (confirmed from classmap cache):**

```
Entity:      ResearchEvidence → Espo\Custom\Entities\ResearchEvidence    ← WINS
Controller:  ResearchEvidence → Espo\Custom\Controllers\ResearchEvidence  ← WINS
```

---

## 2. File Inventory — Complete Overlap Map

### 2.1 Files existing in BOTH locations

| File | Custom | Module | Semantic Content Diff? |
|---|---|---|---|
| `Entities/ResearchEvidence.php` | `Espo\Custom\Entities` | `Espo\Modules\Prospecting\Entities` | Namespace only; bodies identical |
| `Controllers/ResearchEvidence.php` | `Espo\Custom\Controllers` | `Espo\Modules\Prospecting\Controllers` | Namespace only; bodies identical |
| `Resources/metadata/entityDefs/ResearchEvidence.json` | Compact JSON | Expanded JSON | **YES — Module has `tooltip:true` on 3 fields + `view:views/fields/user` on 2 fields** |
| `Resources/metadata/entityDefs/Lead.json` | Compact JSON | Expanded JSON | **YES — Module has `tooltip:true` on all 8 pe* fields** |
| `Resources/metadata/scopes/ResearchEvidence.json` | 7 keys | 9 keys | **YES — Module adds `module:"Prospecting"` + `statusField:null`** |
| `Resources/metadata/clientDefs/ResearchEvidence.json` | Identical | Identical | No |

### 2.2 Files existing ONLY in Module (missing from Custom)

| File | Purpose | Impact if lost |
|---|---|---|
| `Resources/module.json` | `{"order": 25}` — module load order | Module entity registered after Crm |
| `Resources/metadata/aclDefs/ResearchEvidence.json` | Non-standard ACL registry | Low (ACL driven by `scopes.acl=true`) |
| `Resources/i18n/en_US/Lead.json` | Lead field labels | UI field labels gone |
| `Resources/i18n/en_US/ResearchEvidence.json` | ResearchEvidence labels + tooltips | UI labels + tooltip text gone |
| `Resources/layouts/ResearchEvidence/detail.json` | Detail view layout | UI detail view broken |
| `Resources/layouts/ResearchEvidence/list.json` | List view layout | UI list view broken |

### 2.3 Files existing in NEITHER location

| Item | Status |
|---|---|
| `Resources/metadata/relationships/` | Does not exist anywhere |
| `Services/ResearchEvidence.php` | Not needed (uses default Record service) |
| Installable `.zip` package | Not yet built |

### 2.4 Source-of-truth on disk

The `espocrm_extension/files/` directory on the host contains BOTH sets as the
authoritative source. The Docker container at `/var/www/html/custom/Espo/` is a
copy deployed during installation.

```
espocrm_extension/files/custom/Espo/
├── Custom/                              ← Custom overlay (6 files)
│   ├── Entities/ResearchEvidence.php
│   ├── Controllers/ResearchEvidence.php
│   └── Resources/metadata/
│       ├── entityDefs/Lead.json
│       ├── entityDefs/ResearchEvidence.json
│       ├── scopes/ResearchEvidence.json
│       └── clientDefs/ResearchEvidence.json
└── Modules/Prospecting/                 ← Module package (15 files)
    ├── Entities/ResearchEvidence.php
    ├── Controllers/ResearchEvidence.php
    ├── Api/README.md
    ├── Services/README.md
    └── Resources/
        ├── module.json
        ├── i18n/en_US/{Lead,ResearchEvidence}.json
        ├── layouts/ResearchEvidence/{detail,list}.json
        └── metadata/
            ├── aclDefs/ResearchEvidence.json
            ├── clientDefs/ResearchEvidence.json
            ├── entityDefs/{Lead,ResearchEvidence}.json
            └── scopes/ResearchEvidence.json
```

---

## 3. Runtime Loading — Precedence Analysis

### 3.1 EspoCRM Loading Order

```
1. Core (application/Espo/Resources/metadata/)
2. Modules (custom/Espo/Modules/*/Resources/metadata/)  ← loaded after core
3. Custom  (custom/Espo/Custom/Resources/metadata/)      ← loaded LAST
```

### 3.2 PHP Class Resolution (classmap)

EspoCRM's `rebuild` command scans directories in order:
1. `custom/Espo/Modules/*/{Entities,Controllers,Services,...}`
2. `custom/Espo/Custom/{Entities,Controllers,Services,...}`

Later entries **overwrite** earlier entries in the classmap. Therefore:
- `Espo\Custom\Entities\ResearchEvidence` wins over `Espo\Modules\Prospecting\Entities\ResearchEvidence`
- `Espo\Custom\Controllers\ResearchEvidence` wins over `Espo\Modules\Prospecting\Controllers\ResearchEvidence`

**Confirmed (2026-07-11):**
```
classmapEntities.php:    'ResearchEvidence' => 'Espo\Custom\Entities\ResearchEvidence'
classmapControllers.php: 'ResearchEvidence' => 'Espo\Custom\Controllers\ResearchEvidence'
```

### 3.3 Metadata Resolution (recursive merge)

EspoCRM **deep-merges** metadata from all three layers. For overlapping keys at
the same level, the last-loaded value wins entirely.

| Metadata key | Module defines | Custom defines | Effective result | Winner |
|---|---|---|---|---|
| `scopes.ResearchEvidence.module` | `"Prospecting"` | *(absent)* | `"Prospecting"` | Module (survives — not overridden) |
| `scopes.ResearchEvidence.statusField` | `null` | *(absent)* | `null` | Module (survives) |
| `scopes.ResearchEvidence.type` | `"Base"` | `"Base"` | `"Base"` | Same value |
| `entityDefs.ResearchEvidence.fields.peEvidenceId.tooltip` | `true` | *(absent)* | **ABSENT** | Custom wins (replaces entire field def) |
| `entityDefs.ResearchEvidence.fields.peClaimType.tooltip` | `true` | *(absent)* | **ABSENT** | Custom wins |
| `entityDefs.ResearchEvidence.fields.peEvidenceText.tooltip` | `true` | *(absent)* | **ABSENT** | Custom wins |
| `entityDefs.ResearchEvidence.fields.createdBy.view` | `"views/fields/user"` | *(absent)* | **ABSENT** | Custom wins |
| `entityDefs.ResearchEvidence.fields.modifiedBy.view` | `"views/fields/user"` | *(absent)* | **ABSENT** | Custom wins |
| `entityDefs.Lead.fields.pe*.tooltip` | `true` (all 8) | *(absent)* (all 8) | **ABSENT** (all 8) | Custom wins |
| `entityDefs.ResearchEvidence.collection` | Present | Present | Present (Custom value) | Custom wins |
| `entityDefs.ResearchEvidence.indexes` | Present | Present | Present (Custom value) | Custom wins |

**Key finding:** The Custom overlay silently strips Module metadata rich
properties (`tooltip`, `view`) because Custom redefines the same field keys with
fewer properties, and deep merge replaces entire field sub-objects at collision
points. Module-only top-level keys (`module`, `statusField`) survive because
Custom doesn't override them.

### 3.4 Current preflight() check

`LocalEspoCRMClient.preflight()` in `integration/espocrm_sync/real_client.py`
validates:
```python
_LEAD_FIELDS = {"name","website","description","peOpportunityScoreV4","peScoreTier",
    "peConfidence","peEvidenceCoverage","peBestFirstProduct","peQualificationStatus",
    "peEngineVersion","peScoreRulesVersion"}
_RESEARCH_EVIDENCE_FIELDS = {"name","peEvidenceId","peClaim","peClaimType",
    "peSourceUrl","peEvidenceText","peConfidence","peCapturedAt","peSchemaVersion",
    "peSnapshotHash"}
```

It checks **field existence only** — not tooltips, views, collection, indexes,
or other metadata properties. The preflight passes under the current dual-source
setup because all required field names exist regardless of which layer provides
them.

---

## 4. Risk Analysis

### 4.1 Risk Matrix

| Risk | Severity | Likelihood | Impact | Trigger condition |
|---|---|---|---|---|
| **Metadata drift deepens** | **HIGH** | **HIGH** | Custom copies fall further behind Module definitions; tooltips, views, layouts silently break | Any future field edit made to one copy but not the other |
| **EspoCRM rebuild changes winner** | **MEDIUM** | **LOW** | A `rebuild` after removing one source could flip class resolution | Selective deletion without understanding loading order |
| **EspoCRM version upgrade** | **MEDIUM** | **MEDIUM** | Module upgrade/reinstall could overwrite Module files and leave stale Custom copies | Admin reinstalls/upgrades the Prospecting module |
| **Admin UI writes to Custom** | **MEDIUM** | **MEDIUM** | Entity Manager writes customizations under `Custom/`, amplifying split-brain | Admin modifies ResearchEvidence fields via UI |
| **Field property drift** | **MEDIUM** | **ACTIVE** | `tooltip:true` on 11 fields is silently stripped; `view:views/fields/user` lost on 2 fields | Already happening — Custom copies lack these properties |
| **Scope metadata conflict** | **LOW** | **LOW** | `module:"Prospecting"` survives only because Custom doesn't override it | Someone adds `module` to Custom scopes |
| **aclDefs non-standard** | **LOW** | **LOW** | Non-standard aclDefs format may confuse future tooling | ACL checker or migration tool runs |
| **Missing relationships/ dir** | **LOW** | **LOW** | Current link defs in entityDefs are sufficient for simple belongsTo/hasMany | Complex many-to-many needed in future |

### 4.2 Current Active Drift (DETAILED)

The following metadata properties are **currently stripped** by the Custom overlay:

**ResearchEvidence entityDefs:**
| Field | Property | Module | Custom | Effective |
|---|---|---|---|---|
| `peEvidenceId` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peClaimType` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peEvidenceText` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `createdBy` | `view` | `"views/fields/user"` | *(absent)* | **ABSENT** |
| `modifiedBy` | `view` | `"views/fields/user"` | *(absent)* | **ABSENT** |

**Lead entityDefs:**
| Field | Property | Module | Custom | Effective |
|---|---|---|---|---|
| `peOpportunityScoreV4` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peScoreTier` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peConfidence` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peEvidenceCoverage` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peBestFirstProduct` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peQualificationStatus` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peEngineVersion` | `tooltip` | `true` | *(absent)* | **ABSENT** |
| `peScoreRulesVersion` | `tooltip` | `true` | *(absent)* | **ABSENT** |

**Total: 11 `tooltip:true` properties + 2 `view` properties = 13 silently stripped metadata attributes.**

### 4.3 EspoCRM Rebuild Behavior

```
php command.php rebuild
```

What happens:
1. Scans all `custom/Espo/Modules/*/` directories for PHP classes → writes to classmap
2. Scans `custom/Espo/Custom/` → **overwrites** Module entries in classmap
3. Merges all metadata JSON from core → modules → custom
4. Clears and regenerates cache

**If Custom files were removed before rebuild:**
- Classmap would resolve to `Espo\Modules\Prospecting\*` classes
- Metadata would use Module-only definitions
- `tooltip:true` and `view` properties would reappear
- `module:"Prospecting"` and `statusField:null` in scopes would persist (they already survive)
- i18n and layouts would still work (they only exist in Module)

**If Module files were removed before rebuild:**
- Classmap would still resolve to `Espo\Custom\*` classes
- Metadata from Module (tooltips, views, module key, i18n, layouts) **would be lost**
- Entity would still function but UI would degrade (no tooltips, no i18n, no layouts)
- `module.json` gone → no module load order guarantee

### 4.4 EspoCRM Upgrade Risk

If the Prospecting module is ever packaged as a proper installable extension
(`.zip` with `manifest.json`) and reinstalled:

1. Module files under `custom/Espo/Modules/Prospecting/` would be overwritten
2. Custom files under `custom/Espo/Custom/` would **NOT** be touched
3. After reinstall, Custom would still shadow Module PHP classes
4. Any Module JSON improvements would still be stripped by Custom
5. New Module-only files would be added but may be partially neutralized by
   existing Custom overlays

**This is the upgrade trap:** reinstalling/upgrading only the Module while Custom
copies exist gives the illusion of an update but preserves the stale overlay.

---

## 5. Migration Plans

### 5.1 Plan A — Keep Modules/Prospecting (Delete Custom Overlay)

**Strategy:** Eliminate the `custom/Espo/Custom/` copies entirely. Let the
Prospecting module be the single source of truth.

**Actions required:**
1. Remove these files from Docker container and `espocrm_extension/files/`:
   - `custom/Espo/Custom/Entities/ResearchEvidence.php`
   - `custom/Espo/Custom/Controllers/ResearchEvidence.php`
   - `custom/Espo/Custom/Resources/metadata/entityDefs/Lead.json`
   - `custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json`
   - `custom/Espo/Custom/Resources/metadata/scopes/ResearchEvidence.json`
   - `custom/Espo/Custom/Resources/metadata/clientDefs/ResearchEvidence.json`
2. Ensure Module entityDefs are the RICH versions (with `tooltip:true`, `view`,
   `collection`, `indexes`) — **they already are**.
3. Run `php command.php rebuild` to regenerate classmap pointing to
   `Espo\Modules\Prospecting\*`.
4. Rerun `preflight()` → should still PASS (same field names).
5. Update `test_extension_skeleton.py` to remove expected Custom PHP files.
6. Update `espocrm_extension/files/` to remove the `Custom/` subtree.

**Impact on installed container files:**
- Remove: 6 files from `custom/Espo/Custom/`
- No changes to: `custom/Espo/Modules/Prospecting/` (unchanged)

**Risk assessment:**
| Factor | Rating |
|---|---|
| Risk of breaking existing functionality | LOW — Module has everything Custom has PLUS more |
| Rebuild risk | LOW — classmap regenerates correctly |
| Metadata correctness after merge | IMPROVES — tooltips, views, module key all restored |
| i18n/layouts affected? | NO — these only exist in Module |
| Rollback difficulty | LOW — restore Custom files and rebuild |
| Preflight impact | NONE — preflight only checks field existence |

**Workload:** ~1 hour
- Remove 6 files from 2 locations (container + host source)
- Rebuild EspoCRM metadata
- Rerun preflight
- Update 1 test file
- Update documentation

**Pros:**
- Single source of truth
- Module follows EspoCRM convention for custom entities
- Richer metadata restored (tooltips, views)
- Installable as proper module package in future
- i18n and layouts stay with the entity definition

**Cons:**
- Loses the "Custom overlay" pattern that EspoCRM admin UI uses
- Custom directory pattern is what Entity Manager creates automatically — if
  someone modifies ResearchEvidence via Admin UI, Custom files could reappear

### 5.2 Plan B — Keep Custom Overlay (Delete Module)

**Strategy:** Eliminate the `custom/Espo/Modules/Prospecting/` module. Move
all Module-only assets (i18n, layouts, module.json) into the Custom tree.
Custom becomes the single source of truth.

**Actions required:**
1. Enrich Custom entityDefs with ALL Module properties currently stripped:
   - Add `"tooltip": true` to peEvidenceId, peClaimType, peEvidenceText
   - Add `"tooltip": true` to ALL 8 pe* Lead fields
   - Add `"view": "views/fields/user"` to createdBy, modifiedBy
   - Add `"module": "Prospecting"` and `"statusField": null` to scopes
2. Copy Module-only assets into Custom tree:
   - `Resources/i18n/en_US/Lead.json` → `custom/Espo/Custom/Resources/i18n/en_US/`
   - `Resources/i18n/en_US/ResearchEvidence.json` → same
   - `Resources/layouts/ResearchEvidence/detail.json` → same
   - `Resources/layouts/ResearchEvidence/list.json` → same
3. Remove ALL Module files from Docker container and `espocrm_extension/files/`:
   - 15 files under `custom/Espo/Modules/Prospecting/`
4. Remove `espocrm_extension/custom/Espo/Modules/Prospecting/` placeholder dirs
   (Controllers/README.md, Services/README.md, Api/README.md)
5. Remove `espocrm_extension/Resources/` surface-level duplicate entityDefs
   (or repoint them to Custom)
6. Keep `manifest.json` at `espocrm_extension/` root (still needed for
   extension identity)
7. Update `module.json` → no longer needed if not a module
8. Run `php command.php rebuild`
9. Rerun `preflight()` → should PASS
10. Update `test_extension_skeleton.py` to test Custom paths instead of Module

**Risk assessment:**
| Factor | Rating |
|---|---|
| Risk of breaking existing functionality | MEDIUM — metadata enrichment needed; missing any property causes drift |
| Rebuild risk | LOW — classmap already points to Custom |
| Metadata correctness after merge | DEPENDS on correct enrichment |
| i18n/layouts affected? | YES — must be manually moved |
| Rollback difficulty | MEDIUM — restore 15+ Module files and rebuild |
| Preflight impact | NONE — preflight only checks field existence |
| Future module packagability | LOST — no longer a proper EspoCRM module |

**Workload:** ~3 hours
- Enrich 4 Custom JSON files with missing properties
- Move 4 i18n/layout files into Custom tree
- Remove 15+ Module files from 2 locations
- Remove surface-level duplicate Resources
- Rebuild
- Update test file (significant rewrites)
- Update documentation

**Pros:**
- Simpler single-directory model
- PHP classmap already points to Custom (no change needed)
- Aligns with how EspoCRM Entity Manager writes customizations

**Cons:**
- **Loses module packagability** — cannot distribute as installable `.zip`
- Custom directory is EspoCRM's "admin customization" location, not designed
  for packaged extension distribution
- Requires careful metadata enrichment to avoid losing properties
- `module.json` has no equivalent in Custom tree (load order control lost)
- Surface-level `Resources/` duplicate entityDefs become the sole canonical
  definitions instead of being parity-checked against a Module source
- More files to move (4 asset files + enrichment of 4 JSON files)
- Higher risk of human error during enrichment

### 5.3 Comparative Summary

| Dimension | Plan A (Keep Module) | Plan B (Keep Custom) |
|---|---|---|
| **Risk** | LOW | MEDIUM |
| **Workload** | ~1 hour | ~3 hours |
| **Rollback difficulty** | LOW (restore 6 files) | MEDIUM (restore 15+ files) |
| **Preflight impact** | NONE | NONE |
| **Metadata correctness** | IMPROVES automatically | REQUIRES manual enrichment |
| **Future module packaging** | YES | NO |
| **EspoCRM convention** | Standard module pattern | Non-standard (Custom for packaged ext) |
| **Admin UI safety** | Entity Manager could recreate Custom copies | Natural (Admin UI writes to Custom) |
| **Test changes needed** | Minor (remove 2 expected paths) | Major (rewrite all Module→Custom paths) |
| **i18n / layouts** | Unchanged (stay in Module) | Must be moved manually |
| **Load order (`module.json`)** | Preserved | Lost |
| **PHP namespace** | `Espo\Modules\Prospecting` | `Espo\Custom` |

---

## 6. Recommendation

**Plan A (Keep Module, Delete Custom) is the clear winner.**

Reasons:
1. **Lower risk** — Module definitions are already richer; no enrichment needed
2. **Less work** — 1 hour vs 3 hours
3. **Proper EspoCRM convention** — custom entities belong in modules
4. **Future-proof** — can be packaged as installable `.zip` extension
5. **Easy rollback** — restore 6 Custom files and rebuild
6. **Automatic metadata improvement** — tooltips, views silently stripped today
   are restored without manual edits
7. **Test changes are minimal** — the test already validates Module as the
   canonical source and only checks Custom PHP file existence as a secondary
   condition

### 6.1 Counter-indication: Admin UI Regeneration Risk

If an admin uses EspoCRM's Entity Manager to modify ResearchEvidence fields,
EspoCRM may write new files under `custom/Espo/Custom/`, recreating the
split-brain. This is a manageable risk:

**Mitigation:**
- After migration, document that ResearchEvidence modifications should happen
  in the Module source, not via Admin UI
- Add a `custom/Espo/Custom/.htaccess` deny rule or gitignore marker if the
  team wants to prevent accidental Admin UI writes
- The `preflight()` check would catch regression (field drift detection)

---

## 7. Migration Execution Plan (Plan A — Reference Only; NOT Authorized)

### Phase 1: Pre-migration snapshot
1. Backup current Docker container state: `docker commit espocrm espocrm:pre-merge-snapshot`
2. Export current classmap: `docker exec espocrm cat data/cache/application/classmapEntities.php > temp/pre_merge_classmap.txt`

### Phase 2: Remove Custom overlay
3. Remove from Docker container:
   ```bash
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Entities/ResearchEvidence.php
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Controllers/ResearchEvidence.php
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Resources/metadata/entityDefs/Lead.json
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Resources/metadata/scopes/ResearchEvidence.json
   docker exec espocrm rm -rf /var/www/html/custom/Espo/Custom/Resources/metadata/clientDefs/ResearchEvidence.json
   ```
4. Remove from host source tree:
   ```powershell
   Remove-Item -Recurse -Force espocrm_extension/files/custom/Espo/Custom/
   ```

### Phase 3: Rebuild and verify
5. Rebuild EspoCRM:
   ```bash
   docker exec espocrm php command.php rebuild
   ```
6. Verify classmap (should now show `Espo\Modules\Prospecting\*`):
   ```bash
   docker exec espocrm cat data/cache/application/classmapEntities.php | grep ResearchEvidence
   ```
7. Run preflight:
   ```bash
   python -c "from integration.espocrm_sync.real_client import LocalEspoCRMClient; ..."
   ```

### Phase 4: Update tests and docs
8. Update `espocrm_extension/tests/test_extension_skeleton.py`:
   - Remove `Custom/Entities/ResearchEvidence.php` and `Custom/Controllers/ResearchEvidence.php`
     from `test_only_standard_research_evidence_php_shells_exist`
9. Update `CLAUDE.md` deployment instructions to reference Module-only paths
10. Update this report status to EXECUTED with results

### Phase 5: Rollback plan (if needed)
```bash
# Restore Custom files from git
git checkout -- espocrm_extension/files/custom/Espo/Custom/
# Redeploy to container (copy files back)
# Rebuild
docker exec espocrm php command.php rebuild
```

---

## 8. Preflight Impact Analysis

### Current preflight checks (`real_client.py:107-119`):

```python
def preflight(self) -> PreflightResult:
    self._require_authentication()
    lead_fields = self._metadata("entityDefs.Lead.fields")
    evidence_definition = self._metadata("entityDefs.ResearchEvidence")
    if not isinstance(lead_fields, Mapping) or not isinstance(evidence_definition, Mapping):
        raise EnvironmentSafetyError("required local EspoCRM extension metadata is unavailable")
    evidence_fields = evidence_definition.get("fields")
    lead_links = self._metadata("entityDefs.Lead.links")
    missing_lead = _LEAD_FIELDS - set(lead_fields)
    missing_evidence = _RESEARCH_EVIDENCE_FIELDS - set(evidence_fields or {})
    if missing_lead or missing_evidence or not isinstance(lead_links, Mapping) or "researchEvidences" not in lead_links:
        raise EnvironmentSafetyError("local EspoCRM extension schema does not match the approved skeleton")
    return PreflightResult(tuple(sorted(lead_fields)), tuple(sorted(evidence_fields)))
```

### Impact of Plan A on preflight:

| Check | Before (dual-source) | After (Module-only) | Change? |
|---|---|---|---|
| `entityDefs.Lead.fields` keys | All 8 pe* present | All 8 pe* present | No change |
| `entityDefs.ResearchEvidence` mapping | Present | Present | No change |
| `entityDefs.ResearchEvidence.fields` keys | All 10 required | All 10 required | No change |
| `entityDefs.Lead.links.researchEvidences` | Present | Present | No change |
| `_LEAD_FIELDS - set(lead_fields)` | Empty | Empty | No change |
| `_RESEARCH_EVIDENCE_FIELDS - set(evidence_fields)` | Empty | Empty | No change |

**PREFLIGHT: NO IMPACT.** Plan A will pass `preflight()` identically to the
current dual-source state. The only difference is that tooltip/view metadata
properties will be restored in the API response, but `preflight()` does not
inspect those.

---

## 9. Test Impact Analysis

### `test_extension_skeleton.py` changes needed for Plan A

**`test_only_standard_research_evidence_php_shells_exist` (line 174-182):**

Current:
```python
expected = {
    MODULE / "Entities" / "ResearchEvidence.php",
    MODULE / "Controllers" / "ResearchEvidence.php",
    EXT / "files" / "custom" / "Espo" / "Custom" / "Entities" / "ResearchEvidence.php",
    EXT / "files" / "custom" / "Espo" / "Custom" / "Controllers" / "ResearchEvidence.php",
}
```

After Plan A:
```python
expected = {
    MODULE / "Entities" / "ResearchEvidence.php",
    MODULE / "Controllers" / "ResearchEvidence.php",
}
```

**`test_required_directory_structure` (line 99-103):**
- No change needed — Module directories remain listed in `REQUIRED_DIRS`

**All other tests:** No change needed. Contract, field, surface-parity tests all
validate against the Module source, which is unchanged.

---

## 10. Edge Cases and Open Questions

### 10.1 What if Admin UI recreates Custom files?

**Scenario:** Admin opens Entity Manager → ResearchEvidence → saves a change.
EspoCRM writes to `custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json`.

**Mitigation:** The `preflight()` gate would NOT catch this (it only checks field
existence, not property drift). A separate metadata integrity check could be added:
```python
# Optional: post-migration integrity check
def _check_custom_overlay_absent():
    custom_path = "/var/www/html/custom/Espo/Custom/Resources/metadata/entityDefs/ResearchEvidence.json"
    if os.path.exists(custom_path):
        raise EnvironmentSafetyError("Custom overlay regenerated — metadata split-brain detected")
```

### 10.2 What about the surface-level Resources/ duplication?

`espocrm_extension/Resources/entityDefs/` contains copies of the Module
entityDefs that serve as parity-check targets in `test_surface_and_module_entity_defs_match`.
After Plan A, these remain useful as a secondary validation layer but are
redundant. Consider removing them in a follow-up cleanup or keeping them as
design-time documentation.

### 10.3 Non-standard aclDefs

`Resources/metadata/aclDefs/ResearchEvidence.json` with `{"Prospecting": {"ResearchEvidence": true}}`
is non-standard EspoCRM format. It should be addressed in a separate cleanup
task. Plan A does not modify this file.

### 10.4 relationships/ directory

Neither location has a `relationships/` directory. Current link definitions
in `entityDefs` are sufficient. If complex many-to-many relationships are
added in the future, explicit `relationships/` metadata should be created
under the Module path.

### 10.5 What about the Lead.json in Module i18n?

`Resources/i18n/en_US/Lead.json` in the Module provides labels for the pe*
Lead fields. This file is Module-only and unaffected by Plan A or B. However,
note that it extends a core entity (Lead) from within a module, which is
standard EspoCRM practice.

---

## 11. Sign-off Required Before Execution

| Gate | Required? | Status |
|---|---|---|
| Human authorization to modify EspoCRM files | YES | PENDING |
| Docker container snapshot created | YES | PENDING |
| Test environment verified green before changes | YES | PENDING |
| Plan A vs Plan B decision confirmed | YES | PENDING |
| Rollback procedure documented and tested | YES | PENDING (procedure in §7 Phase 5) |

---

## 12. Appendices

### A. Complete File Hash Comparison

Source-of-truth files in `espocrm_extension/files/` (host disk):

| File | Custom sha256 | Module sha256 | Identical? |
|---|---|---|---|
| `Entities/ResearchEvidence.php` | Diff namespace | Diff namespace | NO |
| `Controllers/ResearchEvidence.php` | Diff namespace | Diff namespace | NO |
| `entityDefs/ResearchEvidence.json` | Compact, stripped | Expanded, rich | NO |
| `entityDefs/Lead.json` | Compact, stripped | Expanded, rich | NO |
| `scopes/ResearchEvidence.json` | 7 keys | 9 keys | NO |
| `clientDefs/ResearchEvidence.json` | Identical content | Identical content | YES |

### B. Key Files at a Glance

```
espocrm_extension/
├── manifest.json                                    ← Extension identity
├── files/custom/Espo/
│   ├── Custom/                                      ← TO BE REMOVED (Plan A)
│   │   ├── Entities/ResearchEvidence.php
│   │   ├── Controllers/ResearchEvidence.php
│   │   └── Resources/metadata/
│   │       ├── entityDefs/{Lead,ResearchEvidence}.json
│   │       ├── scopes/ResearchEvidence.json
│   │       └── clientDefs/ResearchEvidence.json
│   └── Modules/Prospecting/                         ← KEEP (Plan A)
│       ├── Entities/ResearchEvidence.php
│       ├── Controllers/ResearchEvidence.php
│       ├── Api/README.md
│       ├── Services/README.md
│       └── Resources/
│           ├── module.json
│           ├── i18n/en_US/{Lead,ResearchEvidence}.json
│           ├── layouts/ResearchEvidence/{detail,list}.json
│           └── metadata/
│               ├── aclDefs/ResearchEvidence.json
│               ├── clientDefs/ResearchEvidence.json
│               ├── entityDefs/{Lead,ResearchEvidence}.json
│               └── scopes/ResearchEvidence.json
├── Resources/                                       ← Surface-level copies (parity check)
│   └── entityDefs/{Lead,ResearchEvidence}.json
└── tests/test_extension_skeleton.py                 ← Extension validation tests
```

---

**No files were modified by this audit.**
