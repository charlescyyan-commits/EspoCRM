# ADR: ProspectingDashboard — Operational Workspace Evolution

**Status:** Accepted

**Date:** 2026-07-27 (proposed); 2026-07-27 (accepted — governance review)

**Amends:** `docs/architecture/ADR_C17_NAVIGATION_OPERATIONAL_CENTERS.md` §Dashboard (PS-3)

**Governance input:** `docs/PHASE3C19_PROSPECTING_DASHBOARD_IA_AUDIT.md` (2026-07-27)

**Relationship:** Evolution within PS-3 authority. Does not overturn, deprecate, or redesign ADR-C17. Does not modify ADR-C16.

**Decision Owners:**
- Principal Software Architect, EspoCRM Prospecting module
- Phase3C19 Governance Review

---

## 1. Context

### 1.1 C17 Original Purpose

ADR-C17 §PS-3 promoted `ProspectingDashboard` from "supporting-only" (C16 N-IA-3: hidden from `config.tabList`) to a **Primary Center Entry (Class A)** and the **default Prospecting landing surface**. Its role was defined as:

> "Aggregates operational data and routes users into Centers."

At the time of C17, the navigation IA was entity-first and cluttered — twelve entity tabs under one divider, no workflow grouping, no clean Center entry points. The dashboard's launcher role (left sidebar with Center links + center entry cards with drill-down entity lists) was a **compensating mechanism** for navigation gaps that have since been resolved.

### 1.2 C19 Navigation Cleanup

Phase3C19 Navigation Amendment A3 (`docs/architecture/ADR_NAVIGATION_AMENDMENT_A3.md`, Accepted 2026-07-27) restructured the top-level IA:

```
Before A3                      After A3
───────────                    ────────
潜客开发                        潜客开发
├ 潜客运营 (Dashboard)          ├ 潜客运营 (Dashboard)
├ 搜索中心                       ├ 搜索中心
├ 触达中心                       ├ 情报中心 (composition reference)
├ 报价中心                       └ 触达中心
└ (情报中心 implicit)
                               商务
                               └ 报价中心 (moved)

                               支持
                               └ 知识库 (moved)
```

The navbar now provides **clean, direct Center access** with no ambiguity. The dashboard's original compensating purpose — routing users through a cluttered tab bar — is obsolete.

### 1.3 Triple Duplication Problem

The dashboard IA audit (`docs/PHASE3C19_PROSPECTING_DASHBOARD_IA_AUDIT.md`) identified that Center entries appear in three places simultaneously:

```
NAVBAR                DASHBOARD SIDEBAR      DASHBOARD CENTER CARDS
─────────────────     ──────────────────     ──────────────────────
潜客运营 (tab)         运营看板 (active)       (not in cards)
搜索中心 (tab)         搜索中心 (link)         搜索中心 (card + entries)
触达中心 (tab)         触达中心 (link)         触达中心 (card + entries)
情报中心 (ref)          情报中心 (link)         情报中心 (card + entries)
商务/报价 (tab)        报价中心 (link)         报价中心 (card + entries)  ← stale
```

This creates three problems:
1. **Structural redundancy** — the same entry appears three times with zero differentiation
2. **Staleness** — the dashboard sidebar lists Quote under 潜客开发, but A3 moved it to 商务
3. **Identity confusion** — the page is named "潜客运营" (Prospecting Operations) implying a workspace, but its content is 80% navigation links

### 1.4 Guiding Principle

```
Navigation owns:   "Where to go"      — Center entry, module discovery, business location
Dashboard owns:    "Current work state" — operational summary, workflow visibility, queue overview
Command Center owns: "Full execution grid" — task processing, operational queues, deep work
```

---

## 2. Decision

**ProspectingDashboard evolves from a Center Launcher into an Operational Workspace.**

| Dimension | Current (Launcher) | Target (Workspace) |
|---|---|---|
| Primary content | Center entry cards + sidebar links | Live work-state cards: queue depths, pipeline status, KPIs |
| Navigation role | Replicates navbar entries | Links from queue cards to entity lists (not Center entries) |
| Sidebar | 5 Center links + workflow diagram | Removed — navbar handles routing |
| Summary data | 5 client-side counters | Server-side PrimaryFilter counts via Records views |
| Relationship to navbar | Duplicates it | Complements it — different surface, different purpose |

