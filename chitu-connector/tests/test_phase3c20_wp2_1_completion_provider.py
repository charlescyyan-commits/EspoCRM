from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

from chitu_connector.acquisition.providers.capabilities import Capability, CapabilityDeclaration
from chitu_connector.acquisition.providers.completion import (
    CompletionCapability,
    CompletionProvider,
    CompletionRequest,
    CompletionResult,
)
from chitu_connector.acquisition.providers.cost import CostEnvelope


def test_completion_port_is_limited_to_the_ratified_capabilities() -> None:
    request = CompletionRequest(
        capability=CompletionCapability.REPLY_ASSISTANCE,
        purpose="classify an operator-selected reply",
        prompt="Use the approved template.",
        idempotency_key="idem-001",
        initiating_user="operator-001",
    )
    result = CompletionResult(
        completion_id="completion-001",
        capability=CompletionCapability.REPLY_ASSISTANCE,
        content="classification only",
        finish_reason="STOP",
        model="fixture-model",
        cost=CostEnvelope(10, 4, "fixture-model", 18, "provider-request-001"),
    )

    assert result.cost.provider_request_id == "provider-request-001"
    assert "idem-001" not in repr(request)
    assert tuple(item.name for item in CompletionCapability) == (
        "RESEARCH_EVIDENCE",
        "QUALIFICATION_INSIGHT",
        "DRAFT_ASSISTANCE",
        "REPLY_ASSISTANCE",
    )


def test_completion_protocol_requires_operator_identity_and_has_no_forbidden_capability() -> None:
    parameters = inspect.signature(CompletionRequest).parameters

    assert parameters["initiating_user"].default is inspect.Parameter.empty
    assert {"name", "capabilities", "complete"}.issubset(CompletionProvider.__dict__)
    assert CapabilityDeclaration(Capability.COMPLETION).capability is Capability.COMPLETION

    public_field_names = {
        field.name
        for value_type in (CompletionRequest, CompletionResult)
        for field in fields(value_type)
    }
    enum_names = {item.name for item in CompletionCapability}
    assert not any("credential" in name.lower() or "secret" in name.lower() for name in public_field_names)
    assert not any("SCORE" in name or "EMAIL" in name for name in enum_names)


def test_completion_result_accepts_only_the_authorized_finish_reasons() -> None:
    common = {
        "completion_id": "completion-001",
        "capability": CompletionCapability.REPLY_ASSISTANCE,
        "content": "classification only",
        "model": "fixture-model",
        "cost": CostEnvelope(10, 4, "fixture-model", 18, "provider-request-001"),
    }

    for finish_reason in ("STOP", "LENGTH", "CONTENT_FILTER"):
        assert CompletionResult(finish_reason=finish_reason, **common).finish_reason == finish_reason
    with pytest.raises(ValueError, match="finish_reason"):
        CompletionResult(finish_reason="UNBOUNDED", **common)
