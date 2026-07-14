"""Synthetic end-to-end runtime acceptance for C09 outreach preparation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.campaign_projection import CampaignProjectionAdapter, CampaignProjectionStatus
from chitu_connector.espocrm_sync.email_draft_generation import DeterministicEmailDraftGenerator
from chitu_connector.espocrm_sync.enrichment_gate import DeterministicEnrichmentGate, QualificationStatus
from chitu_connector.espocrm_sync.outreach_input_adapter import DeterministicOutreachInputAdapter
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


SYNTHETIC_MARKER = "[C09_RUNTIME_SYNTHETIC]"
SYNTHETIC_LEAD_ID = "synthetic-c09-runtime-existing-lead"
SCORED_AT = datetime(2026, 7, 14, tzinfo=timezone.utc)


class SyntheticExistingLeadTarget:
    """One pre-existing synthetic Lead and explicit forbidden side-effect logs."""

    def __init__(self) -> None:
        self.lead = {
            "id": SYNTHETIC_LEAD_ID,
            "name": f"{SYNTHETIC_MARKER} Industrial Distributor",
            "status": "New",
        }
        self.projection_updates: list[tuple[str, dict[str, Any]]] = []
        self.lead_creations: list[object] = []
        self.opportunity_creations: list[object] = []
        self.email_sends: list[object] = []
        self.campaign_executions: list[object] = []
        self.approvals: list[object] = []
        self.workflow_events: list[object] = []

    def update_lead_campaign_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        if lead_id != self.lead["id"]:
            raise LookupError("synthetic fixture has one existing Lead")
        body = dict(fields)
        self.projection_updates.append((lead_id, body))
        self.lead.update(body)
        return {"id": lead_id, **body}


def synthetic_evidence() -> tuple[dict[str, object], ...]:
    return (
        {
            "peEvidenceId": "ev-c09-about",
            "peEvidenceType": "title",
            "peSourceUrl": "https://c09-runtime-synthetic.example/about",
            "peClaim": f"{SYNTHETIC_MARKER} operates as an industrial distributor.",
            "peEvidenceText": f"{SYNTHETIC_MARKER} operates as an industrial distributor.",
            "peConfidence": 0.92,
        },
        {
            "peEvidenceId": "ev-c09-products",
            "peEvidenceType": "visible_text",
            "peSourceUrl": "https://c09-runtime-synthetic.example/products",
            "peClaim": f"{SYNTHETIC_MARKER} lists industrial resin printers.",
            "peEvidenceText": f"{SYNTHETIC_MARKER} lists industrial resin printers.",
            "peConfidence": 0.90,
        },
    )


def synthetic_score_result() -> CanonicalScoreResult:
    return CanonicalScoreResult(
        accepted=True,
        opportunity_score=82,
        score_tier="A",
        best_first_product="Resin Printer",
        customer_type="DISTRIBUTOR",
        contact_priority="HIGH",
        score_reasons=("FROZEN_CANONICAL_RUNTIME_FIXTURE",),
        evidence_refs=("ev-c09-about", "ev-c09-products"),
        component_traces=(),
        validation_errors=(),
        canonical_engine_version="canonical-scoring-v4.0",
        canonical_content_hash="c09-runtime-canonical-fixture-hash",
        raw_decision={"fixture": "c09-runtime"},
        adapter_version="canonical-score-adapter-v1",
        scored_at=SCORED_AT,
    )


class C09OutreachRuntimeAcceptanceTests(TestCase):
    def test_qualified_intelligence_to_draft_and_existing_lead_projection(self) -> None:
        evidence = synthetic_evidence()
        qualification = DeterministicEnrichmentGate().evaluate(evidence)
        self.assertEqual(qualification.status, QualificationStatus.QUALIFIED)
        self.assertEqual(qualification.evidence_count, 2)

        outreach_input = DeterministicOutreachInputAdapter().build(
            {
                "name": f"{SYNTHETIC_MARKER} Industrial Distributor",
                "website": "https://c09-runtime-synthetic.example",
                "addressCountry": "DE",
                "peIndustry": "Additive Manufacturing",
                "peBusinessModel": "B2B Distribution",
                "peCompanyType": "DISTRIBUTOR",
            },
            qualification,
            synthetic_score_result(),
            evidence,
        )
        self.assertEqual(outreach_input.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(outreach_input.score_tier, "A")
        self.assertEqual(outreach_input.recommended_product, "Resin Printer")
        self.assertEqual(
            tuple(point.evidence_id for point in outreach_input.talking_points),
            ("ev-c09-about", "ev-c09-products"),
        )

        draft = DeterministicEmailDraftGenerator().generate(outreach_input)
        self.assertEqual(draft.subject, f"{SYNTHETIC_MARKER} Industrial Distributor: Resin Printer")
        self.assertIn(f"{SYNTHETIC_MARKER} operates as an industrial distributor.", draft.body)
        self.assertIn("Resin Printer", draft.body)
        self.assertEqual(draft.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(draft.score_tier, "A")
        self.assertEqual(draft.recommended_product, "Resin Printer")
        self.assertEqual(
            tuple(reference.evidence_id for reference in draft.evidence_references),
            ("ev-c09-about", "ev-c09-products"),
        )

        target = SyntheticExistingLeadTarget()
        projection = CampaignProjectionAdapter(target).project(SYNTHETIC_LEAD_ID, draft)
        self.assertEqual(projection.status, CampaignProjectionStatus.PROJECTED)
        self.assertEqual(projection.evidence_reference_count, 2)
        self.assertEqual(projection.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(projection.draft_generation_version, "c09-email-draft-boundary-v1")
        self.assertEqual(
            target.projection_updates,
            [(
                SYNTHETIC_LEAD_ID,
                {
                    "peEmailStatus": "DRAFT_READY",
                    "peEmailCampaignName": "C09 Draft Preparation",
                    "peRecommendedApproach": "Evidence-backed first touch for Resin Printer.",
                },
            )],
        )
        self.assertEqual(target.lead["name"], f"{SYNTHETIC_MARKER} Industrial Distributor")
        self.assertEqual(target.lead["status"], "New")
        self.assertNotIn("body", target.lead)
        self.assertEqual(target.lead_creations, [])
        self.assertEqual(target.opportunity_creations, [])
        self.assertEqual(target.email_sends, [])
        self.assertEqual(target.campaign_executions, [])
        self.assertEqual(target.approvals, [])
        self.assertEqual(target.workflow_events, [])
