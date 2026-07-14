# Phase C11.1 — ReplyStatus and DraftStore Contract Review

> **Date**: 2026-07-14
> **Review Type**: Read-Only Architecture Contract Review
> **Repository**: D:\EspoCRM-Production (branch: `master`)
> **Precondition**: C10.6 frozen, G05 C11 Scope Architecture Review completed
> **Status**: COMPLETE — No code modified

---

## Executive Summary

| Review Dimension | Verdict |
|---|---|
| 1. Reply Status Existing State Audit | **INVENTORIED** — 6 distinct values found across 4 writers |
| 2. ReplyEvent Contract Design | **CONFIRMED** — C10.4 contract is the source of truth; Lead is projection only |
| 3. Migration Mapping | **DEFINED** — Full mapping from varchar values to ReplyStatus enum |
| 4. DraftStore Contract Review | **APPROVED** — Protocol correct; no AI reasoning stored |
| 5. Draft Approval Integrity | **DESIGNED** — SHA-256 content hash with approval-store + send-verify |
| 6. Boundary Check | **CLEAN** — C11 scope does not overlap C10 |

**Overall Verdict: CONTRACTS READY FOR C11.1 IMPLEMENTATION**

---

## 1. Current State — Reply Status Existing State Audit

### 1.1 Lead.peEmailStatus (enum — CRM entity field)

**Definition**: `crm-extension/Resources/entityDefs/Lead.json:73-89`

| Value | Display Style | Meaning |
|---|---|---|
| `NONE` | default | No email activity yet |
| `DRAFT_READY` | warning | C09 draft prepared, awaiting review |
| `APPROVED` | info | Draft approved by human reviewer |
| `SENT` | primary | Email sent via provider |
| `REPLIED` | success | Recipient replied |
| `BOUNCED` | danger | Email bounced |

**Gap**: Three enum values are missing from CRM but exist in the C10 Python state machine:
- `PENDING_REVIEW` — draft submitted for review (C10.1 ApprovalStatus)
- `READY_TO_SEND` — approval complete, ready for execution (C10.1 ApprovalStatus)
- `SEND_FAILED` — execution failed (C10.3 SendExecutionState)

### 1.2 Lead.peEmailReplyStatus (varchar(64) — CRM entity field)

**Definition**: `crm-extension/Resources/entityDefs/Lead.json:104-111`
- **Type**: `varchar`, max 64 chars
- **NOT an enum** — no validation, any string is accepted
- Displayed on Lead and Opportunity detail layouts

### 1.3 Actual Values Found in Codebase

| Value | Source | Writer | Context |
|---|---|---|---|
| `REPLIED` | `EmailEventWorkflowHook.php:90` | PHP Hook (Brevo webhook) | When EmailEvent.eventType = REPLIED |
| `BOUNCED` | `EmailEventWorkflowHook.php:105` | PHP Hook (Brevo webhook) | When EmailEvent.eventType = BOUNCED |
| `NONE` | `email_lifecycle_sync.py:64` | Python Connector (synthetic test) | Initial state / DRAFT_READY transition |
| `NO_REPLY` | `email_lifecycle_sync.py:66` | Python Connector (synthetic test) | SENT transition |
| `POSITIVE_REPLY` | `email_lifecycle_sync.py:67` | Python Connector (synthetic test) | REPLIED transition |
| *(any ≤64 char)* | `email_lifecycle.py:41,48-49` | `EmailLifecycleUpdate.reply_state` | Any string, validated only for length (1-64) |

### 1.4 EmailEvent.eventType (enum — CRM entity)

**Definition**: `crm-extension/Resources/entityDefs/EmailEvent.json:5-17`

| Value | Source | Triggers Lead update? |
|---|---|---|
| `SENT` | Brevo webhook | Yes → peEmailStatus = SENT |
| `DELIVERED` | Brevo webhook | Yes → peEmailStatus = SENT (if not REPLIED/BOUNCED) |
| `OPENED` | Brevo webhook | Engagement only (no status change) |
| `CLICKED` | Brevo webhook | Engagement only (no status change) |
| `REPLIED` | Brevo webhook | Yes → peEmailStatus = REPLIED, peEmailReplyStatus = REPLIED |
| `BOUNCED` | Brevo webhook | Yes → peEmailStatus = BOUNCED, peEmailReplyStatus = BOUNCED |

