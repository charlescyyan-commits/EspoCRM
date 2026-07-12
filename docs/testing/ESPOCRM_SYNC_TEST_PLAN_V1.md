# EspoCRM Sync Test Plan V1

## Purpose

This plan defines offline contract tests for a future implementation. Phase 3A-1 runs no EspoCRM, database, HTTP, email, provider, or real synchronization test.

## Fixture Rules

- Fixtures are synthetic, secret-free, and use reserved example domains.
- A valid fixture must satisfy `ESPOCRM_SYNC_CONTRACT_V1.json` and all semantic gates.
- Rejection fixtures must prove no mutation command would be emitted by the future receiver.
- Assertions include receiver result, mutation count, Lead count, evidence count, and audit reason code.

## Required Cases

| ID | Scenario | Expected result | Required assertion |
|---|---|---|---|
| CT-01 | Complete `OUTREACH_READY` V4 candidate with 0.76 coverage, 0.86 confidence, evidence, and non-brand domain | `SYNCED` | One Lead, linked evidence records, and one audit entry proposed. |
| CT-02 | Missing `score` object or score value | `REJECTED_VALIDATION` | Zero Lead/Evidence mutations. |
| CT-03 | Empty evidence array or missing evidence reference | `REJECTED_VALIDATION` or `REJECTED_GATE` | Zero mutations; reason identifies evidence failure. |
| CT-04 | Official-brand domain/flag | `REJECTED_GATE` | Zero mutations; official-brand reason preserved. |
| CT-05 | Technical research failure/unavailable site | `REJECTED_GATE` | Zero mutations; not reclassified as low fit. |
| CT-06 | Same domain and same idempotency/payload hash submitted twice | `ALREADY_SYNCED` on second submission | Lead count stays one; no duplicate evidence. |
| CT-07 | V3 score rules version | `REJECTED_VERSION` | No V3 data enters a V4 CRM contract. |
| CT-08 | V4 score rules version | eligible to continue to semantic gate | Version is accepted; normal gate decides outcome. |
| CT-09 | Additive optional field in `1.x` payload | accepted | Receiver ignores/preserves approved optional field without breaking required mapping. |
| CT-10 | Unknown major contract version | `REJECTED_VERSION` | Fail closed with no mutation. |
| CT-11 | Nullable country and product recommendation | `SYNCED` when other gates pass | Null remains null; no invented country/product. |
| CT-12 | Coverage below 0.50 or confidence below 0.60 | `REJECTED_GATE` | No Lead creation despite `OUTREACH_READY`. |
| CT-13 | Score tier `D` or `INSUFFICIENT_EVIDENCE` | `REJECTED_GATE` | No Lead creation. |
| CT-14 | Same canonical domain with a changed payload hash | controlled update or `CONFLICT` | Never creates a second Lead; only Engine-owned fields may change. |
| CT-15 | Existing Lead with CRM-owner/manual fields populated | controlled update | CRM-owned fields remain unchanged. |
| CT-16 | Account/Opportunity proposal supplied | `SYNCED` only for Lead/Evidence | No Account or Opportunity creation call is emitted. |

## Contract Assertions

For every accepted fixture, verify:

1. `canonical_domain` is the duplicate lookup identity.
2. Every imported evidence record includes claim, source URL, excerpt, confidence, capture time, and schema version.
3. Raw HTML, cookies, crawler logs, and debug data are absent from serialized payload and receiver audit output.
4. Lead contains all required Engine snapshot fields and exact version provenance.
5. Account and Opportunity mutation counts remain zero.

## Compatibility and Rollback Tests

- Replay a previously accepted payload after extension restart: result is `ALREADY_SYNCED`.
- Submit an unknown required semantic change: receiver returns `REJECTED_VERSION` and creates nothing.
- Force an evidence insertion failure after Lead validation: transaction rolls back with no partial Lead/Evidence import.
- Disable the integration credential: subsequent submissions are rejected before schema processing; existing CRM records remain unchanged.

## Phase 3A-1 Validation Performed

Only static validation is in scope for this phase: JSON parsing, contract-document consistency review, and confirmation that no implementation files outside `docs/espocrm-extension/` are changed.
