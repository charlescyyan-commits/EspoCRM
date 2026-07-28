"""Normalized, provider-neutral invocation cost metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CostEnvelope:
    """Cost and provenance returned by a completed provider invocation."""

    tokens_in: int
    tokens_out: int
    model: str
    latency_ms: int
    provider_request_id: str
    currency: str = "USD"
    amount: float = 0.0
