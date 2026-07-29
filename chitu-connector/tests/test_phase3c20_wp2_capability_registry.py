from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

from chitu_connector.acquisition.models import ProviderError
from chitu_connector.acquisition.providers.capabilities import Capability
from chitu_connector.acquisition.providers.registry import (
    AdapterRegistration,
    CapabilityRegistry,
    CapabilityResolutionRequest,
    CapabilityResolutionResult,
    ProviderBinding,
    ProviderCandidateEvaluation,
    ProviderHealthState,
)


def registration(provider_id: str, adapter_type: str, capabilities: frozenset[Capability]) -> AdapterRegistration:
    return AdapterRegistration(provider_id, adapter_type, capabilities)


def binding(
    provider_id: str,
    adapter_type: str,
    priority: int,
    capabilities: frozenset[Capability],
    *,
    enabled: bool = True,
    credential_reference: str | None = None,
    health_state: ProviderHealthState = ProviderHealthState.HEALTHY,
    purposes: frozenset[str] = frozenset({"discovery"}),
) -> ProviderBinding:
    return ProviderBinding(
        provider_id=provider_id,
        adapter_type=adapter_type,
        priority=priority,
        enabled=enabled,
        credential_reference=credential_reference or f"crm-ref-{provider_id}",
        supported_capabilities=capabilities,
        health_state=health_state,
        allowed_purposes=purposes,
    )


def request(
    bindings: tuple[ProviderBinding, ...],
    *,
    capability: Capability = Capability.SEARCH,
    purpose: str = "discovery",
    availability: dict[str, bool] | None = None,
    health: dict[str, ProviderHealthState] | None = None,
    context: dict[str, object] | None = None,
) -> CapabilityResolutionRequest:
    credential_availability = availability or {
        candidate.credential_reference: True
        for candidate in bindings
        if candidate.credential_reference
    }
    return CapabilityResolutionRequest(
        capability=capability,
        purpose=purpose,
        allowed_provider_bindings=bindings,
        credential_availability=credential_availability,
        provider_health=health or {},
        policy_version="crm-policy-v1",
        request_context=context or {"request_id": "fixture-request"},
    )


def test_single_available_crm_authorized_provider_resolves() -> None:
    candidate = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry((registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),))

    result = registry.resolve(request((candidate,)))

    assert result.selected_provider_id == "apify"
    assert result.selected_adapter_type == "ApifyProvider"
    assert result.selected_credential_reference == "crm-ref-apify"
    assert result.fallback_occurred is False
    assert result.resolution_reason == "primary eligible candidate selected"


def test_resolution_is_deterministic_by_priority_then_provider_id() -> None:
    apify = binding("apify", "ApifyProvider", 20, frozenset({Capability.SEARCH}))
    serper = binding("serper", "SerperSearchProvider", 10, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    first = registry.resolve(request((apify, serper)))
    second = registry.resolve(request((serper, apify)))

    assert first == second
    assert first.selected_provider_id == "serper"


def test_disabled_provider_is_skipped() -> None:
    primary = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}), enabled=False)
    fallback = binding("serper", "SerperSearchProvider", 20, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    result = registry.resolve(request((primary, fallback)))

    assert result.selected_provider_id == "serper"
    assert result.candidate_evaluations[0].skipped_reason == "PROVIDER_DISABLED"


def test_unavailable_credential_is_skipped() -> None:
    primary = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}))
    fallback = binding("serper", "SerperSearchProvider", 20, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    result = registry.resolve(request((primary, fallback), availability={"crm-ref-apify": False, "crm-ref-serper": True}))

    assert result.selected_provider_id == "serper"
    assert result.candidate_evaluations[0].skipped_reason == "CREDENTIAL_UNAVAILABLE"


def test_unhealthy_provider_is_skipped() -> None:
    primary = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}))
    fallback = binding("serper", "SerperSearchProvider", 20, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    result = registry.resolve(request((primary, fallback), health={"apify": ProviderHealthState.UNHEALTHY}))

    assert result.selected_provider_id == "serper"
    assert result.candidate_evaluations[0].skipped_reason == "PROVIDER_UNHEALTHY"


def test_healthy_provider_precedes_degraded_provider_and_audits_fallback() -> None:
    degraded = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}), health_state=ProviderHealthState.DEGRADED)
    healthy = binding("serper", "SerperSearchProvider", 20, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    result = registry.resolve(request((degraded, healthy)))

    assert result.selected_provider_id == "serper"
    assert result.fallback_occurred is True
    assert "fallback" in result.resolution_reason
    assert result.candidate_evaluations[0].eligible is True
    assert result.candidate_evaluations[0].health_state is ProviderHealthState.DEGRADED


def test_no_available_provider_uses_existing_controlled_provider_error() -> None:
    candidate = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}), enabled=False)
    registry = CapabilityRegistry((registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),))

    with pytest.raises(ProviderError) as raised:
        registry.resolve(request((candidate,)))

    assert raised.value.code == "CAPABILITY_UNAVAILABLE"
    assert raised.value.error_class.value == "PROVIDER"
    assert raised.value.retryable is True
    assert raised.value.candidate_evaluations[0].skipped_reason == "PROVIDER_DISABLED"


