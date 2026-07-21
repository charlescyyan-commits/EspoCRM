# Phase3C16.3B-2 ApprovalDecisionService Report

**Date:** 2026-07-21
**Commit Baseline:** 3b37e6d
**Phase:** C16.3B-2 — Approval decision orchestration

---

## Summary

Created `ApprovalDecisionService` — the application orchestration layer that
coordinates Approval decisions with Quote state propagation. This service is
the ONLY layer allowed to bridge both domains.

---

## Architecture

### Three-Layer Domain Separation

```
┌──────────────────────────────────────┐
│     ApprovalDecisionService          │  ← orchestration (NEW)
│   approveApproval / rejectApproval   │
│   role authorization, outer tx       │
└──────┬──────────────────┬────────────┘
       │                  │
       ▼                  ▼
┌──────────────┐  ┌────────────────────┐
│ApprovalService│  │QuoteTransitionSvc  │  ← domain (existing)
│ owns Approval │  │ owns Quote.status  │
│ .status       │  │                    │
│ audit fields  │  │                    │
└──────────────┘  └────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|---|---|
| Decision service owns the outer transaction | If any domain operation fails, both roll back atomically |
| Inner services keep their own transactions | No redesign of existing tested code; nested txn supported (C16.3B-0) |
| Validation happens before the transaction | Avoids opening a txn for trivially invalid requests |
| propagateToQuote skips when Quote already at target | Idempotent replay: previously-approved Approvals can safely re-run |
| Role check at orchestration layer | Keeps domain services pure; authorization is application concern |

---

## Implementation

### ApprovalDecisionService

**File:** `Services/ApprovalDecisionService.php`

**Constructor dependencies** (all mandatory, fail-fast):

| Dependency | Purpose |
|---|---|
| EntityManager | Persistence, entity loading, transaction management |
| ApprovalService | Approval state mutations |
| QuoteTransitionService | Quote state mutations |

**Methods:**

#### approveApproval(Entity $approval, User $actor, ?string $reason): Entity

1. Validate target type is `Quote`
2. Validate target exists
3. Assert manage role (Manager / Sales Manager / Admin)
4. **Transaction:**
   - Call `ApprovalService::approve()` (four-eyes, idempotency enforced there)
   - Load target Quote
   - If Quote not already `APPROVED`: `QuoteTransitionService::transition()` → `APPROVED`
5. Return Approval entity

#### rejectApproval(Entity $approval, User $actor, string $reason): Entity

1. Validate target type is `Quote`
2. Validate target exists
3. Assert manager role
4. **Transaction:**
   - Call `ApprovalService::reject()` (conflict/idempotency enforced there)
   - Load target Quote
   - If Quote not already `DRAFT`: `QuoteTransitionService::transition()` → `DRAFT`
5. Return Approval entity

### Transaction Flow

```
ApprovalDecisionService Transaction START
  ├── ApprovalService::approve() [inner txn via savepoint]
  │     ├── lockApproval (SELECT FOR UPDATE)
  │     ├── validate state + four-eyes
  │     └── saveEntity (Approval)
  ├── loadTargetQuote
  └── QuoteTransitionService::transition() [inner txn via savepoint]
        ├── validateTransition
        ├── saveEntity (Quote)
        └── afterTransition (no-op: not DRAFT→IN_REVIEW)
