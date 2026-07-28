from __future__ import annotations

import inspect

import pytest

from chitu_connector.acquisition.models import ProviderError, ProviderResult, SearchRequest as LegacySearchRequest
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
)
from chitu_connector.acquisition.providers.search import SearchRequest as CapabilitySearchRequest, SearchResult


class FixtureTransport:
    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def legacy_request() -> LegacySearchRequest:
    return LegacySearchRequest(
        job_id="legacy-job-001",
        provider_name="fixture",
        keyword="3d distributor",
        country="US",
        persona="distributor",
        product="resin",
        result_limit=2,
    )


def capability_request() -> CapabilitySearchRequest:
    return CapabilitySearchRequest(
        job_id="port-job-001",
        provider_name="fixture",
        keyword="3d distributor",
        country="US",
        persona="distributor",
        product="resin",
        result_limit=2,
        idempotency_key="port-idempotency-001",
    )


def apify_provider(transport: FixtureTransport) -> ApifyProvider:
    return ApifyProvider(
        ApifyConfig("fixture-token", base_url="https://fixture.apify.invalid", actor_id="fixture/search"),
        transport=transport,
    )


def serper_provider(transport: FixtureTransport) -> SerperSearchProvider:
    return SerperSearchProvider(
        SerperConfig("fixture-key", base_url="https://fixture.serper.invalid"),
        transport=transport,
    )


def apify_success_responses() -> list[HttpResponse]:
    return [
        HttpResponse(201, {"data": {"defaultDatasetId": "dataset-001"}}),
        HttpResponse(200, [{"id": "candidate-001", "title": "Fixture Distributor", "url": "https://fixture.invalid"}]),
    ]


def serper_success_responses() -> list[HttpResponse]:
    return [
        HttpResponse(200, {"organic": [{"position": 1, "title": "Fixture Distributor", "link": "https://fixture.invalid"}]}),
    ]


@pytest.mark.parametrize(
    ("provider", "responses"),
    [
        (apify_provider, apify_success_responses),
        (serper_provider, serper_success_responses),
    ],
)
def test_search_adapters_declare_the_search_capability(provider, responses) -> None:
    adapter = provider(FixtureTransport(responses()))

    assert adapter.capabilities == CapabilityDeclaration(Capability.SEARCH, supports_json_mode=True)


@pytest.mark.parametrize(
    ("provider", "responses"),
    [
        (apify_provider, apify_success_responses),
        (serper_provider, serper_success_responses),
    ],
)
def test_search_adapters_support_new_port_contract_without_breaking_legacy_callers(provider, responses) -> None:
    legacy_transport = FixtureTransport(responses())
    legacy_result = provider(legacy_transport).search(legacy_request())
    port_transport = FixtureTransport(responses())
    port_result = provider(port_transport).search(capability_request())

    assert isinstance(legacy_result, ProviderResult)
    assert not isinstance(legacy_result, SearchResult)
    assert isinstance(port_result, SearchResult)
    assert port_result.capability is Capability.SEARCH
    assert all("Idempotency-Key" not in request.headers for request in legacy_transport.requests)
    assert all(request.headers["Idempotency-Key"] == "port-idempotency-001" for request in port_transport.requests)


@pytest.mark.parametrize(
    ("provider", "status_code", "expected"),
    [
        (apify_provider, 401, ErrorClass.AUTH),
        (apify_provider, 429, ErrorClass.RATE_LIMIT),
        (apify_provider, 500, ErrorClass.PROVIDER),
        (serper_provider, 401, ErrorClass.AUTH),
        (serper_provider, 429, ErrorClass.RATE_LIMIT),
        (serper_provider, 500, ErrorClass.PROVIDER),
    ],
)
def test_search_adapter_http_failures_are_classified(provider, status_code: int, expected: ErrorClass) -> None:
    with pytest.raises(ProviderError) as error:
        provider(FixtureTransport([HttpResponse(status_code, {})])).search(legacy_request())

    assert error.value.error_class is expected
    assert error.value.retryable is (expected in {ErrorClass.RATE_LIMIT, ErrorClass.PROVIDER})


@pytest.mark.parametrize("provider", [apify_provider, serper_provider])
def test_search_adapter_transport_failures_map_to_network(provider) -> None:
    with pytest.raises(ProviderError) as error:
        provider(FixtureTransport([TimeoutError()])).search(legacy_request())

    assert error.value.error_class is ErrorClass.NETWORK
    assert error.value.retryable is True


@pytest.mark.parametrize("provider_type", [ApifyProvider, SerperSearchProvider])
def test_search_adapters_still_require_explicit_transport(provider_type) -> None:
    parameters = inspect.signature(provider_type).parameters

    assert parameters["transport"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["transport"].default is inspect.Parameter.empty
