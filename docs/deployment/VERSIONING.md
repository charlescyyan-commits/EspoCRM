# Versioning

**Status:** Static Verified from `manifest.json` and release reports

## Extension Version

| Field | Current value | Location |
|-------|---------------|----------|
| `version` | `1.9.8-alpha` | `crm-extension/manifest.json` |
| `releaseDate` | `2026-07-23` | `crm-extension/manifest.json` |
| `acceptableVersions` | `>=7.4.0` | EspoCRM platform |
| `php` | `>=8.1` | PHP runtime |

## Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Extension ZIP | `prospecting-extension-<semver>.zip` | `prospecting-extension-1.9.8-alpha.zip` |
| Checksum sidecar | `<zip>.sha256` | `prospecting-extension-<version>.zip.sha256` |
| Phase report | `PHASE<phase>_<name>_REPORT.md` | `PHASE3C02_2C_JOB_RUNNER_REPORT.md` |

## Pre-release Suffix Semantics

| Suffix | Meaning in this repo |
|--------|---------------------|
| `-alpha` | Metadata and connector features under active development; disposable CRM testing |
| `-beta` | Not currently used in manifest |
| `-rc` | Not currently used |
| (none) | Stable — not yet declared for this extension |

## Version Sync Rules

These must match at release time:

1. `crm-extension/manifest.json` → `version`
2. ZIP filename under `deployment/`
3. `test_extension_skeleton.py` expected version assertion
4. Release notes document (when published)

For the current package, the ZIP and manifest are aligned at `1.9.8-alpha` with committed sidecar `deployment/prospecting-extension-1.9.8-alpha.zip.sha256`. Build and verify from the repository root with `python crm-extension/scripts/build_release_package.py` and `python crm-extension/scripts/build_release_package.py --check` (use `py` in place of `python` on Windows when applicable).

## Connector Versioning

`chitu-connector` has no separate semver in manifest. It tracks the git commit used with a given extension release. Job runner phase references commits in [PHASE3C02_2C_JOB_RUNNER_REPORT.md](../PHASE3C02_2C_JOB_RUNNER_REPORT.md).

## Sync Contract Version

CRM sync requires `contract_version: "1.0"` in JSON payloads (`ChituSyncService`). Contract schema: `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json`.

## Related Documents

- [../release/VERSION_POLICY.md](../release/VERSION_POLICY.md)
- [PACKAGE.md](PACKAGE.md)
