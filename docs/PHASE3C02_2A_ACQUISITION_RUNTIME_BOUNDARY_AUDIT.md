# Phase3C02.2A — Acquisition / Search Discovery Runtime Boundary Audit

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Type:** Read-Only Architecture Audit  
**Verdict:** PASS — All critical boundaries confirmed; no blockers for follow-up implementation

---

## 1. Executive Verdict

The Acquisition/Search Discovery system is a **metadata-complete, function-incomplete** workspace. Three entities (`SearchStrategy`, `SearchJob`, `ProspectPool`) are fully defined with entity definitions, controllers, services, ACL, layouts, dashlets, and a `generate-jobs` API — but the runtime execution path stops at SearchJob creation. No code currently calls an external search provider, creates ProspectPool records from search results, or automatically converts any acquisition entity into a CRM Lead.

**What works today:**
- `SearchStrategy` CRUD via EspoCRM UI and API
- `POST /Prospecting/search-strategy/generate-jobs` — expands a SearchStrategy into SearchJob records with SHA-256 fingerprint deduplication
- `SearchJob` and `ProspectPool` CRUD via EspoCRM UI and API
- All three entities have ACL enforcement, dashlet widgets, and filter presets

**What does NOT exist:**
- Any external search execution (no HTTP call to Google, Apify, or any search provider)
- Any automatic ProspectPool creation from SearchJob results
- Any automatic Lead creation from ProspectPool
- Any bridge between the Acquisition entities and `ChituSyncService`
- Any worker/daemon/queue consumer that processes SearchJobs

**Architectural boundary assessment:** The design correctly separates concerns — SearchStrategy/Job define "what to search," ProspectPool holds "raw search results," and ChituSyncService/connector handle "pushing qualified candidates to CRM Leads." The missing piece is the runtime that connects them: a worker that reads QUEUED SearchJobs, calls an external provider, writes results to ProspectPool, and then optionally triggers ChituSync.

---

## 2. Current Architecture Map

