"""Static contract tests for the ACL03 Sales Manager field policy."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deployment" / "provisioning" / "phase_acl03_apply_sales_manager_field_visibility.php"
LEAD_ENTITY_DEF = (
    ROOT
    / "crm-extension"
    / "files"
    / "custom"
    / "Espo"
    / "Modules"
    / "Prospecting"
    / "Resources"
    / "metadata"
    / "entityDefs"
    / "Lead.json"
)


class SalesManagerFieldVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = SCRIPT.read_text(encoding="utf-8")

    def test_only_sales_manager_role_is_targeted(self) -> None:
        self.assertIn("['name' => 'Sales Manager']", self.script)
        self.assertNotIn("'Sales User'", self.script)
        self.assertNotIn("'Integration Bot'", self.script)
        self.assertNotIn("'Admin'", self.script)

    def test_technical_fields_are_hidden(self) -> None:
        expected = {
            "peSyncStatus",
            "peSourceSystem",
            "peCandidateId",
            "peLastSyncAt",
            "peEngineVersion",
            "peScoreRulesVersion",
            "peSourceBatchId",
        }
        for field in expected:
            self.assertIn(f"'{field}'", self.script)
        self.assertIn("['read' => 'no', 'edit' => 'no']", self.script)

    def test_projection_fields_are_read_only(self) -> None:
        expected = {
            "peOpportunityScoreV4",
            "peScoreTier",
            "peResearchSummary",
            "peKeyEvidence",
            "peRecommendedApproach",
            "peEmailStatus",
            "peProposalAction",
            "peContactFormUrl",
            "peLinkedinUrl",
        }
        for field in expected:
            self.assertIn(f"'{field}'", self.script)
        self.assertIn("['read' => 'yes', 'edit' => 'no']", self.script)

    def test_only_crm_owned_pe_activity_fields_remain_editable(self) -> None:
        self.assertIn("$editableFields = ['peNextActionDate', 'peLastContactDate'];", self.script)
        self.assertIn('unset($leadFieldData[$field]);', self.script)

    def test_every_other_defined_pe_field_has_an_explicit_policy(self) -> None:
        import json

        fields = json.loads(LEAD_ENTITY_DEF.read_text(encoding="utf-8"))["fields"]
        editable = {"peNextActionDate", "peLastContactDate"}
        projected = {field for field in fields if field.startswith("pe")} - editable

        self.assertEqual(len(projected), 35)
        for field in projected:
            self.assertIn(f"'{field}'", self.script)

    def test_entity_acl_and_other_role_data_are_not_changed(self) -> None:
        self.assertNotIn("$role->set('data'", self.script)
        self.assertNotIn("getRelation(", self.script)
        self.assertNotIn("getEntity('User')", self.script)

    def test_runtime_role_payload_is_converted_from_espocrm_stdclass(self) -> None:
        self.assertIn("$fieldData = (array) ($role->get('fieldData') ?? []);", self.script)
        self.assertIn("$leadFieldData = (array) ($fieldData['Lead'] ?? []);", self.script)

    def test_provisioning_fails_loudly_if_persisted_rules_do_not_match(self) -> None:
        self.assertIn("$persistedRole = $entityManager->getRDBRepository('Role')", self.script)
        self.assertIn("ACL03 persistence validation failed", self.script)


if __name__ == "__main__":
    unittest.main()
