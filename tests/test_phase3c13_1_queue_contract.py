"""Offline tests for the C13.1 SendExecution queue contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.queue_contract import InMemorySendExecutionQueue, QueueItemState
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
QUEUE_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "queue_contract.py"
NOW = datetime(2026, 7, 14, 16, 0, tzinfo=timezone.utc)


class QueueContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = InMemorySendExecutionQueue()

    def test_enqueue_creates_queue_item_for_send_execution(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)

        self.assertEqual(item.queue_item_id, "queue:send-execution-001")
        self.assertEqual(item.state, QueueItemState.QUEUED)
        self.assertIsNone(item.claimed_at)
        self.assertIsNone(item.completed_at)

    def test_duplicate_enqueue_returns_same_identity_without_amplification(self) -> None:
        first = self.queue.enqueue("send-execution-001", NOW)
        repeated = self.queue.enqueue("send-execution-001", NOW + timedelta(minutes=1))

        self.assertEqual(first, repeated)
        self.assertEqual(self.queue.item_count, 1)

    def test_claim_moves_queued_item_to_claimed(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)

        result = self.queue.claim(item.queue_item_id, "worker-001", NOW + timedelta(minutes=1))

        self.assertTrue(result.claimed)
        self.assertEqual(result.item and result.item.state, QueueItemState.CLAIMED)
        self.assertEqual(result.item and result.item.worker_id, "worker-001")

    def test_double_claim_is_safely_rejected(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)
        self.queue.claim(item.queue_item_id, "worker-001", NOW + timedelta(minutes=1))

        result = self.queue.claim(item.queue_item_id, "worker-002", NOW + timedelta(minutes=2))

        self.assertFalse(result.claimed)
        self.assertEqual(result.reason_code, "QUEUE_ITEM_NOT_QUEUED")
        self.assertEqual(result.item and result.item.worker_id, "worker-001")

    def test_complete_moves_owned_claim_to_terminal_completed(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)
        self.queue.claim(item.queue_item_id, "worker-001", NOW + timedelta(minutes=1))

        completed = self.queue.complete(item.queue_item_id, "worker-001", NOW + timedelta(minutes=2))

        self.assertEqual(completed.state, QueueItemState.COMPLETED)
        self.assertEqual(completed.completed_at, NOW + timedelta(minutes=2))

    def test_invalid_terminal_transition_is_blocked(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)

        with self.assertRaisesRegex(ValueError, "QUEUED -> terminal"):
            self.queue.complete(item.queue_item_id, "worker-001", NOW + timedelta(minutes=1))

    def test_fail_records_c11_failure_category_without_retry(self) -> None:
        item = self.queue.enqueue("send-execution-001", NOW)
        self.queue.claim(item.queue_item_id, "worker-001", NOW + timedelta(minutes=1))

        failed = self.queue.fail(item.queue_item_id, "worker-001", "NETWORK", NOW + timedelta(minutes=2))

        self.assertEqual(failed.state, QueueItemState.FAILED)
        self.assertEqual(failed.failure_category, FailureCategory.NETWORK)
        with self.assertRaisesRegex(ValueError, "FAILED -> terminal"):
            self.queue.complete(item.queue_item_id, "worker-001", NOW + timedelta(minutes=3))

    def test_queue_has_zero_external_requests_and_c10_is_frozen(self) -> None:
        self.assertEqual(self.queue.external_request_count, 0)
        source = QUEUE_SOURCE.read_text(encoding="utf-8")
        for forbidden_import in ("provider_contract", "brevo_provider", "brevo_http", "requests", "redis", "celery", "subprocess"):
            self.assertNotIn(forbidden_import, source)
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
