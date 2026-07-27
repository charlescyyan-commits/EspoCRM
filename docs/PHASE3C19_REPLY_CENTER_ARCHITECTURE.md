# Phase3C19 Reply Center Architecture

**Status:** Accepted design (WP1 implemented; reconciled 2026-07-27)
**Date:** 2026-07-26 (original); 2026-07-27 (reconciled to WP1 implementation)
**Implements:** `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` — governance marker **`adr-c19-replyevent-v1`** (amended)
**Baseline:** `master @ 74f0f1eb` (Phase3C19 WP1.5 reconciliation)

> "Reply Center" is an **architecture name** for the reply-handling pipeline.
> It is **not** a new scope, entity, or navigation center (C19 Charter §5).

> **Reconciliation note (2026-07-27):** This document has been updated to match the
> WP1 implementation. The original WP0 design specified `RESOLVED`/`IGNORED` with
> `reopen` and `triagedAt`/`triagedBy`/`triageReason` audit fields. WP1 implemented
> `IN_PROGRESS`/`CLOSED` with explicit `assignedUser` ownership, `close` (terminal),
> `closedReason`/`closedAt`/`closedBy` audit fields, and a second queue `c19MyReplies`.
> See `docs/PHASE3C19_WP1_LIFECYCLE_RECONCILIATION_REPORT.md` for the full review.
> The ADR has been amended accordingly.

---

## 1. Objective

Give sales operators a governed daily workflow for provider reply events:

```
provider webhook / sync
        │
        ▼
PostSyncReplyEvent (ingress) ── creates ReplyEvent ── replyStatus = provider fact (immutable)
        │                                              triageStatus = OPEN (actionable) or null
        │                                              assignedUserId = lead.assignedUserId (seed)
        ▼
c19OpenReplies queue (server-side PrimaryFilter, read-only surface)
        │
        ▼  operator claims (assign) — takes ownership
c19MyReplies queue (operator-scoped: IN_PROGRESS + assigned)
        │
        ▼  operator acts from the ReplyEvent detail view (never the queue)
ReplyTriageService ── sole writer of triageStatus + ownership + close audit fields
        │
        ▼
CLOSED (terminal — close reason required; audit fields written)
```

The Lead projection path (`EmailLifecycleProjectionService` → `Lead.peEmailReplyStatus`)
is **untouched** and continues in parallel.

---

## 2. Field Ownership Matrix

| Field | Class | Writer | Mutability |
| --- | --- | --- | --- |
| `replyStatus` | Provider fact | `PostSyncReplyEvent` at create | **Immutable** after create |
| `receivedAt`, `externalEventId`, `sendTraceReference`, `sendExecution`, `lead`, `eventMetadata` | Provider fact | Ingress at create | Immutable (existing unique index on `externalEventId`) |
| `triageStatus` | Work lifecycle | `ReplyTriageService`; ingress **at create only** (initialization) | Transitions per ADR-C19 (amended) §3.3 |
| `assignedUser` | Ownership | `ReplyTriageService` (assign/release) + ingress seed | Written on IN_PROGRESS (set) and OPEN (clear); CLOSED retains |
| `closedReason` / `closedAt` / `closedBy` | Close audit | `ReplyTriageService` | readOnly; reason required for CLOSED |

Initialization policy at ingress: `REPLIED` / `BOUNCED` / `UNSUBSCRIBED` → `OPEN`;
`SENT` → null (monitoring signal, not work).

---

## 3. Components (WP1 build list — implemented)

| Component | Type | Responsibility |
| --- | --- | --- |
| `Api/PostSyncReplyEvent.php` | New API action | `POST /Prospecting/reply-event/sync`; integration-actor authorization; payload validation; dedupe on `externalEventId` (idempotent 200 on duplicate); create with provider fact + triage initialization; **no Lead writes** |
| `Services/ReplyTriageService.php` | New lifecycle owner | Sole writer of `triageStatus` + `assignedUser` + close audit fields; transition matrix `OPEN→IN_PROGRESS`, `OPEN→CLOSED`, `IN_PROGRESS→OPEN`, `IN_PROGRESS→CLOSED`; action authorization (`replyEvent.assign` / `replyEvent.release` / `replyEvent.close`); `afterTriage()` structured log |
| `Hooks/ReplyEvent/` triage guard | New BeforeSave guard | `triageStatus` / `closedReason` / `closedAt` / `closedById` accepted only with authorized save option (`StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED`); `replyStatus` rewrite rejected; create-time initialization limited to OPEN; mirrors `SendExecutionStatusMutationGuard` |
| `Classes/Select/ReplyEvent/PrimaryFilters/C19OpenReplies.php` | New PrimaryFilter | `where(['triageStatus' => 'OPEN'])` — single predicate, server-side, non-mutating |
| `Classes/Select/ReplyEvent/PrimaryFilters/C19MyReplies.php` | New PrimaryFilter | `where(['triageStatus' => 'IN_PROGRESS', 'assignedUserId' => current])` — operator-scoped, server-side user binding via constructor injection |
| `selectDefs/ReplyEvent.json` | Metadata | `primaryFilterClassNameMap` entries for `c17AwaitingReply`, `c19OpenReplies`, `c19MyReplies` |
| `clientDefs/ReplyEvent.json` | Metadata | Name-only `filterList` exposure (`c19OpenReplies`, `c19MyReplies`); **no** client `where` |
| `entityDefs/ReplyEvent.json` | Metadata | `triageStatus` enum (readOnly, options `OPEN`/`IN_PROGRESS`/`CLOSED`, nullable), `closedReason`, `closedAt`, `closedBy`; `assignedUser` link |
| `app.prospectingWorkflow` policy | Metadata | Role bindings for the three triage action keys (logged fallback per existing pattern) |
| i18n `Global.json` + `ReplyEvent.json` (zh/en) | Metadata | Field labels, option labels (待处理/处理中/已关闭), filter labels (待处理回复/我的回复) |

