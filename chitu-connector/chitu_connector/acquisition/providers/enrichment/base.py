"""Enrichment capability-port protocol; no provider adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from ..capabilities import Capability, CapabilityDeclaration
from ..cost import CostEnvelope


@dataclass(frozen=True, slots=True)
class EnrichmentRequest:
    request_id: str
    provider_name: str
    entity_type: str
    lookup_key: str
    lookup_type: str
    fields_requested: tuple[str, ...]
    idempotency_key: str = field(repr=False)
    initiating_user: str


@dataclass(frozen=True, slots=True)
class EnrichmentResult:
    provider_name: str
    entity_type: str
    lookup_key: str
    fields: Mapping[str, Any]
    cost: CostEnvelope | None
    capability: Capability = Capability.ENRICHMENT


class EnrichmentProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult: ...
