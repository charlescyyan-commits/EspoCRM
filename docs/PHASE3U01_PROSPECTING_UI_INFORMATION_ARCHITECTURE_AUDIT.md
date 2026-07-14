# Phase3U01 — Prospecting Acquisition UI Audit & Information Architecture

**Date:** 2026-07-13
**Auditor:** Claude Code (DeepSeek V4 Pro API, High Reasoning)
**Status:** **READY FOR U02**
**Mode:** Read-only audit. Zero production modifications.

---

## 1. Executive Summary

The current EspoCRM extension (`1.9.0-alpha`) has a solid metadata foundation for the acquisition workflow but the UI does not yet tell a coherent story. Three entities — SearchStrategy, SearchJob, ProspectPool — are correctly defined with `tab:true`, `acl:true`, filters, layouts, and dashlets. However, key gaps prevent users from understanding the workflow:

1. **No entity-level filters for SearchStrategy** — Users cannot filter strategies by status (Draft/Ready/Generated/Running).
2. **SearchJob list hides critical timing fields** — `startedAt`, `completedAt`, `errorMessage` are missing from the list view.
3. **ProspectPool lacks acceptance/rejection actions** — The entity has `acceptedCount`/`rejectedCount` on SearchJob but no per-prospect accept/reject mechanism.
4. **No entry-point landing page** — Users enter via an 8-dashlet dashboard with no workflow guidance.
5. **i18n uses developer-facing terminology** — "prospectPools", "queryFingerprint", "pe" prefix on Lead fields.

**Recommendation:** Native entity-first UI (Option A) augmented by a single Prospecting landing dashlet that orients users. This is the lowest-risk, highest-clarity approach given current backend maturity.

**U02 blocking gap count:** 0 (zero backend contract gaps block U02)

---

## 2. Current UI Inventory

### 2.1 Entity Registration Summary

| Entity | Scope | Tab | ACL | Module | Status Field |
|---|---|---|---|---|---|
| SearchStrategy | ✅ entity/object | ✅ tab:true | ✅ acl:true | Prospecting | null |
| SearchJob | ✅ entity/object | ✅ tab:true | ✅ acl:true | Prospecting | null |
| ProspectPool | ✅ entity/object | ✅ tab:true | ✅ acl:true | Prospecting | null |
| ResearchEvidence | ✅ entity/object | ✅ tab:true | ✅ acl:true | Prospecting | null |
| Lead | EspoCRM core | core-controlled | core-controlled | (core) | status |

### 2.2 Navigation Visibility

All four Prospecting entities (`tab:true`, `module: "Prospecting"`) appear as separate tabs in the EspoCRM top navigation bar under their own section. EspoCRM groups tabs by module when `module` is set. The `module.json` sets `order: 25`, placing Prospecting after standard modules.

**Current tab order (inferred from module order):**
1. Accounts, Contacts, Leads, Opportunities... (core, lower order)
2. **SearchStrategy** (Prospecting, order 25)
3. **SearchJob** (Prospecting, order 25)
4. **ProspectPool** (Prospecting, order 25)
5. **ResearchEvidence** (Prospecting, order 25)
6. SalesFeedback, LearningSignal, EmailEvent... (other Prospecting entities)

**Problem:** All 4 entities appear as flat tabs with no hierarchy, no group label, and no visual distinction between "strategy planning" and "execution results" entities. A sales user sees 4 unfamiliar tabs with no obvious entry point.

### 2.3 Entity Icons

| Entity | Icon | Semantics |
|---|---|---|
| SearchStrategy | `fas fa-sitemap` | Organization chart / hierarchy |
| SearchJob | `fas fa-search` | Search / discovery |
| ProspectPool | `fas fa-layer-group` | Layers / collection |
| ResearchEvidence | (default) | Not explicitly set in clientDefs |

### 2.4 Controller Architecture

All four Prospecting entities use standard EspoCRM Record controllers with zero custom logic:

```php
// Every controller follows this pattern
class SearchStrategy extends Record {}
class SearchJob extends Record {}
class ProspectPool extends Record {}
class ResearchEvidence extends Record {}
```

This is positive — it means entity CRUD, list, detail, edit, and delete all work through EspoCRM's battle-tested record infrastructure with no custom bugs.

### 2.5 Custom Views

Only **one** custom frontend handler exists:

| Handler | Path | Purpose |
|---|---|---|
| `custom:handlers/search-strategy/generate-jobs` | `files/client/custom/src/handlers/search-strategy/generate-jobs.js` | Detail action button on SearchStrategy |

It calls `POST /Prospecting/search-strategy/generate-jobs` and refreshes the model on success. **No custom record views, list views, or dashlet views exist** — all UI rendering uses EspoCRM built-in views.

### 2.6 Dashlet Inventory

11 dashlets are registered for the Prospecting module:

| Dashlet Name | Entity | Title | Filter | Dashboard Placement |
|---|---|---|---|---|
| ProspectingIntelligence | Lead | Prospecting Intelligence | none | (user-added) |
| RecentResearchEvidence | ResearchEvidence | Recent Research Evidence | none | (user-added) |
| RecentSalesFeedback | SalesFeedback | Recent Sales Feedback | recentFeedback | (user-added) |
| **AcquisitionSearchStrategies** | **SearchStrategy** | **Search Strategies** | none | **Acquisition tab** |
| **AcquisitionDiscoveryJobs** | **SearchJob** | **Discovery Jobs** | none | **Acquisition tab** |
| **AcquisitionJobsRunning** | **SearchJob** | **Running** | jobsRunning | **Acquisition tab** |
| **AcquisitionJobsWaiting** | **SearchJob** | **Queued** | jobsQueued | **Acquisition tab** |
| **AcquisitionJobsCompleted** | **SearchJob** | **Completed** | jobsCompleted | **Acquisition tab** |
| **AcquisitionJobsFailed** | **SearchJob** | **Failed** | jobsFailed | **Acquisition tab** |
| **AcquisitionLeadPool** | **ProspectPool** | **Lead Pool** | none | **Acquisition tab** |
| **AcquisitionResearchQueue** | **ProspectPool** | **Research Queue** | researchQueue | **Acquisition tab** |

