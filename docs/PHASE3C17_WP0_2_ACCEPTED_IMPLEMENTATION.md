# Phase3C17 WP0.2 Quote Mark Accepted Implementation Report

**Status:** IMPLEMENTED
**Date:** 2026-07-22
**Baseline:** Phase3C17 WP0.4 shared authorizer (`3f051fd`)

---

## 1. Change Summary

Implemented the SENT → ACCEPTED workflow completion path. A "Mark Accepted" action is now available on Quote detail views when the Quote is in SENT status. The action routes through the shared `WorkflowAuthorizationService` → `QuoteWorkflowActionService` → `QuoteTransitionService` pipeline, consistent with all other Quote workflow actions.

## 2. Files Changed

| File | Action | Description |
|------|--------|-------------|
| `WorkflowAuthorizationService.php` | **Modified** | Added `ACTION_MARK_ACCEPTED` constant, `mark-accepted` alias, and authorization policy (Sales, Sales Rep, Sales User, Manager, Sales Manager + Admin bypass) |
| `QuoteWorkflowActionService.php` | **Modified** | Added `ACTION_MARK_ACCEPTED` to ACTIONS map with `TYPE_QUOTE` → `STATUS_ACCEPTED` |
| `QuoteTransitionService.php` | **Modified** | Sets `acceptedAt` and `acceptedBy` audit fields inside the transition transaction when target is ACCEPTED |
| `entityDefs/Quote.json` (module) | **Modified** | Added `acceptedAt` (datetime, readOnly) and `acceptedBy` (link, readOnly) field + link definitions |
| `entityDefs/Quote.json` (surface mirror) | **Modified** | Parity mirror of module entityDefs |
| `clientDefs/Quote.json` | **Modified** | Added "Mark Accepted" detail action with visibility and handler bindings |
| `workflow-transition.js` | **Modified** | Added `markAccepted()` action (with confirmation dialog), `isMarkAcceptedVisible()` (SENT-only), and menu-item mapping |
| `test_phase3c17_wp0_2_mark_accepted.py` | **Created** | 24 offline contract tests |
| `test_c16_entity_contracts.py` | **Modified** | Added `markAcceptedQuote` to expected UI action set |
| `test_c16_quote_ui_actions.py` | **Modified** | Added `markAcceptedQuote` → `mark-accepted` expected mapping |

## 3. Architecture: Ownership Verification

```
Mark Accepted UI (client handler)
  ↓  POST /Prospecting/quote/:id/workflow/mark-accepted
PostQuoteWorkflowAction (API)
  ↓  $this->service->execute($quoteId, 'mark-accepted')
QuoteWorkflowActionService
  ↓  $this->authorizationService->authorizeQuoteAction($quote, $user, 'mark-accepted')
WorkflowAuthorizationService
  ├── resolveAction('mark-accepted') → 'quote.markAccepted'
  ├── checkEntityEdit($quote)         ← existing Quote edit ACL
  ├── assertActionPermission($user)   ← role + admin check
  ↓  returns 'quote.markAccepted'
QuoteWorkflowActionService
  ↓  executeQuoteAction($quote, STATUS_ACCEPTED)
QuoteTransitionService
  ├── validateTransition(SENT, ACCEPTED) → true
  ├── set acceptedAt = now (DateTimeImmutable)
  ├── set acceptedById = $this->user->getId()
  ├── set acceptedByName = $this->user->get('name')
  ├── set status = ACCEPTED
  └── saveEntity with QUOTE_STATUS_MUTATION_AUTHORIZED marker
```

**Ownership boundaries preserved:**

| Owner | Responsibility | Unchanged? |
|-------|---------------|------------|
| `QuoteTransitionService` | Quote.status writes + acceptedAt/acceptedBy | ✅ (extended with audit fields) |
| `ApprovalService` | Approval.status writes | ✅ Not modified |
| `ApprovalDecisionService` | Approval orchestration | ✅ Not modified |
| `WorkflowAuthorizationService` | Action resolution + authorization | ✅ Extended (new action, same pattern) |
| `QuoteWorkflowActionService` | Command routing | ✅ Extended (new mapping, same pattern) |
| `QuoteStatusMutationGuard` | Terminal persistence boundary | ✅ Not modified |

## 4. Authorization Policy

| Role | Can Mark Accepted? |
|------|-------------------|
| Sales | ✅ |
| Sales Representative | ✅ |
| Sales User | ✅ |
| Manager | ✅ |
| Sales Manager | ✅ |
| Administrator | ✅ (bypass) |

Plus: Quote edit ACL must pass.

## 5. Audit Fields

| Field | Type | Writable by | Rules |
|-------|------|-------------|-------|
| `acceptedAt` | datetime | `QuoteTransitionService` only | Set to current time on SENT→ACCEPTED transition |
| `acceptedBy` | link (User) | `QuoteTransitionService` only | Set to authenticated user on SENT→ACCEPTED transition |

Both fields are `readOnly: true` in entityDefs — not client-writable via Record API.

## 6. Strict Restrictions Compliance

| Restriction | Status |
|-------------|--------|
| Do not modify ApprovalService | ✅ Not modified |
| Do not call ApprovalDecisionService | ✅ Not called for mark-accepted |
| Do not add Approval records | ✅ No approval records created |
| Do not add PI workflow | ✅ No ProformaInvoice references |
| Do not add PDF generation | ✅ No PDF references |
| Do not add notifications | ✅ No Notification references |
| Do not add order automation | ✅ No Order references |
| Do not add customer portal | ✅ No CustomerPortal references |
| Do not add reopen path | ✅ ACCEPTED is terminal (no outgoing transitions) |
| Do not create new routes | ✅ Reuses existing `/Prospecting/quote/:id/workflow/:action` |

## 7. Test Results

```
python -m unittest crm-extension.tests.test_phase3c17_wp0_2_mark_accepted -v
# Ran 24 tests — OK

python -m unittest discover -s crm-extension/tests -p test_*.py
# Ran 198 tests — OK
```

**Test coverage:**
- SENT → ACCEPTED transition validity
- Terminal state (no outgoing transitions from ACCEPTED)
- Invalid state rejection (DRAFT → ACCEPTED, ACCEPTED → anything)
- Authorization allow/deny by role
- Administrator bypass
- Audit field persistence (acceptedAt, acceptedBy)
- Audit fields set inside transaction
- Mutation guard protection (marker-based save)
- UI visibility (SENT-only)
- Confirmation dialog
- Ownership boundaries (only QuoteTransitionService writes accepted fields)
- No forbidden dependencies (PI, PDF, notification, order, portal, reopen)
- ApprovalService and ApprovalDecisionService not modified

## 8. Risk Assessment

**Low risk.** This change:

- Adds one new action following the exact pattern of all 6 existing workflow actions
- Extends the transition transaction to set audit fields — same pattern as `assignQuoteNumberBoundary`
- Does not alter any existing transition, authorization policy, or mutation guard
- Does not introduce new routes, services, or dependencies
- ACCEPTED was already a terminal state in the transition matrix — this just adds the UI to reach it
- All 174 pre-existing tests continue to pass without modification (4 test files updated to include the new action in their expected sets)

## 9. Pre-existing Architecture Used

- `QuoteTransitionService::STATUS_ACCEPTED` — existed since C16
- `VALID_TRANSITIONS[STATUS_SENT]` already included `STATUS_ACCEPTED`
- ACCEPTED already terminal (`STATUS_ACCEPTED => []`)
- `PostQuoteWorkflowAction` API route — reused without modification
- `QuoteStatusMutationGuard` — unchanged, still enforces marker-only status writes
