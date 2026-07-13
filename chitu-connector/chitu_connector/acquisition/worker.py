"""Single-job acquisition worker with injectable persistence and provider edges."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, Protocol

from .models import ClaimResult, JobExecutionResult, PersistenceError, ProviderError, SearchRequest
from .normalization import normalize_candidate
from .provider import SearchProvider


class AcquisitionStore(Protocol):
    """Persistence boundary with conditional-claim and conditional-update semantics.

    A future EspoCRM adapter may implement the conditions with an atomic action,
    an ETag/If-Match check, or best-effort compare-and-set.  The worker never
    performs a read-then-unconditional RUNNING transition itself.
    """

    def claim_search_job(
        self,
        job_id: str,
        *,
        expected_status: str,
        started_at: str,
        expected_version: str | None = None,
    ) -> ClaimResult: ...

    def update_search_job(
        self,
        job_id: str,
        values: Mapping[str, Any],
        *,
        expected_status: str | None = None,
        expected_version: str | None = None,
    ) -> None: ...

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
        try:
            claim = self._store.claim_search_job(
                search_job_id,
                expected_status="QUEUED",
                started_at=started_at,
            )
        except Exception as error:
            code, summary, retryable = _error_details(error)
            return JobExecutionResult(
                search_job_id,
                "CLAIM_FAILED",
                claimed=False,
                retryable=retryable,
                error_code=code,
                error_summary=summary,
                claim_failed=True,
                failure_stage="CLAIM",
                started_at=started_at,
            )

        if not claim.claimed or claim.job is None:
            return JobExecutionResult(
                search_job_id,
                "NOT_CLAIMED",
                claimed=False,
                error_code=claim.reason,
                previous_status=claim.previous_status,
                final_status=claim.current_status,
                failure_stage="CLAIM" if claim.reason else None,
                started_at=started_at,
            )

        job = claim.job

        request = SearchRequest(
            job_id=search_job_id,
            provider_name=self._provider.name,
            keyword=str(job.get("keyword") or ""),
            country=_optional_text(job.get("country")),
            persona=_optional_text(job.get("persona")),
            product=_optional_text(job.get("product")),
            result_limit=self._result_limit,
        )
        result_count = inserted = duplicates = rejected = 0
        provider_name = self._provider.name
        stage = "PROVIDER"
        try:
            result = self._provider.search(request)
            provider_name = result.provider_name
            result_count = len(result.candidates)
            seen_fingerprints: set[str] = set()
            stage = "NORMALIZATION"
            for raw_candidate in result.candidates:
                candidate = normalize_candidate(result.provider_name, raw_candidate)
                if candidate is None:
                    rejected += 1
                    continue
                stage = "DEDUPLICATION"
                if candidate.dedupe_fingerprint in seen_fingerprints or self._store.has_prospect(
                    candidate.provider_name, candidate.normalized_domain
                ):
                    duplicates += 1
                    continue
                seen_fingerprints.add(candidate.dedupe_fingerprint)
                stage = "PERSISTENCE"
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

            stage = "COMPLETION"
            completed_at = _now()
            self._store.update_search_job(
                search_job_id,
                {
                    "status": "COMPLETED",
                    "completedAt": completed_at,
                    "resultCount": result_count,
                    "acceptedCount": inserted,
                    "rejectedCount": rejected,
                    "prospectCount": inserted,
                    "errorMessage": None,
                    "failureReason": None,
                },
                expected_status="RUNNING",
                expected_version=claim.version,
            )
            return JobExecutionResult(
                search_job_id,
                "COMPLETED",
                True,
                result_count,
                inserted,
                duplicates,
                rejected,
                previous_status=claim.previous_status,
                final_status="COMPLETED",
                provider=provider_name,
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as error:
            return self._fail_after_claim(
                search_job_id,
                claim,
                started_at,
                error,
                stage="PROVIDER" if isinstance(error, ProviderError) else stage,
                result_count=result_count,
                inserted_count=inserted,
                duplicate_count=duplicates,
                rejected_count=rejected,
                provider=provider_name,
            )

    def _fail_after_claim(
        self,
        search_job_id: str,
        claim: ClaimResult,
        started_at: str,
        error: Exception,
        *,
        stage: str,
        result_count: int,
        inserted_count: int,
        duplicate_count: int,
        rejected_count: int,
        provider: str,
    ) -> JobExecutionResult:
        code, summary, retryable = _error_details(error)
        completed_at = _now()
        try:
            self._store.update_search_job(
                search_job_id,
                {
                    "status": "FAILED",
                    "completedAt": completed_at,
                    "resultCount": result_count,
                    "acceptedCount": inserted_count,
                    "rejectedCount": rejected_count,
                    "prospectCount": inserted_count,
                    "errorMessage": summary,
                    "failureReason": f"{code}; retryable={'true' if retryable else 'false'}; stage={stage}",
                },
                expected_status="RUNNING",
                expected_version=claim.version,
            )
        except Exception:
            return JobExecutionResult(
                search_job_id,
                "FAILED",
                True,
                result_count,
                inserted_count,
                duplicate_count,
                rejected_count,
                retryable=retryable,
                error_code=code,
                error_summary=summary,
                previous_status=claim.previous_status,
                provider=provider,
                partial_persistence=inserted_count > 0,
                completion_persistence_failed=stage == "COMPLETION",
                failure_persistence_failed=True,
                final_status_uncertain=True,
                failure_stage=stage,
                started_at=started_at,
                completed_at=completed_at,
            )
        return JobExecutionResult(
            search_job_id,
            "FAILED",
            True,
            result_count,
            inserted_count,
            duplicate_count,
            rejected_count,
            retryable=retryable,
            error_code=code,
            error_summary=summary,
            previous_status=claim.previous_status,
            final_status="FAILED",
            provider=provider,
            partial_persistence=inserted_count > 0,
            completion_persistence_failed=stage == "COMPLETION",
            failure_stage=stage,
            started_at=started_at,
            completed_at=completed_at,
        )


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _error_details(error: Exception) -> tuple[str, str, bool]:
    if isinstance(error, ProviderError):
        return error.code, _safe_summary(error.safe_message), error.retryable
    if isinstance(error, PersistenceError):
        return error.code, _safe_summary(error.safe_message), error.retryable
    return "UNEXPECTED_WORKER_ERROR", _safe_summary(f"Unexpected {type(error).__name__}"), True


def _safe_summary(value: str) -> str:
    summary = " ".join(value.split())[:240]
    if not summary:
        return "Operation failed"
    if any(marker in summary.casefold() for marker in ("authorization", "api key", "api_key", "bearer ", "token=", "secret", "password")):
        return "Sensitive error details suppressed"
    return summary
