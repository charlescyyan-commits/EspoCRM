# System Boundaries

**Status:** Static Verified from code and phase audits

## 1. CRM Extension ↔ Chitu Connector

| Boundary | CRM Extension owns | Connector owns |
|----------|-------------------|----------------|
| Record storage | Lead, ResearchEvidence, SearchJob, etc. | Nothing persistent |
| HTTP surface | `/Prospecting/*` Action classes | HTTP client (`ProspectingConnectorClient`) |
| Contract enforcement | `ChituSyncService::payload()` requires `contract_version 1.0` | `validate_sync_contract()`, `evaluate_sync_gate()` |
| ACL | EspoCRM ACL on all scopes | API key authentication on outbound requests |

**Rule:** Connector never writes SQL or PHP metadata. Extension never imports Python.

## 2. Connector ↔ Runtime AI / Engine

| Item | Status |
|------|--------|
| Vendored contracts in `chitu_connector/vendored/` | **Implemented** |
| Live Engine / DeepSeek / crawler runtime | **Out of scope** — must not be imported |
| Scoring logic changes | **Forbidden** per `AGENTS.md` / `CLAUDE.md` |

Connector accepts **already materialized** contract JSON or `SyncSource` objects built in tests.

## 3. Search Strategy ↔ Discovery Provider

| Layer | Responsibility | Status |
|-------|----------------|--------|
| SearchStrategy | Planning: product, country, personas, keywords, sourcePlan | **Implemented** (CRM) |
| SearchJob | Executable query unit with fingerprint dedupe | **Implemented** (CRM) |
| SearchProvider protocol | External search execution | **Contract defined** (`acquisition/provider.py`) |
| FakeSearchProvider | Test double | **Implemented** |
| Google / Apify / live providers | Production discovery | **Not Implemented** |

`SearchStrategyService` does **not** call HTTP. It only creates `SearchJob` rows.

## 4. Worker Core ↔ REST Adapter

| Component | Location | Status |
|-----------|----------|--------|
| `AcquisitionWorker` | `acquisition/worker.py` | **Implemented** |
| `AcquisitionStore` protocol | `acquisition/worker.py` | **Contract defined** |
| In-memory / test stores | Worker tests | **Static Verified** |
| `EspoAcquisitionRepository` | `acquisition/espo_repository.py` | **Implemented** (GET-then-PUT MVP) |
| Atomic claim API on CRM | Optional `POST /SearchJob/{id}/claim` | **Not Implemented** (design option; adapter uses REST PUT) |

Worker never performs unconditional RUNNING transition; claim semantics are delegated to the store.

## 5. Acquisition ↔ CRM Lead Sync

| Link | Status |
|------|--------|
| SearchJob → ProspectPool (worker) | **Implemented** in connector (`runner.py` + `espo_repository.py`); **Runtime Verified** deferred |
| ProspectPool → Lead (`ChituSyncService`) | **Not Implemented** — zero references in `ChituSyncService` |
| Engine → Lead (direct sync) | **Implemented** — independent path |

These are **intentionally separate** pipelines per Phase 3C02.2A audit.

## 6. Opportunity Boundary

| Rule | Enforcement |
|------|-------------|
| No automatic Opportunity creation | `syncOpportunityProposal` updates Lead fields only when score ≥ 80 |
| Default action | `peProposalAction = NO_AUTOMATIC_OPPORTUNITY` |
| API response | `'action' => 'NO_AUTOMATIC_OPPORTUNITY'` |
| Test guard | `test_extension_skeleton.py` asserts no `getEntity('Opportunity')` in `ChituSyncService` |

Human users may still create Opportunities manually in native EspoCRM.

## 7. Email Content Boundary

| Stored | Not stored |
|--------|------------|
| `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` | `peEmailSubject`, `peEmailBody` |
| `EmailEvent` metadata (type, campaign, timestamp) | Full message HTML/text |

**Evidence:** `test_phase3a27_email_status_integration_metadata` in `test_extension_skeleton.py`.

## 8. Research Evidence Boundary

- CRM stores compact evidence fields (`peClaim`, `peSourceUrl`, `peEvidenceText`, etc.)
- Contract forbids copying raw crawler payloads, credentials, or debug HTML (see sync contract boundary doc)
- `ResearchEvidence` relationship panel: create disabled in UI (`create: false`)

## 9. Dependency on Legacy Chitu Runtime

| Check | Result |
|-------|--------|
| `prospecting_engine/` in repo | Absent |
| Extension overlaps `app/` or `revenue_system/` | Test-enforced forbidden |
| Connector imports Chitu app | Uses `vendored/` only |

This workspace is a **cutover boundary** from in-app CRM integration to extension + connector.

## 10. Deployment / Production Boundary

- `deployment/provisioning/*.php` scripts exist but require **manual** execution on an approved CRM instance
- `deployment/README.md`: no production credentials extracted
- Phase reports document runtime verification on disposable instances only

## Related Documents

- [DATA_FLOW.md](DATA_FLOW.md)
- [../sync-contracts/ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md](../sync-contracts/ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md)
- [../PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md](../PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md)
