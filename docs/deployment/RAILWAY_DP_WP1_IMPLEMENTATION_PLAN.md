# Railway DP-WP1 Deterministic Extension Installation Implementation Plan

| Field | Value |
| --- | --- |
| Status | IMPLEMENTATION PLAN COMPLETE — IMPLEMENTATION NOT AUTHORIZED |
| Work package | DP-WP1 — Deterministic Extension Installation |
| Authorized baseline reviewed | `77245d3ff9d54ca75219fc4a630e733f4db5ca52` |
| Governing charter | `docs/deployment/RAILWAY_DP_WP1_INSTALLATION_CHARTER.md` |
| Prerequisite | DP-WP0 RATIFIED AND COMMITTED |

## 1. Purpose and Governance Boundary

This plan translates the ratified DP-WP1 charter into a concrete future implementation design. It is a design record only. It does not create an installer, execute `AfterInstall.php`, run a migration, change a database, alter Railway or Docker configuration, or deploy a release.

DP-WP1 implementation is **NOT STARTED**. A separate implementation authorization must name the exact code, schema, and test files before work begins. This plan consumes, and does not redefine, the DP-WP0 manifest, its verification procedure, canonical roots, release identity, or source-of-truth exclusions.

The plan is limited to deterministic extension registration, the installation-runner contract, lock and ledger mechanics, controlled hook classification, metadata-refresh control, and restart/failure safety. Roles, ACL, navigation, provisioning, branding, full C16–C25 schema work, Railway release wiring, browser validation, provider activity, and deployment closure remain outside DP-WP1.

## 2. Architecture Overview

The future installation path is an explicit, operator-selected administrative command or one-shot release operation. It is never a web request, browser action, Apache startup action, or background job.

```text
explicit administrator invocation
          |
          v
Installation Runner -- acquires one DB-scoped installation lock
          |
          +-- Artifact Verification Layer -- DP-WP0 manifest/check procedure
          |
          +-- Installation Ledger -- durable attempts and step events
          |
          +-- Extension Registration Adapter -- discover/register/validate
          |
          +-- Controlled Hook Adapter -- named allowlisted actions only
          |
          +-- Migration Interface -- contract only; DP-WP4 owns schema set
          |
          +-- Metadata Adapter -- rebuild and metadata-load verification
          |
          v
redacted operator status: completed, failed, or blocked
```

### 2.1 Installation Runner

The runner accepts an explicit requested release identity, performs phases in the order in this plan, records every phase before and after it runs, and stops at the first unresolved result. It exposes only a redacted administrative status derived from the ledger; it creates no CRM entity, browser page, or user-facing history.

It must hold one installation lock from state discovery through terminal completion, failure, or block recording. A concurrent invocation either waits according to a bounded administrative policy or exits as blocked; it must never perform duplicate work.

### 2.2 Artifact Verification Layer

The verification layer consumes `deployment/railway/full-application-artifact-manifest.json` and the existing DP-WP0 check procedure without reimplementing or weakening either. Before any registration, hook, migration-interface call, or metadata action it must:

1. verify the exact manifest bytes and required-artifact hashes by the DP-WP0 procedure;
2. read the extension name and version from `crm-extension/manifest.json`;
3. compare those values with the manifest release identity and the explicitly selected source commit; and
4. verify all required canonical files are present.

The verification result is an immutable release identity: extension name, extension version, manifest SHA-256, and source Git commit. Any mismatch, absent required file, malformed manifest, or failed hash check blocks installation before a non-ledger installation mutation occurs.

### 2.3 Interfaces and Least Privilege

Future implementation must use narrow adapters rather than allow a general-purpose shell, arbitrary PHP include, or opaque hook execution. Database access is limited to installation ledger, registration state, and separately admitted installation steps. Filesystem access is limited to manifest/artifact reads and the specific cache paths required for metadata refresh. No adapter receives provider credentials, SMTP configuration, customer data, uploads, preferences, sessions, or external-network capability.

## 3. Installation State Model

The attempt-level state is distinct from the current phase. The ledger retains both so an operator can distinguish a terminal result from the last durable step.

