# Phase3C10.5 — Evidence Runtime Path Verification

**Date:** 2026-07-14
**Scope:** Read-only path tracing — ResearchEvidence production write path
**Status:** **VERIFIED** — Single production path identified; 2 additional non-production paths documented

---

## Executive Summary

ResearchEvidence records are created through **one production path** and **two non-production paths**. The production path goes through PHP `ChituSyncService::syncEvidence()` — the Python `ResearchEvidencePersistenceAdapter` (with correct dedup and field mapping) is **never called in production**.

---

## 1. All ResearchEvidence Creation Entry Points

### Entry Point A — Production Sync (PHP)

| Property | Value |
|----------|-------|
| **Path** | `POST /api/v1/Prospecting/sync/evidence` |
| **API Controller** | `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostSyncEvidence.php` |
| **Service** | `ChituSyncService::syncEvidence()` (lines 40–79) |
| **Caller** | `ProspectingConnectorClient.sync_evidence()` → `sync_source()` |
| **Production?** | **YES — this is the production runtime path** |

### Entry Point B — Python Persistence Adapter (Test-Only)

| Property | Value |
|----------|-------|
| **Module** | `research_evidence_persistence.py` → `ResearchEvidencePersistenceAdapter.persist()` |
| **Protocol** | `ResearchEvidencePersistenceClient.create_research_evidence()` |
| **Callers** | `test_phase3c07_research_evidence_persistence.py`, `test_phase3c07_runtime_acceptance.py`, `test_phase3c10_evidence_dedup_hardening.py` |
| **Production?** | **NO — instantiated only in test files** |

### Entry Point C — Synthetic Diagnostic (LocalEspoCRMClient)

| Property | Value |
|----------|-------|
| **Method** | `LocalEspoCRMClient.sync_payload()` (lines 201–219) |
| **HTTP** | `POST /api/v1/ResearchEvidence` (generic CRUD endpoint) |
| **Caller** | `real_sync.py` → `run_local_synthetic_sync()` |
| **Production?** | **NO — synthetic test only; records are rolled back after verification** |

### Entry Point D — Standard CRM CRUD

| Property | Value |
|----------|-------|
| **Controller** | `ResearchEvidence` extends `Record` (empty extension) |
| **HTTP** | `POST /api/v1/ResearchEvidence` (standard EspoCRM CRUD) |
| **Caller** | Any authenticated user with `ResearchEvidence: create` permission |
| **Production?** | **YES — but this is manual CRM operation, not automated sync** |

---

## 2. Production Runtime Path — Confirmed

The **only automated production write path** for ResearchEvidence is:

```
Chitu Intelligence Engine (external)
  │
  │  imports ProspectingConnectorClient
  │  constructs SyncSource (Candidate + Research + Score + Qualification)
  │  calls client.sync_source(source)
  │
  ▼
ProspectingConnectorClient.sync_source()
  [connector_api.py:70-97]
  │
  │  1. EspoCRMSyncMapper.build(source) → SyncContractPayload V1
  │  2. validate_sync_contract(payload) → structural validation
  │  3. evaluate_sync_gate(source, payload) → eligibility gate
  │  4. sync_lead(payload) → POST /Prospecting/sync/lead
  │  5. sync_evidence(payload) → POST /Prospecting/sync/evidence  ◄── EVIDENCE PATH
  │  6. sync_opportunity_proposal(payload) → POST /Prospecting/sync/opportunity-proposal
  │
  ▼
sync_evidence(payload)
  [connector_api.py:64-65]
  │
  │  POST /api/v1/Prospecting/sync/evidence
  │  Body: FULL SyncContractPayload as JSON
  │  Headers: X-Api-Key, Content-Type: application/json
  │
  ▼
PostSyncEvidence API Controller
  [Api/PostSyncEvidence.php:11-18]
  │
  │  $this->service->syncEvidence($request->getParsedBody())
  │
  ▼
ChituSyncService::syncEvidence()
  [Services/ChituSyncService.php:40-79]
  │
  │  1. payload($body) → parses and validates contract
  │  2. requiredLead(candidate_id) → finds Lead by peCandidateId
  │  3. assertScope('ResearchEvidence', 'create') → ACL check
  │  4. foreach evidence item:
  │       $evidence = $entityManager->getEntity('ResearchEvidence')  // NEW entity
  │       $evidence->set([...field mapping...])                      // see §3 below
  │       $entityManager->saveEntity($evidence)                      // INSERT into DB
  │  5. Return {success, crm_ids, evidence_count}
  │
  ▼
EspoCRM Database — ResearchEvidence table
  │
  │  Fields written (see §3)
  │
  └─► NO dedup, NO identity check, NO snapshot lookup
```

