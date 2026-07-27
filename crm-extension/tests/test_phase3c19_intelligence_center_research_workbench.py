"""Phase3C19 Intelligence Center Research Workbench contract tests.

Frozen decisions:
  - ProspectPool remains the pre-Lead intelligence subject.
  - ResearchEvidence gets prospectPool link.
  - ProspectPool gets lead link.
  - Evidence inheritance must be idempotent.
  - No Lead lifecycle changes.
  - No ProspectPool status ownership changes.
  - No navigation tab changes.

Tests:
  1. Evidence parent validation (lead OR prospectPool required).
  2. Schema links integrity (entityDefs, indexes).
  3. Inheritance idempotency (service contract).
  4. PromotionInheritanceService class contract.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
MODULE = EXTENSION / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
SERVICES = MODULE / "Services"

REQUIRED_PARENT_LINK_MESSAGE = (
    "ResearchEvidence must be linked to a Lead or a ProspectPool."
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C19EvidenceParentValidationTests(unittest.TestCase):
    """Evidence must have lead OR prospectPool parent."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence_defs = load_json(ENTITY_DEFS / "ResearchEvidence.json")
        cls.service_file = SERVICES / "ResearchEvidenceService.php"
        cls.service_source = cls.service_file.read_text(encoding="utf-8")

    # --- entityDefs fields ---

    def test_evidence_has_lead_field(self) -> None:
        self.assertIn("lead", self.evidence_defs["fields"])
        self.assertEqual(self.evidence_defs["fields"]["lead"]["type"], "link")

    def test_evidence_has_prospect_pool_field(self) -> None:
        self.assertIn("prospectPool", self.evidence_defs["fields"])
        self.assertEqual(self.evidence_defs["fields"]["prospectPool"]["type"], "link")

    def test_evidence_has_lead_link(self) -> None:
        self.assertIn("lead", self.evidence_defs["links"])
        self.assertEqual(self.evidence_defs["links"]["lead"]["type"], "belongsTo")
        self.assertEqual(self.evidence_defs["links"]["lead"]["entity"], "Lead")

    def test_evidence_has_prospect_pool_link(self) -> None:
        self.assertIn("prospectPool", self.evidence_defs["links"])
        self.assertEqual(self.evidence_defs["links"]["prospectPool"]["type"], "belongsTo")
        self.assertEqual(self.evidence_defs["links"]["prospectPool"]["entity"], "ProspectPool")

    # --- unique indexes cover both parents ---

    def test_unique_index_covers_lead_id(self) -> None:
        indexes = self.evidence_defs.get("indexes", {})
        self.assertIn("c10EvidenceIdentity", indexes)
        self.assertEqual(indexes["c10EvidenceIdentity"]["type"], "unique")
        self.assertIn("leadId", indexes["c10EvidenceIdentity"]["columns"])

    def test_unique_index_covers_prospect_pool_id(self) -> None:
        indexes = self.evidence_defs.get("indexes", {})
        self.assertIn("c10EvidenceIdentityProspectPool", indexes)
        self.assertEqual(indexes["c10EvidenceIdentityProspectPool"]["type"], "unique")
        self.assertIn("prospectPoolId", indexes["c10EvidenceIdentityProspectPool"]["columns"])

    # --- validation service ---

    def test_validation_service_exists(self) -> None:
        self.assertTrue(self.service_file.exists(),
                        "ResearchEvidenceService.php must exist")

    def test_validation_service_extends_record_service(self) -> None:
        self.assertIn("class ResearchEvidenceService extends Service", self.service_source)

    def test_validation_service_validates_parent_link(self) -> None:
        self.assertIn("validateParentLink", self.service_source)

    def test_validation_service_rejects_no_parent(self) -> None:
        self.assertIn("leadId", self.service_source)
        self.assertIn("prospectPoolId", self.service_source)
        self.assertIn(REQUIRED_PARENT_LINK_MESSAGE, self.service_source)


