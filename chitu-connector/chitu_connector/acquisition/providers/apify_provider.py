"""Fixture-ready Apify adapter skeleton.

The default transport is deliberately absent: callers must inject a transport
for an actual invocation. This keeps unit tests and the frozen worker contract
independent from external APIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

from ..models import ProviderError, ProviderResult, RawCandidate, SearchRequest
from .base import HttpRequest, HttpResponse, HttpTransport
from .config import ApifyConfig


@dataclass(frozen=True, slots=True)
class _ApifyEndpoints:
    run_path: str
    dataset_path: str


class ApifyProvider:
    name = "APIFY"

    def __init__(self, config: ApifyConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    def build_run_request(self, request: SearchRequest) -> HttpRequest:
        if request.result_limit < 1:
            raise ProviderError("APIFY_INVALID_REQUEST", "result_limit must be positive", retryable=False)
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
            headers=self._headers(),
            body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    def build_dataset_request(self, dataset_id: str) -> HttpRequest:
        if not dataset_id.strip():
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify run did not return a dataset", retryable=False)
        return HttpRequest(
            method="GET",
            url=self._url(f"/v2/datasets/{quote(dataset_id, safe='~_-')}/items?clean=true&format=json"),
            headers=self._headers(),
        )

    def search(self, request: SearchRequest) -> ProviderResult:
        run_response = self._send(self.build_run_request(request))
        run_payload = self._json(run_response)
        dataset_id = self._dataset_id(run_payload)
        dataset_response = self._send(self.build_dataset_request(dataset_id))
        items = self._dataset_items(self._json(dataset_response))
        candidates = tuple(self._candidate(item, request) for item in items[: request.result_limit])
        return ProviderResult(self.name, candidates)

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise ProviderError("APIFY_TIMEOUT", "Apify request timed out", retryable=True) from error
        except OSError as error:
            raise ProviderError("APIFY_TRANSPORT_ERROR", "Apify transport failed", retryable=True) from error
        if response.status_code >= 400:
            raise self._http_error(response.status_code)
        return response

    @staticmethod
    def _json(response: HttpResponse) -> Mapping[str, Any] | list[Any]:
        if isinstance(response.body, (Mapping, list)):
            return response.body
        try:
            payload = json.loads(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body)
        except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as error:
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify returned malformed JSON", retryable=False) from error
        if not isinstance(payload, (Mapping, list)):
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify returned an invalid JSON shape", retryable=False)
        return payload

    @staticmethod
    def _dataset_id(payload: Mapping[str, Any] | list[Any]) -> str:
        if not isinstance(payload, Mapping):
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify run response is not an object", retryable=False)
        data = payload.get("data") if isinstance(payload.get("data"), Mapping) else payload
        dataset_id = data.get("defaultDatasetId") or data.get("datasetId")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify run did not return a dataset", retryable=False)
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
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify dataset response is not a result list", retryable=False)
        if not all(isinstance(item, Mapping) for item in items):
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify dataset contains an invalid result", retryable=False)
        return list(items)

    @staticmethod
    def _candidate(item: Mapping[str, Any], request: SearchRequest) -> RawCandidate:
        candidate_id = _text(item, "id", "rawResultId", "resultId")
        company_name = _text(item, "companyName", "company_name", "name", "title")
        if not candidate_id or not company_name:
            raise ProviderError("APIFY_MALFORMED_RESPONSE", "Apify result lacks candidate identity", retryable=False)
        domain = _text(item, "domain", "website", "displayedUrl", "url")
        source_url = _text(item, "sourceUrl", "url")
        country = _text(item, "country") or request.country
        return RawCandidate(candidate_id, company_name, domain, source_url, country, dict(item))

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "Authorization": f"Bearer {self._config.api_token}", "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}{path}"

    @staticmethod
    def _query(request: SearchRequest) -> str:
        country = request.country.strip() if request.country else ""
        return f'{request.keyword.strip()} "{country}"'.strip()

    @staticmethod
    def _http_error(status_code: int) -> ProviderError:
        if status_code == 401:
            return ProviderError("APIFY_AUTHENTICATION_FAILED", "Apify authentication failed", retryable=False)
        if status_code == 403:
            return ProviderError("APIFY_FORBIDDEN", "Apify access was forbidden", retryable=False)
        if status_code == 429:
            return ProviderError("APIFY_RATE_LIMITED", "Apify rate limit reached", retryable=True)
        if status_code >= 500:
            return ProviderError("APIFY_UPSTREAM_ERROR", "Apify service failed", retryable=True)
        return ProviderError("APIFY_REQUEST_REJECTED", "Apify rejected the request", retryable=False)


def _text(item: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
