"""Focused runtime-entry and localization contracts for Phase3C17 WP1.4B."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


EXTENSION = Path(__file__).resolve().parents[1]
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C17WP14BRuntimeFixTests(unittest.TestCase):
    def test_operational_record_entries_have_native_record_controllers(self) -> None:
        for entity_type in ("DraftApproval", "Quote"):
            source = (MODULE / "Controllers" / f"{entity_type}.php").read_text(encoding="utf-8")
            self.assertIn("namespace Espo\\Modules\\Prospecting\\Controllers;", source)
            self.assertIn("use Espo\\Core\\Controllers\\Record;", source)
            self.assertIn(f"class {entity_type} extends Record", source)

    def test_workflow_page_i18n_keys_have_en_zh_parity(self) -> None:
        for entity_type in ("ProspectingSearch", "ProspectingDashboard", "Quote"):
            en = load_json(MODULE / "Resources" / "i18n" / "en_US" / f"{entity_type}.json")
            zh = load_json(MODULE / "Resources" / "i18n" / "zh_CN" / f"{entity_type}.json")
            self.assertEqual(set(en["labels"]), set(zh["labels"]), msg=entity_type)

    def test_search_and_dashboard_visible_copy_is_i18n_backed(self) -> None:
        search_source = (CLIENT / "src" / "views" / "prospecting" / "search.js").read_text(encoding="utf-8")
        search_template = (CLIENT / "res" / "templates" / "prospecting" / "search.tpl").read_text(encoding="utf-8")
        dashboard_source = (CLIENT / "src" / "views" / "prospecting" / "dashboard.js").read_text(encoding="utf-8")
        dashboard_template = (CLIENT / "res" / "templates" / "prospecting" / "dashboard.tpl").read_text(encoding="utf-8")

        self.assertIn("'labels', 'ProspectingSearch'", search_source)
        self.assertIn("labels.queuedOnlyHelp", search_template)
        self.assertNotIn("Country and Keyword are required", search_source)
        self.assertIn("'labels', 'ProspectingDashboard'", dashboard_source)
        self.assertIn("operationalCenters: translate('operationalCenters')", dashboard_source)
        self.assertIn("labels.operationsDescription", dashboard_template)
        self.assertIn("labels.totalProspects", dashboard_source)
        self.assertNotIn("label: 'Total Prospects'", dashboard_source)

    def test_quote_actions_keep_server_routing_and_localize_messages(self) -> None:
        source = (CLIENT / "src" / "handlers" / "quote" / "workflow-transition.js").read_text(encoding="utf-8")
        self.assertIn("'Prospecting/quote/'", source)
        self.assertIn("'labels', 'Quote'", source)
        self.assertIn("this.translate('quoteSubmittedForReview')", source)
        self.assertIn("this.translate('rejectionReasonPrompt')", source)
        self.assertNotIn("model.set('status'", source)
        self.assertNotIn('model.set("status"', source)


if __name__ == "__main__":
    unittest.main()
