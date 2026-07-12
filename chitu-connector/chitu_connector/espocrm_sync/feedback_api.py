"""Authenticated client for CRM feedback ingestion without altering Sync Contract V1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_FEEDBACK_TYPES = frozenset({
    "CONTACT_ATTEMPT", "CUSTOMER_REPLY", "INTERESTED", "NOT_INTERESTED", "NO_RESPONSE", "WON", "LOST",
})
_OUTCOMES = frozenset({"POSITIVE", "NEGATIVE", "NEUTRAL"})


class FeedbackApiError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FeedbackSyncPayload:
    lead_id: str
    feedback_type: str
    outcome: str
    timestamp: datetime
    feedback_id: str | None = None
    external_lead_id: str | None = None
    product: str | None = None
    product_result: str | None = None
    stage: str | None = None
    reason: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.lead_id:
            raise FeedbackApiError("lead_id is required")
        if self.feedback_type not in _FEEDBACK_TYPES:
            raise FeedbackApiError("unsupported feedback_type")
        if self.outcome not in _OUTCOMES:
            raise FeedbackApiError("unsupported outcome")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise FeedbackApiError("timestamp must include a timezone")
        for value in (
            self.feedback_id,
            self.external_lead_id,
            self.product,
            self.product_result,
            self.stage,
            self.reason,
            self.note,
        ):
            if value is not None and not isinstance(value, str):
                raise FeedbackApiError("optional feedback fields must be strings")

    def to_dict(self) -> dict[str, str]:
        values = {
            "lead_id": self.lead_id,
            "feedback_type": self.feedback_type,
            "outcome": self.outcome,
            "timestamp": self.timestamp.isoformat(),
            "feedback_id": self.feedback_id,
            "external_lead_id": self.external_lead_id,
            "product": self.product,
            "product_result": self.product_result,
            "stage": self.stage,
            "reason": self.reason,
            "note": self.note,
        }
        return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True, slots=True)
class FeedbackSyncResponse:
    success: bool
    external_id: str
    accepted: bool
    created: bool
    feedback_id: str
    learning_signal_id: str


class FeedbackConnectorClient:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 15.0) -> None:
        if not api_key:
            raise FeedbackApiError("an API key is required")
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise FeedbackApiError("base URL must be an absolute HTTP(S) URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def sync_feedback(self, payload: FeedbackSyncPayload) -> FeedbackSyncResponse:
        body = json.dumps(payload.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/v1/Prospecting/feedback/sync",
            data=body,
            headers={"Accept": "application/json", "Content-Type": "application/json", "X-Api-Key": self.api_key},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise FeedbackApiError(f"EspoCRM feedback API returned HTTP {error.code}") from error
        except URLError as error:
            raise FeedbackApiError("EspoCRM feedback API request failed") from error
        except json.JSONDecodeError as error:
            raise FeedbackApiError("EspoCRM feedback API returned invalid JSON") from error

        return self._response(data)

    @staticmethod
    def _response(data: Any) -> FeedbackSyncResponse:
        if not isinstance(data, Mapping):
            raise FeedbackApiError("EspoCRM feedback API response is not an object")
        required = ("success", "external_id", "accepted", "created", "feedback_id", "learning_signal_id")
        if any(name not in data for name in required):
            raise FeedbackApiError("EspoCRM feedback API response is missing required fields")
        if not isinstance(data["success"], bool) or not isinstance(data["accepted"], bool) or not isinstance(data["created"], bool):
            raise FeedbackApiError("EspoCRM feedback API response has invalid status fields")
        if any(not isinstance(data[name], str) for name in ("external_id", "feedback_id", "learning_signal_id")):
            raise FeedbackApiError("EspoCRM feedback API response has invalid identifiers")
        return FeedbackSyncResponse(
            success=data["success"],
            external_id=data["external_id"],
            accepted=data["accepted"],
            created=data["created"],
            feedback_id=data["feedback_id"],
            learning_signal_id=data["learning_signal_id"],
        )
