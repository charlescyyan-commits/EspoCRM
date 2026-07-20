# Phase3S02 Architecture Readiness Review

**Date:** 2026-07-20
**Review type:** Read-only Architecture Analysis
**Current baseline:** `v1.9.6-alpha` (Phase3S01 Freeze)
**Phase under review:** Phase3S02 (not yet started)
**Reviewer:** Claude Code (DeepSeek V4 Pro)

---

## Executive Summary

The EspoCRM Production workspace is in **healthy structural condition** following the Phase3S01 freeze. The deterministic Python builder, contract validation, extension skeleton tests, connector unit tests, and documentation center form a solid foundation. The project is **READY FOR S02 PLANNING**.

The primary finding is that S02 should focus on **engineering consolidation, not business-feature expansion**. The test system roadmap (T02–T08) is well-designed but entirely unexecuted. Release governance is documented but fully manual. Documentation has accumulated version-staleness across 286 files. The Python connector has 30+ well-structured modules that lack a unified package definition (`pyproject.toml`). The CRM extension has a legacy `custom/` directory alongside the canonical `files/` tree.

**S02 should be a stabilization sprint**: unify test entrypoints, harden the regression gate, eliminate documentation staleness, clean up the legacy extension directory dualism, and formalize the freeze gate automation — before C16 (Quotation / PI) introduces new complexity.

---

## 1. Current Engineering Structure

### Assessment: STRONG

The workspace follows a clean four-module architecture:

| Module | Role | Status |
|--------|------|--------|
| `crm-extension/` | Installable EspoCRM Prospecting module | **Clean** — well-structured metadata, clear entity ownership |
| `chitu-connector/` | Python sync + acquisition connector | **Clean** — strong module boundaries, explicit exports |
| `deployment/` | Versioned ZIPs + provisioning + validation | **Clean** — only current artifact + SHA-256 sidecar |
| `docs/` | Documentation center + phase reports | **Adequate** — 286 files, organized but with staleness |
| `scripts/` | Operational + testing scripts | **Adequate** — functional but fragmented |
| `archive/` | Runtime backups | **Not reviewed** — operational artifact storage |

### Strengths

1. **Clear module boundaries.** The extension never imports Python; the connector never writes PHP/SQL. This is enforced by tests (`test_core_espocrm_untouched`, `test_prospecting_engine_untouched_by_extension_tree`).

2. **Single version authority.** `crm-extension/manifest.json` is the sole source of truth for `version`, `releaseDate`, and platform compatibility (`>=7.4.0`, `>=8.1`).

3. **Deterministic build.** The Python builder (`crm-extension/scripts/build_release_package.py`) is CWD-independent, produces reproducible ZIPs with deterministic timestamps, normalizes line endings, and performs deep byte-level parity checks. The PowerShell builder is retained for Windows compatibility with cross-builder parity verification.

4. **Vendored contracts isolation.** `chitu-connector/vendored/` contains only stable interface copies. The connector must not import Chitu application trees — this is enforced by code reviews and phase audits.

### Issues Found

#### MEDIUM: Legacy `custom/` directory alongside canonical `files/` tree

The CRM extension root contains both:
- `crm-extension/custom/Espo/Modules/Prospecting/` — legacy placeholder directory with README.md files
- `crm-extension/files/custom/Espo/Modules/Prospecting/` — canonical installable package root

The `custom/` directory at the extension root has no purpose beyond placeholder READMEs. Its existence alongside the canonical `files/` tree creates confusion about which path is authoritative. The extension skeleton tests reference `MODULE` as `files/custom/Espo/Modules/Prospecting`, confirming `files/` is canonical.

**Recommendation:** S02 should either remove `custom/` or clearly document it as a legacy artifact with a deprecation banner. Test assertions should explicitly verify that no PHP logic lives under the legacy path.

#### LOW: `Resources/` directory duplicated between extension root and module

`crm-extension/Resources/` (surface design mirror) and `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/` (module metadata) contain duplicated entityDefs, layouts, and ACL definitions. Parity is enforced by tests (`test_surface_and_module_entity_defs_match`), but the duplication is mechanical — any entity change requires editing two locations.

**Recommendation:** S02 could add a script that generates the surface mirror from the module metadata, or document the rationale for the dual structure more explicitly in the extension docs.

#### LOW: `deployment/` directory holds only one artifact

Currently `deployment/` contains only `prospecting-extension-1.9.6-alpha.zip` and its SHA-256 sidecar. Previous releases are referenced by checksum in `docs/PHASE3B_FINAL_SUMMARY.md` but their ZIPs are not retained in the repository.

**Recommendation:** Document the artifact retention policy. If previous ZIPs are stored externally, note where. If they are intentionally discarded, state that explicitly.

---

## 2. Test System

### Assessment: ADEQUATE (Layer 1–2 strong; Layer 3+ needs execution)

### Layer Coverage Status

| Layer | Status | Test Count | Blocking Gaps |
|-------|--------|------------|---------------|
| 1. Static Validation | **Strong** | ~30 methods (3 files) | JSON schema validation against EspoCRM entityDefs schema not automated |
| 2. Unit Tests | **Strong** | ~86 methods (11 files) | SearchStrategyTemplates logic not unit-tested in isolation |
| 3. Contract Tests | **Partial** | ~22 methods | ACL contract, REST API contract not validated offline |
| 4. Integration Tests | **Partial** | Mocked only | No disposable CRM test harness |
| 5. Runtime REST | **Partial** | 1 script (TBD) | No automated CRM provisioning; requires manual setup |
| 6. Browser Acceptance | **Not Implemented** | 0 | All UI verification is manual |
| 7. Packaging/Install | **Not Implemented** | 0 | ZIP validation is manual-only |
| 8. Upgrade/Rollback | **Not Implemented** | 0 | No automated upgrade-path testing |
| 9. Performance | **Not Implemented** | 0 | No baselines exist |
| 10. Security/Residue | **Partial** | Manual only | No automated secret scanning |

