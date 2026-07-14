# Phase3C07 — Evidence Extraction Architecture Audit

**Date:** 2026-07-13
**Type:** Read-Only Architecture Audit
**Scope:** Evidence extraction pipeline from Website Research through AI, Scoring, to CRM Projection
**Verdict:** READY — C07 has sufficient upstream contracts and downstream consumers to begin design

---

## 1. Current Architecture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         CONNECTOR (Python)                                 │
│                                                                           │
│  C03  Provider Adapters                                                    │
│       └── ProviderResult → RawCandidate                                    │
│                   │                                                        │
│                   ▼                                                        │
│  C04  Master Prospect Dedup                                                │
│       └── MasterProspect {master_id, normalized_domain, website, ...}      │
│                   │                                                        │
│                   ▼                                                        │
│  C05  Website Research Pipeline (INTERNAL, IMPLEMENTED)                    │
│       └── WebsiteResearchPipelineResult {                                  │
│             pages: WebsiteResearchPageResult[]  ← raw pages with text      │
│             trace: WebsiteResearchPipelineTrace[] ← fetch/classify log     │
│             research_status: ResearchStatus                                │
│           }                                                                │
│                   │                                                        │
│                   ▼  ═══════ C07 BOUNDARY ═══════                         │
│                                                                           │
│  C07  Evidence Extraction (NOT YET IMPLEMENTED)                            │
│       ┌─────────────────────────────────────────────────────┐             │
│       │  Input:  WebsiteResearchPipelineResult (C05)        │             │
│       │  Output: EvidenceItem[]  (vendored contract)        │             │
│       │          WebsiteResearchResult (vendored contract)  │             │
│       │          ResearchEvidence[] → EspoCRM (schema ready)│             │
│       │  Gate:   EnrichmentEligibility                      │             │
│       └─────────────────────────────────────────────────────┘             │
│                   │                                                        │
│                   ▼                                                        │
│  C08  AI Research (FUTURE)                                                 │
│       └── Input: EvidenceItem[] + WebsiteResearchPageResult.text_content   │
│       └── Output: company_summary, detected_brands, detected_products,     │
│                    customer_type_candidates, business_signals              │
│                   │                                                        │
│                   ▼                                                        │
│  C09  Scoring (FUTURE)                                                     │
│       └── Input: WebsiteResearchResult + EvidenceItem[]                    │
│       └── Output: CanonicalScoreResult {opportunity_score, score_tier,     │
│                    best_first_product, evidence_refs, component_traces}    │
│                   │                                                        │
│                   ▼                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                         ESPOCRM (PHP)                                       │
│                                                                           │
│  C06  ResearchEvidence (SCHEMA READY)                                      │
│       ├── peEvidenceId, peClaim, peClaimType, peEvidenceType               │
│       ├── peSourceUrl, peEvidenceText, peContentSummary                    │
│       ├── peConfidence, peCapturedAt, peSchemaVersion, peSnapshotHash      │
│       └── lead (belongsTo) ← linked by C08/C09 connector                   │
│                                                                           │
│  C08/09  Lead Intelligence Fields (SCHEMA READY)                           │
│       ├── peResearchSummary, peKeyEvidence, peRecommendedApproach (AI)     │
│       ├── peOpportunityScoreV4, peScoreTier, peBestFirstProduct (Score)    │
│       ├── peConfidence, peEvidenceCoverage (Metadata)                      │
│       └── researchEvidences (hasMany → ResearchEvidence)                   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Website Research → Evidence Input Link

### 2.1 C05 Output Analysis

`WebsiteResearchPipelineResult` (from `chitu_connector/acquisition/website_research.py`):

| Field | Type | Evidence-Relevant? | Notes |
|---|---|---|---|
| `master_id` | str | Yes | Links evidence to MasterProspect |
| `normalized_domain` | str\|None | Yes | Domain identity for dedup |
| `canonical_name` | str\|None | Yes | Company name for grouping |
| `root_url` | str\|None | Yes | Base URL for source attribution |
| `pages` | tuple[WebsiteResearchPageResult, ...] | **PRIMARY** | Raw material for evidence extraction |
| `research_status` | ResearchStatus | Yes | Eligibility/failure → evidence gating |
| `successful_page_count` | int | Yes | Evidence quantity signal |
| `failed_page_count` | int | Yes | Evidence quality signal |
| `selected_page_types` | tuple[PageType, ...] | Yes | Page type distribution |
| `started_at` | str | Metadata | Timestamp |
| `completed_at` | str | Metadata | Timestamp |
| `trace` | tuple[WebsiteResearchPipelineTrace, ...] | Yes | Audit trail per page |

