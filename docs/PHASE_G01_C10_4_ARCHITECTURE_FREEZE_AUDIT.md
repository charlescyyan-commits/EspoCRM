# Phase G01 — Phase3C10.4 Architecture Freeze Audit

**Date:** 2026-07-14
**Audit Type:** Read-only architecture freeze audit
**Scope:** Full codebase (crm-extension/, chitu-connector/, deployment/)
**Status:** **CONDITIONAL GO** — 3 BLOCKERs, 11 WARNINGs, 15 PASS items

---

# Executive Summary

The Phase3C10.4 architecture is **structurally sound** with correct boundary enforcement, well-defined state machines (at the Python connector level), and proper human-approval gating. The core architectural decisions — Engine→CRM sync direction, NO_AUTOMATIC_OPPORTUNITY, pe* projection-only fields, immutable approval state machines — are correctly implemented and verified.

However, **3 BLOCKERs** must be resolved before freeze:

1. **PHP `syncEvidence()` maps `peEvidenceType` from `claim_type`** — should be `evidence_type` (data corruption in production)
2. **PHP `syncEvidence()` has zero dedup** — every call creates duplicate ResearchEvidence records
3. **Python dedup adapter is never called in production** — correct code exists but is bypassed

These BLOCKERs affect evidence data quality, not system safety or architectural boundaries. The approval gate, send execution controls, and CRM projection contracts are all intact.

**11 WARNINGs** cover: hardcoded test credentials, synthetic data scripts, debug scripts, missing SHA256 sidecars, stale version references, no git tags, duplicate metadata (Resources/ vs files/), empty skeleton directories, unclean working tree, accumulated test artifacts, and missing CRM-level state machine enforcement (mitigated by Python connector guards).

---

# PASS — Architecture Boundaries Verified

## PASS-1: System Boundary Correctness

**Verdict: PASS**

EspoCRM remains a **sales operation system / customer workflow system** and is NOT an AI scoring engine, research engine, or sending engine.

Evidence:
- `CLAUDE.md` explicitly forbids modifying Chitu scoring, AI research, email-generation, or unrelated Chitu application code
- All AI/scoring/research/sending logic lives in the external Chitu Intelligence Engine
- The chitu-connector imports only `chitu_connector` and vendored stable interfaces
- CRM extension provides projection entities (ResearchEvidence, SalesFeedback, LearningSignal), not AI capabilities

```
External Intelligence Engine (search/research/scoring/AI)
        |
        |  Sync Contract V1 (one-way push)
        |
Chitu Connector (auth/validation/mapping/idempotent transport)
        |
        |  EspoCRM REST API
        |
EspoCRM Prospecting Extension (projection/evidence/feedback/dashboards)
        |
        |
CRM Sales Operations (human judgment/stages/follow-up/tasks/outcomes)
```

## PASS-2: Sync Direction — Engine → CRM

**Verdict: PASS**

The sync is overwhelmingly **Engine (Chitu) → CRM (EspoCRM)**. All write paths push intelligence into CRM:

| Path | Module | Direction |
|------|--------|-----------|
| Lead sync | `connector_api.py` → `ChituSyncService::syncLead()` | Engine → CRM |
| Evidence sync | `connector_api.py` → `ChituSyncService::syncEvidence()` | Engine → CRM |
| Opportunity proposal | `connector_api.py` → `ChituSyncService::syncOpportunityProposal()` | Engine → CRM |
| Email events | `brevo_api.py` → Brevo endpoint | Engine → CRM |
| Feedback signals | `feedback_api.py` → Feedback endpoint | Engine → CRM |
| Campaign projection | `campaign_projection.py` | Engine → CRM |
| Score projection | `crm_score_projection.py` | Engine → CRM |

The **only reverse path** is `feedback_signal_export.py` — a **read-only pull** of LearningSignal records from CRM for Chitu model improvement. This is NOT reverse control; it exports CRM-side signals back to Chitu for learning.

**No CRM → AI reverse control exists.**

## PASS-3: pe* Fields — External Intelligence Projection

**Verdict: PASS**

All `pe*` fields on the Lead entity are clearly marked as external intelligence projection:

