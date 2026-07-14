# Phase ACL03 — Sales Manager Field Visibility Report

**Date:** 2026-07-14  
**Status:** PASS — runtime field ACL applied and regression-safe.  
**Scope:** Sales Manager `Lead.fieldData` only.  

## Outcome

Sales Manager retains native EspoCRM `Lead.read=team` and `Lead.edit=team`, but
its 37 Prospecting-prefixed Lead fields are now explicitly governed as follows:

- **7 technical fields:** hidden (`read=no`, `edit=no`);
- **28 engine/connector projection fields:** read-only (`read=yes`, `edit=no`);
- **2 CRM-owned sales activity fields:** editable by the existing team entity
  permission (`peNextActionDate`, `peLastContactDate`).

No PHP backend, connector, evidence persistence, sync logic, workflow, scoring,
Lead pipeline, entity definition, layout, or language label was modified.

## Changed files

| File | Change |
| --- | --- |
| `deployment/provisioning/phase_acl03_apply_sales_manager_field_visibility.php` | New idempotent runtime provisioning script. It updates only the existing Sales Manager `fieldData.Lead`, then re-reads and validates the persisted rules. |
| `crm-extension/tests/test_phase_acl03_sales_manager_field_visibility.py` | New 8-test static ACL contract suite, including a guard that every non-activity `pe*` Lead field has an explicit policy. |
| `docs/PHASE_ACL02_FIELD_VISIBILITY_REVIEW.md` | Corrected the audit inventory count: metadata defines 37 `pe*` fields, so the pre-change unrestricted count was 21. No recommendation changed. |
| `docs/PHASE_ACL03_SALES_MANAGER_FIELD_VISIBILITY_REPORT.md` | This implementation report. |

## Audit and permission matrix

The runtime Sales Manager record was audited before application. Its entity ACL
was, and remains, `Lead: create=yes, read=team, edit=team, delete=no,
stream=team`.

| Field category | Before | After | Result |
| --- | --- | --- | --- |
| Technical sync/identity | 6 hidden; `peSourceBatchId` editable | 7 hidden | `peSourceBatchId` converged to hidden; existing six retained |
| Intelligence/research core | 10 read-only | 10 read-only | Retained |
| Email lifecycle projection | 4 editable | 4 read-only | Converged |
| Opportunity proposal projection | 5 editable | 5 read-only | Converged |
| Research timestamp | `peLastResearchedAt` editable | Read-only | Converged |
| Source/classification/contact discovery | 8 editable by omission | 8 read-only | Explicit conservative ownership boundary |
| Derived priority | `pePriorityLevel` editable | Read-only | Formula-derived projection protected |
| CRM sales activity | `peNextActionDate`, `peLastContactDate` editable | Editable | Retained through `Lead.edit=team` |

### Final field policy

**Hidden — technical metadata**

`peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`,
`peEngineVersion`, `peScoreRulesVersion`, `peSourceBatchId`.

**Read-only — engine/connector projections**

`peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`,
`peResearchStatus`, `peEmailStatus`, `peLastEmailDate`,
`peEmailCampaignName`, `peEmailReplyStatus`, `peSourceType`,
`peDiscoverySource`, `peCompanyType`, `peIndustry`, `peBusinessModel`,
`pePriorityLevel`, `peLastResearchedAt`, `peProposalProductFitScore`,
`peProposalCooperationType`, `peProposalSuggestedNextAction`,
`peProposalEligibility`, `peProposalAction`, `peContactFormUrl`,
`peLinkedinUrl`, `peResearchSummary`, `peKeyEvidence`,
`peRecommendedApproach`, `peConfidence`, `peEvidenceCoverage`, and
`peQualificationStatus`.

**Editable — CRM-owned sales activity**

`peNextActionDate`, `peLastContactDate`.

The provisioning script deliberately removes any field-level override for the
two editable fields. It does not grant a new permission; they remain editable
only where the Sales Manager already satisfies native `Lead.edit=team`.

## Role isolation

- **Admin:** unchanged; no field rule or entity ACL change was applied.
- **Integration Bot:** unchanged; no sync scope or field permission changed.
- **Sales User:** unchanged; ACL03 neither reads nor saves that role.
- **Sales Manager:** only `fieldData.Lead` was saved. The script does not set
  role `data`, flags, user relations, or any other scope.

## Runtime application and metadata validation

The locally running EspoCRM accepted the provisioning script after PHP lint:

```text
ACL03_OK roleId=6a5237bd77ef7161e hidden=7 readOnly=28
editable=peNextActionDate,peLastContactDate
Cache has been cleared.
```

The script re-fetches the Sales Manager role after saving and fails loudly if a
persisted field rule does not match. This validates the active database role
payload rather than only the source definition.

No metadata files changed, so no metadata rebuild was required. Cache was
cleared after the role update. The regression Baseline suite also verified that
all extension metadata JSON remains parseable.

## Tests and regression impact

| Validation | Result |
| --- | --- |
| ACL03 static contract suite | PASS — 8/8 |
| Extension tests (includes ACL03 and metadata tests) | PASS — 65/65 |
| PHP lint in running EspoCRM container | PASS |
| Runtime Sales Manager persistence self-check | PASS — 7 hidden, 28 read-only, 2 editable |
| Core Regression Gate | PASS — 7/7 required suites |

Regression Gate result:

| Suite | Passed |
| --- | ---:|
| Extension | 65 |
| Connector | 270 |
| Worker | 31 |
| Static | 2 |
| Runtime | 11 |
| Baseline | 3 |

Machine-readable gate result:
`temp/test-results/regression-gate-20260714-155211-337.json`.

## Browser validation

**DEFERRED — local browser-control attachment failure, not a permission
failure.** The local EspoCRM UI opened and the existing Sales User session was
observed. After standard logout, the browser-control surface could no longer
attach to the Sales Manager login form, so it was not possible to complete the
requested interactive Manager edit-state check. No Lead record or field value
was changed during the attempt.

Runtime persistence validation confirms the server-side result. A future
authenticated Sales Manager browser check should confirm that
`peNextActionDate` and `peLastContactDate` render editable for a team-owned
Lead and that all engine-owned fields render non-editable or are absent when
hidden.

## Boundary confirmation

- No business logic changed.
- No C09/C10 Outreach Lifecycle contract changed.
- No connector, Evidence persistence, workflow, scoring, or pipeline behavior
  changed.
- No Git commit was created.