Per-page fields in `WebsiteResearchPageResult`:

| Field | Type | Evidence Potential | Notes |
|---|---|---|---|
| `requested_url` | str | Source URL | Maps to `peSourceUrl` |
| `final_url` | str\|None | Redirect chain endpoint | |
| `page_type` | PageType | Claim classification | HOME/ABOUT/CONTACT/PRODUCTS/BRANDS/OTHER → claim_type |
| `title` | str\|None | **Evidence text** | Page title as evidence |
| `text_content` | str\|None | **Primary evidence source** | Sanitized visible text (≤100KB) |
| `raw_html` | str\|None | **Source material** | For AI extraction (not stored in CRM) |
| `meta_description` | str\|None | Evidence | Page description |
| `links` | tuple[str, ...] | Contact/social discovery | |
| `fetch_status` | FetchStatus | Evidence gating | Only SUCCESS pages produce evidence |
| `error` | WebsiteResearchError\|None | Failure classification | |
| `status_code` | int\|None | Metadata | HTTP status |
| `content_type` | str\|None | Metadata | |
| `redirect_chain` | tuple[str, ...] | Trace | |
| `fetched_at` | str | Timestamp | |
| `classification_reason` | str | Audit | Why this page type |
| `sanitization_actions` | tuple[str, ...] | Audit | What was cleaned |

### 2.2 Information Sufficiency

| Assessment | Verdict |
|---|---|
| **Field sufficiency for factual evidence** | ✅ Sufficient — `text_content`, `title`, `meta_description`, `page_type`, `requested_url`, `links` provide all source material needed for deterministic and AI extraction |
| **Field sufficiency for confidence scoring** | ✅ Sufficient — `fetch_status`, `page_type`, `classification_reason`, trace completeness |
| **Field sufficiency for audit trail** | ✅ Sufficient — `trace`, `redirect_chain`, `sanitization_actions`, `fetched_at` |
| **Information loss risk** | ⚠️ LOW — `raw_html` is retained in the result; C05 truncates `text_content` at 100KB. Very large pages lose tail content but this is a bounded safety measure. |

### 2.3 Fields Needed by Evidence Extraction (Not in C05 Output)

| Missing Field | Needed By | Mitigation |
|---|---|---|
| Evidence-level confidence heuristic | C07 Extractor | C07 must compute from page-level signals (fetch status, page type, classification confidence) |
| Claim extraction rules | C07 Extractor | C07 must define per-page-type extraction patterns |
| Brand/product detection | C08 AI / C07 deterministic rules | Not in C05 scope; C07 may implement simple regex or defer to AI |
| Customer type inference | C08 AI | Deferred to AI phase |
| Business signal detection | C08 AI | Deferred to AI phase |

### 2.4 Trace Completeness

C05 provides `WebsiteResearchPipelineTrace` per planned page:
```python
class WebsiteResearchPipelineTrace:
    planning_rule: str         # e.g., "DEFAULT_HOME_PATH"
    selected_url: str          # URL that was fetched
    page_type: PageType        # planned type
    fetch_outcome: FetchStatus # SUCCESS / FAILED / NOT_FETCHED
    classification_reason: str # why page was classified as X
    sanitization_actions: tuple[str, ...]  # what was cleaned
    error_classification: ResearchErrorCode | None
```

**Sufficient for C07 extraction trace?** Yes. Each evidence item can reference its source trace entry for full auditability.

---

## 3. ResearchEvidence Entity Audit

### 3.1 Entity Definition Review

`ResearchEvidence` (EspoCRM `entityDefs/ResearchEvidence.json`):

| Field | Type | Maps To (Vendored Contract) | Category |
|---|---|---|---|
| `name` | varchar(255) | (label) | Human-readable title |
| `peEvidenceId` | varchar(255) | `EvidenceItem.evidence_id` | **Evidence** |
| `peClaim` | varchar(500) | `EvidenceItem.claim` | **Evidence** |
| `peClaimType` | varchar(100) | `EvidenceItem.claim_type` | **Evidence** |
| `peEvidenceType` | varchar(100) | `EvidenceItem.evidence_type` | **Evidence** |
| `peSourceUrl` | url | `EvidenceItem.source_url` | **Evidence** |
| `peEvidenceText` | text | `EvidenceItem.evidence_text` | **Evidence** |
| `peContentSummary` | text | (CRM-only, generated) | **Evidence (CRM view)** |
| `peConfidence` | float(0–1) | `EvidenceItem.confidence` | **Evidence** |
| `peCapturedAt` | datetime | `EvidenceItem.captured_at` | **Research Metadata** |
| `peSchemaVersion` | varchar(64) | `schema_version` | **Research Metadata** |
| `peSnapshotHash` | varchar(128) | (dedup) | **Research Metadata** |
| `lead` | link→Lead | (CRM link) | **CRM Projection** |

