from __future__ import annotations

import json
from unittest import TestCase

from chitu_connector.acquisition.models import ProviderError, ProviderRateLimitError, SearchRequest
from chitu_connector.acquisition.providers import (
    HttpRequest,
    HttpResponse,
    ProviderConfigurationError,
    SerperConfig,
    SerperSearchProvider,
)


class FixtureTransport:
    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def search_request(*, result_limit: int = 10, keyword: str = "3d distributor", country: str = "US") -> SearchRequest:
    return SearchRequest(
        job_id="job-fixture-serper-001",
        provider_name="SERPER",
        keyword=keyword,
        country=country,
        persona="distributor",
        product="Resin Tank",
        result_limit=result_limit,
    )


def provider_for(transport: FixtureTransport) -> SerperSearchProvider:
    config = SerperConfig(
        "fixture-serper-api-key",
        base_url="https://fixture.serper.invalid",
        timeout_seconds=9,
    )
    return SerperSearchProvider(config, transport=transport)


_ORGANIC_ITEMS = [
    {
        "position": 1,
        "title": "Alpha 3D Distribution",
        "link": "https://alpha-3d.example/catalog",
        "snippet": "A leading 3D printing distributor",
    },
    {
        "position": 2,
        "title": "Beta Distributor Inc",
        "link": "https://beta-distributor.example",
        "snippet": "Industrial distribution services",
    },
]


