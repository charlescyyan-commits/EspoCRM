"""Phase3C21 WP1 ResearchEvidence governance hardening contracts.

The tests protect the additive legacy mapping, immutable evidence history,
C20 provenance references, explicit validation actions, and C21 boundaries.
They intentionally do not introduce a provider, runtime, score writer, or CRM
lifecycle workflow.
"""

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
APP_METADATA = MODULE / "Resources" / "metadata" / "app"
SERVICES = MODULE / "Services"
GUARD = (
    MODULE
    / "Hooks"
    / "ResearchEvidence"
    / "ResearchEvidenceGovernanceGuard.php"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C21ResearchEvidenceMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity = load_json(ENTITY_DEFS / "ResearchEvidence.json")
        cls.fields = cls.entity["fields"]
        cls.links = cls.entity["links"]

    def test_existing_entity_and_legacy_fields_are_preserved(self) -> None:
        for field in (
            "peEvidenceId",
            "peClaim",
            "peEvidenceType",
            "peSourceUrl",
            "peEvidenceText",
            "peContentSummary",
            "peConfidence",
            "peCapturedAt",
            "peSnapshotHash",
            "peCanonicalUrl",
            "peClaimHash",
        ):
            self.assertIn(field, self.fields)

    def test_governed_classification_is_separate_from_source_taxonomy(self) -> None:
        self.assertEqual(self.fields["peEvidenceType"]["type"], "varchar")
        governed = self.fields["evidenceType"]
        self.assertEqual(governed["type"], "enum")
        self.assertEqual(
            governed["options"],
            ["UNKNOWN", "FACT", "OBSERVATION", "AI_INFERENCE"],
        )

    def test_legacy_defaults_are_safe_and_explained(self) -> None:
        self.assertEqual(self.fields["evidenceType"]["default"], "UNKNOWN")
        reason = self.fields["classificationReason"]
        self.assertEqual(reason["default"], "LEGACY_UNCLASSIFIED")
        self.assertTrue(reason["readOnly"])
        self.assertEqual(
            self.fields["provenanceReference"]["default"],
            "LEGACY_UNCLASSIFIED",
        )

    def test_evidence_revision_defaults_to_first_revision_and_is_read_only(self) -> None:
        revision = self.fields["evidenceRevision"]
        self.assertEqual(revision["type"], "int")
        self.assertEqual(revision["default"], 1)
        self.assertEqual(revision["min"], 1)
        self.assertTrue(revision["readOnly"])

    def test_validation_state_is_independent_from_confidence(self) -> None:
        validation = self.fields["validationState"]
        self.assertEqual(
            validation["options"],
            ["UNVALIDATED", "VERIFIED", "REJECTED", "SUPERSEDED"],
        )
        self.assertEqual(validation["default"], "UNVALIDATED")
        self.assertTrue(validation["readOnly"])
        self.assertEqual(self.fields["peConfidence"]["type"], "float")
        self.assertNotIn("confidence", self.fields)

    def test_correction_and_c20_reference_links_exist(self) -> None:
        expected = {
            "supersedes": "ResearchEvidence",
            "sourceAIRequestLog": "AIRequestLog",
            "sourceAIJob": "AIJob",
        }
        for link, entity_type in expected.items():
            with self.subTest(link=link):
                self.assertEqual(self.fields[link]["type"], "link")
                self.assertEqual(self.links[link]["type"], "belongsTo")
                self.assertEqual(self.links[link]["entity"], entity_type)
        self.assertEqual(self.links["supersedes"]["foreign"], "supersededBy")

    def test_existing_parent_and_identity_indexes_are_preserved(self) -> None:
        self.assertEqual(self.links["lead"]["entity"], "Lead")
        self.assertEqual(self.links["prospectPool"]["entity"], "ProspectPool")
        indexes = self.entity["indexes"]
        self.assertIn("c10EvidenceIdentity", indexes)
        self.assertIn("c10EvidenceIdentityProspectPool", indexes)
        self.assertNotIn(
            "evidenceRevision",
            indexes["c10EvidenceIdentity"]["columns"],
        )
        self.assertNotIn(
            "evidenceRevision",
            indexes["c10EvidenceIdentityProspectPool"]["columns"],
        )
        self.assertIn("sourceAIRequestLogId", indexes["sourceAIRequestLog"]["columns"])
        self.assertIn("supersedesId", indexes["supersedes"]["columns"])

    def test_no_secret_or_raw_provider_payload_fields_exist(self) -> None:
        forbidden = {
            "apiKey",
            "token",
            "password",
            "credential",
            "secret",
            "providerToken",
            "rawPrompt",
            "rawResponse",
            "requestBody",
            "responseBody",
        }
        self.assertTrue(forbidden.isdisjoint(self.fields))


class Phase3C21LegacyClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record_service = (
            SERVICES / "ResearchEvidenceService.php"
        ).read_text(encoding="utf-8")
        cls.ingress = (SERVICES / "ChituSyncService.php").read_text(
            encoding="utf-8"
        )
        cls.governance = (
            SERVICES / "ResearchEvidenceGovernanceService.php"
        ).read_text(encoding="utf-8")

    def test_new_records_cannot_use_unknown(self) -> None:
        self.assertIn("GOVERNED_EVIDENCE_TYPES", self.record_service)
        self.assertIn(
            "New ResearchEvidence requires an explicit FACT, OBSERVATION, or AI_INFERENCE classification.",
            self.record_service,
        )

    def test_legacy_classification_is_one_time_and_reviewed(self) -> None:
        self.assertIn("classifyLegacy", self.governance)
        self.assertIn("TYPE_UNKNOWN", self.governance)
        self.assertIn("CLASSIFICATION_LEGACY_MANUAL_REVIEW", self.governance)
        self.assertIn(
            "LEGACY_CLASSIFICATION_AUTHORIZED",
            self.governance,
        )
        guard = GUARD.read_text(encoding="utf-8")
        create_section = guard.split(
            "private function prepareAndValidateCreate", 1
        )[1].split("private function assertImmutableCoreUnchanged", 1)[0]
        legacy_section = guard.split(
            "private function assertLegacyClassificationMutation", 1
        )[1].split("private function assertValidationMutation", 1)[0]
        self.assertIn("assertCreateContract($entity);", create_section)
        self.assertIn("assertCreateContract($entity, true)", legacy_section)

    def test_no_confidence_based_fact_mapping_exists(self) -> None:
        combined = self.record_service + self.governance
        self.assertNotIn("peConfidence') >", combined)
        self.assertNotIn("peConfidence') >=", combined)
        self.assertNotIn("confidence > 0.8", combined)
        self.assertNotIn("confidence >= 0.8", combined)

    def test_no_ai_inference_to_fact_automatic_conversion(self) -> None:
        self.assertNotIn("TYPE_AI_INFERENCE => self::TYPE_FACT", self.record_service)
        self.assertNotIn("AI_INFERENCE' => 'FACT", self.governance)

    def test_ingress_classifies_only_new_source_observations(self) -> None:
        self.assertIn("$createdEvidence = false", self.ingress)
        self.assertIn("if ($createdEvidence)", self.ingress)
        self.assertIn(
            "$evidenceFields['evidenceType'] = 'OBSERVATION'",
            self.ingress,
        )
        self.assertIn(
            "Existing legacy rows remain UNKNOWN until reviewed.",
            self.ingress,
        )

    def test_legacy_fields_are_not_removed_or_rewritten_by_a_migration(self) -> None:
        migration_files = [
            path
            for path in MODULE.rglob("*")
            if path.is_file() and "migration" in path.name.lower()
        ]
        self.assertEqual(migration_files, [])


class Phase3C21ImmutableEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = GUARD.read_text(encoding="utf-8")
        cls.save_option = (
            SERVICES / "ResearchEvidenceSaveOption.php"
        ).read_text(encoding="utf-8")
        cls.governance = (
            SERVICES / "ResearchEvidenceGovernanceService.php"
        ).read_text(encoding="utf-8")
        cls.promotion = (
            SERVICES / "PromotionInheritanceService.php"
        ).read_text(encoding="utf-8")

    def test_persistence_guard_covers_save_and_remove(self) -> None:
        self.assertTrue(GUARD.exists())
        self.assertIn("implements BeforeSave, BeforeRemove", self.guard)
        self.assertIn("function beforeRemove", self.guard)
        self.assertIn("cannot be deleted", self.guard)

    def test_immutable_core_covers_frozen_evidence_facts(self) -> None:
        for field in (
            "evidenceType",
            "peClaim",
            "peEvidenceText",
            "peContentSummary",
            "peSourceUrl",
            "peCanonicalUrl",
            "peCapturedAt",
            "peConfidence",
            "provenanceReference",
            "sourceAIRequestLogId",
            "sourceAIJobId",
            "supersedesId",
            "evidenceRevision",
        ):
            with self.subTest(field=field):
                self.assertIn(f"'{field}'", self.guard)

    def test_direct_validation_update_is_rejected(self) -> None:
        self.assertIn("isAttributeChanged('validationState')", self.guard)
        self.assertIn("VALIDATION_MUTATION_AUTHORIZED", self.guard)
        self.assertIn(
            "validationState mutation must use the governance service",
            self.guard,
        )

    def test_validation_transition_matrix_does_not_use_confidence(self) -> None:
        self.assertIn("VALIDATION_TRANSITIONS", self.governance)
        self.assertIn("VALIDATION_UNVALIDATED", self.governance)
        self.assertIn("VALIDATION_SUPERSEDED", self.governance)
        transition_method = self.governance.split(
            "public function transitionValidation", 1
        )[1].split("public function createCorrection", 1)[0]
        self.assertNotIn("Confidence", transition_method)
        self.assertNotIn("peConfidence", transition_method)

    def test_correction_creates_new_record_and_preserves_original(self) -> None:
        self.assertIn("public function createCorrection", self.governance)
        self.assertIn("getNewEntity('ResearchEvidence')", self.governance)
        self.assertIn("'supersedesId' => $original->getId()", self.governance)
        self.assertIn("'evidenceRevision' =>", self.governance)
        self.assertIn(
            "max(1, (int) $original->get('evidenceRevision')) + 1",
            self.governance,
        )
        self.assertIn("VALIDATION_SUPERSEDED", self.governance)
        self.assertIn("getTransactionManager()->run", self.governance)
        self.assertNotIn("removeEntity", self.governance)

    def test_correction_revision_is_derived_only_from_predecessor_revision(self) -> None:
        correction_method = self.governance.split(
            "public function createCorrection", 1
        )[1].split("private function assertEvidence", 1)[0]
        self.assertIn("$original->get('evidenceRevision')", correction_method)
        for forbidden_basis in (
            "peConfidence",
            "peClaim",
            "peEvidenceType",
            "evidenceType",
        ):
            with self.subTest(forbidden_basis=forbidden_basis):
                self.assertNotIn(forbidden_basis, correction_method)

    def test_promotion_lead_attachment_uses_narrow_authorization(self) -> None:
        self.assertIn("LEAD_ATTACHMENT_AUTHORIZED", self.promotion)
        self.assertIn("prospectPoolId", self.promotion)
        self.assertNotIn("getNewEntity('ResearchEvidence')", self.promotion)


class Phase3C21ProvenanceAndAclTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = GUARD.read_text(encoding="utf-8")
        cls.record_service = (
            SERVICES / "ResearchEvidenceService.php"
        ).read_text(encoding="utf-8")
        cls.governance = (
            SERVICES / "ResearchEvidenceGovernanceService.php"
        ).read_text(encoding="utf-8")
        cls.app_acl = load_json(APP_METADATA / "acl.json")
        cls.portal_acl = load_json(APP_METADATA / "aclPortal.json")
        cls.scope = load_json(SCOPES / "ResearchEvidence.json")

    def test_ai_inference_requires_c20_request_log_reference(self) -> None:
        self.assertIn("TYPE_AI_INFERENCE", self.record_service)
        self.assertIn(
            "AI_INFERENCE ResearchEvidence requires sourceAIRequestLogId.",
            self.record_service,
        )

    def test_optional_ai_job_must_match_request_log_owner(self) -> None:
        self.assertIn("getEntity(", self.guard)
        self.assertIn("'AIRequestLog'", self.guard)
        self.assertIn("get('aiJobId')", self.guard)
        self.assertIn(
            "sourceAIJobId must match the AIJob owned by sourceAIRequestLogId.",
            self.guard,
        )

    def test_c21_only_reads_c20_provenance(self) -> None:
        combined = self.guard + self.governance
        self.assertNotIn("getNewEntity('AIJob')", combined)
        self.assertNotIn("getNewEntity('AIRequestLog')", combined)
        self.assertNotIn("getNewEntity('PromptTemplate')", combined)
        self.assertNotIn("saveEntity($requestLog", combined)
        self.assertNotIn("saveEntity($job", combined)

    def test_acl_allows_governed_create_read_and_denies_delete(self) -> None:
        acl = self.app_acl["adminMandatory"]["scopeLevel"]["ResearchEvidence"]
        self.assertEqual(
            acl,
            {
                "create": "yes",
                "read": "all",
                "edit": "all",
                "delete": "no",
            },
        )
        self.assertFalse(
            self.app_acl["mandatory"]["scopeLevel"]["ResearchEvidence"]
        )
        self.assertFalse(
            self.portal_acl["mandatory"]["scopeLevel"]["ResearchEvidence"]
        )
        self.assertFalse(self.scope["aclPortal"])

    def test_no_provider_runtime_or_business_lifecycle_ownership(self) -> None:
        governed_sources = self.guard + self.record_service + self.governance
        forbidden = (
            "HttpClient",
            "curl_",
            "ProviderRegistry",
            "ProviderAdapter",
            "sendEmail",
            "Opportunity",
            "ProspectCandidate",
            "ActionLedger",
            "AutomationRule",
            "score",
            "qualification",
        )
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, governed_sources)


if __name__ == "__main__":
    unittest.main()
