# Phase C14.3.1 — CRM SendExecution Boundary Audit

## Final Verdict

**READY_FOR_C14_3_IMPLEMENTATION**

The boundary is well-understood, the gap is precisely located, and all historical lifecycle issues have been traced to a single root cause. C14.3 implementation can proceed with a clear, bounded scope.

---

## Part 1: Current CRM Email Flow — Complete Trace

### 1.1 Entity Map

```
┌──────────────────────────────────────────────────────────────────────┐
│                            LEAD                                       │
│  peEmailStatus (12-value enum: NONE → … → REPLIED/BOUNCED)           │
│  peEmailReplyStatus (varchar(64))   peLastEmailDate (datetime)        │
│  peEmailCampaignName (varchar)                                         │
│                                                                        │
│  hasMany → DraftApproval   hasMany → SendExecution                    │
│  hasMany → EmailEvent      hasMany → ReplyEvent                       │
└──────────────────────────────────────────────────────────────────────┘
        │                    │                    │                    │
        ▼                    ▼                    ▼                    ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ DraftApproval│  │  SendExecution  │  │  EmailEvent  │  │  ReplyEvent  │
│              │  │                 │  │              │  │              │
│ draftId (UQ) │  │ sendRequestId   │  │ extMessageId │  │ extEventId   │
│ status:      │  │   (UQ)          │  │ eventType:   │  │   (UQ)       │
│  PENDING     │  │ status:         │  │  SENT        │  │ replyStatus: │
│  APPROVED    │  │  CREATED        │  │  DELIVERED   │  │  SENT        │
│  REJECTED    │  │  READY          │  │  OPENED      │  │  REPLIED     │
│              │  │  SENT           │  │  CLICKED     │  │  BOUNCED     │
│ contentHash  │  │  FAILED         │  │  REPLIED     │  │  UNSUBSCRIBED│
│ evidenceRef  │  │  CANCELLED      │  │  BOUNCED     │  │              │
│ scoreSnap    │  │                 │  │              │  │ sendTraceRef │
│              │  │ providerName    │  │ source:      │  │              │
│ belongsTo    │  │ providerMsgId   │  │  BREVO       │  │ belongsTo    │
│  → Lead      │  │ retryCount      │  │              │  │  → SendExec  │
│              │  │ maxRetries      │  │ belongsTo    │  │  → Lead      │
│ hasMany      │  │ nextRetryAt     │  │  → Lead      │  │              │
│  → SendExec  │  │ lastError       │  │              │  │              │
│              │  │ failureCategory │  │              │  │              │
│              │  │                 │  │              │  │              │
│              │  │ belongsTo       │  │              │  │              │
│              │  │  → DraftApproval│  │              │  │              │
│              │  │  → Lead         │  │              │  │              │
│              │  │                 │  │              │  │              │
│              │  │ hasMany         │  │              │  │              │
│              │  │  → ReplyEvent   │  │              │  │              │
└──────────────┘  └─────────────────┘  └──────────────┘  └──────────────┘
```

### 1.2 Hook Execution Order on Each Entity

| Entity | Hook | Order | Trigger | Action |
|---|---|---|---|---|
| **Lead** | LeadWorkflowHook | 10 | afterSave | peResearchStatus→COMPLETED: creates "Prepare Outreach" task. peOpportunityScoreV4≥80: creates "Review and Contact Lead" task |
| **Lead** | Formula (beforeSave) | — | beforeSave | peResearchStatus→COMPLETED sets outreachStatus=RESEARCH_COMPLETED; score≥80 sets pePriorityLevel=HIGH; email/phone populated sets outreachStatus=CONTACT_READY |
| **DraftApproval** | EmailLifecycleProjectionHook | 50 | afterSave | Maps DraftApproval.status → Lead.peEmailStatus (PENDING→DRAFT_PENDING_APPROVAL, APPROVED→APPROVED, REJECTED→REJECTED) |
| **SendExecution** | EmailLifecycleProjectionHook | 50 | afterSave | Maps SendExecution.status → Lead.peEmailStatus (CREATED→PENDING, READY→READY_TO_SEND, SENT→SENT, FAILED→FAILED, CANCELLED→CANCELLED) |
| **EmailEvent** | EmailEventWorkflowHook | 20 | afterSave (new) | Maps eventType → Lead.peEmailStatus/peEmailReplyStatus/peLastEmailDate. Creates tasks for REPLIED/BOUNCED |
| **EmailEvent** | EmailEventSalesFeedbackHook | 30 | afterSave (new) | Maps REPLIED/CLICKED/BOUNCED → SalesFeedback records |
| **ReplyEvent** | EmailLifecycleProjectionHook | 50 | afterSave | Maps ReplyEvent.replyStatus → Lead.peEmailReplyStatus (REPLIED/BOUNCED) |

