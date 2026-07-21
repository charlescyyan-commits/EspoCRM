"""Offline C16.2A Quote workflow core contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
QUOTE_TRANSITION_SERVICE = SERVICES / "QuoteTransitionService.php"
QUOTE_NUMBERING_INTERFACE = SERVICES / "QuoteNumberingServiceInterface.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16QuoteWorkflowCoreTests(unittest.TestCase):
    def test_quote_transition_service_exists_in_prospecting_namespace(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("namespace Espo\\Modules\\Prospecting\\Services;", source)
        self.assertIn("class QuoteTransitionService", source)
        self.assertIn("public function validateTransition(string $currentStatus, string $targetStatus): bool", source)
        self.assertIn("public function transition(Entity $quote, string $targetStatus, array $options = []): Entity", source)
        self.assertIn("private EntityManager $entityManager", source)
        self.assertIn("private Acl $acl", source)

    def test_valid_transition_matrix_is_frozen(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)
        expected_edges = {
            ("STATUS_DRAFT", "STATUS_IN_REVIEW"),
            ("STATUS_IN_REVIEW", "STATUS_APPROVED"),
            ("STATUS_IN_REVIEW", "STATUS_DRAFT"),
            ("STATUS_APPROVED", "STATUS_SENT"),
            ("STATUS_APPROVED", "STATUS_EXPIRED"),
            ("STATUS_SENT", "STATUS_ACCEPTED"),
            ("STATUS_SENT", "STATUS_REJECTED"),
        }

        for from_status, to_status in expected_edges:
            pattern = rf"self::{from_status}\s*=>\s*\[[^\]]*self::{to_status}[^\]]*\]"
            self.assertRegex(source, pattern, msg=f"Missing transition {from_status} -> {to_status}")

        self.assertNotRegex(source, r"STATUS_SENT\s*=>\s*\[[^\]]*STATUS_DRAFT", msg="SENT -> DRAFT must stay forbidden")
        self.assertNotRegex(source, r"STATUS_ACCEPTED\s*=>\s*\[[^\]]*STATUS_DRAFT", msg="ACCEPTED -> DRAFT must stay forbidden")
        self.assertNotRegex(source, r"STATUS_REJECTED\s*=>\s*\[[^\]]*STATUS_APPROVED", msg="REJECTED -> APPROVED must stay forbidden")
        self.assertNotRegex(source, r"STATUS_DRAFT\s*=>\s*\[[^\]]*STATUS_APPROVED", msg="DRAFT -> APPROVED must pass through review")
        self.assertNotRegex(source, r"STATUS_IN_REVIEW\s*=>\s*\[[^\]]*STATUS_SENT", msg="IN_REVIEW -> SENT must pass through approval")

    def test_terminal_states_have_no_outgoing_transitions(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        for terminal in ("STATUS_ACCEPTED", "STATUS_REJECTED", "STATUS_EXPIRED"):
            self.assertRegex(source, rf"self::{terminal}\s*=>\s*\[\s*\]", msg=f"{terminal} must be terminal")

    def test_approved_to_expired_requires_time_or_admin_override(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("private function canExpire(Entity $quote, array $options): bool", source)
        self.assertIn("$targetStatus === self::STATUS_EXPIRED", source)
        self.assertIn("$options['adminOverride']", source)
        self.assertIn("$quote->get('validUntil')", source)
        self.assertIn("new DateTimeImmutable($validUntil) <= $now", source)

    def test_transition_persists_status_and_uses_transaction(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("$quote->set('status', $targetStatus);", source)
        self.assertIn("$this->entityManager->saveEntity($quote);", source)
        self.assertIn("protected function afterTransition(Entity $quote, string $fromStatus, string $toStatus): void", source)
        self.assertIn("getTransactionManager()->run", source)
        self.assertNotIn("getEntity('Approval')", source)
        self.assertNotIn('getEntity("Approval")', source)
        self.assertNotIn("getEntity('EmailEvent')", source)
        self.assertNotIn("getEntity('DraftApproval')", source)

    def test_after_transition_creates_approval_on_draft_to_review(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("use Espo\\Entities\\User;", source)
        self.assertIn("private User $user", source)
        self.assertIn("private ApprovalService $approvalService", source)
        self.assertIn("$this->approvalService->createForQuote($quote, $this->user)", source)
        self.assertIn("$fromStatus === self::STATUS_DRAFT && $toStatus === self::STATUS_IN_REVIEW", source)
        # Guard: no approval creation for other transitions
        self.assertEqual(
            1,
            source.count("$this->approvalService->createForQuote"),
            msg="Approval creation must only happen once — in the DRAFT→IN_REVIEW guard",
        )

    def test_transaction_wraps_transition_and_after_transition(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("$this->entityManager->getTransactionManager()->run(", source)
        self.assertEqual(source.count("getTransactionManager()->run"), 1)
        # afterTransition must be called INSIDE the transaction closure
        transaction_body = source.split("getTransactionManager()->run(")[1].split("});")[0]
        self.assertIn("$this->afterTransition($quote, $currentStatus, $targetStatus);", transaction_body)
        self.assertIn("$quote->set('status', $targetStatus);", transaction_body)
        self.assertIn("$this->entityManager->saveEntity($quote);", transaction_body)

    def test_numbering_boundary_is_interface_only(self) -> None:
        service = read(QUOTE_TRANSITION_SERVICE)
        interface = read(QUOTE_NUMBERING_INTERFACE)

        self.assertIn("interface QuoteNumberingServiceInterface", interface)
        self.assertIn("public function generateQuoteNumber(int|string $year): string;", interface)
        self.assertIn("public function assignQuoteNumber(Entity $quote, int|string|null $year = null): string;", interface)
        self.assertIn("private QuoteNumberingServiceInterface $numberingService", service)
        self.assertNotIn("?QuoteNumberingServiceInterface $numberingService = null", service)
        self.assertNotIn("$this->numberingService === null", service)
        self.assertIn("assignQuoteNumber($quote)", service)
        self.assertNotIn("numbering_sequence", service + interface)
        self.assertNotIn("LAST_INSERT_ID", service + interface)
        self.assertNotIn("SELECT FOR UPDATE", service + interface)

    def test_numbering_dependency_is_mandatory_fail_fast(self) -> None:
        service = read(QUOTE_TRANSITION_SERVICE)

        self.assertRegex(
            service,
            r"private QuoteNumberingServiceInterface \$numberingService[,)]",
            msg="QuoteNumberingServiceInterface must be a mandatory constructor dependency",
        )
        self.assertNotRegex(
            service,
            r"\?QuoteNumberingServiceInterface \$numberingService\s*=\s*null",
            msg="Nullable numbering DI silently disables quote numbering and is forbidden",
        )

    def test_quote_workflow_core_has_no_forbidden_dependencies(self) -> None:
        combined = "\n".join(read(path) for path in (QUOTE_TRANSITION_SERVICE, QUOTE_NUMBERING_INTERFACE))
        forbidden = (
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
            self.assertNotIn(token, combined)

    def test_service_does_not_expose_ui_or_controller_surface(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)
        source_lower = source.lower()

        self.assertNotIn("Controller", source)
        self.assertNotIn("actionClassName", source)
        self.assertNotIn("detailaction", source_lower)
        self.assertNotIn("button", source_lower)


if __name__ == "__main__":
    unittest.main()