### 3.2 Field Gaps for Evidence Storage

| Gap | Severity | Recommendation |
|---|---|---|
| **No `pageTitle` field** | Low | `EvidenceItem.page_title` exists in vendored contract but ResearchEvidence lacks it. Can embed in `peEvidenceText` or add `pePageTitle`. |
| **No `extractorVersion` field** | Low | `EvidenceItem.extractor_version` is in the vendored contract. C07 could store in `peSchemaVersion` or add a field. |
| **No link to ProspectPool** | Medium | Evidence should be traceable to the ProspectPool record that generated it. Currently only `lead` link exists. Add `prospectPool` link. |
| **No link to SearchJob** | Low | Useful for batch traceability but not essential. |
| **`peContentSummary` is CRM-only** | Low | Not in vendored contract. Useful for CRM preview but should be generated by C07, not C08 AI. |

### 3.3 Relationship Audit

```
ResearchEvidence ──belongsTo──→ Lead (via lead foreign: researchEvidences)
ResearchEvidence ←──hasMany──── Lead (researchEvidences)
```

**Missing:** ResearchEvidence → ProspectPool link. Currently evidence can only be linked to a Lead, but evidence originates from website research on a ProspectPool record. The ProspectPool → Lead conversion happens later (C08/C09). Evidence created in C07 has no direct ProspectPool back-reference.

### 3.4 ACL and Scope

- Scope: `entity: true, object: true, tab: true, acl: true, module: Prospecting`
- ACL: Controlled by Prospecting module (`"Prospecting": {"ResearchEvidence": true}`)
- **Assessment:** Standard EspoCRM record-level ACL. No unrestricted public access. Fine for C07.

### 3.5 Indexes

| Index | Columns | Purpose |
|---|---|---|
| `peEvidenceId` | `[peEvidenceId]` | Dedup/lookup by engine evidence ID |
| `peSnapshotHash` | `[peSnapshotHash]` | Content-based dedup |

**Assessment:** Two indexes support idempotent evidence persistence. C07 should populate both fields for every evidence item to enable upsert/dedup logic.

---

## 4. Evidence Data Model Design Recommendations

### 4.1 Current Model Inventory

```text
Vendored Contract (Python):
  EvidenceItem          ← canonical evidence schema
  WebsiteResearchResult ← contains evidence_items, plus AI-generated fields

CRM Schema (PHP/JSON):
  ResearchEvidence      ← persistent evidence storage in EspoCRM

Sync Contract (Python):
  SyncContractPayload.evidence  ← tuple of evidence dicts for API transport
  Required evidence fields: evidence_id, claim_type, claim, source_url,
                            evidence_text, confidence, captured_at, schema_version

Domain Model (Python):
  ResearchRecord.evidence  ← tuple of strings (evidence references, not items)
  ResearchRecord.summary   ← string
  ResearchRecord.detected_brands/products ← string tuples

Business Qualification (Python):
  EvidenceRequirement     ← requirement_id, description, satisfied, evidence_refs
  RoutingInstruction      ← which pipelines are allowed
```

### 4.2 Model Sufficiency Assessment

| Data Model | Sufficient for C07? | Notes |
|---|---|---|
| `EvidenceItem` (vendored) | ✅ YES | Complete evidence schema: 10 fields including evidence_id, claim_type, claim, source_url, page_title, evidence_text, evidence_type, confidence, captured_at, extractor_version |
| `ResearchEvidence` (CRM) | ✅ YES with gap | Missing `pageTitle` and `extractorVersion`. Otherwise maps 1:1 to `EvidenceItem`. |
| `SyncContractPayload.evidence` | ✅ YES | Validates 8 required fields per evidence item + 4 optional. C07 output must satisfy this validator. |
| `ResearchRecord.evidence` (domain) | ⚠️ INSUFFICIENT | Tuple of strings only. C07 should produce `EvidenceItem[]`, not string refs. Domain model needs updating. |
| `EvidenceRequirement` (qualification) | ✅ YES | Good pattern: requirement → evidence_refs → satisfied. C07 can use this for coverage checking. |

