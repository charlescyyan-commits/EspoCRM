# Directory Structure

**Status:** Static Verified — reflects repository as scanned for Phase D01

```text
EspoCRM-Production/
├── crm-extension/          # EspoCRM extension source (installable package)
│   ├── manifest.json
│   ├── Resources/            # Design-surface metadata (review + parity tests)
│   ├── files/                # Content copied into EspoCRM on install
│   │   ├── custom/Espo/Modules/Prospecting/
│   │   └── client/custom/src/   # SearchStrategy UI handlers
│   ├── custom/               # Placeholder READMEs (not installed)
│   ├── scripts/              # build_release_package.ps1
│   └── tests/                # Offline extension skeleton tests
├── chitu-connector/          # Python connector + worker core
│   ├── chitu_connector/
│   │   ├── espocrm_sync/
│   │   ├── acquisition/
│   │   └── vendored/
│   └── tests/
├── deployment/               # ZIP artifacts, provisioning, validation
│   ├── provisioning/
│   ├── validation/
│   └── prospecting-extension-*.zip
├── docs/                     # Documentation center (this tree)
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   ├── developer/
│   ├── user-guide/
│   ├── testing/
│   ├── release/
│   ├── reports/
│   ├── adr/
│   ├── diagrams/
│   ├── phase-reports/        # Historical phase archive
│   ├── sync-contracts/
│   ├── workflow/
│   └── email-rules/
├── AGENTS.md                 # Workspace agent rules (not modified by D01)
└── CLAUDE.md                 # Workspace instructions (not modified by D01)
```

## `crm-extension` Detail

| Path | Installed to EspoCRM? | Purpose |
|------|----------------------|---------|
| `manifest.json` | Yes (ZIP root) | Extension identity and version |
| `files/custom/.../Prospecting/` | Yes | Module PHP, metadata, layouts, i18n |
| `files/client/custom/...` | Yes | Client JS (e.g. SearchStrategy generate-jobs) |
| `Resources/` | No | Mirror for review; must match module metadata in tests |
| `custom/` (top-level) | No | Documentation placeholders |
| `tests/` | No | `unittest` validation |
| `scripts/` | No | ZIP build script |

## `chitu-connector` Detail

| Path | Purpose |
|------|---------|
| `chitu_connector/espocrm_sync/` | Sync contract validation, mapping, REST client |
| `chitu_connector/acquisition/` | Worker core, models, fake provider |
| `chitu_connector/vendored/` | Vendored stable interfaces (no Chitu app import) |
| `tests/` | Connector and worker unit tests |

**Present (Phase 3C02.2C):**

- `chitu_connector/acquisition/runner.py`
- `chitu_connector/acquisition/espo_repository.py`

## `deployment` Detail

| Path | Purpose |
|------|---------|
| `prospecting-extension-<version>.zip` | Release artifacts |
| `*.zip.sha256` | Checksum sidecars |
| `provisioning/*.php` | Role, dashboard, synthetic data scripts |
| `validation/*.py` | Live CRM acceptance tests |
| `README.md` | States `railway/`, `docker/`, `backup/` are intentional empty boundaries |

## `docs` Detail

New Phase D01 categories live alongside historical content. Root-level `PHASE3*.md` files are **not relocated** to preserve existing links.

## Paths That Do Not Exist in This Repository

The following are referenced in early phase docs but are **not** present in this workspace:

- `espocrm_extension/` (renamed to `crm-extension/`)
- `app/`, `prospecting_engine/`, `revenue_system/` (Chitu application trees — out of scope)
- EspoCRM core `application/Espo/`

## Related Documents

- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
- [../developer/PROJECT_STRUCTURE.md](../developer/PROJECT_STRUCTURE.md)
