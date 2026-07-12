# Phase 3A24 Synthetic Sync Runtime Result

**Date:** 2026-07-11  
**Target:** `http://localhost:8080` only  
**Status:** STOPPED AT EXISTING LEAD CREATE ERROR

## Runtime Verification

| Check | Result |
|---|---|
| `LocalEspoCRMClient` construction | PASS |
| API-key authentication | PASS |
| Existing `preflight()` | PASS |
| Existing sync gate for synthetic payload | PASS |
| Target | Local EspoCRM only |

## Synthetic Sync Attempt

The existing `LocalEspoCRMClient.sync_payload()` was invoked once with the existing synthetic source from `build_synthetic_source()`.

| Step | Result |
|---|---|
| `POST /api/v1/Lead` | FAIL - HTTP 400 Bad Request |
| Lead ID | Not returned |
| ResearchEvidence POST | Not called |
| Lead-to-ResearchEvidence relationship POST | Not called |
| Lead GET field verification | Not available; no Lead ID |
| ResearchEvidence GET verification | Not available; no Evidence ID |
| Relationship GET verification | Not available; no Lead ID |
| Duplicate/idempotency second run | Not attempted after the first-create failure |

The current client intentionally reports only the HTTP status for this failure path. No modification was made to expose or alter the existing client error behavior.

## Rollback and Residue Verification

Because the Lead create response did not return an ID, the existing client did not create or link any downstream entity. A subsequent read-only call to `find_synthetic_lead()` returned no result.

| Check | Result |
|---|---|
| Synthetic Lead residue | NONE |
| Synthetic ResearchEvidence residue | NONE - no Lead was created |
| Rollback API call | Not required; no records existed to delete |
| Real customer data touched | NO |

## Scope Confirmation

- `real_client.py`, authentication, extension metadata, and sync logic were not modified in this phase.
- No real customer, bulk data, email, SMTP, DeepSeek, Apify, or Playwright operation occurred.
- The only mutation attempt was the single authorized synthetic Lead POST, rejected by EspoCRM before record creation.

## Required Next Decision

The HTTP 400 must be diagnosed from the existing local EspoCRM validation response or configuration before another synthetic create attempt. Per task instruction, no client, authentication, extension, or schema change was made automatically.
