"""Offline contracts for Phase3C17 WP0.2 Quote Mark Accepted workflow action."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
CLIENT = ROOT / "crm-extension" / "files" / "client" / "custom" / "src"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs" / "Quote.json"
CLIENT_DEF = MODULE / "Resources" / "metadata" / "clientDefs" / "Quote.json"
AUTHORIZER = SERVICES / "WorkflowAuthorizationService.php"
POLICY = MODULE / "Resources" / "metadata" / "app" / "prospectingWorkflow.json"
WORKFLOW_ACTION = SERVICES / "QuoteWorkflowActionService.php"
TRANSITION = SERVICES / "QuoteTransitionService.php"
HANDLER = CLIENT / "handlers" / "quote" / "workflow-transition.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C17WP02MarkAcceptedTests(unittest.TestCase):
    # ------------------------------------------------------------------
    # Action identifier and route alias
    # ------------------------------------------------------------------

    def test_action_constant_and_alias_are_registered(self) -> None:
        source = read(AUTHORIZER)

        self.assertIn("ACTION_MARK_ACCEPTED = 'quote.markAccepted';", source)
        self.assertIn("'mark-accepted' => self::ACTION_MARK_ACCEPTED", source)

    def test_mark_accepted_authorization_policy(self) -> None:
        source = read(AUTHORIZER)

        # Allowed roles: Sales, Sales Representative, Sales User, Manager, Sales Manager
        self.assertIn(
            "'Sales', 'Sales Representative', 'Sales User', 'Manager', 'Sales Manager'",
            source,
        )
        # Must be in the ACTION_MARK_ACCEPTED policy entry
        self.assertIn("self::ACTION_MARK_ACCEPTED => [", source)
        # Not admin-only — extract the MARK_ACCEPTED policy block precisely
        block = source.split("self::ACTION_MARK_ACCEPTED => [")[1].split("self::ACTION_EXPIRE => [")[0]
        self.assertNotIn("'adminOnly' => true", block)

    def test_mark_accepted_metadata_binding_preserves_default_roles(self) -> None:
        policy = json.loads(read(POLICY))
        binding = policy["actionRoleBindings"]["quote.markAccepted"]
        self.assertEqual(binding["roleIds"], [])
        self.assertEqual(
            binding["roleNames"],
            ["Sales", "Sales Representative", "Sales User", "Manager", "Sales Manager"],
        )

    def test_administrator_bypass_applies_to_mark_accepted(self) -> None:
        source = read(AUTHORIZER)

        self.assertIn("if ($actor->isAdmin())", source)
        self.assertIn("return;", source)

    # ------------------------------------------------------------------
    # Workflow action mapping
    # ------------------------------------------------------------------

    def test_workflow_action_service_maps_mark_accepted(self) -> None:
        source = read(WORKFLOW_ACTION)

        self.assertIn("WorkflowAuthorizationService::ACTION_MARK_ACCEPTED => [", source)
        self.assertIn("'type' => self::TYPE_QUOTE", source)
        self.assertIn(
            "'targetStatus' => QuoteTransitionService::STATUS_ACCEPTED",
            source,
        )

    def test_mark_accepted_is_a_quote_action_not_approval(self) -> None:
        source = read(WORKFLOW_ACTION)

        # ACTION_MARK_ACCEPTED must use TYPE_QUOTE, not TYPE_APPROVAL
        block = source.split("ACTION_MARK_ACCEPTED => [")[1].split("],")[0]
        self.assertIn("TYPE_QUOTE", block)
        self.assertNotIn("TYPE_APPROVAL", block)

    # ------------------------------------------------------------------
    # Transition: SENT → ACCEPTED
    # ------------------------------------------------------------------

    def test_sent_to_accepted_is_a_valid_transition(self) -> None:
        source = read(TRANSITION)

        self.assertRegex(
            source,
            r"self::STATUS_SENT\s*=>\s*\[[^\]]*self::STATUS_ACCEPTED[^\]]*\]",
            msg="SENT → ACCEPTED must be in the transition matrix",
        )

    def test_accepted_is_a_terminal_state(self) -> None:
        source = read(TRANSITION)

        self.assertRegex(
            source,
            r"self::STATUS_ACCEPTED\s*=>\s*\[\s*\]",
            msg="ACCEPTED must have no outgoing transitions",
        )

    def test_invalid_state_rejection(self) -> None:
        source = read(TRANSITION)

        self.assertIn("if (!$this->validateTransition($currentStatus, $targetStatus))", source)
        self.assertIn("is not allowed.", source)
        # DRAFT cannot jump directly to ACCEPTED
        self.assertNotIn("STATUS_DRAFT => [self::STATUS_ACCEPTED", source)
        # ACCEPTED cannot transition to anything
        self.assertNotIn("STATUS_ACCEPTED => [self::STATUS_DRAFT", source)
        self.assertNotIn("STATUS_ACCEPTED => [self::STATUS_SENT", source)

    # ------------------------------------------------------------------
    # Audit field persistence
    # ------------------------------------------------------------------

    def test_accepted_at_and_accepted_by_are_set_on_transition(self) -> None:
        source = read(TRANSITION)

        self.assertIn("$targetStatus === self::STATUS_ACCEPTED", source)
        self.assertIn("$quote->set('acceptedAt'", source)
        self.assertIn("$quote->set('acceptedById'", source)
        self.assertIn("$quote->set('acceptedByName'", source)
        self.assertIn("new DateTimeImmutable()", source)
        self.assertIn("$this->user->getId()", source)
        self.assertIn("$this->user->get('name')", source)

    def test_audit_fields_are_set_inside_transaction(self) -> None:
        source = read(TRANSITION)

        transaction_body = source.split("getTransactionManager()->run(")[1].split("});")[0]
        self.assertIn("$targetStatus === self::STATUS_ACCEPTED", transaction_body)
        self.assertIn("$quote->set('acceptedAt'", transaction_body)

    def test_entity_defs_declare_audit_fields_read_only(self) -> None:
        entity_defs = json.loads(read(ENTITY_DEFS))
        fields = entity_defs["fields"]

        self.assertIn("acceptedAt", fields)
        self.assertIn("acceptedBy", fields)
        self.assertEqual(fields["acceptedAt"]["type"], "datetime")
        self.assertTrue(fields["acceptedAt"]["readOnly"])
        self.assertEqual(fields["acceptedBy"]["type"], "link")
        self.assertTrue(fields["acceptedBy"]["readOnly"])

    def test_accepted_by_link_is_defined(self) -> None:
        entity_defs = json.loads(read(ENTITY_DEFS))
        links = entity_defs["links"]

        self.assertIn("acceptedBy", links)
        self.assertEqual(links["acceptedBy"]["type"], "belongsTo")
        self.assertEqual(links["acceptedBy"]["entity"], "User")

    # ------------------------------------------------------------------
    # Mutation guard protection
    # ------------------------------------------------------------------

    def test_mutation_guard_still_protects_status(self) -> None:
        """acceptedAt/acceptedBy are set inside QuoteTransitionService, so
        the mutation guard's marker check still passes."""
        source = read(TRANSITION)

        # Status save still uses the authorized marker
        self.assertIn("StatusMutationSaveOption::QUOTE_STATUS_MUTATION_AUTHORIZED => true", source)
        # QuoteWorkflowActionService does NOT save entities itself
        workflow = read(WORKFLOW_ACTION)
        self.assertNotIn("saveEntity(", workflow)
        self.assertNotIn("set('status'", workflow)
        self.assertNotIn("set('acceptedAt'", workflow)
        self.assertNotIn("set('acceptedBy'", workflow)

    def test_workflow_action_service_delegates_mark_accepted_to_transition(self) -> None:
        source = read(WORKFLOW_ACTION)

        self.assertIn("$this->transitionService->transition(", source)
        # No direct status mutation
        self.assertNotIn("set('status'", source)
        self.assertNotIn("set('acceptedAt'", source)

    # ------------------------------------------------------------------
    # UI visibility
    # ------------------------------------------------------------------

    def test_mark_accepted_ui_action_in_client_defs(self) -> None:
        client_def = json.loads(read(CLIENT_DEF))
        actions_by_name = {
            item["name"]: item
            for item in client_def["detailActionList"]
            if isinstance(item, dict)
        }

        self.assertIn("markAcceptedQuote", actions_by_name)
        action = actions_by_name["markAcceptedQuote"]
        self.assertEqual(action["label"], "Mark Accepted")
        self.assertEqual(action["acl"], "edit")
        self.assertEqual(action["handler"], "custom:handlers/quote/workflow-transition")
        self.assertEqual(action["checkVisibilityFunction"], "isMarkAcceptedVisible")
        self.assertEqual(action["actionFunction"], "markAccepted")

    def test_client_handler_has_mark_accepted_methods(self) -> None:
        source = read(HANDLER)

        self.assertIn("async markAccepted()", source)
        self.assertIn("isMarkAcceptedVisible()", source)
        self.assertIn("isStatus('SENT')", source)
        self.assertIn("'mark-accepted': 'markAcceptedQuote'", source)

    def test_mark_accepted_shows_confirmation(self) -> None:
        source = read(HANDLER)

        self.assertIn("confirm(", source)
        self.assertIn("mark this quote as accepted", source)

    def test_mark_accepted_visible_only_in_sent(self) -> None:
        source = read(HANDLER)

        mark_accepted_method = source.split("isMarkAcceptedVisible()")[1].split("}")[0]
        self.assertIn("isStatus('SENT')", mark_accepted_method)
        # Must NOT be visible in other statuses
        self.assertNotIn("DRAFT", mark_accepted_method)
        self.assertNotIn("IN_REVIEW", mark_accepted_method)
        self.assertNotIn("APPROVED", mark_accepted_method)
        self.assertNotIn("EXPIRED", mark_accepted_method)

    # ------------------------------------------------------------------
    # Ownership and boundaries
    # ------------------------------------------------------------------

    def test_only_quote_transition_service_writes_accepted_fields(self) -> None:
        """acceptedAt and acceptedBy are only set in QuoteTransitionService."""
        from pathlib import Path as P

        custom_dir = ROOT / "crm-extension" / "files" / "custom" / "Espo"
        for path in custom_dir.rglob("*.php"):
            source = read(path)
            if "acceptedAt" in source or "acceptedById" in source:
                self.assertTrue(
                    str(path).endswith("QuoteTransitionService.php"),
                    msg=f"acceptedAt/acceptedBy writer found outside QuoteTransitionService: {path}",
                )

    def test_approval_service_is_not_modified(self) -> None:
        """C17 WP0.2 must not modify ApprovalService."""
        source = read(SERVICES / "ApprovalService.php")
        self.assertNotIn("markAccepted", source)
        self.assertNotIn("acceptedAt", source)
        self.assertNotIn("acceptedBy", source)
        self.assertNotIn("ACTION_MARK_ACCEPTED", source)

    def test_approval_decision_service_is_not_modified(self) -> None:
        """C17 WP0.2 must not modify ApprovalDecisionService."""
        source = read(SERVICES / "ApprovalDecisionService.php")
        self.assertNotIn("markAccepted", source)
        self.assertNotIn("acceptedAt", source)
        self.assertNotIn("ACTION_MARK_ACCEPTED", source)

    def test_no_forbidden_additions(self) -> None:
        """No PI, PDF, notification, order, customer portal, or reopen path."""
        combined = (
            read(AUTHORIZER)
            + read(WORKFLOW_ACTION)
            + read(TRANSITION)
            + read(HANDLER)
        )
        forbidden = (
            "ProformaInvoice",
            "Pdf",
            "PDF",
            "Notification",
            "Order",
            "CustomerPortal",
            "reopen",
            "Reopen",
        )
        for token in forbidden:
            self.assertNotIn(token, combined, msg=f"Forbidden token: {token}")

    def test_authorization_resolve_action_accepts_mark_accepted(self) -> None:
        source = read(AUTHORIZER)

        self.assertIn("public function resolveAction(string $action): string", source)
        self.assertIn("self::ACTION_ALIASES[$action] ?? $action", source)
        self.assertIn("'mark-accepted' => self::ACTION_MARK_ACCEPTED", source)
        self.assertIn("public function authorizeQuoteAction(", source)
        self.assertIn("$this->acl->checkEntityEdit($quote)", source)

    def test_reject_review_approval_actions_unchanged(self) -> None:
        """APPROVE and REJECT_REVIEW still route through ApprovalDecisionService."""
        source = read(WORKFLOW_ACTION)

        self.assertIn("ACTION_APPROVE", source)
        self.assertIn("ACTION_REJECT_REVIEW", source)
        self.assertIn("TYPE_APPROVAL", source)
        self.assertIn("$this->decisionService->approveApproval(", source)
        self.assertIn("$this->decisionService->rejectApproval(", source)


if __name__ == "__main__":
    unittest.main()
