"""Phase3C19 WP1 Reply Center lifecycle foundation contracts (ADR-C19 / adr-c19-replyevent-v1)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "crm-extension" / "files" / "custom" / "Espo"
MODULE = CUSTOM / "Modules" / "Prospecting"
SERVICES = MODULE / "Services"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs" / "ReplyEvent.json"
POLICY = MODULE / "Resources" / "metadata" / "app" / "prospectingWorkflow.json"
ROUTES = MODULE / "Resources" / "routes.json"
I18N_EN = MODULE / "Resources" / "i18n" / "en_US" / "ReplyEvent.json"
I18N_ZH = MODULE / "Resources" / "i18n" / "zh_CN" / "ReplyEvent.json"
TRIAGE = SERVICES / "ReplyTriageService.php"
SAVE_OPTION = SERVICES / "StatusMutationSaveOption.php"
SYNC = SERVICES / "ReplyEventSyncService.php"
API = MODULE / "Api" / "PostSyncReplyEvent.php"
GUARD = CUSTOM / "Custom" / "Hooks" / "ReplyEvent" / "ReplyEventMutationGuard.php"

GOVERNANCE_MARKER = "adr-c19-replyevent-v1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


class Phase3C19ReplyTriageServiceTests(unittest.TestCase):
    """Lifecycle ownership: ReplyTriageService is the sole triage writer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read(TRIAGE)
        cls.save_option = read(SAVE_OPTION)

    def test_service_exists_with_governance_marker(self) -> None:
        self.assertIn("namespace Espo\\Modules\\Prospecting\\Services;", self.source)
        self.assertIn("class ReplyTriageService", self.source)
        self.assertIn(f"public const GOVERNANCE_MARKER = '{GOVERNANCE_MARKER}';", self.source)
        self.assertIn(
            "public function validateTransition(string $currentStatus, string $targetStatus): bool",
            self.source,
        )
        self.assertIn(
            "public function transition(Entity $replyEvent, string $targetStatus, array $options = []): Entity",
            self.source,
        )
        self.assertIn("public function authorize(Entity $replyEvent, string $action): void", self.source)
        self.assertIn("public function resolveAction(string $currentStatus, string $targetStatus): string", self.source)

    def test_valid_transition_matrix_matches_wp1_scope(self) -> None:
        expected_edges = {
            ("TRIAGE_OPEN", "TRIAGE_IN_PROGRESS"),
            ("TRIAGE_OPEN", "TRIAGE_CLOSED"),
            ("TRIAGE_IN_PROGRESS", "TRIAGE_OPEN"),
            ("TRIAGE_IN_PROGRESS", "TRIAGE_CLOSED"),
        }
        for from_status, to_status in expected_edges:
            pattern = rf"self::{from_status}\s*=>\s*\[[^\]]*self::{to_status}"
            self.assertRegex(self.source, pattern, msg=f"Missing transition {from_status} -> {to_status}")

    def test_invalid_transitions_are_not_declared(self) -> None:
        forbidden = [
            ("TRIAGE_OPEN", "TRIAGE_OPEN"),
            ("TRIAGE_IN_PROGRESS", "TRIAGE_IN_PROGRESS"),
            ("TRIAGE_CLOSED", "TRIAGE_OPEN"),
            ("TRIAGE_CLOSED", "TRIAGE_IN_PROGRESS"),
            ("TRIAGE_CLOSED", "TRIAGE_CLOSED"),
        ]
        for from_status, to_status in forbidden:
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

    def test_closed_is_terminal(self) -> None:
        self.assertRegex(
            self.source,
            r"self::TRIAGE_CLOSED\s*=>\s*\[\s*\]",
            msg="CLOSED must have no outgoing transitions",
        )

    def test_authorization_action_keys(self) -> None:
        self.assertIn("ACTION_START_PROGRESS = 'replyEvent.startProgress'", self.source)
        self.assertIn("ACTION_REOPEN = 'replyEvent.reopen'", self.source)
        self.assertIn("ACTION_CLOSE = 'replyEvent.close'", self.source)
        self.assertIn("TRANSITION_ACTIONS", self.source)
        self.assertIn("self::TRIAGE_IN_PROGRESS => self::ACTION_START_PROGRESS", self.source)
        self.assertIn("self::TRIAGE_CLOSED => self::ACTION_CLOSE", self.source)
        self.assertIn("self::TRIAGE_OPEN => self::ACTION_REOPEN", self.source)

    def test_close_requires_reason(self) -> None:
        self.assertIn("ReplyEvent close requires a closedReason.", self.source)
        self.assertIn("$targetStatus === self::TRIAGE_CLOSED", self.source)
        self.assertIn("$replyEvent->set('closedReason'", self.source)
        self.assertIn("$replyEvent->set('closedAt'", self.source)
        self.assertIn("$replyEvent->set('closedById'", self.source)

    def test_transition_persists_with_authorized_save_option(self) -> None:
        self.assertIn("$replyEvent->set('triageStatus', $targetStatus);", self.source)
        self.assertIn(
            "StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED => true",
            self.source,
        )
        self.assertIn("REPLY_TRIAGE_MUTATION_AUTHORIZED", self.save_option)
        self.assertIn("getTransactionManager()->run", self.source)
        self.assertIn(
            "protected function afterTriage(Entity $replyEvent, string $fromStatus, string $toStatus, string $action, ?string $reason): void",
            self.source,
        )

    def test_acl_authorization_integration_present(self) -> None:
        self.assertIn("private Acl $acl", self.source)
        self.assertIn("private User $user", self.source)
        self.assertIn("checkEntityEdit($replyEvent)", self.source)
        self.assertIn("skipAuthorization", self.source)

    def test_service_does_not_write_provider_facts(self) -> None:
        for field in ("replyStatus", "externalEventId", "receivedAt"):
            self.assertNotIn(f"set('{field}'", self.source)
            self.assertNotIn(f"set(\"{field}\"", self.source)

    def test_does_not_touch_send_execution_quote_or_approval(self) -> None:
        self.assertNotIn("SendExecutionTransitionService", self.source)
        self.assertNotIn("QuoteTransitionService", self.source)
        self.assertNotIn("ApprovalService", self.source)
        self.assertNotIn("SendExecution.status", self.source)
        self.assertNotIn("Quote.status", self.source)
        self.assertNotIn("Approval.status", self.source)

    def test_only_triage_service_and_ingress_supply_mutation_marker(self) -> None:
        writers: list[Path] = []
        for path in CUSTOM.rglob("*.php"):
            if "REPLY_TRIAGE_MUTATION_AUTHORIZED => true" in read(path):
                writers.append(path)
        self.assertEqual(
            sorted(path.relative_to(CUSTOM).as_posix() for path in writers),
            [
                "Modules/Prospecting/Services/ReplyEventSyncService.php",
                "Modules/Prospecting/Services/ReplyTriageService.php",
            ],
        )

        triage_writers: list[Path] = []
        for path in CUSTOM.rglob("*.php"):
            if re.search(r"->set\(\s*['\"]triageStatus['\"]", read(path)):
                triage_writers.append(path)
        self.assertEqual(
            sorted(path.relative_to(CUSTOM).as_posix() for path in triage_writers),
            [
                "Modules/Prospecting/Services/ReplyEventSyncService.php",
                "Modules/Prospecting/Services/ReplyTriageService.php",
            ],
        )


