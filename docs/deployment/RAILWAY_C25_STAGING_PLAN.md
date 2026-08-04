# Railway C25 Staging Deployment Plan

| Field | Value |
| --- | --- |
| Document Type | Operational Deployment Plan |
| Environment | **staging only** |
| Production promotion | **forbidden** |
| Baseline commit | `44d9ffa` — `feat(deploy): add Railway C25 staging EspoCRM Dockerfile scaffold` |
| Repo | https://github.com/charlescyyan-commits/EspoCRM |
| Branch | `master` |
| Scaffold docs | `deployment/railway/README.md` |
| Status | READY TO EXECUTE IN RAILWAY DASHBOARD |

This plan tells an operator **exactly how to create and verify** the first C25 staging EspoCRM service on Railway. It does not authorize production, provider credentials, code changes, or promotion.

---

## 0. Preconditions (already satisfied)

| Check | Evidence |
| --- | --- |
| Scaffold committed | `44d9ffa` |
| Scaffold on `origin/master` | local HEAD == `origin/master` == `44d9ffa` |
| Builder is Dockerfile (not Railpack) | `deployment/railway/Dockerfile` + `railway.toml` |
| Local validation | docker build/run, HTTP 200, overlay present, pytest 15 passed |
| Staging guards | entrypoint refuses `APP_ENV=production` and Instantly/Apollo/Apify/SMTP/Brevo keys |

Do **not** wait for unrelated local dirty/untracked files. Railway builds from GitHub `master` at `44d9ffa` (plus later commits). Uncommitted WIP will not appear in the deploy.

---

## 1. Goal

Stand up a disposable **EspoCRM 10.0.1** staging instance that:

1. Builds from the monorepo via Dockerfile
2. Loads `crm-extension/files` overlay at container start
3. Uses an isolated staging MySQL/MariaDB
4. Persists only `/var/www/html/data`
5. Exposes public HTTP health on `/`
6. Never connects to real Instantly / Apollo / Apify / SMTP providers
7. Never points at a production database

---

## 2. Architecture (deploy target)

```text
GitHub master @ 44d9ffa+
        │
        ▼
Railway Project: espocrm-c25-staging   (name suggestion)
   │
   ├─ Service: espocrm-web
   │    Builder: DOCKERFILE
   │    Dockerfile: deployment/railway/Dockerfile
   │    Root Directory: (empty = repo root)
   │    Start Command: (empty)
   │    Volume: /var/www/html/data
   │    Public HTTP + healthcheck /
   │
   └─ Plugin: MySQL or MariaDB (staging-only)
        ↕ ESPOCRM_DATABASE_* variable references
```

Pinned image inside Dockerfile: `espocrm/espocrm:10.0.1`.

---

## 3. Execution checklist (Railway dashboard)

### Step A — Create project

1. Open Railway → **New Project**
2. Name: `espocrm-c25-staging` (or equivalent staging-only name)
3. Do **not** reuse a production project

### Step B — Add staging database

1. Add plugin: **MySQL** or **MariaDB**
2. Keep default generated credentials in Railway secrets
3. Confirm this plugin is **not** shared with any production service
4. Note the private variable names Railway exposes (typically `MYSQLHOST`, `MYSQLPORT`, `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD` — exact names may vary by plugin UI)

### Step C — Add web service from GitHub

1. **Add Service** → Deploy from GitHub repo `charlescyyan-commits/EspoCRM`
2. Branch: `master`
3. Wait for first auto-detect attempt if it starts — you will override builder next

### Step D — Force Dockerfile settings

In service **Settings**:

| Setting | Required value |
| --- | --- |
| Root Directory | **empty** (repository root) |
| Builder | **Dockerfile** |
| Dockerfile Path | `deployment/railway/Dockerfile` |
| Watch Paths (optional) | `crm-extension/**`, `deployment/railway/**` |
| Custom Start Command | **empty / cleared** |
| Healthcheck Path | `/` |
| Healthcheck Timeout | `300` seconds (first install is slow) |

If Railway still selects Railpack/Nixpacks, stop the deploy and re-save Builder = Dockerfile.

### Step E — Attach volume

| Setting | Value |
| --- | --- |
| Volume Mount Path | `/var/www/html/data` |
| Size | start small (Railway default is fine for staging) |

**Forbidden mount:** `/var/www/html` (full tree). That is legacy and blocks clean upgrades/overlays.

### Step F — Set environment variables

#### Required on web service

