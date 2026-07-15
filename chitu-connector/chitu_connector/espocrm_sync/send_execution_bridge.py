"""C14.3.1B-1 connector-domain contract for bridging CRM SendExecution records.

This module deliberately defines data contracts only. It does not import or
invoke the C13 queue/worker, C12 providers, Brevo transport, or CRM runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import re
from threading import RLock
from typing import Protocol


BRIDGE_CONTRACT_VERSION = "phase3c14.3.1b1-send-execution-bridge-v1"
_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$")
_SAFE_ERROR_CODE = re.compile(r"^[A-Z0-9_:-]+$")


class BridgeNormalizedStatus(str, Enum):
    """Terminal outcome returned to the future CRM-side bridge."""

    SENT = "SENT"
    FAILED = "FAILED"


class BridgeErrorClass(str, Enum):
    """Failure classes compatible with the C14.2B terminal mapping."""

    NETWORK = "NETWORK"
    AUTH = "AUTH"
    VALIDATION = "VALIDATION"
    PROVIDER = "PROVIDER"
    UNKNOWN = "UNKNOWN"


def generate_idempotency_key(execution_id: str) -> str:
    """Return a stable, opaque key for one CRM SendExecution identity."""

    normalized_execution_id = _require_text("execution_id", execution_id)
    material = (BRIDGE_CONTRACT_VERSION + ":" + normalized_execution_id).encode("utf-8")
    return sha256(material).hexdigest()


def hash_recipient_reference(recipient: str) -> str:
    """Hash a recipient at an authorized ingress without retaining it."""

    normalized_recipient = _require_text("recipient", recipient).casefold()
    return sha256(normalized_recipient.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SendExecutionBridgeRequest:
    """Safe contract payload; no raw recipient, content, or credentials."""

    execution_id: str
    idempotency_key: str
    content_hash: str
    recipient_hash: str
    campaign_reference: str
    created_at: datetime

    def __post_init__(self) -> None:
        execution_id = _require_text("execution_id", self.execution_id)
        _require_text("campaign_reference", self.campaign_reference)
        _require_hash("content_hash", self.content_hash)
        _require_hash("recipient_hash", self.recipient_hash)
        _require_aware_timestamp("created_at", self.created_at)
        if self.idempotency_key != generate_idempotency_key(execution_id):
            raise ValueError("idempotency_key must be the stable key for execution_id")


@dataclass(frozen=True, slots=True)
class SendExecutionBridgeResult:
    """Terminal outcome. This contract never makes a retry decision."""

    execution_id: str
    provider_attempt_id: str | None
    normalized_status: BridgeNormalizedStatus
    error_class: BridgeErrorClass | None
    error_code: str | None
    occurred_at: datetime

    def __post_init__(self) -> None:
        _require_text("execution_id", self.execution_id)
        _require_aware_timestamp("occurred_at", self.occurred_at)
        if self.provider_attempt_id is not None:
            _require_text("provider_attempt_id", self.provider_attempt_id)

        if self.normalized_status is BridgeNormalizedStatus.SENT:
            if self.error_class is not None or self.error_code is not None:
                raise ValueError("SENT results must not include an error")
            return
        if self.normalized_status is BridgeNormalizedStatus.FAILED:
            if self.error_class is None:
                raise ValueError("FAILED results require error_class")
            _require_error_code(self.error_code)
            return
        raise ValueError("normalized_status must be a supported terminal status")

    @classmethod
    def terminal_failure(
        cls,
        *,
        execution_id: str,
        error_class: BridgeErrorClass,
        error_code: str,
        occurred_at: datetime,
        provider_attempt_id: str | None = None,
    ) -> "SendExecutionBridgeResult":
        """Preserve a provider terminal error, such as BREVO_NETWORK_ERROR."""

        return cls(
            execution_id=execution_id,
            provider_attempt_id=provider_attempt_id,
            normalized_status=BridgeNormalizedStatus.FAILED,
            error_class=error_class,
            error_code=error_code,
            occurred_at=occurred_at,
        )


@dataclass(frozen=True, slots=True)
class SendExecutionBridgeReceipt:
    """Acknowledgement from a bridge adapter; no queue implementation is implied."""

    execution_id: str
    idempotency_key: str
    duplicate: bool


class SendExecutionBridgeAdapter(Protocol):
    """Boundary between a CRM-side bridge and a future execution path."""

    def enqueue(self, request: SendExecutionBridgeRequest) -> SendExecutionBridgeReceipt:
        """Accept a safe request exactly once for an execution identity."""

    def record_result(self, result: SendExecutionBridgeResult) -> SendExecutionBridgeResult:
        """Accept one terminal result for a previously enqueued execution."""


class InMemorySendExecutionBridgeFixture:
    """Deterministic test double, not a Queue or Worker implementation."""

    def __init__(self) -> None:
        self._requests: dict[str, SendExecutionBridgeRequest] = {}
        self._results: dict[str, SendExecutionBridgeResult] = {}
        self._lock = RLock()

    def enqueue(self, request: SendExecutionBridgeRequest) -> SendExecutionBridgeReceipt:
        with self._lock:
            existing = self._requests.get(request.execution_id)
            if existing is None:
                self._requests[request.execution_id] = request
                return SendExecutionBridgeReceipt(
                    execution_id=request.execution_id,
                    idempotency_key=request.idempotency_key,
                    duplicate=False,
                )
            if existing.idempotency_key != request.idempotency_key:
                raise ValueError("execution_id cannot be associated with another key")
            return SendExecutionBridgeReceipt(
                execution_id=request.execution_id,
                idempotency_key=existing.idempotency_key,
                duplicate=True,
            )

    def record_result(self, result: SendExecutionBridgeResult) -> SendExecutionBridgeResult:
        with self._lock:
            if result.execution_id not in self._requests:
                raise KeyError("result requires a previously enqueued execution")
            existing = self._results.get(result.execution_id)
            if existing is None:
                self._results[result.execution_id] = result
                return result
            if existing != result:
                raise ValueError("execution already has a different terminal result")
            return existing

    def request_for(self, execution_id: str) -> SendExecutionBridgeRequest | None:
        with self._lock:
            return self._requests.get(execution_id)

    def result_for(self, execution_id: str) -> SendExecutionBridgeResult | None:
        with self._lock:
            return self._results.get(execution_id)


def _require_text(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field_name + " must be a non-empty string")
    return value.strip()


def _require_hash(field_name: str, value: str) -> None:
    if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
        raise ValueError(field_name + " must be a lower-case SHA-256 hex digest")


def _require_aware_timestamp(field_name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(field_name + " must be a timezone-aware datetime")


def _require_error_code(value: str | None) -> None:
    if not isinstance(value, str) or _SAFE_ERROR_CODE.fullmatch(value) is None:
        raise ValueError("error_code must be a non-secret upper-case error identifier")
