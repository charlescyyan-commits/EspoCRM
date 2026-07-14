"""Read-only preparation facts for a future outreach owner.

This boundary deliberately prepares no email content and has no CRM, campaign,
provider, or AI dependency.  It retains only direct lead, qualification,
canonical-score, and source-backed evidence facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlparse

from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


ADAPTER_VERSION = "c09-outreach-input-adapter-v1"


@dataclass(frozen=True, slots=True)
class CompanyContext:
    """Direct, compact company facts available from Lead intelligence context."""

    name: str | None
    website_url: str | None
    country: str | None
    industry: str | None
    business_model: str | None
    company_type: str | None


@dataclass(frozen=True, slots=True)
class EvidenceBackedTalkingPoint:
    """A factual claim with the exact source needed to substantiate it."""

    evidence_id: str
    claim: str
    evidence_type: str | None
    source_url: str
    confidence: float | None


@dataclass(frozen=True, slots=True)
class OutreachInput:
    """Stable facts available to a future, separately owned outreach stage."""

    company_context: CompanyContext
    qualification_status: QualificationStatus
    qualification_reason: str
    score_tier: str | None
    recommended_product: str | None
    talking_points: tuple[EvidenceBackedTalkingPoint, ...]
    source_references: tuple[str, ...]
    adapter_version: str = ADAPTER_VERSION


class OutreachInputAdapter(Protocol):
    adapter_version: str

    def build(
        self,
        lead_intelligence_context: Mapping[str, Any],
        qualification: QualificationDecision,
        score_result: CanonicalScoreResult | None,
        research_evidence: Sequence[Mapping[str, Any]],
    ) -> OutreachInput: ...


class DeterministicOutreachInputAdapter:
    """Expose direct preparation facts without interpreting or acting on them."""

    adapter_version = ADAPTER_VERSION

    def build(
        self,
        lead_intelligence_context: Mapping[str, Any],
        qualification: QualificationDecision,
        score_result: CanonicalScoreResult | None,
        research_evidence: Sequence[Mapping[str, Any]],
    ) -> OutreachInput:
        if not isinstance(lead_intelligence_context, Mapping):
            raise TypeError("lead_intelligence_context must be a mapping")
        if not isinstance(qualification, QualificationDecision):
            raise TypeError("qualification must be a QualificationDecision")
        talking_points = _talking_points(research_evidence)
        return OutreachInput(
            company_context=_company_context(lead_intelligence_context),
            qualification_status=qualification.status,
            qualification_reason=qualification.reason,
            score_tier=_score_tier(score_result),
            recommended_product=_recommended_product(score_result),
            talking_points=talking_points,
            source_references=tuple(sorted({point.source_url for point in talking_points})),
        )


def _company_context(context: Mapping[str, Any]) -> CompanyContext:
    return CompanyContext(
        name=_first_text(context, "name", "companyName"),
        website_url=_first_text(context, "website", "websiteUrl"),
        country=_first_text(context, "country", "addressCountry"),
        industry=_first_text(context, "peIndustry", "industry"),
        business_model=_first_text(context, "peBusinessModel", "businessModel"),
        company_type=_first_text(context, "peCompanyType", "companyType"),
    )


def _first_text(context: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _score_tier(score_result: CanonicalScoreResult | None) -> str | None:
    if not isinstance(score_result, CanonicalScoreResult) or not score_result.accepted:
        return None
    return _text(score_result.score_tier)


def _recommended_product(score_result: CanonicalScoreResult | None) -> str | None:
    if not isinstance(score_result, CanonicalScoreResult) or not score_result.accepted:
        return None
    return _text(score_result.best_first_product)


def _talking_points(value: Any) -> tuple[EvidenceBackedTalkingPoint, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    points = {
        (point.evidence_id, point.claim, point.evidence_type, point.source_url, point.confidence): point
        for record in value
        if isinstance(record, Mapping)
        if (point := _talking_point(record)) is not None
    }
    return tuple(
        sorted(
            points.values(),
            key=lambda point: (
                point.evidence_id,
                point.claim,
                point.evidence_type or "",
                point.source_url,
                -1.0 if point.confidence is None else point.confidence,
            ),
        )
    )


def _talking_point(record: Mapping[str, Any]) -> EvidenceBackedTalkingPoint | None:
    evidence_id = _text(record.get("peEvidenceId"))
    claim = _text(record.get("peClaim")) or _text(record.get("peEvidenceText"))
    source_url = _text(record.get("peSourceUrl"))
    if evidence_id is None or claim is None or source_url is None or not _public_http_url(source_url):
        return None
    confidence = record.get("peConfidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        confidence = None
    return EvidenceBackedTalkingPoint(
        evidence_id=evidence_id,
        claim=claim,
        evidence_type=_text(record.get("peEvidenceType")),
        source_url=source_url,
        confidence=float(confidence) if confidence is not None else None,
    )


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _public_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
