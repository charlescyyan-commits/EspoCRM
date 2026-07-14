# CI Roadmap

**Status:** Phase CI01 Plan — 2026-07-13

> Defines subsequent CI phases (CI02–CI07) for building out the CI/CD pipeline. Each phase has a goal, dependencies, affected files, conflict risk, recommended tools, and acceptance criteria. Phases are designed to be executed sequentially with T02–T08 as prerequisites.

---

## CI02 — Static and Offline Test Workflow

### Goal
Create the first CI workflow: `ci-static.yml` running Layers 1-2 on every push and PR. This is the foundation for all subsequent CI work.

### Scope
- Create `.github/workflows/ci-static.yml`
- Run extension skeleton + SearchStrategy foundation + detail view validation
- Python 3.12 setup on `ubuntu-latest`
- Fast feedback (< 1 minute)
- JUnit XML output (informational)
- Block PR merge on failure

### Dependencies
- **T02 (Unified Test Entrypoints)** — required for clean single-command invocation
- **T03 (Core Regression Gate)** — recommended (skipIf guards, stable test set)

### Files Affected
- `.github/workflows/ci-static.yml` (NEW)
- `docs/ci/CURRENT_STATE.md` (UPDATE)
- `docs/README.md` (UPDATE — CI status)

### Conflict Risk
**SAFE** — purely additive. No existing files modified. No secrets required. Fork PRs safe.

### Recommended Tool
- GitHub Actions
- Python 3.12 (`actions/setup-python`)

### Recommended Model
- Haiku 4.5 (YAML authoring, simple scripting)

### Acceptance Criteria
- [ ] `ci-static.yml` triggers on `push` (all branches) and `pull_request` (→ main)
- [ ] All Layer 1-2 tests pass in CI
- [ ] Total workflow time < 2 minutes (including setup)
- [ ] PR merge blocked on failure
- [ ] Fork PRs run successfully (no secrets needed)

---

## CI03 — Package Build and Artifact Workflow

### Goal
Create `ci-package.yml` and `ci-tests.yml`: build extension ZIP on merge to main, validate structure, and publish as CI artifact.

### Scope
- Create `.github/workflows/ci-tests.yml` (connector unit tests)
- Create `.github/workflows/ci-package.yml` (build + validate)
- Automated ZIP structure validation (Python script)
- SHA-256 generation and validation
- Dry-run build on PRs (artifact not retained)
- Release build on main merges (artifact retained 7 days)

### Dependencies
- **CI02** (static workflow) — required
- **T02** (unified entrypoints) — required
- **T03** (regression gate) — required (skipIf guards for CI safety)

### Files Affected
- `.github/workflows/ci-tests.yml` (NEW)
- `.github/workflows/ci-package.yml` (NEW)
- `scripts/validate_zip.py` or `crm-extension/tests/test_zip_structure.py` (NEW)
- `docs/ci/CURRENT_STATE.md` (UPDATE)

### Conflict Risk
**SAFE** — additive. Build script is stable. ZIP validator is new and independent.

### Recommended Tool
- GitHub Actions
- Python `zipfile` + `hashlib` (stdlib)
- PowerShell (`build_release_package.ps1`) on `windows-latest` runner

### Recommended Model
- Haiku 4.5

### Acceptance Criteria
- [ ] `ci-tests.yml` runs all connector unit tests in CI
- [ ] `ci-package.yml` builds ZIP on main push, validates structure
- [ ] ZIP validation: manifest at root, forward-slash paths, no excluded directories
- [ ] SHA-256 generated and attached as workflow artifact
- [ ] Dry-run builds on PR validate without publishing
- [ ] All workflows pass without secrets

---

## CI04 — Runtime Integration Workflow

### Goal
Create `ci-runtime.yml`: spin up disposable EspoCRM via Docker, install extension, run REST API tests, cleanup.

