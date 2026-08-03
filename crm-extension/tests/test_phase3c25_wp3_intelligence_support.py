"""Phase3C25 WP3 Commercial Intelligence Support Layer contracts.

Boundary / ownership / authority / provenance — no runtime execution.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "CommercialIntelligence"
)

INSIGHT_ENTITY = CI / "Entities" / "CommercialInsight.php"
CONTEXT_ENTITY = CI / "Entities" / "BusinessReviewContext.php"
INSIGHT_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "CommercialInsight.json"
CONTEXT_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "BusinessReviewContext.json"
INSIGHT_SCOPES = CI / "Resources" / "metadata" / "scopes" / "CommercialInsight.json"
CONTEXT_SCOPES = CI / "Resources" / "metadata" / "scopes" / "BusinessReviewContext.json"

PROPOSAL = CI / "Services" / "CommercialInsightProposalService.php"
REVIEW = CI / "Services" / "CommercialInsightReviewService.php"
AGGREGATION = CI / "Services" / "BusinessReviewContextAggregationService.php"
READ_ONLY = CI / "Services" / "Wp3ReadOnlySourceService.php"
PROVENANCE = CI / "Services" / "InsightProvenanceValidator.php"
SAVE_OPTION = CI / "Services" / "Wp3InsightSaveOption.php"

INSIGHT_IMMUTABLE = (
    CI / "Hooks" / "CommercialInsight" / "CommercialInsightImmutabilityGuard.php"
)
INSIGHT_STATUS = (
    CI / "Hooks" / "CommercialInsight" / "CommercialInsightReviewStatusGuard.php"
)
CONTEXT_GUARD = (
    CI / "Hooks" / "BusinessReviewContext" / "BusinessReviewContextGuard.php"
)

INSIGHT_CONTROLLER = CI / "Controllers" / "CommercialInsight.php"
CONTEXT_CONTROLLER = CI / "Controllers" / "BusinessReviewContext.php"

FIXTURE = (
    ROOT
    / "crm-extension"
    / "tests"
    / "fixtures"
    / "phase3c25_wp3_commercial_insight_proposal.json"
)

FORBIDDEN_RUNTIME = (
    "curl_init",
    "curl_exec",
    "GuzzleHttp",
    "chitu_connector",
    "AIDispatchService",
    "AIJobService",
    "AIDispatchWorker",
    "subprocess",
    "fsockopen",
)

FORBIDDEN_MUTATION_CALLS = (
    "saveEntity('Lead'",
    'saveEntity("Lead"',
    "saveEntity('Opportunity'",
    'saveEntity("Opportunity"',
    "saveEntity('RevenueInsight'",
    'saveEntity("RevenueInsight"',
    "saveEntity('PipelineMetric'",
    'saveEntity("PipelineMetric"',
    "saveEntity('OpportunityCandidate'",
    'saveEntity("OpportunityCandidate"',
    "saveEntity('ProspectRun'",
    'saveEntity("ProspectRun"',
    "saveEntity('ExecutionLedger'",
    'saveEntity("ExecutionLedger"',
)

PHP_SOURCES = [
    INSIGHT_ENTITY,
    CONTEXT_ENTITY,
    PROPOSAL,
    REVIEW,
    AGGREGATION,
    READ_ONLY,
    PROVENANCE,
    SAVE_OPTION,
    INSIGHT_IMMUTABLE,
    INSIGHT_STATUS,
    CONTEXT_GUARD,
    INSIGHT_CONTROLLER,
    CONTEXT_CONTROLLER,
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C25Wp3IntelligenceSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.insight_defs = json.loads(read(INSIGHT_DEFS))
        cls.context_defs = json.loads(read(CONTEXT_DEFS))
        cls.proposal = read(PROPOSAL)
        cls.review = read(REVIEW)
        cls.aggregation = read(AGGREGATION)
        cls.read_only = read(READ_ONLY)
        cls.provenance = read(PROVENANCE)
        cls.fixture = json.loads(read(FIXTURE))
        cls.status_guard = read(INSIGHT_STATUS)

    def test_required_files_exist(self) -> None:
        for path in PHP_SOURCES + [
            INSIGHT_DEFS,
            CONTEXT_DEFS,
            INSIGHT_SCOPES,
            CONTEXT_SCOPES,
            FIXTURE,
        ]:
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_boundary_no_runtime_provider_connector(self) -> None:
        for path in PHP_SOURCES:
            source = read(path)
            for marker in FORBIDDEN_RUNTIME:
                self.assertNotIn(marker, source, msg=f"{path.name}: {marker}")

    def test_ownership_no_c22_c24_crm_mutation(self) -> None:
        blob = "\n".join(read(p) for p in PHP_SOURCES)
        for marker in FORBIDDEN_MUTATION_CALLS:
            self.assertNotIn(marker, blob, msg=marker)
        self.assertIn("READ_ONLY_TYPES", self.read_only)
        self.assertIn("FORBIDDEN_MUTATION_TYPES", self.read_only)
        self.assertIn("'ProspectRun'", self.read_only)
        self.assertIn("OpportunityCandidate", self.read_only)
        self.assertIn("RevenueInsight", self.read_only)
        self.assertIn("PipelineMetric", self.read_only)
        self.assertIn("getEntity", self.read_only)
        # Read-only source service itself must never persist.
        self.assertNotIn("saveEntity", self.read_only)

    def test_assistant_advisory_boundary(self) -> None:
        self.assertIn("human-facing advisory intelligence interface", self.proposal)
        self.assertIn("human-facing-advisory-intelligence-interface", self.aggregation)
        self.assertIn("FIXTURE", self.proposal)
        self.assertIn("STUB", self.proposal)
        self.assertIn("DETERMINISTIC", self.proposal)
        self.assertNotIn("LIVE", self.proposal)

    def test_authority_human_required_ai_cannot_approve(self) -> None:
        self.assertIn("assertHumanReviewer", self.review)
        self.assertIn("type === 'api'", self.review)
        self.assertIn("type === 'system'", self.review)
        self.assertIn("cannot accept, dismiss, decide, approve, or execute", self.review)
        self.assertIn("assertHumanCloser", self.aggregation)
        self.assertIn("AI/system cannot decide or approve", self.aggregation)
        self.assertIn("'GENERATED' => ['REVIEWED']", self.status_guard)
        self.assertIn("'REVIEWED' => ['ACCEPTED', 'DISMISSED']", self.status_guard)

    def test_provenance_retained(self) -> None:
        fields = self.insight_defs["fields"]
        for key in (
            "sourceEvidenceReference",
            "capabilityReference",
            "purposeReference",
        ):
            self.assertTrue(fields[key]["required"], msg=key)
        self.assertEqual(fields["capabilityReference"]["default"], "COMMERCIAL_BRIEF")
        self.assertEqual(
            fields["purposeReference"]["default"],
            "commercial_insight_advisory",
        )
        self.assertIn("CAPABILITY_COMMERCIAL_BRIEF", self.provenance)
        self.assertIn("PURPOSE_COMMERCIAL_INSIGHT_ADVISORY", self.provenance)
        self.assertEqual(self.fixture["capabilityReference"], "COMMERCIAL_BRIEF")
        self.assertEqual(
            self.fixture["purposeReference"],
            "commercial_insight_advisory",
        )
        self.assertTrue(self.fixture["sourceEvidenceReference"])

    def test_context_holds_references_not_owned_lifecycles(self) -> None:
        fields = self.context_defs["fields"]
        self.assertIn("opportunityCandidateReference", fields)
        self.assertIn("revenueInsightReference", fields)
        self.assertIn("pipelineMetricReference", fields)
        self.assertIn("commercialBriefReferences", fields)
        self.assertEqual(fields["status"]["options"], ["OPEN", "CLOSED"])
        self.assertIn("mutation' => 'none'", self.aggregation)


if __name__ == "__main__":
    unittest.main()