### 4.3 Recommended C07 Data Architecture (Design Only — No Implementation)

```text
C07 should introduce:

1. EvidenceExtractor (Python, chitu_connector/acquisition/)
   ┌──────────────────────────────────────────────────────┐
   │ Input:  WebsiteResearchPipelineResult (C05)           │
   │         MasterProspect (C04)                          │
   │                                                       │
   │ Processing:                                           │
   │  1. Page-level extraction (per page type):            │
   │     - Extract claims from text_content using rules    │
   │     - Assign claim_type based on page_type            │
   │     - Assign confidence from fetch signals            │
   │     - Generate evidence_id (deterministic hash)       │
   │                                                       │
   │  2. Cross-page synthesis:                             │
   │     - Merge duplicate claims (same claim text)        │
   │     - Dedup by evidence_id                            │
   │     - Rank by confidence                              │
   │                                                       │
   │  3. Quality gate:                                     │
   │     - Minimum evidence count threshold                │
   │     - Required page type coverage check               │
   │     - Confidence floor                                 │
   │                                                       │
   │ Output: EvidenceExtractionResult                      │
   │         ├── evidence_items: tuple[EvidenceItem, ...]  │
   │         ├── extraction_trace: tuple[...]              │
   │         ├── coverage: dict[PageType, int]             │
   │         ├── total_claims: int                         │
   │         ├── average_confidence: float                 │
   │         └── status: ExtractionStatus                  │
   └──────────────────────────────────────────────────────┘

2. EvidenceExtractionResult (new dataclass)
   Fields:
   - master_id: str
   - evidence_items: tuple[EvidenceItem, ...]
   - trace: tuple[ExtractionTraceEntry, ...]
   - coverage: Mapping[str, int]
   - total_claims: int
   - average_confidence: float
   - low_confidence_count: int
   - extraction_status: ExtractionStatus
   - started_at: str
   - completed_at: str

3. ExtractionStatus (enum)
   - COMPLETE — all pages processed, evidence extracted
   - PARTIAL — some pages failed extraction
   - INSUFFICIENT — below minimum evidence threshold
   - EMPTY — no extractable claims found
   - FAILED — extraction error

4. ExtractionTraceEntry
   - source_page_url: str
   - page_type: PageType
   - claims_found: int
   - claims_accepted: int
   - claims_rejected: int
   - rejection_reasons: tuple[str, ...]
   - extraction_rule_version: str
```

### 4.4 What NOT to Add in C07

| Don't Add | Why | Belongs In |
|---|---|---|
| AI-generated summaries | AI extraction boundary | C08 |
| Scoring/tier assignment | Scoring boundary | C09 |
| Email templates/content | Email generation boundary | Later phase |
| Opportunity proposals | CRM intelligence projection | C08/C09 |
| Lead auto-creation | CRM boundary | C08/C09 |
| `detected_brands`/`detected_products` | These require AI/LLM classification | C08 |

---

## 5. C07 → C08 AI Research Interface

### 5.1 What AI Research Needs

The vendored `WebsiteResearchResult` (future AI contract) expects:

| Input Field | Source in C07 | Available? |
|---|---|---|
| `candidate_id` | MasterProspect.master_id | ✅ |
| `website_url` | WebsiteResearchPipelineResult.root_url | ✅ |
| `final_url` | Page result final_url | ✅ |
| `website_accessible` | research_status != NOT_ELIGIBLE/FAILED | ✅ |
| `page_title` | Page result title | ✅ |
| `meta_description` | Page result meta_description | ✅ |
| `visited_pages` | Page result URLs | ✅ |

AI must produce:

| Output Field | Type | Evidence-Backed? |
|---|---|---|
| `company_summary` | str | Must cite evidence_ids |
| `detected_brands` | tuple[str, ...] | Must cite evidence_ids |
| `detected_products` | tuple[str, ...] | Must cite evidence_ids |
| `customer_type_candidates` | tuple[CustomerTypeCandidate, ...] | Each has evidence_ids |
| `business_signals` | tuple[str, ...] | Must cite evidence_ids |
| `contact_page_urls` | tuple[str, ...] | Direct from page links |
| `public_emails` | tuple[str, ...] | Extracted from page text |
| `public_phones` | tuple[str, ...] | Extracted from page text |

