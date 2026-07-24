# Phase3C17 Release Rebuild Report

**Date:** 2026-07-25  
**Scope:** Release package rebuild only (no feature / navigation / ACL / workflow changes)

## Results

| Field | Value |
| --- | --- |
| Commit | `5ff7cc3` feature fix; packaging `32b2027` — rebuild artifact |
| Remote | `origin/master` @ `32b2027` (`HEAD == origin/master`) |
| Version | `1.9.10-alpha` (unchanged; no version bump) |
| Artifact | `deployment/prospecting-extension-1.9.10-alpha.zip` |
| SHA-256 | `62DF8E4C576AF6C0980BC5F8B920974A69B453D1EED41A5A53471BA91A8E022B` |
| Prior SHA (superseded build) | `10ED255C3AB2BA043E13B767EF6CECF1CEF8CE88942499458F433008FBA5300D` |
| `1.9.9-alpha` | Immutable — `067A89E52EFB35DF7DA4D9437485381D93004063BFC0E81B67EF2C67995871C2` |

## Gates

| Gate | Result |
| --- | --- |
| `build_release_package.py --check` | PASS |
| Extension suite | OK — 267 passed |
| Release integrity + consumers | OK — 26 passed |

## Metadata

- Manifest version already `1.9.10-alpha` — no bump.
- Release notes updated to document packaged `ReplyEvent` / `Approval` Record controllers.
- No navigation, ACL, or workflow service edits in this rebuild.
- The reconciled artifact includes
  `Controllers/SendExecution.php`, matching the source tree at `3bff2e2`.

## Remaining risks

- New-user default Command Center assignment still requires provisioner re-run or native Dashboard Templates (no login hook).
- DraftApproval `c17Pending` primary-filter availability depends on installed metadata filters on the target CRM; verify after install if queue data still 400s.
- Rebuild did not re-run browser smoke; install + smoke on disposable CRM remains the next operational step.
