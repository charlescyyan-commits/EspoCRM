"""Internal, deterministic Master Prospect deduplication for Discovery data.

This module intentionally has no persistence, HTTP, provider, worker, runner,
or CRM dependency.  It accepts immutable ``RawCandidate`` values produced by
the frozen provider contract and returns an in-memory, traceable Master
Prospect view without changing those raw values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable, Mapping

from .models import RawCandidate
from .normalization import normalize_domain


RULE_ROOT_DOMAIN = "ROOT_DOMAIN"
RULE_CANONICAL_WEBSITE = "CANONICAL_WEBSITE"
RULE_COMPANY_NAME = "COMPANY_NAME"
RULE_COMPANY_COUNTRY = "COMPANY_COUNTRY"
RULE_COMPANY_CITY = "COMPANY_CITY"
RULE_NEW_MASTER = "NEW_MASTER"

_MATCH_CONFIDENCE: Mapping[str, float] = {
    RULE_ROOT_DOMAIN: 1.0,
    RULE_CANONICAL_WEBSITE: 0.99,
    RULE_COMPANY_NAME: 0.95,
    RULE_COMPANY_COUNTRY: 0.94,
    RULE_COMPANY_CITY: 0.93,
    RULE_NEW_MASTER: 1.0,
}

# Ordered longest-first so a multi-token legal suffix is removed as one unit.
# This is a deliberately small, deterministic list of common terminal company
# designators, not a country/legal-entity inference service.
_COMPANY_SUFFIXES: tuple[tuple[str, ...], ...] = (
    ("incorporated",),
    ("corporation",),
    ("limited",),
    ("gmbh",),
    ("llc",),
    ("ltd",),
    ("inc",),
    ("plc",),
    ("corp",),
    ("company",),
    ("co",),
    ("bv",),
    ("b", "v"),
    ("sarl",),
    ("sa",),
    ("ag",),
    ("oy",),
    ("ab",),
    ("pte",),
    ("pty",),
)


@dataclass(frozen=True, slots=True)
class RawProspect:
    """A Discovery record with its original provider result kept intact.

    ``raw_candidate`` and both metadata mappings are retained by reference and
    are never altered by this module.  ``discovery_id`` is optional contextual
    metadata (for example a future discovery batch ID), not a CRM identifier.
    """

    provider_name: str
    raw_candidate: RawCandidate
    city: str | None = None
    provider_metadata: Mapping[str, Any] = field(default_factory=dict)
    discovery_id: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedRawProspect:
    """Deterministic comparison values derived from one raw prospect."""

    raw_prospect: RawProspect
    record_id: str
    normalized_domain: str | None
    canonical_website: str | None
    canonical_name: str | None
    country: str | None
    city: str | None


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    provider_name: str
    provider_candidate_id: str
    metadata: Mapping[str, Any]
    raw_payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class DiscoveryHistoryEntry:
    record_id: str
    provider_name: str
    provider_candidate_id: str
    source_url: str | None
    discovery_id: str | None


@dataclass(frozen=True, slots=True)
class MergeTrace:
    record_id: str
    matched_record_id: str | None
    matching_rule: str
    confidence: float
    reason: str
    merge_timestamp: str


@dataclass(frozen=True, slots=True)
class MasterProspect:
    master_id: str
    normalized_domain: str | None
    canonical_name: str | None
    website: str | None
    country: str | None
    city: str | None
    source_count: int
    provider_list: tuple[str, ...]
    matched_raw_records: tuple[RawProspect, ...]
    provider_metadata: tuple[ProviderMetadata, ...]
    discovery_history: tuple[DiscoveryHistoryEntry, ...]
    merge_traces: tuple[MergeTrace, ...]
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class MasterProspectMergeResult:
    masters: tuple[MasterProspect, ...]
    merge_traces: tuple[MergeTrace, ...]


class ProspectNormalizer:
    """Normalizes comparison fields without mutating raw provider output."""

    def normalize(self, prospect: RawProspect, *, occurrence: int = 0) -> NormalizedRawProspect:
        candidate = prospect.raw_candidate
        domain = normalize_domain(candidate.domain)
        website_domain = normalize_domain(candidate.source_url) or domain
        return NormalizedRawProspect(
            raw_prospect=prospect,
            record_id=_record_id(prospect, occurrence),
            normalized_domain=domain,
            canonical_website=f"https://{website_domain}" if website_domain else None,
            canonical_name=normalize_company_name(candidate.company_name),
            country=normalize_country(candidate.country),
            city=normalize_city(prospect.city),
        )


class ProspectMatcher:
    """Exact-only matching rules in the Phase3C04 priority order."""

    def match_rule(self, left: NormalizedRawProspect, right: NormalizedRawProspect) -> str | None:
        if left.normalized_domain and left.normalized_domain == right.normalized_domain:
            return RULE_ROOT_DOMAIN
        if left.canonical_website and left.canonical_website == right.canonical_website:
            return RULE_CANONICAL_WEBSITE

        if not _same_name(left, right):
            return None

        # A bare exact name is only safe when neither record supplies a
        # geographic discriminator.  Otherwise use the tighter geographic
        # rules below; no fuzzy or inferred comparison is ever performed.
        if not any((left.country, right.country, left.city, right.city)):
            return RULE_COMPANY_NAME
        if left.country and left.country == right.country:
            return RULE_COMPANY_COUNTRY
        if left.city and left.city == right.city:
            return RULE_COMPANY_CITY
        return None


class MasterProspectMerger:
    """Creates traceable Master Prospect clusters from normalized raw records."""

    def __init__(self, matcher: ProspectMatcher | None = None) -> None:
        self._matcher = matcher or ProspectMatcher()

    def merge(
        self,
        prospects: Iterable[RawProspect],
        *,
        merge_timestamp: str | None = None,
    ) -> MasterProspectMergeResult:
        timestamp = merge_timestamp or _utc_timestamp()
        ordered_prospects = tuple(sorted(prospects, key=_raw_sort_key))
        normalized = tuple(
            ProspectNormalizer().normalize(prospect, occurrence=index)
            for index, prospect in enumerate(ordered_prospects)
        )
        groups = _groups(normalized, self._matcher)
        masters = tuple(self._master(group, timestamp) for group in groups)
        masters = tuple(sorted(masters, key=lambda master: master.master_id))
        traces = tuple(trace for master in masters for trace in master.merge_traces)
        return MasterProspectMergeResult(masters=masters, merge_traces=traces)

    def _master(self, group: tuple[NormalizedRawProspect, ...], timestamp: str) -> MasterProspect:
        records = tuple(sorted(group, key=lambda item: item.record_id))
        primary = _primary_record(records)
        traces = _traces(records, self._matcher, timestamp)
        providers = tuple(sorted({item.raw_prospect.provider_name.strip() for item in records}, key=str.casefold))
        metadata = tuple(
            ProviderMetadata(
                provider_name=item.raw_prospect.provider_name,
                provider_candidate_id=item.raw_prospect.raw_candidate.provider_candidate_id,
                metadata=item.raw_prospect.provider_metadata,
                raw_payload=item.raw_prospect.raw_candidate.raw_payload,
            )
            for item in records
        )
        history = tuple(
            DiscoveryHistoryEntry(
                record_id=item.record_id,
                provider_name=item.raw_prospect.provider_name,
                provider_candidate_id=item.raw_prospect.raw_candidate.provider_candidate_id,
                source_url=item.raw_prospect.raw_candidate.source_url,
                discovery_id=item.raw_prospect.discovery_id,
            )
            for item in records
        )
        return MasterProspect(
            master_id=_master_id(records, primary),
            normalized_domain=primary.normalized_domain or _first_value(records, "canonical_website", strip_scheme=True),
            canonical_name=primary.canonical_name or _first_value(records, "canonical_name"),
            website=primary.canonical_website or _first_value(records, "canonical_website"),
            country=primary.country or _first_value(records, "country"),
            city=primary.city or _first_value(records, "city"),
            source_count=len(providers),
            provider_list=providers,
            matched_raw_records=tuple(item.raw_prospect for item in records),
            provider_metadata=metadata,
            discovery_history=history,
            merge_traces=traces,
            created_at=timestamp,
            updated_at=timestamp,
        )


def normalize_company_name(value: str | None) -> str | None:
    """Return an exact-comparison key while retaining the original raw name.

    Terminal punctuation, whitespace, case, and common legal company suffixes
    are normalized away.  Only a terminal suffix is removed, and never when it
    would leave an empty name.
    """

    if not value or not value.strip():
        return None
    normalized = unicodedata.normalize("NFKC", value).casefold()
    tokens = tuple(token for token in re.split(r"[^\w]+", normalized) if token)
    if not tokens:
        return None
    remaining = _strip_company_suffixes(tokens)
    canonical = "".join(remaining)
    return canonical or "".join(tokens) or None


def normalize_country(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    return normalized.upper() if re.fullmatch(r"[A-Za-z]{2}", normalized) else normalized.casefold()


def normalize_city(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split()) or None


def _same_name(left: NormalizedRawProspect, right: NormalizedRawProspect) -> bool:
    return bool(left.canonical_name and left.canonical_name == right.canonical_name)


def _strip_company_suffixes(tokens: tuple[str, ...]) -> tuple[str, ...]:
    remaining = tokens
    while len(remaining) > 1:
        suffix = next(
            (candidate for candidate in _COMPANY_SUFFIXES if remaining[-len(candidate):] == candidate),
            None,
        )
        if suffix is None or len(remaining) == len(suffix):
            break
        remaining = remaining[:-len(suffix)]
    return remaining


def _groups(
    records: tuple[NormalizedRawProspect, ...], matcher: ProspectMatcher
) -> tuple[tuple[NormalizedRawProspect, ...], ...]:
    parents = list(range(len(records)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[max(left_root, right_root)] = min(left_root, right_root)

    for left_index, left in enumerate(records):
        for right_index in range(left_index + 1, len(records)):
            if matcher.match_rule(left, records[right_index]):
                union(left_index, right_index)

    grouped: dict[int, list[NormalizedRawProspect]] = {}
    for index, record in enumerate(records):
        grouped.setdefault(find(index), []).append(record)
    return tuple(
        tuple(sorted(group, key=lambda item: item.record_id))
        for _, group in sorted(grouped.items(), key=lambda pair: pair[1][0].record_id)
    )


def _traces(
    records: tuple[NormalizedRawProspect, ...], matcher: ProspectMatcher, timestamp: str
) -> tuple[MergeTrace, ...]:
    traces: list[MergeTrace] = []
    for index, record in enumerate(records):
        matches = [
            (matcher.match_rule(record, previous), previous)
            for previous in records[:index]
        ]
        matched = [(rule, previous) for rule, previous in matches if rule]
        if not matched:
            traces.append(MergeTrace(
                record_id=record.record_id,
                matched_record_id=None,
                matching_rule=RULE_NEW_MASTER,
                confidence=_MATCH_CONFIDENCE[RULE_NEW_MASTER],
                reason="No earlier deterministic match; created Master Prospect cluster.",
                merge_timestamp=timestamp,
            ))
            continue
        rule, prior = min(matched, key=lambda pair: (_rule_rank(pair[0]), pair[1].record_id))
        traces.append(MergeTrace(
            record_id=record.record_id,
            matched_record_id=prior.record_id,
            matching_rule=rule,
            confidence=_MATCH_CONFIDENCE[rule],
            reason=_reason(rule, record, prior),
            merge_timestamp=timestamp,
        ))
    return tuple(traces)


def _primary_record(records: tuple[NormalizedRawProspect, ...]) -> NormalizedRawProspect:
    return min(
        records,
        key=lambda item: (
            0 if item.normalized_domain else 1,
            0 if item.canonical_website else 1,
            0 if item.canonical_name else 1,
            item.normalized_domain or "",
            item.canonical_website or "",
            item.canonical_name or "",
            item.country or "",
            item.city or "",
            _raw_sort_key(item.raw_prospect),
        ),
    )


def _first_value(
    records: tuple[NormalizedRawProspect, ...], attribute: str, *, strip_scheme: bool = False
) -> str | None:
    values = sorted({getattr(record, attribute) for record in records if getattr(record, attribute)})
    if not values:
        return None
    value = values[0]
    return value.removeprefix("https://") if strip_scheme else value


def _master_id(records: tuple[NormalizedRawProspect, ...], primary: NormalizedRawProspect) -> str:
    identity = (
        primary.normalized_domain
        or primary.canonical_website
        or "|".join(filter(None, (primary.canonical_name, primary.country, primary.city)))
        or "|".join(record.record_id for record in records)
    )
    return "mp_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _record_id(prospect: RawProspect, occurrence: int) -> str:
    candidate = prospect.raw_candidate
    payload = json.dumps(candidate.raw_payload, sort_keys=True, separators=(",", ":"), default=str)
    identity = "|".join((
        prospect.provider_name.strip().casefold(),
        candidate.provider_candidate_id.strip(),
        prospect.discovery_id or "",
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        str(occurrence),
    ))
    return "raw_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _raw_sort_key(prospect: RawProspect) -> tuple[str, str, str, str, str, str, str, str]:
    candidate = prospect.raw_candidate
    return (
        prospect.provider_name.casefold().strip(),
        candidate.provider_candidate_id.strip(),
        candidate.company_name,
        candidate.domain or "",
        candidate.source_url or "",
        candidate.country or "",
        prospect.city or "",
        json.dumps(
            (prospect.discovery_id, prospect.provider_metadata, candidate.raw_payload),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ),
    )


def _rule_rank(rule: str) -> int:
    return {
        RULE_ROOT_DOMAIN: 1,
        RULE_CANONICAL_WEBSITE: 2,
        RULE_COMPANY_NAME: 3,
        RULE_COMPANY_COUNTRY: 4,
        RULE_COMPANY_CITY: 5,
    }[rule]


def _reason(rule: str, record: NormalizedRawProspect, prior: NormalizedRawProspect) -> str:
    if rule == RULE_ROOT_DOMAIN:
        return f"Root domain exact match: {record.normalized_domain}."
    if rule == RULE_CANONICAL_WEBSITE:
        return f"Canonical website exact match: {record.canonical_website}."
    if rule == RULE_COMPANY_NAME:
        return f"Canonical company name exact match: {record.canonical_name}."
    if rule == RULE_COMPANY_COUNTRY:
        return f"Canonical company and country exact match: {record.canonical_name} / {record.country}."
    return f"Canonical company and city exact match: {record.canonical_name} / {record.city}."


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
