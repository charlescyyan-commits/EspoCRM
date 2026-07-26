"""Phase3C18 WP2.2 SendExecution operational queue surface contracts.

Queues are composition-only: native Records dashlets / dashboard links consume
existing PrimaryFilters. No lifecycle mutation, navigation tabs, or ACL redesign.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVISIONER = ROOT / "deployment" / "provisioning" / "phase3c17_provision_sales_development_command_center.php"
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = ROOT / "crm-extension" / "files" / "client" / "custom"
DASHBOARD_JS = CLIENT / "src" / "views" / "prospecting" / "dashboard.js"
TRANSITION = MODULE / "Services" / "SendExecutionTransitionService.php"
SELECT_DEFS = MODULE / "Resources" / "metadata" / "selectDefs" / "SendExecution.json"
SCOPES = MODULE / "Resources" / "metadata" / "scopes" / "SendExecution.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C18SendExecutionQueueSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provisioner = read(PROVISIONER)
        cls.dashboard = read(DASHBOARD_JS)
        cls.select_defs = load_json(SELECT_DEFS)

    def test_dashlet_binds_pending_send_to_ready_primary_filter(self) -> None:
        self.assertIn(
            "phase3c17RecordsOptions('待发送', 'SendExecution', 'c18ReadyToSend', 'createdAt')",
            self.provisioner,
        )
        self.assertIn(
            "'id' => 'phase3c18-command-pending-send', 'name' => 'Records'",
            self.provisioner,
        )
        self.assertIn("c18ReadyToSend", self.select_defs["primaryFilterClassNameMap"])
        self.assertIn("/^(phase3(?:u03|b07|c0[12]|c17|c18)-)/", self.provisioner)

    def test_outreach_center_exposes_pending_and_failed_send_queues(self) -> None:
        self.assertIn("C18DashboardPendingSend", self.dashboard)
        self.assertIn("C18DashboardFailedSend", self.dashboard)
        self.assertIn(
            "href: '#SendExecution/list/primary=c18ReadyToSend'",
            self.dashboard,
        )
        self.assertIn(
            "href: '#SendExecution/list/primary=c18FailedSend'",
            self.dashboard,
        )
        self.assertIn("c18FailedSend", self.select_defs["primaryFilterClassNameMap"])

        en = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")["labels"]
        zh = load_json(MODULE / "Resources" / "i18n" / "zh_CN" / "Global.json")["labels"]
        self.assertEqual(en["C18DashboardPendingSend"], "Pending Send")
        self.assertEqual(en["C18DashboardFailedSend"], "Failed Send")
        self.assertEqual(zh["C18DashboardPendingSend"], "待发送")
        self.assertEqual(zh["C18DashboardFailedSend"], "发送失败")

    def test_acl_visibility_preserved_for_queue_surfaces(self) -> None:
        scopes = load_json(SCOPES)
        self.assertTrue(scopes.get("acl"))
        # Outreach center entries remain ACL-gated by scope.
        self.assertIn("acl.check(entry.scope, 'read')", self.dashboard)
        self.assertIn("scope: 'SendExecution'", self.dashboard)
        # Command Center pending-send is a native Records dashlet (ACL via entityType).
        self.assertNotIn("skipAccessCheck", self.provisioner)
        self.assertNotIn("disableAccessControl", self.provisioner)

    def test_no_lifecycle_mutation_on_queue_surfaces(self) -> None:
        dashboard_l = self.dashboard.lower()
        provisioner_l = self.provisioner.lower()
        for banned in (
            "sendexecutiontransitionservice",
            "statusmutationsaveoption",
            "model.set('status'",
            'model.set("status"',
            ".save(",
            "recordsent",
            "recordfailed",
            "applyprovideroutcome",
        ):
            self.assertNotIn(banned, dashboard_l, msg=banned)
            self.assertNotIn(banned, provisioner_l, msg=banned)
        # No operator retry/cancel action wiring on composition surfaces.
        self.assertNotIn("data-action=\"retry\"", dashboard_l)
        self.assertNotIn("data-action=\"cancel\"", dashboard_l)
        self.assertNotIn("sendexecution.retry", provisioner_l)
        self.assertNotIn("sendexecution.cancel", provisioner_l)
        # Ownership core remains the sole status writer.
        transition = read(TRANSITION)
        self.assertIn("public const GOVERNANCE_MARKER = 'adr-c18-sendexecution-v1';", transition)
        self.assertIn("$execution->set('status', $targetStatus);", transition)

    def test_forbidden_surfaces_not_introduced(self) -> None:
        for banned in ("tabList", "navigation.json", "ConfigWriter", "aclDefs"):
            self.assertNotIn(banned, self.provisioner)
        # No Failed Send daily queue on Command Center (Outreach Center only).
        self.assertNotIn("c18FailedSend", self.provisioner)
        self.assertNotIn("发送失败", self.provisioner)
        # No new center/scope invented by this WP.
        for banned_scope in ("BusinessCenter", "SendCenter", "OutreachQueue"):
            self.assertFalse(
                (MODULE / "Resources" / "metadata" / "entityDefs" / f"{banned_scope}.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
