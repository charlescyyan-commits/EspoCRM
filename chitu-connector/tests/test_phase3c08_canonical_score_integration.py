"""Tests for C08.2 single-path canonical score integration."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.canonical_score_integration import CanonicalScoreIntegration
from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus
from chitu_connector.espocrm_sync.score_input_adapter import DeterministicScoreInputAdapter, ScoreInput
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult, ScoreComponentTrace


NOW = datetime(2026, 7, 13, 0, 0, 0, tzinfo=timezone.utc)


def evidence(evidence_id: str, confidence: float, evidence_type: str = "visible_text") -> dict[str, object]:
    return {
        "id": f"crm-{evidence_id}",
        "peEvidenceId": evidence_id,
        "peEvidenceType": evidence_type,
        "peSourceUrl": f"https://dealer.example/{evidence_id}",
        "peEvidenceText": f"Public website evidence {evidence_id}.",
        "peConfidence": confidence,
    }


class FrozenCanonicalExecutor:
    """A fixed-output stand-in for the existing canonical scorer in tests only."""

    engine_version = "canonical-scoring-v4.0"

    def __init__(self) -> None:
        self.calls: list[ScoreInput] = []
        self.result = CanonicalScoreResult(
            accepted=True,
            opportunity_score=82,
            score_tier="A",
            best_first_product="Resin Printer",
            customer_type="DISTRIBUTOR",
            contact_priority="HIGH",
            score_reasons=("FROZEN_CANONICAL_FIXTURE",),
            evidence_refs=("ev-products", "ev-title"),
            component_traces=(ScoreComponentTrace("product-fit", 42, ("ev-products",)),),
            validation_errors=(),
            canonical_engine_version=self.engine_version,
            canonical_content_hash="canonical-fixture-hash",
            raw_decision={"fixture": "frozen-canonical"},
            adapter_version="canonical-score-adapter-v1",
            scored_at=NOW,
        )

    def score(self, score_input: ScoreInput) -> CanonicalScoreResult:
        self.calls.append(score_input)
        return self.result


class CanonicalScoreIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.records = (evidence("ev-products", 0.9), evidence("ev-title", 0.95, "title"))
        self.score_input = DeterministicScoreInputAdapter().build(
            self.records,
            QualificationDecision(QualificationStatus.QUALIFIED, "fixture", 2),
        )
        self.executor = FrozenCanonicalExecutor()
        self.integration = CanonicalScoreIntegration(self.executor)

    def test_same_input_produces_the_same_canonical_score(self) -> None:
        first = self.integration.evaluate(self.score_input, self.records)
        second = self.integration.evaluate(self.score_input, tuple(reversed(self.records)))

        self.assertEqual(first.result, second.result)
        self.assertEqual(first.trace.input_hash, second.trace.input_hash)
        self.assertEqual(first.trace.input_evidence_refs, second.trace.input_evidence_refs)
        self.assertEqual(len(self.executor.calls), 2)

    def test_uses_one_canonical_scoring_path_per_explicit_evaluation(self) -> None:
        decision = self.integration.evaluate(self.score_input, self.records)

        self.assertEqual(len(self.executor.calls), 1)
        self.assertIs(self.executor.calls[0], self.score_input)
        self.assertIs(decision.result, self.executor.result)

    def test_preserves_frozen_result_versions_tiers_and_evidence_traceability(self) -> None:
        decision = self.integration.evaluate(self.score_input, self.records)

        self.assertEqual(decision.result.opportunity_score, 82)
        self.assertEqual(decision.result.score_tier, "A")
        self.assertEqual(decision.result.canonical_engine_version, "canonical-scoring-v4.0")
        self.assertEqual(decision.result.adapter_version, "canonical-score-adapter-v1")
        self.assertEqual(decision.trace.input_evidence_refs, ("ev-products", "ev-title"))
        self.assertEqual(decision.trace.qualification_status, "QUALIFIED")
        self.assertEqual(decision.trace.canonical_content_hash, "canonical-fixture-hash")
