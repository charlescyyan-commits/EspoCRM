"""Offline contracts for Phase3C17 WP0.4 shared workflow authorization."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Services"
AUTHORIZER = SERVICES / "WorkflowAuthorizationService.php"
WORKFLOW = SERVICES / "QuoteWorkflowActionService.php"
DECISION = SERVICES / "ApprovalDecisionService.php"
TRANSITION = SERVICES / "QuoteTransitionService.php"
APPROVAL = SERVICES / "ApprovalService.php"
POLICY = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "metadata" / "app" / "prospectingWorkflow.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C17WorkflowAuthorizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read(AUTHORIZER)
        cls.workflow = read(WORKFLOW)
        cls.decision = read(DECISION)
        cls.policy = json.loads(read(POLICY))

    def test_stable_action_constants_cover_the_approved_workflow_surface(self) -> None:
        expected = {
            "ACTION_SUBMIT_FOR_REVIEW": "quote.submitForReview",
            "ACTION_APPROVE": "quote.approve",
            "ACTION_REJECT_REVIEW": "quote.rejectReview",
            "ACTION_SEND": "quote.send",
            "ACTION_MARK_CUSTOMER_REJECTED": "quote.markCustomerRejected",
            "ACTION_MARK_ACCEPTED": "quote.markAccepted",
            "ACTION_EXPIRE": "quote.expire",
        }
        for constant, value in expected.items():
            self.assertIn(f"public const {constant} = '{value}';", self.source)

    def test_existing_route_actions_are_resolved_without_changing_routes(self) -> None:
        for legacy in (
            "'submit-for-review'",
            "'approve'",
            "'reject-review'",
            "'send'",
            "'mark-customer-rejected'",
            "'reject'",
        ):
            self.assertIn(legacy, self.source)
        self.assertIn("public function resolveAction(string $action): string", self.source)

    def test_existing_allowed_roles_remain_allowed(self) -> None:
        bindings = self.policy["actionRoleBindings"]
        self.assertEqual(bindings["quote.submitForReview"]["roleNames"], ["Sales", "Sales Representative", "Sales User"])
        self.assertEqual(bindings["quote.approve"]["roleNames"], ["Manager", "Sales Manager"])
        self.assertEqual(
            bindings["quote.markCustomerRejected"]["roleNames"],
            ["Sales", "Sales Representative", "Sales User", "Manager", "Sales Manager"],
        )
        self.assertIn("if ($actor->isAdmin())", self.source)

    def test_metadata_role_bindings_have_stable_schema_and_action_coverage(self) -> None:
        self.assertEqual(self.policy["version"], 1)
        bindings = self.policy["actionRoleBindings"]
        self.assertEqual(
            set(bindings),
            {
                "quote.submitForReview",
                "quote.approve",
                "quote.rejectReview",
                "quote.send",
                "quote.markCustomerRejected",
                "quote.markAccepted",
                "quote.expire",
            },
        )
        for binding in bindings.values():
            self.assertIsInstance(binding["roleIds"], list)
            self.assertIsInstance(binding["roleNames"], list)

    def test_metadata_is_loaded_with_role_id_primary_and_role_name_fallback(self) -> None:
        self.assertIn("use Espo\\Core\\Utils\\Metadata;", self.source)
        self.assertIn("private Metadata $metadata", self.source)
        self.assertIn("$this->metadata->get(['app', 'prospectingWorkflow'])", self.source)
        self.assertIn("private function effectiveRoleIds(User $user): array", self.source)
        role_id_match = self.source.index("array_intersect($binding['roleIds'], $roleIds)")
        role_name_fallback = self.source.index("array_intersect($binding['roleNames'], $this->effectiveRoleNames($actor))")
        self.assertLess(role_id_match, role_name_fallback)

    def test_role_id_binding_preserves_access_when_a_role_is_renamed(self) -> None:
        role_id_match = self.source.index("array_intersect($binding['roleIds'], $roleIds)")
        role_name_fallback = self.source.index("array_intersect($binding['roleNames'], $this->effectiveRoleNames($actor))")
        self.assertLess(role_id_match, role_name_fallback)
        self.assertIn("return;", self.source[role_id_match:role_name_fallback])

    def test_invalid_or_missing_metadata_uses_logged_deny_safe_fallback(self) -> None:
        self.assertIn("private function isValidActionRoleBindingPolicy", self.source)
        self.assertIn("private function fallbackActionRoleBindings", self.source)
        self.assertIn("private Log $log", self.source)
        self.assertIn("$this->log->warning(", self.source)
        self.assertIn("metadata is missing or invalid", self.source)
        self.assertIn("throw new Forbidden('Current role cannot perform this Quote workflow action.')", self.source)

    def test_unknown_and_denied_actions_remain_rejected(self) -> None:
        self.assertIn("throw new BadRequest('Unsupported Quote workflow action.')", self.source)
        self.assertIn("throw new Forbidden('Current role cannot perform this Quote workflow action.')", self.source)

    def test_php_policy_constant_has_no_role_display_name_dependency(self) -> None:
        options = self.source.split("private const ACTION_OPTIONS = [", 1)[1].split("];", 1)[0]
        self.assertNotIn("Sales", options)
        self.assertNotIn("Manager", options)
        self.assertNotIn("roleNames", options)

    def test_existing_denial_rules_remain_centralized(self) -> None:
        self.assertIn("$this->acl->checkEntityEdit($quote)", self.source)
        self.assertIn("Only administrators can expire an approved Quote manually.", self.source)
        self.assertIn("Current role cannot perform this Quote workflow action.", self.source)
        self.assertIn("throw new Forbidden()", self.source)

    def test_direct_and_team_role_context_remain_supported(self) -> None:
        self.assertIn("getLinkMultipleIdList('roles')", self.source)
        self.assertIn("getLinkMultipleIdList('teams')", self.source)
        self.assertIn("getEntityById('Team', $teamId)", self.source)
        self.assertIn("getEntityById('Role', $roleId)", self.source)

    def test_both_command_services_delegate_authorization_to_the_shared_service(self) -> None:
        self.assertIn("private WorkflowAuthorizationService $authorizationService", self.workflow)
        self.assertIn("$this->authorizationService->authorizeQuoteAction($quote, $this->user, $action)", self.workflow)
        self.assertIn("private WorkflowAuthorizationService $authorizationService", self.decision)
        self.assertEqual(self.decision.count("authorizeApprovalDecision("), 2)
        self.assertNotIn("assertActionPermission", self.workflow)
        self.assertNotIn("assertManagerRole", self.decision)

    def test_transition_and_approval_ownership_are_unchanged(self) -> None:
        self.assertIn("$this->transitionService->transition(", self.workflow)
        self.assertIn("$this->approvalService->approve(", self.decision)
        self.assertIn("$this->approvalService->reject(", self.decision)
        self.assertNotIn("set('status'", self.source)
        self.assertNotIn("saveEntity(", self.source)
        self.assertNotIn("getTransactionManager", self.source)
        self.assertIn("$quote->set('status', $targetStatus);", read(TRANSITION))
        self.assertIn("class ApprovalService", read(APPROVAL))


if __name__ == "__main__":
    unittest.main()
