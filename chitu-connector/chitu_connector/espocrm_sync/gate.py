"""Fail-closed eligibility gate for the V1 sync payload."""

from __future__ import annotations

from chitu_connector.espocrm_sync.contract import SyncContractPayload, validate_sync_contract
from chitu_connector.espocrm_sync.models import GateDecision, SyncSource


def evaluate_sync_gate(source: SyncSource, payload: SyncContractPayload) -> GateDecision:
    data = payload.to_dict()
    if source.official_brand_excluded or data["provenance"]["official_brand_excluded"]:
        return GateDecision(False, "OFFICIAL_BRAND_EXCLUDED")
    if source.is_business_rejected:
        return GateDecision(False, "REJECTED_BUSINESS")
    if data["research"]["failure_code"] is not None or not data["research"]["website_accessible"]:
        return GateDecision(False, "FAILED_TECHNICAL")
    if data["qualification"]["status"] != "OUTREACH_READY":
        return GateDecision(False, "NOT_OUTREACH_READY")
    if data["score"]["rules_version"] != "canonical-scoring-v4.0":
        return GateDecision(False, "INVALID_SCORE_VERSION")
    if not data["evidence"]:
        return GateDecision(False, "MISSING_EVIDENCE")
    if data["score"]["score_tier"] not in {"A", "B", "C"}:
        return GateDecision(False, "INVALID_SCORE_TIER")
    if not isinstance(data["score"]["value"], (int, float)):
        return GateDecision(False, "MISSING_SCORE")
    if data["score"]["evidence_coverage"] is None or data["score"]["evidence_coverage"] < 0.5:
        return GateDecision(False, "INSUFFICIENT_EVIDENCE_COVERAGE")
    if data["score"]["aggregate_confidence"] is None or data["score"]["aggregate_confidence"] < 0.6:
        return GateDecision(False, "INSUFFICIENT_CONFIDENCE")
    errors = validate_sync_contract(data)
    if errors:
        return GateDecision(False, errors[0])
    return GateDecision(True)