```
┌─────────────────────────────────────────────────────────────┐
│                    ESPOCRM (PHP Runtime)                      │
│                                                               │
│  ┌──────────────────┐    generates     ┌──────────────────┐  │
│  │  SearchStrategy  │ ──────────────→  │    SearchJob     │  │
│  │                  │  (1:N via API)   │                  │  │
│  │  - product       │                  │  - keyword       │  │
│  │  - country       │                  │  - country       │  │
│  │  - targetPersona │                  │  - source        │  │
│  │  - sourcePlan    │                  │  - status        │  │
│  │  - keywords      │                  │  - queryFingerprint │
│  │  - status        │                  │  - resultCount   │  │
│  └──────────────────┘                  └───────┬──────────┘  │
│                                                │ (1:N)       │
│                                                ▼              │
│                                       ┌──────────────────┐  │
│                                       │   ProspectPool    │  │
│                                       │                  │  │
│                                       │  - externalProspectId │
│                                       │  - sourceUrl      │  │
│                                       │  - website        │  │
│                                       │  - country        │  │
│                                       │  - queue (DISCOVERY │
│                                       │    /QUALIFICATION  │  │
│                                       │    /RESEARCH/CRM) │  │
│                                       │  - status         │  │
│                                       │  - researchStatus │  │
│                                       │  - crmPushStatus  │  │
│                                       └──────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              ChituSyncService (connector API)         │    │
│  │                                                       │    │
│  │  POST /Prospecting/sync/lead          → Lead          │    │
│  │  POST /Prospecting/sync/evidence      → ResearchEvidence │
│  │  POST /Prospecting/sync/opportunity-proposal → Lead   │    │
│  │                                                       │    │
│  │  ⚠ ZERO references to SearchJob or ProspectPool       │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           LeadWorkflowHook (Phase3B02)                │    │
│  │                                                       │    │
│  │  AfterSave: creates Tasks for high-score/research     │    │
│  │  ⚠ ZERO references to Acquisition entities            │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               CHITU-CONNECTOR (Python)                        │
│                                                               │
│  ProspectingConnectorClient                                   │
│  ├── sync_lead()          → POST /Prospecting/sync/lead       │
│  ├── sync_evidence()      → POST /Prospecting/sync/evidence   │
│  └── sync_opportunity_proposal() → /sync/opportunity-proposal │
│                                                               │
│  ⚠ ZERO references to SearchStrategy, SearchJob, ProspectPool │
│  ⚠ ZERO search/discovery endpoints consumed                   │
└─────────────────────────────────────────────────────────────┘

┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│               EXTERNAL (NOT IMPLEMENTED)                       │
│                                                                 │
│  ❌ Search Provider Adapter (Google, Apify, etc.)              │
│  ❌ SearchJob Worker/Daemon                                    │
│  ❌ ProspectPool auto-creation from search results             │
│  ❌ ProspectPool → Lead auto-conversion                        │
│  ❌ Discovery Provider interface/contract                      │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

---

## 3. SearchStrategy Actual Capability

### 3.1 Entity Definition (`SearchStrategy.json`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | yes | Strategy label |
| `product` | enum | yes | 8 Chitu products (PlateCycler, Resin Tank, etc.) |
| `country` | varchar(100) | yes | Target country |
| `region` | varchar(100) | no | Optional region refinement |
| `targetPersona` | multiEnum | yes | 9 persona types (Distributor, Reseller, Dealer, etc.) |
| `targetCompanyType` | varchar(100) | no | Additional company classification |
| `keywords` | text | no | Additional search terms |
| `excludedKeywords` | text | no | Terms to exclude |
| `sourcePlan` | multiEnum | yes | 6 source types (GOOGLE_SEARCH, GOOGLE_MAPS, APIFY, DIRECTORY, CUSTOM_IMPORT, CUSTOMS_DATA) |
| `status` | enum | yes | DRAFT→READY→GENERATED→RUNNING→COMPLETED→FAILED→CANCELLED |
| `generatedJobCount` | int | yes (readOnly) | Counter for generated SearchJobs |

### 3.2 Relationships

- `searchJobs` (hasMany → SearchJob.strategy)
- `createdBy` (belongsTo → User)
- `assignedUser` (belongsTo → User)
- `teams` (hasMany → Team)

### 3.3 API Endpoints

| Route | Method | Implementation | Status |
|-------|--------|---------------|--------|
| `/SearchStrategy` | GET/POST/PUT/DELETE | Standard Record controller | **Working** |
| `/Prospecting/search-strategy/generate-jobs` | POST | `PostGenerateSearchStrategyJobs` → `SearchStrategyService.generate()` | **Working** |

### 3.4 The `generate()` Algorithm

Located in `SearchStrategyService.php`, this is the **only runtime execution path** in the entire acquisition system:

1. Validates the SearchStrategy (product, country, personas, sources)
2. Expands `PRODUCTS[keywords]` × `PERSONAS` × `sources` into candidate queries
3. Applies excluded keywords filter
4. Generates SHA-256 `fingerprint(product|country|keyword|source)` for each candidate
5. **Deduplicates** against existing SearchJob records via `queryFingerprint` index
6. Creates QUEUED SearchJob records (max 40 per strategy)
7. Updates SearchStrategy status to GENERATED

### 3.5 Template Data (`SearchStrategyTemplates.php`)

- **MAX_JOBS:** 40
- **PRODUCTS:** 8 products × 5 default keywords each
- **PERSONAS:** 9 persona types with search-friendly values
- **SOURCES:** 6 source types

### 3.6 Client-Side

- Custom detail view (`files/client/custom/src/views/search-strategy/detail.js`)
- Adds "Generate Jobs" action button
- **Known Issue (Phase3C02.1):** `RangeError: Maximum call stack size exceeded` in Sales Manager browser session when rendering SearchStrategy detail — NOT caused by C02.1 changes; pre-existing in client runtime

---

## 4. SearchJob Actual Capability

### 4.1 Entity Definition (`SearchJob.json`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | yes | "{keyword} [{source}]" |
| `keyword` | varchar(255) | no | Search keyword |
| `country` | varchar(100) | no | Target country |
| `strategy` | link | no | Parent SearchStrategy |
| `product` | enum | no | Product category |
| `status` | enum | yes | QUEUED→RUNNING→COMPLETED→FAILED→CANCELLED |
| `source` | varchar(100) | no | GOOGLE_SEARCH, GOOGLE_MAPS, etc. |
| `priority` | enum | yes | P1, P2, P3 (default P2) |
| `queryFingerprint` | varchar(64) | no | SHA-256 dedup key (indexed) |
| `resultCount` | int | yes | Default 0 |
| `acceptedCount` | int | yes | Default 0 |
| `rejectedCount` | int | yes | Default 0 |
| `errorMessage` | text | no | Failure details |
| `startedAt` | datetime | no | Execution start |
| `completedAt` | datetime | no | Execution end |
| `prospectCount` | int | no | ProspectPool records produced |
| `failureReason` | text | no | Failure classification |

### 4.2 Relationships

- `strategy` (belongsTo → SearchStrategy.searchJobs)
- `prospectPools` (hasMany → ProspectPool.searchJob)
- `assignedUser` (belongsTo → User)
- `teams` (hasMany → Team)

### 4.3 Indices

| Index | Columns | Purpose |
|-------|---------|---------|
| `status` | [status] | Queue filtering |
| `source` | [source] | Source filtering |
| `queryFingerprint` | [queryFingerprint] | **Deduplication** — used by `generate()` to skip existing jobs |

### 4.4 Status Lifecycle

```
QUEUED ──→ RUNNING ──→ COMPLETED
  │           │
  │           ├──→ FAILED
  │           │
  └───────────┴──→ CANCELLED
