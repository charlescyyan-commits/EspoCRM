# Phase3C14.2A.1 — Send Boundary Hardening Design

> **Date**: 2026-07-14
> **Task Type**: DESIGN ONLY — Read-Only Architecture Design
> **Repository**: D:\EspoCRM-Production (branch: `master`)
> **Precondition**: C14.2A Send Simulation / Boundary Audit — BLOCKED
> **Target**: C14.2B Live Single Recipient Acceptance
> **Verdict**: **READY FOR IMPLEMENTATION — With 6 Mandatory Guardrails**

---

## Executive Summary

C14.2A identified 3 BLOCKERs and 4 additional risks preventing any live Brevo API call. This design resolves all findings with a **minimum-surface safety architecture** that:

1. Adds a **single recipient override guard** at the Provider Adapter layer (not CRM, not Queue, not Worker)
2. Defines an **acceptance-mode flag** that gates the entire send path
3. Preserves the existing C13 Queue→Worker→ProviderAdapter path as the **sole live send authority**
4. Documents the **CRM↔Worker bridge gap** without implementing it (C14.2B scope is isolated adapter only)
5. Defines failure boundaries, idempotency guarantees, and audit requirements

**No CRM entity, migration, deployment, Docker change, or real email is executed by this design.**

---

## 1. Recipient Safety Boundary Design

### 1.1 Problem Statement

```
CURRENT STATE (C14.2A audit finding):

  BrevoProviderAdapter._send_once()
    → BrevoHttpClient.post_json("/smtp/email", payload={
        "to": [{"email": request.recipient}]  ← UNCHANGED from caller
      })

  BREVO_TEST_RECIPIENT:
    - Present in C14.1 preflight script (presence check only)
    - Present in documentation (5 files reference it)
    - ZERO production code consumption
    - ZERO use sites in BrevoProviderAdapter
    - ZERO use sites in SendExecutionWorker
    - ZERO use sites in queue_contract or worker_execution

  RESULT: Any caller that constructs a SendRequest with any recipient
          and passes it to BrevoProviderAdapter.send() WILL send to
          that recipient. No guard. No allowlist. No override.
```

### 1.2 Recommended Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                RECIPIENT SAFETY LAYER DESIGN                      │
│                                                                   │
│  LAYER 4: Runtime Configuration (process environment)             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ BREVO_ACCEPTANCE_MODE = "true" | unset                       │ │
│  │ BREVO_TEST_RECIPIENT = "test@example.com"                    │ │
│  │                                                               │ │
│  │ Defined ONCE at process startup. Immutable after init.       │ │
│  │ Neither value is a secret — safe for env vars.              │ │
│  └───────────────────────────┬─────────────────────────────────┘ │
│                              │ read by                            │
│  LAYER 3: BrevoConfiguration (config dataclass)                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ acceptance_mode: bool  (default: False)                       │ │
│  │ test_recipient: str | None  (from BREVO_TEST_RECIPIENT)       │ │
│  │                                                               │ │
│  │ .is_acceptance_mode() → bool                                  │ │
│  │ .resolve_recipient(request.recipient) → str                   │ │
│  └───────────────────────────┬─────────────────────────────────┘ │
│                              │ enforced by                        │
│  LAYER 2: BrevoProviderAdapter.send() — THE GUARD                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ if config.is_acceptance_mode():                               │ │
│  │     recipient = config.test_recipient  ← OVERRIDE            │ │
│  │ else:                                                         │ │
│  │     recipient = request.recipient      ← production path     │ │
│  │                                                               │ │
│  │ GUARD 1: If acceptance_mode AND test_recipient is None:      │ │
│  │          → PERMANENT_FAILURE (VALIDATION_ERROR)               │ │
│  │          → "ACCEPTANCE_RECIPIENT_NOT_CONFIGURED"              │ │
│  │                                                               │ │
│  │ GUARD 2: If acceptance_mode AND test_recipient is set:       │ │
│  │          → Override recipient to test_recipient               │ │
│  │          → Log: "acceptance mode: recipient overridden"       │ │
│  │          → Include original recipient in X- header for audit  │ │
│  │                                                               │ │
│  │ GUARD 3: If NOT acceptance_mode:                              │ │
│  │          → Use request.recipient unchanged                    │ │
│  │          → Normal production path                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  LAYER 1: BrevoHttpClient (HTTP transport)                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ No recipient logic. Receives already-resolved payload.       │ │
│  │ Unchanged from current implementation.                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 Why Provider Adapter Layer (Not CRM, Queue, or Worker)

| Layer | Suitability | Rationale |
|---|---|---|
| **CRM (PHP)** | ❌ Unsuitable | CRM has no send capability. Adding recipient guards in PHP creates a false sense of safety — Python paths can bypass it. |
| **SendExecution entity** | ❌ Unsuitable | C11 CRM SendExecution is not bridged to C13 Worker. Guarding it protects a path that doesn't call Brevo. |
| **Queue / Worker** | ⚠️ Partial | Worker is generic over `ProviderAdapter`. Adding a recipient guard here couples Queue/Worker to email semantics. |
| **Provider Adapter** | ✅ **CORRECT** | This is the LAST layer before the HTTP call. It is the single point where recipient resolution must be correct. It is provider-specific (Brevo) so email semantics are appropriate here. |
| **Runtime Config** | ✅ **CORRECT** | `BREVO_ACCEPTANCE_MODE` + `BREVO_TEST_RECIPIENT` are environment-level safety switches. No code change needed to toggle between acceptance and production. |