- `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct` — scoring projection
- `peResearchStatus`, `peLastResearchedAt`, `peResearchSummary` — research status
- `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName` — email projection
- `peSourceSystem` defaults to "Chitu Intelligence"
- `peProposalAction` defaults to "NO_AUTOMATIC_OPPORTUNITY"
- `peConfidence`, `peEvidenceCoverage` — quality metadata
- `peEngineVersion`, `peScoreRulesVersion` — provenance

These fields are **never confused with native CRM sales fields** (status, stage, amount, assignedUser). The `lifecycle.py` module enforces a `_FORBIDDEN_SALES_FIELDS` blocklist preventing Chitu from writing CRM-owned fields.

Subset allowlists for targeted projection (not full sync):
- `crm_score_projection.py`: only `{peOpportunityScoreV4, peScoreTier, peBestFirstProduct, peScoreRulesVersion}`
- `campaign_projection.py`: only `{peEmailStatus, peEmailCampaignName, peRecommendedApproach}`
- `email_lifecycle.py`: only `{peEmailStatus, peLastEmailDate, peEmailCampaignName, peEmailReplyStatus}`

## PASS-4: NO_AUTOMATIC_OPPORTUNITY Enforced

**Verdict: PASS**

Five independent enforcement mechanisms:

1. **`_FORBIDDEN_SALES_FIELDS` blocklist** (`lifecycle.py:54-63`): Blocks writes to `{assignedUserId, assignedUserName, status, stage, amount, amountCurrency, closeDate, probability, teamsIds}` — verified by `_assert_no_sales_fields()` on every write.

2. **No Opportunity creation path**: `LifecycleSyncService.sync()` only creates/updates Leads. Account, Contact, and Opportunity are only updated (not created) after native CRM Lead conversion.

3. **Opportunity writes are restricted**: Only `peProductInterest` is written to Opportunities (`lifecycle.py:168-174`). All sales fields remain CRM-owned.

4. **PHP endpoint default**: `ChituSyncService::syncOpportunityProposal()` sets `peProposalAction = 'NO_AUTOMATIC_OPPORTUNITY'` (line 103) and the response includes `'action' => 'NO_AUTOMATIC_OPPORTUNITY'`.

5. **Integration test verified**: Synthetic lifecycle sync tests confirm Opportunity `stage`, `amount`, and `closeDate` remain unchanged after sync.

## PASS-5: Approval Flow State Machine

**Verdict: PASS**

The `human_approval.py` state machine is correctly implemented:

```
DRAFT_READY → PENDING_REVIEW → APPROVED → READY_TO_SEND
                              → REJECTED (terminal)
```

Allowed transitions (line 224-230):
```python
DRAFT_READY:     {PENDING_REVIEW}
PENDING_REVIEW:  {APPROVED, REJECTED}
APPROVED:        {READY_TO_SEND}
REJECTED:        {}  # terminal
READY_TO_SEND:   {}  # terminal
```

Verification:
- **Transitions are explicit**: Each state change goes through `_transition()` which validates against `_ALLOWED_TRANSITIONS`
- **Illegal jumps blocked**: `ValueError("invalid approval transition")` raised for any disallowed jump
- **REJECTED is terminal**: No path from REJECTED to any other state — a new draft identity is required
- **Human reviewer required**: `approve()` and `reject()` require `reviewer_id` (validated by `_require_identifier`)
- **Immutable audit trail**: Every transition appends an `ApprovalAuditTrace` record

## PASS-6: Send Execution State Machine

**Verdict: PASS**

The `send_execution.py` state machine is correctly implemented:

```
READY_TO_SEND → SUBMITTED → PROCESSING → SENT
                                        → FAILED
```

Allowed transitions (line 269-275):
```python
READY_TO_SEND:  {SUBMITTED}
SUBMITTED:      {PROCESSING}
PROCESSING:     {SENT, FAILED}
SENT:           {}  # terminal
FAILED:         {}  # terminal
```

