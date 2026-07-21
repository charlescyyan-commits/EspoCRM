# Phase3C16.3B-1 Core Integration Report

**Date:** 2026-07-21
**Commit Baseline:** af2521d
**Phase:** C16.3B-1 — Quote submission lifecycle → Approval creation

---

## Summary

Implemented the core integration connecting Quote submission with Approval creation.
Quote DRAFT → IN_REVIEW now automatically creates a PENDING Approval within a
transactional boundary, ensuring atomicity: if Approval creation fails, the Quote
transition rolls back entirely.

---

## Changes

### 1. QuoteTransitionService — Transaction Boundary

**Before:** `saveEntity()` followed by `afterTransition()` with no transaction
wrapping. Partial success was possible — a Quote could become IN_REVIEW without
a corresponding Approval.

**After:** The transition body (status update, save, afterTransition) is wrapped
in `TransactionManager->run()`. If any step within the closure fails, the entire
operation rolls back:

```php
return $this->entityManager->getTransactionManager()->run(
    function () use ($quote, $currentStatus, $targetStatus): Entity {
        if ($currentStatus === self::STATUS_DRAFT && $targetStatus === self::STATUS_IN_REVIEW) {
            $this->assignQuoteNumberBoundary($quote);
        }
        $quote->set('status', $targetStatus);
        $this->entityManager->saveEntity($quote);
        $this->afterTransition($quote, $currentStatus, $targetStatus);
        return $quote;
    }
);
```

**Decision:** NESTED_TRANSACTION_SUPPORTED — ApprovalService::createForQuote also
uses TransactionManager internally; EspoCRM handles nested calls via savepoints.

### 2. afterTransition — Approval Creation Hook

The previously empty `afterTransition()` now creates a PENDING Approval when a
Quote transitions from DRAFT to IN_REVIEW:

```php
protected function afterTransition(Entity $quote, string $fromStatus, string $toStatus): void
{
    if ($fromStatus === self::STATUS_DRAFT && $toStatus === self::STATUS_IN_REVIEW) {
        $this->approvalService->createForQuote($quote, $this->user);
    }
}
```

ApprovalService is injected as a mandatory constructor dependency, along with
`Espo\Entities\User` for the current user context.

**Loop prevention:** Approval creation only triggers on DRAFT → IN_REVIEW.
No other transitions (IN_REVIEW → APPROVED, IN_REVIEW → DRAFT, APPROVED → SENT)
create Approvals. ApprovalService never writes Quote.status, so no circular
trigger is possible.

### 3. State Machine — IN_REVIEW → DRAFT

Added `IN_REVIEW` → `DRAFT` to the VALID_TRANSITIONS matrix:

```php
self::STATUS_IN_REVIEW => [self::STATUS_APPROVED, self::STATUS_DRAFT],
```

This supports the future flow: Approval REJECTED → Quote IN_REVIEW → DRAFT.
`IN_REVIEW → REJECTED` was deliberately NOT added (REJECTED remains
customer-rejection only, reachable from SENT).

### 4. Number Preservation

QuoteNumberingService.assignQuoteNumber() is idempotent — it returns the
existing quoteNumber if already set. The flow DRAFT → IN_REVIEW → DRAFT →
IN_REVIEW preserves the original quote number. No changes to
QuoteNumberingService were needed.

### 5. Constructor Dependencies

QuoteTransitionService constructor now accepts five mandatory dependencies:

| Dependency | Type | Purpose |
|---|---|---|
| EntityManager | EntityManager | Persistence |
| Acl | Acl | Access control |
| QuoteNumberingServiceInterface | Interface | Quote number assignment |
| User | Espo\Entities\User | Current user (for Approval requester) |
| ApprovalService | ApprovalService | Approval creation delegation |

All dependencies are non-nullable (fail-fast DI).

### 6. Domain Ownership

The strict boundary is maintained:

| Service | Owns | Never writes |
|---|---|---|
| QuoteTransitionService | Quote.status | Approval.status |
| ApprovalService | Approval.status | Quote.status |

