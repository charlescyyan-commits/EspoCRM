# Phase3C16.1A — Contract Test Hardening Report

## Scope

This change hardens only the offline C16.1A contract tests. It does not modify entityDefs, metadata, business logic, artifacts, or release scripts.

Baseline HEAD before this hardening: `9ad55a83e2fdd74627142af2dd41fdc27859403d` (`phase3c16: promote c16.1a artifact baseline`).

## Review summary

Existing `crm-extension/tests/test_c16_entity_contracts.py` already covered entity registration/mirrors, required fields, core relationships, status enums, scopes/ACL, and a string-level boundary ban on `DraftApproval` / `SendExecution` / connector ownership.

Gaps found (no architecture defect; test coverage only):

| Gap | Risk if untested | Hardening action |
| --- | --- | --- |
| Quote → ProformaInvoice `hasMany` not asserted on Quote | Reciprocal PI link could drift silently | Extended `test_relationship_contract` |
| QuoteItem parent integrity weak | Orphan item links / missing `quoteId` index | Added `test_quote_item_relationship_integrity` |
| PI `paymentStatus` vs `status` only listed, not proven independent | Workflow/payment dimensions could be conflated | Added `test_pi_payment_status_is_separate_from_workflow_status` |
| Approval vs DraftApproval only string-banned | C16 could silently reuse C11 email-approval shape | Added `test_quote_and_approval_do_not_reuse_draft_approval` |
| Approval `targetType` / `targetId` not locked | Polymorphic target contract could drift | Extended `test_state_contract` |

No architecture stop condition was triggered. C16 `Approval` remains a distinct entity from C11 `DraftApproval`; PI workflow and payment enums remain disjoint; QuoteItem remains Quote-owned.

## Tests changed

File: `crm-extension/tests/test_c16_entity_contracts.py`

- Strengthened relationship coverage with Quote.`proformaInvoices`.
- Added QuoteItem reciprocal foreign-key, required parent, single business link, and `quoteId` index assertions.
- Added explicit PI workflow/payment dimension separation (disjoint option sets, independent defaults, SENT≠PAID ownership).
- Added structural DraftApproval isolation (C11-only fields/links absent from C16 Approval; Quote links to `Approval`, not `DraftApproval`).
- Locked Approval `targetType` options to `Quote` / `ProformaInvoice` with required `targetId`.

Test count: 6 → 9 contract tests. Existing test goals unchanged.

## Validation

| Command | Result |
| --- | --- |
| `.venv-s01\Scripts\python.exe -m pytest crm-extension/tests/test_c16_entity_contracts.py -v` | 9 passed |
| `.venv-s01\Scripts\python.exe -m pytest crm-extension/tests -q` | 84 passed, 22 subtests passed |

Full release / package rebuild was not run (out of scope for this hardening pass).

## Files touched

- `crm-extension/tests/test_c16_entity_contracts.py`
- `docs/PHASE3C16_1A_TEST_HARDENING_REPORT.md`

## Untouched boundaries

entityDefs, scopes, aclDefs, layouts, connector code, artifacts, release builders, DraftApproval, SendExecution, and C14 email lifecycle paths were not modified.

## Verdict

**PASS — C16.1A contract tests hardened; ready for remote re-review.**
