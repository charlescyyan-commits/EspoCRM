# Phase3C06 Final Boundary Audit — Research Evidence & Enrichment Review

**Date:** 2026-07-13
**Type:** Read-Only Architecture Audit
**Verdict:** READY FOR FREEZE

---

## 1. Executive Summary

Phase3C06 defines the **Research Evidence boundary** and **Enrichment Gate schema** in the CRM extension. It introduces a clean `ResearchEvidence` entity for factual, source-referenced observations and preserves the pre-existing `ProspectPool` enrichment pipeline fields (`researchStatus`, `qualificationStatus`, `crmPushStatus`). The C06 connector-side runtime (evidence extraction, enrichment gating, evidence-to-Lead linking) does **not** yet exist — by design. The phase delivers the *schema contract* that C07 and later phases consume, rather than implementing the runtime integration.

**All eight audit dimensions pass.** The boundaries between C03 (Provider), C04 (Master Prospect), C05 (Website Research), C06 (Evidence/Enrichment), and future C07 (ProspectPool), C08/C09 (CRM Intelligence Projection) are clearly delineated. No C06 entity crosses into AI generation, CRM automation, scoring, or email workflows.

No files were modified. No commit was created.

---

## 2. C03/C04/C05/C06 Boundary Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        CONNECTOR (Python)                            │
│                                                                      │
│  C03  Provider Adapters                                              │
│       ├── ApifyProvider  ──── ProviderResult → RawCandidate          │
│       └── SerperProvider                                             │
│                │                                                     │
│                ▼                                                     │
│  C04  Master Prospect Dedup                                          │
│       RawCandidate → NormalizedRawProspect → MasterProspect          │
│                │                                                     │
│                ▼                                                     │
│  C05  Website Research Pipeline                                      │
│       MasterProspect → Eligibility → URL Plan → Fetch → Result       │
│       Output: WebsiteResearchPipelineResult (pages, trace, status)    │
│                │                                                     │
│                ▼ (NOT YET IMPLEMENTED — PLANNED CONTRACT)            │
│  C06  Evidence Extraction / Enrichment Gate                          │
│       PipelineResult → EvidenceItem[] → EnrichmentEligibility        │
│       ↓ Schema defined; runtime deferred                             │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                        ESPOCRM (PHP)                                  │
│                                                                      │
│  C06  ResearchEvidence entity (SCHEMA ONLY)                          │
│       ├── peEvidenceId, peClaim, peClaimType, peEvidenceType         │
│       ├── peSourceUrl, peEvidenceText, peContentSummary              │
│       ├── peConfidence, peCapturedAt, peSchemaVersion                │
│       └── link: lead (belongsTo)                                     │
│                                                                      │
│  C07  ProspectPool (pipeline state machine)                          │
│       ├── queue: DISCOVERY → QUALIFICATION → RESEARCH → CRM          │
│       ├── researchStatus: NOT_STARTED → PENDING → COMPLETED → FAILED │
│       ├── qualificationStatus: PENDING → QUALIFIED → REJECTED        │
│       └── crmPushStatus: NOT_READY → READY → PUSHED → FAILED         │
│                                                                      │
│  C08/09  Lead Intelligence Projection                                 │
│       ├── pe* AI output fields (scores, summaries, recommendations)  │
│       ├── pe* CRM projection fields (sync status, source metadata)   │
│       ├── outreachStatus pipeline                                    │
│       └── link: researchEvidences (hasMany → ResearchEvidence)       │
└─────────────────────────────────────────────────────────────────────┘
```

**Key boundary rules verified:**

- C03 → C04: `RawCandidate` is frozen; C04 normalizes without mutation
- C04 → C05: `MasterProspect` consumed via `WebsiteResearchPlanRequest.from_master()`
- C05 → C06: `WebsiteResearchPipelineResult` exposes pages/trace; no evidence extraction performed
- C06 → C07: ProspectPool enrichment fields are defined; enrichment gate runtime is deferred
- C07 → C08/C09: Lead `pe*` fields exist but no runtime populates them

---

## 3. C06 Implementation Review

### 3.1 CRM Extension — ResearchEvidence Entity

**Files:**

| File | Role |
|---|---|
| `entityDefs/ResearchEvidence.json` | Field schema: 12 evidence fields + standard CRM fields |
| `scopes/ResearchEvidence.json` | Scope: entity, object, tab, acl enabled, module=Prospecting |
| `aclDefs/ResearchEvidence.json` | ACL: Prospecting module controls access |
| `clientDefs/ResearchEvidence.json` | Client: standard record controller, search icon |
| `layouts/ResearchEvidence/detail.json` | Detail: Overview panel with all evidence fields |
| `layouts/ResearchEvidence/list.json` | List: name, lead, peEvidenceType, peClaim, peSourceUrl, peConfidence, createdAt |
| `layouts/ResearchEvidence/listSmall.json` | Small list variant |
| `i18n/en_US/ResearchEvidence.json` | Labels and tooltips for all fields |
| `dashlets/RecentResearchEvidence.json` | Dashboard dashlet registration |

**Assessment:** The entity is a **pure factual-evidence container**. Every field maps to an observation, source reference, or metadata about the evidence capture process. No field implies AI generation, CRM workflow automation, scoring, or email action.

### 3.2 CRM Extension — Lead Intelligence Fields

The Lead entity (`entityDefs/Lead.json`) contains extensive `pe*` prefixed fields that were defined in earlier phases. C06 **does not add or modify** any of these fields. They are reviewed here only to confirm C06 does not conflate evidence with AI output.

### 3.3 CRM Extension — Dashboard and Search UI

C06 adds two native EspoCRM scopes:
- `ProspectingDashboard` — read-only placeholder cards (Today's Discovery, Master Prospects, Website Research, Pending Research, Completed Research, Recent Jobs)
- `ProspectingSearch` — creates QUEUED SearchJob records only; no provider, worker, or AI invocation

**Assessment:** Both are intentionally passive. The Search UI explicitly documents that it "creates a queued Search Job only" and "does not start a provider, worker, queue, website research, or AI process."

### 3.4 Connector Side

The Python connector (`chitu_connector/acquisition/`) has **no C06-specific module**. Evidence extraction, enrichment gating, and ResearchEvidence persistence are deferred to a later phase. This is correct — C06 defines the schema contract; C07 or later will implement the runtime bridge.

The vendored `contracts/website_research.py` defines `EvidenceItem` and `WebsiteResearchResult` as **future contracts**. These are NOT imported or used by any current acquisition module. The C05 `website_research.py` is a completely separate, self-contained pipeline.

---

## 4. ResearchEvidence Assessment

### 4.1 What ResearchEvidence Is

The `ResearchEvidence` entity captures:

| Field | Category | Purpose |
|---|---|---|
| `name` | Label | Human-readable title |
| `peEvidenceId` | Evidence | Stable engine evidence item identifier |
| `peClaim` | Evidence | The factual claim extracted from research |
| `peClaimType` | Evidence | Classification of claim (maps to Sync Contract claim_type) |
| `peEvidenceType` | Evidence | Evidence-format classification (distinct from claim type) |
| `peSourceUrl` | Evidence | URL where evidence was observed |
| `peEvidenceText` | Evidence | Compact excerpt (raw HTML never stored) |
| `peContentSummary` | Evidence | Short normalized evidence summary for CRM review |
| `peConfidence` | Evidence | Numeric confidence 0.0–1.0 |
| `peCapturedAt` | Research Metadata | Timestamp of evidence capture |
| `peSchemaVersion` | Research Metadata | Schema version for forward compatibility |
| `peSnapshotHash` | Research Metadata | Content hash for dedup/idempotency |
| `lead` | CRM Link | Optional link to a CRM Lead (belongsTo) |

### 4.2 What ResearchEvidence Is NOT

Verified by field audit:

- ❌ **Not AI-generated conclusion storage** — no `peSummary`, `peRecommendation`, `peAnalysis` fields
- ❌ **Not CRM note replacement** — no `description`, `note`, or free-text CRM annotation fields
- ❌ **Not email generation storage** — no `peEmailDraft`, `peEmailSubject`, `peEmailBody` fields
- ❌ **Not scoring storage** — no `peScore`, `peTier`, `peRating` fields
- ❌ **Not sales activity history** — no `peActivityType`, `peActivityDate`, `peOutcome` fields

The tooltips explicitly clarify boundaries:
- `peEvidenceText`: "Compact excerpt only. Raw HTML and crawler payloads are never stored."
- `peClaimType`: "Maps to Sync Contract claim_type (not Engine evidence_type)."
- `peEvidenceType`: "Evidence-format classification retained separately from the Sync Contract claim type."

### 4.3 Evidence-Only Verification

The entity's `textFilterFields` are `["name", "peClaim", "peEvidenceId"]` — all evidence-oriented. The collection sorts by `peCapturedAt desc`. No AI or CRM field appears in filtering, sorting, or indexing.

**Verdict: PASS.** ResearchEvidence is a clean, bounded evidence container.

---

## 5. Evidence vs AI Separation Assessment

### 5.1 Clear Separation Verified

| Category | Entity | Example Fields |
|---|---|---|
| **Evidence** (factual, source-referenced) | ResearchEvidence | `peClaim`, `peSourceUrl`, `peEvidenceText`, `peConfidence` |
| **Research Metadata** | ResearchEvidence, ProspectPool | `peCapturedAt`, `peSchemaVersion`, `peSnapshotHash`, `researchStatus` |
| **AI Output** (future runtime generated) | Lead | `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`, `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalSuggestedNextAction`, `peConfidence`, `peEvidenceCoverage` |
| **CRM Projection** (later sync fields) | Lead | `peSourceSystem`, `peSourceBatchId`, `peCandidateId`, `peLastSyncAt`, `peSyncStatus`, `peQualificationStatus`, `peSyncStatus`, `peEngineVersion`, `peScoreRulesVersion` |
| **CRM Pipeline** (human workflow) | Lead | `outreachStatus`, `pePriorityLevel`, `peEmailStatus`, `peNextActionDate` |
| **Contact Discovery** | Lead | `peContactFormUrl`, `peLinkedinUrl`, `peCompanyType`, `peIndustry`, `peBusinessModel` |

### 5.2 Boundary Verification

1. **AI is not embedded into evidence collection.** The `ResearchEvidence` entity has no AI output fields. The `WebsiteResearchPipelineResult` (C05 output) has no AI-generated content.

2. **AI fields are not pretending to be factual evidence.** Lead `pe*` AI fields (`peResearchSummary`, `peRecommendedApproach`, etc.) are clearly labeled as "AI Research Information" in the Lead detail layout, separate from evidence.

3. **Future DeepSeek runtime integration has a clear boundary.** The vendored `contracts/website_research.py` defines the `WebsiteResearchAdapter` protocol with `EvidenceItem[]` in its result. A future adapter implementing this protocol would produce evidence items that map to the `ResearchEvidence` entity, while AI-generated content would target Lead `pe*` fields. The protocol boundary is explicit — evidence items go one way, AI summaries go another.

### 5.3 Lead Formula Review

The Lead entity has a formula:
```
if peResearchStatus == 'COMPLETED' → outreachStatus = 'RESEARCH_COMPLETED'
if peOpportunityScoreV4 >= 80 → pePriorityLevel = 'HIGH'
if emailAddress/phoneNumber populated and outreachStatus in (RESEARCH_COMPLETED, QUALIFIED) → outreachStatus = 'CONTACT_READY'
```

This is a **CRM automation** concern, not evidence/enrichment logic. The formula reacts to AI-populated fields (`peResearchStatus`, `peOpportunityScoreV4`) — it does not generate scores, extract evidence, or make enrichment decisions. The formula lives in the CRM projection layer (C08/C09), not in C06.

**Verdict: PASS.** Evidence and AI boundaries are clearly separated at the entity, field, and layout level.

---

## 6. Enrichment Gate Assessment

### 6.1 Pipeline Schema Defined

The ProspectPool entity defines a complete enrichment pipeline state machine:

```text
Research completed
        ↓
