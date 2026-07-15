# Phase3C14.4B Legacy Writer Reachability Audit

**Date:** 2026-07-15
**Status:** COMPLETE
**Predecessor:** C14.4A (PASS WITH RISKS)
**Scope:** Production reachability of W-CON-01 and W-CON-02 legacy peEmail* writers
**Method:** Static import graph + deployment/CI/CLI/scheduler surface audit
**No code was modified. No writer was deleted. No CRM write was performed.**

---

## Executive Summary

Both legacy writers (`EmailLifecycleSyncService` and `CampaignProjectionAdapter`) have **zero production callers** in the repository. Every import path dead-ends in test harnesses or the public `__init__.py` re-export. No CLI command, scheduler, cron job, Docker entrypoint, or deployment script invokes either writer against a real CRM. The C14.3 bridge is a completely independent code path.

**Verdict: READY_FOR_REMOVAL_PLAN**

---

## 1. Audit Dimensions — Full Results

### 1.1 Python Import Graph

All non-test, non-`__init__.py` importers of the two legacy writers:

| Importer | W-CON-01 | W-CON-02 | Production? |
|---|---|---|---|
| `espocrm_sync/__init__.py` | ✅ (re-export) | ✅ (re-export) | Public API surface only |
| `espocrm_sync/email_lifecycle_sync.py` | ✅ (W-TEST-03) | — | TEST_ONLY (`ESPOCRM_TEST_ENV` guard) |
| `tests/test_espocrm_email_lifecycle.py` | ✅ | — | TEST_ONLY (mock client) |
| `tests/test_phase3c14_4a_writer_convergence.py` | ✅ | ✅ | TEST_ONLY (mock client) |
| `tests/test_phase3c09_campaign_projection.py` | — | ✅ | TEST_ONLY (mock client) |
| `tests/test_phase3c09_outreach_runtime_acceptance.py` | — | ✅ | TEST_ONLY (mock client) |

**Zero production modules** import either writer. The C14.3 bridge modules (`crm_send_execution_bridge_adapter.py`, `explicit_bridge_invocation.py`, `send_execution_bridge.py`, `send_execution_result_adapter.py`) have no import dependency on either legacy writer.

### 1.2 CLI Commands

- `pyproject.toml`: No `[project.scripts]` or `[project.entry-points]` defined
- No `__main__.py` in any package
- No `console_scripts` entry points
- The `run_local_synthetic_email_lifecycle_sync()` function in `email_lifecycle_sync.py` is a manually-invoked function (no `if __name__ == "__main__"`), guarded by `ESPOCRM_TEST_ENV` checks and `LocalEspoCRMClient.from_environment()`

**Verdict: No CLI path to either writer.**

### 1.3 Scheduled Tasks / Cron / systemd / Docker

- No `Dockerfile` in repository
- No `docker-compose.yml` in repository
- No `.github/workflows/` directory (no CI/CD pipelines)
- No `crontab` files
- No `systemd` unit files
- No `Makefile`
- No `.sh` or `.bat` scripts
- `.ps1` test runner scripts (`scripts/testing/run-tests.ps1`) run `unittest discover` only — no writer invocation outside test discovery

**Verdict: No scheduled or containerized execution path.**

### 1.4 Deployment Files

- `deployment/provisioning/`: PHP provisioning scripts reference `peEmailStatus`, `peEmailCampaignName`, `peEmailReplyStatus` **as field ACL definitions only** — they provision field visibility, not writer invocation
- `deployment/provisioning/phase3b06_provision_synthetic_lead.php`: Sets initial `peEmailStatus` = `SENT` on a synthetic Lead — static provisioning, not a writer call
- Zero references to `EmailLifecycleSyncService` or `CampaignProjectionAdapter` class names

**Verdict: Deployment files do not invoke either writer.**

### 1.5 CI/CD Workflows

