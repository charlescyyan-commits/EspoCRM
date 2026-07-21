# ADR: C16 State Machine Addendum — PI State Reconciliation

**Status:** Accepted — Canonical Reference  
**Date:** 2026-07-21  
**Phase:** Phase3C16.1C-1 — ADR Alignment Remediation  
**Supersedes:** ADR_C16_QUOTE_PI_ARCHITECTURE.md §4.2 (PI state model), C16_IMPLEMENTATION_PREPARATION.md §1.4 (PI status enum)  
**References:** [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md), [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md), [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md)

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Conflict Identification](#2-conflict-identification)
3. [Canonical PI State Model](#3-canonical-pi-state-model)
4. [Quote State Machine — Unchanged](#4-quote-state-machine--unchanged)
5. [Approval State Machine — Unchanged](#5-approval-state-machine--unchanged)
6. [Superseded Sections](#6-superseded-sections)
7. [Decision Log](#7-decision-log)

---

## 1. Purpose

### 1.1 Why This Addendum Exists

During the Phase3C16.1C-1 ADR alignment audit, a conflict was identified: multiple ADR documents describe the ProformaInvoice (PI) state machine inconsistently. The base ADR ([ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) §4.2) conflates workflow and payment into a single state enum. The extensions ADR ([ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) §3) correctly separates them into independent dimensions but does not explicitly declare itself as the canonical reference.

This addendum **resolves the conflict** by declaring the canonical PI state model and explicitly marking the superseded sections.

### 1.2 What This Addendum Does NOT Change

- **Quote state machine** — unchanged; consistent across all ADRs
- **Approval state machine** — unchanged; consistent across all ADRs
- **Quote/PI relationship rules** — unchanged
- **Quote modification rules** — unchanged
- **Any entity definitions, metadata, or code** — this is a documentation-only reconciliation

---

## 2. Conflict Identification

### 2.1 Conflicting Documents

| Document | Section | PI States Listed | Problem |
|----------|---------|-----------------|---------|
| ADR_C16_QUOTE_PI_ARCHITECTURE.md | §4.2 | `DRAFT`, `ISSUED`, `SENT`, `PAID`, `VOID` | Conflates workflow and payment into a single enum; treats `PAID` as a state-machine state rather than a payment dimension |
| C16_IMPLEMENTATION_PREPARATION.md | §1.4 | `DRAFT`, `ISSUED`, `SENT`, `PAID`, `VOID` | Follows the base ADR's conflated model; `status` enum contains payment state |
| ADR_C16_STATE_MACHINE_EXTENSIONS.md | §3.2, §3.3 | Workflow: `DRAFT`, `ISSUED`, `SENT`, `VOID`<br>Payment: `UNPAID`, `PARTIAL`, `PAID`, `OVERDUE` | **Correct model** — separates workflow from payment |

### 2.2 Root Cause

The base ADR was written as an initial design freeze before the full implications of PI lifecycle management were understood. The extensions ADR refined the design by recognizing that workflow progression (draft → issue → send → void) and payment status (unpaid → partial → paid → overdue) are **orthogonal concerns** with different actors, timelines, and transition rules. The implementation preparation document was not updated to reflect this refinement.

### 2.3 Impact of the Conflict

If left unresolved, implementers referencing the base ADR or implementation preparation document would:
- Model `PAID` as a workflow state, creating ambiguity about whether a SENT+PAID PI is in two states simultaneously
- Be unable to represent a SENT+UNPAID PI (the normal state after sending but before payment)
- Have no mechanism for partial payments or overdue tracking
- Need a schema migration later to separate the dimensions

---

## 3. Canonical PI State Model

### 3.1 Design Principle: Separate Workflow from Payment

A Proforma Invoice has **two independent dimensions**:

| Dimension | Field | Purpose | Owner |
|-----------|-------|---------|-------|
| **Workflow state** | `status` | Where the PI is in the issuance/send/void lifecycle | Finance |
| **Payment state** | `paymentStatus` | Whether the PI has been paid, and how much | Finance + System (OVERDUE cron) |

**Each dimension operates independently.** A PI's workflow state does not constrain its payment state (except VOID, which freezes payment updates). A PI's payment state does not drive workflow transitions.

### 3.2 Workflow State Machine

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

**Workflow States (canonical):**

| State | Meaning | Payment Field Access |
|-------|---------|:--------------------:|
| **DRAFT** | Internal working document. Not yet issued. No `piNumber` assigned. | ✅ Full access |
| **ISSUED** | Formally issued with `piNumber`. Financial snapshot frozen in `quoteSnapshot`. | ✅ Full access |
| **SENT** | Delivered to customer. Awaiting payment. PDF generated. | ✅ Full access |
| **VOID** | Cancelled. Terminal workflow state. | ❌ Frozen at last value |

### 3.3 Payment State Machine

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

**Payment States (canonical):**

| State | Meaning | Trigger |
|-------|---------|---------|
| **UNPAID** | No payment received. Default for all new PIs. | Initial state |
| **PARTIAL** | Some but not all of the total has been paid. | Manual (Finance records a partial payment) |
| **PAID** | Full amount received. Terminal payment state. | Manual (Finance confirms full payment) |
| **OVERDUE** | Payment due date passed without full payment. | System cron or manual |

### 3.4 Valid Workflow × Payment Combinations

Not all 4 × 4 = 16 combinations are semantically valid:

| Workflow ↓ / Payment → | UNPAID | PARTIAL | PAID | OVERDUE |
|------------------------|:------:|:-------:|:----:|:-------:|
| **DRAFT** | ✅ | ❌ | ❌ | ❌ |
| **ISSUED** | ✅ | ⚠️ Rare | ⚠️ Rare | ✅ |
| **SENT** | ✅ Normal | ✅ | ✅ | ✅ |
| **VOID** | ✅ | ✅ (frozen) | ✅ (frozen) | ✅ (frozen) |

- **DRAFT + anything but UNPAID:** A PI that hasn't been issued should not have payment activity. Payment status is set to UNPAID on create and should not change until ISSUED.
- **ISSUED + PARTIAL/PAID:** Unusual but possible — a customer might pay before the PI is formally sent (e.g., based on a Quote or verbal agreement). The system permits it but flags it for review.
- **VOID + any payment state:** The payment status is frozen at whatever it was when the PI was voided. This preserves the audit trail.

### 3.5 Transition Rules — Workflow

| # | From | To | Trigger | Actor | Guards |
|---|------|----|---------|-------|--------|
| W1 | (new) | DRAFT | `create()` | Finance, Admin | Linked Quote is APPROVED, SENT, or ACCEPTED |
| W2 | DRAFT | ISSUED | `issue()` | Finance | All fields complete; `piNumber` assigned; `quoteSnapshot` captured |
| W3 | ISSUED | SENT | `send()` | Sales, Finance | PDF generated and attached |
| W4 | DRAFT | VOID | `void()` | Finance, Admin | Void reason required |
| W5 | ISSUED | VOID | `void()` | Finance, Admin | Void reason required |
| W6 | SENT | VOID | `void()` | Finance, Admin | Void reason required |

**Idempotency:** All workflow transitions are no-ops if the PI is already in the target state.

### 3.6 Transition Rules — Payment

| # | From | To | Trigger | Actor | Guards |
|---|------|----|---------|-------|--------|
| P1 | (new) | UNPAID | Auto | System | Default for all new PIs |
| P2 | UNPAID | PARTIAL | `recordPayment(amount < total)` | Finance | Amount > 0; amount < remaining |
| P3 | UNPAID | PAID | `recordPayment(amount = total)` | Finance | Amount = remaining |
| P4 | PARTIAL | PARTIAL | `recordPayment(amount < remaining)` | Finance | Additional partial payment |
| P5 | PARTIAL | PAID | `recordPayment(amount = remaining)` | Finance | Final payment |
| P6 | UNPAID | OVERDUE | `checkOverdue()` | System (cron) | `paymentDueDate < now()` |
| P7 | PARTIAL | OVERDUE | `checkOverdue()` | System (cron) | `paymentDueDate < now()` |
| P8 | OVERDUE | PAID | `recordPayment(amount = remaining)` | Finance | Late full payment |
| P9 | OVERDUE | PARTIAL | `recordPayment(amount < remaining)` | Finance | Late partial payment; payment status returns to PARTIAL |

**Freeze rule:** All payment transitions are blocked when the PI workflow state is VOID. Payment status is frozen at the last value before voiding.

### 3.7 Field Design Summary

```
ProformaInvoice
├── status: enum (DRAFT, ISSUED, SENT, VOID)         ← Workflow dimension
├── paymentStatus: enum (UNPAID, PARTIAL, PAID, OVERDUE)  ← Payment dimension
├── paymentDueDate: date                                   ← For OVERDUE cron
├── paidAmount: currency                                   ← Running total of payments received
└── payments: hasMany Payment (future entity — post-C16)   ← Individual payment records
```

**C16.5 scope:** `paymentStatus`, `paymentDueDate`, and `paidAmount` are implemented as fields on ProformaInvoice. The `Payment` entity for tracking individual payments is deferred to a post-C16 enhancement. `paymentStatus` is updated manually by Finance (recording a payment) or automatically by system cron (marking OVERDUE).

---

## 4. Quote State Machine — Unchanged

The Quote state machine is **consistent across all ADRs** and requires no reconciliation:

**States:** `DRAFT`, `IN_REVIEW`, `APPROVED`, `SENT`, `ACCEPTED`, `REJECTED`, `EXPIRED`

All three documents agree on:
- States and their semantics
- Valid transitions (including the `APPROVED → EXPIRED` path added by the extensions ADR)
- Modification rules by state
- Idempotency guarantees
- Terminal state immutability

**Canonical reference for Quote state machine:** [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) §1–2 (extends [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) §4.1).

---

## 5. Approval State Machine — Unchanged

The Approval state machine is **consistent across all ADRs** and requires no reconciliation:

**States:** `PENDING`, `APPROVED`, `REJECTED`

All three documents agree on:
- States and their semantics
- Valid transitions
- Role-based actor mapping (Manager for QUOTE, Finance for PI)
- No exit from APPROVED or REJECTED
- Re-submission creates a new Approval record

**Canonical reference for Approval state machine:** [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) §5 (extends [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) §4.3).

---

## 6. Superseded Sections

The following sections of older ADRs are **superseded** by this addendum and [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) §3:

### 6.1 ADR_C16_QUOTE_PI_ARCHITECTURE.md §4.2 — ProformaInvoice State Machine

**Superseded content:** The PI state diagram and transition table in §4.2 of the base ADR, which defines PI states as `DRAFT`, `ISSUED`, `SENT`, `PAID`, `VOID`.

**Why superseded:** This model embeds `PAID` as a workflow state, conflating the workflow dimension (issuance/send lifecycle) with the payment dimension (payment receipt status). The canonical model separates these into `status` (DRAFT, ISSUED, SENT, VOID) and `paymentStatus` (UNPAID, PARTIAL, PAID, OVERDUE).

**What remains valid from §4.2:**
- PI general constraints (`piNumber` uniqueness, multiple PIs per Quote)
- Rollback policy principles (SENT immutability, VOID terminality)
- Idempotency rules (adapted to the separated model)
- Cross-entity consistency rules (§4.4)

### 6.2 ADR_C16_QUOTE_PI_ARCHITECTURE.md §4.2 — Transition Table

**Superseded content:** Transition P4 (`SENT → PAID` via `markPaid()`). In the canonical model, payment is not a workflow transition. `markPaid()` sets `paymentStatus = PAID` and `paidAt` but does not change `status`.

**Replacement:** See §3.6 of this addendum for payment state transitions.

### 6.3 C16_IMPLEMENTATION_PREPARATION.md §1.4 — PI Status Enum

**Superseded content:** The `status` field definition in §1.4 listing options as `DRAFT, ISSUED, SENT, PAID, VOID`.

**Why superseded:** `PAID` is removed from the workflow `status` enum and placed in the separate `paymentStatus` field.

**Corrected field definitions for ProformaInvoice:**

| Field | Type | Values |
|-------|------|--------|
| `status` | enum | `DRAFT`, `ISSUED`, `SENT`, `VOID` |
| `paymentStatus` | enum | `UNPAID`, `PARTIAL`, `PAID`, `OVERDUE` |

**What remains valid from §1.4:**
- All other PI field mappings (currency, subtotal, taxAmount, total, paymentTerms, shippingTerms, timestamps, notes, quoteSnapshot, PDF fields)
- Display styles for `status` (minus the `PAID` entry, which moves to `paymentStatus`)
- Relationship mapping (§1.6)

### 6.4 Non-Superseded Content

The following remain fully authoritative and are not modified:

- **ADR_C16_QUOTE_PI_ARCHITECTURE.md** §4.1 (Quote state machine), §4.3 (Approval state machine), §4.4 (cross-entity consistency), all other sections
- **ADR_C16_STATE_MACHINE_EXTENSIONS.md** §1–2 (Quote lifecycle extended), §3 (PI lifecycle — **this is canonical**), §4 (Quote/PI relationship), §5 (Approval lifecycle extended), §6–7 (transition tables, test implications)
- **C16_IMPLEMENTATION_PREPARATION.md** all sections except §1.4 `status` enum values

---

## 7. Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| R1 | PI workflow and payment are separate dimensions | Different actors, timelines, and transition independence; conflating them forces false coupling and prevents normal states like SENT+UNPAID | 2026-07-21 |
| R2 | Canonical PI workflow states: DRAFT, ISSUED, SENT, VOID | Matches ADR_C16_STATE_MACHINE_EXTENSIONS.md §3.2; `PAID` is not a workflow state | 2026-07-21 |
| R3 | Canonical PI payment states: UNPAID, PARTIAL, PAID, OVERDUE | Matches ADR_C16_STATE_MACHINE_EXTENSIONS.md §3.3; payment is tracked independently of workflow | 2026-07-21 |
| R4 | ADR_C16_STATE_MACHINE_EXTENSIONS.md §3 is the canonical PI reference | It was the first document to correctly separate workflow from payment; the base ADR and implementation prep doc were written before this refinement | 2026-07-21 |
| R5 | Base ADR §4.2 and implementation prep §1.4 PI status enum are superseded | These sections contain the conflated model; this addendum formally marks them as superseded to prevent implementers from following the outdated design | 2026-07-21 |
| R6 | Superseded sections are marked, not deleted | Historical ADRs are preserved intact for traceability; this addendum is the single reconciliation point | 2026-07-21 |
| R7 | Quote and Approval state machines require no reconciliation | Consistent across all three ADR documents; no changes needed | 2026-07-21 |

---

## Appendix A: Quick Reference — All C16 State Machines (Canonical)

### Quote States

```
DRAFT → IN_REVIEW → APPROVED → SENT → ACCEPTED
                    ↓            ↓  → REJECTED
                    DRAFT         ↓  → EXPIRED
                    (revision)    ↓
                              EXPIRED (from APPROVED, never sent)
```

### PI Workflow States

```
DRAFT → ISSUED → SENT
  ↓        ↓        ↓
  └────────┴────────┴──→ VOID (from any non-terminal)
```

### PI Payment States

```
UNPAID → PARTIAL → PAID
   ↓         ↓        ↑
   └─────────┴──→ OVERDUE → PAID
                     ↓
                  PARTIAL
```

### Approval States

```
PENDING → APPROVED
       → REJECTED
```

---

## Appendix B: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) — Base architecture (PI state model in §4.2 superseded by this addendum)
- [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) — Extended state machines (PI §3 is canonical reference)
- [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md) — Implementation prep (PI status enum in §1.4 superseded by this addendum)
- [BOUNDARIES.md](BOUNDARIES.md) — System boundaries
- [PHASE3C16_1A_METADATA_AUDIT.md](../PHASE3C16_1A_METADATA_AUDIT.md) — C16.1A metadata audit

---

*End of Addendum. This document is the single reconciliation point for PI state machine conflicts. For implementation, refer to this addendum and ADR_C16_STATE_MACHINE_EXTENSIONS.md §3 as the canonical PI state references.*
