# Railway DP-WP2 Runtime Navigation Admission Authorization

| Field | Value |
| --- | --- |
| Decision | **AUTHORIZED WITH FIRST-RUNTIME ADMISSION CONDITIONS** |
| Work package | DP-WP2 navigation provisioning runtime admission |
| Adapter baseline | `phase3c25-dp-wp2-navigation-adapter-complete` (`590a25e4347c24743752939f739cad9eea58d6e1`) |
| Phase | `navigation_provisioning` |
| Governing target | `deployment/navigation/phase3c17_navigation.json` / `phase3c19-ia-v1` |
| Target source SHA-256 | `ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e` |
| Target canonical SHA-256 | `bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6` |
| Expected postcondition SHA-256 | `fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0` |
| Release identity | `Chitu Prospecting Integration` `1.9.13-alpha` / manifest `9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649` / commit `6ef712134f581a12a18da5c98691884e73388b78` |

## 1. Executive Verdict

DP-WP2 navigation provisioning is authorized for a single, explicit first
runtime admission from a valid `REGISTERED` installation record, subject to
the gates in this amendment. The admission is not a resume and must not be
simulated by adding a successful adapter event or postcondition marker before
the adapter has performed its real read-back verification.

This authorization admits only the named, tagged report-only adapter and the
ratified navigation target. It does not grant general DP-WP2 lifecycle,
provisioning, or CRM authority.

## 2. Amendment Scope

### 2.1 First-runtime admission model

`FIRST_RUNTIME_ADMISSION` is an administrative admission classification, not a
new durable lifecycle state. It is available only when all conditions below are
true under one durable-ledger lock:

1. A named operator explicitly invokes the navigation action; no startup,
   scheduler, healthcheck, release command, browser action, or runtime observer
   may invoke it.
2. The DP-WP1.3 ledger is acquired and reloaded under its existing exclusive
   lock. Its record exists, is non-corrupt, has exactly the release identity in
   the header, and is in `REGISTERED`.
3. No prior successful or failed durable step exists for
   `adapter:navigation_provisioning:postcondition:navigation_state_matches_definition`.
   A prior failed record is `FAILED_PRESERVED`; a prior successful record is a
   revalidation case under §3.3, not first admission.
4. The operator supplies an independently reviewed, immutable evidence package
   bound to the same `installationId`, extension name/version, manifest hash,
   and source commit. It must prove native extension registration and
   authoritative availability of `ProspectingDashboard`, `ProspectingSearch`,
   and `DraftApproval`.
5. The adapter binary/source and target definition match the exact baseline and
   checksums in this document. Any mismatch is
   `NAVIGATION_DEFINITION_MISMATCH` before a navigation write.

The current generic `RESUME` branch must not be used to bypass these
conditions. In particular, an operator must not write a synthetic success step,
manufacture a `resume_postcondition`, alter a ledger JSON file, or move the
record to another state merely to make a generic resume path admit the action.
A runtime path that cannot distinguish first admission from resume remains
blocked before adapter invocation until separately reviewed implementation
provides that distinction.

### 2.2 Identity and lock boundary

The operator request, dependency evidence, adapter input, durable record, step
event, and postcondition evidence all carry the identical immutable tuple:

```text
installationId
extensionName = Chitu Prospecting Integration
extensionVersion = 1.9.13-alpha
manifestHash = 9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649
sourceCommit = 6ef712134f581a12a18da5c98691884e73388b78
```

The lock covers recovery, identity comparison, definition validation, baseline
read, the one bounded navigation write when needed, read-back, step-result
recording, and the resulting lifecycle transition or failure preservation. A
lock failure, corrupt ledger, identity mismatch, absent evidence, or stale
target check fails closed without a navigation write.

## 3. Authorization Decision and Lifecycle Boundary

### 3.1 Authorized path

Only the following path is authorized:

```text
REGISTERED
  -> explicit FIRST_RUNTIME_ADMISSION for navigation_provisioning
  -> exact navigation target read / bounded write if required / exact read-back
  -> durable successful step evidence
  -> HOOK_PENDING
```