The dashboard is explicitly **not**:
- A navigation replacement
- A new business Center
- An entity list or CRUD surface
- A new data owner or workflow owner
- A Command Center replacement

The dashboard remains a **Class A Primary Center Entry** under the 潜客开发 divider. Its `tab:true`, `entity:false`, `object:false`, `acl:false` scope definition is unchanged.

---

## 3. Target Dashboard Design

### 3.1 Layout Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│ 潜客运营                                          [2026-07-27]   │
│ "今日销售开发概览"                                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ════════════ 今日工作概览 ════════════                          │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │ 待发送   │ │ 发送失败 │ │ 已回复   │ │ 待审批           │    │
│  │  READY   │ │  FAILED  │ │ 待处理   │ │  PENDING          │    │
│  │   → 12   │ │   → 3 ⚠  │ │   → 7    │ │  → 2             │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘    │
│                                                                  │
│  ════════════ 研究进度 ════════════                              │
│                                                                  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐   │
│  │ 待研究客户       │ │ 今日跟进         │ │ 研究失败返工   │   │
│  │ researchQueue    │ │ peFollowUpDue    │ │ peResearchFailed│   │
│  │ ProspectPool     │ │ Lead             │ │ Lead            │   │
│  │      → 24        │ │     → 5          │ │     → 2         │   │
│  └──────────────────┘ └──────────────────┘ └────────────────┘   │
│                                                                  │
│  ════════════ 触达状态 ════════════                              │
│                                                                  │
│  ┌──────────────────┐ ┌──────────────────────────────────────┐   │
│  │ 待触达           │ │ 待回复 (发送确认监听)                 │   │
│  │ c17Pending       │ │ c17AwaitingReply                     │   │
│  │ DraftApproval    │ │ ReplyEvent                           │   │
│  │      → 3         │ │     → 15                             │   │
│  └──────────────────┘ └──────────────────────────────────────┘   │
│                                                                  │
│  ════════════ 商务交接 ════════════                              │
│                                                                  │
│  ┌──────────────────┐ ┌──────────────────────────────────────┐   │
│  │ 待报价评审       │ │ 报价中心 (链接到 商务)               │   │
│  │ peProposalReview │ │ #Quote                                │   │
│  │ Required         │ │ "管理报价、审批和形式发票"            │   │
│  │ Lead             │ │                                      │   │
│  │      → 1         │ │                                      │   │
│  └──────────────────┘ └──────────────────────────────────────┘   │
│                                                                  │
│  ════════════ Pipeline ════════════                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ 潜客池 [247] → 研究中 [84] → 已研究 [63] → 已触达 [19] → ... ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Section A — Overview (今日工作概览)

**Purpose:** Immediate-action items. "What must I do this morning?"

| Card | Entity | Filter | Predicate | Priority |
|---|---|---|---|---|
| 待发送 | SendExecution | `c18ReadyToSend` | `status = READY` | P0 |
| 发送失败 | SendExecution | `c18FailedSend` | `status = FAILED` | P0 |
| 已回复待处理 | ReplyEvent | `c19OpenReplies` | `triageStatus = OPEN` | P0 |
| 待审批 | Approval | `c17Pending` | `status = PENDING` | P1 |

All cards use existing server-side PrimaryFilters. All are read-only Records views with count badges. Click navigates to the entity's filtered list — not to a Center entry.

### 3.3 Section B — Research Status (研究进度)

**Purpose:** Pipeline movement. Research backlog and follow-up state.

| Card | Entity | Filter | Predicate | Priority |
|---|---|---|---|---|
| 待研究客户 | ProspectPool | `researchQueue` | Research queue | P1 |
| 今日跟进 | Lead | `peFollowUpDue` | `nextFollowUpAt <= now` | P1 |
| 研究失败返工 | Lead | `peResearchFailed` | Research failure | P2 |
| 证据缺失 | Lead | `peMissingEvidence` | Evidence gaps | P2 |

All filters exist in `Classes/Select/Lead/PrimaryFilters/` and `Classes/Select/ProspectPool/PrimaryFilters/`.

### 3.4 Section C — Outreach Status (触达状态)

**Purpose:** Outreach pipeline visibility. What's in review, what's sent, what's pending reply.

