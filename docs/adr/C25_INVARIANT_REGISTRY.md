# C25 Invariant Registry

| Field | Value |
| --- | --- |
| Document Type | Governance Registry |
| Status | DOCUMENTATION_ONLY |
| Owner | Phase3C25 AI Commercial Intelligence Governance |
| Scope | AI-assisted commercial intelligence consumption and presentation; no CRM lifecycle or commercial authority |
| Related Charter | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) |
| Related Review | `docs/audit/PHASE3C25_CHARTER_RATIFICATION_REVIEW.md` |
| Related ADR Review | `docs/audit/PHASE3C25_ADR_RATIFICATION_REVIEW.md` |
| Related ADR | `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md` |
| Style Precedent | `docs/adr/C24_INVARIANT_REGISTRY.md` |
| Baseline | `phase3c24-master-freeze` (`6dd784c`); Charter commit `6e2dcf8`; WP2.2 freeze `phase3c25-wp2-2-freeze`; WP3 freeze `phase3c25-wp3-freeze` |
| Reconciliation | ADR Ratification Condition #1 — Path A (INT-006 registered as formal invariant) |
| Invariant activation | **NOT DONE** — all entries remain DOCUMENTATION_ONLY / PROPOSED |

This registry formalizes the C25 invariants for Charter → ADR → Registry
synchronization after ADR package ratification. It creates no entity, service,
metadata, route, client surface, test, runtime, or CRM lifecycle behavior.
Every invariant remains **DOCUMENTATION_ONLY** / **PROPOSED** until its owning
ADR activation trigger, implementation work package, and independent governance
review are approved.

WP2.2 / WP3 freezes deliver application intelligence artifacts only and do
**not** activate any C25 invariant.

Formal set: five category-prefixed invariants from Charter §11 plus
`C25-INV-INT-006` from ADR-C25-006 (Evidence Interpretation Boundary).

## Registry Lifecycle

```text
DOCUMENTATION_ONLY -> PROPOSED -> ACTIVE -> SUPERSEDED
```

An invariant cannot be silently removed. A superseding invariant must identify
the prior ID, preserve its rationale, and receive independent governance review.

## 1. Ownership Boundary

### C25-INV-OWN-001 — Commercial Intelligence Ownership Boundary

| Field | Definition |
| --- | --- |
| ID | `C25-INV-OWN-001` |
| Name | Commercial Intelligence Ownership Boundary |
| Category | Ownership Boundary |
| Purpose | Define the exclusive ownership scope of C25 within the C20–C25 stack. |
| Rule | C25 owns workspace and context interpretation surfaces, but does not own commercial truth, CRM lifecycle, revenue authority, or execution authority. C25 exclusively owns CommercialContext assembly, AI Commercial Brief (immutable projection), the read-only AI Assistant interface, and the Human Decision Workspace presentation layer. C25 MUST NOT own any C20/C21/C22/C23/C24 artifact, any CRM Core entity, or any business fact. |
| Rationale | Prevents the intelligence layer from becoming a parallel authority over facts, metrics, lifecycle, or commercial truth already owned by predecessor layers and CRM Core. |
| Enforcement direction | Future C25 entity/service contracts must be bounded to the four ownership areas. Contract tests must verify zero C25 write paths to C20/C21/C22/C23/C24/CRM Core entities and zero business-fact persistence owned by C25. |
| Relation | Extends `C24-INV-SEP-001`, `C23-INV-OWN-001`, `C22-INV-ID-001`, and C21 intelligence ownership. Absorbs historical candidates `C25-INV-INT-002` and `C25-INV-INT-004`. Complements — does not replace — `C25-INV-INT-006`. |
| Coverage | ADR-C25-001; ADR-C25-005 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 2. Advisory Boundary

### C25-INV-ADV-001 — Advisory Output Non-Authority

| Field | Definition |
| --- | --- |
| ID | `C25-INV-ADV-001` |
| Name | Advisory Output Non-Authority |
| Category | Advisory Boundary |
| Purpose | Ensure every C25 intelligence output is structurally advisory and cannot be misread as operational authority. |
| Rule | All C25 outputs are advisory. AI explanations and summaries cannot become commercial decisions or authoritative recommendations. Every C25 intelligence output — AI Commercial Brief, AI Assistant response, workspace assembly, or decision-support material — MUST NOT act as an execution command, approval directive, CRM mutation instruction, forecast commitment, opportunity-creation trigger, or workflow trigger. Every C25 output MUST carry an explicit advisory designation. |
| Rationale | Extends the C23/C24 advisory-only chain to AI-generated commercial intelligence so summarization never becomes command authority. |
| Enforcement direction | Future C25 output schemas must exclude command, approval, automation, CRM-write, and forecast-commitment fields; every generated artifact must carry mandatory advisory designation; boundary tests must prove no path from C25 output to execution or lifecycle mutation. |
| Relation | Extends `C24-INV-ADV-001`, `C24-INV-REV-001`, `C23-INV-ADV-001`. Maps from historical candidate `C25-INV-INT-001`. Complements `C25-INV-INT-006` for confidence/output non-authority. |
| Coverage | ADR-C25-002; ADR-C25-003; ADR-C25-006 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 3. Human Governance

