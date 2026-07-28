from __future__ import annotations

import inspect
import json
import socket
from dataclasses import fields
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from chitu_connector.acquisition.models import ProviderError, ProviderRateLimitError
from chitu_connector.acquisition.providers import Capability, CapabilityDeclaration, HttpRequest, HttpResponse
from chitu_connector.acquisition.providers.enrichment import EnrichmentRequest, EnrichmentResult
from chitu_connector.acquisition.providers.enrichment.adapter import (
    ApolloConfig,
    ApolloEnrichmentProvider,
    HunterConfig,
    HunterEnrichmentProvider,
)


FIXTURES = Path(__file__).parent / "fixtures" / "wp2_2"


class FakeHttpTransport:
    """Fixture-only transport: tests cannot make a real provider request."""

    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def fixture_response(name: str) -> HttpResponse:
    fixture = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    response = fixture["response"]
    return HttpResponse(response["status_code"], response["body"], response.get("headers", {}))


def enrichment_request(
    *,
    entity_type: str = "company",
    lookup_key: str = "example.com",
    lookup_type: str = "domain",
    fields_requested: tuple[str, ...] = ("company_name", "domain", "employees", "industry", "revenue"),
) -> EnrichmentRequest:
    return EnrichmentRequest(
        request_id="wp2-2-a-request",
        provider_name="fixture",
        entity_type=entity_type,
        lookup_key=lookup_key,
        lookup_type=lookup_type,
        fields_requested=fields_requested,
        idempotency_key="wp2-2-a-idempotency-key",
        initiating_user="operator-001",
    )


def apollo(transport: FakeHttpTransport) -> ApolloEnrichmentProvider:
    return ApolloEnrichmentProvider(ApolloConfig("fixture-apollo-key"), transport=transport)


def hunter(transport: FakeHttpTransport) -> HunterEnrichmentProvider:
    return HunterEnrichmentProvider(HunterConfig("fixture-hunter-key"), transport=transport)


class TestApolloEnrichmentProvider:
    def test_company_domain_fixture_is_normalized_and_filtered(self) -> None:
        transport = FakeHttpTransport([fixture_response("apollo_company_domain_lookup.json")])

        result = apollo(transport).enrich(enrichment_request())

        assert result == EnrichmentResult(
            provider_name="APOLLO",
            entity_type="company",
            lookup_key="example.com",
            fields={
                "company_name": "Example Corp",
                "domain": "example.com",
                "employees": 150,
                "industry": "Technology",
                "revenue": 50000000,
            },
            cost=None,
        )
        request = transport.requests[0]
        assert request.method == "POST"
        assert request.url == "https://api.apollo.io/api/v1/organizations/enrich"
        assert request.headers["Idempotency-Key"] == "wp2-2-a-idempotency-key"
        assert json.loads(request.body or b"{}") == {"domain": "example.com"}

    def test_person_email_fixture_is_normalized(self) -> None:
        transport = FakeHttpTransport([fixture_response("apollo_person_email_lookup.json")])

        result = apollo(transport).enrich(
            enrichment_request(
                entity_type="person",
                lookup_key="ada@example.com",
                lookup_type="email",
                fields_requested=("person_name", "title", "email"),
            )
        )

        assert result.fields == {"person_name": "Ada Lovelace", "title": "Engineering Lead", "email": "ada@example.com"}
        assert json.loads(transport.requests[0].body or b"{}") == {"email": "ada@example.com"}

    def test_company_name_uses_the_approved_apollo_name_payload(self) -> None:
        transport = FakeHttpTransport([fixture_response("apollo_company_domain_lookup.json")])

        result = apollo(transport).enrich(
            enrichment_request(lookup_key="Example Corp", lookup_type="name", fields_requested=("company_name",))
        )

        assert result.fields == {"company_name": "Example Corp"}
        assert json.loads(transport.requests[0].body or b"{}") == {"q_organization_name": "Example Corp"}

    @pytest.mark.parametrize("failure", [TimeoutError(), OSError("fixture failure")])
    def test_transport_failures_are_network_errors(self, failure: Exception) -> None:
        with pytest.raises(ProviderError) as raised:
            apollo(FakeHttpTransport([failure])).enrich(enrichment_request())

        assert raised.value.error_class.value == "NETWORK"
        assert raised.value.retryable is True

    @pytest.mark.parametrize(
        ("response", "expected", "retryable"),
        [
            (fixture_response("apollo_error_401.json"), "AUTH", False),
            (fixture_response("apollo_error_429.json"), "RATE_LIMIT", True),
            (HttpResponse(500, {}), "PROVIDER", True),
            (HttpResponse(402, {}), "QUOTA", False),
            (HttpResponse(400, {}), "VALIDATION", False),
        ],
    )
    def test_http_failures_use_shared_taxonomy(self, response: HttpResponse, expected: str, retryable: bool) -> None:
        with pytest.raises(ProviderError) as raised:
            apollo(FakeHttpTransport([response])).enrich(enrichment_request())

        assert raised.value.error_class.value == expected
        assert raised.value.retryable is retryable
        if expected == "RATE_LIMIT":
            assert isinstance(raised.value, ProviderRateLimitError)
            assert raised.value.retry_after == 17


