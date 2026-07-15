# Phase3C14.4A Global Writer Convergence Audit

**Date:** 2026-07-14
**Phase:** C14.4A — Writer Convergence Audit (Read-Only)
**Status:** COMPLETE
**Previous Phase:** C14.3 FREEZE_APPROVED_WITH_RISKS

---

## 1. Executive Verdict

**VERDICT: READY_FOR_IMPLEMENTATION**

The audit identified **16 writers** across the full repository. Of these, **6 writers**
are production-reachable for `peEmail*` / `peProposal*` fields. **2 connector writers**
(W-CON-01, W-CON-02) conflict with the CRM-side canonical projection authority
(`EmailLifecycleProjectionService`). These 2 connector writers have **no guards**
(no rank, timestamp, null-exclusion, or terminal-state protection) and can
degrade Lead email state after CRM projection.

The recommended convergence path is **Option C (Guarded Compatibility Writer)**
as the immediate gate, with **Option A (Remove Legacy Email Summary Writes)**
as the definitive target after connector call-site verification.

---

## 2. Global Writer Inventory

### Classification Key

| Code | Meaning |
|------|---------|
| CANONICAL | Authoritative writer; single owner of its field set |
| LEGACY_COMPAT | Historically required; now superseded but still reachable |
| PROJECTION | Reads source records, projects computed state |
| FIXTURE | Deployment/dev data seeding only |
| TEST_ONLY | Test harness or in-memory fixture |
| FORBIDDEN | Violates single-writer principle; MUST be removed or gated |
| UNKNOWN | Production reachability not determined |

### Complete Inventory

| Writer ID | File | Class/Function | Trigger | Fields Written | Source State | Direct/Projection | Runtime Path | Idempotency | Current Authority | Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| **W-CRM-01** | `EmailLifecycleProjectionService.php:78` | `projectEmailEvent()` | EmailEvent after-save hook | peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus | EmailEvent.eventType, eventAt, campaign | PROJECTION | CRM hook (every EmailEvent save) | Timestamp gate + rank gate + changed-only filter | **CANONICAL** | LOW |
| **W-CRM-02** | `EmailLifecycleProjectionService.php:127` | `projectDraftApproval()` | DraftApproval after-save hook | peEmailStatus, peLastEmailDate | DraftApproval.status, approvedAt | PROJECTION | CRM hook (every DraftApproval save) | Timestamp gate + rank gate + changed-only filter | **CANONICAL** | LOW |
| **W-CRM-03** | `EmailLifecycleProjectionService.php:137` | `projectSendExecution()` | SendExecution after-save hook | peEmailStatus, peLastEmailDate | SendExecution.status, modifiedAt | PROJECTION | CRM hook (every SendExecution save) | Timestamp gate + rank gate + changed-only filter | **CANONICAL** | LOW |
| **W-CRM-04** | `EmailLifecycleProjectionService.php:147` | `projectReplyEvent()` | ReplyEvent after-save hook | peEmailReplyStatus, peLastEmailDate | ReplyEvent.replyStatus, receivedAt | PROJECTION | CRM hook (every ReplyEvent save) | Timestamp gate + changed-only filter | **CANONICAL** | LOW |
| **W-CRM-05** | `ChituSyncService.php:21` | `syncLead()` | Connector API `Prospecting/sync/lead` | peOpportunityScoreV4, peScoreTier, peBestFirstProduct, peQualificationStatus, peConfidence, peEvidenceCoverage, peEngineVersion, peScoreRulesVersion, peSyncStatus, peResearchStatus, peSourceSystem, peCandidateId, peLastSyncAt, peResearchSummary, peKeyEvidence, peRecommendedApproach, pePriorityLevel, peLastResearchedAt, peSourceType, peDiscoverySource (NO peEmail*) | SyncContractPayload | DIRECT | Connector CLI / scheduler invocation | External ID dedup (peCandidateId) | **CANONICAL** (intelligence fields only) | LOW |
| **W-CRM-06** | `ChituSyncService.php:219` | `syncOpportunityProposal()` | Connector API `Prospecting/sync/opportunity-proposal` | peProposalProductFitScore, peProposalCooperationType, peProposalSuggestedNextAction, peProposalEligibility, peProposalAction, peBestFirstProduct, peOpportunityScoreV4 | SyncContractPayload (score >= 80 gate) | DIRECT | Connector CLI / scheduler invocation | External ID based | **CANONICAL** (peProposal* fields) | LOW |
| **W-CON-01** | `email_lifecycle.py:69` | `EmailLifecycleSyncService.sync()` | Explicit caller (test harness only in repo) | peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus | EmailLifecycleUpdate dataclass | DIRECT PATCH to Lead | **UNKNOWN** production reachability — only test callers found | Field allowlist only; NO rank/timestamp/null guard | **LEGACY_COMPAT** → target FORBIDDEN | **HIGH** |
| **W-CON-02** | `campaign_projection.py:46` | `CampaignProjectionAdapter.project()` | Explicit caller (test harness only in repo) | peEmailStatus (DRAFT_READY), peEmailCampaignName, peRecommendedApproach | EmailDraft + QualificationStatus | DIRECT PUT to Lead | **UNKNOWN** production reachability — only test callers found | Idempotent (same DRAFT_READY); NO rank/timestamp guard | **LEGACY_COMPAT** → target FORBIDDEN | **HIGH** |
| **W-CON-03** | `lifecycle.py:67` | `LifecycleSyncService.sync()` | Explicit invocation | 22 intelligence fields (explicit whitelist; NO peEmail*) | SyncContractPayload | DIRECT create/update | Explicit CLI / scheduler invocation | External ID dedup + field whitelist | **CANONICAL** (intelligence fields) | LOW |
| **W-CON-04** | `crm_score_projection.py:42` | `CRMScoreProjectionAdapter.project()` | Explicit caller | peOpportunityScoreV4, peScoreTier, peBestFirstProduct, peScoreRulesVersion | CanonicalScoreResult | DIRECT PUT to Lead | Explicit invocation | Field allowlist + validation | **CANONICAL** (score projection) | LOW |
| **W-DEP-01** | `phase3b06_provision_synthetic_lead.php:42` | Inline fixture | Deployment provisioning script | peEmailStatus=SENT, peLastEmailDate, peEmailCampaignName, peProposal* fields | Hardcoded fixture values | DIRECT create | One-time provisioning | N/A (seed data) | **FIXTURE** | LOW (dev only) |
| **W-DEP-02** | `phase3b07_provision_synthetic_records.php:109` | Inline fixture | Deployment provisioning script | peProposalEligibility, peProposalAction, peProposalSuggestedNextAction | Fixture definition array | DIRECT create | One-time provisioning | N/A (seed data) | **FIXTURE** | LOW (dev only) |
| **W-TEST-01** | `real_client.py:189` | `LocalEspoCRMClient.update_lead_campaign_projection()` | Test code only (ESPOCRM_TEST_ENV guard) | peEmailStatus, peEmailCampaignName, peRecommendedApproach | Caller-supplied dict | DIRECT PUT | Synthetic test only | ESPOCRM_TEST_ENV=true guard | **TEST_ONLY** | NONE |
| **W-TEST-02** | `real_client.py:283` | `LocalEspoCRMClient.update_record()` | Test code only (ESPOCRM_TEST_ENV guard) | Generic (any fields) | Caller-supplied dict | DIRECT PUT | Synthetic test only | ESPOCRM_TEST_ENV=true guard | **TEST_ONLY** | NONE |
| **W-TEST-03** | `email_lifecycle_sync.py:31` | `run_local_synthetic_email_lifecycle_sync()` | Manual test invocation | peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus | Hardcoded test sequence | Via EmailLifecycleSyncService | Manual CLI test run | ESPOCRM_TEST_ENV guard | **TEST_ONLY** | NONE |
| **W-TEST-04** | `test_espocrm_email_lifecycle.py:42` | Unit test | pytest/unittest | peEmailStatus (via mock client) | Test fixture | Via EmailLifecycleSyncService | Test suite | Mock client (no real CRM) | **TEST_ONLY** | NONE |

