from __future__ import annotations

import inspect
import json
import socket
from dataclasses import fields
from pathlib import Path

import pytest

from chitu_connector.acquisition.models import ProviderError
from chitu_connector.acquisition.providers import (
    ApifyConfig,
    ApifyProvider,
    Capability,
    CapabilityDeclaration,
    ErrorClass,
    HttpRequest,
    HttpResponse,
    SerperConfig,
    SerperSearchProvider,
    classify_provider_error,
)
from chitu_connector.acquisition.providers.completion import (
    CompletionCapability,
    CompletionProvider,
    CompletionRequest,
    CompletionResult,
)
from chitu_connector.acquisition.providers.enrichment import (
    EnrichmentProvider,
    EnrichmentRequest,
    EnrichmentResult,
)
from chitu_connector.acquisition.providers.search import SearchProvider, SearchRequest, SearchResult


class FixtureOnlyTransport:
    """Deterministic in-memory transport that rejects every non-fixture URL."""

    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self._responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        assert request.url.startswith("https://fixture."), "contract tests must not target a live provider"
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _port_request() -> SearchRequest:
    return SearchRequest(
        job_id="wp2-contract-job",
        provider_name="fixture",
        keyword="3d distributor",
        country="US",
        persona="distributor",
        product="resin",
        result_limit=1,
        idempotency_key="wp2-contract-idempotency-key",
    )


def _apify_success() -> list[HttpResponse]:
    return [
        HttpResponse(201, {"data": {"defaultDatasetId": "fixture-dataset"}}),
        HttpResponse(200, [{"id": "fixture-1", "title": "Fixture Distributor", "url": "https://fixture.invalid"}]),
    ]


def _serper_success() -> list[HttpResponse]:
    return [
        HttpResponse(200, {"organic": [{"position": 1, "title": "Fixture Distributor", "link": "https://fixture.invalid"}]})
    ]


def _apify(transport: FixtureOnlyTransport) -> ApifyProvider:
    return ApifyProvider(
        ApifyConfig("fixture-token", base_url="https://fixture.apify.invalid", actor_id="fixture/search"),
        transport=transport,
    )


def _serper(transport: FixtureOnlyTransport) -> SerperSearchProvider:
    return SerperSearchProvider(
        SerperConfig("fixture-key", base_url="https://fixture.serper.invalid"),
        transport=transport,
    )


@pytest.mark.parametrize(
    ("adapter_factory", "responses"),
    [(_apify, _apify_success), (_serper, _serper_success)],
)
def test_search_provider_contract_declares_only_the_search_capability(adapter_factory, responses) -> None:
    adapter = adapter_factory(FixtureOnlyTransport(responses()))

    assert adapter.capabilities == CapabilityDeclaration(Capability.SEARCH, supports_json_mode=True)
    assert tuple(inspect.signature(SearchProvider.search).parameters) == ("self", "request")
    assert inspect.signature(adapter.search).parameters["request"].annotation


def test_enrichment_protocol_has_reference_only_request_and_result_contract() -> None:
    assert {"name", "capabilities", "enrich"}.issubset(EnrichmentProvider.__dict__)
    assert tuple(inspect.signature(EnrichmentProvider.enrich).parameters) == ("self", "request")
    assert {field.name for field in fields(EnrichmentRequest)} == {
        "request_id", "provider_name", "entity_type", "lookup_key", "lookup_type", "fields_requested", "idempotency_key", "initiating_user",
    }
    assert {field.name for field in fields(EnrichmentResult)} == {
        "provider_name", "entity_type", "lookup_key", "fields", "cost", "capability",
    }


def test_completion_protocol_is_limited_to_ratified_non_executing_capabilities() -> None:
    assert {item.value for item in CompletionCapability} == {
        "research_evidence", "qualification_insight", "draft_assistance", "reply_assistance",
    }
    assert tuple(inspect.signature(CompletionProvider.complete).parameters) == ("self", "request")
    assert "credential" not in {field.name.casefold() for field in fields(CompletionRequest)}
    assert "credential" not in {field.name.casefold() for field in fields(CompletionResult)}


@pytest.mark.parametrize(
    ("adapter_factory", "status_code", "provider_code"),
    [
        (_apify, 401, "APIFY_AUTHENTICATION_FAILED"),
        (_apify, 429, "APIFY_RATE_LIMITED"),
        (_apify, 500, "APIFY_UPSTREAM_ERROR"),
        (_serper, 401, "SERPER_AUTHENTICATION_FAILED"),
        (_serper, 429, "SERPER_RATE_LIMITED"),
        (_serper, 500, "SERPER_UPSTREAM_ERROR"),
    ],
)
def test_adapter_failures_match_the_shared_error_taxonomy(adapter_factory, status_code: int, provider_code: str) -> None:
    with pytest.raises(ProviderError) as raised:
        adapter_factory(FixtureOnlyTransport([HttpResponse(status_code, {})])).search(_port_request())

    expected = classify_provider_error(status_code, provider_code)
    assert raised.value.error_class is expected.error_class
    assert raised.value.retryable is expected.retryable


@pytest.mark.parametrize(
    ("adapter_factory", "responses"),
    [(_apify, _apify_success), (_serper, _serper_success)],
)
def test_idempotency_and_fixture_transport_prevent_egress(monkeypatch, adapter_factory, responses) -> None:
    def _network_forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        pytest.fail("fixture transport must not create a network connection")

    monkeypatch.setattr(socket, "create_connection", _network_forbidden)
    first_transport = FixtureOnlyTransport(responses())
    second_transport = FixtureOnlyTransport(responses())

    first_result = adapter_factory(first_transport).search(_port_request())
    second_result = adapter_factory(second_transport).search(_port_request())

    assert isinstance(first_result, SearchResult)
    assert first_result == second_result
    for transport in (first_transport, second_transport):
        assert transport.requests
        assert {request.headers["Idempotency-Key"] for request in transport.requests} == {"wp2-contract-idempotency-key"}


def test_providercredential_remains_an_internal_crm_reference_unavailable_to_ports() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    credential_metadata = repository_root / "crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/ProviderCredential.json"
    credential_acl = repository_root / "crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityAcl/ProviderCredential.json"
    metadata = json.loads(credential_metadata.read_text(encoding="utf-8"))
    acl = json.loads(credential_acl.read_text(encoding="utf-8"))

    assert metadata["fields"]["credentialReference"]["type"] == "varchar"
    assert acl == {"fields": {"credentialReference": {"internal": True}}}

    port_sources = [
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/capabilities.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/taxonomy.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/search/base.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/enrichment/base.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/completion/base.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/apify_provider.py",
        repository_root / "chitu-connector/chitu_connector/acquisition/providers/serper_provider.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in port_sources)

    assert "credentialReference" not in source
    assert "ProviderCredential" not in source
