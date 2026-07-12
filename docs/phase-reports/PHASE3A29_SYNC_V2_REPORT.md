# Phase3A29 Chitu EspoCRM Sync V2 Report

**Date:** 2026-07-11  
**Scope:** Schema-free Chitu Intelligence to native EspoCRM lifecycle synchronization  
**Verdict:** Runtime, API, duplicate prevention, update, rollback, and regression PASS; authenticated browser record visibility BLOCKED by missing local UI credentials

## Architecture Boundary

EspoCRM remains the CRM system of record. Chitu Intelligence remains the discovery, research, scoring, and recommendation engine.

V2 does not create another CRM store, move scoring or email logic, create custom frontend code, or change EspoCRM schema. It uses existing `Lead.peCandidateId` as the Chitu external ID and existing native conversion relationships as the Account, Contact, and Opportunity mapping.

Native conversion remains a deliberate CRM action. V2 creates or updates a Lead; it does **not** auto-create Account, Contact, or Opportunity records. Until a CRM user converts the Lead, V2 returns `AWAITING_CRM_CONVERSION` for the downstream records.

## Current Sync Architecture Audit

| Area | V1 finding | V2 result |
|---|---|---|
| API endpoints | `App/user`, `Metadata`, Lead, ResearchEvidence, and Lead-to-evidence relationship calls | Adds native Lead conversion plus Account, Contact, and Opportunity read/update/delete calls |
| Authentication | `ESPOCRM_TEST_ENV=true`; localhost-only API key or Basic auth | Unchanged |
| Mapping | Engine payload maps compact intelligence fields to Lead plus ResearchEvidence | Reuses V1 Lead mapping and resolves converted CRM records through native links |
| Error handling | Local-only target validation; HTTP/URL errors converted to client errors; V1 rollback | V2 rejects unsupported entities, duplicate external IDs, and broken conversion links before child writes |
| Duplicate prevention | Contract hash and synthetic-name check; no general runtime Lead upsert | `peCandidateId` external-ID search before Lead create; more than one match is a conflict |

The native CRM conversion endpoint is `POST Lead/action/convert`. The initial V1 client was intentionally Lead/Evidence-only and returned duplicate for the synthetic-name path; it did not provide lifecycle resolution or external-ID upsert for converted records.

## V2 Synchronization Design

### External-ID Mapping

| CRM record | Lookup / native mapping | V2 behavior |
|---|---|---|
| Lead | `Lead.peCandidateId` = Chitu `candidate_id` | Search first; create if absent; update only Chitu-owned Lead fields if one record exists; conflict if more than one matches |
| Account | `Lead.createdAccountId` and `Account.originalLeadId` | Require native conversion link; update Chitu factual company website/country only |
| Contact | `Lead.createdContactId`, `Contact.originalLeadId`, and `Contact.accountId` | Require and verify native conversion links; no direct Chitu contact-field write because the V1 contract has no individual contact identity payload |
| Opportunity | `Lead.createdOpportunityId` and `Opportunity.originalLeadId` | Require native conversion links; update Chitu recommendation snapshot only in `peProductInterest` |

### Source-of-Truth Conflict Strategy

| Chitu-owned / synchronized | EspoCRM-owned / never written by V2 |
|---|---|
| Lead AI score, tier, confidence, evidence coverage, research summary, recommendation, provenance, and sync timestamps | Lead status, owner, teams, activities, and manual CRM workflow data |
| Account website and evidence-backed billing country | Account owner, status, activities, and sales workflow data |
| Opportunity `peProductInterest` as the Chitu recommendation snapshot | Opportunity stage, amount, currency, close date, probability, owner, teams, contacts, activities, and sales progress |
| Native conversion-link verification | Contact identity, owner, activities, and CRM-maintained relationship values |

The service has an explicit forbidden-field guard for `status`, `stage`, `amount`, `amountCurrency`, `closeDate`, `probability`, owner, and team attributes. Unit tests prove these fields are absent from every V2 update body.

## Implementation

