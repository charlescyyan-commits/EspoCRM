from __future__ import annotations

import pytest

from chitu_connector.acquisition.providers.taxonomy import ErrorClass, classify_provider_error


@pytest.mark.parametrize(
    ("status_code", "provider_code", "expected_class", "retryable"),
    [
        (0, None, ErrorClass.NETWORK, True),
        (500, None, ErrorClass.PROVIDER, True),
        (401, None, ErrorClass.AUTH, False),
        (400, None, ErrorClass.VALIDATION, False),
        (700, None, ErrorClass.UNKNOWN, False),
        (429, None, ErrorClass.RATE_LIMIT, True),
        (402, None, ErrorClass.QUOTA, False),
        (200, "content-filter", ErrorClass.CONTENT_FILTER, False),
    ],
)
def test_taxonomy_is_complete_and_uses_only_safe_retry_classes(
    status_code: int,
    provider_code: str | None,
    expected_class: ErrorClass,
    retryable: bool,
) -> None:
    result = classify_provider_error(status_code, provider_code, retry_after=30)

    assert result.error_class is expected_class
    assert result.retryable is retryable
    assert result.retry_after == (30 if expected_class is ErrorClass.RATE_LIMIT else None)
    assert result.safe_message


def test_rate_limit_and_quota_are_distinct_terminal_decisions() -> None:
    rate_limit = classify_provider_error(429, retry_after=42)
    quota = classify_provider_error(402)

    assert rate_limit.error_class is ErrorClass.RATE_LIMIT
    assert rate_limit.retryable is True
    assert rate_limit.retry_after == 42
    assert quota.error_class is ErrorClass.QUOTA
    assert quota.retryable is False


def test_provider_codes_are_normalized_before_being_returned() -> None:
    result = classify_provider_error(200, "content filter / response value")

    assert result.error_class is ErrorClass.CONTENT_FILTER
    assert result.provider_code == "CONTENT_FILTER___RESPONSE_VALUE"
    assert "response value" not in result.safe_message.lower()