### Test Entry Point Fragmentation

Tests are runnable but fragmented across multiple entry points:

| Entry point | Scope |
|-------------|-------|
| `python -m unittest crm-extension.tests.test_extension_skeleton -v` | Extension skeleton |
| `python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v` | Connector tests |
| `python -m unittest tests.regression.test_phase3s01_release_integrity` | S01 release integrity |
| `powershell scripts/testing/run-regression-gate.ps1` | Full gate (delegates) |
| `powershell scripts/testing/run-freeze-gate.ps1` | Freeze gate (delegates) |
| `powershell scripts/testing/run-runtime-tests.ps1` | Runtime tests |

There is **no single command** that runs all offline tests from the repository root.

### Test Infrastructure Maturity

The `docs/testing/TEST_SYSTEM_ROADMAP.md` defines a clear T02–T08 roadmap with well-scoped phases, dependency analysis, and conflict risk assessment with Phase3C. **None of T02–T08 have been executed.** The roadmap is a design artifact, not implemented infrastructure.

### Issues Found

#### HIGH: No unified test entrypoint

Every test run requires remembering which directory, which discovery pattern, and which Python path setup to use. The test layer model (10 layers) has no corresponding unified runner. `docs/testing/TEST_SYSTEM_ROADMAP.md` T02 (Unified Test Entrypoints) is fully planned but not implemented.

**Impact:** New contributors and automated CI integration face unnecessary friction. Regression risk increases when tests are easy to skip.

**Recommendation:** S02.1 should prioritize T02 execution.

#### MEDIUM: Test discovery depends on implicit PYTHONPATH

Connector tests require `chitu-connector/` on `PYTHONPATH`. Extension tests require `crm-extension/` as a package. There is no `.python-version`, `pyproject.toml`, or `setup.py` to encode these requirements.

**Recommendation:** Add a minimal `pyproject.toml` at repo root that configures `PYTHONPATH` for both packages.

#### MEDIUM: Live test guards are inconsistent

`test_espocrm_real_client.py` references `ESPOCRM_TEST_ENV` but the guard behavior is not uniformly applied across all runtime-dependent tests. The T02 roadmap item to add `@unittest.skipIf` is planned but not done.

#### LOW: Regression gate map references unimplemented suites

`scripts/testing/regression-gate-map.json` defines 4 conditional suites (`Browser acceptance`, `Runtime REST adapter`, `Runtime worker execution`, `Package lifecycle`) all with status `NOT_IMPLEMENTED`. The gate correctly treats them as non-blocking, but their presence in the map creates a permanent "TODO" noise.

**Recommendation:** Either implement or remove conditional suite declarations that have no target date.

---

## 3. Release Engineering

### Assessment: ADEQUATE (S01 foundation solid; automation missing)

### S01 Freeze Achievements

The Phase3S01 freeze delivered:
- Deterministic, CWD-independent Python builder (`build_release_package.py`)
- Deep artifact/source parity check (`--check` mode)
- SHA-256 sidecar generation and verification
- Cross-builder parity verification (Python ↔ PowerShell)
- Release integrity regression tests (`tests/regression/test_phase3s01_release_integrity`)
- Deterministic ZIP timestamps anchored to `manifest.json` `releaseDate`

### Remaining Engineering Debt

#### HIGH: Release process is fully manual

The current release workflow requires:
1. Manual `manifest.json` edit (version + releaseDate)
2. Manual `test_extension_skeleton.py` version constant update
3. Manual build command invocation
4. Manual SHA-256 verification
5. Manual release notes creation
6. Manual git tag creation (or none at all — the process says "manual, out of band")

There is no single `make release` or scripted release command. Tag creation is "recommended but not automatically created."

**Impact:** Every release is a human-error-prone procedure. The S01 release integrity tests protect against bad artifacts but don't prevent procedural mistakes (e.g., forgetting to update the skeleton test version constant).

**Recommendation:** S02 should create a `scripts/release/cut-release.sh` (or `.ps1`) that executes steps 1–6 in sequence with pre-flight checks.

#### MEDIUM: `test_extension_skeleton.py` version constant is a sync risk

Line 17 hardcodes `RELEASE_VERSION = "1.9.6-alpha"`. If `manifest.json` is bumped but this constant is forgotten, the skeleton test will fail — which is the desired behavior, but the process relies on human memory to update both. A release script would eliminate this risk.

#### MEDIUM: Historical commit message risk documented but unresolved

`docs/release/RELEASE_NOTES_1.9.6-alpha.md` explicitly documents that the historical baseline commit `fd671e5` has the non-descriptive message `111`, calling it "a governance risk." This is recorded but not addressed. Any history rewrite requires owner decision, but the risk report has no associated mitigation (e.g., an annotated tag with a descriptive message on that commit).

#### LOW: `deployment/` directory lacks version retention policy

