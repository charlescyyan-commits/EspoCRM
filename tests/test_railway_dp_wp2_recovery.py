"""Focused DP-WP2 Stage-1 recovery and durability boundary tests."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_ledger_interaction as interaction
from scripts import dp_wp2_phase_adapter_contract as contract
from scripts import dp_wp2_provisioning_orchestrator as orchestrator


def identity() -> foundation.ReleaseIdentity:
    return foundation.ReleaseIdentity("Chitu", "1.0.0", "a" * 64, "b" * 40)


def invocation(
    resume_postcondition: contract.PhasePostcondition | None = None,
) -> orchestrator.ProvisioningInvocation:
    return orchestrator.ProvisioningInvocation(
        identity=identity(),
        phase_name="contract-only-phase",
        idempotency=contract.IdempotencyContract(
            key="contract-only-phase:v1",
            mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
        ),
        target_phase=foundation.InstallationState.REGISTERED,
        resume_postcondition=resume_postcondition,
    )


def test_corrupt_durable_ledger_fails_closed_before_orchestration(tmp_path) -> None:
    storage_path = tmp_path / "ledger.json"
    storage_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(foundation.LedgerCorruptionError):
        foundation.JsonFileInstallationLedger(storage_path)


def test_lock_scoped_reload_corruption_returns_a_redacted_hard_stop(tmp_path) -> None:
    storage_path = tmp_path / "ledger.json"
    ledger = foundation.JsonFileInstallationLedger(storage_path)
    storage_path.write_text("not-json", encoding="utf-8")
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )

    result = runner.invoke(invocation())

    assert result.failure_code == "LEDGER_CORRUPT"
    assert result.state is None
    assert result.adapter_invoked is False


def test_lock_contention_returns_a_redacted_hard_stop(tmp_path) -> None:
    storage_path = tmp_path / "ledger.json"
    first = foundation.JsonFileInstallationLedger(storage_path)
    first.acquire_lock()
    try:
        second = foundation.JsonFileInstallationLedger(storage_path)
        runner = orchestrator.ProvisioningOrchestrator(
            interaction.ProvisioningLedgerInteraction(second)
        )
        result = runner.invoke(invocation())
    finally:
        first.release_lock()

    assert result.failure_code == "LEDGER_LOCK_UNAVAILABLE"
    assert result.state is None


def test_resume_rejects_a_caller_only_postcondition_claim_and_maps_to_failed(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.READY)
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.INSTALLING)

    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )
    result = runner.invoke(
        invocation(
            contract.PhasePostcondition(
                name="caller-only", satisfied=True, evidence="caller supplied assertion"
            )
        )
    )

    assert result.recovery_disposition == foundation.RecoveryDisposition.RESUME
    assert result.state == foundation.InstallationState.FAILED
    assert result.failure_code == "RESUME_POSTCONDITION_UNVERIFIED"


def test_resume_accepts_only_a_postcondition_bound_to_durable_step_evidence(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    postcondition = contract.PhasePostcondition(
        name="resume-check", satisfied=True, evidence="synthetic-revalidation"
    )
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.READY)
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.INSTALLING
        )
        setup.record_step_result(
            release_identity,
            record.installation_id,
            "adapter:contract-only-phase:postcondition:resume-check",
            "succeeded",
        )

    report_adapter = Mock()
    report_adapter.report.side_effect = lambda request: contract.PhaseAdapterOutput(
        installation_id=request.installation_id,
        identity=request.identity,
        phase_name=request.phase_name,
        idempotency=request.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=postcondition,
    )
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {"contract-only-phase": report_adapter},
    )

    result = runner.invoke(invocation(postcondition))

    assert result.recovery_disposition == foundation.RecoveryDisposition.RESUME
    assert result.admission_kind == orchestrator.AdmissionKind.RESUME
    assert result.state == foundation.InstallationState.REGISTERED


def test_generic_resume_from_registered_without_navigation_evidence_still_requires_step(
    tmp_path,
) -> None:
    """Non-navigation REGISTERED resume remains evidence-bound (not first admission)."""

    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.READY)
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.INSTALLING
        )
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.REGISTERED
        )

    adapter = Mock()
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {"contract-only-phase": adapter},
    )
    result = runner.invoke(invocation())

    assert result.recovery_disposition == foundation.RecoveryDisposition.RESUME
    assert result.admission_kind == orchestrator.AdmissionKind.RESUME
    assert result.failure_code == "RESUME_POSTCONDITION_UNVERIFIED"
    assert result.state == foundation.InstallationState.FAILED
    adapter.report.assert_not_called()


def test_failed_preserved_recovery_performs_no_new_mutation(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        setup.mark_failure(
            release_identity,
            record.installation_id,
            "SYNTHETIC_FAILURE: preserved for recovery test",
            foundation.InstallationState.PRECHECK_FAILED,
        )

    before = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )
    result = runner.invoke(invocation())
    after = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)

    assert result.recovery_disposition == foundation.RecoveryDisposition.FAILED_PRESERVED
    assert result.failure_code == "FAILED_PRESERVED"
    assert result.adapter_invoked is False
    assert before.record is not None and after.record is not None
    assert after.record.events == before.record.events


def test_baseline_recovery_admission_after_failed_navigation_and_successful_baseline(
    tmp_path,
) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        for phase in (
            foundation.InstallationState.READY,
            foundation.InstallationState.INSTALLING,
            foundation.InstallationState.REGISTERED,
        ):
            setup.record_phase(release_identity, record.installation_id, phase)
        setup.record_step_result(
            release_identity,
            record.installation_id,
            "adapter:navigation_provisioning:postcondition:navigation_state_matches_definition",
            "failed",
        )
        setup.mark_failure(
            release_identity,
            record.installation_id,
            "NAVIGATION_BASELINE_UNRECOGNIZED: preserved for recovery admission test",
            foundation.InstallationState.FAILED,
        )
        setup.record_step_result(
            release_identity,
            record.installation_id,
            orchestrator.BASELINE_STEP_ID,
            "succeeded",
        )
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.READY)
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.INSTALLING
        )
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.REGISTERED
        )
        installation_id = record.installation_id

    adapter = Mock()
    adapter.report.side_effect = lambda request: contract.PhaseAdapterOutput(
        installation_id=request.installation_id,
        identity=request.identity,
        phase_name=request.phase_name,
        idempotency=request.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=contract.PhasePostcondition(
            name="navigation_state_matches_definition",
            satisfied=True,
            evidence="sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0",
        ),
    )
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {orchestrator.NAVIGATION_PROVISIONING_PHASE: adapter},
    )
    result = runner.invoke(
        orchestrator.ProvisioningInvocation(
            identity=release_identity,
            phase_name=orchestrator.NAVIGATION_PROVISIONING_PHASE,
            idempotency=contract.IdempotencyContract(
                key="navigation:phase3c19-ia-v1:bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6",
                mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
            ),
            target_phase=foundation.InstallationState.HOOK_PENDING,
            dependency_evidence=orchestrator.RuntimeDependencyEvidence(
                installation_id=installation_id,
                identity=release_identity,
                extension_registered=True,
                available_modules=frozenset(
                    {"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}
                ),
            ),
        )
    )

    assert result.admission_kind == orchestrator.AdmissionKind.BASELINE_RECOVERY_ADMISSION
    assert result.adapter_invoked is True
    assert result.state == foundation.InstallationState.HOOK_PENDING
    assert result.failure_code is None


def test_empty_registry_at_registered_first_admission_candidate_fails_closed(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        setup.record_phase(release_identity, record.installation_id, foundation.InstallationState.READY)
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.INSTALLING
        )
        setup.record_phase(
            release_identity, record.installation_id, foundation.InstallationState.REGISTERED
        )
        installation_id = record.installation_id

    evidence = orchestrator.RuntimeDependencyEvidence(
        installation_id=installation_id,
        identity=release_identity,
        extension_registered=True,
        available_modules=frozenset(
            {"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}
        ),
    )
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )
    result = runner.invoke(
        orchestrator.ProvisioningInvocation(
            identity=release_identity,
            phase_name=orchestrator.NAVIGATION_PROVISIONING_PHASE,
            idempotency=contract.IdempotencyContract(
                key="navigation_provisioning:v1",
                mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
            ),
            target_phase=foundation.InstallationState.HOOK_PENDING,
            dependency_evidence=evidence,
        )
    )

    assert result.adapter_invoked is False
    assert result.failure_code == "ADAPTER_REGISTRY_EMPTY"
    assert result.state == foundation.InstallationState.FAILED
    recovered = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)
    assert recovered.disposition == foundation.RecoveryDisposition.FAILED_PRESERVED