- No `.github/` directory exists
- No CI configuration files of any kind (GitLab CI, Jenkins, CircleCI, etc.)

**Verdict: No CI/CD path.**

### 1.6 Connector Package Exports

Both writers are publicly exported in `chitu_connector/espocrm_sync/__init__.py`:

```python
# Line 12
from chitu_connector.espocrm_sync.email_lifecycle import (
    EmailLifecycleStatus, EmailLifecycleSyncResult,
    EmailLifecycleSyncService, EmailLifecycleUpdate
)
# Line 106
from chitu_connector.espocrm_sync.campaign_projection import (
    CampaignProjectionAdapter, CampaignProjectionResult,
    CampaignProjectionStatus, LeadCampaignProjectionClient
)
```

These are the **only public API surface** through which external consumers could reach the writers. The `__all__` list (lines 161–209) includes both.

**Risk: External packages could import these from `chitu_connector.espocrm_sync`. Removal requires a deprecation window on the public export, not just internal deletion.**

### 1.7 Test Usage

| Test File | Writer | Mock/Real | Fields Exercised |
|---|---|---|---|
| `test_espocrm_email_lifecycle.py` | W-CON-01 | Mock (no CRM) | peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus |
| `test_phase3c14_4a_writer_convergence.py` | W-CON-01, W-CON-02 | Mock (no CRM) | All fields + guard decision testing |
| `test_phase3c09_campaign_projection.py` | W-CON-02 | Mock (no CRM) | peEmailStatus, peEmailCampaignName, peRecommendedApproach |
| `test_phase3c09_outreach_runtime_acceptance.py` | W-CON-02 | Mock (no CRM) | Campaign projection status |
| `test_phase3c11_2_persistence_entities.py` | W-CON-01 | Forbidden-term check | Lists `EmailLifecycleSyncService` as forbidden |

**All tests use mock clients. Zero real CRM writes in test suite.** The `run_local_synthetic_email_lifecycle_sync()` (W-TEST-03) is the only path that touches a real CRM, and it is a manual harness with an `ESPOCRM_TEST_ENV` environment guard.

### 1.8 Documentation References

Extensive documentation references exist across 20+ audit/report/design documents. Key mentions:

| Document | Context |
|---|---|
| `PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md` | Describes `EmailLifecycleSyncService` as a disconnected CRM Display Layer |
| `PHASE3C11_0_PERSISTENCE_ARCHITECTURE_APPROVAL.md` | RISK-2: "EmailLifecycleSyncService and C10 execution are disconnected systems" |
| `PHASE_G06_C11_FOLLOWUP_BOUNDARY_AUDIT.md` | "Writer B (EmailLifecycleSyncService) MUST be deprecated" — explicit directive |
| `PHASE3C14_3_1_FINAL_BOUNDARY_AUDIT.md` | Both writers "retain direct existing-Lead update seams" |
| `PHASE3C14_4A_GLOBAL_WRITER_CONVERGENCE_AUDIT.md` | C14.4A guard implementation report |
| `PHASE3_PRE_C10_PRODUCTION_READINESS_AUDIT.md` | Documents field ownership boundaries |

Documentation does not constitute a production code path.

### 1.9 External Integration Assumptions

- The `EmailLifecycleClient` Protocol and `LeadCampaignProjectionClient` Protocol are defined within the same modules — no external implementation exists
- `LocalEspoCRMClient` (`real_client.py`) implements both Protocols but is only called from the test harness `email_lifecycle_sync.py`
- The `update_lead_campaign_projection()` method on `LocalEspoCRMClient` (line 189) is the real CRM write path — called only from `CampaignProjectionAdapter.project()` and only from tests

### 1.10 C14.3 Bridge Independence Confirmed

The C14.3 bridge path uses a completely separate module set:

```
explicit_bridge_invocation.py  →  crm_send_execution_bridge_adapter.py  →  queue_contract.py
send_execution_result_adapter.py  →  send_execution_bridge.py
```

