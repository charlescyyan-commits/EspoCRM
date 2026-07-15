"""Durable, connector-owned immutable delivery-payload snapshots.

This module is intentionally independent of CRM, Queue, Worker, Provider, and
Brevo runtime code.  It persists the minimum raw delivery content needed by a
future execution boundary in SQLite.  Production deployments must place the
database on a connector-owned encrypted persistent volume; this module does
not accept or manage encryption keys, API keys, authorization headers, or
other credentials.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Protocol


PAYLOAD_SNAPSHOT_SCHEMA_VERSION = "phase3c14.3.1b3-payload-snapshot-v1"
_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$")
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|authorization|x-api-key|x-sib-api-key)\s*[:=]"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~-]{8,}"),
    re.compile(r"\b(?:sk|xkeysib)-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)\b(?:password|secret|token)\s*[:=]\s*\S+"),
)


class PayloadSnapshotValidationError(ValueError):
    """Raised when a snapshot input cannot safely be persisted."""


class PayloadSnapshotConflictError(ValueError):
    """Raised when an existing execution would require mutable content."""


class PayloadSnapshotIntegrityError(ValueError):
    """Raised when durable data does not verify against its stored hashes."""


@dataclass(frozen=True, slots=True)
class PayloadSnapshotInput:
    """Content supplied by an authorized connector-only payload ingress.

    ``content_hash`` is the approved-content reference from the existing
    approval boundary.  ``snapshot_hash`` is independently calculated over
    the execution identity and actual delivery content, so durable storage can
    verify its own record without calling CRM.
    """

    execution_id: str
    content_hash: str
    recipient: str = field(repr=False)
    subject: str = field(repr=False)
    body: str = field(repr=False)
    campaign_reference: str
    payload_created_at: datetime

    def __post_init__(self) -> None:
        _require_text("execution_id", self.execution_id)
        _require_hash("content_hash", self.content_hash)
        _require_text("recipient", self.recipient)
        _require_text("subject", self.subject)
        _require_text("body", self.body)
        _require_text("campaign_reference", self.campaign_reference)
        _require_aware_timestamp("payload_created_at", self.payload_created_at)
        _reject_secret_patterns(
            self.recipient,
            self.subject,
            self.body,
            self.campaign_reference,
        )


@dataclass(frozen=True, slots=True)
class PayloadSnapshot:
    """An immutable, self-verifying persisted execution payload.

    Raw recipient, subject, and body are excluded from ``repr`` so ordinary
    diagnostics cannot expose them accidentally.
    """

    snapshot_id: str
    execution_id: str
    content_hash: str
    recipient_hash: str
    snapshot_hash: str
    payload_created_at: datetime
    schema_version: str
    recipient: str = field(repr=False)
    subject: str = field(repr=False)
    body: str = field(repr=False)
    campaign_reference: str = field(repr=False)

    def __post_init__(self) -> None:
        _require_text("snapshot_id", self.snapshot_id)
        _require_text("execution_id", self.execution_id)
        _require_hash("content_hash", self.content_hash)
        _require_hash("recipient_hash", self.recipient_hash)
        _require_hash("snapshot_hash", self.snapshot_hash)
        _require_text("schema_version", self.schema_version)
        _require_text("recipient", self.recipient)
        _require_text("subject", self.subject)
        _require_text("body", self.body)
        _require_text("campaign_reference", self.campaign_reference)
        _require_aware_timestamp("payload_created_at", self.payload_created_at)
        _reject_secret_patterns(
            self.recipient,
            self.subject,
            self.body,
            self.campaign_reference,
        )

        if self.recipient_hash != generate_recipient_hash(self.recipient):
            raise PayloadSnapshotIntegrityError("RECIPIENT_HASH_MISMATCH")
        expected_snapshot_hash = generate_snapshot_hash(
            execution_id=self.execution_id,
            content_hash=self.content_hash,
            recipient_hash=self.recipient_hash,
            subject=self.subject,
            body=self.body,
            campaign_reference=self.campaign_reference,
            schema_version=self.schema_version,
        )
        if self.snapshot_hash != expected_snapshot_hash:
            raise PayloadSnapshotIntegrityError("SNAPSHOT_HASH_MISMATCH")
        if self.snapshot_id != snapshot_id_for_hash(self.snapshot_hash):
            raise PayloadSnapshotIntegrityError("SNAPSHOT_ID_MISMATCH")

    @classmethod
    def create(cls, value: PayloadSnapshotInput) -> "PayloadSnapshot":
        """Create a deterministic snapshot without any persistence side effect."""

        if not isinstance(value, PayloadSnapshotInput):
            raise PayloadSnapshotValidationError("INVALID_PAYLOAD_SNAPSHOT_INPUT")
        recipient = _normalize_recipient(value.recipient)
        schema_version = PAYLOAD_SNAPSHOT_SCHEMA_VERSION
        recipient_hash = generate_recipient_hash(recipient)
        snapshot_hash = generate_snapshot_hash(
            execution_id=value.execution_id,
            content_hash=value.content_hash,
            recipient_hash=recipient_hash,
            subject=value.subject,
            body=value.body,
            campaign_reference=value.campaign_reference,
            schema_version=schema_version,
        )
        return cls(
            snapshot_id=snapshot_id_for_hash(snapshot_hash),
            execution_id=value.execution_id.strip(),
            content_hash=value.content_hash,
            recipient_hash=recipient_hash,
            snapshot_hash=snapshot_hash,
            payload_created_at=value.payload_created_at,
            schema_version=schema_version,
            recipient=recipient,
            subject=value.subject,
            body=value.body,
            campaign_reference=value.campaign_reference.strip(),
        )


class PayloadSnapshotStore(Protocol):
    """Connector persistence boundary for immutable execution payloads."""

    def save_if_absent(self, value: PayloadSnapshotInput) -> PayloadSnapshot: ...

    def get(self, execution_id: str) -> PayloadSnapshot | None: ...


class SqlitePayloadSnapshotStore:
    """SQLite-backed connector store with immutable execution rows.

    SQLite supplies transactional uniqueness for bridge and Worker processes
    sharing one connector-owned database.  The database file is intentionally
    outside CRM and must be deployed on encrypted persistent storage.
    """

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_if_absent(self, value: PayloadSnapshotInput) -> PayloadSnapshot:
        snapshot = PayloadSnapshot.create(value)
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO connector_payload_snapshots (
                        execution_id, snapshot_id, schema_version, content_hash,
                        recipient_hash, snapshot_hash, recipient, subject, body,
                        campaign_reference, payload_created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _snapshot_values(snapshot),
                )
            except sqlite3.IntegrityError as error:
                existing = _fetch_snapshot(connection, snapshot.execution_id)
                connection.rollback()
                if existing == snapshot:
                    return existing
                raise PayloadSnapshotConflictError("PAYLOAD_IMMUTABILITY_CONFLICT") from error
            connection.commit()
        return snapshot

    def get(self, execution_id: str) -> PayloadSnapshot | None:
        normalized_execution_id = _require_text("execution_id", execution_id)
        with closing(self._connect()) as connection:
            return _fetch_snapshot(connection, normalized_execution_id)

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS connector_payload_snapshots (
                    execution_id TEXT PRIMARY KEY NOT NULL,
                    snapshot_id TEXT UNIQUE NOT NULL,
                    schema_version TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    recipient_hash TEXT NOT NULL,
                    snapshot_hash TEXT UNIQUE NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    campaign_reference TEXT NOT NULL,
                    payload_created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._database_path), isolation_level=None)


def generate_recipient_hash(recipient: str) -> str:
    """Generate the B-1-compatible SHA-256 reference without retaining secrets."""

    return sha256(_normalize_recipient(recipient).encode("utf-8")).hexdigest()


def generate_snapshot_hash(
    *,
    execution_id: str,
    content_hash: str,
    recipient_hash: str,
    subject: str,
    body: str,
    campaign_reference: str,
    schema_version: str = PAYLOAD_SNAPSHOT_SCHEMA_VERSION,
) -> str:
    """Hash canonical immutable payload content; timestamps are deliberately excluded."""

    _require_text("execution_id", execution_id)
    _require_hash("content_hash", content_hash)
    _require_hash("recipient_hash", recipient_hash)
    _require_text("subject", subject)
    _require_text("body", body)
    _require_text("campaign_reference", campaign_reference)
    _require_text("schema_version", schema_version)
    _reject_secret_patterns(subject, body, campaign_reference)
    canonical_payload = {
        "body": body,
        "campaignReference": campaign_reference.strip(),
        "contentHash": content_hash,
        "executionId": execution_id.strip(),
        "recipientHash": recipient_hash,
        "schemaVersion": schema_version,
        "subject": subject,
    }
    serialized = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def snapshot_id_for_hash(snapshot_hash: str) -> str:
    """Return the deterministic opaque identifier for one immutable snapshot."""

    _require_hash("snapshot_hash", snapshot_hash)
    return "payload:" + snapshot_hash


def _fetch_snapshot(connection: sqlite3.Connection, execution_id: str) -> PayloadSnapshot | None:
    row = connection.execute(
        """
        SELECT snapshot_id, execution_id, content_hash, recipient_hash, snapshot_hash,
               payload_created_at, schema_version, recipient, subject, body,
               campaign_reference
          FROM connector_payload_snapshots
         WHERE execution_id = ?
        """,
        (execution_id,),
    ).fetchone()
    if row is None:
        return None
    return PayloadSnapshot(
        snapshot_id=row[0],
        execution_id=row[1],
        content_hash=row[2],
        recipient_hash=row[3],
        snapshot_hash=row[4],
        payload_created_at=datetime.fromisoformat(row[5]),
        schema_version=row[6],
        recipient=row[7],
        subject=row[8],
        body=row[9],
        campaign_reference=row[10],
    )


def _snapshot_values(snapshot: PayloadSnapshot) -> tuple[str, ...]:
    return (
        snapshot.execution_id,
        snapshot.snapshot_id,
        snapshot.schema_version,
        snapshot.content_hash,
        snapshot.recipient_hash,
        snapshot.snapshot_hash,
        snapshot.recipient,
        snapshot.subject,
        snapshot.body,
        snapshot.campaign_reference,
        snapshot.payload_created_at.isoformat(),
    )


def _normalize_recipient(value: str) -> str:
    return _require_text("recipient", value).casefold()


def _require_text(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PayloadSnapshotValidationError("MISSING_" + field_name.upper())
    return value.strip()


def _require_hash(field_name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
        raise PayloadSnapshotValidationError("INVALID_" + field_name.upper())


def _require_aware_timestamp(field_name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise PayloadSnapshotValidationError("INVALID_" + field_name.upper())


def _reject_secret_patterns(*values: str) -> None:
    for value in values:
        if any(pattern.search(value) for pattern in _SECRET_PATTERNS):
            raise PayloadSnapshotValidationError("PAYLOAD_CONTAINS_SECRET")
