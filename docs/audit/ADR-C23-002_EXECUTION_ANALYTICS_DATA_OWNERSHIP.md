# ADR-C23-002: Execution Analytics Data Ownership

| Field | Value |
| --- | --- |
| **Status** | Draft — Phase 1 Governance |
| **Date** | 2026-07-30 |
| **Decision Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Depends On** | ADR-C23-001 Optimization Ownership Boundary |
| **Implementation Authorization** | None |

## 1. Context

C22 owns the autonomous prospecting execution-governance records:
`ProspectRun`, `ActionGate`, `ExecutionLedger`, and `ReplyDetection`. C23 needs
to learn from historical execution outcomes without becoming a second execution
ledger, an authorization mechanism, or a writer to C22 records.

This ADR defines data ownership before C23 develops any analytics view,
`PerformanceMetric`, service, API, or entity.

## 2. Problem Statement

Execution data is operationally valuable: it can reveal completion patterns,
failure rates, approval patterns, timing, and cohort outcomes. Unbounded access
would create unacceptable paths for C23 to:

- alter execution history or run state;
- use aggregate performance to influence `ActionGate` approval decisions;
- derive an execution decision or trigger from an analytical conclusion; or
- claim C22 operational evidence as C23-owned data.

The system requires a read-only consumption boundary that preserves C22 as the
exclusive execution-governance owner.

## 3. Decision

C23 consumes C22 execution information only as **read-only analytical input**.
It may derive aggregate execution outcomes, aggregate performance data, and
future operational metrics for human strategic review. C23 never owns, mutates,
or controls the source C22 records.

`ProspectRun`, `ActionGate`, `ExecutionLedger`, and `ReplyDetection` remain
C22-owned. An aggregate C23 measurement is a separate analytical description
of a declared population and period; it is not a replacement for a C22 source
record or a new execution decision.

## 4. Ownership Matrix

| Record or Concept | Owner | C23 Permitted Use | C23 Prohibited Use |
| --- | --- | --- | --- |
| `ProspectRun` | C22 | Read terminal and lifecycle outcomes in aggregate. | Start, stop, transition, retry, or mutate a run. |
| `ActionGate` | C22 | Analyze aggregate approval/denial patterns outside the gate. | Create a decision, alter a decision, display C23 output at the gate, or influence approval. |
| `ExecutionLedger` | C22 | Read append-only events to compute aggregate operational evidence. | Modify, annotate, delete, rewrite, or supersede ledger entries. |
| `ReplyDetection` | C22 | Read aggregate outcome classifications for historical analysis. | Trigger follow-up, CRM mutation, or new execution. |
| Future C23 aggregate metric | C23 | Describe declared cohort, period, method, sample, and result. | Serve as a control signal or execution authority. |

## 5. Data Flow

```text
C22-owned records
  ProspectRun + ActionGate + ExecutionLedger + ReplyDetection
                              │
                              │ read-only, bounded analytical consumption
                              v
                     C23 aggregate analysis
                              │
                              v
               human-reviewable operational measurement

Forbidden: C23 analysis -> ActionGate / ProspectRun transition / execution
```

The C23 output must preserve source provenance, measurement period, sample
scope, and the distinction between observed outcome and proposed strategy.

## 6. Read-only Consumption Rules

1. C23 reads only the fields necessary for aggregate analysis.
2. C23 must identify the source period, source references, and aggregation
   method for any derived measurement or insight.
3. C23 may examine ActionGate decisions as historical aggregate patterns, but
   must not surface C23 data in the ActionGate review interface.
4. C23 may not establish foreign-key, service, or workflow semantics that imply
   ownership, mutation, retry, or transition authority over C22 records.
5. Derived C23 records must never be treated as a correction or extension of
   `ExecutionLedger`; C22 retains its append-only audit history.

## 7. Forbidden Operations

C23 must not:

- modify any C22 entity, including `ExecutionLedger`;
- create execution decisions, approvals, denials, retries, or dispatches;
- use performance data to influence `ActionGate`;
- trigger execution, workflow mutation, or CRM lifecycle changes;
- create a parallel execution ledger, execution history, or state machine; or
- use C22 data to bypass the permanent human approval requirement.

## 8. Consequences

### Positive

- C23 can support strategic learning without compromising execution evidence.
- C22 retains the single source of truth for run state, authorization, and
  append-only audit records.
- Operators can distinguish a historical measurement from an execution command.

### Constraints

- C23 cannot “fix” a source execution record; corrections remain C22 concerns.
- Any C23 suggestion requires a human-operated, separately governed path before
  it can affect strategy or configuration.
- C23 dashboards, metrics, and future entities must be designed to remain
  outside `ActionGate` and execution workflow surfaces.

## 9. Related Invariants

| Invariant | Application |
| --- | --- |
| C23-INV-OWN-002 | C23 owns no C22 record. |
| C23-INV-SEP-002 | C22 execution records are read-only analytical input. |
| C23-INV-SEP-005 | C23 data is excluded from ActionGate review and evidence. |
| C23-INV-MET-002 | Metrics cannot become execution, approval, or configuration triggers. |
| C23-INV-PROV-002 | Derived metrics declare scope, period, sample size, references, and methodology. |

## Decision Status

**Draft.** This ADR is a governance boundary only. It creates no C23 entity,
metric, integration, API, client surface, or execution capability.
