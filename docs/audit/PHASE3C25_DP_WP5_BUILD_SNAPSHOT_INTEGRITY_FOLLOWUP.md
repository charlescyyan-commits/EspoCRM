# DP-WP5 Build Snapshot Integrity Follow-up

**Opened:** 2026-08-06
**Status:** `OPEN / FOLLOW-UP REQUIRED`
**Owner boundary:** DP-WP5 build and release governance
**Related closure:** `PHASE3C25_DP_WP5_RUNTIME_RECOVERY_CLOSURE.md`

## 1. Observed condition

A new deployment from the current workspace snapshot failed at the existing
Dockerfile manifest integrity gate before image completion:

```text
test "$(sha256sum /opt/dp-wp0/full-application-artifact-manifest.json ...)" =
"9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649"
process ... did not complete successfully: exit code: 1
```

The gate is intentionally fail-closed. The failure was not bypassed, and it
did not alter the recovered staging runtime or its database.

## 2. Required follow-up

Before any future source rebuild:

1. Reconcile the working source snapshot with the frozen DP-WP0 manifest.
2. Produce a clean build input from the approved freeze boundary.
3. Verify the manifest checksum before submitting the build.
4. Rebuild with the pinned base-image reference and record the resulting image
   digest.
5. Run an independent build/release review before replacing the known-good
   staging image.

## 3. Explicit constraints

This follow-up does not authorize:

- bypassing or weakening the manifest checksum gate;
- changing the Dockerfile, entrypoint, or healthcheck as part of runtime
  closure;
- reinstalling EspoCRM or running migrations;
- resetting the database or deleting either volume; or
- replacing the accepted recovery deployment without separate authorization.

The existing freeze tag remains the reference implementation boundary:

```text
phase3c25-dp-wp5-railway-implementation-freeze
-> 2abd28769dc3fa7039d34df211c657ef7497270d
```

## 4. Exit criteria

Close this follow-up only after a separately authorized build demonstrates:

- the expected frozen manifest checksum;
- successful Dockerfile image creation;
- immutable base-image and output image digest evidence; and
- an independent review confirming that the runtime recovery closure remains
  unchanged.
