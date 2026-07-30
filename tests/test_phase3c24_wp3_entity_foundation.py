"""Phase3C24 WP3.1 RevenueInsight and PipelineMetric entity foundation tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
I18N = MODULE / "Resources" / "i18n"

REVENUE_INSIGHT = "RevenueInsight"
PIPELINE_METRIC = "PipelineMetric"

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

FORBIDDEN_FIELDS = {
    "Opportunity",
    "OpportunityId",
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
    "ExecutionStatus",
    "executionStatus",
    "ActionGate",
    "actionGate",
    "ExecutionLedger",
    "executionLedger",
    "workflowTrigger",
    "automationAction",
    "decisionAuthority",
    "revenueCommitment",
    "aiDecision",
    "autoApprove",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entity_paths(entity: str) -> dict[str, Path]:
    return {
        "class": MODULE / "Entities" / f"{entity}.php",
        "defs": METADATA / "entityDefs" / f"{entity}.json",
        "scope": METADATA / "scopes" / f"{entity}.json",
        "acl": METADATA / "aclDefs" / f"{entity}.json",
        "i18n_en": I18N / "en_US" / f"{entity}.json",
        "i18n_zh": I18N / "zh_CN" / f"{entity}.json",
    }


def foundation_blob() -> str:
    parts: list[str] = []
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        paths = entity_paths(entity)
        for path in paths.values():
            parts.append(path.read_text(encoding="utf-8"))
    parts.append((METADATA / "app" / "acl.json").read_text(encoding="utf-8"))
    parts.append((METADATA / "app" / "aclPortal.json").read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_entity_files_exist() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        paths = entity_paths(entity)
        for path in paths.values():
            assert path.is_file(), path
        source = paths["class"].read_text(encoding="utf-8")
        assert f"final class {entity}" in source
        assert f"ENTITY_TYPE = '{entity}'" in source


def test_metadata_json_valid() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        paths = entity_paths(entity)
        defs = load_json(paths["defs"])
        scope = load_json(paths["scope"])
        acl = load_json(paths["acl"])
        assert isinstance(defs["fields"], dict)
        assert scope["entity"] is True
        assert scope["acl"] is True
        assert scope["aclPortal"] is False
        assert scope["module"] == "Prospecting"
        assert acl == {}
        load_json(paths["i18n_en"])
        load_json(paths["i18n_zh"])


def test_allowed_fields_exist() -> None:
    revenue = load_json(entity_paths(REVENUE_INSIGHT)["defs"])
    pipeline = load_json(entity_paths(PIPELINE_METRIC)["defs"])
    assert set(revenue["fields"]) == REVENUE_ALLOWED
    assert set(pipeline["fields"]) == PIPELINE_ALLOWED
    assert all(field.get("readOnly") for field in revenue["fields"].values())
    assert all(field.get("readOnly") for field in pipeline["fields"].values())
    review = revenue["fields"]["reviewStatus"]
    assert review["default"] == "GENERATED"
    assert review["options"] == ["GENERATED", "REVIEWED", "ACCEPTED", "REJECTED"]
    assert load_json(entity_paths(REVENUE_INSIGHT)["scope"])["statusField"] == "reviewStatus"


def test_forbidden_fields_absent() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        fields = set(load_json(entity_paths(entity)["defs"])["fields"])
        assert not fields & FORBIDDEN_FIELDS


def test_no_relationships() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        definition = load_json(entity_paths(entity)["defs"])
        assert "links" not in definition
        assert "relationships" not in definition


def test_no_crm_core_references() -> None:
    blob = foundation_blob()
    for value in (
        '"entity": "Opportunity"',
        '"entity": "Lead"',
        '"entity": "Account"',
        '"entity": "Contact"',
        "use Espo\\Entities\\Opportunity",
        "use Espo\\Entities\\Lead",
    ):
        assert value not in blob, value


def test_no_c20_provider_references() -> None:
    blob = foundation_blob().lower()
    for token in ("provider", "credential", "sdk", "guzzle", "curl", "httpclient", "secret"):
        assert token not in blob, token
    assert not re.search(r"(?i)https?://", foundation_blob())


def test_no_c22_execution_references() -> None:
    blob = foundation_blob()
    for value in (
        '"entity": "ActionGate"',
        '"entity": "ExecutionLedger"',
        '"entity": "ProspectRun"',
        "ActionGateService",
        "ExecutionLedgerService",
    ):
        assert value not in blob, value


def test_no_c23_metric_duplication() -> None:
    revenue_source = entity_paths(REVENUE_INSIGHT)["class"].read_text(encoding="utf-8")
    pipeline_source = entity_paths(PIPELINE_METRIC)["class"].read_text(encoding="utf-8")
    revenue_defs = load_json(entity_paths(REVENUE_INSIGHT)["defs"])
    pipeline_defs = load_json(entity_paths(PIPELINE_METRIC)["defs"])
    performance_defs = load_json(METADATA / "entityDefs" / "PerformanceMetric.json")
    optimization_defs = load_json(METADATA / "entityDefs" / "OptimizationInsight.json")

    assert "ENTITY_TYPE = 'PipelineMetric'" in pipeline_source
    assert "ENTITY_TYPE = 'RevenueInsight'" in revenue_source
    assert "ENTITY_TYPE = 'PerformanceMetric'" not in pipeline_source
    assert "ENTITY_TYPE = 'OptimizationInsight'" not in revenue_source
    assert set(pipeline_defs["fields"]) != set(performance_defs["fields"])
    assert set(revenue_defs["fields"]) != set(optimization_defs["fields"])
    assert "metricName" in pipeline_defs["fields"]
    assert "metricValue" not in pipeline_defs["fields"]
    assert "value" in pipeline_defs["fields"]
    assert "aggregationPeriod" not in pipeline_defs["fields"]
    assert "reviewStatus" in revenue_defs["fields"]
    assert "insightSummary" in revenue_defs["fields"]
    assert "optimizationStatus" not in revenue_defs["fields"]


def test_inventory_updated() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    assert 'Entities" / "RevenueInsight.php"' in inventory
    assert 'Entities" / "PipelineMetric.php"' in inventory
    assert 'scopes" / "RevenueInsight.json"' in inventory
    assert 'scopes" / "PipelineMetric.json"' in inventory


def test_acl_portal_disabled_and_internal_governance_access() -> None:
    acl = load_json(METADATA / "app" / "acl.json")
    portal = load_json(METADATA / "app" / "aclPortal.json")
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        assert acl["mandatory"]["scopeLevel"][entity] is False
        assert portal["mandatory"]["scopeLevel"][entity] is False
        rights = acl["adminMandatory"]["scopeLevel"][entity]
        assert rights == {
            "create": "yes",
            "read": "all",
            "edit": "no",
            "delete": "no",
        }


def test_static_security_scan() -> None:
    blob = foundation_blob().lower()
    forbidden = (
        "http",
        "curl",
        "guzzle",
        "sdk",
        "provider",
        "credential",
        "secret",
        "worker",
        "scheduler",
        "queue",
        "workflow",
        "automation",
    )
    for token in forbidden:
        assert token not in blob, token
    assert not (MODULE / "Services" / "RevenueInsightLifecycleService.php").exists()
    assert not (MODULE / "Services" / "PipelineMetricIntegrityService.php").exists()