QuoteTransitionService delegates Approval creation to ApprovalService but does
not mutate Approval fields directly. ApprovalService never references
QuoteTransitionService or QuoteWorkflowActionService.

---

## Tests

### Updated Tests

**test_c16_quote_workflow_core.py:**
- `test_valid_transition_matrix_is_frozen` — Added `IN_REVIEW → DRAFT` edge
- `test_quote_workflow_core_has_no_forbidden_dependencies` — Removed
  "ApprovalService" from forbidden list (now a legitimate dependency)
- `test_transition_persists_status_and_uses_transaction` — Renamed from
  `test_transition_persists_status_without_writing_other_workflows`; now verifies
  transaction wrapping
- `test_service_does_not_expose_ui_or_controller_surface` — Replaced broad
  "action" substring check with specific UI pattern checks to avoid false
  positive on "Transaction"

**test_c16_approval_service.py:**
- `test_quote_workflow_core_integration_boundaries` — Replaced
  `test_quote_workflow_core_untouched_by_approval_service`; now verifies:
  - QuoteTransitionService references ApprovalService (for createForQuote)
  - QuoteWorkflowActionService does NOT reference ApprovalService
  - Existing boundary guards remain

### New Tests

**test_c16_quote_workflow_core.py:**
- `test_after_transition_creates_approval_on_draft_to_review` — Verifies:
  - User and ApprovalService are injected
  - `createForQuote` is called exactly once
  - Guard: only on DRAFT → IN_REVIEW
- `test_transaction_wraps_transition_and_after_transition` — Verifies:
  - TransactionManager is used exactly once
  - afterTransition is called INSIDE the transaction closure
  - Status update and saveEntity are inside the transaction

### Test Results

All 37 C16-focused tests pass. All 38 extension skeleton tests pass.
No regressions.

### Implicit Verifications

The existing test suite implicitly verifies:
- **Approval contract untouched:** `test_create_for_quote_contract`,
  `test_approve_contract_*`, `test_reject_contract_*` all pass unchanged
- **Number preservation:** `QuoteNumberingService.assignQuoteNumber` idempotency
  unchanged
- **QuoteWorkflowActionService clean:** No ApprovalService dependency leaked to
  UI routing layer
- **No IN_REVIEW → REJECTED:** `test_in_review_reject_contradiction_*` still
  passes
- **IN_REVIEW → DRAFT allowed:** New edge validated in transition matrix test

---

## Rollback Guarantees

| Scenario | Guarantee |
|---|---|
| Approval creation throws Conflict (duplicate PENDING) | Quote transition rolls back, status stays DRAFT |
| Approval creation throws any exception | Quote transition rolls back |
| PDO/database failure during Approval save | Full rollback |
| QuoteNumberingService sequence consumed | Gap in sequence (acceptable; documented gap policy) |

No orphan: a Quote can never be IN_REVIEW without a corresponding PENDING Approval.

---

## Remaining C16.3B Scope

NOT IMPLEMENTED in this phase:

- Approval decision propagation (APPROVED → Quote APPROVED, REJECTED → Quote DRAFT)
- ApprovalDecisionService
- Approve/reject migration
- UI changes
- API changes
- ACL changes
- Action rename (the "Reject" button still maps to STATUS_REJECTED from SENT only)
- Dashboard
- PI workflow
- PDF
- Notification
- Multi-level approval

---

## File Changes

| File | Change |
|---|---|
| `Services/QuoteTransitionService.php` | Transaction boundary, afterTransition, IN_REVIEW→DRAFT, new DI deps |
| `tests/test_c16_quote_workflow_core.py` | Updated transitions, forbidden deps, new integration tests |
| `tests/test_c16_approval_service.py` | Updated integration boundaries test |

---

## Validation

- ✅ 37 C16-focused tests pass
- ✅ 38 extension skeleton tests pass
- ✅ No forbidden dependency violations
- ✅ Domain ownership boundaries intact
- ✅ State machine frozen except for planned IN_REVIEW → DRAFT addition
