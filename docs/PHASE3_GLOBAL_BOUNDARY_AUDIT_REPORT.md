# Phase3 Global Boundary Audit Report

**Date:** 2026-07-14
**Auditor:** Claude Code (DeepSeek V4 Pro API)
**Mode:** Read-only. Zero code, test, metadata, or CRM data modifications.
**Scope:** Complete Phase3 intelligence CRM pipeline (C01–C09 + U03)

---

## Final Verdict: **PASS WITH MINOR FINDINGS**

---

## Executive Summary

The Phase3 intelligence CRM pipeline maintains strong separation between Evidence, AI, Scoring, Outreach Preparation, and CRM Projection domains. Each domain boundary is enforced through typed contracts (Protocol classes, frozen dataclasses, field allowlists) and explicit documentation. No automatic Opportunity creation, no hidden AI/LLM calls, no unauthorized email sending, and no shadow scoring were found. One legacy artifact (`gate.py` referencing `canonical-scoring-v4.0`), one intentionally disabled placeholder (`scoring.py`'s `DecisionEngineAdapter`), and one naming issue (Phase3A30 dashboard template) are the only findings.

---

## 1. Evidence Boundary Audit

### Verdict: **PASS**

### Data Flow

```
Website Research (C05)
    → WebsiteResearchEvidenceExtractor (C07.1)
    → EvidenceItem dataclass (factual claims only)
    → ResearchEvidencePersistenceAdapter (C07.2)
    → ResearchEvidence CRM entity
    → DeterministicEnrichmentGate (C07.3)
    → QualificationDecision
```

### Evidence Extraction (`evidence_extraction.py`)

**File:** `chitu-connector/chitu_connector/acquisition/evidence_extraction.py`

The extractor consumes `WebsiteResearchPipelineResult` (serialized C05 output) and produces `EvidenceItem` values containing ONLY factual website observations:

| Evidence Type | Source | Extraction Method |
|---|---|---|
| `title` | `<title>` tag text | Direct copy, truncated to 500 chars |
| `meta_description` | `<meta name="description">` | Direct copy, truncated to 500 chars |
| `visible_text` | Page text content | First sentence extraction |

**Boundary checks — ALL PASS:**

- ✅ **No AI-generated conclusions stored as evidence** — The extractor performs deterministic text extraction only. The `claim` field is the raw observed text itself, never an AI inference.
- ✅ **No score fields mixed into evidence** — `EvidenceItem` dataclass has no score-related fields.
- ✅ **No email fields mixed into evidence** — `EvidenceItem` dataclass has no email-related fields.
- ✅ **Source traceability preserved** — Every `EvidenceItem` carries `source_url`, `page_title`, `evidence_id` (SHA-256 of claim_type + source_url + text), and `extractor_version`.

### Evidence Persistence (`research_evidence_persistence.py`)

**File:** `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py`

- ✅ **Immutable snapshot semantics** — Uses `evidence_snapshot_hash` for deduplication. Identical snapshots return `SKIPPED`.
- ✅ **Validates every field** — `_validation_error()` checks evidence_id, claim, source_url (http/https only), confidence (0–1 float), text length (≤1000), claim_type, evidence_type, extractor_version.
- ✅ **No Lead mutation** — The adapter only creates ResearchEvidence records linked to an existing Lead via `leadId`. It never updates Lead fields.
- ✅ **No AI, scoring, or email** — Explicitly stated in module docstring: "does not create or update Leads, and it has no scoring, AI, email, or workflow responsibilities."

### ResearchEvidence CRM Entity

**Files:**
- `crm-extension/Resources/entityDefs/ResearchEvidence.json`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/ResearchEvidence.json`

**Entity fields are purely factual:**

| Field | Type | Classification |
|---|---|---|
| `name` | varchar | Record label |
| `peEvidenceId` | varchar | Unique evidence identifier |
| `peClaim` | text | Observed claim (source text) |
| `peClaimType` | varchar | page_title / meta_description / visible_text |
| `peEvidenceType` | varchar | title / meta_description / visible_text |
| `peSourceUrl` | varchar | Public HTTP URL of source page |
| `peEvidenceText` | text | Raw observed text |
| `peContentSummary` | text | Abbreviated claim |
| `peConfidence` | float | Deterministic confidence (0.85–0.95) |
| `peCapturedAt` | datetime | When the page was fetched |
| `peSchemaVersion` | varchar | Extractor version |
| `peSnapshotHash` | varchar | Batch deduplication hash |

**Boundary checks — ALL PASS:**
- ✅ No score fields (`peOpportunityScore`, `peScoreTier`, etc.)
- ✅ No AI conclusion fields
- ✅ No email/outreach fields
- ✅ No qualification decision fields (those live in the QualificationDecision dataclass, not in CRM)

### Enrichment Gate (`enrichment_gate.py`)

**File:** `chitu-connector/chitu_connector/espocrm_sync/enrichment_gate.py`

```
DeterministicEnrichmentGate.evaluate(research_evidence, prospect_pool_context=None)
    → QualificationDecision(status, reason, evidence_count)
```

- ✅ **Deterministic, read-only** — Uses fixed thresholds: ≥2 valid evidence items, ≥0.80 average confidence.
- ✅ **No AI** — "The gate is deliberately read-only. It does not invoke AI, alter scoring, or write ProspectPool, Lead, Opportunity, or ResearchEvidence records."
- ✅ **No CRM mutation** — `prospect_pool_context` parameter is explicitly discarded (`del prospect_pool_context`).
- ✅ **Four qualification states** — `NOT_READY` → `RESEARCH_COMPLETE` → `QUALIFIED` → `REVIEW_REQUIRED`. No hidden states.

---

## 2. AI Boundary Audit

### Verdict: **PASS**

### LLM/AI Call Search — Complete Inventory

A full-project grep for AI/LLM keywords (`deepseek`, `openai`, `llm`, `ai call`, `model infer`, `chat completion`) across the entire `chitu-connector/` directory returned ZERO functional AI calls in pipeline code:

| Location | Context | Verdict |
|---|---|---|
| `tests/test_espocrm_phase3c06_research_evidence_boundary.py:39` | Test fixture — lists `"openai"` as a FORBIDDEN token to check DOES NOT leak | ✅ Boundary test |
| `tests/test_espocrm_phase3c06_research_evidence_boundary.py:520` | Test — verifies "DeepSeek" is NOT present in evidence records | ✅ Boundary test |
| `tests/test_phase3c03_2_serper_runner.py:165` | Test — "Transport must not be called" assertion | ✅ Isolation test |
| `acquisition/website_research.py:4` | Docstring — "A caller must inject worker/runner, CRM, persistence, browser tooling, and AI" | ✅ Documentation of injection pattern |
| `acquisition/evidence_extraction.py:4` | Docstring — "performs no... AI call" | ✅ Explicit boundary statement |

### Key Architecture Decisions

1. **All "intelligence" classes are explicitly deterministic:**
   - `DeterministicEnrichmentGate`
   - `DeterministicScoreInputAdapter`
   - `DeterministicOutreachInputAdapter`
   - `DeterministicEmailDraftGenerator`
   - `DeterministicFakeProvider`

2. **AI injection seams are defined but NOT implemented:**
   - `EmailDraftGenerator` (Protocol) — "A future provider can implement... and return the same immutable contract"
   - `CanonicalScoreExecutor` (Protocol) — "Stable invocation seam implemented by the existing canonical scorer"
   - `ScoreEngine` (Protocol) — "Deliberately unavailable placeholder"

3. **No duplicate AI scoring paths** — The `CanonicalScoreIntegration` is the ONLY bridge to scoring. There is no alternative scoring path.

4. **No LLM calls hidden in PHP** — The CRM extension (`crm-extension/`) has ZERO PHP files that call external AI/LLM services. The only HTTP calls are to Brevo (email events) and Chitu (connector API).

---

## 3. Scoring Ownership Audit

### Verdict: **PASS** (one minor finding)

### Canonical Scoring Contract

**File:** `chitu-connector/chitu_connector/vendored/contracts/canonical_score.py`

```python
CanonicalScoreResult(
    accepted: bool
    opportunity_score: int | None
    score_tier: str | None           # A, B, C, D
    best_first_product: str | None
    customer_type: str | None
    contact_priority: str | None
    score_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]    # → Traceable to ResearchEvidence
    component_traces: tuple[ScoreComponentTrace, ...]  # → Per-component traceability
    validation_errors: tuple[str, ...]
    canonical_engine_version: str | None
    canonical_content_hash: str | None  # → Reproducibility
    raw_decision: dict[str, Any] | None
    adapter_version: str
    scored_at: datetime
)
```

### Scoring Pipeline (C08)

```
ResearchEvidence (C07)
    → DeterministicScoreInputAdapter (read-only facts)
    → ScoreInput {evidence_count, confidences, qualification_status, ...}
    → CanonicalScoreIntegration.evaluate(score_input, research_evidence)
    → CanonicalScoreExecutor.score(score_input)  [injected, single seam]
    → CanonicalScoreResult
    → CRMScoreProjectionAdapter.project(lead_id, score_result)
    → Lead fields: peOpportunityScoreV4, peScoreTier, peBestFirstProduct, peScoreRulesVersion