### 1.5 C10.4 ReplyStatus (Python enum — Connector domain)

**Definition**: `chitu_connector/chitu_connector/espocrm_sync/reply_tracking.py:27-31`

| Value | Meaning |
|---|---|
| `SENT` | Base state — execution sent, no reply yet |
| `REPLIED` | Positive reply received |
| `BOUNCED` | Hard bounce received |
| `UNSUBSCRIBED` | Recipient unsubscribed |

### 1.6 All Writers of peEmailReplyStatus (System Inventory)

```
┌──────────────────────────────────────────────────────────────────┐
│  WRITER 1: EmailEventWorkflowHook.php (PHP)                     │
│  Trigger:  Brevo webhook → EmailEvent after-save hook            │
│  Writes:   'REPLIED', 'BOUNCED'                                  │
│  Scope:    Only on new EmailEvent records with leadId            │
│  Guard:    $event->isNew() check                                 │
├──────────────────────────────────────────────────────────────────┤
│  WRITER 2: EmailLifecycleSyncService (Python)                    │
│  Trigger:  Explicit connector sync call                          │
│  Writes:   Any string ≤64 chars (reply_state parameter)          │
│  Scope:    Synthetic test only (no production path active)       │
│  Guard:    Allowlisted _SYNCED_FIELDS set                        │
├──────────────────────────────────────────────────────────────────┤
│  WRITER 3: C09 CampaignProjectionAdapter (Python)                │
│  Writes:   DOES NOT WRITE peEmailReplyStatus                     │
│  Verified:  test_phase3c09_campaign_projection.py:100            │
│             self.assertNotIn("peEmailReplyStatus", fields)       │
├──────────────────────────────────────────────────────────────────┤
│  WRITER 4: C11 CRM Status Projection (Python — PLANNED)          │
│  Writes:   TBD — post-transition hook from ReplyEvent            │
│  Scope:    One-way projection only, not reverse control          │
└──────────────────────────────────────────────────────────────────┘
```

### 1.7 Risk: Unvalidated varchar Field

The `peEmailReplyStatus` field is `varchar(64)` with **no enum constraint**. Any of the four writers (or a manual CRM edit) can write arbitrary strings. The C10 Architecture Audit (RISK-8) flagged this as a data-quality risk. The C11 plan to convert this to an enum requires preflight inventory of all existing values in the production CRM before migration.

---

## 2. Recommended Contract — ReplyEvent

### 2.1 Source of Truth Declaration

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCE OF TRUTH:  C10.4 ReplyEvent (Python Connector domain)   │
│                                                                  │
│  ReplyEvent is a connector-domain immutable record.              │
│  It is created ONLY by ReplyTrackingService.track().             │
│  It requires a traceable SENT SendExecution.                     │
│                                                                  │
│  CRM ReplyEvent entity (C11):                                    │
│  → Durable persistence of the identical contract                 │
│  → Append-only, Integration Bot write, Admin/Sales read          │
│  → reply_event_id = SHA-256 (same as C10.4 identity)            │
│  → original_send_trace preserved as JSON array                   │
│                                                                  │
│  Lead.peEmailReplyStatus (CRM):                                  │
│  → READ-ONLY PROJECTION of the latest ReplyEvent                 │
│  → NEVER a reverse control channel into the C10 state machine   │
│  → Updated by CrmStatusProjectionAdapter (post-transition hook)  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 ReplyEvent Contract (Frozen from C10.4)

| Field | Type | Required | Identity Component? | Description |
|---|---|---|---|---|
| `reply_event_id` | varchar(256) | Yes | **PRIMARY KEY** | SHA-256(content hash) |
| `lead_id` | varchar(64) | Yes | Yes | FK → Lead.id |
| `draft_id` | varchar(128) | Yes | Yes | C09 draft identity |
| `send_attempt_id` | varchar(256) | Yes | Yes | Provider attempt ID |
| `thread_id` | varchar(256) | Yes | Yes | Email thread identifier |
| `received_at` | datetime (tz-aware) | Yes | Yes | UTC receipt timestamp |
| `sender_reference` | varchar(255) | Yes | Yes | Reply sender address |
| `reply_status` | enum(ReplyStatus) | Yes | Yes | SENT\|REPLIED\|BOUNCED\|UNSUBSCRIBED |
| `event_version` | varchar(64) | Yes | Yes | "c10.4-reply-tracking-v1" |
| `original_send_trace` | jsonArray | Yes | No | Preserved SendExecutionAuditTrace[] |
| `send_request_id` | varchar(256) | Yes (C11) | No | FK → SendExecution (denormalized for lookup) |

