# Phase3B06.1 — Complete Connector Projection Report

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Runtime:** local EspoCRM-Test Docker stack only (`http://localhost:8080`)  
**Extension:** Chitu Prospecting Integration `1.6.1-alpha`  
**Status:** **PASS**

## 1. Architecture

`ProspectingConnectorClient.sync_source(source)` is now the single live orchestration path:

```text
V1 payload build
  -> V1 structural validation
  -> evaluate_sync_gate
  -> POST /Prospecting/sync/lead
  -> POST /Prospecting/sync/evidence
  -> POST /Prospecting/sync/opportunity-proposal
```

- It uses the existing `EspoCRMSyncMapper`, `validate_sync_contract`, `evaluate_sync_gate`, and the existing three Prospecting routes.
- Structural validation or gate rejection returns a structured failed result before any HTTP write.
- A transport error is re-raised; a `success=false` endpoint response returns a failed result and stops later steps. No partial execution is reported as overall success.
- No second mapper, gate, API surface, scoring engine, AI engine, UI, database schema, Docker Compose, or Opportunity creation path was added.

## 2. Mapping

`ChituSyncService::leadFields` retains the V1-backed Lead projection for score, tier, product, confidence, coverage, research status, last researched timestamp, and sync status.

The missing display projections are now deterministic and use only V1 fields:

| Lead field | Source |
|---|---|
| `peResearchSummary` | `company.name`, `score.value`, `score.score_tier`, `recommendation.best_first_product`, `score.evidence_coverage` |
| `peKeyEvidence` | First five non-empty V1 `evidence[].claim` values with their `claim_type`; null if none exist |
| `peRecommendedApproach` | Existing V1 `recommendation.best_first_product`; null if absent |

No score, tier, product, evidence, AI output, or recommendation is invented or recalculated.

## 3. API

- V1 contract was not changed; `docs/sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json` has no Phase3B06.1 edit.
- Existing authenticated routes remain unchanged:
  - `POST /api/v1/Prospecting/sync/lead`
  - `POST /api/v1/Prospecting/sync/evidence`
  - `POST /api/v1/Prospecting/sync/opportunity-proposal`
- The local real validation used a disposable API user and `X-Api-Key` only.
- A real anonymous `POST /api/v1/Prospecting/sync/lead` returned `401`.

## 4. Idempotency

Real local validation used `[CHITU_PHASE3B06_1_TEST]` and the same source twice through `sync_source()`:

| Step | First sync | Second sync |
|---|---|---|
| Lead | created | updated; same Lead ID |
| ResearchEvidence | one created | one additional record created |
| Opportunity Proposal | updated Lead metadata only | updated Lead metadata only |

The observed Evidence count after the second sync was `2`. This is the existing Phase3B03 append-only contract: evidence is not de-duplicated by `peEvidenceId` on rerun. No CRM `Opportunity` was created.

## 5. Security

- Connector construction requires an absolute HTTP(S) URL and non-empty API key.
- Runtime anonymous route check returned `401`.
- Invalid V1 tier and empty V1 evidence were rejected before HTTP writes in the real `sync_source()` validation.
- The disposable API identity used the existing `Integration Bot` role and was removed after validation.

## 6. Validation Results

| Validation | Result |
|---|---|
| Extension package | PASS — `deployment/prospecting-extension-1.6.1-alpha.zip` |
| Package SHA-256 | `E73F61B072C3768EE5F09400DDB0A624401EC712EE2572E02ACF29AE758C4FA0` |
| Install / rebuild / cache clear | PASS — installed `1.6.1-alpha` in local Docker EspoCRM only |
| Runtime PHP lint | PASS — `ChituSyncService.php` |
| Focused regressions | PASS — 69 tests |
| Full connector regressions | PASS — 58 tests |
| Full extension regressions | PASS — 34 tests |
| Valid `sync_source()` | PASS — Lead, Evidence, Proposal executed in order with successful responses |
| Duplicate `sync_source()` | PASS — one Lead, append-only Evidence count `2` |
| Invalid tier / empty evidence | PASS — rejected with zero Lead writes |
| Lead projection | PASS — summary, key evidence, approach, tier, product, confidence and coverage were non-empty and correct |
| Opportunity boundary | PASS — `NO_AUTOMATIC_OPPORTUNITY`; marker Opportunity count `0` |
| Browser Lead detail | PASS — marker Lead showed score `80`, tier `A`, product `Resin Tank`, all three projected text fields, and Proposal Action `NO_AUTOMATIC_OPPORTUNITY` |
| Browser Evidence panel/detail | PASS — panel displayed two append records; detail showed claim, source URL, evidence text, confidence, captured timestamp, and Lead relation |
| Cleanup | PASS — marker Lead/Evidence GETs returned `404`; marker Lead, Evidence, Opportunity, and temporary API-user counts were all `0` |

The browser validation used `sales_test`. Because its existing ACL is `own`, the marker Lead and its two marker Evidence records were temporarily assigned to that user after connector validation solely to display the already-created records. Those assignments and all marker records were removed during cleanup; no role or ACL was modified.

## 7. Limitations

1. ResearchEvidence remains append-only by the established Phase3B03 behavior. Repeating a source adds another Evidence record; it does not perform evidence-level de-duplication.
2. V1 carries no CRM owner or team. With the existing Sales `own` ACL, production ownership/team assignment must be handled by an approved CRM process if Sales users must view connector-created records. This phase deliberately did not change ACL, roles, V1, or assignment policy.
3. This phase does not create Opportunities, run AI/scoring in EspoCRM, send email, or enter Phase3B07.

## 8. Files Changed for This Phase

- `chitu-connector/chitu_connector/espocrm_sync/connector_api.py`
- `chitu-connector/chitu_connector/espocrm_sync/gate.py`
- `chitu-connector/tests/test_espocrm_connector_api.py`
- `chitu-connector/tests/test_espocrm_sync_adapter.py`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ChituSyncService.php`
- `crm-extension/manifest.json`
- `crm-extension/tests/test_extension_skeleton.py`
- `deployment/provisioning/phase3b06_1_provision_connector_test_user.php`
- `deployment/provisioning/phase3b06_1_cleanup_validation_records.php`

The two provisioning files are test-only support required for the authorized local API identity and guaranteed marker cleanup. Existing Phase3B06 workspace artifacts already present in the worktree were not altered by this phase.