### C25-INV-HG-001 — Human Decision Delegation

| Field | Definition |
| --- | --- |
| ID | `C25-INV-HG-001` |
| Name | Human Decision Delegation |
| Category | Human Governance |
| Purpose | Keep commercial decisions exclusively human-owned; AI assists, never decides. |
| Rule | Humans own interpretation, prioritization, and action selection. C25 cannot autonomously decide or execute. Commercial interpretation, opportunity prioritization, sales action, revenue decision, forecast commitment, pipeline strategy, and brief acceptance are exclusively human-owned. Every AI-generated recommendation must carry an explicit human-review gate before any operational use. Human decisions are enacted outside C25 through the owning layer's governed service. |
| Rationale | Commercial accountability cannot be delegated to an intelligence or presentation layer. |
| Enforcement direction | Future workspace/brief contracts must require human acceptance before downstream operational use; contract tests must verify zero paths from C25 workspace to C24 Transition Service or CRM Core mutation without an authenticated human actor outside C25. |
| Relation | Extends `C24-INV-HG-001`, `C24-INV-HG-002`, `C23-INV-HG-001`. Maps from historical candidate `C25-INV-INT-003`; absorbs autonomous-action prohibition from historical `C25-INV-INT-005`. |
| Coverage | ADR-C25-004; ADR-C25-006 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 4. Security / Tool Boundary

### C25-INV-SEC-001 — Read-Only Assistant Tool Boundary

| Field | Definition |
| --- | --- |
| ID | `C25-INV-SEC-001` |
| Name | Read-Only Assistant Tool Boundary |
| Category | Security Boundary |
| Purpose | Enforce Assistant read-only behavior by capability absence, not prompt wording. |
| Rule | C25 has no provider ownership, credential ownership, execution runtime, automation authority, or external side effects. The C25 AI Assistant permits only Query, Read, Aggregate, Compare, Explain, and Summarize. It MUST NOT provide Create, Update, Delete, Send Email, Trigger Outreach, Change Lifecycle, Access Credentials, or Direct Provider Call. Primary enforcement is structural allow-list and absence of write paths; prompt refusal is defense-in-depth only. |
| Rationale | Prompt-only constraints are insufficient for commercial safety; forbidden capabilities must not exist in the tool surface. |
| Enforcement direction | Future Assistant tool definitions must be a structural allow-list; service-layer contract tests must verify zero write/send/trigger/lifecycle/credential/direct-provider paths; tool capability must be auditable in code. |
| Relation | Extends C20 D3 / credential custody, `C22-INV-EX-001`, `C22-INV-PR-001`. Absorbs execution/autonomy aspects of historical candidate `C25-INV-INT-005`. |
| Coverage | ADR-C25-003; ADR-C25-005 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 5. Provenance Governance

### C25-INV-PROV-001 — AI Explanation Provenance

| Field | Definition |
| --- | --- |
| ID | `C25-INV-PROV-001` |
| Name | AI Explanation Provenance |
| Category | Provenance Governance |
| Purpose | Preserve source identity and AI generation traceability for every C25 output. |
| Rule | C25 must preserve source artifact identity, revision, freshness, and evidence references. Every AI-generated C25 artifact — AI Commercial Brief, AI Assistant analytical response, or any future C25 AI output — MUST also record: `sourceAIJobId`, `sourceAIRequestLogId`, `provider`, `model`, and `generationVersion`. Outputs without this chain are invalid. The provenance chain MUST survive deletion of the C25 artifact; C20 AIJob/AIRequestLog records are independent of C25 artifact lifecycle. |
| Rationale | Extends measurement/insight provenance to AI explanations so commercial intelligence remains reviewable, attributable, and reproducible. |
| Enforcement direction | Future brief/response schemas must require source identity/revision/freshness/evidence fields plus the five AI provenance fields; validators must reject incomplete provenance; contract tests must verify AIJob/AIRequestLog existence, supersession survival, and that deleting a C25 artifact does not delete C20 provenance. |
| Relation | Extends C20 ADR C8/C9, `C23-INV-PROV-002`, `C24-INV-MET-001`, `C24-INV-REV-004`. Complements `C25-INV-INT-006` for audit non-truthfulness of C25 records. |
| Coverage | ADR-C25-002; ADR-C25-005; ADR-C25-006 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 6. Interpretation Boundary

### C25-INV-INT-006 — Evidence Interpretation Boundary