### 2.3 Identity Contract

```python
# From reply_tracking.py:152-174
reply_event_id = SHA-256({
    "event_version": "c10.4-reply-tracking-v1",
    "lead_id": "<trimmed>",
    "draft_id": "<trimmed>",
    "send_attempt_id": "<trimmed>",
    "thread_id": "<trimmed>",
    "received_at": "<UTC ISO 8601>",
    "sender_reference": "<trimmed>",
    "reply_status": "SENT|REPLIED|BOUNCED|UNSUBSCRIBED",
})
```

**Guarantee**: Same inputs → same identity. Duplicate detection at database level via `UNIQUE(replyEventId)`.

### 2.4 Connector Responsibilities (UNCHANGED from C10.4)

1. **Reply detection** — `ReplyTrackingService.track()` validates inputs
2. **Transition validation** — Only accepts events for `SENT` executions
3. **Trace matching** — Verifies `lead_id` and `draft_id` match the execution
4. **Trace preservation** — Embeds full `SendExecutionAuditTrace[]` in the event
5. **Identity generation** — Deterministic SHA-256

### 2.5 Lead Field Constraint (NEW in C11)

```
RULE: Lead.peEmailReplyStatus MUST NOT reverse-control the reply lifecycle.

CORRECT:
  ReplyEvent (created by connector) → projection → Lead.peEmailReplyStatus

INCORRECT:
  Lead.peEmailReplyStatus (manually edited) → triggers ReplyEvent creation
  Lead.peEmailReplyStatus (manually edited) → changes ReplyEvent.reply_status
  Lead.peEmailReplyStatus (manually edited) → affects C10 state machine
```

**Enforcement**: CRM ACL restricts `peEmailReplyStatus` write to Integration Bot role only. Sales roles have read-only access.

### 2.6 C11 CRM Entity Projection Mapping

```
Connector Domain Event              →  CRM Projection
─────────────────────────────────────────────────────────
ReplyEvent(status=SENT)             →  peEmailReplyStatus = "NONE"
                                       (base state — SENT with no reply yet)
ReplyEvent(status=REPLIED)          →  peEmailReplyStatus = "POSITIVE_REPLY"
                                       peEmailStatus = "REPLIED"
ReplyEvent(status=BOUNCED)          →  peEmailReplyStatus = "BOUNCED"
                                       peEmailStatus = "BOUNCED"
ReplyEvent(status=UNSUBSCRIBED)     →  peEmailReplyStatus = "UNSUBSCRIBED"
                                       (peEmailStatus unchanged)
```

---

## 3. Migration Mapping

### 3.1 Old peEmailReplyStatus → New ReplyStatus Mapping

| Old Value (varchar) | Observed In | Maps To ReplyEvent.replyStatus | Maps To New peEmailReplyStatus (enum) | Notes |
|---|---|---|---|---|
| `"REPLIED"` | EmailEventWorkflowHook, Brevo | `REPLIED` | `POSITIVE_REPLY` | Direct mapping |
| `"BOUNCED"` | EmailEventWorkflowHook, Brevo | `BOUNCED` | `BOUNCED` | Direct mapping |
| `"NONE"` | EmailLifecycleSync test | *(no event)* | `NONE` | Initial state, no ReplyEvent needed |
| `"NO_REPLY"` | EmailLifecycleSync test | *(no event)* | `NO_REPLY` | SENT with no reply detected |
| `"POSITIVE_REPLY"` | EmailLifecycleSync test | `REPLIED` | `POSITIVE_REPLY` | New enum preserves this value |
| `NULL` / empty | Database default | *(no event)* | `NONE` | Treated as initial state |
| *(any other)* | Production CRM (unknown) | `REJECTED` (log + skip) | `NONE` (safe default) | Requires preflight inventory |

### 3.2 C11 peEmailReplyStatus Enum Design

**New enum definition** (replaces varchar):