class TestHunterEnrichmentProvider:
    def test_domain_fixture_is_normalized_and_filtered(self) -> None:
        transport = FakeHttpTransport([fixture_response("hunter_domain_lookup.json")])

        result = hunter(transport).enrich(
            enrichment_request(fields_requested=("domain", "company_name", "emails"))
        )

        assert result.fields == {
            "domain": "example.com",
            "company_name": "Example Corp",
            "emails": ["sales@example.com", "info@example.com"],
        }
        request = transport.requests[0]
        assert request.method == "GET"
        assert urlparse(request.url).path == "/v2/domain-search"
        assert parse_qs(urlparse(request.url).query) == {"domain": ["example.com"], "api_key": ["fixture-hunter-key"]}
        assert request.headers["Idempotency-Key"] == "wp2-2-a-idempotency-key"

    def test_email_verification_normalizes_informational_confidence_only(self) -> None:
        transport = FakeHttpTransport([fixture_response("hunter_email_verification.json")])

        result = hunter(transport).enrich(
            enrichment_request(
                entity_type="person",
                lookup_key="ada@example.com",
                lookup_type="email",
                fields_requested=("email", "email_status", "confidence_score"),
            )
        )

        assert result.fields == {"email": "ada@example.com", "email_status": "deliverable", "confidence_score": 92}
        assert "canonical_score" not in result.fields
        assert urlparse(transport.requests[0].url).path == "/v2/email-verifier"

    @pytest.mark.parametrize("failure", [TimeoutError(), OSError("fixture failure")])
    def test_transport_failures_are_network_errors(self, failure: Exception) -> None:
        with pytest.raises(ProviderError) as raised:
            hunter(FakeHttpTransport([failure])).enrich(enrichment_request())

        assert raised.value.error_class.value == "NETWORK"
        assert raised.value.retryable is True

    @pytest.mark.parametrize(
        ("response", "expected", "retryable"),
        [
            (fixture_response("hunter_error_401.json"), "AUTH", False),
            (fixture_response("hunter_error_429.json"), "RATE_LIMIT", True),
            (HttpResponse(500, {}), "PROVIDER", True),
            (HttpResponse(402, {}), "QUOTA", False),
            (HttpResponse(400, {}), "VALIDATION", False),
        ],
    )
    def test_http_failures_use_shared_taxonomy(self, response: HttpResponse, expected: str, retryable: bool) -> None:
        with pytest.raises(ProviderError) as raised:
            hunter(FakeHttpTransport([response])).enrich(enrichment_request())

        assert raised.value.error_class.value == expected
        assert raised.value.retryable is retryable
        if expected == "RATE_LIMIT":
            assert isinstance(raised.value, ProviderRateLimitError)
            assert raised.value.retry_after == 23


