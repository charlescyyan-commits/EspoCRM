# Phase3U04 Browser Acceptance — C10.4 Runtime Validation

**Date:** 2026-07-14
**Target:** Local Docker EspoCRM at `http://localhost:8080`
**Mode:** Browser-only, read-only validation
**Verdict:** **PASS WITH MINOR FINDINGS**

## Scope and safety

Validation used the existing local `Admin` and `sales_test` (Sales User)
sessions. No record was created, edited, approved, converted, sent, delivered,
or deleted. Create forms were opened only to inspect their rendered fields and
were left unsaved. No approval, send, or email-delivery control was invoked.

## Admin validation

### Prospecting menu and dashboard

| Check | Result | Browser evidence |
| --- | --- | --- |
| Prospecting navigation | PASS | Prospecting Operations, Search, Search Jobs, Prospect Pool, Research Evidence, and Search Strategies are visible. |
| Prospecting Operations loads | PASS | `#ProspectingDashboard` loaded without an error or warning. |
| Dashboard labels | PASS | Prospecting Summary, Total Prospects, New This Week, Need Research, Research Completed, High Priority, Recent Discovery Activity, Start Discover, and Open Search Strategies all render. |
| Empty data handling | PASS | All five metrics show `0` plus `No data available`; recent activity shows its explicit empty state. No fabricated counts appeared. |
| Layout/navigation links | PASS | Dashboard sidebar workflow and all action links rendered; the compact native layout has no observed overlap or broken control. |

The Admin home dashboard also loaded its existing acquisition dashlets (Search
Strategies, Discovery Jobs, Running, Queued, Completed, Failed, Lead Pool, and
Research Queue) with the native empty state. This confirms the dashboard
dashlets load; record-row alignment cannot be exercised while their result sets
are empty.

### Entity UI

| Entity | Fields, filters, and buttons | Result |
| --- | --- | --- |
| SearchStrategy | List loads with Create Search Strategy and the Draft, Ready, Active, Completed filter choices. The rendered form has Strategy Definition, Query Plan, and Ownership sections with required product/country/persona/source-plan fields. | PASS |
| SearchJob | List loads with Create Search Job and Queued, Running, Completed, Failed, Cancelled filters. Form exposes job definition and execution fields including provider, priority, counts, timestamps, Error Message, and Failure Summary. | PASS |
| ProspectPool | List loads with business and queue filters. Form exposes Discovery Information, Acquisition Pipeline, and Notes and Ownership; labels include Company, Website, Provider, Search Job, Research Status, Qualification, and CRM Push Status. | PASS |
| Lead | List and detail load. The Lead layout contains Intelligence Summary, Pipeline, Opportunity Proposal, Sales Activity, Email Status, AI Research Information, Sync Information, and Contact & Ownership. | PASS |

No SearchStrategy record exists in the local test data, so the per-record
**Generate Search Jobs** button could not be inspected without creating test
data. It was not exercised.

## Sales User validation

The browser logged in as `sales_test`. The assigned marker Lead
`PHASE3B02 TEST-001` was visible and opened successfully.

### Lead list

| Check | Result | Evidence |
| --- | --- | --- |
| List load | PASS | One owned Lead rendered. |
| Columns | PASS | Name, Country, Opportunity Score, Score Tier, Best First Product, Research Status, Outreach Status, Next Follow-Up At, Email Status, and Priority Level are visible. |
| Filters | PASS WITH FINDING | Runtime menu exposes All, Open, Converted, Research Pending, Only My, and Followed. See finding F-01. |
| Sorting | PASS | Clicking Opportunity Score displayed the native descending sort indicator. |

### Lead detail

| Requested area | Result | Evidence |
| --- | --- | --- |
| Intelligence Summary | PASS | Source Type, Discovery Source, Opportunity Score, Score Tier, Best First Product, Research Status, Priority Level, Company Type, Industry, and Business Model render. |
| Proposal information | PASS | Proposal Eligible for Review is a disabled display-only checkbox; Proposal Action reads `NO_AUTOMATIC_OPPORTUNITY`. |
| Email Status | PASS | Email Status, Last Email Date, Campaign Name, and Reply Status render with the correct empty/`None` state for this marker Lead. |
| Research Evidence | PASS WITH FINDING | The standalone AI Research Evidence entity is accessible and its empty-state copy renders. The Lead detail does not render its expected AI Research Evidence relationship panel. See F-02. |

## C10.4 lifecycle UI check

| State surface | Result |
| --- | --- |
| Approval/proposal display | PASS | Proposal Eligible for Review is non-editable and false for the marker record; no approval action was exposed or invoked. |
| Execution status | PASS | Outreach Status displays `NEW`; the UI exposes no execution/send command in the verified surfaces. |
| Email lifecycle | PASS | Email Status displays `None`, with no last-email date, campaign, or reply state. No email action was taken. |

## Browser quality

All visited pages loaded successfully. Browser console capture after each
navigation showed **no error or warning entries**. No broken control, missing
dashboard label, or visual overlap was observed in the loaded native views.

## Minor findings

| ID | Finding | Impact |
| --- | --- | --- |
| F-01 | Sales User Lead filter dropdown shows only the native All/Open/Converted choices plus Research Pending, rather than the wider configured Prospecting operational filter inventory. | Existing primary workflow filter works; limits Sales User filter discoverability. |
| F-02 | AI Research Evidence opens as a standalone entity for Sales User, but the Lead detail page does not show the corresponding relationship panel, even as an empty panel. | Evidence can be reached from navigation but not from the Lead record context. |

These are observation-only findings. No source, metadata, cache, role, ACL,
data, or runtime change was made during this validation.

## Deferred coverage

- Per-record SearchStrategy **Generate Search Jobs** button: no existing
  SearchStrategy record; creating one would violate the read-only scope.
- Dashlet record-row field alignment: acquisition dashlets have no records in
  the local environment, so only their load and empty-state behavior was
  verified.
