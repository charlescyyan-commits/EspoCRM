"""DP-WP2 Stage-1 report-only phase-adapter contract.

The contract defines data an eventual reviewed adapter may report.  It has no
ledger, state-machine, workflow, runtime, or concrete-adapter dependency, so
it cannot advance installation state or activate provisioning by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from scripts.dp_wp1_installation_foundation import ReleaseIdentity


class PhaseAdapterContractError(ValueError):
    """Raised when a report does not satisfy the report-only contract."""


class PhaseOutcome(str, Enum):
    """A report result, not a lifecycle state or transition request."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class IdempotencyMode(str, Enum):
    """The declared replay behavior for one named phase action."""

    REVALIDATE_AND_NOOP = "REVALIDATE_AND_NOOP"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"


@dataclass(frozen=True)
class IdempotencyContract:
    """An identity-bound replay rule that an adapter must declare."""

    key: str
    mode: IdempotencyMode


@dataclass(frozen=True)
class PhaseAdapterInput:
    """The complete, immutable input for one named phase action."""

    installation_id: str
    identity: ReleaseIdentity
    phase_name: str
    idempotency: IdempotencyContract


@dataclass(frozen=True)
class PhasePostcondition:
    """A named, redacted assertion an adapter reports after its action."""

    name: str
    satisfied: bool
    evidence: str


@dataclass(frozen=True)
class RedactedFailure:
    """A stable redacted diagnostic; no payload or exception object is allowed."""

    code: str
    summary: str


@dataclass(frozen=True)
class PhaseAdapterOutput:
    """A report-only output; it contains no ledger ID or transition target."""

    installation_id: str
    identity: ReleaseIdentity
    phase_name: str
    idempotency: IdempotencyContract
    outcome: PhaseOutcome
    postcondition: PhasePostcondition
    failure: RedactedFailure | None = None


class ReportOnlyPhaseAdapter(Protocol):
    """Future adapters may report a result but have no lifecycle authority."""

    def report(self, request: PhaseAdapterInput) -> PhaseAdapterOutput:
        """Return one contract-valid report for the supplied phase input."""


def validate_phase_adapter_output(
    request: PhaseAdapterInput, report: PhaseAdapterOutput
) -> None:
    """Validate a report without persisting, transitioning, or invoking anything."""

    _require_non_empty(request.installation_id, "installation_id")
    _require_non_empty(request.phase_name, "phase_name")
    _require_non_empty(request.idempotency.key, "idempotency key")
    _require_non_empty(report.installation_id, "report installation_id")
    _require_non_empty(report.phase_name, "report phase_name")
    _require_non_empty(report.idempotency.key, "report idempotency key")
    _require_non_empty(report.postcondition.name, "postcondition name")
    _require_non_empty(report.postcondition.evidence, "postcondition evidence")

    if report.installation_id != request.installation_id:
        raise PhaseAdapterContractError("report installation identity does not match request")
    if report.identity != request.identity:
        raise PhaseAdapterContractError("report release identity does not match request")
    if report.phase_name != request.phase_name:
        raise PhaseAdapterContractError("report phase name does not match request")
    if report.idempotency != request.idempotency:
        raise PhaseAdapterContractError("report idempotency contract does not match request")

    if report.outcome == PhaseOutcome.SUCCEEDED:
        if not report.postcondition.satisfied:
            raise PhaseAdapterContractError("successful report requires a satisfied postcondition")
        if report.failure is not None:
            raise PhaseAdapterContractError("successful report cannot include a failure")
        return

    if report.outcome == PhaseOutcome.FAILED:
        if report.postcondition.satisfied:
            raise PhaseAdapterContractError("failed report cannot claim a satisfied postcondition")
        if report.failure is None:
            raise PhaseAdapterContractError("failed report requires a redacted failure")
        _validate_redacted_failure(report.failure)
        return

    raise PhaseAdapterContractError("report outcome is not supported")


def _validate_redacted_failure(failure: RedactedFailure) -> None:
    _require_non_empty(failure.code, "failure code")
    _require_non_empty(failure.summary, "failure summary")
    if not all(character.isupper() or character.isdigit() or character == "_" for character in failure.code):
        raise PhaseAdapterContractError("failure code must contain only uppercase letters, digits, or underscores")
    if "\n" in failure.summary or "\r" in failure.summary:
        raise PhaseAdapterContractError("failure summary must be a single redacted line")


def _require_non_empty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PhaseAdapterContractError(f"{label} must be a non-empty string")