Verification:
- **Transitions are explicit**: `InMemorySendExecutionRegistry.transition()` enforces allowed transitions
- **Illegal jumps blocked**: `ValueError("invalid execution transition")` raised
- **Duplicate execution prevented**: `ControlledSendExecutionService.execute()` checks for existing execution by `send_request_id` and returns `DUPLICATE_EXECUTION`
- **Draft double-send prevented**: `DRAFT_ALREADY_SENT` returned if any execution for the approval is already SENT
- **In-progress guard**: `EXECUTION_IN_PROGRESS` returned if any execution is READY_TO_SEND/SUBMITTED/PROCESSING

## PASS-7: Human Approval Cannot Be Bypassed

**Verdict: PASS**

`ControlledSendExecutionService.execute()` enforces a mandatory approval check:

1. Requires `approval.status is ApprovalStatus.READY_TO_SEND` (line 221) — returns `APPROVAL_NOT_READY` otherwise
2. Validation of all inputs before any side effect (line 210)
3. Requires valid `approval_id` resolving to an existing approval (line 218-220)
4. Each execution records the full audit trace (`SendExecutionAuditTrace`)

There is **no code path** that creates a send execution without first checking approval status. The approval registry is the single source of truth for the READY_TO_SEND gate.

## PASS-8: Send Idempotency

**Verdict: PASS**

The `send_idempotency.py` module provides:

1. **Stable idempotency keys**: `generate_send_idempotency_key()` hashes `(version, draft_id, lead_id, send_request_id, provider_name)` — `created_at` is deliberately excluded so replay produces the same key

2. **Send attempt state machine**: `CREATED → READY → PROCESSING → SENT/FAILED` with CANCELLED as an exit from CREATED/READY

3. **Duplicate reservation**: `InMemorySendIdempotencyRegistry.reserve()` returns `EXISTING` for already-reserved requests

4. **Request validation**: `validate_send_request()` verifies all fields and key consistency

## PASS-9: Evidence Identity Contract (Python Adapter)

**Verdict: PASS (Python adapter)**

The `evidence_identity_key()` in `research_evidence_persistence.py:212-233` correctly implements:

```
SHA-256({
    "version": "c10-research-evidence-identity-v1",
    "lead_id": lead_id.strip(),
    "source_url": _canonical_source_url(source_url),  # scheme/host normalized
    "claim_type": _normalize_text(claim_type).lower(),
    "claim_hash": sha256(_normalize_text(claim).encode("utf-8")).hexdigest()
})
```

This is exactly: **leadId + canonical source URL + normalized claimType + claim SHA-256**

Verification:
- URL canonicalization handles HTTPS/HTTP, default ports, trailing slashes, query param ordering
- Claim normalization compresses whitespace
- Deterministic identity tested with URL and whitespace variants
- **snapshotHash is intentionally excluded** from identity — confirmed by docstring: "The batch snapshot hash is intentionally excluded: it describes a complete extraction run and changes when unrelated evidence is added or removed"

**However, see BLOCKER-3: this correct adapter is never called in production.**

## PASS-10: Snapshot Hash Scope

**Verdict: PASS**

`snapshotHash` (stored as `peSnapshotHash` in CRM) is used **only** for:

1. Batch-level quick-path lookup (`find_research_evidence_for_snapshot`) — checking if the entire batch was already persisted
2. Version/snapshot attribution on the CRM record
3. A non-unique database index (not a unique constraint)

It is **never used** for:
- Evidence identity matching
- Deduplication decisions
- Unique constraint enforcement

This is architecturally correct — `snapshotHash` describes a batch extraction run and changes when unrelated evidence is added/removed. Using it for identity would incorrectly block legitimate evidence updates in different snapshots.

## PASS-11: Extension Module Structure

**Verdict: PASS**

The Prospecting module is the single source of truth for all custom entities:

- All 9 entities (Lead extension, ResearchEvidence, SearchStrategy, SearchJob, ProspectPool, SalesFeedback, LearningSignal, EmailEvent, Opportunity extension) are defined under `files/custom/Espo/Modules/Prospecting/`
- The old `custom/Espo/Custom/` overlay was removed (Phase3A25 single-source migration)
- No duplicate PHP classmap entries
- All controllers, entities, services, and APIs are in the Prospecting namespace
- The `Resources/` directory at extension root contains design-surface copies (reference only, not packaged)

