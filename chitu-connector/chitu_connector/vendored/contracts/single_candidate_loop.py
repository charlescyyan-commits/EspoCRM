"""Typed input/output contracts for the single candidate closed loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


class RunMode(StrEnum):
    FULL = "FULL"
    DRY_RUN_PRE_SCREEN = "DRY_RUN_PRE_SCREEN"
    NO_NETWORK = "NO_NETWORK"


@dataclass(frozen=True, slots=True)
class SingleCandidateLoopRequest:
    """All inputs needed to run one candidate through the complete loop."""

    # ICP definition
    product: str
    target_countries: tuple[str, ...]
    customer_types: tuple[str, ...] = ()
    target_brands: tuple[str, ...] = ()
    include_terms: tuple[str, ...] = ()
    exclude_terms: tuple[str, ...] = ()
    languages: tuple[str, ...] = ("en",)
    expected_count: int = 100

    # Candidate identity
    candidate_company_name: str = ""
    candidate_website_url: str = ""
    candidate_country: str = ""
    candidate_source_label: str = "CONTROLLED_MANUAL_INPUT"

    # Research parameters
    expected_customer_types: tuple[str, ...] = ()
    expected_brands: tuple[str, ...] = ()
    expected_products: tuple[str, ...] = ()
    max_pages: int = 8
    timeout_seconds: float = 12.0
    total_timeout_seconds: float = 90.0

    # Control
    force_refresh: bool = False
    run_mode: RunMode = RunMode.FULL

    def __post_init__(self) -> None:
        if not self.product.strip():
            raise ValueError("product is required")
        if not self.target_countries:
            raise ValueError("at least one target country is required")
        if not self.candidate_website_url.strip():
            raise ValueError("candidate_website_url is required")
        if not self.candidate_company_name.strip():
            raise ValueError("candidate_company_name is required")

    @property
    def payload_hash(self) -> str:
        from dataclasses import asdict
        return sha256(dumps(asdict(self), sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SingleCandidateLoopResult:
    """Complete result of one single-candidate loop execution."""

    job_id: str
    candidate_id: str
    run_id: str

    # States
    initial_state: str
    final_state: str
    state_transitions: tuple[dict[str, Any], ...]

    # Identity
    identity_result: dict[str, Any]  # BrandFilterDecision serialized

    # Pre-screen
    pre_screen_result: dict[str, Any] | None

    # Research
    research_decision: str | None
    research_result: dict[str, Any] | None
    evidence_fixture_reference: str | None

    # Score
    v4_score_result: dict[str, Any] | None

    # Enrichment
    enrichment_decision: dict[str, Any] | None

    # Exclusion
    exclusion_result: dict[str, Any] | None  # If excluded at any gate

    # Technical
    technical_failures: tuple[dict[str, Any], ...]

    # Audit
    audit_events: tuple[dict[str, Any], ...]

    # Hashes
    run_hash: str
    started_at: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return _serialize({
            "job_id": self.job_id, "candidate_id": self.candidate_id, "run_id": self.run_id,
            "initial_state": self.initial_state, "final_state": self.final_state,
            "state_transitions": self.state_transitions, "identity_result": self.identity_result,
            "pre_screen_result": self.pre_screen_result, "research_decision": self.research_decision,
            "research_result": self.research_result, "evidence_fixture_reference": self.evidence_fixture_reference,
            "v4_score_result": self.v4_score_result, "enrichment_decision": self.enrichment_decision,
            "exclusion_result": self.exclusion_result, "technical_failures": self.technical_failures,
            "audit_events": self.audit_events, "run_hash": self.run_hash,
            "started_at": self.started_at, "completed_at": self.completed_at,
        })
