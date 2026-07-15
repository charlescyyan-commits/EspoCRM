"""Fixture-driven offline regression coverage for lifecycle, evidence, and ACL."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
CONNECTOR_ROOT = ROOT / "chitu-connector"
if str(CONNECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(CONNECTOR_ROOT))

from chitu_connector.espocrm_sync.research_evidence_persistence import (  # noqa: E402
    EvidencePersistenceStatus,
    ResearchEvidencePersistenceAdapter,
)
from chitu_connector.vendored.contracts.website_research import EvidenceItem  # noqa: E402


PROJECTION_SERVICE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Services" / "EmailLifecycleProjectionService.php"
ACL_PROVISIONING = ROOT / "deployment" / "provisioning" / "phase3c11_2_provision_persistence_acl.php"
PERSISTENCE_ENTITY_DEFS = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting" / "Resources" / "metadata" / "entityDefs"

STATUS_MAPS = {
    "DraftApproval": {"PENDING": "DRAFT_PENDING_APPROVAL", "APPROVED": "APPROVED", "REJECTED": "REJECTED"},
    "SendExecution": {"CREATED": "PENDING", "READY": "READY_TO_SEND", "SENT": "SENT", "FAILED": "FAILED", "CANCELLED": "CANCELLED"},
}


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def evidence_item(payload: dict) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=payload["evidence_id"],
        claim_type=payload["claim_type"],
        claim=payload["claim"],
        source_url=payload["source_url"],
        page_title=payload["page_title"],
        evidence_text=payload["evidence_text"],
        evidence_type=payload["evidence_type"],
        confidence=payload["confidence"],
        captured_at=datetime.fromisoformat(payload["captured_at"]),
        extractor_version=payload["extractor_version"],
    )


class FixtureEvidenceClient:
    """In-memory CRM-shaped test double; it never performs I/O."""

    def __init__(self) -> None:
        self.records: list[dict] = []
        self.create_count = 0

    def find_research_evidence_for_snapshot(self, lead_id: str, snapshot_hash: str) -> list[dict]:
        return [record for record in self.records if record["leadId"] == lead_id and record["peSnapshotHash"] == snapshot_hash]

    def find_research_evidence_by_identity(self, lead_id: str, source_url: str, claim_type: str, claim: str) -> list[dict]:
        return [record for record in self.records if record["leadId"] == lead_id and record["peSourceUrl"] == source_url and record["peClaimType"] == claim_type and record["peClaim"] == claim]

    def create_research_evidence(self, body: dict) -> dict:
        self.create_count += 1
        record = dict(body)
        record["id"] = f"fixture-crm-{self.create_count:03d}"
        self.records.append(record)
        return record


class FixtureProjection:
    """Minimal deterministic oracle for the approved Lead projection fields."""

    def __init__(self, initial: dict) -> None:
        self.lead = deepcopy(initial)

    def apply(self, source_entity: str, source_status: str, occurred_at: str) -> None:
        if source_entity == "ReplyEvent":
            self.lead["peEmailReplyStatus"] = source_status
            self.lead["peLastEmailDate"] = occurred_at
            return
        self.lead["peEmailStatus"] = STATUS_MAPS[source_entity][source_status]
        self.lead["peLastEmailDate"] = occurred_at


class ProspectingRegressionFixtureTests(unittest.TestCase):
    def test_email_lifecycle_fixture_projects_the_approved_crm_fields(self) -> None:
        source = PROJECTION_SERVICE.read_text(encoding="utf-8")
        cases = load_fixture("email_lifecycle_cases.json")["cases"]
        self.assertEqual([case["name"] for case in cases], ["draft", "approved", "queued", "sent", "failed", "replied"])

        for case in cases:
            with self.subTest(case=case["name"]):
                projection = FixtureProjection(case["initial"])
                projection.apply(case["source_entity"], case["source_status"], case["occurred_at"])
                self.assertEqual(projection.lead, case["expected"])
                if case["source_entity"] == "ReplyEvent":
                    self.assertIn("'REPLIED' => 'REPLIED'", source)
                else:
                    expected = case["expected"]["peEmailStatus"]
                    self.assertIn(f"'{case['source_status']}' => '{expected}'", source)

    def test_research_evidence_fixture_covers_new_duplicate_and_invalid_cases(self) -> None:
        fixture = load_fixture("research_evidence_cases.json")
        lead_id = fixture["lead_id"]
        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                client = FixtureEvidenceClient()
                adapter = ResearchEvidencePersistenceAdapter(client)
                item = evidence_item(case["evidence"])
                runs = 2 if case["mode"] == "repeat" else 1
                results = [adapter.persist(lead_id, [item]) for _ in range(runs)]
                self.assertEqual([result.status.value for result in results], case["expected_statuses"])
                self.assertEqual(client.create_count, case["expected_create_count"])
                if "expected_reason_code" in case:
                    self.assertEqual(results[-1].reason_code, case["expected_reason_code"])

    def test_acl_fixture_matches_all_persistence_roles_and_scopes(self) -> None:
        fixture = load_fixture("persistence_acl_roles.json")
        provisioning = ACL_PROVISIONING.read_text(encoding="utf-8")
        for role_name, permissions in fixture["roles"].items():
            with self.subTest(role=role_name):
                expected = ", ".join(f"'{key}' => '{value}'" for key, value in permissions.items())
                self.assertIn(f"'{role_name}' => [{expected}]", provisioning)
        for scope_name in fixture["scopes"]:
            with self.subTest(scope=scope_name):
                definition = json.loads((PERSISTENCE_ENTITY_DEFS / f"{scope_name}.json").read_text(encoding="utf-8"))
                self.assertTrue(definition["collection"]["orderBy"])

    def test_projection_fixture_does_not_extend_crm_fields_or_evidence_contract(self) -> None:
        source = PROJECTION_SERVICE.read_text(encoding="utf-8")
        self.assertIn("'peEmailStatus'", source)
        self.assertIn("'peLastEmailDate'", source)
        self.assertIn("'peEmailReplyStatus'", source)
        for forbidden in ("peOpportunityScoreV4", "peResearchStatus", "ResearchEvidence", "Opportunity", "curl_", "queue", "worker"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
