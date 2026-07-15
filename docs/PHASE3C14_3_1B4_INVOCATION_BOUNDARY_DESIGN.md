# Phase C14.3.1B-4 — Runtime Invocation Boundary Design

## Final Verdict

**RECOMMENDED_OPTION: C — Explicit Command Invocation**

**READY_FOR_IMPLEMENTATION: YES** (limited to the invocation boundary described in Section 4; does not authorize CRM hooks, schedulers, or automatic triggers)

---

## 1. Current Architecture — The Missing Link

### 1.1 What Exists (B-1, B-2, B-3)

```
┌──────────────────────────────────────────────────────────────────┐
│  B-3: Durable Payload Snapshot (SQLite)                          │
│  payload_snapshot.py                                              │
│  ├── PayloadSnapshotInput  (execution_id, content_hash,          │
│  │                           recipient, subject, body, campaign)  │
│  ├── PayloadSnapshot       (immutable, self-verifying)            │
│  ├── SqlitePayloadSnapshotStore.save_if_absent()                  │
│  └── SqlitePayloadSnapshotStore.get()  ← survives restart         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │  ApprovedDeliveryPayloadSource
                             │  (B-2 protocol, NOT yet wired to B-3)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  B-2: CRM Bridge Adapter (Python, connector-side)                │
│  crm_send_execution_bridge_adapter.py                             │
│  ├── CrmSendExecutionBridgeAdapter.submit(execution_id)           │
│  │     ├── Reads CRM SendExecution (via CrmSendExecutionRepository)│
│  │     ├── Reads CRM DraftApproval                                │
│  │     ├── Reads ApprovedDeliveryPayloadSource                    │
│  │     ├── Validates: APPROVED + READY + content hash match       │
│  │     ├── Constructs B-1 SendExecutionBridgeRequest (safe refs)  │
│  │     └── Calls bridge_adapter.enqueue(request)                  │
│  └── Returns BridgeSubmissionOutcome (SUBMITTED/DUPLICATE/BLOCKED)│
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │  SendExecutionBridgeAdapter.enqueue()
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  B-1: Bridge Contract (Python, connector-side)                   │
│  send_execution_bridge.py                                         │
│  ├── SendExecutionBridgeRequest  (safe: hashes only, no content)  │
│  ├── SendExecutionBridgeResult   (SENT/FAILED + error_class)      │
│  └── InMemorySendExecutionBridgeFixture (test double)             │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 What Does NOT Exist — The Invocation Trigger

```
                         ┌──────────────────┐
                         │   WHO CALLS      │
                         │   submit() ?     │  ← THIS IS THE GAP
                         └────────┬─────────┘
                                  │
                                  ▼
                    CrmSendExecutionBridgeAdapter
                         .submit(execution_id)