Zero imports from `email_lifecycle.py` or `campaign_projection.py`. The bridge writes through `SendExecutionWorker` → `ProviderAdapter` → queue, not through legacy direct PATCH.

---

## 2. Detailed Writer Analysis

### W-CON-01: `EmailLifecycleSyncService`

**Definition:** `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py:80`

**Fields written:** `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus`

**Target entities:** Lead (required), Opportunity (optional)

**C14.4A guards applied:**
- `guard_email_summary_update()` — status-rank ordering check against `C14_3_EMAIL_STATUS_RANK`
- Terminal status protection (SENT/FAILED/CANCELLED/REPLIED/BOUNCED cannot be downgraded)
- Timestamp ordering check (newer timestamps only)
- `exclude_empty_fields()` — prevents clearing text fields with empty writes

**Call chain (complete):**
```
[ZERO PRODUCTION CALLERS]
     ↓
  __init__.py (re-export only)
     ↓
  email_lifecycle_sync.py::run_local_synthetic_email_lifecycle_sync()  [W-TEST-03, manual, ESPOCRM_TEST_ENV]
     ↓
  EmailLifecycleSyncService.sync(client, lead_id, update, opportunity_id?)
     ↓
  EmailLifecycleUpdate.fields() → field allowlist enforced
     ↓
  guard_email_summary_update() → C14.3 rank check
     ↓
  client.update_record("Lead"/"Opportunity", id, fields)  [direct PATCH]
```

**Answers:**
1. **Who calls?** Only tests and the manual test harness (W-TEST-03). Zero production callers.
2. **Production entry point?** No. No CLI, no scheduler, no cron.
3. **Used by scheduler?** No scheduler exists in this repository.
4. **Historical compatibility only?** Yes. The C14.4A guards were added specifically to make it safe as a compatibility shim while the C14.3 bridge replaces it.
5. **Impact of deletion?** Test files break (4 test files reference it). Public API contract changes (`__init__.py` export removed). Documentation becomes historical. No production functionality affected.

### W-CON-02: `CampaignProjectionAdapter`

**Definition:** `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py:52`

**Fields written:** `peEmailStatus` (always `DRAFT_READY`), `peEmailCampaignName`, `peRecommendedApproach`

**Target entities:** Lead only (existing Lead, update only — no create)

**C14.4A guards applied:**
- `guard_email_summary_update()` — status-rank check (same guard as W-CON-01)
- Idempotent by design (always projects `DRAFT_READY`)
- Input validation on `EmailDraft` (subject, body, generation_version, qualification_status, evidence_references)
- Protocol-enforced: `LeadCampaignProjectionClient` has no `create` or `send` method

**Call chain (complete):**
```
[ZERO PRODUCTION CALLERS]
     ↓
  __init__.py (re-export only)
     ↓
  CampaignProjectionAdapter(client).project(lead_id, email_draft)
     ↓
  _projection_fields() → validates EmailDraft + 3-field allowlist
     ↓
  guard_email_summary_update() → C14.3 rank check
     ↓
  client.update_lead_campaign_projection(lead_id, fields)  [direct PUT]
```

**Answers:**
1. **Who calls?** Only tests (3 test files). Zero production callers.
2. **Production entry point?** No.
3. **Used by scheduler?** No scheduler exists.
4. **Historical compatibility only?** Yes. Designed for C09 draft preparation display; superseded by C14.3 bridge for actual send execution.
5. **Impact of deletion?** Test files break (3 test files reference it). Public API contract changes. The C09 "Draft Preparation" display path loses its connector-side projection (but CRM-side `EmailLifecycleProjectionService` remains).

---

## 3. Global Reachability Matrix

