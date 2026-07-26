"""Phase3C18 WP2.1 SendExecution operational queue PrimaryFilter contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
TRANSITION = MODULE / "Services" / "SendExecutionTransitionService.php"
SCOPES = MODULE / "Resources" / "metadata" / "scopes" / "SendExecution.json"
CONTROLLER = MODULE / "Controllers" / "SendExecution.php"
ACL_DEFS = MODULE / "Resources" / "metadata" / "aclDefs" / "SendExecution.json"

# filter key, class name, expected status
C18_FILTERS = (
    ("c18ReadyToSend", "C18ReadyToSend", "READY"),
    ("c18FailedSend", "C18FailedSend", "FAILED"),
)

WHERE_PATTERN = re.compile(
    r"->where\(\['status'\s*=>\s*'(?P<value>[A-Z_]+)'\]\)"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C18SendExecutionQueueFilterTests(unittest.TestCase):
    def test_selectdefs_maps_each_operational_queue_filter(self) -> None:
        select_defs = load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "SendExecution.json")
        filter_map = select_defs["primaryFilterClassNameMap"]
        for filter_key, class_name, _status in C18_FILTERS:
            self.assertIn(filter_key, filter_map)
            self.assertEqual(
                filter_map[filter_key],
                "Espo\\Modules\\Prospecting\\Classes\\Select\\SendExecution\\"
                f"PrimaryFilters\\{class_name}",
            )

    def test_primary_filter_classes_implement_native_interface(self) -> None:
        for _key, class_name, status in C18_FILTERS:
            path = MODULE / "Classes" / "Select" / "SendExecution" / "PrimaryFilters" / f"{class_name}.php"
            source = read(path)
            self.assertIn(
                "namespace Espo\\Modules\\Prospecting\\Classes\\Select\\SendExecution\\PrimaryFilters;",
                source,
            )
            self.assertIn("use Espo\\Core\\Select\\Primary\\Filter;", source)
            self.assertIn("use Espo\\ORM\\Query\\SelectBuilder;", source)
            self.assertIn(f"class {class_name} implements Filter", source)
            self.assertIn("public function apply(SelectBuilder $queryBuilder): void", source)
            self.assertIn(f"$queryBuilder->where(['status' => '{status}']);", source)
            self.assertIn("adr-c18-sendexecution-v1", source)

    def test_filter_returns_correct_statuses(self) -> None:
        entity_defs = load_json(MODULE / "Resources" / "metadata" / "entityDefs" / "SendExecution.json")
        status_options = entity_defs["fields"]["status"]["options"]

        for _key, class_name, status in C18_FILTERS:
            source = read(
                MODULE / "Classes" / "Select" / "SendExecution" / "PrimaryFilters" / f"{class_name}.php"
            )
            match = WHERE_PATTERN.search(source)
            self.assertIsNotNone(match, msg=f"{class_name} missing status where")
            self.assertEqual(match.group("value"), status)
            self.assertIn(status, status_options)

            def passes(record: dict) -> bool:
                return record.get("status") == match.group("value")

            self.assertTrue(passes({"status": status}))
            for other in status_options:
                if other == status:
                    continue
                self.assertFalse(
                    passes({"status": other}),
                    msg=f"{class_name} must exclude status={other}",
                )

    def test_clientdefs_exposes_filters_without_client_where(self) -> None:
        client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SendExecution.json")
        names = [item["name"] for item in client_defs["filterList"]]
        self.assertEqual(names, ["c18ReadyToSend", "c18FailedSend"])
        for item in client_defs["filterList"]:
            self.assertNotIn("where", item, msg="No client-only where filters")

    def test_acl_narrowing_preserved(self) -> None:
        scopes = load_json(SCOPES)
        self.assertTrue(scopes.get("acl"), msg="SendExecution scope must remain ACL controlled")
        controller = read(CONTROLLER)
        for bypass in ("bypass", "skipAccessCheck", "disableAccessControl"):
            self.assertNotIn(bypass, controller, msg="SendExecution controller must not touch ACL")
        # Filter classes must not disable ACL or mutate status.
        for _key, class_name, _status in C18_FILTERS:
            source = read(
                MODULE / "Classes" / "Select" / "SendExecution" / "PrimaryFilters" / f"{class_name}.php"
            )
            self.assertNotIn("saveEntity", source)
            self.assertNotIn("set('status'", source)
            self.assertNotIn("StatusMutationSaveOption", source)
            self.assertNotIn("skipAccessCheck", source)
        acl_defs = load_json(ACL_DEFS)
        self.assertIsInstance(acl_defs, dict)

    def test_governance_marker_preserved(self) -> None:
        transition = read(TRANSITION)
        self.assertIn("public const GOVERNANCE_MARKER = 'adr-c18-sendexecution-v1';", transition)
        for _key, class_name, _status in C18_FILTERS:
            source = read(
                MODULE / "Classes" / "Select" / "SendExecution" / "PrimaryFilters" / f"{class_name}.php"
            )
            self.assertIn("adr-c18-sendexecution-v1", source)

    def test_does_not_touch_quote_approval_navigation_or_dashboard(self) -> None:
        for _key, class_name, _status in C18_FILTERS:
            source = read(
                MODULE / "Classes" / "Select" / "SendExecution" / "PrimaryFilters" / f"{class_name}.php"
            )
            self.assertNotIn("Quote", source)
            self.assertNotIn("Approval", source)
            self.assertNotIn("tabList", source)
            self.assertNotIn("dashboard", source.lower())


if __name__ == "__main__":
    unittest.main()
