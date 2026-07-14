# Core Regression Gate

The T03 Core Regression Gate is the CI02-ready offline admission check. It always runs the complete current core set; change detection only records impact and never reduces required coverage.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testing\run-regression-gate.ps1
```

When Python is not on `PATH`, pass a Python 3.12+ executable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testing\run-regression-gate.ps1 -PythonExecutable C:\Python312\python.exe
```

The script locates the repository and the T02 runner from its own path, so it can be invoked outside the repository root. It is offline-only: no CRM, database, or external system is contacted.

## Required suites

The gate runs these real T02 suites every time:

| Suite | Coverage |
|---|---|
| Extension | Extension metadata plus JSON/static validation |
| Connector | Connector and contract tests |
| Worker | Acquisition worker, persistence, and runner tests |
| Static | Deployment-static validation |
| Runtime | Offline runtime-harness safety and cleanup tests |
| Baseline | Extension package build, install preflight, and full metadata JSON validation |
| Runner integrity | T02 runner existence and complete, parseable suite output |

Any required failure fails the gate. A missing runner, missing dependency, missing required suite, malformed runner summary, or missing JSON result is fail-closed.

## Change mapping

`scripts/testing/regression-gate-map.json` maps paths to areas and reasons. The gate accepts `-ChangedPath` for callers that already know their changed paths; otherwise it can classify the current Git working tree. This classification is advisory for reporting: the gate always runs all required suites, including when the changed area is unknown or Git information is unavailable.

| Area | Mapped impact |
|---|---|
| `docs-only` | No extra runtime requirement; full core gate still runs |
| `crm-extension` | Extension and static required; browser acceptance reported as not implemented |
| `chitu-connector` | Connector and worker required; runtime REST adapter reported as not implemented |
| `worker` | Worker and connector required; runtime worker execution reported as not implemented |
| `testing-infrastructure` or `tests` | Full required gate and runner integrity |
| `deployment` or `manifest` | Extension and static required; package lifecycle reported as not implemented |
| `unknown` | Full core gate, never a reduced selection |

## Classifications

- **REQUIRED**: blocks the gate on failure.
- **CONDITIONAL**: reported when its change area is present. A conditional can block only when its mapping marks it blocking. Current unimplemented runtime/browser/package layers are explicitly `NOT_IMPLEMENTED` and non-blocking.
- **OPTIONAL**: informational and never changes the gate result.
- **NOT_IMPLEMENTED**: no suite exists; never presented as a pass.

## Results and exit codes

Each run writes `temp/test-results/regression-gate-<timestamp>.json` plus the existing per-suite logs from T02. The JSON schema includes gate metadata, changed areas, suite commands and counts, totals, failures, warnings, and status values limited to `PASS`, `FAIL`, `SKIPPED`, `BLOCKED`, and `NOT_IMPLEMENTED`.

| Exit code | Meaning |
|---|---|
| `0` | Gate passed. |
| `1` | A required suite failed. |
| `2` | Gate configuration is invalid or runner output cannot be parsed. |
| `3` | A required dependency or entrypoint is missing. |
| `4` | Machine-readable result generation failed. |
| `5` | A blocking conditional requirement was unmet. |

The console summary is for humans; the JSON is the stable CI02 interface. Neither output includes environment values, passwords, or API keys.

## Adding a suite

First add a real, offline suite to the T02 runner. Then update the required suite inventory and mapping in `regression-gate-map.json`, preserve the runner's summary fields, and update this document. Do not add a placeholder pass for a suite that does not exist.

## Current non-implemented layers

Browser acceptance, live runtime execution, live package installation/upgrade/rollback, and performance baselines are outside the current offline gate. Runtime-harness safety and package archive preflight are required offline suites.

## T07 final baseline (before C11.1)

Use the freeze wrapper with an explicit Python executable when Python is not on
`PATH`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-freeze-gate.ps1 -PythonExecutable <python-3.12-plus>
```

The 2026-07-14 T07 baseline is **7/7 required suites PASS**, **382/382 test
invocations PASS**, and exit code **0**: Extension 65, Connector 270, Worker
31, Static 2, Runtime 11, and package/metadata Baseline 3. Worker intentionally
overlaps the complete Connector suite, so the invocation total is not a count
of unique test definitions.

Before C11.1, a regression is any required-suite failure, non-zero freeze-gate
exit code, missing or unparseable gate result, or a reduction in required
suite coverage. Test-count changes are permitted only with a reviewed baseline
update and an all-suite PASS run. Browser and live-runtime acceptance remain
`NOT_IMPLEMENTED` outside this offline baseline; they must not be recorded as
passed without their own runtime evidence.
