# Phase3C19 Freeze Checklist

**Release:** `v1.9.12-alpha`  
**Commit:** `8ae8eb1`  
**Date:** 2026-07-27

Use this list as the freeze gate. Details live in linked reports — do not copy long narratives here.

---

## Required checks

- [x] Runtime verified  
- [x] Release artifact verified  
- [x] Package check PASS (`build_release_package.py --check`)  
- [x] Extension test suite PASS (`384` tests)  
- [x] Repository regression suite reviewed:  
  - `156` passed  
  - Known stale assertions: `2` tests require C20 test maintenance  
  - Impact: No runtime impact.  
- [x] Runtime screenshots captured (`docs/evidence/phase3c19-search-center-gate/`)  
- [x] Navigation verified (C17 desired-state / contract tests; DraftApproval remains Outreach entry)  
- [x] Search Center verified (acquisition cards + Research Queue route/count)  
- [x] Outreach Workspace verified (workspace opens; native list preserved)  
- [x] i18n verified (en/zh ProspectingSearch + DraftApproval workspace key parity)  
- [x] Ready for release  

---

## Test scope clarification

The `384` test result refers specifically to:

`crm-extension/tests/`

The complete repository regression invocation currently reports two stale assertions superseded by C18 architecture changes.

These are tracked as C20 WP0 maintenance items.

---

## Artifact pin

| Item | Value |
|---|---|
| ZIP | `deployment/prospecting-extension-1.9.12-alpha.zip` |
| SHA-256 | `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218` |
| Entries | `315` |

---

## Non-blocking known issue

- [x] Recorded: ProspectPool primaryFilter chip may show **All** until hydration — deferred UX polish (`docs/PHASE3C19_FINALIZATION_REPORT.md` §6)

---

## Sign-off references

- Finalization: `docs/PHASE3C19_FINALIZATION_REPORT.md`  
- Runtime gates: `docs/PHASE3C19_RUNTIME_GATE_SUMMARY.md`  
- Release index: `docs/PHASE3C19_RELEASE_NOTES.md`  
- Product notes: `docs/release/RELEASE_NOTES_1.9.12-alpha.md`  

**Freeze checklist result: PASS — ready for release tag consideration.**
