"""Controlled, offline orchestration from C10.1 approval to C10.2 adapter.

This service creates C10.0-B requests only for approvals already marked
``READY_TO_SEND``. It uses an injected provider adapter and an in-memory
execution registry; it contains no provider SDK, network, CRM, or email code.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.human_approval import ApprovalStatus, DraftApproval, HumanApprovalRegistry
from chitu_connector.espocrm_sync.send_idempotency import SendRequest, generate_send_idempotency_key
from chitu_connector.espocrm_sync.send_provider import (
    ProviderResultStatus,
    SendProviderAdapter,
    SendProviderAttemptResult,
)


class SendExecutionState(StrEnum):
    READY_TO_SEND = "READY_TO_SEND"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class SendExecution:
    """One persisted orchestration record; it contains no email content."""

    draft_id: str
    approval_id: str
    send_request: SendRequest
    state: SendExecutionState
    send_attempt_id: str | None
    provider_name: str
    result_status: ProviderResultStatus | None
    reason_code: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SendExecutionAuditTrace:
    """Required execution trace for each accepted state transition."""

    draft_id: str
    approval_id: str
    send_request_id: str
    send_attempt_id: str | None
    provider: str
    result: ProviderResultStatus | None
    timestamp: datetime
    state: SendExecutionState


@dataclass(frozen=True, slots=True)
class SendExecutionOutcome:
    """Service output for both accepted and safely rejected orchestration calls."""

    execution: SendExecution | None
    reason_code: str | None = None
    duplicate: bool = False


class SendExecutionRegistry(Protocol):
    """Persistence seam for execution records and their append-only trace."""

    def create(self, execution: SendExecution) -> SendExecution: ...

    def get(self, send_request_id: str) -> SendExecution | None: ...

    def find_by_send_attempt_id(self, send_attempt_id: str) -> SendExecution | None: ...

    def for_approval(self, approval_id: str) -> tuple[SendExecution, ...]: ...

    def transition(
        self,
        send_request_id: str,
        target: SendExecutionState,
        timestamp: datetime,
        *,
        send_attempt_id: str | None = None,
        result_status: ProviderResultStatus | None = None,
        reason_code: str | None = None,
    ) -> SendExecution: ...

    def audit_trace(self, send_request_id: str) -> tuple[SendExecutionAuditTrace, ...]: ...


class InMemorySendExecutionRegistry:
    """Thread-safe, state-only execution persistence for offline orchestration."""

    def __init__(self) -> None:
        self._executions_by_request_id: dict[str, SendExecution] = {}
        self._request_ids_by_approval: dict[str, list[str]] = {}
        self._audit_by_request_id: dict[str, list[SendExecutionAuditTrace]] = {}
        self._lock = RLock()

    def create(self, execution: SendExecution) -> SendExecution:
        with self._lock:
            request_id = execution.send_request.send_request_id
            if request_id in self._executions_by_request_id:
                raise ValueError("duplicate send execution request id")
            self._executions_by_request_id[request_id] = execution
            self._request_ids_by_approval.setdefault(execution.approval_id, []).append(request_id)
            self._append_audit(execution, execution.created_at)
            return execution

    def get(self, send_request_id: str) -> SendExecution | None:
        with self._lock:
            return self._executions_by_request_id.get(send_request_id)

    def find_by_send_attempt_id(self, send_attempt_id: str) -> SendExecution | None:
        with self._lock:
            return next(
                (
                    execution
                    for execution in self._executions_by_request_id.values()
                    if execution.send_attempt_id == send_attempt_id
                ),
                None,
            )

    def for_approval(self, approval_id: str) -> tuple[SendExecution, ...]:
        with self._lock:
            return tuple(
                self._executions_by_request_id[request_id]
                for request_id in self._request_ids_by_approval.get(approval_id, ())
            )

    def transition(
        self,
        send_request_id: str,
        target: SendExecutionState,
        timestamp: datetime,
        *,
        send_attempt_id: str | None = None,
        result_status: ProviderResultStatus | None = None,
        reason_code: str | None = None,
    ) -> SendExecution:
        _require_datetime("timestamp", timestamp)
        with self._lock:
            current = self._executions_by_request_id.get(send_request_id)
            if current is None:
                raise KeyError("unknown send execution request id")
            if target not in _ALLOWED_TRANSITIONS[current.state]:
                raise ValueError(f"invalid execution transition: {current.state} -> {target}")
            updated = replace(
                current,
                state=target,
                send_attempt_id=send_attempt_id if send_attempt_id is not None else current.send_attempt_id,
                result_status=result_status if result_status is not None else current.result_status,
                reason_code=reason_code if reason_code is not None else current.reason_code,
                updated_at=timestamp,
            )
            self._executions_by_request_id[send_request_id] = updated
            self._append_audit(updated, timestamp)
            return updated

    def audit_trace(self, send_request_id: str) -> tuple[SendExecutionAuditTrace, ...]:
        with self._lock:
            if send_request_id not in self._executions_by_request_id:
                raise KeyError("unknown send execution request id")
            return tuple(self._audit_by_request_id[send_request_id])

    def _append_audit(self, execution: SendExecution, timestamp: datetime) -> None:
        self._audit_by_request_id.setdefault(execution.send_request.send_request_id, []).append(
            SendExecutionAuditTrace(
                draft_id=execution.draft_id,
                approval_id=execution.approval_id,
                send_request_id=execution.send_request.send_request_id,
                send_attempt_id=execution.send_attempt_id,
                provider=execution.provider_name,
                result=execution.result_status,
                timestamp=timestamp,
                state=execution.state,
            )
        )


class ControlledSendExecutionService:
    """Enforce C10.1 approval, C10.0-B identity, and C10.2 delegation."""

    def __init__(
        self,
        approvals: HumanApprovalRegistry,
        provider_adapter: SendProviderAdapter,
        registry: SendExecutionRegistry | None = None,
    ) -> None:
        self._approvals = approvals
        self._provider_adapter = provider_adapter
        self._registry = registry or InMemorySendExecutionRegistry()
        self._lock = RLock()

    def execute(
        self,
        approval_id: str,
        lead_id: str,
        provider_name: str,
        send_request_id: str,
        timestamp: datetime,
    ) -> SendExecutionOutcome:
        invalid = _validate_execution_input(approval_id, lead_id, provider_name, send_request_id, timestamp)
        if invalid:
            return SendExecutionOutcome(None, invalid)
        with self._lock:
            existing = self._registry.get(send_request_id)
            if existing is not None:
                return SendExecutionOutcome(existing, "DUPLICATE_EXECUTION", duplicate=True)
            try:
                approval = self._approvals.get(approval_id)
            except KeyError:
                return SendExecutionOutcome(None, "UNKNOWN_APPROVAL")
            if approval.status is not ApprovalStatus.READY_TO_SEND:
                return SendExecutionOutcome(None, "APPROVAL_NOT_READY")
            if any(item.state is SendExecutionState.SENT for item in self._registry.for_approval(approval_id)):
                return SendExecutionOutcome(None, "DRAFT_ALREADY_SENT")
            if any(item.state in {SendExecutionState.READY_TO_SEND, SendExecutionState.SUBMITTED, SendExecutionState.PROCESSING}
                   for item in self._registry.for_approval(approval_id)):
                return SendExecutionOutcome(None, "EXECUTION_IN_PROGRESS")
            request = _create_send_request(approval, lead_id, provider_name, send_request_id, timestamp)
            execution = self._registry.create(
                SendExecution(
                    draft_id=approval.draft_id,
                    approval_id=approval.approval_id,
                    send_request=request,
                    state=SendExecutionState.READY_TO_SEND,
                    send_attempt_id=None,
                    provider_name=provider_name,
                    result_status=None,
                    reason_code=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            execution = self._registry.transition(send_request_id, SendExecutionState.SUBMITTED, timestamp)
            execution = self._registry.transition(send_request_id, SendExecutionState.PROCESSING, timestamp)
            adapter_result = self._provider_adapter.submit(request)
            return SendExecutionOutcome(self._persist_provider_result(execution, adapter_result, timestamp))

    def audit_trace(self, send_request_id: str) -> tuple[SendExecutionAuditTrace, ...]:
        return self._registry.audit_trace(send_request_id)

    def _persist_provider_result(
        self,
        execution: SendExecution,
        adapter_result: SendProviderAttemptResult,
        timestamp: datetime,
    ) -> SendExecution:
        result = adapter_result.provider_result
        target = SendExecutionState.SENT if result.status is ProviderResultStatus.ACCEPTED else SendExecutionState.FAILED
        return self._registry.transition(
            execution.send_request.send_request_id,
            target,
            timestamp,
            send_attempt_id=result.send_attempt_id,
            result_status=result.status,
            reason_code=result.reason_code,
        )


_ALLOWED_TRANSITIONS: dict[SendExecutionState, frozenset[SendExecutionState]] = {
    SendExecutionState.READY_TO_SEND: frozenset({SendExecutionState.SUBMITTED}),
    SendExecutionState.SUBMITTED: frozenset({SendExecutionState.PROCESSING}),
    SendExecutionState.PROCESSING: frozenset({SendExecutionState.SENT, SendExecutionState.FAILED}),
    SendExecutionState.SENT: frozenset(),
    SendExecutionState.FAILED: frozenset(),
}


def _create_send_request(
    approval: DraftApproval,
    lead_id: str,
    provider_name: str,
    send_request_id: str,
    created_at: datetime,
) -> SendRequest:
    return SendRequest(
        draft_id=approval.draft_id,
        lead_id=lead_id,
        send_request_id=send_request_id,
        idempotency_key=generate_send_idempotency_key(
            approval.draft_id,
            lead_id,
            send_request_id,
            provider_name,
        ),
        provider_name=provider_name,
        created_at=created_at,
    )


def _validate_execution_input(
    approval_id: object,
    lead_id: object,
    provider_name: object,
    send_request_id: object,
    timestamp: object,
) -> str | None:
    for name, value in (
        ("approval_id", approval_id),
        ("lead_id", lead_id),
        ("provider_name", provider_name),
        ("send_request_id", send_request_id),
    ):
        if not isinstance(value, str) or not value.strip():
            return f"INVALID_{name.upper()}"
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return "INVALID_TIMESTAMP"
    return None


def _require_datetime(name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"invalid {name}")
