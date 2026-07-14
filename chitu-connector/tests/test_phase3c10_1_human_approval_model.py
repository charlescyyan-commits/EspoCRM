"""Offline contract tests for the mandatory C10.1 human approval boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.human_approval import (
    APPROVAL_VERSION,
    ApprovalStatus,
    InMemoryHumanApprovalRegistry,
)


CREATED_AT = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)


class HumanApprovalModelTests(TestCase):
    def setUp(self) -> None:
        self.registry = InMemoryHumanApprovalRegistry()

    def _draft_ready(self, *, draft_id: str = "draft-c09-001", approval_id: str = "approval-c10-001"):
        return self.registry.create_draft_ready(draft_id, approval_id, CREATED_AT, "draft-service")

    def test_submit_for_review_records_pending_state_and_audit_trace(self) -> None:
        created = self._draft_ready()
        pending = self.registry.submit_for_review(created.approval_id, "operator-001", CREATED_AT + timedelta(minutes=1))

        self.assertEqual(created.status, ApprovalStatus.DRAFT_READY)
        self.assertEqual(pending.status, ApprovalStatus.PENDING_REVIEW)
        self.assertIsNone(pending.reviewer_id)
        trace = self.registry.audit_trace(pending.approval_id)
        self.assertEqual([(item.who, item.decision) for item in trace], [
            ("draft-service", ApprovalStatus.DRAFT_READY),
            ("operator-001", ApprovalStatus.PENDING_REVIEW),
        ])
        self.assertEqual({item.approval_version for item in trace}, {APPROVAL_VERSION})

    def test_approve_requires_pending_review_and_can_become_ready_to_send(self) -> None:
        created = self._draft_ready()
        self.registry.submit_for_review(created.approval_id, "operator-001", CREATED_AT + timedelta(minutes=1))
        approved_at = CREATED_AT + timedelta(minutes=2)
        approved = self.registry.approve(created.approval_id, "reviewer-001", approved_at)
        ready = self.registry.mark_ready_to_send(created.approval_id, "release-operator-001", CREATED_AT + timedelta(minutes=3))

        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.reviewer_id, "reviewer-001")
        self.assertEqual(approved.decided_at, approved_at)
        self.assertIsNone(approved.rejection_reason)
        self.assertEqual(ready.status, ApprovalStatus.READY_TO_SEND)
        self.assertEqual(ready.reviewer_id, "reviewer-001")
        self.assertEqual(ready.decided_at, approved_at)

    def test_reject_records_named_reviewer_reason_and_terminal_state(self) -> None:
        created = self._draft_ready()
        self.registry.submit_for_review(created.approval_id, "operator-001", CREATED_AT + timedelta(minutes=1))
        rejected_at = CREATED_AT + timedelta(minutes=2)
        rejected = self.registry.reject(
            created.approval_id,
            "reviewer-002",
            "Needs a verified contact route.",
            rejected_at,
        )

        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(rejected.reviewer_id, "reviewer-002")
        self.assertEqual(rejected.decided_at, rejected_at)
        self.assertEqual(rejected.rejection_reason, "Needs a verified contact route.")
        trace = self.registry.audit_trace(created.approval_id)
        self.assertEqual(trace[-1].who, "reviewer-002")
        self.assertEqual(trace[-1].decision, ApprovalStatus.REJECTED)

    def test_invalid_transition_fails(self) -> None:
        created = self._draft_ready()

        with self.assertRaisesRegex(ValueError, "DRAFT_READY -> APPROVED"):
            self.registry.approve(created.approval_id, "reviewer-001", CREATED_AT + timedelta(minutes=1))

    def test_duplicate_approval_attempt_for_same_draft_fails(self) -> None:
        self._draft_ready()

        with self.assertRaisesRegex(ValueError, "duplicate approval attempt for draft"):
            self._draft_ready(approval_id="approval-c10-duplicate")

    def test_already_rejected_draft_cannot_be_resubmitted_or_approved(self) -> None:
        created = self._draft_ready()
        self.registry.submit_for_review(created.approval_id, "operator-001", CREATED_AT + timedelta(minutes=1))
        self.registry.reject(created.approval_id, "reviewer-002", "Not ready for outreach.", CREATED_AT + timedelta(minutes=2))

        with self.assertRaisesRegex(ValueError, "REJECTED -> PENDING_REVIEW"):
            self.registry.submit_for_review(created.approval_id, "operator-001", CREATED_AT + timedelta(minutes=3))
        with self.assertRaisesRegex(ValueError, "REJECTED -> APPROVED"):
            self.registry.approve(created.approval_id, "reviewer-001", CREATED_AT + timedelta(minutes=3))