The directory contains only the current artifact. Historical ZIPs referenced in `PHASE3B_FINAL_SUMMARY.md` (1.6.0 through 1.7.1) are not present. It's unclear whether they are stored externally or were intentionally not retained.

#### LOW: PowerShell builder parity check is Windows-gated

The README states the PowerShell builder's package content "is checked against the Python builder when PowerShell is installed." This means the parity check is skipped on non-Windows platforms. The Python builder is the canonical one; this is acceptable but should be documented as a limitation.

---

## 4. Python Connector

### Assessment: STRONG

### Module Structure

The `chitu-connector` package is well-organized with clear separation:

| Package | Files | Responsibility |
|---------|-------|----------------|
| `espocrm_sync/` | ~30 modules | Contract validation, CRM HTTP client, sync gate, lifecycle, feedback, email, scoring, send path, draft store, queue, worker execution, reply tracking |
| `acquisition/` | ~10 modules | Worker core, fake provider, models, normalization, EspoCRM repository, runner, providers (Apify, Serper), master prospect, website research, evidence extraction |
| `vendored/` | ~8 modules | Stable copied contracts only (ICP, scoring, search, entity identity, etc.) |

### Strengths

1. **Explicit public API.** `espocrm_sync/__init__.py` exports ~200 symbols in an explicit `__all__` list. No wildcard re-exports. Every public name is intentional.

2. **Strong typing.** All modules use `from __future__ import annotations`, dataclasses with `frozen=True` and `slots=True`, and clear type hints. Contract validation returns typed error tuples.

3. **Clean DTO layer.** `espocrm_sync/models.py` defines `AdapterResult`, `AuditStatus`, `GateDecision`, `MockSyncStatus`, `SyncSource` as frozen dataclasses. `acquisition/models.py` defines `ClaimResult`, `JobExecutionResult`, `NormalizedCandidate`, etc.

4. **Injectable dependencies.** Worker uses protocol-style `AcquisitionStore` and provider interfaces. Fake/Mock implementations exist for all major components (`MockEspoCRMClient`, `DeterministicFakeProvider`, `FakeProviderAdapter`, `InMemoryDraftStore`, `InMemorySendExecutionQueue`, etc.).

5. **Fail-closed gate.** `gate.py` evaluates 13 conditions before allowing sync, defaulting to `GateDecision(False, reason)` on any failure.

6. **Contract validation is thorough.** `contract.py` validates 11 top-level sections, 8+ string fields, 8+ evidence items with format checks (URL, datetime, domain, enum, range).

### Issues Found

#### MEDIUM: No `pyproject.toml` or package definition

The connector has no `pyproject.toml`, `setup.py`, or `setup.cfg`. It relies entirely on implicit `PYTHONPATH` manipulation. There is no declared Python version requirement, no dependency list (stdlib-only is the claim but not verified by a build system), and no package metadata.

**Impact:** Cannot be installed via `pip install -e .` for development. CI/CD integration requires manual `PYTHONPATH` setup. Linting/type-checking tools have no configuration anchor.

**Recommendation:** S02 should add a minimal `pyproject.toml` for both the repo root and `chitu-connector/`.

#### MEDIUM: `acquisition/providers/` partially implemented

`apify_provider.py` and `serper_provider.py` exist but their runtime readiness is unclear. The provider contract is well-defined (`acquisition/provider.py` protocol), but `DeterministicFakeProvider` is the only fully tested path. Real providers may have undocumented API key requirements, rate limit behaviors, or response format assumptions.

**Recommendation:** S02 should audit provider implementations for completeness (error handling, rate limiting, API key configuration) and add provider-specific integration tests gated behind environment variables.

#### LOW: Logging is ad-hoc

The connector modules use `print()` or rely on exception propagation for diagnostics. There is no structured logging framework (`logging` module, log levels, contextual metadata). For a library that will eventually run in production pipelines, this is a gap.

**Recommendation:** S02 should add a `logging`-based diagnostics module with configurable levels and structured context (sync job ID, lead ID, provider name).

#### LOW: Exception hierarchy is flat

Exceptions like `ProviderError`, `ProviderRateLimitError`, `PersistenceError`, `GateError`, `ConnectorApiError`, `FeedbackApiError` are defined locally in each module. They don't share a common base exception for the connector package, making it hard to catch "any connector error" vs "unexpected runtime error."

**Recommendation:** Define a `ChituConnectorError` base class and have all connector exceptions inherit from it.

#### LOW: Config is environment-variable-only

Configuration is read directly from `os.environ` (e.g., `ESPOCRM_BASE_URL`, `ESPOCRM_API_KEY`). There is no config object, no validation at import time, and no support for config files.

**Recommendation:** Add a `ConnectorConfig` dataclass with environment-variable parsing, validation, and explicit defaults.

---

## 5. EspoCRM Extension

### Assessment: STRONG

### Structure

The extension follows EspoCRM's standard module layout:

| Path | Content | Status |
|------|---------|--------|
| `files/custom/Espo/Modules/Prospecting/Entities/` | 9 entity PHP shells | Clean |
| `files/custom/Espo/Modules/Prospecting/Controllers/` | 9 controller PHP shells | Clean |
| `files/custom/Espo/Modules/Prospecting/Services/` | 11 service classes | Substantial logic |
| `files/custom/Espo/Modules/Prospecting/Api/` | 6 API endpoint classes | Clean |
| `files/custom/Espo/Modules/Prospecting/Classes/Select/` | 31 primary filter classes | Well-organized |
| `files/custom/Espo/Modules/Prospecting/Resources/` | Metadata, layouts, i18n, routes | Comprehensive |
| `files/custom/Espo/Custom/Hooks/` | 5 hook classes | Clean separation |

