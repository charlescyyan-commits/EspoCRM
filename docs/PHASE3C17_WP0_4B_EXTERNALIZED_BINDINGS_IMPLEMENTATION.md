# Phase3C17 WP0.4b Externalized Workflow Authorization Bindings Implementation

**Status:** IMPLEMENTED
**Date:** 2026-07-23
**Baseline:** Phase3C17 WP0.5 metadata source convergence guard (`6920719`)

---

## 1. Change Summary

Externalized the hard-coded role-to-action authorization mappings from `WorkflowAuthorizationService.php` into a declarative configuration artifact at `Resources/metadata/app/prospectingWorkflow.json`. The PHP service now reads its role bindings from the configuration artifact at construct time, eliminating a source-code-only authorization surface.

This completes the WP0.4→WP0.5 convergence: metadata source is single-tree, authorization bindings are declarative, and the guard suite covers both dimensions.

## 2. Files Changed

| File | Action | Description |
|------|--------|-------------|
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/app/prospectingWorkflow.json` | **Created** | Declarative workflow configuration: version, 7 action-to-role bindings |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/WorkflowAuthorizationService.php` | **Modified** | Reads role bindings from `prospectingWorkflow.json` at construct time via EspoCRM metadata container; removed hard-coded per-action role arrays |
| `crm-extension/tests/test_phase3c17_wp0_4_workflow_authorizer.py` | **Modified** | Added declarative-binding parity assertions: every action in code has a binding entry; every binding entry maps to a known action; role sets match |
| `crm-extension/tests/test_phase3c17_wp0_2_mark_accepted.py` | **Modified** | Updated authorization assertions to reference the declarative binding for `quote.markAccepted` |

## 3. Configuration Artifact

`Resources/metadata/app/prospectingWorkflow.json`:

| Action | Authorized Roles |
|--------|-----------------|
| `quote.submitForReview` | Sales, Sales Representative, Sales User |
| `quote.approve` | Manager, Sales Manager |
| `quote.rejectReview` | Manager, Sales Manager |
| `quote.send` | Sales, Sales Representative, Sales User |
| `quote.markCustomerRejected` | Sales, Sales Representative, Sales User, Manager, Sales Manager |
| `quote.markAccepted` | Sales, Sales Representative, Sales User, Manager, Sales Manager |
| `quote.expire` | (none — system-only via expiry guard) |

Artifact version: `1`. Format: `actionRoleBindings` mapping action identifier → `roleNames[]` + `roleIds[]` (reserved for future role-id binding).

## 4. Architecture: Binding Resolution Pipeline

```
prospectingWorkflow.json (declarative authority)
  ↓  loaded by EspoCRM metadata container
WorkflowAuthorizationService::__construct()
  ↓  reads actionRoleBindings from metadata
WorkflowAuthorizationService::assertActionPermission()
  ↓  looks up action → roleNames[]
  ↓  checks user roles + admin bypass
  ↓  returns authorized action identifier or throws Forbidden
QuoteWorkflowActionService / ApprovalDecisionService
  ↓  consume authorized action identifier unchanged
```

**Ownership boundaries preserved:**

| Owner | Responsibility | Change |
|-------|---------------|--------|
| `prospectingWorkflow.json` | Declarative role bindings | **New** |
| `WorkflowAuthorizationService` | Action resolution + role enforcement | Refactored: reads bindings instead of hard-coding |
| `QuoteWorkflowActionService` | Command routing | Unchanged |
| `QuoteTransitionService` | Quote.status writes | Unchanged |
| `ApprovalDecisionService` | Approval orchestration | Unchanged |

## 5. Strict Restrictions Compliance

| Restriction | Status |
|-------------|--------|
| Do not change authorization outcomes | ✅ Role sets identical to WP0.4 hard-coded values |
| Do not modify QuoteTransitionService | ✅ Not modified |
| Do not modify ApprovalService | ✅ Not modified |
| Do not modify ApprovalDecisionService authorization boundary | ✅ Not modified |
| Do not add new routes | ✅ No route changes |
| Do not change client metadata | ✅ No client metadata changes |
| Do not introduce runtime config dependency | ✅ Uses existing EspoCRM metadata container (already loaded) |

## 6. Test Results

```text
python -m unittest crm-extension.tests.test_phase3c17_wp0_4_workflow_authorizer -v
# Updated assertions for declarative bindings — OK

python -m unittest crm-extension.tests.test_phase3c17_wp0_2_mark_accepted -v
# Updated to reference declarative binding for mark-accepted — OK

python -m unittest discover -s crm-extension/tests -p test_*.py
# All suites — OK
```

**Added test coverage:**
- Every binding entry in `prospectingWorkflow.json` maps to a known internal action constant
- Every internal action constant has a corresponding binding entry
- Role-name sets match the pre-WP0.4b hard-coded arrays exactly
- `mark-accepted` route alias resolves through the externalized binding
- Administrator bypass still works without a binding entry

## 7. Risk Assessment

**Low risk.** This change:

- Moves authorization role mappings from PHP code to a declarative JSON artifact
- Uses the existing EspoCRM metadata container (no new dependency)
- Preserves exact role sets — authorization outcomes unchanged
- Adds parity assertions to detect any drift between code constants and binding entries
- The JSON artifact is under the same single canonical source tree guarded by WP0.5
- No runtime config, no database changes, no route changes

## 8. Pre-existing Architecture Used

- EspoCRM metadata container (`$this->metadata->get()`) — standard extension pattern
- `prospectingWorkflow.json` follows EspoCRM's `metadata/app/` convention
- Same action identifier constants (`quote.*`) as WP0.4
- Same `WorkflowAuthorizationService` service class, refactored to read bindings
