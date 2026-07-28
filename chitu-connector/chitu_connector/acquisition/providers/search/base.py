"""Search capability-port protocol; no provider adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ...models import RawCandidate
from ..capabilities import Capability, CapabilityDeclaration


@dataclass(frozen=True, slots=True)
class SearchRequest:
    job_id: str
    provider_name: str
    keyword: str
    country: str | None
    persona: str | None
    product: str | None
    result_limit: int
    idempotency_key: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class SearchResult:
    provider_name: str
    candidates: tuple[RawCandidate, ...]
    capability: Capability = Capability.SEARCH


class SearchProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...

    def search(self, request: SearchRequest) -> SearchResult: ...
