# Railway DP-WP2 Provisioning Lifecycle Charter

| Field | Value |
| --- | --- |
| Status | **PROPOSED — NOT RATIFIED — IMPLEMENTATION NOT AUTHORIZED** |
| Work package | DP-WP2 — Provisioning Lifecycle |
| Governing installation charter | `docs/deployment/RAILWAY_DP_WP1_INSTALLATION_CHARTER.md` |
| Durable-state prerequisite | DP-WP1.3 Durable Ledger |
| Transition-governance prerequisite | `docs/deployment/RAILWAY_DP_WP1_4_STATE_TRANSITION_GOVERNANCE_CHARTER.md` — ratified at tag `phase3c25-dp-wp1.4-ratified` (commit `2a3f20b`) |
| Migration owner | DP-WP4 |
| Railway integration owner | DP-WP5 |

## 1. Purpose

DP-WP2 defines the proposed governance boundary for **provisioning** after a release has passed the DP-WP1 artifact, ledger, and state-transition gates. It describes how a future explicit provisioning orchestrator may coordinate reviewed provisioning phase adapters without taking ownership of installation state persistence, state-transition policy, database bootstrap, Railway lifecycle control, or CRM business data.

The intended outcome is a bounded, replay-safe administrative provisioning lifecycle. It must be explicit, identity-bound, lock-held, ledgered, fail-closed, and independently reviewable. This charter defines that contract only; it creates no executable lifecycle.

### 1.1 Non-goals

DP-WP2 does not:

- implement or activate an installation or provisioning runner;
- register an extension, execute `AfterInstall.php`, or rebuild metadata;
- define, invoke, or own migrations, schema bootstrap, DDL, or database changes;
- create or alter CRM entities, business data, users, teams, roles, ACLs, navigation, dashboards, or branding;
- make Railway a lifecycle controller, alter a release command, or change Docker, Railway, runtime, or environment configuration;
- perform browser validation, provider integration, network activity, email delivery, or autonomous background work; or
- alter the DP-WP0 artifact manifest, release identity, canonical file definition, or verification procedure.

## 2. Relationship to Existing DP-WP1 Governance

### 2.1 DP-WP1.3 Durable Ledger

DP-WP1.3 remains the durable record, lock, reload/recovery, corruption-validation, and restart-safety boundary for an installation attempt. A future DP-WP2 orchestrator may use the ledger only through its approved protocol. It may not write ledger files directly, bypass the lock, create its own competing durable state store, reinterpret a corrupt record, or treat an in-memory/reference adapter as durable mutation authority.

The ledger records identity, phase, step outcome, failure, and completion. It does not decide which provisioning phase is permitted, invent provisioning work, or grant authority to execute it.

### 2.2 DP-WP1.4 State Transition Governance

DP-WP1.4, as ratified at tag `phase3c25-dp-wp1.4-ratified` (commit `2a3f20b`), remains the normative authority for the governed state vocabulary, allowed transition matrix, orchestrator-only phase advancement, event semantics, identity binding, and recovery dispositions. DP-WP2 introduces no state and changes no transition.

A future DP-WP2 implementation may proceed only by requesting transitions already allowed by DP-WP1.4. Phase adapters may report named, redacted step outcomes; they may not advance, skip, retry, complete, or fail an installation independently. Governance-deferred controls identified in DP-WP1.4, including record immutability and per-call identity binding, remain deferred and cannot be represented as structurally enforced merely by this charter.

### 2.3 DP-WP0 Release Identity

DP-WP0 remains the sole source of truth for canonical artifacts, manifest bytes and hashes, extension identity, source commit, and release verification. DP-WP2 consumes a release identity that has already passed DP-WP0 verification. It may not repair, download, rewrite, substitute, or otherwise mutate the manifest or artifacts.

## 3. Proposed Provisioning Lifecycle Model

The lifecycle is a sequence of administrative coordination stages, not a new installation state machine:

```text
explicit operator request
  → release-identity and precondition verification
  → acquire DP-WP1.3 lock and reload durable ledger
  → obtain DP-WP1.4-permitted orchestrator disposition
  → invoke one reviewed phase adapter at a time
  → record outcome and validate the phase postcondition
  → advance only through a DP-WP1.4-permitted transition
  → terminal completion, or governed failure preservation
```

Each stage is conditional on the prior stage's recorded success. Failure, lock contention, identity mismatch, ledger corruption, missing adapter contract, unproven postcondition, or an unapproved dependency must stop the lifecycle without silent continuation.

| Lifecycle stage | Required boundary | Result on failure or uncertainty |
| --- | --- | --- |
| Admission | DP-WP0 verifies the exact release identity; DP-WP1.4 permits entry only through its preflight transition | Record/redact precheck failure where authorized; perform no provisioning action. |
| Durable coordination | DP-WP1.3 lock is acquired and the latest durable snapshot is reloaded and validated | Fail closed; do not mutate a stale in-memory snapshot. |
| Disposition | DP-WP1.4 recovery rules identify new, resumable, completed-no-op, or preserved-failure disposition | Completed is a validation-only no-op; failed records remain preserved; ambiguity resolves through a governed failure disposition, never a distinct block state. |
| Phase execution | The orchestrator invokes exactly one reviewed, identity-bound phase adapter | Stop at first non-success; adapter reports an outcome but cannot change lifecycle state. |
| Postcondition | The orchestrator verifies the declared, non-business postcondition for the named phase | Do not advance; record a redacted failure through the governed path; an operator block resolves as `PRECHECK_FAILED` or `FAILED`, never as a distinct state. |
| Terminal handling | DP-WP1.4 governs completion and failure transition semantics | No duplicate completion, hidden retry, rollback inference, or continuation after failure. |

This model does not authorize any stage to execute now. In particular, the use of the terms “invoke,” “record,” and “advance” states requirements for a future separately authorized implementation; it is not execution authority.

### 3.1 Operator Block Is Not a Lifecycle State

An operator block is an intervention condition, not a governed lifecycle state. “BLOCKED” is not introduced as a new DP-WP1.4 state, and DP-WP2 adds no state vocabulary of its own. Operator intervention conditions resolve exclusively through the existing governed failure dispositions already permitted by DP-WP1.4:

```text
Operator block condition
        ↓
PRECHECK_FAILED or FAILED
        ↓
redacted failure reason recorded
        ↓
Recovery returns FAILED_PRESERVED behavior where applicable.
```

An operator block arising during preflight resolves to `PRECHECK_FAILED`; an operator block arising during a later phase resolves to `FAILED`. In either case the orchestrator records a redacted failure reason through the DP-WP1.3 ledger protocol, and subsequent recovery treats the record under the DP-WP1.4 `FAILED_PRESERVED` disposition — preserved for audit, with only the governed retry edge able to re-admit the same identity (ratified DP-WP1.4 charter §5.1 recovery/disposition semantics; §5.3 transition authority). DP-WP1.4 remains the sole state transition authority: an operator block never transitions a record directly and never requires a state that DP-WP1.4 does not already govern.

## 4. Orchestrator Authority Boundary

The future provisioning orchestrator is the only component permitted to coordinate the lifecycle. Its authority is deliberately narrow:

- accept an explicit human administrative request for one verified release identity;
- acquire the existing durable lock, reload the current durable ledger, and obtain a governed recovery disposition;
- select a reviewed phase adapter only when its dependency, input contract, and postcondition are explicitly authorized;
- request DP-WP1.4-permitted phase transitions and record redacted step outcomes through the ledger protocol;
- stop, preserve evidence, and return a redacted administrative result on any unresolved condition.

The orchestrator may not directly edit ledger records, gain authority from the runtime environment, infer phase success from CRM/database/cache state, create business data, or invoke a phase outside its approved work-package owner. It must not execute a new lifecycle on container start, HTTP request, scheduled task, healthcheck, or browser action.

Lock possession permits only the ledger mutation protocol; it is not blanket authority to provision, change CRM state, run migrations, or execute hooks. A lock-holding orchestrator remains bound by DP-WP0 identity verification, DP-WP1.4 transitions, the declared phase-adapter contract, and this charter's exclusions.