### Production-Reachable Writers Summary

| Category | Count | Writers |
|----------|-------|---------|
| CRM Canonical (projection) | 4 | W-CRM-01 through W-CRM-04 |
| CRM Canonical (intelligence) | 2 | W-CRM-05, W-CRM-06 |
| Connector Legacy Compat (email) | 2 | W-CON-01, W-CON-02 |
| Connector Canonical (non-email) | 2 | W-CON-03, W-CON-04 |
| Deployment Fixture | 2 | W-DEP-01, W-DEP-02 |
| Test Only | 4 | W-TEST-01 through W-TEST-04 |
| **TOTAL** | **16** | |

**Production-reachable writers that write peEmail*:** 6 (4 CRM canonical + 2 connector legacy)
**Production-reachable writers that write peProposal*:** 2 (1 CRM canonical + 1 deployment fixture)
**Conflict writers (write same field as another writer without coordination):** 2 (W-CON-01, W-CON-02)

---

## 3. C09/C10 Connector Writer Call Graphs

### W-CON-01: `EmailLifecycleSyncService.sync()`

```
File: chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py
Class: EmailLifecycleSyncService (line 69)
Method: sync(client, lead_id, update, opportunity_id) (line 72)

Call chain:
  Caller (UNKNOWN production path)
    → EmailLifecycleSyncService.sync(lead_id, update)
      → update.fields() → {peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus}
      → client.update_record("Lead", lead_id, fields)   ← DIRECT PATCH/PUT to Lead
      → [optional] client.update_record("Opportunity", opportunity_id, fields)

Fields written:
  - peEmailStatus: Any EmailLifecycleStatus value (NONE/DRAFT_READY/APPROVED/SENT/REPLIED/BOUNCED)
  - peLastEmailDate: UTC datetime string
  - peEmailCampaignName: campaign_reference string (1-255 chars)
  - peEmailReplyStatus: reply_state string (1-64 chars)

Data source: EmailLifecycleUpdate dataclass (caller-supplied)
Guards: Field allowlist only (4 fields). NO rank guard, NO timestamp guard,
        NO null-exclusion, NO terminal-state protection, NO changed-only filter.

Known callers (all test):
  - email_lifecycle_sync.py:62 (synthetic runtime test)
  - test_espocrm_email_lifecycle.py:42,65 (unit tests)
  - No production CLI, scheduler, or API entry point found in repository.

Current classification: LEGACY_COMPAT — frozen by C10 contract, retained in module
  exports but with no known production caller in this repository.
```

