"""Display-only Chitu email lifecycle synchronization for native CRM records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import logging
from typing import Any, Mapping, Protocol
import warnings

from chitu_connector.espocrm_sync.email_projection_guard import (
    exclude_empty_fields,
    guard_email_summary_update,
)


class EmailLifecycleSyncError(ValueError):
    pass


class EmailLifecycleStatus(StrEnum):
    NONE = "NONE"
    DRAFT_READY = "DRAFT_READY"
    APPROVED = "APPROVED"
    SENT = "SENT"
    REPLIED = "REPLIED"
    BOUNCED = "BOUNCED"


_SYNCED_FIELDS = frozenset({
    "peEmailStatus",
    "peLastEmailDate",
    "peEmailCampaignName",
    "peEmailReplyStatus",
})
_EMAIL_SUMMARY_SELECT = "peEmailStatus,peLastEmailDate,peEmailCampaignName,peEmailReplyStatus"
_LOGGER = logging.getLogger(__name__)


class EmailLifecycleClient(Protocol):
    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]: ...

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class EmailLifecycleUpdate:
    status: EmailLifecycleStatus
    occurred_at: datetime
    campaign_reference: str
    reply_state: str

    def fields(self) -> dict[str, str]:
        campaign_reference = self.campaign_reference.strip()
        reply_state = self.reply_state.strip()
        if not campaign_reference or len(campaign_reference) > 255:
            raise EmailLifecycleSyncError("campaign_reference must contain 1 to 255 characters")
        if not reply_state or len(reply_state) > 64:
            raise EmailLifecycleSyncError("reply_state must contain 1 to 64 characters")
        occurred_at = self.occurred_at
        if occurred_at.tzinfo is None:
            raise EmailLifecycleSyncError("occurred_at must include a timezone")
        return {
            "peEmailStatus": self.status.value,
            "peLastEmailDate": occurred_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "peEmailCampaignName": campaign_reference,
            "peEmailReplyStatus": reply_state,
        }


@dataclass(frozen=True, slots=True)
class EmailLifecycleSyncResult:
    lead_id: str
    opportunity_id: str | None
    status: EmailLifecycleStatus
    synced_fields: tuple[str, ...]
    reason_code: str | None = None


class EmailLifecycleSyncService:
    """Deprecated W-CON-01 compatibility writer; prefer the C14.3 CRM bridge."""

    def sync(
        self,
        client: EmailLifecycleClient,
        lead_id: str,
        update: EmailLifecycleUpdate,
        opportunity_id: str | None = None,
    ) -> EmailLifecycleSyncResult:
        warnings.warn(
            "EmailLifecycleSyncService.sync() is deprecated; use the C14.3 CRM SendExecution bridge path for email lifecycle execution.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not lead_id:
            raise EmailLifecycleSyncError("lead_id is required")
        if opportunity_id == "":
            raise EmailLifecycleSyncError("opportunity_id must be omitted or non-empty")
        raw_fields = update.fields()
        if set(raw_fields) != _SYNCED_FIELDS:
            raise EmailLifecycleSyncError("email lifecycle sync body is not allowlisted")
        fields = exclude_empty_fields(raw_fields)
        if "peEmailStatus" not in fields or "peLastEmailDate" not in fields:
            return self._skipped(lead_id, opportunity_id, update.status, "EMPTY_REQUIRED_EMAIL_FIELD")

        targets = (("Lead", lead_id),) + (("Opportunity", opportunity_id),) if opportunity_id else (("Lead", lead_id),)
        for entity_type, record_id in targets:
            try:
                current = client.read_record(entity_type, record_id, _EMAIL_SUMMARY_SELECT)
            except Exception:
                return self._skipped(lead_id, opportunity_id, update.status, "CURRENT_EMAIL_STATE_UNAVAILABLE")
            decision = guard_email_summary_update(
                current,
                proposed_status=str(fields["peEmailStatus"]),
                proposed_occurred_at=str(fields["peLastEmailDate"]),
            )
            if not decision.allowed:
                return self._skipped(lead_id, opportunity_id, update.status, decision.reason_code or "EMAIL_STATE_CONFLICT")

        client.update_record("Lead", lead_id, fields)
        if opportunity_id:
            client.update_record("Opportunity", opportunity_id, fields)
        return EmailLifecycleSyncResult(
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            status=update.status,
            synced_fields=tuple(sorted(fields)),
        )

    @staticmethod
    def _skipped(
        lead_id: str,
        opportunity_id: str | None,
        status: EmailLifecycleStatus,
        reason_code: str,
    ) -> EmailLifecycleSyncResult:
        _LOGGER.warning("C14.4A W-CON-01 guarded compatibility writer skipped: %s", reason_code)
        return EmailLifecycleSyncResult(
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            status=status,
            synced_fields=(),
            reason_code=reason_code,
        )