```

The B-2 adapter's `submit()` method is a pure function with zero callers. There is no PHP hook, no scheduler, no CLI command, and no API endpoint that invokes it. The architecture decision (C14.3.1B) explicitly ruled out PHP hooks: "no PHP hook may directly invoke a Python in-memory queue."

### 1.3 What the Invocation Trigger Must Do

The invocation trigger is a thin orchestration layer that:

1. **Acquires** the `execution_id` to process (from operator input, a scheduled scan, or an API call)
2. **Wires** the three B-2 dependencies:
   - `CrmSendExecutionRepository` → reads CRM (via connector API client or direct DB)
   - `ApprovedDeliveryPayloadSource` → reads B-3 durable snapshot store
   - `SendExecutionBridgeAdapter` → B-1 fixture or real queue
3. **Calls** `adapter.submit(execution_id)`
4. **Reports** the `BridgeSubmissionOutcome` to the caller
5. **Does NOT** write to CRM, create queue items, invoke the Worker, or call the Provider

---

## 2. Option Comparison

### 2.1 Option A — EspoCRM Hook Triggers Bridge Invocation

**Mechanism:** PHP `afterSave` hook on `SendExecution` (or `DraftApproval`) calls the Python connector via HTTP or CLI exec.

**Analysis:**

| Criterion | Assessment |
|---|---|
| **Trigger ownership** | CRM PHP hook owns the trigger. Hook fires within the EspoCRM web request lifecycle. |
| **Duplicate prevention** | Hook fires on every `afterSave`. Would need a guard flag (e.g., a CRM field like `bridgeSubmitted`) to prevent re-firing. Re-saves of the same entity would re-trigger unless explicitly gated. |
| **Transaction boundary** | CRM `saveEntity` succeeds → hook fires → HTTP call to Python. If the HTTP call fails, CRM is already committed (SendExecution=READY). No automatic rollback. The CRM transaction and bridge invocation are in separate processes with no distributed transaction coordinator. |
| **Failure recovery** | If the Python connector is unreachable, the hook must either: (a) throw (blocking the CRM save — unacceptable for a web request), (b) swallow the error (leaving SendExecution=READY with no bridge submission — silent failure), or (c) queue a retry (adds retry infrastructure not authorized for C14.3). |
| **C10/C11 compatibility** | **FAIL.** The hook would need to distinguish CRM `APPROVED` from C10 `READY_TO_SEND`. These are separate concepts. The architecture decision explicitly prohibits treating CRM APPROVED as C10 READY_TO_SEND. |
| **C13 compatibility** | **FAIL.** C13 Queue is in-memory, process-local to the Python connector process. A PHP hook from a web request cannot enqueue into Python process memory. The hook would need to: (a) exec a Python CLI (slow, fragile), or (b) HTTP POST to a running Python service (adds deployment coupling and an API surface not authorized for C14.3). |
| **Operational complexity** | **HIGH.** Requires: Python connector process running and reachable from PHP; network path between PHP and Python; error handling for connector unavailability within web request lifecycle; monitoring for silent hook failures. |
| **Rollback difficulty** | **HIGH.** Disabling an automated hook requires a code deploy or metadata change. If the hook misfires in production, it enqueues sends automatically with no human gate. |

**Verdict: REJECTED.** A PHP hook cannot safely bridge the process boundary to Python's in-memory C13 queue. The transaction boundary is unacceptable for C14.3 acceptance.

---

### 2.2 Option B — Connector Scheduled Sync Discovers Ready SendExecution

**Mechanism:** A Python process (cron job, scheduled task, or loop) periodically queries CRM for `SendExecution WHERE status='READY'` and `DraftApproval WHERE status='APPROVED'`, then invokes `adapter.submit()` for each.

**Analysis:**

| Criterion | Assessment |
|---|---|
| **Trigger ownership** | Connector scheduler owns the trigger. Python process, clean separation from CRM. |
| **Duplicate prevention** | **Partial.** The B-2 adapter returns `DUPLICATE` for the same `execution_id`, and B-1's stable idempotency key prevents double-enqueue. However, the scheduler must ensure it doesn't pick up the same execution across multiple poll cycles after a successful submission. This requires either: (a) a CRM flag (SendExecution needs a new field like `bridgeSubmitted`), or (b) the scheduler tracking which executions it already submitted (in-memory, lost on restart). |
| **Transaction boundary** | Clean. Each poll cycle is an independent Python process. If one submission fails, the execution remains READY and is retried on the next poll. No cross-process transaction needed. |
| **Failure recovery** | Good for transient failures. If the connector is temporarily unavailable, the next poll cycle retries. If CRM is unreachable, the scheduler backs off. If a submission fails, the execution stays READY and is discovered again. |
| **C10/C11 compatibility** | **PASS.** The scheduler reads CRM state only (APPROVED + READY). It does not import, call, or modify C10 frozen modules. |
| **C13 compatibility** | **PASS.** The scheduler runs in the same Python process as C13, so in-memory queue access is natural. |
| **Operational complexity** | **MEDIUM.** Requires: a scheduler daemon or cron job; CRM API credentials for the connector; a polling interval decision (trade-off: latency vs CRM load); monitoring for scheduler health (is it still running?). |
| **Rollback difficulty** | **LOW-MEDIUM.** Stop the scheduler — no more automatic submissions. Existing submitted executions are unaffected. |

**Verdict: VIABLE for production, PREMATURE for C14.3 acceptance.** The scheduler is the correct production architecture but adds deployment components (cron, monitoring) that are unnecessary for acceptance testing. It also requires a CRM query API that may not exist yet. Recommended as the **future production path** after C14.3 acceptance validates the bridge function.

---

### 2.3 Option C — Explicit Command/Service Invocation

**Mechanism:** A CLI command or explicit API call invokes `adapter.submit(execution_id)` for a specific, operator-specified `execution_id`. No automatic trigger. No polling. No hook.

**Analysis:**

| Criterion | Assessment |
|---|---|
| **Trigger ownership** | The operator (or test harness, or external orchestration service) owns the trigger. The bridge function is a pure library; invocation is a separate, explicit decision. |
| **Duplicate prevention** | **Natural.** The operator specifies the exact `execution_id`. Running the command twice produces `DUPLICATE` on the second invocation (B-2 + B-1 idempotency). No automatic re-triggering risk. |
| **Transaction boundary** | **Cleanest.** The invocation is a single Python process. CRM reads happen at invocation time. If the command fails, the operator sees the error and can decide to retry. No partial commits, no distributed state. |
| **Failure recovery** | Operator-driven. The command returns a clear outcome: `SUBMITTED`, `DUPLICATE`, `BLOCKED` (with reason_code), or `FAILED_SUBMISSION`. The operator decides the next action. For `FAILED_SUBMISSION`, the execution stays READY and can be resubmitted after the issue is resolved. |
| **C10/C11 compatibility** | **PASS.** The command only invokes B-2, which already validates CRM state without touching C10. |
| **C13 compatibility** | **PASS.** The command runs in the connector Python process, giving natural access to C13 in-memory components. |
| **Operational complexity** | **LOWEST.** One CLI script. No daemon, no scheduler, no monitoring, no CRM API polling, no PHP-to-Python coupling. For C14.3 acceptance, the operator runs the command manually. For C14.3 testing, the test harness runs it programmatically. |
| **Rollback difficulty** | **ZERO.** Don't run the command. No automation to disable. No hooks to remove. |

**Verdict: RECOMMENDED.** Option C is the correct choice for C14.3 acceptance. It is the simplest, safest, and most testable model. It matches C13's caller-driven design philosophy. It has zero automation risk. It defers the scheduling decision to a future phase when the bridge function is proven.

---

## 3. Comparative Decision Matrix

| Criterion | A: PHP Hook | B: Scheduled Sync | C: Explicit Command |
|---|---|---|---|
| Trigger ownership | CRM (PHP) | Connector scheduler | Operator / test harness |
| Duplicate prevention | Requires CRM guard flag | Requires scheduler dedup or CRM flag | Natural — operator specifies ID |
| Transaction boundary | **FAIL** — cross-process, no coordinator | Clean — independent Python process | **Cleanest** — single Python process |
| Failure recovery | Silent failure or web-request blocking | Automatic retry on next poll | Operator-driven; execution stays READY |
| C10/C11 compatibility | **FAIL** — conflates CRM/C10 approval | **PASS** | **PASS** |
| C13 compatibility | **FAIL** — cannot reach in-memory queue | **PASS** | **PASS** |
| Operational complexity | **HIGH** — PHP-Python coupling, web-request latency, monitoring | **MEDIUM** — scheduler daemon, CRM polling, monitoring | **LOWEST** — one CLI script |
| Rollback difficulty | **HIGH** — requires code deploy | **LOW-MEDIUM** — stop scheduler | **ZERO** — don't run the command |
| Suitable for C14.3 acceptance | No | Over-engineered | **Yes** |
| Suitable for production | No | **Yes** (future) | No (manual step) |

---

## 4. Recommended Architecture — Option C with Production Path

### 4.1 Invocation Command Design

```
┌──────────────────────────────────────────────────────────────────┐
│  NEW: scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py        │
│                                                                   │
│  Usage:                                                           │
│    python scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py    │
│          <execution_id>                                           │
│                                                                   │
│  What it does:                                                    │
│    1. Parses execution_id from CLI argument                       │
│    2. Wires dependencies:                                         │
│       - CrmSendExecutionRepository → reads CRM (connector client) │
│       - ApprovedDeliveryPayloadSource → B-3 SqlitePayloadSnapshotStore│
│       - SendExecutionBridgeAdapter → B-1 fixture (or real queue)  │
│    3. Calls CrmSendExecutionBridgeAdapter.submit(execution_id)    │
│    4. Prints BridgeSubmissionOutcome as JSON to stdout            │
│    5. Exit code: 0=SUBMITTED/DUPLICATE, 1=BLOCKED, 2=FAILED      │
│                                                                   │
│  What it does NOT do:                                             │
│    - Write to CRM (SendExecution stays READY)                     │
│    - Invoke the C13 Worker                                        │
│    - Call the C12 Provider                                        │
│    - Send email                                                   │
│    - Create queue items directly                                  │
│    - Schedule retries                                             │
│    - Read API keys or credentials                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Command Contract

