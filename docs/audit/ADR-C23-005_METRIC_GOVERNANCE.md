# ADR-C23-005: Metric Governance

| Field | Value |
| --- | --- |
| **Status** | Draft — Phase 1 Governance |
| **Date** | 2026-07-30 |
| **Decision Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Depends On** | ADR-C23-002 Execution Analytics Data Ownership |
| **Implementation Authorization** | None |

## 1. Context

C23 needs future aggregate operational measurements to describe performance
patterns across declared cohorts and periods. The proposed `PerformanceMetric`
is an analytical reporting artifact derived from governed C20/C21/C22 evidence.
It is not a real-time control system, policy engine, execution trigger, or
authority over a source layer.

This ADR defines reliability, provenance, confidence, and freshness governance
before any metric entity or computation exists.

## 2. Problem Statement

Metrics can appear objective even when their sample, method, period, or source
is inadequate. They can also become de facto operational controls when a value
is used to approve actions, pause runs, select a provider, or change a strategy automatically.

The system requires a reproducible measurement contract and an explicit ban on
metric-driven automation.

## 3. Decision

A future `PerformanceMetric` is a point-in-time **analytical measurement** and
**reporting artifact** owned by C23. It must declare its scope, measurement
period, sample size, source references, methodology, value, unit, confidence
information, and computation time.

It is not a control signal, policy trigger, execution authority, approval input,
or configuration command. Any human response to a metric must occur through a
separate authorized process in the owning layer.

## 4. Ownership and Reliability Matrix

| Aspect | Governance Rule | Owner |
| --- | --- | --- |
| Source execution/intelligence records | Remain owned and immutable/read-only under C20, C21, or C22 rules. | Source layer |
| Metric record | Future C23-owned, immutable point-in-time measurement. | C23 |
| Methodology | Declared, documented, and reproducible from the same inputs. | C23 |
| Confidence | Derived from declared metric category, sample size, and interval. | C23 |
| Operational action | Cannot be caused by the metric itself. | Authorized human and owning operational layer |

## 5. Sample and Confidence Requirements

| Metric Category | Minimum Sample Requirement | Required Presentation |
| --- | --- | --- |
| Descriptive | n >= 5 | Below threshold: `LOW_CONFIDENCE` and confidence interval. |
| Comparative optimization | n >= 30 per group | Below threshold: `LOW_CONFIDENCE`, confidence interval, and “insufficient data for reliable comparison.” |
| Trend | At least 3 time periods, each with n >= 10 | Below threshold: `LOW_CONFIDENCE` and confidence interval. |

Every metric must declare `sampleSize`. Missing sample size invalidates the
metric. Confidence intervals and limitations are part of the reporting
contract, not optional embellishments.

## 6. Freshness Governance

Future reporting must classify metric and insight freshness using these states:

| Status | Meaning | Display Requirement |
| --- | --- | --- |
| `CURRENT` | Source and computation are within the defined current window. | May be displayed as current with provenance. |
| `AGING` | Approaches the staleness boundary. | Display its age and caution. |
| `STALE` | Exceeds the freshness threshold. | Explicit staleness warning; not presented as a current recommendation. |
| `ARCHIVAL` | Retained only for historical reference. | Historical context only; no current-performance claim. |

For OptimizationInsight provenance, the C23 registry requires a `sourcePeriod`
(`sourcePeriodStart` and `sourcePeriodEnd`), `generatedAt`, and
`freshnessStatus`. The Charter thresholds require `STALE` when `generatedAt` is
older than 60 days or `sourcePeriodEnd` is older than 180 days.

## 7. Prohibited Metric Uses

`PerformanceMetric` must not be used as:

- an execution trigger, retry trigger, or dispatch condition;
- an ActionGate approval or denial input;
- a C22 `AutomationRule` condition;
- a provider-selection command or provider runtime control;
- an automatic strategy, template, workflow, or configuration change; or
- a CRM lifecycle or scoring decision.

## 8. Reproducibility and Provenance Rules

1. The same declared inputs and methodology must produce the same metric value.
2. Each metric must retain sufficient source references to support audit without
   transferring ownership of source records to C23.
3. A metric must state the cohort/scope, period, unit, sample size, and method.
4. Aggregate metrics must not be used to reconstruct individual prospect
   qualification or to create a shadow intelligence store.
5. Recalculation creates a new point-in-time measurement; it does not overwrite
   historical reporting evidence.

## 9. Consequences

### Positive

- Operators can assess the reliability and recency of aggregate learning.
- Historical measurements remain reproducible and auditable.
- C23 analytical data cannot quietly become an operational control plane.

### Constraints

- Low-sample results cannot be presented as reliable comparisons.
- Freshness states add display and review requirements to future reporting.
- Future metric implementation must include declared methodology and source
  references before it can be activated.

## 10. Related Invariants

| Invariant | Application |
| --- | --- |
| C23-INV-OWN-004 | Metrics are immutable point-in-time records. |
| C23-INV-PROV-002 | Scope, period, sample, source references, and methodology are required. |
| C23-INV-PROV-004 | Source period, generated time, and freshness govern stale insight display. |
| C23-INV-MET-001 | Missing or low sample size requires invalid/LOW_CONFIDENCE treatment. |
| C23-INV-MET-002 | Metrics cannot trigger execution, approval, configuration, or automation. |
| C23-INV-MET-003 | Methodology is reproducible. |
| C23-INV-MET-004 | Descriptive, comparative, and trend sample thresholds are stratified. |

## Decision Status

**Draft.** This ADR authorizes no `PerformanceMetric` entity, metric engine,
dashboard, automation, provider call, or policy change.
