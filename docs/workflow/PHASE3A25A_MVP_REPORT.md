# Phase 3A25a MVP CRM Workflow Report

**Date:** 2026-07-11  
**Target:** `http://localhost:8080` local EspoCRM test instance only  
**Status:** PASS

## Scope Delivered

The EspoCRM `Lead` metadata now contains the Phase 3A25a MVP workflow fields only. No outreach automation, workflow rule, or new CRM entity was implemented.

| Field | Type | Definition |
|---|---|---|
| `outreachStatus` | `enum` | `DISCOVERED`, `RESEARCH_COMPLETED`, `QUALIFIED`, `OUTREACH_READY`, `CONTACTED`, `REPLIED`, `OPPORTUNITY`, `WON`, `LOST` |
| `lastContactAt` | `datetime` | Nullable contact timestamp. |
| `nextFollowUpAt` | `datetime` | Nullable next follow-up timestamp. |
| `leadSourceEngine` | `varchar(64)` | Nullable source-engine identifier. |
| `syncVersion` | `varchar(64)` | Nullable sync-version identifier. |

All five fields are optional and nullable. Existing scoring fields and the `ResearchEvidence` entity were not changed.

## Extension Files Changed

| File | Purpose |
|---|---|
| `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Lead.json` | Runtime Lead field metadata deployed to EspoCRM. |
| `espocrm_extension/Resources/entityDefs/Lead.json` | Source extension definition kept in parity with runtime metadata. |
| `espocrm_extension/tests/test_extension_skeleton.py` | Metadata assertions for the five approved workflow fields. |

## Deployment and ACL

1. Deployed the existing `Prospecting` custom module to the local container custom mount.
2. Ran `php command.php rebuild` in the local `espocrm` container.
3. No additional ACL metadata was needed: the existing test API user can already read standard `Lead` metadata, and all five fields are visible through that inherited Lead access.
4. No ACL, API authentication, or role setting was changed.

## Runtime Verification

| Check | Result |
|---|---|
| Extension structure tests | PASS (`13` tests) |
| API-key `authenticate()` | PASS |
| Existing `preflight()` | PASS |
| `outreachStatus` visible as `enum` | PASS |
| `outreachStatus` values match approved list | PASS |
| `lastContactAt` visible as `datetime` | PASS |
| `nextFollowUpAt` visible as `datetime` | PASS |
| `leadSourceEngine` visible as `varchar` | PASS |
| `syncVersion` visible as `varchar` | PASS |

The live Lead metadata returned `61` fields, including all five new MVP fields.

## Explicitly Not Implemented

- No `EmailDraft`, `Campaign`, or `Activity` entity.
- No outbound email or automatic sending.
- No complex workflow rules or outreach orchestration.
- No changes to `real_client.py`, sync architecture, API authentication, scoring fields, or `ResearchEvidence`.
- No Lead, ResearchEvidence, activity, campaign, or other business data was created during this phase.
