# Phase3C19 Charter — Sales Daily Command Center

**Status:** Accepted (WP0 governance closure)
**Date:** 2026-07-26
**Baseline:** `9bbd44a` / `phase3c18-freeze` (release line `1.9.11-alpha`)
**Tooling record:** Kimi Code K3 Max, DOCUMENTATION ONLY (WP0)

---

## 1. Mission

Evolve the C17/C18 **Sales Development Command Center** from a *monitoring dashboard*
into a *daily sales action center* that answers:

> **"我今天应该做什么？"**

C17 built the composition layer (read-only queues, center cards, provisioning).
C18 hardened the send lifecycle (transition ownership, operational queue filters).
C19 closes the last mile: **the signals that already exist become actionable daily
work queues with governed handling paths.**

---

## 2. Audit Findings That Motivate C19

Source: `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` (read-only audit, 2026-07-26).

| # | Finding | C19 response |
| --- | --- | --- |
| F1 | 发送失败 filter fully built but **pinned off the Command Center** by a C18 test contract | Admit to Command Center (WP3); amend C18 WP2.2 test contract with decision-log record |
| F2 | 待回复 queue filters `replyStatus = SENT` — actual customer replies (`REPLIED`) have **no queue anywhere**; ReplyEvent has no handled-state | ADR-C19: `triageStatus` work lifecycle + `c19OpenReplies` (WP1) |
| F3 | Five action-grade server filters exist on `Lead` (`peFollowUpDue`, `peAwaitingReply`, `peContactReady`, `peProposalReviewRequired`, `peResearchFailed`) but none are surfaced | Compose into daily queues (WP3) |
| F4 | No ownership scoping (`onlyMy` only on Task), no aging/SLA predicates, no queue-depth signals | Scoped follow-up (WP3 candidates; deferred where they need new semantics) |
| F5 | `FAILED` SendExecution has no authorized operator recovery path (retry/cancel edges exist but sales roles fail the edit-ACL gate) | ADR-C18-A6: recovery action boundary (WP2) |

---

## 3. Governance Baseline (WP0 deliverables — this package)

| Document | Content |
| --- | --- |
| `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` | `replyStatus` = immutable provider fact; `triageStatus` = work lifecycle; `ReplyTriageService` ownership; `PostSyncReplyEvent` ingress; `c19OpenReplies`; marker **`adr-c19-replyevent-v1`** |
| `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` | Retry/Cancel via **existing** transitions; **no RecoveryService**; sentAt remediation; cancel audit fields; **Ignore = CANCELLED + cancelReason**; marker **`adr-c18-sendexecution-v2`** |
| `docs/PHASE3C19_REPLY_CENTER_ARCHITECTURE.md` | Reply Center architecture implementing ADR-C19 |
| `docs/PHASE3C19_SEND_RECOVERY_ARCHITECTURE.md` | Send recovery architecture implementing ADR-C18-A6 (reconciled from the earlier draft audit) |
| `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` | Command Center audit + queue evolution design (WP3 input) |
| `docs/PHASE3C19_WP0_ADR_ACCEPTANCE_REPORT.md` | WP0 acceptance record and verification |

Marker stack after WP0:

| Marker | Owner phase | Scope |
| --- | --- | --- |
| `adr-c18-sendexecution-v1` | C18 | A1–A5 lifecycle invariants — unchanged |
| `adr-c18-sendexecution-v2` | C19 (A6) | Recovery entry-point boundary, sentAt remediation, cancel audit fields |
| `adr-c19-replyevent-v1` | C19 | ReplyEvent provider-fact / triage split |

---

## 4. Work Package Map

| WP | Scope | Depends on | Exit gate |
| --- | --- | --- | --- |
| **WP0** | Charter + ADR governance baseline (documentation only) | — | This package committed; docs-only diff verified |
| **WP1** | Reply Center: `triageStatus` + guard + `ReplyTriageService` + `PostSyncReplyEvent` ingress + `c19OpenReplies` + authorization bindings | WP0 | ADR-C19 §8 invariants pass |
| **WP2** | Send Recovery: workflow-action entry point, cancel audit fields, sentAt remediation, Ignore=Cancel UI action | WP0 | ADR-C18-A6 §8 invariants pass |
| **WP3** | Command Center composition: admit 发送失败, surface `c19OpenReplies` + Lead action filters, re-title 待回复, provisioner `c19` managed-ids | WP1 (queue), WP0 | Composition contracts pass; read-only guarantees intact |

WP ordering note: WP1 and WP2 are independent of each other; WP3 consumes WP1's
`c19OpenReplies` filter and the WP0 governance amendments.

---

## 5. Boundaries (carried from C17/C18, still frozen)

The Command Center remains **a dashboard composition layer**. C19 must NOT:

- Create new business scopes/entities (no BusinessCenter / SalesCenter / WorkflowCenter / ApprovalCenter / QuoteCenter / ReplyCenter **entities** — "Reply Center" is an architecture name, not a scope)
- Modify navigation (`tabList`, `navigation.json`, materializer)
- Redesign ACL (`aclDefs`, roles) — action bindings reuse `app.prospectingWorkflow` metadata policy
- Mutate lifecycle ownership: `SendExecutionTransitionService` (status), `ApprovalService`, `QuoteTransitionService`, `ApprovalDecisionService`, `EmailLifecycleProjectionService` (Lead projection)
- Add in-dashlet mutation, action buttons, or inline edits to any queue surface
- Add funnel/rate/ROI analytics to the Command Center
- Mutate C17/C18 frozen tags (`phase3c17-freeze`, `phase3c18-freeze`) or rebuild release artifacts in WP0

New lifecycle ownership introduced by C19 (WP1 only): **`ReplyTriageService`** owns
`triageStatus` — and nothing else.

---

## 6. Provisioning and i18n Continuity

- Provisioner managed-id regex extends to `c19` in WP3 (`/^(phase3(?:u03|b07|c0[12]|c17|c18|c19)-)/`); personal-dashboard preservation and Command-Center-first-tab rules unchanged.
- Queue titles remain zh-first in the provisioner; `en_US` parity is tracked as a known gap (audit §3.4) — resolution is a WP3 decision, not a WP0 blocker.
- New-user strategy unchanged: native default dashboard + provisioner rerun; no login hooks.

---

## 7. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-26 | C19 chartered on baseline `9bbd44a` / `phase3c18-freeze` |
| 2026-07-26 | ADR-C19 Accepted (marker `adr-c19-replyevent-v1`) |
| 2026-07-26 | ADR-C18 amendment A6 Accepted (marker `adr-c18-sendexecution-v2`); earlier Ignore-as-marker draft rejected |
| 2026-07-26 | WP0 closed — documentation only; WP1–WP3 authorized to start against this baseline |