```json
{
  "peEmailReplyStatus": {
    "type": "enum",
    "required": false,
    "notNull": false,
    "options": ["NONE", "NO_REPLY", "POSITIVE_REPLY", "BOUNCED", "UNSUBSCRIBED"],
    "default": "NONE",
    "displayAsLabel": true,
    "style": {
      "NONE": "default",
      "NO_REPLY": "info",
      "POSITIVE_REPLY": "success",
      "BOUNCED": "danger",
      "UNSUBSCRIBED": "warning"
    }
  }
}
```

**Rationale for each value**:

| Value | Justification |
|---|---|
| `NONE` | Initial state. No email sent, or sent but no reply status known. |
| `NO_REPLY` | Email sent, no reply/bounce/unsubscribe detected. Default after SENT. |
| `POSITIVE_REPLY` | Customer replied positively. Maps from C10.4 `ReplyStatus.REPLIED`. |
| `BOUNCED` | Hard bounce. Maps from C10.4 `ReplyStatus.BOUNCED`. |
| `UNSUBSCRIBED` | Recipient unsubscribed. Maps from C10.4 `ReplyStatus.UNSUBSCRIBED`. |

### 3.3 Migration Procedure (Recommended)

```
Phase 1: PREFLIGHT INVENTORY
  → Query CRM: SELECT DISTINCT peEmailReplyStatus FROM lead
              WHERE peEmailReplyStatus IS NOT NULL AND peEmailReplyStatus != ''
  → Compare against known values: NONE, NO_REPLY, POSITIVE_REPLY,
    REPLIED, BOUNCED
  → Flag any UNKNOWN values for manual review
  → Freeze production writes to peEmailReplyStatus during migration

Phase 2: SCHEMA MIGRATION
  → Add new peEmailReplyStatusEnum field (temporary)
  → Run mapping script to populate new field from old varchar
  → Verify: COUNT(old) == COUNT(new) for non-null rows
  → Drop old varchar field
  → Rename new enum field to peEmailReplyStatus

Phase 3: NULL HANDLING
  → NULL → "NONE" (default)
  → Empty string → "NONE" (default)
  → "REPLIED" → "POSITIVE_REPLY" (legacy Brevo value)
  → UNKNOWN → "NONE" + log warning (safe fallback)

Phase 4: DUPLICATE HANDLING
  → ReplyEvent has UNIQUE(replyEventId) — duplicates rejected at DB level
  → ReplyEventRegistry.record() returns DUPLICATE for repeat ingestion
  → CRM projection writes latest ReplyEvent value (last-write-wins)
  → No merging of duplicate reply events needed
```

### 3.4 Migration Risk Matrix

| Risk | Severity | Mitigation |
|---|---|---|
| Unknown varchar values in production | **HIGH** | Preflight SELECT DISTINCT before migration |
| Multiple writers race on peEmailReplyStatus | **MEDIUM** | Single Integration Bot writer in C11; ACL restricts others |
| Legacy Brevo "REPLIED" ≠ new "POSITIVE_REPLY" | **LOW** | Mapping handles this; both mean same thing |
| Existing Lead records with stale reply status | **LOW** | No ReplyEvent for old data; Lead shows historical projection only |

---

## 4. DraftStore Contract Review

### 4.1 Protocol Definition

```python
class DraftStore(Protocol):
    """Resolve a draft_id to its EmailDraft content for provider delivery."""

    def get(self, draft_id: str) -> EmailDraft: ...
    def content_hash(self, draft_id: str) -> str: ...
    def evidence_references(self, draft_id: str) -> tuple[DraftEvidenceReference, ...]: ...
```

### 4.2 What DraftStore Stores

| Stored | Rationale |
|---|---|
| `draft_id` | C09 immutable draft identity |
| `content_hash` | SHA-256(subject + body + sorted evidence_refs) |
| `version` | Schema version for forward compatibility |
| `evidence_references` | Tuple of (canonical_url, evidence_type, claim_hash) |
| `generated_at` | Timestamp of draft generation |

### 4.3 What DraftStore MUST NOT Store

| NOT Stored | Rationale |
|---|---|
| AI reasoning / prompts | Chitu Intelligence domain — not CRM's concern |
| Raw crawler output | Size + irrelevant to audit |
| Research intermediate state | Connector-internal mechanics |
| Scoring model internals | Chitu Intelligence domain |
| Provider credentials | Security boundary |
| Full email body (in C11 reference impl) | Re-generated from C09 facts; CRM-backed storage deferred |
| Sentiment analysis | Not part of email content contract |
| Personalization logic | Deterministic from OutreachInput facts |

