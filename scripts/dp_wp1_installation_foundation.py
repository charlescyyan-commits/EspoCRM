#!/usr/bin/env python3
"""DP-WP1.1 deterministic installation foundation.

This module deliberately contains no installer, database adapter, network
client, Railway integration, or EspoCRM mutation.  It supplies the pure
state, manifest-validation, ledger, and orchestration boundaries that later
authorized phases can connect to controlled infrastructure adapters.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol


class InstallationState(str, Enum):
    """Explicit states for a single deterministic installation identity."""

    UNKNOWN = "UNKNOWN"
    PRECHECK_FAILED = "PRECHECK_FAILED"
    READY = "READY"
    INSTALLING = "INSTALLING"
    REGISTERED = "REGISTERED"
    HOOK_PENDING = "HOOK_PENDING"
    MIGRATION_PENDING = "MIGRATION_PENDING"
    METADATA_REFRESH = "METADATA_REFRESH"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InvalidStateTransition(ValueError):
    """Raised when an installation state would skip a controlled phase."""


_ALLOWED_TRANSITIONS: dict[InstallationState, frozenset[InstallationState]] = {
    InstallationState.UNKNOWN: frozenset(
        {InstallationState.PRECHECK_FAILED, InstallationState.READY}
    ),
    InstallationState.PRECHECK_FAILED: frozenset({InstallationState.READY}),
    InstallationState.READY: frozenset({InstallationState.INSTALLING}),
    InstallationState.INSTALLING: frozenset(
        {InstallationState.REGISTERED, InstallationState.FAILED}
    ),
    InstallationState.REGISTERED: frozenset(
        {InstallationState.HOOK_PENDING, InstallationState.FAILED}
    ),
    InstallationState.HOOK_PENDING: frozenset(
        {InstallationState.MIGRATION_PENDING, InstallationState.FAILED}
    ),
    InstallationState.MIGRATION_PENDING: frozenset(
        {InstallationState.METADATA_REFRESH, InstallationState.FAILED}
    ),
    InstallationState.METADATA_REFRESH: frozenset(
        {InstallationState.COMPLETED, InstallationState.FAILED}
    ),
    InstallationState.COMPLETED: frozenset(),
    InstallationState.FAILED: frozenset({InstallationState.READY}),
}


def transition(current: InstallationState, target: InstallationState) -> InstallationState:
    """Validate and return one deterministic state transition."""

    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"invalid installation transition: {current} -> {target}")
    return target


@dataclass(frozen=True)
class ReleaseIdentity:
    """The verified manifest identity used for idempotency and recovery."""

    extension_name: str
    extension_version: str
    manifest_hash: str
    source_commit: str

    @property
    def key(self) -> str:
        return "|".join(
            (
                self.extension_name,
                self.extension_version,
                self.manifest_hash,
                self.source_commit,
            )
        )


@dataclass(frozen=True)
class ManifestValidationResult:
    """A deterministic, read-only manifest validation result."""

    valid: bool
    identity: ReleaseIdentity | None
    manifest_hash: str | None
    errors: tuple[str, ...] = ()


class ArtifactManifestValidator:
    """Read-only schema and identity validator for the DP-WP0 manifest."""

    REQUIRED_ROOT_FIELDS = (
        "schemaVersion",
        "release",
        "canonicalRoots",
        "requiredArtifacts",
        "files",
    )
    REQUIRED_FILE_FIELDS = (
        "path",
        "sha256",
        "bytes",
        "category",
        "sourceRoot",
        "required",
        "executionStatus",
    )

    def validate(self, manifest_path: Path) -> ManifestValidationResult:
        """Load and validate one manifest without changing it or its directory."""

        try:
            payload = manifest_path.read_bytes()
        except OSError as error:
            return ManifestValidationResult(
                valid=False,
                identity=None,
                manifest_hash=None,
                errors=(f"manifest cannot be read: {error.__class__.__name__}",),
            )

        manifest_hash = hashlib.sha256(payload).hexdigest()
        try:
            document = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return ManifestValidationResult(
                valid=False,
                identity=None,
                manifest_hash=manifest_hash,
                errors=(f"manifest is not valid JSON: {error.__class__.__name__}",),
            )

        errors = self._schema_errors(document)
        identity, identity_errors = self._identity(document, manifest_hash)
        errors.extend(identity_errors)
        return ManifestValidationResult(
            valid=not errors,
            identity=identity if not errors else None,
            manifest_hash=manifest_hash,
            errors=tuple(errors),
        )

    def _schema_errors(self, document: object) -> list[str]:
        if not isinstance(document, dict):
            return ["manifest root must be an object"]

        errors: list[str] = []
        for field_name in self.REQUIRED_ROOT_FIELDS:
            if field_name not in document:
                errors.append(f"manifest missing required field: {field_name}")
        if document.get("schemaVersion") != 1:
            errors.append("manifest schemaVersion must be 1")
        if not isinstance(document.get("release"), dict):
            errors.append("manifest release must be an object")
        for field_name in ("canonicalRoots", "requiredArtifacts", "files"):
            if not isinstance(document.get(field_name), list):
                errors.append(f"manifest {field_name} must be an array")

        files = document.get("files")
        if isinstance(files, list):
            for index, entry in enumerate(files):
                if not isinstance(entry, dict):
                    errors.append(f"manifest files[{index}] must be an object")
                    continue
                missing = [key for key in self.REQUIRED_FILE_FIELDS if key not in entry]
                if missing:
                    errors.append(
                        f"manifest files[{index}] missing required fields: {', '.join(missing)}"
                    )
        return errors

    def _identity(
        self, document: object, manifest_hash: str
    ) -> tuple[ReleaseIdentity | None, list[str]]:
        if not isinstance(document, dict) or not isinstance(document.get("release"), dict):
            return None, ["manifest release identity is unavailable"]

        release = document["release"]
        assert isinstance(release, dict)
        fields = {
            "extensionName": release.get("extensionName"),
            "extensionVersion": release.get("extensionVersion"),
            "gitCommit": release.get("gitCommit"),
            "deploymentModel": release.get("deploymentModel"),
        }
        errors = [
            f"manifest release {name} must be a non-empty string"
            for name, value in fields.items()
            if not isinstance(value, str) or not value.strip()
        ]
        commit = fields["gitCommit"]
        if isinstance(commit, str) and (
            len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit)
        ):
            errors.append("manifest release gitCommit must be a lowercase 40-character SHA-1")
        if fields["deploymentModel"] != "deterministic-overlay":
            errors.append("manifest release deploymentModel must be deterministic-overlay")
        if errors:
            return None, errors

        return (
            ReleaseIdentity(
                extension_name=fields["extensionName"],
                extension_version=fields["extensionVersion"],
                manifest_hash=manifest_hash,
                source_commit=fields["gitCommit"],
            ),
            [],
        )


@dataclass(frozen=True)
class LedgerEvent:
    kind: str
    value: str
    outcome: str | None = None


@dataclass
class InstallationRecord:
    installation_id: str
    identity: ReleaseIdentity | None
    state: InstallationState = InstallationState.UNKNOWN
    failure_reason: str | None = None
    events: list[LedgerEvent] = field(default_factory=list)


class InstallationLedger(Protocol):
    """Storage boundary; a future adapter may provide durable persistence."""

    def find_by_identity(self, identity: ReleaseIdentity) -> InstallationRecord | None: ...

    def create_installation(self, identity: ReleaseIdentity) -> InstallationRecord: ...

    def create_precheck_failure(
        self, manifest_reference: str, manifest_hash: str | None
    ) -> InstallationRecord: ...

    def record_phase(
        self, installation_id: str, phase: InstallationState
    ) -> InstallationRecord: ...

    def record_step_result(
        self, installation_id: str, step_id: str, outcome: str
    ) -> InstallationRecord: ...

    def mark_failure(
        self,
        installation_id: str,
        reason: str,
        state: InstallationState = InstallationState.FAILED,
    ) -> InstallationRecord: ...

    def mark_completion(self, installation_id: str) -> InstallationRecord: ...


class InMemoryInstallationLedger:
    """Deterministic test/reference implementation; it has no database or UI."""

    def __init__(self) -> None:
        self._records: dict[str, InstallationRecord] = {}
        self._identity_index: dict[str, str] = {}

    def find_by_identity(self, identity: ReleaseIdentity) -> InstallationRecord | None:
        installation_id = self._identity_index.get(identity.key)
        return self._records.get(installation_id) if installation_id else None

    def create_installation(self, identity: ReleaseIdentity) -> InstallationRecord:
        existing = self.find_by_identity(identity)
        if existing:
            return existing
        installation_id = self._installation_id(f"release:{identity.key}")
        record = InstallationRecord(installation_id=installation_id, identity=identity)
        self._records[installation_id] = record
        self._identity_index[identity.key] = installation_id
        record.events.append(LedgerEvent("installation", "created"))
        return record

    def create_precheck_failure(
        self, manifest_reference: str, manifest_hash: str | None
    ) -> InstallationRecord:
        key = f"precheck:{manifest_reference}:{manifest_hash or 'unreadable'}"
        installation_id = self._installation_id(key)
        existing = self._records.get(installation_id)
        if existing:
            return existing
        record = InstallationRecord(installation_id=installation_id, identity=None)
        self._records[installation_id] = record
        record.events.append(LedgerEvent("installation", "precheck-created"))
        return record

    def record_phase(
        self, installation_id: str, phase: InstallationState
    ) -> InstallationRecord:
        record = self._record(installation_id)
        if record.state == phase:
            return record
        record.state = transition(record.state, phase)
        record.events.append(LedgerEvent("phase", phase.value))
        return record

    def record_step_result(
        self, installation_id: str, step_id: str, outcome: str
    ) -> InstallationRecord:
        record = self._record(installation_id)
        event = LedgerEvent("step", step_id, outcome)
        if event not in record.events:
            record.events.append(event)
        return record

    def mark_failure(
        self,
        installation_id: str,
        reason: str,
        state: InstallationState = InstallationState.FAILED,
    ) -> InstallationRecord:
        if state not in {InstallationState.PRECHECK_FAILED, InstallationState.FAILED}:
            raise ValueError("failure state must be PRECHECK_FAILED or FAILED")
        record = self._record(installation_id)
        if record.state != state:
            record.state = transition(record.state, state)
            record.events.append(LedgerEvent("phase", state.value))
        record.failure_reason = reason
        record.events.append(LedgerEvent("failure", reason, "failed"))
        return record

    def mark_completion(self, installation_id: str) -> InstallationRecord:
        record = self._record(installation_id)
        record.state = transition(record.state, InstallationState.COMPLETED)
        record.events.append(LedgerEvent("completion", InstallationState.COMPLETED.value))
        return record

    def _record(self, installation_id: str) -> InstallationRecord:
        try:
            return self._records[installation_id]
        except KeyError as error:
            raise KeyError(f"unknown installation: {installation_id}") from error

    @staticmethod
    def _installation_id(key: str) -> str:
        return "installation-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class FoundationRunResult:
    installation_id: str
    state: InstallationState
    started: bool
    stopped_before: str | None
    errors: tuple[str, ...] = ()


class InstallationRunner:
    """Foundation-only orchestrator that intentionally stops before mutation."""

    def __init__(self, validator: ArtifactManifestValidator, ledger: InstallationLedger) -> None:
        self._validator = validator
        self._ledger = ledger

    def run_foundation(self, manifest_path: Path) -> FoundationRunResult:
        """Validate and ledger preflight; never register, hook, migrate, or refresh."""

        validation = self._validator.validate(manifest_path)
        if not validation.valid:
            record = self._ledger.create_precheck_failure(
                manifest_path.as_posix(), validation.manifest_hash
            )
            self._ledger.mark_failure(
                record.installation_id,
                "; ".join(validation.errors),
                InstallationState.PRECHECK_FAILED,
            )
            self._ledger.record_step_result(
                record.installation_id, "preflight-manifest", "failed"
            )
            return FoundationRunResult(
                installation_id=record.installation_id,
                state=InstallationState.PRECHECK_FAILED,
                started=False,
                stopped_before=None,
                errors=validation.errors,
            )

        assert validation.identity is not None
        record = self._ledger.create_installation(validation.identity)
        if record.state == InstallationState.UNKNOWN:
            self._ledger.record_phase(record.installation_id, InstallationState.READY)
            self._ledger.record_step_result(
                record.installation_id, "preflight-manifest", "succeeded"
            )
            self._ledger.record_phase(record.installation_id, InstallationState.INSTALLING)

        return FoundationRunResult(
            installation_id=record.installation_id,
            state=record.state,
            started=record.state == InstallationState.INSTALLING,
            stopped_before="extension registration",
        )