## PASS-12: ACL and Scope Configuration

**Verdict: PASS**

- 7 entity-specific ACL definitions exist under `Resources/acl/` and `files/.../metadata/aclDefs/`
- All entities have proper scope configuration with `module: "Prospecting"`
- Role-based access control (Admin, Integration Bot, Sales, Manager, Research) is provisioned through deployment scripts
- API endpoints perform ACL checks (`$this->acl->check()`, `assertScope()`) before entity operations
- Dashboard ACL compatibility verified (Phase3B07.2)

## PASS-13: i18n Coverage

**Verdict: PASS**

- Complete English (`en_US`) translations for all 9 entities + Global + dashboards
- Complete Chinese (`zh_CN`) translations for all 9 entities + Global + dashboards
- All pe* fields have `tooltip: true` for user guidance
- Status enums have style mappings (color coding)

## PASS-14: Test Coverage for C10 Capabilities

**Verdict: PASS**

Dedicated test files cover all C10 capabilities:

| Test File | C10 Capability | Lines |
|-----------|---------------|-------|
| `test_phase3c10_1_human_approval_model.py` | Approval state machine | ✓ |
| `test_phase3c10_2_send_provider_adapter.py` | Provider adapter | ✓ |
| `test_phase3c10_3_controlled_send_execution.py` | Controlled execution | ✓ |
| `test_phase3c10_4_reply_tracking_boundary.py` | Reply tracking | ✓ |
| `test_phase3c10_evidence_dedup_hardening.py` | Evidence dedup | ✓ |
| `test_phase3c10_send_idempotency_contract.py` | Send idempotency | ✓ |

All tests use in-memory registries and fake providers — no network, no CRM, no side effects.

## PASS-15: Deployment Infrastructure

**Verdict: PASS**

- `scripts/build_release_package.ps1` builds ZIP from `manifest.json` + `files/`
- 18 versioned releases available for rollback (v1.2.0 through v1.9.5)
- SHA256 sidecars present and verified for v1.6.0 through v1.9.0 (see WARNING-4)
- Provisioning scripts for role/user/ACL setup (see WARNING-1)
- Cleanup scripts paired with all provisioning scripts

---

# WARNING — Non-Blocking Issues

## WARNING-1: Hardcoded Test Credentials in Provisioning Scripts

**Severity: MEDIUM**
**Location:** `deployment/provisioning/*.php`

27 provisioning scripts contain hardcoded test user credentials:

| User | Password/Key | Scripts |
|------|-------------|---------|
| `sales_test` | `SalesTest#2026` | `phase3a33`, `phase3b06` |
| `manager_test` | `ManagerTest#2026` | `phase3a33` |
| `research_test` | `ResearchTest#2026` | `phase3b01`, `phase3b02`, `phase3b06` |
| `phase3b03_connector_test` | `phase3b03-local-test-api-key` | `phase3b03` |
| `phase3b04` (feedback test) | `phase3b04-local-test-api-key` | `phase3b04` |
| `phase3b05a` (brevo test) | `phase3b05a-local-brevo-test-key` | `phase3b05a` |
| `phase3b06_1_connector_test` | `phase3b06_1-local-test-api-key` | `phase3b06_1` |
| `phase3b07` (validation) | `phase3b07-local-test-api-key` | `phase3b07` |

Additionally, passwords are echoed to console in clear text (e.g., `phase3a33_provision_roles.php:174`).

**Risk**: Accidental execution against production would create test users with known credentials.

**Mitigation**: README.md warns these scripts must not be executed without approved target. The scripts themselves are idempotent and have paired cleanup scripts.

## WARNING-2: Synthetic Data Creation Scripts

**Severity: LOW**
**Location:** `deployment/provisioning/phase3b06_provision_synthetic_lead.php`, `phase3b07_provision_synthetic_records.php`

Scripts create synthetic Leads with `.example` domain emails. These are explicitly for validation and have cleanup scripts. No real customer data is imported.

## WARNING-3: Debug Scripts in temp/ Directory

**Severity: LOW**
**Location:** `temp/_debug_formula.php`, `temp/_verify_formula.php`, `temp/_verify_metadata.php`, `temp/check_clientdefs.php`