| Card | Entity | Filter | Predicate | Priority |
|---|---|---|---|---|
| 待触达 | DraftApproval | `c17Pending` | `status = PENDING` | P1 |
| 已发送未回复 | ReplyEvent | `c17AwaitingReply` | `replyStatus = SENT` | P2 |

C19 WP3 re-titles the C17 await-reply queue from 待回复 to 已发送未回复 for disambiguation from the new 已回复待处理 triage queue.

### 3.5 Section D — Commercial Handoff (商务交接)

**Purpose:** Visibility into the commercial phase without owning it. Quote Center lives under the 商务 divider in navigation; the dashboard provides an at-a-glance handoff status.

| Card | Entity | Filter | Predicate | Priority |
|---|---|---|---|---|
| 待报价评审 | Lead | `peProposalReviewRequired` | Proposal review needed | P2 |
| 报价中心 | — | Link to `#Quote` | Navigation handoff | P3 |

The 报价中心 card is a **navigation handoff link only** — a single card pointing to the 商务 divider's Quote Center. It does not replicate Quote data, dashlets, or queues. It acknowledges the commercial phase exists and routes the user there. This is the only Center-navigation element retained, and it is explicitly labeled as a handoff, not as ownership.

**No Quote lifecycle changes. No Quote data on the dashboard. No Quote queue duplication.**

### 3.6 Section E — Pipeline Summary (Pipeline)

**Purpose:** Cross-stage funnel visibility from acquisition through commercial handoff.

A single composite row or card showing stage counts across the pipeline:

```
潜客池 → 研究中 → 已研究 → 已触达 → 报价中 → 成交
```

Each stage is a count from an existing server-side filter. The pipeline summary is read-only and non-mutating. It uses only existing entity data and PrimaryFilters — no new persistence, no metrics database, no analytics engine (C19 Charter §5).

---

## 4. Relationship With Command Center

### 4.1 Two Surfaces, Two Purposes

The ProspectingDashboard and the Command Center (`销售开发指挥中心`) are **complementary**, not competing:

| Dimension | ProspectingDashboard | Command Center |
|---|---|---|
| **Question answered** | "What needs attention?" | "How do we execute it?" |
| **Role** | Curated work-status landing | Full operational grid |
| **Audience** | All Prospecting roles | All Prospecting roles |
| **Content** | ~10 curated cards in 5 sections | 12+ dashlets in 3-band 4-column grid |
| **Layout** | Sectioned cards with count badges | Dashboard grid with full filter/sort controls |
| **Access** | First tab under 潜客开发 | Dashboard tab "销售开发指挥中心" |
| **Provisioning** | Code-shipped custom page | Provisioner-managed Preferences |
| **Depth** | Counts + click-through to lists | Full entity lists in dashlets |

### 4.2 Avoiding Duplicate Queue Ownership

Both surfaces may display the same queue (e.g., 待发送 appears on both), but with different depth:

- **Dashboard:** Count badge + title + click-through link to filtered entity list
- **Command Center:** Full Records dashlet with visible rows, sort controls, and filter toggles

This is acceptable duplication because the surfaces serve different use cases (glance vs. deep work) and share the same underlying PrimaryFilter — no data duplication, no filter duplication, no ownership conflict.

### 4.3 Governance Boundary

The Command Center provisioner (`phase3c17_provision_sales_development_command_center.php`) and the ProspectingDashboard custom page are independently governed:

- **Command Center:** Provisioner owns the managed-id set (`/^(phase3(?:u03|b07|c0[12]|c17|c18|c19)-)/`). Adding C19 queues to the Command Center is a WP3 provisioner change.
- **ProspectingDashboard:** The custom page owns its card composition. Adding workspace cards is a dashboard view/template change.

Neither surface governs the other. Neither can remove or override the other's content.

---

## 5. Existing Data Reuse

### 5.1 Zero New Entities

The workspace dashboard introduces **no new entities, scopes, or persistence**. All data comes from existing entities via existing PrimaryFilters.

### 5.2 Filter Inventory (verified existing)

All proposed cards use filters that already exist in the codebase:

