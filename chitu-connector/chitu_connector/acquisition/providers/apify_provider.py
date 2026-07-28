"""Fixture-ready Apify adapter skeleton.

The default transport is deliberately absent: callers must inject a transport
for an actual invocation. This keeps unit tests and the frozen worker contract
independent from external APIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, overload
from urllib.parse import quote

from ..models import ProviderError, ProviderResult, RawCandidate, SearchRequest as LegacySearchRequest
from .base import HttpRequest, HttpResponse, HttpTransport
from .capabilities import Capability, CapabilityDeclaration
from .config import ApifyConfig
from .search import SearchRequest as CapabilitySearchRequest, SearchResult
from .taxonomy import classify_provider_error


@dataclass(frozen=True, slots=True)
class _ApifyEndpoints:
    run_path: str
    dataset_path: str


class ApifyProvider:
    name = "APIFY"

    def __init__(self, config: ApifyConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(Capability.SEARCH, supports_json_mode=True)

    def build_run_request(self, request: LegacySearchRequest | CapabilitySearchRequest) -> HttpRequest:
        if request.result_limit < 1:
            raise _provider_error("APIFY_INVALID_REQUEST", "result_limit must be positive", 400)
        payload = {
            "searchStringsArray": [self._query(request)],
            "maxPagesPerQuery": 1,
            "resultsPerPage": min(request.result_limit, 100),
            "maxResultsPerQuery": request.result_limit,
            "mobileResults": False,
            "saveHtml": False,
        }
        if request.country:
            payload["countryCode"] = request.country
        return HttpRequest(
            method="POST",
            url=self._url(f"/v2/acts/{quote(self._config.actor_id, safe='~')}/runs"),
            headers=self._headers(_idempotency_key(request)),
            body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    def build_dataset_request(self, dataset_id: str, *, idempotency_key: str | None = None) -> HttpRequest:
        if not dataset_id.strip():
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify run did not return a dataset", 400)
        return HttpRequest(
            method="GET",
            url=self._url(f"/v2/datasets/{quote(dataset_id, safe='~_-')}/items?clean=true&format=json"),
            headers=self._headers(idempotency_key),
        )

    @overload
    def search(self, request: LegacySearchRequest) -> ProviderResult: ...

    @overload
    def search(self, request: CapabilitySearchRequest) -> SearchResult: ...

    def search(self, request: LegacySearchRequest | CapabilitySearchRequest) -> ProviderResult | SearchResult:
        run_response = self._send(self.build_run_request(request))
        run_payload = self._json(run_response)
        dataset_id = self._dataset_id(run_payload)
        dataset_response = self._send(self.build_dataset_request(dataset_id, idempotency_key=_idempotency_key(request)))
        items = self._dataset_items(self._json(dataset_response))
        candidates = tuple(self._candidate(item, request) for item in items[: request.result_limit])
        if isinstance(request, CapabilitySearchRequest):
            return SearchResult(self.name, candidates)
        return ProviderResult(self.name, candidates)

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise _provider_error("APIFY_TIMEOUT", "Apify request timed out", 0) from error
        except OSError as error:
            raise _provider_error("APIFY_TRANSPORT_ERROR", "Apify transport failed", 0) from error
        if response.status_code >= 400:
            raise self._http_error(response)
        return response

    @staticmethod
    def _json(response: HttpResponse) -> Mapping[str, Any] | list[Any]:
        if isinstance(response.body, (Mapping, list)):
            return response.body
        try:
            payload = json.loads(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body)
        except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as error:
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify returned malformed JSON", 400) from error
        if not isinstance(payload, (Mapping, list)):
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify returned an invalid JSON shape", 400)
        return payload

    @staticmethod
    def _dataset_id(payload: Mapping[str, Any] | list[Any]) -> str:
        if not isinstance(payload, Mapping):
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify run response is not an object", 400)
        data = payload.get("data") if isinstance(payload.get("data"), Mapping) else payload
        dataset_id = data.get("defaultDatasetId") or data.get("datasetId")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify run did not return a dataset", 400)
        return dataset_id.strip()

    @staticmethod
    def _dataset_items(payload: Mapping[str, Any] | list[Any]) -> list[Mapping[str, Any]]:
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, Mapping) and isinstance(payload.get("data"), list):
            items = payload["data"]
        elif isinstance(payload, Mapping) and isinstance(payload.get("items"), list):
            items = payload["items"]
        else:
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify dataset response is not a result list", 400)
        if not all(isinstance(item, Mapping) for item in items):
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify dataset contains an invalid result", 400)
        return list(items)

    @staticmethod
    def _candidate(item: Mapping[str, Any], request: SearchRequest) -> RawCandidate:
        candidate_id = _text(item, "id", "rawResultId", "resultId")
        company_name = _text(item, "companyName", "company_name", "name", "title")
        if not candidate_id or not company_name:
            raise _provider_error("APIFY_MALFORMED_RESPONSE", "Apify result lacks candidate identity", 400)
        domain = _text(item, "domain", "website", "displayedUrl", "url")
        source_url = _text(item, "sourceUrl", "url")
        country = _text(item, "country") or request.country
        return RawCandidate(candidate_id, company_name, domain, source_url, country, dict(item))

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self._config.api_token}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}{path}"

    @staticmethod
    def _query(request: LegacySearchRequest | CapabilitySearchRequest) -> str:
        country = request.country.strip() if request.country else ""
        return f'{request.keyword.strip()} "{country}"'.strip()

    @staticmethod
    def _http_error(response: HttpResponse) -> ProviderError:
        status_code = response.status_code
        if status_code == 401:
            return _provider_error("APIFY_AUTHENTICATION_FAILED", "Apify authentication failed", status_code)
        if status_code == 403:
            return _provider_error("APIFY_FORBIDDEN", "Apify access was forbidden", status_code)
        if status_code == 429:
            return _provider_error("APIFY_RATE_LIMITED", "Apify rate limit reached", status_code, retry_after=_parse_retry_after(response.headers))
        if status_code >= 500:
            return _provider_error("APIFY_UPSTREAM_ERROR", "Apify service failed", status_code)
        return _provider_error("APIFY_REQUEST_REJECTED", "Apify rejected the request", status_code)


def _provider_error(code: str, safe_message: str, status_code: int, *, retry_after: int | None = None) -> ProviderError:
    classified = classify_provider_error(status_code, code, retry_after=retry_after)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    error.retry_after = classified.retry_after
    return error


def _idempotency_key(request: LegacySearchRequest | CapabilitySearchRequest) -> str | None:
    return request.idempotency_key if isinstance(request, CapabilitySearchRequest) else None


def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    for key in ("retry-after", "Retry-After"):
        try:
            value = int(headers[key])
        except (KeyError, TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _text(item: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
