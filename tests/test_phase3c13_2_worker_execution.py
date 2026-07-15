"""Controlled offline execution tests for the C13.2 worker engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.provider_contract import (
    FakeProviderAdapter,
    FakeProviderMode,
    ProviderAdapter,
    ProviderErrorCategory,
    ProviderStatus,
    SendResult,
    SendResultStatus,
)
from chitu_connector.espocrm_sync.queue_contract import InMemorySendExecutionQueue, QueueItemState
from chitu_connector.espocrm_sync.worker_execution import (
    InMemorySendExecutionWorkStore,
    SendExecutionWorkItem,
    SendExecutionWorker,
    WorkExecutionStatus,
)
from tests.test_phase3c11_2_persistence_entities import C10_FROZEN_HASHES, C10_TEST_HASHES, sha256


ROOT = Path(__file__).resolve().parents[1]
WORKER_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "worker_execution.py"
NOW = datetime(2026, 7, 14, 17, 0, tzinfo=timezone.utc)


def execution(status: WorkExecutionStatus = WorkExecutionStatus.READY) -> SendExecutionWorkItem:
    return SendExecutionWorkItem(
        send_execution_id="send-execution-001",
        request_id="send-request-001",
        status=status,
        recipient="fixture-recipient@example.test",
        subject="Fixture subject",
        body="Fixture body",
        draft_hash="d" * 64,
        created_at=NOW,
    )


class RaisingProvider:
    def send(self, request: object) -> SendResult:
        raise RuntimeError("fixture exception")

    def get_status(self, provider_message_id: str) -> ProviderStatus:
        return ProviderStatus.UNKNOWN


class WorkerExecutionTests(unittest.TestCase):
    def make_worker(
        self,
        *,
        status: WorkExecutionStatus = WorkExecutionStatus.READY,
        provider: ProviderAdapter | None = None,
    ) -> tuple[SendExecutionWorker, InMemorySendExecutionQueue, InMemorySendExecutionWorkStore, object]:
        queue = InMemorySendExecutionQueue()
        item = queue.enqueue("send-execution-001", NOW)
        store = InMemorySendExecutionWorkStore((execution(status),))
        worker = SendExecutionWorker(queue, store, "worker-001", provider)
        return worker, queue, store, item

    def test_ready_execution_with_fake_success_sends_once_and_completes(self) -> None:
        fake = FakeProviderAdapter()
        worker, queue, store, item = self.make_worker(provider=fake)

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(fake.send_call_count, 1)
        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.SENT)
        self.assertEqual(outcome.execution and outcome.execution.provider_message_id, "fake:send-execution-001:send-request-001")
        self.assertEqual(outcome.queue_item and outcome.queue_item.state, QueueItemState.COMPLETED)
        self.assertEqual(store.get("send-execution-001").status, WorkExecutionStatus.SENT)  # type: ignore[union-attr]
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.COMPLETED)  # type: ignore[union-attr]

    def test_provider_failure_marks_execution_and_queue_failed(self) -> None:
        fake = FakeProviderAdapter(mode=FakeProviderMode.FAILURE, failure_category=ProviderErrorCategory.AUTH_ERROR)
        worker, queue, store, item = self.make_worker(provider=fake)

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(fake.send_call_count, 1)
        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.FAILED)
        self.assertEqual(outcome.execution and outcome.execution.failure_category, FailureCategory.AUTH)
        self.assertEqual(outcome.queue_item and outcome.queue_item.state, QueueItemState.FAILED)
        self.assertEqual(outcome.queue_item and outcome.queue_item.failure_category, FailureCategory.AUTH)
        self.assertEqual(store.get("send-execution-001").status, WorkExecutionStatus.FAILED)  # type: ignore[union-attr]
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.FAILED)  # type: ignore[union-attr]

    def test_invalid_execution_state_fails_queue_without_provider_call(self) -> None:
        fake = FakeProviderAdapter()
        worker, queue, store, item = self.make_worker(status=WorkExecutionStatus.CREATED, provider=fake)

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(fake.send_call_count, 0)
        self.assertEqual(outcome.reason_code, "EXECUTION_NOT_READY")
        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.CREATED)
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.FAILED)  # type: ignore[union-attr]

    def test_duplicate_worker_execution_does_not_recall_provider(self) -> None:
        fake = FakeProviderAdapter()
        worker, _, _, item = self.make_worker(provider=fake)

        first = worker.process(item, NOW + timedelta(minutes=1))
        repeated = worker.process(item, NOW + timedelta(minutes=2))

        self.assertEqual(first.queue_item and first.queue_item.state, QueueItemState.COMPLETED)
        self.assertEqual(repeated.reason_code, "QUEUE_ITEM_NOT_QUEUED")
        self.assertEqual(fake.send_call_count, 1)

    def test_provider_exception_safely_fails_without_stuck_claim(self) -> None:
        worker, queue, store, item = self.make_worker(provider=RaisingProvider())

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.FAILED)
        self.assertEqual(outcome.execution and outcome.execution.failure_category, FailureCategory.UNKNOWN)
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.FAILED)  # type: ignore[union-attr]
        self.assertEqual(store.get("send-execution-001").status, WorkExecutionStatus.FAILED)  # type: ignore[union-attr]

    def test_default_fake_provider_has_zero_external_http_and_c10_is_frozen(self) -> None:
        worker, _, _, item = self.make_worker()

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.SENT)
        source = WORKER_SOURCE.read_text(encoding="utf-8")
        for forbidden in ("brevo_provider", "brevo_http", "requests", "smtplib", "urllib", "logging", "print("):
            self.assertNotIn(forbidden, source)
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