| State | Meaning | Permitted next state |
| --- | --- | --- |
| `UNKNOWN` | No matching release attempt has been discovered. | `READY`, `PREFLIGHT_FAILED`, `BLOCKED` |
| `PREFLIGHT_FAILED` | Identity, manifest, lock, or minimal-permission preflight failed. | `READY` only after a new verified invocation; otherwise `BLOCKED` |
| `READY` | Lock held, prior state classified, and preflight complete. | `INSTALLING`, `COMPLETED`, `BLOCKED` |
| `INSTALLING` | Registration or a named controlled step is active. | `REGISTERED`, `HOOK_RUNNING`, `FAILED`, `BLOCKED` |
| `REGISTERED` | Matching extension registration has been proven or recorded. | `HOOK_RUNNING`, `METADATA_REFRESH`, `FAILED`, `BLOCKED` |
| `HOOK_RUNNING` | A named, allowlisted hook-adapter action is active. | `METADATA_REFRESH`, `FAILED`, `BLOCKED` |
| `METADATA_REFRESH` | Metadata rebuild/cache action is active. | `COMPLETED`, `FAILED`, `BLOCKED` |
| `COMPLETED` | Matching identity, all required recorded steps, and metadata-load validation succeeded. | no automatic transition |
| `FAILED` | A started phase failed and its redacted reason is durable. | `READY` only through controlled identity-matching recovery; otherwise `BLOCKED` |
| `BLOCKED` | Progress is unsafe or unapproved, such as a release mismatch or missing required DP-WP4 migration. | no automatic transition; operator review is required |

Valid transitions are monotonic in phase order, except controlled recovery from `PREFLIGHT_FAILED` or `FAILED` to a newly revalidated `READY` state under the same release identity. A matching `COMPLETED` attempt is a validation-only no-op. Forbidden transitions include `COMPLETED` back to an active state, skipping artifact verification, executing a later phase after failure, changing identity during an active attempt, and treating a table or cache file as proof of an unrecorded step.

On process restart, a durable active phase is classified as incomplete. The runner reacquires the lock, verifies the same identity, rechecks the last successful postcondition, and resumes only at the first uncompleted step. If either identity or postcondition cannot be proven, it records `BLOCKED` and requires operator review.

## 4. Durable Installation Ledger

The planned ledger is extension-owned storage in the target EspoCRM application's database, implemented as a dedicated installation-attempt record and append-only installation-step/event records. The names, migrations, and DDL are not created by this plan; they require separate DP-WP1 implementation authorization. The ledger is not a CRM entity, business audit trail, or user-facing history.

The attempt record must include at least:

| Field | Requirement |
| --- | --- |
| `installationId` | Immutable unique attempt identifier. |
| `extensionName` | Derived from the verified manifest. |
| `extensionVersion` | Derived from the verified manifest. |
| `manifestHash` | SHA-256 of the exact verified DP-WP0 manifest. |
| `sourceCommit` | Verified Git release identity. |
| `phase` | Last durable lifecycle phase/state. |
| `status` | `running`, `completed`, `failed`, or `blocked`, consistent with the state model. |
| `startedAt` | Controlled attempt start timestamp. |
| `completedAt` | Set only after completion validation succeeds. |
| `failureReason` | Redacted stable diagnostic code and concise cause; no secret or business payload. |

Each append-only step/event record must capture `installationId`, stable step identifier, declared sequence, step-definition checksum, release identity, start/end time, outcome, and the expected-postcondition result. Step checksums bind behavior to the reviewed step definition; a changed checksum, unknown prior step, duplicate completed step, or out-of-order sequence blocks the attempt.

Ledger writes occur durably before a mutable step starts and after it ends. A uniqueness rule permits at most one completed attempt per immutable release identity. Earlier failed and incomplete attempts remain preserved. The lock and ledger state must be transactionally coordinated where the storage engine supports it; otherwise the implementation must make the before/after write protocol restart-detectable and fail closed.

## 5. Runner Execution Phases

Every phase has a stable identifier, expected postcondition, durable start/result event, and a redacted failure code. No phase activates a later work package.

