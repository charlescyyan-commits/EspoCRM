"""Phase3C20 RT-WP7 Lite Runtime Guards Foundation contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
SERVICES = AI_PLATFORM / "Services"

RULE = SERVICES / "AIGuardRule.php"
RESULT = SERVICES / "AIGuardValidationResult.php"
SERVICE = SERVICES / "AIGuardService.php"

FOUNDATION_STATE = SERVICES / "AIFoundationState.php"
FAILURE_METADATA = SERVICES / "AIFailureMetadata.php"
RESERVATION_METADATA = SERVICES / "AIReservationMetadata.php"
DISPATCH_SERVICE = SERVICES / "AIDispatchService.php"
PROVIDER_BINDING_SERVICE = SERVICES / "ProviderBindingService.php"

INVARIANT_REGISTRY = ROOT / "docs" / "adr" / "C20_INVARIANT_REGISTRY.md"
COMPLETION_BASE = (
    ROOT
    / "chitu-connector"
    / "chitu_connector"
    / "acquisition"
    / "providers"
    / "completion"
    / "base.py"
)

RULE_IDS = {
    "CAPABILITY",
    "PURPOSE",
    "BINDING_REFERENCE",
    "FOUNDATION_STATE",
    "FAILURE_CODE",
    "RESERVATION_INTENT",
    "PAYLOAD_SAFETY",
}

REASON_CODES = {
    "UNKNOWN_CAPABILITY",
    "COMMERCIAL_BRIEF_FORBIDDEN",
    "PURPOSE_MISSING",
    "PURPOSE_INVALID",
    "BINDING_REFERENCE_MISSING",
    "SECRET_SHAPED_INPUT",
    "INVALID_FOUNDATION_STATE",
    "INVALID_FAILURE_CODE",
    "INVALID_RESERVATION_INTENT",
    "OWNER_REFERENCE_REQUIRED",
    "EXECUTION_CONTROL_FORBIDDEN",
    "C25_AUTHORITY_FORBIDDEN",
}

COMPLETION_PORTFOLIO = {
    "RESEARCH_EVIDENCE",
    "QUALIFICATION_INSIGHT",
    "DRAFT_ASSISTANCE",
    "REPLY_ASSISTANCE",
    "COMMERCIAL_BRIEF",
}

FORBIDDEN_RUNTIME_MARKERS = (
    "curl_init",
    "curl_exec",
    "GuzzleHttp",
    "file_get_contents",
    "fsockopen",
    "stream_socket_client",
    "ConnectorBoundary",
    "chitu_connector",
    "subprocess",
    "AIRetryPolicy",
    "IdempotencyReservation",
    "AIDispatchWorker",
    "->saveEntity(",
    "registerPurpose(",
    "AclManager",
    "RoleService",
    "WorkflowManager",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C20RTWP7RuntimeGuardsTests(unittest.TestCase):
    def test_allowlist_files_exist(self) -> None:
        for path in (RULE, RESULT, SERVICE):
            self.assertTrue(path.is_file(), msg=str(path))

    def test_guard_rule_dimensions_and_reasons(self) -> None:
        text = read(RULE)
        for rule_id in RULE_IDS:
            self.assertIn(f"const {rule_id}", text)
            self.assertIn(f"'{rule_id}'", text)
        for reason in REASON_CODES:
            self.assertIn(f"'{reason}'", text)
        for capability in COMPLETION_PORTFOLIO:
            self.assertIn(f"'{capability}'", text)
        self.assertIn("Guard ≠ authorization engine", text)
        self.assertIn("Guard ≠ workflow engine", text)
        self.assertIn("Guard ≠ execution engine", text)

    def test_validation_result_contract(self) -> None:
        text = read(RESULT)
        self.assertIn("function accept(", text)
        self.assertIn("function reject(", text)
        self.assertIn("function toArray(", text)
        for field in ("accepted", "ruleId", "reasonCode", "detailsSafe"):
            self.assertIn(f"'{field}'", text)
        self.assertIn("Does not grant permissions", text)

    def test_guard_service_validations(self) -> None:
        text = read(SERVICE)
        self.assertIn("function validate(", text)
        self.assertIn("function validateCapability(", text)
        self.assertIn("function validatePurpose(", text)
        self.assertIn("function validateBindingReference(", text)
        self.assertIn("function validateFoundationState(", text)
        self.assertIn("function validateFailureCode(", text)
        self.assertIn("function validateReservationOwnership(", text)
        self.assertIn("function validatePayloadSafety(", text)
        self.assertIn("COMMERCIAL_BRIEF_FORBIDDEN", text)
        self.assertIn("BINDING_REFERENCE_MISSING", text)
        self.assertIn("SECRET_SHAPED_INPUT", text)
        self.assertIn("INVALID_FOUNDATION_STATE", text)
        self.assertIn("Does not grant permissions", text)
        self.assertIn("Guard ≠ authorization engine", text)

    def test_isolation_no_acl_workflow_connector_http(self) -> None:
        blob = "\n".join(read(path) for path in (RULE, RESULT, SERVICE))
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            self.assertNotIn(marker, blob, msg=f"forbidden marker present: {marker}")

    def test_no_entity_acl_workflow_merge(self) -> None:
        blob = "\n".join(read(path) for path in (RULE, RESULT, SERVICE))
        for marker in (
            "entityDefs",
            "AIJob",
            "EntityManager",
            "Jobs/",
            "PermissionLevel",
        ):
            self.assertNotIn(marker, blob)
        # C25 authority labels appear only on the reject list.
        self.assertIn("'CommercialBrief'", read(SERVICE))
        self.assertIn("'Opportunity'", read(SERVICE))
        self.assertIn("C25_AUTHORITY_FORBIDDEN", read(SERVICE))

    def test_upstream_wp_files_unmodified_coupling(self) -> None:
        for path in (
            FOUNDATION_STATE,
            FAILURE_METADATA,
            RESERVATION_METADATA,
            DISPATCH_SERVICE,
            PROVIDER_BINDING_SERVICE,
        ):
            text = read(path)
            for marker in ("AIGuardRule", "AIGuardValidationResult", "AIGuardService"):
                self.assertNotIn(marker, text)

    def test_completion_capability_portfolio_includes_commercial_brief_identity(self) -> None:
        text = read(COMPLETION_BASE)
        match = re.search(
            r"class CompletionCapability\(Enum\):(.*?)(?:\nclass |\Z)",
            text,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        assert match is not None
        names = set(re.findall(r'^\s+([A-Z_]+) = "', match.group(1), flags=re.M))
        self.assertEqual(names, COMPLETION_PORTFOLIO)
        self.assertIn("COMMERCIAL_BRIEF", names)

    def test_invariant_registry_statuses_unchanged(self) -> None:
        text = read(INVARIANT_REGISTRY)
        self.assertRegex(text, r"\|\s*C20-INV-02\s*\|.*\|\s*ACTIVE\s*\|")
        self.assertRegex(text, r"\|\s*C20-INV-03\s*\|.*\|\s*ACTIVE\s*\|")
        for inv in range(4, 14):
            self.assertRegex(
                text,
                rf"\|\s*C20-INV-{inv:02d}\s*\|.*\|\s*DEFERRED\s*\|",
                msg=f"C20-INV-{inv:02d} must remain DEFERRED",
            )


if __name__ == "__main__":
    unittest.main()
