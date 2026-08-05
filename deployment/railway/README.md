# DP-WP5 Railway Execution Boundary

**Status:** implementation support only; deployment is not authorized.

Railway is an execution environment. It may build and run an approved immutable
image and perform availability checks. It has no migration, registration,
navigation-provisioning, or lifecycle authority.

## Required immutable inputs

- Base image: an approved `espocrm/espocrm:10.0.1@sha256:...` reference.
- DP-WP0 manifest SHA-256:
  `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649`.
- DP-WP0 source commit:
  `6ef712134f581a12a18da5c98691884e73388b78`.
- A separately obtained built-image digest.

Run `verify_deployment_identity.py` offline with those values before any future
authorization review. The verifier reads repository inputs only; it does not
build, pull, run, or inspect an image.

## Runtime boundary

The entrypoint may validate staging variables, reject a full application-root
volume, configure `PORT`, and start the supplied service process. It does not
delegate to an installation entrypoint and contains no installation, migration,
metadata rebuild, hook, or `AfterInstall` route.

The healthcheck makes only a local HTTP request. A passing response establishes
availability only; it is not registration, migration, or lifecycle evidence.

## Volume policy

The EspoCRM service may persist `/var/www/html/data` only. Do not mount
`/var/www/html`, `/var/www/html/custom`, or `/var/www/html/client/custom`;
those mounts can mask the verified image overlay. The wrapper fails closed if
it detects a full `/var/www/html` mount.

## Prohibited operations

No Railway build, deployment, release command, startup installation, migration,
provisioning, extension registration, metadata rebuild, hook, `AfterInstall`,
or production action is authorized by this directory or its tests.
