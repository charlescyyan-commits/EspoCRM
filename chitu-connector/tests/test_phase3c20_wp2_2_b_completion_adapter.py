from __future__ import annotations

import inspect
import json
import socket
from dataclasses import fields
from pathlib import Path

import pytest

from chitu_connector.acquisition.models import ProviderError, ProviderRateLimitError
from chitu_connector.acquisition.providers import Capability, CapabilityDeclaration, HttpRequest, HttpResponse
from chitu_connector.acquisition.providers.completion import CompletionCapability, CompletionRequest, CompletionResult
from chitu_connector.acquisition.providers.completion.adapter import CompletionBridgeProvider, CompletionConfig
from chitu_connector.acquisition.providers.cost import CostEnvelope


FIXTURES = Path(__file__).parent / "fixtures" / "wp2_2"


class FakeHttpTransport:
    """In-memory fixture transport; it contains no network implementation."""

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


def completion_request(
    capability: CompletionCapability = CompletionCapability.RESEARCH_EVIDENCE,
    **overrides,
) -> CompletionRequest:
    values = {
        "capability": capability,
        "purpose": "Provide an operator-reviewable summary",
        "prompt": "Summarize the supplied material.",
        "idempotency_key": "wp2-2-b-idempotency-key",
        "initiating_user": "operator-001",
        "context": {"evidence": "fixture evidence"},
        "prompt_template_version": "fixture-template-v1",
    }
    values.update(overrides)
    return CompletionRequest(**values)


def bridge(transport: FakeHttpTransport) -> CompletionBridgeProvider:
    return CompletionBridgeProvider(
        CompletionConfig("fixture-completion-key", "https://fixture.completion.invalid", "fixture-default-model"),
        transport=transport,
    )


class TestCompletionProviderHappyPath:
    @pytest.mark.parametrize(
        ("capability", "fixture", "expected_finish"),
        [
            (CompletionCapability.RESEARCH_EVIDENCE, "completion_research_evidence.json", "STOP"),
            (CompletionCapability.QUALIFICATION_INSIGHT, "completion_qualification_insight.json", "LENGTH"),
            (CompletionCapability.DRAFT_ASSISTANCE, "completion_draft_assistance.json", "STOP"),
            (CompletionCapability.REPLY_ASSISTANCE, "completion_reply_assistance.json", "CONTENT_FILTER"),
        ],
    )
    def test_each_authorized_capability_replays_a_fixture(
        self,
        capability: CompletionCapability,
        fixture: str,
        expected_finish: str,
    ) -> None:
        result = bridge(FakeHttpTransport([fixture_response(fixture)])).complete(completion_request(capability))

        assert result.capability is capability
        assert result.finish_reason == expected_finish
        assert result.content
        assert result.prompt_template_version == "fixture-template-v1"

    def test_context_and_operator_attribution_are_in_the_bridge_request(self) -> None:
        transport = FakeHttpTransport([fixture_response("completion_research_evidence.json")])

        bridge(transport).complete(completion_request())

        request = transport.requests[0]
        body = json.loads(request.body or b"{}")
        assert request.method == "POST"
        assert request.url == "https://fixture.completion.invalid/chat/completions"
        assert request.headers["Idempotency-Key"] == "wp2-2-b-idempotency-key"
        assert body["metadata"] == {"initiating_user": "operator-001"}
        assert "fixture evidence" in body["messages"][0]["content"]


class TestCompletionProviderErrorTaxonomy:
    @pytest.mark.parametrize("failure", [TimeoutError(), OSError("fixture failure")])
    def test_transport_failures_are_network_errors(self, failure: Exception) -> None:
        with pytest.raises(ProviderError) as raised:
            bridge(FakeHttpTransport([failure])).complete(completion_request())

        assert raised.value.error_class.value == "NETWORK"
        assert raised.value.retryable is True

    @pytest.mark.parametrize(
        ("response", "expected", "retryable"),
        [
            (HttpResponse(401, {}), "AUTH", False),
            (HttpResponse(403, {}), "AUTH", False),
            (fixture_response("completion_error_429.json"), "RATE_LIMIT", True),
            (HttpResponse(500, {}), "PROVIDER", True),
            (HttpResponse(502, {}), "PROVIDER", True),
            (HttpResponse(402, {}), "QUOTA", False),
            (HttpResponse(400, {"error": "invalid request"}), "VALIDATION", False),
            (fixture_response("completion_error_content_filter.json"), "CONTENT_FILTER", False),
        ],
    )
    def test_http_failures_are_normalized(self, response: HttpResponse, expected: str, retryable: bool) -> None:
        with pytest.raises(ProviderError) as raised:
            bridge(FakeHttpTransport([response])).complete(completion_request())

        assert raised.value.error_class.value == expected
        assert raised.value.retryable is retryable
        if expected == "RATE_LIMIT":
            assert isinstance(raised.value, ProviderRateLimitError)
            assert raised.value.retry_after == 29