class Phase3C19ReplyEventMutationGuardTests(unittest.TestCase):
    """Mutation guard: provider facts immutable; triage fields owner-gated."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = read(GUARD)

    def test_guard_exists_as_before_save_boundary(self) -> None:
        self.assertIn("namespace Espo\\Custom\\Hooks\\ReplyEvent;", self.guard)
        self.assertIn("class ReplyEventMutationGuard implements BeforeSave", self.guard)
        self.assertIn("public static int $order = 1000;", self.guard)
        self.assertIn("StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED", self.guard)
        self.assertIn("=== true", self.guard)
        self.assertNotIn("SKIP_HOOKS", self.guard)
        self.assertNotIn("SKIP_ALL", self.guard)
        self.assertNotIn("isAdmin", self.guard)

    def test_provider_fact_fields_are_protected(self) -> None:
        self.assertIn("PROVIDER_FACT_FIELDS", self.guard)
        for field in ("replyStatus", "externalEventId", "receivedAt"):
            self.assertIn(f"'{field}'", self.guard)

    def test_unauthorized_provider_fact_write_rejection(self) -> None:
        self.assertIn("$entity->isNew()", self.guard)
        self.assertIn(
            "ReplyEvent provider facts are immutable after create; only sync ingress may write them.",
            self.guard,
        )
        self.assertIn("hasChangedAttributes($entity, self::PROVIDER_FACT_FIELDS)", self.guard)
        self.assertIn("throw new Forbidden(", self.guard)

    def test_triage_fields_require_authorized_save_option(self) -> None:
        self.assertIn("TRIAGE_FIELDS", self.guard)
        for field in ("triageStatus", "closedReason", "closedAt", "closedById"):
            self.assertIn(f"'{field}'", self.guard)
        self.assertIn(
            "ReplyEvent triage fields may only be written by ReplyTriageService.",
            self.guard,
        )

    def test_create_time_triage_initialization_is_ingress_gated(self) -> None:
        self.assertIn(
            "ReplyEvent triage initialization at create requires the authorized sync ingress save option.",
            self.guard,
        )
        self.assertIn(
            "ReplyEvent triage may only initialize to OPEN at create; closed audit fields are transition-owned.",
            self.guard,
        )
        self.assertIn("ReplyTriageService::TRIAGE_OPEN", self.guard)

    def test_guard_does_not_touch_other_lifecycles(self) -> None:
        self.assertNotIn("SendExecutionTransitionService", self.guard)
        self.assertNotIn("QuoteTransitionService", self.guard)
        self.assertNotIn("ApprovalService", self.guard)
        self.assertNotIn("SendExecution.status", self.guard)
        self.assertNotIn("Quote.status", self.guard)
        self.assertNotIn("Approval.status", self.guard)


class Phase3C19PostSyncReplyEventTests(unittest.TestCase):
    """Sync ingress: idempotent create, authorized option, no lifecycle mutation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = read(SYNC)
        cls.api = read(API)
        cls.routes = load_json(ROUTES)

    def test_route_is_registered(self) -> None:
        self.assertIn(
            {
                "route": "/Prospecting/reply-event/sync",
                "method": "post",
                "actionClassName": "Espo\\Modules\\Prospecting\\Api\\PostSyncReplyEvent",
            },
            self.routes,
        )

    def test_api_action_is_a_thin_delegate(self) -> None:
        self.assertIn("namespace Espo\\Modules\\Prospecting\\Api;", self.api)
        self.assertIn("class PostSyncReplyEvent implements Action", self.api)
        self.assertIn("private ReplyEventSyncService $service", self.api)
        self.assertIn("ResponseComposer::json($this->service->sync($request->getParsedBody()))", self.api)

    def test_external_event_id_idempotency(self) -> None:
        self.assertIn("->where(['externalEventId' => $externalEventId])", self.sync)
        self.assertIn("'created' => false", self.sync)
        self.assertIn("'duplicate' => true", self.sync)
        self.assertIn("Reply event external event ID belongs to another Lead.", self.sync)
        # Duplicate branch returns before any save — no second write.
        self.assertLess(self.sync.index("'duplicate' => true"), self.sync.index("saveEntity"))

    def test_create_uses_authorized_save_option(self) -> None:
        self.assertIn(
            "StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED => true",
            self.sync,
        )

    def test_triage_initialization_policy(self) -> None:
        self.assertIn("ACTIONABLE_STATUSES = ['REPLIED', 'BOUNCED', 'UNSUBSCRIBED']", self.sync)
        self.assertIn("$event->set('triageStatus', ReplyTriageService::TRIAGE_OPEN);", self.sync)
        # Exactly one triage write site: create-time initialization only.
        self.assertEqual(self.sync.count("set('triageStatus'"), 1)

    def test_no_direct_lifecycle_mutation_on_existing_records(self) -> None:
        duplicate_branch = self.sync.split("if ($existing) {", 1)[1].split("return [", 1)[0]
        self.assertNotIn("saveEntity", duplicate_branch)
        self.assertNotIn("->set(", duplicate_branch)

    def test_no_lead_or_send_execution_writes_at_ingress(self) -> None:
        self.assertNotIn("$lead->set(", self.sync)
        self.assertNotIn("saveEntity($lead", self.sync)
        self.assertNotIn("$sendExecution->set(", self.sync)
        self.assertNotIn("saveEntity($sendExecution", self.sync)
        self.assertNotIn("set('status'", self.sync)

    def test_provider_status_mapping(self) -> None:
        self.assertIn("'email_replied' => 'REPLIED'", self.sync)
        self.assertIn("'email_bounced' => 'BOUNCED'", self.sync)
        self.assertIn("'email_unsubscribed' => 'UNSUBSCRIBED'", self.sync)
        self.assertIn("'email_sent' => 'SENT'", self.sync)
        self.assertIn("REPLY_STATUSES = ['SENT', 'REPLIED', 'BOUNCED', 'UNSUBSCRIBED']", self.sync)
        self.assertIn("Unsupported reply event reply_status.", self.sync)

    def test_integration_actor_authorization(self) -> None:
        self.assertIn("$this->acl->check($scope, $action)", self.sync)
        self.assertIn("assertScope('ReplyEvent', 'create')", self.sync)
        self.assertIn("checkEntityEdit($lead)", self.sync)
        self.assertIn("checkEntityRead($lead)", self.sync)

    def test_ingress_does_not_use_transition_service(self) -> None:
        # Ingress initializes at create only; transitions stay service-owned.
        self.assertNotIn("->transition(", self.sync)
        self.assertNotIn("resolveAction", self.sync)


