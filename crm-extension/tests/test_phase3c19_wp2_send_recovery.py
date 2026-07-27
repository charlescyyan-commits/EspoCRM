"""Focused contracts for Phase3C19 WP2 SendExecution recovery entry points."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CUSTOM = EXTENSION / "files" / "custom" / "Espo" / "Custom"
SERVICES = MODULE / "Services"
API = MODULE / "Api"
RESOURCES = MODULE / "Resources"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


class Phase3C19WP2SendRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transition = read(SERVICES / "SendExecutionTransitionService.php")
        cls.workflow = read(SERVICES / "SendExecutionWorkflowActionService.php")
        cls.authorizer = read(SERVICES / "WorkflowAuthorizationService.php")
        cls.api = read(API / "PostSendExecutionWorkflowAction.php")
        cls.guard = read(CUSTOM / "Hooks" / "SendExecution" / "SendExecutionStatusMutationGuard.php")
        cls.handler = read(
            EXTENSION / "files" / "client" / "custom" / "src" / "handlers" / "send-execution" / "workflow-transition.js"
        )
        cls.policy = load_json(RESOURCES / "metadata" / "app" / "prospectingWorkflow.json")
        cls.entity_defs = load_json(RESOURCES / "metadata" / "entityDefs" / "SendExecution.json")
        cls.client_defs = load_json(RESOURCES / "metadata" / "clientDefs" / "SendExecution.json")

    def test_recovery_api_is_thin_and_uses_the_canonical_route(self) -> None:
        routes = load_json(RESOURCES / "routes.json")
        self.assertIn(
            {
                "route": "/Prospecting/send-execution/:id/workflow/:action",
                "method": "post",
                "actionClassName": "Espo\\Modules\\Prospecting\\Api\\PostSendExecutionWorkflowAction",
            },
            routes,
        )
        self.assertIn("class PostSendExecutionWorkflowAction implements Action", self.api)
        self.assertIn("SendExecution workflow route is incomplete.", self.api)
        self.assertIn("$this->service->execute(", self.api)
        self.assertNotIn("saveEntity(", self.api)
        self.assertNotIn("set('status'", self.api)

    def test_command_adapter_delegates_to_authorizer_and_transition_owner(self) -> None:
        self.assertIn("class SendExecutionWorkflowActionService", self.workflow)
        self.assertIn("authorizeSendExecutionAction(", self.workflow)
        self.assertIn("$this->transitionService->transition(", self.workflow)
        self.assertIn("STATUS_READY", self.workflow)
        self.assertIn("STATUS_CANCELLED", self.workflow)
        self.assertIn("workflowAuthorizationChecked", self.workflow)
        self.assertIn("IGNORE_REASON = 'IGNORED'", self.workflow)
        self.assertIn("CANCEL_REASONS", self.workflow)
        self.assertNotIn("set('status'", self.workflow)
        self.assertNotIn("saveEntity(", self.workflow)
        self.assertNotIn("VALID_TRANSITIONS", self.workflow)

    def test_existing_transition_matrix_is_preserved_and_cancel_audit_is_owner_written(self) -> None:
        self.assertIn("public const GOVERNANCE_MARKER = 'adr-c18-sendexecution-v1';", self.transition)
        self.assertIn("public const RECOVERY_GOVERNANCE_MARKER = 'adr-c18-sendexecution-v2';", self.transition)
        self.assertIn("self::STATUS_FAILED => [self::STATUS_READY, self::STATUS_CANCELLED]", self.transition)
        self.assertIn("self::STATUS_SENT => []", self.transition)
        self.assertIn("self::STATUS_CANCELLED => []", self.transition)
        self.assertIn("$execution->set('cancelledAt'", self.transition)
        self.assertIn("$execution->set('cancelledById'", self.transition)
        self.assertIn("$execution->set('cancelReason'", self.transition)
        self.assertIn("normalizeCancelReason", self.transition)
        self.assertNotIn("QuoteTransitionService", self.transition)
        self.assertNotIn("ApprovalService", self.transition)

    def test_cancel_audit_fields_are_metadata_backed_and_guarded(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertTrue(self.entity_defs["audited"])
        self.assertEqual(fields["cancelledAt"]["type"], "datetime")
        self.assertTrue(fields["cancelledAt"]["readOnly"])
        self.assertEqual(fields["cancelledBy"]["type"], "link")
        self.assertTrue(fields["cancelledBy"]["readOnly"])
        self.assertEqual(fields["cancelReason"]["options"], ["IGNORED", "ABANDONED", "DUPLICATE", "OTHER"])
        self.assertTrue(fields["cancelReason"]["readOnly"])
        self.assertEqual(self.entity_defs["links"]["cancelledBy"]["entity"], "User")
        for field in ("cancelledAt", "cancelledById", "cancelReason"):
            self.assertIn(f"'{field}'", self.guard)
        self.assertIn("SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED", self.guard)
        self.assertNotIn("ReplyTriageService", self.guard)

    def test_recovery_authorization_is_read_acl_plus_manager_or_integration_binding(self) -> None:
        self.assertIn("ACTION_SEND_EXECUTION_RETRY = 'sendExecution.retry'", self.authorizer)
        self.assertIn("ACTION_SEND_EXECUTION_CANCEL = 'sendExecution.cancel'", self.authorizer)
        self.assertIn("authorizeSendExecutionAction", self.authorizer)
        self.assertIn("checkEntityRead($execution)", self.authorizer)
        self.assertIn("resolveSendExecutionAction", self.authorizer)
        self.assertNotIn("checkEntityEdit($execution)", self.authorizer)
        self.assertEqual(self.policy["sendExecution"]["marker"], "adr-c18-sendexecution-v1")
        self.assertEqual(self.policy["sendExecution"]["recoveryMarker"], "adr-c18-sendexecution-v2")
        for action in ("sendExecution.retry", "sendExecution.cancel"):
            self.assertEqual(
                self.policy["actionRoleBindings"][action]["roleNames"],
                ["Sales Manager", "Integration Bot"],
            )

    def test_detail_actions_are_failed_only_and_call_the_workflow_api(self) -> None:
        actions = {item["name"]: item for item in self.client_defs["detailActionList"] if isinstance(item, dict)}
        self.assertEqual(set(actions), {"retrySendExecution", "cancelSendExecution", "ignoreSendExecution"})
        for action in actions.values():
            self.assertEqual(action["acl"], "read")
            self.assertEqual(action["handler"], "custom:handlers/send-execution/workflow-transition")
        self.assertIn("this.view.model.get('status') === 'FAILED'", self.handler)
        self.assertIn("retryCount() < this.maxRetries()", self.handler)
        self.assertIn("Prospecting/send-execution/", self.handler)
        self.assertIn("ignoreConfirmation", self.handler)
        self.assertIn("reason: 'IGNORED'", self.handler)
        self.assertNotIn("model.set('status'", self.handler)

    def test_send_execution_i18n_has_en_zh_key_parity(self) -> None:
        en = load_json(RESOURCES / "i18n" / "en_US" / "SendExecution.json")
        zh = load_json(RESOURCES / "i18n" / "zh_CN" / "SendExecution.json")
        for section in ("fields", "links", "labels", "options"):
            self.assertEqual(set(en[section]), set(zh[section]), msg=section)
        self.assertEqual(set(en["options"]["cancelReason"]), set(zh["options"]["cancelReason"]))

    def test_wp2_does_not_modify_navigation_or_reply_or_quote_ownership(self) -> None:
        sources = "\n".join([self.api, self.workflow, self.transition, self.guard, self.handler])
        for forbidden in ("tabList", "phase3c17_navigation", "ReplyTriageService", "QuoteTransitionService", "ApprovalDecisionService"):
            self.assertNotIn(forbidden, sources)


if __name__ == "__main__":
    unittest.main()
