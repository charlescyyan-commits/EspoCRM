# Project Structure

**Status:** Static Verified

See also [../architecture/DIRECTORY_STRUCTURE.md](../architecture/DIRECTORY_STRUCTURE.md).

## Top-Level Directories

| Path | Role |
|------|------|
| `crm-extension/` | EspoCRM extension package source |
| `chitu-connector/` | Python connector and acquisition worker |
| `deployment/` | Release ZIPs, provisioning PHP, validation tests |
| `docs/` | Documentation center and phase reports |

## `crm-extension` Key Paths

| Path | Installed? | Notes |
|------|------------|-------|
| `manifest.json` | Yes | Version `1.9.5-alpha` (version authority) |
| `files/custom/Espo/Modules/Prospecting/` | Yes | Module API/controllers/entities/services plus native metadata, layouts, and i18n |
| `files/client/custom/src/` | Yes | Native Prospecting controllers, handlers, and views |
| `Resources/` | No | Design mirror; parity-tested |
| `tests/` | No | `unittest` skeleton |

## `chitu-connector` Key Paths

| Path | Purpose |
|------|---------|
| `chitu_connector/espocrm_sync/` | Sync client, mapper, gate, feedback, Brevo |
| `chitu_connector/acquisition/worker.py` | Worker core |
| `chitu_connector/acquisition/runner.py` | CLI single-job runner |
| `chitu_connector/acquisition/espo_repository.py` | EspoCRM REST adapter |
| `chitu_connector/vendored/` | Stable contract copies only |
| `tests/` | Connector and worker tests |

## `deployment` Key Paths

| Path | Purpose |
|------|---------|
| `prospecting-extension-*.zip` | Release artifacts |
| `provisioning/*.php` | Roles, dashboards, synthetic data |
| `validation/*.py` | Live CRM acceptance tests |

## Documentation Areas

| Path | Content |
|------|---------|
| `docs/architecture/` | System design (D01) |
| `docs/api/` | API reference (D01) |
| `docs/phase-reports/` | Historical phase archive |
| `docs/sync-contracts/` | JSON contract and boundaries |
| `docs/PHASE3*.md` | Root-level phase reports (not moved) |

## Out of Scope Paths

Not present or forbidden in this workspace:

- `app/`, `prospecting_engine/`, `revenue_system/`
- EspoCRM core `application/Espo/`

## Related Documents

- [GETTING_STARTED.md](GETTING_STARTED.md)
- [CODING_GUIDELINES.md](CODING_GUIDELINES.md)
