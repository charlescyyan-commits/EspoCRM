"""Phase3C20 WP3.1 AIJob lifecycle-only skeleton contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ENTITY_DEF = AI_PLATFORM / "Resources" / "metadata" / "entityDefs" / "AIJob.json"
SCOPE = AI_PLATFORM / "Resources" / "metadata" / "scopes" / "AIJob.json"
ACL_DEF = AI_PLATFORM / "Resources" / "metadata" / "aclDefs" / "AIJob.json"
SERVICE = AI_PLATFORM / "Services" / "AIJobService.php"
SAVE_OPTION = AI_PLATFORM / "Services" / "AIJobStatusMutationSaveOption.php"
GUARD = AI_PLATFORM / "Hooks" / "AIJob" / "AIJobStatusMutationGuard.php"

STATUSES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"}
FAILURE_CATEGORIES = [
    "NETWORK",
    "PROVIDER",
    "AUTH",
    "RATE_LIMIT",
    "VALIDATION",
    "UNKNOWN",
    "QUOTA",
    "CONTENT_FILTER",
]
EXPECTED_FIELDS = {
    "name",
    "capability",
    "purpose",
    "requestedBy",
    "policyVersion",
    "status",
    "attemptCount",
    "failureCategory",
    "lastError",
    "nextRetryAt",
    "startedAt",
    "completedAt",
    "executionMode",
    "idempotencyKey",
    "resultReference",
    "createdAt",
}
FORBIDDEN_FIELDS = {
    "apiKey",
    "token",
    "password",
    "secret",
    "providerCredential",
    "leadScore",
    "qualificationScore",
    "retryAlgorithm",
    "backoffPolicy",
    "providerRetryStrategy",
}
FORBIDDEN_RUNTIME_NAMES = (
    "AIRequestLog",
    "PromptTemplate",
    "CapabilityRegistry",
    "ProviderRoute",
    "ProviderHealth",
    "Prospecting",
    "Lead",
    "Opportunity",
    "ResearchEvidence",
    "ProspectCandidate",
    "curl_init",
    "Guzzle",
    "HttpClient",
    "file_get_contents",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def metadata() -> dict[str, object]:
    return json.loads(read(ENTITY_DEF))


class Phase3C20WP31AIJobSkeletonTests(unittest.TestCase):
    def test_entity_metadata_exists_with_exact_skeleton_fields(self) -> None:
        self.assertTrue(ENTITY_DEF.is_file())
        entity = metadata()
        self.assertEqual(set(entity["fields"]), EXPECTED_FIELDS)
        self.assertEqual(entity["fields"]["status"]["type"], "enum")
        self.assertEqual(set(entity["fields"]["status"]["options"]), STATUSES)
        self.assertEqual(entity["fields"]["status"]["default"], "QUEUED")
        self.assertEqual(entity["fields"]["executionMode"]["options"], ["LIVE", "DRY_RUN"])
        self.assertEqual(entity["fields"]["attemptCount"]["default"], 0)
        self.assertEqual(entity["fields"]["failureCategory"]["options"], FAILURE_CATEGORIES)

    def test_identity_and_links_are_generic_and_not_business_relations(self) -> None:
        entity = metadata()
        self.assertEqual(entity["links"], {"requestedBy": {"type": "belongsTo", "entity": "User"}})
        self.assertTrue(entity["fields"]["idempotencyKey"]["required"])
        self.assertEqual(entity["fields"]["resultReference"]["type"], "varchar")
        self.assertEqual(entity["indexes"]["idempotencyKey"], {"type": "unique", "columns": ["idempotencyKey", "deleteId"]})

    def test_forbidden_fields_and_non_governance_entities_are_absent(self) -> None:
        entity = metadata()
        self.assertTrue(FORBIDDEN_FIELDS.isdisjoint(entity["fields"]))
        source = read(ENTITY_DEF)
        for name in FORBIDDEN_FIELDS | {"ResearchEvidence", "ProspectCandidate", "Lead", "Opportunity"}:
            self.assertNotRegex(source, rf'"{re.escape(name)}"\\s*:')

    def test_scope_and_acl_are_internal_non_ui_basics(self) -> None:
        self.assertEqual(
            json.loads(read(SCOPE)),
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
        self.assertEqual(json.loads(read(ACL_DEF)), {})
        for forbidden in ("Api", "Controllers", "Views", "Resources/metadata/clientDefs"):
            self.assertFalse((AI_PLATFORM / forbidden).exists(), msg=forbidden)
        self.assertFalse((AI_PLATFORM / "Resources" / "layouts" / "AIJob").exists())

    def test_state_machine_has_only_authorized_edges(self) -> None:
        source = read(SERVICE)
        for status in STATUSES:
            self.assertIn(f"public const STATUS_{status}", source)
        for edge in (
            "self::STATUS_QUEUED => [self::STATUS_RUNNING, self::STATUS_CANCELLED]",
            "self::STATUS_RUNNING => [",
            "self::STATUS_FAILED => [self::STATUS_QUEUED]",
            "self::STATUS_SUCCEEDED => []",
            "self::STATUS_CANCELLED => []",
        ):
            self.assertIn(edge, source)
        self.assertNotIn("STATUS_CREATED", source)
        self.assertNotIn("WAITING_RETRY", source)

    def test_service_creates_queued_jobs_under_create_acl(self) -> None:
        source = read(SERVICE)
        self.assertIn("$this->acl->check(self::ENTITY_TYPE, 'create')", source)
        self.assertIn("$this->entityManager->getEntity(self::ENTITY_TYPE)", source)
        self.assertIn("'status' => self::STATUS_QUEUED", source)
        self.assertIn("'attemptCount' => 0", source)
        self.assertIn("assertCreateAttributes", source)

    def test_service_validates_illegal_transitions_and_direct_status_write_is_guarded(self) -> None:
        service = read(SERVICE)
        guard = read(GUARD)
        self.assertIn("validateTransition", service)
        self.assertIn("AIJob transition {$currentStatus} -> {$targetStatus} is not allowed.", service)
        self.assertIn("AIJobStatusMutationSaveOption::AI_JOB_STATUS_MUTATION_AUTHORIZED", service)
        self.assertIn("AIJobStatusMutationSaveOption::AI_JOB_STATUS_MUTATION_AUTHORIZED", guard)
        self.assertIn("AIJob lifecycle fields may only be written by AIJobService.", guard)
        self.assertIn("AIJob creation must initialize to QUEUED with zero attempts.", guard)

    def test_idempotency_is_deterministic(self) -> None:
        source = read(SERVICE)
        self.assertIn("findExistingIdempotencyKey", source)
        self.assertIn("assertEquivalentIdempotencyContext", source)
        self.assertIn("AIJob idempotency key belongs to a different execution context.", source)
        self.assertIn("return $existing;", source)

    def test_dry_run_is_a_mode_not_an_execution_path(self) -> None:
        source = read(SERVICE)
        self.assertIn("public const EXECUTION_MODE_DRY_RUN = 'DRY_RUN'", source)
        self.assertIn("unsupported executionMode", source)
        self.assertNotRegex(source, r"->(?:send|dispatch|execute)\s*\(")

    def test_module_has_no_provider_or_business_runtime_dependency(self) -> None:
        for path in (SERVICE, SAVE_OPTION, GUARD, ENTITY_DEF, SCOPE, ACL_DEF):
            source = read(path)
            for name in FORBIDDEN_RUNTIME_NAMES:
                self.assertNotIn(name, source, msg=f"{path}: {name}")
        php_sources = list(AI_PLATFORM.rglob("*.php"))
        self.assertTrue(php_sources)
        for path in php_sources:
            source = read(path)
            self.assertNotRegex(source, r"https?://")
            self.assertNotRegex(source, r"\\b(?:curl_exec|stream_socket_client|fsockopen)\\b")


if __name__ == "__main__":
    unittest.main()
