"""C14.3.1B-4 tests for explicit, queue-backed bridge invocation."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from chitu_connector.espocrm_sync.crm_send_execution_bridge_adapter import (
    BridgeSubmissionStatus,
    CrmDraftApprovalRecord,
    CrmDraftApprovalStatus,
    CrmSendExecutionBridgeAdapter,
    CrmSendExecutionRecord,
    CrmSendExecutionStatus,
    InMemoryCrmSendExecutionRepository,
)
from chitu_connector.espocrm_sync.explicit_bridge_invocation import (
    ExplicitBridgeInvocationService,
    QueueSubmissionBridgeAdapter,
    SqliteApprovedDeliveryPayloadSource,
)
from chitu_connector.espocrm_sync.payload_snapshot import PayloadSnapshotInput, SqlitePayloadSnapshotStore
from chitu_connector.espocrm_sync.queue_contract import InMemorySendExecutionQueue
from chitu_connector.espocrm_sync.send_execution_bridge import generate_idempotency_key


NOW = datetime(2026, 7, 14, 15, 30, tzinfo=timezone.utc)
CONTENT_HASH = "d" * 64


def approval() -> CrmDraftApprovalRecord:
    return CrmDraftApprovalRecord(
        id="approval-invocation-001",
        draft_id="draft-invocation-001",
        status=CrmDraftApprovalStatus.APPROVED,
        content_hash=CONTENT_HASH,
    )


def execution() -> CrmSendExecutionRecord:
    return CrmSendExecutionRecord(
        id="execution-invocation-001",
        send_request_id="request-invocation-001",
        status=CrmSendExecutionStatus.READY,
        draft_approval_id="approval-invocation-001",
        created_at=NOW,
    )


def snapshot_input() -> PayloadSnapshotInput:
    return PayloadSnapshotInput(
        execution_id="execution-invocation-001",
        content_hash=CONTENT_HASH,
        recipient="invocation@example.invalid",
        subject="Explicit invocation boundary",
        body="This is an acceptance-only durable payload.",
        campaign_reference="campaign-invocation-001",
        payload_created_at=NOW,
    )


class UnavailableQueue:
    def get(self, queue_item_id: str) -> object:
        raise RuntimeError("queue unavailable")

    def enqueue(self, send_execution_id: str, created_at: datetime) -> object:
        raise RuntimeError("queue unavailable")


class ExplicitBridgeInvocationTests(unittest.TestCase):
    def _service(
        self,
        *,
        crm_execution: CrmSendExecutionRecord | None = None,
        crm_approval: CrmDraftApprovalRecord | None = None,
        persist_snapshot: bool = True,
        queue: object | None = None,
    ) -> tuple[ExplicitBridgeInvocationService, SqlitePayloadSnapshotStore, object, CrmSendExecutionRecord]:
        current_execution = crm_execution or execution()
        current_approval = crm_approval or approval()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        store = SqlitePayloadSnapshotStore(Path(directory.name) / "payloads.sqlite")
        if persist_snapshot:
            store.save_if_absent(snapshot_input())
        repository = InMemoryCrmSendExecutionRepository(
            executions=(current_execution,),
            approvals=(current_approval,),
        )
        payload_source = SqliteApprovedDeliveryPayloadSource(
            store,
            {current_approval.draft_id: current_execution.id},
        )
        selected_queue = queue if queue is not None else InMemorySendExecutionQueue()
        queue_bridge = QueueSubmissionBridgeAdapter(selected_queue)  # type: ignore[arg-type]
        adapter = CrmSendExecutionBridgeAdapter(repository, payload_source, queue_bridge)
        return ExplicitBridgeInvocationService(repository, store, adapter), store, selected_queue, current_execution

    def test_valid_execution_submits_once_to_c13_queue(self) -> None:
        service, _, queue, _ = self._service()

        outcome = service.submit("execution-invocation-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.SUBMITTED)
        self.assertEqual(outcome.idempotency_key, generate_idempotency_key("execution-invocation-001"))
        self.assertFalse(outcome.retryable_submission_failure)
        self.assertEqual(queue.item_count, 1)
        self.assertEqual(queue.get("queue:execution-invocation-001").send_execution_id, "execution-invocation-001")

    def test_duplicate_submit_returns_duplicate_without_second_queue_item(self) -> None:
        service, _, queue, _ = self._service()

        first = service.submit("execution-invocation-001")
        duplicate = service.submit("execution-invocation-001")

        self.assertEqual(first.status, BridgeSubmissionStatus.SUBMITTED)
        self.assertEqual(duplicate.status, BridgeSubmissionStatus.DUPLICATE)
        self.assertEqual(duplicate.idempotency_key, first.idempotency_key)
        self.assertEqual(queue.item_count, 1)

    def test_missing_snapshot_is_blocked_before_bridge_or_queue_submission(self) -> None:
        service, _, queue, _ = self._service(persist_snapshot=False)

        outcome = service.submit("execution-invocation-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "PAYLOAD_SNAPSHOT_NOT_FOUND")
        self.assertEqual(queue.item_count, 0)

    def test_invalid_execution_state_is_blocked_before_queue_submission(self) -> None:
        service, _, queue, current_execution = self._service(
            crm_execution=replace(execution(), status=CrmSendExecutionStatus.CREATED)
        )

        outcome = service.submit("execution-invocation-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "SEND_EXECUTION_NOT_READY")
        self.assertEqual(current_execution.status, CrmSendExecutionStatus.CREATED)
        self.assertEqual(queue.item_count, 0)

    def test_queue_unavailable_returns_retryable_failure_without_crm_or_snapshot_corruption(self) -> None:
        crm_execution = execution()
        service, store, _, original_execution = self._service(crm_execution=crm_execution, queue=UnavailableQueue())

        outcome = service.submit("execution-invocation-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.FAILED_SUBMISSION)
        self.assertEqual(outcome.reason_code, "BRIDGE_SUBMISSION_UNAVAILABLE")
        self.assertTrue(outcome.retryable_submission_failure)
        self.assertEqual(original_execution.status, CrmSendExecutionStatus.READY)
        self.assertIsNotNone(store.get("execution-invocation-001"))

    def test_hash_mismatch_is_blocked_by_existing_b2_validation(self) -> None:
        mismatched_approval = replace(approval(), content_hash="e" * 64)
        service, _, queue, _ = self._service(crm_approval=mismatched_approval)

        outcome = service.submit("execution-invocation-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "APPROVED_PAYLOAD_HASH_MISMATCH")
        self.assertEqual(queue.item_count, 0)

    def test_source_has_no_worker_provider_brevo_or_transport_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "explicit_bridge_invocation.py"
        ).read_text(encoding="utf-8")
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )

        for forbidden in (
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
