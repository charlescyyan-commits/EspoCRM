"""Human-only approval contract for future outreach readiness.

This module stores and transitions approval state only.  It has no email,
provider, campaign, CRM, AI, or delivery dependency.  ``READY_TO_SEND`` is a
state-contract outcome, not an instruction to send anything.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol


APPROVAL_VERSION = "c10.1-human-approval-v1"


class ApprovalStatus(StrEnum):
    DRAFT_READY = "DRAFT_READY"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    READY_TO_SEND = "READY_TO_SEND"


@dataclass(frozen=True, slots=True)
class DraftApproval:
    """Approval record for one immutable draft identity.

    ``reviewer_id`` remains a placeholder until a named human approves or
    rejects the draft.  The model deliberately carries only ``draft_id`` and
    never email content, recipients, provider details, or a send request.
    """

    draft_id: str
    approval_id: str
    status: ApprovalStatus
    reviewer_id: str | None
    created_at: datetime
    decided_at: datetime | None
    rejection_reason: str | None
    approval_version: str = APPROVAL_VERSION


@dataclass(frozen=True, slots=True)
class ApprovalAuditTrace:
    """Append-only transition evidence: who, when, decision, and version."""

    draft_id: str
    approval_id: str
    who: str
    when: datetime
    decision: ApprovalStatus
    approval_version: str


class HumanApprovalRegistry(Protocol):
    """Persistence seam for a mandatory human review boundary."""

    def create_draft_ready(
        self,
        draft_id: str,
        approval_id: str,
        created_at: datetime,
        actor_id: str,
    ) -> DraftApproval: ...

    def submit_for_review(self, approval_id: str, actor_id: str, occurred_at: datetime) -> DraftApproval: ...

    def approve(self, approval_id: str, reviewer_id: str, decided_at: datetime) -> DraftApproval: ...

    def reject(
        self,
        approval_id: str,
        reviewer_id: str,
        rejection_reason: str,
        decided_at: datetime,
    ) -> DraftApproval: ...

    def mark_ready_to_send(self, approval_id: str, actor_id: str, occurred_at: datetime) -> DraftApproval: ...

    def get(self, approval_id: str) -> DraftApproval: ...

    def audit_trace(self, approval_id: str) -> tuple[ApprovalAuditTrace, ...]: ...


class InMemoryHumanApprovalRegistry:
    """Thread-safe reference implementation for offline contract tests.

    One draft can have exactly one approval record.  Rejected records are
    terminal, so a replacement draft identity is required before a new review
    cycle can begin.  No method performs approval automatically.
    """

    def __init__(self) -> None:
        self._approvals_by_id: dict[str, DraftApproval] = {}
        self._approval_id_by_draft: dict[str, str] = {}
        self._audit_by_approval_id: dict[str, list[ApprovalAuditTrace]] = {}
        self._lock = RLock()

    def create_draft_ready(
        self,
        draft_id: str,
        approval_id: str,
        created_at: datetime,
        actor_id: str,
    ) -> DraftApproval:
        _require_identifier("draft_id", draft_id)
        _require_identifier("approval_id", approval_id)
        _require_identifier("actor_id", actor_id)
        _require_datetime("created_at", created_at)
        with self._lock:
            if draft_id in self._approval_id_by_draft:
                raise ValueError("duplicate approval attempt for draft")
            if approval_id in self._approvals_by_id:
                raise ValueError("duplicate approval id")
            approval = DraftApproval(
                draft_id=draft_id,
                approval_id=approval_id,
                status=ApprovalStatus.DRAFT_READY,
                reviewer_id=None,
                created_at=created_at,
                decided_at=None,
                rejection_reason=None,
            )
            self._approvals_by_id[approval_id] = approval
            self._approval_id_by_draft[draft_id] = approval_id
            self._append_audit(approval, actor_id, created_at)
            return approval

    def submit_for_review(self, approval_id: str, actor_id: str, occurred_at: datetime) -> DraftApproval:
        return self._transition(approval_id, ApprovalStatus.PENDING_REVIEW, actor_id, occurred_at)

    def approve(self, approval_id: str, reviewer_id: str, decided_at: datetime) -> DraftApproval:
        _require_identifier("reviewer_id", reviewer_id)
        return self._transition(
            approval_id,
            ApprovalStatus.APPROVED,
            reviewer_id,
            decided_at,
            reviewer_id=reviewer_id,
        )

    def reject(
        self,
        approval_id: str,
        reviewer_id: str,
        rejection_reason: str,
        decided_at: datetime,
    ) -> DraftApproval:
        _require_identifier("reviewer_id", reviewer_id)
        _require_identifier("rejection_reason", rejection_reason)
        return self._transition(
            approval_id,
            ApprovalStatus.REJECTED,
            reviewer_id,
            decided_at,
            reviewer_id=reviewer_id,
            rejection_reason=rejection_reason.strip(),
        )

    def mark_ready_to_send(self, approval_id: str, actor_id: str, occurred_at: datetime) -> DraftApproval:
        return self._transition(approval_id, ApprovalStatus.READY_TO_SEND, actor_id, occurred_at)

    def get(self, approval_id: str) -> DraftApproval:
        _require_identifier("approval_id", approval_id)
        with self._lock:
            approval = self._approvals_by_id.get(approval_id)
            if approval is None:
                raise KeyError("unknown approval id")
            return approval

    def audit_trace(self, approval_id: str) -> tuple[ApprovalAuditTrace, ...]:
        _require_identifier("approval_id", approval_id)
        with self._lock:
            if approval_id not in self._approvals_by_id:
                raise KeyError("unknown approval id")
            return tuple(self._audit_by_approval_id[approval_id])

    def _transition(
        self,
        approval_id: str,
        target: ApprovalStatus,
        actor_id: str,
        occurred_at: datetime,
        *,
        reviewer_id: str | None = None,
        rejection_reason: str | None = None,
    ) -> DraftApproval:
        _require_identifier("approval_id", approval_id)
        _require_identifier("actor_id", actor_id)
        _require_datetime("occurred_at", occurred_at)
        with self._lock:
            current = self.get(approval_id)
            if target not in _ALLOWED_TRANSITIONS[current.status]:
                raise ValueError(f"invalid approval transition: {current.status} -> {target}")
            updated = replace(
                current,
                status=target,
                reviewer_id=reviewer_id if target in _DECISION_STATUSES else current.reviewer_id,
                decided_at=occurred_at if target in _DECISION_STATUSES else current.decided_at,
                rejection_reason=rejection_reason if target is ApprovalStatus.REJECTED else None,
            )
            self._approvals_by_id[approval_id] = updated
            self._append_audit(updated, actor_id, occurred_at)
            return updated

    def _append_audit(self, approval: DraftApproval, who: str, when: datetime) -> None:
        self._audit_by_approval_id.setdefault(approval.approval_id, []).append(
            ApprovalAuditTrace(
                draft_id=approval.draft_id,
                approval_id=approval.approval_id,
                who=who,
                when=when,
                decision=approval.status,
                approval_version=approval.approval_version,
            )
        )


_DECISION_STATUSES = frozenset({ApprovalStatus.APPROVED, ApprovalStatus.REJECTED})
_ALLOWED_TRANSITIONS: dict[ApprovalStatus, frozenset[ApprovalStatus]] = {
    ApprovalStatus.DRAFT_READY: frozenset({ApprovalStatus.PENDING_REVIEW}),
    ApprovalStatus.PENDING_REVIEW: frozenset({ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}),
    ApprovalStatus.APPROVED: frozenset({ApprovalStatus.READY_TO_SEND}),
    ApprovalStatus.REJECTED: frozenset(),
    ApprovalStatus.READY_TO_SEND: frozenset(),
}


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {name}")


def _require_datetime(name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"invalid {name}")
