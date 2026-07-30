# ADR-C24-002: ReplySignal Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation |
| Baseline | `9814c57` |
| Depends On | `docs/PHASE3C24_CHARTER.md`; C22 ReplyDetection ownership |
| Related Invariant | `C24-INV-ADV-001` |
| Implementation Authorization | None |

## Context

C22 owns ReplyDetection as an execution-governance concern. C24 may need a
commercial interpretation of governed reply evidence, but that interpretation
cannot replace technical detection or gain execution or CRM authority.

## Decision

`ReplySignal` is a future C24 interpretation artifact and advisory input. It
may express a human-reviewable business interpretation of C22 ReplyDetection
evidence with source provenance. It does not replace C22 technical detection.

## Boundary

| Allowed ReplySignal Role | Forbidden ReplySignal Role |
| --- | --- |
| Advisory business interpretation | Execution command |
| Human-review input for OpportunityCandidate consideration | Opportunity-creation command |
| Provenance-bearing commercial evidence | Sales-stage mutation |
| Aggregate revenue-analysis input | Workflow trigger, auto-response, or outreach trigger |

## Governance Rules

1. Every future ReplySignal must preserve a source reference to governed reply
   evidence and declare its interpretation basis.
2. A ReplySignal can inform human review but cannot itself create or advance an
   OpportunityCandidate state.
3. A changed interpretation requires a new, explicitly superseding signal;
   the prior interpretation remains historically traceable.
4. C24 cannot detect replies in place of C22 or write to C22 execution records.

## Consequences

Future contracts must treat ReplySignal as advisory evidence only. No service,
worker, route, provider integration, automated follow-up, CRM mutation, or
workflow behavior is authorized by this ADR.
