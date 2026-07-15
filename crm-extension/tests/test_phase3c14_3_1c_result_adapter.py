"""Static C14.3.1C CRM result-adapter boundary checks."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SERVICE = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Services"
    / "SendExecutionResultAdapterService.php"
)


class CrmResultAdapterBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SERVICE.read_text(encoding="utf-8")

    def test_service_updates_only_existing_send_execution_terminal_fields(self) -> None:
        self.assertIn("getEntityById('SendExecution', $result->executionId())", self.source)
        for field_name in ("'status'", "'providerMessageId'", "'failureCategory'", "'lastError'"):
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, self.source)
        self.assertIn("$this->entityManager->saveEntity($execution)", self.source)

    def test_service_preserves_terminal_and_duplicate_rules_without_retry(self) -> None:
        self.assertIn("'DUPLICATE_RESULT'", self.source)
        self.assertIn("'RESULT_CONFLICT'", self.source)
        self.assertIn("'RESULT_NOT_APPLICABLE'", self.source)
        self.assertIn("$currentStatus === 'READY'", self.source)
        self.assertNotIn("retryCount", self.source)
        self.assertNotIn("nextRetryAt", self.source)

    def test_service_has_no_event_reply_or_direct_lead_write(self) -> None:
        for forbidden in (
            "getEntity('EmailEvent')",
            "getEntity('ReplyEvent')",
            "getEntityById('Lead'",
            "peEmailStatus",
            "peEmailReplyStatus",
            "SendExecutionWorker",
            "ProviderAdapter",
            "Brevo",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
