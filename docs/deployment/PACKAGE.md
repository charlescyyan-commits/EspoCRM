# Package Build

**Status:** Static Verified

## Extension ZIP Layout

Installable archive contains **only**:

```text
manifest.json
files/
  custom/Espo/Modules/Prospecting/...
  client/custom/src/...
```

**Not included:** `Resources/`, `tests/`, `custom/` placeholders, `scripts/`, `docs/`.

## Build Script

**Path:** `crm-extension/scripts/build_release_package.ps1`

```powershell
param([string]$OutputPath)  # Mandatory
```

Behavior:

1. Resolves output path; creates parent directory if missing.
2. Removes existing output file.
3. Adds `manifest.json` and all files under `files/` recursively.
4. Uses forward-slash ZIP entry names (required for EspoCRM on Linux).

Example:

```powershell
cd D:\EspoCRM-Production\crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension-1.9.6-alpha.zip
```

## Checksum

Release packages should record SHA-256 hashes in sidecar files:

```text
deployment/prospecting-extension-<version>.zip.sha256
```

Generate manually (PowerShell):

```powershell
Get-FileHash ..\deployment\prospecting-extension-1.9.6-alpha.zip -Algorithm SHA256
```

## Validation

```powershell
cd D:\EspoCRM-Production
python -m unittest crm-extension.tests.test_extension_skeleton.ExtensionSkeletonTests.test_manifest_json_valid -v
```

`test_extension_skeleton.py` also asserts directory structure, route parity, and entity metadata.

## Known Artifacts in `deployment/`

| File | Version (from naming) |
|------|----------------------|
| `prospecting-extension-1.8.0-alpha.zip` | Historical package |
| `prospecting-extension-1.9.0-alpha.zip` | Historical package |
| `prospecting-extension-1.9.1-alpha.zip` | Historical package |
| `prospecting-extension-1.9.6-alpha.zip` | Current package; matches `manifest.json` |

The current `1.9.6-alpha` ZIP has a committed `.sha256` sidecar at `deployment/prospecting-extension-1.9.6-alpha.zip.sha256`.

## Related Documents

- [INSTALL.md](INSTALL.md)
- [VERSIONING.md](VERSIONING.md)
- [../PHASE3B03_RELEASE_ARTIFACT.md](../PHASE3B03_RELEASE_ARTIFACT.md)
