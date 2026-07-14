# Phase ACL Verification Report

**Date:** 2026-07-14  
**Target:** isolated local EspoCRM candidate at `http://localhost:8080`  
**Mode:** read-only verification; no ACL, role, entity-permission, workflow, record, or configuration writes were made.

## Freeze disposition

**NOT READY FOR PRODUCTION CANDIDATE FREEZE.**

The three requested role behaviours are present for **Sales User**, **Integration Bot**, and team visibility for **Sales Manager**. However, the live Sales Manager field ACL has drifted from the intended sales field policy: eleven engine-owned Lead fields have no field-level restriction. Because Sales Manager has `Lead.edit=team`, those fields are potentially editable on team records. In addition, an authenticated current-browser rendering check was not run: no existing authenticated browser session was available and no saved credentials were transmitted during this read-only audit.

## Evidence and scope

The isolated runtime was healthy at the time of the check:

| Component | Result |
| --- | --- |
| `espocrm` | healthy; bound to port 8080 |
| `espocrm-db` | healthy |
| `espocrm-daemon` | healthy |
| Role records | Admin, Integration Bot, Sales User, and Sales Manager all present |
| Test identities | `admin`, `integration_bot_test`, `sales_test`, and `manager_test` active |

Runtime inspection read the persisted Role `data` and `fieldData`, User-to-Role and User-to-Team relations, and the active Lead client layout and client metadata from the running EspoCRM container. It did not send create, update, or delete API requests.

## ACL metadata

The extension registers ACL metadata for the custom Prospecting entities. The following active definitions declare their entity in the `Prospecting` ACL group:

- `ResearchEvidence`
- `EmailEvent`
- `SalesFeedback`
- `LearningSignal`
- `SearchStrategy`
- `SearchJob`
- `ProspectPool`

The persisted Role records contain explicit permissions for these scopes. Lead, Account, Contact, Opportunity, Task, Meeting, Call, and Note use the native EspoCRM ACL scopes with persisted Role data.

## Requested-role verification

| Role | Runtime evidence | Result |
| --- | --- | --- |
| Admin | The `admin` user is active with `type=admin`; the Admin role also grants create/read/edit/delete `all` for the reviewed business and Prospecting scopes. | PASS |
| Integration Bot | `integration_bot_test` is an active API user assigned only to Integration Bot. Lead, Account, Contact, Opportunity, ResearchEvidence, EmailEvent, SalesFeedback, SearchStrategy, SearchJob, and ProspectPool have create/read/edit enabled; every reviewed scope has `delete=no`. `exportPermission=no` and `massUpdatePermission=no`. | PASS |
| Sales User business visibility | `sales_test` is active, assigned only to Sales User, and belongs to Sales Team. Lead/Opportunity/Contact have `read=own`, `edit=own`; business, AI, research, proposal, and email summary fields are readable and engine-owned fields are non-editable. | PASS |
| Sales User technical-field protection | Seven sync/technical fields are all persisted as `read=no, edit=no`: `peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`, `peEngineVersion`, `peScoreRulesVersion`, and `peSourceBatchId`. | PASS |
| Sales Manager team visibility | `manager_test` is active, assigned only to Sales Manager, and belongs to the same Sales Team as `sales_test`. Lead, Account, Contact, Opportunity, Task, Meeting, Call, and Note have `read=team`, `edit=team`, and (where applicable) `stream=team`; delete is denied. | PASS |

Integration Bot delete-disablement is verified directly from the current persisted ACL values. No DELETE request was issued, so the audit did not risk changing data merely to prove an expected denial.

## Client visibility

The active Lead list layout is sales-facing: it contains `name`, geography, score/tier, recommended product, research status, outreach status, next follow-up, email status, and priority. It does not contain a sync/technical field.

The active Lead detail layout contains business sections for Intelligence Summary, Pipeline, Opportunity Proposal, Sales Activity, Email Status, and AI Research Information. The standard relationship panels also prevent creation of Research Evidence, Email Events, and Learning Signals; Sales Feedback and Tasks are the only reviewed panels configured to allow creation.

The layout also contains a `Sync Information` section with the seven protected fields plus `peQualificationStatus`. For Sales User, the seven protected fields are removed by field ACL at runtime. `peQualificationStatus` is intentionally readable but non-editable, so the exact visual handling of the section heading requires an authenticated browser session to confirm.

**Client configuration result: PASS for list/detail field policy; browser-render acceptance: DEFERRED.**

## Freeze blocker: Sales Manager field-ACL drift

The current Sales Manager Lead field map is not equivalent to Sales User's engine-owned field policy. The following fields are restricted for Sales User but absent from Sales Manager `fieldData.Lead`:

| Missing Sales Manager field rule | Risk under current `Lead.edit=team` |
| --- | --- |
| `peSourceBatchId` | Technical sync/batch identifier can be exposed and may be editable on team records. |
| `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` | Engine-projected email summary values may be editable. |
| `peLastResearchedAt` | Engine-owned research timestamp may be editable. |
| `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalEligibility`, `peProposalSuggestedNextAction`, `peProposalAction` | Proposal projection values may be editable. |

This is a runtime configuration finding, not an inferred source-code issue. It contradicts the earlier intended policy that sales roles use the same Lead field protections. No corrective change was made, in accordance with this phase's prohibition on ACL or role changes.

## Required actions before freeze

1. Reconcile the Sales Manager Lead `fieldData` with the approved engine-owned-field policy, including the eleven fields above, through the approved change-control process.
2. Run a clean authenticated browser verification for Sales User and Sales Manager after reconciliation. Confirm that technical fields cannot be viewed or edited by Sales User, that business information remains visible, and that the Manager sees a Sales Team record without a browser/client error.
3. Re-run this read-only verification and attach the resulting role/field ACL export to the candidate-freeze evidence.

## Non-changes

- No ACL metadata was changed.
- No role, user, team, entity permission, or workflow was changed.
- No customer data was imported and no outreach was enabled.
- Existing unrelated working-tree changes were left untouched.