class Phase3C19ReplyEventMetadataTests(unittest.TestCase):
    """Additive lifecycle fields, frozen provider fact, policy marker, i18n."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entity_defs = load_json(ENTITY_DEFS)
        cls.policy = load_json(POLICY)
        cls.en = load_json(I18N_EN)
        cls.zh = load_json(I18N_ZH)

    def test_triage_fields_are_additive_and_read_only(self) -> None:
        fields = self.entity_defs["fields"]
        triage = fields["triageStatus"]
        self.assertEqual(triage["type"], "enum")
        self.assertEqual(triage["options"], ["OPEN", "IN_PROGRESS", "CLOSED"])
        self.assertTrue(triage["readOnly"])
        self.assertFalse(triage["notNull"])
        self.assertFalse(triage["required"])
        self.assertEqual(fields["closedReason"]["type"], "text")
        self.assertTrue(fields["closedReason"]["readOnly"])
        self.assertEqual(fields["closedAt"]["type"], "datetime")
        self.assertTrue(fields["closedAt"]["readOnly"])
        self.assertEqual(fields["closedBy"]["type"], "link")
        self.assertTrue(fields["closedBy"]["readOnly"])
        self.assertEqual(self.entity_defs["links"]["closedBy"]["entity"], "User")

    def test_provider_fact_metadata_is_unchanged(self) -> None:
        fields = self.entity_defs["fields"]
        self.assertEqual(
            fields["replyStatus"]["options"],
            ["SENT", "REPLIED", "BOUNCED", "UNSUBSCRIBED"],
        )
        self.assertTrue(fields["replyStatus"]["required"])
        self.assertNotIn("readOnly", fields["replyStatus"])
        self.assertTrue(fields["receivedAt"]["required"])
        self.assertTrue(fields["externalEventId"]["required"])
        self.assertEqual(self.entity_defs["indexes"]["externalEventId"]["type"], "unique")

    def test_policy_references_governance_marker(self) -> None:
        reply_event = self.policy["replyEvent"]
        self.assertEqual(reply_event["marker"], GOVERNANCE_MARKER)
        self.assertEqual(reply_event["lifecycleOwner"], "ReplyTriageService")
        self.assertEqual(
            reply_event["actions"],
            ["replyEvent.startProgress", "replyEvent.reopen", "replyEvent.close"],
        )
        # C18 policy surfaces stay untouched; no reply keys inside quote bindings.
        self.assertEqual(self.policy["governanceMarker"], "adr-c18-sendexecution-v1")
        self.assertEqual(self.policy["sendExecution"]["marker"], "adr-c18-sendexecution-v1")
        for key in self.policy["actionRoleBindings"]:
            self.assertFalse(key.startswith("replyEvent."), msg=f"Unexpected reply binding {key}")

    def test_i18n_labels_for_triage_fields(self) -> None:
        for field in ("triageStatus", "closedReason", "closedAt", "closedBy"):
            self.assertIn(field, self.en["fields"])
            self.assertIn(field, self.zh["fields"])
        self.assertEqual(
            self.en["options"]["triageStatus"],
            {"OPEN": "Open", "IN_PROGRESS": "In Progress", "CLOSED": "Closed"},
        )
        self.assertEqual(
            self.zh["options"]["triageStatus"],
            {"OPEN": "待处理", "IN_PROGRESS": "处理中", "CLOSED": "已关闭"},
        )
        # Provider fact labels untouched.
        self.assertEqual(
            self.en["options"]["replyStatus"],
            {"SENT": "Sent", "REPLIED": "Replied", "BOUNCED": "Bounced", "UNSUBSCRIBED": "Unsubscribed"},
        )


if __name__ == "__main__":
    unittest.main()
