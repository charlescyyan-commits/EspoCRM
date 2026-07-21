"""C16.3A-0 foundation: i18n scope labels and locale key parity."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "i18n"
C16_ENTITIES = ("Quote", "QuoteItem", "ProformaInvoice", "Approval")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(obj: object, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                keys |= flatten(value, path)
            else:
                keys.add(path)
    return keys


class C16I18nFoundationTests(unittest.TestCase):
    def test_global_scope_labels_cover_c16_entities_with_locale_parity(self) -> None:
        en = load(I18N / "en_US" / "Global.json")
        zh = load(I18N / "zh_CN" / "Global.json")

        for entity in C16_ENTITIES:
            self.assertIn(entity, en["scopeNames"])
            self.assertIn(entity, en["scopeNamesPlural"])
            self.assertIn(entity, zh["scopeNames"])
            self.assertIn(entity, zh["scopeNamesPlural"])
            self.assertTrue(str(en["scopeNames"][entity]).strip())
            self.assertTrue(str(zh["scopeNames"][entity]).strip())

        self.assertEqual(flatten(en), flatten(zh))

    def test_c16_entity_locale_files_have_key_parity(self) -> None:
        for entity in C16_ENTITIES:
            en_path = I18N / "en_US" / f"{entity}.json"
            zh_path = I18N / "zh_CN" / f"{entity}.json"
            self.assertTrue(en_path.is_file(), msg=f"missing {en_path}")
            self.assertTrue(zh_path.is_file(), msg=f"missing {zh_path}")
            en_keys = flatten(load(en_path))
            zh_keys = flatten(load(zh_path))
            self.assertEqual(en_keys, zh_keys, msg=f"{entity} en_US/zh_CN key mismatch")


if __name__ == "__main__":
    unittest.main()
