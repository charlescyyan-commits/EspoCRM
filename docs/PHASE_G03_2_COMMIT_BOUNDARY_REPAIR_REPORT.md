# Phase G03.2 — Commit Boundary Repair Report

**Date:** 2026-07-14  
**Scope:** Git staging and commit-boundary repair without business-logic changes,
history amendment, reset, or file deletion.

## Actions completed

1. Cleared the entire Git index with `git restore --staged :/`. All working
   files were preserved.
2. Rechecked the worktree: the former test, `scripts/testing`, and runtime
   harness entries are now unstaged/untracked rather than staged.
3. Revalidated the existing C10.6 (`e8d1899`) and ACL03 (`7a2f02d`) commits:
   neither contains a C11 path.
4. Ran the U04-adjacent static UI suites:
   `test_phase3c06_prospecting_ui_foundation` and
   `test_phase3u03_dashboard_productization` — **12/12 PASS**.

## U04 boundary finding

U04 UI metadata (layouts, client definitions, dashlets, i18n, and the U04
navbar provisioning script) is already recorded in `f7acc1b` (`phase-c06: add
prospecting UI and dashboard surface`). The standalone `c70db67` U04 commit
contains reports only.

Creating a genuinely independent metadata commit would require rewriting or
reversing existing committed history, which is outside this phase because
amend, reset, and file deletion are prohibited. No empty or duplicate U04
commit is created. This is a historical boundary limitation, not a staged
pollution issue.

## Commit boundaries prepared

| Boundary | Allowed paths | Exclusions |
| --- | --- | --- |
| Documentation | `docs/` and README files only | C11 documentation, source, tests, scripts, packages |
| Release cleanup | `deployment/`, `archive/`, and `.gitignore` only if required | docs, source, tests, `scripts/testing`, runtime harness, C11 |

The C11 readiness document remains untracked and is explicitly excluded from
both prepared boundaries.

## Expected post-repair status

After the allowed Documentation and Release cleanup commits, Git status should
contain no staged test, `scripts/testing`, runtime-harness, or C11 file. Any
remaining C11 documentation remains untracked and intentionally excluded.

## Constraint note

The U04 historical commit split cannot be repaired further without authority to
rewrite already-created commits. All other stage pollution can be repaired by
path-scoped commits in this phase.