| Phase | Input and action | Success output | Failure and rollback boundary |
| --- | --- | --- | --- |
| 0 — Preflight | Explicit release identity; acquire installation lock; inspect ledger; verify minimal writable paths without broadening permissions. | A classified prior state and locked `READY` attempt. | Record `PREFLIGHT_FAILED` or `BLOCKED`; no registration, hook, migration, metadata, provisioning, or cache mutation. No rollback is needed beyond lock release. |
| 1 — Artifact verification | DP-WP0 manifest, manifest-check procedure, extension manifest, selected commit, canonical files. | Immutable verified release identity recorded in the ledger. | Block before installation mutation. Preserve a redacted failure event; never substitute local volumes, database state, ZIPs, or cache as release input. |
| 2 — Extension registration | Verified identity and discovered EspoCRM registration/version state. | Existing matching completed registration is validated as a no-op, or one matching registration record is durably recorded. | Stop and record failure/block. Do not auto-upgrade, downgrade, duplicate registration, or remove a prior release. Any compensation is limited to reviewed non-destructive registration state. |
| 3 — Controlled installation hook | Verified identity, registered state, and a named allowlisted hook-action specification. | Only an admitted, ledgered action with its postcondition may advance. | The current hook is never run as opaque code. An unknown, changed, or unapproved action blocks; do not retry automatically. |
| 4 — Migration framework invocation | Ordered DP-WP4-owned migration descriptors accepted through the runner contract. | Per-step checksum, result, and postcondition are recorded. | Stop at first failure, preserve state, and defer recovery/compensation to the reviewed migration owner. DP-WP1 supplies no C16–C25 migration body. |
| 5 — Metadata/cache refresh | Successful required registration and migration-interface postconditions. | A controlled rebuild/cache refresh event and successful metadata-load check. | Stop and record failure; never use cache deletion as a substitute for registration or migration success. No provider, business-data, or browser action may occur. |
| 6 — Validation | Verified identity, ledger completion, registration state, and metadata-load result. | `COMPLETED` only when all recorded postconditions match the same identity. | Mark failed/blocked on any mismatch. This phase is programmatic installation validation only, not DP-WP6 browser validation. |

The runner must refuse Phase 4 when a required schema action has not been separately supplied and authorized by DP-WP4. That is an intentional `BLOCKED` outcome, not permission to infer or create schema.

## 6. `AfterInstall.php` Boundary

The inspected `crm-extension/scripts/AfterInstall.php` currently performs two observable operations: `CREATE TABLE IF NOT EXISTS numbering_sequence` and `DataManager::rebuild()`.

The planned implementation does **not** execute `AfterInstall.php` directly. It replaces opaque direct execution with a controlled hook adapter that admits only named, reviewed, versioned, checksummed, locked, ledgered actions. The rationale is that direct hook execution cannot independently prove ordering, exact behavior, or restart-safe postconditions.

| Observed action | Classification | Planned treatment |
| --- | --- | --- |
| `numbering_sequence` table initialization | Conditionally allowed deterministic extension-owned schema preparation | Model it as a named migration-interface step. The runner enforces lock, checksum, ledger, and postcondition, but the actual C16–C25 schema/migration content and its authorization remain DP-WP4-owned. |
| `DataManager::rebuild()` | Conditionally allowed metadata operation | Move it to Phase 5 as an explicit metadata-adapter step after all required database postconditions succeed. |

Allowed hook-adapter categories are extension registration, safe deterministic initialization admitted through the migration contract, and metadata operations. Forbidden categories are provider calls, external APIs or network access, email/SMTP, credentials, business data, automatic Lead or Opportunity creation, AI execution, outreach, autonomous jobs, ACL/navigation/provisioning, and any unreviewed destructive operation. The adapter must reject an action outside its allowlist before execution.

## 7. Migration Framework Boundary

DP-WP1 plans the migration framework contract: installation lock, stable step identifier, declared ordering, content checksum, runner interface, durable ledger integration, explicit precondition/postcondition, and fail-closed recovery. It does not plan or implement all C16–C25 migrations, fresh-schema bootstrap, business-data movement, customer data import, or a general-purpose migration executor.

DP-WP4 owns the reviewed C16–C25 schema set, schema bootstrap, migration bodies, their database compatibility review, and any recovery/compensation defined for those bodies. A future DP-WP1 runner may invoke only DP-WP4-approved descriptors through the narrow contract. It must not manufacture missing descriptors, silently skip a required one, or consider schema presence alone to be success.

