# Railway DP-WP2 Navigation Baseline Preparation Implementation Authorization

| Field | Value |
| --- | --- |
| Record type | Formal implementation authorization record |
| Decision | **PASS WITH CONDITIONS — IMPLEMENTATION AUTHORIZED ONLY FOR BASELINE PREPARATION** |
| Date | 2026-08-05 |
| Work package | DP-WP2 — navigation baseline preparation (default Espo 29-item → exact `phase3c19-ia-v1`) |
| Governing amendment | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_AMENDMENT.md` |
| Amendment review | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_AMENDMENT_REVIEW.md` — **PASS WITH CONDITIONS** |
| Blocking runtime evidence | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_RUNTIME_EVIDENCE.md` — `NAVIGATION_BASELINE_UNRECOGNIZED` |
| Navigation target contract | `docs/deployment/RAILWAY_DP_WP2_NAVIGATION_TARGET_CONTRACT.md` / `phase3c19-ia-v1` |
| Adapter baseline | `phase3c25-dp-wp2-navigation-adapter-complete` (`590a25e4347c24743752939f739cad9eea58d6e1`) — **read-only; must not be modified** |
| Document authority | Authorizes the allowlisted baseline-preparation implementation, focused tests, and evidence record only. It does **not** authorize navigation adapter changes, `HOOK_PENDING` success claims, Railway activation, or forbidden surfaces. |

## 1. Executive Verdict

```text
PASS WITH CONDITIONS — IMPLEMENTATION AUTHORIZED ONLY FOR BASELINE PREPARATION
```

Implementation of a narrowly scoped baseline-preparation runner is authorized so the
evidenced default EspoCRM **29-item** `config.tabList` can be replaced with the
exact approved **19-item** `phase3c19-ia-v1` definition, with checksum, diff,
read-back, and durable baseline-step evidence. The `navigation_provisioning`
permutation gate remains unchanged. Navigation re-admission toward
`HOOK_PENDING` remains blocked until `BASELINE_RECOVERY_ADMISSION` is
implemented under a separate allowlist (not this record) and executed under a
later operator task.

This record resolves amendment-review conditions F6–F10 for authorization
content. It does not itself execute the host write.

## 2. Exact File Allowlist

### 2.1 Implementation (create or modify)

```text
scripts/dp_wp2_navigation_baseline_preparation.py
```

### 2.2 Tests (create or modify)

```text
tests/test_railway_dp_wp2_navigation_baseline_preparation.py
```

### 2.3 Evidence (create after successful controlled execution)

```text
docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_EVIDENCE.md
```

### 2.4 Explicitly not on the allowlist

Any change outside §2.1–§2.3 is unauthorized under this record, including but
not limited to:

- `scripts/dp_wp2_phase_adapters/navigation_provisioning.py`
- `scripts/dp_wp2_provisioning_orchestrator.py` (recovery-admission wiring is a
  follow-on authorization; see §5)
- `scripts/dp_wp1_installation_foundation.py`
- `deployment/provisioning/phase3c17_provision_operational_centers_navigation.php`
- ACL, dashboard, migration, Railway, hook, or CRM business-data files

Temporary operator forensic artifacts under `temp/dp-wp2-navigation-runtime/`
may be used during controlled execution but are not authorized Git deliverables
unless separately accepted.

## 3. Pinned Identities and Checksums

| Field | Required value |
| --- | --- |
| `installationId` | `installation-501688a00ef4b8e5ee083c1d` |
| Extension name | `Chitu Prospecting Integration` |
| Extension version | `1.9.13-alpha` |
| Manifest SHA-256 | `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649` |
| Source commit | `6ef712134f581a12a18da5c98691884e73388b78` |
| Target definition | `deployment/navigation/phase3c17_navigation.json` |
| Navigation version | `phase3c19-ia-v1` |
| Target source SHA-256 | `ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e` |
| Canonical-definition SHA-256 | `bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6` |
| Expected postcondition SHA-256 | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Authorized unrecognized before checksum | `cd0179f6d0e0e2964076994197cd956a62ac1d0c7eccc92f051cde1d559bde8d` (canonical serialization of the evidenced coerced 29-item default `tabList`) |
| Durable baseline step id | `baseline:navigation_default_to_phase3c19_ia_v1` |
| Durable ledger path | `temp/dp-wp1-registration-evidence/installation-ledger.json` |

If the live before-checksum differs from the pinned value, the runner must fail
closed with a redacted mismatch code and must not write. A superseding
amendment is required to authorize a different unrecognized source class.

## 4. Allowed Operation

### 4.1 Sole permitted mutation

```text
default Espo 29-item config.tabList
  (before sha256:cd0179f6d0e0e2964076994197cd956a62ac1d0c7eccc92f051cde1d559bde8d)