**Input:** `execution_id` (string) — the CRM SendExecution record ID.

**Output (stdout):** JSON `BridgeSubmissionOutcome`:
```json
{
  "status": "SUBMITTED | DUPLICATE | BLOCKED | FAILED_SUBMISSION",
  "execution_id": "<id>",
  "reason_code": "<code or null>",
  "idempotency_key": "<sha256 or null>"
}
```

**Exit codes:**

| Exit | Status | Meaning |
|---|---|---|
| 0 | SUBMITTED | Bridge accepted the request; queue item created |
| 0 | DUPLICATE | Bridge already has this execution; idempotent return |
| 1 | BLOCKED | Validation failed (see reason_code); execution not submitted |
| 2 | FAILED_SUBMISSION | Bridge unavailable; execution stays READY |

### 4.3 Dependency Wiring

The command must wire these three dependencies for B-2:

```python
# 1. CRM repository — reads SendExecution + DraftApproval from CRM
crm_repository = ConnectorCrmSendExecutionRepository(
    base_url=CRM_BASE_URL,
    api_key=CRM_API_KEY,
)

# 2. Payload source — reads durable snapshot from B-3 SQLite store
payload_source = SqliteApprovedDeliveryPayloadSource(
    store=SqlitePayloadSnapshotStore(database_path=PAYLOAD_DB_PATH),
)

# 3. Bridge adapter — B-1 fixture (acceptance) or real queue (future)
bridge_adapter = InMemorySendExecutionBridgeFixture()

# Compose and invoke
adapter = CrmSendExecutionBridgeAdapter(
    crm_repository=crm_repository,
    payload_source=payload_source,
    bridge_adapter=bridge_adapter,
)
outcome = adapter.submit(execution_id)
```

