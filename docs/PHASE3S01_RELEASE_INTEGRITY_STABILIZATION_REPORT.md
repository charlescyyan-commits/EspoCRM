# Phase3S01 Release Integrity Stabilization Report

## Scope and commits

Phase3S01 restores release-package integrity without changing CRM business behavior, Queue, Worker, Provider, retry semantics, CRM schema/entities, C14.3 frozen contracts, or `ESPOCRM_SYNC_CONTRACT_V1.json`.

- S01 baseline commit: `2434de4a262ba487a6c4fd0d62c18e0155bad7f2` (`phase3s01: restore release integrity and rebuild 1.9.6-alpha`).
- S01.1 reproducibility commit: `21585f91f758f5ca0ec532ff12ce8db14112e66a` (`phase3s01: make release artifact reproducible across checkouts`).
- This report records the subsequent S01.2 clean-clone verification before its evidence-only commit.

No reset, rebase, amend, or force push was performed. The approved annotated release tag was created only after independent review and full S01 gate verification. Phase3S02 has not started.

## Cross-platform defect and remediation

An independent Linux clean-clone review rejected the original S01 artifact because nine Windows working-tree source files had CRLF bytes while Git's canonical clean-clone sources had LF bytes. The original Python builder read raw working-tree bytes, so Windows `--check` could pass while the canonical ZIP differed from an LF checkout. The PowerShell builder had the same raw-copy behavior.

S01.1 resolves this with all of the following:

- Root `.gitattributes` defines LF for known package text extensions and preserves known binary formats; PowerShell/CMD/BAT files retain CRLF policy.
- Both builders canonicalize only explicit text-source extensions (`.php`, `.py`, `.js`, `.json`, `.tpl`, `.md`, `.css`, `.html`, `.xml`, `.yml`, `.yaml`, `.txt`) to LF at the byte level. Other files are never decoded or transformed.
- The S01 regression gate independently compares ZIP entries against canonical text bytes, rejects CRLF in packaged text, and verifies normalization is binary-safe.
- `docs/deployment/PACKAGE.md` now documents root-relative Python build/check commands and canonical line-ending behavior.

The canonical package SHA changed from the Windows-working-tree result `D79FD97CD5868652D031FC9B0C081A00365A8B13D9E6E79A61E5BCB344216146` to the reproducible source result recorded below.

## Pytest exit diagnosis

The first S01.1 temporary-clone attempt displayed pytest progress at 100% but the direct execution harness did not return a final summary or observable exit code. S01.2 recreated the clone with `git clone --no-local` and a new `.venv-audit` containing only pytest 9.1.1 and its direct dependencies.

`python -s` reported `ENABLE_USER_SITE=False`; the environment contained no third-party pytest plugins. `pytest --trace-config` listed only pytest's built-in `_pytest.*` modules. Under `PYTHONNOUSERSITE=1` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, a temporary external wrapper ran each child command with explicit `wait()` and exit-code capture. Extension pytest exited 0 with 75 passed; connector pytest exited 0 with 279 passed. Therefore there was no repository test thread, child process, fixture, or plugin cleanup defect to fix. The earlier apparent hang was an execution-harness process-result collection issue, not a release-gate failure.

The two environment variables were used only to make this audit self-contained. They are verification conditions, not a repository runtime requirement; no test code or pytest configuration was changed in S01.2.

## Verification environments

| Environment | Python | pytest | Isolation |
| --- | --- | --- |
| Main worktree | `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe`, Python 3.12.13 | 9.1.1 | repository-local, ignored |
| Clean clone | Python 3.12.13, `.venv-audit` | 9.1.1 | created from `21585f9` using `git clone --no-local`; user site and plugin autoload disabled for audit |

## Main-worktree Gate results

All commands used `D:\EspoCRM-Production\.venv-s01\Scripts\python.exe` and exited 0.

