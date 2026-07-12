"""Authenticated Brevo email-event client for EspoCRM status sync (no send path)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_EVENT_TYPES = frozenset({"SENT", "DELIVERED", "OPENED", "CLICKED", "REPLIED", "BOUNCED"})
_BREVO_ALIASES = {
    "email_sent": "SENT",
    "sent": "SENT",
    "email_delivered": "DELIVERED",
    "delivered": "DELIVERED",
    "email_opened": "OPENED",
    "opened": "OPENED",
    "unique_opened": "OPENED",
    "email_clicked": "CLICKED",
    "click": "CLICKED",
    "email_replied": "REPLIED",
    "reply": "REPLIED",
    "email_bounced": "BOUNCED",
    "hard_bounce": "BOUNCED",
    "soft_bounce": "BOUNCED",
    "bounce": "BOUNCED",
}
_SOURCES = frozenset({"BREVO", "CONNECTOR_SYNC", "MANUAL"})


class BrevoApiError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BrevoEmailEventPayload:
    lead_id: str
    message_id: str
    event_type: str
    timestamp: datetime
    campaign: str | None = None
    external_lead_id: str | None = None
    reply_status: str | None = None
    source: str = "BREVO"

    def __post_init__(self) -> None:
        if not self.lead_id:
            raise BrevoApiError("lead_id is required")
        if not self.message_id:
            raise BrevoApiError("message_id is required")
        normalized = _BREVO_ALIASES.get(self.event_type.lower(), self.event_type)
        if normalized not in _EVENT_TYPES:
            raise BrevoApiError("unsupported event_type")
        object.__setattr__(self, "event_type", normalized)
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise BrevoApiError("timestamp must include a timezone")
        if self.source not in _SOURCES:
            raise BrevoApiError("unsupported source")
        for value in (self.campaign, self.external_lead_id, self.reply_status):
            if value is not None and not isinstance(value, str):
                raise BrevoApiError("optional Brevo fields must be strings")

    def to_dict(self) -> dict[str, str]:
        values = {
            "lead_id": self.lead_id,
            "message_id": self.message_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "campaign": self.campaign,
            "external_lead_id": self.external_lead_id,
            "reply_status": self.reply_status,
            "source": self.source,
        }
        return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True, slots=True)
class BrevoEmailEventResponse:
    success: bool
    accepted: bool
    created: bool
    duplicate: bool
    external_message_id: str
    event_type: str
    email_event_id: str
    lead_id: str


class BrevoConnectorClient:
    """Posts normalized Brevo execution events to EspoCRM. Does not send email."""

    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 15.0) -> None:
        if not api_key:
            raise BrevoApiError("an API key is required")
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BrevoApiError("base URL must be an absolute HTTP(S) URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def sync_email_event(self, payload: BrevoEmailEventPayload) -> BrevoEmailEventResponse:
        body = json.dumps(payload.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/v1/Prospecting/brevo/email-event",
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise BrevoApiError(f"EspoCRM Brevo email-event API returned HTTP {error.code}") from error
        except URLError as error:
            raise BrevoApiError("EspoCRM Brevo email-event API request failed") from error
        except json.JSONDecodeError as error:
            raise BrevoApiError("EspoCRM Brevo email-event API returned invalid JSON") from error
        return self._response(data)

    @staticmethod
    def _response(data: Any) -> BrevoEmailEventResponse:
        if not isinstance(data, Mapping):
            raise BrevoApiError("EspoCRM Brevo email-event API response is not an object")
        required = (
            "success",
            "accepted",
            "created",
            "duplicate",
            "external_message_id",
            "event_type",
            "email_event_id",
            "lead_id",
        )
        if any(name not in data for name in required):
            raise BrevoApiError("EspoCRM Brevo email-event API response is missing required fields")
        for name in ("success", "accepted", "created", "duplicate"):
            if not isinstance(data[name], bool):
                raise BrevoApiError("EspoCRM Brevo email-event API response has invalid status fields")
        for name in ("external_message_id", "event_type", "email_event_id", "lead_id"):
            if not isinstance(data[name], str):
                raise BrevoApiError("EspoCRM Brevo email-event API response has invalid identifiers")
        return BrevoEmailEventResponse(
            success=data["success"],
            accepted=data["accepted"],
            created=data["created"],
            duplicate=data["duplicate"],
            external_message_id=data["external_message_id"],
            event_type=data["event_type"],
            email_event_id=data["email_event_id"],
            lead_id=data["lead_id"],
        )
