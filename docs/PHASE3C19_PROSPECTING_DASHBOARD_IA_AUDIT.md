# Phase3C19 Prospecting Dashboard IA Audit

**Status:** Audit (read-only product IA review)
**Date:** 2026-07-27
**Baseline:** `master` @ `74f0f1eb`
**Governance context:** A3 Navigation Amendment accepted; `phase3c17_navigation.json` marker `phase3c19-ia-v1`

---

## Executive Summary

The `ProspectingDashboard` custom page currently operates as a **navigation launcher** — a secondary navigation layer that duplicates the left navbar's Center entries. This audit evaluates whether the dashboard should remain a launcher or be converted into an operational workspace, and identifies the structural duplication between the navbar, the dashboard's left sidebar, and its center cards.

**Key finding:** Three navigation surfaces expose the same Center entries, and the dashboard sidebar is out of date versus the A3 navigation target. The recommended path is **Option B — Operational Workspace** that removes the redundant launcher role and surfaces live work state (queues, KPIs, workflow status) as the primary content.

---

## 1. Current State

### 1.1 ProspectingDashboard Definition

**Scope:** `scopes/ProspectingDashboard.json`

| Property | Value | Meaning |
|---|---|---|
| `entity` | `false` | Not an entity — no CRUD, no persistence |
| `object` | `false` | Not a business object |
| `tab` | `true` | Tab-capable; visible in `config.tabList` |
| `acl` | `false` | No ACL ownership — inherits visibility from entity scopes |

**ClientDefs:** `clientDefs/ProspectingDashboard.json`
- Controller: `custom:controllers/prospecting-dashboard`
- Icon: `fas fa-binoculars` (binoculars/scanning)
- Color: `#0B6E4F` (Prospecting green)

**Controller:** `controllers/prospecting-dashboard.js` — Thin; renders `custom:views/prospecting/dashboard`.

**View:** `views/prospecting/dashboard.js` — Renders a launcher page with:
- Left sidebar: navigation-style Center links + workflow diagram
- Main content: Center entry cards + summary metrics + recent activity

**Template:** `templates/prospecting/dashboard.tpl` — Handlebars, two-column layout.

### 1.2 Navigation Ownership (A3 current)

The `phase3c17_navigation.json` (marker `phase3c19-ia-v1`) defines:

```
潜客开发 (divider: phase3c17-prospecting)
├ ProspectingDashboard     ← 潜客运营
├ ProspectingSearch        ← 搜索中心
└ DraftApproval            ← 触达中心

客户管理 (divider: phase3c17-customer-management)
├ Account, Contact, Lead, Opportunity

商务 (divider: phase3c19-commercial)
└ Quote                    ← 报价中心 (moved from 潜客开发 by A3)

支持 (divider: phase3c19-support)
└ KnowledgeBaseArticle

活动 (divider: phase3c17-activities)
└ Email

更多 (divider: phase3c17-more)
└ Task, Calendar
```

Navigation exposes **four** entries under the Prospecting divider: 潜客运营, 搜索中心, 触达中心, plus 情报中心 as a composition reference (navigates to Lead under 客户管理).

Quote Center is **no longer** under 潜客开发 — it lives under the 商务 divider.

### 1.3 Dashboard Left Sidebar (current code)

```text
潜客开发 (sidebar panel header)
├ 运营看板               (#ProspectingDashboard)
├ 搜索中心               (#ProspectingSearch)
├ 情报中心               (#Lead)
├ 触达中心               (#DraftApproval)
└ 报价中心               (#Quote)          ← STALE: not under 潜客开发 anymore

工作流 (sidebar panel header)
├ 1. 发现潜客
├ 2. 调研线索
├ 3. 审核触达
└ 4. 管理报价
```

### 1.4 Dashboard Center Cards (current code)

Four cards in a 2×2 grid — each with a title link and drill-down entries:

| Card | Href | Entries |
|---|---|---|
| **搜索中心** | `#ProspectingSearch` | Search Strategies, Search Jobs, Prospect Pool |
| **情报中心** | `#Lead` | Leads, Research Evidence, Sales Feedback, Learning Signals |
| **触达中心** | `#DraftApproval` | Draft Approvals, Pending Send, Failed Send, Send Executions, Reply Events, Email Events |
| **报价中心** | `#Quote` | Quotes, Quote Approvals, Proforma Invoices |

### 1.5 Dashboard Summary Metrics

Five metric cards, client-side counted via Collection API:

