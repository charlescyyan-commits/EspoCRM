# Phase3C15 Discovery Audit

**Date:** 2026-07-15
**Method:** Static repository analysis — 10-dimension audit
**Model:** DeepSeek V4 Pro (Reasoning: High)
**Status:** COMPLETE
**Predecessors:** C14.3 Final Freeze (PASS), C14.4A Convergence (PASS WITH RISKS), C14.4B Reachability (READY_FOR_REMOVAL_PLAN), C14.4C Phase 1 Deprecation (PASS WITH RISKS)

**No code was modified. No external services were called. No CRM writes occurred.**

---

## Verdict

**READY_FOR_C15_DESIGN — NOT_READY_FOR_C15_IMPLEMENTATION**

C15 must first be specified as a dedicated operational-readiness phase with explicit scope boundaries. It cannot implicitly absorb the separately deferred C14.4 durable-runtime work. An approved C15 specification is the gating precondition (P-C15-01).

C15 can proceed **in parallel** with C14.4C Phase 2 observation — the C14.3 bridge and C15 operational checks are independent code paths.

---

## Executive Summary

C15 is the operational readiness phase. Its scope is deployment validation, configuration attestation, and environment evidence — not new code features. The C14.3 final freeze risk register defines the only C15 handoffs:

1. **B-3 payload snapshot encryption validation** — verify deployment has encrypted persistent volume, access boundary, and backup/retention policy
2. **Brevo TLS/egress remediation** — operator-side network fix, followed by credential-free probes and one guarded live attempt

The existing C14 architecture is frozen and stable. All C14.3 bridge modules are independent of legacy writers. No production caller uses the deprecated writers. The C15 work items are operational checks that do not require modifying any existing module.

**Critical constraint:** C15 must NOT silently absorb C14.4 work. Durable queue, work store, result inbox, scheduler, daemon, and retry mechanisms are explicitly out of C15 scope unless separately approved.

---

## 1. C15 Scope Identified

### 1.1 In Scope (from C14.3 final freeze handoff)

| Item | Source | Description |
|---|---|---|
| OPS-01 | C14.3 freeze R-4 | Verify B-3 SQLite snapshot database is on **encrypted persistent volume** with least-privilege access |
| OPS-02 | C14.3 freeze R-4 | Validate snapshot **retention, deletion, backup, restore, and incident-access policy** |
| OPS-03 | C14.3 freeze R-5 | Operator-side **Brevo TLS/egress remediation** — credential-free network probes |
| OPS-04 | C14.3 freeze R-5 | Re-run **preflight + dry-run gate** after network fix |
| OPS-05 | C14.3 freeze R-5 | One **separately authorized guarded live acceptance** attempt (recipient-guarded, no resend) |
| OPS-06 | Design | **Non-secret configuration validation** — env var presence, recipient guard, dry-run default |
| OPS-07 | Design | **Operational runbook** — rollback/escalation, test/attestation evidence format |
| OPS-08 | Design | **Evidence collection framework** — distinguish offline, synthetic, network, and live verdicts |

### 1.2 Explicitly Out of Scope

| Item | Owner | Reason |
|---|---|---|
| Durable queue (non-memory) | C14.4 | C13 queue is process-local by design; durability is a C14.4 architecture decision |
| Durable work store | C14.4 | InMemorySendExecutionWorkStore is intentional; crash recovery = C14.4 |
| Durable result inbox | C14.4 | Result repository is fixture-only; atomic replay = C14.4 |
| Scheduler / daemon | FORBIDDEN | C14.2B freeze explicitly prohibits automatic retry, daemon, scheduler |
| Automatic retry / resend | FORBIDDEN | C14.2B freeze constraint; timeout delivery ambiguity = no resend |
| Worker code changes | C14.4 | Worker is single-item, explicit invocation only |
| Provider code changes | C12 freeze | Provider contract is frozen |
| Brevo code changes | C12 freeze | Brevo adapter is frozen |
| CRM schema changes | C11 freeze | CRM projection ownership frozen |
| Legacy writer removal | C14.4C Phase 3 | Observation window must complete first |
| Real CRM writes | Governance | Requires separate approval per workspace rules |
| Real email sends (during audit) | Governance | Requires separate approval per workspace rules |

---

