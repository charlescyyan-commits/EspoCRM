"""Offline tests for C10.3 controlled send-execution orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import TestCase

from chitu_connector.espocrm_sync.human_approval import InMemoryHumanApprovalRegistry
from chitu_connector.espocrm_sync.send_execution import ControlledSendExecutionService, SendExecutionState
from chitu_connector.espocrm_sync.send_idempotency import SendAttempt, SendRequest
from chitu_connector.espocrm_sync.send_provider import ProviderResultStatus, SendProviderAdapter, SendProviderResult


CREATED_AT = datetime(2026, 7, 14, 14, 0, 0, tzinfo=timezone.utc)


class SequencedFakeProvider:
    provider_name = "fake-provider"

    def __init__(self, *statuses: ProviderResultStatus) -> None:
        self._statuses = list(statuses or (ProviderResultStatus.ACCEPTED,))
        self.calls: list[tuple[SendRequest, SendAttempt]] = []

    def submit(self, request: SendRequest, send_attempt: SendAttempt) -> SendProviderResult:
        self.calls.append((request, send_attempt))
        status = self._statuses.pop(0)
        return SendProviderResult(
            provider_name=self.provider_name,
            send_attempt_id=f"fake-attempt:{request.send_request_id}",
            idempotency_key=request.idempotency_key,
            request_version=request.request_version,
            status=status,
            reason_code="FAKE_PROVIDER_FAILED" if status is ProviderResultStatus.FAILED else None,
        )


class ControlledSendExecutionTests(TestCase):
    def _approval_registry(self, *, ready: bool) -> InMemoryHumanApprovalRegistry:
        approvals = InMemoryHumanApprovalRegistry()
        approvals.create_draft_ready("draft-c09-001", "approval-c10-001", CREATED_AT, "draft-service")
        if ready:
            approvals.submit_for_review("approval-c10-001", "operator-001", CREATED_AT + timedelta(minutes=1))
            approvals.approve("approval-c10-001", "reviewer-001", CREATED_AT + timedelta(minutes=2))
            approvals.mark_ready_to_send("approval-c10-001", "release-operator-001", CREATED_AT + timedelta(minutes=3))
        return approvals

    def _service(self, provider: SequencedFakeProvider, *, ready: bool = True) -> ControlledSendExecutionService:
        return ControlledSendExecutionService(self._approval_registry(ready=ready), SendProviderAdapter(provider))

    def test_approved_draft_can_execute_and_persists_complete_audit_trace(self) -> None:
        provider = SequencedFakeProvider(ProviderResultStatus.ACCEPTED)
        service = self._service(provider)
        timestamp = CREATED_AT + timedelta(minutes=4)

        outcome = service.execute("approval-c10-001", "lead-001", "fake-provider", "request-c10-3-001", timestamp)

        self.assertIsNone(outcome.reason_code)
        self.assertEqual(outcome.execution.state, SendExecutionState.SENT)
        self.assertEqual(outcome.execution.draft_id, "draft-c09-001")
        self.assertEqual(outcome.execution.send_request.send_request_id, "request-c10-3-001")
        self.assertEqual(outcome.execution.send_attempt_id, "fake-attempt:request-c10-3-001")
        trace = service.audit_trace("request-c10-3-001")
        self.assertEqual([item.state for item in trace], [
            SendExecutionState.READY_TO_SEND,
            SendExecutionState.SUBMITTED,
            SendExecutionState.PROCESSING,
            SendExecutionState.SENT,
        ])
        self.assertEqual(trace[-1].draft_id, "draft-c09-001")
        self.assertEqual(trace[-1].approval_id, "approval-c10-001")
        self.assertEqual(trace[-1].send_request_id, "request-c10-3-001")
        self.assertEqual(trace[-1].send_attempt_id, "fake-attempt:request-c10-3-001")
        self.assertEqual(trace[-1].provider, "fake-provider")
        self.assertEqual(trace[-1].result, ProviderResultStatus.ACCEPTED)
        self.assertEqual(trace[-1].timestamp, timestamp)

    def test_non_approved_draft_is_rejected_before_request_or_provider_call(self) -> None:
        provider = SequencedFakeProvider()
        service = self._service(provider, ready=False)

        outcome = service.execute("approval-c10-001", "lead-001", "fake-provider", "request-c10-3-001", CREATED_AT)

        self.assertIsNone(outcome.execution)
        self.assertEqual(outcome.reason_code, "APPROVAL_NOT_READY")
        self.assertEqual(provider.calls, [])

    def test_duplicate_execution_is_prevented(self) -> None:
        provider = SequencedFakeProvider()
        service = self._service(provider)
        first = service.execute("approval-c10-001", "lead-001", "fake-provider", "request-c10-3-duplicate", CREATED_AT)
        repeated = service.execute("approval-c10-001", "lead-001", "fake-provider", "request-c10-3-duplicate", CREATED_AT)

        self.assertEqual(first.execution, repeated.execution)
        self.assertTrue(repeated.duplicate)
        self.assertEqual(repeated.reason_code, "DUPLICATE_EXECUTION")
        self.assertEqual(len(provider.calls), 1)

    def test_provider_accepted_maps_to_sent(self) -> None:
        provider = SequencedFakeProvider(ProviderResultStatus.ACCEPTED)

        outcome = self._service(provider).execute(
            "approval-c10-001", "lead-001", "fake-provider", "request-c10-3-accepted", CREATED_AT,
        )

        self.assertEqual(outcome.execution.state, SendExecutionState.SENT)
        self.assertEqual(outcome.execution.result_status, ProviderResultStatus.ACCEPTED)

    def test_provider_failed_maps_to_failed(self) -> None:
        provider = SequencedFakeProvider(ProviderResultStatus.FAILED)

        outcome = self._service(provider).execute(
            "approval-c10-001", "lead-001", "fake-provider", "request-c10-3-failed", CREATED_AT,
        )

        self.assertEqual(outcome.execution.state, SendExecutionState.FAILED)
        self.assertEqual(outcome.execution.result_status, ProviderResultStatus.FAILED)
        self.assertEqual(outcome.execution.reason_code, "FAKE_PROVIDER_FAILED")

    def test_retry_after_failure_requires_and_uses_new_send_request_id(self) -> None:
        provider = SequencedFakeProvider(ProviderResultStatus.FAILED, ProviderResultStatus.ACCEPTED)
        service = self._service(provider)
        first = service.execute("approval-c10-001", "lead-001", "fake-provider", "request-c10-3-failed", CREATED_AT)
        retry = service.execute(
            "approval-c10-001", "lead-001", "fake-provider", "request-c10-3-retry", CREATED_AT + timedelta(minutes=1),
        )

        self.assertEqual(first.execution.state, SendExecutionState.FAILED)
        self.assertEqual(retry.execution.state, SendExecutionState.SENT)
        self.assertNotEqual(first.execution.send_request.idempotency_key, retry.execution.send_request.idempotency_key)
        self.assertEqual(len(provider.calls), 2)
