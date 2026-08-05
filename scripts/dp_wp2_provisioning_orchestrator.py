"""DP-WP2 Stage-1 explicit-invocation provisioning orchestrator skeleton.

This module is inert until a caller explicitly invokes ``invoke`` with a
verified release identity.  It does not register adapters, execute a hook,
run a migration, or attach to a runtime trigger.  Its only persistent actions
are requests through the DP-WP2 ledger-interaction boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from scripts.dp_wp1_installation_foundation import (
    InstallationLockError,
    InstallationState,
    InvalidStateTransition,
    LedgerCorruptionError,
    RecoveryDisposition,
    ReleaseIdentity,
    transition,
)
from scripts.dp_wp2_ledger_interaction import (
    InstallationRecordSnapshot,
    LedgerInteractionLockError,
    ProvisioningLedgerInteraction,
)
from scripts.dp_wp2_phase_adapter_contract import (
    IdempotencyContract,
    PhaseAdapterContractError,
    PhaseAdapterInput,
    PhaseAdapterOutput,
    PhaseOutcome,
    PhasePostcondition,
    RedactedFailure,
    ReportOnlyPhaseAdapter,
    validate_phase_adapter_output,
)

NAVIGATION_PROVISIONING_PHASE = "navigation_provisioning"
NAVIGATION_POSTCONDITION_NAME = "navigation_state_matches_definition"
NAVIGATION_REQUIRED_MODULES = frozenset(
    {"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}
)


class OperatorBlockStage(str, Enum):
    """Administrative block classification; this is not a ledger state."""

    PREFLIGHT = "PREFLIGHT"
    LATER_PHASE = "LATER_PHASE"


class AdmissionKind(str, Enum):
    """Administrative admission classification; not a durable lifecycle state."""

    FIRST_RUNTIME_ADMISSION = "FIRST_RUNTIME_ADMISSION"
    BASELINE_RECOVERY_ADMISSION = "BASELINE_RECOVERY_ADMISSION"
    RESUME = "RESUME"
    NEW_ATTEMPT = "NEW_ATTEMPT"


BASELINE_STEP_ID = "baseline:navigation_default_to_phase3c19_ia_v1"

@dataclass(frozen=True)
class OperatorBlockCondition:
    """A pre-redacted operator decision that the orchestrator must ledger."""

    stage: OperatorBlockStage
    failure: RedactedFailure


@dataclass(frozen=True)
class RuntimeDependencyEvidence:
    """Immutable DP-WP1 registration/module proof for first-runtime admission."""

    installation_id: str
    identity: ReleaseIdentity
    extension_registered: bool
    available_modules: frozenset[str]


@dataclass(frozen=True)
class ProvisioningInvocation:
    """Explicit, identity-bound input for one report-only adapter invocation."""

    identity: ReleaseIdentity
    phase_name: str
    idempotency: IdempotencyContract
    target_phase: InstallationState
    resume_postcondition: PhasePostcondition | None = None
    dependency_evidence: RuntimeDependencyEvidence | None = None


@dataclass(frozen=True)
class ProvisioningInvocationResult:
    """Redacted administrative result; no business or provider data is returned."""

    installation_id: str | None
    state: InstallationState | None
    recovery_disposition: RecoveryDisposition | None
    adapter_invoked: bool
    completed_noop: bool
    failure_code: str | None = None
    admission_kind: AdmissionKind | None = None


class ProvisioningOrchestrator:
    """Coordinate one explicit, governed adapter report through DP-WP1.3/1.4."""

    _ADAPTER_TARGETS = frozenset(
        {
            InstallationState.REGISTERED,
            InstallationState.HOOK_PENDING,
            InstallationState.MIGRATION_PENDING,
            InstallationState.METADATA_REFRESH,
        }
    )

    def __init__(
        self,
        ledger_interaction: ProvisioningLedgerInteraction,
        adapters: Mapping[str, ReportOnlyPhaseAdapter] | None = None,
    ) -> None:
        self._ledger = ledger_interaction
        self._adapters = dict(adapters or {})

    def invoke(
        self,
        invocation: ProvisioningInvocation,
        operator_block: OperatorBlockCondition | None = None,
    ) -> ProvisioningInvocationResult:
        """Process one explicit request; no caller or runtime invokes this implicitly."""

        input_failure = self._invocation_failure(invocation)
        if input_failure is not None:
            return self._rejected(input_failure)

        try:
            with self._ledger.locked():
                recovery = self._ledger.recover(invocation.identity)
                if recovery.disposition == RecoveryDisposition.COMPLETED_NOOP:
                    return self._result(recovery.record, recovery.disposition, False, True)
                if recovery.disposition == RecoveryDisposition.FAILED_PRESERVED:
                    return self._result(
                        recovery.record,
                        recovery.disposition,
                        False,
                        False,
                        "FAILED_PRESERVED",
                    )

                record = recovery.record
                if recovery.disposition == RecoveryDisposition.NOT_FOUND:
                    record = self._ledger.create_installation(invocation.identity)
                assert record is not None

                if operator_block is not None:
                    return self._record_operator_block(
                        record, recovery.disposition, operator_block
                    )

                admission_kind = AdmissionKind.NEW_ATTEMPT
                if recovery.disposition == RecoveryDisposition.RESUME:
                    admission_kind, admission_failure = self._classify_resume_admission(
                        record, invocation
                    )
                    if admission_failure is not None:
                        return self._record_operator_block(
                            record,
                            recovery.disposition,
                            OperatorBlockCondition(
                                OperatorBlockStage.LATER_PHASE,
                                RedactedFailure(
                                    admission_failure,
                                    self._admission_failure_summary(admission_failure),
                                ),
                            ),
                            admission_kind=admission_kind,
                        )

                adapter = self._adapters.get(invocation.phase_name)
                if adapter is None:
                    block_stage = (
                        OperatorBlockStage.PREFLIGHT
                        if record.state == InstallationState.UNKNOWN
                        else OperatorBlockStage.LATER_PHASE
                    )
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(
                            block_stage,
                            RedactedFailure(
                                "ADAPTER_REGISTRY_EMPTY",
                                "no reviewed phase adapter is registered",
                            ),
                        ),
                        admission_kind=admission_kind,
                    )

                # First-runtime admission must not invent step markers or change state
                # before the adapter reports. REGISTERED stays REGISTERED until success.
                record = self._admit_adapter(record, invocation.identity)
                request = PhaseAdapterInput(
                    installation_id=record.installation_id,
                    identity=invocation.identity,
                    phase_name=invocation.phase_name,
                    idempotency=invocation.idempotency,
                )
                try:
                    report = adapter.report(request)
                    validate_phase_adapter_output(request, report)
                except (PhaseAdapterContractError, ValueError):
                    record = self._record_adapter_step_result(
                        record,
                        invocation.identity,
                        invocation.phase_name,
                        "failed",
                    )
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(
                            OperatorBlockStage.LATER_PHASE,
                            RedactedFailure(
                                "ADAPTER_CONTRACT_INVALID",
                                "phase adapter report failed contract validation",
                            ),
                        ),
                        adapter_invoked=True,
                        admission_kind=admission_kind,
                    )
                except Exception:
                    record = self._record_adapter_step_result(
                        record,
                        invocation.identity,
                        invocation.phase_name,
                        "failed",
                    )
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(
                            OperatorBlockStage.LATER_PHASE,
                            RedactedFailure(
                                "ADAPTER_REPORT_FAILED",
                                "phase adapter did not return a valid report",
                            ),
                        ),
                        adapter_invoked=True,
                        admission_kind=admission_kind,
                    )

                record = self._record_adapter_step_result(
                    record,
                    invocation.identity,
                    invocation.phase_name,
                    "succeeded" if report.outcome == PhaseOutcome.SUCCEEDED else "failed",
                    report.postcondition.name,
                )
                if report.outcome == PhaseOutcome.FAILED:
                    assert report.failure is not None
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(OperatorBlockStage.LATER_PHASE, report.failure),
                        adapter_invoked=True,
                        admission_kind=admission_kind,
                    )

                if invocation.target_phase not in self._ADAPTER_TARGETS:
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(
                            OperatorBlockStage.LATER_PHASE,
                            RedactedFailure(
                                "PHASE_TARGET_NOT_AUTHORIZED",
                                "adapter target phase is not authorized",
                            ),
                        ),
                        adapter_invoked=True,
                        admission_kind=admission_kind,
                    )

                try:
                    transition(record.state, invocation.target_phase)
                except InvalidStateTransition:
                    return self._record_operator_block(
                        record,
                        recovery.disposition,
                        OperatorBlockCondition(
                            OperatorBlockStage.LATER_PHASE,
                            RedactedFailure(
                                "PHASE_TRANSITION_REJECTED",
                                "adapter target is not an allowed transition",
                            ),
                        ),
                        adapter_invoked=True,
                        admission_kind=admission_kind,
                    )

                updated = self._ledger.record_phase(
                    invocation.identity, record.installation_id, invocation.target_phase
                )
                return self._result(
                    updated,
                    recovery.disposition,
                    True,
                    False,
                    admission_kind=admission_kind,
                )
        except (InstallationLockError, LedgerInteractionLockError):
            return self._rejected("LEDGER_LOCK_UNAVAILABLE")
        except LedgerCorruptionError:
            return self._rejected("LEDGER_CORRUPT")

    def _admit_adapter(
        self, record: InstallationRecordSnapshot, identity: ReleaseIdentity
    ) -> InstallationRecordSnapshot:
        """Enter the existing governed execution boundary before a report call."""

        if record.state == InstallationState.UNKNOWN:
            record = self._ledger.record_phase(
                identity, record.installation_id, InstallationState.READY
            )
        if record.state == InstallationState.READY:
            record = self._ledger.record_phase(
                identity, record.installation_id, InstallationState.INSTALLING
            )
        return record

    def _record_operator_block(
        self,
        record: InstallationRecordSnapshot,
        disposition: RecoveryDisposition,
        condition: OperatorBlockCondition,
        adapter_invoked: bool = False,
        admission_kind: AdmissionKind | None = None,
    ) -> ProvisioningInvocationResult:
        """Map a block to an existing failure state; never create ``BLOCKED``."""

        failure_state = (
            InstallationState.PRECHECK_FAILED
            if condition.stage == OperatorBlockStage.PREFLIGHT
            or record.state == InstallationState.UNKNOWN
            else InstallationState.FAILED
        )
        reason = self._redacted_reason(condition.failure)
        updated = self._ledger.mark_failure(
            record.identity,
            record.installation_id,
            reason,
            failure_state,
        )
        return self._result(
            updated,
            disposition,
            adapter_invoked,
            False,
            condition.failure.code,
            admission_kind=admission_kind,
        )

    def _record_adapter_step_result(
        self,
        record: InstallationRecordSnapshot,
        identity: ReleaseIdentity,
        phase_name: str,
        outcome: str,
        postcondition_name: str | None = None,
    ) -> InstallationRecordSnapshot:
        """Persist one redacted adapter outcome before handling its result."""

        return self._ledger.record_step_result(
            identity,
            record.installation_id,
            self._adapter_step_id(phase_name, postcondition_name),
            outcome,
        )

    @staticmethod
    def _adapter_step_id(phase_name: str, postcondition_name: str | None = None) -> str:
        """Derive a stable, non-secret ledger step identifier from contract names."""

        suffix = postcondition_name or "adapter-report"
        return f"adapter:{phase_name}:postcondition:{suffix}"

    @classmethod
    def _navigation_step_id(cls) -> str:
        return cls._adapter_step_id(
            NAVIGATION_PROVISIONING_PHASE, NAVIGATION_POSTCONDITION_NAME
        )

    @classmethod
    def _classify_resume_admission(
        cls,
        record: InstallationRecordSnapshot,
        invocation: ProvisioningInvocation,
    ) -> tuple[AdmissionKind, str | None]:
        """Distinguish first-runtime, baseline-recovery, and evidence-bound resume.

        Admission kinds are administrative classifications only. They do not write
        lifecycle states, invent step markers, or waive adapter evidence.
        """

        if cls._is_first_runtime_admission_candidate(record, invocation):
            evidence_failure = cls._first_runtime_evidence_failure(record, invocation)
            if evidence_failure is not None:
                return AdmissionKind.FIRST_RUNTIME_ADMISSION, evidence_failure
            return AdmissionKind.FIRST_RUNTIME_ADMISSION, None

        if cls._is_baseline_recovery_admission_candidate(record, invocation):
            evidence_failure = cls._first_runtime_evidence_failure(record, invocation)
            if evidence_failure is not None:
                return AdmissionKind.BASELINE_RECOVERY_ADMISSION, evidence_failure
            return AdmissionKind.BASELINE_RECOVERY_ADMISSION, None

        if cls._resume_is_validated(
            record, invocation.phase_name, invocation.resume_postcondition
        ):
            return AdmissionKind.RESUME, None

        return AdmissionKind.RESUME, "RESUME_POSTCONDITION_UNVERIFIED"

    @classmethod
    def _is_first_runtime_admission_candidate(
        cls,
        record: InstallationRecordSnapshot,
        invocation: ProvisioningInvocation,
    ) -> bool:
        if record.state != InstallationState.REGISTERED:
            return False
        if invocation.phase_name != NAVIGATION_PROVISIONING_PHASE:
            return False
        if invocation.target_phase != InstallationState.HOOK_PENDING:
            return False
        step_id = cls._navigation_step_id()
        return not any(
            event.kind == "step" and event.value == step_id for event in record.events
        )

    @classmethod
    def _is_baseline_recovery_admission_candidate(
        cls,
        record: InstallationRecordSnapshot,
        invocation: ProvisioningInvocation,
    ) -> bool:
        """Admit navigation after baseline prep when a prior navigation attempt failed."""

        if record.state != InstallationState.REGISTERED:
            return False
        if invocation.phase_name != NAVIGATION_PROVISIONING_PHASE:
            return False
        if invocation.target_phase != InstallationState.HOOK_PENDING:
            return False
        nav_step = cls._navigation_step_id()
        has_failed_navigation = any(
            event.kind == "step"
            and event.value == nav_step
            and event.outcome == "failed"
            for event in record.events
        )
        has_succeeded_navigation = any(
            event.kind == "step"
            and event.value == nav_step
            and event.outcome == "succeeded"
            for event in record.events
        )
        has_succeeded_baseline = any(
            event.kind == "step"
            and event.value == BASELINE_STEP_ID
            and event.outcome == "succeeded"
            for event in record.events
        )
        return (
            has_failed_navigation
            and has_succeeded_baseline
            and not has_succeeded_navigation
        )

    @staticmethod
    def _first_runtime_evidence_failure(
        record: InstallationRecordSnapshot,
        invocation: ProvisioningInvocation,
    ) -> str | None:
        evidence = invocation.dependency_evidence
        if evidence is None:
            return "NAVIGATION_DEPENDENCY_UNAVAILABLE"
        if evidence.installation_id != record.installation_id:
            return "NAVIGATION_DEPENDENCY_UNAVAILABLE"
        if evidence.identity != invocation.identity or evidence.identity != record.identity:
            return "NAVIGATION_DEPENDENCY_UNAVAILABLE"
        if not evidence.extension_registered:
            return "NAVIGATION_DEPENDENCY_UNAVAILABLE"
        if not NAVIGATION_REQUIRED_MODULES.issubset(evidence.available_modules):
            return "NAVIGATION_DEPENDENCY_UNAVAILABLE"
        return None

    @staticmethod
    def _admission_failure_summary(failure_code: str) -> str:
        if failure_code == "NAVIGATION_DEPENDENCY_UNAVAILABLE":
            return "approved dependency evidence is absent or invalid"
        return "resume postcondition is not validated"

    @classmethod
    def _resume_is_validated(
        cls,
        record: InstallationRecordSnapshot,
        phase_name: str,
        postcondition: PhasePostcondition | None,
    ) -> bool:
        return bool(
            postcondition
            and postcondition.satisfied
            and postcondition.name.strip()
            and postcondition.evidence.strip()
            and any(
                event.kind == "step"
                and event.value == cls._adapter_step_id(phase_name, postcondition.name)
                and event.outcome == "succeeded"
                for event in record.events
            )
        )

    @staticmethod
    def _invocation_failure(invocation: ProvisioningInvocation) -> str | None:
        if not invocation.phase_name.strip():
            return "INVOCATION_PHASE_INVALID"
        if not invocation.idempotency.key.strip():
            return "INVOCATION_IDEMPOTENCY_INVALID"
        if invocation.target_phase not in ProvisioningOrchestrator._ADAPTER_TARGETS:
            return "PHASE_TARGET_NOT_AUTHORIZED"
        return None

    @staticmethod
    def _redacted_reason(failure: RedactedFailure) -> str:
        code = failure.code.strip()
        summary = failure.summary.strip()
        if (
            not code
            or not summary
            or not all(character.isupper() or character.isdigit() or character == "_" for character in code)
            or "\n" in summary
            or "\r" in summary
        ):
            return "INVALID_REDACTED_FAILURE: redacted failure was invalid"
        return f"{code}: {summary}"

    @staticmethod
    def _result(
        record: InstallationRecordSnapshot | None,
        disposition: RecoveryDisposition | None,
        adapter_invoked: bool,
        completed_noop: bool,
        failure_code: str | None = None,
        admission_kind: AdmissionKind | None = None,
    ) -> ProvisioningInvocationResult:
        return ProvisioningInvocationResult(
            installation_id=record.installation_id if record else None,
            state=record.state if record else None,
            recovery_disposition=disposition,
            adapter_invoked=adapter_invoked,
            completed_noop=completed_noop,
            failure_code=failure_code,
            admission_kind=admission_kind,
        )

    @staticmethod
    def _rejected(failure_code: str) -> ProvisioningInvocationResult:
        return ProvisioningInvocationResult(
            installation_id=None,
            state=None,
            recovery_disposition=None,
            adapter_invoked=False,
            completed_noop=False,
            failure_code=failure_code,
        )
