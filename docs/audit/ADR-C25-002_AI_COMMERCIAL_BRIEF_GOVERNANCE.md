# ADR-C25-002: AI Commercial Brief Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); CommercialBrief application delivery FROZEN (WP2.2) |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); WP2.2 freeze `phase3c25-wp2-2-freeze` |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) §5.2; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md`; ADR-C25-001; ADR-C25-005; ADR-C25-006 |
| Related Invariants | `C25-INV-ADV-001`, `C25-INV-PROV-001`, `C25-INV-HG-001`, `C25-INV-INT-006` |
| Implementation Authorization | None for invariant activation; WP2.2 application delivery separately FROZEN |
| Freeze references | `phase3c25-wp2-2-freeze` — does not activate invariants or Runtime Expansion |

## 1. Context

Human commercial operators need a human-readable summary that synthesizes the
assembled CommercialContext (ADR-C25-001) into decision-support material.
Without an explicit governance decision, an AI-generated brief could become a
second source of business facts, assert priority/lifecycle/revenue authority
it does not own, mutate after generation, or trigger downstream action.

This ADR defines the AI Commercial Brief (WP2) as an immutable projection
artifact with a human-review lifecycle. It resolves charter open question Q1
(brief persistence and lifecycle).

## 2. Decision

An AI Commercial Brief is a **persistent, immutable projection artifact — not
a business authority**. It is an AI-generated, human-reviewable summary of
commercial evidence at a point in time, generated only by explicit human
request (charter §8: no scheduler, worker, webhook, or autonomous trigger).

Its human-review lifecycle is:

```text
GENERATED -> REVIEWED -> ACCEPTED
                      -> DISMISSED
```

`ACCEPTED` means a human accepts the brief as valid decision-support material
(charter Gate 8). It does not approve execution, authorize a CRM change,
transition an OpportunityCandidate, create an Opportunity, commit a forecast,
or prioritize any work. `ACCEPTED` and `DISMISSED` are human decisions and
are terminal for the brief; the commercial action decision (Gate 9) happens
outside C25.

## 3. Content Structure

Every brief contains four advisory sections:

| Section | Content |
| --- | --- |
| Customer Situation | Synthesized context about the prospect, their organization, and relevant intelligence |
| Commercial Signals | Interpreted evidence of commercial interest, intent, or opportunity |
| Risk Factors | Identified risks, gaps in evidence, or areas requiring human attention |
| Suggested Review Points | Advisory prompts for human commercial evaluation — phrased as observations, never directives |

## 4. Mandatory Fields

Every AI Commercial Brief MUST record:

| Field | Purpose |
| --- | --- |
| Source record IDs | Entity type and ID for every source artifact referenced |
| Reporting period | The time window the brief covers |
| Generated timestamp | When the brief was produced |
| Generation version | Version of the generation logic/prompt |
| Source AIJob ID | The C20 AIJob that produced this generation |
| Source AIRequestLog IDs | The C20 AIRequestLog records for provider invocations |
| Provider | The AI provider used (via C20 routing) |
| Model | The model used for generation |
| Advisory designation | Mandatory label, verbatim: "AI-generated commercial summary — for human review only. Not a forecast, commitment, or decision." |

The five provenance fields (`sourceAIJobId`, `sourceAIRequestLogId`,
`provider`, `model`, `generationVersion`) implement C25-INV-PROV-001. A brief
missing any mandatory field is invalid and must be rejected by validation.

The brief schema MUST also carry a fixed machine-readable designation field
`legalDesignation` with the constant value
`AI-GENERATED_ADVISORY_PROJECTION_NOT_A_COMMERCIAL_DECISION` — the
machine-readable counterpart to the human-readable advisory designation
(Risk Review R3c/E4).

## 5. Field Authority Constraints

Brief fields MUST NOT constitute a second source of business facts.

**Forbidden authority fields.** The Brief MUST NOT contain fields that
assert — excluded at the schema level, not by convention (Risk Review
R2b/E3):

| Forbidden Field Type | Rationale | Example (FORBIDDEN) |
| --- | --- | --- |
| Priority authority | Human owns prioritization; Brief does not rank | `OpportunityPriority = High` |
| Ranking authority | Human owns ranking; Brief does not order | `Rank = 1` |
| Score authority | Chitu owns canonical_score; C25 owns no scores | `Score = 95` |
| Probability authority | Commercial outcomes are not AI-predictable | `Close probability = 80%` |
| Revenue impact authority | CRM Core and C24 own revenue facts | `Revenue impact = $50K` |
| Commercial ranking authority | Brief is not an ordering surface | `Top candidate`, `#1 of 12` |
| Lifecycle authority | C24 owns OpportunityCandidate lifecycle | `Recommended lifecycle stage: Qualified` |
| Opportunity stage authority | CRM Core owns Opportunity stages | `Suggested Stage: Negotiation` |
| Revenue truth authority | CRM Core and C24 own revenue facts | `Forecast = $50K`, `Commit = Close in Q3` |

