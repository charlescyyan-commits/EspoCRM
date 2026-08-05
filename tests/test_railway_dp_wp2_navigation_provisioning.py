"""Focused unit tests for the DP-WP2 navigation_provisioning adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_phase_adapter_contract as contract
from scripts.dp_wp2_phase_adapters import navigation_provisioning as navigation

ROOT = Path(__file__).resolve().parent.parent
DEFINITION = ROOT / "deployment" / "navigation" / "phase3c17_navigation.json"


def release_identity() -> foundation.ReleaseIdentity:
    return foundation.ReleaseIdentity(
        "Chitu Prospecting Integration",
        "1.9.13-alpha",
        "9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649",
        "6ef712134f581a12a18da5c98691884e73388b78",
    )


def dependency(
    identity: foundation.ReleaseIdentity | None = None,
    *,
    registered: bool = True,
    modules: frozenset[str] | None = None,
    ledger_state: str = "REGISTERED",
) -> navigation.NavigationDependencyEvidence:
    return navigation.NavigationDependencyEvidence(
        installation_id="installation-nav-1",
        identity=identity or release_identity(),
        extension_registered=registered,
        available_modules=modules
        or frozenset({"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}),
        ledger_state=ledger_state,
    )


def request_for(
    identity: foundation.ReleaseIdentity | None = None,
) -> contract.PhaseAdapterInput:
    return contract.PhaseAdapterInput(
        installation_id="installation-nav-1",
        identity=identity or release_identity(),
        phase_name=navigation.PHASE_NAME,
        idempotency=navigation.navigation_idempotency_contract(),
    )


def target_items() -> list[navigation.NavigationItem]:
    document = json.loads(DEFINITION.read_text(encoding="utf-8"))
    return [navigation.normalize_navigation_item(item) for item in document["topLevelOrder"]]


def permuted_baseline() -> list[navigation.NavigationItem]:
    items = target_items()
    # Swap two module entries after the first divider while keeping membership.
    items[2], items[3] = items[3], items[2]
    return items


def build_adapter(
    surface: navigation.InMemoryNavigationSurface,
    evidence: navigation.NavigationDependencyEvidence | None = None,
    definition_path: Path = DEFINITION,
) -> navigation.NavigationProvisioningAdapter:
    return navigation.NavigationProvisioningAdapter(
        surface,
        definition_path,
        evidence or dependency(),
    )


def test_exact_contract_match_writes_and_returns_checksum_evidence() -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    adapter = build_adapter(surface)
    phase_input = request_for()

    report = adapter.report(phase_input)
    contract.validate_phase_adapter_output(phase_input, report)

    assert report.outcome == contract.PhaseOutcome.SUCCEEDED
    assert report.postcondition.name == navigation.POSTCONDITION_NAME
    assert report.postcondition.satisfied is True
    assert report.postcondition.evidence.startswith("sha256:")
    assert report.failure is None
    assert surface.write_count == 1
    assert surface.read_top_level() == target_items()
    assert surface.business_data_touched is False
    expected = (
        "sha256:"
        + navigation.sha256_hex(navigation.canonical_json_bytes(target_items()))
    )
    assert report.postcondition.evidence == expected


def test_checksum_mismatch_fails_closed_without_write(tmp_path: Path) -> None:
    mutated = json.loads(DEFINITION.read_text(encoding="utf-8"))
    mutated["navigationVersion"] = "phase3c19-ia-v1-mutated"
    bad_path = tmp_path / "bad-navigation.json"
    bad_path.write_text(json.dumps(mutated), encoding="utf-8")

    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    adapter = build_adapter(surface, definition_path=bad_path)
    phase_input = request_for()

    report = adapter.report(phase_input)
    contract.validate_phase_adapter_output(phase_input, report)

    assert report.outcome == contract.PhaseOutcome.FAILED
    assert report.failure is not None
    assert report.failure.code == "NAVIGATION_DEFINITION_MISMATCH"
    assert "\n" not in report.failure.summary
    assert surface.write_count == 0
    assert surface.read_top_level() == permuted_baseline()


def test_idempotent_noop_when_already_at_target() -> None:
    surface = navigation.InMemoryNavigationSurface(target_items())
    adapter = build_adapter(surface)
    phase_input = request_for()

    first = adapter.report(phase_input)
    second = adapter.report(phase_input)

    assert first.outcome == contract.PhaseOutcome.SUCCEEDED
    assert second.outcome == contract.PhaseOutcome.SUCCEEDED
    assert first.postcondition.evidence == second.postcondition.evidence
    assert surface.write_count == 0


def test_failure_preservation_for_unrecognized_baseline() -> None:
    surface = navigation.InMemoryNavigationSurface(["Home", "Lead", "Account"])
    adapter = build_adapter(surface)
    phase_input = request_for()

    report = adapter.report(phase_input)
    contract.validate_phase_adapter_output(phase_input, report)

    assert report.outcome == contract.PhaseOutcome.FAILED
    assert report.failure is not None
    assert report.failure.code == "NAVIGATION_BASELINE_UNRECOGNIZED"
    assert report.postcondition.satisfied is False
    assert surface.write_count == 0


def test_no_business_data_mutation_on_success_or_failure() -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    adapter = build_adapter(surface)

    adapter.report(request_for())
    assert surface.business_data_touched is False

    surface_fail = navigation.InMemoryNavigationSurface(["Home"])
    build_adapter(surface_fail).report(request_for())
    assert surface_fail.business_data_touched is False
    assert surface_fail.write_count == 0


def test_report_only_behavior_has_no_lifecycle_authority() -> None:
    adapter = build_adapter(navigation.InMemoryNavigationSurface(target_items()))
    assert not hasattr(adapter, "record_phase")
    assert not hasattr(adapter, "mark_failure")
    assert not hasattr(adapter, "mark_completion")
    assert not hasattr(adapter, "transition")

    report = adapter.report(request_for())
    assert report.outcome == contract.PhaseOutcome.SUCCEEDED
    assert "HOOK_PENDING" not in report.postcondition.evidence
    assert "REGISTERED" not in report.postcondition.evidence


def test_dependency_unavailable_fails_closed() -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    adapter = build_adapter(
        surface,
        evidence=dependency(registered=False),
    )
    report = adapter.report(request_for())
    assert report.outcome == contract.PhaseOutcome.FAILED
    assert report.failure is not None
    assert report.failure.code == "NAVIGATION_DEPENDENCY_UNAVAILABLE"
    assert surface.write_count == 0


def test_wrong_idempotency_key_is_definition_mismatch() -> None:
    surface = navigation.InMemoryNavigationSurface(target_items())
    adapter = build_adapter(surface)
    phase_input = contract.PhaseAdapterInput(
        installation_id="installation-nav-1",
        identity=release_identity(),
        phase_name=navigation.PHASE_NAME,
        idempotency=contract.IdempotencyContract(
            key="navigation:wrong",
            mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
        ),
    )
    report = adapter.report(phase_input)
    assert report.failure is not None
    assert report.failure.code == "NAVIGATION_DEFINITION_MISMATCH"
    assert surface.write_count == 0