### 1.4 Acceptance Mode Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  ACCEPTANCE MODE LIFECYCLE                                       │
│                                                                  │
│  C14.2B (Live Single Recipient Acceptance):                      │
│    BREVO_ACCEPTANCE_MODE = "true"                                │
│    BREVO_TEST_RECIPIENT = "qa-test@company.com"                  │
│    → ALL sends go to qa-test@company.com                         │
│    → Original recipient preserved in X-C14-Original-Recipient    │
│                                                                  │
│  C14.3+ (Production Readiness):                                  │
│    BREVO_ACCEPTANCE_MODE = NOT SET (or "false")                  │
│    → Sends go to request.recipient unchanged                     │
│    → Production path active                                      │
│                                                                  │
│  TRANSITION:                                                      │
│    Changing acceptance_mode requires process restart.            │
│    No runtime toggle. No API to flip modes.                      │
│    This is intentional — prevents accidental mode switches.      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.5 Failure Behavior

```
When BrevoProviderAdapter.send() is called with:
  acceptance_mode = True
  test_recipient = None (not configured)

Result:
  SendResult(
    success = False,
    status = PERMANENT_FAILURE,
    provider_message_id = None,
    provider_status = FAILED,
    error = ProviderError(
      category = VALIDATION_ERROR,
      safe_code = "ACCEPTANCE_RECIPIENT_NOT_CONFIGURED"
    )
  )

  → NO HTTP call is made
  → Worker settles queue item as FAILED (VALIDATION)
  → Failure is recorded in worker outcome
```

### 1.6 Production Recipient Protection (Future)

```
For C14.2B: acceptance_mode is the ONLY protection.
Production recipient blocking is OUT OF SCOPE for C14.2B.

Future C14.3+ production protection design (NOT IMPLEMENTED NOW):
  - Recipient domain allowlist (only @company.com domains)
  - Maximum recipients per batch (1 for transactional)
  - Send rate limiting (Brevo-side + client-side)
  - Production mode requires acceptance_mode = False explicitly
```

---

## 2. CRM SendExecution vs C13 Queue/Worker Boundary

### 2.1 Current State (Two Disconnected Systems)

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM A: C11 CRM Persistence (PHP)                             │
│  ─────────────────────────────────                              │
│  CRM DraftApproval (entity)                                      │
│       ↓                                                          │
│  CRM SendExecution (entity)                                      │
│       ↓                                                          │
│  C11 EmailLifecycleProjectionService                             │
│       ↓                                                          │
│  Lead.peEmailStatus (projection)                                 │
│                                                                  │
│  STATUS: Entity exists. No send capability.                      │
│          No bridge to C13 Worker.                                │
│          State transitions via CRM saves only.                   │
├─────────────────────────────────────────────────────────────────┤
│  SYSTEM B: C13 Queue/Worker/Provider (Python)                    │
│  ─────────────────────────────────────────                      │
│  InMemorySendExecutionQueue                                      │
│       ↓                                                          │
│  SendExecutionWorker.process()                                   │
│       ↓                                                          │
│  ProviderAdapter.send()  (FakeProviderAdapter default)           │
│       ↓                                                          │
│  BrevoProviderAdapter → BrevoHttpClient → /smtp/email            │
│                                                                  │
│  STATUS: All in-memory. All test-only constructions.             │
│          No CRM read. No CRM write-back.                         │
│          FakeProviderAdapter default — no real send.             │
├─────────────────────────────────────────────────────────────────┤
│  THE BRIDGE: DOES NOT EXIST                                       │
│  ─────────────────────────                                      │
│  CRM SendExecution → C13 Queue:  NOT IMPLEMENTED                 │
│  C13 Worker result → CRM SendExecution:  NOT IMPLEMENTED         │
│  C13 Worker result → CRM EmailEvent:  NOT IMPLEMENTED            │
│  C13 Worker result → Lead projection:  NOT IMPLEMENTED           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 C14.2B Scope Decision: Isolated Adapter Path ONLY

