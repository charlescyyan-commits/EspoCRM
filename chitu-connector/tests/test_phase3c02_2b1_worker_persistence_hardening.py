from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.acquisition import (
    AcquisitionWorker,
    ClaimResult,
    PersistenceError,
    ProviderError,
    ProviderResult,
    RawCandidate,
)


def queued_job(status: str = "QUEUED") -> dict[str, Any]:
    return {
        "id": "job-001",
        "status": status,
        "keyword": "fault-test",
        "country": "US",
        "product": "Resin Tank",
    }


def candidate(number: int) -> RawCandidate:
    return RawCandidate(
        provider_candidate_id=f"candidate-{number}",
        company_name=f"Candidate {number}",
        domain=f"candidate-{number}.example",
        source_url=f"https://provider.invalid/candidate/{number}",
        country="US",
        raw_payload={"fixture": number},
    )


class SpyProvider:
    name = "SPY_PROVIDER"

    def __init__(self, result: ProviderResult | None = None, error: Exception | None = None) -> None:
        self.result = result or ProviderResult(self.name, (candidate(1), candidate(2), candidate(3)))
        self.error = error
        self.calls = 0

    def search(self, request: object) -> ProviderResult:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class FaultInjectionStore:
    def __init__(
        self,
        job: dict[str, Any],
        *,
        claim_error: Exception | None = None,
        fail_create_at: int | None = None,
        fail_completion: bool = False,
        fail_failure_update: bool = False,
    ) -> None:
        self.job = deepcopy(job)
        self.claim_error = claim_error
        self.fail_create_at = fail_create_at
        self.fail_completion = fail_completion
        self.fail_failure_update = fail_failure_update
        self.prospects: list[dict[str, Any]] = []
        self.create_calls = 0
        self.claim_expected_status: str | None = None
        self.update_expected_statuses: list[str | None] = []

    def claim_search_job(
        self,
        job_id: str,
        *,
        expected_status: str,
        started_at: str,
        expected_version: str | None = None,
    ) -> ClaimResult:
        self.claim_expected_status = expected_status
        if self.claim_error is not None:
            raise self.claim_error
        if job_id != self.job["id"]:
            return ClaimResult(False, reason="NOT_FOUND")
        if self.job["status"] != expected_status:
            return ClaimResult(False, previous_status=self.job["status"], current_status=self.job["status"], reason="STATUS_MISMATCH")
        self.job.update({"status": "RUNNING", "startedAt": started_at})
        return ClaimResult(True, deepcopy(self.job), expected_status, "RUNNING", version="v1")

    def update_search_job(
        self,
        job_id: str,
        values: Mapping[str, Any],
        *,
        expected_status: str | None = None,
        expected_version: str | None = None,
    ) -> None:
        self.update_expected_statuses.append(expected_status)
        if expected_status is not None and self.job["status"] != expected_status:
            raise PersistenceError("STATUS_CONFLICT", "SearchJob status changed before update", retryable=True)
        if values.get("status") == "COMPLETED" and self.fail_completion:
            raise PersistenceError("COMPLETE_WRITE_FAILED", "Authorization: Bearer never-persist-this", retryable=True)
        if values.get("status") == "FAILED" and self.fail_failure_update:
            raise PersistenceError("FAILURE_WRITE_FAILED", "Failure status update unavailable", retryable=True)
        self.job.update(values)

    def has_prospect(self, provider_name: str, normalized_domain: str) -> bool:
        return any(item["source"] == provider_name and item["website"] == f"https://{normalized_domain}" for item in self.prospects)

    def create_prospect(self, values: Mapping[str, Any]) -> None:
        self.create_calls += 1
        if self.fail_create_at == self.create_calls:
            raise PersistenceError("PROSPECT_WRITE_FAILED", "secret=never-persist-this", retryable=True)
        self.prospects.append(dict(values))