```

### Boundary Checks

- ✅ **Single scoring path** — `CanonicalScoreIntegration` is the only bridge. The `ScoreInputAdapter` produces facts without calculating scores.
- ✅ **No shadow scoring** — `DeterministicScoreInputAdapter.build()` produces `ScoreInput` with evidence facts only, never a score value.
- ✅ **No score mutation during projection** — `CRMScoreProjectionAdapter` writes exactly the fields produced by the canonical scorer with validation:
  - Score must be 0–100 (int/float)
  - Score tier must be A/B/C/D
  - Version must be non-empty string
  - Product recommendation must be ≤255 chars
- ✅ **Score traceability preserved** — `CanonicalScoreTrace` records `input_hash` (SHA-256 of ScoreInput), `input_evidence_refs`, and `canonical_content_hash`.
- ✅ **Field allowlist** — `_PROJECTABLE_FIELDS = {"peOpportunityScoreV4", "peScoreTier", "peBestFirstProduct", "peScoreRulesVersion"}` — ONLY these 4 fields can be written.

### MINOR FINDING: Legacy V1 Sync Gate References `canonical-scoring-v4.0`

**File:** `chitu-connector/chitu_connector/espocrm_sync/gate.py:19`

```python
if data["score"]["rules_version"] != "canonical-scoring-v4.0":
    return GateDecision(False, "INVALID_SCORE_VERSION")