Four PHP debug scripts reference EspoCRM's bootstrap path (`/var/www/html/bootstrap.php`). These are development tools, not production code. They are git-ignored.

## WARNING-4: Missing SHA256 Sidecars for Latest Releases

**Severity: MEDIUM**
**Location:** `deployment/`

Versions 1.9.1-alpha through 1.9.5-alpha (the latest 5 releases) have **no SHA256 sidecar files**. This breaks the release integrity process established for v1.6.0 through v1.9.0.

The current deployed version (1.9.5-alpha) has no cryptographic integrity attestation.

Additionally:
- `deployment/prospecting-extension.zip` (unversioned) coexists with versioned artifacts, creating ambiguity
- SHA256 file format is inconsistent: v1.6.0-v1.7.1 use raw hash only; v1.8.0-v1.9.0 use `<hash>  <filename>` format

## WARNING-5: Stale Version References

**Severity: LOW**
**Location:** Multiple documentation files

| File | Stated Version | Actual |
|------|---------------|--------|
| `crm-extension/README.md` | `1.1.0-alpha` | `1.9.5-alpha` |
| `docs/deployment/VERSIONING.md` | `1.9.0-alpha` | `1.9.5-alpha` |
| `docs/release/VERSION_POLICY.md` | `1.9.0-alpha` | `1.9.5-alpha` |

Only one release notes file exists (`docs/RELEASE_NOTES_1.7.1-alpha.md`) — no release notes for 1.8.0 through 1.9.5.

## WARNING-6: No Git Tags

**Severity: LOW**

`git tag -l` returns empty output. The release process specified in `docs/release/RELEASE_PROCESS.md` requires `v<version>` tags, but none have been created.

## WARNING-7: Design-Surface / Installable Metadata Duplication

**Severity: LOW**
**Location:** `crm-extension/Resources/` vs `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/`

Entity definitions, layouts, and routes exist in both locations. The build script (`build_release_package.ps1`) only packages `files/`, so the `Resources/` directory at extension root is a design-surface reference. However, some files (e.g., ResearchEvidence `list.json`) have diverged between the two locations, meaning the design surface shows stale layout information.

This is a maintenance risk: editing one location without the other creates metadata drift.

## WARNING-8: Working Tree Not Clean

**Severity: LOW**

48 files modified, 1 file deleted, ~100 files untracked. A production freeze should operate from a clean git state. However, the working tree changes appear to be Phase3C10.x in-progress work (acquisition modules, connector sync updates, dashboard additions, i18n updates).

Deleted file: `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchJob/PrimaryFilters/JobsWaiting.php` — appears to be an intentional removal (replaced by new dashlet-based approach).

## WARNING-9: Accumulated Build Artifacts and Test Logs

**Severity: LOW**
**Location:** `deployment/`, `temp/test-results/`

- 19 ZIP build artifacts in `deployment/` (only current version should exist on production host)
- ~150 test result log files in `temp/test-results/`
- ~105+ Python `__pycache__/*.pyc` files (git-ignored but present on disk)
- 5 test output dump files: `temp/c06_*.txt`

All are git-ignored or in deployment directory. No production impact but should be cleaned before release packaging.

---

# BLOCKER — Must Fix Before Freeze

## BLOCKER-1: PHP `peEvidenceType` Field Mapping Error

**Severity: HIGH — Data Integrity**
**Location:** `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php:60`

```php
// CURRENT (bug):
'peEvidenceType' => $item['claim_type'],   // Maps claim_type to BOTH peClaimType AND peEvidenceType

// CORRECT:
'peEvidenceType' => $item['evidence_type'], // evidence_type is the evidence format classification
```

`peClaimType` (what the claim is about — e.g., "product_mention", "technical_capability") and `peEvidenceType` (how the evidence was found — e.g., "visible_text", "title_tag", "meta_description") are semantically different fields. The current code maps `claim_type` to both, losing the evidence format classification.

The Python `ResearchEvidencePersistenceAdapter` correctly maps this:
```python
# research_evidence_persistence.py:281
"peEvidenceType": item.evidence_type,  # correct
```

