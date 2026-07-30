"""Phase3C23 WP1: execution analytics foundation boundary tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"

ENTITY_DEFS = {
    "OptimizationInsight": METADATA / "entityDefs" / "OptimizationInsight.json",
    "PerformanceMetric": METADATA / "entityDefs" / "PerformanceMetric.json",
}
SCOPES = {
    name: METADATA / "scopes" / f"{name}.json" for name in ENTITY_DEFS
}
ACL_DEFS = {
    name: METADATA / "aclDefs" / f"{name}.json" for name in ENTITY_DEFS
}
PHP_FILES = [
    MODULE / "Entities" / "OptimizationInsight.php",
    MODULE / "Entities" / "PerformanceMetric.php",
    MODULE / "Services" / "C23AnalyticsSaveOption.php",
    MODULE / "Services" / "OptimizationInsightService.php",
    MODULE / "Services" / "PerformanceMetricService.php",
    MODULE / "Hooks" / "OptimizationInsight" / "OptimizationInsightImmutableGuard.php",
    MODULE / "Hooks" / "PerformanceMetric" / "PerformanceMetricImmutableGuard.php",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Phase3C23Wp1AnalyticsFoundationTests(unittest.TestCase):
    def test_c23_entity_contracts_exist_with_only_approved_fields(self) -> None:
        expected_fields = {
            "OptimizationInsight": {
                "name",
                "insightType",
                "title",
                "description",
                "recommendation",
                "evidenceReference",
                "sourcePeriodStart",
                "sourcePeriodEnd",
                "generatedAt",
                "freshnessStatus",
                "confidence",
                "status",
                "reviewedAt",
                "reviewedByReference",
                "decisionNote",
                "supersedesInsightId",
                "createdAt",
            },
            "PerformanceMetric": {
                "name",
                "metricType",
                "metricValue",
                "aggregationPeriod",
                "sampleSize",
                "confidenceLevel",
                "freshnessStatus",
                "sourceReference",
                "generatedAt",
                "createdAt",
            },
        }
        forbidden = {
            "prospectId",
            "prospectCandidateId",
            "prospectPoolId",
            "leadId",
            "opportunityId",
            "qualificationScore",
            "rankingScore",
            "approvalDecision",
            "executionAction",
            "providerAction",
            "automationRule",
            "triggerAction",
            "policyChange",
            "approvalAuthority",
            "executionCommand",
            "providerSelection",
            "workflowMutation",
        }

        for entity, path in ENTITY_DEFS.items():
            self.assertTrue(path.is_file(), f"Missing {entity} entity definition")
            definition = load_json(path)
            fields = set(definition["fields"])
            self.assertEqual(fields, expected_fields[entity])
            self.assertFalse(fields & forbidden)
            self.assertNotIn("links", definition)
            self.assertNotIn("relationships", definition)
            for field in definition["fields"].values():
                self.assertTrue(field.get("readOnly"), entity)

    def test_freshness_and_generated_at_are_required(self) -> None:
        expected_statuses = {"CURRENT", "AGING", "STALE", "ARCHIVAL"}
        for path in ENTITY_DEFS.values():
            definition = load_json(path)
            self.assertTrue(definition["fields"]["generatedAt"]["required"])
            self.assertEqual(
                set(definition["fields"]["freshnessStatus"]["options"]),
                expected_statuses,
            )

    def test_entities_and_services_are_explicitly_advisory_and_read_isolated(self) -> None:
        optimization = (
            MODULE / "Services" / "OptimizationInsightService.php"
        ).read_text(encoding="utf-8")
        metric = (
            MODULE / "Services" / "PerformanceMetricService.php"
        ).read_text(encoding="utf-8")

        for source, entity in (
            (optimization, "OptimizationInsight"),
            (metric, "PerformanceMetric"),
        ):
            self.assertIn("function create", source)
            self.assertIn("function validate", source)
            self.assertIn("function read", source)
            self.assertIn("checkEntityRead", source)
            self.assertIn(f"getNewEntity(self::ENTITY_TYPE)", source)
            self.assertIn("SaveOption", source)
            self.assertNotRegex(source, r"(?i)function\s+(execute|approve|trigger)")
            self.assertNotRegex(source, r"(?i)(workflow|actiongate).*decide")

        self.assertIn("advisory-only", optimization.lower())
        self.assertNotIn("executionCommand", optimization)
        self.assertNotIn("policyChange", metric)

    def test_immutability_guards_only_allow_service_authorized_creation(self) -> None:
        expected = {
            "OptimizationInsight": "OPTIMIZATION_INSIGHT_CREATE_AUTHORIZED",
            "PerformanceMetric": "PERFORMANCE_METRIC_CREATE_AUTHORIZED",
        }
        for entity, marker in expected.items():
            guard = (
                MODULE / "Hooks" / entity / f"{entity}ImmutableGuard.php"
            ).read_text(encoding="utf-8")
            self.assertIn(marker, guard)
            self.assertIn("isNew", guard)
            self.assertIn("BeforeRemove", guard)
            self.assertIn("cannot be deleted", guard)

    def test_acl_is_authorized_read_only_and_portal_is_blocked(self) -> None:
        app_acl = load_json(METADATA / "app" / "acl.json")
        portal_acl = load_json(METADATA / "app" / "aclPortal.json")
        for entity, scope_path in SCOPES.items():
            scope = load_json(scope_path)
            self.assertTrue(scope["entity"])
            self.assertTrue(scope["acl"])
            self.assertFalse(scope["aclPortal"])
            self.assertEqual(load_json(ACL_DEFS[entity]), {})
            self.assertFalse(app_acl["mandatory"]["scopeLevel"][entity])
            rights = app_acl["adminMandatory"]["scopeLevel"][entity]
            expected_edit = "all" if entity == "OptimizationInsight" else "no"
            self.assertEqual(rights, {
                "create": "yes",
                "read": "all",
                "edit": expected_edit,
                "delete": "no",
            })
            self.assertFalse(portal_acl["mandatory"]["scopeLevel"][entity])

    def test_no_c20_c21_or_c22_mutation_or_ownership_leaks(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in PHP_FILES)
        forbidden = [
            "ResearchEvidence",
            "AIQualificationInsight",
            "HumanFeedback",
            "ProspectCandidate",
            "ActionGateService",
            "saveEntity($prospectRun",
            "saveEntity($executionLedger",
            "decide(",
            "Lead",
            "Opportunity",
        ]
        for value in forbidden:
            self.assertNotIn(value, source, value)

        for path in ENTITY_DEFS.values():
            definition = load_json(path)
            self.assertNotIn("links", definition)
            self.assertNotIn("Lead", path.read_text(encoding="utf-8"))
            self.assertNotIn("Opportunity", path.read_text(encoding="utf-8"))

    def test_no_egress_secret_or_vendor_runtime_is_present(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in PHP_FILES)
        forbidden_literals = [
            "curl",
            "guzzlehttp",
            "file_get_contents",
            "apify",
            "apollo",
            "hunter",
            "deepseek",
            "openai",
            "instantly",
            "brevo",
            "smtp",
            "api key",
            "access token",
            "secret",
        ]
        lower_source = source.lower()
        for value in forbidden_literals:
            self.assertNotIn(value, lower_source, value)
        self.assertNotRegex(
            source,
            re.compile(r"(?i)(httpclient|https?://|sdk|network|queue|scheduler|worker)"),
        )

    def test_extension_inventory_lists_every_new_php_file(self) -> None:
        inventory = (
            EXT / "tests" / "test_extension_skeleton.py"
        ).read_text(encoding="utf-8")
        for path in PHP_FILES:
            self.assertIn(path.name, inventory)


if __name__ == "__main__":
    unittest.main()