| Metric | Entity | Filter |
|---|---|---|
| Total Prospects | ProspectPool | `{}` (all) |
| New This Week | ProspectPool | `where: lastXDays createdAt 7` |
| Need Research | ProspectPool | `primaryFilter: prospectsReadyForResearch` |
| Research Completed | ProspectPool | `where: researchStatus = COMPLETED` |
| High Priority | SearchJob | `where: priority = P1` |

Plus: Recent Discovery Activity table (8 most recent SearchJobs by `createdAt desc`).

### 1.6 Command Center (separate surface)

The `销售开发指挥中心` is a **user Preferences dashboard tab**, provisioned by `phase3c17_provision_sales_development_command_center.php`. It is a distinct surface from `ProspectingDashboard`:

| Dimension | ProspectingDashboard | Command Center |
|---|---|---|
| Type | Custom page (`#ProspectingDashboard`) | Dashboard tab in Preferences |
| Content | Center cards + summary metrics | Queue dashlets (Records + extension dashlets) |
| Provisioner | None (code-shipped) | `phase3c17_provision_sales_development_command_center.php` |
| Access | Tab click → custom page | Dashboard tab → EspoCRM dashboard grid |

Command Center dashlets (12 items in a 4-column grid):

**TOP band (summaries):**
- 潜客概览 (ProspectingSummary) — 5 metric cards
- 获客概览 (AcquisitionOverview) — SearchStrategy record-list

**MIDDLE band (queues):**
- 我的任务 (Task, `actual`, `onlyMy`)
- 待研究客户 (AcquisitionResearchQueue)
- 待触达 (DraftApproval, `c17Pending`)
- 待发送 (SendExecution, `c18ReadyToSend`)
- 待回复 (ReplyEvent, `c17AwaitingReply`)
- 待审批 (Approval, `c17Pending`)

**BOTTOM band (activity):**
- 客户池 (AcquisitionLeadPool)
- 新增客户 (ProspectingRecentDiscovery)
- 研究完成（任务）(AcquisitionJobsCompleted)
- 研究完成（证据）(RecentResearchEvidence)

---

## 2. IA Problems

### 2.1 Triple Navigation Duplication (CRITICAL)

The same Center entries appear in three places simultaneously, without differentiation:

```
LEFT NAVBAR             DASHBOARD SIDEBAR       DASHBOARD CENTER CARDS
────────────────────    ────────────────────    ──────────────────────
潜客运营 ← tab          运营看板 ← active link   (not in center cards)
搜索中心 ← tab          搜索中心 ← link          搜索中心 ← card + entries
(Lead via 客户管理)      情报中心 ← link          情报中心 ← card + entries
触达中心 ← tab          触达中心 ← link          触达中心 ← card + entries
(Quote via 商务)         报价中心 ← link          报价中心 ← card + entries
```

**Impact:** Users see the same "Search Center" label in the navbar, the dashboard sidebar, and the dashboard center card. There is no differentiation in presentation, behavior, or purpose. The dashboard sidebar is a literal copy of the navbar — it is a **second navigation layer**.

### 2.2 Dashboard Sidebar Stale vs. A3 (HIGH)

The dashboard sidebar hardcodes Quote Center under the 潜客开发 panel header, but A3 moved Quote to the 商务 divider. The sidebar has not been updated to reflect the new IA:

| A3 Navigation | Dashboard Sidebar | Drift |
|---|---|---|
| 潜客开发: Dashboard, Search, (Intelligence-ref), Outreach | 潜客开发: Dashboard, Search, Intelligence, Outreach, **Quote** | Quote incorrectly listed |
| 商务: Quote | — | Missing from sidebar entirely |

### 2.3 Dashboard Sidebar Redundancy (MEDIUM)

The left sidebar occupies 25% of the viewport (`col-sm-3`) to render a static link list that duplicates the global navbar. The navbar is always visible in EspoCRM; there is no UX need for an in-page copy.

### 2.4 Launcher vs. Workspace Identity Confusion (MEDIUM)

The dashboard's name is "潜客运营" (Prospecting Operations), which implies an operational workspace. But its primary content is Center navigation cards — a launcher. The secondary content (5 summary metrics + recent activity) is operational but minimal. This creates an identity problem:

- **Name says:** operational workspace
- **Content says:** navigation launcher with a few counters
- **ADR-C17 says:** "cross-center landing surface; aggregates operational data and routes users into Centers"

