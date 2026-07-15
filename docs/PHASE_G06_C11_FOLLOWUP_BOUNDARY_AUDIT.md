# Phase G06 — C11 Follow-up Boundary Audit

> **Date**: 2026-07-14
> **Audit Type**: Read-Only Architecture Boundary Audit
> **Repository**: D:\EspoCRM-Production (branch: `master`, HEAD: `7f4ba26`)
> **Precondition**: C10.6 frozen, C11.1 preflight complete, C11.2 DraftApproval in progress
> **Scope**: C11.3 Status Bridge + C11.4 DraftStore Retrieval boundaries
> **Verdict**: **BOUNDARIES CONFIRMED — 4 HIGH risks require guardrails before C11.3/C11.4**

---

## Executive Summary

| Audit Dimension | Verdict |
|---|---|
| 1. C11.3 Status Bridge Source of Truth | **CLEAR** — Connector owns lifecycle; CRM is projection-only |
| 2. Email Lifecycle Non-Reimplementation | **CONFIRMED** — C11.3 is projection/sync, not reimplementation |
| 3. C11.4 DraftStore Retrieval Boundary | **CLEAN** — No overlap with AI, scoring, research, evidence |
| 4. DraftApproval Integration Boundary | **CLEAN** — Approval decision only; no draft gen, AI, or provider |
| 5. Entity Ownership | **DEFINED** — 3 CRM entities + 1 Connector Protocol + 1 Shared |
| 6. Implementation Risks | **4 HIGH, 4 MEDIUM, 3 LOW** |

**Overall Verdict: BOUNDARIES CONFIRMED. C11.3 and C11.4 may proceed with the guardrails documented below.**

The C10 frozen contracts are not violated by the proposed C11.3/C11.4 scope. C11.3 is a one-way projection bridge, not a state machine reimplementation. C11.4 DraftStore is a retrieval Protocol with clean separation from AI/scoring/research. However, **4 HIGH risks** require explicit resolution before implementation — particularly the multiple-writer race condition on `Lead.peEmail*` fields.

---

## 1. State Ownership Matrix

