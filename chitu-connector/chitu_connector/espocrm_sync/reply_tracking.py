"""Reply-event tracking contract after a completed controlled send execution.

This module records provider-neutral reply events only. It has no reply
generation, AI, sentiment, scoring, CRM, follow-up, or workflow capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from json import dumps
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.send_execution import (
    SendExecutionAuditTrace,
    SendExecutionRegistry,
    SendExecutionState,
)


REPLY_EVENT_VERSION = "c10.4-reply-tracking-v1"


class ReplyStatus(StrEnum):
    SENT = "SENT"
    REPLIED = "REPLIED"
    BOUNCED = "BOUNCED"
    UNSUBSCRIBED = "UNSUBSCRIBED"


class ReplyEventReservationStatus(StrEnum):
    CREATED = "CREATED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ReplyEvent:
    """Immutable reply-tracking record with preserved original send trace."""

    reply_event_id: str
    lead_id: str
    draft_id: str
    send_attempt_id: str
    thread_id: str
    received_at: datetime
    sender_reference: str
    reply_status: ReplyStatus
    event_version: str = REPLY_EVENT_VERSION
    original_send_trace: tuple[SendExecutionAuditTrace, ...] = ()


@dataclass(frozen=True, slots=True)
class ReplyEventReservation:
    status: ReplyEventReservationStatus
    event: ReplyEvent | None
    reason_code: str | None = None


class ReplyEventRegistry(Protocol):
    """Persistence seam for deterministic, immutable reply events."""

    def record(self, event: ReplyEvent) -> ReplyEventReservation: ...

    def get(self, reply_event_id: str) -> ReplyEvent | None: ...


class InMemoryReplyEventRegistry:
    """Thread-safe reference registry; duplicate event identities are ignored."""

    def __init__(self) -> None:
        self._events_by_id: dict[str, ReplyEvent] = {}
        self._lock = RLock()

    def record(self, event: ReplyEvent) -> ReplyEventReservation:
        error = validate_reply_event(event)
        if error:
            return ReplyEventReservation(ReplyEventReservationStatus.REJECTED, None, error)
        with self._lock:
            existing = self._events_by_id.get(event.reply_event_id)
            if existing is not None:
                return ReplyEventReservation(ReplyEventReservationStatus.DUPLICATE, existing)
            self._events_by_id[event.reply_event_id] = event
            return ReplyEventReservation(ReplyEventReservationStatus.CREATED, event)

    def get(self, reply_event_id: str) -> ReplyEvent | None:
        with self._lock:
            return self._events_by_id.get(reply_event_id)


class ReplyTrackingService:
    """Create reply events only for a traceable C10.3 ``SENT`` execution."""

    def __init__(self, executions: SendExecutionRegistry, registry: ReplyEventRegistry | None = None) -> None:
        self._executions = executions
        self._registry = registry or InMemoryReplyEventRegistry()

    def track(
        self,
        lead_id: str,
        draft_id: str,
        send_attempt_id: str,
        thread_id: str,
        received_at: datetime,
        sender_reference: str,
        reply_status: ReplyStatus,
    ) -> ReplyEventReservation:
        error = _validate_tracking_input(
            lead_id,
            draft_id,
            send_attempt_id,
            thread_id,
            received_at,
            sender_reference,
            reply_status,
        )
        if error:
            return ReplyEventReservation(ReplyEventReservationStatus.REJECTED, None, error)
        execution = self._executions.find_by_send_attempt_id(send_attempt_id)
        if execution is None or execution.state is not SendExecutionState.SENT:
            return ReplyEventReservation(ReplyEventReservationStatus.REJECTED, None, "UNKNOWN_SENT_ATTEMPT")
        if execution.draft_id != draft_id or execution.send_request.lead_id != lead_id:
            return ReplyEventReservation(ReplyEventReservationStatus.REJECTED, None, "SEND_TRACE_MISMATCH")
        trace = self._executions.audit_trace(execution.send_request.send_request_id)
        if not trace:
            return ReplyEventReservation(ReplyEventReservationStatus.REJECTED, None, "MISSING_SEND_TRACE")
        event = ReplyEvent(
            reply_event_id=generate_reply_event_id(
                lead_id,
                draft_id,
                send_attempt_id,
                thread_id,
                received_at,
                sender_reference,
                reply_status,
            ),
            lead_id=lead_id.strip(),
            draft_id=draft_id.strip(),
            send_attempt_id=send_attempt_id.strip(),
            thread_id=thread_id.strip(),
            received_at=received_at,
            sender_reference=sender_reference.strip(),
            reply_status=reply_status,
            original_send_trace=trace,
        )
        return self._registry.record(event)


def generate_reply_event_id(
    lead_id: str,
    draft_id: str,
    send_attempt_id: str,
    thread_id: str,
    received_at: datetime,
    sender_reference: str,
    reply_status: ReplyStatus,
    event_version: str = REPLY_EVENT_VERSION,
) -> str:
    """Generate a canonical identity for duplicate-safe reply-event ingestion."""
    payload = {
        "event_version": event_version.strip(),
        "lead_id": lead_id.strip(),
        "draft_id": draft_id.strip(),
        "send_attempt_id": send_attempt_id.strip(),
        "thread_id": thread_id.strip(),
        "received_at": received_at.astimezone(timezone.utc).isoformat(),
        "sender_reference": sender_reference.strip(),
        "reply_status": reply_status.value,
    }
    encoded = dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def validate_reply_event(event: object) -> str | None:
    if not isinstance(event, ReplyEvent):
        return "INVALID_REPLY_EVENT"
    for name in ("reply_event_id", "lead_id", "draft_id", "send_attempt_id", "thread_id", "sender_reference", "event_version"):
        value = getattr(event, name)
        if not isinstance(value, str) or not value.strip():
            return f"INVALID_{name.upper()}"
    if not isinstance(event.received_at, datetime) or event.received_at.tzinfo is None or event.received_at.utcoffset() is None:
        return "INVALID_RECEIVED_AT"
    if not isinstance(event.reply_status, ReplyStatus):
        return "INVALID_REPLY_STATUS"
    if event.event_version != REPLY_EVENT_VERSION:
        return "UNSUPPORTED_EVENT_VERSION"
    expected_id = generate_reply_event_id(
        event.lead_id,
        event.draft_id,
        event.send_attempt_id,
        event.thread_id,
        event.received_at,
        event.sender_reference,
        event.reply_status,
        event.event_version,
    )
    if event.reply_event_id != expected_id:
        return "INVALID_REPLY_EVENT_ID"
    if not event.original_send_trace:
        return "MISSING_SEND_TRACE"
    return None


def _validate_tracking_input(
    lead_id: object,
    draft_id: object,
    send_attempt_id: object,
    thread_id: object,
    received_at: object,
    sender_reference: object,
    reply_status: object,
) -> str | None:
    for name, value in (
        ("lead_id", lead_id),
        ("draft_id", draft_id),
        ("send_attempt_id", send_attempt_id),
        ("thread_id", thread_id),
        ("sender_reference", sender_reference),
    ):
        if not isinstance(value, str) or not value.strip():
            return f"INVALID_{name.upper()}"
    if not isinstance(received_at, datetime) or received_at.tzinfo is None or received_at.utcoffset() is None:
        return "INVALID_RECEIVED_AT"
    if not isinstance(reply_status, ReplyStatus):
        return "INVALID_REPLY_STATUS"
    return None
