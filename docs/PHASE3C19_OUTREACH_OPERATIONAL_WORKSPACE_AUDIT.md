# Phase3C19 Outreach Operational Workspace Audit

**Mode:** READ-ONLY ARCHITECTURE AUDIT
**Date:** 2026-07-27
**Baseline:** `2d07b5c` (HEAD, master)
**Auditor:** Claude Code — 6-layer automated exploration

---

## Executive Summary

**Classification: B — Convert Outreach Center to Operational Workspace (Phased)**

The Outreach Center is currently a bare `DraftApproval` record list with zero action buttons, no custom views, and no visibility into its downstream entities (SendExecution, ReplyEvent). Six concrete gaps were identified. The Outreach Center should be converted to a domain-specific operational workspace — analogous to the Search Center workspace — that provides a morning-check surface with count cards and direct action entry points, without duplicating the Dashboard (cross-domain aggregation) or Command Center (deep execution grid).

---

## 1. Current Structure

### 1.1 Navigation Ownership

```
潜客开发 (divider: phase3c17-prospecting)
 ├ ProspectingDashboard  → 潜客运营 (Dashboard Workspace)
 ├ ProspectingSearch     → 搜索中心 (Search Center Workspace)
 └ DraftApproval         → 触达中心 (Outreach Center — LIST ONLY)
```

`DraftApproval` is the sole navigation tab for the Outreach Center. `SendExecution` and `ReplyEvent` are in `managedTopLevelEntries` — stripped from the navigation tab bar by the materializer despite having `tab: true` in their scope definitions. Users cannot see SendExecution or ReplyEvent tabs in the navbar.

### 1.2 Entity Chain

```
DraftApproval (触达中心 nav tab)
 ├── lead (belongsTo)
 ├── sendExecutions (hasMany) ─────────────────┐
                                               │
SendExecution (hidden from nav) ◄──────────────┘
 ├── draftApproval (belongsTo, required)
 ├── lead (belongsTo, required)
 ├── replyEvents (hasMany) ────────────────────┐
                                               │
ReplyEvent (hidden from nav) ◄─────────────────┘
 ├── sendExecution (belongsTo, required)
 ├── lead (belongsTo, required)
 └── (NO link to DraftApproval — indirect only)
```

### 1.3 Global Scope Names

| Entity | en_US scopeName | zh_CN scopeName | Tab Visible |
|---|---|---|---|
| DraftApproval | "Outreach Center" | "触达中心" | Yes |
| SendExecution | "Send Execution" | "发送执行" | No (managedTopLevelEntries) |
| ReplyEvent | "Customer Reply" | "客户回复" | No (managedTopLevelEntries) |

---

## 2. Surface Inventory

### 2.1 DraftApproval (触达中心 Entry Point)

| Aspect | Detail |
|---|---|
| Controller | `Controllers/DraftApproval.php` — extends Record, no custom actions |
| ClientDefs | Standard `controllers/record`, icon `fa-user-check` |
| Views | **None** — no custom JS views or templates exist |
| FilterList | Single filter: `c17Pending` (status=PENDING) |
| Detail Layout | 10-field, 7-row layout (name, status, draftId, lead, approvedBy, approvedAt, evidenceReference, scoreSnapshot, contentHash, decisionReason, assignedUser, teams) |
| List Layout | 6 columns: name, status, draftId, lead, approvedBy, approvedAt |
| Detail Actions | **None** — no `detailActionList` defined |
| Mass Actions | **None** — no `massActionList` defined |
| Status Field | `status`: PENDING/APPROVED/REJECTED — **not readOnly** in entityDefs, but no client UI to mutate |
| Relationship Panels | `sendExecutions` (hasMany → SendExecution) |

**Status: Bare record list with zero operational surface.**

### 2.2 SendExecution (Operational Queue, Hidden from Nav)

