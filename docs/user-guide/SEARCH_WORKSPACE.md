# Search Workspace (User Guide)

**Status:** Metadata **Implemented**; job execution **Draft** for real providers

## Overview

The Acquisition workspace helps plan and queue discovery searches before prospects enter the main Lead sync pipeline.

## Entities

### Search Strategy

**Status:** **Implemented** (UI + API)

Create a Search Strategy with:

- Product (enum: PlateCycler, Resin Tank, etc.)
- Country (required)
- Target persona(s) (multi-select)
- Optional keywords and excluded keywords
- Source plan (GOOGLE_SEARCH, GOOGLE_MAPS, APIFY, DIRECTORY, CUSTOM_IMPORT, CUSTOMS_DATA)

**Statuses:** `DRAFT`, `READY`, `GENERATED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`

### Generate Discovery Jobs

**Status:** **Implemented**

On Search Strategy detail view, use **Generate Jobs** action:

- Calls `POST /Prospecting/search-strategy/generate-jobs`
- Creates `SearchJob` records with status `QUEUED`
- Deduplicates by `queryFingerprint` (SHA-256)
- Maximum 40 jobs per strategy

### Search Job (Discovery Job)

**Status:** **Implemented** (metadata + filters)

| Field | Purpose |
|-------|---------|
| `keyword`, `country`, `product`, `source` | Query dimensions |
| `status` | `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `queryFingerprint` | Dedup key |
| `resultCount`, `acceptedCount`, `rejectedCount` | Execution metrics |

**Filters:** jobsQueued, jobsRunning, jobsCompleted, jobsFailed, jobsCancelled

### Job Execution

**Status:** **Draft**

- Connector CLI can run a **fake provider** job against live CRM: `python -m chitu_connector.acquisition.runner run-job --job-id <id> --provider fake`
- Real Google/Apify search from UI: **Not Implemented**
- **TBD — requires runtime verification** for operator workflow on your CRM instance

## Dashboards

Acquisition dashlets (when provisioned): Search Strategies, Discovery Jobs, Jobs Running/Waiting/Completed/Failed, Lead Pool, Research Queue.

Provisioning: `deployment/provisioning/phase3c01_provision_acquisition_workspace.php`

## Related Documents

- [PROSPECT_POOL.md](PROSPECT_POOL.md)
- [../architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md)
