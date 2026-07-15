"""Offline C12.1 contract between lifecycle records and a future email provider.

The module defines request, result, status, and error shapes only.  It has no
HTTP, SMTP, credential, queue, worker, CRM, or lifecycle-transition behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Mapping, Protocol

from chitu_connector.espocrm_sync.failure_classification import FailureCategory


class SendResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"


class ProviderStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    FAILED = "FAILED"


class ProviderErrorCategory(StrEnum):
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK_ERROR = "NETWORK_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class FakeProviderMode(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True)
class ProviderError:
    """Sanitized error trace; it intentionally has no raw provider payload."""

    category: ProviderErrorCategory
    safe_code: str


@dataclass(frozen=True, slots=True)
class SendRequest:
    """Immutable provider-bound request; content is excluded from repr/logging."""

    request_id: str
    send_execution_id: str
    recipient: str = field(repr=False)
    subject: str = field(repr=False)
    body: str = field(repr=False)
    metadata: Mapping[str, object] = field(default_factory=dict, repr=False)
    draft_hash: str = ""
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SendResult:
    """Provider outcome carrying only safe status and error identifiers."""

    success: bool
    status: SendResultStatus
    provider_message_id: str | None
    provider_status: ProviderStatus
    error: ProviderError | None


class ProviderAdapter(Protocol):
    """Stable future provider seam, independent of C10/C11 state transitions."""

    def send(self, request: SendRequest) -> SendResult: ...

    def get_status(self, provider_message_id: str) -> ProviderStatus: ...


class FakeProviderAdapter:
    """Deterministic, network-free adapter used only for contract verification."""

    def __init__(
        self,
        *,
        mode: FakeProviderMode = FakeProviderMode.SUCCESS,
        failure_category: ProviderErrorCategory = ProviderErrorCategory.PROVIDER_ERROR,
    ) -> None:
        self._mode = mode
        self._failure_category = failure_category
        self._results_by_identity: dict[tuple[str, str], SendResult] = {}
        self._request_to_execution: dict[str, str] = {}
        self._execution_to_request: dict[str, str] = {}
        self._status_by_message_id: dict[str, ProviderStatus] = {}
        self._send_call_count = 0
        self._lock = RLock()

    @property
    def send_call_count(self) -> int:
        with self._lock:
            return self._send_call_count

    @property
    def external_request_count(self) -> int:
        """Always zero: this fake adapter does not have an external transport."""

        return 0

    def send(self, request: SendRequest) -> SendResult:
        validation_error = validate_send_request(request)
        if validation_error is not None:
            return _failure(SendResultStatus.PERMANENT_FAILURE, validation_error)
        assert isinstance(request, SendRequest)
        identity = (request.send_execution_id, request.request_id)
        with self._lock:
            cached = self._results_by_identity.get(identity)
            if cached is not None:
                return cached
            if self._has_identity_conflict(request):
                return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.VALIDATION_ERROR, "IDENTITY_CONFLICT")
            self._send_call_count += 1
            result = self._result_for_mode(request)
            self._results_by_identity[identity] = result
            self._request_to_execution[request.request_id] = request.send_execution_id
            self._execution_to_request[request.send_execution_id] = request.request_id
            if result.provider_message_id is not None:
                self._status_by_message_id[result.provider_message_id] = result.provider_status
            return result

    def get_status(self, provider_message_id: str) -> ProviderStatus:
        if not isinstance(provider_message_id, str) or not provider_message_id.strip():
            return ProviderStatus.UNKNOWN
        with self._lock:
            return self._status_by_message_id.get(provider_message_id, ProviderStatus.UNKNOWN)

    def _has_identity_conflict(self, request: SendRequest) -> bool:
        return (
            self._request_to_execution.get(request.request_id) not in {None, request.send_execution_id}
            or self._execution_to_request.get(request.send_execution_id) not in {None, request.request_id}
        )

    def _result_for_mode(self, request: SendRequest) -> SendResult:
        if self._mode is FakeProviderMode.SUCCESS:
            message_id = f"fake:{request.send_execution_id}:{request.request_id}"
            return SendResult(True, SendResultStatus.SUCCESS, message_id, ProviderStatus.SENT, None)
        if self._mode is FakeProviderMode.TIMEOUT:
            return _failure(SendResultStatus.RETRYABLE_FAILURE, ProviderErrorCategory.NETWORK_ERROR, "SIMULATED_TIMEOUT")
        status = (
            SendResultStatus.RETRYABLE_FAILURE
            if self._failure_category in {ProviderErrorCategory.NETWORK_ERROR, ProviderErrorCategory.RATE_LIMIT}
            else SendResultStatus.PERMANENT_FAILURE
        )
        return _failure(status, self._failure_category, "SIMULATED_FAILURE")


def map_error_to_failure_category(error_category: ProviderErrorCategory) -> FailureCategory:
    """Map C12 provider taxonomy to the C11.5 persistence taxonomy."""

    return {
        ProviderErrorCategory.AUTH_ERROR: FailureCategory.AUTH,
        ProviderErrorCategory.RATE_LIMIT: FailureCategory.RATE_LIMIT,
        ProviderErrorCategory.NETWORK_ERROR: FailureCategory.NETWORK,
        ProviderErrorCategory.VALIDATION_ERROR: FailureCategory.VALIDATION,
        ProviderErrorCategory.PROVIDER_ERROR: FailureCategory.PROVIDER,
        ProviderErrorCategory.UNKNOWN_ERROR: FailureCategory.UNKNOWN,
    }[error_category]


def validate_send_request(value: object) -> ProviderErrorCategory | None:
    """Validate request shape without retaining content or contacting a provider."""

    if not isinstance(value, SendRequest):
        return ProviderErrorCategory.VALIDATION_ERROR
    for field_name in ("request_id", "send_execution_id", "recipient", "subject", "body", "draft_hash"):
        field_value = getattr(value, field_name)
        if not isinstance(field_value, str) or not field_value.strip():
            return ProviderErrorCategory.VALIDATION_ERROR
    if not isinstance(value.created_at, datetime) or value.created_at.tzinfo is None or value.created_at.utcoffset() is None:
        return ProviderErrorCategory.VALIDATION_ERROR
    if not isinstance(value.metadata, Mapping):
        return ProviderErrorCategory.VALIDATION_ERROR
    for key in value.metadata:
        if not isinstance(key, str) or _is_secret_key(key):
            return ProviderErrorCategory.VALIDATION_ERROR
    return None


def _failure(
    status: SendResultStatus,
    category: ProviderErrorCategory,
    safe_code: str = "INVALID_REQUEST",
) -> SendResult:
    return SendResult(False, status, None, ProviderStatus.FAILED, ProviderError(category, safe_code))


def _is_secret_key(value: str) -> bool:
    normalized = "".join(character for character in value.casefold() if character.isalnum())
    return any(token in normalized for token in ("apikey", "authorization", "credential", "password", "token", "secret"))
