# Phase3S02.4 — Extension Directory Cleanup Audit Report

**Date:** 2026-07-21
**Phase:** S02.4 Extension Directory Cleanup Audit
**Scope:** Read-only structural audit — **no files deleted or moved**
**Verdict:** **AUDIT COMPLETE** — 8 findings, 0 deletions executed

---

## 1. Audit Method

Scanned the complete `crm-extension/` directory tree (300+ files across 50+ directories). Each directory and file was classified into one of four categories:

| Category | Meaning |
|----------|---------|
| **KEEP** | Currently required; no action needed |
| **MOVE CANDIDATE** | Could be reorganized in a future phase |
| **DEPRECATION CANDIDATE** | Likely obsolete; needs confirmation before removal |
| **DELETE CANDIDATE** | Confirmed safe to remove after verification |

---

## 2. Complete Directory Inventory

### 2.1 Top-Level Structure

```
crm-extension/
├── manifest.json          # Extension manifest (v1.9.6-alpha)
├── README.md              # Extension documentation
├── files/                 # CANONICAL — packaged for installation (233 files)
├── Resources/             # Design-surface mirror (47 files)
├── custom/                # Legacy placeholder directory (4 README stubs)
├── tests/                 # Python test suite (7 test modules)
├── scripts/               # Build scripts (Python + PowerShell)
├── application/           # Reserved namespace boundary (1 README)
└── docs/                  # Unpopulated (only .gitkeep)
```

### 2.2 `files/` — Canonical Package Root

**Classification: KEEP**

This is the authoritative installable source. The build script (`build_release_package.py`) packages `manifest.json` + `files/` into the release ZIP. Contains:

| Subpath | Files | Description |
|---------|-------|-------------|
| `custom/Espo/Modules/Prospecting/` | ~80 files | PHP entities, controllers, services, API endpoints, primary filters |
| `custom/Espo/Custom/Hooks/` | 6 PHP files | Workflow hooks (Lead, EmailEvent, SalesFeedback, DraftApproval, SendExecution, ReplyEvent) |
| `client/custom/src/` | 8 JS files | Client-side views, handlers, controllers |
| `client/custom/res/templates/` | 3 TPL files | Handlebars templates |
| `.../Resources/` | ~127 files | Module metadata (entityDefs, layouts, scopes, clientDefs, ACL, dashlets, i18n, routes, selectDefs) |

One issue found within `files/`:

#### Finding F1: Empty directory inside package root

| Path | Type | Risk |
|------|------|------|
| `files/custom/Espo/Custom/Resources/metadata/scopes/` | Empty directory | **LOW** |

**Classification: DELETE CANDIDATE**

This empty directory sits alongside the 12 active scope JSON files at `Modules/Prospecting/Resources/metadata/scopes/`. It serves no purpose and would be included as an empty folder in the release ZIP. The build script `source_entries()` iterates `FILES_ROOT.rglob("*")` and skips directories, so it currently does NOT end up in the ZIP — but its presence is misleading.

**Recommendation:** Remove in a future cleanup phase. Verify no test asserts its existence first.

---

### 2.3 `Resources/` — Design-Surface Mirror

**Classification: DEPRECATION CANDIDATE**

Contains 47 files. Of these, **45 are byte-identical duplicates** of files in `files/custom/Espo/Modules/Prospecting/Resources/`. Only 2 files are unique (README.md files).

The mirror is a strict subset — `files/.../Resources/` has 127 files vs Resources/' 47. Missing from the mirror:

| Category | Count in files/ | Count in Resources/ |
|----------|----------------|---------------------|
| entityDefs | 12 | 12 (complete) |
| layouts | 27 | 24 (missing 3 `listDashletExpanded.json`) |
| aclDefs | 10 | 7 (missing 3) |
| clientDefs | 13 | 0 |
| scopes | 12 | 0 |
| dashlets | 12 | 0 |
| selectDefs | 5 | 0 |
| i18n (en_US + zh_CN) | 30 | 0 |
| routes.json | 1 | 1 |
| formula/Lead.json | 1 | 1 |
| **Total** | **127** | **47** |