### 4.4 Acceptance Test Flow

For C14.3.1B-4 acceptance:
1. Create CRM DraftApproval (APPROVED) and SendExecution (READY) — via CRM UI or API
2. Persist approved payload via B-3 snapshot ingress (separate command)
3. Run `phase3c14_3_1b4_invoke_bridge.py <execution_id>`
4. Verify outcome: `SUBMITTED` with valid `idempotency_key`
5. Run again with same `execution_id` — verify `DUPLICATE`
6. Run with non-existent `execution_id` — verify `BLOCKED: SEND_EXECUTION_NOT_FOUND`
7. Run with non-READY execution — verify `BLOCKED: SEND_EXECUTION_NOT_READY`
8. Run with hash mismatch — verify `BLOCKED: APPROVED_PAYLOAD_HASH_MISMATCH`

### 4.5 Future Production Path (Option B Integration)

When C14.3 acceptance is complete and the bridge function is proven, Option B can be added as a thin wrapper:

```python
# Future: scripts/scheduled_bridge_sync.py (NOT in C14.3 scope)
def scan_and_submit():
    ready_executions = crm_repository.find_ready_send_executions()
    for execution_id in ready_executions:
        outcome = adapter.submit(execution_id)
        log_outcome(outcome)
```

The key architectural property: **the bridge function (`adapter.submit()`) is identical in both Option C and Option B.** The invocation trigger is a separate, swappable concern. This validates the architecture decision's prediction: "an explicit invocation owner for the bridge is named."

