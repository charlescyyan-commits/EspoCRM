"""Phase3C24 WP3.5 boundary security and full verification tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"

REVENUE_INSIGHT = "RevenueInsight"
PIPELINE_METRIC = "PipelineMetric"

REVENUE_ENTITY = MODULE / "Entities" / f"{REVENUE_INSIGHT}.php"
PIPELINE_ENTITY = MODULE / "Entities" / f"{PIPELINE_METRIC}.php"
REVENUE_DEFS = METADATA / "entityDefs" / f"{REVENUE_INSIGHT}.json"
PIPELINE_DEFS = METADATA / "entityDefs" / f"{PIPELINE_METRIC}.json"

REVENUE_IMMUTABLE = (
    MODULE / "Hooks" / REVENUE_INSIGHT / "RevenueInsightImmutableGuard.php"
)
REVENUE_LIFECYCLE = (
    MODULE / "Hooks" / REVENUE_INSIGHT / "RevenueInsightLifecycleGuard.php"
)
PIPELINE_INTEGRITY = (
    MODULE / "Hooks" / PIPELINE_METRIC / "PipelineMetricIntegrityGuard.php"
)

REVENUE_OPTION = MODULE / "Services" / "C24RevenueInsightSaveOption.php"
PIPELINE_OPTION = MODULE / "Services" / "C24PipelineMetricSaveOption.php"
REVENUE_SERVICE = MODULE / "Services" / "RevenueInsightService.php"
PIPELINE_SERVICE = MODULE / "Services" / "PipelineMetricService.php"

WP3_PHP = [
    REVENUE_ENTITY,
    PIPELINE_ENTITY,
    REVENUE_IMMUTABLE,
    REVENUE_LIFECYCLE,
    PIPELINE_INTEGRITY,
    REVENUE_OPTION,
    PIPELINE_OPTION,
    REVENUE_SERVICE,
    PIPELINE_SERVICE,
]

REVENUE_ALLOWED = {
    "name",
    "sourceReference",
    "provenance",
    "insightSummary",
    "interpretation",
    "confidence",
    "metricReferences",
    "reportingPeriod",
    "freshnessStatus",
    "reviewStatus",
    "reviewNote",
    "createdAt",
    "createdBy",
}

PIPELINE_ALLOWED = {
    "metricName",
    "metricType",
    "value",
    "unit",
    "reportingPeriod",
    "methodology",
    "provenance",
    "freshnessStatus",
    "createdAt",
    "createdBy",
}

FORBIDDEN_CRM_FIELDS = {
    "Opportunity",
    "opportunityId",
    "Lead",
    "leadId",
    "Account",
    "accountId",
    "Contact",
    "contactId",
    "Forecast",
    "forecastAmount",
    "forecastCommitment",
    "RevenueAmount",
    "SalesStage",
    "salesStage",
    "PipelineStage",
    "pipelineStage",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wp3_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP3_PHP)


# ── Section 1: Entity Contract ───────────────────────────────────────────


def test_entity_contract_revenue_insight_approved_fields_only() -> None:
    assert REVENUE_ENTITY.is_file()
    source = REVENUE_ENTITY.read_text(encoding="utf-8")
    assert "final class RevenueInsight" in source
    assert "ENTITY_TYPE = 'RevenueInsight'" in source
    defs = load_json(REVENUE_DEFS)
    assert set(defs["fields"]) == REVENUE_ALLOWED
    assert "links" not in defs
    assert not set(defs["fields"]) & FORBIDDEN_CRM_FIELDS


def test_entity_contract_pipeline_metric_approved_fields_only() -> None:
    assert PIPELINE_ENTITY.is_file()
    source = PIPELINE_ENTITY.read_text(encoding="utf-8")
    assert "final class PipelineMetric" in source
    assert "ENTITY_TYPE = 'PipelineMetric'" in source
    defs = load_json(PIPELINE_DEFS)
    assert set(defs["fields"]) == PIPELINE_ALLOWED
    assert "links" not in defs
    decision_fields = {
        "decisionAuthority",
        "workflowTrigger",
        "automationAction",
        "forecastCommitment",
        "revenueCommitment",
    }
    assert not set(defs["fields"]) & (FORBIDDEN_CRM_FIELDS | decision_fields)


# ── Section 2: Guard Verification ────────────────────────────────────────


def test_revenue_guards_protect_immutable_and_lifecycle_fields() -> None:
    assert REVENUE_IMMUTABLE.is_file()
    assert REVENUE_LIFECYCLE.is_file()
    immutable = REVENUE_IMMUTABLE.read_text(encoding="utf-8")
    lifecycle = REVENUE_LIFECYCLE.read_text(encoding="utf-8")

    for field in (
        "sourceReference",
        "provenance",
        "metricReferences",
        "reportingPeriod",
        "createdAt",
        "createdBy",
    ):
        assert f"'{field}'" in immutable
    assert "is immutable" in immutable
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in immutable
    assert "public static int $order = 1000" in immutable
    assert "public static int $order = 1010" in lifecycle


def test_revenue_lifecycle_states_and_invalid_transitions() -> None:
    source = REVENUE_LIFECYCLE.read_text(encoding="utf-8")
    for state in ("GENERATED", "REVIEWED", "ACCEPTED", "REJECTED"):
        assert f"'{state}'" in source
    for transition in (
        "'GENERATED' => ['REVIEWED']",
        "'REVIEWED' => ['ACCEPTED', 'REJECTED']",
        "'ACCEPTED' => []",
        "'REJECTED' => []",
    ):
        assert transition in source
    assert "transition {$from} to {$to} is forbidden" in source
    for marker in (
        "LIFECYCLE_ACTOR_REFERENCE",
        "LIFECYCLE_TRANSITION_REASON",
        "LIFECYCLE_TRANSITION_TIMESTAMP",
    ):
        assert marker in source
    assert "authenticated actor" in source
    assert "transition reason" in source
    assert "requires timestamp" in source


def test_pipeline_integrity_guard_protects_metric_definition_fields() -> None:
    assert PIPELINE_INTEGRITY.is_file()
    source = PIPELINE_INTEGRITY.read_text(encoding="utf-8")
    for field in ("metricType", "methodology", "provenance", "reportingPeriod"):
        assert f"'{field}'" in source
    assert "INTEGRITY_UPDATE_AUTHORIZED" in source
    assert "requires authorized integrity context" in source
    assert "INTEGRITY_UPDATE_AUTHORIZED" in PIPELINE_OPTION.read_text(encoding="utf-8")


# ── Section 3: Service Boundary ──────────────────────────────────────────


def test_revenue_service_allows_advisory_assembly_only() -> None:
    source = REVENUE_SERVICE.read_text(encoding="utf-8")
    for method in (
        "assembleContext",
        "validateProvenance",
        "evaluateFreshness",
        "prepareAdvisorySummary",
    ):
        assert f"function {method}" in source
    for forbidden in (
        "saveEntity",
        "getEntity('Opportunity')",
        "getEntity('Lead')",
        "forecast",
        "workflow",
        "EntityManager",
    ):
        assert forbidden not in source, forbidden


def test_pipeline_service_allows_validation_and_aggregation_only() -> None:
    source = PIPELINE_SERVICE.read_text(encoding="utf-8")
    for method in ("validateMetric", "validateProvenance", "evaluateFreshness", "aggregate"):
        assert f"function {method}" in source
    for forbidden in (
        "decisionAuthority",
        "automation",
        "workflow",
        "saveEntity",
        "getEntity",
        "EntityManager",
        "createEntity",
    ):
        assert forbidden not in source, forbidden


# ── Sections 4–10: Cross-layer + security scans ──────────────────────────


def test_c20_boundary_no_provider_or_egress() -> None:
    source = wp3_source().lower()
    for token in (
        "curl",
        "guzzle",
        "guzzlehttp",
        "sdk",
        "provider",
        "credential",
        "secret",
        "token",
        "httpclient",
        "file_get_contents",
    ):
        assert token not in source, token
    assert not re.search(r"(?i)https?://", wp3_source())


def test_c21_boundary_no_qualification_ownership() -> None:
    source = wp3_source()
    for value in (
        "AIQualificationInsight",
        "ResearchEvidence",
        "HumanFeedback",
        "AIQualificationInsightService",
        "ResearchEvidenceService",
        "HumanFeedbackService",
    ):
        assert value not in source, value


def test_c22_boundary_no_execution_influence() -> None:
    source = wp3_source()
    for value in (
        "ActionGate",
        "ExecutionLedger",
        "ProspectRun",
        "SendExecution",
        "ActionGateService",
        "ExecutionLedgerService",
        "ProspectRunLifecycleService",
    ):
        assert value not in source, value


def test_c23_boundary_no_metric_duplication_or_mutation() -> None:
    source = wp3_source()
    for value in (
        "PerformanceMetric",
        "OptimizationInsight",
        "FeedbackLearningObservation",
        "PerformanceMetricService",
        "OptimizationInsightService",
        "FeedbackLearningObservationService",
    ):
        assert value not in source, value

    assert "ENTITY_TYPE = 'PipelineMetric'" in PIPELINE_ENTITY.read_text(encoding="utf-8")
    assert "ENTITY_TYPE = 'RevenueInsight'" in REVENUE_ENTITY.read_text(encoding="utf-8")
    performance = load_json(METADATA / "entityDefs" / "PerformanceMetric.json")
    optimization = load_json(METADATA / "entityDefs" / "OptimizationInsight.json")
    assert set(load_json(PIPELINE_DEFS)["fields"]) != set(performance["fields"])
    assert set(load_json(REVENUE_DEFS)["fields"]) != set(optimization["fields"])


def test_wp1_wp2_boundary_no_reply_or_candidate_mutation() -> None:
    source = wp3_source()
    for value in (
        "ReplySignal",
        "ReplySignalService",
        "C24ReplySignalSaveOption",
        "OpportunityCandidate",
        "OpportunityCandidateLifecycleService",
        "C24OpportunityCandidateSaveOption",
    ):
        assert value not in source, value


def test_crm_core_boundary_no_write_path_or_fk() -> None:
    source = wp3_source()
    for value in (
        "getEntity('Opportunity')",
        "getEntity('Lead')",
        "getEntity('Account')",
        "getEntity('Contact')",
        "saveEntity",
        "createEntity",
        "use Espo\\Entities\\Opportunity",
        "use Espo\\Entities\\Lead",
        '"entity": "Opportunity"',
        '"entity": "Lead"',
    ):
        assert value not in source, value
    assert "links" not in load_json(REVENUE_DEFS)
    assert "links" not in load_json(PIPELINE_DEFS)


def test_security_runtime_scan_no_background_execution() -> None:
    source = wp3_source().lower()
    for token in (
        "worker",
        "scheduler",
        "queue",
        "webhook",
        "workflow",
        "automation",
        "eventlistener",
        "cron",
        "background",
    ):
        assert token not in source, token
    assert not (MODULE / "Jobs").exists()
    assert not list((MODULE / "Api").glob("*Revenue*"))
    assert not list((MODULE / "Api").glob("*Pipeline*"))
    assert not list((MODULE / "Controllers").glob("*Revenue*"))
    assert not list((MODULE / "Controllers").glob("*Pipeline*"))


# ── Section 11: Inventory ────────────────────────────────────────────────


def test_inventory_lists_only_approved_wp3_artifacts() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    approved = [
        "RevenueInsight.php",
        "PipelineMetric.php",
        "RevenueInsightService.php",
        "PipelineMetricService.php",
        "C24RevenueInsightSaveOption.php",
        "C24PipelineMetricSaveOption.php",
        "RevenueInsightImmutableGuard.php",
        "RevenueInsightLifecycleGuard.php",
        "PipelineMetricIntegrityGuard.php",
    ]
    for name in approved:
        assert name in inventory, name
        path_matches = [path for path in WP3_PHP if path.name == name]
        assert path_matches, name
        assert path_matches[0].is_file()

    assert "RevenueInsightLifecycleService.php" not in inventory
    assert not (MODULE / "Services" / "RevenueInsightLifecycleService.php").exists()
    assert not (MODULE / "Services" / "PipelineMetricIntegrityService.php").exists()
