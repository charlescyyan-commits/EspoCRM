"""Serializable, versioned domain models with explicit status separation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from chitu_connector.vendored.config.search_sources import SearchSource


SCHEMA_VERSION = "1.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    return value


class SerializableModel:
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


class ProspectState(StrEnum):
    DISCOVERED = "DISCOVERED"
    PRE_SCREENED = "PRE_SCREENED"
    RESEARCH_QUEUED = "RESEARCH_QUEUED"
    RESEARCHING = "RESEARCHING"
    RESEARCHED = "RESEARCHED"
    SCORE_QUEUED = "SCORE_QUEUED"
    SCORING = "SCORING"
    SCORED = "SCORED"
    ENRICHMENT_QUEUED = "ENRICHMENT_QUEUED"
    ENRICHING = "ENRICHING"
    ENRICHED = "ENRICHED"
    OUTREACH_READY = "OUTREACH_READY"
    APPROVED_FOR_CRM = "APPROVED_FOR_CRM"
    SYNCED_TO_ESPO = "SYNCED_TO_ESPO"
    REJECTED_BUSINESS = "REJECTED_BUSINESS"
    FAILED_TECHNICAL = "FAILED_TECHNICAL"
    RETRY_PENDING = "RETRY_PENDING"


class TechnicalStatus(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    HEALTHY = "HEALTHY"
    FAILED = "FAILED"


class BusinessStatus(StrEnum):
    UNASSESSED = "UNASSESSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ResearchDecisionType(StrEnum):
    RESEARCH_NOW = "RESEARCH_NOW"
    RESEARCH_LATER = "RESEARCH_LATER"
    REJECT_BUSINESS = "REJECT_BUSINESS"
    HOLD_TECHNICAL = "HOLD_TECHNICAL"


class EnrichmentDecisionType(StrEnum):
    ALLOW = "ALLOW"
    DENY_LOW_VALUE = "DENY_LOW_VALUE"
    DENY_DUPLICATE = "DENY_DUPLICATE"
    DENY_NOT_RESEARCHED = "DENY_NOT_RESEARCHED"
    DENY_TECHNICAL_FAILURE = "DENY_TECHNICAL_FAILURE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ResearchStatus(StrEnum):
    NOT_RESEARCHED = "NOT_RESEARCHED"
    COMPLETE = "COMPLETE"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"


@dataclass(frozen=True, slots=True)
class ICPDefinition(SerializableModel):
    id: str
    version: str
    product: str
    target_countries: tuple[str, ...]
    customer_types: tuple[str, ...]
    target_brands: tuple[str, ...]
    company_size_min: int | None
    company_size_max: int | None
    include_terms: tuple[str, ...]
    exclude_terms: tuple[str, ...]
    languages: tuple[str, ...]
    source_preferences: tuple[str, ...]
    expected_count: int
    created_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SearchPlan(SerializableModel):
    id: str
    icp_id: str
    source: SearchSource
    query: str
    country: str
    language: str
    quota: int
    priority: int
    rationale: str
    version: str
    schema_version: str = SCHEMA_VERSION


@dataclass(slots=True)
class ProspectingJob(SerializableModel):
    id: str
    icp_id: str
    plan_ids: tuple[str, ...]
    state: ProspectState = ProspectState.DISCOVERED
    created_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION


@dataclass(slots=True)
class Candidate(SerializableModel):
    id: str
    job_id: str
    company_name: str
    raw_url: str
    canonical_domain: str | None
    country: str
    source: SearchSource
    source_url: str
    raw_payload: dict[str, Any]
    pre_screen_score: int | None = None
    research_priority: str | None = None
    current_state: ProspectState = ProspectState.DISCOVERED
    technical_status: TechnicalStatus = TechnicalStatus.NOT_ATTEMPTED
    business_status: BusinessStatus = BusinessStatus.UNASSESSED
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ResearchRecord(SerializableModel):
    candidate_id: str
    status: ResearchStatus
    evidence: tuple[str, ...]
    summary: str
    detected_brands: tuple[str, ...]
    detected_products: tuple[str, ...]
    customer_type: str | None
    researched_at: datetime = field(default_factory=utc_now)
    technical_error: str | None = None
    adapter_version: str = "foundation-mock-v1"
    payload_hash: str = ""
    evidence_schema_version: str = "1.1"
    research_input_hash: str = ""
    research_output_hash: str = ""
    company_country: str | None = None
    company_country_code: str | None = None
    company_country_confidence: float = 0.0
    company_country_evidence_ids: tuple[str, ...] = ()
    company_country_inference: bool = False
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ScoreResult(SerializableModel):
    candidate_id: str
    engine_version: str
    opportunity_score: int
    score_tier: str
    best_first_product: str | None
    cross_sell_path: tuple[str, ...]
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    scored_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class EnrichmentDecision(SerializableModel):
    candidate_id: str
    decision: EnrichmentDecisionType
    reason_codes: tuple[str, ...]
    rule_version: str
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class TechnicalFailure(SerializableModel):
    candidate_id: str
    code: str
    message: str
    retry_eligible: bool
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class BusinessRejection(SerializableModel):
    candidate_id: str
    code: str
    message: str
    retry_eligible: bool = False
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class PreScreenResult(SerializableModel):
    candidate_id: str
    pre_screen_score: int
    research_decision: ResearchDecisionType
    research_priority: str
    reason_codes: tuple[str, ...]
    rule_version: str
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class StateTransitionRecord(SerializableModel):
    candidate_id: str
    previous_state: str
    next_state: str
    timestamp: datetime = field(default_factory=utc_now)
    reason_code: str = ""
    actor: str = ""
    evidence_ref: str = ""
    schema_version: str = SCHEMA_VERSION
