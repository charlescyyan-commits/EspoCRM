# Phase3C19 Release Notes (Freeze Index)

**Status:** Freeze documentation  
**Date:** 2026-07-27  
**Release:** `v1.9.12-alpha`  
**Release sync commit:** `8ae8eb1`

---

## Canonical product notes

Do not maintain a second full release-notes body here.

**Authoritative file:** [`docs/release/RELEASE_NOTES_1.9.12-alpha.md`](release/RELEASE_NOTES_1.9.12-alpha.md)

That document describes shipped WP0–WP3 state, Search Center acquisition pipeline, Outreach Workspace v1, preserved boundaries, and install guidance.

---

## Freeze artifact pin

| Field | Value |
|---|---|
| Version | `1.9.12-alpha` |
| Commit | `8ae8eb1` (`phase3c19: sync 1.9.12-alpha release after Search Center workspace`) |
| Package | `deployment/prospecting-extension-1.9.12-alpha.zip` |
| Sidecar | `deployment/prospecting-extension-1.9.12-alpha.zip.sha256` |
| SHA-256 | `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218` |
| ZIP entries | `315` |
| Integrity | `python crm-extension/scripts/build_release_package.py --check` → **PASS** |
| Tests at freeze | **384** extension tests **PASS** |

---

## Freeze delta after mainline closure (`2d07b5c`)

Mainline WP0–WP3 / dashboard closure narrative remains in:

- `docs/phase-reports/PHASE3C19_MAINLINE_FREEZE_CLOSURE_REPORT.md`

Post-`2d07b5c` product surfaces packaged at `8ae8eb1`:

1. **Search Center** — acquisition pipeline cards (Search Jobs, Prospect Pool, Research Queue); Search Strategy removed from large cards.  
2. **Outreach Workspace v1** — DraftApproval index/workspace routing with queue count cards.  
3. **Release artifact rebuild** — ZIP/SHA aligned to the above sources.

---

## Operator summary

Install the ZIP on a disposable CRM only. Verify the SHA-256 sidecar before install. Complete EspoCRM clear-cache / rebuild after install.

Freeze readiness and known limitations: `docs/PHASE3C19_FINALIZATION_REPORT.md`, `docs/PHASE3C19_FREEZE_CHECKLIST.md`.
