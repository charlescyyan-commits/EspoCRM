# Unified Test Entrypoints

Phase T02 provides one repeatable, offline-only PowerShell entrypoint for the test suites that currently exist in this repository.

Run from any directory:

```powershell
powershell -ExecutionPolicy Bypass -File D:\EspoCRM-Production\scripts\testing\run-tests.ps1 all
```

When `python` is not available on `PATH`, provide an explicit Python 3.12+ executable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testing\run-tests.ps1 all -PythonExecutable C:\Python312\python.exe
```

The runner resolves its repository root from its own location, sets `PYTHONPATH` for `chitu-connector`, and invokes only offline `unittest` suites. It does not call EspoCRM, a database, or an external system.

## Commands and suite mapping

| Argument | Required test mapping |
|---|---|
| `extension` | `crm-extension/tests/test_*.py` (extension metadata and JSON/static validation) |
| `connector` | `chitu-connector/tests/test_*.py` (complete connector, contract, pipeline, and deterministic acceptance coverage) |
| `worker` | `chitu-connector/tests/test_phase3c02_*.py` (worker, persistence, and runner tests) |
| `static` | `deployment/validation/test_*.py` (deployment-static validation only) |
| `runtime` | `tests/runtime/test_*.py` (offline runtime-harness safety and cleanup tests) |
| `baseline` | `tests/regression/test_*.py` (extension archive build, install preflight, and complete JSON metadata validation) |
| `regression` | The required `extension`, `connector`, `worker`, `static`, `runtime`, and `baseline` sets |
| `all` | The regression set plus explicit notices for optional layers not yet implemented |
| `help` | Prints runner usage without executing tests |

The connector set contains the complete current connector test inventory. The extension set includes metadata and JSON validation. The baseline set builds a temporary extension archive and validates its EspoCRM install layout; it is not a live CRM installation. The runner deliberately excludes live acceptance, provisioning, browser, performance, and install/upgrade/rollback work from `all` because those layers are not implemented as safe offline suites.

For a fail-closed, machine-readable admission check over this same required set, use the [Core Regression Gate](CORE_REGRESSION_GATE.md).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All required suites passed. |
| `1` | One or more suites failed. |
| `2` | Invalid arguments or runner configuration error (including zero tests discovered). |
| `3` | Python or a required test entrypoint is missing. |

Each executed suite prints `Suite`, `Status`, `Command`, test counts, `Duration`, `Exit code`, and `Log path`, followed by a final test summary. Test logs are written to `temp/test-results/<suite>-<timestamp>.log`; that directory is ignored by Git.

## Common failures

- **Exit 3 / Python not found:** install Python 3.12+ or pass `-PythonExecutable`.
- **Exit 3 / test entrypoint missing:** restore the expected test directory; the runner does not replace missing tests with a false pass.
- **Exit 1:** open the suite log printed in the summary and fix the failing existing test or working-tree inconsistency.
- **Live test expectation:** use the dedicated runtime acceptance workflow in a later phase. T02 does not run it or create test data.

## Adding a suite

Add a real offline test directory or discovery pattern first. Then add a definition in `scripts/testing/run-tests.ps1`, list the required paths, and update the mapping table above plus `TEST_INVENTORY.md` and `REGRESSION_MATRIX.md`. A suite that discovers no tests is a configuration error, not a passing placeholder.