---

## 5. Must-Answer Questions

### Q1: Approval 后是否立即执行？

**No.** CRM `DraftApproval.status = APPROVED` is a human decision record. It does not trigger execution. Execution requires **three independent conditions**, all verified at invocation time:

1. `DraftApproval.status == APPROVED` — human approved the content
2. `SendExecution.status == READY` — execution record is marked ready for dispatch
3. `PayloadSnapshot` exists and `content_hash` matches `DraftApproval.contentHash` — immutable delivery content is available

The bridge does not automatically detect when these conditions become true. An explicit invocation (Option C) or scheduled scan (Option B) triggers the bridge after all three are satisfied.

**Rationale:** Separating approval from execution prevents the system from sending email automatically when a human clicks "Approve." The approval and the send are distinct decisions made by distinct actors.

### Q2: APPROVED 到 READY_TO_SEND 如何映射？

**They are not mapped. They are separate concepts in separate domains.**

| Concept | Domain | Owner | Semantics |
|---|---|---|---|
| `DraftApproval.APPROVED` | CRM (PHP) | Human reviewer | "I approve this draft content." |
| C10 `READY_TO_SEND` | Connector (Python, frozen) | C10 state machine | "The C10 approval registry has advanced to the pre-send terminal state." |
| `SendExecution.READY` | CRM (PHP) | Bridge caller | "The execution record is ready for the bridge to enqueue." |

The bridge requires `DraftApproval.APPROVED` AND `SendExecution.READY`. It does **not** read, import, or require the C10 `READY_TO_SEND` state. The C10 in-memory registry is untouched.

The `SendExecution.READY` status is set by an authorized CRM user or API call **after** the approved payload snapshot has been persisted to B-3. This is a separate, explicit step — it is not automated by any CRM hook.

**Rationale:** The architecture decision (C14.3.1B) explicitly states: "CRM SendExecution.READY is its own explicit execution-readiness record and must be set by an authorized future bridge caller after payload verification."

### Q3: 谁拥有 enqueue intent？

**The explicit invocation owner** — the operator, test harness, or (future) scheduled sync process that calls the bridge command.

The enqueue intent flows through a strict chain of custody:

```
Operator / Test Harness
  │
  │  "I intend to send execution <id>"
  │
  ▼
CrmSendExecutionBridgeAdapter.submit(execution_id)
  │
  │  "I have verified CRM state and payload integrity"
  │
  ▼
SendExecutionBridgeAdapter.enqueue(request)
  │
  │  "I have accepted this request; here is the receipt"
  │
  ▼
(Optionally) C13 InMemorySendExecutionQueue.enqueue(send_execution_id)
  │
  │  "A QueueItem now exists for this execution"
  │
  ▼
C13 SendExecutionWorker.process(queue_item)
  │
  │  "I will now invoke the provider"
```

The CRM does **not** own the enqueue intent. The C10 approval registry does **not** own it. The B-3 payload store does **not** own it. Only the explicit invocation caller decides "now is the time to enqueue."

### Q4: 如何保证 one execution attempt per SendExecution？

**Six-layer protection chain, with one known C13 limitation:**