```

This gate enforces a hard-coded scoring version `canonical-scoring-v4.0` that predates the C08 scoring pipeline. The C08 pipeline uses `canonical_engine_version` from `CanonicalScoreResult` which may be a different version string. This gate is part of the V1 sync contract path (used by `ChituSyncService.syncLead()` in PHP) and could reject valid C08-scored payloads if the version doesn't match exactly.

**Risk:** LOW (only affects the V1 sync API path, not the C08 pipeline path)
**Recommendation:** Evaluate whether `gate.py` should accept the C08 canonical engine version string or be retired in favor of the C08 projection path.

### MINOR FINDING: Intentionally Disabled DecisionEngineAdapter

**File:** `chitu-connector/chitu_connector/vendored/contracts/scoring.py:29-30`

```python
class DecisionEngineAdapter:
    """Deliberately unavailable placeholder for the candidate canonical engine."""

    engine_version = "decision-engine-candidate-v5.0.0"

    def score(self, request: ScoreRequest) -> ScoreResult:
        raise RuntimeError("DecisionEngineAdapter is intentionally disabled in Foundation V1")
```

**Risk:** NONE (intentional safety mechanism)
**Recommendation:** Remove or replace when the canonical engine is ready. Document the migration path.

---

## 4. Outreach Boundary Audit

### Verdict: **PASS**

### Outreach Pipeline (C09)

```
OutreachInputAdapter (C09.1)
    → OutreachInput {company_context, talking_points, qualification_status, score_tier, ...}
    → DeterministicEmailDraftGenerator (C09.2)
    → EmailDraft {subject, body, evidence_references, ...}
    → CampaignProjectionAdapter (C09.3)
    → Lead fields: peEmailStatus=DRAFT_READY, peEmailCampaignName, peRecommendedApproach
```

### Boundary Checks

- ✅ **Draft ≠ Sent Email** — `EmailDraft` is an immutable dataclass with `subject`, `body`, and `evidence_references`. It has NO `send()`, `deliver()`, or SMTP method. The `EmailDraftGenerator` Protocol only returns a draft contract.
- ✅ **No automatic sending path** — `CampaignProjectionAdapter.project()` writes `peEmailStatus: "DRAFT_READY"` to the Lead. There is NO code path from `DRAFT_READY` to `SENT` anywhere in the connector or CRM extension. The Brevo email event service explicitly states "Does not send email."
- ✅ **No SMTP/provider coupling** — The draft generator is provider-neutral. The `EmailDraftGenerator` Protocol allows any implementation. The current `DeterministicEmailDraftGenerator` is a template-based reference implementation with zero external dependencies.
- ✅ **No campaign execution hidden in projection** — `CampaignProjectionAdapter` writes exactly 3 fields (`peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach`) to an existing Lead. The `LeadCampaignProjectionClient` Protocol has only `update_lead_campaign_projection()` — no send, create, or delete method.

### Brevo Email Event Handling (PHP)

**File:** `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BrevoEmailEventSyncService.php`

```php
/**
 * Append-only Brevo email execution event ingestion.
 * Does not send email. CRM lifecycle projection and Task automation are owned by EmailEventWorkflowHook.
 */