Entry-point UI (WP1): detail-view action menu only (Assign / Release / Close with
confirmation + reason prompt), modeled on the Quote command flow. **No list-row
actions, no inline edit, no dashlet mutation.**

---

## 4. Queue and Surface Contracts

| Surface | Filter | Predicate | Notes |
| --- | --- | --- | --- |
| Command Center 已回复待处理 (WP3) | `c19OpenReplies` | `triageStatus = OPEN` | Work queue; sort `receivedAt` desc |
| 触达中心 link (existing card surface) | `c19OpenReplies` | same | Add link entry beside 客户回复 (WP3 composition) |
| Operator "My Replies" (WP3) | `c19MyReplies` | `triageStatus = IN_PROGRESS AND assignedUserId = current` | User-scoped (mirrors 我的任务 `onlyMy` pattern); optional Command Center queue |
| Existing C17 queue | `c17AwaitingReply` | `replyStatus = SENT` | **Kept** — monitoring queue; WP3 re-titles to 已发送未回复 for disambiguation |

Read-only guarantees (carried): queues narrow after ACL, never widen; no
`skipAccessCheck`; no mutation strings on composition surfaces (contract-tested).

---

## 5. Interaction with Existing Pipelines

| Pipeline | Relationship |
| --- | --- |
| `BrevoEmailEventSyncService` / connector reply tracking | Continue to map provider events (`email_replied → REPLIED`, …). Ingress consumes the normalized result; connector code is **not** changed by WP1 |
| `EmailLifecycleProjectionService` | Remains sole writer of `Lead.peEmailReplyStatus` / `peLastEmailDate`. Triggered by ReplyEvent save hook as today. Triage writes must not re-trigger rank projection (`triageStatus` is not a projection input) |
| `SendExecutionTransitionService` | No interaction; reply triage never writes SendExecution state |
| Quote / Approval workflows | No interaction |

---

## 6. Authorization Matrix (WP1 metadata policy)

| Action | Sales User | Sales Manager | Integration Bot | Admin |
| --- | --- | --- | --- | --- |
| `replyEvent.assign` (OPEN → IN_PROGRESS) | ✅ | ✅ | — | ✅ |
| `replyEvent.release` (IN_PROGRESS → OPEN) | ✅ | ✅ | — | ✅ |
| `replyEvent.close` (→ CLOSED; reason required) | ✅ | ✅ | — | ✅ |
| Ingress sync (`PostSyncReplyEvent`) | — | — | ✅ | ✅ |

Rationale: triage is the queue-owning role's daily work (Sales User holds
assign/release/close); ingress is an integration concern. Authorization = entity
read ACL + action binding (Quote pattern); unauthorized → `403 Forbidden`, zero writes.

---

## 7. Test Expectations (WP1 contract suite — passing)

1. Marker `adr-c19-replyevent-v1` asserted in policy + tests.
2. `replyStatus` rewrite attempt → rejected by guard.
3. `triageStatus` write without authorized save option → rejected.
4. Transition matrix enforced: illegal transitions (`null→CLOSED`, `OPEN→OPEN`, `CLOSED→*`, …) → `BadRequest`.
5. Close without reason → rejected; unauthorized actor → `Forbidden`, zero writes.
6. Ingress: duplicate `externalEventId` → idempotent, no second record; `SENT` payload → `triageStatus` null; `REPLIED` payload → `OPEN`; no Lead-field writes at ingress.
7. `c19OpenReplies` returns only `triageStatus = OPEN`, server-side, ACL-narrowed; `c19MyReplies` returns `IN_PROGRESS` + assigned to current user, server-side.
8. Projection isolation: triage transition does not alter `Lead.peEmailReplyStatus`.
9. No mutation strings on any queue/dashboard surface (grep-level contract, C17/C18 style).
10. Ownership: assign writes `assignedUserId`; release clears it; close retains last assignee.

---

## 8. Deferred (explicit non-goals for WP1)

- Auto-triage / classification of reply content
- Reply drafting or sending from the triage surface (outreach pipeline concern)
- Unsubscribe-suppression automation (compliance WP)
- `stream`/feed enablement decision (audit-only default)
- Command Center composition (WP3)
