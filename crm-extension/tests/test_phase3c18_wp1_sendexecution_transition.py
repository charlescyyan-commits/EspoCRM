"""Phase3C18 WP1.1 SendExecutionTransitionService foundation contracts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs" / "SendExecution.json"
TRANSITION = SERVICES / "SendExecutionTransitionService.php"
SAVE_OPTION = SERVICES / "StatusMutationSaveOption.php"
BRIDGE = SERVICES / "SendExecutionBridgeAdapterService.php"
RESULT = SERVICES / "SendExecutionResultAdapterService.php"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C18SendExecutionTransitionServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read(TRANSITION)
        cls.save_option = read(SAVE_OPTION)
        cls.entity_defs = read(ENTITY_DEFS)

    def test_service_exists_with_governance_marker(self) -> None:
        self.assertIn("namespace Espo\\Modules\\Prospecting\\Services;", self.source)
        self.assertIn("class SendExecutionTransitionService", self.source)
        self.assertIn("public const GOVERNANCE_MARKER = 'adr-c18-sendexecution-v1';", self.source)
        self.assertIn("public function validateTransition(string $currentStatus, string $targetStatus): bool", self.source)
        self.assertIn("public function transition(Entity $execution, string $targetStatus, array $options = []): Entity", self.source)
        self.assertIn("public function authorize(Entity $execution, string $action): void", self.source)
        self.assertIn("public function resolveAction(string $currentStatus, string $targetStatus): string", self.source)

    def test_valid_transition_matrix_matches_adr(self) -> None:
        expected_edges = {
            ("STATUS_CREATED", "STATUS_READY"),
            ("STATUS_READY", "STATUS_SENT"),
            ("STATUS_READY", "STATUS_FAILED"),
            ("STATUS_READY", "STATUS_CANCELLED"),
            ("STATUS_FAILED", "STATUS_READY"),
            ("STATUS_FAILED", "STATUS_CANCELLED"),
        }
        for from_status, to_status in expected_edges:
            pattern = rf"self::{from_status}\s*=>\s*\[[^\]]*self::{to_status}"
            self.assertRegex(self.source, pattern, msg=f"Missing transition {from_status} -> {to_status}")

    def test_invalid_transitions_are_not_declared(self) -> None:
        forbidden = [
            ("STATUS_CREATED", "STATUS_SENT"),
            ("STATUS_CREATED", "STATUS_FAILED"),
            ("STATUS_CREATED", "STATUS_CANCELLED"),
            ("STATUS_SENT", "STATUS_READY"),
            ("STATUS_SENT", "STATUS_FAILED"),
            ("STATUS_CANCELLED", "STATUS_READY"),
            ("STATUS_FAILED", "STATUS_SENT"),
            ("STATUS_READY", "STATUS_CREATED"),
        ]
        for from_status, to_status in forbidden:
            # Ensure to_status is not listed under from_status's array entry.
            block = re.search(
                rf"self::{from_status}\s*=>\s*\[(.*?)\]",
                self.source,
                flags=re.S,
            )
            self.assertIsNotNone(block, msg=f"Missing matrix row for {from_status}")
            self.assertNotIn(
                f"self::{to_status}",
                block.group(1),
                msg=f"Forbidden transition present: {from_status} -> {to_status}",
            )

    def test_terminal_states_have_no_outgoing_transitions(self) -> None:
        for terminal in ("STATUS_SENT", "STATUS_CANCELLED"):
            self.assertRegex(
                self.source,
                rf"self::{terminal}\s*=>\s*\[\s*\]",
                msg=f"{terminal} must be terminal",
            )

    def test_authorization_action_keys_match_adr(self) -> None:
        self.assertIn("ACTION_PREPARE = 'sendExecution.prepare'", self.source)
        self.assertIn("ACTION_RECORD_SENT = 'sendExecution.recordSent'", self.source)
        self.assertIn("ACTION_RECORD_FAILED = 'sendExecution.recordFailed'", self.source)
        self.assertIn("ACTION_RETRY = 'sendExecution.retry'", self.source)
        self.assertIn("ACTION_CANCEL = 'sendExecution.cancel'", self.source)
        self.assertIn("TRANSITION_ACTIONS", self.source)
        self.assertIn("self::STATUS_FAILED => [", self.source)
        self.assertIn("self::STATUS_CANCELLED => self::ACTION_CANCEL", self.source)

    def test_transition_persists_status_with_authorized_save_option(self) -> None:
        self.assertIn("$execution->set('status', $targetStatus);", self.source)
        self.assertIn(
            "StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true",
            self.source,
        )
        self.assertIn("SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED", self.save_option)
        self.assertIn("getTransactionManager()->run", self.source)
        self.assertIn("protected function afterTransition(Entity $execution, string $fromStatus, string $toStatus): void", self.source)

    def test_sent_transition_writes_sent_at_audit_field(self) -> None:
        self.assertIn("$targetStatus === self::STATUS_SENT", self.source)
        self.assertIn("$execution->set('sentAt', $now->format('Y-m-d H:i:s'));", self.source)
        # Additive entityDefs for sentAt land with packaging WP; service already owns the write.
        self.assertNotIn('"sentAt"', self.entity_defs)

    def test_retry_respects_max_retries_boundary(self) -> None:
        self.assertIn("private function assertRetryAllowed(Entity $execution): void", self.source)
        self.assertIn("retryCount", self.source)
        self.assertIn("maxRetries", self.source)
        self.assertIn("SendExecution retry limit reached for maxRetries.", self.source)

    def test_acl_authorization_integration_present(self) -> None:
        self.assertIn("private Acl $acl", self.source)
        self.assertIn("private User $user", self.source)
        self.assertIn("checkEntityEdit($execution)", self.source)
        self.assertIn("skipAuthorization", self.source)

    def test_adapters_not_migrated_yet(self) -> None:
        bridge = read(BRIDGE)
        result = read(RESULT)
        self.assertNotIn("SendExecutionTransitionService", bridge)
        self.assertNotIn("SendExecutionTransitionService", result)
        self.assertIn("'status' => 'SENT'", bridge)
        self.assertIn("'status' => 'FAILED'", bridge)
        self.assertIn("'status' => 'SENT'", result)
        self.assertIn("'status' => 'FAILED'", result)

    def test_does_not_touch_quote_or_approval_lifecycle(self) -> None:
        self.assertNotIn("QuoteTransitionService", self.source)
        self.assertNotIn("ApprovalService", self.source)
        self.assertNotIn("Quote.status", self.source)
        self.assertNotIn("Approval.status", self.source)


if __name__ == "__main__":
    unittest.main()
