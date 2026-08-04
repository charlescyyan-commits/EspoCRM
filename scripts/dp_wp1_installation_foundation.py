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
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Protocol


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


class LedgerCorruptionError(RuntimeError):
    """Raised when durable ledger data cannot be safely interpreted."""


class InstallationLockError(RuntimeError):
    """Raised when another installation process owns the durable ledger lock."""


_ALLOWED_TRANSITIONS: dict[InstallationState, frozenset[InstallationState]] = {
    InstallationState.UNKNOWN: frozenset(
        {InstallationState.PRECHECK_FAILED, InstallationState.READY}
    ),
    InstallationState.PRECHECK_FAILED: frozenset(
        {InstallationState.READY, InstallationState.FAILED}
    ),
    InstallationState.READY: frozenset(
        {InstallationState.INSTALLING, InstallationState.FAILED}
    ),
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


@dataclass(frozen=True)
class ManifestVerificationResult:
    """The result of read-only DP-WP0 artifact verification."""

    valid: bool
    identity: ReleaseIdentity | None
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


class ArtifactManifestVerifier:
    """Verify a DP-WP0 manifest, release identity, and listed artifact hashes.

    This adapter is deliberately read-only. It does not run the manifest
    generator, change release inputs, contact a network service, or invoke an
    installation action.
    """

    def __init__(
        self, repository_root: Path, validator: ArtifactManifestValidator | None = None
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._validator = validator or ArtifactManifestValidator()

    def verify(
        self, manifest_path: Path, expected_source_commit: str
    ) -> ManifestVerificationResult:
        """Verify one selected release identity and every manifest-listed file."""

        validation = self._validator.validate(manifest_path)
        if not validation.valid:
            return ManifestVerificationResult(False, None, validation.errors)

        assert validation.identity is not None
        errors: list[str] = []
        if validation.identity.source_commit != expected_source_commit:
            errors.append("manifest source commit does not match the selected release")

        try:
            manifest_bytes = manifest_path.read_bytes()
            document = json.loads(manifest_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            return ManifestVerificationResult(
                False,
                validation.identity,
                (f"manifest cannot be re-read for verification: {error.__class__.__name__}",),
            )
        if hashlib.sha256(manifest_bytes).hexdigest() != validation.identity.manifest_hash:
            errors.append("manifest changed during verification")

        errors.extend(self._extension_identity_errors(validation.identity))
        files = document.get("files")
        if isinstance(files, list):
            errors.extend(self._artifact_errors(files))

        try:
            if manifest_path.read_bytes() != manifest_bytes:
                errors.append("manifest changed during verification")
        except OSError as error:
            errors.append(f"manifest cannot be re-read for verification: {error.__class__.__name__}")

        return ManifestVerificationResult(
            valid=not errors,
            identity=validation.identity,
            errors=tuple(errors),
        )

    def _extension_identity_errors(self, identity: ReleaseIdentity) -> list[str]:
        extension_manifest = self._repository_root / "crm-extension" / "manifest.json"
        try:
            document = json.loads(extension_manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            return [f"extension manifest cannot be read: {error.__class__.__name__}"]
        if not isinstance(document, dict):
            return ["extension manifest root must be an object"]

        extension_name = document.get("extensionName") or document.get("name")
        extension_version = document.get("version")
        errors: list[str] = []
        if extension_name != identity.extension_name:
            errors.append("manifest extension name does not match crm-extension/manifest.json")
        if extension_version != identity.extension_version:
            errors.append("manifest extension version does not match crm-extension/manifest.json")
        return errors

    def _artifact_errors(self, files: list[object]) -> list[str]:
        errors: list[str] = []
        for index, entry in enumerate(files):
            if not isinstance(entry, dict):
                # The schema validator reports this too; retain a clear result
                # when the verifier is used with a custom validator.
                errors.append(f"manifest files[{index}] must be an object")
                continue
            path_text = entry.get("path")
            expected_hash = entry.get("sha256")
            expected_bytes = entry.get("bytes")
            if not isinstance(path_text, str) or not self._is_safe_relative_path(path_text):
                errors.append(f"manifest files[{index}] has an unsafe path")
                continue
            if not isinstance(expected_hash, str) or (
                len(expected_hash) != 64
                or any(character not in "0123456789abcdef" for character in expected_hash)
            ):
                errors.append(f"manifest file has an invalid SHA-256: {path_text}")
                continue
            if not isinstance(expected_bytes, int) or expected_bytes < 0:
                errors.append(f"manifest file has invalid byte count: {path_text}")
                continue

            artifact = self._repository_root / Path(path_text)
            if not artifact.is_file() or artifact.is_symlink():
                errors.append(f"manifest artifact is missing: {path_text}")
                continue
            if artifact.stat().st_size != expected_bytes:
                errors.append(f"manifest artifact byte count mismatch: {path_text}")
                continue
            with artifact.open("rb") as handle:
                actual_hash = hashlib.file_digest(handle, "sha256").hexdigest()
            if actual_hash != expected_hash:
                errors.append(f"manifest artifact SHA-256 mismatch: {path_text}")
        return errors

    @staticmethod
    def _is_safe_relative_path(path_text: str) -> bool:
        path = Path(path_text)
        return (
            bool(path_text)
            and not path.is_absolute()
            and "\\" not in path_text
            and ".." not in path.parts
        )


@dataclass(frozen=True)
class LedgerEvent:
    kind: str
    value: str
    outcome: str | None = None
    recorded_at: str | None = None


@dataclass
class InstallationRecord:
    installation_id: str
    identity: ReleaseIdentity | None
    state: InstallationState = InstallationState.UNKNOWN
    failure_reason: str | None = None
    events: list[LedgerEvent] = field(default_factory=list)
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


class RecoveryDisposition(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    RESUME = "RESUME"
    COMPLETED_NOOP = "COMPLETED_NOOP"
    FAILED_PRESERVED = "FAILED_PRESERVED"


@dataclass(frozen=True)
class LedgerRecovery:
    disposition: RecoveryDisposition
    record: InstallationRecord | None


class InstallationLedger(Protocol):
    """Storage boundary; a future adapter may provide durable persistence."""

    def find_by_identity(self, identity: ReleaseIdentity) -> InstallationRecord | None: ...

    def recover(self, identity: ReleaseIdentity) -> LedgerRecovery: ...

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

    def recover(self, identity: ReleaseIdentity) -> LedgerRecovery:
        record = self.find_by_identity(identity)
        if record is None:
            return LedgerRecovery(RecoveryDisposition.NOT_FOUND, None)
        if record.state == InstallationState.COMPLETED:
            return LedgerRecovery(RecoveryDisposition.COMPLETED_NOOP, record)
        if record.state in {InstallationState.FAILED, InstallationState.PRECHECK_FAILED}:
            return LedgerRecovery(RecoveryDisposition.FAILED_PRESERVED, record)
        return LedgerRecovery(RecoveryDisposition.RESUME, record)

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
        if not any(
            existing.kind == event.kind
            and existing.value == event.value
            and existing.outcome == event.outcome
            for existing in record.events
        ):
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


class JsonFileInstallationLedger(InMemoryInstallationLedger):
    """Durable, restart-safe JSON installation ledger with an exclusive lock.

    The adapter stores only installation control state in a caller-selected
    file. It has no database, CRM entity, UI, business-data, network, or
    installation-action dependency. Each mutation requires an acquired lock
    and is persisted by an atomic file replacement.
    """

    SCHEMA_VERSION = 1

    def __init__(self, storage_path: Path) -> None:
        super().__init__()
        self._storage_path = storage_path
        self._lock_path = storage_path.with_name(f"{storage_path.name}.lock")
        self._lock_owned = False
        self._lock_handle: BinaryIO | None = None
        self._load()

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    def acquire_lock(self) -> None:
        if self._lock_owned:
            return
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle = self._lock_path.open("a+b")
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            self._lock_handle_acquire(handle)
        except OSError as error:
            if "handle" in locals():
                handle.close()
            raise InstallationLockError(
                f"installation ledger is locked: {self._lock_path}"
            ) from error
        self._lock_handle = handle
        self._lock_owned = True
        try:
            # The adapter may have been constructed before another process
            # committed and released its own mutation. Reload only after the
            # exclusive lock is held so every following identity lookup and
            # mutation uses the latest validated durable snapshot.
            self._reload_after_lock()
        except Exception:
            self.release_lock()
            raise

    def release_lock(self) -> None:
        if not self._lock_owned:
            return
        try:
            assert self._lock_handle is not None
            self._lock_handle_release(self._lock_handle)
        finally:
            if self._lock_handle is not None:
                self._lock_handle.close()
            self._lock_handle = None
            self._lock_owned = False

    def create_installation(self, identity: ReleaseIdentity) -> InstallationRecord:
        self._require_lock()
        existing = self.find_by_identity(identity)
        if existing is not None:
            return existing
        record = super().create_installation(identity)
        self._persist_changed(record, previous_event_count=0)
        return record

    def create_precheck_failure(
        self, manifest_reference: str, manifest_hash: str | None
    ) -> InstallationRecord:
        self._require_lock()
        key = self._installation_id(
            f"precheck:{manifest_reference}:{manifest_hash or 'unreadable'}"
        )
        existing = self._records.get(key)
        if existing is not None:
            return existing
        record = super().create_precheck_failure(manifest_reference, manifest_hash)
        self._persist_changed(record, previous_event_count=0)
        return record

    def record_phase(
        self, installation_id: str, phase: InstallationState
    ) -> InstallationRecord:
        self._require_lock()
        record = self._record(installation_id)
        before_state = record.state
        before_events = len(record.events)
        result = super().record_phase(installation_id, phase)
        if result.state != before_state or len(result.events) != before_events:
            self._persist_changed(result, before_events)
        return result

    def record_step_result(
        self, installation_id: str, step_id: str, outcome: str
    ) -> InstallationRecord:
        self._require_lock()
        record = self._record(installation_id)
        before_events = len(record.events)
        result = super().record_step_result(installation_id, step_id, outcome)
        if len(result.events) != before_events:
            self._persist_changed(result, before_events)
        return result

    def mark_failure(
        self,
        installation_id: str,
        reason: str,
        state: InstallationState = InstallationState.FAILED,
    ) -> InstallationRecord:
        self._require_lock()
        record = self._record(installation_id)
        before_events = len(record.events)
        result = super().mark_failure(installation_id, reason, state)
        self._persist_changed(result, before_events)
        return result

    def mark_completion(self, installation_id: str) -> InstallationRecord:
        self._require_lock()
        record = self._record(installation_id)
        before_events = len(record.events)
        result = super().mark_completion(installation_id)
        self._persist_changed(result, before_events)
        return result

    def _require_lock(self) -> None:
        if not self._lock_owned:
            raise InstallationLockError("acquire the installation ledger lock before mutation")

    def _persist_changed(self, record: InstallationRecord, previous_event_count: int) -> None:
        timestamp = self._timestamp()
        if record.started_at is None:
            record.started_at = timestamp
        record.updated_at = timestamp
        if record.state == InstallationState.COMPLETED and record.completed_at is None:
            record.completed_at = timestamp
        for index in range(previous_event_count, len(record.events)):
            event = record.events[index]
            record.events[index] = LedgerEvent(
                event.kind,
                event.value,
                event.outcome,
                timestamp,
            )
        self._persist()

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            document = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LedgerCorruptionError(
                f"cannot parse durable installation ledger: {self._storage_path}"
            ) from error
        if not isinstance(document, dict) or document.get("schemaVersion") != self.SCHEMA_VERSION:
            raise LedgerCorruptionError("durable installation ledger has an unsupported schema")
        records = document.get("records")
        if not isinstance(records, list):
            raise LedgerCorruptionError("durable installation ledger records must be an array")
        for payload in records:
            record = self._record_from_payload(payload)
            if record.installation_id in self._records:
                raise LedgerCorruptionError("durable installation ledger has duplicate installation IDs")
            self._records[record.installation_id] = record
            if record.identity is not None:
                if record.identity.key in self._identity_index:
                    raise LedgerCorruptionError("durable installation ledger has duplicate release identities")
                self._identity_index[record.identity.key] = record.installation_id

    def _reload_after_lock(self) -> None:
        self._records.clear()
        self._identity_index.clear()
        self._load()

    def _persist(self) -> None:
        document = {
            "schemaVersion": self.SCHEMA_VERSION,
            "records": [
                self._record_to_payload(self._records[installation_id])
                for installation_id in sorted(self._records)
            ],
        }
        payload = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=self._storage_path.parent,
            prefix=f".{self._storage_path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            self._sync(handle)
        try:
            temporary_path.replace(self._storage_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def _record_to_payload(self, record: InstallationRecord) -> dict[str, object]:
        identity = record.identity
        return {
            "installationId": record.installation_id,
            "extensionName": identity.extension_name if identity else None,
            "extensionVersion": identity.extension_version if identity else None,
            "manifestHash": identity.manifest_hash if identity else None,
            "sourceCommit": identity.source_commit if identity else None,
            "status": self._status_for(record.state),
            "currentPhase": record.state.value,
            "stepEvents": [
                {
                    "kind": event.kind,
                    "value": event.value,
                    "outcome": event.outcome,
                    "recordedAt": event.recorded_at,
                }
                for event in record.events
            ],
            "startedAt": record.started_at,
            "updatedAt": record.updated_at,
            "completedAt": record.completed_at,
            "failureReason": record.failure_reason,
        }

    def _record_from_payload(self, payload: object) -> InstallationRecord:
        if not isinstance(payload, dict):
            raise LedgerCorruptionError("durable installation record must be an object")
        installation_id = payload.get("installationId")
        phase = payload.get("currentPhase")
        status = payload.get("status")
        if not isinstance(installation_id, str) or not installation_id:
            raise LedgerCorruptionError("durable installation record has no installationId")
        try:
            state = InstallationState(phase)
        except (TypeError, ValueError) as error:
            raise LedgerCorruptionError("durable installation record has an invalid currentPhase") from error
        if status != self._status_for(state):
            raise LedgerCorruptionError("durable installation record status does not match currentPhase")

        identity_values = [
            payload.get("extensionName"),
            payload.get("extensionVersion"),
            payload.get("manifestHash"),
            payload.get("sourceCommit"),
        ]
        if all(value is None for value in identity_values):
            identity = None
        elif all(isinstance(value, str) and value for value in identity_values):
            identity = ReleaseIdentity(
                extension_name=identity_values[0],
                extension_version=identity_values[1],
                manifest_hash=identity_values[2],
                source_commit=identity_values[3],
            )
        else:
            raise LedgerCorruptionError("durable installation record has a partial release identity")

        events_payload = payload.get("stepEvents")
        if not isinstance(events_payload, list):
            raise LedgerCorruptionError("durable installation record stepEvents must be an array")
        events: list[LedgerEvent] = []
        for event_payload in events_payload:
            if not isinstance(event_payload, dict):
                raise LedgerCorruptionError("durable installation event must be an object")
            kind = event_payload.get("kind")
            value = event_payload.get("value")
            outcome = event_payload.get("outcome")
            recorded_at = event_payload.get("recordedAt")
            if not isinstance(kind, str) or not isinstance(value, str):
                raise LedgerCorruptionError("durable installation event is invalid")
            if outcome is not None and not isinstance(outcome, str):
                raise LedgerCorruptionError("durable installation event outcome is invalid")
            if recorded_at is not None and not isinstance(recorded_at, str):
                raise LedgerCorruptionError("durable installation event timestamp is invalid")
            events.append(LedgerEvent(kind, value, outcome, recorded_at))

        timestamps = [payload.get("startedAt"), payload.get("updatedAt"), payload.get("completedAt")]
        if any(value is not None and not isinstance(value, str) for value in timestamps):
            raise LedgerCorruptionError("durable installation record timestamp is invalid")
        failure_reason = payload.get("failureReason")
        if failure_reason is not None and not isinstance(failure_reason, str):
            raise LedgerCorruptionError("durable installation failure reason is invalid")
        return InstallationRecord(
            installation_id=installation_id,
            identity=identity,
            state=state,
            failure_reason=failure_reason,
            events=events,
            started_at=timestamps[0],
            updated_at=timestamps[1],
            completed_at=timestamps[2],
        )

    @staticmethod
    def _status_for(state: InstallationState) -> str:
        if state == InstallationState.COMPLETED:
            return "completed"
        if state in {InstallationState.PRECHECK_FAILED, InstallationState.FAILED}:
            return "failed"
        if state == InstallationState.UNKNOWN:
            return "planned"
        return "running"

    @staticmethod
    def _timestamp() -> str:
        # A monotonic wall-clock source is intentionally not required for the
        # ledger's recovery decision; timestamps are audit metadata only.
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _lock_handle_acquire(handle: BinaryIO) -> None:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _lock_handle_release(handle: BinaryIO) -> None:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _sync(handle: BinaryIO) -> None:
        if os.name == "nt":
            import msvcrt

            msvcrt.setmode(handle.fileno(), os.O_BINARY)
        os.fsync(handle.fileno())


@dataclass(frozen=True)
class FoundationRunResult:
    installation_id: str
    state: InstallationState
    started: bool
    stopped_before: str | None
    errors: tuple[str, ...] = ()


class InstallationRunner:
    """Foundation-only orchestrator that intentionally stops before mutation."""

    def __init__(
        self,
        validator: ArtifactManifestValidator,
        ledger: InstallationLedger,
        verifier: ArtifactManifestVerifier,
    ) -> None:
        self._validator = validator
        self._ledger = ledger
        self._verifier = verifier

    def run_foundation(
        self, manifest_path: Path, expected_source_commit: str
    ) -> FoundationRunResult:
        """Preflight and verify artifacts; never register, hook, migrate, or refresh."""

        validation = self._validator.validate(manifest_path)
        if not validation.valid:
            record = self._ledger.create_precheck_failure(
                manifest_path.as_posix(), validation.manifest_hash
            )
            self._ledger.record_phase(
                record.installation_id, InstallationState.PRECHECK_FAILED
            )
            self._ledger.record_step_result(
                record.installation_id, "preflight-manifest", "failed"
            )
            self._ledger.mark_failure(
                record.installation_id,
                "; ".join(validation.errors),
            )
            return FoundationRunResult(
                installation_id=record.installation_id,
                state=InstallationState.FAILED,
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

        verification = self._verifier.verify(manifest_path, expected_source_commit)
        if not verification.valid:
            self._ledger.record_step_result(
                record.installation_id, "artifact-manifest", "failed"
            )
            self._ledger.mark_failure(
                record.installation_id,
                "; ".join(verification.errors),
            )
            return FoundationRunResult(
                installation_id=record.installation_id,
                state=InstallationState.FAILED,
                started=False,
                stopped_before=None,
                errors=verification.errors,
            )

        self._ledger.record_step_result(
            record.installation_id, "artifact-manifest", "succeeded"
        )
        if record.state == InstallationState.READY:
            self._ledger.record_phase(record.installation_id, InstallationState.INSTALLING)

        return FoundationRunResult(
            installation_id=record.installation_id,
            state=record.state,
            started=record.state == InstallationState.INSTALLING,
            stopped_before="extension registration",
        )