| Filter class | Entity | Status |
|---|---|---|
| `C18ReadyToSend` | SendExecution | ✅ C18 WP2.2 |
| `C18FailedSend` | SendExecution | ✅ C18 WP2.2 |
| `C19OpenReplies` | ReplyEvent | ✅ C19 WP1 |
| `C17AwaitingReply` | ReplyEvent | ✅ C17 |
| `C17Pending` | DraftApproval | ✅ C17 |
| `C17Pending` | Approval | ✅ C17 |
| `researchQueue` | ProspectPool | ✅ C17 |
| `peFollowUpDue` | Lead | ✅ C17 |
| `peResearchFailed` | Lead | ✅ C17 |
| `peMissingEvidence` | Lead | ✅ C17 |
| `peProposalReviewRequired` | Lead | ✅ C17 |
| `prospectsReadyForResearch` | ProspectPool | ✅ C17 |

**Zero new PrimaryFilter classes are required for the workspace dashboard.**

### 5.3 Existing Services

| Service | Role | Dashboard Interaction |
|---|---|---|
| `ReplyTriageService` | Owns `triageStatus` | **None** — dashboard reads `triageStatus` via list API; never writes |
| `SendExecutionTransitionService` | Owns `SendExecution.status` | **None** — dashboard reads `status` via list API; never writes |
| `ApprovalService` | Owns Approval business state | **None** |
| `QuoteTransitionService` | Owns `Quote.status` | **None** |
| `EmailLifecycleProjectionService` | Lead projection | **None** |

The dashboard is a read-only composition surface. It invokes no transition services and performs no mutation.

### 5.4 Implementation Mechanism

Cards are implemented as **native EspoCRM Records views** (same pattern as Command Center queue dashlets) configured with:
- `entityType` — the entity scope
- `primaryFilter` — the existing server-side filter name
- `displayRecords` — small count (e.g., 5) for a compact card
- `sortBy` + `sortDirection` — appropriate ordering

No custom JS view per card. No custom filter logic. No client-side `where` clauses (C18 WP2 contract).

---

## 6. Non-Goals (Frozen)

The following are explicitly **NOT** in scope:

- **No new entities** — no BusinessCenter, WorkflowCenter, or any new scope
- **No new scopes** — all entities remain as defined in C17/C18
- **No new ACL model** — no `aclDefs` changes, no role permission changes
- **No Lead lifecycle changes** — Lead status, fields, and filters untouched
- **No Quote lifecycle changes** — Quote ownership, services, and transitions untouched
- **No Reply Center redesign** — `ReplyTriageService`, ADR-C19, triage model unchanged
- **No navigation redesign** — `navigation.json`, materializer, `config.tabList` governance unchanged
- **No Command Center replacement** — the Command Center dashboard tab is a separate surface, independently governed
- **No in-dashlet mutation** — no action buttons, inline edits, or status writes on any card
- **No funnel/rate/ROI analytics** — Pipeline Summary is stage counts only; no conversion rates, reply rates, or financial metrics (C19 Charter §5)
- **No new custom composition pages** — dashboard remains a single custom page, not a new Center
- **No navigation entry-point changes** — `ProspectingDashboard` stays as a tab under 潜客开发
- **No scope definition changes** — `tab:true`, `entity:false`, `acl:false` preserved

---

## 7. Implementation Boundary

### 7.1 In Scope (future implementation task)

| Artifact | Change |
|---|---|
| `views/prospecting/dashboard.js` | Replace launcher logic with workspace card composition |
| `templates/prospecting/dashboard.tpl` | New sectioned layout without sidebar or center cards |
| `i18n/*/ProspectingDashboard.json` | New labels for workspace sections and card titles; remove obsolete launcher labels |
| `clientDefs/ProspectingDashboard.json` | Likely unchanged (icon/color/controller binding preserved) |
| Contract tests | New assertions: workspace composition, filter bindings, read-only guarantees, no navigation duplication |

### 7.2 Explicitly NOT in Scope

| Artifact | Status |
|---|---|
| `navigation.json` | **Unchanged** — `ProspectingDashboard` entry preserved |
| Materializer | **Unchanged** |
| `config.tabList` | **Unchanged** — no navigation mutation |
| Scope metadata | **Unchanged** — `ProspectingDashboard.json`, entity scopes |
| Entity definitions | **Unchanged** |
| Services | **Unchanged** |
| ACL | **Unchanged** |
| Command Center provisioner | **Unchanged** — separate surface |
| PrimaryFilter classes | **Unchanged** — all filters already exist |
| C19 WP1/WP2/WP3 scope | **Unchanged** — workspace dashboard consumes WP outputs; does not drive them |

