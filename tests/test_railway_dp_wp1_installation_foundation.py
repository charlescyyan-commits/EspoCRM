"""Focused offline tests for the DP-WP1.1 installation foundation."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "dp_wp1_installation_foundation.py"
DP_WP0_MANIFEST = ROOT / "deployment" / "railway" / "full-application-artifact-manifest.json"
SPEC = importlib.util.spec_from_file_location("dp_wp1_installation_foundation", SCRIPT_PATH)
assert SPEC and SPEC.loader
foundation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = foundation
SPEC.loader.exec_module(foundation)


def valid_manifest() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "release": {
            "extensionName": "Chitu Prospecting Integration",
            "extensionVersion": "1.9.13-alpha",
            "gitCommit": "6ef712134f581a12a18da5c98691884e73388b78",
            "deploymentModel": "deterministic-overlay",
        },
        "canonicalRoots": [],
        "requiredArtifacts": [],
        "files": [],
    }


def write_manifest(tmp_path: Path, document: dict[str, object]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def advance_to_metadata(ledger: object, installation_id: str) -> None:
    for state in (
        foundation.InstallationState.READY,
        foundation.InstallationState.INSTALLING,
        foundation.InstallationState.REGISTERED,
        foundation.InstallationState.HOOK_PENDING,
        foundation.InstallationState.MIGRATION_PENDING,
        foundation.InstallationState.METADATA_REFRESH,
    ):
        ledger.record_phase(installation_id, state)


def test_state_machine_allows_ordered_transition_and_rejects_skip() -> None:
    assert (
        foundation.transition(
            foundation.InstallationState.UNKNOWN, foundation.InstallationState.READY
        )
        == foundation.InstallationState.READY
    )
    with pytest.raises(foundation.InvalidStateTransition, match="UNKNOWN.*COMPLETED"):
        foundation.transition(
            foundation.InstallationState.UNKNOWN, foundation.InstallationState.COMPLETED
        )


def test_ledger_creates_idempotently_records_events_failure_and_completion() -> None:
    ledger = foundation.InMemoryInstallationLedger()
    identity = foundation.ReleaseIdentity("Chitu", "1.0.0", "a" * 64, "b" * 40)
    record = ledger.create_installation(identity)
    assert ledger.create_installation(identity).installation_id == record.installation_id

    ledger.record_phase(record.installation_id, foundation.InstallationState.READY)
    ledger.record_phase(record.installation_id, foundation.InstallationState.INSTALLING)
    ledger.record_step_result(record.installation_id, "preflight", "succeeded")
    ledger.mark_failure(record.installation_id, "synthetic failure")
    assert record.state == foundation.InstallationState.FAILED
    assert record.failure_reason == "synthetic failure"

    ledger.record_phase(record.installation_id, foundation.InstallationState.READY)
    advance_to_metadata(ledger, record.installation_id)
    ledger.mark_completion(record.installation_id)
    assert record.state == foundation.InstallationState.COMPLETED
    assert ledger.find_by_identity(identity) is record


def test_manifest_validator_accepts_valid_manifest_without_mutating_file(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, valid_manifest())
    before = path.read_bytes()
    result = foundation.ArtifactManifestValidator().validate(path)

    assert result.valid
    assert result.identity is not None
    assert result.identity.extension_name == "Chitu Prospecting Integration"
    assert path.read_bytes() == before


def test_manifest_validator_accepts_current_dp_wp0_manifest_without_mutation() -> None:
    before = DP_WP0_MANIFEST.read_bytes()
    result = foundation.ArtifactManifestValidator().validate(DP_WP0_MANIFEST)

    assert result.valid
    assert result.identity is not None
    assert result.identity.extension_version == "1.9.13-alpha"
    assert DP_WP0_MANIFEST.read_bytes() == before


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (lambda document: document.__setitem__("schemaVersion", 2), "schemaVersion"),
        (
            lambda document: document["release"].__setitem__("gitCommit", "invalid"),
            "gitCommit",
        ),
    ],
)
def test_manifest_validator_rejects_invalid_schema_and_identity(
    tmp_path: Path, mutation: object, expected_error: str
) -> None:
    document = valid_manifest()
    mutation(document)
    result = foundation.ArtifactManifestValidator().validate(write_manifest(tmp_path, document))

    assert not result.valid
    assert result.identity is None
    assert any(expected_error in error for error in result.errors)


def test_runner_successful_foundation_flow_stops_before_mutation(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path, valid_manifest())
    ledger = foundation.InMemoryInstallationLedger()
    runner = foundation.InstallationRunner(foundation.ArtifactManifestValidator(), ledger)

    first = runner.run_foundation(manifest)
    second = runner.run_foundation(manifest)

    assert first.started
    assert first.state == foundation.InstallationState.INSTALLING
    assert first.stopped_before == "extension registration"
    assert second.installation_id == first.installation_id
    assert second.state == foundation.InstallationState.INSTALLING
    record = next(iter(ledger._records.values()))
    assert [event.value for event in record.events if event.kind == "phase"] == [
        "READY",
        "INSTALLING",
    ]
    assert all(
        event.value not in {"REGISTERED", "HOOK_PENDING", "MIGRATION_PENDING", "METADATA_REFRESH"}
        for event in record.events
    )


def test_runner_failed_validation_is_ledgered_and_does_not_mutate_manifest(tmp_path: Path) -> None:
    document = valid_manifest()
    document["release"]["deploymentModel"] = "unsafe"
    manifest = write_manifest(tmp_path, document)
    before = manifest.read_bytes()
    ledger = foundation.InMemoryInstallationLedger()

    result = foundation.InstallationRunner(
        foundation.ArtifactManifestValidator(), ledger
    ).run_foundation(manifest)

    assert not result.started
    assert result.state == foundation.InstallationState.PRECHECK_FAILED
    assert "deploymentModel" in "; ".join(result.errors)
    assert manifest.read_bytes() == before
    record = ledger._records[result.installation_id]
    assert record.failure_reason is not None
    assert all(event.kind != "completion" for event in record.events)