### Strengths

1. **Comprehensive static validation.** `test_extension_skeleton.py` has 26 test methods covering manifest, directory structure, entity fields, layouts, routes, formulas, hooks, ACL provisioning, filter inventory, and surface/module parity. The test invokes PHP source reading to verify business logic constraints (e.g., no `getEntity('Opportunity')` in `ChituSyncService`).

2. **Explicit filter inventory.** The test asserts an exact, enumerated set of PHP files. No unexpected PHP files can be added without test failure.

3. **Clean entity ownership.** Each Prospecting entity has the standard quartet: `Entities/X.php`, `Controllers/X.php`, entityDefs JSON, and optionally `Services/XService.php`. No orphaned files.

4. **Formula + hook separation.** Business rules are split appropriately: stateless transitions in `formula/Lead.json` (before-save), side-effect generation in `LeadWorkflowHook.php` (after-save → Task creation).

5. **Boundary enforcement.** `ChituSyncService` explicitly sets `NO_AUTOMATIC_OPPORTUNITY`. Email body fields (`peEmailSubject`, `peEmailBody`) are explicitly absent.

6. **Layout ownership.** `app/layouts.json` declares Prospecting module ownership for Lead detail/list, preventing Crm core layout fallback.

### Issues Found

#### MEDIUM: `custom/` directory at extension root is vestigial

The extension root has `crm-extension/custom/Espo/Modules/Prospecting/` with placeholder READMEs in `Controllers/`, `Services/`, `Api/`. This directory is not the installable package root (`files/` is). It exists only to satisfy a historical convention.

**Recommendation:** S02 should remove the legacy `custom/` directory and update any references. If it must be retained for backward compatibility, add a `DEPRECATED.md` explaining its status.

#### LOW: Entity/Controller PHP shells are nearly empty

Most entity PHP files (e.g., `ResearchEvidence.php`, `SearchJob.php`) contain only a class declaration extending the EspoCRM base class. These are EspoCRM-required boilerplate. A code generation script could reduce manual maintenance.

**Recommendation:** Consider a code-gen approach in a future phase. Not urgent for S02.

#### LOW: 31 primary filter classes follow a repetitive pattern

Each `Pe*.php` filter follows an identical pattern (apply a WHERE clause to a query builder). The filters are well-tested but mechanically repetitive. Template or base-class extraction could reduce the class count by ~60%.

**Recommendation:** Low priority. The current structure is clear and testable. Refactoring should wait until the filter inventory stabilizes.

#### LOW: `Resources/` split (surface vs module) creates dual maintenance

Every entityDefs change requires editing both `crm-extension/Resources/entityDefs/X.json` and `crm-extension/files/.../Resources/metadata/entityDefs/X.json`. Parity is test-enforced but still manual.

**Recommendation:** S02 could add a `--sync-resources` flag to the build script that copies `files/.../Resources/` to `Resources/` before the parity check, making the surface mirror a build artifact rather than a co-edited source.

---

## 6. Documentation

### Assessment: ADEQUATE (comprehensive but accumulating staleness)

### Documentation Inventory

Approximately 286 markdown files in `docs/` organized into:

| Category | Location | Files | Status |
|----------|----------|-------|--------|
| Architecture | `docs/architecture/` | 9 | Up-to-date (post-D01) |
| API/Contracts | `docs/api/`, `docs/sync-contracts/` | ~8 | Current for V1 |
| Deployment | `docs/deployment/` | 5 | Current |
| Developer Guide | `docs/developer/` | 5 | Current (post-D01) |
| User Guide | `docs/user-guide/` | 5 | Adequate |
| Testing | `docs/testing/` | ~10 | Mixed — roadmap is design-only |
| Release | `docs/release/` | 7 | Current for 1.9.6-alpha |
| Phase Reports | `docs/phase-reports/` | ~50 | Historical (correctly frozen) |
| Root-level reports | `docs/PHASE3*` | ~30 | Mixed ages |
| Email Rules | `docs/email-rules/` | 7 | Reference (no code) |
| Workflow | `docs/workflow/` | 3 | Reference |
| CI | `docs/ci/` | 3 | Design-only |
| Other (ADR, Diagrams) | `docs/adr/`, `docs/diagrams/` | 2 | Skeleton |

### Issues Found

#### HIGH: Version staleness across documentation

The `docs/README.md` "Current System Status" table references `1.9.5-alpha` while the actual release is `1.9.6-alpha`. The `docs/architecture/SYSTEM_OVERVIEW.md` and `docs/architecture/MODULES.md` also reference `1.9.5-alpha`. This is a systemic issue — the Documentation Center was frozen at D01 (pre-S01) and the S01 version bump did not propagate to all active documentation.

**Impact:** Readers consulting docs/README.md for current status get stale information. The "Current packaged release" and "Latest packaged artifact" fields are wrong.

**Recommendation:** S02 should include a documentation staleness audit. Update all "Current System Status" tables, architecture docs, and module docs to reflect `1.9.6-alpha`. Consider adding a CI check that compares `manifest.json` version against `docs/README.md` declared version.

#### MEDIUM: Phase reports accumulate without lifecycle management

