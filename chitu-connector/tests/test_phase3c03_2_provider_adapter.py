from __future__ import annotations

import json
from unittest import TestCase

from chitu_connector.acquisition.models import ProviderError, SearchRequest
from chitu_connector.acquisition.providers import ApifyConfig, ApifyProvider, HttpRequest, HttpResponse, ProviderConfigurationError


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


def search_request(*, result_limit: int = 10) -> SearchRequest:
    return SearchRequest(
        job_id="job-fixture-001",
        provider_name="APIFY",
        keyword="3d distributor",
        country="US",
        persona="distributor",
        product="Resin Tank",
        result_limit=result_limit,
    )


def provider_for(transport: FixtureTransport) -> ApifyProvider:
    config = ApifyConfig(
        "fixture-secret-token",
        base_url="https://fixture.apify.invalid",
        actor_id="fixture/search-actor",
        timeout_seconds=9,
    )
    return ApifyProvider(config, transport=transport)


class ApifyProviderAdapterTests(TestCase):
    def test_fixture_response_maps_to_raw_candidates_without_worker_or_crm_writes(self) -> None:
        transport = FixtureTransport([
            HttpResponse(201, {"data": {"defaultDatasetId": "dataset-fixture-001"}}),
            HttpResponse(200, [
                {
                    "id": "result-001",
                    "title": "Example Distributor",
                    "url": "https://example.invalid/catalog",
                    "description": "Fixture result",
                    "position": 1,
                },
                {
                    "id": "result-002",
                    "companyName": "Second Distributor",
                    "domain": "second.invalid",
                    "sourceUrl": "https://search.invalid/result-002",
                    "country": "CA",
                },
            ]),
        ])

        result = provider_for(transport).search(search_request(result_limit=2))

        self.assertEqual(result.provider_name, "APIFY")
        self.assertEqual([candidate.provider_candidate_id for candidate in result.candidates], ["result-001", "result-002"])
        self.assertEqual(result.candidates[0].company_name, "Example Distributor")
        self.assertEqual(result.candidates[0].domain, "https://example.invalid/catalog")
        self.assertEqual(result.candidates[0].country, "US")
        self.assertEqual(result.candidates[0].raw_payload["position"], 1)
        self.assertEqual(len(transport.requests), 2)
        run_payload = json.loads(transport.requests[0].body or b"{}")
        self.assertEqual(run_payload["searchStringsArray"], ['3d distributor "US"'])
        self.assertEqual(run_payload["maxResultsPerQuery"], 2)
        self.assertEqual(transport.requests[0].headers["Authorization"], "Bearer fixture-secret-token")
        self.assertNotIn("fixture-secret-token", repr(transport.requests[0]))

    def test_request_builders_use_auth_header_without_token_in_url(self) -> None:
        transport = FixtureTransport([])
        provider = provider_for(transport)

        run_request = provider.build_run_request(search_request())
        dataset_request = provider.build_dataset_request("dataset-fixture-001")

        self.assertEqual(run_request.method, "POST")
        self.assertIn("/v2/acts/fixture%2Fsearch-actor/runs", run_request.url)
        self.assertIn("/v2/datasets/dataset-fixture-001/items", dataset_request.url)
        self.assertNotIn("fixture-secret-token", run_request.url)
        self.assertNotIn("fixture-secret-token", dataset_request.url)
        self.assertEqual(dataset_request.headers["Authorization"], "Bearer fixture-secret-token")

    def test_configuration_requires_token_and_validates_timeout(self) -> None:
        with self.assertRaises(ProviderConfigurationError):
            ApifyConfig.from_env({})
        with self.assertRaises(ProviderConfigurationError):
            ApifyConfig.from_env({"APIFY_API_TOKEN": "token", "APIFY_TIMEOUT_SECONDS": "bad"})
        with self.assertRaises(ProviderConfigurationError):
            ApifyConfig.from_env({"APIFY_API_TOKEN": "token", "APIFY_TIMEOUT_SECONDS": "0"})

        config = ApifyConfig.from_env({"APIFY_API_TOKEN": " token ", "APIFY_ACTOR_ID": "fixture~actor"})
        self.assertEqual(config.api_token, "token")
        self.assertEqual(config.actor_id, "fixture~actor")
        self.assertNotIn("token", repr(config))

    def test_http_failures_map_to_safe_retry_classification(self) -> None:
        expected = {
            401: ("APIFY_AUTHENTICATION_FAILED", False),
            403: ("APIFY_FORBIDDEN", False),
            429: ("APIFY_RATE_LIMITED", True),
            500: ("APIFY_UPSTREAM_ERROR", True),
        }
        for status_code, (code, retryable) in expected.items():
            with self.subTest(status_code=status_code):
                transport = FixtureTransport([HttpResponse(status_code, {"secret": "not surfaced"})])
                with self.assertRaises(ProviderError) as context:
                    provider_for(transport).search(search_request())
                self.assertEqual(context.exception.code, code)
                self.assertEqual(context.exception.retryable, retryable)
                self.assertNotIn("not surfaced", str(context.exception))

    def test_timeout_is_retryable_and_malformed_responses_are_safe(self) -> None:
        with self.assertRaises(ProviderError) as timeout_context:
            provider_for(FixtureTransport([TimeoutError()])).search(search_request())
        self.assertEqual(timeout_context.exception.code, "APIFY_TIMEOUT")
        self.assertTrue(timeout_context.exception.retryable)

        malformed_run = FixtureTransport([HttpResponse(200, "not-json")])
        with self.assertRaises(ProviderError) as json_context:
            provider_for(malformed_run).search(search_request())
        self.assertEqual(json_context.exception.code, "APIFY_MALFORMED_RESPONSE")
        self.assertFalse(json_context.exception.retryable)

        malformed_item = FixtureTransport([
            HttpResponse(200, {"data": {"defaultDatasetId": "dataset-fixture-001"}}),
            HttpResponse(200, [{"title": "Missing stable id"}]),
        ])
        with self.assertRaises(ProviderError) as item_context:
            provider_for(malformed_item).search(search_request())
        self.assertEqual(item_context.exception.code, "APIFY_MALFORMED_RESPONSE")
        self.assertFalse(item_context.exception.retryable)

    def test_invalid_result_limit_is_non_retryable(self) -> None:
        transport = FixtureTransport([])
        with self.assertRaises(ProviderError) as context:
            provider_for(transport).build_run_request(search_request(result_limit=0))
        self.assertEqual(context.exception.code, "APIFY_INVALID_REQUEST")
        self.assertFalse(context.exception.retryable)
        self.assertEqual(transport.requests, [])
