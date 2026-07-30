# ADR-C24-003: PipelineMetric Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation |
| Baseline | `9814c57` |
| Depends On | `docs/PHASE3C24_CHARTER.md`; C23 metric-separation boundary |
| Related Invariants | `C24-INV-SEP-001`, `C24-INV-MET-001` |
| Implementation Authorization | None |

## Context

C24 requires a governed vocabulary for commercial pipeline and revenue
measurement. It must not redefine C23 acquisition-effectiveness metrics or turn
analytical measurement into automated commercial authority.

## Decision

`PipelineMetric` is a future C24 measurement artifact only. It reports
commercial pipeline or revenue-outcome health and remains distinct from C23
`PerformanceMetric`, which measures prospecting effectiveness.

## Required Measurement Properties

Every future PipelineMetric must declare:

- source references and provenance;
- documented, reproducible computation methodology;
- reporting period;
- sample size; and
- freshness status.

An undeclared or non-reproducible metric is not valid governed measurement.

## Authority Boundary

| PipelineMetric May | PipelineMetric Must Not |
| --- | --- |
| Measure pipeline health, conversion, velocity, coverage, or reported revenue outcome | Redefine or overwrite a C23 optimization metric |
| Inform a human commercial review | Control opportunity acceptance |
| Supply aggregate evidence to RevenueInsight | Control forecast acceptance or commitment |
| Display freshness and method limitations | Control or mutate sales stage |

No single AI score, PipelineMetric, RevenueInsight, or aggregate signal may
control an opportunity, forecast, sales-stage, or revenue decision. Metrics are
not workflow, execution, approval, or CRM lifecycle triggers.

## Consequences

Future metric designs must preserve provenance, reproducibility, and separation
from C23. This ADR creates no metric entity, calculation, data query, reporting
surface, test, automation, or CRM integration.