class WorkerPersistenceHardeningTests(TestCase):
    def test_conditional_claim_requires_queued_and_does_not_call_provider_when_rejected(self) -> None:
        for status in ("RUNNING", "COMPLETED", "FAILED", "CANCELLED"):
            with self.subTest(status=status):
                store = FaultInjectionStore(queued_job(status))
                provider = SpyProvider()
                result = AcquisitionWorker(store, provider).execute_job("job-001")

                self.assertEqual(result.status, "NOT_CLAIMED")
                self.assertEqual(result.previous_status, status)
                self.assertEqual(result.final_status, status)
                self.assertEqual(store.claim_expected_status, "QUEUED")
                self.assertEqual(provider.calls, 0)
                self.assertEqual(store.prospects, [])

    def test_claim_persistence_error_returns_structured_failure_without_provider_call(self) -> None:
        store = FaultInjectionStore(
            queued_job(),
            claim_error=PersistenceError("CLAIM_TRANSPORT", "Connection reset", retryable=True),
        )
        provider = SpyProvider()
        result = AcquisitionWorker(store, provider).execute_job("job-001")

        self.assertEqual(result.status, "CLAIM_FAILED")
        self.assertTrue(result.claim_failed)
        self.assertTrue(result.retryable)
        self.assertEqual(result.error_code, "CLAIM_TRANSPORT")
        self.assertIsNone(result.final_status)
        self.assertEqual(provider.calls, 0)

    def test_provider_and_unexpected_errors_are_structured_and_safe(self) -> None:
        cases = (
            (ProviderError("TRANSIENT", "Provider temporarily unavailable", retryable=True), "TRANSIENT", True, "PROVIDER"),
            (ProviderError("INVALID", "Provider request invalid", retryable=False), "INVALID", False, "PROVIDER"),
            (RuntimeError("Authorization: Bearer secret-value"), "UNEXPECTED_WORKER_ERROR", True, "PROVIDER"),
        )
        for error, code, retryable, stage in cases:
            with self.subTest(code=code):
                store = FaultInjectionStore(queued_job())
                result = AcquisitionWorker(store, SpyProvider(error=error)).execute_job("job-001")

                self.assertEqual(result.status, "FAILED")
                self.assertEqual(result.final_status, "FAILED")
                self.assertEqual(result.error_code, code)
                self.assertEqual(result.retryable, retryable)
                self.assertEqual(result.failure_stage, stage)
                self.assertNotIn("secret-value", result.error_summary or "")
                self.assertNotIn("Traceback", store.job["errorMessage"])

    def test_first_persistence_failure_is_fail_fast_and_preserves_safe_counts(self) -> None:
        store = FaultInjectionStore(queued_job(), fail_create_at=1)
        result = AcquisitionWorker(store, SpyProvider()).execute_job("job-001")

        self.assertEqual(result.status, "FAILED")
        self.assertFalse(result.partial_persistence)
        self.assertEqual(result.failure_stage, "PERSISTENCE")
        self.assertEqual((result.inserted_count, result.duplicate_count, result.rejected_count), (0, 0, 0))
        self.assertEqual(store.create_calls, 1)
        self.assertEqual(store.prospects, [])
        self.assertEqual(store.job["status"], "FAILED")
        self.assertNotIn("never-persist-this", store.job["errorMessage"])

    def test_partial_persistence_stops_later_writes_and_preserves_counts(self) -> None:
        store = FaultInjectionStore(queued_job(), fail_create_at=2)
        result = AcquisitionWorker(store, SpyProvider()).execute_job("job-001")

        self.assertEqual(result.status, "FAILED")
        self.assertTrue(result.partial_persistence)
        self.assertEqual((result.inserted_count, result.duplicate_count, result.rejected_count), (1, 0, 0))
        self.assertEqual(store.create_calls, 2)
        self.assertEqual(len(store.prospects), 1)
        self.assertEqual(store.job["acceptedCount"], 1)
        self.assertEqual(store.job["status"], "FAILED")
        self.assertEqual(store.update_expected_statuses[-1], "RUNNING")

    def test_completion_failure_preserves_prospects_and_records_explicit_failure(self) -> None:
        store = FaultInjectionStore(queued_job(), fail_completion=True)
        result = AcquisitionWorker(store, SpyProvider()).execute_job("job-001")

        self.assertEqual(result.status, "FAILED")
        self.assertTrue(result.partial_persistence)
        self.assertTrue(result.completion_persistence_failed)
        self.assertFalse(result.final_status_uncertain)
        self.assertEqual(result.final_status, "FAILED")
        self.assertEqual(len(store.prospects), 3)
        self.assertEqual(store.job["status"], "FAILED")
        self.assertEqual(result.error_summary, "Sensitive error details suppressed")

    def test_failure_update_error_returns_uncertain_final_status_without_raising(self) -> None:
        store = FaultInjectionStore(queued_job(), fail_create_at=2, fail_failure_update=True)
        result = AcquisitionWorker(store, SpyProvider()).execute_job("job-001")

        self.assertEqual(result.status, "FAILED")
        self.assertTrue(result.failure_persistence_failed)
        self.assertTrue(result.final_status_uncertain)
        self.assertIsNone(result.final_status)
        self.assertEqual(len(store.prospects), 1)
        self.assertEqual(store.job["status"], "RUNNING")

    def test_normalization_exception_is_caught_without_persisting_exception_text(self) -> None:
        provider = SpyProvider(ProviderResult("SPY_PROVIDER", ("not-a-candidate",)))  # type: ignore[arg-type]
        store = FaultInjectionStore(queued_job())
        result = AcquisitionWorker(store, provider).execute_job("job-001")

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.error_code, "UNEXPECTED_WORKER_ERROR")
        self.assertEqual(result.failure_stage, "NORMALIZATION")
        self.assertEqual(result.error_summary, "Unexpected AttributeError")
        self.assertEqual(store.prospects, [])
        self.assertEqual(store.job["status"], "FAILED")

