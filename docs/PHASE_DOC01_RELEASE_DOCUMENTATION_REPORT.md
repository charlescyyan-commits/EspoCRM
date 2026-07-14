# Phase DOC01 - Release Documentation Cleanup Report

**Date:** 2026-07-14
**Scope:** Documentation only - `docs/`, root `README.md`, and `crm-extension/README.md`.
**Excluded:** PHP, Python, connector, metadata, package artifacts, and tests were not modified.

## Result

**COMPLETE - current operational documentation now uses `1.9.5-alpha` as the packaged release baseline.**

`crm-extension/manifest.json` is the version authority and declares `1.9.5-alpha`. The corresponding packaged ZIP is `deployment/prospecting-extension-1.9.5-alpha.zip`. The local runtime audit also established that the installed archive matches this package hash; DOC01 did not install, rebuild, or otherwise modify the runtime.

## 1. Version consistency

| Area | Before | After | Result |
| --- | --- | --- | --- |
| Version authority | Mixed prose references to `1.9.0-alpha` | `crm-extension/manifest.json` treated as the authority (`1.9.5-alpha`) | PASS |
| Operational deployment docs | Build/install/upgrade examples used `1.9.0-alpha` | Examples and current-value tables use `1.9.5-alpha` | PASS |
| README files | Root workspace README lacked a release baseline; extension README described an obsolete `1.1.0-alpha` skeleton | Both describe the current `1.9.5-alpha` package and current module layout | PASS |
| CI/testing documentation | Current-state and manual-test prose named `1.9.0-alpha` | Current package references use `1.9.5-alpha` | PASS |
| Historical reports | Old versions appear in historical phase/audit reports | Preserved as historical evidence | PASS |

`1.8.0-alpha`, `1.9.0-alpha`, and `1.9.1-alpha` are now represented as historical package releases, not as the current version. `1.9.5-alpha` is the only current packaged-release value in operational documentation.

## 2. Release notes

Created a release-notes index and package-specific notes:

| Version | Release notes |
| --- | --- |
| `1.8.0-alpha` | [RELEASE_NOTES_1.8.0-alpha.md](release/RELEASE_NOTES_1.8.0-alpha.md) |
| `1.9.0-alpha` | [RELEASE_NOTES_1.9.0-alpha.md](release/RELEASE_NOTES_1.9.0-alpha.md) |
| `1.9.1-alpha` | [RELEASE_NOTES_1.9.1-alpha.md](release/RELEASE_NOTES_1.9.1-alpha.md) |
| `1.9.5-alpha` | [RELEASE_NOTES_1.9.5-alpha.md](release/RELEASE_NOTES_1.9.5-alpha.md) |

Each note contains a feature summary, breaking-change assessment, migration notes, and an explicit verification boundary. The content was reconstructed from adjacent ZIP package deltas, rather than inferred from currently developing work.

## 3. README and architecture consistency

- Rewrote the root README with the version authority, current package baseline, workspace boundaries, and release-documentation links.
- Rewrote `crm-extension/README.md` to describe the actual installable layout: `files/`, Prospecting module server resources, native client resources, `Resources/` mirror, tests, and package build script.
- Updated the documentation center, architecture/module references, deployment guides, local setup, version policy, and installation guidance to use the current baseline.
- C10.6 is explicitly labelled as **in development** and is not claimed as part of `1.9.5-alpha`.

## 4. Documentation navigation

- Added [release/README.md](release/README.md) as the release-notes index.
- Updated [docs/README.md](README.md) to point to the release index and current release note.
- Added a **Current Phase Navigation** table in [reports/README.md](reports/README.md), covering C03-C10, U01-U04, and DOC01.

## 5. Remaining release-hygiene finding

The `1.9.5-alpha` ZIP has no committed `.sha256` sidecar. DOC01 documents this accurately in deployment guidance but does not generate or add an artifact, because this phase is documentation-only. Create and retain the sidecar under a separately approved release/package task.

## Validation

- Compared `crm-extension/manifest.json` with the `1.9.5-alpha` package manifest.
- Compared adjacent ZIP package entries to derive release-note deltas.
- Performed a documentation-version sweep and relative-link validation for the documentation, release, and reports indexes.
- Ran `git diff --check` on DOC01 documentation changes.

## Files changed

- `README.md`
- `crm-extension/README.md`
- `docs/README.md`
- `docs/architecture/SYSTEM_OVERVIEW.md`
- `docs/architecture/MODULES.md`
- `docs/ci/CI_ROADMAP.md`
- `docs/ci/CURRENT_STATE.md`
- `docs/ci/RELEASE_AUTOMATION_DESIGN.md`
- `docs/deployment/INSTALL.md`
- `docs/deployment/PACKAGE.md`
- `docs/deployment/UPGRADE.md`
- `docs/deployment/VERSIONING.md`
- `docs/developer/LOCAL_SETUP.md`
- `docs/developer/PROJECT_STRUCTURE.md`
- `docs/release/CHANGELOG_POLICY.md`
- `docs/release/README.md`
- `docs/release/RELEASE_NOTES_1.8.0-alpha.md`
- `docs/release/RELEASE_NOTES_1.9.0-alpha.md`
- `docs/release/RELEASE_NOTES_1.9.1-alpha.md`
- `docs/release/RELEASE_NOTES_1.9.5-alpha.md`
- `docs/release/RELEASE_PROCESS.md`
- `docs/release/VERSION_POLICY.md`
- `docs/reports/README.md`
- `docs/testing/MANUAL_TESTS.md`
- `docs/testing/TEST_INVENTORY.md`
- `docs/testing/TEST_RELIABILITY_RISKS.md`
- `docs/user-guide/INSTALL_EXTENSION.md`

No runtime, code, metadata, connector, package, or test file was changed.
