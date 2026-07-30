# ADR-C24-001: Opportunity Ownership Boundary

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation |
| Baseline | `9814c57` |
| Depends On | `docs/PHASE3C24_CHARTER.md`; C24 Charter Ratification Review |
| Related Invariants | `C24-INV-SEP-002`, `C24-INV-LIFE-001`, `C24-INV-HG-001` |
| Implementation Authorization | None |

## Context

C24 needs a governance record for human consideration of commercial signals
without duplicating or taking control of CRM Core's canonical Opportunity
lifecycle. A candidate-commercial interpretation must not become an automatic
Opportunity, stage movement, or commercial commitment.

## Decision

`OpportunityCandidate` is a future C24 governance record only. CRM Core remains
the sole owner of canonical Opportunity lifecycle, sales stage, commercial
record, forecast commitment, and CRM lifecycle mutation. C24 owns candidate
qualification workflow governance and advisory revenue insight, not the CRM
Opportunity itself.

## Ownership Boundary

| Concern | Owner | C24 Role | Prohibited C24 Role |
| --- | --- | --- | --- |
| Opportunity lifecycle | CRM Core | Human-facing context only | Create, alter, close, reopen, or own the canonical Opportunity |
| Sales stage | CRM Core | Observe commercial reporting context | Automatic or direct stage mutation |
| Commercial record | CRM Core | Candidate governance before a separate human CRM action | Parallel commercial identity or authoritative revenue record |
| OpportunityCandidate | C24 | Human-governed candidate workflow and audit trail | Automatic promotion into a CRM Opportunity |
| RevenueInsight | C24 | Aggregate advisory commercial analysis | Forecast, lifecycle, or sales decision authority |

## OpportunityCandidate Governance

The Charter-defined lifecycle is the only future candidate workflow:

```text
IDENTIFIED -> REVIEW_PENDING -> ACCEPTED -> ACTIVE -> WON
                                          -> LOST
                    -> REJECTED
```

`REJECTED`, `WON`, and `LOST` are terminal. Each transition after
`IDENTIFIED` requires an authenticated authorized human, reason where
applicable, provenance, and an immutable transition record. A terminal record
is not reopened; reconsideration creates a new candidate with provenance.

`ACCEPTED` means a human accepts the candidate for commercial consideration. It
does not create a CRM Opportunity, approve a stage change, authorize execution,
or commit a forecast.

## Explicit Prohibitions

- No `AutoOpportunityAgent` or equivalent autonomous promotion authority.
- No automatic Opportunity creation.
- No automatic or direct sales-stage mutation.
- No candidate transition as a substitute for ActionGate or C22 execution.
- No AI-created `ACCEPTED`, `ACTIVE`, `WON`, `LOST`, or `REJECTED` state.

## Consequences

Future C24 work must preserve a separate C24 candidate record and require an
explicit, human-performed CRM Core action for any later Opportunity creation or
stage change. This ADR authorizes no entity, schema, service, API, UI, ACL, or
integration implementation.
