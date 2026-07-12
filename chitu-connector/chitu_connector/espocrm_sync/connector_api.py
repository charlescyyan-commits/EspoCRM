"""Authenticated client for the EspoCRM Prospecting sync API."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from chitu_connector.espocrm_sync.contract import SyncContractPayload
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.models import SyncSource


class ConnectorApiError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ConnectorSyncResponse:
    success: bool
    created: bool
    updated: bool
    external_id: str
    crm_id: str
    eligibility: bool | None = None
    action: str | None = None


class ProspectingConnectorClient:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 15.0) -> None:
        if not api_key:
            raise ConnectorApiError("an API key is required")
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConnectorApiError("base URL must be an absolute HTTP(S) URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def sync_lead(self, payload: SyncContractPayload) -> ConnectorSyncResponse:
        return self._post("Prospecting/sync/lead", payload)

    def sync_evidence(self, payload: SyncContractPayload) -> ConnectorSyncResponse:
        return self._post("Prospecting/sync/evidence", payload)

    def sync_opportunity_proposal(self, payload: SyncContractPayload) -> ConnectorSyncResponse:
        return self._post("Prospecting/sync/opportunity-proposal", payload)

    def sync_source(self, source: SyncSource) -> ConnectorSyncResponse:
        return self.sync_lead(EspoCRMSyncMapper().build(source))

    def _post(self, path: str, payload: SyncContractPayload) -> ConnectorSyncResponse:
        body = json.dumps(payload.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/v1/{path}",
            data=body,
            headers={"Accept": "application/json", "Content-Type": "application/json", "X-Api-Key": self.api_key},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise ConnectorApiError(f"EspoCRM connector API returned HTTP {error.code}") from error
        except URLError as error:
            raise ConnectorApiError("EspoCRM connector API request failed") from error
        except json.JSONDecodeError as error:
            raise ConnectorApiError("EspoCRM connector API returned invalid JSON") from error

        return self._response(data)

    @staticmethod
    def _response(data: Any) -> ConnectorSyncResponse:
        if not isinstance(data, Mapping):
            raise ConnectorApiError("EspoCRM connector API response is not an object")
        required = ("success", "created", "updated", "external_id", "crm_id")
        if any(name not in data for name in required):
            raise ConnectorApiError("EspoCRM connector API response is missing required fields")
        if not isinstance(data["success"], bool) or not isinstance(data["created"], bool) or not isinstance(data["updated"], bool):
            raise ConnectorApiError("EspoCRM connector API response has invalid status fields")
        if not isinstance(data["external_id"], str) or not isinstance(data["crm_id"], str):
            raise ConnectorApiError("EspoCRM connector API response has invalid identifiers")

        eligibility = data.get("eligibility")
        action = data.get("action")
        if eligibility is not None and not isinstance(eligibility, bool):
            raise ConnectorApiError("EspoCRM connector API response has invalid eligibility")
        if action is not None and not isinstance(action, str):
            raise ConnectorApiError("EspoCRM connector API response has invalid action")

        return ConnectorSyncResponse(
            success=data["success"],
            created=data["created"],
            updated=data["updated"],
            external_id=data["external_id"],
            crm_id=data["crm_id"],
            eligibility=eligibility,
            action=action,
        )
