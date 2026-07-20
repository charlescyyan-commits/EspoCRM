# Phase3S01 Release Integrity Stabilization Report

## 1. Baseline and repository state

- Initial and final uncommitted `HEAD`: `76c165b6a3ed633b4a5c5ad9a3f786922ff28f2c` on `master`.
- Initial `git status --short` contained 21 staged Phase3S01 paths; no unrelated paths were present (Git emitted a non-repository warning that `C:\Users\98624\.config\git\ignore` was inaccessible).
- `master` and its local `origin/master` tracking reference were aligned (`0` ahead, `0` behind).
- Audit baseline `fd671e56e8af222c5a77049401761b9c1509d490` is an ancestor of `HEAD`; no reset, rebase, amendment, or history rewrite was performed.

`fd671e5` has historical message `111` and its actual scope includes the C11–C14 CRM/connector send-boundary work. Phase3S01 does not extend or modify that frozen send core. The non-descriptive historical message remains a governance risk; any history rewrite is an owner decision outside this phase.

## 2. Issue verification and resolution

| Issue | Initial state and evidence | Phase3S01 action | Final state |
| --- | --- | --- | --- |
| B1 version/artifact identity | Manifest, deployment ZIP, and sidecar already named `1.9.6-alpha`; 19 historical ZIP checksums already matched `SHA256SUMS.txt`. No extra deployment ZIP was present. | Added permanent checks for canonical name, singleton deployment artifact, sidecar, historical checksum coverage, and source/artifact bytes. Rebuilt the canonical ZIP from source. | Fixed/gated. |
| B2 cross-platform builder | Only `build_release_package.ps1` existed. | Added an anchored, deterministic Python builder with fixed metadata, normal build, strict name policy, explicit temporary-output override, and `--check`. Preserved PowerShell and verified entry/content parity on Windows. | Fixed. |
| B3 S01 evidence | A tracked S01 report existed, but it declared `PASS`/S02 readiness without this run's required current gate evidence or the required C14-history disclosure. | Replaced it with this report from observed commands only. | Fixed/gated. |
| B4 release-document drift | Installation instructions used a hard-coded `D:\` path and invalid hyphenated Python module paths; release index still called `1.9.5-alpha` current. | Corrected root-relative commands, current artifact/version references, and release index. | Fixed. |
| B5 history scope disclosure | No 1.9.6-alpha notes disclosed the historical scope. | Added release notes with `fd671e5 ("111")` scope/governance disclosure and no-send-core-change statement. | Fixed. |
| B6 CWD/version/gate accuracy | Relevant tests were already `__file__`-anchored and the Job Runner test passed from root and `chitu-connector`; extension tests repeated literal version assertions. | Kept functional tests, consolidated each extension test file to a single `RELEASE_VERSION`, made package verification Python-first, and added CWD-independent builder coverage. | Fixed. |

First new-gate result: the initial Phase3S01 regression run failed six `Resources/layouts` semantic parity checks (Lead, ResearchEvidence, SalesFeedback). The corresponding non-packaged design mirrors were synchronized to the already-packaged module layout JSON. The final S01 gate passed all 10 checks.

## 3. Files changed

- `crm-extension/scripts/build_release_package.py` — deterministic cross-platform build and verification boundary.
- `tests/regression/test_extension_package_baseline.py` — Python package gate, determinism, and PowerShell/Python content-parity coverage.
- `tests/regression/test_phase3s01_release_integrity.py` — permanent S01 release-integrity regression gate.
- `crm-extension/Resources/layouts/{Lead,ResearchEvidence,SalesFeedback}/*.json` — synchronized six non-installed design mirrors to package sources.
- `crm-extension/tests/test_extension_skeleton.py`, `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` — one version constant per test file.
- `deployment/prospecting-extension-1.9.6-alpha.zip` and `.sha256` — rebuilt canonical artifact and matching sidecar.
- `README.md`, `docs/deployment/INSTALL.md`, `docs/deployment/VERSIONING.md`, `docs/release/VERSION_POLICY.md`, `docs/release/README.md` — current version, artifact, and root-command consistency.
- `docs/release/RELEASE_NOTES_1.9.6-alpha.md` — release scope and integrity notes.
- `.gitignore` — added the repo-local test virtualenv `.venv-s01/` (test environment only; never committed).
- This report.

Untouched boundaries include `chitu-connector/chitu_connector/espocrm_sync/**`, the acquisition runner and repository, all Worker/Queue/Provider/retry behavior, CRM schema/entities, `docs/PHASE3C14_*`, `docs/PHASE_G03_*`, and `ESPOCRM_SYNC_CONTRACT_V1.json`.

## 4. Test runtime and prior-number clarification

The previous revision of this report recorded that every mandated `pytest` command failed at collection with `No module named pytest`, while a separate set of `unittest` discoveries passed. Those earlier "137 root / 4 runtime / 279 connector passed" figures were produced by `python -m unittest`, **not** by pytest, so they could not stand as the mandated pytest evidence.

This run resolves that runtime blocker with a repository-local isolated virtual environment. No global or system Python package was installed, and no system Python was modified.

- Python executable: `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe`
- Python version: 3.12.13
- pip version: 25.0.1
- pytest version: 9.1.1
- Dependency source: the repository declares no pinned test-requirements file (only `chitu-connector/pyproject.toml`, a build definition with no test extras). Per the fallback policy, `pytest` alone is present inside the local venv.
- Isolation: the broken prior `.venv-s01/` (which referenced a removed Python 3.12 executable) was replaced with this repo-local environment; it is git-ignored and is not committed.

## 5. Mandated gate evidence

All commands used the same pytest-capable venv above.

| Command | Passed | Failed | Skipped | Exit |
| --- | ---: | ---: | ---: | ---: |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m pytest crm-extension/tests -q` | 75 (+22 subtests) | 0 | 0 | 0 |
| from `chitu-connector`: `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m pytest tests -q` | 279 (+92 subtests) | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m pytest tests scripts/runtime -q` | 160 (+808 subtests) | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m pytest tests/regression/test_phase3s01_release_integrity.py -q` | 10 (+63 subtests) | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m pytest tests/regression/test_extension_package_baseline.py -q` | 5 (+535 subtests) | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe -m unittest discover -s crm-extension/tests` | 75 | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe crm-extension/scripts/build_release_package.py` | build complete | 0 | 0 | 0 |
| `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe crm-extension/scripts/build_release_package.py --check` | check complete | 0 | 0 | 0 |

The connector suite emitted 10 pre-existing `DeprecationWarning`s from legacy `EmailLifecycleSyncService.sync` / `CampaignProjectionAdapter.project` paths. Pytest additionally emitted one ignored-cache write warning because pre-existing `.pytest_cache` directories are inaccessible. These are informational, not failures. No assertion was lowered, deleted, or converted to a skip. Gate 5 executed the Windows PowerShell/Python builder parity check with zero skips (`-rs` reported no skip reasons).

## 6. Artifact evidence

- Artifact: `deployment/prospecting-extension-1.9.6-alpha.zip`
- Size: 141,621 bytes.
- Package entries: 234 regular entries.
- Packaged source entity definitions: 12.
- SHA-256: `D79FD97CD5868652D031FC9B0C081A00365A8B13D9E6E79A61E5BCB344216146`
- Sidecar `deployment/prospecting-extension-1.9.6-alpha.zip.sha256`: matches the archive hash and filename exactly (case-insensitive hex).
- Determinism: two consecutive isolated builds in this environment produced the identical SHA-256 above (byte-identical). The rebuilt artifact also equals the already-staged working-tree ZIP and its sidecar, so this run introduced no unexpected artifact change. The old committed artifact differed only in the prior S01 rebuild; the current source tree deterministically yields the hash above.
- Python `--check`: passed.
- Windows PowerShell/Python builder parity: verified via Gate 5 (no skip).

## 7. Boundary verification and residual risk

`git diff --stat` for the three forbidden ranges (`chitu-connector/chitu_connector/espocrm_sync`, `chitu-connector/chitu_connector/acquisition/runner.py`, `chitu-connector/chitu_connector/acquisition/espo_repository.py`) produced no output. No test was deleted and no assertion was weakened. No test-environment files (`.venv-s01/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`) are staged or committed. The only `.gitignore` change is the added `.venv-s01/` entry.

The pytest runtime blocker recorded in the prior revision is resolved; the four mandated pytest commands plus the S01 and baseline gates now execute and pass. No CRM write, external CRM call, real send, or release tag was performed.

## 8. Git delivery

- Initial and pre-commit `HEAD`: `76c165b6a3ed633b4a5c5ad9a3f786922ff28f2c` on `master`; its local `origin/master` tracking reference was aligned before commit (`0` ahead, `0` behind).
- This report is updated before the single intended normal commit: `phase3s01: restore release integrity and rebuild 1.9.6-alpha`.
- The post-commit execution summary records the actual commit hash, ordinary `origin/master` push result, and local/remote equality. No tag, amend, rebase, reset, or Freeze is permitted.

## Verdict

**PASS — READY FOR S01 REMOTE RE-REVIEW**