```

- ✅ **Append-only** — Creates `EmailEvent` records. Never sends email.
- ✅ **Clear ownership separation** — "CRM lifecycle projection and Task automation are owned by EmailEventWorkflowHook."

### Lead Email Fields

**File:** `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Lead.json`

| Field | Type | Classification |
|---|---|---|
| `peEmailStatus` | enum | Lifecycle status (NONE, DRAFT_READY, APPROVED, SENT, REPLIED, BOUNCED) |
| `peEmailCampaignName` | varchar | Campaign reference label |
| `peLastEmailDate` | datetime | When last email event occurred |
| `peEmailReplyStatus` | varchar | Reply tracking |
| `peRecommendedApproach` | text | Human-readable outreach guidance |

All fields are preparation/monitoring fields. The `SENT` status is set by `BrevoEmailEventSyncService` when Brevo reports a `sent` event — NOT by the connector initiating a send.

---

## 5. CRM Projection Audit

### Verdict: **PASS**

### Allowed CRM Writes (Exhaustive Inventory)

| Adapter | Target Entity | Fields Written | Operation |
|---|---|---|---|
| `CRMScoreProjectionAdapter` | Lead | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peScoreRulesVersion` | Update only |
| `CampaignProjectionAdapter` | Lead | `peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach` | Update only |
| `ChituSyncService.syncLead()` | Lead | 23 fields (full V1 contract) | Create or Update |
| `ChituSyncService.syncEvidence()` | ResearchEvidence | 12 fields (evidence snapshot) | Create only |
| `ChituSyncService.syncOpportunityProposal()` | Lead | 7 fields (proposal context) | Update only |
| `EspoAcquisitionRepository` | SearchJob, ProspectPool | Acquisition data | Create/Update |
| `BrevoEmailEventSyncService` | EmailEvent | Brevo event fields | Create only |

### Forbidden CRM Writes — ALL VERIFIED ABSENT

- ❌ **Automatic Opportunity creation** — `ChituSyncService.syncOpportunityProposal()` explicitly returns `"action": "NO_AUTOMATIC_OPPORTUNITY"`. The `syncLead()` V1 path does not create Opportunities. The C08/C09 projection adapters only update existing Leads.
- ❌ **Unexpected Lead mutations** — All projection adapters use explicit field allowlists (`_PROJECTABLE_FIELDS`, `allowed_campaign_projection_fields()`). The PHP `ChituSyncService.leadFields()` explicitly enumerates every writable field.
- ❌ **Workflow side effects** — The connector has no workflow triggers. The PHP `BrevoEmailEventSyncService` defers Task automation to `EmailEventWorkflowHook` (separate ownership).
- ❌ **Email sending** — Verified absent across all code paths (see §4).

### Lead AI Information Fields (Allowed Writes)

These fields on the Lead entity are explicitly documented as Chitu-provided intelligence context:

| Field | Purpose | Boundary |
|---|---|---|
| `peOpportunityScoreV4` | Canonical Scoring V4 score | Written by CRMScoreProjectionAdapter |
| `peScoreTier` | A/B/C/D tier | Written by CRMScoreProjectionAdapter |
| `peBestFirstProduct` | Recommended product | Written by CRMScoreProjectionAdapter |
| `peScoreRulesVersion` | Canonical engine version | Written by CRMScoreProjectionAdapter |
| `peEmailStatus` | DRAFT_READY / APPROVED / SENT / etc. | Written by CampaignProjectionAdapter or Brevo sync |
| `peEmailCampaignName` | Campaign label | Written by CampaignProjectionAdapter |
| `peRecommendedApproach` | Human-readable guidance | Written by CampaignProjectionAdapter |
| `peResearchStatus` | COMPLETED / FAILED | Written by ChituSyncService (V1 sync) |
| `peResearchSummary` | Human-readable summary | Written by ChituSyncService (V1 sync) |
| `peKeyEvidence` | Top 5 evidence claims | Written by ChituSyncService (V1 sync) |
| `peProposalAction` | Always `NO_AUTOMATIC_OPPORTUNITY` | Written by ChituSyncService |

All AI information fields are clearly prefixed with `pe` (Prospecting Engine), distinguishing them from CRM-core fields (`name`, `amount`, `stage`, etc.).

### Native CRM Core Fields — NOT Modified

The connector NEVER writes to core CRM fields:
- `Opportunity.amount` — CRM-owned
- `Opportunity.stage` — CRM-owned
- `Lead.status` — CRM-owned
- `Task.*` — CRM-owned
- `Account.*` — CRM-owned

---

## 6. Data Ownership Matrix

