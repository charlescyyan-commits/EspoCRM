# Phase3C16.1C PHP Lint Gate Report

## Implementation

Phase3C16.1C adds a required PHP syntax lint stage to the unified gate runner.

Changed file:

- `scripts/testing/run-unified-gate.ps1`

The new stage:

- Resolves PHP from `-PhpExecutable` when provided, otherwise from `php` on `PATH`.
- Fails fast with a clear message when PHP is unavailable.
- Scans `crm-extension/**/*.php`.
- Runs `php -l` for each discovered PHP file.
- Returns non-zero through the unified gate summary when any file fails syntax lint.

No business PHP, metadata, artifact builder, artifact logic, connector, worker, or provider code was changed.

## Commands

Explicit PHP executable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 -Profile offline -PythonExecutable .venv-s01\Scripts\python.exe -PhpExecutable C:\tmp\php-c16\runtime\php.exe
```

Compatibility failure check when `php` is not on `PATH`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 -Profile offline -PythonExecutable .venv-s01\Scripts\python.exe
```

Expected failure message:

```text
PHP was not found on PATH. Install PHP or pass -PhpExecutable explicitly; PHP syntax lint is required and is not skipped.
```

## Validation

Environment:

- Python: `.venv-s01\Scripts\python.exe`
- PHP: `C:\tmp\php-c16\runtime\php.exe`
- PHP version: `8.3.32`

Pre-validation:

- Missing PHP compatibility check: PASS, runner fails with an explicit required-lint message.
- Release profile with explicit PHP: PASS.
- PHP lint discovered files: 89.
- PHP lint failures: 0.

Final validation:

- Unified offline gate: PASS.
- PHP lint: 89 passed, 0 failed.
- Extension pytest: 86 passed.
- Connector pytest: 279 passed.
- Root/runtime pytest: 162 passed.
- S01 integrity pytest: 12 passed.
- Package baseline pytest: 5 passed.
- Extension unittest: 86 passed.
- Artifact check: PASS.
- Deployment validation pytest: 2 passed.

## Limitations

- PHP is not currently available on `PATH` in this workstation session. The gate therefore requires `-PhpExecutable` unless the environment installs PHP on `PATH`.
- The stage is syntax-only. It does not execute CRM runtime rebuilds, services, hooks, or integration workflows.
