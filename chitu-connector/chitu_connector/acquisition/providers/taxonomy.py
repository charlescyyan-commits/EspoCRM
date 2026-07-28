"""Pure mapping for the ADR-C20 provider-error taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorClass(Enum):
    """ADR-C20 section 4.3 normalized provider-error classes."""

    NETWORK = "NETWORK"
    PROVIDER = "PROVIDER"
    AUTH = "AUTH"
    VALIDATION = "VALIDATION"
    UNKNOWN = "UNKNOWN"
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA = "QUOTA"
    CONTENT_FILTER = "CONTENT_FILTER"


@dataclass(frozen=True, slots=True)
class ClassifiedError:
    """A safe, normalized provider error with retry guidance."""

    error_class: ErrorClass
    provider_code: str
    safe_message: str
    retryable: bool
    retry_after: int | None = None


_RETRYABLE_CLASSES = frozenset({
    ErrorClass.NETWORK,
    ErrorClass.PROVIDER,
    ErrorClass.RATE_LIMIT,
})


def classify_provider_error(
    status_code: int,
    provider_error_code: str | None = None,
    *,
    retry_after: int | None = None,
) -> ClassifiedError:
    """Map a status and optional safe provider code to the C20 taxonomy.

    The function is deliberately pure: it neither calls a provider nor reads
    configuration.  Provider error codes are normalized before they are
    returned so an arbitrary raw response string cannot become log output.
    """

    code = _normalize_code(provider_error_code) or f"HTTP_{status_code}"
    error_class = _classify(status_code, code)
    return ClassifiedError(
        error_class=error_class,
        provider_code=code,
        safe_message=_safe_message(error_class),
        retryable=error_class in _RETRYABLE_CLASSES,
        retry_after=retry_after if error_class is ErrorClass.RATE_LIMIT else None,
    )


def _classify(status_code: int, provider_code: str) -> ErrorClass:
    if "CONTENT_FILTER" in provider_code:
        return ErrorClass.CONTENT_FILTER
    if "QUOTA" in provider_code or "INSUFFICIENT_CREDITS" in provider_code:
        return ErrorClass.QUOTA
    if status_code in {0, 408, 504}:
        return ErrorClass.NETWORK
    if status_code in {401, 403}:
        return ErrorClass.AUTH
    if status_code == 402:
        return ErrorClass.QUOTA
    if status_code == 429:
        return ErrorClass.RATE_LIMIT
    if 500 <= status_code <= 599:
        return ErrorClass.PROVIDER
    if 400 <= status_code <= 499:
        return ErrorClass.VALIDATION
    return ErrorClass.UNKNOWN


def _normalize_code(value: str | None) -> str:
    if not value:
        return ""
    return "".join(character if character.isalnum() else "_" for character in value.upper()).strip("_")


def _safe_message(error_class: ErrorClass) -> str:
    return {
        ErrorClass.NETWORK: "Provider network request failed.",
        ErrorClass.PROVIDER: "Provider service failed.",
        ErrorClass.AUTH: "Provider authentication failed.",
        ErrorClass.VALIDATION: "Provider request was invalid.",
        ErrorClass.UNKNOWN: "Provider request failed with an unknown error.",
        ErrorClass.RATE_LIMIT: "Provider rate limit reached.",
        ErrorClass.QUOTA: "Provider quota is unavailable.",
        ErrorClass.CONTENT_FILTER: "Provider content filter rejected the request.",
    }[error_class]