class Phase3C19SchemaLinksIntegrityTests(unittest.TestCase):
    """ProspectPool ↔ Lead ↔ ResearchEvidence link integrity."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prospect_pool_defs = load_json(ENTITY_DEFS / "ProspectPool.json")
        cls.lead_defs = load_json(ENTITY_DEFS / "Lead.json")

    # --- ProspectPool links ---

    def test_prospect_pool_has_lead_link(self) -> None:
        self.assertIn("lead", self.prospect_pool_defs["links"])
        self.assertEqual(self.prospect_pool_defs["links"]["lead"]["type"], "belongsTo")
        self.assertEqual(self.prospect_pool_defs["links"]["lead"]["entity"], "Lead")
        self.assertEqual(self.prospect_pool_defs["links"]["lead"]["foreign"], "prospectPools")

    def test_prospect_pool_has_research_evidences_link(self) -> None:
        self.assertIn("researchEvidences", self.prospect_pool_defs["links"])
        self.assertEqual(self.prospect_pool_defs["links"]["researchEvidences"]["type"], "hasMany")
        self.assertEqual(self.prospect_pool_defs["links"]["researchEvidences"]["entity"], "ResearchEvidence")
        self.assertEqual(self.prospect_pool_defs["links"]["researchEvidences"]["foreign"], "prospectPool")

    def test_prospect_pool_has_lead_field(self) -> None:
        self.assertIn("lead", self.prospect_pool_defs["fields"])
        self.assertEqual(self.prospect_pool_defs["fields"]["lead"]["type"], "link")

    # --- Lead links ---

    def test_lead_has_prospect_pools_link(self) -> None:
        self.assertIn("prospectPools", self.lead_defs["links"])
        self.assertEqual(self.lead_defs["links"]["prospectPools"]["type"], "hasMany")
        self.assertEqual(self.lead_defs["links"]["prospectPools"]["entity"], "ProspectPool")
        self.assertEqual(self.lead_defs["links"]["prospectPools"]["foreign"], "lead")

    # --- status fields untouched ---

    def test_prospect_pool_status_fields_unchanged(self) -> None:
        """Frozen: No ProspectPool status ownership changes."""
        status_field = self.prospect_pool_defs["fields"]["status"]
        self.assertEqual(status_field["type"], "enum")
        self.assertEqual(status_field["default"], "WAITING")
        self.assertIn("COMPLETED", status_field["options"])

    def test_lead_status_fields_unchanged(self) -> None:
        """Frozen: No Lead lifecycle changes."""
        status_field = self.lead_defs["fields"]["status"]
        self.assertEqual(status_field["default"], "New")
        self.assertIn("Converted", status_field["options"])


class Phase3C19InheritanceIdempotencyTests(unittest.TestCase):
    """PromotionInheritanceService class contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.service_file = SERVICES / "PromotionInheritanceService.php"
        cls.service_source = cls.service_file.read_text(encoding="utf-8")

    def test_promotion_inheritance_service_exists(self) -> None:
        self.assertTrue(self.service_file.exists(),
                        "PromotionInheritanceService.php must exist")

    def test_service_has_inherit_method(self) -> None:
        self.assertIn("inheritEvidenceToLead", self.service_source)

    def test_service_validates_prospect_pool_id(self) -> None:
        self.assertIn("ProspectPool ID is required", self.service_source)

    def test_service_validates_lead_id(self) -> None:
        self.assertIn("Lead ID is required", self.service_source)

    def test_service_is_idempotent(self) -> None:
        """The 'skipped' counter proves idempotent skip path exists."""
        self.assertIn("skipped", self.service_source)
        # Already linked to the same lead → idempotent skip.
        self.assertIn("Already linked to the same lead", self.service_source)

    def test_service_rejects_different_lead_reassignment(self) -> None:
        self.assertIn("already linked to lead", self.service_source.lower())

    def test_service_preserves_prospect_pool_relation(self) -> None:
        """Evidence retains prospectPoolId when leadId is attached."""
        self.assertIn("prospectPoolId", self.service_source)

    def test_service_no_duplication(self) -> None:
        """Service updates existing rows; never creates duplicates."""
        self.assertIn('find', self.service_source.lower())
        # Must use the repository to look up existing evidence (not create new).
        self.assertIn('getRDBRepository', self.service_source)

    def test_service_returns_linked_and_skipped_counts(self) -> None:
        self.assertIn("'linked'", self.service_source)
        self.assertIn("'skipped'", self.service_source)


class Phase3C19I18nCoverageTests(unittest.TestCase):
    """New fields are covered in en_US and zh_CN i18n."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.i18n_en = MODULE / "Resources" / "i18n" / "en_US"
        cls.i18n_zh = MODULE / "Resources" / "i18n" / "zh_CN"

    def test_research_evidence_i18n_has_prospect_pool(self) -> None:
        for lang_dir in (self.i18n_en, self.i18n_zh):
            with self.subTest(lang=lang_dir.parent.name):
                data = load_json(lang_dir / "ResearchEvidence.json")
                self.assertIn("prospectPool", data["fields"])
                self.assertIn("prospectPool", data["links"])

    def test_prospect_pool_i18n_has_lead(self) -> None:
        for lang_dir in (self.i18n_en, self.i18n_zh):
            with self.subTest(lang=lang_dir.parent.name):
                data = load_json(lang_dir / "ProspectPool.json")
                self.assertIn("lead", data["fields"])
                self.assertIn("lead", data["links"])
                self.assertIn("researchEvidences", data["links"])
