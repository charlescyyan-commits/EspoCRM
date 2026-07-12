# Phase3B01A — Railway EspoCRM Deployment Plan

**Date:** 2026-07-11
**Status:** DESIGN ONLY — No deployment performed
**Scope:** READ-ONLY planning for independent EspoCRM production deployment on Railway
**Dependencies:** PHASE3B00 (Production Readiness Audit), PHASE3B00.1 (Integration Bot Cutover), PHASE3A32 (Production Preparation), PHASE3A33 (ACL Validation), PHASE3A34 (Layout Activation)

---

## Critical Architecture Decision

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   BEFORE                          AFTER                          │
│                                                                  │
│   Railway                          Railway                       │
│   ┌─────────────────┐             ┌─────────────────────────┐    │
│   │ Chitu Intelligence│            │ EspoCRM (standalone)     │    │
│   │ + EspoCRM        │    ──→     │                         │    │
│   │ (tightly coupled) │   REMOVE   │ • EspoCRM 10.0.1        │    │
│   └─────────────────┘   Chitu     │ • MariaDB 11.4          │    │
│                         from      │ • EspoCRM Daemon        │    │
│                         Railway   │ • Prospecting Extension  │    │
│                                   └─────────────────────────┘    │
│                                                                  │
│   Chitu Intelligence runs        EspoCRM is an INDEPENDENT       │
│   elsewhere (local, or           production CRM system.          │
│   separate Railway project       Chitu connects TO it via        │
│   if needed).                    its API — not embedded in it.   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**EspoCRM is deployed independently. Do not assume Chitu Intelligence services, databases, or workers exist in the same Railway project, network, or account.** The Chitu Intelligence application will be removed from Railway. EspoCRM stands alone.

---

## Table of Contents

