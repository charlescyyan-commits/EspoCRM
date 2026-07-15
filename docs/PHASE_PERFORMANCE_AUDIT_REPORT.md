# EspoCRM Prospecting Module Performance Audit

**Date:** 2026-07-14  
**Mode:** Read-only source, metadata, Docker runtime, MariaDB index, and
`EXPLAIN` audit. No code, cache, database, container, or configuration was
changed.

## 1. Problem summary

Reported slow surfaces are Lead List, Lead Detail, ResearchEvidence, and the
Prospecting Operations dashboard. The local Docker runtime is healthy, but its
active data set is small:

| Table | Active rows (`deleted = 0`) |
| --- | ---: |
| `lead` | 7 |
| `research_evidence` | 0 |
| `email_event` | 0 |
| `prospect_pool` | 0 |
| `search_job` | 0 |

Therefore a multi-second load in this local state is **not explained by current
row volume**. The most credible immediate candidates are client/API request
fan-out, relationship-panel loading, and local runtime/network latency. Missing
indexes are nevertheless a material scale risk: the measured query plans
already contain full scans and filesorts for the specified Prospecting fields.

## 2. Root-cause candidates

### A. Prospecting Operations dashboard request fan-out — HIGH

`ProspectingSummary` performs five parallel collection fetches solely to read
totals: all ProspectPool records, recent ProspectPool records, research queue,
research-completed ProspectPool records, and high-priority SearchJobs. Each
uses `maxSize = 1` but still needs a collection total/count query.

The provisioned Operations dashboard has:

- **9 dashlets** for `manager_test`: summary, recent discovery, and seven Lead
  intelligence lists;
- **11 dashlets** for other provisioned users, adding recent ResearchEvidence
  and SalesFeedback lists.

This establishes a lower-bound of roughly **13** and **15** collection/API
fetches respectively at initial dashboard load (five summary counts, one recent
discovery fetch, seven Lead lists, and optionally two related-entity lists).
Record-list endpoints commonly also calculate totals, so SQL operations may
exceed this request count. This is client-side fan-out, not a confirmed
server-side ORM N+1 loop.

There is a second custom `ProspectingDashboard` view with the same five-count
pattern plus a recent-jobs fetch. The audit found no evidence that it and the
dashlet are rendered on the same route, but they should not be composed
together without sharing metrics.

### B. Lead Detail relationship panels — HIGH candidate

`Lead` detail configures five relationship panels: ResearchEvidence, EmailEvent,
Task, SalesFeedback, and LearningSignal. Each has its own sort and related-list
loading path. Depending on EspoCRM panel lazy-loading behavior, this can cause
up to five post-detail collection requests in addition to the Lead detail API.

The source contains no custom Lead read controller or per-row server loop, so
this is an API/UI fan-out candidate. A browser Network waterfall is required to
confirm whether these panel calls are parallel, deferred, or serial in the
reported session.

### C. Unindexed Lead score/status ordering and filters — HIGH scale risk

The live `lead` table has an index for `created_at` and `pe_source_batch_id`
only among Prospecting fields. It has **no index** for:

- `pe_opportunity_score_v4`
- `pe_score_tier`
- `pe_research_status`
- `pe_email_status`

Measured MariaDB plans:

| Representative query shape | Plan |
| --- | --- |
| `deleted = 0 ORDER BY pe_opportunity_score_v4 DESC LIMIT 10` | full scan + `Using filesort` |
| `deleted = 0 ORDER BY pe_research_status DESC LIMIT 10` | full scan + `Using filesort` |
| `deleted = 0 ORDER BY pe_email_status DESC LIMIT 10` | full scan + `Using filesort` |
| `deleted = 0 ORDER BY created_at DESC LIMIT 10` | uses `IDX_CREATED_AT`; no filesort |

This directly affects the ProspectingIntelligence dashlet default
`peOpportunityScoreV4` ordering and several primary filters. It is inexpensive
at seven active Leads, but will become progressively slower as production data
grows.

### D. Related-list sort indexes — MEDIUM scale risk

ResearchEvidence has `lead_id`, identity, snapshot, and evidence-ID indexes,
but no index ending in `pe_captured_at`. EmailEvent has `lead_id` and a
message/event index, but no index ending in `event_at`.

Measured global recent-list shapes for both entities use full scans and
filesorts. For Lead detail panels, the current `lead_id` indexes can locate
related rows, but cannot efficiently satisfy `lead_id + deleted + ordered
timestamp` at scale.

### E. Primary-filter query complexity — MEDIUM

Most Lead filters are simple status predicates, but their fields are unindexed.
The `peMissingEvidence` / `peCompletedWithoutEvidence` filter is more expensive:
it adds a `LEFT JOIN ResearchEvidence`, `DISTINCT`, and a null anti-join test.
It is correctly bounded in semantics, but is a high-query-risk filter on larger
tables or when used in a dashboard dashlet.

`peIncompleteResearchProjection` also tests three potentially large text fields
for null/empty values. It should be treated as an exception/report filter, not
a default dashboard query.

