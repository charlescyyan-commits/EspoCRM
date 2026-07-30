"""Phase3C24 WP2.3 OpportunityCandidate lifecycle governance tests."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "crm-extension"
MODULE = EXT / "files" / "custom" / "Espo" / "Modules" / "Prospecting"
ENTITY = "OpportunityCandidate"

SERVICE = MODULE / "Services" / "OpportunityCandidateLifecycleService.php"
SAVE_OPTION = MODULE / "Services" / "C24OpportunityCandidateSaveOption.php"
GUARD = MODULE / "Hooks" / ENTITY / "OpportunityCandidateLifecycleGuard.php"
WP23_PHP = [SERVICE, SAVE_OPTION, GUARD]


def wp23_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WP23_PHP)


def test_lifecycle_artifacts_exist() -> None:
    for path in WP23_PHP:
        assert path.is_file(), path
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in SAVE_OPTION.read_text(encoding="utf-8")


def test_every_valid_transition_has_a_human_service_entrypoint() -> None:
    source = SERVICE.read_text(encoding="utf-8")
    expected = {
        "submitForReview": ("STATUS_IDENTIFIED", "STATUS_REVIEW_PENDING"),
        "accept": ("STATUS_REVIEW_PENDING", "STATUS_ACCEPTED"),
        "reject": ("STATUS_REVIEW_PENDING", "STATUS_REJECTED"),
        "activate": ("STATUS_ACCEPTED", "STATUS_ACTIVE"),
        "recordWon": ("STATUS_ACTIVE", "STATUS_WON"),
        "recordLost": ("STATUS_ACTIVE", "STATUS_LOST"),
    }
    for method, (from_status, to_status) in expected.items():
        match = re.search(
            rf"public function {method}\b(?P<body>.*?)(?=\n    public function|\n    private function)",
            source,
            re.DOTALL,
        )
        assert match, method
        assert from_status in match.group("body")
        assert to_status in match.group("body")


def test_invalid_and_terminal_transitions_are_rejected() -> None:
    source = GUARD.read_text(encoding="utf-8")
    for transition in (
        "'IDENTIFIED' => ['REVIEW_PENDING']",
        "'REVIEW_PENDING' => ['ACCEPTED', 'REJECTED']",
        "'ACCEPTED' => ['ACTIVE']",
        "'ACTIVE' => ['WON', 'LOST']",
        "'WON' => []",
        "'LOST' => []",
        "'REJECTED' => []",
    ):
        assert transition in source
    assert "transition {$from} to {$to} is forbidden" in source


def test_direct_status_or_history_mutation_is_rejected() -> None:
    source = GUARD.read_text(encoding="utf-8")
    assert "LIFECYCLE_TRANSITION_AUTHORIZED" in source
    assert "must use its lifecycle service" in source
    for field in ("status", "transitionHistory", "lastTransitionBy", "lastTransitionAt"):
        assert f"'{field}'" in source


def test_human_actor_timestamp_and_reason_are_required() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    guard = GUARD.read_text(encoding="utf-8")
    assert "authenticated human actor" in service
    assert "transition requires a reason" in service
    assert "DateTimeImmutable" in service
    for field in ("actorReference", "transitionedAt", "transitionReason"):
        assert f"'{field}'" in service
        assert f"'{field}'" in guard
    assert "human audit provenance" in guard


def test_transition_history_is_append_only_and_previous_records_are_preserved() -> None:
    source = GUARD.read_text(encoding="utf-8")
    assert "count($current) !== count($previous) + 1" in source
    assert "array_slice($current, 0, count($previous)) !== $previous" in source
    assert "append one immutable record" in source
    assert "array_key_last($current)" in source


def test_no_c21_c22_c23_or_crm_mutation_path_exists() -> None:
    source = wp23_source()
    forbidden = (
        "AIQualificationInsight",
        "ActionGate",
        "ExecutionLedger",
        "PerformanceMetric",
        "OptimizationInsight",
        "ReplySignal",
        "getEntity('Opportunity')",
        "saveEntity($opportunity",
    )
    for value in forbidden:
        assert value not in source, value


def test_no_runtime_egress_or_automation_surface_exists() -> None:
    source = wp23_source().lower()
    forbidden = (
        "curl",
        "guzzlehttp",
        "file_get_contents",
        "httpclient",
        "sdk",
        "provider",
        "credential",
        "secret",
        "scheduler",
        "queue",
        "worker",
        "workflow",
        "automation",
    )
    for value in forbidden:
        assert value not in source, value


def test_extension_inventory_lists_each_wp23_php_file() -> None:
    inventory = (EXT / "tests" / "test_extension_skeleton.py").read_text(encoding="utf-8")
    for path in WP23_PHP:
        assert path.name in inventory
