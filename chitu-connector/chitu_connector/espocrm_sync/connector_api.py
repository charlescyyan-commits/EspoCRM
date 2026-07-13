"""Authenticated client for the EspoCRM Prospecting sync API."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from chitu_connector.espocrm_sync.contract import SyncContractPayload, validate_sync_contract
from chitu_connector.espocrm_sync.gate import evaluate_sync_gate
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


@dataclass(frozen=True, slots=True)
class ConnectorSyncStep:
    completed: bool
    reason: str | None = None
    response: ConnectorSyncResponse | None = None


@dataclass(frozen=True, slots=True)
class ConnectorSyncResult:
    success: bool
    validation: ConnectorSyncStep
    gate: ConnectorSyncStep
    lead: ConnectorSyncStep
    evidence: ConnectorSyncStep
    proposal: ConnectorSyncStep


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

    def sync_source(self, source: SyncSource) -> ConnectorSyncResult:
        payload = EspoCRMSyncMapper().build(source)
        errors = validate_sync_contract(payload.to_dict())
        if errors:
            return self._rejected_result(errors[0], validation=True)

        gate = evaluate_sync_gate(source, payload)
        if not gate.accepted:
            return self._rejected_result(gate.reason_code)

        lead = self.sync_lead(payload)
        if not lead.success:
            return self._failed_result(lead=lead)
        evidence = self.sync_evidence(payload)
        if not evidence.success:
            return self._failed_result(lead=lead, evidence=evidence)
        proposal = self.sync_opportunity_proposal(payload)
        if not proposal.success:
            return self._failed_result(lead=lead, evidence=evidence, proposal=proposal)

        return ConnectorSyncResult(
            success=lead.success and evidence.success and proposal.success,
            validation=ConnectorSyncStep(completed=True),
            gate=ConnectorSyncStep(completed=True),
            lead=ConnectorSyncStep(completed=True, response=lead),
            evidence=ConnectorSyncStep(completed=True, response=evidence),
            proposal=ConnectorSyncStep(completed=True, response=proposal),
        )

    @staticmethod
    def _rejected_result(reason: str, *, validation: bool = False) -> ConnectorSyncResult:
        rejected = ConnectorSyncStep(completed=False, reason=reason)
        not_run = ConnectorSyncStep(completed=False)
        return ConnectorSyncResult(
            success=False,
            validation=rejected if validation else ConnectorSyncStep(completed=True),
            gate=not_run if validation else rejected,
            lead=not_run,
            evidence=not_run,
            proposal=not_run,
        )

    @staticmethod
    def _failed_result(
        *,
        lead: ConnectorSyncResponse | None = None,
        evidence: ConnectorSyncResponse | None = None,
        proposal: ConnectorSyncResponse | None = None,
    ) -> ConnectorSyncResult:
        return ConnectorSyncResult(
            success=False,
            validation=ConnectorSyncStep(completed=True),
            gate=ConnectorSyncStep(completed=True),
            lead=ConnectorSyncStep(completed=lead is not None, response=lead),
            evidence=ConnectorSyncStep(completed=evidence is not None, response=evidence),
            proposal=ConnectorSyncStep(completed=proposal is not None, response=proposal),
        )

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
