# Data Flow

**Status:** Mixed — sync path **Implemented**; acquisition runner **Implemented** (fake provider + Espo REST adapter, static tests); live multi-runner and real providers **Not Implemented**

## 1. Chitu Sync Pipeline (Implemented)

One-way intelligence projection from connector to CRM.

```mermaid
sequenceDiagram
  participant Engine as External Engine
  participant Conn as chitu-connector
  participant API as EspoCRM /Prospecting/*
  participant CRM as Lead / ResearchEvidence

  Engine->>Conn: SyncSource / contract JSON
  Conn->>Conn: validate_sync_contract + gate
  Conn->>API: POST /Prospecting/sync/lead
  API->>CRM: Upsert Lead by peCandidateId
  Conn->>API: POST /Prospecting/sync/evidence
  API->>CRM: Create ResearchEvidence rows
  Conn->>API: POST /Prospecting/sync/opportunity-proposal
  API->>CRM: Update Lead proposal fields only
  Note over CRM: peProposalAction = NO_AUTOMATIC_OPPORTUNITY
```

**Source files:**

- Connector: `chitu-connector/chitu_connector/espocrm_sync/connector_api.py`
- CRM: `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`

**Contract version:** `contract_version: "1.0"` required by `ChituSyncService::payload()`.

## 2. Feedback Loop (Implemented)

```mermaid
sequenceDiagram
  participant Conn as chitu-connector
  participant API as POST /Prospecting/feedback/sync
  participant SF as SalesFeedback
  participant LS as LearningSignal

  Conn->>API: feedback payload
  API->>SF: Upsert by externalFeedbackId
  API->>LS: Hook creates LearningSignal
```

**CRM hook:** `SalesFeedbackLearningSignalHook.php` (referenced by tests).

## 3. Brevo Email Events (Implemented)

Append-only event ingestion — **does not send email**.

```mermaid
sequenceDiagram
  participant Brevo as Brevo / Connector
  participant API as POST /Prospecting/brevo/email-event
  participant EE as EmailEvent
  participant L as Lead

  Brevo->>API: message_id, event_type, timestamp
  API->>EE: Dedupe by externalMessageId + eventType
  EE->>L: EmailEventWorkflowHook updates peEmailStatus, Tasks
```

**Note:** This is a custom REST ingestion endpoint, not a generic EspoCRM webhook framework.

## 4. Search Strategy → Search Jobs (Implemented)

```mermaid
flowchart TD
  A[User creates SearchStrategy] --> B[UI: Generate Jobs action]
  B --> C[POST /Prospecting/search-strategy/generate-jobs]
  C --> D[SearchStrategyService.expand]
  D --> E{Dedupe by queryFingerprint}
  E -->|new| F[Create SearchJob status=QUEUED]
  E -->|exists| G[Skip create, count existing]
  F --> H[SearchStrategy status=GENERATED]
  G --> H
```

**Limits:** Max 40 jobs per expansion (`SearchStrategyTemplates::MAX_JOBS`).

## 5. Acquisition Worker (Partial)

**Worker Core — Implemented** (`chitu_connector/acquisition/worker.py`):

```mermaid
flowchart TD
  SJ[SearchJob QUEUED] --> W[AcquisitionWorker.execute_job]
  W --> C[store.claim_search_job expected_status=QUEUED]
  C -->|claimed| P[SearchProvider.search]
  P --> N[normalize_candidate]
  N --> PP[store.create_prospect]
  PP --> U[store.update_search_job COMPLETED]
  C -->|not claimed| NC[NOT_CLAIMED result]
```

**EspoCRM adapter — Implemented (MVP, fake provider only):**

- `EspoAcquisitionRepository` in `chitu-connector/chitu_connector/acquisition/espo_repository.py`
- CLI: `python -m chitu_connector.acquisition.runner run-job --job-id <id> --provider fake`
- Uses standard EspoCRM REST (`GET/PUT SearchJob`, `POST ProspectPool`) with GET-then-PUT claim
- **Runtime Verified:** deferred per [PHASE3C02_2C_JOB_RUNNER_REPORT.md](../PHASE3C02_2C_JOB_RUNNER_REPORT.md)
- Design background: [PHASE3C02_2C_JOB_RUNNER_DESIGN.md](../PHASE3C02_2C_JOB_RUNNER_DESIGN.md)

## 6. ProspectPool → Lead (Not Implemented)

`ProspectPool` has `crmPushStatus` and queue stages (`DISCOVERY` → `CRM`) but:

- No PHP service bridges ProspectPool to `ChituSyncService`
- No worker writes ProspectPool from search results in production code path
- Audit: [PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md](../PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md)

## 7. Explicitly Forbidden Automatic Behaviors

| Behavior | Status | Evidence |
|----------|--------|----------|
| Auto-create Opportunity from proposal | **Blocked** | `ChituSyncService::syncOpportunityProposal` sets `NO_AUTOMATIC_OPPORTUNITY`; tests assert no `getEntity('Opportunity')` |
| Store full email body on Lead | **Not stored** | `peEmailSubject` / `peEmailBody` absent from Lead entityDefs |
| CRM → Engine score writeback | **Out of scope** | Sync contract boundary V1 |
| Old Chitu-intelligence runtime in CRM | **Not used** | Extension tests assert no `prospecting_engine/` overlap |

## 8. CAS / ETag (Not Implemented)

`AcquisitionStore` documents optional `expected_version` for future compare-and-set. No EspoCRM ETag or atomic claim API exists in `crm-extension` routes today. C02.2C design allows GET-then-PUT for single-runner MVP.

## Related Documents

- [BOUNDARIES.md](BOUNDARIES.md)
- [../api/REST_ENDPOINTS.md](../api/REST_ENDPOINTS.md)
- [../sync-contracts/ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md](../sync-contracts/ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md)
