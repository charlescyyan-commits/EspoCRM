# ADR-C23-003: Feedback Learning Governance

| Field | Value |
| --- | --- |
| **Status** | Draft — Governance Prepared in Phase 1; implementation remains future work |
| **Date** | 2026-07-30 |
| **Decision Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **Depends On** | ADR-C23-001; ADR-C23-002 |
| **Implementation Authorization** | None |

## 1. Context

C21 `HumanFeedback` records human corrections and observations. C22 execution
outcomes (`ExecutionOutcome` as a conceptual aggregate context, not a C23
entity) record governed operational results. C23 may learn from their aggregate
relationship to suggest improvements, but feedback must not be reinterpreted as
an autonomous command or an alternative authorization path.

This ADR defines the human-mediated learning loop before any feedback analysis,
correlation engine, OptimizationInsight generator, or policy application exists.

## 2. Problem Statement

Feedback is often operationally persuasive: a repeated correction can reveal a
useful strategy pattern. If feedback directly changes a policy, approves an
action, or triggers execution, the system silently transfers human authority to
an analytical pipeline. It could also allow C23 to overwrite C21 intelligence
or C22 authorization decisions.

The design must separate pattern discovery from action and keep both source
records and resulting operator decisions under their existing owners.

## 3. Decision

The allowed learning path is:

```text
C21 HumanFeedback + C22 execution outcomes + aggregate metrics
                         │
                         v
                 C23 aggregation and pattern discovery
                         │
                         v
                  advisory optimization suggestion
                         │
                         v
                 human strategic review and decision
```

AI or C23 analysis may aggregate evidence, discover patterns, and generate
advisory suggestions. Humans alone decide whether to accept an insight, change
a strategy, or change a process. A review outcome is not an execution command.

## 4. Human and AI Responsibilities

| Responsibility | Owner | Boundary |
| --- | --- | --- |
| Record feedback | C21 / human feedback process | C23 reads it only. |
| Aggregate feedback and outcomes | C23 analytical process | Aggregate, traceable, and advisory only. |
| Discover correlations or patterns | C23 analytical process | Must not create prospect qualification authority. |
| Generate a suggestion | C23 analytical process | Suggestion cannot direct execution, approval, or mutation. |
| Accept, adapt, or reject an insight | Human operator | Requires review; no automatic acceptance. |
| Change strategy or process | Authorized human operator | Separate governed action outside C23 output authority. |
| Approve an executable action | C22 ActionGate human decision | Never delegated to C23 feedback learning. |

## 5. Allowed Learning Inputs and Outputs

### Allowed inputs

- C21 `HumanFeedback` as read-only input;
- read-only C22 execution outcomes, including aggregate reply and completion
  patterns; and
- aggregate C23 metrics with declared scope, period, sample size, and method.

### Allowed outputs

- observations about aggregate feedback-to-outcome patterns;
- correlations with stated evidence and confidence limitations; and
- human-reviewable suggestions for future strategy or process consideration.

## 6. Forbidden Feedback Paths

The following paths are prohibited:

```text
Feedback -> automatic policy change
Feedback -> ActionGate approval or denial
Feedback -> execution trigger, retry, send, or dispatch
Feedback -> C21 intelligence mutation or replacement
```

C23 must not convert a feedback pattern into an `AutomationRule`, a workflow
mutation, a provider change, a CRM update, or a C22 state transition.

## 7. Governance Rules

1. Feedback provenance must remain traceable to the source C21 and C22 records
   without transferring ownership to C23.
2. Learning must be aggregate; individual prospect feedback cannot become an
   individual C23 qualification conclusion.
3. A suggestion must communicate uncertainty and sample limitations where
   applicable.
4. Human review must be explicit. “Accepted” means a human accepted the
   analytical observation for consideration; it does not apply a policy.
5. Any later strategy or process change must use its own authorized operational
   path and remain subject to C20/C21/C22/CRM boundaries.

## 8. Consequences

### Positive

- Human feedback can inform organizational learning without losing human
  accountability.
- C23 can identify repeatable improvement opportunities while C21 and C22
  retain source-record authority.
- The architecture avoids a closed feedback-to-execution loop.

### Constraints

- C23 cannot provide instant or automatic adaptation from feedback.
- Future feedback analytics must support aggregate provenance and human review.
- A human-approved strategy change does not relax ActionGate or provider
  governance for later executable actions.

## 9. Related Invariants

| Invariant | Application |
| --- | --- |
| C23-INV-SEP-001 | HumanFeedback and other C21 records remain read-only to C23. |
| C23-INV-SEP-002 | Execution outcomes remain read-only to C23. |
| C23-INV-SEP-004 | Feedback learning cannot become individual prospect qualification. |
| C23-INV-ADV-001 / ADV-003 | Learning output remains advisory and non-directive. |
| C23-INV-HG-001 / HG-002 | Human review is required; automation is structurally off by default. |
| C23-INV-MET-002 | Aggregate metrics cannot trigger operational change. |

## Decision Status

**Draft.** This ADR defines governance for a future learning capability. It
creates no insight entity, feedback processor, policy engine, ActionGate path,
or execution trigger.
