"""Deterministic extraction of factual evidence from C05 research output.

This adapter consumes only the serialized ``WebsiteResearchPipelineResult``
boundary. It performs no persistence, CRM access, network I/O, AI call, or
workflow update.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from chitu_connector.vendored.contracts.website_research import EvidenceItem


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_EXTRACTOR_VERSION = "c07-evidence-extraction-v1"
_MAX_CLAIM_CHARS = 500
_MAX_EVIDENCE_TEXT_CHARS = 1_000
_CONFIDENCE_BY_EVIDENCE_TYPE = {
    "title": 0.95,
    "meta_description": 0.90,
    "visible_text": 0.85,
}


class EvidenceExtractor(Protocol):
    """Boundary for converting serialized C05 output into evidence items."""

    extractor_version: str

    def extract(self, pipeline_result: Mapping[str, Any]) -> list[EvidenceItem]: ...


class WebsiteResearchEvidenceExtractor:
    """Extracts source-backed website observations in stable page order."""

    extractor_version = _EXTRACTOR_VERSION

    def extract(self, pipeline_result: Mapping[str, Any]) -> list[EvidenceItem]:
        if not isinstance(pipeline_result, Mapping):
            return []

        pages = pipeline_result.get("pages")
        if not isinstance(pages, (list, tuple)):
            return []

        fallback_captured_at = _parse_timestamp(
            pipeline_result.get("completed_at") or pipeline_result.get("started_at")
        )
        evidence_items: list[EvidenceItem] = []
        seen: set[str] = set()

        for page in pages:
            if not isinstance(page, Mapping) or page.get("fetch_status") != "SUCCESS":
                continue

            source_url = _source_url(page)
            if source_url is None:
                continue

            captured_at = _parse_timestamp(page.get("fetched_at"), fallback_captured_at)
            for claim_type, evidence_type, evidence_text in _page_observations(page):
                dedupe_key = _dedupe_key(source_url, evidence_text)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=_evidence_id(claim_type, source_url, evidence_text),
                        claim_type=claim_type,
                        claim=_claim_for(claim_type, evidence_text),
                        source_url=source_url,
                        page_title=_clean_text(page.get("title")),
                        evidence_text=evidence_text,
                        evidence_type=evidence_type,
                        confidence=_CONFIDENCE_BY_EVIDENCE_TYPE[evidence_type],
                        captured_at=captured_at,
                        extractor_version=self.extractor_version,
                    )
                )

        return evidence_items


def _page_observations(page: Mapping[str, Any]) -> tuple[tuple[str, str, str], ...]:
    observations: list[tuple[str, str, str]] = []
    for field, claim_type, evidence_type in (
        ("title", "page_title", "title"),
        ("meta_description", "meta_description", "meta_description"),
        ("text_content", "visible_text", "visible_text"),
    ):
        value = _clean_text(page.get(field))
        if value:
            observations.append((claim_type, evidence_type, value))
    return tuple(observations)


def _source_url(page: Mapping[str, Any]) -> str | None:
    for key in ("final_url", "requested_url"):
        value = page.get(key)
        if isinstance(value, str) and _is_public_http_url(value):
            return value
    return None


def _is_public_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:_MAX_EVIDENCE_TEXT_CHARS]


def _claim_for(claim_type: str, evidence_text: str) -> str:
    if claim_type != "visible_text":
        return evidence_text[:_MAX_CLAIM_CHARS]
    sentence_end = min((index for index in (evidence_text.find("."), evidence_text.find("!"), evidence_text.find("?")) if index >= 0), default=-1)
    claim = evidence_text[: sentence_end + 1] if sentence_end >= 0 else evidence_text
    return claim[:_MAX_CLAIM_CHARS]


def _evidence_id(claim_type: str, source_url: str, evidence_text: str) -> str:
    payload = "\x1f".join((claim_type, source_url, evidence_text, _EXTRACTOR_VERSION))
    return f"ev_{sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _dedupe_key(source_url: str, evidence_text: str) -> str:
    return sha256("\x1f".join((source_url, evidence_text)).encode("utf-8")).hexdigest()


def _parse_timestamp(value: Any, fallback: datetime = _EPOCH) -> datetime:
    if not isinstance(value, str):
        return fallback
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
