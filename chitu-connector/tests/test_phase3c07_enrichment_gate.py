"""Offline tests for deterministic C07.3 enrichment qualification."""

from __future__ import annotations

from copy import deepcopy
from unittest import TestCase

from chitu_connector.espocrm_sync.enrichment_gate import (
    DeterministicEnrichmentGate,
    QualificationStatus,
    RULE_VERSION,
)


def evidence_record(
    evidence_id: str = "ev-products",
    confidence: float = 0.9,
    **overrides: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": f"crm-{evidence_id}",
        "peEvidenceId": evidence_id,
        "peEvidenceType": "visible_text",
        "peSourceUrl": "https://dealer.example/products",
        "peEvidenceText": "The public product page lists industrial resin printers.",
        "peConfidence": confidence,
    }
    record.update(overrides)
    return record


class DeterministicEnrichmentGateTests(TestCase):
    def setUp(self) -> None:
        self.gate = DeterministicEnrichmentGate()

    def test_empty_evidence_is_not_ready(self) -> None:
        decision = self.gate.evaluate(())

        self.assertEqual(decision.status, QualificationStatus.NOT_READY)
        self.assertEqual(decision.reason, "NO_VALID_WEBSITE_EVIDENCE")
        self.assertEqual(decision.evidence_count, 0)
        self.assertEqual(decision.rule_version, RULE_VERSION)

    def test_one_valid_website_evidence_marks_research_complete(self) -> None:
        decision = self.gate.evaluate((evidence_record(),), {"id": "pool-1", "researchStatus": "COMPLETED"})

        self.assertEqual(decision.status, QualificationStatus.RESEARCH_COMPLETE)
        self.assertEqual(decision.reason, "VALID_WEBSITE_EVIDENCE")
        self.assertEqual(decision.evidence_count, 1)

    def test_two_high_quality_website_evidence_records_qualify(self) -> None:
        decision = self.gate.evaluate((evidence_record(), evidence_record("ev-contact", 0.85)))

        self.assertEqual(decision.status, QualificationStatus.QUALIFIED)
        self.assertEqual(decision.reason, "EVIDENCE_QUALITY_THRESHOLD_MET")
        self.assertEqual(decision.evidence_count, 2)

    def test_low_confidence_evidence_requires_review(self) -> None:
        decision = self.gate.evaluate((evidence_record(confidence=0.55),))

        self.assertEqual(decision.status, QualificationStatus.REVIEW_REQUIRED)
        self.assertEqual(decision.reason, "LOW_EVIDENCE_CONFIDENCE")
        self.assertEqual(decision.evidence_count, 1)

    def test_mixed_confidence_evidence_requires_review(self) -> None:
        decision = self.gate.evaluate((evidence_record("ev-products", 0.95), evidence_record("ev-contact", 0.45)))

        self.assertEqual(decision.status, QualificationStatus.REVIEW_REQUIRED)
        self.assertEqual(decision.reason, "LOW_EVIDENCE_CONFIDENCE")
        self.assertEqual(decision.evidence_count, 2)

    def test_repeated_evaluation_is_identical_and_does_not_mutate_context(self) -> None:
        evidence = (evidence_record(), evidence_record("ev-contact", 0.85))
        context = {"id": "pool-1", "qualificationStatus": "PENDING"}
        original_context = deepcopy(context)

        first = self.gate.evaluate(evidence, context)
        second = self.gate.evaluate(tuple(reversed(evidence)), context)

        self.assertEqual(first, second)
        self.assertEqual(context, original_context)
