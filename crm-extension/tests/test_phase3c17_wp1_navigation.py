"""Focused contracts for Phase3C17 WP1 Operational Centers navigation."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
RESOURCES = MODULE / "Resources"
CLIENT = EXTENSION / "files" / "client" / "custom"
DESIRED_PATH = ROOT / "deployment" / "navigation" / "phase3c17_navigation.json"
MATERIALIZER = (
    ROOT
    / "deployment"
    / "provisioning"
    / "phase3c17_provision_operational_centers_navigation.php"
)
LEGACY_U04 = (
    ROOT
    / "deployment"
    / "provisioning"
    / "phase3u04_provision_navbar_tab_order.php"
)
ADR = ROOT / "docs" / "architecture" / "ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize(existing: list[object], desired: dict) -> list[object]:
    managed = set(desired["managedTopLevelEntries"])
    legacy_dividers = set(desired["legacyDividerIds"])
    legacy_texts = set(desired["legacyDividerTexts"])
    preserved: list[object] = []
    for item in existing:
        if isinstance(item, str) and item in managed:
            continue
        if item == "_delimiter_":
            continue
        if isinstance(item, dict) and (
            item.get("id") in legacy_dividers
            or item.get("text") in legacy_texts
            or item.get("text") is None
        ):
            continue
        preserved.append(item)
    compacted: list[object] = []
    pending: object | None = None
    for item in preserved:
        if isinstance(item, dict) and item.get("type") == "divider":
            pending = item
            continue
        if pending is not None:
            compacted.append(pending)
            pending = None
        compacted.append(item)
    return [item for item in desired["topLevelOrder"] if item != "Home"] + compacted


class Phase3C17WP1NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.desired = load_json(DESIRED_PATH)
        cls.materializer = MATERIALIZER.read_text(encoding="utf-8")
        cls.dashboard_template = (
            CLIENT / "res" / "templates" / "prospecting" / "dashboard.tpl"
        ).read_text(encoding="utf-8")
        cls.dashboard_js = (
            CLIENT / "src" / "views" / "prospecting" / "dashboard.js"
        ).read_text(encoding="utf-8")

    def test_accepted_adr_and_one_declarative_navigation_authority_exist(self) -> None:
        self.assertEqual(self.desired["schemaVersion"], 1)
        self.assertEqual(
            self.desired["navigationVersion"],
            "phase3c17-wp1-4-product-polish-v1",
        )
        adr = ADR.read_text(encoding="utf-8")
        self.assertIn("## Status\n\n**Accepted**", adr)
        self.assertIn("deployment/navigation/phase3c17_navigation.json", adr)

    def test_only_c17_materializer_writes_global_tab_list(self) -> None:
        writers = []
        for path in (ROOT / "deployment" / "provisioning").glob("*.php"):
            source = path.read_text(encoding="utf-8")
            if "->set('tabList'" in source or '->set("tabList"' in source:
                writers.append(path.name)
        self.assertEqual(
            writers,
            ["phase3c17_provision_operational_centers_navigation.php"],
        )
        self.assertIn("phase3c17LoadJson", self.materializer)
        self.assertNotIn("$prospectingNavigationGroup", self.materializer)

    def test_legacy_u04_delegates_and_cannot_overwrite_c17(self) -> None:
        legacy = LEGACY_U04.read_text(encoding="utf-8")
        self.assertIn("DEPRECATED", legacy)
        self.assertIn(
            "phase3c17_provision_operational_centers_navigation.php",
            legacy,
        )
        self.assertNotIn("ConfigWriter", legacy)
        self.assertNotIn("->set('tabList'", legacy)
        for stale_entry in ("SearchJob", "ProspectPool", "ResearchEvidence"):
            self.assertNotIn(f"'{stale_entry}'", legacy)

    def test_materialization_is_idempotent(self) -> None:
        initial = [
            "Lead",
            {"type": "divider", "text": "Prospecting", "id": "phase3u04-prospecting"},
            "ProspectingSearch",
            "SearchJob",
            "ResearchEvidence",
        ]
        once = materialize(initial, self.desired)
        twice = materialize(once, self.desired)
        self.assertEqual(once, twice)

    def test_unrelated_tabs_and_single_global_lead_are_preserved(self) -> None:
        initial = ["Home", "Account", "Lead", "Opportunity", "SearchJob"]
        result = materialize(initial, self.desired)
        for entry in ("Account", "Lead", "Opportunity"):
            self.assertIn(entry, result)
        self.assertEqual(result.count("Lead"), 1)
        self.assertIn("requiredPreservedGlobalEntries", self.materializer)

    def test_required_physical_center_entries_are_exact(self) -> None:
        self.assertEqual(
            self.desired["prospectingEntries"],
            [
                "ProspectingDashboard",
                "ProspectingSearch",
                "DraftApproval",
                "Quote",
            ],
        )
        self.assertEqual(
            self.desired["centers"]["research"]["placement"],
            "global-native-preserved",
        )
        self.assertEqual(self.desired["centers"]["research"]["entry"], "Lead")

    def test_product_polish_physical_order_is_chinese_first_and_lead_is_unique(self) -> None:
        order = self.desired["topLevelOrder"]
        self.assertEqual(order[0], "Home")
        self.assertEqual(
            order[1:],
            [
                {"type": "divider", "text": "潜客开发", "id": "phase3c17-prospecting"},
                "ProspectingDashboard", "ProspectingSearch", "DraftApproval", "Quote",
                {"type": "divider", "text": "客户管理", "id": "phase3c17-customer-management"},
                "Account", "Contact", "Lead", "Opportunity",
                {"type": "divider", "text": "活动", "id": "phase3c17-activities"},
                "Email",
                {"type": "divider", "text": "更多", "id": "phase3c17-more"},
                "Task", "Calendar", "KnowledgeBaseArticle",
            ],
        )
        self.assertEqual(order.count("Lead"), 1)

    def test_supporting_objects_are_not_top_level_prospecting_entries(self) -> None:
        hidden = {
            "SearchStrategy",
            "SearchJob",
            "ProspectPool",
            "ResearchEvidence",
            "SendExecution",
            "ReplyEvent",
            "EmailEvent",
            "SalesFeedback",
            "LearningSignal",
            "Approval",
            "ProformaInvoice",
            "QuoteItem",
        }
        self.assertTrue(hidden.isdisjoint(self.desired["prospectingEntries"]))
        self.assertTrue(hidden.issubset(self.desired["managedProspectingEntries"]))

    def test_search_center_retains_direct_operational_access(self) -> None:
        search = (
            CLIENT / "res" / "templates" / "prospecting" / "search.tpl"
        ).read_text(encoding="utf-8")
        for route in ("#SearchStrategy", "#SearchJob", "#ProspectPool"):
            self.assertIn(route, search)

    def test_dashboard_retains_every_required_supporting_access_path(self) -> None:
        for route in (
            "#Lead",
            "#ResearchEvidence",
            "#SalesFeedback",
            "#LearningSignal",
            "#DraftApproval",
            "#SendExecution",
            "#ReplyEvent",
            "#EmailEvent",
            "#Quote",
            "#Approval",
            "#ProformaInvoice",
        ):
            self.assertIn(route, self.dashboard_js + self.dashboard_template)
        self.assertNotIn("#QuoteItem", self.dashboard_js + self.dashboard_template)

    def test_existing_lead_and_quote_relationship_panels_preserve_child_access(self) -> None:
        lead = load_json(RESOURCES / "metadata" / "clientDefs" / "Lead.json")
        lead_panels = {item["name"] for item in lead["bottomPanels"]["detail"][1:]}
        self.assertTrue(
            {"researchEvidences", "emailEvents", "salesFeedbacks", "learningSignals"}
            .issubset(lead_panels)
        )
        quote = load_json(RESOURCES / "metadata" / "clientDefs" / "Quote.json")
        self.assertEqual(quote["controller"], "controllers/record")
        quote_defs = load_json(RESOURCES / "metadata" / "entityDefs" / "Quote.json")
        self.assertTrue(
            {"quoteItems", "approvals", "proformaInvoices"}
            .issubset(quote_defs["links"])
        )

    def test_existing_non_tab_scope_contracts_remain_frozen(self) -> None:
        for scope_name in ("QuoteItem", "EmailEvent", "SalesFeedback", "LearningSignal"):
            scope = load_json(RESOURCES / "metadata" / "scopes" / f"{scope_name}.json")
            self.assertFalse(scope["tab"], msg=scope_name)

    def test_quote_and_approval_status_fields_remain_read_only(self) -> None:
        for entity_name in ("Quote", "Approval"):
            fields = load_json(
                RESOURCES / "metadata" / "entityDefs" / f"{entity_name}.json"
            )["fields"]
            self.assertTrue(fields["status"]["readOnly"], msg=entity_name)

    def test_navigation_introduces_no_direct_status_mutation(self) -> None:
        navigation_sources = "\n".join(
            [
                self.materializer,
                self.dashboard_js,
                self.dashboard_template,
                (
                    CLIENT / "res" / "templates" / "prospecting" / "search.tpl"
                ).read_text(encoding="utf-8"),
            ]
        )
        for forbidden in (
            "model.set('status'",
            'model.set("status"',
            "->set('status'",
            '->set("status"',
            'data-name="status"',
        ):
            self.assertNotIn(forbidden, navigation_sources)

    def test_draft_and_quote_approval_labels_are_distinct(self) -> None:
        global_en = load_json(RESOURCES / "i18n" / "en_US" / "Global.json")
        draft_en = load_json(RESOURCES / "i18n" / "en_US" / "DraftApproval.json")
        approval_en = load_json(RESOURCES / "i18n" / "en_US" / "Approval.json")
        self.assertEqual(global_en["scopeNames"]["DraftApproval"], "Outreach Center")
        self.assertEqual(global_en["scopeNames"]["Approval"], "Quote Approval")
        self.assertEqual(draft_en["labels"]["DraftApprovals"], "Draft Approvals")
        self.assertEqual(approval_en["labels"]["Approvals"], "Quote Approvals")

    def test_global_i18n_has_en_zh_key_parity_and_c17_product_names(self) -> None:
        global_en = load_json(RESOURCES / "i18n" / "en_US" / "Global.json")
        global_zh = load_json(RESOURCES / "i18n" / "zh_CN" / "Global.json")
        for section in ("scopeNames", "scopeNamesPlural", "scopeNamesSingular", "dashlets", "labels"):
            self.assertEqual(set(global_en[section]), set(global_zh[section]), msg=section)
        self.assertEqual(global_zh["scopeNames"]["ProspectingDashboard"], "潜客运营")
        self.assertEqual(global_zh["scopeNamesSingular"], {
            "DraftApproval": "触达审批", "Quote": "报价", "Approval": "报价审批",
        })
        self.assertEqual(global_zh["scopeNames"]["SendExecution"], "发送执行")
        self.assertEqual(global_zh["scopeNames"]["ReplyEvent"], "客户回复")
        self.assertEqual(global_zh["scopeNames"]["EmailEvent"], "邮件事件")
        self.assertEqual(global_zh["scopeNames"]["SalesFeedback"], "销售反馈")
        self.assertEqual(global_zh["scopeNames"]["LearningSignal"], "学习信号")

    def test_dashboard_center_labels_are_i18n_backed(self) -> None:
        self.assertIn("getLanguage().translate(key, 'labels', 'Global')", self.dashboard_js)
        for literal in (
            "name: 'Search Center'",
            "name: 'Research Center'",
            "name: 'Outreach Center'",
            "name: 'Quote Center'",
        ):
            self.assertNotIn(literal, self.dashboard_js)

    def test_canonical_metadata_tree_remains_singular(self) -> None:
        authoritative = (
            EXTENSION
            / "files"
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Resources"
        )
        self.assertTrue(authoritative.is_dir())
        self.assertFalse((EXTENSION / "Resources").exists())
        self.assertFalse((EXTENSION / "custom").exists())

    def test_release_builder_includes_all_changed_canonical_files(self) -> None:
        builder_path = EXTENSION / "scripts" / "build_release_package.py"
        spec = importlib.util.spec_from_file_location("phase3c17_builder", builder_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        entries = module.source_entries()
        for entry in (
            "files/client/custom/src/views/prospecting/dashboard.js",
            "files/client/custom/res/templates/prospecting/dashboard.tpl",
            "files/client/custom/res/templates/prospecting/search.tpl",
            "files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json",
            "files/custom/Espo/Modules/Prospecting/Resources/i18n/zh_CN/Global.json",
        ):
            self.assertIn(entry, entries)

    def test_materializer_has_snapshot_restore_and_observable_output(self) -> None:
        for contract in (
            "--snapshot=",
            "--restore=",
            "PHASE3C17_SNAPSHOT_CREATED",
            "PHASE3C17_NAVIGATION_BEFORE",
            "PHASE3C17_NAVIGATION_AFTER",
            "PHASE3C17_NAVIGATION_READY",
        ):
            self.assertIn(contract, self.materializer)


if __name__ == "__main__":
    unittest.main()
