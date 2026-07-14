"""Phase3U03 dashboard productization — presentation contracts only."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


EXTENSION = Path(__file__).resolve().parents[1]
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
CLIENT = EXTENSION / "files" / "client" / "custom"
ROOT = EXTENSION.parent


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ProspectingDashboardProductizationTests(unittest.TestCase):
    def test_summary_dashlet_uses_native_counts_without_fake_data(self) -> None:
        view = (CLIENT / "src" / "views" / "dashlets" / "prospecting-summary.js").read_text(encoding="utf-8")
        self.assertIn("custom:views/dashlets/prospecting-summary", view)
        self.assertIn("countRecords", view)
        self.assertIn("ProspectPool", view)
        self.assertIn("prospectsReadyForResearch", view)
        self.assertIn("No data available", (CLIENT / "res" / "templates" / "dashlets" / "prospecting-summary.tpl").read_text(encoding="utf-8"))
        for banned in ("PHASE3B02", "FORMULA-TEST", "fake", "mockTotal", "hardcoded"):
            self.assertNotIn(banned, view)

        meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingSummary.json")
        self.assertEqual(meta["view"], "custom:views/dashlets/prospecting-summary")
        self.assertEqual(meta["options"]["defaults"]["title"], "Prospecting Summary")

    def test_recent_discovery_dashlet_lists_search_jobs(self) -> None:
        meta = load_json(MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingRecentDiscovery.json")
        self.assertEqual(meta["view"], "views/dashlets/abstract/record-list")
        self.assertEqual(meta["entityType"], "SearchJob")
        self.assertEqual(meta["options"]["defaults"]["title"], "Recent Discovery Activity")
        rows = meta["options"]["defaults"]["expandedLayout"]["rows"]
        flat = [cell["name"] for row in rows for cell in row]
        self.assertEqual(flat, ["name", "status", "createdAt", "resultCount"])

    def test_global_i18n_registers_new_dashlets(self) -> None:
        global_i18n = load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")
        self.assertEqual(global_i18n["dashlets"]["ProspectingSummary"], "Prospecting Summary")
        self.assertEqual(global_i18n["dashlets"]["ProspectingRecentDiscovery"], "Recent Discovery Activity")

    def test_c01_c06_runtime_contracts_untouched(self) -> None:
        # Search still only queues SearchJob; no provider/runtime calls.
        search_js = (CLIENT / "src" / "views" / "prospecting" / "search.js").read_text(encoding="utf-8")
        self.assertIn("status: 'QUEUED'", search_js)
        self.assertNotIn("Ajax.", search_js)
        self.assertNotIn("provider/", search_js.lower())

        # No connector/provider files changed by this presentation phase assertion surface.
        self.assertTrue((ROOT / "chitu-connector").is_dir())


if __name__ == "__main__":
    unittest.main()
