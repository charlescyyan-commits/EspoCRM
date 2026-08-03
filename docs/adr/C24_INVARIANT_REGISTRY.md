# C24 Invariant Registry

| Field | Value |
| --- | --- |
| Document Type | Governance Registry |
| Status | DOCUMENTATION_ONLY |
| Owner | Phase3C24 Revenue Operations Governance |
| Scope | Revenue outcome governance and human commercial decision support |
| Related Charter | `docs/PHASE3C24_CHARTER.md` |
| Related Review | `docs/audit/PHASE3C24_CHARTER_RATIFICATION_REVIEW.md` |
| Baseline | `9814c57`; C25 consume-only confirmed at `phase3c25-wp2-2-freeze` / `phase3c25-wp3-freeze` |

This registry formalizes the ratified C24 Charter invariants, the WP2
reconciliation additions, and the WP3 revenue-analytics invariants required for
Charter → ADR → Registry synchronization. It creates no entity, service,
metadata, route, client surface, test, runtime, or CRM lifecycle behavior.
Every invariant remains **DOCUMENTATION_ONLY** until its owning ADR,
implementation work package, and independent governance review are approved.

**C25 consumer note (WP3/WP4):** C25 may **consume** `OpportunityCandidate`,
`RevenueInsight`, and `PipelineMetric` read-only. C25 must not mutate,
replace, or assume ownership of these entities. WP4 (if later authorized)
remains consume-only toward C24.

## Registry Lifecycle

```text
DOCUMENTATION_ONLY -> PROPOSED -> ACTIVE -> SUPERSEDED
```

An invariant cannot be silently removed. A superseding invariant must identify
the prior ID, preserve its rationale, and receive independent governance review.

## 1. Ownership Boundary

### C24-INV-SEP-001 — Commercial Outcome / Acquisition Effectiveness Separation

| Field | Definition |
| --- | --- |
| ID | `C24-INV-SEP-001` |
| Name | Commercial Outcome / Acquisition Effectiveness Separation |
| Rule | C24 revenue analytics MUST NOT redefine, overwrite, or create a competing version of C23 optimization metrics. C23 owns acquisition effectiveness; C24 owns commercial outcome governance. |
| Rationale | Preserves the distinction between “Did prospecting work?” and “Did prospecting create commercial value?” and prevents conflicting metric authority. |
| Enforcement direction | Future PipelineMetric and RevenueInsight contracts must distinguish their commercial source domain, reject C23 metric ownership fields, and be covered by layer-separation tests. |
| Status | DOCUMENTATION_ONLY |

## 2. Lifecycle Governance

### C24-INV-SEP-002 — Human-Governed OpportunityCandidate Acceptance

| Field | Definition |
| --- | --- |
| ID | `C24-INV-SEP-002` |
| Name | Human-Governed OpportunityCandidate Acceptance |
| Rule | `OpportunityCandidate` acceptance requires an explicit authorized human governance transition. AI signals cannot directly create an `ACCEPTED` opportunity-candidate state. |
| Rationale | A commercial candidate is not a canonical Opportunity and cannot become a human commercial decision by automated inference. |
| Enforcement direction | Future lifecycle contracts must require an authenticated human actor, reason, evidence reference, and immutable transition record for `REVIEW_PENDING -> ACCEPTED`. |
| Status | DOCUMENTATION_ONLY |

### C24-INV-LIFE-001 — Immutable Lifecycle Transition Records

| Field | Definition |
| --- | --- |
| ID | `C24-INV-LIFE-001` |
| Name | Immutable Lifecycle Transition Records |
| Rule | Every permitted OpportunityCandidate lifecycle transition requires an explicit immutable state-transition record containing predecessor state, successor state, timestamp, authorized human actor, applicable reason, and provenance references. |
| Rationale | Makes human commercial governance reviewable and prevents hidden timers, background progression, or silent record rewriting. |
| Enforcement direction | Future transition guards and persistence contracts must reject direct state mutation, automatic progression, terminal-state reopening, and a missing transition record. |
| Status | DOCUMENTATION_ONLY |

