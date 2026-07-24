"""Server-side PrimaryFilter contracts for Phase3C17 center queue filters.

CC-0A: the three Center Composition queue filters must be backed by EspoCRM
native server-side PrimaryFilter implementations, not client-only filterList
declarations. These tests verify:

1. selectDefs primaryFilterClassNameMap maps each filter key.
2. The mapped PrimaryFilter class exists with the correct namespace/interface.
3. The class generates the expected where condition.
4. Behavior parity: a record matching the condition is included, a
   non-matching record is excluded (simulated against the parsed condition).
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"

# entity, filter key, class name, field, value
C17_FILTERS = (
    ("DraftApproval", "c17Pending", "C17Pending", "status", "PENDING"),
    ("ReplyEvent", "c17AwaitingReply", "C17AwaitingReply", "replyStatus", "SENT"),
    ("Approval", "c17Pending", "C17Pending", "status", "PENDING"),
)

WHERE_PATTERN = re.compile(
    r"->where\(\['(?P<field>[A-Za-z0-9_]+)'\s*=>\s*'(?P<value>[A-Z_]+)'\]\)"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C17QueueFilterTests(unittest.TestCase):
    def test_selectdefs_maps_each_queue_filter(self) -> None:
        for entity, filter_key, class_name, _field, _value in C17_FILTERS:
            select_defs = load_json(MODULE / "Resources" / "metadata" / "selectDefs" / f"{entity}.json")
            filter_map = select_defs["primaryFilterClassNameMap"]
            self.assertIn(filter_key, filter_map, msg=f"{entity} selectDefs missing {filter_key}")
            self.assertEqual(
                filter_map[filter_key],
                f"Espo\\Modules\\Prospecting\\Classes\\Select\\{entity}\\PrimaryFilters\\{class_name}",
                msg=f"{entity} selectDefs maps {filter_key} to the wrong class",
            )

    def test_primary_filter_class_exists_and_implements_native_interface(self) -> None:
        for entity, _key, class_name, _field, _value in C17_FILTERS:
            path = MODULE / "Classes" / "Select" / entity / "PrimaryFilters" / f"{class_name}.php"
            self.assertTrue(path.is_file(), msg=f"Missing PrimaryFilter class: {path}")
            source = path.read_text(encoding="utf-8")
            self.assertIn(
                f"namespace Espo\\Modules\\Prospecting\\Classes\\Select\\{entity}\\PrimaryFilters;",
                source,
            )
            self.assertIn("use Espo\\Core\\Select\\Primary\\Filter;", source)
            self.assertIn("use Espo\\ORM\\Query\\SelectBuilder;", source)
            self.assertIn(f"class {class_name} implements Filter", source)
            self.assertIn("public function apply(SelectBuilder $queryBuilder): void", source)

    def test_primary_filter_generates_expected_where_condition(self) -> None:
        for entity, _key, class_name, field, value in C17_FILTERS:
            source = (
                MODULE / "Classes" / "Select" / entity / "PrimaryFilters" / f"{class_name}.php"
            ).read_text(encoding="utf-8")
            self.assertIn(f"$queryBuilder->where(['{field}' => '{value}']);", source)

    def test_where_condition_matches_enum_field_contract(self) -> None:
        for entity, _key, class_name, field, value in C17_FILTERS:
            entity_defs = load_json(MODULE / "Resources" / "metadata" / "entityDefs" / f"{entity}.json")
            field_def = entity_defs["fields"][field]
            self.assertEqual(field_def["type"], "enum", msg=f"{entity}.{field}")
            self.assertIn(value, field_def["options"], msg=f"{entity}.{field} missing {value}")

    def test_server_condition_matches_client_filterlist_declaration(self) -> None:
        # No filter bypass: client filterList and server PrimaryFilter must
        # express the identical condition for each queue filter.
        for entity, filter_key, _class, field, value in C17_FILTERS:
            client_defs = load_json(MODULE / "Resources" / "metadata" / "clientDefs" / f"{entity}.json")
            filter_def = next(
                item for item in client_defs["filterList"] if item["name"] == filter_key
            )
            where = filter_def["where"][0]
            self.assertEqual(where["type"], "equals")
            self.assertEqual(where["attribute"], field)
            self.assertEqual(where["value"], value)

    def test_behavior_matching_record_included_non_matching_excluded(self) -> None:
        # Simulate server-side filtering: parse the where condition from the
        # PrimaryFilter source and apply it to candidate records.
        for entity, _key, class_name, field, value in C17_FILTERS:
            source = (
                MODULE / "Classes" / "Select" / entity / "PrimaryFilters" / f"{class_name}.php"
            ).read_text(encoding="utf-8")
            match = WHERE_PATTERN.search(source)
            self.assertIsNotNone(match, msg=f"{entity}/{class_name} has no simple equality where")
            self.assertEqual(match.group("field"), field)
            self.assertEqual(match.group("value"), value)

            entity_defs = load_json(MODULE / "Resources" / "metadata" / "entityDefs" / f"{entity}.json")
            non_matching = [option for option in entity_defs["fields"][field]["options"] if option != value]
            self.assertTrue(non_matching, msg=f"{entity}.{field} needs non-matching options")

            matching_record = {field: value}
            excluded_records = [{field: option} for option in non_matching]

            def passes(record: dict) -> bool:
                return record.get(match.group("field")) == match.group("value")

            self.assertTrue(passes(matching_record), msg=f"{entity}: matching record excluded")
            for record in excluded_records:
                self.assertFalse(passes(record), msg=f"{entity}: non-matching record included")


if __name__ == "__main__":
    unittest.main()
