# Phase Browser Regression Round 2

**Date:** 2026-07-14  
**Target:** isolated EspoCRM runtime at `http://localhost:8080`  
**Mode:** browser and read-only metadata verification. No code, ACL, role, record, workflow, or test-data change was made.

## Verdict

**PARTIAL PASS — Sales User and Sales Manager UI regression checks pass; Admin coverage is blocked by unavailable current credentials; UI metadata drift remains open.**

The C10.6 ResearchEvidence metadata is active in the runtime. Sales User and Sales Manager completed real authenticated browser checks without console warnings or errors. Admin dashboard, Admin Lead, Admin ResearchEvidence, and Admin email-lifecycle checks were not attempted after the configured initial Admin password was rejected; no password reset or user change was made.

## Test boundaries

- Existing identities only: `sales_test` and `manager_test`.
- Existing Lead only: `PHASE3B02 TEST-001` (`6a527c8be16c09158`), assigned to Sales Test and Sales Team.
- Browser actions were navigation, filter-menu inspection, opening an edit form, and cancelling it. No Save, Create, Delete, or lifecycle action was invoked.
- Browser console was collected after each completed role flow. No `warn` or `error` entries were present for the Sales User or Sales Manager flows.

## Admin

| Check | Result | Evidence |
| --- | --- | --- |
| Login | BLOCKED | Container initial-password environment value was rejected by the current login form. |
| Dashboard | DEFERRED | Requires an authenticated Admin session. |
| Lead | DEFERRED | Requires an authenticated Admin session. |
| ResearchEvidence UI | DEFERRED | Requires an authenticated Admin session. C10.6 metadata itself is verified below. |
| Email lifecycle UI | DEFERRED | Requires an authenticated Admin session; no lifecycle record was created or modified. |

No additional password was guessed, no Admin password was reset, and no authentication configuration was changed.

## Sales User

| Check | Result | Browser evidence |
| --- | --- | --- |
| Login and loading | PASS | Home dashboard and Leads list loaded normally. |
| Lead list | PASS | One assigned Lead was visible. The list rendered Name, Country, Opportunity Score, Score Tier, Best First Product, Research Status, Outreach Status, Next Follow-Up, Email Status, and Priority Level. |
| Filters | PASS | The visible filter menu opened and rendered All, Open, Converted, Research Pending, Only My, and Followed controls. |
| Intelligence Summary | PASS | Detail view rendered the Intelligence Summary section with business/intelligence fields. |
| Proposal | PASS | Opportunity Proposal rendered, including the disabled Proposal Eligible for Review checkbox and `NO_AUTOMATIC_OPPORTUNITY` action. |
| Console | PASS | No browser warning or error entries after login, list, filter, or detail navigation. |

The Lead detail page still renders a Sync Information section, but Sales User's protected fields were represented as inaccessible placeholders while `peQualificationStatus` remained readable. This is consistent with the current field policy; its section-level presentation remains a UX observation rather than an edit-permission bypass.

## Sales Manager

| Check | Result | Browser evidence |
| --- | --- | --- |
| Login and loading | PASS | Home and Leads list loaded normally. |
| Team visibility | PASS | `manager_test` saw `PHASE3B02 TEST-001`, a Lead assigned to Sales Test in the same Sales Team. |
| Edit entry | PASS | Edit control was available for the team Lead. |
| ACL03 protected fields | PASS | In the edit form, `peSyncStatus`, `peSourceBatchId`, `peOpportunityScoreV4`, `peProposalAction`, and `peEmailStatus` rendered with no input, textarea, or select control. |
| CRM-owned activity fields | PASS | `peNextActionDate` and `peLastContactDate` rendered enabled editable inputs, as intended by ACL03. |
| No-write control | PASS | The form was cancelled without Save. |
| Console | PASS | No browser warning or error entries during list, detail, edit-form, or cancel flow. |

## C10.6 runtime metadata

The running EspoCRM metadata service confirms the C10.6 ResearchEvidence identity metadata is active:

| Metadata item | Result |
| --- | --- |
| `peCanonicalUrl` field | present |
| `peEvidenceTypeNormalized` field | present |
| `peClaimHash` field | present |
| `c10EvidenceIdentity` index definition | present |

This verifies C10.6 metadata availability, but does not replace the deferred authenticated Admin ResearchEvidence UI check.

## Metadata drift

**OPEN — runtime UI metadata is still not aligned to the workspace candidate.**

This run's direct metadata-service read returned only two Lead `clientDefs.filterList` entries (`actual` and `converted`). The workspace Lead client definition declares 26 filter entries. The browser did render the active `Research Pending` list filter, but that isolated UI observation does not establish that the complete workspace filter set is loaded.

The prior R01 post-refresh manifest comparison remains the authoritative file-level alignment evidence: 101 workspace and 101 runtime metadata paths existed, but 20 contents differed after rebuild and cache clear. This round confirms the drift is still visible in effective metadata service output.

## Follow-up required

1. Supply or authorize the current Admin test credential, then rerun the four deferred Admin browser checks without changing the account.
2. Install an approved extension artifact whose UI metadata manifest matches the workspace candidate, then rebuild and clear cache.
3. Re-run this round and require the complete Lead filter metadata set plus zero manifest differences before calling the browser regression fully PASS.

## Non-changes

- No application code, ACL, role, workflow, metadata source file, or connector was modified.
- No Lead, ResearchEvidence, Email, or lifecycle record was created, edited, saved, deleted, or sent.
- No authentication account or password was changed.
- The only repository artifact created by this phase is this report.
