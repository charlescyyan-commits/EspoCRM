"""Brevo implementation of the C12.1 provider contract.

Sending occurs only if an explicit caller supplies a configured adapter and
invokes send. This module does not start work, read credentials outside its
configuration boundary, or mutate CRM/lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from threading import RLock
from typing import Mapping

from chitu_connector.espocrm_sync.brevo_http import BrevoHttpClient, BrevoHttpResponse, BrevoTransportError
from chitu_connector.espocrm_sync.provider_contract import (
    ProviderError,
    ProviderErrorCategory,
    ProviderStatus,
    SendRequest,
    SendResult,
    SendResultStatus,
    validate_send_request,
)


@dataclass(frozen=True, slots=True)
class BrevoConfiguration:
    """Environment-backed configuration. Secrets are redacted from repr."""

    api_key: str | None = field(repr=False)
    sender_email: str | None
    sender_name: str | None = None
    acceptance_mode: bool = False
    test_recipient: str | None = field(default=None, repr=False)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "BrevoConfiguration":
        values = os.environ if environment is None else environment
        return cls(
            api_key=_optional_value(values.get("BREVO_API_KEY")),
            sender_email=_optional_value(values.get("BREVO_SENDER_EMAIL")),
            sender_name=_optional_value(values.get("BREVO_SENDER_NAME")),
            acceptance_mode=_is_acceptance_mode(values.get("BREVO_ACCEPTANCE_MODE")),
            test_recipient=_optional_value(values.get("BREVO_TEST_RECIPIENT")),
        )

    def missing_configuration_code(self) -> str | None:
        if not self.api_key:
            return "MISSING_BREVO_API_KEY"
        if not self.sender_email:
            return "MISSING_BREVO_SENDER_EMAIL"
        if self.acceptance_mode and not self.test_recipient:
            return "ACCEPTANCE_RECIPIENT_NOT_CONFIGURED"
        return None

    def resolve_recipient(self, request_recipient: str) -> str:
        """Return the configured acceptance recipient or preserve production input."""

        return self.test_recipient if self.acceptance_mode and self.test_recipient else request_recipient


class BrevoProviderAdapter:
    """Transactional-email adapter with explicit configuration and transport seams."""

    def __init__(
        self,
        configuration: BrevoConfiguration,
        http_client: BrevoHttpClient,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._configuration = configuration
        self._http_client = http_client
        self._timeout_seconds = timeout_seconds
        self._results_by_identity: dict[tuple[str, str], SendResult] = {}
        self._request_to_execution: dict[str, str] = {}
        self._execution_to_request: dict[str, str] = {}
        self._lock = RLock()

    def send(self, request: SendRequest) -> SendResult:
        invalid = validate_send_request(request)
        if invalid is not None:
            return _failure(SendResultStatus.PERMANENT_FAILURE, invalid, "INVALID_SEND_REQUEST")
        assert isinstance(request, SendRequest)
        missing_configuration = self._configuration.missing_configuration_code()
        if missing_configuration is not None:
            return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.VALIDATION_ERROR, missing_configuration)
        identity = (request.send_execution_id, request.request_id)
        with self._lock:
            cached = self._results_by_identity.get(identity)
            if cached is not None:
                return cached
            if self._has_identity_conflict(request):
                return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.VALIDATION_ERROR, "IDENTITY_CONFLICT")
            result = self._send_once(request)
            self._results_by_identity[identity] = result
            self._request_to_execution[request.request_id] = request.send_execution_id
            self._execution_to_request[request.send_execution_id] = request.request_id
            return result

    def get_status(self, provider_message_id: str) -> ProviderStatus:
        """No transactional-message status lookup is available in this contract."""

        return ProviderStatus.NOT_SUPPORTED

    def _send_once(self, request: SendRequest) -> SendResult:
        try:
            response = self._http_client.post_json(
                "/smtp/email",
                headers={"api-key": self._configuration.api_key or ""},
                payload=_payload(request, self._configuration),
                timeout_seconds=self._timeout_seconds,
            )
        except (BrevoTransportError, TimeoutError):
            return _failure(SendResultStatus.RETRYABLE_FAILURE, ProviderErrorCategory.NETWORK_ERROR, "BREVO_NETWORK_ERROR")
        except Exception:
            return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.UNKNOWN_ERROR, "BREVO_TRANSPORT_UNKNOWN")
        return _result_from_response(response)

    def _has_identity_conflict(self, request: SendRequest) -> bool:
        return (
            self._request_to_execution.get(request.request_id) not in {None, request.send_execution_id}
            or self._execution_to_request.get(request.send_execution_id) not in {None, request.request_id}
        )


def _payload(request: SendRequest, configuration: BrevoConfiguration) -> Mapping[str, object]:
    sender: dict[str, object] = {"email": configuration.sender_email or ""}
    if configuration.sender_name:
        sender["name"] = configuration.sender_name
    return {
        "sender": sender,
        "to": [{"email": configuration.resolve_recipient(request.recipient)}],
        "subject": request.subject,
        "htmlContent": request.body,
        "headers": {
            "X-C12-Request-Id": request.request_id,
            "X-C12-Send-Execution-Id": request.send_execution_id,
            "X-C12-Draft-Hash": request.draft_hash,
        },
    }


def _result_from_response(response: BrevoHttpResponse) -> SendResult:
    if response.status_code in {200, 201, 202}:
        message_id = response.body.get("messageId") if response.body is not None else None
        if isinstance(message_id, str) and message_id.strip():
            return SendResult(True, SendResultStatus.SUCCESS, message_id, ProviderStatus.ACCEPTED, None)
        return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.UNKNOWN_ERROR, "BREVO_MALFORMED_SUCCESS_RESPONSE")
    if response.status_code in {401, 403}:
        return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.AUTH_ERROR, "BREVO_AUTH_ERROR")
    if response.status_code == 429:
        return _failure(SendResultStatus.RETRYABLE_FAILURE, ProviderErrorCategory.RATE_LIMIT, "BREVO_RATE_LIMIT")
    if response.status_code == 400:
        return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.VALIDATION_ERROR, "BREVO_VALIDATION_ERROR")
    if 500 <= response.status_code <= 599:
        return _failure(SendResultStatus.RETRYABLE_FAILURE, ProviderErrorCategory.PROVIDER_ERROR, "BREVO_PROVIDER_ERROR")
    return _failure(SendResultStatus.PERMANENT_FAILURE, ProviderErrorCategory.UNKNOWN_ERROR, "BREVO_UNKNOWN_RESPONSE")


def _failure(status: SendResultStatus, category: ProviderErrorCategory, safe_code: str) -> SendResult:
    return SendResult(False, status, None, ProviderStatus.FAILED, ProviderError(category, safe_code))


def _optional_value(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _is_acceptance_mode(value: object) -> bool:
    return isinstance(value, str) and value.strip().casefold() == "true"