| Layer | Mechanism | Restart-Safe? | Notes |
|---|---|---|---|
| **L1. CRM** | `sendRequestId` UNIQUE index | Yes (database) | Cannot create two SendExecutions with same sendRequestId |
| **L2. B-2 validation** | Rejects non-READY executions | Yes (re-reads CRM) | SENT/FAILED/CANCELLED executions blocked before B-1 |
| **L3. B-1 idempotency key** | `SHA-256(contract_version + execution_id)` | Yes (deterministic) | Same execution always produces same key |
| **L4. B-1 fixture** | `enqueue()` returns duplicate receipt | **No** (in-memory) | `InMemorySendExecutionBridgeFixture` loses state on restart |
| **L5. B-3 payload** | `execution_id` PRIMARY KEY, `save_if_absent()` | Yes (SQLite) | Cannot persist different content for same execution; `IMMUTABILITY_CONFLICT` on mismatch |
| **L6. C13 queue** | One QueueItem per `send_execution_id` | **No** (in-memory) | `InMemorySendExecutionQueue` loses state on restart |

**Known gap (L4 + L6):** After a connector process restart, the B-1 fixture and C13 queue are empty. A re-invocation with the same `execution_id` would be accepted as new (not duplicate). The C13 Worker could process it again.

**Mitigation for C14.3 acceptance:**
- The acceptance test runs in a single Python process — no restart between enqueue and Worker execution
- The operator does not invoke the command twice for the same execution
- If a restart does occur, the operator checks CRM: if `SendExecution.status` is already `SENT` (from a prior successful run), the B-2 adapter rejects the re-invocation at L2 (`SEND_EXECUTION_NOT_READY`)

**Production hardening (C14.4+):**
- Replace B-1's `InMemorySendExecutionBridgeFixture` with a durable implementation backed by B-3's SQLite store
- Add a `bridge_submitted_at` field or state to the B-3 execution-payload binding to persist enqueue acknowledgment
- These are explicitly deferred; C14.3 accepts the process-local limitation

### Q5: 如果 snapshot 成功但 queue 不可用，系统状态是什么？

**Scenario:** Snapshot persisted (B-3 SQLite COMMIT successful), but B-1 enqueue fails (C13 queue unavailable, process crash, or network error).

**Step-by-step trace:**

```
1. B-3: save_if_absent(input) → COMMIT ✓
   Payload snapshot is now durable on disk.

2. B-2: adapter.submit(execution_id)
   ├── crm_repository.get_send_execution() → READY ✓
   ├── crm_repository.get_draft_approval() → APPROVED ✓
   ├── payload_source.get_approved_payload() → snapshot found ✓
   ├── content_hash match ✓
   ├── Constructs SendExecutionBridgeRequest ✓
   └── bridge_adapter.enqueue(request) → EXCEPTION ✗
       (queue unavailable, process crash, or network error)

3. B-2: catches exception → returns FAILED_SUBMISSION
   BridgeSubmissionOutcome(
     status=FAILED_SUBMISSION,
     execution_id="<id>",
     reason_code="BRIDGE_SUBMISSION_UNAVAILABLE",
   )
```

**Resulting system state:**

| Component | State | Recoverable? |
|---|---|---|
| **CRM DraftApproval** | `APPROVED` (unchanged) | N/A — correct |
| **CRM SendExecution** | `READY` (unchanged) | N/A — correct; adapter has no CRM write capability |
| **B-3 payload snapshot** | Durable in SQLite, `execution_id` row exists | Yes — identical content available on re-read |
| **B-1 bridge fixture** | No record (enqueue failed) | Acceptable — will accept re-submission |
| **C13 queue** | No QueueItem (enqueue never reached queue) | Acceptable |
| **C12 Provider** | Not called | Correct — no HTTP request made |
| **Email** | Not sent | Correct |
| **Lead** | Unchanged | Correct |

**This is a recoverable pending state — not a failure that requires repair.**

The operator can:
1. Restore queue availability (restart connector process, fix network, etc.)
2. Re-run the invocation command with the same `execution_id`
3. B-2 re-reads CRM (still `READY` + `APPROVED`) ✓
4. B-2 re-reads snapshot (still durable, same `content_hash`) ✓
5. B-1 enqueue succeeds this time → `SUBMITTED`

**No state corruption. No ambiguous delivery. No retry risk. No CRM inconsistency.**