### 1.3 The Projection Service: EmailLifecycleProjectionService

Located at `crm-extension/files/custom/Espo/Modules/Prospecting/Services/EmailLifecycleProjectionService.php`, this is the central read-model projector invoked by DraftApproval, SendExecution, and ReplyEvent hooks.

**Status rank ordering (monotonic enforcement):**

| Rank | peEmailStatus | Source Entity(s) |
|---|---|---|
| 0 | NONE | (initial) |
| 10 | DRAFT_READY | CampaignProjectionAdapter (C09, Python) |
| 20 | DRAFT_PENDING_APPROVAL | DraftApproval (PENDING) |
| 30 | APPROVED / REJECTED | DraftApproval (APPROVED/REJECTED) |
| 40 | PENDING | SendExecution (CREATED) |
| 50 | READY_TO_SEND | SendExecution (READY) |
| 60 | SENT / FAILED / CANCELLED | SendExecution (SENT/FAILED/CANCELLED) or EmailEvent (SENT/DELIVERED) |
| 70 | REPLIED / BOUNCED | EmailEvent (REPLIED/BOUNCED) or ReplyEvent |

Key behaviors:
- **Never downgrades**: lower-ranked status cannot overwrite higher-ranked at same timestamp
- **Timestamp-gated**: ignores events older than current `peLastEmailDate`
- **Changed-only writes**: only touches Lead when a field value actually changes
- **One-way projection only**: never reads Lead state as input to its own logic (no circular dependency)

### 1.4 The Complete Flow (Conceptual, Not All Wired)

```
[Chitu Engine] ──POST /Prospecting/sync/lead──→ Lead (created/updated)
                                                      │
                                    (C09 Python) CampaignProjectionAdapter
                                    sets peEmailStatus=DRAFT_READY
                                                      │
[Draft Generator] ──creates──→ DraftApproval (PENDING)
                                    │   hook → peEmailStatus=DRAFT_PENDING_APPROVAL
                                    │
[Human Reviewer] ──approves──→ DraftApproval (APPROVED)
                                    │   hook → peEmailStatus=APPROVED
                                    │
[Send Orchestrator] ──creates──→ SendExecution (CREATED)
                                    │   hook → peEmailStatus=PENDING
                                    │
                         ┌─────────┴──────────┐
                         │   THE GAP (B2)      │
                         │   CRM SendExecution │
                         │   is NOT bridged    │
                         │   to C13 Queue/     │
                         │   Worker/Provider   │
                         └─────────┬──────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
   [C13 Queue]             [C13 Worker]           [C12 Provider]
   InMemoryQueue           SendExecutionWorker    BrevoProviderAdapter
   (process-local)         (explicit invoke)      (real HTTP)
                                   │
                                   ▼
                          [Brevo API]
                          POST /smtp/email
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              EmailEvent      EmailEvent      EmailEvent
              (SENT)          (REPLIED)       (BOUNCED)
              hook→SENT       hook→REPLIED    hook→BOUNCED
                    │              │              │
                    ▼              ▼              ▼
              ReplyEvent      ReplyEvent      ReplyEvent
              (SENT)          (REPLIED)       (BOUNCED)
```

### 1.5 Missing Components

| Component | Status | Location |
|---|---|---|
| CRM → Queue bridge | **MISSING** | No code bridges SendExecution entity creation/update to `InMemorySendExecutionQueue.enqueue()` |
| Worker → CRM result bridge | **MISSING** | No code updates CRM SendExecution.status from Worker outcome |
| EmailEvent → SendExecution link | **MISSING** | EmailEvent has no foreign key to SendExecution; linked only via Lead |
| ReplyEvent → EmailEvent link | **MISSING** | ReplyEvent links to SendExecution but not to EmailEvent |
| C10 → C13 bridge | **MISSING** | `ControlledSendExecutionService` (C10.3) does not invoke C13 `SendExecutionWorker` |
| Durable queue | **MISSING** | C13 queue is `InMemorySendExecutionQueue` only |
| Retry execution | **MISSING** | Schema reservation only (retryCount, maxRetries, nextRetryAt); no logic |
| Provider webhook handler | **MISSING** | Brevo delivery events arrive via `POST /Prospecting/brevo/email-event` but no SendExecution link |

---

## Part 2: State Ownership Audit

### 2.1 Ownership Matrix

