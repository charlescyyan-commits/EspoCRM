from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.contract import SyncContractPayload
from chitu_connector.espocrm_sync.lifecycle import LifecycleAction, LifecycleConflictError, LifecycleSyncService
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.real_sync import build_synthetic_source


class InMemoryLifecycleClient:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, dict[str, Any]]] = {
            "Lead": {},
            "Account": {},
            "Contact": {},
            "Opportunity": {},
        }
        self.create_calls: list[tuple[str, dict[str, Any]]] = []
        self.update_calls: list[tuple[str, str, dict[str, Any]]] = []

    def search_records(self, entity_type: str, attribute: str, value: str, select: str, max_size: int = 2) -> tuple[Mapping[str, Any], ...]:
        records = [record for record in self.records[entity_type].values() if record.get(attribute) == value]
        return tuple(deepcopy(records[:max_size]))

    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]:
        return deepcopy(self.records[entity_type][record_id])

    def create_record(self, entity_type: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        record_id = f"{entity_type.lower()}-{len(self.records[entity_type]) + 1}"
        record = {"id": record_id, **body}
        self.records[entity_type][record_id] = record
        self.create_calls.append((entity_type, dict(body)))
        return deepcopy(record)

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.records[entity_type][record_id].update(body)
        self.update_calls.append((entity_type, record_id, dict(body)))
        return deepcopy(self.records[entity_type][record_id])


def _payload(product: str = "Resin Tank") -> SyncContractPayload:
    source = build_synthetic_source()
    source.score["best_first_product"] = product
    return EspoCRMSyncMapper().build(source)


class LifecycleSyncTests(TestCase):
    def test_creates_lead_by_external_id_and_waits_for_native_conversion(self) -> None:
        client = InMemoryLifecycleClient()
        result = LifecycleSyncService().sync(client, _payload())

        self.assertEqual(result.lead_action, LifecycleAction.CREATED)
        self.assertEqual(result.account_action, LifecycleAction.AWAITING_CRM_CONVERSION)
        self.assertEqual(len(client.records["Lead"]), 1)
        lead = client.records["Lead"][result.lead_id]
        self.assertEqual(lead["peCandidateId"], "synthetic_test_dealer_v1")
        self.assertNotIn("status", lead)
        self.assertNotIn("assignedUserId", lead)
        self.assertEqual(len(client.records["Account"]), 0)
        self.assertEqual(len(client.records["Contact"]), 0)
        self.assertEqual(len(client.records["Opportunity"]), 0)

    def test_updates_converted_records_without_sales_field_writes(self) -> None:
        client = InMemoryLifecycleClient()
        payload = _payload("Filament Dryer")
        lead_id = "lead-1"
        account_id = "account-1"
        contact_id = "contact-1"
        opportunity_id = "opportunity-1"
        client.records["Lead"][lead_id] = {
            "id": lead_id,
            "peCandidateId": "synthetic_test_dealer_v1",
            "createdAccountId": account_id,
            "createdContactId": contact_id,
            "createdOpportunityId": opportunity_id,
            "status": "Converted",
        }
        client.records["Account"][account_id] = {"id": account_id, "originalLeadId": lead_id}
        client.records["Contact"][contact_id] = {"id": contact_id, "originalLeadId": lead_id, "accountId": account_id}
        client.records["Opportunity"][opportunity_id] = {
            "id": opportunity_id,
            "originalLeadId": lead_id,
            "accountId": account_id,
            "contactId": contact_id,
            "stage": "Negotiation",
            "amount": 75000,
            "closeDate": "2026-10-31",
            "assignedUserId": "sales-owner",
        }

        result = LifecycleSyncService().sync(client, payload)

        self.assertEqual(result.lead_action, LifecycleAction.UPDATED)
        self.assertEqual(result.account_action, LifecycleAction.UPDATED)
        self.assertEqual(result.contact_action, LifecycleAction.LINKED)
        self.assertEqual(result.opportunity_action, LifecycleAction.UPDATED)
        self.assertEqual(client.records["Opportunity"][opportunity_id]["peProductInterest"], "Filament Dryer")
        self.assertEqual(client.records["Opportunity"][opportunity_id]["stage"], "Negotiation")
        self.assertEqual(client.records["Opportunity"][opportunity_id]["amount"], 75000)
        self.assertEqual(client.records["Opportunity"][opportunity_id]["closeDate"], "2026-10-31")
        self.assertEqual(client.records["Opportunity"][opportunity_id]["assignedUserId"], "sales-owner")
        for _, _, body in client.update_calls:
            self.assertFalse({"status", "stage", "amount", "closeDate", "assignedUserId"} & set(body))

    def test_duplicate_external_id_stops_before_mutation(self) -> None:
        client = InMemoryLifecycleClient()
        for record_id in ("lead-1", "lead-2"):
            client.records["Lead"][record_id] = {"id": record_id, "peCandidateId": "synthetic_test_dealer_v1"}

        with self.assertRaises(LifecycleConflictError):
            LifecycleSyncService().sync(client, _payload())
        self.assertEqual(client.create_calls, [])
        self.assertEqual(client.update_calls, [])

    def test_broken_conversion_link_stops_before_child_update(self) -> None:
        client = InMemoryLifecycleClient()
        client.records["Lead"]["lead-1"] = {
            "id": "lead-1",
            "peCandidateId": "synthetic_test_dealer_v1",
            "createdAccountId": "account-1",
            "createdContactId": "contact-1",
            "createdOpportunityId": "opportunity-1",
        }
        client.records["Account"]["account-1"] = {"id": "account-1", "originalLeadId": "other-lead"}
        client.records["Contact"]["contact-1"] = {"id": "contact-1", "originalLeadId": "lead-1", "accountId": "account-1"}
        client.records["Opportunity"]["opportunity-1"] = {
            "id": "opportunity-1",
            "originalLeadId": "lead-1",
            "accountId": "account-1",
            "contactId": "contact-1",
        }

        with self.assertRaises(LifecycleConflictError):
            LifecycleSyncService().sync(client, _payload())
        self.assertEqual([call[0] for call in client.update_calls], ["Lead"])