## 5. Component Authority Matrix

| Component | Authority | Explicitly not authorized to do |
| --- | --- | --- |
| Orchestrator | Coordinate an explicit approved lifecycle; acquire the ledger lock; request allowed DP-WP1.4 transitions; invoke one reviewed adapter; validate and record outcomes | Edit ledger storage directly; create CRM/business data; define schema; execute uncontrolled hooks; derive authority from Railway/startup; bypass a failed state or a governed failure disposition; represent an operator block as a lifecycle state |
| Ledger adapter | Persist and reload installation identity, phases, step events, failures, and completion under its lock and validation rules | Choose phases; execute provisioning; decide policy; write CRM records; act as a phase adapter; grant authority to an in-memory/reference adapter |
| Phase adapters | Perform only their individually approved, named provisioning action and report a redacted outcome/postcondition to the orchestrator | Acquire independent lifecycle authority; transition state; change another phase's record; execute unrelated work; invoke migrations, AfterInstall, or Railway actions unless separately approved and owned |
| `AfterInstall.php` | None under DP-WP2. Its DP-WP1 classification remains a future controlled-hook boundary | Run as opaque provisioning code; alter lifecycle state; create an implicit startup action; replace named ledgered steps |
| Migration runner | None under DP-WP2. It may later supply DP-WP4-owned, reviewed migration contract results | Own provisioning orchestration; run migrations from this charter; change schema under DP-WP2 authority; advance lifecycle state directly |
| Railway runtime | Provide environment/process hosting only, subject to DP-WP5 governance | Trigger, schedule, infer, resume, or authorize provisioning; hold a lifecycle lock; convert health/startup into installation success |
| CRM layer | Be a bounded target for separately approved provisioning adapters and postcondition checks | Become the lifecycle ledger, orchestrator, source of release identity, or implicit authority for provisioning; create business data outside a separately authorized scope |

## 6. Railway Boundary

Railway is an **environment provider only** for DP-WP2. It may supply the process environment that a separately authorized, explicitly invoked administrative operation runs within. It has no provisioning lifecycle authority.

Accordingly, DP-WP2 prohibits using a Railway deploy, container start, restart, healthcheck, release command, environment variable, mounted volume, scheduler, or runtime observation as a trigger or proof of a lifecycle transition. Railway release wiring, persistent-volume behavior, health, backup, and production operations remain reserved to DP-WP5. No Railway file, configuration, service, or runtime behavior is changed by this charter.

## 7. Migration Boundary

All fresh database bootstrap, schema design, DDL, migration descriptors, C16–C25 migration bodies, migration execution, post-migration validation, and compensation are reserved for DP-WP4.

DP-WP2 may describe a future orchestration boundary at which a DP-WP4-approved migration adapter reports a result. It may not define the migration contents, execute the adapter, assume that a table's presence proves success, or use migration work as a substitute for ledgered lifecycle evidence. Until DP-WP4 is separately authorized and reviewed, the migration boundary remains unavailable and must cause a lifecycle stop rather than a workaround.

## 8. CRM and Provisioning Separation

Provisioning is operational coordination, not CRM-domain ownership. The lifecycle record remains extension-owned installation evidence and must not become a CRM entity, UI history, user-facing audit feed, or source of business decisions.

Any future DP-WP2 phase that might configure roles, teams, ACLs, navigation, dashboards, or other CRM administration must have a separately approved target contract, least-privilege access, idempotent postconditions, and synthetic/non-secret test evidence. This charter creates none of those adapters, records, settings, or mutations. It does not permit provisioning to access customer data, provider credentials, uploads, sessions, preferences, email, or autonomous workflows.

## 9. Risks and Required Controls

