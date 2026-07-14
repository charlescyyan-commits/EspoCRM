"""Offline contract tests for C10.4 reply tracking after controlled send."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.human_approval import InMemoryHumanApprovalRegistry
from chitu_connector.espocrm_sync.reply_tracking import (
    ReplyEventReservationStatus,
    ReplyStatus,
    ReplyTrackingService,
    generate_reply_event_id,
)
from chitu_connector.espocrm_sync.send_execution import (
    ControlledSendExecutionService,
    InMemorySendExecutionRegistry,
)
from chitu_connector.espocrm_sync.send_idempotency import SendAttempt, SendRequest
from chitu_connector.espocrm_sync.send_provider import ProviderResultStatus, SendProviderAdapter, SendProviderResult


CREATED_AT = datetime(2026, 7, 14, 15, 0, 0, tzinfo=timezone.utc)


class AcceptingFakeProvider:
    provider_name = "fake-provider"

    def submit(self, request: SendRequest, send_attempt: SendAttempt) -> SendProviderResult:
        return SendProviderResult(
            provider_name=self.provider_name,
            send_attempt_id=f"fake-attempt:{request.send_request_id}",
            idempotency_key=request.idempotency_key,
            request_version=request.request_version,
            status=ProviderResultStatus.ACCEPTED,
        )


class ReplyTrackingBoundaryTests(TestCase):
    def _tracking_service(self) -> tuple[ReplyTrackingService, str, tuple]:
        approvals = InMemoryHumanApprovalRegistry()
        approvals.create_draft_ready("draft-c09-001", "approval-c10-001", CREATED_AT, "draft-service")
        approvals.submit_for_review("approval-c10-001", "operator-001", CREATED_AT + timedelta(minutes=1))
        approvals.approve("approval-c10-001", "reviewer-001", CREATED_AT + timedelta(minutes=2))
        approvals.mark_ready_to_send("approval-c10-001", "release-operator-001", CREATED_AT + timedelta(minutes=3))
        executions = InMemorySendExecutionRegistry()
        execution_service = ControlledSendExecutionService(
            approvals,
            SendProviderAdapter(AcceptingFakeProvider()),
            executions,
        )
        execution = execution_service.execute(
            "approval-c10-001", "lead-001", "fake-provider", "request-c10-4-001", CREATED_AT + timedelta(minutes=4),
        ).execution
        return ReplyTrackingService(executions), execution.send_attempt_id, execution_service.audit_trace("request-c10-4-001")

    def test_create_reply_event_preserves_original_send_trace(self) -> None:
        service, send_attempt_id, send_trace = self._tracking_service()
        received_at = CREATED_AT + timedelta(minutes=5)

        result = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "thread-001", received_at, "contact-001", ReplyStatus.REPLIED,
        )

        self.assertEqual(result.status, ReplyEventReservationStatus.CREATED)
        self.assertEqual(result.event.reply_status, ReplyStatus.REPLIED)
        self.assertEqual(result.event.original_send_trace, send_trace)
        self.assertEqual(
            result.event.reply_event_id,
            generate_reply_event_id(
                "lead-001", "draft-c09-001", send_attempt_id, "thread-001", received_at, "contact-001", ReplyStatus.REPLIED,
            ),
        )

    def test_duplicate_reply_event_is_ignored(self) -> None:
        service, send_attempt_id, _ = self._tracking_service()
        received_at = CREATED_AT + timedelta(minutes=5)
        first = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "thread-001", received_at, "contact-001", ReplyStatus.REPLIED,
        )
        repeated = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "thread-001", received_at, "contact-001", ReplyStatus.REPLIED,
        )

        self.assertEqual(first.status, ReplyEventReservationStatus.CREATED)
        self.assertEqual(repeated.status, ReplyEventReservationStatus.DUPLICATE)
        self.assertEqual(repeated.event, first.event)

    def test_bounced_event_is_recorded_without_follow_up_action(self) -> None:
        service, send_attempt_id, _ = self._tracking_service()

        result = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "thread-002", CREATED_AT, "delivery-system", ReplyStatus.BOUNCED,
        )

        self.assertEqual(result.status, ReplyEventReservationStatus.CREATED)
        self.assertEqual(result.event.reply_status, ReplyStatus.BOUNCED)

    def test_unsubscribed_event_is_recorded_without_workflow_action(self) -> None:
        service, send_attempt_id, _ = self._tracking_service()

        result = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "thread-003", CREATED_AT, "contact-001", ReplyStatus.UNSUBSCRIBED,
        )

        self.assertEqual(result.status, ReplyEventReservationStatus.CREATED)
        self.assertEqual(result.event.reply_status, ReplyStatus.UNSUBSCRIBED)

    def test_invalid_event_is_rejected_before_registry_write(self) -> None:
        service, send_attempt_id, _ = self._tracking_service()

        result = service.track(
            "lead-001", "draft-c09-001", send_attempt_id, "", CREATED_AT, "contact-001", ReplyStatus.REPLIED,
        )

        self.assertEqual(result.status, ReplyEventReservationStatus.REJECTED)
        self.assertEqual(result.reason_code, "INVALID_THREAD_ID")
        self.assertIsNone(result.event)
