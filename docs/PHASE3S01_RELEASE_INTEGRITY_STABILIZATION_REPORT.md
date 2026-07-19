# Phase3S01 — Release Integrity Stabilization Report

**Date:** 2026-07-20
**Verdict:** PASS
**Ready for Phase3S02:** YES

---

## 1. Original Issues — Verified

| # | Claim | Verified? | Resolution |
|---|-------|-----------|------------|
| 1 | Working tree contains SendExecution, DraftApproval, ReplyEvent entityDefs not in v1.9.5-alpha ZIP | ✅ CONFIRMED | Rebuilt ZIP; all 12 entityDefs now included |
| 2 | Two different contents share same version label 1.9.5-alpha | ✅ CONFIRMED | Bumped to 1.9.6-alpha; old deployment artifacts removed |
| 3 | README/INSTALL ZIP filename vs disk actual filename mismatch | ✅ CONFIRMED | Disk filename aligned to VERSION_POLICY naming convention (`prospecting-extension-<version>.zip`) |
| 4 | Build script path in README missing `crm-extension/` prefix | ✅ CONFIRMED | Fixed to `crm-extension/scripts/build_release_package.ps1` |
| 5 | test_phase3c02_2c_job_runner.py has CWD-dependent relative paths | ✅ CONFIRMED | Paths anchored to `__file__` via `Path(__file__).resolve().parents[2]` |
| 6 | Test entrypoints inconsistent across docs | ❌ NOT A REAL ISSUE | TEST_PLAN, UNIFIED_TEST_ENTRYPOINTS, and T02 runner already consistent |

---

## 2. Version Selection Rationale

**Chosen:** `1.9.6-alpha`

Reasoning:
- VERSION_POLICY mandates `MAJOR.MINOR.PATCH[-prerelease]` format
- Repository history shows 19 versions all following patch-bump convention for entity/feature additions (1.9.0 → 1.9.1 → … → 1.9.4 → 1.9.5)
- Working tree added 3 new entities (SendExecution, DraftApproval, ReplyEvent) plus associated scopes, metadata, and layouts since 1.9.5-alpha
- `1.9.5-alpha.1` is not a format used anywhere in the repo's 19-version history
- No other convention-violating format was considered

Artifact naming follows VERSION_POLICY:
- `deployment/prospecting-extension-1.9.6-alpha.zip`
- `deployment/prospecting-extension-1.9.6-alpha.zip.sha256`

---

## 3. Old ZIP vs New ZIP — Content Differences

| Metric | Old deployment ZIP (`v1.9.5-alpha.zip`) | Old historical ZIP (`prospecting-extension-1.9.5-alpha.zip`) | New ZIP (`prospecting-extension-1.9.6-alpha.zip`) |
|--------|----------------------------------------|-------------------------------------------------------------|---------------------------------------------------|
| Total entries | 197 | 182 | 234 |
| entityDefs count | 9 | 9 | 12 |
| SendExecution | ❌ Missing | ❌ Missing | ✅ Included |
| DraftApproval | ❌ Missing | ❌ Missing | ✅ Included |
| ReplyEvent | ❌ Missing | ❌ Missing | ✅ Included |
| SHA256 | `09E2E4...B4D1B2` | `927E0B...8CF1C7E4` | `2A0B16...C6719E` |
| Naming convention | `v` prefix (non-standard) | `prospecting-extension-` (standard) | `prospecting-extension-` (standard) |

Note: The old deployment ZIP and old historical ZIP had different SHA256 hashes — confirming the audit finding that two different contents shared the 1.9.5-alpha label.

---

## 4. EntityDefs and Key Entities Confirmed

### Working tree → ZIP parity: ✅ 12/12 match

| Entity | In Working Tree | In New ZIP | Scope file |
|--------|:---:|:---:|:---:|
| DraftApproval | ✅ | ✅ | ✅ |
| EmailEvent | ✅ | ✅ | ✅ |
| Lead | ✅ | ✅ | N/A (core entity) |
| LearningSignal | ✅ | ✅ | ✅ |
| Opportunity | ✅ | ✅ | N/A (core entity) |
| ProspectPool | ✅ | ✅ | ✅ |
| ReplyEvent | ✅ | ✅ | ✅ |
| ResearchEvidence | ✅ | ✅ | ✅ |
| SalesFeedback | ✅ | ✅ | ✅ |
| SearchJob | ✅ | ✅ | ✅ |
| SearchStrategy | ✅ | ✅ | ✅ |
| SendExecution | ✅ | ✅ | ✅ |

---

## 5. Documentation Path Consistency

