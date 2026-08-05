# Railway DP-WP2 Navigation Baseline Preparation Amendment

| Field | Value |
| --- | --- |
| Record type | Architecture governance amendment |
| Decision | **AUTHORIZED WITH CONDITIONS (governance design only — no runtime execution)** |
| Date | 2026-08-05 |
| Work package | DP-WP2 — navigation baseline preparation (unrecognized default → approved `phase3c19-ia-v1`) |
| Blocking evidence | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_RUNTIME_EVIDENCE.md` — `NAVIGATION_BASELINE_UNRECOGNIZED` |
| Governing target | `deployment/navigation/phase3c17_navigation.json` / `phase3c19-ia-v1` |
| Target source SHA-256 | `ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e` |
| Canonical-definition SHA-256 | `bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6` |
| Expected postcondition SHA-256 | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Release identity | `Chitu Prospecting Integration` `1.9.13-alpha` / manifest `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649` / commit `6ef712134f581a12a18da5c98691884e73388b78` |
| Installation identity | `installation-501688a00ef4b8e5ee083c1d` |
| Document authority | Defines the missing baseline-preparation boundary only. It does **not** execute preparation, recover the ledger, invoke the navigation adapter, or authorize Railway/ACL/dashboard/migration/hook work. |

## 1. Executive Verdict

The reviewed `navigation_provisioning` adapter correctly refused to write when the
host `config.tabList` was the default EspoCRM **29-item** layout. Under the
ratified target contract, a write is allowed only when the current list is
already a **recognized permutation** of the approved **19-item**
`phase3c19-ia-v1` target. That leaves a governed gap: first materialization from
an unrecognized default baseline is outside adapter authority and must not be
simulated by merging, repairing, or running a legacy materializer.

This amendment **defines** a separate, narrowly scoped **baseline preparation**
action that may later place the host navigation surface onto the approved
19-item definition (exact order) so a subsequent `navigation_provisioning`
admission can succeed. It authorizes the governance model and evidence/recovery
rules only. **Runtime execution and implementation remain NOT AUTHORIZED** until
a separate implementation authorization is issued and independently reviewed.

## 2. Decision

```text
AUTHORIZED WITH CONDITIONS — governance design of baseline preparation
NOT AUTHORIZED — runtime execution, implementation, ledger recovery, or adapter re-admission
```

| Gate | Result |
| --- | --- |
| Problem is real and evidenced | PASS — `NAVIGATION_BASELINE_UNRECOGNIZED`; 29 ≠ 19; zero write |
| Adapter must not expand to merge/repair | PASS — adapter permutation gate preserved |
| Legacy materializer must remain forbidden | PASS — C17 PHP materializer stays out of scope |
| Separate preparation action is required | PASS — defined here as host `config.tabList` only |
| Ledger recovery after failed navigation | PASS — governed `FAILED → READY` retry + re-registration proof, then re-admission rules |
| Execution in this document | FAIL / blocked — design only |

## 3. Baseline Transition

### 3.1 Problem statement

```text
current host baseline:  default EspoCRM 29-item config.tabList (unrecognized)
required approved baseline: phase3c19-ia-v1 exact 19-item topLevelOrder
adapter gate today:     recognized permutation of the 19-item set only
observed failure:       NAVIGATION_BASELINE_UNRECOGNIZED (no write)
ledger after attempt:   FAILED / FAILED_PRESERVED
```

### 3.2 Approved end state of baseline preparation

Baseline preparation is complete only when a fresh read of the host top-level
navigation surface equals the ratified target **value-for-value and
position-for-position** (the exact §3.2 order of the navigation target
contract), including divider `type` / `id` / `text` and module names.

A recognized **permutation** of the 19 items is an acceptable intermediate host
state for a later adapter reorder, but the preferred preparation outcome for
this amendment is the **exact** approved order so the subsequent
`navigation_provisioning` call is a no-write success (`REVALIDATE_AND_NOOP`).

### 3.3 Transition model

Baseline preparation is **not** a new DP-WP1.4 lifecycle state and is **not** a
`navigation_provisioning` adapter write under the permutation gate. It is a
separate administrative configuration action with its own durable step identity:

```text
step id (proposed):
  baseline:navigation_default_to_phase3c19_ia_v1

allowed host mutation:
  config.tabList  ->  exact phase3c19-ia-v1 topLevelOrder only

disallowed:
  merge unknown items, preserve extras, ACL/role changes, legacy materializer,
  snapshots/restore tooling, SQL, direct ledger JSON edits
