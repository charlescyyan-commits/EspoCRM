# DP-WP5 Railway Implementation Freeze Closure

**Closure date:** 2026-08-05
**Role:** Release governance operator
**Mode:** Closure only
**Decision:** COMPLETE / FROZEN

## 1. Frozen implementation scope

The committed DP-WP5 implementation boundary consists of:

| Surface | Frozen responsibility |
| --- | --- |
| `deployment/railway/Dockerfile` | Immutable base-image input, frozen DP-WP0 identity labels, copied-manifest checksum gate, and image-local overlay inputs. |
| `deployment/railway/docker-entrypoint-railway.sh` | Staging guards, full-application-root mount rejection, port preparation, fail-closed Apache `mpm_prefork` runtime guard, and service startup only. |
| `deployment/railway/healthcheck.sh` | Read-only local HTTP availability check only. |
| `deployment/railway/verify_deployment_identity.py` | Offline manifest, overlay, extension-identity, Dockerfile, and supplied digest verification. |
| `deployment/railway/.env.example`, `docker-compose.staging.yml`, `railway.toml`, and `README.md` | Declarative execution-boundary and data-volume policy. |
| `tests/test_railway_c25_staging_scaffold.py` | Static regression coverage for the DP-WP5 boundary. |

## 2. Review evidence and amendment resolution

The independent review found that a frozen DP-WP0 label could coexist with a
copied manifest of another checksum. The amendment resolves that condition:

- Required frozen manifest SHA-256:
  `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649`.
- The Dockerfile computes the SHA-256 of the copied manifest and fails the
  build before image completion unless it equals that frozen value.
- The reusable verifier applies the same manifest checksum rule before overlay
  and identity verification.
- The static regression suite passed **13/13**, including the frozen `HEAD`
  manifest positive case, a byte-altered negative case, and Apache MPM
  guard ordering/conflict/prefork-negative coverage.

### MPM runtime guard amendment

The entrypoint now invokes `guard_apache_mpm_prefork` before `exec "$@"`. The
guard removes `mpm_event` and `mpm_worker`, enables `mpm_prefork`, inspects the
effective `apache2ctl -M` output, and exits non-zero unless exactly one
`mpm_prefork` module is loaded.

The re-frozen entrypoint checksum is:

```text
fd0656c9ce9690621dee674aeef3bb3ad8a41e245f1191475fb6a27dba968f81
```

The current user-owned working manifest remains outside this closure commit.
Its checksum differs from the frozen value, so the Dockerfile intentionally
fails closed until the frozen manifest is supplied as a future build input.

## 3. Boundary confirmation

Not executed during implementation, amendment, review, or closure:

- Railway deployment or Railway access;
- image build or container/runtime execution;
- migration, installation, provisioning, hooks, or `AfterInstall`;
- CRM mutation, registry creation, or ledger mutation; or
- lifecycle transition.

The freeze recognizes implementation controls only. It does not recognize a
deployment, image, migration, or lifecycle outcome.

## 4. Evidence references

- `PHASE3C25_DP_WP5_RAILWAY_IMPLEMENTATION_EVIDENCE.md` records source
  checksums, the offline test command, the 13/13 result, and the MPM guard
  checksum.
- `PHASE3C25_DP_WP5_MPM_GUARD_AMENDMENT_REVIEW.md` records the independent
  amendment review and re-freeze readiness.
- `RAILWAY_DP_WP5_IMPLEMENTATION_AUTHORIZATION.md` defines the approved
  implementation boundary and its conditions.
- The independent amendment re-review accepted the fail-closed checksum gate
  and recommended implementation freeze.

## 5. Authorization state

```text
DP-WP5 Railway Implementation: COMPLETE / FROZEN
Deployment: NOT AUTHORIZED
```

A deployment requires separate authorization, a restored frozen manifest as
the build input, immutable base and built-image digest evidence, and its own
independent review.