## 2. Current Architecture State

### 2.1 Module Inventory — Complete C14 System

```
espocrm_sync/
├── [FROZEN — C09/C10 Legacy — DEPRECATED C14.4C]
│   ├── email_lifecycle.py          W-CON-01 EmailLifecycleSyncService (DeprecationWarning active)
│   ├── email_lifecycle_sync.py     W-TEST-03 Manual harness (ESPOCRM_TEST_ENV guard)
│   ├── campaign_projection.py      W-CON-02 CampaignProjectionAdapter (DeprecationWarning active)
│   └── email_projection_guard.py   C14.3 rank guard — KEPT (not deprecated, guards both writers)
│
├── [FROZEN — C14.3 CRM Bridge]
│   ├── crm_send_execution_bridge_adapter.py  B-2 CRM bridge adapter (CrmSendExecutionBridgeAdapter)
│   ├── explicit_bridge_invocation.py         B-4 Explicit bridge invocation service
│   ├── send_execution_bridge.py              Bridge contract (BridgeRequest, BridgeNormalizedStatus)
│   └── send_execution_result_adapter.py      C/D Result adapter (SendExecutionResultCommand)
│
├── [FROZEN — C14.3 B-3 Payload Snapshots]
│   └── payload_snapshot.py         SqlitePayloadSnapshotStore, PayloadSnapshot, immutable hashes
│
├── [FROZEN — C13 Queue / Worker]
│   ├── queue_contract.py           InMemorySendExecutionQueue, QueueItem, QueueClaim
│   └── worker_execution.py         InMemorySendExecutionWorkStore, SendExecutionWorker
│
├── [FROZEN — C12 Provider]
│   ├── provider_contract.py        ProviderAdapter, FakeProviderAdapter, SendRequest, SendResult
│   ├── brevo_provider.py           BrevoProviderAdapter, BrevoConfiguration (env-backed)
│   └── brevo_http.py               UrllibBrevoHttpClient, BrevoHttpClient Protocol
│
├── [FROZEN — C11 CRM Projection — CRM-side only]
│   └── (PHP) EmailLifecycleProjectionService — owns peEmail* field authority
│
├── [FROZEN — C10 Send Execution]
│   └── send_execution.py           ControlledSendExecutionService (in-memory registry)
│
├── [FROZEN — Supporting Modules]
│   ├── draft_store.py              InMemoryDraftStore, DraftSnapshot
│   ├── human_approval.py           InMemoryHumanApprovalRegistry
│   ├── send_idempotency.py         InMemorySendIdempotencyRegistry
│   ├── reply_tracking.py           InMemoryReplyEventRegistry
│   ├── failure_classification.py   FailureCategory, classify_failure
│   ├── send_provider.py            SendProviderAdapter
│   └── real_client.py              LocalEspoCRMClient (ESPOCRM_TEST_ENV guard)
│
└── [PUBLIC API]
    └── __init__.py                  Full package re-exports (includes deprecated writers)
```

### 2.2 Key Architectural Properties Relevant to C15

| Property | Status | C15 Impact |
|---|---|---|
| **Queue durability** | Process-local/in-memory only | C15 documents limitation; does not fix |
| **Work store durability** | Process-local/in-memory only | C15 documents limitation; does not fix |
| **Result inbox** | Fixture-only (InMemoryCrmSendExecutionResultRepository) | C15 documents limitation; does not fix |
| **Snapshot durability** | SQLite with WAL + FULL synchronous | C15 validates deployment encryption, does not add code encryption |
| **Snapshot immutability** | Hash-verified on read; INSERT-or-conflict | Production-ready pattern; C15 validates deployment |
| **Provider config** | Environment variables (no file-based secrets) | C15 validates presence, not values |
| **Recipient guard** | BrevoConfiguration.acceptance_mode + test_recipient | C15 re-validates in deployment context |
| **Dry-run default** | BrevoProviderAdapter requires explicit --execute-live | C15 re-validates in deployment context |
| **No automatic execution** | Worker requires explicit caller; no scheduler/daemon | C15 must not add automation |
| **Bridge independence** | Zero imports from legacy writers | C15 can assess bridge independently |

---

## 3. C14 Dependency Analysis

### 3.1 C14.4C Phase 2 Observation ↔ C15 Parallelism

