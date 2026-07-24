"""Phase3C17 CC-1 Center Composition contracts.

The Sales Development Command Center is a dashboard composition layer only:
no new scopes, no workflow mutation, no ACL changes, no navigation changes.
These tests pin the composition structure, queue wiring, i18n coverage, and
personal-dashboard preservation of the CC-0B hardened provisioner.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVISIONER = ROOT / "deployment" / "provisioning" / "phase3c17_provision_sales_development_command_center.php"
EXTENSION = ROOT / "crm-extension"
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"

COMMAND_CENTER_ITEMS = (
    "phase3c17-command-summary",
    "phase3c17-command-overview",
    "phase3c17-command-my-tasks",
    "phase3c17-command-research",
    "phase3c17-command-outreach",
    "phase3c17-command-replies",
    "phase3c17-command-approvals",
    "phase3c17-command-pool",
    "phase3c17-command-recent-discovery",
    "phase3c17-command-completed",
    "phase3c17-command-evidence",
)

CUSTOM_DASHLETS = (
    "ProspectingSummary",
    "AcquisitionOverview",
    "AcquisitionResearchQueue",
    "AcquisitionLeadPool",
    "ProspectingRecentDiscovery",
    "AcquisitionJobsCompleted",
    "RecentResearchEvidence",
)

# Module scopes referenced by the four center entry cards. Lead/Quote/
# ProformaInvoice/Task are EspoCRM core scopes (not vendored in this repo).
MODULE_CENTER_SCOPES = (
    "SearchStrategy", "SearchJob", "ProspectPool",
    "ResearchEvidence", "SalesFeedback", "LearningSignal",
    "DraftApproval", "SendExecution", "ReplyEvent", "EmailEvent", "Approval",
)
CORE_CENTER_SCOPES = ("Lead", "Quote", "ProformaInvoice", "Task")

SUMMARY_LABEL_KEYS = (
    "totalProspects", "newThisWeek", "needResearch", "researchCompleted",
    "highPriority", "loading", "noData", "noActivity",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C17CC1CenterCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provisioner = PROVISIONER.read_text(encoding="utf-8")

    # 1. Command Center dashboard structure exists.
    def test_command_center_structure_exists(self) -> None:
        self.assertIn("const PHASE3C17_COMMAND_CENTER = '销售开发指挥中心';", self.provisioner)
        for item_id in COMMAND_CENTER_ITEMS:
            self.assertIn(f"'id' => '{item_id}'", self.provisioner)
        for section in ("// TOP:", "// MIDDLE:", "// BOTTOM:"):
            self.assertIn(section, self.provisioner)
        # Top summary cards are content-titled, not center-titled.
        self.assertIn("'title' => '潜客概览'", self.provisioner)
        self.assertIn("'title' => '获客概览'", self.provisioner)
        self.assertNotIn("'title' => '潜客运营'", self.provisioner)
        self.assertNotIn("'title' => '搜索中心'", self.provisioner)
        # Bottom stays operational counters only — no funnel/rate analytics.
        for banned in ("conversion", "replyRate", "funnel", "ROI", "转化率", "回复率", "漏斗"):
            self.assertNotIn(banned, self.provisioner)

    # 2. Required dashlets exist.
    def test_required_dashlets_exist(self) -> None:
        for dashlet in CUSTOM_DASHLETS:
            meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / f"{dashlet}.json")
            self.assertIn("view", meta, msg=dashlet)
            self.assertTrue(meta.get("aclScope"), msg=f"{dashlet} must be ACL scoped")
        summary_meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingSummary.json")
        self.assertEqual(summary_meta["view"], "custom:views/dashlets/prospecting-summary")
        self.assertTrue((CLIENT / "src" / "views" / "dashlets" / "prospecting-summary.js").is_file())
        self.assertTrue((CLIENT / "res" / "templates" / "dashlets" / "prospecting-summary.tpl").is_file())
        for dashlet in CUSTOM_DASHLETS:
            if dashlet == "ProspectingSummary":
                continue
            meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / f"{dashlet}.json")
            self.assertEqual(meta["view"], "views/dashlets/abstract/record-list", msg=dashlet)
        # Queue dashlets reuse the native Records dashlet; no custom queue view.
        for queue_id in (
            "phase3c17-command-my-tasks", "phase3c17-command-outreach",
            "phase3c17-command-replies", "phase3c17-command-approvals",
        ):
            self.assertIn(f"'id' => '{queue_id}', 'name' => 'Records'", self.provisioner)

    # 3. No duplicate managed tabs.
    def test_no_duplicate_managed_tabs(self) -> None:
        for legacy in ("Prospecting Operations", "Acquisition", "Prospecting Home", "销售开发指挥中心"):
            self.assertIn(f"'{legacy}'", self.provisioner)
        self.assertIn("array_merge([$commandCenterTab], $preservedTabs)", self.provisioner)
        self.assertIn("/^(phase3(?:u03|b07|c0[12]|c17)-)/", self.provisioner)
        # Carried personal items are shifted below the managed grid, not duplicated.
        self.assertIn("max(14, (int) ($item['y'] ?? 0) + 14)", self.provisioner)

    # 4. Queue dashlets reference correct entities.
    def test_queue_dashlets_reference_correct_entities(self) -> None:
        self.assertIn(
            "phase3c17RecordsOptions('我的任务', 'Task', 'actual', 'dateStart', 'asc', ['onlyMy'])",
            self.provisioner,
        )
        self.assertIn("phase3c17RecordsOptions('待触达', 'DraftApproval', 'c17Pending', 'createdAt')", self.provisioner)
        self.assertIn("phase3c17RecordsOptions('待回复', 'ReplyEvent', 'c17AwaitingReply', 'receivedAt')", self.provisioner)
        self.assertIn("phase3c17RecordsOptions('待审批', 'Approval', 'c17Pending', 'createdAt')", self.provisioner)
        research_meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / "AcquisitionResearchQueue.json")
        self.assertEqual(research_meta["entityType"], "ProspectPool")
        self.assertEqual(research_meta["options"]["defaults"]["searchData"], {"primary": "researchQueue"})
        pool_filters = load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "ProspectPool.json")
        self.assertIn("researchQueue", pool_filters["primaryFilterClassNameMap"])
        # CC-0A server-side primary filters back the three queue Records dashlets.
        for entity, key in (("DraftApproval", "c17Pending"), ("ReplyEvent", "c17AwaitingReply"), ("Approval", "c17Pending")):
            select_defs = load_json(MODULE / "Resources" / "metadata" / "selectDefs" / f"{entity}.json")
            self.assertIn(key, select_defs["primaryFilterClassNameMap"], msg=entity)

    # 5. No workflow mutation code.
    def test_no_workflow_mutation_code(self) -> None:
        for banned in (
            "ApprovalService", "QuoteTransitionService", "ApprovalDecisionService",
            "aclDefs", "tabList", "navigation.json", "ConfigWriter",
        ):
            self.assertNotIn(banned, self.provisioner)
        for view_path in (
            CLIENT / "src" / "views" / "dashlets" / "prospecting-summary.js",
            CLIENT / "src" / "views" / "prospecting" / "dashboard.js",
        ):
            source = view_path.read_text(encoding="utf-8")
            self.assertNotIn(".save(", source, msg=view_path.name)
            self.assertNotIn("model.set('status'", source, msg=view_path.name)
            self.assertNotIn('model.set("status"', source, msg=view_path.name)
        # Queues are read-only: no workflow action buttons in dashlet templates.
        summary_tpl = (CLIENT / "res" / "templates" / "dashlets" / "prospecting-summary.tpl").read_text(encoding="utf-8")
        self.assertNotIn("data-action", summary_tpl)
        # CC-1 creates no new business center scopes/entities.
        for banned_scope in ("BusinessCenter", "SalesCenter", "WorkflowCenter", "ApprovalCenter", "QuoteCenter"):
            self.assertFalse(
                (MODULE / "Resources" / "metadata" / "entityDefs" / f"{banned_scope}.json").exists(),
                msg=banned_scope,
            )
            self.assertNotIn(banned_scope, self.provisioner)

    # 6. i18n keys exist in zh/en.
    def test_i18n_keys_exist_in_zh_and_en(self) -> None:
        en_dashboard = load_json(MODULE / "Resources" / "i18n" / "en_US" / "ProspectingDashboard.json")["labels"]
        zh_dashboard = load_json(MODULE / "Resources" / "i18n" / "zh_CN" / "ProspectingDashboard.json")["labels"]
        self.assertEqual(set(en_dashboard), set(zh_dashboard))
        for key in SUMMARY_LABEL_KEYS:
            self.assertIn(key, en_dashboard, msg=f"en_US missing {key}")
            self.assertIn(key, zh_dashboard, msg=f"zh_CN missing {key}")

        en_global = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")
        zh_global = load_json(MODULE / "Resources" / "i18n" / "zh_CN" / "Global.json")
        for dashlet in CUSTOM_DASHLETS:
            self.assertIn(dashlet, en_global["dashlets"], msg=f"en_US dashlet {dashlet}")
            self.assertIn(dashlet, zh_global["dashlets"], msg=f"zh_CN dashlet {dashlet}")
        self.assertEqual(zh_global["dashlets"]["ProspectingSummary"], "潜客概览")
        self.assertEqual(zh_global["dashlets"]["AcquisitionOverview"], "获客概览")

        en_c17 = {k for k in en_global["labels"] if k.startswith("C17Dashboard")}
        zh_c17 = {k for k in zh_global["labels"] if k.startswith("C17Dashboard")}
        self.assertEqual(en_c17, zh_c17)
        for center in ("SearchCenter", "ResearchCenter", "OutreachCenter", "QuoteCenter"):
            self.assertIn(f"C17Dashboard{center}", en_c17)
        self.assertEqual(zh_global["labels"]["C17DashboardSearchCenter"], "搜索中心")
        self.assertEqual(zh_global["labels"]["C17DashboardResearchCenter"], "情报中心")
        self.assertEqual(zh_global["labels"]["C17DashboardOutreachCenter"], "触达中心")
        self.assertEqual(zh_global["labels"]["C17DashboardQuoteCenter"], "报价中心")

        # No hardcoded Chinese/English UI copy in the summary dashlet assets.
        view = (CLIENT / "src" / "views" / "dashlets" / "prospecting-summary.js").read_text(encoding="utf-8")
        for hardcoded in ("'Total Prospects'", "'New This Week'", "'Need Research'", "'Research Completed'", "'High Priority'"):
            self.assertNotIn(hardcoded, view)
        template = (CLIENT / "res" / "templates" / "dashlets" / "prospecting-summary.tpl").read_text(encoding="utf-8")
        for hardcoded in ("Loading...", "No data available", "No prospecting activity yet"):
            self.assertNotIn(hardcoded, template)
        for i18n_binding in ("labels.loading", "labels.noData", "labels.noActivity"):
            self.assertIn(i18n_binding, template)

    # 7. Existing user dashboard preservation.
    def test_existing_user_dashboard_preservation(self) -> None:
        # Non-legacy personal tabs (e.g. My Espo) pass through untouched.
        self.assertIn("in_array($tab['name'] ?? null, PHASE3C17_LEGACY_TABS, true)", self.provisioner)
        self.assertIn("$preservedTabs[] = $tab;", self.provisioner)
        # Non-managed dashlets on legacy tabs are carried over with a y-offset.
        self.assertIn("$carriedItems[] = $item;", self.provisioner)
        # dashletsOptions only unsets phase-managed ids; personal options survive.
        options_body = self.provisioner.split("function phase3c17BuildDashletsOptions", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("phase3c17IsManagedDashletId", options_body)
        self.assertNotIn("$options = [];", options_body)

    # Spec section 2: center entry cards route to existing scopes/pages only.
    def test_center_entry_cards_route_to_existing_scopes(self) -> None:
        dashboard_js = (CLIENT / "src" / "views" / "prospecting" / "dashboard.js").read_text(encoding="utf-8")
        hrefs = set(re.findall(r"href: '#([A-Za-z]+)'", dashboard_js))
        for scope in MODULE_CENTER_SCOPES:
            self.assertTrue(
                (MODULE / "Resources" / "metadata" / "entityDefs" / f"{scope}.json").is_file(),
                msg=f"center card targets missing module scope: {scope}",
            )
        for scope in hrefs - {"ProspectingSearch"}:
            self.assertIn(scope, MODULE_CENTER_SCOPES + CORE_CENTER_SCOPES, msg=f"unknown center route: #{scope}")
        self.assertIn("ProspectingSearch", hrefs)
        self.assertTrue((CLIENT / "src" / "views" / "prospecting" / "search.js").is_file())
        self.assertTrue((CLIENT / "res" / "templates" / "prospecting" / "search.tpl").is_file())
        # Card entries remain ACL-checked.
        self.assertIn("acl.check(entry.scope, 'read')", dashboard_js)


if __name__ == "__main__":
    unittest.main()
