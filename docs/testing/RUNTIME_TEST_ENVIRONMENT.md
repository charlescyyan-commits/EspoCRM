# Runtime Test Environment Contract

T04 runtime tests are disabled by default and may target only a local test environment such as `http://localhost:8080/api/v1`. Do not place real values in this document or in the repository.

| Variable | Required | Meaning |
|---|---|---|
| `ESPOCRM_RUNTIME_TEST_ENABLED` | Yes | Must be exactly `true`; otherwise no HTTP request is sent. |
| `ESPOCRM_BASE_URL` | Yes | Local EspoCRM API root, without credentials, query parameters, or fragments. |
| `ESPOCRM_API_KEY` | Yes | Dedicated local test API key; never printed or written to result files. |
| `ESPOCRM_RUNTIME_TEST_PREFIX` | Yes | Safe marker prefix; defaults to `CHITU_RT`. |
| `ESPOCRM_RUNTIME_TEST_TIMEOUT` | Yes | Request timeout in seconds; defaults to `20`, allowed range 1–120. |
| `ESPOCRM_RUNTIME_ALLOWED_HOSTS` | Optional | Comma-separated extra local test hosts. Defaults allow `localhost`, `127.0.0.1`, and `::1`. |

The guard rejects non-HTTP URLs, credential-bearing URLs, URLs with query/fragment components, production-like hostnames, non-local hosts without an explicit allowlist, missing credentials, unsafe markers, and disabled execution. API keys, passwords, cookies, authorization headers, and complete environment values are not logged.
