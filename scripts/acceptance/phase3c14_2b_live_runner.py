"""One-shot C14.2B live Brevo acceptance runner.

The default mode is dry-run validation and never opens an HTTP transport.  A
single live invocation requires --execute-live plus the acceptance-recipient
guard supplied entirely through the process environment.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import sys
from typing import Mapping, Sequence
from uuid import uuid4


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
CONNECTOR_ROOT = WORKSPACE_ROOT / "chitu-connector"
if str(CONNECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(CONNECTOR_ROOT))

from chitu_connector.espocrm_sync.brevo_http import UrllibBrevoHttpClient
from chitu_connector.espocrm_sync.brevo_provider import BrevoConfiguration, BrevoProviderAdapter
from chitu_connector.espocrm_sync.queue_contract import InMemorySendExecutionQueue
from chitu_connector.espocrm_sync.worker_execution import (
    InMemorySendExecutionWorkStore,
    SendExecutionWorkItem,
    SendExecutionWorker,
    WorkExecutionStatus,
)


TEST_RECIPIENT_BEFORE_GUARD = "c14.2b-original-recipient@example.invalid"
TEST_SUBJECT = "[C14.2B TEST EMAIL] One-shot live acceptance"
TEST_BODY = "C14.2B TEST EMAIL. This synthetic message validates one controlled provider path."
WORKER_ID = "c14.2b-one-shot-worker"


@dataclass(frozen=True, slots=True)
class AcceptancePlan:
    send_execution_id: str
    request_id: str
    created_at: datetime
    recipient_before_guard: str
    subject: str
    body: str
    draft_hash: str


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one controlled C14.2B Brevo acceptance request.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the protected environment and print the planned one-shot request (default).",
    )
    mode.add_argument(
        "--execute-live",
        action="store_true",
        help="Perform exactly one Queue -> Worker -> Brevo adapter request.",
    )
    return parser.parse_args(arguments)


def main(
    arguments: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> int:
    """Validate a one-shot plan, optionally executing its single provider request."""

    args = parse_args(arguments)
    values = os.environ if environment is None else environment
    configuration = BrevoConfiguration.from_environment(values)
    failure_code = _acceptance_failure(configuration, values.get("BREVO_ACCEPTANCE_MODE"))
    if failure_code is not None:
        _print_blocked(failure_code)
        return 2

    plan = _new_plan()
    _print_plan(plan, configuration.resolve_recipient(plan.recipient_before_guard))

    if not args.execute_live:
        print("MODE=DRY_RUN")
        print("LIVE_SEND=NOT_INVOKED")
        return 0

    print("MODE=EXECUTE_LIVE")
    return _execute_single_plan(plan, configuration)


def _acceptance_failure(configuration: BrevoConfiguration, acceptance_mode: object) -> str | None:
    if acceptance_mode != "true" or not configuration.acceptance_mode:
        return "BREVO_ACCEPTANCE_MODE_NOT_TRUE"
    if not configuration.test_recipient:
        return "BREVO_TEST_RECIPIENT_MISSING"
    return configuration.missing_configuration_code()


def _new_plan() -> AcceptancePlan:
    created_at = datetime.now(timezone.utc)
    unique_id = uuid4().hex
    draft_hash = sha256(f"{TEST_SUBJECT}\n{TEST_BODY}".encode("utf-8")).hexdigest()
    return AcceptancePlan(
        send_execution_id=f"c14.2b-send-execution-{unique_id}",
        request_id=f"c14.2b-request-{unique_id}",
        created_at=created_at,
        recipient_before_guard=TEST_RECIPIENT_BEFORE_GUARD,
        subject=TEST_SUBJECT,
        body=TEST_BODY,
        draft_hash=draft_hash,
    )


def _execute_single_plan(plan: AcceptancePlan, configuration: BrevoConfiguration) -> int:
    """Create one in-memory work item and invoke the worker exactly once."""

    queue = InMemorySendExecutionQueue()
    queue_item = queue.enqueue(plan.send_execution_id, plan.created_at)
    execution = SendExecutionWorkItem(
        send_execution_id=plan.send_execution_id,
        request_id=plan.request_id,
        status=WorkExecutionStatus.READY,
        recipient=plan.recipient_before_guard,
        subject=plan.subject,
        body=plan.body,
        draft_hash=plan.draft_hash,
        created_at=plan.created_at,
    )
    store = InMemorySendExecutionWorkStore((execution,))
    adapter = BrevoProviderAdapter(configuration, UrllibBrevoHttpClient())
    worker = SendExecutionWorker(queue, store, WORKER_ID, adapter)

    outcome = worker.process(queue_item, datetime.now(timezone.utc))
    result = outcome.provider_result
    if result is None:
        print(f"PROVIDER_RESULT=NOT_RETURNED reason={outcome.reason_code or 'UNKNOWN'}")
        return 3

    safe_error = result.error.safe_code if result.error is not None else "NONE"
    print(
        "PROVIDER_RESULT="
        f"success={str(result.success).upper()} "
        f"status={result.status} "
        f"provider_status={result.provider_status} "
        f"error={safe_error}"
    )
    if result.provider_message_id:
        print(f"EXTERNAL_MESSAGE_ID={result.provider_message_id}")
    else:
        print("EXTERNAL_MESSAGE_ID=NONE")
    return 0 if result.success else 3


def _print_plan(plan: AcceptancePlan, recipient_after_guard: str) -> None:
    print(f"JOB_ID={plan.send_execution_id}")
    print(f"RECIPIENT_BEFORE_GUARD={plan.recipient_before_guard}")
    print(f"RECIPIENT_AFTER_GUARD={recipient_after_guard}")


def _print_blocked(reason: str) -> None:
    print(f"C14_2B_RUNNER=BLOCKED reason={reason}")
    print("LIVE_SEND=NOT_INVOKED")


if __name__ == "__main__":
    raise SystemExit(main())
