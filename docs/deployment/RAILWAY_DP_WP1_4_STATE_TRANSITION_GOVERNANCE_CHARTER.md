# Railway DP-WP1.4 State Transition Governance Charter (Review Preparation)

| Field | Value |
| --- | --- |
| Status | CHARTER PROPOSED — NOT RATIFIED — IMPLEMENTATION NOT AUTHORIZED |
| Work package | DP-WP1.4 — State Transition and Mutation Authority Governance (sub-package of DP-WP1 — Deterministic Extension Installation) |
| Prepared for | Independent charter review |
| Governing documents | `docs/deployment/RAILWAY_DP_WP1_INSTALLATION_CHARTER.md`, `docs/deployment/RAILWAY_DP_WP1_IMPLEMENTATION_PLAN.md` |
| Foundation baseline | `197e91aa953d14ef4f9f20467fdef7daea14ea82` plus the preserved uncommitted DP-WP1.3 durable-ledger change set |
| Foundation artifacts governed | `scripts/dp_wp1_installation_foundation.py` (state machine, ledger protocol, durable adapter, foundation runner) |
| Implementation authority | Not granted by this charter |

## 1. Executive Summary

DP-WP1.1–DP-WP1.3 delivered an offline installation foundation: a ten-state machine, an in-memory ledger, a durable JSON ledger with an exclusive lock and fail-closed recovery, manifest validation/verification, and a foundation runner that deliberately stops before any mutation. What does not yet exist is a governance definition of **who may drive state transitions and under what authority** once real mutation-capable phases (registration, hook, migration, metadata) are connected.

DP-WP1.4 is proposed as a **documentation-and-contract work package**: it defines the state transition model, the allowed/forbidden transition matrix, the mutation authority model, ledger event semantics, and the recovery interaction boundary, all layered above the DP-WP1.3 durable ledger. It changes no code, adds no hooks, adds no migrations, integrates no Railway surface, and touches no CRM entities. Its output is a ratifiable contract that a future, separately authorized implementation phase must satisfy.

## 2. Proposed DP-WP1.4 Scope

### 2.1 In scope (definition and governance only)

- Ratify the existing ten-state vocabulary (`UNKNOWN`, `PRECHECK_FAILED`, `READY`, `INSTALLING`, `REGISTERED`, `HOOK_PENDING`, `MIGRATION_PENDING`, `METADATA_REFRESH`, `COMPLETED`, `FAILED`) as the governed state model; no new states are introduced by this charter.
- Define the allowed/forbidden transition matrix and its enforcement rules (§3).
- Define the mutation authority model: lock ownership, orchestrator-only phase advancement, adapter reporting limits, identity binding (§4).
- Define ledger event semantics: event kinds, append-only rules, deduplication, redaction, and the audit-only role of timestamps (§4.3).
- Define the recovery interaction boundary: disposition handling, resume preconditions, and prohibited recovery behaviors (§5).
- Define the relationship contracts with the installation workflow, `AfterInstall.php`, migrations, and Railway provisioning (§6).
- Define exit criteria that a future DP-WP1.4 implementation authorization must evidence.

### 2.2 Explicit non-scope

- No implementation, modification, or refactoring of `scripts/dp_wp1_installation_foundation.py` or any other code.
- No installation-workflow execution; the runner continues to stop before extension registration.
- No `AfterInstall.php` execution, hook adapter, or hook-content change.
- No migration bodies, descriptors, DDL, or migration-runner invocation (DP-WP4-owned).
- No Railway integration, entrypoint/release wiring, or provisioning of any kind (DP-WP5 / DP-WP2-owned).
- No CRM entity, entityDefs, ACL, navigation, metadata, or database change.
- No database-backed ledger; the plan's database ledger remains separately authorized future work.
- No retry counters, `BLOCKED` state, or new ledger fields — open questions are recorded in §5 and require separate authorization to resolve in code.

## 3. State Machine Proposal

### 3.1 Governed transition matrix

The matrix below ratifies the behavior already enforced by `_ALLOWED_TRANSITIONS` and `transition()` in the foundation. DP-WP1.4 proposes no change to it; it assigns governance meaning to each edge.