### Key Observations

1. **The Python `ResearchEvidencePersistenceAdapter` is never called.** The production flow goes directly from `connector_api.py` to the PHP endpoint. The dedup adapter exists, passes tests, but is dead code in production.

2. **The PHP endpoint creates records unconditionally.** No `WHERE` query checks for existing records before `saveEntity()`. No identity key comparison. No snapshot hash lookup.

3. **The full SyncContractPayload is sent to the PHP endpoint.** The PHP service parses the `evidence[]` array from the contract and creates one ResearchEvidence record per item.

---

## 3. Field Mapping in Production Path

The PHP `ChituSyncService::syncEvidence()` maps fields as follows (lines 54–67):

| CRM Field | Source from Payload | Correct? |
|-----------|-------------------|:---:|
| `name` | `company.name + " — " + evidence_id` | ✅ |
| `leadId` | `$lead->getId()` (resolved from `peCandidateId`) | ✅ |
| `peEvidenceId` | `$item['evidence_id']` | ✅ |
| `peClaim` | `$item['claim']` | ✅ |
| `peClaimType` | `$item['claim_type']` | ✅ |
| **`peEvidenceType`** | **`$item['claim_type']`** | **❌ BLOCKER: should be `$item['evidence_type']`** |
| `peSourceUrl` | `$item['source_url']` | ✅ |
| `peEvidenceText` | `$item['evidence_text']` | ✅ |
| `peContentSummary` | `$item['evidence_text']` | ⚠️ Duplicate of evidence_text |
| `peConfidence` | `$item['confidence']` | ✅ |
| `peCapturedAt` | `$item['captured_at']` (reformatted) | ✅ |
| `peSchemaVersion` | `$item['schema_version']` | ✅ |
| `peSnapshotHash` | `$payload['provenance']['evidence_snapshot_hash']` | ✅ |

**BLOCKER (confirmed):** Line 60 maps `claim_type` to `peEvidenceType`. The Python adapter correctly maps `evidence_type` to `peEvidenceType`. The `claim_type` field describes what the claim is about (e.g., "product_mention"); `evidence_type` describes how the evidence was found (e.g., "visible_text", "title_tag"). These are semantically different. Every ResearchEvidence record created through the production path has an incorrect `peEvidenceType` value.

For comparison, the Python `ResearchEvidencePersistenceAdapter._research_evidence_body()` maps correctly:

```python
# research_evidence_persistence.py:273-288
"peClaimType": item.claim_type,       # correct
"peEvidenceType": item.evidence_type,  # correct
```

---

## 4. Non-Production Paths — Why They Exist

### Path B: Python Persistence Adapter

The `ResearchEvidencePersistenceAdapter` implements a correct three-layer dedup strategy:

1. **Batch dedup**: Rejects duplicate `evidence_id` and duplicate `evidence_identity_key` within input
2. **Snapshot dedup**: Queries CRM by `leadId + snapshotHash` before creating
3. **Per-evidence identity dedup**: Queries CRM by `leadId + sourceUrl + claimType + claim`

It is called **exclusively from test files**:
- `test_phase3c07_research_evidence_persistence.py` — 6 adapter unit tests
- `test_phase3c07_runtime_acceptance.py` — 2 synthetic end-to-end tests
- `test_phase3c10_evidence_dedup_hardening.py` — 5 dedup hardening tests

The adapter is correctly designed and fully tested. It is **not wired into the production flow** because `ProspectingConnectorClient.sync_evidence()` sends the raw payload directly to the PHP endpoint rather than calling `adapter.persist()` first.

### Path C: Synthetic Diagnostic

`LocalEspoCRMClient.sync_payload()` creates a synthetic Lead + ResearchEvidence records for preflight/diagnostic verification, then **rolls them back**. This path:
- Uses a `SYNTHETIC_MARKER` in the description field
- Checks for existing synthetic records before creating
- Calls `rollback()` on failure or after verification
- Is only called by `run_local_synthetic_sync()` in `real_sync.py`
- Is for local development use only — not production

