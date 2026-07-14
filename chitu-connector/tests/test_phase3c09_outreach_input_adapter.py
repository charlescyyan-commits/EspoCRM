"""Tests for the C09.1 read-only outreach preparation input boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus
from chitu_connector.espocrm_sync.outreach_input_adapter import ADAPTER_VERSION, DeterministicOutreachInputAdapter
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)


def lead_context() -> dict[str, object]:
    return {
        "name": "Synthetic Industrial Distributor",
        "website": "https://dealer.example",
        "addressCountry": "DE",
        "peIndustry": "Additive Manufacturing",
        "peBusinessModel": "B2B Distribution",
        "peCompanyType": "DISTRIBUTOR",
    }


def evidence(evidence_id: str, *, claim: str, source_url: str, confidence: float = 0.9) -> dict[str, object]:
    return {
        "peEvidenceId": evidence_id,
        "peClaim": claim,
        "peEvidenceType": "visible_text",
        "peSourceUrl": source_url,
        "peEvidenceText": f"Evidence text for {claim}",
        "peConfidence": confidence,
    }


def decision(status: QualificationStatus) -> QualificationDecision:
    return QualificationDecision(status, f"fixture:{status.value}", 2)


def score_result(**overrides: object) -> CanonicalScoreResult:
    values: dict[str, object] = {
        "accepted": True,
        "opportunity_score": 82,
        "score_tier": "A",
        "best_first_product": "Resin Printer",
        "customer_type": "DISTRIBUTOR",
        "contact_priority": "HIGH",
        "score_reasons": ("FROZEN_CANONICAL_FIXTURE",),
        "evidence_refs": ("ev-products",),
        "component_traces": (),
        "validation_errors": (),
        "canonical_engine_version": "canonical-scoring-v4.0",
        "canonical_content_hash": "fixture-hash",
        "raw_decision": {"fixture": True},
        "adapter_version": "canonical-score-adapter-v1",
        "scored_at": NOW,
    }
    values.update(overrides)
    return CanonicalScoreResult(**values)  # type: ignore[arg-type]


class DeterministicOutreachInputAdapterTests(TestCase):
    def setUp(self) -> None:
        self.adapter = DeterministicOutreachInputAdapter()

    def test_maps_qualified_lead_to_source_backed_business_preparation_facts(self) -> None:
        result = self.adapter.build(
            lead_context(),
            decision(QualificationStatus.QUALIFIED),
            score_result(),
            (
                evidence("ev-products", claim="Lists industrial resin printers.", source_url="https://dealer.example/products"),
                evidence("ev-about", claim="Operates as a distributor.", source_url="https://dealer.example/about", confidence=0.95),
            ),
        )

        self.assertEqual(result.company_context.name, "Synthetic Industrial Distributor")
        self.assertEqual(result.company_context.country, "DE")
        self.assertEqual(result.company_context.industry, "Additive Manufacturing")
        self.assertEqual(result.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(result.score_tier, "A")
        self.assertEqual(result.recommended_product, "Resin Printer")
        self.assertEqual(tuple(point.evidence_id for point in result.talking_points), ("ev-about", "ev-products"))
        self.assertEqual(result.source_references, ("https://dealer.example/about", "https://dealer.example/products"))
        self.assertEqual(result.adapter_version, ADAPTER_VERSION)

    def test_preserves_unqualified_status_without_declaring_outreach_readiness(self) -> None:
        result = self.adapter.build(
            lead_context(),
            decision(QualificationStatus.REVIEW_REQUIRED),
            score_result(),
            (evidence("ev-products", claim="Lists products.", source_url="https://dealer.example/products"),),
        )

        self.assertEqual(result.qualification_status, QualificationStatus.REVIEW_REQUIRED)
        self.assertEqual(result.qualification_reason, "fixture:REVIEW_REQUIRED")
        self.assertNotIn("outreach_ready", result.__dataclass_fields__)

    def test_missing_evidence_produces_no_talking_points_or_source_references(self) -> None:
        result = self.adapter.build(lead_context(), decision(QualificationStatus.NOT_READY), score_result(), ())

        self.assertEqual(result.talking_points, ())
        self.assertEqual(result.source_references, ())
        self.assertEqual(result.qualification_status, QualificationStatus.NOT_READY)

    def test_missing_or_unaccepted_score_has_no_tier_or_recommendation(self) -> None:
        records = (evidence("ev-products", claim="Lists products.", source_url="https://dealer.example/products"),)

        missing = self.adapter.build(lead_context(), decision(QualificationStatus.QUALIFIED), None, records)
        unaccepted = self.adapter.build(
            lead_context(),
            decision(QualificationStatus.QUALIFIED),
            score_result(accepted=False, score_tier=None, best_first_product=None),
            records,
        )

        self.assertEqual((missing.score_tier, missing.recommended_product), (None, None))
        self.assertEqual((unaccepted.score_tier, unaccepted.recommended_product), (None, None))

    def test_output_is_deterministic_and_deduplicates_identical_source_backed_facts(self) -> None:
        records = (
            evidence("ev-products", claim="Lists products.", source_url="https://dealer.example/products"),
            evidence("ev-about", claim="Operates as a distributor.", source_url="https://dealer.example/about", confidence=0.95),
            evidence("ev-products", claim="Lists products.", source_url="https://dealer.example/products"),
        )

        first = self.adapter.build(lead_context(), decision(QualificationStatus.QUALIFIED), score_result(), records)
        second = self.adapter.build(lead_context(), decision(QualificationStatus.QUALIFIED), score_result(), tuple(reversed(records)))

        self.assertEqual(first, second)
        self.assertEqual(len(first.talking_points), 2)
