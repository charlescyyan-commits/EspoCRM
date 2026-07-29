# ADR-C23-004: Optimization Suggestion Boundary

| Field | Value |
| --- | --- |
| **Status** | Draft — Governance Prepared in Phase 1; implementation remains future work |
| **Date** | 2026-07-30 |
| **Decision Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Depends On** | ADR-C23-001; ADR-C23-003 |
| **Implementation Authorization** | None |

## 1. Context

Future C23 `OptimizationInsight` records are intended to express aggregate
operational learning for human review. The record cannot be allowed to become a
command object, an approval artifact, a workflow input, or a policy mechanism
by virtue of its lifecycle status.

This ADR defines the lifecycle vocabulary and the hard boundary between human
review of a suggestion and any separate operational action.

## 2. Problem Statement

Terms such as “accepted” can be mistaken for authorization. If acceptance
automatically changes a provider, alters CRM data, triggers a workflow, or
approves an ActionGate request, C23 advisory learning acquires execution
authority through status semantics rather than an explicit API.

The lifecycle must therefore describe only the governance state of a
recommendation, never the state of an operational action.

## 3. Decision

The conceptual lifecycle is:

```text
Generated -> Reviewed -> Accepted
                    \-> Rejected
```

`Generated` means an aggregate advisory suggestion exists.
`Reviewed` means an authorized human has examined it.
`Accepted` means a human accepts the suggestion for strategic consideration.
`Rejected` means a human declines it. A future immutable/supersession model may
record a materially revised suggestion as a new record, but no lifecycle state
authorizes an operational side effect.

## 4. Lifecycle Semantics

| State | Meaning | Does Not Mean |
| --- | --- | --- |
| Generated | C23 produced an advisory suggestion with evidence. | An action is queued, approved, or executed. |
| Reviewed | A human examined evidence, scope, freshness, and limitations. | A policy or workflow has changed. |
| Accepted | A human accepts the recommendation for consideration. | Execute, approve, modify CRM, or change provider. |
| Rejected | A human declines the recommendation. | Source evidence is deleted or rewritten. |

## 5. Advisory Boundary

An OptimizationInsight may state observations, patterns, correlations, and
human-reviewable suggestions. It must not contain or imply instructions to
approve, send, execute, create, switch, route, schedule, reallocate, or mutate.

An accepted suggestion remains an advisory record. If a human later changes a
strategy or configuration, that change occurs through a separately authorized
surface owned by the relevant layer. The change must not be modeled as an
automatic consequence of the insight lifecycle.

## 6. Prohibited Downstream Paths

```text
OptimizationInsight -> ActionGate
OptimizationInsight -> AutomationRule
OptimizationInsight -> workflow mutation
OptimizationInsight -> provider change
OptimizationInsight -> CRM lifecycle mutation
OptimizationInsight -> execution trigger
```

In particular, C23 output may not appear in C22 ActionGate review, may not be
used as approval/denial evidence, and may not act as a condition for a future
automation rule.

## 7. Human Governance

| Decision | Owner | Required Constraint |
| --- | --- | --- |
| Review an insight | Authorized human operator | Reviews aggregate evidence, freshness, and confidence. |
| Accept or reject an insight | Authorized human operator | Changes only the advisory review state. |
| Change a strategy or process | Authorized human operator in the owning layer | Must use a separate governed path. |
| Approve execution | C22 ActionGate human decision | C23 insight is excluded from the gate. |
| Execute provider or outreach work | Connector/C22 governed execution path | No C23 lifecycle state can initiate it. |

## 8. Consequences

### Positive

- Lifecycle names cannot be used to smuggle execution authority into C23.
- Human review produces an auditable distinction between learning and action.
- C22 ActionGate remains the sole authorization boundary for executable work.

### Constraints

- “Accepted” deliberately has no automatic downstream effect.
- Future UX must avoid buttons, routes, or hidden handlers that apply an insight
  to configuration, execution, or CRM records.
- Any automation proposal requires Charter amendment and independent review.

## 9. Related Invariants

| Invariant | Application |
| --- | --- |
| C23-INV-OWN-003 | Future insights are immutable and revised by supersession. |
| C23-INV-ADV-001 / ADV-003 | Insight content is advisory and non-directive. |
| C23-INV-HG-001 / HG-002 | Human review is required and auto-application is prohibited. |
| C23-INV-SEP-005 | Insight data is excluded from ActionGate. |
| C23-INV-MET-002 | Neither metrics nor insights can become automation conditions. |

## Decision Status

**Draft.** This document defines a future conceptual lifecycle only. It creates
no `OptimizationInsight` entity, status field, API, workflow, AutomationRule,
provider action, or CRM mutation path.
