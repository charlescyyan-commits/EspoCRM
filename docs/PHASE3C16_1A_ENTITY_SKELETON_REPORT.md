# Phase3C16.1A — Entity Skeleton + Contract Tests Report

## Scope

This change establishes only the C16 entity, relationship, scope, and ACL skeletons. It does not add services, hooks, state transitions, numbering, calculations, PDF generation, approvals, payment processing, client layouts, dashboards, notifications, or connector behavior.

## Entities created

- `Quote` — name, quote number, status, validity date, amount, Opportunity link, and Lead link.
- `QuoteItem` — name, quantity, unit price, amount, and parent Quote link.
- `ProformaInvoice` — name, PI number, workflow status, payment status, and parent Quote link.
- `Approval` — independent C16 approval record with status, approval level, target type, target ID, and optional Quote/PI links.

Each entity definition has a matching `crm-extension/Resources/entityDefs` surface mirror. Each entity is registered by a Prospecting module scope and module/surface ACL metadata.

## Relationships

```text
Opportunity 1 <- * Quote * -> 1 Lead
Quote 1 -> * QuoteItem
Quote 1 -> * Approval
Quote 1 -> * ProformaInvoice
ProformaInvoice 1 -> * Approval
```

The `Approval` entity is new and deliberately separate from C11 `DraftApproval`. No C11/C14 relationship metadata was changed.

## Contract tests

`crm-extension/tests/test_c16_entity_contracts.py` verifies:

- all four entities are registered and surface/module entity definitions remain byte-equivalent JSON;
- required fields, link types, and identifier field sizes;
- Quote, QuoteItem, PI, and Approval relationship contracts;
- Quote, PI workflow, PI payment, and Approval state options/defaults;
- scope tab/ACL configuration and ACL mirror parity;
- the C16 metadata does not reuse `DraftApproval`, `SendExecution`, connector ownership, or `ChituSyncService`.

## Validation result

PASS — all extension JSON metadata parsed successfully. PHP lint passed for 89 existing PHP files. The extension suite passed with 81 tests, including the 6 new C16 contract tests.

PASS — the offline unified gate passed all eight gates: extension pytest (81), connector pytest (279), root/runtime pytest (162), S01 integrity pytest (12), package baseline pytest (5), extension unittest (81), artifact check, and deployment validation.

PASS — C16.1A is promoted as the `1.9.7-alpha` development artifact baseline. Its deterministic artifact SHA-256 is `9F7DA7A56DBEF95C52197A558491A76370FAEE81923827C2C292E59878ACF7E8`. The frozen `1.9.6-alpha` artifact and sidecar are retained and individually sidecar-validated as historical evidence.

No CRM rebuild is performed because this repository has no provisioned EspoCRM runtime, and this C16.1A change is metadata-only/offline-testable.

## Known limitations

- `quoteNumber` and `piNumber` fields are intentionally nullable: numbering is deferred to C16.2/C16.5 as frozen by the numbering ADR.
- State values are metadata contracts only; workflow transitions, approval automation, payment behavior, and validation guards are deferred.
- No client layouts, dashboards, notifications, PDFs, or connector integration are created in this phase.
