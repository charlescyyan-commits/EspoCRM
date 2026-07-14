# Workflow Plan

**Status:** Phase CI01 Design — 2026-07-13

> Defines the recommended GitHub Actions workflow split. No `.github/workflows/**` files are created in this phase.

---

## Workflow Inventory

```
.github/workflows/
├── ci-static.yml         # Layers 1-2: repo validation + static checks
├── ci-tests.yml          # Layers 3-5: extension + connector + contract tests
├── ci-package.yml        # Layers 6-7: package validation + artifact build
├── ci-runtime.yml        # Layer 8: runtime REST tests (disposable CRM)
├── ci-browser.yml        # Layer 9: browser acceptance tests (Playwright)
└── release.yml           # Layer 10: release gate + artifact publication
```

---

## 1. `ci-static.yml` — Static Validation

| Attribute | Value |
|-----------|-------|
| **Trigger** | `push` (all branches), `pull_request` (→ main) |
| **Purpose** | Fast pre-flight: catch JSON errors, metadata parity issues, route mismatches before running heavier tests |
| **Jobs** | `static-checks` |
| **Runner** | `ubuntu-latest` (or `windows-latest` if PowerShell required) |
| **Steps** | Checkout → Python 3.12 setup → Run skeleton tests → Run SearchStrategy foundation tests → Run detail view validation |
| **Inputs** | None |
| **Dependencies** | None |
| **Artifacts** | None |
| **Required secrets** | None |
| **Failure behavior** | Blocks PR merge; alerts on push |
| **Can run now** | ✅ Yes — all tests are stable and pass offline |
| **Blockers** | None |
| **Expected runtime** | < 1 minute |

---

## 2. `ci-tests.yml` — Unit & Contract Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | `push` (all branches), `pull_request` (→ main) |
| **Purpose** | Run all offline connector unit tests + contract tests |
| **Jobs** | `connector-tests` |
| **Runner** | `ubuntu-latest` |
| **Steps** | Checkout → Python 3.12 setup → Set PYTHONPATH → Run connector tests → Check live test guard |
| **Inputs** | None |
| **Dependencies** | `ci-static.yml` must pass (or runs in parallel with final gate check) |
| **Artifacts** | Test results (JUnit XML — future) |
| **Required secrets** | None |
| **Failure behavior** | Blocks PR merge |
| **Can run now** | ✅ Yes — all connector tests are mocked and pass |
| **Blockers** | T02: needs unified entrypoint for clean PYTHONPATH handling. T03: needs `@unittest.skipIf` guard on real client tests. |
| **Expected runtime** | < 3 minutes |

---

## 3. `ci-package.yml` — Package & Build Validation

| Attribute | Value |
|-----------|-------|
| **Trigger** | `pull_request` (→ main), `push` (→ main), `release` (published) |
| **Purpose** | Build extension ZIP, validate structure, generate SHA-256 |
| **Jobs** | `build-and-validate` |
| **Runner** | `windows-latest` (PowerShell build script) |
| **Steps** | Checkout → Build ZIP → Validate structure (manifest root, files/ dir, path format) → Validate manifest.json → Generate SHA-256 → Upload artifact |
| **Inputs** | `version` (optional override; defaults to manifest) |
| **Dependencies** | `ci-tests.yml` must pass |
| **Artifacts** | `prospecting-extension-<version>.zip`, `<zip>.sha256` |
| **Required secrets** | None (for dry-run); `ARTIFACT_STORAGE_*` for release |
| **Failure behavior** | Blocks release |
| **Can run now** | ✅ Build script is stable. Missing: automated ZIP structure validation (needs a small Python script). |
| **Blockers** | ZIP structure validation not yet automated (trivial to implement). |
| **Expected runtime** | < 1 minute |

---

## 4. `ci-runtime.yml` — Runtime REST Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | `schedule` (nightly), `workflow_dispatch` (manual), `release` (published) |
| **Purpose** | Run live REST API tests against a disposable EspoCRM instance |
| **Jobs** | `provision-crm`, `run-rest-tests`, `cleanup` |
| **Runner** | `ubuntu-latest` |
| **Steps** | Start Docker EspoCRM → Install extension → Provision test users → Run REST tests → Capture results → Cleanup (always, even on failure) |
| **Inputs** | `crm_version` (EspoCRM version to test against), `extension_artifact` (from ci-package) |
| **Dependencies** | `ci-package.yml` artifact, Docker, disposable EspoCRM image |
| **Artifacts** | Test results (JUnit XML), cleanup verification log |
| **Required secrets** | `ESPOCRM_BASE_URL`, `ESPOCRM_ADMIN_API_KEY`, test user API keys (4 users) |
| **Failure behavior** | Blocks release; advisory for nightly |
| **Can run now** | ❌ No — requires T04 (runtime test harness) + disposable CRM Docker setup |
| **Blockers** | T04: no runtime harness exists. No Docker EspoCRM image configured. No automated provisioning. Secret management not set up. |
| **Expected runtime** | 10-15 minutes |

