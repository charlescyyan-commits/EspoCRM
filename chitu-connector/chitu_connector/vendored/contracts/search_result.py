"""Typed contracts for search results and pre-ingestion pipeline output."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class ExclusionReason(StrEnum):
    OFFICIAL_BRAND_ROOT_DOMAIN = "OFFICIAL_BRAND_ROOT_DOMAIN"
    OFFICIAL_BRAND_REGIONAL_SITE = "OFFICIAL_BRAND_REGIONAL_SITE"
    OFFICIAL_BRAND_STORE = "OFFICIAL_BRAND_STORE"
    OFFICIAL_BRAND_SUBDOMAIN = "OFFICIAL_BRAND_SUBDOMAIN"
    OFFICIAL_BRAND_REDIRECT = "OFFICIAL_BRAND_REDIRECT"
    MARKETPLACE_DOMAIN = "MARKETPLACE_DOMAIN"
    SOCIAL_PLATFORM_DOMAIN = "SOCIAL_PLATFORM_DOMAIN"
    NON_TARGET_MEDIA_SITE = "NON_TARGET_MEDIA_SITE"
    INVALID_DOMAIN = "INVALID_DOMAIN"
    INVALID_URL = "INVALID_URL"
    DUPLICATE_DOMAIN = "DUPLICATE_DOMAIN"
    PLATFORM_DOMAIN = "PLATFORM_DOMAIN"
    BLOG_ARTICLE = "BLOG_ARTICLE"
    DIRECTORY_CATEGORY = "DIRECTORY_CATEGORY"
    CONTAMINATED_TEST_DATA = "CONTAMINATED_TEST_DATA"


class CandidateClassification(StrEnum):
    MULTI_BRAND_DISTRIBUTOR = "MULTI_BRAND_DISTRIBUTOR"
    MULTI_BRAND_RETAILER = "MULTI_BRAND_RETAILER"
    AUTHORIZED_RESELLER = "AUTHORIZED_RESELLER"
    INDEPENDENT_RESELLER = "INDEPENDENT_RESELLER"
    DISTRIBUTOR = "DISTRIBUTOR"
    DEALER = "DEALER"
    RESELLER = "RESELLER"
    RETAILER = "RETAILER"
    PRINT_SERVICE = "PRINT_SERVICE"
    MATERIAL_SUPPLIER = "MATERIAL_SUPPLIER"
    UNCERTAIN = "UNCERTAIN"
    HOLD_FOR_IDENTITY_REVIEW = "HOLD_FOR_IDENTITY_REVIEW"


@dataclass(frozen=True, slots=True)
class ApifySearchRequest:
    keyword: str
    country: str
    max_results: int = 15
    actor_id: str = "apify/google-search-scraper"
    results_per_page: int = 15
    max_pages_per_query: int = 1
    mobile_results: bool = False
    save_html: bool = False
    timeout_seconds: float = 90.0
    dry_run: bool = False

    def __post_init__(self) -> None:
        if not self.keyword.strip():
            raise ValueError("keyword is required")
        if not self.country.strip():
            raise ValueError("country is required")
        if self.max_results < 1 or self.max_results > 20:
            raise ValueError("max_results must be 1-20")
        object.__setattr__(self, "max_results", int(self.max_results))
        object.__setattr__(self, "results_per_page", int(self.results_per_page))

    @property
    def query(self) -> str:
        return f'{self.keyword} "{self.country}"'

    @property
    def payload_hash(self) -> str:
        payload = {
            "keyword": self.keyword, "country": self.country,
            "max_results": self.max_results, "actor_id": self.actor_id,
            "results_per_page": self.results_per_page,
            "max_pages_per_query": self.max_pages_per_query,
            "mobile_results": self.mobile_results, "save_html": self.save_html,
        }
        return sha256(dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RawSearchResult:
    raw_result_id: str
    title: str
    url: str
    displayed_url: str
    snippet: str
    position: int
    source: str
    source_query: str
    raw_payload: dict[str, Any]
    captured_at: str


@dataclass(frozen=True, slots=True)
class FilteredResult:
    """Result after running through the full pre-ingestion pipeline."""
    raw_result_id: str
    original_url: str
    canonical_domain: str | None
    classification: str  # CandidateClassification or ExclusionReason
    exclusion_reason: str | None
    matched_brand_or_platform: str | None
    registry_version: str
    policy_version: str
    research_decision: str | None  # RESEARCH_QUEUED, RESEARCH_LATER, REJECTED_BUSINESS, etc.
    research_priority: str | None
    pre_screen_score: int | None
    candidate_id: str | None
    reason_codes: tuple[str, ...]
    title: str
    snippet: str
    timestamp: str

    @property
    def is_preserved(self) -> bool:
        return self.exclusion_reason is None and self.candidate_id is not None

    @property
    def is_excluded(self) -> bool:
        return self.exclusion_reason is not None


@dataclass(frozen=True, slots=True)
class PreIngestionPipelineResult:
    """Complete output of one pre-ingestion pipeline run."""
    search_request: dict[str, Any]
    search_plan: dict[str, Any]
    raw_results: tuple[RawSearchResult, ...]
    filtered_results: tuple[FilteredResult, ...]
    summary: dict[str, Any]
    actor_run_id: str | None
    dataset_id: str | None
    raw_result_count: int
    accepted_count: int
    excluded_count: int
    duplicate_count: int
    fixture_path: str | None
    fixture_hash: str | None
    execution_duration_seconds: float
    technical_warnings: tuple[str, ...]
    captured_at: str
