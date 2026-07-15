"""Explicit, safe terminal-result command boundary for C14.3.1C.

This module accepts only the existing B-1 terminal result vocabulary and
updates a CRM-shaped SendExecution result repository.  It has no dependency on
Worker, Queue, Provider, Brevo, HTTP, retry, EmailEvent, ReplyEvent, or Lead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.send_execution_bridge import (
    BridgeErrorClass,
    BridgeNormalizedStatus,
    SendExecutionBridgeResult,
)


RESULT_COMMAND_VERSION = "phase3c14.3.1c-explicit-result-command-v1"


class ResultCommandStatus(StrEnum):
    APPLIED = "APPLIED"
    DUPLICATE_RESULT = "DUPLICATE_RESULT"
    BLOCKED = "BLOCKED"
    RESULT_CONFLICT = "RESULT_CONFLICT"


@dataclass(frozen=True, slots=True)
class SendExecutionResultCommand:
    """One explicit, self-identifying safe terminal result command."""

    execution_id: str
    provider_attempt_id: str | None
    normalized_status: BridgeNormalizedStatus
    failure_class: BridgeErrorClass | None
    error_code: str | None
    occurred_at: datetime
    result_id: str

    def __post_init__(self) -> None:
        SendExecutionBridgeResult(
            execution_id=self.execution_id,
            provider_attempt_id=self.provider_attempt_id,
            normalized_status=self.normalized_status,
            error_class=self.failure_class,
            error_code=self.error_code,
            occurred_at=self.occurred_at,
        )
        if self.result_id != generate_result_id(
            execution_id=self.execution_id,
            provider_attempt_id=self.provider_attempt_id,
            normalized_status=self.normalized_status,
            failure_class=self.failure_class,
            error_code=self.error_code,
        ):
            raise ValueError("result_id must be the stable key for the terminal result")

    @classmethod
    def from_bridge_result(cls, result: SendExecutionBridgeResult) -> "SendExecutionResultCommand":
        """Create a deterministic command from the existing B-1 safe result."""

        if not isinstance(result, SendExecutionBridgeResult):
            raise ValueError("result must be a SendExecutionBridgeResult")
        return cls(
            execution_id=result.execution_id,
            provider_attempt_id=result.provider_attempt_id,
            normalized_status=result.normalized_status,
            failure_class=result.error_class,
            error_code=result.error_code,
            occurred_at=result.occurred_at,
            result_id=generate_result_id(
                execution_id=result.execution_id,
                provider_attempt_id=result.provider_attempt_id,
                normalized_status=result.normalized_status,
                failure_class=result.error_class,
                error_code=result.error_code,
            ),
        )


@dataclass(frozen=True, slots=True)
class CrmSendExecutionResultRecord:
    """CRM-shaped terminal-state view without Lead or payload fields."""

    id: str
    status: str
    provider_message_id: str | None = None
    failure_category: str | None = None
    last_error: str | None = None


class CrmSendExecutionResultRepository(Protocol):
    """Read/CAS seam for the explicit CRM result adapter."""

    def get(self, execution_id: str) -> CrmSendExecutionResultRecord | None: ...

    def compare_and_set_ready(
        self,
        execution_id: str,
        result: SendExecutionResultCommand,
    ) -> CrmSendExecutionResultRecord | None: ...


@dataclass(frozen=True, slots=True)
class ResultAdapterOutcome:
    """Safe observable outcome; raw payload and provider response are absent."""

    status: ResultCommandStatus
    execution_id: str
    result_id: str
    reason_code: str | None = None
    record: CrmSendExecutionResultRecord | None = None


class ExplicitSendExecutionResultAdapter:
    """Apply a safe result once, preserving terminal CRM state."""

    def __init__(self, repository: CrmSendExecutionResultRepository) -> None:
        self._repository = repository

    def apply(self, command: SendExecutionResultCommand) -> ResultAdapterOutcome:
        if not isinstance(command, SendExecutionResultCommand):
            raise ValueError("command must be a SendExecutionResultCommand")
        record = self._repository.get(command.execution_id)
        if record is None:
            return _outcome(ResultCommandStatus.BLOCKED, command, "SEND_EXECUTION_NOT_FOUND")

        if record.status == "READY":
            updated = self._repository.compare_and_set_ready(command.execution_id, command)
            if updated is not None:
                return _outcome(ResultCommandStatus.APPLIED, command, record=updated)
            record = self._repository.get(command.execution_id)
            if record is None:
                return _outcome(ResultCommandStatus.BLOCKED, command, "SEND_EXECUTION_NOT_FOUND")

        if _is_identical_terminal_result(record, command):
            return _outcome(ResultCommandStatus.DUPLICATE_RESULT, command, record=record)
        if record.status in {"SENT", "FAILED"}:
            return _outcome(ResultCommandStatus.RESULT_CONFLICT, command, "TERMINAL_RESULT_CONFLICT", record)
        return _outcome(ResultCommandStatus.BLOCKED, command, "RESULT_NOT_APPLICABLE", record)


class InMemoryCrmSendExecutionResultRepository:
    """Thread-safe acceptance fixture; it is not a CRM runtime client."""

    def __init__(self, records: tuple[CrmSendExecutionResultRecord, ...] = ()) -> None:
        self._records = {item.id: item for item in records}
        self._lock = RLock()
        self.compare_and_set_count = 0

    def get(self, execution_id: str) -> CrmSendExecutionResultRecord | None:
        with self._lock:
            return self._records.get(execution_id)

    def compare_and_set_ready(
        self,
        execution_id: str,
        result: SendExecutionResultCommand,
    ) -> CrmSendExecutionResultRecord | None:
        with self._lock:
            current = self._records.get(execution_id)
            if current is None or current.status != "READY":
                return None
            updated = _terminal_record(current, result)
            self._records[execution_id] = updated
            self.compare_and_set_count += 1
            return updated


def generate_result_id(
    *,
    execution_id: str,
    provider_attempt_id: str | None,
    normalized_status: BridgeNormalizedStatus,
    failure_class: BridgeErrorClass | None,
    error_code: str | None,
) -> str:
    """Return the stable idempotency key for one terminal semantic result."""

    bridge_result = SendExecutionBridgeResult(
        execution_id=execution_id,
        provider_attempt_id=provider_attempt_id,
        normalized_status=normalized_status,
        error_class=failure_class,
        error_code=error_code,
        occurred_at=datetime.now().astimezone(),
    )
    canonical = {
        "errorCode": bridge_result.error_code,
        "errorClass": bridge_result.error_class.value if bridge_result.error_class is not None else None,
        "executionId": bridge_result.execution_id,
        "normalizedStatus": bridge_result.normalized_status.value,
        "providerAttemptId": bridge_result.provider_attempt_id,
        "version": RESULT_COMMAND_VERSION,
    }
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _terminal_record(
    current: CrmSendExecutionResultRecord,
    command: SendExecutionResultCommand,
) -> CrmSendExecutionResultRecord:
    if command.normalized_status is BridgeNormalizedStatus.SENT:
        return CrmSendExecutionResultRecord(
            id=current.id,
            status="SENT",
            provider_message_id=command.provider_attempt_id,
            failure_category=None,
            last_error=None,
        )
    assert command.failure_class is not None
    assert command.error_code is not None
    return CrmSendExecutionResultRecord(
        id=current.id,
        status="FAILED",
        provider_message_id=None,
        failure_category=command.failure_class.value,
        last_error=command.error_code,
    )


def _is_identical_terminal_result(
    record: CrmSendExecutionResultRecord,
    command: SendExecutionResultCommand,
) -> bool:
    if command.normalized_status is BridgeNormalizedStatus.SENT:
        return record.status == "SENT" and record.provider_message_id == command.provider_attempt_id
    return (
        record.status == "FAILED"
        and command.failure_class is not None
        and command.error_code is not None
        and record.failure_category == command.failure_class.value
        and record.last_error == command.error_code
    )


def _outcome(
    status: ResultCommandStatus,
    command: SendExecutionResultCommand,
    reason_code: str | None = None,
    record: CrmSendExecutionResultRecord | None = None,
) -> ResultAdapterOutcome:
    return ResultAdapterOutcome(
        status=status,
        execution_id=command.execution_id,
        result_id=command.result_id,
        reason_code=reason_code,
        record=record,
    )
