# ADR-C23-001: Optimization Ownership Boundary

| Field | Value |
| --- | --- |
| **Status** | Draft — Phase 1 Governance |
| **Date** | 2026-07-30 |
| **Decision Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Related Charter** | `docs/PHASE3C23_CHARTER.md` §§2–3, 6, 10–11 |
| **Related Registry** | `docs/adr/C23_INVARIANT_REGISTRY.md` |
| **Implementation Authorization** | None |

## 1. Context

C23 is the AI Prospecting Optimization & Learning Governance Layer. It consumes
aggregate operational evidence from C20, C21, and C22 to produce human-reviewable
strategy suggestions. C21 remains the AI Intelligence Governance Layer and owns
the prospect-level intelligence record `AIQualificationInsight`.

Without an explicit ownership decision, a future C23 optimization record could
drift into per-prospect interpretation, duplicate C21 intelligence, or become an
input to C22 authorization. This ADR establishes the boundary before any C23
entity, service, metric engine, or UI exists.

## 2. Problem Statement

Both `AIQualificationInsight` and the proposed `OptimizationInsight` may use
analytical evidence and confidence language. That superficial similarity creates
three governance risks:

1. C23 could score, rank, or qualify individual prospects and thereby compete
   with C21.
2. C23 could retain per-prospect evidence references and form a shadow
   intelligence store.
3. C23 performance learning could be displayed at, or cited as evidence for,
   C22 `ActionGate` decisions.

The system needs a durable distinction between prospect intelligence and
aggregate strategy learning while preserving the advisory-only nature of both
layers.

## 3. Decision

C23 owns future `OptimizationInsight` records solely as **aggregate operational
strategy recommendations**. An OptimizationInsight may describe a cohort,
strategy, time-window, template, provider, or other aggregate operational
pattern, but it must not interpret, rank, score, qualify, or recommend action
for an individual prospect.

C21 continues to own `AIQualificationInsight` as **individual prospect
qualification intelligence**. C23 may read C21 records only as governed,
read-only analytical input and may not replace, rewrite, or re-publish them.

C23 output is advisory for human strategic review. It has no execution,
approval, configuration-mutation, CRM-lifecycle, or ActionGate influence
authority.

## 4. Ownership Matrix

| Record | Owner | Purpose | Scope | C23 Access | Explicit Non-Authority |
| --- | --- | --- | --- | --- | --- |
| `AIQualificationInsight` | C21 | Prospect qualification intelligence | Individual prospect interpretation | Read-only analytical input only | C23 cannot create, modify, supersede, rank, or replace it |
| `OptimizationInsight` | C23 | Operational optimization learning | Aggregate strategy improvement | C23-only future ownership | Cannot score or qualify prospects, execute, approve, or affect ActionGate |
| `PerformanceMetric` | C23 | Point-in-time aggregate operational measurement | Cohort, period, strategy, or provider measurement | C23-only future ownership | Cannot trigger execution, approval, or configuration changes |
| `ActionGate` | C22 | Human execution authorization | Individual governed action | No C23 presentation or decision input | C23 cannot influence approval or denial |

## 5. C21/C23 Boundary

The boundary is based on purpose and granularity, not merely on record names.

| Dimension | C21 `AIQualificationInsight` | C23 `OptimizationInsight` |
| --- | --- | --- |
| Owner | C21 Intelligence Governance | C23 Optimization Learning Governance |
| Purpose | Qualification intelligence | Aggregate strategy improvement |
| Unit of analysis | Individual prospect | Aggregate operational cohort or time window |
| Consumer | Human intelligence review and C21-governed context | Human strategic review |
| Confidence meaning | Confidence in prospect-level intelligence interpretation | Confidence in an aggregate operational pattern |
| Permitted evidence | C21-governed intelligence evidence | Aggregate operational evidence only |

`OptimizationInsight` must not replace `AIQualificationInsight`. It must not
become a second qualification lifecycle through differently named fields,
historical accumulation, or consumer behavior.

## 6. Data Flow

```text
C20 AIJob / AIRequestLog          ┐
C21 read-only intelligence        ├─> C23 aggregate analysis
C22 read-only execution evidence  │        │
                                  │        v
                                  └─> OptimizationInsight (advisory)
                                             │
                                             v
                                      Human strategic review

Forbidden: C23 output -> ActionGate decision / execution / CRM mutation
```

`OptimizationInsight.evidenceReference` may use aggregate operational sources,
including `PerformanceMetric`, `ProspectRun`, `ExecutionLedger`,
`IntelligenceAggregate`, `AIJob`, and `AIRequestLog`, subject to future
validation. It must not reference `ProspectCandidate`, `ProspectPool`, `Lead`,
`Account`, `Opportunity`, `ResearchEvidence`, or `AIQualificationInsight`.

## 7. Forbidden Overlap

C23 must not:

- score, rank, qualify, or interpret an individual prospect;
- replace, update, supersede, or create `AIQualificationInsight`;
- store individual prospect or CRM identity references as OptimizationInsight
  evidence;
- create a parallel intelligence store or execution ledger;
- display C23 data in C22 `ActionGate` review or use it as approval/denial
  evidence;
- influence ActionGate decisions, initiate execution, or mutate C20/C21/C22 or
  CRM Core records.

## 8. Consequences

### Positive

- C21 retains a single, unambiguous owner for prospect qualification
  intelligence.
- C23 can learn from historical operational outcomes without acquiring
  operational authority.
- C22 ActionGate remains a human authorization boundary insulated from
  optimization pressure.
- Aggregate evidence and freshness requirements make future suggestions
  auditable, including their sourcePeriod, generatedAt, and freshnessStatus.

### Constraints

- C23 cannot use its own records as a workaround for missing C21 intelligence.
- A useful C23 recommendation may still require a human to independently decide
  whether and how to change strategy.
- Any future C23 entity design must encode aggregate-only references and
  advisory-only fields before implementation proceeds.

## 9. Invariants

This ADR owns or constrains the following registry entries:

| Invariant | Role in this decision |
| --- | --- |
| C23-INV-OWN-001 through OWN-004 | C23-only ownership and immutability of future C23 records |
| C23-INV-PROV-001 through PROV-004 | Traceable, aggregate-only, fresh evidence |
| C23-INV-SEP-001 through SEP-003 | Read-only C21/C22 consumption and no parallel authority |
| C23-INV-SEP-004 | Hard C21/C23 intelligence separation; OptimizationInsight does not replace AIQualificationInsight |
| C23-INV-SEP-005 | ActionGate isolation from all C23 output |
| C23-INV-ADV-001 and ADV-003 | Advisory-only output boundary |
| C23-INV-HG-001 | Human review before any corresponding change |

## 10. Future Evolution Rules

1. No C23 entity, service, scope, metadata, client view, or API is authorized
   by this ADR alone.
2. ADR-C23-002 must define read-only execution-analytics data ownership before
   `PerformanceMetric` design or implementation.
3. ADR-C23-003 and ADR-C23-004 must define feedback learning and the permitted
   language of optimization suggestions before insight generation.
4. ADR-C23-005 must define reproducible metrics, confidence, sample governance,
   and freshness enforcement before metric computation.
5. Any proposal to let C23 influence ActionGate, execution, configuration, or
   CRM lifecycle requires a ratified C23 Charter Amendment, new invariants, and
   independent governance review.

## Decision Status

**Draft.** This ADR establishes documentation-only governance. It does not
create `OptimizationInsight`, `PerformanceMetric`, or any runtime capability.
