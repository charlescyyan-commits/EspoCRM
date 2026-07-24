# Phase3C17 Browser Runtime Smoke Report

## Runtime Result

**Verdict: BLOCKED BY HOST PORT COLLISION — the browser did not reach EspoCRM.**

The Playwright smoke reproduced the visible `Internal Server Error`, but the first
failing response came from an unrelated Next.js development server bound to host port
8080. It did not come from the EspoCRM Apache container.

Evidence:

| Check | Observed result |
| --- | --- |
| Repository HEAD | `6fd69f68fd2041a52c59c0a4fee07d5085415e8d` |
| Initial repository status | Clean |
| EspoCRM container | `healthy`, image `espocrm/espocrm:10.0.1` |
| Compose declaration | Container port 80 intended to publish as host 8080 |
| Docker `HostConfig.PortBindings` | `80/tcp -> 8080` requested |
| Docker effective `NetworkSettings.Ports` | `{"80/tcp":[]}` — no active host publication |
| `docker ps` / `docker compose ps` | Shows only `80/tcp`, not `0.0.0.0:8080->80/tcp` |
| Host port 8080 owner | PID `55148`, `node.exe` |
| PID 55148 command | `D:\CreateShape3D\node_modules\next\dist\server\lib\start-server.js` |
| Parent command | `next dev -p 8080` |
| EspoCRM container-internal `/` | HTTP 200, `Server: Apache/2.4.67 (Debian)` |
| Playwright-time Apache access log | No Playwright request reached Apache |

The effective request path was therefore:

```text
Playwright / Chrome
  -> http://localhost:8080
  -> D:\CreateShape3D Next.js development server
  -> HTTP 500

NOT:

Playwright / Chrome
  -> EspoCRM Docker port 80
  -> Apache / EspoCRM
```

Playwright version: `1.61.1`  
Node: `v22.12.0`  
npm: `10.9.0`

The test used a temporary `npx` execution and did not create or modify `package.json`
or install repository dependencies.

## Browser Errors

Playwright captured one browser console error:

```text
Failed to load resource: the server responded with a status of 500
(Internal Server Error)
```

Failure details:

| Field | Value |
| --- | --- |
| URL | `http://localhost:8080/` |
| Status | `500 Internal Server Error` |
| Resource type | `document` |
| Response body | `Internal Server Error` |
| Page title | Empty |
| EspoCRM bootstrap | Not detected |
| Login form | Not detected |
| `pageerror` | None |
| Browser-side stack trace | None — no application JavaScript bootstrapped |

The screenshot contains only the plain response text:

`tmp/espo-runtime-error.png`

Raw Playwright result:

`tmp/navigation-smoke-results.json`

No frontend JavaScript exception or module-load stack was produced because the main
HTML document failed before EspoCRM assets could load.

## Failed Requests

### First failing request

```text
URL: http://localhost:8080/
Status: 500 Internal Server Error
Response: Internal Server Error
Stack trace: none; main-document HTTP failure before JavaScript execution
Likely owner: local development port orchestration / CreateShape3D Next dev server
```

### Explicit endpoint probes

All requested C17/EspoCRM-sensitive endpoints returned the same response from the
wrong host-port owner:

| URL | Status | Response | Stack trace | Likely owner |
| --- | --- | --- | --- | --- |
| `/api/v1/App/user` | 500 | `Internal Server Error` | None | Port 8080 Next server |
| `/api/v1/Metadata` | 500 | `Internal Server Error` | None | Port 8080 Next server |
| `/api/v1/Preferences` | 500 | `Internal Server Error` | None | Port 8080 Next server |
| `/api/v1/Settings` | 500 | `Internal Server Error` | None | Port 8080 Next server |
| `/api/v1/Tab` | 500 | `Internal Server Error` | None | Port 8080 Next server |

These are not valid observations of EspoCRM REST behavior. The requests never reached
EspoCRM, so the uniform 500 responses do not implicate `App/user`, Metadata,
Preferences, Settings, navigation, `tabList`, or authentication.

Playwright reported no transport-level `requestfailed` event. The wrong server accepted
each request and deliberately returned HTTP 500.

## Root Cause Classification

| Candidate | Verdict | Evidence |
| --- | --- | --- |
| A. Frontend JavaScript error | **NO** | No `pageerror`, no JS stack, and no EspoCRM bootstrap |
| B. EspoCRM REST API 500 | **NO** | API probes reached the Next server, not Apache |
| C. Metadata/navigation API failure | **NO** | Main document already failed at the wrong origin owner |
| D. Authentication/session failure | **NO** | Login UI never loaded; failure precedes authentication |
| E. Host routing/port ownership conflict | **YES** | `next dev -p 8080` owns the port; Docker has no effective published binding |

The likely sequence is:

1. `D:\CreateShape3D` started a Next.js development server on port 8080.
2. The EspoCRM container retained the desired Compose/HostConfig declaration for 8080,
   but its effective network port list contains no host binding.
3. Chrome and Playwright navigated to the unrelated Next server.
4. That server returned its own plain HTTP 500 response.

There is no evidence in this smoke that the Phase3C17 navigation implementation causes
a frontend, REST, metadata, navigation, or authentication defect.

## Recommended Owner

Primary owner:

**Local development environment / Docker port orchestration owner.**

Coordination may also be required with the **CreateShape3D frontend development owner**
because that Next.js process currently claims port 8080 and separately returns 500.

Recommended next action, not executed by this task:

1. Stop or move the unrelated `D:\CreateShape3D` Next development server away from
   port 8080.
2. Recreate or restart only the EspoCRM Compose service as required for Docker to
   establish the declared mapping.
3. Confirm `docker ps` shows an effective mapping such as
   `0.0.0.0:8080->80/tcp`.
4. Confirm host `GET /` returns the EspoCRM/Apache response rather than the Next server.
5. Rerun `tmp/navigation-smoke.spec.js`.
6. Only after the request reaches EspoCRM should any remaining frontend, API,
   metadata, navigation, or login failure be attributed and investigated.

No fix, container restart, cache clear, reinstall, metadata mutation, navigation
mutation, ACL change, workflow change, or application-code change was performed.
