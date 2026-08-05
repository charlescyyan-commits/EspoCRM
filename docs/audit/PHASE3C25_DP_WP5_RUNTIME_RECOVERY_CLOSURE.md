# DP-WP5 Runtime Recovery Closure

**Closure date:** 2026-08-06
**Scope:** Documentation and governance closure only
**Decision:** `CLOSED / ACCEPTED`

## 1. Final staging record

| Field | Verified value |
| --- | --- |
| Project | `espocrm-c25` |
| Environment | `staging` |
| Service | `espocrm-c25-staging` |
| Recovery deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` |
| Deployment status | `SUCCESS` |
| Image digest | `sha256:59d3c93b5eb67e5260b82664c0bfa460707d919da5b5119474826eed3559f819` |
| Builder | `DOCKERFILE` |
| Healthcheck | `/` -> HTTP `200` |
| Application volume | `/var/www/html/data` |

The recovery reused the known-good image and restored normal container startup.
No application code, Dockerfile, entrypoint, database, or volume was changed
by the closure activity.

## 2. Acceptance criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Dockerfile deployment | PASS | Recovery deployment manifest selected `DOCKERFILE` and `deployment/railway/Dockerfile`. |
| Normal startup | PASS | No temporary installation start command in the recovery deployment. |
| Apache runtime guard | PASS | Runtime logs prove `mpm_prefork only`. |
| Health | PASS | Railway healthcheck returned HTTP `200` for `/`. |
| EspoCRM installation | PASS | Installation completion and post-install checks were recorded in deployment `32e5d1c2-c001-4ff6-835a-cf6e85e25f7b`. |
| Existing admin | PASS | `App/user` authentication returned HTTP `200` for existing `admin`. |
| Database preservation | PASS | Existing MySQL service and volume remained present and running. |
| Application volume preservation | PASS | Existing application volume remained `Ready` at `/var/www/html/data`. |

## 3. Runtime guard evidence

The recovery deployment emitted:

```text
Apache/2.4.67 configured -- resuming normal operations
railway-staging: enforcing Apache mpm_prefork at runtime
railway-staging: Apache MPM runtime guard passed: mpm_prefork only
```

The prior `AH00534: More than one MPM loaded` crash-loop signature was not
present in the recovery runtime logs.

## 4. Installation evidence

The temporary installation deployment recorded:

```text
LAYER_A_INSTALL_BEGIN
The user 'admin' has been created.
Migration not needed: OK
Database: OK
Cron is enabled: OK
LAYER_A_INSTALL_COMPLETE
```

Subsequent container retries recorded `LAYER_A_ALREADY_INSTALLED`, confirming
that the installation marker was set and the installed state was reused. The
recovery deployment did not run the installation command again.

## 5. Database and volume preservation

The following resources remained unchanged and available:

| Resource | Identity | State |
| --- | --- | --- |
| Application volume | `espocrm-c25-staging-volume` / `24c49981-ee2c-4cc1-a043-893289e1f468` | `Ready`, `/var/www/html/data` |
| MySQL service | `a29fb2eb-b768-469a-9e50-a1aef825e99a` | `SUCCESS`, running |
| MySQL volume | `mysql-volume` / `19185432-0230-4e3e-b020-bdd806ae788c` | `Ready`, `/var/lib/mysql` |

No database reset, schema migration, volume deletion, admin recreation, or
reinstallation was performed during recovery.

## 6. Incident boundary

The temporary `startCommand` exceeded its authorization boundary and executed
the EspoCRM CLI installation path. That path initialized staging, created the
admin user and scheduled jobs, and initialized the database. The temporary
command then bypassed the normal runtime wrapper, producing the Apache MPM
crash loop.

The authorized recovery boundary was limited to:

- removing the temporary `startCommand`;
- reusing the existing installed state and database;
- restoring normal container startup; and
- verifying runtime health and login.

That boundary was respected during recovery.

## 7. Closure decision

```text
DP-WP5 Runtime Recovery: CLOSED / ACCEPTED
Deployment: 1dd8584c-f23a-45ba-89b6-51f2da95c2b1
Database and volumes: PRESERVED
Build Snapshot Integrity: FOLLOW-UP REQUIRED
```

This record closes the runtime incident. It does not close the separate build
snapshot integrity issue recorded in the companion follow-up.