| Writer | Production Path | Caller | Status | Removal Risk |
|---|---|---|---|---|
| **W-CON-01** `EmailLifecycleSyncService` | **NONE** | Tests only (4 files) + `__init__.py` re-export | **SAFE_REMOVE** | LOW — production is unaffected; tests need migration |
| **W-CON-02** `CampaignProjectionAdapter` | **NONE** | Tests only (3 files) + `__init__.py` re-export | **SAFE_REMOVE** | LOW — production is unaffected; tests need migration |
| **W-TEST-03** `run_local_synthetic_email_lifecycle_sync` | Manual harness (`ESPOCRM_TEST_ENV`) | `email_lifecycle_sync.py` | **SAFE_REMOVE** (with W-CON-01) | LOW — test-only harness |
| **W-TEST-04** `test_espocrm_email_lifecycle.py` | Test suite | unittest discover | **MIGRATE** | Tests validate guard behavior; migrate to C14.3 bridge tests |

---

## 4. Removal Impact Analysis

### 4.1 Functions Affected

If both writers are removed:

| Affected Area | Detail | Severity |
|---|---|---|
| **C09 Draft Preparation display** | `CampaignProjectionAdapter` was the connector-side projector for `peEmailStatus=DRAFT_READY`. The CRM-side `EmailLifecycleProjectionService` remains and can handle this. | LOW — CRM-side covers it |
| **C10 Lifecycle display sync** | `EmailLifecycleSyncService` was the connector-side sync for APPROVED/SENT/REPLIED/BOUNCED. The C14.3 bridge + `EmailLifecycleProjectionService` now handles these transitions. | LOW — bridge replaces it |
| **Manual test harness** | `run_local_synthetic_email_lifecycle_sync()` in `email_lifecycle_sync.py` becomes dead code. | LOW — test-only |
| **Public API** | `__init__.py` exports removed. External consumers relying on `from chitu_connector.espocrm_sync import EmailLifecycleSyncService` break. | MEDIUM — needs deprecation window |

### 4.2 Tests That Would Fail

| Test File | Failing Tests | Reason |
|---|---|---|
| `test_espocrm_email_lifecycle.py` | All (~4 test methods) | Directly imports and instantiates `EmailLifecycleSyncService` |
| `test_phase3c09_campaign_projection.py` | `CampaignProjectionAdapterTests` (all) | Directly imports and instantiates `CampaignProjectionAdapter` |
| `test_phase3c14_4a_writer_convergence.py` | W-CON-01 and W-CON-02 guard tests | Directly imports both writers |
| `test_phase3c09_outreach_runtime_acceptance.py` | Campaign projection test | Uses `CampaignProjectionAdapter` |
| `test_phase3c11_2_persistence_entities.py` | Forbidden-term check | Lists `EmailLifecycleSyncService` as forbidden — needs update |

**Total: ~12-15 test methods across 5 files** would need migration or removal.

### 4.3 Contracts Broken

| Contract | Status |
|---|---|
| `EmailLifecycleClient` Protocol | Defined in `email_lifecycle.py` — removed with writer |
| `LeadCampaignProjectionClient` Protocol | Defined in `campaign_projection.py` — removed with writer |
| `EmailLifecycleUpdate` dataclass | Input contract for W-CON-01 — removed with writer |
| `EmailLifecycleSyncResult` dataclass | Output contract for W-CON-01 — removed with writer |
| `CampaignProjectionResult` dataclass | Output contract for W-CON-02 — removed with writer |
| `EmailLifecycleStatus` enum | Shared enum — may have value independent of writers |
| `CampaignProjectionStatus` enum | Output enum for W-CON-02 — removed with writer |
| C14.3 `C14_3_EMAIL_STATUS_RANK` | Lives in `email_projection_guard.py` — **NOT removed**, stays as connector-side contract mirror |
| `guard_email_summary_update()` | Lives in `email_projection_guard.py` — **NOT removed**, may be reusable by future guards |

### 4.4 Documentation-Only References

