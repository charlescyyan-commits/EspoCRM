# Phase3C11.0 — Persistence Architecture Approval Review

> **Date**: 2026-07-14
> **Review Type**: Architecture Design Review — read-only, no implementation
> **Repository**: D:\EspoCRM-Production (branch: `master`, HEAD: `a4b0e6e`)
> **Extension Version**: 1.9.5-alpha
> **Precondition**: C10 Outreach Lifecycle frozen. C10.6 Evidence Production Alignment complete.

---

## Executive Summary

| Review Dimension | Verdict |
|------------------|---------|
| 1. Source of Truth Architecture | **HYBRID** — CRM entities for human-visible state; connector owns execution logic |
| 2. CRM Projection Boundary | **PROJECTION** — peEmail* fields are derived views, not canonical state |
| 3. DraftStore Design | **APPROVED** — Protocol + re-generation-backed reference implementation |
| 4. Persistence Entity Model | **APPROVED** — 3 new CRM entities, 0 new databases |
| 5. Idempotency Boundary | **APPROVED** — 5 unique keys at database level |
| 6. Worker/Retry Compatibility | **FORWARD-COMPATIBLE** — schema预留, no worker implementation |
| 7. EspoCRM Native Alignment | **APPROVED** — CRM entities for human-facing state; connector domain for mechanics |

**Overall Verdict: APPROVED WITH CONDITIONS**

The C11 Persistence Architecture is sound. All C10 Protocol seams are preserved. No C10 contract is modified. No new database is introduced. The 3 proposed CRM entities leverage EspoCRM's native ACL, API, workflow, and audit capabilities. Five conditions must be satisfied before C11 implementation begins.

---

## 1. Current C10 Boundary (Pre-C11 Baseline)

### 1.1 What Exists Today

```
┌──────────────────────────────────────────────────────┐
│  CONNECTOR (Python) — ALL IN-MEMORY                  │
│                                                      │
│  C09: EmailDraft (immutable dataclass)               │
│       ├── subject, body                              │
│       ├── evidence_references                        │
│       ├── personalization_references                 │
│       ├── score_tier, recommended_product            │
│       └── qualification_status                       │
│                                                      │
│  C10.1: DraftApproval (InMemoryHumanApprovalRegistry)│
│       ├── draft_id, approval_id                      │
│       ├── status: DRAFT_READY → PENDING_REVIEW       │
│       │         → APPROVED → READY_TO_SEND           │
│       │         → REJECTED (terminal)                │
│       ├── reviewer_id, rejection_reason              │
│       └── audit_trace: ApprovalAuditTrace[]          │
│                                                      │
│  C10.0-B: SendRequest / SendAttempt                  │
│       (InMemorySendIdempotencyRegistry)              │
│       ├── idempotency_key: SHA-256(draft,lead,       │
│       │   request,provider,version)                  │
│       └── state: CREATED→READY→PROCESSING→SENT/FAILED│
│                                                      │
│  C10.2-C10.3: SendExecution                          │
│       (InMemorySendExecutionRegistry)                │
│       ├── approval_id → send_request → provider      │
│       └── state: READY_TO_SEND→SUBMITTED→PROCESSING  │
│                  →SENT/FAILED                        │
│                                                      │
│  C10.4: ReplyEvent (InMemoryReplyEventRegistry)      │
│       ├── reply_event_id: SHA-256(content)           │
│       ├── original_send_trace preserved              │
│       └── status: SENT/REPLIED/BOUNCED/UNSUBSCRIBED  │
│                                                      │
│  ALL REGISTRIES: Protocol-based seams                │
│  ALL: threading.RLock, frozen dataclasses            │
│  ZERO: CRM writes, network calls, real providers     │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  CRM (EspoCRM PHP) — PERSISTENT                      │
│                                                      │
│  Lead.peEmailStatus: enum(NONE, DRAFT_READY,         │
│    APPROVED, SENT, REPLIED, BOUNCED)                 │
│  Lead.peLastEmailDate: datetime                      │
│  Lead.peEmailCampaignName: varchar(255)               │
│  Lead.peEmailReplyStatus: varchar(64) ← no enum      │
│                                                      │
│  ResearchEvidence: C10.6 identity index active        │
│  EmailEvent: Brevo append-only ingestion             │
│                                                      │
│  ZERO C10 entities: no DraftApproval, SendExecution, │
│    or ReplyEvent in CRM                              │
└──────────────────────────────────────────────────────┘
```

### 1.2 C10 Architecture Audit — 3 HIGH Risks Confirmed

From `PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md` (2026-07-14):

| Risk | Severity | Description |
|------|----------|-------------|
| RISK-1 | **HIGH** | C10 state has no CRM persistence — all in-memory, lost on restart |
| RISK-2 | **HIGH** | EmailLifecycleSyncService and C10 execution are disconnected systems |
| RISK-3 | **HIGH** | No DraftStore abstraction — C10 modules reference draft_id but cannot retrieve content |

These 3 risks define C11's minimum scope.

### 1.3 Gap: Two Disconnected Status Systems

