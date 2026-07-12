"""Strict localhost-only EspoCRM client for one synthetic integration test."""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import json
import os
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from chitu_connector.espocrm_sync.contract import SyncContractPayload
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper


LOCAL_TEST_URL = "http://localhost:8080"
SYNTHETIC_MARKER = "[CHITU_SYNTHETIC_TEST]"
SYNTHETIC_LEAD_NAME = "Synthetic 3D Dealer Test GmbH"
_LEAD_FIELDS = {
    "name", "website", "description", "peOpportunityScoreV4", "peScoreTier", "peConfidence",
    "peEvidenceCoverage", "peBestFirstProduct", "peQualificationStatus", "peEngineVersion", "peScoreRulesVersion",
    "peSyncStatus", "peResearchStatus", "peSourceSystem", "peCandidateId", "peLastSyncAt",
    "peResearchSummary", "peKeyEvidence", "peRecommendedApproach", "addressCountry",
}
_RESEARCH_EVIDENCE_FIELDS = {
    "name", "peEvidenceId", "peClaim", "peClaimType", "peSourceUrl", "peEvidenceText", "peConfidence",
    "peCapturedAt", "peSchemaVersion", "peSnapshotHash",
}
_LIFECYCLE_ENTITY_TYPES = {"Lead", "Account", "Contact", "Opportunity"}


class LocalEspoCRMError(RuntimeError):
    pass


class EnvironmentSafetyError(LocalEspoCRMError):
    pass


class RealSyncStatus(StrEnum):
    CREATED = "CREATED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class PreflightResult:
    lead_fields: tuple[str, ...]
    evidence_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RealSyncResult:
    status: RealSyncStatus
    lead_id: str
    evidence_ids: tuple[str, ...]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