def test_registered_but_not_crm_authorized_provider_cannot_be_selected() -> None:
    allowed = binding("serper", "SerperSearchProvider", 10, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    result = registry.resolve(request((allowed,)))

    assert result.selected_provider_id == "serper"


def test_provider_without_requested_capability_cannot_be_selected() -> None:
    candidate = binding("apollo", "ApolloEnrichmentProvider", 10, frozenset({Capability.ENRICHMENT}))
    registry = CapabilityRegistry((registration("apollo", "ApolloEnrichmentProvider", frozenset({Capability.ENRICHMENT})),))

    with pytest.raises(ProviderError) as raised:
        registry.resolve(request((candidate,), capability=Capability.SEARCH))

    assert raised.value.candidate_evaluations[0].skipped_reason == "BINDING_CAPABILITY_UNSUPPORTED"


def test_duplicate_provider_registration_fails_closed() -> None:
    provider = registration("apify", "ApifyProvider", frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry((provider,))

    with pytest.raises(ProviderError) as raised:
        registry.register(provider)

    assert raised.value.code == "DUPLICATE_PROVIDER_ID"
    assert raised.value.error_class.value == "VALIDATION"


def test_purpose_can_resolve_to_different_authorized_provider() -> None:
    discovery = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}), purposes=frozenset({"discovery"}))
    research = binding("serper", "SerperSearchProvider", 10, frozenset({Capability.SEARCH}), purposes=frozenset({"research"}))
    registry = CapabilityRegistry(
        (
            registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),
            registration("serper", "SerperSearchProvider", frozenset({Capability.SEARCH})),
        )
    )

    assert registry.resolve(request((discovery, research), purpose="discovery")).selected_provider_id == "apify"
    assert registry.resolve(request((discovery, research), purpose="research")).selected_provider_id == "serper"


def test_result_and_evaluations_expose_only_safe_registry_metadata() -> None:
    assert {field.name for field in fields(CapabilityResolutionResult)} == {
        "requested_capability", "purpose", "selected_provider_id", "selected_adapter_type", "selected_credential_reference", "policy_version", "candidate_evaluations", "fallback_occurred", "resolution_reason",
    }
    assert {field.name for field in fields(ProviderCandidateEvaluation)} == {
        "provider_id", "eligible", "skipped_reason", "priority", "health_state", "credential_available",
    }
    registry = CapabilityRegistry((registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),))

    with pytest.raises(ProviderError) as raised:
        registry.resolve(request((binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH})),), context={"apiKey": "forbidden"}))

    assert raised.value.code == "SECRET_IN_RESOLUTION_INPUT"
    assert "forbidden" not in str(raised.value)


def test_registry_has_no_network_transport_or_adapter_invocation_surface() -> None:
    source = inspect.getsource(inspect.getmodule(CapabilityRegistry))

    assert "HttpTransport" not in source
    assert ".send(" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib3" not in source
    assert "os.environ" not in source


def test_duplicate_binding_and_unknown_health_are_rejected_or_skipped_safely() -> None:
    candidate = binding("apify", "ApifyProvider", 10, frozenset({Capability.SEARCH}))
    registry = CapabilityRegistry((registration("apify", "ApifyProvider", frozenset({Capability.SEARCH})),))

    with pytest.raises(ProviderError) as duplicate:
        registry.resolve(request((candidate, candidate)))
    assert duplicate.value.code == "DUPLICATE_PROVIDER_BINDING"

    with pytest.raises(ProviderError) as unknown:
        registry.resolve(request((candidate,), health={"apify": ProviderHealthState.UNKNOWN}))
    assert unknown.value.candidate_evaluations[0].skipped_reason == "PROVIDER_HEALTH_UNKNOWN"

    with pytest.raises(ProviderError) as invalid:
        registry.resolve(request((candidate,), health={"apify": "HEALTHY"}))  # type: ignore[dict-item]
    assert invalid.value.code == "INVALID_PROVIDER_HEALTH"
