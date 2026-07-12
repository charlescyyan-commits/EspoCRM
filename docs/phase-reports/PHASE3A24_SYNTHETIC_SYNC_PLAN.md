# Phase 3A-2.4 Synthetic Lead Sync Verification Plan

**Status:** DESIGN ONLY — no API writes in this document  
**Date:** 2026-07-11  
**Prerequisite:** Phase 3A-2.3 preflight PASS (`authenticate` + `preflight`)  
**Target:** `http://localhost:8080` only  
**API principal:** `chitu_ai_connector` via `X-Api-Key`

## Purpose

Validate one controlled Engine → EspoCRM synthetic write path:

1. Create one synthetic Lead  
2. Create one (or more) ResearchEvidence records  
3. Link Lead → ResearchEvidence  
4. GET-verify field consistency  
5. Rollback (delete) all synthetic test data  

This phase must not touch production, real dealers, email, scoring rules, or Sync Contract V1.

## Existing Implementation Entry (do not redesign)

Preferred runner already exists:

| Component | Path | Role |
|---|---|---|
| Workflow | `integration/espocrm_sync/real_sync.py` → `run_local_synthetic_sync()` | End-to-end synthetic sync + duplicate check + rollback |
| Client | `integration/espocrm_sync/real_client.py` → `LocalEspoCRMClient` | Localhost-only REST calls |
| Payload builder | `EspoCRMSyncMapper` + `build_synthetic_source()` | Contract-aligned synthetic source |

Phase 3A-2.4 execution (when authorized) should call this existing path rather than inventing ad-hoc curl scripts.

---

## 1. API Endpoints

Base: `http://localhost:8080/api/v1/`  
Auth header: `X-Api-Key: <ESPOCRM_TEST_API_KEY>`  
Content-Type (writes): `application/json`

### Read / gate (already proven)

| Step | Method | Path | Purpose |
|---|---|---|---|
| Auth | GET | `App/user` | Confirm API user |
| Preflight | GET | `Metadata?key=entityDefs.Lead.fields` | Lead fields visible |
| Preflight | GET | `Metadata?key=entityDefs.ResearchEvidence` | Evidence entity visible |
| Preflight | GET | `Metadata?key=entityDefs.Lead.links` | `researchEvidences` link visible |

### Write path (planned — not executed now)

| Step | Method | Path | Body summary |
|---|---|---|---|
| Duplicate probe | GET | `Lead?where[0][type]=equals&where[0][attribute]=name&where[0][value]=Synthetic 3D Dealer Test GmbH` | Find prior synthetic Lead |
| Create Lead | POST | `Lead` | Synthetic Lead fields + marker description |
| Create Evidence | POST | `ResearchEvidence` | Compact evidence fields |
| Link | POST | `Lead/{leadId}/researchEvidences` | `{"id": "{evidenceId}"}` |

### Verify path

| Step | Method | Path | Purpose |
|---|---|---|---|
| GET Lead | GET | `Lead/{leadId}?select=name,website,peOpportunityScoreV4,...` | Field equality |
| GET Evidence | GET | `ResearchEvidence/{id}?select=peClaim,peSourceUrl,...` | Field equality |
| GET relation | GET | `Lead/{leadId}/researchEvidences?select=id` | Link membership |

### Rollback path

| Step | Method | Path | Purpose |
|---|---|---|---|
| Delete Evidence | DELETE | `ResearchEvidence/{evidenceId}` | Remove synthetic evidence first |
| Delete Lead | DELETE | `Lead/{leadId}` | Remove synthetic Lead |
| Confirm clean | GET | Lead search by synthetic name + marker | Must return no match |

---

## 2. Payload Design

### Identity / safety markers (mandatory)

| Marker | Value | Where |
|---|---|---|
| Lead name | `Synthetic 3D Dealer Test GmbH` | `Lead.name` |
| Description marker | `[CHITU_SYNTHETIC_TEST]` | `Lead.description` line 1 |
| Flags | `is_test=true`, `data_type=synthetic` | `Lead.description` |
| Sync key line | `sync_key=<idempotency_key>` | `Lead.description` |
| Domain | `synthetic-dealer.example` | Engine identity / website host |
| Evidence id | `test-ev-001` (synthetic) | `peEvidenceId` |

Only records containing the description marker are treated as synthetic for lookup/rollback.

### Synthetic Lead POST body (planned shape)

Derived by `LocalEspoCRMClient._lead_body()` from Sync Contract payload:

```json
{
  "name": "Synthetic 3D Dealer Test GmbH",
  "website": "https://synthetic-dealer.example",
  "peOpportunityScoreV4": 80.0,
  "peScoreTier": "A",
  "peConfidence": 1.0,
  "peEvidenceCoverage": 0.75,
  "peBestFirstProduct": "Resin Tank",
  "peQualificationStatus": "OUTREACH_READY",
  "peEngineVersion": "prospecting-engine-test",
  "peScoreRulesVersion": "canonical-scoring-v4.0",
  "description": "[CHITU_SYNTHETIC_TEST]\nis_test=true\ndata_type=synthetic\nsync_key=<idempotency_key>"
}
```

