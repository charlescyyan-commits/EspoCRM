"""Offline contract tests for C10.0-B delivery-level idempotency."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.send_idempotency import (
    SEND_REQUEST_VERSION,
    InMemorySendIdempotencyRegistry,
    SendAttemptState,
    SendRequest,
    SendReservationStatus,
    generate_send_idempotency_key,
)


CREATED_AT = datetime(2026, 7, 14, 10, 0, 0, tzinfo=timezone.utc)


def send_request(
    *,
    draft_id: str = "draft-c09-001",
    lead_id: str = "lead-001",
    send_request_id: str = "request-001",
    provider_name: str = "future-provider",
    created_at: datetime = CREATED_AT,
) -> SendRequest:
    return SendRequest(
        draft_id=draft_id,
        lead_id=lead_id,
        send_request_id=send_request_id,
        idempotency_key=generate_send_idempotency_key(
            draft_id,
            lead_id,
            send_request_id,
            provider_name,
        ),
        provider_name=provider_name,
        created_at=created_at,
    )


class SendIdempotencyContractTests(TestCase):
    def setUp(self) -> None:
        self.registry = InMemorySendIdempotencyRegistry()

    def test_same_request_repeated_returns_existing_attempt(self) -> None:
        request = send_request()
        first = self.registry.reserve(request)
        repeated = self.registry.reserve(request)

        self.assertEqual(first.status, SendReservationStatus.RESERVED)
        self.assertEqual(repeated.status, SendReservationStatus.EXISTING)
        self.assertEqual(repeated.attempt, first.attempt)
        self.assertEqual(repeated.attempt.state, SendAttemptState.CREATED)

    def test_different_request_reserves_a_distinct_attempt(self) -> None:
        first = self.registry.reserve(send_request(send_request_id="request-001"))
        second = self.registry.reserve(send_request(send_request_id="request-002"))

        self.assertEqual(first.status, SendReservationStatus.RESERVED)
        self.assertEqual(second.status, SendReservationStatus.RESERVED)
        self.assertNotEqual(first.attempt.request.idempotency_key, second.attempt.request.idempotency_key)

    def test_retry_after_failure_requires_a_new_request_key(self) -> None:
        original = send_request(send_request_id="request-failed")
        first = self.registry.reserve(original)
        self.registry.transition(original.idempotency_key, SendAttemptState.READY)
        self.registry.transition(original.idempotency_key, SendAttemptState.PROCESSING)
        failed = self.registry.transition(original.idempotency_key, SendAttemptState.FAILED)
        replay = self.registry.reserve(original)
        retry = self.registry.reserve(send_request(send_request_id="request-retry"))

        self.assertEqual(first.status, SendReservationStatus.RESERVED)
        self.assertEqual(failed.state, SendAttemptState.FAILED)
        self.assertEqual(replay.status, SendReservationStatus.EXISTING)
        self.assertEqual(replay.attempt.state, SendAttemptState.FAILED)
        self.assertEqual(retry.status, SendReservationStatus.RESERVED)
        self.assertEqual(retry.attempt.state, SendAttemptState.CREATED)

    def test_concurrent_duplicate_attempts_reserve_once(self) -> None:
        request = send_request(send_request_id="request-concurrent")
        with ThreadPoolExecutor(max_workers=8) as executor:
            reservations = tuple(executor.map(lambda _: self.registry.reserve(request), range(16)))

        self.assertEqual(sum(item.status is SendReservationStatus.RESERVED for item in reservations), 1)
        self.assertEqual(sum(item.status is SendReservationStatus.EXISTING for item in reservations), 15)
        self.assertEqual({item.attempt.request.idempotency_key for item in reservations}, {request.idempotency_key})

    def test_invalid_request_is_rejected_without_reservation(self) -> None:
        request = send_request()
        invalid = SendRequest(
            draft_id=request.draft_id,
            lead_id=request.lead_id,
            send_request_id=request.send_request_id,
            idempotency_key="not-a-valid-key",
            provider_name=request.provider_name,
            created_at=request.created_at,
            request_version=SEND_REQUEST_VERSION,
        )

        result = self.registry.reserve(invalid)

        self.assertEqual(result.status, SendReservationStatus.INVALID)
        self.assertEqual(result.reason_code, "INVALID_IDEMPOTENCY_KEY")
        self.assertIsNone(result.attempt)