The dashboard is currently more launcher than aggregator. The only aggregated data is 5 ProspectPool/SearchJob counters — no pipeline status, no queue depths, no workflow state.

### 2.5 ProspectingSummary Dashlet Duplication (LOW)

The `ProspectingSummary` dashlet (used in the Command Center TOP band) provides metric cards nearly identical to the dashboard's summary section. Both count ProspectPool totals, research status, etc. The dashboard's metrics are computed client-side via Collection API; the dashlet has its own implementation.

### 2.6 情报中心 Entry Gap (LOW)

The dashboard center card shows 情报中心 with entries: Leads, Research Evidence, Sales Feedback, Learning Signals. But the A3 navigation lists 情报中心 as a composition reference under 潜客开发 — it navigates to Lead. The dashboard presents it as a standalone Center with its own entries, which is a richer presentation than the navigation provides. This is not wrong, but it highlights that the dashboard's Center cards serve a different purpose (entity discovery) than the navigation (entry point routing).

---

## 3. Analysis

### 3.1 Current Responsibility

**Is ProspectingDashboard currently a navigation replacement?**

Partially. The left sidebar is functionally a navigation replacement — it replicates the navbar's Center links. The center cards go beyond navigation by exposing drill-down entity entries within each Center, which the flat navbar cannot express. The dashboard is a **hybrid**: nav sidebar + entity directory + summary counters.

**Is it an operational dashboard?**

No. The only live data is 5 counters and a recent-activity table. There are no queue lists, no KPI trends, no workflow visualization, no status summaries. The Command Center (`销售开发指挥中心`) is the operational dashboard.

**Is it a workflow overview?**

Partially. The workflow panel in the sidebar shows the 4-step workflow (Discover → Research → Outreach → Quotes) as static text. This is informational, not interactive.

**Is it a KPI workspace?**

No. The 5 metrics are simple counts, not KPIs. No trends, no targets, no comparisons, no time-series data.

### 3.2 Duplication Acceptability

| Duplication | Acceptable? | Rationale |
|---|---|---|
| Navbar 搜索中心 ↔ Dashboard sidebar 搜索中心 | **No** | The navbar is always visible; sidebar adds zero signal |
| Navbar 触达中心 ↔ Dashboard sidebar 触达中心 | **No** | Same — pure duplication |
| Navbar 潜客运营 ↔ Dashboard sidebar 运营看板 | **Acceptable** | "You are here" indicator; self-referential link is fine |
| Dashboard sidebar 报价中心 ↔ Navbar 商务/Quote | **No + stale** | Quote not under 潜客开发 anymore; sidebar should not list it under Prospecting |
| Dashboard center cards ↔ Navbar entries | **Partially** | Center cards add entity discovery that navbar cannot express; but the card title links duplicate navbar entries exactly |
| Dashboard summary metrics ↔ Command Center ProspectingSummary | **Tolerable** | Different surfaces, but the Command Center should be the authoritative metric surface |

### 3.3 Root Cause

The dashboard was designed in C16/C17 when the navigation model was entity-first and the tab bar was cluttered. ADR-C17 §PS-3 promoted Dashboard from "supporting-only" to "Primary Center Entry" and "main Prospecting landing page." At that time, navigation did not have the clean divider structure A3 now provides. The dashboard's launcher role was a workaround for a navigation IA that has since been resolved.

With A3, the navigation is clean: 4 entries under 潜客开发, Quote under 商务. The navbar now provides direct Center access. The dashboard's launcher role has been superseded.

---

## 4. Recommended Target Design

### 4.1 Recommendation: Option B — Operational Workspace

**Convert ProspectingDashboard from a launcher into an operational workspace.**

The navbar now handles navigation. The dashboard should own "current work state."

### 4.2 Target Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ 潜客运营                                  [today's date]     │
│ "今日工作概览"                                              │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│ │ 待发送   │ │ 发送失败 │ │ 待回复   │ │ 待审批           │ │
│ │   12     │ │    3 ⚠   │ │    7     │ │    2             │ │
│ │ READY    │ │ FAILED   │ │ triage   │ │ PENDING          │ │
│ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│                                                              │
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │ 待研究客户      [8] │ │ 今日跟进                   [5]  │ │
│ │ researchQueue       │ │ peFollowUpDue                   │ │
│ │ ProspectPool        │ │ Lead                            │ │
│ └─────────────────────┘ └─────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │ 待触达           [3] │ │ 待报价评审                 [1]  │ │
│ │ c17Pending           │ │ peProposalReviewRequired         │ │
│ │ DraftApproval        │ │ Lead                            │ │
│ └─────────────────────┘ └─────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Pipeline Summary                                         │ │
│ │ [潜客池: 247] → [研究中: 84] → [已研究: 63] → [已触达: 19] │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Recommended Dashlet Inventory