### F. Large fields and write hooks — LOW for page-read latency

Lead List excludes the large text projections. Lead Detail intentionally loads
`peResearchSummary`, `peKeyEvidence`, `peRecommendedApproach`, and description.
ResearchEvidence Detail loads both `peEvidenceText` and `peContentSummary`;
the sync path currently assigns the same evidence text to both, which can
double detail-payload text for evidence records.

Lead formulas and `LeadWorkflowHook` run on save, not List/Detail reads. The
EmailEvent hooks perform extra read/write work on event ingestion (Lead lookup,
projection, optional Task/SalesFeedback lookup), but they do not execute during
List or Detail API reads. They are write-path risks, not an explanation for the
reported page-load latency.

## 3. Query risk by surface

| Surface | Observed design | Risk | Evidence |
| --- | --- | --- | --- |
| Lead List | Standard Record controller; 26 primary filters; list layout is compact | Medium now / High at scale | Score, tier, research, and email fields lack indexes; score sorting filesorts. |
| Lead Detail | Standard detail API plus 5 relationship panels and several large text fields | High candidate | Related-panel fetch fan-out is likely; requires browser waterfall confirmation. |
| ResearchEvidence List | Standard Record controller; compact list fields; default `peCapturedAt DESC` | Medium at scale | `pe_captured_at` has no index; `EXPLAIN` is full scan/filesort. |
| ResearchEvidence Detail | Two large evidence-text fields plus Lead/User/Team links | Medium | Payload can be large; no custom read-side query loop found. |
| EmailEvent List/detail | Standard Record controller; Lead relation; default `eventAt DESC` | Medium at scale | `event_at` has no index; `EXPLAIN` is full scan/filesort. |
| Operations dashboard | 9–11 dashlets and 13–15 initial collection fetches | High | Five count requests in custom summary plus seven Lead lists and optional related lists. |

## 4. Recommended optimization (do not implement in this audit)

1. **Instrument before changing behavior.** Capture a browser Network waterfall
   for one slow Lead Detail and one Operations dashboard load; record endpoint,
   duration, response size, and whether related panels are serial. Enable or
   consult slow-query telemetry in a controlled environment before applying
   indexes.
2. **Reduce dashboard round trips.** Replace the five independent summary
   count fetches with a single aggregate read model/endpoint or a short-lived
   cached metric response. Keep the displayed semantics unchanged. Review the
   7 Lead intelligence dashlets and defer/lazy-load below-the-fold lists.
3. **Add indexes only after production-plan validation.** Initial candidates:
   - `lead(deleted, pe_opportunity_score_v4)` for score-ranked dashlets;
   - `lead(deleted, pe_score_tier, pe_opportunity_score_v4)` for tier queues;
   - `lead(deleted, pe_research_status, pe_last_researched_at)` for research
     queues/recent research;
   - `lead(deleted, pe_email_status, created_at)` only if email-status lists
     become a frequent operational surface;
   - `research_evidence(lead_id, deleted, pe_captured_at)` for Lead panels and
     recent-evidence ordering;
   - `email_event(lead_id, deleted, event_at)` for Lead panels and recent-event
     ordering.
   Validate each candidate with real production cardinality and `EXPLAIN`;
   avoid adding every single-field index indiscriminately.
4. **Keep exception filters off default dashboard load.** In particular, do not
   auto-load the anti-join `peMissingEvidence` filter or text-null diagnostic
   filter until they have measured plans and appropriate supporting indexes.
5. **Trim read payloads only where UX permits.** Keep evidence text out of list
   APIs (already true). Consider loading one of the duplicate evidence-text
   representations on demand in detail if response-size capture proves it is
   significant.

## 5. Risk level and priority

### HIGH

1. Dashboard API/count fan-out: establish browser timing evidence, then
   consolidate summary counts and defer noncritical dashlets.
2. Lead Detail related-panel waterfall: measure panel request behavior and
   defer/lazy-load nonessential panels if confirmed.
3. Lead score/tier/research/email query plans: introduce only validated
   composite indexes before production data grows.

### MEDIUM

1. ResearchEvidence and EmailEvent ordered related lists: validate and add
   timestamp composite indexes when their tables contain operational data.
2. `peMissingEvidence` anti-join and text-null diagnostic filters: prevent
   default use and benchmark against realistic data.
3. ResearchEvidence Detail duplicate text payload: measure response bytes
   before changing the read layout.

### LOW

1. Lead formula and after-save hooks: monitor event-ingestion/write latency,
   but they are not read-page root causes.
2. Current local database volume: the active rows are too few for table-scan
   cost to explain multi-second UI loads; investigate client waterfall, PHP/API
   timing, and local Docker resource contention next.

## Audit limitations

No authenticated browser HAR, server slow-query log, production-sized data set,
or API timing trace was available in this read-only audit. Findings distinguish
measured source/index/plan facts from candidates; production prioritization
should be confirmed with those traces before schema or UI changes.
