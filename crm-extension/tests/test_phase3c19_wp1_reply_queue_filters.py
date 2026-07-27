"""Phase3C19 WP1 ReplyEvent queue PrimaryFilter contracts (ADR-C19 / adr-c19-replyevent-v1)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
FILTERS_DIR = MODULE / "Classes" / "Select" / "ReplyEvent" / "PrimaryFilters"
SELECT_DEFS = MODULE / "Resources" / "metadata" / "selectDefs" / "ReplyEvent.json"
CLIENT_DEFS = MODULE / "Resources" / "metadata" / "clientDefs" / "ReplyEvent.json"
SCOPES = MODULE / "Resources" / "metadata" / "scopes" / "ReplyEvent.json"
CONTROLLER = MODULE / "Controllers" / "ReplyEvent.php"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs" / "ReplyEvent.json"
POLICY = MODULE / "Resources" / "metadata" / "app" / "prospectingWorkflow.json"
I18N_EN = MODULE / "Resources" / "i18n" / "en_US" / "ReplyEvent.json"
I18N_ZH = MODULE / "Resources" / "i18n" / "zh_CN" / "ReplyEvent.json"

GOVERNANCE_MARKER = "adr-c19-replyevent-v1"

# filter key, class name, expected triage status
C19_FILTERS = (
    ("c19OpenReplies", "C19OpenReplies", "OPEN"),
    ("c19MyReplies", "C19MyReplies", "IN_PROGRESS"),
)

TRIAGE_OPTIONS = ("OPEN", "IN_PROGRESS", "CLOSED")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase3C19ReplyQueueFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.open_source = read(FILTERS_DIR / "C19OpenReplies.php")
        cls.my_source = read(FILTERS_DIR / "C19MyReplies.php")
        cls.select_defs = load_json(SELECT_DEFS)
        cls.client_defs = load_json(CLIENT_DEFS)
        cls.entity_defs = load_json(ENTITY_DEFS)

    def test_selectdefs_maps_each_reply_queue_filter(self) -> None:
        filter_map = self.select_defs["primaryFilterClassNameMap"]
        for filter_key, class_name, _status in C19_FILTERS:
            self.assertIn(filter_key, filter_map)
            self.assertEqual(
                filter_map[filter_key],
                "Espo\\Modules\\Prospecting\\Classes\\Select\\ReplyEvent\\"
                f"PrimaryFilters\\{class_name}",
            )
        # C17 monitoring queue mapping is preserved, not replaced.
        self.assertIn("c17AwaitingReply", filter_map)

    def test_primary_filter_classes_implement_native_interface(self) -> None:
        for filter_key, class_name, _status in C19_FILTERS:
            source = read(FILTERS_DIR / f"{class_name}.php")
            self.assertIn(
                "namespace Espo\\Modules\\Prospecting\\Classes\\Select\\ReplyEvent\\PrimaryFilters;",
                source,
            )
            self.assertIn("use Espo\\Core\\Select\\Primary\\Filter;", source)
            self.assertIn("use Espo\\ORM\\Query\\SelectBuilder;", source)
            self.assertIn(f"class {class_name} implements Filter", source)
            self.assertIn("public function apply(SelectBuilder $queryBuilder): void", source)
            self.assertIn(GOVERNANCE_MARKER, source)

    def test_open_queue_returns_only_open(self) -> None:
        self.assertIn("$queryBuilder->where(['triageStatus' => 'OPEN']);", self.open_source)
        match = re.search(r"->where\(\['triageStatus'\s*=>\s*'(?P<value>[A-Z_]+)'\]\)", self.open_source)
        self.assertIsNotNone(match)

        def passes(record: dict) -> bool:
            return record.get("triageStatus") == match.group("value")

        self.assertTrue(passes({"triageStatus": "OPEN"}))
        self.assertFalse(passes({"triageStatus": "IN_PROGRESS"}))
        self.assertFalse(passes({"triageStatus": "CLOSED"}), msg="c19OpenReplies must exclude CLOSED")
        self.assertFalse(passes({"triageStatus": None}), msg="c19OpenReplies must exclude non-actionable events")

    def test_my_queue_returns_only_assigned_in_progress(self) -> None:
        # Server-side current-user binding via constructor injection.
        self.assertIn("use Espo\\Entities\\User;", self.my_source)
        self.assertIn("public function __construct(private User $user)", self.my_source)
        self.assertIn("'assignedUserId' => $this->user->getId()", self.my_source)
        self.assertIn("'triageStatus' => 'IN_PROGRESS'", self.my_source)

        status_match = re.search(r"'triageStatus'\s*=>\s*'(?P<value>[A-Z_]+)'", self.my_source)
        self.assertIsNotNone(status_match)

        def passes(record: dict, current_user_id: str) -> bool:
            return (
                record.get("triageStatus") == status_match.group("value")
                and record.get("assignedUserId") == current_user_id
            )

        self.assertTrue(passes({"triageStatus": "IN_PROGRESS", "assignedUserId": "u1"}, "u1"))
        self.assertFalse(passes({"triageStatus": "IN_PROGRESS", "assignedUserId": "u2"}, "u1"),
                         msg="c19MyReplies must exclude other operators' IN_PROGRESS replies")
        self.assertFalse(passes({"triageStatus": "OPEN", "assignedUserId": "u1"}, "u1"))
        self.assertFalse(passes({"triageStatus": "CLOSED", "assignedUserId": "u1"}, "u1"),
                         msg="c19MyReplies must exclude CLOSED")

    def test_closed_is_excluded_from_every_reply_queue(self) -> None:
        for _key, class_name, _status in C19_FILTERS:
            source = read(FILTERS_DIR / f"{class_name}.php")
            self.assertNotIn("'CLOSED'", source, msg=f"{class_name} must not select CLOSED")

    def test_filter_predicates_reference_valid_triage_options(self) -> None:
        options = self.entity_defs["fields"]["triageStatus"]["options"]
        self.assertEqual(options, list(TRIAGE_OPTIONS))
        for _key, _class_name, status in C19_FILTERS:
            self.assertIn(status, options)

    def test_clientdefs_exposes_filters_without_client_where(self) -> None:
        by_name = {item["name"]: item for item in self.client_defs["filterList"]}
        for filter_key, _class_name, _status in C19_FILTERS:
            self.assertIn(filter_key, by_name)
            self.assertNotIn("where", by_name[filter_key], msg="No client-only where filters")
        # C17 frozen filter exposure is unchanged (client where preserved as-is).
        self.assertEqual(
            by_name["c17AwaitingReply"].get("where"),
            [{"type": "equals", "attribute": "replyStatus", "value": "SENT"}],
        )

    def test_i18n_preset_filter_labels(self) -> None:
        en = load_json(I18N_EN)["presetFilters"]
        zh = load_json(I18N_ZH)["presetFilters"]
        self.assertEqual(en["c19OpenReplies"], "Open Replies")
        self.assertEqual(en["c19MyReplies"], "My Replies")
        self.assertIn("c19OpenReplies", zh)
        self.assertIn("c19MyReplies", zh)

    def test_acl_narrowing_preserved(self) -> None:
        scopes = load_json(SCOPES)
        self.assertTrue(scopes.get("acl"), msg="ReplyEvent scope must remain ACL controlled")
        controller = read(CONTROLLER)
        self.assertIn("class ReplyEvent extends Record", controller)
        for bypass in ("bypass", "skipAccessCheck", "disableAccessControl"):
            self.assertNotIn(bypass, controller, msg="ReplyEvent controller must not touch ACL")
        for _key, class_name, _status in C19_FILTERS:
            source = read(FILTERS_DIR / f"{class_name}.php")
            self.assertNotIn("saveEntity", source)
            self.assertNotIn("set('triageStatus'", source)
            self.assertNotIn("StatusMutationSaveOption", source)
            self.assertNotIn("skipAccessCheck", source)

    def test_governance_marker_preserved(self) -> None:
        for _key, class_name, _status in C19_FILTERS:
            source = read(FILTERS_DIR / f"{class_name}.php")
            self.assertIn(GOVERNANCE_MARKER, source)
        policy = load_json(POLICY)
        self.assertEqual(policy["replyEvent"]["marker"], GOVERNANCE_MARKER)
        for key in policy["actionRoleBindings"]:
            self.assertFalse(key.startswith("replyEvent."), msg=f"Unexpected reply binding {key}")

    def test_does_not_touch_send_execution_quote_or_navigation(self) -> None:
        for _key, class_name, _status in C19_FILTERS:
            source = read(FILTERS_DIR / f"{class_name}.php")
            self.assertNotIn("SendExecution", source)
            self.assertNotIn("Quote", source)
            self.assertNotIn("Approval", source)
            self.assertNotIn("tabList", source)
            self.assertNotIn("dashboard", source.lower())


if __name__ == "__main__":
    unittest.main()
