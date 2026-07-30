"""Phase3C24 WP3.3 governance guard and save-option tests."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"

REVENUE_OPTION = MODULE / "Services" / "C24RevenueInsightSaveOption.php"
REVENUE_IMMUTABLE = MODULE / "Hooks" / "RevenueInsight" / "RevenueInsightImmutableGuard.php"
REVENUE_LIFECYCLE = MODULE / "Hooks" / "RevenueInsight" / "RevenueInsightLifecycleGuard.php"
PIPELINE_OPTION = MODULE / "Services" / "C24PipelineMetricSaveOption.php"
PIPELINE_INTEGRITY = MODULE / "Hooks" / "PipelineMetric" / "PipelineMetricIntegrityGuard.php"
WP33_PHP = [
    REVENUE_OPTION,
    REVENUE_IMMUTABLE,
    REVENUE_LIFECYCLE,
    PIPELINE_OPTION,
    PIPELINE_INTEGRITY,
]


def wp33_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP33_PHP)


def test_required_save_options_and_guards_exist() -> None:
    for path in WP33_PHP:
        assert path.is_file(), path
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in REVENUE_OPTION.read_text(encoding="utf-8")
    assert "INTEGRITY_UPDATE_AUTHORIZED" in PIPELINE_OPTION.read_text(encoding="utf-8")


def test_revenue_insight_immutable_governance_fields_are_blocked() -> None:
    source = REVENUE_IMMUTABLE.read_text(encoding="utf-8")
    for field in (
        "sourceReference",
        "provenance",
        "metricReferences",
        "reportingPeriod",
        "createdAt",
        "createdBy",
    ):
        assert f"'{field}'" in source
    assert "is immutable" in source
    assert "public static int $order = 1000" in source


def test_revenue_lifecycle_state_graph_rejects_invalid_transitions() -> None:
    source = REVENUE_LIFECYCLE.read_text(encoding="utf-8")
    for transition in (
        "'GENERATED' => ['REVIEWED']",
        "'REVIEWED' => ['ACCEPTED', 'REJECTED']",
        "'ACCEPTED' => []",
        "'REJECTED' => []",
    ):
        assert transition in source
    assert "transition {$from} to {$to} is forbidden" in source
    assert "public static int $order = 1010" in source


def test_revenue_transition_request_requires_marker_actor_reason_and_timestamp() -> None:
    source = REVENUE_LIFECYCLE.read_text(encoding="utf-8")
    for marker in (
        "LIFECYCLE_TRANSITION_AUTHORIZED",
        "LIFECYCLE_ACTOR_REFERENCE",
        "LIFECYCLE_TRANSITION_REASON",
        "LIFECYCLE_TRANSITION_TIMESTAMP",
    ):
        assert marker in source
    assert "authenticated actor" in source
    assert "transition reason" in source
    assert "requires timestamp" in source
    assert "DateTimeImmutable" in source


def test_pipeline_metric_integrity_fields_require_authorized_marker() -> None:
    source = PIPELINE_INTEGRITY.read_text(encoding="utf-8")
    for field in ("metricType", "methodology", "provenance", "reportingPeriod"):
        assert f"'{field}'" in source
    assert "INTEGRITY_UPDATE_AUTHORIZED" in source
    assert "requires authorized integrity context" in source


def test_no_lifecycle_orchestration_service_exists() -> None:
    # WP3.4 introduced advisory read-model services; lifecycle/integrity
    # orchestration services remain out of scope.
    assert (MODULE / "Services" / "RevenueInsightService.php").is_file()
    assert (MODULE / "Services" / "PipelineMetricService.php").is_file()
    assert not (MODULE / "Services" / "RevenueInsightLifecycleService.php").exists()
    assert not (MODULE / "Services" / "PipelineMetricIntegrityService.php").exists()


def test_no_c20_c21_c22_c23_or_crm_mutation_path_exists() -> None:
    source = wp33_source()
    forbidden = (
        "AIQualificationInsight",
        "ResearchEvidence",
        "ActionGate",
        "ExecutionLedger",
        "ProspectRun",
        "ReplySignal",
        "PerformanceMetric",
        "OptimizationInsight",
        "getEntity('Opportunity')",
        "getEntity('Lead')",
        "saveEntity($opportunity",
    )
    for value in forbidden:
        assert value not in source, value


def test_no_runtime_integration_or_automation_surface_exists() -> None:
    source = wp33_source().lower()
    forbidden = (
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
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
    for value in forbidden:
        assert value not in source, value


def test_extension_inventory_lists_every_wp33_php_file() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    for path in WP33_PHP:
        assert path.name in inventory