### 4.4 C11 Reference Implementation: Re-generation

```
DraftStore.get(draft_id):
  1. Extract lead_id from draft_id (or lookup table)
  2. Fetch Lead pe* fields from CRM (score, tier, qualification, product)
  3. Fetch ResearchEvidence records for lead
  4. Construct OutreachInput from current CRM state
  5. DeterministicEmailDraftGenerator.generate(OutreachInput)
  6. Return EmailDraft (subject, body, evidence_references, ...)

Content hash verification:
  SHA-256(subject + body + sorted(evidence_references))
```

**Key property**: Re-generation always reflects **current** CRM facts. If evidence/score change between draft creation and send time, the provider gets updated content. This is intentional — the `draft_id` captures the *identity* (which lead, which template version), not a frozen snapshot of content.

### 4.5 Future: CRM-Backed DraftStore

If re-generation proves expensive or if exact as-approved content must be audited, a future phase can implement a CRM-backed DraftStore that persists the full `EmailDraft` content. The Protocol seam ensures zero code changes in consumers.

---

## 5. Draft Approval Integrity

### 5.1 Content Immutability Rule

```
RULE: Content approved by human reviewer MUST equal content sent to provider.

VIOLATION: If DraftStore re-generates different content at send time than
           what was shown to the reviewer at approval time, the human
           approval gate is bypassed.
```

### 5.2 Design: SHA-256 Content Hash Chain

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: DRAFT GENERATION (C09)                                     │
│                                                                      │
│  draft = EmailDraft(subject, body, evidence_refs, ...)               │
│  draft_id = C09 deterministic identity                               │
│  content_hash = SHA-256(subject + body + sorted(evidence_refs))     │
│                                                                      │
│  The content_hash is embedded in the draft metadata.                 │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: APPROVAL (C10.1 → C11 CRM)                                 │
│                                                                      │
│  DraftApproval record stores:                                        │
│    - draft_id                                                        │
│    - content_hash (approved hash at time of review)                  │
│    - reviewer_id                                                     │
│    - approval_audit_trace                                            │
│                                                                      │
│  The content_hash is IMMUTABLE once APPROVED.                        │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: SEND EXECUTION (C10.3 → C11)                               │
│                                                                      │
│  Before provider call:                                               │
│    current_draft = DraftStore.get(draft_id)                          │
│    current_hash = SHA-256(current_draft.subject +                    │
│                           current_draft.body +                       │
│                           sorted(current_draft.evidence_refs))       │
│    approved_hash = DraftApproval.get(draft_id).content_hash          │
│                                                                      │
│    if current_hash != approved_hash:                                 │
│        → REJECT send                                                 │
│        → Require new draft_id + re-approval                          │
│        → Log: "content drift detected for draft {draft_id}"         │
│                                                                      │
│    if current_hash == approved_hash:                                 │
│        → PROCEED with send                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Hash Verification Contract

```python
def verify_approval_integrity(
    draft_id: str,
    draft_store: DraftStore,
    approval_registry: HumanApprovalRegistry,
) -> bool:
    """
    Verify that the current draft content matches what was approved.

    Returns True if:
      - The draft was approved (not REJECTED or PENDING_REVIEW)
      - The current content hash matches the stored approved hash

    Returns False if:
      - The draft was never approved
      - Content drift detected (re-generated content ≠ approved content)
    """
    approval = approval_registry.get(draft_id)
    if approval is None or approval.status != ApprovalStatus.APPROVED:
        return False
    current_hash = draft_store.content_hash(draft_id)
    return current_hash == approval.content_hash
```

### 5.4 Drift Scenarios

| Scenario | Detection | Action |
|---|---|---|
| Evidence updated between approval and send | Hash mismatch | Reject send; require re-approval |
| Score changed between approval and send | Hash mismatch (score affects body) | Reject send; require re-approval |
| Template version changed | Hash mismatch | Reject send; create new draft |
| Same facts, same template | Hash match | Proceed (deterministic generation) |
| Manual CRM edit to Lead fields | Hash mismatch | Reject send; require re-approval |