### 5.2 Audit Trail Requirements

For each AI output, C07 evidence must support:

| Requirement | C07 Status |
|---|---|
| **Source URL preserved** | ✅ `EvidenceItem.source_url` |
| **Original text preserved** | ✅ `EvidenceItem.evidence_text` (CRM: `peEvidenceText`) |
| **Confidence preserved** | ✅ `EvidenceItem.confidence` |
| **Audit support** | ✅ `EvidenceItem.evidence_id` + trace |
| **Regeneration support** | ✅ C05 `WebsiteResearchPageResult.raw_html` is available for re-extraction |

### 5.3 Structural Readiness

AI input requires structured evidence per claim type:

```text
Claims by type → AI prompt context:
  - CONTACT claims → contact_page_urls, public_emails, public_phones
  - PRODUCTS claims → detected_products, product evidence
  - BRANDS claims → detected_brands, brand evidence
  - ABOUT claims → company_summary, business_signals
  - HOME claims → company_summary, meta_description
```

C07 should organize evidence by `claim_type` before passing to AI. This grouping is a C07 responsibility.

---

## 6. C07 → C09 Scoring Interface

### 6.1 What Scoring Needs from Evidence

The vendored `CanonicalScoreRequest` takes `WebsiteResearchResult` (which contains `evidence_items`). Per `canonical_score.py`:

```python
class ScoreComponentTrace:
    component: str       # which scoring component
    points: int          # points awarded
    evidence_refs: tuple[str, ...]  # ← evidence_ids backing this score
```

Each score component must reference specific evidence items. C07 must ensure:

| Scoring Need | Evidence Requirement |
|---|---|
| **Evidence Type** | `EvidenceItem.claim_type` classifies evidence (PRODUCT, BRAND, CONTACT, etc.) |
| **Confidence** | `EvidenceItem.confidence` weights evidence reliability |
| **Source** | `EvidenceItem.source_url` provides provenance |
| **Freshness** | `EvidenceItem.captured_at` enables staleness checks |
| **Verification** | `EvidenceItem.evidence_id` enables cross-reference and audit |

### 6.2 Score Component → Evidence Mapping

Based on the `CanonicalScoreResult.component_traces` pattern:

| Score Component | Evidence Claim Types Needed | Min Evidence Count |
|---|---|---|
| Product Fit | PRODUCTS, BRANDS | 2+ |
| Contact Availability | CONTACT | 1+ |
| Website Quality | HOME, ABOUT | 1+ |
| Business Signals | ABOUT, HOME (signals extracted later by AI) | 1+ |
| Geographic Match | (from MasterProspect, not evidence) | N/A |

### 6.3 Evidence Coverage Metric

The sync contract validates `score.evidence_coverage` (float 0–1). C07 must provide a coverage metric:

```text
evidence_coverage = (claims_with_evidence / required_claim_types)
```

Where `required_claim_types` is the set of claim types needed for a complete score.

---

## 7. EspoCRM Mapping Audit

### 7.1 Current Relationship Map

```text
MasterProspect (C04, Python, in-memory)
    │
    │  C05 research
    ▼
WebsiteResearchPipelineResult (C05, Python, in-memory)
    │
    │  C07 extraction (NOT YET IMPLEMENTED)
    ▼
EvidenceItem[] (C07, Python, in-memory → vendored contract)
    │
    ├──→ ResearchEvidence (C06, EspoCRM, schema ready)
    │    └── lead (belongsTo) → Lead
    │
    └──→ SyncContractPayload.evidence (C07→C08, API transport)
         └──→ Lead.pe* fields (C08/C09, EspoCRM, schema ready)
              └── researchEvidences (hasMany) → ResearchEvidence
```

### 7.2 ResearchEvidence ↔ Lead Relationship

```
ResearchEvidence.lead (belongsTo) → Lead
Lead.researchEvidences (hasMany) → ResearchEvidence
```

This is a **bidirectional link** that C08/C09 will populate. C07's responsibility is to create `ResearchEvidence` records. The `lead` link is populated later when the ProspectPool is promoted to a Lead.

### 7.3 ProspectPool Relationship Gap

Current:
```
ProspectPool ← hasMany ← nothing (no evidence link)
ResearchEvidence ← belongsTo ← Lead (only)
```

**Recommended:** Add a `prospectPool` link on ResearchEvidence:
```
ResearchEvidence.prospectPool (belongsTo) → ProspectPool
ProspectPool.researchEvidences (hasMany) → ResearchEvidence
```

