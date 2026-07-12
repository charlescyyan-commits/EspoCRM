from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.email_lifecycle import (
    EmailLifecycleStatus,
    EmailLifecycleSyncError,
    EmailLifecycleSyncService,
    EmailLifecycleUpdate,
)


class InMemoryEmailLifecycleClient:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, dict[str, Any]]] = {
            "Lead": {"lead-1": {"id": "lead-1", "status": "Converted"}},
            "Opportunity": {"opportunity-1": {"id": "opportunity-1", "stage": "Proposal", "amount": 50000}},
        }
        self.update_calls: list[tuple[str, str, dict[str, Any]]] = []

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.records[entity_type][record_id].update(body)
        self.update_calls.append((entity_type, record_id, dict(body)))
        return self.records[entity_type][record_id]


def _update(status: EmailLifecycleStatus = EmailLifecycleStatus.REPLIED) -> EmailLifecycleUpdate:
    return EmailLifecycleUpdate(
        status=status,
        occurred_at=datetime(2026, 7, 11, 12, 15, tzinfo=timezone.utc),
        campaign_reference="Synthetic Reply Campaign",
        reply_state="POSITIVE_REPLY",
    )


class EmailLifecycleSyncTests(TestCase):
    def test_syncs_only_allowlisted_summary_fields_to_linked_records(self) -> None:
        client = InMemoryEmailLifecycleClient()

        result = EmailLifecycleSyncService().sync(client, "lead-1", _update(), "opportunity-1")

        expected = {
            "peEmailStatus": "REPLIED",
            "peLastEmailDate": "2026-07-11 12:15:00",
            "peEmailCampaignName": "Synthetic Reply Campaign",
            "peEmailReplyStatus": "POSITIVE_REPLY",
        }
        self.assertEqual(result.status, EmailLifecycleStatus.REPLIED)
        self.assertEqual(result.synced_fields, tuple(sorted(expected)))
        self.assertEqual(len(client.update_calls), 2)
        for entity_type, record_id, body in client.update_calls:
            self.assertIn(entity_type, {"Lead", "Opportunity"})
            self.assertIn(record_id, {"lead-1", "opportunity-1"})
            self.assertEqual(body, expected)
            self.assertFalse({"subject", "body", "to", "from", "html", "text"} & set(body))
        self.assertEqual(client.records["Lead"]["lead-1"]["status"], "Converted")
        self.assertEqual(client.records["Opportunity"]["opportunity-1"]["stage"], "Proposal")
        self.assertEqual(client.records["Opportunity"]["opportunity-1"]["amount"], 50000)

    def test_does_not_require_or_create_an_opportunity(self) -> None:
        client = InMemoryEmailLifecycleClient()

        result = EmailLifecycleSyncService().sync(client, "lead-1", _update(EmailLifecycleStatus.DRAFT_READY))

        self.assertIsNone(result.opportunity_id)
        self.assertEqual([call[0] for call in client.update_calls], ["Lead"])

    def test_rejects_content_like_or_timezone_free_input(self) -> None:
        with self.assertRaises(EmailLifecycleSyncError):
            EmailLifecycleUpdate(
                status=EmailLifecycleStatus.SENT,
                occurred_at=datetime(2026, 7, 11, 12, 0),
                campaign_reference="Synthetic Campaign",
                reply_state="NO_REPLY",
            ).fields()
        with self.assertRaises(EmailLifecycleSyncError):
            EmailLifecycleUpdate(
                status=EmailLifecycleStatus.SENT,
                occurred_at=datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc),
                campaign_reference="Synthetic Campaign",
                reply_state="x" * 65,
            ).fields()