| State Field | C09 Python | C10 Python (frozen) | C11 CRM (PHP) | C13 Worker (Python) | C12 Provider (Python) | Brevo Webhook (PHP) |
|---|---|---|---|---|---|---|
| **DraftApproval.status** | — | — | **OWNER** (store) | — | — | — |
| **DraftApproval.contentHash** | — | — | **OWNER** (store) | Read (verify) | — | — |
| **SendExecution.status** | — | Read (C10.3) | **OWNER** (store) | **WRITER** (via bridge) | — | — |
| **SendExecution.providerName** | — | — | **OWNER** (store) | **WRITER** (via bridge) | — | — |
| **SendExecution.providerMessageId** | — | — | **OWNER** (store) | **WRITER** (via bridge) | Provides value | — |
| **SendExecution.retryCount** | — | — | **OWNER** (store) | **WRITER** (reserved) | — | — |
| **SendExecution.lastError** | — | — | **OWNER** (store) | **WRITER** (via bridge) | — | — |
| **SendExecution.failureCategory** | — | — | **OWNER** (store) | **WRITER** (via bridge) | — | — |
| **EmailEvent.eventType** | — | — | **OWNER** (store) | — | — | **WRITER** (Brevo) |
| **EmailEvent.externalMessageId** | — | — | **OWNER** (store) | — | Provides value | **WRITER** (Brevo) |
| **ReplyEvent.replyStatus** | — | Read (C10.4) | **OWNER** (store) | — | — | — |
| **Lead.peEmailStatus** | WRITER (DRAFT_READY) | — | WRITER (projection hook) | — | — | **WRITER** (EmailEventWorkflowHook) |
| **Lead.peEmailReplyStatus** | — | — | WRITER (projection hook) | — | — | **WRITER** (EmailEventWorkflowHook) |
| **Lead.peLastEmailDate** | — | — | WRITER (projection hook) | — | — | **WRITER** (EmailEventWorkflowHook) |
| **Lead.peEmailCampaignName** | WRITER (campaign name) | — | — | — | — | WRITER (EmailEventWorkflowHook) |
| **QueueItem.state** | — | — | — | **OWNER** | — | — |
| **SendResult** (provider) | — | — | — | Read | **OWNER** | — |
| **SendRequest.idempotencyKey** | — | **OWNER** (frozen) | — | Read | — | — |

### 2.2 Identified Conflicts

#### CONFLICT-1 (CRITICAL): Multiple Writers for Lead.peEmailStatus

**Four writers compete for the same fields on Lead:**

| Writer | Source | Trigger | What It Writes | Status |
|---|---|---|---|---|
| A: CampaignProjectionAdapter | C09 Python | OutreachInput prepared | `peEmailStatus=DRAFT_READY`, `peEmailCampaignName` | Python, explicit invocation only |
| B: EmailLifecycleProjectionService | C11 PHP hook | DraftApproval afterSave | `peEmailStatus=DRAFT_PENDING_APPROVAL/APPROVED/REJECTED` | **ACTIVE in CRM** |
| C: EmailLifecycleProjectionService | C11 PHP hook | SendExecution afterSave | `peEmailStatus=PENDING/READY_TO_SEND/SENT/FAILED/CANCELLED` | **ACTIVE in CRM** |
| D: EmailEventWorkflowHook | PHP hook | EmailEvent afterSave (new) | `peEmailStatus=SENT/REPLIED/BOUNCED`, `peEmailReplyStatus`, `peLastEmailDate` | **ACTIVE in CRM** |
| E: EmailLifecycleProjectionService | C11 PHP hook | ReplyEvent afterSave | `peEmailReplyStatus=REPLIED/BOUNCED` | **ACTIVE in CRM** |

The EmailLifecycleProjectionService has rank-ordering and timestamp-gating that partially mitigates write conflicts. However, EmailEventWorkflowHook (Writer D) does **not** use the rank-ordering service — it writes `peEmailStatus` directly in its own hook logic, bypassing the monotonic enforcement.

**Risk:** If an EmailEvent arrives out of order (e.g., BOUNCED arrives before SENT, or a DELIVERED event arrives after a REPLIED), the hook could downgrade `peEmailStatus`. The hook partially guards against this (checks "unless already REPLIED/BOUNCED" for SENT/DELIVERED), but the guard is ad-hoc and not comprehensive across all event types.

**Origin:** This is the documented RISK-C11.3-001, deferred across C11, C12, C13, and C14. Decision recorded in C11.3: "hook was deliberately not changed."

#### CONFLICT-2: CRM SendExecution vs Provider Reality

