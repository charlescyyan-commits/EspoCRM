"""Configuration-safe acceptance fixtures for the C12.2 Brevo adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.brevo_http import BrevoHttpResponse
from chitu_connector.espocrm_sync.brevo_provider import BrevoConfiguration, BrevoProviderAdapter
from chitu_connector.espocrm_sync.provider_contract import ProviderErrorCategory, ProviderStatus, SendRequest, SendResultStatus
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "brevo_provider.py"
DOCUMENTED_SUCCESS_FIXTURE = {"messageId": "fixture-brevo-message-acceptance-001"}
CREATED_AT = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)


class FixtureBrevoHttpClient:
    """In-process documented response fixture; it never opens a transport."""

    def __init__(self, response: BrevoHttpResponse) -> None:
        self._response = response
        self.calls = 0

    def post_json(self, path: str, *, headers: dict[str, str], payload: dict[str, object], timeout_seconds: float) -> BrevoHttpResponse:
        self.calls += 1
        return self._response


def request() -> SendRequest:
    return SendRequest(
        request_id="acceptance-request-001",
        send_execution_id="acceptance-execution-001",
        recipient="test-recipient@example.test",
        subject="[C12.3 TEST] Brevo adapter acceptance fixture",
        body="This is deterministic acceptance-fixture content. No live delivery is performed.",
        metadata={"purpose": "provider-acceptance-fixture"},
        draft_hash="c" * 64,
        created_at=CREATED_AT,
    )


def adapter(response: BrevoHttpResponse) -> tuple[BrevoProviderAdapter, FixtureBrevoHttpClient]:
    client = FixtureBrevoHttpClient(response)
    config = BrevoConfiguration.from_environment(
        {"BREVO_API_KEY": "fixture-only-key", "BREVO_SENDER_EMAIL": "fixture-sender@example.test"}
    )
    return BrevoProviderAdapter(config, client), client


class BrevoAcceptanceFixtureTests(unittest.TestCase):
    def test_configuration_validation_is_safe_without_environment_credentials(self) -> None:
        configuration = BrevoConfiguration.from_environment({})

        self.assertEqual(configuration.missing_configuration_code(), "MISSING_BREVO_API_KEY")
        self.assertNotIn("fixture-only-key", repr(configuration))

    def test_documented_success_fixture_maps_message_id_and_provider_status(self) -> None:
        provider, client = adapter(BrevoHttpResponse(201, DOCUMENTED_SUCCESS_FIXTURE))

        result = provider.send(request())

        self.assertTrue(result.success)
        self.assertEqual(result.status, SendResultStatus.SUCCESS)
        self.assertEqual(result.provider_message_id, DOCUMENTED_SUCCESS_FIXTURE["messageId"])
        self.assertEqual(result.provider_status, ProviderStatus.ACCEPTED)
        self.assertEqual(client.calls, 1)

    def test_documented_error_fixtures_map_to_contract_taxonomy(self) -> None:
        cases = (
            (401, ProviderErrorCategory.AUTH_ERROR, SendResultStatus.PERMANENT_FAILURE),
            (429, ProviderErrorCategory.RATE_LIMIT, SendResultStatus.RETRYABLE_FAILURE),
            (400, ProviderErrorCategory.VALIDATION_ERROR, SendResultStatus.PERMANENT_FAILURE),
        )
        for status_code, category, result_status in cases:
            with self.subTest(status_code=status_code):
                provider, _ = adapter(BrevoHttpResponse(status_code, {}))
                result = provider.send(request())
                self.assertEqual(result.error and result.error.category, category)
                self.assertEqual(result.status, result_status)

    def test_fixture_execution_has_no_crm_side_effect_path(self) -> None:
        source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        for forbidden in ("real_client", "EntityManager", "Lead", "SendExecution", "DraftApproval", "ReplyEvent"):
            self.assertNotIn(forbidden, source)

    def test_c10_lifecycle_contract_and_tests_remain_frozen(self) -> None:
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
