# Phase T03 - Core Regression Gate Report

**Date:** 2026-07-13  
**Phase:** T03 - Core Regression Gate

## Verdict

**PASS**

## Phase status

**DONE**

## Scope

T03 adds an offline, fail-closed regression-gate wrapper around T02. It does not change business logic or existing test assertions.

## Added or updated files

- `scripts/testing/run-regression-gate.ps1` - single-command, fail-closed gate wrapper.
- `scripts/testing/regression-gate-map.json` - maintained change-area mapping and suite classifications.
- `docs/testing/CORE_REGRESSION_GATE.md` - operator and CI02 interface documentation.
- `docs/testing/UNIFIED_TEST_ENTRYPOINTS.md` - link to the gate.
- `docs/testing/REGRESSION_MATRIX.md` - gate command and mapping reference.
- `docs/testing/TEST_INVENTORY.md` - core-gate inventory reference.
- `docs/PHASE_T03_CORE_REGRESSION_GATE_REPORT.md` - this report.

## Gate entrypoint

`powershell -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1`

The gate resolves its repository, mapping, and T02 runner from the script location and can therefore run outside the repository root. It delegates real test execution to `run-tests.ps1 regression`; it does not duplicate or change test assertions.

## Required suites

| Classification | Suite | Current behavior |
|---|---|---|
| REQUIRED | Extension | Extension metadata plus JSON/static validation |
| REQUIRED | Connector | Connector and contract tests |
| REQUIRED | Worker | Acquisition worker, persistence, and runner tests |
| REQUIRED | Static | Deployment-static validation |
| REQUIRED | Runner integrity | T02 runner exists and emits complete, parseable required-suite summaries |
| CONDITIONAL | Browser, runtime REST/worker, package lifecycle | Explicit `NOT_IMPLEMENTED`, non-blocking until T04/T05/T06 provide real suites |
| OPTIONAL | Performance baseline, documentation review | Informational only |

Any REQUIRED failure, unparseable runner output, missing runner/dependency, skipped required suite, or JSON-write failure is fail-closed.

## Change-trigger mapping

The mapping is maintained in `scripts/testing/regression-gate-map.json`. It supports explicit changed paths and dirty working trees, but never narrows the executed required set: every run executes all four real core suites plus runner integrity.

| Input category verified | Mapped area | Gate behavior |
|---|---|---|
| `docs/**` | `docs-only` | Full core gate; no invented runtime requirement |
| `crm-extension/**` | `crm-extension` | Full core gate; browser acceptance reported `NOT_IMPLEMENTED` |
| `chitu-connector/**` | `chitu-connector` | Full core gate; runtime REST adapter reported `NOT_IMPLEMENTED` |
| `chitu-connector/chitu_connector/acquisition/**` | `chitu-connector`, `worker` | Full core gate; runtime worker execution reported `NOT_IMPLEMENTED` |
| `scripts/testing/**` | `testing-infrastructure` | Full core gate and runner integrity |
| `deployment/**` | `deployment` | Full core gate; package lifecycle reported `NOT_IMPLEMENTED` |
| unknown path | `unknown` | Full core gate; no reduced selection |

## Actual validation results

| Check | Result |
|---|---|
| Normal gate | PASS; 131 discovered / 131 passed / 0 failed / 0 skipped; exit 0 |
| Required suites | 5/5 passed, including runner integrity |
| Human summary | PASS; reports each required suite, totals, overall status, and exit code |
| JSON result | PASS; parsed successfully with schema version, totals, areas, suite commands/counts/log paths, failures, and warnings |
| JSON secret scan | PASS; no test credentials, API keys, or environment values recorded |
| Child failure propagation | PASS; temporary non-Python child executable caused gate `FAIL`, four failed required suites, exit 1 |
| Missing dependency | PASS; no default Python produced exit 3 |
| Invalid configuration | PASS; temporary invalid mapping produced exit 2 |
| Blocking conditional | PASS; temporary mapping with a blocking unmet requirement produced `BLOCKED`, gate `FAIL`, exit 5 |
| Invocation outside repo | PASS; full gate exited 0 from a caller path containing spaces |
| Mapping categories | PASS; docs-only, extension, connector, worker, testing-infrastructure, deployment, and unknown were all classified and still ran the full core gate |

The normal validation used the local bundled Python 3.12 executable through `-PythonExecutable` because `python` was not on this shell's `PATH`. The runner's documented standard path remains Python on `PATH`.

## Exit codes

| Code | Verified meaning |
|---:|---|
| 0 | Gate passed |
| 1 | Required suite child failure propagated |
| 2 | Invalid gate map or unparseable gate configuration |
| 3 | Required Python dependency/entrypoint missing |
| 4 | Implemented for machine-readable result write failure; not deliberately induced because it would require breaking the approved local result directory |
| 5 | Blocking conditional requirement unmet |

## CI02 readiness

**READY.** CI02 can invoke one Windows command, consume the JSON path printed by the gate, use stable exit codes, and retain per-suite logs. No CI workflow was created in T03.

## Current non-implemented layers

- Runtime harness and automated cleanup verification (T04)
- Browser acceptance (T05)
- Install / upgrade / rollback lifecycle tests (T06)
- Performance baselines (T07)

These layers are explicitly represented as `NOT_IMPLEMENTED`, never as passing tests.

## Parallel conflict and scope audit

The workspace began with unrelated Phase 3C modifications in protected extension and deployment paths. T03 did not reset, clean, restore, format, stage, commit, push, or otherwise alter them. Temporary probes and result logs were removed after validation.

```
Business logic modified: NO
Existing test assertions modified: NO
SearchStrategy modified: NO
SearchJob modified: NO
ProspectPool modified: NO
Deployment modified: NO
Manifest modified: NO
Database modified: NO
External system accessed: NO
Git commit created: NO
Git push performed: NO
```

T01 and T02 conclusions were preserved. No T04 work or CI workflow was started.