```

Governed sequence after this amendment is ratified for implementation:

```text
1) FAILED_PRESERVED (NAVIGATION_BASELINE_UNRECOGNIZED) remains frozen
2) explicit baseline preparation (this amendment's future implementation)
     -> durable baseline step succeeded
     -> host tabList exact-match read-back
3) governed ledger recovery:
     FAILED -> READY
     READY  -> INSTALLING
     INSTALLING -> REGISTERED
   using revalidated DP-WP1 registration/module evidence (no package reinstall,
   no AfterInstall, no rebuild unless separately authorized)
4) explicit navigation re-admission under a reviewed recovery-admission rule
     (see §5.3) because a prior failed navigation step already exists
5) navigation_provisioning success evidence
     -> REGISTERED -> HOOK_PENDING
```

Steps 2–5 are **not** authorized by this document; they require a separate
implementation authorization that cites this amendment.

### 3.4 What this amendment deliberately does not do

- It does **not** weaken `NAVIGATION_BASELINE_UNRECOGNIZED` inside the existing
  adapter so that unrecognized defaults can be overwritten silently.
- It does **not** authorize `deployment/provisioning/phase3c17_provision_operational_centers_navigation.php`
  or any legacy snapshot/restore path.
- It does **not** invent a synthetic successful
  `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition`
  event to bypass admission.

## 4. Authority

### 4.1 Who may perform first baseline preparation

Only a **named human operator** acting under a future implementation
authorization that references this amendment and the exact release /
`installationId` tuple below. No container start, healthcheck, scheduler,
release command, browser action, CI job, or Railway deploy may perform it.

### 4.2 Explicit invocation requirements

1. Written implementation authorization exists and names the operator role.
2. Preconditions are verified before any write:
   - durable ledger is non-corrupt and lockable;
   - identity matches the pinned release tuple;
   - extension remains registered at exact name/version;
   - required modules remain available;
   - current failure (if any) is `NAVIGATION_BASELINE_UNRECOGNIZED` or the host
     baseline is independently proven unrecognized;
   - target definition checksums match this amendment header.
3. Invocation is a single explicit command/script path reviewed in that
   implementation authorization — not an in-adapter side effect.
4. At most one bounded `config.tabList` replacement to the exact approved
   19-item list is permitted per successful preparation attempt.

### 4.3 Lock boundary

All of the following occur under one DP-WP1.3 durable-ledger exclusive lock
(and the same operator session for the host config write):

- ledger reload and identity comparison;
- before-state capture (checksum only in durable evidence; forensic payload
  retained outside Git if needed);
- single `config.tabList` write to the exact target;
- mandatory exact read-back;
- durable baseline step result;
- failure preservation if any check fails.

A lock failure or ledger corruption fails closed with zero navigation write.

### 4.4 Identity binding

Every request, evidence package, step event, and read-back assertion carries:

```text
installationId = installation-501688a00ef4b8e5ee083c1d
extensionName  = Chitu Prospecting Integration
extensionVersion = 1.9.13-alpha
manifestHash   = 9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649
sourceCommit   = 6ef712134f581a12a18da5c98691884e73388b78
navigationVersion = phase3c19-ia-v1
canonicalDefinitionSha256 = bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6
```

Any mismatch is fail closed before write.

## 5. Allowed Change

This amendment’s future implementation may change **only**:

- the host top-level navigation configuration surface (`config.tabList`) from an
  unrecognized default (or other unrecognized layout) to the exact approved
  `phase3c19-ia-v1` 19-item definition.

It may also record redacted durable ledger step/failure evidence for that
preparation action through existing DP-WP1.3 ledger APIs.

## 6. Forbidden Scope

This amendment does **not** authorize:

- ACL, roles, teams, user or field visibility, or any access-control change;
- dashboards, dashlets, branding, or user preferences;
- migrations, DDL, schema/bootstrap, database repair, or DP-WP4 work;
- Railway deployment, compose, restart, healthcheck, volume, or environment
  mutation;
- hooks, workflows, jobs, metadata rebuilds, extension upload/install,
  `BeforeInstall.php`, or `AfterInstall.php`;
- CRM business data mutation (Account, Contact, Lead, Opportunity, Quote,
  Email, provider, outreach, audit, or workflow records);
- the legacy C17 navigation materializer / snapshot / restore tooling;
- weakening the `navigation_provisioning` permutation gate;
- synthetic success markers for the navigation adapter step;
- direct ledger JSON edits, direct SQL against configuration tables, or
  `COMPLETED` record mutation.

## 7. Evidence Requirements

A future baseline-preparation evidence package must include all of the
following. Raw `tabList` payloads may be retained in a controlled temp/evidence
path for forensics but must **not** be committed into durable ledger events or
required audit prose beyond redacted checksums and a structured diff summary.

| Evidence | Requirement |
| --- | --- |
| Before checksum | SHA-256 of the canonical serialization of the pre-write top-level list |
| Target checksums | Source-byte, canonical-definition, and expected postcondition SHA-256 from this header |
| Exact `tabList` diff | Structured add/remove/reorder summary proving transition from unrecognized baseline to the exact 19-item target (module/divider identities and positions only; no secrets) |
| Postcondition verification | Fresh read-back equals exact target; evidence `sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Durable step evidence | `baseline:navigation_default_to_phase3c19_ia_v1` outcome recorded under lock before any claim of success |
| Identity binding | Exact `installationId` + release identity tuple |
| Negative proof | No ACL/dashboard/migration/Railway/hook/AfterInstall/business-data mutation |

