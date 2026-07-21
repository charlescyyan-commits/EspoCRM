# Phase3C16.3B-4R1 Artifact + Test Recovery Report

## Scope and baseline

This recovery is based on `82bbd3b3f9cd2945d576fb07ed3375b81fdba593`.
It addresses only the stale 1.9.7-alpha release artifact and the C16 UI-action
contract that became stale after the C16.3B-3 action migration. No C16 domain
service or workflow behavior was changed.

## Artifact root cause and recovery

`crm-extension/scripts/build_release_package.py` already discovers the
extension source recursively and deterministically. The packaging logic did
not exclude `ApprovalDecisionService.php`.

The canonical `deployment/prospecting-extension-1.9.7-alpha.zip` had simply
not been rebuilt after
`files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php`
was added. The old archive had 275 entries while the source set had 276; the
missing entry was exactly the new service.

The canonical artifact and its SHA-256 sidecar were regenerated with the
existing builder. The rebuilt ZIP contains
`files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php`.

Current SHA-256:

```
B0E69A4EDF95D0CC5800F1072718B10BFC71724D1AD7A29119F41DDC3C717BB1
```

The existing builder `--check` completed successfully, confirming source and
artifact parity.

## Test-contract migration

`test_c16_entity_contracts.py` still required the pre-migration Quote action
set. Its exact action-set assertion now covers the current action surface:

- `submitForReview`
- `approveQuote`
- `rejectReviewQuote`
- `markCustomerRejectedQuote`
- `rejectQuote` (the retained compatibility alias)
- `sendQuote`
- `expireQuote`

No boundary assertion was removed or weakened. The existing focused UI-action
contracts continue to verify that approve and reject-review route through
`ApprovalDecisionService`, while customer rejection routes through
`QuoteTransitionService`.

## Validation

- PHP lint: PASS for `ApprovalDecisionService.php` and
  `QuoteWorkflowActionService.php`.
- C16 focused pytest: PASS, 82 passed.
- Full extension pytest: PASS, 160 passed and 22 subtests passed.
- Artifact builder `--check`: PASS.
- Unified offline gate: PASS.
  - PHP lint: 99 files PASS.
  - Extension pytest, connector pytest, root runtime pytest, S01 integrity,
    package baseline, extension unittest, artifact check, and deployment
    validation: all PASS.

## Remaining blockers outside this recovery

The following release-audit items remain deliberately out of scope:

- generic CRUD status-mutation guard;
- real EspoCRM 10.0.1 runtime deployment and smoke validation.

They require their own follow-up work. This recovery makes no claim to resolve
either item.