| File | Change |
|---|---|
| `integration/espocrm_sync/real_client.py` | Adds allowlisted native CRM record search/read/create/update/delete helpers and native Lead conversion call |
| `integration/espocrm_sync/lifecycle.py` | Adds V2 external-ID upsert, conversion-link validation, ownership allowlists, and conflict handling |
| `integration/espocrm_sync/lifecycle_sync.py` | Adds complete localhost synthetic lifecycle verification with post-delete 404 rollback checks |
| `integration/espocrm_sync/__init__.py` | Exports V2 lifecycle types and runner |
| `tests/test_espocrm_lifecycle_sync.py` | Covers create/pending conversion, converted-record update, duplicate conflict, broken-link conflict, and sales-field protection |
| `tests/test_espocrm_real_client.py` | Covers lifecycle helper entity allowlist |

No EspoCRM metadata, custom fields, database tables, migrations, core files, scoring engine files, or email engine files were changed.

## Validation

### Runtime and API

| Check | Result |
|---|---:|
| `espocrm` container health | PASS |
| `espocrm-db` container health | PASS |
| Local API authentication | PASS |
| V1 Lead + ResearchEvidence sync regression | PASS |
| V2 synthetic lifecycle sync | PASS |

### Synthetic Full Lifecycle

The V2 runner used a unique external ID and performed the following sequence:

1. Search Lead by `peCandidateId`; no match; create one Lead.
2. Confirm downstream records are pending native CRM conversion.
3. Convert that Lead through `Lead/action/convert` into one Account, Contact, and Opportunity.
4. Re-sync V2; update Lead intelligence, Account factual fields, and Opportunity recommendation snapshot.
5. Re-sync changed Chitu intelligence (`score=85.0`, product=`Filament Dryer`, website suffix `/v2`).
6. Verify the same Lead, Account, Contact, and Opportunity IDs remain in use and exactly one Lead matches the external ID.
7. Verify native sales fields remain `stage=Proposal`, `amount=50000`, and `closeDate=2026-09-30`.
8. Delete Opportunity, Contact, Account, and Lead through the API and verify every GET returns HTTP 404.

| Requirement | Result |
|---|---:|
| Synthetic Lead creation | PASS |
| Native Account + Contact + Opportunity conversion | PASS |
| External-ID no-duplicate check | PASS: exactly one matching Lead |
| Lead intelligence update | PASS |
| Account factual update | PASS |
| Contact native-link verification | PASS |
| Opportunity recommendation update | PASS |
| CRM sales-owned field preservation | PASS |
| API rollback and post-delete 404 checks | PASS |

### ACL Configuration for Test Rollback

The local disposable `Chitu Integration Role` already allowed create/read/edit for Account, Contact, and Opportunity. Its local test configuration was updated from `delete=no` to `delete=all` for those three native entities only, then cache was cleared. This is an ACL configuration change, not a database schema change, and allows the required rollback to run through the same API user.

### Automated Tests

```powershell
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client tests.test_espocrm_lifecycle_sync -v
```

| Suite | Result |
|---|---:|
| Extension metadata tests | 16 PASS |
| V1 adapter tests | 20 PASS |
| Real-client safety tests | 10 PASS |
| V2 lifecycle tests | 4 PASS |
| Total | 50 PASS |

## Browser Verification

| Check | Result |
|---|---:|
| Native EspoCRM login screen available | PASS |
| Authenticated Lead/Account/Contact/Opportunity visibility | BLOCKED |

The local environment has an API key but no `ESPOCRM_TEST_USERNAME`/`ESPOCRM_TEST_PASSWORD` or admin browser credentials. No user account was changed solely to bypass this boundary. API verification proves records were created, read, updated, and deleted; authenticated UI visibility remains the only unclosed check.

## Files Changed

- `integration/espocrm_sync/real_client.py`
- `integration/espocrm_sync/lifecycle.py`
- `integration/espocrm_sync/lifecycle_sync.py`
- `integration/espocrm_sync/__init__.py`
- `tests/test_espocrm_real_client.py`
- `tests/test_espocrm_lifecycle_sync.py`
- `docs/espocrm-extension/PHASE3A29_SYNC_V2_REPORT.md`

## Explicit Non-Changes

- No database schema change, migration, or custom metadata field was added.
- No EspoCRM core file was modified.
- No automatic Account, Contact, or Opportunity creation was added.
- No CRM sales stage, amount, close date, owner, team, activity, or status is written by V2.
- No scoring, research-generation, or email-generation logic was modified.
- No custom frontend or React page was created.

## Completion Status

Phase3A29 V2 lifecycle sync is ready for API-backed internal testing. The remaining browser acceptance step needs a disposable local EspoCRM UI session or credentials; no schema or architecture change is needed to complete it.