### Synthetic ResearchEvidence POST body (planned shape)

```json
{
  "name": "Synthetic evidence test-ev-001",
  "peEvidenceId": "test-ev-001",
  "peClaim": "Synthetic 3D dealer",
  "peClaimType": "company_type",
  "peSourceUrl": "https://synthetic-dealer.example/about",
  "peEvidenceText": "Synthetic test evidence only.",
  "peConfidence": 1.0,
  "peCapturedAt": "YYYY-MM-DD HH:MM:SS",
  "peSchemaVersion": "<evidence schema version from payload>",
  "peSnapshotHash": "<provenance.evidence_snapshot_hash>"
}
```

Notes:

- `peCapturedAt` is converted from ISO-8601 to EspoCRM datetime string.
- Evidence body does **not** include score/ranking/email/AI fields.
- Relationship is established by a separate link POST, not by embedding `leadId` alone (current client design).

### Link POST body

```json
{ "id": "<created_research_evidence_id>" }
```

to `POST /api/v1/Lead/{leadId}/researchEvidences`.

---

## 3. Field Mapping

### Lead

| EspoCRM field | Sync Contract / Engine source | Required in verify |
|---|---|---|
| `name` | `company.name` / synthetic company name | YES |
| `website` | `company.website` | YES |
| `peOpportunityScoreV4` | `score.value` | YES |
| `peScoreTier` | `score.score_tier` | YES |
| `peConfidence` | `score.aggregate_confidence` | YES |
| `peEvidenceCoverage` | `score.evidence_coverage` | YES |
| `peBestFirstProduct` | `recommendation.best_first_product` | YES (in body; verify set includes it via `_LEAD_FIELDS`) |
| `peQualificationStatus` | `qualification.status` | YES |
| `peEngineVersion` | `provenance.engine_version` | YES |
| `peScoreRulesVersion` | `score.rules_version` | YES |
| `description` | synthetic marker block | YES (marker presence) |

### ResearchEvidence

| EspoCRM field | Sync Contract path | Required in verify |
|---|---|---|
| `name` | generated from evidence id | create only |
| `peEvidenceId` | `evidence[].evidence_id` | create |
| `peClaim` | `evidence[].claim` | YES |
| `peClaimType` | `evidence[].claim_type` | create |
| `peSourceUrl` | `evidence[].source_url` | YES (selected in GET) |
| `peEvidenceText` | `evidence[].evidence_text` | YES |
| `peConfidence` | `evidence[].confidence` | YES |
| `peCapturedAt` | `evidence[].captured_at` | create |
| `peSchemaVersion` | `evidence[].schema_version` | YES |
| `peSnapshotHash` | `provenance.evidence_snapshot_hash` | create |

### Relationship

| Side | Link | Foreign |
|---|---|---|
| Lead | `researchEvidences` (hasMany) | ResearchEvidence |
| ResearchEvidence | `lead` (belongsTo) | Lead |

---

## 4. Verification Steps (execution order when authorized)

### Gate 0 — Environment

1. Confirm `ESPOCRM_TEST_ENV=true`.  
2. Confirm `ESPOCRM_TEST_API_KEY` present (do not log value).  
3. Confirm base URL is `http://localhost:8080` only.

### Gate 1 — Auth + preflight (must remain PASS)

1. `authenticate()` → `GET App/user` → userName `chitu_ai_connector`.  
2. `preflight()` → Lead `pe*` fields, ResearchEvidence fields, `researchEvidences` link visible.

### Gate 2 — ACL readiness for writes + rollback (must check before POST)

Confirm API Role allows:

| Scope | create | read | edit | delete |
|---|---|---|---|---|
| Lead | yes (required) | all/own sufficient for GET | optional | **yes required for rollback** |
| ResearchEvidence | yes | all | all (current) | **yes required for current rollback code** |

**Known blocker from Phase 3A-2.3:** ResearchEvidence Role currently has `delete: no`.  
Existing `LocalEspoCRMClient.rollback()` issues `DELETE ResearchEvidence/{id}` then `DELETE Lead/{id}`.  
With `delete: no`, Phase 3A-2.4 will create data it cannot clean up via the API user unless delete is granted (or a separate authorized admin rollback path is approved).

Do not start POST until delete ACL (or alternate rollback authorization) is resolved.

### Step A — Stale cleanup (only if prior synthetic exists)

1. `find_synthetic_lead()` by name + marker.  
2. If found: rollback that Lead/evidence, then `verify_rollback()`.

### Step B — Create