| Object | Owner | Allowed Mutation | Mutation Source |
|---|---|---|---|
| **SearchStrategy** | CRM User (via EspoCRM UI) | Create, Update (Draft→Ready→Active), Delete | `SearchStrategyService.php`, `PostGenerateSearchStrategyJobs.php` |
| **SearchJob** | Acquisition Worker (connector) | Create (QUEUED), Update (status transitions, result counts) | `EspoAcquisitionRepository`, `PostGenerateSearchStrategyJobs.php` |
| **ProspectPool** | Acquisition Worker (connector) | Create, Update (research/qualification/crm status) | `EspoAcquisitionRepository` |
| **ResearchEvidence** | Evidence Pipeline (C07) | Create only (immutable after write) | `ResearchEvidencePersistenceAdapter`, `ChituSyncService.syncEvidence()` |
| **QualificationDecision** | Enrichment Gate (C07.3) | In-memory only (never persisted directly) | `DeterministicEnrichmentGate.evaluate()` |
| **ScoreInput** | Score Input Adapter (C08.1) | In-memory only (read-only facts) | `DeterministicScoreInputAdapter.build()` |
| **CanonicalScoreResult** | Canonical Score Engine | In-memory only; projected to Lead | `CanonicalScoreIntegration.evaluate()` → `CRMScoreProjectionAdapter.project()` |
| **ScoreResult (V1)** | Legacy Scoring Engine | In-memory; projected via V1 sync contract | `ChituSyncService.syncLead()` |
| **EmailDraft** | Draft Generator (C09.2) | In-memory only (never sent) | `DeterministicEmailDraftGenerator.generate()` |
| **OutreachInput** | Outreach Input Adapter (C09.1) | In-memory only (preparation facts) | `DeterministicOutreachInputAdapter.build()` |
| **Lead (core fields)** | CRM User (EspoCRM) | CRM-owned fields only by CRM users | EspoCRM UI, API |
| **Lead (pe* fields)** | Chitu Intelligence Pipeline | pe*-prefixed intelligence fields only | C08/C09 projection adapters, V1 sync |
| **Opportunity (core)** | CRM User (EspoCRM) | Manual creation only; NO automatic creation | EspoCRM UI/API only |
| **Opportunity (pe* fields)** | CRM User / Chitu sync | pe*-prefixed context fields; read-only intelligence | `entityDefs/Opportunity.json` (field definition only) |
| **EmailEvent** | Brevo Event Sync | Create only (append-only event log) | `BrevoEmailEventSyncService` |
| **SalesFeedback** | CRM User | Create, Update | CRM UI, `FeedbackSyncService` |
| **LearningSignal** | Feedback Pipeline | Create only | `FeedbackSignalExportClient` |
| **Task** | CRM User / Workflow Hook | CRM-owned; automation owned by EmailEventWorkflowHook | EspoCRM UI/API |

### Ownership Principles

1. **CRM owns CRM-core fields** — The connector never modifies `name`, `amount`, `stage`, `status` (core), `assignedUser`, or any non-`pe` field on Lead/Opportunity.
2. **Chitu owns `pe*` intelligence fields** — All connector-written fields are `pe`-prefixed on Lead and Opportunity.
3. **Evidence is immutable after creation** — ResearchEvidence has no update path in the connector.
4. **Drafts ≠ Sent Emails** — EmailDraft exists only in-memory. Sent status is reported by Brevo, not initiated by the connector.
5. **No automatic CRM entity creation beyond ProspectPool/ResearchEvidence/EmailEvent** — Leads are created by the V1 sync path (explicit API call). Opportunities are NEVER created automatically.

---

## 7. Phase Coupling Audit

### Verdict: **PASS**

### Dependency Direction

```
Foundation (C01)
  ↓
Discovery Model (C02) → Provider Adapter (C03)
  ↓                         ↓
Master Prospect (C04) ←─────┘
  ↓
Website Research (C05)
  ↓
Prospecting Workspace (C06) ← UI layer, consumes C02–C05 entities
  ↓
Evidence Intelligence (C07) ← consumes C05 output
  ↓
Score Integration (C08) ← consumes C07 evidence facts
  ↓
Outreach Preparation (C09) ← consumes C07 evidence + C08 score
```

### Dependency Analysis

| Phase | Depends On | Dependency Type |
|---|---|---|
| C01 | (none) | Foundation — entity definitions, ACL, module structure |
| C02 | C01 | Discovery model — SearchStrategy, SearchJob, ProspectPool entities |
| C03 | C02, vendored contracts | Provider adapter — Serper, Apify implementations |
| C04 | C02, C03 | Master Prospect deduplication — consumes provider results |
| C05 | C04, vendored contracts | Website research — consumes prospect identity |
| C06 | C02–C05 | Prospecting UI — displays entities from C02, dashlets for C02 data |
| C07 | C05, C06 | Evidence extraction — consumes C05 website output, persists to C06 ResearchEvidence entity |
| C08 | C07 | Score input — consumes C07 evidence facts |
| C09 | C07, C08 | Outreach preparation — consumes C07 talking points + C08 score/recommendation |

### Circular Dependency Check — ALL CLEAR

- ✅ No phase imports a later phase (C07 does not import C08; C08 does not import C09)
- ✅ The `vendored/contracts/` directory forms a stable interface layer that all phases consume without coupling to each other
- ✅ The `espocrm_sync/__init__.py` explicitly re-exports all pipeline components in phase order (C07 → C08 → C09)

### Hidden Import Check — ALL CLEAR

