"""C14.3.1D freeze checks for terminal failure projection behavior.

These checks deliberately exercise the explicit C14.3.1C result boundary with
synthetic records only.  They do not invoke a Worker, Queue, Provider, CRM
runtime, or delivery transport.
"""

from datetime import datetime, timezone
from pathlib import Path
import unittest

from chitu_connector.espocrm_sync.provider_contract import SendResultStatus
from chitu_connector.espocrm_sync.send_execution_bridge import (
    BridgeErrorClass,
    BridgeNormalizedStatus,
    SendExecutionBridgeResult,
)
from chitu_connector.espocrm_sync.send_execution_result_adapter import (
    CrmSendExecutionResultRecord,
    ExplicitSendExecutionResultAdapter,
    InMemoryCrmSendExecutionResultRepository,
    ResultCommandStatus,
    SendExecutionResultCommand,
)


NOW = datetime(2026, 7, 14, 17, 0, tzinfo=timezone.utc)
EXECUTION_ID = "execution-freeze-001"


def result_command(
    *,
    status: BridgeNormalizedStatus,
    provider_attempt_id: str | None = None,
    failure_class: BridgeErrorClass | None = None,
    error_code: str | None = None,
) -> SendExecutionResultCommand:
    return SendExecutionResultCommand.from_bridge_result(
        SendExecutionBridgeResult(
            execution_id=EXECUTION_ID,
            provider_attempt_id=provider_attempt_id,
            normalized_status=status,
            error_class=failure_class,
            error_code=error_code,
            occurred_at=NOW,
        )
    )


def ready_adapter() -> tuple[ExplicitSendExecutionResultAdapter, InMemoryCrmSendExecutionResultRepository]:
    repository = InMemoryCrmSendExecutionResultRepository(
        (CrmSendExecutionResultRecord(id=EXECUTION_ID, status="READY"),)
    )
    return ExplicitSendExecutionResultAdapter(repository), repository