| Gate | Command | Passed | Failed | Skipped | Exit |
| --- | --- | ---: | ---: | ---: | ---: |
| Extension | `python -m pytest crm-extension/tests -q` | 75 (+22 subtests) | 0 | 0 | 0 |
| Connector | from `chitu-connector`: `python -m pytest tests -q` | 279 (+92 subtests) | 0 | 0 | 0 |
| Root/runtime | `python -m pytest tests scripts/runtime -q` | 162 (+1042 subtests) | 0 | 0 | 0 |
| S01 integrity | `python -m pytest tests/regression/test_phase3s01_release_integrity.py -q` | 12 (+297 subtests) | 0 | 0 | 0 |
| Package baseline | `python -m pytest tests/regression/test_extension_package_baseline.py -q` | 5 (+535 subtests) | 0 | 0 | 0 |
| Unittest | `python -m unittest discover -s crm-extension/tests` | 75 | 0 | 0 | 0 |
| Builder check | `python crm-extension/scripts/build_release_package.py --check` | n/a | 0 | 0 | 0 |

The connector suite emitted ten pre-existing deprecation warnings. The main checkout may also report one ignored-cache write warning; neither is a failure. PowerShell/Python package-content parity executed inside the package baseline with no skip.

## Clean-clone Gate results

The clean clone was at `21585f91f758f5ca0ec532ff12ce8db14112e66a`. Each command used the one isolated Python executable with `-s`, `PYTHONNOUSERSITE=1`, and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; the temporary wrapper recorded normal child-process exit.

| Gate | Effective child command | Passed | Failed | Skipped | Exit |
| --- | --- | ---: | ---: | ---: | ---: |
| Extension | `python -s -m pytest crm-extension/tests -q` | 75 (+22 subtests) | 0 | 0 | 0 |
| Connector | from `chitu-connector`: `python -s -m pytest tests -q` | 279 (+92 subtests) | 0 | 0 | 0 |
| Root/runtime | `python -s -m pytest tests scripts/runtime -q` | 162 (+1042 subtests) | 0 | 0 | 0 |
| S01 integrity | `python -s -m pytest tests/regression/test_phase3s01_release_integrity.py -q` | 12 (+297 subtests) | 0 | 0 | 0 |
| Package baseline | `python -s -m pytest tests/regression/test_extension_package_baseline.py -q` | 5 (+535 subtests) | 0 | 0 | 0 |
| Unittest | `python -s -m unittest discover -s crm-extension/tests` | 75 | 0 | 0 | 0 |
| Builder check | `python -s crm-extension/scripts/build_release_package.py --check` | n/a | 0 | 0 | 0 |
| SHA sidecar | recompute ZIP SHA-256 and compare sidecar | n/a | 0 | 0 | 0 |
| Determinism | two consecutive canonical builds | n/a | 0 | 0 | 0 |
| Final check | `python -s crm-extension/scripts/build_release_package.py --check` | n/a | 0 | 0 | 0 |

## Canonical artifact evidence

- Artifact: `deployment/prospecting-extension-1.9.6-alpha.zip`
- Size: 141,563 bytes
- Regular ZIP entries: 234
- Packaged entity definitions: 12
- SHA-256: `2A3A1D88B2D7F01229801FD44F2AF73B84128445A86637564EF49F8D714B86DF`
- Sidecar: exact hash and archive filename match
- ZIP corruption check: `None`
- Text-entry CRLF scan: 0
- Source byte parity: PASS
- PowerShell/Python source-content parity: PASS
- First/second deterministic SHA-256: both `2A3A1D88B2D7F01229801FD44F2AF73B84128445A86637564EF49F8D714B86DF`

## Boundary and delivery status

The forbidden connector synchronization, acquisition runner/repository, and frozen contract paths have no S01 changes. No environment, cache, temporary clone, temporary ZIP, or diagnostic wrapper is tracked. A common-secret-pattern scan found no secrets in the S01.1 diff.

The clean-clone evidence commit was pushed normally to `origin/master`. The approved release tag below freezes the validated release commit; this status update is documentation only.

## Phase3S01 Status

| Field | Value |
| --- | --- |
| Status | PASS |
| Freeze date | 2026-07-20 |
| Tag | `v1.9.6-alpha` |
| Release HEAD | `1ce4cda2af00267ae769ab67b0062991fddcff30` |
| Independent remote review | PASS |
| Phase3S02 | NOT STARTED |

## Verdict

**PASS — READY FOR S01 REMOTE RE-REVIEW**
