"""Provider-neutral acquisition data contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SearchRequest:
    job_id: str
    provider_name: str
    keyword: str
    country: str | None
    persona: str | None
    product: str | None
    result_limit: int


@dataclass(frozen=True, slots=True)
class RawCandidate:
    provider_candidate_id: str
    company_name: str
    domain: str | None
    source_url: str | None
    country: str | None
    raw_payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class NormalizedCandidate:
    provider_name: str
    provider_candidate_id: str
    company_name: str
    normalized_domain: str
    website: str
    source_url: str | None
    country: str | None
    dedupe_fingerprint: str
    raw_payload_digest: str


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider_name: str
    candidates: tuple[RawCandidate, ...]


class ProviderError(Exception):
    """Safe provider failure classification; never carries a traceback/payload."""

    def __init__(self, code: str, safe_message: str, *, retryable: bool) -> None:
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class JobExecutionResult:
    job_id: str
    status: str
    claimed: bool
    result_count: int = 0
    inserted_count: int = 0
    duplicate_count: int = 0
    rejected_count: int = 0
    retryable: bool | None = None
    error_code: str | None = None
