# Phase RC01 — Release Candidate Package Report

**Date:** 2026-07-14  
**Result:** **PASS**  
**Scope:** package build and read-only package validation. No business code, connector, Evidence logic, metadata, tests, or version source files were modified.

## Release candidate

| Item | Value |
|---|---|
| Workspace manifest version | `1.9.5-alpha` |
| Package | `deployment/v1.9.5-alpha.zip` |
| SHA-256 sidecar | `deployment/v1.9.5-alpha.zip.sha256` |
| Package size | 119,212 bytes |
| SHA-256 | `4B77F90F01958D3F99A197841DE1264D2E0D80EA5A8AB585CBEE273AF7C593AF` |

The candidate was built with the repository release builder:

```powershell
crm-extension/scripts/build_release_package.ps1 -OutputPath deployment/v1.9.5-alpha.zip
```

The local PowerShell execution policy required a one-time `ExecutionPolicy Bypass` invocation of the existing script. The script itself was not changed.

## Package boundary

The builder includes exactly:

- `manifest.json`
- every current file under `crm-extension/files/`

It excludes repository docs, tests, scripts, connector source, `Resources/` design copies, temporary files, and historical deployment artifacts.

| Validation | Result |
|---|---|
| Manifest version is `1.9.5-alpha` | PASS |
| Package manifest equals workspace manifest version | PASS |
| SHA-256 recalculation equals sidecar | PASS |
| ZIP entries | 197 |
| Expected release entries (manifest + 196 files) | 197 |
| Entries outside `manifest.json` / `files/` | 0 |
| Duplicate ZIP entries | 0 |
| Workspace release files missing from ZIP | 0 |
| Extra ZIP entries | 0 |
| Per-file SHA-256 differences between ZIP and current release tree | 0 |

## Conclusion

`v1.9.5-alpha.zip` is a complete, hash-attested freeze candidate for the current `crm-extension` release tree. The existing historical `prospecting-extension-1.9.5-alpha.zip` artifact was not altered or used as the candidate.

No commit, deployment, installation, runtime rebuild, or cache-clear operation was performed by Phase RC01.
