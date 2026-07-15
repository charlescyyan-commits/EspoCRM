"""Connector-side compatibility guard for the frozen C14.3 email projection.

The CRM projection service is PHP and cannot be imported by connector Python.
This module is the one connector-side representation of its frozen status-rank
contract.  C14.4A tests lock these values to the PHP ``STATUS_RANK`` entries.
It is deliberately a read-before-write guard, not a CRM projection service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


C14_3_EMAIL_STATUS_RANK: Mapping[str, int] = MappingProxyType({
    "NONE": 0,
    "DRAFT_READY": 10,
    "DRAFT_PENDING_APPROVAL": 20,
    "APPROVED": 30,
    "REJECTED": 30,
    "PENDING": 40,
    "READY_TO_SEND": 50,
    "SENT": 60,
    "FAILED": 60,
    "CANCELLED": 60,
    "REPLIED": 70,
    "BOUNCED": 70,
})
C14_3_TERMINAL_EMAIL_STATUSES = frozenset({"SENT", "FAILED", "CANCELLED", "REPLIED", "BOUNCED"})


@dataclass(frozen=True, slots=True)
class EmailProjectionGuardDecision:
    allowed: bool
    reason_code: str | None = None


def guard_email_summary_update(
    current: Mapping[str, Any],
    *,
    proposed_status: str,
    proposed_occurred_at: str | None,
) -> EmailProjectionGuardDecision:
    """Reject a legacy update that could regress the C14.3 projected state."""

    current_status = _status(current.get("peEmailStatus"))
    next_status = _status(proposed_status)
    if next_status is None or next_status not in C14_3_EMAIL_STATUS_RANK:
        return EmailProjectionGuardDecision(False, "INVALID_PROPOSED_EMAIL_STATUS")
    if current_status is not None and current_status not in C14_3_EMAIL_STATUS_RANK:
        return EmailProjectionGuardDecision(False, "UNKNOWN_CURRENT_EMAIL_STATUS")

    current_timestamp_value = current.get("peLastEmailDate")
    current_timestamp = _timestamp(current_timestamp_value)
    next_timestamp = _timestamp(proposed_occurred_at)
    if proposed_occurred_at is not None and next_timestamp is None:
        return EmailProjectionGuardDecision(False, "INVALID_PROPOSED_EMAIL_TIMESTAMP")
    if current_timestamp_value is not None and not (
        isinstance(current_timestamp_value, str) and not current_timestamp_value.strip()
    ) and current_timestamp is None:
        return EmailProjectionGuardDecision(False, "INVALID_CURRENT_EMAIL_TIMESTAMP")
    if current_timestamp is not None and next_timestamp is not None and next_timestamp < current_timestamp:
        return EmailProjectionGuardDecision(False, "OLDER_EMAIL_TIMESTAMP")

    if current_status is None:
        return EmailProjectionGuardDecision(True)
    current_rank = C14_3_EMAIL_STATUS_RANK[current_status]
    next_rank = C14_3_EMAIL_STATUS_RANK[next_status]
    if current_status in C14_3_TERMINAL_EMAIL_STATUSES and next_rank < current_rank:
        return EmailProjectionGuardDecision(False, "TERMINAL_EMAIL_STATUS_PROTECTED")
    if next_rank < current_rank:
        return EmailProjectionGuardDecision(False, "LOWER_EMAIL_STATUS_RANK")
    return EmailProjectionGuardDecision(True)


def exclude_empty_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Never issue a legacy write that would clear a text summary field."""

    return {
        field_name: value
        for field_name, value in fields.items()
        if value is not None and (not isinstance(value, str) or bool(value.strip()))
    }


def _status(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().upper()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed
