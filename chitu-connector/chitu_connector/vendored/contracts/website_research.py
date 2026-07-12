"""Typed, evidence-first contract for static public website research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any, Protocol
from urllib.parse import urlparse


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


class ResearchFailureCode(StrEnum):
    INVALID_URL = "INVALID_URL"
    DNS_FAILURE = "DNS_FAILURE"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    TLS_ERROR = "TLS_ERROR"
    HTTP_403 = "HTTP_403"
    HTTP_404 = "HTTP_404"
    HTTP_429 = "HTTP_429"
    HTTP_5XX = "HTTP_5XX"
    ROBOTS_RESTRICTED = "ROBOTS_RESTRICTED"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    EMPTY_CONTENT = "EMPTY_CONTENT"
    PARSE_FAILURE = "PARSE_FAILURE"
    PAGE_LIMIT_REACHED = "PAGE_LIMIT_REACHED"
    TOTAL_TIMEOUT = "TOTAL_TIMEOUT"
    ADAPTER_INTERNAL_ERROR = "ADAPTER_INTERNAL_ERROR"


@dataclass(frozen=True, slots=True)
class WebsiteResearchRequest:
    candidate_id: str
    canonical_domain: str
    website_url: str
    country: str
    expected_customer_types: tuple[str, ...] = ()
    expected_brands: tuple[str, ...] = ()
    expected_products: tuple[str, ...] = ()
    max_pages: int = 8
    timeout_seconds: float = 12.0
    total_timeout_seconds: float = 45.0
    adapter_version: str = "static-website-research-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_pages", int(self.max_pages))
        object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))
        object.__setattr__(self, "total_timeout_seconds", float(self.total_timeout_seconds))
        parsed = urlparse(self.website_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("website_url must be an absolute http(s) URL")
        host = parsed.hostname.lower().removeprefix("www.")
        if host != self.canonical_domain.lower().removeprefix("www."):
            raise ValueError("website_url must match canonical_domain")
        if not 1 <= self.max_pages <= 8:
            raise ValueError("max_pages must be between 1 and 8")
        if self.timeout_seconds <= 0 or self.total_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")

    @property
    def payload_hash(self) -> str:
        payload = asdict(self)
        return sha256(dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    claim_type: str
    claim: str
    source_url: str
    page_title: str
    evidence_text: str
    evidence_type: str
    confidence: float
    captured_at: datetime = field(default_factory=_now)
    extractor_version: str = "website-research-v1"

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class CustomerTypeCandidate:
    value: str
    evidence_ids: tuple[str, ...]
    is_inference: bool = False


@dataclass(frozen=True, slots=True)
class WebsiteResearchResult:
    candidate_id: str
    website_url: str
    final_url: str
    website_accessible: bool
    http_status: int | None
    page_title: str
    meta_description: str
    company_summary: str
    detected_brands: tuple[str, ...]
    detected_products: tuple[str, ...]
    customer_type_candidates: tuple[CustomerTypeCandidate, ...]
    business_signals: tuple[str, ...]
    contact_page_urls: tuple[str, ...]
    public_emails: tuple[str, ...]
    public_phones: tuple[str, ...]
    evidence_items: tuple[EvidenceItem, ...]
    visited_pages: tuple[str, ...]
    technical_warnings: tuple[str, ...]
    failure_code: ResearchFailureCode | None
    failure_message: str | None
    researched_at: datetime
    adapter_version: str
    payload_hash: str
    company_country: str | None = None
    company_country_code: str | None = None
    company_country_confidence: float = 0.0
    company_country_evidence_ids: tuple[str, ...] = ()
    company_country_inference: bool = False
    evidence_schema_version: str = "1.1"
    research_input_hash: str = ""
    research_output_hash: str = ""
    captured_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


class WebsiteResearchAdapter(Protocol):
    adapter_version: str

    def research(self, request: WebsiteResearchRequest) -> WebsiteResearchResult: ...