The 8 Acquisition dashlets are provisioned into an "Acquisition" dashboard tab by `phase3c01_provision_acquisition_workspace.php`.

### 2.7 Current Dashboard Layout

The Acquisition dashboard tab layout (grid: 4 columns):

```
Row 0: [Search Strategies (2w)] [Discovery Jobs (2w)]
Row 2: [Running (1w)] [Queued (1w)] [Completed (1w)] [Failed (1w)]
Row 4: [Lead Pool (2w)]            [Research Queue (2w)]
```

**Assessment:** Good foundation. Shows the pipeline from strategies → jobs → prospects. But lacks:
- Workflow narrative (what do I do first?)
- Count indicators (how many running? how many new prospects?)
- Direct click-through to action (dashlet rows link to entities but don't guide action)

---

## 3. Confirmed Entity Visibility

### 3.1 SearchStrategy — Visible ✅

- **Tab:** Yes (`tab:true`)
- **List:** Yes (standard Record controller, 8-column list layout)
- **Detail:** Yes (3-panel detail layout)
- **Create:** Yes (standard Record controller)
- **Edit:** Yes (standard Record controller)
- **Delete:** Depends on role (Admin/Sales Manager: yes; Sales User/Integration Bot: no per ACL)
- **Filters:** **NONE defined** — `selectDefs/SearchStrategy.json` does not exist
- **Icon:** `fas fa-sitemap` — reasonable for a strategy/planning entity
- **Detail actions:** "Generate Jobs" button (edit ACL required)

### 3.2 SearchJob — Visible ✅

- **Tab:** Yes (`tab:true`)
- **List:** Yes (standard Record controller, 10-column list layout)
- **Detail:** Yes (3-panel detail layout)
- **Create:** Yes (standard Record controller — though SearchJobs are typically auto-generated)
- **Edit:** Depends on role
- **Delete:** Depends on role
- **Filters:** 5 defined — jobsQueued, jobsRunning, jobsCompleted, jobsFailed, jobsCancelled
- **Icon:** `fas fa-search` — appropriate for a search/discovery entity
- **Detail actions:** None beyond standard Record actions
- **Relationship panel:** prospectPools (create enabled, showing child prospects)

### 3.3 ProspectPool — Visible ✅

- **Tab:** Yes (`tab:true`)
- **List:** Yes (standard Record controller, 9-column list layout)
- **Detail:** Yes (3-panel detail layout with Acquisition Pipeline section)
- **Create:** Yes (standard Record controller — though prospects are normally auto-created by worker)
- **Edit:** Depends on role
- **Delete:** Depends on role
- **Filters:** 4 defined — discoveryQueue, qualificationQueue, researchQueue, crmQueue
- **Icon:** `fas fa-layer-group` — acceptable but not intuitive for "prospect pool"
- **Detail actions:** None beyond standard Record actions

### 3.4 ResearchEvidence — Visible ✅

- **Tab:** Yes (`tab:true`)
- **List:** Yes (standard Record controller)
- **Detail:** Yes (standard layout)
- **Filters:** None defined in selectDefs
- **Assessment:** Should remain visible as a reference entity but not part of the primary acquisition workflow. Accessed via Lead detail bottom panel ("AI Research Evidence").

### 3.5 Lead — Visible (Core Entity) ✅

- **Tab:** Yes (EspoCRM core)
- **Acquisition-relevant fields:** `peDiscoverySource`, `peSourceType`, `peSourceBatchId`, `peCandidateId`, `peSourceSystem`, `peSyncStatus` (in Sync Information panel)
- **Relationship:** `researchEvidences` (bottom panel on detail view)
- **Assessment:** Acquisition provenance is visible in the "Sync Information" section of Lead detail, but not prominent enough for users to trace a prospect → lead journey.

---

## 4. Current Navigation Gaps

### Gap 1: No entry point
Users must guess which tab to click first. "SearchStrategy" is alphabetically last among prospecting entities but should be first in the workflow.

### Gap 2: No workflow grouping
The 4 Prospecting entities appear as flat, undifferentiated tabs. A sales user cannot distinguish "planning" entities from "execution" entities from "reference" entities.

### Gap 3: No status overview
There is no single view that answers "how many strategies are active?", "how many jobs ran today?", "how many new prospects were discovered this week?"

### Gap 4: SearchStrategy filters missing
The entity with the most complex state machine (DRAFT → READY → GENERATED → RUNNING → COMPLETED → FAILED → CANCELLED) has zero primary filters. Users cannot see "Active Strategies" or "Ready to Generate" strategies from the list view.

### Gap 5: Technical terminology in user-facing labels
- "prospectPools" appears as the link label for SearchJob→ProspectPool relationship
- "queryFingerprint" is visible in the SearchJob detail and list (internal dedup field)
- "externalProspectId" visible in ProspectPool detail
- "pe" prefix on all Lead intelligence fields

### Gap 6: Missing list columns on SearchJob
Critical operational fields missing from SearchJob list view:
- `startedAt` — when did the job start?
- `completedAt` — when did it finish?
- `errorMessage` — why did it fail? (first line visible in list)
- `acceptedCount` / `rejectedCount` — how many prospects passed/failed?

### Gap 7: No Create SearchStrategy guide
The "Create SearchStrategy" form exposes all fields including `keywords`, `excludedKeywords`, `region`, `targetCompanyType` — many of which are optional or advanced. There's no inline guidance on what fields are required vs. optional.

### Gap 8: ProspectPool detail has no Link to Lead action
When a prospect is promoted to CRM (crmPushStatus: PUSHED), there is no visible link to the resulting Lead record. The `crmPushStatus` field shows "Pushed" but provides no navigation.

---

## 5. Recommended User Journey

```
┌─────────────────────────────────────────────────────────┐
│  PROSPECTING HOME (dashboard or landing page)            │
│  Shows: Active Strategies | Running Jobs | New Prospects │
│         Recent Failures | Ready for Research             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  1. CREATE / SELECT SEARCH STRATEGY                       │
│     Entity: SearchStrategy                                │
│     Entry: "Create Search Strategy" button on home        │
│     Action: Define product, country, persona, sources     │
│     Output: Strategy saved as DRAFT                       │
│     Next: Set status to READY, click "Generate Jobs"      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  2. GENERATE DISCOVERY JOBS                               │
│     Entity: SearchStrategy detail → "Generate Jobs"       │
│     Action: System creates SearchJob records (QUEUED)     │
│     Output: Job count shown (generatedJobCount updated)   │
│     Next: Monitor jobs on Acquisition dashboard           │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  3. MONITOR JOB STATUS                                    │
│     Entity: SearchJob list (filtered by status)           │
│     Entry: Dashboard "Running" / "Queued" dashlets        │
│     Action: Click into failed jobs to see errorMessage    │
│     Output: Jobs progress through QUEUED→RUNNING→COMPLETED│
│     Next: Review discovered prospects when COMPLETED      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  4. REVIEW DISCOVERED PROSPECTS                           │
│     Entity: ProspectPool list (DISCOVERY queue)           │
│     Entry: SearchJob detail → prospectPools panel         │
│     Action: Review prospect name, website, source         │
│     Output: Assess which prospects look relevant          │
│     Next: Promote selected prospects to QUALIFICATION     │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  5. QUALIFY AND PROMOTE                                   │
│     Entity: ProspectPool (QUALIFICATION queue)            │
│     Action: Accept/reject prospects, mark duplicates      │
│     Output: Qualified prospects move to RESEARCH queue    │
│     Next: Research-qualified prospects → CRM Lead         │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  6. CONTINUE INTO LEAD WORKFLOW                           │
│     Entity: Lead (EspoCRM core)                           │
│     Entry: ProspectPool detail → pushed Lead link         │
│     Action: Standard CRM lead qualification + outreach    │
│     Output: Lead in pipeline with acquisition provenance  │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Architecture Option Comparison

### Option A — Native Entity-First UI

Use standard EspoCRM tabs, list views, detail views, filters, relationships, and dashlets. Add minimal customizations (filters, actions, labels).

| Criterion | Assessment |
|---|---|
| Implementation cost | **Low** — JSON metadata changes only; no custom JS views needed |
| Maintainability | **High** — follows EspoCRM conventions; upgrade-safe |
| Consistency with EspoCRM | **Excellent** — users see familiar Record UI patterns |
| User clarity | **Good** — if entity names and labels are clear |
| Dependency on backend | **None beyond current** — all entities exist today |
| ACL complexity | **Low** — uses native EspoCRM ACL |
| Upgrade risk | **Minimal** — metadata-only changes survive EspoCRM upgrades |
| Browser testing burden | **Minimal** — no custom rendering paths |

### Option B — Lightweight Prospecting Workspace

Add one custom landing page that links into native entity views. The landing page shows counts, recent activity, and CTAs.

| Criterion | Assessment |
|---|---|
| Implementation cost | **Medium** — requires 1 custom view JS + 1 custom dashlet |
| Maintainability | **Medium** — custom JS needs maintenance on EspoCRM upgrades |
| Consistency with EspoCRM | **Good** — wrapper page, but entity views remain native |
| User clarity | **Better** — explicit workflow entry point |
| Dependency on backend | **Same as Option A** |
| ACL complexity | **Low-Medium** — custom view needs ACL checks |
| Upgrade risk | **Medium** — custom view API may change |
| Browser testing burden | **Medium** — 1 custom rendering path |

### Option C — Fully Custom Acquisition Application

Create a dedicated custom page with custom frontend interaction, workflow state machine, and visual pipeline.

| Criterion | Assessment |
|---|---|
| Implementation cost | **High** — custom SPA-like frontend |
| Maintainability | **Low** — high coupling to internal EspoCRM APIs |
| Consistency with EspoCRM | **Poor** — alien UI in a CRM context |
| User clarity | **Potentially best** — but at high cost |
| Dependency on backend | **Very High** — needs C05/C06/C07 completion |
| ACL complexity | **High** — must reimplement all permission checks |
| Upgrade risk | **High** — fragile on EspoCRM version changes |
| Browser testing burden | **High** — every interaction is custom |

### Recommendation: **Option A** (Native Entity-First)

With one enhancement: a single **"Acquisition Overview" dashlet** (a `record-list` dashlet with custom search data) on the Acquisition dashboard that shows:
- "Getting Started" guidance (collapsible)
- Active strategy count
- Jobs run in last 24h
- New prospects discovered today
- Quick-create buttons for SearchStrategy

This is achievable with **zero custom JS** — dashlet metadata and a standard list view with pre-filtered search data are sufficient.

---

## 7. Recommended Architecture: Native Entity-First + Overview Dashlet

**Primary pattern:** Standard EspoCRM entity tabs with enhanced filters, labels, and list columns.

**Entry point:** The existing "Acquisition" dashboard tab, enhanced with an overview dashlet.

**Custom code required for U02:** 0 lines of JavaScript. All changes are metadata JSON:
- `selectDefs/SearchStrategy.json` — add status filters
- `clientDefs/SearchJob.json` — adjust list column visibility
- `layouts/SearchJob/list.json` — add startedAt, errorMessage columns
- `i18n/*.json` — improve labels
- 1 new dashlet definition JSON — Acquisition Overview

**When to revisit:** After C05 (website research) and C06 (research eligibility gate) are complete, consider a lightweight "Research Queue" action handler on ProspectPool. That is a U04/U05 concern.

---

## 8. Navigation Model

### 8.1 Left Navigation / Tab Bar

Recommend renaming and reordering within the Prospecting module group:

```
Prospecting
  ├── Prospecting Home        ← dashboard (existing "Acquisition" tab, renamed)
  ├── Search Strategies       ← SearchStrategy (was "Search Strategy")
  ├── Discovery Jobs          ← SearchJob (was "Search Job")
  ├── Lead Pool               ← ProspectPool (was "Prospect Pool")
  └── AI Research Evidence    ← ResearchEvidence (unchanged, low prominence)
```

**Implementation note:** EspoCRM tab labels come from `i18n/*.json` → `labels.SearchStrategys` and similar keys. Tab ordering within a module is controlled by entity definition order or custom tab list configuration. For U02, the simplest change is updating labels only. Tab reordering can be done via a custom tab list if needed.

### 8.2 Default Landing Destination

**Recommendation:** The "Acquisition" dashboard tab (renamed to "Prospecting Home") should be the default entry point for users with Prospecting access.

The dashboard already exists and is provisioned by `phase3c01_provision_acquisition_workspace.php`. U02 should:
1. Rename the tab from "Acquisition" to "Prospecting Home"
2. Add an overview/guidance dashlet at the top
3. Reorder dashlets to tell the workflow story left-to-right, top-to-bottom

### 8.3 Role Visibility Matrix

| Entity | Admin | Sales Manager | Sales User | Integration Bot |
|---|---|---|---|---|
| **SearchStrategy** | Full CRUD | Create/Read/Edit all, no Delete | Create/Read/Edit own, no Delete | Create/Read/Edit all, no Delete |
| **SearchJob** | Full CRUD | Create/Read/Edit all, no Delete | Create/Read/Edit own, no Delete | Create/Read/Edit all, no Delete |
| **ProspectPool** | Full CRUD | Create/Read/Edit all, no Delete | Create/Read/Edit own, no Delete | Create/Read/Edit all, no Delete |
| **ResearchEvidence** | Full access | Read all | Read own | Read all |

**Design principle:** Integration Bot is a machine user. It needs API-level CRUD but should not see the dashboard or navigation tabs. This is already handled by the ACL script assigning scope permissions; the dashboard is provisioned per-user.

**Tab visibility recommendation:**

| Entity Tab | Admin | Sales Manager | Sales User | Integration Bot |
|---|---|---|---|---|
| Prospecting Home (dashboard) | ✅ | ✅ | ✅ | ❌ (machine user) |
| Search Strategies | ✅ | ✅ | ✅ | ❌ |
| Discovery Jobs | ✅ | ✅ | ✅ | ❌ |
| Lead Pool | ✅ | ✅ | ✅ | ❌ |
| AI Research Evidence | ✅ | ✅ | ❌ (low value) | ❌ |

---

## 9. Entity-by-Entity UI Specification

### 9.1 SearchStrategy

**Purpose:** Planning entity. Defines what to search for (product + country + persona), which sources to use, and optional keyword overrides. A single SearchStrategy generates multiple SearchJobs (one per keyword × country combination).

**Ideal list columns (current → recommended):**

| Column | Width | Current? | Recommended? | Rationale |
|---|---|---|---|---|
| name (link) | 24 | ✅ | ✅ | Primary identifier |
| product | 14 | ✅ | ✅ | Core strategy dimension |
| country | 12 | ✅ | ✅ | Core strategy dimension |
| targetPersona | 18 | ✅ | ✅ | Who we're targeting |
| sourcePlan | 16 | ✅ | ✅ | Which search sources |
| status | 12 | ✅ | ✅ | Workflow state |
| generatedJobCount | 12 | ✅ | ✅ | How many jobs created |
| createdAt | 16 | ✅ | ✅ | When created |

**Change needed:** Add `region` column (12) for multi-region strategies. The current list is adequate for U02.

**Ideal detail sections (current → recommended):**

| Panel | Current Fields | U02 Changes |
|---|---|---|
| Strategy Definition | name, status, product, country, region, targetPersona, targetCompanyType, sourcePlan | Add inline guidance: "Required: Product, Country, Target Persona. Optional: Region, Company Type." |
| Query Plan | keywords, excludedKeywords, generatedJobCount | Add helper text: "Leave keywords empty to auto-generate from product + persona templates." |
| Ownership | assignedUser, teams, createdAt, createdBy | No change |

**Primary filters (CURRENTLY MISSING → recommended):**

| Filter Name | Label | Logic | U02 Priority |
|---|---|---|---|
| strategiesDraft | Draft | status = DRAFT | Required |
| strategiesReady | Ready | status = READY | Required |
| strategiesActive | Active | status IN (GENERATED, RUNNING) | Required |
| strategiesCompleted | Completed | status = COMPLETED | Required |
| strategiesFailed | Failed | status = FAILED | Nice-to-have |
| strategiesCancelled | Cancelled | status = CANCELLED | Nice-to-have |

**Actions:**

| Action | Placement | ACL | Precondition | Implementable? |
|---|---|---|---|---|
| Create Strategy | List view top button | create | — | ✅ (standard) |
| Edit Strategy | Detail view edit button | edit | — | ✅ (standard) |
| Generate Jobs | Detail view action button | edit | status = READY | ✅ (API exists: `POST /search-strategy/generate-jobs`) |
| Cancel Strategy | Detail action | edit | status IN (DRAFT, READY, GENERATED) | ✅ (field update to CANCELLED) |
| Delete Strategy | Detail action dropdown | delete | no generated jobs | ✅ (standard; add guard in service) |

**Hidden fields for Sales Users:** `keywords`, `excludedKeywords` (advanced), `queryFingerprint` (technical).

### 9.2 SearchJob

**Purpose:** Execution entity. Represents a single search query dispatched to a provider. Tracks status, result counts, timing, and errors.

**Ideal list columns (current → recommended):**

| Column | Width | Current? | Recommended? | Rationale |
|---|---|---|---|---|
| name (link) | 24 | ✅ | ✅ | Primary identifier |
| strategy | 16 | ✅ | ✅ | Parent context |
| product | 14 | ✅ | ✅ | Quick filter |
| keyword | 18 | ✅ | ✅ | What was searched |
| country | 12 | ✅ | ✅ | Where |
| status | 12 | ✅ | ✅ | Workflow state |
| priority | 10 | ✅ | ✅ | P1/P2/P3 |
| resultCount | 10 | ✅ | ✅ | How many found |
| **startedAt** | 14 | ❌ | **✅ Add** | When job ran |
| **errorMessage** | 14 | ❌ | **✅ Add** | Failure reason (truncated) |
| createdAt | 16 | ✅ | ✅ | When created |

Remove from list: `source` (provider name — not useful in list view; keep on detail).

**Change needed:** Add `startedAt` and `errorMessage` columns. Remove `source` from list (keep on detail). Total columns: 11 (reasonable).

**Ideal detail sections (current → recommended):**

| Panel | Current Fields | U02 Changes |
|---|---|---|
| Discovery Job | name, status, strategy, product, keyword, country, source, priority, queryFingerprint | Move queryFingerprint to collapsed/advanced section. Add `failureReason` alongside `errorMessage` for richer error display. |
| Execution | resultCount, acceptedCount, rejectedCount, startedAt, completedAt, errorMessage | Add `prospectCount` (legacy field — may be deprecated). Include timing display: "Ran for X minutes". |
| Ownership | assignedUser, teams, createdAt | No change |

**Primary filters (all exist ✅):**

| Filter Name | Label | Status |
|---|---|---|
| jobsQueued | Queued | ✅ Implemented |
| jobsRunning | Running | ✅ Implemented |
| jobsCompleted | Completed | ✅ Implemented |
| jobsFailed | Failed | ✅ Implemented |
| jobsCancelled | Cancelled | ✅ Implemented |

**Additional filters needed for U02:**

| Filter Name | Label | Logic | Priority |
|---|---|---|---|
| jobsWithResults | Has Results | resultCount > 0 | Recommended |
| jobsToday | Today | createdAt = today | Recommended |
| jobsP1 | Priority P1 | priority = P1 | Nice-to-have |

**Actions:**

| Action | Placement | ACL | Precondition | Implementable? |
|---|---|---|---|---|
| View Job | List row click | read | — | ✅ (standard) |
| Cancel Job | Detail action | edit | status IN (QUEUED, RUNNING) | ✅ (field update) |
| Retry Job | Detail action | edit | status IN (FAILED, CANCELLED) | ⚠️ Needs C05 runner endpoint |
| View Prospects | Detail → prospectPools panel | read | resultCount > 0 | ✅ (relationship panel) |

**Status presentation (color semantics via EspoCRM `style` in entityDefs):**

| Status | Color | Meaning |
|---|---|---|
| QUEUED | `default` (gray) | Waiting for runner |
| RUNNING | `warning` (yellow/orange) | In progress |
| COMPLETED | `success` (green) | Done, results available |
| FAILED | `danger` (red) | Error occurred |
| CANCELLED | `default` (gray, muted) | User stopped |

**Note:** SearchJob entityDefs currently uses `displayAsLabel: true` but does not define `style` for status values. Adding `style` is a single-line JSON metadata change.

### 9.3 ProspectPool

**Purpose:** Result entity. Each record is one discovered prospect from a SearchJob. Tracks the prospect's journey through acquisition pipeline stages (queues) and readiness for CRM promotion.

**Ideal list columns (current → recommended):**

| Column | Width | Current? | Recommended? | Rationale |
|---|---|---|---|---|
| name (link) | 22 | ✅ | ✅ | Company name |
| website | 14 | ❌ | **✅ Add** | Quick external check |
| country | 12 | ✅ | ✅ | Location |
| source | 14 | ✅ | ✅ | Provider name |
| queue | 14 | ✅ | ✅ | Pipeline stage |
| status | 12 | ✅ | ✅ | Processing status |
| researchStatus | 14 | ✅ | ✅ | Research readiness |
| createdAt | 16 | ✅ | ✅ | Discovery date |

Remove from list: `qualificationStatus`, `crmPushStatus` (keep on detail for pipeline tracking).

**Change needed:** Add `website` column. Remove `qualificationStatus` and `crmPushStatus` from list (move to detail only). Total columns: 9 (same as current).

**Ideal detail sections (current → recommended):**

| Panel | Current Fields | U02 Changes |
|---|---|---|
| Raw Prospect | name, externalProspectId, source, sourceUrl, website, country, searchJob | Rename "Raw Prospect" → "Discovery Information". Add inline link to open website in new tab. |
| Acquisition Pipeline | queue, status, researchStatus, qualificationStatus, crmPushStatus, qualifiedAt, crmPushedAt | Add visual pipeline indicator (queue progression). Add "Promote to Research" action. |
| Notes and Ownership | note, assignedUser, teams, createdAt | No change |

**Primary filters (all exist ✅):**

| Filter Name | Label | Status |
|---|---|---|
| discoveryQueue | Discovery Queue | ✅ Implemented |
| qualificationQueue | Qualification Queue | ✅ Implemented |
| researchQueue | Research Queue | ✅ Implemented |
| crmQueue | CRM Queue | ✅ Implemented |

**Additional filters needed for U02:**

| Filter Name | Label | Logic | Priority |
|---|---|---|---|
| newToday | New Today | createdAt = today | Recommended |
| readyForResearch | Ready for Research | researchStatus = PENDING, qualificationStatus = QUALIFIED | Recommended |
| duplicates | Duplicates | queue = DISCOVERY, status = FAILED (dedup rejection) | Nice-to-have |
| pushedToCRM | Pushed to CRM | crmPushStatus = PUSHED | Nice-to-have |

**Actions:**

| Action | Placement | ACL | Precondition | Implementable? |
|---|---|---|---|---|
| View Prospect | List row click | read | — | ✅ (standard) |
| Accept Prospect | Detail action / mass action | edit | queue = DISCOVERY | ⚠️ Needs queue move logic (field update, no API needed) |
| Reject Prospect | Detail action / mass action | edit | queue = DISCOVERY | ⚠️ Same as above |
| Mark Duplicate | Detail action | edit | any queue | ⚠️ Needs dedup state tracking |
| Promote to Research | Detail action / mass action | edit | qualificationStatus = QUALIFIED | ⚠️ Needs queue move logic |
| Push to CRM | Detail action / mass action | edit | crmPushStatus = READY | ⚠️ Needs C05/C06 contract for Lead creation |
| Add Note | Detail → note field | edit | — | ✅ (standard field) |

**Queue pipeline visualization (conceptual):**

```
DISCOVERY ──→ QUALIFICATION ──→ RESEARCH ──→ CRM
  (new)      (reviewed)       (researched)   (pushed to Lead)
    │              │                │
    └── Rejected   └── Rejected     └── Failed
```

### 9.4 Lead (Acquisition Integration)

**Purpose:** The existing Lead entity already has extensive prospecting intelligence fields. U02 should NOT modify Lead entityDefs or layouts — all changes are additive labels and relationship visibility.

**Acquisition origin visibility:**

The "Sync Information" panel on Lead detail already shows: `peCandidateId`, `peSyncStatus`, `peSourceSystem`, `peSourceBatchId`, `peLastSyncAt`, `peQualificationStatus`, `peEngineVersion`, `peScoreRulesVersion`.

**Recommendation for U02:** No changes to Lead. The acquisition provenance is adequate. Future U04/U05 phases may add a "Source Prospect" link from Lead back to ProspectPool.

**ResearchEvidence visibility on Lead:**
The "AI Research Evidence" bottom panel on Lead detail is correctly configured. ResearchEvidence records are read-only relationship children. **No changes needed for U02.**

### 9.5 ResearchEvidence

**Purpose:** Reference/evidence entity. Records individual research findings attached to a Lead. Created by the AI research engine (Phase3B), not by the acquisition workflow.

**Recommendation:** Keep as-is. Tab visible to Admin and Sales Manager. Not part of the primary acquisition workflow. No U02 changes.

---

## 10. List Column Matrix (Recommended)

### SearchStrategy List
| # | Column | Width | Link | Priority |
|---|---|---|---|---|
| 1 | name | 24 | ✅ | Required |
| 2 | product | 14 | — | Required |
| 3 | country | 12 | — | Required |
| 4 | targetPersona | 18 | — | Required |
| 5 | sourcePlan | 16 | — | Required |
| 6 | status | 12 | — | Required |
| 7 | generatedJobCount | 12 | — | Recommended |
| 8 | createdAt | 16 | — | Required |

### SearchJob List
| # | Column | Width | Link | Priority |
|---|---|---|---|---|
| 1 | name | 24 | ✅ | Required |
| 2 | strategy | 16 | ✅ | Required |
| 3 | product | 14 | — | Required |
| 4 | keyword | 18 | — | Required |
| 5 | country | 12 | — | Required |
| 6 | status | 12 | — | Required |
| 7 | priority | 10 | — | Required |
| 8 | resultCount | 10 | — | Required |
| 9 | startedAt | 14 | — | **ADD for U02** |
| 10 | errorMessage | 14 | — | **ADD for U02** (truncated) |
| 11 | createdAt | 16 | — | Required |

### ProspectPool List
| # | Column | Width | Link | Priority |
|---|---|---|---|---|
| 1 | name | 22 | ✅ | Required |
| 2 | website | 14 | — | **ADD for U02** |
| 3 | country | 12 | — | Required |
| 4 | source | 14 | — | Required |
| 5 | queue | 14 | — | Required |
| 6 | status | 12 | — | Required |
| 7 | researchStatus | 14 | — | Required |
| 8 | createdAt | 16 | — | Required |

---

## 11. Detail Section Matrix (Recommended)

### SearchStrategy Detail
| Panel Label | Fields | U02 Changes |
|---|---|---|
| Strategy Definition | name, status, product, country, region, targetPersona, targetCompanyType, sourcePlan | Add helper text metadata (tooltip or description on fields) |
| Query Plan | keywords, excludedKeywords, generatedJobCount | No structural change |
| Ownership | assignedUser, teams, createdAt, createdBy | No change |

### SearchJob Detail
| Panel Label | Fields | U02 Changes |
|---|---|---|
| Discovery Job | name, status, strategy, product, keyword, country, source, priority, queryFingerprint | Move queryFingerprint to bottom; add `failureReason` alongside `errorMessage` |
| Execution | resultCount, acceptedCount, rejectedCount, startedAt, completedAt, errorMessage | Add `prospectCount` (legacy) and timing display |
| Ownership | assignedUser, teams, createdAt | No change |

### ProspectPool Detail
| Panel Label | Fields | U02 Changes |
|---|---|---|
| Discovery Information | name, externalProspectId, source, sourceUrl, website, country, searchJob | Rename from "Raw Prospect"; add website link |
| Acquisition Pipeline | queue, status, researchStatus, qualificationStatus, crmPushStatus, qualifiedAt, crmPushedAt | Add visual pipeline flow |
| Notes and Ownership | note, assignedUser, teams, createdAt | No change |

---

## 12. Filter Matrix

### Implemented ✅
| Entity | Filter | Label |
|---|---|---|
| SearchJob | jobsQueued | Queued |
| SearchJob | jobsRunning | Running |
| SearchJob | jobsCompleted | Completed |
| SearchJob | jobsFailed | Failed |
| SearchJob | jobsCancelled | Cancelled |
| ProspectPool | discoveryQueue | Discovery Queue |
| ProspectPool | qualificationQueue | Qualification Queue |
| ProspectPool | researchQueue | Research Queue |
| ProspectPool | crmQueue | CRM Queue |
| Lead | peTierA/B/C/D, pePendingOutreach, peContactReady, etc. (26 total) | Various |

### Missing — U02 Priority
| Entity | Filter | Label | Logic |
|---|---|---|---|
| **SearchStrategy** | strategiesDraft | Draft | status = DRAFT |
| **SearchStrategy** | strategiesReady | Ready | status = READY |
| **SearchStrategy** | strategiesActive | Active | status IN (GENERATED, RUNNING) |
| **SearchStrategy** | strategiesCompleted | Completed | status = COMPLETED |
| SearchJob | jobsWithResults | Has Results | resultCount > 0 |
| SearchJob | jobsToday | Today | createdAt = today |
| ProspectPool | newToday | New Today | createdAt = today |

### Provisional — depends on future backend
| Entity | Filter | Label | Depends On |
|---|---|---|---|
| ProspectPool | readyForResearch | Ready for Research | C05 research eligibility gate |
| ProspectPool | duplicates | Duplicates | C04 dedup engine |
| ProspectPool | pushedToCRM | In CRM | C06 CRM push pipeline |
| SearchJob | jobsRetrying | Retrying | C05 runner retry logic |

---

## 13. Action / Button Matrix

### Currently Implemented ✅
| Action | Entity | Placement | ACL |
|---|---|---|---|
| Generate Jobs | SearchStrategy | Detail action button | edit |
| Standard CRUD (Create/Edit/Delete) | All entities | Standard Record UI | per-role |

### Recommended for U02
| Action | Entity | Placement | ACL | Precondition | Backend Dependency |
|---|---|---|---|---|---|
| Create Strategy CTA | Dashboard | Overview dashlet button | create | — | None |
| Cancel Job | SearchJob | Detail action dropdown | edit | status IN (QUEUED, RUNNING) | None (field update) |
| Accept Prospect | ProspectPool | Detail action + mass action | edit | queue = DISCOVERY | None (queue field update) |
| Reject Prospect | ProspectPool | Detail action + mass action | edit | queue = DISCOVERY | None (queue field update) |
| Promote to Research | ProspectPool | Detail action + mass action | edit | qualificationStatus = QUALIFIED | None (queue field update) |

### Provisional — depends on future backend
| Action | Entity | Placement | Depends On |
|---|---|---|---|
| Retry Job | SearchJob | Detail action | C05 runner retry endpoint |
| Push to CRM | ProspectPool | Detail action + mass action | C06 CRM push pipeline |
| Mark Duplicate | ProspectPool | Detail action | C04 dedup engine |
| View Lead | ProspectPool | Detail link | C06 CRM linkage |

---

## 14. ACL Visibility Matrix

Based on `phase3c02_1_provision_acquisition_acl.php`:

| Permission | Admin | Sales Manager | Sales User | Integration Bot |
|---|---|---|---|---|
| **SearchStrategy** | | | | |
| Create | yes | yes | yes | yes |
| Read | all | all | own | all |
| Edit | all | all | own | all |
| Delete | all | no | no | no |
| **SearchJob** | | | | |
| Create | yes | yes | yes | yes |
| Read | all | all | own | all |
| Edit | all | all | own | all |
| Delete | all | no | no | no |
| **ProspectPool** | | | | |
| Create | yes | yes | yes | yes |
| Read | all | all | own | all |
| Edit | all | all | own | all |
| Delete | all | no | no | no |

### Recommended ACL adjustments for U02:
- **Sales User: SearchStrategy Read = "team"** (not "own") — strategies are team assets, not individual
- **Integration Bot: disable tab visibility** (API access only) — already handled by not provisioning dashboard to bot user

---

## 15. Dashboard / Landing-Page Requirements

### MVP (U02) — Acquisition Overview Dashlet

Add a new dashlet above the existing 8 Acquisition dashlets:

**Dashlet definition:**
```json
{
  "view": "views/dashlets/abstract/record-list",
  "aclScope": "SearchStrategy",
  "entityType": "SearchStrategy",
  "options": {
    "defaults": {
      "title": "Acquisition Overview",
      "orderBy": "createdAt",
      "order": "desc",
      "displayRecords": 5,
      "includeShared": true,
      "expandedLayout": {
        "rows": [
          [{"name": "name", "link": true}, {"name": "status"}],
          [{"name": "product"}, {"name": "generatedJobCount"}]
        ]
      }
    }
  }
}
```

This shows the 5 most recent strategies with their status and job count. Combined with the existing status-filtered Job dashlets, users get a complete workflow picture.

### Recommended dashboard layout (revised for U02):

```
Row 0: [Acquisition Overview (4w)]                           ← NEW
Row 2: [Search Strategies (2w)]  [Discovery Jobs (2w)]
Row 4: [Queued (1w)] [Running (1w)] [Completed (1w)] [Failed (1w)]
Row 6: [Lead Pool (2w)]          [Research Queue (2w)]
```

### Useful later additions (U04+):
- "Ready for Research" count (needs C05)
- Duplicate rate percentage (needs C04)
- Provider usage breakdown (needs C05 aggregated data)
- Week-over-week discovery trend (needs time-series data)
- Recently promoted to Lead (needs C06)

### Do NOT add for decoration:
- Pie charts of status distribution (EspoCRM dashlets don't natively support charts without custom JS)
- "Acquisition Health Score" (no data contract exists)
- Real-time job progress bars (runner is poll-based, not streaming)

---

## 16. Backend / UI Contract Gaps

### Blocking for U02: NONE

All U02 changes are metadata-only and do not require new backend endpoints or contract changes.

### Non-blocking for U02 (can proceed without):

| Gap | Impact | Mitigation |
|---|---|---|
| No SearchStrategy selectDefs | Users can't filter strategies by status | U02 adds the JSON file and PHP filter classes — metadata-only |
| No "Accept/Reject" on ProspectPool | Users can't easily curate prospects | U02 adds queue-update actions — field writes via standard Record API |
| No "Retry Job" endpoint | Failed jobs can't be re-run from UI | U02 labels the action but gates it behind C05; shows "Coming Soon" tooltip |
| No "Push to CRM" pipeline | Prospects can't auto-create Leads | U02 shows crmPushStatus as read-only; gated behind C06 |
| No cancel-Job API guard | Cancel button exists but service doesn't validate transition | U02 adds status transition validation in SearchJob service (PHP metadata change) |
| `errorMessage` vs `failureReason` | Two fields for errors — confusing | U02 consolidates: `errorMessage` for technical, `failureReason` for user-facing summary |

### Later enhancements (U04+):

| Gap | Needed For | Phase |
|---|---|---|
| Retry endpoint in runner | "Retry Job" button functional | C05 |
| Research eligibility gate | "Ready for Research" filter accurate | C05 |
| CRM push pipeline | "Push to CRM" action functional | C06 |
| Dedup counters in UI | Duplicate detection visibility | C04 (data exists, needs UI wiring) |
| Lead back-link from ProspectPool | Trace prospect→lead journey | C06 |

---

## 17. MVP Scope for Phase3U02

### Included in U02 (metadata-only, zero JS):

1. **Add SearchStrategy status filters** — `selectDefs/SearchStrategy.json` + 4 PHP filter classes (mirror SearchJob filter pattern)

2. **Update SearchJob list layout** — add `startedAt`, `errorMessage` columns; remove `source` from list

3. **Update ProspectPool list layout** — add `website` column; remove `qualificationStatus`, `crmPushStatus` from list

4. **Improve i18n labels:**
   - `SearchStrategys` → "Search Strategies"
   - `Create SearchStrategy` → "Create Search Strategy"
   - `ProspectPools` → "Lead Pool"
   - `Create ProspectPool` → "Create Prospect"
   - `prospectPools` (link label) → "Discovered Prospects"
   - Add human-readable labels for `queryFingerprint` → "Query Fingerprint" (already OK) with tooltip "Internal deduplication key"
   - Add `externalProspectId` → "Provider Reference ID"

5. **Add status color styles** to SearchJob and SearchStrategy entityDefs (`style` map on status field)

6. **Add Acquisition Overview dashlet definition**

7. **Update Acquisition dashboard layout** to include overview dashlet

8. **Add SearchJob detail actions:** Cancel Job (status transition guard in service layer)

9. **Add ProspectPool detail actions:** Accept, Reject (queue transition via field update)

10. **Rename Acquisition dashboard tab** → "Prospecting Home" (i18n change in dashlet labels)

### Explicitly deferred from U02:
- Retry Job functionality
- Push to CRM
- Mark Duplicate
- Any custom JavaScript views
- Any backend contract changes
- Any C05/C06/C07 dependencies

---

## 18. Deferred Enhancements

| Enhancement | Phase | Dependency |
|---|---|---|
| "Retry Job" action functional | U04 | C05 runner retry endpoint |
| "Push to CRM" mass action | U05 | C06 CRM push pipeline |
| Research eligibility filter on ProspectPool | U04 | C05 research gate |
| Duplicate detection badge on ProspectPool | U04 | C04 dedup integration |
| "View Lead" back-link from ProspectPool | U05 | C06 CRM linkage |
| Acquisition pipeline visualization (custom view) | U06 | C06 + user feedback |
| Provider performance dashboard | U07 | C05 aggregated metrics |
| Email notification on job failure | U06 | EspoCRM email + C05 runner events |
| Bulk strategy creation wizard | U07 | C05 template engine maturity |

---

## 19. File-Level Implementation Map for U02

### Files to CREATE:

| # | File | Content |
|---|---|---|
| 1 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/selectDefs/SearchStrategy.json` | 4-6 primary filter entries |
| 2 | `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchStrategy/PrimaryFilters/StrategiesDraft.php` | Filter: status = DRAFT |
| 3 | `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchStrategy/PrimaryFilters/StrategiesReady.php` | Filter: status = READY |
| 4 | `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchStrategy/PrimaryFilters/StrategiesActive.php` | Filter: status IN (GENERATED, RUNNING) |
| 5 | `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/SearchStrategy/PrimaryFilters/StrategiesCompleted.php` | Filter: status = COMPLETED |
| 6 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/dashlets/AcquisitionOverview.json` | Overview dashlet definition |

### Files to MODIFY:

| # | File | Change |
|---|---|---|
| 7 | `crm-extension/Resources/entityDefs/SearchJob.json` | Add `style` to status field |
| 8 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchJob.json` | Mirror #7 |
| 9 | `crm-extension/Resources/entityDefs/SearchStrategy.json` | Add `style` to status field |
| 10 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SearchStrategy.json` | Mirror #9 |
| 11 | `crm-extension/Resources/layouts/SearchJob/list.json` | Add startedAt, errorMessage; remove source |
| 12 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/SearchJob/list.json` | Mirror #11 |
| 13 | `crm-extension/Resources/layouts/ProspectPool/list.json` | Add website; remove qualificationStatus, crmPushStatus |
| 14 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/layouts/ProspectPool/list.json` | Mirror #13 |
| 15 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/SearchStrategy.json` | Label improvements |
| 16 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/SearchJob.json` | Label improvements |
| 17 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/ProspectPool.json` | Label improvements |
| 18 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json` | Dashboard tab name |
| 19 | `deployment/provisioning/phase3c01_provision_acquisition_workspace.php` | Add AcquisitionOverview dashlet to layout |
| 20 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/clientDefs/SearchJob.json` | Update filterList if needed |
| 21 | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/clientDefs/SearchStrategy.json` | Add filterList |

**Total: 6 new files, 15 modified files. Zero JavaScript. Zero backend contract changes.**

---

## 20. Conflict Map Against Phase3C05/C06/C07

| C05 (Website Research) | U02 Conflict? | Notes |
|---|---|---|
| `website_research.py` | None | Python backend, U02 is PHP metadata |
| Research eligibility logic | None | U02 shows `researchStatus` as read-only; C05 writes it |
| Research gate criteria | None | U02 doesn't define criteria; C05 owns that |

| C06 (CRM Push Pipeline) | U02 Conflict? | Notes |
|---|---|---|
| Lead creation from ProspectPool | None | U02 shows `crmPushStatus` as read-only label |
| Push endpoint | None | U02 doesn't call it |
| Prospect→Lead linkage | None | U02 defers "View Lead" back-link |

| C07 (Email/Outreach Integration) | U02 Conflict? | Notes |
|---|---|---|
| Email campaign linkage | None | U02 doesn't touch Lead outreach fields |
| Brevo integration | None | Separate API route, not modified by U02 |

**Verdict: Zero conflicts.** U02 changes are pure CRM metadata and label improvements with no intersection with C05/C06/C07 Python backend work.

---

## 21. Confirmation

```
Production code modified:         NO
Metadata modified:                NO (audit only)
Layouts modified:                 NO
ClientDefs modified:              NO
ACL modified:                     NO
Buttons added:                    NO
Dashboards added:                 NO
Routes added:                     NO
Custom views added:               NO
Entity definitions changed:       NO
Backend contracts changed:        NO
SearchJob states changed:         NO
Provider behavior changed:        NO
Runner orchestration changed:     NO
ProspectPool persistence changed: NO
Second acquisition workflow created: NO
Browser automation run:           NO
Extension packages installed:     NO
Git commit created:               NO
```

---

## Final Verdict

**READY FOR U02**

**Recommended UI Architecture:** Native entity-first (Option A) + single Acquisition Overview dashlet

**Recommended Default Entry Point:** "Prospecting Home" dashboard tab (renamed from "Acquisition")

**Blocking Contract Gaps:** 0

All U02 changes are achievable through metadata JSON files and standard EspoCRM extension mechanisms. No JavaScript, no backend contract changes, no C05/C06/C07 dependencies.

**Report path:** `docs/PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md`