class FailureProjectionHardeningTests(unittest.TestCase):
    def test_ready_allows_each_terminal_state_once(self) -> None:
        success_adapter, success_repository = ready_adapter()
        failure_adapter, failure_repository = ready_adapter()

        success = success_adapter.apply(
            result_command(
                status=BridgeNormalizedStatus.SENT,
                provider_attempt_id="provider-attempt-success",
            )
        )
        failure = failure_adapter.apply(
            result_command(
                status=BridgeNormalizedStatus.FAILED,
                failure_class=BridgeErrorClass.VALIDATION,
                error_code="BREVO_VALIDATION_ERROR",
            )
        )

        self.assertEqual(success.status, ResultCommandStatus.APPLIED)
        self.assertEqual(success_repository.get(EXECUTION_ID).status, "SENT")
        self.assertEqual(failure.status, ResultCommandStatus.APPLIED)
        self.assertEqual(failure_repository.get(EXECUTION_ID).status, "FAILED")

    def test_replaying_same_result_is_noop_without_second_projection_source_save(self) -> None:
        service, repository = ready_adapter()
        command = result_command(
            status=BridgeNormalizedStatus.FAILED,
            failure_class=BridgeErrorClass.NETWORK,
            error_code="BREVO_NETWORK_ERROR",
        )

        first = service.apply(command)
        replay = service.apply(command)

        self.assertEqual(first.status, ResultCommandStatus.APPLIED)
        self.assertEqual(replay.status, ResultCommandStatus.DUPLICATE_RESULT)
        self.assertEqual(repository.compare_and_set_count, 1)
        self.assertEqual(replay.record, first.record)

    def test_old_failure_cannot_downgrade_sent_execution_or_trigger_projection(self) -> None:
        sent = CrmSendExecutionResultRecord(
            id=EXECUTION_ID,
            status="SENT",
            provider_message_id="provider-attempt-success",
        )
        repository = InMemoryCrmSendExecutionResultRepository((sent,))
        service = ExplicitSendExecutionResultAdapter(repository)

        outcome = service.apply(
            result_command(
                status=BridgeNormalizedStatus.FAILED,
                failure_class=BridgeErrorClass.PROVIDER,
                error_code="BREVO_PROVIDER_ERROR",
            )
        )

        self.assertEqual(outcome.status, ResultCommandStatus.RESULT_CONFLICT)
        self.assertEqual(repository.get(EXECUTION_ID), sent)
        self.assertEqual(repository.compare_and_set_count, 0)

    def test_failed_execution_cannot_be_promoted_to_sent_without_authorized_priority(self) -> None:
        failed = CrmSendExecutionResultRecord(
            id=EXECUTION_ID,
            status="FAILED",
            failure_category="NETWORK",
            last_error="BREVO_NETWORK_ERROR",
        )
        repository = InMemoryCrmSendExecutionResultRepository((failed,))
        service = ExplicitSendExecutionResultAdapter(repository)

        outcome = service.apply(
            result_command(
                status=BridgeNormalizedStatus.SENT,
                provider_attempt_id="late-provider-attempt",
            )
        )

        self.assertEqual(outcome.status, ResultCommandStatus.RESULT_CONFLICT)
        self.assertEqual(repository.get(EXECUTION_ID), failed)
        self.assertEqual(repository.compare_and_set_count, 0)

    def test_network_ambiguity_remains_terminal_failure_without_retry_side_effect(self) -> None:
        service, repository = ready_adapter()
        command = result_command(
            status=BridgeNormalizedStatus.FAILED,
            failure_class=BridgeErrorClass.NETWORK,
            error_code="BREVO_NETWORK_ERROR",
        )

        outcome = service.apply(command)
        record = repository.get(EXECUTION_ID)

        self.assertEqual(SendResultStatus.RETRYABLE_FAILURE.value, "RETRYABLE_FAILURE")
        self.assertEqual(outcome.status, ResultCommandStatus.APPLIED)
        self.assertEqual(record.status, "FAILED")
        self.assertEqual(record.failure_category, "NETWORK")
        self.assertEqual(record.last_error, "BREVO_NETWORK_ERROR")

        root = Path(__file__).resolve().parents[1]
        result_source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "send_execution_result_adapter.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn(".retry(", result_source.casefold())
        self.assertNotIn(".enqueue(", result_source.casefold())

    def test_result_boundary_has_no_direct_lead_or_event_writer(self) -> None:
        root = Path(__file__).resolve().parents[1]
        python_source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "send_execution_result_adapter.py"
        ).read_text(encoding="utf-8")
        php_source = (
            root
            / "crm-extension"
            / "files"
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Services"
            / "SendExecutionResultAdapterService.php"
        ).read_text(encoding="utf-8")

        self.assertNotIn("peEmailStatus", python_source)
        self.assertNotIn("peEmailStatus", php_source)
        self.assertNotIn("EmailEvent", php_source)
        self.assertNotIn("ReplyEvent", php_source)
        self.assertNotIn("getEntity('Lead'", php_source)
        self.assertNotIn('getEntity("Lead"', php_source)
        self.assertIn("saveEntity($execution)", php_source)

    def test_safe_result_surfaces_contain_no_secrets_or_recipient_content(self) -> None:
        root = Path(__file__).resolve().parents[1]
        sources = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "send_execution_result_adapter.py",
            root
            / "crm-extension"
            / "files"
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Services"
            / "SendExecutionResultAdapterService.php",
            root / "scripts" / "acceptance" / "phase3c14_3_1c_apply_result.py",
        )
        forbidden_markers = (
            "api_key",
            "authorization",
            "bearer ",
            "password",
            "secret",
            "recipient",
            "subject",
            "body",
        )

        for source_path in sources:
            source = source_path.read_text(encoding="utf-8").casefold()
            for marker in forbidden_markers:
                with self.subTest(source=source_path.name, marker=marker):
                    self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