This allows evidence → prospect traceability before CRM conversion. Without it, evidence created in C07 is orphaned until C08/C09 links it to a Lead.

### 7.4 Lead Intelligence Field Mapping

The `EspoCRMSyncMapper.lead_fields()` method shows how evidence flows to Lead:

| Lead Field | Evidence Source | Category |
|---|---|---|
| `peResearchSummary` | AI-generated from evidence | AI Output |
| `peKeyEvidence` | Top 5 evidence claims formatted as bullet list | AI Output (formatted evidence) |
| `peRecommendedApproach` | AI-generated from evidence + product fit | AI Output |
| `peOpportunityScoreV4` | Scoring engine from evidence | Score |
| `peScoreTier` | Scoring engine tier | Score |
| `peBestFirstProduct` | Scoring engine recommendation | Score |
| `peConfidence` | Score.aggregate_confidence | Metadata |
| `peEvidenceCoverage` | Score.evidence_coverage | Metadata |
| `peEvidenceSchemaVersion` | Evidence schema version | Metadata |
| `peEvidenceSnapshotHash` | Evidence snapshot hash | Metadata |

**Assessment:** Lead intelligence fields are correctly positioned as **consumers** of C07 evidence, not producers. C07 creates evidence; C08/C09 transform it into Lead fields.

---

## 8. Current Findings Summary

### 8.1 Met ✅

| # | Finding |
|---|---|
| F1 | C05 `WebsiteResearchPipelineResult` provides all source material needed for evidence extraction (text_content, title, meta_description, raw_html, page_type, links, trace) |
| F2 | Vendored `EvidenceItem` contract is complete and maps 1:1 to CRM `ResearchEvidence` entity (with minor field gaps) |
| F3 | `ResearchEvidence` entity schema is defined, indexed, and ACL-gated in EspoCRM |
| F4 | Sync contract `validate_sync_contract()` enforces 8 required evidence fields + validation rules |
| F5 | `CanonicalScoreResult` references evidence via `evidence_refs` and `component_traces` — evidence traceability is structurally supported |
| F6 | `EvidenceRequirement` in business qualification provides a pattern for evidence-satisfaction checking |
| F7 | C05 trace is complete per-page, enabling full extraction audit trail |
| F8 | Raw HTML is retained in C05 output for re-extraction / AI processing |
| F9 | No evidence-related code exists in the connector yet — greenfield for C07 |
| F10 | Lead detail layout has dedicated "AI Research Information" panel with `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach` — ready to display C07→C08 outputs |

### 8.2 Missing ⚠️

| # | Gap | Severity | Resolution |
|---|---|---|---|
| G1 | **No EvidenceExtractor exists** — C05 output has no code path to EvidenceItem[] | **Blocker for C07** | C07 must implement extraction rules per page type |
| G2 | **No connector → ResearchEvidence persistence adapter** — EspoCRM ResearchEvidence entity has no Python write path | **Blocker for C07** | C07 must extend `EspoAcquisitionRepository` or create `EspoEvidenceRepository` |
| G3 | **ResearchEvidence has no ProspectPool link** — evidence is orphaned until Lead creation | **Medium** | Add `prospectPool` link to ResearchEvidence entityDefs |
| G4 | **ResearchRecord.evidence is tuple[str]** — domain model stores string refs, not structured evidence | **Medium** | Update domain model or use vendored `EvidenceItem` directly |
| G5 | **ResearchEvidence entity missing pageTitle field** — `EvidenceItem.page_title` has no CRM column | **Low** | Add `pePageTitle` varchar field or embed in peEvidenceText |
| G6 | **No evidence confidence heuristic** — C05 has no confidence model for extracted claims | **Medium** | C07 must design per-page-type confidence scoring |
| G7 | **No evidence dedup strategy** — `peSnapshotHash` index exists but no code computes hashes | **Medium** | C07 must implement content-based dedup |
| G8 | **Evidence extraction rules undefined** — no specification for what constitutes a "claim" per page type | **High** | C07 design phase must define extraction patterns |
| G9 | **C05 internal pipeline has no integration with vendored contracts** — two separate `website_research.py` modules exist with different contracts | **Medium** | C07 bridges this gap; document the mapping explicitly |

