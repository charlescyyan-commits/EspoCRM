# ADR: C16 ACCEPTED Lifecycle State — Deferred

**Status:** Accepted — Design Freeze
**Date:** 2026-07-22
**Phase:** Phase3C16.3B Release Freeze
**References:** [ADR_C16_STATE_MACHINE_EXTENSIONS.md](architecture/ADR_C16_STATE_MACHINE_EXTENSIONS.md), [ADR_C16_STATE_MACHINE_ADDENDUM.md](architecture/ADR_C16_STATE_MACHINE_ADDENDUM.md)

---

## 1. Context

The C16 Quote state machine, as designed in `ADR_C16_STATE_MACHINE_EXTENSIONS.md`, defines the `ACCEPTED` state as a valid terminal state reachable from `SENT` via the `accepted()` transition. This state models a customer's formal acceptance of a sent quotation.

During Phase3C16.3B implementation and release freeze verification, it was determined that:

1. The `ACCEPTED` state enum is defined in the metadata.
2. The `accepted()` transition exists in the state machine specification.
3. **No runtime API surface currently exposes this transition.**
4. **No workflow endpoint, controller, or action handler implements `accepted()` at this time.**

## 2. Decision

**The `ACCEPTED` lifecycle state is reserved in the design but deferred from the current runtime surface.**

### 2.1 What IS Implemented

The following Quote states and transitions are fully implemented and verified at runtime:

| State | Reachable From | Via |
|-------|---------------|-----|
| DRAFT | REJECTED, IN_REVIEW (reject-review) | `requestRevision()`, `rejectReview()` |
| IN_REVIEW | DRAFT, REJECTED (resubmit) | `submitForReview()`, `resubmit()` |
| APPROVED | IN_REVIEW | `approve()` |
| SENT | APPROVED | `send()` |
| REJECTED | SENT | `rejected()` (customer rejection) |
| EXPIRED | APPROVED | `expire()` (admin-only) |

### 2.2 What IS Deferred

| State | Transition | Reason |
|-------|-----------|--------|
| ACCEPTED | `accepted()` from SENT | No runtime API surface; deferred to future commercial lifecycle phase |

## 3. Rationale

### 3.1 Why Reserve, Not Remove

- The `ACCEPTED` state is architecturally sound: it models the natural conclusion of a successful quote-to-order pipeline.
- Removing it from the metadata would require a migration to re-add it later, creating unnecessary churn.
- Keeping it reserved in the design ensures the state machine diagram and documentation remain aligned with the intended long-term architecture.

### 3.2 Why Not Implement Now

- The commercial workflow that triggers `accepted()` (e.g., customer clicks "Accept Quote" in a portal, or an ERP integration marks it accepted) is not yet defined.
- Implementing a transition without a clear triggering actor and authorization model would create dead code and potential security surface without value.
- The existing workflow endpoints (`submit-for-review`, `approve`, `send`, `reject-review`, `customer-reject`, `expire`) cover the complete B2B quote negotiation lifecycle that Phase3C16.3B targets.

### 3.3 No Security Risk

- The `ACCEPTED` state is unreachable through any HTTP endpoint, workflow action, or service method.
- Direct `EntityManager` mutation is blocked by `QuoteStatusMutationGuard`.
- No ACL rule, controller route, or scope exposes `accepted()`.

## 4. Future Activation

When the `ACCEPTED` lifecycle is activated, the following will be required:

1. A workflow action handler (e.g., `PostQuoteWorkflowAction` with `action=accept`).
2. An authorization decision (which roles may accept? Customer? Manager? Both?).
3. A triggering mechanism (API endpoint, portal UI action, or ERP webhook).
4. Transition validation rules (e.g., only from `SENT`, only if not expired).
5. Test coverage for the new transition path.

## 5. Consequences

- **Positive:** Clean architecture — the state machine design is forward-looking without dead runtime code.
- **Positive:** No security surface for an unimplemented transition.
- **Negative:** The state machine diagram shows `ACCEPTED` as reachable, but it is not. This ADR documents the gap.
- **Mitigation:** Future phases will activate `ACCEPTED` when the commercial lifecycle requires it.

## 6. Relationship to R5 Verdict

The R5 report (`PHASE3C16_3B_4R5_RUNTIME_DEFECT_REPAIR_AND_COMPLETE_RESMOKE_REPORT.md`) notes that `POST /api/v1/Quote` returns HTTP 404 — a separate deferred API-surface gap (Scope Amendment A). The `ACCEPTED` state deferral is consistent with that scope boundary: neither generic Quote CRUD nor the `accepted()` transition are in the Phase3C16.3B runtime surface.

## 7. Signoff

This ADR is accepted as part of the Phase3C16.3B release freeze. The `ACCEPTED` state remains reserved in the metadata and state machine specification but carries no runtime surface, no security risk, and no blocker status for the current release.
