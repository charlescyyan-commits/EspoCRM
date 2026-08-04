"""Focused DP-WP2 Stage-1 tests for the inert provisioning orchestrator."""

from __future__ import annotations

from unittest.mock import Mock

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_ledger_interaction as interaction
from scripts import dp_wp2_phase_adapter_contract as contract
from scripts import dp_wp2_provisioning_orchestrator as orchestrator


def identity(version: str = "1.0.0") -> foundation.ReleaseIdentity:
    return foundation.ReleaseIdentity("Chitu", version, "a" * 64, "b" * 40)


def invocation(
    release_identity: foundation.ReleaseIdentity | None = None,
    resume_postcondition: contract.PhasePostcondition | None = None,
) -> orchestrator.ProvisioningInvocation:
    return orchestrator.ProvisioningInvocation(
        identity=release_identity or identity(),
        phase_name="contract-only-phase",
        idempotency=contract.IdempotencyContract(
            key="contract-only-phase:v1",
            mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
        ),
        target_phase=foundation.InstallationState.REGISTERED,
        resume_postcondition=resume_postcondition,
    )


def test_empty_adapter_registry_fails_closed_as_precheck_failure(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )

    result = runner.invoke(invocation())

    assert result.adapter_invoked is False
    assert result.state == foundation.InstallationState.PRECHECK_FAILED
    assert result.failure_code == "ADAPTER_REGISTRY_EMPTY"
    recovered = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(identity())
    assert recovered.disposition == foundation.RecoveryDisposition.FAILED_PRESERVED
    assert recovered.record is not None
    assert recovered.record.failure_reason == (
        "ADAPTER_REGISTRY_EMPTY: no reviewed phase adapter is registered"
    )


def test_operator_block_uses_existing_precheck_and_later_failure_states(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger)
    )
    preflight = runner.invoke(
        invocation(),
        orchestrator.OperatorBlockCondition(
            orchestrator.OperatorBlockStage.PREFLIGHT,
            contract.RedactedFailure("PREFLIGHT_BLOCKED", "preflight condition is unresolved"),
        ),
    )
    assert preflight.state == foundation.InstallationState.PRECHECK_FAILED

    later_identity = identity("2.0.0")
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(later_identity)
        setup.record_phase(later_identity, record.installation_id, foundation.InstallationState.READY)
    later = runner.invoke(
        invocation(later_identity),
        orchestrator.OperatorBlockCondition(
            orchestrator.OperatorBlockStage.LATER_PHASE,
            contract.RedactedFailure("LATER_PHASE_BLOCKED", "phase condition is unresolved"),
        ),
    )
    assert later.state == foundation.InstallationState.FAILED
    assert later.failure_code == "LATER_PHASE_BLOCKED"


def test_explicit_mock_report_is_validated_before_the_governed_transition(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    adapter = Mock()
    adapter.report.side_effect = lambda request: contract.PhaseAdapterOutput(
        installation_id=request.installation_id,
        identity=request.identity,
        phase_name=request.phase_name,
        idempotency=request.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=contract.PhasePostcondition(
            name="synthetic-contract", satisfied=True, evidence="synthetic-fixture"
        ),
    )
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {"contract-only-phase": adapter},
    )

    result = runner.invoke(invocation(release_identity))

    assert result.adapter_invoked is True
    assert result.state == foundation.InstallationState.REGISTERED
    adapter.report.assert_called_once()
    persisted = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)
    assert persisted.record is not None
    assert any(
        event.kind == "step"
        and event.value == "adapter:contract-only-phase:postcondition:synthetic-contract"
        and event.outcome == "succeeded"
        for event in persisted.record.events
    )


def test_invalid_adapter_identity_report_fails_closed_without_target_transition(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    adapter = Mock()
    adapter.report.side_effect = lambda request: contract.PhaseAdapterOutput(
        installation_id=request.installation_id,
        identity=identity("2.0.0"),
        phase_name=request.phase_name,
        idempotency=request.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=contract.PhasePostcondition(
            name="synthetic-contract", satisfied=True, evidence="synthetic-fixture"
        ),
    )
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {"contract-only-phase": adapter},
    )

    result = runner.invoke(invocation())

    assert result.adapter_invoked is True
    assert result.state == foundation.InstallationState.FAILED
    assert result.failure_code == "ADAPTER_CONTRACT_INVALID"
    persisted = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(identity())
    assert persisted.record is not None
    step_index = next(
        index
        for index, event in enumerate(persisted.record.events)
        if event.kind == "step"
        and event.value == "adapter:contract-only-phase:postcondition:adapter-report"
        and event.outcome == "failed"
    )
    failure_index = next(
        index for index, event in enumerate(persisted.record.events) if event.kind == "failure"
    )
    assert step_index < failure_index


def test_completed_disposition_is_a_noop_without_adapter_or_ledger_mutation(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "ledger.json")
    release_identity = identity()
    setup = interaction.ProvisioningLedgerInteraction(ledger)
    with setup.locked():
        record = setup.create_installation(release_identity)
        for phase in (
            foundation.InstallationState.READY,
            foundation.InstallationState.INSTALLING,
            foundation.InstallationState.REGISTERED,
            foundation.InstallationState.HOOK_PENDING,
            foundation.InstallationState.MIGRATION_PENDING,
            foundation.InstallationState.METADATA_REFRESH,
        ):
            setup.record_phase(release_identity, record.installation_id, phase)
        setup.mark_completion(release_identity, record.installation_id)

    adapter = Mock()
    runner = orchestrator.ProvisioningOrchestrator(
        interaction.ProvisioningLedgerInteraction(ledger),
        {"contract-only-phase": adapter},
    )
    before = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)
    result = runner.invoke(invocation(release_identity))
    after = foundation.JsonFileInstallationLedger(ledger.storage_path).recover(release_identity)

    assert result.recovery_disposition == foundation.RecoveryDisposition.COMPLETED_NOOP
    assert result.completed_noop is True
    assert result.adapter_invoked is False
    adapter.report.assert_not_called()
    assert before.record is not None and after.record is not None
    assert after.record.events == before.record.events
