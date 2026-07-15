"""C14.3.1B-2 tests for the CRM-side bridge adapter boundary."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.crm_send_execution_bridge_adapter import (
    ApprovedDeliveryPayload,
    BridgeSubmissionStatus,
    CrmDraftApprovalRecord,
    CrmDraftApprovalStatus,
    CrmSendExecutionBridgeAdapter,
    CrmSendExecutionRecord,
    CrmSendExecutionStatus,
    InMemoryApprovedDeliveryPayloadSource,
    InMemoryCrmSendExecutionRepository,
)
from chitu_connector.espocrm_sync.send_execution_bridge import (
    InMemorySendExecutionBridgeFixture,
)


NOW = datetime(2026, 7, 14, 13, 0, tzinfo=timezone.utc)
CONTENT_HASH = "b" * 64


def approval() -> CrmDraftApprovalRecord:
    return CrmDraftApprovalRecord(
        id="approval-001",
        draft_id="draft-001",
        status=CrmDraftApprovalStatus.APPROVED,
        content_hash=CONTENT_HASH,
    )


def execution() -> CrmSendExecutionRecord:
    return CrmSendExecutionRecord(
        id="execution-001",
        send_request_id="request-001",
        status=CrmSendExecutionStatus.READY,
        draft_approval_id="approval-001",
        created_at=NOW,
    )


def payload() -> ApprovedDeliveryPayload:
    return ApprovedDeliveryPayload(
        draft_id="draft-001",
        content_hash=CONTENT_HASH,
        recipient="approved-test@example.invalid",
        subject="Approved boundary test",
        body="C14.3.1B-2 approved delivery content.",
        campaign_reference="campaign-boundary-001",
        generated_at=NOW,
    )


def adapter(
    *,
    crm_execution: CrmSendExecutionRecord | None = None,
    crm_approval: CrmDraftApprovalRecord | None = None,
    approved_payload: ApprovedDeliveryPayload | None = None,
    bridge: object | None = None,
) -> tuple[CrmSendExecutionBridgeAdapter, InMemorySendExecutionBridgeFixture]:
    fixture = bridge if isinstance(bridge, InMemorySendExecutionBridgeFixture) else InMemorySendExecutionBridgeFixture()
    repository = InMemoryCrmSendExecutionRepository(
        executions=(crm_execution or execution(),),
        approvals=(crm_approval or approval(),),
    )
    source = InMemoryApprovedDeliveryPayloadSource((approved_payload or payload(),))
    return CrmSendExecutionBridgeAdapter(repository, source, bridge or fixture), fixture


class FailingBridge:
    def enqueue(self, request: object) -> object:
        raise RuntimeError("simulated bridge submission outage")

    def record_result(self, result: object) -> object:
        raise AssertionError("result callback is outside B-2 scope")


class CrmSendExecutionBridgeAdapterTests(unittest.TestCase):
    def test_approved_ready_execution_creates_bridge_request(self) -> None:
        service, bridge = adapter()

        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.SUBMITTED)
        self.assertIsNotNone(outcome.request)
        self.assertIsNotNone(outcome.receipt)
        self.assertFalse(outcome.receipt.duplicate)
        self.assertEqual(outcome.request.execution_id, "execution-001")
        self.assertEqual(outcome.request.content_hash, CONTENT_HASH)
        self.assertEqual(bridge.request_for("execution-001"), outcome.request)

    def test_duplicate_trigger_uses_same_idempotency_key(self) -> None:
        service, bridge = adapter()

        first = service.submit("execution-001")
        second = service.submit("execution-001")

        self.assertEqual(first.status, BridgeSubmissionStatus.SUBMITTED)
        self.assertEqual(second.status, BridgeSubmissionStatus.DUPLICATE)
        self.assertEqual(first.request.idempotency_key, second.request.idempotency_key)
        self.assertTrue(second.receipt.duplicate)
        self.assertEqual(bridge.request_for("execution-001"), first.request)

    def test_missing_content_blocks_enqueue(self) -> None:
        incomplete_payload = replace(payload(), body="")
        service, bridge = adapter(approved_payload=incomplete_payload)

        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "MISSING_APPROVED_BODY")
        self.assertIsNone(outcome.request)
        self.assertIsNone(bridge.request_for("execution-001"))

    def test_missing_recipient_blocks_enqueue(self) -> None:
        incomplete_payload = replace(payload(), recipient="")
        service, bridge = adapter(approved_payload=incomplete_payload)

        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "MISSING_APPROVED_RECIPIENT")
        self.assertIsNone(outcome.request)
        self.assertIsNone(bridge.request_for("execution-001"))

    def test_bridge_failure_does_not_mark_execution_sent(self) -> None:
        crm_execution = execution()
        service, _ = adapter(crm_execution=crm_execution, bridge=FailingBridge())

        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.FAILED_SUBMISSION)
        self.assertEqual(outcome.reason_code, "BRIDGE_SUBMISSION_UNAVAILABLE")
        self.assertEqual(crm_execution.status, CrmSendExecutionStatus.READY)
        self.assertEqual(outcome.request.execution_id, crm_execution.id)

    def test_non_approved_or_non_ready_records_are_rejected_before_submission(self) -> None:
        rejected_approval = replace(approval(), status=CrmDraftApprovalStatus.REJECTED)
        service, bridge = adapter(crm_approval=rejected_approval)
        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "DRAFT_NOT_APPROVED")
        self.assertIsNone(bridge.request_for("execution-001"))

        created_execution = replace(execution(), status=CrmSendExecutionStatus.CREATED)
        service, bridge = adapter(crm_execution=created_execution)
        outcome = service.submit("execution-001")

        self.assertEqual(outcome.status, BridgeSubmissionStatus.BLOCKED)
        self.assertEqual(outcome.reason_code, "SEND_EXECUTION_NOT_READY")
        self.assertIsNone(bridge.request_for("execution-001"))

    def test_adapter_has_no_queue_worker_provider_or_php_hook_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "crm_send_execution_bridge_adapter.py"
        ).read_text(encoding="utf-8")
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )

        for forbidden in (
            "queue_contract",
            "worker_execution",
            "provider_contract",
            "brevo",
            "urllib",
            "requests",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, imports)


if __name__ == "__main__":
    unittest.main()
