# Phase T04 - Runtime Test Harness Report

**Date:** 2026-07-13  
**Phase:** T04 - Runtime Test Harness

## Verdict

**PARTIAL PASS**

## Phase status

**COMPLETE — LIVE RUNTIME EVIDENCE PENDING**

## T03 status

**FROZEN BASELINE**

T03 remains a separate offline regression gate and was not changed by T04.

## Deliverables

- `tests/runtime/runtime_harness.py`: stdlib-only REST client, local-target safety guard, fixture registry, marker verification, reverse-order cleanup, and residue audit.
- `tests/runtime/runtime_cli.py` and `scripts/testing/run-runtime-tests.ps1`: noninteractive `check`, `smoke`, `acl`, `cleanup-preview`, `cleanup`, and `all` commands with stable exit codes.
- `tests/runtime/test_runtime_harness.py`: offline safety and cleanup tests.
- `docs/testing/RUNTIME_TEST_HARNESS.md` and `docs/testing/RUNTIME_TEST_ENVIRONMENT.md`: execution and environment contract.

## Safety Contract

Runtime execution is disabled unless `ESPOCRM_RUNTIME_TEST_ENABLED=true`. The harness requires a HTTP(S) base URL and API key, rejects credential-bearing/query/fragment URLs and production-like or non-allowlisted hosts, validates marker and timeout inputs, and never logs the API key.

Fixtures use a run-specific marker such as `CHITU_RT_20260713T000000Z_ABCDEF12`. Their IDs are persisted immediately in `temp/test-results/runtime-fixtures-<runId>.json`. Cleanup acts only on that registry, confirms the marker on the live record, deletes in dependency order (`ResearchEvidence`, `ProspectPool`, `SearchJob`, `SearchStrategy`, `Lead`), verifies HTTP 404 afterward, continues after individual failures, and reports residue as exit code 4.

## Offline Verification

| Check | Result |
|---|---|
| Runtime harness unit suite | PASS — 11/11 |
| Disabled guard, before HTTP | PASS — exit 5 |
| Missing cleanup run ID | PASS — exit 2 |
| Missing API credential | PASS — exit 3 |
| Production-like target rejection | PASS — exit 5 |
| Invalid timeout configuration | PASS — exit 2 |
| Cleanup preview performs no REST call | PASS — unit verified |
| External registry refusal | PASS — unit verified |
| Child failure still attempts cleanup | PASS — unit verified |
| Caller outside repo / path with spaces | PASS — help command exit 0 |
| Secret redaction in client error path | PASS — unit verified |

Host environment inspection found none of the six documented runtime-contract variables configured. No HTTP request, fixture creation, deletion, or residue audit was attempted against a CRM target.

## Live Runtime Result

**NOT EXECUTED.** The required explicit local-runtime configuration and dedicated API credential were absent. Therefore no claim is made for authenticated preflight, Lead/ResearchEvidence CRUD, relationship behavior, ACL enforcement, fixture cleanup, or zero-residue state.

To advance this verdict, set the documented local-only variables and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 all
```

Only a successful local run with `fixturesCreated == fixturesCleaned` and `residueCount == 0` may upgrade T04 to PASS.

## T01 Risk Disposition

| Risk | T04 status |
|---|---|
| R01 hardcoded provisioning credentials | DEFERRED — outside T04 scope; no provisioning files changed. |
| R02 no automated cleanup verification | PARTIALLY RESOLVED — T04 provides registry-only automatic cleanup and residue checks; live proof is pending. |

## T03 Regression Preservation

`scripts/testing/run-regression-gate.ps1` completed successfully after T04: **131/131 tests passed**, 5/5 required suites, exit 0. No T03 runner, gate map, or test semantics were modified.

## Scope and CI

T04 changed only the permitted runtime harness, runner, and testing documentation paths. It did not modify connector worker/provider/normalization/repository code, Serper work, deployment manifests, provisioning, or CI workflows. T04 remains local-only and is not CI-enabled.
