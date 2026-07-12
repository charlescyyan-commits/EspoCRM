"""Display-only Chitu email lifecycle synchronization for native CRM records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping, Protocol


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


class EmailLifecycleClient(Protocol):
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


class EmailLifecycleSyncService:
    """Sync only lifecycle summaries to existing Lead and Opportunity records."""

    def sync(
        self,
        client: EmailLifecycleClient,
        lead_id: str,
        update: EmailLifecycleUpdate,
        opportunity_id: str | None = None,
    ) -> EmailLifecycleSyncResult:
        if not lead_id:
            raise EmailLifecycleSyncError("lead_id is required")
        if opportunity_id == "":
            raise EmailLifecycleSyncError("opportunity_id must be omitted or non-empty")
        fields = update.fields()
        if set(fields) != _SYNCED_FIELDS:
            raise EmailLifecycleSyncError("email lifecycle sync body is not allowlisted")
        client.update_record("Lead", lead_id, fields)
        if opportunity_id:
            client.update_record("Opportunity", opportunity_id, fields)
        return EmailLifecycleSyncResult(
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            status=update.status,
            synced_fields=tuple(sorted(fields)),
        )