| Aspect | Detail |
|---|---|
| Controller | `Controllers/SendExecution.php` — extends Record |
| ClientDefs | Standard `controllers/record`, icon `fa-paper-plane` |
| Views | **None** — no custom JS views or templates |
| FilterList | 2 filters: `c18ReadyToSend` (status=READY), `c18FailedSend` (status=FAILED) |
| Detail Layout | 10-row layout with full SendExecution fields |
| List Layout | 7 columns: name, status, failureCategory, sendRequestId, lead, providerName, modifiedAt |
| Detail Actions | 3 workflow actions (FAILED status only): Retry, Cancel, Ignore — handler: `custom:handlers/send-execution/workflow-transition` |
| Mass Actions | **None** |
| Status Field | `status`: CREATED/READY/SENT/FAILED/CANCELLED — **readOnly** in entityDefs, mutated only via `SendExecutionTransitionService` |
| Relationship Panels | `replyEvents` (hasMany → ReplyEvent) |
| Required Links | `draftApproval` (belongsTo DraftApproval), `lead` (belongsTo Lead) |

**Status: Operationally complete (workflow actions exist) but invisible from nav.**

### 2.3 ReplyEvent (Reply Queue, Hidden from Nav)

| Aspect | Detail |
|---|---|
| Controller | `Controllers/ReplyEvent.php` — extends Record |
| ClientDefs | Standard `controllers/record`, icon `fa-reply` |
| Views | **None** — no custom JS views or templates |
| FilterList | 3 filters: `c17AwaitingReply` (replyStatus=SENT), `c19OpenReplies` (triageStatus=OPEN), `c19MyReplies` (triageStatus=IN_PROGRESS + assignedUserId=self) |
| Detail Layout | 6-row layout: name, replyStatus, externalEventId, receivedAt, sendExecution, lead, sendTraceReference, eventMetadata, assignedUser, teams |
| List Layout | 6 columns: name, replyStatus, externalEventId, lead, sendExecution, receivedAt |
| Detail Actions | **None** — no `detailActionList` defined |
| Mass Actions | **None** |
| Reply Triage | `ReplyTriageService` exists with full state machine (OPEN↔IN_PROGRESS→CLOSED) — **API-only**, no UI actions |
| Mutation Guard | `ReplyEventMutationGuard` enforces triage-only-write, provider-fact immutability |
| Required Links | `sendExecution` (belongsTo SendExecution), `lead` (belongsTo Lead) |
| DraftApproval Link | **None** — must navigate via SendExecution to reach DraftApproval |

**Status: Full backend service exists but zero UI actions. Triage is API-only.**

---

## 3. Dashboard and Command Center References

### 3.1 ProspectingDashboard Workspace

Outreach entities appear in two sections of the 4-section operational workspace:

**Overview Section:**
| Card | Entity | PrimaryFilter | Link |
|---|---|---|---|
| `pendingSend` | SendExecution | `c18ReadyToSend` | `#SendExecution/list/primary=c18ReadyToSend` |
| `failedSend` | SendExecution | `c18FailedSend` | `#SendExecution/list/primary=c18FailedSend` |
| `repliedPendingTriage` | ReplyEvent | `c19OpenReplies` | `#ReplyEvent/list/primary=c19OpenReplies` |
| `pendingApprovals` | Approval | `c17Pending` | `#Approval/list/primary=c17Pending` |

**Outreach Status Section:**
| Card | Entity | PrimaryFilter | Link |
|---|---|---|---|
| `pendingOutreach` | DraftApproval | `c17Pending` | `#DraftApproval/list/primary=c17Pending` |
| `sentAwaitingReply` | ReplyEvent | `c17AwaitingReply` | `#ReplyEvent/list/primary=c17AwaitingReply` |

### 3.2 Command Center (销售开发指挥中心)

7 outreach-related Records dashlets across 2 bands:

| Band | Dashlet ID | Entity | Filter | Grid (x,y) |
|---|---|---|---|---|
| ACTION | `phase3c19-command-failed-send` | SendExecution | `c18FailedSend` | (0,2) |
| ACTION | `phase3c19-command-open-replies` | ReplyEvent | `c19OpenReplies` | (1,2) |
| ACTION | `phase3c17-command-approvals` | Approval | `c17Pending` | (2,2) |
| MIDDLE | `phase3c17-command-outreach` | DraftApproval | `c17Pending` | (1,5) |
| MIDDLE | `phase3c18-command-pending-send` | SendExecution | `c18ReadyToSend` | (2,5) |
| MIDDLE | `phase3c17-command-replies` | ReplyEvent | `c17AwaitingReply` | (3,5) |
| MIDDLE | `phase3c19-command-my-replies` | ReplyEvent | `c19MyReplies` | (3,8) |

