"""Tests for the C09.2 provider-neutral email draft generation boundary."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.email_draft_generation import (
    GENERATION_VERSION,
    DeterministicEmailDraftGenerator,
)
from chitu_connector.espocrm_sync.enrichment_gate import QualificationDecision, QualificationStatus
from chitu_connector.espocrm_sync.outreach_input_adapter import (
    DeterministicOutreachInputAdapter,
    EvidenceBackedTalkingPoint,
)
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)


def outreach_input():
    score = CanonicalScoreResult(
        accepted=True,
        opportunity_score=82,
        score_tier="A",
        best_first_product="Resin Printer",
        customer_type="DISTRIBUTOR",
        contact_priority="HIGH",
        score_reasons=("FROZEN_CANONICAL_FIXTURE",),
        evidence_refs=("ev-products",),
        component_traces=(),
        validation_errors=(),
        canonical_engine_version="canonical-scoring-v4.0",
        canonical_content_hash="fixture-hash",
        raw_decision={"fixture": True},
        adapter_version="canonical-score-adapter-v1",
        scored_at=NOW,
    )
    return DeterministicOutreachInputAdapter().build(
        {
            "name": "Synthetic Industrial Distributor",
            "addressCountry": "DE",
            "peIndustry": "Additive Manufacturing",
            "peBusinessModel": "B2B Distribution",
        },
        QualificationDecision(QualificationStatus.QUALIFIED, "fixture:qualified", 2),
        score,
        (
            {
                "peEvidenceId": "ev-products",
                "peClaim": "Lists industrial resin printers.",
                "peEvidenceType": "visible_text",
                "peSourceUrl": "https://dealer.example/products",
                "peConfidence": 0.92,
            },
            {
                "peEvidenceId": "ev-about",
                "peClaim": "Operates as a distributor.",
                "peEvidenceType": "title",
                "peSourceUrl": "https://dealer.example/about",
                "peConfidence": 0.9,
            },
        ),
    )


class DeterministicEmailDraftGeneratorTests(TestCase):
    def setUp(self) -> None:
        self.generator = DeterministicEmailDraftGenerator()

    def test_generates_a_deterministic_source_backed_fixture_draft(self) -> None:
        first = self.generator.generate(outreach_input())
        second = self.generator.generate(outreach_input())

        self.assertEqual(first, second)
        self.assertEqual(first.subject, "Synthetic Industrial Distributor: Resin Printer")
        self.assertIn("Operates as a distributor.", first.body)
        self.assertEqual(first.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(first.score_tier, "A")
        self.assertEqual(first.recommended_product, "Resin Printer")
        self.assertEqual(
            tuple(reference.evidence_id for reference in first.evidence_references),
            ("ev-about", "ev-products"),
        )

    def test_rejects_missing_or_incomplete_input_without_a_draft(self) -> None:
        with self.assertRaises(TypeError):
            self.generator.generate(None)  # type: ignore[arg-type]

        incomplete = replace(outreach_input(), company_context=replace(outreach_input().company_context, name=None))
        with self.assertRaisesRegex(ValueError, "company_context.name"):
            self.generator.generate(incomplete)

    def test_rejects_invalid_evidence_before_draft_creation(self) -> None:
        invalid_point = EvidenceBackedTalkingPoint(
            evidence_id="ev-invalid",
            claim="Unsupported claim.",
            evidence_type="visible_text",
            source_url="not-a-url",
            confidence=0.9,
        )
        invalid = replace(outreach_input(), talking_points=(invalid_point,))

        with self.assertRaisesRegex(ValueError, "invalid evidence"):
            self.generator.generate(invalid)

    def test_tracks_generation_version_and_direct_personalization_references(self) -> None:
        draft = self.generator.generate(outreach_input())

        self.assertEqual(draft.generation_version, GENERATION_VERSION)
        self.assertEqual(self.generator.generation_version, GENERATION_VERSION)
        self.assertIn(("company.name", "Synthetic Industrial Distributor"), {(item.field, item.value) for item in draft.personalization_references})
        self.assertIn(("score.recommended_product", "Resin Printer"), {(item.field, item.value) for item in draft.personalization_references})
