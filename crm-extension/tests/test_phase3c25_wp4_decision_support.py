"""Phase3C25 WP4 Commercial Decision Support Layer contracts.

Ownership / authority / provenance / boundary / lifecycle — no runtime execution.
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

CONTEXT_ENTITY = CI / "Entities" / "DecisionSupportContext.php"
REVIEW_ENTITY = CI / "Entities" / "HumanReviewDecisionRecord.php"
FEEDBACK_ENTITY = CI / "Entities" / "PresentationFeedback.php"

CONTEXT_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "DecisionSupportContext.json"
REVIEW_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "HumanReviewDecisionRecord.json"
FEEDBACK_DEFS = CI / "Resources" / "metadata" / "entityDefs" / "PresentationFeedback.json"

CONTEXT_SCOPES = CI / "Resources" / "metadata" / "scopes" / "DecisionSupportContext.json"
REVIEW_SCOPES = CI / "Resources" / "metadata" / "scopes" / "HumanReviewDecisionRecord.json"
FEEDBACK_SCOPES = CI / "Resources" / "metadata" / "scopes" / "PresentationFeedback.json"

AGGREGATION = CI / "Services" / "DecisionSupportContextAggregationService.php"
REVIEW = CI / "Services" / "HumanReviewDecisionService.php"
FEEDBACK = CI / "Services" / "PresentationFeedbackService.php"
READ_ONLY = CI / "Services" / "Wp4ReadOnlySourceService.php"
PROVENANCE = CI / "Services" / "DecisionSupportProvenanceValidator.php"
SAVE_OPTION = CI / "Services" / "Wp4DecisionSupportSaveOption.php"

CONTEXT_GUARD = (
    CI / "Hooks" / "DecisionSupportContext" / "DecisionSupportContextGuard.php"
)
REVIEW_IMMUTABLE = (
    CI
    / "Hooks"
    / "HumanReviewDecisionRecord"
    / "HumanReviewDecisionImmutabilityGuard.php"
)
REVIEW_STATUS = (
    CI / "Hooks" / "HumanReviewDecisionRecord" / "HumanReviewDecisionStatusGuard.php"
)
FEEDBACK_GUARD = CI / "Hooks" / "PresentationFeedback" / "PresentationFeedbackGuard.php"

CONTEXT_CONTROLLER = CI / "Controllers" / "DecisionSupportContext.php"
REVIEW_CONTROLLER = CI / "Controllers" / "HumanReviewDecisionRecord.php"
FEEDBACK_CONTROLLER = CI / "Controllers" / "PresentationFeedback.php"

FIXTURE = (
    ROOT
    / "crm-extension"
    / "tests"
    / "fixtures"
    / "phase3c25_wp4_decision_support_context.json"
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
    "Scheduler",
    "QueueItem",
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
    CONTEXT_ENTITY,
    REVIEW_ENTITY,
    FEEDBACK_ENTITY,
    AGGREGATION,
    REVIEW,
    FEEDBACK,
    READ_ONLY,
    PROVENANCE,
    SAVE_OPTION,
    CONTEXT_GUARD,
    REVIEW_IMMUTABLE,
    REVIEW_STATUS,
    FEEDBACK_GUARD,
    CONTEXT_CONTROLLER,
    REVIEW_CONTROLLER,
    FEEDBACK_CONTROLLER,
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C25Wp4DecisionSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context_defs = json.loads(read(CONTEXT_DEFS))
        cls.review_defs = json.loads(read(REVIEW_DEFS))
        cls.feedback_defs = json.loads(read(FEEDBACK_DEFS))
        cls.aggregation = read(AGGREGATION)
        cls.review = read(REVIEW)
        cls.feedback = read(FEEDBACK)
        cls.read_only = read(READ_ONLY)
        cls.provenance = read(PROVENANCE)
        cls.status_guard = read(REVIEW_STATUS)
        cls.fixture = json.loads(read(FIXTURE))

    def test_required_files_exist(self) -> None:
        for path in PHP_SOURCES + [
            CONTEXT_DEFS,
            REVIEW_DEFS,
            FEEDBACK_DEFS,
            CONTEXT_SCOPES,
            REVIEW_SCOPES,
            FEEDBACK_SCOPES,
            FIXTURE,
        ]:
            self.assertTrue(path.is_file(), msg=f"missing {path}")

    def test_boundary_no_runtime_provider_connector(self) -> None:
        for path in PHP_SOURCES:
            source = read(path)
            for marker in FORBIDDEN_RUNTIME:
                self.assertNotIn(marker, source, msg=f"{path.name}: {marker}")
            self.assertNotIn("DecisionIntentRecord", source, msg=path.name)

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
        self.assertIn("CommercialBrief", self.read_only)
        self.assertIn("CommercialInsight", self.read_only)
        self.assertIn("BusinessReviewContext", self.read_only)
        self.assertIn("getEntity", self.read_only)
        self.assertNotIn("saveEntity", self.read_only)

    def test_authority_human_required_ai_cannot_approve(self) -> None:
        self.assertIn("assertHumanReviewer", self.review)
        self.assertIn("type === 'api'", self.review)
        self.assertIn("type === 'system'", self.review)
        self.assertIn(
            "cannot accept, dismiss, decide, approve, or execute",
            self.review,
        )
        self.assertIn("assertHumanCloser", self.aggregation)
        self.assertIn("AI/system cannot decide or approve", self.aggregation)
        self.assertIn("assertHumanAuthor", self.feedback)
        self.assertIn("'GENERATED' => ['REVIEWED']", self.status_guard)
        self.assertIn("'REVIEWED' => ['ACCEPTED', 'DISMISSED']", self.status_guard)

    def test_provenance_retained(self) -> None:
        for defs in (self.context_defs, self.review_defs, self.feedback_defs):
            fields = defs["fields"]
            for key in (
                "sourceEvidenceReference",
                "capabilityReference",
                "purposeReference",
            ):
                self.assertTrue(fields[key]["required"], msg=key)
            self.assertEqual(fields["capabilityReference"]["default"], "COMMERCIAL_BRIEF")
            self.assertEqual(
                fields["purposeReference"]["default"],
                "commercial_decision_support",
            )
        self.assertIn("CAPABILITY_COMMERCIAL_BRIEF", self.provenance)
        self.assertIn("PURPOSE_COMMERCIAL_DECISION_SUPPORT", self.provenance)
        self.assertEqual(self.fixture["capabilityReference"], "COMMERCIAL_BRIEF")
        self.assertEqual(
            self.fixture["purposeReference"],
            "commercial_decision_support",
        )
        self.assertTrue(self.fixture["sourceEvidenceReference"])

    def test_decision_support_context_named_references(self) -> None:
        fields = self.context_defs["fields"]
        self.assertIn("commercialBriefReferences", fields)
        self.assertIn("commercialInsightReferences", fields)
        self.assertIn("businessReviewContextReferences", fields)
        self.assertIn("opportunityCandidateReference", fields)
        self.assertIn("revenueInsightReference", fields)
        self.assertIn("pipelineMetricReference", fields)
        self.assertEqual(fields["status"]["options"], ["OPEN", "CLOSED"])
        self.assertIn("mutation' => 'none'", self.aggregation)
        self.assertIn("transitionInvocation' => 'none'", self.aggregation)
        self.assertIn("ENTITY_COMMERCIAL_BRIEF", self.aggregation)
        self.assertIn("ENTITY_COMMERCIAL_INSIGHT", self.aggregation)
        self.assertIn("ENTITY_BUSINESS_REVIEW_CONTEXT", self.aggregation)
        self.assertIn("ENTITY_OPPORTUNITY_CANDIDATE", self.aggregation)
        self.assertIn("ENTITY_REVENUE_INSIGHT", self.aggregation)
        self.assertIn("ENTITY_PIPELINE_METRIC", self.aggregation)

    def test_human_review_decision_record_not_intent_store(self) -> None:
        fields = self.review_defs["fields"]
        self.assertEqual(
            fields["reviewStatus"]["options"],
            ["GENERATED", "REVIEWED", "ACCEPTED", "DISMISSED"],
        )
        self.assertIn("reviewComment", fields)
        self.assertIn("lastTransitionBy", fields)
        self.assertIn("lastTransitionAt", fields)
        for forbidden in (
            "actionCommand",
            "workflowCommand",
            "crmLifecycleInstruction",
            "futureActionIntent",
            "c24TransitionInstruction",
        ):
            self.assertNotIn(forbidden, fields)
        self.assertIn("human review outcome", self.review.lower())
        self.assertIn("Not a persisted decision-intent store", self.review)
        self.assertNotIn("DecisionIntentRecord", self.review)
        self.assertNotIn("DecisionIntentRecord", read(REVIEW_ENTITY))
        self.assertNotIn("DecisionIntentRecord", read(REVIEW_CONTROLLER))

    def test_presentation_feedback_boundary(self) -> None:
        fields = self.feedback_defs["fields"]
        self.assertEqual(
            fields["feedbackType"]["options"],
            ["PRESENTATION", "EXPLANATION_QUALITY", "ANNOTATION"],
        )
        self.assertEqual(
            fields["advisorySource"]["options"],
            ["FIXTURE", "STUB", "DETERMINISTIC", "HUMAN_AUTHORED"],
        )
        self.assertIn("No training loop", self.feedback)
        self.assertNotIn("LIVE", self.feedback)

    def test_assistant_advisory_boundary(self) -> None:
        self.assertIn("human-facing-advisory-intelligence-interface", self.aggregation)
        self.assertIn("commercial-decision-support-layer", self.aggregation)
        self.assertNotIn("LIVE", self.aggregation)
        self.assertNotIn("DecisionIntentRecord", self.aggregation)


if __name__ == "__main__":
    unittest.main()