~80 phase reports exist across `docs/phase-reports/` and `docs/` root. The policy correctly states "historical phase reports are not moved or renamed." However, there is no mechanism to distinguish "actively referenced" from "purely archival" reports. The `docs/reports/README.md` index is referenced but its completeness is unverified.

**Recommendation:** Add frontmatter or a `status` field to phase reports indicating `active-reference` vs `archival`. Ensure the reports index is complete.

#### MEDIUM: Release notes location is inconsistent

- `docs/release/RELEASE_NOTES_1.9.6-alpha.md` — correct location
- `docs/RELEASE_NOTES_1.7.1-alpha.md` — historical (root level)
- `docs/PHASE3B_FINAL_SUMMARY.md` — contains release artifact checksums, making it a hybrid phase-report/release-note

**Recommendation:** Move `docs/RELEASE_NOTES_1.7.1-alpha.md` to `docs/release/`. Extract checksum records to a dedicated `docs/release/CHECKSUMS.md`.

#### LOW: `docs/README.md` maintenance policy (section 10) is clear but not enforced

The per-phase documentation update rules are well-specified but rely on human discipline. A CI lint rule that checks "if manifest.json version changed, docs/README.md must also change" would catch this mechanically.

#### LOW: ADR directory is nearly empty

`docs/adr/README.md` exists but contains no actual Architecture Decision Records. The ADR template is not documented.

---

## 7. Release Governance

### Assessment: ADEQUATE (process defined; automation absent)

### Current Governance Model

1. **Freeze gate:** `scripts/testing/run-freeze-gate.ps1` → delegates to `run-regression-gate.ps1` → runs Extension + Connector + Worker + Static + Runtime + Baseline + Runner integrity suites
2. **Regression gate map:** `scripts/testing/regression-gate-map.json` defines 8 required suites with area-specific triggering rules
3. **Release process:** 8-step manual procedure in `docs/release/RELEASE_PROCESS.md`
4. **Version policy:** `docs/release/VERSION_POLICY.md` defines semver + prerelease tags (`alpha` only; `beta`/`rc` reserved)
5. **Changelog policy:** `docs/release/CHANGELOG_POLICY.md` distinguishes user-visible release notes from engineering phase reports
6. **Runtime gate:** `scripts/runtime/runtime_gate.py` performs read-only (GET-only) CRM validation

### Issues Found

#### MEDIUM: Freeze gate is PowerShell-only

The freeze gate is a PowerShell script that delegates to another PowerShell script. It cannot run on Linux/macOS without PowerShell Core. The Python builder is cross-platform; the gate should be too.

**Recommendation:** S02 should create a Python equivalent of the freeze gate that wraps the same test suites.

#### MEDIUM: Git tag creation is "manual, out of band"

The release process explicitly states tags are recommended but not automatically created. `v1.9.6-alpha` exists as a tag per `git tag` output, but the process to create it is not scripted. The tag message, signing, and push are all ad-hoc.

**Recommendation:** A release script should optionally create and push an annotated tag with the release notes summary as the message body.

#### LOW: No release approval gate

The release process has no explicit approval step between "build ZIP" and "tag commit." The freeze gate is technical, not procedural. For alpha releases this is acceptable; for beta/rc, an approval gate should be designed.

#### LOW: No artifact signing beyond SHA-256

The SHA-256 sidecar provides integrity but not authenticity. GPG signing of the sidecar or the ZIP itself is not mentioned.

**Recommendation:** For beta releases, add GPG signing. Document the signing key policy.

#### LOW: Rollback materials are referenced but not validated

`docs/deployment/ROLLBACK.md` exists but references "previous ZIP + SQL backup references." The release process step 8 says "Keep previous ZIP + SQL backup references" but provides no automation or verification. Previous ZIPs are not in the repository.

---

## 8. Future C16 Readiness

### Assessment: ADEQUATE (foundation exists; significant new work needed)

### What C16 (Quotation / PI) Would Require

Based on the domain analysis, C16 would introduce:

| Capability | What exists | What's needed |
|------------|-------------|---------------|
| **Quote entity** | No entity, no metadata | New CRM entity + entityDefs + layouts + ACL + API routes |
| **PI (Proforma Invoice)** | No entity, no metadata | New CRM entity + entityDefs + layouts + ACL + API routes |
| **Approval workflow** | `DraftApproval` entity exists (email draft approval) | New approval entity or extension of existing for Quote/PI |
| **PDF generation** | Nothing | PDF templating engine integration (outside CRM? inside?) |
| **Quote→Opportunity link** | Opportunity has `pe*` fields | Quote entity needs link to Opportunity and Lead |
| **PI→Quote link** | Nothing | PI entity needs link to Quote |
| **CRM integration** | `ChituSyncService` handles Lead/Evidence/Opportunity sync | New sync endpoints for Quote/PI data |

### Architectural Readiness Assessment

**What the current architecture handles well:**
- The sync contract V1 already has `recommendation` (product, cross-sell), `score`, and `qualification` sections that could feed Quote generation
- The gate framework (`evaluate_sync_gate`) is extensible — new gate conditions for Quote eligibility can be added
- The connector module pattern (contract → mapper → client → gate) is proven and repeatable for new entities
- The extension entity pattern (entityDefs + scope + clientDefs + ACL + layouts + i18n) is well-established
- Lead fields like `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalEligibility` already model proposal data

