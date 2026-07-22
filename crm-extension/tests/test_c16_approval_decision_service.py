"""Offline C16.3B-2 ApprovalDecisionService contract tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
DECISION_SERVICE = SERVICES / "ApprovalDecisionService.php"
APPROVAL_SERVICE = SERVICES / "ApprovalService.php"
QUOTE_TRANSITION = SERVICES / "QuoteTransitionService.php"
QUOTE_WORKFLOW = SERVICES / "QuoteWorkflowActionService.php"
AUTHORIZER = SERVICES / "WorkflowAuthorizationService.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16ApprovalDecisionServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read(DECISION_SERVICE)
        cls.approval_src = read(APPROVAL_SERVICE)
        cls.transition_src = read(QUOTE_TRANSITION)
        cls.authorizer_src = read(AUTHORIZER)

    # ------------------------------------------------------------------
    # Existence and basic structure
    # ------------------------------------------------------------------

    def test_service_exists_with_correct_namespace_and_class(self) -> None:
        self.assertTrue(DECISION_SERVICE.is_file())
        self.assertIn("namespace Espo\\Modules\\Prospecting\\Services;", self.source)
        self.assertIn("class ApprovalDecisionService", self.source)
        self.assertNotIn("extends", self.source.split("class ApprovalDecisionService")[1].split("{")[0])

    def test_mandatory_constructor_dependencies(self) -> None:
        self.assertIn("private EntityManager $entityManager", self.source)
        self.assertIn("private WorkflowAuthorizationService $authorizationService", self.source)
        self.assertIn("private ApprovalService $approvalService", self.source)
        self.assertIn("private QuoteTransitionService $transitionService", self.source)
        # All deps are non-nullable (fail-fast DI)
        self.assertNotRegex(self.source, r"private \?\w+Service\s+\$")
        self.assertNotRegex(self.source, r"\?\w+Service\s+\$\w+\s*=\s*null")

    # ------------------------------------------------------------------
    # approveApproval contract
    # ------------------------------------------------------------------

    def test_approve_approval_method_signature(self) -> None:
        self.assertIn(
            "public function approveApproval(Entity $approval, User $actor, ?string $reason = null): Entity",
            self.source,
        )

    def test_approve_approval_uses_single_transaction(self) -> None:
        body = self._method_body("approveApproval")
        self.assertEqual(body.count("getTransactionManager()->run"), 1)
        # Delegates to ApprovalService, does not write Approval directly
        self.assertIn("$this->approvalService->approve(", body)
        self.assertNotIn("$approval->set('status'", body)
        self.assertNotIn('$approval->set("status"', body)
        self.assertNotIn("saveEntity($approval)", body)

    def test_approve_approval_propagates_to_quote(self) -> None:
        body = self._method_body("approveApproval")
        self.assertIn("$this->propagateToQuote($approval, QuoteTransitionService::STATUS_APPROVED)", body)
        # Assert propagation happens AFTER approve call succeeds
        approve_call_idx = body.index("$this->approvalService->approve(")
        propagate_idx = body.index("$this->propagateToQuote(")
        self.assertLess(approve_call_idx, propagate_idx)

    def test_approve_approval_validates_target_before_transaction(self) -> None:
        body = self._method_body("approveApproval")
        transaction_idx = body.index("getTransactionManager()->run")
        # Target validation must happen outside/before the transaction
        self.assertIn("$this->assertTargetTypeQuote($approval);", body)
        self.assertIn("$this->assertTargetExists($approval);", body)
        self.assertIn("$this->authorizationService->authorizeApprovalDecision(", body)
        self.assertIn("WorkflowAuthorizationService::ACTION_APPROVE", body)
        target_idx = body.index("$this->assertTargetTypeQuote")
        role_idx = body.index("$this->authorizationService->authorizeApprovalDecision")
        self.assertLess(target_idx, transaction_idx)
        self.assertLess(role_idx, transaction_idx)

    # ------------------------------------------------------------------
    # rejectApproval contract
    # ------------------------------------------------------------------

    def test_reject_approval_method_signature(self) -> None:
        self.assertIn(
            "public function rejectApproval(Entity $approval, User $actor, string $reason): Entity",
            self.source,
        )

    def test_reject_approval_uses_single_transaction(self) -> None:
        body = self._method_body("rejectApproval")
        self.assertEqual(body.count("getTransactionManager()->run"), 1)
        self.assertIn("$this->approvalService->reject(", body)
        self.assertNotIn("$approval->set('status'", body)
        self.assertNotIn('$approval->set("status"', body)
        self.assertNotIn("saveEntity($approval)", body)

    def test_reject_approval_propagates_to_quote(self) -> None:
        body = self._method_body("rejectApproval")
        self.assertIn("$this->propagateToQuote($approval, QuoteTransitionService::STATUS_DRAFT)", body)
        # Propagation occurs AFTER reject call
        reject_call_idx = body.index("$this->approvalService->reject(")
        propagate_idx = body.index("$this->propagateToQuote(")
        self.assertLess(reject_call_idx, propagate_idx)

    def test_reject_approval_validates_target_and_role_before_transaction(self) -> None:
        body = self._method_body("rejectApproval")
        transaction_idx = body.index("getTransactionManager()->run")
        self.assertIn("WorkflowAuthorizationService::ACTION_REJECT_REVIEW", body)
        role_idx = body.index("$this->authorizationService->authorizeApprovalDecision")
        self.assertLess(role_idx, transaction_idx)

    # ------------------------------------------------------------------
    # Propagation replay / idempotency
    # ------------------------------------------------------------------

    def test_propagate_to_quote_skips_when_already_in_target_status(self) -> None:
        self.assertIn("private function propagateToQuote", self.source)
        self.assertIn("$currentStatus === $targetStatus", self.source)
        self.assertIn("return;", self._method_body("propagateToQuote"))

    def test_propagate_to_quote_delegates_to_transition_service(self) -> None:
        body = self._method_body("propagateToQuote")
        self.assertIn("$this->transitionService->transition($quote, $targetStatus)", body)
        # Never writes Quote.status directly
        self.assertNotIn("$quote->set('status'", body)
        self.assertNotIn('$quote->set("status"', body)

    # ------------------------------------------------------------------
    # Domain boundary
    # ------------------------------------------------------------------

    def test_decision_service_never_writes_quote_status_directly(self) -> None:
        self.assertNotIn("$quote->set('status'", self.source)
        self.assertNotIn('$quote->set("status"', self.source)
        self.assertNotIn("saveEntity($quote)", self.source)

    def test_decision_service_never_writes_approval_status_directly(self) -> None:
        self.assertNotIn("$approval->set('status'", self.source)
        self.assertNotIn('$approval->set("status"', self.source)
        self.assertNotIn("saveEntity($approval)", self.source)

    def test_decision_service_depends_only_on_allowed_services(self) -> None:
        """Only ApprovalService & QuoteTransitionService are injected."""
        self.assertIn("private ApprovalService $approvalService", self.source)
        self.assertIn("private QuoteTransitionService $transitionService", self.source)
        # No forbidden deps
        forbidden = (
            "QuoteWorkflowActionService",
            "DraftApproval",
            "SendExecution",
            "EmailEvent",
            "ChituSyncService",
            "chitu_connector",
            "Brevo",
            "Queue",
            "Provider",
            "Pdf",
            "ProformaInvoiceService",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source, msg=f"Forbidden dependency: {token}")

    # ------------------------------------------------------------------
    # Role authorization
    # ------------------------------------------------------------------

    def test_approval_role_check_is_delegated_to_shared_authorizer(self) -> None:
        self.assertNotIn("assertManagerRole", self.source)
        self.assertNotIn("effectiveRoleNames", self.source)
        self.assertIn("WorkflowAuthorizationService::ACTION_APPROVE", self.source)
        self.assertIn("WorkflowAuthorizationService::ACTION_REJECT_REVIEW", self.source)
        self.assertIn("'Manager', 'Sales Manager'", self.authorizer_src)

    def test_effective_role_names_is_owned_by_shared_authorizer(self) -> None:
        self.assertIn("private function effectiveRoleNames(User $user): array", self.authorizer_src)
        self.assertIn("getLinkMultipleIdList('roles')", self.authorizer_src)
        self.assertIn("getLinkMultipleIdList('teams')", self.authorizer_src)
        self.assertIn("getEntityById('Team', $teamId)", self.authorizer_src)
        self.assertIn("getEntityById('Role', $roleId)", self.authorizer_src)

    # ------------------------------------------------------------------
    # Target validation
    # ------------------------------------------------------------------

    def test_assert_target_type_quote_rejects_non_quote_targets(self) -> None:
        self.assertIn("private function assertTargetTypeQuote", self.source)
        self.assertIn("TARGET_TYPE_QUOTE", self.source)
        self.assertIn("only supports Quote target type", self.source)

    def test_assert_target_exists_rejects_empty_target_id(self) -> None:
        self.assertIn("private function assertTargetExists", self.source)
        self.assertIn("'targetId'", self.source)
        self.assertIn("has no targetId", self.source)

    def test_load_target_quote_throws_not_found_for_missing_quote(self) -> None:
        self.assertIn("private function loadTargetQuote", self.source)
        self.assertIn("getEntityById('Quote', $quoteId)", self.source)
        self.assertIn("Target Quote was not found.", self.source)

    # ------------------------------------------------------------------
    # Regression: existing services untouched
    # ------------------------------------------------------------------

    def test_approval_service_unchanged(self) -> None:
        """C16.3A ApprovalService tests remain valid — no changes."""
        self.assertIn("class ApprovalService", self.approval_src)
        self.assertIn("public function approve(Entity $approval, User $actor, ?string $reason = null): Entity", self.approval_src)
        self.assertIn("public function reject(Entity $approval, User $actor, string $reason): Entity", self.approval_src)
        self.assertNotIn("QuoteTransitionService", self.approval_src)
        self.assertNotIn("ApprovalDecisionService", self.approval_src)

    def test_quote_transition_service_unchanged(self) -> None:
        """C16.3B-1 QuoteTransitionService remains sole Quote.status writer."""
        self.assertIn("class QuoteTransitionService", self.transition_src)
        self.assertIn("$quote->set('status', $targetStatus);", self.transition_src)
        self.assertNotIn("ApprovalDecisionService", self.transition_src)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _method_body(self, method_name: str) -> str:
        pattern = rf"public function {method_name}\(.*?\n    \}}\n"
        match = re.search(pattern, self.source, re.S)
        if match is None:
            pattern = rf"private function {method_name}\(.*?\n    \}}\n"
            match = re.search(pattern, self.source, re.S)
        self.assertIsNotNone(match, msg=f"Method {method_name} not found in source")
        assert match is not None
        return match.group(0)


if __name__ == "__main__":
    unittest.main()
