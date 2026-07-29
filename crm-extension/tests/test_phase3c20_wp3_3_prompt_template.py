"""Phase3C20 WP3.3 PromptTemplate governance skeleton contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "crm-extension" / "files" / "custom" / "Espo"
MODULE = CUSTOM / "Modules" / "AIPlatform"
ENTITY_DEF = MODULE / "Resources" / "metadata" / "entityDefs" / "PromptTemplate.json"
SCOPE = MODULE / "Resources" / "metadata" / "scopes" / "PromptTemplate.json"
ACL_DEF = MODULE / "Resources" / "metadata" / "aclDefs" / "PromptTemplate.json"
ENTITY_ACL = MODULE / "Resources" / "metadata" / "entityAcl" / "PromptTemplate.json"
APP_ACL = MODULE / "Resources" / "metadata" / "app" / "acl.json"
PORTAL_ACL = MODULE / "Resources" / "metadata" / "app" / "aclPortal.json"
ENTITY = MODULE / "Entities" / "PromptTemplate.php"
SERVICE = MODULE / "Services" / "PromptTemplateService.php"
SAVE_OPTION = MODULE / "Services" / "PromptTemplateSaveOption.php"
GUARD = MODULE / "Hooks" / "PromptTemplate" / "PromptTemplateMutationGuard.php"

REQUIRED_FIELDS = {
    "name",
    "templateKey",
    "version",
    "contentHash",
    "capability",
    "purpose",
    "templateBody",
    "status",
}
FORBIDDEN_FIELDS = {
    "provider",
    "apiUrl",
    "apiKey",
    "token",
    "credential",
    "leadId",
    "prospectId",
    "opportunityId",
    "score",
    "qualification",
}
BOUNDARY_TERMS = (
    "Prospecting",
    "Lead",
    "Opportunity",
    "SendExecution",
    "ReplyEvent",
    "Email",
    "AIJob",
    "AIRequestLog",
    "DeepSeek",
    "OpenAI",
)
EGRESS_PATTERNS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b",
    r"\bGuzzle\b",
    r"\bHttpClient\b",
    r"\bfile_get_contents\b",
    r"\bstream_socket_client\b",
    r"\bfsockopen\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict[str, object]:
    return json.loads(read(path))


class Phase3C20WP33PromptTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity_defs = load(ENTITY_DEF)
        cls.scope = load(SCOPE)
        cls.service = read(SERVICE)
        cls.guard = read(GUARD)

    def test_entity_and_metadata_exist(self) -> None:
        for path in (
            ENTITY,
            ENTITY_DEF,
            SCOPE,
            ACL_DEF,
            ENTITY_ACL,
            SERVICE,
            SAVE_OPTION,
            GUARD,
        ):
            self.assertTrue(path.is_file(), msg=str(path))

        self.assertIn("namespace Espo\\Modules\\AIPlatform\\Entities;", read(ENTITY))
        self.assertIn("final class PromptTemplate extends Entity", read(ENTITY))
        self.assertIn("public const ENTITY_TYPE = 'PromptTemplate';", read(ENTITY))

    def test_required_fields_and_types_are_declared(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertTrue(REQUIRED_FIELDS.issubset(fields))
        self.assertEqual(
            {name: fields[name]["type"] for name in REQUIRED_FIELDS},
            {
                "name": "varchar",
                "templateKey": "varchar",
                "version": "int",
                "contentHash": "varchar",
                "capability": "varchar",
                "purpose": "varchar",
                "templateBody": "text",
                "status": "enum",
            },
        )
        for name in REQUIRED_FIELDS:
            self.assertTrue(fields[name]["required"], msg=name)
        self.assertEqual(fields["contentHash"]["maxLength"], 64)
        self.assertEqual(fields["version"]["min"], 1)

    def test_scope_is_internal_base_entity_with_implicit_id(self) -> None:
        self.assertEqual(
            self.scope,
            {
                "entity": True,
                "object": False,
                "tab": False,
                "acl": True,
                "aclPortal": False,
                "customizable": False,
                "importable": False,
                "module": "AIPlatform",
                "type": "Base",
                "statusField": "status",
            },
        )
        self.assertEqual(self.entity_defs["fields"]["name"]["type"], "varchar")

    def test_lifecycle_metadata_is_exact(self) -> None:
        status = self.entity_defs["fields"]["status"]
        self.assertEqual(status["options"], ["DRAFT", "ACTIVE", "RETIRED"])
        self.assertEqual(status["default"], "DRAFT")
        self.assertTrue(status["readOnly"])

    def test_lifecycle_service_allows_only_forward_edges(self) -> None:
        expected_rows = {
            "STATUS_DRAFT": "self::STATUS_ACTIVE",
            "STATUS_ACTIVE": "self::STATUS_RETIRED",
            "STATUS_RETIRED": "",
        }
        for status, expected_target in expected_rows.items():
            row = re.search(
                rf"self::{status}\s*=>\s*\[(.*?)\]",
                self.service,
                flags=re.S,
            )
            self.assertIsNotNone(row, msg=status)
            self.assertIn(expected_target, row.group(1))

        retired = re.search(
            r"self::STATUS_RETIRED\s*=>\s*\[(.*?)\]",
            self.service,
            flags=re.S,
        )
        self.assertIsNotNone(retired)
        self.assertNotIn("STATUS_ACTIVE", retired.group(1))
        self.assertIn("public function activate(Entity $template): Entity", self.service)
        self.assertIn("public function retire(Entity $template): Entity", self.service)

    def test_version_pair_has_database_and_service_uniqueness_guards(self) -> None:
        index = self.entity_defs["indexes"]["templateKeyVersion"]
        self.assertEqual(index["type"], "unique")
        self.assertEqual(index["columns"], ["templateKey", "version", "deleteId"])
        self.assertIn("private function assertVersionAvailable", self.service)
        self.assertIn("'templateKey' => $templateKey", self.service)
        self.assertIn("'version' => $version", self.service)
        self.assertIn("throw new Conflict(", self.service)

    def test_new_versions_keep_logical_key_and_require_higher_version(self) -> None:
        self.assertIn("public function createNewVersion(", self.service)
        self.assertIn("'templateKey' => (string) $source->get('templateKey')", self.service)
        self.assertIn("if ($version <= $currentVersion)", self.service)
        self.assertIn("'status' => self::STATUS_DRAFT", self.service)

    def test_hash_is_sha256_and_guarded_against_body(self) -> None:
        self.assertIn("return hash('sha256', $templateBody);", self.service)
        self.assertIn("PromptTemplateService::hashContent(", self.guard)
        self.assertIn("hash_equals($expectedHash", self.guard)
        self.assertIn("PromptTemplate contentHash must match templateBody.", self.guard)

    def test_referenced_active_version_is_immutable(self) -> None:
        for field in ("templateKey", "version", "contentHash", "templateBody"):
            self.assertIn(f"'{field}'", self.service)
        self.assertIn("$governedStatus", self.service)
        self.assertIn("self::STATUS_RETIRED", self.service)
        self.assertIn("$referenced", self.service)
        self.assertIn("isAttributeChanged($field)", self.service)
        self.assertIn("create a new version.", self.service)
        self.assertIn(
            "PromptTemplateService::assertImmutableFieldsUnchanged($entity);",
            self.guard,
        )

    def test_reference_marker_is_internal_one_way_and_service_owned(self) -> None:
        self.assertEqual(
            self.entity_defs["fields"]["hasBeenReferenced"],
            {
                "type": "bool",
                "required": True,
                "readOnly": True,
                "default": False,
            },
        )
        self.assertEqual(
            load(ENTITY_ACL),
            {"fields": {"hasBeenReferenced": {"internal": True}}},
        )
        self.assertIn("public function markReferenced(Entity $template): Entity", self.service)
        self.assertIn("REFERENCE_MARK_AUTHORIZED => true", self.service)
        self.assertIn("getFetched('hasBeenReferenced')", self.guard)

    def test_status_mutation_must_use_service(self) -> None:
        self.assertIn("implements BeforeSave", self.guard)
        self.assertIn("public static int $order = 1000;", self.guard)
        self.assertIn("LIFECYCLE_MUTATION_AUTHORIZED", self.guard)
        self.assertIn(
            "PromptTemplate status mutation must use PromptTemplateService.",
            self.guard,
        )
        self.assertIn("LIFECYCLE_MUTATION_AUTHORIZED => true", self.service)

    def test_forbidden_secret_routing_and_business_fields_are_absent(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertTrue(FORBIDDEN_FIELDS.isdisjoint(fields))
        metadata_source = read(ENTITY_DEF)
        for field in FORBIDDEN_FIELDS:
            self.assertIsNone(
                re.search(rf'"{re.escape(field)}"\s*:', metadata_source, re.I),
                msg=field,
            )

    def test_boundary_dependencies_are_absent(self) -> None:
        runtime = "\n".join(read(path) for path in (ENTITY, SERVICE, SAVE_OPTION, GUARD))
        for term in BOUNDARY_TERMS:
            self.assertIsNone(
                re.search(rf"\b{re.escape(term)}\b", runtime),
                msg=term,
            )
        for pattern in EGRESS_PATTERNS:
            self.assertIsNone(re.search(pattern, runtime, re.I), msg=pattern)

    def test_no_ui_or_execution_surface_is_added(self) -> None:
        forbidden_paths = (
            MODULE / "Resources" / "layouts" / "PromptTemplate",
            MODULE / "Resources" / "metadata" / "clientDefs" / "PromptTemplate.json",
            MODULE / "Controllers" / "PromptTemplate.php",
            MODULE / "Api",
            MODULE / "Jobs",
            MODULE / "Actions",
        )
        for path in forbidden_paths:
            self.assertFalse(path.exists(), msg=str(path))

    def test_acl_denies_portal_and_record_deletion(self) -> None:
        acl = load(APP_ACL)
        self.assertFalse(acl["mandatory"]["scopeLevel"]["PromptTemplate"])
        self.assertEqual(
            acl["adminMandatory"]["scopeLevel"]["PromptTemplate"],
            {
                "create": "yes",
                "read": "all",
                "edit": "all",
                "delete": "no",
            },
        )
        self.assertFalse(load(PORTAL_ACL)["mandatory"]["scopeLevel"]["PromptTemplate"])


if __name__ == "__main__":
    unittest.main()
