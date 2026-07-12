# Phase3B00.2A — EspoCRM Production Repository Boundary Audit

**Date:** 2026-07-12  
**Scope:** READ-ONLY analysis — no file moves, deletions, renames, code modifications, or git history changes  
**Status:** AUDIT COMPLETE  
**Prerequisite for:** Phase3B00.2B (repository migration execution)

---

## Table of Contents

1. [Current Repository Scan](#1-current-repository-scan)
2. [File Classification Matrix](#2-file-classification-matrix)
3. [Dependency Analysis](#3-dependency-analysis)
4. [Target Directory Mapping](#4-target-directory-mapping)
5. [Risk Register](#5-risk-register)
6. [Migration Plan](#6-migration-plan)
7. [Post-Migration Verification](#7-post-migration-verification)
8. [Open Decisions](#8-open-decisions)

---

## 1. Current Repository Scan

### 1.1 Repository Profile

| Attribute | Value |
|---|---|
| Root | `D:\Chitu-intelligence` |
| Git branch | `master` |
| Total files (non-.git, non-node_modules, non-__pycache__) | ~1,200+ |
| Key top-level directories | 18 |
| Loose root files | ~110 (mostly .md reports/docs) |
| Mixed responsibilities since | Project inception |

### 1.2 Directory Inventory

```
D:\Chitu-intelligence\
├── .agents/                    [Claude agent definitions]
├── .claude/                    [Claude Code settings, hooks, workflows]
├── .codex/                     [Codex config]
├── .codex_spreadsheet_build/   [Codex spreadsheet build artifacts]
├── .git/                       [Git repository]
├── .github/workflows/          [CI/CD workflows]
├── .phase1-patch/              [Phase 1 patch artifacts]
├── .phase1-staging/            [Phase 1 staging area]
├── .playwright-mcp/            [Playwright MCP session data]
├── .venv-deep-research/        [Python venv for deep research]
├── app/                        [Chitu Intelligence web application]
│   ├── backend/                [FastAPI backend: API, services, core, db, models]
│   │   ├── api/                [REST API routes]
│   │   ├── core/               [Decision engine, state logic]
│   │   ├── db/                 [Database access]
│   │   ├── middleware/         [API middleware]
│   │   ├── models/             [Data models]
│   │   ├── services/           [Business logic services]
│   │   └── utils/              [Utilities]
│   ├── exports/                [Export artifacts]
│   └── frontend/               [React UI: dashboard, dist, i18n, src]
├── config/                     [Chitu search/country/keyword configs]
│   ├── apify_queries.txt
│   ├── apify_queries_metadata.json
│   ├── apify_query_groups.json
│   ├── countries.yml
│   └── keywords.yml
├── data/                       [Runtime data: leads_processed, leads_raw, logs, products]
├── db/                         [Database schema files]
├── dealer-database/            [Dealer pipeline data]
│   ├── analyzed/               [Analyzed dealers]
│   ├── bambu-pipeline/         [Bambu dealer pipeline]
│   ├── deep-research/          [Deep research outputs]
│   ├── discovered/             [Discovered dealers]
│   ├── outreach-ready/         [Outreach-ready dealers]
│   ├── researched/             [Researched dealers]
│   └── scored/                 [Scored dealers]
├── docs/                       [Documentation]
│   ├── espocrm-extension/      [43 EspoCRM-related docs]
│   └── prospecting-engine/     [58 Prospecting Engine docs]
├── espocrm_extension/          [EspoCRM extension package]
│   ├── Resources/              [Extension-wide resources: acl, entityDefs, layouts, metadata]
│   ├── application/            [Application README]
│   ├── custom/                 [Module source overlay (Custom namespace)]
│   ├── docs/                   [Extension docs placeholder]
│   ├── files/                  [Deployable extension files]
│   │   └── custom/Espo/
│   │       ├── Custom/         [Custom namespace overlay]
│   │       └── Modules/Prospecting/  [Prospecting module]
│   │           ├── Api/
│   │           ├── Classes/Select/Lead/PrimaryFilters/
│   │           ├── Controllers/
│   │           ├── Entities/
│   │           ├── Resources/
│   │           │   ├── i18n/en_US/
│   │           │   ├── layouts/
│   │           │   └── metadata/
│   │           └── Services/
│   ├── scripts/                [Build script]
│   └── tests/                  [Extension tests]
├── integration/                [Integration adapters]
│   └── espocrm_sync/           [14 Python files: sync adapter for Engine→CRM]
│       └── provisioning/       [CRM provisioning scripts]
├── logs/                       [Runtime logs]
├── memory/                     [Claude session memory files]
├── node_modules/               [npm dependencies]
├── outputs/                    [Build outputs, workbooks]
├── prospecting_engine/         [AI Prospecting Engine]
│   ├── adapters/               [External service adapters (Apify)]
│   ├── config/                 [Engine configuration]
│   ├── contracts/              [Data contracts (scoring, research, ICP, etc.)]
│   ├── domain/                 [Domain models and state machine]
│   ├── fixtures/               [Test fixtures and scenarios]
│   ├── repositories/           [Data repositories]
│   ├── scoring/v4/             [Canonical V4 scoring engine]
│   ├── services/               [Business logic services]
│   └── tests/                  [Engine tests]
├── raw-data/                   [Raw imported data]
├── reports/                    [Generated reports]
├── revenue_system/             [Revenue optimization layer]
├── scripts/                    [~130 utility/pipeline/build scripts]
│   └── build_safety/           [Frontend build safety checks]
├── temp/                       [Temporary files]
├── test-dealers/               [Test dealer data]
├── tests/                      [10 integration/E2E tests]
├── tools/                      [External tools]
└── workflows/                  [Workflow definition documents]
```

---

## 2. File Classification Matrix

### Classification Key

| Category | Label | Action |
|---|---|---|
| **A** | CRM-MOVE | Move to `D:\EspoCRM-Production\` |
| **B** | CHITU-KEEP | Keep in `D:\Chitu-intelligence-archive\` |
| **C** | REVIEW | Requires human decision before move |
| **X** | EXCLUDE | Excluded from migration (temp, venv, caches) |

### 2.1 Top-Level Directories

| Directory | Category | Rationale |
|---|---|---|
| `espocrm_extension/` | **A — CRM-MOVE** | Core EspoCRM extension package. Entire directory. |
| `integration/espocrm_sync/` | **A — CRM-MOVE** | Engine→CRM sync adapter. Runtime dependency of CRM pipeline. |
| `integration/` (rest) | **C — REVIEW** | Only `espocrm_sync/` subdirectory is CRM; `__init__.py` is shared. |
| `docs/espocrm-extension/` | **A — CRM-MOVE** | All 43 CRM design/phase/report documents. |
| `docs/prospecting-engine/` | **B — CHITU-KEEP** | Prospecting engine documentation. |
| `docs/` (root-level) | **C — REVIEW** | Mixed docs — see §2.5. |
| `prospecting_engine/` | **B — CHITU-KEEP** | AI prospecting engine — core Chitu Intelligence IP. |
| `app/` | **B — CHITU-KEEP** | Chitu web application (backend + frontend). |
| `scripts/` | **C — REVIEW** | Mixed scripts — see §2.4. |
| `tests/` | **C — REVIEW** | Mixed tests — see §2.3. |
| `config/` | **B — CHITU-KEEP** | Chitu search/country/keyword configuration. |
| `data/` | **B — CHITU-KEEP** | Chitu runtime data. |
| `db/` | **B — CHITU-KEEP** | Chitu database schema. |
| `dealer-database/` | **B — CHITU-KEEP** | Dealer pipeline data — core Chitu IP. |
| `logs/` | **X — EXCLUDE** | Runtime logs. |
| `memory/` | **X — EXCLUDE** | Session memory files. |
| `node_modules/` | **X — EXCLUDE** | npm dependencies (reinstall). |
| `outputs/` | **B — CHITU-KEEP** | Chitu build outputs. |
| `raw-data/` | **B — CHITU-KEEP** | Chitu raw input data. |
| `reports/` | **B — CHITU-KEEP** | Chitu-generated reports. |
| `revenue_system/` | **B — CHITU-KEEP** | Revenue optimization — Chitu IP. |
| `temp/` | **X — EXCLUDE** | Temporary files. |
| `test-dealers/` | **B — CHITU-KEEP** | Test dealer data. |
| `tools/` | **B — CHITU-KEEP** | Chitu tools. |
| `workflows/` | **B — CHITU-KEEP** | Workflow definition documents (Chitu process). |
| `.agents/` | **C — REVIEW** | Claude agent definitions — may contain CRM-related agents. |
| `.claude/` | **C — REVIEW** | Claude Code settings — project-specific, may need split. |
| `.github/workflows/` | **C — REVIEW** | CI/CD — may need split between CRM and Chitu. |
| `.codex/`, `.codex_spreadsheet_build/` | **B — CHITU-KEEP** | Codex artifacts. |
| `.phase1-patch/`, `.phase1-staging/` | **X — EXCLUDE** | Historical artifacts. |
| `.playwright-mcp/` | **X — EXCLUDE** | Browser session data. |
| `.venv-deep-research/` | **X — EXCLUDE** | Python venv (recreate). |

### 2.2 espocrm_extension/ — Detailed Breakdown

All files classified **A — CRM-MOVE** unless noted.

| File | Category | Notes |
|---|---|---|
| `manifest.json` | A | Extension manifest |
| `README.md` | A | Extension README |
| `scripts/build_release_package.ps1` | A | Build script for extension ZIP |
| `scripts/README.md` | A | Script docs |
| `application/README.md` | A | Placeholder |
| `Resources/` (entire tree) | A | Extension-wide resources: acl, entityDefs, layouts, metadata |
| `custom/` (entire tree) | A | Module source overlay |
| `files/custom/Espo/Modules/Prospecting/` (entire tree) | A | **Core extension code** — entities, controllers, services, metadata, i18n, layouts, primary filters |
| `files/custom/Espo/Custom/` (entire tree) | A | Custom namespace overlay |
| `docs/.gitkeep` | A | Placeholder |
| `tests/__init__.py` | A | Test package init |
| `tests/test_extension_skeleton.py` | A | Extension structure test |
| `tests/README.md` | A | Test docs |

**Extensions file count:** 41 files (excluding `__pycache__`)

**Build script analysis** (`scripts/build_release_package.ps1`):
- Takes `-OutputPath` parameter
- Packages `manifest.json` + everything under `files/`
- Uses relative paths from `$extensionRoot` (parent of `scripts/`)
- **No external dependencies.** Self-contained.
- **Migration note:** Will work unchanged in new workspace. Simply needs `espocrm_extension/` directory structure preserved.

### 2.3 tests/ — Detailed Breakdown

| File | Category | Rationale |
|---|---|---|
| `test_espocrm_real_client.py` | **A — CRM-MOVE** | Tests EspoCRM real client integration |
| `test_espocrm_sync_adapter.py` | **A — CRM-MOVE** | Tests EspoCRM sync adapter |
| `test_espocrm_lifecycle_sync.py` | **A — CRM-MOVE** | Tests Lead lifecycle sync |
| `test_espocrm_email_lifecycle.py` | **A — CRM-MOVE** | Tests email lifecycle integration |
| `test_alpha_auth.py` | **B — CHITU-KEEP** | Tests Chitu alpha authentication |
| `test_alpha_blockers.py` | **B — CHITU-KEEP** | Tests Chitu alpha blockers |
| `test_apify_exclusions.py` | **B — CHITU-KEEP** | Tests Apify exclusion logic |
| `test_dry_run_isolation.py` | **B — CHITU-KEEP** | Tests Chitu dry-run isolation |
| `test_lead_mutation_safety.py` | **B — CHITU-KEEP** | Tests Chitu lead mutation safety |
| `test_lead_visibility.py` | **B — CHITU-KEEP** | Tests Chitu lead visibility |

**Verdict:** 4 EspoCRM tests → Category A. 6 Chitu tests → Category B. Clean split.

### 2.4 scripts/ — Detailed Breakdown

~130 files. Classified by purpose:

#### CRM-Related Scripts (Category A)

| File | Rationale |
|---|---|
| *(none identified)* | All scripts serve Chitu Intelligence pipeline, JSX conversion, data migration, or Apify integration. |

**Verdict:** All scripts are **B — CHITU-KEEP**. No scripts currently serve EspoCRM production operations. The CRM build script is in `espocrm_extension/scripts/`, not here.

### 2.5 Root-Level Markdown Documents — Classification

~110 loose .md files at repository root. Classified by topic:

#### Category A — CRM-MOVE (EspoCRM-related)

| File | Rationale |
|---|---|
| `EMAIL_GENERATOR_V3_SPEC.md` | Email generation spec — CRM operational reference |
| `EMAIL_WRITING_RULES_V2.md` | Email rules — CRM operational reference |
| `EMAIL_WRITING_RULES_V3.md` | Email rules (authoritative) — CRM operational reference |
| `EMAIL_DRAFT_PROMPT_V1.md` | Email prompt spec — CRM operational reference |
| `OUTREACH_RESULTS_SCHEMA_V2.md` | Outreach schema — CRM data model reference |
| `MULTI_PRODUCT_OUTREACH_RULE.md` | Outreach rules — CRM operational reference |
| `LCD_OUTREACH_INTELLIGENCE_V1.md` | LCD outreach rules — CRM operational reference |

#### Category B — CHITU-KEEP (Chitu Intelligence-specific)

All other root .md files are Chitu Intelligence reports, audits, deployment plans, and project documentation. Notable examples:

| File | Topic |
|---|---|
| `CHITU_BACKEND_SALVAGE_AUDIT_V1.md` | Chitu backend audit |
| `CHITU_CURRENT_STATE_MACHINE_V1.md` | Chitu state machine audit |
| `CHITU_CODEBASE_MAP_V1.md` | Chitu codebase map |
| `RAILWAY_*.md` (~20 files) | Railway deployment reports |
| `ALPHA_*.md` (~8 files) | Alpha deployment reports |
| `LEAD_*.md` (~8 files) | Lead system audits |
| `PRE_ALPHA_*.md` (3 files) | Pre-alpha readiness |
| `PROJECT_STATE*.md` (2 files) | Project state docs |
| `SCORING_ENGINE_*.md` (2 files) | Scoring engine specs |
| `SYSTEM_*.md` (2 files) | System documentation |
| All other `*_REPORT*.md` / `*_AUDIT*.md` / `*_DIAGNOSIS*.md` | Historical reports |

#### Category C — REVIEW

| File | Rationale |
|---|---|
| `CLAUDE.md` | Project instructions. Contains both Chitu AND CRM rules. Needs split or copy. |
| `ACTIVE_RULES.md` | Current active rules — references both systems. |
| `START_HERE.md` | Project onboarding — mixed references. |
| `README.md` | Project README — mixed references. |
| `PRODUCT_INTELLIGENCE_V2.md` | Product intelligence — used by both email generation AND scoring. |
| `PROCESS_DEALERS_GAP_REPORT.md` | Gap analysis — references both systems. |
| `WORKFLOW_CURRENT.md` | Current workflow doc — mixed references. |
| `DOCUMENT_ARCHIVE_PLAN.md` | Document archive plan — covers both. |
| `DO_NOT_CHANGE.md` | Protected items list — mixed scope. |
| `CHANGELOG.md` | Project changelog — mixed scope. |
| `CURRENT_TASK.md` | Current task tracking. |
| `IMPLEMENTATION_PLAN.md` | Implementation plan — mixed scope. |

### 2.6 Root-Level Non-Markdown Files

| File | Category | Rationale |
|---|---|---|
| `Dockerfile` | **B — CHITU-KEEP** | Chitu Railway deployment (Python+Node+Playwright) |
| `docker-compose.local.yml` | **B — CHITU-KEEP** | Chitu local dev setup |
| `Procfile` | **B — CHITU-KEEP** | Chitu Railway process definition |
| `nixpacks.toml` | **B — CHITU-KEEP** | Chitu Railway build config |
| `package.json` | **B — CHITU-KEEP** | Chitu frontend dependencies |
| `package-lock.json` | **B — CHITU-KEEP** | Chitu frontend lockfile |
| `.env` | **X — EXCLUDE** | Secrets — never migrate |
| `.env.example` | **C — REVIEW** | Env template — contains both CRM and Chitu vars |
| `.dockerignore` | **B — CHITU-KEEP** | Chitu Docker config |
| `.gitignore` | **C — REVIEW** | Git ignore — may need adaptation for CRM repo |
| `.mcp.json` | **C — REVIEW** | MCP server config — session-specific |
| `requirements-webapp.txt` | **B — CHITU-KEEP** | Chitu Python deps |
| `requirements-deep-research.txt` | **B — CHITU-KEEP** | Chitu deep research deps |
| `deployment_manifest.json` | **B — CHITU-KEEP** | Chitu deployment manifest |
| `ci_guard_result.json` | **B — CHITU-KEEP** | Chitu CI result |
| `*.py` (debug/test/tmp files) | **X — EXCLUDE** | Debug scripts (debug2.py, debug3.py, test_db.py, etc.) |
| `tmp_*.py` / `tmp_*.txt` | **X — EXCLUDE** | Temporary fix scripts |
| `*.patch` / `*.diff` | **X — EXCLUDE** | Historical patches |
| `*.ts` / `*.tsx` (loose) | **B — CHITU-KEEP** | Phase 1 UI prototypes |
| `*.png` | **B — CHITU-KEEP** | Screenshot |
| `research-*.md` | **B — CHITU-KEEP** | Research reports |
| `*_report.md` (loose) | **C — REVIEW** | Mixed reports — classify by content |
| `contact_enrichment_v2_report.md` | **B — CHITU-KEEP** | Chitu enrichment report |
| `dealer-analysis-prompt.md` | **B — CHITU-KEEP** | Chitu analysis prompt |
| `dealer_contact_enrichment_v1_report.md` | **B — CHITU-KEEP** | Chitu enrichment report |
| `deep_research_pipeline_validation_report.md` | **B — CHITU-KEEP** | Chitu pipeline report |
| `lead-intelligence-schema.md` | **B — CHITU-KEEP** | Chitu schema doc |
| `lcd_email_v2_examples.md` | **A — CRM-MOVE** | LCD email examples — CRM operational reference |
| `product-detail-*.md` / `product-match-rules*.md` | **B — CHITU-KEEP** | Product detail/matching docs |
| `quotation-page-screenshot.png` | **B — CHITU-KEEP** | Screenshot |

---

## 3. Dependency Analysis

### 3.1 Critical Cross-Dependency: integration/espocrm_sync → prospecting_engine

**This is the single most important dependency to resolve before migration.**

Files in `integration/espocrm_sync/` that import from `prospecting_engine/`:

| File | Import | Purpose |
|---|---|---|
| `models.py` | `prospecting_engine.contracts.business_qualification.BusinessQualificationResult` | Type annotation for SyncSource |
| `models.py` | `prospecting_engine.contracts.website_research.WebsiteResearchResult` | Type annotation for SyncSource |
| `models.py` | `prospecting_engine.domain.models.Candidate` | Type annotation for SyncSource |
| `real_sync.py` | `prospecting_engine.config.search_sources.SearchSource` | Build synthetic source |
| `real_sync.py` | `prospecting_engine.contracts.website_research.EvidenceItem` | Build synthetic source |
| `real_sync.py` | `prospecting_engine.contracts.website_research.WebsiteResearchResult` | Build synthetic source |
| `real_sync.py` | `prospecting_engine.domain.models.Candidate` | Build synthetic source |
| `real_sync.py` | `prospecting_engine.domain.models.ProspectState` | Build synthetic source |

**Severity: HIGH.** Moving `integration/espocrm_sync/` without the `prospecting_engine/` contracts and domain models will break imports.

**Resolution options** (for implementation phase, not this audit):

| Option | Description | Risk |
|---|---|---|
| **A — Vendor contracts** | Copy `prospecting_engine/contracts/` and `prospecting_engine/domain/models.py` into EspoCRM-Production as a vendored dependency | Low. Contracts are designed as stable, versioned interfaces. |
| **B — Shared contracts package** | Extract contracts into a standalone `chitu-contracts` Python package (pip-installable) used by both repos | Medium. Requires packaging work but cleanest long-term. |
| **C — Keep monorepo** | Don't split; keep integration/ in Chitu-intelligence | Defeats purpose of migration. |
| **D — Decouple with dicts** | Rewrite integration to use plain dicts/dataclasses instead of prospecting_engine imports | Medium. Breaking change to sync adapter. |

**Recommendation: Option A (vendor contracts)** as immediate step, with Option B (shared package) as Phase 3B-03 follow-up.

### 3.2 integration/espocrm_sync → prospecting_engine (config)

`real_sync.py` imports `SearchSource` from `prospecting_engine.config.search_sources`. This is used only in `build_synthetic_source()` — the test fixture builder. Not a production sync path dependency.

**Resolution:** Copy `search_sources.py` alongside tests, or refactor synthetic source builder to use inline constants.

### 3.3 Internal integration/ Dependencies

All modules within `integration/espocrm_sync/` reference each other via `integration.espocrm_sync.*` package paths. These are self-contained within the module.

| Import pattern | Count | Resolution |
|---|---|---|
| `from integration.espocrm_sync.X import Y` | ~25 | Works if `integration/espocrm_sync/` directory structure preserved |
| `from integration.espocrm_sync.X import Y` (via `__init__.py`) | 13 | Re-exports in `__init__.py` — same resolution |
| `from prospecting_engine.X import Y` | 8 | **BREAKS** — see §3.1 |

### 3.4 EspoCRM Extension Internal Dependencies

The extension package (`espocrm_extension/files/`) is a standard EspoCRM module with no external Python/PHP dependencies.

| Item | Dependency | Status |
|---|---|---|
| `Entities/ResearchEvidence.php` | `namespace Espo\Modules\Prospecting\Entities` | Self-contained |
| `Controllers/ResearchEvidence.php` | `namespace Espo\Modules\Prospecting\Controllers`; extends `\Espo\Core\Controllers\Record` | Standard EspoCRM dependency |
| `Classes/Select/Lead/PrimaryFilters/*.php` | `namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters`; extends `\Espo\Core\Select\Primary\Filter` | Standard EspoCRM dependency |
| `entityDefs/*.json` | References `ResearchEvidence` entity, `Lead` entity, `Opportunity` entity | All within EspoCRM |
| Build script | PowerShell, `System.IO.Compression` | Standard Windows/.NET |

**No broken dependencies.** The extension is architecturally clean with respect to EspoCRM internals.

### 3.5 Test File Dependencies

| Test | Imports From | After Move Status |
|---|---|---|
| `test_espocrm_real_client.py` | `integration.espocrm_sync.real_client` | ✅ Works (module moves together) |
| `test_espocrm_sync_adapter.py` | `integration.espocrm_sync.client`, `integration.espocrm_sync.models` | ✅ Works |
| `test_espocrm_lifecycle_sync.py` | `integration.espocrm_sync.lifecycle_sync` | ✅ Works |
| `test_espocrm_email_lifecycle.py` | `integration.espocrm_sync.email_lifecycle_sync` | ✅ Works |

All CRM test dependencies are internal to `integration/espocrm_sync/` and will resolve correctly after migration (assuming §3.1 resolution).

### 3.6 Documentation Cross-References

| Doc (CRM-MOVE) | References | Status |
|---|---|---|
| `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md` | `CLAUDE.md`, `SCORING_ENGINE_V3.md` | ⚠️ Cross-system references |
| `ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md` | References Engine scoring rules | ⚠️ Cross-system |
| `PHASE3A25_WORKFLOW_DESIGN.md` | `PROSPECTING_ENGINE_STATE_MACHINE_V1.md`, `EMAIL_WRITING_RULES_V3.md`, `CLAUDE.md` | ⚠️ Cross-system |
| `ESPOCRM_SYNC_RULES_V1.md` | Engine version references | ⚠️ Cross-system |

**Mitigation:** Cross-references are informational (design rationale), not operational. They do not break functionality. When referenced docs are in the Chitu archive, update links to point to archive paths or inline the essential context.

---

## 4. Target Directory Mapping

### 4.1 Proposed Target Structure

```
D:\
├── EspoCRM-Test\
│   └── docker-compose.yml              [Existing local test environment]
│
├── EspoCRM-Production\                  [NEW — Production CRM workspace]
│   │
│   ├── crm-extension\                   [EspoCRM extension package]
│   │   ├── manifest.json               ← espocrm_extension/manifest.json
│   │   ├── README.md                   ← espocrm_extension/README.md
│   │   ├── Resources\                  ← espocrm_extension/Resources/*
│   │   ├── application\               ← espocrm_extension/application/*
│   │   ├── custom\                     ← espocrm_extension/custom/*
│   │   ├── files\                      ← espocrm_extension/files/*
│   │   ├── scripts\                    ← espocrm_extension/scripts/*
│   │   ├── tests\                      ← espocrm_extension/tests/*
│   │   └── docs\                       ← espocrm_extension/docs/*
│   │
│   ├── chitu-connector\                [Engine→CRM sync adapter (Python)]
│   │   ├── __init__.py                 ← integration/__init__.py
│   │   ├── espocrm_sync\              ← integration/espocrm_sync/*
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── contract.py
│   │   │   ├── gate.py
│   │   │   ├── mapper.py
│   │   │   ├── client.py
│   │   │   ├── real_client.py
│   │   │   ├── real_sync.py
│   │   │   ├── lifecycle.py
│   │   │   ├── lifecycle_sync.py
│   │   │   ├── email_lifecycle.py
│   │   │   ├── email_lifecycle_sync.py
│   │   │   ├── idempotency.py
│   │   │   ├── audit.py
│   │   │   └── provisioning\          ← integration/espocrm_sync/provisioning/*
│   │   ├── vendored\                   [Vendored prospecting_engine contracts]
│   │   │   ├── contracts\             ← prospecting_engine/contracts/*
│   │   │   │   ├── business_qualification.py
│   │   │   │   ├── canonical_score.py
│   │   │   │   ├── entity_identity.py
│   │   │   │   ├── icp.py
│   │   │   │   ├── scoring.py
│   │   │   │   ├── search_result.py
│   │   │   │   ├── single_candidate_loop.py
│   │   │   │   └── website_research.py
│   │   │   ├── domain\                ← prospecting_engine/domain/models.py
│   │   │   │   └── models.py
│   │   │   └── config\                ← prospecting_engine/config/search_sources.py
│   │   │       └── search_sources.py
│   │   └── requirements.txt            [Python dependencies for connector]
│   │
│   ├── deployment\                      [CRM deployment scripts and configs]
│   │   ├── docker-compose.prod.yml     [Production EspoCRM Docker config]
│   │   ├── .env.example                [CRM environment template]
│   │   └── provisioning\               [CRM provisioning scripts]
│   │       └── phase3a33_provision_roles.php
│   │
│   ├── docs\                            [CRM operational documentation]
│   │   ├── architecture\               [Architecture docs]
│   │   │   ├── ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md
│   │   │   ├── ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md
│   │   │   ├── ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md
│   │   │   └── ESPOCRM_SYNC_RULES_V1.md
│   │   ├── workflow\                   [Workflow design docs]
│   │   │   ├── PHASE3A25_WORKFLOW_DESIGN.md
│   │   │   └── OUTREACH_STATUS_MODEL_V1.md
│   │   ├── sync-contracts\             [Sync contract specs]
│   │   │   └── ESPOCRM_SYNC_CONTRACT_V1.json
│   │   ├── phase-reports\              [Phase execution reports]
│   │   │   ├── PHASE3A1_FINAL_REPORT_V1.md
│   │   │   ├── PHASE3A22A_FINAL_REPORT_V1.md
│   │   │   ├── PHASE3A22B_*.md
│   │   │   ├── PHASE3A23_*.md
│   │   │   ├── PHASE3A24_*.md
│   │   │   ├── PHASE3A25_*.md
│   │   │   ├── PHASE3A26_*.md
│   │   │   ├── PHASE3A27_*.md
│   │   │   ├── PHASE3A28_*.md
│   │   │   ├── PHASE3A29_*.md
│   │   │   ├── PHASE3A30_*.md
│   │   │   ├── PHASE3A31_*.md
│   │   │   ├── PHASE3A32_*.md
│   │   │   ├── PHASE3A33_*.md
│   │   │   ├── PHASE3A34_*.md
│   │   │   ├── PHASE3B00_*.md
│   │   │   └── PHASE3B01_*.md
│   │   ├── email-rules\                [Email operational rules]
│   │   │   ├── EMAIL_GENERATOR_V3_SPEC.md
│   │   │   ├── EMAIL_WRITING_RULES_V3.md
│   │   │   ├── EMAIL_DRAFT_PROMPT_V1.md
│   │   │   ├── MULTI_PRODUCT_OUTREACH_RULE.md
│   │   │   └── lcd_email_v2_examples.md
│   │   ├── testing\                    [Test plans and reports]
│   │   │   ├── ESPOCRM_SYNC_TEST_PLAN_V1.md
│   │   │   ├── ESPOCRM_SYNC_ADAPTER_TEST_REPORT_V1.md
│   │   │   └── ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md
│   │   └── PROJECT.md                  [CRM project README]
│   │
│   ├── tests\                           [CRM integration tests]
│   │   ├── test_espocrm_real_client.py
│   │   ├── test_espocrm_sync_adapter.py
│   │   ├── test_espocrm_lifecycle_sync.py
│   │   └── test_espocrm_email_lifecycle.py
│   │
│   └── README.md                        [CRM workspace README]
│
└── Chitu-intelligence-archive\          [Frozen legacy AI workspace]
    └── (all Category B files from D:\Chitu-intelligence)
```

### 4.2 Detailed File Mapping

#### 4.2.1 crm-extension/

| Source (D:\Chitu-intelligence\) | Target (D:\EspoCRM-Production\crm-extension\) |
|---|---|
| `espocrm_extension/manifest.json` | `manifest.json` |
| `espocrm_extension/README.md` | `README.md` |
| `espocrm_extension/Resources/**` | `Resources/**` |
| `espocrm_extension/application/**` | `application/**` |
| `espocrm_extension/custom/**` | `custom/**` |
| `espocrm_extension/files/**` | `files/**` |
| `espocrm_extension/scripts/**` | `scripts/**` |
| `espocrm_extension/tests/**` | `tests/**` |
| `espocrm_extension/docs/**` | `docs/**` |

**Path adjustment needed:** The build script `scripts/build_release_package.ps1` uses `Split-Path -Parent $PSScriptRoot` to find the extension root. After migration, this still works correctly since the relative structure (`scripts/` → parent = `crm-extension/`) is preserved.

#### 4.2.2 chitu-connector/

| Source | Target | Notes |
|---|---|---|
| `integration/__init__.py` | `chitu-connector/__init__.py` | Package init (if any content) |
| `integration/espocrm_sync/__init__.py` | `chitu-connector/espocrm_sync/__init__.py` | ⚠️ See import path fix |
| `integration/espocrm_sync/models.py` | `chitu-connector/espocrm_sync/models.py` | ⚠️ See import path fix |
| `integration/espocrm_sync/contract.py` | `chitu-connector/espocrm_sync/contract.py` | — |
| `integration/espocrm_sync/gate.py` | `chitu-connector/espocrm_sync/gate.py` | — |
| `integration/espocrm_sync/mapper.py` | `chitu-connector/espocrm_sync/mapper.py` | — |
| `integration/espocrm_sync/client.py` | `chitu-connector/espocrm_sync/client.py` | — |
| `integration/espocrm_sync/real_client.py` | `chitu-connector/espocrm_sync/real_client.py` | — |
| `integration/espocrm_sync/real_sync.py` | `chitu-connector/espocrm_sync/real_sync.py` | ⚠️ See import path fix |
| `integration/espocrm_sync/lifecycle.py` | `chitu-connector/espocrm_sync/lifecycle.py` | — |
| `integration/espocrm_sync/lifecycle_sync.py` | `chitu-connector/espocrm_sync/lifecycle_sync.py` | — |
| `integration/espocrm_sync/email_lifecycle.py` | `chitu-connector/espocrm_sync/email_lifecycle.py` | — |
| `integration/espocrm_sync/email_lifecycle_sync.py` | `chitu-connector/espocrm_sync/email_lifecycle_sync.py` | — |
| `integration/espocrm_sync/idempotency.py` | `chitu-connector/espocrm_sync/idempotency.py` | — |
| `integration/espocrm_sync/audit.py` | `chitu-connector/espocrm_sync/audit.py` | — |
| `integration/espocrm_sync/provisioning/phase3a33_provision_roles.php` | `chitu-connector/espocrm_sync/provisioning/phase3a33_provision_roles.php` | — |
| `prospecting_engine/contracts/*.py` (8 files) | `chitu-connector/vendored/contracts/*.py` | Vendored copy |
| `prospecting_engine/domain/models.py` | `chitu-connector/vendored/domain/models.py` | Vendored copy |
| `prospecting_engine/config/search_sources.py` | `chitu-connector/vendored/config/search_sources.py` | Vendored copy |

#### 4.2.3 Import Path Fix Required

After migration, all `from integration.espocrm_sync.X import Y` imports must change to reflect the new package root. Two approaches:

**Approach 1 — Make `chitu-connector/` the Python package root:**
```python
# Before (in real_sync.py):
from integration.espocrm_sync.gate import evaluate_sync_gate

# After:
from espocrm_sync.gate import evaluate_sync_gate
```

**Approach 2 — Keep `chitu-connector/` as a sub-package:**
```python
# Before:
from integration.espocrm_sync.gate import evaluate_sync_gate

# After:
from chitu_connector.espocrm_sync.gate import evaluate_sync_gate
```

And for vendored imports:
```python
# Before (in models.py):
from prospecting_engine.contracts.business_qualification import BusinessQualificationResult

# After (Approach 1):
from vendored.contracts.business_qualification import BusinessQualificationResult

# After (Approach 2):
from chitu_connector.vendored.contracts.business_qualification import BusinessQualificationResult
```

**Recommendation: Approach 2** — keeps a namespace prefix, avoids collision with other packages, and makes the vendored status explicit.

#### 4.2.4 docs/

All 43 files from `docs/espocrm-extension/` → `EspoCRM-Production/docs/` reorganized into subdirectories (see §4.1).

7 root-level CRM docs → `EspoCRM-Production/docs/email-rules/`.

### 4.3 Chitu-intelligence-archive Structure

The archive preserves the original `D:\Chitu-intelligence\` layout minus moved CRM files:

```
D:\Chitu-intelligence-archive\
├── app\                       [unchanged]
├── config\                    [unchanged]
├── data\                      [unchanged]
├── db\                        [unchanged]
├── dealer-database\           [unchanged]
├── docs\                      [minus espocrm-extension/]
│   └── prospecting-engine\   [unchanged]
├── logs\                      [unchanged]
├── outputs\                   [unchanged]
├── prospecting_engine\        [unchanged]
├── raw-data\                  [unchanged]
├── reports\                   [unchanged]
├── revenue_system\            [unchanged]
├── scripts\                   [unchanged]
├── temp\                      [unchanged]
├── test-dealers\              [unchanged]
├── tests\                     [minus 4 CRM tests]
├── tools\                     [unchanged]
├── workflows\                 [unchanged]
├── .agents\                   [unchanged]
├── .claude\                   [unchanged]
├── .github\                   [unchanged]
├── .git\                      [preserved git history]
└── (root .md files)           [minus 7 CRM docs]
```

---

## 5. Risk Register

| # | Risk | Severity | Affected Files | Mitigation |
|---|---|---|---|---|
| **R1** | `prospecting_engine` imports break in `integration/espocrm_sync/` | **HIGH** | `models.py`, `real_sync.py` | Vendor contracts as described in §3.1. Update import paths. |
| **R2** | Import paths break after package rename (`integration.espocrm_sync` → `chitu_connector.espocrm_sync`) | **HIGH** | All 14 `.py` files in `integration/espocrm_sync/` | Systematic search-and-replace of import paths. Verify with `python -c "import chitu_connector"`. |
| **R3** | Build script `build_release_package.ps1` fails due to path assumptions | **LOW** | `espocrm_extension/scripts/build_release_package.ps1` | Script uses `$PSScriptRoot`-relative paths. As long as `scripts/` is sibling to `manifest.json` and `files/`, it works. Verified: structure preserved. |
| **R4** | Test files reference old import paths | **MEDIUM** | 4 CRM test files in `tests/` | Same import path fix as R2. Update `from integration.espocrm_sync` → `from chitu_connector.espocrm_sync`. |
| **R5** | Documentation cross-references point to Chitu archive paths that don't exist | **LOW** | ~10 CRM docs reference Chitu docs | Add a `CROSS_REFERENCES.md` in CRM docs listing archive paths. Non-blocking. |
| **R6** | EspoCRM extension Custom vs Module overlay dual-registration persists | **MEDIUM** | `espocrm_extension/files/custom/Espo/Custom/` + `Modules/Prospecting/` | Documented in `EXTENSION_STRUCTURE_AUDIT_REPORT.md`. Migration doesn't fix — needs separate cleanup phase. Not a migration blocker. |
| **R7** | `.env.example` contains both CRM and Chitu variables | **LOW** | `.env.example` | Split into two: `EspoCRM-Production/deployment/.env.example` (CRM vars only) and archive (original). |
| **R8** | Git history: moved files lose git history if not using `git mv` | **MEDIUM** | All moved files | Use `git mv` where possible to preserve history. For cross-repo moves, note the source commit hash in migration log. |
| **R9** | `__init__.py` re-exports may expose stale module paths | **LOW** | `integration/espocrm_sync/__init__.py` | Re-export block uses `from integration.espocrm_sync.X import Y`. Update along with R2. |
| **R10** | Provisioning PHP script references EspoCRM bootstrap path | **LOW** | `provisioning/phase3a33_provision_roles.php` | `require '/var/www/html/bootstrap.php'` is a Docker-internal path. Works as long as Docker container is EspoCRM. No change needed. |

---

## 6. Migration Plan

### Phase 3B00.2B — Repository Migration Execution (NOT this phase)

**Prerequisite:** This audit document approved.

**Step 1: Create EspoCRM-Production workspace**
```
mkdir D:\EspoCRM-Production
cd D:\EspoCRM-Production
git init
```

**Step 2: Create directory scaffold**
```
mkdir D:\EspoCRM-Production\crm-extension
mkdir D:\EspoCRM-Production\chitu-connector\espocrm_sync
mkdir D:\EspoCRM-Production\chitu-connector\vendored\contracts
mkdir D:\EspoCRM-Production\chitu-connector\vendored\domain
mkdir D:\EspoCRM-Production\chitu-connector\vendored\config
mkdir D:\EspoCRM-Production\deployment\provisioning
mkdir D:\EspoCRM-Production\docs\architecture
mkdir D:\EspoCRM-Production\docs\workflow
mkdir D:\EspoCRM-Production\docs\sync-contracts
mkdir D:\EspoCRM-Production\docs\phase-reports
mkdir D:\EspoCRM-Production\docs\email-rules
mkdir D:\EspoCRM-Production\docs\testing
mkdir D:\EspoCRM-Production\tests
```

**Step 3: Copy Category A files**
```
# Extension package
Copy-Item -Recurse D:\Chitu-intelligence\espocrm_extension\* D:\EspoCRM-Production\crm-extension\

# Integration adapter
Copy-Item -Recurse D:\Chitu-intelligence\integration\espocrm_sync\* D:\EspoCRM-Production\chitu-connector\espocrm_sync\
Copy-Item D:\Chitu-intelligence\integration\__init__.py D:\EspoCRM-Production\chitu-connector\

# Vendored contracts
Copy-Item -Recurse D:\Chitu-intelligence\prospecting_engine\contracts\* D:\EspoCRM-Production\chitu-connector\vendored\contracts\
Copy-Item D:\Chitu-intelligence\prospecting_engine\domain\models.py D:\EspoCRM-Production\chitu-connector\vendored\domain\
Copy-Item D:\Chitu-intelligence\prospecting_engine\config\search_sources.py D:\EspoCRM-Production\chitu-connector\vendored\config\

# Provisioning
Copy-Item D:\Chitu-intelligence\integration\espocrm_sync\provisioning\phase3a33_provision_roles.php D:\EspoCRM-Production\deployment\provisioning\

# CRM docs (43 files)
Copy-Item -Recurse D:\Chitu-intelligence\docs\espocrm-extension\* D:\EspoCRM-Production\docs\phase-reports\

# Email operational docs (7 files)
Copy-Item D:\Chitu-intelligence\EMAIL_GENERATOR_V3_SPEC.md D:\EspoCRM-Production\docs\email-rules\
Copy-Item D:\Chitu-intelligence\EMAIL_WRITING_RULES_V3.md D:\EspoCRM-Production\docs\email-rules\
Copy-Item D:\Chitu-intelligence\EMAIL_DRAFT_PROMPT_V1.md D:\EspoCRM-Production\docs\email-rules\
Copy-Item D:\Chitu-intelligence\MULTI_PRODUCT_OUTREACH_RULE.md D:\EspoCRM-Production\docs\email-rules\
Copy-Item D:\Chitu-intelligence\lcd_email_v2_examples.md D:\EspoCRM-Production\docs\email-rules\
Copy-Item D:\Chitu-intelligence\OUTREACH_RESULTS_SCHEMA_V2.md D:\EspoCRM-Production\docs\email-rules\

# CRM tests (4 files)
Copy-Item D:\Chitu-intelligence\tests\test_espocrm_*.py D:\EspoCRM-Production\tests\
```

**Step 4: Fix import paths**

Update all `from integration.espocrm_sync` → `from chitu_connector.espocrm_sync` in:
- `chitu-connector/espocrm_sync/__init__.py`
- `chitu-connector/espocrm_sync/real_sync.py`
- `chitu-connector/espocrm_sync/real_client.py`
- `chitu-connector/espocrm_sync/client.py`
- `chitu-connector/espocrm_sync/gate.py`
- `chitu-connector/espocrm_sync/lifecycle.py`
- `chitu-connector/espocrm_sync/lifecycle_sync.py`
- `chitu-connector/espocrm_sync/email_lifecycle_sync.py`
- All 4 CRM test files

Update all `from prospecting_engine.` → `from chitu_connector.vendored.` in:
- `chitu-connector/espocrm_sync/models.py`
- `chitu-connector/espocrm_sync/real_sync.py`

Update vendored files to use relative imports:
- `chitu-connector/vendored/domain/models.py` imports `prospecting_engine.contracts.*` → `chitu_connector.vendored.contracts.*`
- `chitu-connector/vendored/contracts/website_research.py` imports `prospecting_engine.domain.models` → `chitu_connector.vendored.domain.models`

**Step 5: Organize docs**

Move docs from flat `phase-reports/` into subdirectories per §4.1. Create `docs/PROJECT.md` as CRM workspace README.

**Step 6: Verify build**
```
cd D:\EspoCRM-Production\crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension.zip
# Verify ZIP contains manifest.json and files/
```

**Step 7: Verify extension tests**
```
cd D:\EspoCRM-Production
python -m pytest crm-extension/tests/ -v
```

**Step 8: Verify connector imports**
```
cd D:\EspoCRM-Production
python -c "from chitu_connector.espocrm_sync import EspoCRMSyncMapper; print('OK')"
python -c "from chitu_connector.espocrm_sync.contract import SyncContractPayload; print('OK')"
python -c "from chitu_connector.vendored.domain.models import Candidate; print('OK')"
```

**Step 9: Create Chitu-intelligence-archive**
```
# Option A: Rename in-place (if Chitu development is frozen)
Rename-Item D:\Chitu-intelligence D:\Chitu-intelligence-archive

# Option B: Copy then clean up source
Copy-Item -Recurse D:\Chitu-intelligence D:\Chitu-intelligence-archive
# Then delete CRM-moved files from D:\Chitu-intelligence
```

**Step 10: Initialize git in EspoCRM-Production**
```
cd D:\EspoCRM-Production
git init
git add -A
git commit -m "Initial CRM production workspace — migrated from Chitu Intelligence

Source: D:\Chitu-intelligence
Source commit: <git rev-parse HEAD from Chitu-intelligence>
Migration audit: docs/phase-reports/PHASE3B00_2A_REPOSITORY_BOUNDARY_AUDIT.md"
```

---

## 7. Post-Migration Verification

### 7.1 Structural Verification

| Check | Command | Expected |
|---|---|---|
| Extension build works | `.\crm-extension\scripts\build_release_package.ps1 -OutputPath test.zip` | ZIP created with manifest.json + files/ |
| Extension tests pass | `python -m pytest crm-extension/tests/ -v` | All tests green |
| Connector imports resolve | `python -c "import chitu_connector"` | No ImportError |
| CRM tests pass | `python -m pytest tests/ -v` | All CRM tests green |
| No stale Chitu references | `grep -r "D:\\\\Chitu-intelligence" .` | No results |
| No stale prospecting_engine imports | `grep -r "from prospecting_engine" chitu-connector/` | No results (all updated to vendored) |
| Docs organized | `ls docs/` | Subdirectories: architecture, workflow, sync-contracts, phase-reports, email-rules, testing |

### 7.2 Functional Verification

| Check | Description |
|---|---|
| `LocalEspoCRMClient` instantiation | Construct client pointing to EspoCRM-Test; verify auth |
| Synthetic sync | Run `run_local_synthetic_sync()` against EspoCRM-Test |
| Lifecycle sync | Run `run_local_synthetic_lifecycle_sync()` against EspoCRM-Test |
| Email lifecycle sync | Run email lifecycle synthetic test |

---

## 8. Open Decisions

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | How to resolve `prospecting_engine` dependency? | A) Vendor contracts B) Shared package C) Keep monorepo D) Rewrite with dicts | **A — Vendor contracts** as immediate step (least risk). Phase B) as Phase 3B-03 follow-up. |
| **D2** | Package name for the sync adapter? | A) `chitu_connector` B) `espocrm_connector` C) `chitu_espocrm_bridge` | **A — `chitu_connector`** — names the producer, not the target. |
| **D3** | Import path convention after migration? | A) Flat: `from espocrm_sync import ...` B) Prefixed: `from chitu_connector.espocrm_sync import ...` | **B — Prefixed** — avoids name collisions, makes vendored status explicit. |
| **D4** | How to handle `__init__.py` in `integration/` (parent)? | A) Copy to `chitu-connector/` with updated imports B) Don't copy — it's empty | **B — Don't copy** if `__init__.py` is empty. Copy with updates if it has content. Currently: `integration/__init__.py` appears to be empty or minimal. |
| **D5** | Should Category C root docs (CLAUDE.md, ACTIVE_RULES.md, etc.) be COPIED to CRM or MOVED? | A) Copy (both repos get a version) B) Move (only CRM gets it) C) Leave in archive (CRM references archive) | **A — Copy** for CLAUDE.md and operational docs. Each repo needs its own CLAUDE.md. |
| **D6** | Archive strategy: rename in-place or copy-then-clean? | A) Rename (git mv) B) Copy (preserve original, clean up later) | **A — Rename** if Chitu work is frozen. **B — Copy** if Chitu may still need to run independently. |
| **D7** | Git history: start fresh or preserve? | A) Fresh `git init` in EspoCRM-Production B) `git filter-branch` to extract CRM subtree with history | **A — Fresh init** (simpler, cleaner). Note source commit hash in initial commit message for traceability. |

---

## Appendix A: Complete Category A File Inventory

### A1 — espocrm_extension/ (41 files)

```
espocrm_extension/
├── manifest.json
├── README.md
├── Resources/
│   ├── README.md
│   ├── acl/ResearchEvidence.json
│   ├── entityDefs/Lead.json
│   ├── entityDefs/Opportunity.json
│   ├── entityDefs/ResearchEvidence.json
│   ├── layouts/Lead/detail.json
│   ├── layouts/Lead/list.json
│   ├── layouts/Opportunity/detail.json
│   ├── layouts/ResearchEvidence/detail.json
│   ├── layouts/ResearchEvidence/list.json
│   └── metadata/README.md
├── application/README.md
├── custom/Espo/Modules/Prospecting/
│   ├── Api/README.md
│   ├── Controllers/README.md
│   ├── README.md
│   └── Services/README.md
├── docs/.gitkeep
├── files/custom/Espo/
│   ├── Custom/
│   │   ├── Controllers/ResearchEvidence.php
│   │   ├── Entities/ResearchEvidence.php
│   │   └── Resources/metadata/
│   │       ├── clientDefs/ResearchEvidence.json
│   │       ├── entityDefs/Lead.json
│   │       ├── entityDefs/ResearchEvidence.json
│   │       └── scopes/ResearchEvidence.json
│   └── Modules/Prospecting/
│       ├── Api/README.md
│       ├── Classes/Select/Lead/PrimaryFilters/
│       │   ├── PeRecentlySynced.php
│       │   └── PeTierA.php
│       ├── Controllers/
│       │   ├── README.md
│       │   └── ResearchEvidence.php
│       ├── Entities/ResearchEvidence.php
│       ├── Resources/
│       │   ├── module.json
│       │   ├── i18n/en_US/
│       │   │   ├── Lead.json
│       │   │   ├── Opportunity.json
│       │   │   └── ResearchEvidence.json
│       │   ├── layouts/
│       │   │   ├── Lead/detail.json
│       │   │   ├── Lead/list.json
│       │   │   ├── Opportunity/detail.json
│       │   │   ├── ResearchEvidence/detail.json
│       │   │   └── ResearchEvidence/list.json
│       │   └── metadata/
│       │       ├── aclDefs/ResearchEvidence.json
│       │       ├── app/layouts.json
│       │       ├── clientDefs/Lead.json
│       │       ├── clientDefs/ResearchEvidence.json
│       │       ├── entityDefs/Lead.json
│       │       ├── entityDefs/Opportunity.json
│       │       ├── entityDefs/ResearchEvidence.json
│       │       ├── scopes/ResearchEvidence.json
│       │       └── selectDefs/Lead.json
│       └── Services/README.md
├── scripts/
│   ├── README.md
│   └── build_release_package.ps1
└── tests/
    ├── README.md
    ├── __init__.py
    └── test_extension_skeleton.py
```

### A2 — integration/espocrm_sync/ (15 files)

```
integration/
├── __init__.py
└── espocrm_sync/
    ├── __init__.py
    ├── audit.py
    ├── client.py
    ├── contract.py
    ├── email_lifecycle.py
    ├── email_lifecycle_sync.py
    ├── gate.py
    ├── idempotency.py
    ├── lifecycle.py
    ├── lifecycle_sync.py
    ├── mapper.py
    ├── models.py
    ├── real_client.py
    ├── real_sync.py
    └── provisioning/
        └── phase3a33_provision_roles.php
```

### A3 — Vendored contracts (10 files)

```
prospecting_engine/
├── contracts/
│   ├── __init__.py
│   ├── business_qualification.py
│   ├── canonical_score.py
│   ├── entity_identity.py
│   ├── icp.py
│   ├── scoring.py
│   ├── search_result.py
│   ├── single_candidate_loop.py
│   └── website_research.py
├── domain/
│   └── models.py
└── config/
    └── search_sources.py
```

### A4 — CRM Tests (4 files)

```
tests/
├── test_espocrm_real_client.py
├── test_espocrm_sync_adapter.py
├── test_espocrm_lifecycle_sync.py
└── test_espocrm_email_lifecycle.py
```

### A5 — CRM Documentation (50 files)

43 files from `docs/espocrm-extension/` + 7 root-level CRM docs (see §2.5 for complete list).

---

## Appendix B: Category C Items Requiring Review

| Item | Concern | Suggested Disposition |
|---|---|---|
| `CLAUDE.md` | Contains both Chitu AND CRM rules | Copy to both repos; edit each to contain only its scope |
| `ACTIVE_RULES.md` | Mixed content | Copy; edit each version |
| `START_HERE.md` | Mixed onboarding | Keep in archive; write new CRM-specific START_HERE.md |
| `README.md` | Mixed project overview | Keep in archive; write new CRM README.md |
| `PRODUCT_INTELLIGENCE_V2.md` | Referenced by email + scoring | Copy to CRM docs/email-rules/ |
| `.env.example` | Mixed env vars | Split: CRM env vars → CRM deployment/; archive keeps original |
| `.gitignore` | Mixed patterns | Copy; adapt CRM version |
| `integration/__init__.py` | Package init for `integration` namespace | Verify empty; if so, skip. If has content, copy to `chitu-connector/`. |
| `.agents/` | Agent definitions | Review for CRM-specific agents; copy relevant ones |
| `.claude/` | Claude settings | Each repo needs its own `.claude/`. Copy and customize for CRM. |
| `.github/workflows/` | CI/CD | Review for CRM-specific workflows; split if needed |
| Root `*_REPORT*.md` files (~12) | Mixed topic reports | Classify by reading content: if CRM topic → Category A; if Chitu topic → Category B |

---

## Appendix C: Excluded Items (Category X)

| Path | Reason |
|---|---|
| `.venv-deep-research/` | Python virtual environment |
| `node_modules/` | npm dependencies |
| `__pycache__/` (all) | Python bytecode cache |
| `.playwright-mcp/` | Browser session data |
| `.phase1-patch/` | Historical patch artifacts |
| `.phase1-staging/` | Historical staging artifacts |
| `logs/` | Runtime logs |
| `temp/` | Temporary files |
| `data/` | Runtime data with possible secrets |
| `.env` | Contains secrets |
| `debug*.py`, `test_db.py`, `test_*.py` (root-level) | Debug/test scripts |
| `tmp_*.py`, `tmp_*.txt` | Temporary fix scripts |
| `*.patch`, `*.diff` | Historical patches |
| `.codex_spreadsheet_build/` | Build artifacts |

---

*End of Phase3B00.2A Repository Boundary Audit V1*