All are read-only `Records` dashlets with 10-record display, empty `boolFilterList`, server-side PrimaryFilter predicates, and `createdAt DESC` / `receivedAt DESC` sort.

### 3.3 Cross-Surface Coverage Matrix

| Queue | Dashboard | CC ACTION | CC MIDDLE | From 触达中心 Tab |
|---|---|---|---|---|
| Pending DraftApprovals (`c17Pending`) | outreachStatus (count) | — | Records dashlet | Yes — default filter |
| Pending Send (`c18ReadyToSend`) | overview (count) | — | Records dashlet | **No** — must drill through relationship panel |
| Failed Send (`c18FailedSend`) | overview (count) | Records dashlet | — | **No** — must drill through relationship panel |
| Sent Awaiting Reply (`c17AwaitingReply`) | outreachStatus (count) | — | Records dashlet | **No** — 2 hops away |
| Open Replies (`c19OpenReplies`) | overview (count) | Records dashlet | — | **No** — 2 hops away |
| My Replies (`c19MyReplies`) | — | — | Records dashlet | **No** — 2 hops away |

---

## 4. Launcher Pattern Detection

All 16 old-launcher patterns were searched across the entire codebase:

| # | Pattern | Source Matches | Status |
|---|---|---|---|
| 1 | `centerLauncher` | 0 | Clean |
| 2 | `buildCenters` | 0 | Clean |
| 3 | `centerCards` | 0 | Clean |
| 4 | `sidebar` | 0 | Clean |
| 5 | `operationalCenters` | 0 | Clean |
| 6 | `launcher` | 0 | Clean |
| 7 | `centerEntry` | 0 | Clean |
| 8 | `centerLead` | 0 | Clean |
| 9 | `centerDraftApproval` | 0 | Clean |
| 10 | `centerQuote` | 0 | Clean |
| 11 | `actionOpenSearch` | 0 | Clean |
| 12 | `outreachCenter` / `outreach_center` | 0 | Clean |
| 13 | `OutreachCenter` | 0 | Clean |
| 14 | `outreach` + `workspace` co-occurrence | 4 (legitimate C19) | Clean |
| 15 | `outreach` + `dashboard` co-occurrence | 6+ (legitimate C19) | Clean |
| 16 | `OutreachWorkspace` | 0 | Never existed |

**Verdict: The outreach domain has zero legacy launcher code.** The cleanup that was applied to the Search Center (removing sidebar, operationalCenters, centerLead, centerDraftApproval, centerQuote labels) was thorough.

---

## 5. User Workflow Analysis

### 5.1 What a User CAN Do from 触达中心 (DraftApproval Tab)

| Action | Accessible? | How |
|---|---|---|
| View pending DraftApprovals | **Yes** | Default `c17Pending` filter on list view |
| See DraftApproval details | **Yes** | Click record → detail view |
| Navigate to a SendExecution | **Yes (indirect)** | DraftApproval detail → sendExecutions relationship panel |
| Navigate to a ReplyEvent | **Yes (2 hops)** | DraftApproval detail → SendExecution detail → replyEvents relationship panel |
| Approve or reject a DraftApproval | **No** | Zero action buttons, no `detailActionList` |
| Retry/Cancel/Ignore a failed SendExecution | **Yes (indirect)** | Must first navigate to the SendExecution detail view, then use dropdown actions |
| Triage a ReplyEvent (assign/release/close) | **No** | ReplyTriageService is API-only, no UI actions |
| See pending SendExecutions at a glance | **No** | Must drill through relationship panel or navigate to Dashboard |
| See customer replies at a glance | **No** | Must navigate 2 hops or go to Dashboard |

### 5.2 Gap Analysis

