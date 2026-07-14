# Phase G03.3 - v1.9.5-alpha Version Alignment Report

**Date:** 2026-07-14
**Target baseline:** `v1.9.5-alpha`
**Scope:** Release metadata only
**Result:** **PASS (metadata alignment); CLEAN-COMMIT GATE BLOCKED by pre-existing out-of-scope files**

## Version authority

`crm-extension/manifest.json` is the extension package version authority. Its
working-tree release metadata is aligned as follows:

| File | Old version | New version | Classification |
|---|---|---|---|
| `crm-extension/manifest.json` | `1.9.0-alpha` | `1.9.5-alpha` | Active package metadata |

No other package metadata manifest was found in this repository.

## Release metadata present for this baseline

The following current-release metadata already identifies `1.9.5-alpha` and
forms the release-documentation baseline:

- `README.md`
- `crm-extension/README.md`
- `docs/README.md`
- `docs/deployment/INSTALL.md`
- `docs/deployment/PACKAGE.md`
- `docs/deployment/UPGRADE.md`
- `docs/deployment/VERSIONING.md`
- `docs/release/README.md`
- `docs/release/RELEASE_NOTES_1.9.5-alpha.md`
- `docs/release/VERSION_POLICY.md`

The release notes name the matching package
`deployment/prospecting-extension-1.9.5-alpha.zip`.

## `1.9.0-alpha` search and exclusions

Every remaining `1.9.0-alpha` reference was reviewed and intentionally
excluded from editing because it is historical evidence, a historical package
identifier, or an immutable phase-report observation. This includes:

- `archive/deployment/historical-packages/` package checksum records;
- `docs/release/RELEASE_NOTES_1.9.0-alpha.md` and the historical release index
  entry in `docs/release/README.md`;
- `docs/deployment/PACKAGE.md`, where the value names a historical package;
- existing phase, audit, and documentation reports that record the version
  observed at the time of their respective phases.

No historical report content was modified.

## Changed files for the prepared release-metadata commit

1. `crm-extension/manifest.json` - active package version `1.9.0-alpha` to
   `1.9.5-alpha`.
2. `docs/PHASE_G03_VERSION_ALIGNMENT_REPORT.md` - this alignment record.

The current README and release-note references listed above are release
metadata already present in the working tree; this phase did not modify their
non-version content.

## Validation

| Check | Result | Evidence |
|---|---|---|
| Manifest version | PASS | `crm-extension/manifest.json` declares `1.9.5-alpha`. |
| Current release documentation | PASS | Current README, deployment, and release-note metadata consistently use `1.9.5-alpha`. |
| Package metadata search | PASS | No additional `package.json`, `composer.json`, or other package manifest was found. |
| Runtime behavior | PASS | **No runtime behavior changed.** No runtime code, tests, C10/C10.6, ACL, or architecture files were modified by this phase. |
| C11 files in release commit scope | PASS | This phase adds no C11 files. |
| Temporary/archive files in release commit scope | PASS | This phase adds no temporary or archive files. |
| Clean repository gate | BLOCKED | Pre-existing untracked `docs/PHASE_G04_C11_READINESS_REVIEW.md` and `archive/` content remain outside this phase's scope and must not be included in the release-metadata commit. |

## Commit preparation boundary

Do not commit the pre-existing C11 document, `archive/`, deployment archives,
or unrelated staged C01-C10.6/ACL work with this metadata baseline. This phase
does not create a commit or tag.
