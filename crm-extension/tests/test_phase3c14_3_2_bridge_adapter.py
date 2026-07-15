"""C14.3.2 contract checks for the CRM-side terminal bridge adapter."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SERVICE_DIR = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Services"
)
ADAPTER = SERVICE_DIR / "SendExecutionBridgeAdapterService.php"
RESULT = SERVICE_DIR / "SendExecutionBridgeResult.php"
SEND_HOOK = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Custom"
    / "Hooks"
    / "SendExecution"
    / "EmailLifecycleProjectionHook.php"
)


class BridgeAdapterContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = ADAPTER.read_text(encoding="utf-8")
        self.result = RESULT.read_text(encoding="utf-8")

    def test_sent_result_persists_execution_then_creates_email_event_for_projection(self) -> None:
        self.assertIn("'status' => 'SENT'", self.adapter)
        self.assertIn("'providerName' => 'Brevo'", self.adapter)
        self.assertIn("'providerMessageId' => $result->providerAttemptId()", self.adapter)
        self.assertIn("$this->entityManager->saveEntity($execution);", self.adapter)
        self.assertIn("$this->ensureSentEmailEvent($execution, $result);", self.adapter)
        self.assertLess(
            self.adapter.index("$this->entityManager->saveEntity($execution);"),
            self.adapter.index("$this->ensureSentEmailEvent($execution, $result);"),
        )
        for field in (
            "'externalMessageId' => $providerMessageId",
            "'eventType' => 'SENT'",
            "'source' => 'CONNECTOR_SYNC'",
            "'leadId' => $leadId",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.adapter)
        self.assertIn("projectSendExecution", SEND_HOOK.read_text(encoding="utf-8"))

    def test_failed_network_maps_to_network_and_increments_retry_count(self) -> None:
        self.assertIn("BridgeErrorClass::NETWORK => 'NETWORK'", self.adapter)
        self.assertIn("'failureCategory' => $this->failureCategory($result->errorClass())", self.adapter)
        self.assertIn("'lastError' => $result->errorCode()", self.adapter)
        self.assertIn("'retryCount' => ((int) ($execution->get('retryCount') ?? 0)) + 1", self.adapter)

    def test_failed_auth_maps_to_auth(self) -> None:
        self.assertIn("BridgeErrorClass::AUTH => 'AUTH'", self.adapter)
        self.assertIn("BridgeErrorClass::VALIDATION => 'VALIDATION'", self.adapter)
        self.assertIn("BridgeErrorClass::PROVIDER => 'PROVIDER'", self.adapter)
        self.assertIn("BridgeErrorClass::UNKNOWN => 'UNKNOWN'", self.adapter)

    def test_invalid_payload_is_rejected_before_entity_lookup(self) -> None:
        self.assertIn("private const ALLOWED_PAYLOAD_FIELDS", self.result)
        self.assertIn("private static function forbiddenLeadFields", self.result)
        self.assertIn("Missing bridge result field", self.result)
        self.assertIn("Unsupported bridge result field", self.result)
        self.assertIn("SENT result requires provider_attempt_id", self.result)
        self.assertIn("SENT result must not include an error", self.result)
        self.assertIn("FAILED result requires error_class and error_code", self.result)
        self.assertIn("error_code must be a safe upper-case code", self.result)

    def test_forbidden_lead_direct_write_is_impossible_in_adapter(self) -> None:
        for field in (
            "peEmailStatus",
            "peLastEmailDate",
            "peEmailReplyStatus",
            "peEmailCampaignName",
        ):
            with self.subTest(field=field):
                self.assertNotIn(field, self.adapter)
        for lead_access in ("getEntityById('Lead'", "getRDBRepository('Lead'"):
            with self.subTest(lead_access=lead_access):
                self.assertNotIn(lead_access, self.adapter)
        self.assertIn("'pe' . 'EmailStatus'", self.result)
        self.assertIn("Bridge result payload must not contain Lead fields", self.result)

    def test_retry_policy_fields_are_not_written(self) -> None:
        self.assertNotIn("maxRetries", self.adapter)
        self.assertNotIn("nextRetryAt", self.adapter)
        self.assertNotIn("queue", self.adapter.lower())
        self.assertNotIn("worker", self.adapter.lower())

    def test_execution_identity_and_terminal_state_contracts_are_enforced(self) -> None:
        self.assertIn("->where(['sendRequestId' => $executionId])", self.adapter)
        self.assertIn("Unknown execution:", self.adapter)
        self.assertIn("Execution is cancelled.", self.adapter)
        self.assertIn("Execution already SENT.", self.adapter)
        self.assertIn("Execution already SENT with another provider message ID.", self.adapter)
        self.assertIn("'CREATED', 'READY', 'FAILED'", self.adapter)
        self.assertIn("'externalMessageId' => $providerMessageId", self.adapter)
        self.assertIn("'eventType' => 'SENT'", self.adapter)


if __name__ == "__main__":
    unittest.main()
