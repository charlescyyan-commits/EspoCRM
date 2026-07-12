"""Synthetic localhost verification for display-only email lifecycle synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from chitu_connector.espocrm_sync.email_lifecycle import (
    EmailLifecycleStatus,
    EmailLifecycleSyncService,
    EmailLifecycleUpdate,
)
from chitu_connector.espocrm_sync.real_client import LocalEspoCRMClient, LocalEspoCRMError


SYNTHETIC_EMAIL_LIFECYCLE_MARKER = "[CHITU_PHASE3A31_TEST]"
_EMAIL_FIELDS = "peEmailStatus,peLastEmailDate,peEmailCampaignName,peEmailReplyStatus"


@dataclass(frozen=True, slots=True)
class EmailLifecycleRuntimeResult:
    lead_id: str
    account_id: str
    contact_id: str
    opportunity_id: str
    transitions: tuple[EmailLifecycleStatus, ...]


def run_local_synthetic_email_lifecycle_sync() -> EmailLifecycleRuntimeResult:
    client = LocalEspoCRMClient.from_environment()
    client.authenticate()
    client.preflight()
    _require_email_lifecycle_metadata(client)

    run_id = uuid4().hex[:12]
    lead_id = account_id = contact_id = opportunity_id = ""
    try:
        lead = client.create_record("Lead", {
            "lastName": f"{SYNTHETIC_EMAIL_LIFECYCLE_MARKER} Lead {run_id}",
            "description": SYNTHETIC_EMAIL_LIFECYCLE_MARKER,
        })
        lead_id = _required_id(lead, "id")
        converted = client.convert_lead(lead_id, {
            "Account": {"name": f"{SYNTHETIC_EMAIL_LIFECYCLE_MARKER} Account {run_id}"},
            "Contact": {"lastName": f"{SYNTHETIC_EMAIL_LIFECYCLE_MARKER} Contact {run_id}"},
            "Opportunity": {
                "name": f"{SYNTHETIC_EMAIL_LIFECYCLE_MARKER} Opportunity {run_id}",
                "stage": "Proposal",
                "amount": 50000,
                "amountCurrency": "USD",
                "closeDate": "2026-09-30",
            },
        })
        account_id = _required_id(converted, "createdAccountId")
        contact_id = _required_id(converted, "createdContactId")
        opportunity_id = _required_id(converted, "createdOpportunityId")
        lead_before = client.read_record("Lead", lead_id, "status")
        opportunity_before = client.read_record("Opportunity", opportunity_id, "stage,amount,closeDate")

        service = EmailLifecycleSyncService()
        transitions = (
            _update(EmailLifecycleStatus.DRAFT_READY, "2026-07-11T12:00:00+00:00", "NONE"),
            _update(EmailLifecycleStatus.APPROVED, "2026-07-11T12:05:00+00:00", "NONE"),
            _update(EmailLifecycleStatus.SENT, "2026-07-11T12:10:00+00:00", "NO_REPLY"),
            _update(EmailLifecycleStatus.REPLIED, "2026-07-11T12:15:00+00:00", "POSITIVE_REPLY"),
        )
        for update in transitions:
            service.sync(client, lead_id, update, opportunity_id)
            _assert_display_state(client, "Lead", lead_id, update)
            _assert_display_state(client, "Opportunity", opportunity_id, update)

        lead_after = client.read_record("Lead", lead_id, "status")
        opportunity_after = client.read_record("Opportunity", opportunity_id, "stage,amount,closeDate")
        if lead_after.get("status") != lead_before.get("status"):
            raise RuntimeError("email lifecycle sync changed native Lead status")
        for field in ("stage", "amount", "closeDate"):
            if opportunity_after.get(field) != opportunity_before.get(field):
                raise RuntimeError(f"email lifecycle sync changed native Opportunity sales field: {field}")

        result = EmailLifecycleRuntimeResult(
            lead_id=lead_id,
            account_id=account_id,
            contact_id=contact_id,
            opportunity_id=opportunity_id,
            transitions=tuple(update.status for update in transitions),
        )
        _rollback(client, result)
        _verify_rollback(client, result)
        return result
    finally:
        if any((lead_id, account_id, contact_id, opportunity_id)):
            _rollback(
                client,
                EmailLifecycleRuntimeResult(
                    lead_id=lead_id,
                    account_id=account_id,
                    contact_id=contact_id,
                    opportunity_id=opportunity_id,
                    transitions=(),
                ),
                suppress_missing=True,
            )


def _update(status: EmailLifecycleStatus, occurred_at: str, reply_state: str) -> EmailLifecycleUpdate:
    return EmailLifecycleUpdate(
        status=status,
        occurred_at=datetime.fromisoformat(occurred_at),
        campaign_reference="Phase3A31 Synthetic Campaign",
        reply_state=reply_state,
    )


def _require_email_lifecycle_metadata(client: LocalEspoCRMClient) -> None:
    expected = {"peEmailStatus", "peLastEmailDate", "peEmailCampaignName", "peEmailReplyStatus"}
    for entity_type in ("Lead", "Opportunity"):
        fields = client._metadata(f"entityDefs.{entity_type}.fields")
        if not isinstance(fields, Mapping) or not expected.issubset(fields):
            raise RuntimeError(f"Phase3A31 {entity_type} email lifecycle metadata is unavailable")


def _assert_display_state(
    client: LocalEspoCRMClient,
    entity_type: str,
    record_id: str,
    update: EmailLifecycleUpdate,
) -> None:
    record = client.read_record(entity_type, record_id, _EMAIL_FIELDS)
    expected = update.fields()
    for field, value in expected.items():
        if record.get(field) != value:
            raise RuntimeError(f"{entity_type} email lifecycle value did not persist: {field}")


def _required_id(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"native Lead conversion did not return {field}")
    return value


def _rollback(
    client: LocalEspoCRMClient,
    result: EmailLifecycleRuntimeResult,
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


def _verify_rollback(client: LocalEspoCRMClient, result: EmailLifecycleRuntimeResult) -> None:
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
        raise RuntimeError(f"synthetic {entity_type} remains after email lifecycle rollback")
