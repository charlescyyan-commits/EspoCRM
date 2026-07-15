"""Static contract tests for Phase3C11.2 native CRM persistence entities."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
MODULE_ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
SURFACE_ENTITY_DEFS = EXT / "Resources" / "entityDefs"
ENTITY_NAMES = ("DraftApproval", "SendExecution", "ReplyEvent")

C10_FROZEN_HASHES = {
    "chitu-connector/chitu_connector/espocrm_sync/send_idempotency.py": "D305E1BBB3D100EB0F90940E598EADC0BF9E25DDDB5C0AB99B37F2F583661C75",
    "chitu-connector/chitu_connector/espocrm_sync/send_execution.py": "BDEDB145D7F759F78049C1C452707F47AD2565D9341079FAEE64DAFA77D34CE7",
    "chitu-connector/chitu_connector/espocrm_sync/send_provider.py": "B912ABC60391969E2BE290C97F7BF8C116D558B51BF086C333183CC5D9DE9AA7",
    "chitu-connector/chitu_connector/espocrm_sync/reply_tracking.py": "8BD2176BB39878384E5B55A07BFBC74D03C8422C9BAE4FF560688272BE0FC066",
    "chitu-connector/chitu_connector/espocrm_sync/human_approval.py": "FD9A6DA9EC68C726BE9D58FCAC3E55FF81C4FF343943E6CA29B68D83E193FE4C",
}

C10_TEST_HASHES = {
    "chitu-connector/tests/test_phase3c10_1_human_approval_model.py": "3C67DE2A15E6A4BBA2A35178F41B5F0AF16CD6D167A1D2EC0C183585EBA69871",
    "chitu-connector/tests/test_phase3c10_2_send_provider_adapter.py": "6249B884AE6072A3239382F25B81956EA079D2E800A365B1D79C9AE4C6F733A3",
    "chitu-connector/tests/test_phase3c10_3_controlled_send_execution.py": "DA940FBFCECC62DE0A584A9F8CB0DC42932845620D65E9661E007053FD581555",
    "chitu-connector/tests/test_phase3c10_4_reply_tracking_boundary.py": "D9943261F5366552B0EEE51DEE7A872D2E7A5319EBB9D65932493E7A3751C0C9",
    "chitu-connector/tests/test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py": "8A480E7151694D067923F727FF70594CA26D650824186595E068A7E9EE66AF43",
    "chitu-connector/tests/test_phase3c10_6_evidence_production_alignment.py": "11C70CC298E16FD59417DDF02494DC92502C7BD0D4FA91D099CABA70756FEEAD",
    "chitu-connector/tests/test_phase3c10_evidence_dedup_hardening.py": "8FB709C4E2F2F87FA8FE2E951E974241D0C409C73C96AB061968BC2D6F24B902",
    "chitu-connector/tests/test_phase3c10_send_idempotency_contract.py": "4B5AEABC8DE481F8FDA4F45FF87944F2FD1B4785BAFE224E9C72372B50272793",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PersistenceEntitiesTests(unittest.TestCase):
    def test_all_native_entity_surfaces_exist_and_match(self) -> None:
        for entity_name in ENTITY_NAMES:
            with self.subTest(entity=entity_name):
                surface = SURFACE_ENTITY_DEFS / f"{entity_name}.json"
                module = MODULE_ENTITY_DEFS / f"{entity_name}.json"
                self.assertTrue(surface.is_file())
                self.assertTrue(module.is_file())
                self.assertEqual(load_json(surface), load_json(module))
                self.assertTrue((MODULE / "Resources" / "metadata" / "scopes" / f"{entity_name}.json").is_file())
                self.assertTrue((MODULE / "Resources" / "metadata" / "clientDefs" / f"{entity_name}.json").is_file())
                self.assertTrue((MODULE / "Resources" / "metadata" / "aclDefs" / f"{entity_name}.json").is_file())
                self.assertTrue((MODULE / "Entities" / f"{entity_name}.php").is_file())
                for layout_name in ("detail", "list"):
                    self.assertEqual(
                        load_json(EXT / "Resources" / "layouts" / entity_name / f"{layout_name}.json"),
                        load_json(MODULE / "Resources" / "layouts" / entity_name / f"{layout_name}.json"),
                    )

    def test_draft_approval_contract(self) -> None:
        definition = load_json(MODULE_ENTITY_DEFS / "DraftApproval.json")
        fields = definition["fields"]
        self.assertEqual(fields["draftId"]["type"], "varchar")
        self.assertEqual(fields["status"]["options"], ["PENDING", "APPROVED", "REJECTED"])
        self.assertTrue(fields["lead"]["required"])
        self.assertEqual(fields["approvedBy"]["type"], "link")
        self.assertEqual(fields["approvedAt"]["type"], "datetime")
        self.assertEqual(fields["decisionReason"]["type"], "text")
        self.assertIn("evidenceReference", fields)
        self.assertIn("scoreSnapshot", fields)
        self.assertNotIn("body", fields)
        self.assertNotIn("prompt", fields)
        self.assertEqual(definition["indexes"]["draftId"]["type"], "unique")
        self.assertEqual(definition["links"]["lead"], {"type": "belongsTo", "entity": "Lead", "foreign": "draftApprovals"})

    def test_send_execution_contract_is_schema_only(self) -> None:
        definition = load_json(MODULE_ENTITY_DEFS / "SendExecution.json")
        fields = definition["fields"]
        self.assertEqual(fields["sendRequestId"]["type"], "varchar")
        self.assertEqual(fields["status"]["options"], ["CREATED", "READY", "SENT", "FAILED", "CANCELLED"])
        for field_name in ("draftApproval", "lead", "retryCount", "maxRetries", "nextRetryAt", "lastError"):
            self.assertIn(field_name, fields)
        self.assertEqual(fields["retryCount"]["default"], 0)
        self.assertEqual(fields["maxRetries"]["default"], 0)
        self.assertEqual(definition["indexes"]["sendRequestId"]["type"], "unique")
        self.assertEqual(definition["links"]["draftApproval"]["entity"], "DraftApproval")
        self.assertEqual(definition["links"]["lead"]["entity"], "Lead")

    def test_reply_event_contract_is_traceable_and_content_limited(self) -> None:
        definition = load_json(MODULE_ENTITY_DEFS / "ReplyEvent.json")
        fields = definition["fields"]
        self.assertEqual(fields["externalEventId"]["type"], "varchar")
        self.assertEqual(fields["replyStatus"]["options"], ["SENT", "REPLIED", "BOUNCED", "UNSUBSCRIBED"])
        self.assertTrue(fields["receivedAt"]["required"])
        self.assertTrue(fields["sendTraceReference"]["required"])
        self.assertTrue(fields["sendExecution"]["required"])
        self.assertTrue(fields["lead"]["required"])
        self.assertTrue({"body", "subject", "messageContent", "prompt"}.isdisjoint(fields))
        self.assertEqual(definition["indexes"]["externalEventId"]["type"], "unique")
        self.assertEqual(definition["links"]["sendExecution"]["entity"], "SendExecution")
        self.assertEqual(definition["links"]["lead"]["entity"], "Lead")

    def test_relationships_do_not_change_lead_projection_or_evidence_ownership(self) -> None:
        lead = load_json(MODULE_ENTITY_DEFS / "Lead.json")
        self.assertEqual(lead["fields"]["peEmailReplyStatus"]["type"], "varchar")
        self.assertEqual(
            lead["fields"]["peEmailStatus"]["options"],
            ["NONE", "DRAFT_READY", "DRAFT_PENDING_APPROVAL", "APPROVED", "REJECTED", "PENDING", "READY_TO_SEND", "SENT", "FAILED", "CANCELLED", "REPLIED", "BOUNCED"],
        )
        self.assertEqual(lead["links"]["draftApprovals"]["entity"], "DraftApproval")
        self.assertEqual(lead["links"]["sendExecutions"]["entity"], "SendExecution")
        self.assertEqual(lead["links"]["replyEvents"]["entity"], "ReplyEvent")
        for entity_name in ENTITY_NAMES:
            links = load_json(MODULE_ENTITY_DEFS / f"{entity_name}.json")["links"]
            self.assertNotIn("ResearchEvidence", {link.get("entity") for link in links.values()})
            self.assertNotIn("Opportunity", {link.get("entity") for link in links.values()})

    def test_acl_contract_keeps_sales_users_read_only(self) -> None:
        provisioning = (ROOT / "deployment" / "provisioning" / "phase3c11_2_provision_persistence_acl.php").read_text(encoding="utf-8")
        self.assertIn("$scopeList = ['DraftApproval', 'SendExecution', 'ReplyEvent'];", provisioning)
        self.assertIn("'Admin' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all']", provisioning)
        self.assertIn("'Integration Bot' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no']", provisioning)
        self.assertIn("'Sales User' => ['create' => 'no', 'read' => 'all', 'edit' => 'no', 'delete' => 'no']", provisioning)
        for entity_name in ENTITY_NAMES:
            scope = load_json(MODULE / "Resources" / "metadata" / "scopes" / f"{entity_name}.json")
            self.assertTrue(scope["acl"])
            self.assertTrue(scope["tab"])

    def test_c10_contract_and_tests_remain_frozen(self) -> None:
        for relative_path, expected_hash in {**C10_FROZEN_HASHES, **C10_TEST_HASHES}.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256(ROOT / relative_path), expected_hash)

    def test_no_provider_worker_or_opportunity_side_effect_implementation(self) -> None:
        provisioning = (ROOT / "deployment" / "provisioning" / "phase3c11_2_provision_persistence_acl.php").read_text(encoding="utf-8")
        for forbidden in ("curl_", "file_get_contents", "queue", "worker", "Opportunity", "EmailDraft", "EmailLifecycleSyncService"):
            self.assertNotIn(forbidden, provisioning)
        for entity_name in ENTITY_NAMES:
            entity_shell = (MODULE / "Entities" / f"{entity_name}.php").read_text(encoding="utf-8")
            self.assertIn(f"class {entity_name} extends Entity", entity_shell)
            self.assertNotIn("function ", entity_shell)


if __name__ == "__main__":
    unittest.main()
