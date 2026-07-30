# ADR-C24-005: Forecast Human Governance

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation |
| Baseline | `9814c57` |
| Depends On | `docs/PHASE3C24_CHARTER.md`; CRM Core lifecycle ownership |
| Related Invariants | `C24-INV-HG-001`, `C24-INV-ADV-001` |
| Implementation Authorization | None |

## Context

Commercial forecasts and pipeline commitments carry human accountability and
remain within CRM Core's commercial lifecycle. C24 can provide governed analysis
but cannot make, commit, or operationalize a commercial decision.

## Decision

Humans exclusively own forecast acceptance, commercial decisions, and pipeline
commitments. C24 analytical assistance may summarize, analyze, and explain
commercial evidence, but it cannot commit a forecast or change an Opportunity
status, sales stage, or other CRM lifecycle state.

## Responsibility Boundary

| Actor | Permitted Responsibility | Prohibited Responsibility |
| --- | --- | --- |
| Human commercial operator | Accept or reject a forecast, decide pipeline actions, make commitments, perform CRM actions | Delegate accountable commercial decision to C24 output |
| C24 advisory artifact | Summarize, analyze, explain, and present provenance/freshness | Commit forecast, alter CRM state, execute workflow, create commercial commitment |
| CRM Core | Store canonical Opportunity, sales stage, forecast commitment, and lifecycle action | Delegate canonical ownership to C24 |

## Governance Rules

1. A forecast decision must be an explicit human decision outside an automated
   C24 path.
2. Commercial commitments require an accountable human actor and applicable
   evidence or rationale.
3. Advisory evidence may inform a decision but cannot be encoded as an automatic
   acceptance, stage movement, close, or forecast commit instruction.
4. Any future proposal to automate a commercial decision requires a Charter
   amendment, dedicated ADR, invariant update, and independent governance
   review before implementation consideration.

## Consequences

This ADR preserves zero automation as the default for forecast and commercial
decisions. It authorizes no forecast entity, service, integration, worker,
queue, scheduler, client control, or CRM mutation.