All 20+ documentation files referencing these writers become historical records. Key docs to annotate:
- `PHASE3C14_4A_GLOBAL_WRITER_CONVERGENCE_AUDIT.md` — Add "REMOVED in C14.4B" note
- `PHASE3C14_3_1A_WRITER_INVENTORY.md` — Mark entries as historical
- `PHASE_G06_C11_FOLLOWUP_BOUNDARY_AUDIT.md` — Deprecation directive fulfilled

---

## 5. Option A Removal Plan

### Guiding Principle

The C14.4A guards (`email_projection_guard.py`) ensure both writers are safe to keep as no-op compatibility shims during the deprecation window. The plan phases are designed to validate zero production impact before physical deletion.

### Phase 1: Deprecation (C14.4B — this phase)

**Actions:**
1. Mark both classes with `DeprecationWarning` in their docstrings
2. Add `warnings.warn("...", DeprecationWarning)` on instantiation
3. Do NOT remove from `__init__.py` yet
4. Add `# DEPRECATED: C14.4B — scheduled for removal in C14.4C` comments
5. Update `__all__` comments to note deprecation status

**No code deletion. No behavior change. No test breakage.**

**Validation:**
- All existing tests pass
- Deprecation warnings visible in test output
- C14.3 bridge continues to operate independently

### Phase 2: Observe (1 release cycle)

**Actions:**
1. Monitor for any external consumer reports
2. Verify C14.3 bridge handles all peEmail* transitions that the legacy writers covered:
   - DRAFT_READY → APPROVED → SENT → REPLIED/BOUNCED
3. Confirm `EmailLifecycleProjectionService` (CRM-side PHP) is the sole peEmail* writer in production
4. Run C14.4A guard convergence tests — ensure guards still prevent regression

**No code deletion. Observation only.**

**Gate criteria for Phase 3:**
- Zero external dependency reports
- C14.3 bridge handles all lifecycle transitions
- CRM-side projection service confirmed as sole production writer

### Phase 3: Remove (C14.4C)

**Actions:**
1. Remove from `__init__.py` exports:
   - `EmailLifecycleSyncService`, `EmailLifecycleUpdate`, `EmailLifecycleSyncResult`
   - `CampaignProjectionAdapter`, `CampaignProjectionResult`, `CampaignProjectionStatus`, `LeadCampaignProjectionClient`
2. Evaluate `EmailLifecycleStatus` enum — keep if used by C14.3 bridge or other modules; remove if only used by legacy writers
3. Remove `email_lifecycle.py` (or retain only `EmailLifecycleStatus` if needed)
4. Remove `campaign_projection.py`
5. Remove `email_lifecycle_sync.py` (W-TEST-03 manual harness)
6. Remove or migrate test files:
   - `test_espocrm_email_lifecycle.py` → **DELETE** (guard tests covered by C14.4A convergence tests)
   - `test_phase3c09_campaign_projection.py` → **DELETE** (C09 frozen; no longer needed)
   - `test_phase3c09_outreach_runtime_acceptance.py` → **MIGRATE** campaign projection test to use C14.3 bridge
   - `test_phase3c14_4a_writer_convergence.py` → **MIGRATE** to test `email_projection_guard.py` directly
   - `test_phase3c11_2_persistence_entities.py` → **UPDATE** forbidden-term list
7. Update `__all__` in `__init__.py`
8. Annotate historical docs with removal version

**Code deletion authorized. All tests must pass after migration.**

---

## 6. What Stays (NOT Removed)

The following C14.4A infrastructure is **independent of the legacy writers** and stays:

| Module | Component | Reason |
|---|---|---|
| `email_projection_guard.py` | `C14_3_EMAIL_STATUS_RANK` | Frozen C14.3 contract mirror — used by C14.4A guard tests |
| `email_projection_guard.py` | `guard_email_summary_update()` | Guard function — may be reusable for future connector-side safety checks |
| `email_projection_guard.py` | `EmailProjectionGuardDecision` | Guard output dataclass |
| `email_projection_guard.py` | `exclude_empty_fields()` | Utility — may be reusable |
| C14.3 bridge modules | All (`crm_send_execution_bridge_adapter.py`, `explicit_bridge_invocation.py`, `send_execution_bridge.py`, `send_execution_result_adapter.py`, `payload_snapshot.py`, `queue_contract.py`, etc.) | Independent production path |

