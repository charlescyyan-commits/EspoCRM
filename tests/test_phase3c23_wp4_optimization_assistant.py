"""Phase3C23 WP4 optimization assistant read-only boundary tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
METADATA = MODULE / "Resources" / "metadata"
SERVICE = MODULE / "Services" / "OptimizationAssistantService.php"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source() -> str:
    return SERVICE.read_text(encoding="utf-8")


def test_assistant_service_exists() -> None:
    assert SERVICE.is_file()
    assert "final class OptimizationAssistantService" in source()


def test_public_surface_is_read_only_summary_explain_and_read() -> None:
    public_methods = set(re.findall(r"public function\s+(\w+)", source()))
    assert public_methods == {"__construct", "summarize", "explain", "read"}
    assert "checkEntityRead" in source()
    assert "checkEntityEdit" not in source()


def test_input_boundary_is_only_c23_analytical_artifacts() -> None:
    service = source()
    assert "private const INPUT_ENTITY_TYPES" in service
    for entity in (
        "OptimizationInsight",
        "PerformanceMetric",
        "FeedbackLearningObservation",
    ):
        assert f"'{entity}'" in service
    assert "assertInputEntityType" in service
    assert "->order('createdAt', 'desc')" in service


def test_assistant_never_writes_or_changes_lifecycle() -> None:
    service = source()
    for forbidden in (
        "saveEntity",
        "getNewEntity",
        "->set(",
        "OptimizationInsightReviewService",
        "C23OptimizationInsightLifecycleSaveOption",
        "LIFECYCLE_MUTATION_AUTHORIZED",
    ):
        assert forbidden not in service


def test_no_c21_access_or_qualification_authority() -> None:
    service = source()
    for forbidden in (
        "AIQualificationInsight",
        "ResearchEvidence",
        "HumanFeedback",
        "qualification",
        "ranking",
        "score",
    ):
        assert forbidden.lower() not in service.lower()


def test_no_c22_access_execution_or_approval_path() -> None:
    service = source()
    for forbidden in (
        "ActionGate",
        "ProspectRun",
        "ExecutionLedger",
        "execute",
        "approve",
        "reject",
        "trigger",
        "workflow",
    ):
        assert forbidden.lower() not in service.lower()


def test_output_is_explicitly_advisory_only() -> None:
    service = source()
    assert "human review only" in service.lower()
    assert "does not authorize an operational change" in service.lower()
    assert "No operational action follows" in service


def test_no_egress_provider_or_automation_runtime() -> None:
    lowered = source().lower()
    forbidden = (
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "http://",
        "https://",
        "sdk",
        "provider",
        "credential",
        "secret",
        "api key",
        "access token",
        "apify",
        "apollo",
        "hunter",
        "deepseek",
        "openai",
        "instantly",
        "brevo",
        "smtp",
        "worker",
        "scheduler",
        "queue",
        "automation",
    )
    for value in forbidden:
        assert value not in lowered, value


def test_source_scopes_remain_portal_disabled_and_read_governed() -> None:
    app_acl = load_json(METADATA / "app" / "acl.json")
    portal_acl = load_json(METADATA / "app" / "aclPortal.json")
    for entity in (
        "OptimizationInsight",
        "PerformanceMetric",
        "FeedbackLearningObservation",
    ):
        scope = load_json(METADATA / "scopes" / f"{entity}.json")
        assert scope["acl"] is True
        assert scope["aclPortal"] is False
        assert portal_acl["mandatory"]["scopeLevel"][entity] is False
        assert app_acl["adminMandatory"]["scopeLevel"][entity]["read"] == "all"


def test_extension_inventory_registers_assistant_service() -> None:
    inventory = (
        EXT / "tests" / "test_extension_skeleton.py"
    ).read_text(encoding="utf-8")
    assert SERVICE.name in inventory
