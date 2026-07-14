"""Tests for safe C09.3 draft-preparation projection to an existing Lead."""

from __future__ import annotations

from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.campaign_projection import (
    CampaignProjectionAdapter,
    CampaignProjectionStatus,
)
from chitu_connector.espocrm_sync.email_draft_generation import (
    DraftEvidenceReference,
    EmailDraft,
    PersonalizationReference,
)
from chitu_connector.espocrm_sync.enrichment_gate import QualificationStatus


class FakeCampaignProjectionClient:
    def __init__(self, *, permission_denied: bool = False) -> None:
        self.permission_denied = permission_denied
        self.update_calls: list[tuple[str, dict[str, Any]]] = []
        self.lead_creations: list[object] = []
        self.opportunity_creations: list[object] = []
        self.email_sends: list[object] = []
        self.approvals: list[object] = []
        self.workflow_events: list[object] = []

    def update_lead_campaign_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        if self.permission_denied:
            raise PermissionError("campaign preparation fields are read-only")
        self.update_calls.append((lead_id, dict(fields)))
        return {"id": lead_id, **fields}


def email_draft() -> EmailDraft:
    return EmailDraft(
        subject="Synthetic Industrial Distributor: Resin Printer",
        body="Hello Synthetic Industrial Distributor,\n\nI noticed: Operates as a distributor.",
        personalization_references=(PersonalizationReference("company.name", "Synthetic Industrial Distributor"),),
        evidence_references=(
            DraftEvidenceReference("ev-about", "https://dealer.example/about"),
            DraftEvidenceReference("ev-products", "https://dealer.example/products"),
        ),
        qualification_status=QualificationStatus.QUALIFIED,
        qualification_reason="fixture:qualified",
        score_tier="A",
        recommended_product="Resin Printer",
        generation_version="c09-email-draft-boundary-v1",
    )


class CampaignProjectionAdapterTests(TestCase):
    def setUp(self) -> None:
        self.client = FakeCampaignProjectionClient()
        self.adapter = CampaignProjectionAdapter(self.client)

    def test_projects_only_existing_lead_draft_preparation_fields(self) -> None:
        result = self.adapter.project("lead-123", email_draft())

        self.assertEqual(result.status, CampaignProjectionStatus.PROJECTED)
        self.assertEqual(result.updated_fields, ("peEmailStatus", "peEmailCampaignName", "peRecommendedApproach"))
        self.assertEqual(result.draft_generation_version, "c09-email-draft-boundary-v1")
        self.assertEqual(result.evidence_reference_count, 2)
        self.assertEqual(result.qualification_status, QualificationStatus.QUALIFIED)
        self.assertEqual(
            self.client.update_calls,
            [(
                "lead-123",
                {
                    "peEmailStatus": "DRAFT_READY",
                    "peEmailCampaignName": "C09 Draft Preparation",
                    "peRecommendedApproach": "Evidence-backed first touch for Resin Printer.",
                },
            )],
        )

    def test_permission_denial_does_not_retry_or_trigger_side_effects(self) -> None:
        client = FakeCampaignProjectionClient(permission_denied=True)
        result = CampaignProjectionAdapter(client).project("lead-123", email_draft())

        self.assertEqual(result.status, CampaignProjectionStatus.DENIED)
        self.assertEqual(result.reason_code, "CRM_PERMISSION_DENIED")
        self.assertEqual(client.update_calls, [])
        self.assertEqual(client.lead_creations, [])
        self.assertEqual(client.opportunity_creations, [])
        self.assertEqual(client.email_sends, [])
        self.assertEqual(client.approvals, [])
        self.assertEqual(client.workflow_events, [])

    def test_never_projects_draft_content_or_unrelated_lead_fields(self) -> None:
        self.adapter.project("lead-123", email_draft())

        fields = self.client.update_calls[0][1]
        self.assertEqual(set(fields), {"peEmailStatus", "peEmailCampaignName", "peRecommendedApproach"})
        self.assertNotIn("subject", fields)
        self.assertNotIn("body", fields)
        self.assertNotIn("peLastEmailDate", fields)
        self.assertNotIn("peEmailReplyStatus", fields)
        self.assertNotIn("peOpportunityScoreV4", fields)
        self.assertNotIn("peResearchSummary", fields)
        self.assertNotIn("status", fields)