**What the current architecture does NOT yet support:**
- **PDF generation pipeline.** No templating engine, no rendering service, no binary storage strategy. This is the biggest architectural unknown.
- **Quote calculation logic.** Pricing, discount, tax, currency handling — none of this exists anywhere in the codebase.
- **PI numbering/sequencing.** Legal/accounting requirements for invoice numbering are not modeled.
- **Multi-entity workflow.** Quote → PI → Opportunity is a state machine that spans 3+ CRM entities. The current workflow hooks are single-entity.
- **Approval chains.** `DraftApproval` exists for email drafts but is a single-approver model. Quote approval may require multi-level chains.

### Verdict on C16 Readiness

The architecture is **structurally capable of absorbing C16** but the new work is substantial. S02 should focus on:
1. **Designing the Quote/PI entity model** (ADR-level, not implementation)
2. **Assessing PDF generation options** (EspoCRM PDF engine? External service? Client-side?)
3. **Defining the Quote→Opportunity transition rules** (when does a Quote become an Opportunity?)

These design activities can proceed in parallel with S02 engineering consolidation without blocking either track.

---

## 9. Recommended S02 Breakdown

### S02.1 — Test System Unification

**Goal:** Make all offline tests runnable with a single command from repo root.

**In scope:**
- Execute T02: Create `run_all_tests.py` or unified entrypoint
- Standardize PYTHONPATH handling
- Add `--layer` filter (static, unit, contract, all)
- Add `.python-version` or document Python requirement
- Update `docs/developer/TESTING.md`

**Out of scope:**
- Writing new tests (T03)
- Runtime test harness (T04)
- Browser tests (T05)
- CI configuration (T08)

**Recommended tool:** Python `unittest` discovery
**Estimated difficulty:** Low (2–4 hours)
**Parallelizable:** Yes — independent of all other S02 work
**Exit criteria:**
- `python run_all_tests.py` passes all offline tests
- `--layer static` runs only extension skeleton + foundation tests
- Exit code 0 on pass, non-zero on failure
- PYTHONPATH automatically configured

---

### S02.2 — Documentation Staleness Correction

**Goal:** Align all active documentation with the `1.9.6-alpha` release baseline.

**In scope:**
- Update `docs/README.md` System Status table (1.9.5 → 1.9.6)
- Update `docs/architecture/SYSTEM_OVERVIEW.md` version references
- Update `docs/architecture/MODULES.md` version references
- Move `docs/RELEASE_NOTES_1.7.1-alpha.md` to `docs/release/`
- Verify `docs/reports/README.md` completeness
- Add version-staleness check to documentation policy

**Out of scope:**
- Rewriting historical phase reports
- Creating new architecture documents
- Modifying email-rules, workflow, or CI design docs

**Recommended tool:** Manual review + search for "1.9.5"
**Estimated difficulty:** Low (2–3 hours)
**Parallelizable:** Yes — independent of code changes
**Exit criteria:**
- `grep -r "1.9.5-alpha" docs/` returns only valid historical references
- `docs/README.md` System Status matches `manifest.json`

---

### S02.3 — Release Engineering Automation

**Goal:** Create a single-command release workflow.

**In scope:**
- Create `scripts/release/cut-release.ps1` (or `.py`) — interactive release script
- Automate: version bump → test → build → checksum → verify → tag
- Add pre-flight checks (clean working tree, all tests pass, manifest valid)
- Add git tag creation with release notes summary as message
- Create Python freeze gate wrapper for cross-platform support
- Document rollback artifact retention policy

**Out of scope:**
- CI/CD pipeline integration (T08)
- GPG signing (defer to beta)
- Automated changelog generation from commits
- Deployment to live CRM

**Recommended tool:** Python (cross-platform) + PowerShell (Windows-native)
**Estimated difficulty:** Medium (4–6 hours)
**Parallelizable:** Can start after S02.1 (depends on unified tests)
**Exit criteria:**
- `python scripts/release/cut-release.py --dry-run` validates all pre-flights
- Release script bumps version in both `manifest.json` and `test_extension_skeleton.py`
- Git tag is created with annotated message
- Freeze gate runs from Python on any platform

---

### S02.4 — Extension Directory Cleanup

**Goal:** Eliminate the legacy `custom/` directory; document the `Resources/` dualism.

**In scope:**
- Remove or deprecate `crm-extension/custom/`
- Update extension skeleton tests if directory assertions change
- Add `Resources/` mirroring rationale to `crm-extension/Resources/README.md`
- Optionally: add `--sync-resources` to build script (low priority)

**Out of scope:**
- Refactoring PHP entity shells
- Consolidating primary filter classes
- Changing the module structure

**Recommended tool:** Manual cleanup + test update
**Estimated difficulty:** Low (1–2 hours)
**Parallelizable:** Yes — independent
**Exit criteria:**
- `crm-extension/custom/` is removed or contains a `DEPRECATED.md`
- All extension skeleton tests pass
- `Resources/` README explains the dual-structure rationale

---

### S02.5 — Connector Package Foundation

**Goal:** Add `pyproject.toml` and minimal package infrastructure.

**In scope:**
- Add `pyproject.toml` to repo root with test configuration
- Add `pyproject.toml` to `chitu-connector/` with package metadata
- Define Python version requirement (≥3.10 based on `from __future__ import annotations` + `slots=True`)
- Add `ConnectorConfig` dataclass for environment-variable parsing
- Add `ChituConnectorError` base exception class
- Add `logging`-based diagnostics module

**Out of scope:**
- Converting to full `pip install` package
- Adding external dependencies
- Restructuring module layout