| From | Allowed targets | Governance meaning |
| --- | --- | --- |
| `UNKNOWN` | `READY`, `PRECHECK_FAILED` | Attempt entry: preflight passes or fails before any mutation. |
| `PRECHECK_FAILED` | `READY`, `FAILED` | Operator-supplied corrected identity may re-enter preflight; otherwise terminal failure record. |
| `READY` | `INSTALLING`, `FAILED` | Verified identity admitted to the mutation pipeline, or failed before mutation. |
| `INSTALLING` | `REGISTERED`, `FAILED` | Extension registration step boundary. |
| `REGISTERED` | `HOOK_PENDING`, `FAILED` | Controlled-hook phase boundary (classification per DP-WP1 charter §4.C). |
| `HOOK_PENDING` | `MIGRATION_PENDING`, `FAILED` | Migration-framework invocation boundary (DP-WP4 descriptors only). |
| `MIGRATION_PENDING` | `METADATA_REFRESH`, `FAILED` | Metadata/cache refresh boundary. |
| `METADATA_REFRESH` | `COMPLETED`, `FAILED` | Validation and completion boundary. |
| `COMPLETED` | *(none — terminal)* | No outbound transition under any authority. |
| `FAILED` | `READY` | Controlled retry edge only; see §5.3. |

### 3.2 Forbidden transitions (normative)

A future implementation must reject, and reviewers must verify rejection of:

- **Phase skips** — any edge not in §3.1 (e.g., `READY → REGISTERED`, `INSTALLING → MIGRATION_PENDING`).
- **Completion escape** — any transition out of `COMPLETED`; re-installation of the same identity is a validation-only no-op, not a transition.
- **Failure laundering** — `FAILED →` anything except `READY`; in particular no direct `FAILED → COMPLETED` or failure-record overwriting.
- **Out-of-band writes** — any state change not performed through the ledger protocol's mutation methods; direct record-field edits, manual ledger-file edits, and inference from table/cache presence are not transitions.
- **Anonymous transitions** — any transition without the durable lock held (enforced by `JsonFileInstallationLedger._require_lock`) or without an appended ledger event.
- **Identity drift** — any transition applied to a record whose verified release identity differs from the identity under which the run was admitted.
- **Cross-record mutation** — one attempt's run mutating another attempt's record, including precheck-failure records.

### 3.3 State semantics notes for reviewers

- `record_phase` is idempotent for re-entry of the current state (returns without event); this is a no-op, not a transition.
- `mark_failure` accepts only `PRECHECK_FAILED` or `FAILED` targets and appends both a `phase` event and a `failure` event; the failure reason is a redacted diagnostic string.
- `mark_completion` is valid only from `METADATA_REFRESH`; completion uniqueness per release identity is enforced at creation (`create_installation` returns the existing record).
- The derived `status` vocabulary (`planned` / `running` / `failed` / `completed`) is a projection of `currentPhase`, not independent state; a durable record whose `status` disagrees with `currentPhase` is corruption and must fail closed (already enforced by the DP-WP1.3 loader).

## 4. Authority Boundary

### 4.1 Mutation authority model

1. **Lock = authority.** The process holding the durable ledger lock is the sole mutation authority for the ledger file. Any mutation attempt without the lock must raise `InstallationLockError`. Lock acquisition triggers a reload so authority is always exercised over the latest durable snapshot.
2. **Orchestrator-only phase advancement.** Only the installation runner (orchestrator) may invoke `record_phase`, `mark_failure`, and `mark_completion`. Future phase adapters (registration, hook, migration, metadata) may **report step outcomes only** (`record_step_result`); they must never advance, skip, or force a phase.
3. **Protocol-only mutation.** All state changes flow through the `InstallationLedger` mutation methods (`create_installation`, `create_precheck_failure`, `record_phase`, `record_step_result`, `mark_failure`, `mark_completion`). `recover` and `find_by_identity` are read-only inspection methods and are not mutation methods. No caller may construct or edit `InstallationRecord` fields directly.
4. **Identity binding.** Every mutation is bound to the verified `ReleaseIdentity` (extension name, extension version, manifest hash, source commit). A run admitted under one identity must fail closed — not transition — when confronted with a different identity's record, except the governed `FAILED → READY` retry of the same identity.
5. **No environmental authority.** Database contents, table presence, cache state, file timestamps, container restarts, and Railway health signals confer no transition authority. Only ledgered, lock-held, identity-bound runner decisions do.

### 4.1.1 Ratification-time enforcement classification

The following classifications distinguish mechanisms already enforced by the foundation from governance requirements that a later, separately authorized implementation must make structural. A governance rule remains binding even where this charter labels its current enforcement as deferred.

| Control | Classification | Current basis and required future evidence |
| --- | --- | --- |
| Lock enforcement | **STRUCTURALLY ENFORCED** | `JsonFileInstallationLedger` requires the OS-managed lock before every durable mutation and reloads the durable snapshot after lock acquisition. |
| Transition validation | **STRUCTURALLY ENFORCED** | `transition()` rejects edges outside the governed matrix; durable mutation methods route phase changes through it. |
| Persistence validation | **STRUCTURALLY ENFORCED** | The durable loader validates ledger schema, identity completeness, event shape, and `status`/`currentPhase` consistency; corruption fails closed. |
| Record immutability | **GOVERNANCE-DEFERRED** | `InstallationRecord` is presently mutable and returned by ledger methods. A future implementation must provide reviewed immutability or defensive-copy enforcement before relying on this norm as a technical boundary. |
| Per-call identity binding | **GOVERNANCE-DEFERRED** | Current phase/failure/completion mutation methods accept `installationId` without a per-call expected-identity assertion. A future implementation must add and test identity assertions before treating this norm as structural. |