→
exact phase3c19-ia-v1 19-item config.tabList
  (postcondition sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0)
```

Exactly one bounded `config.tabList` replacement to the exact approved ordered
list is permitted per successful attempt. No merge, no preservation of unknown
items, no permutation-only intermediate write under this authorization (exact
order required).

### 4.2 Frozen execution sequence

Baseline preparation runs while the durable record remains in `FAILED` /
`FAILED_PRESERVED` with prior
`NAVIGATION_BASELINE_UNRECOGNIZED` evidence. It does **not** clear that
disposition.

```text
1. Explicit operator invocation of the allowlisted runner only
2. Acquire DP-WP1.3 durable-ledger exclusive lock; reload
3. Verify identity + installationId + non-corrupt ledger
4. Verify state == FAILED and prior failed navigation step exists for
   adapter:navigation_provisioning:postcondition:navigation_state_matches_definition
5. Read-only registration + module validation (§6)
6. Read host tabList; compute before checksum; require exact pin match (§3)
7. Verify target definition checksums (§3)
8. Single config.tabList write to exact 19-item target
9. Fresh exact read-back; require postcondition checksum match
10. Record durable step
    baseline:navigation_default_to_phase3c19_ia_v1 / succeeded
    under the same lock while state remains FAILED
11. Release lock; retain evidence package (§7)
```

On any failure before or after write: record
`baseline:navigation_default_to_phase3c19_ia_v1 / failed` when a write was
attempted or a durable failure marker is required; leave or preserve `FAILED`;
no automatic retry.

Ledger recovery (`FAILED → READY → INSTALLING → REGISTERED`) and navigation
re-admission are **out of scope for this allowlist’s code**. They are governed
by §5 and require follow-on authorization before execution.

### 4.3 Required evidence artifacts (implementation must produce)

| Artifact | Requirement |
| --- | --- |
| Before checksum | SHA-256 of canonical pre-write top-level list; must equal pinned value |
| Target checksums | Source, canonical-definition, and expected postcondition from §3 |
| Exact `tabList` diff | Structured add/remove/reorder summary (identities + positions only) |
| Read-back verification | Fresh list equals exact target; evidence `sha256:fe0c9ed6…` |
| Durable baseline step | `baseline:navigation_default_to_phase3c19_ia_v1` succeeded under lock |
| Negative proof | Forbidden surfaces untouched |

Success postcondition name for baseline evidence only:

```text
name:     navigation_baseline_matches_definition
satisfied: true
evidence: sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0
```

This does **not** satisfy or replace
`navigation_state_matches_definition` for `navigation_provisioning`.

## 5. Recovery Governance — `BASELINE_RECOVERY_ADMISSION`

### 5.1 Definition

`BASELINE_RECOVERY_ADMISSION` is an administrative admission classification for a
later `navigation_provisioning` invoke. It is **not** a durable lifecycle state
and is **not** implemented by the §2.1 runner. Orchestrator wiring requires a
separate implementation authorization naming
`scripts/dp_wp2_provisioning_orchestrator.py` (and focused tests).

### 5.2 Preconditions (all required)

Under one durable-ledger lock, admit only when all are true:

1. `state == REGISTERED` after governed recovery
   `FAILED → READY → INSTALLING → REGISTERED` with revalidated registration
   evidence (§6); no package reinstall.
2. A prior **failed** durable step exists for
   `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition`.
3. A prior **succeeded** durable step exists for
   `baseline:navigation_default_to_phase3c19_ia_v1`.
4. No prior **succeeded** navigation adapter step exists for the same navigation
   durable step id (if one exists, use idempotent revalidation rules instead).
5. Host top-level navigation fresh read equals the exact approved 19-item target
   **or** is a ratified recognized permutation of that target.
6. Operator supplies approved dependency evidence bound to the §3 identity
   tuple; extension registered; required modules available.
7. Explicit operator invocation; lock held; ledger non-corrupt.

### 5.3 Effects

- May invoke the reviewed `navigation_provisioning` adapter only.
- Must not invent synthetic navigation success markers.
- On adapter success: record the navigation durable success step, then
  `REGISTERED → HOOK_PENDING` only through existing orchestrator authority.
- On adapter failure: preserve `FAILED` / `FAILED_PRESERVED` as today.

### 5.4 Explicitly not authorized by this record

Execution of ledger recovery or `BASELINE_RECOVERY_ADMISSION` is **not**
authorized here. This section freezes the rule so the follow-on orchestrator
authorization cannot invent a weaker gate.

## 6. Registration Validation

### 6.1 Allowed

Read-only verification only:

- `php command.php extension --list` (or equivalent read-only Extension entity
  observation) proving name/version installed;
- read-only metadata presence for `ProspectingDashboard`, `ProspectingSearch`,
  and `DraftApproval`;
- citation of existing DP-WP1 native registration evidence
  (`docs/audit/RAILWAY_DP_WP1_NATIVE_REGISTRATION_EVIDENCE.md`) as historical
  context, not as a license to reinstall.

### 6.2 Forbidden

- Extension upload/install/reinstall;
- `BeforeInstall.php` / `AfterInstall.php`;
- hooks, workflows, jobs;
- metadata rebuild / clear-cache (unless a separate amendment authorizes it);
- migrations / DDL / schema work;
- any package or registry mutation.

## 7. Forbidden Scope

This authorization does **not** permit:

- ACL, roles, teams, or field-visibility changes;
- dashboards, dashlets, branding, or preferences;
- migrations, schema/bootstrap, or database repair;
- Railway deployment, compose, startup/restart, healthcheck, volume, or
  environment mutation;
- hooks, workflows, jobs, or AfterInstall/BeforeInstall;
- CRM business-data mutation;
- the legacy C17 navigation materializer / snapshot / restore tooling;
- modification of the `navigation_provisioning` adapter or weakening of
  `NAVIGATION_BASELINE_UNRECOGNIZED`;
- direct ledger JSON edits or direct SQL against configuration stores;
- synthetic resume or navigation success markers;
- claiming `HOOK_PENDING`, completed navigation provisioning, or Railway
  activation as an outcome of this allowlist.

## 8. Exit Criteria

Implementation under this authorization is complete only when all are true:

1. **Allowlist only** — git diff confined to §2.1–§2.2 for code/tests; evidence
   file §2.3 added only after controlled execution.
2. **Tests pass** — `tests/test_railway_dp_wp2_navigation_baseline_preparation.py`
   covers at least: pinned before-checksum gate; exact target write + read-back;
   durable baseline step on `FAILED` without clearing disposition; mismatch fail
   closed; registration-missing fail closed; no business-data touch.
3. **Baseline evidence generated** —
   `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_EVIDENCE.md`
   with §4.3 artifacts after a controlled operator run.
4. **No navigation adapter modification** — adapter file/hash unchanged from
   `590a25e4347c24743752939f739cad9eea58d6e1` baseline content.
5. **No runtime provisioning success claim** — evidence must not assert
   `HOOK_PENDING`, successful `navigation_state_matches_definition` adapter
   step, or completed DP-WP2 provisioning.

Until exit criteria are met, baseline preparation is unfinished. Meeting them
still does **not** authorize navigation re-admission execution.

## 9. Authorization State

| Scope | State |
| --- | --- |
| Baseline-preparation implementation (§2.1–§2.2) | **AUTHORIZED WITH CONDITIONS** |
| Controlled baseline host write + evidence (§2.3) | **AUTHORIZED after tests pass; separate operator execution task** |
| `navigation_provisioning` adapter changes | **NOT AUTHORIZED** |
| Orchestrator `BASELINE_RECOVERY_ADMISSION` wiring | **DEFINED HERE; IMPLEMENTATION NOT AUTHORIZED** |
| Ledger recovery to `REGISTERED` | **NOT AUTHORIZED by this record** |
| Navigation re-admission / `HOOK_PENDING` | **NOT AUTHORIZED** |
| Forbidden surfaces (§7) | **NOT AUTHORIZED** |

## 10. Next Action

1. Implement allowlisted runner + tests; run focused suite.
2. Operator-controlled baseline preparation execution against staging; write
   evidence record §2.3.
3. Issue a separate implementation authorization for orchestrator
   `BASELINE_RECOVERY_ADMISSION` + governed `FAILED → … → REGISTERED` recovery
   procedure.
4. Only then re-admit `navigation_provisioning` toward `HOOK_PENDING`.
