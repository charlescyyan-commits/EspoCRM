# Release Automation Design

**Status:** Phase CI01 Design — 2026-07-13

> Defines the target state for automated release. No actual automation is implemented in this phase.

---

## 1. Version Source of Truth

| Attribute | Current | Target |
|-----------|---------|--------|
| **Authority** | `crm-extension/manifest.json` `version` field | Same — manifest remains the single source of truth |
| **Format** | `MAJOR.MINOR.PATCH-prerelease` (e.g., `1.9.5-alpha`) | Same |
| **Validation** | Manual (human checks manifest) | Automated: CI validates manifest version matches ZIP filename, tag, and release notes |
| **Version bump** | Manual edit of `manifest.json` | Manual edit + CI validates consistency |

**Rule:** The manifest is always the authority. No env var, CI variable, or git tag overrides it.

---

## 2. Manifest Validation (Pre-Build Gate)

Before building, CI must verify:

- `manifest.json` is valid JSON
- `version` field matches semver pattern (`\d+\.\d+\.\d+(-alpha|-beta|-rc)?`)
- `releaseDate` is today's date or a recent date
- `acceptableVersions` array is non-empty
- `php` array is non-empty
- `name`, `extensionName`, `author`, `description` are non-empty strings
- `skipBackup` is boolean
- `checkVersionConflict` is boolean

**Script:** A small Python validator using `json.load()` + field assertions (can be added to `ci-package.yml`).

---

## 3. ZIP Build & Naming

| Attribute | Rule |
|-----------|------|
| **Output path** | `deployment/prospecting-extension-<version>.zip` |
| **Version in filename** | Must exactly match `manifest.json` `version` |
| **Builder** | `crm-extension/scripts/build_release_package.ps1` |
| **ZIP contents** | `manifest.json` at root + `files/` directory (forward-slash entries only) |
| **Excluded** | `Resources/`, `tests/`, `custom/` placeholders, `scripts/`, `docs/` |

**Post-build validation:**
1. Open ZIP, list all entries
2. Assert `manifest.json` is the first or root entry
3. Assert all paths use `/` (not `\`)
4. Assert no `Resources/` directory in archive
5. Assert no `tests/` directory in archive
6. Assert `files/custom/Espo/Modules/Prospecting/` exists

---

## 4. SHA-256 Generation

| Attribute | Rule |
|-----------|------|
| **File** | `deployment/prospecting-extension-<version>.zip.sha256` |
| **Format** | `<hex_hash>  prospecting-extension-<version>.zip` (or raw hex) |
| **Generation** | `Get-FileHash -Algorithm SHA256` (PowerShell) or `sha256sum` (Linux) |
| **Verification** | CI validates SHA-256 of built artifact matches sidecar before publishing |

---

## 5. Artifact Retention

| Artifact | Retention | Rationale |
|----------|-----------|-----------|
| Release ZIP | **Permanent** — published to GitHub Releases | Required for install and rollback |
| SHA-256 sidecar | **Permanent** — attached to same release | Integrity verification |
| CI build artifacts (non-release) | **7 days** | Debugging failed builds |
| Test results (JUnit XML) | **90 days** | Trend analysis |
| Browser screenshots (failure) | **30 days** | Debugging UI failures |

**Historical artifacts** in `deployment/` (through `1.9.5-alpha`) should be migrated to GitHub Releases but not deleted from the repository.

---

## 6. Release Notes

| Attribute | Rule |
|-----------|------|
| **Location** | `docs/release/RELEASE_NOTES_<version>.md` |
| **Format** | Summary, upgrade instructions, verification results (per `CHANGELOG_POLICY.md`) |
| **Review** | Human-written; CI validates file exists and is non-empty |
| **Publication** | Attached to GitHub Release body |

**Automation scope:** CI cannot generate release notes from commits (commits are granular phase work, not user-facing). Release notes remain human-authored.

---

## 7. Tag Policy

| Attribute | Rule |
|-----------|------|
| **Tag format** | `v<version>` (e.g., `v1.9.5-alpha`) |
| **Tag creator** | Human (via `git tag`) or CI (on release workflow dispatch) |
| **Tag trigger** | Pushing a `v*` tag triggers `release.yml` |
| **Lightweight vs annotated** | Annotated tags preferred (include releaser + date) |
| **Tag protection** | Recommended: only maintainers can push `v*` tags |

**Current state:** No standardized tag convention. Occasional tags match extension version.

---

## 8. Manual Approval Gate

| Step | Manual or Automated |
|------|---------------------|
| Version bump | Manual (edit `manifest.json`) |
| Release notes | Manual (write `release/RELEASE_NOTES_<version>.md`) |
| All CI gates passing | Automated (Layers 1-9) |
| Runtime verification on disposable CRM | Automated (Layer 8) |
| Browser acceptance | Automated (Layer 9) |
| **Final release approval** | **Manual** — human reviews all gates + release notes before pushing tag |
| Tag creation | Manual (or one-click workflow dispatch) |
| Artifact publication | Automated (on tag push) |

**The human gate is between CI passing and tag creation.** Once the tag is pushed, artifact publication is automatic.

---

## 9. Rollback Material

Every release must preserve:

| Material | Location | Purpose |
|----------|----------|---------|
| Previous release ZIP | GitHub Releases | Direct rollback install |
| Previous SHA-256 | GitHub Releases | Integrity check on rollback |
| Previous manifest version | Git history (`git show <tag>:crm-extension/manifest.json`) | Reference |
| Database backup reference | N/A (CRM operator responsibility) | CRM state rollback |
| Rollback procedure | `docs/deployment/ROLLBACK.md` | Operator instructions |

CI does not perform rollback — it only ensures rollback materials are preserved.

---

## 10. Alpha / Beta / RC / Stable Rules

### Alpha (`-alpha`)

- All Layers 1-5 must pass
- Layers 6-7 must pass (package builds and validates)
- Layers 8-9 are optional (runtime verification deferred is acceptable)
- Release notes must list known TBD/Draft items
- Artifact published with `-alpha` suffix
- **Current state:** This is the only release type produced so far

### Beta (`-beta`)

- All Layers 1-7 must pass
- Layer 8 must pass (runtime REST tests required)
- Layer 9 is recommended but not blocking
- Release notes must list remaining known gaps
- **Current state:** Not yet used

### RC (`-rc`)

- All Layers 1-9 must pass
- Full runtime + browser acceptance required
- Zero known TBD items that affect core functionality
- Release notes must be complete
- **Current state:** Not yet used

### Stable (no suffix)

- All Layers 1-10 must pass
- Full pipeline green
- Upgrade path from previous stable tested
- Rollback tested
- Production operator sign-off
- **Current state:** Not yet declared

---

## 11. Implementation Phasing

| Phase | Scope | Depends On |
|-------|-------|------------|
| CI06 (Release Automation) | Implement `release.yml`, ZIP validator, SHA-256 automation, GitHub Release publication | CI02-CI05, T02-T06 |
| First alpha via CI | Build and publish `-alpha` artifact via GitHub Actions | CI02 + CI03 |
| First beta via CI | Build, test, publish `-beta` with runtime verification | CI02-CI04 |
| First stable via CI | Full pipeline including browser acceptance + upgrade tests | CI02-CI06 |