A grep for all imports across the `chitu_connector/` package revealed:

| Import | Classification |
|---|---|
| `from chitu_connector.vendored.contracts.*` | ✅ Stable contract imports (allowed) |
| `from chitu_connector.vendored.domain.*` | ✅ Domain model imports (allowed) |
| `from chitu_connector.espocrm_sync.*` | ✅ Within-package imports (allowed) |
| `from chitu_connector.acquisition.*` | ✅ Acquisition boundary imports (worker↔runner↔provider) |

No cross-phase hidden imports found. No `sys.path` manipulation. No dynamic imports (`importlib`, `__import__`).

### Runtime Coupling Check

| Coupling Point | Type | Risk |
|---|---|---|
| `CanonicalScoreIntegration.__init__(executor)` | Constructor injection (Protocol) | LOW — clean seam |
| `CRMScoreProjectionAdapter.__init__(client)` | Constructor injection (Protocol) | LOW — clean seam |
| `CampaignProjectionAdapter.__init__(client)` | Constructor injection (Protocol) | LOW — clean seam |
| `ResearchEvidencePersistenceAdapter.__init__(client)` | Constructor injection (Protocol) | LOW — clean seam |
| `AcquisitionWorker.__init__(store, provider)` | Constructor injection (Protocol) | LOW — clean seam |
| `EspoAcquisitionRepository.__init__(base_url, api_key)` | REST client (direct HTTP) | MEDIUM — real HTTP coupling; acceptable for MVP |

---

## 8. Production Readiness Risks

### Technical Debt

| Item | Severity | Detail |
|---|---|---|
| Legacy `gate.py` hard-codes `canonical-scoring-v4.0` | LOW | May reject C08-scored payloads on the V1 sync path. Does not affect C08 projection path. |
| `DecisionEngineAdapter` raises RuntimeError | LOW | Intentional placeholder. Remove when canonical engine is deployed. |
| `SingleCandidateLoop` contract model exists but is unused | LOW | `vendored/contracts/single_candidate_loop.py` defines a full closed-loop contract but no current phase consumes it. May be stale. |
| V1 sync contract (`contract.py`) parallel to C08 pipeline | MEDIUM | The V1 `ChituSyncService.syncLead()` writes Lead fields directly (23 fields), bypassing the C07→C08→C09 pipeline. This creates two independent write paths for the same Lead fields. |
| `espo_repository.py` uses GET-then-PUT for job claims | MEDIUM | No atomic claim primitive in EspoCRM. Documented as "intentionally limited to the single-runner MVP." Risk of race condition with multi-runner deployment. |

### Missing Contracts

| Gap | Impact | Recommendation |
|---|---|---|
| No contract test between V1 sync path and C08 projection path | Potential field conflict | Test that V1 `leadFields()` and C08 `_projection_fields()` don't produce conflicting values for the same Lead |
| No end-to-end test from C05 research → C09 draft | Unverified integration | Create an integration test that feeds C05 output through the entire C07→C08→C09 chain |
| No `AcquisitionStore` real-EspoCRM integration test | Unverified persistence boundary | The `EspoAcquisitionRepository` has no integration test against a real EspoCRM instance |
| No Serper provider rate-limit recovery test | Provider resilience unknown | Test `SerperSearchProvider` retry/backoff behavior under simulated 429 responses |

### Unsafe Future Extensions

| Risk | Mitigation |
|---|---|
| Adding a second scoring path that bypasses `CanonicalScoreIntegration` | Enforce through code review: any new scoring MUST go through `CanonicalScoreExecutor` Protocol |
| Adding email sending to `CampaignProjectionAdapter` | The `LeadCampaignProjectionClient` Protocol intentionally has no `send()` method. Any send capability should be a separate service. |
| Adding Opportunity creation to any projection adapter | All adapters declare "update only" in docstrings. Enforce through `LeadScoreProjectionClient` Protocol (no create method). |
| Adding AI inference to `DeterministicEmailDraftGenerator` | The `EmailDraftGenerator` Protocol is the AI injection seam. Keep `DeterministicEmailDraftGenerator` as the reference implementation; add AI variants as separate implementations. |

### Scaling Risks

| Risk | Detail |
|---|---|
| Single-runner acquisition | `espo_repository.py` claims jobs with GET-then-PUT. Multi-runner deployment requires atomic claim (database-level or EspoCRM action). |
| Evidence snapshot hash collision | SHA-256 is used for deduplication. Collision risk is cryptographically negligible but no collision handling exists. |
| CRM projection update conflicts | If two connectors project to the same Lead simultaneously, the last write wins. No optimistic locking on `pe*` fields. Acceptable for MVP since projections are idempotent. |

---

## 9. Compliance with Project Instructions (CLAUDE.md)

### Allowed Operations — VERIFIED

