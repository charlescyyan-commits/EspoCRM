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

**Primary path:** `crm-extension/scripts/build_release_package.py`

```text
python crm-extension/scripts/build_release_package.py
python crm-extension/scripts/build_release_package.py --check
```

Behavior:

1. Resolves the repository root independently of the current directory.
2. Packages `manifest.json` and all files under `files/` with forward-slash ZIP entry names.
3. Canonicalizes only known text-source line endings to LF before packaging; binary sources remain byte-for-byte unchanged.
4. Writes a SHA-256 sidecar and verifies artifact/source byte parity with `--check`.

Example:

```text
# Run from the repository root.
python crm-extension/scripts/build_release_package.py
python crm-extension/scripts/build_release_package.py --check
```

## Checksum

Release packages should record SHA-256 hashes in sidecar files:

```text
deployment/prospecting-extension-<version>.zip.sha256
```

Generate manually (PowerShell):

```powershell
Get-FileHash deployment\prospecting-extension-1.9.7-alpha.zip -Algorithm SHA256
```

## Validation

```text
python -m unittest discover -s crm-extension/tests
```

`test_extension_skeleton.py` also asserts directory structure, route parity, and entity metadata.

## Known Artifacts in `deployment/`

| File | Version (from naming) |
|------|----------------------|
| `prospecting-extension-1.8.0-alpha.zip` | Historical package |
| `prospecting-extension-1.9.0-alpha.zip` | Historical package |
| `prospecting-extension-1.9.1-alpha.zip` | Historical package |
| `prospecting-extension-1.9.7-alpha.zip` | Current package; matches `manifest.json` |

The current `1.9.7-alpha` ZIP has a committed `.sha256` sidecar at `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`.

## Related Documents

- [INSTALL.md](INSTALL.md)
- [VERSIONING.md](VERSIONING.md)
- [../PHASE3B03_RELEASE_ARTIFACT.md](../PHASE3B03_RELEASE_ARTIFACT.md)
