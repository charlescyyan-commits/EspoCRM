"""Offline guard for the single authoritative Prospecting metadata tree."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
AUTHORITATIVE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources"
STALE_RESOURCES = EXTENSION / "Resources"
STALE_CUSTOM = EXTENSION / "custom"


class Phase3C17WP05MetadataSourceGuardTests(unittest.TestCase):
    def test_packaged_prospecting_resources_are_authoritative(self) -> None:
        self.assertTrue(AUTHORITATIVE.is_dir(), msg=f"Missing authoritative metadata tree: {AUTHORITATIVE}")
        for name in ("metadata", "layouts", "i18n"):
            self.assertTrue((AUTHORITATIVE / name).is_dir(), msg=f"Missing packaged Resource category: {name}")

    def test_stale_metadata_tree_has_been_removed(self) -> None:
        self.assertFalse(
            STALE_RESOURCES.exists(),
            msg="crm-extension/Resources is stale and must not be recreated as a metadata source.",
        )

    def test_no_unpackaged_prospecting_resources_tree_exists(self) -> None:
        resource_trees = [path for path in EXTENSION.rglob("Resources") if path.is_dir() and path != AUTHORITATIVE]
        self.assertEqual(
            resource_trees,
            [],
            msg="Only files/custom/Espo/Modules/Prospecting/Resources may provide Prospecting metadata.",
        )

    def test_legacy_custom_placeholder_tree_has_been_removed(self) -> None:
        self.assertFalse(
            STALE_CUSTOM.exists(),
            msg="crm-extension/custom is a non-packaged placeholder tree and must not be recreated.",
        )


if __name__ == "__main__":
    unittest.main()