### Path D: Standard CRUD

The empty `ResearchEvidence` controller inherits from EspoCRM's `Record` controller, providing standard REST CRUD operations. A human user (or API client) with `ResearchEvidence: create` permission can create records via `POST /api/v1/ResearchEvidence`. This is manual CRM operation, not automated sync, and is the expected behavior for a CRM entity.

---

## 5. Production Runtime Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHITU INTELLIGENCE ENGINE                          │
│                    (external, not in this repo)                       │
│                                                                       │
│  SyncSource = { Candidate + Research + Score + Qualification }       │
│       │                                                               │
└───────┼───────────────────────────────────────────────────────────────┘
        │
        │  ProspectingConnectorClient(base_url, api_key)
        │  client.sync_source(source)
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                   PYTHON CONNECTOR (connector_api.py)                  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  sync_source()                                                   │  │
│  │  1. EspoCRMSyncMapper.build(source) → SyncContractPayload V1    │  │
│  │  2. validate_sync_contract(payload) → structural validation      │  │
│  │  3. evaluate_sync_gate(source, payload) → eligibility gate       │  │
│  │  4. sync_lead(payload)         → POST /Prospecting/sync/lead    │  │
│  │  5. sync_evidence(payload)     → POST /Prospecting/sync/evidence│  │
│  │  6. sync_opportunity_proposal  → POST /.../opportunity-proposal │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ★ ResearchEvidencePersistenceAdapter is NOT called here              │
│  ★ No dedup, no identity check, no snapshot lookup                    │
│                                                                        │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               │  HTTPS POST (X-Api-Key auth)
                               │  Full SyncContractPayload as JSON body
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     ESPOCRM PHP EXTENSION                              │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  PostSyncEvidence API Controller                                 │   │
│  │  → ChituSyncService::syncEvidence($body)                         │   │
│  └────────────────────────┬───────────────────────────────────────┘   │
│                           │                                            │
│                           ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  ChituSyncService::syncEvidence()                                │   │
│  │                                                                   │   │
│  │  payload($body):                                                  │   │
│  │    - Parses JSON body                                            │   │
│  │    - Validates contract_version == '1.0'                         │   │
│  │    - Checks all 10 required sections present                     │   │
│  │    - Validates identity.candidate_id                             │   │
│  │                                                                   │   │
│  │  requiredLead(candidate_id):                                      │   │
│  │    - SELECT * FROM lead WHERE pe_candidate_id = ?                │   │
│  │    - Throws Conflict if >1 match                                  │   │
│  │    - Throws NotFound if 0 matches                                 │   │
│  │                                                                   │   │
│  │  assertScope('ResearchEvidence', 'create'):                       │   │
│  │    - ACL check on API user                                        │   │
│  │                                                                   │   │
│  │  foreach evidence[] as item:                                      │   │
│  │    $evidence = new ResearchEvidence()     ← ALWAYS new entity    │   │
│  │    $evidence->set([...field mapping...])                          │   │
│  │    $entityManager->saveEntity($evidence)  ← ALWAYS INSERT        │   │
│  │                                                                   │   │
│  │  ★ NO dedup query before saveEntity()                             │   │
│  │  ★ NO identity key check                                          │   │
│  │  ★ NO snapshot hash lookup                                        │   │
│  │  ★ peEvidenceType ← claim_type (BUG)                              │   │
│  │                                                                   │   │
│  │  Return { success: true, crm_ids: [...], evidence_count: N }     │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               │  INSERT INTO research_evidence (...)
                               │
                               ▼
                    ┌──────────────────────┐
                    │   ESPOCRM DATABASE    │
                    │   research_evidence   │
                    │                      │
                    │  No unique constraint │
                    │  on (leadId, source,  │
                    │  claimType, claim)    │
                    └──────────────────────┘
