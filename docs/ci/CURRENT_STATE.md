# CI/CD Current State

**Status:** Phase CI01 Audit — 2026-07-13  
**CI/CD Maturity:** Manual (no automated pipelines)

> **Note (Phase3S02.2):** This document was authored against the `1.9.5-alpha` baseline. The current release is `1.9.6-alpha` (Phase3S01 freeze). Version-dependent examples (build commands, artifact names) below reflect the snapshot at time of audit. See `docs/developer/TESTING.md` for the current unified test gate commands (S02.1).

---

## 1. Automated Commands Available Today

All of the following can be executed from a developer workstation with Python 3.12 and PowerShell:

### Extension Tests (Offline)

```powershell
# Static skeleton validation (~40 assertions across 26 methods)
python -m unittest crm-extension.tests.test_extension_skeleton -v

# SearchStrategy foundation validation (2 methods)
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v
```

### Connector Tests (Offline)

```powershell
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

11 test files, ~89 test methods covering sync adapter, connector API, worker core, persistence hardening, job runner, lifecycle, email, feedback, Brevo, signal export, real client safety.

### Deployment Validation (Offline)

```powershell
python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v
```

### Deployment Validation (Live — requires CRM)

```powershell
python deployment/validation/phase3c02_1_api_acl_acceptance.py
# Requires: ESPOCRM_BASE_URL + 4 API key env vars + running EspoCRM with provisioned users
```

### Extension Package Build

```powershell
cd crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension-1.9.5-alpha.zip
```

### SHA-256 Generation (Manual)

```powershell
Get-FileHash ..\deployment\prospecting-extension-1.9.5-alpha.zip -Algorithm SHA256
```

---

## 2. Command Stability Assessment

| Command | Stable? | Notes |
|---------|---------|-------|
| `test_extension_skeleton.py` | ✅ Stable | Pure static validation; no network, no database |
| `test_phase3c02_search_strategy_foundation.py` | ✅ Stable | Pure static validation |
| `test_phase3c02_1a_search_strategy_detail.py` | ✅ Stable | Pure static validation |
| Connector unit tests (10 files) | ✅ Stable | Mocked HTTP, memory stores |
| `test_espocrm_real_client.py` | ⚠️ Conditional | Env-gated; safe when `ESPOCRM_TEST_ENV` unset |
| `phase3c02_1_api_acl_acceptance.py` | ⚠️ Conditional | Requires live CRM + provisioned users |
| `build_release_package.ps1` | ✅ Stable | Pure ZIP packaging, no side effects |

---

## 3. Environment Dependencies

### Local Only (No External Services)

| Category | Files | Requires |
|----------|-------|----------|
| Extension skeleton | 2 test files | Python 3.12 stdlib + repo checkout |
| Connector unit | 10 test files | Python 3.12 stdlib + PYTHONPATH + repo checkout |
| Deployment validation (static) | 1 test file | Python 3.12 stdlib + repo checkout |
| Build script | 1 PowerShell | PowerShell 5.1+ |
| **Total offline tests** | **13 files, ~118 methods** | Python 3.12 + repo checkout |

### Requires Docker

None currently. No Docker-based test infrastructure exists.

### Requires Live EspoCRM

| Item | Files | Notes |
|------|-------|-------|
| API ACL acceptance | `deployment/validation/phase3c02_1_api_acl_acceptance.py` | Manual only; needs 4 provisioned users |
| Real client live tests | `test_espocrm_real_client.py` | Env-gated behind `ESPOCRM_TEST_ENV=true` |
| Provisioning scripts | 26 PHP files | Manual execution on CRM host |

### Requires Browser

None. Zero browser/UI tests exist.

---

## 4. Side-Effect Risk Classification

### Read-Only / No Side Effects (Safe for CI)

- All extension skeleton tests
- All connector unit tests (mocked HTTP)
- All deployment validation static tests
- Build script (produces artifact in `deployment/`)

### Data Side Effects (Needs Cleanup)

- `phase3c02_1_api_acl_acceptance.py` — creates/deletes `[CHITU_PHASE3C02_TEST]` records
- `test_espocrm_real_client.py` (live mode) — creates Lead records
- All provisioning scripts — create roles, users, dashboards on CRM

### Destructive (Requires Gating)

- Provisioning cleanup scripts — delete records
- Extension uninstall — removes module files from CRM

---

## 5. Manual-Only Procedures

The following currently have **no automation** and require human execution:

| Procedure | Current Method | Automation Feasibility |
|-----------|---------------|----------------------|
| Extension install on CRM | Admin UI upload | Automatable via REST API |
| Extension uninstall | Admin UI | Automatable via REST API |
| Cache rebuild | Admin UI / CLI | Automatable via REST API |
| Provisioning script execution | Manual PHP run on CRM host | Automatable via REST API |
| Runtime verification | Manual walkthrough per MANUAL_TESTS.md | Partially automatable (Layers 5-6) |
| Browser workflow tests | Manual per MANUAL_TESTS.md | Automatable via Playwright |
| SHA-256 generation | Manual PowerShell | Trivially automatable |
| Git tag creation | Manual | Automatable via GitHub Actions |
| Release notes | Manual Markdown | Template-able, human review required |

---

## 6. Current CI/CD Infrastructure

| Item | Status |
|------|--------|
| GitHub Actions workflows | **None** — `.github/` directory does not exist |
| CI configuration (any platform) | **None** |
| Pre-commit hooks | **None** |
| Secret scanning | **None** |
| Automated test runner script | **None** (T02 will create unified entrypoints) |
| Automated build pipeline | **None** (only manual `build_release_package.ps1`) |
| Automated release | **None** |
| Test reporting (JUnit XML) | **None** |
| Coverage reporting | **None** |
| Branch protection rules | Unknown (not visible in repository) |

---

## 7. Versioning and Release Infrastructure

| Item | Current State |
|------|---------------|
| Version authority | `crm-extension/manifest.json` (`"version": "1.9.5-alpha"`) |
| Build script | `crm-extension/scripts/build_release_package.ps1` |
| Artifact naming | `prospecting-extension-<version>.zip` |
| Checksum format | SHA-256 sidecar (`<zip>.sha256`) |
| Historical artifacts | Versioned ZIPs through `1.9.5-alpha`; see `docs/release/README.md` |
| Release notes | `docs/release/` index with package notes through `1.9.5-alpha` |
| Git tag convention | None standardized (tags match extension version when created) |
| Release process doc | `docs/release/RELEASE_PROCESS.md` (8-step manual process) |
| Changelog policy | `docs/release/CHANGELOG_POLICY.md` |
| Version policy | `docs/release/VERSION_POLICY.md` |

---

## 8. Key CI/CD Gaps

1. **No CI pipeline at all** — every test run is manual
2. **No unified test entrypoint** — separate commands for each test suite (T02 will address)
3. **No package validation automation** — ZIP structure checked manually
4. **No automated install/upgrade verification** — manual only
5. **No runtime test harness** — live tests require manual CRM setup (T04 will address)
6. **No browser tests** — all UI verification is manual (T05 will address)
7. **No automated release** — entirely manual process
8. **No secret scanning** — test credentials committed to repo
9. **No automated cleanup** — test residue requires manual `--cleanup` flag
10. **No Docker infrastructure** — no containerized test environments
11. **No CI-aware test design** — tests don't produce JUnit XML or structured output
12. **No branch/tag policy enforcement** — manual convention only
