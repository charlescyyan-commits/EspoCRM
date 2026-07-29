# C23 Invariant Registry

| Field | Value |
| --- | --- |
| **Document Type** | Governance Registry |
| **Status** | DOCUMENTATION_ONLY |
| **Owner** | Phase3C23 Governance |
| **Scope** | AI Prospecting Optimization & Learning Governance |
| **Related Charter** | `docs/PHASE3C23_CHARTER.md` §11 |
| **Related ADR** | `docs/audit/ADR-C23-001_OPTIMIZATION_OWNERSHIP_BOUNDARY.md` |
| **Baseline** | `phase3c22-final-freeze` |

This registry promotes the twenty-two C23 Charter invariants into the formal
governance index. It authorizes no entity, metadata, service, client, metric,
or automation implementation. Every invariant is **DOCUMENTATION_ONLY** until
its owning ADR, activation trigger, and enforcement mechanism are accepted for
the relevant future work package.

## Lifecycle

```text
DOCUMENTATION_ONLY -> PROPOSED -> ACTIVE -> SUPERSEDED
```

An invariant is not silently removed. A replacement must name the superseded
invariant, preserve its governance rationale, and receive an independent review.

## 1. Ownership Boundary

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-OWN-001 | C23 exclusively owns future `OptimizationInsight` and `PerformanceMetric` records; no other layer may create, modify, or delete them. | Keeps optimization learning distinct from C20 execution, C21 intelligence, C22 execution governance, and CRM lifecycle. | C23 | Future entity ownership guards and contract tests under the owning C23 ADRs. | C22 writes an `OptimizationInsight` to justify an execution decision. | DOCUMENTATION_ONLY — activate when the entities and their owning services are approved. |
| C23-INV-OWN-002 | C23 owns no C20, C21, C22, CRM Core, or Chitu entity; its cross-layer consumption is read-only and governed by the source layer. | Analysis must not become lifecycle or intelligence authority. | Source layer for each consumed record; C23 only consumes. | Future read-only access contracts and absence tests. | C23 updates an `AIJob`, `ActionGate`, `Lead`, or `canonical_score`. | DOCUMENTATION_ONLY — activate with cross-layer read contracts. |
| C23-INV-OWN-003 | `OptimizationInsight` is immutable after creation; any changed conclusion or review outcome is represented by a new superseding record. | Preserves a trustworthy history of advisory conclusions. | C23 | Future append-only persistence guard and supersession contract test. | An operator edits an existing insight recommendation in place. | DOCUMENTATION_ONLY — activate when `OptimizationInsight` persistence is approved. |
| C23-INV-OWN-004 | `PerformanceMetric` is immutable after creation; each record is a point-in-time measurement and recalculation creates a new record. | Prevents silent rewriting of historical operational evidence. | C23 | Future append-only persistence guard and metric history contract test. | A service overwrites last month's reply-rate value. | DOCUMENTATION_ONLY — activate when `PerformanceMetric` persistence is approved. |

## 2. Provenance Governance

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-PROV-001 | Every `OptimizationInsight` must reference specific supporting source evidence by entity type and identifier; an insight without evidence is invalid. | Human reviewers must be able to trace a recommendation to governed evidence. | C23 | Future validation service and provenance contract test. | An insight says “change template” with no source evidence. | DOCUMENTATION_ONLY — activate with insight creation validation. |
| C23-INV-PROV-002 | Every `PerformanceMetric` must declare scope, measurement period, sample size, source references, and computation methodology; an undeclared metric is invalid. | Makes analytical claims reproducible and reviewable. | C23 | Future metric validation service and reproducibility contract test. | A provider-performance rate is stored without a period or population. | DOCUMENTATION_ONLY — activate with metric computation implementation. |
| C23-INV-PROV-003 | `OptimizationInsight.evidenceReference` must contain aggregate operational evidence only. It must not reference `ProspectCandidate`, `ProspectPool`, `Lead`, `Account`, `Opportunity`, `ResearchEvidence`, or `AIQualificationInsight`. | Prevents C23 from accumulating per-prospect intelligence or CRM identity data. | C23 | Future allow-list validator and forbidden-reference contract test. | An insight cites a named `ProspectCandidate` or an `AIQualificationInsight`. | DOCUMENTATION_ONLY — activate with insight evidence-reference validation. |
| C23-INV-PROV-004 | Every `OptimizationInsight` must declare a `sourcePeriod` (`sourcePeriodStart` and `sourcePeriodEnd`), `generatedAt`, and `freshnessStatus`. `sourcePeriodEnd` older than 180 days or `generatedAt` older than 60 days requires `STALE`; stale insights require an explicit warning when displayed. | Prevents outdated aggregate evidence from being presented as a current recommendation. | C23 | Future freshness classifier, display guard, and contract test. | A six-month-old insight is displayed as current without a staleness warning. | DOCUMENTATION_ONLY — activate with insight creation and display surfaces. |

