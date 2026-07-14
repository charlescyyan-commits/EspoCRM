"""Provider-agnostic, no-side-effect adapter contract for future sending.

The adapter validates and reserves an existing C10.0-B ``SendRequest`` before
delegating to an injected provider contract. It ships no real provider and
does not send email, use credentials, or write CRM data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from typing import Protocol

from chitu_connector.espocrm_sync.send_idempotency import (
    InMemorySendIdempotencyRegistry,
    SendAttempt,
    SendIdempotencyRegistry,
    SendRequest,
    SendReservationStatus,
    validate_send_request,
)


class ProviderResultStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class SendProviderResult:
    """Provider result trace for one C10.0-B reservation.

    The provider must echo the request's idempotency key and request version.
    ``send_attempt_id`` is provider-owned and distinct from ``send_request_id``.
    """

    provider_name: str
    send_attempt_id: str
    idempotency_key: str
    request_version: str
    status: ProviderResultStatus
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class SendProviderAttemptResult:
    """Adapter output: reserved C10.0-B attempt plus preserved provider trace."""

    send_attempt: SendAttempt | None
    provider_result: SendProviderResult


class SendProviderUnavailableError(RuntimeError):
    """A provider implementation can raise this without exposing internals."""


class SendProvider(Protocol):
    """Provider seam; implementations return a trace and own no CRM behavior."""

    provider_name: str

    def submit(self, request: SendRequest, send_attempt: SendAttempt) -> SendProviderResult: ...


class SendProviderAdapter:
    """Validate, reserve, and call one provider contract exactly once per key.

    The adapter is deliberately not an executor. It has no network client,
    credential handling, email content, recipient, campaign, or CRM logic.
    A future caller must enforce the C10.1 ``READY_TO_SEND`` boundary before
    constructing its C10.0-B request.
    """

    def __init__(self, provider: SendProvider, registry: SendIdempotencyRegistry | None = None) -> None:
        self._provider = provider
        self._registry = registry or InMemorySendIdempotencyRegistry()
        self._results_by_idempotency_key: dict[str, SendProviderAttemptResult] = {}
        self._lock = RLock()

    def submit(self, request: object) -> SendProviderAttemptResult:
        error = validate_send_request(request)
        if error:
            return SendProviderAttemptResult(None, _result_from_request(request, ProviderResultStatus.REJECTED, error))
        assert isinstance(request, SendRequest)
        if _normalized_name(request.provider_name) != _normalized_name(self._provider.provider_name):
            return SendProviderAttemptResult(
                None,
                _result_from_request(request, ProviderResultStatus.REJECTED, "PROVIDER_NAME_MISMATCH"),
            )
        with self._lock:
            cached = self._results_by_idempotency_key.get(request.idempotency_key)
            if cached is not None:
                return cached
            reservation = self._registry.reserve(request)
            if reservation.status is SendReservationStatus.INVALID:
                return SendProviderAttemptResult(
                    None,
                    _result_from_request(request, ProviderResultStatus.REJECTED, reservation.reason_code or "INVALID_SEND_REQUEST"),
                )
            if reservation.status is SendReservationStatus.EXISTING:
                return SendProviderAttemptResult(
                    reservation.attempt,
                    _result_from_request(request, ProviderResultStatus.REJECTED, "DUPLICATE_REQUEST_WITHOUT_PROVIDER_TRACE"),
                )
            assert reservation.attempt is not None
            try:
                result = self._provider.submit(request, reservation.attempt)
            except SendProviderUnavailableError:
                result = _result_from_request(request, ProviderResultStatus.FAILED, "PROVIDER_UNAVAILABLE")
            except Exception:
                result = _result_from_request(request, ProviderResultStatus.FAILED, "PROVIDER_ADAPTER_FAILED")
            contract_error = validate_provider_result(request, result)
            if contract_error:
                result = _result_from_request(request, ProviderResultStatus.REJECTED, contract_error)
            output = SendProviderAttemptResult(reservation.attempt, result)
            self._results_by_idempotency_key[request.idempotency_key] = output
            return output


def validate_provider_result(request: SendRequest, result: object) -> str | None:
    """Validate trace integrity without interpreting provider-specific details."""
    if not isinstance(result, SendProviderResult):
        return "INVALID_PROVIDER_RESULT"
    if _normalized_name(result.provider_name) != _normalized_name(request.provider_name):
        return "INVALID_PROVIDER_NAME"
    if not isinstance(result.send_attempt_id, str) or not result.send_attempt_id.strip():
        return "INVALID_SEND_ATTEMPT_ID"
    if result.idempotency_key != request.idempotency_key:
        return "INVALID_IDEMPOTENCY_KEY"
    if result.request_version != request.request_version:
        return "INVALID_REQUEST_VERSION"
    if not isinstance(result.status, ProviderResultStatus):
        return "INVALID_PROVIDER_STATUS"
    if result.reason_code is not None and (not isinstance(result.reason_code, str) or not result.reason_code.strip()):
        return "INVALID_REASON_CODE"
    return None


def _result_from_request(request: object, status: ProviderResultStatus, reason_code: str) -> SendProviderResult:
    if isinstance(request, SendRequest):
        return SendProviderResult(
            provider_name=request.provider_name,
            send_attempt_id=f"adapter:{request.send_request_id}",
            idempotency_key=request.idempotency_key,
            request_version=request.request_version,
            status=status,
            reason_code=reason_code,
        )
    return SendProviderResult(
        provider_name="unknown",
        send_attempt_id="adapter:invalid-request",
        idempotency_key="",
        request_version="",
        status=status,
        reason_code=reason_code,
    )


def _normalized_name(value: object) -> str:
    return value.strip().lower() if isinstance(value, str) else ""