| State | System A: CRM peEmailStatus | System B: Python C10 |
|-------|---------------------------|----------------------|
| Draft ready | DRAFT_READY (via C09 campaign_projection) | ApprovalStatus.DRAFT_READY |
| In review | **NOT IN CRM** | ApprovalStatus.PENDING_REVIEW |
| Approved | APPROVED (via EmailLifecycleSyncService) | ApprovalStatus.APPROVED |
| Ready to send | **NOT IN CRM** | ApprovalStatus.READY_TO_SEND |
| Sent | SENT (via EmailLifecycleSyncService) | SendExecutionState.SENT |
| Send failed | **NOT IN CRM** | SendExecutionState.FAILED |
| Replied | REPLIED (via EmailLifecycleSyncService) | ReplyStatus.REPLIED |
| Bounced | BOUNCED (via EmailLifecycleSyncService) | ReplyStatus.BOUNCED |

**Three enum values missing from CRM peEmailStatus**: `PENDING_REVIEW`, `READY_TO_SEND`, `SEND_FAILED`.

---

## 2. Recommended C11 Architecture

### 2.1 Source of Truth — Hybrid Model

```
┌─────────────────────────────────────────────────────────┐
│  CRM (EspoCRM) — SOURCE OF TRUTH                        │
│                                                         │
│  Human-facing, persistent entities:                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ DraftApproval (NEW C11 ENTITY)                   │  │
│  │   draft_id, lead_id, status, reviewer_id,        │  │
│  │   rejection_reason, audit_trace                  │  │
│  │   ACL: Admin CRUD, Sales Manager read+approve,   │  │
│  │        Integration Bot CRUD                       │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SendExecution (NEW C11 ENTITY)                   │  │
│  │   send_request_id, approval_id, lead_id,         │  │
│  │   provider_name, state, result_status,           │  │
│  │   send_attempt_id, reason_code, audit_trace      │  │
│  │   ACL: Admin read, Integration Bot CRUD          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ReplyEvent (NEW C11 ENTITY)                      │  │
│  │   reply_event_id, lead_id, draft_id,             │  │
│  │   send_attempt_id, thread_id, reply_status,      │  │
│  │   original_send_trace (JSON)                     │  │
│  │   ACL: Admin read, Integration Bot CRUD          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Lead (EXISTING, EXTENDED):                              │
│    peEmailStatus: +PENDING_REVIEW, READY_TO_SEND,       │
│                   SEND_FAILED                            │
│    peEmailReplyStatus: → enum(ReplyStatus)               │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (existing Prospecting routes)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  CONNECTOR (Python) — EXECUTION OWNER                   │
│                                                         │
│  Protocol implementations backed by CRM REST:           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ EspoCRMDraftApprovalRegistry                     │  │
│  │   implements HumanApprovalRegistry Protocol      │  │
│  │   → POST/GET/PUT /Prospecting/approval/*         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ EspoCRMSendExecutionRegistry                     │  │
│  │   implements SendExecutionRegistry Protocol      │  │
│  │   → POST/GET/PUT /Prospecting/execution/*        │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ EspoCRMReplyEventRegistry                        │  │
│  │   implements ReplyEventRegistry Protocol         │  │
│  │   → POST/GET /Prospecting/reply-event/*          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Domain-only (NOT in CRM):                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ SendIdempotencyRegistry                          │  │
│  │   → Connector-side SQLite or CRM entity TBD      │  │
│  │   (internal mechanics, not human-facing)         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ DraftStore (NEW Protocol)                        │  │
│  │   → Re-generation from C09 facts (reference)     │  │
│  │   → CRM-backed (future)                          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ALL Protocols preserved — in-memory impls retained     │
│  for offline contract tests.                            │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Rationale for Hybrid Model

**Why CRM entities for DraftApproval, SendExecution, ReplyEvent:**

1. **Single database**: The workspace already uses EspoCRM as its only persistent store. Adding a second database (SQLite, Postgres) creates deployment complexity, backup fragmentation, and operational toil without justification.

2. **Built-in capabilities**: EspoCRM provides ACL (who can approve?), API (REST endpoints auto-generated), UI (list/detail views with zero frontend code), workflow hooks (auto-create Tasks on status change), audit fields (createdAt, modifiedAt, createdBy, modifiedBy), and relationship traversal (Lead → Approvals, Lead → SendExecutions).

3. **Human visibility**: Approval requires a human reviewer. That reviewer already works in EspoCRM. The approval record must be visible in CRM for them to act on it. Send history and reply events are operational data that CRM users need to see.

4. **Protocol preservation**: The C10 Python `HumanApprovalRegistry`, `SendExecutionRegistry`, and `ReplyEventRegistry` Protocols are interfaces — the in-memory implementations can be swapped for REST-backed implementations without changing any C10 business logic.

**Why NOT CRM entities for SendIdempotencyRegistry:**

1. **Internal mechanics**: Send request reservation is a connector-internal idempotency concern. CRM users never interact with it directly.
2. **Performance**: Idempotency checks are high-frequency (every send attempt). CRM REST overhead is acceptable for state transitions but not for every idempotency lookup.
3. **Simplicity**: Can be a SQLite file in the connector workspace or a lightweight CRM entity. Defer this decision to C11 implementation — the Protocol seam allows either.

**Why NOT CRM entity for EmailDraft:**

1. **Size**: Drafts contain full subject/body text, evidence references, and personalization data — potentially kilobytes each.
2. **Re-generability**: Drafts are deterministically generated from source facts (OutreachInput). A DraftStore that re-generates from C09 facts is always consistent with the current evidence and score state.
3. **Immutability reference**: The draft_id + content hash provides integrity without storing the full content in CRM.

---

## 3. Entity / Data Model Proposal

### 3.1 DraftApproval (CRM Entity)

```
Entity: DraftApproval
Purpose: Human-visible approval record for one immutable draft identity.
         One draft_id → exactly one DraftApproval record.