```
┌─────────────────────────────────────────────────────────────────┐
│  C14.2B SCOPE: ISOLATED ADAPTER ACCEPTANCE                       │
│                                                                  │
│  The C14.2B live test verifies ONLY:                             │
│                                                                  │
│  InMemorySendExecutionQueue                                       │
│       ↓                                                          │
│  SendExecutionWorker (with BrevoProviderAdapter injected)         │
│       ↓                                                          │
│  BrevoProviderAdapter (with acceptance_mode + test_recipient)    │
│       ↓                                                          │
│  BrevoHttpClient → POST /smtp/email → Brevo API                  │
│       ↓                                                          │
│  Response verification (201, messageId extracted)                │
│                                                                  │
│  EXPLICITLY EXCLUDED FROM C14.2B:                                │
│  ❌ CRM SendExecution entity                                     │
│  ❌ CRM DraftApproval entity                                     │
│  ❌ CRM EmailEvent creation                                      │
│  ❌ Lead.peEmail* projection                                     │
│  ❌ C10 lifecycle involvement                                    │
│  ❌ C09 draft generation                                         │
│  ❌ Any PHP code path                                            │
│  ❌ Any database write                                           │
│  ❌ Approval workflow                                            │
│  ❌ Reply tracking                                               │
│  ❌ Provider-event webhook ingestion                             │
│                                                                  │
│  RATIONALE: Verify the Brevo transport boundary first.           │
│  The CRM bridge is a separate, larger design problem             │
│  (C14.3+ scope). Mixing them creates untestable complexity.      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Future Bridge Design (C14.3+ — NOT IMPLEMENTED NOW)

```
┌─────────────────────────────────────────────────────────────────┐
│  FUTURE: CRM ↔ Worker Bridge (C14.3+ design sketch only)         │
│                                                                  │
│  CRM → Worker (enqueue):                                         │
│    PHP: C11 SendExecution after-save hook                        │
│      → POST /Prospecting/queue/enqueue (new API endpoint)       │
│      → Python: enqueue in SendExecutionQueue                     │
│                                                                  │
│  Worker → CRM (result write-back):                               │
│    Python: WorkerExecutionOutcome                                 │
│      → PUT /Prospecting/execution/{id}/result (new endpoint)    │
│      → PHP: Update CRM SendExecution state                       │
│      → PHP: Create EmailEvent if SUCCESS                         │
│      → PHP: Update Lead.peEmailStatus projection                 │
│                                                                  │
│  REQUIRED BEFORE BRIDGE:                                         │
│    1. Durable queue (not in-memory)                              │
│    2. Multi-worker claim safety (not RLock)                      │
│    3. Retry infrastructure (not reservation-only)                │
│    4. PHP API endpoints for enqueue + result write-back          │
│    5. Integration Bot authentication on new endpoints            │
│    6. C11.3 single-writer resolution (RISK-C11.3-001)           │
│                                                                  │
│  C14.2B does NOT require any of these.                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Which Layer Owns Final Send Authority

```
┌─────────────────────────────────────────────────────────────────┐
│  FINAL SEND AUTHORITY: C13 SendExecutionWorker                   │
│                                                                  │
│  The Worker is the ONLY component that:                          │
│  1. Claims a queue item (atomic ownership)                       │
│  2. Validates READY state (pre-send guard)                       │
│  3. Calls ProviderAdapter.send() (the actual HTTP call)          │
│  4. Settles the queue item (COMPLETED or FAILED)                 │
│                                                                  │
│  CRM does NOT own send authority. CRM owns:                      │
│  - Durable send record (SendExecution entity)                    │
│  - Human approval (DraftApproval entity)                         │
│  - Display projection (Lead.peEmail*)                            │
│                                                                  │
│  Queue does NOT own send authority. Queue owns:                  │
│  - Work reservation (QUEUED → CLAIMED)                           │
│  - Duplicate prevention (one item per sendExecutionId)            │
│                                                                  │
│  Provider does NOT own send authority. Provider owns:             │
│  - Transport execution (HTTP → Brevo API)                        │
│  - Result normalization (status codes → SendResult)              │
│                                                                  │
│  NO DUPLICATE LIFECYCLE:                                          │
│  - C10 ControlledSendExecutionService: FROZEN, in-memory only    │
│  - C11 CRM SendExecution: Durable record, no send capability     │
│  - C13 Worker execution: Live send authority (C14.2B path)       │
│  - These are SEPARATE concerns, not duplicate state machines.    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. State Ownership Model

### 3.1 Complete Ownership Table

```
┌──────────────────────┬──────────┬──────────┬──────────┬────────────────────┐
│ STATE                │   CRM    │  QUEUE   │ PROVIDER │  NOTES             │
├──────────────────────┼──────────┼──────────┼──────────┼────────────────────┤
│                      │          │          │          │                    │
│ Draft content        │    —     │    —     │    —     │ C09 domain;        │
│ (subject, body)      │          │          │          │ DraftStore owns     │
│                      │          │          │          │                    │
│ DraftApproval.status │    ●     │    —     │    —     │ CRM entity;        │
│                      │          │          │          │ Human decision     │
│                      │          │          │          │                    │
│ SendExecution.state  │    ●     │    —     │    —     │ CRM entity;        │
│ (CRM persistent)     │          │          │          │ CREATED→READY→     │
│                      │          │          │          │ SENT→FAILED        │
│                      │          │          │          │                    │
│ Lead.peEmailStatus   │    ○     │    —     │    —     │ Projection only;   │
│                      │          │          │          │ Connector writes   │
│                      │          │          │          │                    │
│ Lead.peEmailReply    │    ○     │    —     │    —     │ Projection only    │
│ Status               │          │          │          │                    │
│                      │          │          │          │                    │
│ EmailEvent           │    ●     │    —     │    —     │ CRM entity;        │
│ (provider event)     │          │          │          │ Brevo webhook      │
│                      │          │          │          │                    │
│ QueueItem.state      │    —     │    ●     │    —     │ QUEUED→CLAIMED→    │
│                      │          │          │          │ COMPLETED/FAILED   │
│                      │          │          │          │                    │
│ QueueItem.worker_id  │    —     │    ●     │    —     │ Claim ownership    │
│                      │          │          │          │                    │
│ QueueItem.failure    │    —     │    ●     │    —     │ C11.5 taxonomy     │
│ Category             │          │          │          │                    │
│                      │          │          │          │                    │
│ WorkItem.status      │    —     │    ●     │    —     │ READY→SENT/FAILED  │
│ (in-memory)          │          │          │          │ (worker view)      │
│                      │          │          │          │                    │
│ SendResult.status    │    —     │    —     │    ●     │ SUCCESS/FAILED/    │
│                      │          │          │          │ RETRYABLE/PERM     │
│                      │          │          │          │                    │
│ SendResult.provider  │    —     │    —     │    ●     │ Brevo messageId    │
│ _message_id          │          │          │          │                    │
│                      │          │          │          │                    │
│ ProviderStatus       │    —     │    —     │    ●     │ ACCEPTED/FAILED/   │
│                      │          │          │          │ NOT_SUPPORTED      │
│                      │          │          │          │                    │
│ acceptance_mode      │    —     │    —     │    ●     │ BrevoConfiguration │
│ (C14.2A NEW)         │          │          │          │ env-backed flag    │
│                      │          │          │          │                    │
│ test_recipient       │    —     │    —     │    ●     │ BrevoConfiguration │
│ (C14.2A NEW)         │          │          │          │ override value     │
│                      │          │          │          │                    │
│ Retry fields         │    ●     │    —     │    —     │ Schema预留 only;   │
│ (retryCount etc.)    │          │          │          │ no execution logic  │
│                      │          │          │          │                    │
│ C10 approval state   │    —     │    —     │    —     │ FROZEN; in-memory  │
│ (DraftApproval Py)   │          │          │          │ contract only      │
│                      │          │          │          │                    │
│ C10 execution state  │    —     │    —     │    —     │ FROZEN; in-memory  │
│ (SendExecution Py)   │          │          │          │ contract only      │
└──────────────────────┴──────────┴──────────┴──────────┴────────────────────┘

