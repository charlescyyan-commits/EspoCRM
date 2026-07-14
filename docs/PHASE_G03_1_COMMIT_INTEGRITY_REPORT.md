# Phase G03.1 — Git Freeze Integrity Verification

**Date:** 2026-07-14  
**Mode:** Read-only Git verification (except creation of this requested report)  
**Verdict:** **NEEDS FIX**

## Scope and method

Inspected `git log --stat -10`, `git show --name-status` for each of the ten
most recent commits, and `git status --porcelain=v1 --untracked-files=all`.
No commit, amend, reset, restore, or repair action was performed.

## 1. Recent boundary sequence

Newest to oldest:

| Commit | Subject | Boundary assessment |
| --- | --- | --- |
| `01fa599` | `docs: consolidate release and freeze records` | Documentation-only: README files and `docs/` only; 127 paths. |
| `b0e1988` | `Release: align v1.9.5-alpha metadata` | Additional release/version-alignment commit; not the requested Release cleanup boundary. |
| `c70db67` | `phase-u04: document prospecting UI polish` | U04 reports only; no UI metadata paths are present in this commit. |
| `7a2f02d` | `phase-acl03: constrain sales manager projection editing` | ACL03 provisioning, its test, and ACL docs. |
| `e8d1899` | `phase-c10.6: align evidence production persistence` | C10.6 Connector/Evidence implementation, metadata, provisioning, test, and sync contract. |

The requested logical order was C10.6 → U04 → ACL03 → Documentation → Release
cleanup. The committed order is C10.6 → ACL03 → U04 → release metadata →
Documentation. There is **no Release cleanup commit** in the recent history.
Therefore the requested commit sequence is incomplete and not in the requested
order.

## 2. Committed-path contamination check

| Commit | C11 paths | `tests` / `scripts/testing` / runtime-harness paths | Result |
| --- | ---: | ---: | --- |
| `01fa599` Documentation | 0 | 0 | Clean documentation boundary. |
| `b0e1988` version alignment | 0 | 0 | No C11 or test/harness contamination. |
| `c70db67` U04 | 0 | 0 | No C11 or test/harness contamination. |
| `7a2f02d` ACL03 | 0 | 1 ACL03-specific test | Expected test within ACL03 boundary. |
| `e8d1899` C10.6 | 0 | 1 C10.6-specific test | Expected test within C10.6 boundary. |

The complete `git show --name-status` scan across the ten most recent commits
found **zero C11 path matches**. No `scripts/testing` or runtime-harness files
are present in the five relevant committed boundaries.

## 3. Current worktree classification

### Staged

- Expected-but-uncommitted release cleanup material: archive retention rules,
  historical package relocations, `SHA256SUMS.txt`, and
  `deployment/v1.9.5-alpha.zip` with its checksum sidecar.
- Unexpected freeze-boundary material:
  - `crm-extension/tests/test_extension_skeleton.py`
  - `scripts/testing/regression-gate-map.json`
  - `scripts/testing/run-freeze-gate.ps1`
  - `scripts/testing/run-regression-gate.ps1`
  - `scripts/testing/run-runtime-tests.ps1`
  - `scripts/testing/run-tests.ps1`
  - `tests/regression/test_extension_package_baseline.py`
  - `tests/runtime/__init__.py`
  - `tests/runtime/runtime_cli.py`
  - `tests/runtime/runtime_harness.py`
  - `tests/runtime/test_runtime_harness.py`

### Unstaged

None reported by porcelain status.

### Untracked

- `docs/PHASE_G03_4_RELEASE_CANDIDATE_BUILD_REPORT.md`
- `docs/PHASE_G04_C11_READINESS_REVIEW.md` (C11; not committed)
- This requested integrity report.

## 4. Findings

1. **Release cleanup is not committed.** Its intended files are staged, so the
   freeze boundary is incomplete.
2. **Test and harness files are co-staged with release-cleanup material.** They
   have not entered a commit, but the index is not cleanly separated.
3. **C11 exclusion from commits passes.** The C11 readiness report remains
   untracked; it did not enter any scanned commit.
4. **U04 is report-only in its dedicated commit.** The actual U04 metadata work
   is not represented in `c70db67`; it appears to have been committed earlier
   with the broader C06 UI surface.
5. **Commit order differs from the requested sequence.** ACL03 precedes U04,
   and a separate version-alignment commit intervenes before Documentation.

## Conclusion

**NEEDS FIX.** No C11 file has polluted the committed history inspected, but
the approved release-cleanup boundary is absent and the staged index contains
unrelated tests, `scripts/testing`, and runtime-harness files alongside the
pending release artifacts.
