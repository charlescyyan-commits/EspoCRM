"""Controlled, single-item execution engine for the C13 queue contract.

This is not a daemon or scheduler. A caller explicitly invokes process for one
already-enqueued item. The default provider is the C12 fake adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.failure_classification import FailureCategory
from chitu_connector.espocrm_sync.provider_contract import (
    FakeProviderAdapter,
    ProviderAdapter,
    ProviderErrorCategory,
    SendRequest,
    SendResult,
    SendResultStatus,
    map_error_to_failure_category,
)
from chitu_connector.espocrm_sync.queue_contract import QueueItem, QueueItemState, SendExecutionQueue


class WorkExecutionStatus(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class SendExecutionWorkItem:
    """Offline worker view of a SendExecution plus approved delivery content."""

    send_execution_id: str
    request_id: str
    status: WorkExecutionStatus
    recipient: str
    subject: str
    body: str
    draft_hash: str
    created_at: datetime
    provider_message_id: str | None = None
    completed_at: datetime | None = None
    failure_category: FailureCategory | None = None


class SendExecutionWorkStore(Protocol):
    """Future persistence adapter seam; this phase supplies only in-memory storage."""

    def get(self, send_execution_id: str) -> SendExecutionWorkItem | None: ...

    def mark_sent(self, send_execution_id: str, provider_message_id: str, completed_at: datetime) -> SendExecutionWorkItem: ...

    def mark_failed(
        self,
        send_execution_id: str,
        failure_category: FailureCategory,
        completed_at: datetime,
    ) -> SendExecutionWorkItem: ...


class InMemorySendExecutionWorkStore:
    """Thread-safe test double; it is not a CRM entity repository."""

    def __init__(self, items: tuple[SendExecutionWorkItem, ...] = ()) -> None:
        self._items = {item.send_execution_id: item for item in items}
        self._lock = RLock()

    def get(self, send_execution_id: str) -> SendExecutionWorkItem | None:
        with self._lock:
            return self._items.get(send_execution_id)

    def mark_sent(self, send_execution_id: str, provider_message_id: str, completed_at: datetime) -> SendExecutionWorkItem:
        with self._lock:
            current = self._ready_item(send_execution_id)
            updated = replace(
                current,
                status=WorkExecutionStatus.SENT,
                provider_message_id=provider_message_id,
                completed_at=completed_at,
                failure_category=None,
            )
            self._items[send_execution_id] = updated
            return updated

    def mark_failed(
        self,
        send_execution_id: str,
        failure_category: FailureCategory,
        completed_at: datetime,
    ) -> SendExecutionWorkItem:
        with self._lock:
            current = self._ready_item(send_execution_id)
            updated = replace(
                current,
                status=WorkExecutionStatus.FAILED,
                completed_at=completed_at,
                failure_category=failure_category,
            )
            self._items[send_execution_id] = updated
            return updated

    def _ready_item(self, send_execution_id: str) -> SendExecutionWorkItem:
        current = self._items.get(send_execution_id)
        if current is None:
            raise KeyError("unknown send execution")
        if current.status is not WorkExecutionStatus.READY:
            raise ValueError(f"invalid execution transition: {current.status} -> terminal")
        return current


@dataclass(frozen=True, slots=True)
class WorkerExecutionOutcome:
    """Safe result of processing a single queue item."""

    queue_item: QueueItem | None
    execution: SendExecutionWorkItem | None
    provider_result: SendResult | None
    reason_code: str | None = None


class SendExecutionWorker:
    """Claim one item, validate READY state, invoke one ProviderAdapter, then settle it."""

    def __init__(
        self,
        queue: SendExecutionQueue,
        execution_store: SendExecutionWorkStore,
        worker_id: str,
        provider_adapter: ProviderAdapter | None = None,
    ) -> None:
        if not isinstance(worker_id, str) or not worker_id.strip():
            raise ValueError("invalid worker_id")
        self._queue = queue
        self._execution_store = execution_store
        self._worker_id = worker_id.strip()
        self._provider = provider_adapter or FakeProviderAdapter()

    def process(self, queue_item: QueueItem, timestamp: datetime) -> WorkerExecutionOutcome:
        claim = self._queue.claim(queue_item.queue_item_id, self._worker_id, timestamp)
        if not claim.claimed:
            return WorkerExecutionOutcome(claim.item, None, None, claim.reason_code)
        assert claim.item is not None
        try:
            execution = self._execution_store.get(claim.item.send_execution_id)
        except Exception:
            return self._settle_claim_failure(
                claim.item,
                timestamp,
                FailureCategory.UNKNOWN,
                "EXECUTION_LOAD_FAILED",
            )
        if execution is None:
            return self._settle_validation_failure(claim.item, None, timestamp, "UNKNOWN_SEND_EXECUTION")
        if execution.status is not WorkExecutionStatus.READY:
            return self._settle_validation_failure(claim.item, execution, timestamp, "EXECUTION_NOT_READY")
        try:
            result = self._provider.send(_provider_request(execution))
        except Exception:
            result = _exception_result()
        if result.status is SendResultStatus.SUCCESS and result.success and result.provider_message_id:
            return self._settle_success(claim.item, execution, result, timestamp)
        return self._settle_provider_failure(claim.item, execution, result, timestamp)

    def _settle_success(
        self,
        queue_item: QueueItem,
        execution: SendExecutionWorkItem,
        result: SendResult,
        timestamp: datetime,
    ) -> WorkerExecutionOutcome:
        try:
            updated_execution = self._execution_store.mark_sent(execution.send_execution_id, result.provider_message_id or "", timestamp)
            updated_queue = self._queue.complete(queue_item.queue_item_id, self._worker_id, timestamp)
        except Exception:
            return self._settle_validation_failure(queue_item, execution, timestamp, "EXECUTION_SETTLEMENT_FAILED")
        return WorkerExecutionOutcome(updated_queue, updated_execution, result)

    def _settle_provider_failure(
        self,
        queue_item: QueueItem,
        execution: SendExecutionWorkItem,
        result: SendResult,
        timestamp: datetime,
    ) -> WorkerExecutionOutcome:
        category = map_error_to_failure_category(
            result.error.category if result.error is not None else ProviderErrorCategory.UNKNOWN_ERROR
        )
        return self._settle_failure(queue_item, execution, result, category, timestamp)

    def _settle_validation_failure(
        self,
        queue_item: QueueItem,
        execution: SendExecutionWorkItem | None,
        timestamp: datetime,
        reason_code: str,
    ) -> WorkerExecutionOutcome:
        if execution is not None and execution.status is WorkExecutionStatus.READY:
            return self._settle_failure(
                queue_item,
                execution,
                None,
                FailureCategory.VALIDATION,
                timestamp,
                reason_code,
            )
        failed_queue = self._queue.fail(
            queue_item.queue_item_id,
            self._worker_id,
            FailureCategory.VALIDATION,
            timestamp,
        )
        return WorkerExecutionOutcome(failed_queue, execution, None, reason_code)

    def _settle_failure(
        self,
        queue_item: QueueItem,
        execution: SendExecutionWorkItem,
        result: SendResult | None,
        category: FailureCategory,
        timestamp: datetime,
        reason_code: str | None = None,
    ) -> WorkerExecutionOutcome:
        try:
            updated_execution = self._execution_store.mark_failed(execution.send_execution_id, category, timestamp)
            updated_queue = self._queue.fail(queue_item.queue_item_id, self._worker_id, category, timestamp)
        except Exception:
            failed_queue = self._queue.fail(
                queue_item.queue_item_id,
                self._worker_id,
                FailureCategory.UNKNOWN,
                timestamp,
            )
            return WorkerExecutionOutcome(failed_queue, execution, result, "EXECUTION_SETTLEMENT_FAILED")
        return WorkerExecutionOutcome(updated_queue, updated_execution, result, reason_code)

    def _settle_claim_failure(
        self,
        queue_item: QueueItem,
        timestamp: datetime,
        category: FailureCategory,
        reason_code: str,
    ) -> WorkerExecutionOutcome:
        """Contain a post-claim local exception without scheduling recovery."""

        failed_queue = self._queue.fail(
            queue_item.queue_item_id,
            self._worker_id,
            category,
            timestamp,
        )
        return WorkerExecutionOutcome(failed_queue, None, None, reason_code)


def _provider_request(execution: SendExecutionWorkItem) -> SendRequest:
    return SendRequest(
        request_id=execution.request_id,
        send_execution_id=execution.send_execution_id,
        recipient=execution.recipient,
        subject=execution.subject,
        body=execution.body,
        metadata={"source": "c13-worker"},
        draft_hash=execution.draft_hash,
        created_at=execution.created_at,
    )


def _exception_result() -> SendResult:
    from chitu_connector.espocrm_sync.provider_contract import ProviderError, ProviderStatus

    return SendResult(
        False,
        SendResultStatus.PERMANENT_FAILURE,
        None,
        ProviderStatus.FAILED,
        ProviderError(ProviderErrorCategory.UNKNOWN_ERROR, "PROVIDER_EXCEPTION"),
    )