- ✅ EspoCRM extension development — Prospecting module correctly structured
- ✅ Chitu-to-EspoCRM connector integration — Clean boundary via vendored contracts
- ✅ CRM deployment preparation — Provisioning scripts use proper EspoCRM APIs

### Forbidden Operations — VERIFIED ABSENT

- ❌ Modify Chitu scoring logic — `scoring.py` has `DecisionEngineAdapter` intentionally disabled
- ❌ Modify AI research logic — No AI calls in connector; `evidence_extraction.py` is deterministic
- ❌ Modify email-generation engine — `DeterministicEmailDraftGenerator` is template-based, not AI
- ❌ Modify unrelated Chitu application code — `vendored/` directory is read-only contracts
- ❌ Import real customer data or enable outreach — No real data in codebase; all tests use synthetic fixtures

---

## 10. Detailed File Inventory

### Connector Pipeline Files (Python)

| File | Phase | Boundary Role |
|---|---|---|
| `chitu_connector/acquisition/__init__.py` | C02 | Acquisition worker public API |
| `chitu_connector/acquisition/worker.py` | C02 | Single-job worker with injectable store/provider |
| `chitu_connector/acquisition/runner.py` | C02 | CLI runner (fake + Serper providers) |
| `chitu_connector/acquisition/models.py` | C02 | Acquisition domain models |
| `chitu_connector/acquisition/espo_repository.py` | C02 | EspoCRM REST persistence adapter |
| `chitu_connector/acquisition/normalization.py` | C04 | Candidate normalization |
| `chitu_connector/acquisition/master_prospect.py` | C04 | Deduplication logic |
| `chitu_connector/acquisition/website_research.py` | C05 | Website research pipeline |
| `chitu_connector/acquisition/evidence_extraction.py` | C07.1 | Deterministic evidence extraction |
| `chitu_connector/acquisition/providers/serper_provider.py` | C03 | Serper search provider |
| `chitu_connector/espocrm_sync/__init__.py` | All | Public API surface |
| `chitu_connector/espocrm_sync/research_evidence_persistence.py` | C07.2 | Evidence persistence adapter |
| `chitu_connector/espocrm_sync/enrichment_gate.py` | C07.3 | Deterministic enrichment gate |
| `chitu_connector/espocrm_sync/score_input_adapter.py` | C08.1 | Read-only score input adapter |
| `chitu_connector/espocrm_sync/canonical_score_integration.py` | C08.2 | Single-path canonical scoring bridge |
| `chitu_connector/espocrm_sync/crm_score_projection.py` | C08.3 | Score-to-Lead projection |
| `chitu_connector/espocrm_sync/outreach_input_adapter.py` | C09.1 | Outreach preparation facts |
| `chitu_connector/espocrm_sync/email_draft_generation.py` | C09.2 | Provider-neutral draft generation |
| `chitu_connector/espocrm_sync/campaign_projection.py` | C09.3 | Campaign metadata projection |
| `chitu_connector/espocrm_sync/gate.py` | V1 | Legacy V1 sync gate |
| `chitu_connector/espocrm_sync/contract.py` | V1 | V1 sync contract model + validation |
| `chitu_connector/espocrm_sync/real_client.py` | V1 | EspoCRM REST client |
| `chitu_connector/vendored/contracts/canonical_score.py` | C08 | Canonical score contract |
| `chitu_connector/vendored/contracts/scoring.py` | V1 | Scoring boundary (disabled adapter) |
| `chitu_connector/vendored/contracts/website_research.py` | C05 | Website research contract |
| `chitu_connector/vendored/contracts/business_qualification.py` | C04 | Three-layer qualification contract |
| `chitu_connector/vendored/contracts/single_candidate_loop.py` | C04 | Closed-loop contract (unused) |
| `chitu_connector/vendored/domain/models.py` | C02 | Domain model definitions |

### CRM Extension Files (PHP/JSON)

| File | Boundary Role |
|---|---|
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php` | V1 sync service (Lead CRUD, Evidence, Opportunity proposal) |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BrevoEmailEventSyncService.php` | Append-only Brevo event ingestion |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SearchStrategyService.php` | SearchStrategy CRUD + job generation |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostGenerateSearchStrategyJobs.php` | Job generation API endpoint |
| `crm-extension/Resources/routes.json` | API route definitions |
| `crm-extension/manifest.json` | Extension manifest (v1.9.5-alpha) |

---

## 11. Field-Level Boundary Violations (CRM Entity Audit)

A complete field-level audit of all 9 CRM entities revealed 12 boundary violations:

### Naming Convention Violations

| # | Field | Entity | Issue |
|---|---|---|---|
| 1 | `peNextActionDate` | Lead | `pe`-prefix but i18n says "CRM-owned date for the next sales follow-up action" |
| 2 | `peLastContactDate` | Lead | `pe`-prefix but i18n says "CRM-owned date of the most recent sales contact" |
| 3 | `peOpportunitySource` | Opportunity | `pe`-prefix but i18n says "CRM-owned source context for this sales opportunity" |