```

**Current reality:** Jobs stay at QUEUED forever. No code transitions them to RUNNING or any terminal state.

### 4.5 API Endpoints

| Route | Method | Implementation | Status |
|-------|--------|---------------|--------|
| `/SearchJob` | GET/POST/PUT/DELETE | Standard Record controller | **Working** |

**No custom API endpoint exists for executing a SearchJob.**

---

## 5. ProspectPool Actual Capability

### 5.1 Entity Definition (`ProspectPool.json`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | yes | Prospect label |
| `externalProspectId` | varchar(128) | no | Provider-side ID (indexed) |
| `source` | varchar(100) | no | Origin source |
| `sourceUrl` | url | no | Source reference URL |
| `website` | url | no | Prospect website |
| `country` | varchar(100) | no | Prospect country |
| `queue` | enum | yes | **DISCOVERY → QUALIFICATION → RESEARCH → CRM** |
| `status` | enum | yes | WAITING → RUNNING → COMPLETED → FAILED |
| `researchStatus` | enum | yes | NOT_STARTED → PENDING → COMPLETED → FAILED |
| `qualificationStatus` | enum | yes | PENDING → QUALIFIED → REJECTED |
| `crmPushStatus` | enum | yes | NOT_READY → READY → PUSHED → FAILED |
| `qualifiedAt` | datetime | no | Qualification timestamp |
| `crmPushedAt` | datetime | no | CRM push timestamp |
| `note` | text | no | Human notes |

### 5.2 Queue Pipeline (Designed, Not Implemented)

```
DISCOVERY → QUALIFICATION → RESEARCH → CRM
```

The `queue` field is the **routing mechanism** for prospect processing. Each queue represents a processing stage:
- **DISCOVERY:** Raw search results, not yet qualified
- **QUALIFICATION:** Passed business qualification filters
- **RESEARCH:** Ready for deep website research
- **CRM:** Qualified for CRM Lead creation

**Current reality:** No code writes to ProspectPool. Records are created only through manual UI entry.

### 5.3 Deduplication

- `externalProspectId` index exists but is **not used by any code** for dedup
- No fingerprint or hash field for content-based dedup
- No unique constraint on `website` or `sourceUrl`

### 5.4 Relationships

- `searchJob` (belongsTo → SearchJob.prospectPools)
- `assignedUser` (belongsTo → User)
- `teams` (hasMany → Team)

### 5.5 API Endpoints

| Route | Method | Implementation | Status |
|-------|--------|---------------|--------|
| `/ProspectPool` | GET/POST/PUT/DELETE | Standard Record controller | **Working** |

---

## 6. Existing Execution Paths

### 6.1 Path A: Strategy → Job Generation (WORKING)

```
User clicks "Generate Jobs" on SearchStrategy detail
  → POST /Prospecting/search-strategy/generate-jobs {strategyId}
    → PostGenerateSearchStrategyJobs::process()
      → SearchStrategyService::generate()
        → expand(): PRODUCT keywords × PERSONAS × sources
        → fingerprint(): SHA-256 hash
        → Dedup check against existing queryFingerprint
        → Create QUEUED SearchJob records (max 40)
        → Update SearchStrategy.status = GENERATED
      ← {success, strategy_id, generated_count, existing_count}
    ← 200 JSON
