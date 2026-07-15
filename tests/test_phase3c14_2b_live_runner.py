"""Offline safety tests for the C14.2B one-shot acceptance runner."""

from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "acceptance" / "phase3c14_2b_live_runner.py"


def load_runner():
    specification = importlib.util.spec_from_file_location("phase3c14_2b_live_runner", RUNNER_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


class OneShotLiveAcceptanceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = load_runner()
        self.ready_environment = {
            "BREVO_API_KEY": "test-only-key",
            "BREVO_SENDER_EMAIL": "sender@example.test",
            "BREVO_TEST_RECIPIENT": "acceptance@example.test",
            "BREVO_ACCEPTANCE_MODE": "true",
        }

    def invoke(self, arguments: list[str], environment: dict[str, str]) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            result = self.runner.main(arguments, environment=environment)
        return result, output.getvalue()

    def test_default_mode_is_dry_run_and_does_not_construct_http_client(self) -> None:
        class UnexpectedHttpClient:
            def __init__(self) -> None:
                raise AssertionError("dry run must not construct HTTP transport")

        self.runner.UrllibBrevoHttpClient = UnexpectedHttpClient

        result, output = self.invoke([], self.ready_environment)

        self.assertEqual(result, 0)
        self.assertIn("MODE=DRY_RUN", output)
        self.assertIn("LIVE_SEND=NOT_INVOKED", output)
        self.assertIn("RECIPIENT_BEFORE_GUARD=c14.2b-original-recipient@example.invalid", output)
        self.assertIn("RECIPIENT_AFTER_GUARD=acceptance@example.test", output)

    def test_acceptance_mode_must_be_true_before_any_live_path(self) -> None:
        environment = dict(self.ready_environment, BREVO_ACCEPTANCE_MODE="false")

        result, output = self.invoke(["--execute-live"], environment)

        self.assertEqual(result, 2)
        self.assertIn("BREVO_ACCEPTANCE_MODE_NOT_TRUE", output)
        self.assertIn("LIVE_SEND=NOT_INVOKED", output)

    def test_acceptance_mode_requires_the_exact_true_value(self) -> None:
        environment = dict(self.ready_environment, BREVO_ACCEPTANCE_MODE="TRUE")

        result, output = self.invoke(["--execute-live"], environment)

        self.assertEqual(result, 2)
        self.assertIn("BREVO_ACCEPTANCE_MODE_NOT_TRUE", output)
        self.assertIn("LIVE_SEND=NOT_INVOKED", output)

    def test_missing_test_recipient_blocks_before_any_live_path(self) -> None:
        environment = dict(self.ready_environment)
        environment.pop("BREVO_TEST_RECIPIENT")

        result, output = self.invoke(["--execute-live"], environment)

        self.assertEqual(result, 2)
        self.assertIn("BREVO_TEST_RECIPIENT_MISSING", output)
        self.assertIn("LIVE_SEND=NOT_INVOKED", output)


if __name__ == "__main__":
    unittest.main()