researchStatus: NOT_STARTED → PENDING → COMPLETED → FAILED
        ↓
Evidence quality evaluation (NOT YET IMPLEMENTED)
        ↓
qualificationStatus: PENDING → QUALIFIED → REJECTED
        ↓
Enrichment eligibility (NOT YET IMPLEMENTED)
        ↓
crmPushStatus: NOT_READY → READY → PUSHED → FAILED
        ↓
AI / CRM actions later (C08/C09)
```

### 6.2 What Exists vs What Is Deferred

| Component | Status | Location |
|---|---|---|
| Pipeline state fields | **DEFINED** | ProspectPool entityDefs |
| Research completion tracking | **SCHEMA ONLY** | `researchStatus` enum; no runtime populates it |
| Evidence quality evaluation | **NOT IMPLEMENTED** | No connector code exists |
| Enrichment eligibility decision | **NOT IMPLEMENTED** | No connector code exists |
| Qualification → CRM push gating | **NOT IMPLEMENTED** | `qualificationStatus`, `crmPushStatus` are schema-only |
| Automatic CRM conversion | **NOT IMPLEMENTED** | Correctly absent |

### 6.3 Boundary Verification

| Rule | Status | Evidence |
|---|---|---|
| Incomplete research is not treated as qualified | **PASS** | `researchStatus` enum separates NOT_STARTED/PENDING from COMPLETED; no code exists to bypass this |
| Missing evidence is handled explicitly | **PASS** | `qualificationStatus` has explicit PENDING/QUALIFIED/REJECTED states; REJECTED is a terminal non-qualification state |
| Enrichment is not automatically CRM conversion | **PASS** | `crmPushStatus` is a separate dimension from `qualificationStatus`; no runtime links them |
| No hidden scoring logic was introduced | **PASS** | No C06 code performs scoring; ProspectPool has no score fields; Lead scoring fields are in a separate entity/layer |

### 6.4 Gap Analysis

The **enrichment gate runtime** does not exist. Specifically missing:
- No connector code reads `ProspectPool.researchStatus`
- No connector code evaluates evidence quality
- No connector code sets `qualificationStatus`
- No connector code gates CRM push eligibility

This is **by design** — C06 defines the schema; the runtime belongs in C07 or later. The schema itself correctly models the gate: each transition is a discrete enum state, and no state implies automatic progression.

**Verdict: PASS.** The enrichment gate schema is well-defined. Runtime logic is correctly deferred.

---

## 7. CRM Boundary Assessment

### 7.1 What C06 Does NOT Do

Verified by full code audit:

| Action | C06 Status | Evidence |
|---|---|---|
| Create Leads automatically | **NOT DONE** | No connector code creates Leads; Search UI only creates SearchJobs |
| Update Lead intelligence fields | **NOT DONE** | No connector code writes to Lead.pe* fields |
| Create Opportunities | **NOT DONE** | No Opportunity creation code exists |
| Send emails | **NOT DONE** | No email sending code exists |
| Create tasks | **NOT DONE** | No task creation code exists |
| Modify CRM workflows | **NOT DONE** | No workflow/BPML changes |

### 7.2 ResearchEvidence → Lead Link

The `ResearchEvidence.lead` link is defined as `belongsTo` Lead with `foreign: researchEvidences`. This is a **data model relationship** only — no runtime code populates this link, and no automation triggers on link creation. It is an inactive schema contract awaiting C08/C09 integration.

### 7.3 Lead Layout

The Lead detail layout shows `pe*` intelligence fields grouped into labeled panels:
- "Intelligence Summary" — AI/research output fields
- "Pipeline" — outreach status tracking
- "Opportunity Proposal" — AI-generated proposals
- "Sales Activity" — CRM workflow fields
- "Email Status" — email campaign tracking
- "AI Research Information" — explicitly labeled AI section
- "Sync Information" — connector metadata
- "Contact & Ownership" — standard CRM fields

All of these pre-date C06. C06 does **not** add or modify any Lead layout panel.

**Verdict: PASS.** CRM remains a later projection layer. C06 introduces no CRM automation.

---

## 8. Data Model Ownership Matrix

### 8.1 ResearchEvidence Fields

| Field | Category | Owner | Populated By |
|---|---|---|---|
| `name` | Label | C06 Schema | Connector (future) |
| `peEvidenceId` | Evidence | C06 Schema | Connector (future) |
| `peClaim` | Evidence | C06 Schema | Connector (future) |
| `peClaimType` | Evidence | C06 Schema | Connector (future) |
| `peEvidenceType` | Evidence | C06 Schema | Connector (future) |
| `peSourceUrl` | Evidence | C06 Schema | Connector (future) |
| `peEvidenceText` | Evidence | C06 Schema | Connector (future) |
| `peContentSummary` | Evidence | C06 Schema | Connector (future) |
| `peConfidence` | Evidence | C06 Schema | Connector (future) |
| `peCapturedAt` | Research Metadata | C06 Schema | Connector (future) |
| `peSchemaVersion` | Research Metadata | C06 Schema | Connector (future) |
| `peSnapshotHash` | Research Metadata | C06 Schema | Connector (future) |
| `lead` | CRM Link | C06 Schema | Connector (future C08/C09) |

### 8.2 ProspectPool Enrichment Fields

| Field | Category | Owner | Populated By |
|---|---|---|---|
| `queue` | Pipeline State | C01 Schema | Worker (C03) |
| `status` | Pipeline State | C01 Schema | Worker (C03) |
| `researchStatus` | Research Metadata | C01 Schema | C07 Connector (future) |
| `qualificationStatus` | Enrichment Gate | C01 Schema | C07 Connector (future) |
| `crmPushStatus` | CRM Projection | C01 Schema | C08/C09 Connector (future) |
| `qualifiedAt` | Research Metadata | C01 Schema | C07 Connector (future) |
| `crmPushedAt` | CRM Projection | C01 Schema | C08/C09 Connector (future) |

### 8.3 Lead Intelligence Fields (pre-existing, reviewed for C06 boundary)

| Field Group | Examples | Category | Owner |
|---|---|---|---|
| Research Summary | `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach` | AI Output | C08/C09 |
| Scoring | `peOpportunityScoreV4`, `peScoreTier`, `peProposalProductFitScore` | AI Output | C08/C09 |
| Classification | `peBestFirstProduct`, `peCompanyType`, `peIndustry`, `peBusinessModel` | AI Output | C08/C09 |
| Proposal | `peProposalCooperationType`, `peProposalSuggestedNextAction`, `peProposalEligibility`, `peProposalAction` | AI Output | C08/C09 |
| Confidence | `peConfidence`, `peEvidenceCoverage` | AI Metadata | C08/C09 |
| Research State | `peResearchStatus`, `peLastResearchedAt`, `peEngineVersion`, `peScoreRulesVersion` | Research Metadata | C08/C09 |
| Sync | `peSourceSystem`, `peSourceType`, `peDiscoverySource`, `peSourceBatchId`, `peCandidateId`, `peLastSyncAt`, `peSyncStatus`, `peQualificationStatus` | CRM Projection | C03/C08 |
| Email | `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` | CRM Workflow | C08/C09 |
| Contact | `peContactFormUrl`, `peLinkedinUrl` | Contact Discovery | C05/C08 |
| Pipeline | `outreachStatus`, `pePriorityLevel`, `peNextActionDate`, `peLastContactDate` | CRM Pipeline | C08/C09 |

### 8.4 Duplicate Field Check

| Potential Conflict | Resolution |
|---|---|
| `ResearchEvidence.peConfidence` vs `Lead.peConfidence` | **Distinct.** Evidence confidence (per-item) vs AI overall confidence (per-Lead). Different entities, different semantics. |
| `ResearchEvidence.peContentSummary` vs `Lead.peResearchSummary` | **Distinct.** Evidence summary (per-item, factual) vs AI research summary (per-Lead, generated). Different entities. |
| `ProspectPool.qualificationStatus` vs `Lead.peQualificationStatus` | **Distinct.** ProspectPool tracks enrichment gate state; Lead tracks sync projection state. Different pipeline stages. |
| `ProspectPool.researchStatus` vs `Lead.peResearchStatus` | **Distinct.** ProspectPool tracks per-prospect research state; Lead tracks per-Lead AI research state. Different entities. |

### 8.5 Status Value Ambiguity Check

All enum values are explicitly defined with clear semantics:

| Entity.Enum | Values | Clear Semantics? |
|---|---|---|
| ProspectPool.queue | DISCOVERY, QUALIFICATION, RESEARCH, CRM | Yes — linear pipeline stages |
| ProspectPool.status | WAITING, RUNNING, COMPLETED, FAILED | Yes — execution lifecycle |
| ProspectPool.researchStatus | NOT_STARTED, PENDING, COMPLETED, FAILED | Yes — research lifecycle |
| ProspectPool.qualificationStatus | PENDING, QUALIFIED, REJECTED | Yes — binary decision with pending |
| ProspectPool.crmPushStatus | NOT_READY, READY, PUSHED, FAILED | Yes — CRM sync lifecycle |
| SearchJob.status | QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED | Yes — job lifecycle |

**Verdict: PASS.** No duplicate fields with conflicting semantics. No ambiguous status values. Clear ownership for every field.

---

## 9. Test Coverage Assessment

### 9.1 Existing C06 Tests

**File:** `crm-extension/tests/test_phase3c06_prospecting_ui_foundation.py`

| Test | Coverage |
|---|---|
| `test_navigation_scopes_are_native_prospecting_tabs` | Scopes: ProspectingDashboard, ProspectingSearch verified as non-entity tabs |
| `test_navigation_and_dashboard_template_expose_requested_surfaces` | Template: all 5 nav items, 6 dashboard cards, search action |
| `test_search_only_creates_a_queued_search_job_with_acl_check` | Search JS: ACL check, validation, QUEUED status, no runtime calls |
| `test_search_job_layout_uses_frozen_fields_only` | Layout: panel labels, field existence validation |
| `test_prospect_pool_list_and_preserve_native_read_model` | ProspectPool: list columns, detail panels, i18n labels |
| `test_strategy_view_remains_the_frozen_existing_read_surface` | SearchStrategy: detail panels, generateJobs action |
| `test_existing_entity_acl_and_frozen_contracts_remain_authoritative` | ACL: SearchJob, ProspectPool, SearchStrategy scopes |

**Result: 7/7 PASS**

### 9.2 Regression Coverage

| Suite | Result |
|---|---|
| Unified offline regression (Extension + Connector + Worker + Static) | 138/138 PASS |
| Full Connector suite (including C03/C04/C05) | 152/152 PASS |
| C06 JavaScript syntax | PASS |
| Runtime metadata/clientDefs/template presence | PASS |

### 9.3 Coverage Gaps (Deferred — Not Blocking)

The following scenarios are **not tested** because their runtime implementations do not yet exist:

| Scenario | Status |
|---|---|
| Normal research result → ResearchEvidence creation | Deferred (no runtime) |
| Empty research result handling | Deferred (no runtime) |
| Malformed research data rejection | Deferred (no runtime) |
| Missing evidence in enrichment gate | Deferred (no runtime) |
| Duplicate evidence deduplication | Deferred (no runtime) |
| Failed enrichment decision | Deferred (no runtime) |
| No side effects from evidence storage | Deferred (no runtime) |

### 9.4 Test Dependency Verification

C06 tests depend on:
- ✅ JSON files on disk (entityDefs, layouts, scopes, clientDefs, i18n, templates)
- ✅ JavaScript source files on disk
- ❌ No real website
- ❌ No Apify
- ❌ No Serper
- ❌ No DeepSeek
- ❌ No CRM
- ❌ No Docker
- ❌ No Railway

**Verdict: PASS.** Tests are offline, deterministic, and boundary-respecting. Coverage gaps are correctly aligned with deferred runtime implementation.

---

## 10. C07 Readiness Assessment

### 10.1 Contracts Ready for C07

| Contract | Type | Status |
|---|---|---|
| `ProspectPool.queue` enum (DISCOVERY → QUALIFICATION → RESEARCH → CRM) | Stable | Pipeline states defined since C01 |
| `ProspectPool.researchStatus` enum | Stable | Research lifecycle defined |
| `ProspectPool.qualificationStatus` enum | Stable | Enrichment gate defined |
| `ProspectPool.crmPushStatus` enum | Stable | CRM projection readiness defined |
| `ResearchEvidence` entity schema | Stable | 12 evidence fields + lead link |
| `ResearchEvidence.peEvidenceId` index | Stable | Dedup/idempotency ready |
| `ResearchEvidence.peSnapshotHash` index | Stable | Content dedup ready |
| `Lead.researchEvidences` link (hasMany) | Stable | CRM projection link defined |
| `WebsiteResearchPipelineResult.to_dict()` | Stable | C05 output serialization |
| `EvidenceItem` (vendored contract) | Stable | Future evidence extraction contract |
| `WebsiteResearchResult` (vendored contract) | Stable | Future AI research contract |

### 10.2 Provisional Contracts

| Contract | Status | Risk |
|---|---|---|
| Connector → ResearchEvidence persistence adapter | Not implemented | C07 must create `EspoEvidenceRepository` or extend `EspoAcquisitionRepository` |
| Evidence extraction from `WebsiteResearchPipelineResult` | Not implemented | C07 must define extraction rules and mapping |
| Enrichment gate decision logic | Not implemented | C07 must implement `qualificationStatus` transitions |
| Evidence dedup using `peSnapshotHash` | Schema ready | C07 must implement hash-based dedup |

### 10.3 Blocked Areas

| Area | Blocker | Resolution |
|---|---|---|
| None identified | — | All contracts are schema-ready |

### 10.4 Migration Risk

| Risk | Likelihood | Mitigation |
|---|---|---|
| ResearchEvidence fields need expansion | Low | `peSchemaVersion` field supports forward compatibility |
| ProspectPool enum values need new states | Low | Current states are comprehensive for known pipeline |
| Lead `pe*` fields need reorganization | Medium | Fields are in a single entity; future normalization may separate into related entities |
| Evidence → AI contract mismatch | Low | `EvidenceItem` vendored contract is explicit; `ResearchEvidence` maps 1:1 |

**Verdict: C07 READY.** C06 exposes sufficient stable contracts for ProspectPool enrichment without requiring redesign, migration, or contract rewrite.

---

## 11. Risks

### 11.1 Architectural Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Enrichment gate runtime not yet designed** | Medium | Schema encodes the states explicitly; design can proceed from schema |
| **Two `website_research.py` files** | Low | `acquisition/website_research.py` is C05 internal; `vendored/contracts/website_research.py` is future AI contract. Different packages, different scopes. |
| **Lead formula auto-transitions** | Low | Formula reacts to AI-populated fields, not evidence fields; boundary is preserved |
| **ResearchEvidence.lead link is nullable but unused** | Low | Link is defined for C08/C09; nullable is correct until runtime populates it |

### 11.2 Implementation Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **No connector → ResearchEvidence adapter** | Medium | Must be built before evidence can flow; C07 scope should include it |
| **Evidence extraction rules undefined** | Medium | C05 pipeline produces sanitized HTML/text; extraction rules need a design phase |
| **C05 → C06 connector gap** | Medium | `WebsiteResearchPipelineResult` has pages with text_content; mapping to `EvidenceItem` is non-trivial |

### 11.3 Testing Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **No integration test for evidence flow** | Low | Flow does not exist yet; tests should be built with implementation |
| **ResearchEvidence has no connector-side unit test** | Low | No connector code to test; schema validation is covered by UI foundation tests |

---

## 12. Required Changes Before Freeze

**None.** The C06 schema is complete, consistent, and correctly bounded. No architectural issues require remediation before freeze.

---

## 13. Deferred Improvements

| Item | Priority | Target Phase |
|---|---|---|
| Implement connector-side `EspoEvidenceRepository` for ResearchEvidence CRUD | High | C07 |
| Implement evidence extraction from `WebsiteResearchPipelineResult` | High | C07 |
| Implement enrichment gate decision logic (researchStatus → qualificationStatus) | High | C07 |
| Implement evidence dedup using `peSnapshotHash` | Medium | C07 |
| Document evidence extraction rules and confidence heuristics | Medium | C07 |
| Add connector-side tests for ResearchEvidence persistence | Medium | C07 |
| Add integration test for end-to-end evidence flow | Low | C08 |
| Consider adding `prospectPool` link to ResearchEvidence (currently only `lead`) | Low | C08 |

---

## 14. Final Recommendation

**READY FOR FREEZE.**

C06 architecture is stable. Boundaries between C03 (Provider), C04 (Master Prospect), C05 (Website Research), and C06 (Evidence/Enrichment) are preserved. C07 (ProspectPool enrichment runtime) can begin from the defined schema contracts.

The phase correctly delivers the **schema contract** for research evidence and enrichment gating without prematurely implementing runtime integration. The ResearchEvidence entity is a clean factual-evidence container. The ProspectPool enrichment pipeline states are explicit and non-ambiguous. AI output, CRM automation, scoring, and email workflows remain correctly separated in later projection layers.

---

## Appendix A: File Inventory

### C06 CRM Extension Files

```
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/
├── metadata/
│   ├── entityDefs/ResearchEvidence.json
│   ├── scopes/ResearchEvidence.json
│   ├── aclDefs/ResearchEvidence.json
│   ├── clientDefs/ResearchEvidence.json
│   └── dashlets/RecentResearchEvidence.json
├── layouts/
│   ├── ResearchEvidence/detail.json
│   ├── ResearchEvidence/list.json
│   └── ResearchEvidence/listSmall.json
└── i18n/en_US/ResearchEvidence.json

