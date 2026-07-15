"""C14.3.1B-1 tests for the connector-domain SendExecution bridge contract."""

from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.send_execution_bridge import (
    BridgeErrorClass,
    BridgeNormalizedStatus,
    InMemorySendExecutionBridgeFixture,
    SendExecutionBridgeRequest,
    SendExecutionBridgeResult,
    generate_idempotency_key,
    hash_recipient_reference,
)


NOW = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
CONTENT_HASH = "a" * 64


def make_request(execution_id: str = "send-execution-001") -> SendExecutionBridgeRequest:
    return SendExecutionBridgeRequest(
        execution_id=execution_id,
        idempotency_key=generate_idempotency_key(execution_id),
        content_hash=CONTENT_HASH,
        recipient_hash=hash_recipient_reference("protected-test@example.invalid"),
        campaign_reference="acceptance-campaign-reference",
        created_at=NOW,
    )


class SendExecutionBridgeContractTests(unittest.TestCase):
    def test_current_crm_execution_fields_are_not_extended_by_this_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        entity_definition = (
            root
            / "crm-extension"
            / "files"
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Resources"
            / "metadata"
            / "entityDefs"
            / "SendExecution.json"
        ).read_text(encoding="utf-8")

        self.assertIn('"sendRequestId"', entity_definition)
        self.assertIn('"status"', entity_definition)
        self.assertIn('"draftApproval"', entity_definition)
        self.assertIn('"createdAt"', entity_definition)
        self.assertNotIn('"recipient"', entity_definition)
        self.assertNotIn('"contentHash"', entity_definition)

    def test_same_execution_generates_the_same_stable_idempotency_key(self) -> None:
        first = make_request()
        second = make_request()

        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(first.idempotency_key, generate_idempotency_key(first.execution_id))

        fixture = InMemorySendExecutionBridgeFixture()
        self.assertFalse(fixture.enqueue(first).duplicate)
        self.assertTrue(fixture.enqueue(second).duplicate)

    def test_different_executions_generate_different_idempotency_keys(self) -> None:
        self.assertNotEqual(
            generate_idempotency_key("send-execution-001"),
            generate_idempotency_key("send-execution-002"),
        )

    def test_request_payload_excludes_raw_recipient_and_secrets(self) -> None:
        request = make_request()
        field_names = {field.name for field in fields(SendExecutionBridgeRequest)}
        forbidden_names = {
            "recipient",
            "subject",
            "body",
            "api_key",
            "secret",
            "token",
            "authorization",
            "password",
        }

        self.assertTrue(field_names.isdisjoint(forbidden_names))
        serialized = repr(asdict(request))
        self.assertNotIn("protected-test@example.invalid", serialized)
        self.assertNotIn("BREVO", serialized)

    def test_network_terminal_failure_mapping_is_preserved(self) -> None:
        result = SendExecutionBridgeResult.terminal_failure(
            execution_id="send-execution-network",
            error_class=BridgeErrorClass.NETWORK,
            error_code="BREVO_NETWORK_ERROR",
            occurred_at=NOW,
        )

        self.assertEqual(result.normalized_status, BridgeNormalizedStatus.FAILED)
        self.assertEqual(result.error_class, BridgeErrorClass.NETWORK)
        self.assertEqual(result.error_code, "BREVO_NETWORK_ERROR")

        fixture = InMemorySendExecutionBridgeFixture()
        fixture.enqueue(make_request("send-execution-network"))
        self.assertEqual(fixture.record_result(result), result)
        self.assertEqual(fixture.result_for(result.execution_id), result)

    def test_malformed_result_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SendExecutionBridgeResult(
                execution_id="send-execution-invalid",
                provider_attempt_id=None,
                normalized_status=BridgeNormalizedStatus.SENT,
                error_class=BridgeErrorClass.NETWORK,
                error_code="BREVO_NETWORK_ERROR",
                occurred_at=NOW,
            )

        with self.assertRaises(ValueError):
            SendExecutionBridgeResult(
                execution_id="send-execution-invalid",
                provider_attempt_id=None,
                normalized_status=BridgeNormalizedStatus.FAILED,
                error_class=None,
                error_code="BREVO_NETWORK_ERROR",
                occurred_at=NOW,
            )

    def test_contract_source_has_no_execution_or_transport_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "send_execution_bridge.py"
        ).read_text(encoding="utf-8")

        forbidden_module_names = (
            "queue_contract",
            "worker_execution",
            "provider_contract",
            "brevo_http",
            "brevo_provider",
            "urllib",
            "requests",
            "http.client",
        )
        imported_source = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )
        for dependency in forbidden_module_names:
            with self.subTest(dependency=dependency):
                self.assertNotIn(dependency, imported_source)


if __name__ == "__main__":
    unittest.main()
