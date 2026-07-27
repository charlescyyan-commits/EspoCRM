# Phase3C19 WP1.5 — Reply Center Lifecycle Reconciliation Report

**Status:** Complete
**Date:** 2026-07-27
**Baseline:** `master @ 74f0f1eb` (Phase3C19, Reply Center WP1 implemented)
**Governance Marker:** `adr-c19-replyevent-v1`
**Review Type:** Architecture Decision Review — Documentation Reconciliation

---

## 1. Background

At WP1 implementation, the Reply Center's `triageStatus` lifecycle adopted a different
state model than what WP0's ADR-C19 documented. This report records the formal
reconciliation: reviewing both models, evaluating impact, selecting the superior
design, and amending the documentation stack.

---

## 2. Divergence Detected

### ADR-C19 (WP0 documentation)

```
States:     (null), OPEN, RESOLVED, IGNORED
Transitions: OPEN → RESOLVED (resolve)
             OPEN → IGNORED (ignore; reason required)
             IGNORED → OPEN (reopen)
             RESOLVED → OPEN (reopen)
Audit:      triagedAt, triagedBy, triageReason
Actions:    replyEvent.resolve, replyEvent.ignore, replyEvent.reopen
Queues:     c19OpenReplies only
```

### WP1 Code (implemented)

```
States:     (null), OPEN, IN_PROGRESS, CLOSED
Transitions: OPEN → IN_PROGRESS (assign — take ownership)
             OPEN → CLOSED (close; reason required)
             IN_PROGRESS → OPEN (release — return to pool)
             IN_PROGRESS → CLOSED (close; reason required)
             CLOSED → (none — terminal)
Audit:      closedReason, closedAt, closedBy (on CLOSE only)
Actions:    replyEvent.assign, replyEvent.release, replyEvent.close
Queues:     c19OpenReplies + c19MyReplies
Ownership:  assignedUserId written on assign/release
```

---

## 3. Impact Assessment

### 3.1 Queue Filters

**Finding:** Code added `c19MyReplies` (operator-scoped, IN_PROGRESS + assignedUser).
**Assessment:** Essential for multi-user work queues. Mirrors the `我的任务` pattern.
**Verdict:** Code superior. Two-queue design required.

### 3.2 Ownership

**Finding:** Code writes `assignedUserId` on assign/release; ADR had no ownership mechanism.
**Assessment:** Without explicit ownership, two operators could simultaneously work the same reply. Code model prevents this.
**Verdict:** Code superior. Ownership is operationally necessary.

### 3.3 Command Center (WP3)

**Finding:** WP3 design needs to account for `c19MyReplies` as an optional user-scoped queue.
**Assessment:** Minor composition change. The `我的任务` (onlyMy) pattern already exists in the Command Center.
**Verdict:** Low impact. WP3 design updated accordingly.

### 3.4 Workflow / Authorization

**Finding:** Actions changed from resolve/ignore/reopen to assign/release/close.
**Assessment:** Same cardinality (3 actions); code's actions are cleaner and more descriptive.
**Verdict:** Code superior. Actions map directly to observable operations.

### 3.5 Audit Fields

**Finding:** ADR specified triagedAt/triagedBy/triageReason (on every transition). Code uses closedReason/closedAt/closedBy (on CLOSE only).
**Assessment:** Code approach is more economical — audit the terminal action only. Assign/release are temporal states tracked through standard modifiedAt/modifiedBy. Requiring reason for every close (not just IGNORED) is stronger.
**Verdict:** Code superior. Terminal-only audit is sufficient; EspoCRM's standard audit covers the rest.

---

## 4. Decision

| Item | Value |
|------|-------|
| **Decision** | **Amend ADR-C19 to match WP1 code** |
| **Rationale** | Code model is operationally superior on all five assessed dimensions: explicit ownership, CRM-native semantics, two-queue coverage, cleaner action keys, and economical terminal-only audit |
| **Code changes** | None |
| **Document changes** | 4 files amended (see §5) |

---

## 5. Documents Amended

| File | Changes |
|------|---------|
| `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` | §§3–8 rewritten: IN_PROGRESS/CLOSED states, assign/release/close actions, c19MyReplies queue, ownership semantics, closedReason/closedAt/closedBy audit. §10 decision log entry added. Status → Accepted (Amended). |
| `docs/PHASE3C19_REPLY_CENTER_ARCHITECTURE.md` | §1 pipeline diagram, §2 field matrix, §3 component table, §4 queue contracts (c19MyReplies added), §6 authorization matrix, §7 test expectations — all reconciled to WP1 code. |
| `docs/PHASE3C19_WP0_ADR_ACCEPTANCE_REPORT.md` | D2 description amended; §3 marker stack updated; §4 file status notes added; §7 decision log entry added. |
| `docs/PHASE3C19_COMMAND_CENTER_DESIGN.md` | §2.4 reply queue description updated; queue wiring summary table updated with c19MyReplies row. |

### 5.1 Document NOT Changed

- `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` — unrelated; no reply lifecycle impact
- `docs/PHASE3C19_SEND_RECOVERY_ARCHITECTURE.md` — unrelated; no reply lifecycle impact
- `docs/PHASE3C19_CHARTER.md` — charter scope unchanged; WP1 implementation delivered the chartered scope

---

## 6. What Does NOT Change

- `replyStatus` provider fact immutability
- `PostSyncReplyEvent` ingress responsibilities and triage initialization policy
- `ReplyTriageService` sole-writer ownership
- `StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED` guard mechanism
- `ReplyEventMutationGuard` persistence boundary pattern
- `EmailLifecycleProjectionService` isolation
- Governance marker `adr-c19-replyevent-v1`
- C17 `c17AwaitingReply` monitoring queue (frozen, untouched)

---

## 7. Verification

| Check | Result |
|-------|--------|
| All C19-WP1 contract tests pass | ✅ (test_phase3c19_wp1_reply_triage.py, test_phase3c19_wp1_reply_queue_filters.py) |
| Governance marker consistent across code + docs | ✅ `adr-c19-replyevent-v1` |
| Provider fact immutability intact | ✅ |
| No code changes in this reconciliation | ✅ (documentation only) |
| No changes to C18/C17 artifacts | ✅ |
| ADR-C19, architecture, WP0 report, Command Center design all consistent | ✅ |

---

## 8. Decision Log

| Date | Decision |
|------|----------|
| 2026-07-26 | ADR-C19 Accepted at WP0 with RESOLVED/IGNORED/reopen model |
| 2026-07-27 | WP1 implemented IN_PROGRESS/CLOSED with explicit ownership |
| 2026-07-27 | Architecture Decision Review complete: code model recommended |
| 2026-07-27 | ADR-C19 amended; architecture + WP0 report + Command Center design reconciled |
