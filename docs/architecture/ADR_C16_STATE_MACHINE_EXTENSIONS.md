# ADR: C16 State Machine Extensions

**Status:** Accepted — Design Freeze  
**Date:** 2026-07-21  
**Phase:** Phase3C16 Architecture Refinement  
**Supersedes:** ADR_C16_QUOTE_PI_ARCHITECTURE.md §4 (extends, does not replace)  
**References:** [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md), [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md), [ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md](ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md)

---

## Table of Contents

1. [Quote Lifecycle — Extended](#1-quote-lifecycle--extended)
2. [Quote Modification Rules](#2-quote-modification-rules)
3. [PI Lifecycle — Workflow and Payment Separation](#3-pi-lifecycle--workflow-and-payment-separation)
4. [Quote / PI Relationship](#4-quote--pi-relationship)
5. [Approval Lifecycle — Extended](#5-approval-lifecycle--extended)
6. [State Transition Rules — Complete Tables](#6-state-transition-rules--complete-tables)
7. [Test Implications](#7-test-implications)

---

## 1. Quote Lifecycle — Extended

### 1.1 Complete State Diagram

The base ADR defines 7 states with transitions. This section adds the **APPROVED → EXPIRED** path and defines expiration triggers in detail.

```
                         ┌──────────────┐
                         │    DRAFT     │◄──────────────────────────┐
                         └──────┬───────┘                           │
                                │ submitForReview()                 │
                                ▼                                   │
                         ┌──────────────┐                           │
                         │  IN_REVIEW   │                           │
                         └──────┬───────┘                           │
                                │                                   │
              ┌─────────────────┼─────────────────┐                 │
              │ requestRevision()                 │ approve()       │
              ▼                                   ▼                 │
       ┌──────────────┐                    ┌──────────────┐         │
       │    DRAFT     │                    │   APPROVED   │─────────┼──┐
       └──────────────┘                    └──────┬───────┘         │  │
                                                  │ send()          │  │
                                                  ▼                 │  │
                                           ┌──────────────┐         │  │
                                           │     SENT     │         │  │
                                           └──────┬───────┘         │  │
                                                  │                 │  │
                               ┌──────────────────┼──────────┐      │  │
                               │                  │          │      │  │
                         accepted()         rejected()   expire()   │  │
                               │                  │          │      │  │
                               ▼                  ▼          ▼      │  │
                        ┌───────────┐     ┌───────────┐ ┌────────┐  │  │
                        │ ACCEPTED  │     │ REJECTED  │ │EXPIRED │◄─┘  │
                        └───────────┘     └───────────┘ └────────┘     │
                                                                       │
                                                    expire() from       │
                                                    APPROVED (new) ─────┘
```

### 1.2 Expiration Triggers

A Quote transitions to EXPIRED when:

| Trigger | From State | Mechanism | Actor |
|---------|-----------|-----------|-------|
| `validUntil` date passed | DRAFT | System cron (`QuoteExpirationJob`) | System |
| `validUntil` date passed | APPROVED | System cron (`QuoteExpirationJob`) | System |
| `validUntil` date passed | SENT | System cron (`QuoteExpirationJob`) | System |
| Manual expire | DRAFT | Admin action | Admin |
| Manual expire | APPROVED | Admin action | Admin |
| Manual expire | SENT | Admin action | Admin |

**Expiration rules:**
- A Quote can expire from DRAFT, APPROVED, or SENT.
- A Quote cannot expire from IN_REVIEW — the reviewer should either approve or request revision; expiration from review is a DRAFT→EXPIRED path after revision.
- Expiration from ACCEPTED or REJECTED is meaningless — these are terminal states.
- Expiration does **not** change line items, PDFs, or attached Approvals. It only changes the `status` field and sets a timestamp.
- Expired Quotes can be cloned as new DRAFT Quotes (the "Re-quote" pattern).

### 1.3 State Semantics

| State | Meaning | Visibility to Customer | Editable |
|-------|---------|----------------------|----------|
| **DRAFT** | Internal working document. Not yet submitted for review. | ❌ | ✅ Full edit |
| **IN_REVIEW** | Submitted to Manager for approval. Identifiable by `quoteNumber`. | ❌ | ⚠️ Restricted (§2) |
| **APPROVED** | Manager approved. Ready to send to customer. | ❌ (until sent) | ❌ (except notes) |
| **SENT** | Delivered to customer. Awaiting response. | ✅ | ❌ (except accept/reject/notes) |
| **ACCEPTED** | Customer accepted the Quote. Terminal. | ✅ | ❌ Terminal |
| **REJECTED** | Customer rejected the Quote. Terminal. | ✅ | ❌ Terminal |
| **EXPIRED** | Quote validity period elapsed. Terminal. | N/A | ❌ Terminal |

### 1.4 APPROVED → EXPIRED (New Path)

**Why this path exists:** A Quote may be approved by a Manager but not sent to the customer within the validity window. For example:
- Sales rep is on leave after approval
- Customer requested a delay in receiving the formal Quote
- Internal process delay (PDF generation issue, compliance check)

Without the APPROVED → EXPIRED path, an approved-but-unsent Quote would remain in APPROVED indefinitely, cluttering the pipeline and creating ambiguity. The system cron transitions it to EXPIRED when `validUntil < now()`.

**Difference from SENT → EXPIRED:**
- SENT → EXPIRED: The customer received the Quote but didn't respond in time. The Quote is part of the customer's history.
- APPROVED → EXPIRED: The Quote was never sent. The customer never saw it. It's an internal expiration.

---

## 2. Quote Modification Rules

### 2.1 Edit Permissions by State

| State | Line Items | Financial Fields | Terms | Notes | Status |
|-------|:----------:|:----------------:|:-----:|:-----:|:------:|
| **DRAFT** | ✅ Add/Edit/Delete | ✅ Edit all | ✅ | ✅ | ❌ (only via transitions) |
| **IN_REVIEW** | ❌ Locked | ❌ Locked | ✅ (minor) | ✅ | ❌ (only via transitions) |
| **APPROVED** | ❌ Locked | ❌ Locked | ❌ Locked | ✅ | ❌ (only via transitions) |
| **SENT** | ❌ Locked | ❌ Locked | ❌ Locked | ✅ | ❌ (only accept/reject) |
| **ACCEPTED** | ❌ Locked | ❌ Locked | ❌ Locked | ❌ | ❌ Terminal |
| **REJECTED** | ❌ Locked | ❌ Locked | ❌ Locked | ✅ | ❌ Terminal |
| **EXPIRED** | ❌ Locked | ❌ Locked | ❌ Locked | ✅ | ❌ Terminal |

### 2.2 DRAFT: Full Edit

- All fields are editable
- Line items can be added, removed, or modified
- `subtotal`, `taxAmount`, `total` are recalculated from line items on every save
- `quoteNumber` is not yet assigned

### 2.3 IN_REVIEW: Restricted Edit

- **Line items are locked.** Once submitted for review, the commercial terms are fixed. A reviewer should not have the Quote change underneath them.
- **Financial fields are locked.** `subtotal`, `taxAmount`, `total`, `taxRate`, `currency` cannot change during review.
- **Terms are editable (minor).** `termsAndConditions` can be adjusted for clarity. `validUntil` can be extended if the review process takes longer than expected.
- **Notes are editable.** Internal notes can be added by both the submitter and the reviewer.
- **Status changes only via transitions:** `requestRevision` (back to DRAFT) or `approve` (forward to APPROVED).
- **`quoteNumber` is immutable** once assigned on DRAFT → IN_REVIEW.

### 2.4 APPROVED: Locked Except Notes

- All commercial fields are locked: line items, financials, terms, currency.
- Notes remain editable for internal communication.
- The only valid state transition is `send()` → SENT, or system-triggered `expire()` → EXPIRED.
- **Rationale for locking financial fields:** After Manager approval, the Quote represents an authorized offer. Changing financial terms after approval would circumvent the approval process.

### 2.5 SENT: Customer-Facing Immutability

- The Quote is now a customer-facing document. **No field that appears on the PDF may change.**
- Only `notes` and `status` (via accept/reject transitions) are modifiable.
- If a change is needed after sending: create a new Quote (clone from the SENT Quote as DRAFT), revise, re-approve, and re-send. The old SENT Quote remains in history as REJECTED (superseded) or EXPIRED.

### 2.6 Terminal States: Read-Only

- ACCEPTED, REJECTED, EXPIRED: no edits of any kind.
- These are historical records. Any new engagement starts from a new DRAFT Quote.
- **Exception:** A REJECTED Quote's `notes` field may be updated to record the reason for re-engagement (e.g., "Customer reconsidered — see QT-2026-0051 for new Quote").

---

## 3. PI Lifecycle — Workflow and Payment Separation

### 3.1 Design Principle: Separate Workflow State from Payment State

A Proforma Invoice has two independent dimensions:

| Dimension | Purpose | States |
|-----------|---------|--------|
| **Workflow state** | Where the PI is in the issuance/send lifecycle | DRAFT, ISSUED, SENT, VOID |
| **Payment state** | Whether the PI has been paid | UNPAID, PARTIAL, PAID, OVERDUE |

**Why separate:**

1. **Different actors.** Workflow is driven by Finance (issue, send). Payment is driven by external reality (customer pays). Conflating them creates artificial coupling.
2. **Different timelines.** A PI can be SENT (workflow) and remain UNPAID (payment) for 30+ days. The PI is not "incomplete" — it's sent and awaiting payment.
3. **Partial payments.** A single PI can receive multiple payments. Tracking `PARTIAL` vs. `PAID` is a payment concern, not a workflow concern.
4. **Independent state transitions.** A PI can transition from UNPAID to OVERDUE without changing its workflow state. A PI can be VOID (workflow) and still show its last known payment state for audit.

### 3.2 Workflow State Machine (Extended)

```
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │ issue()
                           ▼
                    ┌──────────────┐
                    │    ISSUED    │──────────────────────────┐
                    └──────┬───────┘                          │
                           │ send()                           │
                           ▼                                  │
                    ┌──────────────┐                          │
                    │     SENT     │                          │
                    └──────────────┘                          │
                                                              │
                    ┌──────────────┐                          │
                    │     VOID     │◄─────────────────────────┘
                    └──────────────┘   void() from any non-terminal
```

**Workflow states:**

| State | Meaning | Payment Field Write Access |
|-------|---------|:--------------------------:|
| **DRAFT** | Internal working document. Not yet issued. | ✅ Finance can set initial payment status |
| **ISSUED** | Formally issued with `piNumber`. Financial snapshot frozen. | ✅ Finance can update payment status |
| **SENT** | Delivered to customer. Awaiting payment. | ✅ Finance can update payment status |
| **VOID** | Cancelled. Terminal. | ❌ Payment status frozen at last value |

### 3.3 Payment State Machine (Independent Dimension)

```
                    ┌──────────────┐
                    │   UNPAID     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │ partial    │            │ due date passed
              ▼            │            ▼
       ┌──────────────┐    │     ┌──────────────┐
       │   PARTIAL    │    │     │   OVERDUE    │
       └──────┬───────┘    │     └──────┬───────┘
              │            │            │
              │ paid       │ paid       │ paid
              ▼            ▼            ▼
       ┌──────────────────────────────────────┐
       │               PAID                   │
       └──────────────────────────────────────┘
```

**Payment states:**

| State | Meaning | Trigger |
|-------|---------|---------|
| **UNPAID** | No payment received. Default for new PIs. | Initial state |
| **PARTIAL** | Some but not all of the total paid. | Manual (Finance records a partial payment) |
| **PAID** | Full amount received. Terminal. | Manual (Finance confirms full payment) |
| **OVERDUE** | Payment due date passed without full payment. | System cron or manual |

**Payment state transitions are independent of workflow transitions.** A PI can be:
- SENT + UNPAID (normal — just sent, awaiting payment)
- SENT + PARTIAL (customer made a partial payment)
- SENT + PAID (fully paid)
- SENT + OVERDUE (past due date, unpaid or partially paid)
- VOID + PAID (paid but later voided — rare, for audit trail)

### 3.4 Payment State Field Design

Rather than a single `paymentStatus` field on ProformaInvoice, payment tracking uses a dedicated `Payment` entity (future — C16.5+ enhancement or post-C16):

```
ProformaInvoice
├── paymentStatus: enum (UNPAID, PARTIAL, PAID, OVERDUE)  ← summary field
├── paymentDueDate: date                                   ← for OVERDUE cron
├── paidAmount: currency                                   ← running total of payments
└── payments: hasMany Payment (future entity)
```

**C16.5 scope:** Implement `paymentStatus`, `paymentDueDate`, and `paidAmount` as fields on ProformaInvoice. The `Payment` entity for tracking individual payments is deferred to a post-C16 enhancement. The `paymentStatus` field is updated manually by Finance (recording a payment) or automatically by system cron (marking OVERDUE).

---

## 4. Quote / PI Relationship

### 4.1 Quote State Required for PI Creation

| Quote State | Can Create PI? | Rationale |
|-------------|:--------------:|-----------|
| DRAFT | ❌ | Quote is not yet a committed offer |
| IN_REVIEW | ❌ | Quote is under review; terms may change |
| APPROVED | ✅ | Quote is approved and represents a firm offer |
| SENT | ✅ | Quote has been sent to customer |
| ACCEPTED | ✅ | Customer accepted; PI is the natural next step |
| REJECTED | ❌ | Quote was rejected; no basis for PI |
| EXPIRED | ❌ | Quote validity elapsed |

**Primary path:** Quote ACCEPTED → create PI. The customer has formally accepted the Quote; the PI formalizes the financial obligation.

**Allowed path:** Quote APPROVED → create PI. Some business processes issue a PI alongside the Quote (before formal acceptance), especially for international trade where the PI is needed for import licensing or letter of credit applications.

### 4.2 Quote Freeze on PI Issuance

When a PI transitions DRAFT → ISSUED:

| Quote Field | Behavior |
|-------------|----------|
| `status` | **Not changed.** The Quote remains in its current state. |
| Line items | **Not changed.** The PI has its own `quoteSnapshot`. |
| Financial fields | **Not changed.** The PI has its own copy. |
| Ability to transition to DRAFT | **Blocked** if any non-VOID ISSUED/SENT PI references this Quote |

**Quote freeze rule:** A Quote cannot transition backward (APPROVED → DRAFT, SENT → DRAFT) if any non-VOID PI references it. This prevents the scenario where a Quote is revised after a PI has been issued against it, creating inconsistency between the Quote and the PI that was based on it.

**PI VOID un-freezes the Quote:** If all PIs referencing a Quote are VOID, the Quote freeze is lifted (though other state transition rules may still prevent backward transitions).

### 4.3 Multiple PIs per Quote

A single Quote may have multiple PIs:

| Scenario | PI Relationship |
|----------|----------------|
| Revision | PI v1 → VOID, PI v2 issued with updated terms |
| Partial shipment | PI #1 for 60% of items, PI #2 for 40% |
| Amendment | Customer requests change after PI issued → VOID old PI, issue new PI |

Each PI is an independent record with its own `piNumber`, `quoteSnapshot`, and lifecycle. The Quote serves as the **master agreement**; PIs are **execution documents**.

### 4.4 Quote → PI Data Flow

```
Quote (ACCEPTED)
  │
  ├── Quote items (line items) ──► PI.quoteSnapshot (JSON)
  ├── Quote.currency ───────────► PI.currency
  ├── Quote.subtotal ───────────► PI.subtotal
  ├── Quote.taxAmount ──────────► PI.taxAmount
  ├── Quote.total ──────────────► PI.total
  └── Quote.quoteNumber ────────► (reference only, not a FK constraint)
```

The `quoteSnapshot` field on PI is a JSON object capturing the complete Quote state at issuance time:

```json
{
  "quoteId": "abc123",
  "quoteNumber": "QT-2026-0042",
  "capturedAt": "2026-07-21T14:30:00Z",
  "currency": "USD",
  "subtotal": 15000.00,
  "taxRate": 10.00,
  "taxAmount": 1500.00,
  "total": 16500.00,
  "items": [
    {
      "product": "PlateCycler-2000",
      "description": "Automated thermal cycler, 96-well",
      "quantity": 2,
      "unitPrice": 5000.00,
      "discount": 10.00,
      "lineTotal": 9000.00
    },
    {
      "product": "ResinTank-Pro",
      "description": "Large format resin tank, 5L",
      "quantity": 3,
      "unitPrice": 2000.00,
      "discount": 0,
      "lineTotal": 6000.00
    }
  ]
}
```

---

## 5. Approval Lifecycle — Extended

### 5.1 Current Design (Single-Level)

```
                    ┌──────────────┐
                    │   PENDING    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │ approve()              │ reject()
              ▼                        ▼
       ┌──────────────┐         ┌──────────────┐
       │   APPROVED   │         │   REJECTED   │
       └──────────────┘         └──────────────┘
```

### 5.2 Actor Mapping

| Approval Type | PENDING → APPROVED | PENDING → REJECTED |
|---------------|:------------------:|:------------------:|
| QUOTE | Manager | Manager |
| PI | Finance | Finance |

### 5.3 Cross-Entity Effect of Approval Decision

| Approval Entity | Decision | Effect on Parent Entity |
|-----------------|----------|------------------------|
| Quote | APPROVED | Quote transitions IN_REVIEW → APPROVED |
| Quote | REJECTED | Quote transitions IN_REVIEW → DRAFT (revision) |
| PI | APPROVED | PI transitions ISSUED → SENT (approval is the send gate) |
| PI | REJECTED | PI transitions ISSUED → DRAFT (revision) |

### 5.4 Multi-Level Approval — Extension Point (Future)

The current design is single-level. Multi-level approval (e.g., Manager → Director → Finance) is deferred to a post-C16 enhancement (ADR Q2). However, the data model is designed to accommodate it:

**Extension design (not implemented in C16):**

```
Approval record:
  approvalLevel: int (1, 2, 3...)
  parentApprovalId: link to previous Approval in chain
  status: PENDING, APPROVED, REJECTED, ESCALATED

Chain example:
  Approval #1: level=1, approver=Manager, status=APPROVED
  Approval #2: level=2, approver=Director, status=PENDING (auto-created after #1 APPROVED)
  Approval #3: level=3, approver=Finance, status=PENDING (auto-created after #2 APPROVED)
```

**C16.3 implements only level 1.** The `approvalLevel` field is included as an integer with default `1` to avoid a schema migration when multi-level is added. The Service layer in C16.3 ignores levels > 1.

### 5.5 Approval Re-Submission

If a Quote is rejected (IN_REVIEW → DRAFT) and later re-submitted (DRAFT → IN_REVIEW):
- A **new** Approval record is created with status PENDING.
- The old Approval (REJECTED) remains in history for audit.
- The new Approval is independent — it does not reference the old one (until multi-level approval is implemented).

---

## 6. State Transition Rules — Complete Tables

### 6.1 Quote Transition Table

| # | From | To | Trigger | Actor | Guards | Idempotent? |
|---|------|----|---------|-------|--------|:-----------:|
| T1 | (new) | DRAFT | `create()` | Sales, Manager, Admin | None | — |
| T2 | DRAFT | IN_REVIEW | `submitForReview()` | Sales, Manager | ≥1 QuoteItem; total > 0; `quoteNumber` assigned | ✅ (no-op if already IN_REVIEW) |
| T3 | IN_REVIEW | APPROVED | `approve()` | Manager | Approval.status = APPROVED; all required fields complete | ✅ (no-op if already APPROVED) |
| T4 | IN_REVIEW | DRAFT | `requestRevision()` | Manager | Revision reason required; no non-VOID PI exists for this Quote | — |
| T5 | APPROVED | SENT | `send()` | Sales, Manager | PDF generated and attached | ✅ (no-op if already SENT) |
| T6 | SENT | ACCEPTED | `accept()` | Sales, Manager | None | ✅ (no-op if already ACCEPTED) |
| T7 | SENT | REJECTED | `reject()` | Sales, Manager | Rejection reason required | ✅ (no-op if already REJECTED) |
| T8 | SENT | EXPIRED | `expire()` | System (cron), Admin | `validUntil < now()`; not already ACCEPTED/REJECTED | ✅ (no-op if already EXPIRED) |
| T9 | DRAFT | EXPIRED | `expire()` | System (cron), Admin | `validUntil < now()` | ✅ |
| T10 | APPROVED | EXPIRED | `expire()` | System (cron), Admin | `validUntil < now()` | ✅ |
| T11 | ACCEPTED | (any) | — | — | **No exit from terminal** | — |
| T12 | REJECTED | (any) | — | — | **No exit from terminal** | — |
| T13 | EXPIRED | (any) | — | — | **No exit from terminal** | — |

### 6.2 PI Workflow Transition Table

| # | From | To | Trigger | Actor | Guards | Idempotent? |
|---|------|----|---------|-------|--------|:-----------:|
| P1 | (new) | DRAFT | `create()` | Finance, Admin | Linked Quote is APPROVED, SENT, or ACCEPTED | — |
| P2 | DRAFT | ISSUED | `issue()` | Finance | All fields complete; `piNumber` assigned; `quoteSnapshot` captured | ✅ (no-op if already ISSUED) |
| P3 | ISSUED | SENT | `send()` | Sales, Finance | PDF generated and attached | ✅ (no-op if already SENT) |
| P4 | SENT | PAID | `markPaid()` | Finance | Payment confirmed; `paidAt` set | ✅ (no-op if already PAID) |
| P5 | * | VOID | `void()` | Finance, Admin | Void reason required; cannot un-void | ✅ (no-op if already VOID) |

**Note:** The original ADR had `SENT → PAID` as the payment transition and `VOID` as a separate terminal. The payment dimension is now independent (§3.3). This table reflects the **workflow** dimension only.

### 6.3 PI Payment Transition Table (Independent)

| # | From | To | Trigger | Actor | Guards |
|---|------|----|---------|-------|--------|
| PP1 | (new) | UNPAID | Auto | System | Default for all new PIs |
| PP2 | UNPAID | PARTIAL | `recordPayment(amount < total)` | Finance | Amount > 0; amount < remaining |
| PP3 | UNPAID | PAID | `recordPayment(amount = total)` | Finance | Amount = remaining |
| PP4 | PARTIAL | PARTIAL | `recordPayment(amount < remaining)` | Finance | Additional partial payment |
| PP5 | PARTIAL | PAID | `recordPayment(amount = remaining)` | Finance | Final payment |
| PP6 | UNPAID | OVERDUE | `checkOverdue()` | System (cron) | `paymentDueDate < now()`; paymentStatus ≠ PAID |
| PP7 | PARTIAL | OVERDUE | `checkOverdue()` | System (cron) | `paymentDueDate < now()`; paymentStatus ≠ PAID |
| PP8 | OVERDUE | PAID | `recordPayment(amount = remaining)` | Finance | Late full payment |
| PP9 | OVERDUE | PARTIAL | `recordPayment(amount < remaining)` | Finance | Late partial payment |

### 6.4 Approval Transition Table

| # | From | To | Trigger | Actor | Guards | Idempotent? |
|---|------|----|---------|-------|--------|:-----------:|
| A1 | (new) | PENDING | Auto (on Quote IN_REVIEW or PI ISSUED) | System | Parent entity is in correct state | — |
| A2 | PENDING | APPROVED | `approve()` | Manager (QUOTE), Finance (PI) | Actor has correct role for approvalType | ✅ (no-op if already APPROVED) |
| A3 | PENDING | REJECTED | `reject()` | Manager (QUOTE), Finance (PI) | Reason required; actor has correct role | ✅ (no-op if already REJECTED) |
| A4 | APPROVED | (any) | — | — | **No exit.** Create new Approval for re-approval. | — |
| A5 | REJECTED | (any) | — | — | **No exit.** Re-submission creates new Approval. | — |

### 6.5 Forbidden Transitions (Enforced in Service Layer)

| From | To | Reason Blocked |
|------|----|---------------|
| DRAFT | APPROVED | Must pass through IN_REVIEW |
| DRAFT | SENT | Must pass through IN_REVIEW → APPROVED |
| IN_REVIEW | SENT | Must pass through APPROVED |
| APPROVED | DRAFT | Approved Quotes are immutable; no backward transition |
| APPROVED | IN_REVIEW | Already approved; no re-review |
| SENT | DRAFT | Customer-facing document; cannot un-send |
| SENT | APPROVED | Already sent; cannot go backward |
| SENT | IN_REVIEW | Already sent; cannot go backward |
| ACCEPTED | * | Terminal state |
| REJECTED | * | Terminal state |
| EXPIRED | * | Terminal state |
| ISSUED | DRAFT (PI) | Issued PI cannot be un-issued; void instead |
| SENT | ISSUED (PI) | Sent PI cannot be un-sent; void instead |

---

## 7. Test Implications

### 7.1 State Transition Tests

For each entity, test that:
- Every valid transition in the transition tables (§6.1–6.4) succeeds.
- Every forbidden transition in §6.5 is rejected with an appropriate error.
- Idempotent transitions (marked ✅) are no-ops when the entity is already in the target state.
- Transitions called on an entity not in the required source state return an error.

**Test budget:** ~15 Quote, ~10 PI, ~8 Approval = ~33 transition tests.

### 7.2 Modification Rule Tests

For Quote modification rules (§2):
- DRAFT: all fields editable; line items can be added/removed
- IN_REVIEW: financial fields locked; line items locked; terms editable
- APPROVED: only notes editable
- SENT: only notes and status (accept/reject) modifiable
- Terminal states: no edits of any kind

**Test budget:** ~12 modification tests (2 per state × 6 non-terminal-adjacent states).

### 7.3 Permission Tests

Verify role-based access:
- Sales can submitForReview but not approve
- Manager can approve Quote but not PI
- Finance can issue PI but not approve Quote
- Admin can do everything
- System cron can expire but not approve/send

**Test budget:** ~10 permission tests.

### 7.4 Rollback Tests

Verify that:
- `IN_REVIEW → DRAFT` (revision) preserves line items
- After `APPROVED`, no backward transition works
- After `SENT`, no backward transition works
- VOID is terminal for PI
- Terminal states (ACCEPTED, REJECTED, EXPIRED, VOID) have no exits

**Test budget:** ~8 rollback tests.

### 7.5 Expiration Tests

Verify that:
- System cron correctly identifies Quotes with `validUntil < now()`
- DRAFT Quotes expire correctly
- APPROVED Quotes expire correctly (new path §1.4)
- SENT Quotes expire correctly
- Quotes already ACCEPTED/REJECTED/EXPIRED are not re-expired
- Expired Quote fields are unchanged (only status changes)

**Test budget:** ~6 expiration tests.

### 7.6 PI Workflow/Payment Separation Tests

Verify that:
- Workflow state and payment state are independent
- A PI can be SENT + UNPAID
- A PI can be SENT + PAID
- Payment state transitions don't affect workflow state
- Workflow state transitions don't affect payment state (except VOID freezes payment)

**Test budget:** ~8 separation tests.

### 7.7 Cross-Entity Consistency Tests

Verify that:
- Quote can only reach APPROVED if latest Approval is APPROVED
- Quote blocked from DRAFT if non-VOID PI exists
- PI can only be created from APPROVED/SENT/ACCEPTED Quote
- `quoteSnapshot` is immutable after PI issuance
- PI VOID un-freezes the Quote

**Test budget:** ~8 cross-entity tests.

### 7.8 Total State Machine Test Budget

| Category | Tests |
|----------|:-----:|
| State transitions (§7.1) | 33 |
| Modification rules (§7.2) | 12 |
| Permissions (§7.3) | 10 |
| Rollback (§7.4) | 8 |
| Expiration (§7.5) | 6 |
| PI workflow/payment separation (§7.6) | 8 |
| Cross-entity consistency (§7.7) | 8 |
| **Total** | **85** |

These tests are distributed across C16.2, C16.3, and C16.5, with cross-entity tests concentrated in C16.6.

---

## Appendix A: Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| S1 | APPROVED → EXPIRED is a valid transition | Approved-but-unsent Quotes should not remain in APPROVED indefinitely | 2026-07-21 |
| S2 | IN_REVIEW locks line items and financial fields | Reviewer must review a stable Quote; changing terms mid-review subverts approval | 2026-07-21 |
| S3 | PI workflow state and payment state are separate dimensions | Different actors, timelines, and transition independence | 2026-07-21 |
| S4 | PI payment state uses a summary `paymentStatus` field in C16.5; `Payment` entity deferred | Simpler C16.5 scope; individual payment tracking is a post-C16 enhancement | 2026-07-21 |
| S5 | Quote freeze on PI issuance (no backward Quote transitions if non-VOID PI exists) | Prevents Quote-PI inconsistency after PI is issued | 2026-07-21 |
| S6 | `approvalLevel` field included from C16.1 with default 1 | Schema-ready for multi-level approval without migration; logic deferred | 2026-07-21 |
| S7 | SENT Quotes are customer-facing immutable; changes require a new Quote | Protects customer-facing document integrity | 2026-07-21 |
| S8 | Re-submission after rejection creates a new Approval record | Audit trail; old rejections are historical records | 2026-07-21 |

## Appendix B: Unresolved Questions

| # | Question | Status | Target |
|---|----------|--------|--------|
| S-Q1 | Should `EXPIRED` Quotes be auto-cloned as new DRAFT Quotes? | Deferred; the "Re-quote" pattern is a UI action, not an automated behavior | Post-C16 |
| S-Q2 | Should PI `paymentDueDate` default to Quote `validUntil` + N days? | PI `paymentDueDate` is an independent field set by Finance; no auto-derivation | C16.5 |
| S-Q3 | Should `approvalLevel` be validated in C16.3 even if multi-level logic is deferred? | Yes — validate that `approvalLevel` = 1 in C16.3; reject levels > 1 until multi-level is implemented | C16.3 |
| S-Q4 | Should the system auto-transition Quote to EXPIRED or send a warning before `validUntil`? | System cron expires exactly at `validUntil < now()`. Warning notification (e.g., 7 days before) is a post-C16 enhancement | C16.2 for expiration; post-C16 for warning |

## Appendix C: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) §4 — Original state machine design
- [ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md](ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md) — Number assignment timing (triggers state-dependent numbering)
- [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md) §5 — Test strategy
- [BOUNDARIES.md](BOUNDARIES.md) — System boundary enforcement

---

*End of ADR. State machine design frozen. Implementation deferred to C16.2–C16.6.*
