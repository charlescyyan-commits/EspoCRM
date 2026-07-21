# Phase3C16.3B-3 Action Migration Report

**Date:** 2026-07-21
**Commit Baseline:** ebbe22d
**Phase:** C16.3B-3 — Migrate quote workflow actions to approval-driven workflow

---

## Summary

Migrated user-facing workflow actions so that manager approval now operates
through the ApprovalDecisionService orchestration layer rather than directly
mutating Quote.status. Split the ambiguous "reject" into two distinct actions:
`reject-review` (internal review rejection via ApprovalDecisionService) and
`mark-customer-rejected` (customer rejection via QuoteTransitionService).

---

## Action Changes

### Old → New Mapping

| Old Action | New Action | Type | Target | Roles |
|---|---|---|---|---|
| `approve` | `approve` (rerouted) | approval | Approval PENDING → APPROVED, Quote IN_REVIEW → APPROVED | Manager, Sales Manager |
| `reject` (ambiguous) | `reject-review` | approval | Approval PENDING → REJECTED, Quote IN_REVIEW → DRAFT | Manager, Sales Manager |
| `reject` (ambiguous) | `mark-customer-rejected` | quote | Quote SENT → REJECTED | Sales + Manager |
| `reject` (alias) | ⇒ `mark-customer-rejected` | quote | backward compat | Sales + Manager |
| `submit-for-review` | `submit-for-review` | quote | Quote DRAFT → IN_REVIEW | Sales |
| `send` | `send` | quote | Quote APPROVED → SENT | Sales |
| `expire` | `expire` | quote | Quote APPROVED → EXPIRED | Admin only |

### Reject Semantic Split

```
BEFORE                          AFTER
──────                          ─────
"reject"                    ┌── reject-review (internal)
(ambiguous)   ──→           │   Approval REJECTED + Quote → DRAFT
                            │   Manager only, reason required
                            │
                            └── mark-customer-rejected (external)
                                Quote SENT → REJECTED
                                Sales + Manager
                                
                            reject (backward compat alias)
                                → mark-customer-rejected
```

---

## Implementation Details

### 1. QuoteWorkflowActionService

**New dependency:** `ApprovalDecisionService` (mandatory, fail-fast)

**Action type system:** Actions are now classified as `type: 'quote'` or
`type: 'approval'`:

- **quote type** → delegates to `QuoteTransitionService::transition()` (unchanged flow)
- **approval type** → finds the PENDING Approval for the Quote, then delegates
  to `ApprovalDecisionService::approveApproval()` or `rejectApproval()`

**New helper:** `findPendingApprovalForQuote()` — looks up the PENDING Approval
by `targetType=Quote`, `targetId=$quoteId`, `status=PENDING`.

**Backward compat:** The `reject` action constant is retained as a deprecated
alias mapped identically to `mark-customer-rejected`.

**Result reload:** After approval actions, the Quote is reloaded to reflect any
cross-domain propagation performed by ApprovalDecisionService.

### 2. PostQuoteWorkflowAction (API Controller)

- Extracts optional `reason` from request body (`$request->getParsedBody()`)
- Passes reason to `QuoteWorkflowActionService::execute($quoteId, $action, $reason)`

### 3. Client Handler (workflow-transition.js)

**New methods:**
- `rejectReview()` — prompts for reason, calls `reject-review` action
- `markCustomerRejected()` — calls `mark-customer-rejected` action

**Updated methods:**
- `approve()` — now routes through ApprovalDecisionService (action name unchanged)
- `reject()` — retained as deprecated backward-compat alias

**Visibility functions:**
- `isApproveVisible()` — IN_REVIEW
- `isRejectReviewVisible()` — IN_REVIEW (new)
- `isMarkCustomerRejectedVisible()` — SENT (new)
- `isRejectVisible()` — SENT (backward compat)
- All other visibility functions unchanged

### 4. ClientDefs (Quote.json)

Added two new detail action buttons:
- `rejectReviewQuote` — label "Reject Review"
- `markCustomerRejectedQuote` — label "Mark Customer Rejected"

Existing `rejectQuote` retained for backward compatibility.

---

## Domain Boundaries Preserved

| Service | Owns | Never touches |
|---|---|---|
| QuoteTransitionService | Quote.status | Approval.status |
| ApprovalService | Approval.status | Quote.status |
| ApprovalDecisionService | Cross-domain orchestration | Neither directly |
| QuoteWorkflowActionService | Action routing | Neither directly |

QuoteWorkflowActionService delegates to either QuoteTransitionService (for
quote-level actions) or ApprovalDecisionService (for approval-driven actions).
It never writes Quote.status or Approval.status directly.

---

## Compatibility

- **API route:** `/Prospecting/quote/:id/workflow/:action` — unchanged
- **`reject` action:** Still accepted; maps to `mark-customer-rejected` with
  identical behavior (Quote SENT → REJECTED)
- **`approve` action:** Same action name, now routed through
  ApprovalDecisionService instead of directly calling transitionService

---

## Tests

### Updated: `test_c16_quote_ui_actions.py` — 12 tests (rewritten)

| Group | Tests |
|---|---|
| Action definitions | 2 — detail action list, API route + action types |
| Approval-driven routing | 4 — approve routing, reject reason, quote delegation, API reason extraction |
| ACL/authorization | 1 — record + role checks |
| Status mutation ownership | 2 — delegation pattern, decision service unchanged |
| State machine guards | 1 — illegal transitions rejected |
| Dependency hygiene | 1 — forbidden deps check |
| Client handler | 2 — new methods, visibility functions |

### Updated: `test_c16_approval_service.py` — 1 test updated

- `test_quote_workflow_core_integration_boundaries` — Updated to allow
  ApprovalService constant references in QuoteWorkflowActionService while
  forbidding direct `$this->approvalService->` method calls

### Unchanged tests — 92/105 pass without modification

- 21 approval decision service tests
- 10 approval service core tests (9 unchanged + 1 updated)
- 11 quote workflow core tests
- 9 quote numbering tests
- 4 quote numbering runtime tests
- 38 extension skeleton tests

### Test Results: 105/105 pass

---

## Remaining C16.3B Scope

NOT IMPLEMENTED in this phase:

- ACL redesign
- Approval dashboard
- assignedUser
- Notifications
- PI approval
- PDF
- Multi-level approval

---

## File Changes

| File | Change |
|---|---|
| `Services/QuoteWorkflowActionService.php` | Migrated to approval-driven routing (+123/-38) |
| `Api/PostQuoteWorkflowAction.php` | Extracts reason from request body |
| `client/.../workflow-transition.js` | New action methods + visibility functions |
| `Resources/metadata/clientDefs/Quote.json` | Added reject-review + mark-customer-rejected buttons |
| `tests/test_c16_quote_ui_actions.py` | Rewritten for new action mapping |
| `tests/test_c16_approval_service.py` | Updated boundary assertion |

---

## Validation

- ✅ 105/105 tests pass
- ✅ No chitu-connector changes
- ✅ No C11 frozen file changes
- ✅ No C14 frozen file changes
- ✅ ApprovalService unchanged
- ✅ ApprovalDecisionService unchanged
- ✅ QuoteTransitionService unchanged
- ✅ All domain boundaries preserved
