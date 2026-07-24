# Version Policy

**Status:** Static Verified from current manifest practice

## Extension Versioning

- **Format:** `MAJOR.MINOR.PATCH[-prerelease]`
- **Current packaged release:** `1.9.9-alpha`
- **Authority:** `crm-extension/manifest.json`

### Prerelease Tags

| Tag | Use in this repo |
|-----|------------------|
| `alpha` | Active development; disposable CRM testing |
| `beta` | Reserved — not used yet |
| `rc` | Reserved — not used yet |
| (stable) | Future — requires explicit phase sign-off |

## Artifact Naming

```text
deployment/prospecting-extension-<version>.zip
deployment/prospecting-extension-<version>.zip.sha256
```

Version in filename must match `manifest.json`.

The artifact whose filename matches `manifest.json` is the current canonical release. Earlier frozen artifacts may remain in `deployment/` as historical evidence; each retained ZIP must have an exact matching `.sha256` sidecar. The release-integrity gate validates every retained sidecar and performs source-byte parity validation for the current canonical artifact.

Build and validate the current canonical artifact from the repository root:

```text
python crm-extension/scripts/build_release_package.py
python crm-extension/scripts/build_release_package.py --check
```

The Python builder is CWD-independent and produces deterministic ZIP entries from `manifest.json` plus `files/`. On Windows, `py` may be substituted for `python`.

## Platform Compatibility

Declared in manifest:

- EspoCRM `acceptableVersions`: `>=7.4.0`
- PHP: `>=8.1`

Bump manifest constraints only when tested against target platform.

## Contract Versioning

Sync JSON uses `contract_version: "1.0"`. Breaking contract changes require:

1. New schema file (e.g. `ESPOCRM_SYNC_CONTRACT_V2.json`)
2. CRM service acceptance logic update
3. Connector mapper update
4. New phase report

## Connector Versioning

No separate package version. Tag connector state by git commit in phase reports when releasing extension + connector together.

## Related Documents

- [../deployment/VERSIONING.md](../deployment/VERSIONING.md)
- [CHANGELOG_POLICY.md](CHANGELOG_POLICY.md)
