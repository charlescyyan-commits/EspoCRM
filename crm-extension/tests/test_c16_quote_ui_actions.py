"""Offline C16.2C Quote workflow UI action and ACL contracts."""

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
HANDLER = CLIENT / "handlers" / "quote" / "workflow-transition.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16QuoteUiActionTests(unittest.TestCase):
    def test_actions_exist_with_existing_detail_action_pattern(self) -> None:
        client_def = json.loads(read(CLIENT_DEF))
        actions = {item["name"]: item for item in client_def["detailActionList"] if isinstance(item, dict)}

        expected = {
            "submitForReview": "submit-for-review",
            "approveQuote": "approve",
            "rejectQuote": "reject",
            "sendQuote": "send",
            "expireQuote": "expire",
        }
        self.assertEqual(set(actions), set(expected))
        for name in expected:
            self.assertEqual(actions[name]["acl"], "edit")
            self.assertEqual(actions[name]["handler"], "custom:handlers/quote/workflow-transition")
            self.assertIn("checkVisibilityFunction", actions[name])

    def test_actions_use_explicit_api_route_and_valid_transition_targets(self) -> None:
        routes = json.loads(read(ROUTES))
        route = next(item for item in routes if item["route"] == "/Prospecting/quote/:id/workflow/:action")

        self.assertEqual(route["method"], "post")
        self.assertEqual(route["actionClassName"], "Espo\\Modules\\Prospecting\\Api\\PostQuoteWorkflowAction")
        source = read(SERVICE)
        for action, status in (
            ("ACTION_SUBMIT_FOR_REVIEW", "STATUS_IN_REVIEW"),
            ("ACTION_APPROVE", "STATUS_APPROVED"),
            ("ACTION_REJECT", "STATUS_REJECTED"),
            ("ACTION_SEND", "STATUS_SENT"),
            ("ACTION_EXPIRE", "STATUS_EXPIRED"),
        ):
            self.assertIn(action, source)
            self.assertIn(status, source)

    def test_acl_restricts_record_and_role_before_transition(self) -> None:
        source = read(SERVICE)

        self.assertIn("$this->acl->checkEntityEdit($quote)", source)
        self.assertIn("$this->user->isAdmin()", source)
        self.assertIn("getLinkMultipleIdList('roles')", source)
        self.assertIn("'Sales User'", source)
        self.assertIn("'Sales Manager'", source)
        self.assertIn("Only administrators can expire", source)
        self.assertLess(source.index("assertActionPermission"), source.index("$this->transitionService->transition"))

    def test_only_transition_service_mutates_quote_status(self) -> None:
        handler = read(HANDLER)
        api = read(API)
        service = read(SERVICE)

        self.assertIn("$this->transitionService->transition($quote, $definition['targetStatus'], $options)", service)
        self.assertNotIn("set('status'", service)
        self.assertNotIn("saveEntity($quote)", service)
        self.assertNotIn("set('status'", api)
        self.assertNotIn("model.set('status'", handler)
        self.assertNotIn("model.save", handler)

    def test_illegal_state_remains_rejected_by_workflow_core(self) -> None:
        source = read(TRANSITION_SERVICE)

        self.assertIn("if (!$this->validateTransition($currentStatus, $targetStatus))", source)
        self.assertNotIn("STATUS_SENT => [self::STATUS_APPROVED]", source)

    def test_ui_surface_has_no_pdf_or_approval_dependency(self) -> None:
        combined = "\n".join(read(path) for path in (HANDLER, API, SERVICE))
        for token in ("Pdf", "PDF", "Approval", "DraftApproval", "ProformaInvoice", "EmailEvent", "Connector", "Worker", "Queue"):
            self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
