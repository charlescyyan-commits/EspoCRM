"""Phase3C20 WP1.3.2 ProviderCredential layout and translation contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
LAYOUTS = AI_PLATFORM / "Resources" / "layouts" / "ProviderCredential"
LIST_LAYOUT = LAYOUTS / "list.json"
DETAIL_LAYOUT = LAYOUTS / "detail.json"
I18N = AI_PLATFORM / "Resources" / "i18n"
ENTITY_I18N = {
    "en_US": I18N / "en_US" / "ProviderCredential.json",
    "zh_CN": I18N / "zh_CN" / "ProviderCredential.json",
}
GLOBAL_I18N = {
    "en_US": I18N / "en_US" / "Global.json",
    "zh_CN": I18N / "zh_CN" / "Global.json",
}

DISPLAY_FIELDS = {
    "displayName",
    "providerKey",
    "environment",
    "fingerprint",
    "lastFour",
    "ownerUser",
    "rotationDueAt",
    "lastRotatedAt",
    "description",
}
ALL_LABEL_FIELDS = DISPLAY_FIELDS | {"credentialReference"}
FORBIDDEN_SECRET_FIELDS = {
    "apiKey",
    "apiSecret",
    "token",
    "password",
    "secret",
    "plaintextCredential",
    "encryptedSecret",
    "decryptedValue",
    "rawCredential",
    "privateKey",
    "accessToken",
    "refreshToken",
}
FORBIDDEN_RUNTIME_DIRECTORIES = (
    "Api",
    "Actions",
    "Controllers",
    "Entities",
    "Jobs",
)
ALLOWED_WP3_RUNTIME_FILES = {
    AI_PLATFORM / "Services" / "AIJobService.php",
    AI_PLATFORM / "Services" / "AIJobStatusMutationSaveOption.php",
    AI_PLATFORM / "Hooks" / "AIJob" / "AIJobStatusMutationGuard.php",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def layout_fields(value: object) -> list[str]:
    names: list[str] = []
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str):
            names.append(name)
        for nested in value.values():
            names.extend(layout_fields(nested))
    elif isinstance(value, list):
        for nested in value:
            names.extend(layout_fields(nested))
    return names


class Phase3C20WP13LayoutI18nTests(unittest.TestCase):
    def test_native_list_and_detail_layouts_exist(self) -> None:
        self.assertEqual(set(LAYOUTS.glob("*.json")), {LIST_LAYOUT, DETAIL_LAYOUT})
        self.assertEqual(
            layout_fields(load_json(LIST_LAYOUT)),
            ["displayName", "providerKey", "environment", "fingerprint", "lastFour", "rotationDueAt"],
        )
        self.assertEqual(set(layout_fields(load_json(DETAIL_LAYOUT))), DISPLAY_FIELDS)

    def test_credential_reference_is_absent_from_every_layout(self) -> None:
        self.assertFalse((LAYOUTS / "search.json").exists())
        for path in LAYOUTS.glob("*.json"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("credentialReference", source, msg=str(path))

    def test_forbidden_secret_fields_are_absent_from_layouts_and_labels(self) -> None:
        presentation_files = {LIST_LAYOUT, DETAIL_LAYOUT, *ENTITY_I18N.values()}
        for path in presentation_files:
            source = path.read_text(encoding="utf-8")
            for identifier in FORBIDDEN_SECRET_FIELDS:
                self.assertIsNone(
                    re.search(rf"\b{re.escape(identifier)}\b", source, flags=re.IGNORECASE),
                    msg=f"{path}: {identifier}",
                )

    def test_english_and_chinese_field_labels_are_complete_and_aligned(self) -> None:
        translations = {locale: load_json(path) for locale, path in ENTITY_I18N.items()}
        english = translations["en_US"]
        chinese = translations["zh_CN"]
        self.assertEqual(set(english), {"fields", "links", "labels"})
        for section in english:
            self.assertEqual(set(english[section]), set(chinese[section]), msg=section)
        self.assertEqual(set(english["fields"]), ALL_LABEL_FIELDS)
        self.assertEqual(set(english["links"]), {"ownerUser"})
        self.assertEqual(
            set(english["labels"]),
            {"Create ProviderCredential", "ProviderCredentials", "Credential Reference Registry"},
        )

        self.assertEqual(load_json(GLOBAL_I18N["en_US"])["scopeNames"]["ProviderCredential"], "Provider Credential")
        self.assertEqual(load_json(GLOBAL_I18N["zh_CN"])["scopeNames"]["ProviderCredential"], "提供商凭据引用")

    def test_presentation_adds_no_client_or_runtime_layer(self) -> None:
        self.assertFalse((AI_PLATFORM / "Resources" / "metadata" / "clientDefs").exists())
        self.assertEqual(list(AI_PLATFORM.rglob("*.js")), [])
        for directory in FORBIDDEN_RUNTIME_DIRECTORIES:
            self.assertFalse((AI_PLATFORM / directory).exists(), msg=directory)
        runtime_files = {
            * (AI_PLATFORM / "Services").glob("*.php"),
            * (AI_PLATFORM / "Hooks").rglob("*.php"),
        }
        self.assertEqual(runtime_files, ALLOWED_WP3_RUNTIME_FILES)


if __name__ == "__main__":
    unittest.main()
