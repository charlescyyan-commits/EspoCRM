"""Authenticated export of CRM feedback/learning signals for Chitu consumption."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class FeedbackSignalExportError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FeedbackSignalPayload:
    lead_id: str
    feedback_type: str
    outcome: str
    timestamp: datetime
    product: str | None = None
    campaign: str | None = None
    feedback_id: str | None = None
    learning_signal_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        values = {
            "lead_id": self.lead_id,
            "feedback_type": self.feedback_type,
            "outcome": self.outcome,
            "product": self.product,
            "campaign": self.campaign,
            "timestamp": self.timestamp.isoformat(),
            "feedback_id": self.feedback_id,
            "learning_signal_id": self.learning_signal_id,
        }
        return {key: value for key, value in values.items() if value is not None}


class FeedbackSignalExportClient:
    """Pull LearningSignal records from EspoCRM and map to Chitu feedback-signal payloads."""

    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 15.0) -> None:
        if not api_key:
            raise FeedbackSignalExportError("an API key is required")
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise FeedbackSignalExportError("base URL must be an absolute HTTP(S) URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def export_for_lead(self, lead_id: str) -> list[FeedbackSignalPayload]:
        if not lead_id:
            raise FeedbackSignalExportError("lead_id is required")
        query = urlencode({
            "where": json.dumps([{"type": "equals", "attribute": "leadId", "value": lead_id}]),
            "maxSize": 200,
            "orderBy": "createdAt",
            "order": "desc",
        })
        data = self._get(f"/api/v1/LearningSignal?{query}")
        rows = data.get("list") if isinstance(data, Mapping) else None
        if not isinstance(rows, list):
            raise FeedbackSignalExportError("LearningSignal list response is invalid")
        return [self._map_signal(row) for row in rows if isinstance(row, Mapping)]

    def export_signal(self, learning_signal_id: str) -> FeedbackSignalPayload:
        if not learning_signal_id:
            raise FeedbackSignalExportError("learning_signal_id is required")
        data = self._get(f"/api/v1/LearningSignal/{learning_signal_id}")
        if not isinstance(data, Mapping):
            raise FeedbackSignalExportError("LearningSignal response is invalid")
        return self._map_signal(data)

    def _get(self, path: str) -> Any:
        request = Request(
            f"{self.base_url}{path}",
            headers={"Accept": "application/json", "X-Api-Key": self.api_key},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise FeedbackSignalExportError(
                f"EspoCRM learning-signal export returned HTTP {error.code}"
            ) from error
        except URLError as error:
            raise FeedbackSignalExportError("EspoCRM learning-signal export request failed") from error
        except json.JSONDecodeError as error:
            raise FeedbackSignalExportError("EspoCRM learning-signal export returned invalid JSON") from error

    @staticmethod
    def _map_signal(row: Mapping[str, Any]) -> FeedbackSignalPayload:
        lead_id = row.get("leadId")
        signal_type = row.get("signalType")
        outcome = row.get("actualOutcome")
        created_at = row.get("createdAt")
        if not isinstance(lead_id, str) or not lead_id:
            raise FeedbackSignalExportError("learning signal missing lead_id")
        if not isinstance(signal_type, str) or not signal_type:
            raise FeedbackSignalExportError("learning signal missing feedback_type")
        if not isinstance(outcome, str) or not outcome:
            raise FeedbackSignalExportError("learning signal missing outcome")
        timestamp = FeedbackSignalExportClient._parse_time(created_at)
        product = row.get("product") if isinstance(row.get("product"), str) else None
        campaign = row.get("campaign") if isinstance(row.get("campaign"), str) else None
        feedback_id = row.get("salesFeedbackId") if isinstance(row.get("salesFeedbackId"), str) else None
        signal_id = row.get("id") if isinstance(row.get("id"), str) else None
        return FeedbackSignalPayload(
            lead_id=lead_id,
            feedback_type=signal_type,
            outcome=outcome,
            timestamp=timestamp,
            product=product,
            campaign=campaign,
            feedback_id=feedback_id,
            learning_signal_id=signal_id,
        )

    @staticmethod
    def _parse_time(value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise FeedbackSignalExportError("timestamp must include a timezone")
            return value
        if not isinstance(value, str) or not value:
            raise FeedbackSignalExportError("learning signal missing timestamp")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError, IndexError) as error:
                raise FeedbackSignalExportError("learning signal timestamp is invalid") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise FeedbackSignalExportError("timestamp must include a timezone")
        return parsed
