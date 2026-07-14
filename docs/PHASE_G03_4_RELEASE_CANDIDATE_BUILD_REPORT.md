# Phase G03.4 - Release Candidate Build Report

**Date:** 2026-07-14
**Result:** **PASS**

## Source baseline

| Item | Value |
|---|---|
| Source commit | `b0e198851bc698ab01ef2abc0a63673f945b4a3c` |
| Manifest version | `1.9.5-alpha` |
| Build input | Git snapshot of `crm-extension/manifest.json` and `crm-extension/files/` from the source commit |

The source snapshot was used intentionally so existing working-tree changes and
the later documentation-only HEAD commit could not enter the candidate.

## Release candidate artifact

| Item | Value |
|---|---|
| Artifact | `deployment/v1.9.5-alpha.zip` |
| SHA256 sidecar | `deployment/v1.9.5-alpha.zip.sha256` |
| Size | `120203` bytes |
| SHA256 | `09E2E4E3543E3583A74672B69E4CEC2059EE39186784DD31456BDC59E6B4D1B2` |

The sidecar contains:

```text
09E2E4E3543E3583A74672B69E4CEC2059EE39186784DD31456BDC59E6B4D1B2  v1.9.5-alpha.zip
```

## ZIP content validation

The package content list was read from the built ZIP and compared exactly with
the selected source-commit file list.

| ZIP root / source selection | Entries |
|---|---:|
| `manifest.json` | 1 |
| `files/**` | 196 |
| Total | 197 |

Validation result: 197 entries found, 0 missing entries, 0 unexpected entries,
and the packaged `manifest.json` declares `1.9.5-alpha`.

## Explicit exclusions

The builder selects only `manifest.json` and regular files below `files/` from
the source snapshot. The ZIP therefore excludes:

- `.git/`
- `archive/`
- `temp/` and `tmp/`
- local runtime data
- `.env`, secret, and credential paths
- `logs/` and `*.log`
- repository documentation, tests, build scripts, and uncommitted working-tree files

The built ZIP content list contains zero paths matching the excluded categories.

## SHA256 verification

SHA256 was recalculated from `deployment/v1.9.5-alpha.zip` after the artifact
was written. The recalculated value matches the sidecar exactly.

| Check | Result |
|---|---|
| Source manifest version | PASS |
| ZIP entry list versus source snapshot | PASS |
| Excluded-path scan | PASS |
| Packaged manifest version | PASS |
| SHA256 recomputation and sidecar match | PASS |

No git tag was created. No C11 work was run. No runtime or business-code source
files were modified by this phase.