### 4.2 Authority matrix

| Actor | May do | May not do |
| --- | --- | --- |
| Operator (human) | Explicitly invoke the runner with a selected release identity; request retry after failure review | Edit ledger records/files directly; invoke phases individually; substitute release inputs |
| Runner / orchestrator | Drive §3.1 transitions under lock and identity; append all event kinds | Re-run completed steps; transition without lock; modify another identity's record |
| Future phase adapters | Report named step outcomes with postcondition evidence to the orchestrator | Advance phases; hold the lock independently; call providers/network; mutate business data |
| Durable JSON ledger adapter | Persist and validate exactly what the mutation protocol receives; fail closed on corruption | Invent events, reorder history, or reinterpret failure state |
| In-memory/reference adapter | Provide deterministic test/reference behavior only | Represent durable mutation authority, lock authority, restart-safe storage, or a production installation record |
| Railway / container runtime | Nothing (no authority) | Trigger, schedule, or imply transitions; startup must never invoke the runner (DP-WP5-owned wiring) |

### 4.3 Ledger event semantics

- **Event kinds**: `installation` (`created` / `precheck-created`), `phase` (state value), `step` (step identifier + outcome), `failure` (redacted reason, outcome `failed`), `completion` (`COMPLETED`).
- **Append-only history.** Events are never rewritten or deleted; a persisted record preserves prior attempts and states for audit. Step events deduplicate on `(kind, value, outcome)` so retried persistence is idempotent without double-counting.
- **Timestamps are audit metadata only.** `recorded_at`, `started_at`, `updated_at`, `completed_at` must never drive recovery, ordering, or transition decisions.
- **Redaction rule.** `failureReason` and event values carry stable diagnostic codes/summaries — never credentials, environment values, provider payloads, or business data (DP-WP1 charter §7).
- **Durable-boundary reload/recovery rule.** A durable mutation is authoritative only after its atomic temp-file replacement and sync complete. If persistence fails, transient in-memory state may be ahead of the durable file; it is not durable authority and must be discarded/replaced by the latest validated durable snapshot on the next lock-scoped reload/recovery. This charter makes no rollback claim for volatile state.

## 5. Recovery Interaction Boundary

### 5.1 Disposition handling (ratifies DP-WP1.3 `recover()` behavior)

| Disposition | Meaning | Permitted next action |
| --- | --- | --- |
| `NOT_FOUND` | No durable record for the identity | Create a new attempt through preflight only. |
| `RESUME` | Incomplete non-failed record exists | Controlled resume only: same verified identity, lock reacquired, reload performed, resume at the first step whose recorded postcondition is revalidated. Never replay completed steps. |
| `COMPLETED_NOOP` | Matching completed installation | Validation-only no-op. No transition, no step re-execution, no duplicate completion record. |
| `FAILED_PRESERVED` | `FAILED` or `PRECHECK_FAILED` record | Preserve for audit untouched. Only the governed retry edge (§5.3) may re-admit the same identity. |

### 5.2 Prohibited recovery behaviors

- Manufacturing transitions to "catch up" a record to observed infrastructure state.
- Treating `RESUME` as authorization to re-verify less than the full preflight input set.
- Inferring success from schema/table/cache presence (DP-WP1 charter §4.D).
- Overwriting or deleting a failed record; failure history is retained.
- Cross-process recovery without the lock; a contended lock means wait or fail, never bypass.

### 5.3 Open questions recorded for review (no code change authorized)

- **Retry governance.** The `FAILED → READY` edge exists in the foundation but has no attempt counter or operator-attestation record. This charter proposes that retry requires explicit operator re-invocation; adding attempt accounting is future, separately authorized work.
- **`BLOCKED` vocabulary.** The DP-WP1 implementation plan uses `blocked` as a possible mark; the foundation implements no `BLOCKED` state. This charter proposes that operator-block conditions be represented as `FAILED_PRESERVED` with a redacted reason until a separately authorized amendment adds a distinct state.
- **Ledger storage evolution.** The governed adapter is the DP-WP1.3 JSON file ledger. The plan's extension-owned database ledger, when authorized, must satisfy this charter's semantics and provide a reviewed migration path from file records; that path is out of scope here.
- **Cross-host lock scope.** The file lock serializes processes on one host filesystem. Multi-host or shared-volume contention semantics are unverified and must be resolved before any Railway-attached runner authorization (DP-WP5 boundary).

