import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "crm-extension"
SURFACE = EXT / "Resources"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


class SearchStrategyFoundationTests(unittest.TestCase):
    def test_entity_metadata_is_registered_and_mirrored(self) -> None:
        self.assertEqual(
            _load_json(SURFACE / "entityDefs" / "SearchStrategy.json"),
            _load_json(MODULE / "Resources" / "metadata" / "entityDefs" / "SearchStrategy.json"),
        )
        self.assertEqual(
            _load_json(SURFACE / "acl" / "SearchStrategy.json"),
            _load_json(MODULE / "Resources" / "metadata" / "aclDefs" / "SearchStrategy.json"),
        )

        strategy = _load_json(MODULE / "Resources" / "metadata" / "entityDefs" / "SearchStrategy.json")
        self.assertEqual(
            set(strategy["fields"]),
            {
                "name", "product", "country", "region", "targetPersona", "targetCompanyType", "keywords",
                "excludedKeywords", "sourcePlan", "status", "generatedJobCount", "createdAt", "createdBy",
                "assignedUser", "teams", "searchJobs",
            },
        )
        self.assertEqual(strategy["fields"]["status"].get("default"), "DRAFT")
        self.assertEqual(strategy["links"]["searchJobs"]["entity"], "SearchJob")
        self.assertEqual(strategy["links"]["searchJobs"]["foreign"], "strategy")

        scope = _load_json(MODULE / "Resources" / "metadata" / "scopes" / "SearchStrategy.json")
        self.assertTrue(scope["entity"])
        self.assertTrue(scope["object"])
        self.assertTrue(scope["tab"])
        self.assertTrue(scope["acl"])
        self.assertEqual(scope["module"], "Prospecting")

    def test_entity_ui_baseline_is_present(self) -> None:
        for layout_name in ("detail.json", "list.json"):
            self.assertEqual(
                _load_json(SURFACE / "layouts" / "SearchStrategy" / layout_name),
                _load_json(MODULE / "Resources" / "layouts" / "SearchStrategy" / layout_name),
            )

        labels = _load_json(MODULE / "Resources" / "i18n" / "en_US" / "SearchStrategy.json")
        self.assertEqual(labels["fields"]["name"], "Search Strategy")
        self.assertEqual(labels["labels"]["SearchStrategys"], "Search Strategies")

        app_layouts = _load_json(MODULE / "Resources" / "metadata" / "app" / "layouts.json")
        self.assertEqual(app_layouts["SearchStrategy"]["detail"]["module"], "Prospecting")
        self.assertEqual(app_layouts["SearchStrategy"]["list"]["module"], "Prospecting")

        detail_view = EXT / "files" / "client" / "custom" / "src" / "views" / "search-strategy" / "detail.js"
        self.assertIn("'views/detail'", detail_view.read_text(encoding="utf-8"))
        self.assertTrue((MODULE / "Entities" / "SearchStrategy.php").is_file())
        self.assertTrue((MODULE / "Controllers" / "SearchStrategy.php").is_file())

        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["version"], "1.9.0-alpha")


if __name__ == "__main__":
    unittest.main()
