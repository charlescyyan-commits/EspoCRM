"""Phase3C20 WP0.2 invariant registry governance contracts.

Parses docs/adr/C20_INVARIANT_REGISTRY.md and enforces the machine-checkable
registry rules. Does not implement AIPlatform, entities, providers, or runtime.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "adr" / "C20_INVARIANT_REGISTRY.md"
EXTENSION = ROOT / "crm-extension"
AI_PLATFORM = (
    EXTENSION
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "AIPlatform"
)
PROSPECTING = (
    EXTENSION
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
)

EXPECTED_IDS = [f"C20-INV-{index:02d}" for index in range(1, 23)]
EXPECTED_TOTAL = 22
ROW_RE = re.compile(
    r"^\|\s*(C20-INV-\d{2})\s*\|\s*(.*?)\s*\|\s*(ACTIVE|DEFERRED)\s*\|\s*(WP[0-5])\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$"
)
PROSPECTING_IDENTIFIERS = (
    "Lead",
    "ProspectPool",
    "SearchJob",
    "DraftApproval",
    "SendExecution",
    "ReplyEvent",
    "Quote",
)


def parse_registry(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line.strip())
        if not match:
            continue
        rows.append(
            {
                "id": match.group(1),
                "description": match.group(2).strip(),
                "status": match.group(3),
                "owning_wp": match.group(4),
                "test_file": match.group(5).strip(),
                "activation_trigger": match.group(6).strip(),
            }
        )
    return rows


class Phase3C20WP0InvariantRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assert REGISTRY.is_file(), f"Missing registry: {REGISTRY}"
        cls.rows = parse_registry(REGISTRY)
        cls.by_id = {row["id"]: row for row in cls.rows}

    def test_all_22_invariants_exist(self) -> None:
        self.assertEqual(len(self.rows), EXPECTED_TOTAL)
        self.assertEqual(sorted(self.by_id), EXPECTED_IDS)

    def test_no_duplicate_ids(self) -> None:
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_missing_ids(self) -> None:
        missing = [invariant_id for invariant_id in EXPECTED_IDS if invariant_id not in self.by_id]
        self.assertEqual(missing, [])

    def test_active_and_deferred_total_validation(self) -> None:
        active = [row for row in self.rows if row["status"] == "ACTIVE"]
        deferred = [row for row in self.rows if row["status"] == "DEFERRED"]
        self.assertEqual(len(active) + len(deferred), EXPECTED_TOTAL)
        self.assertEqual(len(active), 9)
        self.assertEqual(len(deferred), 13)
        for row in deferred:
            with self.subTest(invariant_id=row["id"]):
                self.assertTrue(row["owning_wp"], msg="DEFERRED rows must declare owning_wp")
                self.assertTrue(row["activation_trigger"], msg="DEFERRED rows must declare activation_trigger")

    def test_referenced_active_test_files_exist(self) -> None:
        for row in self.rows:
            if row["status"] != "ACTIVE":
                continue
            with self.subTest(invariant_id=row["id"]):
                self.assertNotEqual(row["test_file"], "-")
                self.assertTrue(
                    (ROOT / row["test_file"]).is_file(),
                    msg=f"ACTIVE invariant {row['id']} references missing test file: {row['test_file']}",
                )

    def test_c20_inv_02_aiplatform_has_no_prospecting_identifiers(self) -> None:
        if not AI_PLATFORM.exists():
            self.assertFalse(AI_PLATFORM.exists())
            return
        offenders: list[str] = []
        for path in AI_PLATFORM.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".php", ".json", ".js", ".tpl"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for identifier in PROSPECTING_IDENTIFIERS:
                if re.search(rf"\b{re.escape(identifier)}\b", text):
                    offenders.append(f"{path.relative_to(ROOT)}:{identifier}")
        self.assertEqual(offenders, [])

    def test_c20_inv_14_no_aiscore_entity_or_score_authority(self) -> None:
        aiscore_paths = list(EXTENSION.rglob("*AIScore*"))
        self.assertEqual(aiscore_paths, [], msg="AIScore artifacts are forbidden")
        if AI_PLATFORM.exists():
            for path in AI_PLATFORM.rglob("*.php"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("canonical_score", text)
                self.assertNotRegex(text, r"\bcomputeScore\b")
                self.assertNotRegex(text, r"\bcalculateScore\b")

    def test_c20_inv_15_no_email_delivery_path_in_aiplatform(self) -> None:
        self.assertFalse(
            any(EXTENSION.rglob("*EmailDeliveryProvider*")),
            msg="EmailDeliveryProvider must not exist in C20",
        )
        if AI_PLATFORM.exists():
            for path in AI_PLATFORM.rglob("*.php"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("EmailDeliveryProvider", text)
                self.assertNotIn("SendExecution", text)

    def test_c20_inv_16_19_21_22_advisory_qualification_governance(self) -> None:
        # WP0: no premature AIQualificationInsight entity or queue authority surfaces.
        insight_paths = list(EXTENSION.rglob("*AIQualificationInsight*"))
        self.assertEqual(
            insight_paths,
            [],
            msg="AIQualificationInsight must not be introduced before its owning WP",
        )
        primary_filters = (
            PROSPECTING
            / "Resources"
            / "metadata"
            / "clientDefs"
        )
        if primary_filters.is_dir():
            for path in primary_filters.rglob("*.json"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("AIQualificationInsight", text)
                self.assertNotIn("c20AiQualification", text)
        if AI_PLATFORM.exists():
            for path in AI_PLATFORM.rglob("*.php"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertIsNone(
                    re.search(r"\bqualify(Verdict|Decision)?\b", text, flags=re.IGNORECASE),
                    msg=f"Qualification decision terminology is forbidden in {path}",
                )
                self.assertNotIn("canonical_score", text)


if __name__ == "__main__":
    unittest.main()