1. Build synthetic SyncSource (`build_synthetic_source()`).  
2. Map + gate (`EspoCRMSyncMapper` + `evaluate_sync_gate`) — must accept.  
3. `POST Lead` → capture `lead_id`.  
4. `POST ResearchEvidence` for each evidence item → capture `evidence_ids`.  
5. `POST Lead/{lead_id}/researchEvidences` for each evidence id.

Expected first-run status: `CREATED`.

### Step C — GET verify

1. GET Lead; compare all `_LEAD_FIELDS` except requiring exact full description equality — marker must be present; other pe* fields must equal posted body.  
2. GET each ResearchEvidence; at minimum `peClaim` and `peSchemaVersion` must match (current client verify).  
3. GET relation list; all created evidence ids must be linked.

### Step D — Duplicate behavior

1. Call `sync_payload` again with same synthetic identity.  
2. Expect `DUPLICATE` and same `lead_id` (no second Lead).

### Step E — Rollback

1. DELETE each ResearchEvidence id.  
2. DELETE Lead id.  
3. `verify_rollback()` — synthetic Lead search must be empty.

### Step F — Pass criteria

| Check | Pass condition |
|---|---|
| Create Lead | HTTP success + id returned |
| Create Evidence | HTTP success + id returned |
| Link | Evidence appears under Lead relation |
| Field verify | Mapped fields match GET |
| Duplicate | Second sync returns existing Lead |
| Rollback | Synthetic Lead gone; no orphan evidence for that Lead |

---

## 5. Rollback Strategy

### Primary (implemented)

```text
for evidence_id in evidence_ids:
    DELETE ResearchEvidence/{evidence_id}
DELETE Lead/{lead_id}
GET search synthetic name+marker → must be empty
```

### Failure-path rollback

If create fails after Lead exists, current client already attempts `rollback(lead_id, evidence_ids)` in `except`.

### Safety rules

1. Delete **only** records identified by synthetic name + `[CHITU_SYNTHETIC_TEST]` marker (or ids created in this run).  
2. Never delete by broad Lead queries without marker.  
3. Never run against non-localhost hosts (`LocalEspoCRMClient` already enforces localhost:8080).  
4. Prefer evidence-first deletion to avoid orphan relation issues.  
5. If DELETE is forbidden by ACL, **stop and escalate** — do not leave a half-verified green result.

### Manual emergency cleanup (human Admin UI only, if API delete blocked)

1. Search Lead name `Synthetic 3D Dealer Test GmbH`.  
2. Confirm description contains `[CHITU_SYNTHETIC_TEST]`.  
3. Delete linked ResearchEvidence, then Lead.  
4. Record manual cleanup in the execution report.

---

## 6. Risk Points

| Risk | Impact | Mitigation before execution |
|---|---|---|
| ResearchEvidence `delete: no` for API Role | Rollback fails; synthetic data remains | Grant delete for test Role **or** approve admin-only rollback; re-check `App/user` ACL table |
| Lead delete ACL unknown/insufficient | Lead remains after evidence deleted | Confirm Lead delete permission before POST |
| Link POST permission | Evidence created but unlinked | Confirm Role can link Lead↔ResearchEvidence; verify relation GET |
| Duplicate Custom vs Module overlay | Unexpected field/behavior drift | Already audited; monitor verify field mismatches |
| Stale synthetic from prior aborted run | False DUPLICATE / polluted verify | Gate Step A stale cleanup first |
| Non-localhost misconfig | Safety abort | Keep `ESPOCRM_TEST_URL` unset or localhost:8080 |
| Float/datetime formatting | GET verify false fail | Use client converters already in `_evidence_body` / mapper |
| Partial create then process kill | Orphans | Always run rollback in `finally`; manual cleanup checklist if interrupted |
| Treating this as production sync | Real customer pollution | Synthetic domain/name/marker only; no real dealer payloads |

---

## 7. Explicit Non-Goals

- No production EspoCRM  
- No real dealer domains  
- No Account / Opportunity creation  
- No email / SMTP  
- No Sync Contract changes  
- No scoring rule changes  
- No extension refactor (Custom vs Module cleanup) in this phase  
- **This planning document performs no POST/DELETE**

---

## 8. Suggested Execution Command (when explicitly authorized later)

From repo root, with env loaded:

```powershell
cd D:\Chitu-intelligence
# Ensure ESPOCRM_TEST_ENV=true and ESPOCRM_TEST_API_KEY are visible to the process
python -c "from integration.espocrm_sync.real_sync import run_local_synthetic_sync; print(run_local_synthetic_sync())"
```

Do not run that command until:

1. Delete ACL blocker is cleared, and  
2. An explicit Phase 3A-2.4 execution authorization is given.

---

## 9. Planned Deliverables After Execution (future)

| Artifact | Purpose |
|---|---|
| `PHASE3A24_SYNTHETIC_SYNC_TEST_REPORT.md` | Pass/fail per step, ids created, rollback proof |
| Updated final phase report | Auth / create / verify / rollback checklist |

No execution artifacts are produced by this plan-only task.
