"""C14.3.1C explicit safe result-command boundary tests."""

from datetime import datetime, timezone
from pathlib import Path
import unittest

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


NOW = datetime(2026, 7, 14, 16, 0, tzinfo=timezone.utc)


def command(
    *,
    execution_id: str = "execution-result-001",
    status: BridgeNormalizedStatus = BridgeNormalizedStatus.SENT,
    provider_attempt_id: str | None = "provider-attempt-001",
    failure_class: BridgeErrorClass | None = None,
    error_code: str | None = None,
) -> SendExecutionResultCommand:
    bridge = SendExecutionBridgeResult(
        execution_id=execution_id,
        provider_attempt_id=provider_attempt_id,
        normalized_status=status,
        error_class=failure_class,
        error_code=error_code,
        occurred_at=NOW,
    )
    return SendExecutionResultCommand.from_bridge_result(bridge)


def adapter(
    record: CrmSendExecutionResultRecord | None = None,
) -> tuple[ExplicitSendExecutionResultAdapter, InMemoryCrmSendExecutionResultRepository]:
    repository = InMemoryCrmSendExecutionResultRepository(
        (record or CrmSendExecutionResultRecord(id="execution-result-001", status="READY"),)
    )
    return ExplicitSendExecutionResultAdapter(repository), repository


class ExplicitResultAdapterTests(unittest.TestCase):
    def test_success_result_updates_send_execution_only(self) -> None:
        service, repository = adapter()

        outcome = service.apply(command())

        self.assertEqual(outcome.status, ResultCommandStatus.APPLIED)
        self.assertEqual(repository.get("execution-result-001").status, "SENT")
        self.assertEqual(repository.get("execution-result-001").provider_message_id, "provider-attempt-001")
        self.assertIsNone(repository.get("execution-result-001").failure_category)
        self.assertIsNone(repository.get("execution-result-001").last_error)
        self.assertEqual(repository.compare_and_set_count, 1)

    def test_failed_result_updates_send_execution_with_safe_failure_only(self) -> None:
        service, repository = adapter()
        failed = command(
            status=BridgeNormalizedStatus.FAILED,
            provider_attempt_id=None,
            failure_class=BridgeErrorClass.AUTH,
            error_code="BREVO_AUTH_ERROR",
        )

        outcome = service.apply(failed)

        self.assertEqual(outcome.status, ResultCommandStatus.APPLIED)
        record = repository.get("execution-result-001")
        self.assertEqual(record.status, "FAILED")
        self.assertEqual(record.failure_category, "AUTH")
        self.assertEqual(record.last_error, "BREVO_AUTH_ERROR")
        self.assertIsNone(record.provider_message_id)

    def test_duplicate_result_is_ignored_without_second_update(self) -> None:
        service, repository = adapter()
        first = service.apply(command())
        duplicate = service.apply(command())

        self.assertEqual(first.status, ResultCommandStatus.APPLIED)
        self.assertEqual(duplicate.status, ResultCommandStatus.DUPLICATE_RESULT)
        self.assertEqual(first.result_id, duplicate.result_id)
        self.assertEqual(repository.compare_and_set_count, 1)

    def test_old_failed_result_cannot_downgrade_sent_execution(self) -> None:
        sent = CrmSendExecutionResultRecord(
            id="execution-result-001",
            status="SENT",
            provider_message_id="provider-attempt-001",
        )
        service, repository = adapter(sent)
        old_failure = command(
            status=BridgeNormalizedStatus.FAILED,
            provider_attempt_id=None,
            failure_class=BridgeErrorClass.PROVIDER,
            error_code="BREVO_PROVIDER_ERROR",
        )

        outcome = service.apply(old_failure)

        self.assertEqual(outcome.status, ResultCommandStatus.RESULT_CONFLICT)
        self.assertEqual(repository.get("execution-result-001"), sent)
        self.assertEqual(repository.compare_and_set_count, 0)

    def test_network_error_classification_is_preserved_without_retry(self) -> None:
        service, repository = adapter()
        network_failure = command(
            status=BridgeNormalizedStatus.FAILED,
            provider_attempt_id=None,
            failure_class=BridgeErrorClass.NETWORK,
            error_code="BREVO_NETWORK_ERROR",
        )

        outcome = service.apply(network_failure)

        self.assertEqual(outcome.status, ResultCommandStatus.APPLIED)
        record = repository.get("execution-result-001")
        self.assertEqual(record.status, "FAILED")
        self.assertEqual(record.failure_category, "NETWORK")
        self.assertEqual(record.last_error, "BREVO_NETWORK_ERROR")

    def test_result_id_is_stable_for_same_terminal_result(self) -> None:
        self.assertEqual(command().result_id, command().result_id)

    def test_worker_cannot_write_crm_entities(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "worker_execution.py"
        ).read_text(encoding="utf-8")
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )

        for forbidden in (
            "crm_send_execution_bridge_adapter",
            "explicit_bridge_invocation",
            "send_execution_result_adapter",
            "EmailEvent",
            "ReplyEvent",
            "Espo",
            "requests",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, imports)

    def test_adapter_has_no_worker_queue_provider_brevo_or_event_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (
            root
            / "chitu-connector"
            / "chitu_connector"
            / "espocrm_sync"
            / "send_execution_result_adapter.py"
        ).read_text(encoding="utf-8")
        imports = "\n".join(
            line.strip()
            for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )

        for forbidden in (
            "worker_execution",
            "queue_contract",
            "provider_contract",
            "brevo",
            "EmailEvent",
            "ReplyEvent",
            "urllib",
            "requests",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, imports)


if __name__ == "__main__":
    unittest.main()
