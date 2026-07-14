"""Offline contract tests for the C10.2 provider-agnostic send boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.send_idempotency import SendAttempt, SendRequest, generate_send_idempotency_key
from chitu_connector.espocrm_sync.send_provider import (
    ProviderResultStatus,
    SendProviderAdapter,
    SendProviderResult,
    SendProviderUnavailableError,
)


CREATED_AT = datetime(2026, 7, 14, 13, 0, 0, tzinfo=timezone.utc)


def send_request(
    *,
    send_request_id: str = "request-c10-2-001",
    provider_name: str = "contract-provider",
) -> SendRequest:
    return SendRequest(
        draft_id="draft-c09-001",
        lead_id="lead-001",
        send_request_id=send_request_id,
        idempotency_key=generate_send_idempotency_key(
            "draft-c09-001",
            "lead-001",
            send_request_id,
            provider_name,
        ),
        provider_name=provider_name,
        created_at=CREATED_AT,
    )


class RecordingProvider:
    provider_name = "contract-provider"

    def __init__(self, *, unavailable: bool = False, status: ProviderResultStatus = ProviderResultStatus.ACCEPTED) -> None:
        self.unavailable = unavailable
        self.status = status
        self.calls: list[tuple[SendRequest, SendAttempt]] = []
        self.result: SendProviderResult | None = None

    def submit(self, request: SendRequest, send_attempt: SendAttempt) -> SendProviderResult:
        self.calls.append((request, send_attempt))
        if self.unavailable:
            raise SendProviderUnavailableError("offline fixture")
        self.result = SendProviderResult(
            provider_name=self.provider_name,
            send_attempt_id=f"provider-attempt:{request.send_request_id}",
            idempotency_key=request.idempotency_key,
            request_version=request.request_version,
            status=self.status,
            reason_code="FIXTURE_POLICY" if self.status is ProviderResultStatus.REJECTED else None,
        )
        return self.result


class SendProviderAdapterTests(TestCase):
    def test_valid_send_request_is_accepted_by_adapter_boundary(self) -> None:
        provider = RecordingProvider()
        request = send_request()

        output = SendProviderAdapter(provider).submit(request)

        self.assertEqual(output.provider_result.status, ProviderResultStatus.ACCEPTED)
        self.assertEqual(output.provider_result.provider_name, request.provider_name)
        self.assertEqual(output.provider_result.send_attempt_id, "provider-attempt:request-c10-2-001")
        self.assertEqual(output.provider_result.idempotency_key, request.idempotency_key)
        self.assertEqual(output.provider_result.request_version, request.request_version)
        self.assertEqual(output.send_attempt.request, request)
        self.assertEqual(len(provider.calls), 1)

    def test_duplicate_idempotency_request_returns_original_result_without_provider_recall(self) -> None:
        provider = RecordingProvider()
        adapter = SendProviderAdapter(provider)
        request = send_request()

        first = adapter.submit(request)
        repeated = adapter.submit(request)

        self.assertEqual(repeated, first)
        self.assertEqual(len(provider.calls), 1)

    def test_provider_unavailable_returns_failed_trace(self) -> None:
        provider = RecordingProvider(unavailable=True)

        output = SendProviderAdapter(provider).submit(send_request())

        self.assertEqual(output.provider_result.status, ProviderResultStatus.FAILED)
        self.assertEqual(output.provider_result.reason_code, "PROVIDER_UNAVAILABLE")
        self.assertIsNotNone(output.send_attempt)
        self.assertEqual(len(provider.calls), 1)

    def test_invalid_request_is_rejected_before_provider_call(self) -> None:
        provider = RecordingProvider()
        request = send_request()
        invalid = SendRequest(
            draft_id=request.draft_id,
            lead_id=request.lead_id,
            send_request_id=request.send_request_id,
            idempotency_key="invalid",
            provider_name=request.provider_name,
            created_at=request.created_at,
            request_version=request.request_version,
        )

        output = SendProviderAdapter(provider).submit(invalid)

        self.assertEqual(output.provider_result.status, ProviderResultStatus.REJECTED)
        self.assertEqual(output.provider_result.reason_code, "INVALID_IDEMPOTENCY_KEY")
        self.assertIsNone(output.send_attempt)
        self.assertEqual(provider.calls, [])

    def test_provider_result_trace_is_preserved(self) -> None:
        provider = RecordingProvider(status=ProviderResultStatus.REJECTED)

        output = SendProviderAdapter(provider).submit(send_request())

        self.assertEqual(output.provider_result, provider.result)
        self.assertEqual(output.provider_result.reason_code, "FIXTURE_POLICY")
        self.assertEqual(output.provider_result.status, ProviderResultStatus.REJECTED)