**Proxy prohibition (Risk Review §2, R3a/B1).** The Brief MUST NOT become a
scoring proxy, ranking proxy, or forecast proxy. The field prohibitions
above extend to equivalent natural-language constructs: summary judgments
("High," "Strong," "Top") without evidence anchoring are forbidden. Every
observation MUST use specific, evidence-anchored language anchored to
source records — "3 ReplySignals detected within 14 days; all classified
as COMMERCIAL_INQUIRY" — not summary-level judgments that function as a
de facto score.

**Permitted presentation forms.** Information a reader might interpret as
authoritative MUST use observation, analysis, or explanation forms:

| Permitted Form | Example (PERMITTED) |
| --- | --- |
| Observation | `Observed market signal: 3 ReplySignals in 14 days, all COMMERCIAL_INQUIRY` |
| Analysis | `AI analysis: ReplySignal confidence and engagement velocity suggest commercial interest` |
| Explanation | `AI explanation: Historical pattern indicates stronger engagement when 3+ ReplySignals are detected within 14 days` |
| Review point | `Consider reviewing: This candidate has accumulated signals across multiple channels. Human priority assessment recommended.` |

**Governance rule:** the Brief describes what the evidence shows. It does not
declare what the business should do. Every field that could be read as a
decision carries an explicit observation/analysis/explanation label, never an
authority label.

## 6. Immutability, Supersession, and Deletion

| Rule | Requirement |
| --- | --- |
| Immutability | Once generated, a brief is immutable — no field may be updated |
| Supersession | A changed interpretation requires a new superseding brief; the superseding brief MUST reference the brief it supersedes; provenance fields survive supersession |
| Version preservation | All brief versions are preserved for audit |
| Superseded presentation | Superseded briefs default to visually de-emphasized (collapsed or hidden) in all presentation surfaces; the current version is the default view (Risk Review R2c/B3) |
| Generation context | Brief generation MUST NOT read prior briefs for the same candidate as source context; each brief is a fresh projection of governed evidence at generation time — prior briefs are preserved for audit, not used as input (Risk Review R3b/B2) |
| Deletion rule | Deleting all AI Commercial Briefs MUST NOT lose any business fact. Briefs are projections of governed evidence; facts reside in C20–C24 and CRM Core source artifacts |
| Provenance survival | The C20 AIJob/AIRequestLog provenance chain is independent of brief lifecycle and survives brief deletion |

## 7. Human Review Gate

| Rule | Requirement |
| --- | --- |
| Individual review | Each brief requires individual human review; batch brief generation without a human review gate is forbidden |
| Acceptance semantics | ACCEPTED = valid decision-support material only; zero operational side effect |
| Acceptance scope | Brief ACCEPTED status is machine-readable as `acceptanceScope: "DECISION_SUPPORT_MATERIAL_ONLY"` — acceptance records decision-support validity, never approval, prioritization, or commitment (Risk Review R2a/B6) |
| Freshness declaration | Briefs MUST declare generation timestamp and evidence freshness, surfacing C24 staleness status |
| Constraint phrasing | Briefs MUST NOT contain execution directives, CRM mutation commands, or forecast commitments; suggestions are phrased as observations ("Consider reviewing..." not "The pipeline should be...") |

### 7.1 Acceptance Creates No Commercial Truth

Brief review — including ACCEPTED — evaluates the brief as decision-support
material only. It does not create commercial truth: no business fact, no
priority, no ranking, no forecast, and no lifecycle effect results from
brief acceptance. Commercial facts remain exclusively in their C20–C24 and
CRM Core source artifacts. The acceptance event is governed audit material
(ADR-C25-006 §4), not a commercial record.

### 7.2 Human Feedback Boundary

Humans may record feedback on a brief — its usefulness, clarity, and
explanation quality — governed by ADR-C25-006 §5. Brief feedback is C25
feedback (AI explanation quality); it is not C21 HumanFeedback (evidence
quality, intelligence interpretation). Feedback MUST NOT automatically
regenerate the brief, modify any source artifact, or change C21/C24 truth.
Any regeneration is a new human-initiated generation (charter §8) producing
a new superseding brief.

## 8. Explicit Prohibitions

- No authority fields (priority, ranking, score, probability, revenue
  impact, commercial ranking, lifecycle, stage, revenue truth) — excluded
  at schema level.
- No brief as scoring proxy, ranking proxy, or forecast proxy, in fields
  or in natural-language summary judgments (§5).
- No mutable brief — correction only by superseding brief.
- No brief generation reading prior briefs as source context (§6).
- No brief without the mandatory advisory designation.
- No brief without the full C20 provenance chain.
- No brief-triggered workflow, automation, ActionGate evidence, or candidate
  state change.
- No brief appearance in standard CRM Core entity lists or global search
  without an explicit "include AI projections" toggle (Risk Review R2d/B5).
- No scheduled, event-driven, or autonomous brief generation (Phase 1).

## 9. Consequences

Future brief schemas must enforce the mandatory field set, forbidden-field
exclusion, immutability, and supersession references by contract test. The
brief becomes decision-support input to the Human Decision Workspace
(ADR-C25-004); its acceptance is Gate 8 in the extended human governance
chain. This ADR authorizes no entity, schema, service, API, UI, ACL, or
integration implementation.
