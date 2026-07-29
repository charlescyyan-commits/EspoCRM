"""Phase3C20 WP3.2 AIRequestLog execution-evidence contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ENTITY_DEF = MODULE / "Resources" / "metadata" / "entityDefs" / "AIRequestLog.json"
SCOPE = MODULE / "Resources" / "metadata" / "scopes" / "AIRequestLog.json"
ACL_DEF = MODULE / "Resources" / "metadata" / "aclDefs" / "AIRequestLog.json"
APP_ACL = MODULE / "Resources" / "metadata" / "app" / "acl.json"
PORTAL_ACL = MODULE / "Resources" / "metadata" / "app" / "aclPortal.json"
ENTITY = MODULE / "Entities" / "AIRequestLog.php"
SERVICE = MODULE / "Services" / "AIRequestLogService.php"
SAVE_OPTION = MODULE / "Services" / "AIRequestLogSaveOption.php"
GUARD = MODULE / "Hooks" / "AIRequestLog" / "AIRequestLogAppendOnlyGuard.php"

REQUIRED_FIELDS = {
    "name", "aiJob", "attemptId", "attemptNumber", "capability", "purpose",
    "provider", "model", "promptTemplateId", "promptTemplateVersion",
    "promptTemplateHash", "inputTokens", "outputTokens", "totalTokens",
    "costAmount", "costCurrency", "latencyMs", "status", "errorClass",
    "failureCategory", "createdAt", "createdBy",
}
FORBIDDEN_FIELDS = {
    "prospectId", "leadId", "opportunityId", "providerSecret", "apiKey",
    "credential", "rawPrompt", "rawResponse", "requestBody", "responseBody",
    "token", "password", "secret",
}
PROSPECTING_TERMS = (
    "Prospecting", "ProspectCandidate", "ResearchEvidence", "QualificationInsight",
    "Lead", "Opportunity", "SendExecution", "ReplyEvent", "Email",
)
EGRESS_PATTERNS = (
    r"\bcurl(?:_[A-Za-z0-9_]+)?\b", r"\bGuzzle\b", r"\bHttpClient\b",
    r"\bfile_get_contents\b", r"\bstream_socket_client\b", r"\bfsockopen\b",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict[str, object]:
    return json.loads(read(path))


class Phase3C20WP32AIRequestLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entity_defs = load(ENTITY_DEF)
        cls.service = read(SERVICE)
        cls.guard = read(GUARD)

    def test_entity_and_metadata_exist(self) -> None:
        for path in (ENTITY, ENTITY_DEF, SCOPE, ACL_DEF, SERVICE, SAVE_OPTION, GUARD):
            self.assertTrue(path.is_file(), msg=str(path))
        self.assertIn("namespace Espo\\Modules\\AIPlatform\\Entities;", read(ENTITY))
        self.assertIn("final class AIRequestLog extends Entity", read(ENTITY))
        self.assertIn("public const ENTITY_TYPE = 'AIRequestLog';", read(ENTITY))

    def test_entity_fields_are_execution_evidence_metadata(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertEqual(set(fields), REQUIRED_FIELDS)
        self.assertEqual(fields["aiJob"], {"type": "link", "required": True, "readOnly": True})
        self.assertEqual(fields["attemptNumber"]["min"], 1)
        self.assertEqual(fields["promptTemplateHash"]["maxLength"], 64)
        self.assertEqual(fields["totalTokens"]["min"], 0)
        self.assertEqual(fields["costAmount"]["type"], "float")
        self.assertEqual(fields["latencyMs"]["min"], 0)
        self.assertEqual(
            self.entity_defs["links"],
            {
                "aiJob": {"type": "belongsTo", "entity": "AIJob"},
                "createdBy": {"type": "belongsTo", "entity": "User"},
            },
        )

    def test_only_aijob_is_a_business_execution_reference(self) -> None:
        source = read(ENTITY_DEF)
        self.assertIn('"aiJobId"', source)
        for field in ("prospectId", "leadId", "opportunityId"):
            self.assertNotIn(f'"{field}"', source)
        self.assertNotIn('"PromptTemplate"', source)

    def test_scope_is_internal_and_has_no_custom_controller_surface(self) -> None:
        self.assertEqual(
            load(SCOPE),
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
        self.assertEqual(load(ACL_DEF), {})
        self.assertFalse((MODULE / "Controllers" / "AIRequestLog.php").exists())
        self.assertFalse((MODULE / "Api").exists())
        self.assertFalse((MODULE / "Actions").exists())

    def test_create_passes_only_through_the_acl_checked_service(self) -> None:
        self.assertIn("$this->acl->check(self::ENTITY_TYPE, 'create')", self.service)
        self.assertIn("public function create(array $attributes): Entity", self.service)
        self.assertIn("AIRequestLogSaveOption::AI_REQUEST_LOG_CREATE_AUTHORIZED => true", self.service)
        self.assertIn("AIRequestLog creation must use AIRequestLogService.", self.guard)
        self.assertIn("$entity->isNew()", self.guard)

    def test_update_and_delete_fail_at_the_persistence_guard(self) -> None:
        self.assertIn("implements BeforeSave, BeforeRemove", self.guard)
        self.assertIn("AIRequestLog is append-only and cannot be modified.", self.guard)
        self.assertIn("public function beforeRemove(Entity $entity, RemoveOptions $options): void", self.guard)
        self.assertIn("AIRequestLog is append-only and cannot be deleted.", self.guard)

    def test_generic_controller_acl_allows_create_read_but_denies_edit_delete(self) -> None:
        acl = load(APP_ACL)["adminMandatory"]["scopeLevel"]["AIRequestLog"]
        self.assertEqual(acl, {"create": "yes", "read": "all", "edit": "no", "delete": "no"})
        self.assertFalse(load(APP_ACL)["mandatory"]["scopeLevel"]["AIRequestLog"])
        self.assertFalse(load(PORTAL_ACL)["mandatory"]["scopeLevel"]["AIRequestLog"])

    def test_payloads_secrets_and_unsafe_error_evidence_are_not_persisted(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertTrue(FORBIDDEN_FIELDS.isdisjoint(fields))
        metadata_source = read(ENTITY_DEF)
        for field in FORBIDDEN_FIELDS:
            self.assertIsNone(re.search(rf'"{re.escape(field)}"\s*:', metadata_source, re.I), msg=field)
        self.assertNotIn("raw exception", self.service.lower())
        self.assertNotIn("stack trace", self.service.lower())

    def test_prompt_provenance_saves_reference_version_and_hash_not_prompt_text(self) -> None:
        for field in ("promptTemplateId", "promptTemplateVersion", "promptTemplateHash"):
            self.assertIn(f"'{field}'", self.service)
            self.assertTrue(self.entity_defs["fields"][field]["readOnly"])
        self.assertIn("must be a SHA-256 hex digest", self.service)
        self.assertIn("assertPromptTemplateProvenance", self.service)
        self.assertIn("$this->promptTemplateService->markReferenced($template);", self.service)
        self.assertNotIn("rawPrompt", self.service)
        self.assertNotIn("templateBody", self.service)

    def test_cost_usage_metadata_is_accepted_and_consistent(self) -> None:
        for field in ("inputTokens", "outputTokens", "totalTokens", "costAmount", "costCurrency", "latencyMs"):
            self.assertIn(f"'{field}'", self.service)
        self.assertIn("totalTokens must equal inputTokens plus outputTokens.", self.service)
        self.assertIn("costCurrency must be an ISO 4217 code.", self.service)

    def test_has_no_provider_execution_or_prospecting_dependency(self) -> None:
        runtime = "\n".join(read(path) for path in (ENTITY, SERVICE, SAVE_OPTION, GUARD))
        for term in PROSPECTING_TERMS:
            self.assertIsNone(re.search(rf"\b{re.escape(term)}\b", runtime), msg=term)
        for pattern in EGRESS_PATTERNS:
            self.assertIsNone(re.search(pattern, runtime, re.I), msg=pattern)
        self.assertNotRegex(runtime, r"https?://")


if __name__ == "__main__":
    unittest.main()
