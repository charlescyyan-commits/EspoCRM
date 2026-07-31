# Railway C25 Staging Deployment

**Environment:** staging only  
**Production promotion:** forbidden  
**Builder:** Dockerfile (not Railpack / Nixpacks)  
**Pinned EspoCRM image:** `espocrm/espocrm:10.0.1`  
**Extension source:** `crm-extension/files/` → `/var/www/html/custom` + `/var/www/html/client/custom`

---

## 1. Root cause of previous Railway failure

| Fact | Implication |
| --- | --- |
| Repository is a **monorepo** (`crm-extension`, `chitu-connector`, `docs`, `tests`, …) | Root is not an EspoCRM web application |
| Local `EspoCRM/` is **untracked** and not on GitHub | Railpack cannot discover a PHP app root from git |
| Railpack looked for `start.sh` / language autodetection | No valid build plan → “Script start.sh not found” / “could not determine how to build” |

**Fix:** force Railway to use this Dockerfile with repository-root build context.

---

## 2. Architecture

```text
Railway Service (staging)
  Dockerfile: deployment/railway/Dockerfile
  FROM espocrm/espocrm:10.0.1
       │
       ├─ COPY crm-extension/files → /opt/crm-extension-overlay (pristine)
       ├─ COPY crm-extension/files → /var/www/html/{custom,client/custom}
       └─ ENTRYPOINT docker-entrypoint-railway.sh
              │
              ├─ refuse production / provider credential envs
              ├─ Apache Listen $PORT
              ├─ re-sync overlay → custom + client/custom
              ├─ clear data/cache if already installed
              └─ exec official docker-entrypoint.sh → apache2-foreground

Railway MySQL/MariaDB (staging-only plugin)
  ← ESPOCRM_DATABASE_* env mapping

Volume
  Mount Path: /var/www/html/data
  (config, cache, uploads — NOT full /var/www/html)
```

---

## 3. Railway dashboard settings

| Setting | Value |
| --- | --- |
| **Root Directory** | empty / repository root (`.`) |
| **Builder** | Dockerfile |
| **Dockerfile Path** | `deployment/railway/Dockerfile` |
| **Watch Paths** (optional) | `crm-extension/**`, `deployment/railway/**` |
| **Start Command** | **leave empty** |
| **Volume Mount Path** | `/var/www/html/data` |
| **Public Networking** | enable HTTP; Railway sets `PORT` |
| **Healthcheck Path** | `/` |
| **Environment** | staging variables only (see §5) |

Do **not** set Root Directory to `deployment/railway` — the Dockerfile must `COPY crm-extension/` from the repo root.

Do **not** mount `/var/www/html` as a single volume (legacy layout; blocks upgrades and hides image overlays until entrypoint re-syncs).

---

## 4. Volume strategy

| Path | Persist? | Why |
| --- | --- | --- |
| `/var/www/html/data` | **Yes** (Railway volume) | `config.php`, cache, uploads, install state |
| `/var/www/html/custom` | **No** (image + entrypoint sync) | Extension code must refresh on every deploy |
| `/var/www/html/client/custom` | **No** (image + entrypoint sync) | Client overlays must refresh on every deploy |
| `/var/www/html` (full) | **No** | Legacy; EspoCRM 10 warns and blocks clean upgrades |

**Overlay vs volume risk**

1. Extension is baked into the image and also stored at `/opt/crm-extension-overlay`.
2. Every container start re-syncs overlay → `custom/` and `client/custom/`.
3. After sync on an installed instance, `data/cache` is cleared so metadata reloads.
4. Full rebuild (`bin/command rebuild`) is **not** automatic on every boot (expensive). Run manually after major metadata changes if scopes do not appear.

---

## 5. Required variables

### Application service

| Variable | Required | Notes |
| --- | --- | --- |
| `PORT` | Railway-provided | Entrypoint binds Apache to this port |
| `APP_ENV` | yes | must be `staging` |
| `ESPOCRM_STAGING` | yes | `1` |
| `ESPOCRM_DATABASE_PLATFORM` | yes | `Mysql` |
| `ESPOCRM_DATABASE_HOST` | yes | Railway MySQL host / private DNS |
| `ESPOCRM_DATABASE_PORT` | yes | usually `3306` |
| `ESPOCRM_DATABASE_NAME` | yes | staging DB name only |
| `ESPOCRM_DATABASE_USER` | yes | staging user only |
| `ESPOCRM_DATABASE_PASSWORD` | yes | Railway secret — never commit |
| `ESPOCRM_ADMIN_USERNAME` | first install | change after first login |
| `ESPOCRM_ADMIN_PASSWORD` | first install | Railway secret — never commit |
| `ESPOCRM_SITE_URL` | yes | public `https://<staging-domain>` |
| `ESPOCRM_LANGUAGE` | optional | default `en_US` |

### Railway MySQL plugin mapping (example)

