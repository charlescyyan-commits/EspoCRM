"""Deterministic identity and delivery keys for the V1 sync contract."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from json import dumps
from typing import Any, Mapping


CONTRACT_VERSION = "1.0"


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def record_identity_key(canonical_domain: str) -> str:
    return _digest(f"espocrm-lead-v1|{canonical_domain.lower()}")


def idempotency_key(
    canonical_domain: str,
    engine_version: str,
    score_rules_version: str,
    contract_version: str = CONTRACT_VERSION,
) -> str:
    return _digest(
        f"espocrm-sync-v1|{canonical_domain.lower()}|{engine_version}|{score_rules_version}|{contract_version}"
    )


def payload_hash(payload: Mapping[str, Any]) -> str:
    canonical = deepcopy(dict(payload))
    sync = dict(canonical.get("sync", {}))
    sync.pop("payload_hash", None)
    sync.pop("requested_at", None)
    canonical["sync"] = sync
    encoded = dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return _digest(encoded)


def evidence_snapshot_hash(evidence: list[dict[str, Any]]) -> str:
    encoded = dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return _digest(encoded)
