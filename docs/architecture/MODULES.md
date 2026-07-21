# Modules

**Status:** Static Verified from repository layout

## `crm-extension` — Chitu Prospecting Integration

| Attribute | Value |
|-----------|-------|
| **Path** | `crm-extension/` |
| **Package name** | Chitu Prospecting Integration |
| **Version** | `1.9.7-alpha` (`manifest.json`) |
| **Runtime** | EspoCRM PHP module `Prospecting` |
| **Packaged baseline** | `1.9.7-alpha`; C16.1A entity skeleton is packaged, while C16 workflows remain in development |

### Inputs

- Extension ZIP install into EspoCRM `custom/`
- HTTP POST bodies on `/Prospecting/*` routes (sync, feedback, Brevo events, generate-jobs)
- EspoCRM UI CRUD on Prospecting entities

### Outputs

- CRM records: Lead, ResearchEvidence, SearchStrategy, SearchJob, ProspectPool, SalesFeedback, LearningSignal, EmailEvent
- Workflow side effects: Lead/EmailEvent hooks create Tasks; SalesFeedback hook creates LearningSignal
- JSON API responses from custom Action classes

### Dependencies

- EspoCRM `>=7.4.0`, PHP `>=8.1`
- No dependency on `chitu-connector` at PHP runtime

### Should not

- Call external search providers
- Store full email bodies (`peEmailSubject` / `peEmailBody` are absent by design)
- Auto-create Opportunities (`ChituSyncService` sets `peProposalAction = NO_AUTOMATIC_OPPORTUNITY`)
- Import Chitu application runtime code

---

## `chitu-connector` — Python Connector

| Attribute | Value |
|-----------|-------|
| **Path** | `chitu-connector/` |
| **Runtime** | Python library + single-job CLI (`runner.py`) |
| **Current phase** | Sync adapter + Acquisition Worker Core (3C02.2B) |

### Submodules

| Submodule | Path | Status |
|-----------|------|--------|
| `espocrm_sync` | `chitu_connector/espocrm_sync/` | **Implemented** — REST client, mapper, gate, lifecycle helpers |
| `acquisition` | `chitu_connector/acquisition/` | **Partial** — worker, runner, `EspoAcquisitionRepository`, fake provider; real search providers **Not Implemented** |
| `vendored` | `chitu_connector/vendored/` | **Implemented** — copied stable contracts only |

### Inputs

- `SyncContractPayload` / `SyncSource` objects
- Environment: `ESPOCRM_BASE_URL`, `ESPOCRM_API_KEY` (for live client tests only)
- Injectable `AcquisitionStore` + `SearchProvider` for worker tests

### Outputs

- HTTP requests to EspoCRM `/Prospecting/*` endpoints
- `ConnectorSyncResult`, feedback/Brevo API results
- `JobExecutionResult` from worker (in test or future runner context)

### Dependencies

- Standard library + package-local vendored contracts
- Must **not** import Chitu application trees (`app/`, `prospecting_engine/`, etc.)

### Should not

- Modify EspoCRM metadata directly
- Embed scoring or research logic (uses vendored interfaces only)
- Send email (Brevo service is event ingestion only)

---

## `deployment` — Packaging and Provisioning

| Attribute | Value |
|-----------|-------|
| **Path** | `deployment/` |
| **Runtime** | Manual scripts; **not** auto-executed by CI in this repo |

### Contents

| Area | Purpose |
|------|---------|
| `prospecting-extension-*.zip` | Versioned extension packages + `.sha256` sidecars |
| `provisioning/*.php` | One-off EspoCRM role/dashboard/test-data scripts |
| `validation/*.py` | Browser/API acceptance tests (require live CRM) |

### Should not

- Store production credentials (per `deployment/README.md`)
- Be run against production without explicit approval

---

## `docs` — Documentation and Phase Reports

Historical phase reports, sync contracts, workflow specs, and this documentation center. Not installed into EspoCRM.

---

## Cross-Module Data Ownership

| Data | Owner | Consumer |
|------|-------|----------|
| Lead `pe*` fields | CRM extension (projection from contract) | Connector sync client |
| ResearchEvidence | CRM extension | Connector sync client |
| SearchJob queue state | CRM extension (metadata) | Future worker adapter |
| ProspectPool records | CRM extension (metadata) | Future worker adapter |
| Scoring / research | External engine (out of repo) | Connector via contract JSON only |

## Related Documents

- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
- [BOUNDARIES.md](BOUNDARIES.md)
- [../api/CONNECTOR_API.md](../api/CONNECTOR_API.md)
