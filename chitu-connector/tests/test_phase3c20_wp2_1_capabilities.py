from __future__ import annotations

from dataclasses import fields

from chitu_connector.acquisition.providers.capabilities import Capability, CapabilityDeclaration
from chitu_connector.acquisition.providers.completion import CompletionCapability


def test_capability_declaration_defaults_are_conservative() -> None:
    declaration = CapabilityDeclaration(Capability.COMPLETION)

    assert declaration.capability is Capability.COMPLETION
    assert declaration.supports_streaming is False
    assert declaration.supports_json_mode is False
    assert declaration.max_context_tokens is None
    assert declaration.supports_vision is False
    assert tuple(field.name for field in fields(CapabilityDeclaration)) == (
        "capability",
        "supports_streaming",
        "supports_json_mode",
        "max_context_tokens",
        "supports_vision",
    )


def test_capability_enums_are_bounded_to_the_authorized_portfolio() -> None:
    assert tuple(item.value for item in Capability) == ("search", "enrichment", "completion")
    assert tuple(item.value for item in CompletionCapability) == (
        "research_evidence",
        "qualification_insight",
        "draft_assistance",
        "reply_assistance",
        "commercial_brief",
    )

    enum_names = {item.name for item in Capability} | {item.name for item in CompletionCapability}
    assert not any("SCORE" in name or "EMAIL" in name for name in enum_names)
    assert "COMMERCIAL_BRIEF" in enum_names
