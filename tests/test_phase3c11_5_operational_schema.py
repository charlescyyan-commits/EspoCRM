"""Static and offline tests for C11.5 operational readiness reservation."""

from __future__ import annotations

import json
from pathlib import Path
import unittest
import zipfile

from chitu_connector.espocrm_sync.failure_classification import (
    FailureCategory,
    classify_failure,
    normalize_failure_category,
)
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "metadata" / "entityDefs" / "SendExecution.json"
CANONICAL_ARCHIVE = ROOT / "deployment" / "prospecting-extension-1.9.8-alpha.zip"
PROJECTION = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Services" / "EmailLifecycleProjectionService.php"
FAILURE_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "failure_classification.py"

FAILURE_CATEGORIES = ["NETWORK", "PROVIDER", "AUTH", "RATE_LIMIT", "VALIDATION", "UNKNOWN"]
SEND_EXECUTION_STATUSES = ["CREATED", "READY", "SENT", "FAILED", "CANCELLED"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class OperationalReadinessSchemaTests(unittest.TestCase):
    def test_retry_reservation_fields_exist_with_safe_defaults(self) -> None:
        fields = load_json(MODULE)["fields"]
        self.assertEqual(fields["retryCount"], {"type": "int", "required": True, "default": 0, "min": 0})
        self.assertEqual(fields["maxRetries"], {"type": "int", "required": True, "default": 0, "min": 0})
        self.assertEqual(fields["nextRetryAt"]["type"], "datetime")
        self.assertFalse(fields["nextRetryAt"]["required"])
        self.assertEqual(fields["lastError"]["type"], "text")
        self.assertFalse(fields["lastError"]["required"])

    def test_failure_category_schema_accepts_only_reserved_values(self) -> None:
        with zipfile.ZipFile(CANONICAL_ARCHIVE) as archive:
            packaged = json.loads(
                archive.read(
                    "files/custom/Espo/Modules/Prospecting/Resources/"
                    "metadata/entityDefs/SendExecution.json"
                )
            )
        self.assertEqual(packaged, load_json(MODULE))
        self.assertFalse(EXT.joinpath("Resources").exists())
        field = load_json(MODULE)["fields"]["failureCategory"]
        self.assertEqual(field["type"], "enum")
        self.assertFalse(field["required"])
        self.assertEqual(field["options"], FAILURE_CATEGORIES)
        self.assertEqual([item.value for item in FailureCategory], FAILURE_CATEGORIES)

    def test_failure_mapping_is_deterministic_and_unknown_is_safe(self) -> None:
        self.assertEqual(classify_failure(error_code="timeout"), FailureCategory.NETWORK)
        self.assertEqual(classify_failure(status_code=429), FailureCategory.RATE_LIMIT)
        self.assertEqual(classify_failure(status_code=401), FailureCategory.AUTH)
        self.assertEqual(classify_failure(status_code=403), FailureCategory.AUTH)
        self.assertEqual(classify_failure(error_code="invalid_payload"), FailureCategory.VALIDATION)
        self.assertEqual(normalize_failure_category("not-a-category"), FailureCategory.UNKNOWN)
        self.assertEqual(normalize_failure_category(None), FailureCategory.UNKNOWN)

    def test_status_and_idempotency_reservations_remain_unchanged(self) -> None:
        definition = load_json(MODULE)
        self.assertEqual(definition["fields"]["status"]["options"], SEND_EXECUTION_STATUSES)
        self.assertNotIn("RETRYING", definition["fields"]["status"]["options"])
        self.assertEqual(definition["indexes"]["sendRequestId"], {"type": "unique", "columns": ["sendRequestId", "deleteId"]})
        self.assertIn("'FAILED' => 'FAILED'", PROJECTION.read_text(encoding="utf-8"))

    def test_no_retry_execution_or_external_side_effect_dependencies(self) -> None:
        source = FAILURE_SOURCE.read_text(encoding="utf-8")
        for forbidden_import in (
            "real_client",
            "send_execution",
            "send_provider",
            "human_approval",
            "reply_tracking",
            "requests",
            "subprocess",
        ):
            self.assertNotIn(f"import {forbidden_import}", source)
            self.assertNotIn(f"from chitu_connector.espocrm_sync.{forbidden_import}", source)

    def test_c10_contract_and_tests_remain_frozen(self) -> None:
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
