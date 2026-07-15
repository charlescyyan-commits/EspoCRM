"""Explicit C14.3.1B-4 acceptance command; it never sends mail.

Usage:
    python scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py EXECUTION_ID \
        --fixture crm-fixture.json --payload-db connector-payload.sqlite

The fixture is a local acceptance-only CRM-shaped read model.  It is not a
CRM API client and this command makes no network request or CRM write.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Sequence


CONNECTOR_ROOT = Path(__file__).resolve().parents[2] / "chitu-connector"
if str(CONNECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(CONNECTOR_ROOT))

from chitu_connector.espocrm_sync.crm_send_execution_bridge_adapter import (  # noqa: E402
    CrmDraftApprovalRecord,
    CrmDraftApprovalStatus,
    CrmSendExecutionBridgeAdapter,
    CrmSendExecutionRecord,
    CrmSendExecutionStatus,
    InMemoryCrmSendExecutionRepository,
)
from chitu_connector.espocrm_sync.explicit_bridge_invocation import (  # noqa: E402
    ExplicitBridgeInvocationService,
    QueueSubmissionBridgeAdapter,
    SqliteApprovedDeliveryPayloadSource,
)
from chitu_connector.espocrm_sync.payload_snapshot import SqlitePayloadSnapshotStore  # noqa: E402
from chitu_connector.espocrm_sync.queue_contract import InMemorySendExecutionQueue  # noqa: E402


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explicit C14.3.1B-4 bridge invocation; no send is performed.")
    parser.add_argument("execution_id", help="Explicit CRM SendExecution identity to validate and enqueue")
    parser.add_argument("--fixture", required=True, type=Path, help="Acceptance-only CRM-shaped JSON read fixture")
    parser.add_argument("--payload-db", required=True, type=Path, help="Connector-owned B-3 SQLite payload database")
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    try:
        executions, approvals, execution_id_by_draft_id = _load_fixture(args.fixture)
        repository = InMemoryCrmSendExecutionRepository(executions=executions, approvals=approvals)
        snapshot_store = SqlitePayloadSnapshotStore(args.payload_db)
        payload_source = SqliteApprovedDeliveryPayloadSource(snapshot_store, execution_id_by_draft_id)
        queue = InMemorySendExecutionQueue()
        bridge_adapter = QueueSubmissionBridgeAdapter(queue)
        adapter = CrmSendExecutionBridgeAdapter(repository, payload_source, bridge_adapter)
        outcome = ExplicitBridgeInvocationService(repository, snapshot_store, adapter).submit(args.execution_id)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        print(json.dumps({"status": "FAILED_SUBMISSION", "reason_code": "INVOCATION_CONFIGURATION_ERROR"}, sort_keys=True))
        return 2

    print(
        json.dumps(
            {
                "execution_id": outcome.execution_id,
                "idempotency_key": outcome.idempotency_key,
                "reason_code": outcome.reason_code,
                "retryable_submission_failure": outcome.retryable_submission_failure,
                "status": outcome.status.value,
            },
            sort_keys=True,
        )
    )
    if outcome.status.value in {"SUBMITTED", "DUPLICATE"}:
        return 0
    if outcome.status.value == "BLOCKED":
        return 1
    return 2


def _load_fixture(
    fixture_path: Path,
) -> tuple[tuple[CrmSendExecutionRecord, ...], tuple[CrmDraftApprovalRecord, ...], dict[str, str]]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    approval_records = tuple(
        CrmDraftApprovalRecord(
            id=item["id"],
            draft_id=item["draft_id"],
            status=CrmDraftApprovalStatus(item["status"]),
            content_hash=item["content_hash"],
        )
        for item in fixture["draft_approvals"]
    )
    execution_records = tuple(
        CrmSendExecutionRecord(
            id=item["id"],
            send_request_id=item["send_request_id"],
            status=CrmSendExecutionStatus(item["status"]),
            draft_approval_id=item["draft_approval_id"],
            created_at=_aware_datetime(item["created_at"]),
        )
        for item in fixture["send_executions"]
    )
    approvals_by_id = {item.id: item for item in approval_records}
    execution_id_by_draft_id: dict[str, str] = {}
    for execution in execution_records:
        approval = approvals_by_id[execution.draft_approval_id]
        if approval.draft_id in execution_id_by_draft_id:
            raise ValueError("DUPLICATE_DRAFT_EXECUTION_MAPPING")
        execution_id_by_draft_id[approval.draft_id] = execution.id
    return execution_records, approval_records, execution_id_by_draft_id


def _aware_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("INVALID_CREATED_AT")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("INVALID_CREATED_AT")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
