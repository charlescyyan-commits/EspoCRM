"""Offline C16.3A ApprovalService core contract tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICE = MODULE / "Services" / "ApprovalService.php"
ENTITY = MODULE / "Entities" / "Approval.php"
HOOK = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Custom"
    / "Hooks"
    / "Approval"
    / "AuditFieldProtectionHook.php"
)
QUOTE_TRANSITION = MODULE / "Services" / "QuoteTransitionService.php"
QUOTE_WORKFLOW = MODULE / "Services" / "QuoteWorkflowActionService.php"
DECISION_SERVICE = MODULE / "Services" / "ApprovalDecisionService.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16ApprovalServiceCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = read(SERVICE)
        cls.hook = read(HOOK)
        cls.entity = read(ENTITY)

    def test_service_and_entity_exist_with_mandatory_di(self) -> None:
        self.assertTrue(SERVICE.is_file())
        self.assertTrue(ENTITY.is_file())
        self.assertIn("namespace Espo\\Modules\\Prospecting\\Services;", self.service)
        self.assertIn("class ApprovalService", self.service)
        self.assertIn("public function __construct(private EntityManager $entityManager) {}", self.service)
        self.assertNotRegex(self.service, r"private \?\w+(?:Service|Interface)\s+\$")
        self.assertNotRegex(self.service, r"\?\w+(?:Service|Interface)\s+\$\w+\s*=\s*null")
        self.assertIn("class Approval extends Entity", self.entity)

    def test_create_for_quote_contract(self) -> None:
        self.assertIn("public function createForQuote(Entity $quote, User $requester): Entity", self.service)
        self.assertIn("TARGET_TYPE_QUOTE", self.service)
        self.assertIn("'status' => self::STATUS_PENDING", self.service)
        self.assertIn("'approvalLevel' => self::DEFAULT_APPROVAL_LEVEL", self.service)
        self.assertIn("'targetType' => self::TARGET_TYPE_QUOTE", self.service)
        self.assertIn("'targetId' => $quoteId", self.service)
        self.assertIn("'requestedById' => (string) $requester->getId()", self.service)
        self.assertIn("sprintf('%s Approval #%d'", self.service)
        self.assertIn("A PENDING Approval already exists for this Quote.", self.service)
        self.assertIn("findPendingForQuoteForUpdate", self.service)
        self.assertIn("->forUpdate()", self.service)
        self.assertIn("getTransactionManager()->run", self.service)

    def test_approve_contract_four_eyes_audit_and_idempotency(self) -> None:
        self.assertIn(
            "public function approve(Entity $approval, User $actor, ?string $reason = null): Entity",
            self.service,
        )
        self.assertIn("assertFourEyes", self.service)
        self.assertIn("Four-eyes rule", self.service)
        self.assertIn("'status' => self::STATUS_APPROVED", self.service)
        self.assertIn("'decision' => self::DECISION_APPROVED", self.service)
        self.assertIn("'approverId' => (string) $actor->getId()", self.service)
        self.assertIn("'decidedAt' => date('Y-m-d H:i:s')", self.service)
        self.assertIn("if ($status === self::STATUS_APPROVED)", self.service)
        self.assertIn("return $locked;", self.service)
        self.assertIn("A REJECTED Approval cannot be approved.", self.service)
        # Idempotent APPROVED path must not rewrite decidedAt before return.
        approve_method = self._method_body("approve")
        noop_block = approve_method.split("if ($status === self::STATUS_APPROVED)")[1].split("if ($status === self::STATUS_REJECTED)")[0]
        self.assertIn("return $locked;", noop_block)
        self.assertNotIn("decidedAt", noop_block)

    def test_reject_contract_reason_idempotency_and_conflicts(self) -> None:
        self.assertIn(
            "public function reject(Entity $approval, User $actor, string $reason): Entity",
            self.service,
        )
        self.assertIn("A rejection reason is required.", self.service)
        self.assertIn("'status' => self::STATUS_REJECTED", self.service)
        self.assertIn("'decision' => self::DECISION_REJECTED", self.service)
        self.assertIn("An APPROVED Approval cannot be rejected.", self.service)
        reject_method = self._method_body("reject")
        noop_block = reject_method.split("if ($status === self::STATUS_REJECTED)")[1].split("if ($status === self::STATUS_APPROVED)")[0]
        self.assertIn("return $locked;", noop_block)
        self.assertNotIn("decidedAt", noop_block)

    def test_each_public_method_uses_one_transaction_and_single_save(self) -> None:
        for method in ("createForQuote", "approve", "reject"):
            body = self._method_body(method)
            self.assertEqual(body.count("getTransactionManager()->run"), 1, msg=method)
            self.assertEqual(body.count("saveEntity("), 1, msg=f"{method} must save once")

    def test_approval_service_never_writes_quote_status(self) -> None:
        self.assertNotIn("QuoteTransitionService", self.service)
        self.assertNotIn("QuoteWorkflowActionService", self.service)
        self.assertNotIn("$quote->set('status'", self.service)
        self.assertNotIn('$quote->set("status"', self.service)
        self.assertNotIn("saveEntity($quote)", self.service)

    def test_audit_protection_hook_locks_fields_after_decision(self) -> None:
        self.assertTrue(HOOK.is_file())
        self.assertIn("implements BeforeSave", self.hook)
        self.assertIn("Approval audit fields are immutable after a decision.", self.hook)
        for field in (
            "requestedById",
            "approverId",
            "decision",
            "decidedAt",
            "reason",
            "status",
        ):
            self.assertIn(field, self.service)
        self.assertIn("AUDIT_FIELDS", self.hook)
        self.assertIn("STATUS_APPROVED", self.hook)
        self.assertIn("STATUS_REJECTED", self.hook)

    def test_quote_workflow_core_integration_boundaries(self) -> None:
        transition = read(QUOTE_TRANSITION)
        workflow = read(QUOTE_WORKFLOW)
        decision = read(DECISION_SERVICE) if DECISION_SERVICE.is_file() else ""
        # QuoteTransitionService delegates Approval creation to ApprovalService.
        self.assertIn("ApprovalService", transition)
        self.assertIn("$this->approvalService->createForQuote", transition)
        # QuoteWorkflowActionService still routes without direct Approval knowledge.
        self.assertNotIn("ApprovalService", workflow)
        # ApprovalService still never writes Quote.status (verified above).
        # QuoteTransitionService still owns Quote.status exclusively.
        # ApprovalDecisionService is the ONLY orchestrator.
        if decision:
            self.assertIn("ApprovalDecisionService", decision)
            self.assertIn("class ApprovalDecisionService", decision)

    def test_approval_service_never_depends_on_decision_service(self) -> None:
        # ApprovalService remains a pure domain service.
        self.assertNotIn("ApprovalDecisionService", self.service)

    def _method_body(self, method_name: str) -> str:
        pattern = rf"public function {method_name}\(.*?\n    \}}\n"
        match = re.search(pattern, self.service, re.S)
        self.assertIsNotNone(match, msg=f"method {method_name} not found")
        assert match is not None
        return match.group(0)


if __name__ == "__main__":
    unittest.main()