**Two separate state machines for the same send:**

| Aspect | CRM SendExecution (C11) | C13 Worker Outcome | C10 SendExecution (frozen) |
|---|---|---|---|
| State values | CREATED, READY, SENT, FAILED, CANCELLED | QUEUED→CLAIMED→COMPLETED/FAILED | READY_TO_SEND→SUBMITTED→PROCESSING→SENT/FAILED |
| Persistence | CRM database (durable) | In-memory (process-local) | In-memory (frozen) |
| Writer | CRM hook projection | Worker.process() | ControlledSendExecutionService |
| Bridge to provider | **NONE** | Direct via ProviderAdapter | Via SendProviderAdapter |

These are three independent records of the same conceptual event. They are not synchronized. The CRM SendExecution record can show SENT while the C13 worker shows FAILED, and neither reflects the C10 in-memory registry.

#### CONFLICT-3: EmailEvent Has No SendExecution Link

EmailEvent (from Brevo webhook) links to Lead but **not** to SendExecution. This means:
- A Brevo delivery event cannot be correlated to the specific SendExecution that initiated it
- If multiple SendExecutions exist for the same Lead, there is no way to determine which one the EmailEvent refers to
- The externalMessageId on EmailEvent should match providerMessageId on SendExecution, but the code does not use this for linking

---

## Part 3: Historical Bug Risk Investigation

### Risk A: CRM Shows SENT While Provider Failed

**Status: CONFIRMED — currently possible.**

**Scenario:**
1. SendExecution is created in CRM with status=SENT (e.g., by direct API call or manual edit)
2. EmailLifecycleProjectionHook fires, sets `Lead.peEmailStatus=SENT`
3. No provider call was ever made, or the provider call failed and returned BREVO_NETWORK_ERROR
4. CRM displays SENT status; no email was delivered

**Root cause:** The CRM SendExecution entity is a passive data store with an afterSave hook. There is no guard requiring a successful provider result before transitioning to SENT. The entity can be marked SENT independently of any provider interaction.

**Current mitigation:** None. The gap between CRM SendExecution and C13 Worker means CRM state and provider state are completely decoupled.

**Recommended fix:** The C14.3 bridge must enforce that only the Worker (via the bridge) can set SendExecution.status=SENT, and only after receiving a successful `SendResult` with a valid `provider_message_id`.

### Risk B: Provider Sent Successfully But CRM Not Updated

**Status: CONFIRMED — currently possible.**

**Scenario:**
1. BrevoProviderAdapter returns `SendResult(success=True, provider_message_id="<msg-id>")`
2. C13 Worker marks QueueItem as COMPLETED and WorkItem as SENT
3. No code propagates this result back to CRM SendExecution entity
4. CRM SendExecution remains at its last state (e.g., READY or CREATED)
5. Lead.peEmailStatus is never updated to SENT from this path

**Root cause:** The C13 Worker has no CRM write capability. The `_settle_success()` method updates only the in-memory `SendExecutionWorkStore` and `InMemorySendExecutionQueue`. There is no callback, webhook, or API client that writes the result back to the CRM.

**Current mitigation:** The separate EmailEvent webhook path (`POST /Prospecting/brevo/email-event`) can provide Brevo delivery confirmation, but it arrives through a completely separate channel with no SendExecution link.

**Recommended fix:** The C14.3 bridge must include a CRM result callback: after Worker settlement, update CRM SendExecution.status, SendExecution.providerMessageId, and trigger the projection hook (or directly update Lead.peEmailStatus through the rank-ordered projection service).

### Risk C: ReplyEvent Changes State Owned by Another Component

**Status: CONFIRMED — active conflict.**

**Scenario:**
1. Brevo REPLIED event arrives via `POST /Prospecting/brevo/email-event`
2. EmailEvent is created with eventType=REPLIED
3. EmailEventWorkflowHook fires, writes `Lead.peEmailStatus=REPLIED`, `peEmailReplyStatus=REPLIED`
4. Separately, a ReplyEvent is created with replyStatus=REPLIED
5. EmailLifecycleProjectionHook fires, also writes `Lead.peEmailReplyStatus=REPLIED`

Two independent hooks write the same Lead fields for the same conceptual event. The EmailEventWorkflowHook uses its own logic; the EmailLifecycleProjectionService uses rank ordering. They are not coordinated.

**Root cause:** The ReplyEvent entity and the EmailEvent entity overlap in semantics. Both represent "something happened after the send." EmailEvent is the Brevo webhook payload (external source of truth). ReplyEvent is the CRM's own tracking record (C10.4 design). They were designed at different times (C10.4 for ReplyEvent, C11.2 for the CRM entity) without coordinating their Lead projection behavior.