### Scope
- Create `.github/workflows/ci-runtime.yml`
- Docker Compose or Docker CLI for EspoCRM disposable instance
- Extension install via REST API
- Test user provisioning (migrated from hardcoded PHP scripts to env-var-driven)
- REST API test suite (using T04 runtime harness)
- Automated cleanup (always runs, even on failure)
- Residue check: assert zero `[CHITU_TEST]` records remain

### Dependencies
- **CI03** (package build) — required (needs built artifact)
- **T04** (Runtime Test Harness) — required
- Docker + EspoCRM Docker image
- CI secrets: `ESPOCRM_BASE_URL`, admin API key, test user API keys

### Files Affected
- `.github/workflows/ci-runtime.yml` (NEW)
- `tests/runtime/` (from T04)
- `deployment/provisioning/*.php` (UPDATE — env var migration)
- `.env.example` (NEW)
- `.gitignore` (UPDATE — add `.env`)
- CI secret store (UPDATE — add secrets)

### Conflict Risk
**MEDIUM** — modifies provisioning scripts (env var migration). Must coordinate with any parallel work touching `deployment/provisioning/`.

### Recommended Tool
- GitHub Actions
- Docker (`espocrm/espocrm` image or custom Dockerfile)
- Python `urllib` (stdlib) for REST calls
- T04 runtime harness

### Recommended Model
- Opus 4.8 (infrastructure + security-sensitive)

### Acceptance Criteria
- [ ] Disposable CRM starts, extension installs, tests run, CRM destroyed
- [ ] All Layer 5 tests pass against live CRM
- [ ] Cleanup verified: zero test residue after run
- [ ] Workflow runs nightly + on release tags + manual dispatch
- [ ] Fork PRs do NOT trigger this workflow (secrets gated)
- [ ] Hardcoded credentials removed from provisioning scripts
- [ ] `.env.example` provides template; `.env` is gitignored

---

## CI05 — Browser Acceptance Workflow

### Goal
Create `ci-browser.yml`: run Playwright browser tests against disposable EspoCRM.

### Scope
- Create `.github/workflows/ci-browser.yml`
- Use T05 browser tests (Playwright page objects + test suites)
- Run against same disposable CRM instance from CI04
- Screenshot capture on failure (uploaded as workflow artifact)
- Test video recording (optional, for debugging)

### Dependencies
- **CI04** (runtime workflow) — required (needs functional CRM)
- **T05** (Browser Acceptance Tests) — required
- Playwright + Chromium/Firefox binaries

### Files Affected
- `.github/workflows/ci-browser.yml` (NEW)
- `tests/browser/` (from T05)
- `requirements-browser.txt` (from T05)

### Conflict Risk
**SAFE** — additive. Uses T05 tests. No existing files modified.

### Recommended Tool
- GitHub Actions
- Playwright for Python
- `playwright install --with-deps chromium`

### Recommended Model
- Opus 4.8

### Acceptance Criteria
- [ ] 4 browser test suites run against disposable CRM
- [ ] Screenshots captured on failure
- [ ] Workflow runs weekly + manual dispatch + release tags
- [ ] Test video artifacts cleaned up after 7 days

---

## CI06 — Release Automation

### Goal
Implement `release.yml`: full release pipeline triggered by version tags.

### Scope
- Create `.github/workflows/release.yml`
- Tag-triggered (`v*` pattern)
- Verify all CI gates pass (static, tests, package, runtime, browser)
- Build release artifact
- Generate SHA-256
- Create GitHub Release with artifacts attached
- Publish release notes (from `docs/release/RELEASE_NOTES_<version>.md`)

### Dependencies
- **CI02–CI05** (all CI workflows) — required
- **T06** (Install/Upgrade Tests) — recommended for beta+
- Stable release process documented in `docs/release/`

### Files Affected
- `.github/workflows/release.yml` (NEW)
- `docs/release/RELEASE_PROCESS.md` (UPDATE — reference CI automation)
- `docs/ci/RELEASE_AUTOMATION_DESIGN.md` (UPDATE — reflect implementation)

