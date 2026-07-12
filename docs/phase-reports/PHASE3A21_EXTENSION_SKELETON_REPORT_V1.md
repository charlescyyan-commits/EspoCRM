# Phase 3A-2.1 — EspoCRM Extension Skeleton Report V1

**Status:** COMPLETE — skeleton only  
**Date:** 2026-07-10  
**Package version:** `1.0.0-alpha`

## Scope

Implemented an installable EspoCRM extension skeleton under `espocrm_extension/`.

No Engine API, sync controller, authentication, webhook, automatic Lead/Account/Opportunity creation, email, AI call, database migration, or live CRM modification was performed.

## Created Directories

```text
espocrm_extension/
├── Resources/
│   ├── metadata/
│   ├── layouts/ResearchEvidence/
│   ├── entityDefs/
│   └── acl/
├── files/custom/Espo/Modules/Prospecting/
│   ├── Resources/
│   │   ├── metadata/{entityDefs,scopes,clientDefs,aclDefs}/
│   │   ├── layouts/ResearchEvidence/
│   │   └── i18n/en_US/
│   ├── Controllers/
│   ├── Services/
│   └── Api/
├── custom/Espo/Modules/Prospecting/{Controllers,Services,Api}/
├── application/
├── scripts/
├── docs/
└── tests/
```

## Created Files (primary)

| Path | Role |
|---|---|
| `espocrm_extension/manifest.json` | Extension manifest |
| `espocrm_extension/README.md` | Package overview |
| `Resources/entityDefs/ResearchEvidence.json` | Design-surface entity defs |
| `Resources/entityDefs/Lead.json` | Design-surface Lead overlay |
| `files/custom/Espo/Modules/Prospecting/Resources/**` | Installable EspoCRM module metadata |
| `custom/.../Controllers|Services|Api/README.md` | Sync placeholders for Phase 3A-2.2 |
| `tests/test_extension_skeleton.py` | Structure + contract validation |
| `docs/espocrm-extension/PHASE3A21_EXTENSION_SKELETON_REPORT_V1.md` | This report |
| `docs/espocrm-extension/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md` | Install / rollback guide |

## Entity List

| Entity | Type | Notes |
|---|---|---|
| `ResearchEvidence` | New custom entity | Compact evidence storage; not a scoring object |
| `Lead` | Metadata overlay only | Nullable Prospecting fields; Core Lead PHP untouched |

## Field Lists

### ResearchEvidence (CRM field → Sync Contract path)

| CRM field | Contract / mapping source |
|---|---|
| `name` | Generated label from claim (EspoCRM display requirement) |
| `peEvidenceId` | `evidence[].evidence_id` |
| `peClaim` | `evidence[].claim` |
| `peClaimType` | `evidence[].claim_type` |
| `peSourceUrl` | `evidence[].source_url` |
| `peEvidenceText` | `evidence[].evidence_text` |
| `peConfidence` | `evidence[].confidence` |
| `peCapturedAt` | `evidence[].captured_at` |
| `peSchemaVersion` | `evidence[].schema_version` |
| `peSnapshotHash` | `provenance.evidence_snapshot_hash` |
| `lead` | Parent Lead relationship |

Forbidden on evidence: score, ranking, AI result, email.

### Lead extension fields (all nullable)

| CRM field | Conceptual / contract source |
|---|---|
| `peOpportunityScoreV4` | `score.value` / opportunity_score_v4 |
| `peScoreTier` | `score.score_tier` |
| `peConfidence` | `score.aggregate_confidence` |
| `peEvidenceCoverage` | `score.evidence_coverage` |
| `peBestFirstProduct` | `recommendation.best_first_product` |
| `peQualificationStatus` | `qualification.status` |
| `peEngineVersion` | `provenance.engine_version` |
| `peScoreRulesVersion` | `score.rules_version` |

Historical Leads may leave all Prospecting fields null.

## Design Notes (recorded, not changed)

1. **Task brief `evidence_type` vs Sync Contract `claim_type`**  
   Sync Contract V1 and Entity Mapping use `claim_type` → `peClaimType`. Engine `EvidenceItem` also has a separate `evidence_type` (title/meta/visible_text). The skeleton maps `claim_type` only and does not add `peEvidenceType`. Architecture was not altered.

2. **CRM naming uses `pe*` camelCase**  
   Matches `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md`. Task brief snake_case names are conceptual aliases.

3. **Lead skeleton fields are a subset of the full mapping**  
   Phase 3A-2.1 defines only the eight Prospecting fields listed in the task. Additional mapping fields (`peCanonicalDomain`, `peSyncStatus`, etc.) remain deferred.

4. **`files/` vs `Files/`**  
   EspoCRM requires lowercase `files/`. Windows cannot host both `files/` and `Files/`. The skeleton uses `files/` plus top-level `application/` as the reserved application placeholder.

5. **Architecture plan vs task layout**  
   Phase 3A-1 architecture draft used `custom/Espo/Custom/`. This skeleton follows EspoCRM module packaging under `files/custom/Espo/Modules/Prospecting/` as required by Phase 3A-2.1. Sync Contract JSON was not modified.

## Not Implemented

- Engine API / import endpoint
- Controllers, Services, Api PHP
- Authentication / credentials
- Webhooks / queues
- Automatic sync
- Lead create/update logic
- Account creation / conversion
- Opportunity creation
- Email / SMTP
- AI calls
- Live EspoCRM install verification against a running instance
- Database schema rebuild against a real CRM

## Validation Checklist

| Check | Result |
|---|---|
| Extension skeleton created | YES |
| Manifest valid | YES |
| ResearchEvidence entity created | YES |
| Lead fields defined | YES |
| Core EspoCRM untouched | YES |
| Prospecting Engine untouched | YES |
| Database modified | NO |
| Real EspoCRM modified | NO |
| API implemented | NO |
| Sync implemented | NO |
| Emails sent | NO |
| Enter Phase 3A-2.2 | YES — skeleton prerequisite complete; separate explicit authorization still required for sync implementation |

## Next Phase Preparation (3A-2.2)

Ready once explicitly authorized:

1. Implement Controllers / Services / Api under the Prospecting module.
2. Validate against `ESPOCRM_SYNC_CONTRACT_V1.json` and sync rules.
3. Enforce OUTREACH_READY + V4-only gate.
4. Create/update Lead Engine-owned fields and ResearchEvidence snapshots only.
5. Keep Account / Opportunity human-only.
6. Use a disposable test CRM; no production writes.
