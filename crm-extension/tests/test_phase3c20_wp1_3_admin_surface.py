"""Phase3C20 WP1.3.1 native Administration credentials-surface contracts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "AIPlatform"
ADMIN_PANEL = AI_PLATFORM / "Resources" / "metadata" / "app" / "adminPanel.json"
APP_ACL = AI_PLATFORM / "Resources" / "metadata" / "app" / "acl.json"
APP_ACL_PORTAL = AI_PLATFORM / "Resources" / "metadata" / "app" / "aclPortal.json"
ENTITY_ACL = AI_PLATFORM / "Resources" / "metadata" / "entityAcl" / "ProviderCredential.json"
I18N = AI_PLATFORM / "Resources" / "i18n"
LAYOUTS = AI_PLATFORM / "Resources" / "layouts" / "ProviderCredential"
APPROVED_LAYOUTS = {LAYOUTS / "list.json", LAYOUTS / "detail.json"}

ADMIN_I18N = {
    "en_US": I18N / "en_US" / "Admin.json",
    "zh_CN": I18N / "zh_CN" / "Admin.json",
}
GLOBAL_I18N = {
    "en_US": I18N / "en_US" / "Global.json",
    "zh_CN": I18N / "zh_CN" / "Global.json",
}
FORBIDDEN_ADMIN_ENTRIES = {
    "AI Providers",
    "Providers",
    "Models",
    "Routes",
    "Prompt Templates",
    "Usage Logs",
    "Health Dashboard",
    "Health",
    "Jobs",
    "Capabilities",
}
FORBIDDEN_SECRET_IDENTIFIERS = {
    "apiKey",
    "apiSecret",
    "token",
    "password",
    "secret",
    "plaintextCredential",
    "encryptedSecret",
    "decryptedValue",
    "rawCredential",
}
FORBIDDEN_RUNTIME_DIRECTORIES = (
    "Api",
    "Actions",
    "Controllers",
    "Jobs",
)
ALLOWED_WP3_RUNTIME_FILES = {
    AI_PLATFORM / "Services" / "AIJobService.php",
    AI_PLATFORM / "Services" / "AIJobStatusMutationSaveOption.php",
    AI_PLATFORM / "Hooks" / "AIJob" / "AIJobStatusMutationGuard.php",
    AI_PLATFORM / "Services" / "AIRequestLogService.php",
    AI_PLATFORM / "Services" / "AIRequestLogSaveOption.php",
    AI_PLATFORM / "Hooks" / "AIRequestLog" / "AIRequestLogAppendOnlyGuard.php",
    AI_PLATFORM / "Services" / "PromptTemplateService.php",
    AI_PLATFORM / "Services" / "PromptTemplateSaveOption.php",
    AI_PLATFORM / "Hooks" / "PromptTemplate" / "PromptTemplateMutationGuard.php",
}
ALLOWED_WP3_ENTITIES = {
    AI_PLATFORM / "Entities" / "AIRequestLog.php",
    AI_PLATFORM / "Entities" / "PromptTemplate.php",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C20WP13AdminSurfaceTests(unittest.TestCase):
    def test_administration_contains_only_ai_platform_credentials_entry(self) -> None:
        metadata = load_json(ADMIN_PANEL)
        self.assertEqual(set(metadata), {"aiPlatform"})

        panel = metadata["aiPlatform"]
        self.assertEqual(panel["label"], "AI Platform")
        self.assertEqual(panel["order"], 80)
        self.assertEqual(
            panel["itemList"],
            [
                {
                    "url": "#ProviderCredential",
                    "label": "Credentials",
                    "iconClass": "fas fa-key",
                    "description": "providerCredentialReferenceCustody",
                }
            ],
        )
        self.assertNotIn("recordView", panel["itemList"][0])

    def test_only_approved_administration_surface_exists(self) -> None:
        metadata = load_json(ADMIN_PANEL)
        labels = {metadata["aiPlatform"]["label"]}
        labels.update(item["label"] for item in metadata["aiPlatform"]["itemList"])
        self.assertEqual(labels, {"AI Platform", "Credentials"})
        self.assertTrue(labels.isdisjoint(FORBIDDEN_ADMIN_ENTRIES))

    def test_administration_labels_have_english_chinese_parity(self) -> None:
        for locale, path in ADMIN_I18N.items():
            self.assertTrue(path.is_file(), msg=locale)
        english = load_json(ADMIN_I18N["en_US"])
        chinese = load_json(ADMIN_I18N["zh_CN"])
        self.assertEqual(set(english), {"labels", "descriptions", "keywords"})
        for section in english:
            self.assertEqual(set(english[section]), set(chinese[section]), msg=section)
        self.assertEqual(set(english["labels"]), {"AI Platform", "Credentials"})

        for locale, path in GLOBAL_I18N.items():
            labels = load_json(path)
            self.assertEqual(set(labels), {"scopeNames", "scopeNamesPlural"}, msg=locale)
            self.assertEqual(set(labels["scopeNames"]), {"ProviderCredential"}, msg=locale)
            self.assertEqual(set(labels["scopeNamesPlural"]), {"ProviderCredential"}, msg=locale)

    def test_acl_remains_admin_only_and_portal_denied(self) -> None:
        acl = load_json(APP_ACL)
        self.assertFalse(acl["mandatory"]["scopeLevel"]["ProviderCredential"])
        self.assertEqual(
            acl["adminMandatory"]["scopeLevel"]["ProviderCredential"],
            {"create": "yes", "read": "all", "edit": "all", "delete": "all"},
        )
        self.assertFalse(
            load_json(APP_ACL_PORTAL)["mandatory"]["scopeLevel"]["ProviderCredential"]
        )

    def test_ui_metadata_does_not_expose_secret_identifiers_or_reference(self) -> None:
        ui_files = {ADMIN_PANEL, *ADMIN_I18N.values(), *GLOBAL_I18N.values()}
        for path in ui_files:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("credentialReference", source, msg=str(path))
            for identifier in FORBIDDEN_SECRET_IDENTIFIERS:
                self.assertIsNone(
                    re.search(rf"\b{re.escape(identifier)}\b", source, flags=re.IGNORECASE),
                    msg=f"{path}: {identifier}",
                )
        self.assertEqual(
            load_json(ENTITY_ACL),
            {"fields": {"credentialReference": {"internal": True}}},
        )

    def test_native_surface_adds_no_custom_js_or_runtime_layer(self) -> None:
        self.assertEqual(list(AI_PLATFORM.rglob("*.js")), [])
        for directory in FORBIDDEN_RUNTIME_DIRECTORIES:
            self.assertFalse((AI_PLATFORM / directory).exists(), msg=directory)
        runtime_files = {
            * (AI_PLATFORM / "Services").glob("*.php"),
            * (AI_PLATFORM / "Hooks").rglob("*.php"),
        }
        self.assertEqual(runtime_files, ALLOWED_WP3_RUNTIME_FILES)
        self.assertEqual(
            set((AI_PLATFORM / "Entities").glob("*.php")),
            ALLOWED_WP3_ENTITIES,
        )
        self.assertFalse((AI_PLATFORM / "Resources" / "metadata" / "clientDefs").exists())
        self.assertEqual(
            set((AI_PLATFORM / "Resources" / "layouts").rglob("*.json")),
            APPROVED_LAYOUTS,
        )


if __name__ == "__main__":
    unittest.main()