### W-CON-02: `CampaignProjectionAdapter.project()`

```
File: chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py
Class: CampaignProjectionAdapter (line 46)
Method: project(lead_id, email_draft, campaign_name) (line 52)

Call chain:
  Caller (UNKNOWN production path)
    → CampaignProjectionAdapter.project(lead_id, email_draft)
      → _projection_fields(email_draft, campaign_name)
        → {"peEmailStatus": "DRAFT_READY", "peEmailCampaignName": campaign_name,
           "peRecommendedApproach": approach_text}
      → client.update_lead_campaign_projection(lead_id, fields)  ← DIRECT PUT to Lead

Fields written:
  - peEmailStatus: Always "DRAFT_READY" (fixed value)
  - peEmailCampaignName: "C09 Draft Preparation" (default) or caller-supplied
  - peRecommendedApproach: Evidence-backed first touch text

Data source: EmailDraft + QualificationStatus (both caller-supplied)
Guards: Content validation (non-empty subject/body, valid evidence refs, valid
        campaign name). Field allowlist (3 fields). NO rank guard, NO timestamp
        guard, NO null-exclusion, NO terminal-state protection.

Known callers (all test):
  - test_phase3c09_campaign_projection.py:57,81 (unit tests)
  - test_phase3c09_outreach_runtime_acceptance.py:129 (acceptance test)
  - No production CLI, scheduler, or API entry point found in repository.

Current classification: LEGACY_COMPAT — frozen by C09 contract, retained in module
  exports but with no known production caller in this repository.
```

### Production Reachability Assessment for W-CON-01 and W-CON-02

**Finding: UNKNOWN — cannot confirm or deny production reachability from repository inspection alone.**

Evidence:
- Both are exported from `chitu_connector.espocrm_sync.__init__` (lines 12, 106)
- Both are importable Python modules
- No CLI entry point, scheduler config, cron job, or API endpoint in this repository invokes them
- The C10 Architecture Audit Report (PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md:412) states:
  > "There is no code path that syncs C10 execution results back to CRM peEmailStatus."
- These could be invoked by external systems, separate deployment repos, or manual operator actions not tracked in this repository

This does NOT mean they are safe to ignore. The code exists, is importable, and
if invoked would directly write to Lead without guards. The conservative
position is to treat them as **reachable until proven otherwise**.

---

## 4. Conflict Scenario Analysis

### Scenario 1: SENT degraded by legacy DRAFT_READY

**Setup:** SendExecution saved → W-CRM-03 projects `peEmailStatus=SENT`.
  Subsequently, W-CON-02 writes `peEmailStatus=DRAFT_READY`.

**Current behavior:** W-CON-02 has no rank guard. It unconditionally writes
  `peEmailStatus=DRAFT_READY` via PUT to Lead. The CRM-side SENT is overwritten
  with DRAFT_READY.

**Evidence:** `campaign_projection.py:91` — `"peEmailStatus": "DRAFT_READY"` is
  always written. No comparison with current Lead state. The
  `LeadCampaignProjectionClient` Protocol has no read capability.

**Severity:** **CRITICAL** — irrecoverable state degradation. SENT → DRAFT_READY
  is a loss of delivery confirmation.

**Reproducible:** Yes, if W-CON-02 is invoked after a SendExecution save.

**Recommended protection:** Add rank guard: refuse to write if current
  `peEmailStatus` rank > DRAFT_READY rank (10).

### Scenario 2: REPLIED overwritten by legacy SENT

**Setup:** ReplyEvent saved → W-CRM-04 projects `peEmailReplyStatus=REPLIED`,
  W-CRM-01 projects `peEmailStatus=REPLIED`. Subsequently, W-CON-01 writes
  `peEmailStatus=SENT`.

**Current behavior:** W-CON-01 writes `peEmailStatus=SENT` without checking
  current state. The CRM-side REPLIED (rank 70) is overwritten with SENT (rank 60).

**Evidence:** `email_lifecycle.py:86` — `client.update_record("Lead", lead_id, fields)`
  with no pre-read of current Lead state. The EmailLifecycleClient Protocol has
  only `update_record`, no read method.

**Severity:** **CRITICAL** — loss of reply state. A replied Lead appears as
  merely sent.