class TestCompletionProviderCostEnvelope:
    def test_cost_metadata_is_complete_and_pricing_is_deferred(self) -> None:
        result = bridge(FakeHttpTransport([fixture_response("completion_research_evidence.json")])).complete(completion_request())

        assert isinstance(result.cost, CostEnvelope)
        assert result.cost.tokens_in == 31
        assert result.cost.tokens_out == 9
        assert result.cost.model == "fixture-model"
        assert result.cost.latency_ms > 0
        assert result.cost.provider_request_id == "fixture-research-request"
        assert result.cost.currency == "USD"
        assert result.cost.amount == 0.0


class TestCompletionProviderFinishReason:
    @pytest.mark.parametrize("finish_reason", ["STOP", "LENGTH", "CONTENT_FILTER"])
    def test_contract_accepts_the_three_normalized_finish_reasons(self, finish_reason: str) -> None:
        result = CompletionResult(
            completion_id="fixture-completion",
            capability=CompletionCapability.RESEARCH_EVIDENCE,
            content="fixture",
            finish_reason=finish_reason,
            model="fixture-model",
            cost=CostEnvelope(1, 1, "fixture-model", 1, "fixture-request"),
        )

        assert result.finish_reason == finish_reason

    def test_contract_rejects_an_unknown_finish_reason(self) -> None:
        with pytest.raises(ValueError):
            CompletionResult(
                completion_id="fixture-completion",
                capability=CompletionCapability.RESEARCH_EVIDENCE,
                content="fixture",
                finish_reason="VENDOR_VALUE",
                model="fixture-model",
                cost=CostEnvelope(1, 1, "fixture-model", 1, "fixture-request"),
            )


class TestCompletionProviderForbiddenCapabilities:
    def test_capability_port_remains_exactly_the_ratified_four(self) -> None:
        assert {item.value for item in CompletionCapability} == {
            "research_evidence",
            "qualification_insight",
            "draft_assistance",
            "reply_assistance",
        }

    def test_adapter_has_no_chitu_lifecycle_or_delivery_dependencies(self) -> None:
        adapter_source = inspect.getsource(inspect.getmodule(CompletionBridgeProvider))
        forbidden = (
            "canonical_score",
            "scoring",
            "AIScore",
            "website_research",
            "single_candidate_loop",
            "icp",
            "email_generation",
            "send_email",
            "EmailDelivery",
            "ProspectPool",
            "SendExecution",
            "ReplyEvent",
            "transition",
            "vendored.contracts",
            "espocrm_sync",
        )

        assert all(term not in adapter_source for term in forbidden)

    def test_completion_contract_has_no_credential_fields_or_vendor_public_types(self) -> None:
        forbidden = {"api_key", "api_secret", "token", "password", "credential", "credential_reference"}

        assert not ({field.name.casefold() for field in fields(CompletionRequest)} & forbidden)
        assert not ({field.name.casefold() for field in fields(CompletionResult)} & forbidden)
        assert tuple(inspect.signature(CompletionBridgeProvider.complete).parameters) == ("self", "request")


class TestCompletionProviderTransportBoundary:
    def test_explicit_transport_is_required(self) -> None:
        config = CompletionConfig("fixture-completion-key", "https://fixture.completion.invalid", "fixture-default-model")

        with pytest.raises(TypeError):
            CompletionBridgeProvider(config)

    def test_fixture_transport_has_zero_network_egress(self, monkeypatch) -> None:
        def network_forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
            pytest.fail("fixture transport must not create a network connection")

        monkeypatch.setattr(socket, "create_connection", network_forbidden)
        transport = FakeHttpTransport([fixture_response("completion_research_evidence.json")])

        bridge(transport).complete(completion_request())

        assert len(transport.requests) == 1

    def test_capability_declaration_configuration_and_idempotency_are_bounded(self) -> None:
        first = bridge(FakeHttpTransport([fixture_response("completion_research_evidence.json")])).complete(completion_request())
        second = bridge(FakeHttpTransport([fixture_response("completion_research_evidence.json")])).complete(completion_request())

        assert bridge(FakeHttpTransport([])).capabilities == CapabilityDeclaration(Capability.COMPLETION, supports_json_mode=True)
        assert first == second
        assert "fixture-completion-key" not in repr(
            CompletionConfig("fixture-completion-key", "https://fixture.completion.invalid", "fixture-default-model")
        )

    @pytest.mark.parametrize(
        "invalid_request",
        [
            completion_request(initiating_user=" "),
            completion_request(purpose=" "),
            completion_request(prompt=" "),
        ],
    )
    def test_unattributed_or_empty_requests_are_rejected_before_transport(self, invalid_request: CompletionRequest) -> None:
        transport = FakeHttpTransport([])

        with pytest.raises(ProviderError) as raised:
            bridge(transport).complete(invalid_request)

        assert raised.value.error_class.value == "VALIDATION"
        assert raised.value.retryable is False
        assert transport.requests == []

    def test_adapter_has_no_default_http_client_or_logging_surface(self) -> None:
        adapter_source = inspect.getsource(inspect.getmodule(CompletionBridgeProvider))

        assert "os.environ" not in adapter_source
        assert "import requests" not in adapter_source
        assert "import httpx" not in adapter_source
        assert "import urllib3" not in adapter_source
        assert "logging.info" not in adapter_source
        assert "print(" not in adapter_source