```

**Files involved:**
- `Api/PostGenerateSearchStrategyJobs.php`
- `Services/SearchStrategyService.php`
- `Services/SearchStrategyTemplates.php`
- `files/client/custom/src/views/search-strategy/detail.js`

### 6.2 Path B: Connector Lead Sync (WORKING, Separate System)

```
Chitu Intelligence Python runtime
  → ProspectingConnectorClient.sync_lead(payload)
    → POST /Prospecting/sync/lead
      → PostSyncLead::process()
        → ChituSyncService::syncLead()
          → findLead() by peCandidateId
          → Create or update Lead
        ← {success, created, crm_id}
```

**Files involved:** `Api/PostSyncLead.php`, `Services/ChituSyncService.php`

### 6.3 Path C: Connector Evidence Sync (WORKING, Separate System)

```
Chitu Intelligence Python runtime
  → ProspectingConnectorClient.sync_evidence(payload)
    → POST /Prospecting/sync/evidence
      → ChituSyncService::syncEvidence()
        → Create ResearchEvidence records linked to Lead
```

### 6.4 Path D: Connector Opportunity Proposal (WORKING, Separate System)

```
Chitu Intelligence Python runtime
  → ProspectingConnectorClient.sync_opportunity_proposal(payload)
    → POST /Prospecting/sync/opportunity-proposal
      → ChituSyncService::syncOpportunityProposal()
        → Updates Lead with proposal fields
        → EXPLICITLY sets peProposalAction = 'NO_AUTOMATIC_OPPORTUNITY'
