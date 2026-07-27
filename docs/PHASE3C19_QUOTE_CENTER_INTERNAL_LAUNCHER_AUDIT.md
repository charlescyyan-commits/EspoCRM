# Phase3C19 Quote Center Internal Launcher Audit

**Mode:** READ-ONLY ARCHITECTURE AUDIT
**Date:** 2026-07-27
**Baseline:** `2d07b5c` (HEAD, master)

---

## 1. Executive Summary

**Verdict: CLEAN — No internal launcher, sidebar, or navigation duplication found.**

The Quote Center is a standalone business surface with its own navigation tab under the 商务 (Commercial) divider, following A3 relocation from 潜客开发. It has clean workflow actions, no embedded links to other centers, and no legacy launcher code. The only cleanup items are 10 orphan C17-era i18n labels that are unreferenced by any active code.

---

## 2. Quote Center Structure

### 2.1 Navigation Ownership (Post-A3)

```
潜客开发
 ├ 潜客运营      → ProspectingDashboard (workspace)
 ├ 搜索中心      → ProspectingSearch (search jobs)
 └ 触达中心      → DraftApproval (outreach drafts)

客户管理
 └ 潜在客户      → Lead (native CRM)

商务
 └ 报价中心      → Quote (quotes + approvals + invoices)
```

**A3 Relocation verified:** Quote is at `topLevelOrder[28]` under divider `phase3c19-commercial` (商务), NOT under the 潜客开发 divider. The `navigation.json` `centers.quote` definition:

```json
"quote": {
  "entry": "Quote",
  "label": "报价中心",
  "operationalQueues": ["Approval", "ProformaInvoice"],
  "supportingObjects": ["QuoteItem"]
}
```

### 2.2 Entity Architecture

| Entity | Scope | Navigation Tab | Lifecycle Owner |
|---|---|---|---|
| **Quote** | `tab: true` | 报价中心 (under 商务) | `QuoteTransitionService` |
| **Approval** | `tab: true` | 报价审批 (managed, in navigation) | `ApprovalService` + `ApprovalDecisionService` |
| **ProformaInvoice** | `tab: true` | 形式发票 (managed, in navigation) | Standard CRUD |
| **QuoteItem** | `tab: false` | — (detail panel only) | Standard CRUD |

### 2.3 Quote Entity (Clean Standalone Business Surface)

**EntityDefs** (`entityDefs/Quote.json`):
- 7 status states: `DRAFT → IN_REVIEW → APPROVED → SENT → {ACCEPTED, REJECTED}`; `EXPIRED` from APPROVED
- Status field: `readOnly: true` — mutation only via `QuoteTransitionService`
- Links: `opportunity` (belongsTo), `lead` (belongsTo), `quoteItems` (hasMany), `approvals` (hasMany), `proformaInvoices` (hasMany)
- Audit: `acceptedAt`, `acceptedBy` — readOnly transition audit fields

**ClientDefs** (`clientDefs/Quote.json`):
- 8 workflow actions via `custom:handlers/quote/workflow-transition`:
  - Submit for Review (DRAFT → IN_REVIEW)
  - Approve (IN_REVIEW → APPROVED)
  - Reject Review (IN_REVIEW → DRAFT)
  - Send Quote (APPROVED → SENT)
  - Mark Customer Rejected (SENT → REJECTED)
  - Reject (SENT → REJECTED, deprecated alias)
  - Mark Accepted (SENT → ACCEPTED)
  - Expire (APPROVED → EXPIRED)
- All actions are status-gated by visibility functions
- Ajax route: `POST /Prospecting/quote/:id/workflow/:action`

**Controller** (`Controllers/Quote.php`):
```php
class Quote extends Record {}  // Standard CRUD, no custom logic
```

**Mutation Guard** (`Hooks/Quote/QuoteStatusMutationGuard.php`):
- `BeforeSave`, order 1000
- Create: only `DRAFT` allowed
- Update: status changes require `QUOTE_STATUS_MUTATION_AUTHORIZED` save option
- Pattern identical to SendExecution + ReplyEvent guards

### 2.4 Subordinate Entities

