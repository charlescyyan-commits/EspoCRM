"""Phase3C20 WP0.4 BridgeErrorClass parity contracts.

Covers RATE_LIMIT parity plus new QUOTA / CONTENT_FILTER classes.
Does not change lifecycle ownership, retry policy ownership, or add provider runtime.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.send_execution_bridge import BridgeErrorClass


ROOT = Path(__file__).resolve().parents[2]
SERVICE_DIR = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Services"
)
BRIDGE_ERROR_CLASS_PHP = SERVICE_DIR / "BridgeErrorClass.php"
BRIDGE_ADAPTER = SERVICE_DIR / "SendExecutionBridgeAdapterService.php"
RESULT_ADAPTER = SERVICE_DIR / "SendExecutionResultAdapterService.php"
ENTITY_DEFS = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "metadata"
    / "entityDefs"
    / "SendExecution.json"
)
I18N_EN = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "i18n"
    / "en_US"
    / "SendExecution.json"
)
I18N_ZH = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "i18n"
    / "zh_CN"
    / "SendExecution.json"
)
EXISTING_CLASSES = (
    "NETWORK",
    "AUTH",
    "VALIDATION",
    "PROVIDER",
    "UNKNOWN",
)
PARITY_RATE_LIMIT = "RATE_LIMIT"
NEW_CLASSES = ("QUOTA", "CONTENT_FILTER")
ALL_BRIDGE_CLASSES = EXISTING_CLASSES + (PARITY_RATE_LIMIT,) + NEW_CLASSES

# Taxonomy-level eligibility only — does not schedule retries.
AUTO_RETRY_ELIGIBLE = {
    BridgeErrorClass.NETWORK,
    BridgeErrorClass.PROVIDER,
    BridgeErrorClass.RATE_LIMIT,
}
AUTO_RETRY_INELIGIBLE = {
    BridgeErrorClass.AUTH,
    BridgeErrorClass.VALIDATION,
    BridgeErrorClass.UNKNOWN,
    BridgeErrorClass.QUOTA,
    BridgeErrorClass.CONTENT_FILTER,
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


class Phase3C20WP0BridgeErrorParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.php = read(BRIDGE_ERROR_CLASS_PHP)
        cls.bridge_adapter = read(BRIDGE_ADAPTER)
        cls.result_adapter = read(RESULT_ADAPTER)
        cls.entity_defs = load_json(ENTITY_DEFS)
        cls.i18n_en = load_json(I18N_EN)
        cls.i18n_zh = load_json(I18N_ZH)

    def test_python_bridge_error_class_has_parity_and_new_categories(self) -> None:
        values = {member.value for member in BridgeErrorClass}
        self.assertEqual(values, set(ALL_BRIDGE_CLASSES))
        self.assertIn(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass)
        self.assertIn(BridgeErrorClass.QUOTA, BridgeErrorClass)
        self.assertIn(BridgeErrorClass.CONTENT_FILTER, BridgeErrorClass)

    def test_php_bridge_error_class_has_parity_and_new_categories(self) -> None:
        for name in ALL_BRIDGE_CLASSES:
            with self.subTest(name=name):
                self.assertIn(f"public const {name} = '{name}';", self.php)
        values_block = re.search(r"function values\(\).*?return \[(.*?)\];", self.php, re.S)
        self.assertIsNotNone(values_block)
        returned = values_block.group(1)  # type: ignore[union-attr]
        for name in ALL_BRIDGE_CLASSES:
            with self.subTest(returned=name):
                self.assertIn(f"self::{name}", returned)

    def test_rate_limit_remains_distinguishable_from_core_classes(self) -> None:
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.NETWORK)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.AUTH)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.VALIDATION)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.PROVIDER)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.UNKNOWN)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.QUOTA)
        self.assertNotEqual(BridgeErrorClass.RATE_LIMIT, BridgeErrorClass.CONTENT_FILTER)

    def test_adapter_mapping_correctness_for_all_bridge_error_classes(self) -> None:
        for source_name, source in (
            ("bridge_adapter", self.bridge_adapter),
            ("result_adapter", self.result_adapter),
        ):
            for name in ALL_BRIDGE_CLASSES:
                with self.subTest(source=source_name, name=name):
                    self.assertIn(
                        f"BridgeErrorClass::{name} => '{name}'",
                        source,
                        msg=f"{source_name} must map {name} 1:1 to failureCategory",
                    )

    def test_send_execution_failure_category_schema_parity(self) -> None:
        options = self.entity_defs["fields"]["failureCategory"]["options"]
        for name in ALL_BRIDGE_CLASSES:
            with self.subTest(name=name):
                self.assertIn(name, options)
        for name in NEW_CLASSES + (PARITY_RATE_LIMIT,):
            with self.subTest(style=name):
                self.assertIn(name, self.entity_defs["fields"]["failureCategory"]["style"])

    def test_i18n_parity_en_zh(self) -> None:
        en_opts = self.i18n_en["options"]["failureCategory"]
        zh_opts = self.i18n_zh["options"]["failureCategory"]
        for name in ALL_BRIDGE_CLASSES:
            with self.subTest(name=name):
                self.assertIn(name, en_opts)
                self.assertIn(name, zh_opts)
        self.assertEqual(set(en_opts), set(zh_opts))

    def test_retry_classification_preservation(self) -> None:
        for error_class in AUTO_RETRY_ELIGIBLE:
            with self.subTest(error_class=error_class.value, eligible=True):
                self.assertTrue(error_class.is_auto_retry_eligible())
        for error_class in AUTO_RETRY_INELIGIBLE:
            with self.subTest(error_class=error_class.value, eligible=False):
                self.assertFalse(error_class.is_auto_retry_eligible())
        self.assertIn("isAutoRetryEligible", self.php)
        self.assertIn("self::RATE_LIMIT", self.php)
        self.assertIn("self::QUOTA", self.php)
        self.assertIn("self::CONTENT_FILTER", self.php)
        # Retry eligibility helper must not schedule or own transitions.
        self.assertNotIn("SendExecutionTransitionService", self.php)
        self.assertNotIn("nextRetryAt", self.php)

    def test_failure_category_enum_includes_new_classes_without_breaking_rate_limit(self) -> None:
        values = {member.value for member in FailureCategory}
        self.assertIn(FailureCategory.RATE_LIMIT.value, values)
        self.assertIn(FailureCategory.QUOTA.value, values)
        self.assertIn(FailureCategory.CONTENT_FILTER.value, values)
        self.assertEqual(FailureCategory.RATE_LIMIT.value, "RATE_LIMIT")

    def test_no_provider_client_introduced(self) -> None:
        for path in (BRIDGE_ERROR_CLASS_PHP, BRIDGE_ADAPTER, RESULT_ADAPTER):
            text = read(path)
            self.assertNotIn("DeepSeek", text)
            self.assertNotIn("OpenAI", text)
            self.assertNotIn("EmailDeliveryProvider", text)
            self.assertNotIn("AIJob", text)
            self.assertNotIn("AIQualificationInsight", text)


if __name__ == "__main__":
    unittest.main()
