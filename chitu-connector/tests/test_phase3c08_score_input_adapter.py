"""Tests for the read-only C08.1 scoring input boundary."""

from __future__ import annotations

from unittest import TestCase

from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus
from chitu_connector.espocrm_sync.score_input_adapter import ADAPTER_VERSION, DeterministicScoreInputAdapter


def evidence(
    evidence_id: str = "ev-products",
    confidence: float = 0.9,
    evidence_type: str = "visible_text",
    source_url: str = "https://dealer.example/products",
) -> dict[str, object]:
    return {
        "id": f"crm-{evidence_id}",
        "peEvidenceId": evidence_id,
        "peEvidenceType": evidence_type,
        "peSourceUrl": source_url,
        "peEvidenceText": "Public website observation.",
        "peConfidence": confidence,
    }


def decision(status: QualificationStatus) -> QualificationDecision:
    return QualificationDecision(status, f"fixture:{status.value}", 0)


class DeterministicScoreInputAdapterTests(TestCase):
    def setUp(self) -> None:
        self.adapter = DeterministicScoreInputAdapter()

    def test_maps_valid_evidence_facts_without_a_score(self) -> None:
        result = self.adapter.build(
            (evidence("ev-products", 0.85, "visible_text"), evidence("ev-title", 0.95, "title")),
            decision(QualificationStatus.QUALIFIED),
        )

        self.assertEqual(result.evidence_count, 2)
        self.assertEqual(result.evidence_confidences, (0.85, 0.95))
        self.assertEqual(result.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(result.evidence_categories, ("title", "visible_text"))
        self.assertEqual(result.source_quality_indicators, ("PUBLIC_HTTP_SOURCE",))
        self.assertEqual(result.adapter_version, ADAPTER_VERSION)
        self.assertNotIn("score", result.__dataclass_fields__)

    def test_maps_empty_evidence_as_facts_only(self) -> None:
        result = self.adapter.build((), decision(QualificationStatus.NOT_READY))

        self.assertEqual(result.evidence_count, 0)
        self.assertEqual(result.evidence_confidences, ())
        self.assertEqual(result.evidence_categories, ())
        self.assertEqual(result.source_quality_indicators, ("NO_SOURCE_EVIDENCE",))
        self.assertEqual(result.qualification_status, QualificationStatus.NOT_READY)

    def test_retains_low_confidence_without_interpreting_it_as_a_score(self) -> None:
        result = self.adapter.build((evidence(confidence=0.35),), decision(QualificationStatus.REVIEW_REQUIRED))

        self.assertEqual(result.evidence_confidences, (0.35,))
        self.assertEqual(result.qualification_status, QualificationStatus.REVIEW_REQUIRED)

    def test_preserves_qualified_and_unqualified_decision_statuses(self) -> None:
        records = (evidence(),)

        qualified = self.adapter.build(records, decision(QualificationStatus.QUALIFIED))
        unqualified = self.adapter.build(records, decision(QualificationStatus.RESEARCH_COMPLETE))

        self.assertEqual(qualified.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(unqualified.qualification_status, QualificationStatus.RESEARCH_COMPLETE)
        self.assertEqual(qualified.evidence_confidences, unqualified.evidence_confidences)

    def test_reports_only_available_source_quality_indicators(self) -> None:
        result = self.adapter.build(
            (evidence("ev-valid"), evidence("ev-missing", source_url="")),
            decision(QualificationStatus.REVIEW_REQUIRED),
        )

        self.assertEqual(result.source_quality_indicators, ("MISSING_OR_INVALID_SOURCE", "PUBLIC_HTTP_SOURCE"))
