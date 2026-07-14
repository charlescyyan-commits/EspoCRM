# Phase ACL02 — Sales Manager Field Visibility Review

**Date:** 2026-07-14  
**Mode:** Read-only review and recommendation only.  
**Scope:** Sales Manager access to `Lead` projection, sync, and technical fields.  

## Verdict

**WARNING CONFIRMED — no ACL change made.**

The running Sales Manager role has `Lead.read=team` and `Lead.edit=team`. A Lead
field is therefore editable on an accessible team record unless its `fieldData`
contains `edit=no`. The current runtime role protects 16 of the 37 `pe*` fields
defined by the Prospecting Lead metadata; it leaves the other 21 unrestricted.

The G02/ACL verification warning is specifically confirmed for **11 fields**:
they are protected on the current Sales User role but are absent from Sales
Manager `fieldData.Lead`. They consequently inherit Sales Manager's team edit
permission. This is a real least-privilege drift, not merely a layout issue.

## Evidence reviewed

- Runtime `role` table export from the isolated local EspoCRM on 2026-07-14.
  The persisted `Sales Manager` field map contains 6 hidden and 10 read-only
  Lead fields; `Lead.edit` is `team`.
- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/Lead.json`:
  36 Prospecting-prefixed (`pe*`) Lead fields are currently defined.
- `deployment/provisioning/phase3a33_provision_roles.php`: the original shared
  sales policy seeds 6 hidden technical and 10 read-only AI/research fields.
- `docs/PHASE_ACL_VERIFICATION_REPORT.md`: current runtime comparison of Sales
  User and Sales Manager field maps.
- Field ownership declarations in `docs/PHASE3C06_FINAL_BOUNDARY_AUDIT.md` and
  the Lead i18n tooltips.

No Role, ACL metadata, entity definition, layout, workflow, record, or
permission was changed during this review.

## Current effective Sales Manager access

### Correctly hidden today (read=no, edit=no)

These six fields cannot be read or edited by Sales Manager:

- `peSyncStatus`
- `peSourceSystem`
- `peCandidateId`
- `peLastSyncAt`
- `peEngineVersion`
- `peScoreRulesVersion`

### Correctly read-only today (read=yes, edit=no)

These ten fields are readable but not editable by Sales Manager:

- `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`
- `peConfidence`, `peEvidenceCoverage`, `peQualificationStatus`
- `peResearchStatus`, `peResearchSummary`, `peKeyEvidence`,
  `peRecommendedApproach`

### Currently editable by inheritance (no Sales Manager field rule)

The following fields have no Sales Manager field-level rule. On a Lead that the
manager may edit by team ACL, they are effectively editable:

- `peSourceType`, `peDiscoverySource`, `peSourceBatchId`
- `peCompanyType`, `peIndustry`, `peBusinessModel`
- `pePriorityLevel`, `peLastResearchedAt`
- `peProposalProductFitScore`, `peProposalCooperationType`,
  `peProposalSuggestedNextAction`, `peProposalEligibility`, `peProposalAction`
- `peContactFormUrl`, `peLinkedinUrl`
- `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`,
  `peEmailReplyStatus`
- `peNextActionDate`, `peLastContactDate`

## Confirmed G02 drift: required reconciliation set

The eleven fields below are already protected on Sales User and must have the
same Sales Manager field policy if the approved sales-role policy remains
"technical hidden; engine-owned data readable but non-editable":

| Field group | Fields | Current Manager | Recommended policy |
| --- | --- | --- | --- |
| Technical batch identity | `peSourceBatchId` | Editable | `read=no`, `edit=no` |
| Email lifecycle projection | `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` | Editable | `read=yes`, `edit=no` |
| Research timestamp | `peLastResearchedAt` | Editable | `read=yes`, `edit=no` |
| Opportunity-proposal projection | `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalSuggestedNextAction`, `peProposalEligibility`, `peProposalAction` | Editable | `read=yes`, `edit=no` |

This is the minimum, evidence-backed remediation set. It restores parity with
the present Sales User role without changing entity ACL scope or business flow.

## Business ownership recommendation

The `pe` prefix alone is not sufficient to infer editability. The field owner
and the write path are decisive.

### Recommended editable for Sales Manager

Keep only the following `pe*` fields editable on team-visible Leads:

- `peNextActionDate` — explicitly documented as CRM-owned next sales action.
- `peLastContactDate` — explicitly documented as CRM-owned most-recent sales
  contact date.

Native CRM-owned sales fields (for example Lead `status`, assignment and normal
contact/account data) continue to follow the existing entity-level team ACL;
they are outside this review's `pe*` decision.

### Recommended read-only for Sales Manager

All engine- or connector-projected fields should be readable but non-editable:

- Score, tier, confidence, qualification, research summary/evidence, and
  recommended approach fields.
- Proposal fields and the email lifecycle summary fields in the confirmed G02
  reconciliation set.
- `peLastResearchedAt`.
- `peSourceType` and `peDiscoverySource`, because the sync service projects
  them from the connector source payload.
- `peCompanyType`, `peIndustry`, and `peBusinessModel`, because the boundary
  audit classifies them as Chitu/AI classifications.
- `pePriorityLevel`, because it is derived by the existing Lead formula from
  the score and is not a CRM sales stage.
- `peContactFormUrl` and `peLinkedinUrl` by the conservative production
  default: they are contact-discovery output, not a documented CRM-owned
  override surface.

For the final five bullets, both current sales roles lack field-level rules.
They are **not part of the confirmed G02 parity drift**; this report recommends
an explicit product decision before changing them. If Sales must correct a
discovered URL or a classification, that should be an approved ownership
exception (or a separate override/audit design), rather than an accidental
consequence of omitted field ACL.

### Recommended hidden from Sales Manager

Technical identity, transport, and diagnostic fields should remain hidden:

- `peSyncStatus`, `peSourceSystem`, `peCandidateId`, `peLastSyncAt`,
  `peEngineVersion`, `peScoreRulesVersion`, and `peSourceBatchId`.

This preserves the previously validated dashboard behavior: technical sync
fields must not be selected or used for Sales Manager list ordering.

## Implementation guidance for a later approved ACL change

1. Make the 11 confirmed fields match the current Sales User policy first.
2. Separately approve the ownership decision for source/classification/contact
   discovery fields; do not silently bundle that broader policy change into a
   G02 repair.
3. Do **not** rerun the existing `phase3a33_provision_roles.php` blindly as a
   remedy. Its shared `$salesLeadFieldData` seed contains only the original 16
   rules and would not preserve the later Sales User protections for the 11
   fields above.
4. After any approved change, verify field-level read/edit behavior with a
   Sales Manager API session and an authenticated browser session on a
   team-owned Lead. Confirm that standard CRM sales activity remains editable
   and technical fields cannot be exposed, edited, or used as list sort keys.

## Non-changes

- No roles or permissions changed.
- No entity, metadata, layout, workflow, connector, or data changed.
- No browser state, CRM records, or outreach behavior was changed.
