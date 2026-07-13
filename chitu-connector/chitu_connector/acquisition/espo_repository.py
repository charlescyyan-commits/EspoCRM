"""EspoCRM REST persistence adapter for the single-job acquisition runner."""

from __future__ import annotations

import json
import ssl
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .models import ClaimResult, PersistenceError


_SEARCH_JOB_FIELDS = (
    "id,status,keyword,country,product,source,queryFingerprint,startedAt,completedAt,"
    "resultCount,acceptedCount,rejectedCount,prospectCount,errorMessage,failureReason,modifiedAt"
)
_PROSPECT_FIELDS = frozenset({
    "name", "externalProspectId", "source", "sourceUrl", "website", "country", "queue", "status",
    "researchStatus", "qualificationStatus", "crmPushStatus", "searchJobId", "note",
})


class EspoAcquisitionRepository:
    """Best-effort conditional ``AcquisitionStore`` implementation over EspoCRM REST.

    EspoCRM currently exposes no dedicated atomic claim action or ETag contract for
    SearchJob. Claims therefore use GET-then-PUT with a post-write verification and
    are intentionally limited to the single-runner MVP.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: float = 30.0,
        verify_tls: bool = True,
        request_opener: Callable[..., Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("an EspoCRM API key is required")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.params or parsed.query or parsed.fragment:
            raise ValueError("base URL must be an absolute HTTP(S) URL without query or fragment")
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._verify_tls = verify_tls
        self._request_opener = request_opener or urlopen

    def fetch_search_job(self, job_id: str) -> Mapping[str, Any] | None:
        self._validate_id(job_id)
        return self._request(
            "GET",
            f"SearchJob/{job_id}",
            query={"select": _SEARCH_JOB_FIELDS},
            operation="read",
            not_found_is_none=True,
        )

    def claim_search_job(
        self,
        job_id: str,
        *,
        expected_status: str,
        started_at: str,
        expected_version: str | None = None,
    ) -> ClaimResult:
        job = self.fetch_search_job(job_id)
        if job is None:
            return ClaimResult(False, reason="NOT_FOUND")
        previous_status = _optional_text(job.get("status"))
        if previous_status != expected_status:
            return ClaimResult(
                False,
                previous_status=previous_status,
                current_status=previous_status,
                reason="STATUS_MISMATCH",
                version=_version(job),
            )
        if expected_version is not None and _version(job) != expected_version:
            return ClaimResult(
                False,
                previous_status=previous_status,
                current_status=previous_status,
                reason="VERSION_MISMATCH",
                version=_version(job),
            )

        self._request(
            "PUT",
            f"SearchJob/{job_id}",
            body={"status": "RUNNING", "startedAt": started_at},
            operation="write",
        )
        confirmed = self.fetch_search_job(job_id)
        current_status = _optional_text(confirmed.get("status")) if confirmed is not None else None
        if confirmed is None or current_status != "RUNNING":
            return ClaimResult(
                False,
                previous_status=previous_status,
                current_status=current_status,
                reason="CLAIM_NOT_CONFIRMED",
                version=_version(confirmed),
            )
        return ClaimResult(
            True,
            job=confirmed,
            previous_status=previous_status,
            current_status="RUNNING",
            version=_version(confirmed),
        )

    def update_search_job(
        self,
        job_id: str,
        values: Mapping[str, Any],
        *,
        expected_status: str | None = None,
        expected_version: str | None = None,
    ) -> None:
        self._validate_id(job_id)
        if not values:
            raise PersistenceError("ESPO_WRITE_ERROR", "SearchJob update values are required", retryable=False)
        if expected_status is not None or expected_version is not None:
            current = self.fetch_search_job(job_id)
            if current is None:
                raise PersistenceError("ESPO_WRITE_ERROR", "SearchJob was not found during conditional update", retryable=False)
            if expected_status is not None and current.get("status") != expected_status:
                raise PersistenceError("STATUS_CONFLICT", "SearchJob status changed before update", retryable=True)
            if expected_version is not None and _version(current) != expected_version:
                raise PersistenceError("VERSION_CONFLICT", "SearchJob version changed before update", retryable=True)

        self._request("PUT", f"SearchJob/{job_id}", body=dict(values), operation="write")
        desired_status = _optional_text(values.get("status"))
        if desired_status is None:
            return
        confirmed = self.fetch_search_job(job_id)
        if confirmed is None or confirmed.get("status") != desired_status:
            raise PersistenceError("ESPO_WRITE_ERROR", "SearchJob update was not confirmed", retryable=True)

    def has_prospect(self, provider_name: str, normalized_domain: str) -> bool:
        website = f"https://{normalized_domain}"
        response = self._request(
            "GET",
            "ProspectPool",
            query={
                "maxSize": "1",
                "select": "id,source,website",
                "where[0][type]": "equals",
                "where[0][attribute]": "source",
                "where[0][value]": provider_name,
                "where[1][type]": "equals",
                "where[1][attribute]": "website",
                "where[1][value]": website,
            },
            operation="read",
        )
        records = response.get("list") if isinstance(response, Mapping) else None
        return isinstance(records, list) and any(isinstance(item, Mapping) for item in records)

    def create_prospect(self, values: Mapping[str, Any]) -> None:
        body = {key: value for key, value in values.items() if key in _PROSPECT_FIELDS}
        if not _optional_text(body.get("name")):
            raise PersistenceError("ESPO_WRITE_ERROR", "ProspectPool name is required", retryable=False)
        response = self._request("POST", "ProspectPool", body=body, operation="write")
        if not isinstance(response.get("id") if isinstance(response, Mapping) else None, str):
            raise PersistenceError("ESPO_WRITE_ERROR", "ProspectPool create response was not confirmed", retryable=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        query: Mapping[str, str] | None = None,
        operation: str,
        not_found_is_none: bool = False,
    ) -> Mapping[str, Any] | None:
        if path.startswith(("/", "http://", "https://")):
            raise ValueError("absolute API paths are forbidden")
        url = f"{self.base_url}/api/v1/{path}"
        if query:
            url = f"{url}?{urlencode(query, safe='[]')}"
        headers = {"Accept": "application/json", "X-Api-Key": self._api_key}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=method)
        opener_kwargs: dict[str, Any] = {"timeout": self._timeout_seconds}
        if url.startswith("https://") and not self._verify_tls:
            opener_kwargs["context"] = ssl._create_unverified_context()
        try:
            with self._request_opener(request, **opener_kwargs) as response:
                raw = response.read()
        except HTTPError as error:
            if error.code == 404 and not_found_is_none:
                return None
            raise _http_error(operation, error.code) from error
        except (URLError, TimeoutError, OSError) as error:
            raise PersistenceError(_operation_code(operation), f"EspoCRM {operation} request failed", retryable=True) from error
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PersistenceError(_operation_code(operation), f"EspoCRM {operation} response was not valid JSON", retryable=False) from error
        if not isinstance(payload, Mapping):
            raise PersistenceError(_operation_code(operation), f"EspoCRM {operation} response was not an object", retryable=False)
        return payload

    @staticmethod
    def _validate_id(job_id: str) -> None:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id is required")


def _http_error(operation: str, status_code: int) -> PersistenceError:
    if status_code in {401, 403}:
        return PersistenceError(_operation_code(operation), f"EspoCRM {operation} authentication failed (HTTP {status_code})", retryable=False)
    if status_code == 429 or status_code >= 500:
        return PersistenceError(_operation_code(operation), f"EspoCRM {operation} request failed (HTTP {status_code})", retryable=True)
    return PersistenceError(_operation_code(operation), f"EspoCRM {operation} request failed (HTTP {status_code})", retryable=False)


def _operation_code(operation: str) -> str:
    return "ESPO_READ_ERROR" if operation == "read" else "ESPO_WRITE_ERROR"


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _version(record: Mapping[str, Any] | None) -> str | None:
    if not isinstance(record, Mapping):
        return None
    return _optional_text(record.get("modifiedAt")) or _optional_text(record.get("version"))
