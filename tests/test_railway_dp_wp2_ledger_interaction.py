"""Focused DP-WP2 Stage-1 tests for the durable ledger interaction wrapper."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_ledger_interaction as interaction


def identity(version: str = "1.0.0") -> foundation.ReleaseIdentity:
    return foundation.ReleaseIdentity("Chitu", version, "a" * 64, "b" * 40)


def test_requires_the_durable_dp_wp1_3_adapter() -> None:
    with pytest.raises(interaction.DurableLedgerRequiredError):
        interaction.ProvisioningLedgerInteraction(foundation.InMemoryInstallationLedger())


def test_interaction_requires_its_lock_scoped_boundary(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "installation-ledger.json")
    layer = interaction.ProvisioningLedgerInteraction(ledger)

    with pytest.raises(interaction.LedgerInteractionLockError):
        layer.create_installation(identity())


def test_mutations_are_identity_bound_and_return_immutable_snapshots(tmp_path) -> None:
    ledger = foundation.JsonFileInstallationLedger(tmp_path / "installation-ledger.json")
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    first_identity = identity()
    second_identity = identity("2.0.0")

    with layer.locked():
        first = layer.create_installation(first_identity)
        second = layer.create_installation(second_identity)

        with pytest.raises(interaction.LedgerIdentityMismatchError):
            layer.record_phase(
                first_identity,
                second.installation_id,
                foundation.InstallationState.READY,
            )

        unchanged = layer.recover(second_identity)
        assert unchanged.record is not None
        assert unchanged.record.state == foundation.InstallationState.UNKNOWN

        updated = layer.record_phase(
            first_identity,
            first.installation_id,
            foundation.InstallationState.READY,
        )

    assert updated.identity == first_identity
    with pytest.raises(FrozenInstanceError):
        updated.state = foundation.InstallationState.FAILED


def test_wrapper_preserves_existing_state_machine_and_persists_via_durable_ledger(tmp_path) -> None:
    storage_path = tmp_path / "installation-ledger.json"
    ledger = foundation.JsonFileInstallationLedger(storage_path)
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    release_identity = identity()

    with layer.locked():
        record = layer.create_installation(release_identity)
        for phase in (
            foundation.InstallationState.READY,
            foundation.InstallationState.INSTALLING,
            foundation.InstallationState.REGISTERED,
            foundation.InstallationState.HOOK_PENDING,
            foundation.InstallationState.MIGRATION_PENDING,
            foundation.InstallationState.METADATA_REFRESH,
        ):
            layer.record_phase(release_identity, record.installation_id, phase)
        layer.record_step_result(
            release_identity, record.installation_id, "contract-only", "succeeded"
        )
        completed = layer.mark_completion(release_identity, record.installation_id)

    assert completed.state == foundation.InstallationState.COMPLETED
    restarted = foundation.JsonFileInstallationLedger(storage_path)
    recovered = restarted.recover(release_identity)
    assert recovered.disposition == foundation.RecoveryDisposition.COMPLETED_NOOP
