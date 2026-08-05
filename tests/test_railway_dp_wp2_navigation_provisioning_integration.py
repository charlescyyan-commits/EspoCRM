"""Integration tests for navigation_provisioning through the Stage-1 orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_ledger_interaction as interaction
from scripts import dp_wp2_phase_adapter_contract as contract
from scripts import dp_wp2_provisioning_orchestrator as orchestrator
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


def target_items() -> list[navigation.NavigationItem]:
    document = json.loads(DEFINITION.read_text(encoding="utf-8"))
    return [navigation.normalize_navigation_item(item) for item in document["topLevelOrder"]]


def permuted_baseline() -> list[navigation.NavigationItem]:
    items = target_items()
    items[2], items[3] = items[3], items[2]
    return items


def seed_registered_ledger(
    ledger: foundation.JsonFileInstallationLedger,
    identity: foundation.ReleaseIdentity,
    *,
    admit_resume: bool = True,
) -> str:
    """Seed a REGISTERED record.

    Stage-1 treats REGISTERED as RESUME and requires a validated resume
    postcondition before any adapter call. When admit_resume is true, seed the
    durable navigation step marker so the orchestrator may invoke the adapter.
    """

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.create_installation(identity)
        for phase in (
            foundation.InstallationState.READY,
            foundation.InstallationState.INSTALLING,
            foundation.InstallationState.REGISTERED,
        ):
            layer.record_phase(identity, record.installation_id, phase)
        if admit_resume:
            layer.record_step_result(
                identity,
                record.installation_id,
                navigation.DURABLE_STEP_ID,
                "succeeded",
            )
        return record.installation_id


def resume_postcondition() -> contract.PhasePostcondition:
    return contract.PhasePostcondition(
        name=navigation.POSTCONDITION_NAME,
        satisfied=True,
        evidence="sha256:resume-admitted",
    )


def build_stack(
    tmp_path: Path,
    surface: navigation.InMemoryNavigationSurface,
    *,
    registered: bool = True,
    admit_resume: bool = True,
    definition_path: Path = DEFINITION,
):
    identity = release_identity()
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "installation-ledger.json")
    installation_id = seed_registered_ledger(
        ledger, identity, admit_resume=admit_resume
    )
    evidence = navigation.NavigationDependencyEvidence(
        installation_id=installation_id,
        identity=identity,
        extension_registered=registered,
        available_modules=frozenset(
            {"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}
        ),
        ledger_state="REGISTERED",
    )
    adapter = navigation.NavigationProvisioningAdapter(
        surface, definition_path, evidence
    )
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    orch = orchestrator.ProvisioningOrchestrator(
        layer,
        adapters={navigation.PHASE_NAME: adapter},
    )
    return identity, ledger, orch, installation_id


def invocation_for(
    identity: foundation.ReleaseIdentity,
    *,
    with_resume: bool = True,
) -> orchestrator.ProvisioningInvocation:
    return orchestrator.ProvisioningInvocation(
        identity=identity,
        phase_name=navigation.PHASE_NAME,
        idempotency=navigation.navigation_idempotency_contract(),
        target_phase=foundation.InstallationState.HOOK_PENDING,
        resume_postcondition=resume_postcondition() if with_resume else None,
    )


def test_integration_exact_match_records_step_and_transitions_to_hook_pending(
    tmp_path: Path,
) -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    identity, ledger, orch, installation_id = build_stack(tmp_path, surface)

    result = orch.invoke(invocation_for(identity))

    assert result.adapter_invoked is True
    assert result.failure_code is None
    assert result.state == foundation.InstallationState.HOOK_PENDING
    assert result.installation_id == installation_id
    assert surface.write_count == 1
    assert surface.read_top_level() == target_items()
    assert surface.business_data_touched is False

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity).record
        assert record is not None
        assert record.state == foundation.InstallationState.HOOK_PENDING
        assert any(
            event.kind == "step"
            and event.value == navigation.DURABLE_STEP_ID
            and event.outcome == "succeeded"
            for event in record.events
        )


def test_integration_checksum_mismatch_preserves_failure(tmp_path: Path) -> None:
    mutated = json.loads(DEFINITION.read_text(encoding="utf-8"))
    mutated["navigationVersion"] = "bad-version"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(mutated), encoding="utf-8")

    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    identity, ledger, orch, _installation_id = build_stack(
        tmp_path, surface, definition_path=bad
    )

    result = orch.invoke(invocation_for(identity))

    assert result.adapter_invoked is True
    assert result.failure_code == "NAVIGATION_DEFINITION_MISMATCH"
    assert result.state == foundation.InstallationState.FAILED
    assert surface.write_count == 0

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        recovery = layer.recover(identity)
        assert recovery.disposition == foundation.RecoveryDisposition.FAILED_PRESERVED
        assert recovery.record is not None
        assert any(
            event.kind == "step"
            and event.value == navigation.DURABLE_STEP_ID
            and event.outcome == "failed"
            for event in recovery.record.events
        )


def test_integration_idempotent_noop_does_not_rewrite(tmp_path: Path) -> None:
    surface = navigation.InMemoryNavigationSurface(target_items())
    identity, ledger, orch, _installation_id = build_stack(tmp_path, surface)

    first = orch.invoke(invocation_for(identity))

    assert first.state == foundation.InstallationState.HOOK_PENDING
    assert surface.write_count == 0

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity).record
        assert record is not None
        assert any(
            event.kind == "step"
            and event.value == navigation.DURABLE_STEP_ID
            and event.outcome == "succeeded"
            for event in record.events
        )


def test_integration_report_only_adapter_cannot_be_used_to_mutate_business_data(
    tmp_path: Path,
) -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    identity, _ledger, orch, _installation_id = build_stack(tmp_path, surface)

    orch.invoke(invocation_for(identity))

    assert surface.business_data_touched is False
    for item in surface.read_top_level():
        if isinstance(item, str):
            assert item.isidentifier() or item[0].isupper()
        else:
            assert set(item) <= {"type", "id", "text"}
            assert "password" not in item and "credential" not in item


def test_integration_dependency_gap_fails_without_transition(tmp_path: Path) -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    identity, ledger, orch, _installation_id = build_stack(
        tmp_path, surface, registered=False
    )

    result = orch.invoke(invocation_for(identity))

    assert result.failure_code == "NAVIGATION_DEPENDENCY_UNAVAILABLE"
    assert result.state == foundation.InstallationState.FAILED
    assert surface.write_count == 0

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        assert (
            layer.recover(identity).disposition
            == foundation.RecoveryDisposition.FAILED_PRESERVED
        )


def test_integration_registered_without_resume_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    surface = navigation.InMemoryNavigationSurface(permuted_baseline())
    identity, _ledger, orch, _installation_id = build_stack(
        tmp_path, surface, admit_resume=False
    )

    result = orch.invoke(invocation_for(identity, with_resume=False))

    assert result.adapter_invoked is False
    assert result.failure_code == "RESUME_POSTCONDITION_UNVERIFIED"
    assert result.state == foundation.InstallationState.FAILED
    assert surface.write_count == 0
