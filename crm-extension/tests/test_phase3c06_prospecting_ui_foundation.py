"""Static UI-contract tests for Phase3C06 Prospecting UI Foundation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


EXTENSION = Path(__file__).resolve().parents[1]
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def layout_labels(path: Path) -> set[str]:
    return {section["label"] for section in load_json(path)}


class ProspectingUiFoundationTests(unittest.TestCase):
    def test_navigation_scopes_are_native_prospecting_tabs(self) -> None:
        for scope_name in ("ProspectingDashboard", "ProspectingSearch"):
            scope = load_json(MODULE / "Resources" / "metadata" / "scopes" / f"{scope_name}.json")
            self.assertFalse(scope["entity"])
            self.assertFalse(scope["object"])
            self.assertTrue(scope["tab"])
            self.assertFalse(scope["acl"])
            self.assertEqual(scope["module"], "Prospecting")

        global_i18n = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")
        self.assertEqual(
            {
                name: global_i18n["scopeNames"][name]
                for name in ("ProspectingDashboard", "ProspectingSearch")
            },
            {
                "ProspectingDashboard": "Prospecting Operations",
                "ProspectingSearch": "Search Center",
            },
        )

        for scope_name, controller, icon in (
            ("ProspectingDashboard", "custom:controllers/prospecting-dashboard", "fas fa-binoculars"),
            ("ProspectingSearch", "custom:controllers/prospecting-search", "fas fa-search"),
        ):
            client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / f"{scope_name}.json")
            self.assertEqual(client_defs["controller"], controller)
            self.assertEqual(client_defs["iconClass"], icon)

        search_job_client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SearchJob.json")
        self.assertEqual(search_job_client_defs["iconClass"], "fas fa-list")

    def test_navigation_and_dashboard_template_expose_requested_surfaces(self) -> None:
        source = (CLIENT / "res" / "templates" / "prospecting" / "dashboard.tpl").read_text(encoding="utf-8")
        dashboard_js = (CLIENT / "src" / "views" / "prospecting" / "dashboard.js").read_text(encoding="utf-8")
        navigation_surface = source + dashboard_js
        for route in ("#ProspectingDashboard", "#ProspectingSearch", "#SearchJob", "#ProspectPool", "#SearchStrategy"):
            self.assertIn(route, navigation_surface)
        # Phase3U03 dashboard productization: overview + summary + recent discovery empty states
        for label in (
            "Operational Centers",
            "Prospecting Summary",
            "Recent Discovery Activity",
            "No data available",
        ):
            self.assertIn(label, source)
        labels = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")["labels"]
        self.assertEqual(labels["C17DashboardSearchJobs"], "Search Jobs")
        self.assertEqual(labels["C17DashboardProspectPool"], "Prospect Pool")
        self.assertIn("getLanguage().translate(key, 'labels', 'Global')", dashboard_js)
        self.assertIn('data-action="open-search"', source)

        for key in (
            "C17DashboardSearchCenter",
            "C17DashboardResearchCenter",
            "C17DashboardOutreachCenter",
            "C17DashboardQuoteCenter",
        ):
            self.assertIn(key, dashboard_js)
        self.assertIn("countRecords", dashboard_js)
        self.assertIn("loadRecentJobs", dashboard_js)
        self.assertIn("ProspectPool", dashboard_js)
        self.assertIn("SearchJob", dashboard_js)
        self.assertNotIn("PHASE3B02", dashboard_js)
        self.assertNotIn("FORMULA-TEST", dashboard_js)

    def test_search_only_creates_a_queued_search_job_with_acl_check(self) -> None:
        source = (CLIENT / "src" / "views" / "prospecting" / "search.js").read_text(encoding="utf-8")
        template = (CLIENT / "res" / "templates" / "prospecting" / "search.tpl").read_text(encoding="utf-8")
        self.assertIn("getAcl().check('SearchJob', 'create')", source)
        self.assertIn("if (!country || !keyword)", source)
        self.assertIn("Country and Keyword are required", source)
        self.assertIn("getModelFactory().create('SearchJob')", source)
        self.assertIn("create('SearchJob').then(function (model)", source)
        self.assertIn("status: 'QUEUED'", source)
        self.assertIn("assignedUserId: currentUser.id", source)
        self.assertNotIn("Ajax.", source)
        self.assertNotIn("provider/", source.lower())
        self.assertNotIn("runtime", source.lower())
        self.assertNotIn("research", source.lower())
        for label in ("Country", "Keyword", "Provider", "Strategy", "Result Limit", "Start Search"):
            self.assertIn(label, template)
        self.assertIn("creates a queued Search Job only", template)
        self.assertIn("disabled", template)

    def test_search_job_layout_uses_frozen_fields_only(self) -> None:
        labels = layout_labels(MODULE / "Resources" / "layouts" / "SearchJob" / "detail.json")
        # Phase3U02 native presentation panels (supersede C06 draft panel names)
        self.assertTrue({"Search Job", "Execution", "Ownership"}.issubset(labels))
        fields = load_json(MODULE / "Resources" / "metadata" / "entityDefs" / "SearchJob.json")["fields"]
        detail = load_json(MODULE / "Resources" / "layouts" / "SearchJob" / "detail.json")
        for section in detail:
            for row in section["rows"]:
                for cell in row:
                    if isinstance(cell, dict) and "name" in cell:
                        self.assertIn(cell["name"], fields)

    def test_prospect_pool_list_and_detail_preserve_native_read_model(self) -> None:
        listing = load_json(MODULE / "Resources" / "layouts" / "ProspectPool" / "list.json")
        # Phase3U02 list: website added; queue/status retained; qualification/crmPush moved to detail
        self.assertEqual(
            [item["name"] for item in listing],
            ["name", "website", "country", "source", "researchStatus", "createdAt"],
        )
        labels = layout_labels(MODULE / "Resources" / "layouts" / "ProspectPool" / "detail.json")
        self.assertTrue(
            {"Discovery Information", "Acquisition Pipeline", "Notes and Ownership"}.issubset(labels)
        )
        labels_i18n = load_json(MODULE / "Resources" / "i18n" / "en_US" / "ProspectPool.json")
        self.assertEqual(labels_i18n["fields"]["name"], "Company")
        self.assertEqual(labels_i18n["fields"]["source"], "Provider")
        self.assertEqual(labels_i18n["fields"]["crmPushStatus"], "CRM Push Status")

    def test_business_labels_and_dashlet_titles_use_merged_vocabulary(self) -> None:
        global_i18n = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")
        self.assertEqual(global_i18n["scopeNamesPlural"]["SearchJob"], "Search Jobs")
        self.assertEqual(global_i18n["scopeNamesPlural"]["ProspectPool"], "Prospect Pool")
        self.assertEqual(global_i18n["dashlets"]["AcquisitionOverview"], "Acquisition Overview")

        for filename, title in (
            ("AcquisitionOverview.json", "Acquisition Overview"),
            ("AcquisitionDiscoveryJobs.json", "Search Jobs"),
            ("AcquisitionLeadPool.json", "Prospect Pool"),
        ):
            dashlet = load_json(MODULE / "Resources" / "metadata" / "dashlets" / filename)
            self.assertEqual(dashlet["options"]["defaults"]["title"], title)

    def test_strategy_view_remains_the_frozen_existing_read_surface(self) -> None:
        labels = layout_labels(MODULE / "Resources" / "layouts" / "SearchStrategy" / "detail.json")
        self.assertTrue({"Strategy Definition", "Query Plan"}.issubset(labels))
        client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SearchStrategy.json")
        self.assertEqual(client_defs["detailActionList"][-1]["name"], "generateJobs")

    def test_existing_entity_acl_and_frozen_contracts_remain_authoritative(self) -> None:
        for scope_name in ("SearchJob", "ProspectPool", "SearchStrategy"):
            scope = load_json(MODULE / "Resources" / "metadata" / "scopes" / f"{scope_name}.json")
            self.assertTrue(scope["acl"])
            self.assertTrue(scope["tab"])
            self.assertEqual(scope["module"], "Prospecting")


if __name__ == "__main__":
    unittest.main()