**Recommended fix:** Unify the reply/bounce projection path. Either:
- Remove the `peEmailReplyStatus` write from EmailEventWorkflowHook and let only the EmailLifecycleProjectionService handle it via ReplyEvent hooks; or
- Remove ReplyEvent's projection hook and let EmailEventWorkflowHook be the sole writer, with ReplyEvent as a read-only audit record.

### Risk D: Duplicate Send Caused by Retry Ambiguity

**Status: PARTIALLY MITIGATED — in-memory only.**

**Current protections:**
- C10.3 `SendIdempotencyRegistry`: `SendRequest` idempotency key prevents duplicate reservation in-process
- C12 `BrevoProviderAdapter`: caches `SendResult` by `(send_execution_id, request_id)` identity pair; repeat calls return cached result
- C13 `InMemorySendExecutionQueue`: enqueue is idempotent for same `send_execution_id`; double-claim rejected
- C13 `SendExecutionWorker`: same QueueItem cannot be processed twice (claim fails after first completion)

**Gaps:**
- All idempotency is process-local (`threading.RLock`). Process restart loses all registries.
- The CRM SendExecution entity has `retryCount` and `maxRetries` fields but no code that reads or enforces them.
- The C13 queue has no RETRYING state; terminal FAILED is the only post-CLAIMED outcome.
- If the CRM bridge creates a new SendExecution (new sendRequestId) from the same approved draft, the idempotency registries would not catch it — it's a different request identity.

**Risk of duplicate send in current architecture:** LOW for a single process. MEDIUM if multiple processes or a process restart intervenes. No cross-process or durable idempotency exists.

**Recommended fix:** The C14.3 bridge should check CRM SendExecution for existing SENT records for the same draftApproval before enqueuing a new send.

### Risk E: Multiple Sources of Truth

**Status: CONFIRMED.**

The following fields on Lead have multiple independent writers with no coordination:

| Field | Writers | Coordination |
|---|---|---|
| `peEmailStatus` | 4 writers (see CONFLICT-1) | Partial: projection service uses rank order; EmailEventWorkflowHook does not |
| `peEmailReplyStatus` | 2 writers (EmailEventWorkflowHook, EmailLifecycleProjectionService) | None: both write independently |
| `peLastEmailDate` | 2 writers (EmailEventWorkflowHook, EmailLifecycleProjectionService) | Timestamp comparison in projection service only |
| `peEmailCampaignName` | 2 writers (CampaignProjectionAdapter, EmailEventWorkflowHook) | None |

The G06 Boundary Audit (C11 follow-up) declared: "Single writer rule declared but NOT enforced in C11.3." This remains true at C14.3.

**Recommended fix:** Consolidate all `peEmail*` writes into EmailLifecycleProjectionService, which already has rank-ordering and timestamp-gating. Disable the direct writes in EmailEventWorkflowHook and CampaignProjectionAdapter, routing them through the projection service instead.

---

## Part 4: C14.3 Boundary Design

### 4.1 The Gap: CRM SendExecution ↔ C13 Queue/Worker/Provider

The C14.2A Send Boundary Audit identified this as **BLOCKER B2**: "No production bridge from CRM SendExecution to C13 work item/queue/worker or back to CRM result."

The current state:

```
┌──────────────────────┐         ┌──────────────────────┐
│   CRM LAYER (PHP)    │         │  CONNECTOR (Python)  │
│                      │         │                      │
│  SendExecution       │         │  InMemoryQueue        │
│  (entity, durable)   │   ???   │  SendExecutionWorker  │
│                      │─────────│  BrevoProviderAdapter │
│  DraftApproval       │  GAP!   │  UrllibBrevoHttpClient│
│  EmailEvent          │         │                      │
│  ReplyEvent          │         │  All in-memory        │
│                      │         │  All process-local    │
└──────────────────────┘         └──────────────────────┘
```

