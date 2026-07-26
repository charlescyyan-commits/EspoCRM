# Phase3C19 — Command Center Design (Audit + Queue Evolution)

**Status:** Accepted design (WP3 implementation input; audit findings verified read-only)
**Date:** 2026-07-26
**Baseline:** `9bbd44a` / `phase3c18-freeze`
**Governance inputs:** ADR-C19 (`adr-c19-replyevent-v1`), ADR-C18-A6 (`adr-c18-sendexecution-v2`), C19 Charter

> This document serves two roles: (1) the read-only audit of the C17/C18 Command
> Center, (2) the WP3 queue-evolution design, **reconciled at WP0** with the accepted
> ADRs. Where the raw audit floated options, this version records the WP0 decisions.

---

## 1. Current Dashlets (audited as-built)

Source of truth: `deployment/provisioning/phase3c17_provision_sales_development_command_center.php`
(per-user `Preferences.dashboardLayout` + `dashletsOptions`; managed-id pattern
`/^(phase3(?:u03|b07|c0[12]|c17|c18)-)/`). Runtime confirmed by C18 evidence
(`p3c18-evidence/05-command-center-dashlet.jpg`).

### TOP band — operational summaries (2)

| ID | Dashlet | View | Source |
|---|---|---|---|
| `phase3c17-command-summary` | ProspectingSummary (潜客概览) | `custom:views/dashlets/prospecting-summary` | ProspectPool / SearchJob counts (5 metric cards with click-through hrefs) |
| `phase3c17-command-overview` | AcquisitionOverview (获客概览) | native `record-list` | SearchStrategy |

### MIDDLE band — daily queues (6)

| ID | Title | Entity | PrimaryFilter | Sort | Notes |
|---|---|---|---|---|---|
| `phase3c17-command-my-tasks` | 我的任务 | Task | `actual` | dateStart asc | bool `onlyMy` — the **only** user-scoped queue |
| `phase3c17-command-research` | 待研究客户 | ProspectPool | `researchQueue` | — | AcquisitionResearchQueue dashlet |
| `phase3c17-command-outreach` | 待触达 | DraftApproval | `c17Pending` (status=PENDING) | createdAt desc | native Records |
| `phase3c18-command-pending-send` | 待发送 | SendExecution | `c18ReadyToSend` (status=READY) | createdAt desc | C18 WP2.2 addition |
| `phase3c17-command-replies` | 待回复 | ReplyEvent | `c17AwaitingReply` (replyStatus=**SENT**) | receivedAt desc | semantic issue — §2.4 |
| `phase3c17-command-approvals` | 待审批 | Approval | `c17Pending` (status=PENDING) | createdAt desc | approver field unused for scoping |

### BOTTOM band — operational counters/activity (4)

| ID | Dashlet | Entity |
|---|---|---|
| `phase3c17-command-pool` | AcquisitionLeadPool (客户池) | ProspectPool |
| `phase3c17-command-recent-discovery` | ProspectingRecentDiscovery (新增客户) | SearchJob |
| `phase3c17-command-completed` | AcquisitionJobsCompleted (研究完成（任务）) | SearchJob |
| `phase3c17-command-evidence` | RecentResearchEvidence (研究完成（证据）) | ResearchEvidence |

**Verified properties:** all queue dashlets native `Records`/`record-list`; every
extension dashlet declares `aclScope`; no `save()`/status mutation on composition
surfaces (contract-pinned); forbidden analytics (conversion/reply-rate/funnel/ROI)
absent; personal dashboards preserved (carried-item y-offset `max(14, y+14)`).

### Four center entry cards (separate surface)

`crm-extension/files/client/custom/src/views/prospecting/dashboard.js` renders
搜索中心 / 情报中心 / 触达中心 / 报价中心 with ACL-checked entries. C18 added
待发送 / 发送失败 links to 触达中心 — currently the **only** place Failed Send is reachable.

---

## 2. Existing Queues (audit verdicts)

### 2.1 Pending Send (待发送) — ✅ healthy

Records dashlet → `SendExecution` → `c18ReadyToSend` → `status = READY` → ACL-filtered
select. Server-side, single-predicate, non-mutating; conforms to `adr-c18-sendexecution-v1`.

### 2.2 Failed Send (发送失败) — ⚠️ built but hidden (WP0 decision: admit)

- Filter fully exists: `C18FailedSend` (`status = FAILED`), selectDefs mapping, name-only clientDefs, i18n (`C18DashboardFailedSend`).
- **Excluded from the Command Center by a C18 test contract** (`test_phase3c18_wp2_sendexecution_queue_surface.py` pins `assertNotIn("c18FailedSend", provisioner)` — "Outreach Center only").
- **WP0 decision (Charter §2 F1):** admit to the Command Center in WP3. Failed sends are the highest-urgency morning triage item; `SendExecution` already carries triage context (`failureCategory`, `lastError`, `retryCount`, `nextRetryAt`); read-only surfacing does not violate lifecycle ownership; recovery actions route through ADR-C18-A6 entry points. The C18 test contract is amended in WP3 with a decision-log record in `docs/PHASE3C18_WP2_CC2_OPERATIONAL_QUEUE_DESIGN.md` §9.