```
C14.4C Phase 2 (observation)          C15 (operational readiness)
─────────────────────────────          ─────────────────────────────
Monitor deprecation warnings    │      Validate snapshot deployment
Wait for external reports       │      Verify Brevo TLS/egress
Keep legacy writers functional  │      Non-secret config checks
Keep C14.3 bridge as preferred  │      Operational runbook
                                │      Evidence collection
        ─── NO CODE OVERLAP ───
```

**Finding: C15 can proceed in full parallel with C14.4C Phase 2 observation.**

Rationale:
- C15 operational checks are read-only deployment validation
- C14.3 bridge has zero imports from legacy writers
- C15 does not modify any writer, bridge, provider, queue, or worker code
- The observation window and operational readiness are independent concerns

### 3.2 What C15 Depends on From C14

| Dependency | Status | Blocking? |
|---|---|---|
| C14.3 bridge contracts (frozen) | Complete | No — C15 validates deployment of frozen code |
| C14.3 B-3 snapshot store | Complete | No — C15 validates deployment encryption, not code |
| C14.4A rank guard (`email_projection_guard.py`) | Complete | No — C15 does not touch guards |
| C14.4C Phase 3 (legacy removal) | Not started | **No** — C15 explicitly excludes removal |
| C14.4 durable queue (future) | Not designed | **No** — C14.4 is a separate workstream; C15 docs the current limitation |

### 3.3 What C14 Depends on From C15

**Nothing.** C14 code is frozen. C15 is pure operational validation.

---

## 4. Legacy Writer Impact on C15

### 4.1 Current State

| Writer | Status | C15 Relevance |
|---|---|---|
| W-CON-01 `EmailLifecycleSyncService` | Deprecated (DeprecationWarning), functional, guarded | **NONE** — C15 does not invoke it |
| W-CON-02 `CampaignProjectionAdapter` | Deprecated (DeprecationWarning), functional, guarded | **NONE** — C15 does not invoke it |

### 4.2 Coupling Analysis

| Coupling Point | Status |
|---|---|
| C14.3 bridge imports from legacy writers | **ZERO** — verified in C14.4B audit |
| C15 operational checks invoke legacy writers | **NOT PLANNED** — C15 is read-only deployment validation |
| Legacy writer removal blocks C15 | **NO** — C15 explicitly excludes removal |
| C15 introduces new peEmail* writers | **FORBIDDEN** — C14.3 freeze reserves CRM-side projection authority |

### 4.3 Risk if Observation Window Is Incomplete at C15 Start

**Risk R-C15-04 (LOW):** Legacy writers remain public exports. An unobserved external consumer could still import them. C15 should:
- Document that public exports remain available during observation
- Not add new code paths that depend on legacy writers
- Not claim single-writer authority until C14.4C Phase 3 completes

---

## 5. Runtime Dependency Findings

### 5.1 Current Runtime Entry Points

| Entry Point | Type | Production? | C15 Relevance |
|---|---|---|---|
| `run_local_synthetic_email_lifecycle_sync()` | Manual harness | TEST_ONLY (ESPOCRM_TEST_ENV) | None |
| `run_local_synthetic_lifecycle_sync()` | Manual harness | TEST_ONLY (ESPOCRM_TEST_ENV) | None |
| `runtime_gate.py` | CLI (read-only GET) | Readiness check | **C15 foundation** — pattern for operational checks |
| `phase3c14_3_1b4_invoke_bridge.py` | CLI (fixture) | TEST_ONLY | Pattern for explicit invocation |
| `phase3c14_3_1c_apply_result.py` | CLI (fixture) | TEST_ONLY | Pattern for result application |
| `phase3c14_2b_live_runner.py` | CLI (dry-run default) | TEST_ONLY (gated) | Pattern for guarded acceptance |
| `run-tests.ps1` | Test runner | TEST_ONLY | None |

**Finding: Zero production runtime entry points exist in the repository.** All runtime paths are either test harnesses with environment guards or explicit CLI tools with dry-run defaults.

### 5.2 Environment Variable Dependencies

