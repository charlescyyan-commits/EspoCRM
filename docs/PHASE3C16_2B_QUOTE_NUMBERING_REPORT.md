# Phase3C16.2B Quote Numbering Atomic Sequence Report

## Scope

Phase3C16.2B adds the Quote numbering boundary required by the C16 ADRs.

Implemented:

- Quote-only numbering service.
- `QT-YYYY-NNNN` number generation.
- Year-partitioned sequence storage.
- DRAFT to IN_REVIEW assignment boundary.
- Contract tests for numbering behavior and ownership boundaries.

Not implemented:

- Proforma Invoice numbering.
- PDF generation.
- Approval workflow.
- UI actions.
- Connector, worker, provider, or queue integration.

## Design

`QuoteNumberingService` implements `QuoteNumberingServiceInterface`.

Primary methods:

- `generateQuoteNumber(int|string $year): string`
- `assignQuoteNumber(Entity $quote, int|string|null $year = null): string`

`generateQuoteNumber` owns sequence allocation and returns a formatted Quote number.
`assignQuoteNumber` assigns a number to a Quote entity only when `quoteNumber` is empty.
It does not modify Quote status.

The existing `QuoteTransitionService` remains the workflow boundary. During `DRAFT -> IN_REVIEW`, it invokes `assignQuoteNumber` before status mutation and persistence. If numbering fails, the transition fails before the status is saved.

## Storage Decision

The service uses a CRM-owned `numbering_sequence` table:

- `sequence_key` primary key.
- `current_value` integer counter.
- `updated_at` timestamp.
- InnoDB engine.

Quote sequence keys are year-partitioned:

- `QUOTE-2026`
- `QUOTE-2027`

Generated numbers use:

- `QT-2026-0001`
- `QT-2026-0002`
- `QT-2027-0001`

The atomic increment uses MySQL `LAST_INSERT_ID(current_value + 1)` on the target sequence row. This keeps allocation single-row and avoids duplicate numbers under concurrent requests sharing the same database.

## Transaction and Failure Behavior

The transition boundary is explicit:

1. Validate requested Quote status transition.
2. On `DRAFT -> IN_REVIEW`, allocate and assign a Quote number.
3. Set Quote status.
4. Persist the Quote.

Numbering failure stops the transition before status mutation.

Gap policy follows the ADR: gaps are allowed and numbers are not recycled. If a number is allocated and a later Quote save fails, the consumed sequence value is intentionally not decremented or reused.

## Tests

Added C16.2B numbering tests covering:

- Service existence and interface implementation.
- `QT-YYYY-NNNN` format.
- First number and sequential increment contract.
- Year partitioning.
- Atomic increment storage contract.
- No recycle / no decrement gap policy.
- `DRAFT -> IN_REVIEW` numbering boundary.
- No Proforma Invoice numbering.
- No connector, worker, provider, PDF, or DraftApproval dependency.

Updated existing contract tests so the PHP service inventory and Quote workflow interface contract include `QuoteNumberingService`.

## Validation Result

Validation passed:

- PHP lint: PASS, 92 PHP files.
- C16.2B numbering tests: PASS, 8 tests.
- C16.2 Quote workflow tests: PASS, 16 tests.
- C16 contract tests: PASS, 29 tests.
- Extension tests: PASS, 104 tests, 22 subtests.
- Full extension unittest suite: PASS, 104 tests.
- Connector tests: PASS, 279 tests, 92 subtests.
- Root runtime tests: PASS, 162 tests, 1204 subtests.
- S01 integrity tests: PASS, 12 tests, 348 subtests.
- Package baseline tests: PASS, 5 tests, 646 subtests.
- Deployment validation tests: PASS, 2 tests.
- Artifact rebuild: PASS.
- Artifact check: PASS.
- Unified offline gate: PASS.

Artifact:

- `deployment/prospecting-extension-1.9.7-alpha.zip`
- SHA256: `6FBD7F2423AC78F2A92BF1466D63D9480EE97242FC3D0115E39B0BBB4748E7EC`

## Limitations

- Runtime EspoCRM dependency injection wiring was not exercised in a live CRM rebuild environment.
- The implementation is intentionally Quote-only; Proforma Invoice numbering remains out of scope.
- The sequence table is created lazily by the service and should be reviewed during deployment hardening if a central migration mechanism is introduced later.
- Gaps are expected after post-allocation failures and are not treated as defects.
