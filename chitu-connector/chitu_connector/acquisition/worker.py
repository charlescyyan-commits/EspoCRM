"""Single-job acquisition worker with injectable persistence and provider edges."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, Protocol

from .models import JobExecutionResult, ProviderError, SearchRequest
from .normalization import normalize_candidate
from .provider import SearchProvider


class AcquisitionStore(Protocol):
    """Persistence boundary; implementations must claim QUEUED jobs atomically."""

    def claim_queued_job(self, job_id: str, started_at: str) -> Mapping[str, Any] | None: ...

    def update_search_job(self, job_id: str, values: Mapping[str, Any]) -> None: ...

    def has_prospect(self, provider_name: str, normalized_domain: str) -> bool: ...

    def create_prospect(self, values: Mapping[str, Any]) -> None: ...


class AcquisitionWorker:
    def __init__(self, store: AcquisitionStore, provider: SearchProvider, *, result_limit: int = 10) -> None:
        if result_limit < 1:
            raise ValueError("result_limit must be positive")
        self._store = store
        self._provider = provider
        self._result_limit = result_limit

    def execute_job(self, search_job_id: str) -> JobExecutionResult:
        started_at = _now()
        job = self._store.claim_queued_job(search_job_id, started_at)
        if job is None:
            return JobExecutionResult(search_job_id, "NOT_CLAIMED", claimed=False)

        request = SearchRequest(
            job_id=search_job_id,
            provider_name=self._provider.name,
            keyword=str(job.get("keyword") or ""),
            country=_optional_text(job.get("country")),
            persona=_optional_text(job.get("persona")),
            product=_optional_text(job.get("product")),
            result_limit=self._result_limit,
        )
        try:
            result = self._provider.search(request)
        except ProviderError as error:
            self._store.update_search_job(search_job_id, {
                "status": "FAILED",
                "completedAt": _now(),
                "errorMessage": error.safe_message,
                "failureReason": f"{error.code}; retryable={'true' if error.retryable else 'false'}",
            })
            return JobExecutionResult(search_job_id, "FAILED", True, retryable=error.retryable, error_code=error.code)

        inserted = duplicates = rejected = 0
        seen_fingerprints: set[str] = set()
        for raw_candidate in result.candidates:
            candidate = normalize_candidate(result.provider_name, raw_candidate)
            if candidate is None:
                rejected += 1
                continue
            if candidate.dedupe_fingerprint in seen_fingerprints or self._store.has_prospect(
                candidate.provider_name, candidate.normalized_domain
            ):
                duplicates += 1
                continue
            seen_fingerprints.add(candidate.dedupe_fingerprint)
            self._store.create_prospect({
                "name": candidate.company_name,
                "externalProspectId": candidate.provider_candidate_id,
                "source": candidate.provider_name,
                "sourceUrl": candidate.source_url,
                "website": candidate.website,
                "country": candidate.country,
                "queue": "DISCOVERY",
                "status": "WAITING",
                "researchStatus": "NOT_STARTED",
                "qualificationStatus": "PENDING",
                "crmPushStatus": "NOT_READY",
                "searchJobId": search_job_id,
                # Existing CRM fields are intentionally reused; no raw payload is persisted.
                "note": (
                    "acquisition:v1 "
                    f"fingerprint={candidate.dedupe_fingerprint} "
                    f"normalized_domain={candidate.normalized_domain} "
                    f"raw_payload_sha256={candidate.raw_payload_digest}"
                ),
            })
            inserted += 1

        self._store.update_search_job(search_job_id, {
            "status": "COMPLETED",
            "completedAt": _now(),
            "resultCount": len(result.candidates),
            "acceptedCount": inserted,
            "rejectedCount": rejected,
            "prospectCount": inserted,
            "errorMessage": None,
            "failureReason": None,
        })
        return JobExecutionResult(search_job_id, "COMPLETED", True, len(result.candidates), inserted, duplicates, rejected)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None
