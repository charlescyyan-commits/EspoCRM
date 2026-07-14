# Phase G03 - Repository Freeze Execution Report

**Date:** 2026-07-14
**Scope:** Repository-freeze preparation: temporary-artifact retention, deployment-artifact organization, SHA-256 coverage, and Git-status classification.

## Verdict

**PREPARED, BUT NOT READY FOR FINAL GIT FREEZE.**

Artifact hygiene is complete: the active deployment directory now contains only the current package and its checksum, while temporary data is retained in a recoverable archive. The repository still has release-code, test, and documentation changes that require an explicit inclusion/exclusion decision before staging. In particular, Connector, Evidence, and unfinished ACL03 paths remain present and were not changed by this phase.

No commit was created.

## 1. Temporary-artifact execution

`temp/` was reorganized without deletion. It now contains **0 files**; empty directory containers were left in place.

| Source class | Retained destination | Count / evidence | Freeze label |
| --- | --- | --- | --- |
| C10.6 runtime backup | `archive/runtime-backups/phase3c10_6_1-20260714-151113/` | 335 files, including `espocrm.sql` (25,131,853 bytes) | Required backup - retain |
| Test logs and result JSON | `archive/audit-artifacts/test-results/20260713-20260714/` | 213 files | Audit artifact - retain |
| C06 transcripts | `archive/audit-artifacts/c06-test-transcripts/` | 5 `.txt` files | Historical audit artifact - retain |
| Dashboard-preference snapshot | `archive/audit-artifacts/dashboard-preferences/` | 1 JSON file | Required UI audit evidence - retain |
| One-off diagnostics | `archive/debug-scripts/20260712-20260713/` | 4 PHP files | Obsolete/debug - not release code |

The retained C10.6 SQL backup has SHA-256:

```text
B7ED6830E117ED955EE727F514CB837A45DB45220715D422D29AE074E04BD0F2
```

## 2. Deployment-artifact execution

### Active deployment surface

`deployment/` now retains only:

```text
prospecting-extension-1.9.5-alpha.zip
prospecting-extension-1.9.5-alpha.zip.sha256
```

The checksum sidecar was added in the existing repository format and verifies the active ZIP:

```text
927E0BC67E670C66625AB2631AA7B361BCCD3FF20B25D8502E0DF7218CF1C7E4  prospecting-extension-1.9.5-alpha.zip
```

### Historical packages

- Moved **18** historical ZIPs from `deployment/` to `archive/deployment/historical-packages/`.
- Moved legacy checksum sidecars with their corresponding historical packages.
- Added `archive/deployment/historical-packages/SHA256SUMS.txt` to record SHA-256 values for all archived ZIPs, including versions that did not previously have individual sidecars.
- SHA-256 comparison found no byte-identical duplicate packages. Historical packages are retained for rollback/investigation, not as active deployment inputs.

`archive/README.md` records the retention layout and restoration boundary.

## 3. Git status classification

The worktree is intentionally **not staged** and **not committed**. Current porcelain status was classified as follows:

| Category | Total | Modified/deleted | Untracked | Interpretation |
| --- | ---: | ---: | ---: | --- |
| A - Release code | 136 | 53 | 83 | Requires deliberate release-scope selection. Includes CRM extension, Connector, provisioning, and scripts. |
| B - Tests | 38 | 2 | 36 | Requires test-baseline decision with the selected release code. |
| C - Docs | 134 | 4 | 130 | Includes phase reports, DOC01, documentation center work, and archive documentation. |
| D - Artifacts | 269 | 18 | 251 | Includes the archival relocation and active package/sidecar. The 18 historical ZIP deletions become renames only if the matching archive destinations are staged later. |

### Freeze blockers outside G03 authority

The following categories remain in the worktree and were classified but not modified:

- **Connector:** modified and untracked `chitu-connector/` implementation paths.
- **Evidence:** ResearchEvidence metadata/client/UI, Evidence connector paths, tests, provisioning, and phase reports.
- **ACL03:** the sales-manager field-visibility provisioning script, its test, and related documentation.

These paths are not silently removed, moved, staged, or altered because they are excluded from this phase. A final freeze must explicitly decide whether to include, separately complete, or revert them under authorized work.

## 4. Validation

| Check | Result |
| --- | --- |
| `temp/` file count | PASS - 0 remaining files |
| C10.6 backup retained | PASS - archive path and SQL hash verified |
| Active deployment ZIP count | PASS - 1 (`1.9.5-alpha`) |
| Historical ZIP count | PASS - 18 retained in archive |
| Active SHA-256 sidecar | PASS - hash matches ZIP |
| Historical exact duplicates | PASS - none found |
| Business/Connector/Evidence/ACL03 code changes by G03 | PASS - none made |
| Commit created | PASS - none |

## Files added by G03

- `archive/README.md`
- `archive/deployment/historical-packages/SHA256SUMS.txt`
- `deployment/prospecting-extension-1.9.5-alpha.zip.sha256`
- `docs/PHASE_G03_FREEZE_EXECUTION_REPORT.md`

All other G03 filesystem changes are recoverable moves into `archive/`; no file was deleted.

## Next authorized freeze step

Select the exact release set from categories A, B, and C, resolve the excluded Connector/Evidence/ACL03 work separately, then stage the selected code/tests/docs together with the archive moves so Git records package relocations rather than standalone deletions. Do not commit until that selection is approved.