| Document | Reference | Before | After | Status |
|----------|-----------|--------|-------|--------|
| README.md L6 | Version | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| README.md L9 | Artifact filename | `prospecting-extension-1.9.5-alpha.zip` | `prospecting-extension-1.9.6-alpha.zip` | ✅ Fixed |
| README.md L35 | Build script path | `scripts/build_release_package.ps1` | `crm-extension/scripts/build_release_package.ps1` | ✅ Fixed |
| INSTALL.md L4 | Version | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| INSTALL.md L26 | Build command | `prospecting-extension-1.9.5-alpha.zip` | `prospecting-extension-1.9.6-alpha.zip` | ✅ Fixed |
| PACKAGE.md L37 | Build command | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| PACKAGE.md L51 | Checksum command | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| PACKAGE.md L70 | Known artifacts table | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| PACKAGE.md L72 | SHA256 note | "no committed sidecar" | "committed sidecar at ..." | ✅ Fixed |
| VERSIONING.md L9-L10 | Version/releaseDate | `1.9.5-alpha` / `2026-07-13` | `1.9.6-alpha` / `2026-07-20` | ✅ Fixed |
| VERSIONING.md L18 | Example filename | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| VERSIONING.md L40 | SHA256 note | "SHA-256 sidecar is still a release-hygiene follow-up" | "with a committed SHA-256 sidecar" | ✅ Fixed |
| UPGRADE.md L7 | Version | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |
| VERSION_POLICY.md L8 | Current release | `1.9.5-alpha` | `1.9.6-alpha` | ✅ Fixed |

All ZIP filenames in documentation now match the disk artifact:
`deployment/prospecting-extension-1.9.6-alpha.zip`

---

## 6. Test Entrypoint Consistency

| Source | Extension | Connector | Worker | Static | Runtime | Baseline |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| TEST_PLAN.md | ✅ `crm-extension/tests/` | ✅ `chitu-connector/tests/` | ✅ phase3c02 files | N/A | N/A | N/A |
| UNIFIED_TEST_ENTRYPOINTS.md | ✅ via T02 runner | ✅ via T02 runner | ✅ via T02 runner | ✅ via T02 runner | ✅ via T02 runner | ✅ via T02 runner |
| T02 runner (`run-tests.ps1`) | ✅ `crm-extension/tests/test_*.py` | ✅ `chitu-connector/tests/test_*.py` | ✅ `test_phase3c02_*.py` | ✅ `deployment/validation/test_*.py` | ✅ `tests/runtime/test_*.py` | ✅ `tests/regression/test_*.py` |

**Verdict: Consistent.** All three documents agree on test location and discovery patterns.

---

## 7. Hermetic Test Verification

**Test:** `test_phase3c02_2c_job_runner.py::EspoRepositoryTests::test_static_boundary_has_no_sync_service_or_real_provider`

**Before:** Used bare `Path("chitu-connector/...")` — required CWD to be repo root.
**After:** Uses `Path(__file__).resolve().parents[2] / relative` — works from any CWD.

**Verification:**
- Test passed when run from repo root (`D:\EspoCRM-Production`)
- Test passed when run via `unittest discover -s chitu-connector/tests` (which sets start-dir but does not change CWD)
- Path resolution is now self-contained — no external CWD dependency remains

---

## 8. ZIP SHA-256

```
2A0B161C5E4B13ADC14DB4AB69A8EAA54FFF8E2431D42A4CC59BAECD88C6719E  prospecting-extension-1.9.6-alpha.zip
```

Sidecar file: `deployment/prospecting-extension-1.9.6-alpha.zip.sha256`

---

## 9. Test Results

| Suite | Tests | Status |
|-------|------:|:------:|
| Extension (`crm-extension/tests/`) | 75 | ✅ PASS |
| Connector (`chitu-connector/tests/`) | 279 | ✅ PASS |
| Worker (`test_phase3c02_*.py`) | 31 | ✅ PASS |
| Static (`deployment/validation/`) | 2 | ✅ PASS |
| Runtime (`tests/runtime/`) | 11 | ✅ PASS |
| Baseline (`tests/regression/`) | 7 | ✅ PASS |
| **Total** | **405** | **✅ ALL PASS** |

---

## 10. Modified Files

