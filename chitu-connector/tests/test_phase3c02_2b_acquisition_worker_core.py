from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.acquisition import AcquisitionWorker, DeterministicFakeProvider
from chitu_connector.acquisition.models import ProviderResult, RawCandidate, SearchRequest
from chitu_connector.acquisition.normalization import normalize_candidate, normalize_domain


class MemoryAcquisitionStore:
    """Isolated persistence double; it records only SearchJob/ProspectPool writes."""

    def __init__(self, jobs: list[dict[str, Any]]) -> None:
        self.jobs = {job["id"]: deepcopy(job) for job in jobs}
        self.prospects: list[dict[str, Any]] = []
        self.claims: list[str] = []
        self.other_entity_writes: list[str] = []

    def claim_queued_job(self, job_id: str, started_at: str) -> Mapping[str, Any] | None:
        job = self.jobs.get(job_id)
        if job is None or job["status"] != "QUEUED":
            return None
        job.update({"status": "RUNNING", "startedAt": started_at})
        self.claims.append(job_id)
        return deepcopy(job)

    def update_search_job(self, job_id: str, values: Mapping[str, Any]) -> None:
        self.jobs[job_id].update(values)

    def has_prospect(self, provider_name: str, normalized_domain: str) -> bool:
        return any(
            prospect["source"] == provider_name and prospect["website"] == f"https://{normalized_domain}"
            for prospect in self.prospects
        )

    def create_prospect(self, values: Mapping[str, Any]) -> None:
        self.prospects.append(dict(values))


class StaticProvider:
    name = "STATIC_FAKE"

    def __init__(self, candidates: tuple[RawCandidate, ...]) -> None:
        self.candidates = candidates

    def search(self, request: SearchRequest) -> ProviderResult:
        return ProviderResult(self.name, self.candidates[: request.result_limit])


def queued_job(job_id: str = "job-001", *, keyword: str = "3d distributor") -> dict[str, Any]:
    return {
        "id": job_id,
        "status": "QUEUED",
        "source": "GOOGLE_SEARCH",
        "keyword": keyword,
        "country": "US",
        "product": "Resin Tank",
    }


