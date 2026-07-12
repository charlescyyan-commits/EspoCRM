"""Scoring boundary: no legacy engine is executed in this phase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chitu_connector.vendored.domain.models import Candidate, ResearchRecord, ScoreResult


@dataclass(frozen=True, slots=True)
class ScoreRequest:
    candidate: Candidate
    research: ResearchRecord
    requested_engine_version: str = "decision-engine-candidate-v5.0.0"


class ScoreEngine(Protocol):
    engine_version: str

    def score(self, request: ScoreRequest) -> ScoreResult: ...


class DecisionEngineAdapter:
    """Deliberately unavailable placeholder for the candidate canonical engine."""

    engine_version = "decision-engine-candidate-v5.0.0"

    def score(self, request: ScoreRequest) -> ScoreResult:
        raise RuntimeError("DecisionEngineAdapter is intentionally disabled in Foundation V1")
