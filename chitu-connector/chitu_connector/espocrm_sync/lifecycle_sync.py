"""Synthetic localhost verification for schema-free EspoCRM lifecycle sync V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from chitu_connector.espocrm_sync.contract import SyncContractPayload
from chitu_connector.espocrm_sync.lifecycle import LifecycleAction, LifecycleSyncService
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.real_client import LocalEspoCRMClient, LocalEspoCRMError
from chitu_connector.espocrm_sync.real_sync import build_synthetic_source


SYNTHETIC_LIFECYCLE_MARKER = "[CHITU_PHASE3A29_TEST]"


@dataclass(frozen=True, slots=True)
class LifecycleRuntimeResult:
    lead_id: str
    account_id: str
    contact_id: str
    opportunity_id: str


def run_local_synthetic_lifecycle_sync() -> LifecycleRuntimeResult:
    client = LocalEspoCRMClient.from_environment()
    client.authenticate()
    client.preflight()
    _require_opportunity_metadata(client)

    run_id = uuid4().hex[:12]
    payload = _synthetic_payload(run_id)
    service = LifecycleSyncService()
    lead_id = account_id = contact_id = opportunity_id = None
    try:
        first = service.sync(client, payload)
        if first.lead_action != LifecycleAction.CREATED:
            raise RuntimeError("first lifecycle sync did not create a Lead")
        if first.account_action != LifecycleAction.AWAITING_CRM_CONVERSION:
            raise RuntimeError("new Lead was not held for native CRM conversion")
        lead_id = first.lead_id

        converted = client.convert_lead(lead_id, {
            "Account": {"name": f"{SYNTHETIC_LIFECYCLE_MARKER} Account {run_id}"},
            "Contact": {"lastName": f"{SYNTHETIC_LIFECYCLE_MARKER} Contact {run_id}"},
            "Opportunity": {
                "name": f"{SYNTHETIC_LIFECYCLE_MARKER} Opportunity {run_id}",
                "stage": "Proposal",
                "amount": 50000,
                "amountCurrency": "USD",
                "closeDate": "2026-09-30",
            },
        })
        account_id = _required_id(converted, "createdAccountId")
        contact_id = _required_id(converted, "createdContactId")
        opportunity_id = _required_id(converted, "createdOpportunityId")

        second = service.sync(client, payload)
        _assert_lifecycle_ids(second, lead_id, account_id, contact_id, opportunity_id)
        if second.opportunity_action != LifecycleAction.UPDATED:
            raise RuntimeError("converted Opportunity did not receive Chitu recommendation sync")

        updated_payload = _updated_synthetic_payload(payload)
        third = service.sync(client, updated_payload)
        _assert_lifecycle_ids(third, lead_id, account_id, contact_id, opportunity_id)

        duplicate_check = client.search_records(
            "Lead",
            "peCandidateId",
            str(updated_payload.to_dict()["identity"]["candidate_id"]),
            "id,peCandidateId",
        )
        if len(duplicate_check) != 1:
            raise RuntimeError("external-ID lookup found duplicate synthetic Leads")

        lead = client.read_record("Lead", lead_id, "peOpportunityScoreV4,status")
        account = client.read_record("Account", account_id, "website,billingAddressCountry,originalLeadId")
        contact = client.read_record("Contact", contact_id, "originalLeadId,accountId")
        opportunity = client.read_record(
            "Opportunity",
            opportunity_id,
            "originalLeadId,accountId,contactId,peProductInterest,stage,amount,closeDate",
        )
        if lead.get("peOpportunityScoreV4") != 85.0 or lead.get("status") != "Converted":
            raise RuntimeError("Lead intelligence update overwrote CRM status or did not persist score")
        if account.get("website") != "https://synthetic-dealer.example/v2" or account.get("billingAddressCountry") != "DE":
            raise RuntimeError("Account factual update did not persist")
        if contact.get("originalLeadId") != lead_id or contact.get("accountId") != account_id:
            raise RuntimeError("Contact conversion relationship verification failed")
        expected_opportunity = {
            "originalLeadId": lead_id,
            "accountId": account_id,
            "contactId": contact_id,
            "peProductInterest": "Filament Dryer",
            "stage": "Proposal",
            "amount": 50000,
            "closeDate": "2026-09-30",
        }
        for name, expected in expected_opportunity.items():
            if opportunity.get(name) != expected:
                raise RuntimeError(f"Opportunity verification failed: {name}")

        result = LifecycleRuntimeResult(lead_id, account_id, contact_id, opportunity_id)
        _rollback_lifecycle(client, result)
        _verify_rollback(client, result)
        return result
    finally:
        if any((lead_id, account_id, contact_id, opportunity_id)):
            _rollback_lifecycle(client, LifecycleRuntimeResult(
                lead_id or "",
                account_id or "",
                contact_id or "",
                opportunity_id or "",
            ), suppress_missing=True)


def _synthetic_payload(run_id: str) -> SyncContractPayload:
    payload = EspoCRMSyncMapper().build(build_synthetic_source())
    data = payload.to_dict()
    data["identity"]["candidate_id"] = f"phase3a29-{run_id}"
    data["company"]["name"] = f"{SYNTHETIC_LIFECYCLE_MARKER} Lead {run_id}"
    return _payload_from_data(data)


def _updated_synthetic_payload(payload: SyncContractPayload) -> SyncContractPayload:
    data = payload.to_dict()
    data["company"]["website"] = "https://synthetic-dealer.example/v2"
    data["score"]["value"] = 85.0
    data["score"]["result_hash"] = "d" * 64
    data["recommendation"]["best_first_product"] = "Filament Dryer"
    data["sync"]["requested_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    data["sync"]["payload_hash"] = "e" * 64
    return _payload_from_data(data)


def _payload_from_data(data: dict[str, Any]) -> SyncContractPayload:
    return SyncContractPayload(
        contract_version=data["contract_version"],
        identity=data["identity"],
        qualification=data["qualification"],
        company=data["company"],
        source=data["source"],
        research=data["research"],
        score=data["score"],
        recommendation=data["recommendation"],
        evidence=tuple(data["evidence"]),
        provenance=data["provenance"],
        sync=data["sync"],
    )


def _require_opportunity_metadata(client: LocalEspoCRMClient) -> None:
    fields = client._metadata("entityDefs.Opportunity.fields")
    if not isinstance(fields, dict) or "peProductInterest" not in fields:
        raise RuntimeError("Phase3A28 Opportunity metadata is unavailable")


def _assert_lifecycle_ids(
    result: Any,
    lead_id: str,
    account_id: str,
    contact_id: str,
    opportunity_id: str,
) -> None:
    if (result.lead_id, result.account_id, result.contact_id, result.opportunity_id) != (
        lead_id,
        account_id,
        contact_id,
        opportunity_id,
    ):
        raise RuntimeError("lifecycle sync changed a native CRM identity")


def _required_id(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"native Lead conversion did not return {field}")
    return value


def _rollback_lifecycle(
    client: LocalEspoCRMClient,
    result: LifecycleRuntimeResult,
    suppress_missing: bool = False,
) -> None:
    for entity_type, record_id in (
        ("Opportunity", result.opportunity_id),
        ("Contact", result.contact_id),
        ("Account", result.account_id),
        ("Lead", result.lead_id),
    ):
        if not record_id:
            continue
        try:
            client.delete_record(entity_type, record_id)
        except LocalEspoCRMError as error:
            if suppress_missing and "404" in str(error):
                continue
            raise


def _verify_rollback(client: LocalEspoCRMClient, result: LifecycleRuntimeResult) -> None:
    for entity_type, record_id in (
        ("Opportunity", result.opportunity_id),
        ("Contact", result.contact_id),
        ("Account", result.account_id),
        ("Lead", result.lead_id),
    ):
        try:
            client.read_record(entity_type, record_id, "id")
        except LocalEspoCRMError as error:
            if "404" in str(error):
                continue
            raise
        raise RuntimeError(f"synthetic {entity_type} remains after lifecycle rollback")