Remove:
- Left sidebar (Center link list — superseded by navbar)
- Center entry cards (entity discovery — superseded by navbar + entity list views)
- Workflow static panel (informational only; no action)
- Client-side metric counters (superseded by Command Center ProspectingSummary)
- Recent Discovery Activity table (superseded by Command Center bottom band)

Add (all read-only, ACL-gated, no in-dashlet mutation):

| Priority | Dashlet | Entity | Filter | Purpose |
|---|---|---|---|---|
| P0 | 待发送 | SendExecution | `c18ReadyToSend` | Morning triage — what goes out today |
| P0 | 发送失败 | SendExecution | `c18FailedSend` | Highest urgency — delivery failures |
| P0 | 已回复待处理 | ReplyEvent | `c19OpenReplies` | Customer replies needing triage |
| P1 | 待审批 | Approval | `c17Pending` | Commercial approvals awaiting decision |
| P1 | 待研究客户 | ProspectPool | `researchQueue` | Research backlog |
| P1 | 今日跟进 | Lead | `peFollowUpDue` | Scheduled follow-ups due today |
| P1 | 待触达 | DraftApproval | `c17Pending` | Drafts awaiting review |
| P2 | 待报价评审 | Lead | `peProposalReviewRequired` | Proposals needing commercial evaluation |
| P2 | 研究失败返工 | Lead | `peResearchFailed` | Research that needs rework |
| P3 | Pipeline Summary | — (composite) | Aggregated counts | Cross-stage funnel visibility |

All queues use **existing server-side PrimaryFilters** — zero new filter classes needed (pending `c19OpenReplies` from C19 WP1).

### 4.4 Principles

1. **Navigation owns "where to go."** The left navbar is the authoritative Center routing surface. The dashboard must not duplicate it.
2. **Dashboard owns "current work state."** The dashboard answers "what needs my attention right now?" with live queue depths and pipeline status.
3. **Read-only composition.** All dashlets are Records/record-list types with existing PrimaryFilters. No in-dashlet action buttons, no inline edits, no mutation strings — same contract as Command Center.
4. **No new entities, no new filters.** All queue filters already exist (C17/C18) or are in-flight (C19 WP1 `c19OpenReplies`).
5. **Separate from Command Center.** The ProspectingDashboard custom page and the Command Center dashboard tab serve different roles: the custom page is the first-tab landing surface showing a curated subset; the Command Center is the full grid of all queues for deep work.

### 4.5 ProspectingDashboard vs. Command Center

| Dimension | ProspectingDashboard | Command Center |
|---|---|---|
| **Role** | Daily work-status landing page | Full operational grid |
| **Audience** | All Prospecting roles | All Prospecting roles |
| **Content** | Curated subset (~8 queues + pipeline summary) | Full inventory (12+ dashlets in 3 bands) |
| **Layout** | Responsive 2-3 column cards | 4-column dashboard grid |
| **Access** | First tab under 潜客开发 | Dashboard tab "销售开发指挥中心" |
| **Provisioning** | Code-shipped custom page | Provisioner-managed Preferences |

The two surfaces are **complementary**, not redundant. The custom page is the "morning glance" — what to do first. The Command Center is the "deep work" surface — all queues with full filtering.

---

## 5. Boundary Definition

### 5.1 Ownership Model

```text
Navigation (navbar)
  Owns: "Where to go"
  Authority: ADR-C17 + navigation.json + materializer
  Content: Center entry surfaces (direct entry points)
  Example: Click 搜索中心 → opens ProspectingSearch page

ProspectingDashboard (custom page)
  Owns: "Current work state"
  Authority: Custom page code (views/prospecting/dashboard.js)
  Content: Live work queues, pipeline status, KPI summaries
  Example: Sees 3 failed sends → navigates to SendExecution list

Command Center (dashboard tab)
  Owns: "Full operational grid"
  Authority: phase3c17_provision_sales_development_command_center.php
  Content: Complete queue inventory in 3-band 4-column grid
  Example: All 12 dashlets with full filtering capability

Center Pages (ProspectingSearch, entity lists)
  Owns: "Do the work"
  Content: Entity CRUD, filtered lists, workflow actions
```

