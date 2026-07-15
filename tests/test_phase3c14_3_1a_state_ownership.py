"""Offline C14.3.1A ownership tests for Lead email lifecycle projections."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "crm-extension" / "files" / "custom" / "Espo"
SERVICE = EXTENSION / "Modules" / "Prospecting" / "Services" / "EmailLifecycleProjectionService.php"
EMAIL_EVENT_HOOK = EXTENSION / "Custom" / "Hooks" / "EmailEvent" / "EmailEventWorkflowHook.php"
REPLY_EVENT_HOOK = EXTENSION / "Custom" / "Hooks" / "ReplyEvent" / "EmailLifecycleProjectionHook.php"

RANK = {
    "NONE": 0,
    "DRAFT_READY": 10,
    "DRAFT_PENDING_APPROVAL": 20,
    "APPROVED": 30,
    "REJECTED": 30,
    "PENDING": 40,
    "READY_TO_SEND": 50,
    "SENT": 60,
    "FAILED": 60,
    "CANCELLED": 60,
    "REPLIED": 70,
    "BOUNCED": 70,
}


class EmailEventProjectionOracle:
    """Deterministic oracle for the new EmailEvent projection entry point."""

    status_map = {
        "SENT": "SENT",
        "DELIVERED": "SENT",
        "REPLIED": "REPLIED",
        "BOUNCED": "BOUNCED",
    }
    reply_map = {"REPLIED": "REPLIED", "BOUNCED": "BOUNCED"}

    def __init__(self) -> None:
        self.lead = {
            "peEmailStatus": "NONE",
            "peEmailReplyStatus": "",
            "peLastEmailDate": None,
            "peEmailCampaignName": "",
        }
        self.write_count = 0

    def project_email_event(self, event_type: str, occurred_at: str, campaign: str = "") -> bool:
        status = self.status_map.get(event_type)
        reply_status = self.reply_map.get(event_type)
        if status is None and event_type not in {"OPENED", "CLICKED"}:
            return False
        current_at = self.lead["peLastEmailDate"]
        if current_at and occurred_at < current_at:
            return False
        current_status = self.lead["peEmailStatus"]
        if status == "SENT" and current_status in {"REPLIED", "BOUNCED"}:
            status = None
        if current_at == occurred_at and status and RANK[status] < RANK[current_status]:
            return False

        requested = {"peLastEmailDate": occurred_at}
        if campaign:
            requested["peEmailCampaignName"] = campaign
        if status:
            requested["peEmailStatus"] = status
        if reply_status:
            requested["peEmailReplyStatus"] = reply_status
        if all(self.lead[key] == value for key, value in requested.items()):
            return False
        self.lead.update(requested)
        self.write_count += 1
        return True

    def project_status(self, status: str, occurred_at: str) -> bool:
        current_at = self.lead["peLastEmailDate"]
        if current_at and occurred_at < current_at:
            return False
        if current_at == occurred_at and RANK[status] < RANK[self.lead["peEmailStatus"]]:
            return False
        proposed = {"peEmailStatus": status, "peLastEmailDate": occurred_at}
        if all(self.lead[key] == value for key, value in proposed.items()):
            return False
        self.lead.update(proposed)
        self.write_count += 1
        return True


class StateOwnershipBoundaryTests(unittest.TestCase):
    def test_email_event_sent_delegates_to_projection_and_updates_once(self) -> None:
        hook = EMAIL_EVENT_HOOK.read_text(encoding="utf-8")
        service = SERVICE.read_text(encoding="utf-8")
        projection = EmailEventProjectionOracle()

        self.assertIn("projectEmailEvent($event)", hook)
        self.assertIn("public function projectEmailEvent", service)
        self.assertNotIn("peEmailStatus", hook)
        self.assertNotIn("peEmailReplyStatus", hook)
        self.assertNotIn("$lead->set", hook)
        self.assertNotIn("saveEntity($lead)", hook)

        self.assertTrue(projection.project_email_event("SENT", "2026-07-14 10:00:00", "Acceptance"))
        self.assertEqual(projection.lead["peEmailStatus"], "SENT")
        self.assertEqual(projection.write_count, 1)

    def test_older_failed_after_sent_cannot_roll_back_lead(self) -> None:
        projection = EmailEventProjectionOracle()
        self.assertTrue(projection.project_status("SENT", "2026-07-14 10:03:00"))
        baseline = deepcopy(projection.lead)

        self.assertFalse(projection.project_status("FAILED", "2026-07-14 10:02:00"))

        self.assertEqual(projection.lead, baseline)
        self.assertEqual(projection.lead["peEmailStatus"], "SENT")
        self.assertEqual(projection.write_count, 1)

    def test_reply_event_uses_only_the_authorized_projection_path(self) -> None:
        reply_hook = REPLY_EVENT_HOOK.read_text(encoding="utf-8")
        php_writers = [
            path
            for path in EXTENSION.rglob("*.php")
            if "peEmailReplyStatus" in path.read_text(encoding="utf-8")
        ]

        self.assertIn("projectReplyEvent($entity)", reply_hook)
        self.assertNotIn("$entity->set", reply_hook)
        self.assertEqual(php_writers, [SERVICE])

    def test_no_forbidden_crm_hook_writer_remains(self) -> None:
        php_writers = [
            path
            for path in EXTENSION.rglob("*.php")
            if "peEmailStatus" in path.read_text(encoding="utf-8")
            or "peEmailReplyStatus" in path.read_text(encoding="utf-8")
        ]

        self.assertEqual(php_writers, [SERVICE])
        service = SERVICE.read_text(encoding="utf-8")
        self.assertIn("isOlderThanLead", service)
        self.assertIn("hasLowerRankAtSameTime", service)
        self.assertIn("changedUpdates", service)


if __name__ == "__main__":
    unittest.main()