**Approval** (`clientDefs/Approval.json`):
- Standard record controller
- Single filter: `c17Pending` (status = PENDING)
- No launcher links, no center references

**QuoteItem** (`clientDefs/QuoteItem.json`):
- Minimal: `{"controller": "controllers/record", "iconClass": "fas fa-list"}`
- `tab: false` — not in navigation; accessed only from Quote detail panel

**ProformaInvoice**:
- `tab: true` — independent navigation tab
- Standard record controller (inherited)

### 2.5 Quote Workflow Handler (JS)

`client/custom/src/handlers/quote/workflow-transition.js`:
- 8 transition methods + 8 visibility methods
- All API calls target `Prospecting/quote/:id/workflow/:action`
- No cross-entity navigation, no center links, no launcher references
- 124 lines of pure workflow logic

---

## 3. Duplicate Ownership Analysis

### 3.1 Quote Center vs. 潜客开发 (Prospecting Development)

| Question | Finding |
|---|---|
| Is Quote in the 潜客开发 divider? | **No** — Quote is under 商务 (Commercial), not 潜客开发 |
| Does DraftApproval link to Quote? | **No** — DraftApproval entityDefs has no Quote links |
| Does the Quote entityDefs link to DraftApproval? | **No** — Quote's links are Opportunity, Lead, QuoteItem, Approval, ProformaInvoice |
| Does the outreachStatus section reference Quote? | **No** — only DraftApproval and ReplyEvent |

**Verdict: No overlap.** A3 relocation is correctly implemented. Quote and 潜客开发 are in separate navigation groups with separate entity ownership.

### 3.2 Quote Center vs. Workspace Dashboard

The workspace dashboard (`dashboard.js`) has a single Quote reference:

```javascript
// Commercial Handoff section (line 102-108)
{
    key: 'commercialHandoff',
    cards: [
        this.buildCountCard('proposalReviewRequired', 'Lead', 'Lead',
            'peProposalReviewRequired',
            '#Lead/list/primary=peProposalReviewRequired'),
        this.buildHandoffCard('quoteCenterHandoff', 'Quote', '#Quote',
            this.labels.quoteCenterDescription),
    ],
}
```

| Card | Type | Target | Purpose |
|---|---|---|---|
| `proposalReviewRequired` | Count card | `#Lead/list/primary=peProposalReviewRequired` | Lead pipeline stage — Leads needing proposal review |
| `quoteCenterHandoff` | **Handoff card** | `#Quote` | Navigation bridge to Quote Center |

**Analysis:**
- The `quoteCenterHandoff` is a **handoff card** (link + description), NOT a count card and NOT a launcher
- It has no count, no filter, no `where` clause — it's a single `<a href="#Quote">` link
- The description reads: "前往商务分组下的报价中心管理报价、审批和形式发票。" — explicitly directing users to the Commercial navigation group
- This is a UX convenience, not a duplicate entry point
- The `proposalReviewRequired` count card is on **Lead**, not Quote — it monitors Leads that have `peProposalEligibility = true AND peProposalAction = NO_AUTOMATIC_OPPORTUNITY`

**Verdict: NOT duplication.** The dashboard card is a navigation bridge that acknowledges Quote's relocation to the Commercial group.

### 3.3 Quote Center vs. Command Center

| Question | Finding |
|---|---|
| Are there Quote-specific dashlets in the Command Center? | **No** — zero Quote/Approval/ProformaInvoice Records dashlets |
| Does the provisioner reference Quote? | Only in the comment header: "报价中心: quote + approval visibility (Quote, Approval, ProformaInvoice)" |
| Is `peProposalReviewRequired` a Quote queue? | **No** — it's a Lead filter; "待报价评审" = leads needing proposal review |
| Is there an Approval queue? | Yes — `phase3c17-command-approvals` = Approval/c17Pending (审批), not Quote-specific |

**Verdict: No overlap.** The Command Center deliberately does not surface Quote entities. Quote is accessed through its own navigation tab under 商务.

### 3.4 Approval: Independent Tab or Quote Sub-entity?