---

## 8. Acceptance Criteria

### 8.1 Structural

- [ ] No Center launcher cards in the dashboard (搜索中心, 情报中心, 触达中心, 报价中心 as primary content)
- [ ] No left sidebar replicating navbar Center links
- [ ] Workspace cards present in sections: Overview, Research Status, Outreach Status, Commercial Handoff
- [ ] Every card backed by an existing server-side PrimaryFilter (no client-side `where`)
- [ ] Pipeline Summary present as a cross-stage count row
- [ ] 报价中心 handoff card is a single navigation link — no Quote data on the dashboard

### 8.2 Governance

- [ ] Navigation remains the single source of Center entry
- [ ] Dashboard no longer acts as a navigation surface
- [ ] No `navigation.json` or materializer changes
- [ ] No scope definition changes
- [ ] Command Center unchanged (separate provisioner-managed surface)

### 8.3 Constraints

- [ ] No new entities, scopes, or persistence
- [ ] No new PrimaryFilter classes
- [ ] No ACL changes
- [ ] No service or lifecycle ownership changes
- [ ] No in-dashlet mutation strings or action buttons
- [ ] No conversion/funnel/ROI analytics
- [ ] All existing tests continue to pass

### 8.4 C19 Charter Boundary

- [ ] No C19 Charter §5 violations (no navigation mutation, no new entities, no ACL redesign, no in-dashlet mutation, no funnel analytics)
- [ ] C19 WP1/WP2/WP3 scope boundaries respected (dashboard consumes, does not drive)

---

## 9. Rollback

### 9.1 Primary Rollback

Restore the pre-evolution dashboard view and template from version control. No navigation, metadata, entity, or service state is affected by the dashboard's internal composition.

### 9.2 Impact if Not Applied

If this ADR is rejected:
- Dashboard continues as a Center launcher with triple navigation duplication
- Dashboard sidebar remains stale (Quote listed under 潜客开发)
- The "潜客运营" name remains in tension with launcher content
- Zero functional regression — the launcher works; it's just architecturally redundant

---

## 10. Decision Summary

| Question | Answer |
|---|---|
| Is ADR-C17 overturned? | No — evolution within PS-3 authority |
| Is ADR-C16 affected? | No |
| Is A3 affected? | No — navigation IA unchanged |
| Does the dashboard become a new Center? | No — it remains the Dashboard Center entry, now with workspace content |
| Are new entities introduced? | No |
| Are new filters created? | No — all filters already exist in the codebase |
| Is the Command Center replaced? | No — separate surface, separate purpose |
| Does this change navigation? | No |
| Does this change any service or lifecycle? | No |
| What is the substantive change? | Dashboard content: Center launcher cards → operational workspace cards; sidebar removed |
| Is rollback safe? | Yes — version control restore; zero data, navigation, or service impact |

---

## 11. Decision Record

| Date | Decision | Authority |
|---|---|---|
| 2026-07-27 | ProspectingDashboard IA Audit completed — triple duplication confirmed; launcher role obsolete | Phase3C19 Dashboard IA Audit |
| 2026-07-27 | **ADR Proposed** — ProspectingDashboard evolves from Center Launcher to Operational Workspace | Architecture design |
| 2026-07-27 | Governance validation gates 1–6 PASS | Phase3C19 Docs-Only Governance Review |
| 2026-07-27 | **ADR Accepted** — design authority only; no implementation authorized by this acceptance alone | Phase3C19 ProspectingDashboard Operational Workspace ADR Acceptance |

---

## 12. Acceptance Record

### 12.1 Governance Validation (2026-07-27)