### 1.1 Complete Ownership Table

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         STATE OWNERSHIP MATRIX                                │
│                                                                               │
│  LEGEND:                                                                      │
│    ● = Canonical owner (writes state, enforces transitions)                   │
│    ○ = Projection reader (reads state for display, does not write)            │
│    ◐ = Shared (CRM stores, Connector validates transitions)                   │
│    — = Neither (does not interact with this state)                            │
│                                                                               │
├───────────────────────────────┬──────────┬──────────┬──────────┬─────────────┤
│ STATE                         │ CRM      │CONNECTOR │  SHARED  │  NOTES      │
├───────────────────────────────┼──────────┼──────────┼──────────┼─────────────┤
│ DraftApproval.status          │    ◐     │    ◐     │   YES    │ CRM=store,  │
│                               │          │          │          │ Conn=guard  │
│ DraftApproval.reviewerId      │    ●     │    ○     │    —     │ CRM user ID │
│ DraftApproval.auditTrace      │    ◐     │    ◐     │   YES    │ Both append │
│                               │          │          │          │             │
│ SendExecution.state           │    ◐     │    ◐     │   YES    │ CRM=store,  │
│                               │          │          │          │ Conn=trans  │
│ SendExecution.providerName    │    ○     │    ●     │    —     │ Conn writes │
│ SendExecution.resultStatus    │    ○     │    ●     │    —     │ Conn writes │
│ SendExecution.auditTrace      │    ○     │    ●     │    —     │ Conn writes │
│                               │          │          │          │             │
│ ReplyEvent.replyStatus        │    ○     │    ●     │    —     │ Conn creates│
│ ReplyEvent.replyEventId       │    ○     │    ●     │    —     │ SHA-256 ID  │
│ ReplyEvent.originalSendTrace  │    ○     │    ●     │    —     │ Conn embeds │
│                               │          │          │          │             │
│ Lead.peEmailStatus            │    ○     │    ●     │    —     │ PROJECTION  │
│                               │          │          │          │ Conn=writer │
│ Lead.peEmailReplyStatus       │    ○     │    ●     │    —     │ PROJECTION  │
│                               │          │          │          │ Conn=writer │
│ Lead.peLastEmailDate          │    ○     │    ●     │    —     │ PROJECTION  │
│ Lead.peEmailCampaignName      │    ○     │    ●     │    —     │ PROJECTION  │
│                               │          │          │          │             │
│ SendRequest.idempotencyKey    │    —     │    ●     │    —     │ Internal    │
│ SendAttempt.state             │    —     │    ●     │    —     │ Internal    │
│                               │          │          │          │             │
│ DraftStore.contentHash        │    —     │    ●     │    —     │ New C11     │
│ DraftStore.evidenceRefs       │    —     │    ●     │    —     │ New C11     │
│                               │          │          │          │             │
│ EmailDraft.subject/body       │    —     │    ●     │    —     │ C09 frozen  │
│ OutreachInput facts           │    —     │    ●     │    —     │ C09 frozen  │
│ ResearchEvidence.*            │    ●     │    ○     │    —     │ C10.6 frozen│
└───────────────────────────────┴──────────┴──────────┴──────────┴─────────────┘
```

### 1.2 Key Ownership Principles

1. **CRM stores durable records.** DraftApproval, SendExecution, and ReplyEvent are persistent CRM entities with ACL-governed access. But CRM does NOT own the state machine logic.

2. **Connector owns lifecycle transitions.** The C10 state machines (approval, execution, reply) are connector-domain logic. CRM-backed registries implement the same Protocols — they do not replace the transition guards.

3. **Lead.peEmail\* is a PROJECTION, not a source of truth.** The connector writes projection fields. CRM users read them. CRM workflows MUST NOT write them. The fields are NOT a reverse control channel.

4. **DraftStore is connector-internal.** No CRM entity. No body storage. Reference implementation re-generates from C09 facts.

---

## 2. C11.3 Status Bridge Boundary

### 2.1 Current Writers of Lead.peEmail\* Fields (Pre-C11)

```
┌──────────────────────────────────────────────────────────────────┐
│  WRITER A: CampaignProjectionAdapter (Python, C09)               │
│  ─────────────────────────────────────────────────               │
│  File:    campaign_projection.py                                  │
│  Trigger: Explicit call from connector when draft is generated    │
│  Writes:  peEmailStatus = "DRAFT_READY"                           │
│           peEmailCampaignName = campaign_name                     │
│           peRecommendedApproach = approach_text                   │
│  Allowlist: _PROJECTABLE_FIELDS = {peEmailStatus,                 │
│              peEmailCampaignName, peRecommendedApproach}           │
│  Does NOT write: peEmailReplyStatus, peLastEmailDate              │
│  Guard:   Requires valid EmailDraft with evidence refs            │
├──────────────────────────────────────────────────────────────────┤
│  WRITER B: EmailLifecycleSyncService (Python, Phase3A31)         │
│  ─────────────────────────────────────────────                   │
│  File:    email_lifecycle.py                                      │
│  Trigger: Explicit connector sync call (synthetic test only)      │
│  Writes:  peEmailStatus, peLastEmailDate, peEmailCampaignName,    │
│           peEmailReplyStatus (4-field allowlist)                  │
│  Guard:   _SYNCED_FIELDS frozenset validation                     │
│  Status:  Display-only; not a production writer currently         │
├──────────────────────────────────────────────────────────────────┤
│  WRITER C: EmailEventWorkflowHook (PHP, Phase3B05-B)             │
│  ───────────────────────────────────────────                     │
│  File:    EmailEventWorkflowHook.php                              │
│  Trigger: Brevo webhook → EmailEvent after-save (isNew() only)    │
│  Writes:  SENT    → peEmailStatus = "SENT"                        │
│           REPLIED → peEmailStatus = "REPLIED"                     │
│                     peEmailReplyStatus = "REPLIED"                │
│           BOUNCED → peEmailStatus = "BOUNCED"                     │
│                     peEmailReplyStatus = "BOUNCED"                │
│  Guard:   Only on new EmailEvent; guards against downgrade        │
│           (won't change REPLIED/BOUNCED back to SENT)             │
│  Status:  ACTIVE — triggered by real Brevo webhook events         │
├──────────────────────────────────────────────────────────────────┤
│  WRITER D: CrmStatusProjectionAdapter (Python, C11.3 — PLANNED)  │
│  ───────────────────────────────────────────────────────          │
│  File:    crm_status_projection.py (NOT YET IMPLEMENTED)          │
│  Trigger: Post-transition hook from all 3 C10 registries          │
│  Writes:  TBD — maps C10 state → peEmail* fields                  │
│  Guard:   One-way projection only; Integration Bot credential     │
│  Status:  PLANNED — will become the 4th writer                    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Multiple Writer Analysis (CRITICAL)

After C11.3, **four systems** could write to `Lead.peEmail*` fields:

| Event | Writer A (C09) | Writer B (Lifecycle) | Writer C (Webhook) | Writer D (C11.3) |
|---|---|---|---|---|
| Draft generated | ✅ DRAFT_READY | — | — | — |
| Approval transitions | — | — | — | ✅ PENDING_REVIEW, APPROVED, READY_TO_SEND |
| Email sent via Brevo | — | — | ✅ SENT | ✅ SENT |
| Reply received | — | — | ✅ REPLIED | ✅ REPLIED |
| Email bounces | — | — | ✅ BOUNCED | ✅ BOUNCED |
| Send execution fails | — | — | — | ✅ SEND_FAILED |
| Unsubscribe | — | — | — | ✅ UNSUBSCRIBED |

**Race condition**: When Brevo sends a `REPLIED` webhook event, BOTH Writer C (PHP hook) AND Writer D (C11.3 projection from ReplyEvent) will attempt to update the same Lead fields. The last write wins — but the values should be identical (both write "REPLIED").

### 2.3 RECOMMENDED: Single Writer Rule

```
┌─────────────────────────────────────────────────────────────────┐
│  C11.3 DESIGN CONSTRAINT: SINGLE PROJECTION WRITER              │
│                                                                  │
│  After C11.3 is active, the CrmStatusProjectionAdapter MUST     │
│  be the ONLY writer of peEmailStatus and peEmailReplyStatus.     │
│                                                                  │
│  Required actions:                                               │
│                                                                  │
│  1. Writer C (EmailEventWorkflowHook) MUST be disabled or        │
│     scoped to Task creation only. Remove peEmail* writes.        │
│                                                                  │
│  2. Writer B (EmailLifecycleSyncService) MUST be deprecated      │
│     and replaced by Writer D for all lifecycle projections.      │
│                                                                  │
│  3. Writer A (CampaignProjectionAdapter) continues to set        │
│     DRAFT_READY as the initial state. Writer D handles all       │
│     subsequent transitions.                                      │
│                                                                  │
│  4. CRM ACL MUST restrict peEmail* field writes to Integration   │
│     Bot role only. Sales roles have read-only access.             │
│                                                                  │
│  RACE MITIGATION:                                               │
│  If Writers C and D both fire for the same event (e.g., Brevo   │
│  REPLIED), they write the SAME projected value. The race is     │
│  benign (last-write-wins with identical value) but wasteful.    │
│  Disabling Writer C's field writes is preferred.                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Prohibition: Reverse Control Channel

```
┌─────────────────────────────────────────────────────────────────┐
│  PROHIBITED PATTERN: Reverse Control via Projection Fields      │
│                                                                  │
│  ❌ CRM workflow reads peEmailStatus=APPROVED → triggers send    │
│  ❌ CRM formula updates peEmailStatus → connector acts on it     │
│  ❌ Human edits peEmailReplyStatus → creates ReplyEvent          │
│  ❌ CRM hook reads peEmailStatus → advances C10 state machine    │
│                                                                  │
│  ALLOWED PATTERN: One-Way Projection                             │
│                                                                  │
│  ✅ C10 state change → post-transition hook → CRM field update   │
│  ✅ CRM field update → display in UI → human reads               │
│  ✅ CRM dashboard queries peEmailStatus for reporting            │
│  ✅ CRM workflow reads peEmailStatus → creates Task (no state    │
│     machine change)                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 Projection Mapping (C10 → CRM)

```
Connector Domain Event           →  CRM Lead Projection
─────────────────────────────────────────────────────────────────
Approval.created(DRAFT_READY)    →  peEmailStatus = "DRAFT_READY"
                                    (Writer A — existing C09 path)

Approval.submit_for_review()     →  peEmailStatus = "PENDING_REVIEW"
                                    (Writer D — NEW in C11.3)

Approval.approve()               →  peEmailStatus = "APPROVED"
                                    (Writer D — NEW in C11.3)

Approval.mark_ready_to_send()    →  peEmailStatus = "READY_TO_SEND"
                                    (Writer D — NEW in C11.3)

Execution.state → SENT           →  peEmailStatus = "SENT"
                                    peLastEmailDate = execution.updatedAt
                                    (Writer D — NEW in C11.3)

Execution.state → FAILED         →  peEmailStatus = "SEND_FAILED"
                                    (Writer D — NEW in C11.3)

ReplyEvent(status=SENT)          →  peEmailReplyStatus = "NO_REPLY"
                                    (Writer D — NEW in C11.3)

ReplyEvent(status=REPLIED)       →  peEmailStatus = "REPLIED"
                                    peEmailReplyStatus = "POSITIVE_REPLY"
                                    (Writer D — NEW in C11.3)

ReplyEvent(status=BOUNCED)       →  peEmailStatus = "BOUNCED"
                                    peEmailReplyStatus = "BOUNCED"
                                    (Writer D — NEW in C11.3)

ReplyEvent(status=UNSUBSCRIBED)  →  peEmailReplyStatus = "UNSUBSCRIBED"
                                    peEmailStatus unchanged
                                    (Writer D — NEW in C11.3)
```

---

## 3. Email Lifecycle Boundary

### 3.1 What C10 Already Owns (FROZEN — C11 MUST NOT Reimplement)

| C10 Module | Frozen Responsibility | File |
|---|---|---|
| C10.1 Human Approval | State machine: DRAFT_READY→PENDING_REVIEW→APPROVED→READY_TO_SEND / REJECTED | `human_approval.py` |
| C10.0-B Send Idempotency | SendRequest identity, SHA-256 idempotency key, SendAttempt state machine | `send_idempotency.py` |
| C10.2 Send Provider | Provider-agnostic adapter, result validation, idempotency cache | `send_provider.py` |
| C10.3 Send Execution | 6-layer approval gate, execution orchestration, state: READY_TO_SEND→SUBMITTED→PROCESSING→SENT/FAILED | `send_execution.py` |
| C10.4 Reply Tracking | ReplyEvent identity, deterministic SHA-256 ID, send trace preservation, SENT-only validation | `reply_tracking.py` |
| C10.5 Lifecycle Acceptance | Synthetic E2E tests, SideEffectLedger, zero-external-effects verification | Test files |

### 3.2 C11.3 Classification: PROJECTION / SYNCHRONIZATION ONLY

```
C11.3 Status Bridge analysis against C10 frozen modules:

┌──────────────────────────────────┬──────┬─────────────────────────┐
│ Check                            │ Pass │ Evidence                │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 reimplement send      │  NO  │ Send state machine      │
│ transition?                      │      │ remains in              │
│                                  │      │ send_execution.py       │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 reimplement provider  │  NO  │ SendProviderAdapter     │
│ execution?                       │      │ unchanged               │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 reimplement reply     │  NO  │ ReplyTrackingService    │
│ detection?                       │      │ unchanged               │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 reimplement approval  │  NO  │ HumanApprovalRegistry   │
│ state machine?                   │      │ transitions unchanged   │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 add new send path?    │  NO  │ No SMTP, no provider,   │
│                                  │      │ no credentials          │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Does C11.3 change C10 state      │  NO  │ Transition guards       │
│ transitions?                     │      │ unchanged               │
├──────────────────────────────────┼──────┼─────────────────────────┤
│ Is C11.3 ONLY projection/sync?   │ YES  │ Post-transition hook    │
│                                  │      │ writes CRM fields only  │
└──────────────────────────────────┴──────┴─────────────────────────┘

VERDICT: C11.3 is a pure projection/synchronization layer.
It does NOT reimplement any C10 frozen contract.
```

### 3.3 C10 Protocol Preservation in C11

Each C10 Protocol has two implementations after C11:

```
C10 Protocol              In-Memory (preserved)     CRM-Backed (C11 new)
─────────────────────────────────────────────────────────────────────────
HumanApprovalRegistry     InMemoryHumanApprovalRegistry  EspoCRMDraftApprovalRegistry
SendExecutionRegistry     InMemorySendExecutionRegistry  EspoCRMSendExecutionRegistry
ReplyEventRegistry        InMemoryReplyEventRegistry     EspoCRMReplyEventRegistry
SendIdempotencyRegistry   InMemorySendIdempotencyRegistry  (deferred — in-memory retained)
```

**Preservation guarantee**: All C10 offline contract tests use in-memory registries. C11 CRM-backed registries are tested separately for parity. No C10 test changes are required.

---

## 4. C11.4 DraftStore Retrieval Boundary

### 4.1 DraftStore Responsibilities (Allowed)

| Responsibility | Description | Status |
|---|---|---|
| `get(draft_id)` | Resolve draft_id → EmailDraft content | ✅ In scope |
| `content_hash(draft_id)` | Return SHA-256 hash of draft content | ✅ In scope |
| `evidence_references(draft_id)` | Return evidence reference tuple | ✅ In scope |
| Version selection | Use generation_version from EmailDraft | ✅ In scope |
| Approved content lookup | Compare hash with DraftApproval.contentHash | ✅ In scope |
| Hash verification | Verify current hash matches approved hash | ✅ In scope |

### 4.2 DraftStore Prohibitions (NOT Allowed)

| Prohibition | Reason | Boundary |
|---|---|---|
| ❌ AI generation | Chitu Intelligence domain | Not in repository |
| ❌ Scoring computation | C08 canonical_score_integration domain | Frozen contract |
| ❌ Research execution | Chitu Intelligence engine | Not in repository |
| ❌ Evidence generation | C07 evidence_extraction domain | Frozen contract |
| ❌ Provider sending | C10.2 send_provider domain | Frozen contract |
| ❌ CRM writes | DraftStore has no CRM entity | Design decision |
| ❌ Full body persistence (C11 ref impl) | Re-generation from C09 facts | CRM-backed deferred |
| ❌ Approval decision | C10.1 human_approval domain | Frozen contract |
| ❌ Prompt storage | AI reasoning is not outreach data | Security boundary |
| ❌ Scoring model internals | Chitu Intelligence domain | Not in repository |

### 4.3 DraftStore Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DRAFTSTORE BOUNDARY                           │
│                                                                  │
│  C09 FACTS (reads, does NOT modify)                              │
│  ┌──────────────────────────────────────────┐                   │
│  │ OutreachInput                            │                   │
│  │   ├── company_context (name, industry…)   │                   │
│  │   ├── talking_points (evidence-backed)    │                   │
│  │   ├── qualification_status                │                   │
│  │   ├── score_tier                          │                   │
│  │   └── recommended_product                 │                   │
│  └────────────────┬─────────────────────────┘                   │
│                   │ read-only                                    │
│                   ▼                                              │
│  ┌──────────────────────────────────────────┐                   │
│  │            DraftStore Protocol            │                   │
│  │                                           │                   │
│  │  get(draft_id) → EmailDraft               │                   │
│  │  content_hash(draft_id) → SHA-256         │                   │
│  │  evidence_references(draft_id) → tuple    │                   │
│  │                                           │                   │
│  │  Reference impl: RegeneratingDraftStore    │                   │
│  │  ┌─────────────────────────────────────┐  │                   │
│  │  │ 1. Extract lead_id from draft_id    │  │                   │
│  │  │ 2. Fetch facts from CRM             │  │                   │
│  │  │ 3. Construct OutreachInput          │  │                   │
│  │  │ 4. DeterministicEmailDraftGenerator │  │                   │
│  │  │ 5. Return EmailDraft                │  │                   │
│  │  └─────────────────────────────────────┘  │                   │
│  └────────────────┬─────────────────────────┘                   │
│                   │ provides content to                          │
│                   ▼                                              │
│  C10 LIFECYCLE (consumer, does NOT control)                      │
│  ┌──────────────────────────────────────────┐                   │
│  │ ControlledSendExecutionService            │                   │
│  │   ├── Reads draft content via DraftStore  │                   │
│  │   ├── Verifies hash vs DraftApproval      │                   │
│  │   └── Delegates to SendProviderAdapter    │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  CRM ENTITIES (NO DraftStore entity)                             │
│  ┌──────────────────────────────────────────┐                   │
│  │ DraftApproval.contentHash (varchar 64)    │                   │
│  │   → stored at approval time              │                   │
│  │   → compared at send execution time      │                   │
│  │   → mismatch → reject send               │                   │
│  │                                           │                   │
│  │ NO EmailDraft entity                      │                   │
│  │ NO draft body storage                     │                   │
│  │ NO AI reasoning storage                   │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  OUTSIDE DRAFTSTORE BOUNDARY                                     │
│  ┌──────────────────────────────────────────┐                   │
│  │ Chitu Intelligence Engine                │  NOT IN REPO      │
│  │   ├── AI research                        │                   │
│  │   ├── Scoring models                     │                   │
│  │   ├── Evidence generation                │                   │
│  │   └── Enrichment engine                  │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Content Hash Contract

```python
# Hash computation (canonical, stable ordering)
content_hash = SHA-256(
    draft.subject +
    draft.body +
    "".join(sorted(ref.evidence_id + ref.source_url
                   for ref in draft.evidence_references))
)

# Stored at approval time
DraftApproval.contentHash = content_hash

# Verified at send execution time
if DraftStore.content_hash(draft_id) != DraftApproval.get(draft_id).contentHash:
    raise ValueError("CONTENT_DRIFT: approved hash does not match current draft")
```

---

## 5. DraftApproval Integration Boundary

### 5.1 DraftApproval Responsibilities (Allowed)

| Responsibility | Description | Owner |
|---|---|---|
| ✅ Approval decision | Status transitions: PENDING_REVIEW→APPROVED/REJECTED | Human reviewer |
| ✅ Approved version reference | draft_id + approval_version stored | Connector creates |
| ✅ Approver information | reviewer_id, decided_at recorded | CRM user context |
| ✅ Rejection reason | rejection_reason when REJECTED | Human reviewer |
| ✅ Audit trail | ApprovalAuditTrace[] appended on each transition | Connector registry |

### 5.2 DraftApproval Prohibitions (NOT Allowed)

| Prohibition | Reason | Boundary |
|---|---|---|
| ❌ Draft generation | C09 email_draft_generation domain | Frozen contract |
| ❌ AI reasoning | Chitu Intelligence domain | Not in repository |
| ❌ Provider sending | C10.2-C10.3 domain | Frozen contract |
| ❌ Email content storage | DraftApproval stores draft_id, not body | Design decision |
| ❌ Recipient validation | C10.3 send_execution domain | Frozen contract |
| ❌ Campaign execution | Explicitly deferred | Out of scope |
| ❌ Auto-approval | Human approval is mandatory | Architecture invariant |

### 5.3 DraftApproval vs Neighboring Domains

```
┌─────────────────────────────────────────────────────────────────┐
│  WHAT DRAFTAPPROVAL OWNS vs WHAT IT REFERENCES                   │
│                                                                  │
│  DRAFTAPPROVAL OWNS:                                             │
│    draft_id           ← C09 identity (referenced, not owned)     │
│    approval_id        ← OWN identifier                           │
│    status             ← OWN state machine                        │
│    reviewer_id        ← OWN human reference                      │
│    rejection_reason   ← OWN decision artifact                    │
│    approval_version   ← OWN contract version                     │
│    content_hash       ← OWN integrity anchor                     │
│    audit_trace        ← OWN transition evidence                  │
│                                                                  │
│  DRAFTAPPROVAL REFERENCES:                                       │
│    lead_id            ← FK to Lead (CRM relationship)            │
│    draft_id           ← FK to C09 EmailDraft (connector domain)  │
│                                                                  │
│  DRAFTAPPROVAL DOES NOT OWN:                                     │
│    EmailDraft.subject/body  ← C09 owns                           │
│    OutreachInput facts      ← C09 owns                           │
│    SendRequest/Attempt      ← C10.0-B owns                       │
│    SendExecution            ← C10.3 owns (references approval)   │
│    Provider results         ← C10.2 owns                         │
│    ReplyEvent               ← C10.4 owns (references draft)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Entity Ownership Review

### 6.1 Ownership Classification

```
┌────────────────────┬──────────┬──────────┬──────────┬──────────────────────┐
│ ENTITY / CONCEPT   │   CRM    │CONNECTOR │  SHARED  │  RATIONALE           │
├────────────────────┼──────────┼──────────┼──────────┼──────────────────────┤
│                    │          │          │          │                      │
│ DraftApproval      │    ◐     │    ◐     │   YES    │ CRM: durable storage  │
│                    │          │          │          │ Conn: transition      │
│                    │          │          │          │   validation via      │
│                    │          │          │          │   HumanApprovalReg    │
│                    │          │          │          │   Protocol            │
│                    │          │          │          │                      │
│ SendExecution      │    ◐     │    ◐     │   YES    │ CRM: durable storage  │
│                    │          │          │          │ Conn: orchestration   │
│                    │          │          │          │   via SendExecReg     │
│                    │          │          │          │   Protocol            │
│                    │          │          │          │                      │
│ ReplyEvent         │    ◐     │    ◐     │   YES    │ CRM: durable storage  │
│                    │          │          │          │ Conn: identity +      │
│                    │          │          │          │   validation via      │
│                    │          │          │          │   ReplyEventReg       │
│                    │          │          │          │   Protocol            │
│                    │          │          │          │                      │
│ DraftStore         │    —     │    ●     │    NO    │ Connector-only        │
│                    │          │          │          │ Protocol. No CRM      │
│                    │          │          │          │ entity. No draft      │
│                    │          │          │          │ body storage.         │
│                    │          │          │          │                      │
│ SendIdempotency    │    —     │    ●     │    NO    │ Connector-internal.   │
│                    │          │          │          │ In-memory for C11.    │
│                    │          │          │          │ CRM entity deferred.  │
│                    │          │          │          │                      │
│ EmailDraft         │    —     │    ●     │    NO    │ C09 frozen. No CRM    │
│                    │          │          │          │ entity. Content re-   │
│                    │          │          │          │ generated from facts. │
│                    │          │          │          │                      │
│ Lead.peEmail*      │    ○     │    ●     │    NO    │ CRM displays.         │
│                    │          │          │          │ Connector writes      │
│                    │          │          │          │ (one-way projection). │
│                    │          │          │          │                      │
│ ResearchEvidence   │    ●     │    ○     │    NO    │ CRM owns. C10.6       │
│                    │          │          │          │ frozen. Conn reads.   │
│                    │          │          │          │                      │
│ EmailEvent         │    ●     │    —     │    NO    │ CRM owns. Brevo       │
│                    │          │          │          │ webhook ingestion.    │
│                    │          │          │          │                      │
│ OutreachInput      │    —     │    ●     │    NO    │ C09 frozen. Connector │
│                    │          │          │          │ internal facts.       │
│                    │          │          │          │                      │
└────────────────────┴──────────┴──────────┴──────────┴──────────────────────┘

LEGEND:
  ● = Primary owner (writes state, enforces contracts)
  ◐ = Shared ownership (CRM stores, Connector validates)
  ○ = Read-only consumer (reads for display/queries)
  — = No interaction
```

### 6.2 No Duplicate Entities

| Check | Result |
|---|---|
| DraftApproval exists in CRM AND connector? | **Shared** — CRM stores entity, Connector validates transitions. Not duplicated — different responsibilities. |
| SendExecution exists in CRM AND connector? | **Shared** — same pattern. CRM=persistence, Connector=orchestration. |
| ReplyEvent exists in CRM AND connector? | **Shared** — same pattern. CRM=storage, Connector=identity+tracking. |
| DraftStore exists in CRM? | **NO** — connector-only Protocol. No CRM entity planned. |
| EmailDraft exists in CRM? | **NO** — C09 frozen, no CRM entity planned. |
| SendIdempotency exists in CRM? | **NO** — connector-internal. Deferred. |

---

## 7. C11 Implementation Risks

### 7.1 HIGH Severity

| # | Risk | Impact | Required Guardrail | Affected Phase |
|---|---|---|---|---|
| **H1** | **Multiple writer race on peEmail\* fields** | 4 writers (C09 projection + lifecycle sync + Brevo webhook hook + C11.3 bridge) could conflict, causing state oscillation or audit confusion | Disable EmailEventWorkflowHook's peEmail\* writes (keep Task creation). Deprecate EmailLifecycleSyncService for projection. Single Integration Bot writer. | C11.3 |
| **H2** | **Content drift: approved draft ≠ sent draft** | Re-generation from C09 facts at send time can produce different content than what reviewer approved. Bypasses human approval gate. | Implement SHA-256 content hash at approval time. Verify hash at send execution time. Mismatch → reject + require re-approval with new draft_id. | C11.4 |
| **H3** | **EmailEventWorkflowHook continues independent writes** | Brevo webhook REPLIED/BOUNCED events will continue to write peEmailReplyStatus directly, bypassing the ReplyEvent → projection path. Creates parallel truth. | Disable field writes in the hook before C11.3 activation. Keep only Task creation logic. The connector's ReplyTrackingService becomes the sole reply authority. | C11.3 |
| **H4** | **peEmailReplyStatus varchar→enum data loss** | Production CRM may have values not in the known mapping. Migration could fail or corrupt data. | Re-run SELECT DISTINCT on production immediately before migration. Unknown values → NONE + log. Freeze writes during migration window. | C11.1 (precondition) |

### 7.2 MEDIUM Severity

| # | Risk | Impact | Required Guardrail | Affected Phase |
|---|---|---|---|---|
| **M1** | **CRM-backed registry behavior differs from in-memory** | C10 Protocol tests pass with in-memory but fail with CRM-backed. Subtle timing, ordering, or error-path differences. | Registry parity test suite: identical inputs → identical outputs. Test all error paths (DUPLICATE, REJECTED, UNKNOWN_SENT_ATTEMPT). | C11.2 |
| **M2** | **State drift: C10 connector state ≠ CRM projection** | If CRM-backed registry write succeeds but projection adapter fails, connector state and CRM display diverge. | Atomic post-transition hook. If projection fails, log + retry. Don't roll back the registry write — projection is eventually consistent. | C11.3 |
| **M3** | **DraftStore re-generation performance** | Fetching facts from CRM, constructing OutreachInput, and running DeterministicEmailDraftGenerator at send time adds latency. | Measure re-generation time. If > 500ms, consider caching content hash → draft mapping. Defer CRM-backed DraftStore to future phase if needed. | C11.4 |
| **M4** | **Brevo webhook timing vs connector reply tracking** | Brevo REPLIED webhook creates EmailEvent before connector ReplyTrackingService processes the reply. The PHP hook writes peEmailReplyStatus first, then C11.3 projection overwrites. | Disable hook field writes (H3 guardrail). ReplyEvent is the authoritative record; EmailEvent is the raw webhook log. | C11.3 |

### 7.3 LOW Severity

| # | Risk | Impact | Required Guardrail | Affected Phase |
|---|---|---|---|---|
| **L1** | **peEmailStatus enum extension backward compatibility** | Adding PENDING_REVIEW, READY_TO_SEND, SEND_FAILED to existing enum is backward-compatible. Existing records keep current values. No data migration needed. | Standard EspoCRM extension upgrade path. Verify peEmailStatus enum options after upgrade. | C11.1 |
| **L2** | **Schema预留 complexity (retryCount, maxRetries, etc.)** | Fields exist in schema but have no active logic. Could confuse CRM users or accumulate stale data. | Document that retry fields are reserved for future worker phase. Hide from CRM UI layouts until active. | C11.2 |
| **L3** | **Metadata duplication across entityDefs paths** | G01 identified duplicate entityDefs. If C11 adds 3 new entities to both paths, the duplication grows. | Add C11 entities to only one canonical path. Document which path is canonical. | C11.2 |

---

## 8. Implementation Constraints

### 8.1 Phase Sequencing Requirements

```
C11.2 (DraftApproval Implementation) — IN PROGRESS
  │
  ├── Must complete before C11.3 (Status Bridge needs CRM entities)
  │
  ▼
C11.3 (Status Bridge) — THIS AUDIT'S SCOPE
  │
  │  PRECONDITIONS:
  │  ├── H1: Single writer rule decided (which writers stay, which go)
  │  ├── H3: EmailEventWorkflowHook field writes disabled
  │  ├── H4: Production peEmailReplyStatus values re-inventoried
  │  └── C11.2 entities operational in CRM
  │
  │  IMPLEMENTATION:
  │  ├── CrmStatusProjectionAdapter (new module)
  │  ├── Post-transition hooks on all 3 registries
  │  ├── peEmailStatus enum extension (+3 values)
  │  └── peEmailReplyStatus varchar→enum migration
  │
  ▼
C11.4 (DraftStore Retrieval) — THIS AUDIT'S SCOPE
  │
  │  PRECONDITIONS:
  │  ├── H2: Content hash contract finalized
  │  ├── DraftApproval.contentHash field exists
  │  └── C11.3 projection operational
  │
  │  IMPLEMENTATION:
  │  ├── DraftStore Protocol definition
  │  ├── RegeneratingDraftStore reference implementation
  │  ├── Content hash verification in send execution path
  │  └── Integration test with SendProvider adapter
  │
  ▼
C11.5 (Verification)
```

### 8.2 Immutable Design Decisions (from this audit)

| # | Decision | Locked? | Can Change? |
|---|---|---|---|
| D1 | Connector owns lifecycle transitions; CRM is durable storage | **YES** | Only with new architecture approval |
| D2 | Lead.peEmail* fields are one-way projection only | **YES** | Architecture invariant |
| D3 | DraftStore is connector-only Protocol; no CRM entity | **YES** | Future phase can add CRM-backed impl |
| D4 | SHA-256 content hash stored at approval, verified at send | **YES** | Algorithm can change versioned |
| D5 | Single Integration Bot writer for peEmail* fields in C11.3 | **YES** | Only if writer race is otherwise resolved |
| D6 | In-memory registries preserved for offline contract tests | **YES** | Protocol contract requirement |
| D7 | C10 frozen modules unchanged by C11 | **YES** | Requires new C10 contract version |

### 8.3 C11.3 Implementation Must-Haves

1. **Single projection writer**: `CrmStatusProjectionAdapter` is the only module that writes `peEmail*` fields post-C11.3 activation.
2. **Integration Bot ACL**: Only the Integration Bot role has write permission on `peEmail*` fields. Sales roles have read-only.
3. **Post-transition hook pattern**: Projection fires AFTER the registry transition succeeds, not before. If projection fails, log + retry; do not roll back the registry.
4. **No reverse control**: CRM workflows may read `peEmail*` fields only for display, reporting, or Task creation — never to trigger state machine changes.
5. **Deprecation plan**: `EmailLifecycleSyncService` and `EmailEventWorkflowHook` field writes are deprecated with a migration window.

### 8.4 C11.4 Implementation Must-Haves

1. **Protocol-first**: Define `DraftStore` Protocol before implementing `RegeneratingDraftStore`.
2. **Hash verification gate**: `ControlledSendExecutionService.execute()` must verify `content_hash(draft_id) == approval.content_hash` before provider delegation.
3. **No body storage**: Reference implementation re-generates drafts. Do not persist EmailDraft content in CRM.
4. **Evidence reference stability**: Hash computation must use canonical, sorted ordering of evidence references for deterministic output.
5. **Timeout + fallback**: If re-generation fails (CRM unavailable, facts changed), return a clear error — do not silently proceed with unverified content.

---

## 9. Pre-Flight Checklist (Before C11.3 / C11.4)

| # | Condition | Status (2026-07-14) | Owner |
|---|---|---|---|
| **P1** | C11.2 DraftApproval entity operational in CRM | ⚠️ IN PROGRESS | C11.2 |
| **P2** | Production peEmailReplyStatus values re-inventoried | ⚠️ Required (last check: all NULL) | C11.3 |
| **P3** | EmailEventWorkflowHook modification plan approved | ⚠️ Not started | C11.3 |
| **P4** | Single writer rule documented and agreed | ⚠️ This audit recommends it | Architecture |
| **P5** | Content hash field added to DraftApproval schema | ⚠️ Not started | C11.2/C11.4 |
| **P6** | DraftStore Protocol signature finalized | ⚠️ Design exists, not implemented | C11.4 |
| **P7** | Regression Gate 7/7 PASS from clean baseline | ✅ PASS (382/382, commit 7f4ba26) | QA |
| **P8** | C10 frozen contracts verified unchanged | ⚠️ Re-verify before C11.3 | Architecture |

---

## Appendix A: Files Audited

| File | Role in Audit |
|---|---|
| `chitu_connector/chitu_connector/espocrm_sync/human_approval.py` | C10.1 approval state machine — DraftApproval contract |
| `chitu_connector/chitu_connector/espocrm_sync/send_execution.py` | C10.3 execution orchestration — SendExecution contract |
| `chitu_connector/chitu_connector/espocrm_sync/send_provider.py` | C10.2 provider adapter — SendProvider contract |
| `chitu_connector/chitu_connector/espocrm_sync/reply_tracking.py` | C10.4 reply tracking — ReplyEvent contract |
| `chitu_connector/chitu_connector/espocrm_sync/send_idempotency.py` | C10.0-B idempotency — SendRequest contract |
| `chitu_connector/chitu_connector/espocrm_sync/email_draft_generation.py` | C09 draft generation — EmailDraft contract |
| `chitu_connector/chitu_connector/espocrm_sync/campaign_projection.py` | C09 projection — Writer A (3-field allowlist) |
| `chitu_connector/chitu_connector/espocrm_sync/email_lifecycle.py` | Phase3A31 lifecycle sync — Writer B (4-field sync) |
| `chitu_connector/chitu_connector/espocrm_sync/email_lifecycle_sync.py` | Synthetic lifecycle test — reply_state values |
| `chitu_connector/chitu_connector/espocrm_sync/__init__.py` | Public interface — all C10/C09/C08 exports |
| `crm-extension/files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php` | Writer C — Brevo webhook → peEmail* writes |
| `crm-extension/Resources/entityDefs/Lead.json` | Lead entity — peEmail* field definitions |
| `crm-extension/Resources/entityDefs/EmailEvent.json` | EmailEvent entity — eventType enum |
| `docs/PHASE_G05_C11_SCOPE_ARCHITECTURE_REVIEW.md` | C11 scope and ownership boundaries |
| `docs/PHASE3C11_0_PERSISTENCE_ARCHITECTURE_APPROVAL.md` | C11 entity model design |
| `docs/PHASE_C11_1_REPLY_DRAFTSTORE_CONTRACT_REVIEW.md` | C11.1 contract review (prior audit) |
| `docs/PHASE3C11_1_FINAL_CLOSURE_GATE_REPORT.md` | C11.1 preflight closure |
| `docs/PHASE3C11_1_1_BASELINE_HYGIENE_REPORT.md` | C11.1.1 baseline hygiene |
| `docs/PHASE3C10_FREEZE.md` | C10 frozen contracts |

## Appendix B: Methodology

This audit was conducted as a **read-only architecture boundary audit**. All findings are based on static code analysis of the repository at `D:\EspoCRM-Production` on branch `master` at commit `7f4ba26`.

**Code analyzed**: 19 files across CRM extension (PHP), connector (Python), and documentation.

**No files were modified. No CRM entities were created. No database migrations were performed. No external APIs were called. No production CRM was accessed.**

---

**End of Report**