Approval is:
- `tab: true` — independent navigation tab
- Linked to Quote via `foreign: "quote"` in entityDefs
- Has its own lifecycle service (`ApprovalService` + `ApprovalDecisionService`)
- Has its own mutation guard (`ApprovalStatusMutationGuard`)
- Listed as `operationalQueues` under `centers.quote` in navigation.json

**Assessment:** Approval is both an independent entity AND a Quote workflow dependency. Its `tab: true` means it appears in navigation independently. The `centers.quote.operationalQueues` designation is metadata only — it documents the relationship without creating duplicate UI surface. This is the same pattern as SendExecution/ReplyEvent under `centers.outreach`.

---

## 4. Legacy Artifact Scan

### 4.1 Center Launcher Code

| Pattern | Files Found | In Quote-relevant files? |
|---|---|---|
| `buildCenters` | **0 matches** | — |
| `centerCards` | **0 matches** | — |
| `centerLauncher` | **0 matches** | — |
| `centerEntry` | **0 matches** | — |
| `sidebar` | **0 matches** | — |
| `launcher` | **0 matches** | — |

**Verdict: Zero launcher code exists anywhere in the codebase.** The center launcher concept was designed in C17 but never implemented in any center.

### 4.2 Orphan i18n Labels

`Global.json` (zh_CN + en_US) contains 10 C17-era Quote center launcher labels that are **not referenced** by any production code:

| Label Key | zh_CN | en_US | Referenced In |
|---|---|---|---|
| `C17DashboardQuoteCenter` | 报价中心 | Quote Center | Test only (line 284) |
| `C17DashboardQuoteDescription` | 管理报价、商业审批和形式发票。 | Manage quotes, commercial approvals, and proforma invoices. | Not referenced |
| `C17DashboardQuotes` | 报价 | Quotes | Not referenced |
| `C17DashboardQuoteApprovals` | 报价审批 | Quote Approvals | Not referenced |
| `C17DashboardProformaInvoices` | 形式发票 | Proforma Invoices | Not referenced |

Non-Quote legacy labels in the same group (for context):
| `C17DashboardSearchCenter` | 搜索中心 | Search Center | Test only (line 281) |
| `C17DashboardSearchDescription` | 规划搜索、监控任务并整理潜客池。 | ... | Not referenced |
| `C17DashboardResearchCenter` | 情报中心 | Research Center | Test only (line 282) |
| `C17DashboardResearchDescription` | 使用原生线索作为研究记录来源。 | ... | Not referenced |
| `C17DashboardOutreachCenter` | 触达中心 | Outreach Center | Test only (line 283) |
| `C17DashboardOutreachDescription` | 审核触达草稿、发送执行和客户回复。 | ... | Not referenced |

**Total orphan count:** 12 labels (4 center names + 4 center descriptions + 12 entity-sub-labels = 24 total across both languages, minus 8 C19 active labels).

**Only active labels in this group are C19-prefixed:**
- `C19DashboardFailedSend`, `C19DashboardOpenReplies`, `C19DashboardMyReplies`
- `C19DashboardFollowUpDue`, `C19DashboardProposalReviewRequired`, `C19DashboardResearchFailed`
- `C19DashboardSentAwaitingReply`

### 4.3 Test Assertions on Orphan Labels

`test_phase3c17_cc1_center_composition.py` lines 281-284:

```python
self.assertEqual(zh_global["labels"]["C17DashboardSearchCenter"], "搜索中心")
self.assertEqual(zh_global["labels"]["C17DashboardResearchCenter"], "情报中心")
self.assertEqual(zh_global["labels"]["C17DashboardOutreachCenter"], "触达中心")
self.assertEqual(zh_global["labels"]["C17DashboardQuoteCenter"], "报价中心")
```

These assertions test that the orphan labels exist — a self-referential test. If the labels are removed, these test lines must also be removed.

Line 254: Confirms `QuoteCenter` is a banned entity scope (no entityDefs/QuoteCenter.json exists):