## 6. Relationship Contracts

### 6.1 Installation workflow

DP-WP1.4 governs transition authority **above** the workflow; it does not implement or execute it. The current foundation runner performs preflight/verification and stops before extension registration (`stopped_before="extension registration"`). Any future workflow phase becomes admissible only when a separate implementation authorization binds it to this charter: orchestrator-driven transitions, lock-held mutations, ledgered step outcomes, fail-closed recovery.

### 6.2 `AfterInstall.php`

Unchanged and unexecuted. The DP-WP1 charter §4.C classification stands: `numbering_sequence` initialization and `DataManager::rebuild()` are conditionally allowed only as named, versioned, locked, ledgered steps. Under DP-WP1.4 governance, a future hook adapter may report step outcomes but may never advance phases or run the hook as opaque code. This charter authorizes neither the adapter nor the hook execution.

### 6.3 Migrations

DP-WP4 owns all C16–C25 migration bodies, descriptors, schema bootstrap, and compensation. DP-WP1.4 governs only the `MIGRATION_PENDING` transition boundary: a future runner may enter that phase only with DP-WP4-approved descriptors, must record per-step checksum/outcome, and must stop at first failure with state preserved for the DP-WP4 owner. DP-WP1.4 itself adds no migration capability.

### 6.4 Railway provisioning

No relationship is created by this charter. Runner invocation remains an explicit administrative action, never a container-start or release action (DP-WP1 charter §3; plan §8). Railway release wiring, volumes, health, and backups remain DP-WP5-owned; roles/ACL/navigation/provisioning remain DP-WP2-owned. DP-WP1.4 adds no Railway surface, environment variable, or provisioning step.

## 7. Risks

| Risk | Impact | Mitigation proposed in this charter |
| --- | --- | --- |
| Governance drift: future adapters mutate state directly | Silent phase skips; unauditable installs | §4.1 orchestrator-only rule + §3.2 normative forbidden list as review gate |
| `FAILED → READY` retry without attempt accounting | Unbounded silent retry loops | §5.3 operator-invocation requirement; attempt accounting flagged as future work |
| Plan/code vocabulary mismatch (`blocked`) | Ambiguous recovery decisions | §5.3 records the reconciliation rule; amendment needed for a distinct state |
| File-lock scope limits (single host) | Duplicate mutation authority on shared volumes | §5.3 defers multi-host semantics to DP-WP5-facing authorization |
| Recovery without postcondition revalidation | Resuming onto inconsistent infrastructure | §5.1 makes revalidation a hard resume precondition |
| Timestamp misuse | Non-deterministic recovery decisions | §4.3 audit-only rule, already reflected in code comments |
| Redaction failure in failure reasons | Credential/data leakage into durable files | §4.3 redaction rule + review checklist item R7 |
| Uncommitted foundation state | Review baseline ambiguity | Baseline pinned in header: `197e91a` + preserved DP-WP1.3 change set |

## 8. Review Checklist

Reviewers should verify each item and record PASS/FAIL per line:

- R1. The charter introduces no new states and matches `_ALLOWED_TRANSITIONS` in `scripts/dp_wp1_installation_foundation.py` edge-for-edge (§3.1).
- R2. Every forbidden transition in §3.2 is enforceable by existing mechanisms (`transition()`, `_require_lock`, protocol-only access) or is explicitly deferred with an owner.
- R3. The mutation authority model (§4.1) names exactly one mutation authority (lock-holding orchestrator) and strips phase adapters of transition rights.
- R4. The authority matrix (§4.2) grants Railway/container runtime zero transition authority.
- R5. Ledger event semantics (§4.3) cover all five event kinds, the append-only/dedup rules, audit-only timestamps, and redaction.
- R6. Recovery dispositions (§5.1) match `recover()` behavior in both ledger adapters, and §5.2 prohibitions are each testable.
- R7. No section authorizes code change, hook execution, migration capability, Railway integration, CRM entity change, or provisioning.
- R8. Relationship contracts (§6) are consistent with DP-WP1 charter §§3–5 and the implementation plan §§5–8, and do not redefine DP-WP0/DP-WP4/DP-WP5 ownership.
- R9. Open questions (§5.3) are recorded with explicit "no code change authorized" handling.
- R10. The charter remains inside DP-WP1 ownership and states its own non-implementation boundary (§9).

## 9. Authorization Boundary

This document is review preparation only. It does not ratify DP-WP1.4, authorize implementation, modify code, execute any installation, hook, or migration, integrate Railway, change CRM entities, or provision anything. DP-WP1.4 remains **PROPOSED — NOT RATIFIED** until independent review passes and a separate ratification record is issued. DP-WP1.5+ and DP-WP2–DP-WP7 remain **NOT AUTHORIZED**.