Success claim format:

```text
name:     navigation_baseline_matches_definition
satisfied: true
evidence: sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0
```

This postcondition name is for baseline preparation evidence only. It does **not**
replace `navigation_state_matches_definition` for the later
`navigation_provisioning` adapter step.

## 8. Recovery

### 8.1 Failure handling during baseline preparation

| Condition | Required handling |
| --- | --- |
| Checksum / definition mismatch | No write; redacted failure; preserve current ledger disposition |
| Lock unavailable / ledger corrupt | Stage-1 `LEDGER_LOCK_UNAVAILABLE` / `LEDGER_CORRUPT`; no write |
| Identity mismatch | No write; fail closed |
| Module / registration evidence absent | No write; `NAVIGATION_DEPENDENCY_UNAVAILABLE` (or equivalent redacted code) |
| Read-back mismatch after write | Record failed baseline step; do not claim success; preserve failure; no automatic second write |
| Unexpected business/config mutation | Abort; fail closed; operator review |

### 8.2 `FAILED_PRESERVED`

The current navigation-runtime failure remains `FAILED_PRESERVED` until a
governed recovery is separately authorized. Baseline preparation does **not**
silently clear that disposition. Automatic retry of either baseline preparation
or `navigation_provisioning` is forbidden.

### 8.3 Retry rules

1. **No automatic retry** of baseline preparation or navigation admission.
2. After a failed baseline attempt: remain fail-closed; require operator review
   and a new explicit invocation under the same implementation authorization
   (or a superseding amendment if the target changed).
3. After a **successful** baseline preparation:
   - recover the durable record only via the existing governed edge
     `FAILED → READY`, then `READY → INSTALLING → REGISTERED` with
     revalidated registration/module evidence (no native reinstall unless a
     separate registration amendment says otherwise);
   - do **not** treat the prior failed
     `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition`
     step as success;
   - do **not** invent a synthetic navigation success step.
4. **Re-admission after prior failed navigation step** requires a separately
   reviewed recovery-admission rule (proposed name:
   `BASELINE_RECOVERY_ADMISSION`) because `FIRST_RUNTIME_ADMISSION` is defined
   only when no prior navigation durable step exists. That rule is **out of
   scope for execution here** and must appear in the implementation
   authorization before any re-invoke of `navigation_provisioning`.

## 9. Authorization Boundary

This document:

- **does** define the missing baseline-preparation governance gap;
- **does** pin identity, checksums, allowed host mutation, evidence, and recovery
  rules;
- **does not** authorize runtime execution;
- **does not** authorize code changes;
- **does not** authorize ledger recovery or navigation re-admission;
- **does not** authorize Railway, ACL, dashboard, migration, hooks, or
  AfterInstall work.

## 10. Next Action

1. Independent review of this amendment.
2. If accepted: issue a **separate DP-WP2 Navigation Baseline Preparation
   Implementation Authorization** with an exact allowlist (runner/surface files
   and tests), recovery-admission rule for post-failure re-entry, and operator
   procedure.
3. Only after that authorization: execute baseline preparation, retain evidence,
   recover to `REGISTERED`, then re-admit `navigation_provisioning` toward
   `HOOK_PENDING`.
4. Until then: leave host `tabList` and `FAILED_PRESERVED` unchanged; do not
   force success via synthetic ledger markers or the legacy materializer.
