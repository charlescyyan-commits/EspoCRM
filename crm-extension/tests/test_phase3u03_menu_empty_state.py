"""Phase3U03-B/C — menu prominence, empty states, list presentation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


EXTENSION = Path(__file__).resolve().parents[1]
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ProspectingMenuEmptyStateTests(unittest.TestCase):
    def test_prospecting_module_orders_before_crm(self) -> None:
        module = load_json(MODULE / "Resources" / "module.json")
        self.assertEqual(module["order"], 5)
        self.assertLess(module["order"], 10)

    def test_empty_state_i18n_labels(self) -> None:
        cases = {
            "ProspectPool": "No prospects yet. Start a discovery search to build your prospect pool.",
            "SearchJob": "No search jobs yet. Create your first search job.",
            "SearchStrategy": "No search strategies configured. Create a strategy to start discovery.",
            "ResearchEvidence": "Website research results will appear after prospects are analyzed.",
        }
        for entity, message in cases.items():
            i18n = load_json(MODULE / "Resources" / "i18n" / "en_US" / f"{entity}.json")
            self.assertEqual(i18n["labels"]["No Data"], message)

    def test_empty_state_record_list_views_registered(self) -> None:
        mapping = {
            "ProspectPool": "custom:views/prospect-pool/record/list",
            "SearchJob": "custom:views/search-job/record/list",
            "SearchStrategy": "custom:views/search-strategy/record/list",
            "ResearchEvidence": "custom:views/research-evidence/record/list",
        }
        paths = {
            "ProspectPool": CLIENT / "src" / "views" / "prospect-pool" / "record" / "list.js",
            "SearchJob": CLIENT / "src" / "views" / "search-job" / "record" / "list.js",
            "SearchStrategy": CLIENT / "src" / "views" / "search-strategy" / "record" / "list.js",
            "ResearchEvidence": CLIENT / "src" / "views" / "research-evidence" / "record" / "list.js",
        }
        for entity, view_name in mapping.items():
            client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / f"{entity}.json")
            self.assertEqual(client_defs["recordViews"]["list"], view_name)
            source = paths[entity].read_text(encoding="utf-8")
            self.assertIn("emptyStateText", source)
            self.assertIn("applyEmptyStateText", source)
            self.assertNotIn("Ajax.", source)

    def test_list_column_order_is_sales_facing(self) -> None:
        pool = load_json(MODULE / "Resources" / "layouts" / "ProspectPool" / "list.json")
        self.assertEqual(
            [item["name"] for item in pool],
            ["name", "website", "country", "source", "researchStatus", "createdAt"],
        )
        jobs = load_json(MODULE / "Resources" / "layouts" / "SearchJob" / "list.json")
        self.assertEqual(
            [item["name"] for item in jobs],
            ["name", "source", "strategy", "status", "resultCount", "createdAt"],
        )

    def test_c06_search_contract_untouched(self) -> None:
        search_js = (CLIENT / "src" / "views" / "prospecting" / "search.js").read_text(encoding="utf-8")
        self.assertIn("status: 'QUEUED'", search_js)
        self.assertNotIn("provider/", search_js.lower())
        self.assertNotIn("Ajax.", search_js)


if __name__ == "__main__":
    unittest.main()
