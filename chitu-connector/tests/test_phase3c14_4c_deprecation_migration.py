"""C14.4C Phase 1: legacy writer deprecation and bridge-preference coverage."""

from __future__ import annotations

from datetime import datetime, timezone
import warnings
from unittest import TestCase

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
from chitu_connector.espocrm_sync.send_execution_bridge import InMemorySendExecutionBridgeFixture


NOW = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
CONTENT_HASH = "4" * 64


class DeprecationMigrationTests(TestCase):
    def test_internal_execution_submission_prefers_c14_3_bridge_without_legacy_warning(self) -> None:
        approval = CrmDraftApprovalRecord(
            id="approval-c14-4c-001",
            draft_id="draft-c14-4c-001",
            status=CrmDraftApprovalStatus.APPROVED,
            content_hash=CONTENT_HASH,
        )
        execution = CrmSendExecutionRecord(
            id="execution-c14-4c-001",
            send_request_id="request-c14-4c-001",
            status=CrmSendExecutionStatus.READY,
            draft_approval_id=approval.id,
            created_at=NOW,
        )
        adapter = CrmSendExecutionBridgeAdapter(
            InMemoryCrmSendExecutionRepository(executions=(execution,), approvals=(approval,)),
            InMemoryApprovedDeliveryPayloadSource((ApprovedDeliveryPayload(
                draft_id=approval.draft_id,
                content_hash=CONTENT_HASH,
                recipient="c14-4c@example.invalid",
                subject="C14.4C bridge preference",
                body="Synthetic bridge-only payload.",
                campaign_reference="c14-4c",
                generated_at=NOW,
            ),)),
            InMemorySendExecutionBridgeFixture(),
        )

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always", DeprecationWarning)
            outcome = adapter.submit(execution.id)

        self.assertEqual(outcome.status, BridgeSubmissionStatus.SUBMITTED)
        self.assertEqual([item for item in captured if issubclass(item.category, DeprecationWarning)], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