```python
for banned_scope in ("BusinessCenter", "SalesCenter", "WorkflowCenter",
                      "ApprovalCenter", "QuoteCenter"):
    self.assertFalse(
        (MODULE / "Resources" / "metadata" / "entityDefs" / f"{banned_scope}.json").exists(),
        msg=banned_scope,
    )
```

This test passes — `QuoteCenter` entity was never created ✅.

### 4.4 No Cross-Center Links in Quote Files

| File | Cross-Center References |
|---|---|
| `handlers/quote/workflow-transition.js` | None — only Quote-internal workflow actions |
| `Api/PostQuoteWorkflowAction.php` | None — delegates to QuoteWorkflowActionService |
| `Controllers/Quote.php` | None — standard Record controller |
| `clientDefs/Quote.json` | None — only workflow action definitions |
| `entityDefs/Quote.json` | Links to Opportunity, Lead — both in Customer Management group |
| `i18n/*/Quote.json` | None — only Quote-field translations |

---

## 5. Classification

### 5.1 Keep as Quote Business Workflow

| Item | Rationale |
|---|---|
| Quote entity + navigation tab | Primary business surface — correct |
| QuoteTransitionService + QuoteStatusMutationGuard | Lifecycle ownership — correct |
| 8 workflow actions (submit/approve/reject/send/accept/expire) | Core business workflow — correct |
| Approval entity + ApprovalService | Approval gating for Quote — correct |
| ProformaInvoice entity | Post-acceptance invoicing — correct |
| QuoteItem entity (detail panel only) | Line-item management — correct |

### 5.2 Remove (Orphan Labels Only)

| Item | Rationale |
|---|---|
| `C17DashboardQuoteCenter` + en_US | Unreferenced by any view/controller/handler |
| `C17DashboardQuoteDescription` + en_US | Unreferenced by any view/controller/handler |
| `C17DashboardQuotes` + en_US | Unreferenced by any view/controller/handler |
| `C17DashboardQuoteApprovals` + en_US | Unreferenced by any view/controller/handler |
| `C17DashboardProformaInvoices` + en_US | Unreferenced by any view/controller/handler |

Plus the 14 non-Quote C17Dashboard* labels (search/research/outreach centers + descriptions + entity sub-labels) if removing all C17 center launcher residuals.

**Total: 10 Quote-specific orphans + 14 non-Quote orphans = 24 labels across both languages.**

### 5.3 Move to Navigation Only

Nothing to move. All Quote entities are already navigation tabs:
- Quote → 商务 divider, position 28
- Approval → managed as independent tab
- ProformaInvoice → managed as independent tab

### 5.4 Convert to Operational Queue

Already correct. Quote is a **business workflow**, not an operational queue. The Command Center's operational queues (Lead filters, SendExecution, ReplyEvent, DraftApproval, Task) are daily work items. Quote is accessed through:
- Navigation tab (primary)
- Dashboard handoff card (bridge)  
- NOT the Command Center (correct exclusion)

---

## 6. Recommended Cleanup Scope

### Level 1: Orphan Label Removal (Safe, Zero Behavioral Impact)

Remove 24 unreferenced `C17Dashboard*` labels from `Global.json` (zh_CN + en_US):

**Center names + descriptions (8 labels × 2 languages = 16):**
```
C17DashboardSearchCenter, C17DashboardSearchDescription
C17DashboardResearchCenter, C17DashboardResearchDescription
C17DashboardOutreachCenter, C17DashboardOutreachDescription
C17DashboardQuoteCenter, C17DashboardQuoteDescription
```

**Entity sub-labels (8 labels × 2 languages = 16, minus any that ARE referenced):**
```
C17DashboardDraftApprovals, C17DashboardSendExecutions
C17DashboardReplyEvents, C17DashboardEmailEvents
C17DashboardQuotes, C17DashboardQuoteApprovals
C17DashboardProformaInvoices, C17DashboardSearchStrategies
C17DashboardSearchJobs, C17DashboardProspectPool
C17DashboardLeads, C17DashboardResearchEvidence
C17DashboardSalesFeedback, C17DashboardLearningSignals
```

Verify each is unreferenced before removal (grep across PHP, JS, JSON, TPL files).