### 8.3 Risks 🔴

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **C05 text_content truncation at 100KB loses evidence** | Low | Low | 100KB is generous for visible text; raw_html is preserved for AI reprocessing |
| R2 | **Evidence extraction rules produce false claims** | Medium | Medium | Start with high-confidence deterministic rules; defer low-confidence to AI verification |
| R3 | **Duplicate evidence from same domain across multiple prospects** | Low | Medium | `peSnapshotHash` dedup handles this; cross-prospect dedup needs `normalized_domain` index |
| R4 | **C05 → C07 contract mismatch if C05 internal models change** | Low | High | C05 is frozen; C07 should consume `WebsiteResearchPipelineResult.to_dict()` for stability |
| R5 | **Evidence volume explosion** — 10 pages × N claims per page | Medium | Low | Cap claims per page (e.g., 20) and total claims per prospect (e.g., 100) |
| R6 | **CRM API rate limiting for bulk evidence writes** | Low | Medium | Batch evidence creation or use EspoCRM bulk API |

---

## 9. Recommended C07 Contract

### 9.1 ExtractionInput

```text
Contract: EvidenceExtractionInput

Fields:
  master_prospect   MasterProspect          # From C04 (identity)
  research_result   WebsiteResearchPipelineResult  # From C05 (raw pages)
  options           ExtractionOptions       # Configuration

ExtractionOptions:
  min_confidence        float = 0.3         # Minimum confidence to accept claim
  max_claims_per_page   int = 20            # Claims per page cap
  max_total_claims      int = 100           # Total claims cap
  extractor_version     str = "c07-v1"      # Version for traceability
  page_types            tuple[PageType, ...] # Which page types to extract from (default: all)
```

### 9.2 ExtractionOutput

```text
Contract: EvidenceExtractionResult

Fields:
  master_id              str                        # MasterProspect.master_id
  evidence_items         tuple[EvidenceItem, ...]   # Vendored contract items
  trace                  tuple[ExtractionTraceEntry, ...]  # Per-page extraction audit
  coverage               dict[str, int]             # PageType → claim count
  total_claims           int                        # Total claims extracted
  accepted_claims        int                        # Claims above confidence threshold
  rejected_claims        int                        # Claims below threshold / duplicates
  low_confidence_count   int                        # Claims below min_confidence
  average_confidence     float                      # Mean confidence across accepted claims
  extraction_status      ExtractionStatus           # COMPLETE / PARTIAL / INSUFFICIENT / EMPTY / FAILED
  started_at             str                        # ISO timestamp
  completed_at           str                        # ISO timestamp
  extractor_version      str                        # Version for audit

ExtractionStatus (enum):
  COMPLETE       # All pages processed, sufficient evidence
  PARTIAL        # Some pages failed or low confidence
  INSUFFICIENT   # Below minimum evidence threshold
  EMPTY          # No extractable claims
  FAILED         # Extraction error

ExtractionTraceEntry:
  source_page_url        str
  page_type              PageType
  claims_found           int
  claims_accepted        int
  claims_rejected        int
  rejection_reasons      tuple[str, ...]
  extraction_rule_version str
```

### 9.3 PersistenceOutput

```text
Contract: EvidencePersistenceResult

Fields:
  master_id              str
  evidence_items         tuple[EvidenceItem, ...]
  created_count          int       # New ResearchEvidence records
  updated_count          int       # Updated existing records
  duplicate_count        int       # Skipped (hash match)
  failed_count           int       # Persistence failures
  crm_evidence_ids       tuple[str, ...]  # EspoCRM ResearchEvidence IDs
  persistence_status     PersistenceStatus
  error_summary          str | None

PersistenceStatus (enum):
  STORED         # All items persisted
  PARTIAL        # Some items failed
  FAILED         # Persistence error
```

---

## 10. Backward Compatibility

### 10.1 Frozen Contracts — No Impact

| Contract | C07 Impact | Verification |
|---|---|---|
| **C03 Provider** (`RawCandidate`, `ProviderResult`) | **None** | C07 operates downstream of C05, far from providers |
| **C04 Master Prospect** (`MasterProspect`, matching rules) | **None** | C07 reads `master_id` only; no normalization/matching changes |
| **C05 Website Research** (`WebsiteResearchPipelineResult`) | **Read-only consumer** | C07 reads `.to_dict()` output; C05 models are frozen and immutable |
| **C06 ResearchEvidence entity** | **Writer** | C07 creates records; schema is stable. Add `prospectPool` link if needed but don't remove fields. |
| **EspoCRM Extension** | **Additive only** | New ResearchEvidence records. No layout, ACL, or metadata changes needed by C07. |
| **Sync Contract V1** | **Producer** | C07 evidence must pass `validate_sync_contract()` validation. |
| **Vendored `EvidenceItem`** | **Producer** | C07 implements the contract; does not modify it. |