**Recommended tool:** Python `toml` + stdlib `logging`
**Estimated difficulty:** Medium (3–5 hours)
**Parallelizable:** Yes — independent of extension work
**Exit criteria:**
- `pip install -e chitu-connector/` works in development mode
- `python -m unittest discover` works from any directory
- All existing tests pass under the new package configuration
- `ConnectorConfig` validates environment variables at init time
- All connector exceptions inherit from `ChituConnectorError`

---

### S02.6 — C16 Architecture Design (ADR)

**Goal:** Produce Architecture Decision Records for Quote/PI/Approval/PDF without implementation.

**In scope:**
- ADR: Quote entity model and relationship to Lead/Opportunity
- ADR: PI entity model and relationship to Quote
- ADR: PDF generation strategy (EspoCRM engine vs external service)
- ADR: Approval workflow for Quote/PI
- ADR: Sync contract V2 considerations for Quote/PI data

**Out of scope:**
- Implementing any C16 entities
- Writing C16 code
- Modifying existing entities

**Recommended tool:** Markdown ADRs in `docs/adr/`
**Estimated difficulty:** Medium (design only, 4–6 hours)
**Parallelizable:** Yes — can run in parallel with all S02 consolidation work
**Exit criteria:**
- 4–5 ADRs in `docs/adr/` with clear status (Proposed / Accepted / Deprecated)
- Each ADR identifies what current architecture supports vs what needs building
- PDF strategy ADR includes feasibility assessment of at least 2 options

---

## 10. Risk Matrix

| # | Finding | Severity | Domain | Recommended Phase |
|---|---------|----------|--------|-------------------|
| H1 | No unified test entrypoint | **HIGH** | Testing | S02.1 |
| H2 | Release process is fully manual | **HIGH** | Release Engineering | S02.3 |
| H3 | Documentation version staleness (1.9.5 vs 1.9.6) | **HIGH** | Documentation | S02.2 |
| M1 | Legacy `custom/` directory alongside canonical `files/` | **MEDIUM** | Extension | S02.4 |
| M2 | No `pyproject.toml` or package definition | **MEDIUM** | Connector | S02.5 |
| M3 | Test discovery depends on implicit PYTHONPATH | **MEDIUM** | Testing | S02.1 |
| M4 | Live test guards are inconsistent | **MEDIUM** | Testing | S02.1 (T02) |
| M5 | `test_extension_skeleton.py` version constant sync risk | **MEDIUM** | Release Engineering | S02.3 |
| M6 | Historical commit message risk unresolved | **MEDIUM** | Release Governance | S02.3 |
| M7 | Freeze gate is PowerShell-only | **MEDIUM** | Release Governance | S02.3 |
| M8 | Phase reports lack lifecycle management | **MEDIUM** | Documentation | S02.2 |
| M9 | Release notes location inconsistent | **MEDIUM** | Documentation | S02.2 |
| M10 | Provider implementations partially complete | **MEDIUM** | Connector | S02.5 |
| L1 | `Resources/` surface/module duplication | **LOW** | Extension | S02.4 |
| L2 | `deployment/` artifact retention policy undefined | **LOW** | Release Engineering | S02.3 |
| L3 | PowerShell builder parity check is Windows-gated | **LOW** | Release Engineering | DEFER |
| L4 | Connector logging is ad-hoc | **LOW** | Connector | S02.5 |
| L5 | Connector exception hierarchy is flat | **LOW** | Connector | S02.5 |
| L6 | Config is environment-variable-only | **LOW** | Connector | S02.5 |
| L7 | Entity/Controller PHP shells are boilerplate | **LOW** | Extension | DEFER |
| L8 | Primary filter classes are repetitive | **LOW** | Extension | DEFER |
| L9 | ADR directory is nearly empty | **LOW** | Documentation | S02.6 |
| L10 | No release approval gate | **LOW** | Release Governance | DEFER |
| L11 | No artifact signing beyond SHA-256 | **LOW** | Release Governance | DEFER |
| L12 | Regression gate map references unimplemented suites | **LOW** | Testing | DEFER |

---

## 11. Recommended Execution Order

```
Week 1                  Week 2                  Week 3
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ S02.1        │       │ S02.3        │       │ S02.5        │
│ Test Unify   │──────▶│ Release Auto │──────▶│ Connector    │
│ (LOW diff)   │       │ (MED diff)   │       │ Pkg (MED)    │
└──────────────┘       └──────────────┘       └──────────────┘
       │                       │                       │
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ S02.2        │       │ S02.4        │       │ S02.6        │
│ Docs Fix     │       │ Ext Cleanup  │       │ C16 ADR      │
│ (LOW diff)   │       │ (LOW diff)   │       │ (MED diff)   │
└──────────────┘       └──────────────┘       └──────────────┘

  PARALLEL                SEQUENTIAL              PARALLEL
```

