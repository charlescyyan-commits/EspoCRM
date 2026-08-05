# Railway DP-WP2 Recovery Admission Closure

| Field | Value |
| --- | --- |
| Record type | Recovery-admission authorization closure |
| Decision | **CLOSED — RATIFIED FOR COMPLETED `HOOK_PENDING` STOP LINE** |
| Date | 2026-08-05 |
| Work package | DP-WP2 navigation provisioning — recovery re-admission after baseline preparation |
| Prior freeze review | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_PROVISIONING_FINAL_FREEZE_REVIEW.md` — **PASS WITH CONDITIONS** |
| Runtime evidence | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_RUNTIME_EVIDENCE.md` — **PASS** |
| Baseline evidence | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_EVIDENCE.md` — **PASS** |
| Rule source | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION.md` §5 |
| Document authority | Closes freeze-review conditions F7/F8 for the navigation/`HOOK_PENDING` stop line only. It does **not** authorize hooks, migrations, Railway, ACL, dashboard, or CRM work. |

## 1. Purpose

This record retrospectively ratifies the governed recovery and
`BASELINE_RECOVERY_ADMISSION` path used to reach `HOOK_PENDING` after the first
navigation attempt failed closed with `NAVIGATION_BASELINE_UNRECOGNIZED` and
baseline preparation placed the exact `phase3c19-ia-v1` host navigation.

It satisfies the freeze-review requirement for a dedicated recovery-admission
closure after successful runtime evidence.

## 2. `FAILED_PRESERVED` Recovery Rule

When the durable record is `FAILED` / `FAILED_PRESERVED` with a prior failed
navigation step and a later successful baseline step:

1. Do **not** invent a synthetic navigation success marker.
2. Do **not** edit ledger JSON directly.
3. Recover only through DP-WP1.3 ledger interaction APIs:

```text
FAILED -> READY
READY  -> INSTALLING
INSTALLING -> REGISTERED
```

4. Revalidate extension registration and required modules **read-only**.
5. Do **not** reinstall the package, run AfterInstall, hooks, rebuilds, or
   migrations unless separately authorized.

Observed recovery for `installation-501688a00ef4b8e5ee083c1d` followed this
rule and restored `REGISTERED` without synthetic navigation success.

## 3. `BASELINE_RECOVERY_ADMISSION`

`BASELINE_RECOVERY_ADMISSION` is an administrative admission classification, not
a durable lifecycle state. It is authorized for `navigation_provisioning` only
when all are true under one durable-ledger lock:

1. `state == REGISTERED` after the governed recovery above.
2. A prior **failed** durable step exists for
   `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition`.
3. A prior **succeeded** durable step exists for
   `baseline:navigation_default_to_phase3c19_ia_v1`.
4. No prior **succeeded** navigation adapter step exists for that same
   navigation step id.
5. Operator supplies approved dependency evidence bound to the pinned release /
   `installationId` tuple.
6. Explicit operator invocation; lock held; ledger non-corrupt.

Host exact-target (or ratified permutation) verification remains enforced by the
reviewed navigation adapter. On success, the orchestrator alone may request
`REGISTERED → HOOK_PENDING` after recording the durable navigation success step.

`FIRST_RUNTIME_ADMISSION` remains reserved for a virgin `REGISTERED` record with
**no** prior navigation durable step and is not used for this recovery path.

## 4. No Synthetic Markers

This closure reaffirms:

- no pre-adapter navigation success step may be manufactured to force resume;
- baseline success does **not** substitute for
  `navigation_state_matches_definition`;
- recovery must not rewrite or delete the prior failed navigation step.

## 5. `HOOK_PENDING` Stop Line

The authorized and evidenced stop line is:

```text
REGISTERED
  -> BASELINE_RECOVERY_ADMISSION
  -> navigation_provisioning success (exact read-back)
  -> HOOK_PENDING
```

Live closure check (2026-08-05):

| Check | Result |
| --- | --- |
| Ledger state | `HOOK_PENDING` |
| Navigation success step | Present |
| Baseline success step | Present |
| Host postcondition SHA-256 | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| `MIGRATION_PENDING` / hooks / Railway | Absent / not executed |

## 6. Explicit Non-Authorization

This closure does **not** authorize:

- hook execution or `HOOK_PENDING → MIGRATION_PENDING`;
- migrations, schema/bootstrap, metadata refresh, or `COMPLETED`;
- Railway deployment/startup/restart;
- ACL, roles, teams, dashboards, preferences;
- AfterInstall/BeforeInstall;
- CRM business-data mutation;
- weakening the navigation adapter baseline gate.

## 7. Closure Decision

```text
Recovery-admission authorization gap (freeze F7): CLOSED by this record
Orchestrator admission amendments (freeze F8): committed/tagged with
  phase3c25-dp-wp2-navigation-frozen
Navigation provisioning stop line: FROZEN at HOOK_PENDING
```
