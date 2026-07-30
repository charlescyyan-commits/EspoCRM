# C24 Invariant Registry

| Field | Value |
| --- | --- |
| Document Type | Governance Registry |
| Status | DOCUMENTATION_ONLY |
| Owner | Phase3C24 Revenue Operations Governance |
| Scope | Revenue outcome governance and human commercial decision support |
| Related Charter | `docs/PHASE3C24_CHARTER.md` |
| Related Review | `docs/audit/PHASE3C24_CHARTER_RATIFICATION_REVIEW.md` |
| Baseline | `9814c57` |

This registry formalizes the six ratified C24 Charter invariants. It creates no
entity, service, metadata, route, client surface, test, runtime, or CRM
lifecycle behavior. Every invariant remains **DOCUMENTATION_ONLY** until its
owning ADR, implementation work package, and independent governance review are
approved.

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

## 6. Layer Separation

| Source Layer | Source Ownership | C24 Permitted Relationship | C24 Prohibition |
| --- | --- | --- | --- |
| C20 | Provider contracts, credentials, AI runtime, routing, egress | Future model use only through a C20 capability boundary | Direct provider, credential, SDK, or transport ownership |
| C21 | Research evidence, qualification intelligence, human feedback | Read-only analytical context | Qualification scoring, ranking, intelligence replacement, mutation |
| C22 | ProspectRun, ActionGate, ExecutionLedger, ReplyDetection | Read-only outcome evidence | Triggering execution, influencing ActionGate, mutation, auto-send |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only contextual consumption | Redefining acquisition-effectiveness metrics or parallel optimization authority |
| CRM Core | Lead, Opportunity, Account, sales stage, forecast commitment | Human-directed commercial action outside C24 | Automatic create, move, close, or commit lifecycle records |

## Summary

| Category | Count |
| --- | ---: |
| Ownership Boundary | 1 |
| Lifecycle Governance | 2 |
| Advisory Boundary | 1 |
| Human Governance | 1 |
| Metric Integrity | 1 |
| Layer Separation | 6 cross-layer directions |
| **Formal invariant total** | **6** |

## Registry Rules

- Every formal invariant ID appears exactly once in this registry.
- All six formal invariants have status `DOCUMENTATION_ONLY`.
- This registry does not authorize implementation of `ReplySignal`,
  `OpportunityCandidate`, `PipelineMetric`, `RevenueInsight`, or any related
  service, metadata, UI, test, or automation.

## References

- `docs/PHASE3C24_CHARTER.md`
- `docs/audit/PHASE3C24_CHARTER_RATIFICATION_REVIEW.md`
- `docs/audit/ADR-C24-001_OPPORTUNITY_OWNERSHIP_BOUNDARY.md`
- `docs/audit/ADR-C24-002_REPLY_SIGNAL_GOVERNANCE.md`
- `docs/audit/ADR-C24-003_PIPELINE_METRIC_GOVERNANCE.md`
- `docs/audit/ADR-C24-004_REVENUE_INSIGHT_LIFECYCLE.md`
- `docs/audit/ADR-C24-005_FORECAST_HUMAN_GOVERNANCE.md`
