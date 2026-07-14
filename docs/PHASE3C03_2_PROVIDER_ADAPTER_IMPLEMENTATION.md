# Phase3C03.2 — First Real Provider Adapter Skeleton

## Scope

This phase adds a fixture-driven Apify adapter skeleton behind the frozen acquisition contract. It does not wait for C03.1, invoke a real provider, create a SearchJob, persist a ProspectPool, call the worker or runner, or touch EspoCRM Runtime, Docker, browser, CRM, or production data.

## Frozen Contract

The adapter consumes `SearchRequest` and returns `ProviderResult` containing `RawCandidate` values. It raises the existing `ProviderError` with a safe code, safe summary, and retryability classification. The worker and runner were not modified or imported by the adapter.

## Provider Interface

`acquisition/providers/base.py` defines:

- `HttpRequest` with method, URL, headers, and optional JSON body.
- `HttpResponse` with status and fixture-compatible body types.
- `HttpTransport`, an injectable transport protocol.
- `ProviderAdapter`, the provider-neutral search interface.

Request headers and bodies are excluded from request representations so credentials are not exposed by accidental debugging output.

## Configuration

`acquisition/providers/config.py` defines `ApifyConfig` and `ProviderConfigurationError`.

Supported environment keys are:

- `APIFY_API_TOKEN` — required, never included in `repr` or URLs.
- `APIFY_API_BASE_URL` — defaults to `https://api.apify.com` and must be an absolute HTTP(S) URL without query or fragment.
- `APIFY_ACTOR_ID` — defaults to `apify/google-search-scraper`.
- `APIFY_TIMEOUT_SECONDS` — defaults to `30` and must be positive numeric input.

The test suite uses a fixture token only; no real credential is read or used.

## Apify Adapter

`acquisition/providers/apify_provider.py` implements `ApifyProvider`.

- Builds an Apify actor run request from keyword, country, and result limit.
- Uses `Authorization: Bearer <token>` and never places the token in a URL.
- Reads a dataset ID from the actor run response.
- Reads dataset arrays from either a direct list, `data`, or `items` fixture shape.
- Maps fixture records into `RawCandidate` without writing or normalizing CRM data.
- Preserves each fixture item only in the in-memory `raw_payload` contract field.
- Requires an injected `HttpTransport`; no network transport is constructed by this skeleton.

## Error Mapping

| Condition | Code | Retryable |
|---|---|---:|
| HTTP 401 | `APIFY_AUTHENTICATION_FAILED` | No |
| HTTP 403 | `APIFY_FORBIDDEN` | No |
| HTTP 429 | `APIFY_RATE_LIMITED` | Yes |
| HTTP 500+ | `APIFY_UPSTREAM_ERROR` | Yes |
| Timeout | `APIFY_TIMEOUT` | Yes |
| Other HTTP 4xx | `APIFY_REQUEST_REJECTED` | No |
| Malformed JSON or result shape | `APIFY_MALFORMED_RESPONSE` | No |
| Invalid result limit | `APIFY_INVALID_REQUEST` | No |

Response bodies are not copied into `ProviderError` messages.

## Fixture Tests

`tests/test_phase3c03_2_provider_adapter.py` provides an in-memory `FixtureTransport` and covers:

- Successful Apify run and dataset fixture mapping to `RawCandidate`.
- Request payload, actor URL, dataset URL, and bearer authentication header.
- Token exclusion from request URL and request/config representations.
- Missing token, invalid timeout, and invalid result-limit configuration.
- 401, 403, 429, and 500 classification.
- Timeout retryability.
- Malformed JSON and malformed candidate identity.
- No Worker, Runner, CRM, Docker, browser, or external network call.

## Validation

- Focused adapter tests: `6/6` passed.
- Full connector unittest suite: `95/95` passed.
- Python compile check passed for the new provider package and test.
- `git diff --check` passed for the new files.
- No Runtime, Docker, browser, CRM API, real provider API, or real API key was used.

## Files

- `chitu-connector/chitu_connector/acquisition/providers/__init__.py`
- `chitu-connector/chitu_connector/acquisition/providers/base.py`
- `chitu-connector/chitu_connector/acquisition/providers/config.py`
- `chitu-connector/chitu_connector/acquisition/providers/apify_provider.py`
- `chitu-connector/tests/test_phase3c03_2_provider_adapter.py`
- `docs/PHASE3C03_2_PROVIDER_ADAPTER_IMPLEMENTATION.md`

## Boundary and Follow-up

This is an adapter skeleton only. Wiring it into provider selection, Worker execution, Runner configuration, real Apify credentials, or EspoCRM persistence requires a separate explicitly scoped phase and runtime approval.
