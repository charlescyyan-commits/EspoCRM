# Phase G03.6 - Final Release Verification Report

**Date:** 2026-07-14
**Verdict:** **FAIL - tag created, but the required clean Regression Gate is 6/7 PASS**

## Tag information

| Item | Value |
|---|---|
| Tag | `v1.9.5-alpha` |
| Tag type | Annotated |
| Target commit | `d004397b8c8a28baa4cdc33415899860f127c1f3` |
| Target subject | `Release: v1.9.5-alpha candidate artifact` |

`git show v1.9.5-alpha` confirms that the tag resolves to the required release
evidence commit. The tagged manifest declares `1.9.5-alpha` and the commit
contains `deployment/v1.9.5-alpha.zip`, its SHA256 sidecar, and the G03.4
release-candidate build report.

## Artifact evidence

| Item | Value |
|---|---|
| Artifact | `deployment/v1.9.5-alpha.zip` |
| SHA256 | `09E2E4E3543E3583A74672B69E4CEC2059EE39186784DD31456BDC59E6B4D1B2` |
| SHA256 sidecar | `deployment/v1.9.5-alpha.zip.sha256` |
| Sidecar verification | PASS - recomputed value matches exactly |

## Clean Regression Gate

The release source was exported from commit `d004397b8c8a28baa4cdc33415899860f127c1f3`
to an isolated `C:\tmp` snapshot. The current `scripts/testing/` gate runner and
root-level `tests/` were supplied only as external test tooling because they are
not committed in the tagged release; no working-tree product source was used.

| Item | Value |
|---|---|
| Command | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` |
| Started (UTC) | `2026-07-14T08:31:35.1481387Z` |
| Finished (UTC) | `2026-07-14T08:31:39.3439515Z` |
| Gate result timestamp (UTC) | `2026-07-14T08:31:39.0888171Z` |
| Exit code | `1` |
| Required suites | `6/7 PASS` |
| Tests | `373 passed / 381 discovered / 8 failed / 0 skipped` |

| Required suite | Result |
|---|---|
| Extension | FAIL - 56 passed, 8 failed |
| Connector | PASS - 270 passed |
| Worker | PASS - 31 passed |
| Static | PASS - 2 passed |
| Runtime | PASS - 11 passed |
| Baseline | PASS - 3 passed |
| Runner integrity | PASS |

### Blocking failures

All eight failures are in the committed Extension suite:

- `test_contract_field_consistency`
- `test_manifest_json_valid` (still expects `1.8.0-alpha`)
- `test_only_standard_research_evidence_php_shells_exist`
- `test_phase3b03_connector_routes_and_proposal_model`
- `test_phase3b06_prospecting_workspace_ui`
- `test_phase3b07_operations_metadata`
- `test_phase3c01_acquisition_workspace_foundation`
- `test_phase3c02_1_acquisition_acl_provisioning`

The requested 7/7 PASS condition is therefore not met. No code or test changes
were made to mask, repair, or rerun these failures.

## Working-tree notes

The primary workspace was not cleaned or altered. Before this report was added,
it contained one unrelated unstaged test-file modification and untracked
`docs/PHASE_G04_C11_READINESS_REVIEW.md`, `scripts/testing/`, and `tests/`.
Those paths were excluded from the release snapshot and were not modified,
staged, committed, or removed.

No branch was created, no commit history was rewritten, no C11 work was run,
and no runtime or business-code source files were changed by this phase.
