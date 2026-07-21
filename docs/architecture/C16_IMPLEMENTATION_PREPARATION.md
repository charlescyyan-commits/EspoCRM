# C16 Implementation Preparation — Design Freeze

**Status:** Pre-Implementation Design  
**Date:** 2026-07-21  
**Phase:** C16.0 — Implementation Preparation  
**References:** [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md), [PHASE3S02_COMPLETION_REPORT.md](../PHASE3S02_COMPLETION_REPORT.md)  
**Current HEAD:** `ed05319`

---

## Table of Contents

1. [EspoCRM Entity Mapping](#1-espocrm-entity-mapping)
2. [Metadata Strategy](#2-metadata-strategy)
3. [Database / Migration Strategy](#3-database--migration-strategy)
4. [ACL Design](#4-acl-design)
5. [Test Strategy](#5-test-strategy)
6. [Implementation Sequence](#6-implementation-sequence)
7. [Boundary Rules](#7-boundary-rules)
8. [Unresolved Decisions](#8-unresolved-decisions)
9. [Recommended First Implementation Task](#9-recommended-first-implementation-task)

---

## 1. EspoCRM Entity Mapping

### 1.1 Entity Type and Ownership Summary

| ADR Entity | EspoCRM Entity Name | Module | Type | Owner | Tab | ACL | Status Field |
|------------|---------------------|--------|------|-------|-----|-----|-------------|
| Quote | `Quote` | Prospecting | Base | CRM Extension | Yes | Yes | `status` |
| QuoteItem | `QuoteItem` | Prospecting | Base | CRM Extension | No (inline) | Inherited via Quote | — |
| ProformaInvoice | `ProformaInvoice` | Prospecting | Base | CRM Extension | Yes | Yes | `status` |
| Approval | `Approval` | Prospecting | Base | CRM Extension | Yes | Yes | `status` |

### 1.2 Quote — Complete Field Mapping

| ADR Field | EspoCRM Type | Required | Read-Only | Default | Notes |
|-----------|-------------|----------|-----------|---------|-------|
| `name` | `varchar` (255) | Yes | No | Auto from `quoteNumber` | Display name; `trim: true` |
| `quoteNumber` | `varchar` (32) | Yes | After assign | — | Format: `QT-YYYY-NNNN` |
| `status` | `enum` | Yes | Conditional | `DRAFT` | Options: DRAFT, IN_REVIEW, APPROVED, SENT, ACCEPTED, REJECTED, EXPIRED |
| `currency` | `varchar` (3) | Yes | No | `USD` | ISO 4217; `maxLength: 3` |
| `subtotal` | `currency` | No | Auto-calculated | `0.00` | Sum of QuoteItem.lineTotal |
| `taxRate` | `float` | No | No | `null` | Percentage; `min: 0, max: 100` |
| `taxAmount` | `currency` | No | Auto-calculated | `null` | `subtotal × taxRate / 100` |
| `total` | `currency` | No | Auto-calculated | `0.00` | `subtotal + taxAmount` |
| `validUntil` | `date` | No | No | `null` | After `validUntil`, system cron may expire |
| `notes` | `text` | No | No | `null` | Internal notes |
| `termsAndConditions` | `text` | No | No | `null` | Customer-facing; included in PDF |
| `pdfGeneratedAt` | `datetime` | No | Auto-set | `null` | Set when PDF is generated |
| `pdfStoragePath` | `varchar` (255) | No | Auto-set | `null` | Filesystem reference to PDF |
| `opportunity` | `link` | No | No | `null` | `belongsTo` Opportunity |
| `lead` | `link` | No | No | `null` | `belongsTo` Lead |
| `assignedUser` | `link` | No | No | Current user | Standard EspoCRM ownership |
| `teams` | `linkMultiple` | No | No | Current user's team | Standard EspoCRM teams |
| `createdAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `createdBy` | `link` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedBy` | `link` | Yes | Yes | Auto | Standard EspoCRM |

**Display styles for `status`:**
```json
{
  "DRAFT": "default",
  "IN_REVIEW": "warning",
  "APPROVED": "info",
  "SENT": "primary",
  "ACCEPTED": "success",
  "REJECTED": "danger",
  "EXPIRED": "default"
}
```

### 1.3 QuoteItem — Complete Field Mapping

| ADR Field | EspoCRM Type | Required | Read-Only | Default | Notes |
|-----------|-------------|----------|-----------|---------|-------|
| `name` | `varchar` (255) | Yes | No | — | Line item description; `trim: true` |
| `product` | `varchar` (255) | No | No | `null` | Product/service identifier |
| `description` | `text` | No | No | `null` | Detailed description |
| `quantity` | `float` | Yes | No | `1` | `min: 0` (exclusive; enforced in Service layer) |
| `unitPrice` | `currency` | Yes | No | `0.00` | `min: 0` |
| `discount` | `float` | No | No | `0` | Percentage; `min: 0, max: 100` |
| `lineTotal` | `currency` | No | Auto-calculated | `0.00` | `quantity × unitPrice × (1 − discount/100)` |
| `sortOrder` | `int` | No | No | `0` | Display ordering within parent Quote |
| `quote` | `link` | Yes | No | — | `belongsTo` Quote |
| `createdAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |

### 1.4 ProformaInvoice — Complete Field Mapping

| ADR Field | EspoCRM Type | Required | Read-Only | Default | Notes |
|-----------|-------------|----------|-----------|---------|-------|
| `name` | `varchar` (255) | Yes | No | Auto from `piNumber` | Display name; `trim: true` |
| `piNumber` | `varchar` (32) | Yes | After ISSUED | — | Format: `PI-YYYY-NNNN` |
| `status` | `enum` | Yes | Conditional | `DRAFT` | Options: DRAFT, ISSUED, SENT, PAID, VOID |
| `currency` | `varchar` (3) | Yes | After create | Inherited | Inherited from Quote at creation |
| `subtotal` | `currency` | No | After ISSUED | Snapshot | Snapshot from Quote at issuance |
| `taxAmount` | `currency` | No | After ISSUED | Snapshot | Snapshot from Quote at issuance |
| `total` | `currency` | No | After ISSUED | Snapshot | Snapshot from Quote at issuance |
| `paymentTerms` | `text` | No | No | `null` | e.g., "Net 30", "50% upfront, 50% on delivery" |
| `shippingTerms` | `text` | No | No | `null` | e.g., "FOB Shanghai", "CIF Los Angeles" |
| `issuedAt` | `datetime` | No | Auto on issue | `null` | Set on DRAFT → ISSUED |
| `sentAt` | `datetime` | No | Auto on send | `null` | Set on ISSUED → SENT |
| `paidAt` | `datetime` | No | Manual | `null` | Set when payment confirmed |
| `notes` | `text` | No | No | `null` | Internal notes |
| `quoteSnapshot` | `jsonObject` | No | Auto on issue | `null` | Immutable snapshot of Quote items at issuance time |
| `pdfGeneratedAt` | `datetime` | No | Auto-set | `null` | Set when PDF is generated |
| `pdfStoragePath` | `varchar` (255) | No | Auto-set | `null` | Filesystem reference to PDF |
| `quote` | `link` | Yes | Yes (after create) | — | `belongsTo` Quote |
| `assignedUser` | `link` | No | No | Current user | Standard EspoCRM ownership |
| `teams` | `linkMultiple` | No | No | Current user's team | Standard EspoCRM teams |
| `createdAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `createdBy` | `link` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedBy` | `link` | Yes | Yes | Auto | Standard EspoCRM |

**Display styles for `status`:**
```json
{
  "DRAFT": "default",
  "ISSUED": "info",
  "SENT": "primary",
  "PAID": "success",
  "VOID": "danger"
}
```

### 1.5 Approval — Complete Field Mapping

| ADR Field | EspoCRM Type | Required | Read-Only | Default | Notes |
|-----------|-------------|----------|-----------|---------|-------|
| `name` | `varchar` (255) | Yes | No | Auto | e.g., "Quote QT-2026-0001 Approval" |
| `approvalType` | `enum` | Yes | Yes (after create) | — | Options: `QUOTE`, `PI` |
| `status` | `enum` | Yes | Conditional | `PENDING` | Options: PENDING, APPROVED, REJECTED |
| `requestedBy` | `link` (User) | Yes | Yes | Auto | Set to current user on create |
| `approver` | `link` (User) | No | Auto on decision | `null` | Set when approve/reject is called |
| `decision` | `enum` | No | Auto on decision | `null` | Options: `APPROVED`, `REJECTED` |
| `reason` | `text` | No | No | `null` | Decision rationale (required on REJECTED) |
| `decidedAt` | `datetime` | No | Auto on decision | `null` | Timestamp of decision |
| `quote` | `link` | No | Yes (after create) | `null` | `belongsTo` Quote (when `approvalType = QUOTE`) |
| `proformaInvoice` | `link` | No | Yes (after create) | `null` | `belongsTo` ProformaInvoice (when `approvalType = PI`) |
| `createdAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |
| `modifiedAt` | `datetime` | Yes | Yes | Auto | Standard EspoCRM |

**Display styles for `status`:**
```json
{
  "PENDING": "warning",
  "APPROVED": "success",
  "REJECTED": "danger"
}
```

**Display styles for `decision`:**
```json
{
  "APPROVED": "success",
  "REJECTED": "danger"
}
```

**Design note (polymorphic FK):** EspoCRM does not natively support polymorphic `entityType`/`entityId`. The ADR recommends two optional link fields (`quoteId`, `proformaInvoiceId`). The Service layer enforces exactly one non-null link at create time. This is the simplest EspoCRM-compatible approach.

### 1.6 Relationship Map

```
Quote
├── belongsTo ──► Opportunity (optional, nullable)
├── belongsTo ──► Lead (optional, nullable)
├── hasMany ────► QuoteItem (foreign: quote)
├── hasMany ────► Approval (foreign: quote)
├── hasMany ────► ProformaInvoice (foreign: quote)
├── belongsTo ──► User (assignedUser)
├── belongsTo ──► User (createdBy, modifiedBy)
└── hasMany ────► Team (entityTeam)

QuoteItem
└── belongsTo ──► Quote (foreign: quoteItems)

ProformaInvoice
├── belongsTo ──► Quote (foreign: proformaInvoices)
├── hasMany ────► Approval (foreign: proformaInvoice)
├── belongsTo ──► User (assignedUser)
├── belongsTo ──► User (createdBy, modifiedBy)
└── hasMany ────► Team (entityTeam)

Approval
├── belongsTo ──► Quote (foreign: approvals)
├── belongsTo ──► ProformaInvoice (foreign: approvals)
├── belongsTo ──► User (requestedBy)
├── belongsTo ──► User (approver)
└── belongsTo ──► User (createdBy, modifiedBy)
```

### 1.7 Fields Category Summary

| Category | Fields | Entities |
|----------|--------|----------|
| **Business identity** | `quoteNumber`, `piNumber`, `name` | Quote, PI |
| **State** | `status` | Quote, PI, Approval |
| **Financial** | `currency`, `subtotal`, `taxRate`, `taxAmount`, `total` | Quote, PI, QuoteItem (`unitPrice`, `discount`, `lineTotal`) |
| **Line items** | `product`, `description`, `quantity`, `unitPrice`, `discount`, `lineTotal`, `sortOrder` | QuoteItem |
| **Terms** | `termsAndConditions`, `paymentTerms`, `shippingTerms` | Quote, PI |
| **Timeline** | `validUntil`, `issuedAt`, `sentAt`, `paidAt`, `decidedAt` | Quote, PI, Approval |
| **PDF** | `pdfGeneratedAt`, `pdfStoragePath` | Quote, PI |
| **Snapshot** | `quoteSnapshot` | PI |
| **Approval** | `approvalType`, `decision`, `reason` | Approval |
| **Standard CRM** | `createdAt`, `modifiedAt`, `createdBy`, `modifiedBy`, `assignedUser`, `teams` | All |

---

## 2. Metadata Strategy

### 2.1 Metadata Files Required per Entity

Each C16 entity requires the following metadata files (following existing Prospecting module conventions):

| Metadata Type | Path (relative to module Resources/) | Purpose |
|---------------|--------------------------------------|---------|
| **entityDefs** | `metadata/entityDefs/{Entity}.json` | Field definitions, links, indexes, collection settings |
| **clientDefs** | `metadata/clientDefs/{Entity}.json` | Client-side UI configuration, side panels, relationship panels |
| **scopes** | `metadata/scopes/{Entity}.json` | Entity type, ACL enablement, tab visibility, importability |
| **aclDefs** | `metadata/aclDefs/{Entity}.json` | Module-level ACL gate |
| **layouts** | `layouts/{Entity}/detail.json` | Detail view panel layout |
| **layouts** | `layouts/{Entity}/list.json` | List view column layout |
| **layouts** | `layouts/{Entity}/detailSmall.json` | Quick detail view (optional) |
| **i18n** | `i18n/en_US/{Entity}.json` | English field labels and translations |
| **i18n** | `i18n/zh_CN/{Entity}.json` | Chinese field labels and translations |

**Total metadata files for C16:** ~36 files (4 entities × ~9 files each)

### 2.2 Metadata File Inventory (Planned)

```
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/
  metadata/
    entityDefs/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
    clientDefs/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
    scopes/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
    aclDefs/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
  layouts/
    Quote/
      detail.json                                  # C16.1
      list.json                                    # C16.1
    QuoteItem/
      detail.json                                  # C16.1 (inline in Quote detail)
      list.json                                    # C16.1
    ProformaInvoice/
      detail.json                                  # C16.1
      list.json                                    # C16.1
    Approval/
      detail.json                                  # C16.1
      list.json                                    # C16.1
  i18n/
    en_US/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
    zh_CN/
      Quote.json                                   # C16.1
      QuoteItem.json                               # C16.1
      ProformaInvoice.json                         # C16.1
      Approval.json                                # C16.1
```

### 2.3 Surface-Level Mirror (Design Artifact)

Per existing convention, `crm-extension/Resources/` mirrors the module-level `Resources/` directory. C16 entity definitions must be duplicated in both locations. This is a known maintenance overhead (documented in S02.4 finding #2). The extension skeleton test `test_surface_and_module_entity_defs_match` enforces parity.

### 2.4 Collection Configuration

| Entity | `orderBy` | `order` | `textFilterFields` |
|--------|-----------|---------|---------------------|
| Quote | `modifiedAt` | `desc` | `name`, `quoteNumber`, `status`, `currency` |
| QuoteItem | `sortOrder` | `asc` | `name`, `product`, `description` |
| ProformaInvoice | `modifiedAt` | `desc` | `name`, `piNumber`, `status` |
| Approval | `modifiedAt` | `desc` | `name`, `approvalType`, `status`, `decision` |

### 2.5 Dashboards (Future — C16.5+)

Potential dashboard dashlets for the Prospecting dashboard:

| Dashlet | Entity | Purpose |
|---------|--------|---------|
| `RecentQuotes` | Quote | Recently modified Quotes |
| `QuotesByStatus` | Quote | Quote pipeline summary (DRAFT/IN_REVIEW/APPROVED/SENT) |
| `PendingApprovals` | Approval | Approvals awaiting decision |
| `RecentInvoices` | ProformaInvoice | Recently issued PIs |
| `QuotesExpiringSoon` | Quote | Quotes with `validUntil` within 30 days |

These are **not part of C16.1** and should be deferred to a post-C16.5 UI enhancement phase.

---

## 3. Database / Migration Strategy

### 3.1 Migration Type

C16 entities are **net-new**. No existing data requires migration. No existing tables or columns are modified.

**Migration class:** Not required for net-new entities in EspoCRM. Entity metadata JSON files in `entityDefs/` and `scopes/` are sufficient. EspoCRM's installer creates tables automatically from entity metadata.

### 3.2 New Tables (Auto-Created by EspoCRM)

| Entity | Table Name | Estimated Columns |
|--------|------------|-------------------|
| Quote | `quote` | ~20 columns |
| QuoteItem | `quote_item` | ~12 columns |
| ProformaInvoice | `proforma_invoice` | ~20 columns |
| Approval | `approval` | ~12 columns |

Plus standard junction tables for `linkMultiple` relations (`entity_team`).

### 3.3 Index Strategy

| Entity | Index Name | Columns | Type | Purpose |
|--------|------------|---------|------|---------|
| Quote | `quoteNumber` | `quoteNumber`, `deleteId` | Unique (with soft-delete) | Quote number uniqueness |
| Quote | `status` | `status` | Non-unique | Status filtering |
| Quote | `opportunityId` | `opportunityId` | Non-unique | Quote lookup by Opportunity |
| Quote | `leadId` | `leadId` | Non-unique | Quote lookup by Lead |
| Quote | `assignedUserId` | `assignedUserId` | Non-unique | User's Quote list |
| Quote | `validUntil` | `validUntil` | Non-unique | Expiration cron |
| QuoteItem | `quoteId_sortOrder` | `quoteId`, `sortOrder` | Composite | Ordered line items per Quote |
| ProformaInvoice | `piNumber` | `piNumber`, `deleteId` | Unique (with soft-delete) | PI number uniqueness |
| ProformaInvoice | `quoteId` | `quoteId` | Non-unique | PI lookup by Quote |
| ProformaInvoice | `status` | `status` | Non-unique | Status filtering |
| Approval | `quoteId_status` | `quoteId`, `status` | Composite | Pending approvals for a Quote |
| Approval | `piId_status` | `proformaInvoiceId`, `status` | Composite | Pending approvals for a PI |

### 3.4 Soft Delete

Quote, QuoteItem, ProformaInvoice, and Approval all use `"deleteId": true` (soft delete). This is the standard pattern in the Prospecting module (ResearchEvidence, DraftApproval, SendExecution, ReplyEvent all use soft delete).

### 3.5 Existing Entity Protection

C16 **does not modify** any of the following existing tables or columns:

| Entity | Protection |
|--------|-----------|
| `lead` | No new columns, no modified columns, no new indexes on existing columns |
| `opportunity` | No modifications |
| `email_event` | No modifications |
| `send_execution` | No modifications |
| `draft_approval` | No modifications |
| `research_evidence` | No modifications |
| `prospect_pool` | No modifications |
| `search_job` | No modifications |
| `search_strategy` | No modifications |
| `sales_feedback` | No modifications |
| `learning_signal` | No modifications |
| `reply_event` | No modifications |

**C16 entities are completely independent.** The only cross-entity links are:

- `Quote.opportunityId → opportunity.id` (nullable FK; Opportunity table unchanged)
- `Quote.leadId → lead.id` (nullable FK; Lead table unchanged)

These are standard EspoCRM `link` fields that do not alter the target table.

### 3.6 Sequence Table for Numbering

C16 requires a `numbering_sequence` table for atomic quote/PI number generation:

```sql
-- Managed by EspoCRM entity metadata or a dedicated Service
-- Fallback: file-based lock if DB-level atomic increment is unavailable
CREATE TABLE numbering_sequence (
  sequence_key VARCHAR(64) NOT NULL,  -- e.g., 'QUOTE-2026', 'PI-2026'
  current_value INT NOT NULL DEFAULT 0,
  PRIMARY KEY (sequence_key)
) ENGINE=InnoDB;
```

**Alternative (EspoCRM-native):** Store as a Singleton entity or use `Espo\Core\Utils\Util::generateId()` with date-prefixed increment. Decision deferred to C16.2 (see §8 Unresolved Decisions).

---

## 4. ACL Design

### 4.1 Role Definitions

| Role | Label | Scope | C16 Access |
|------|-------|-------|------------|
| **Sales** | Sales Representative | Assigned + team Quotes | Create, edit own DRAFT Quotes, send |
| **Manager** | Sales Manager | All team Quotes | Approve Quotes, view all, edit IN_REVIEW |
| **Finance** | Finance Officer | All PIs | Create/issue/send PI, mark paid, approve PI |
| **Admin** | System Administrator | Everything | Full CRUD, system overrides |

### 4.2 Module-Level ACL

Each C16 entity requires a module-level ACL entry:

```json
// metadata/aclDefs/Quote.json
{"Prospecting": {"Quote": true}}

// metadata/aclDefs/QuoteItem.json
{"Prospecting": {"QuoteItem": true}}

// metadata/aclDefs/ProformaInvoice.json
{"Prospecting": {"ProformaInvoice": true}}

// metadata/aclDefs/Approval.json
{"Prospecting": {"Approval": true}}
```

This follows the exact pattern used by all existing Prospecting entities (DraftApproval, SendExecution, etc.).

### 4.3 Detailed Permission Matrix

#### Quote Permissions

| Action | Sales | Manager | Finance | Admin | Condition |
|--------|:-----:|:-------:|:-------:|:-----:|-----------|
| Create | ✅ | ✅ | ❌ | ✅ | — |
| Read (own) | ✅ | ✅ | ✅ | ✅ | assignedUser = current user |
| Read (team) | ✅ | ✅ | ✅ | ✅ | teams contains current user's team |
| Read (all) | ❌ | ✅ | ✅ | ✅ | — |
| Edit (own, DRAFT) | ✅ | ✅ | ❌ | ✅ | status = DRAFT |
| Edit (own, IN_REVIEW) | ❌ | ✅ | ❌ | ✅ | status = IN_REVIEW |
| Edit (own, APPROVED+) | ❌ | ❌ | ❌ | ✅ | status = APPROVED/SENT/ACCEPTED/REJECTED/EXPIRED |
| Delete (own, DRAFT) | ✅ | ✅ | ❌ | ✅ | status = DRAFT |
| Delete (non-DRAFT) | ❌ | ❌ | ❌ | ✅ | — |
| Submit for review | ✅ | ✅ | ❌ | ✅ | Only from DRAFT |
| Approve | ❌ | ✅ | ❌ | ✅ | Only from IN_REVIEW |
| Send to customer | ✅ | ✅ | ❌ | ✅ | Only from APPROVED; PDF must exist |
| Accept / Reject | ✅ | ✅ | ❌ | ✅ | Only from SENT |
| Download PDF (own) | ✅ | ✅ | ✅ | ✅ | — |
| Download PDF (any) | ❌ | ✅ | ✅ | ✅ | — |
| Expire (manual) | ❌ | ❌ | ❌ | ✅ | Only from SENT |

#### QuoteItem Permissions

| Action | Sales | Manager | Finance | Admin | Condition |
|--------|:-----:|:-------:|:-------:|:-----:|-----------|
| Create | ✅ | ✅ | ❌ | ✅ | Parent Quote status = DRAFT |
| Read | ✅ | ✅ | ✅ | ✅ | Inherited from parent Quote |
| Edit | ✅ | ✅ | ❌ | ✅ | Parent Quote status = DRAFT |
| Delete | ✅ | ✅ | ❌ | ✅ | Parent Quote status = DRAFT |

**Implementation note:** QuoteItem has no independent ACL. Permissions are checked against the parent Quote in the Service layer. The `aclDefs/QuoteItem.json` enables the ACL module gate; the Service layer enforces the parent-link constraint.

#### ProformaInvoice Permissions

| Action | Sales | Manager | Finance | Admin | Condition |
|--------|:-----:|:-------:|:-------:|:-----:|-----------|
| Create | ❌ | ❌ | ✅ | ✅ | Parent Quote status ∈ {APPROVED, ACCEPTED} |
| Read (own) | ✅ | ✅ | ✅ | ✅ | — |
| Read (all) | ❌ | ✅ | ✅ | ✅ | — |
| Edit (DRAFT) | ❌ | ❌ | ✅ | ✅ | status = DRAFT |
| Edit (ISSUED+) | ❌ | ❌ | ❌ | ✅ | — |
| Issue | ❌ | ❌ | ✅ | ✅ | Only from DRAFT |
| Send | ❌ | ✅ | ✅ | ✅ | Only from ISSUED |
| Mark Paid | ❌ | ❌ | ✅ | ✅ | Only from SENT |
| Void | ❌ | ❌ | ✅ | ✅ | From any non-terminal state |
| Download PDF | ✅ | ✅ | ✅ | ✅ | — |

#### Approval Permissions

| Action | Sales | Manager | Finance | Admin | Condition |
|--------|:-----:|:-------:|:-------:|:-----:|-----------|
| View (own requests) | ✅ | ✅ | ✅ | ✅ | `requestedBy` = current user |
| View (all Quote approvals) | ❌ | ✅ | ❌ | ✅ | `approvalType` = QUOTE |
| View (all PI approvals) | ❌ | ❌ | ✅ | ✅ | `approvalType` = PI |
| Approve (Quote) | ❌ | ✅ | ❌ | ✅ | `approvalType` = QUOTE, status = PENDING |
| Reject (Quote) | ❌ | ✅ | ❌ | ✅ | `approvalType` = QUOTE, status = PENDING |
| Approve (PI) | ❌ | ❌ | ✅ | ✅ | `approvalType` = PI, status = PENDING |
| Reject (PI) | ❌ | ❌ | ✅ | ✅ | `approvalType` = PI, status = PENDING |

### 4.4 Field-Level ACL

| Entity | Field | Access Rule |
|--------|-------|------------|
| Quote | `total`, `taxAmount` | Read-only for Sales after APPROVED |
| Quote | `pdfStoragePath` | Hidden from UI; internal-only |
| Quote | `quoteNumber` | Read-only after IN_REVIEW |
| ProformaInvoice | `paidAt` | Write-only for Finance |
| ProformaInvoice | `piNumber` | Read-only after ISSUED |
| ProformaInvoice | `quoteSnapshot` | Read-only after ISSUED |
| Approval | `decision`, `reason` | Write-only for Manager (Quote) / Finance (PI) on decision; read-only after |

### 4.5 Scope-Level ACL

- **Sales** — sees assigned Quotes + team Quotes (standard EspoCRM `assignedUser` + `teams` scope)
- **Manager** — sees all Quotes in their team(s) (standard EspoCRM `teams` scope)
- **Finance** — sees all PIs (no scope restriction); sees Quote `total`/`subtotal` for invoicing context
- **Admin** — sees everything (no scope restriction)

---

## 5. Test Strategy

### 5.1 Test Categories

| Category | Framework | Location | Purpose |
|----------|-----------|----------|---------|
| **Unit tests (PHP)** | PHPUnit (EspoCRM test harness) | `crm-extension/tests/` | Service logic, state transitions, numbering |
| **Extension skeleton tests** | pytest | `crm-extension/tests/` (Python) | Entity metadata integrity, ACL configuration |
| **Integration tests (PHP)** | PHPUnit | `crm-extension/tests/` | End-to-end workflows, cross-entity consistency |
| **Runtime tests** | pytest | `tests/` | Gate verification, regression protection |
| **Gate integration** | Existing unified gate | `scripts/testing/` | All C16 tests must pass in unified gate |

### 5.2 Unit Test Coverage Plan

#### C16.1 — Entity Foundation

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_c16_entity_definitions.py` | 12 | All 4 entity metadata files exist, valid JSON, required fields present |
| `test_c16_entity_scopes.py` | 8 | All 4 scope files exist, correct type/ACL/tab settings |
| `test_c16_entity_layouts.py` | 8 | Detail and list layouts exist for all tab-visible entities |
| `test_c16_entity_i18n.py` | 4 | en_US and zh_CN translations exist for all entities |
| `test_c16_surface_module_parity.py` | 4 | Surface `Resources/` entityDefs match module `Resources/` entityDefs |

**Total C16.1 extension skeleton tests:** ~36 tests

#### C16.2 — Quote Workflow

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_quote_numbering.py` | 8 | Format validation, annual reset, uniqueness, concurrency simulation |
| `test_quote_state_transitions.py` | 15 | All valid transitions succeed; all invalid transitions fail |
| `test_quote_line_total_calculation.py` | 6 | Correct subtotal/tax/total computation |
| `test_quote_validation.py` | 8 | Required fields, min/max constraints, validUntil > createdAt |
| `test_quote_idempotency.py` | 6 | Double-submit, double-approve, double-send are no-ops |

**Total C16.2 unit tests:** ~43 tests

#### C16.3 — Approval Workflow

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_approval_creation.py` | 6 | Auto-created on Quote IN_REVIEW, PI ISSUED |
| `test_approval_state_transitions.py` | 8 | PENDING→APPROVED, PENDING→REJECTED, terminal no-exit |
| `test_approval_cross_entity_consistency.py` | 6 | Quote can't reach APPROVED without Approval; PI can't reach ISSUED without Quote APPROVED/ACCEPTED |
| `test_approval_permissions.py` | 8 | Sales can't approve; Manager can approve Quote only; Finance can approve PI only |

**Total C16.3 unit tests:** ~28 tests

#### C16.4 — PDF Pipeline

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_pdf_client_service.py` | 6 | HTTP client construction, request payload, error handling |
| `test_pdf_attachment_storage.py` | 6 | PDF saved as EspoCRM Attachment, linked to parent entity |
| `test_pdf_generation_triggers.py` | 6 | Generated on APPROVED→SENT (Quote), ISSUED→SENT (PI) |
| `test_pdf_draft_watermark.py` | 3 | DRAFT watermark applied for pre-APPROVED preview |

**Total C16.4 unit tests:** ~21 tests

#### C16.5 — PI Workflow

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_pi_numbering.py` | 6 | Format validation, annual reset, uniqueness |
| `test_pi_state_transitions.py` | 10 | Valid transitions succeed; invalid transitions fail |
| `test_pi_quote_snapshot.py` | 5 | Quote items snapshot captured on ISSUED; immutable after |
| `test_pi_quote_state_guard.py` | 5 | PI can only be created from APPROVED/ACCEPTED Quote |

**Total C16.5 unit tests:** ~26 tests

#### C16.6 — Integration

| Test File | Tests | Assertions |
|-----------|-------|------------|
| `test_c16_end_to_end.py` | 8 | Full flow: Quote create → approve → PDF → send → accept → PI create → issue → send → paid |
| `test_c16_regression_no_modify.py` | 6 | Existing entities untouched; existing gate still passes |

**Total C16.6 integration tests:** ~14 tests

### 5.3 Total Test Budget

| Phase | New Tests | Cumulative |
|-------|-----------|------------|
| C16.1 | ~36 | 36 |
| C16.2 | ~43 | 79 |
| C16.3 | ~28 | 107 |
| C16.4 | ~21 | 128 |
| C16.5 | ~26 | 154 |
| C16.6 | ~14 | 168 |

**Total C16 test budget:** ~168 tests across 27 test files.

### 5.4 Regression Gate Updates

Each C16 phase must update `test_extension_skeleton.py` (the Python pytest gate) to assert:
- C16 entity metadata files exist and are valid JSON
- C16 entity ACL defs exist
- C16 entity scopes are correctly configured
- No existing entity metadata was modified (checksum comparison or field-count assertion)

The unified gate (`scripts/testing/run-unified-gate.ps1`) continues to run all tests including the updated skeleton.

### 5.5 Test Isolation Guarantees

- **No CRM instance required:** Unit tests use mock/fake service dependencies
- **No database required:** Extension skeleton tests validate metadata files, not runtime DB state
- **No network required:** PDF client is mocked; document service is not called
- **No connector required:** C16 tests are CRM-side only

---

## 6. Implementation Sequence

### 6.1 Phase Dependency Graph

```
C16.1 (Entity Foundation)
  │
  ├──► C16.2 (Quote Workflow)
  │      │
  │      ├──► C16.3 (Approval Workflow)
  │      │      │
  │      │      ├──► C16.4 (PDF Pipeline)
  │      │      │      │
  │      │      │      └──► C16.6 (Integration)
  │      │      │
  │      │      └──► C16.5 (PI Workflow)
  │      │             │
  │      │             └──► C16.6 (Integration)
  │      │
  │      └──► C16.5 (PI Workflow) [can start after C16.2 + C16.3]
  │
  └──► (all phases depend on C16.1)
```

**Critical path:** C16.1 → C16.2 → C16.3 → C16.4 → C16.6
**Parallel opportunity:** C16.4 and C16.5 can be developed concurrently after C16.3

### 6.2 Phase Details

---

#### C16.1 — Entity Foundation

**Goal:** All four C16 entities exist as valid EspoCRM metadata. No business logic yet.

**Scope:**
- 4 × `entityDefs/*.json` (Quote, QuoteItem, ProformaInvoice, Approval)
- 4 × `clientDefs/*.json`
- 4 × `scopes/*.json`
- 4 × `aclDefs/*.json`
- 8 × layout files (`detail.json`, `list.json` per entity)
- 8 × i18n files (`en_US`, `zh_CN` per entity)
- Surface-level mirror in `crm-extension/Resources/`
- Update `test_extension_skeleton.py` with C16 entity assertions

**Files created:** ~36 metadata files + ~36 surface mirrors = ~72 files (see §2.2)

**Risks:**
- **LOW:** Surface/module mirror duplication — must keep both copies in sync
- **LOW:** EspoCRM may require a `clear_cache` after new entity installation

**Validation:**
- Extension skeleton tests detect all 4 entities
- All metadata files are valid JSON
- Entity scopes are correctly configured
- No existing entity metadata modified

---

#### C16.2 — Quote Workflow

**Goal:** Quotes can be created, edited, submitted, approved, sent, accepted, rejected, and expired — with correct state transitions, numbering, and line-item calculations.

**Scope:**
- `QuoteService.php` — CRUD + state transitions + idempotency
- `QuoteItemService.php` — CRUD + line-total calculation
- `QuoteNumberingService.php` — atomic sequence generation
- `QuoteStatusTimestamps.json` (formula) — auto-set `validUntil` warnings
- Quote-related hooks (optional — state transitions may be formula-driven)

**Key implementation details:**
- Numbering: first `submitForReview()` transitions from DRAFT → IN_REVIEW assigns `quoteNumber`
- Line totals: recomputed on QuoteItem save; Quote `subtotal`/`taxAmount`/`total` recalculated
- State guards: see ADR §4.1 transition table
- Idempotency: all state transitions are no-ops if already in target state

**Risks:**
- **MEDIUM:** Numbering concurrency — DB-level atomic increment may require raw SQL; prototype before committing to implementation
- **LOW:** Line-item recalculation on every save — ensure formula/hook doesn't create an infinite loop

**Validation:**
- ~43 unit tests pass (see §5.2)
- State machine: all valid transitions succeed, all invalid transitions blocked
- Numbering: format `QT-YYYY-NNNN`, annual reset, no duplicates
- Line totals: correct arithmetic for subtotal/tax/total

---

#### C16.3 — Approval Workflow

**Goal:** Approvals are auto-created on Quote IN_REVIEW and PI ISSUED. Managers can approve/reject Quotes. Finance can approve/reject PIs. Cross-entity state consistency is enforced.

**Scope:**
- `ApprovalService.php` — create, approve, reject
- Auto-creation hook/formula: Quote reaches IN_REVIEW → Approval (PENDING); PI reaches ISSUED → Approval (PENDING)
- Approval decision → parent entity state propagation: APPROVED Quote → Quote status update; REJECTED Quote → back to DRAFT
- Cross-entity consistency guards (see ADR §4.4)

**Key implementation details:**
- Quote approval: Manager approves → Quote transitions to APPROVED; Manager rejects → Quote transitions back to DRAFT (with revision note)
- PI approval: Finance approves → PI transitions to SENT; Finance rejects → PI transitions to DRAFT
- Decision reason is required for rejection
- `decidedAt` and `approver` set automatically on decision

**Risks:**
- **MEDIUM:** Cross-entity consistency — Quote cannot reach APPROVED without an APPROVED Approval. If the Approval is deleted, the Quote state must be re-evaluated
- **LOW:** Approval chain escalation is not implemented in C16.3 (deferred to future enhancement per ADR Q2)

**Validation:**
- ~28 unit tests pass (see §5.2)
- Approval auto-created on correct triggers
- Approval decision propagates to parent entity correctly
- Permission enforcement: Sales can't approve; role separation verified

---

#### C16.4 — PDF Pipeline

**Goal:** Quote and PI PDFs are generated via the Document Service, stored as EspoCRM Attachments, and downloadable by authorized users.

**Scope:**
- `PdfClientService.php` — HTTP client for Document Service API
- PDF generation trigger: on Quote SENT, on PI SENT
- PDF storage: EspoCRM Attachment (primary) + filesystem path reference (fallback)
- DRAFT watermark rendering (preview without approval)
- PDF download endpoint (standard EspoCRM attachment download)

**Key implementation details:**
- Document Service API contract: `POST /api/v1/pdf/render` with `{ template, data, apiKey }`
- Templates: `quote.html` and `pi.html` (HTML/CSS; maintained in document service, not CRM)
- PDF is generated once per Quote/PI version; regeneration only allowed in DRAFT
- Attachment created with `parentType: "Quote"` (or `"ProformaInvoice"`), `parentId: <entityId>`

**Risks:**
- **HIGH:** Document Service does not exist yet — C16.4 requires either selecting and deploying an existing service (Gotenberg, Puppeteer-based) or building a minimal one. This is the biggest external dependency in C16.
- **MEDIUM:** PDF template design — HTML/CSS templates must render correctly across the document service. Template iteration may require multiple rounds.
- **LOW:** Network timeout — 30s timeout may need tuning for complex Quotes with many line items.

**Validation:**
- ~21 unit tests pass (see §5.2)
- PDF generated and stored as Attachment on Quote SENT / PI SENT
- DRAFT watermark present for pre-APPROVED preview
- PDF regeneration blocked for non-DRAFT Quotes
- Attachment download works for authorized users

---

#### C16.5 — PI Workflow

**Goal:** Proforma Invoices can be created from approved Quotes, issued, sent, marked as paid, and voided — with correct state transitions, numbering, and Quote snapshot immutability.

**Scope:**
- `ProformaInvoiceService.php` — CRUD + state transitions + idempotency
- `PINumberingService.php` — atomic sequence generation
- Quote → PI data snapshot on issuance (quoteSnapshot JSON field)
- PI state transition validation
- Cross-entity guards (Quote must be APPROVED/ACCEPTED)

**Key implementation details:**
- PI created with financial fields inherited from Quote (currency, subtotal, taxAmount, total)
- On `issue()`: `piNumber` assigned, `quoteSnapshot` captured, `issuedAt` set, Approval auto-created
- `quoteSnapshot` is a JSON serialization of Quote + QuoteItem data at issuance time
- Quote can have multiple PIs (revisions); old PIs remain accessible

**Risks:**
- **LOW:** Quote modification after PI issuance — PI has a snapshot, so Quote changes don't affect issued PIs. This is by design.
- **LOW:** Quote cannot be deleted or reverted to DRAFT if an ISSUED/SENT PI exists (unless PI is VOID). Service-layer guard required.

**Validation:**
- ~26 unit tests pass (see §5.2)
- PI can only be created from APPROVED/ACCEPTED Quote
- `quoteSnapshot` is immutable after issuance
- State transitions: all valid transitions succeed; all invalid transitions blocked
- Numbering: format `PI-YYYY-NNNN`, annual reset, no duplicates

---

#### C16.6 — Integration

**Goal:** Full end-to-end flows verified. Existing gate passes. No regressions.

**Scope:**
- End-to-end smoke test: Quote create → add items → submit → approve → PDF → send → accept → PI create → issue → send → mark paid
- Regression verification: all existing tests (528) continue to pass
- Extension skeleton test updated with full C16 coverage
- Documentation: update `SYSTEM_OVERVIEW.md`, `MODULES.md`, `BOUNDARIES.md` to include C16 entities
- Release readiness: unified gate passes with C16 tests included

**Key implementation details:**
- No new business logic in C16.6 — this is a verification and documentation phase
- Update `docs/architecture/SYSTEM_OVERVIEW.md` entity table
- Update `docs/architecture/DATA_FLOW.md` if C16 introduces any new flow patterns
- Update `docs/architecture/BOUNDARIES.md` if C16 introduces any new boundaries
- Confirm `scripts/release.ps1` successfully runs the unified gate with C16 tests

**Risks:**
- **LOW:** Test count increase may affect gate execution time — monitor and adjust timeout if needed

**Validation:**
- ~14 integration tests pass (see §5.2)
- Full end-to-end flow completes without errors
- Existing 528-test gate continues to pass
- Release flow (`scripts/release.ps1 -DryRun`) succeeds
- No regressions in C10, C11, C14 entity behavior

---

### 6.3 Phase Summary Table

| Phase | New Files | New Tests | External Dependency | Risk Level |
|-------|-----------|-----------|---------------------|------------|
| C16.1 | ~72 (metadata) | ~36 | None | LOW |
| C16.2 | ~5 (PHP services) | ~43 | None | MEDIUM (numbering concurrency) |
| C16.3 | ~2 (PHP service) | ~28 | None | MEDIUM (cross-entity consistency) |
| C16.4 | ~2 (PHP client) + ~2 (HTML templates) | ~21 | **Document Service** | HIGH (external service dependency) |
| C16.5 | ~3 (PHP services) | ~26 | None | LOW |
| C16.6 | ~4 (docs updated) | ~14 | None | LOW |

---

## 7. Boundary Rules

### 7.1 C16 Must Not Modify

The following components are **explicitly out of scope** for all C16 phases. Any test that detects a modification to these components is a blocking regression:

| Component | Path Pattern | Reason |
|-----------|-------------|--------|
| Acquisition worker | `chitu-connector/chitu_connector/acquisition/worker.py` | C10 acquisition; different domain |
| Search providers | `chitu-connector/chitu_connector/acquisition/providers/` | C10 acquisition; different domain |
| Brevo adapter | `chitu-connector/chitu_connector/espocrm_sync/brevo_*.py` | C14 email provider; different domain |
| Retry queue | `chitu-connector/chitu_connector/espocrm_sync/queue_contract.py` | C14 send queue; different domain |
| Send execution worker | `chitu-connector/chitu_connector/espocrm_sync/worker_execution.py` | C14 send worker; different domain |
| ChituSyncService | `crm-extension/.../Services/ChituSyncService.php` | C10 sync; different domain |
| EmailLifecycleProjectionService | `crm-extension/.../Services/EmailLifecycleProjectionService.php` | C14.3 projection; different domain |
| BrevoEmailEventSyncService | `crm-extension/.../Services/BrevoEmailEventSyncService.php` | C14 email events; different domain |
| SendExecutionBridgeAdapterService | `crm-extension/.../Services/SendExecutionBridgeAdapterService.php` | C14 bridge; different domain |
| DraftApproval entity | `crm-extension/.../entityDefs/DraftApproval.json` | C11 email draft approval; different domain |
| SendExecution entity | `crm-extension/.../entityDefs/SendExecution.json` | C11/C14 send execution; different domain |
| EmailEvent entity | `crm-extension/.../entityDefs/EmailEvent.json` | C14 email events; different domain |
| Lead entity | `crm-extension/.../entityDefs/Lead.json` | C10/C11/C14 shared entity; multiple domains |
| Opportunity entity | `crm-extension/.../entityDefs/Opportunity.json` | C10 opportunity projection; different domain |
| Manifest / build | `crm-extension/manifest.json`, `crm-extension/scripts/build_release_package.py` | S01 release integrity |
| Release script | `scripts/release.ps1` | S02.3 release automation |

### 7.2 Connector Interaction Boundary

The connector's relationship to C16 is **read-only and optional**:

| Direction | Allowed | Mechanism |
|-----------|---------|-----------|
| Connector → Quote (read) | ✅ Allowed | Standard EspoCRM REST API (GET) |
| Connector → PI (read) | ✅ Allowed | Standard EspoCRM REST API (GET) |
| Connector → Quote (write) | ❌ Forbidden | — |
| Connector → PI (write) | ❌ Forbidden | — |
| Connector → Approval (write) | ❌ Forbidden | — |
| CRM → Connector (Quote event) | ✅ Future | Event emission pattern (C16.6) |
| CRM → Document Service | ✅ Allowed | HTTP POST for PDF rendering |

### 7.3 CRM Ownership

| Entity | Owner | Write Access |
|--------|-------|-------------|
| Quote | CRM Extension | Sales, Manager, Admin |
| QuoteItem | CRM Extension | Sales, Manager, Admin (via parent Quote) |
| ProformaInvoice | CRM Extension | Finance, Admin |
| Approval | CRM Extension | Manager (Quote), Finance (PI), Admin |

---

## 8. Unresolved Decisions

The following decisions from the ADR (Appendix Q1–Q8) remain unresolved and should be addressed before or during the relevant implementation phase:

| # | Question | Relevant Phase | Current Position | Decision Deadline |
|---|----------|---------------|------------------|-------------------|
| Q1 | Multi-currency conversion rates? | C16.2 | Defer; single currency per Quote | Before C16.2 freeze |
| Q2 | Multi-level approval (Manager → Director → Finance)? | C16.3 | Single-level in C16.3; design `approvalLevel` field for future | Before C16.3 freeze |
| Q3 | Auto-notify assigned user on Quote expiration? | C16.2 | Defer to EspoCRM notification system | During C16.2 implementation |
| Q4 | Exact Document Service technology (Gotenberg vs. Puppeteer vs. WeasyPrint)? | C16.4 | **Decision required before C16.4 starts** | Before C16.4 starts |
| Q5 | Document Service: separate repo or co-located? | C16.4 | **Decision required before C16.4 starts** | Before C16.4 starts |
| Q6 | PDF archival/retention policy? | C16.6 | Defer; legal/compliance dependent | Before C16.6 freeze |
| Q7 | Digital signatures on PI PDFs? | C16.5+ | Defer; evaluate as enhancement | Post-C16 |
| Q8 | Exact concurrency mechanism for numbering? | C16.2 | Prototype DB-level atomic increment; fall back to file-lock or UUID if unavailable | Before C16.2 freeze |

**New decisions arising from this preparation document:**

| # | Question | Context | Recommendation |
|---|----------|---------|----------------|
| Q9 | Should `numbering_sequence` be an EspoCRM entity or a raw DB table? | §3.6 | Recommend raw DB table managed by Service — simpler, no entity overhead; EspoCRM entity if UI management of sequence is desired |
| Q10 | Should QuoteItem be a tab-visible entity or only visible inline on Quote detail? | §1.1 | Recommend inline-only (tab: false) — matches standard CRM Quote pattern; QuoteItem has no independent business meaning |
| Q11 | Should Approval be a tab-visible entity? | §1.1 | Recommend tab: true — Managers and Finance need to see their pending approvals independently of the parent entity |

---

## 9. Recommended First Implementation Task

### C16.1 — Entity Foundation

**Why C16.1 first:**
- All subsequent phases depend on entities existing
- Pure metadata work — no business logic, lowest risk
- Establishes the target for all test assertions
- Can be validated entirely offline (extension skeleton tests)

**Recommended task breakdown:**

1. Create `Quote.json` entityDefs (see §1.2 field table)
2. Create `QuoteItem.json` entityDefs (see §1.3 field table)
3. Create `ProformaInvoice.json` entityDefs (see §1.4 field table)
4. Create `Approval.json` entityDefs (see §1.5 field table, §1.5 polymorphic FK design note)
5. Create `scopes/*.json` for all 4 entities (§2.1)
6. Create `aclDefs/*.json` for all 4 entities (§4.2)
7. Create `clientDefs/*.json` for all 4 entities
8. Create `layouts/{Entity}/detail.json` and `list.json` for tab-visible entities (Quote, ProformaInvoice, Approval)
9. Create `i18n/en_US/{Entity}.json` and `i18n/zh_CN/{Entity}.json` for all 4 entities
10. Mirror all metadata to `crm-extension/Resources/` (surface level)
11. Update `crm-extension/tests/test_extension_skeleton.py`:
    - Assert all 4 entity metadata files exist
    - Assert all 4 scope files exist with correct configuration
    - Assert all 4 ACL defs exist
    - Assert surface/module parity for all 4 entities
12. Run unified gate to confirm no regressions

**Estimated effort:** 1 session (metadata-only; no PHP code)

**Deliverable:** 4 valid EspoCRM entities (Quote, QuoteItem, ProformaInvoice, Approval) with complete metadata, layouts, i18n, and test coverage.

---

## Appendix A: File Creation Summary

| Phase | Files Created | Type |
|-------|--------------|------|
| C16.1 | ~72 | Metadata JSON + i18n + layouts (inc. surface mirrors) |
| C16.2 | ~5 | PHP services + formula JSON |
| C16.3 | ~2 | PHP service |
| C16.4 | ~4 | PHP client + HTML templates (in document service) |
| C16.5 | ~3 | PHP services |
| C16.6 | ~4 | Documentation updates |
| **Total** | **~90** | |

## Appendix B: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) — C16 architecture decisions
- [PHASE3S02_COMPLETION_REPORT.md](../PHASE3S02_COMPLETION_REPORT.md) — S02 freeze baseline
- [PHASE3S02_ARCHITECTURE_READINESS_REVIEW.md](../PHASE3S02_ARCHITECTURE_READINESS_REVIEW.md) — S02 planning
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) — Current entity map
- [BOUNDARIES.md](BOUNDARIES.md) — System boundary enforcement
- [MODULES.md](MODULES.md) — Module structure

---

*End of C16 Implementation Preparation. No code implemented. Design freeze only.*