1. [Railway Architecture](#1-railway-architecture)
2. [EspoCRM Container Plan](#2-espocrm-container-plan)
3. [Database Plan](#3-database-plan)
4. [Extension Deployment](#4-extension-deployment)
5. [Security Plan](#5-security-plan)
6. [Local Validation Before Railway](#6-local-validation-before-railway)
7. [Deployment Sequence](#7-deployment-sequence)
8. [Rollback Plan](#8-rollback-plan)

---

## 1. Railway Architecture

### 1.1 Project Structure

**Recommendation: Single Railway project with 3 services.**

```
Railway Project: chitu-espocrm-prod
│
├── Service: espocrm          (Docker image: espocrm/espocrm:10.0.1)
│   ├── Port: 80 (internal) → Railway domain (external)
│   ├── Volume: espocrm-custom   → /var/www/html/custom
│   ├── Volume: espocrm-uploads  → /var/www/html/data/upload
│   └── Env vars from shared project environment
│
├── Service: espocrm-db       (Docker image: mariadb:11.4)
│   ├── Port: 3306 (internal only)
│   ├── Volume: espocrm-db-data → /var/lib/mysql
│   └── Env vars: MARIADB_ROOT_PASSWORD, MARIADB_DATABASE, etc.
│
└── Service: espocrm-daemon   (Docker image: espocrm/espocrm-daemon:10.0.1)
    ├── No exposed port
    └── Connects to espocrm-db:3306
```

### 1.2 Option A vs Option B

#### Option A: All services in one Railway project (RECOMMENDED)

```
✅ Single project boundary — simpler management
✅ Internal networking between services (espocrm → espocrm-db without public exposure)
✅ Shared environment variables across services
✅ Single backup/restore scope
✅ Single billing entity
✅ Railway's internal DNS resolves service names automatically
   (espocrm-db.railway.internal → 3306)
```

#### Option B: Separate Railway projects for each service

```
❌ Cross-project networking requires public exposure or VPN
❌ Two billing entities, two deployment pipelines
❌ Environment variable duplication across projects
❌ Harder to coordinate backups across projects
❌ No benefit for a 3-service deployment
```

**Verdict:** Option A. A single Railway project is the correct choice for this scale. EspoCRM, MariaDB, and the daemon are tightly related and do not benefit from project-level isolation. Separate projects introduce networking complexity without meaningful security gain — Railway's internal network already isolates services from the public internet unless explicitly exposed.

### 1.3 Persistent Volumes

Railway volumes are region-scoped and survive service restarts and redeploys.

| Volume Name | Mount Point | Size Recommendation | Purpose |
|------------|-------------|---------------------|---------|
| `espocrm-custom` | `/var/www/html/custom` | 1 GB | Custom extensions, metadata, layouts (survives container rebuild) |
| `espocrm-uploads` | `/var/www/html/data/upload` | 5 GB | CRM user uploads, attachments |
| `espocrm-db-data` | `/var/lib/mysql` | 20 GB | MariaDB persistent storage |

**Warning:** The official `espocrm/espocrm` Docker image stores application code at `/var/www/html`. Only `/var/www/html/custom` and `/var/www/html/data/upload` need persistence. The rest of the application is replaced on image update. Do NOT mount a volume over `/var/www/html` — this would prevent image updates from applying.

### 1.4 Internal Networking

Railway automatically provides internal DNS between services in the same project:

```yaml
# EspoCRM → MariaDB connection
ESPOCRM_DATABASE_HOST: espocrm-db.railway.internal
ESPOCRM_DATABASE_PORT: 3306
```

No public port exposure is needed for the database service. Railway's internal network handles service-to-service communication.

### 1.5 Public Exposure

| Service | Public Exposure | Rationale |
|---------|:--------------:|-----------|
| `espocrm` | **Yes** | CRM UI and API access for Chitu sync + sales users |
| `espocrm-db` | **No** | Database accessed only internally |
| `espocrm-daemon` | **No** | Background job processor, no external interface |

EspoCRM will receive a Railway-generated domain (e.g., `chitu-espocrm-prod.up.railway.app`). A custom domain can be added later.

### 1.6 Railway Project Configuration

Railway uses a `railway.toml` or service-level configuration. The recommended approach is Railway's dashboard-based configuration (simpler for a first deployment), with a generated `railway.toml` for reproducibility.

**Conceptual `railway.toml` (for future infra-as-code):**

```toml
[build]
watch = ["espocrm_extension/files/**"]

[deploy]

[service.espocrm]
image = "espocrm/espocrm:10.0.1"

[service.espocrm.volume.espocrm-custom]
mount = "/var/www/html/custom"

[service.espocrm.volume.espocrm-uploads]
mount = "/var/www/html/data/upload"

[service.espocrm-db]
image = "mariadb:11.4"

[service.espocrm-db.volume.espocrm-db-data]
mount = "/var/lib/mysql"

[service.espocrm-daemon]
image = "espocrm/espocrm-daemon:10.0.1"
```

**Note:** This is a conceptual reference. Actual Railway service creation is done through the Railway dashboard or CLI. Do not create this file until Railway services are provisioned.

---

## 2. EspoCRM Container Plan

### 2.1 Docker Images (Version-Pinned)

| Service | Image | Tag | Digest Verification |
|---------|-------|-----|---------------------|
| EspoCRM Application | `espocrm/espocrm` | `10.0.1` | Pull and record SHA256 before deploy |
| EspoCRM Daemon | `espocrm/espocrm-daemon` | `10.0.1` | Must match application version |
| MariaDB | `mariadb` | `11.4` | LTS release track |

**Version pinning rule:** Never use `latest` tag. Always pin to a specific version. Before upgrading, test in the local rehearsal environment first.

### 2.2 EspoCRM Service Configuration

#### Environment Variables

These are set in the Railway project dashboard (shared across all services) or per-service overrides.

```bash
# ─── EspoCRM Core ───
ESPOCRM_SITE_URL=${RAILWAY_PUBLIC_DOMAIN}       # Set automatically by Railway
ESPOCRM_ADMIN_USERNAME=admin                     # Production admin username
ESPOCRM_ADMIN_PASSWORD=<secure-password>         # Generated, stored in secrets manager

# ─── Database Connection ───
ESPOCRM_DATABASE_HOST=espocrm-db.railway.internal
ESPOCRM_DATABASE_PORT=3306
ESPOCRM_DATABASE_NAME=espocrm
ESPOCRM_DATABASE_USER=espocrm
ESPOCRM_DATABASE_PASSWORD=<secure-password>      # Generated, stored in secrets manager

# ─── MariaDB Root (for DB service only) ───
MARIADB_ROOT_PASSWORD=<secure-password>          # Generated, stored in secrets manager
MARIADB_DATABASE=espocrm
MARIADB_USER=espocrm
MARIADB_PASSWORD=<same-as-ESPOCRM_DATABASE_PASSWORD>

# ─── EspoCRM Configuration ───
ESPOCRM_CONFIG_USE_CACHE_IN_AUTH=true
ESPOCRM_CONFIG_IS_DEV_MODE=false
ESPOCRM_CONFIG_AUTH_2FA=false                    # 2FA for interactive users only, not API
ESPOCRM_CONFIG_AUTH_TOKEN_EXPIRED=86400          # 24h

# ─── Email (CRM system emails only — not outreach) ───
# EspoCRM sends password resets and system notifications only.
# Outreach emails are sent by Chitu, NOT by EspoCRM.
ESPOCRM_CONFIG_OUTBOUND_EMAIL_FROM_ADDRESS=noreply@<domain>
# Use Railway's SMTP or a dedicated transactional email service
```

**Important:** EspoCRM does NOT send outreach emails. The email configuration is for CRM system emails only (password resets, notifications). The `peEmailStatus` fields on Lead are Chitu-owned display fields — EspoCRM never initiates email sending for outreach.

#### Health Checks

Railway uses HTTP health checks on the exposed port.

```yaml
# Conceptual health check configuration
health_check:
  path: /api/v1/                            # EspoCRM API root returns 200
  port: 80
  interval: 30s
  timeout: 10s
  unhealthy_threshold: 3
  start_period: 60s                         # Allow time for PHP-FPM + DB connection
```

The EspoCRM API root (`/api/v1/`) returns HTTP 200 when the application is healthy and the database is reachable. This is the recommended health check endpoint.

#### Startup Order

```
espocrm-db (MariaDB)
    │
    ├── Health: port 3306 accepting connections
    │
    ├──→ espocrm (Application)
    │       │
    │       └── Runs: php command.php rebuild (first boot only)
    │
    └──→ espocrm-daemon (Background Jobs)
            │
            └── Waits for espocrm to be healthy before starting jobs
```

Railway handles startup ordering through health check dependencies. The `espocrm` and `espocrm-daemon` services should NOT start until `espocrm-db` is healthy.

### 2.3 EspoCRM Daemon Service

The EspoCRM daemon processes background jobs (notifications, workflow triggers, scheduled jobs).

```bash
# Environment (same as espocrm service + daemon-specific)
ESPOCRM_DATABASE_HOST=espocrm-db.railway.internal
ESPOCRM_DATABASE_PORT=3306
ESPOCRM_DATABASE_NAME=espocrm
ESPOCRM_DATABASE_USER=espocrm
ESPOCRM_DATABASE_PASSWORD=<same-password>
```

The daemon image (`espocrm/espocrm-daemon:10.0.1`) is designed to connect to the same database as the application. No separate configuration is needed beyond database connection parameters.

### 2.4 Resource Allocation (Starting Recommendations)

| Service | CPU | Memory | Disk | Rationale |
|---------|-----|--------|------|-----------|
| `espocrm` | 0.5 vCPU | 512 MB | 1 GB (base) | PHP-FPM with 2-4 workers, low concurrent user count |
| `espocrm-db` | 0.5 vCPU | 512 MB | 20 GB (volume) | MariaDB with small dataset (< 1000 Leads initially) |
| `espocrm-daemon` | 0.25 vCPU | 256 MB | 512 MB (base) | Lightweight job polling |

**Scale up rule:** Monitor Railway metrics. Increase `espocrm` memory to 1 GB if PHP-FPM workers exhaust memory. Increase `espocrm-db` to 1 GB if query performance degrades.

---

## 3. Database Plan

### 3.1 MariaDB Version

**Version: `mariadb:11.4` (LTS)**

MariaDB 11.4 is the current LTS release. It is already validated in the local test environment (`espocrm-db` container). The EspoCRM 10.0.1 official image supports MariaDB natively.

### 3.2 Volume Strategy

```
Volume: espocrm-db-data
Mount:  /var/lib/mysql
Size:   20 GB (starting)
Type:   Railway persistent volume (region-scoped, SSD-backed)
```

**Volume characteristics:**
- Survives service restarts, redeploys, and image updates
- Not automatically backed up by Railway — requires manual backup (see §3.3)
- Region-scoped: cannot be moved between regions without export/import
- Grows with data; monitor usage via Railway dashboard

### 3.3 Backup Strategy

**Daily automated backup via Railway Cron Job or external scheduler.**

#### Backup Command (runs inside espocrm-db container or via Railway CLI)

```bash
# Create consistent backup
mysqldump \
  --host=espocrm-db.railway.internal \
  --port=3306 \
  --user=root \
  --password="${MARIADB_ROOT_PASSWORD}" \
  --single-transaction \
  --routines \
  --events \
  --triggers \
  --databases espocrm \
  --result-file=/backup/espocrm-$(date +%Y%m%d-%H%M%S).sql

# Create checksum
sha256sum /backup/espocrm-*.sql > /backup/espocrm-$(date +%Y%m%d-%H%M%S).sql.sha256
```

#### Backup Retention Policy

| Backup Type | Frequency | Retention | Storage Location |
|------------|-----------|-----------|-----------------|
| Daily | Every 24h | 7 days | Railway volume or S3-compatible bucket |
| Weekly | Every 7 days | 4 weeks | S3-compatible bucket (separate region) |
| Pre-deployment | Before each deploy | 30 days | Local download + S3 |

#### Backup Automation Options

1. **Railway Cron Job** (simplest): Add a cron service to the Railway project that runs the mysqldump command daily.
2. **External scheduler**: A GitHub Action or external cron that connects to Railway via CLI and runs the backup.
3. **EspoCRM built-in**: EspoCRM has a backup command (`php command.php backup`) that dumps the database.

**Recommendation:** Option 1 (Railway Cron) for daily backups + manual download before each deployment.

### 3.4 Restore Procedure

```bash
# 1. Stop the EspoCRM application (prevent writes during restore)
railway service stop --service espocrm
railway service stop --service espocrm-daemon

# 2. Restore the database
mysql \
  --host=espocrm-db.railway.internal \
  --port=3306 \
  --user=root \
  --password="${MARIADB_ROOT_PASSWORD}" \
  espocrm < espocrm-YYYYMMDD-HHMMSS.sql

# 3. Rebuild EspoCRM cache
railway service start --service espocrm
railway run --service espocrm php command.php rebuild
railway run --service espocrm php command.php clear-cache

# 4. Start daemon
railway service start --service espocrm-daemon

# 5. Verify
# - Check /api/v1/ returns 200
# - Verify Lead count matches expected
# - Test API authentication
# - Verify extension metadata intact
```

### 3.5 Disaster Recovery

1. Spin up a new Railway project with the same service configuration
2. Create a new MariaDB volume
3. Restore the most recent backup from S3
4. Rebuild cache
5. Verify data integrity
6. Update DNS/custom domain to point to the new project

---

## 4. Extension Deployment

### 4.1 Release Package

The Phase3A32 release package is built from the extension source:

```powershell
# Build the release package (PowerShell, from repository root)
.\espocrm_extension\scripts\build_release_package.ps1 -OutputPath .\releases\chitu-prospecting-v1.0.0.zip
```

**Current verified package SHA-256:** `AA777F308E8FCD06362605DF3447EB0CBB4BFBE8BA72697FB3676DF91A862562` (from Phase3B01 production preflight)

**Package contents (26 entries):**
```
manifest.json
files/custom/Espo/Modules/Prospecting/...    (25 files)
```

### 4.2 Installation Procedure (Railway)

EspoCRM supports two installation methods: Admin UI upload and CLI command. For Railway, CLI is recommended for reproducibility.

#### Method: CLI Install (Recommended)

```bash
# 1. Copy the release ZIP to the espocrm service
#    Use railway CLI or SCP to place the ZIP in the container
railway run --service espocrm -- mkdir -p /tmp/extension

#    Upload the ZIP file to Railway (via railway CLI or temporary volume)
#    railway run does not support file upload directly.
#    Alternative: use a temporary volume mount or curl to an accessible URL.

# 2. Install extension via EspoCRM CLI
railway run --service espocrm php command.php extension \
  --install \
  --file=/tmp/extension/chitu-prospecting-v1.0.0.zip

# 3. Rebuild cache (required after any extension install)
railway run --service espocrm php command.php rebuild

# 4. Clear cache
railway run --service espocrm php command.php clear-cache

# 5. Verify installation
railway run --service espocrm php command.php extension --list
# Expected output: "Chitu Prospecting Integration" 1.0.0-alpha [installed]
```

#### Method: Admin UI Upload (Alternative)

1. Log in to EspoCRM as admin at the Railway-provided URL
2. Navigate to Administration → Extensions
3. Click "Install" → upload the ZIP file
4. Click "Install" on the confirmation dialog
5. After install completes, click "Rebuild" when prompted
6. Verify extension appears in the installed extensions list

**Recommendation:** Use CLI method for first production deployment (provides clear error messages in logs). Use Admin UI for subsequent updates (simpler workflow).

### 4.3 Extension Version Bump (Before Production)

Before deploying to Railway production, bump the manifest version:

1. Edit `espocrm_extension/manifest.json`: change `"version": "1.0.0-alpha"` to `"version": "1.0.0"`
2. Rebuild the release package
3. Record the new SHA-256

This is **not** performed now — it is part of the Pre-Deployment Checklist (§6.14).

### 4.4 Extension Cache Rebuild

After installing or updating the extension, always run:

```bash
php command.php rebuild       # Rebuilds metadata, entity definitions, classmap
php command.php clear-cache   # Clears application cache
```

**What rebuild does:**
- Regenerates metadata from JSON entity definitions
- Creates/updates database columns for custom fields
- Rebuilds the PHP classmap (autoloader paths)
- Regenerates ACL cache
- Rebuilds layout and clientDef caches

**Verification after rebuild:**
- `grep ResearchEvidence data/cache/application/classmapEntities.php` should return the entity class path
- Lead detail page should show the Prospecting layout (6 sections)
- `GET /api/v1/Lead/layout/detail` should return the custom panels

### 4.5 Role Provisioning

Roles are provisioned by the idempotent script at:

```
integration/espocrm_sync/provisioning/phase3a33_provision_roles.php
```

This script is **outside the extension package** (intentionally — it is a deployment tooling script, not production code).

**Provisioning procedure (Railway):**

```bash
# 1. Copy the provisioning script to the container
#    (via railway CLI or a temporary volume)

# 2. Run the provisioning script
railway run --service espocrm php /tmp/phase3a33_provision_roles.php

# Expected output: "PHASE3A33_PROVISION_DONE"

# 3. Verify roles exist
#    Use the API or Admin UI to confirm 4 roles:
#    - Admin (6a5237bd7122de6a7)
#    - Integration Bot (6a5237bd75bd64da2)
#    - Sales User (6a5237bd76d175566)
#    - Sales Manager (6a5237bd77ef7161e)
```

**Note:** The role IDs above are from the local test instance. On a fresh EspoCRM instance, the `gen_random_uuid()` IDs will differ. The provisioning script is idempotent — it creates roles by name, not by ID.

### 4.6 Post-Deployment Verification Checklist

After extension install + role provisioning + cache rebuild:

- [ ] `GET /api/v1/` returns HTTP 200
- [ ] `GET /api/v1/Lead/layout/detail` returns 6 custom panels (not core Overview/Details)
- [ ] `GET /api/v1/metadata` includes `ResearchEvidence` in entity list
- [ ] `GET /api/v1/metadata` includes all 75 Lead fields (29 pe* + native fields)
- [ ] Extension listed in Admin → Extensions as installed
- [ ] 4 roles visible in Admin → Roles
- [ ] Sales Team exists in Admin → Teams
- [ ] Integration Bot role has `create/read/edit=yes`, `delete=no` on Lead, Account, Contact, Opportunity, ResearchEvidence
- [ ] Sales User role has `read=own, edit=own, delete=no` on Lead
- [ ] Sales User field ACL: sync fields hidden, AI fields read-only
- [ ] ResearchEvidence denied to Sales User and Sales Manager
- [ ] `php command.php rebuild` completes without errors

---

## 5. Security Plan

### 5.1 Production Roles

These 4 roles are provisioned on the production instance after extension installation:

| Role | Purpose | Key Restrictions |
|------|---------|-----------------|
| **Admin** | Full CRM business access | Full CRUD on all entities; manages roles and users |
| **Integration Bot** | Chitu → EspoCRM API writes | `create/read/edit=yes`, **`delete=no`** on Lead, Account, Contact, Opportunity, ResearchEvidence. No export, no mass-update. |
| **Sales User** | Sales rep daily workflow | Own records only. Sync fields hidden. AI fields read-only. ResearchEvidence denied. |
| **Sales Manager** | Team pipeline management | Team-level visibility. Pipeline reporting. Same field restrictions as Sales User. |

### 5.2 Least-Privilege Matrix (Production)

| Entity | Admin | Integration Bot | Sales User | Sales Manager |
|--------|:-----:|:---------------:|:----------:|:-------------:|
| Lead | CRUD all | CRU, no D | CRU own, no D | CRU team, no D |
| Account | CRUD all | CRU, no D | R own (created by conversion) | RU team, no D |
| Contact | CRUD all | CRU, no D | CRU own, no D | CRU team, no D |
| Opportunity | CRUD all | CRU, no D | CRU own, no D | CRU team, no D |
| ResearchEvidence | CRUD all | CRU, no D | **Denied** (false) | **Denied** (false) |
| Task | CRUD all | — | CRUD own | CRU team |
| Meeting/Call | CRUD all | — | CRU own, no D | CRU team, no D |
| Note | CRUD all | — | CRUD own | CRU team |
| Report | CRUD all | — | — | R all |

**Integration Bot field access:**
- All `pe*` fields: read + edit (needs full field visibility for sync)
- CRM-owned sales fields (`status`, `stage`, `amount`, `closeDate`, `assignedUser`): **NOT written by bot** — enforced in code by `_FORBIDDEN_SALES_FIELDS` in `lifecycle.py`

**Sales User field access on Lead:**
- **Hidden** (`read=no, edit=no`): `peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peEngineVersion`, `peScoreRulesVersion`
- **Read-only** (`read=yes, edit=no`): `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peConfidence`, `peEvidenceCoverage`, `peQualificationStatus`, `peResearchStatus`, `peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`

### 5.3 Secrets Handling

**Rule: No secrets in code, no secrets in git, no secrets in environment variable outputs.**

| Secret | Storage Method | Access Pattern |
|--------|---------------|----------------|
| EspoCRM Admin Password | Railway shared variable (secret type) | Used only by admin users for login |
| MariaDB Root Password | Railway shared variable (secret type) | Used only by DB service and backup jobs |
| MariaDB User Password | Railway shared variable (secret type) | EspoCRM service → DB connection |
| Integration Bot API Key | Generated in EspoCRM Admin UI → stored in Railway shared variable | Chitu Intelligence → EspoCRM API calls |
| Sales User Password | Generated in EspoCRM Admin UI → shared with user via secure channel | Sales user login |
| Sales Manager Password | Generated in EspoCRM Admin UI → shared with user via secure channel | Sales manager login |

**Railway shared variables:** All service-level environment variables are encrypted at rest and in transit within Railway. Secret-type variables are redacted in Railway logs and dashboard.

### 5.4 API Credential Management

**Integration Bot API Key lifecycle:**

```text
1. GENERATE: In EspoCRM Admin UI → User (api type) → Create API Key
2. STORE:   Copy key once → paste into Railway shared variable ESPOCRM_API_KEY
3. VERIFY:  curl -H "X-Api-Key: $ESPOCRM_API_KEY" https://<domain>/api/v1/
4. ROTATE:  Every 90 days. Generate new key → update Railway variable → revoke old key
5. REVOKE:  On compromise: delete API Key in EspoCRM Admin UI → generate replacement
```

**The API key is never:**
- Hard-coded in Chitu application source
- Committed to git
- Printed in logs
- Stored in `.env` files on disk
- Shared between environments (test has its own `chitu_ai_connector` key)

### 5.5 Admin Access Policy

| Rule | Implementation |
|------|---------------|
| Admin login uses strong password (16+ chars, generated) | Set via `ESPOCRM_ADMIN_PASSWORD` env var on first boot; rotate after initial setup |
| No shared admin accounts | Each human admin gets their own user with Admin role |
| 2FA for human admin users (optional for initial deployment) | EspoCRM native 2FA (`auth2FA=true`), configurable per user |
| API users cannot be admins | `integration_bot` user type is `api`, not `regular` + admin role |
| Admin UI access via HTTPS only | Railway provides automatic TLS for `*.up.railway.app` domains |
| Session timeout: 24 hours | `ESPOCRM_CONFIG_AUTH_TOKEN_EXPIRED=86400` |

### 5.6 Network Security

| Boundary | Policy |
|----------|--------|
| Public → EspoCRM | HTTPS only (Railway auto-TLS). Port 80 HTTP redirects to 443. |
| EspoCRM → MariaDB | Internal Railway network only. MariaDB port NOT exposed publicly. |
| EspoCRM → Internet | Outbound only for system emails (password resets via SMTP). No inbound connections from unknown sources. |
| Chitu → EspoCRM | HTTPS + X-Api-Key header. Verified by `authenticate()` before any operation. |

### 5.7 Data Encryption

| Layer | Status |
|-------|--------|
| Transit (HTTPS) | Railway-provided TLS termination |
| Database at rest | Railway SSD volumes (physical encryption). Application-level encryption not required for Lead/Contact CRM data. |
| API credentials at rest | Railway secret-type variables (encrypted) |
| Backups at rest | S3 server-side encryption (AES-256) |

---

## 6. Local Validation Before Railway

**MANDATORY: All items must PASS before any Railway project is created.**

This section defines the local rehearsal that validates the deployment plan. Run this on the local Docker environment (`D:\EspoCRM-Test`) before touching Railway.

### 6.1 Environment Teardown & Fresh Start

```bash
# Stop and remove existing containers (preserve volumes for safety)
docker stop espocrm espocrm-db espocrm-daemon
docker rm espocrm espocrm-db espocrm-daemon

# Remove the old database volume (FRESH start)
docker volume rm espocrm-test_espocrm-db-data

# Start fresh
docker compose -f docker-compose.yml up -d

# Wait for healthy
docker ps --filter "name=espocrm" --format "table {{.Names}}\t{{.Status}}"
```

**Check:** All 3 containers show `(healthy)` status. `http://localhost:8080` returns EspoCRM installation/setup page.

### 6.2 Fresh EspoCRM Install

- [ ] Complete the EspoCRM installation wizard at `http://localhost:8080`
- [ ] Set admin username and password (record for this rehearsal)
- [ ] Configure database connection (espocrm-db:3306)
- [ ] Set site URL to `http://localhost:8080`
- [ ] Confirm installation completes without errors
- [ ] Log in as admin → verify dashboard loads

### 6.3 Extension Installation

- [ ] Build the release package: `.\espocrm_extension\scripts\build_release_package.ps1 -OutputPath .\releases\chitu-prospecting-v1.0.0.zip`
- [ ] Verify package SHA-256 matches recorded value
- [ ] Copy ZIP to EspoCRM container
- [ ] Install via CLI: `php command.php extension --install --file=/tmp/chitu-prospecting-v1.0.0.zip`
- [ ] `php command.php rebuild`
- [ ] `php command.php clear-cache`
- [ ] Verify: `php command.php extension --list` shows extension installed
- [ ] Verify: `grep ResearchEvidence data/cache/application/classmapEntities.php` returns entity class

### 6.4 Role Provisioning

- [ ] Copy `integration/espocrm_sync/provisioning/phase3a33_provision_roles.php` to EspoCRM container
- [ ] Run: `php /tmp/phase3a33_provision_roles.php`
- [ ] Output contains `PHASE3A33_PROVISION_DONE`
- [ ] Admin UI → Roles shows 4 roles: Admin, Integration Bot, Sales User, Sales Manager
- [ ] Admin UI → Teams shows Sales Team

### 6.5 User & API Key Creation

- [ ] Create API user `integration_bot` (type=api, role=Integration Bot)
- [ ] Generate API key for `integration_bot` — record for verification
- [ ] Create regular user `sales_test` (role=Sales User, team=Sales Team)
- [ ] Create regular user `manager_test` (role=Sales Manager, team=Sales Team)

### 6.6 Lead Workflow Validation

- [ ] Log in as `sales_test`
- [ ] Create a test Lead with company name, website, country
- [ ] Verify Lead appears in sales_test's Lead list
- [ ] Verify Lead detail shows Prospecting layout (6 sections)
- [ ] Verify AI/research fields are visible (read-only)
- [ ] Verify sync fields are NOT visible to sales_test
- [ ] Attempt to edit `peScoreTier` → should be rejected or silently ignored
- [ ] Attempt to delete Lead → should be denied (403)

### 6.7 Opportunity Workflow Validation

- [ ] Log in as `sales_test`
- [ ] Create an Opportunity linked to the test Lead
- [ ] Verify Opportunity appears in sales_test's Opportunity list
- [ ] Verify Opportunity Kanban board is accessible
- [ ] Verify `peEmailStatus` field is visible on Opportunity detail
- [ ] Verify `peProductInterest` field is visible on Opportunity detail

### 6.8 Dashboard Validation

- [ ] Log in as `sales_test`
- [ ] Home dashboard loads with Stream and My Activities dashlets
- [ ] Lead list is filterable by `peTierA` and `peRecentlySynced` primary filters
- [ ] Log in as `manager_test`
- [ ] Home dashboard loads with team visibility
- [ ] Export option available (manager-only)
- [ ] Log in as admin
- [ ] All dashboards load. Reports accessible.

### 6.9 Email Status Validation

- [ ] Verify `peEmailStatus` enum contains all expected values: `NONE`, `DRAFT_READY`, `APPROVED`, `SENT`, `REPLIED`, `BOUNCED`
- [ ] Verify `peEmailReplyStatus` field visible on Lead detail
- [ ] Verify `peLastEmailDate` field visible on Lead detail
- [ ] Verify `peEmailCampaignName` field visible on Lead detail
- [ ] Verify no SMTP/outbound email configuration exists (EspoCRM does not send outreach)

### 6.10 API Sync Simulation

Using the integration test suite against the local rehearsal environment:

```bash
python -m unittest tests.test_espocrm_real_client -v
```

- [ ] Authentication with API key succeeds
- [ ] Preflight returns 75 Lead fields + 17 ResearchEvidence fields
- [ ] Create Lead via API succeeds (200)
- [ ] Create Account via API succeeds (200)
- [ ] Create Contact via API succeeds (200)
- [ ] Create Opportunity via API succeeds (200)
- [ ] Create ResearchEvidence via API succeeds (200)
- [ ] Update Lead intelligence fields via API succeeds
- [ ] Delete Lead via API is denied (403)
- [ ] Delete ResearchEvidence via API is denied (403)

### 6.11 Full Test Suite

```bash
python -m unittest espocrm_extension.tests.test_extension_skeleton \
    tests.test_espocrm_sync_adapter \
    tests.test_espocrm_real_client \
    tests.test_espocrm_lifecycle_sync \
    tests.test_espocrm_email_lifecycle -v
```

- [ ] All tests pass (expected: 55+)
- [ ] Extension skeleton tests pass (18)
- [ ] Sync adapter tests pass
- [ ] Real client tests pass
- [ ] Lifecycle sync tests pass
- [ ] Email lifecycle tests pass

### 6.12 Backup and Restore Rehearsal

```bash
# 1. Create seed data (a test Lead with evidence)
#    (use API to create 1 Lead + 2 ResearchEvidence records)

# 2. Take database backup
docker exec espocrm-db mysqldump \
  --single-transaction --routines --events --triggers \
  --databases espocrm > rehearsal-backup-$(date +%Y%m%d-%H%M%S).sql

# 3. Record backup SHA-256
sha256sum rehearsal-backup-*.sql > rehearsal-backup.sha256

# 4. Delete the seed data (via API or Admin UI)

# 5. Restore backup
docker exec -i espocrm-db mysql espocrm < rehearsal-backup-YYYYMMDD-HHMMSS.sql

# 6. Rebuild cache
docker exec espocrm php command.php rebuild
docker exec espocrm php command.php clear-cache

# 7. Verify
#    - Seed Lead is restored with correct score and evidence
#    - Lead count matches pre-backup state
#    - Layout loads correctly
#    - API responds with 200
```

- [ ] Backup file created and SHA-256 recorded
- [ ] Backup file is non-empty and contains CREATE TABLE statements
- [ ] Seed data deleted successfully
- [ ] Restore completed without errors
- [ ] Seed data restored correctly
- [ ] Cache rebuild successful
- [ ] API and UI functional after restore

### 6.13 Extension Uninstall and Reinstall Rehearsal

```bash
# 1. Take backup (safety)
# 2. Uninstall extension
docker exec espocrm php command.php extension --uninstall --name="Chitu Prospecting Integration"

# 3. Rebuild cache
docker exec espocrm php command.php rebuild

# 4. Verify: custom fields removed, Lead layout reverted to default

# 5. Reinstall extension from ZIP
docker exec espocrm php command.php extension --install --file=/tmp/chitu-prospecting-v1.0.0.zip

# 6. Rebuild cache

# 7. Verify: extension reinstalled, fields restored, layout active
```

- [ ] Uninstall completes without errors
- [ ] Custom `pe*` fields removed after uninstall
- [ ] Reinstall completes without errors
- [ ] Custom fields, layouts, and metadata restored after reinstall
- [ ] Existing Lead records preserved (not deleted by extension uninstall)

### 6.14 Pre-Deployment Checklist (Before Railway)

| # | Item | Status |
|---|------|--------|
| 1 | Bump `manifest.json` version from `1.0.0-alpha` to `1.0.0` | ☐ |
| 2 | Rebuild release package with version `1.0.0` | ☐ |
| 3 | Record new package SHA-256 | ☐ |
| 4 | All local validation items (§6.1–§6.13) PASS | ☐ |
| 5 | Full test suite passes (55+ tests) | ☐ |
| 6 | Generate production passwords (admin, DB root, DB user) — 16+ chars each | ☐ |
| 7 | Store production passwords in approved secrets manager | ☐ |
| 8 | Confirm Railway account has billing configured | ☐ |
| 9 | Confirm Railway CLI is authenticated (`railway status`) | ☐ |
| 10 | Verify `espocrm/espocrm:10.0.1` is pullable on Railway's container registry | ☐ |
| 11 | Verify `mariadb:11.4` is pullable on Railway's container registry | ☐ |
| 12 | Verify `espocrm/espocrm-daemon:10.0.1` is pullable on Railway's container registry | ☐ |

**STOP if any item is not PASS.** Do not proceed to Railway deployment until all items are verified.

---

## 7. Deployment Sequence

### 7.1 Exact Order of Operations

```
PHASE 1: LOCAL FINAL VALIDATION
─────────────────────────────────
  1. Complete all items in Section 6 (Local Validation Before Railway)
  2. Bump manifest version to 1.0.0
  3. Build final release package → record SHA-256
  4. Full test suite → 55+ tests PASS
  5. Generate all production passwords → store in secrets manager
  6. Confirm Railway CLI authenticated and account active

PHASE 2: BACKUP (of local environment, as safety reference)
─────────────────────────────────
  7. Export local Docker database backup
  8. Export local EspoCRM custom/ directory archive
  9. Export extension package ZIP
 10. Store all backups in secure location

PHASE 3: RAILWAY PROJECT CREATION
─────────────────────────────────
 11. Create Railway project: "chitu-espocrm-prod"
 12. Create Railway shared environment variables:
     - ESPOCRM_ADMIN_USERNAME (value: admin)
     - ESPOCRM_ADMIN_PASSWORD (value: <from secrets manager>)
     - ESPOCRM_SITE_URL (will be set to Railway domain after service creation)
     - MARIADB_ROOT_PASSWORD (value: <from secrets manager>)
     - MARIADB_DATABASE (value: espocrm)
     - MARIADB_USER (value: espocrm)
     - MARIADB_PASSWORD (value: <from secrets manager>)
     - ESPOCRM_DATABASE_HOST (value: espocrm-db.railway.internal)
     - ESPOCRM_DATABASE_PORT (value: 3306)
     - ESPOCRM_DATABASE_NAME (value: espocrm)
     - ESPOCRM_DATABASE_USER (value: espocrm)
     - ESPOCRM_DATABASE_PASSWORD (value: <same as MARIADB_PASSWORD>)

PHASE 4: MARIADB SERVICE
─────────────────────────────────
 13. Create Railway service "espocrm-db"
     - Source: Docker image
     - Image: mariadb:11.4
     - Volume: espocrm-db-data (20 GB, mount: /var/lib/mysql)
     - NO public port/domain
 14. Wait for espocrm-db to show "healthy" status
 15. Verify: `railway run --service espocrm-db mysqladmin ping -h localhost`
     → "mysqld is alive"

PHASE 5: ESPOCRM SERVICE
─────────────────────────────────
 16. Create Railway service "espocrm"
     - Source: Docker image
     - Image: espocrm/espocrm:10.0.1
     - Volume: espocrm-custom (1 GB, mount: /var/www/html/custom)
     - Volume: espocrm-uploads (5 GB, mount: /var/www/html/data/upload)
     - Public domain: YES (generate Railway domain)
 17. After service creation, set ESPOCRM_SITE_URL to the Railway domain
    (e.g., https://chitu-espocrm-prod.up.railway.app)
 18. Run EspoCRM installation:
     railway run --service espocrm php command.php install \
       --admin-username="${ESPOCRM_ADMIN_USERNAME}" \
       --admin-password="${ESPOCRM_ADMIN_PASSWORD}" \
       --site-url="${ESPOCRM_SITE_URL}"
 19. Wait for espocrm to show "healthy" status
 20. Verify: open EspoCRM URL in browser → login page appears

PHASE 6: ESPOCRM DAEMON
─────────────────────────────────
 21. Create Railway service "espocrm-daemon"
     - Source: Docker image
     - Image: espocrm/espocrm-daemon:10.0.1
     - NO volume mounts
     - NO public port/domain
 22. Wait for espocrm-daemon to show "healthy" status
 23. Verify: daemon logs show successful DB connection

PHASE 7: EXTENSION INSTALL
─────────────────────────────────
 24. Upload extension ZIP to espocrm service
 25. Install extension:
     railway run --service espocrm php command.php extension \
       --install --file=/tmp/chitu-prospecting-v1.0.0.zip
 26. Rebuild cache:
     railway run --service espocrm php command.php rebuild
 27. Clear cache:
     railway run --service espocrm php command.php clear-cache
 28. Verify extension:
     railway run --service espocrm php command.php extension --list
     → "Chitu Prospecting Integration 1.0.0 [installed]"
 29. Verify metadata:
     railway run --service espocrm php -r \
       "echo count(json_decode(file_get_contents('data/cache/application/metadata.php'),true)['entityDefs']['Lead']['fields']??[]);"
     → Should return 75+ (native + 29 pe* + oa* fields)

PHASE 8: ACL SETUP
─────────────────────────────────
 30. Upload provisioning script to espocrm service
 31. Run provisioning:
     railway run --service espocrm php /tmp/phase3a33_provision_roles.php
     → "PHASE3A33_PROVISION_DONE"
 32. Verify 4 roles + Sales Team exist in Admin UI
 33. Create API user "integration_bot" (type=api, role=Integration Bot)
 34. Generate API key → store in secrets manager as ESPOCRM_API_KEY
 35. Create sales users (as needed by team)
 36. Verify Integration Bot has DELETE=no (attempt delete → 403)

PHASE 9: SMOKE TEST
─────────────────────────────────
 37. Admin login → dashboard loads
 38. Sales User login → dashboard loads, layout correct, ACL enforced
 39. Sales Manager login → team visibility works
 40. API call with Integration Bot key → GET /api/v1/ returns 200
 41. API preflight → returns correct field counts
 42. Create test Lead via API → 200
 43. Update Lead intelligence fields via API → 200
 44. Delete Lead via API → 403 (denied)
 45. Create test Lead via Admin UI → appears in list
 46. Create test Opportunity via Admin UI → Kanban shows it
 47. ENABLE Railway backups (daily cron or scheduled backup)
 48. TAKE FIRST PRODUCTION BACKUP

PHASE 10: PILOT PREPARATION
─────────────────────────────────
 49. Clean up test records (remove synthetic test data)
 50. Document production URL, API key location, admin credentials location
 51. Tag release: git tag v1.0.0-espocrm-extension
 52. STOP — await explicit authorization before importing real dealer data
```

### 7.2 Duration Estimates

| Phase | Steps | Estimated Duration |
|-------|-------|-------------------|
| 1. Local Final Validation | 1–6 | 1–2 hours (mostly automated) |
| 2. Backup | 7–10 | 10 minutes |
| 3. Railway Project Creation | 11–12 | 10 minutes |
| 4. MariaDB Service | 13–15 | 5 minutes |
| 5. EspoCRM Service | 16–20 | 10 minutes |
| 6. EspoCRM Daemon | 21–23 | 5 minutes |
| 7. Extension Install | 24–29 | 10 minutes |
| 8. ACL Setup | 30–36 | 20 minutes (manual role verification) |
| 9. Smoke Test | 37–48 | 30 minutes |
| 10. Pilot Preparation | 49–52 | 10 minutes |
| **Total** | | **~3 hours** |

---

## 8. Rollback Plan

### 8.1 Rollback Decision Criteria

Trigger rollback if any of these occur during deployment:

1. Extension install fails (CLI returns error)
2. `php command.php rebuild` fails
3. API returns non-200 after extension install
4. Lead layout does not render (returns core Overview/Details instead of Prospecting panels)
5. Role provisioning fails
6. Integration Bot receives 403 on ALL operations (not just delete)
7. Sales User can see sync fields (field ACL leak)
8. Sales User can edit AI fields (field ACL write leak)
9. Database connection fails after any service restart

### 8.2 Database Rollback

```bash
# 1. Stop EspoCRM to prevent writes
railway service stop --service espocrm
railway service stop --service espocrm-daemon

# 2. Drop corrupted database
railway run --service espocrm-db mysql \
  -u root -p"${MARIADB_ROOT_PASSWORD}" \
  -e "DROP DATABASE IF EXISTS espocrm; CREATE DATABASE espocrm;"

# 3. Restore from pre-deployment backup
railway run --service espocrm-db mysql \
  espocrm < espocrm-pre-deployment-backup.sql

# 4. Rebuild cache
railway service start --service espocrm
railway run --service espocrm php command.php rebuild
railway run --service espocrm php command.php clear-cache

# 5. Start daemon
railway service start --service espocrm-daemon

# 6. Verify
railway run --service espocrm php -r "echo 'OK';"
→ "OK"
```

### 8.3 Extension Rollback

If the extension installs but causes problems (e.g., broken layouts, missing metadata):

```bash
# 1. Uninstall extension
railway run --service espocrm php command.php extension \
  --uninstall --name="Chitu Prospecting Integration"

# 2. Rebuild cache
railway run --service espocrm php command.php rebuild
railway run --service espocrm php command.php clear-cache

# 3. Verify core EspoCRM is functional
#    - Login page loads
#    - Lead detail shows core Overview/Details
#    - API /api/v1/ returns 200

# 4. If uninstall fails: restore database from pre-extension backup (§8.2)
#    and manually remove custom/Espo/Modules/Prospecting/ files
```

### 8.4 Service Rollback

If a service update causes the container to fail:

```bash
# Railway supports rolling back to a previous deployment via dashboard.
# Navigate to: Project → Service → Deployments → select previous deployment → "Rollback"

# Manual rollback (if Railway rollback is not available):
# 1. Redeploy with the known-good image tag
railway service update --service espocrm --image espocrm/espocrm:10.0.1

# 2. Wait for health check to pass
# 3. Rebuild cache
railway run --service espocrm php command.php rebuild
```

### 8.5 Complete Disaster Recovery

If the entire Railway project becomes unrecoverable:

```text
1. Create NEW Railway project "chitu-espocrm-prod-recovery"
2. Set up identical services (espocrm, espocrm-db, espocrm-daemon)
3. Restore database from the most recent S3 backup
4. Install extension from release package
5. Run role provisioning
6. Rebuild cache
7. Verify data integrity
8. Update DNS/custom domain to point to new project
9. Create new API keys → update Chitu configuration
10. Verify full smoke test
```

**Recovery Time Objective (RTO):** < 1 hour
**Recovery Point Objective (RPO):** < 24 hours (based on daily backup)

---

## Appendix A: Environment Variables Quick Reference

### Shared (Railway project-level)

| Variable | Type | Service Access | Notes |
|----------|------|---------------|-------|
| `ESPOCRM_ADMIN_USERNAME` | normal | espocrm | Admin login username |
| `ESPOCRM_ADMIN_PASSWORD` | **secret** | espocrm | Admin login password (16+ chars) |
| `ESPOCRM_SITE_URL` | normal | espocrm | Set to Railway domain after creation |
| `MARIADB_ROOT_PASSWORD` | **secret** | espocrm-db | MariaDB root password (16+ chars) |
| `MARIADB_DATABASE` | normal | espocrm-db | Database name: `espocrm` |
| `MARIADB_USER` | normal | espocrm-db | Database user: `espocrm` |
| `MARIADB_PASSWORD` | **secret** | espocrm-db | Database user password (16+ chars) |
| `ESPOCRM_DATABASE_HOST` | normal | espocrm, daemon | `espocrm-db.railway.internal` |
| `ESPOCRM_DATABASE_PORT` | normal | espocrm, daemon | `3306` |
| `ESPOCRM_DATABASE_NAME` | normal | espocrm, daemon | `espocrm` |
| `ESPOCRM_DATABASE_USER` | normal | espocrm, daemon | `espocrm` |
| `ESPOCRM_DATABASE_PASSWORD` | **secret** | espocrm, daemon | Same as `MARIADB_PASSWORD` |
| `ESPOCRM_API_KEY` | **secret** | (not used by EspoCRM) | Integration Bot API key for Chitu → CRM calls |

### EspoCRM Service Only

| Variable | Value | Notes |
|----------|-------|-------|
| `ESPOCRM_CONFIG_USE_CACHE_IN_AUTH` | `true` | Performance |
| `ESPOCRM_CONFIG_IS_DEV_MODE` | `false` | Production mode |
| `ESPOCRM_CONFIG_AUTH_2FA` | `false` | 2FA managed per-user, not globally enforced |
| `ESPOCRM_CONFIG_AUTH_TOKEN_EXPIRED` | `86400` | 24h session |

---

## Appendix B: Railway CLI Quick Reference

```bash
# Login
railway login

# Link to project
railway link --project chitu-espocrm-prod

# List services
railway service list

# View logs
railway logs --service espocrm

# Run command in service
railway run --service espocrm php command.php rebuild

# View environment variables
railway variables list

# Set a secret variable
railway variables set ESPOCRM_ADMIN_PASSWORD --secret

# Deploy (trigger redeploy)
railway up --service espocrm

# Open service URL
railway open --service espocrm
```

---

## Appendix C: Docker Image Registry

| Image | Source | Pull Command |
|-------|--------|-------------|
| `espocrm/espocrm:10.0.1` | Docker Hub | `docker pull espocrm/espocrm:10.0.1` |
| `mariadb:11.4` | Docker Hub | `docker pull mariadb:11.4` |
| `espocrm/espocrm-daemon:10.0.1` | Docker Hub | `docker pull espocrm/espocrm-daemon:10.0.1` |

**Before deployment:** Verify all three images are pullable from Railway's container runtime. Railway uses standard Docker Hub registry — these should be available without additional configuration.

---

*End of document. No files were modified. No Railway project was created. No deployment was performed.*