| # | Gap | Severity | Detail |
|---|---|---|---|
| G1 | **DraftApproval has zero action buttons** | High | `status` is writable in entityDefs but no client UI exists. Users cannot approve or reject outreach drafts from the Outreach Center. |
| G2 | **SendExecution and ReplyEvent are hidden from nav** | High | Both have `tab: true` in scopes but are stripped by `managedTopLevelEntries`. Primary discovery path is the Dashboard — if a user navigates directly to 触达中心, they have no visible path to these entities. |
| G3 | **ReplyEvent triage is API-only** | High | `ReplyTriageService` is a complete state machine with assign/release/close, ACL authorization, and audit trail. Zero UI actions exist in clientDefs. The most critical outreach workflow (handling customer replies) requires API access. |
| G4 | **No end-to-end outreach thread view** | Medium | The chain DraftApproval → SendExecution → ReplyEvent requires 3-hop navigation. No single view shows the full outreach lifecycle for a given lead. |
| G5 | **Dashboard is the only aggregation surface** | Medium | If Dashboard ACL denies access to any outreach entity, that entity's card disappears entirely, removing the sole discovery path for hidden-tab entities. |
| G6 | **Approval entity confusion** | Low | `Approval` (Quote approval with four-eyes rule) shares name space with `DraftApproval` (outreach draft approval). Both use `c17Pending` filter. Approval is in `centers.quote.operationalQueues`, not outreach — but it appears in the Dashboard Overview section alongside outreach cards. |

---

## 6. Ownership Mapping

### 6.1 Three-Layer Responsibility Model

| Layer | Owner | Outreach Role | Current State |
|---|---|---|---|
| **Navigation** ("where to go") | `phase3c17_navigation.json` | DraftApproval tab under 潜客开发 | Correct — single entry point |
| **Dashboard** ("what needs attention") | `dashboard.js` workspace | 6 count cards across Overview + Outreach Status | Correct — read-only counts with list links |
| **Command Center** ("how to execute") | `phase3c17_provision_sales_development_command_center.php` | 7 Records dashlets across ACTION + MIDDLE bands | Correct — deep execution grid |

**Missing: A fourth layer — the Center Workspace ("where to do outreach work").**

### 6.2 Proposed Four-Layer Model

| Layer | Owner | Outreach Role |
|---|---|---|
| **Navigation** | `navigation.json` | DraftApproval tab → 触达中心 |
| **Outreach Workspace** *(new)* | Custom DraftApproval view | Domain-specific morning-check + action surface |
| **Dashboard** | `dashboard.js` | Cross-domain aggregation (counts only) |
| **Command Center** | Provisioner | Deep execution grid (full Records dashlets) |

---

## 7. Non-Duplication Boundaries

Any Outreach Workspace MUST respect these boundaries to avoid duplicating existing surfaces:

### 7.1 Must NOT Duplicate: Dashboard

| Dashboard Feature | Outreach Workspace Treatment |
|---|---|
| Cross-domain aggregation (Overview + Research + Outreach + Commercial in one view) | NOT duplicated — Outreach Workspace is outreach-domain only |
| Pipeline summary (5-stage funnel) | NOT duplicated — belongs to cross-domain Dashboard |
| Handoff cards (Quote Center) | NOT duplicated |
| Section grouping (overview, researchStatus, outreachStatus, commercialHandoff) | NOT duplicated — Outreach Workspace uses outreach-specific groupings |

### 7.2 Must NOT Duplicate: Command Center

| Command Center Feature | Outreach Workspace Treatment |
|---|---|
| Full Records dashlets with 10-record display | NOT duplicated — Outreach Workspace uses count cards only |
| 18-dashlet grid across 4 bands | NOT duplicated |
| User-scoped personal queues (my-replies, my-tasks) | NOT duplicated |
| Operational counter dashlets (LeadPool, RecentDiscovery, JobsCompleted) | NOT duplicated |

### 7.3 Must NOT Modify (Per Constraints)

| Protected Artifact | Constraint |
|---|---|
| `navigation.json` | No changes to tab structure or divider ownership |
| `dashboard.js` / `dashboard.tpl` | No changes to existing workspace cards or sections |
| `entityDefs` | No field or link changes |
| `ACL` | No scope permission changes |
| `Lifecycle` | No transition service or mutation guard changes |
| `Services` | No backend service changes |

