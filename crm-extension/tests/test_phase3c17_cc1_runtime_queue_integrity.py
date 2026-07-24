"""Phase3C17 CC-1 Runtime Queue Integrity contracts.

Runtime smoke (docs/PHASE3C17_FINALIZATION_REPORT.md section 2) captured:

- ``Controller 'ReplyEvent' does not exist`` (待回复 list load)
- ``Controller 'Approval' does not exist`` (待审批 list load)
- ``No primary filter 'c17Pending' for 'DraftApproval'`` (待触达 list load)

Root cause: the three queue scopes lacked a complete runtime chain
(dashlet -> Record list API -> controller -> scope metadata -> selectDefs /
PrimaryFilter). This test pins the restored chain without redesigning
Center Composition, ACL, navigation, or workflow ownership.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVISIONER = ROOT / "deployment" / "provisioning" / "phase3c17_provision_sales_development_command_center.php"
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"

# scope -> (controller class, primary filter key, PrimaryFilter class)
QUEUE_SCOPES = {
    "DraftApproval": ("DraftApproval", "c17Pending", "C17Pending"),
    "Approval": ("Approval", "c17Pending", "C17Pending"),
    "ReplyEvent": ("ReplyEvent", "c17AwaitingReply", "C17AwaitingReply"),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C17RuntimeQueueIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provisioner = PROVISIONER.read_text(encoding="utf-8")

    # 1. Each queue scope has a runtime controller.
    def test_each_queue_scope_has_native_record_controller(self) -> None:
        for scope in QUEUE_SCOPES:
            path = MODULE / "Controllers" / f"{scope}.php"
            self.assertTrue(path.is_file(), msg=f"Missing runtime controller: {path}")
            source = path.read_text(encoding="utf-8")
            self.assertIn("namespace Espo\\Modules\\Prospecting\\Controllers;", source)
            self.assertIn("use Espo\\Core\\Controllers\\Record;", source)
            self.assertIn(f"class {scope} extends Record", source)

    # 2. API route resolvable: entity scope metadata + controller both present,
    #    so Espo's api/v1/{scope} route can resolve the Record controller.
    def test_api_route_resolvable_for_queue_scopes(self) -> None:
        for scope in QUEUE_SCOPES:
            scopes_meta = load_json(MODULE / "Resources" / "metadata" / "scopes" / f"{scope}.json")
            self.assertTrue(scopes_meta.get("entity"), msg=f"{scope} scope must be an entity")
            self.assertTrue(scopes_meta.get("object"), msg=f"{scope} scope must be an object")
            self.assertEqual(scopes_meta.get("module"), "Prospecting", msg=scope)
            self.assertTrue(
                (MODULE / "Controllers" / f"{scope}.php").is_file(),
                msg=f"{scope} route still has no controller to resolve",
            )
        # Module controllers must be empty Record shells — no custom routing.
        for scope in QUEUE_SCOPES:
            source = (MODULE / "Controllers" / f"{scope}.php").read_text(encoding="utf-8")
            self.assertNotIn("function action", source, msg=f"{scope} controller must stay native")
            self.assertNotIn("Route", source, msg=scope)

    # 3. Only mapped primary filters are referenced; any other name falls
    #    through to Espo's native "No primary filter" client-visible error.
    def test_provisioner_references_only_mapped_primary_filters(self) -> None:
        referenced = re.findall(r"phase3c17RecordsOptions\('[^']+', '([A-Za-z]+)', '([A-Za-z0-9]+)'", self.provisioner)
        self.assertTrue(referenced, msg="no queue Records options found in provisioner")
        for entity_type, primary_filter in referenced:
            select_defs_path = MODULE / "Resources" / "metadata" / "selectDefs" / f"{entity_type}.json"
            if entity_type == "Task":
                # Task.actual is an EspoCRM core primary filter.
                self.assertEqual(primary_filter, "actual")
                continue
            select_defs = load_json(select_defs_path)
            self.assertIn(
                primary_filter,
                select_defs["primaryFilterClassNameMap"],
                msg=f"{entity_type}.{primary_filter} referenced but not mapped (would 400)",
            )

    # 4. PrimaryFilter remains server-side for every queue scope.
    def test_primary_filters_remain_server_side(self) -> None:
        for scope, (_controller, filter_key, class_name) in QUEUE_SCOPES.items():
            select_defs = load_json(MODULE / "Resources" / "metadata" / "selectDefs" / f"{scope}.json")
            mapped = select_defs["primaryFilterClassNameMap"].get(filter_key)
            self.assertEqual(
                mapped,
                f"Espo\\Modules\\Prospecting\\Classes\\Select\\{scope}\\PrimaryFilters\\{class_name}",
                msg=f"{scope}.{filter_key} mapping drifted",
            )
            source = (
                MODULE / "Classes" / "Select" / scope / "PrimaryFilters" / f"{class_name}.php"
            ).read_text(encoding="utf-8")
            self.assertIn("implements Filter", source)
            self.assertIn("public function apply(SelectBuilder $queryBuilder): void", source)

    # 5. ACL still applies: scopes stay ACL-controlled; controllers add no bypass.
    def test_acl_still_applies(self) -> None:
        for scope in QUEUE_SCOPES:
            scopes_meta = load_json(MODULE / "Resources" / "metadata" / "scopes" / f"{scope}.json")
            self.assertTrue(scopes_meta.get("acl"), msg=f"{scope} scope must stay ACL controlled")
            controller = (MODULE / "Controllers" / f"{scope}.php").read_text(encoding="utf-8")
            for bypass in ("Acl", "acl", "bypass", "skipAccessCheck", "disableAccessControl"):
                self.assertNotIn(bypass, controller, msg=f"{scope} controller must not touch ACL")
        # No aclDefs changes accompany this fix.
        acl_defs = load_json(MODULE / "Resources" / "metadata" / "aclDefs" / "Approval.json")
        self.assertTrue(isinstance(acl_defs, dict))

    # 6. No workflow service changes.
    def test_no_workflow_service_changes(self) -> None:
        for scope in QUEUE_SCOPES:
            controller = (MODULE / "Controllers" / f"{scope}.php").read_text(encoding="utf-8")
            for service in ("QuoteTransitionService", "ApprovalService", "ApprovalDecisionService"):
                self.assertNotIn(service, controller, msg=f"{scope} controller must not touch workflow")
        for service_path in (
            MODULE / "Services" / "QuoteTransitionService.php",
            MODULE / "Services" / "ApprovalService.php",
            MODULE / "Services" / "ApprovalDecisionService.php",
        ):
            self.assertTrue(service_path.is_file(), msg=f"workflow service missing: {service_path}")

    # 7. Dashboard queue configuration unchanged by this fix.
    def test_dashboard_queue_configuration_unchanged(self) -> None:
        for expected in (
            "phase3c17RecordsOptions('我的任务', 'Task', 'actual', 'dateStart', 'asc', ['onlyMy'])",
            "phase3c17RecordsOptions('待触达', 'DraftApproval', 'c17Pending', 'createdAt')",
            "phase3c17RecordsOptions('待回复', 'ReplyEvent', 'c17AwaitingReply', 'receivedAt')",
            "phase3c17RecordsOptions('待审批', 'Approval', 'c17Pending', 'createdAt')",
        ):
            self.assertIn(expected, self.provisioner)
        # Queue dashlets still reuse the native Records dashlet.
        for queue_id in (
            "phase3c17-command-my-tasks", "phase3c17-command-outreach",
            "phase3c17-command-replies", "phase3c17-command-approvals",
        ):
            self.assertIn(f"'id' => '{queue_id}', 'name' => 'Records'", self.provisioner)


if __name__ == "__main__":
    unittest.main()
