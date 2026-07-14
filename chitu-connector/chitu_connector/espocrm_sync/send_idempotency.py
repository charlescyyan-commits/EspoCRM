"""Provider-neutral, no-send idempotency contract for future delivery execution.

This module deliberately has no provider, network, CRM, approval, or delivery
operation. It defines how a future executor must reserve and observe one
delivery request before it is allowed to call any sending system.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from threading import RLock
from typing import Protocol


SEND_REQUEST_VERSION = "c10-send-idempotency-v1"


class SendAttemptState(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SendReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    EXISTING = "EXISTING"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class SendRequest:
    """An immutable request to reserve one future delivery attempt."""

    draft_id: str
    lead_id: str
    send_request_id: str
    idempotency_key: str
    provider_name: str
    created_at: datetime
    request_version: str = SEND_REQUEST_VERSION


@dataclass(frozen=True, slots=True)
class SendAttempt:
    """State-only representation of a reserved request; it performs no send."""

    request: SendRequest
    state: SendAttemptState = SendAttemptState.CREATED


@dataclass(frozen=True, slots=True)
class SendReservation:
    """The contract result returned before any future provider invocation."""

    status: SendReservationStatus
    attempt: SendAttempt | None
    reason_code: str | None = None


class SendIdempotencyRegistry(Protocol):
    """Persistence seam for reserving, reading, and state-tracking attempts."""

    def reserve(self, request: SendRequest) -> SendReservation: ...

    def transition(self, idempotency_key: str, state: SendAttemptState) -> SendAttempt: ...


def generate_send_idempotency_key(
    draft_id: str,
    lead_id: str,
    send_request_id: str,
    provider_name: str,
    request_version: str = SEND_REQUEST_VERSION,
) -> str:
    """Generate a stable key for one explicitly named delivery request.

    ``created_at`` is deliberately excluded, so replaying the same request at
    a later time produces the same key. A retry must use a new
    ``send_request_id`` and therefore receives a new key and a new attempt.
    """
    payload = {
        "version": request_version.strip(),
        "draft_id": draft_id.strip(),
        "lead_id": lead_id.strip(),
        "send_request_id": send_request_id.strip(),
        "provider_name": provider_name.strip().lower(),
    }
    encoded = dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def validate_send_request(value: object) -> str | None:
    """Return a stable rejection code without attempting delivery."""
    if not isinstance(value, SendRequest):
        return "INVALID_SEND_REQUEST"
    for field in ("draft_id", "lead_id", "send_request_id", "idempotency_key", "provider_name", "request_version"):
        field_value = getattr(value, field)
        if not isinstance(field_value, str) or not field_value.strip():
            return f"INVALID_{field.upper()}"
    if not isinstance(value.created_at, datetime) or value.created_at.tzinfo is None or value.created_at.utcoffset() is None:
        return "INVALID_CREATED_AT"
    if value.request_version != SEND_REQUEST_VERSION:
        return "UNSUPPORTED_REQUEST_VERSION"
    expected_key = generate_send_idempotency_key(
        value.draft_id,
        value.lead_id,
        value.send_request_id,
        value.provider_name,
        value.request_version,
    )
    if value.idempotency_key != expected_key:
        return "INVALID_IDEMPOTENCY_KEY"
    return None


class InMemorySendIdempotencyRegistry:
    """Thread-safe reference registry for contract tests and future adapters.

    It reserves and transitions state only. It does not know how to send an
    email, contact a provider, write CRM data, or approve a request.
    """

    def __init__(self) -> None:
        self._attempts_by_key: dict[str, SendAttempt] = {}
        self._lock = RLock()

    def reserve(self, request: SendRequest) -> SendReservation:
        error = validate_send_request(request)
        if error:
            return SendReservation(SendReservationStatus.INVALID, None, error)
        with self._lock:
            existing = self._attempts_by_key.get(request.idempotency_key)
            if existing is not None:
                return SendReservation(SendReservationStatus.EXISTING, existing)
            attempt = SendAttempt(request)
            self._attempts_by_key[request.idempotency_key] = attempt
            return SendReservation(SendReservationStatus.RESERVED, attempt)

    def transition(self, idempotency_key: str, state: SendAttemptState) -> SendAttempt:
        with self._lock:
            current = self._attempts_by_key.get(idempotency_key)
            if current is None:
                raise KeyError("unknown idempotency key")
            if state not in _ALLOWED_TRANSITIONS[current.state]:
                raise ValueError(f"invalid send attempt transition: {current.state} -> {state}")
            updated = replace(current, state=state)
            self._attempts_by_key[idempotency_key] = updated
            return updated


_ALLOWED_TRANSITIONS: dict[SendAttemptState, frozenset[SendAttemptState]] = {
    SendAttemptState.CREATED: frozenset({SendAttemptState.READY, SendAttemptState.CANCELLED}),
    SendAttemptState.READY: frozenset({SendAttemptState.PROCESSING, SendAttemptState.CANCELLED}),
    SendAttemptState.PROCESSING: frozenset({SendAttemptState.SENT, SendAttemptState.FAILED}),
    SendAttemptState.SENT: frozenset(),
    SendAttemptState.FAILED: frozenset(),
    SendAttemptState.CANCELLED: frozenset(),
}