| Field | Definition |
| --- | --- |
| ID | `C25-INV-INT-006` |
| Name | Evidence Interpretation Boundary |
| Category | Interpretation Boundary |
| Purpose | Ensure C25's interpretation of governed evidence never becomes the canonical source of commercial truth. |
| Rule | C25 may interpret governed evidence, but cannot become the canonical source of commercial truth. C25 may assemble, explain, summarize, and present AI-assisted commercial understanding, but all commercial truth remains in CRM Core and the C20–C24 owning layers. C25 interpretations are advisory projections: they carry evidence basis, confidence indication, freshness consideration, and limitation statement; they never assert outcome certainty; and deleting them loses no business fact. |
| Rationale | Ownership (`OWN-001`), advisory designation (`ADV-001`), and provenance (`PROV-001`) do not by themselves close the interpretation-vs-truth gap: C25 could still be treated as a competing commercial-truth authority unless interpretation is explicitly bounded. |
| Enforcement direction | Contract tests verify: C25 output schemas exclude truth-asserting fields (priority, score, probability, revenue impact, commercial ranking); every AI output carries the four confidence elements from ADR-C25-006 §3.1; deleting all C25 artifacts changes zero fields on any C20–C24 or CRM Core entity. |
| Relation | Extends `C25-INV-OWN-001`, `C25-INV-ADV-001`, and `C24-INV-REV-003`. Sixth C25 formal invariant; supersedes none. Numbering note: Charter v1.0 IDs INT-001–INT-005 were renumbered to category prefixes; INT-006 continues the sequence for the interpretation category and is the only INT-prefixed formal ID. |
| Coverage | ADR-C25-006 |
| Status | DOCUMENTATION_ONLY / PROPOSED |

## 7. Layer Separation Directions

| Source Layer | Source Ownership | C25 Permitted Relationship | C25 Prohibition |
| --- | --- | --- | --- |
| C20 | Provider contracts, credentials, AIJob, AIRequestLog, runtime, routing, egress | Read-only cost/provenance context; model invocation only through C20 capability interfaces | Direct provider, credential, SDK, or transport ownership |
| C21 | ResearchEvidence (governed), AIQualificationInsight, HumanFeedback, IntelligenceAggregate | Read-only intelligence context; may consume feedback about explanation quality only as non-truth input | Qualification scoring, ranking, intelligence replacement, mutation; merging C25 feedback into C21 HumanFeedback |
| C22 | ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, ReplyDetection | Read-only execution history | Triggering execution, influencing ActionGate, mutation, auto-send |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only optimization context | Redefining metrics or parallel optimization authority |
| C24 | ReplySignal, OpportunityCandidate lifecycle, RevenueInsight, PipelineMetric | Read-only evidence for commercial intelligence assembly | Artifact mutation, lifecycle transition, recomputation, bypass of C24 Transition Service |
| CRM Core | Account, Contact, Opportunity, sales stage, forecast, revenue | Read-only commercial context; human-directed action outside C25 | Automatic create, move, close, or commit lifecycle records |

## 8. Evaluation — Confidence / Audit / Feedback

These themes are governed by ADR-C25-006 but are **not** independent formal
invariants. They remain covered by the six-invariant set above.

### 8.1 Confidence — No independent C25 invariant

| Question | Recommendation |
| --- | --- |
| Need independent ID? | **No** |
| Why | Confidence is preserved from source layers and declared as an output-content rule (ADR-C25-006 §3). C25 must surface evidence-anchored confidence indications; it must not invent a competing confidence/scoring authority. |
| Covered by | `C25-INV-INT-006` + `C25-INV-ADV-001`; plus predecessor `C23-INV-MET-001` / `C24-INV-REV-005` |
| Reopen if | Future C25 work introduces a C25-native confidence score that ranks opportunities, drives prioritization, or replaces source-layer confidence |

### 8.2 Audit — No independent C25 invariant

| Question | Recommendation |
| --- | --- |
| Need independent ID? | **No** |
| Why | Audit is covered by C20 AIRequestLog, C24 transition audit, and C25 provenance governance. C25 audit events create no commercial truth under `C25-INV-INT-006`. |
| Covered by | `C25-INV-PROV-001` + `C25-INV-INT-006`; C20 ADR C8; `C24-INV-LIFE-001` |
| Reopen if | Future C25 persists a distinct decision-audit entity that replaces C20 provenance or C24 transition history |

### 8.3 Feedback — No independent C25 invariant

| Question | Recommendation |
| --- | --- |
| Need independent ID? | **No** |
| Why | Feedback ownership remains with C21/C23. C25 only consumes feedback about explanation quality; it must not merge into C21 HumanFeedback or drive automation/truth changes. |
| Covered by | `C25-INV-OWN-001` + `C25-INV-HG-001`; ADR-C25-006 §5 |
| Reopen if | Future Charter Amendment introduces a C25-native feedback artifact with lifecycle, mutation, or learning authority |