ApprovalDecisionService Transaction COMMIT / ROLLBACK
```

---

## Idempotency & Conflict Matrix

| Approval Status | Quote Status | approveApproval | rejectApproval |
|---|---|---|---|
| PENDING | IN_REVIEW | → APPROVED / APPROVED | → REJECTED / DRAFT |
| APPROVED | APPROVED | no-op (success) | Conflict |
| APPROVED | IN_REVIEW | → APPROVED (propagation replay) | Conflict |
| REJECTED | DRAFT | Conflict | no-op (success) |
| REJECTED | IN_REVIEW | Conflict | → DRAFT (propagation replay) |

Conflicts and four-eyes violations are thrown by `ApprovalService`, not duplicated in the decision service.

---

## Role Authorization

- ApprovalDecisionService enforces: **Manager**, **Sales Manager**, or **Admin** role
- Uses the same role-resolution pattern as `QuoteWorkflowActionService`:
  - Direct user roles + team-inherited roles
  - Admin bypass
- ApprovalService remains role-agnostic (pure domain)

---

## Tests

### New: `test_c16_approval_decision_service.py` — 21 tests

| Group | Tests | Coverage |
|---|---|---|
| Existence & structure | 2 | Namespace, class, mandatory DI |
| approveApproval contract | 4 | Signature, transaction, propagation, validation order |
| rejectApproval contract | 4 | Signature, transaction, propagation, validation order |
| Propagation replay | 2 | Status skip, delegation to transition service |
| Domain boundary | 3 | Never writes Quote/Approval directly, only allowed deps |
| Role authorization | 2 | Admin bypass, Manager/Sales Manager roles, team roles |
| Target validation | 3 | Quote type check, targetId check, missing Quote |
| Regression | 2 | ApprovalService unchanged, QuoteTransitionService unchanged |

### Updated: `test_c16_approval_service.py` — +2 tests

- `test_quote_workflow_core_integration_boundaries` — extended to verify
  ApprovalDecisionService exists
- `test_approval_service_never_depends_on_decision_service` — ApprovalService
  stays pure, no circular dep

### Updated: `test_extension_skeleton.py` — +1 entry

- Registered `ApprovalDecisionService.php` in the PHP file inventory

### Test Results: 98/98 pass

- 21 approval decision service tests (new)
- 10 approval service core tests
- 11 quote workflow core tests
- 7 quote UI action tests
- 9 quote numbering tests
- 4 quote numbering runtime integrity tests
- 38 extension skeleton tests

---

## Rollback Guarantees

| Failure Point | Outcome |
|---|---|
| ApprovalService::approve() throws (Conflict, Forbidden, etc.) | Full rollback; Quote untouched |
| QuoteTransitionService::transition() throws | Full rollback; Approval decision reverted |
| PDO/database failure at any point | Full rollback |
| Approval already APPROVED + Quote propagation fails | Approval already committed; retry emits Conflict |

No orphan: a REJECTED Approval can never leave a Quote at IN_REVIEW (it transitions to DRAFT atomically). An APPROVED Approval can never leave a Quote at IN_REVIEW (it transitions to APPROVED atomically).

---

## Remaining C16.3B Scope

NOT IMPLEMENTED in this phase:

- QuoteWorkflowActionService migration (still uses old approve/reject paths)
- UI action changes (buttons still mapped to old workflow)
- API route for approval decisions
- Reject action split (SENT→REJECTED vs Approval→DRAFT)
- Client handler changes
- ACL redesign
- AssignedUser
- Dashboard
- Notifications
- PI workflow
- PDF
- Multi-level approval

These belong to C16.3B-3 / later phases.

---

## File Changes

| File | Change |
|---|---|
| `Services/ApprovalDecisionService.php` | New — orchestration service |
| `tests/test_c16_approval_decision_service.py` | New — 21 focused contract tests |
| `tests/test_c16_approval_service.py` | +2 boundary tests, +1 integration assertion |
| `tests/test_extension_skeleton.py` | +1 PHP file registration |

---

## Validation

- ✅ 98/98 tests pass (21 new, 77 existing)
- ✅ No chitu-connector changes
- ✅ No C11 frozen file changes
- ✅ No C14 frozen file changes
- ✅ ApprovalService unchanged (pure domain)
- ✅ QuoteTransitionService unchanged (sole Quote.status writer)
- ✅ QuoteWorkflowActionService unchanged
- ✅ All domain boundaries preserved
