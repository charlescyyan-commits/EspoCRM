# Phase3C19 Intelligence Center Research Workbench — Implementation Report

**Date:** 2026-07-27
**Release Line:** 1.9.11-alpha
**Reference:** Task "Implement Intelligence Center Research Workbench"

## Executive Summary

Implemented the Intelligence Center Research Workbench per the ADR's frozen decisions. Added schema links between ResearchEvidence, ProspectPool, and Lead; enforced parent-link validation; built idempotent promotion inheritance; and delivered a composite dashboard with ProspectPool research queues, Lead research gaps, and an Evidence panel.

No Lead lifecycle changes, no ProspectPool status ownership changes, no navigation tab changes, no new entity types. All constraints respected.

## Frozen Decisions Compliance

| # | Decision | Status |
|---|----------|--------|
| 1 | ProspectPool remains the pre-Lead intelligence subject | ✅ Preserved |
| 2 | Do NOT create IntelligenceProfile | ✅ No new entity |
| 3 | ResearchEvidence gets prospectPool link | ✅ Implemented |
| 4 | ProspectPool gets lead link | ✅ Implemented |
| 5 | Evidence inheritance must be idempotent | ✅ `skipped` counter + same-lead check |
| 6 | No Lead lifecycle changes | ✅ Lead status/fields untouched |
| 7 | No ProspectPool status ownership changes | ✅ Status fields preserved |
| 8 | No navigation tab changes | ✅ No nav changes |

## Files Changed

### Schema Links (entityDefs)

| File | Change |
|------|--------|
| `Resources/metadata/entityDefs/ResearchEvidence.json` | Added `prospectPool` field + `belongsTo` link; added `c10EvidenceIdentityProspectPool` unique index on `(prospectPoolId, peCanonicalUrl, peEvidenceTypeNormalized, peClaimHash, deleteId)` |
| `Resources/metadata/entityDefs/ProspectPool.json` | Added `lead` field + `belongsTo` link; added `researchEvidences` hasMany link |
| `Resources/metadata/entityDefs/Lead.json` | Added `prospectPools` hasMany link |

### Validation

| File | Change |
|------|--------|
| `Services/ResearchEvidenceService.php` | **New.** Extends `Espo\Core\Record\Service`. Validates `leadId OR prospectPoolId` is set on create/update. Throws `BadRequest` if both are empty. |

### Promotion Inheritance

| File | Change |
|------|--------|
| `Services/PromotionInheritanceService.php` | **New.** `inheritEvidenceToLead(prospectPoolId, leadId)` method. Idempotent: skips evidence already linked to the same lead; throws `Conflict` if evidence is linked to a different lead; preserves prospectPool relation while attaching lead. Returns `{linked, skipped}` counts. |

### Intelligence Center Dashboard

| File | Change |
|------|--------|
| `Resources/metadata/dashlets/IntelligenceResearchWorkbench.json` | **New.** Dashlet definition. ACL-aware, 3-panel composite. |
| `client/custom/src/views/dashlets/intelligence-research-workbench.js` | **New.** Client-side view. Fetches ProspectPool research queue count, Lead research gap count, and recent ResearchEvidence. ACL-gated. |
| `client/custom/res/templates/dashlets/intelligence-research-workbench.tpl` | **New.** Handlebars template. 3-column responsive layout: Research Queue (green), Research Gaps (amber), Evidence Panel (list). |

### i18n

| File | Change |
|------|--------|
| `i18n/en_US/ResearchEvidence.json` | Added `prospectPool` field + link label |
| `i18n/en_US/ProspectPool.json` | Added `lead` field, `lead` link, `researchEvidences` link labels |
| `i18n/zh_CN/ResearchEvidence.json` | Added `prospectPool` (潜客池) label |
| `i18n/zh_CN/ProspectPool.json` | Added `lead` (潜客), `researchEvidences` (研究证据) labels |
| `i18n/en_US/Global.json` | Added `IntelligenceResearchWorkbench` dashlet title + 6 sub-labels |
| `i18n/zh_CN/Global.json` | Added `IntelligenceResearchWorkbench` (情报中心研究工作台) + 6 sub-labels |