**Rationale:**
- S02.1 must come first (unified tests are a prerequisite for S02.3's pre-flight checks)
- S02.2 and S02.4 are independent and can run in parallel with S02.1
- S02.3 depends on S02.1 (needs unified test command for pre-flight)
- S02.5 and S02.6 are independent and can run in parallel with each other and with S02.3/S02.4

---

## 12. Final Verdict

### READY FOR S02 PLANNING

**Basis:** The project has no blocking architectural defects. The S01 freeze artifacts (deterministic builder, release integrity tests, version authority) are sound. The test system has strong Layer 1–2 coverage that catches regressions. The connector has well-isolated module boundaries. The extension has comprehensive static validation.

**Three HIGH findings** require attention early in S02 but none are blockers to starting S02:
1. No unified test entrypoint — S02.1
2. Release process is manual — S02.3
3. Documentation version staleness — S02.2

**C16 is architecturally feasible** but requires design-before-implementation (S02.6 ADRs). The current sync contract, gate, and entity patterns can absorb Quote/PI without architectural overhaul.

**Recommended S02 posture:** Consolidation over expansion. Execute the test unification and release automation before taking on any new business features. The project's engineering foundation is solid enough to support C16, but the tooling around that foundation (test running, release cutting, doc maintenance) needs hardening first.

---

## Appendix A: Key Directories Reviewed

| Directory | Review Depth |
|-----------|-------------|
| `docs/` (README, architecture, testing, release, phase-reports) | Deep — read 12+ files |
| `crm-extension/` (manifest, Resources, files/, tests, scripts) | Deep — read manifest, skeleton tests, build script, module.json |
| `chitu-connector/` (espocrm_sync, acquisition, vendored, tests) | Deep — read `__init__.py`, contract, gate, acquisition `__init__`, worker |
| `scripts/` (testing, runtime, acceptance) | Medium — read gate map, freeze gate, runtime gate |
| `deployment/` | Light — read README, verified artifact presence |
| `.gitignore`, `.gitattributes` | Light — verified coverage |
| `CLAUDE.md`, `README.md` | Deep — read in full |

**Not reviewed:** `archive/` directory, individual PHP service implementations, individual provider implementations, test file bodies beyond skeleton tests, provisioning scripts beyond what skeleton tests reference.

---

## Appendix B: Findings Summary by Severity

### HIGH (3)
- No unified test entrypoint (Testing)
- Release process is fully manual (Release Engineering)
- Documentation version staleness across ~286 files (Documentation)

### MEDIUM (10)
- Legacy `custom/` directory duplicating `files/` (Extension)
- No `pyproject.toml` for connector package (Connector)
- Test discovery depends on implicit PYTHONPATH (Testing)
- Live test guards inconsistent (Testing)
- Version constant sync risk in skeleton tests (Release Engineering)
- Historical commit message governance risk (Release Governance)
- Freeze gate is PowerShell-only (Release Governance)
- Phase reports lack lifecycle management (Documentation)
- Release notes location inconsistent (Documentation)
- Provider implementations partially complete (Connector)

### LOW / DEFER (12)
- `Resources/` surface/module duplication
- Artifact retention policy undefined
- PowerShell builder parity check Windows-gated
- Connector logging ad-hoc
- Exception hierarchy flat
- Config environment-variable-only
- PHP entity/controller shells boilerplate
- Primary filter classes repetitive
- ADR directory empty
- No release approval gate
- No artifact signing beyond SHA-256
- Regression gate map references unimplemented suites

---

## Appendix C: Recommended S02 Sub-Phases

| Phase | Name | Difficulty | Depends On | Parallelizable |
|-------|------|-----------|------------|----------------|
| **S02.1** | Test System Unification | Low | None | Yes |
| **S02.2** | Documentation Staleness Correction | Low | None | Yes |
| **S02.3** | Release Engineering Automation | Medium | S02.1 | No |
| **S02.4** | Extension Directory Cleanup | Low | None | Yes |
| **S02.5** | Connector Package Foundation | Medium | None | Yes |
| **S02.6** | C16 Architecture Design (ADR) | Medium | None | Yes |

---

## Appendix D: Recommended Priority

1. **S02.1** — Test System Unification (unblocks S02.3, highest practical impact)
2. **S02.2** — Documentation Staleness (quick win, prevents confusion)
3. **S02.3** — Release Automation (reduces human error in every future release)
4. **S02.4** — Extension Cleanup (removes ambiguity)
5. **S02.5** — Connector Package Foundation (enables proper dev workflow)
6. **S02.6** — C16 ADRs (design foundation for Phase3S03+)

---

## Appendix E: C16 Readiness Summary

| C16 Capability | Current Support | Gap | Severity |
|----------------|-----------------|-----|----------|
| Quote entity model | None — new entity needed | Entity design + metadata + API | Expected (new feature) |
| PI entity model | None — new entity needed | Entity design + metadata + API | Expected (new feature) |
| Approval workflow | Partial — `DraftApproval` exists for emails | Multi-entity, multi-level approval needed | Medium |
| PDF generation | None | Complete pipeline needed (engine selection is key decision) | **High** (architectural unknown) |
| Quote→Opportunity link | Lead→Opportunity projection exists | New relationship + transition rules | Low |
| CRM integration | `ChituSyncService` handles Lead/Evidence | New sync endpoints needed | Low |
| Sync contract | V1 has relevant fields | V2 may need Quote/PI sections | Low |

**Overall C16 readiness:** The foundation is solid. PDF generation is the only architectural unknown that requires early design attention (S02.6 ADR). All other gaps are expected new-feature work that the existing patterns can accommodate.

---

## Appendix F: Final Verdict

# READY FOR S02 PLANNING

The EspoCRM Production workspace is architecturally sound. The S01 freeze baseline is stable. Three HIGH findings (test unification, release automation, documentation staleness) are actionable consolidation items, not structural defects. C16 is feasible on the current architecture with one key design decision (PDF generation) to resolve early.

**S02 should be a stabilization sprint before C16 complexity arrives.**
