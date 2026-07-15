"""Explicit C14.3.1C result command; fixture-only and no-send.

Usage:
    python scripts/acceptance/phase3c14_3_1c_apply_result.py \
        --fixture crm-result-fixture.json --result safe-result.json
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

from chitu_connector.espocrm_sync.send_execution_bridge import BridgeErrorClass, BridgeNormalizedStatus  # noqa: E402
from chitu_connector.espocrm_sync.send_execution_result_adapter import (  # noqa: E402
    CrmSendExecutionResultRecord,
    ExplicitSendExecutionResultAdapter,
    InMemoryCrmSendExecutionResultRepository,
    SendExecutionResultCommand,
)


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explicit C14.3.1C terminal result command; no send is performed.")
    parser.add_argument("--fixture", required=True, type=Path, help="Acceptance-only CRM-shaped SendExecution fixture")
    parser.add_argument("--result", required=True, type=Path, help="Safe result-command JSON")
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    try:
        repository = InMemoryCrmSendExecutionResultRepository(_records(args.fixture))
        command = _command(args.result)
        outcome = ExplicitSendExecutionResultAdapter(repository).apply(command)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        print(json.dumps({"status": "BLOCKED", "reason_code": "RESULT_COMMAND_CONFIGURATION_ERROR"}, sort_keys=True))
        return 2

    print(
        json.dumps(
            {
                "execution_id": outcome.execution_id,
                "reason_code": outcome.reason_code,
                "result_id": outcome.result_id,
                "status": outcome.status.value,
            },
            sort_keys=True,
        )
    )
    return 0 if outcome.status.value in {"APPLIED", "DUPLICATE_RESULT"} else 1


def _records(path: Path) -> tuple[CrmSendExecutionResultRecord, ...]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        CrmSendExecutionResultRecord(
            id=item["id"],
            status=item["status"],
            provider_message_id=item.get("provider_message_id"),
            failure_category=item.get("failure_category"),
            last_error=item.get("last_error"),
        )
        for item in fixture["send_executions"]
    )


def _command(path: Path) -> SendExecutionResultCommand:
    payload = json.loads(path.read_text(encoding="utf-8"))
    occurred_at = datetime.fromisoformat(payload["occurred_at"])
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("occurred_at must include a timezone")
    return SendExecutionResultCommand(
        execution_id=payload["execution_id"],
        provider_attempt_id=payload["provider_attempt_id"],
        normalized_status=BridgeNormalizedStatus(payload["normalized_status"]),
        failure_class=BridgeErrorClass(payload["failure_class"]) if payload["failure_class"] is not None else None,
        error_code=payload["error_code"],
        occurred_at=occurred_at,
        result_id=payload["result_id"],
    )


if __name__ == "__main__":
    raise SystemExit(main())
