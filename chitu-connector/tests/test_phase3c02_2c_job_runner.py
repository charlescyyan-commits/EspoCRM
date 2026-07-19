from __future__ import annotations

from copy import deepcopy
from io import BytesIO, StringIO
import json
from pathlib import Path
from typing import Any, Mapping
from unittest import TestCase
from urllib.error import HTTPError, URLError

from chitu_connector.acquisition.espo_repository import EspoAcquisitionRepository
from chitu_connector.acquisition.models import ClaimResult, PersistenceError
from chitu_connector.acquisition import runner


def queued_job(*, keyword: str = "fake:default", status: str = "QUEUED") -> dict[str, Any]:
    return {
        "id": "job-2c-001",
        "status": status,
        "keyword": keyword,
        "country": "US",
        "product": "Resin Tank",
        "modifiedAt": "v-queued",
    }


class MemoryRepository:
    def __init__(self, job: Mapping[str, Any], *, fail_create_at: int | None = None) -> None:
        self.job = deepcopy(dict(job))
        self.prospects: list[dict[str, Any]] = []
        self.fail_create_at = fail_create_at
        self.create_calls = 0
        self.fetch_calls = 0

    def fetch_search_job(self, job_id: str) -> Mapping[str, Any] | None:
        self.fetch_calls += 1
        return deepcopy(self.job) if job_id == self.job["id"] else None

    def claim_search_job(
        self,
        job_id: str,
        *,
        expected_status: str,
        started_at: str,
        expected_version: str | None = None,
    ) -> ClaimResult:
        if job_id != self.job["id"]:
            return ClaimResult(False, reason="NOT_FOUND")
        if self.job["status"] != expected_status:
            return ClaimResult(False, previous_status=self.job["status"], current_status=self.job["status"], reason="STATUS_MISMATCH")
        if expected_version is not None and self.job.get("modifiedAt") != expected_version:
            return ClaimResult(False, previous_status=self.job["status"], current_status=self.job["status"], reason="VERSION_MISMATCH")
        self.job.update({"status": "RUNNING", "startedAt": started_at, "modifiedAt": "v-running"})
        return ClaimResult(True, deepcopy(self.job), "QUEUED", "RUNNING", version="v-running")

    def update_search_job(
        self,
        job_id: str,
        values: Mapping[str, Any],
        *,
        expected_status: str | None = None,
        expected_version: str | None = None,
    ) -> None:
        if job_id != self.job["id"]:
            raise PersistenceError("ESPO_WRITE_ERROR", "SearchJob was not found", retryable=False)
        if expected_status is not None and self.job["status"] != expected_status:
            raise PersistenceError("STATUS_CONFLICT", "SearchJob status changed", retryable=True)
        if expected_version is not None and self.job.get("modifiedAt") != expected_version:
            raise PersistenceError("VERSION_CONFLICT", "SearchJob version changed", retryable=True)
        self.job.update(values)
        self.job["modifiedAt"] = "v-final"

    def has_prospect(self, provider_name: str, normalized_domain: str) -> bool:
        return any(item["source"] == provider_name and item["website"] == f"https://{normalized_domain}" for item in self.prospects)

    def create_prospect(self, values: Mapping[str, Any]) -> None:
        self.create_calls += 1
        if self.fail_create_at == self.create_calls:
            raise PersistenceError("ESPO_WRITE_ERROR", "Prospect write failed", retryable=True)
        self.prospects.append(dict(values))


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


class ScriptedOpener:
    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.requests: list[Any] = []
        self.kwargs: list[dict[str, Any]] = []

    def __call__(self, request: Any, **kwargs: Any) -> FakeResponse:
        self.requests.append(request)
        self.kwargs.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return FakeResponse(response)