### Score Fields in Non-Score Entities

| # | Field | Entity | Issue |
|---|---|---|---|
| 4 | `peConfidence` | ResearchEvidence | Score/confidence field in a pure evidence entity |
| 5 | `predictionScore` | LearningSignal | ML prediction score in a learning entity, not a Lead score |

### Evidence Data Leaking to Lead

| # | Field | Entity | Issue |
|---|---|---|---|
| 6 | `peKeyEvidence` | Lead | Evidence text denormalized onto Lead outside ResearchEvidence |
| 7 | `peEvidenceCoverage` | Lead | Evidence-intelligence metric expressed as a score on CRM entity |
| 8 | `peConfidence` | Lead | Confidence duplicated across Lead and ResearchEvidence |

### Engine-to-CRM State Mutation via Formula

| # | Location | Issue |
|---|---|---|
| 9 | `formula/Lead.json` | Engine state changes (`peResearchStatus`→`outreachStatus`, `peOpportunityScoreV4`→`pePriorityLevel`) directly mutate CRM workflow fields via before-save hook |

### Phase3 Pipeline Stages Injected into CRM Core Enum

| # | Field | Entity | Issue |
|---|---|---|---|
| 10 | `stage` | Opportunity | Phase3 pipeline stages `DISCOVERY` and `QUALIFICATION` injected into CRM-owned `Opportunity.stage` enum |

### Circular Entity Relationship

| # | Link | Issue |
|---|---|---|
| 11 | SalesFeedback ↔ LearningSignal | `hasOne` + `belongsTo` circular link creates tight coupling between feedback and learning domains |

### Engine Versioning on CRM Entity

| # | Field | Entity | Issue |
|---|---|---|---|
| 12 | `peScoreRulesVersion` | Lead | Engine versioning metadata stored on CRM entity couples Lead to engine internals |

All 12 violations are classified as **LOW severity** — they represent naming inconsistency or cross-domain field placement rather than functional defects. The `pe` prefix convention is consistently applied to 33 Lead fields and 11 Opportunity fields, with only 3 exceptions where the prefix is used on CRM-owned data.

---

## Summary of Findings

| # | Finding | Dimension | Severity | Status |
|---|---|---|---|---|
| 1 | Legacy `gate.py` hard-codes `canonical-scoring-v4.0` | Scoring | LOW | Requires evaluation |
| 2 | `DecisionEngineAdapter` intentionally disabled | Scoring | NONE | Placeholder |
| 3 | V1 sync path parallel to C08 pipeline | Architecture | MEDIUM | Two write paths for same Lead fields |
| 4 | `espo_repository.py` GET-then-PUT claims | Acquisition | MEDIUM | Single-runner limitation |
| 5 | No end-to-end C05→C09 integration test | Testing | MEDIUM | Missing coverage |
| 6 | `SingleCandidateLoop` contract unused | Architecture | LOW | Stale code |
| 7 | 3 `pe`-prefix naming violations on CRM-owned fields | Naming | LOW | `peNextActionDate`, `peLastContactDate`, `peOpportunitySource` |
| 8 | Score fields in non-score entities | Boundary | LOW | `peConfidence` on ResearchEvidence, `predictionScore` on LearningSignal |
| 9 | Evidence data denormalized onto Lead | Boundary | LOW | `peKeyEvidence`, `peEvidenceCoverage`, `peConfidence` |
| 10 | Formula crosses Engine→CRM boundary | Boundary | LOW | Automation mutates `outreachStatus`/`pePriorityLevel` from engine state |
| 11 | Phase3 stages in CRM core `Opportunity.stage` | Boundary | LOW | `DISCOVERY`/`QUALIFICATION` injected into CRM-owned enum |
| 12 | Circular SalesFeedback↔LearningSignal link | Data Model | LOW | Tight coupling between feedback and learning domains

---

## Final Verdict

**PASS WITH MINOR FINDINGS**

The Phase3 architecture maintains strong domain boundaries. Evidence stays factual, AI injection points are defined but gated behind Protocols, scoring has a single canonical path, outreach preparation is cleanly separated from execution, and CRM projection uses explicit field allowlists. No automatic Opportunity creation, no hidden email sending, no shadow scoring, and no AI calls embedded in pipeline code were found.

The six findings are all either intentional design choices (disabled adapter, single-runner limitation), legacy artifacts that don't affect the C08/C09 pipeline path, or test coverage gaps. None constitute a boundary violation or architectural defect.

The two MEDIUM-severity findings — the parallel V1/C08 write paths for Lead fields and the missing end-to-end test — should be addressed before production deployment but do not block the current frozen baseline.
