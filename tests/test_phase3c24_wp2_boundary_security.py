"""Phase3C24 WP2.4 immutable and boundary-security tests."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
ENTITY = "OpportunityCandidate"

IMMUTABLE_GUARD = MODULE / "Hooks" / ENTITY / "OpportunityCandidateImmutableGuard.php"
LIFECYCLE_GUARD = MODULE / "Hooks" / ENTITY / "OpportunityCandidateLifecycleGuard.php"
LIFECYCLE_SERVICE = MODULE / "Services" / "OpportunityCandidateLifecycleService.php"
SAVE_OPTION = MODULE / "Services" / "C24OpportunityCandidateSaveOption.php"
ENTITY_CLASS = MODULE / "Entities" / "OpportunityCandidate.php"
WP2_PHP = [
    ENTITY_CLASS,
    LIFECYCLE_SERVICE,
    SAVE_OPTION,
    IMMUTABLE_GUARD,
    LIFECYCLE_GUARD,
]


def wp2_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP2_PHP)


def test_immutable_guard_exists_before_lifecycle_guard() -> None:
    assert IMMUTABLE_GUARD.is_file()
    source = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    assert "final class OpportunityCandidateImmutableGuard" in source
    assert "public static int $order = 1000" in source
    assert "public static int $order = 1010" in LIFECYCLE_GUARD.read_text(encoding="utf-8")


def test_immutable_field_modification_is_blocked_after_creation() -> None:
    source = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    for field in (
        "provenanceReference",
        "outcomeReference",
        "outcomeRecordedAt",
    ):
        assert f"'{field}'" in source
        assert f"field {{$field}} is immutable" in source
    assert "isAttributeChanged($field)" in source


def test_lifecycle_audit_changes_require_the_lifecycle_service_marker() -> None:
    source = IMMUTABLE_GUARD.read_text(encoding="utf-8")
    for field in ("transitionHistory", "lastTransitionBy", "lastTransitionAt"):
        assert f"'{field}'" in source
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in source
    assert "must use its lifecycle service" in source
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in LIFECYCLE_SERVICE.read_text(encoding="utf-8")


def test_history_overwrite_is_blocked_and_service_append_remains_governed() -> None:
    source = LIFECYCLE_GUARD.read_text(encoding="utf-8")
    assert "count($current) !== count($previous) + 1" in source
    assert "array_slice($current, 0, count($previous)) !== $previous" in source
    assert "append one immutable record" in source
    assert "transitionHistory" in LIFECYCLE_SERVICE.read_text(encoding="utf-8")


def test_no_c21_c22_c23_wp1_or_crm_access_path_exists() -> None:
    source = wp2_source()
    forbidden = (
        "AIQualificationInsight",
        "ResearchEvidence",
        "ActionGate",
        "ExecutionLedger",
        "ProspectRun",
        "OptimizationInsight",
        "PerformanceMetric",
        "FeedbackLearningObservation",
        "ReplySignal",
        "getEntity('Opportunity')",
        "getEntity('Lead')",
        "saveEntity($opportunity",
    )
    for value in forbidden:
        assert value not in source, value


def test_no_runtime_egress_or_automation_import_is_present() -> None:
    source = wp2_source().lower()
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
        "workflow",
        "automation",
    )
    for value in forbidden:
        assert value not in source, value


def test_extension_inventory_lists_immutable_guard() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    assert IMMUTABLE_GUARD.name in inventory
