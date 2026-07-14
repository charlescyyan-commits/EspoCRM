"""Synthetic, end-to-end runtime acceptance for the C07 evidence flow.

The in-memory target implements the exact C07.2 persistence interface. It is
deliberately limited to ResearchEvidence operations so this acceptance flow
cannot create Leads, Opportunities, emails, or workflow events.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence
from unittest import TestCase

from chitu_connector.acquisition.evidence_extraction import WebsiteResearchEvidenceExtractor
from chitu_connector.acquisition.website_research import (
    FetchStatus,
    PageType,
    ResearchStatus,
    WebsiteResearchPageResult,
    WebsiteResearchPipelineResult,
)
from chitu_connector.espocrm_sync.enrichment_gate import DeterministicEnrichmentGate, QualificationStatus
from chitu_connector.espocrm_sync.research_evidence_persistence import (
    EvidencePersistenceStatus,
    ResearchEvidencePersistenceAdapter,
)


SYNTHETIC_MARKER = "[C07_RUNTIME_SYNTHETIC]"
TIME = "2026-07-13T00:00:00Z"
SYNTHETIC_LEAD_ID = "synthetic-c07-runtime-lead"


class SyntheticResearchEvidenceRuntime:
    """Memory-only ResearchEvidence target with explicit forbidden surfaces."""

    def __init__(self) -> None:
        self.research_evidence: list[dict[str, Any]] = []
        self.lookup_calls: list[tuple[str, str]] = []
        self.create_calls: list[dict[str, Any]] = []
        self.leads: list[dict[str, Any]] = []
        self.opportunities: list[dict[str, Any]] = []
        self.emails: list[dict[str, Any]] = []
        self.workflow_events: list[dict[str, Any]] = []

    def find_research_evidence_for_snapshot(
        self,
        lead_id: str,
        snapshot_hash: str,
    ) -> Sequence[Mapping[str, Any]]:
        self.lookup_calls.append((lead_id, snapshot_hash))
        return tuple(
            dict(record)
            for record in self.research_evidence
            if record["leadId"] == lead_id and record["peSnapshotHash"] == snapshot_hash
        )

    def find_research_evidence_by_identity(
        self,
        lead_id: str,
        source_url: str,
        claim_type: str,
        claim: str,
    ) -> Sequence[Mapping[str, Any]]:
        return tuple(
            dict(record)
            for record in self.research_evidence
            if record["leadId"] == lead_id
            and record["peSourceUrl"] == source_url
            and record["peClaimType"] == claim_type
            and record["peClaim"] == claim
        )

    def create_research_evidence(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        record = dict(body)
        record["id"] = f"synthetic-evidence-{len(self.research_evidence) + 1}"
        self.research_evidence.append(record)
        self.create_calls.append(dict(body))
        return {"id": record["id"]}


def synthetic_research_fixture() -> dict[str, object]:
    page = WebsiteResearchPageResult(
        requested_url="https://c07-runtime-synthetic.example/",
        final_url="https://c07-runtime-synthetic.example/",
        page_type=PageType.HOME,
        status_code=200,
        content_type="text/html",
        title=f"{SYNTHETIC_MARKER} Industrial Products",
        text_content="The synthetic fixture lists industrial resin printers. Contact details are publicly listed.",
        raw_html=None,
        meta_description="Synthetic public catalog for C07 runtime acceptance.",
        links=(),
        fetch_status=FetchStatus.SUCCESS,
        error=None,
        redirect_chain=(),
        fetched_at=TIME,
        classification_reason="Synthetic runtime acceptance fixture.",
        sanitization_actions=(),
    )
    return WebsiteResearchPipelineResult(
        master_id="synthetic-c07-runtime-master",
        normalized_domain="c07-runtime-synthetic.example",
        canonical_name=SYNTHETIC_MARKER,
        root_url="https://c07-runtime-synthetic.example/",
        pages=(page,),
        research_status=ResearchStatus.COMPLETED,
        successful_page_count=1,
        failed_page_count=0,
        selected_page_types=(PageType.HOME,),
        started_at=TIME,
        completed_at=TIME,
        trace=(),
    ).to_dict()


class C07RuntimeAcceptanceTests(TestCase):
    def setUp(self) -> None:
        self.runtime = SyntheticResearchEvidenceRuntime()
        self.extractor = WebsiteResearchEvidenceExtractor()
        self.persistence = ResearchEvidencePersistenceAdapter(self.runtime)
        self.gate = DeterministicEnrichmentGate()

    def test_complete_synthetic_flow_persists_once_and_qualifies(self) -> None:
        evidence = self.extractor.extract(synthetic_research_fixture())
        self.assertEqual(len(evidence), 3)

        first = self.persistence.persist(SYNTHETIC_LEAD_ID, evidence)
        second = self.persistence.persist(SYNTHETIC_LEAD_ID, evidence)

        self.assertEqual(first.status, EvidencePersistenceStatus.CREATED)
        self.assertEqual(second.status, EvidencePersistenceStatus.SKIPPED)
        self.assertEqual(first.snapshot_hash, second.snapshot_hash)
        self.assertEqual(len(self.runtime.research_evidence), 3)
        self.assertEqual(len(self.runtime.create_calls), 3)
        for record, item in zip(self.runtime.research_evidence, evidence, strict=True):
            self.assertEqual(record["leadId"], SYNTHETIC_LEAD_ID)
            self.assertEqual(record["peSourceUrl"], item.source_url)
            self.assertEqual(record["peClaim"], item.claim)
            self.assertEqual(record["peEvidenceText"], item.evidence_text)
            self.assertEqual(record["peConfidence"], item.confidence)
            self.assertEqual(record["peSnapshotHash"], first.snapshot_hash)

        context = {"id": "synthetic-prospect-pool", "note": SYNTHETIC_MARKER}
        decision = self.gate.evaluate(tuple(self.runtime.research_evidence), context)
        self.assertEqual(decision.status, QualificationStatus.QUALIFIED)
        self.assertEqual(decision.evidence_count, 3)
        self.assertEqual(context, {"id": "synthetic-prospect-pool", "note": SYNTHETIC_MARKER})
        self._assert_no_forbidden_side_effects()

    def test_all_qualification_outcomes_are_deterministic(self) -> None:
        evidence = self.extractor.extract(synthetic_research_fixture())
        persisted = self.persistence.persist(SYNTHETIC_LEAD_ID, evidence)
        self.assertEqual(persisted.status, EvidencePersistenceStatus.CREATED)
        records = self.runtime.research_evidence

        self.assertEqual(self.gate.evaluate(()).status, QualificationStatus.NOT_READY)
        self.assertEqual(self.gate.evaluate((records[0],)).status, QualificationStatus.RESEARCH_COMPLETE)
        low_confidence = deepcopy(records[0])
        low_confidence["peConfidence"] = 0.50
        self.assertEqual(self.gate.evaluate((low_confidence,)).status, QualificationStatus.REVIEW_REQUIRED)
        self.assertEqual(self.gate.evaluate((records[0], low_confidence)).status, QualificationStatus.REVIEW_REQUIRED)
        self.assertEqual(self.gate.evaluate(tuple(reversed(records))), self.gate.evaluate(tuple(records)))
        self._assert_no_forbidden_side_effects()

    def _assert_no_forbidden_side_effects(self) -> None:
        self.assertEqual(self.runtime.leads, [])
        self.assertEqual(self.runtime.opportunities, [])
        self.assertEqual(self.runtime.emails, [])
        self.assertEqual(self.runtime.workflow_events, [])