Layout comparison (`diff -rq`) revealed 3 layout files differ between the two locations, suggesting the mirror has fallen out of sync with the authoritative source.

**Risks of keeping as-is:**
1. **Edit divergence:** A developer editing an entityDef in `Resources/` instead of `files/.../Resources/` would lose their changes on install — the `files/` version is what gets packaged.
2. **False confidence:** The test `test_surface_and_module_entity_defs_match` only checks entityDefs parity, not layouts, ACLs, or clientDefs. The mirror could silently diverge.
3. **Maintenance burden:** Every entity change requires editing two locations. This is currently done manually.

**Recommendation:** Either:
- (A) Remove `Resources/` entirely and update extension skeleton tests to validate against `files/.../Resources/` directly, OR
- (B) Add a `--sync-resources` flag to the build script that copies `files/.../Resources/` → `Resources/` as a pre-build step, making the mirror a generated artifact.

---

### 2.4 `custom/` — Legacy Placeholder Directory

**Classification: DEPRECATION CANDIDATE**

Contains 4 README.md files and 2 empty directories:

```
custom/Espo/Modules/Prospecting/
├── README.md          # "Prospecting namespace reservation — Phase 3A-2.1"
├── Api/README.md      # "Phase 3A-2.2 — No API route definitions implemented"
├── Controllers/README.md  # "Phase 3A-2.1 — No controller PHP is implemented"
└── Services/README.md     # "Phase 3A-2.1 — No service PHP is implemented"

custom/Espo/Custom/Hooks/Lead/   # EMPTY DIRECTORY
```

**Key observations:**
- All READMEs reference Phase 3A-2.1/2.2 — these are from the **initial extension skeleton era** (January 2026)
- Every README claims "no PHP implemented" — which was true at the time but is now false (the `files/` tree has 60+ PHP files)
- The `custom/Espo/Custom/Hooks/Lead/` directory is **completely empty** — not even a .gitkeep

**Why this exists:** During early Phase 3A development, a `custom/` directory may have been the intended package root. The project later migrated to `files/` as the canonical root, but the legacy structure was preserved.

**Risks:**
1. **Developer confusion:** A new contributor looking in `custom/` for PHP code will find only READMEs saying "not implemented."
2. **Git tracking:** These 4 READMEs are tracked in git (confirmed via `git ls-files`).