### 5.2 Navigation Contract (frozen)

The dashboard must not:
- Replicate the navbar's Center list
- Introduce new navigation entry points
- Bypass the materializer governance chain
- Duplicate the `centers` definitions from `navigation.json`
- Create a parallel "where to go" surface

The dashboard may:
- Link to Center entry surfaces from queue items (e.g., click "发送失败: 3" → `#SendExecution/list/primary=c18FailedSend`)
- Surface entity counts and queue depths for existing scopes
- Compose existing dashlets and PrimaryFilters
- Present pipeline-stage aggregation from existing entity data

---

## 6. Impact Assessment

### 6.1 Files Potentially Affected

| File | Change | Risk |
|---|---|---|
| `views/prospecting/dashboard.js` | **Rewrite** — replace launcher logic with queue/pipeline composition | Medium |
| `templates/prospecting/dashboard.tpl` | **Rewrite** — new layout without sidebar, with queue cards | Medium |
| `controllers/prospecting-dashboard.js` | Likely unchanged (thin controller) | Low |
| `clientDefs/ProspectingDashboard.json` | Possibly unchanged (icon/color may stay) | Low |
| `i18n/*/ProspectingDashboard.json` | **Update** — new labels for queue cards, pipeline summary; remove obsolete launcher labels | Low |
| `i18n/*/Global.json` | Possibly add `C19Dashboard*` labels if reused from Command Center | Low |
| `scopes/ProspectingDashboard.json` | **Unchanged** — `entity:false, object:false, tab:true, acl:false` still correct | None |
| `navigation.json` | **Unchanged** — `ProspectingDashboard` entry unchanged | None |
| Materializer | **Unchanged** | None |
| Command Center provisioner | **Unchanged** — separate surface | None |
| Contract tests | **Update** — new assertions for workspace composition; remove launcher structure tests | Medium |

### 6.2 ADR Required?

**Yes — an ADR amendment is recommended** but not strictly required if the change is scoped as a C17 navigation-governed evolution. The key ADR touch points:

| ADR | Clause | Impact |
|---|---|---|
| ADR-C17 | PS-3: "Dashboard is Primary Center Entry and landing surface" | Dashboard role evolves from launcher to workspace — **consistent** with "landing surface" intent; richer operational expression of the same role |
| ADR-C17 | §Dashboard: "aggregates operational data and routes users into Centers" | Workspace model strengthens "aggregates operational data"; routing is reduced (navbar handles it) |
| ADR-C17 | Frozen boundary: "Centers are navigation and workspace composition" | Workspace composition unchanged; still using existing dashlets and PrimaryFilters |

**Recommendation:** Record as a C19 Dashboard IA amendment (similar to A3) rather than a full C17 ADR amendment. The dashboard's role is evolving within PS-3's authority, not overturning it.

### 6.3 Navigation Changes Required?

**No.** The `navigation.json` entry for `ProspectingDashboard` under the 潜客开发 divider is unchanged. The dashboard's `tab:true` scope is unchanged. No materializer or `config.tabList` changes are needed.

### 6.4 C19 Scope Conflict?

**No conflict, positive synergy.** The workspace dashboard will consume C19 WP1's `c19OpenReplies` filter and C19 WP3's Command Center queue definitions. Converting the dashboard to a workspace aligns with the C19 Charter's mission: "evolve the Sales Development Command Center from a monitoring dashboard into a daily sales action center."

The C19 Charter §5 boundary is respected: no new entities, no navigation mutation, no ACL redesign, no in-dashlet mutation.

### 6.5 Test Impact

- Remove assertions that pin the launcher structure (sidebar link list, center card grid)
- Add assertions for workspace queue composition (dashlet types, PrimaryFilter bindings, read-only guarantees)
- Existing 356 tests preserved; C19 pre-existing failures (3) unaffected

---

## 7. Migration Plan

### Phase 1 — Design Acceptance
1. Accept this audit as the design authority for ProspectingDashboard workspace conversion.
2. Record the decision as a C19 Dashboard IA amendment (governance only).
3. Freeze the target layout and dashlet inventory (§4.2–4.3).

### Phase 2 — Remove Launcher Artifacts
1. Remove left sidebar template block (Center link list + workflow panel).
2. Remove center card grid (buildCenters JS + template block).
3. Remove client-side summary metrics (buildEmptyMetrics, countRecords, loadDashboardData).
4. Remove recent-activity table (loadRecentJobs + template block).
5. Clean up obsolete i18n labels from `ProspectingDashboard.json`.
6. Update test contracts to reflect removed launcher structure.

