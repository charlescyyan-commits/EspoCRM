"""Fixture-ready Serper adapter.

The default transport is deliberately absent: callers must inject a transport
for an actual invocation. This keeps unit tests and the frozen worker contract
independent from external APIs.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..models import ProviderError, ProviderRateLimitError, ProviderResult, RawCandidate, SearchRequest
from .base import HttpRequest, HttpResponse, HttpTransport
from .config import SerperConfig


class SerperSearchProvider:
    name = "SERPER"

    def __init__(self, config: SerperConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    def build_request(self, request: SearchRequest) -> HttpRequest:
        if request.result_limit < 1:
            raise ProviderError("SERPER_INVALID_REQUEST", "result_limit must be positive", retryable=False)
        payload: dict[str, Any] = {
            "q": self._query(request),
            "num": min(request.result_limit, 100),
        }
        if request.country:
            payload["gl"] = request.country.strip().casefold()
        return HttpRequest(
            method="POST",
            url=f"{self._config.base_url.rstrip('/')}/search",
            headers=self._headers(),
            body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    def search(self, request: SearchRequest) -> ProviderResult:
        http_request = self.build_request(request)
        response = self._send(http_request)
        payload = self._json(response)
        candidates = tuple(self._candidate(item, request) for item in self._organic_results(payload)[: request.result_limit])
        return ProviderResult(self.name, candidates)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise ProviderError("SERPER_TIMEOUT", "Serper request timed out", retryable=True) from error
        except OSError as error:
            raise ProviderError("SERPER_TRANSPORT_ERROR", "Serper transport failed", retryable=True) from error
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
            raise ProviderError("SERPER_MALFORMED_RESPONSE", "Serper returned malformed JSON", retryable=False) from error
        if not isinstance(payload, Mapping):
            raise ProviderError("SERPER_MALFORMED_RESPONSE", "Serper returned an invalid JSON shape", retryable=False)
        return payload

    @staticmethod
    def _organic_results(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        organic = payload.get("organic")
        if organic is None:
            return []
        if not isinstance(organic, list):
            raise ProviderError("SERPER_MALFORMED_RESPONSE", "Serper organic results is not a list", retryable=False)
        if not all(isinstance(item, Mapping) for item in organic):
            raise ProviderError("SERPER_MALFORMED_RESPONSE", "Serper organic result contains an invalid entry", retryable=False)
        return list(organic)

    @staticmethod
    def _candidate(item: Mapping[str, Any], request: SearchRequest) -> RawCandidate:
        candidate_id = _text(item, "position", "link", "title")
        company_name = _text(item, "title")
        if not candidate_id or not company_name:
            raise ProviderError("SERPER_MALFORMED_RESPONSE", "Serper result lacks candidate identity", retryable=False)
        link = _text(item, "link")
        domain = link
        source_url = link
        country = request.country
        return RawCandidate(candidate_id, company_name, domain, source_url, country, dict(item))

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self._config.api_key,
        }

    @staticmethod
    def _query(request: SearchRequest) -> str:
        country = request.country.strip() if request.country else ""
        return f'{request.keyword.strip()} "{country}"'.strip()

    @staticmethod
    def _http_error(response: HttpResponse) -> ProviderError:
        status_code = response.status_code
        if status_code == 401:
            return ProviderError("SERPER_AUTHENTICATION_FAILED", "Serper authentication failed", retryable=False)
        if status_code == 403:
            return ProviderError("SERPER_FORBIDDEN", "Serper access was forbidden", retryable=False)
        if status_code == 429:
            retry_after = _parse_retry_after(response.headers)
            return ProviderRateLimitError("SERPER_RATE_LIMITED", "Serper rate limit reached", retryable=True, retry_after=retry_after)
        if status_code >= 500:
            return ProviderError("SERPER_UPSTREAM_ERROR", "Serper service failed", retryable=True)
        return ProviderError("SERPER_REQUEST_REJECTED", "Serper rejected the request", retryable=False)


def _text(item: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


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
