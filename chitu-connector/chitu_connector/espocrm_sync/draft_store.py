"""Draft snapshot identity and content-integrity boundary.

This module is an offline reference implementation only.  It stores immutable
draft snapshots in process memory and deliberately has no CRM, approval,
provider, queue, worker, or delivery dependency.  Future persistent adapters
can implement :class:`DraftStore` without changing the snapshot contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from threading import RLock
from types import MappingProxyType
from typing import Mapping, Protocol

from chitu_connector.espocrm_sync.email_draft_generation import DraftEvidenceReference


DRAFT_STORE_VERSION = "c11.4-draft-store-boundary-v1"

_FORBIDDEN_METADATA_KEY_TOKENS = (
    "chainofthought",
    "hiddenreasoning",
    "reasoning",
    "prompt",
    "modeltrace",
)
_FORBIDDEN_METADATA_VALUE_PHRASES = (
    "chain of thought",
    "hidden reasoning",
    "ai reasoning",
    "internal prompt",
    "model trace",
)


@dataclass(frozen=True, slots=True)
class DraftSnapshotInput:
    """The content and trace references eligible for a DraftStore snapshot.

    The contract purposefully has no prompt, reasoning, or model-trace field.
    ``metadata`` is limited to JSON-compatible business metadata and is
    validated before it can enter the store.
    """

    draft_id: str
    lead_id: str
    subject: str
    body: str
    metadata: Mapping[str, object]
    evidence_references: tuple[DraftEvidenceReference, ...]
    score_snapshot_reference: str
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class DraftSnapshot:
    """Immutable saved snapshot with its deterministic content hash."""

    draft_id: str
    lead_id: str
    subject: str
    body: str
    metadata: Mapping[str, object]
    evidence_references: tuple[DraftEvidenceReference, ...]
    score_snapshot_reference: str
    generated_at: datetime
    content_hash: str
    store_version: str = DRAFT_STORE_VERSION


@dataclass(frozen=True, slots=True)
class DraftContentReference:
    """Identity and integrity pair retained by future approval and send records."""

    draft_id: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class SnapshotVerification:
    """Safe, side-effect-free result of matching approval and send references."""

    verified: bool
    reason_code: str | None = None


class DraftStore(Protocol):
    """Persistence seam for immutable draft snapshots."""

    def save(self, snapshot_input: DraftSnapshotInput) -> DraftSnapshot: ...

    def get(self, draft_id: str) -> DraftSnapshot | None: ...

    def get_content_hash(self, draft_id: str) -> str | None: ...

    def verify_snapshot(
        self,
        approved: DraftContentReference,
        send_execution: DraftContentReference,
    ) -> SnapshotVerification: ...


class InMemoryDraftStore:
    """Thread-safe deterministic reference store with no external side effects."""

    def __init__(self) -> None:
        self._snapshots_by_id: dict[str, DraftSnapshot] = {}
        self._lock = RLock()

    @property
    def snapshot_count(self) -> int:
        """Reference-only observability for deterministic tests."""

        with self._lock:
            return len(self._snapshots_by_id)

    def save(self, snapshot_input: DraftSnapshotInput) -> DraftSnapshot:
        _validate_input(snapshot_input)
        candidate = _to_snapshot(snapshot_input)
        with self._lock:
            existing = self._snapshots_by_id.get(candidate.draft_id)
            if existing is None:
                self._snapshots_by_id[candidate.draft_id] = candidate
                return candidate
            if _same_snapshot_identity(existing, candidate):
                return existing
            raise ValueError("draft id already has a different snapshot")

    def get(self, draft_id: str) -> DraftSnapshot | None:
        _require_identifier("draft_id", draft_id)
        with self._lock:
            return self._snapshots_by_id.get(draft_id)

    def get_content_hash(self, draft_id: str) -> str | None:
        snapshot = self.get(draft_id)
        return snapshot.content_hash if snapshot is not None else None

    def verify_snapshot(
        self,
        approved: DraftContentReference,
        send_execution: DraftContentReference,
    ) -> SnapshotVerification:
        if not _valid_reference(approved):
            return SnapshotVerification(False, "INVALID_APPROVAL_SNAPSHOT_REFERENCE")
        if not _valid_reference(send_execution):
            return SnapshotVerification(False, "INVALID_SEND_SNAPSHOT_REFERENCE")
        if approved.draft_id != send_execution.draft_id:
            return SnapshotVerification(False, "DRAFT_ID_MISMATCH")
        if approved.content_hash != send_execution.content_hash:
            return SnapshotVerification(False, "CONTENT_HASH_MISMATCH")
        actual_hash = self.get_content_hash(approved.draft_id)
        if actual_hash is None:
            return SnapshotVerification(False, "SNAPSHOT_NOT_FOUND")
        if actual_hash != approved.content_hash:
            return SnapshotVerification(False, "SNAPSHOT_HASH_MISMATCH")
        return SnapshotVerification(True)


def _to_snapshot(value: DraftSnapshotInput) -> DraftSnapshot:
    metadata = _freeze_metadata(value.metadata)
    references = tuple(sorted(value.evidence_references, key=lambda item: (item.evidence_id, item.source_url)))
    return DraftSnapshot(
        draft_id=value.draft_id.strip(),
        lead_id=value.lead_id.strip(),
        subject=value.subject,
        body=value.body,
        metadata=metadata,
        evidence_references=references,
        score_snapshot_reference=value.score_snapshot_reference.strip(),
        generated_at=value.generated_at.astimezone(timezone.utc),
        content_hash=_content_hash(value.subject, value.body, metadata, references, value.score_snapshot_reference),
    )


def _content_hash(
    subject: str,
    body: str,
    metadata: Mapping[str, object],
    evidence_references: tuple[DraftEvidenceReference, ...],
    score_snapshot_reference: str,
) -> str:
    payload = {
        "body": body,
        "evidenceReferences": [
            {"evidenceId": item.evidence_id, "sourceUrl": item.source_url}
            for item in evidence_references
        ],
        "metadata": _json_value(metadata),
        "scoreSnapshotReference": score_snapshot_reference.strip(),
        "subject": subject,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _same_snapshot_identity(existing: DraftSnapshot, candidate: DraftSnapshot) -> bool:
    return (
        existing.lead_id == candidate.lead_id
        and existing.content_hash == candidate.content_hash
        and existing.score_snapshot_reference == candidate.score_snapshot_reference
        and existing.evidence_references == candidate.evidence_references
    )


def _validate_input(value: object) -> None:
    if not isinstance(value, DraftSnapshotInput):
        raise TypeError("snapshot_input must be a DraftSnapshotInput")
    _require_identifier("draft_id", value.draft_id)
    _require_identifier("lead_id", value.lead_id)
    _require_text("subject", value.subject)
    _require_text("body", value.body)
    _require_identifier("score_snapshot_reference", value.score_snapshot_reference)
    if not isinstance(value.generated_at, datetime) or value.generated_at.tzinfo is None or value.generated_at.utcoffset() is None:
        raise ValueError("invalid generated_at")
    if not isinstance(value.evidence_references, tuple) or not value.evidence_references:
        raise ValueError("evidence_references must be a non-empty tuple")
    for reference in value.evidence_references:
        if not isinstance(reference, DraftEvidenceReference) or not reference.evidence_id.strip() or not reference.source_url.strip():
            raise ValueError("invalid evidence reference")
    _freeze_metadata(value.metadata)


def _freeze_metadata(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("metadata must be a mapping")
    frozen: dict[str, object] = {}
    for key in sorted(value):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("metadata keys must be non-empty strings")
        normalized_key = "".join(character for character in key.casefold() if character.isalnum())
        if any(token in normalized_key for token in _FORBIDDEN_METADATA_KEY_TOKENS):
            raise ValueError("metadata contains forbidden reasoning or prompt content")
        frozen[key] = _freeze_metadata_value(value[key])
    return MappingProxyType(frozen)


def _freeze_metadata_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        lowered = value.casefold()
        if any(phrase in lowered for phrase in _FORBIDDEN_METADATA_VALUE_PHRASES):
            raise ValueError("metadata contains forbidden reasoning or prompt content")
        return value
    if isinstance(value, Mapping):
        return _freeze_metadata(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_metadata_value(item) for item in value)
    raise ValueError("metadata must contain JSON-compatible values")


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _valid_reference(value: object) -> bool:
    return (
        isinstance(value, DraftContentReference)
        and isinstance(value.draft_id, str)
        and bool(value.draft_id.strip())
        and isinstance(value.content_hash, str)
        and bool(value.content_hash.strip())
    )


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {name}")


def _require_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {name}")