**Impact**: All ResearchEvidence records created through the production sync path have incorrect `peEvidenceType` values. The field contains claim type data instead of evidence format data.

## BLOCKER-2: PHP `syncEvidence()` Has Zero Dedup — Creates Duplicates

**Severity: CRITICAL — Data Integrity**
**Location:** `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php:40-79`

The production evidence sync endpoint performs **no deduplication whatsoever**:

```php
// Lines 52-71: Unconditional create loop — no lookup, no identity check, no snapshot check
foreach ($payload['evidence'] as $item) {
    $evidence = $this->entityManager->getEntity('ResearchEvidence');  // Always new entity
    $evidence->set([...]);
    $this->entityManager->saveEntity($evidence);                      // Always saves
    $ids[] = $evidence->getId();
}
```

There is:
- No `find_research_evidence_for_snapshot()` call
- No `evidence_identity_key()` check
- No `peEvidenceId` uniqueness check
- No `peSnapshotHash` lookup
- No database-level unique constraint (only non-unique indexes exist)

**Impact**: Every call to `POST /Prospecting/sync/evidence` creates duplicate ResearchEvidence records. Retries, re-syncs, and replay all produce duplicates. This applies to the **production code path** (`connector_api.py → ChituSyncService::syncEvidence()`).

## BLOCKER-3: Python Dedup Adapter Never Called in Production

**Severity: CRITICAL — Architecture Gap**
**Location:** `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py`

The `ResearchEvidencePersistenceAdapter` implements a correct three-layer dedup strategy:
1. **Batch-level dedup**: Rejects duplicate `evidence_id` and duplicate `evidence_identity_key` within input
2. **Snapshot-level dedup**: Queries CRM by `leadId + snapshotHash` — skips entire batch if all already exist
3. **Per-evidence identity dedup**: Queries CRM by `leadId + sourceUrl + claimType + claim` — skips individual already-existing facts

This adapter is **correctly designed, fully tested, and never called by any production code path**.

The production flow (`connector_api.py:64-83`) uses:
```python
# connector_api.py - calls PHP endpoint directly, bypassing Python adapter
lead = self.sync_lead(payload)         # POST /Prospecting/sync/lead
evidence = self.sync_evidence(payload) # POST /Prospecting/sync/evidence ← no dedup
```

The evidence sync goes directly to the PHP endpoint (BLOCKER-2), completely bypassing the Python dedup adapter.

**Impact**: The correct dedup logic exists, passes tests, but is dead code in production. This is an architecture integration gap — the right code exists but isn't wired into the production path.

### Root Cause Analysis

The architecture has two evidence sync paths that are **not unified**:

| Path | Module | Dedup? | In Production? |
|------|--------|:---:|:---:|
| Python adapter | `ResearchEvidencePersistenceAdapter` | ✅ 3-layer | ❌ Never called |
| PHP endpoint | `ChituSyncService::syncEvidence()` | ❌ None | ✅ Production path |

The production path (`connector_api.py → POST /Prospecting/sync/evidence → ChituSyncService`) skips the dedup adapter entirely.

---

# Phase3C10.4 Capability Verification

## C10.0-A: Evidence Dedup Hardening

| Check | Status |
|-------|:---:|
| Identity formula: leadId + canonical URL + claimType + claim SHA-256 | ✅ PASS |
| snapshotHash excluded from identity | ✅ PASS |
| Python adapter: batch + snapshot + per-evidence dedup | ✅ PASS |
| Python adapter: partial failure recovery | ✅ PASS |
| Tests: deterministic identity, duplicate prevention, retry safety | ✅ PASS |
| **Production code path uses dedup adapter** | ❌ **BLOCKER-3** |
| PHP endpoint has zero dedup | ❌ **BLOCKER-2** |

## C10.0-B: Send Idempotency Contract

| Check | Status |
|-------|:---:|
| SHA-256 idempotency key (created_at excluded) | ✅ PASS |
| SendAttempt state machine (CREATED→READY→PROCESSING→SENT/FAILED) | ✅ PASS |
| Duplicate reservation returns EXISTING | ✅ PASS |
| Request validation (all fields + key consistency) | ✅ PASS |
| Tests: reservation, transition, cancellation, validation | ✅ PASS |