### 2.3 Draft Approval (待触达) — ✅ functional, two caveats

- `DraftApproval.c17Pending` → `status = PENDING`; read-only; decision in detail view.
- Caveat A — title/semantics: queue lists *draft approvals pending review*, titled 待触达. WP3 re-title candidate: 待审核触达.
- Caveat B — no ownership scoping: `assignedUser` exists but queue is team-wide (unlike 我的任务 `onlyMy`).

### 2.4 Reply Event (待回复) — ❌ semantic mismatch (resolved by ADR-C19)

- `C17AwaitingReply` applies `replyStatus = SENT` — **send-confirmation events**, not customer replies. Actual `REPLIED` events had no queue anywhere, and ReplyEvent had no handled-state.
- **WP0 resolution (ADR-C19):** additive `triageStatus` work lifecycle (`ReplyTriageService`-owned) + `c19OpenReplies` (`triageStatus = OPEN`). The C17 filter is kept as a monitoring queue; WP3 re-titles it 已发送未回复 and adds 已回复待处理 backed by `c19OpenReplies`.

### Queue wiring summary

| Queue | Entity | Predicate | Server-side | ACL | User-scoped | On Command Center |
|---|---|---|---|---|---|---|
| 待发送 | SendExecution | status=READY | ✅ | ✅ | ❌ | ✅ |
| 发送失败 | SendExecution | status=FAILED | ✅ | ✅ | ❌ | ❌ → **WP3 admit** |
| 待触达 | DraftApproval | status=PENDING | ✅ | ✅ | ❌ | ✅ |
| 待回复 (SENT monitoring) | ReplyEvent | replyStatus=SENT | ✅ | ✅ | ❌ | ✅ (re-title WP3) |
| 已回复待处理 (work) | ReplyEvent | triageStatus=OPEN | WP1 builds `c19OpenReplies` | ✅ | ❌ | ❌ → **WP3 add** |

---

## 3. Missing Sales Actions (audit inventory)