Ownership: Connector creates (Integration Bot); human reviewer transitions.
Lifecycle: DRAFT_READY → PENDING_REVIEW → APPROVED → READY_TO_SEND
           or PENDING_REVIEW → REJECTED (terminal)

Fields:
  draftId          varchar(128)   UNIQUE NOT NULL   # C09 draft identity
  leadId           varchar(64)    NOT NULL           # FK → Lead.id
  status           enum           NOT NULL           # DRAFT_READY|PENDING_REVIEW|
                                                     # APPROVED|REJECTED|READY_TO_SEND
  reviewerId       varchar(128)   NULL               # CRM user ID who decided
  rejectionReason  text           NULL               # Required when REJECTED
  approvalVersion  varchar(64)    DEFAULT "c10.1-human-approval-v1"

Relationships:
  lead             belongsTo      Lead               # Lead ← approval
  approvals        hasMany        Lead               # (inverse on Lead)

Audit Trail (embedded JSON or separate entity):
  approvalAuditTrail  jsonArray   NOT NULL
    [{who, when, decision, approvalVersion}, ...]

Unique Constraints:
  UNIQUE(draftId)
  UNIQUE(leadId, draftId)  # One approval per draft per lead

EspoCRM Metadata:
  acl: Admin CRUD, Sales Manager read+transition, Integration Bot CRUD
  formula: none required (state machine is in Python)
  layouts: detail (status, reviewer, rejection reason, audit trail)
           list (lead, status, reviewer, createdAt)
```

**Relationship to C10 Python model**: Direct 1:1 mapping to `DraftApproval` dataclass. The CRM entity adds `leadId` for relationship traversal (the Python model only has `draft_id` — `lead_id` is on `SendRequest`).

### 3.2 SendExecution (CRM Entity)

```
Entity: SendExecution
Purpose: Audit record of one controlled send execution.
         One send_request_id → exactly one SendExecution record.
Ownership: Connector creates and transitions (Integration Bot).
Lifecycle: READY_TO_SEND → SUBMITTED → PROCESSING → SENT | FAILED

Fields:
  sendRequestId    varchar(256)   UNIQUE NOT NULL   # C10.0-B send_request_id
  approvalId       varchar(128)   NOT NULL           # FK → DraftApproval
  leadId           varchar(64)    NOT NULL           # FK → Lead.id
  draftId          varchar(128)   NOT NULL           # C09 draft identity (denormalized)
  providerName     varchar(128)   NOT NULL           # e.g., "brevo"
  state            enum           NOT NULL           # READY_TO_SEND|SUBMITTED|
                                                     # PROCESSING|SENT|FAILED
  sendAttemptId    varchar(256)   NULL               # Provider-assigned attempt ID
  resultStatus     enum           NULL               # ACCEPTED|FAILED|REJECTED
  reasonCode       varchar(255)   NULL               # Provider/adapter reason
  retryCount       int            DEFAULT 0          # Number of retries attempted
  maxRetries       int            DEFAULT 3          # Configurable max
  nextRetryAt      datetime       NULL               # Scheduled retry time
  lastError        text           NULL               # Last error message for diagnosis

Relationships:
  approval         belongsTo      DraftApproval      # Execution → approval
  lead             belongsTo      Lead               # Execution → lead
  executions       hasMany        DraftApproval      # (inverse)
  replyEvents      hasMany        ReplyEvent         # Execution → replies

Audit Trail (embedded JSON):
  executionAuditTrail  jsonArray  NOT NULL
    [{draftId, approvalId, sendRequestId, sendAttemptId,
      provider, result, timestamp, state}, ...]

Unique Constraints:
  UNIQUE(sendRequestId)
  INDEX(approvalId)
  INDEX(leadId)
  INDEX(state)  # For queue queries: "find all READY_TO_SEND"

