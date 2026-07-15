"""Mock-HTTP tests for the C12.2 Brevo provider adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.brevo_http import BrevoHttpResponse, BrevoTransportError
from chitu_connector.espocrm_sync.brevo_provider import BrevoConfiguration, BrevoProviderAdapter
from chitu_connector.espocrm_sync.provider_contract import ProviderErrorCategory, ProviderStatus, SendRequest, SendResultStatus
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "brevo_provider.py"
HTTP_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "brevo_http.py"
CREATED_AT = datetime(2026, 7, 14, 14, 0, tzinfo=timezone.utc)


class MockBrevoHttpClient:
    def __init__(self, response: BrevoHttpResponse | Exception) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], dict[str, object], float]] = []

    def post_json(self, path: str, *, headers: dict[str, str], payload: dict[str, object], timeout_seconds: float) -> BrevoHttpResponse:
        self.calls.append((path, dict(headers), dict(payload), timeout_seconds))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def request() -> SendRequest:
    return SendRequest(
        request_id="brevo-request-001",
        send_execution_id="brevo-execution-001",
        recipient="recipient@example.test",
        subject="Fixture subject",
        body="Fixture body",
        metadata={"campaign": "fixture"},
        draft_hash="b" * 64,
        created_at=CREATED_AT,
    )


def configured_adapter(
    client: MockBrevoHttpClient,
    environment: dict[str, str] | None = None,
) -> BrevoProviderAdapter:
    values = {"BREVO_API_KEY": "test-only-key", "BREVO_SENDER_EMAIL": "sender@example.test"}
    if environment:
        values.update(environment)
    configuration = BrevoConfiguration.from_environment(values)
    return BrevoProviderAdapter(configuration, client)


class BrevoProviderAdapterTests(unittest.TestCase):
    def test_successful_send_uses_transactional_payload_and_returns_success(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "brevo-message-001"}))

        result = configured_adapter(client).send(request())

        self.assertTrue(result.success)
        self.assertEqual(result.status, SendResultStatus.SUCCESS)
        self.assertEqual(result.provider_message_id, "brevo-message-001")
        self.assertEqual(result.provider_status, ProviderStatus.ACCEPTED)
        self.assertEqual(len(client.calls), 1)
        path, headers, payload, _ = client.calls[0]
        self.assertEqual(path, "/smtp/email")
        self.assertEqual(headers["api-key"], "test-only-key")
        self.assertEqual(payload["sender"], {"email": "sender@example.test"})
        self.assertEqual(payload["to"], [{"email": "recipient@example.test"}])

    def test_acceptance_mode_rewrites_recipient_to_controlled_test_mailbox(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "brevo-acceptance-001"}))
        adapter = configured_adapter(
            client,
            {
                "BREVO_ACCEPTANCE_MODE": "true",
                "BREVO_TEST_RECIPIENT": "acceptance@example.test",
            },
        )

        result = adapter.send(request())

        self.assertTrue(result.success)
        self.assertEqual(len(client.calls), 1)
        _, _, payload, _ = client.calls[0]
        self.assertEqual(payload["to"], [{"email": "acceptance@example.test"}])
        self.assertEqual(request().recipient, "recipient@example.test")

    def test_acceptance_mode_without_test_recipient_fails_before_http(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "must-not-be-used"}))
        adapter = configured_adapter(client, {"BREVO_ACCEPTANCE_MODE": "true"})

        result = adapter.send(request())

        self.assertFalse(result.success)
        self.assertEqual(result.status, SendResultStatus.PERMANENT_FAILURE)
        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.VALIDATION_ERROR)
        self.assertEqual(result.error and result.error.safe_code, "ACCEPTANCE_RECIPIENT_NOT_CONFIGURED")
        self.assertEqual(client.calls, [])

    def test_production_mode_preserves_original_recipient(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "brevo-production-001"}))
        adapter = configured_adapter(
            client,
            {
                "BREVO_ACCEPTANCE_MODE": "false",
                "BREVO_TEST_RECIPIENT": "acceptance@example.test",
            },
        )

        result = adapter.send(request())

        self.assertTrue(result.success)
        _, _, payload, _ = client.calls[0]
        self.assertEqual(payload["to"], [{"email": "recipient@example.test"}])

    def test_401_maps_to_auth_error(self) -> None:
        result = configured_adapter(MockBrevoHttpClient(BrevoHttpResponse(401, {}))).send(request())

        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.AUTH_ERROR)
        self.assertEqual(result.status, SendResultStatus.PERMANENT_FAILURE)

    def test_429_maps_to_rate_limit(self) -> None:
        result = configured_adapter(MockBrevoHttpClient(BrevoHttpResponse(429, {}))).send(request())

        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.RATE_LIMIT)
        self.assertEqual(result.status, SendResultStatus.RETRYABLE_FAILURE)

    def test_timeout_maps_to_network_error(self) -> None:
        result = configured_adapter(MockBrevoHttpClient(BrevoTransportError("timeout"))).send(request())

        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.NETWORK_ERROR)
        self.assertEqual(result.status, SendResultStatus.RETRYABLE_FAILURE)

    def test_malformed_success_response_maps_to_unknown_error(self) -> None:
        result = configured_adapter(MockBrevoHttpClient(BrevoHttpResponse(201, {"unexpected": "value"}))).send(request())

        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.UNKNOWN_ERROR)
        self.assertEqual(result.status, SendResultStatus.PERMANENT_FAILURE)

    def test_missing_api_key_is_safe_configuration_failure_without_http_call(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "must-not-be-used"}))
        adapter = BrevoProviderAdapter(
            BrevoConfiguration.from_environment({"BREVO_SENDER_EMAIL": "sender@example.test"}),
            client,
        )

        result = adapter.send(request())

        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.VALIDATION_ERROR)
        self.assertEqual(result.error and result.error.safe_code, "MISSING_BREVO_API_KEY")
        self.assertEqual(client.calls, [])

    def test_duplicate_identity_is_cached_and_status_query_is_explicitly_unsupported(self) -> None:
        client = MockBrevoHttpClient(BrevoHttpResponse(201, {"messageId": "brevo-message-001"}))
        adapter = configured_adapter(client)

        first = adapter.send(request())
        repeated = adapter.send(request())

        self.assertEqual(first, repeated)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(adapter.get_status("brevo-message-001"), ProviderStatus.NOT_SUPPORTED)

    def test_no_logging_or_credentials_in_adapter_source_and_c10_is_frozen(self) -> None:
        adapter_source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        http_source = HTTP_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("logging", adapter_source)
        self.assertNotIn("print(", adapter_source)
        self.assertNotIn("requests", adapter_source)
        self.assertIn("class BrevoHttpClient(Protocol)", http_source)
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
