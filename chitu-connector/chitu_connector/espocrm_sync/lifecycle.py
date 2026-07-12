"""Schema-free Chitu intelligence synchronization across native CRM lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol

from chitu_connector.espocrm_sync.contract import SyncContractPayload
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper


class LifecycleSyncError(RuntimeError):
    pass


class LifecycleConflictError(LifecycleSyncError):
    pass


class LifecycleAction(StrEnum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    LINKED = "LINKED"
    AWAITING_CRM_CONVERSION = "AWAITING_CRM_CONVERSION"


@dataclass(frozen=True, slots=True)
class LifecycleSyncResult:
    lead_id: str
    lead_action: LifecycleAction
    account_id: str | None
    account_action: LifecycleAction
    contact_id: str | None
    contact_action: LifecycleAction
    opportunity_id: str | None
    opportunity_action: LifecycleAction


class LifecycleClient(Protocol):
    def search_records(self, entity_type: str, attribute: str, value: str, select: str, max_size: int = 2) -> tuple[Mapping[str, Any], ...]: ...

    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]: ...

    def create_record(self, entity_type: str, body: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]: ...


_LEAD_SELECT = "id,createdAccountId,createdContactId,createdOpportunityId"
_ACCOUNT_SELECT = "id,originalLeadId"
_CONTACT_SELECT = "id,originalLeadId,accountId"
_OPPORTUNITY_SELECT = "id,originalLeadId,accountId,contactId,stage,amount,closeDate,assignedUserId"
_FORBIDDEN_SALES_FIELDS = {
    "assignedUserId",
    "assignedUserName",
    "status",
    "stage",
    "amount",
    "amountCurrency",
    "closeDate",
    "probability",
    "teamsIds",
}


class LifecycleSyncService:
    """Upsert Chitu-owned intelligence without creating CRM-owned sales records."""

    def sync(self, client: LifecycleClient, payload: SyncContractPayload) -> LifecycleSyncResult:
        candidate_id = str(payload.to_dict()["identity"]["candidate_id"])
        lead_body = self._lead_body(payload)
        matches = client.search_records("Lead", "peCandidateId", candidate_id, _LEAD_SELECT)
        if len(matches) > 1:
            raise LifecycleConflictError(f"multiple Lead records share Chitu external ID {candidate_id}")

        if matches:
            lead_id = _record_id(matches[0], "Lead")
            client.update_record("Lead", lead_id, lead_body)
            lead_action = LifecycleAction.UPDATED
        else:
            created = client.create_record("Lead", lead_body)
            lead_id = _record_id(created, "Lead")
            lead_action = LifecycleAction.CREATED

        lead = client.read_record("Lead", lead_id, _LEAD_SELECT)
        account_id = _optional_id(lead, "createdAccountId")
        contact_id = _optional_id(lead, "createdContactId")
        opportunity_id = _optional_id(lead, "createdOpportunityId")
        if not account_id or not contact_id or not opportunity_id:
            return LifecycleSyncResult(
                lead_id,
                lead_action,
                account_id,
                LifecycleAction.AWAITING_CRM_CONVERSION,
                contact_id,
                LifecycleAction.AWAITING_CRM_CONVERSION,
                opportunity_id,
                LifecycleAction.AWAITING_CRM_CONVERSION,
            )

        account = client.read_record("Account", account_id, _ACCOUNT_SELECT)
        contact = client.read_record("Contact", contact_id, _CONTACT_SELECT)
        opportunity = client.read_record("Opportunity", opportunity_id, _OPPORTUNITY_SELECT)
        self._verify_native_conversion_links(lead_id, account, contact, opportunity, account_id, contact_id)

        account_body = self._account_body(payload)
        client.update_record("Account", account_id, account_body)

        opportunity_body = self._opportunity_body(payload)
        opportunity_action = LifecycleAction.LINKED
        if opportunity_body:
            client.update_record("Opportunity", opportunity_id, opportunity_body)
            opportunity_action = LifecycleAction.UPDATED

        return LifecycleSyncResult(
            lead_id,
            lead_action,
            account_id,
            LifecycleAction.UPDATED,
            contact_id,
            LifecycleAction.LINKED,
            opportunity_id,
            opportunity_action,
        )

    @staticmethod
    def _lead_body(payload: SyncContractPayload) -> dict[str, Any]:
        fields = EspoCRMSyncMapper.lead_fields(payload)
        body = {
            name: value
            for name, value in fields.items()
            if name in {
                "website",
                "peOpportunityScoreV4",
                "peScoreTier",
                "peConfidence",
                "peEvidenceCoverage",
                "peBestFirstProduct",
                "peQualificationStatus",
                "peEngineVersion",
                "peScoreRulesVersion",
                "peSyncStatus",
                "peResearchStatus",
                "peSourceSystem",
                "peCandidateId",
                "peLastSyncAt",
                "peResearchSummary",
                "peKeyEvidence",
                "peRecommendedApproach",
                "addressCountry",
            }
        }
        body["lastName"] = str(fields["name"])
        _assert_no_sales_fields(body)
        return body

    @staticmethod
    def _account_body(payload: SyncContractPayload) -> dict[str, Any]:
        company = payload.to_dict()["company"]
        body: dict[str, Any] = {"website": company["website"]}
        if company["country_code"] is not None:
            body["billingAddressCountry"] = company["country_code"]
        _assert_no_sales_fields(body)
        return body

    @staticmethod
    def _opportunity_body(payload: SyncContractPayload) -> dict[str, Any]:
        product = payload.to_dict()["recommendation"]["best_first_product"]
        if not product:
            return {}
        body = {"peProductInterest": product}
        _assert_no_sales_fields(body)
        return body

    @staticmethod
    def _verify_native_conversion_links(
        lead_id: str,
        account: Mapping[str, Any],
        contact: Mapping[str, Any],
        opportunity: Mapping[str, Any],
        account_id: str,
        contact_id: str,
    ) -> None:
        if account.get("originalLeadId") != lead_id:
            raise LifecycleConflictError("Account is not linked to the resolved Lead")
        if contact.get("originalLeadId") != lead_id or contact.get("accountId") != account_id:
            raise LifecycleConflictError("Contact is not linked to the resolved Lead and Account")
        if (
            opportunity.get("originalLeadId") != lead_id
            or opportunity.get("accountId") != account_id
            or opportunity.get("contactId") != contact_id
        ):
            raise LifecycleConflictError("Opportunity is not linked to the resolved Lead, Account, and Contact")


def _record_id(record: Mapping[str, Any], entity_type: str) -> str:
    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id:
        raise LifecycleSyncError(f"{entity_type} response did not contain an id")
    return record_id


def _optional_id(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    return value if isinstance(value, str) and value else None


def _assert_no_sales_fields(body: Mapping[str, Any]) -> None:
    overlap = _FORBIDDEN_SALES_FIELDS & set(body)
    if overlap:
        raise LifecycleSyncError(f"sync body contains CRM-owned sales fields: {sorted(overlap)}")