## 3. Advisory Only

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-ADV-001 | No C23 AI output may be interpreted as an execution, approval, or decision directive; future C23 records must not contain execution, approval, or authorization authority fields. | C23 is an analytical learning layer, not an operational control plane. | C23 | Future entity-schema allow-list and advisory-output contract test. | An insight includes an `approve` or `execute` field. | DOCUMENTATION_ONLY — activate with any C23 output contract. |
| C23-INV-ADV-002 | Any future C23 AI model invocation must route through C20 capability interfaces; C23 must not hold credentials or invoke providers directly. | Reaffirms C20 D3, provider custody, and sole-egress governance. | C20 for provider capability; C23 as consumer. | Future dependency contract and static egress/credential tests. | A C23 service calls a model SDK with its own API key. | DOCUMENTATION_ONLY — activate before any C23 AI-assisted analysis. |
| C23-INV-ADV-003 | C23 output must not be phrased or structured as “approve”, “send”, “execute”, “create”, “switch”, “route”, “schedule”, or “reallocate”; output is limited to observations, patterns, correlations, and suggestions. | Prevents advisory language from becoming an executable instruction by implication. | C23 | Future output-schema policy and content contract tests. | “Auto-switch provider X now” is emitted as an optimization insight. | DOCUMENTATION_ONLY — activate with optimization-suggestion generation. |

## 4. Human Governance

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-HG-001 | Every `OptimizationInsight` requires human review before any corresponding strategy, configuration, or execution change; C23 output has no automatic effect on any entity outside C23. | Maintains human accountability for adopting analytical advice. | Human operator; C23 records review only. | Future review workflow guard and no-auto-apply contract test. | A metric automatically changes a search strategy configuration. | DOCUMENTATION_ONLY — activate with any insight-review workflow. |
| C23-INV-HG-002 | Future automation that applies a C23 insight requires a dedicated C23 Charter Amendment, new ADR, invariant updates, and independent governance review. Zero automation is the default. | Prevents gradual automation creep from bypassing governance. | Charter governance | Charter amendment gate and future architecture review. | A later work package enables automatic template changes without amendment. | DOCUMENTATION_ONLY — activate only by the required amendment process. |

