# Phase 3A24 Lead POST 400 Root Cause

**Date:** 2026-07-11  
**Target:** `http://localhost:8080` only  
**Scope:** Existing `integration/espocrm_sync/` adapter and one synthetic runtime attempt

## Verdict

The original `POST /api/v1/Lead` failure was a native EspoCRM `Lead` name-field validation failure, not an Extension schema, authentication, enum, numeric-type, or create-ACL failure.

The smallest adapter correction was applied: the existing synthetic company name is also supplied as EspoCRM's native `lastName` component. No Extension, field definition, authentication, or architecture was changed.

## Captured HTTP 400 Response

The original request used the existing `_lead_body()` output. EspoCRM returned:

```text
HTTP 400 Bad Request
X-Status-Reason: Field validation failure; entityType: Lead, field: name, type: required.

{"messageTranslation":{"label":"validationFailure","scope":null,"data":{"field":"name","type":"required"}}}
```

The request had supplied a string `name` value:

```json
{
  "name": "Synthetic 3D Dealer Test GmbH"
}
```

## `_lead_body()` vs. Live Lead Metadata

| Field | Existing value | Live EspoCRM metadata | Result |
|---|---|---|---|
| `name` | `"Synthetic 3D Dealer Test GmbH"` | `personName` | Invalid write shape for the required native name field; string did not satisfy validation. |
| `lastName` | Missing | Native `varchar` name component | Required in practice to satisfy the `personName` validation for this synthetic company Lead. |
| `website` | Synthetic HTTPS URL | `url` | Valid. |
| `peOpportunityScoreV4` | `80.0` | `float`, range `0..100` | Valid. |
| `peConfidence` | `1.0` | `float`, range `0..1` | Valid. |
| `peEvidenceCoverage` | `0.75` | `float`, range `0..1` | Valid. |
| `peScoreTier` | `"A"` | `enum`: `""`, `A`, `B`, `C` | Valid. |
| `peQualificationStatus` | `"OUTREACH_READY"` | `varchar` | Valid. |
| Product and version fields | Existing synthetic strings | `varchar` | Accepted by the successful retry. |

## Minimal Correction

Changed only the existing adapter payload construction:

```python
body["lastName"] = body["name"]
```

Location: `integration/espocrm_sync/real_client.py` in `_lead_body()`.

The focused client test was updated to assert that the required native component is included and matches the synthetic `name` value. No `_LEAD_FIELDS` contract field, CRM field design, Extension metadata, authentication setting, or sync architecture changed.

## Validation After Correction

| Check | Result |
|---|---|
| API-key authentication | PASS |
| Existing `preflight()` | PASS |
| `POST /api/v1/Lead` | PASS |
| Synthetic Lead ID | `6a518bfc1927182bb` |
| `POST /api/v1/ResearchEvidence` | PASS |
| Synthetic ResearchEvidence ID | `6a518bfc2e154ca1f` |
| Lead-to-ResearchEvidence relationship POST | PASS |
| Lead GET field consistency | PASS |
| Relationship GET consistency | PASS |
| Focused unit tests | PASS (`9` tests) |

The successful runtime retry proves the original 400 was resolved by the `lastName` mapping. It also proves there is no Lead create ACL block and no invalid custom-field type or enum value in this synthetic payload.

## Separate Rollback ACL Blocker

Rollback could not complete because the API user lacks delete access for `ResearchEvidence`.

```text
DELETE /api/v1/ResearchEvidence/6a518bfc2e154ca1f
HTTP 403 Forbidden
X-Status-Reason: No delete access.
Response body: <empty>
```

The existing rollback stops at the evidence delete, so the following **synthetic-only** records remain in the local test CRM:

| Entity | ID |
|---|---|
| Lead | `6a518bfc1927182bb` |
| ResearchEvidence | `6a518bfc2e154ca1f` |

No real customer or batch data was created. No ACL, authentication, Extension, or schema change was made to bypass the 403. A local EspoCRM administrator must either remove these two synthetic records or grant the test API user delete permission for `ResearchEvidence` before a rollback-complete runtime run can pass.

## Scope Confirmation

- No change to EspoCRM Extension architecture or entity/field definitions.
- No change to API-key authentication.
- No real customer, bulk data, or production target used.
- No change to `real_client.py` beyond the minimal native `lastName` request mapping required by the captured 400 response.
