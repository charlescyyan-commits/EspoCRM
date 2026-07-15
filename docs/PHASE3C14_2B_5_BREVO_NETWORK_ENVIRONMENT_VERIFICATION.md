# Phase C14.2B.5 — Brevo Network Environment Verification

## Verdict

NETWORK_BLOCKED

The environment can resolve `api.brevo.com` and establish TCP/443 reachability, but it does not provide a stable usable HTTPS/TLS path to Brevo. The actual C14.2B send attempt failed at the same transport boundary, and subsequent credential-free root-path probes observed TLS EOF failures.

No Brevo SMTP endpoint was called. No API key was used. No email, live-runner retry, configuration change, code change, or commit occurred.

## Scope

All HTTPS probes used only the unauthenticated root URL:

```text
https://api.brevo.com/
```

They did not access:

```text
https://api.brevo.com/v3/smtp/email
```

No request carried an API key or email payload.

## Verification Results

Timestamp started (UTC): `2026-07-14T14:08:25.9291151Z`

| Check | Result | Interpretation |
|---|---|---|
| DNS: `api.brevo.com` | PASS | One IPv4 address resolved. |
| TCP/443: `api.brevo.com` | PASS | A TCP connection test succeeded. |
| TCP/443: `example.com` | PASS | General outbound TCP/443 is available. |
| Python urllib: Brevo HTTPS root, first probe | HTTP 404 response | At least one root-path request completed DNS, TCP, TLS, and HTTP. A root 404 is expected for a non-resource path and proves it was not an SMTP request. |
| Python urllib: Brevo HTTPS root, later probe | `URLError` with `SSLEOFError` reason | The TLS peer/path closed unexpectedly before a usable HTTP response. |
| Python urllib: `example.com` HTTPS root | HTTP 200 response | General Python HTTPS and certificate validation work for a normal control site. |
| Python urllib, proxy-disabled: Brevo HTTPS root | `URLError` with `SSLEOFError` reason | The failing Brevo TLS path persists when Python proxy use is explicitly disabled. |
| Python proxy discovery | Proxy configuration present for `ftp`, `http`, and `https` schemes | A proxy-aware route exists in the environment. Values were not read or recorded. |
| WinHTTP proxy configuration | Direct access configured | The Python proxy discovery and WinHTTP settings are not identical; no proxy value was disclosed. |

## Python Transport Behavior

The C14 runner uses Python's `urllib.request.urlopen()` through `UrllibBrevoHttpClient`.

The observed `SSLEOFError` was returned as the reason of a `urllib.error.URLError`. The production transport converts that `URLError` to `BrevoTransportError`; the adapter then correctly returns:

```text
RETRYABLE_FAILURE
NETWORK_ERROR
BREVO_NETWORK_ERROR
```

The separate successful `example.com` HTTPS response rules out a broad Python HTTPS failure. The successful TCP/443 test rules out simple DNS failure or a complete port block. However, TCP success alone does not prove that a TLS session can complete.

## Endpoint Assessment

The adapter endpoint remains:

```text
https://api.brevo.com/v3/smtp/email
```

It is assembled from the fixed base `https://api.brevo.com/v3` and path `/smtp/email`. The root-path checks used above did not test or invoke that endpoint.

No malformed endpoint configuration was found. The observed failure occurs at the network/TLS boundary before the adapter can receive an HTTP response.

## Interpretation

The evidence supports a Brevo-specific or path-specific environment restriction:

- DNS works.
- TCP port 443 works.
- Normal HTTPS works.
- Brevo HTTPS is intermittent at best: one root request returned HTTP 404, while later default-proxy and direct/no-proxy requests failed with `SSLEOFError`.
- Disabling Python proxy handling did not restore the Brevo TLS connection, so the detected proxy configuration is not sufficient to explain the fault by itself.

Likely environmental classes include outbound egress filtering, TLS inspection or policy, a network device closing the Brevo TLS session, proxy-route inconsistency, or upstream network instability. This read-only evidence cannot attribute the failure to a specific device or provider.

## Operational Decision

Treat the current environment as blocked for C14.2B live acceptance.

Do not retry the original send: a previous timeout/network failure cannot prove that Brevo did not receive any portion of the request. Any future acceptance must wait for environment-level TLS/egress remediation and a separately approved controlled execution.

