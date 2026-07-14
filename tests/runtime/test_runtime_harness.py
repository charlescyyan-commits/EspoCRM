from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_harness import (  # noqa: E402
    ApiResponse, CleanupEngine, FixtureRegistry, RuntimeConfig, RuntimeDependencyError, RuntimeHarnessError,
    RuntimeRestClient, RuntimeSafetyError, new_run_id, run_with_cleanup, validate_run_id,
)


def enabled_env(**overrides: str) -> dict[str, str]:
    env = {
        "ESPOCRM_RUNTIME_TEST_ENABLED": "true", "ESPOCRM_BASE_URL": "http://localhost:8080/api/v1",
        "ESPOCRM_API_KEY": "test-key", "ESPOCRM_RUNTIME_TEST_PREFIX": "CHITU_RT", "ESPOCRM_RUNTIME_TEST_TIMEOUT": "20",
    }
    env.update(overrides)
    return env


class FakeClient:
    def __init__(self, records: dict[tuple[str, str], ApiResponse]) -> None:
        self.records = records
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, path: str, **_: object) -> ApiResponse:
        self.calls.append((method, path))
        key = tuple(path.split("/", 1))
        if method == "DELETE":
            self.records[key] = ApiResponse(404, None)
            return ApiResponse(200, {})
        return self.records.get(key, ApiResponse(404, None))


class RuntimeHarnessTests(unittest.TestCase):
    def test_disabled_guard_blocks_before_client_creation(self) -> None:
        with self.assertRaises(RuntimeSafetyError):
            RuntimeConfig.from_environment({})

    def test_missing_credential_is_dependency_error(self) -> None:
        env = enabled_env(ESPOCRM_API_KEY="")
        with self.assertRaises(RuntimeDependencyError):
            RuntimeConfig.from_environment(env)

    def test_production_and_credential_urls_are_rejected(self) -> None:
        with self.assertRaises(RuntimeSafetyError):
            RuntimeConfig.from_environment(enabled_env(ESPOCRM_BASE_URL="https://production.example"))
        with self.assertRaises(RuntimeSafetyError):
            RuntimeConfig.from_environment(enabled_env(ESPOCRM_BASE_URL="http://user:pass@localhost:8080/api"))

    def test_run_id_and_prefix_are_safe(self) -> None:
        run_id = new_run_id("CHITU_RT")
        self.assertRegex(run_id, r"^CHITU_RT_\d{8}T\d{6}Z_[0-9A-F]{8}$")
        self.assertEqual(validate_run_id(run_id), run_id)
        with self.assertRaises(Exception):
            validate_run_id("unsafe-run-id")
        with self.assertRaises(Exception):
            RuntimeConfig.from_environment(enabled_env(ESPOCRM_RUNTIME_TEST_PREFIX="bad prefix"))

    def test_registry_persists_fixture_immediately_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = FixtureRegistry.create(Path(directory), "CHITU_RT_20260713T000000Z_ABCDEF12")
            registry.register("Lead", "lead-1", registry.run_id, "smoke")
            raw = json.loads(registry.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["fixtures"][0]["recordId"], "lead-1")
            self.assertNotIn("test-key", registry.path.read_text(encoding="utf-8"))

    def test_preview_never_calls_rest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = FixtureRegistry.create(Path(directory), "CHITU_RT_20260713T000000Z_ABCDEF12")
            registry.register("Lead", "lead-1", registry.run_id, "smoke")
            client = FakeClient({})
            preview = CleanupEngine(client, registry).preview()
            self.assertEqual(preview[0]["recordId"], "lead-1")
            self.assertEqual(client.calls, [])

    def test_cleanup_refuses_marker_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = FixtureRegistry.create(Path(directory), "CHITU_RT_20260713T000000Z_ABCDEF12")
            registry.register("Lead", "lead-1", registry.run_id, "smoke")
            client = FakeClient({("Lead", "lead-1"): ApiResponse(200, {"name": "unrelated"})})
            result = CleanupEngine(client, registry).cleanup()
            self.assertEqual(result[0].cleanupResult, "FAILED")
            self.assertNotIn(("DELETE", "Lead/lead-1"), client.calls)

    def test_cleanup_continues_after_one_failure_and_removes_safe_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = FixtureRegistry.create(Path(directory), "CHITU_RT_20260713T000000Z_ABCDEF12")
            registry.register("Lead", "unsafe", registry.run_id, "smoke")
            registry.register("ResearchEvidence", "safe", registry.run_id, "smoke")
            client = FakeClient({
                ("Lead", "unsafe"): ApiResponse(200, {"name": "other"}),
                ("ResearchEvidence", "safe"): ApiResponse(200, {"name": registry.run_id}),
            })
            results = CleanupEngine(client, registry).cleanup()
            self.assertEqual({item.recordId: item.cleanupResult for item in results}["unsafe"], "FAILED")
            self.assertEqual({item.recordId: item.cleanupResult for item in results}["safe"], "CLEANED")

    def test_external_registry_is_rejected_without_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime-fixtures-external.json"
            path.write_text(json.dumps({"runId": "EXTERNAL_20260713T000000Z_ABCDEF12", "fixtures": []}), encoding="utf-8")
            with self.assertRaises(RuntimeSafetyError):
                FixtureRegistry.load(path, "CHITU_RT_20260713T000000Z_ABCDEF12")

    def test_child_failure_still_runs_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = FixtureRegistry.create(Path(directory), "CHITU_RT_20260713T000000Z_ABCDEF12")
            registry.register("Lead", "lead-1", registry.run_id, "smoke")
            client = FakeClient({("Lead", "lead-1"): ApiResponse(200, {"description": registry.run_id})})
            def failing_child() -> list[dict[str, object]]:
                raise ValueError("synthetic child failure")
            with self.assertRaises(RuntimeHarnessError):
                run_with_cleanup(client, registry, failing_child)
            self.assertIn(("DELETE", "Lead/lead-1"), client.calls)

    def test_client_error_text_does_not_include_api_key(self) -> None:
        config = RuntimeConfig.from_environment(enabled_env(ESPOCRM_API_KEY="sensitive-key"))
        def failing_opener(*_: object, **__: object) -> object:
            raise TimeoutError()
        with self.assertRaises(Exception) as raised:
            RuntimeRestClient(config, opener=failing_opener).request("GET", "App/user")
        self.assertNotIn("sensitive-key", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