### 4.2 Recommended Bridge Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CRM LAYER (PHP)                              │
│                                                                      │
│  SendExecution (CREATED)                                             │
│       │                                                              │
│       │  [NEW] SendExecutionBridgeHook (order=10, afterSave)         │
│       │  - Fires only on status=CREATED (new records)                │
│       │  - Loads DraftApproval for contentHash, evidenceRef          │
│       │  - Loads Lead for emailAddress                               │
│       │  - POSTs to Connector bridge endpoint                        │
│       │  - Does NOT change SendExecution.status                      │
│       │                                                              │
└───────┼──────────────────────────────────────────────────────────────┘
        │
        │  POST /Prospecting/bridge/send-execution
        │  Payload: {sendRequestId, leadId, draftId, recipient,
        │            contentHash, subject?, body?}
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BRIDGE ENDPOINT (NEW)                             │
│                                                                      │
│  Python Flask/FastAPI endpoint (or PHP controller forwarding)        │
│  1. Validates payload                                                │
│  2. Constructs SendExecutionWorkItem with status=READY               │
│  3. Enqueues: InMemorySendExecutionQueue.enqueue(sendRequestId)      │
│  4. Worker processes: SendExecutionWorker.process(queueItem)         │
│  5. Collects WorkerExecutionOutcome                                  │
│  6. Returns result to CRM caller                                     │
│                                                                      │
└───────┬──────────────────────────────────────────────────────────────┘
        │
        │  Bridge result: {success, status, providerMessageId,
        │                  failureCategory, error}
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CRM CALLBACK (PHP)                               │
│                                                                      │
│  [NEW] SendExecutionResultService                                     │
│  - Receives bridge result                                            │
│  - Updates SendExecution.status (READY/SENT/FAILED)                  │
│  - Updates SendExecution.providerName, providerMessageId             │
│  - Updates SendExecution.failureCategory, lastError                  │
│  - Save triggers EmailLifecycleProjectionHook → Lead.peEmailStatus   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Key Design Decisions

#### D1: SendExecution → Queue Bridge Point

**Location:** New PHP hook `SendExecutionBridgeHook` on afterSave (order=10, before projection hook at order=50).

**Trigger:** Only when `status == 'CREATED'` and the record is new (not an update).

**Action:** POST to a new connector bridge endpoint. Does NOT set status=READY itself — the bridge sets READY after successful enqueue, and sets SENT/FAILED after Worker completion.

**Rationale:** The CREATED→READY transition must only happen after the connector confirms it accepted the work item. This prevents CRM from showing READY_TO_SEND when the connector never received the request.

#### D2: Worker Result → CRM Callback

**Location:** The bridge endpoint (Python side) synchronously waits for Worker completion and returns the result to the CRM caller. The CRM caller then updates SendExecution via `SendExecutionResultService`.

**Rationale:** For C14.3 acceptance, synchronous request-response is acceptable. The one-shot C14.2B runner already demonstrated this pattern. Async callback (webhook) is a future concern.

#### D3: Idempotency Boundary

**CRM side:** `sendRequestId` is unique on SendExecution. The bridge hook fires only once per record (afterSave, new only). Duplicate bridge calls for the same `sendRequestId` are prevented at the CRM entity level.

**Connector side:** `InMemorySendExecutionQueue.enqueue()` is idempotent for the same `send_execution_id`. C12 `BrevoProviderAdapter` caches results by `(send_execution_id, request_id)` identity. Double-send is prevented within the same process lifetime.

**Gap accepted for C14.3:** Process restart loses in-memory idempotency registries. Cross-process duplicate prevention requires durable idempotency storage (deferred to C14.4+).

#### D4: Failure Handling

| Failure Point | CRM SendExecution | Queue | Worker | Provider |
|---|---|---|---|---|
| Bridge endpoint unreachable | Stays CREATED; hook logs error | — | — | — |
| Enqueue fails | Stays CREATED; hook logs error | No item created | — | — |
| Worker claim fails | Stays READY | Item stuck QUEUED | Not invoked | — |
| Provider returns failure | status=FAILED, failureCategory set | Item FAILED | Settled as failed | Result recorded |
| Provider network error | status=FAILED, failureCategory=NETWORK | Item FAILED | Settled as failed | BREVO_NETWORK_ERROR |
| CRM update fails after worker success | status=READY (stale) | Item COMPLETED | Settled as success | Email sent |

**Note on last row:** If the provider succeeds and email is sent, but the CRM update fails, CRM shows stale state. This is a known gap for C14.3. The EmailEvent webhook path provides a backstop (Brevo SENT event will eventually update Lead.peEmailStatus), but the SendExecution record itself would remain stale. This is deferred to C14.4 (durable result delivery).

#### D5: Draft Content Availability

**Problem:** The C13 Worker's `SendExecutionWorkItem` requires `recipient`, `subject`, `body`, and `draft_hash`. The CRM DraftApproval entity stores `contentHash` and `evidenceReference` but does **not** store the email subject or body (by design — C11.4 DraftStore keeps bodies out of CRM).

**Options for C14.3:**

