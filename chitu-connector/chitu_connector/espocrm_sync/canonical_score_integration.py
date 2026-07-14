"""Single-path bridge from C08 ScoreInput to the canonical scoring owner.

No scoring formula, threshold, or tier definition exists here. The injected
canonical executor is the only component allowed to produce a score result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Any, Mapping, Protocol, Sequence

from chitu_connector.espocrm_sync.score_input_adapter import ScoreInput
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


INTEGRATION_VERSION = "c08-canonical-score-integration-v1"


class CanonicalScoreExecutor(Protocol):
    """Stable invocation seam implemented by the existing canonical scorer."""

    engine_version: str

    def score(self, score_input: ScoreInput) -> CanonicalScoreResult: ...


@dataclass(frozen=True, slots=True)
class CanonicalScoreTrace:
    input_hash: str
    input_evidence_refs: tuple[str, ...]
    qualification_status: str
    canonical_engine_version: str | None
    canonical_content_hash: str | None
    integration_version: str = INTEGRATION_VERSION


@dataclass(frozen=True, slots=True)
class CanonicalScoreDecision:
    """Unmodified canonical result plus C08 input-to-output traceability."""

    result: CanonicalScoreResult
    trace: CanonicalScoreTrace


class CanonicalScoreIntegration:
    """Invoke exactly one canonical scorer for each explicit ScoreInput."""

    def __init__(self, executor: CanonicalScoreExecutor) -> None:
        self.executor = executor

    def evaluate(
        self,
        score_input: ScoreInput,
        research_evidence: Sequence[Mapping[str, Any]],
    ) -> CanonicalScoreDecision:
        if not isinstance(score_input, ScoreInput):
            raise TypeError("score_input must be a ScoreInput")
        result = self.executor.score(score_input)
        if not isinstance(result, CanonicalScoreResult):
            raise TypeError("canonical executor must return CanonicalScoreResult")
        return CanonicalScoreDecision(
            result=result,
            trace=CanonicalScoreTrace(
                input_hash=_score_input_hash(score_input),
                input_evidence_refs=_evidence_refs(research_evidence),
                qualification_status=score_input.qualification_status.value,
                canonical_engine_version=result.canonical_engine_version,
                canonical_content_hash=result.canonical_content_hash,
            ),
        )


def _score_input_hash(score_input: ScoreInput) -> str:
    data = asdict(score_input)
    data["qualification_status"] = score_input.qualification_status.value
    encoded = dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _evidence_refs(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(sorted({str(record["peEvidenceId"]) for record in value if isinstance(record, Mapping) and isinstance(record.get("peEvidenceId"), str) and record["peEvidenceId"]}))
