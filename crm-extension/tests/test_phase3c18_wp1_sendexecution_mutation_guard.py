"""Phase3C18 WP1.3 SendExecutionStatusMutationGuard contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "crm-extension" / "files" / "custom" / "Espo"
MODULE = CUSTOM / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs" / "SendExecution.json"
GUARD = CUSTOM / "Custom" / "Hooks" / "SendExecution" / "SendExecutionStatusMutationGuard.php"
TRANSITION = SERVICES / "SendExecutionTransitionService.php"
SAVE_OPTION = SERVICES / "StatusMutationSaveOption.php"
BRIDGE = SERVICES / "SendExecutionBridgeAdapterService.php"
RESULT = SERVICES / "SendExecutionResultAdapterService.php"
AUTHORIZER = SERVICES / "WorkflowAuthorizationService.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C18SendExecutionMutationGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = read(GUARD)
        cls.transition = read(TRANSITION)
        cls.save_option = read(SAVE_OPTION)
        cls.entity_defs = json.loads(read(ENTITY_DEFS))
        cls.bridge = read(BRIDGE)
        cls.result = read(RESULT)
        cls.authorizer = read(AUTHORIZER)

    def test_guard_exists_as_before_save_boundary(self) -> None:
        self.assertIn("namespace Espo\\Custom\\Hooks\\SendExecution;", self.guard)
        self.assertIn("class SendExecutionStatusMutationGuard implements BeforeSave", self.guard)
        self.assertIn("public static int $order = 1000;", self.guard)
        self.assertIn("StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED", self.guard)
        self.assertIn("=== true", self.guard)
        self.assertNotIn("SKIP_HOOKS", self.guard)
        self.assertNotIn("SKIP_ALL", self.guard)
        self.assertNotIn("isAdmin", self.guard)

    def test_status_metadata_is_read_only_without_changing_state_contract(self) -> None:
        status = self.entity_defs["fields"]["status"]
        self.assertTrue(status["readOnly"])
        self.assertEqual(status["default"], "CREATED")
        self.assertEqual(
            status["options"],
            ["CREATED", "READY", "SENT", "FAILED", "CANCELLED"],
        )
        self.assertNotIn("sentAt", self.entity_defs["fields"])

    def test_unauthorized_mutation_rejection(self) -> None:
        self.assertIn(
            "SendExecution status mutation must use SendExecutionTransitionService.",
            self.guard,
        )
        self.assertIn(
            "SendExecution sendRequestId is immutable after create.",
            self.guard,
        )
        self.assertIn(
            "SendExecution sentAt may only be written by SendExecutionTransitionService.",
            self.guard,
        )
        self.assertIn("$entity->isNew()", self.guard)
        self.assertIn("STATUS_CREATED", self.guard)
        self.assertIn("LIFECYCLE_FIELDS", self.guard)
        self.assertIn("'status'", self.guard)
        self.assertIn("'sentAt'", self.guard)
        self.assertIn("isAttributeChanged('sendRequestId')", self.guard)
        self.assertIn("isAttributeChanged($field)", self.guard)

    def test_allowed_transition_service_mutation(self) -> None:
        self.assertIn(
            "StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true",
            self.transition,
        )
        self.assertEqual(
            self.transition.count(
                "StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true"
            ),
            1,
        )
        self.assertIn("SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED", self.save_option)
        self.assertIn("$execution->set('status', $targetStatus);", self.transition)
        self.assertIn("$execution->set('sentAt'", self.transition)

        for adapter_source in (self.bridge, self.result):
            self.assertNotIn("StatusMutationSaveOption", adapter_source)
            self.assertNotIn("'status' => 'SENT'", adapter_source)
            self.assertNotIn("'status' => 'FAILED'", adapter_source)
            self.assertNotIn("set('status'", adapter_source)

    def test_terminal_state_protection(self) -> None:
        self.assertIn("TERMINAL_STATUSES", self.guard)
        self.assertIn("STATUS_SENT", self.guard)
        self.assertIn("STATUS_CANCELLED", self.guard)
        self.assertIn("getFetched('status')", self.guard)
        self.assertIn(
            "SendExecution terminal lifecycle fields are immutable outside SendExecutionTransitionService.",
            self.guard,
        )
        self.assertIn("TERMINAL_EVIDENCE_FIELDS", self.guard)
        self.assertIn("'sentAt'", self.guard)
        self.assertIn("'sendRequestId'", self.guard)

    def test_provider_trace_and_normal_crud_are_not_blocked(self) -> None:
        # Guard only lists lifecycle / evidence fields — not provider trace.
        for field in (
            "providerName",
            "providerMessageId",
            "lastError",
            "failureCategory",
            "retryCount",
        ):
            self.assertNotIn(f"'{field}'", self.guard)

        self.assertIn("Provider-trace fields and ordinary CRUD attributes remain writable.", self.guard)
        # Adapters still supply provider-trace inputs through the transition handoff.
        self.assertIn("'providerName' => 'Brevo'", self.bridge)
        self.assertIn("'providerMessageId'", self.bridge)
        self.assertIn("'failureCategory'", self.bridge)
        self.assertIn("'lastError'", self.bridge)
        self.assertIn("'retryCount'", self.bridge)

    def test_reuses_workflow_authorization_ownership_pattern_without_new_acl(self) -> None:
        self.assertIn("WorkflowAuthorizationService", self.guard)
        self.assertIn("without introducing a second ACL architecture", self.guard)
        # C19 WP2 extends the shared authorizer; the guard itself still does not
        # invent a parallel authorization path.
        self.assertIn("authorizeSendExecutionAction", self.authorizer)
        self.assertIn("sendExecution.retry", self.authorizer)
        self.assertIn("sendExecution.cancel", self.authorizer)
        self.assertNotIn("SendExecutionStatusMutationGuard", self.authorizer)
        self.assertIn("private Acl $acl", self.transition)
        self.assertIn("checkEntityEdit($execution)", self.transition)

    def test_does_not_touch_quote_or_approval_lifecycle(self) -> None:
        self.assertNotIn("QuoteTransitionService", self.guard)
        self.assertNotIn("ApprovalService", self.guard)
        self.assertNotIn("Quote.status", self.guard)
        self.assertNotIn("Approval.status", self.guard)

    def test_only_transition_service_supplies_send_execution_mutation_marker(self) -> None:
        writers: list[Path] = []
        for path in CUSTOM.rglob("*.php"):
            source = read(path)
            if "SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true" in source:
                writers.append(path)
        self.assertEqual(writers, [TRANSITION])

        status_writers: list[Path] = []
        for path in CUSTOM.rglob("*.php"):
            source = read(path)
            if re.search(r"\$execution->set\(\s*['\"]status['\"]", source):
                status_writers.append(path)
        self.assertEqual(status_writers, [TRANSITION])


if __name__ == "__main__":
    unittest.main()