| # | Daily sales action | Backing asset | WP0 disposition |
|---|---|---|---|
| 1 | 发送失败 triage | `c18FailedSend` + A6 recovery entry points | **WP3 admit** + WP2 actions |
| 2 | 已回复处理 | ADR-C19 `triageStatus` + `c19OpenReplies` | **WP1 build, WP3 surface** (raw audit's Lead `peAwaitingReply` fallback not needed — event-level handled-state now exists) |
| 3 | 今日跟进 | Lead `peFollowUpDue` (`nextFollowUpAt <= now`) — exists | **WP3 surface** |
| 4 | 联系就绪未触达 | Lead `peContactReady` (+ `peContactReadyWithoutContactMethod`) — exists | WP3 candidate |
| 5 | 可报价 / 待报价评审 | Lead `peProposalEligible` / `peProposalReviewRequired` / `peProposalActionMissing` — exist | **WP3 surface** (`peProposalReviewRequired`) |
| 6 | 研究失败返工 | Lead `peResearchFailed` — exists | **WP3 surface** |
| 7 | 我的审批 (approver = me) | `Approval.approver` link | Deferred — primary filters lack user context; needs bool-filter design (WP3+ decision) |
| 8 | 队列深度 / aging (e.g. PENDING > 48h) | none | Deferred — single-predicate rule requires separate aging filters; WP3+ decision |
| 9 | 销售反馈闭环 | SalesFeedback `needsFollowUp` filter + RecentSalesFeedback dashlet (in metadata, not on grid) | WP3 candidate |

Non-signals (correctly absent, still forbidden): conversion rate, reply rate, funnel, ROI.

### Minor observations

- **Client-side `where` in counters:** `prospecting-summary.js` / `prospecting/dashboard.js` compute counts with client-only `where` (`lastXDays createdAt 7`, `researchStatus=COMPLETED`, `priority=P1`). C18 WP2 forbade client-only `where` for *queue filters*; counters were out of scope. WP3 should prefer existing server filters (`peResearchCompleted`, `peHighPriority`) for any new counting.
- **Hardcoded queue titles:** provisioner titles are Chinese literals — zh-first accepted; `en_US` users see Chinese titles. Known gap; WP3 decision.
- **New-user strategy** unchanged: rerun provisioner / native default dashboard; no login hooks.

---

## 4. Recommended Daily Workflow (WP3 target)

**Morning — clear exceptions first (触达 block)**

1. **发送失败** → triage by `failureCategory` (AUTH/PROVIDER escalate; RATE_LIMIT/NETWORK wait `nextRetryAt`; VALIDATION fix draft) → act via A6 entry points (Retry/Ignore/Cancel from detail view).
2. **已回复待处理** (`c19OpenReplies`) → work replies top-down (resolve / follow-up task / advance lead).
3. **已发送未回复** (re-titled C17 queue) → scan stale threads → follow-up tasks.
4. **待审批** (manager/approver) → clear PENDING approvals.

**Midday — move the pipeline (潜客 block)**

5. **我的任务** → due/overdue tasks. 6. **今日跟进** (`peFollowUpDue`).
7. **待触达** → review pending drafts → tomorrow's sends. 8. **待研究客户** → drain research queue.

**Wrap-up — commercial progression (报价 block)**

9. **待报价评审** (`peProposalReviewRequired`). 10. Bottom-band counters sanity check.

### WP3 grid evolution (composition-only, current 4-column grid)

```
TOP:    [潜客概览]        [获客概览]                                  (unchanged)
ACTION: [发送失败]        [已回复待处理]  [待审批]      [今日跟进]      (new band)
MIDDLE: [我的任务]        [待触达]       [待发送]      [已发送未回复*]  (*re-title)
        [待研究客户]      [待报价评审]   [研究失败]     —
BOTTOM: [客户池]          [新增客户]     [研究完成(任务)] [研究完成(证据)] (unchanged)
```

Everything stays read-only; "action" means jump-off to the owning surface (WP1/WP2
detail-view actions), never in-dashlet mutation.

---

## 5. Required Metadata / Provisioning Changes (WP3)

All composition + metadata. **No** new scopes/entities, **no** ACL/aclDefs redesign,
**no** navigation changes, **no** workflow-service changes (WP1/WP2 own their own gates).

### 5.1 Governance amendment (prerequisite, WP3)

- Amend `test_phase3c18_wp2_sendexecution_queue_surface.py`: remove the two `assertNotIn` lines pinning Failed Send off the Command Center; replace with positive assertions; record the reversal in `docs/PHASE3C18_WP2_CC2_OPERATIONAL_QUEUE_DESIGN.md` §9 (rationale: action-center objective; queue read-only; recovery via A6 entry points).

### 5.2 Provisioner (`phase3c17_provision_sales_development_command_center.php`)

- Extend managed-id regex: `/^(phase3(?:u03|b07|c0[12]|c17|c18|c19)-)/`.
- New dashlet items + options (native `Records`, `displayRecords` 10):

| New ID | Title (zh) | Entity | PrimaryFilter | Sort |
|---|---|---|---|---|
| `phase3c19-command-failed-send` | 发送失败 | SendExecution | `c18FailedSend` | createdAt desc |
| `phase3c19-command-open-replies` | 已回复待处理 | ReplyEvent | `c19OpenReplies` (WP1) | receivedAt desc |
| `phase3c19-command-followup` | 今日跟进 | Lead | `peFollowUpDue` | nextFollowUpAt asc |
| `phase3c19-command-proposal-review` | 待报价评审 | Lead | `peProposalReviewRequired` | modifiedAt desc |
| `phase3c19-command-research-failed` | 研究失败 | Lead | `peResearchFailed` | modifiedAt desc |

- Re-title `phase3c17-command-replies` option: 待回复 → 已发送未回复 (filter unchanged).
- Re-grid per §4; keep carried-personal-item offset and Command-Center-first-tab rules intact.

### 5.3 Filter dependencies

- `c19OpenReplies` arrives from **WP1** (ADR-C19). All other WP3 queues reuse **existing** filters — zero new filter classes in WP3.
- Aging variants (PENDING > 48h) and approver-scoped 我的审批 remain deferred (§3 rows 7–8) — separate decision, not a WP3 blocker.

### 5.4 Metadata touch points

- i18n `Global.json` (zh/en): `C19Dashboard*` labels; key parity.
- `clientDefs` name-only `filterList` for any filter newly exposed in list views (no client `where`).
- Optional (WP3 decision): language-aware provisioner titles.

### 5.5 Tests (WP3)

- Amend C18 WP2.2 test (5.1). Extend `test_phase3c17_cc1_center_composition.py`: new IDs, entity/filter bindings, `c19` regex, i18n parity.
- Regression: personal-dashboard preservation, no duplicate tabs, no workflow-mutation strings.

### 5.6 Out of scope for WP3

- In-dashlet action buttons (WP1/WP2 surface actions in detail views only).
- Quote/Approval lifecycle, navigation, release artifacts, funnel analytics.
- New-user auto-provisioning (rerun strategy retained).

---

## Appendix — Key Evidence Paths

| Artifact | Path |
|---|---|
| Command Center provisioner | `deployment/provisioning/phase3c17_provision_sales_development_command_center.php` |
| Queue filter classes | `crm-extension/files/custom/Espo/Modules/Prospecting/Classes/Select/{SendExecution,ReplyEvent,DraftApproval,Approval,Lead}/PrimaryFilters/` |
| selectDefs | `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/selectDefs/*.json` |
| Center entry cards | `crm-extension/files/client/custom/src/views/prospecting/dashboard.js` |
| Contracts/tests | `crm-extension/tests/test_phase3c17_cc1_center_composition.py`, `test_phase3c18_wp2_sendexecution_queue_surface.py` |
| Governance | `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md`, `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md`, `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md`, `docs/PHASE3C18_WP2_CC2_OPERATIONAL_QUEUE_DESIGN.md` |
| Runtime evidence | `p3c18-evidence/01–06` (audit workspace) |

*WP0 documentation only. No PHP, metadata, tests, navigation, ACL configuration, or release artifacts are modified by this document.*