### 10.2 What C07 Must NOT Change

- ❌ C05 `website_research.py` internal models
- ❌ C04 `master_prospect.py` matching/normalization
- ❌ C03 `models.py` provider contracts
- ❌ `ResearchEvidence` entityDefs (additive links are OK; field removal is NOT)
- ❌ `SyncContractPayload` required fields
- ❌ Vendored `EvidenceItem` fields
- ❌ Lead `pe*` field definitions
- ❌ ProspectPool entityDefs

---

## 11. Implementation Plan (for Codex — No Code)

### Phase C07.1 — Evidence Extraction Core (Python)

**Scope:** Deterministic rule-based extraction from C05 output.

1. Create `chitu_connector/acquisition/evidence_extraction.py`
   - `EvidenceExtractor` class with injectable extraction rules
   - Per-page-type extraction strategies:
     - HOME → company name, tagline, meta description claims
     - ABOUT → company description, history, team size claims
     - PRODUCTS → product names, categories, descriptions claims
     - BRANDS → brand names, partnerships claims
     - CONTACT → email, phone, address, contact form URL claims
   - Confidence heuristic: page type match confidence × content quality signal
   - Deterministic evidence_id generation: SHA-256 of (master_id + source_url + claim_type + claim text)
   - Output: `EvidenceExtractionResult`

2. Tests: `tests/test_phase3c07_evidence_extraction.py`
   - Fixture-based: fake C05 pipeline results → extraction → verify evidence items
   - Coverage: normal, empty, partial, malformed, duplicate claims
   - No real websites, no AI, no CRM

### Phase C07.2 — Evidence Persistence (Python → EspoCRM)

**Scope:** Write extracted evidence to EspoCRM ResearchEvidence entities.

3. Extend `EspoAcquisitionRepository` or create `EspoEvidenceRepository`
   - `create_evidence(values)` → POST ResearchEvidence
   - `find_evidence_by_hash(snapshot_hash)` → dedup check
   - `upsert_evidence(values)` → create or skip if hash exists

4. Tests: fixture-based with mock HTTP transport
   - No real EspoCRM instance required

### Phase C07.3 — Enrichment Gate (Python)

**Scope:** Decision logic for whether evidence is sufficient.

5. Create `chitu_connector/acquisition/enrichment_gate.py`
   - Input: `EvidenceExtractionResult`
   - Rules: minimum claim count, required page type coverage, confidence floor
   - Output: `EnrichmentEligibility {eligible, reason, missing_evidence_types}`

6. Tests: fixture-based decision validation

### Phase C07.4 — Integration (Python)

**Scope:** Wire extraction → persistence → gating into the acquisition runner.

7. Update `AcquisitionWorker` flow:
   ```
   Provider → MasterProspect → WebsiteResearch → EvidenceExtraction → EvidencePersistence → EnrichmentGate → ProspectPool status update
   ```

8. End-to-end test with fake provider + fake transport

### Deferred to C08/C09

- AI research (DeepSeek/LLM integration)
- Scoring engine
- Lead creation from ProspectPool
- Lead `pe*` field population
- ResearchEvidence → Lead linking
- Email generation
- Opportunity creation

---

## 12. Final Verdict

```text
READY — C07 can begin design
```

**Summary:** C07 has well-defined upstream inputs (C05 `WebsiteResearchPipelineResult`), a complete target schema (vendored `EvidenceItem` + CRM `ResearchEvidence`), validated downstream contracts (sync contract evidence validation + scoring evidence_refs), and clear consumers (C08 AI Research, C09 Scoring, CRM Lead projection). The gap is purely the extraction and persistence runtime — which is exactly what C07 is designed to implement.

**Nine gaps** are identified (G1–G9), all of which are implementation items for C07, not architectural blockers. **Six risks** (R1–R6) are manageable with the mitigations described. **No frozen contract** (C03/C04/C05/C06) is at risk from C07 implementation.

**C07 should proceed.** The extraction rules design (G8) is the highest-priority item to resolve before coding begins.

---

**Audit completed:** 2026-07-13
**Files modified:** 0
**Commits created:** 0
**Verdict:** READY — C07 can begin design
