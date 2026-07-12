"""V1 contract model and offline structural validation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from urllib.parse import urlparse


CONTRACT_VERSION = "1.0"
_TOP_LEVEL_REQUIRED = {
    "contract_version", "identity", "qualification", "company", "source", "research",
    "score", "recommendation", "evidence", "provenance", "sync",
}
_TOP_LEVEL_OPTIONAL = {"account_transition_proposal", "opportunity_proposal"}


@dataclass(frozen=True, slots=True)
class SyncContractPayload:
    contract_version: str
    identity: Mapping[str, Any]
    qualification: Mapping[str, Any]
    company: Mapping[str, Any]
    source: Mapping[str, Any]
    research: Mapping[str, Any]
    score: Mapping[str, Any]
    recommendation: Mapping[str, Any]
    evidence: tuple[Mapping[str, Any], ...]
    provenance: Mapping[str, Any]
    sync: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "identity": deepcopy(dict(self.identity)),
            "qualification": deepcopy(dict(self.qualification)),
            "company": deepcopy(dict(self.company)),
            "source": deepcopy(dict(self.source)),
            "research": deepcopy(dict(self.research)),
            "score": deepcopy(dict(self.score)),
            "recommendation": deepcopy(dict(self.recommendation)),
            "evidence": [deepcopy(dict(item)) for item in self.evidence],
            "provenance": deepcopy(dict(self.provenance)),
            "sync": deepcopy(dict(self.sync)),
        }


def validate_sync_contract(payload: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    keys = set(payload)
    errors.extend(f"MISSING_FIELD:{name}" for name in sorted(_TOP_LEVEL_REQUIRED - keys))
    errors.extend(f"UNKNOWN_FIELD:{name}" for name in sorted(keys - _TOP_LEVEL_REQUIRED - _TOP_LEVEL_OPTIONAL))
    if errors:
        return tuple(errors)
    if payload.get("contract_version") != CONTRACT_VERSION:
        errors.append("INVALID_CONTRACT_VERSION")
    _validate_object(payload, "identity", {"candidate_id", "canonical_domain", "record_identity_key"}, errors)
    _validate_object(payload, "qualification", {"status", "customer_type"}, errors)
    _validate_object(payload, "company", {"name", "website", "country_code"}, errors)
    _validate_object(payload, "source", {"channel", "source_url"}, errors)
    _validate_object(payload, "research", {"status", "website_accessible", "failure_code"}, errors)
    _validate_object(payload, "score", {"value", "score_tier", "aggregate_confidence", "evidence_coverage", "rules_version", "result_hash"}, errors)
    _validate_object(payload, "recommendation", {"best_first_product", "cross_sell_path", "reason_codes"}, errors)
    _validate_object(payload, "provenance", {"engine_version", "evidence_schema_version", "evidence_snapshot_hash", "official_brand_excluded", "official_brand_registry_version"}, errors)
    _validate_object(payload, "sync", {"idempotency_key", "payload_hash", "requested_at"}, errors)
    _validate_strings(payload, errors)
    _validate_evidence(payload.get("evidence"), errors)
    return tuple(errors)


def _validate_object(payload: Mapping[str, Any], name: str, required: set[str], errors: list[str]) -> None:
    value = payload.get(name)
    if not isinstance(value, Mapping):
        errors.append(f"INVALID_OBJECT:{name}")
        return
    keys = set(value)
    errors.extend(f"MISSING_FIELD:{name}.{field}" for field in sorted(required - keys))
    errors.extend(f"UNKNOWN_FIELD:{name}.{field}" for field in sorted(keys - required))


def _validate_strings(payload: Mapping[str, Any], errors: list[str]) -> None:
    identity = payload.get("identity", {})
    company = payload.get("company", {})
    source = payload.get("source", {})
    score = payload.get("score", {})
    provenance = payload.get("provenance", {})
    sync = payload.get("sync", {})
    if isinstance(identity, Mapping):
        if not _valid_domain(identity.get("canonical_domain")):
            errors.append("INVALID_CANONICAL_DOMAIN")
        for name in ("candidate_id", "record_identity_key"):
            if not _non_empty(identity.get(name)):
                errors.append(f"INVALID_FIELD:identity.{name}")
    if isinstance(company, Mapping):
        if not _non_empty(company.get("name")):
            errors.append("INVALID_FIELD:company.name")
        if not _valid_url(company.get("website")):
            errors.append("INVALID_FIELD:company.website")
        country = company.get("country_code")
        if country is not None and (not isinstance(country, str) or len(country) != 2 or country != country.upper()):
            errors.append("INVALID_FIELD:company.country_code")
    if isinstance(source, Mapping):
        if source.get("channel") not in {"WEB_SEARCH", "CONTROLLED_MANUAL_INPUT", "APPROVED_IMPORT"}:
            errors.append("INVALID_FIELD:source.channel")
        if source.get("source_url") is not None and not _valid_url(source.get("source_url")):
            errors.append("INVALID_FIELD:source.source_url")
    if isinstance(score, Mapping):
        if not isinstance(score.get("value"), (int, float)):
            errors.append("INVALID_FIELD:score.value")
        for name in ("aggregate_confidence", "evidence_coverage"):
            if not isinstance(score.get(name), (int, float)):
                errors.append(f"INVALID_FIELD:score.{name}")
        for name in ("score_tier", "rules_version", "result_hash"):
            if not _non_empty(score.get(name)):
                errors.append(f"INVALID_FIELD:score.{name}")
    if isinstance(provenance, Mapping):
        for name in ("engine_version", "evidence_schema_version", "evidence_snapshot_hash"):
            if not _non_empty(provenance.get(name)):
                errors.append(f"INVALID_FIELD:provenance.{name}")
    if isinstance(sync, Mapping):
        for name in ("idempotency_key", "payload_hash"):
            if not _non_empty(sync.get(name)):
                errors.append(f"INVALID_FIELD:sync.{name}")
        if not _valid_datetime(sync.get("requested_at")):
            errors.append("INVALID_FIELD:sync.requested_at")


def _validate_evidence(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("MISSING_EVIDENCE")
        return
    required = {"evidence_id", "claim_type", "claim", "source_url", "evidence_text", "confidence", "captured_at", "schema_version"}
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"INVALID_EVIDENCE:{index}")
            continue
        keys = set(item)
        errors.extend(f"MISSING_EVIDENCE_FIELD:{index}.{name}" for name in sorted(required - keys))
        errors.extend(f"UNKNOWN_EVIDENCE_FIELD:{index}.{name}" for name in sorted(keys - required))
        if not _non_empty(item.get("evidence_id")) or not _non_empty(item.get("claim_type")):
            errors.append(f"INVALID_EVIDENCE_REFERENCE:{index}")
        if not _valid_url(item.get("source_url")):
            errors.append(f"INVALID_EVIDENCE_URL:{index}")
        text = item.get("evidence_text")
        if not _non_empty(text) or len(str(text)) > 1000:
            errors.append(f"INVALID_EVIDENCE_TEXT:{index}")
        if not isinstance(item.get("confidence"), (int, float)):
            errors.append(f"INVALID_EVIDENCE_CONFIDENCE:{index}")
        if not _valid_datetime(item.get("captured_at")):
            errors.append(f"INVALID_EVIDENCE_TIMESTAMP:{index}")


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_domain(value: Any) -> bool:
    return isinstance(value, str) and "." in value and value == value.lower() and " " not in value


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
