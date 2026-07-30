from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "crm-extension" / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
REVENUE_INSIGHT_SERVICE = MODULE / "Services" / "RevenueInsightService.php"
PIPELINE_METRIC_SERVICE = MODULE / "Services" / "PipelineMetricService.php"
SERVICE_FILES = (REVENUE_INSIGHT_SERVICE, PIPELINE_METRIC_SERVICE)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_governance_services_exist_and_remain_read_only():
    revenue_source = read(REVENUE_INSIGHT_SERVICE)
    metric_source = read(PIPELINE_METRIC_SERVICE)

    assert "final class RevenueInsightService" in revenue_source
    assert "final class PipelineMetricService" in metric_source

    for source in (revenue_source, metric_source):
        assert "EntityManager" not in source
        assert "saveEntity" not in source
        assert "getEntity" not in source
        assert "set(" not in source


def test_revenue_insight_service_assembles_advisory_context_with_provenance_and_freshness():
    source = read(REVENUE_INSIGHT_SERVICE)

    for method in (
        "assembleContext",
        "validateProvenance",
        "evaluateFreshness",
        "prepareAdvisorySummary",
    ):
        assert f"function {method}" in source

    for field in ("sourceReference", "provenance", "metricReferences", "insightSummary"):
        assert field in source

    for status in ("CURRENT", "fresh", "stale", "unknown"):
        assert status in source


def test_pipeline_metric_service_validates_provenance_and_aggregates_descriptively():
    source = read(PIPELINE_METRIC_SERVICE)

    for method in ("validateMetric", "validateProvenance", "evaluateFreshness", "aggregate"):
        assert f"function {method}" in source

    for field in (
        "metricType",
        "value",
        "unit",
        "reportingPeriod",
        "methodology",
        "provenance",
    ):
        assert field in source

    for aggregate_key in ("count", "total", "average", "freshness"):
        assert aggregate_key in source


def test_no_lifecycle_or_integrity_orchestration_service_is_introduced():
    assert not (MODULE / "Services" / "RevenueInsightLifecycleService.php").exists()
    assert not (MODULE / "Services" / "PipelineMetricIntegrityService.php").exists()


def test_services_do_not_reach_cross_layer_or_crm_ownership_paths():
    forbidden_terms = (
        "AIQualificationInsight",
        "ResearchEvidence",
        "HumanFeedback",
        "ActionGate",
        "ExecutionLedger",
        "ProspectRun",
        "SendExecution",
        "OptimizationInsight",
        "PerformanceMetric",
        "FeedbackLearningObservation",
        "ReplySignal",
        "OpportunityCandidate",
        "Opportunity",
        "Lead",
    )

    for path in SERVICE_FILES:
        source = read(path)
        for term in forbidden_terms:
            assert term not in source, f"{path.name} must not access {term}"


def test_services_contain_no_runtime_egress_or_automation_dependencies():
    forbidden_terms = (
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "http",
        "sdk",
        "provider",
        "credential",
        "secret",
        "worker",
        "scheduler",
        "queue",
        "webhook",
        "automation",
    )

    for path in SERVICE_FILES:
        source = read(path).lower()
        for term in forbidden_terms:
            assert term not in source, f"{path.name} must not contain {term}"


def test_extension_inventory_includes_only_the_wp3_service_additions():
    inventory = read(ROOT / "crm-extension" / "tests" / "test_extension_skeleton.py")

    assert 'MODULE / "Services" / "RevenueInsightService.php"' in inventory
    assert 'MODULE / "Services" / "PipelineMetricService.php"' in inventory
