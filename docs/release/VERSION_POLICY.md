# Version Policy

**Status:** Static Verified from current manifest practice

## Extension Versioning

- **Format:** `MAJOR.MINOR.PATCH[-prerelease]`
- **Current packaged release:** `1.9.5-alpha`
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
