"""Reference-only persistence behavior for website research evidence.

This module accepts only vendored :class:`EvidenceItem` values and an existing
EspoCRM Lead identifier.  It does not create or update Leads, and it has no
scoring, AI, email, or workflow responsibilities.

The production writer is PHP ``ChituSyncService::syncEvidence``. This adapter
is retained as a reference implementation and contract-test utility only; the
production connector must not depend on it at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from chitu_connector.espocrm_sync.idempotency import evidence_snapshot_hash
from chitu_connector.vendored.contracts.website_research import EvidenceItem


class ResearchEvidencePersistenceClient(Protocol):
    """Minimal EspoCRM operations required by the persistence adapter."""

    def find_research_evidence_for_snapshot(
        self,
        lead_id: str,
        snapshot_hash: str,
    ) -> Sequence[Mapping[str, Any]]: ...

    def find_research_evidence_by_identity(
        self,
        lead_id: str,
        source_url: str,
        claim_type: str,
        claim: str,
    ) -> Sequence[Mapping[str, Any]]: ...

    def create_research_evidence(self, body: Mapping[str, Any]) -> Mapping[str, Any]: ...


class EvidencePersistenceStatus(StrEnum):
    CREATED = "CREATED"
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class EvidencePersistenceResult:
    status: EvidencePersistenceStatus
    lead_id: str | None
    snapshot_hash: str | None
    evidence_ids: tuple[str, ...] = ()
    crm_ids: tuple[str, ...] = ()
    reason_code: str | None = None


class ResearchEvidencePersistenceAdapter:
    """Reference implementation and contract-test utility, not a runtime writer.

    Existing rows are first matched by Lead and snapshot, then by stable
    per-evidence identity. Complete snapshots are skipped; a partial prior
    attempt creates only missing rows. This makes retries deterministic and
    prevents duplicate CRM evidence rows when an otherwise identical fact is
    delivered in a later snapshot.
    """

    def __init__(self, client: ResearchEvidencePersistenceClient) -> None:
        self.client = client

    def persist(
        self,
        lead_id: str,
        evidence_items: Sequence[EvidenceItem],
    ) -> EvidencePersistenceResult:
        if not isinstance(lead_id, str) or not lead_id.strip():
            return EvidencePersistenceResult(
                EvidencePersistenceStatus.REJECTED,
                None,
                None,
                reason_code="INVALID_LEAD_ID",
            )
        if not isinstance(evidence_items, Sequence) or isinstance(evidence_items, (str, bytes)) or not evidence_items:
            return EvidencePersistenceResult(
                EvidencePersistenceStatus.REJECTED,
                lead_id,
                None,
                reason_code="MISSING_EVIDENCE",
            )

        records: list[tuple[EvidenceItem, dict[str, Any], str]] = []
        item_ids: set[str] = set()
        identities: set[str] = set()
        for item in evidence_items:
            error = _validation_error(item)
            if error:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.REJECTED,
                    lead_id,
                    None,
                    reason_code=error,
                )
            if item.evidence_id in item_ids:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.REJECTED,
                    lead_id,
                    None,
                    reason_code="DUPLICATE_EVIDENCE_ID",
                )
            item_ids.add(item.evidence_id)
            identity = evidence_identity_key(lead_id, item.source_url, item.claim_type, item.claim)
            if identity in identities:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.REJECTED,
                    lead_id,
                    None,
                    reason_code="DUPLICATE_EVIDENCE_IDENTITY",
                )
            identities.add(identity)
            records.append((item, _snapshot_item(item), identity))

        snapshot_hash = evidence_snapshot_hash([snapshot_item for _, snapshot_item, _ in records])
        evidence_ids = tuple(item.evidence_id for item, _, _ in records)
        try:
            existing = self.client.find_research_evidence_for_snapshot(lead_id, snapshot_hash)
        except Exception:
            return EvidencePersistenceResult(
                EvidencePersistenceStatus.FAILED,
                lead_id,
                snapshot_hash,
                evidence_ids,
                reason_code="LOOKUP_FAILED",
            )
        existing_by_identity = _existing_by_identity(lead_id, existing)
        expected_ids = tuple(item.evidence_id for item, _, _ in records)
        crm_ids_by_evidence_id = {
            item.evidence_id: existing_by_identity[identity]
            for item, _, identity in records
            if identity in existing_by_identity
        }
        if len(crm_ids_by_evidence_id) == len(expected_ids):
            return EvidencePersistenceResult(
                EvidencePersistenceStatus.SKIPPED,
                lead_id,
                snapshot_hash,
                evidence_ids,
                tuple(crm_ids_by_evidence_id[evidence_id] for evidence_id in expected_ids),
            )

        created_any = False
        for item, _, identity in records:
            if item.evidence_id in crm_ids_by_evidence_id:
                continue
            try:
                matching_records = self.client.find_research_evidence_by_identity(
                    lead_id,
                    item.source_url,
                    item.claim_type,
                    item.claim,
                )
            except Exception:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.FAILED,
                    lead_id,
                    snapshot_hash,
                    evidence_ids,
                    tuple(crm_ids_by_evidence_id[evidence_id] for evidence_id in expected_ids if evidence_id in crm_ids_by_evidence_id),
                    reason_code="LOOKUP_FAILED",
                )
            matching_by_identity = _existing_by_identity(lead_id, matching_records)
            matching_crm_id = matching_by_identity.get(identity)
            if matching_crm_id:
                crm_ids_by_evidence_id[item.evidence_id] = matching_crm_id
                continue
            try:
                created = self.client.create_research_evidence(_research_evidence_body(lead_id, item, snapshot_hash))
            except Exception:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.FAILED,
                    lead_id,
                    snapshot_hash,
                    evidence_ids,
                    tuple(crm_ids_by_evidence_id[evidence_id] for evidence_id in expected_ids if evidence_id in crm_ids_by_evidence_id),
                    reason_code="CREATE_FAILED",
                )
            crm_id = created.get("id") if isinstance(created, Mapping) else None
            if not isinstance(crm_id, str) or not crm_id:
                return EvidencePersistenceResult(
                    EvidencePersistenceStatus.FAILED,
                    lead_id,
                    snapshot_hash,
                    evidence_ids,
                    tuple(crm_ids_by_evidence_id[evidence_id] for evidence_id in expected_ids if evidence_id in crm_ids_by_evidence_id),
                    reason_code="INVALID_CREATE_RESPONSE",
                )
            crm_ids_by_evidence_id[item.evidence_id] = crm_id
            created_any = True

        return EvidencePersistenceResult(
            EvidencePersistenceStatus.CREATED if created_any else EvidencePersistenceStatus.SKIPPED,
            lead_id,
            snapshot_hash,
            evidence_ids,
            tuple(crm_ids_by_evidence_id[evidence_id] for evidence_id in expected_ids),
        )


_EVIDENCE_IDENTITY_VERSION = "c10-research-evidence-identity-v1"


def evidence_identity_key(
    lead_id: str,
    source_url: str,
    claim_type: str,
    claim: str,
) -> str:
    """Return the stable identity for one fact within one Lead.

    The batch snapshot hash is intentionally excluded: it describes a complete
    extraction run and changes when unrelated evidence is added or removed.
    Per-evidence identity instead scopes a normalized source and factual claim
    to a Lead, so retries and later snapshots cannot duplicate the same fact.
    """
    payload = {
        "version": _EVIDENCE_IDENTITY_VERSION,
        "lead_id": lead_id.strip(),
        "source_url": _canonical_source_url(source_url),
        "claim_type": _normalize_text(claim_type).lower(),
        "claim_hash": sha256(_normalize_text(claim).encode("utf-8")).hexdigest(),
    }
    encoded = dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _existing_by_identity(
    lead_id: str,
    records: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    existing: dict[str, str] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        crm_id = record.get("id")
        source_url = record.get("peSourceUrl")
        claim_type = record.get("peClaimType")
        claim = record.get("peClaim")
        if not all(isinstance(value, str) and value for value in (crm_id, source_url, claim_type, claim)):
            continue
        identity = evidence_identity_key(lead_id, source_url, claim_type, claim)
        existing.setdefault(identity, crm_id)
    return existing


def _canonical_source_url(value: str) -> str:
    parsed = urlparse(value.strip())
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    default_port = (parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80)
    netloc = hostname if not port or default_port else f"{hostname}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunparse((parsed.scheme.lower(), netloc, path, "", query, ""))


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _research_evidence_body(lead_id: str, item: EvidenceItem, snapshot_hash: str) -> dict[str, Any]:
    """Map a validated item to the frozen C06 ResearchEvidence field set."""
    return {
        "name": _record_name(item),
        "leadId": lead_id,
        "peEvidenceId": item.evidence_id,
        "peClaim": item.claim,
        "peClaimType": item.claim_type,
        "peEvidenceType": item.evidence_type,
        "peSourceUrl": item.source_url,
        "peEvidenceText": item.evidence_text,
        "peContentSummary": item.claim,
        "peConfidence": float(item.confidence),
        "peCapturedAt": _espo_datetime(item.captured_at),
        "peSchemaVersion": item.extractor_version,
        "peSnapshotHash": snapshot_hash,
    }


def _snapshot_item(item: EvidenceItem) -> dict[str, Any]:
    return {
        "evidence_id": item.evidence_id,
        "claim_type": item.claim_type,
        "claim": item.claim,
        "source_url": item.source_url,
        "page_title": item.page_title,
        "evidence_text": item.evidence_text,
        "evidence_type": item.evidence_type,
        "confidence": float(item.confidence),
        "captured_at": item.captured_at.isoformat(),
        "extractor_version": item.extractor_version,
    }


def _validation_error(item: Any) -> str | None:
    if not isinstance(item, EvidenceItem):
        return "INVALID_EVIDENCE_ITEM"
    for field in ("evidence_id", "claim_type", "claim", "source_url", "evidence_text", "evidence_type", "extractor_version"):
        value = getattr(item, field)
        if not isinstance(value, str) or not value.strip():
            return f"INVALID_{field.upper()}"
    if len(item.evidence_id) > 255:
        return "EVIDENCE_ID_TOO_LONG"
    if len(item.claim) > 500:
        return "CLAIM_TOO_LONG"
    if len(item.claim_type) > 100 or len(item.evidence_type) > 100:
        return "TYPE_TOO_LONG"
    if len(item.extractor_version) > 64:
        return "SCHEMA_VERSION_TOO_LONG"
    if len(item.evidence_text) > 1000:
        return "EVIDENCE_TEXT_TOO_LONG"
    parsed = urlparse(item.source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "INVALID_SOURCE_URL"
    try:
        parsed.port
    except ValueError:
        return "INVALID_SOURCE_URL"
    if isinstance(item.confidence, bool) or not isinstance(item.confidence, (int, float)) or not 0 <= item.confidence <= 1:
        return "INVALID_CONFIDENCE"
    if not isinstance(item.captured_at, datetime):
        return "INVALID_CAPTURED_AT"
    return None


def _record_name(item: EvidenceItem) -> str:
    prefix = "Evidence "
    return f"{prefix}{item.evidence_id}"[:255]


def _espo_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")
