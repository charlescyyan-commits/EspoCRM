# C25 Staging Baseline Acceptance

**Review date:** 2026-08-06
**Scope:** Governance and verification documentation only
**Evidence mode:** Read-only live Railway review

## 1. Executive Verdict

**Status:**

```text
PASS WITH INFORMATIONAL NOTES
```

C25 staging satisfies the accepted baseline scope for availability, runtime
stability, installation state, and administrative access. This document does
not authorize business-feature, production-readiness, migration, or customer
data validation.

## 2. Environment Identity

| Field | Verified value |
| --- | --- |
| Project | `espocrm-c25` |
| Environment | `staging` |
| Service | `espocrm-c25-staging` |
| Deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` |
| Image digest | `sha256:59d3c93b5eb67e5260b82664c0bfa460707d919da5b5119474826eed3559f819` |
| Deployment status | `SUCCESS` |

## 3. Runtime Baseline

The accepted deployment records:

- Dockerfile builder;
- Dockerfile path `deployment/railway/Dockerfile`;
- no `startCommand` (`null` in the deployment manifest);
- active Railway staging entrypoint/wrapper;
- Apache `mpm_prefork` runtime guard passed; and
- healthcheck `/` returned HTTP `200`.

Runtime evidence included:

```text
railway-staging: starting DP-WP5 Railway service wrapper
railway-staging: Apache MPM runtime guard passed: mpm_prefork only
GET / HTTP/1.1" 200 ... "RailwayHealthCheck/1.0"
```

The prior `AH00534: More than one MPM loaded` crash signature was not present
in the accepted deployment runtime logs.

## 4. Storage Baseline

| Resource | Mount path | Preservation result |
| --- | --- | --- |
| Application volume | `/var/www/html/data` | Preserved; no reset; no deletion |
| MySQL volume | `/var/lib/mysql` | Preserved; no reset; no deletion |

The application volume and MySQL volume remained present and `Ready`. No
database reset, volume deletion, or storage replacement was performed.

## 5. EspoCRM Baseline

The accepted baseline records:

- EspoCRM installation completed;
- existing admin authentication verified with HTTP `200`;
- root page available as EspoCRM without an install loop; and
- database initialized and retained.

The installation deployment recorded `LAYER_A_INSTALL_COMPLETE`,
`Migration not needed: OK`, and `Database: OK`. The recovery deployment did
not run the installation command again.

## 6. Incident Closure Reference

**Reference:** DP-WP5 Runtime Recovery
**Status:** `CLOSED / ACCEPTED`

The temporary `startCommand` exceeded authorization and initialized staging.

Resolution:

- removed the temporary `startCommand`;
- preserved the database;
- preserved the volumes; and
- restored normal container startup.

## 7. Known Follow-ups

### 7.1 Build Snapshot Integrity

**Status:** `OPEN / FOLLOW-UP ONLY`

The current workspace snapshot must be reconciled with the frozen manifest
before any future source-driven rebuild. The integrity gate must not be
bypassed.

### 7.2 Apache AH00558 FQDN warning

**Status:** `INFORMATIONAL ONLY`

The Apache FQDN warning does not block startup, healthcheck, or the resolved
MPM guard failure.

### 7.3 Railway configuration readback hygiene

**Status:** `FUTURE CLEANUP`

The accepted deployment manifest resolves to Dockerfile, while a generic
service-instance readback still exposes default `RAILPACK`/empty values. This
does not block the accepted running deployment, but should be reconciled before
future source-driven deployment work.

## 8. Baseline Usage Boundary

This staging baseline may be used for:

- C25 feature validation;
- controlled implementation testing; and
- workspace verification.

The following are not authorized by this baseline:

- production deployment;
- customer data import or use;
- outbound automation; and
- real AI provider credentials.

Business features, AI providers, CRM workflows, data migration, and production
readiness are outside this acceptance scope.

## 9. Final Status

```text
C25 Staging Baseline:
PASS WITH INFORMATIONAL NOTES
```