class RunnerCliTests(TestCase):
    def _run(self, args: list[str], store: MemoryRepository, env: Mapping[str, str] | None = None) -> tuple[int, dict[str, Any]]:
        output = StringIO()
        code = runner.main(
            args,
            repository_factory=lambda _: store,
            environ=env or {"ESPOCRM_BASE_URL": "http://crm.invalid", "ESPOCRM_API_KEY": "test-key"},
            stdout=output,
        )
        return code, json.loads(output.getvalue())

    def test_missing_configuration_fails_before_repository_access(self) -> None:
        output = StringIO()
        called = False

        def repository_factory(_: runner.RunnerConfig) -> MemoryRepository:
            nonlocal called
            called = True
            return MemoryRepository(queued_job())

        code = runner.main(["run-job", "--job-id", "job-2c-001"], repository_factory=repository_factory, environ={}, stdout=output)
        self.assertEqual(code, runner.EXIT_INPUT_OR_CONFIG)
        self.assertFalse(called)
        self.assertEqual(json.loads(output.getvalue())["errorCode"], "CONFIG_ERROR")

    def test_non_fake_provider_is_rejected_before_configuration_or_network(self) -> None:
        output = StringIO()
        code = runner.main(["run-job", "--job-id", "job-2c-001", "--provider", "google"], environ={}, stdout=output)
        self.assertEqual(code, runner.EXIT_INPUT_OR_CONFIG)
        self.assertEqual(json.loads(output.getvalue())["errorCode"], "INVALID_ARGUMENT")

    def test_success_json_output_is_safe_and_replay_is_rejected(self) -> None:
        store = MemoryRepository(queued_job())
        code, payload = self._run(["run-job", "--job-id", "job-2c-001"], store)
        self.assertEqual(code, runner.EXIT_SUCCESS)
        self.assertEqual(payload["finalStatus"], "COMPLETED")
        self.assertEqual((payload["insertedCount"], payload["duplicateCount"]), (2, 1))
        self.assertNotIn("test-key", json.dumps(payload))
        self.assertEqual(len(store.prospects), 2)

        replay_code, replay = self._run(["run-job", "--job-id", "job-2c-001"], store)
        self.assertEqual(replay_code, runner.EXIT_NOT_CLAIMED)
        self.assertEqual(replay["errorCode"], "JOB_NOT_QUEUED")
        self.assertEqual(len(store.prospects), 2)

    def test_empty_and_provider_error_modes_have_stable_exit_codes(self) -> None:
        empty_code, empty = self._run(["run-job", "--job-id", "job-2c-001"], MemoryRepository(queued_job(keyword="fake:empty")))
        self.assertEqual(empty_code, runner.EXIT_SUCCESS)
        self.assertEqual((empty["resultCount"], empty["insertedCount"]), (0, 0))

        for keyword in ("fake:retryable-error", "fake:non-retryable-error"):
            with self.subTest(keyword=keyword):
                code, payload = self._run(["run-job", "--job-id", "job-2c-001"], MemoryRepository(queued_job(keyword=keyword)))
                self.assertEqual(code, runner.EXIT_PROVIDER_FAILURE)
                self.assertEqual(payload["failureStage"], "PROVIDER")
                self.assertEqual(payload["finalStatus"], "FAILED")

    def test_partial_persistence_uses_exit_six(self) -> None:
        code, payload = self._run(["run-job", "--job-id", "job-2c-001"], MemoryRepository(queued_job(), fail_create_at=2))
        self.assertEqual(code, runner.EXIT_PARTIAL_OR_UNCERTAIN)
        self.assertTrue(payload["partialPersistence"])
        self.assertEqual(payload["insertedCount"], 1)

    def test_completed_running_failed_and_cancelled_jobs_do_not_execute(self) -> None:
        for status in ("COMPLETED", "RUNNING", "FAILED", "CANCELLED"):
            with self.subTest(status=status):
                store = MemoryRepository(queued_job(status=status))
                code, payload = self._run(["run-job", "--job-id", "job-2c-001"], store)
                self.assertEqual(code, runner.EXIT_NOT_CLAIMED)
                self.assertEqual(payload["previousStatus"], status)
                self.assertEqual(store.prospects, [])


