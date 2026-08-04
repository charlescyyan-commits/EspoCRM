# Railway DP-WP2 Stage-1 Implementation Authorization

| Field | Value |
| --- | --- |
| Record type | Formal implementation authorization record |
| Decision | **AUTHORIZED WITH CONDITIONS** |
| Date | 2026-08-04 |
| Work package | DP-WP2 — Provisioning Lifecycle (Stage-1 skeleton) |
| Governing charter | `docs/deployment/RAILWAY_DP_WP2_PROVISIONING_LIFECYCLE_CHARTER.md` — ratified at `phase3c25-dp-wp2-ratified` |
| Transition-governance baseline | `phase3c25-dp-wp1.4-ratified` |
| Durable-ledger baseline | `phase3c25-dp-wp1.3-closed` |
| Document authority | This record captures the authorization decision only. It does not execute, stage, or commit the authorized implementation. |

## 1. Authorization Decision

```text
DP-WP2 Stage-1 skeleton implementation: AUTHORIZED WITH CONDITIONS
```

The Stage-1 skeleton — the provisioning orchestrator, the bounded ledger interaction layer, and the report-only phase adapter contract, together with their focused tests — is authorized for implementation, subject to the mandatory conditions in §6 and the exit criteria in §7. The skeleton is an **inert, testable design scaffold**; it activates no installation or provisioning workflow and creates no runtime behavior.

This record is the authorization. The creation, staging, and commit of the authorized files is a separate subsequent implementation task that must satisfy every condition and exit criterion below.

## 2. Baseline Verification

| Baseline | Tag | Resolved commit | Verified |
| --- | --- | --- | --- |
| DP-WP2 provisioning lifecycle charter | `phase3c25-dp-wp2-ratified` | `b4c348910f824abb042abd215138b7540b3e133f` | ✅ |
| DP-WP1.4 state transition governance | `phase3c25-dp-wp1.4-ratified` | `2a3f20bad121534939ab5f7c56030fbc44365662` | ✅ |
| DP-WP1.3 durable ledger foundation | `phase3c25-dp-wp1.3-closed` | `eb8368a578fc962c5be26f1f423873bde2433340` | ✅ |

Current `HEAD` at authorization time: `b4c348910f824abb042abd215138b7540b3e133f`.

## 3. Authorized Stage-1 Scope

Stage-1 implements the DP-WP2 skeleton only, as a scaffold over the unmodified DP-WP1.3 foundation:

1. **Provisioning Orchestrator** — explicit-invocation coordination; disposition selection from `recover()`; one reviewed adapter at a time; redacted outcome recording; operator-block resolution to `PRECHECK_FAILED`/`FAILED`; no lifecycle movement outside the DP-WP1.4 matrix.
2. **Ledger Interaction Layer** — the approved DP-WP1.3 protocol surface only; durable lock boundary preservation; per-call identity assertion; no direct file writes, no record-field editing, no competing durable store.
3. **Phase Adapter Contract** — report-only protocol (input/output/postcondition, idempotency, redacted failure contract); empty adapter set fails closed; adapters can never advance state.
4. **Recovery Handling** — `NOT_FOUND`, `RESUME`, `COMPLETED_NOOP`, `FAILED_PRESERVED` disposition behavior, with `FAILED_PRESERVED` preservation for failed/precheck-failed records.

## 4. Exact Authorized Files

### New implementation files allowed to create

```text
scripts/dp_wp2_ledger_interaction.py
scripts/dp_wp2_phase_adapter_contract.py
scripts/dp_wp2_provisioning_orchestrator.py
```

### New test files allowed to create

```text
tests/test_railway_dp_wp2_ledger_interaction.py
tests/test_railway_dp_wp2_phase_adapter_contract.py
tests/test_railway_dp_wp2_provisioning_orchestrator.py
tests/test_railway_dp_wp2_recovery.py
```

### Documentation allowed to create for this record

```text
docs/audit/RAILWAY_DP_WP2_STAGE1_IMPLEMENTATION_AUTHORIZATION.md
```

This documentation record is the only file created by the authorization task itself; it is not a runtime implementation artifact.

## 5. Forbidden Scope

The following remain **not authorized** in Stage-1 or any later stage without a separate authorization:

```text
scripts/dp_wp1_installation_foundation.py                 (read-only DP-WP1.3 foundation)
scripts/generate_railway_artifact_manifest.py             (DP-WP0 surface)
deployment/railway/full-application-artifact-manifest.json (DP-WP0 canonical manifest)
deployment/railway/Dockerfile
deployment/railway/docker-entrypoint-railway.sh
deployment/railway/railway.toml
deployment/railway/healthcheck.sh
deployment/railway/docker-compose.staging.yml
crm-extension/** (including AfterInstall.php, entityDefs, ACL, navigation, metadata,
                  dashboards, branding)
migration bodies, descriptors, DDL, schema bootstrap
runtime configuration, secrets, environment variables
EspoCRM core application code
```

