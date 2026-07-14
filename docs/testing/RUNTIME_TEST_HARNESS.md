# Runtime Test Harness

T04 provides a local-only REST harness separate from the offline T03 gate. It uses Python standard library modules only and never contacts a provider or production target.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 check
powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 smoke
powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 all
```

Use `-PythonExecutable` when Python is not on `PATH`. The runner finds the repository from its own location and supports callers outside the repository root.

## Commands

| Command | Behavior |
|---|---|
| `check` | Guard, authenticated JSON preflight; no writes. |
| `smoke` | Lead and ResearchEvidence create/read/update/relationship checks, followed by automatic cleanup and residue audit. |
| `acl` | Unauthenticated and invalid-key denial checks; denied-write role is skipped unless a dedicated credential is added later. |
| `cleanup-preview` | Lists only fixtures in the exact run registry; never deletes. Requires `-RunId`. |
| `cleanup` | Cleans only registered fixtures for `-RunId`, verifies markers and 404 after delete. |
| `all` | Smoke plus ACL, with cleanup attempted even after a smoke failure. |

Each run uses `CHITU_RT_<UTC timestamp>_<random>` (or the configured prefix) as its only marker. Fixture records are registered immediately in `temp/test-results/runtime-fixtures-<runId>.json`. Cleanup uses the registered fixture IDs in reverse dependency order and refuses deletion if the current record does not contain the exact marker. Residue audit checks only current-run registered fixtures.

Machine-readable results are written to `temp/test-results/runtime-test-<runId>.json`. They contain run metadata, status, counts, fixture cleanup outcomes, warnings, and failures; credentials and request headers are excluded.

Exit codes: `0` pass, `1` test failure, `2` configuration, `3` missing dependency/credential, `4` cleanup or residue failure, `5` safety guard block.

T04 is not part of T03. It becomes CI-eligible only after a dedicated disposable test environment, credential, stable cleanup, and zero-residue evidence are available.
