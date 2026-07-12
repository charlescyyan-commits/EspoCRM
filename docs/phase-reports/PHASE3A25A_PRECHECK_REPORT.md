# Phase 3A-25a Precheck Report

**Date:** 2026-07-11  
**Scope:** Audit Lead metadata before MVP workflow fields  
**Code modified in this precheck:** NO

## 1. Current Lead pe* fields (live API)

| Field | Present | Type / notes |
|---|---|---|
| `peOpportunityScoreV4` | YES | float 0–100 |
| `peOpportunityScore` | NO | Requested name not present |
| `peScoreTier` | YES | enum `""`, A, B, C (no D) |
| `peBestFirstProduct` | YES | varchar |
| `peQualificationStatus` | YES | varchar (Engine snapshot) |
| `peConfidence` | YES | float |
| `peEvidenceCoverage` | YES | float |
| `peEngineVersion` | YES | varchar |
| `peScoreRulesVersion` | YES | varchar |
| `peSyncStatus` | NO | Missing — MVP add |
| `peResearchStatus` | NO | Missing in entityDefs (mapper already emits it) |

Core EspoCRM `status` remains: New / Assigned / In Process / Converted / Recycled / Dead (unchanged).

## 2. Naming / semantic conflicts

| Topic | Severity | Decision for 3A25a |
|---|---|---|
| `peOpportunityScore` vs existing `peOpportunityScoreV4` | Medium | **Reuse `peOpportunityScoreV4`.** Do not add duplicate `peOpportunityScore`. |
| `peScoreTier` missing `D` | Low | **Additive:** append `D` to options. |
| `peBestFirstProduct` | None | **Reuse.** |
| Mapper `peResearchStatus` = contract `COMPLETE` vs requested enum `COMPLETED` | Medium | **Add field** with options including both `COMPLETE` (Engine/contract) and `COMPLETED`/`VERIFIED`/`PENDING` (human). No Sync Contract change. |
| Pre-existing `outreachStatus` / `lastContactAt` / `nextFollowUpAt` / `leadSourceEngine` / `syncVersion` in module Lead.json | Medium | Already in extension source & container file; **outside 3A25a requested set.** Leave as-is; do not expand or remove. `peSyncStatus` still added as requested MVP field. |
| Dual workflow enums (`outreachStatus` vs `peSyncStatus`) | Medium | Documented risk; MVP still adds `peSyncStatus` because task names it explicitly. Human SOP should prefer `peSyncStatus` for 3A25a flow. |

## 3. Mapper / live POST capability

| Requested signal | Mapper today | Live POST (`_LEAD_FIELDS`) |
|---|---|---|
| opportunity_score | YES → `peOpportunityScoreV4` | YES |
| tier | YES → `peScoreTier` | YES |
| best_first_product | YES → `peBestFirstProduct` | YES |
| research status | YES → `peResearchStatus` | NO (not in `_LEAD_FIELDS`, field missing) |
| sync status | NO | NO |

## 4. Go / No-go

**GO with constrained MVP** (no architecture change):

1. Add `peSyncStatus` enum (NEW/SYNCED/REVIEWING/QUALIFIED/OUTREACH_READY/CONTACTED), default NEW.  
2. Add `peResearchStatus` enum (PENDING/COMPLETE/COMPLETED/VERIFIED), default PENDING — `COMPLETE` kept for frozen Sync Contract compatibility.  
3. Reuse `peOpportunityScoreV4`, `peScoreTier` (+D), `peBestFirstProduct`.  
4. Minimal mapper addition: set `peSyncStatus=SYNCED` on mapped Lead fields.  
5. Minimal real_client `_LEAD_FIELDS` allow-list add: `peSyncStatus`, `peResearchStatus` (no auth changes).  
6. i18n + Lead detail layout panel for CRM visibility.  

**Stop conditions not triggered** for core MVP; dual `outreachStatus` noted but does not block adding `peSyncStatus`.

## 5. Explicitly out of scope

- EmailDraft / Campaign / OutreachActivity  
- Mail send / auto workflow  
- Sync Contract edits  
- ResearchEvidence changes  
- Auth / API key / extension registration changes  
