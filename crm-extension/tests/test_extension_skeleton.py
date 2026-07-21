"""Phase 3A-2.1 EspoCRM Extension Skeleton validation tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


EXT = Path(__file__).resolve().parents[1]
ROOT = EXT.parent
CONTRACT = ROOT / "docs" / "sync-contracts" / "ESPOCRM_SYNC_CONTRACT_V1.json"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
MODULE_ENTITY_DEFS = MODULE / "Resources" / "metadata" / "entityDefs"
MODULE_LAYOUTS = MODULE / "Resources" / "layouts"
SURFACE_ENTITY_DEFS = EXT / "Resources" / "entityDefs"
RELEASE_VERSION = "1.9.7-alpha"

REQUIRED_DIRS = [
    EXT / "Resources" / "metadata",
    EXT / "Resources" / "layouts",
    EXT / "Resources" / "entityDefs",
    EXT / "Resources" / "acl",
    EXT / "Resources" / "metadata" / "formula",
    EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting",
    EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Controllers",
    EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Services",
    EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Api",
    EXT / "application",
    EXT / "docs",
    EXT / "tests",
    MODULE / "Resources" / "metadata" / "entityDefs",
    MODULE / "Resources" / "metadata" / "scopes",
    MODULE / "Resources" / "metadata" / "clientDefs",
    MODULE / "Resources" / "metadata" / "aclDefs",
    MODULE / "Resources" / "metadata" / "formula",
    MODULE / "Resources" / "layouts" / "ResearchEvidence",
    MODULE / "Resources" / "i18n" / "en_US",
    MODULE / "Controllers",
    MODULE / "Services",
    MODULE / "Api",
]

RESEARCH_EVIDENCE_REQUIRED_FIELDS = {
    "peClaim",
    "peClaimType",
    "peEvidenceType",
    "peSourceUrl",
    "peEvidenceText",
    "peContentSummary",
    "peConfidence",
    "peCapturedAt",
    "peSchemaVersion",
}

LEAD_REQUIRED_FIELDS = {
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
    "peSourceType",
    "peDiscoverySource",
    "peSourceBatchId",
    "peCompanyType",
    "peIndustry",
    "peBusinessModel",
    "pePriorityLevel",
    "peLastResearchedAt",
    "peProposalProductFitScore",
    "peProposalCooperationType",
    "peProposalSuggestedNextAction",
    "peProposalEligibility",
    "peProposalAction",
    "peContactFormUrl",
    "peLinkedinUrl",
}

MVP_WORKFLOW_FIELD_TYPES = {
    "outreachStatus": "enum",
    "lastContactAt": "datetime",
    "nextFollowUpAt": "datetime",
    "leadSourceEngine": "varchar",
    "syncVersion": "varchar",
    "peSyncStatus": "enum",
    "peResearchStatus": "enum",
}

OUTREACH_STATUS_OPTIONS = [
    "DISCOVERED",
    "RESEARCH_COMPLETED",
    "QUALIFIED",
    "OUTREACH_READY",
    "CONTACTED",
    "REPLIED",
    "OPPORTUNITY",
    "WON",
    "LOST",
]

PHASE3B02_OUTREACH_STATUS_OPTIONS = [
    "NEW",
    "RESEARCHING",
    "RESEARCH_COMPLETED",
    "QUALIFIED",
    "CONTACT_READY",
    "CONTACTED",
    "RESPONDED",
    "CONVERTED",
    "CLOSED_LOST",
]

PHASE3B02_OUTREACH_STATUS_STYLES = {
    "NEW": "default",
    "RESEARCHING": "warning",
    "RESEARCH_COMPLETED": "info",
    "QUALIFIED": "primary",
    "CONTACT_READY": "success",
    "CONTACTED": "primary",
    "RESPONDED": "success",
    "CONVERTED": "success",
    "CLOSED_LOST": "danger",
}

OPPORTUNITY_PIPELINE_STAGES = [
    "DISCOVERY",
    "QUALIFICATION",
    "CONTACTED",
    "NEGOTIATION",
    "WON",
    "LOST",
]

OPPORTUNITY_PIPELINE_PROBABILITY = {
    "DISCOVERY": 10,
    "QUALIFICATION": 25,
    "CONTACTED": 40,
    "NEGOTIATION": 60,
    "WON": 100,
    "LOST": 0,
}

PE_SYNC_STATUS_OPTIONS = [
    "PENDING",
    "SYNCED",
    "FAILED",
]

PE_RESEARCH_STATUS_OPTIONS = [
    "NONE",
    "RESEARCHING",
    "COMPLETED",
    "FAILED",
]

SALES_STATUS_OPTIONS = [
    "New",
    "Reviewed",
    "Contacted",
    "Interested",
    "Qualified",
    "Converted",
    "Rejected",
]

LEAD_EMAIL_STATUS_OPTIONS = [
    "NONE",
    "DRAFT_READY",
    "DRAFT_PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "PENDING",
    "READY_TO_SEND",
    "SENT",
    "FAILED",
    "CANCELLED",
    "REPLIED",
    "BOUNCED",
]

OPPORTUNITY_EMAIL_STATUS_OPTIONS = [
    "NONE",
    "DRAFT_READY",
    "APPROVED",
    "SENT",
    "REPLIED",
    "BOUNCED",
]

OPPORTUNITY_INTELLIGENCE_FIELDS = {
    "peOpportunitySource",
    "peProductInterest",
    "peProductFitScore",
    "peCooperationType",
    "peNextAction",
    "peEstimatedValue",
    "peExpectedCloseDate",
}

EMAIL_LIFECYCLE_FIELDS = {
    "peEmailStatus",
    "peLastEmailDate",
    "peEmailCampaignName",
    "peEmailReplyStatus",
}

OPPORTUNITY_REQUIRED_FIELDS = OPPORTUNITY_INTELLIGENCE_FIELDS | EMAIL_LIFECYCLE_FIELDS

# Phase3B02: stage is now explicitly configured in entityDefs (native CRM field with Chitu pipeline)
OPPORTUNITY_REQUIRED_FIELDS_B02 = OPPORTUNITY_REQUIRED_FIELDS | {"stage"}

OPPORTUNITY_FIELD_TYPES = {
    "peOpportunitySource": "varchar",
    "peProductInterest": "varchar",
    "peProductFitScore": "float",
    "peCooperationType": "varchar",
    "peNextAction": "varchar",
    "peEstimatedValue": "currency",
    "peExpectedCloseDate": "date",
}

CONTRACT_EVIDENCE_TO_CRM = {
    "claim": "peClaim",
    "claim_type": "peClaimType",
    "evidence_type": "peEvidenceType",
    "source_url": "peSourceUrl",
    "evidence_text": "peEvidenceText",
    "confidence": "peConfidence",
    "captured_at": "peCapturedAt",
    "schema_version": "peSchemaVersion",
}

FORBIDDEN_EVIDENCE_FIELDS = {"score", "ranking", "aiResult", "email", "opportunityScore"}

PROTECTED_TREES = [
    ROOT / "app",
    ROOT / "revenue_system",
]


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class ExtensionSkeletonTests(unittest.TestCase):
    def test_manifest_json_valid(self) -> None:
        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["extensionName"], "Chitu Prospecting Integration")
        self.assertEqual(manifest["name"], "Chitu Prospecting Integration")
        self.assertEqual(manifest["version"], RELEASE_VERSION)
        self.assertIn("author", manifest)
        self.assertEqual(
            manifest["description"],
            "Chitu Prospecting CRM sync, native Prospecting Workspace, and deterministic Acquisition Strategy planning for EspoCRM",
        )
        self.assertIsInstance(manifest["acceptableVersions"], list)
        self.assertTrue(manifest["acceptableVersions"])

    def test_required_directory_structure(self) -> None:
        missing = [str(path.relative_to(ROOT)) for path in REQUIRED_DIRS if not path.is_dir()]
        self.assertEqual(missing, [], msg=f"Missing directories: {missing}")
        self.assertTrue((EXT / "README.md").is_file())
        self.assertTrue((EXT / "manifest.json").is_file())

    def test_research_evidence_entity_created(self) -> None:
        for path in (
            SURFACE_ENTITY_DEFS / "ResearchEvidence.json",
            MODULE_ENTITY_DEFS / "ResearchEvidence.json",
            MODULE / "Resources" / "metadata" / "scopes" / "ResearchEvidence.json",
            MODULE / "Resources" / "metadata" / "clientDefs" / "ResearchEvidence.json",
        ):
            self.assertTrue(path.is_file(), msg=f"Missing {path}")

    def test_research_evidence_required_fields(self) -> None:
        entity = _load_json(MODULE_ENTITY_DEFS / "ResearchEvidence.json")
        fields = set(entity["fields"])
        missing = sorted(RESEARCH_EVIDENCE_REQUIRED_FIELDS - fields)
        self.assertEqual(missing, [], msg=f"Missing ResearchEvidence fields: {missing}")
        forbidden = sorted(FORBIDDEN_EVIDENCE_FIELDS & fields)
        self.assertEqual(forbidden, [], msg=f"Forbidden evidence fields present: {forbidden}")

    def test_lead_extension_fields(self) -> None:
        entity = _load_json(MODULE_ENTITY_DEFS / "Lead.json")
        fields = entity["fields"]
        missing = sorted(LEAD_REQUIRED_FIELDS - set(fields))
        self.assertEqual(missing, [], msg=f"Missing Lead fields: {missing}")
        for name in LEAD_REQUIRED_FIELDS:
            field = fields[name]
            self.assertFalse(field.get("required", False), msg=f"{name} must be nullable/not required")
            self.assertFalse(field.get("notNull", False), msg=f"{name} must allow null")

    def test_phase3b01_lead_intelligence_model(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        self.assertEqual(fields["pePriorityLevel"]["options"], ["LOW", "NORMAL", "HIGH", "URGENT"])
        self.assertEqual(fields["pePriorityLevel"].get("default"), "NORMAL")
        self.assertEqual(fields["peLastResearchedAt"]["type"], "datetime")
        self.assertEqual(fields["peContactFormUrl"]["type"], "url")
        self.assertEqual(fields["peLinkedinUrl"]["type"], "url")
        self.assertEqual(
            fields.get("peSourceBatchId"),
            {"type": "varchar", "maxLength": 128, "required": False, "notNull": False, "trim": True, "tooltip": True},
        )
        self.assertIn("peSourceBatchId", _load_json(MODULE_ENTITY_DEFS / "Lead.json")["indexes"])

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        intelligence_fields = {
            cell["name"]
            for row in sections["Intelligence Summary"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertTrue({"name", "website", "addressCountry", "addressState"}.issubset(intelligence_fields))
        self.assertTrue({"peSourceType", "peDiscoverySource", "peCompanyType", "peIndustry", "peBusinessModel", "pePriorityLevel"}.issubset(intelligence_fields))

    def test_mvp_workflow_fields(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        for name, field_type in MVP_WORKFLOW_FIELD_TYPES.items():
            self.assertIn(name, fields, msg=f"Missing MVP workflow field: {name}")
            self.assertEqual(fields[name]["type"], field_type)
            self.assertFalse(fields[name].get("required", False))
            self.assertFalse(fields[name].get("notNull", False))
        # Phase3B01 legacy: the original set is still valid for backward compat
        self.assertEqual(fields["outreachStatus"]["options"], PHASE3B02_OUTREACH_STATUS_OPTIONS)
        self.assertEqual(fields["peSyncStatus"]["options"], PE_SYNC_STATUS_OPTIONS)
        self.assertEqual(fields["peSyncStatus"].get("default"), "PENDING")
        self.assertEqual(fields["peResearchStatus"]["options"], PE_RESEARCH_STATUS_OPTIONS)
        self.assertEqual(fields["peResearchStatus"].get("default"), "NONE")
        self.assertIn("D", fields["peScoreTier"]["options"])
        for name in (
            "peSourceSystem",
            "peCandidateId",
            "peLastSyncAt",
            "peResearchSummary",
            "peKeyEvidence",
            "peRecommendedApproach",
        ):
            self.assertIn(name, fields)

    def test_phase3a26_sales_activity_workflow_metadata(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        self.assertEqual(fields["status"]["options"], SALES_STATUS_OPTIONS)
        self.assertEqual(fields["status"].get("default"), "New")
        self.assertEqual(fields["peNextActionDate"]["type"], "date")
        self.assertEqual(fields["peLastContactDate"]["type"], "date")
        for name in ("peNextActionDate", "peLastContactDate"):
            self.assertFalse(fields[name].get("required", False))
            self.assertFalse(fields[name].get("notNull", False))

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Sales Activity", sections)
        sales_fields = {
            cell["name"]
            for row in sections["Sales Activity"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(
            sales_fields,
            {"status", "assignedUser", "peNextActionDate", "peLastContactDate"},
        )
        for label in ("Intelligence Summary", "AI Research Information", "Sync Information"):
            self.assertIn(label, sections)

    def test_phase3a34_lead_layout_activation_metadata(self) -> None:
        """Prospecting must own Lead detail/list so Crm core layouts are not used."""
        layouts_meta = _load_json(MODULE / "Resources" / "metadata" / "app" / "layouts.json")
        self.assertEqual(layouts_meta["Lead"]["detail"]["module"], "Prospecting")
        self.assertEqual(layouts_meta["Lead"]["list"]["module"], "Prospecting")

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"] for section in detail}
        for label in (
            "Intelligence Summary",
            "AI Research Information",
            "Email Status",
            "Sync Information",
            "Contact & Ownership",
        ):
            self.assertIn(label, sections)
        self.assertNotIn("Overview", sections)
        self.assertNotIn("Details", sections)

    def test_phase3a27_email_status_integration_metadata(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        self.assertEqual(fields["peEmailStatus"]["type"], "enum")
        self.assertEqual(fields["peEmailStatus"]["options"], LEAD_EMAIL_STATUS_OPTIONS)
        self.assertEqual(fields["peEmailStatus"].get("default"), "NONE")
        self.assertEqual(fields["peLastEmailDate"]["type"], "datetime")
        self.assertEqual(fields["peEmailCampaignName"]["type"], "varchar")
        self.assertEqual(fields["peEmailReplyStatus"]["type"], "varchar")
        for name in ("peEmailStatus", "peLastEmailDate", "peEmailCampaignName", "peEmailReplyStatus"):
            self.assertFalse(fields[name].get("required", False))
            self.assertFalse(fields[name].get("notNull", False))
        self.assertNotIn("peEmailSubject", fields)
        self.assertNotIn("peEmailBody", fields)

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Email Status", sections)
        email_fields = {
            cell["name"]
            for row in sections["Email Status"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(
            email_fields,
            {"peEmailStatus", "peLastEmailDate", "peEmailCampaignName", "peEmailReplyStatus"},
        )
        for label in ("Sales Activity", "Intelligence Summary", "AI Research Information", "Sync Information"):
            self.assertIn(label, sections)

    def test_phase3a28_opportunity_workflow_metadata(self) -> None:
        entity = _load_json(MODULE_ENTITY_DEFS / "Opportunity.json")
        fields = entity["fields"]
        self.assertEqual(set(fields), OPPORTUNITY_REQUIRED_FIELDS_B02)
        self.assertNotIn("links", entity, msg="Opportunity must retain native CRM relationships")
        for name, field_type in OPPORTUNITY_FIELD_TYPES.items():
            self.assertEqual(fields[name]["type"], field_type)
            self.assertFalse(fields[name].get("required", False))
            self.assertFalse(fields[name].get("notNull", False))

        self.assertEqual(fields["peEstimatedValue"].get("min"), 0)
        self.assertEqual(fields["peProductFitScore"].get("min"), 0)
        self.assertEqual(fields["peProductFitScore"].get("max"), 100)
        # Phase3B02: stage is now explicitly configured with Chitu pipeline stages.
        # Native CRM stage behavior (probability, closeDate, amount) is preserved.
        self.assertIn("stage", fields, msg="Phase3B02 must configure Opportunity stage")

        detail = _load_json(MODULE_LAYOUTS / "Opportunity" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Customer Intelligence", sections)
        customer_intelligence_fields = {
            cell["name"]
            for row in sections["Customer Intelligence"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(customer_intelligence_fields, OPPORTUNITY_INTELLIGENCE_FIELDS)
        self.assertIn("Overview", sections)

        labels = _load_json(MODULE / "Resources" / "i18n" / "en_US" / "Opportunity.json")
        self.assertEqual(set(labels["fields"]), OPPORTUNITY_REQUIRED_FIELDS)

    def test_phase3a31_opportunity_email_lifecycle_metadata(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Opportunity.json")["fields"]
        self.assertEqual(fields["peEmailStatus"]["type"], "enum")
        self.assertEqual(fields["peEmailStatus"]["options"], OPPORTUNITY_EMAIL_STATUS_OPTIONS)
        self.assertEqual(fields["peEmailStatus"].get("default"), "NONE")
        self.assertEqual(fields["peLastEmailDate"]["type"], "datetime")
        self.assertEqual(fields["peEmailCampaignName"]["type"], "varchar")
        self.assertEqual(fields["peEmailReplyStatus"]["type"], "varchar")
        for name in EMAIL_LIFECYCLE_FIELDS:
            self.assertFalse(fields[name].get("required", False))
            self.assertFalse(fields[name].get("notNull", False))
        self.assertNotIn("peEmailSubject", fields)
        self.assertNotIn("peEmailBody", fields)

        detail = _load_json(MODULE_LAYOUTS / "Opportunity" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Email Status", sections)
        email_fields = {
            cell["name"]
            for row in sections["Email Status"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(email_fields, EMAIL_LIFECYCLE_FIELDS)

    def test_surface_and_module_entity_defs_match(self) -> None:
        for name in ("ResearchEvidence.json", "Lead.json", "Opportunity.json"):
            surface = _load_json(SURFACE_ENTITY_DEFS / name)
            module = _load_json(MODULE_ENTITY_DEFS / name)
            self.assertEqual(surface, module, msg=f"Parity mismatch for {name}")

    def test_contract_field_consistency(self) -> None:
        contract = _load_json(CONTRACT)
        evidence_props = set(contract["properties"]["evidence"]["items"]["properties"])
        for contract_field, crm_field in CONTRACT_EVIDENCE_TO_CRM.items():
            self.assertIn(contract_field, evidence_props, msg=f"Contract missing {contract_field}")
            entity = _load_json(MODULE_ENTITY_DEFS / "ResearchEvidence.json")
            self.assertIn(crm_field, entity["fields"], msg=f"CRM missing mapping for {contract_field}")

        score = contract["properties"]["score"]["properties"]
        qualification = contract["properties"]["qualification"]["properties"]
        recommendation = contract["properties"]["recommendation"]["properties"]
        provenance = contract["properties"]["provenance"]["properties"]
        lead = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]

        self.assertIn("value", score)
        self.assertIn("peOpportunityScoreV4", lead)
        self.assertIn("score_tier", score)
        self.assertIn("peScoreTier", lead)
        self.assertIn("aggregate_confidence", score)
        self.assertIn("peConfidence", lead)
        self.assertIn("evidence_coverage", score)
        self.assertIn("peEvidenceCoverage", lead)
        self.assertIn("best_first_product", recommendation)
        self.assertIn("peBestFirstProduct", lead)
        self.assertIn("status", qualification)
        self.assertIn("peQualificationStatus", lead)
        self.assertIn("engine_version", provenance)
        self.assertIn("peEngineVersion", lead)
        self.assertIn("rules_version", score)
        self.assertIn("peScoreRulesVersion", lead)

        # C10.6 accepts the engine evidence-format classification as an
        # optional V1 pass-through without changing V1 required fields.
        self.assertIn("claim_type", evidence_props)
        self.assertIn("evidence_type", evidence_props)

    def test_only_standard_research_evidence_php_shells_exist(self) -> None:
        php_files = list(EXT.rglob("*.php"))
        # Module entity/controller shells + native Select primary filters + Phase3B02 workflow hook.
        expected = {
            MODULE / "Entities" / "ResearchEvidence.php",
            MODULE / "Controllers" / "ResearchEvidence.php",
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeTierA.php",
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeRecentlySynced.php",
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeRecentlyResearched.php",
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeContactReady.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "Lead" / "LeadWorkflowHook.php",
            MODULE / "Api" / "PostSyncLead.php",
            MODULE / "Api" / "PostSyncEvidence.php",
            MODULE / "Api" / "PostSyncOpportunityProposal.php",
            MODULE / "Services" / "ChituSyncService.php",
            MODULE / "Api" / "PostSyncFeedback.php",
            MODULE / "Services" / "FeedbackSyncService.php",
            MODULE / "Entities" / "SalesFeedback.php",
            MODULE / "Entities" / "LearningSignal.php",
            MODULE / "Controllers" / "SalesFeedback.php",
            MODULE / "Controllers" / "LearningSignal.php",
            MODULE / "Entities" / "EmailEvent.php",
            MODULE / "Controllers" / "EmailEvent.php",
            MODULE / "Entities" / "SearchJob.php",
            MODULE / "Controllers" / "SearchJob.php",
            MODULE / "Entities" / "ProspectPool.php",
            MODULE / "Controllers" / "ProspectPool.php",
            MODULE / "Entities" / "SearchStrategy.php",
            MODULE / "Entities" / "DraftApproval.php",
            MODULE / "Entities" / "SendExecution.php",
            MODULE / "Entities" / "ReplyEvent.php",
            MODULE / "Controllers" / "SearchStrategy.php",
            MODULE / "Api" / "PostGenerateSearchStrategyJobs.php",
            MODULE / "Api" / "PostQuoteWorkflowAction.php",
            MODULE / "Services" / "SearchStrategyService.php",
            MODULE / "Services" / "SearchStrategyTemplates.php",
            MODULE / "Api" / "PostSyncBrevoEmailEvent.php",
            MODULE / "Services" / "BrevoEmailEventSyncService.php",
            MODULE / "Services" / "EmailLifecycleProjectionService.php",
            MODULE / "Services" / "BridgeRejectionException.php",
            MODULE / "Services" / "BridgeNormalizedStatus.php",
            MODULE / "Services" / "BridgeErrorClass.php",
            MODULE / "Services" / "SendExecutionBridgeResult.php",
            MODULE / "Services" / "SendExecutionBridgeAdapterService.php",
            MODULE / "Services" / "SendExecutionResultAdapterService.php",
            MODULE / "Services" / "QuoteNumberingService.php",
            MODULE / "Services" / "QuoteNumberingServiceInterface.php",
            MODULE / "Services" / "QuoteTransitionService.php",
            MODULE / "Services" / "QuoteWorkflowActionService.php",
            MODULE / "Services" / "ApprovalService.php",
            MODULE / "Entities" / "Approval.php",
            MODULE / "Binding.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "Approval" / "AuditFieldProtectionHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "SalesFeedback" / "SalesFeedbackLearningSignalHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "EmailEvent" / "EmailEventWorkflowHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "EmailEvent" / "EmailEventSalesFeedbackHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "DraftApproval" / "EmailLifecycleProjectionHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "SendExecution" / "EmailLifecycleProjectionHook.php",
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "ReplyEvent" / "EmailLifecycleProjectionHook.php",
        }
        expected |= set((MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters").glob("*.php"))
        expected |= set((MODULE / "Classes" / "Select" / "SalesFeedback" / "PrimaryFilters").glob("*.php"))
        expected |= set((MODULE / "Classes" / "Select" / "SearchJob" / "PrimaryFilters").glob("*.php"))
        expected |= set((MODULE / "Classes" / "Select" / "ProspectPool" / "PrimaryFilters").glob("*.php"))
        # Phase3U02 presentation filters — exact inventory (no arbitrary future PHP)
        strategy_filters = {
            MODULE / "Classes" / "Select" / "SearchStrategy" / "PrimaryFilters" / "StrategiesDraft.php",
            MODULE / "Classes" / "Select" / "SearchStrategy" / "PrimaryFilters" / "StrategiesReady.php",
            MODULE / "Classes" / "Select" / "SearchStrategy" / "PrimaryFilters" / "StrategiesActive.php",
            MODULE / "Classes" / "Select" / "SearchStrategy" / "PrimaryFilters" / "StrategiesCompleted.php",
        }
        for path in strategy_filters:
            self.assertTrue(path.is_file(), msg=f"Missing U02 SearchStrategy filter: {path}")
        expected |= strategy_filters
        self.assertEqual(
            set((MODULE / "Classes" / "Select" / "SearchStrategy" / "PrimaryFilters").glob("*.php")),
            strategy_filters,
            msg="SearchStrategy PrimaryFilters must match the approved U02 inventory exactly",
        )
        self.assertEqual(set(php_files), expected, msg=f"Unexpected PHP files: {php_files}")

    def test_core_espocrm_untouched(self) -> None:
        # This repository does not vendor EspoCRM core. Guard against accidental core trees.
        for name in ("application/Espo/Resources", "application/Espo/Core", "vendor/espocrm"):
            self.assertFalse((ROOT / name).exists(), msg=f"Unexpected EspoCRM core path: {name}")

    def test_prospecting_engine_untouched_by_extension_tree(self) -> None:
        self.assertFalse((ROOT / "prospecting_engine").exists())
        # Extension must not nest inside unrelated application trees.
        for tree in PROTECTED_TREES:
            overlap = list(EXT.rglob("*"))
            for path in overlap:
                self.assertFalse(
                    str(path.resolve()).startswith(str(tree.resolve()) + "\\")
                    or str(path.resolve()).startswith(str(tree.resolve()) + "/"),
                    msg=f"Extension path overlaps protected tree: {path}",
                )

    def test_no_database_migration_artifacts(self) -> None:
        migration_globs = list(EXT.rglob("*migration*")) + list(EXT.rglob("*.sql"))
        self.assertEqual(migration_globs, [], msg=f"Unexpected migration artifacts: {migration_globs}")

    def test_placeholder_readmes_present(self) -> None:
        for path in (
            EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Controllers" / "README.md",
            EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Services" / "README.md",
            EXT / "custom" / "Espo" / "Modules" / "Prospecting" / "Api" / "README.md",
            MODULE / "Controllers" / "README.md",
            MODULE / "Services" / "README.md",
            MODULE / "Api" / "README.md",
        ):
            self.assertTrue(path.is_file(), msg=f"Missing placeholder README: {path}")


    # ── Phase3B02 — Workflow & Pipeline Tests ──────────────────────────

    def test_phase3b02_outreach_status_pipeline(self) -> None:
        """Lead outreachStatus must define the Phase3B02 pipeline with display labels."""
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        status = fields["outreachStatus"]
        self.assertEqual(status["type"], "enum")
        self.assertEqual(status["options"], PHASE3B02_OUTREACH_STATUS_OPTIONS)
        self.assertEqual(status.get("default"), "NEW")
        self.assertTrue(status.get("displayAsLabel"), True)
        self.assertFalse(status.get("required", False))
        self.assertFalse(status.get("notNull", False))
        for option in PHASE3B02_OUTREACH_STATUS_OPTIONS:
            self.assertIn(option, status["style"],
                          msg=f"outreachStatus missing style for {option}")

    def test_phase3b02_lead_formula_metadata(self) -> None:
        """Lead entityDefs must include a before-save formula for automation Rules 1-3."""
        entity = _load_json(MODULE_ENTITY_DEFS / "Lead.json")
        self.assertIn("formula", entity, msg="Lead entityDefs missing formula key")
        formula: str = entity["formula"]
        self.assertIsInstance(formula, str)
        self.assertGreater(len(formula.strip()), 0, msg="Formula must not be empty")
        # Rule 1: Research Completed → outreachStatus transition
        self.assertIn("peResearchStatus", formula)
        self.assertIn("'COMPLETED'", formula)
        self.assertIn("outreachStatus = 'RESEARCH_COMPLETED'", formula)
        # Rule 2: High Opportunity Score → priority update
        self.assertIn("peOpportunityScoreV4", formula)
        self.assertIn(">= 80", formula)
        self.assertIn("pePriorityLevel = 'HIGH'", formula)
        # Rule 3: Contact Ready → pipeline state
        self.assertIn("emailAddress", formula)
        self.assertIn("phoneNumber", formula)
        self.assertIn("CONTACT_READY", formula)

    def test_phase3b02_lead_hook_exists(self) -> None:
        """LeadWorkflowHook.php must exist for after-save task auto-generation."""
        hook_path = EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "Lead" / "LeadWorkflowHook.php"
        self.assertTrue(hook_path.is_file(), msg=f"Hook file missing: {hook_path}")
        content = hook_path.read_text(encoding="utf-8")
        self.assertIn("class LeadWorkflowHook", content)
        self.assertIn("AfterSave", content)
        self.assertIn("peResearchStatus", content)
        self.assertIn("peOpportunityScoreV4", content)
        self.assertIn("Prepare Outreach", content)
        self.assertIn("Review and Contact Lead", content)

    def test_phase3b02_opportunity_pipeline_stages(self) -> None:
        """Opportunity stage must define Chitu pipeline with probability map."""
        fields = _load_json(MODULE_ENTITY_DEFS / "Opportunity.json")["fields"]
        self.assertIn("stage", fields, msg="Opportunity entityDefs missing stage field")
        stage = fields["stage"]
        self.assertEqual(stage["type"], "enum")
        self.assertEqual(stage["options"], OPPORTUNITY_PIPELINE_STAGES)
        self.assertEqual(stage.get("default"), "DISCOVERY")
        self.assertTrue(stage.get("displayAsLabel"), True)
        self.assertIn("probabilityMap", stage)
        prob_map = stage["probabilityMap"]
        for stage_name in OPPORTUNITY_PIPELINE_STAGES:
            self.assertIn(stage_name, prob_map,
                          msg=f"Stage {stage_name} missing probability")
        self.assertEqual(prob_map["WON"], 100)
        self.assertEqual(prob_map["LOST"], 0)
        for stage_name in OPPORTUNITY_PIPELINE_STAGES:
            self.assertIn(stage_name, stage["style"],
                          msg=f"Stage {stage_name} missing style")

    def test_phase3b02_pipeline_layout_section(self) -> None:
        """Lead detail layout must include the Pipeline section."""
        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Pipeline", sections, msg="Lead detail missing Pipeline section")
        pipeline_fields = {
            cell["name"]
            for row in sections["Pipeline"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(
            pipeline_fields,
            {"outreachStatus", "nextFollowUpAt", "lastContactAt"},
        )

    def test_phase3b02_opportunity_field_count(self) -> None:
        """Opportunity entityDefs must include native stage + Chitu intelligence + email fields."""
        fields = _load_json(MODULE_ENTITY_DEFS / "Opportunity.json")["fields"]
        self.assertEqual(set(fields), OPPORTUNITY_REQUIRED_FIELDS_B02)

    def test_phase3b02_surface_and_module_parity(self) -> None:
        """Surface and module copies must remain identical after Phase3B02 edits."""
        for name in ("ResearchEvidence.json", "Lead.json", "Opportunity.json"):
            surface = _load_json(SURFACE_ENTITY_DEFS / name)
            module = _load_json(MODULE_ENTITY_DEFS / name)
            self.assertEqual(surface, module, msg=f"Parity mismatch for {name}")

    def test_phase3b02_formula_metadata_file(self) -> None:
        """Formula metadata must be present at formula/Lead.json in both surface and module."""
        surface_formula = EXT / "Resources" / "metadata" / "formula" / "Lead.json"
        module_formula = MODULE / "Resources" / "metadata" / "formula" / "Lead.json"
        self.assertTrue(surface_formula.is_file(), msg="Surface formula/Lead.json missing")
        self.assertTrue(module_formula.is_file(), msg="Module formula/Lead.json missing")
        surface = _load_json(surface_formula)
        module = _load_json(module_formula)
        self.assertIn("beforeSaveCustomScript", surface)
        self.assertIn("beforeSaveCustomScript", module)
        self.assertEqual(surface, module, msg="Formula parity mismatch")
        script = surface["beforeSaveCustomScript"]
        self.assertIn("RESEARCH_COMPLETED", script)
        self.assertIn("pePriorityLevel = 'HIGH'", script)
        self.assertIn("CONTACT_READY", script)

    def test_phase3b03_connector_routes_and_proposal_model(self) -> None:
        routes = _load_json(MODULE / "Resources" / "routes.json")
        self.assertEqual(routes, _load_json(EXT / "Resources" / "routes.json"))
        self.assertEqual(
            {(route["method"], route["route"], route["actionClassName"]) for route in routes},
            {
                ("post", "/Prospecting/sync/lead", "Espo\\Modules\\Prospecting\\Api\\PostSyncLead"),
                ("post", "/Prospecting/sync/evidence", "Espo\\Modules\\Prospecting\\Api\\PostSyncEvidence"),
                ("post", "/Prospecting/sync/opportunity-proposal", "Espo\\Modules\\Prospecting\\Api\\PostSyncOpportunityProposal"),
                ("post", "/Prospecting/feedback/sync", "Espo\\Modules\\Prospecting\\Api\\PostSyncFeedback"),
                ("post", "/Prospecting/brevo/email-event", "Espo\\Modules\\Prospecting\\Api\\PostSyncBrevoEmailEvent"),
                ("post", "/Prospecting/search-strategy/generate-jobs", "Espo\\Modules\\Prospecting\\Api\\PostGenerateSearchStrategyJobs"),
                ("post", "/Prospecting/quote/:id/workflow/:action", "Espo\\Modules\\Prospecting\\Api\\PostQuoteWorkflowAction"),
            },
        )

        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        self.assertEqual(fields["peProposalProductFitScore"]["type"], "float")
        self.assertEqual(fields["peProposalEligibility"]["type"], "bool")
        self.assertEqual(fields["peProposalEligibility"].get("default"), False)
        self.assertEqual(fields["peProposalAction"].get("default"), "NO_AUTOMATIC_OPPORTUNITY")

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Opportunity Proposal", sections)
        proposal_fields = {
            cell["name"]
            for row in sections["Opportunity Proposal"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertEqual(
            proposal_fields,
            {
                "peBestFirstProduct",
                "peOpportunityScoreV4",
                "peProposalProductFitScore",
                "peProposalCooperationType",
                "peProposalEligibility",
                "peProposalAction",
                "peProposalSuggestedNextAction",
            },
        )

        service = (MODULE / "Services" / "ChituSyncService.php").read_text(encoding="utf-8")
        self.assertIn("NO_AUTOMATIC_OPPORTUNITY", service)
        self.assertIn("foreach ($payload['evidence'] as $item)", service)
        self.assertNotIn("getEntity('Opportunity')", service)

    def test_phase3b06_1_lead_projection_uses_only_v1_fields(self) -> None:
        service = (MODULE / "Services" / "ChituSyncService.php").read_text(encoding="utf-8")
        for field in ("peResearchSummary", "peKeyEvidence", "peRecommendedApproach"):
            self.assertIn(f"'{field}'", service)
        self.assertIn("private function researchSummary", service)
        self.assertIn("private function keyEvidence", service)
        self.assertIn("private function recommendedApproach", service)
        self.assertIn("foreach ($payload['evidence'] as $item)", service)
        self.assertIn("return $lines ?", service)
        self.assertNotIn("getEntity('Opportunity')", service)

    def test_phase3b04_feedback_loop_metadata(self) -> None:
        for name in ("SalesFeedback.json", "LearningSignal.json"):
            self.assertEqual(
                _load_json(SURFACE_ENTITY_DEFS / name),
                _load_json(MODULE_ENTITY_DEFS / name),
                msg=f"Parity mismatch for {name}",
            )

        feedback = _load_json(MODULE_ENTITY_DEFS / "SalesFeedback.json")
        signal = _load_json(MODULE_ENTITY_DEFS / "LearningSignal.json")
        lead = _load_json(MODULE_ENTITY_DEFS / "Lead.json")
        self.assertEqual(
            set(feedback["fields"]),
            {
                "name", "externalFeedbackId", "externalLeadId", "feedbackType", "outcome", "reason", "note",
                "currentStage", "product", "productResult", "campaign", "source", "feedbackAt", "createdAt", "lead", "learningSignal",
                "assignedUser", "teams",
            },
        )
        self.assertEqual(
            set(signal["fields"]),
            {"name", "signalType", "predictionScore", "actualOutcome", "product", "campaign", "createdAt", "lead", "salesFeedback", "assignedUser", "teams"},
        )
        self.assertEqual(feedback["links"]["lead"]["foreign"], "salesFeedbacks")
        self.assertEqual(signal["links"]["salesFeedback"]["foreign"], "learningSignal")
        self.assertIn("salesFeedbacks", lead["links"])
        self.assertIn("learningSignals", lead["links"])
        self.assertEqual(feedback["fields"]["feedbackType"]["options"], [
            "CONTACT_ATTEMPT", "CUSTOMER_REPLY", "INTERESTED", "NOT_INTERESTED", "NO_RESPONSE", "WON", "LOST",
            "EMAIL_INTERESTED", "EMAIL_NOT_INTERESTED", "EMAIL_BOUNCED", "EMAIL_NO_RESPONSE",
        ])
        self.assertEqual(feedback["fields"]["outcome"]["options"], ["POSITIVE", "NEGATIVE", "NEUTRAL"])
        self.assertEqual(signal["fields"]["signalType"]["options"], feedback["fields"]["feedbackType"]["options"])

        service = (MODULE / "Services" / "FeedbackSyncService.php").read_text(encoding="utf-8")
        hook = (EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "SalesFeedback" / "SalesFeedbackLearningSignalHook.php").read_text(encoding="utf-8")
        self.assertIn("externalFeedbackId", service)
        self.assertIn("hash('sha256'", service)
        self.assertIn("LearningSignal", hook)
        self.assertIn("salesFeedbackId", hook)
        self.assertIn("campaign", hook)

    def test_phase3b05a_brevo_email_event_metadata(self) -> None:
        self.assertEqual(
            _load_json(SURFACE_ENTITY_DEFS / "EmailEvent.json"),
            _load_json(MODULE_ENTITY_DEFS / "EmailEvent.json"),
        )
        event = _load_json(MODULE_ENTITY_DEFS / "EmailEvent.json")
        lead = _load_json(MODULE_ENTITY_DEFS / "Lead.json")
        self.assertEqual(
            set(event["fields"]),
            {
                "name",
                "externalMessageId",
                "eventType",
                "campaign",
                "eventAt",
                "source",
                "createdAt",
                "lead",
                "assignedUser",
                "teams",
            },
        )
        self.assertEqual(
            event["fields"]["eventType"]["options"],
            ["SENT", "DELIVERED", "OPENED", "CLICKED", "REPLIED", "BOUNCED"],
        )
        self.assertEqual(event["links"]["lead"]["foreign"], "emailEvents")
        self.assertIn("emailEvents", lead["links"])
        self.assertEqual(lead["links"]["emailEvents"]["entity"], "EmailEvent")

        client_defs = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "Lead.json")
        self.assertIn("emailEvents", client_defs.get("relationshipPanels", {}))

        service = (MODULE / "Services" / "BrevoEmailEventSyncService.php").read_text(encoding="utf-8")
        self.assertIn("externalMessageId", service)
        self.assertIn("eventType", service)
        self.assertIn("email_sent", service)
        self.assertIn("duplicate", service)
        self.assertIn("EmailEventWorkflowHook", service)

        hook = (
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "EmailEvent" / "EmailEventWorkflowHook.php"
        ).read_text(encoding="utf-8")
        self.assertIn("class EmailEventWorkflowHook", hook)
        self.assertIn("Follow up customer reply", hook)
        self.assertIn("Verify customer email", hook)
        self.assertIn("EmailLifecycleProjectionService", hook)
        self.assertIn("projectEmailEvent($event)", hook)
        self.assertNotIn("peEmailStatus", hook)
        self.assertNotIn("peEmailReplyStatus", hook)
        self.assertIn("getEntity('Task')", hook)

    def test_phase3b05b_email_workflow_hook(self) -> None:
        fields = _load_json(MODULE_ENTITY_DEFS / "Lead.json")["fields"]
        self.assertEqual(fields["peEmailStatus"]["options"], LEAD_EMAIL_STATUS_OPTIONS)
        self.assertEqual(fields["peLastEmailDate"]["type"], "datetime")
        self.assertEqual(fields["peEmailReplyStatus"]["type"], "varchar")
        self.assertIn("emailEvents", _load_json(MODULE_ENTITY_DEFS / "Lead.json")["links"])

        hook = (
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "EmailEvent" / "EmailEventWorkflowHook.php"
        ).read_text(encoding="utf-8")
        service = (MODULE / "Services" / "EmailLifecycleProjectionService.php").read_text(encoding="utf-8")
        self.assertIn("projectEmailEvent($event)", hook)
        self.assertIn("public function projectEmailEvent", service)
        self.assertIn("'OPENED', 'CLICKED'", service)
        self.assertNotIn("$lead->set", hook)
        self.assertNotIn("saveEntity($lead)", hook)
        self.assertIn("createTaskOnce", hook)
        # LearningSignal must remain untouched by this phase.
        self.assertNotIn("LearningSignal", hook)

    def test_phase3b05c_email_feedback_integration(self) -> None:
        feedback_hook = (
            EXT / "files" / "custom" / "Espo" / "Custom" / "Hooks" / "EmailEvent" / "EmailEventSalesFeedbackHook.php"
        ).read_text(encoding="utf-8")
        self.assertIn("class EmailEventSalesFeedbackHook", feedback_hook)
        self.assertIn("email-event:", feedback_hook)
        self.assertIn("CUSTOMER_REPLY", feedback_hook)
        self.assertIn("EMAIL_INTERESTED", feedback_hook)
        self.assertIn("EMAIL_BOUNCED", feedback_hook)
        self.assertIn("EMAIL_EVENT", feedback_hook)
        self.assertIn("getEntity('SalesFeedback')", feedback_hook)
        self.assertNotIn("getEntity('LearningSignal')", feedback_hook)

        panels = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "Lead.json")["relationshipPanels"]
        self.assertIn("emailEvents", panels)
        self.assertIn("salesFeedbacks", panels)
        self.assertIn("learningSignals", panels)

    def test_phase3b06_prospecting_workspace_ui(self) -> None:
        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertIn("Intelligence Summary", sections)
        self.assertIn("Opportunity Proposal", sections)
        self.assertIn("AI Research Information", sections)
        intelligence_fields = {
            cell["name"]
            for row in sections["Intelligence Summary"]
            for cell in row
            if isinstance(cell, dict)
        }
        self.assertTrue(
            {
                "name",
                "website",
                "addressCountry",
                "peOpportunityScoreV4",
                "peScoreTier",
                "peBestFirstProduct",
                "peResearchStatus",
                "peSourceType",
            }.issubset(intelligence_fields)
        )
        self.assertNotIn("peSourceBatchId", intelligence_fields)
        self.assertNotIn("peCandidateId", intelligence_fields)

        list_layout = _load_json(MODULE_LAYOUTS / "Lead" / "list.json")
        list_fields = [cell["name"] for cell in list_layout]
        self.assertEqual(
            list_fields,
            [
                "name",
                "addressCountry",
                "peOpportunityScoreV4",
                "peScoreTier",
                "peBestFirstProduct",
                "peResearchStatus",
                "outreachStatus",
                "nextFollowUpAt",
                "peEmailStatus",
                "pePriorityLevel",
            ],
        )

        client_defs = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "Lead.json")
        filter_names = [item["name"] for item in client_defs["filterList"]]
        self.assertEqual(
            filter_names,
            [
                "peTierA", "peTierB", "peTierC", "peTierD", "pePendingOutreach", "peAwaitingReply",
                "peHighPriority", "peFollowUpDue", "peRecentlyResearched", "peContactReady", "peRecentlySynced",
                "peResearchPending", "peResearchCompleted", "peResearchFailed", "peMissingEvidence",
                "peIncompleteResearchProjection", "peProposalReviewRequired", "peProposalEligible", "peProposalNotReady",
                "peScoreWithoutTier", "peCompletedWithoutEvidence", "peMissingBestFirstProduct", "peSyncFailed",
                "peMissingWebsite", "peProposalActionMissing", "peContactReadyWithoutContactMethod",
            ],
        )
        panels = client_defs["relationshipPanels"]
        self.assertIn("researchEvidences", panels)
        self.assertFalse(panels["researchEvidences"].get("create", True))
        self.assertEqual(panels["researchEvidences"].get("layout"), "listSmall")
        bottom = client_defs["bottomPanels"]["detail"]
        self.assertEqual(bottom[0], "__APPEND__")
        bottom_names = [item["name"] for item in bottom if isinstance(item, dict)]
        self.assertEqual(
            bottom_names,
            ["researchEvidences", "emailEvents", "salesFeedbacks", "learningSignals"],
        )

        select_defs = _load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "Lead.json")
        filter_map = select_defs["primaryFilterClassNameMap"]
        for key in ("peTierA", "peRecentlyResearched", "peContactReady", "peRecentlySynced"):
            self.assertIn(key, filter_map)

        tier_a = (
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeTierA.php"
        ).read_text(encoding="utf-8")
        self.assertIn("peScoreTier", tier_a)
        self.assertIn("'A'", tier_a)

        recently = (
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeRecentlyResearched.php"
        ).read_text(encoding="utf-8")
        self.assertIn("peLastResearchedAt>=", recently)
        self.assertIn("COMPLETED", recently)

        contact_ready = (
            MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters" / "PeContactReady.php"
        ).read_text(encoding="utf-8")
        self.assertIn("CONTACT_READY", contact_ready)

        dashlet = _load_json(
            MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingIntelligence.json"
        )
        self.assertEqual(dashlet["view"], "views/dashlets/abstract/record-list")
        self.assertEqual(dashlet["aclScope"], "Lead")
        self.assertEqual(dashlet["entityType"], "Lead")
        self.assertEqual(dashlet["options"]["defaults"]["orderBy"], "peOpportunityScoreV4")
        self.assertEqual(dashlet["options"]["defaults"]["order"], "desc")
        self.assertEqual(dashlet["options"]["defaults"]["displayRecords"], 10)

        evidence_list_small = _load_json(MODULE_LAYOUTS / "ResearchEvidence" / "listSmall.json")
        evidence_fields = [cell["name"] for cell in evidence_list_small]
        self.assertEqual(
            evidence_fields,
            ["name", "peEvidenceType", "peClaim", "peSourceUrl", "peConfidence", "createdAt"],
        )

        global_i18n = _load_json(MODULE / "Resources" / "i18n" / "en_US" / "Global.json")
        self.assertEqual(
            global_i18n["dashlets"]["ProspectingIntelligence"],
            "Prospecting Intelligence",
        )

        lead_i18n = _load_json(MODULE / "Resources" / "i18n" / "en_US" / "Lead.json")
        self.assertEqual(lead_i18n["presetFilters"]["peRecentlyResearched"], "Recently Researched")
        self.assertEqual(lead_i18n["presetFilters"]["peContactReady"], "Ready for Outreach")
        self.assertEqual(lead_i18n["labels"]["researchEvidences"], "AI Research Evidence")

        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["version"], RELEASE_VERSION)

    def test_phase3b07_operations_metadata(self) -> None:
        lead_filters = _load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "Lead.json")["primaryFilterClassNameMap"]
        required_filters = {
            "peTierA", "peTierB", "peTierC", "peTierD", "pePendingOutreach", "peAwaitingReply",
            "peHighPriority", "peFollowUpDue", "peResearchPending", "peResearchCompleted", "peResearchFailed",
            "peMissingEvidence", "peIncompleteResearchProjection", "peProposalReviewRequired", "peProposalEligible",
            "peProposalNotReady", "peScoreWithoutTier", "peCompletedWithoutEvidence", "peMissingBestFirstProduct",
            "peSyncFailed", "peMissingWebsite", "peProposalActionMissing", "peContactReadyWithoutContactMethod",
        }
        self.assertTrue(required_filters.issubset(lead_filters))

        filter_directory = MODULE / "Classes" / "Select" / "Lead" / "PrimaryFilters"
        for filter_name in required_filters:
            class_name = lead_filters[filter_name].rsplit("\\", 1)[-1]
            self.assertTrue((filter_directory / f"{class_name}.php").is_file(), msg=filter_name)

        missing_evidence = (filter_directory / "PeMissingEvidence.php").read_text(encoding="utf-8")
        self.assertIn("leftJoin('ResearchEvidence'", missing_evidence)
        self.assertIn("'researchEvidence.id' => null", missing_evidence)
        score_without_tier = (filter_directory / "PeScoreWithoutTier.php").read_text(encoding="utf-8")
        self.assertIn("peOpportunityScoreV4", score_without_tier)
        self.assertIn("peScoreTier", score_without_tier)

        detail = _load_json(MODULE_LAYOUTS / "Lead" / "detail.json")
        sections = {section["label"]: section["rows"] for section in detail}
        self.assertEqual(sections["Pipeline"][0], [{"name": "outreachStatus"}, False])
        self.assertIn("pePriorityLevel", {cell["name"] for row in sections["Intelligence Summary"] for cell in row if isinstance(cell, dict)})

        evidence_list = [item["name"] for item in _load_json(MODULE_LAYOUTS / "ResearchEvidence" / "list.json")]
        self.assertEqual(evidence_list, ["name", "lead", "peEvidenceType", "peClaim", "peSourceUrl", "peConfidence", "createdAt"])
        feedback_list = [item["name"] for item in _load_json(MODULE_LAYOUTS / "SalesFeedback" / "list.json")]
        self.assertEqual(feedback_list, ["name", "lead", "feedbackType", "outcome", "reason", "createdAt", "createdBy"])
        feedback_detail = _load_json(MODULE_LAYOUTS / "SalesFeedback" / "detail.json")
        feedback_fields = {cell["name"] for row in feedback_detail[0]["rows"] for cell in row if isinstance(cell, dict)}
        self.assertTrue({"lead", "feedbackType", "outcome", "reason", "note", "createdAt", "createdBy"}.issubset(feedback_fields))

        app_layouts = _load_json(MODULE / "Resources" / "metadata" / "app" / "layouts.json")
        self.assertEqual(app_layouts["ResearchEvidence"]["detail"]["module"], "Prospecting")
        self.assertEqual(app_layouts["SalesFeedback"]["list"]["module"], "Prospecting")
        self.assertEqual(app_layouts["SalesFeedback"]["detail"]["module"], "Prospecting")

        feedback_filters = _load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "SalesFeedback.json")["primaryFilterClassNameMap"]
        self.assertEqual(set(feedback_filters), {"positiveFeedback", "negativeFeedback", "needsFollowUp", "recentFeedback"})
        feedback_filter_directory = MODULE / "Classes" / "Select" / "SalesFeedback" / "PrimaryFilters"
        for class_path in feedback_filters.values():
            class_name = class_path.rsplit("\\", 1)[-1]
            self.assertTrue((feedback_filter_directory / f"{class_name}.php").is_file())

        for name, entity_type in (("RecentResearchEvidence", "ResearchEvidence"), ("RecentSalesFeedback", "SalesFeedback")):
            dashlet = _load_json(MODULE / "Resources" / "metadata" / "dashlets" / f"{name}.json")
            self.assertEqual(dashlet["view"], "views/dashlets/abstract/record-list")
            self.assertEqual(dashlet["entityType"], entity_type)
            self.assertEqual(dashlet["aclScope"], entity_type)

        role_script = (ROOT / "deployment" / "provisioning" / "phase3b06_provision_workspace_roles.php").read_text(encoding="utf-8")
        self.assertIn("'ResearchEvidence' => ['create' => 'no', 'read' => 'own'", role_script)
        self.assertIn("$fd[$f] = ['read' => 'no', 'edit' => 'no'];", role_script)

        provisioning = ROOT / "deployment" / "provisioning"
        dashboard_script = (provisioning / "phase3b07_provision_operations_dashboards.php").read_text(encoding="utf-8")
        self.assertIn("Prospecting Operations", dashboard_script)
        self.assertIn("phase3b07-tier-a", dashboard_script)
        self.assertIn("phase3u03-summary", dashboard_script)
        self.assertIn("ProspectingSummary", dashboard_script)
        self.assertIn("ProspectingRecentDiscovery", dashboard_script)
        self.assertIn("RecentResearchEvidence", dashboard_script)
        self.assertIn("$includeRelatedEntityDashlets", dashboard_script)
        self.assertIn("$userName !== 'manager_test'", dashboard_script)
        self.assertIn(
            "dashboardOptions('Sync Issues', 'Lead', 'modifiedAt', 'peSyncFailed')",
            dashboard_script,
        )
        self.assertNotIn("peLastSyncAt", dashboard_script)
        self.assertNotIn("getEntity('Role')", dashboard_script)
        self.assertIn("'peLastSyncAt'", role_script)
        self.assertIn("$fd[$f] = ['read' => 'no', 'edit' => 'no'];", role_script)
        cleanup_script = (provisioning / "phase3b07_cleanup_validation_records.php").read_text(encoding="utf-8")
        self.assertIn("[CHITU_PHASE3B07_TEST]%", cleanup_script)
        self.assertIn("ResearchEvidence", cleanup_script)
        self.assertIn("SalesFeedback", cleanup_script)
        self.assertIn("Task", cleanup_script)
        self.assertNotIn("Opportunity", cleanup_script)
        self.assertTrue((provisioning / "phase3b07_provision_validation_user.php").is_file())
        self.assertTrue((provisioning / "phase3b07_provision_synthetic_records.php").is_file())

        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["version"], RELEASE_VERSION)

    def test_phase3c01_acquisition_workspace_foundation(self) -> None:
        for name in ("SearchJob", "ProspectPool"):
            self.assertEqual(
                _load_json(SURFACE_ENTITY_DEFS / f"{name}.json"),
                _load_json(MODULE_ENTITY_DEFS / f"{name}.json"),
                msg=f"Parity mismatch for {name}",
            )
            self.assertTrue((MODULE / "Resources" / "metadata" / "scopes" / f"{name}.json").is_file())
            self.assertTrue((MODULE / "Resources" / "metadata" / "clientDefs" / f"{name}.json").is_file())
            self.assertFalse(
                (EXT / "files" / "custom" / "Espo" / "Custom" / "Resources" / "metadata" / "scopes" / f"{name}.json").exists(),
                msg=f"{name} scope must have a single module authority",
            )

        search_job = _load_json(MODULE_ENTITY_DEFS / "SearchJob.json")
        self.assertEqual(
            set(search_job["fields"]),
            {
                "name", "keyword", "country", "strategy", "product", "status", "source", "priority",
                "queryFingerprint", "resultCount", "acceptedCount", "rejectedCount", "errorMessage", "startedAt",
                "completedAt", "prospectCount", "failureReason", "createdAt", "assignedUser", "teams", "prospectPools",
            },
        )
        self.assertEqual(search_job["fields"]["status"]["options"], ["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"])
        self.assertEqual(search_job["fields"]["status"].get("default"), "QUEUED")
        self.assertEqual(search_job["links"]["prospectPools"]["entity"], "ProspectPool")
        self.assertEqual(search_job["links"]["prospectPools"]["foreign"], "searchJob")

        pool = _load_json(MODULE_ENTITY_DEFS / "ProspectPool.json")
        self.assertEqual(pool["fields"]["queue"]["options"], ["DISCOVERY", "QUALIFICATION", "RESEARCH", "CRM"])
        self.assertEqual(pool["fields"]["queue"].get("default"), "DISCOVERY")
        self.assertEqual(pool["fields"]["researchStatus"]["options"], ["NOT_STARTED", "PENDING", "COMPLETED", "FAILED"])
        self.assertEqual(pool["fields"]["qualificationStatus"]["options"], ["PENDING", "QUALIFIED", "REJECTED"])
        self.assertEqual(pool["fields"]["crmPushStatus"]["options"], ["NOT_READY", "READY", "PUSHED", "FAILED"])
        self.assertIn("searchJob", pool["links"])
        self.assertNotIn("lead", pool["fields"])
        self.assertNotIn("crmLead", pool["fields"])

        search_client = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SearchJob.json")
        pool_client = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "ProspectPool.json")
        self.assertEqual([item["name"] for item in search_client["filterList"]], ["jobsQueued", "jobsRunning", "jobsCompleted", "jobsFailed", "jobsCancelled"])
        # Phase3U02: business filters first, then existing queue filters (UI order intentional)
        self.assertEqual(
            [item["name"] for item in pool_client["filterList"]],
            [
                "prospectsNew",
                "prospectsAccepted",
                "prospectsRejected",
                "prospectsDuplicate",
                "prospectsReadyForResearch",
                "discoveryQueue",
                "qualificationQueue",
                "researchQueue",
                "crmQueue",
            ],
        )

        search_filters = _load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "SearchJob.json")["primaryFilterClassNameMap"]
        pool_filters = _load_json(MODULE / "Resources" / "metadata" / "selectDefs" / "ProspectPool.json")["primaryFilterClassNameMap"]
        self.assertEqual(set(search_filters), {"jobsQueued", "jobsRunning", "jobsCompleted", "jobsFailed", "jobsCancelled"})
        self.assertEqual(
            set(pool_filters),
            {
                "prospectsNew",
                "prospectsAccepted",
                "prospectsRejected",
                "prospectsDuplicate",
                "prospectsReadyForResearch",
                "discoveryQueue",
                "qualificationQueue",
                "researchQueue",
                "crmQueue",
            },
        )
        for class_path in (*search_filters.values(), *pool_filters.values()):
            entity_name = "SearchJob" if "SearchJob" in class_path else "ProspectPool"
            class_name = class_path.rsplit("\\", 1)[-1]
            self.assertTrue(
                (MODULE / "Classes" / "Select" / entity_name / "PrimaryFilters" / f"{class_name}.php").is_file(),
                msg=class_path,
            )

        expected_dashlets = {
            "AcquisitionSearchStrategies": ("SearchStrategy", None),
            "AcquisitionDiscoveryJobs": ("SearchJob", None),
            "AcquisitionJobsRunning": ("SearchJob", "jobsRunning"),
            "AcquisitionJobsWaiting": ("SearchJob", "jobsQueued"),
            "AcquisitionJobsCompleted": ("SearchJob", "jobsCompleted"),
            "AcquisitionJobsFailed": ("SearchJob", "jobsFailed"),
            "AcquisitionLeadPool": ("ProspectPool", None),
            "AcquisitionResearchQueue": ("ProspectPool", "researchQueue"),
        }
        for name, (entity_type, primary) in expected_dashlets.items():
            dashlet = _load_json(MODULE / "Resources" / "metadata" / "dashlets" / f"{name}.json")
            self.assertEqual(dashlet["entityType"], entity_type)
            self.assertEqual(dashlet["aclScope"], entity_type)
            self.assertEqual(dashlet["options"]["defaults"].get("searchData", {}).get("primary"), primary)

        layouts = _load_json(MODULE / "Resources" / "metadata" / "app" / "layouts.json")
        self.assertEqual(layouts["SearchJob"]["detail"]["module"], "Prospecting")
        self.assertEqual(layouts["ProspectPool"]["list"]["module"], "Prospecting")

        provisioning = (ROOT / "deployment" / "provisioning" / "phase3c01_provision_acquisition_workspace.php").read_text(encoding="utf-8")
        self.assertIn("Prospecting Home", provisioning)
        self.assertIn("ProspectingSummary", provisioning)
        self.assertIn("ProspectingRecentDiscovery", provisioning)
        self.assertIn("phase3u03-summary", provisioning)
        self.assertIn("phase3u03-recent-discovery", provisioning)
        self.assertIn("phase3c01-research-queue", provisioning)
        self.assertIn("phase3c02-search-strategies", provisioning)
        self.assertIn("/^(phase3c0[12]|phase3u03)-/", provisioning)
        self.assertIn("SearchJob", provisioning)
        self.assertIn("ProspectPool", provisioning)
        self.assertNotIn("getEntity('Lead')", provisioning)
        self.assertNotIn("getEntity('Opportunity')", provisioning)

        summary_dashlet = _load_json(MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingSummary.json")
        self.assertEqual(summary_dashlet["view"], "custom:views/dashlets/prospecting-summary")
        self.assertEqual(summary_dashlet["aclScope"], "ProspectPool")
        recent_dashlet = _load_json(MODULE / "Resources" / "metadata" / "dashlets" / "ProspectingRecentDiscovery.json")
        self.assertEqual(recent_dashlet["entityType"], "SearchJob")
        self.assertEqual(recent_dashlet["options"]["defaults"]["title"], "Recent Discovery Activity")
        self.assertTrue((EXT / "files" / "client" / "custom" / "src" / "views" / "dashlets" / "prospecting-summary.js").is_file())
        self.assertTrue((EXT / "files" / "client" / "custom" / "res" / "templates" / "dashlets" / "prospecting-summary.tpl").is_file())

        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["version"], RELEASE_VERSION)

    def test_phase3c02_search_strategy_discovery_jobs(self) -> None:
        search_job = _load_json(MODULE_ENTITY_DEFS / "SearchJob.json")
        self.assertEqual(search_job["links"]["strategy"]["entity"], "SearchStrategy")
        self.assertEqual(search_job["links"]["strategy"]["foreign"], "searchJobs")
        self.assertEqual(search_job["fields"]["priority"]["options"], ["P1", "P2", "P3"])
        self.assertEqual(search_job["fields"]["priority"].get("default"), "P2")
        self.assertIn("queryFingerprint", search_job["indexes"])

        client_defs = _load_json(MODULE / "Resources" / "metadata" / "clientDefs" / "SearchStrategy.json")
        # Phase3U03-C: list-only empty-state presentation view is allowed; detail/edit remain frozen.
        self.assertEqual(
            client_defs.get("recordViews"),
            {"list": "custom:views/search-strategy/record/list"},
        )
        self.assertNotIn("detail", client_defs.get("recordViews", {}))
        self.assertNotIn("edit", client_defs.get("recordViews", {}))
        self.assertEqual(client_defs["detailActionList"][-1]["name"], "generateJobs")
        self.assertEqual(client_defs["detailActionList"][-1]["handler"], "custom:handlers/search-strategy/generate-jobs")
        self.assertFalse(client_defs["relationshipPanels"]["searchJobs"]["create"])
        self.assertTrue((EXT / "files" / "client" / "custom" / "src" / "views" / "search-strategy" / "detail.js").is_file())
        self.assertTrue((EXT / "files" / "client" / "custom" / "src" / "views" / "search-strategy" / "record" / "list.js").is_file())

        templates = (MODULE / "Services" / "SearchStrategyTemplates.php").read_text(encoding="utf-8")
        for product in ("PlateCycler", "Resin Tank", "Filament Dryer", "Resin", "LCD Replacement", "Mainboard", "UV Meter", "Heater"):
            self.assertIn(f"'{product}'", templates)
        for persona in ("Distributor", "Reseller", "Dealer", "3D Printer Store", "Print Farm", "Service Provider", "Education Supplier", "Dental Distributor", "Industrial Distributor"):
            self.assertIn(f"'{persona}'", templates)
        self.assertIn("MAX_JOBS = 40", templates)

        service = (MODULE / "Services" / "SearchStrategyService.php").read_text(encoding="utf-8")
        self.assertIn("hash('sha256'", service)
        self.assertIn("queryFingerprint", service)
        self.assertIn("Unsupported or missing product", service)
        self.assertIn("Missing country", service)
        self.assertIn("Unsupported targetPersona", service)
        self.assertIn("exceeds maximum Discovery Job count", service)
        self.assertIn("checkEntityEdit($strategy)", service)
        self.assertIn("'status' => 'QUEUED'", service)
        self.assertNotIn("getEntity('Lead')", service)
        self.assertNotIn("getEntity('Opportunity')", service)
        self.assertNotIn("curl_", service)
        self.assertNotIn("file_get_contents", service)
        self.assertNotIn("DeepSeek", service)

        routes = _load_json(MODULE / "Resources" / "routes.json")
        self.assertIn(
            {
                "route": "/Prospecting/search-strategy/generate-jobs",
                "method": "post",
                "actionClassName": "Espo\\Modules\\Prospecting\\Api\\PostGenerateSearchStrategyJobs",
            },
            routes,
        )
        self.assertEqual(_load_json(MODULE / "Resources" / "routes.json"), _load_json(EXT / "Resources" / "routes.json"))

        role_script = (ROOT / "deployment" / "provisioning" / "phase3b06_provision_workspace_roles.php").read_text(encoding="utf-8")
        self.assertNotIn("SearchStrategy", role_script)
        self.assertNotIn("SearchJob", role_script)
        self.assertNotIn("ProspectPool", role_script)

    def test_phase3c02_1_acquisition_acl_provisioning(self) -> None:
        script = (ROOT / "deployment" / "provisioning" / "phase3c02_1_provision_acquisition_acl.php").read_text(encoding="utf-8")

        self.assertIn("$scopeList = ['SearchStrategy', 'SearchJob', 'ProspectPool'];", script)
        self.assertIn("'Admin' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all']", script)
        self.assertIn("'Sales Manager' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no']", script)
        self.assertIn("'Sales User' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no']", script)
        self.assertIn("'Integration Bot' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no']", script)
        self.assertIn("$roleData[$scopeName] = $permissions;", script)
        self.assertNotIn("getEntity('Role')", script)
        self.assertNotIn("'Lead' =>", script)
        self.assertNotIn("'Opportunity' =>", script)

        manifest = _load_json(EXT / "manifest.json")
        self.assertEqual(manifest["version"], RELEASE_VERSION)


if __name__ == "__main__":
    unittest.main()
