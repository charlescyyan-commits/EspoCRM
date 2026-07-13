"""Candidate normalisation and deterministic provider-plus-domain identity."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse

from .models import NormalizedCandidate, RawCandidate

_TRAILING_PUNCTUATION = ".,;:!?)]}>\"'"


def normalize_candidate(provider_name: str, candidate: RawCandidate) -> NormalizedCandidate | None:
    domain = normalize_domain(candidate.domain)
    if domain is None:
        return None
    source_url = normalize_source_url(candidate.source_url)
    company_name = " ".join(candidate.company_name.split())
    if not company_name:
        company_name = domain
    fingerprint = hashlib.sha256(f"{provider_name}|{domain}".encode("utf-8")).hexdigest()
    raw_payload_digest = hashlib.sha256(
        json.dumps(candidate.raw_payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
    return NormalizedCandidate(
        provider_name=provider_name,
        provider_candidate_id=candidate.provider_candidate_id.strip(),
        company_name=company_name,
        normalized_domain=domain,
        website=f"https://{domain}",
        source_url=source_url,
        country=" ".join(candidate.country.split()) if candidate.country else None,
        dedupe_fingerprint=fingerprint,
        raw_payload_digest=raw_payload_digest,
    )


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip().rstrip(_TRAILING_PUNCTUATION).strip()
    if not clean:
        return None
    parsed = urlparse(clean if "://" in clean else f"https://{clean}")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    domain = parsed.hostname.casefold().rstrip(".")
    while domain.startswith("www."):
        domain = domain[4:]
    if not domain or "." not in domain or not _valid_hostname(domain):
        return None
    return domain


def normalize_source_url(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip().rstrip(_TRAILING_PUNCTUATION).strip()
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return clean


def _valid_hostname(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", value))
