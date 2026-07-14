"""Read-only facts boundary for the canonical scoring owner.

This adapter deliberately does not import, invoke, or implement canonical
scoring. It only normalizes available C07 evidence facts into ``ScoreInput``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlparse

from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus


ADAPTER_VERSION = "c08-score-input-adapter-v1"
_PUBLIC_HTTP_SOURCE = "PUBLIC_HTTP_SOURCE"
_MISSING_OR_INVALID_SOURCE = "MISSING_OR_INVALID_SOURCE"
_NO_SOURCE_EVIDENCE = "NO_SOURCE_EVIDENCE"


@dataclass(frozen=True, slots=True)
class ScoreInput:
    """Evidence facts made available to, but not evaluated by, scoring."""

    evidence_count: int
    evidence_confidences: tuple[float, ...]
    qualification_status: QualificationStatus
    evidence_categories: tuple[str, ...]
    source_quality_indicators: tuple[str, ...]
    adapter_version: str = ADAPTER_VERSION


class ScoreInputAdapter(Protocol):
    adapter_version: str

    def build(
        self,
        research_evidence: Sequence[Mapping[str, Any]],
        qualification: QualificationDecision,
    ) -> ScoreInput: ...


class DeterministicScoreInputAdapter:
    """Map persisted evidence facts without calculating a score or mutating CRM."""

    adapter_version = ADAPTER_VERSION

    def build(
        self,
        research_evidence: Sequence[Mapping[str, Any]],
        qualification: QualificationDecision,
    ) -> ScoreInput:
        if not isinstance(qualification, QualificationDecision):
            raise TypeError("qualification must be a QualificationDecision")
        records = _records(research_evidence)
        confidences = tuple(sorted(_confidence(record) for record in records if _confidence(record) is not None))
        categories = tuple(sorted({value for record in records if isinstance((value := record.get("peEvidenceType")), str) and value.strip()}))
        return ScoreInput(
            evidence_count=len(records),
            evidence_confidences=confidences,
            qualification_status=qualification.status,
            evidence_categories=categories,
            source_quality_indicators=_source_quality_indicators(records),
        )


def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(record for record in value if isinstance(record, Mapping))


def _confidence(record: Mapping[str, Any]) -> float | None:
    value = record.get("peConfidence")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        return None
    return float(value)


def _source_quality_indicators(records: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    if not records:
        return (_NO_SOURCE_EVIDENCE,)
    indicators: set[str] = set()
    for record in records:
        source_url = record.get("peSourceUrl")
        parsed = urlparse(source_url) if isinstance(source_url, str) else None
        if parsed is not None and parsed.scheme in {"http", "https"} and parsed.netloc:
            indicators.add(_PUBLIC_HTTP_SOURCE)
        else:
            indicators.add(_MISSING_OR_INVALID_SOURCE)
    return tuple(sorted(indicators))