```text
ESPOCRM_DATABASE_HOST=${{MySQL.MYSQLHOST}}
ESPOCRM_DATABASE_PORT=${{MySQL.MYSQLPORT}}
ESPOCRM_DATABASE_NAME=${{MySQL.MYSQLDATABASE}}
ESPOCRM_DATABASE_USER=${{MySQL.MYSQLUSER}}
ESPOCRM_DATABASE_PASSWORD=${{MySQL.MYSQLPASSWORD}}
```

Use a **dedicated staging MySQL service**. Never point staging at a production database.

### Forbidden variables (entrypoint refuses to start)

- `INSTANTLY_API_KEY`
- `APOLLO_API_KEY`
- `APIFY_TOKEN` / `APIFY_API_TOKEN`
- `SMTP_PASSWORD`
- `BREVO_API_KEY`
- `ESPOCRM_ALLOW_PRODUCTION=1` / `APP_ENV=production`

---

## 6. First install (Railway)

1. Create a new Railway **project** named for staging (e.g. `espocrm-c25-staging`).
2. Add **MySQL** or **MariaDB** plugin (staging-only).
3. Add a service from this GitHub repo (`charlescyyan-commits/EspoCRM`), branch `master` (or staging branch).
4. Set Builder = Dockerfile, Dockerfile Path = `deployment/railway/Dockerfile`, Root Directory empty.
5. Attach volume → Mount Path `/var/www/html/data`.
6. Set environment variables from §5 (map MySQL plugin refs).
7. Set `ESPOCRM_SITE_URL` to the Railway public HTTPS URL.
8. Deploy. Watch logs for:
   - `railway-staging: configuring Apache to listen on PORT=...`
   - `railway-staging: overlay sync complete`
   - official `Running "install" action` / `Installation completed successfully`
9. Open `ESPOCRM_SITE_URL`, log in with admin credentials, change password.
10. Confirm Administration → Entity Manager shows Prospecting scopes (e.g. ProspectPool, SearchStrategy).

---

## 7. Redeploy (extension update)

1. Merge/push committed `crm-extension/files/**` changes (uncommitted local WIP will **not** be on Railway).
2. Redeploy the Railway service (image rebuild).
3. Entrypoint re-syncs overlay and clears `data/cache`.
4. If new entities do not appear, open a one-off shell / local exec and run:
   ```bash
   cd /var/www/html && bin/command rebuild
   ```
5. Data under `/var/www/html/data` remains on the volume across redeploys.

---

## 8. Local validation

From repository root:

```bash
# Build
docker compose -f deployment/railway/docker-compose.staging.yml build

# Run
docker compose -f deployment/railway/docker-compose.staging.yml up -d

# Wait for healthy, then:
curl -I http://localhost:18080/

# Confirm extension inside container
docker compose -f deployment/railway/docker-compose.staging.yml exec espocrm \
  test -d /var/www/html/custom/Espo/Modules/Prospecting

# Persistence check: restart web service, verify still installed
docker compose -f deployment/railway/docker-compose.staging.yml restart espocrm
curl -I http://localhost:18080/

# Tear down (keeps volumes unless -v)
docker compose -f deployment/railway/docker-compose.staging.yml down
```

Offline scaffold tests:

```bash
python -m pytest tests/test_railway_c25_staging_scaffold.py -q
```

---

## 9. Security & isolation checklist

| Check | Rule |
| --- | --- |
| Staging only | `APP_ENV=staging`; production promotion blocked |
| DB isolation | Dedicated staging MySQL; never production DSN |
| No provider creds | Entrypoint refuses Instantly/Apollo/Apify/SMTP/Brevo keys |
| No secrets in git | Use Railway variables / `.env` (gitignored) |
| No local EspoCRM vendor commit | Do not add `EspoCRM/` runtime tree |
| No architecture / business logic changes | Overlay only; no C20–C25 boundary edits in this scaffold |
| Credentials | Rotate staging admin password after first login |

---

## 10. Files in this directory

| File | Role |
| --- | --- |
| `Dockerfile` | Official EspoCRM pin + extension overlay |
| `docker-entrypoint-railway.sh` | PORT, overlay sync, staging guards |
| `healthcheck.sh` | HTTP / app-check health |
| `docker-compose.staging.yml` | Local validation stack |
| `.env.example` | Variable template (no secrets) |
| `railway.toml` | Builder hints |
| `README.md` | This document |

---

## 11. Remaining blockers (ops)

1. Railway project/service must be created in the dashboard (not done by this scaffold).
2. Staging MySQL plugin + variable mapping must be attached manually.
3. Only **committed** `crm-extension` files appear in remote builds — commit C25 WIP separately if needed on staging.
4. Optional daemon/websocket sidecars are out of scope for the minimal staging web service.
5. Production promotion requires a separate approved deployment charter — not this scaffold.