## 3. Advisory Boundary

### C24-INV-ADV-001 — Advisory Revenue Artifacts Only

| Field | Definition |
| --- | --- |
| ID | `C24-INV-ADV-001` |
| Name | Advisory Revenue Artifacts Only |
| Rule | `ReplySignal`, `RevenueInsight`, and `PipelineMetric` are advisory interpretations, analyses, or measurements only. They MUST NOT act as execution commands, approval directives, CRM mutation directives, opportunity-creation commands, or workflow triggers. |
| Rationale | C24 informs human commercial judgment; it neither replaces C22 execution governance nor CRM Core lifecycle ownership. |
| Enforcement direction | Future schemas and service contracts must exclude command, approval, automation, CRM-write, and provider-control fields; boundary tests must prove no path from C24 artifacts to execution or lifecycle mutation. |
| Status | DOCUMENTATION_ONLY |

### C24-INV-REV-001 — RevenueInsight Advisory Boundary

| Field | Definition |
| --- | --- |
| ID | `C24-INV-REV-001` |
| Name | RevenueInsight Advisory Boundary |
| Category | Advisory Boundary |
| Rule | `RevenueInsight` provides advisory commercial interpretation only. It cannot execute actions, mutate CRM lifecycle, own Opportunity decisions, or authorize revenue commitments. |
| Rationale | Refines `C24-INV-ADV-001` for the WP3 `RevenueInsight` artifact so analytical acceptance never becomes commercial authority. |
| Enforcement direction | Future RevenueInsight schemas and services must exclude execution, CRM-write, Opportunity-decision, and revenue-commitment fields; boundary tests must prove no mutation or commitment path from insight acceptance. |
| Coverage | ADR-C24-011; ADR-C24-014 |
| Status | DOCUMENTATION_ONLY |

## 4. Human Governance

### C24-INV-HG-001 — Human Ownership of Commercial Decisions

| Field | Definition |
| --- | --- |
| ID | `C24-INV-HG-001` |
| Name | Human Ownership of Commercial Decisions |
| Rule | Opportunity acceptance and rejection, pipeline decisions, forecast approval, CRM stage changes, and commercial actions require explicit authorized human action. |
| Rationale | Commercial accountability cannot be delegated to a governance or analytical layer. |
| Enforcement direction | Future ACL, review, and CRM integration contracts must require a human actor and prohibit automatic acceptance, automatic stage movement, automatic close, and forecast commitment. |
| Status | DOCUMENTATION_ONLY |

### C24-INV-HG-002 — Commercial Decision Ownership

| Field | Definition |
| --- | --- |
| ID | `C24-INV-HG-002` |
| Name | Commercial Decision Ownership |
| Category | Human Governance |
| Purpose | Commercial decision ownership. |
| Rule | Opportunity acceptance requires human decision. Pipeline entry requires human governance. Forecast commitment remains human-owned. AI signals cannot create commercial commitments. No autonomous revenue decisions. |
| Rationale | Closes the Charter / ADR reference gap for human commercial ownership at the WP2 decision boundary: advisory signals may inform judgment, but they cannot accept candidates, enter pipeline, commit forecast, or create revenue obligations. |
| Enforcement direction | Future commercial-decision and pipeline-entry contracts must require an authorized human actor for acceptance, pipeline entry, and forecast commitment; reject AI-authored commercial commitments and autonomous revenue decisions. |
| Coverage | ADR-C24-008; ADR-C24-009 |
| Status | DOCUMENTATION_ONLY |

## 5. Metric Integrity

### C24-INV-MET-001 — Reproducible, Non-Directive Pipeline Measurement

| Field | Definition |
| --- | --- |
| ID | `C24-INV-MET-001` |
| Name | Reproducible, Non-Directive Pipeline Measurement |
| Rule | Every `PipelineMetric` MUST declare source references, computation methodology, reporting period, sample size, and freshness status. No metric, aggregate signal, or single AI score may control opportunity acceptance, forecast acceptance, sales stage, or a revenue decision. |
| Rationale | Measurements must be traceable and reviewable without becoming automated commercial authority. |
| Enforcement direction | Future metric validators must require the declared fields; reporting and integration contracts must reject metric-driven workflow, approval, or CRM lifecycle triggers. |
| Status | DOCUMENTATION_ONLY |

