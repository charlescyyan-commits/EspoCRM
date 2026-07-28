"""Fixture-ready Serper adapter.

The default transport is deliberately absent: callers must inject a transport
for an actual invocation. This keeps unit tests and the frozen worker contract
independent from external APIs.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, overload

from ..models import ProviderError, ProviderRateLimitError, ProviderResult, RawCandidate, SearchRequest as LegacySearchRequest
from .base import HttpRequest, HttpResponse, HttpTransport
from .capabilities import Capability, CapabilityDeclaration
from .config import SerperConfig
from .search import SearchRequest as CapabilitySearchRequest, SearchResult
from .taxonomy import classify_provider_error


class SerperSearchProvider:
    name = "SERPER"

    def __init__(self, config: SerperConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(Capability.SEARCH, supports_json_mode=True)

    def build_request(self, request: LegacySearchRequest | CapabilitySearchRequest) -> HttpRequest:
        if request.result_limit < 1:
            raise _provider_error("SERPER_INVALID_REQUEST", "result_limit must be positive", 400)
        payload: dict[str, Any] = {
            "q": self._query(request),
            "num": min(request.result_limit, 100),
        }
        if request.country:
            payload["gl"] = request.country.strip().casefold()
        return HttpRequest(
            method="POST",
            url=f"{self._config.base_url.rstrip('/')}/search",
            headers=self._headers(_idempotency_key(request)),
            body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    @overload
    def search(self, request: LegacySearchRequest) -> ProviderResult: ...

    @overload
    def search(self, request: CapabilitySearchRequest) -> SearchResult: ...

    def search(self, request: LegacySearchRequest | CapabilitySearchRequest) -> ProviderResult | SearchResult:
        http_request = self.build_request(request)
        response = self._send(http_request)
        payload = self._json(response)
        candidates = tuple(self._candidate(item, request) for item in self._organic_results(payload)[: request.result_limit])
        if isinstance(request, CapabilitySearchRequest):
            return SearchResult(self.name, candidates)
        return ProviderResult(self.name, candidates)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise _provider_error("SERPER_TIMEOUT", "Serper request timed out", 0) from error
        except OSError as error:
            raise _provider_error("SERPER_TRANSPORT_ERROR", "Serper transport failed", 0) from error
        if response.status_code >= 400:
            raise self._http_error(response)
        return response

    @staticmethod
    def _json(response: HttpResponse) -> Mapping[str, Any]:
        if isinstance(response.body, Mapping):
            return response.body
        try:
            payload = json.loads(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body)
        except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as error:
            raise _provider_error("SERPER_MALFORMED_RESPONSE", "Serper returned malformed JSON", 400) from error
        if not isinstance(payload, Mapping):
            raise _provider_error("SERPER_MALFORMED_RESPONSE", "Serper returned an invalid JSON shape", 400)
        return payload

    @staticmethod
    def _organic_results(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        organic = payload.get("organic")
        if organic is None:
            return []
        if not isinstance(organic, list):
            raise _provider_error("SERPER_MALFORMED_RESPONSE", "Serper organic results is not a list", 400)
        if not all(isinstance(item, Mapping) for item in organic):
            raise _provider_error("SERPER_MALFORMED_RESPONSE", "Serper organic result contains an invalid entry", 400)
        return list(organic)

    @staticmethod
    def _candidate(item: Mapping[str, Any], request: SearchRequest) -> RawCandidate:
        candidate_id = _text(item, "position", "link", "title")
        company_name = _text(item, "title")
        if not candidate_id or not company_name:
            raise _provider_error("SERPER_MALFORMED_RESPONSE", "Serper result lacks candidate identity", 400)
        link = _text(item, "link")
        domain = link
        source_url = link
        country = request.country
        return RawCandidate(candidate_id, company_name, domain, source_url, country, dict(item))

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self._config.api_key,
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    @staticmethod
    def _query(request: LegacySearchRequest | CapabilitySearchRequest) -> str:
        country = request.country.strip() if request.country else ""
        return f'{request.keyword.strip()} "{country}"'.strip()

    @staticmethod
    def _http_error(response: HttpResponse) -> ProviderError:
        status_code = response.status_code
        if status_code == 401:
            return _provider_error("SERPER_AUTHENTICATION_FAILED", "Serper authentication failed", status_code)
        if status_code == 403:
            return _provider_error("SERPER_FORBIDDEN", "Serper access was forbidden", status_code)
        if status_code == 429:
            retry_after = _parse_retry_after(response.headers)
            return _rate_limit_error("SERPER_RATE_LIMITED", "Serper rate limit reached", retry_after)
        if status_code >= 500:
            return _provider_error("SERPER_UPSTREAM_ERROR", "Serper service failed", status_code)
        return _provider_error("SERPER_REQUEST_REJECTED", "Serper rejected the request", status_code)


def _text(item: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def _provider_error(code: str, safe_message: str, status_code: int) -> ProviderError:
    classified = classify_provider_error(status_code, code)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    return error


def _rate_limit_error(code: str, safe_message: str, retry_after: int | None) -> ProviderRateLimitError:
    classified = classify_provider_error(429, code, retry_after=retry_after)
    error = ProviderRateLimitError(code, safe_message, retryable=classified.retryable, retry_after=classified.retry_after)
    error.error_class = classified.error_class
    return error


def _idempotency_key(request: LegacySearchRequest | CapabilitySearchRequest) -> str | None:
    return request.idempotency_key if isinstance(request, CapabilitySearchRequest) else None


def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    for key in ("retry-after", "Retry-After"):
        value = headers.get(key)
        if value is None:
            continue
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            continue
        if seconds >= 0:
            return seconds
    return None
