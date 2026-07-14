"""Safe projection of an existing canonical score result to an existing Lead."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol

from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


_PROJECTABLE_FIELDS = frozenset({
    "peOpportunityScoreV4",
    "peScoreTier",
    "peBestFirstProduct",
    "peScoreRulesVersion",
})
_LEAD_SCORE_TIERS = frozenset({"A", "B", "C", "D"})


class LeadScoreProjectionClient(Protocol):
    """Existing-Lead update operation; it intentionally has no create method."""

    def update_lead_score_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]: ...


class ScoreProjectionStatus(StrEnum):
    PROJECTED = "PROJECTED"
    SKIPPED = "SKIPPED"
    DENIED = "DENIED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ScoreProjectionResult:
    status: ScoreProjectionStatus
    lead_id: str | None
    updated_fields: tuple[str, ...] = ()
    reason_code: str | None = None


class CRMScoreProjectionAdapter:
    """Project only direct canonical score fields without CRM side effects elsewhere."""

    def __init__(self, client: LeadScoreProjectionClient) -> None:
        self.client = client

    def project(self, lead_id: str, score_result: CanonicalScoreResult) -> ScoreProjectionResult:
        if not isinstance(lead_id, str) or not lead_id.strip():
            return ScoreProjectionResult(ScoreProjectionStatus.SKIPPED, None, reason_code="INVALID_LEAD_ID")
        fields, reason_code = _projection_fields(score_result)
        if reason_code:
            return ScoreProjectionResult(ScoreProjectionStatus.SKIPPED, lead_id, reason_code=reason_code)
        try:
            self.client.update_lead_score_projection(lead_id, fields)
        except PermissionError:
            return ScoreProjectionResult(ScoreProjectionStatus.DENIED, lead_id, reason_code="CRM_PERMISSION_DENIED")
        except Exception:
            return ScoreProjectionResult(ScoreProjectionStatus.FAILED, lead_id, reason_code="CRM_UPDATE_FAILED")
        return ScoreProjectionResult(ScoreProjectionStatus.PROJECTED, lead_id, tuple(fields))


def _projection_fields(score_result: Any) -> tuple[dict[str, Any], str | None]:
    if not isinstance(score_result, CanonicalScoreResult) or not score_result.accepted:
        return {}, "MISSING_SCORE_DATA"
    score = score_result.opportunity_score
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
        return {}, "MISSING_SCORE_DATA"
    if score_result.score_tier not in _LEAD_SCORE_TIERS:
        return {}, "INVALID_SCORE_TIER"
    version = score_result.canonical_engine_version
    if not isinstance(version, str) or not version.strip():
        return {}, "MISSING_CANONICAL_VERSION"
    fields: dict[str, Any] = {
        "peOpportunityScoreV4": float(score),
        "peScoreTier": score_result.score_tier,
        "peScoreRulesVersion": version,
    }
    product = score_result.best_first_product
    if product is not None:
        if not isinstance(product, str) or len(product) > 255:
            return {}, "INVALID_RECOMMENDATION"
        if product.strip():
            fields["peBestFirstProduct"] = product.strip()
    return fields, None


def allowed_projection_fields() -> frozenset[str]:
    """Expose the allowlist for transport clients and boundary tests."""
    return _PROJECTABLE_FIELDS