class AcquisitionWorkerCoreTests(TestCase):
    def test_fake_provider_is_deterministic_and_network_free_fixture(self) -> None:
        provider = DeterministicFakeProvider()
        request = SearchRequest("job-001", provider.name, "3D distributor", "US", None, "Resin Tank", 10)
        self.assertEqual(provider.search(request), provider.search(request))
        self.assertEqual(len(provider.search(request).candidates), 3)

    def test_queued_job_transitions_to_completed_and_persists_two_discovery_prospects(self) -> None:
        store = MemoryAcquisitionStore([queued_job()])
        result = AcquisitionWorker(store, DeterministicFakeProvider()).execute_job("job-001")

        self.assertEqual(result.status, "COMPLETED")
        self.assertTrue(result.claimed)
        self.assertEqual((result.result_count, result.inserted_count, result.duplicate_count, result.rejected_count), (3, 2, 1, 0))
        self.assertEqual(store.jobs["job-001"]["status"], "COMPLETED")
        self.assertTrue(store.jobs["job-001"]["startedAt"])
        self.assertTrue(store.jobs["job-001"]["completedAt"])
        self.assertEqual(store.jobs["job-001"]["resultCount"], 3)
        self.assertEqual(store.jobs["job-001"]["acceptedCount"], 2)
        self.assertEqual(store.jobs["job-001"]["rejectedCount"], 0)
        self.assertEqual(store.jobs["job-001"]["prospectCount"], 2)
        self.assertEqual(len(store.prospects), 2)
        for prospect in store.prospects:
            self.assertEqual(prospect["queue"], "DISCOVERY")
            self.assertEqual(prospect["searchJobId"], "job-001")
            self.assertEqual(prospect["source"], "DETERMINISTIC_FAKE")
            self.assertTrue(prospect["website"].startswith("https://"))
            self.assertIn("fingerprint=", prospect["note"])
            self.assertIn("raw_payload_sha256=", prospect["note"])
            self.assertNotIn("fixture", prospect["note"])

    def test_same_job_replay_is_not_claimed_or_written_again(self) -> None:
        store = MemoryAcquisitionStore([queued_job()])
        worker = AcquisitionWorker(store, DeterministicFakeProvider())
        worker.execute_job("job-001")
        replay = worker.execute_job("job-001")

        self.assertEqual(replay.status, "NOT_CLAIMED")
        self.assertFalse(replay.claimed)
        self.assertEqual(store.claims, ["job-001"])
        self.assertEqual(len(store.prospects), 2)

    def test_same_provider_and_normalized_domain_deduplicates_across_jobs(self) -> None:
        store = MemoryAcquisitionStore([queued_job("job-001"), queued_job("job-002")])
        worker = AcquisitionWorker(store, DeterministicFakeProvider())
        worker.execute_job("job-001")
        result = worker.execute_job("job-002")

        self.assertEqual((result.inserted_count, result.duplicate_count), (0, 3))
        self.assertEqual(len(store.prospects), 2)

    def test_domain_normalization_is_deterministic_and_removes_transport_noise(self) -> None:
        self.assertEqual(normalize_domain(" HTTPS://www.www.Example.COM:443/a/b?q=x#section. "), "example.com")
        candidate = normalize_candidate(
            "DETERMINISTIC_FAKE",
            RawCandidate("external-1", "  Example   Company ", "http://www.example.com/path", None, " US ", {"b": 2, "a": 1}),
        )
        assert candidate is not None
        self.assertEqual(candidate.company_name, "Example Company")
        self.assertEqual(candidate.website, "https://example.com")
        self.assertEqual(
            candidate.dedupe_fingerprint,
            hashlib.sha256(b"DETERMINISTIC_FAKE|example.com").hexdigest(),
        )
        self.assertEqual(normalize_domain("not a domain"), None)
        self.assertEqual(normalize_domain(None), None)

    def test_empty_result_completes_without_prospects(self) -> None:
        store = MemoryAcquisitionStore([queued_job(keyword="fake:empty")])
        result = AcquisitionWorker(store, DeterministicFakeProvider()).execute_job("job-001")

        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.result_count, 0)
        self.assertEqual(len(store.prospects), 0)

    def test_provider_errors_fail_job_with_explicit_retryability(self) -> None:
        for keyword, retryable, code in (
            ("fake:retryable-error", True, "FAKE_TRANSIENT"),
            ("fake:non-retryable-error", False, "FAKE_INVALID_REQUEST"),
        ):
            with self.subTest(keyword=keyword):
                store = MemoryAcquisitionStore([queued_job(keyword=keyword)])
                result = AcquisitionWorker(store, DeterministicFakeProvider()).execute_job("job-001")

                self.assertEqual(result.status, "FAILED")
                self.assertEqual(result.retryable, retryable)
                self.assertEqual(result.error_code, code)
                self.assertEqual(store.jobs["job-001"]["status"], "FAILED")
                self.assertIn(f"retryable={'true' if retryable else 'false'}", store.jobs["job-001"]["failureReason"])
                self.assertNotIn("Traceback", store.jobs["job-001"]["errorMessage"])

    def test_non_queued_and_cancelled_jobs_are_not_claimed(self) -> None:
        for status in ("RUNNING", "COMPLETED", "FAILED", "CANCELLED"):
            with self.subTest(status=status):
                job = queued_job()
                job["status"] = status
                store = MemoryAcquisitionStore([job])
                result = AcquisitionWorker(store, DeterministicFakeProvider()).execute_job("job-001")
                self.assertEqual(result.status, "NOT_CLAIMED")
                self.assertEqual(len(store.prospects), 0)

    def test_invalid_candidate_is_rejected_without_downstream_side_effects(self) -> None:
        provider = StaticProvider((
            RawCandidate("bad-1", "Invalid", "", "https://provider.invalid/x", "US", {"secret": "never persisted"}),
        ))
        store = MemoryAcquisitionStore([queued_job()])
        result = AcquisitionWorker(store, provider).execute_job("job-001")

        self.assertEqual((result.result_count, result.inserted_count, result.rejected_count), (1, 0, 1))
        self.assertEqual(store.prospects, [])
        self.assertEqual(store.other_entity_writes, [])

    def test_core_has_no_connector_or_downstream_crm_side_effect_imports(self) -> None:
        import chitu_connector.acquisition.worker as worker_module
        from pathlib import Path

        source = Path(worker_module.__file__).read_text(encoding="utf-8")
        for forbidden in ("ChituSyncService", "Lead", "Opportunity", "ResearchEvidence", "Email", "urlopen", "requests", "socket"):
            self.assertNotIn(forbidden, source)