| File | Change Type | Description |
|------|-------------|-------------|
| `crm-extension/manifest.json` | Modified | Version `1.9.5-alpha` → `1.9.6-alpha`; releaseDate `2026-07-13` → `2026-07-20` |
| `README.md` | Modified | Version, artifact filename, build script path |
| `docs/deployment/INSTALL.md` | Modified | Version, build command filename |
| `docs/deployment/PACKAGE.md` | Modified | Version, build command, checksum command, artifact table, SHA256 note |
| `docs/deployment/VERSIONING.md` | Modified | Version, releaseDate, example filename, SHA256 note |
| `docs/deployment/UPGRADE.md` | Modified | Version |
| `docs/release/VERSION_POLICY.md` | Modified | Current packaged release |
| `crm-extension/tests/test_extension_skeleton.py` | Modified | 5 version assertions `1.9.5-alpha` → `1.9.6-alpha` |
| `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` | Modified | 1 version assertion `1.9.5-alpha` → `1.9.6-alpha` |
| `chitu-connector/tests/test_phase3c02_2c_job_runner.py` | Modified | CWD dependency fix (paths anchored to `__file__`) |
| `deployment/v1.9.5-alpha.zip` | Deleted | Old deployment artifact (wrong naming convention) |
| `deployment/v1.9.5-alpha.zip.sha256` | Deleted | Old SHA256 sidecar |
| `deployment/prospecting-extension-1.9.6-alpha.zip` | **New** | Rebuilt release ZIP (234 entries, 12 entityDefs) |
| `deployment/prospecting-extension-1.9.6-alpha.zip.sha256` | **New** | SHA256 sidecar |

12 modified/deleted files + 2 new files = 14 files changed.

---

## 11. Unmodified Scope — Confirmed

The following were **not touched** and remain unchanged:

- ✅ Worker (`chitu_connector/acquisition/runner.py`, worker execution logic)
- ✅ Queue (queue contract in `tests/test_phase3c13_1_queue_contract.py`)
- ✅ Provider (provider contract, Brevo adapter)
- ✅ CRM Bridge (bridge contract, CRM bridge adapter)
- ✅ CRM Projection (projection tests)
- ✅ SendExecution business logic
- ✅ Retry behavior
- ✅ Payload snapshot storage logic
- ✅ Brevo real-send logic
- ✅ CRM schema/entity content (entityDefs JSON bodies unchanged; only version assertions in tests updated)
- ✅ Any C15 features
- ✅ Any dependency versions
- ✅ Any database data
- ✅ Any external services
- ✅ Any real email sending
- ✅ Historical release packages in `archive/deployment/historical-packages/`

---

## 12. Residual Risks

1. **CI documentation lag:** `docs/ci/RELEASE_AUTOMATION_DESIGN.md` and `docs/ci/CURRENT_STATE.md` reference `1.9.5-alpha` as historical state. These are design/reference documents capturing the state at time of writing — not operational docs. No functional impact.
2. **T02 regression gate runner:** The `run-regression-gate.ps1` script has a pre-existing process-launch issue with Python resolution when invoked from PowerShell 5.1 (the `Start` method on `ProcessStartInfo` cannot find `python`). This is not caused by Phase3S01 and does not affect direct `python -m unittest` invocation.
3. **Archived v1.9.5-alpha copies:** Two different ZIPs with the 1.9.5-alpha label remain in `archive/` — one in `historical-packages/` and one in `runtime-backups/c11_1_baseline/`. These are immutable archival copies and do not affect current release integrity.
4. **Release notes:** `docs/release/RELEASE_NOTES_1.9.5-alpha.md` is a historical record for that version. A new `RELEASE_NOTES_1.9.6-alpha.md` should be authored in a subsequent phase to document the 1.9.6-alpha changes.

---

## 13. Git Status

```
On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  modified:   README.md
  modified:   chitu-connector/tests/test_phase3c02_2c_job_runner.py
  modified:   crm-extension/manifest.json
  modified:   crm-extension/tests/test_extension_skeleton.py
  modified:   crm-extension/tests/test_phase3c02_search_strategy_foundation.py
  deleted:    deployment/v1.9.5-alpha.zip
  deleted:    deployment/v1.9.5-alpha.zip.sha256
  modified:   docs/deployment/INSTALL.md
  modified:   docs/deployment/PACKAGE.md
  modified:   docs/deployment/UPGRADE.md
  modified:   docs/deployment/VERSIONING.md
  modified:   docs/release/VERSION_POLICY.md

Untracked files:
  deployment/prospecting-extension-1.9.6-alpha.zip
  deployment/prospecting-extension-1.9.6-alpha.zip.sha256

no changes added to commit (use "git add" and/or "git commit -a")
```

**No commit was made** — per task instructions.

---

## 14. Verdict

**PASS** — All 6 original issues verified and resolved:
- ✅ Version drift eliminated (1.9.5-alpha → 1.9.6-alpha)
- ✅ Release ZIP rebuilt with all 12 entityDefs
- ✅ ZIP filename aligned to VERSION_POLICY
- ✅ Documentation filenames and paths unified
- ✅ Test entrypoints verified consistent
- ✅ CWD dependency fixed in test_phase3c02_2c_job_runner.py
- ✅ All 405 tests pass across 6 suites
- ✅ No forbidden code modified

**READY_FOR_PHASE3S02:** YES
