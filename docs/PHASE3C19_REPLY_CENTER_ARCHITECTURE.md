# Phase3C19 Reply Center Architecture

**Status:** Accepted design (WP1 implementation input; no code in WP0)
**Date:** 2026-07-26
**Implements:** `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` — governance marker **`adr-c19-replyevent-v1`**
**Baseline:** `9bbd44a` / `phase3c18-freeze`

> "Reply Center" is an **architecture name** for the reply-handling pipeline.
> It is **not** a new scope, entity, or navigation center (C19 Charter §5).

---

## 1. Objective

Give sales operators a governed daily workflow for provider reply events:

```
provider webhook / sync
        │
        ▼
PostSyncReplyEvent (ingress) ── creates ReplyEvent ── replyStatus = provider fact (immutable)
        │                                              triageStatus = OPEN (actionable) or null
        ▼
c19OpenReplies queue (server-side PrimaryFilter, read-only surface)
        │
        ▼  operator acts from the ReplyEvent detail view (never the queue)
ReplyTriageService ── sole writer of triageStatus
        │
        ▼
RESOLVED / IGNORED (+ reopen back to OPEN)
```

The Lead projection path (`EmailLifecycleProjectionService` → `Lead.peEmailReplyStatus`)
is **untouched** and continues in parallel.

---

## 2. Field Ownership Matrix

| Field | Class | Writer | Mutability |
| --- | --- | --- | --- |
| `replyStatus` | Provider fact | `PostSyncReplyEvent` at create | **Immutable** after create |
| `receivedAt`, `externalEventId`, `sendTraceReference`, `sendExecution`, `lead`, `eventMetadata` | Provider fact | Ingress at create | Immutable (existing unique index on `externalEventId`) |
| `triageStatus` | Work lifecycle | `ReplyTriageService`; ingress **at create only** (initialization) | Transitions per ADR-C19 §3.3 |
| `triagedAt` / `triagedBy` / `triageReason` | Triage audit | `ReplyTriageService` | readOnly; reason required for `IGNORED` |

Initialization policy at ingress: `REPLIED` / `BOUNCED` / `UNSUBSCRIBED` → `OPEN`;
`SENT` → null (monitoring signal, not work).

---

## 3. Components (WP1 build list)

| Component | Type | Responsibility |
| --- | --- | --- |
| `Api/PostSyncReplyEvent.php` | New API action | `POST /Prospecting/reply-event/sync`; integration-actor authorization; payload validation; dedupe on `externalEventId` (idempotent 200 on duplicate); create with provider fact + triage initialization; **no Lead writes** |
| `Services/ReplyTriageService.php` | New lifecycle owner | Sole writer of `triageStatus` + triage audit fields; transition matrix `OPEN→RESOLVED`, `OPEN→IGNORED`, `RESOLVED\|IGNORED→OPEN`; action authorization (`replyEvent.resolve` / `replyEvent.ignore` / `replyEvent.reopen`); `afterTriage()` structured log |
| `Hooks/ReplyEvent/` triage guard | New BeforeSave guard (WP1) | `triageStatus` / triage audit fields accepted only with authorized save option (e.g. `ReplyTriageSaveOption::TRIAGE_MUTATION_AUTHORIZED`); `replyStatus` rewrite rejected; mirrors `SendExecutionStatusMutationGuard` |
| `Classes/Select/ReplyEvent/PrimaryFilters/C19OpenReplies.php` | New PrimaryFilter | `where(['triageStatus' => 'OPEN'])` — single predicate, server-side, non-mutating |
| `selectDefs/ReplyEvent.json` | Metadata | `primaryFilterClassNameMap.c19OpenReplies` entry |
| `clientDefs/ReplyEvent.json` | Metadata | Name-only `filterList` exposure (`c19OpenReplies`); **no** client `where` |
| `entityDefs/ReplyEvent.json` | Metadata (additive) | `triageStatus` enum (readOnly, options `OPEN`/`RESOLVED`/`IGNORED`, nullable), `triagedAt`, `triagedBy`, `triageReason`; optional `audited: true` decision recorded at WP1 |
| `app.prospectingWorkflow` policy | Metadata | Role bindings for the three triage action keys (logged fallback per existing pattern) |
| i18n `Global.json` + `ReplyEvent.json` (zh/en) | Metadata | Field labels, option labels, `C19DashboardOpenReplies` queue label, filter `presetFilters` labels |

Entry-point UI (WP1): detail-view action menu only (Resolve / Ignore / Reopen with
confirmation + reason prompt), modeled on the Quote command flow. **No list-row
actions, no inline edit, no dashlet mutation.**

---

## 4. Queue and Surface Contracts

| Surface | Filter | Predicate | Notes |
| --- | --- | --- | --- |
| Command Center 已回复待处理 (WP3) | `c19OpenReplies` | `triageStatus = OPEN` | Work queue; sort `receivedAt` desc |
| 触达中心 link (existing card surface) | `c19OpenReplies` | same | Add link entry beside 客户回复 (WP3 composition) |
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

## 6. Authorization Matrix (proposal, frozen in WP1 metadata policy)

| Action | Sales User | Sales Manager | Integration Bot | Admin |
| --- | --- | --- | --- | --- |
| `replyEvent.resolve` | ✅ | ✅ | — | ✅ |
| `replyEvent.ignore` (reason required) | ✅ | ✅ | — | ✅ |
| `replyEvent.reopen` | — | ✅ | — | ✅ |
| Ingress sync (`PostSyncReplyEvent`) | — | — | ✅ | ✅ |

Rationale: triage is the queue-owning role's daily work (Sales User holds
resolve/ignore); reopen rewinds a colleague's decision and is manager-gated; ingress is
an integration concern. Authorization = entity read ACL + action binding (Quote
pattern); unauthorized → `403 Forbidden`, zero writes.

---

## 7. Test Expectations (WP1 contract suite)

1. Marker `adr-c19-replyevent-v1` asserted in policy + tests.
2. `replyStatus` rewrite attempt → rejected by guard.
3. `triageStatus` write without authorized save option → rejected.
4. Transition matrix enforced: illegal transitions (`null→RESOLVED`, `OPEN→OPEN`, …) → `BadRequest`.
5. `IGNORED` without reason → rejected; unauthorized actor → `Forbidden`, zero writes.
6. Ingress: duplicate `externalEventId` → idempotent, no second record; `SENT` payload → `triageStatus` null; `REPLIED` payload → `OPEN`; no Lead-field writes at ingress.
7. `c19OpenReplies` returns only `triageStatus = OPEN`, server-side, ACL-narrowed; unknown primaryFilter → expected error.
8. Projection isolation: triage transition does not alter `Lead.peEmailReplyStatus`.
9. No mutation strings on any queue/dashboard surface (grep-level contract, C17/C18 style).

---

## 8. Deferred (explicit non-goals for WP1)

- Auto-triage / classification of reply content
- Reply drafting or sending from the triage surface (outreach pipeline concern)
- Unsubscribe-suppression automation (compliance WP)
- `stream`/feed enablement decision (audit-only default)
- Command Center composition (WP3)

---

*Architecture design only. WP0 modifies no PHP, metadata, tests, navigation, ACL configuration, or release artifacts.*
