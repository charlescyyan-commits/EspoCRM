"""Typed, side-effect-free models for the Engine-side EspoCRM sync adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping

from chitu_connector.vendored.contracts.business_qualification import BusinessQualificationResult
from chitu_connector.vendored.contracts.website_research import WebsiteResearchResult
from chitu_connector.vendored.domain.models import Candidate


class AuditStatus(StrEnum):
    READY = "READY"
    SYNCED = "SYNCED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


class MockSyncStatus(StrEnum):
    SUCCESS = "SUCCESS"
    DUPLICATE = "DUPLICATE"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass(frozen=True, slots=True)
class SyncSource:
    candidate: Candidate
    research: WebsiteResearchResult
    score: Mapping[str, Any]
    engine_version: str
    qualification: BusinessQualificationResult | None = None
    qualification_status: str | None = None
    customer_type: str | None = None
    cross_sell_path: tuple[str, ...] = ()
    official_brand_excluded: bool = False
    official_brand_registry_version: str | None = None

    @property
    def effective_qualification_status(self) -> str:
        if self.qualification_status:
            return self.qualification_status
        state = self.candidate.current_state
        return state.value if isinstance(state, StrEnum) else str(state)

    @property
    def effective_customer_type(self) -> str | None:
        if self.customer_type:
            return self.customer_type
        if self.score.get("customer_type"):
            return str(self.score["customer_type"])
        if self.qualification and self.qualification.business_role:
            return self.qualification.business_role
        if self.research.customer_type_candidates:
            return self.research.customer_type_candidates[0].value
        return None

    @property
    def is_business_rejected(self) -> bool:
        state = self.candidate.current_state
        state_value = state.value if isinstance(state, StrEnum) else str(state)
        if state_value == "REJECTED_BUSINESS":
            return True
        if self.qualification and self.qualification.is_excluded:
            return True
        return False


@dataclass(frozen=True, slots=True)
class GateDecision:
    accepted: bool
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class MockSyncResult:
    status: MockSyncStatus
    reason_code: str | None
    lead_id: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class AuditEntry:
    sync_id: str
    idempotency_key: str
    status: AuditStatus
    timestamp: datetime
    payload_hash: str
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class AdapterResult:
    status: AuditStatus
    reason_code: str | None
    lead_id: str | None
    payload: Mapping[str, Any]
    audit_entries: tuple[AuditEntry, ...] = field(default_factory=tuple)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)
