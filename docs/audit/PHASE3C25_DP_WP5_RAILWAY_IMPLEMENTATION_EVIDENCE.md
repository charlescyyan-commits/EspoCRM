# DP-WP5 Railway Implementation Evidence

**Date:** 2026-08-05
**Mode:** Offline implementation verification only
**Implementation state:** Complete pending independent review
**Deployment state:** Not run

## 1. Scope and identity

The implementation changes only `deployment/railway/*`,
`tests/test_railway_*.py`, and this DP-WP5 audit evidence file. No Railway
project, service, image build, container, production system, CRM instance,
migration, registry, ledger, hook, or `AfterInstall` action was executed.

The verifier binds future deployment evidence to:

| Identity input | Required value |
| --- | --- |
| Extension | Chitu Prospecting Integration 1.9.13-alpha |
| DP-WP0 source commit | `6ef712134f581a12a18da5c98691884e73388b78` |
| DP-WP0 manifest SHA-256 | `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649` |
| Base image | Approved immutable `sha256:` digest; not supplied or resolved in this implementation-only task |
| Built image | Immutable `sha256:` digest obtained only by a future authorized build; not produced here |

`deployment/railway/verify_deployment_identity.py` validates the manifest
checksum, release fields, every manifest file hash, Dockerfile bindings, and
the copied extension-manifest name/version, plus syntactic base/built image
digest inputs. It is offline and does not pull, build, inspect, or run an
image.

### Manifest identity amendment

The Dockerfile now checks the SHA-256 of the copied
`/opt/dp-wp0/full-application-artifact-manifest.json` during the image build.
It must equal the frozen DP-WP0 value above; otherwise the build fails closed
before an image can be produced. The active working-tree manifest remains a
user-owned modified file and does not currently have that value, so it cannot
be embedded successfully until the frozen manifest is restored as the build
input. The regression test reads the frozen `HEAD` manifest, confirms it
passes, then alters one byte and confirms rejection.

## 2. Entrypoint checks

`docker-entrypoint-railway.sh` is limited to:

- staging and provider-credential guards;
- rejection of a full `/var/www/html` mount;
- numeric `PORT` validation and Apache port configuration; and
- `exec "$@"` service startup.

It has no overlay-sync, cache-clear, upstream-entrypoint delegation,
installation, migration, rebuild, hook, or `AfterInstall` execution route.
Before `exec "$@"`, `guard_apache_mpm_prefork` removes any event/worker MPM,
checks the effective `apache2ctl -M` output, and fails closed unless exactly
one `mpm_prefork` module is loaded.

## 3. Healthcheck checks

`healthcheck.sh` issues a local HTTP request only. It does not invoke
`bin/command` or any application-maintenance action. A successful result is
availability evidence only and cannot imply a lifecycle, registration,
provisioning, or migration result.

## 4. Volume checks

The EspoCRM service declares only `/var/www/html/data` as its application
volume. Full application-root, `custom`, and `client/custom` mounts are not
declared; a detected full application-root mount causes entrypoint failure.

## 5. Forbidden-scope verification

Static tests verify no Railway release command and no entrypoint or healthcheck
route for installation, migration, metadata rebuild, hooks, or `AfterInstall`.
No deployment or runtime evidence is claimed by this record.

## 6. Test result

Offline static suite executed:

```text
C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -p test_railway_c25_staging_scaffold.py -v
Ran 13 tests in 0.057s
OK
```

Static input checksums recorded after that run:

| File | SHA-256 |
| --- | --- |
| `deployment/railway/Dockerfile` | `27593291c738ec21e36035c10e2489fc7d6e9c673add463410436b78981e1ed0` |
| `deployment/railway/docker-entrypoint-railway.sh` | `fd0656c9ce9690621dee674aeef3bb3ad8a41e245f1191475fb6a27dba968f81` |
| `deployment/railway/healthcheck.sh` | `dc972a3a2fbaf4458be2fe726ff660da5c171f55b0f37c31c0fedea2ebeb0d50` |
| `deployment/railway/verify_deployment_identity.py` | `80479a4dce7c4977badf31dd3d7388f278d8c52dbd41a485d72288833233581d` |
| `tests/test_railway_c25_staging_scaffold.py` | `f37ccfd5205604f9527ac2ea481890f1679564555dd663bece094b2ca35ab565` |

An independent review is required before any DP-WP5 implementation freeze; a
separate authorization is required before deployment.

## 7. Authorization state

```text
DP-WP5 Railway Implementation: AUTHORIZED WITH CONDITIONS
Deployment: NOT YET RUN
```
