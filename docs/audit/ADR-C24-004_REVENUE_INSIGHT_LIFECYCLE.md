# ADR-C24-004: RevenueInsight Lifecycle

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation |
| Baseline | `9814c57` |
| Depends On | `docs/PHASE3C24_CHARTER.md`; ADR-C24-003 |
| Related Invariants | `C24-INV-ADV-001`, `C24-INV-HG-001`, `C24-INV-MET-001` |
| Implementation Authorization | None |

## Context

C24 may later present aggregate commercial analysis to human revenue operators.
The analysis must remain traceable, fresh, and advisory; accepting an analysis
cannot become authorization to change CRM records or commit a commercial action.

## Decision

`RevenueInsight` is a future aggregate commercial analysis, pipeline
observation, and revenue reporting artifact. Every insight must state
provenance, freshness status, and reporting period.

Its human-review lifecycle is:

```text
GENERATED -> REVIEWED -> ACCEPTED
                     -> REJECTED
```

`ACCEPTED` means a human accepts the analysis as decision-support material. It
does not approve execution, authorize a CRM change, create an Opportunity,
change a sales stage, commit a forecast, or mutate a pipeline.

## Lifecycle Rules

| State | Meaning | Governance Requirement |
| --- | --- | --- |
| GENERATED | Aggregate analysis has been recorded for review | Required provenance, freshness, and reporting period |
| REVIEWED | Authorized human has examined the analysis | Explicit human review record |
| ACCEPTED | Human accepts the analysis as advisory evidence | No operational side effect |
| REJECTED | Human declines the analysis as decision-support material | Reason retained where applicable |

Only `GENERATED -> REVIEWED`, `REVIEWED -> ACCEPTED`, and
`REVIEWED -> REJECTED` are allowed. `ACCEPTED` and `REJECTED` are terminal in
this lifecycle. A corrected conclusion requires a new superseding insight,
leaving the prior artifact auditable.

## Explicit Prohibitions

RevenueInsight must not:

- execute or trigger work;
- approve a CRM change;
- mutate a pipeline, opportunity, stage, or forecast;
- create an OpportunityCandidate; or
- become a sales decision engine.

## Consequences

Any future lifecycle guard must enforce human review and advisory-only
semantics. This ADR authorizes no entity, service, metadata, UI, route, test,
worker, or CRM integration.