---

## 5. `ci-browser.yml` — Browser Acceptance Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | `schedule` (weekly), `workflow_dispatch` (manual), `release` (published) |
| **Purpose** | Run Playwright browser tests against disposable EspoCRM |
| **Jobs** | `browser-tests` |
| **Runner** | `ubuntu-latest` |
| **Steps** | Start Docker EspoCRM → Install extension → Provision test users → Run Playwright tests → Capture screenshots on failure → Cleanup |
| **Inputs** | `crm_version`, `extension_artifact` |
| **Dependencies** | `ci-runtime.yml` (CRM must be functional), Playwright + browsers |
| **Artifacts** | Screenshots (on failure), test video (optional), JUnit XML |
| **Required secrets** | CRM credentials, test user passwords |
| **Failure behavior** | Blocks release; advisory for weekly |
| **Can run now** | ❌ No — requires T05 (browser tests) + T04 (runtime harness) |
| **Blockers** | T05: zero browser tests exist. No Playwright setup. No page objects. |
| **Expected runtime** | 15-20 minutes |

---

## 6. `release.yml` — Release Gate

| Attribute | Value |
|-----------|-------|
| **Trigger** | `push` of tag matching `v*` pattern |
| **Purpose** | Execute full release pipeline and publish artifacts |
| **Jobs** | `validate-all-gates`, `build-release`, `publish-artifact` |
| **Runner** | `windows-latest` (build), `ubuntu-latest` (validation) |
| **Steps** | Verify all lower gates pass → Bump version (if not already) → Build release ZIP → Generate SHA-256 → Tag commit → Create GitHub Release → Attach artifacts → Update docs index |
| **Inputs** | None (triggered by tag) |
| **Dependencies** | All ci-* workflows passing, release notes document present |
| **Artifacts** | Release ZIP + SHA-256 published to GitHub Releases |
| **Required secrets** | `GITHUB_TOKEN` (auto-provided), `ARTIFACT_STORAGE_*` |
| **Failure behavior** | Release blocked; tag remains but no artifacts published |
| **Can run now** | ❌ No — entire release chain needs automation |
| **Blockers** | No automated runtime tests. No browser tests. No package validation automation. Release notes are manual. |
| **Expected runtime** | 30-60 minutes (mostly waiting on runtime + browser tests) |

---

## Workflow Dependency Graph

```
ci-static.yml ──────┐
                    ├──► ci-package.yml ──► ci-runtime.yml ──► ci-browser.yml
ci-tests.yml ───────┘                                              │
                                                                   ▼
                                                            release.yml
```

- `ci-static.yml` and `ci-tests.yml` can run in **parallel** on push/PR
- `ci-package.yml` depends on both passing
- `ci-runtime.yml` depends on `ci-package.yml` (needs the built artifact)
- `ci-browser.yml` depends on `ci-runtime.yml` (needs a functional CRM)
- `release.yml` gates on all of the above

---

## What Can Be Created Now (Without Blockers)

| Workflow | Create Now? | Why |
|----------|------------|-----|
| `ci-static.yml` | ✅ Yes | All tests stable, no secrets, no CRM |
| `ci-tests.yml` | ⚠️ After T02+T03 | Needs unified entrypoint + skipIf guard |
| `ci-package.yml` | ⚠️ After ZIP validator | Build script stable; missing small validation script |
| `ci-runtime.yml` | ❌ After T04 | Needs runtime harness + Docker CRM |
| `ci-browser.yml` | ❌ After T05 | Needs browser tests |
| `release.yml` | ❌ After all above | Needs full pipeline |

---

## Parallel Risk Classification

Per T01/T02 boundary analysis:

| Category | Workflows | Notes |
|----------|-----------|-------|
| **SAFE NOW** | `ci-static.yml` design | No dependencies on T02 or Phase C03 |
| **WAIT FOR T02** | `ci-tests.yml` implementation | Needs unified entrypoints |
| **WAIT FOR T03** | `ci-tests.yml` (contract portion) | Needs ACL contract tests + skipIf guard |
| **WAIT FOR T04** | `ci-runtime.yml` | Needs runtime harness |
| **WAIT FOR T05** | `ci-browser.yml` | Needs browser tests |
| **WAIT FOR RELEASE POLICY** | `release.yml` | Needs stable release process + runtime verification |
