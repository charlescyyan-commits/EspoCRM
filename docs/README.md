# EspoCRM Production — Documentation Center

> **Phase D01 Documentation Center is complete and frozen as the documentation baseline.**
> Future phases must update only the documents directly affected by their changes.
> See [DOCUMENTATION_CENTER_REPORT.md](DOCUMENTATION_CENTER_REPORT.md) §10 for the full Maintenance Policy.

Central index for the **Chitu Prospecting Integration** workspace. All content is derived from current repository code, tests, manifests, deployment assets, and phase reports unless marked **Draft** or **TBD**.

## Current System Status

| Item | Value | Evidence |
|------|-------|----------|
| Extension version | `1.9.5-alpha` | `crm-extension/manifest.json` |
| EspoCRM compatibility | `>=7.4.0` | `crm-extension/manifest.json` |
| PHP compatibility | `>=8.1` | `crm-extension/manifest.json` |
| Latest packaged artifact | `deployment/prospecting-extension-1.9.5-alpha.zip` | `deployment/` |
| Connector sync contract | `1.0` | `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json` |
| Acquisition worker core | **Implemented** (in-memory / fake provider tests) | `chitu-connector/chitu_connector/acquisition/worker.py` |
| Job runner (EspoCRM adapter) | **Implemented** (fake provider only; offline tests) | `chitu-connector/chitu_connector/acquisition/runner.py`, [PHASE3C02_2C_JOB_RUNNER_REPORT.md](PHASE3C02_2C_JOB_RUNNER_REPORT.md) |

## Documentation Map

### Architecture

- [System Overview](architecture/SYSTEM_OVERVIEW.md)
- [Modules](architecture/MODULES.md)
- [Directory Structure](architecture/DIRECTORY_STRUCTURE.md)
- [Data Flow](architecture/DATA_FLOW.md)
- [Boundaries](architecture/BOUNDARIES.md)
- Historical: [Phase 3B Architecture](ARCHITECTURE_PHASE3B.md), [Extension Architecture Plan](architecture/ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md)

### API and Connector Contracts

- [API Index](api/README.md)
- [Connector API](api/CONNECTOR_API.md)
- [REST Endpoints](api/REST_ENDPOINTS.md)
- [Webhooks](api/WEBHOOKS.md)
- Contract artifacts: [sync-contracts/](sync-contracts/)

### Deployment

- [Install](deployment/INSTALL.md)
- [Upgrade](deployment/UPGRADE.md)
- [Rollback](deployment/ROLLBACK.md)
- [Package Build](deployment/PACKAGE.md)
- [Versioning](deployment/VERSIONING.md)
- Deployment assets: [../deployment/README.md](../deployment/README.md)

### Developer Guide

- [Getting Started](developer/GETTING_STARTED.md)
- [Local Setup](developer/LOCAL_SETUP.md)
- [Project Structure](developer/PROJECT_STRUCTURE.md)
- [Coding Guidelines](developer/CODING_GUIDELINES.md)
- [Testing](developer/TESTING.md)

### User Guide

- [Install Extension](user-guide/INSTALL_EXTENSION.md)
- [Search Workspace](user-guide/SEARCH_WORKSPACE.md)
- [Prospect Pool](user-guide/PROSPECT_POOL.md)
- [Leads](user-guide/LEADS.md)
- [ACL](user-guide/ACL.md)

### Testing

- [Test Plan](testing/TEST_PLAN.md)
- [Regression](testing/REGRESSION.md)
- [Manual Tests](testing/MANUAL_TESTS.md)
- [Checklist](testing/CHECKLIST.md)
- Historical test reports: [testing/](testing/)

### Release Engineering

- [Changelog Policy](release/CHANGELOG_POLICY.md)
- [Version Policy](release/VERSION_POLICY.md)
- [Release Process](release/RELEASE_PROCESS.md)
- [Release Notes Index](release/README.md)
- Current release: [v1.9.5-alpha](release/RELEASE_NOTES_1.9.5-alpha.md)

### Reports

- [Reports Index](reports/README.md)
- Phase reports (root): [PHASE3C_BACKLOG.md](PHASE3C_BACKLOG.md), [PHASE3B_FINAL_SUMMARY.md](PHASE3B_FINAL_SUMMARY.md)
- Phase reports (archive): [phase-reports/](phase-reports/)

### ADR

- [Architecture Decision Records](adr/README.md)

### Diagrams

- [Diagram Index](diagrams/README.md)

### Other Reference Areas (unchanged)

- [workflow/](workflow/) — outreach and CRM workflow references
- [email-rules/](email-rules/) — operational email references (not runtime code)

## Status Labels

Documents use these labels for important claims:

| Label | Meaning |
|-------|---------|
| **Implemented** | Present in committed source and installable metadata |
| **Contract Defined** | Schema or protocol documented; runtime adapter may be absent |
| **Runtime Verified** | Confirmed against a live EspoCRM instance in a phase report |
| **Static Verified** | Confirmed by offline tests or metadata checks |
| **Draft** | UI or workflow described but not runtime-verified in this repo |
| **TBD** | Requires runtime verification or a future phase |
| **Out of Scope** | Explicitly excluded by workspace rules |
| **Not Implemented** | Designed or referenced but no code in this repository |

## Maintenance Conventions

1. **Scope** — Update docs when code, tests, or manifests change. Do not document future phases as complete.
2. **Evidence** — Prefer links to source files and phase reports over narrative memory.
3. **Historical reports** — Phase reports under `docs/` and `docs/phase-reports/` are not moved or renamed; index them from [reports/README.md](reports/README.md).
4. **Relative links** — All internal links use paths relative to `docs/`.
5. **Secrets** — Never commit API keys, passwords, or `.env` contents to documentation.
6. **Parallel worktrees** — If `crm-extension/` or `chitu-connector/` have uncommitted changes, treat `manifest.json` and tests as the version authority over stale prose.
7. **Release baseline** — `1.9.5-alpha` is the current packaged release. Keep historical phase reports factual; update current operational documentation and add a release note for each packaged version.

## Per-Phase Documentation Update Rules

When completing a subsequent Phase, update only what that Phase directly changes:

| Change Type | Documents to Update |
|-------------|---------------------|
| New or changed CRM entities / fields | `architecture/SYSTEM_OVERVIEW.md`, `architecture/MODULES.md` (if new module) |
| New or changed API routes / endpoints | `api/REST_ENDPOINTS.md`, `api/CONNECTOR_API.md` |
| New or changed user-facing workflows | Corresponding `user-guide/*.md` |
| New or changed test commands / coverage | `developer/TESTING.md`, `testing/TEST_PLAN.md` |
| New or changed build / install / deploy steps | Corresponding `deployment/*.md` |
| Phase completion (any) | `reports/README.md` (add entry), `docs/README.md` (update system status if needed) |
| New ADR | `adr/README.md` (add entry) |
| New diagram | `diagrams/README.md` (add entry) |

**Do not** touch documents that are not directly affected. "Keeping them in sync" is not a valid reason to modify a document whose content has not changed. Historical phase reports, the ADR template, and the freeze policy itself are never modified as part of a routine Phase.

## Documentation Center Report

Phase D01 completion report: [DOCUMENTATION_CENTER_REPORT.md](DOCUMENTATION_CENTER_REPORT.md)
