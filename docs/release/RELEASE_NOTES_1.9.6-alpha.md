# Release Notes: 1.9.6-alpha

**Artifact:** `deployment/prospecting-extension-1.9.6-alpha.zip`  
**Integrity sidecar:** `deployment/prospecting-extension-1.9.6-alpha.zip.sha256`

## Release-integrity stabilization

- Rebuilt the canonical release ZIP from the current `manifest.json` and installable `files/` source tree.
- Added a cross-platform, deterministic Python builder and a deep artifact/source parity check.
- Retained the Windows PowerShell builder and added a Windows parity check for the two builders' package contents.
- Added CWD-independent release-integrity regression coverage and corrected root-level build and verification commands in release documentation.
- Verified the historical package checksum manifest. The historical `1.9.5-alpha` ZIP identity issue remains recorded as historical evidence; that ZIP is not rebuilt or rewritten by this release.

## Scope disclosure

The historical baseline commit `fd671e5` (message: `111`) supplied the prior release-state scope. This Phase3S01 stabilization changes release packaging, integrity gates, and release documentation only. It introduces no business feature and makes no change to the Send Path, Queue, Worker, Provider, retry behavior, CRM schema, or frozen C14 contracts.

The non-descriptive historical commit message `111` remains a governance risk. Any history rewrite, split, or amendment is an owner decision and is outside this release.

## Verification

From the repository root:

```text
python crm-extension/scripts/build_release_package.py
python crm-extension/scripts/build_release_package.py --check
python -m unittest tests.regression.test_phase3s01_release_integrity
```

Use `py` instead of `python` on Windows where that launcher is provided. This is an alpha release for disposable or explicitly approved CRM validation only; it does not authorize a production send or deployment.
