"""Offline queue and worker contract for future SendExecution processing.

This module defines state ownership and idempotency only. It contains no
provider execution, daemon, scheduler, queue service, or retry implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.failure_classification import FailureCategory, normalize_failure_category


class QueueItemState(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class QueueItem:
    """A state-only reservation for exactly one SendExecution identity."""

    queue_item_id: str
    send_execution_id: str
    state: QueueItemState
    created_at: datetime
    claimed_at: datetime | None
    completed_at: datetime | None
    worker_id: str | None
    failure_category: FailureCategory | None = None


@dataclass(frozen=True, slots=True)
class QueueClaim:
    """Safe result of an atomic-concept claim attempt."""

    item: QueueItem | None
    claimed: bool
    reason_code: str | None = None


class SendExecutionQueue(Protocol):
    """Persistence seam for future worker execution claims."""

    def enqueue(self, send_execution_id: str, created_at: datetime) -> QueueItem: ...

    def claim(self, queue_item_id: str, worker_id: str, claimed_at: datetime) -> QueueClaim: ...

    def complete(self, queue_item_id: str, worker_id: str, completed_at: datetime) -> QueueItem: ...

    def fail(
        self,
        queue_item_id: str,
        worker_id: str,
        failure_category: FailureCategory | str | None,
        completed_at: datetime,
    ) -> QueueItem: ...

    def get(self, queue_item_id: str) -> QueueItem | None: ...


class SendExecutionWorker(Protocol):
    """Future worker seam; this phase intentionally provides no implementation."""

    def process(self, queue_item: QueueItem) -> None: ...


class InMemorySendExecutionQueue:
    """Thread-safe reference queue with local claim atomicity only."""

    def __init__(self) -> None:
        self._items_by_id: dict[str, QueueItem] = {}
        self._item_id_by_execution: dict[str, str] = {}
        self._lock = RLock()

    @property
    def item_count(self) -> int:
        with self._lock:
            return len(self._items_by_id)

    @property
    def external_request_count(self) -> int:
        """Always zero; this reference store has no transport dependency."""

        return 0

    def enqueue(self, send_execution_id: str, created_at: datetime) -> QueueItem:
        _require_identifier("send_execution_id", send_execution_id)
        _require_datetime("created_at", created_at)
        normalized_id = send_execution_id.strip()
        with self._lock:
            existing_id = self._item_id_by_execution.get(normalized_id)
            if existing_id is not None:
                return self._items_by_id[existing_id]
            item = QueueItem(
                queue_item_id=f"queue:{normalized_id}",
                send_execution_id=normalized_id,
                state=QueueItemState.QUEUED,
                created_at=created_at,
                claimed_at=None,
                completed_at=None,
                worker_id=None,
            )
            self._items_by_id[item.queue_item_id] = item
            self._item_id_by_execution[normalized_id] = item.queue_item_id
            return item

    def claim(self, queue_item_id: str, worker_id: str, claimed_at: datetime) -> QueueClaim:
        _require_identifier("queue_item_id", queue_item_id)
        _require_identifier("worker_id", worker_id)
        _require_datetime("claimed_at", claimed_at)
        with self._lock:
            current = self._items_by_id.get(queue_item_id)
            if current is None:
                return QueueClaim(None, False, "UNKNOWN_QUEUE_ITEM")
            if current.state is not QueueItemState.QUEUED:
                return QueueClaim(current, False, "QUEUE_ITEM_NOT_QUEUED")
            claimed = replace(
                current,
                state=QueueItemState.CLAIMED,
                claimed_at=claimed_at,
                worker_id=worker_id.strip(),
            )
            self._items_by_id[queue_item_id] = claimed
            return QueueClaim(claimed, True)

    def complete(self, queue_item_id: str, worker_id: str, completed_at: datetime) -> QueueItem:
        current = self._owned_claim(queue_item_id, worker_id, completed_at)
        completed = replace(current, state=QueueItemState.COMPLETED, completed_at=completed_at)
        with self._lock:
            self._items_by_id[queue_item_id] = completed
        return completed

    def fail(
        self,
        queue_item_id: str,
        worker_id: str,
        failure_category: FailureCategory | str | None,
        completed_at: datetime,
    ) -> QueueItem:
        current = self._owned_claim(queue_item_id, worker_id, completed_at)
        failed = replace(
            current,
            state=QueueItemState.FAILED,
            completed_at=completed_at,
            failure_category=normalize_failure_category(failure_category),
        )
        with self._lock:
            self._items_by_id[queue_item_id] = failed
        return failed

    def get(self, queue_item_id: str) -> QueueItem | None:
        _require_identifier("queue_item_id", queue_item_id)
        with self._lock:
            return self._items_by_id.get(queue_item_id)

    def _owned_claim(self, queue_item_id: str, worker_id: str, timestamp: datetime) -> QueueItem:
        _require_identifier("queue_item_id", queue_item_id)
        _require_identifier("worker_id", worker_id)
        _require_datetime("timestamp", timestamp)
        with self._lock:
            current = self._items_by_id.get(queue_item_id)
            if current is None:
                raise KeyError("unknown queue item")
            if current.state is not QueueItemState.CLAIMED:
                raise ValueError(f"invalid queue transition: {current.state} -> terminal")
            if current.worker_id != worker_id.strip():
                raise ValueError("queue item is owned by a different worker")
            return current


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {name}")


def _require_datetime(name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"invalid {name}")
