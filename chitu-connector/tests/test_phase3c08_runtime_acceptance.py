"""Synthetic runtime acceptance for the C08 evidence-to-Lead score flow.

The workspace does not contain the canonical V4 scorer.  The fixture below is
an external-owner test double: it returns one already-canonical result and
records invocation.  It does not implement scoring rules or fallback logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.canonical_score_integration import CanonicalScoreIntegration
from chitu_connector.espocrm_sync.crm_score_projection import CRMScoreProjectionAdapter, ScoreProjectionStatus
from chitu_connector.espocrm_sync.enrichment_gate import DeterministicEnrichmentGate, QualificationStatus
from chitu_connector.espocrm_sync.score_input_adapter import DeterministicScoreInputAdapter, ScoreInput
from chitu_connector.vendored.contracts.canonical_score import CanonicalScoreResult, ScoreComponentTrace


SYNTHETIC_MARKER = "[C08_RUNTIME_SYNTHETIC]"
SYNTHETIC_LEAD_ID = "synthetic-c08-runtime-existing-lead"
SCORED_AT = datetime(2026, 7, 14, tzinfo=timezone.utc)


def synthetic_research_evidence() -> tuple[dict[str, object], ...]:
    return (
        {
            "id": "synthetic-research-evidence-1",
            "peEvidenceId": "ev-synthetic-products",
            "peEvidenceType": "visible_text",
            "peSourceUrl": "https://score-runtime-synthetic.example/products",
            "peEvidenceText": f"{SYNTHETIC_MARKER} public product catalogue lists resin printers.",
            "peConfidence": 0.92,
        },
        {
            "id": "synthetic-research-evidence-2",
            "peEvidenceId": "ev-synthetic-about",
            "peEvidenceType": "title",
            "peSourceUrl": "https://score-runtime-synthetic.example/about",
            "peEvidenceText": f"{SYNTHETIC_MARKER} industrial distributor profile.",
            "peConfidence": 0.90,
        },
    )


class FrozenExternalCanonicalExecutor:
    """Records the single C08.2 invocation and returns an external fixture."""

    engine_version = "canonical-scoring-v4.0"

    def __init__(self) -> None:
        self.calls: list[ScoreInput] = []

    def score(self, score_input: ScoreInput) -> CanonicalScoreResult:
        self.calls.append(score_input)
        return CanonicalScoreResult(
            accepted=True,
            opportunity_score=82,
            score_tier="A",
            best_first_product="Resin Printer",
            customer_type="DISTRIBUTOR",
            contact_priority="HIGH",
            score_reasons=("FROZEN_CANONICAL_RUNTIME_FIXTURE",),
            evidence_refs=("ev-synthetic-about", "ev-synthetic-products"),
            component_traces=(
                ScoreComponentTrace("product-fit", 42, ("ev-synthetic-products",)),
            ),
            validation_errors=(),
            canonical_engine_version=self.engine_version,
            canonical_content_hash="c08-runtime-canonical-fixture-hash",
            raw_decision={"fixture": "external-canonical-owner"},
            adapter_version="canonical-score-adapter-v1",
            scored_at=SCORED_AT,
        )


class SyntheticExistingLeadTarget:
    """Memory-only target with one pre-existing Lead and no create surfaces."""

    def __init__(self) -> None:
        self.lead = {
            "id": SYNTHETIC_LEAD_ID,
            "name": f"{SYNTHETIC_MARKER} existing lead",
            "status": "New",
        }
        self.projection_updates: list[tuple[str, dict[str, Any]]] = []
        self.lead_creations: list[object] = []
        self.opportunity_creations: list[object] = []
        self.email_sends: list[object] = []
        self.workflow_events: list[object] = []

    def update_lead_score_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        if lead_id != self.lead["id"]:
            raise LookupError("synthetic fixture has one existing Lead")
        body = dict(fields)
        self.projection_updates.append((lead_id, body))
        self.lead.update(body)
        return {"id": lead_id, **body}


class C08RuntimeAcceptanceTests(TestCase):
    def test_synthetic_evidence_qualification_score_and_lead_projection_flow(self) -> None:
        evidence = synthetic_research_evidence()
        qualification = DeterministicEnrichmentGate().evaluate(evidence)
        self.assertEqual(qualification.status, QualificationStatus.QUALIFIED)
        self.assertEqual(qualification.evidence_count, 2)

        score_input = DeterministicScoreInputAdapter().build(evidence, qualification)
        self.assertEqual(score_input.evidence_count, 2)
        self.assertEqual(score_input.evidence_confidences, (0.9, 0.92))
        self.assertEqual(score_input.qualification_status, QualificationStatus.QUALIFIED)

        executor = FrozenExternalCanonicalExecutor()
        score_decision = CanonicalScoreIntegration(executor).evaluate(score_input, evidence)
        self.assertEqual(len(executor.calls), 1)
        self.assertIs(executor.calls[0], score_input)
        self.assertEqual(score_decision.result.opportunity_score, 82)
        self.assertEqual(score_decision.result.score_tier, "A")
        self.assertEqual(score_decision.result.canonical_engine_version, "canonical-scoring-v4.0")
        self.assertEqual(score_decision.trace.input_evidence_refs, ("ev-synthetic-about", "ev-synthetic-products"))

        target = SyntheticExistingLeadTarget()
        projection = CRMScoreProjectionAdapter(target).project(SYNTHETIC_LEAD_ID, score_decision.result)
        self.assertEqual(projection.status, ScoreProjectionStatus.PROJECTED)
        self.assertEqual(
            target.projection_updates,
            [(
                SYNTHETIC_LEAD_ID,
                {
                    "peOpportunityScoreV4": 82.0,
                    "peScoreTier": "A",
                    "peScoreRulesVersion": "canonical-scoring-v4.0",
                    "peBestFirstProduct": "Resin Printer",
                },
            )],
        )
        self.assertEqual(target.lead["name"], f"{SYNTHETIC_MARKER} existing lead")
        self.assertEqual(target.lead["status"], "New")
        self.assertEqual(target.lead["peOpportunityScoreV4"], 82.0)
        self.assertEqual(target.lead["peScoreTier"], "A")
        self.assertEqual(target.lead["peBestFirstProduct"], "Resin Printer")
        self.assertEqual(target.lead["peScoreRulesVersion"], "canonical-scoring-v4.0")

        self.assertEqual(target.lead_creations, [])
        self.assertEqual(target.opportunity_creations, [])
        self.assertEqual(target.email_sends, [])
        self.assertEqual(target.workflow_events, [])
