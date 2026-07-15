"""Explicit, operator-owned bridge invocation for C14.3.1B-4.

This is a thin composition layer.  It performs no CRM write, provider call,
Worker call, scheduling, retry, or network access.  It only validates an
explicit execution identity, delegates the existing B-2 checks, and submits a
safe B-1 request to the existing C13 in-memory Queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Mapping

from chitu_connector.espocrm_sync.crm_send_execution_bridge_adapter import (
    ApprovedDeliveryPayload,
    BridgeSubmissionOutcome,
    BridgeSubmissionStatus,
    CrmSendExecutionBridgeAdapter,
    CrmSendExecutionRepository,
    CrmSendExecutionStatus,
)
from chitu_connector.espocrm_sync.payload_snapshot import PayloadSnapshotStore
from chitu_connector.espocrm_sync.queue_contract import SendExecutionQueue
from chitu_connector.espocrm_sync.send_execution_bridge import (
    InMemorySendExecutionBridgeFixture,
    SendExecutionBridgeRequest,
    SendExecutionBridgeResult,
    SendExecutionBridgeReceipt,
    generate_idempotency_key,
)


@dataclass(frozen=True, slots=True)
class ExplicitInvocationOutcome:
    """Safe command result.  It intentionally has no raw payload fields."""

    status: BridgeSubmissionStatus
    execution_id: str
    reason_code: str | None
    idempotency_key: str | None
    retryable_submission_failure: bool


class SqliteApprovedDeliveryPayloadSource:
    """Read B-3 snapshots through the B-2 approved-payload protocol.

    B-3 is keyed by ``execution_id`` while B-2 asks for ``draft_id``.  The
    explicit acceptance composition supplies the narrow, read-only mapping;
    this is not a CRM query, write, or production discovery mechanism.
    """

    def __init__(
        self,
        snapshot_store: PayloadSnapshotStore,
        execution_id_by_draft_id: Mapping[str, str],
    ) -> None:
        self._snapshot_store = snapshot_store
        self._execution_id_by_draft_id = {
            _require_identifier("draft_id", draft_id): _require_identifier("execution_id", execution_id)
            for draft_id, execution_id in execution_id_by_draft_id.items()
        }

    def get_approved_payload(self, draft_id: str) -> ApprovedDeliveryPayload | None:
        execution_id = self._execution_id_by_draft_id.get(draft_id)
        if execution_id is None:
            return None
        snapshot = self._snapshot_store.get(execution_id)
        if snapshot is None:
            return None
        return ApprovedDeliveryPayload(
            draft_id=draft_id,
            content_hash=snapshot.content_hash,
            recipient=snapshot.recipient,
            subject=snapshot.subject,
            body=snapshot.body,
            campaign_reference=snapshot.campaign_reference,
            generated_at=snapshot.payload_created_at,
        )


class QueueSubmissionBridgeAdapter:
    """B-1 adapter that creates exactly one existing C13 QueueItem per process.

    The adapter is intentionally in-memory because C13 Queue is in-memory.
    It validates the B-1 deterministic idempotency key before touching Queue.
    A Queue exception is allowed to reach B-2, which returns the existing
    retryable-safe ``FAILED_SUBMISSION`` outcome without CRM mutation.
    """

    def __init__(self, queue: SendExecutionQueue) -> None:
        self._queue = queue
        self._bridge = InMemorySendExecutionBridgeFixture()
        self._lock = RLock()

    def enqueue(self, request: SendExecutionBridgeRequest) -> SendExecutionBridgeReceipt:
        expected_key = generate_idempotency_key(request.execution_id)
        if request.idempotency_key != expected_key:
            raise ValueError("IDEMPOTENCY_KEY_MISMATCH")

        with self._lock:
            existing_request = self._bridge.request_for(request.execution_id)
            if existing_request is not None:
                return self._bridge.enqueue(request)

            queue_item_id = "queue:" + request.execution_id
            existing_queue_item = self._queue.get(queue_item_id)
            if existing_queue_item is not None:
                self._bridge.enqueue(request)
                return SendExecutionBridgeReceipt(
                    execution_id=request.execution_id,
                    idempotency_key=request.idempotency_key,
                    duplicate=True,
                )

            self._queue.enqueue(request.execution_id, request.created_at)
            return self._bridge.enqueue(request)

    def record_result(self, result: SendExecutionBridgeResult) -> SendExecutionBridgeResult:
        """Preserve the B-1 result contract without introducing a result adapter."""

        return self._bridge.record_result(result)


class ExplicitBridgeInvocationService:
    """Validate an explicit operator/test request and invoke B-2 exactly once."""

    def __init__(
        self,
        crm_repository: CrmSendExecutionRepository,
        snapshot_store: PayloadSnapshotStore,
        adapter: CrmSendExecutionBridgeAdapter,
    ) -> None:
        self._crm_repository = crm_repository
        self._snapshot_store = snapshot_store
        self._adapter = adapter

    def submit(self, execution_id: str) -> ExplicitInvocationOutcome:
        """Submit only a READY execution with a durable, verified snapshot."""

        if not isinstance(execution_id, str) or not execution_id.strip():
            return _outcome(BridgeSubmissionStatus.BLOCKED, "", "INVALID_SEND_EXECUTION_ID")
        normalized_execution_id = execution_id.strip()

        try:
            execution = self._crm_repository.get_send_execution(normalized_execution_id)
        except Exception:
            return _outcome(
                BridgeSubmissionStatus.FAILED_SUBMISSION,
                normalized_execution_id,
                "CRM_REPOSITORY_UNAVAILABLE",
            )
        if execution is None:
            return _outcome(BridgeSubmissionStatus.BLOCKED, normalized_execution_id, "SEND_EXECUTION_NOT_FOUND")
        if execution.status is not CrmSendExecutionStatus.READY:
            return _outcome(BridgeSubmissionStatus.BLOCKED, execution.id, "SEND_EXECUTION_NOT_READY")

        try:
            snapshot = self._snapshot_store.get(execution.id)
        except Exception:
            return _outcome(
                BridgeSubmissionStatus.FAILED_SUBMISSION,
                execution.id,
                "PAYLOAD_SNAPSHOT_UNAVAILABLE",
            )
        if snapshot is None:
            return _outcome(BridgeSubmissionStatus.BLOCKED, execution.id, "PAYLOAD_SNAPSHOT_NOT_FOUND")

        bridge_outcome = self._adapter.submit(execution.id)
        idempotency_key = bridge_outcome.request.idempotency_key if bridge_outcome.request is not None else None
        if idempotency_key is not None and idempotency_key != generate_idempotency_key(execution.id):
            return _outcome(
                BridgeSubmissionStatus.FAILED_SUBMISSION,
                execution.id,
                "IDEMPOTENCY_KEY_MISMATCH",
            )
        return ExplicitInvocationOutcome(
            status=bridge_outcome.status,
            execution_id=bridge_outcome.execution_id,
            reason_code=bridge_outcome.reason_code,
            idempotency_key=idempotency_key,
            retryable_submission_failure=bridge_outcome.status is BridgeSubmissionStatus.FAILED_SUBMISSION,
        )


def _outcome(
    status: BridgeSubmissionStatus,
    execution_id: str,
    reason_code: str,
) -> ExplicitInvocationOutcome:
    return ExplicitInvocationOutcome(
        status=status,
        execution_id=execution_id,
        reason_code=reason_code,
        idempotency_key=None,
        retryable_submission_failure=status is BridgeSubmissionStatus.FAILED_SUBMISSION,
    )


def _require_identifier(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("INVALID_" + field_name.upper())
    return value.strip()
