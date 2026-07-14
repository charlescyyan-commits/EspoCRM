# Connector API

**Status:** Implemented (Python client) — maps to CRM `/Prospecting/*` routes  
**Package:** `chitu-connector/chitu_connector/espocrm_sync/`

## Overview

The connector is a **client library**, not a standalone HTTP server. It validates sync contracts and calls EspoCRM custom API actions.

## Primary Client

**Class:** `ProspectingConnectorClient`  
**Source:** `chitu-connector/chitu_connector/espocrm_sync/connector_api.py`

### Construction

```python
ProspectingConnectorClient(base_url: str, api_key: str, timeout_seconds: float = 15.0)
```

- `base_url` — absolute HTTP(S) EspoCRM root (no trailing slash required)
- `api_key` — EspoCRM API key (never log or commit)

## Sync Methods

| Method | CRM route | Purpose | Status |
|--------|-----------|---------|--------|
| `sync_lead(payload)` | `POST /Prospecting/sync/lead` | Upsert Lead by `peCandidateId` | **Implemented** |
| `sync_evidence(payload)` | `POST /Prospecting/sync/evidence` | Create ResearchEvidence rows | **Implemented** |
| `sync_opportunity_proposal(payload)` | `POST /Prospecting/sync/opportunity-proposal` | Project proposal fields; **no Opportunity create** | **Implemented** |
| `sync_source(source)` | All three above in sequence | Full pipeline with validation + gate | **Implemented** |

### `sync_source` Pipeline

1. `EspoCRMSyncMapper().build(source)` → `SyncContractPayload`
2. `validate_sync_contract()` — reject on schema errors
3. `evaluate_sync_gate()` — business gate (see `gate.py`)
4. Sequential POST: lead → evidence → proposal

Returns `ConnectorSyncResult` with per-step `ConnectorSyncStep` status.

## Related API Modules

| Module | File | Purpose | Status |
|--------|------|---------|--------|
| Feedback | `feedback_api.py` | `POST /Prospecting/feedback/sync` | **Implemented** |
| Brevo events | `brevo_api.py` | `POST /Prospecting/brevo/email-event` | **Implemented** |
| Lifecycle | `lifecycle_sync.py`, `email_lifecycle_sync.py` | Higher-level orchestration | **Implemented** |
| Real client | `real_client.py` | Live CRM integration tests | **Implemented** (test-only usage) |

## Contract

- JSON schema: `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json`
- Boundary rules: `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md`
- Required field: `contract_version: "1.0"` (enforced by CRM `ChituSyncService`)

## Acquisition Worker (Separate Module)

**Not part of `ProspectingConnectorClient`.**

| Component | Path | Status |
|-----------|------|--------|
| `AcquisitionWorker` | `chitu_connector/acquisition/worker.py` | **Implemented** |
| `AcquisitionStore` | Protocol in `worker.py` | **Contract defined** |
| `EspoAcquisitionRepository` | `acquisition/espo_repository.py` | **Implemented** |
| `runner` CLI | `acquisition/runner.py` | **Implemented** (`--provider fake` only) |

## Failure Behavior

| Error | Behavior |
|-------|----------|
| Invalid contract | `ConnectorSyncResult.success = False`; validation step rejected |
| Gate rejection | Gate step rejected; no CRM writes |
| HTTP 4xx/5xx | `ConnectorApiError` or failed step with CRM error body |
| Missing API key at construct | `ConnectorApiError` |

## Tests

| Test module | Approx. tests | Scope |
|-------------|---------------|-------|
| `test_espocrm_connector_api.py` | 11 | Client behavior |
| `test_espocrm_sync_adapter.py` | 24 | Mapper + adapter |
| `test_espocrm_feedback_api.py` | 2 | Feedback |
| `test_espocrm_brevo_api.py` | 2 | Brevo |
| `test_phase3c02_2b_acquisition_worker_core.py` | 10 | Worker core |
| `test_phase3c02_2b1_worker_persistence_hardening.py` | 8 | Persistence hardening |
| `test_phase3c02_2c_job_runner.py` | 13 | Job runner + Espo repository |
| Others (lifecycle, email, real client) | 19 | Various connector tests |
| **Total** | **89** | Phase D01 verified count |

## Related Documents

- [REST_ENDPOINTS.md](REST_ENDPOINTS.md)
- [../architecture/BOUNDARIES.md](../architecture/BOUNDARIES.md)
- [../sync-contracts/ESPOCRM_SYNC_RULES_V1.md](../sync-contracts/ESPOCRM_SYNC_RULES_V1.md)