`HOOK_PENDING` is the only lifecycle continuation permitted by this amendment.
It is requested by the orchestrator only after the adapter returns a valid
successful report and the durable success step is recorded. This document does
not authorize a hook, a later phase, `MIGRATION_PENDING`, `METADATA_REFRESH`,
or `COMPLETED`.

### 3.2 First invocation controls

The first invocation may use the exact idempotency contract only:

```text
phase: navigation_provisioning
mode: REVALIDATE_AND_NOOP
key: navigation:phase3c19-ia-v1:bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6
step: adapter:navigation_provisioning:postcondition:navigation_state_matches_definition
```

The adapter may read only the bounded top-level navigation surface. It may
write that surface once only when the current list is a recognized permutation
of the ratified 19-item target and differs from it. An exact target at first
read is a successful no-write result. An unrecognized baseline, unavailable
module, contract mismatch, or read-back mismatch is a failure; it must not be
merged, repaired, expanded, or retried automatically.

### 3.3 Evidence and idempotent rerun

Success requires a fresh read-back equal value-for-value and
position-for-position to the ratified target. The successful postcondition is:

```text
name: navigation_state_matches_definition
evidence: sha256:fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0
```

The raw target source checksum and canonical-definition checksum in the header
must be retained with this postcondition checksum in the runtime evidence.
Raw navigation payloads, configuration paths, credentials, user preferences,
and business data must not enter the evidence or ledger.

An idempotent rerun is permitted only after a recorded successful step for the
same identity, key, and checksums. It is read-back revalidation only: it must
not write navigation, append a duplicate success event, or request another
lifecycle transition. A changed checksum or a failed/precheck-failed prior
attempt is not an idempotent rerun and remains `FAILED_PRESERVED` pending a
separate recovery decision.

## 4. Allowed Scope

This amendment permits only:

- an explicit operator invocation through the reviewed DP-WP2
  `navigation_provisioning` adapter;
- consumption of the exact ratified navigation target contract and checksum
  tuple in this record;
- lock-scoped, identity-bound read of the configured top-level navigation
  surface, with at most one exact target write under §3.2;
- mandatory exact read-back verification, durable redacted step evidence, and
  the governed `REGISTERED -> HOOK_PENDING` continuation after success; and
- no-write, exact-read-back idempotent revalidation after a prior successful
  invocation.

## 5. Forbidden Scope

This amendment does **not** authorize:

- ACL, roles, teams, user or field visibility, or access-control changes;
- dashboards, dashlets, branding, preferences, or any other navigation target;
- migrations, DDL, schema/bootstrap work, database repair, or DP-WP4 work;
- Railway deployment, startup/restart/release/healthcheck triggers, Docker,
  environment, volume, or runtime-configuration changes;
- `BeforeInstall.php`, `AfterInstall.php`, hooks, workflows, jobs, metadata
  rebuilds, extension registration, or package actions;
- CRM business data, including customer, account, contact, lead, opportunity,
  quote, email, provider, outreach, audit, or workflow records; or
- a synthetic resume marker, direct ledger edit, direct SQL, a legacy
  materializer, an unreviewed adapter, or an unverified target addition.

## 6. Exit Criteria and Failure Preservation

The runtime admission is complete only when the retained evidence shows:

1. exact release and `installationId` binding under the durable lock;
2. reviewed DP-WP1 registration and module-availability evidence;
3. the target source checksum, canonical-definition checksum, and expected
   postcondition checksum from this record;
4. a fresh exact read-back and the durable successful adapter step event before
   the single `REGISTERED -> HOOK_PENDING` transition; and
5. a no-write idempotent rerun that revalidates the same postcondition and
   leaves the durable event count and lifecycle state unchanged.

On every failure, the adapter step outcome and a redacted stable failure code
must be recorded under the lock, then the record must be preserved as
`FAILED_PRESERVED`. No automatic retry, synthesized evidence, lifecycle skip,
or mutation beyond the approved navigation surface is permitted.

## 7. Next Action

Before the first runtime invocation, independently verify that the runtime
orchestrator has a reviewed first-admission path satisfying §2.1 rather than
its generic resume branch. Then an authorized operator may invoke only the
bounded action above and retain the required runtime evidence. If that path is
absent, stop before invocation; a separate narrowly scoped implementation
authorization is required, not a synthetic ledger workaround.