1. **Inline content in bridge payload:** The bridge hook reads the subject/body from wherever it's stored (Python InMemoryDraftStore, if accessible) and includes it in the bridge POST payload. This requires the draft body to be available in the Python process.

2. **Content reconstruction:** The Worker reconstructs the email from DraftApproval fields (evidenceReference, scoreSnapshot) and Lead fields (peRecommendedApproach, etc.) using the same EmailDraftGenerator. Risk: non-deterministic generation could produce different content than what was approved.

3. **Draft body URL:** The CRM stores a reference (not the body) and the Worker fetches the body from a draft storage service at send time. This keeps bodies out of CRM but requires a fetchable draft store.

**Recommendation:** For C14.3 acceptance, use Option 2 (reconstruction) with the `contentHash` verification. The `DraftStore.verify_snapshot()` can compare the approved `contentHash` against the reconstructed content. If they match, the approved intent is preserved. If they don't match, the send is rejected. This is the design intent of C11.4's content hash chain.

### 4.4 What C14.3 Must NOT Build

These are explicitly deferred:

| Item | Reason |
|---|---|
| Durable queue (Redis/Celery/DB) | C13 design constraint; in-memory acceptable for acceptance |
| Async worker daemon | C13 design constraint; explicit invocation acceptable |
| Automatic retry engine | C11.5 schema reservation only; no execution logic |
| Distributed idempotency | Process-local acceptable for single-process acceptance |
| Brevo webhook → SendExecution link | Separate EmailEvent entity; cross-referencing deferred |
| Draft body storage in CRM | C11.4 design constraint; bodies stay out of CRM |
| Multi-tenant queue | Single-process acceptance only |
| Rate limiting / circuit breaker | Not needed for controlled one-shot sends |
| Production deployment manifest | Acceptance environment only |

---

## Part 5: C10/C11/C12/C13 Safety Check

### 5.1 C10 Frozen Modules — Confirmed Intact

| Module | File | Frozen Contract | C14.3 Impact |
|---|---|---|---|
| Send idempotency | `send_idempotency.py` | `SendRequest` identity, reservation, state machine | **No change.** C14.3 bridge uses C12 SendRequest/C13 Queue, not C10 send_idempotency. |
| Human approval | `human_approval.py` | Approval state machine, registry protocol | **No change.** C14.3 reads DraftApproval (CRM entity), not C10 InMemoryHumanApprovalRegistry. |
| Send provider | `send_provider.py` | `SendProvider` Protocol, `SendProviderAdapter` | **No change.** C14.3 uses C12 BrevoProviderAdapter, not C10 SendProviderAdapter. |
| Send execution | `send_execution.py` | `ControlledSendExecutionService`, execution state machine | **No change.** C14.3 bridges CRM SendExecution to C13 Worker, bypassing C10.3 orchestration. |
| Reply tracking | `reply_tracking.py` | ReplyEvent identity, SENT-only tracking | **No change.** C14.3 bridge does not touch reply tracking. |

**Verdict:** C14.3 does not import, call, modify, or subclass any C10 frozen module. The C10 freeze boundary is intact.

### 5.2 C13 Worker Contract — Confirmed Intact

| Aspect | Current Contract | C14.3 Impact |
|---|---|---|
| `SendExecutionQueue` Protocol | `enqueue`, `claim`, `complete`, `fail` | **No change to interface.** C14.3 bridge calls these methods but does not modify the protocol. |
| `SendExecutionWorker` Protocol | `process(queue_item, timestamp)` | **No change to interface.** C14.3 bridge invokes the worker; does not modify it. |
| `SendExecutionWorkItem` structure | `send_execution_id`, `request_id`, `status`, `recipient`, `subject`, `body`, `draft_hash`, ... | **No change.** C14.3 bridge constructs WorkItems from CRM data. |
| In-memory implementation | `InMemorySendExecutionQueue`, `InMemorySendExecutionWorkStore` | **No change.** C14.3 uses the existing implementations. |

**Verdict:** C14.3 uses the C13 contracts as-is. No modification to the queue, worker, or work store protocols.

### 5.3 Brevo Adapter Contract — Confirmed Intact

| Aspect | Current Contract | C14.3 Impact |
|---|---|---|
| `ProviderAdapter` Protocol | `send(request) → SendResult` | **No change.** C13 Worker already calls this; C14.3 bridge does not add a new call path. |
| `BrevoProviderAdapter` | Implements ProviderAdapter; recipient guard at `send()` | **No change.** Guard remains active. C14.3 does not bypass it. |
| `BREVO_ACCEPTANCE_MODE` | Exact `"true"` required for recipient override | **No change.** C14.3 bridge does not read or modify this variable. |
| `BrevoHttpClient` Protocol | `post_json(path, headers, payload, timeout)` | **No change.** C14.3 bridge does not introduce a new HTTP client. |

