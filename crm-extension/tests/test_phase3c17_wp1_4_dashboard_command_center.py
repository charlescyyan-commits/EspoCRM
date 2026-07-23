"""Presentation-only contracts for the Phase3C17 WP1.4 command center."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVISIONER = ROOT / "deployment" / "provisioning" / "phase3c17_provision_sales_development_command_center.php"
LEGACY_B07 = ROOT / "deployment" / "provisioning" / "phase3b07_provision_operations_dashboards.php"
LEGACY_C01 = ROOT / "deployment" / "provisioning" / "phase3c01_provision_acquisition_workspace.php"
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C17WP14DashboardCommandCenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROVISIONER.read_text(encoding="utf-8")

    def test_one_primary_chinese_command_center_and_compatible_wrappers(self) -> None:
        self.assertIn("const PHASE3C17_COMMAND_CENTER = '销售开发指挥中心';", self.source)
        self.assertIn("Prospecting Operations", self.source)
        self.assertIn("Acquisition", self.source)
        for wrapper in (LEGACY_B07, LEGACY_C01):
            self.assertIn("phase3c17_provision_sales_development_command_center.php", wrapper.read_text(encoding="utf-8"))

    def test_command_center_uses_existing_or_native_dashlets_only(self) -> None:
        for dashlet in (
            "ProspectingSummary", "AcquisitionOverview", "Records", "AcquisitionResearchQueue",
            "AcquisitionLeadPool", "ProspectingRecentDiscovery", "AcquisitionJobsCompleted",
            "RecentResearchEvidence",
        ):
            self.assertIn(f"'name' => '{dashlet}'", self.source)
        self.assertNotIn("metadata/dashlets", self.source)
        self.assertNotIn("new \\Espo\\Modules", self.source)

    def test_daily_queue_filters_use_existing_status_fields_without_services_or_acl_changes(self) -> None:
        self.assertIn("'Task', 'actual', 'dateStart', 'asc', ['onlyMy']", self.source)
        self.assertIn("'DraftApproval', 'c17Pending', 'createdAt'", self.source)
        self.assertIn("'ReplyEvent', 'c17AwaitingReply', 'receivedAt'", self.source)
        self.assertIn("'Approval', 'c17Pending', 'createdAt'", self.source)
        for path, filter_name, field, value in (
            ("DraftApproval.json", "c17Pending", "status", "PENDING"),
            ("ReplyEvent.json", "c17AwaitingReply", "replyStatus", "SENT"),
            ("Approval.json", "c17Pending", "status", "PENDING"),
        ):
            payload = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / path)
            filter_def = payload["filterList"][0]
            self.assertEqual(filter_def["name"], filter_name)
            self.assertEqual(filter_def["where"][0]["attribute"], field)
            self.assertEqual(filter_def["where"][0]["value"], value)
        for forbidden in ("ConfigWriter", "tabList", "ApprovalService", "QuoteTransitionService", "aclDefs"):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
