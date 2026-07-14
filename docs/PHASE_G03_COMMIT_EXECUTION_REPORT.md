# Phase G03 - Commit Separation Execution Report

**Date:** 2026-07-14
**Scope:** Execute the approved freeze commit boundaries without changing business logic and without including C11 files.

## Result

The requested boundaries were separated into the existing C10.6 and ACL03 commits, a new U04 documentation commit, this documentation commit, and a subsequent release-cleanup commit.

No C11-named files were found in the repository before staging or committing.

## Commit boundaries

| Order | Boundary | Commit | Contents | Validation |
| ---: | --- | --- | --- | --- |
| 1 | C10.6 Evidence Alignment | `e8d1899` | Evidence persistence production alignment: PHP writer, ResearchEvidence identity metadata, connector contract/mapper/persistence utility, duplicate preflight, V1 contract, and focused test | Evidence alignment 6/6 PASS; extension skeleton 38/38 PASS |
| 2 | U04 UI | `c70db67` | U04 dashboard-cleanup, UI-polish, and browser-acceptance reports. The matching native UI metadata was already committed in `f7acc1b` (`phase-c06`) before this execution; no source rewrite was performed. | Extension suite 65/65 PASS |
| 3 | ACL03 | `7a2f02d` | Sales Manager field-visibility provisioning script, 8-test static ACL suite, ACL02 review, and ACL03 report | ACL03 suite 8/8 PASS |
| 4 | Documentation | This commit | README, documentation center, architecture/deployment/release/testing/user-guide documents, phase reports, and this execution record | Documentation link/version validation PASS |
| 5 | Release cleanup | Subsequent commit | Active 1.9.5 checksum, historical-package relocation, archive retention rules, and G03 cleanup evidence | SHA-256/archive inventory validation PASS |

## Ordering note

At execution start, `e8d1899` (C10.6) and `7a2f02d` (ACL03) were already present in the shared branch, in that order. The U04 source metadata was already included in the earlier `f7acc1b` C06 UI commit. Rewriting or reordering existing shared history would be destructive and was not performed. The remaining U04 report boundary was committed as `c70db67` after the already-existing ACL03 commit.

## Test evidence

```text
C10.6 EvidenceProductionAlignmentTests: 6/6 PASS
Extension skeleton suite:             38/38 PASS
Full crm-extension suite:             65/65 PASS
ACL03 SalesManagerFieldVisibility:     8/8 PASS
```

Documentation validation checks relative links in the Documentation Center, release index, and reports index. Release cleanup validation verifies that the active `1.9.5-alpha` ZIP matches its SHA-256 sidecar and that all archived historical ZIPs match `SHA256SUMS.txt`.

## C11 exclusion

A filename scan for `C11` / `Phase3C11` returned no repository candidates. No C11 file was staged or committed by this execution.

## Release-cleanup boundary

The release-cleanup commit includes only repository-safe release artifacts:

- `deployment/prospecting-extension-1.9.5-alpha.zip.sha256`
- historical deployment ZIP moves to `archive/deployment/historical-packages/`
- `archive/deployment/historical-packages/SHA256SUMS.txt`
- archive retention documentation and ignore rules

The local C10.6 backup, audit logs, dashboard snapshot, and diagnostic scripts remain retained locally under `archive/` but are ignored from Git. They are not release inputs and are not committed.

## Boundary protection

- No business logic was edited for commit separation.
- No C11 content was introduced.
- Existing C10.6 and ACL03 history was not rewritten.
- No commit includes local SQL backups, test logs, or debug scripts.