class TestEnrichmentValidation:
    @pytest.mark.parametrize("provider", [apollo, hunter])
    @pytest.mark.parametrize(
        "invalid_request",
        [
            enrichment_request(entity_type="lead"),
            enrichment_request(lookup_type="phone"),
            enrichment_request(lookup_key="   "),
        ],
    )
    def test_invalid_requests_are_terminal_and_do_not_send(self, provider, invalid_request: EnrichmentRequest) -> None:
        transport = FakeHttpTransport([])

        with pytest.raises(ProviderError) as raised:
            provider(transport).enrich(invalid_request)

        assert raised.value.error_class.value == "VALIDATION"
        assert raised.value.retryable is False
        assert transport.requests == []

    @pytest.mark.parametrize(
        ("provider", "response"),
        [(apollo, "apollo_company_domain_lookup.json"), (hunter, "hunter_domain_lookup.json")],
    )
    def test_valid_request_returns_enrichment_result(self, provider, response: str) -> None:
        result = provider(FakeHttpTransport([fixture_response(response)])).enrich(enrichment_request())

        assert isinstance(result, EnrichmentResult)
        assert result.capability is Capability.ENRICHMENT
        assert result.cost is None


class TestEnrichmentBoundaries:
    @pytest.mark.parametrize(
        ("provider_type", "config"),
        [(ApolloEnrichmentProvider, ApolloConfig("fixture-apollo-key")), (HunterEnrichmentProvider, HunterConfig("fixture-hunter-key"))],
    )
    def test_explicit_transport_is_required(self, provider_type, config) -> None:
        with pytest.raises(TypeError):
            provider_type(config)

    @pytest.mark.parametrize(
        ("provider", "response"),
        [(apollo, "apollo_company_domain_lookup.json"), (hunter, "hunter_domain_lookup.json")],
    )
    def test_fixture_mode_has_zero_network_egress(self, monkeypatch, provider, response: str) -> None:
        def network_forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
            pytest.fail("fixture transport must not create a network connection")

        monkeypatch.setattr(socket, "create_connection", network_forbidden)
        transport = FakeHttpTransport([fixture_response(response)])

        provider(transport).enrich(enrichment_request())

        assert len(transport.requests) == 1

    @pytest.mark.parametrize(
        ("provider", "response"),
        [(apollo, "apollo_company_domain_lookup.json"), (hunter, "hunter_domain_lookup.json")],
    )
    def test_same_idempotency_key_replays_to_the_same_result(self, provider, response: str) -> None:
        first = provider(FakeHttpTransport([fixture_response(response)])).enrich(enrichment_request())
        second = provider(FakeHttpTransport([fixture_response(response)])).enrich(enrichment_request())

        assert first == second

    def test_capability_contract_and_credential_boundary(self) -> None:
        assert apollo(FakeHttpTransport([])).capabilities == CapabilityDeclaration(Capability.ENRICHMENT, supports_json_mode=True)
        assert hunter(FakeHttpTransport([])).capabilities == CapabilityDeclaration(Capability.ENRICHMENT, supports_json_mode=True)
        assert "fixture-apollo-key" not in repr(ApolloConfig("fixture-apollo-key"))
        assert "fixture-hunter-key" not in repr(HunterConfig("fixture-hunter-key"))
        forbidden = {"api_key", "api_secret", "token", "password", "credential", "credential_reference"}
        assert not ({field.name.casefold() for field in fields(EnrichmentRequest)} & forbidden)
        assert not ({field.name.casefold() for field in fields(EnrichmentResult)} & forbidden)

    def test_public_contract_uses_only_normalized_fields_and_no_default_client(self) -> None:
        adapter_source = inspect.getsource(inspect.getmodule(ApolloEnrichmentProvider))

        assert "os.environ" not in adapter_source
        assert "import requests" not in adapter_source
        assert "import httpx" not in adapter_source
        assert "import urllib3" not in adapter_source
        assert "logging.info" not in adapter_source
        assert "print(" not in adapter_source
        assert tuple(inspect.signature(ApolloEnrichmentProvider.enrich).parameters) == ("self", "request")
        assert tuple(inspect.signature(HunterEnrichmentProvider.enrich).parameters) == ("self", "request")
        assert "Mapping" in str(inspect.signature(EnrichmentResult).parameters["fields"].annotation)
