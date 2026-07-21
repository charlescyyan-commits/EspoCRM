"""C16.3B-0 runtime integrity: numbering DI binding and reject-matrix guard."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
BINDING = MODULE / "Binding.php"
NUMBERING = MODULE / "Services" / "QuoteNumberingService.php"
INTERFACE = MODULE / "Services" / "QuoteNumberingServiceInterface.php"
TRANSITION = MODULE / "Services" / "QuoteTransitionService.php"
CLIENT_DEF = MODULE / "Resources" / "metadata" / "clientDefs" / "Quote.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16QuoteNumberingRuntimeIntegrityTests(unittest.TestCase):
    def test_module_binding_registers_numbering_interface_once(self) -> None:
        source = read(BINDING)

        self.assertIn("namespace Espo\\Modules\\Prospecting;", source)
        self.assertIn("class Binding implements BindingProcessor", source)
        self.assertIn("QuoteNumberingServiceInterface::class", source)
        self.assertIn("QuoteNumberingService::class", source)
        self.assertEqual(source.count("bindImplementation("), 1)
        self.assertIn("bindImplementation(", source)
        self.assertLess(
            source.index("QuoteNumberingServiceInterface::class"),
            source.index("QuoteNumberingService::class"),
        )

    def test_numbering_service_uses_entity_manager_not_raw_pdo_ctor(self) -> None:
        source = read(NUMBERING)

        self.assertIn("public function __construct(private EntityManager $entityManager) {}", source)
        self.assertNotIn("private PDO $pdo", source)
        self.assertNotRegex(source, r"__construct\(private \?EntityManager")
        self.assertIn("return $this->entityManager->getPDO();", source)
        self.assertIn("private function pdo(): PDO", source)

    def test_transition_requires_numbering_and_never_skips_silently(self) -> None:
        source = read(TRANSITION)

        self.assertIn("private QuoteNumberingServiceInterface $numberingService", source)
        self.assertNotIn("?QuoteNumberingServiceInterface $numberingService = null", source)
        self.assertNotIn("$this->numberingService === null", source)
        self.assertIn("$currentStatus === self::STATUS_DRAFT && $targetStatus === self::STATUS_IN_REVIEW", source)
        self.assertIn("$this->assignQuoteNumberBoundary($quote);", source)
        self.assertIn("$this->numberingService->assignQuoteNumber($quote)", source)

    def test_in_review_reject_contradiction_is_documented_not_expanded(self) -> None:
        """Client Reject is visible in IN_REVIEW, but server forbids IN_REVIEW -> REJECTED.

        C16.3B will migrate Reject to Approval REJECTED -> Quote DRAFT.
        This phase must not invent IN_REVIEW -> REJECTED.
        """
        transition = read(TRANSITION)
        client = json.loads(read(CLIENT_DEF))
        actions = {item["name"]: item for item in client["detailActionList"] if isinstance(item, dict)}

        self.assertIn("rejectQuote", actions)
        self.assertRegex(
            transition,
            r"self::STATUS_IN_REVIEW\s*=>\s*\[[^\]]*self::STATUS_APPROVED[^\]]*\]",
        )
        self.assertNotRegex(
            transition,
            r"self::STATUS_IN_REVIEW\s*=>\s*\[[^\]]*self::STATUS_REJECTED",
            msg="Do not expand IN_REVIEW -> REJECTED here; that belongs to C16.3B Approval propagation",
        )
        # SENT -> REJECTED remains the only customer-reject style path on Quote.status.
        self.assertRegex(
            transition,
            r"self::STATUS_SENT\s*=>\s*\[[^\]]*self::STATUS_REJECTED[^\]]*\]",
        )


if __name__ == "__main__":
    unittest.main()