| Variable | Module | Required? | Secret? | C15 Check |
|---|---|---|---|---|
| `ESPOCRM_BASE_URL` | `real_client.py`, `runtime_gate.py` | Yes (for runtime) | No | Validate presence + format |
| `ESPOCRM_API_KEY` | `real_client.py`, `runtime_gate.py` | Yes (for runtime) | **YES** | Validate presence only (never log value) |
| `ESPOCRM_TEST_ENV` | `real_client.py` | Gate only | No | Document as safety guard |
| `BREVO_API_KEY` | `brevo_provider.py` | Yes (for send) | **YES** | Validate presence only (never log value) |
| `BREVO_SENDER_EMAIL` | `brevo_provider.py` | Yes (for send) | No | Validate presence + format |
| `BREVO_SENDER_NAME` | `brevo_provider.py` | Optional | No | Validate format if present |
| `BREVO_ACCEPTANCE_MODE` | `brevo_provider.py` | Safety gate | No | Validate "true" when set |
| `BREVO_TEST_RECIPIENT` | `brevo_provider.py` | Required in acceptance | **YES** | Validate presence in acceptance mode |

### 5.3 Persistence Locations

| Store | Backend | Location | Durability | C15 Concern |
|---|---|---|---|---|
| Payload snapshots | SQLite (WAL, FULL sync) | `database_path` parameter | Durable (file) | Encrypted volume, access boundary |
| Queue items | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Work store items | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Send execution registry | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Approval registry | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Reply event registry | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Draft store | `dict` (RLock) | Process memory | **Volatile** | Document limitation |
| Idempotency registry | `dict` (RLock) | Process memory | **Volatile** | Document limitation |

**Key finding:** Only `SqlitePayloadSnapshotStore` has durable persistence. All other stores are process-local/in-memory.

---

## 6. Test Coverage Findings

### 6.1 C15-Relevant Test Inventory

| Test File | Area | Count | Mock/Real | C15 Relevance |
|---|---|---|---|---|
| `test_phase3c03_2_provider_adapter.py` | Provider contract | ~6 | Mock | Validates FakeProviderAdapter — C15 preflight foundation |
| `test_phase3c10_2_send_provider_adapter.py` | Send provider | ~5 | Mock | Validates SendProviderAdapter contract |
| `test_phase3c10_3_controlled_send_execution.py` | Send execution | ~8 | Mock | C10 execution registry |
| `test_phase3c10_4_reply_tracking_boundary.py` | Reply tracking | ~6 | Mock | Reply event boundary |
| `test_phase3c10_send_idempotency_contract.py` | Idempotency | ~5 | Mock | Send idempotency |
| `test_phase3c10_1_human_approval_model.py` | Approval | ~5 | Mock | Human approval registry |
| `test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py` | Runtime acceptance | ~8 | Mock | C10 runtime acceptance |
| `test_phase3c14_4a_writer_convergence.py` | Writer guards | ~10 | Mock | Guard convergence — validates C14.3 rank contract |
| `test_phase3c14_4c_deprecation_migration.py` | Deprecation + bridge | ~2 | Mock | Bridge preference + deprecation warnings |
| `test_espocrm_brevo_api.py` | Brevo API | ~4 | Mock | Brevo event webhook |
| `test_espocrm_real_client.py` | Real client | ~3 | Mock (env-gated) | LocalEspoCRMClient safety |

**Total: ~62 tests across 11 files validate the C10-C14 system.** All use mock clients or in-memory stores. Zero real CRM writes.

### 6.2 C15 Coverage Gaps

| Gap | Current State | Required for C15 |
|---|---|---|
| **Deployment config validation** | No automated checks for encrypted volume, file permissions, access boundary | C15 preflight scripts — environment attestation |
| **Snapshot store deployment** | Tests use temporary SQLite files; no persistent-path validation | C15 validates path is persistent, non-world-writable, outside CRM |
| **Secret redaction in logs** | `BrevoConfiguration.__repr__` redacts secrets; no automated redaction tests | C15 evidence collection must never expose secret values |
| **Process restart recovery** | No crash/restart test exists; B-3 snapshot survives (SQLite) but queue doesn't | C15 restart acceptance: prove snapshot survives, report queue loss |
| **TLS/egress probes** | Network-blocked in current environment; `SSLEOFError` documented | C15 operator-side probes — credential-free, pre-send |
| **Guarded live acceptance** | Runner exists (`phase3c14_2b_live_runner.py`) but untested in fixed network | One authorized attempt after network remediation |
| **Backup/restore drill** | No documented procedure for snapshot database backup/restore | C15 operational runbook |
| **Retention/deletion policy** | No policy defined | C15 operational runbook |

