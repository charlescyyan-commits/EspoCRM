"""In-memory audit log for offline sync attempts."""

from __future__ import annotations

from uuid import uuid4

from chitu_connector.espocrm_sync.models import AuditEntry, AuditStatus, utc_now


class SyncAuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    def record(self, idempotency_key: str, status: AuditStatus, payload_hash: str, reason_code: str | None = None) -> AuditEntry:
        entry = AuditEntry(
            sync_id=str(uuid4()), idempotency_key=idempotency_key, status=status,
            timestamp=utc_now(), payload_hash=payload_hash, reason_code=reason_code,
        )
        self._entries.append(entry)
        return entry
