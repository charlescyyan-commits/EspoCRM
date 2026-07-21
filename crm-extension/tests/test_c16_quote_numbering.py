"""Offline C16.2B Quote numbering contract tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
QUOTE_NUMBERING_SERVICE = SERVICES / "QuoteNumberingService.php"
QUOTE_NUMBERING_INTERFACE = SERVICES / "QuoteNumberingServiceInterface.php"
QUOTE_TRANSITION_SERVICE = SERVICES / "QuoteTransitionService.php"
AFTER_INSTALL = ROOT / "crm-extension" / "scripts" / "AfterInstall.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class C16QuoteNumberingTests(unittest.TestCase):
    def test_quote_numbering_service_exists_and_implements_boundary(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)
        interface = read(QUOTE_NUMBERING_INTERFACE)

        self.assertIn("class QuoteNumberingService implements QuoteNumberingServiceInterface", source)
        self.assertIn("private EntityManager $entityManager", source)
        self.assertIn("return $this->entityManager->getPDO();", source)
        self.assertNotIn("__construct(private PDO $pdo)", source)
        self.assertIn("public function generateQuoteNumber(int|string $year): string", source)
        self.assertIn("public function assignQuoteNumber(Entity $quote, int|string|null $year = null): string", source)
        self.assertIn("public function generateQuoteNumber(int|string $year): string;", interface)
        self.assertIn("public function assignQuoteNumber(Entity $quote, int|string|null $year = null): string;", interface)

    def test_format_is_qt_year_four_digit_sequence(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)

        self.assertIn("private const NUMBER_PREFIX = 'QT';", source)
        self.assertIn("sprintf('%s-%s-%04d'", source)
        self.assertRegex("QT-2026-0001", r"^QT-\d{4}-\d{4}$")
        self.assertNotRegex("PI-2026-0001", r"^QT-\d{4}-\d{4}$")

    def test_first_number_and_sequential_increment_use_atomic_table_value(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)
        installer = read(AFTER_INSTALL)

        self.assertIn("current_value INT UNSIGNED NOT NULL DEFAULT 0", installer)
        self.assertIn("VALUES (:sequenceKey, 0)", source)
        self.assertIn("LAST_INSERT_ID(current_value + 1)", source)
        self.assertIn("SELECT LAST_INSERT_ID()", source)
        self.assertIn("return (int) $value;", source)

    def test_year_partitioning_uses_quote_year_sequence_key(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)

        self.assertIn("private const SEQUENCE_PREFIX = 'QUOTE';", source)
        self.assertIn("return self::SEQUENCE_PREFIX . '-' . $year;", source)
        self.assertNotIn("PI-", source)
        self.assertNotIn("PINumber", source)

    def test_storage_has_primary_key_for_concurrent_safety(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)
        installer = read(AFTER_INSTALL)

        self.assertNotIn("CREATE TABLE", source)
        self.assertNotIn("ALTER TABLE", source)
        self.assertIn("CREATE TABLE IF NOT EXISTS numbering_sequence", installer)
        self.assertIn("sequence_key VARCHAR(64) NOT NULL PRIMARY KEY", installer)
        self.assertIn("ENGINE=InnoDB", installer)
        self.assertRegex(
            source,
            re.compile(r"UPDATE\s+'\s*\.\s*self::TABLE\s*\.\s*'\s+SET current_value = LAST_INSERT_ID", re.S),
        )

    def test_gap_policy_does_not_recycle_after_generation(self) -> None:
        source = read(QUOTE_NUMBERING_SERVICE)

        self.assertIn("MAX_SEQUENCE_VALUE = 9999", source)
        self.assertIn("if ($nextValue > self::MAX_SEQUENCE_VALUE)", source)
        self.assertNotIn("current_value - 1", source)
        self.assertNotIn("DELETE FROM numbering_sequence", source)
        self.assertNotIn("recycle", source.lower())

    def test_transition_boundary_invokes_numbering_only_on_draft_to_review(self) -> None:
        source = read(QUOTE_TRANSITION_SERVICE)

        self.assertIn("$currentStatus === self::STATUS_DRAFT && $targetStatus === self::STATUS_IN_REVIEW", source)
        self.assertIn("$this->assignQuoteNumberBoundary($quote);", source)
        self.assertIn("$quote->set('quoteNumber', $this->numberingService->assignQuoteNumber($quote));", source)
        self.assertLess(source.index("assignQuoteNumberBoundary($quote)"), source.index("$quote->set('status', $targetStatus);"))

    def test_no_pi_connector_worker_provider_or_pdf_numbering(self) -> None:
        combined = "\n".join(read(path) for path in (QUOTE_NUMBERING_SERVICE, QUOTE_NUMBERING_INTERFACE, QUOTE_TRANSITION_SERVICE))
        forbidden = (
            "PINumber",
            "ProformaInvoice",
            "DraftApproval",
            "EmailEvent",
            "ChituSyncService",
            "chitu_connector",
            "Worker",
            "Queue",
            "Provider",
            "Pdf",
            "PDF",
        )

        for token in forbidden:
            self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