---

## 7. Risk Register

| Risk ID | Description | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-4B-01 | External package imports writers from `chitu_connector.espocrm_sync` | LOW | MEDIUM | Phase 1 deprecation warning gives signal |
| R-4B-02 | `EmailLifecycleStatus` enum removal breaks C14.3 bridge or Brevo integration | LOW | MEDIUM | Audit enum usage before Phase 3 deletion |
| R-4B-03 | CRM-side `EmailLifecycleProjectionService` doesn't cover all transitions | LOW | HIGH | Phase 2 observation validates coverage |
| R-4B-04 | Test migration introduces gaps in guard coverage | MEDIUM | LOW | Migrate guard tests to `email_projection_guard.py` directly |
| R-4B-05 | `CampaignProjectionAdapter` removal loses DRAFT_READY projection path | LOW | LOW | CRM-side projection service covers this; C09 is frozen |

---

## 8. Enum & Dataclass Retention Decision

| Symbol | Decision | Rationale |
|---|---|---|
| `EmailLifecycleStatus` | **KEEP** (evaluate in Phase 2) | Shared enum; verify no external consumers before removing |
| `EmailLifecycleUpdate` | **REMOVE** in Phase 3 | Only used by W-CON-01; no independent value |
| `EmailLifecycleSyncResult` | **REMOVE** in Phase 3 | Only returned by W-CON-01; no independent value |
| `EmailLifecycleSyncService` | **REMOVE** in Phase 3 | The legacy writer itself |
| `CampaignProjectionAdapter` | **REMOVE** in Phase 3 | The legacy writer itself |
| `CampaignProjectionResult` | **REMOVE** in Phase 3 | Only returned by W-CON-02; no independent value |
| `CampaignProjectionStatus` | **REMOVE** in Phase 3 | Only used by W-CON-02; no independent value |
| `LeadCampaignProjectionClient` | **REMOVE** in Phase 3 | Only used by W-CON-02; no independent value |
| `EmailLifecycleClient` | **REMOVE** in Phase 3 | Only used by W-CON-01; no independent value |
| `run_local_synthetic_email_lifecycle_sync` | **REMOVE** in Phase 3 | W-TEST-03 manual harness |
| `EmailLifecycleRuntimeResult` | **REMOVE** in Phase 3 | Only used by W-TEST-03 |

---

## 9. Final Verdict

```
VERDICT: READY_FOR_REMOVAL_PLAN
         ↓
         KEEP_GUARDED (Phase 1: deprecation warnings, no deletion)
         ↓
         OBSERVE (Phase 2: 1 release cycle)
         ↓
         REMOVE (Phase 3: physical deletion)
```

### Confirmed

- ✅ **No code was modified** in this audit
- ✅ **No writer was deleted** in this audit
- ✅ **No C14.3 contracts were touched** — bridge independence verified
- ✅ **No CRM writes were performed** — all analysis is static
- ✅ **C14.4A guards remain intact** — `email_projection_guard.py` is NOT targeted for removal
- ✅ **Zero production callers found** — exhaustive import graph analysis confirms tests are the sole consumers

### Next Phase

**C14.4B Phase 1 (Deprecation):** Add `DeprecationWarning` to both writers, update docstrings. No deletion.

**C14.4C Phase 3 (Removal):** After 1 release cycle of observation, physically delete both writers and migrate affected tests. The C14.3 bridge becomes the sole connector-side peEmail* transition path, with CRM-side `EmailLifecycleProjectionService` as the authoritative writer.