| Risk | Consequence | Required control |
| --- | --- | --- |
| Lifecycle authority leaks into adapters or Railway | Hidden, duplicate, or out-of-order provisioning | Orchestrator-only coordination; Railway has zero lifecycle authority; adapter outcome-only reporting |
| Stale or corrupt durable state | Record loss or unsafe resumption | DP-WP1.3 lock-scoped reload and fail-closed validation before mutation |
| State-machine drift | Phase skips or fabricated completion | DP-WP1.4 allowed-transition matrix is normative; no new DP-WP2 states; operator-block conditions resolve as `PRECHECK_FAILED` or `FAILED`, with no `BLOCKED` state introduced |
| Migration work enters provisioning scope | Unreviewed schema/database change | DP-WP4 reservation and a hard stop when unavailable |
| CRM actions become business-data actions | Unauthorized data mutation or disclosure | CRM/provisioning separation, least privilege, redaction, and explicit future adapter authorization |
| Runtime startup becomes an installer | Non-deterministic deployment behavior | Explicit human invocation only; no startup, healthcheck, scheduler, or browser trigger |
| Incorrect retry/recovery | Repeated work or failure laundering | DP-WP1.4 recovery dispositions, preserved failures, verified identity, and postcondition revalidation |

## 10. Implementation Exit Criteria

No DP-WP2 implementation may be considered for authorization until a separate implementation plan identifies exact files, tests, adapter contracts, and dependencies. If authorized in the future, implementation exit evidence must show all of the following:

1. DP-WP0 manifest and release identity verification occur before every lifecycle mutation.
2. The orchestrator uses DP-WP1.3's lock-scoped durable reload and validated ledger protocol; no in-memory/reference adapter is used as durable mutation authority.
3. Every lifecycle movement matches DP-WP1.4's transition matrix, is identity-bound, and has a recorded, redacted outcome.
4. Each phase adapter has one named owner, defined input/output/postcondition, idempotency behavior, and failure contract; adapters cannot advance state directly.
5. Completed records are validation-only no-ops; interrupted records resume only after governed revalidation; failed and precheck-failed records remain preserved; operator-block conditions resolve to `PRECHECK_FAILED` or `FAILED` with a redacted reason and never introduce a `BLOCKED` state.
6. Railway has no lifecycle trigger or authority, and no deployment/runtime configuration is introduced without separately authorized DP-WP5 work.
7. Migration integration is absent unless DP-WP4 has separately authorized, reviewed, and supplied the required migration contract.
8. No CRM entity, business data, customer data, provider integration, email, browser flow, `AfterInstall.php` execution, database change, or autonomous workflow is introduced unless separately owned and authorized.
9. Focused automated tests, security review, independent review, and governance ratification pass before any production or Railway use is considered.

## 11. Review Checklist

Reviewers must confirm each item before recommending ratification:

- C1. The document status remains **PROPOSED — NOT RATIFIED — IMPLEMENTATION NOT AUTHORIZED** and no section grants execution authority.
- C2. DP-WP1.3 retains durable persistence, locking, reload/recovery, corruption handling, and restart-safety ownership.
- C3. DP-WP1.4 retains the state vocabulary, transition matrix, orchestrator-only phase advancement, and recovery semantics.
- C4. DP-WP0 remains the canonical artifact and release-identity authority.
- C5. The lifecycle model adds no states, no implicit trigger, and no phase-skip path; operator-block conditions resolve through DP-WP1.4 governed failure dispositions and introduce no `BLOCKED` state.
- C6. The authority matrix gives Railway only environment-provider status and no lifecycle authority.
- C7. The migration boundary is exclusively reserved to DP-WP4.
- C8. CRM/provisioning separation prohibits CRM entities, business data, user-facing history, and unapproved administrative mutation.
- C9. `AfterInstall.php` remains unexecuted and cannot act as opaque provisioning code.
- C10. The exit criteria require separate authorization, tests, review, and ratification before implementation.

## 12. Authorization Boundary

This charter is documentation and governance only. It authorizes no implementation, code change, test change, hook, migration, Railway deployment/integration, CRM entity change, installation action, provisioning action, or workflow activation.

**DP-WP2 status: PROPOSED — NOT RATIFIED — IMPLEMENTATION NOT AUTHORIZED.**
