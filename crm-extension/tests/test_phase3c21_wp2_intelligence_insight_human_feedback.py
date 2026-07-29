"""Phase3C21 WP2 advisory insight and human-feedback governance contracts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
)
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
SCOPES = MODULE / "Resources" / "metadata" / "scopes"
ACL_DEFS = MODULE / "Resources" / "metadata" / "aclDefs"
APP = MODULE / "Resources" / "metadata" / "app"
SERVICES = MODULE / "Services"
HOOKS = MODULE / "Hooks"
ENTITIES = MODULE / "Entities"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C21AIQualificationInsightEntityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity = load_json(ENTITY_DEFS / "AIQualificationInsight.json")
        cls.fields = cls.entity["fields"]
        cls.links = cls.entity["links"]
        cls.scope = load_json(SCOPES / "AIQualificationInsight.json")

    def test_entity_shell_and_metadata_exist(self) -> None:
        shell = ENTITIES / "AIQualificationInsight.php"
        self.assertTrue(shell.is_file())
        self.assertIn(
            "final class AIQualificationInsight extends Entity",
            shell.read_text(encoding="utf-8"),
        )
        self.assertEqual(load_json(ACL_DEFS / "AIQualificationInsight.json"), {})

    def test_entity_is_hidden_governed_record(self) -> None:
        self.assertTrue(self.scope["entity"])
        self.assertFalse(self.scope["object"])
        self.assertFalse(self.scope["tab"])
        self.assertFalse(self.scope["aclPortal"])
        self.assertFalse(self.scope["importable"])
        self.assertIsNone(self.scope["statusField"])

    def test_required_advisory_fields_exist(self) -> None:
        for field in (
            "prospectPool",
            "insightContent",
            "signals",
            "reasoning",
            "confidence",
            "evidenceReferences",
            "evidenceReferenceIds",
            "sourceAIRequestLog",
            "sourceAIJob",
            "createdAt",
            "supersedes",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.fields)
        self.assertEqual(self.fields["confidence"]["min"], 0)
        self.assertEqual(self.fields["confidence"]["max"], 1)

    def test_confidence_is_not_validation_or_decision_state(self) -> None:
        self.assertNotIn("validationState", self.fields)
        self.assertNotIn("status", self.fields)
        self.assertTrue(self.fields["confidence"]["readOnly"])

    def test_prospect_pool_and_c20_provenance_links_are_correct(self) -> None:
        self.assertEqual(self.links["prospectPool"]["entity"], "ProspectPool")
        self.assertEqual(
            self.links["sourceAIRequestLog"]["entity"],
            "AIRequestLog",
        )
        self.assertEqual(self.links["sourceAIJob"]["entity"], "AIJob")
        self.assertEqual(
            self.links["supersedes"]["entity"],
            "AIQualificationInsight",
        )

    def test_evidence_reference_is_real_relation_with_immutable_snapshot(self) -> None:
        evidence = self.links["evidenceReferences"]
        self.assertEqual(evidence["type"], "hasMany")
        self.assertEqual(evidence["entity"], "ResearchEvidence")
        self.assertEqual(
            evidence["relationName"],
            "c21AIQualificationInsightResearchEvidence",
        )
        self.assertEqual(evidence["foreign"], "qualificationInsights")
        self.assertTrue(self.fields["evidenceReferenceIds"]["readOnly"])

    def test_no_score_or_qualification_verdict_fields_exist(self) -> None:
        forbidden = {
            "score",
            "AIScore",
            "canonicalScore",
            "canonical_score",
            "qualificationScore",
            "qualification_score",
            "qualified",
            "disqualified",
            "hot",
            "cold",
            "isCurrent",
        }
        self.assertTrue(forbidden.isdisjoint(self.fields))


class Phase3C21AIQualificationInsightServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = (
            SERVICES / "AIQualificationInsightService.php"
        ).read_text(encoding="utf-8")
        cls.guard = (
            HOOKS
            / "AIQualificationInsight"
            / "AIQualificationInsightImmutableGuard.php"
        ).read_text(encoding="utf-8")

    def test_service_only_create_and_immutable_guard(self) -> None:
        self.assertIn("public function create(array $attributes)", self.service)
        self.assertIn(
            "C21IntelligenceSaveOption::INSIGHT_CREATE_AUTHORIZED",
            self.service,
        )
        self.assertIn("implements BeforeSave, BeforeRemove", self.guard)
        self.assertIn("if (!$entity->isNew())", self.guard)
        self.assertIn("cannot be deleted", self.guard)

    def test_service_validates_evidence_belongs_to_prospect_pool(self) -> None:
        self.assertIn("evidenceReferences(", self.service)
        self.assertIn("existingEntity('ResearchEvidence'", self.service)
        self.assertIn("get('prospectPoolId')", self.service)
        self.assertIn(
            "evidence must belong to its ProspectPool",
            self.service,
        )

    def test_service_saves_snapshot_and_relationship(self) -> None:
        self.assertIn("'evidenceReferenceIds' => json_encode(", self.service)
        self.assertIn(
            "getRelation($insight, 'evidenceReferences')",
            self.service,
        )
        self.assertIn("$relation->relate($evidence)", self.service)
        self.assertIn("getTransactionManager()->run", self.service)

    def test_c20_provenance_is_required_and_consistent(self) -> None:
        self.assertIn("requiredId($attributes, 'sourceAIRequestLogId')", self.service)
        self.assertIn("'AIRequestLog'", self.service)
        self.assertIn("get('aiJobId')", self.service)
        self.assertIn(
            "sourceAIJobId must match sourceAIRequestLogId",
            self.service,
        )

    def test_supersession_creates_linear_same_candidate_history(self) -> None:
        self.assertIn("assertSupersession(", self.service)
        self.assertIn("same ProspectPool", self.service)
        self.assertIn("already has a direct successor", self.service)
        self.assertNotIn("isCurrent", self.service)

    def test_service_does_not_create_or_modify_c20_records(self) -> None:
        self.assertNotIn("getNewEntity('AIJob')", self.service)
        self.assertNotIn("getNewEntity('AIRequestLog')", self.service)
        self.assertNotIn("getNewEntity('PromptTemplate')", self.service)
        self.assertNotIn("saveEntity($requestLog", self.service)
        self.assertNotIn("saveEntity($job", self.service)

    def test_referenced_records_require_read_acl(self) -> None:
        self.assertIn("$this->acl->checkEntityRead($entity)", self.service)


class Phase3C21HumanFeedbackEntityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity = load_json(ENTITY_DEFS / "HumanFeedback.json")
        cls.fields = cls.entity["fields"]
        cls.links = cls.entity["links"]
        cls.scope = load_json(SCOPES / "HumanFeedback.json")

    def test_entity_shell_and_hidden_scope_exist(self) -> None:
        shell = ENTITIES / "HumanFeedback.php"
        self.assertTrue(shell.is_file())
        self.assertIn(
            "final class HumanFeedback extends Entity",
            shell.read_text(encoding="utf-8"),
        )
        self.assertFalse(self.scope["tab"])
        self.assertFalse(self.scope["object"])
        self.assertFalse(self.scope["aclPortal"])

    def test_parent_target_supports_only_c21_intelligence(self) -> None:
        target = self.fields["target"]
        self.assertEqual(target["type"], "linkParent")
        self.assertEqual(
            target["entityList"],
            ["AIQualificationInsight", "ResearchEvidence", "ProspectPool"],
        )
        self.assertEqual(self.links["target"]["type"], "belongsToParent")
        self.assertNotIn("Lead", target["entityList"])
        self.assertNotIn("Opportunity", target["entityList"])

    def test_feedback_types_are_review_signals_not_crm_commands(self) -> None:
        self.assertEqual(
            self.fields["feedbackType"]["options"],
            ["CONFIRM", "CORRECT", "DISAGREE", "COMMENT"],
        )
        self.assertNotIn(
            "APPROVED_LEAD",
            self.fields["feedbackType"]["options"],
        )
        self.assertNotIn(
            "REJECTED_LEAD",
            self.fields["feedbackType"]["options"],
        )

    def test_actor_comment_assessment_and_supersession_exist(self) -> None:
        for field in ("comment", "assessment", "actor", "supersedes", "createdAt"):
            self.assertIn(field, self.fields)
        self.assertEqual(self.links["actor"]["entity"], "User")
        self.assertEqual(self.links["supersedes"]["entity"], "HumanFeedback")

    def test_feedback_has_no_lifecycle_or_score_fields(self) -> None:
        forbidden = {
            "status",
            "stage",
            "score",
            "qualification",
            "lead",
            "opportunity",
            "approvedLead",
            "rejectedLead",
        }
        self.assertTrue(forbidden.isdisjoint(self.fields))


class Phase3C21HumanFeedbackServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = (SERVICES / "HumanFeedbackService.php").read_text(
            encoding="utf-8"
        )
        cls.guard = (
            HOOKS / "HumanFeedback" / "HumanFeedbackAppendOnlyGuard.php"
        ).read_text(encoding="utf-8")

    def test_append_only_guard_blocks_update_and_delete(self) -> None:
        self.assertIn("implements BeforeSave, BeforeRemove", self.guard)
        self.assertIn("if (!$entity->isNew())", self.guard)
        self.assertIn("append-only and cannot be modified", self.guard)
        self.assertIn("append-only and cannot be deleted", self.guard)

    def test_service_records_authenticated_actor(self) -> None:
        self.assertIn("private User $user", self.service)
        self.assertIn("$this->user->getId()", self.service)
        self.assertIn("'actorId' => $actorId", self.service)

    def test_correction_and_comment_require_explanation(self) -> None:
        self.assertIn("['CORRECT', 'COMMENT']", self.service)
        self.assertIn("requires comment", self.service)

    def test_feedback_supersession_preserves_target(self) -> None:
        self.assertIn("assertSupersession(", self.service)
        self.assertIn("must retain the same target", self.service)
        self.assertIn("already has a direct successor", self.service)

    def test_service_never_saves_or_mutates_target(self) -> None:
        self.assertIn("$this->acl->checkEntityRead($target)", self.service)
        self.assertNotIn("saveEntity($target", self.service)
        self.assertNotIn("$target->set(", self.service)
        self.assertNotIn("getNewEntity('Lead')", self.service)
        self.assertNotIn("getNewEntity('Opportunity')", self.service)


class Phase3C21WP2AclCompatibilityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.acl = load_json(APP / "acl.json")
        cls.portal_acl = load_json(APP / "aclPortal.json")
        cls.insight_service = (
            SERVICES / "AIQualificationInsightService.php"
        ).read_text(encoding="utf-8")
        cls.feedback_service = (
            SERVICES / "HumanFeedbackService.php"
        ).read_text(encoding="utf-8")

    def test_acl_allows_create_read_and_denies_edit_delete(self) -> None:
        for entity_type in ("AIQualificationInsight", "HumanFeedback"):
            with self.subTest(entity_type=entity_type):
                self.assertEqual(
                    self.acl["adminMandatory"]["scopeLevel"][entity_type],
                    {
                        "create": "yes",
                        "read": "all",
                        "edit": "no",
                        "delete": "no",
                    },
                )
                self.assertFalse(
                    self.acl["mandatory"]["scopeLevel"][entity_type]
                )
                self.assertFalse(
                    self.portal_acl["mandatory"]["scopeLevel"][entity_type]
                )

    def test_existing_sales_feedback_contract_is_not_reused(self) -> None:
        sales_feedback = load_json(ENTITY_DEFS / "SalesFeedback.json")
        self.assertIn("lead", sales_feedback["fields"])
        self.assertIn("outcome", sales_feedback["fields"])
        self.assertNotIn("target", sales_feedback["fields"])
        self.assertNotIn("supersedes", sales_feedback["fields"])

    def test_prospect_pool_and_research_evidence_compatibility_links_exist(self) -> None:
        prospect_pool = load_json(ENTITY_DEFS / "ProspectPool.json")
        evidence = load_json(ENTITY_DEFS / "ResearchEvidence.json")
        self.assertEqual(
            prospect_pool["links"]["qualificationInsights"]["entity"],
            "AIQualificationInsight",
        )
        self.assertEqual(
            evidence["links"]["qualificationInsights"]["entity"],
            "AIQualificationInsight",
        )
        self.assertEqual(
            evidence["links"]["humanFeedbacks"]["entity"],
            "HumanFeedback",
        )

    def test_no_runtime_execution_or_automation_dependencies(self) -> None:
        combined = self.insight_service + self.feedback_service
        forbidden = (
            "HttpClient",
            "curl_",
            "ProviderRegistry",
            "ProviderAdapter",
            "sendEmail",
            "ActionLedger",
            "AutomationRule",
            "AgentLoop",
        )
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, combined)

    def test_no_secret_or_raw_provider_payload_fields(self) -> None:
        fields = (
            set(load_json(ENTITY_DEFS / "AIQualificationInsight.json")["fields"])
            | set(load_json(ENTITY_DEFS / "HumanFeedback.json")["fields"])
        )
        forbidden = {
            "apiKey",
            "token",
            "password",
            "credential",
            "secret",
            "rawPrompt",
            "rawResponse",
            "requestBody",
            "responseBody",
            "providerPayload",
        }
        self.assertTrue(forbidden.isdisjoint(fields))


if __name__ == "__main__":
    unittest.main()
