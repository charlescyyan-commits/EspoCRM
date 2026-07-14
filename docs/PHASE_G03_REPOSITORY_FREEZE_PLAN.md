# Phase G03 — Repository Freeze Preparation Plan

**Date:** 2026-07-14  
**Mode:** repository hygiene only; no source, metadata, contract, runtime, migration, or test-behaviour changes were made.  
**Freeze verdict:** **NOT READY TO FREEZE**. Phase3C10.6 Evidence Production Alignment is still an active change set, and the worktree must first be separated into coherent commits.

## 1. Git status snapshot and classification

`git status --porcelain -uall` was inspected on 2026-07-14. The fully expanded snapshot contains **294 entries**: **56 modified**, **1 deleted**, and **237 untracked**. The count can change while C10.6 work continues.

| Class | Snapshot count | Contents | Freeze handling |
|---|---:|---|---|
| A. Active development | 8 non-document files, plus C10.6 contract documentation | C10.6 ResearchEvidence entity metadata, connector mapper/contract, `ChituSyncService.php`, persistence implementation, C10.6 test, and duplicate-preflight helper | Keep isolated and do not stage until the C10.6 owner declares a stable boundary. |
| B. Completed phase changes | 164 | Accumulated C01–C10.5 acquisition/connector work, Prospecting metadata/UI work, U04 work, and test/harness work | Split by completed phase; do not combine with C10.6. |
| C. Documentation | 115 | Phase reports, architecture/release notes, test reports, and contract documentation | Review for consistency, then commit by the phase it documents or in one docs-only commit. |
| D. Generated artifacts | 7 untracked | `deployment/prospecting-extension-1.9.0` through `1.9.5` ZIP/checksum additions | Do not treat as a source commit; see artifact proposal. |
| E. Local temporary files | 551 ignored files, 27,562,223 bytes | `temp/` backups, test logs/results, UI snapshots, and debug helpers | Remain out of Git. Retain or dispose only under the proposal below. |

The `temp/` rule in `.gitignore` already excludes all checked local-temporary examples. No `.gitignore` change is needed for this snapshot. Git emitted an environment warning while reading the user-global ignore file (`C:\Users\98624/.config/git/ignore`); repository `.gitignore` classification still worked and should be rechecked in the final freeze environment.

### A. Active C10.6 boundary

The following must remain outside all unrelated commits while Evidence Production Alignment is active:

- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`
- Root and module `ResearchEvidence.json` entity definitions
- `chitu-connector/chitu_connector/espocrm_sync/{contract.py,mapper.py,research_evidence_persistence.py}`
- `chitu-connector/tests/test_phase3c10_6_evidence_production_alignment.py`
- `deployment/provisioning/phase3c10_6_check_research_evidence_duplicates.php`
- `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json` and the C10.6 reports

This plan does not alter any of those files.

### B/C. Completed work and documentation

The remaining tracked/untracked source, metadata, UI, connector, test, `scripts/testing`, and phase-report files are accumulated completed work. The status list shows multiple independent phase families (acquisition foundation, C06–C10.5 projections/outreach boundaries, U01–U04 UI, and T01–T06 test harnesses). They are not one safe “catch-all” commit.

## 2. Artifact cleanup proposal (inventory only; no deletion)

### `deployment/`

| Finding | Evidence | Proposed later action |
|---|---|---|
| Historical ZIP chain | Unversioned ZIP, `v1.2.0`, then `1.3.1` through `1.9.5` alpha ZIPs are present. | Retain unchanged through freeze. After a release-retention decision, move superseded packages to an external/archive location rather than deleting them in a source commit. |
| Duplicate/ambiguous names | Both unversioned and differently prefixed early packages exist. | Designate one immutable release artifact naming convention for the post-C10.6 package; do not rename historical files during active work. |
| Checksum coverage gap | `1.9.1`–`1.9.5` ZIPs have no adjacent `.sha256` file; C10.6 has no new package artifact yet. | In a later release-packaging task, generate a manifest and checksum for the final package. Do not infer that `1.9.5` represents C10.6. |

### `temp/`

| Finding | Evidence | Proposed later action |
|---|---|---|
| Active rollback material | `temp/backups/phase3c10_6_1-20260714-151113/`, including a 25,131,853-byte `espocrm.sql` and runtime copies | **Retain.** This is C10.6.1 activation/rollback evidence; require explicit retention approval before removal. |
| Repeated test logs/results | `temp/test-results/` and legacy C06 output files | After final gate evidence is recorded and the retention window expires, remove or archive logs by dated run. |
| Debug helpers | `temp/_debug_formula.php`, `_verify_formula.php`, `_verify_metadata.php`, `check_clientdefs.php` | Confirm they are not part of an active runbook, then remove locally or archive with the diagnostic record. Never commit them. |
| UI snapshot | `temp/dashboard_preferences_before_20260714T000000Z.json` | Retain until U04 UI acceptance is signed off; then apply the same local retention policy. |

No artifact, backup, test log, or debug file was deleted or moved in Phase G03.

## 3. Deleted-file verification — `JobsWaiting.php`

**Verdict: intentional replacement; do not restore.**

The deleted primary filter previously restricted `SearchJob.status` to `WAITING`. Its replacement, `Classes/Select/SearchJob/PrimaryFilters/JobsQueued.php`, restricts the status to `QUEUED`. The active metadata references the replacement:

- `Resources/metadata/selectDefs/SearchJob.json` maps `jobsQueued` to `JobsQueued` and has no `jobsWaiting` mapping.
- `Resources/metadata/dashlets/AcquisitionJobsWaiting.json` now presents “Queued Jobs” and uses primary filter `jobsQueued`.

The deletion is currently uncommitted, not a disappearance requiring recovery. Commit the deletion **atomically** with `JobsQueued.php`, the SearchJob select definition, the dashlet, and associated labels/layout changes. A commit containing only the deletion could leave a broken filter boundary; restoring `JobsWaiting.php` would reintroduce the obsolete `WAITING` vocabulary.

## 4. Recommended commit boundaries (proposal only)

| Order | Commit boundary | Include | Exclude |
|---:|---|---|---|
| 1 | `phase3c10.6-evidence-production-alignment` | Only the active C10.6 list above and directly matching C10.6 reports | Any U04, prior connector, test-harness, or package history. Do not create until C10.6 is stable. |
| 2 | `phase-u04-prospecting-ui-polish` | U04 layouts, client definitions, dashlets, language files, UI validation/report | Evidence runtime, connector contract, state/lifecycle logic. |
| 3 | `phase-searchjob-queued-filter-normalization` | `JobsWaiting.php` deletion, `JobsQueued.php`, SearchJob selectDefs/dashlet/i18n, and their scoped tests/docs | Unrelated U04 and C10.6 work. |
| 4 | `phase-t01-t06-regression-harness` | `scripts/testing/`, `tests/`, extension test additions, and T01–T06 reports | Production source and metadata unrelated to harness support. |
| 5 | `phase-c01-c10.5-completed-work` | Remaining completed acquisition/connector work, divided further by phase if reviewer needs bisectable history | C10.6 active files and historical package ZIPs. |
| 6 | `docs-freeze-records` | Cross-phase documentation not already committed with its implementation | Generated packages, local `temp/`, source changes. |
| 7 | `release-artifact-manifest` (future) | One approved post-C10.6 ZIP, checksum, and manifest only | Historical ZIP rewrite/deletion and any source changes. |

## Freeze exit criteria

1. C10.6 owner declares the Evidence change set stable and its required gate is recorded.
2. Each proposed boundary is reviewed from `git diff --cached` before commit; no broad `git add .`.
3. The final release package is rebuilt from the selected commit and given a checksum/manifest.
4. `temp/` retention is explicitly decided; the C10.6.1 backup is preserved until that decision.
5. Run the existing T06 freeze gate from the final candidate commit and attach its result to the release record.

## Scope confirmation

Phase G03 made only this plan document. It did **not** delete files, commit changes, alter business logic, modify CRM metadata, change connector behaviour/contract, modify Evidence persistence, or change test behaviour.
