# Leads (User Guide)

**Status:** **Implemented** (metadata and sync); outreach automation partial

## Overview

Native EspoCRM **Lead** records are extended with `pe*` (prospecting engine) fields for intelligence, sync state, email status, and opportunity proposals.

## Intelligence Sections (Detail Layout)

| Section | Content |
|---------|---------|
| Intelligence Summary | Score, tier, product fit, research status, source |
| AI Research Information | Summary, key evidence, recommended approach |
| Opportunity Proposal | Scores, eligibility, `peProposalAction` |
| Email Status | Status, last date, campaign, reply status (no full body) |
| Pipeline | `outreachStatus`, follow-up dates |
| Sales Activity | Native status, next/last contact dates |
| Sync Information | Sync status, engine versions |

## Sync from Connector

When connector posts sync contract `1.0`:

1. Lead created/updated by `peCandidateId`
2. ResearchEvidence rows attached
3. Proposal fields updated if score ≥ 80 — **no Opportunity auto-created**

Response action: `NO_AUTOMATIC_OPPORTUNITY`

## Outreach Status Pipeline

Phase 3B02 pipeline options on `outreachStatus`:

`NEW` → `RESEARCHING` → `RESEARCH_COMPLETED` → `QUALIFIED` → `CONTACT_READY` → `CONTACTED` → `RESPONDED` → `CONVERTED` / `CLOSED_LOST`

Formula and hooks may auto-adjust priority and create Tasks — **Runtime Verified** in phase 3B reports on test CRM.

## Related Panels

- AI Research Evidence (read-oriented; create disabled)
- Email Events
- Sales Feedback
- Learning Signals

## Not Stored in CRM

- Full email subject/body (`peEmailSubject`, `peEmailBody` absent by design)
- Raw crawler HTML or credentials

## Related Documents

- [ACL.md](ACL.md)
- [../api/REST_ENDPOINTS.md](../api/REST_ENDPOINTS.md)
- [../sync-contracts/ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md](../sync-contracts/ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md)