## C10.1: Human Approval Model

| Check | Status |
|-------|:---:|
| State machine: DRAFT_READY→PENDING_REVIEW→APPROVED/REJECTED→READY_TO_SEND | ✅ PASS |
| REJECTED is terminal (new draft identity required) | ✅ PASS |
| READY_TO_SEND is terminal | ✅ PASS |
| Illegal transitions blocked | ✅ PASS |
| Human reviewer required for approve/reject | ✅ PASS |
| Immutable audit trail per transition | ✅ PASS |
| Tests: all states, all transitions, duplicate rejection, audit trace | ✅ PASS |

## C10.2: Send Provider Adapter

| Check | Status |
|-------|:---:|
| Provider-neutral SendProvider protocol | ✅ PASS |
| Provider result validation | ✅ PASS |
| Provider name mismatch rejection | ✅ PASS |
| No provider SDK, network, or CRM dependency | ✅ PASS |
| Tests: acceptance, rejection, failure, provider validation | ✅ PASS |

## C10.3: Controlled Send Execution

| Check | Status |
|-------|:---:|
| Execution state machine: READY_TO_SEND→SUBMITTED→PROCESSING→SENT/FAILED | ✅ PASS |
| Requires READY_TO_SEND approval status | ✅ PASS |
| Duplicate execution prevented (DUPLICATE_EXECUTION) | ✅ PASS |
| Draft double-send prevented (DRAFT_ALREADY_SENT) | ✅ PASS |
| In-progress guard (EXECUTION_IN_PROGRESS) | ✅ PASS |
| Approval checks before any side effect | ✅ PASS |
| Immutable audit trace preserved | ✅ PASS |
| Tests: success, duplicate, approval-not-ready, already-sent, in-progress | ✅ PASS |

## C10.4: Reply Tracking Boundary

| Check | Status |
|-------|:---:|
| Reply event identity (deterministic ID generation) | ✅ PASS |
| Only SENT executions can receive replies | ✅ PASS |
| Lead/draft match verification | ✅ PASS |
| Original send audit trace preserved in reply event | ✅ PASS |
| Duplicate reply events rejected | ✅ PASS |
| States: SENT, REPLIED, BOUNCED, UNSUBSCRIBED | ✅ PASS |
| Tests: creation, trace preservation, duplicate, bounce, unsubscribe, validation | ✅ PASS |

---

# Database-Level Guarantees

| Entity | Unique Constraints | Non-Unique Indexes |
|--------|:---:|:---:|
| Lead | `peCandidateId` (not unique index) | `peSourceBatchId` |
| ResearchEvidence | **None** | `peEvidenceId`, `peSnapshotHash` |
| SearchJob | `queryFingerprint` (not unique) | `status`, `source` |
| ProspectPool | None verified | None verified |

**No database-level unique constraint exists for evidence dedup.** The correct composite unique index would be on `(leadId, peSourceUrl, peClaimType, peClaim)` or on a hash thereof. This means dedup protection is entirely application-layer — and the production application layer (PHP) has none.

---

# Freeze Recommendation

**VERDICT: CONDITIONAL GO**

The Phase3C10.4 architecture is **structurally sound**. All state machines are correct, all boundaries are enforced, and the human approval gate cannot be bypassed. The three BLOCKERs are **integration/implementation gaps**, not architectural flaws:

1. **BLOCKER-1** (peEvidenceType mapping): One-line PHP fix
2. **BLOCKER-2** (PHP no dedup): Wire `ResearchEvidencePersistenceAdapter` into the `syncEvidence` flow, or add identity checks to the PHP endpoint
3. **BLOCKER-3** (Python adapter unused): Single integration point — change `connector_api.py::sync_evidence()` to use the adapter instead of direct POST

**Recommended path to freeze:**

