# Phase T05 - Regression Baseline Hardening Report

**Date:** 2026-07-14  
**Phase:** T05 - Regression Baseline Hardening  
**Scope:** `scripts/testing`, `tests`, and `docs` only  
**Execution mode:** Offline only; no CRM, database, external provider, or production data access.

## Verdict

**T05 IMPLEMENTATION: PASS**  
**FREEZE REGRESSION BASELINE: BLOCKED**

T05 establishes a required, fail-closed offline baseline for the complete current connector suite, focused worker suite, extension/static validation, runtime-harness safety tests, and a new extension package/metadata preflight. The full gate correctly fails because an existing extension test detects a metadata mismatch outside this phase's permitted paths. T05 did not alter that metadata, its contract, or the existing assertion.

## Current Baseline

| Required suite | Entrypoint | Result | Tests passed | Tests failed | Notes |
|---|---|---:|---:|---:|---|
| Extension | `crm-extension/tests/test_*.py` | FAIL | 56 | 1 | Existing Phase3B03 metadata/contract assertion failure. |
| Connector | `chitu-connector/tests/test_*.py` | PASS | 243 | 0 | Full current connector inventory, including Phase3C03--C10 coverage. |
| Worker | `chitu-connector/tests/test_phase3c02_*.py` | PASS | 31 | 0 | Focused worker/persistence/runner diagnostic subset; also included in Connector. |
| Static | `deployment/validation/test_*.py` | PASS | 2 | 0 | Offline deployment-static validation. |
| Runtime | `tests/runtime/test_*.py` | PASS | 11 | 0 | Offline safety, cleanup, and credential-redaction coverage only. |
| Baseline | `tests/regression/test_*.py` | PASS | 3 | 0 | New metadata, archive-build, and install-layout preflight. |
| Runner integrity | Parsed suite summaries | PASS | - | - | Gate requires all six real suite summaries and fails closed on malformed or missing output. |

The gate executed **347 test invocations**: 346 passed and 1 failed. The focused Worker suite overlaps the complete Connector suite by design; the de-duplicated count across the six real test directories is **316 tests** (57 Extension + 243 Connector + 2 Static + 11 Runtime + 3 Baseline).

## T05 Changes

1. `scripts/testing/run-tests.ps1`
   - Added `runtime` and `baseline` suite entrypoints.
   - Expanded `connector` from the legacy `test_espocrm_*.py` pattern to `test_*.py`, so Phase3C03--C10 tests are now part of every regression run.
   - Made Extension, Connector, Worker, Static, Runtime, and Baseline mandatory for `regression` and `all`.

2. `scripts/testing/run-regression-gate.ps1` and `regression-gate-map.json`
   - Updated the fail-closed parser and gate inventory to require all six real suites plus Runner integrity.
   - Kept live browser, live CRM execution, and live install/upgrade/rollback lifecycle work explicitly non-implemented and non-passing.

3. `tests/regression/test_extension_package_baseline.py`
   - Parses every extension JSON metadata file.
   - Executes the existing extension package builder only into a temporary directory.
   - Validates ZIP integrity, manifest parity, safe/unique archive paths, EspoCRM `files/` install layout, complete source-package file parity, and JSON payloads inside the generated archive.

The new check is an **offline archive install preflight**. It does not claim a live EspoCRM installation, upgrade, rollback, or browser result.

## Commands Executed

```powershell
& <bundled-python> -m unittest discover -s tests\regression -p 'test_*.py' -v
# 3 passed; exit 0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-tests.ps1 all -PythonExecutable <bundled-python>
# 346 passed, 1 failed; exit 1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-regression-gate.ps1 -PythonExecutable <bundled-python>
# Required suites 6/7 passed; exit 1
```

The bundled Python used in this workspace was:

```text
C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

The gate wrote its machine-readable result to:

```text
temp/test-results/regression-gate-20260714-141520-779.json
```

## Failure

Only the Extension suite failed:

```text
crm-extension/tests/test_extension_skeleton.py
test_phase3b03_connector_routes_and_proposal_model

Missing from the observed Lead metadata field set:
- peOpportunityScoreV4
- peBestFirstProduct
```

This is a real regression-baseline blocker: the test's expected Phase3B03 connector projection fields no longer match the current CRM metadata. The affected CRM metadata is outside T05's allowed paths, and changing either the metadata or contract assertion would violate the phase boundary. No workaround, assertion relaxation, or business-logic change was made.

## Failure Propagation

`run-tests.ps1 all` reported Extension as `FAIL` and exited `1`. The outer gate parsed all six suite summaries, retained the individual test counts, marked the required Extension suite as failed, produced a JSON result, and exited `1`. This confirms required-suite failure propagation remains fail-closed after adding Runtime and Baseline.

## Recommendations

1. Assign the Phase3B03 Lead metadata/contract mismatch to the owning CRM metadata phase; decide whether the two expected fields should be restored or whether the existing contract assertion should be revised under explicit connector-contract authority.
2. Do not declare the regression baseline frozen until that owner change is independently reviewed and `run-regression-gate.ps1` returns `0`.
3. Keep live EspoCRM installation/upgrade/rollback as a later, explicitly provisioned test phase. T05 provides archive-level evidence only and must not be reported as live installation proof.
4. Preserve the complete Connector suite pattern (`test_*.py`) as new Phase3C tests are added, so the stable entrypoint does not silently omit later phases.

## Scope Audit

```
CRM entity modified:                    NO
Connector Contract modified:            NO
Scoring modified:                       NO
Workflow modified:                      NO
UI metadata modified:                   NO
CRM/database/external system contacted: NO
Production data imported:               NO
```

T05 changes are confined to `scripts/testing`, `tests`, and `docs`.
