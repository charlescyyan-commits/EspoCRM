"""CRM-shaped adapter for the C14.3.1B-1 SendExecution bridge contract.

The module is deliberately an explicit connector-side invocation seam. It does
not implement an EspoCRM hook, Queue, Worker, provider, transport, or result
callback. A caller supplies CRM record views and a connector-owned approved
delivery payload source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from chitu_connector.espocrm_sync.send_execution_bridge import (
    SendExecutionBridgeAdapter,
    SendExecutionBridgeReceipt,
    SendExecutionBridgeRequest,
    generate_idempotency_key,
    hash_recipient_reference,
)


class CrmDraftApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CrmSendExecutionStatus(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class CrmDraftApprovalRecord:
    """Only approval references required for a bridge submission."""

    id: str
    draft_id: str
    status: CrmDraftApprovalStatus
    content_hash: str


@dataclass(frozen=True, slots=True)
class CrmSendExecutionRecord:
    """Read-only CRM execution view used by the explicit bridge caller."""

    id: str
    send_request_id: str
    status: CrmSendExecutionStatus
    draft_approval_id: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ApprovedDeliveryPayload:
    """Connector-owned content eligible for an already-approved delivery.

    Recipient, subject, and body never enter the B-1 bridge request. They are
    validated here solely to prove the future execution payload is complete.
    """

    draft_id: str
    content_hash: str
    recipient: str
    subject: str
    body: str
    campaign_reference: str
    generated_at: datetime


class CrmSendExecutionRepository(Protocol):
    """Read-only CRM record lookup boundary for an explicit bridge caller."""

    def get_send_execution(self, execution_id: str) -> CrmSendExecutionRecord | None: ...

    def get_draft_approval(self, approval_id: str) -> CrmDraftApprovalRecord | None: ...


class ApprovedDeliveryPayloadSource(Protocol):
    """Connector-owned lookup boundary for an approved delivery payload."""

    def get_approved_payload(self, draft_id: str) -> ApprovedDeliveryPayload | None: ...


class BridgeSubmissionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    DUPLICATE = "DUPLICATE"
    BLOCKED = "BLOCKED"
    FAILED_SUBMISSION = "FAILED_SUBMISSION"


@dataclass(frozen=True, slots=True)
class BridgeSubmissionOutcome:
    """Safe observable result. It never includes raw delivery content."""

    status: BridgeSubmissionStatus
    execution_id: str
    reason_code: str | None = None
    request: SendExecutionBridgeRequest | None = None
    receipt: SendExecutionBridgeReceipt | None = None


class CrmSendExecutionBridgeAdapter:
    """Construct and submit a B-1 request from verified CRM/payload references."""

    def __init__(
        self,
        crm_repository: CrmSendExecutionRepository,
        payload_source: ApprovedDeliveryPayloadSource,
        bridge_adapter: SendExecutionBridgeAdapter,
    ) -> None:
        self._crm_repository = crm_repository
        self._payload_source = payload_source
        self._bridge_adapter = bridge_adapter

    def submit(self, execution_id: str) -> BridgeSubmissionOutcome:
        """Submit once after approval and readiness verification.

        This method has no CRM write capability. Rejection and bridge errors
        therefore cannot mark a CRM SendExecution SENT or alter Lead state.
        """

        execution = self._crm_repository.get_send_execution(execution_id)
        if execution is None:
            return _blocked(execution_id, "SEND_EXECUTION_NOT_FOUND")
        if not _valid_text(execution.id):
            return _blocked(execution_id, "INVALID_SEND_EXECUTION_ID")
        if not _valid_text(execution.send_request_id):
            return _blocked(execution.id, "MISSING_SEND_REQUEST_ID")
        if execution.status is not CrmSendExecutionStatus.READY:
            return _blocked(execution.id, "SEND_EXECUTION_NOT_READY")
        if not _valid_text(execution.draft_approval_id):
            return _blocked(execution.id, "MISSING_DRAFT_APPROVAL_REFERENCE")
        if not _valid_timestamp(execution.created_at):
            return _blocked(execution.id, "INVALID_EXECUTION_TIMESTAMP")

        approval = self._crm_repository.get_draft_approval(execution.draft_approval_id)
        if approval is None:
            return _blocked(execution.id, "DRAFT_APPROVAL_NOT_FOUND")
        if approval.id != execution.draft_approval_id:
            return _blocked(execution.id, "DRAFT_APPROVAL_REFERENCE_MISMATCH")
        if approval.status is not CrmDraftApprovalStatus.APPROVED:
            return _blocked(execution.id, "DRAFT_NOT_APPROVED")
        if not _valid_text(approval.draft_id):
            return _blocked(execution.id, "MISSING_APPROVED_DRAFT_ID")
        if not _valid_hash(approval.content_hash):
            return _blocked(execution.id, "MISSING_APPROVED_CONTENT_HASH")

        payload = self._payload_source.get_approved_payload(approval.draft_id)
        if payload is None:
            return _blocked(execution.id, "APPROVED_PAYLOAD_NOT_FOUND")
        if payload.draft_id != approval.draft_id:
            return _blocked(execution.id, "APPROVED_PAYLOAD_DRAFT_MISMATCH")
        if payload.content_hash != approval.content_hash:
            return _blocked(execution.id, "APPROVED_PAYLOAD_HASH_MISMATCH")
        if not _valid_text(payload.recipient):
            return _blocked(execution.id, "MISSING_APPROVED_RECIPIENT")
        if not _valid_text(payload.subject):
            return _blocked(execution.id, "MISSING_APPROVED_SUBJECT")
        if not _valid_text(payload.body):
            return _blocked(execution.id, "MISSING_APPROVED_BODY")
        if not _valid_text(payload.campaign_reference):
            return _blocked(execution.id, "MISSING_CAMPAIGN_REFERENCE")
        if not _valid_timestamp(payload.generated_at):
            return _blocked(execution.id, "INVALID_APPROVED_PAYLOAD_TIMESTAMP")

        request = SendExecutionBridgeRequest(
            execution_id=execution.id,
            idempotency_key=generate_idempotency_key(execution.id),
            content_hash=payload.content_hash,
            recipient_hash=hash_recipient_reference(payload.recipient),
            campaign_reference=payload.campaign_reference.strip(),
            created_at=execution.created_at,
        )

        try:
            receipt = self._bridge_adapter.enqueue(request)
        except Exception:
            return BridgeSubmissionOutcome(
                status=BridgeSubmissionStatus.FAILED_SUBMISSION,
                execution_id=execution.id,
                reason_code="BRIDGE_SUBMISSION_UNAVAILABLE",
                request=request,
            )

        return BridgeSubmissionOutcome(
            status=BridgeSubmissionStatus.DUPLICATE if receipt.duplicate else BridgeSubmissionStatus.SUBMITTED,
            execution_id=execution.id,
            request=request,
            receipt=receipt,
        )


class InMemoryCrmSendExecutionRepository:
    """Read-only fixture repository for adapter unit tests."""

    def __init__(
        self,
        executions: tuple[CrmSendExecutionRecord, ...] = (),
        approvals: tuple[CrmDraftApprovalRecord, ...] = (),
    ) -> None:
        self._executions = {item.id: item for item in executions}
        self._approvals = {item.id: item for item in approvals}

    def get_send_execution(self, execution_id: str) -> CrmSendExecutionRecord | None:
        return self._executions.get(execution_id)

    def get_draft_approval(self, approval_id: str) -> CrmDraftApprovalRecord | None:
        return self._approvals.get(approval_id)


class InMemoryApprovedDeliveryPayloadSource:
    """In-process fixture source; it is not a durable production payload store."""

    def __init__(self, payloads: tuple[ApprovedDeliveryPayload, ...] = ()) -> None:
        self._payloads = {item.draft_id: item for item in payloads}

    def get_approved_payload(self, draft_id: str) -> ApprovedDeliveryPayload | None:
        return self._payloads.get(draft_id)


def _blocked(execution_id: str, reason_code: str) -> BridgeSubmissionOutcome:
    return BridgeSubmissionOutcome(
        status=BridgeSubmissionStatus.BLOCKED,
        execution_id=execution_id,
        reason_code=reason_code,
    )


def _valid_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_hash(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_timestamp(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
