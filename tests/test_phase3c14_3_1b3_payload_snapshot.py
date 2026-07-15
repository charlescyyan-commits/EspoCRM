"""C14.3.1B-3 tests for the durable connector payload snapshot boundary."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from chitu_connector.espocrm_sync.payload_snapshot import (
    PayloadSnapshot,
    PayloadSnapshotConflictError,
    PayloadSnapshotInput,
    PayloadSnapshotValidationError,
    SqlitePayloadSnapshotStore,
)


NOW = datetime(2026, 7, 14, 14, 30, tzinfo=timezone.utc)
CONTENT_HASH = "c" * 64


def snapshot_input(
    *,
    execution_id: str = "execution-payload-001",
    body: str = "A durable, approved connector payload.",
) -> PayloadSnapshotInput:
    return PayloadSnapshotInput(
        execution_id=execution_id,
        content_hash=CONTENT_HASH,
        recipient="Approved.Recipient@Example.Invalid",
        subject="Approved payload boundary",
        body=body,
        campaign_reference="campaign-payload-001",
        payload_created_at=NOW,
    )


class PayloadSnapshotTests(unittest.TestCase):
    def test_same_input_generates_same_deterministic_hash_and_persisted_snapshot(self) -> None:
        first = PayloadSnapshot.create(snapshot_input())
        second = PayloadSnapshot.create(snapshot_input())

        self.assertEqual(first.snapshot_hash, second.snapshot_hash)
        self.assertEqual(first.snapshot_id, second.snapshot_id)
        self.assertEqual(first.recipient_hash, second.recipient_hash)

        with tempfile.TemporaryDirectory() as directory:
            store = SqlitePayloadSnapshotStore(Path(directory) / "payloads.sqlite")
            saved = store.save_if_absent(snapshot_input())
            duplicate = store.save_if_absent(snapshot_input())

        self.assertEqual(saved, first)
        self.assertEqual(duplicate, first)

    def test_different_content_generates_different_snapshot_hash(self) -> None:
        original = PayloadSnapshot.create(snapshot_input())
        changed = PayloadSnapshot.create(snapshot_input(body="Changed approved payload."))

        self.assertNotEqual(original.snapshot_hash, changed.snapshot_hash)
        self.assertNotEqual(original.snapshot_id, changed.snapshot_id)

    def test_snapshot_is_immutable_and_existing_execution_cannot_be_replaced(self) -> None:
        snapshot = PayloadSnapshot.create(snapshot_input())
        with self.assertRaises(FrozenInstanceError):
            snapshot.subject = "replacement"  # type: ignore[misc]

        with tempfile.TemporaryDirectory() as directory:
            store = SqlitePayloadSnapshotStore(Path(directory) / "payloads.sqlite")
            saved = store.save_if_absent(snapshot_input())
            with self.assertRaises(PayloadSnapshotConflictError) as raised:
                store.save_if_absent(snapshot_input(body="Changed approved payload."))

        self.assertEqual(str(raised.exception), "PAYLOAD_IMMUTABILITY_CONFLICT")
        self.assertEqual(saved.body, "A durable, approved connector payload.")

    def test_missing_required_fields_are_rejected(self) -> None:
        for field_name, invalid_value in (
            ("execution_id", ""),
            ("content_hash", "not-a-sha256"),
            ("recipient", ""),
            ("subject", ""),
            ("body", ""),
            ("campaign_reference", ""),
            ("payload_created_at", datetime(2026, 7, 14, 14, 30)),
        ):
            with self.subTest(field_name=field_name):
                values = {
                    "execution_id": "execution-payload-001",
                    "content_hash": CONTENT_HASH,
                    "recipient": "approved@example.invalid",
                    "subject": "Approved payload boundary",
                    "body": "A durable approved connector payload.",
                    "campaign_reference": "campaign-payload-001",
                    "payload_created_at": NOW,
                }
                values[field_name] = invalid_value
                with self.assertRaises(PayloadSnapshotValidationError):
                    PayloadSnapshotInput(**values)

    def test_secret_pattern_scan_rejects_credentials_before_persistence(self) -> None:
        with self.assertRaises(PayloadSnapshotValidationError) as raised:
            snapshot_input(body="Authorization: Bearer abcdefghijklmnop")

        self.assertEqual(str(raised.exception), "PAYLOAD_CONTAINS_SECRET")

        with tempfile.TemporaryDirectory() as directory:
            store = SqlitePayloadSnapshotStore(Path(directory) / "payloads.sqlite")
            self.assertIsNone(store.get("execution-payload-001"))

    def test_snapshot_survives_new_store_instance_and_self_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payloads.sqlite"
            initial_store = SqlitePayloadSnapshotStore(path)
            saved = initial_store.save_if_absent(snapshot_input())

            reopened_store = SqlitePayloadSnapshotStore(path)
            reopened = reopened_store.get("execution-payload-001")

        self.assertEqual(reopened, saved)
        self.assertEqual(reopened.body, "A durable, approved connector payload.")

    def test_module_has_no_crm_worker_queue_provider_or_transport_import(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "payload_snapshot.py"
        ).read_text(encoding="utf-8")
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )

        for forbidden in (
            "crm_send_execution_bridge_adapter",
            "queue_contract",
            "worker_execution",
            "provider_contract",
            "brevo",
            "urllib",
            "requests",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, imports)


if __name__ == "__main__":
    unittest.main()
