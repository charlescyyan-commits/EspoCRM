# DP-WP5 Apache MPM Guard Amendment Closure

**Date:** 2026-08-05
**Mode:** Closure evidence only
**Deployment:** Not run

## 1. Amendment scope

The runtime guard is present in
`deployment/railway/docker-entrypoint-railway.sh`. It executes after staging,
volume, and port checks and before `exec "$@"`. The guard removes
`mpm_event`/`mpm_worker`, enables `mpm_prefork`, inspects effective
`apache2ctl -M` output, and exits non-zero unless exactly one prefork MPM is
loaded.

No application, Dockerfile, database, migration, hook, `AfterInstall`, or
lifecycle logic was changed by this closure.

## 2. Regression coverage

`tests/test_railway_c25_staging_scaffold.py` now verifies:

- `guard_apache_mpm_prefork` exists and is invoked before `exec "$@"`;
- event and worker conflicts are explicitly disabled and fail closed;
- missing prefork is rejected; and
- the existing immutable-image, manifest, volume, healthcheck, and lifecycle
  boundary checks remain intact.

Result:

```text
Ran 13 tests in 0.057s
OK
```

## 3. Checksum evidence

| File | SHA-256 |
| --- | --- |
| `deployment/railway/docker-entrypoint-railway.sh` | `fd0656c9ce9690621dee674aeef3bb3ad8a41e245f1191475fb6a27dba968f81` |
| `tests/test_railway_c25_staging_scaffold.py` | `f37ccfd5205604f9527ac2ea481890f1679564555dd663bece094b2ca35ab565` |
| `docs/audit/PHASE3C25_DP_WP5_RAILWAY_IMPLEMENTATION_EVIDENCE.md` | Updated with the same entrypoint checksum and 13-test result |

## 4. Identity and boundary preservation

The DP-WP5 implementation remains related to frozen commit
`2abd28769dc3fa7039d34df211c657ef7497270d`; the DP-WP0 identity remains
unchanged. No app or database files changed, and no Railway deployment or
runtime action was executed.

## 5. Closure state

```text
MPM guard amendment closure: READY FOR RE-FREEZE
Deployment: NOT AUTHORIZED BY THIS RECORD
Production: NOT AUTHORIZED
```
