"""Pure, deterministic qualification gate for persisted website evidence.

The gate is deliberately read-only. It does not invoke AI, alter scoring, or
write ProspectPool, Lead, Opportunity, or ResearchEvidence records.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlparse


RULE_VERSION = "c07-enrichment-gate-v1"
_QUALIFICATION_MIN_EVIDENCE = 2
_QUALIFICATION_MIN_AVERAGE_CONFIDENCE = 0.80
_WEBSITE_EVIDENCE_TYPES = frozenset({"title", "meta_description", "visible_text"})


class QualificationStatus(StrEnum):
    NOT_READY = "NOT_READY"
    RESEARCH_COMPLETE = "RESEARCH_COMPLETE"
    QUALIFIED = "QUALIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class QualificationDecision:
    status: QualificationStatus
    reason: str
    evidence_count: int
    rule_version: str = RULE_VERSION


class EnrichmentGate(Protocol):
    rule_version: str

    def evaluate(
        self,
        research_evidence: Sequence[Mapping[str, Any]],
        prospect_pool_context: Mapping[str, Any] | None = None,
    ) -> QualificationDecision: ...


class DeterministicEnrichmentGate:
    """Apply fixed evidence-quality rules without modifying CRM state.

    ``prospect_pool_context`` is accepted for future caller context but has no
    effect on this evidence-only decision and is never mutated.
    """

    rule_version = RULE_VERSION

    def evaluate(
        self,
        research_evidence: Sequence[Mapping[str, Any]],
        prospect_pool_context: Mapping[str, Any] | None = None,
    ) -> QualificationDecision:
        del prospect_pool_context
        records = _records(research_evidence)
        valid, has_invalid = _valid_evidence(records)
        evidence_count = len(valid)
        if not valid:
            return QualificationDecision(
                QualificationStatus.NOT_READY,
                "NO_VALID_WEBSITE_EVIDENCE",
                evidence_count,
            )
        if has_invalid:
            return QualificationDecision(
                QualificationStatus.REVIEW_REQUIRED,
                "INVALID_EVIDENCE_PRESENT",
                evidence_count,
            )
        average_confidence = sum(float(record["peConfidence"]) for record in valid) / evidence_count
        if average_confidence < _QUALIFICATION_MIN_AVERAGE_CONFIDENCE:
            return QualificationDecision(
                QualificationStatus.REVIEW_REQUIRED,
                "LOW_EVIDENCE_CONFIDENCE",
                evidence_count,
            )
        if evidence_count < _QUALIFICATION_MIN_EVIDENCE:
            return QualificationDecision(
                QualificationStatus.RESEARCH_COMPLETE,
                "VALID_WEBSITE_EVIDENCE",
                evidence_count,
            )
        return QualificationDecision(
            QualificationStatus.QUALIFIED,
            "EVIDENCE_QUALITY_THRESHOLD_MET",
            evidence_count,
        )


def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(record for record in value if isinstance(record, Mapping))


def _valid_evidence(records: Sequence[Mapping[str, Any]]) -> tuple[tuple[Mapping[str, Any], ...], bool]:
    valid: dict[str, Mapping[str, Any]] = {}
    has_invalid = len(records) == 0
    for record in records:
        evidence_id = record.get("peEvidenceId")
        if not isinstance(evidence_id, str) or not evidence_id.strip() or not _is_valid_website_evidence(record):
            has_invalid = True
            continue
        candidate = dict(record)
        current = valid.get(evidence_id)
        if current is None or _canonical_record(candidate) < _canonical_record(current):
            valid[evidence_id] = candidate
    ordered = tuple(valid[evidence_id] for evidence_id in sorted(valid))
    return ordered, has_invalid


def _is_valid_website_evidence(record: Mapping[str, Any]) -> bool:
    evidence_type = record.get("peEvidenceType")
    source_url = record.get("peSourceUrl")
    text = record.get("peEvidenceText")
    confidence = record.get("peConfidence")
    parsed = urlparse(source_url) if isinstance(source_url, str) else None
    return (
        isinstance(evidence_type, str)
        and evidence_type in _WEBSITE_EVIDENCE_TYPES
        and parsed is not None
        and parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and isinstance(text, str)
        and bool(text.strip())
        and len(text) <= 1000
        and not isinstance(confidence, bool)
        and isinstance(confidence, (int, float))
        and 0 <= confidence <= 1
    )


def _canonical_record(record: Mapping[str, Any]) -> tuple[str, str, str, float]:
    return (
        str(record.get("peEvidenceType", "")),
        str(record.get("peSourceUrl", "")),
        str(record.get("peEvidenceText", "")),
        float(record.get("peConfidence", 0)),
    )
