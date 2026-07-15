"""C14.4A guards for the two legacy connector email-summary writers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from unittest import TestCase

from chitu_connector.espocrm_sync.campaign_projection import (
    CampaignProjectionAdapter,
    CampaignProjectionStatus,
)
from chitu_connector.espocrm_sync.email_draft_generation import (
    DraftEvidenceReference,
    EmailDraft,
    PersonalizationReference,
)
from chitu_connector.espocrm_sync.email_lifecycle import (
    EmailLifecycleStatus,
    EmailLifecycleSyncService,
    EmailLifecycleUpdate,
)
from chitu_connector.espocrm_sync.email_projection_guard import (
    C14_3_EMAIL_STATUS_RANK,
    guard_email_summary_update,
)
from chitu_connector.espocrm_sync.enrichment_gate import QualificationStatus


class GuardedLifecycleClient:
    def __init__(self, lead: Mapping[str, Any]) -> None:
        self.records = {"Lead": {"lead-1": dict(lead)}}
        self.update_calls: list[tuple[str, str, dict[str, Any]]] = []

    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]:
        return dict(self.records[entity_type][record_id])

    def update_record(self, entity_type: str, record_id: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.records[entity_type][record_id].update(body)
        self.update_calls.append((entity_type, record_id, dict(body)))
        return self.records[entity_type][record_id]


class GuardedCampaignClient:
    def __init__(self, lead: Mapping[str, Any]) -> None:
        self.lead = dict(lead)
        self.update_calls: list[tuple[str, dict[str, Any]]] = []

    def read_record(self, entity_type: str, record_id: str, select: str) -> Mapping[str, Any]:
        if entity_type != "Lead" or record_id != "lead-1":
            raise LookupError(record_id)
        return dict(self.lead)

    def update_lead_campaign_projection(self, lead_id: str, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        self.lead.update(fields)
        self.update_calls.append((lead_id, dict(fields)))
        return {"id": lead_id, **fields}


def lifecycle_update(status: EmailLifecycleStatus, *, occurred_at: datetime | None = None) -> EmailLifecycleUpdate:
    return EmailLifecycleUpdate(
        status=status,
        occurred_at=occurred_at or datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
        campaign_reference="C14.4A synthetic campaign",
        reply_state="NO_REPLY",
    )


def email_draft() -> EmailDraft:
    return EmailDraft(
        subject="Synthetic draft",
        body="Synthetic draft body",
        personalization_references=(PersonalizationReference("company.name", "Synthetic"),),
        evidence_references=(DraftEvidenceReference("evidence-1", "https://example.invalid/evidence"),),
        qualification_status=QualificationStatus.QUALIFIED,
        qualification_reason="fixture",
        score_tier="A",
        recommended_product="Resin Printer",
        generation_version="c14.4a-fixture-v1",
    )


class WriterConvergenceTests(TestCase):
    def test_w_con_01_sent_cannot_downgrade_to_approved(self) -> None:
        client = GuardedLifecycleClient({"peEmailStatus": "SENT", "peLastEmailDate": "2026-07-14 11:00:00"})

        with self.assertLogs("chitu_connector.espocrm_sync.email_lifecycle", level="WARNING") as logs:
            result = EmailLifecycleSyncService().sync(client, "lead-1", lifecycle_update(EmailLifecycleStatus.APPROVED))

        self.assertEqual(result.synced_fields, ())
        self.assertEqual(result.reason_code, "TERMINAL_EMAIL_STATUS_PROTECTED")
        self.assertEqual(client.records["Lead"]["lead-1"]["peEmailStatus"], "SENT")
        self.assertEqual(client.update_calls, [])
        self.assertIn("TERMINAL_EMAIL_STATUS_PROTECTED", "\n".join(logs.output))

    def test_w_con_01_replied_cannot_downgrade_to_sent(self) -> None:
        client = GuardedLifecycleClient({"peEmailStatus": "REPLIED", "peLastEmailDate": "2026-07-14 11:00:00"})

        result = EmailLifecycleSyncService().sync(client, "lead-1", lifecycle_update(EmailLifecycleStatus.SENT))

        self.assertEqual(result.reason_code, "TERMINAL_EMAIL_STATUS_PROTECTED")
        self.assertEqual(client.records["Lead"]["lead-1"]["peEmailStatus"], "REPLIED")
        self.assertEqual(client.update_calls, [])

    def test_w_con_01_empty_optional_fields_are_excluded_not_cleared(self) -> None:
        client = GuardedLifecycleClient({
            "peEmailStatus": "REPLIED",
            "peLastEmailDate": "2026-07-14 11:00:00",
            "peEmailCampaignName": "Existing campaign",
            "peEmailReplyStatus": "POSITIVE_REPLY",
        })

        class PartialLegacyUpdate:
            status = EmailLifecycleStatus.REPLIED

            @staticmethod
            def fields() -> dict[str, Any]:
                return {
                    "peEmailStatus": "REPLIED",
                    "peLastEmailDate": "2026-07-14 12:00:00",
                    "peEmailCampaignName": "",
                    "peEmailReplyStatus": None,
                }

        result = EmailLifecycleSyncService().sync(client, "lead-1", PartialLegacyUpdate())  # type: ignore[arg-type]

        self.assertEqual(result.synced_fields, ("peEmailStatus", "peLastEmailDate"))
        self.assertEqual(client.records["Lead"]["lead-1"]["peEmailCampaignName"], "Existing campaign")
        self.assertEqual(client.records["Lead"]["lead-1"]["peEmailReplyStatus"], "POSITIVE_REPLY")
        self.assertEqual(set(client.update_calls[0][2]), {"peEmailStatus", "peLastEmailDate"})

    def test_w_con_01_older_timestamp_is_skipped(self) -> None:
        client = GuardedLifecycleClient({"peEmailStatus": "APPROVED", "peLastEmailDate": "2026-07-14 13:00:00"})

        result = EmailLifecycleSyncService().sync(
            client,
            "lead-1",
            lifecycle_update(EmailLifecycleStatus.SENT, occurred_at=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)),
        )

        self.assertEqual(result.reason_code, "OLDER_EMAIL_TIMESTAMP")
        self.assertEqual(client.update_calls, [])

    def test_w_con_02_draft_ready_cannot_overwrite_sent(self) -> None:
        client = GuardedCampaignClient({"id": "lead-1", "peEmailStatus": "SENT", "peLastEmailDate": "2026-07-14 11:00:00"})

        with self.assertLogs("chitu_connector.espocrm_sync.campaign_projection", level="WARNING") as logs:
            result = CampaignProjectionAdapter(client).project("lead-1", email_draft())

        self.assertEqual(result.status, CampaignProjectionStatus.SKIPPED)
        self.assertEqual(result.reason_code, "TERMINAL_EMAIL_STATUS_PROTECTED")
        self.assertEqual(client.lead["peEmailStatus"], "SENT")
        self.assertEqual(client.update_calls, [])
        self.assertIn("TERMINAL_EMAIL_STATUS_PROTECTED", "\n".join(logs.output))

    def test_non_conflicting_legacy_sync_still_updates_allowlisted_fields(self) -> None:
        client = GuardedLifecycleClient({"peEmailStatus": "APPROVED", "peLastEmailDate": "2026-07-14 11:00:00"})

        result = EmailLifecycleSyncService().sync(client, "lead-1", lifecycle_update(EmailLifecycleStatus.SENT))

        self.assertEqual(result.reason_code, None)
        self.assertEqual(result.synced_fields, (
            "peEmailCampaignName",
            "peEmailReplyStatus",
            "peEmailStatus",
            "peLastEmailDate",
        ))
        self.assertEqual(client.records["Lead"]["lead-1"]["peEmailStatus"], "SENT")
        self.assertEqual(len(client.update_calls), 1)

    def test_guard_rank_contract_matches_c14_3_projection_service(self) -> None:
        root = Path(__file__).resolve().parents[2]
        php_source = (
            root
            / "crm-extension"
            / "files"
            / "custom"
            / "Espo"
            / "Modules"
            / "Prospecting"
            / "Services"
            / "EmailLifecycleProjectionService.php"
        ).read_text(encoding="utf-8")

        for status, rank in C14_3_EMAIL_STATUS_RANK.items():
            with self.subTest(status=status):
                self.assertIn(f"'{status}' => {rank}", php_source)

    def test_forbidden_direct_downgrades_are_rejected_by_shared_guard(self) -> None:
        for current_status in ("SENT", "REPLIED", "BOUNCED"):
            for proposed_status in ("NONE", "DRAFT_READY", "APPROVED"):
                with self.subTest(current=current_status, proposed=proposed_status):
                    decision = guard_email_summary_update(
                        {"peEmailStatus": current_status, "peLastEmailDate": "2026-07-14 11:00:00"},
                        proposed_status=proposed_status,
                        proposed_occurred_at="2026-07-14 12:00:00",
                    )
                    self.assertFalse(decision.allowed)


if __name__ == "__main__":
    import unittest

    unittest.main()
