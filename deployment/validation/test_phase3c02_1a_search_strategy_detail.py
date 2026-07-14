from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DETAIL_VIEW = ROOT / "crm-extension" / "files" / "client" / "custom" / "src" / "views" / "search-strategy" / "detail.js"
CLIENT_DEFS = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "metadata" / "clientDefs" / "SearchStrategy.json"
ACTION_HANDLER = ROOT / "crm-extension" / "files" / "client" / "custom" / "src" / "handlers" / "search-strategy" / "generate-jobs.js"


class SearchStrategyDetailViewTests(unittest.TestCase):
    def test_full_detail_view_is_not_used_as_a_record_view(self) -> None:
        source = DETAIL_VIEW.read_text(encoding="utf-8")

        self.assertIn("'views/detail'", source)

    def test_generate_jobs_uses_a_detail_action_handler(self) -> None:
        import json

        client_defs = json.loads(CLIENT_DEFS.read_text(encoding="utf-8"))

        # Phase3U03-C allows list-only empty-state recordViews; detail/edit remain frozen.
        self.assertEqual(
            client_defs.get("recordViews"),
            {"list": "custom:views/search-strategy/record/list"},
        )
        self.assertNotIn("detail", client_defs.get("recordViews", {}))
        self.assertNotIn("edit", client_defs.get("recordViews", {}))
        self.assertEqual(client_defs["detailActionList"][0], "__APPEND__")
        self.assertEqual(client_defs["detailActionList"][1]["name"], "generateJobs")
        self.assertEqual(client_defs["detailActionList"][1]["handler"], "custom:handlers/search-strategy/generate-jobs")
        self.assertTrue(ACTION_HANDLER.is_file())


if __name__ == "__main__":
    unittest.main()