| Variable | Value |
| --- | --- |
| `APP_ENV` | `staging` |
| `ESPOCRM_STAGING` | `1` |
| `ESPOCRM_DATABASE_PLATFORM` | `Mysql` |
| `ESPOCRM_DATABASE_HOST` | `${{MySQL.MYSQLHOST}}` *(adjust plugin name)* |
| `ESPOCRM_DATABASE_PORT` | `${{MySQL.MYSQLPORT}}` |
| `ESPOCRM_DATABASE_NAME` | `${{MySQL.MYSQLDATABASE}}` |
| `ESPOCRM_DATABASE_USER` | `${{MySQL.MYSQLUSER}}` |
| `ESPOCRM_DATABASE_PASSWORD` | `${{MySQL.MYSQLPASSWORD}}` |
| `ESPOCRM_ADMIN_USERNAME` | staging admin (e.g. `admin`) |
| `ESPOCRM_ADMIN_PASSWORD` | strong unique staging secret |
| `ESPOCRM_SITE_URL` | `https://<railway-public-domain>` (set after domain known; redeploy if needed) |
| `ESPOCRM_LANGUAGE` | `en_US` |

`PORT` is injected by Railway — do not hardcode.

#### Forbidden (must remain unset)

- `INSTANTLY_API_KEY`
- `APOLLO_API_KEY`
- `APIFY_TOKEN` / `APIFY_API_TOKEN`
- `SMTP_PASSWORD`
- `BREVO_API_KEY`
- `APP_ENV=production`
- `ESPOCRM_ALLOW_PRODUCTION=1`

Entrypoint will refuse to start if these are present.

### Step G — Deploy

1. Trigger **Deploy**
2. Watch build logs for Docker build (not Railpack)
3. Watch runtime logs for:

```text
railway-staging: configuring Apache to listen on PORT=...
railway-staging: overlay sync complete (Prospecting present)
info: Running "install" action.
info: Installation completed successfully.
```

4. First boot may take several minutes (DB wait + install + rebuild)

### Step H — Post-deploy smoke

1. Open public URL → HTTP 200 / login page
2. Login with staging admin → **change password immediately**
3. Confirm Prospecting scopes exist (e.g. ProspectPool / SearchStrategy) in Entity Manager or UI
4. Optional one-off shell:

```bash
test -d /var/www/html/custom/Espo/Modules/Prospecting && echo OK
bin/command app-check
```

5. Redeploy once after `ESPOCRM_SITE_URL` is finalized if the first deploy used a placeholder URL

---

## 4. Acceptance criteria

| # | Criterion | Pass? |
| --- | --- | --- |
| 1 | Build uses Dockerfile path `deployment/railway/Dockerfile` | ⬜ |
| 2 | No Railpack / `start.sh not found` errors | ⬜ |
| 3 | Install completes; `app-check` OK | ⬜ |
| 4 | Public `/` returns success | ⬜ |
| 5 | Prospecting module present under `custom/Espo/Modules/Prospecting` | ⬜ |
| 6 | Volume persists across restart (still installed after redeploy) | ⬜ |
| 7 | DB is staging plugin only (not production DSN) | ⬜ |
| 8 | No provider credential env set | ⬜ |
| 9 | `APP_ENV=staging` | ⬜ |

All boxes must be checked before calling staging “up”.

---

## 5. Redeploy / extension update procedure

1. Merge/push committed `crm-extension/files/**` changes to `master`
2. Redeploy Railway web service (rebuild image)
3. Entrypoint re-syncs overlay and clears `data/cache`
4. If new entities missing, run once:

```bash
cd /var/www/html && bin/command rebuild
```

5. Data under `/var/www/html/data` remains on the volume

---

## 6. Rollback

| Scenario | Action |
| --- | --- |
| Bad web deploy | Redeploy previous successful Railway deployment |
| Bad extension overlay | Revert git commit on `master`, redeploy |
| Corrupt app state | Keep DB volume; clear/recreate **only** web volume `/var/www/html/data` as last resort (re-install) |
| Wrong database | Stop web service; never reconnect to production DB |

Production promotion remains forbidden — there is no prod cutover path in this plan.

---

## 7. Out of scope

- Production Railway project / prod DB
- Instantly / Apollo / Apify / SMTP integration
- Daemon / websocket sidecars (optional later)
- Committing local `EspoCRM/` runtime tree
- Amending `44d9ffa` or changing scaffold in this plan
- C25 business-logic implementation changes

---

## 8. Operator notes

1. Railway Root Directory must stay empty so `COPY crm-extension/...` works.
2. Only **committed** extension files appear in remote builds.
3. Staging admin password is a Railway secret — rotate after first login.
4. If first install fails on DB connect, re-check variable references to the MySQL plugin service name.
5. Detailed rationale and local compose validation remain in `deployment/railway/README.md`.

---

## 9. Immediate next action

**Execute Steps A–H in the Railway dashboard now**, using GitHub `master` at/after `44d9ffa`.

When complete, record:

- Railway project URL
- Public staging URL
- Deploy ID / successful deployment timestamp
- Acceptance checklist results (§4)

---

*Operational plan only. Does not authorize production promotion, provider credentials, code changes, commits, tags, or force pushes.*
