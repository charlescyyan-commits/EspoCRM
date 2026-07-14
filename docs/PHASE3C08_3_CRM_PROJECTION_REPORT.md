# Phase3C08.3 — CRM Score Projection Report

## Status

**PASS — projection boundary implemented and validated.**

No commit was created.

## Scope Delivered

Implemented a connector-side, existing-Lead-only score projection boundary:

- `CRMScoreProjectionAdapter` accepts an existing Lead ID and a C08.2
  `CanonicalScoreResult`.
- `LocalEspoCRMClient.update_lead_score_projection` updates only an explicit
  allowlist of existing Lead fields.
- Invalid, missing, or unaccepted score results are skipped before a CRM call.
- CRM permission denial returns a structured `DENIED` result; it neither
  retries nor invokes any other CRM operation.

## Field Projection

| Canonical result field | Existing Lead field | Rule |
| --- | --- | --- |
| `opportunity_score` | `peOpportunityScoreV4` | Required numeric score in the existing 0–100 range. |
| `score_tier` | `peScoreTier` | Required existing Lead tier (`A`–`D`). |
| `best_first_product` | `peBestFirstProduct` | Included only when direct, non-empty canonical output is available. |
| `canonical_engine_version` | `peScoreRulesVersion` | Required canonical score-rule/version provenance. |

The adapter does not infer or create research narrative.  It leaves
`peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`, and
`peEngineVersion` untouched because C08.2 provides no direct canonical value
for those fields.

## Safety and Ownership Boundaries

- Only `PUT Lead/{id}` is available through this projection method; no Lead
  creation method is exposed or called.
- The local client rejects every field outside the four-field projection
  allowlist before issuing a request.
- No Opportunity creation, email operation, scoring-rule change, evidence
  schema change, workflow change, or API-contract change was made.
- Canonical scoring remains outside this adapter.  The adapter only validates
  and projects an already accepted `CanonicalScoreResult`.

## Validation

### C08.3 unit tests

`chitu-connector.tests.test_phase3c08_crm_score_projection` — **4 passed**

- complete direct mapping;
- missing or unaccepted score data skips the CRM update;
- permission denial is contained with no retry or entity mutation;
- projection body contains no unrelated Lead fields.

### Focused boundary regression

The C08.3 tests plus C08.1/C08.2, C07 extraction/persistence/gate/runtime, and
C06 ResearchEvidence boundary tests completed successfully: **61 passed**.

### Core Regression Gate

`scripts/testing/run-regression-gate.ps1` — **PASS**

| Suite | Result |
| --- | --- |
| Extension | 57 passed |
| Connector | 86 passed |
| Worker | 31 passed |
| Static | 2 passed |
| Overall | PASS (5/5 required suites) |

Result artifact:
`temp/test-results/regression-gate-20260713-235944-868.json`

Python compilation for the new projection adapter and the modified local CRM
client also passed.

## Runtime Note

This phase uses isolated client doubles only.  No live CRM write was run,
which avoids modifying any existing Lead while the requested scope is limited
to the projection adapter.