### C24-INV-MET-002 — PipelineMetric Governance Boundary

| Field | Definition |
| --- | --- |
| ID | `C24-INV-MET-002` |
| Name | PipelineMetric Governance Boundary |
| Category | Metric Integrity |
| Purpose | PipelineMetric governance boundary. |
| Rule | `PipelineMetric` belongs to C24 commercial value analysis. It MUST NOT replace C23 `PerformanceMetric`. It MUST NOT create automated revenue decisions. It MUST preserve provenance and measurement period. Metric output is advisory only. |
| Rationale | Keeps C24 commercial-outcome measurement distinct from C23 acquisition-effectiveness measurement, preserves provenance/period integrity, and prevents metric values from becoming automated commercial authority. |
| Enforcement direction | Future PipelineMetric schemas and validators must declare C24 commercial-value domain ownership, reject C23 PerformanceMetric replacement fields, require provenance and measurement period, and exclude automated revenue-decision or workflow-trigger semantics. |
| Coverage | ADR-C24-010 |
| Status | DOCUMENTATION_ONLY |

### C24-INV-REV-002 — PipelineMetric Non-Directive Measurement

| Field | Definition |
| --- | --- |
| ID | `C24-INV-REV-002` |
| Name | PipelineMetric Non-Directive Measurement |
| Category | Metric Integrity |
| Rule | `PipelineMetric` measures commercial performance but cannot trigger workflow, automation, CRM mutation, or business decisions. |
| Rationale | Extends metric non-directive governance for WP3 so measurement never becomes an automated commercial or CRM control plane. |
| Enforcement direction | Future PipelineMetric contracts must reject workflow-trigger, automation, CRM-mutation, and decision-authority fields; integration tests must prove metrics cannot initiate actions. |
| Coverage | ADR-C24-012 |
| Status | DOCUMENTATION_ONLY |

### C24-INV-REV-004 — PipelineMetric Provenance Integrity

| Field | Definition |
| --- | --- |
| ID | `C24-INV-REV-004` |
| Name | PipelineMetric Provenance Integrity |
| Category | Metric Integrity |
| Rule | `PipelineMetric` requires provenance, methodology, reporting period, and freshness metadata. |
| Rationale | Makes WP3 commercial measurements reviewable and reproducible before any human uses them as advisory context. |
| Enforcement direction | Future PipelineMetric validators must require provenance, methodology, reporting period, and freshness; incomplete metric records must be rejected. |
| Coverage | ADR-C24-012; ADR-C24-015 |
| Status | DOCUMENTATION_ONLY |

## 6. Layer Separation

### C24-INV-REV-003 — Revenue Analytics Lifecycle Separation

| Field | Definition |
| --- | --- |
| ID | `C24-INV-REV-003` |
| Name | Revenue Analytics Lifecycle Separation |
| Category | Layer Separation |
| Rule | Revenue analytics cannot mutate CRM Core lifecycle entities or replace CRM Opportunity ownership. |
| Rationale | Keeps WP3 analytics on the advisory side of the CRM Core boundary and preserves human/CRM ownership of Opportunity lifecycle. |
| Enforcement direction | Future RevenueInsight and PipelineMetric contracts must remain read-only toward CRM Core lifecycle entities and must not encode Opportunity ownership transfer or mutation semantics. |
| Coverage | ADR-C24-011; ADR-C24-012 |
| Status | DOCUMENTATION_ONLY |

