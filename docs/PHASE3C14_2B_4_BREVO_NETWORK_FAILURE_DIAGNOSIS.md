# Phase C14.2B.4 — Brevo Network Failure Diagnosis

## Final Verdict

ENVIRONMENT_NETWORK_ISSUE

The observed result is consistent with a failure in the host-to-Brevo network path, not an HTTP-level Brevo response and not an adapter endpoint/configuration defect. The exact network root cause cannot be determined from the retained safe result because the transport deliberately standardizes the original exception.

No retry, Brevo API call, runner execution, configuration change, or code change was performed for this diagnosis.

## Observed Live Result

The single prior C14.2B live execution reported:

```text
MODE=EXECUTE_LIVE
PROVIDER_RESULT:
success=FALSE
status=RETRYABLE_FAILURE
provider_status=FAILED
error=BREVO_NETWORK_ERROR
EXTERNAL_MESSAGE_ID=NONE
```

## Execution Boundary

The one-shot runner injects the real transport path only in explicit live mode:

```text
SendExecutionWorker.process(...)
  -> BrevoProviderAdapter.send(...)
  -> BrevoProviderAdapter._send_once(...)
  -> UrllibBrevoHttpClient.post_json(...)
  -> urllib.request.urlopen(...)
```

The runner uses `UrllibBrevoHttpClient`, so this result establishes that the adapter invoked the HTTP client and that the client reached its `urlopen()` attempt.

It does **not** establish that a TCP connection was made, that TLS completed, that request bytes reached Brevo, or that Brevo accepted the email. A DNS, proxy, TLS, connect, or socket-timeout failure can all occur after the process begins the `urlopen()` operation but before a provider response is available.

Because delivery after a client-side timeout can be indeterminate, the instructed no-retry decision is correct.

## Exception Mapping

### HTTP transport

`UrllibBrevoHttpClient.post_json()` builds a POST request and calls:

```text
urlopen(request, timeout=timeout_seconds)
```

It handles outcomes as follows:

| Transport outcome | HTTP-client result |
|---|---|
| HTTP response, including non-2xx | `BrevoHttpResponse(status_code, body)` |
| `HTTPError` | Converted to `BrevoHttpResponse(error.code, body)` |
| `URLError` | Raises `BrevoTransportError("URLError")` |
| `TimeoutError` | Raises `BrevoTransportError("TimeoutError")` |

### Provider adapter

`BrevoProviderAdapter._send_once()` maps `BrevoTransportError` or `TimeoutError` to:

```text
SendResultStatus.RETRYABLE_FAILURE
ProviderErrorCategory.NETWORK_ERROR
safe code: BREVO_NETWORK_ERROR
```

The C13 Worker subsequently maps the provider category to the C11.5 `NETWORK` failure category and terminates the in-memory QueueItem as `FAILED`. It does not schedule or execute a retry.

## Exact Exception

The safe result does not retain the exact underlying exception instance.

With the production `UrllibBrevoHttpClient` injected by the runner, the immediate exception caught by `BrevoProviderAdapter` was necessarily `BrevoTransportError`. That wrapper was raised from either:

- `urllib.error.URLError`; or
- `TimeoutError`.

The original error is attached only as a Python exception cause in the terminated process. The adapter intentionally returns only `BREVO_NETWORK_ERROR`, and the runner prints only that safe error code. No current log or persisted diagnostic record retains the underlying DNS name-resolution error, proxy error, TLS certificate/handshake error, connect refusal, or timeout detail.

## HTTP Request Reachability

| Question | Determination |
|---|---|
| Did the adapter call its HTTP transport seam? | Yes. The reported error requires the `_send_once()` transport-error path. |
| Did `urlopen()` begin an outbound attempt? | Yes. The real transport produces this error only from its `urlopen()` try block. |
| Did the HTTP request leave the host process? | Not provable. It may have failed during DNS/proxy resolution, connection setup, TLS, or a later timeout. |
| Did Brevo receive or accept the message? | Not provable. No HTTP response or external message ID was returned. |
| Is a retry safe? | No. Do not retry: a timeout can leave delivery state ambiguous. |

## Timeout, DNS, TLS, and Network Handling

The adapter uses a fixed 10-second timeout when the runner constructs `BrevoProviderAdapter` without an override.

| Failure class | Current behavior |
|---|---|
| DNS resolution failure | Typically surfaces as `URLError` and becomes `BREVO_NETWORK_ERROR`. |
| Proxy resolution/connect failure | Typically surfaces as `URLError` and becomes `BREVO_NETWORK_ERROR`. |
| TCP connection failure | Typically surfaces as `URLError` and becomes `BREVO_NETWORK_ERROR`. |
| TLS handshake/certificate failure | Typically surfaces through `URLError` and becomes `BREVO_NETWORK_ERROR`. |
| Socket/read timeout | Surfaces as `TimeoutError` or a wrapped `URLError`; becomes `BREVO_NETWORK_ERROR`. |
| HTTP 401/403/429/400/5xx | Does not become `BREVO_NETWORK_ERROR`; it is returned as an HTTP response and mapped to the corresponding provider category. |

## Endpoint Configuration

The active C12.2 transport uses a fixed, non-environment-overridable endpoint:

```text
https://api.brevo.com/v3/smtp/email
```

It is built from:

- base URL: `https://api.brevo.com/v3`
- path: `/smtp/email`
- method: `POST`

This is the expected Brevo transactional-email endpoint. The observed `BREVO_NETWORK_ERROR` is therefore not evidence of a malformed configured endpoint. It occurred before any HTTP status could be parsed.

## Classification Assessment

`RETRYABLE_FAILURE / NETWORK_ERROR` is the correct **classification** for the adapter boundary: it distinguishes transport failure from authentication, validation, rate-limit, provider HTTP, and malformed-response failures.

It is not permission to retry automatically. C13 has no automatic retry implementation, and this phase explicitly forbids a repeat send. The terminal `FAILED` result is the correct state for this one-shot acceptance attempt.

## Remaining Evidence Gap

The current secure error model intentionally removes the exact network cause and has no external delivery observation. Consequently, this diagnosis cannot distinguish DNS, proxy, firewall, TLS, outbound egress, or timeout as the precise environmental fault.

No further provider call should be made to resolve that ambiguity. Any later investigation must use host/network telemetry or Brevo-side delivery visibility outside this runner, without resending the request.