### 6.3 Test Migration Forecast

| Action | Files Affected | C15 Phase |
|---|---|---|
| Add deployment attestation tests | NEW: `tests/test_phase3c15_deployment_checks.py` | C15 implementation |
| Add secret-redaction verification | NEW assertions in deployment tests | C15 implementation |
| Add restart recovery test | NEW: `tests/test_phase3c15_restart_recovery.py` | C15 implementation |
| Keep all existing C10-C14 tests | None modified | Throughout C15 |
| Legacy writer tests remain until C14.4C Phase 3 | 4 files (documented in C14.4B) | Post-C15 |

---

## 7. Risk Matrix

| ID | Risk | Severity | Impact | Boundary | Evidence | Required Treatment |
|---|---|---|---|---|---|---|
| **R-C15-01** | Raw snapshot content stored without code-managed encryption | **MEDIUM** | **HIGH** | B-3 deployment | `payload_snapshot.py` stores recipient/subject/body in SQLite | Encrypted persistent volume + ACL + retention/backup policy + evidence attestation |
| **R-C15-02** | Queue/work store/result repository are process-local; crash loses execution/result evidence | **HIGH** | **HIGH** | C13/C14.3 | `InMemorySendExecutionQueue`, `InMemorySendExecutionWorkStore`, fixture-only result repository | Keep as C14.4 architecture work; C15 documents limitation; do NOT claim recovery in C15 |
| **R-C15-03** | Brevo TLS/egress is network-blocked; timeout delivery is ambiguous | **HIGH** | **HIGH** | C14.2B operations | `SSLEOFError` documented; dry-run runner exists but untested in fixed network | Operator remediation → credential-free probes → preflight → dry-run → one guarded attempt; NO resend |
| **R-C15-04** | Legacy writer public exports may have unobserved external consumers | **LOW** | **MEDIUM** | C14.4C migration | C14.4B audit found zero repo callers; external consumers unknown | Complete observation window or formally accept risk; do NOT remove in C15 |
| **R-C15-05** | C15 scope creep adds scheduler/retry/daemon | **MEDIUM** | **HIGH** | C13/C14.2B freeze | C14.2B frozen constraint: "no automatic retry or daemon" | Explicitly prohibit in C15 specification; validate prohibition in C15 tests |
| **R-C15-06** | Deployment evidence exposes credentials or recipient/body content | **MEDIUM** | **HIGH** | Security operations | `BrevoConfiguration.__repr__` already redacts `api_key` and `test_recipient` | Presence/attestation checks only; redacted evidence; never log raw values |
| **R-C15-07** | Configuration check mistaken for production runtime proof | **MEDIUM** | **HIGH** | Release governance | `runtime_gate.py` uses read-only GET — correct pattern | Separate offline / synthetic / network / live evidence verdicts; never conflate |
| **R-C15-08** | C15 attempts to fix C14.4 durability gaps | **LOW** | **HIGH** | Architecture boundary | C14.4 design not yet started | C15 spec must name C14.4 as owner of durable queue/work/result; C15 only validates what exists |

---

## 8. Recommended Implementation Sequence

### Phase 1: C15 Specification (Prerequisite — gates all implementation)

1. **Approve C15 operational-readiness specification.** Freeze scope: deployment validation + environment evidence only.
2. **Name explicit non-goals.** Durable queue, scheduler, retry, legacy removal, code changes.
3. **Define evidence format.** JSON-attestation schema with redacted fields.
4. **Define acceptance gates.** Offline config → synthetic restart → network probe → dry-run → guarded live (separately authorized).
5. **Close P-C15-01 and P-C15-02.** Architecture owner signs scope and prohibited-change list.

### Phase 2: C14.4 Design Decision (Parallel or prerequisite)

6. **Decide C14.4 durable queue/work/result ownership.** Either start C14.4 design or explicitly retain current non-production limitation.
7. **Document C14.4 ↔ C15 boundary.** C14.4 owns durable runtime; C15 owns deployment validation of existing persisted components.