The `SendExecution` remains `READY` — the correct representation: "this execution is ready to be sent, but has not yet been dispatched to the provider." The operator sees this and re-invokes.

**Contrast with the dangerous scenario (which does NOT occur):**
- ❌ SendExecution marked `SENT` before enqueue → CRM shows SENT but no email was sent
- ❌ SendExecution marked `FAILED` on transient queue error → loses the ability to distinguish "queue temporarily down" from "provider permanently rejected"
- ❌ C10 registry advanced to `FAILED` → frozen C10 state changed without provider involvement

The B-2 adapter's design decision — **no CRM write capability** — is the key safety property. It cannot mark a SendExecution SENT or FAILED. Only the result adapter (B-2 CRM-side, PHP) writes terminal status, and it only does so after receiving a terminal `SendExecutionBridgeResult` from the Worker.

---

## 6. Invocation Boundary Contract

### 6.1 Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│  INVOCATION TRIGGER (this phase)                         │
│                                                          │
│  Responsibility: WHEN to call the bridge                 │
│  - Operator command (Option C, C14.3 acceptance)         │
│  - Scheduled sync (Option B, future production)          │
│  - External orchestration service                        │
│                                                          │
│  This layer is THIN. It only:                            │
│    1. Obtains execution_id                               │
│    2. Wires dependencies                                 │
│    3. Calls adapter.submit()                             │
│    4. Reports outcome                                    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          │  Calls (same process, same function)
                          ▼
┌─────────────────────────────────────────────────────────┐
│  BRIDGE FUNCTION (B-1 + B-2 + B-3, already built)       │
│                                                          │
│  Responsibility: HOW to validate and enqueue             │
│  - CRM state validation                                  │
│  - Payload integrity verification                        │
│  - Bridge request construction                           │
│  - Idempotent enqueue                                    │
│                                                          │
│  This layer is a PURE FUNCTION of its inputs.            │
│  It has no side effects on CRM.                          │
│  It returns a deterministic outcome for the same inputs. │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Invocation Trigger Contract

| Aspect | Rule |
|---|---|
| **Input** | `execution_id` (CRM SendExecution record ID) |
| **Preconditions** | All three conditions verified by B-2 at invocation time (not before) |
| **Side effects** | Only through B-1 `enqueue()` — creates an in-memory bridge receipt |
| **CRM writes** | **None.** The invocation trigger must not write to CRM. |
| **Provider calls** | **None.** The invocation trigger does not invoke the Worker. |
| **Idempotency** | Re-invocation with same `execution_id` returns `DUPLICATE` (in-process) or re-validates and submits (after restart). Either is safe. |
| **Error reporting** | Structured JSON outcome with status + reason_code. Never includes raw content. |
| **Exit behavior** | Exit code signals outcome class (0=success, 1=blocked, 2=failed). |

### 6.3 What the Invocation Trigger Is NOT

The invocation trigger is explicitly NOT:
- A CRM hook, workflow, or formula
- A background daemon or scheduler (for C14.3; this is the future Option B path)
- A queue consumer or Worker
- A retry engine
- A batch processor
- An automatic approval-to-send pipeline

---

## 7. C10/C11/C12/C13/C14.2B Safety Check

| Contract | Impact of Option C |
|---|---|
| **C10 frozen modules** | **No impact.** Invocation command does not import `human_approval`, `send_execution`, `send_provider`, `send_idempotency`, or `reply_tracking`. CRM `APPROVED` is not mapped to C10 `READY_TO_SEND`. |
| **C11 CRM entities** | **No structural change.** No new entity, field, metadata, schema, or hook. B-2 reads CRM state via `CrmSendExecutionRepository` Protocol — the real implementation (not in C14.3 scope) would use the connector API client, not direct database access. |
| **C11 projection** | **No change.** `EmailLifecycleProjectionService` is not called, modified, or bypassed by the invocation trigger. |
| **C12 Provider contract** | **No impact.** Invocation command does not import `provider_contract`, `BrevoProviderAdapter`, or `brevo_http`. |
| **C13 Queue/Worker** | **No change to contracts.** The invocation command wires `InMemorySendExecutionBridgeFixture` as the B-1 adapter. A future composition may wire the real C13 `InMemorySendExecutionQueue` as the B-1 adapter's backend — but that is a wiring decision, not a contract change. |
| **C14.2B terminal handling** | **No change.** Network failures remain terminal. No retry is introduced. The invocation trigger does not interpret `BREVO_NETWORK_ERROR`. |

