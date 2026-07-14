# Phase T02 - Unified Test Entrypoints Report

**Date:** 2026-07-13  
**Phase:** T02 - Unified Test Entrypoints

## Verdict

**PASS** - All currently implemented required offline test entrypoints completed successfully.

## Scope

T02 adds offline test-running infrastructure only. It does not alter CRM extension, connector business, SearchStrategy, SearchJob, ProspectPool, deployment, runtime configuration, or database behavior.

## Added or updated files

- `scripts/testing/run-tests.ps1` - unified PowerShell runner.
- `docs/testing/UNIFIED_TEST_ENTRYPOINTS.md` - commands, mappings, exit codes, logs, and extension guidance.
- `docs/testing/TEST_INVENTORY.md` - T02 entrypoint reference.
- `docs/testing/REGRESSION_MATRIX.md` - T02 regression entrypoint reference.
- `docs/PHASE_T02_UNIFIED_TEST_ENTRYPOINTS_REPORT.md` - this report.

## Runner mapping

| Entry point | Real suite mapping |
|---|---|
| `extension` | `crm-extension/tests/test_*.py` |
| `connector` | `chitu-connector/tests/test_espocrm_*.py`, including contract tests |
| `worker` | `chitu-connector/tests/test_phase3c02_*.py` |
| `static` | `deployment/validation/test_*.py` |
| `regression` | Required extension, connector, worker, static, contract, metadata/JSON validation sets |
| `all` | Regression set; browser, performance, and install/upgrade/rollback explicitly reported as not implemented |

The runner resolves the repository root from its own path, makes `chitu-connector` available through `PYTHONPATH`, and writes timestamped suite logs to ignored `temp/test-results/` paths. It uses exit code `0` for pass, `1` for suite failures, `2` for invalid arguments or configuration errors, and `3` for a missing Python executable or required test entrypoint.

## Validation results

| Command / check | Tests passed | Failed | Skipped | Exit code | Result |
|---|---:|---:|---:|---:|---|
| `help` | - | - | - | 0 | PASS |
| `extension` | 40 | 0 | 0 | 0 | PASS |
| `connector` | 58 | 0 | 0 | 0 | PASS |
| `worker` | 31 | 0 | 0 | 0 | PASS |
| `static` | 2 | 0 | 0 | 0 | PASS |
| `regression` | 131 | 0 | 0 | 0 | PASS |
| `all` | 131 | 0 | 0 | 0 | PASS; executed from a caller directory containing spaces |
| invalid suite argument | - | - | - | 2 | PASS - invalid arguments are rejected |
| missing default Python | - | - | - | 3 | PASS - missing dependency is explicit |
| temporary child-process failure probe | 0 | 0 | 0 | 1 | PASS - runner propagated a non-zero child result |

Validation used the local bundled Python 3.12 executable passed through `-PythonExecutable`, because `python` was not available on this shell's `PATH`. The normal entrypoint remains `python` on `PATH`; the explicit parameter is the documented fallback.

`all` reported these optional layers as `NOT IMPLEMENTED` / `SKIPPED - no test suite implemented`: browser acceptance, performance baseline, and install/upgrade/rollback. They do not affect T02's required offline result.

## T01 High reliability risks

| Risk | T02 status | Evidence / follow-up |
|---|---|---|
| R01 - hardcoded provisioning test credentials | DEFERRED | Requires changes to provisioning scripts and credential handling, which are outside T02's runner-only scope. Address in a dedicated security/provisioning phase. |
| R02 - no automated cleanup verification for runtime tests | DEFERRED | Requires a runtime harness and CRM residue check. T02 runs no runtime or provisioning tests and creates no test data. Address in T04. |

## Not implemented test layers

- Browser acceptance
- Performance baseline
- Install / upgrade / rollback
- Reusable runtime REST harness and automatic cleanup verification

## Parallel conflict and scope audit

The preflight working tree already contained unrelated Phase 3C changes, including protected extension and deployment files. T02 did not modify, reset, clean, restore, stage, commit, or otherwise alter those changes. Its runner and documentation changes are confined to the allowed T02 paths.

```
Business logic modified: NO
SearchStrategy modified: NO
SearchJob modified: NO
ProspectPool modified: NO
Deployment modified: NO
Database modified: NO
External system accessed: NO
Git commit created: NO
Git push performed: NO
```

Temporary validation probes and logs were removed after verification. No T03 work was started.
