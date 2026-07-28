"""Fixture-ready Apollo and Hunter enrichment capability adapters.

The adapters are connector-side only.  They require an injected transport so
the capability contract remains deterministic in tests and never creates a
default network client.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlencode

from ...models import ProviderError, ProviderRateLimitError
from ..base import HttpRequest, HttpResponse, HttpTransport
from ..capabilities import Capability, CapabilityDeclaration
from ..taxonomy import classify_provider_error
from .base import EnrichmentRequest, EnrichmentResult


_VALID_ENTITY_TYPES = frozenset({"company", "person"})
_VALID_LOOKUP_TYPES = frozenset({"domain", "email", "name"})


@dataclass(frozen=True, slots=True)
class ApolloConfig:
    """Resolved Apollo configuration; its credential is never repr-visible."""

    api_key: str = field(repr=False)
    base_url: str = "https://api.apollo.io/api/v1"


@dataclass(frozen=True, slots=True)
class HunterConfig:
    """Resolved Hunter configuration; its credential is never repr-visible."""

    api_key: str = field(repr=False)
    base_url: str = "https://api.hunter.io/v2"


class ApolloEnrichmentProvider:
    """Apollo data-lookup adapter implementing the enrichment capability."""

    name = "APOLLO"

    def __init__(self, config: ApolloConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(Capability.ENRICHMENT, supports_json_mode=True)

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        _validate(request)
        response = self._send(self._build(request))
        payload = _decode_mapping(response, "APOLLO")
        return EnrichmentResult(
            provider_name=self.name,
            entity_type=request.entity_type,
            lookup_key=request.lookup_key,
            fields=self._normalize(payload, request),
            cost=None,
        )

    def _build(self, request: EnrichmentRequest) -> HttpRequest:
        path = "/organizations/enrich" if request.entity_type == "company" else "/people/match"
        body_key = {
            "domain": "domain",
            "email": "email",
            "name": "q_organization_name",
        }[request.lookup_type]
        payload = {body_key: request.lookup_key}
        return HttpRequest(
            method="POST",
            url=f"{self._config.base_url.rstrip('/')}{path}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self._config.api_key,
                "Idempotency-Key": request.idempotency_key,
            },
            body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        )

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise _provider_error("APOLLO_TIMEOUT", "Apollo request timed out", 0) from error
        except OSError as error:
            raise _provider_error("APOLLO_TRANSPORT_ERROR", "Apollo transport failed", 0) from error
        if response.status_code >= 400:
            raise _http_error(response, "APOLLO", "Apollo")
        return response

    @staticmethod
    def _normalize(payload: Mapping[str, Any], request: EnrichmentRequest) -> Mapping[str, Any]:
        record_key = "organization" if request.entity_type == "company" else "person"
        record = payload.get(record_key)
        if not isinstance(record, Mapping):
            raise _provider_error("APOLLO_MALFORMED_RESPONSE", "Apollo returned an invalid enrichment response", 400)

        if request.entity_type == "company":
            normalized = {
                "company_name": record.get("name"),
                "domain": record.get("website_url"),
                "employees": record.get("estimated_num_employees"),
                "industry": record.get("industry"),
                "revenue": record.get("annual_revenue"),
                "linkedin_url": record.get("linkedin_url"),
                "city": record.get("city"),
                "state": record.get("state"),
                "country": record.get("country"),
            }
        else:
            normalized = {
                "person_name": record.get("name"),
                "title": record.get("title"),
                "email": record.get("email"),
            }
        return _requested_fields(normalized, request.fields_requested)


class HunterEnrichmentProvider:
    """Hunter data-lookup adapter implementing the enrichment capability."""

    name = "HUNTER"

    def __init__(self, config: HunterConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(Capability.ENRICHMENT, supports_json_mode=True)

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        _validate(request)
        response = self._send(self._build(request))
        payload = _decode_mapping(response, "HUNTER")
        return EnrichmentResult(
            provider_name=self.name,
            entity_type=request.entity_type,
            lookup_key=request.lookup_key,
            fields=self._normalize(payload, request),
            cost=None,
        )

    def _build(self, request: EnrichmentRequest) -> HttpRequest:
        path, query = self._route(request)
        query["api_key"] = self._config.api_key
        return HttpRequest(
            method="GET",
            url=f"{self._config.base_url.rstrip('/')}{path}?{urlencode(query)}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Idempotency-Key": request.idempotency_key,
            },
        )

    @staticmethod
    def _route(request: EnrichmentRequest) -> tuple[str, dict[str, str]]:
        if request.lookup_type == "email":
            return "/email-verifier", {"email": request.lookup_key}
        if request.entity_type == "company":
            return "/domain-search", {"domain": request.lookup_key}
        if request.lookup_type == "domain":
            return "/email-finder", {"domain": request.lookup_key}
        return "/email-finder", {"full_name": request.lookup_key}

    def _send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self._transport.send(request)
        except TimeoutError as error:
            raise _provider_error("HUNTER_TIMEOUT", "Hunter request timed out", 0) from error
        except OSError as error:
            raise _provider_error("HUNTER_TRANSPORT_ERROR", "Hunter transport failed", 0) from error
        if response.status_code >= 400:
            raise _http_error(response, "HUNTER", "Hunter")
        return response

    @staticmethod
    def _normalize(payload: Mapping[str, Any], request: EnrichmentRequest) -> Mapping[str, Any]:
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise _provider_error("HUNTER_MALFORMED_RESPONSE", "Hunter returned an invalid enrichment response", 400)

        if request.entity_type == "company":
            normalized = {
                "domain": data.get("domain"),
                "company_name": data.get("organization"),
                "emails": _email_values(data.get("emails")),
            }
        else:
            normalized = {
                "email": data.get("email"),
                "email_status": data.get("result"),
                "confidence_score": data.get("score"),
            }
        return _requested_fields(normalized, request.fields_requested)


def _validate(request: EnrichmentRequest) -> None:
    if request.entity_type not in _VALID_ENTITY_TYPES:
        raise _provider_error(
            "ENRICH_INVALID_ENTITY_TYPE",
            f"entity_type must be one of {sorted(_VALID_ENTITY_TYPES)}",
            400,
        )
    if request.lookup_type not in _VALID_LOOKUP_TYPES:
        raise _provider_error(
            "ENRICH_INVALID_LOOKUP_TYPE",
            f"lookup_type must be one of {sorted(_VALID_LOOKUP_TYPES)}",
            400,
        )
    if not request.lookup_key.strip():
        raise _provider_error("ENRICH_EMPTY_LOOKUP_KEY", "lookup_key must not be empty", 400)


def _decode_mapping(response: HttpResponse, provider: str) -> Mapping[str, Any]:
    if isinstance(response.body, Mapping):
        return response.body
    try:
        payload = json.loads(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body)
    except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as error:
        raise _provider_error(f"{provider}_MALFORMED_RESPONSE", f"{provider.title()} returned malformed JSON", 400) from error
    if not isinstance(payload, Mapping):
        raise _provider_error(f"{provider}_MALFORMED_RESPONSE", f"{provider.title()} returned an invalid response", 400)
    return payload


def _requested_fields(values: Mapping[str, Any], requested: tuple[str, ...]) -> Mapping[str, Any]:
    return {key: value for key, value in values.items() if key in requested and value is not None}


def _email_values(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    emails = [item["value"].strip() for item in value if isinstance(item, Mapping) and isinstance(item.get("value"), str) and item["value"].strip()]
    return emails or None


def _http_error(response: HttpResponse, code_prefix: str, provider_name: str) -> ProviderError:
    if response.status_code == 429:
        return _rate_limit_error(
            f"{code_prefix}_RATE_LIMITED",
            f"{provider_name} rate limit reached",
            _parse_retry_after(response.headers),
        )
    if response.status_code >= 500:
        return _provider_error(f"{code_prefix}_UPSTREAM_ERROR", f"{provider_name} service failed", response.status_code)
    return _provider_error(f"{code_prefix}_HTTP_{response.status_code}", f"{provider_name} rejected the request", response.status_code)


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
