# REST Endpoints

**Status:** Static Verified from `crm-extension/Resources/routes.json`  
**Base path:** EspoCRM API root + route (authenticated with `X-Api-Key`)

All custom Prospecting routes are registered in both `crm-extension/Resources/routes.json` and the installed module copy under `files/custom/.../Resources/routes.json`.

## Custom Prospecting Routes

### POST `/Prospecting/sync/lead`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Create or update Lead from sync contract by `identity.candidate_id` → `peCandidateId` |
| **Action class** | `Espo\Modules\Prospecting\Api\PostSyncLead` |
| **Service** | `ChituSyncService::syncLead` |
| **Auth** | EspoCRM API key + ACL (`Lead` create/edit) |
| **Request** | JSON body; `contract_version` must be `"1.0"` |
| **Response** | `{ success, created, updated, external_id, crm_id }` |
| **Failure** | `400` BadRequest (contract), `403` Forbidden, `409` Conflict (duplicate external ID) |
| **Status** | **Implemented** |

### POST `/Prospecting/sync/evidence`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Create `ResearchEvidence` rows linked to existing Lead |
| **Action class** | `PostSyncEvidence` |
| **Service** | `ChituSyncService::syncEvidence` |
| **Request** | Same contract envelope; `evidence[]` required |
| **Response** | `{ success, created, crm_ids[], evidence_count, ... }` |
| **Failure** | `404` if Lead not found; `403` if ACL denies |
| **Status** | **Implemented** |

### POST `/Prospecting/sync/opportunity-proposal`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Project proposal fields onto Lead when score ≥ 80 |
| **Action class** | `PostSyncOpportunityProposal` |
| **Service** | `ChituSyncService::syncOpportunityProposal` |
| **Response** | Includes `action: NO_AUTOMATIC_OPPORTUNITY` when eligible |
| **Constraint** | Does **not** create Opportunity records |
| **Status** | **Implemented** |

### POST `/Prospecting/feedback/sync`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Upsert `SalesFeedback`; hook creates `LearningSignal` |
| **Action class** | `PostSyncFeedback` |
| **Service** | `FeedbackSyncService::sync` |
| **Required fields** | `lead_id`, `feedback_type`, `outcome`, `timestamp` |
| **Status** | **Implemented** |

### POST `/Prospecting/brevo/email-event`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Append-only `EmailEvent` ingestion (does not send email) |
| **Action class** | `PostSyncBrevoEmailEvent` |
| **Service** | `BrevoEmailEventSyncService::sync` |
| **Required fields** | `lead_id`, `message_id`, `event_type`, `timestamp` |
| **Dedup** | `externalMessageId` + `eventType` |
| **Status** | **Implemented** |

### POST `/Prospecting/search-strategy/generate-jobs`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Expand `SearchStrategy` into deduplicated `SearchJob` rows |
| **Action class** | `PostGenerateSearchStrategyJobs` |
| **Service** | `SearchStrategyService::generate` |
| **Request** | `{ "strategyId": "<id>" }` |
| **Response** | `{ success, strategy_id, status, generated_count, existing_count, generated_job_count, max_jobs }` |
| **Limits** | Max 40 jobs (`SearchStrategyTemplates::MAX_JOBS`) |
| **Status** | **Implemented** |

## Standard EspoCRM REST (Used by Connector Runner)

**Status:** Implemented — used by `EspoAcquisitionRepository`, not custom Prospecting routes.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `SearchJob/{id}` | Fetch job for claim pre-check |
| PUT | `SearchJob/{id}` | Claim (`RUNNING`) and complete job |
| GET | `ProspectPool` | Query by `source` + `website` for dedupe |
| POST | `ProspectPool` | Insert discovery prospect |

**Source:** `chitu-connector/chitu_connector/acquisition/espo_repository.py`

**CAS / ETag:** **Not Implemented** — adapter uses GET-then-PUT with post-write verification (single-runner MVP).

## Native Entity CRUD

SearchStrategy, SearchJob, ProspectPool, Lead, ResearchEvidence, etc. are also available through standard EspoCRM Record API when scopes permit. Custom routes above are the **connector integration surface**.

## Related Documents

- [CONNECTOR_API.md](CONNECTOR_API.md)
- [WEBHOOKS.md](WEBHOOKS.md)
- [../sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json](../sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json)