```

**Critical design boundary:** `syncOpportunityProposal()` has a **hard gate** at score < 80 and explicitly refuses to create Opportunities. It sets `NO_AUTOMATIC_OPPORTUNITY` — this is intentional and aligned with the "no automatic Lead creation" rule.

---

## 7. Missing Runtime Paths

### 7.1 External Search Execution (MISSING)

No code performs the actual search. A SearchJob contains "what to search" (keyword, country, source) but nothing reads the QUEUED job and calls Google/Apify/etc.

**What needs to be built:** A worker/consumer that:
1. Polls/reads QUEUED SearchJobs
2. Calls an external provider adapter
3. Writes raw results to ProspectPool (DISCOVERY queue)
4. Updates SearchJob status to RUNNING → COMPLETED/FAILED

### 7.2 Provider Adapter Interface (MISSING)

No interface exists for external search providers. `SearchStrategyTemplates::SOURCES` lists `GOOGLE_SEARCH`, `GOOGLE_MAPS`, `APIFY`, `DIRECTORY`, `CUSTOM_IMPORT`, `CUSTOMS_DATA`, but there are no implementations.

### 7.3 ProspectPool Auto-Creation (MISSING)

No code writes ProspectPool records from search results. The entity has fields for `externalProspectId`, `website`, `sourceUrl`, `country` — but nothing populates them programmatically.

### 7.4 ProspectPool → Lead Conversion (MISSING)

No bridge between ProspectPool and Lead creation. The ProspectPool has `crmPushStatus: READY` state and `CRM` queue, but no code reads these and calls `ChituSyncService` or any Lead creation path.

### 7.5 Job Lifecycle Automation (MISSING)

- No formula or hook that transitions SearchJob status
- No code that sets `startedAt` or `completedAt`
- No code that updates `resultCount`, `acceptedCount`, `rejectedCount`
- No retry logic
- No timeout detection

### 7.6 SearchStrategy Status Automation (PARTIAL)

- `generate()` sets status to GENERATED
- No code transitions from GENERATED → RUNNING → COMPLETED/FAILED
- No code aggregates SearchJob statuses back to SearchStrategy

---

## 8. Data and Side-Effect Boundary

### 8.1 What MUST NOT Happen (Confirmed Safe)

| Concern | Status | Evidence |
|---------|--------|----------|
| Auto-create Lead from SearchJob | **SAFE** — No code exists | Zero references between ChituSyncService and Acquisition entities |
| Auto-create Lead from ProspectPool | **SAFE** — No code exists | ProspectPool has no service/hook/connector path to Lead |
| Auto-create Opportunity | **SAFE** — Explicitly blocked | `syncOpportunityProposal()` sets `NO_AUTOMATIC_OPPORTUNITY` |
| Auto-create ResearchEvidence | **SAFE** — Only via connector | `syncEvidence()` requires explicit API call |
| Auto-send email | **SAFE** — No SMTP code | No email sending in extension; `peEmailStatus` is passive |
| Auto-create Email Draft | **SAFE** — No code exists | No Email entity creation in any service |

### 8.2 Future Boundary Requirements

Any future implementation MUST:

1. **Never** automatically create a Lead from a raw search result without qualification
2. **Never** auto-send email without human approval
3. **Never** bypass the ProspectPool queue pipeline (DISCOVERY → QUALIFICATION → RESEARCH → CRM)
4. **Never** skip the `peProposalAction = 'NO_AUTOMATIC_OPPORTUNITY'` guard
5. Keep idempotency via `queryFingerprint` (SearchJob) and `externalProspectId` (ProspectPool)

---

## 9. Security / ACL Observations

### 9.1 Current ACL (Phase3C02.1)

| Role | SearchStrategy | SearchJob | ProspectPool |
|------|:---:|:---:|:---:|
| Admin | Full | Full | Full |
| Sales Manager | Create/Read/Edit all, No Delete | Same | Same |
| Sales User | Create/Read/Edit own, No Delete | Same | Same |
| Integration Bot | Create/Read/Edit all, No Delete | Same | Same |
| Research User | **No access** | **No access** | **No access** |

### 9.2 Observations

- **Sales Manager has acquisition access** — appropriate; they manage search strategies
- **Research User has NO acquisition access** — gap: Research users should at least read SearchJob/ProspectPool to understand the pipeline feeding their work
- **Integration Bot** has edit-all on ProspectPool — this is the intended consumer for a future worker
- **No delete for non-Admin** — correct safety measure
- **The `generate-jobs` API endpoint checks ACL** via `$this->acl->checkEntityEdit($strategy)` and `$this->acl->check('SearchJob', 'create')`

### 9.3 Future ACL Considerations

- A future worker daemon needs at minimum `Integration Bot` level access
- If Research team reviews raw prospects before qualification, they need `ProspectPool` read access in DISCOVERY/RESEARCH queues
- The CRM push from ProspectPool to Lead requires `Lead` create permission (already on Sales Manager and Integration Bot)

---

## 10. Recommended Runtime Contract

### 10.1 Job Request Contract

```json
{
  "job_id": "string (SearchJob.id)",
  "keyword": "string",
  "country": "string",
  "source": "GOOGLE_SEARCH | GOOGLE_MAPS | APIFY | DIRECTORY",
  "product": "PlateCycler | Resin Tank | ...",
  "query_fingerprint": "string (SHA-256, idempotency key)",
  "priority": "P1 | P2 | P3",
  "max_results": 50
}
```

### 10.2 Provider Adapter Interface (Conceptual)

```python
class DiscoveryProvider:
    """Contract for external search providers."""
    def search(self, request: JobRequest) -> list[RawCandidate]: ...
    def validate_credentials(self) -> bool: ...

