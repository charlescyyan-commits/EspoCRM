"""Phase3C24 WP3.2 RevenueInsight and PipelineMetric metadata/ACL verification."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
I18N = MODULE / "Resources" / "i18n"
APP_ACL = METADATA / "app" / "acl.json"
PORTAL_ACL = METADATA / "app" / "aclPortal.json"

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
    "ActionGate",
    "ExecutionLedger",
    "ProspectRun",
    "PerformanceMetric",
    "OptimizationInsight",
    "ProviderCredential",
    "workflowTrigger",
    "automationAction",
    "decisionAuthority",
    "revenueCommitment",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def paths_for(entity: str) -> dict[str, Path]:
    return {
        "entity": MODULE / "Entities" / f"{entity}.php",
        "defs": METADATA / "entityDefs" / f"{entity}.json",
        "scope": METADATA / "scopes" / f"{entity}.json",
        "acl_def": METADATA / "aclDefs" / f"{entity}.json",
        "i18n_en": I18N / "en_US" / f"{entity}.json",
        "i18n_zh": I18N / "zh_CN" / f"{entity}.json",
    }


def entity_metadata_blob(entity: str) -> str:
    paths = paths_for(entity)
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            paths["entity"],
            paths["defs"],
            paths["scope"],
            paths["acl_def"],
            paths["i18n_en"],
            paths["i18n_zh"],
        )
    )


def wp3_acl_blob() -> str:
    acl = load_json(APP_ACL)
    portal = load_json(PORTAL_ACL)
    return json.dumps(
        {
            "mandatory": {
                entity: acl["mandatory"]["scopeLevel"][entity]
                for entity in (REVENUE_INSIGHT, PIPELINE_METRIC)
            },
            "adminMandatory": {
                entity: acl["adminMandatory"]["scopeLevel"][entity]
                for entity in (REVENUE_INSIGHT, PIPELINE_METRIC)
            },
            "portal": {
                entity: portal["mandatory"]["scopeLevel"][entity]
                for entity in (REVENUE_INSIGHT, PIPELINE_METRIC)
            },
        },
        sort_keys=True,
    )


def test_entitydefs_valid_json() -> None:
    for entity, allowed in (
        (REVENUE_INSIGHT, REVENUE_ALLOWED),
        (PIPELINE_METRIC, PIPELINE_ALLOWED),
    ):
        defs = load_json(paths_for(entity)["defs"])
        assert isinstance(defs, dict)
        assert isinstance(defs["fields"], dict)
        assert set(defs["fields"]) == allowed


def test_scopes_valid() -> None:
    revenue_scope = load_json(paths_for(REVENUE_INSIGHT)["scope"])
    pipeline_scope = load_json(paths_for(PIPELINE_METRIC)["scope"])

    for scope in (revenue_scope, pipeline_scope):
        assert scope["entity"] is True
        assert scope["acl"] is True
        assert scope["aclPortal"] is False
        assert scope["tab"] is False
        assert scope["object"] is False
        assert scope["customizable"] is False
        assert scope["importable"] is False
        assert scope["module"] == "Prospecting"
        assert scope["type"] == "Base"

    assert revenue_scope["statusField"] == "reviewStatus"
    assert pipeline_scope["statusField"] is None


def test_acl_definitions_valid() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        assert load_json(paths_for(entity)["acl_def"]) == {}

    acl = load_json(APP_ACL)
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        assert acl["mandatory"]["scopeLevel"][entity] is False
        rights = acl["adminMandatory"]["scopeLevel"][entity]
        assert rights["create"] == "yes"
        assert rights["read"] == "all"
        assert rights["edit"] == "no"
        assert rights["delete"] == "no"
        assert set(rights) == {"create", "read", "edit", "delete"}


def test_portal_denied() -> None:
    portal = load_json(PORTAL_ACL)
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        assert load_json(paths_for(entity)["scope"])["aclPortal"] is False
        assert portal["mandatory"]["scopeLevel"][entity] is False


def test_field_contract() -> None:
    revenue = load_json(paths_for(REVENUE_INSIGHT)["defs"])
    pipeline = load_json(paths_for(PIPELINE_METRIC)["defs"])
    assert set(revenue["fields"]) == REVENUE_ALLOWED
    assert set(pipeline["fields"]) == PIPELINE_ALLOWED
    assert all(field.get("readOnly") for field in revenue["fields"].values())
    assert all(field.get("readOnly") for field in pipeline["fields"].values())
    assert revenue["fields"]["reviewStatus"]["options"] == [
        "GENERATED",
        "REVIEWED",
        "ACCEPTED",
        "REJECTED",
    ]
    assert revenue["fields"]["reviewStatus"]["default"] == "GENERATED"
    assert pipeline["fields"]["freshnessStatus"]["options"] == [
        "CURRENT",
        "AGING",
        "STALE",
        "ARCHIVAL",
    ]


def test_forbidden_fields() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        fields = set(load_json(paths_for(entity)["defs"])["fields"])
        assert not fields & FORBIDDEN_FIELDS


def test_no_links() -> None:
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        defs = load_json(paths_for(entity)["defs"])
        assert "links" not in defs
        assert "relationships" not in defs


def test_no_crm_core_references() -> None:
    blob = "\n".join(entity_metadata_blob(entity) for entity in (REVENUE_INSIGHT, PIPELINE_METRIC))
    blob += "\n" + wp3_acl_blob()
    for value in (
        '"entity": "Opportunity"',
        '"entity": "Lead"',
        '"entity": "Account"',
        '"entity": "Contact"',
        "use Espo\\Entities\\Opportunity",
        "use Espo\\Entities\\Lead",
        "forecastCommitment",
        "revenueCommitment",
        "salesStage",
        "pipelineStage",
    ):
        assert value not in blob, value


def test_no_c20_c22_c23_coupling() -> None:
    blob = "\n".join(entity_metadata_blob(entity) for entity in (REVENUE_INSIGHT, PIPELINE_METRIC))
    blob += "\n" + wp3_acl_blob()
    forbidden = (
        '"entity": "ActionGate"',
        '"entity": "ExecutionLedger"',
        '"entity": "ProspectRun"',
        '"entity": "PerformanceMetric"',
        '"entity": "OptimizationInsight"',
        '"entity": "ProviderCredential"',
        '"entity": "AIJob"',
        "ActionGateService",
        "ExecutionLedgerService",
        "PerformanceMetricService",
        "OptimizationInsightService",
        "ProviderTypeRegistry",
    )
    for value in forbidden:
        assert value not in blob, value


def test_inventory_consistency() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    for entity in (REVENUE_INSIGHT, PIPELINE_METRIC):
        assert f'Entities" / "{entity}.php"' in inventory
        assert f'scopes" / "{entity}.json"' in inventory
        assert f'aclDefs" / "{entity}.json"' in inventory
        assert f'entityDefs" / "{entity}.json"' in inventory
        assert paths_for(entity)["entity"].is_file()
        assert paths_for(entity)["defs"].is_file()
        assert paths_for(entity)["scope"].is_file()
        assert paths_for(entity)["acl_def"].is_file()


def test_i18n_labels_and_safe_terminology() -> None:
    en_global = load_json(I18N / "en_US" / "Global.json")
    zh_global = load_json(I18N / "zh_CN" / "Global.json")
    assert en_global["scopeNames"][REVENUE_INSIGHT] == "Revenue Insight"
    assert zh_global["scopeNames"][REVENUE_INSIGHT] == "收入洞察"
    assert en_global["scopeNames"][PIPELINE_METRIC] == "Pipeline Metric"
    assert zh_global["scopeNames"][PIPELINE_METRIC] == "管道指标"
    assert set(en_global["scopeNames"]) == set(zh_global["scopeNames"])
    assert set(en_global["scopeNamesPlural"]) == set(zh_global["scopeNamesPlural"])

    for entity, allowed in (
        (REVENUE_INSIGHT, REVENUE_ALLOWED),
        (PIPELINE_METRIC, PIPELINE_ALLOWED),
    ):
        en = load_json(paths_for(entity)["i18n_en"])
        zh = load_json(paths_for(entity)["i18n_zh"])
        assert set(en["fields"]) == allowed
        assert set(zh["fields"]) == allowed
        label_blob = json.dumps(en, ensure_ascii=False) + "\n" + json.dumps(zh, ensure_ascii=False)
        assert re.search(r"(?i)forecast|revenue commitment|decision authority|workflow trigger", label_blob) is None
        assert re.search(r"(?i)provider|credential|secret|sdk", label_blob) is None


def test_boundary_artifacts_remain_advisory_only() -> None:
    revenue = entity_metadata_blob(REVENUE_INSIGHT).lower()
    pipeline = entity_metadata_blob(PIPELINE_METRIC).lower()
    for token in ("forecastcommitment", "salesstage", "pipelinestage", "commercial decision object"):
        assert token not in revenue, token
    for token in ("workflowtrigger", "automationaction", "executionsignal", "decisionauthority"):
        assert token not in pipeline, token
    assert not (MODULE / "Services" / "RevenueInsightLifecycleService.php").exists()
    assert not (MODULE / "Services" / "PipelineMetricIntegrityService.php").exists()


def test_security_scan_on_wp3_metadata() -> None:
    blob = "\n".join(entity_metadata_blob(entity) for entity in (REVENUE_INSIGHT, PIPELINE_METRIC))
    blob += "\n" + wp3_acl_blob()
    lower = blob.lower()
    forbidden = (
        "http",
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
        assert token not in lower, token
    assert not re.search(r"(?i)https?://", blob)
