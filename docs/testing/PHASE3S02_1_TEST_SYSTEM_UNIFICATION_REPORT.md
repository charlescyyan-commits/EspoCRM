# Phase3S02.1 — Test System Unification Report

## Scope

This phase unifies execution of existing offline release gates. It does not modify CRM extension business logic, connector logic, worker/provider behavior, release artifact contents, manifests, or versioning.

## Entry-point audit

| Entrypoint | Framework / purpose | Status |
| --- | --- | --- |
| `scripts/testing/run-tests.ps1` | Legacy T02 offline `unittest` suite map | Retained unchanged |
| `scripts/testing/run-regression-gate.ps1` | T03 mapped regression gate and JSON result | Retained unchanged |
| `scripts/testing/run-freeze-gate.ps1` | Freeze-specific required/conditional verification | Retained unchanged |
| `scripts/testing/run-runtime-tests.ps1` and `scripts/run-runtime-gate.ps1` | Disabled-by-default local runtime harness | Retained unchanged |
| `crm-extension/tests/` | Extension metadata/static tests | Included in unified gate |
| `chitu-connector/tests/` | Connector contract/unit/acceptance tests | Included in unified gate |
| `tests/` and `scripts/runtime/` | Root contracts and offline runtime tests | Included in unified gate |
| `tests/regression/` | Package baseline and S01 release integrity | Included in unified gate |
| `deployment/validation/` | Deployment-static validation | Included in `offline` profile |
| Live deployment acceptance / provisioning | Requires approved CRM credentials or writes | Audited but intentionally excluded |

## Unified runner

`scripts/testing/run-unified-gate.ps1` is an additive entrypoint. It does not replace the existing scripts or their command lines.

```powershell
# Current S01-compatible release gate.
powershell -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 -Profile release -PythonExecutable .\.venv-s01\Scripts\python.exe

# Release gate plus deployment-static validation.
powershell -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 -Profile offline -PythonExecutable .\.venv-s01\Scripts\python.exe
```

The runner resolves its own repository root, invokes each gate in the existing required working directory, writes command output to ignored `temp/test-results/`, prints per-gate pass/fail/count/exit-code summaries, and returns 0 only when every selected gate passes. It invokes no live CRM, database, provisioning, or network action.

## Compatibility

Existing direct commands remain valid, including `python -m pytest crm-extension/tests -q`, the connector command from `chitu-connector`, `python -m unittest discover -s crm-extension/tests`, and the existing PowerShell runners. The unified runner is a consolidated reporting and orchestration option, not a test rewrite.

## Execution evidence

The runner was executed with `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe` (Python 3.12.13, pytest 9.1.1). Both profiles returned exit 0.

| Offline profile gate | Result | Exit |
| --- | --- | ---: |
| Extension pytest | 75 passed (+22 subtests) | 0 |
| Connector pytest | 279 passed (+92 subtests) | 0 |
| Root/runtime pytest | 162 passed (+1042 subtests) | 0 |
| S01 integrity pytest | 12 passed (+297 subtests) | 0 |
| Package baseline pytest | 5 passed (+535 subtests), PowerShell parity not skipped | 0 |
| Extension unittest | 75 passed | 0 |
| Artifact `--check` | SHA-256 `2A3A1D88B2D7F01229801FD44F2AF73B84128445A86637564EF49F8D714B86DF` verified | 0 |
| Deployment validation pytest | 2 passed | 0 |

The connector suite emitted ten pre-existing deprecation warnings. Pytest also reported ignored-cache write warnings because existing `.pytest_cache` directories are inaccessible; these are not test failures and are not tracked. No business behavior was changed to obtain these results.