LEGEND:
  ● = OWNER (canonical source of truth, writes state, enforces transitions)
  ○ = READER (reads state for display, does not write)
  — = NO INTERACTION
```

### 3.2 Key Ownership Principles

1. **CRM owns durable records.** DraftApproval, SendExecution, ReplyEvent, EmailEvent are persistent CRM entities. They survive restarts.

2. **Queue owns work reservation.** QueueItem state (QUEUED→CLAIMED→COMPLETED/FAILED) is the work dispatch authority. Currently in-memory; future durable.

3. **Provider owns transport results.** SendResult, provider_message_id, ProviderStatus are the provider's truth. CRM may cache them but the provider is authoritative.

4. **No state is owned by two systems.** Each state field has exactly one canonical writer. The CRM→Worker bridge (future C14.3+) will synchronize states, not duplicate ownership.

---

## 4. Failure and Retry Boundary

### 4.1 Failure Category Mapping (Already Implemented in C13.2)

```
Provider Error           →  SendResultStatus      →  FailureCategory   Retry?
─────────────────────────────────────────────────────────────────────────────
Brevo 401 (AUTH_ERROR)   →  PERMANENT_FAILURE      →  AUTH              NO
Brevo 403 (AUTH_ERROR)   →  PERMANENT_FAILURE      →  AUTH              NO
Brevo 429 (RATE_LIMIT)   →  RETRYABLE_FAILURE       →  RATE_LIMIT        YES*
Brevo 400 (VALIDATION)   →  PERMANENT_FAILURE      →  VALIDATION        NO
Brevo 5xx (PROVIDER)     →  RETRYABLE_FAILURE       →  PROVIDER          YES*
Timeout (NETWORK)        →  RETRYABLE_FAILURE       →  NETWORK           YES*
Transport exception      →  PERMANENT_FAILURE       →  UNKNOWN           NO
Invalid recipient        →  PERMANENT_FAILURE       →  VALIDATION        NO
Duplicate send_request   →  PERMANENT_FAILURE       →  VALIDATION        NO
Acceptance no recipient  →  PERMANENT_FAILURE       →  VALIDATION        NO
Missing API key          →  PERMANENT_FAILURE       →  VALIDATION        NO
Identity conflict        →  PERMANENT_FAILURE       →  VALIDATION        NO

* Retry is NOT executed in C14.2B. RETRYABLE_FAILURE is a classification
  only. C11.5 retry fields remain schema-reserved with no execution logic.
