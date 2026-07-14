# Phase T05 - Metadata Contract Audit

**Date:** 2026-07-14  
**Mode:** Read-only audit; documentation output only  
**Scope:** `Lead.peOpportunityScoreV4` and `Lead.peBestFirstProduct`

## Verdict: RESTORE METADATA

The expectation is **not obsolete**. Both fields remain part of the active Lead intelligence contract, C08 score-projection allowlist, runtime-client preflight/update allowlist, workflow/read-model metadata, and feedback traceability.

The reported T05 failure did **not** show missing Lead `entityDefs` fields. Its assertion checks the fields displayed in the `Opportunity Proposal` section of the Lead detail layout. At the time of the failed gate that layout did not expose the two fields; at audit time the current layout contains them and the exact previously failing test passes.

Therefore, if this mismatch recurs, restore the existing layout metadata (in both extension surfaces). Do not remove the test expectation, shrink the C08 projection allowlist, or redefine the connector contract without an explicitly authorized contract change.

## Direct Evidence

| Surface | `peOpportunityScoreV4` | `peBestFirstProduct` | Result |
|---|---|---|---|
| `crm-extension/Resources/entityDefs/Lead.json` | `float`, 0--100, nullable | `varchar`, max 255, nullable | Present |
| `crm-extension/files/.../metadata/entityDefs/Lead.json` | Same definition | Same definition | Present |
| `crm-extension/Resources/layouts/Lead/detail.json` | Opportunity Proposal row | Opportunity Proposal row | Present |
| `crm-extension/files/.../Resources/layouts/Lead/detail.json` | Opportunity Proposal row | Opportunity Proposal row | Present |
| Lead list layout | Present | Present | Present |
| Prospecting Intelligence dashlet | Sort/display field | Display field | Present |
| clientDefs / ACL metadata | No field-specific reference | No field-specific reference | No conflicting ACL/client definition found |

The exact test that failed in the previous T05 run is:

```text
crm-extension.tests.test_extension_skeleton.ExtensionSkeletonTests
  .test_phase3b03_connector_routes_and_proposal_model
```

It collects field names from the `Opportunity Proposal` layout section; it does not assert the fields are absent from `entityDefs`. Re-running that individual test during this audit passed. Re-running the complete Extension suite also passed: **57/57**.

## Field Ownership

| Field | Intended purpose | Primary writer / owner | Other controlled writer | Readers |
|---|---|---|---|---|
| `peOpportunityScoreV4` | Persist the accepted canonical opportunity score on an existing Lead. | C08 `CRMScoreProjectionAdapter`, mapping `CanonicalScoreResult.opportunity_score`; `LocalEspoCRMClient.update_lead_score_projection` permits it. | Existing V1 bridge `ChituSyncService::leadFields()` and `syncOpportunityProposal()` copy the contract score; they do not calculate a score. | Proposal/detail/list/dashlet metadata; Lead formula and `LeadWorkflowHook` high-score rule; `PeScoreWithoutTier` filter; `SalesFeedbackLearningSignalHook` prediction snapshot. |
| `peBestFirstProduct` | Persist the direct canonical first-product recommendation, when present. | C08 `CRMScoreProjectionAdapter`, mapping `CanonicalScoreResult.best_first_product` only when non-empty. | Existing V1 bridge `ChituSyncService::leadFields()` and `syncOpportunityProposal()` copy the recommendation. | Proposal/detail/list/dashlet metadata; `PeMissingBestFirstProduct` filter; `EmailEventSalesFeedbackHook` product attribution. |

`ChituSyncService::syncOpportunityProposal()` writes both fields together with the proposal fields only after `score >= 80`, while retaining `NO_AUTOMATIC_OPPORTUNITY`. This is projection of contract data, not authority to create an Opportunity or replace canonical scoring.

## C08 Score Projection Contract

`chitu_connector.espocrm_sync.crm_score_projection` defines this four-field allowlist:

```text
peOpportunityScoreV4
peScoreTier
peBestFirstProduct
peScoreRulesVersion
```

Its direct mapping is:

| Canonical result | Lead field | Requirement |
|---|---|---|
| `opportunity_score` | `peOpportunityScoreV4` | Required accepted score, range 0--100 |
| `score_tier` | `peScoreTier` | Required accepted tier |
| `best_first_product` | `peBestFirstProduct` | Optional only when direct, non-empty canonical output exists |
| `canonical_engine_version` | `peScoreRulesVersion` | Required provenance |

The same four fields are enforced by `LocalEspoCRMClient.update_lead_score_projection`; a field outside this allowlist is rejected before HTTP. C08 tests assert the complete mapping, and the C08.3 report records this as the frozen existing-Lead-only projection boundary.

Consequently, deleting either field from CRM metadata would make a valid accepted C08 result fail CRM projection or lose canonical traceability. Changing the test instead would hide that contract break.

## C09 Outreach Preparation Check

C09 does **not** read these values back from CRM metadata. `DeterministicOutreachInputAdapter` accepts the same `CanonicalScoreResult` directly and produces:

- `score_tier` from the canonical result;
- `recommended_product` from `CanonicalScoreResult.best_first_product`.

It imports no CRM client and performs no Lead write. Thus C09 does not have a runtime read-after-write dependency on `Lead.peOpportunityScoreV4` or `Lead.peBestFirstProduct`.

It does have a semantic dependency: `recommended_product` is the same direct canonical recommendation that C08 persists as `peBestFirstProduct`. Retaining the CRM field preserves the corresponding sales-review, feedback, filtering, and email-event attribution record without making C09 an email or CRM workflow owner.

## Reference Inventory

| Area | Finding |
|---|---|
| entityDefs | Both fields are defined in both extension metadata surfaces. |
| layouts | Both fields are in Lead detail, list, and the Opportunity Proposal section; the latter was the failed test's actual target. |
| clientDefs | No direct field-specific clientDefs entry; no contradictory client configuration found. |
| ACL | No field-specific ACL definition found; ordinary Lead/entity access controls apply. |
| connector projection | C08 allowlist and local client both include both fields; C08 tests verify projection. |
| legacy connector bridge | PHP service copies both direct payload values, including the `score >= 80` proposal projection path. |
| workflow / feedback | Score drives priority/task behavior and prediction snapshots; product is used for filters and email-event feedback attribution. |
| tests | Extension contract/layout test, C08 projection test, sync adapter test, and runtime/lifecycle tests reference the score; C08 tests reference both fields. |
| reports | Phase3B03, C08.3, C09.1, production-readiness, and global boundary reports consistently preserve the fields as Lead intelligence/projection fields. |

## Audit Commands and Results

```powershell
rg -n -i -C 3 "peOpportunityScoreV4|peBestFirstProduct" .

python -m unittest crm-extension.tests.test_extension_skeleton.ExtensionSkeletonTests.test_phase3b03_connector_routes_and_proposal_model -v
# PASS: 1/1

python -m unittest discover -s crm-extension\tests -p 'test_*.py' -v
# PASS: 57/57
```

No CRM, database, external provider, production data, metadata, test, connector, score, workflow, or UI file was modified by this audit.

## Required Follow-up

No contract/test update is justified. Before the next baseline gate, ensure both extension package surfaces retain the two fields in the `Opportunity Proposal` detail layout, then run the normal T05 regression gate. Any further decision about changing the four-field C08 projection contract requires explicit connector-contract authority.