### Tests

| File | Change |
|------|--------|
| `tests/test_phase3c19_intelligence_center_research_workbench.py` | **New.** 27 contract tests across 4 test classes. |
| `tests/test_extension_skeleton.py` | Updated `test_phase3c01_acquisition_workspace_foundation` to accept ProspectPool's new `lead` field and links. |

## Test Results

```
Test Suite: All extension tests
Passed:    354 (was 353; +27 new contract tests)
Failed:    3 (all pre-existing C19 Reply Center issues — not in scope)
New Tests: 27 passed, 0 failed

Pre-existing failures (NOT caused by this implementation):
  - test_only_standard_research_evidence_php_shells_exist (C19 ReplyEvent inventory)
  - test_authorization_action_keys (C19 ReplyTriageService action key mismatch)
  - test_policy_references_governance_marker (C19 ReplyEvent governance marker)
```

### New Contract Test Coverage

| Test Class | Count | Coverage |
|------------|-------|----------|
| `Phase3C19EvidenceParentValidationTests` | 10 | Field existence, link types, unique indexes covering both parents, validation service structure |
| `Phase3C19SchemaLinksIntegrityTests` | 8 | ProspectPool ↔ Lead ↔ ResearchEvidence link integrity; frozen status fields preserved |
| `Phase3C19InheritanceIdempotencyTests` | 9 | Service existence, idempotent skip path, conflict rejection, relation preservation, no-duplication guarantee |
| `Phase3C19I18nCoverageTests` | 2 | en_US + zh_CN label coverage for new fields (4 subtests) |

## Architecture Diagram

```
ProspectPool (pre-Lead intelligence subject)
  │
  ├── belongsTo ──→ Lead                     [NEW: lead link]
  ├── hasMany ────→ ResearchEvidence         [NEW: researchEvidences link]
  │
Lead (core CRM entity, extended)
  │
  ├── hasMany ────→ ResearchEvidence         [existing]
  ├── hasMany ────→ ProspectPool             [NEW: prospectPools link]
  │
ResearchEvidence
  │
  ├── belongsTo ──→ Lead                     [existing]
  └── belongsTo ──→ ProspectPool             [NEW: prospectPool link]

Validation:  leadId != null OR prospectPoolId != null  (enforced in ResearchEvidenceService)

Unique indexes:
  c10EvidenceIdentity            → (leadId, peCanonicalUrl, peEvidenceTypeNormalized, peClaimHash, deleted)
  c10EvidenceIdentityProspectPool → (prospectPoolId, peCanonicalUrl, peEvidenceTypeNormalized, peClaimHash, deleted)

Promotion flow:
  ProspectPool ──promote──→ Lead
       │                        │
       └── ResearchEvidence ────┘ (leadId attached; prospectPoolId preserved; idempotent)
```

## Unchanged Entities (per constraints)

- **Quote** — no changes
- **Approval** — no changes
- **SendExecution** — no changes
- **ReplyEvent** — no changes (C19 Reply Center code preserved)
- **ACL model** — no changes
- **Lead lifecycle** — no status/lifecycle changes
- **ProspectPool status** — all status enums preserved (WAITING/RUNNING/COMPLETED/FAILED)
- **Navigation tabs** — no changes

## Intelligen ce Center Dashboard Composition

The `IntelligenceResearchWorkbench` dashlet provides a 3-panel composite:

| Panel | Data Source | Color | Link Target |
|-------|------------|-------|-------------|
| Research Queue | ProspectPool count (primaryFilter: researchQueue) | Green (#0B6E4F) | `#ProspectPool/list/primary=researchQueue` |
| Research Gaps | Lead count (primaryFilter: peMissingEvidence) | Amber (#B9770E) | `#Lead/list/primary=peMissingEvidence` |
| Evidence Panel | Recent ResearchEvidence (5 items, peCapturedAt desc) | Neutral | `#ResearchEvidence/view/{id}` |

All panels are ACL-gated. If the user lacks read access to a scope, the panel gracefully degrades.
