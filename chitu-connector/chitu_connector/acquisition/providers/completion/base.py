"""Completion capability-port protocol; no provider adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol

from ..capabilities import CapabilityDeclaration
from ..cost import CostEnvelope


class CompletionCapability(Enum):
    """The exhaustive, ratified CompletionProvider capability portfolio."""

    RESEARCH_EVIDENCE = "research_evidence"
    QUALIFICATION_INSIGHT = "qualification_insight"
    DRAFT_ASSISTANCE = "draft_assistance"
    REPLY_ASSISTANCE = "reply_assistance"


_FINISH_REASONS = frozenset({"STOP", "LENGTH", "CONTENT_FILTER"})


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    capability: CompletionCapability
    purpose: str
    prompt: str
    idempotency_key: str = field(repr=False)
    initiating_user: str
    context: Mapping[str, Any] | None = None
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    prompt_template_version: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    completion_id: str
    capability: CompletionCapability
    content: str
    finish_reason: str
    model: str
    cost: CostEnvelope
    prompt_template_version: str | None = None

    def __post_init__(self) -> None:
        if self.finish_reason not in _FINISH_REASONS:
            raise ValueError("finish_reason must be STOP, LENGTH, or CONTENT_FILTER")


class CompletionProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...

    def complete(self, request: CompletionRequest) -> CompletionResult: ...