Additionally, Stage-1 must not:

- introduce a `BLOCKED` state or any state outside the ratified DP-WP1.4 ten-state vocabulary (`UNKNOWN`, `PRECHECK_FAILED`, `READY`, `INSTALLING`, `REGISTERED`, `HOOK_PENDING`, `MIGRATION_PENDING`, `METADATA_REFRESH`, `COMPLETED`, `FAILED`);
- define, register, or invoke any concrete phase adapter (only the report-only contract is authorized);
- add hooks, migrations, Railway wiring, CRM entities, or business-data access;
- modify any existing DP-WP0/DP-WP1 source or test file;
- activate, schedule, or wire any installation or provisioning workflow.

## 6. Required Conditions

The authorization is conditional on each of the following being implemented and evidenced:

| # | Condition | Requirement |
| --- | --- | --- |
| C1 | **Identity assertion** | Per-call identity binding: every ledger mutation made through the interaction layer must assert the expected verified release identity against the record being mutated, closing the DP-WP1.4 §4.1.1 per-call identity-binding deferral. A mismatched identity must fail closed, never transition. |
| C2 | **Durable lock boundary** | All durable mutations occur only while the DP-WP1.3 durable lock is held, preserving the acquire → reload semantics of `JsonFileInstallationLedger`. No lock bypass, no direct ledger-file write, no competing durable state store, and no durable authority for the in-memory/reference adapter. |
| C3 | **Empty adapter fail closed** | With no reviewed adapter registered, the orchestrator must stop with a governed failure disposition (redacted reason recorded) rather than proceed. A missing adapter contract is a hard stop; no adapter is invoked and no lifecycle movement occurs. |
| C4 | **No runtime activation** | The skeleton must not activate on container start, HTTP request, scheduled task, healthcheck, browser action, or any workflow trigger. Only an explicit operator invocation may exercise the orchestrator, and the skeleton wires no entry point into any runtime. |

## 7. Exit Criteria for Stage-1

Stage-1 is complete only when all of the following are evidenced:

1. **Static integrity.** The three implementation modules import cleanly, contain no runtime entry-point registration, and reference the DP-WP1.3 protocol and DP-WP1.4 states only; `git diff --check` passes and no prohibited unresolved markers remain.
2. **Ledger interaction layer.** Calls only the approved protocol methods (`recover`, `create_installation`, `create_precheck_failure`, `record_phase`, `record_step_result`, `mark_failure`, `mark_completion`); enforces the durable lock boundary; asserts per-call identity (C1); cannot write files directly, edit `InstallationRecord` fields, or route around the lock (C2).
3. **Phase adapter contract.** Report-only; adapters can report an outcome/postcondition but cannot advance, skip, retry, complete, or fail a record; an empty adapter set fails closed (C3).
4. **Orchestrator behavior.** Selects the correct disposition for all four `RecoveryDisposition` values; requests only DP-WP1.4-permitted transitions; resolves operator blocks to `PRECHECK_FAILED` (preflight) or `FAILED` (later phase) with a redacted reason; returns only redacted administrative results; never creates a `BLOCKED` state.
5. **No runtime activation.** No startup, HTTP, scheduler, healthcheck, or browser path can reach the orchestrator (C4).
6. **Tests.** The four authorized test files pass: unit (disposition selection, transition-request mapping, operator-block mapping, adapter report-only conformance, redaction, lock boundary, identity assertion), regression (the existing DP-WP0/DP-WP1 suites remain unchanged and green), and corruption/recovery (corrupt ledger → fail closed; lock contention; interrupted-run `RESUME` only after revalidation; `FAILED_PRESERVED` preservation; restart safety).
7. **Scope compliance.** No forbidden path (§5) is modified; no existing file changes outside the exact allowlist (§4).
8. **Independent review readiness.** The implementation is reviewable as a self-contained skeleton for a separate DP-WP2 Stage-1 implementation review before any further stage or any runtime wiring is considered.

## 8. Authorization State

```text
DP-WP1.3 Durable Ledger: CLOSED (phase3c25-dp-wp1.3-closed)
DP-WP1.4 State Transition Governance: RATIFIED (phase3c25-dp-wp1.4-ratified)
DP-WP2 Charter: RATIFIED (phase3c25-dp-wp2-ratified)
DP-WP2 Stage-1 skeleton implementation: AUTHORIZED WITH CONDITIONS
DP-WP2 concrete phase adapters: NOT AUTHORIZED
DP-WP2 runtime activation / workflow wiring: NOT AUTHORIZED
Migration (DP-WP4), Railway wiring (DP-WP5), CRM changes: NOT AUTHORIZED
```

This record grants the Stage-1 skeleton authorization only. It authorizes no workflow activation, no concrete adapter, no migration, no Railway integration, no CRM change, and no production or Railway use.