### 5.5 Design Recommendation: Backward-Compatible Hash Storage

For C11, the content hash can be stored in the `DraftApproval` entity as a `varchar(64)` field:

```
DraftApproval.contentHash  varchar(64)  NOT NULL
  → SHA-256 hex digest, computed at approval time
  → Validated at send execution time by ControlledSendExecutionService
  → Mismatch → ValueError("content drift: approved hash does not match current draft")
```

The hash computation MUST use a canonical, stable ordering of evidence references to ensure deterministic output.

---

## 6. Boundary Check — C11 vs C10 Non-Overlap

### 6.1 What C10 Owns (FROZEN — C11 MUST NOT reimplement)

| C10 Module | Responsibility | Freeze Status |
|---|---|---|
| `send_idempotency.py` | SendRequest identity, SendAttempt state machine, idempotency key generation | **FROZEN** |
| `send_execution.py` | ControlledSendExecutionService, 6-layer approval gate, execution state machine | **FROZEN** |
| `send_provider.py` | SendProvider Protocol, provider adapter, result validation | **FROZEN** |
| `reply_tracking.py` | ReplyEvent identity, ReplyTrackingService, trace validation | **FROZEN** |
| `human_approval.py` | DraftApproval state machine, approval audit trace, transition guards | **FROZEN** |

### 6.2 What C11 Adds (Persistence + Projection — NO reimplementation)

| C11 Component | What it does | Does NOT reimplement |
|---|---|---|
| CRM `DraftApproval` entity | Durable storage for approval records | C10.1 approval state machine |
| CRM `SendExecution` entity | Durable storage for execution records | C10.3 execution orchestration |
| CRM `ReplyEvent` entity | Durable storage for reply records | C10.4 reply tracking logic |
| `EspoCRMDraftApprovalRegistry` | REST-backed Protocol impl | C10.1 transition guards |
| `EspoCRMSendExecutionRegistry` | REST-backed Protocol impl | C10.3 execution orchestration |
| `EspoCRMReplyEventRegistry` | REST-backed Protocol impl | C10.4 reply identity + validation |
| `CrmStatusProjectionAdapter` | Post-transition Lead field updates | C10 state machine |
| `DraftStore` (Protocol) | Draft content retrieval | C09 EmailDraft generation |

### 6.3 Explicit Prohibitions (From G05 Scope Architecture Review)

```
C11 MUST NOT:
  ❌ reimplement C10 approval, send execution, idempotency, reply tracking
  ❌ reimplement frozen state transitions
  ❌ add SMTP, provider SDK, credentials, webhooks, delivery reconciliation
  ❌ add campaign execution, retries, queues, or a send worker
  ❌ alter C10.6 Evidence identity, deduplication, persistence
  ❌ alter Connector Contract V1
  ❌ move AI reasoning, enrichment, research, or scoring into EspoCRM
  ❌ persist full email content in CRM (DraftStore reference impl is re-generation)
  ❌ use Lead fields as a reverse control channel into C10
  ❌ change CRM sales ownership or auto-create Opportunities
```

### 6.4 Protocol Preservation Verification

| C10 Protocol | C10 In-Memory Impl (preserved) | C11 CRM-Backed Impl (new) | Signature Identical? |
|---|---|---|---|
| `HumanApprovalRegistry` | `InMemoryHumanApprovalRegistry` | `EspoCRMDraftApprovalRegistry` | ✅ Yes |
| `SendExecutionRegistry` | `InMemorySendExecutionRegistry` | `EspoCRMSendExecutionRegistry` | ✅ Yes |
| `ReplyEventRegistry` | `InMemoryReplyEventRegistry` | `EspoCRMReplyEventRegistry` | ✅ Yes |
| `SendIdempotencyRegistry` | `InMemorySendIdempotencyRegistry` | *(deferred — in-memory retained)* | ✅ N/A |
| *(new)* `DraftStore` | N/A | `RegeneratingDraftStore` | ✅ New Protocol |

**All C10 in-memory implementations remain in the codebase for offline contract tests.**

### 6.5 Evidence Lifecycle Boundary (C10.6 — UNCHANGED)

