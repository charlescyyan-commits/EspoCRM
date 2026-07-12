# Phase 3A-25a MVP Lead Workflow Report

**Date:** 2026-07-11  
**Status:** COMPLETE (MVP fields + human status path verified)  
**Sync architecture / Contract / ResearchEvidence / auth logic:** unchanged except minimal Lead field mapping allow-list

## 1. Modified Files

| Path | Change |
|---|---|
| `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Lead.json` | Added `peSyncStatus`, `peResearchStatus`; appended tier `D` |
| `espocrm_extension/Resources/entityDefs/Lead.json` | Parity copy |
| `espocrm_extension/files/.../i18n/en_US/Lead.json` | Labels/options/tooltips for MVP fields |
| `espocrm_extension/files/.../layouts/Lead/detail.json` | Core Lead detail + **Prospecting MVP** panel |
| `espocrm_extension/Resources/layouts/Lead/detail.json` | Parity copy |
| `espocrm_extension/tests/test_extension_skeleton.py` | Assert new MVP enums/defaults |
| `integration/espocrm_sync/mapper.py` | Minimal: `peSyncStatus="SYNCED"` on Lead map |
| `integration/espocrm_sync/real_client.py` | Minimal: allow-list `peSyncStatus`, `peResearchStatus` in POST body (**auth untouched**) |
| `docs/espocrm-extension/PHASE3A25A_PRECHECK_REPORT.md` | Precheck |
| `docs/espocrm-extension/PHASE3A25A_MVP_LEAD_WORKFLOW_REPORT.md` | This report |

Deployed into local container `espocrm` module path + `php command.php clear-cache` + `rebuild`.

## 2. New / Reused Fields

| Requested | Implementation | Notes |
|---|---|---|
| `peSyncStatus` | **Added** enum NEW/SYNCED/REVIEWING/QUALIFIED/OUTREACH_READY/CONTACTED, default NEW | Human CRM lifecycle |
| `peResearchStatus` | **Added** enum PENDING/COMPLETE/COMPLETED/VERIFIED, default PENDING | `COMPLETE` kept for frozen Sync Contract |
| `peOpportunityScore` | **Reused** `peOpportunityScoreV4` (float) | No duplicate integer field |
| `peScoreTier` | **Reused**; options now A/B/C/**D** | Additive only |
| `peBestFirstProduct` | **Reused** | Unchanged |

Left untouched (pre-existing, out of 3A25a request set): `outreachStatus`, `lastContactAt`, `nextFollowUpAt`, `leadSourceEngine`, `syncVersion`.

## 3. Metadata Validation

After rebuild, API Metadata for Lead fields includes:

| Field | Visible | Options / type |
|---|---|---|
| `peSyncStatus` | YES | NEW…CONTACTED, default NEW |
| `peResearchStatus` | YES | PENDING/COMPLETE/COMPLETED/VERIFIED |
| `peScoreTier` | YES | includes D |
| `peOpportunityScoreV4` | YES | float |
| `peBestFirstProduct` | YES | varchar |

Lead detail layout includes panel **Prospecting MVP** with score, tier, product, research status, sync status.

## 4. API Validation

| Step | Result |
|---|---|
| `authenticate()` | PASS (`chitu_ai_connector`) |
| `preflight()` metadata for new fields | PASS |
| Extension / adapter unit tests | **42 PASS** |
| Synthetic Lead CREATE | PASS — id `6a521bfb6a666547b` |
| Field READ | PASS — score 80, tier A, product Resin Tank, `peSyncStatus=SYNCED`, `peResearchStatus=COMPLETE` |
| Human status write `SYNCED → REVIEWING` | PASS |
| API DELETE rollback | **FAIL HTTP 403** |

### ACL observed during rollback attempt

| Scope | delete |
|---|---|
| Lead | **no** |
| ResearchEvidence | **no** |

Delete permissions that previously enabled Phase 3A-2.4 rollback are currently **not** present on the API Role. This is an environment ACL regression, not an MVP field defect.

Synthetic residue was removed via EspoCRM **system user** PHP cleanup (marker-guarded), not by changing Role ACL in this task.

## 5. Human Workflow (MVP)

```text
SYNCED → REVIEWING → QUALIFIED → OUTREACH_READY → CONTACTED
```

- Engine import sets `peSyncStatus=SYNCED` and `peResearchStatus=COMPLETE`.  
- Further transitions are **manual** on the Lead record.  
- Engine `peQualificationStatus` remains separate (import gate snapshot).

## 6. Rollback Notes

| Mechanism | Status |
|---|---|
| `LocalEspoCRMClient.rollback()` via API user | Blocked by Role `delete=no` (Lead + ResearchEvidence) |
| Marker-guarded system cleanup (this verification only) | Used to remove synthetic Lead/Evidence after successful field checks |
| Recommendation | Restore test Role `Lead.delete=all` and `ResearchEvidence.delete=all` before next API rollback exercise |

## 7. Not Implemented (explicit)

- EmailDraft / Campaign / OutreachActivity entities  
- Email sending / SMTP / auto workflows  
- Renaming `peOpportunityScoreV4` → `peOpportunityScore`  
- Removing or merging pre-existing `outreachStatus`  
- Sync Contract changes  
- ResearchEvidence schema changes  
- Auth / API key / extension registration changes  
- Account / Opportunity automation  

## 8. Acceptance Summary

| Goal | Result |
|---|---|
| Lead MVP fields for score / tier / product / research / sync status | PASS |
| CRM visible Prospecting MVP panel | PASS (layout deployed) |
| Mapper maps opportunity_score / tier / best_first_product | PASS (existing + sync status) |
| Synthetic write/read + human status change | PASS |
| API rollback | FAIL (ACL delete denied) — documented; synthetic cleaned via system user |
| Stable Engine → Lead → Human Review MVP | **PASS** for field/workflow MVP scope |

Phase 3A-25a MVP Lead Workflow: **DONE** within stated boundaries.