---

## 8. Implementation Scope for C14.3.1B-4

### 8.1 Must Build

1. **`scripts/acceptance/phase3c14_3_1b4_invoke_bridge.py`**
   - CLI entry point: `python <script> <execution_id>`
   - Wires B-2 dependencies (CRM repo, payload source, B-1 fixture)
   - Calls `CrmSendExecutionBridgeAdapter.submit()`
   - Prints JSON outcome to stdout
   - Exit codes: 0/1/2

2. **`SqliteApprovedDeliveryPayloadSource`** (NEW — wires B-3 to B-2)
   - Implements `ApprovedDeliveryPayloadSource` Protocol
   - Backed by `SqlitePayloadSnapshotStore`
   - `get_approved_payload(draft_id)` → queries B-3 store, converts `PayloadSnapshot` → `ApprovedDeliveryPayload`

3. **In-memory CRM repository** (for acceptance testing)
   - Implements `CrmSendExecutionRepository` Protocol
   - Populated with test fixtures (APPROVED DraftApproval + READY SendExecution)
   - No real CRM connection needed for acceptance

### 8.2 Must Test

1. `submit(valid_execution_id)` → `SUBMITTED`
2. `submit(same_execution_id)` twice → first `SUBMITTED`, second `DUPLICATE`
3. `submit(nonexistent_execution_id)` → `BLOCKED: SEND_EXECUTION_NOT_FOUND`
4. `submit(non_ready_execution)` → `BLOCKED: SEND_EXECUTION_NOT_READY`
5. `submit(not_approved_execution)` → `BLOCKED: DRAFT_NOT_APPROVED`
6. `submit(hash_mismatch_execution)` → `BLOCKED: APPROVED_PAYLOAD_HASH_MISMATCH`
7. `submit(missing_payload_execution)` → `BLOCKED: APPROVED_PAYLOAD_NOT_FOUND`
8. B-3 + B-2 wiring: `SqliteApprovedDeliveryPayloadSource` reads back a snapshot persisted via `SqlitePayloadSnapshotStore`
9. B-1 + C13 + C12 + Brevo imports absent from invocation script (dependency isolation)
10. Existing B-1 (7 tests), B-2 (7 tests), B-3 (7 tests) regression: **21 tests must remain PASS**

### 8.3 Must NOT Build

- CRM hooks, workflows, or formulas
- Scheduler daemon, cron job, or polling loop
- C13 Queue or Worker modifications
- CRM API client (use in-memory fixture for acceptance)
- Result callback / CRM write adapter (separate phase)
- Retry logic or failure recovery
- Real Brevo or Provider calls

---

## 9. Decision Summary

| Question | Answer |
|---|---|
| Which option? | **Option C — Explicit Command Invocation** |
| Why not Option A? | PHP hook cannot reach Python in-memory C13 queue; cross-process transaction boundary is unacceptable |
| Why not Option B? | Viable for production but over-engineered for C14.3 acceptance; adds scheduler deployment complexity |
| Can Option B be added later? | **Yes.** The bridge function (`adapter.submit()`) is identical in both models. Option B is a thin scheduling wrapper around the same function. |
| Is C14.3.1B-4 ready to implement? | **Yes** — limited to the invocation command + B-3→B-2 wiring + tests |
| What remains after B-4? | Result callback (CRM-side PHP adapter to update SendExecution.status after Worker completes), end-to-end acceptance test, C14.3 closure |

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-14 | Initial design: RECOMMENDED_OPTION=C, READY_FOR_IMPLEMENTATION=YES |