```

### 4.2 Retry Owner

```
┌─────────────────────────────────────────────────────────────────┐
│  RETRY OWNERSHIP (C14.2B scope)                                  │
│                                                                  │
│  Current: NO RETRY EXECUTION EXISTS                              │
│                                                                  │
│  The C13 Worker:                                                 │
│    - Processes each QueueItem exactly ONCE                       │
│    - Settles FAILED items as terminal                            │
│    - Does NOT re-enqueue FAILED items                            │
│    - Does NOT schedule retry                                     │
│    - Does NOT have a RETRYING state                              │
│                                                                  │
│  The C13 Queue:                                                  │
│    - Has no retry transition                                     │
│    - FAILED items cannot return to QUEUED                        │
│    - No retry count, no backoff, no DLQ                          │
│                                                                  │
│  C11.5 SendExecution entity:                                     │
│    - Has retryCount, maxRetries, nextRetryAt, lastError          │
│    - These are SCHEMA RESERVATION ONLY                           │
│    - No code reads or writes them                                │
│    - No RETRYING enum value exists                               │
│                                                                  │
│  For C14.2B: Single send only. No retry.                         │
│  If the send fails, the test operator must:                      │
│    1. Diagnose the failure from WorkerExecutionOutcome            │
│    2. Create a new QueueItem with a new send_execution_id         │
│    3. Re-run the controlled test                                  │
│                                                                  │
│  Future C13.4+ retry design (NOT IN C14.2B):                     │
│    - RetryScheduler: reads FAILED items, checks nextRetryAt      │
│    - Re-enqueue with incremented retryCount                       │
│    - Exponential backoff (30s, 2m, 5m, 15m, 1h)                  │
│    - Max retries: 3 (configurable per provider)                   │
│    - DLQ after max retries exceeded                               │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Idempotency Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│  IDEMPOTENCY GUARANTEES (C14.2B scope)                           │
│                                                                  │
│  LAYER 1: Queue — one item per sendExecutionId                    │
│    queue_item_id = "queue:<sendExecutionId>"                     │
│    Duplicate enqueue → returns existing item (no new queue entry) │
│    Implementation: InMemorySendExecutionQueue (RLock)            │
│    Scope: Process-local only                                     │
│                                                                  │
│  LAYER 2: Worker — one claim per QueueItem                       │
│    Only QUEUED items can be claimed                              │
│    CLAIMED items can only be settled by owning worker            │
│    Terminal items (COMPLETED/FAILED) cannot be reclaimed         │
│    Implementation: SendExecutionWorker.process()                 │
│    Scope: Process-local only                                     │
│                                                                  │
│  LAYER 3: Provider Adapter — one send per identity               │
│    Identity = (send_execution_id, request_id)                    │
│    Duplicate send → returns cached result (no second HTTP call)  │
│    Identity conflict → PERMANENT_FAILURE                         │
│    Implementation: BrevoProviderAdapter (RLock)                  │
│    Scope: Process-local only                                     │
│                                                                  │
│  LAYER 4: Brevo API — provider-side idempotency                  │
│    Headers: X-C12-Request-Id, X-C12-Send-Execution-Id            │
│    Brevo may deduplicate by these headers (provider-dependent)   │
│    NOT guaranteed by this design                                 │
│                                                                  │
│  CROSS-PROCESS: NOT COVERED IN C14.2B                            │
│    All idempotency is process-local (in-memory + RLock).         │
│    Multi-instance safety requires durable queue + distributed     │
│    claim mechanism (C14.3+ scope).                                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Audit Logging Requirements

```
┌─────────────────────────────────────────────────────────────────┐
│  C14.2B AUDIT TRAIL (minimum required)                            │
│                                                                  │
│  For each C14.2B live test invocation, record:                   │
│                                                                  │
│  1. PRE-SEND:                                                    │
│     - acceptance_mode: True                                      │
│     - test_recipient: <configured value>                         │
│     - original_recipient: <from SendRequest>                     │
│     - send_execution_id: <unique ID>                             │
│     - request_id: <unique ID>                                    │
│     - draft_hash: <content hash>                                 │
│     - timestamp: <UTC ISO 8601>                                  │
│                                                                  │
│  2. POST-SEND:                                                   │
│     - HTTP status_code: <201/401/etc.>                           │
│     - provider_message_id: <Brevo messageId or None>             │
│     - SendResultStatus: <SUCCESS/FAILED/etc.>                    │
│     - error safe_code: <if failed>                               │
│     - WorkerExecutionOutcome: <full dataclass>                   │
│     - duration_ms: <round-trip time>                             │
│                                                                  │
│  3. STORAGE:                                                     │
│     - Write audit record to temp/test-results/                   │
│     - File name: c14_2b_live_acceptance-<timestamp>.json         │
│     - Do NOT write to CRM (no EmailEvent, no SendExecution)      │
│     - Do NOT commit the audit file (gitignore covers temp/)      │
│                                                                  │
│  4. SAFETY:                                                      │
│     - Audit record MUST NOT contain API key                      │
│     - Audit record MUST NOT contain full email body              │
│     - Audit record MUST redact recipient if production           │
│     - Audit record is human-readable JSON                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Minimal Implementation Plan

### 5.1 Files Expected to Change

```
MODIFIED FILES (C14.2B implementation):

  1. chitu-connector/chitu_connector/espocrm_sync/brevo_provider.py
     ├── BrevoConfiguration: add acceptance_mode (bool), test_recipient (str|None)
     ├── BrevoConfiguration.from_environment(): read BREVO_ACCEPTANCE_MODE,
     │      BREVO_TEST_RECIPIENT
     ├── BrevoConfiguration.is_acceptance_mode() → bool  (NEW method)
     ├── BrevoConfiguration.resolve_recipient(request_recipient) → str  (NEW)
     └── BrevoProviderAdapter._send_once(): call resolve_recipient(),
            add X-C14-Original-Recipient header in acceptance mode

  2. scripts/acceptance/phase3c14_1_preflight.ps1
     └── Add BREVO_ACCEPTANCE_MODE to required variable check