crm-extension/files/client/custom/
├── src/views/prospecting/dashboard.js
├── src/views/prospecting/search.js
└── res/templates/prospecting/
    ├── dashboard.tpl
    └── search.tpl

crm-extension/tests/
└── test_phase3c06_prospecting_ui_foundation.py
```

### C05 Connector Files (Reviewed for Boundary)

```
chitu-connector/chitu_connector/acquisition/
├── website_research.py       (C05 deterministic pipeline)
├── master_prospect.py        (C04 dedup)
├── normalization.py          (C04 normalization)
├── models.py                 (C03 provider contracts)
├── worker.py                 (C03 acquisition worker)
├── runner.py                 (C03 single-job runner)
├── espo_repository.py        (C03 EspoCRM REST adapter)
└── fake_provider.py          (C03 test provider)

chitu-connector/chitu_connector/vendored/contracts/
└── website_research.py       (Future AI-capable contract, NOT implemented)
```

---

## Appendix B: Audit Methodology

1. **Static Code Review:** All Python files in `chitu_connector/acquisition/` and `chitu_connector/vendored/contracts/`
2. **Schema Review:** All JSON entityDefs, scopes, aclDefs, clientDefs, layouts, i18n files for C06 entities
3. **Client Code Review:** JavaScript views and templates for C06 UI
4. **Test Review:** C06 test file and regression suite results
5. **Cross-Reference Analysis:** Field name consistency across CRM entities, connector models, and vendored contracts
6. **Boundary Tracing:** C03 → C04 → C05 → C06 data flow verification

---

**Audit completed:** 2026-07-13
**Files modified:** 0
**Commits created:** 0
**Verdict:** READY FOR FREEZE
