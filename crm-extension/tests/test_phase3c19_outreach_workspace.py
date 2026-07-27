"""Phase3C19 Outreach Center operational workspace contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


EXTENSION = Path(__file__).resolve().parents[1]
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"
NAVIGATION = (
    EXTENSION.parent / "deployment" / "navigation" / "phase3c17_navigation.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C19OutreachWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.view = (CLIENT / "src" / "views" / "prospecting" / "outreach.js").read_text(
            encoding="utf-8"
        )
        cls.template = (
            CLIENT / "res" / "templates" / "prospecting" / "outreach.tpl"
        ).read_text(encoding="utf-8")
        cls.controller = (
            CLIENT / "src" / "controllers" / "draft-approval.js"
        ).read_text(encoding="utf-8")
        cls.client_defs = load_json(
            MODULE / "Resources" / "metadata" / "clientDefs" / "DraftApproval.json"
        )
        cls.en = load_json(MODULE / "Resources" / "i18n" / "en_US" / "DraftApproval.json")
        cls.zh = load_json(MODULE / "Resources" / "i18n" / "zh_CN" / "DraftApproval.json")
        cls.navigation = load_json(NAVIGATION)

    def test_navbar_entry_remains_draft_approval(self) -> None:
        order = self.navigation["topLevelOrder"]
        self.assertIn("DraftApproval", order)
        self.assertEqual(self.navigation["centers"]["outreach"]["entry"], "DraftApproval")
        self.assertNotIn("SendExecution", order)
        self.assertNotIn("ReplyEvent", order)
        self.assertEqual(
            load_json(MODULE / "Resources" / "i18n" / "zh_CN" / "Global.json")["scopeNames"][
                "DraftApproval"
            ],
            "触达中心",
        )

    def test_draft_approval_index_opens_outreach_workspace(self) -> None:
        self.assertEqual(self.client_defs["controller"], "custom:controllers/draft-approval")
        self.assertIn("controllers/record", self.controller)
        self.assertIn("actionIndex", self.controller)
        self.assertIn("actionList", self.controller)
        self.assertIn("isExplicitNativeListRequest", self.controller)
        self.assertIn("custom:views/prospecting/outreach", self.controller)
        self.assertIn("template: 'custom:prospecting/outreach'", self.view)

    def test_workspace_has_three_sections_and_overview_queue_cards(self) -> None:
        self.assertIn("key: 'overview'", self.view)
        self.assertIn("key: 'execution'", self.view)
        self.assertIn("key: 'replyHandling'", self.view)
        self.assertNotIn("key: 'approval'", self.view)
        self.assertEqual(len(re.findall(r"key: '", self.view)), 3)

        for route in (
            "#DraftApproval/list/primary=c17Pending",
            "#SendExecution/list/primary=c18ReadyToSend",
            "#SendExecution/list/primary=c18FailedSend",
            "#ReplyEvent/list/primary=c19OpenReplies",
            "#SendExecution",
            "#ReplyEvent",
            "#DraftApproval/list",
        ):
            self.assertIn(route, self.view)

        self.assertIn("countRecords", self.view)
        self.assertIn("primaryFilter", self.view)
        self.assertIn("{{href}}", self.template)
        self.assertIn("{{#if count}}{{count}}{{else}}0{{/if}}", self.template)

    def test_workspace_has_no_cross_center_launcher(self) -> None:
        surface = self.view + self.template
        self.assertNotIn("list-group-item", self.template)
        self.assertNotIn("operationalCenters", surface)
        self.assertNotIn("centerLauncher", surface)
        for banned in (
            "#ProspectingSearch",
            "#ProspectingDashboard",
            "#SearchJob",
            "#SearchStrategy",
            "#ProspectPool",
            "#Lead",
            "#Quote",
            "#Approval",
        ):
            self.assertNotIn(banned, surface)

    def test_existing_primary_filters_and_native_lists_remain(self) -> None:
        filter_names = {item["name"] for item in self.client_defs["filterList"]}
        self.assertIn("c17Pending", filter_names)
        send = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SendExecution.json")
        self.assertTrue(
            {"c18ReadyToSend", "c18FailedSend"}.issubset(
                {item["name"] for item in send["filterList"]}
            )
        )
        reply = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "ReplyEvent.json")
        self.assertIn(
            "c19OpenReplies", {item["name"] for item in reply["filterList"]}
        )
        php = (MODULE / "Controllers" / "DraftApproval.php").read_text(encoding="utf-8")
        self.assertIn("class DraftApproval extends Record", php)
        scope = load_json(MODULE / "Resources" / "metadata" / "scopes" / "DraftApproval.json")
        self.assertTrue(scope["entity"])
        self.assertTrue(scope["tab"])
        self.assertTrue(scope["acl"])

    def test_workspace_i18n_parity(self) -> None:
        self.assertEqual(set(self.en["labels"]), set(self.zh["labels"]))
        self.assertEqual(self.en["labels"]["outreachCenter"], "Outreach Center")
        self.assertEqual(self.zh["labels"]["outreachCenter"], "触达中心")
        self.assertEqual(self.zh["labels"]["overview"], "触达概览")
        self.assertEqual(self.zh["labels"]["execution"], "触达执行")
        self.assertEqual(self.zh["labels"]["replyHandling"], "回复处理")
        self.assertEqual(self.zh["labels"]["pendingApproval"], "待审批")
        self.assertEqual(self.zh["labels"]["pendingSend"], "待发送")
        self.assertEqual(self.zh["labels"]["failedSend"], "发送失败")
        self.assertEqual(self.zh["labels"]["openReplies"], "已回复待处理")
        for key in (
            "overview",
            "execution",
            "replyHandling",
            "pendingApproval",
            "pendingSend",
            "failedSend",
            "openReplies",
            "sendExecution",
            "replyEvent",
            "draftApproval",
        ):
            self.assertIn(key, self.en["labels"])
            self.assertIn(f"translate('{key}')", self.view)
        self.assertNotIn("approval", self.en["labels"])
        self.assertIn("'labels', 'DraftApproval'", self.view)


if __name__ == "__main__":
    unittest.main()
