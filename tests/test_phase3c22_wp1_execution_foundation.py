"""Phase3C22 WP1 autonomous prospecting execution foundation contracts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
ENTITIES = MODULE / "Entities"
HOOKS = MODULE / "Hooks"

ENTITY_TYPES = (
    "ProspectCandidate",
    "ProspectRun",
    "ActionGate",
    "ExecutionLedger",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C22WP1EntityTests(unittest.TestCase):
    def test_all_execution_foundation_entity_surfaces_exist(self) -> None:
        for entity_type in ENTITY_TYPES:
            with self.subTest(entity_type=entity_type):
                self.assertTrue((ENTITIES / f"{entity_type}.php").is_file())
                self.assertTrue((ENTITY_DEFS / f"{entity_type}.json").is_file())
                self.assertTrue((SCOPES / f"{entity_type}.json").is_file())
                self.assertTrue((ACL_DEFS / f"{entity_type}.json").is_file())

                scope = load_json(SCOPES / f"{entity_type}.json")
                self.assertTrue(scope["entity"])
                self.assertTrue(scope["acl"])
                self.assertFalse(scope["aclPortal"])
                self.assertFalse(scope["tab"])
                self.assertFalse(scope["customizable"])
                self.assertFalse(scope["importable"])

    def test_prospect_candidate_is_not_crm_identity(self) -> None:
        definition = load_json(ENTITY_DEFS / "ProspectCandidate.json")
        fields = definition["fields"]
        links = definition["links"]

        self.assertTrue({"name", "candidateKey", "prospectRun"}.issubset(fields))
        self.assertTrue(
            {"leadId", "lead", "opportunityId", "opportunity", "salesStage"}
            .isdisjoint(fields)
        )
        self.assertEqual(links["prospectRun"]["entity"], "ProspectRun")
        self.assertEqual(links["prospectPool"]["entity"], "ProspectPool")
        self.assertTrue(
            {"Lead", "Opportunity", "Account"}.isdisjoint(
                link.get("entity") for link in links.values()
            )
        )

    def test_prospect_run_is_execution_container_without_reasoning(self) -> None:
        definition = load_json(ENTITY_DEFS / "ProspectRun.json")
        fields = definition["fields"]

        self.assertTrue(
            {"name", "runKey", "executionScope", "maxCandidates", "candidates"}
            .issubset(fields)
        )
        self.assertTrue(
            {
                "reasoning",
                "prompt",
                "model",
                "confidence",
                "score",
                "canonicalScore",
                "qualification",
                "leadId",
                "opportunityId",
                "salesStage",
            }.isdisjoint(fields)
        )


class Phase3C22WP1ActionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.definition = load_json(ENTITY_DEFS / "ActionGate.json")
        cls.service = (SERVICES / "ActionGateService.php").read_text(
            encoding="utf-8"
        )
        cls.guard = (
            HOOKS / "ActionGate" / "ActionGateDecisionGuard.php"
        ).read_text(encoding="utf-8")

    def test_gate_decision_contract_is_frozen(self) -> None:
        decision = self.definition["fields"]["decision"]
        self.assertEqual(
            decision["options"],
            ["PENDING", "APPROVED", "DENIED", "DEFERRED"],
        )
        self.assertEqual(decision["default"], "PENDING")
        self.assertTrue(decision["readOnly"])

    def test_execution_requires_approved_gate(self) -> None:
        self.assertIn("public function assertApprovedForExecution", self.service)
        approved_method = self.service.split(
            "public function assertApprovedForExecution", 1
        )[1].split("private function assertGate", 1)[0]
        self.assertIn("self::DECISION_APPROVED", approved_method)
        self.assertIn(
            "No C22 execution is permitted without an APPROVED ActionGate.",
            approved_method,
        )
        self.assertIn("throw new Forbidden", approved_method)

    def test_gate_creation_and_decision_are_service_only(self) -> None:
        self.assertIn("ACTION_GATE_CREATE_AUTHORIZED", self.guard)
        self.assertIn("ACTION_GATE_DECISION_AUTHORIZED", self.guard)
        self.assertIn("creation must use ActionGateService", self.guard)
        self.assertIn("decision must use ActionGateService", self.guard)
        self.assertIn("function beforeRemove", self.guard)
        self.assertIn("ActionGate cannot be deleted", self.guard)

    def test_gate_decision_uses_authenticated_actor(self) -> None:
        self.assertIn("private User $user", self.service)
        self.assertIn("'requestedById' => $actorId", self.service)
        self.assertIn("'decidedById' => $this->authenticatedActorId()", self.service)
        self.assertIn("Only a PENDING ActionGate can be decided", self.service)


class Phase3C22WP1ExecutionLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.definition = load_json(ENTITY_DEFS / "ExecutionLedger.json")
        cls.service = (SERVICES / "ExecutionLedgerService.php").read_text(
            encoding="utf-8"
        )
        cls.guard = (
            HOOKS / "ExecutionLedger" / "ExecutionLedgerAppendOnlyGuard.php"
        ).read_text(encoding="utf-8")

    def test_ledger_is_metadata_only_execution_evidence(self) -> None:
        fields = self.definition["fields"]
        self.assertTrue(
            {
                "prospectCandidate",
                "prospectRun",
                "actionGate",
                "eventType",
                "outcome",
                "failureCategory",
                "actor",
                "occurredAt",
                "supersedes",
            }.issubset(fields)
        )
        for field_name, field in fields.items():
            if field_name not in {"supersededBy"}:
                with self.subTest(field_name=field_name):
                    self.assertTrue(field.get("readOnly", False))

    def test_ledger_append_only_guard_blocks_update_and_delete(self) -> None:
        self.assertIn("implements BeforeSave, BeforeRemove", self.guard)
        self.assertIn("if (!$entity->isNew())", self.guard)
        self.assertIn("append-only and cannot be modified", self.guard)
        self.assertIn("append-only and cannot be deleted", self.guard)
        self.assertIn("EXECUTION_LEDGER_CREATE_AUTHORIZED", self.guard)
        self.assertIn("creation must use ExecutionLedgerService", self.guard)

    def test_execution_events_call_approved_gate_guard(self) -> None:
        self.assertIn("self::EVENT_EXECUTION_STARTED", self.service)
        self.assertIn("self::EVENT_EXECUTION_RESULT", self.service)
        self.assertIn(
            "$this->actionGateService->assertApprovedForExecution($gate)",
            self.service,
        )
        self.assertIn("assertSameExecutionContext", self.service)

    def test_ledger_acl_denies_edit_and_delete(self) -> None:
        acl = load_json(APP / "acl.json")
        ledger_acl = acl["adminMandatory"]["scopeLevel"]["ExecutionLedger"]
        self.assertEqual(ledger_acl["create"], "yes")
        self.assertEqual(ledger_acl["read"], "all")
        self.assertEqual(ledger_acl["edit"], "no")
        self.assertEqual(ledger_acl["delete"], "no")


class Phase3C22WP1BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.php_sources = {
            path.relative_to(MODULE).as_posix(): path.read_text(encoding="utf-8")
            for path in (
                SERVICES / "ActionGateService.php",
                SERVICES / "ExecutionLedgerService.php",
                SERVICES / "C22ExecutionSaveOption.php",
                HOOKS / "ActionGate" / "ActionGateDecisionGuard.php",
                HOOKS
                / "ExecutionLedger"
                / "ExecutionLedgerAppendOnlyGuard.php",
            )
        }

    def test_c22_has_no_crm_lifecycle_mutation_path(self) -> None:
        forbidden_calls = (
            "getNewEntity('Lead')",
            'getNewEntity("Lead")',
            "getNewEntity('Opportunity')",
            'getNewEntity("Opportunity")',
            "getNewEntity('Account')",
            'getNewEntity("Account")',
            "saveEntity($lead",
            "saveEntity($opportunity",
            "salesStage",
            "canonical_score",
        )
        for path, source in self.php_sources.items():
            for forbidden in forbidden_calls:
                with self.subTest(path=path, forbidden=forbidden):
                    self.assertNotIn(forbidden, source)

    def test_c22_has_no_provider_or_message_execution(self) -> None:
        forbidden_runtime = (
            "curl_",
            "file_get_contents(",
            "GuzzleHttp",
            "HttpClient",
            "->request(",
            "->post(",
            "->send(",
            "smtp",
            "WhatsApp",
            "EmailDeliveryProvider",
        )
        for path, source in self.php_sources.items():
            for forbidden in forbidden_runtime:
                with self.subTest(path=path, forbidden=forbidden):
                    self.assertNotIn(forbidden, source)

    def test_no_automation_loop_or_provider_authority_fields(self) -> None:
        forbidden_fields = {
            "apiKey",
            "credential",
            "providerUrl",
            "emailBody",
            "whatsAppMessage",
            "automationRuleId",
            "leadId",
            "opportunityId",
            "salesStage",
        }
        for entity_type in ENTITY_TYPES:
            fields = load_json(ENTITY_DEFS / f"{entity_type}.json")["fields"]
            with self.subTest(entity_type=entity_type):
                self.assertTrue(forbidden_fields.isdisjoint(fields))

    def test_acl_and_portal_boundaries_cover_exact_wp1_entities(self) -> None:
        app_acl = load_json(APP / "acl.json")
        portal_acl = load_json(APP / "aclPortal.json")
        for entity_type in ENTITY_TYPES:
            with self.subTest(entity_type=entity_type):
                self.assertIn(entity_type, app_acl["mandatory"]["scopeLevel"])
                self.assertIn(entity_type, app_acl["adminMandatory"]["scopeLevel"])
                self.assertIn(entity_type, portal_acl["mandatory"]["scopeLevel"])
                self.assertFalse(
                    portal_acl["mandatory"]["scopeLevel"][entity_type]
                )


if __name__ == "__main__":
    unittest.main()