| Gate | Name | Result | Evidence |
|---|---|---|---|
| 1 | **Navigation Boundary** | **PASS** | §1.4 navigation/dashboard separation principle; §2 explicitly "not a navigation replacement"; §6 "No navigation redesign." Navigation artifact `phase3c17_navigation.json` (marker `phase3c19-ia-v1`) confirms ProspectingDashboard under 潜客开发 remains the single Center entry. A3 topology (商务/支持 dividers, Quote moved) preserved. No `navigation.json` changes in working tree. Navigation remains the single source of business center entry. |
| 2 | **Dashboard Responsibility** | **PASS** | §1.4 defines Dashboard owns "Current work state — operational summary, workflow visibility, queue overview"; §2 target model: "Live work-state cards: queue depths, pipeline status, KPIs"; §2 table explicitly NOT: center launcher, duplicate navigation, entity management surface. §3 layout is entirely operational cards in 5 sections (Overview, Research, Outreach, Commercial Handoff, Pipeline). Quote handoff card (§3.5) is a single navigation link — no Quote data, no Center duplication. |
| 3 | **Command Center Boundary** | **PASS** | §4.1 "Two Surfaces, Two Purposes" table: Dashboard answers "What needs attention?"; Command Center answers "How do we execute it?". §4.2 accepts surface-level queue overlap with different depth (count badge vs. full Records dashlet) — same PrimaryFilter, no data duplication. §4.3 governance boundary: "Neither surface governs the other. Neither can remove or override the other's content." |
| 4 | **Data Ownership** | **PASS** | §5.1 "Zero new entities, scopes, or persistence." §5.2: 12 existing PrimaryFilters inventoried — all verified in `selectDefs/Lead.json`, `selectDefs/SendExecution.json`, `selectDefs/ReplyEvent.json`, `selectDefs/ProspectPool.json`, `selectDefs/DraftApproval.json`. §5.3: 5 existing services listed; dashboard is read-only — invokes no transition services. §5.4 implementation uses native Records views. Scope `ProspectingDashboard.json` confirmed: `entity:false, object:false, tab:true, acl:false` — unchanged. |
| 5 | **Business Lifecycle Protection** | **PASS** | §5.3: Dashboard "invokes no transition services and performs no mutation." §6 explicit: No Lead lifecycle changes, No Quote lifecycle changes, No Approval lifecycle changes, No ReplyEvent lifecycle changes, No SendExecution lifecycle changes. §7.2: Services, Entity definitions, ACL all "Unchanged." Working tree confirms zero service/hook/entityDef modifications. All lifecycle owners (`ReplyTriageService`, `SendExecutionTransitionService`, `ApprovalService`, `QuoteTransitionService`, `EmailLifecycleProjectionService`) retain sole-writer authority. |
| 6 | **C19 Scope Alignment** | **PASS** | ADR supports C19 goals: daily sales action center visibility (§3.2 cards surface C19 WP1 deliverables: `c19OpenReplies`), operational awareness (§3.3–3.6 research/outreach/pipeline status), workflow awareness without mutation (§5.3). §6 confirms no C19 Charter §5 violations: no new entities, no navigation modification, no ACL redesign, no lifecycle ownership mutation. §7.2 confirms C19 WP1/WP2/WP3 scope boundaries respected — "dashboard consumes WP outputs; does not drive them." |

### 12.2 Acceptance Decision

**ADR Accepted.** ProspectingDashboard evolves from a Center Launcher into an Operational Workspace as design authority.

Accepted means:

1. The workspace dashboard design in §3 is the authorized target composition.
2. Implementation (view, template, i18n, contract tests in §7.1) remains **not executed** until a separately authorized implementation task.
3. That implementation task must preserve: no navigation mutation, no new entities/scopes/services, no lifecycle ownership changes, no ACL changes, and all existing tests.
4. The dashboard's scope definition (`entity:false`, `object:false`, `tab:true`, `acl:false`) and navigation entry (under 潜客开发) are frozen — this ADR does not authorize changes to either.

### 12.3 Non-Implementation Confirmation

This acceptance task:

- Modified **zero** PHP files
- Modified **zero** metadata files (entityDefs, clientDefs, scopes, aclDefs, selectDefs)
- Modified **zero** navigation artifacts (`navigation.json`, materializer)
- Modified **zero** test files
- Modified **zero** service or hook files
- Created **zero** commits

Changes are limited to this ADR document (`docs/architecture/ADR_PROSPECTING_DASHBOARD_OPERATIONAL_WORKSPACE.md`): status update + acceptance record (§12).

---

*ADR accepted 2026-07-27. Status: Accepted. Design authority only — no runtime, artifact, metadata, code, or test changes authorized by this acceptance alone.*