1. Fix BLOCKER-1: Change `$item['claim_type']` to `$item['evidence_type']` on line 60 of `ChituSyncService.php`
2. Fix BLOCKER-2/3 (same root cause): Either:
   - **Option A (preferred)**: Have `connector_api.py::sync_evidence()` call `ResearchEvidencePersistenceAdapter.persist()` before the PHP POST, or replace the PHP POST with adapter-driven creation
   - **Option B**: Add dedup logic (snapshot hash check + per-evidence identity check) to `ChituSyncService::syncEvidence()` in PHP
3. Add SHA256 sidecar for v1.9.5-alpha
4. Clean working tree (commit or stash pending changes)
5. Update stale version references in documentation

After resolving the 3 BLOCKERs, the architecture is **ready for freeze**.

---

---

# CRM-Level Lifecycle Audit (Supplement)

The C10.x lifecycle state machines (approval, send execution, send idempotency) are correctly implemented in the **Python connector** (`human_approval.py`, `send_execution.py`, `send_idempotency.py`). However, the **CRM PHP layer** has gaps.

## PHP State Machine Gaps

### SearchJob Status: No State Machine Enforcement

The SearchJob `status` field (`QUEUED → RUNNING → COMPLETED/FAILED, CANCELLED`) is a plain `enum` with **no transition guards** in PHP. Any user with edit permission can jump directly from `QUEUED` to `COMPLETED` without passing through `RUNNING`. This is mitigated by:
- The Python `AcquisitionWorker` enforces correct transitions through `claim_search_job(expected_status="QUEUED")` and `update_search_job(expected_status="RUNNING")`
- The connector is the only expected writer of these states

### peEmailStatus: No Transition Guards at CRM Level

The Lead `peEmailStatus` field (`NONE → DRAFT_READY → APPROVED → SENT → REPLIED/BOUNCED`) has no code preventing direct jumps (e.g., NONE → SENT). The only guard is in `EmailEventWorkflowHook::applySent()` which won't overwrite already-REPLIED/BOUNCED records. Mitigation:
- The Python connector enforces `APPROVED → READY_TO_SEND` before `ControlledSendExecutionService.execute()` creates send requests
- EspoCRM does not send email; these are projected states from external systems

### LeadWorkflowHook: No Task Deduplication

`LeadWorkflowHook.php` creates "Prepare Outreach" and "Review and Contact Lead" tasks on `peResearchStatus`/`peOpportunityScoreV4` changes. If `peResearchStatus` is toggled from COMPLETED back to NONE and then to COMPLETED again, duplicate tasks are created. Unlike `EmailEventWorkflowHook` (which uses `createTaskOnce()`), `LeadWorkflowHook` has no duplicate task guard.

---

# Extension Structure Audit (Supplement)

## Duplicate Metadata

Five metadata types are duplicated between `Resources/` (design surface) and `files/.../Prospecting/Resources/` (installable module):

| Metadata Type | Resources/ | Module | Status |
|---------------|:---:|:---:|--------|
| entityDefs (9 files) | ✅ | ✅ | Identical duplicates |
| ACL definitions (7 files) | ✅ | ✅ | Identical duplicates |
| Layouts (20 files) | ✅ | ✅ | Partial (3 listDashletExpanded missing from Resources/) |
| routes.json | ✅ | ✅ | Identical duplicate |
| formula/Lead.json | ✅ | ✅ | Identical duplicate |

Six metadata types exist **only** in the module (single source): clientDefs, scopes, selectDefs, dashlets, app/layouts, i18n.

The build script (`build_release_package.ps1`) only packages `files/`, so Resources/ is a design-surface reference. However, editing one location without the other creates metadata drift.

## Empty Skeleton Directories

- `custom/Espo/Modules/Prospecting/{Api,Controllers,Services}/` — empty, only README placeholders
- `files/custom/Espo/Custom/Resources/metadata/scopes/` — empty directory
- `application/` — reserved placeholder, not packaged

The empty `custom/` skeleton mirrors the module structure without code, creating a risk that developers might create files in the wrong location.

## Stale README

`crm-extension/README.md` states version `1.1.0-alpha` and describes the extension as a "CRM entity model skeleton." The actual extension is v1.9.5-alpha with full controllers, services, API routes, workflow hooks, client-side JS, and i18n.

---

**Phase G01 audit complete. No code was modified, no data was created or deleted.**
