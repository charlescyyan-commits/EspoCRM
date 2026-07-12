# Phase3A26 Sales Activity Workflow Report

**Date:** 2026-07-11  
**Verdict:** PASS  
**Scope:** Native EspoCRM Lead sales workflow, activity records, follow-up fields, Lead detail layout, validation report.

## Workflow Design

EspoCRM remains the sales operation system. Chitu Intelligence remains responsible for discovery, research, scoring, product recommendation, and email generation.

Phase3A26 separates sales lifecycle state from technical Engine state:

| Concern | Field | Owner | Values |
|---|---|---|---|
| CRM sales lifecycle | `Lead.status` | EspoCRM sales users | `New`, `Reviewed`, `Contacted`, `Interested`, `Qualified`, `Converted`, `Rejected` |
| Sync technical state | `peSyncStatus` | Chitu/Espo sync path | `PENDING`, `SYNCED`, `FAILED` |
| Research technical state | `peResearchStatus` | Chitu research/sync path | `NONE`, `RESEARCHING`, `COMPLETED`, `FAILED` |

Sales activities use native EspoCRM entities only:

- `Task`
- `Note`
- `Call`
- `Meeting`
- `Email` records only; no send action or external mail provider was connected or invoked.

No custom activity entity was created.

## Fields Added

Added the two required nullable native Date fields to Lead:

| Field | Type | Nullable | Purpose |
|---|---|---:|---|
| `peNextActionDate` | `date` | yes | CRM-owned next sales action date |
| `peLastContactDate` | `date` | yes | CRM-owned last contact date |

Runtime DB verification after EspoCRM rebuild:

| Column | DB type | Nullable |
|---|---|---:|
| `pe_next_action_date` | `date` | yes |
| `pe_last_contact_date` | `date` | yes |

Existing score/research/sync fields remain present:

- `pe_opportunity_score_v4`
- `pe_score_tier`
- `pe_best_first_product`
- `pe_sync_status`
- `pe_research_status`

## Layout Changes

Updated native Lead detail layout with a new section:

**Sales Activity**

| Row | Fields |
|---|---|
| 1 | `status`, `assignedUser` |
| 2 | `peNextActionDate`, `peLastContactDate` |

Existing sections remain:

- `Lead Intelligence Summary`
- `AI Research Information`
- `Sync Information`
- `Contact & Ownership`

`Lead.status` was moved out of the intelligence summary and into the new sales activity section. Intelligence summary keeps score, tier, product recommendation, and confidence.

## Role / ACL Updates

Updated the local test EspoCRM Role `Chitu Integration Role` so native activity workflow can be validated through the test API user:

| Entity / Permission | Final setting |
|---|---|
| `Task.create/read/edit/delete` | `yes/all/all/all` |
| `Note.create/read/edit/delete` | configured as `yes/all/all/all`; API reports own scoped note ACL |
| `Call.create/read/edit/delete` | `yes/all/all/all` |
| `Meeting.create/read/edit/delete` | `yes/all/all/all` |
| `Email.create/read/edit/delete` | `yes/all/all/all` |
| `Lead.stream` | `all` |
| `assignment_permission` | `all` |

Native ACL was not bypassed. An attempted cross-user assignment to `admin` returned HTTP 403, so final validation used assignment to the test API user itself. This confirms ACL enforcement remains active.

## Functional Test Results

Synthetic marker used:

```text
[CHITU_PHASE3A26_TEST]
```

Functional validation through the EspoCRM API user `chitu_ai_connector`:

| Check | Result |
|---|---|
| Create synthetic Lead | PASS: `6a522392f18fcc7a1` |
| Initial Lead status | PASS: `New` |
| Change status to `Reviewed` | PASS |
| Change status to `Contacted` | PASS |
| Change status to `Interested` | PASS |
| Change status to `Qualified` | PASS |
| Change status to `Rejected` | PASS |
| Assigned User set on Lead create | PASS: `6a511ae1064b220a5` |
| Set `peNextActionDate` | PASS: `2026-07-25` |
| Set `peLastContactDate` | PASS: `2026-07-11` |
| Create native Task | PASS: `6a522393598e099df` |
| Create native Note | PASS: `6a52239373e22f70b` |
| Create native Call | PASS: `6a5223938d9855500` |
| Create native Meeting | PASS: `6a522393a7e52b173` |
| Delete synthetic Task/Note/Call/Meeting/Lead via API | PASS, GET after delete returned HTTP 404 |

Email validation was limited to metadata/ACL visibility. No Email POST/send action was executed.

## Regression Verification

Command:

```powershell
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client -v
```

Result:

| Suite | Result |
|---|---|
| `espocrm_extension.tests.test_extension_skeleton` | 14 PASS |
| `tests.test_espocrm_sync_adapter` | 20 PASS |
| `tests.test_espocrm_real_client` | 9 PASS |
| Total | 43 PASS |

Existing synthetic sync/rollback still works:

| Check | Result |
|---|---|
| `run_local_synthetic_sync()` | PASS |
| Synthetic Lead created | `6a5223a8db4dcb7ab` |
| Synthetic ResearchEvidence created | `6a5223a8e73761f69` |
| Rollback cleanup | PASS |

Post-validation active residue:

| Check | Count |
|---|---:|
| Active Phase3A26 synthetic Leads | 0 |
| Active Phase3A26 synthetic Tasks | 0 |
| Active Phase3A26 synthetic Notes | 0 |
| Active Phase3A26 synthetic Calls | 0 |
| Active Phase3A26 synthetic Meetings | 0 |
| Active sync synthetic Leads | 0 |
| Active sync synthetic ResearchEvidence | 0 |
| Active business Leads | 4 |

## Files Changed

Repository files changed:

- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Lead.json`
- `espocrm_extension/Resources/entityDefs/Lead.json`
- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/Lead/detail.json`
- `espocrm_extension/Resources/layouts/Lead/detail.json`
- `espocrm_extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Lead.json`
- `espocrm_extension/tests/test_extension_skeleton.py`
- `docs/espocrm-extension/PHASE3A26_SALES_ACTIVITY_WORKFLOW_REPORT.md`

Runtime EspoCRM local test environment updates:

- Copied updated Lead entityDefs/layout/i18n metadata into the local EspoCRM container.
- Ran `php rebuild.php`.
- Ran `php clear_cache.php`.

## Explicit Non-Changes

- No custom frontend was created.
- EspoCRM UI was not replaced.
- No React page was built.
- Scoring logic was not moved into EspoCRM.
- Email generation was not moved into EspoCRM.
- Chitu Intelligence scoring engine was not modified.
- Phase3A24 sync foundation code was not modified.
- No custom activity entity was created.
- No real email send provider was connected.
- No email send action was invoked.

## Recommendation

PASS. Phase3A26 MVP native sales activity workflow is ready for internal CRM testing. Recommended next order:

1. Manual EspoCRM UI smoke test for the Lead detail section and activity panels.
2. Sales-user Role review separate from the API test Role.
3. Later phase: record-only Email draft display/association, still without provider send until explicitly approved.