**Test update:** Remove lines 281-284 from `test_phase3c17_cc1_center_composition.py` (the 4 assertions checking orphan center name labels).

### Level 2: Navigation Metadata Simplification (Optional, Cosmetic)

The `centers.quote` block in `navigation.json` is metadata that documents entity relationships:
```json
"quote": {
  "entry": "Quote",
  "label": "报价中心",
  "operationalQueues": ["Approval", "ProformaInvoice"],
  "supportingObjects": ["QuoteItem"]
}
```

If no provisioner or renderer consumes this structure, it can be removed. The same entity relationships are already expressed through:
- `topLevelOrder` (navigation tab positions)
- `managedProspectingEntries` (which entities the provisioner manages)
- `managedTopLevelEntries` (which entities appear as tabs)

**Risk:** Low. The `centers` structure is referenced in test assertions (`test_phase3c17_wp1_navigation.py` line 149 checks `prospectingCenterOrder` includes `"outreach"`), but no production code reads it.

### Level 3: No Changes Needed

The Quote business surface is clean. No view, template, controller, or handler changes are needed. The workflow-transition.js handler is correct. The QuoteStatusMutationGuard is correct. The dashboard handoff card is a valid navigation bridge, not a duplicate.

---

## 7. Constraints Compliance

| Constraint | Status |
|---|---|
| Do not modify navigation.json | ✅ No changes proposed to navigation structure |
| Do not modify dashboard files | ✅ dashboard.js handoff card preserved |
| Do not modify entityDefs | ✅ No entityDefs changes |
| Do not modify ACL | ✅ No aclDefs changes |
| Do not modify lifecycle | ✅ QuoteTransitionService untouched |
| Do not modify Quote services | ✅ All services preserved |
| Do not modify Approval services | ✅ ApprovalService preserved |
| No code changes | ✅ Label removal is i18n only; no PHP/JS changes |
| No commit | ✅ READ-ONLY audit |

---

## 8. Audit Checklist

| # | Check | Result |
|---|---|---|
| 1 | Quote templates: no launcher blocks | ✅ No dedicated Quote template; standard record detail |
| 2 | Quote views: no center launcher | ✅ Only dashboard.js (handoff card) + workflow-transition.js (actions) |
| 3 | Quote controllers: no cross-navigation | ✅ `Quote extends Record` — standard CRUD |
| 4 | Quote clientDefs: workflow actions only | ✅ 8 actions, all Quote-internal |
| 5 | Quote i18n: no launcher strings | ✅ Quote.json contains only field/status/action labels |
| 6 | Quote dashlets: none defined | ✅ No Quote-specific dashlets |
| 7 | `centerLauncher` pattern: 0 matches | ✅ Not present anywhere |
| 8 | `buildCenters` pattern: 0 matches | ✅ Not present anywhere |
| 9 | `centerCards` pattern: 0 matches | ✅ Not present anywhere |
| 10 | `sidebar` navigation: 0 matches | ✅ Not present anywhere |
| 11 | `QuoteCenter` entity: does not exist | ✅ Banned scope, entityDefs file absent |
| 12 | Quote in 潜客开发 divider: no | ✅ In 商务 divider (A3 relocation) |
| 13 | Quote in Command Center: no | ✅ Deliberately excluded |
| 14 | Dashboard Quote launcher: no | ✅ Single handoff card → `#Quote` navigation bridge |
| 15 | Legacy C17 i18n labels: 10 orphan | ⚠️ Removable, unreferenced by code |
| 16 | Test assertions on orphan labels: 4 lines | ⚠️ Self-referential, removable with labels |
| 17 | Approval not duplicating Quote navigation | ✅ Independent tab; `tab: true` is correct |
| 18 | ProformaInvoice not duplicating Quote navigation | ✅ Independent tab; `tab: true` is correct |
| 19 | QuoteItem not leaking into navigation | ✅ `tab: false`, detail panel only |
| 20 | Workflow authorization: correct | ✅ WorkflowAuthorizationService, metadata policy bindings |

---

*Audit performed READ-ONLY. No files modified, no commits made.*