### Conflict Risk
**SAFE** — additive. Uses existing build artifacts. Does not modify source.

### Recommended Tool
- GitHub Actions
- `softprops/action-gh-release` for GitHub Release creation

### Recommended Model
- Haiku 4.5

### Acceptance Criteria
- [ ] Pushing `v<version>` tag triggers release workflow
- [ ] All gates pass → release ZIP + SHA-256 published to GitHub Releases
- [ ] Release notes attached to release body
- [ ] Failed gate blocks release (no partial artifacts published)
- [ ] Previous release artifacts preserved (not overwritten)

---

## CI07 — Deployment Gate (Future)

### Goal
Create a deployment gate for production or staging CRM environments.

### Scope
- Define deployment approval workflow
- Integration with CRM hosting platform (if applicable)
- Smoke tests post-deployment
- Automatic rollback on smoke test failure

### Dependencies
- **CI06** (Release Automation) — required
- Production/staging CRM environment
- Deployment credentials (strictly access-controlled)

### Files Affected
- `.github/workflows/deploy.yml` (NEW)
- `docs/deployment/` (UPDATE)

### Conflict Risk
**HIGH** — touches production. Requires explicit approval per workspace rules.

### Recommended Model
- Opus 4.8

### Acceptance Criteria
- [ ] Defined but not necessarily implemented
- [ ] Deployment requires manual approval gate
- [ ] Smoke tests run post-deployment
- [ ] Rollback procedure tested and documented

---

## Phase Sequencing

```
T02 (entrypoints) ──► T03 (regression) ──► T04 (runtime harness)
                                                  │
CI02 (static CI) ────► CI03 (package CI) ────────► CI04 (runtime CI)
                                                                   │
                                          T05 (browser) ──────────► CI05 (browser CI)
                                          T06 (install/upgrade)
                                                                   │
                                                                   ▼
                                                              CI06 (release)
                                                                   │
                                                                   ▼
                                                              CI07 (deploy)
```

---

## Dependency Matrix

| CI Phase | T Phase Prereqs | Creates | Can Start |
|----------|----------------|---------|-----------|
| CI02 | T02, T03 | `ci-static.yml` | After T02+T03 |
| CI03 | CI02, T02, T03 | `ci-tests.yml`, `ci-package.yml` | After CI02 |
| CI04 | CI03, T04 | `ci-runtime.yml` | After T04 |
| CI05 | CI04, T05 | `ci-browser.yml` | After T05 |
| CI06 | CI02–CI05, T06 | `release.yml` | After CI05 |
| CI07 | CI06 | `deploy.yml` | Future (not scheduled) |

---

## Parallel Conflict Analysis

### SAFE NOW

| Work | Rationale |
|------|-----------|
| CI02 design (static workflow) | No code changes. No secrets. No CRM. |
| CI03 design (package workflow) | Build script stable. ZIP validator is new code. |
| Secret scanning setup (`detect-secrets`) | Additive; does not modify source. |

### WAIT FOR T02

| Work | Rationale |
|------|-----------|
| CI02 implementation | Needs unified test entrypoints for clean CI invocation |
| CI03 implementation (`ci-tests.yml`) | Needs T02 entrypoint + T03 skipIf guards |

### WAIT FOR T04

| Work | Rationale |
|------|-----------|
| CI04 implementation | Needs runtime harness + Docker CRM setup |
| Provisioning script env var migration | Must coordinate with T04 test data management |

### WAIT FOR T05

| Work | Rationale |
|------|-----------|
| CI05 implementation | Needs browser tests + page objects |

### WAIT FOR RELEASE POLICY

| Work | Rationale |
|------|-----------|
| CI06 implementation | Needs stable release process + runtime verification |
| CI07 (deployment gate) | Requires production approval |
