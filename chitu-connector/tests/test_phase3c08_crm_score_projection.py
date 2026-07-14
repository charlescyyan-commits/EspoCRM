"""Tests for safe C08.3 canonical-score projection to an existing Lead."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.crm_score_projection import CRMScoreProjectionAdapter, ScoreProjectionStatus
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult


NOW = datetime(2026, 7, 13, tzinfo=timezone.utc)


class FakeLeadProjectionClient:
    def __init__(self, *, permission_denied: bool = False) -> None:
        self.permission_denied = permission_denied
        self.update_calls: list[tuple[str, dict[str, Any]]] = []
        self.lead_creations: list[object] = []
        self.opportunity_creations: list[object] = []
        self.email_sends: list[object] = []

    def update_lead_score_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        if self.permission_denied:
            raise PermissionError("score fields are read-only")
        self.update_calls.append((lead_id, dict(fields)))
        return {"id": lead_id, **fields}


def score_result(**overrides: Any) -> CanonicalScoreResult:
    values = {
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
    return CanonicalScoreResult(**values)


class CRMScoreProjectionAdapterTests(TestCase):
    def setUp(self) -> None:
        self.client = FakeLeadProjectionClient()
        self.adapter = CRMScoreProjectionAdapter(self.client)

    def test_projects_only_direct_canonical_score_recommendation_and_version_fields(self) -> None:
        result = self.adapter.project("lead-123", score_result())

        self.assertEqual(result.status, ScoreProjectionStatus.PROJECTED)
        self.assertEqual(result.updated_fields, ("peOpportunityScoreV4", "peScoreTier", "peScoreRulesVersion", "peBestFirstProduct"))
        self.assertEqual(
            self.client.update_calls,
            [(
                "lead-123",
                {
                    "peOpportunityScoreV4": 82.0,
                    "peScoreTier": "A",
                    "peScoreRulesVersion": "canonical-scoring-v4.0",
                    "peBestFirstProduct": "Resin Printer",
                },
            )],
        )

    def test_skips_missing_or_unaccepted_score_data_without_crm_update(self) -> None:
        result = self.adapter.project("lead-123", score_result(accepted=False, opportunity_score=None, score_tier=None))

        self.assertEqual(result.status, ScoreProjectionStatus.SKIPPED)
        self.assertEqual(result.reason_code, "MISSING_SCORE_DATA")
        self.assertEqual(self.client.update_calls, [])

    def test_permission_denial_does_not_retry_or_mutate_other_entities(self) -> None:
        client = FakeLeadProjectionClient(permission_denied=True)
        result = CRMScoreProjectionAdapter(client).project("lead-123", score_result())

        self.assertEqual(result.status, ScoreProjectionStatus.DENIED)
        self.assertEqual(result.reason_code, "CRM_PERMISSION_DENIED")
        self.assertEqual(client.update_calls, [])
        self.assertEqual(client.lead_creations, [])
        self.assertEqual(client.opportunity_creations, [])
        self.assertEqual(client.email_sends, [])

    def test_never_sends_unrelated_lead_fields(self) -> None:
        self.adapter.project("lead-123", score_result(best_first_product=None))

        fields = self.client.update_calls[0][1]
        self.assertEqual(set(fields), {"peOpportunityScoreV4", "peScoreTier", "peScoreRulesVersion"})
        self.assertNotIn("peResearchSummary", fields)
        self.assertNotIn("peKeyEvidence", fields)
        self.assertNotIn("peRecommendedApproach", fields)
        self.assertNotIn("status", fields)
        self.assertNotIn("name", fields)