| Source Layer | Source Ownership | C24 Permitted Relationship | C24 Prohibition |
| --- | --- | --- | --- |
| C20 | Provider contracts, credentials, AI runtime, routing, egress | Future model use only through a C20 capability boundary | Direct provider, credential, SDK, or transport ownership |
| C21 | Research evidence, qualification intelligence, human feedback | Read-only analytical context | Qualification scoring, ranking, intelligence replacement, mutation |
| C22 | ProspectRun, ActionGate, ExecutionLedger, ReplyDetection | Read-only outcome evidence | Triggering execution, influencing ActionGate, mutation, auto-send |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only contextual consumption | Redefining acquisition-effectiveness metrics or parallel optimization authority |
| CRM Core | Lead, Opportunity, Account, sales stage, forecast commitment | Human-directed commercial action outside C24 | Automatic create, move, close, or commit lifecycle records |

## 7. Data Governance

### C24-INV-REV-005 — RevenueInsight Freshness Governance

| Field | Definition |
| --- | --- |
| ID | `C24-INV-REV-005` |
| Name | RevenueInsight Freshness Governance |
| Category | Data Governance |
| Rule | `RevenueInsight` must preserve freshness status, provenance, and analytical validity context. |
| Rationale | Prevents stale or unprovenanced advisory insights from being treated as currently valid commercial guidance. |
| Enforcement direction | Future RevenueInsight schemas and review surfaces must require freshness status, provenance, and analytical validity context; stale insights must surface mandatory freshness warnings and may only be corrected by supersession. |
| Coverage | ADR-C24-015 |
| Status | DOCUMENTATION_ONLY |

## Summary

| Category | Count |
| --- | ---: |
| Ownership Boundary | 1 |
| Lifecycle Governance | 2 |
| Advisory Boundary | 2 |
| Human Governance | 2 |
| Metric Integrity | 4 |
| Layer Separation | 1 formal + 6 cross-layer directions |
| Data Governance | 1 |
| **Formal invariant total** | **13** |

## Registry Rules

- Every formal invariant ID appears exactly once in this registry.
- All thirteen formal invariants have status `DOCUMENTATION_ONLY`.
- This registry does not authorize implementation of `ReplySignal`,
  `OpportunityCandidate`, `PipelineMetric`, `RevenueInsight`, or any related
  service, metadata, UI, test, or automation.

## References

- `docs/PHASE3C24_CHARTER.md`
- `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md`
- `docs/PHASE3C24_WP3_REVENUE_INSIGHT_CHARTER.md`
- `docs/audit/PHASE3C24_CHARTER_RATIFICATION_REVIEW.md`
- `docs/audit/PHASE3C24_WP2_ADR_RATIFICATION_REVIEW.md`
- `docs/audit/PHASE3C24_WP3_CHARTER_RATIFICATION_REVIEW.md`
- `docs/audit/PHASE3C24_WP3_ADR_RATIFICATION_REVIEW.md`
- `docs/audit/ADR-C24-001_OPPORTUNITY_OWNERSHIP_BOUNDARY.md`
- `docs/audit/ADR-C24-002_REPLY_SIGNAL_GOVERNANCE.md`
- `docs/audit/ADR-C24-003_PIPELINE_METRIC_GOVERNANCE.md`
- `docs/audit/ADR-C24-004_REVENUE_INSIGHT_LIFECYCLE.md`
- `docs/audit/ADR-C24-005_FORECAST_HUMAN_GOVERNANCE.md`
- `docs/audit/ADR-C24-008_COMMERCIAL_DECISION_BOUNDARY.md`
- `docs/audit/ADR-C24-009_PIPELINE_ENTRY_GOVERNANCE.md`
- `docs/audit/ADR-C24-010_PIPELINE_METRIC_GOVERNANCE.md`
- `docs/audit/ADR-C24-011_REVENUE_INSIGHT_OWNERSHIP_BOUNDARY.md`
- `docs/audit/ADR-C24-012_PIPELINE_METRIC_GOVERNANCE.md`
- `docs/audit/ADR-C24-013_REVENUE_INSIGHT_LIFECYCLE.md`
- `docs/audit/ADR-C24-014_COMMERCIAL_ANALYTICS_HUMAN_GOVERNANCE.md`
- `docs/audit/ADR-C24-015_REVENUE_DATA_FRESHNESS_PROCESSANCE.md`
