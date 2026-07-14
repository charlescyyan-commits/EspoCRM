# Prospect Pool (User Guide)

**Status:** Metadata **Implemented**; automatic population **Draft**

## Purpose

`ProspectPool` holds raw discovery candidates before qualification, research, and optional CRM push.

## Queue Stages

| Queue | Meaning |
|-------|---------|
| `DISCOVERY` | Initial discovery (default) |
| `QUALIFICATION` | Business fit review |
| `RESEARCH` | Research pending/complete |
| `CRM` | Ready or pushed toward CRM |

## Status Fields

| Field | Options |
|-------|---------|
| `status` | `WAITING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `researchStatus` | `NOT_STARTED`, `PENDING`, `COMPLETED`, `FAILED` |
| `qualificationStatus` | `PENDING`, `QUALIFIED`, `REJECTED` |
| `crmPushStatus` | `NOT_READY`, `READY`, `PUSHED`, `FAILED` |

## Key Fields

- `name`, `externalProspectId`, `source`, `sourceUrl`, `website`, `country`
- `searchJob` — link to parent Discovery Job

## What Works Today

**Implemented:**

- Manual CRUD in EspoCRM UI (with ACL)
- Filter presets: discoveryQueue, qualificationQueue, researchQueue, crmQueue
- Connector runner can create ProspectPool rows via REST when executing fake-provider jobs

**Not Implemented:**

- Automatic ProspectPool creation from UI "Run search" (no live provider in CRM)
- Automatic conversion to Lead (`ChituSyncService` has no ProspectPool references)
- End-to-end queue progression automation

## Operator Notes

**TBD — requires runtime verification** for queue workflow on a live instance with your role assignments.

## Related Documents

- [SEARCH_WORKSPACE.md](SEARCH_WORKSPACE.md)
- [LEADS.md](LEADS.md)