## 8. Railway and Startup Boundary

No change to `deployment/railway/docker-entrypoint-railway.sh` is required or proposed by this implementation plan. The future runner is triggered by an explicit administrative CLI command or a separately authorized one-shot release operation. Choosing, wiring, scheduling, and operating that release operation on Railway belongs to DP-WP5.

The existing Apache entrypoint must continue to start the application without invoking the runner. It must not perform registration, hook execution, migration-interface calls, ledger transitions, or metadata rebuilds on every restart. This boundary prevents restart-driven duplicate installation and startup loops. A failed explicit runner exits with its durable failed/blocked ledger state while Apache startup behavior remains independent; no container restart may be used as a retry mechanism.

## 9. Testing Strategy and Exit Evidence

Future implementation authorization must include automated tests with synthetic, non-secret fixtures and no live provider configuration. Required evidence is:

| Test layer | Required cases |
| --- | --- |
| Unit | DP-WP0 manifest and identity validation; missing/changed required-file rejection; state-transition table; ledger append/history and uniqueness rules; step checksum/order validation; lock contention behavior; redaction of failure reasons. |
| Integration | Fresh installation through admitted synthetic steps; second-run matching no-op; interrupted active step and identity-matching restart recovery; version/manifest/source mismatch; failed hook-adapter action; required DP-WP4 migration descriptor missing; metadata rebuild failure. |
| Negative | No provider call, external-network request, email/SMTP attempt, credential read/log, business-data write, automatic Lead/Opportunity creation, AI execution, outreach, duplicate execution, or startup-triggered installation. |
| Validation boundary | Programmatically verify registration, matching completed ledger identity, and metadata-load postcondition. Browser, Railway, full database-bootstrap, and deployment validation remain DP-WP6/DP-WP5/DP-WP4 work. |

The test suite must assert that a complete matching identity does not rerun steps, while a mismatched identity does not advance. It must simulate process interruption between durable before/after ledger events and prove that unsafe recovery becomes `BLOCKED` rather than guessed.

## 10. Rollback and Recovery

| Failure case | Classification | Required response |
| --- | --- | --- |
| Manifest, extension version, source-commit, or required-file mismatch | Non-recoverable for that invocation | Record a redacted preflight failure/block; do not mutate registration, schema, or metadata. Operator supplies a verified identity. |
| Controlled hook-adapter failure | Potentially recoverable only after postcondition review | Record the failed step, stop, retain lock/ledger audit state, and require controlled same-identity resume. Never rerun completed steps automatically. |
| DP-WP4 migration failure | DP-WP4-owned recovery | Preserve the failure state and stop. An operator follows the reviewed DP-WP4 compensation or restore procedure; DP-WP1 does not restore databases. |
| Container/process restart | Recoverable only if identity and postcondition revalidate | Detect incomplete running state, reacquire the lock, and resume at the first uncompleted step. Otherwise mark `BLOCKED`. |
| Concurrent invocation or changed checksum | Non-recoverable automatically | Refuse/serialize, preserve evidence, and require operator review plus a newly authorized definition if applicable. |

There is no automatic database restore, production rollback, data import, force-unlock, version downgrade, or destructive compensation in DP-WP1. Every uncertain state is blocked for operator review.

## 11. Security and Data Review

The design forbids secrets, provider credentials, SMTP configuration, API tokens, customer/business data, user preferences, uploads, sessions, outreach activation, external calls, email delivery, and AI execution in the runner and its tests. Logs and ledger reasons use stable redacted codes rather than payloads or environment values.

Access is least-privilege and limited to the verified artifact read set, the installation ledger, controlled registration state, approved migration interface, and metadata/cache paths. Any new secret, environment setting, provider capability, or broader database privilege needs separate authorization and a separate owner.

## 12. Future Implementation Exit Criteria

A separately authorized implementation may be considered for review only when it evidences manifest-first verification, release-identity binding, one held lock, durable ledger history, checksummed ordered steps, explicit hook adapter behavior, no-op/recovery safety, metadata-load validation, automated negative tests, and no downstream scope expansion. This plan itself grants none of those changes or executions.
