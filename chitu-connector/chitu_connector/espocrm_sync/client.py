"""Memory-only EspoCRM target used to verify adapter behavior offline."""

from __future__ import annotations

from chitu_connector.espocrm_sync.audit import SyncAuditLog
from chitu_connector.espocrm_sync.contract import SyncContractPayload, validate_sync_contract
from chitu_connector.espocrm_sync.gate import evaluate_sync_gate
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.models import AdapterResult, AuditStatus, MockSyncResult, MockSyncStatus, SyncSource


class MockEspoCRMClient:
    def __init__(self) -> None:
        self.mock_sync_history: list[dict[str, object]] = []
        self._lead_ids_by_idempotency_key: dict[str, str] = {}
        self._next_lead_number = 1

    def create_lead(self, payload: SyncContractPayload) -> MockSyncResult:
        data = payload.to_dict()
        key = str(data["sync"]["idempotency_key"])
        errors = validate_sync_contract(data)
        if errors:
            self.mock_sync_history.append({"status": MockSyncStatus.VALIDATION_ERROR.value, "idempotency_key": key, "reason_code": errors[0]})
            return MockSyncResult(MockSyncStatus.VALIDATION_ERROR, errors[0], None, key)
        if key in self._lead_ids_by_idempotency_key:
            lead_id = self._lead_ids_by_idempotency_key[key]
            self.mock_sync_history.append({"status": MockSyncStatus.DUPLICATE.value, "idempotency_key": key, "lead_id": lead_id})
            return MockSyncResult(MockSyncStatus.DUPLICATE, None, lead_id, key)
        lead_id = f"mock-lead-{self._next_lead_number}"
        self._next_lead_number += 1
        self._lead_ids_by_idempotency_key[key] = lead_id
        self.mock_sync_history.append({"status": MockSyncStatus.SUCCESS.value, "idempotency_key": key, "lead_id": lead_id})
        return MockSyncResult(MockSyncStatus.SUCCESS, None, lead_id, key)


class EspoCRMSyncAdapter:
    def __init__(self, mapper: EspoCRMSyncMapper | None = None, client: MockEspoCRMClient | None = None, audit_log: SyncAuditLog | None = None) -> None:
        self.mapper = mapper or EspoCRMSyncMapper()
        self.client = client or MockEspoCRMClient()
        self.audit_log = audit_log or SyncAuditLog()

    def sync(self, source: SyncSource) -> AdapterResult:
        payload = self.mapper.build(source)
        data = payload.to_dict()
        key = data["sync"]["idempotency_key"]
        body_hash = data["sync"]["payload_hash"]
        ready_entry = self.audit_log.record(key, AuditStatus.READY, body_hash)
        decision = evaluate_sync_gate(source, payload)
        if not decision.accepted:
            rejected = self.audit_log.record(key, AuditStatus.REJECTED, body_hash, decision.reason_code)
            return AdapterResult(AuditStatus.REJECTED, decision.reason_code, None, data, (ready_entry, rejected))
        result = self.client.create_lead(payload)
        if result.status == MockSyncStatus.SUCCESS:
            completed = self.audit_log.record(key, AuditStatus.SYNCED, body_hash)
            return AdapterResult(AuditStatus.SYNCED, None, result.lead_id, data, (ready_entry, completed))
        if result.status == MockSyncStatus.DUPLICATE:
            duplicate = self.audit_log.record(key, AuditStatus.DUPLICATE, body_hash)
            return AdapterResult(AuditStatus.DUPLICATE, None, result.lead_id, data, (ready_entry, duplicate))
        rejected = self.audit_log.record(key, AuditStatus.REJECTED, body_hash, result.reason_code)
        return AdapterResult(AuditStatus.REJECTED, result.reason_code, None, data, (ready_entry, rejected))