```
C10.6 Evidence persistence is OUTSIDE C11 scope:
  - ResearchEvidence identity index: UNCHANGED
  - Evidence deduplication: UNCHANGED
  - ChituSyncService evidence writer: UNCHANGED
  - peEvidenceType from evidence_type: UNCHANGED
  - UNIQ_C10_EVIDENCE_IDENTITY unique index: UNCHANGED (active on production)

C11 DraftApproval, SendExecution, and ReplyEvent entities:
  - Do NOT reference ResearchEvidence directly
  - Do NOT modify evidence persistence
  - Do NOT add new evidence identity rules
```

---

## 7. Risks

### 7.1 Contract Risks

| Risk | Severity | Impact | Required Guardrail |
|---|---|---|---|
| **Content drift on re-generation** | HIGH | Re-generated draft at send time may differ from approved draft | Store approved content hash; verify at send; reject on mismatch |
| **Duplicate lifecycle writers** | HIGH | EmailEventWorkflowHook + EmailLifecycleSyncService + C11 Projection could race | C11: single Integration Bot writer for peEmailReplyStatus; ACL restricts PHP hooks |
| **peEmailReplyStatus varchar→enum data loss** | HIGH | Unknown varchar values in production cannot be mapped | Preflight SELECT DISTINCT before migration; UNKNOWN → NONE + log |
| **ReplyStatus enum mismatch** | MEDIUM | C10.4 uses `SENT/REPLIED/BOUNCED/UNSUBSCRIBED`; peEmailReplyStatus uses `NONE/NO_REPLY/POSITIVE_REPLY/BOUNCED/UNSUBSCRIBED` | Two separate enums for different purposes (ReplyEvent vs Lead projection); mapping documented in §3 |
| **Approval hash storage race** | MEDIUM | Two concurrent approval attempts on same draft_id | UNIQUE(draftId) guarantees one approval record; second attempt returns 409 Conflict |

### 7.2 Migration Risks

| Risk | Severity | Impact | Required Guardrail |
|---|---|---|---|
| **Unmappable varchar values** | HIGH | Production CRM may have values outside known set | Preflight inventory; safe fallback to NONE |
| **NULL handling** | LOW | Some Lead records have NULL peEmailReplyStatus | Default to NONE, matching field default |
| **Brevo "REPLIED" vs new "POSITIVE_REPLY"** | LOW | Legacy webhook writes REPLIED; new enum uses POSITIVE_REPLY | Mapping covers this; both mean the same thing |
| **Existing records without ReplyEvent** | LOW | Old Lead records have peEmailReplyStatus but no ReplyEvent entity | Acceptable — ReplyEvent is the canonical record going forward; old Leads retain historical projection only |

### 7.3 Implementation Risks

| Risk | Severity | Impact | Required Guardrail |
|---|---|---|---|
| **C11 expanding scope** | MEDIUM | C11 could drift into C10 reimplementation | G05 scope boundaries frozen; all C11.1 tasks must reference this contract review |
| **Protocol signature drift** | LOW | CRM-backed registries might not preserve exact C10 Protocol behavior | Parity tests: in-memory vs CRM-backed for identical inputs → identical outputs |
| **Trace discontinuity** | LOW | Persistence could drop send trace identifiers | Mandatory fields on all 3 entities; registry parity tests verify trace chain completeness |

---

## 8. C11 Implementation Constraints

### 8.1 Pre-Implementation Gate

| # | Condition | Status (2026-07-14) |
|---|---|---|
| **G1** | peEmailReplyStatus production values inventoried | ⚠️ NOT DONE — this report provides the code-level inventory; production CRM query pending |
| **G2** | C10 freeze verified — all 5 frozen modules unchanged | ⚠️ PENDING — verify no diff in C10 modules since freeze |
| **G3** | Regression Gate 7/7 PASS from clean post-commit state | ⚠️ PENDING — 251 uncommitted changes must be resolved first |
| **G4** | G03 commit separation plan executed | ⚠️ NOT EXECUTED |
| **G5** | This contract review approved | ⚠️ PENDING APPROVAL |

### 8.2 C11.1 Implementation Sequence

