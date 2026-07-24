# Phase3C17 Local Port Isolation Report

**Date:** 2026-07-23  
**Author:** DevOps — Charles Cy Yan  
**Scope:** Development environment port strategy for EspoCRM + CreateShape3D coexistence

---

## Problem

CreateShape3D Next.js dev server (`next dev -p 8080`) and the EspoCRM Docker container both claimed host port `8080`, creating a binding conflict. Playwright smoke validation proved the EspoCRM container was healthy internally (Apache returned 200 inside the container) but the browser could never reach it — all `http://localhost:8080` traffic was routed to CreateShape3D's Next.js process (PID 55148).

## Root Cause

Docker port publishing is first-come-first-served at the OS level. The CreateShape3D Node.js process bound `0.0.0.0:8080` before the EspoCRM container started (or the container was started after CreateShape3D already held the port). Docker's attempt to forward host `:8080` → container `:80` silently failed because the address was already in use, leaving the container healthy internally but unreachable from the host browser.

Evidence from `docker inspect espocrm`:
```json
"NetworkSettings.Ports": {"80/tcp": []}
```
The empty array confirms the host-side bind never succeeded despite the `PortBindings` configuration requesting `8080:80`.

## Existing Port Ownership (Pre-Fix)

| Port  | Owner              | Process              |
|-------|--------------------|----------------------|
| 8080  | CreateShape3D      | `node` PID 55148     |
| 8090  | (free)             | —                    |
| 80    | EspoCRM container  | Apache (internal)    |

## Selected Port Strategy

**Minimal-change approach: move EspoCRM host port only.**

| Service        | Host Port | Container Port | URL                          |
|----------------|-----------|----------------|------------------------------|
| CreateShape3D  | 8080      | N/A (native)   | `http://localhost:8080`      |
| CreateShape3D  | 3001      | N/A (native)   | `http://localhost:3001`      |
| EspoCRM        | **8090**  | 80             | `http://localhost:8090`      |

### Rationale

- CreateShape3D stays on its documented ports (8080, 3001) — zero disruption.
- EspoCRM moves to 8090 — adjacent, memorable, and the standard "second HTTP service" offset.
- Container internal port remains `:80` — no application config changes needed.
- `ESPOCRM_SITE_URL` updated to `http://localhost:8090` so generated URLs are correct.

## Changes

### 1. Container Recreation

| Aspect           | Before                          | After                           |
|------------------|---------------------------------|---------------------------------|
| Container name   | `espocrm`                       | `espocrm`                       |
| Old container    | —                               | `espocrm-backup-8080` (stopped) |
| Host port        | `8080:80`                       | `8090:80`                       |
| Internal port    | `:80`                           | `:80` (unchanged)               |
| `SITE_URL` env   | `http://localhost:8080`         | `http://localhost:8090`         |
| Image            | `espocrm/espocrm:10.0.1`        | `espocrm/espocrm:10.0.1`        |
| Network          | `espocrm-test_default`          | `espocrm-test_default`          |
| Volumes          | 3 named volumes (see below)     | Same 3 named volumes            |
| Restart policy   | `unless-stopped`                | `unless-stopped`                |

### 2. Volumes Preserved (Reattached, Not Recreated)

| Volume Name                     | Mount Point                          |
|---------------------------------|--------------------------------------|
| `espocrm-test-custom-client`    | `/var/www/html/client/custom`        |
| `espocrm-test-custom`           | `/var/www/html/custom`               |
| `espocrm-test-data`             | `/var/www/html/data`                 |

### 3. Database

`espocrm-db` (MariaDB 11.4) was never touched — no restart, no data migration.

### 4. Files Modified

**None.** No application code, metadata, PHP, ACL, workflow, navigation, or release artifact was changed. The only mutation was the Docker container's runtime port binding and one environment variable (`ESPOCRM_SITE_URL`).

## Data Safety

| Concern              | Status        | Detail                                           |
|----------------------|---------------|--------------------------------------------------|
| Database intact      | ✅ Confirmed   | `espocrm-db` never stopped                       |
| Volumes preserved    | ✅ Confirmed   | Same 3 named volumes reattached                  |
| Extensions retained  | ✅ Confirmed   | `client/custom` + `custom` volumes unchanged     |
| Metadata intact      | ✅ Confirmed   | No file modifications                            |
| C17 navigation       | ✅ Preserved   | No metadata/tabList changes                      |
| Rollback possible    | ✅ Available   | `espocrm-backup-8080` container preserved        |

## Verification

### Docker State

```
NAMES                 STATUS                      PORTS
espocrm               Up (healthy)                0.0.0.0:8090->80/tcp
espocrm-daemon        Up (healthy)                80/tcp
espocrm-cron          Up                           80/tcp
espocrm-db            Up (healthy)                3306/tcp
espocrm-backup-8080   Exited (0)                  (preserved)
```

### Service Reachability

| Test                                    | Result        | Detail                            |
|-----------------------------------------|---------------|-----------------------------------|
| EspoCRM internal (`docker exec curl`)   | ✅ 200        | Apache healthy inside container   |
| EspoCRM host (`localhost:8090`)         | ✅ 200        | Full login page with loader JSON  |
| CreateShape3D (`localhost:8080`)        | ✅ Next.js    | 500 from Next.js app (pre-existing app issue, not port-related) |

### C17 Navigation

C17 navigation state is fully preserved — no metadata, tabList, or ACL modifications were made. Navigation runtime inspectable on `http://localhost:8090`.

## Rollback

To restore the original `8080:80` mapping:

```bash
docker stop espocrm
docker rm espocrm
docker rename espocrm-backup-8080 espocrm
docker start espocrm
```

The backup container retains the exact pre-fix configuration including `ESPOCRM_SITE_URL=http://localhost:8080` and `8080:80` port binding.

---

## Summary

| Field               | Value                                    |
|---------------------|------------------------------------------|
| **Verdict**         | Port isolation achieved                  |
| **Root cause**      | Docker port 8080 bind failed — already held by CreateShape3D Next.js |
| **Port strategy**   | EspoCRM → 8090:80; CreateShape3D stays on 8080 |
| **CreateShape3D URL** | `http://localhost:8080`                |
| **EspoCRM URL**     | `http://localhost:8090`                  |
| **Docker mapping**  | `0.0.0.0:8090 → espocrm:80`              |
| **C17 validation**  | Preserved — no app/metadata changes      |
| **Files changed**   | 0                                        |
| **Commit**          | None                                     |
| **Push**            | None                                     |
