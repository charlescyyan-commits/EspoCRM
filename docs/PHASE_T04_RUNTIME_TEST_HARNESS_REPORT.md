# Phase T04 - Runtime Test Harness Report

**Date:** 2026-07-14
**Scope:** Read-only runtime gate for future CI and regression use

## Verdict

**PASS WITH RISKS**

The harness and all four required deterministic scenarios passed. No authenticated CRM runtime configuration was supplied for this run, so live runtime evidence remains pending. The gate stopped before any HTTP request when configuration was absent.

## Deliverables

- `scripts/runtime/runtime_gate.py` - read-only gate implementation.
- `scripts/runtime/test_runtime_gate.py` - deterministic offline scenarios.
- `scripts/run-runtime-gate.ps1` - regression/CI entry point.

The implementation is Python standard-library only. It issues only `GET` requests in `-Mode run`; it contains no Docker, rebuild, cache-clear, migration, or CRUD operation.

## Gate Coverage

| Area | Check | Evidence |
|---|---|---|
| CRM runtime health | Reachability | `GET <ESPOCRM_BASE_URL>` requires a 2xx/3xx response. |
| CRM runtime health | API availability | Authenticated `GET /api/v1/Metadata?key=appParams` requires HTTP 200. |
| Extension | Version | Compares workspace `crm-extension/manifest.json` with a Prospecting extension version exposed by runtime `appParams`; absent runtime version is reported as `RISK`. |
| Extension | Loaded metadata | Reads `ResearchEvidence`, Lead fields, and Lead links through Metadata and requires the approved fields plus `researchEvidences`. |
| Connector | Contract version | Confirms `CONTRACT_VERSION` equals the V1 JSON-schema version. |
| Connector | Schema compatibility | Confirms required Lead and ResearchEvidence connector fields exist in workspace entity definitions. |
| Connector | Configuration | Requires non-empty `ESPOCRM_BASE_URL` and `ESPOCRM_API_KEY` without printing either value. |

## Test Results

Executed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-runtime-gate.ps1 -Mode test -PythonExecutable <python.exe>
```

| Scenario | Result |
|---|---|
| Success case: reachable API, matching extension version, complete metadata | PASS |
| Missing extension metadata | PASS - gate returns `FAIL` for `extension.loaded` |
| Missing connector configuration | PASS - gate returns `FAIL` before any HTTP request |
| API unavailable | PASS - gate returns `FAIL` and uses only a `GET` attempt |

**Result: 4/4 tests passed.**

The real entry point was also run without CRM configuration. It passed all workspace contract checks, then returned the expected `connector.config` failure (`ESPOCRM_BASE_URL is required`) before any HTTP operation. No runtime data was created, changed, or deleted.

## CI / Regression Usage

Run deterministic harness coverage:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-runtime-gate.ps1 -Mode test
```

Run the actual read-only gate in a configured CI/runtime environment:

```powershell
$env:ESPOCRM_BASE_URL = "https://crm-test.example"
$env:ESPOCRM_API_KEY = "<secure CI secret>"
powershell -ExecutionPolicy Bypass -File scripts/run-runtime-gate.ps1 -Mode run
```

The runner never emits the API-key value. A non-`PASS` result blocks the gate; `PASS WITH RISKS` is returned only when the runtime metadata cannot expose an extension version while the remaining read-only checks pass.

## Risks and Follow-up

1. No live authenticated runtime was configured for this phase, so runtime reachability, API access, loaded metadata, and installed-version equivalence have not been proven against Docker.
2. EspoCRM deployments must expose the Prospecting extension version through `appParams` (one of `prospectingExtensionVersion`, `chituProspectingExtensionVersion`, or `extensionVersion`) to produce a full `PASS`; otherwise the check is intentionally `PASS WITH RISKS`.

No C10/C11/C12/C13/C14 module code, business logic, Docker configuration, database data, or runtime metadata was modified.