**Reproducible:** Yes, if W-CON-01 is invoked after a ReplyEvent save.

**Recommended protection:** Same as Scenario 1. Also, W-CRM-01 already has the
  reverse protection (SENT won't overwrite REPLIED/BOUNCED for EmailEvent),
  but W-CON-01 has no equivalent.

### Scenario 3: FAILED overwritten by legacy CONTACTED/DRAFT_READY

**Setup:** SendExecution saved with FAILED status → W-CRM-03 projects
  `peEmailStatus=FAILED` (rank 60). Subsequently, W-CON-02 writes
  `peEmailStatus=DRAFT_READY` (rank 10) or W-CON-01 writes APPROVED (rank 30).

**Current behavior:** Both connector writers would overwrite FAILED with
  lower-rank states. No guard exists.

**Severity:** **HIGH** — masks delivery failure. Operators would not see the
  FAILED state on the Lead.

**Reproducible:** Yes.

**Recommended protection:** Rank guard as in Scenario 1.

### Scenario 4: Null/missing fields clearing existing state

**Setup:** Old sync payload where `peEmailReplyStatus` or `peEmailCampaignName`
  is absent or empty. W-CON-01 writes the partial update.

**Current behavior:** `EmailLifecycleUpdate.fields()` at `email_lifecycle.py:43`
  always produces all 4 fields. A caller passing empty `reply_state` triggers
  `EmailLifecycleSyncError` (line 47-48). So null fields cannot be written
  through the standard path.

  However, `client.update_record()` is a generic method. A direct caller
  bypassing `EmailLifecycleUpdate` could send partial payloads.

**Severity:** **MEDIUM** — the standard path validates inputs, but the
  Protocol-based design means the actual HTTP client could send any body.

**Reproducible:** Only via bypass of EmailLifecycleUpdate.

**Recommended protection:** The field allowlist in `EmailLifecycleSyncService`
  already enforces exact field set. Keep this constraint.

### Scenario 5: Two processes with different timestamps

**Setup:** CRM hook writes `peLastEmailDate=2026-07-14T10:03:00` with
  `peEmailStatus=SENT`. Connector writes `peLastEmailDate=2026-07-14T10:01:00`
  with `peEmailStatus=APPROVED`.

**Current behavior:** W-CON-01 has no `isOlderThanLead` check.
  W-CRM-01/W-CRM-03 DO have `isOlderThanLead` (line 211 of the PHP service).

  Result: Connector writes an older timestamp over a newer one. The CRM-side
  timestamp guard protects CRM→CRM transitions but cannot protect against
  connector→CRM writes (connector bypasses the projection service).

**Severity:** **HIGH** — timestamp regression plus potential status downgrade.

**Reproducible:** Yes.

**Recommended protection:** W-CON-01 must read current `peLastEmailDate` before
  writing, and refuse if its timestamp is older.

### Scenario 6: C14.3 Result Adapter → historical lifecycle_sync conflict

**Setup:** C14.3 `SendExecutionResultAdapterService.apply()` writes
  `SendExecution.status=SENT` → hook → W-CRM-03 projects `peEmailStatus=SENT`.
  Historical `lifecycle_sync` (W-CON-03) runs with old cached data — but
  W-CON-03 does NOT write peEmail* fields (explicit whitelist excludes them).

**Current behavior:** W-CON-03 (`LifecycleSyncService`) has an explicit field
  whitelist at `lifecycle.py:128-155` that excludes peEmail* fields. This
  scenario is a **false alarm** — the intelligence lifecycle sync cannot
  overwrite email state.

  However, `email_lifecycle_sync.py` (W-TEST-03) uses `EmailLifecycleSyncService`
  (W-CON-01) which DOES write peEmail*. If invoked after C14.3 projection,
  conflict occurs as in Scenarios 1-3.

**Severity:** **LOW** for W-CON-03 (no peEmail writes). **HIGH** if W-TEST-03
  is mistaken for a production path and run against real CRM.

**Reproducible:** W-CON-03: not reproducible (whitelist prevents it).
  W-CON-01: yes, if invoked.

**Recommended protection:** Ensure `email_lifecycle_sync.py` remains behind
  `ESPOCRM_TEST_ENV=true` guard.

---

## 5. Historical Contract Alignment

### C09 Contract

| Document | Statement | Assessment |
|----------|-----------|------------|
| PHASE3C09_3_CAMPAIGN_PROJECTION_REPORT.md | `CampaignProjectionAdapter` projects DRAFT_READY metadata to existing Lead | **Frozen implementation**, not a contractual requirement to write peEmailStatus directly |
| PHASE3C10_FREEZE.md | C09.3: "Limited draft-preparation projection contract for an existing Lead" | Freezes the **contract interface**, not the **write mechanism** |

**Verdict:** C09 freezes the `CampaignProjectionAdapter` interface and its 3-field
  allowlist (`peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach`).
  It does NOT mandate that this adapter bypass CRM projection authority.
  The projection contract can be honored by routing through a controlled CRM
  endpoint while preserving the same 3-field payload.

### C10 Contract

| Document | Statement | Assessment |
|----------|-----------|------------|
| PHASE3C10_FREEZE.md | Freezes C10.0-A through C10.4 contracts, all in-memory | Freezes in-memory **orchestration contracts**, not CRM write behavior |
| PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md:412 | "There is no code path that syncs C10 execution results back to CRM peEmailStatus" | C10 execution layer is **disconnected** from CRM display layer |
| PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md:385 | `EmailLifecycleSyncService` described as separate "CRM Display Layer" | Acknowledged as a distinct system from C10 execution |

**Verdict:** C10 freezes the **execution orchestration** (SendRequest, approval,
  provider adapter, reply tracking). The `EmailLifecycleSyncService` is a
  separate **display layer** that happens to share conceptual state names.
  It is not part of the frozen C10 execution contract. The freeze does not
  prevent routing display updates through the CRM projection authority.

### C11 Contract

| Document | Statement | Assessment |
|----------|-----------|------------|
| PHASE3C11_0_PERSISTENCE_ARCHITECTURE_APPROVAL.md:98 | "EmailLifecycleSyncService and C10 execution are disconnected systems" — RISK-2 HIGH | Already identified as a risk |
| PHASE_G06_C11_FOLLOWUP_BOUNDARY_AUDIT.md:172 | "Writer B (EmailLifecycleSyncService) MUST be deprecated" | Explicit deprecation directive already exists |
| PHASE_G06_C11_FOLLOWUP_BOUNDARY_AUDIT.md:569 | "4 writers could conflict, causing state oscillation" — H1 risk | Multiple-writer risk already documented |

**Verdict:** C11 already identified the multi-writer problem and recommended
  deprecation of `EmailLifecycleSyncService` for email projection. This audit
  confirms and extends that finding.

### C12/C13 Contract

Neither C12 (Provider adapter) nor C13 (Queue/Worker) contracts involve Lead
email field writes. **No alignment issue.**

### C14.3 Contract

| Document | Statement | Assessment |
|----------|-----------|------------|
| PHASE3C14_3_1A_WRITER_INVENTORY.md:21-22 | W-CON-01 and W-CON-02 "frozen and excluded from this step" | Deferred, not resolved |
| PHASE3C14_3_1A_STATE_OWNERSHIP_BOUNDARY_REPORT.md:118 | "Connector convergence remains deferred" — Risk #1 | Explicitly flagged as remaining work |
| PHASE3C14_3_FINAL_FREEZE_ACCEPTANCE_REPORT.md:5 | FREEZE_APPROVED_WITH_RISKS | The freeze acknowledged the deferred connector risk |

**Verdict:** C14.3 explicitly deferred connector convergence to a later phase
  (this one — C14.4A). The freeze was approved WITH the understanding that
  connector writers would be addressed.

### Contract Alignment Summary

| Contract | Requires connector to write peEmail*? | Would break if connector stops? |
|----------|---------------------------------------|-------------------------------|
| C09 | **No** — freezes projection interface, not write mechanism | **No** — can route through CRM endpoint |
| C10 | **No** — freezes execution orchestration, not CRM display | **No** — display layer is separate |
| C11 | **No** — explicitly recommends deprecation | **No** — C11 projection service is the target |
| C12 | **No** — provider-only contract | **No** |
| C13 | **No** — queue/worker contract | **No** |
| C14.3 | **No** — deferred convergence | **No** — C14.4A is the resolution phase |

**Conclusion:** No frozen contract requires the connector to directly write
  `peEmail*` fields on Lead. All contracts are compatible with routing through
  the CRM-side projection authority.

---

## 6. Target State Ownership Model

### Principle

```
SendExecution / EmailEvent / ReplyEvent → source records (facts)
EmailLifecycleProjectionService → sole projection owner of Lead.peEmail*
ChituSyncService → owner of Lead.peProposal* and intelligence fields
Connector → submits facts or calls controlled CRM services; never decides Lead email terminal state
```

### Target Ownership Matrix

| Lead Field | Exclusive Owner | Allowed Contributors | Forbidden Writers |
|------------|----------------|---------------------|-------------------|
| peEmailStatus | EmailLifecycleProjectionService | SendExecution hook, DraftApproval hook, EmailEvent hook, ReplyEvent hook (all via projection service) | EmailLifecycleSyncService, CampaignProjectionAdapter, any connector direct PATCH |
| peLastEmailDate | EmailLifecycleProjectionService | Same as above | EmailLifecycleSyncService, any connector direct PATCH |
| peEmailCampaignName | EmailLifecycleProjectionService | EmailEvent hook (via projection service) | CampaignProjectionAdapter, any connector direct PATCH |
| peEmailReplyStatus | EmailLifecycleProjectionService | ReplyEvent hook, EmailEvent hook (via projection service) | EmailLifecycleSyncService, any connector direct PATCH |
| peProposalProductFitScore | ChituSyncService | Connector intelligence sync | Any hook or non-intelligence writer |
| peProposalCooperationType | ChituSyncService | Connector intelligence sync | Any hook or non-intelligence writer |
| peProposalSuggestedNextAction | ChituSyncService | Connector intelligence sync | Any hook or non-intelligence writer |
| peProposalEligibility | ChituSyncService | Connector intelligence sync | Any hook or non-intelligence writer |
| peProposalAction | ChituSyncService | Connector intelligence sync | Any hook or non-intelligence writer |
| peRecommendedApproach | Shared | ChituSyncService (intelligence), CampaignProjectionAdapter (draft), EmailEvent hook (campaign context) | None — multi-source with lower criticality |
| peOpportunityScoreV4 | LifecycleSyncService / ChituSyncService / CRMScoreProjectionAdapter | All three intelligence paths | Any email lifecycle writer |
| peBestFirstProduct | LifecycleSyncService / ChituSyncService / CRMScoreProjectionAdapter | All three intelligence paths | Any email lifecycle writer |

### Fields Where Connector Can Continue Writing Directly

These non-email intelligence fields can continue to be written by the connector
without routing through CRM projection:

- peOpportunityScoreV4, peScoreTier, peBestFirstProduct, peConfidence
- peEvidenceCoverage, peQualificationStatus, peEngineVersion, peScoreRulesVersion
- peSyncStatus, peResearchStatus, peSourceSystem, peCandidateId
- peLastSyncAt, peResearchSummary, peKeyEvidence
- peProposalProductFitScore, peProposalCooperationType, peProposalSuggestedNextAction
- peProposalEligibility, peProposalAction
- pePriorityLevel, peLastResearchedAt, peSourceType, peDiscoverySource
- addressCountry, website, name

The connector's `LifecycleSyncService` (W-CON-03) and `CRMScoreProjectionAdapter`
(W-CON-04) are canonical writers for their respective intelligence fields and
should NOT be modified by this convergence.

---

## 7. Option Comparison

### Option A — Remove Legacy Email Summary Writes

**Description:** W-CON-01 (`EmailLifecycleSyncService`) and W-CON-02
(`CampaignProjectionAdapter`) stop writing `peEmail*` fields. Connector
continues to sync non-email intelligence fields directly.

**Scope of change:**
- `email_lifecycle.py`: Remove the 4-field email summary from `EmailLifecycleUpdate.fields()`; or deprecate the entire service if no non-email use remains
- `campaign_projection.py`: Remove `peEmailStatus` and `peEmailCampaignName` from `_PROJECTABLE_FIELDS`; retain `peRecommendedApproach` as non-email guidance
- `real_client.py`: Remove `update_lead_campaign_projection()` or narrow its allowlist
- Tests: Update to assert email fields are NOT written; add forbidden-writer detection

**Advantages:**
- Cleanest single-writer principle
- Zero risk of connector degrading CRM-projected email state
- Minimal code change
- Aligns with C11/G06 deprecation directive

**Risks:**
- If an external system (outside this repo) invokes W-CON-01 in production, email state updates stop silently
- `peRecommendedApproach` currently tied to campaign projection — needs separate writer
- Test-only `email_lifecycle_sync.py` must be updated or removed

**Rollback:** Restore removed fields to allowlists. No data migration needed
  (CRM projection service already owns the fields).

### Option B — Route Legacy Writer Through Controlled CRM Projection Endpoint

**Description:** Connector stops directly PATCHing Lead email fields. Instead,
  creates an EmailEvent or calls a new CRM API endpoint that enters the
  projection pipeline through `EmailLifecycleProjectionService`.

**Scope of change:**
- New CRM API endpoint or service method that accepts connector email lifecycle updates
- Connector W-CON-01 and W-CON-02 refactored to call the new endpoint
- New EmailEvent or equivalent source record type for connector-originated events
- Authentication/authorization for the new endpoint

**Advantages:**
- All email state flows through one ranked, timestamp-gated pipeline
- Preserves connector's ability to initiate email state transitions
- Clean audit trail via source records

**Risks:**
- **Expands runtime boundary** — new API endpoint is attack surface
- **Overlaps with C14.3 Result Adapter** — existing SendExecution→projection path already covers the post-send flow
- Requires CRM extension deployment
- Higher implementation cost than Option A or C

### Option C — Guarded Compatibility Writer (Recommended)

**Description:** Retain W-CON-01 and W-CON-02 but add:
1. **Rank guard:** Read current `peEmailStatus` before write; refuse if proposed rank < current rank
2. **Timestamp guard:** Read current `peLastEmailDate` before write; refuse if proposed time < current time
3. **Null exclusion:** Never write null/empty to fields that already have values
4. **Terminal-state protection:** Never overwrite REPLIED or BOUNCED with lower-rank states
5. **Deprecation warning:** Log warning on each invocation indicating this path is deprecated

**Scope of change:**
- `email_lifecycle.py`: Add `EmailLifecycleClient` read capability; add guard logic before `update_record`
- `campaign_projection.py`: Add `LeadCampaignProjectionClient` read capability; add guard logic
- `real_client.py`: Add read method to protocol implementations
- Tests: Add guard verification tests; add rank/timestamp conflict tests

**Advantages:**
- **Immediate risk reduction** — prevents state degradation without removing capability
- Backward compatible — existing callers continue to work but safely
- No new CRM endpoint needed
- Buys time for Option A verification

**Risks:**
- **Defers technical debt** — guards are a bandage, not a cure
- **Still violates single-writer principle** — two systems can write same field (even if safely)
- Guards only work if the CRM is queried before write (adds latency)
- Does not solve the fundamental architectural issue

---

## 8. Recommended Option

**Recommendation: Option C → Option A phased approach**

### Phase 1 (C14.4A Implementation — immediate):

**Option C — Guarded Compatibility Writer**

Add rank guards, timestamp guards, null exclusion, and terminal-state protection
to W-CON-01 and W-CON-02. This provides immediate safety without breaking any
unknown external callers.

### Phase 2 (C14.4B or later — after verification):

**Option A — Remove Legacy Email Summary Writes**

Once production call-site verification confirms no external system depends on
connector-originated peEmail* writes (or all callers have been migrated), remove
the email summary write capability from the connector entirely.

### Rationale:

1. Option C can be implemented **immediately** with low risk — pure defensive
   additions to existing code
2. Option C does not require CRM extension changes, new endpoints, or deployment
   coordination
3. The C14.3 FREEZE_APPROVED_WITH_RISKS explicitly defers connector convergence —
   a guarded approach respects that freeze while reducing risk
4. Option A is the correct end state but requires production call-site verification
   that we cannot perform in this read-only audit
5. Option B adds unnecessary complexity; the existing C14.3 result→projection
   pipeline already handles the post-send flow correctly

---

## 9. Exact Implementation Scope (C14.4A Implementation)

### Allowed Changes

#### File: `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py`

1. Add `read_record` method to `EmailLifecycleClient` Protocol
2. Add rank map constant (`_STATUS_RANK`) matching CRM-side `STATUS_RANK`
3. Add `_TERMINAL_STATES = frozenset({"REPLIED", "BOUNCED"})`
4. Before `update_record` in `sync()`:
   - Read current `peEmailStatus` and `peLastEmailDate` from Lead
   - Refuse write if proposed status rank < current status rank
   - Refuse write if proposed timestamp < current timestamp
   - Refuse write if current state is terminal and proposed state is lower rank
   - Skip fields that would set null/empty over existing values
5. Add deprecation warning log on each invocation
6. Add `is_production_safe()` class method returning `False`

#### File: `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py`

1. Add `read_lead` method to `LeadCampaignProjectionClient` Protocol
2. Before `update_lead_campaign_projection` in `project()`:
   - Read current `peEmailStatus` from Lead
   - Refuse write if current rank > DRAFT_READY rank (10)
   - Skip `peEmailStatus` field if current state is already >= DRAFT_READY
3. Add deprecation warning log on each invocation
4. Add `is_production_safe()` class method returning `False`

#### File: `chitu-connector/chitu_connector/espocrm_sync/real_client.py`

1. Add `read_lead` or equivalent method to support guard reads
2. Update `update_lead_campaign_projection` to support the expanded protocol

#### Files: Tests

1. `tests/test_espocrm_email_lifecycle.py`: Add guard tests
2. `tests/test_phase3c09_campaign_projection.py`: Add guard tests
3. New: `tests/test_phase3c14_4a_writer_guards.py`: Comprehensive guard verification
4. New: `tests/test_phase3c14_4a_forbidden_writer_detection.py`: Static analysis

#### Files: Documentation

1. `docs/PHASE3C14_4A_GLOBAL_WRITER_CONVERGENCE_AUDIT.md` (this document)
2. Update `docs/PHASE3C14_3_1A_WRITER_INVENTORY.md` to note guard addition
3. Update `docs/PHASE3C10_FREEZE.md` to note guarded-deprecation status

### Forbidden Changes (C14.4A Boundary)

The following areas MUST NOT be modified:

- **Queue durability** (C13 queue contract)
- **Worker recovery** (C13 worker execution)
- **Result inbox** (C14.3 result adapter)
- **Provider/Brevo** (C12 provider contract, Brevo adapter, Brevo HTTP)
- **Retry policy** (C13 worker retry, failure classification)
- **CRM schema/entity** (Lead.json entityDefs, field definitions)
- **UI** (layouts, labels, dashboards)
- **Automatic sending** (any code path from DRAFT_READY to actual email send)
- **C14.3 frozen result/bridge contract** (SendExecutionBridgeResult, SendExecutionBridgeAdapter)
- **Non-email field connector refactoring** (intelligence sync, score projection, evidence persistence)
- **Database** (no schema changes, no migrations)
- **Runtime** (no runtime behavior change except the guards themselves)
- **Git** (no commits, no branch changes)
- **Real data** (no real CRM data access or modification)

---

## 10. Test Plan (for C14.4A Implementation)

### 10.1 Connector Cannot Directly Write peEmailStatus Without Guards

- Test that `EmailLifecycleSyncService.sync()` reads current state before writing
- Test that write is refused when proposed rank < current rank
- Test that write is refused when proposed timestamp < current timestamp

### 10.2 SENT Not Degraded by Legacy Summary

- Set Lead.peEmailStatus=SENT via mock
- Attempt W-CON-01 write with APPROVED
- Assert Lead.peEmailStatus remains SENT
- Assert guard rejection reason code

### 10.3 REPLIED Not Overwritten by SENT

- Set Lead.peEmailStatus=REPLIED via mock
- Attempt W-CON-01 write with SENT
- Assert Lead.peEmailStatus remains REPLIED

### 10.4 Null/Missing Fields Do Not Clear Summary

- Set Lead.peEmailCampaignName="Existing Campaign"
- Attempt W-CON-01 write with empty campaign_reference (should fail validation)
- Assert existing campaign name preserved

### 10.5 Non-Email Sync Still Functional

- Run existing intelligence sync tests (W-CON-03, W-CON-04)
- Assert all non-email fields sync correctly
- Assert no regression in LifecycleSyncService or CRMScoreProjectionAdapter

### 10.6 C14.3 Projection Tests Maintained

- Run `tests/test_phase3c14_3_1a_state_ownership.py`
- Run `tests/test_phase3c14_3_1c_result_adapter.py`
- Run `tests/test_phase3c14_3_1d_failure_projection_hardening.py`
- Assert all pass unchanged

### 10.7 C09/C10 Compatibility Tests

- Run `tests/test_phase3c09_campaign_projection.py` — update assertions for
  guard behavior (writes may now be SKIPPED instead of PROJECTED)
- Run `tests/test_espocrm_email_lifecycle.py` — update for guard behavior
- Run `tests/test_phase3c09_outreach_runtime_acceptance.py`

### 10.8 Full Connector Regression

```bash
python -m unittest discover -s chitu-connector/tests -p "test_*.py"
```
Target: 100% pass rate (updated for guard behavior)

### 10.9 Extension Lifecycle Regression

```bash
python -m unittest discover -s crm-extension/tests -p "test_*.py"
```
Target: 100% pass rate (no changes expected)

### 10.10 Static Forbidden-Writer Detection

- Scan all Python files for `peEmailStatus` or `peEmailReplyStatus` in write
  contexts outside the guarded services
- Scan all PHP files for direct `$lead->set('peEmail...')` outside
  `EmailLifecycleProjectionService.php`
- Assert no new forbidden writers introduced
- Assert existing guarded writers have guard logic present

---

## 11. Risks and Rollback

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Unknown external caller breaks when guarded write is refused | Low (no known production callers) | Medium (silent email state freeze for that path) | Guards return explicit status codes; log deprecation warnings |
| Guard read-before-write adds latency | Low (guards only add 1 CRM API call) | Low | Async/background where possible |
| Guard logic differs from CRM-side rank map | Medium | High (inconsistent behavior) | Extract rank map to shared constant; cross-test |
| Test-only paths break requiring test rewrite | High | Low | Accept test updates as expected scope |

### Rollback Plan

1. Guards are purely additive — revert the changed files to pre-C14.4A state
2. No database migration, schema change, or CRM entity change to unwind
3. No deployment coordination needed for rollback
4. Tests that were updated for guard behavior would need re-reverting

---

## 12. Final Recommendation

### VERDICT: READY_FOR_IMPLEMENTATION

- **Global writer count:** 16
- **Production-reachable writers:** 12 (including deployment fixtures)
- **Conflict writers (write same peEmail* fields without coordination):** 2
- **Recommended option:** Option C (Guarded Compatibility Writer) → Option A (Remove Legacy Email Writes)
- **Highest risk:** W-CON-01 (`EmailLifecycleSyncService`) can overwrite REPLIED/BOUNCED/SENT with lower-rank states like APPROVED or DRAFT_READY because it has zero guards
- **Report path:** `docs/PHASE3C14_4A_GLOBAL_WRITER_CONVERGENCE_AUDIT.md`
- **This audit did NOT modify any code, database, runtime, Git, or real data**
- **Next step:** C14.4A Implementation — add rank/timestamp/null/terminal guards to W-CON-01 and W-CON-02
- **Recommended tool:** Claude Code + DeepSeek V4 Pro API
- **Recommended model for implementation:** Claude Opus 4.8 (High reasoning effort)

### Post-Implementation Verification

After guard implementation:

1. Verify no `peEmail*` write in connector bypasses the guard
2. Run full test suite (connector + extension + regression)
3. Static scan for forbidden direct writers
4. Document remaining UNKNOWN production reachability and plan call-site discovery
5. Schedule C14.4B for production call-site verification and Option A transition