**Recommendation:**
- The 4 README.md files can be removed (they are tracked in git, so deletion is a tracked change)
- The empty `custom/Espo/Custom/Hooks/Lead/` directory will disappear when its last file is removed (git doesn't track empty directories)
- Before deletion, verify no extension test asserts the existence of `custom/` directories

#### Finding F2: Empty directory at `custom/Espo/Custom/Hooks/Lead/`

**Classification: DELETE CANDIDATE**
**Risk: LOW**

Completely empty. The active `LeadWorkflowHook.php` lives at `files/custom/Espo/Custom/Hooks/Lead/LeadWorkflowHook.php`.

---

### 2.5 `application/` — Reserved Namespace

**Classification: KEEP**

Contains a single `README.md`:

> "Reserved for future non-module application files. Intentionally outside EspoCRM's installable `files/` tree."

This is a deliberate namespace reservation. EspoCRM's extension system allows `application/` files for non-module customizations. The README correctly communicates intent.

---

### 2.6 `docs/` — Unpopulated Extension Docs

**Classification: DELETE CANDIDATE (or populate)**

Contains only `.gitkeep` (0 bytes). The extension README references `docs/deployment/INSTALL.md`, `docs/release/README.md`, etc. — none of which exist here (they live in the repo-level `docs/` directory).

**Recommendation:** Remove and update the extension README to point to the repo-level `docs/` directory.

---

### 2.7 `tests/` — Extension Test Suite

**Classification: KEEP**

Contains 7 active Python test modules plus `README.md` and `__init__.py`. The `__pycache__/` directory is correctly gitignored (not tracked).

---

### 2.8 `scripts/` — Build Scripts

**Classification: KEEP**

| File | Purpose |
|------|---------|
| `build_release_package.py` | Python builder (canonical) |
| `build_release_package.ps1` | PowerShell builder (Windows compat) |
| `README.md` | Documents intended install hooks (not yet implemented) |

---

## 3. Findings Summary

| ID | Finding | Location | Classification | Risk | Actionable in S02? |
|----|---------|----------|---------------|------|---------------------|
| F1 | Empty directory inside package root | `files/.../Resources/metadata/scopes/` | DELETE CANDIDATE | LOW | Yes |
| F2 | Empty legacy hooks directory | `custom/Espo/Custom/Hooks/Lead/` | DELETE CANDIDATE | LOW | Yes |
| F3 | Legacy `custom/` with stale READMEs | `custom/Espo/Modules/Prospecting/` | DEPRECATION CANDIDATE | MEDIUM | Yes (after verification) |
| F4 | Resources/ is a stale subset mirror | `Resources/` (45/47 files duplicated) | DEPRECATION CANDIDATE | MEDIUM | Design decision needed |
| F5 | Resources/ layouts out of sync | 3 layout files differ between Resources/ and files/ | DEPRECATION CANDIDATE | MEDIUM | Part of F4 |
| F6 | Empty extension docs directory | `docs/` (only .gitkeep) | DELETE CANDIDATE | LOW | Yes |
| F7 | `application/` namespace reservation | `application/README.md` | KEEP | NONE | N/A |
| F8 | Python cache in test/script dirs | `__pycache__/` | No action needed | NONE | Already gitignored |

---

## 4. Risk Assessment

| Risk | Severity | Description |
|------|----------|-------------|
| Resources/ edit divergence | **MEDIUM** | Developer could edit wrong copy of entityDef/layout; change would be lost on install |
| custom/ developer confusion | **MEDIUM** | Stale READMEs claim "not implemented" for features that exist in `files/` |
| Empty directories in source tree | **LOW** | No functional impact; misleading during navigation |
| .gitkeep-only docs/ dir | **LOW** | No functional impact; broken README links |

---

## 5. Recommended Actions (Future Phases)

### Phase S02.4 (this phase — audit only)
- [x] Complete structural audit
- [x] Classify all directories
- [x] Report findings
- [ ] **NO DELETIONS** — per phase scope

### Phase S02.4-exec (future cleanup phase)
1. Remove empty directories (F1, F2) — verify no test assertions reference them
2. Remove legacy `custom/` tree (F3) — verify `test_extension_skeleton.py` doesn't assert its existence
3. Remove or populate `docs/` (F6) — update extension README links
4. Design decision on `Resources/` (F4/F5) — either remove or auto-generate

### Phase S03+ (larger refactoring)
5. Consider code generation for repetitive PHP shells (entity/controller boilerplate)
6. Consider base-class extraction for 31 primary filter classes
7. Evaluate `application/` usage when C16 introduces new capabilities

---

## 6. Verification

| Check | Result |
|-------|--------|
| No files deleted | ✅ Confirmed |
| No files moved | ✅ Confirmed |
| No PHP modified | ✅ Confirmed |
| No metadata modified | ✅ Confirmed |
| No namespace changes | ✅ Confirmed |
| No connector changes | ✅ Confirmed |
| Git status clean (no business code changes) | ✅ Confirmed |

---

## 7. Verdict

**AUDIT COMPLETE** — The extension directory structure is clean and well-organized for its primary purpose (the `files/` package root). Two legacy artifacts (`custom/`, `Resources/`) represent technical debt from the Phase 3A skeleton era that should be resolved before C16 adds new entity complexity. Resolution is deferred to a future cleanup phase; no files were deleted or moved in this audit.