class EspoRepositoryTests(TestCase):
    def _repository(self, opener: ScriptedOpener) -> EspoAcquisitionRepository:
        return EspoAcquisitionRepository("https://crm.example", "test-key", request_opener=opener)

    def test_fetch_search_job_and_not_found(self) -> None:
        opener = ScriptedOpener({"id": "job-1", "status": "QUEUED"})
        self.assertEqual(self._repository(opener).fetch_search_job("job-1")["status"], "QUEUED")
        self.assertIn("/api/v1/SearchJob/job-1?", opener.requests[0].full_url)
        self.assertEqual(opener.requests[0].get_header("X-api-key"), "test-key")

        not_found = ScriptedOpener(HTTPError("https://crm.example", 404, "Not Found", {}, BytesIO()))
        self.assertIsNone(self._repository(not_found).fetch_search_job("missing"))

    def test_http_errors_and_malformed_json_are_safely_classified(self) -> None:
        for status_code, retryable in ((401, False), (403, False), (429, True), (500, True)):
            with self.subTest(status_code=status_code):
                opener = ScriptedOpener(HTTPError("https://crm.example", status_code, "error", {}, BytesIO()))
                with self.assertRaises(PersistenceError) as caught:
                    self._repository(opener).fetch_search_job("job-1")
                self.assertEqual(caught.exception.code, "ESPO_READ_ERROR")
                self.assertEqual(caught.exception.retryable, retryable)

        with self.assertRaises(PersistenceError) as malformed:
            self._repository(ScriptedOpener(b"not-json")).fetch_search_job("job-1")
        self.assertFalse(malformed.exception.retryable)
        with self.assertRaises(PersistenceError) as timeout:
            self._repository(ScriptedOpener(URLError("timeout"))).fetch_search_job("job-1")
        self.assertTrue(timeout.exception.retryable)

    def test_claim_is_queued_only_and_confirms_running_status(self) -> None:
        opener = ScriptedOpener(
            {"id": "job-1", "status": "QUEUED", "modifiedAt": "v1"},
            {"id": "job-1"},
            {"id": "job-1", "status": "RUNNING", "modifiedAt": "v2", "keyword": "fake:default"},
        )
        result = self._repository(opener).claim_search_job("job-1", expected_status="QUEUED", started_at="2026-07-13T10:00:00Z")
        self.assertTrue(result.claimed)
        self.assertEqual(result.version, "v2")
        self.assertEqual(opener.requests[1].method, "PUT")
        self.assertEqual(json.loads(opener.requests[1].data.decode("utf-8"))["status"], "RUNNING")

        non_queued = ScriptedOpener({"id": "job-1", "status": "COMPLETED", "modifiedAt": "v1"})
        rejected = self._repository(non_queued).claim_search_job("job-1", expected_status="QUEUED", started_at="now")
        self.assertFalse(rejected.claimed)
        self.assertEqual(rejected.reason, "STATUS_MISMATCH")
        self.assertEqual(len(non_queued.requests), 1)

    def test_claim_requires_running_confirmation(self) -> None:
        opener = ScriptedOpener(
            {"id": "job-1", "status": "QUEUED", "modifiedAt": "v1"},
            {"id": "job-1"},
            {"id": "job-1", "status": "QUEUED", "modifiedAt": "v2"},
        )
        result = self._repository(opener).claim_search_job("job-1", expected_status="QUEUED", started_at="2026-07-13T10:00:00Z")
        self.assertFalse(result.claimed)
        self.assertEqual(result.reason, "CLAIM_NOT_CONFIRMED")
        self.assertEqual(result.current_status, "QUEUED")

    def test_update_uses_expected_status_and_version_then_confirms(self) -> None:
        opener = ScriptedOpener(
            {"id": "job-1", "status": "RUNNING", "modifiedAt": "v2"},
            {"id": "job-1"},
            {"id": "job-1", "status": "COMPLETED", "modifiedAt": "v3"},
        )
        self._repository(opener).update_search_job(
            "job-1", {"status": "COMPLETED", "resultCount": 2}, expected_status="RUNNING", expected_version="v2"
        )
        request_body = json.loads(opener.requests[1].data.decode("utf-8"))
        self.assertEqual(request_body["status"], "COMPLETED")

    def test_prospect_lookup_and_create_use_only_existing_fields(self) -> None:
        existing = ScriptedOpener({"list": [{"id": "pool-1", "source": "DETERMINISTIC_FAKE", "website": "https://alpha.example"}]})
        self.assertTrue(self._repository(existing).has_prospect("DETERMINISTIC_FAKE", "alpha.example"))
        self.assertIn("ProspectPool?", existing.requests[0].full_url)

        create = ScriptedOpener({"id": "pool-2"})
        self._repository(create).create_prospect({
            "name": "Alpha", "source": "DETERMINISTIC_FAKE", "website": "https://alpha.example", "queue": "DISCOVERY",
            "status": "WAITING", "researchStatus": "NOT_STARTED", "qualificationStatus": "PENDING", "crmPushStatus": "NOT_READY",
            "searchJobId": "job-1", "note": "acquisition:v1 fingerprint=abc", "unexpected": "not-sent",
        })
        body = json.loads(create.requests[0].data.decode("utf-8"))
        self.assertNotIn("unexpected", body)
        self.assertEqual(body["searchJobId"], "job-1")

    def test_static_boundary_has_no_sync_service_or_real_provider(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        for relative in (
            "chitu-connector/chitu_connector/acquisition/runner.py",
            "chitu-connector/chitu_connector/acquisition/espo_repository.py",
        ):
            source = (repo_root / relative).read_text(encoding="utf-8")
            self.assertNotIn("ChituSyncService", source)
            self.assertNotIn("Apify", source)
            self.assertNotIn("while True", source)
