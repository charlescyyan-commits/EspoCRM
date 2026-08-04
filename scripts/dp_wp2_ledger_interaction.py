"""DP-WP2 Stage-1 lock-scoped interaction with the DP-WP1.3 durable ledger.

This module is an inert protocol wrapper.  It owns no installation or
provisioning workflow, writes no JSON itself, and never exposes mutable
``InstallationRecord`` instances.  All ledger mutations stay inside the
existing ``JsonFileInstallationLedger`` lock/reload/persist boundary.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from scripts.dp_wp1_installation_foundation import (
    InstallationState,
    JsonFileInstallationLedger,
    LedgerEvent,
    RecoveryDisposition,
    ReleaseIdentity,
)


class DurableLedgerRequiredError(TypeError):
    """Raised when DP-WP2 is given a non-durable ledger adapter."""


class LedgerInteractionLockError(RuntimeError):
    """Raised when a DP-WP2 interaction is attempted outside its lock scope."""


class LedgerIdentityMismatchError(RuntimeError):
    """Raised when an installation ID is not bound to the expected identity."""


@dataclass(frozen=True)
class InstallationRecordSnapshot:
    """Immutable view of a DP-WP1.3 record returned by this wrapper."""

    installation_id: str
    identity: ReleaseIdentity | None
    state: InstallationState
    failure_reason: str | None
    events: tuple[LedgerEvent, ...]
    started_at: str | None
    updated_at: str | None
    completed_at: str | None


@dataclass(frozen=True)
class LedgerRecoverySnapshot:
    """Immutable recovery result without exposing the mutable ledger record."""

    disposition: RecoveryDisposition
    record: InstallationRecordSnapshot | None


class ProvisioningLedgerInteraction:
    """Use the existing durable ledger protocol under one explicit lock scope.

    The interaction layer deliberately omits ``create_precheck_failure``.
    DP-WP1.3 precheck-failure records have no verified ``ReleaseIdentity``;
    exposing them here would violate the Stage-1 per-call identity assertion.
    A future separately authorized preflight boundary must define that mapping
    before it can be added.
    """

    def __init__(self, ledger: JsonFileInstallationLedger) -> None:
        if not isinstance(ledger, JsonFileInstallationLedger):
            raise DurableLedgerRequiredError(
                "DP-WP2 requires the DP-WP1.3 JsonFileInstallationLedger"
            )
        self._ledger = ledger
        self._lock_active = False

    @contextmanager
    def locked(self) -> Iterator["ProvisioningLedgerInteraction"]:
        """Acquire, reload, and release the DP-WP1.3 durable lock boundary."""

        if self._lock_active:
            raise LedgerInteractionLockError("DP-WP2 ledger interaction lock is already active")
        self._ledger.acquire_lock()
        self._lock_active = True
        try:
            yield self
        finally:
            self._lock_active = False
            self._ledger.release_lock()

    def recover(self, expected_identity: ReleaseIdentity) -> LedgerRecoverySnapshot:
        """Read a recovery disposition from the latest lock-scoped snapshot."""

        self._require_lock()
        recovery = self._ledger.recover(expected_identity)
        record = recovery.record
        if record is not None and record.identity != expected_identity:
            raise LedgerIdentityMismatchError("ledger recovery identity does not match request")
        return LedgerRecoverySnapshot(
            disposition=recovery.disposition,
            record=self._snapshot(record) if record is not None else None,
        )

    def create_installation(
        self, expected_identity: ReleaseIdentity
    ) -> InstallationRecordSnapshot:
        """Create or return the identity-bound installation record under lock."""

        self._require_lock()
        record = self._ledger.create_installation(expected_identity)
        self._assert_record_identity(expected_identity, record.installation_id)
        return self._snapshot(record)

    def record_phase(
        self,
        expected_identity: ReleaseIdentity,
        installation_id: str,
        phase: InstallationState,
    ) -> InstallationRecordSnapshot:
        """Request one existing DP-WP1.4-governed phase transition under lock."""

        self._assert_record_identity(expected_identity, installation_id)
        record = self._ledger.record_phase(installation_id, phase)
        return self._snapshot(record)

    def record_step_result(
        self,
        expected_identity: ReleaseIdentity,
        installation_id: str,
        step_id: str,
        outcome: str,
    ) -> InstallationRecordSnapshot:
        """Record a named phase outcome without changing transition authority."""

        self._assert_record_identity(expected_identity, installation_id)
        record = self._ledger.record_step_result(installation_id, step_id, outcome)
        return self._snapshot(record)

    def mark_failure(
        self,
        expected_identity: ReleaseIdentity,
        installation_id: str,
        reason: str,
        state: InstallationState = InstallationState.FAILED,
    ) -> InstallationRecordSnapshot:
        """Record a governed DP-WP1.3 failure for the verified identity."""

        self._assert_record_identity(expected_identity, installation_id)
        record = self._ledger.mark_failure(installation_id, reason, state)
        return self._snapshot(record)

    def mark_completion(
        self, expected_identity: ReleaseIdentity, installation_id: str
    ) -> InstallationRecordSnapshot:
        """Record completion only through the existing DP-WP1.3 protocol."""

        self._assert_record_identity(expected_identity, installation_id)
        record = self._ledger.mark_completion(installation_id)
        return self._snapshot(record)

    def _assert_record_identity(
        self, expected_identity: ReleaseIdentity, installation_id: str
    ) -> None:
        self._require_lock()
        recovery = self._ledger.recover(expected_identity)
        record = recovery.record
        if (
            record is None
            or record.installation_id != installation_id
            or record.identity != expected_identity
        ):
            raise LedgerIdentityMismatchError(
                "installation ID is not bound to the expected release identity"
            )

    def _require_lock(self) -> None:
        if not self._lock_active:
            raise LedgerInteractionLockError(
                "use ProvisioningLedgerInteraction.locked() before interacting with the ledger"
            )

    @staticmethod
    def _snapshot(record: object) -> InstallationRecordSnapshot:
        """Copy only read-only record data; never return or mutate the source record."""

        return InstallationRecordSnapshot(
            installation_id=record.installation_id,
            identity=record.identity,
            state=record.state,
            failure_reason=record.failure_reason,
            events=tuple(record.events),
            started_at=record.started_at,
            updated_at=record.updated_at,
            completed_at=record.completed_at,
        )
