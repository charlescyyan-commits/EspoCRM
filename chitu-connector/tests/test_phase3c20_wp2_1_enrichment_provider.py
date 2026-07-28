from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from chitu_connector.acquisition.providers.capabilities import Capability
from chitu_connector.acquisition.providers.cost import CostEnvelope
from chitu_connector.acquisition.providers.enrichment import EnrichmentProvider, EnrichmentRequest, EnrichmentResult


def test_enrichment_port_is_immutable_and_carries_optional_cost_metadata() -> None:
    request = EnrichmentRequest(
        request_id="request-001",
        provider_name="fixture",
        entity_type="company",
        lookup_key="example.invalid",
        lookup_type="domain",
        fields_requested=("industry", "employees"),
        idempotency_key="idem-001",
        initiating_user="operator-001",
    )
    result = EnrichmentResult(
        provider_name="fixture",
        entity_type="company",
        lookup_key="example.invalid",
        fields={"industry": "manufacturing"},
        cost=CostEnvelope(0, 0, "fixture", 12, "request-001"),
    )

    assert result.capability is Capability.ENRICHMENT
    assert "idem-001" not in repr(request)
    with pytest.raises(FrozenInstanceError):
        request.lookup_key = "mutated.invalid"  # type: ignore[misc]


def test_enrichment_protocol_does_not_expose_credentials_or_vendor_types() -> None:
    assert {"name", "capabilities", "enrich"}.issubset(EnrichmentProvider.__dict__)

    public_field_names = {
        field.name
        for value_type in (EnrichmentRequest, EnrichmentResult)
        for field in fields(value_type)
    }
    assert not any("credential" in name.lower() or "secret" in name.lower() for name in public_field_names)
    assert not any("apollo" in name.lower() or "hunter" in name.lower() for name in public_field_names)
