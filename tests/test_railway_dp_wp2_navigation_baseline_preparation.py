"""Focused tests for DP-WP2 navigation baseline preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import dp_wp1_installation_foundation as foundation
from scripts import dp_wp2_ledger_interaction as interaction
from scripts import dp_wp2_navigation_baseline_preparation as baseline
from scripts.dp_wp2_phase_adapters import navigation_provisioning as navigation

ROOT = Path(__file__).resolve().parent.parent
DEFINITION = ROOT / "deployment" / "navigation" / "phase3c17_navigation.json"
PROBE = ROOT / "temp" / "dp-wp2-navigation-runtime" / "dp_wp2_nav_probe.json"


def identity() -> foundation.ReleaseIdentity:
    return baseline.PINNED_IDENTITY


def target_items() -> list[navigation.NavigationItem]:
    document = json.loads(DEFINITION.read_text(encoding="utf-8"))
    return [navigation.normalize_navigation_item(item) for item in document["topLevelOrder"]]


def default_baseline_items() -> list[navigation.NavigationItem]:
    """Load the pinned Espo 29-item default captured in runtime probe forensics."""

    if not PROBE.exists():
        pytest.skip("runtime probe tabList fixture is required for default-baseline tests")
    raw = json.loads(PROBE.read_text(encoding="utf-8"))["tabList"]
    items = baseline.coerce_host_tab_list(raw)
    assert (
        navigation.sha256_hex(navigation.canonical_json_bytes(items))
        == baseline.PINNED_BEFORE_SHA256
    )
    return items


def seed_failed_navigation_ledger(
    path: Path,
) -> foundation.JsonFileInstallationLedger:
    ledger = foundation.JsonFileInstallationLedger(path)
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.create_installation(identity())
        for phase in (
            foundation.InstallationState.READY,
            foundation.InstallationState.INSTALLING,
            foundation.InstallationState.REGISTERED,
        ):
            layer.record_phase(identity(), record.installation_id, phase)
        layer.record_step_result(
            identity(),
            record.installation_id,
            baseline.NAVIGATION_STEP_ID,
            "failed",
        )
        layer.mark_failure(
            identity(),
            record.installation_id,
            "NAVIGATION_BASELINE_UNRECOGNIZED: current navigation is outside the approved bounded baseline",
            foundation.InstallationState.FAILED,
        )
    return ledger


def proof(registered: bool = True) -> baseline.RegistrationProof:
    return baseline.RegistrationProof(
        extension_registered=registered,
        available_modules=frozenset(baseline.REQUIRED_MODULES)
        if registered
        else frozenset(),
    )


def runner_for(
    tmp_path: Path,
    surface: baseline.InMemoryTabListSurface,
    *,
    registered: bool = True,
    pinned_before: str | None = None,
):
    ledger_path = tmp_path / "installation-ledger.json"
    ledger = seed_failed_navigation_ledger(ledger_path)
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity()).record
        assert record is not None
        installation_id = record.installation_id
    return baseline.NavigationBaselinePreparation(
        layer,
        surface,
        proof(registered),
        DEFINITION,
        expected_installation_id=installation_id,
        pinned_before_sha256=pinned_before or baseline.PINNED_BEFORE_SHA256,
    ), ledger, installation_id


def test_default_baseline_accepted_and_exact_target_applied(tmp_path: Path) -> None:
    items = default_baseline_items()
    assert (
        navigation.sha256_hex(navigation.canonical_json_bytes(items))
        == baseline.PINNED_BEFORE_SHA256
    )
    surface = baseline.InMemoryTabListSurface(items=items)
    prep, ledger, installation_id = runner_for(tmp_path, surface)

    result = prep.prepare()

    assert result.success is True
    assert result.failure_code is None
    assert result.write_count == 1
    assert result.before_checksum == baseline.PINNED_BEFORE_SHA256
    assert result.after_checksum == baseline.EXPECTED_POSTCONDITION_SHA256
    assert result.postcondition_checksum == baseline.EXPECTED_POSTCONDITION_SHA256
    assert result.state == foundation.InstallationState.FAILED
    assert result.baseline_step_outcome == "succeeded"
    assert result.idempotent_noop is False
    assert surface.read_top_level() == target_items()
    assert result.diff is not None
    assert result.diff.before_count == 29
    assert result.diff.after_count == 19
    assert result.business_data_touched is False

    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        recovered = layer.recover(identity())
        assert recovered.disposition == foundation.RecoveryDisposition.FAILED_PRESERVED
        assert recovered.record is not None
        assert recovered.record.installation_id == installation_id
        assert recovered.record.state == foundation.InstallationState.FAILED
        assert any(
            event.kind == "step"
            and event.value == baseline.BASELINE_STEP_ID
            and event.outcome == "succeeded"
            for event in recovered.record.events
        )
        assert not any(
            event.kind == "step"
            and event.value == baseline.NAVIGATION_STEP_ID
            and event.outcome == "succeeded"
            for event in recovered.record.events
        )


def test_checksum_mismatch_fails_closed_without_write(tmp_path: Path) -> None:
    surface = baseline.InMemoryTabListSurface(items=target_items()[:5] + default_baseline_items()[:5])
    prep, _ledger, _installation_id = runner_for(tmp_path, surface)

    result = prep.prepare()

    assert result.success is False
    assert result.failure_code == "BASELINE_CHECKSUM_MISMATCH"
    assert result.write_count == 0
    assert result.state == foundation.InstallationState.FAILED


def test_read_back_mismatch_records_failed_baseline_step(tmp_path: Path) -> None:
    class CorruptSurface(baseline.InMemoryTabListSurface):
        def write_top_level(self, items: list[navigation.NavigationItem]) -> None:
            super().write_top_level(items[:-1])

    surface = CorruptSurface(items=default_baseline_items())
    prep, ledger, _installation_id = runner_for(tmp_path, surface)

    result = prep.prepare()

    assert result.success is False
    assert result.failure_code == "NAVIGATION_READBACK_MISMATCH"
    assert result.write_count == 1
    assert result.state == foundation.InstallationState.FAILED
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity()).record
        assert record is not None
        assert any(
            event.kind == "step"
            and event.value == baseline.BASELINE_STEP_ID
            and event.outcome == "failed"
            for event in record.events
        )


def test_idempotent_rerun_when_already_at_target(tmp_path: Path) -> None:
    surface = baseline.InMemoryTabListSurface(items=default_baseline_items())
    prep, ledger, _installation_id = runner_for(tmp_path, surface)
    first = prep.prepare()
    assert first.success is True
    assert first.write_count == 1

    second_surface = baseline.InMemoryTabListSurface(items=target_items())
    # Rebind surface by constructing a new runner against the same ledger path.
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity()).record
        assert record is not None
        installation_id = record.installation_id
    second = baseline.NavigationBaselinePreparation(
        layer,
        second_surface,
        proof(),
        DEFINITION,
        expected_installation_id=installation_id,
    )
    result = second.prepare()

    assert result.success is True
    assert result.idempotent_noop is True
    assert result.write_count == 0
    assert result.state == foundation.InstallationState.FAILED
    assert result.after_checksum == baseline.EXPECTED_POSTCONDITION_SHA256


def test_registration_missing_fails_closed(tmp_path: Path) -> None:
    surface = baseline.InMemoryTabListSurface(items=default_baseline_items())
    prep, _ledger, _installation_id = runner_for(tmp_path, surface, registered=False)

    result = prep.prepare()

    assert result.success is False
    assert result.failure_code == "NAVIGATION_DEPENDENCY_UNAVAILABLE"
    assert result.write_count == 0


def test_forbidden_scope_does_not_touch_business_data_or_navigation_success(
    tmp_path: Path,
) -> None:
    surface = baseline.InMemoryTabListSurface(items=default_baseline_items())
    prep, ledger, _installation_id = runner_for(tmp_path, surface)

    result = prep.prepare()

    assert result.success is True
    assert result.business_data_touched is False
    assert surface.business_data_touched is False
    layer = interaction.ProvisioningLedgerInteraction(ledger)
    with layer.locked():
        record = layer.recover(identity()).record
        assert record is not None
        assert record.state == foundation.InstallationState.FAILED
        assert not any(
            event.kind == "phase" and event.value == "HOOK_PENDING"
            for event in record.events
        )
        assert not any(
            event.kind == "step"
            and event.value == baseline.NAVIGATION_STEP_ID
            and event.outcome == "succeeded"
            for event in record.events
        )


def test_unexpected_baseline_without_probe_fixture_uses_pinned_gate(tmp_path: Path) -> None:
    # Empty list is not the pinned default.
    surface = baseline.InMemoryTabListSurface(items=[])
    prep, _ledger, _installation_id = runner_for(tmp_path, surface)

    result = prep.prepare()

    assert result.success is False
    assert result.failure_code == "BASELINE_CHECKSUM_MISMATCH"
    assert result.write_count == 0