```
C11.1a — CRM Entity Schema (this phase)
  ├── DraftApproval entity (entityDefs, fields, relationships, indexes)
  ├── SendExecution entity (entityDefs, fields, relationships, indexes)
  ├── ReplyEvent entity (entityDefs, fields, relationships, indexes)
  ├── Lead.peEmailStatus enum extension (+PENDING_REVIEW, +READY_TO_SEND, +SEND_FAILED)
  ├── Lead.peEmailReplyStatus varchar→enum migration (after preflight)
  └── Extension skeleton test assertions for new entities

C11.1b — ACL + Layouts (schema companion)
  ├── ACL: Integration Bot CRUD, Admin read, Sales Manager read+transition
  ├── Layouts: detail + list for all 3 entities
  ├── i18n: en_US + zh_CN labels
  └── Scopes: entity scopes with tab/disabled/menu configuration
```

### 8.3 Immutable Design Decisions

| Decision | Rationale | Can Change? |
|---|---|---|
| ReplyEvent = CRM entity with C10.4 contract | Human-visible; durable; ACL-governed | Only with new C10 contract version |
| DraftStore = NOT a CRM entity | Drafts re-generated; no body storage in CRM | Future phase can add CRM-backed DraftStore |
| peEmailReplyStatus = projection, not source of truth | C10 owns lifecycle; CRM displays it | Architecture invariant |
| ReplyEvent.replyStatus uses C10.4 enum directly | Single source of truth for reply state | Only if C10.4 ReplyStatus changes |
| Approval content hash = SHA-256 | Deterministic, collision-resistant, standard | Algorithm change requires migration |
| UNIQUE(draftId) on DraftApproval | One approval per draft | Only if multi-version approval needed |
| UNIQUE(sendRequestId) on SendExecution | One execution per send request | Architecture invariant |
| UNIQUE(replyEventId) on ReplyEvent | Deterministic duplicate detection | Architecture invariant |

### 8.4 Test Requirements

| Test Suite | Scope | Target |
|---|---|---|
| C11 entity contract tests | All 3 entities: fields, types, relationships, indexes | 100% field coverage |
| CRM-backed registry parity tests | Identical behavior: in-memory vs CRM-backed for same inputs | All C10.4 test scenarios |
| ReplyStatus mapping tests | All known varchar values → new enum; NULL → NONE; UNKNOWN → NONE | 100% mapping coverage |
| DraftStore content hash tests | Same facts → same hash; different facts → different hash | Deterministic verification |
| Approval integrity tests | Hash match → proceed; hash mismatch → reject | All drift scenarios (§5.4) |
| Boundary non-overlap tests | Assert C10 modules unchanged; assert no new writers on evidence | Regression prevention |

---

## Appendix A: Files Referenced

| File | Role |
|---|---|
| `crm-extension/Resources/entityDefs/Lead.json` | Lead entity definition (peEmailStatus, peEmailReplyStatus) |
| `crm-extension/Resources/entityDefs/EmailEvent.json` | EmailEvent entity definition (eventType enum) |
| `crm-extension/files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php` | Brevo webhook → Lead field writer |
| `chitu-connector/chitu_connector/espocrm_sync/reply_tracking.py` | C10.4 ReplyEvent, ReplyStatus, ReplyTrackingService |
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py` | EmailLifecycleUpdate, EmailLifecycleSyncService |
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle_sync.py` | Synthetic email lifecycle test (reply_state values) |
| `docs/PHASE_G05_C11_SCOPE_ARCHITECTURE_REVIEW.md` | C11 scope definition and boundaries |
| `docs/PHASE3C11_0_PERSISTENCE_ARCHITECTURE_APPROVAL.md` | C11 entity model and persistence design |
| `docs/PHASE_G04_C11_READINESS_REVIEW.md` | C11 readiness assessment |
| `docs/PHASE3C10_FREEZE.md` | C10 frozen contracts |
| `docs/PHASE3C10_ARCHITECTURE_AUDIT_REPORT.md` | C10 architecture risks |
| `docs/PHASE3C10_4_REPLY_TRACKING_BOUNDARY_REPORT.md` | C10.4 ReplyEvent boundary |
| `docs/architecture/BOUNDARIES.md` | System boundary definitions |

## Appendix B: Methodology

This review was conducted as a **read-only architecture contract review**. All findings are based on static code analysis of the repository at `D:\EspoCRM-Production` on branch `master`.

**Code analyzed**: 13 files across CRM extension (PHP), connector (Python), and documentation.

**No files were modified. No CRM entities were created. No database migrations were performed. No external APIs were called. No production CRM was accessed.**

---

**End of Report**
