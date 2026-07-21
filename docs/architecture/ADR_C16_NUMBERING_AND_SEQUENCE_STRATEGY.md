# ADR: C16 Numbering and Sequence Strategy

**Status:** Accepted — Design Freeze  
**Date:** 2026-07-21  
**Phase:** Phase3C16 Architecture Refinement  
**Supersedes:** ADR_C16_QUOTE_PI_ARCHITECTURE.md §7 (refines, does not replace)  
**References:** [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md), [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md)

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Number Format Decision](#2-number-format-decision)
3. [Number Assignment Timing](#3-number-assignment-timing)
4. [Sequence Ownership](#4-sequence-ownership)
5. [Concurrency Strategy](#5-concurrency-strategy)
6. [Failure and Recovery](#6-failure-and-recovery)
7. [Implementation Boundary](#7-implementation-boundary)

---

## 1. Problem Statement

### 1.1 Why Stable Numbering Matters

Quote and ProformaInvoice numbers serve as **external business identifiers**. They appear on customer-facing documents (PDFs, emails, invoices) and are referenced in external communication, accounting systems, and audit trails. Unstable or duplicated numbers cause:

| Risk | Impact |
|------|--------|
| **Duplicate numbers** | Two customers receive documents with the same identifier; legal/accounting liability |
| **Number gaps from abandoned drafts** | Wasted sequence numbers if assigned at entity creation; confusing to auditors |
| **Concurrent assignment collision** | Two users creating Quotes simultaneously get the same number under race conditions |
| **Data recovery inconsistency** | Restored backups may re-assign already-used numbers |

### 1.2 Non-Goals

This ADR does not cover:
- Invoice numbering for final/commercial invoices (only Proforma Invoice)
- Purchase Order numbering
- External system integration numbering (ERP sync — deferred)
- PDF filename convention (covered by ADR_C16 §5–6)

---

## 2. Number Format Decision

### 2.1 Quote Number Format

```
QT-YYYY-NNNN
│   │    │
│   │    └── Sequential number: 4 digits, zero-padded, annual reset
│   └─────── Year of number assignment: 4 digits
└─────────── Fixed prefix: "QT" (Quote)
```

**Examples:**
| Number | Meaning |
|--------|---------|
| `QT-2026-0001` | First Quote of 2026 |
| `QT-2026-0142` | 142nd Quote of 2026 |
| `QT-2027-0001` | First Quote of 2027 (counter reset) |

**Rules:**
- Prefix: Immutable. Always `QT`.
- Year component: Derived from the server clock at assignment time (not creation time, not validUntil).
- Sequence component: 4 digits, zero-padded. Range 0001–9999 per year.
- At 9999: Roll over to 0001 within the same year is **NOT allowed**. The system must explicitly refuse to assign numbers beyond 9999 per year. If the limit is approached, the prefix or digit count must be extended via a schema migration before reaching 9999.

### 2.2 ProformaInvoice Number Format

```
PI-YYYY-NNNN
│   │    │
│   │    └── Sequential number: 4 digits, zero-padded, annual reset
│   └─────── Year of number assignment: 4 digits
└─────────── Fixed prefix: "PI" (Proforma Invoice)
```

**Examples:**
| Number | Meaning |
|--------|---------|
| `PI-2026-0001` | First PI of 2026 |
| `PI-2026-0089` | 89th PI of 2026 |

**Rules:**
- Prefix: Immutable. Always `PI`.
- Quote and PI sequences are **independent**. `QT-2026-0001` and `PI-2026-0001` may both exist without conflict.
- Same 4-digit, annual-reset rule as Quote numbering.

### 2.3 Extensibility

| Scenario | Approach |
|----------|----------|
| Exceed 9999 in a year | Schema migration to increase digit count (e.g., 5 digits). Trigger: monitoring alert at 9000 |
| Need sub-types (e.g., Credit Note) | New prefix (e.g., `CN-YYYY-NNNN`) with independent sequence |
| Multi-tenant deployment | Prefix includes tenant code: `QT-{TENANT}-YYYY-NNNN` (future; not in C16) |
| Fiscal year vs. calendar year | Calendar year is the default. Fiscal year alignment is a post-C16 configuration option |

---

## 3. Number Assignment Timing

### 3.1 Options Evaluated

| Option | Assignment Point | Pros | Cons |
|--------|-----------------|------|------|
| **A: Create** | When the entity record is first saved | Simplest implementation; number always exists | Wastes numbers on abandoned drafts; every incomplete Quote consumes a number |
| **B: Review transition** | When Quote transitions DRAFT → IN_REVIEW | Drafts don't consume numbers; number exists before approval | Quote must survive review to be useful |
| **C: Approval transition** | When Quote transitions IN_REVIEW → APPROVED | Only approved Quotes consume numbers | Quote has no stable identifier during review; approver can't reference by number |
| **D: Issue transition** | When PI transitions DRAFT → ISSUED | Only issued PIs consume numbers | PI has no identifier during drafting |

### 3.2 Decision

| Entity | Assignment Point | Rationale |
|--------|-----------------|-----------|
| **Quote** | DRAFT → IN_REVIEW (Option B) | Quote needs a stable identifier during the review process. Reviewers reference Quotes by number. The transition from DRAFT to IN_REVIEW represents a **serious intent** to send — the user has committed line items and clicked "Submit for Review." Drafts that never leave DRAFT are true abandonments and should not consume numbers. |
| **ProformaInvoice** | DRAFT → ISSUED (Option D) | PI is a financial document. Issuance is the point of financial commitment. A PI in DRAFT is an internal working document; assigning a number at ISSUED ensures the PI number has financial significance. |

### 3.3 Explicitly Rejected

| Timing | Reason for Rejection |
|--------|---------------------|
| **On Create (Option A)** | Wastes numbers. A user creating 5 draft Quotes to compare options would consume 5 numbers even if only 1 is ever submitted. This is unacceptable for audit-quality numbering. |
| **On Approval (Option C) for Quote** | Reviewer needs a number to reference the Quote during review. "Please review the Quote for Acme Corp" is ambiguous; "Please review QT-2026-0042" is precise. |

### 3.4 Number Immutability After Assignment

Once a `quoteNumber` or `piNumber` is assigned, it is **immutable for the lifetime of the entity record**. Even if the Quote is rejected back to DRAFT, the number persists. If the Quote is deleted (soft delete), the number is **not recycled**.

---

## 4. Sequence Ownership

### 4.1 Ownership Declaration

**CRM Extension owns all C16 numbering.** This is non-negotiable.

| Component | Role |
|-----------|------|
| **CRM Extension** (`QuoteNumberingService`, `PINumberingService`) | Generates, assigns, and validates all C16 numbers |
| **Connector** | Never generates C16 numbers |
| **Document Service** | Never generates C16 numbers; receives numbers as data |
| **Frontend (JavaScript)** | Never generates C16 numbers; displays numbers received from the server |
| **External ERP/accounting system** | Consumes numbers as references; never generates them |

### 4.2 Rationale

1. **Single source of truth** — The CRM database is the system of record for Quote and PI data. Numbering must originate from the same source.
2. **Atomicity** — Number assignment is coupled to the state transition (DRAFT → IN_REVIEW) within the same database transaction. An external service cannot guarantee this atomicity.
3. **Concurrency** — Only the CRM database can provide the transactional guarantees needed for unique, gap-tolerant sequential numbering (see §5).
4. **Consistency with existing patterns** — C10, C11, and C14 all follow the same rule: CRM owns record identity, Connector owns transport.

### 4.3 Explicitly Forbidden

- ❌ Connector generating `QT-*` or `PI-*` numbers
- ❌ Frontend generating numbers client-side (race condition between two browser tabs)
- ❌ Document Service assigning numbers
- ❌ External API generating numbers

---

## 5. Concurrency Strategy

### 5.1 Problem Illustration

Two users (Alice and Bob) simultaneously submit Quotes for review at 2026-07-21T14:30:00.500:

```
Alice: POST /Quote/{idA}/submitForReview  → needs QT-2026-0042
Bob:   POST /Quote/{idB}/submitForReview  → needs QT-2026-0043
```

Without concurrency control, both transactions could read `current_value = 41` and both assign `QT-2026-0042`.

### 5.2 Options Evaluated

| Option | Mechanism | Uniqueness | Gap Tolerance | Complexity | EspoCRM Compatibility |
|--------|-----------|:----------:|:------------:|:----------:|:---------------------:|
| **A: Database transaction lock** | `SELECT ... FOR UPDATE` on a sequence row within the Quote save transaction | ✅ Guaranteed | ✅ Natural gaps | MEDIUM | ⚠️ Requires raw SQL in EspoCRM's ORM |
| **B: Dedicated sequence table** | `UPDATE number_seq SET val = LAST_INSERT_ID(val+1) WHERE key='QUOTE-2026'` | ✅ Guaranteed | ✅ Natural gaps | LOW | ✅ Pure SQL; no ORM dependency |
| **C: Counter entity** | EspoCRM entity with a single `currentValue` field; increment via `EntityManager` | ⚠️ Race-prone without `FOR UPDATE` | ✅ Natural gaps | LOW (ORM) | ✅ Native EspoCRM entity |
| **D: UUID + mapping** | Generate UUID, map to a sequential number asynchronously | ✅ UUID is unique | ❌ Gap-free (bad) | HIGH | ✅ No concurrency issue |

### 5.3 Decision: Option B — Dedicated Sequence Table

**Recommended approach:** A dedicated `numbering_sequence` table managed via atomic `UPDATE ... LAST_INSERT_ID()`.

**Implementation:**

```sql
-- Schema (created during C16.1 entity installation)
CREATE TABLE numbering_sequence (
    sequence_key VARCHAR(64) NOT NULL PRIMARY KEY,
    current_value INT UNSIGNED NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Atomic fetch-and-increment (single statement, no SELECT FOR UPDATE needed)
UPDATE numbering_sequence
SET current_value = LAST_INSERT_ID(current_value + 1)
WHERE sequence_key = 'QUOTE-2026';

-- Retrieve the assigned value (MySQL session variable)
SELECT LAST_INSERT_ID();  -- returns 42 (for the next QT-2026-0042)
```

**Why this approach wins:**

1. **Single atomic statement** — `UPDATE ... LAST_INSERT_ID(current_value + 1)` is a single atomic operation. Even with `READ COMMITTED` isolation, MySQL serializes writes to the same row. No `SELECT ... FOR UPDATE` or explicit locking required.
2. **Gap tolerance** — If the transaction that consumed value 42 rolls back, value 42 is lost. The next caller gets 43. This is **intentional and acceptable** — sequential numbering with gaps is standard in accounting (invoice numbers routinely have gaps from voided documents).
3. **No ORM dependency** — The sequence table is accessed via raw PDO within the Service layer. It does not require an EspoCRM entity definition, layouts, ACL, or UI.
4. **Annual reset** — The sequence key includes the year (`QUOTE-2026`, `QUOTE-2027`). On January 1st of a new year, the first `UPDATE` on `QUOTE-2027` auto-creates the row (or the Service ensures it exists via `INSERT IGNORE ... VALUES ('QUOTE-2027', 0)` before the first assignment).

### 5.4 Rejected Alternatives

| Option | Rejection Reason |
|--------|-----------------|
| **A: SELECT FOR UPDATE** | Unnecessarily complex. `LAST_INSERT_ID` achieves the same guarantee with a single statement. `SELECT FOR UPDATE` also requires explicit transaction management that EspoCRM's ORM may not expose cleanly. |
| **C: Counter entity** | Race condition. EspoCRM's `EntityManager::saveEntity()` performs a read-then-write. Two concurrent saves would both read the same current value and both write `value + 1`, producing duplicates. This is a classic lost-update problem that only row-level locking (not available through EspoCRM's ORM without raw SQL) can prevent. |
| **D: UUID + mapping** | Over-engineered. UUIDs are not human-readable and cannot serve as external business identifiers. An async mapping layer adds complexity with no benefit for a system that never exceeds 9999 documents per year. |

### 5.5 Sequence Initialization

On the first Quote/PI of a new year, the sequence row for that year must exist:

```php
// In QuoteNumberingService::getNextNumber()
$sequenceKey = 'QUOTE-' . date('Y');
$pdo->exec("INSERT IGNORE INTO numbering_sequence (sequence_key, current_value) VALUES ('$sequenceKey', 0)");
$pdo->exec("UPDATE numbering_sequence SET current_value = LAST_INSERT_ID(current_value + 1) WHERE sequence_key = '$sequenceKey'");
$nextValue = $pdo->query("SELECT LAST_INSERT_ID()")->fetchColumn();
return sprintf('QT-%s-%04d', date('Y'), $nextValue);
```

### 5.6 Multi-Instance Deployment

If the CRM is deployed behind a load balancer with multiple PHP-FPM instances, MySQL's built-in row-level locking on the `UPDATE` statement handles concurrency. No application-level distributed lock (Redis, file lock) is required. MySQL's InnoDB engine serializes writes to the same row at the storage-engine level.

---

## 6. Failure and Recovery

### 6.1 Scenario: Number Generated, Entity Save Failed

```
Sequence: UPDATE numbering_sequence → value = 42 (consumed)
Quote:    Save entity → FAILS (validation error, DB timeout, etc.)
Transaction: ROLLBACK
Result:   value 42 is consumed but not assigned to any Quote
```

**Policy: Gaps are permitted. No number recycling.**

Rationale:
- **Audit integrity** — A gap in the sequence indicates that *something happened* at that point in time (a failed save, a rolled-back transaction, a manual deletion). This is valuable audit metadata.
- **Simplicity** — Recycling numbers requires a compensation mechanism (re-insert the number into the sequence) that itself can fail, creating more complex failure modes.
- **Industry practice** — Accounting standards explicitly allow gaps in invoice/quote numbering. Voided or failed documents leave permanent gaps.

### 6.2 Scenario: Transaction Rollback

If the entire transaction (sequence increment + entity save) rolls back due to a database error:

- The sequence value is **not** rolled back (the `UPDATE` was committed before the rollback, or it was part of the same transaction and rolled back depending on implementation)
- **Implementation choice:** The sequence increment and entity save must be in the **same database transaction**. If the entity save fails and the transaction rolls back, the sequence increment also rolls back. This preserves value 42 for the next caller.
- **Caveat:** This requires EspoCRM's `EntityManager` to support transactional boundaries. If EspoCRM auto-commits after each `saveEntity()`, then the sequence increment must happen *after* the entity save succeeds, not before. See §6.4.

### 6.3 Scenario: Database Restore from Backup

If the CRM database is restored from a backup taken at 2026-07-20, and Quotes `QT-2026-0040` through `QT-2026-0045` were created after the backup:

- After restore, the `numbering_sequence` table for `QUOTE-2026` shows `current_value = 39`.
- The next assigned number will be `QT-2026-0040`, which was previously assigned to an existing Quote.
- **Policy: Manual intervention required.** After a database restore, an administrator must manually update the `numbering_sequence.current_value` to match the highest assigned number in the `quote` table:
  ```sql
  UPDATE numbering_sequence ns
  SET ns.current_value = (
      SELECT MAX(CAST(SUBSTRING_INDEX(q.quote_number, '-', -1) AS UNSIGNED))
      FROM quote q
      WHERE q.quote_number LIKE CONCAT('QT-', YEAR(CURDATE()), '-%')
        AND q.deleted = 0
  )
  WHERE ns.sequence_key = CONCAT('QUOTE-', YEAR(CURDATE()));
  ```
- This is a documented operational procedure, not an automated behavior.

### 6.4 Implementation Order Guarantee

To ensure the sequence increment is not lost on entity save failure:

```
Recommended order (within one transaction):
1. Validate entity (all guards pass)
2. Execute state transition
3. Save entity → if this fails, ROLLBACK everything including sequence
4. Increment sequence (UPDATE numbering_sequence)
5. Assign number to entity
6. Save entity again (update quoteNumber field)
7. COMMIT

Alternative order (if EspoCRM auto-commits step 3):
1. Validate entity
2. Execute state transition
3. Save entity (auto-committed by EspoCRM)
4. Increment sequence (separate transaction)
5. Assign number to entity
6. Save entity again (separate transaction)
   → Risk: Sequence incremented but step 6 fails → gap created
   → Mitigation: Gap tolerance policy (see §6.1)
```

**Decision:** Use the recommended order if EspoCRM's `EntityManager` supports transactional save. If not, use the alternative order with documented gap tolerance.

---

## 7. Implementation Boundary

### 7.1 What C16.1 Does NOT Implement

C16.1 (Entity Foundation) creates only entity metadata — no business logic. Specifically:

| Component | Status in C16.1 |
|-----------|----------------|
| `QuoteNumberingService.php` | **Not created** |
| `PINumberingService.php` | **Not created** |
| `numbering_sequence` table | **Not created** |
| Number assignment logic | **Not implemented** |
| Concurrency handling | **Not implemented** |

### 7.2 What C16.1 Defines

C16.1 defines only:
- The `quoteNumber` field on the Quote entity (type: `varchar(32)`, unique index with soft-delete)
- The `piNumber` field on the ProformaInvoice entity (type: `varchar(32)`, unique index with soft-delete)

These fields exist but are nullable and not auto-populated until C16.2 (QuoteWorkflow) and C16.5 (PI Workflow) implement the numbering services.

### 7.3 Implementation Order Across Phases

| Phase | Numbering Implementation |
|-------|------------------------|
| C16.1 | Fields defined (`quoteNumber`, `piNumber`); indexes created; no assignment logic |
| C16.2 | `QuoteNumberingService` implemented; `numbering_sequence` table created; Quote number assigned on DRAFT → IN_REVIEW |
| C16.5 | `PINumberingService` implemented; PI number assigned on DRAFT → ISSUED |

### 7.4 Interface Contract (Frozen)

The `QuoteNumberingService` interface contract, frozen by this ADR:

```php
interface QuoteNumberingServiceInterface
{
    /**
     * Generates and assigns the next quote number in QT-YYYY-NNNN format.
     *
     * MUST be called within the same database transaction as the
     * DRAFT → IN_REVIEW state transition.
     *
     * @param Quote $quote The quote entity being transitioned
     * @return string The assigned quote number (e.g., "QT-2026-0042")
     * @throws NumberingException If the sequence limit (9999) is exceeded
     */
    public function assignQuoteNumber(Quote $quote): string;
}
```

The `PINumberingService` interface contract, frozen by this ADR:

```php
interface PINumberingServiceInterface
{
    /**
     * Generates and assigns the next PI number in PI-YYYY-NNNN format.
     *
     * MUST be called within the same database transaction as the
     * DRAFT → ISSUED state transition.
     *
     * @param ProformaInvoice $pi The PI entity being transitioned
     * @return string The assigned PI number (e.g., "PI-2026-0089")
     * @throws NumberingException If the sequence limit (9999) is exceeded
     */
    public function assignPiNumber(ProformaInvoice $pi): string;
}
```

---

## Appendix A: Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| N1 | Number format: `QT-YYYY-NNNN` / `PI-YYYY-NNNN` | Human-readable, sortable, industry-standard | 2026-07-21 |
| N2 | Assignment timing: Quote on REVIEW, PI on ISSUE | Drafts don't consume numbers; number signifies commitment | 2026-07-21 |
| N3 | Sequence owner: CRM Extension exclusively | Single source of truth; atomic with entity save | 2026-07-21 |
| N4 | Concurrency: Dedicated sequence table with `LAST_INSERT_ID` | Single atomic statement; no external dependency; gap-tolerant | 2026-07-21 |
| N5 | Gap policy: Permitted; no recycling | Industry standard; audit integrity; implementation simplicity | 2026-07-21 |
| N6 | Recovery: Manual sequence correction after DB restore | Documented operational procedure; automated correction is fragile | 2026-07-21 |
| N7 | Connector/Frontend/Document Service never generate C16 numbers | CRM is the single source of truth for business identifiers | 2026-07-21 |

## Appendix B: Unresolved Questions

| # | Question | Status | Target Phase |
|---|----------|--------|-------------|
| N-Q1 | Should `numbering_sequence` be an EspoCRM entity or a raw DB table? | Raw DB table recommended (§5.3) | C16.2 |
| N-Q2 | Should the sequence use `LAST_INSERT_ID` or `SELECT ... FOR UPDATE`? | `LAST_INSERT_ID` chosen (§5.3) | C16.2 |
| N-Q3 | Can EspoCRM's `EntityManager` wrap the sequence increment + entity save in one transaction? | Prototype required; implementation order depends on answer (§6.4) | C16.2 |
| N-Q4 | What happens when 9999 is reached in a calendar year? | Schema migration to 5 digits; monitoring alert at 9000 (§2.1) | Post-C16 |

## Appendix C: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) §7 — Original numbering design
- [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md) §3.6 — Sequence table migration strategy
- [ADR_C16_STATE_MACHINE_EXTENSIONS.md](ADR_C16_STATE_MACHINE_EXTENSIONS.md) — State transitions that trigger numbering

---

*End of ADR. Numbering strategy frozen. Implementation deferred to C16.2 and C16.5.*