---

## 8. Recommended Implementation Scope

### 8.1 Phase 1: Outreach Workspace View (Minimal)

Create a custom DraftApproval list-view replacement — an operational workspace that renders when the user clicks the 触达中心 tab.

**New files:**
- `client/custom/src/views/prospecting/outreach-workspace.js` — workspace view
- `client/custom/res/templates/prospecting/outreach-workspace.tpl` — Handlebars template
- `client/custom/src/controllers/prospecting-outreach.js` — controller (or modify DraftApproval clientDefs controller reference)

**Workspace sections:**

1. **Overview** (count cards, read-only):
   - `pendingApproval`: DraftApproval count → `c17Pending`
   - `pendingSend`: SendExecution count → `c18ReadyToSend`
   - `failedSend`: SendExecution count → `c18FailedSend`
   - `openReplies`: ReplyEvent count → `c19OpenReplies`

2. **Awaiting Reply** (count cards, read-only):
   - `sentAwaitingReply`: ReplyEvent count → `c17AwaitingReply`

**Non-duplication verification:**
- Dashboard has Overview (cross-domain: SendExecution + ReplyEvent + Approval + APPROVAL) → Outreach Workspace Overview is outreach-only (DraftApproval + SendExecution + ReplyEvent)
- Dashboard has outreachStatus (pendingOutreach + sentAwaitingReply) → Outreach Workspace moves sentAwaitingReply to Awaiting Reply section, keeps pendingOutreach in Overview
- Command Center has Records dashlets → Outreach Workspace has count cards only (no record rows)

### 8.2 Phase 2: Action Buttons (DraftApproval + ReplyEvent)

