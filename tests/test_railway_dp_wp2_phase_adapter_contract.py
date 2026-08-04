"""Focused DP-WP2 Stage-1 tests for the report-only phase-adapter contract."""

from __future__ import annotations

import pytest

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_phase_adapter_contract as contract


def identity() -> foundation.ReleaseIdentity:
    return foundation.ReleaseIdentity("Chitu", "1.0.0", "a" * 64, "b" * 40)


def request() -> contract.PhaseAdapterInput:
    return contract.PhaseAdapterInput(
        installation_id="installation-1",
        identity=identity(),
        phase_name="provisioning-contract-only",
        idempotency=contract.IdempotencyContract(
            key="provisioning-contract-only:v1",
            mode=contract.IdempotencyMode.REVALIDATE_AND_NOOP,
        ),
    )


def test_valid_success_report_carries_input_postcondition_and_idempotency_contract() -> None:
    phase_input = request()
    report = contract.PhaseAdapterOutput(
        installation_id=phase_input.installation_id,
        identity=phase_input.identity,
        phase_name=phase_input.phase_name,
        idempotency=phase_input.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=contract.PhasePostcondition(
            name="contract-validated", satisfied=True, evidence="synthetic-fixture"
        ),
    )

    contract.validate_phase_adapter_output(phase_input, report)


def test_failure_report_requires_a_redacted_single_line_diagnostic() -> None:
    phase_input = request()
    report = contract.PhaseAdapterOutput(
        installation_id=phase_input.installation_id,
        identity=phase_input.identity,
        phase_name=phase_input.phase_name,
        idempotency=phase_input.idempotency,
        outcome=contract.PhaseOutcome.FAILED,
        postcondition=contract.PhasePostcondition(
            name="contract-validated", satisfied=False, evidence="synthetic-fixture"
        ),
        failure=contract.RedactedFailure("ADAPTER_UNAVAILABLE", "adapter is not approved"),
    )

    contract.validate_phase_adapter_output(phase_input, report)

    invalid = contract.PhaseAdapterOutput(
        installation_id=phase_input.installation_id,
        identity=phase_input.identity,
        phase_name=phase_input.phase_name,
        idempotency=phase_input.idempotency,
        outcome=contract.PhaseOutcome.FAILED,
        postcondition=report.postcondition,
        failure=contract.RedactedFailure("adapter unavailable", "line one\nline two"),
    )
    with pytest.raises(contract.PhaseAdapterContractError):
        contract.validate_phase_adapter_output(phase_input, invalid)


def test_report_rejects_identity_drift_and_has_no_transition_authority() -> None:
    phase_input = request()
    drifted = contract.PhaseAdapterOutput(
        installation_id=phase_input.installation_id,
        identity=foundation.ReleaseIdentity("Chitu", "2.0.0", "c" * 64, "d" * 40),
        phase_name=phase_input.phase_name,
        idempotency=phase_input.idempotency,
        outcome=contract.PhaseOutcome.SUCCEEDED,
        postcondition=contract.PhasePostcondition(
            name="contract-validated", satisfied=True, evidence="synthetic-fixture"
        ),
    )

    with pytest.raises(contract.PhaseAdapterContractError, match="release identity"):
        contract.validate_phase_adapter_output(phase_input, drifted)

    assert "record_phase" not in contract.ReportOnlyPhaseAdapter.__dict__
    assert "mark_failure" not in contract.ReportOnlyPhaseAdapter.__dict__
    assert "mark_completion" not in contract.ReportOnlyPhaseAdapter.__dict__
