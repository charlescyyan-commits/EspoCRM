"""Contract tests for the one-way C11 lifecycle-to-Lead projection boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Services" / "EmailLifecycleProjectionService.php"

DRAFT_MAP = {"PENDING": "DRAFT_PENDING_APPROVAL", "APPROVED": "APPROVED", "REJECTED": "REJECTED"}
SEND_MAP = {"CREATED": "PENDING", "READY": "READY_TO_SEND", "SENT": "SENT", "FAILED": "FAILED", "CANCELLED": "CANCELLED"}
REPLY_MAP = {"REPLIED": "REPLIED", "BOUNCED": "BOUNCED"}
RANK = {"NONE": 0, "DRAFT_READY": 10, "DRAFT_PENDING_APPROVAL": 20, "APPROVED": 30, "REJECTED": 30, "PENDING": 40, "READY_TO_SEND": 50, "SENT": 60, "FAILED": 60, "CANCELLED": 60, "REPLIED": 70, "BOUNCED": 70}


class InMemoryProjection:
    """Small deterministic oracle for the PHP projection contract."""

    def __init__(self) -> None:
        self.lead = {"peEmailStatus": "NONE", "peEmailReplyStatus": "", "peLastEmailDate": None}
        self.write_count = 0

    def status(self, value: str, occurred_at: str) -> bool:
        current_at = self.lead["peLastEmailDate"]
        if current_at and occurred_at < current_at:
            return False
        if current_at == occurred_at and RANK[value] < RANK[self.lead["peEmailStatus"]]:
            return False
        proposed = {"peEmailStatus": value, "peLastEmailDate": occurred_at}
        if all(self.lead[key] == item for key, item in proposed.items()):
            return False
        self.lead.update(proposed)
        self.write_count += 1
        return True

    def reply(self, value: str, occurred_at: str) -> bool:
        current_at = self.lead["peLastEmailDate"]
        if current_at and occurred_at < current_at:
            return False
        proposed = {"peEmailReplyStatus": value, "peLastEmailDate": occurred_at}
        if all(self.lead[key] == item for key, item in proposed.items()):
            return False
        self.lead.update(proposed)
        self.write_count += 1
        return True


class LifecycleProjectionTests(unittest.TestCase):
    def test_draft_approval_approved_projects_approved(self) -> None:
        projection = InMemoryProjection()
        projection.status(DRAFT_MAP["APPROVED"], "2026-07-14 10:00:00")
        self.assertEqual(projection.lead["peEmailStatus"], "APPROVED")

    def test_send_execution_sent_projects_sent(self) -> None:
        projection = InMemoryProjection()
        projection.status(SEND_MAP["SENT"], "2026-07-14 10:01:00")
        self.assertEqual(projection.lead["peEmailStatus"], "SENT")

    def test_reply_event_replied_projects_reply_status_only(self) -> None:
        projection = InMemoryProjection()
        projection.status(SEND_MAP["SENT"], "2026-07-14 10:01:00")
        projection.reply(REPLY_MAP["REPLIED"], "2026-07-14 10:02:00")
        self.assertEqual(projection.lead["peEmailStatus"], "SENT")
        self.assertEqual(projection.lead["peEmailReplyStatus"], "REPLIED")

    def test_duplicate_reply_event_is_idempotent(self) -> None:
        projection = InMemoryProjection()
        self.assertTrue(projection.reply(REPLY_MAP["REPLIED"], "2026-07-14 10:02:00"))
        baseline = deepcopy(projection.lead)
        self.assertFalse(projection.reply(REPLY_MAP["REPLIED"], "2026-07-14 10:02:00"))
        self.assertEqual(projection.lead, baseline)
        self.assertEqual(projection.write_count, 1)

    def test_old_event_cannot_roll_back_new_status(self) -> None:
        projection = InMemoryProjection()
        projection.status(SEND_MAP["SENT"], "2026-07-14 10:03:00")
        self.assertFalse(projection.status(SEND_MAP["READY"], "2026-07-14 10:02:00"))
        self.assertEqual(projection.lead["peEmailStatus"], "SENT")

    def test_unknown_reply_status_falls_back_to_none(self) -> None:
        projection = InMemoryProjection()
        projection.reply(REPLY_MAP.get("UNKNOWN", "NONE"), "2026-07-14 10:02:00")
        self.assertEqual(projection.lead["peEmailReplyStatus"], "NONE")

    def test_php_service_has_only_projection_maps_and_allowed_lead_fields(self) -> None:
        content = SERVICE.read_text(encoding="utf-8")
        for source, target in {**DRAFT_MAP, **SEND_MAP}.items():
            self.assertIn(f"'{source}' => '{target}'", content)
        self.assertIn("'REPLIED' => 'REPLIED'", content)
        self.assertIn("'BOUNCED' => 'BOUNCED'", content)
        self.assertIn("?? 'NONE'", content)
        self.assertIn("isOlderThanLead", content)
        self.assertIn("hasLowerRankAtSameTime", content)
        self.assertIn("changedUpdates", content)
        for allowed in ("peEmailStatus", "peLastEmailDate", "peEmailReplyStatus"):
            self.assertIn(allowed, content)
        for forbidden in ("peOpportunityScoreV4", "peResearchStatus", "ResearchEvidence", "Opportunity", "curl_", "queue", "worker", "SendProvider"):
            self.assertNotIn(forbidden, content)

    def test_hooks_project_sources_without_mutating_them(self) -> None:
        hook_paths = {
            "DraftApproval": "projectDraftApproval",
            "SendExecution": "projectSendExecution",
            "ReplyEvent": "projectReplyEvent",
        }
        for entity_name, method_name in hook_paths.items():
            with self.subTest(entity=entity_name):
                path = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Custom" / "Hooks" / entity_name / "EmailLifecycleProjectionHook.php"
                content = path.read_text(encoding="utf-8")
                self.assertIn(method_name, content)
                self.assertNotIn("saveEntity($entity)", content)


if __name__ == "__main__":
    unittest.main()