class RawCandidate:
    external_id: str
    name: str
    website: str | None
    source_url: str | None
    country: str | None
    snippet: str | None
    raw_data: dict  # provider-specific payload
```

### 10.3 Job Status Contract

```
QUEUED → RUNNING (worker claims job)
RUNNING → COMPLETED (results written to ProspectPool)
RUNNING → FAILED (error captured in errorMessage/failureReason)
QUEUED → CANCELLED (manual or timeout)
```

### 10.4 Idempotency

- **SearchJob level:** `queryFingerprint` SHA-256 prevents duplicate job creation
- **ProspectPool level:** `externalProspectId` + `source` composite should be used for dedup when writing results
- **Worker level:** Check SearchJob.status == QUEUED before processing; atomically set to RUNNING

### 10.5 Retry

- FAILED jobs with retryable errors (timeout, rate-limit) should be reset to QUEUED
- Non-retryable errors (auth failure, invalid params) should stay FAILED
- Maximum 3 retries per job

### 10.6 Error Model

```json
{
  "failure_reason": "RATE_LIMIT | AUTH_FAILURE | TIMEOUT | INVALID_PARAMS | PROVIDER_ERROR | EMPTY_RESULTS",
  "error_message": "Human-readable detail",
  "retryable": true,
  "retry_count": 2
}
```

### 10.7 Raw Candidate Normalization

Before writing to ProspectPool, raw provider results must be normalized:
- `name` → ProspectPool.name
- `external_id` → ProspectPool.externalProspectId
- `website` → ProspectPool.website (validated URL)
- `source_url` → ProspectPool.sourceUrl
- `country` → ProspectPool.country
- `queue` = `DISCOVERY` (initial queue)
- `status` = `WAITING`

### 10.8 ProspectPool Persistence

- Write one ProspectPool record per raw candidate
- Dedup on `externalProspectId` within same source
- Link to parent SearchJob via `searchJobId`
- Increment SearchJob.resultCount / acceptedCount

### 10.9 No Automatic Lead Creation

- ProspectPool records with `crmPushStatus = READY` require **human review** before conversion
- The connector's `syncOpportunityProposal` guard (`NO_AUTOMATIC_OPPORTUNITY`) applies equally to acquisition-sourced prospects
- A future "Push to CRM" action should be an explicit button, not automatic

---

## 11. Proposed Small Follow-up Tasks

### Task T1: Fix SearchStrategy Detail RangeError (UI Bug)

**Scope:** Investigate and fix the `RangeError: Maximum call stack size exceeded` in SearchStrategy detail view.

**Files:**
- `crm-extension/files/client/custom/src/views/search-strategy/detail.js`

**Deliverable:** Working SearchStrategy detail view for Sales Manager with clean browser console.

**Estimated effort:** 1 Codex session

---

### Task T2: Discovery Provider Interface + Worker Skeleton

**Scope:** Create the Python-side provider interface, a job consumer skeleton that reads QUEUED SearchJobs from EspoCRM, and a stub/noop provider.

**Files (new):**
- Python: discovery worker entry point, provider adapter interface, EspoCRM SearchJob API client
- **No CRM extension changes** (SearchJob API already supports CRUD via standard Record controller)

**Deliverable:** Worker that reads QUEUED jobs, calls a stub provider (returns empty results), and updates job status.

**Estimated effort:** 1–2 Codex sessions

---

### Task T3: Raw Candidate Normalization + ProspectPool Writer

**Scope:** Implement the normalization layer that converts provider results into ProspectPool records, with dedup and batch writing.

**Files:**
- Python: candidate normalizer, ProspectPool batch writer
- **No CRM extension changes** (ProspectPool API already supports CRUD)

**Deliverable:** Worker writes normalized candidates to ProspectPool (DISCOVERY queue), with idempotency on `externalProspectId`.

**Estimated effort:** 1 Codex session

---

### Task T4: Job Lifecycle + Retry Automation

**Scope:** Add SearchJob state transitions, completion tracking, and retry logic. Implement on the CRM side via service/hook.

**Files likely to change:**
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SearchJobService.php` (new)
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchJob.json` (formula addition)

**Deliverable:** SearchJob automatically updates `startedAt`, `completedAt`, `resultCount`, and handles retryable failures.

**Estimated effort:** 1 Codex session

---

## 12. Exact Files Likely to Change in Each Follow-up

### T1: SearchStrategy UI Fix

| File | Change Type |
|------|-------------|
| `crm-extension/files/client/custom/src/views/search-strategy/detail.js` | Investigate/fix recursion |

### T2: Provider Interface + Worker

| File | Change Type |
|------|-------------|
| `discovery/worker.py` (NEW) | Job consumer entry point |
| `discovery/providers/interface.py` (NEW) | Provider adapter contract |
| `discovery/providers/stub.py` (NEW) | No-op stub provider |
| `discovery/espocrm_client.py` (NEW) | SearchJob/ProspectPool API client |
| `crm-extension/tests/test_extension_skeleton.py` | No changes needed (Python-side code) |

### T3: Normalization + ProspectPool Writer

| File | Change Type |
|------|-------------|
| `discovery/normalizer.py` (NEW) | Raw result → ProspectPool normalization |
| `discovery/prospect_writer.py` (NEW) | Batch dedup + ProspectPool API writer |

### T4: Job Lifecycle Automation

| File | Change Type |
|------|-------------|
| `crm-extension/files/.../Services/SearchJobService.php` (NEW) | State transition service |
| `crm-extension/files/.../Resources/metadata/entityDefs/SearchJob.json` | Add formula or hook |
| `crm-extension/Resources/entityDefs/SearchJob.json` (surface) | Mirror changes |
| `crm-extension/tests/test_extension_skeleton.py` | Add job lifecycle tests |

---

## 13. Collision Check Against Phase3C02.1A

### 13.1 What C02.1A is Working On

The parallel task **Phase3C02.1A — SearchStrategy Detail RangeError Fix** is likely modifying:
- `files/client/custom/src/views/search-strategy/detail.js`
- Possibly `clientDefs/SearchStrategy.json`
- Browser runtime testing

### 13.2 Zero Collision Confirmation

| Resource | C02.1A (likely) | C02.2A (this audit) | Collision? |
|----------|:---:|:---:|:---:|
| `detail.js` | Edit | Read only | **No** |
| `clientDefs/SearchStrategy.json` | Possible edit | Read only | **No** |
| Any PHP service/entity/controller | No | Read only | **No** |
| Python connector files | No | Read only | **No** |
| Docker/EspoCRM runtime | Possible testing | No interaction | **No** |
| Extension package (ZIP) | No | No | **No** |
| Git commits | Possible | No commit | **No** |

**This audit reads files only. It does not write, install, rebuild, or mutate any shared resource. Zero collision risk with C02.1A.**

### 13.3 Recommended Sequencing

1. **First:** Complete C02.1A (SearchStrategy UI fix)
2. **Then:** Start T1 (only if C02.1A didn't already fix the RangeError)
3. **Then:** T2 → T3 → T4 in sequence (each builds on the previous)

---

**Phase3C02.2A audit complete. No code was modified, no runtime was affected, no data was created or deleted.**
