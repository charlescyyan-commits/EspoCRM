"""Evidence-gated compatibility contract around the frozen canonical engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from chitu_connector.vendored.contracts.website_research import WebsiteResearchResult


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


@dataclass(frozen=True, slots=True)
class CanonicalScoreRequest:
    research: WebsiteResearchResult
    adapter_version: str = "canonical-score-adapter-v1"


@dataclass(frozen=True, slots=True)
class ScoreComponentTrace:
    component: str
    points: int
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalScoreResult:
    """Compatibility fields are present only after evidence validation succeeds."""

    accepted: bool
    opportunity_score: int | None
    score_tier: str | None
    best_first_product: str | None
    customer_type: str | None
    contact_priority: str | None
    score_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    component_traces: tuple[ScoreComponentTrace, ...]
    validation_errors: tuple[str, ...]
    canonical_engine_version: str | None
    canonical_content_hash: str | None
    raw_decision: dict[str, Any] | None
    adapter_version: str
    scored_at: datetime

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["scored_at"] = self.scored_at.isoformat()
        return data
