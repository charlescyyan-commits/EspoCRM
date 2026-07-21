"""Offline C16.3B-3 Quote workflow action migration tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = ROOT / "crm-extension" / "files" / "client" / "custom" / "src"
CLIENT_DEF = MODULE / "Resources" / "metadata" / "clientDefs" / "Quote.json"
ROUTES = MODULE / "Resources" / "routes.json"
API = MODULE / "Api" / "PostQuoteWorkflowAction.php"
SERVICE = MODULE / "Services" / "QuoteWorkflowActionService.php"
TRANSITION_SERVICE = MODULE / "Services" / "QuoteTransitionService.php"
DECISION_SERVICE = MODULE / "Services" / "ApprovalDecisionService.php"
HANDLER = CLIENT / "handlers" / "quote" / "workflow-transition.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16QuoteUiActionTests(unittest.TestCase):
    # ------------------------------------------------------------------
    # Action definitions
    # ------------------------------------------------------------------

    def test_actions_exist_with_correct_detail_action_list(self) -> None:
        client_def = json.loads(read(CLIENT_DEF))
        actions = {item["name"]: item for item in client_def["detailActionList"] if isinstance(item, dict)}

        expected = {
            "submitForReview": "submit-for-review",
            "approveQuote": "approve",
            "rejectReviewQuote": "reject-review",
            "markCustomerRejectedQuote": "mark-customer-rejected",
            "rejectQuote": "reject",
            "sendQuote": "send",
            "expireQuote": "expire",
        }
        self.assertEqual(set(actions), set(expected))
        for name in expected:
            self.assertEqual(actions[name]["acl"], "edit")
            self.assertEqual(actions[name]["handler"], "custom:handlers/quote/workflow-transition")
            self.assertIn("checkVisibilityFunction", actions[name])
            self.assertIn("actionFunction", actions[name])

    def test_actions_use_explicit_api_route_and_new_action_types(self) -> None:
        routes = json.loads(read(ROUTES))
        route = next(item for item in routes if item["route"] == "/Prospecting/quote/:id/workflow/:action")

        self.assertEqual(route["method"], "post")
        self.assertEqual(route["actionClassName"], "Espo\\Modules\\Prospecting\\Api\\PostQuoteWorkflowAction")

        source = read(SERVICE)

        # Approval-driven actions (no targetStatus — delegate to ApprovalDecisionService)
        self.assertIn("ACTION_APPROVE", source)
        self.assertIn("ACTION_REJECT_REVIEW", source)
        self.assertIn("TYPE_APPROVAL", source)

        # Quote-level actions (have targetStatus)
        self.assertIn("ACTION_SUBMIT_FOR_REVIEW", source)
        self.assertIn("ACTION_MARK_CUSTOMER_REJECTED", source)
        self.assertIn("ACTION_SEND", source)
        self.assertIn("ACTION_EXPIRE", source)

        # Backward-compat alias
        self.assertIn("ACTION_REJECT", source)
        self.assertIn("deprecated", source.lower())

    # ------------------------------------------------------------------
    # Approval-driven routing
    # ------------------------------------------------------------------

    def test_approve_routes_through_approval_decision_service(self) -> None:
        source = read(SERVICE)

        self.assertIn("private ApprovalDecisionService $decisionService", source)
        self.assertIn("$this->decisionService->approveApproval(", source)
        self.assertIn("$this->decisionService->rejectApproval(", source)
        self.assertIn("executeApprovalAction", source)
        self.assertIn("findPendingApprovalForQuote", source)

    def test_reject_review_requires_reason(self) -> None:
        source = read(SERVICE)

        self.assertIn("A rejection reason is required.", source)
        self.assertIn("$reason", source)

    def test_quote_action_still_delegates_to_transition_service(self) -> None:
        source = read(SERVICE)

        self.assertIn("executeQuoteAction", source)
        self.assertIn("$this->transitionService->transition(", source)
        # Only ACTIONS with type 'quote' use transitionService directly
        self.assertIn("TYPE_QUOTE", source)

    def test_api_controller_extracts_reason_from_body(self) -> None:
        source = read(API)

        self.assertIn("getParsedBody()", source)
        self.assertIn("private function extractReason(mixed $body): ?string", source)
        self.assertIn("is_array($body)", source)
        self.assertIn("$body instanceof \\stdClass", source)
        self.assertIn("$body['reason'] ?? null", source)
        self.assertIn("$body->reason ?? null", source)
        self.assertIn("is_string($value)", source)
        self.assertIn("trim($value)", source)
        self.assertIn("$this->service->execute($quoteId, $action, $reason)", source)

    # ------------------------------------------------------------------
    # ACL and role authorization
    # ------------------------------------------------------------------

    def test_acl_restricts_record_and_role_before_action(self) -> None:
        source = read(SERVICE)

        self.assertIn("$this->acl->checkEntityEdit($quote)", source)
        self.assertIn("$this->user->isAdmin()", source)
        self.assertIn("getLinkMultipleIdList('roles')", source)
        self.assertIn("getLinkMultipleIdList('teams')", source)
        self.assertIn("getEntityById('Team', $teamId)", source)
        self.assertIn("'Sales User'", source)
        self.assertIn("'Sales Manager'", source)
        self.assertIn("Only administrators can expire", source)

    # ------------------------------------------------------------------
    # Status mutation ownership
    # ------------------------------------------------------------------

    def test_only_transition_service_mutates_quote_status(self) -> None:
        handler = read(HANDLER)
        api = read(API)
        service = read(SERVICE)
        decision = read(DECISION_SERVICE) if DECISION_SERVICE.is_file() else ""

        # QuoteWorkflowActionService delegates to transitionService OR decisionService
        self.assertIn("$this->transitionService->transition(", service)
        self.assertIn("$this->decisionService->approveApproval(", service)
        self.assertNotIn("set('status'", service)
        self.assertNotIn("saveEntity($quote)", service)
        self.assertNotIn("saveEntity($approval)", service)

        # API never mutates status
        self.assertNotIn("set('status'", api)

        # Client never mutates status
        self.assertNotIn("model.set('status'", handler)
        self.assertNotIn("model.save", handler)

    def test_approval_decision_service_unchanged(self) -> None:
        decision = read(DECISION_SERVICE)
        self.assertIn("class ApprovalDecisionService", decision)
        # Still only orchestrator — no UI change here
        self.assertNotIn("QuoteWorkflowActionService", decision)

    # ------------------------------------------------------------------
    # State machine guards
    # ------------------------------------------------------------------

    def test_illegal_state_remains_rejected_by_workflow_core(self) -> None:
        source = read(TRANSITION_SERVICE)

        self.assertIn("if (!$this->validateTransition($currentStatus, $targetStatus))", source)
        self.assertNotIn("STATUS_SENT => [self::STATUS_APPROVED]", source)
        self.assertNotIn("STATUS_IN_REVIEW => [self::STATUS_REJECTED]", source)

    # ------------------------------------------------------------------
    # Dependency hygiene
    # ------------------------------------------------------------------

    def test_workflow_action_service_has_no_forbidden_core_deps(self) -> None:
        source = read(SERVICE)

        # Allowed: ApprovalDecisionService (orchestration), QuoteTransitionService (domain)
        self.assertIn("ApprovalDecisionService", source)
        self.assertIn("QuoteTransitionService", source)

        # Forbidden: direct domain access bypassing orchestration
        forbidden = (
            "Pdf",
            "PDF",
            "DraftApproval",
            "ProformaInvoice",
            "EmailEvent",
            "Connector",
            "Worker",
            "Queue",
            "Notification",
        )
        for token in forbidden:
            self.assertNotIn(token, source, msg=f"Forbidden dep in workflow action service: {token}")

    # ------------------------------------------------------------------
    # Client handler
    # ------------------------------------------------------------------

    def test_client_handler_has_new_action_methods(self) -> None:
        source = read(HANDLER)

        # New methods
        self.assertIn("rejectReview()", source)
        self.assertIn("markCustomerRejected()", source)
        # Existing methods retained
        self.assertIn("approve()", source)
        self.assertIn("submitForReview()", source)
        self.assertIn("sendQuote()", source)
        self.assertIn("expire()", source)
        # Deprecated backward-compat
        self.assertIn("async reject()", source)
        self.assertIn("deprecated", source.lower())

    def test_client_handler_visibility_functions(self) -> None:
        source = read(HANDLER)

        self.assertIn("isSubmitForReviewVisible()", source)
        self.assertIn("isApproveVisible()", source)
        self.assertIn("isRejectReviewVisible()", source)
        self.assertIn("isMarkCustomerRejectedVisible()", source)
        self.assertIn("isRejectVisible()", source)
        self.assertIn("isSendQuoteVisible()", source)
        self.assertIn("isExpireVisible()", source)

        # Status-based visibility
        self.assertIn("isStatus('DRAFT')", source)
        self.assertIn("isStatus('IN_REVIEW')", source)
        self.assertIn("isStatus('SENT')", source)
        self.assertIn("isStatus('APPROVED')", source)


if __name__ == "__main__":
    unittest.main()