EspoCRM Metadata:
  acl: Admin read, Integration Bot CRUD (Sales roles: read only own team's leads)
  layouts: detail (state timeline, provider, result)
           list (lead, provider, state, resultStatus, createdAt)
```

**Worker/Retry Compatibility**: `retryCount`, `maxRetries`, `nextRetryAt`, `lastError` are schema预留 (reserved fields) for future worker implementation. C11 does NOT implement a worker — it only defines the schema so future phases can add retry logic without migration. The `state` + `nextRetryAt` pattern supports `SELECT ... WHERE state = 'FAILED' AND retryCount < maxRetries AND nextRetryAt <= NOW()`.

### 3.3 ReplyEvent (CRM Entity)

```
Entity: ReplyEvent
Purpose: Immutable reply tracking record with preserved send execution trace.
         One reply_event_id → exactly one ReplyEvent record.
Ownership: Connector creates (Integration Bot); append-only.
Lifecycle: Created once, never updated.

Fields:
  replyEventId     varchar(256)   UNIQUE NOT NULL   # SHA-256 content hash
  leadId           varchar(64)    NOT NULL           # FK → Lead.id
  draftId          varchar(128)   NOT NULL           # C09 draft identity
  sendAttemptId    varchar(256)   NOT NULL           # Provider attempt ID
  sendRequestId    varchar(256)   NOT NULL           # FK → SendExecution
  threadId         varchar(256)   NOT NULL           # Email thread identifier
  receivedAt       datetime       NOT NULL           # When reply was received
  senderReference  varchar(255)   NOT NULL           # Reply sender address/ID
  replyStatus      enum           NOT NULL           # SENT|REPLIED|BOUNCED|UNSUBSCRIBED
  eventVersion     varchar(64)    DEFAULT "c10.4-reply-tracking-v1"
  originalSendTrace jsonArray     NOT NULL           # Preserved SendExecutionAuditTrace[]

Relationships:
  lead             belongsTo      Lead               # Reply → lead
  sendExecution    belongsTo      SendExecution      # Reply → execution
  replyEvents      hasMany        Lead               # (inverse)

Unique Constraints:
  UNIQUE(replyEventId)
  INDEX(leadId)
  INDEX(sendRequestId)
  INDEX(replyStatus)

EspoCRM Metadata:
  acl: Admin read, Integration Bot CRUD (Sales roles: read own team's leads)
  layouts: detail (status, receivedAt, sender, thread, send trace)
           list (lead, status, receivedAt, senderReference)
```

### 3.4 Lead Enum Extension

```
Lead.peEmailStatus — ADD 3 values:
  Current:  ["NONE", "DRAFT_READY", "APPROVED", "SENT", "REPLIED", "BOUNCED"]
  C11:      ["NONE", "DRAFT_READY", "PENDING_REVIEW", "APPROVED",
             "READY_TO_SEND", "SENT", "SEND_FAILED", "REPLIED", "BOUNCED"]

Lead.peEmailReplyStatus — CHANGE from varchar(64) to enum:
  Current:  varchar(64) — no validation
  C11:      enum["NONE", "NO_REPLY", "POSITIVE_REPLY", "BOUNCED", "UNSUBSCRIBED"]

Lead relationships — ADD:
  draftApprovals   hasMany        DraftApproval      # Lead → approvals
  sendExecutions   hasMany        SendExecution      # Lead → executions
  replyEvents      hasMany        ReplyEvent         # Lead → replies
```

### 3.5 What Is NOT Implemented in C11

| Item | Reason |
|------|--------|
| Worker/daemon | Deferred to C12+ |
| Retry infrastructure | Schema预留 only; no execution logic |
| Real provider integration | Deferred to future provider-specific phase |
| DraftApproval CRM UI for review action | Schema + API only; UI deferred to C11 UI phase |
| Send queue entity | Covered by SendExecution.state queries |
| SendIdempotencyRegistry persistence | Deferred — in-memory acceptable for single-process MVP |
| DraftStore CRM-backed implementation | Reference implementation is re-generation from C09 |

---

## 4. CRM Projection Strategy

### 4.1 Principle: CRM = Projection, Connector = Source of Truth

CRM `peEmail*` fields on Lead are **read-only projections** of the connector's execution state. The connector is the canonical owner of the C10 lifecycle. CRM displays the projection for human visibility.

```
Domain Event (Connector)          →  Projection (CRM Lead fields)
─────────────────────────────────────────────────────────────────
Approval.created(DRAFT_READY)     →  peEmailStatus = DRAFT_READY
                                    (already done by C09 campaign_projection)

Approval.submit_for_review()      →  peEmailStatus = PENDING_REVIEW
                                    (NEW in C11)

Approval.approve()                →  peEmailStatus = APPROVED

Approval.mark_ready_to_send()     →  peEmailStatus = READY_TO_SEND

Execution.state → SENT            →  peEmailStatus = SENT
                                    peLastEmailDate = execution.updatedAt

Execution.state → FAILED          →  peEmailStatus = SEND_FAILED

ReplyEvent(status=REPLIED)        →  peEmailStatus = REPLIED
                                    peEmailReplyStatus = POSITIVE_REPLY

ReplyEvent(status=BOUNCED)        →  peEmailStatus = BOUNCED
                                    peEmailReplyStatus = BOUNCED

ReplyEvent(status=UNSUBSCRIBED)   →  peEmailReplyStatus = UNSUBSCRIBED
                                    (peEmailStatus unchanged)
```

### 4.2 Projection Implementation

The projection adapter (C11 new module: `crm_status_projection.py`) implements a `CrmStatusProjectionClient` Protocol:

```python
class CrmStatusProjectionClient(Protocol):
    def update_lead_email_status(self, lead_id: str, fields: dict) -> dict: ...
```

The adapter is called as a **post-transition hook** from each registry's transition method — after the CRM entity is updated, the adapter projects the relevant status fields to Lead. This follows the same pattern as C09 `CampaignProjectionAdapter`.

### 4.3 Why CRM Is NOT Source of Truth for peEmailStatus

1. **State machine enforcement**: The Python C10 modules enforce strict state transitions (e.g., cannot jump from DRAFT_READY to SENT). CRM formula rules could approximate this but would be fragile and harder to test.

2. **Atomicity**: Approval → Execution → Provider call → Status update is a connector-orchestrated sequence. If CRM were source of truth, the connector would need distributed transaction semantics.

3. **Existing pattern**: C09 `campaign_projection.py` already treats peEmailStatus as a projection target. The pattern is established and tested.

4. **Single writer**: Only the Integration Bot role has write permission on peEmail* fields. Sales roles have read-only access. The projection adapter uses the Integration Bot credential.

---

## 5. DraftStore Design

### 5.1 Protocol Definition

```python
class DraftStore(Protocol):
    """Resolve a draft_id to its EmailDraft content for provider delivery."""

    def get(self, draft_id: str) -> EmailDraft: ...

    def content_hash(self, draft_id: str) -> str: ...

    def evidence_references(self, draft_id: str) -> tuple[DraftEvidenceReference, ...]: ...
```

### 5.2 C11 Reference Implementation: Re-generation from C09 Facts

The reference `DraftStore` implementation does NOT persist drafts. It re-generates them:

```
DraftStore.get(draft_id)
  → Extract lead_id from draft_id (or lookup)
  → Fetch Lead pe* fields from CRM (score, qualification)
  → Fetch ResearchEvidence records for lead (evidence)
  → Construct OutreachInput from current state
  → DeterministicEmailDraftGenerator.generate(outreach_input)
  → Return EmailDraft
```

**Rationale**: Drafts are deterministic given the same input facts. Re-generation ensures the draft always reflects the **current** evidence and score state — not a stale snapshot. If evidence changes between draft creation and send time, the provider receives the updated content.

**Content hash**: `SHA-256(EmailDraft.subject + EmailDraft.body + sorted evidence_references)` — enables immutable identity verification without storing the draft.

### 5.3 Future: CRM-Backed DraftStore

If re-generation proves too expensive or if drafts must be audited exactly as-approved, a future phase can implement a CRM-backed `DraftStore` that persists `EmailDraft` content as a CRM entity or blob. The Protocol seam makes this a pure implementation swap.

---

## 6. Idempotency Strategy

### 6.1 Unique Keys at Database Level

| Entity | Unique Key | Columns | Level |
|--------|-----------|---------|-------|
| DraftApproval | `draftId` | `draft_id` | Database UNIQUE index |
| SendExecution | `sendRequestId` | `send_request_id` | Database UNIQUE index |
| ReplyEvent | `replyEventId` | `reply_event_id` | Database UNIQUE index |
| ResearchEvidence | `c10EvidenceIdentity` | `lead_id, pe_canonical_url, pe_evidence_type_normalized, pe_claim_hash, delete_id` | ✅ Already active (C10.6.1) |
| SendIdempotency | `idempotencyKey` | `idempotency_key` | **Deferred** — in-memory acceptable for single-process MVP |

### 6.2 From Runtime to Persistent Idempotency

| C10 Runtime (current) | C11 Persistent (target) |
|------------------------|------------------------|
| `InMemoryHumanApprovalRegistry` — `dict[approval_id]` | `EspoCRMDraftApprovalRegistry` — CRM UNIQUE(draftId) |
| `InMemorySendExecutionRegistry` — `dict[send_request_id]` | `EspoCRMSendExecutionRegistry` — CRM UNIQUE(sendRequestId) |
| `InMemoryReplyEventRegistry` — `dict[reply_event_id]` | `EspoCRMReplyEventRegistry` — CRM UNIQUE(replyEventId) |
| `InMemorySendIdempotencyRegistry` — `dict[idempotency_key]` | Deferred — in-memory acceptable |

### 6.3 Multi-Process Safety

C10's `threading.RLock` provides single-process safety. C11 CRM-backed registries provide cross-process safety via database UNIQUE constraints:

- **Duplicate approval**: `INSERT` with existing `draftId` → EspoCRM returns 409 Conflict → Python raises `ValueError("duplicate approval attempt for draft")`
- **Duplicate execution**: `INSERT` with existing `sendRequestId` → 409 Conflict → Python raises `ValueError("duplicate send execution request id")`
- **Duplicate reply**: `INSERT` with existing `replyEventId` → 409 Conflict → Python returns `DUPLICATE`

The CRM REST client (existing `real_client.py` pattern) translates HTTP 409 to the appropriate Python exception, preserving the exact exception contract expected by C10 tests.

---

## 7. Worker / Retry Compatibility

C11 does **not** implement a worker, queue, or retry infrastructure. However, the entity schema is designed to support them:

### 7.1 SendExecution Queue Query Pattern

```sql
-- Find pending executions ready for processing
SELECT * FROM send_execution
WHERE state = 'READY_TO_SEND'
ORDER BY created_at ASC
LIMIT 10;

-- Find failed executions due for retry
SELECT * FROM send_execution
WHERE state = 'FAILED'
  AND retry_count < max_retries
  AND next_retry_at <= NOW()
ORDER BY next_retry_at ASC
LIMIT 10;
```

### 7.2 Multi-Worker Claim Pattern

Following the existing `SearchJob` claim pattern (`AcquisitionWorker`):

```
1. GET  /Prospecting/execution/{id}          → read current state
2. Verify state == READY_TO_SEND             → pre-condition check
3. PUT  /Prospecting/execution/{id}          → update state to PROCESSING
   with modifiedAt as optimistic lock         → if 409 Conflict, another worker
                                                 claimed it first
4. Execute provider call
5. PUT  /Prospecting/execution/{id}          → update state to SENT/FAILED
```

### 7.3 Required Persistence Guarantees

| Guarantee | Mechanism |
|-----------|-----------|
| At-most-once delivery | UNIQUE(sendRequestId) + state check before provider call |
| Idempotent retry | New send_request_id per retry → new idempotency_key |
| Failure visibility | state=FAILED + lastError + retryCount in CRM |
| No lost executions | state=READY_TO_SEND persisted before provider call |
| Worker crash recovery | state=PROCESSING + no SENT result for > timeout → retryable |

---

## 8. EspoCRM Native Alignment

### 8.1 States That Belong in CRM Entities

| State | Rationale |
|-------|-----------|
| DraftApproval.status | Humans approve/reject → must be CRM-visible |
| DraftApproval.reviewerId | CRM user identity → native ACL integration |
| DraftApproval.auditTrace | Compliance → CRM audit fields + JSON trace |
| SendExecution.state | Operational visibility → dashboards, alerts |
| SendExecution.resultStatus | Send outcome → CRM-visible for diagnosis |
| SendExecution.providerName | Provider traceability → audit |
| ReplyEvent.replyStatus | Lead lifecycle display → CRM UI |
| ReplyEvent.originalSendTrace | End-to-end traceability → preserved in CRM |

### 8.2 States That Belong in Connector/Domain Layer

| State | Rationale |
|-------|-----------|
| SendRequest.idempotency_key | Internal idempotency — computed, not displayed |
| SendAttempt.state (CREATED→READY→PROCESSING) | Transient — only final SENT/FAILED matters to CRM |
| SendProviderAdapter cache | Process-local performance optimization |
| DraftStore content hash | Integrity verification — computed, not displayed |
| InMemory registries (test doubles) | Test infrastructure — never persistent |

### 8.3 EspoCRM Capabilities Leveraged

| Capability | Used For |
|-----------|----------|
| **Entity** | DraftApproval, SendExecution, ReplyEvent persistence |
| **ACL** | Who can approve (Sales Manager), who can view (own team), who can create (Integration Bot) |
| **Workflow** | Auto-create Task on `SEND_FAILED` (alert sales rep), on `REPLIED` (follow-up Task) |
| **API** | REST endpoints auto-generated for CRUD; custom `/approval/{id}/approve` action |
| **Relationship** | Lead → DraftApprovals, Lead → SendExecutions, Lead → ReplyEvents |
| **Audit fields** | createdAt, modifiedAt, createdBy, modifiedBy — free with every entity |
| **Layouts** | Detail/list views for CRM users without writing frontend code |
| **Formula** | `peEmailStatus` transitions on Lead (display-only, existing pattern) |

---

## 9. Migration Risks

### 9.1 Schema Migration

| Risk | Severity | Mitigation |
|------|----------|------------|
| Adding 3 new entities + extending Lead enum | **LOW** | Standard EspoCRM extension upgrade path. No existing data migration needed — all C10 state was in-memory. |
| Lead.peEmailStatus enum extension | **LOW** | Adding options is backward-compatible. Existing records keep current values. |
| Lead.peEmailReplyStatus varchar→enum | **MEDIUM** | Existing varchar values must map to new enum. Run preflight to inventory current values before migration. |
| UNIQUE constraints on new entities | **LOW** | New entities have no existing data to conflict. |

### 9.2 Contract Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| C10 Protocol signature change | **NONE** | CRM-backed registries implement existing Protocols. No interface change. |
| C10 state machine behavior change | **NONE** | Transition guards unchanged. Only persistence layer swapped. |
| C10 test breakage | **LOW** | In-memory registries retained for offline tests. CRM-backed registries tested separately. |
| C09 EmailDraft contract change | **NONE** | DraftStore is C11-new. C09 EmailDraft unchanged. |

### 9.3 Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| CRM unavailable → connector can't transition state | **MEDIUM** | Connector is a stateless batch runner — exits with error, retries on next run. Acceptable for MVP. |
| REST latency for idempotency checks | **LOW** | SendIdempotencyRegistry remains in-memory for C11. Only state transitions go through CRM. |
| Concurrent approval transitions | **LOW** | EspoCRM entity save is atomic. Last-write-wins for non-conflicting fields. State machine guards validate transitions before save. |

---

## 10. C11 Implementation Entry Criteria

### 10.1 Must Satisfy Before C11 Implementation

| # | Condition | Rationale |
|---|-----------|-----------|
| **C1** | G03 commit separation plan executed | 251 uncommitted changes must be committed before adding C11 work |
| **C2** | Regression Gate passes from clean post-commit state (7/7 suites, 374+ tests) | Baseline stability before 3 new entities added |
| **C3** | This architecture document approved | Design sign-off before implementation |
| **C4** | C10.6.1 backup preserved (`temp/backups/phase3c10_6_1-*`) | Rollback capability for evidence index |
| **C5** | C10 frozen contracts confirmed unchanged | `PHASE3C10_FREEZE.md` entry criteria §1, §7 verified |

### 10.2 C11 Phase Breakdown (Recommended)

```
C11.1 — Entity Schema + Enum Extension
  ├── DraftApproval entity (entityDefs, aclDefs, scopes, layouts, i18n)
  ├── SendExecution entity (entityDefs, aclDefs, scopes, layouts, i18n)
  ├── ReplyEvent entity (entityDefs, aclDefs, scopes, layouts, i18n)
  ├── Lead.peEmailStatus enum extension (+PENDING_REVIEW, READY_TO_SEND, SEND_FAILED)
  ├── Lead.peEmailReplyStatus varchar→enum migration
  └── Extension skeleton test assertions for new entities

C11.2 — CRM-Backed Registry Implementations
  ├── EspoCRMDraftApprovalRegistry (implements HumanApprovalRegistry Protocol)
  ├── EspoCRMSendExecutionRegistry (implements SendExecutionRegistry Protocol)
  ├── EspoCRMReplyEventRegistry (implements ReplyEventRegistry Protocol)
  ├── Custom API endpoints (POST /approval/{id}/approve, POST /approval/{id}/reject)
  └── Integration tests with in-memory→CRM swap

C11.3 — C10→CRM Status Projection Bridge
  ├── CrmStatusProjectionAdapter (new module, follows C09 CampaignProjectionAdapter pattern)
  ├── Post-transition hooks: execution.SENT → peEmailStatus update
  ├── Post-transition hooks: reply.REPLIED → peEmailStatus update
  └── peEmailReplyStatus enum validation alignment with ReplyStatus

C11.4 — DraftStore Protocol + Reference Implementation
  ├── DraftStore Protocol definition
  ├── RegeneratingDraftStore (re-generation from C09 facts)
  ├── Content hash verification
  └── Integration test with SendProvider adapter

C11.5 — Regression Gate Extension
  ├── C11 entity contract tests
  ├── CRM-backed registry vs in-memory parity tests
  ├── Status projection bridge tests
  └── Full Regression Gate re-run (target: 7/7 + C11 suite)
```

---

## 11. Final Verdict

```
 █████╗ ██████╗ ██████╗ ██████╗  ██████╗ ██╗   ██╗███████╗██████╗
██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██║   ██║██╔════╝██╔══██╗
███████║██████╔╝██████╔╝██████╔╝██║   ██║██║   ██║█████╗  ██║  ██║
██╔══██║██╔═══╝ ██╔═══╝ ██╔══██╗██║   ██║╚██╗ ██╔╝██╔══╝  ██║  ██║
██║  ██║██║     ██║     ██║  ██║╚██████╔╝ ╚████╔╝ ███████╗██████╔╝
╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ╚══════╝╚═════╝

██╗    ██╗██╗████████╗██╗  ██╗
██║    ██║██║╚══██╔══╝██║  ██║
██║ █╗ ██║██║   ██║   ███████║
██║███╗██║██║   ██║   ██╔══██║
╚███╔███╔╝██║   ██║   ██║  ██║
 ╚══╝╚══╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝

 ██████╗ ██████╗ ███╗   ██╗██████╗ ██╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝██╔═══██╗████╗  ██║██╔══██╗██║╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
██║     ██║   ██║██╔██╗ ██║██║  ██║██║   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██║     ██║   ██║██║╚██╗██║██║  ██║██║   ██║   ██║██║   ██║██║╚██╗██║╚════██║
╚██████╗╚██████╔╝██║ ╚████║██████╔╝██║   ██║   ██║╚██████╔╝██║ ╚████║███████║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
```

**VERDICT: APPROVED WITH CONDITIONS**

### What Is Approved

1. **Hybrid source-of-truth model**: CRM entities for DraftApproval, SendExecution, ReplyEvent. Connector domain for SendIdempotencyRegistry and DraftStore.

2. **3 new CRM entities**: DraftApproval, SendExecution, ReplyEvent — each with clear purpose, ownership, lifecycle, relationships, and unique constraints.

3. **Lead enum extension**: +3 values to peEmailStatus (PENDING_REVIEW, READY_TO_SEND, SEND_FAILED); peEmailReplyStatus varchar→enum.

4. **CRM projection strategy**: peEmail* fields are derived projections, not canonical state. Connector owns the lifecycle. Projection adapter follows C09 pattern.

5. **DraftStore Protocol**: Interface + re-generation-backed reference implementation. CRM-backed implementation deferred.

6. **Idempotency**: Database-level UNIQUE constraints for 4 of 5 objects. SendIdempotencyRegistry remains in-memory for C11 (acceptable for single-process MVP).

7. **Worker/retry forward-compatibility**: Schema预留 (retryCount, maxRetries, nextRetryAt, lastError) without implementation.

8. **No new database, no C10 contract changes, no provider integration, no worker implementation.**

### Conditions

| # | Condition | Rationale |
|---|-----------|-----------|
| **C1** | G03 commit separation plan executed before C11.1 | Clean working tree required |
| **C2** | Regression Gate 7/7 PASS from clean post-commit state | Baseline stability |
| **C3** | peEmailReplyStatus current values inventoried before enum migration | Data safety |
| **C4** | C10 frozen contracts confirmed unchanged after C11 entity additions | Contract freeze integrity |
| **C5** | All C10 in-memory registry tests continue to pass (in-memory impls retained) | Backward compatibility |

### What Could Trigger Rejection

- G03 commit plan reveals broken intermediate state
- C10 tests fail with CRM-backed registry swap
- EspoCRM schema limitations prevent proposed UNIQUE indexes
- peEmailReplyStatus migration preflight finds unmappable values
- C11 scope expands to include real provider integration (must be deferred)

---

## Appendix A: C10 Protocol → C11 Implementation Mapping

| C10 Protocol | C10 In-Memory Impl | C11 CRM-Backed Impl | CRM Entity |
|-------------|-------------------|--------------------|------------|
| `HumanApprovalRegistry` | `InMemoryHumanApprovalRegistry` | `EspoCRMDraftApprovalRegistry` | `DraftApproval` |
| `SendExecutionRegistry` | `InMemorySendExecutionRegistry` | `EspoCRMSendExecutionRegistry` | `SendExecution` |
| `ReplyEventRegistry` | `InMemoryReplyEventRegistry` | `EspoCRMReplyEventRegistry` | `ReplyEvent` |
| `SendIdempotencyRegistry` | `InMemorySendIdempotencyRegistry` | **Deferred** | N/A |
| `EmailDraftGenerator` | `DeterministicEmailDraftGenerator` | Unchanged | N/A |
| *(new)* `DraftStore` | N/A | `RegeneratingDraftStore` | N/A |
| *(new)* `CrmStatusProjectionClient` | N/A | `CrmStatusProjectionAdapter` | Lead.peEmail* |

## Appendix B: Key Documents Referenced

| Document | Date | Relevance |
|----------|------|-----------|
| `PHASE3C10_FREEZE.md` | 2026-07-14 | Frozen C10 contracts |
| `PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md` | 2026-07-14 | 8 architectural risks, 3 HIGH |
| `PHASE3C10_6_EVIDENCE_PRODUCTION_ALIGNMENT_REPORT.md` | 2026-07-14 | Evidence identity index |
| `PHASE3C10_6_1_RESEARCH_EVIDENCE_INDEX_ACTIVATION_REPORT.md` | 2026-07-14 | C10.6.1 activation |
| `PHASE_G04_C11_READINESS_REVIEW.md` | 2026-07-14 | C11 CONDITIONAL GO |
| `PHASE_G03_REPOSITORY_FREEZE_PLAN.md` | 2026-07-14 | 7 commit boundaries |

## Appendix C: Audit Methodology

This review was conducted as a **read-only architecture design review**. No files were modified, no entities were created, no migrations were executed, no CRM was accessed, and no external APIs were called.

**Code analyzed**:
- `human_approval.py` — DraftApproval dataclass, state machine, InMemoryHumanApprovalRegistry
- `send_idempotency.py` — SendRequest, SendAttempt, idempotency key generation
- `send_execution.py` — SendExecution, ControlledSendExecutionService, 6-layer approval gate
- `reply_tracking.py` — ReplyEvent, ReplyTrackingService, send trace preservation
- `send_provider.py` — SendProvider Protocol, SendProviderAdapter
- `email_draft_generation.py` — EmailDraft, DeterministicEmailDraftGenerator
- `campaign_projection.py` — CampaignProjectionAdapter, 3-field allowlist
- `email_lifecycle.py` — EmailLifecycleSyncService, EmailLifecycleUpdate
- `research_evidence_persistence.py` — Evidence identity, persistence adapter
- `Lead.json` — Current peEmail* fields, enums, relationships
- `ResearchEvidence.json` — C10.6 identity index fields
- `ChituSyncService.php` — CRM evidence sync production writer

---

**No files were modified by this review.**
**No CRM entities were created.**
**No database migrations were performed.**
**No external APIs were called.**
