"""Offline failure-classification contract for SendExecution reservation.

The functions in this module classify already-observed failure facts. They do
not make network requests, schedule retries, submit sends, or mutate CRM data.
"""

from __future__ import annotations

from enum import StrEnum


class FailureCategory(StrEnum):
    NETWORK = "NETWORK"
    PROVIDER = "PROVIDER"
    AUTH = "AUTH"
    RATE_LIMIT = "RATE_LIMIT"
    VALIDATION = "VALIDATION"
    UNKNOWN = "UNKNOWN"


_NETWORK_CODES = frozenset({"CONNECTION_RESET", "CONNECTION_TIMEOUT", "DNS_FAILURE", "TIMEOUT"})
_VALIDATION_CODES = frozenset({"INVALID_PAYLOAD", "INVALID_REQUEST", "VALIDATION_ERROR"})


def classify_failure(*, status_code: int | None = None, error_code: str | None = None) -> FailureCategory:
    """Map a normalized local failure signal to a persistence-safe category."""

    if status_code in {401, 403}:
        return FailureCategory.AUTH
    if status_code == 429:
        return FailureCategory.RATE_LIMIT
    normalized_code = error_code.strip().upper() if isinstance(error_code, str) else ""
    if normalized_code in _NETWORK_CODES:
        return FailureCategory.NETWORK
    if normalized_code in _VALIDATION_CODES:
        return FailureCategory.VALIDATION
    if isinstance(status_code, int) and 500 <= status_code <= 599:
        return FailureCategory.PROVIDER
    return FailureCategory.UNKNOWN


def normalize_failure_category(value: object) -> FailureCategory:
    """Accept only reserved schema values and safely fall back to UNKNOWN."""

    if isinstance(value, FailureCategory):
        return value
    if isinstance(value, str):
        try:
            return FailureCategory(value.strip().upper())
        except ValueError:
            pass
    return FailureCategory.UNKNOWN