**Verdict:** C14.3 does not touch the Brevo adapter, its configuration, its recipient guard, or its HTTP client. The adapter contract is intact.

### 5.4 Lead Projection Safety

**Potential risk:** C14.3 adds a new writer (bridge hook) that could contribute to the multiple-writer problem (CONFLICT-1).

**Mitigation:** The C14.3 design routes all `peEmail*` writes through the existing `SendExecutionResultService`, which updates the CRM SendExecution entity. The existing `EmailLifecycleProjectionHook` (order=50, afterSave on SendExecution) then projects to Lead using the established `EmailLifecycleProjectionService` with its rank-ordering and timestamp-gating.

**C14.3 does NOT:**
- Write directly to `Lead.peEmail*` fields
- Add a new hook that bypasses the projection service
- Modify EmailEventWorkflowHook (the uncoordinated writer)

**The EmailEventWorkflowHook conflict remains deferred** — C14.3 does not resolve it, but it also does not make it worse.

---

## Part 6: Implementation Scope for C14.3

### 6.1 Must Build

1. **`SendExecutionBridgeHook`** (PHP, order=10 on SendExecution afterSave)
   - Fires on new CREATED records only
   - Reads DraftApproval (contentHash, evidenceReference, scoreSnapshot) and Lead (emailAddress)
   - POSTs to connector bridge endpoint
   - Does not change SendExecution.status (bridge sets READY)

2. **Bridge endpoint** (Python, new file in `chitu_connector/espocrm_sync/`)
   - Accepts bridge payload
   - Constructs `SendExecutionWorkItem` with status=READY
   - Enqueues via `InMemorySendExecutionQueue.enqueue()`
   - Invokes `SendExecutionWorker.process()`
   - Returns `WorkerExecutionOutcome` as JSON response

3. **`SendExecutionResultService`** (PHP)
   - Receives bridge result from the hook
   - Updates SendExecution: status, providerName, providerMessageId, failureCategory, lastError
   - Save triggers existing EmailLifecycleProjectionHook → Lead.peEmailStatus

4. **Content reconstruction** (Python)
   - Reconstructs email subject/body from DraftApproval evidenceRef/scoreSnapshot + Lead fields
   - Uses contentHash from DraftApproval for `DraftStore.verify_snapshot()`
   - Rejects send if content hash mismatches

### 6.2 Must Test

1. Bridge hook fires on new CREATED SendExecution only
2. Bridge hook does not fire on status updates (READY→SENT, etc.)
3. Bridge endpoint validates payload (missing fields, malformed IDs)
4. Queue enqueue is idempotent for same sendRequestId
5. Worker processes successfully with valid input
6. Worker fails safely with invalid content hash
7. CRM SendExecution updated correctly on success/failure
8. Lead.peEmailStatus projected correctly through existing hook
9. C10 frozen modules untouched (import check)
10. C13 worker contract unchanged (protocol compliance check)
11. Brevo adapter guard remains active (acceptance mode test)

### 6.3 Must Not Build

- Durable queue storage
- Async/daemon worker
- Automatic retry logic
- EmailEvent → SendExecution linker
- peEmail* writer consolidation (deferred)
- Draft body storage in CRM
- Production deployment artifacts

---

## Part 7: Summary

| Question | Answer |
|---|---|
| Is the CRM email flow fully traced? | Yes — all 4 email entities, 6 hooks, 1 projection service, and the connector pipeline are documented. |
| Is state ownership defined? | Yes — ownership matrix identifies CRM as store owner, Connector Worker as transition owner, Provider as transport-result owner. Four-writer conflict on Lead.peEmail* is documented with deferred resolution. |
| Are historical bugs assessed? | Yes — all 5 risks (A-E) are confirmed as currently possible with root causes identified and recommended fixes scoped. |
| Is C14.3 boundary designed? | Yes — bridge hook → endpoint → enqueue → worker → result callback architecture with idempotency and failure handling defined. |
| Are C10/C11/C12/C13 contracts safe? | Yes — no frozen module, protocol, or adapter is modified by the C14.3 design. |
| What is deferred? | Durable queue, async worker, retry engine, distributed idempotency, writer consolidation, draft body storage, production deployment. |

## Change Log

| Date | Change |
|---|---|
| 2026-07-14 | Initial audit: READY_FOR_C14_3_IMPLEMENTATION |
