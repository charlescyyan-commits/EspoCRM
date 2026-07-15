"""Offline reliability acceptance tests for C13 queue, worker, and provider boundaries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from threading import Barrier, Thread
import unittest

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.provider_contract import (
    FakeProviderAdapter,
    FakeProviderMode,
    ProviderErrorCategory,
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
SEND_EXECUTION_SCHEMA = (
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
WORKER_SOURCE = ROOT / "chitu-connector" / "chitu_connector" / "espocrm_sync" / "worker_execution.py"
NOW = datetime(2026, 7, 14, 19, 30, tzinfo=timezone.utc)


def execution() -> SendExecutionWorkItem:
    return SendExecutionWorkItem(
        send_execution_id="send-execution-reliability-001",
        request_id="send-request-reliability-001",
        status=WorkExecutionStatus.READY,
        recipient="fixture-recipient@example.test",
        subject="Reliability fixture",
        body="No external send occurs.",
        draft_hash="a" * 64,
        created_at=NOW,
    )


def worker_fixture(
    *,
    provider: FakeProviderAdapter | None = None,
) -> tuple[SendExecutionWorker, InMemorySendExecutionQueue, InMemorySendExecutionWorkStore, object, FakeProviderAdapter]:
    queue = InMemorySendExecutionQueue()
    item = queue.enqueue("send-execution-reliability-001", NOW)
    store = InMemorySendExecutionWorkStore((execution(),))
    fake = provider or FakeProviderAdapter()
    return SendExecutionWorker(queue, store, "worker-a", fake), queue, store, item, fake


class LoadFailureStore:
    """Deterministic post-claim crash surrogate: loading always raises."""

    def get(self, send_execution_id: str) -> SendExecutionWorkItem | None:
        raise RuntimeError("fixture load interruption")

    def mark_sent(
        self,
        send_execution_id: str,
        provider_message_id: str,
        completed_at: datetime,
    ) -> SendExecutionWorkItem:
        raise AssertionError("must not be reached")

    def mark_failed(
        self,
        send_execution_id: str,
        failure_category: FailureCategory,
        completed_at: datetime,
    ) -> SendExecutionWorkItem:
        raise AssertionError("must not be reached")


class ReliabilityAcceptanceTests(unittest.TestCase):
    def test_duplicate_execution_keeps_sent_and_calls_provider_once(self) -> None:
        worker, queue, store, item, fake = worker_fixture()

        first = worker.process(item, NOW + timedelta(minutes=1))
        second = worker.process(item, NOW + timedelta(minutes=2))

        self.assertEqual(first.queue_item and first.queue_item.state, QueueItemState.COMPLETED)
        self.assertEqual(second.reason_code, "QUEUE_ITEM_NOT_QUEUED")
        self.assertEqual(fake.send_call_count, 1)
        self.assertEqual(store.get("send-execution-reliability-001").status, WorkExecutionStatus.SENT)  # type: ignore[union-attr]
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.COMPLETED)  # type: ignore[union-attr]

    def test_concurrent_workers_allow_only_one_claim_and_one_provider_call(self) -> None:
        queue = InMemorySendExecutionQueue()
        item = queue.enqueue("send-execution-reliability-001", NOW)
        store = InMemorySendExecutionWorkStore((execution(),))
        fake = FakeProviderAdapter()
        workers = (
            SendExecutionWorker(queue, store, "worker-a", fake),
            SendExecutionWorker(queue, store, "worker-b", fake),
        )
        barrier = Barrier(3)
        outcomes = []

        def run(worker: SendExecutionWorker) -> None:
            barrier.wait()
            outcomes.append(worker.process(item, NOW + timedelta(minutes=1)))

        threads = tuple(Thread(target=run, args=(worker,)) for worker in workers)
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(sum(outcome.reason_code == "QUEUE_ITEM_NOT_QUEUED" for outcome in outcomes), 1)
        self.assertEqual(fake.send_call_count, 1)
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.COMPLETED)  # type: ignore[union-attr]

    def test_provider_failure_matrix_maps_to_reserved_failure_categories(self) -> None:
        expectations = {
            ProviderErrorCategory.AUTH_ERROR: FailureCategory.AUTH,
            ProviderErrorCategory.RATE_LIMIT: FailureCategory.RATE_LIMIT,
            ProviderErrorCategory.NETWORK_ERROR: FailureCategory.NETWORK,
            ProviderErrorCategory.VALIDATION_ERROR: FailureCategory.VALIDATION,
            ProviderErrorCategory.PROVIDER_ERROR: FailureCategory.PROVIDER,
            ProviderErrorCategory.UNKNOWN_ERROR: FailureCategory.UNKNOWN,
        }

        for provider_category, expected_failure_category in expectations.items():
            with self.subTest(provider_category=provider_category):
                fake = FakeProviderAdapter(
                    mode=FakeProviderMode.FAILURE,
                    failure_category=provider_category,
                )
                worker, queue, store, item, _ = worker_fixture(provider=fake)

                outcome = worker.process(item, NOW + timedelta(minutes=1))

                self.assertEqual(fake.send_call_count, 1)
                self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.FAILED)
                self.assertEqual(outcome.execution and outcome.execution.failure_category, expected_failure_category)
                self.assertEqual(outcome.queue_item and outcome.queue_item.state, QueueItemState.FAILED)
                self.assertEqual(outcome.queue_item and outcome.queue_item.failure_category, expected_failure_category)
                self.assertEqual(store.get("send-execution-reliability-001").status, WorkExecutionStatus.FAILED)  # type: ignore[union-attr]
                self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.FAILED)  # type: ignore[union-attr]

    def test_retry_reservation_fields_are_preserved_without_retry_state(self) -> None:
        fields = json.loads(SEND_EXECUTION_SCHEMA.read_text(encoding="utf-8"))["fields"]

        self.assertEqual(fields["retryCount"]["default"], 0)
        self.assertEqual(fields["maxRetries"]["default"], 0)
        self.assertEqual(fields["nextRetryAt"]["type"], "datetime")
        self.assertEqual(fields["lastError"]["type"], "text")
        self.assertEqual(
            fields["failureCategory"]["options"],
            ["NETWORK", "PROVIDER", "AUTH", "RATE_LIMIT", "VALIDATION", "UNKNOWN"],
        )
        self.assertNotIn("RETRYING", fields["status"]["options"])

    def test_terminal_state_transitions_are_blocked(self) -> None:
        worker, queue, store, item, _ = worker_fixture()

        worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(queue.claim(item.queue_item_id, "worker-b", NOW + timedelta(minutes=2)).claimed, False)
        with self.assertRaises(ValueError):
            queue.complete(item.queue_item_id, "worker-a", NOW + timedelta(minutes=2))
        with self.assertRaises(ValueError):
            store.mark_failed(
                "send-execution-reliability-001",
                FailureCategory.UNKNOWN,
                NOW + timedelta(minutes=2),
            )
        self.assertEqual(store.get("send-execution-reliability-001").status, WorkExecutionStatus.SENT)  # type: ignore[union-attr]
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.COMPLETED)  # type: ignore[union-attr]

    def test_post_claim_exception_is_contained_without_stuck_claim(self) -> None:
        queue = InMemorySendExecutionQueue()
        item = queue.enqueue("send-execution-reliability-001", NOW)
        worker = SendExecutionWorker(queue, LoadFailureStore(), "worker-a", FakeProviderAdapter())

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(outcome.reason_code, "EXECUTION_LOAD_FAILED")
        self.assertEqual(outcome.queue_item and outcome.queue_item.state, QueueItemState.FAILED)
        self.assertEqual(outcome.queue_item and outcome.queue_item.failure_category, FailureCategory.UNKNOWN)
        self.assertEqual(queue.get(item.queue_item_id).state, QueueItemState.FAILED)  # type: ignore[union-attr]

    def test_default_fake_provider_has_zero_external_requests_and_c10_is_frozen(self) -> None:
        worker, queue, _, item, fake = worker_fixture()

        outcome = worker.process(item, NOW + timedelta(minutes=1))

        self.assertEqual(outcome.execution and outcome.execution.status, WorkExecutionStatus.SENT)
        self.assertEqual(fake.external_request_count, 0)
        self.assertEqual(queue.external_request_count, 0)
        source = WORKER_SOURCE.read_text(encoding="utf-8")
        for forbidden in (
            "brevo_provider",
            "brevo_http",
            "import requests",
            "import smtplib",
            "import urllib",
            "import schedule",
            "from schedule",
            "import celery",
            "from celery",
        ):
            self.assertNotIn(forbidden, source)
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