### Phase 3: C15 Operational Preflight Checks (Coding begins)

8. **Implement deployment config validation.** Prove snapshot path is persistent, outside CRM, non-world-writable.
9. **Implement secret-redaction verification.** Every check output is redacted; no raw secret values in logs or evidence.
10. **Implement offline operational preflight.** Validate dry-run default and recipient guard are enforced with production-style configuration.
11. **Keep all checks offline, fail-closed, and non-sending.**

### Phase 4: C15 Restart and Recovery Evidence

12. **Implement process-restart acceptance.** Prove B-3 snapshot survives restart; explicitly report queue/work/result as volatile.
13. **Document durability matrix.** Which stores survive restart (snapshot only) and which don't (everything else).

### Phase 5: Environment Remediation (Operator-side)

14. **Fix Brevo TLS/egress externally.** Network/operator remediation outside code.
15. **Collect credential-free stable TLS evidence.** Probe scripts that never use API keys.
16. **Re-run existing dry-run gate.** Confirm recipient guard and dry-run default are intact.

### Phase 6: Guarded Live Acceptance (Separately Authorized)

17. **One recipient-guarded live attempt.** Single send, verified recipient, no automatic retry or resend.
18. **Separate authorization.** This step is explicitly gated and not part of C15 automated checks.

### Phase 7: Return to C14.4C Phase 3 (Post-observation)

19. **Complete C14.4C observation window.** Verify zero external deprecation reports.
20. **Proceed with Option A legacy removal.** Delete files, update exports, migrate tests. Separate from C15.

---

## 9. Open Questions

| ID | Question | Owner | Blocks |
|---|---|---|---|
| Q-C15-01 | Who owns the deployment environment (encrypted volume provisioning, access boundary)? | Platform/security | P-C15-03, P-C15-04 |
| Q-C15-02 | Who owns the Brevo network egress path (TLS termination, firewall, proxy)? | Network/operator | P-C15-05 |
| Q-C15-03 | Is C14.4 durable queue/work/result design starting, or is the current in-memory limitation accepted for the next release? | Architecture | P-C15-02 |
| Q-C15-04 | What format should C15 operational evidence take (JSON attestation, signed report, CI artifact)? | Release | C15 specification |
| Q-C15-05 | Is the observation window period (C14.4C Phase 2) time-based or event-based (e.g., "N weeks without reports" vs "next release cycle")? | Connector owner | C14.4C Phase 3 timing |
| Q-C15-06 | Does the deployment environment support `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = FULL` as configured in `SqlitePayloadSnapshotStore`? | Platform | C15 deployment validation |
| Q-C15-07 | What is the retention period for payload snapshots after send execution completes? | Data/security | P-C15-04 |

---

## 10. Files Inspected

### Source Modules (47 files in `espocrm_sync/`)
All 47 Python files in `chitu-connector/chitu_connector/espocrm_sync/` were inspected, with deep reads of:
- `payload_snapshot.py` — B-3 immutable snapshot store
- `brevo_provider.py` — C12 Brevo adapter with env-backed config
- `brevo_http.py` — HTTP transport seam
- `queue_contract.py` — C13 in-memory queue
- `worker_execution.py` — C13 in-memory work store
- `provider_contract.py` — C12 provider contract
- `send_execution.py` — C10 controlled send execution
- `email_projection_guard.py` — C14.3 rank guard
- `email_lifecycle.py` — W-CON-01 (deprecated)
- `campaign_projection.py` — W-CON-02 (deprecated)
- `crm_send_execution_bridge_adapter.py` — C14.3 B-2 bridge adapter
- `explicit_bridge_invocation.py` — C14.3 B-4 invocation service
- `send_execution_bridge.py` — C14.3 bridge contract
- `send_execution_result_adapter.py` — C14.3 C/D result adapter
- `draft_store.py` — Draft snapshot store
- `real_client.py` — LocalEspoCRMClient
- `__init__.py` — Public API exports

### Test Files (40 files in `chitu-connector/tests/`)
All 40 test files were inventoried, with focused reads of:
- `test_phase3c14_4a_writer_convergence.py`
- `test_phase3c14_4c_deprecation_migration.py`