class LocalEspoCRMClient:
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        if not api_key and (not username or not password):
            raise EnvironmentSafetyError("local test authentication requires an API key or username/password")
        self.base_url = self._validate_base_url(base_url)
        self.username = username
        self.password = password
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._token: str | None = None
        self._basic_authorization: str | None = None
        self._opener = build_opener(_NoRedirect())

    @classmethod
    def from_environment(cls) -> "LocalEspoCRMClient":
        if os.environ.get("ESPOCRM_TEST_ENV", "").lower() != "true":
            raise EnvironmentSafetyError("ESPOCRM_TEST_ENV must be true")
        base_url = os.environ.get("ESPOCRM_TEST_URL", LOCAL_TEST_URL)
        api_key = os.environ.get("ESPOCRM_TEST_API_KEY")
        username = os.environ.get("ESPOCRM_TEST_USERNAME") or os.environ.get("ESPOCRM_ADMIN_USERNAME")
        password = os.environ.get("ESPOCRM_TEST_PASSWORD") or os.environ.get("ESPOCRM_ADMIN_PASSWORD")
        if not api_key and (not username or not password):
            raise EnvironmentSafetyError("missing local test credentials in environment")
        return cls(base_url, username, password, api_key)

    def authenticate(self) -> None:
        if self.api_key:
            self._request("GET", "App/user")
            return
        if not self.username or not self.password:
            raise EnvironmentSafetyError("username/password are required for Basic authentication")
        encoded = b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        try:
            response = self._request("GET", "App/user", headers={"Espo-Authorization": encoded})
        except LocalEspoCRMError:
            self._request("GET", "App/user", headers={"Authorization": f"Basic {encoded}"})
            self._basic_authorization = f"Basic {encoded}"
            return
        token = response.get("token") if isinstance(response, Mapping) else None
        if not isinstance(token, str) or not token:
            raise LocalEspoCRMError("authentication response did not contain a token")
        self._token = token

    def preflight(self) -> PreflightResult:
        self._require_authentication()
        lead_fields = self._metadata("entityDefs.Lead.fields")
        evidence_definition = self._metadata("entityDefs.ResearchEvidence")
        if not isinstance(lead_fields, Mapping) or not isinstance(evidence_definition, Mapping):
            raise EnvironmentSafetyError("required local EspoCRM extension metadata is unavailable")
        evidence_fields = evidence_definition.get("fields")
        lead_links = self._metadata("entityDefs.Lead.links")
        missing_lead = _LEAD_FIELDS - set(lead_fields)
        missing_evidence = _RESEARCH_EVIDENCE_FIELDS - set(evidence_fields or {})
        if missing_lead or missing_evidence or not isinstance(lead_links, Mapping) or "researchEvidences" not in lead_links:
            raise EnvironmentSafetyError("local EspoCRM extension schema does not match the approved skeleton")
        return PreflightResult(tuple(sorted(lead_fields)), tuple(sorted(evidence_fields)))

    def find_synthetic_lead(self) -> Mapping[str, Any] | None:
        response = self._request("GET", "Lead", query={
            "maxSize": "5", "select": "id,name,description",
            "where[0][type]": "equals", "where[0][attribute]": "name", "where[0][value]": SYNTHETIC_LEAD_NAME,
        })
        records = response.get("list", ()) if isinstance(response, Mapping) else ()
        for record in records:
            if isinstance(record, Mapping) and SYNTHETIC_MARKER in str(record.get("description", "")):
                return record
        return None

    def list_synthetic_evidence_ids(self, lead_id: str) -> tuple[str, ...]:
        response = self._request("GET", f"Lead/{lead_id}/researchEvidences", query={"maxSize": "50", "select": "id"})
        records = response.get("list", ()) if isinstance(response, Mapping) else ()
        return tuple(str(item["id"]) for item in records if isinstance(item, Mapping) and item.get("id"))

    def sync_payload(self, payload: SyncContractPayload) -> RealSyncResult:
        existing = self.find_synthetic_lead()
        if existing:
            return RealSyncResult(RealSyncStatus.DUPLICATE, str(existing["id"]), self.list_synthetic_evidence_ids(str(existing["id"])))
        lead_id: str | None = None
        evidence_ids: list[str] = []
        try:
            lead = self._request("POST", "Lead", body=self._lead_body(payload))
            lead_id = _record_id(lead, "Lead")
            for evidence in payload.to_dict()["evidence"]:
                created = self._request("POST", "ResearchEvidence", body=self._evidence_body(evidence, payload))
                evidence_id = _record_id(created, "ResearchEvidence")
                evidence_ids.append(evidence_id)
                self._request("POST", f"Lead/{lead_id}/researchEvidences", body={"id": evidence_id})
            return RealSyncResult(RealSyncStatus.CREATED, lead_id, tuple(evidence_ids))
        except Exception:
            if lead_id:
                self.rollback(lead_id, tuple(evidence_ids))
            raise

    def verify(self, result: RealSyncResult, payload: SyncContractPayload) -> None:
        data = payload.to_dict()
        lead = self._request("GET", f"Lead/{result.lead_id}", query={"select": "name,website,peOpportunityScoreV4,peScoreTier,peConfidence,peEvidenceCoverage,peQualificationStatus,peEngineVersion,peScoreRulesVersion,description"})
        expected = self._lead_body(payload)
        for field in _LEAD_FIELDS:
            if field != "description" and lead.get(field) != expected.get(field):
                raise LocalEspoCRMError(f"Lead field verification failed: {field}")
        if SYNTHETIC_MARKER not in str(lead.get("description", "")):
            raise LocalEspoCRMError("synthetic Lead marker is missing")
        if not result.evidence_ids:
            raise LocalEspoCRMError("no synthetic ResearchEvidence was created")
        for evidence_id, expected_item in zip(result.evidence_ids, data["evidence"], strict=True):
            evidence = self._request("GET", f"ResearchEvidence/{evidence_id}", query={"select": "peClaim,peSourceUrl,peEvidenceText,peConfidence,peSchemaVersion"})
            if evidence.get("peClaim") != expected_item["claim"] or evidence.get("peSchemaVersion") != expected_item["schema_version"]:
                raise LocalEspoCRMError("ResearchEvidence verification failed")
        linked_ids = set(self.list_synthetic_evidence_ids(result.lead_id))
        if not set(result.evidence_ids).issubset(linked_ids):
            raise LocalEspoCRMError("Lead to ResearchEvidence relationship verification failed")

    def rollback(self, lead_id: str, evidence_ids: tuple[str, ...] = ()) -> None:
        ids = evidence_ids or self.list_synthetic_evidence_ids(lead_id)
        for evidence_id in ids:
            self._request("DELETE", f"ResearchEvidence/{evidence_id}")
        self._request("DELETE", f"Lead/{lead_id}")

    def verify_rollback(self) -> None:
        if self.find_synthetic_lead() is not None:
            raise LocalEspoCRMError("synthetic Lead remains after rollback")

    def search_records(
        self,
        entity_type: str,
        attribute: str,
        value: str,
        select: str,
        max_size: int = 2,
    ) -> tuple[Mapping[str, Any], ...]:
        self._require_lifecycle_entity_type(entity_type)
        response = self._request("GET", entity_type, query={
            "maxSize": str(max_size),
            "select": select,
            "where[0][type]": "equals",
            "where[0][attribute]": attribute,
            "where[0][value]": value,
        })
        records = response.get("list", ()) if isinstance(response, Mapping) else ()
        return tuple(item for item in records if isinstance(item, Mapping))

    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]:
        self._require_lifecycle_entity_type(entity_type)
        value = self._request("GET", f"{entity_type}/{record_id}", query={"select": select})
        if not isinstance(value, Mapping):
            raise LocalEspoCRMError(f"{entity_type} read response was not an object")
        return value

    def create_record(self, entity_type: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self._require_lifecycle_entity_type(entity_type)
        value = self._request("POST", entity_type, body=body)
        if not isinstance(value, Mapping):
            raise LocalEspoCRMError(f"{entity_type} create response was not an object")
        return value

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self._require_lifecycle_entity_type(entity_type)
        value = self._request("PUT", f"{entity_type}/{record_id}", body=body)
        if not isinstance(value, Mapping):
            raise LocalEspoCRMError(f"{entity_type} update response was not an object")
        return value

    def delete_record(self, entity_type: str, record_id: str) -> None:
        self._require_lifecycle_entity_type(entity_type)
        self._request("DELETE", f"{entity_type}/{record_id}")

    def convert_lead(self, lead_id: str, records: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
        value = self._request("POST", "Lead/action/convert", body={"id": lead_id, "records": records})
        if not isinstance(value, Mapping):
            raise LocalEspoCRMError("Lead conversion response was not an object")
        return value

    def _lead_body(self, payload: SyncContractPayload) -> dict[str, Any]:
        fields = EspoCRMSyncMapper.lead_fields(payload)
        body = {name: value for name, value in fields.items() if name in _LEAD_FIELDS}
        body["lastName"] = body["name"]
        body["description"] = "\n".join((
            SYNTHETIC_MARKER, "is_test=true", "data_type=synthetic",
            f"sync_key={payload.to_dict()['sync']['idempotency_key']}",
        ))
        return body

    @staticmethod
    def _evidence_body(item: Mapping[str, Any], payload: SyncContractPayload) -> dict[str, Any]:
        captured_at = datetime.fromisoformat(str(item["captured_at"]).replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "name": f"Synthetic evidence {item['evidence_id']}", "peEvidenceId": item["evidence_id"],
            "peClaim": item["claim"], "peClaimType": item["claim_type"], "peSourceUrl": item["source_url"],
            "peEvidenceText": item["evidence_text"], "peConfidence": item["confidence"], "peCapturedAt": captured_at,
            "peSchemaVersion": item["schema_version"], "peSnapshotHash": payload.to_dict()["provenance"]["evidence_snapshot_hash"],
        }

    def _metadata(self, key: str) -> Any:
        return self._request("GET", "Metadata", query={"key": key})

    def _request(self, method: str, path: str, body: Mapping[str, Any] | None = None, query: Mapping[str, str] | None = None, headers: Mapping[str, str] | None = None) -> Any:
        if path.startswith(("http://", "https://")) or path.startswith("/"):
            raise EnvironmentSafetyError("absolute API paths are forbidden")
        url = f"{self.base_url}/api/v1/{path}"
        if query:
            url = f"{url}?{urlencode(query, safe='[]')}"
        request_headers = {"Accept": "application/json"}
        if self.api_key:
            request_headers["X-Api-Key"] = self.api_key
        elif self._token:
            token = b64encode(f"{self.username}:{self._token}".encode("utf-8")).decode("ascii")
            request_headers["Espo-Authorization"] = token
        elif self._basic_authorization:
            request_headers["Authorization"] = self._basic_authorization
        if headers:
            request_headers.update(headers)
        data = None
        if body is not None:
            request_headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(url, data=data, headers=request_headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            raise LocalEspoCRMError(f"EspoCRM HTTP error {error.code}") from error
        except URLError as error:
            raise LocalEspoCRMError("local EspoCRM request failed") from error
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise LocalEspoCRMError("EspoCRM returned non-JSON data") from error

    def _require_authentication(self) -> None:
        if not self.api_key and not self._token and not self._basic_authorization:
            raise LocalEspoCRMError("authenticate before calling EspoCRM")

    @staticmethod
    def _require_lifecycle_entity_type(entity_type: str) -> None:
        if entity_type not in _LIFECYCLE_ENTITY_TYPES:
            raise EnvironmentSafetyError(f"unsupported lifecycle entity type: {entity_type}")

    @staticmethod
    def _validate_base_url(base_url: str) -> str:
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.port != 8080:
            raise EnvironmentSafetyError("only http://localhost:8080 is permitted")
        return base_url.rstrip("/")


def _record_id(value: Any, entity_type: str) -> str:
    record_id = value.get("id") if isinstance(value, Mapping) else None
    if not isinstance(record_id, str) or not record_id:
        raise LocalEspoCRMError(f"{entity_type} create response did not contain an id")
    return record_id
