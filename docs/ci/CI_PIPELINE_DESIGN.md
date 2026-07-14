# CI Pipeline Design

**Status:** Phase CI01 Design — 2026-07-13

> Defines a 10-layer CI pipeline for the EspoCRM Production workspace. Layers are cumulative gates: each layer that fails blocks all layers above it. No actual workflow files are created in this phase.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 10: Release Gate                                  │
│ (Full gate: all layers + sign-off)                      │
├─────────────────────────────────────────────────────────┤
│ Layer 9: Browser Tests                                  │
│ (Playwright UI workflows)                               │
├─────────────────────────────────────────────────────────┤
│ Layer 8: Runtime Tests                                  │
│ (Real EspoCRM REST API, disposable instance)            │
├─────────────────────────────────────────────────────────┤
│ Layer 7: Artifact Build                                 │
│ (ZIP package, SHA-256, structure validation)            │
├─────────────────────────────────────────────────────────┤
│ Layer 6: Package Validation                             │
│ (ZIP structural checks, manifest audit)                 │
├─────────────────────────────────────────────────────────┤
│ Layer 5: Worker / Contract Tests                        │
│ (Sync contract, ACL contract, worker behavior)          │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Connector Tests                                │
│ (All mocked connector unit tests)                       │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Extension Tests                                │
│ (Skeleton, entity metadata, SearchStrategy)             │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Static Checks                                  │
│ (JSON validity, metadata parity, route parity)          │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Repository Validation                          │
│ (Branch, working tree, file existence)                  │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: Repository Validation

| Attribute | Value |
|-----------|-------|
| **Trigger** | Every push, every PR |
| **Required commands** | `git status --porcelain` (verify no unexpected dirty files in release path), `git branch --show-current` |
| **Dependencies** | Git, repo checkout |
| **Expected duration** | < 5 seconds |
| **Side-effect risk** | None |
| **Blocking** | Yes — blocks all layers |
| **Safe for PRs** | Yes |
| **Requires secrets** | No |
| **Current readiness** | ✅ READY — trivial to implement |

---

## Layer 2: Static Checks

| Attribute | Value |
|-----------|-------|
| **Trigger** | Every push, every PR |
| **Required commands** | `python -m unittest crm-extension.tests.test_extension_skeleton -v`, `python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v`, `python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v` |
| **Dependencies** | Python 3.12 stdlib, repo checkout |
| **Expected duration** | < 30 seconds |
| **Side-effect risk** | None (read-only) |
| **Blocking** | Yes — static failures block all further testing |
| **Safe for PRs** | Yes |
| **Requires secrets** | No |
| **Current readiness** | ✅ READY — commands are stable and all pass |

---

## Layer 3: Extension Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | Every push, every PR |
| **Required commands** | (Covered by Layer 2 — extension tests are static) |
| **Dependencies** | Python 3.12 stdlib |
| **Expected duration** | < 10 seconds (already run in Layer 2) |
| **Side-effect risk** | None |
| **Blocking** | Yes |
| **Safe for PRs** | Yes |
| **Requires secrets** | No |
| **Current readiness** | ✅ READY — merged into Layer 2 for efficiency |

**Note:** Extension tests are purely static (skeleton validation + metadata parity checks). They run as part of Layer 2.

---

## Layer 4: Connector Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | Every push, every PR |
| **Required commands** | `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` (with `PYTHONPATH` set) |
| **Dependencies** | Python 3.12 stdlib, `chitu_connector` package, `PYTHONPATH=chitu-connector` |
| **Expected duration** | < 2 minutes |
| **Side-effect risk** | None (all HTTP mocked; live tests auto-skipped without env) |
| **Blocking** | Yes |
| **Safe for PRs** | Yes — requires `@unittest.skipIf` guard on real client tests (see T03) |
| **Requires secrets** | No |
| **Current readiness** | ✅ READY — but needs T02 unified entrypoint + T03 skipIf guard |

---

## Layer 5: Worker / Contract Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | Every push, every PR (merged with Layer 4 for efficiency) |
| **Required commands** | Covered by Layer 4 discover (worker + contract tests are in connector test suite) |
| **Dependencies** | Same as Layer 4 |
| **Expected duration** | Included in Layer 4 timing |
| **Side-effect risk** | None |
| **Blocking** | Yes |
| **Safe for PRs** | Yes |
| **Requires secrets** | No |
| **Current readiness** | ✅ READY — worker/contract tests already pass offline |

**Note:** ACL contract tests and SearchStrategy logic tests are NOT yet implemented (T03 scope). When added, they merge into this layer.

---

## Layer 6: Package Validation

| Attribute | Value |
|-----------|-------|
| **Trigger** | PR to main/master, pre-release |
| **Required commands** | Validate ZIP structure: `manifest.json` at root, `files/` directory, forward-slash paths, no `Resources/` or `tests/` in archive. Verify `manifest.json` version matches expected. |
| **Dependencies** | Python 3.12 stdlib (`zipfile`), build artifact from Layer 7 |
| **Expected duration** | < 10 seconds |
| **Side-effect risk** | None (read-only validation) |
| **Blocking** | Yes — invalid package blocks release |
| **Safe for PRs** | Yes |
| **Requires secrets** | No |
| **Current readiness** | ⚠️ NEEDS IMPLEMENTATION — no automated ZIP validation exists |

