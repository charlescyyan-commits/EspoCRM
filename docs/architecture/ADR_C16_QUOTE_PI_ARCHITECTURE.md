# ADR: C16 — Quote / PI / Approval / CRM Integration Architecture

**Status:** Draft — Design Freeze  
**Date:** 2026-07-21  
**Phase:** Phase3S02.6  
**Author:** Architecture Decision Record  
**Supersedes:** None (new capability)  

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Current Architecture Constraints](#2-current-architecture-constraints)
3. [Domain Model](#3-domain-model)
4. [State Machine Design](#4-state-machine-design)
5. [PDF Architecture Decision](#5-pdf-architecture-decision)
6. [Storage Strategy](#6-storage-strategy)
7. [Numbering Convention](#7-numbering-convention)
8. [Integration Boundary](#8-integration-boundary)
9. [Security and Permission Model](#9-security-and-permission-model)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Unresolved Questions](#11-unresolved-questions)
12. [Decision Log](#12-decision-log)

---

## 1. Purpose and Scope

### 1.1 What This ADR Covers

C16 introduces **Quote, Proforma Invoice (PI), and Approval workflows** into the EspoCRM Prospecting module. This ADR freezes the architecture **before any code is written**.

### 1.2 What This ADR Does NOT Cover

- **C10** — Research lifecycle (ResearchEvidence, SearchStrategy, SearchJob, ProspectPool)
- **C11** — Draft/Approval boundary for email content (DraftApproval, SendExecution)
- **C14** — Email lifecycle (EmailEvent, SendExecution, ReplyEvent, Brevo adapter)
- **C14.3** — Result Projection (EmailLifecycleProjectionService)
- **S01** — Release Integrity (extension packaging, reproducibility)
- **Acquisition worker** — Python-based search execution and prospect discovery
- **Email provider adapters** — Brevo, retry queue, or any outbound email infrastructure
- **Chitu scoring logic** — AI research, scoring engine, email generation engine

### 1.3 Non-Negotiable Constraints

C16 **must not**:
1. Modify `ChituSyncService` scoring or opportunity proposal logic
2. Modify `EmailLifecycleProjectionService` or any C14 email pipeline
3. Modify `DraftApproval` entity or its C11 email-approval workflow
4. Modify `SendExecution` entity or its CREATED→READY→SENT→FAILED state machine
5. Modify the acquisition worker, Brevo adapter, or retry queue
6. Import real customer data or enable outreach without explicit approval
7. Break the existing `test_extension_skeleton.py` gate

---

## 2. Current Architecture Constraints

### 2.1 Existing Entity Map (Pre-C16)

```
Lead (extended)
├── peEmailStatus: NONE → DRAFT_READY → DRAFT_PENDING_APPROVAL → APPROVED/REJECTED
│                    → PENDING → READY_TO_SEND → SENT/FAILED/CANCELLED
│                    → REPLIED/BOUNCED
├── outreachStatus: NEW → RESEARCHING → RESEARCH_COMPLETED → QUALIFIED
│                    → CONTACT_READY → CONTACTED → RESPONDED → CONVERTED/CLOSED_LOST
├── peOpportunityScoreV4 (0–100), peScoreTier (A/B/C/D)
├── peProposalAction: default = NO_AUTOMATIC_OPPORTUNITY
└── Links: researchEvidences, salesFeedbacks, learningSignals,
           emailEvents, draftApprovals, sendExecutions, replyEvents

Opportunity (extended with pe* fields)
└── Never auto-created — NO_AUTOMATIC_OPPORTUNITY enforced in ChituSyncService

DraftApproval (C11 — email draft approval)
├── status: PENDING → APPROVED | REJECTED
├── lead (belongsTo)
├── approvedBy (belongsTo User)
├── draftId, contentHash, scoreSnapshot, evidenceReference
└── Links: sendExecutions (hasMany)

SendExecution (C11/C14 — email send execution)
├── status: CREATED → READY → SENT | FAILED | CANCELLED
├── draftApproval (belongsTo)
├── lead (belongsTo)
├── retryCount, maxRetries, nextRetryAt
├── failureCategory: NETWORK | PROVIDER | AUTH | RATE_LIMIT | VALIDATION | UNKNOWN
└── Links: replyEvents (hasMany)

EmailEvent (C14 — Brevo event ingestion)
├── Append-only, deduped by externalMessageId + eventType
└── Links: lead (belongsTo)

ResearchEvidence (C10)
├── Compact immutable evidence projection
└── Links: lead (belongsTo)

SearchStrategy → SearchJob → ProspectPool (C10)
└── ProspectPool → Lead bridge: Not Implemented

SalesFeedback → LearningSignal (C10 feedback loop)
```

### 2.2 Existing State Machines (Pre-C16)

| Entity | States | Owner |
|--------|--------|-------|
| Lead.peEmailStatus | NONE, DRAFT_READY, DRAFT_PENDING_APPROVAL, APPROVED, REJECTED, PENDING, READY_TO_SEND, SENT, FAILED, CANCELLED, REPLIED, BOUNCED | C14 Email Lifecycle |
| Lead.outreachStatus | NEW, RESEARCHING, RESEARCH_COMPLETED, QUALIFIED, CONTACT_READY, CONTACTED, RESPONDED, CONVERTED, CLOSED_LOST | C10 Prospecting Lifecycle |
| DraftApproval.status | PENDING, APPROVED, REJECTED | C11 Email Draft Approval |
| SendExecution.status | CREATED, READY, SENT, FAILED, CANCELLED | C11/C14 Send Execution |
| SearchJob.status | QUEUED, … CANCELLED | C10 Acquisition |

### 2.3 System Boundaries (Pre-C16)

| Boundary | Rule | Enforced by |
|----------|------|-------------|
| CRM ↔ Connector | CRM owns records; Connector is HTTP client | `BOUNDARIES.md` §1 |
| Connector ↔ Engine | Connector uses vendored contracts only | `BOUNDARIES.md` §2 |
| CRM ↔ Engine | One-way projection; no CRM→Engine writes | `BOUNDARIES.md` §2 |
| Extension ↔ Python | Extension never imports Python; Connector never writes PHP/SQL | `BOUNDARIES.md` §1 |
| Opportunity creation | No automatic creation from proposals | `ChituSyncService` + test_extension_skeleton.py |
| Email content | Subject/body not stored on Lead | `BOUNDARIES.md` §7 |

### 2.4 C16 Must Preserve

| Capability | Component | Must Not Touch |
|------------|-----------|----------------|
| C10 Research lifecycle | SearchStrategy, SearchJob, ProspectPool, ResearchEvidence | Entity defs, services, hooks |
| C11 Draft/Approval boundary | DraftApproval, DraftApproval.status state machine | Entity defs, services, hooks |
| C14 Email lifecycle | EmailEvent, SendExecution, ReplyEvent, BrevoEmailEventSyncService | Entity defs, services, hooks |
| C14.3 Result Projection | EmailLifecycleProjectionService | Service logic |
| S01 Release Integrity | Extension packaging, manifest.json, build pipeline | Build scripts |

---

## 3. Domain Model

### 3.1 Entities and Ownership

#### 3.1.1 Quote

**Owner:** CRM Extension (EspoCRM Prospecting module)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | Yes | Display name; auto-generated from quoteNumber |
| `quoteNumber` | varchar(32) | Yes | Unique formatted number (QT-YYYY-NNNN) |
| `opportunityId` | link | No | Link to native Opportunity |
| `leadId` | link | No | Direct link to Lead (when no Opportunity exists) |
| `status` | enum | Yes | See §4 State Machine |
| `currency` | varchar(3) | Yes | ISO 4217 (default: USD) |
| `subtotal` | currency | Yes | Sum of line items before tax |
| `taxRate` | float | No | Tax percentage (e.g., 10.00) |
| `taxAmount` | currency | No | Calculated tax |
| `total` | currency | Yes | Grand total |
| `validUntil` | date | Yes | Quote expiration date |
| `notes` | text | No | Internal notes |
| `termsAndConditions` | text | No | Customer-facing terms |
| `createdAt` | datetime | Read-only | Auto |
| `modifiedAt` | datetime | Read-only | Auto |
| `createdBy` | link (User) | Read-only | Auto |
| `modifiedBy` | link (User) | Read-only | Auto |
| `assignedUser` | link (User) | No | Owner |
| `teams` | linkMultiple (Team) | No | Team access |

**Links:**
- `opportunity`: belongsTo Opportunity (optional — nullable)
- `lead`: belongsTo Lead (optional — nullable; mutually exclusive with opportunity in business logic but not enforced at schema level)
- `quoteItems`: hasMany QuoteItem
- `approvals`: hasMany Approval
- `proformaInvoices`: hasMany ProformaInvoice
- `createdBy`, `modifiedBy`, `assignedUser`: belongsTo User
- `teams`: hasMany Team

**Constraints:**
- At least one of `opportunityId` or `leadId` must be set (business rule; enforced in Service layer, not schema)
- `quoteNumber` is unique within the tenant
- `validUntil` must be later than `createdAt`

#### 3.1.2 QuoteItem

**Owner:** CRM Extension

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | Yes | Line item description |
| `product` | varchar(255) | No | Product/service identifier |
| `description` | text | No | Detailed description |
| `quantity` | float | Yes | Default: 1 |
| `unitPrice` | currency | Yes | Price per unit |
| `discount` | float | No | Discount percentage (0–100) |
| `lineTotal` | currency | Yes | quantity × unitPrice × (1 − discount/100) |
| `sortOrder` | int | No | Display ordering |
| `quoteId` | link | Yes | Parent Quote |

**Links:**
- `quote`: belongsTo Quote, foreign: quoteItems

**Constraints:**
- `quantity` > 0
- `unitPrice` ≥ 0
- `discount` ∈ [0, 100]

#### 3.1.3 ProformaInvoice

**Owner:** CRM Extension

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | Yes | Display name; auto-generated from piNumber |
| `piNumber` | varchar(32) | Yes | Unique formatted number (PI-YYYY-NNNN) |
| `quoteId` | link | Yes | Source Quote |
| `status` | enum | Yes | See §4 State Machine |
| `currency` | varchar(3) | Yes | Inherited from Quote |
| `subtotal` | currency | Yes | Snapshot from Quote |
| `taxAmount` | currency | No | Snapshot from Quote |
| `total` | currency | Yes | Snapshot from Quote |
| `paymentTerms` | text | No | e.g., "Net 30", "50% upfront" |
| `shippingTerms` | text | No | e.g., "FOB", "CIF" |
| `issuedAt` | datetime | No | When PI was formally issued |
| `sentAt` | datetime | No | When PI was sent to customer |
| `paidAt` | datetime | No | When payment was confirmed |
| `notes` | text | No | Internal notes |
| `quoteSnapshot` | jsonObject | No | Immutable snapshot of Quote items at issuance time |

**Links:**
- `quote`: belongsTo Quote, foreign: proformaInvoices

**Constraints:**
- `piNumber` is unique within the tenant
- A Quote may have multiple PIs (e.g., revisions)

#### 3.1.4 Approval

**Owner:** CRM Extension

**Design Decision:** C16 introduces a **new, separate** `Approval` entity — it does NOT reuse `DraftApproval`. Rationale: `DraftApproval` is semantically bound to email draft approval (C11). Quote/PI approval has different:
- State transitions (PENDING → APPROVED/REJECTED, plus escalation paths)
- Linked entities (Quote, ProformaInvoice — not Lead)
- Audit fields (approvalType, decision, requestedBy)
- Permission boundaries (Finance may approve PI but not email drafts)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | varchar(255) | Yes | Display name |
| `approvalType` | enum | Yes | QUOTE | PI |
| `entityType` | varchar(100) | Yes | Polymorphic: "Quote" or "ProformaInvoice" |
| `entityId` | varchar(36) | Yes | Polymorphic FK |
| `status` | enum | Yes | PENDING, APPROVED, REJECTED (no ESCALATED — handled via new record) |
| `requestedBy` | link (User) | Yes | Who requested approval |
| `approver` | link (User) | No | Who approved/rejected (set on decision) |
| `decision` | enum | No | APPROVED | REJECTED (set on decision) |
| `reason` | text | No | Decision rationale |
| `createdAt` | datetime | Read-only | Auto |
| `decidedAt` | datetime | No | When decision was made |

**Links:**
- `quote`: belongsTo Quote (when entityType = "Quote"), foreign: approvals
- `proformaInvoice`: belongsTo ProformaInvoice (when entityType = "PI"), foreign: approvals
- `requestedBy`, `approver`: belongsTo User

**Constraint:** `entityType` + `entityId` form a logical foreign key. EspoCRM does not natively support polymorphic relations; implement as two optional link fields (`quoteId`, `proformaInvoiceId`) with exactly one required at the Service layer.

#### 3.1.5 PDF Artifact (Design Concept — Not a Database Entity)

The PDF artifact is a **filesystem artifact** (see §5 and §6), not an EspoCRM entity. Its lifecycle is tracked via fields on Quote and ProformaInvoice:

- `Quote.pdfGeneratedAt` — datetime, nullable
- `Quote.pdfStoragePath` — varchar, nullable (internal reference)
- `ProformaInvoice.pdfGeneratedAt` — datetime, nullable
- `ProformaInvoice.pdfStoragePath` — varchar, nullable (internal reference)

### 3.2 Ownership Decision Matrix

| Entity | CRM Ownership | Connector Ownership | Document Ownership | Rationale |
|--------|:---:|:---:|:---:|-----------|
| **Quote** | ✅ | ❌ | ❌ | CRM-native business record; user-authored |
| **QuoteItem** | ✅ | ❌ | ❌ | Child of Quote; CRM-owned |
| **ProformaInvoice** | ✅ | ❌ | ❌ | CRM-native financial record; derived from Quote |
| **Approval** | ✅ | ❌ | ❌ | CRM workflow; human decision |
| **PDF generation logic** | ❌ | ❌ | ✅ | Dedicated document service (see §5) |
| **PDF storage** | ❌ | ❌ | ✅ | Filesystem with CRM attachment reference (see §6) |
| **Numbering sequence** | ✅ | ❌ | ❌ | CRM manages sequence counters (see §7) |
| **Quote→PI derivation** | ✅ | ❌ | ❌ | Business logic in CRM Service layer |
| **External service integration** | ❌ | ✅ | ❌ | Connector handles outbound HTTP (e.g., PDF service API) |

**Key Principle:** CRM owns the **what** (data, state, business rules). Document service owns the **how** (rendering). Connector owns the **transport** (HTTP). This mirrors the existing C10 pattern: CRM owns SearchStrategy/SearchJob, Connector owns the Worker/Provider transport.

---

## 4. State Machine Design

### 4.1 Quote State Machine

```
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │ submitForReview()
                           ▼
                    ┌──────────────┐
                    │  IN_REVIEW   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │ requestRevision()       │ approve()
              ▼                         ▼
       ┌──────────────┐         ┌──────────────┐
       │    DRAFT     │         │   APPROVED   │
       └──────────────┘         └──────┬───────┘
                                       │ send()
                                       ▼
                                ┌──────────────┐
                                │     SENT     │
                                └──────┬───────┘
                                       │
                          ┌────────────┼────────────┐
                          │ accepted()│ rejected()  │ expire()
                          ▼            ▼            ▼
                   ┌───────────┐ ┌───────────┐ ┌───────────┐
                   │ ACCEPTED  │ │ REJECTED  │ │  EXPIRED  │
                   └───────────┘ └───────────┘ └───────────┘
```

**States:** `DRAFT`, `IN_REVIEW`, `APPROVED`, `SENT`, `ACCEPTED`, `REJECTED`, `EXPIRED`

**Transitions:**

| From | To | Trigger | Who Can Execute | Guards |
|------|----|---------|-----------------|--------|
| (new) | DRAFT | create | Sales | None |
| DRAFT | IN_REVIEW | submitForReview | Sales, Manager | Quote has ≥1 QuoteItem; total > 0 |
| IN_REVIEW | APPROVED | approve | Manager | All required fields complete |
| IN_REVIEW | DRAFT | requestRevision | Manager | Revision reason required |
| APPROVED | SENT | send | Sales | PDF must be generated (see §5.4) |
| SENT | ACCEPTED | accept | Sales, Manager | None |
| SENT | REJECTED | reject | Sales, Manager | Rejection reason required |
| SENT | EXPIRED | expire | System (cron) / Admin | validUntil < now() AND not yet ACCEPTED/REJECTED |
| DRAFT | EXPIRED | expire | System (cron) / Admin | validUntil < now() |

**Rollback Policy:**
- `IN_REVIEW → DRAFT`: Allowed (revision loop). Does NOT reset the Quote; preserves line items.
- `SENT → DRAFT`: **NOT allowed**. Once sent to customer, the Quote is immutable except for ACCEPTED/REJECTED/EXPIRED terminal states.
- `APPROVED → DRAFT`: **NOT allowed**. Approved Quotes must be sent or explicitly cancelled via a new revision Quote.
- Terminal states (`ACCEPTED`, `REJECTED`, `EXPIRED`): **No exit**. Create a new Quote for re-engagement.

**Idempotency:**
- `submitForReview` on an already IN_REVIEW Quote: no-op (success, no state change).
- `approve` on an already APPROVED Quote: no-op.
- `send` on an already SENT Quote: no-op (does not re-send).
- `accept`/`reject` on a non-SENT Quote: error.

### 4.2 ProformaInvoice State Machine

```
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │ issue()
                           ▼
                    ┌──────────────┐
                    │    ISSUED    │
                    └──────┬───────┘
                           │ send()
                           ▼
                    ┌──────────────┐
                    │     SENT     │
                    └──────┬───────┘
                           │
                           │ markPaid()
                           ▼
                    ┌──────────────┐
                    │     PAID     │
                    └──────────────┘
```

**States:** `DRAFT`, `ISSUED`, `SENT`, `PAID`, `VOID`

**Transitions:**

| From | To | Trigger | Who Can Execute | Guards |
|------|----|---------|-----------------|--------|
| (new) | DRAFT | create | Sales, Finance | Must have linked Quote (APPROVED or ACCEPTED) |
| DRAFT | ISSUED | issue | Finance | All fields complete; PI number assigned |
| ISSUED | SENT | send | Sales, Finance | PDF generated |
| SENT | PAID | markPaid | Finance | Payment confirmed |
| Any non-terminal | VOID | void | Finance, Admin | Void reason required; PI cannot be un-voided |

**Rollback Policy:**
- `SENT → ISSUED`: **NOT allowed**. Sent PIs are immutable.
- `PAID → SENT`: **NOT allowed**. Payment is terminal.
- `VOID`: Terminal state.

**Idempotency:**
- `issue` on ISSUED PI: no-op.
- `markPaid` on PAID PI: no-op.
- `send` on SENT PI: no-op (does not re-send).

### 4.3 Approval State Machine

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

**States:** `PENDING`, `APPROVED`, `REJECTED`

**Transitions:**

| From | To | Trigger | Who Can Execute | Guards |
|------|----|---------|-----------------|--------|
| (new) | PENDING | create (auto on entity submission) | System | Generated when Quote reaches IN_REVIEW or PI reaches ISSUED |
| PENDING | APPROVED | approve | Manager (Quote), Finance (PI) | Approver must have appropriate role |
| PENDING | REJECTED | reject | Manager (Quote), Finance (PI) | Reason required |

**Rollback Policy:**
- `APPROVED → PENDING`: **NOT allowed**. To reverse an approval, create a new PENDING approval record.
- `REJECTED → PENDING`: **NOT allowed**. Re-submission creates a new Approval.

**Idempotency:**
- `approve` on APPROVED Approval: no-op.
- `reject` on REJECTED Approval: no-op.

### 4.4 Cross-Entity State Consistency Rules

| Rule | Enforcement |
|------|-------------|
| Quote can only reach APPROVED if its latest Approval is APPROVED | Service layer |
| PI can only be created from Quote in APPROVED or ACCEPTED state | Service layer |
| PI can only reach ISSUED if its associated Quote is APPROVED or ACCEPTED | Service layer |
| Quote cannot transition to DRAFT if an ISSUED/SENT PI exists (unless PI is VOID) | Service layer |
| Approval must target exactly one entity (Quote or PI) | Service layer |

---

## 5. PDF Architecture Decision

### 5.1 Options Evaluated

#### Option A: CRM Backend Generated PDF

Generate PDFs server-side within the EspoCRM PHP process using a library (e.g., TCPDF, Dompdf, mPDF).

| Criterion | Assessment |
|-----------|------------|
| Security | ⚠️ PHP process has DB access; PDF generation increases attack surface |
| Maintenance | ⚠️ PHP PDF libraries are maintenance-heavy; styling is fragile |
| Deployment | ✅ Single artifact; no additional service |
| EspoCRM Compatibility | ⚠️ EspoCRM has built-in PDF templates but they are designed for entity print views, not complex Quote/PI layouts |
| Template Management | ⚠️ Templates would be PHP/EspoCRM-specific; hard to version |

#### Option B: Connector Generated PDF

Generate PDFs in the Python connector process.

| Criterion | Assessment |
|-----------|------------|
| Security | ✅ Isolated in Python process; no DB access |
| Maintenance | ✅ Python PDF ecosystem (WeasyPrint, ReportLab) is mature |
| Deployment | ⚠️ Requires Python runtime on or near the CRM server |
| EspoCRM Compatibility | ❌ Connector is a CLI/HTTP client; not designed for on-demand document generation |
| Template Management | ✅ Jinja2/HTML templates; version-controlled alongside connector code |

#### Option C: Dedicated Document Service

A standalone microservice (e.g., Gotenberg, custom Node.js/ Puppeteer service) that accepts HTML + data and returns PDF.

| Criterion | Assessment |
|-----------|------------|
| Security | ✅ Fully isolated; no CRM or Connector access |
| Maintenance | ✅ Single responsibility; focused codebase |
| Deployment | ⚠️ Additional service to deploy, monitor, and scale |
| EspoCRM Compatibility | ✅ Language-agnostic; HTTP API |
| Template Management | ✅ HTML/CSS templates; any template engine |

#### Option D: Template Rendering Pipeline

A pipeline where CRM prepares data → Connector enriches → Document Service renders.

| Criterion | Assessment |
|-----------|------------|
| Security | ✅ Defense in depth; each stage isolated |
| Maintenance | ⚠️ Three components to maintain |
| Deployment | ❌ Most complex; three-component coordination |
| EspoCRM Compatibility | ✅ Each component uses its native strengths |
| Template Management | ✅ Templates live in document service |

### 5.2 Decision: Option C — Dedicated Document Service

**Recommended approach:** Dedicated Document Service.

**Rationale:**
1. **Security isolation** — The document service has zero access to CRM data or connector secrets. It receives only the data needed for rendering.
2. **Single responsibility** — PDF generation is a distinct concern from CRM workflow (CRM extension) and external API integration (connector).
3. **Template portability** — HTML/CSS templates are framework-agnostic and can be previewed outside the CRM.
4. **EspoCRM compatibility** — EspoCRM already has an HTTP client pattern (used by the connector). CRM calls the document service REST API.
5. **Deployment flexibility** — In development, a lightweight Docker container (e.g., Gotenberg) suffices. In production, it can be independently scaled.

**Rejected alternatives:**
- **Option A (CRM backend PDF):** Rejected due to PHP PDF library fragility and tight coupling to EspoCRM's PDF engine, which is designed for simple entity print views, not multi-page Quote/PI layouts with line items and conditional logic.
- **Option B (Connector PDF):** Rejected because the connector is designed as a sync/adapter layer, not an on-demand rendering service. Adding PDF generation would bloat its responsibility.
- **Option D (Pipeline):** Rejected as over-engineered for the current scope. The connector has no enrichment role in PDF generation. CRM → Document Service is sufficient.

### 5.3 Document Service Requirements

- Accept HTTP POST with JSON payload (Quote/PI data + template identifier)
- Return PDF binary with `Content-Type: application/pdf`
- Support HTML/CSS templates with variable substitution
- Support multi-language templates (future)
- Stateless — no session, no database
- Authentication via API key (same pattern as connector → CRM)

### 5.4 PDF Lifecycle

**PDFs are immutable artifacts.** Once generated for a given Quote/PI version, the PDF is stored and never regenerated for that version.

| Event | PDF Action |
|-------|-----------|
| Quote reaches APPROVED | Generate Quote PDF on first `send()` |
| Quote PDF requested before APPROVED | Generate "DRAFT" watermarked preview |
| Quote revised (new Quote from old) | New Quote gets new PDF |
| PI reaches ISSUED | Generate PI PDF on `send()` |
| Quote items modified after PDF generated | PDF is NOT regenerated; Quote must be re-approved and re-sent (creates new version if already SENT) |

**Versioning:** PDFs are versioned by `quoteId + pdfGeneratedAt` timestamp. The `pdfStoragePath` field stores the reference. Older PDFs remain accessible for audit.

**Regeneration:** Explicit regeneration is allowed only for Quotes in DRAFT state. Regeneration for APPROVED/SENT Quotes is prohibited — the PDF is the customer-facing artifact and must not change after sending.

---

## 6. Storage Strategy

### 6.1 Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Database blob** | Store PDF binary in EspoCRM entity field | Simple; co-located with metadata | DB bloat; slow backups; EspoCRM field size limits |
| **B: Filesystem** | Store PDFs on server filesystem | Simple; fast I/O; no DB overhead | Not cloud-portable; backup coupling |
| **C: Object storage (S3)** | Store in S3-compatible bucket | Cloud-native; scalable; independent backup | Additional infrastructure; latency on first access |
| **D: EspoCRM attachment** | Use EspoCRM's built-in Attachment entity | Native UI; access control; familiar UX | Attachment entity is generic; no structured PDF metadata |

### 6.2 Decision: Option D (Primary) + Option B (Fallback)

**Primary: EspoCRM Attachment mechanism.** Quote/PI PDFs are stored as EspoCRM `Attachment` records linked to the Quote/ProformaInvoice entity.

**Rationale:**
1. **Native ACL** — EspoCRM's attachment permissions inherit from the parent entity. No custom access control needed.
2. **UI integration** — Users can view/download PDFs through the standard EspoCRM attachment panel.
3. **Backup consistency** — Attachments are part of EspoCRM's backup/recovery path.
4. **Metadata** — Attachment entity carries name, type, size, and timestamps natively.
5. **Proven pattern** — EspoCRM extensions commonly use the Attachment mechanism for generated documents.

**Fallback: Filesystem path reference.** The `pdfStoragePath` field on Quote/PI stores the filesystem path for:
- Direct filesystem access by the document service
- Bulk export scenarios
- Migration to object storage (future)

**Implementation pattern:**
```
1. CRM → Document Service: POST /render { template, data }
2. Document Service → CRM: PDF binary
3. CRM: Save as EspoCRM Attachment (parentType: "Quote", parentId: quoteId)
4. CRM: Optionally write to configured filesystem path for direct access
5. CRM: Update Quote.pdfStoragePath with filesystem reference
```

### 6.3 Storage Location by Artifact Type

| Artifact | Primary Storage | Secondary |
|----------|----------------|-----------|
| Quote PDF | EspoCRM Attachment (Quote) | Filesystem (pdfStoragePath) |
| PI PDF | EspoCRM Attachment (ProformaInvoice) | Filesystem (pdfStoragePath) |
| Approval evidence attachments | EspoCRM Attachment (Approval) | N/A |

---

## 7. Numbering Convention

### 7.1 Quote Numbering

**Format:** `QT-YYYY-NNNN`

- `QT` — Fixed prefix for Quote
- `YYYY` — Year of creation
- `NNNN` — Zero-padded sequential number (0001–9999), resetting annually

**Examples:** `QT-2026-0001`, `QT-2026-0142`

**Sequence owner:** CRM Extension. A dedicated `QuoteNumberingService` manages a `sequence` table or uses EspoCRM's auto-increment pattern.

### 7.2 ProformaInvoice Numbering

**Format:** `PI-YYYY-NNNN`

- `PI` — Fixed prefix for Proforma Invoice
- `YYYY` — Year of issuance
- `NNNN` — Zero-padded sequential number (0001–9999), resetting annually

**Examples:** `PI-2026-0001`, `PI-2026-0089`

**Sequence owner:** CRM Extension. Separate sequence from Quote numbering.

### 7.3 Concurrency Handling

**Approach: Database-level atomic increment.**

In EspoCRM/MySQL, the sequence is managed via a dedicated `numbering_sequence` table:

```sql
CREATE TABLE numbering_sequence (
  sequence_key VARCHAR(64) NOT NULL,   -- e.g., 'QUOTE-2026', 'PI-2026'
  current_value INT NOT NULL DEFAULT 0,
  PRIMARY KEY (sequence_key)
);
```

Acquisition of the next number uses `SELECT ... FOR UPDATE` or `UPDATE ... SET current_value = LAST_INSERT_ID(current_value + 1)` within a transaction. This guarantees:
- **Uniqueness** — No two concurrent requests get the same number.
- **Gap tolerance** — Rolled-back transactions create gaps; this is acceptable (standard accounting practice).
- **No external dependency** — No Redis, no distributed lock service required.

**Alternative (EspoCRM-native):** If EspoCRM's ORM does not support raw `SELECT ... FOR UPDATE`, use a file-based lock (`flock()`) on a sequence file, or delegate to a simple increment via `Espo\Core\Utils\Util::generateId()` with a prefix.

### 7.4 Number Assignment Timing

| Entity | Number Assigned At |
|--------|--------------------|
| Quote | On first transition from DRAFT to IN_REVIEW (not on create) |
| ProformaInvoice | On `issue()` transition from DRAFT to ISSUED |

**Rationale:** Drafts that are never submitted should not consume sequence numbers. This also avoids gaps from abandoned drafts.

---

## 8. Integration Boundary

### 8.1 What C16 Explicitly Does NOT Touch

C16 is a **net-new capability**. It does not modify any of the following:

| Component | File(s) | Reason |
|-----------|---------|--------|
| ChituSyncService | `crm-extension/.../Services/ChituSyncService.php` | C10 sync contract; different domain |
| EmailLifecycleProjectionService | `crm-extension/.../Services/EmailLifecycleProjectionService.php` | C14.3 email lifecycle; different domain |
| BrevoEmailEventSyncService | `crm-extension/.../Services/BrevoEmailEventSyncService.php` | C14 email events; different domain |
| SendExecutionBridgeAdapterService | `crm-extension/.../Services/SendExecutionBridgeAdapterService.php` | C11 send execution; different domain |
| DraftApproval entity | `crm-extension/.../entityDefs/DraftApproval.json` | C11 email draft approval; different domain |
| SendExecution entity | `crm-extension/.../entityDefs/SendExecution.json` | C11/C14 send execution; different domain |
| EmailEvent entity | `crm-extension/.../entityDefs/EmailEvent.json` | C14 email events; different domain |
| SearchStrategy / SearchJob / ProspectPool | `crm-extension/.../entityDefs/{SearchStrategy,SearchJob,ProspectPool}.json` | C10 acquisition; different domain |
| Acquisition worker | `chitu-connector/chitu_connector/acquisition/worker.py` | C10 acquisition; Python-side |
| Brevo adapter / retry queue | `chitu-connector/chitu_connector/espocrm_sync/brevo_*.py` | C14 email provider; different domain |
| Manifest / build pipeline | `crm-extension/manifest.json`, `deployment/` | S01 release integrity |

### 8.2 Integration Patterns

C16 uses the same integration patterns established by C10, C11, and C14:

#### 8.2.1 C16 → Existing CRM (Native EspoCRM)

- Quote links to Opportunity (native entity) via standard EspoCRM `link` field.
- Quote links to Lead via standard EspoCRM `link` field.
- No modification to native Opportunity or Lead entities required (only new link fields).

#### 8.2.2 C16 → Connector (Event/Projection Pattern)

C16 does **not** require direct connector involvement. However, future integration points are designed as:

- **Event:** When Quote reaches ACCEPTED, emit a CRM event that the connector can optionally listen for (e.g., to update Lead scoring).
- **Projection:** The connector may read Quote/PI data via EspoCRM REST API for reporting/analytics purposes (read-only).
- **No write path:** The connector never creates or modifies Quote, PI, or Approval records.

#### 8.2.3 C16 → External Document Service (Adapter Pattern)

```
CRM Extension                    Document Service
     │                                 │
     │  POST /api/v1/pdf/render        │
     │  { template, data, apiKey }     │
     │ ──────────────────────────────> │
     │                                 │
     │  200 OK, application/pdf        │
     │ <────────────────────────────── │
     │                                 │
```

- CRM calls the document service via HTTP.
- Authentication: API key in header or body.
- The document service is **stateless** — receives all data needed for rendering.
- Timeout: 30s for PDF generation.

#### 8.2.4 Forbidden Integration Paths

| Path | Status | Reason |
|------|--------|--------|
| Connector → Quote/PI write | ❌ Forbidden | CRM owns Quote/PI data |
| Document Service → CRM write | ❌ Forbidden | One-way rendering only |
| C16 → Email sending | ❌ Forbidden | Email is C14 territory; C16 may trigger email via C14 but never directly |
| C16 → Chitu scoring | ❌ Forbidden | Scoring is external engine territory |
| Auto-create Quote from Lead/Opportunity | ❌ Forbidden | Mirroring C11's `NO_AUTOMATIC_OPPORTUNITY` rule |

---

## 9. Security and Permission Model

### 9.1 Role Design

| Role | Description | Scope |
|------|-------------|-------|
| **Sales** | Creates and manages Quotes; sends to customers | Quote: create, read, update (own), send |
| **Manager** | Approves Quotes; oversees sales pipeline | Quote: read (all), approve; Approval: approve/reject |
| **Finance** | Manages PIs; confirms payments | PI: create, read, update, issue, markPaid; Approval: approve/reject (PI) |
| **Admin** | Full access; system overrides | All: full CRUD |

### 9.2 Permission Matrix

| Action | Sales | Manager | Finance | Admin |
|--------|:-----:|:-------:|:-------:|:-----:|
| **Quote** | | | | |
| Create Quote | ✅ | ✅ | ❌ | ✅ |
| Edit Quote (own, DRAFT) | ✅ | ✅ | ❌ | ✅ |
| Edit Quote (own, IN_REVIEW) | ❌ | ✅ | ❌ | ✅ |
| Edit Quote (any) | ❌ | ❌ | ❌ | ✅ |
| Delete Quote (DRAFT, own) | ✅ | ✅ | ❌ | ✅ |
| Submit for review | ✅ | ✅ | ❌ | ✅ |
| Approve Quote | ❌ | ✅ | ❌ | ✅ |
| Send Quote to customer | ✅ | ✅ | ❌ | ✅ |
| Download PDF (own) | ✅ | ✅ | ✅ | ✅ |
| Download PDF (any) | ❌ | ✅ | ✅ | ✅ |
| **QuoteItem** | | | | |
| Create/Edit (parent DRAFT, own) | ✅ | ✅ | ❌ | ✅ |
| Delete (parent DRAFT, own) | ✅ | ✅ | ❌ | ✅ |
| **ProformaInvoice** | | | | |
| Create PI | ❌ | ❌ | ✅ | ✅ |
| Edit PI (DRAFT) | ❌ | ❌ | ✅ | ✅ |
| Issue PI | ❌ | ❌ | ✅ | ✅ |
| Send PI | ❌ | ✅ | ✅ | ✅ |
| Mark PI as Paid | ❌ | ❌ | ✅ | ✅ |
| Void PI | ❌ | ❌ | ✅ | ✅ |
| Download PI PDF | ✅ | ✅ | ✅ | ✅ |
| **Approval** | | | | |
| View approvals (own requests) | ✅ | ✅ | ✅ | ✅ |
| Approve/Reject (Quote) | ❌ | ✅ | ❌ | ✅ |
| Approve/Reject (PI) | ❌ | ❌ | ✅ | ✅ |

### 9.3 ACL Boundary

**Field-level ACL:**
- `Quote.total`, `Quote.taxAmount`: Read-only for Sales after APPROVED.
- `ProformaInvoice.paidAt`: Write-only for Finance.
- `Approval.decision`, `Approval.reason`: Write-only for approver role on decision.

**Scope-level ACL:**
- Sales: sees own Quotes and assigned team Quotes.
- Manager: sees all Quotes in their team(s).
- Finance: sees all PIs; sees Quote totals for invoicing.
- Admin: sees everything.

**Implementation:** Via EspoCRM's built-in ACL system (Roles, `acl.json` in extension metadata). No custom ACL service required.

### 9.4 Audit Trail

All state transitions on Quote, PI, and Approval are logged via EspoCRM's `ActionHistoryRecord` stream (or a dedicated `C16AuditLog` if granularity beyond built-in stream is needed). Minimum audit fields:
- Entity type + ID
- Old state → New state
- Timestamp
- User ID
- IP address

---

## 10. Implementation Roadmap

### 10.1 Phase Sequence

**No code is implemented in this ADR phase.** The roadmap below is the planned implementation sequence, subject to change based on Phase3S03 planning.

```
C16.1 Domain Entities
├── Quote entity definition (metadata JSON)
├── QuoteItem entity definition (metadata JSON)
├── ProformaInvoice entity definition (metadata JSON)
├── Approval entity definition (metadata JSON)
├── Entity relationships (links)
├── Database indexes
└── CRUD ACL scaffolding (roles + acl.json)
    Status: NOT STARTED

C16.2 Quote Workflow
├── QuoteService (create, submit, approve, send, accept, reject, expire)
├── QuoteItemService (CRUD, line total calculation)
├── QuoteNumberingService (atomic sequence)
├── State transition validation
├── Cross-entity consistency guards
├── Formula hooks (status → timestamp automations)
└── Unit tests (PHP)
    Status: NOT STARTED

C16.3 Approval Workflow
├── ApprovalService (create, approve, reject)
├── Auto-creation hook (Quote IN_REVIEW → Approval PENDING)
├── Approval decision → Quote/PI state propagation
├── Escalation support (timeout-based re-assignment)
└── Unit tests (PHP)
    Status: NOT STARTED

C16.4 PDF Generation
├── Document Service API contract definition
├── CRM-side PDF client (HTTP adapter)
├── Quote PDF template (HTML/CSS)
├── PI PDF template (HTML/CSS)
├── PDF → EspoCRM Attachment storage
├── PDF download endpoint
├── DRAFT watermark rendering
└── Integration tests (CRM + Document Service)
    Status: NOT STARTED

C16.5 PI Workflow
├── ProformaInvoiceService (create, issue, send, markPaid, void)
├── Quote → PI data snapshot
├── PINumberingService
├── PI state transition validation
└── Unit tests (PHP)
    Status: NOT STARTED

C16.6 Integration
├── C16 event emission (Quote ACCEPTED, PI PAID)
├── Connector read-only projection (optional)
├── Document Service deployment config
├── End-to-end smoke tests
└── Extension skeleton test updates (test_extension_skeleton.py)
    Status: NOT STARTED
```

### 10.2 Dependencies Between Phases

```
C16.1 ──► C16.2 ──► C16.3 ──► C16.4 ──► C16.5 ──► C16.6
                           └──────────────► C16.5
```

- C16.2 depends on C16.1 (entities must exist before workflows)
- C16.3 depends on C16.2 (approval hooks into Quote workflow states)
- C16.4 depends on C16.3 (PDF generated after approval)
- C16.5 depends on C16.2 + C16.3 (PI derived from approved Quote; PI has its own approval)
- C16.6 depends on C16.4 + C16.5 (integration after core capabilities are stable)

### 10.3 Estimated Entity/File Count per Phase

| Phase | Entities | Services | Templates | Tests | Other Files |
|-------|----------|----------|-----------|-------|-------------|
| C16.1 | 4 metadata JSON | 0 | 0 | 1 skeleton update | layouts, i18n, scopes, acl |
| C16.2 | 0 | 3 PHP | 0 | 3 PHP test files | formula JSON |
| C16.3 | 0 | 1 PHP | 0 | 2 PHP test files | — |
| C16.4 | 0 | 1 PHP (client) | 2 HTML/CSS | 1 integration test | Document Service config |
| C16.5 | 0 | 2 PHP | 0 | 2 PHP test files | — |
| C16.6 | 0 | 0 | 0 | 2 E2E tests | deployment config |

---

## 11. Unresolved Questions

The following questions are identified but **not resolved** in this ADR. They should be addressed during C16.1 planning or implementation:

| # | Question | Context | Proposed Resolution Path |
|---|----------|---------|--------------------------|
| Q1 | Should Quote support multi-currency conversion rates? | Current design stores a single `currency` per Quote. | Defer to C16.2; likely scope as C16.2+ enhancement. |
| Q2 | Should Approval support multi-level (e.g., Manager → Director → Finance)? | Current design is single-level PENDING → APPROVED/REJECTED. | Defer to C16.3; design Approval to support `approvalLevel` and chaining if needed. |
| Q3 | Should expired Quotes auto-notify the assigned user? | Current design: system cron transitions state; no notification. | Defer to C16.2; use EspoCRM notification/email template system. |
| Q4 | What is the exact Document Service technology choice? | ADR recommends "Dedicated Document Service" but does not prescribe the implementation. | Evaluate Gotenberg vs. Puppeteer vs. WeasyPrint during C16.4; document as a sub-ADR. |
| Q5 | Should the Document Service be a separate repository? | Architectural separation suggests yes; operational simplicity suggests co-location. | Decide at C16.4; if simple enough, include in this repo under `document-service/`. |
| Q6 | What PDF archival/retention policy applies? | ADR says PDFs are immutable but does not define retention. | Define during C16.6; legal/compliance may dictate retention periods. |
| Q7 | Should Quote/PI PDFs be digitally signed? | Current design: no signing. Some jurisdictions require digital signatures on PIs. | Defer; evaluate as C16.5+ enhancement. |
| Q8 | What is the exact concurrency mechanism for numbering? | ADR proposes DB-level atomic increment. EspoCRM ORM may limit raw SQL. | Prototype during C16.2; fall back to file-lock or UUID-based approach if DB lock is unavailable. |

---

## 12. Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D1 | New `Approval` entity; do NOT reuse `DraftApproval` | `DraftApproval` is semantically bound to C11 email draft approval with different fields, links, and permission boundaries | 2026-07-21 |
| D2 | Quote and PI are separate entities (not one entity with a type discriminator) | Different state machines, different numbering, different permission boundaries, different lifecycle | 2026-07-21 |
| D3 | PDF generation is a dedicated external service (Option C) | Security isolation, template portability, single responsibility. Rejected: CRM backend (fragile PHP PDF libs), Connector (wrong responsibility), Pipeline (over-engineered) | 2026-07-21 |
| D4 | PDFs stored as EspoCRM Attachments (Option D) | Native ACL, UI integration, backup consistency. Fallback: filesystem path reference | 2026-07-21 |
| D5 | Numbering: `QT-YYYY-NNNN` / `PI-YYYY-NNNN` with annual reset | Industry standard format; annual reset keeps numbers manageable | 2026-07-21 |
| D6 | Numbers assigned on REVIEW/ISSUE, not on CREATE | Prevents abandoned drafts from consuming sequence numbers | 2026-07-21 |
| D7 | Quote supports both Opportunity and Lead as parent (optional, mutually exclusive in business logic) | Flexibility: some Quotes originate from Leads before Opportunity conversion | 2026-07-21 |
| D8 | PI captures a `quoteSnapshot` at issuance time | Immutability: PI totals must not change if Quote is later modified | 2026-07-21 |
| D9 | Rollback restricted: SENT → DRAFT and APPROVED → DRAFT not allowed | Customer-facing artifacts must be immutable; create new revision instead | 2026-07-21 |
| D10 | Idempotent state transitions (no-op for already-in-target-state) | Prevents duplicate side effects from retry or concurrent requests | 2026-07-21 |
| D11 | C16 does not auto-create Quotes from Lead/Opportunity | Mirrors C11 `NO_AUTOMATIC_OPPORTUNITY` rule; Quote creation is an explicit human decision | 2026-07-21 |
| D12 | Connector never writes Quote/PI/Approval records | CRM owns all C16 record data; connector may read for reporting only | 2026-07-21 |

---

## Appendix A: File Manifest (Planned)

All paths relative to `crm-extension/files/custom/Espo/Modules/Prospecting/`.

```
Resources/
  metadata/
    entityDefs/
      Quote.json                          # C16.1
      QuoteItem.json                      # C16.1
      ProformaInvoice.json                # C16.1
      Approval.json                       # C16.1
    clientDefs/
      Quote.json                          # C16.1
      QuoteItem.json                      # C16.1
      ProformaInvoice.json                # C16.1
      Approval.json                       # C16.1
    scopes/
      Quote.json                          # C16.1
      QuoteItem.json                      # C16.1
      ProformaInvoice.json                # C16.1
      Approval.json                       # C16.1
    acl.json                              # C16.1 (update)
  Services/
    QuoteService.php                      # C16.2
    QuoteItemService.php                  # C16.2
    QuoteNumberingService.php             # C16.2
    ApprovalService.php                   # C16.3
    PdfClientService.php                  # C16.4
    ProformaInvoiceService.php            # C16.5
    PINumberingService.php                # C16.5
  Formulas/
    QuoteStatusTimestamps.json            # C16.2
```

## Appendix B: Related Documents

- [BOUNDARIES.md](BOUNDARIES.md) — System boundaries (C10, C11, C14, Connector)
- [DATA_FLOW.md](DATA_FLOW.md) — Data flow diagrams and sync pipeline
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) — Implemented components and entity map
- [MODULES.md](MODULES.md) — Module structure and cross-module data ownership
- [ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md](ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md) — Original extension architecture plan
- [EXTENSION_STRUCTURE_AUDIT_REPORT.md](EXTENSION_STRUCTURE_AUDIT_REPORT.md) — Latest extension audit
- [PHASE3S02_ARCHITECTURE_READINESS_REVIEW.md](../PHASE3S02_ARCHITECTURE_READINESS_REVIEW.md) — S02 architecture readiness

---

*End of ADR. No code implemented. Design freeze only.*