class SerperSearchProviderTests(TestCase):
    # ------------------------------------------------------------------
    # Successful response
    # ------------------------------------------------------------------

    def test_fixture_response_maps_to_raw_candidates(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {"organic": _ORGANIC_ITEMS}),
        ])

        result = provider_for(transport).search(search_request(result_limit=2))

        self.assertEqual(result.provider_name, "SERPER")
        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(result.candidates[0].provider_candidate_id, "1")
        self.assertEqual(result.candidates[0].company_name, "Alpha 3D Distribution")
        self.assertEqual(result.candidates[0].domain, "https://alpha-3d.example/catalog")
        self.assertEqual(result.candidates[0].source_url, "https://alpha-3d.example/catalog")
        self.assertEqual(result.candidates[0].country, "US")
        self.assertEqual(result.candidates[0].raw_payload["snippet"], "A leading 3D printing distributor")
        self.assertEqual(result.candidates[1].provider_candidate_id, "2")
        self.assertEqual(result.candidates[1].company_name, "Beta Distributor Inc")

    def test_request_body_includes_keyword_country_and_limit(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {"organic": _ORGANIC_ITEMS}),
        ])

        provider_for(transport).search(search_request(result_limit=5))

        self.assertEqual(len(transport.requests), 1)
        body = json.loads(transport.requests[0].body or b"{}")
        self.assertEqual(body["q"], '3d distributor "US"')
        self.assertEqual(body["num"], 5)
        self.assertEqual(body["gl"], "us")

    def test_auth_header_uses_x_api_key_without_token_in_url(self) -> None:
        transport = FixtureTransport([])
        provider = provider_for(transport)

        http_request = provider.build_request(search_request())

        self.assertEqual(http_request.method, "POST")
        self.assertIn("/search", http_request.url)
        self.assertNotIn("fixture-serper-api-key", http_request.url)
        self.assertEqual(http_request.headers["X-API-KEY"], "fixture-serper-api-key")
        self.assertNotIn("fixture-serper-api-key", repr(http_request))

    # ------------------------------------------------------------------
    # Empty response
    # ------------------------------------------------------------------

    def test_empty_organic_returns_zero_candidates(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {"organic": []}),
        ])

        result = provider_for(transport).search(search_request())

        self.assertEqual(len(result.candidates), 0)

    def test_missing_organic_key_returns_zero_candidates(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {}),
        ])

        result = provider_for(transport).search(search_request())

        self.assertEqual(len(result.candidates), 0)

    # ------------------------------------------------------------------
    # Malformed JSON
    # ------------------------------------------------------------------

    def test_malformed_json_is_non_retryable(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, "not-valid-json{{{"),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_MALFORMED_RESPONSE")
        self.assertFalse(context.exception.retryable)

    def test_non_dict_json_body_is_rejected(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, [1, 2, 3]),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_MALFORMED_RESPONSE")
        self.assertFalse(context.exception.retryable)

    def test_non_list_organic_is_rejected(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {"organic": "not-a-list"}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_MALFORMED_RESPONSE")
        self.assertFalse(context.exception.retryable)

    def test_organic_item_without_title_is_rejected(self) -> None:
        transport = FixtureTransport([
            HttpResponse(200, {"organic": [{"position": 1, "link": "https://x.example"}]}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_MALFORMED_RESPONSE")
        self.assertFalse(context.exception.retryable)

    # ------------------------------------------------------------------
    # HTTP error classification
    # ------------------------------------------------------------------

    def test_401_is_non_retryable(self) -> None:
        transport = FixtureTransport([
            HttpResponse(401, {"error": "invalid key"}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_AUTHENTICATION_FAILED")
        self.assertFalse(context.exception.retryable)
        self.assertNotIn("invalid key", str(context.exception))

    def test_403_is_non_retryable(self) -> None:
        transport = FixtureTransport([
            HttpResponse(403, {"error": "forbidden"}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_FORBIDDEN")
        self.assertFalse(context.exception.retryable)

    def test_429_raises_provider_rate_limit_error(self) -> None:
        transport = FixtureTransport([
            HttpResponse(429, {"error": "rate limited"}, headers={"retry-after": "42"}),
        ])

        with self.assertRaises(ProviderRateLimitError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_RATE_LIMITED")
        self.assertTrue(context.exception.retryable)
        self.assertEqual(context.exception.retry_after, 42)

    def test_500_is_retryable(self) -> None:
        transport = FixtureTransport([
            HttpResponse(500, {"error": "internal"}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_UPSTREAM_ERROR")
        self.assertTrue(context.exception.retryable)

    def test_502_is_retryable(self) -> None:
        transport = FixtureTransport([
            HttpResponse(502, "Bad Gateway"),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_UPSTREAM_ERROR")
        self.assertTrue(context.exception.retryable)

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    def test_timeout_is_retryable(self) -> None:
        transport = FixtureTransport([TimeoutError()])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_TIMEOUT")
        self.assertTrue(context.exception.retryable)

    def test_transport_os_error_is_retryable(self) -> None:
        transport = FixtureTransport([OSError("connection reset")])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.code, "SERPER_TRANSPORT_ERROR")
        self.assertTrue(context.exception.retryable)

    # ------------------------------------------------------------------
    # Retry-after parsing
    # ------------------------------------------------------------------

    def test_429_with_retry_after_header_parses_seconds(self) -> None:
        transport = FixtureTransport([
            HttpResponse(429, {}, headers={"Retry-After": "120"}),
        ])

        with self.assertRaises(ProviderRateLimitError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.retry_after, 120)

    def test_429_with_lowercase_retry_after_header(self) -> None:
        transport = FixtureTransport([
            HttpResponse(429, {}, headers={"retry-after": "60"}),
        ])

        with self.assertRaises(ProviderRateLimitError) as context:
            provider_for(transport).search(search_request())
        self.assertEqual(context.exception.retry_after, 60)

    def test_429_without_retry_after_header_has_none_retry_after(self) -> None:
        transport = FixtureTransport([
            HttpResponse(429, {}),
        ])

        with self.assertRaises(ProviderRateLimitError) as context:
            provider_for(transport).search(search_request())
        self.assertIsNone(context.exception.retry_after)

    def test_429_with_non_numeric_retry_after_is_none(self) -> None:
        transport = FixtureTransport([
            HttpResponse(429, {}, headers={"retry-after": "not-a-number"}),
        ])

        with self.assertRaises(ProviderRateLimitError) as context:
            provider_for(transport).search(search_request())
        self.assertIsNone(context.exception.retry_after)

    # ------------------------------------------------------------------
    # API key redaction
    # ------------------------------------------------------------------

    def test_api_key_not_in_error_messages(self) -> None:
        transport = FixtureTransport([
            HttpResponse(401, {"error": "Invalid API key fixture-serper-api-key"}),
        ])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).search(search_request())
        self.assertNotIn("fixture-serper-api-key", str(context.exception))

    def test_api_key_not_in_config_repr(self) -> None:
        config = SerperConfig("my-secret-api-key")
        self.assertNotIn("my-secret-api-key", repr(config))

    # ------------------------------------------------------------------
    # Invalid request
    # ------------------------------------------------------------------

    def test_invalid_result_limit_is_non_retryable(self) -> None:
        transport = FixtureTransport([])

        with self.assertRaises(ProviderError) as context:
            provider_for(transport).build_request(search_request(result_limit=0))
        self.assertEqual(context.exception.code, "SERPER_INVALID_REQUEST")
        self.assertFalse(context.exception.retryable)
        self.assertEqual(transport.requests, [])


class SerperConfigTests(TestCase):
    def test_configuration_requires_api_key(self) -> None:
        with self.assertRaises(ProviderConfigurationError):
            SerperConfig.from_env({})

    def test_configuration_validates_timeout(self) -> None:
        with self.assertRaises(ProviderConfigurationError):
            SerperConfig.from_env({"SERPER_API_KEY": "key", "SERPER_TIMEOUT_SECONDS": "bad"})
        with self.assertRaises(ProviderConfigurationError):
            SerperConfig.from_env({"SERPER_API_KEY": "key", "SERPER_TIMEOUT_SECONDS": "0"})

    def test_configuration_from_env_strips_and_validates(self) -> None:
        config = SerperConfig.from_env({
            "SERPER_API_KEY": " my-key ",
            "SERPER_BASE_URL": "https://google.serper.dev",
            "SERPER_TIMEOUT_SECONDS": "15",
        })
        self.assertEqual(config.api_key, "my-key")
        self.assertEqual(config.base_url, "https://google.serper.dev")
        self.assertEqual(config.timeout_seconds, 15.0)
        self.assertNotIn("my-key", repr(config))
