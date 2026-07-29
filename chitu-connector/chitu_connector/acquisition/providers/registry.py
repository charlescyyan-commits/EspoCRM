"""Controlled in-memory resolution of CRM-authorized capability bindings.

This registry deliberately does not discover providers, resolve credentials,
construct transports, or invoke adapters.  It evaluates only the bindings and
availability information supplied by the CRM governance boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from ..models import ProviderError
from .capabilities import Capability
from .taxonomy import ClassifiedError, classify_provider_error


class ProviderHealthState(Enum):
    """Health input supplied by governance; this registry never probes it."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    """A connector-known adapter descriptor, without a live adapter instance."""

    provider_id: str
    adapter_type: str
    supported_capabilities: frozenset[Capability]


@dataclass(frozen=True, slots=True)
class ProviderBinding:
    """A CRM-authorized provider candidate and its non-secret policy metadata."""

    provider_id: str
    adapter_type: str
    priority: int
    enabled: bool
    credential_reference: str | None
    supported_capabilities: frozenset[Capability]
    health_state: ProviderHealthState
    allowed_purposes: frozenset[str]


@dataclass(frozen=True, slots=True)
class CapabilityResolutionRequest:
    """All resolution inputs supplied by the CRM policy boundary."""

    capability: Capability
    purpose: str
    allowed_provider_bindings: tuple[ProviderBinding, ...]
    credential_availability: Mapping[str, bool]
    provider_health: Mapping[str, ProviderHealthState]
    policy_version: str
    request_context: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ProviderCandidateEvaluation:
    """Safe audit evidence for one CRM-authorized candidate."""

    provider_id: str
    eligible: bool
    skipped_reason: str | None
    priority: int
    health_state: ProviderHealthState
    credential_available: bool


@dataclass(frozen=True, slots=True)
class CapabilityResolutionResult:
    """The deterministic selection and its complete non-secret evaluation trace."""

    requested_capability: Capability
    purpose: str
    selected_provider_id: str
    selected_adapter_type: str
    selected_credential_reference: str
    policy_version: str
    candidate_evaluations: tuple[ProviderCandidateEvaluation, ...]
    fallback_occurred: bool
    resolution_reason: str


class CapabilityRegistry:
    """Resolve only CRM-authorized bindings to pre-registered adapter descriptors."""

    def __init__(self, registrations: tuple[AdapterRegistration, ...] = ()) -> None:
        self._registrations: dict[str, AdapterRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: AdapterRegistration) -> None:
        _validate_registration(registration)
        if registration.provider_id in self._registrations:
            raise _controlled_error(
                "DUPLICATE_PROVIDER_ID",
                "Provider registration is already present",
                400,
            )
        self._registrations[registration.provider_id] = registration

    def resolve(self, request: CapabilityResolutionRequest) -> CapabilityResolutionResult:
        _validate_request(request)
        evaluations: list[ProviderCandidateEvaluation] = []
        eligible: list[tuple[ProviderBinding, ProviderCandidateEvaluation]] = []

        for binding in sorted(request.allowed_provider_bindings, key=lambda item: (item.priority, item.provider_id)):
            health_state = request.provider_health.get(binding.provider_id, binding.health_state)
            evaluation = self._evaluate(binding, request, health_state)
            evaluations.append(evaluation)
            if evaluation.eligible:
                eligible.append((binding, evaluation))

        trace = tuple(evaluations)
        if not eligible:
            raise _controlled_error(
                "CAPABILITY_UNAVAILABLE",
                "No CRM-authorized provider is available for the requested capability",
                503,
                trace,
            )

        selected_binding, selected_evaluation = min(
            eligible,
            key=lambda item: (_health_rank(item[1].health_state), item[0].priority, item[0].provider_id),
        )
        fallback_occurred = bool(trace) and trace[0].provider_id != selected_binding.provider_id
        reason = (
            "primary eligible candidate selected"
            if not fallback_occurred
            else "fallback selected after a higher-precedence candidate was ineligible or degraded"
        )
        return CapabilityResolutionResult(
            requested_capability=request.capability,
            purpose=request.purpose,
            selected_provider_id=selected_binding.provider_id,
            selected_adapter_type=selected_binding.adapter_type,
            selected_credential_reference=selected_binding.credential_reference or "",
            policy_version=request.policy_version,
            candidate_evaluations=trace,
            fallback_occurred=fallback_occurred,
            resolution_reason=reason,
        )

    def _evaluate(
        self,
        binding: ProviderBinding,
        request: CapabilityResolutionRequest,
        health_state: ProviderHealthState,
    ) -> ProviderCandidateEvaluation:
        credential_available = bool(
            binding.credential_reference
            and request.credential_availability.get(binding.credential_reference, False)
        )
        skipped_reason = _ineligibility_reason(
            binding,
            request,
            health_state,
            credential_available,
            self._registrations.get(binding.provider_id),
        )
        return ProviderCandidateEvaluation(
            provider_id=binding.provider_id,
            eligible=skipped_reason is None,
            skipped_reason=skipped_reason,
            priority=binding.priority,
            health_state=health_state,
            credential_available=credential_available,
        )


def _ineligibility_reason(
    binding: ProviderBinding,
    request: CapabilityResolutionRequest,
    health_state: ProviderHealthState,
    credential_available: bool,
    registration: AdapterRegistration | None,
) -> str | None:
    if not binding.enabled:
        return "PROVIDER_DISABLED"
    if registration is None:
        return "ADAPTER_NOT_REGISTERED"
    if registration.adapter_type != binding.adapter_type:
        return "ADAPTER_TYPE_MISMATCH"
    if request.capability not in binding.supported_capabilities:
        return "BINDING_CAPABILITY_UNSUPPORTED"
    if request.capability not in registration.supported_capabilities:
        return "ADAPTER_CAPABILITY_UNSUPPORTED"
    if request.purpose not in binding.allowed_purposes:
        return "PURPOSE_NOT_ALLOWED"
    if not binding.credential_reference:
        return "MISSING_CREDENTIAL_REFERENCE"
    if not credential_available:
        return "CREDENTIAL_UNAVAILABLE"
    if health_state is ProviderHealthState.UNHEALTHY:
        return "PROVIDER_UNHEALTHY"
    if health_state is ProviderHealthState.UNKNOWN:
        return "PROVIDER_HEALTH_UNKNOWN"
    return None


def _health_rank(health_state: ProviderHealthState) -> int:
    return 0 if health_state is ProviderHealthState.HEALTHY else 1


def _validate_registration(registration: AdapterRegistration) -> None:
    if not registration.provider_id.strip() or not registration.adapter_type.strip() or not registration.supported_capabilities:
        raise _controlled_error("INVALID_PROVIDER_REGISTRATION", "Provider registration is incomplete", 400)


def _validate_request(request: CapabilityResolutionRequest) -> None:
    if not isinstance(request.capability, Capability):
        raise _controlled_error("INVALID_CAPABILITY", "Requested capability is not recognized", 400)
    if not request.purpose.strip() or not request.policy_version.strip():
        raise _controlled_error("INVALID_RESOLUTION_REQUEST", "Purpose and policy version are required", 400)
    provider_ids = [binding.provider_id for binding in request.allowed_provider_bindings]
    if len(provider_ids) != len(set(provider_ids)):
        raise _controlled_error("DUPLICATE_PROVIDER_BINDING", "Provider bindings must have unique provider IDs", 400)
    for binding in request.allowed_provider_bindings:
        if (
            not binding.provider_id.strip()
            or not binding.adapter_type.strip()
            or not isinstance(binding.priority, int)
            or not isinstance(binding.health_state, ProviderHealthState)
        ):
            raise _controlled_error("INVALID_PROVIDER_BINDING", "Provider binding is incomplete", 400)
    if any(not isinstance(health_state, ProviderHealthState) for health_state in request.provider_health.values()):
        raise _controlled_error("INVALID_PROVIDER_HEALTH", "Provider health input is not recognized", 400)
    if _contains_secret_field(request.request_context):
        raise _controlled_error("SECRET_IN_RESOLUTION_INPUT", "Resolution input must not contain a secret field", 400)


def _contains_secret_field(value: object) -> bool:
    forbidden = {
        "apikey",
        "apisecret",
        "token",
        "password",
        "plaintextcredential",
        "encryptedsecret",
        "decryptedvalue",
        "credentialreference",
    }
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = "".join(character for character in str(key).casefold() if character.isalnum())
            if normalized in forbidden or _contains_secret_field(nested):
                return True
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_secret_field(item) for item in value)
    return False


def _controlled_error(
    code: str,
    safe_message: str,
    status_code: int,
    evaluations: tuple[ProviderCandidateEvaluation, ...] = (),
) -> ProviderError:
    classified: ClassifiedError = classify_provider_error(status_code, code)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    error.candidate_evaluations = evaluations
    return error
