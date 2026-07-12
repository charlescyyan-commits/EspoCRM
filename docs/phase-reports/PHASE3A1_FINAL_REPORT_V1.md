# Phase 3A-1 - Prospecting Engine to EspoCRM Sync Contract Design V1

**Status:** COMPLETE - design only  
**Date:** 2026-07-10

## Delivered Artifacts

1. `ESPOCRM_SYNC_CONTRACT_BOUNDARY_V1.md`
2. `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md`
3. `ESPOCRM_SYNC_CONTRACT_V1.json`
4. `ESPOCRM_SYNC_RULES_V1.md`
5. `ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md`
6. `ESPOCRM_SYNC_TEST_PLAN_V1.md`
7. `PHASE3A1_FINAL_REPORT_V1.md`

## Key Decisions

- Prospecting Engine remains the source of truth for qualification, V4 score, recommendation, and evidence.
- EspoCRM remains the human-review and sales-execution layer.
- Synchronization is one-way: Engine to EspoCRM only.
- A future import creates/updates only Lead and structured `ResearchEvidence` records.
- Account creation/conversion and Opportunity creation are human-only CRM actions.
- Import eligibility requires `OUTREACH_READY`, Canonical Scoring V4, score tier A/B/C, coverage at least 0.50, confidence at least 0.60, compact evidence, no official-brand exclusion, and no technical failure.
- V3 records are rejected by the V1 CRM contract; no V3/V4 mixing is allowed.
- Canonical-domain identity, idempotency key, payload hash, and immutable snapshot provenance prevent duplicate records and unsafe overwrites.

## Validation

| Check | Result |
|---|---|
| Required design files produced | PASS |
| Contract contains required/optional/nullable field definitions | PASS |
| Lead, Account, Opportunity, and Evidence mappings defined | PASS |
| Official-brand, V3/V4, technical-failure, and duplicate protections defined | PASS |
| Sync authorization and rollback behavior defined | PASS |
| JSON schema parse validation | PASS |
| Real EspoCRM, database, API, email, or provider operation | NOT PERFORMED |

## Final Acceptance

| Question | Answer |
|---|---|
| Sync Contract Designed | YES |
| Engine remains source of truth | YES |
| CRM remains execution layer | YES |
| Lead mapping completed | YES |
| Account mapping completed | YES - human conversion only |
| Opportunity rules completed | YES - human creation only |
| Evidence mapping completed | YES - custom `ResearchEvidence` entity recommended |
| Version strategy completed | YES |
| Idempotency strategy completed | YES |
| Official brand protection included | YES |
| V3/V4 separation included | YES |
| Real EspoCRM modified | NO |
| Database modified | NO |
| External API called | NO |
| Emails sent | NO |
| Permit Phase 3A-2 EspoCRM Extension Implementation | YES - contract-design prerequisite is complete; separate explicit implementation authorization remains required. |

## Scope Confirmation

Only new documentation and one JSON Schema contract under `docs/espocrm-extension/` are part of this phase. No Engine scoring rules, data, CRM instance, extension code, UI, API, queue, provider, or email behavior was changed.