---

## Layer 7: Artifact Build

| Attribute | Value |
|-----------|-------|
| **Trigger** | Pre-release, release tag |
| **Required commands** | `build_release_package.ps1 -OutputPath deployment/prospecting-extension-<version>.zip`, SHA-256 generation, structure validation |
| **Dependencies** | PowerShell 5.1+, `crm-extension/manifest.json`, `crm-extension/files/` |
| **Expected duration** | < 30 seconds |
| **Side-effect risk** | **Medium** — writes to `deployment/` directory |
| **Blocking** | Yes — artifact must be valid for release |
| **Safe for PRs** | ⚠️ Conditional — OK as dry-run; production build should be on release branch only |
| **Requires secrets** | No |
| **Current readiness** | ✅ Build script is stable; needs automation wrapper |

---

## Layer 8: Runtime Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | Pre-release, nightly (if disposable CRM available) |
| **Required commands** | API CRUD tests, generate-jobs endpoint test, ACL acceptance, connector sync round-trip |
| **Dependencies** | Running EspoCRM instance (Docker disposable), extension installed, test users provisioned, `ESPOCRM_BASE_URL` + API keys |
| **Expected duration** | 5-10 minutes (including CRM provisioning) |
| **Side-effect risk** | **High** — creates test records with `[CHITU_TEST]` markers; must cleanup |
| **Blocking** | Yes — runtime failures block release |
| **Safe for PRs** | ❌ No — requires dedicated CRM instance + secrets |
| **Requires secrets** | Yes — CRM API keys, CRM URL |
| **Current readiness** | ⚠️ NEEDS T04 (runtime harness) — acceptance script exists but requires manual setup |

---

## Layer 9: Browser Tests

| Attribute | Value |
|-----------|-------|
| **Trigger** | Pre-release, weekly |
| **Required commands** | Playwright-driven UI workflows: Lead detail, SearchStrategy → generate jobs, dashboard tiles, ACL visual enforcement |
| **Dependencies** | Running EspoCRM (Docker disposable), Playwright + browser binaries, test users provisioned |
| **Expected duration** | 10-20 minutes |
| **Side-effect risk** | **High** — creates visible CRM records, screenshots may capture test data |
| **Blocking** | Yes — browser failures block release |
| **Safe for PRs** | ❌ No — requires full CRM + browser environment |
| **Requires secrets** | Yes — CRM credentials, test user passwords |
| **Current readiness** | ❌ NOT IMPLEMENTED — zero browser tests exist (T05 scope) |

---

## Layer 10: Release Gate

| Attribute | Value |
|-----------|-------|
| **Trigger** | Tag push matching version pattern (e.g., `v*`) |
| **Required commands** | All Layer 1-9 must pass. Human sign-off on release notes. |
| **Dependencies** | All lower layers passing, release notes document, changelog entry |
| **Expected duration** | 30-60 minutes (includes human review) |
| **Side-effect risk** | **High** — publishes artifact, creates tag, triggers deployment |
| **Blocking** | N/A — final gate |
| **Safe for PRs** | ❌ No — tag-triggered only |
| **Requires secrets** | Yes — deployment credentials (future) |
| **Current readiness** | ❌ NOT READY — entire release process is manual |

---

## Layer Summary

| Layer | Name | Duration | Side Effects | Secrets | PR Safe | Readiness |
|-------|------|----------|-------------|---------|---------|-----------|
| 1 | Repository Validation | < 5s | None | No | Yes | ✅ Ready |
| 2 | Static Checks | < 30s | None | No | Yes | ✅ Ready |
| 3 | Extension Tests | (merged) | None | No | Yes | ✅ Ready |
| 4 | Connector Tests | < 2min | None | No | Yes | ✅ Ready* |
| 5 | Worker / Contract | (merged) | None | No | Yes | ⚠️ Partial |
| 6 | Package Validation | < 10s | None | No | Yes | ⚠️ Needs impl |
| 7 | Artifact Build | < 30s | Writes files | No | Conditional | ✅ Ready |
| 8 | Runtime Tests | 5-10min | Creates data | Yes | No | ⚠️ Needs T04 |
| 9 | Browser Tests | 10-20min | Creates data | Yes | No | ❌ Needs T05 |
| 10 | Release Gate | 30-60min | Publishes | Yes | No | ❌ Needs T06-T08 |

---

## Gate Behavior per Event Type

| Event | Layers Run | Blocking? |
|-------|-----------|-----------|
| `push` (feature branch) | 1-4 (or 1-2 only for quick feedback) | Yes |
| `pull_request` → main | 1-5 | Yes |
| `push` → main (merge) | 1-6 (build artifact as dry-run) | Yes |
| `schedule` (nightly) | 1-5 + 8 (if CRM available) | Advisory |
| `release` tag | 1-10 | Yes |