```

---

## 6. Comparison: Production vs Python Adapter

| Aspect | Production (PHP) | Python Adapter | Delta |
|--------|:---:|:---:|:---:|
| **Batch dedup** (duplicate evidence_id) | ❌ None | ✅ Rejects `DUPLICATE_EVIDENCE_ID` | Missing in production |
| **Batch dedup** (duplicate identity) | ❌ None | ✅ Rejects `DUPLICATE_EVIDENCE_IDENTITY` | Missing in production |
| **Snapshot-level dedup** (leadId + snapshotHash) | ❌ None | ✅ Skips entire batch if all exist | Missing in production |
| **Per-evidence identity dedup** (leadId + sourceUrl + claimType + claim) | ❌ None | ✅ Skips individual existing facts | Missing in production |
| **Partial failure recovery** | ❌ None | ✅ Creates only missing rows on retry | Missing in production |
| **peEvidenceType mapping** | ❌ `claim_type` | ✅ `evidence_type` | Wrong field in production |
| **peContentSummary** | `evidence_text` (duplicate) | `claim` (correct) | Wrong content |
| **Database-level unique constraint** | ❌ None | N/A (application-layer) | Missing in both |
| **ACL enforcement** | ✅ `assertScope()` | N/A (relies on API auth) | Present in both |
| **Contract validation** | ✅ 10-section check | ✅ `validate_sync_contract()` | Present in both |

---

## 7. Call Graph — Who Calls What

```
sync_source()                                    [connector_api.py:70]
  ├── sync_lead(payload)                         [connector_api.py:61]
  │     └── POST /Prospecting/sync/lead
  │           └── PostSyncLead.process()
  │                 └── ChituSyncService::syncLead()
  │                       └── saveEntity(Lead)              ← CRM write
  │
  ├── sync_evidence(payload)                     [connector_api.py:64]   ◄── PRODUCTION
  │     └── POST /Prospecting/sync/evidence
  │           └── PostSyncEvidence.process()
  │                 └── ChituSyncService::syncEvidence()
  │                       └── saveEntity(ResearchEvidence)  ← CRM write (×N)
  │
  └── sync_opportunity_proposal(payload)         [connector_api.py:67]
        └── POST /Prospecting/sync/opportunity-proposal
              └── PostSyncOpportunityProposal.process()
                    └── ChituSyncService::syncOpportunityProposal()
                          └── saveEntity(Lead)              ← Lead update only

--- Non-Production Paths ---

run_local_synthetic_sync()                       [real_sync.py:48]
  └── LocalEspoCRMClient.sync_payload()          [real_client.py:201]
        └── POST /api/v1/ResearchEvidence (×N)   ← SYNTHETIC ONLY + ROLLBACK

ResearchEvidencePersistenceAdapter.persist()     [research_evidence_persistence.py:72]
  └── client.create_research_evidence()          ← TEST ONLY (test doubles)
        └── (never wired to production HTTP client)

Standard CRUD
  └── POST /api/v1/ResearchEvidence              ← MANUAL CRM OPERATION
        └── ResearchEvidence controller (Record)
```

---

## 8. Verdict

### Production Runtime: PHP `ChituSyncService::syncEvidence()`

- **Confirmed**: This is the only automated production path
- **No dedup**: Every call creates new records unconditionally
- **Field bug**: `peEvidenceType` receives `claim_type` instead of `evidence_type`
- **No database guard**: No unique constraint prevents duplicate identity

### Python Adapter: `ResearchEvidencePersistenceAdapter`

- **Confirmed**: Correctly designed and tested
- **Confirmed**: Not called by any production code path
- **Location**: `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py`
- **Instantiated only in**: 3 test files (13 total test methods)
- **Protocol implementation exists**: `LocalEspoCRMClient.create_research_evidence()` at `real_client.py:170` — but never wired to the adapter in production

### Path to Unification

To bring the production path up to parity with the Python adapter:

1. **Fix field mapping** in `ChituSyncService.php:60`: `'peEvidenceType' => $item['evidence_type']`
2. **Add dedup** — either:
   - **Option A (Python-side)**: Have `connector_api.py:sync_source()` call `ResearchEvidencePersistenceAdapter.persist()` using `LocalEspoCRMClient` as the persistence client, and only POST to the PHP endpoint for non-evidence fields
   - **Option B (PHP-side)**: Add identity-based lookup before insert in `ChituSyncService::syncEvidence()`
   - **Option C (Database)**: Add a composite unique index on `(leadId, peSourceUrl, peClaimType, peClaim)` or on a hash column

---

**Phase3C10.5 evidence runtime path verification complete. The production write path is confirmed as PHP `ChituSyncService::syncEvidence()` with zero dedup and a field mapping bug. The correct Python dedup adapter exists but is not wired into production. No code was modified.**
