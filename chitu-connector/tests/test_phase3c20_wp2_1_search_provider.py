from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from chitu_connector.acquisition.models import RawCandidate
from chitu_connector.acquisition.providers.capabilities import Capability
from chitu_connector.acquisition.providers.search import SearchProvider, SearchRequest, SearchResult


def test_search_port_has_an_immutable_idempotent_request_and_normalized_result() -> None:
    request = SearchRequest(
        job_id="job-001",
        provider_name="fixture",
        keyword="industrial 3d printing",
        country="US",
        persona="distributor",
        product="resin",
        result_limit=10,
        idempotency_key="idem-001",
    )
    candidate = RawCandidate("candidate-001", "Fixture Co", None, None, "US", {})
    result = SearchResult("fixture", (candidate,))

    assert result.capability is Capability.SEARCH
    assert "idem-001" not in repr(request)
    with pytest.raises(FrozenInstanceError):
        request.keyword = "mutated"  # type: ignore[misc]


def test_search_protocol_has_only_the_port_contract_members() -> None:
    assert {"name", "capabilities", "search"}.issubset(SearchProvider.__dict__)
    assert tuple(field.name for field in fields(SearchRequest)) == (
        "job_id",
        "provider_name",
        "keyword",
        "country",
        "persona",
        "product",
        "result_limit",
        "idempotency_key",
    )
    assert not any("credential" in field.name.lower() or "secret" in field.name.lower() for field in fields(SearchRequest))
    assert not any("credential" in field.name.lower() or "secret" in field.name.lower() for field in fields(SearchResult))
