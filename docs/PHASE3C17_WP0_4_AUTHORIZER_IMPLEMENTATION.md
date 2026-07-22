# Phase3C17 WP0.4 Shared Workflow Authorizer Implementation

## Result

Implemented the approved workflow-authorization convergence. `WorkflowAuthorizationService` is now the shared, read-only authorization boundary for Quote workflow commands. It defines stable internal action identifiers:

- `quote.submitForReview`
- `quote.approve`
- `quote.rejectReview`
- `quote.send`
- `quote.markCustomerRejected`
- `quote.expire`

Existing hyphenated route action values remain accepted through an alias map, including the deprecated `reject` route alias. No workflow route or client metadata was changed.

## Files changed

- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/WorkflowAuthorizationService.php` — new shared authorization service.
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteWorkflowActionService.php` — delegates record ACL, action resolution, and role authorization to the shared service.
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php` — delegates approval-decision role authorization to the shared service.
- `crm-extension/tests/test_phase3c17_wp0_4_workflow_authorizer.py` — focused WP0.4 authorization and ownership contracts.
- Existing workflow, approval-decision, namespace, and extension-inventory tests — updated to assert the centralized boundary.

## Architecture impact

The UI command service now resolves and authorizes a Quote action before selecting its existing command path. Quote transitions still delegate to `QuoteTransitionService`; approval decisions still delegate to `ApprovalDecisionService`, then `ApprovalService` and `QuoteTransitionService`.

`WorkflowAuthorizationService` checks existing Quote edit ACL for UI Quote commands and resolves direct plus team-inherited roles. `ApprovalDecisionService` retains its historical role-only authorization boundary for direct owner-service calls, preserving existing permission outcomes without imposing a new Approval ACL requirement.

The service has no status writes, entity saves, transactions, notifications, or domain-command invocation.

## Migration notes

- External route actions remain unchanged (`submit-for-review`, `approve`, `reject-review`, `send`, `mark-customer-rejected`, `expire`, and legacy `reject`).
- Internal command selection uses the stable `quote.*` action constants.
- Existing roles remain unchanged: Sales, Sales Representative, Sales User, Manager, Sales Manager, and Administrator behavior.
- `QuoteTransitionService`, `ApprovalService`, mutation guards, status metadata, ACL metadata, routes, and database schema were not modified.

## Test results

Executed from `D:\EspoCRM-Production` with the bundled Python runtime:

```text
python -m unittest crm-extension.tests.test_phase3c17_wp0_4_workflow_authorizer \
  crm-extension.tests.test_c16_quote_ui_actions \
  crm-extension.tests.test_c16_approval_decision_service -v
# Ran 42 tests — OK

python -m unittest discover -s crm-extension/tests -p test_*.py
# Ran 174 tests — OK
```

The local shell does not provide a PHP executable, so PHP lint could not be run in this checkout. The complete extension static-contract suite passed, including namespace and status-mutation ownership checks.

## Regression assessment

Low risk. Authorization logic was moved without changing its role sets, team-role lookup, administrator override, expiry restriction, or Quote edit ACL behavior. The focused contracts confirm allowed and denied policy paths, legacy action resolution, unchanged transition/approval ownership, four-eyes owner-service path, and absence of direct status mutation.
