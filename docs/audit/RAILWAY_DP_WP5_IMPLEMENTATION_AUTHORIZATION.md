# DP-WP5 Railway Implementation Authorization

**Role:** Independent infrastructure authorization reviewer
**Decision date:** 2026-08-05
**Mode:** Governance authorization only
**Decision:** AUTHORIZED WITH CONDITIONS

## 1. Purpose and prerequisite state

This authorization permits a bounded implementation of the DP-WP5 Railway
execution boundary.  It is based on the following frozen or closed inputs:

| Work package | Required state |
| --- | --- |
| DP-WP0 release identity | Frozen |
| DP-WP1 native registration | Closed |
| DP-WP2 navigation | Frozen at `HOOK_PENDING` |
| DP-WP4 migration | Complete and frozen |
| DP-WP5 Railway design | Design ready |

This is not deployment authorization.  It does not authorize Railway access,
build execution, deployment, runtime execution, installation, CRM mutation, or
creation of a Railway service.

## 2. Authorized implementation scope

Only the following paths may be added or modified:

```text
deployment/railway/*
tests/test_railway_*.py
docs/audit/DP-WP5 evidence files
```

Implementation is limited to declarative execution-boundary controls and tests
that prove those controls.  It must not change extension payload, registration
records, migration definitions, lifecycle ledgers, navigation targets, CRM
application code, or unrelated repository files.

## 3. Docker image identity conditions

The implementation must make the deployable image independently identifiable.
Before a future deployment can be considered, its evidence must bind:

1. the immutable built-image digest;
2. the immutable base-image digest, rather than relying solely on an image tag;
3. the exact Dockerfile checksum and source revision;
4. the approved DP-WP0 overlay identity: extension name and version, source
   commit `6ef712134f581a12a18da5c98691884e73388b78`, and manifest SHA-256
   `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649`; and
5. hashes of the overlay inputs copied into the image.

An image with a matching tag but missing or mismatched immutable digest,
Dockerfile binding, or overlay binding is ineligible.

## 4. Entrypoint boundary

The entrypoint may perform only startup configuration needed to make the
already-approved application available, such as validating the environment,
configuring the listening port, presenting the verified immutable overlay, and
starting the application process.

The implementation and its tests must positively prove that neither the custom
entrypoint nor any delegated entrypoint path can execute:

- installation;
- migration or schema change;
- rebuild or metadata rebuild;
- hooks; or
- `AfterInstall`.

The upstream EspoCRM entrypoint is an untrusted delegated boundary until its
specific, pinned image digest and invocation mode are examined and constrained.
No automatic first-install path is permitted.  Cache handling, if retained,
must be explicitly limited to cache data, may not invoke a rebuild, and may not
be represented as lifecycle progress or completion.

## 5. Railway runtime boundary

Railway is an execution environment only.  A build, deployment, restart,
environment update, volume attach, log entry, health result, or runtime
observation cannot:

- change a DP lifecycle state;
- run a migration;
- provision CRM or navigation;
- create an extension registry record; or
- constitute evidence of lifecycle completion.

Only a separately authorized controlled operation may perform any such action.
Railway-provided logs and health telemetry may be retained as deployment
observations only; they are not ledger or completion evidence.

## 6. Health boundary

The healthcheck must be read-only and availability-only.  It may issue a
non-mutating local HTTP request or a non-mutating application readiness check.
It must not write cache, modify metadata, invoke a command that can repair or
rebuild, run migration/provisioning logic, call hooks, or invoke `AfterInstall`.

Passing health establishes only that the application is reachable at the
checked endpoint.  It does not prove registration, navigation provisioning,
migration completion, or any DP lifecycle transition.

## 7. Required implementation tests

The bounded implementation must include automated tests that at minimum verify:

1. the Dockerfile requires immutable image-digest binding and binds the approved
   overlay inputs;
2. the entrypoint contains no allowed execution route to installation,
   migration, rebuild, hooks, or `AfterInstall`;
3. `railway.toml` contains no release command or other lifecycle trigger;
4. the healthcheck is read-only and contains no mutation-capable command;
5. only `/var/www/html/data` is persistent, and a full application-root volume
   is rejected; and
6. prohibited production and provider-credential configuration is rejected or
   excluded by explicit policy.

## 8. Exit criteria and evidence

Implementation closure requires all of the following before a freeze review:

- passing implementation tests;
- a static implementation evidence record containing file checksums and test
  results;
- a deployment-evidence template that requires deployment identity, image
  digest, redacted environment evidence, volume evidence, and availability-only
  health evidence; and
- an independent review of the completed implementation and evidence.

Actual deployment evidence can be collected only after separate deployment
authorization.  It must not be fabricated, inferred from tests, or emitted by
Railway as evidence of DP completion.

## 9. Authorization state

```text
DP-WP5 Railway Implementation: AUTHORIZED WITH CONDITIONS
Deployment: NOT YET RUN
```

Any action outside the allowed paths or any runtime, Railway, CRM, registry,
ledger, migration, provisioning, hook, or `AfterInstall` action requires a new
explicit authorization.