### Phase 3 — Build Workspace Composition
1. Implement queue-card dashlets using EspoCRM native `Records` views with existing PrimaryFilters.
2. Implement Pipeline Summary composite dashlet (aggregated counts across stages).
3. Add i18n labels for workspace-specific titles and descriptions.
4. Update contract tests for workspace composition.

### Phase 4 — Validation
1. Verify no navbar duplication remains in the dashboard.
2. Verify all queue dashlets are ACL-gated and read-only.
3. Verify no mutation strings on composition surfaces.
4. Verify Command Center is unaffected (separate surface, separate provisioner).
5. Verify navigation contract: dashboard does not introduce new entry points.

---

## 8. Non-Goals (Frozen)

The following are explicitly **NOT** in scope for this audit or its recommended implementation:

- No navigation changes (`navigation.json`, materializer, `config.tabList`)
- No new business entities or scopes
- No new PrimaryFilters (all queues use existing filters)
- No ACL redesign or role changes
- No in-dashlet action buttons, inline edits, or mutation
- No workflow-lifecycle changes (ReplyTriageService, SendExecutionTransitionService, etc.)
- No Command Center provisioner changes
- No removal or restructuring of the Command Center dashboard tab
- No conversion/funnel/ROI analytics (C19 Charter §5 prohibition)
- No change to the ProspectingDashboard scope definition (`tab:true`, `acl:false`)
- No change to the dashboard controller (remains thin delegation layer)
- No new custom Center composition pages
- No C19 WP1 or WP2 scope changes — the workspace dashboard **consumes** their outputs; it does not drive their implementation

---

## 9. Decision Summary

| Question | Answer |
|---|---|
| Is the dashboard currently a launcher or workspace? | **Launcher** — 80% navigation links, 20% operational data |
| Is duplication with the navbar acceptable? | **No** — the left sidebar and center card title links duplicate navbar entries without differentiation |
| Is the dashboard stale vs. A3? | **Yes** — sidebar lists Quote under 潜客开发; A3 moved it to 商务 |
| Should the dashboard remain a launcher? | **No** — the navbar now provides clean Center access; the launcher role is superseded |
| Should the dashboard become an operational workspace? | **Yes** — this aligns with ADR-C17 PS-3 ("landing surface") and C19 Charter ("daily sales action center") |
| What is the boundary between navigation and dashboard? | Navigation = "where to go"; Dashboard = "current work state" |
| Does this require an ADR? | Recommended: C19 Dashboard IA amendment (within PS-3 authority) |
| Does this require navigation changes? | No |
| Does this conflict with C19 scope? | No — positive synergy; consumes C19 WP1/WP3 outputs |

---

## 10. Evidence

### Code Evidence
- `scopes/ProspectingDashboard.json` — scope definition
- `clientDefs/ProspectingDashboard.json` — client controller binding
- `controllers/prospecting-dashboard.js` — thin controller, renders dashboard view
- `views/prospecting/dashboard.js` — launcher logic: buildCenters, buildEmptyMetrics, countRecords
- `templates/prospecting/dashboard.tpl` — sidebar link list, center cards, summary metrics, recent activity
- `i18n/{en_US,zh_CN}/ProspectingDashboard.json` — launcher-focused labels
- `i18n/{en_US,zh_CN}/Global.json` — Center labels (`C17Dashboard*`, `C18Dashboard*`)

### Navigation Evidence
- `deployment/navigation/phase3c17_navigation.json` — marker `phase3c19-ia-v1`; A3 dividers; Center definitions
- `deployment/provisioning/phase3c17_provision_operational_centers_navigation.php` — canonical materializer

### Command Center Evidence
- `deployment/provisioning/phase3c17_provision_sales_development_command_center.php` — separate surface provisioner
- 15 dashlet definitions under `Resources/metadata/dashlets/`

### Governance Evidence
- `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` — PS-3, Dashboard role, frozen boundaries
- `docs/architecture/ADR_NAVIGATION_AMENDMENT_A3.md` — current A3 navigation target
- `docs/PHASE3C19_CHARTER.md` — C19 Charter §5 boundaries
- `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` — Command Center queue evolution (WP3)

---

*Audit only. No implementation. No navigation.json, metadata, code, test, dashboard, or commit changes authorized by this document.*
