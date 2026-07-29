# C21 Invariant Registry

## Status

**Documentation only — Proposed.**

This registry records the invariants intended for Phase3C21 AI Sales
Intelligence governance. It creates no code, entities, metadata, migrations,
tests, runtime behaviour, or implementation authorization.

## Relationship to C20

Some C21 invariants have historical antecedents in C20, especially
`C20-INV-16` through `C20-INV-22`. Those rows remain unchanged in
`docs/adr/C20_INVARIANT_REGISTRY.md`. This registry references their intent as
historical context only; it neither moves, renumbers, deletes, nor changes C20
invariants.

C21 operationalizes intelligence interpretation and references C20 execution
provenance. It does not amend C20 execution governance.

## Status Rules

- `DOCUMENTATION_ONLY` means the invariant is specified but has no C21 code or
  test evidence yet.
- An accepted C21 Charter must define an owning work package, activation
  trigger, implementation evidence, and contract-test path before an
  invariant can become active.
- No status in this document changes any C20 invariant status.

## Proposed Invariants

| ID | Invariant | Status | Historical C20 context | Required future evidence |
| --- | --- | --- | --- | --- |
| C21-INV-01 | C21 does not own final sales or qualification decisions. | DOCUMENTATION_ONLY | C20-INV-16, C20-INV-21 | No decision authority in entities, services, filters, or workflows. |
| C21-INV-02 | `AI_INFERENCE` is never stored, displayed, or promoted as `FACT`. | DOCUMENTATION_ONLY | C20 advisory-separation intent | Evidence-type metadata, append-only correction rules, and contract tests. |
| C21-INV-03 | `AIQualificationInsight` is recommendation, not decision; it has no score or qualification authority. | DOCUMENTATION_ONLY | C20-INV-16, C20-INV-21 | Forbidden score/verdict field and behaviour tests. |
| C21-INV-04 | C21 cannot write CRM lifecycle or revenue-decision fields. | DOCUMENTATION_ONLY | C20-INV-17, C20-INV-18, C20-INV-22 | Cross-module writer and transition-owner boundary tests. |
| C21-INV-05 | AI-produced intelligence has required C20 execution provenance. | DOCUMENTATION_ONLY | C20 execution-evidence contract | Required `sourceAIRequestLogId` provenance validation and referential tests. |
| C21-INV-06 | C21 does not create provider credentials, routing, adapters, or execution runtime. | DOCUMENTATION_ONLY | C20 provider and egress boundary | Module source and metadata absence tests. |
| C21-INV-07 | C21 creates no scoring authority and does not mutate `canonical_score`. | DOCUMENTATION_ONLY | C20-INV-14, C20-INV-19 | No-score/no-writer contract tests. |
| C21-INV-08 | `HumanFeedback` is append-only and cannot overwrite historical insight. | DOCUMENTATION_ONLY | C20-INV-07 append-only pattern | Service, guard, ACL, and correction-history tests. |

## Implementation Gate

These invariants remain documentation only until all of the following occur:

1. ADR-C21 is independently reviewed and accepted.
2. A C21 Charter defines the permitted implementation increment.
3. The identity decision remains frozen: `ProspectPool` is the sole pre-CRM
   candidate identity; no `ProspectCandidate` entity is introduced.
4. Each activated invariant gains its designated test evidence without changing
   C20 ownership, Registry history, provider governance, or Chitu authority.
