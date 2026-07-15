"""Offline contract tests for the C12.1 provider boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.provider_contract import (
    FakeProviderAdapter,
    FakeProviderMode,
    ProviderErrorCategory,
    ProviderStatus,
    SendRequest,
    SendResultStatus,
    map_error_to_failure_category,
)
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "provider_contract.py"
CREATED_AT = datetime(2026, 7, 14, 13, 0, tzinfo=timezone.utc)


def request() -> SendRequest:
    return SendRequest(
        request_id="provider-request-001",
        send_execution_id="send-execution-001",
        recipient="sales@example.test",
        subject="A safe fixture subject",
        body="A safe fixture body that must never be logged.",
        metadata={"campaign": "fixture", "locale": "en-US"},
        draft_hash="a" * 64,
        created_at=CREATED_AT,
    )


class ProviderContractTests(unittest.TestCase):
    def test_fake_provider_success_returns_success_and_status(self) -> None:
        adapter = FakeProviderAdapter()

        result = adapter.send(request())

        self.assertTrue(result.success)
        self.assertEqual(result.status, SendResultStatus.SUCCESS)
        self.assertEqual(result.provider_status, ProviderStatus.SENT)
        self.assertIsNone(result.error)
        self.assertEqual(adapter.get_status(result.provider_message_id or ""), ProviderStatus.SENT)

    def test_timeout_is_network_error_and_retryable(self) -> None:
        result = FakeProviderAdapter(mode=FakeProviderMode.TIMEOUT).send(request())

        self.assertFalse(result.success)
        self.assertEqual(result.status, SendResultStatus.RETRYABLE_FAILURE)
        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.NETWORK_ERROR)
        self.assertEqual(map_error_to_failure_category(result.error.category), FailureCategory.NETWORK)  # type: ignore[union-attr]

    def test_auth_failure_maps_to_auth_error(self) -> None:
        result = FakeProviderAdapter(
            mode=FakeProviderMode.FAILURE,
            failure_category=ProviderErrorCategory.AUTH_ERROR,
        ).send(request())

        self.assertEqual(result.status, SendResultStatus.PERMANENT_FAILURE)
        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.AUTH_ERROR)
        self.assertEqual(map_error_to_failure_category(result.error.category), FailureCategory.AUTH)  # type: ignore[union-attr]

    def test_rate_limit_maps_to_rate_limit(self) -> None:
        result = FakeProviderAdapter(
            mode=FakeProviderMode.FAILURE,
            failure_category=ProviderErrorCategory.RATE_LIMIT,
        ).send(request())

        self.assertEqual(result.status, SendResultStatus.RETRYABLE_FAILURE)
        self.assertEqual(result.error and result.error.category, ProviderErrorCategory.RATE_LIMIT)
        self.assertEqual(map_error_to_failure_category(result.error.category), FailureCategory.RATE_LIMIT)  # type: ignore[union-attr]

    def test_duplicate_identity_returns_deterministic_cached_result(self) -> None:
        adapter = FakeProviderAdapter()

        first = adapter.send(request())
        repeated = adapter.send(request())

        self.assertEqual(first, repeated)
        self.assertEqual(adapter.send_call_count, 1)

    def test_no_real_provider_call_and_request_repr_redacts_content(self) -> None:
        adapter = FakeProviderAdapter()
        fixture = request()
        adapter.send(fixture)

        self.assertEqual(adapter.external_request_count, 0)
        self.assertNotIn(fixture.body, repr(fixture))
        self.assertNotIn(fixture.subject, repr(fixture))
        self.assertNotIn(fixture.recipient, repr(fixture))
        source = SOURCE.read_text(encoding="utf-8")
        for forbidden_import in ("requests", "httpx", "smtplib", "urllib", "socket", "logging"):
            self.assertNotIn(f"import {forbidden_import}", source)

    def test_c10_contract_and_tests_remain_frozen(self) -> None:
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