### 8.4 Disposition summary

| Candidate Theme | Formal independent invariant? | Disposition |
| --- | --- | --- |
| Confidence | No | Preserved from source layers; output-content rule under INT-006 + ADV-001 |
| Audit | No | Covered by C20 AIRequestLog, C24 transition audit, and C25 PROV-001 |
| Feedback | No | Owned by C21/C23; C25 consumes explanation-quality feedback only |

## 9. Historical INT-* Disposition

Charter v1.0 used generic `C25-INV-INT-*` IDs. Charter v2.1 renumbered
INT-001–INT-005 to category prefixes. ADR-C25-006 registers INT-006 as the
sole INT-prefixed formal invariant.

| Historical ID | Historical Name | Disposition | Canonical ID(s) |
| --- | --- | --- | --- |
| `C25-INV-INT-001` | Advisory Boundary | Renamed / promoted | `C25-INV-ADV-001` |
| `C25-INV-INT-002` | No CRM Lifecycle Ownership | Renamed / expanded | `C25-INV-OWN-001` |
| `C25-INV-INT-003` | Human Decision Authority | Renamed / expanded | `C25-INV-HG-001` |
| `C25-INV-INT-004` | Read-only Source Consumption | Absorbed | `C25-INV-OWN-001` (+ §7 read-only directions); capability side in `C25-INV-SEC-001` |
| `C25-INV-INT-005` | No Autonomous Commercial Action | Absorbed | `C25-INV-HG-001` + `C25-INV-SEC-001` |
| `C25-INV-INT-006` | Evidence Interpretation Boundary | **Formal (registered)** | `C25-INV-INT-006` (this registry §6; ADR-C25-006 §6) |

Absorbed historical candidates INT-001–INT-005 MUST NOT be reintroduced as
parallel formal IDs. INT-006 is formal and must not be reclassified as absorbed
without a superseding ADR and governance review.

## 10. Summary

| Category | Count |
| --- | ---: |
| Ownership Boundary | 1 |
| Advisory Boundary | 1 |
| Human Governance | 1 |
| Security Boundary | 1 |
| Provenance Governance | 1 |
| Interpretation Boundary | 1 |
| Layer Separation | 6 cross-layer directions (non-ID table) |
| Deferred themes (Confidence / Audit / Feedback) | 0 formal IDs |
| **Formal invariant total** | **6** |

| ID | Name | Category | Status |
| --- | --- | --- | --- |
| `C25-INV-OWN-001` | Commercial Intelligence Ownership Boundary | Ownership Boundary | DOCUMENTATION_ONLY / PROPOSED |
| `C25-INV-ADV-001` | Advisory Output Non-Authority | Advisory Boundary | DOCUMENTATION_ONLY / PROPOSED |
| `C25-INV-HG-001` | Human Decision Delegation | Human Governance | DOCUMENTATION_ONLY / PROPOSED |
| `C25-INV-SEC-001` | Read-Only Assistant Tool Boundary | Security Boundary | DOCUMENTATION_ONLY / PROPOSED |
| `C25-INV-PROV-001` | AI Explanation Provenance | Provenance Governance | DOCUMENTATION_ONLY / PROPOSED |
| `C25-INV-INT-006` | Evidence Interpretation Boundary | Interpretation Boundary | DOCUMENTATION_ONLY / PROPOSED |

## Registry Rules

- Every formal invariant ID appears exactly once in this registry.
- All six formal invariants have status `DOCUMENTATION_ONLY` / `PROPOSED`.
- No duplicate IDs.
- No C25 invariant conflicts with, replaces, or weakens C20–C24 invariants;
  each extends predecessor boundaries.
- Confidence, Audit, and Feedback remain non-independent themes — not
  formalized as separate invariant IDs.
- This registry does not authorize implementation of CommercialContext
  persistence authority, AI Commercial Brief automation, AI Assistant write
  tools, CRM mutation, C24 lifecycle transitions, or any related service,
  metadata, UI, test, or automation.

## References

- `docs/PHASE3C25_CHARTER_DRAFT.md`
- `docs/audit/PHASE3C25_CHARTER_REVISION_NOTES.md`
- `docs/audit/PHASE3C25_CHARTER_RATIFICATION_REVIEW.md`
- `docs/audit/PHASE3C25_ADR_RATIFICATION_REVIEW.md`
- `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md`
- `docs/adr/C24_INVARIANT_REGISTRY.md`
- `docs/adr/C23_INVARIANT_REGISTRY.md`
- `docs/adr/C22_INVARIANT_REGISTRY.md`
- `docs/adr/C21_INVARIANT_REGISTRY.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- ADR-C25-001 through ADR-C25-006