## 5. Layer Separation

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-SEP-001 | C23 may consume `ResearchEvidence`, `AIQualificationInsight`, `HumanFeedback`, and `IntelligenceAggregate` only as read-only analytical input and must not create, modify, or delete C21 records. | C21 remains the intelligence-governance owner. | C21 owns records; C23 consumes. | Future read-only service contracts and mutation-absence tests. | C23 updates an `AIQualificationInsight` confidence field. | DOCUMENTATION_ONLY — activate with C21 analytical consumption. |
| C23-INV-SEP-002 | C23 may consume `ExecutionLedger`, `ProspectRun`, `ActionGate` decisions, and `ReplyDetection` results only as read-only analytical input and must not create, modify, or delete C22 records. | C22 remains the execution-governance owner. | C22 owns records; C23 consumes. | Future read-only service contracts and mutation-absence tests. | C23 changes a `ProspectRun` state based on a metric. | DOCUMENTATION_ONLY — activate with C22 analytical consumption. |
| C23-INV-SEP-003 | C23 must not create a parallel intelligence store, execution ledger, or qualification authority; `OptimizationInsight` is structurally distinct from `ResearchEvidence` and `AIQualificationInsight`. | Avoids duplicate evidence lifecycles and competing authority. | C21 for intelligence; C22 for execution evidence; C23 for aggregate learning. | Future schema boundary tests and ownership review. | C23 stores per-prospect research conclusions as optimization records. | DOCUMENTATION_ONLY — activate with C23 entity definitions. |
| C23-INV-SEP-004 | `OptimizationInsight` provides aggregate operational strategy recommendations and must not replace `AIQualificationInsight`. It must not represent per-prospect qualification intelligence, ranking authority, intelligence interpretation, or individual recommendations. | Establishes the hard C21/C23 intelligence boundary by granularity, purpose, confidence meaning, and consumer. | C21 owns `AIQualificationInsight`; C23 owns aggregate `OptimizationInsight`. | Future aggregate-scope validation and separation contract test. | C23 records “Prospect X is qualified” or ranks individual prospects. | DOCUMENTATION_ONLY — activate with `OptimizationInsight` design approval. |
| C23-INV-SEP-005 | C23 output, including `PerformanceMetric` values and `OptimizationInsight` recommendations, must not be presented in the C22 ActionGate interface or used as approval/denial evidence. | Strategic review must not influence the operational authorization gate. | C22 owns ActionGate; C23 is excluded. | Future UI exclusion test and ActionGate evidence contract. | An approval screen displays a C23 success-rate recommendation. | DOCUMENTATION_ONLY — activate with any C23 presentation surface. |

## 6. Metric Integrity

| ID | Statement | Rationale | Owner Layer | Enforcement Mechanism | Violation Example | Activation Status |
| --- | --- | --- | --- | --- | --- | --- |
| C23-INV-MET-001 | Every `PerformanceMetric` must declare `sampleSize`. A metric below the category threshold in C23-INV-MET-004 must be `LOW_CONFIDENCE` and include a confidence interval; a metric without sample size is invalid. | Prevents misleadingly confident measurements. | C23 | Future metric validator and confidence contract test. | A rate with no sample size is shown as reliable. | DOCUMENTATION_ONLY — activate with metric computation. |
| C23-INV-MET-002 | `PerformanceMetric` values must not be automated triggers for execution, approval, or configuration changes, including C22 `AutomationRule` conditions. | Metrics inform human judgment; they do not drive operations. | C23 output; C22 protects execution. | Future automation-reference absence tests and rule validator. | “Reply rate < 5%” automatically pauses a run. | DOCUMENTATION_ONLY — activate before metrics are exposed to automation-capable surfaces. |
| C23-INV-MET-003 | Metric methodology must be documented and reproducible: the same declared inputs must produce the same metric value; non-deterministic computation is forbidden. | Allows reviewers to verify and compare operational learning claims. | C23 | Future computation specification, test fixtures, and reproducibility contract. | The same source period produces different values without changed inputs. | DOCUMENTATION_ONLY — activate with metric engine design. |
| C23-INV-MET-004 | Sample-size governance is stratified: descriptive metrics require n >= 5; comparative optimization metrics require n >= 30 per group; trend metrics require at least 3 periods with n >= 10 each. Below threshold requires `LOW_CONFIDENCE` and a confidence interval; below-threshold comparisons must state insufficient data. | A single flat threshold is inadequate for comparisons and trends. | C23 | Future metric classifier, validator, and display contract test. | Template A versus B is reported as reliable with n=8 per group. | DOCUMENTATION_ONLY — activate with metric computation and reporting. |

## Summary

| Category | Count |
| --- | ---: |
| Ownership Boundary | 4 |
| Provenance Governance | 4 |
| Advisory Only | 3 |
| Human Governance | 2 |
| Layer Separation | 5 |
| Metric Integrity | 4 |
| **Total** | **22** |

## Registry Rules

- Every invariant ID in this registry appears exactly once.
- Every invariant remains `DOCUMENTATION_ONLY` until its stated activation
  condition is met and independently reviewed.
- This registry does not create `OptimizationInsight` or `PerformanceMetric`,
  and does not authorize C23 implementation.

## References

- `docs/PHASE3C23_CHARTER.md`
- `docs/audit/PHASE3C23_CHARTER_RATIFICATION_REVIEW.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/adr/C22_INVARIANT_REGISTRY.md`
