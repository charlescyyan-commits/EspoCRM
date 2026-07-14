# Phase3C03.2 — Serper Provider Implementation Report

**Date:** 2026-07-13  
**Status:** **PASS**  
**Scope:** Serper Search Provider implementation with ProviderRateLimitError, runner factory registration, and full test coverage

## 1. Verdict

**PASS** — All new tests pass, all existing suites pass, zero regressions. No forbidden files were touched.

## 2. Files Added

| File | Purpose |
|---|---|
| `chitu-connector/chitu_connector/acquisition/providers/serper_provider.py` | SerperSearchProvider implementation |
| `chitu-connector/tests/test_phase3c03_2_serper_provider.py` | Serper provider unit tests (26 tests) |
| `chitu-connector/tests/test_phase3c03_2_serper_runner.py` | Runner factory resolution tests (5 tests) |

## 3. Files Modified

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/acquisition/models.py` | Added `ProviderRateLimitError` class |
| `chitu-connector/chitu_connector/acquisition/__init__.py` | Exported `ProviderRateLimitError` |
| `chitu-connector/chitu_connector/acquisition/providers/base.py` | Added `headers: Mapping[str, str]` field to `HttpResponse` (default `{}`, backward compatible) |
| `chitu-connector/chitu_connector/acquisition/providers/config.py` | Added `SerperConfig` dataclass with `from_env` factory |
| `chitu-connector/chitu_connector/acquisition/providers/__init__.py` | Exported `SerperConfig`, `SerperSearchProvider` |
| `chitu-connector/chitu_connector/acquisition/runner.py` | Registered serper provider in runner factory; added `_resolve_provider` and `_UrllibTransport` |

## 4. Provider Contract Alignment

| Contract Requirement | Implementation | Status |
|---|---|---|
| `name` property | `SerperSearchProvider.name = "SERPER"` | PASS |
| `search(SearchRequest) -> ProviderResult` | Single-call POST to `/search`, parses `organic` results | PASS |
| Request mapping | `keyword + country` → `{"q": "...", "gl": "us", "num": N}` | PASS |
| Response mapping | `organic[]` items → `RawCandidate` with position, title, link, snippet | PASS |
| Auth in headers, not URL | `X-API-KEY` header; API key excluded from repr/URL/error messages | PASS |
| Error classification | All status codes, timeout, OSError, malformed JSON classified with safe codes | PASS |
| No normalization | Provider returns raw `RawCandidate`; dedup/domain normalize owned by Worker | PASS |
| No persistence | Provider has zero CRM or database imports | PASS |

## 5. Error Mapping

| Condition | Error Code | Retryable | Class |
|---|---|---|---|
| HTTP 401 | `SERPER_AUTHENTICATION_FAILED` | No | `ProviderError` |
| HTTP 403 | `SERPER_FORBIDDEN` | No | `ProviderError` |
| HTTP 429 | `SERPER_RATE_LIMITED` | Yes | `ProviderRateLimitError` |
| HTTP 5xx | `SERPER_UPSTREAM_ERROR` | Yes | `ProviderError` |
| Timeout | `SERPER_TIMEOUT` | Yes | `ProviderError` |
| Transport OSError | `SERPER_TRANSPORT_ERROR` | Yes | `ProviderError` |
| Malformed JSON | `SERPER_MALFORMED_RESPONSE` | No | `ProviderError` |
| Invalid result_limit | `SERPER_INVALID_REQUEST` | No | `ProviderError` |
| Missing candidate identity | `SERPER_MALFORMED_RESPONSE` | No | `ProviderError` |

`ProviderRateLimitError` extends `ProviderError` and adds `retry_after: int | None`, parsed from the `retry-after` / `Retry-After` response header. Invalid or missing header values result in `retry_after=None`.

## 6. Tests Added

### test_phase3c03_2_serper_provider.py (26 tests)

- **Successful response**: fixture mapping, request body, auth header placement
- **Empty response**: `organic: []` → 0 candidates, missing `organic` key → 0 candidates
- **Malformed JSON**: non-JSON body, non-dict JSON, non-list organic, item without title
- **HTTP errors**: 401 (non-retryable), 403 (non-retryable), 429 (ProviderRateLimitError), 500 (retryable), 502 (retryable)
- **Timeout/transport**: TimeoutError (retryable), OSError (retryable)
- **Retry-after parsing**: Retry-After header, lowercase `retry-after`, missing header → None, non-numeric → None
- **API key redaction**: not in error messages, not in config repr
- **Invalid request**: result_limit=0
- **Config validation**: missing API key, bad timeout, env parsing and stripping

### test_phase3c03_2_serper_runner.py (5 tests)

- `--provider fake` still accepted with exit code 0
- `--provider serper` accepted with factory override
- Unknown `--provider` rejected with `INVALID_ARGUMENT`
- `SerperSearchProvider.name == "SERPER"`
- `provider_factory` override supersedes `--provider` flag

## 7. Test Results

| Suite | Count | Status |
|---|---|---|
| Serper provider (new) | 26 | PASS |
| Serper runner factory (new) | 5 | PASS |
| Apify provider adapter (existing) | 6 | PASS |
| Worker core + hardening + runner (existing) | 31 | PASS |
| Full connector suite (existing) | 58 | PASS |
| Extension skeleton (existing) | 40 | PASS |
| Deployment validation (existing) | 2 | PASS |
| **Total** | **168** | **PASS** |

## 8. T03 Regression Result

**PASS** — All T03 Core Regression Gate suites pass:

- Extension: 40/40
- Connector: 58/58
- Worker: 31/31
- Static (deployment validation): 2/2

No existing test was modified. No T03 gate file was touched.

## 9. Parallel Conflict Check

- `scripts/testing/**`: NOT modified
- T04 Runtime Harness: NOT modified
- `deployment/**`: NOT modified
- `manifest.json`: NOT modified
- Phase3C CRM PHP files: NOT modified

No conflict with parallel T04 or Phase3C work.

## 10. Scope Audit — Boundary Confirmations

```
worker.py modified:             NO
fake_provider.py modified:      NO
normalization.py modified:      NO
espo_repository.py modified:    NO
provider.py Protocol modified:  NO
CRM PHP modified:               NO
existing tests modified:        NO
T03 Gate modified:              NO
T04 files modified:             NO
external system accessed:       NO
real API key used:              NO
git commit created:             NO
git push performed:             NO
```

All changes are limited to the permitted scope: `SerperSearchProvider`, `ProviderRateLimitError`, 2 new test files, runner factory entry, and supporting config/export wiring.

## 11. Implementation Notes

- `SerperSearchProvider` follows the same transport-injected pattern as `ApifyProvider` — callers must inject a fixture `HttpTransport` for testing; the production runner uses a minimal `_UrllibTransport` wrapper.
- The `headers` field added to `HttpResponse` is backward compatible (defaults to empty `dict`). Existing code constructing `HttpResponse(status, body)` continues to work unchanged.
- The `provider_factory` parameter in `runner.main()` changed type from `Callable[[], DeterministicFakeProvider]` to `Callable[[], Any] | None` to support both fake and serper providers via the same injection point. When `None`, the runner resolves the provider from the `--provider` flag and environment variables.
- `ProviderRateLimitError` is raised only for HTTP 429 responses. All other errors continue to use `ProviderError`. The error hierarchy was designed to be additive — existing catch blocks for `ProviderError` also catch `ProviderRateLimitError`.