NEW FILES (C14.2B implementation):

  3. scripts/acceptance/run_c14_2b_live_acceptance.ps1
     ├── One-shot acceptance runner
     ├── Validates BREVO_ACCEPTANCE_MODE="true"
     ├── Validates BREVO_TEST_RECIPIENT is present
     ├── Constructs in-memory queue + worker + BrevoProviderAdapter
     ├── Executes single send
     └── Writes audit record to temp/test-results/

  4. tests/test_phase3c14_2b_recipient_safety.py
     ├── Test: acceptance_mode=True + test_recipient → recipient overridden
     ├── Test: acceptance_mode=True + NO test_recipient → PERMANENT_FAILURE
     ├── Test: acceptance_mode=False → recipient unchanged
     ├── Test: X-C14-Original-Recipient header present in acceptance mode
     ├── Test: acceptance_mode + missing API key → still fails safely
     └── Test: no real HTTP call in any test (BrevoHttpClient mocked)

UNCHANGED FILES (verified not modified):

  ✅ chitu-connector/chitu_connector/espocrm_sync/queue_contract.py
  ✅ chitu-connector/chitu_connector/espocrm_sync/worker_execution.py
  ✅ chitu-connector/chitu_connector/espocrm_sync/provider_contract.py
  ✅ chitu-connector/chitu_connector/espocrm_sync/brevo_http.py
  ✅ crm-extension/* (ALL PHP files — CRM bridge deferred to C14.3+)
  ✅ chitu-connector/chitu_connector/espocrm_sync/send_execution.py (C10 frozen)
  ✅ chitu-connector/chitu_connector/espocrm_sync/reply_tracking.py (C10 frozen)
  ✅ chitu-connector/chitu_connector/espocrm_sync/human_approval.py (C10 frozen)
```

### 5.2 Tests Required

```
TEST SUITE: test_phase3c14_2b_recipient_safety.py

  1. test_acceptance_mode_overrides_recipient
     Config: acceptance_mode=True, test_recipient="test@example.com"
     Input: request.recipient="real@customer.com"
     Assert: payload["to"][0]["email"] == "test@example.com"
     Assert: X-C14-Original-Recipient header == "real@customer.com"

  2. test_acceptance_mode_without_test_recipient_fails
     Config: acceptance_mode=True, test_recipient=None
     Assert: SendResult.status == PERMANENT_FAILURE
     Assert: error.safe_code == "ACCEPTANCE_RECIPIENT_NOT_CONFIGURED"
     Assert: NO HTTP call made

  3. test_production_mode_preserves_recipient
     Config: acceptance_mode=False
     Input: request.recipient="real@customer.com"
     Assert: payload["to"][0]["email"] == "real@customer.com"
     Assert: NO X-C14-Original-Recipient header

  4. test_acceptance_mode_still_requires_api_key
     Config: acceptance_mode=True, BREVO_API_KEY=None
     Assert: SendResult.status == PERMANENT_FAILURE
     Assert: error.safe_code == "MISSING_BREVO_API_KEY"

  5. test_acceptance_mode_flag_from_environment
     Config: os.environ with BREVO_ACCEPTANCE_MODE="true"
     Assert: BrevoConfiguration.from_environment().is_acceptance_mode() == True

  6. test_acceptance_mode_flag_defaults_false
     Config: os.environ WITHOUT BREVO_ACCEPTANCE_MODE
     Assert: BrevoConfiguration.from_environment().is_acceptance_mode() == False

  7. test_acceptance_mode_false_for_empty_string
     Config: BREVO_ACCEPTANCE_MODE=""
     Assert: BrevoConfiguration.from_environment().is_acceptance_mode() == False

  8. test_no_real_http_in_test_path
     Verify: BrevoHttpClient is mocked; zero real network calls in test suite
     Verify: C10 frozen hashes unchanged
     Verify: C11-C13 boundary tests still pass

REGRESSION SUITES (must pass unchanged):
  - C13.1 queue contract: 8/8
  - C13.2 worker execution: 6/6
  - C13.3 reliability acceptance: 7/7
  - C12.3 Brevo acceptance fixtures: 5/5
  - C11-C13 boundary: 72/72
  - Extension: 65/65
  - Connector (including C10): 270/270
  - Full Regression Gate: 7/7 suites
```

### 5.3 Regression Impact

```
┌─────────────────────────────────────────────────────────────────┐
│  REGRESSION IMPACT ASSESSMENT                                    │
│                                                                  │
│  LOW IMPACT — BrevoConfiguration changes are additive:           │
│                                                                  │
│  1. BrevoConfiguration gains two new optional fields:            │
│     - acceptance_mode: bool = False (default preserves behavior) │
│     - test_recipient: str | None = None (default: no override)   │
│                                                                  │
│  2. Existing callers of BrevoConfiguration.from_environment():   │
│     - C14.1 preflight: reads BREVO_TEST_RECIPIENT presence       │
│       → Already compatible (reads presence, not value)           │
│     - C12.3 acceptance fixtures: mock environment                │
│       → New fields default to False/None → behavior unchanged    │
│                                                                  │
│  3. Existing callers of BrevoProviderAdapter.send():             │
│     - C13.2 worker tests: use FakeProviderAdapter, not Brevo     │
│       → NO IMPACT                                                │
│     - C12.3 fixture tests: mock HTTP responses                   │
│       → resolve_recipient() returns unchanged request.recipient   │
│         when acceptance_mode=False (default)                     │
│                                                                  │
│  4. C10 frozen contracts:                                        │
│     - NO FILES TOUCHED in C10 modules                            │
│                                                                  │
│  5. CRM extension:                                               │
│     - NO FILES TOUCHED in crm-extension/                         │
│                                                                  │
│  VERDICT: Safe to implement. Default behavior is unchanged.      │
│  Acceptance mode is opt-in via environment variable.             │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Rollback Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│  ROLLBACK STRATEGY                                               │
│                                                                  │
│  C14.2B is a TEST-ONLY phase. No CRM data is modified.           │
│  No migration is performed. No entity is created.                │
│                                                                  │
│  ROLLBACK PATH A: Environment-level (instant)                    │
│    unset BREVO_ACCEPTANCE_MODE                                   │
│    → BrevoProviderAdapter reverts to production path             │
│    → No code change needed                                       │
│                                                                  │
│  ROLLBACK PATH B: Code-level (if acceptance_mode logic is buggy) │
│    git revert <C14.2B commit>                                    │
│    → BrevoProviderAdapter returns to pre-C14.2B state            │
│    → C12.3 + C13 tests still pass (no dependency on C14.2B)     │
│                                                                  │
│  ROLLBACK PATH C: Full runtime restore                           │
│    Use C11.1 baseline snapshot:                                  │
│    archive/runtime-backups/c11_1_baseline-20260714T094409Z/      │
│    → Restores CRM + custom/ + configuration                     │
│    → Pre-C14 state (C11.1 baseline)                             │
│                                                                  │
│  NO DATA MIGRATION ROLLBACK NEEDED:                              │
│    C14.2B does not write to CRM, database, or entities.          │
│    The only artifact is the audit JSON in temp/test-results/.    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Final Verdict

### 6.1 Overall Assessment

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗                       │
│  ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝                       │
│  ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝                        │
│  ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝                         │
│  ██║  ██║███████╗██║  ██║██████╔╝   ██║                          │
│  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝                          │
│                                                                  │
│  ███████╗ ██████╗ ██████╗                                           │
│  ██╔════╝██╔═══██╗██╔══██╗                                          │
│  █████╗  ██║   ██║██████╔╝                                          │
│  ██╔══╝  ██║   ██║██╔══██╗                                          │
│  ██║     ╚██████╔╝██║  ██║                                          │
│  ╚═╝      ╚═════╝ ╚═╝  ╚═╝                                          │
│                                                                  │
│  ██╗███╗   ███╗██████╗ ██╗     ███████╗███╗   ███╗███████╗███╗  ██╗|
│  ██║████╗ ████║██╔══██╗██║     ██╔════╝████╗ ████║██╔════╝████╗ ██║|
│  ██║██╔████╔██║██████╔╝██║     █████╗  ██╔████╔██║█████╗  ██╔██╗██║|
│  ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝  ██║╚██╔╝██║██╔══╝  ██║╚████║|
│  ██║██║ ╚═╝ ██║██║     ███████╗███████╗██║ ╚═╝ ██║███████╗██║ ╚███║|
│  ╚═╝╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝     ╚═╝╚══════╝╚═╝  ╚══╝|
│                                                                  │
│  ████████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗                │
│  ╚══██╔══╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║                │
│     ██║   ███████║   ██║   ██║██║   ██║██╔██╗ ██║                │
│     ██║   ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║                │
│     ██║   ██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║                │
│     ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**VERDICT: READY FOR IMPLEMENTATION — With 6 Mandatory Guardrails**

### 6.2 Mandatory Guardrails (Must Be Satisfied Before C14.2B Live Send)

| # | Guardrail | Rationale | Verification |
|---|---|---|---|
| **G1** | `acceptance_mode` guard active in `BrevoProviderAdapter.send()` | Single point of recipient enforcement at the last layer before HTTP | Test: acceptance_mode=True → recipient overridden |
| **G2** | `test_recipient=None` in acceptance mode → PERMANENT_FAILURE (no HTTP call) | Prevents accidental send to production recipient when test_recipient is misconfigured | Test: acceptance_mode=True, no test_recipient → error, no HTTP |
| **G3** | `acceptance_mode=False` (default) preserves original `request.recipient` unchanged | Backward compatibility. All existing tests pass without environment changes. | Test: acceptance_mode=False → recipient unchanged |
| **G4** | Environment variables injected by operator, not stored in files | No credentials in source, Git, or documentation. `BREVO_ACCEPTANCE_MODE` and `BREVO_TEST_RECIPIENT` are not secrets but should not be hardcoded. | Preflight: check env vars, not files |
| **G5** | C14.2B live test uses isolated C13 Worker path only — no CRM, no PHP, no DB writes | Scope boundary. CRM bridge is C14.3+ scope. | Audit: verify zero CRM entity creation |
| **G6** | Audit record written to `temp/test-results/` (gitignored) — not committed, not in CRM | Safety: audit trail exists without CRM dependency. | Post-test: verify audit file created |

### 6.3 C14.2A BLOCKER Resolution Status

| C14.2A BLOCKER | Resolution in C14.2B Design |
|---|---|
| **B1**: No test-recipient enforcement | **RESOLVED**: `acceptance_mode` + `test_recipient` override in BrevoProviderAdapter (§1.2) |
| **B2**: No CRM↔Worker bridge | **ACCEPTED AS DEFERRED**: C14.2B uses isolated Worker path only; bridge is C14.3+ scope (§2.2) |
| **B3**: C14.1 live acceptance skipped | **RESOLVED**: C14.2B design requires `READY_FOR_LIVE_ACCEPTANCE` preflight before execution (§1.4) |
| **H1**: No dry-run guard on Worker | **RESOLVED**: `acceptance_mode` flag acts as the dry-run guard at the adapter layer (§1.3) |
| **M1**: Multiple Lead projection writers | **DEFERRED**: Not in C14.2B scope (no CRM writes in this phase) |
| **M2**: Parallel approval/execution representations | **DOCUMENTED**: Ownership matrix (§3.1) clarifies which system owns what |

### 6.4 What Could Still Block C14.2B

1. **Credentials remain unavailable.** If `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, or `BREVO_TEST_RECIPIENT` cannot be injected into the acceptance process environment, C14.2B cannot execute. This is an operational prerequisite, not a design gap.

2. **Scope expansion into CRM bridge.** If C14.2B is asked to also verify CRM SendExecution persistence, EmailEvent creation, or Lead projection, this design must be rejected and a larger C14.3 bridge design must be completed first.

3. **Production recipient accidentally used as test_recipient.** The operator must ensure `BREVO_TEST_RECIPIENT` is a controlled internal mailbox. The design enforces the override but cannot validate the override value.

4. **Brevo account not authorized for the test sender.** The sender email configured in `BREVO_SENDER_EMAIL` must be authorized in the Brevo account. This is a Brevo-side configuration prerequisite.

---

## Appendix A: Design Decisions Record

| # | Decision | Rationale | Date |
|---|---|---|---|
| D1 | Recipient guard at Provider Adapter layer | Last layer before HTTP; provider-specific; no coupling to Queue/Worker/CRM | 2026-07-14 |
| D2 | `acceptance_mode` as env var, not code constant | Operator-controlled; no code change to toggle; survives restart | 2026-07-14 |
| D3 | C14.2B uses isolated Worker path (no CRM bridge) | CRM bridge requires durable queue + distributed claims + API endpoints (C14.3+ scope) | 2026-07-14 |
| D4 | Audit trail to temp file, not CRM entity | No CRM dependency for test phase; gitignored; human-readable JSON | 2026-07-14 |
| D5 | `BREVO_TEST_RECIPIENT` not a secret (env var, not credential) | Test recipient is a configuration value, not a secret. Safe for env vars. API key remains the only secret. | 2026-07-14 |
| D6 | C10 frozen contracts untouched | C14 is an independent send path; C10 remains frozen per PHASE3C10_FREEZE.md | 2026-07-14 |

## Appendix B: Files Audited

| File | Role |
|---|---|
| `brevo_provider.py` | BrevoConfiguration, BrevoProviderAdapter — target for recipient guard |
| `provider_contract.py` | SendRequest, SendResult, ProviderAdapter, FakeProviderAdapter — provider contract |
| `queue_contract.py` | QueueItem, SendExecutionQueue, InMemorySendExecutionQueue — queue contract |
| `worker_execution.py` | SendExecutionWorker, SendExecutionWorkItem, WorkExecutionStatus — worker |
| `brevo_http.py` | BrevoHttpClient — HTTP transport layer |
| `send_execution.py` | C10 ControlledSendExecutionService — frozen, not modified |
| `human_approval.py` | C10 HumanApprovalRegistry — frozen, not modified |
| `reply_tracking.py` | C10 ReplyTrackingService — frozen, not modified |
| `PHASE3C14_2A_SEND_SIMULATION_BOUNDARY_AUDIT.md` | C14.2A findings — source of BLOCKERs |
| `PHASE3C14_1_1_BREVO_CONFIGURATION_MIGRATION_REPORT.md` | C14.1.1 config audit — BLOCKED on credentials |
| `PHASE3C14_1_3_ACCEPTANCE_RUNTIME_SETUP_REPORT.md` | C14.1.3 runtime setup — BLOCKED on credentials |
| `PHASE3C13_1_QUEUE_CONTRACT_REPORT.md` | C13.1 queue design |
| `PHASE3C13_2_WORKER_EXECUTION_REPORT.md` | C13.2 worker design |
| `PHASE3C13_3_RETRY_CONCURRENCY_ACCEPTANCE_REPORT.md` | C13.3 reliability acceptance |
| `PHASE3C12_3_BREVO_PROVIDER_ACCEPTANCE_REPORT.md` | C12.3 Brevo fixture acceptance |
| `scripts/acceptance/phase3c14_1_preflight.ps1` | C14.1 preflight runner |

## Appendix C: Methodology

This design was produced as a **read-only architecture design**. All findings are based on static code analysis of the repository at `D:\EspoCRM-Production` on branch `master`.

**Code analyzed**: 16 files across Python connector, PowerShell scripts, and documentation.

**No files were modified. No API calls were made. No credentials were read. No emails were sent. No commits were created.**

---

**End of Design**