After the workspace view exists, add action buttons to DraftApproval and ReplyEvent detail views (within the entity's clientDefs `detailActionList`):

**DraftApproval actions:**
- `Approve` — transitions status PENDING → APPROVED
- `Reject` — transitions status PENDING → REJECTED
- Handler: new `custom:handlers/draft-approval/workflow-transition` or reuse existing pattern

**ReplyEvent actions:**
- `Assign to Me` — transitions triageStatus OPEN → IN_PROGRESS, sets assignedUser
- `Release` — transitions triageStatus IN_PROGRESS → OPEN, clears assignedUser
- `Close Reply` — transitions triageStatus OPEN/IN_PROGRESS → CLOSED, prompts for closedReason
- Handler: new `custom:handlers/reply-event/triage-transition` calling `ReplyTriageService` via API

### 8.3 Scope of Changes (No Protected Artifacts Modified)

| Change | Touches | Protected? |
|---|---|---|
| New `outreach-workspace.js` view | `client/custom/src/views/prospecting/` | No |
| New `outreach-workspace.tpl` template | `client/custom/res/templates/prospecting/` | No |
| New controller or clientDefs redirect | `clientDefs/DraftApproval.json` or new controller | No (metadata only) |
| DraftApproval detailActionList | `clientDefs/DraftApproval.json` | No (metadata only) |
| ReplyEvent detailActionList | `clientDefs/ReplyEvent.json` | No (metadata only) |
| New workflow handlers | `client/custom/src/handlers/` | No (new files) |
| i18n labels (new workspace labels) | `ProspectingDashboard.json` or new domain | No (new keys only) |

**Zero protected artifacts are modified.** The implementation is purely additive: new client views/templates/handlers + metadata clientDefs extensions.

---

## 9. Final IA Tree (With Outreach Workspace)

```
导航栏:
  潜客开发
   ├ 潜客运营      → ProspectingDashboard (cross-domain aggregation)
   ├ 搜索中心      → ProspectingSearch (search workspace: create + counts)
   └ 触达中心      → DraftApproval → Outreach Workspace (outreach workspace: counts + actions)

仪表板:
  Overview (4 cards)        — cross-domain: Send + Reply + Approval
  Research Status (4 cards)  — ProspectPool + Lead
  Outreach Status (2 cards)  — DraftApproval + ReplyEvent
  Commercial Handoff (2 cards) — Lead + Quote

指挥中心:
  ACTION (4 dashlets)        — exception queues: failed-send, open-replies, approvals, followup
  MIDDLE (8 dashlets)        — personal + pipeline: outreach, pending-send, replies, my-replies, ...

触达工作区 (NEW):
  Overview (4 cards)         — outreach-only: pendingApproval, pendingSend, failedSend, openReplies
  Awaiting Reply (1 card)    — sentAwaitingReply
  Draft Actions              — Approve/Reject buttons on DraftApproval records
  Reply Triage Actions       — Assign/Release/Close buttons on ReplyEvent records
```

---

## 10. Risk Assessment

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| R1 | Outreach Workspace count cards duplicate Dashboard cards | Low | Dashboard is cross-domain; Outreach Workspace is domain-specific. Different grouping, different audience. |
| R2 | DraftApproval approve/reject actions may conflict with EmailLifecycleProjectionHook | Low | Hook runs on every save — adding UI actions doesn't change the hook's behavior. Status mutations already flow correctly. |
| R3 | ReplyEvent triage UI actions may bypass ReplyEventMutationGuard | Low | UI handlers call existing API (ReplyTriageService), which already uses `REPLY_TRIAGE_MUTATION_AUTHORIZED` save option. Mutation guard is preserved. |
| R4 | Users may be confused by having both 触达中心 tab and Dashboard outreach section | Low | Clear labeling: 触达中心 = "do outreach work", 潜客运营 = "see everything at a glance" |
| R5 | Approval entity (Quote domain) appears in Dashboard Overview but not in Outreach Workspace | Low | Correct — Approval is in `centers.quote`, not `centers.outreach`. Dashboard intentionally cross-domain. |

---

## 11. Recommendation

### Classification: B — Convert Outreach Center to Operational Workspace

**Rationale:**

The current Outreach Center (DraftApproval tab) is a bare record list that fails to serve as a functional workspace. Six concrete gaps exist, the most severe being:
- No action buttons for draft approval (G1)
- No action buttons for reply triage (G3)
- Hidden SendExecution/ReplyEvent tabs (G2)

The Search Center already follows the workspace pattern (custom view + template + controller). The Outreach Center should follow the same pattern, providing a domain-specific morning-check surface with count cards and action entry points.

**Key design constraint:** The Outreach Workspace must complement — not duplicate — the Dashboard (cross-domain aggregation) and Command Center (deep execution grid). It occupies the fourth layer: the domain action surface.

**Implementation is purely additive** — zero protected artifacts (navigation, dashboard, entityDefs, ACL, lifecycle, services) are modified.

**Phased approach:**
1. Phase 1 (C20 WP1): Custom outreach workspace view with count cards — replaces bare DraftApproval list
2. Phase 2 (C20 WP2): DraftApproval approve/reject and ReplyEvent triage action buttons — closes G1 and G3
3. Future: End-to-end outreach thread view per lead — closes G4

---

## 12. Audit Methodology

| Layer | Method | Files Examined |
|---|---|---|
| DraftApproval surface | Full file reads: entityDefs, clientDefs, scope, i18n (×2), layouts, controller, hooks | 12 |
| SendExecution surface | Full file reads: entityDefs, clientDefs, scope, i18n (×2), layouts, handler, selectDefs, PrimaryFilters, 5× services | 16 |
| ReplyEvent surface | Full file reads: entityDefs, clientDefs, scope, i18n (×2), layouts, selectDefs, PrimaryFilters, ingestion API, triage service, sync service, mutation guard, projection hook | 18 |
| Dashboard + CC references | Full file reads: dashboard.js (260 lines), dashboard.tpl (82 lines), ProspectingDashboard.json (×2), provisioner | 5 |
| Launcher pattern detection | 16 patterns searched across entire codebase | 100+ |
| User workflow analysis | Relationship chain traversal, action audit, navigation visibility check, gap enumeration | 20+ |

**Total files read:** 70+
**Codebase search patterns:** 16
**Independent agents:** 6

---

*Audit completed 2026-07-27. No files were modified during this read-only audit.*