### Scripts (10 files)
- `scripts/runtime/runtime_gate.py` — Read-only runtime gate (C15 pattern foundation)
- `scripts/acceptance/phase3c14_2b_live_runner.py` — Guarded live acceptance runner
- `scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py` — Bridge invocation CLI
- `scripts/acceptance/phase3c14_3_1c_apply_result.py` — Result application CLI
- `scripts/testing/run-tests.ps1` — Test runner

### Documentation (60+ files)
- `docs/PHASE3C14_3_FINAL_FREEZE_ACCEPTANCE_REPORT.md` — C15 handoff source
- `docs/PHASE3C14_4A_GLOBAL_WRITER_CONVERGENCE_AUDIT.md` — Writer convergence
- `docs/PHASE3C14_4B_LEGACY_WRITER_REACHABILITY_AUDIT.md` — Reachability audit
- `docs/PHASE3C14_4C_DEPRECATION_MIGRATION_REPORT.md` — Deprecation migration
- `docs/PHASE3C15_DISCOVERY_AUDIT.md` — Previous C15 audit (this file replaces)
- `docs/architecture/BOUNDARIES.md` — System boundaries
- `docs/ci/CI_ROADMAP.md` — CI roadmap
- `docs/ci/CURRENT_STATE.md` — CI current state
- `docs/deployment/INSTALL.md` — Install guide
- `docs/deployment/UPGRADE.md` — Upgrade guide
- `docs/deployment/ROLLBACK.md` — Rollback guide
- `docs/deployment/VERSIONING.md` — Versioning policy

### Deployment Files
- `deployment/provisioning/` — 26 PHP provisioning scripts (field ACL only, no writer invocation)

### Configuration Files
- `chitu-connector/pyproject.toml` — Package metadata (no console_scripts)
- `crm-extension/manifest.json` — Extension metadata (v1.9.5-alpha)

---

## 11. Searches and Commands Performed

| Search | Scope | Results |
|---|---|---|
| `grep C15\|Phase3C15` in `docs/` | All documentation | Existing C15 audit + C14.3 freeze handoff references |
| `grep EmailLifecycleSyncService\|CampaignProjectionAdapter` in all `.py` | Full codebase | Only tests + `__init__.py` re-exports |
| `grep peEmail` in `deployment/` | Deployment scripts | Field ACL provisioning only; no writer invocation |
| `grep` for imports from bridge/payload/queue/worker/Brevo modules | Test directory | Only `test_phase3c14_4c_deprecation_migration.py` imports bridge |
| `grep TODO\|FIXME\|operational` in `espocrm_sync/` | Source code | 2 references: draft store + payload snapshot future-work comments |
| Directory listing `espocrm_sync/` | Source structure | 47 Python modules |
| Directory listing `chitu-connector/tests/` | Test structure | 40 test files |
| `git log` (15 commits) | Recent history | C11 baseline hygiene, release artifacts |
| File stat timestamps | File ordering | C14.4B → C14.4C → previous C15 audit (same session) |

---

## 12. Confirmations

- ✅ **No code was modified** during this audit
- ✅ **No files were deleted, renamed, or refactored**
- ✅ **No external services were called** — all analysis is static
- ✅ **No CRM writes were performed** — all analysis read-only
- ✅ **No configuration was changed** — no env vars, settings, or manifests modified
- ✅ **No database was accessed** — no SQLite, no CRM API
- ✅ **No git operations were performed** — no commits, no branches
- ✅ **C14.3 bridge contracts remain untouched** — bridge independence verified
- ✅ **C14.4A guards remain intact** — `email_projection_guard.py` not targeted for any change
- ✅ **Legacy writers remain functional and deprecated** — C14.4C Phase 1 state preserved

---

## Recommended Next Step

Create an approved **C15 Operational Readiness Specification** document. This specification must:

1. Name its deployment owner, evidence format, security controls, and acceptance gates
2. Freeze operational scope and keep C14.4 durable-runtime work explicitly separate
3. List prohibited changes (scheduler, daemon, retry, code modifications)
4. Define preconditions P-C15-01 through P-C15-07 with owners and evidence requirements
5. Specify each operational check as fail-closed, non-sending, and evidence-redacted

Until P-C15-01 (approved specification) is closed, C15 implementation should remain blocked rather than guessing whether C15 owns durable execution infrastructure.
