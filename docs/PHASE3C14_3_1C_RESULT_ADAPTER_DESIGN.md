# Phase3C14.3.1C Result Adapter Architecture Design

**Design-only phase.** No code, database, CRM metadata, Worker, Provider, or runtime configuration is changed here.

## Decision

**RECOMMENDED_OPTION: C — Explicit Result Command**

**READY_FOR_IMPLEMENTATION: YES — limited to an explicit terminal-result command and a CRM-side `SendExecution` result adapter.**

Current C13 queue, work-store, bridge-receipt, and Worker result state are process-local. There is no durable result ledger for a pull reconciler, while a direct Worker callback would require a new Worker integration seam. An explicit command can apply one safe terminal B-1 result to CRM `SendExecution` without adding Worker-to-CRM access, scheduling, retry, or a real send.

## Current Evidence

| Layer | Current contract | Result-adapter consequence |
|---|---|---|
| C13 Worker | Returns `WorkerExecutionOutcome(queue_item, execution, provider_result, reason_code)` only to its caller. It has no CRM client, callback, daemon, or scheduler. | Consume the result outside Worker; do not add a CRM dependency to Worker. |
| C12 Provider | `SendResult` exposes success, status, optional provider message id/status, and a safe error category/code. | Accept only normalized safe result values, never raw provider response data. |
| B-1 | `SendExecutionBridgeResult` supplies execution id, optional provider attempt id, terminal `SENT`/`FAILED`, safe error class/code, and occurred time. | This is the cross-boundary result contract. |
| CRM SendExecution | Existing fields: `status`, `providerMessageId`, `failureCategory`, `lastError`. Existing states: `CREATED`, `READY`, `SENT`, `FAILED`, `CANCELLED`. | Existing schema is sufficient for terminal result projection. |
| C11 projection | SendExecution after-save calls `EmailLifecycleProjectionService::projectSendExecution()`. | Result adapter writes SendExecution only; Lead remains indirect projection. |
| EmailEvent / ReplyEvent | Existing append-only provider-event and reply-ingestion paths own these records. | Worker result must not create either record. |

## 1. Result Ownership Matrix

The requested `providerAttemptId`, `failureClass`, and `errorCode` are B-1 result concepts; they are not current CRM field names. The current safe mapping is deliberate and needs no schema addition.

| Field / concept | Current storage | Owner | Authorized writer | Forbidden writer |
|---|---|---|---|---|
| `SendExecution.status` | CRM `SendExecution.status` | CRM execution/audit domain | C14.3.1C CRM result adapter, with guarded terminal transition | Worker, Provider, Queue, Lead hook, EmailEvent writer, ReplyEvent writer |
| `providerAttemptId` | B-1 `provider_attempt_id`; maps to `SendExecution.providerMessageId` on success | Connector/provider result boundary | CRM result adapter only | Worker direct CRM write, Lead/Event/Reply writers |
| `failureClass` | B-1 `error_class`; maps to `SendExecution.failureCategory` | Connector/provider result boundary | CRM result adapter only for failure | Worker direct CRM write, retry scheduler, Lead/Event/Reply writers |
| `errorCode` | B-1 `error_code`; maps to `SendExecution.lastError` | Connector/provider result boundary | CRM result adapter only for failure, after safe-code validation | Worker direct CRM write, raw provider-response/log writer, Lead/Event/Reply writers |
| `EmailEvent` | Separate CRM event record | Provider/webhook event-ingestion domain | Existing `BrevoEmailEventSyncService` and authorized event ingestion only | Worker, result adapter, SendExecution hook, Lead projection service |
| `Lead.peEmailStatus` | CRM Lead projection field | C11 projection domain | `EmailLifecycleProjectionService` only | Worker, result adapter, EmailEvent/ReplyEvent hook direct write, Provider, Queue |
| `ReplyEvent` | Separate CRM reply record | Reply/webhook ingestion domain | Existing authorized reply-ingestion path only | Worker, result adapter, SendExecution hook, Provider result mapper |

`providerMessageId` stays empty for a failed network result unless a safe identifier was actually observed. The adapter must never invent a message id, EmailEvent, ReplyEvent, or delivery confirmation.

## 2. State Transition Design

### Preconditions

The command accepts only a valid terminal B-1 `SendExecutionBridgeResult`:

1. `execution_id` identifies an existing CRM SendExecution.
2. CRM status is `READY`, or is already an identical terminal result replay.
3. Result status is exactly `SENT` or `FAILED`.
4. `SENT` has a non-empty safe provider attempt/message id and no error class/code.
5. `FAILED` has `NETWORK`, `AUTH`, `VALIDATION`, `PROVIDER`, or `UNKNOWN` and an upper-case safe code.
6. The initial update is a guarded `READY -> terminal` compare-and-set. A zero-row update requires a re-read and duplicate/conflict classification.

`CREATED` and `CANCELLED` are blocked. No terminal state is reopened or moved back to `READY`.

### Success

```text
Provider SUCCESS
  -> Worker returns WorkerExecutionOutcome
  -> external caller normalizes B-1 result (SENT)
  -> explicit result command
  -> CRM result adapter: SendExecution.status = SENT
                         providerMessageId = provider_attempt_id
                         failureCategory / lastError = null
  -> existing SendExecution after-save hook
  -> EmailLifecycleProjectionService
  -> Lead.peEmailStatus = SENT, only when ordered projection changes it
```

**No EmailEvent is created.** EmailEvent remains a separate provider/webhook fact stream. No ReplyEvent is created.

### Ordinary failure

```text
Provider FAILED or PERMANENT_FAILURE
  -> Worker maps provider category to C11.5 category
  -> external caller normalizes B-1 result (FAILED)
  -> CRM result adapter: status = FAILED
                         failureCategory = mapped class
                         lastError = safe error_code
                         providerMessageId = null unless safely known
  -> existing SendExecution after-save hook
  -> EmailLifecycleProjectionService
  -> Lead.peEmailStatus = FAILED, through the existing projection only
```

No EmailEvent or ReplyEvent is created: a provider failure is not an engagement event or reply.

### Network / ambiguous delivery

```text
BREVO_NETWORK_ERROR or provider timeout
  -> C12 RETRYABLE_FAILURE / NETWORK_ERROR
  -> C13 maps NETWORK_ERROR -> NETWORK and terminates its item
  -> explicit result command applies FAILED / NETWORK / BREVO_NETWORK_ERROR
```

`FAILED` means that the controlled attempt did not obtain a safe terminal provider acknowledgement. It does **not** prove that the provider did not accept the message. With no `AMBIGUOUS` state in current CRM schema, delivery truth is **UNKNOWN** until external provider-side evidence is obtained.

There is no automatic retry, requeue, resend, `RETRYING` status, or new `sendRequestId`. A timeout-driven resend is explicitly forbidden.

## 3. Option Analysis

### Option A — Worker result callback -> Result Adapter -> SendExecution

**Advantages:** immediate projection; natural future foundation for an outbox; one callback can normalize B-1 result and invoke the CRM adapter.

**Disadvantages / risks:** current Worker has no callback/publisher seam; direct Worker-to-CRM access violates isolation; process-local C13 state loses callback evidence on termination; provider acceptance followed by callback failure creates an unresolved cross-process state.

**Compatibility:** acceptable only with a separate external publisher and durable result/outbox design. Not recommended now because it otherwise requires Worker modification or new durable transport.

### Option B — Result reconciliation pull model

**Advantages:** a future durable connector result store could allow restart recovery and controlled CRM reconciliation.

**Disadvantages / recovery:** C13 Queue, work store, bridge receipt, and result are presently in-memory; there is no durable result ledger to query after restart. Pull requires polling, scheduling, retention, and reconciliation state, all outside current scope.

**Compatibility:** a viable future architecture after durable C13 result persistence, but not ready now.

### Option C — Explicit result command

**Advantages:** matches B-4 explicit ownership and caller-driven C13; no Worker change, scheduler, webhook, or Provider modification; deterministic fixture acceptance; clear operator/runtime audit trail; safe result can be replayed idempotently if retained by its caller.

**Disadvantages / risks:** not production automation; caller must retain safe result evidence; guarded CRM update must reject contradicting terminal results; current in-memory C13 cannot recover a lost result after restart.

**C13 suitability:** Yes, for current C13 acceptance. The Worker keeps returning its unchanged outcome; its caller or a fixture supplies the normalized result to the command.

## 4. Idempotency and Conflict Rules

The idempotency identity is the stable `execution_id` plus normalized terminal values. No new CRM field is needed.

| Current CRM state | Incoming result | Action |
|---|---|---|
| `READY` | `SENT` | Guarded one-time update to `SENT` and provider message id. |
| `READY` | `FAILED` | Guarded one-time update to `FAILED`, failure category, and safe error code. |
| `SENT` | Same `SENT` and same provider message id | No-op `DUPLICATE_RESULT`; no CRM save. |
| `FAILED` | Same `FAILED`, category, and safe error code | No-op `DUPLICATE_RESULT`; no CRM save. |
| `SENT` or `FAILED` | Different terminal values | `RESULT_CONFLICT`; no mutation. |
| `CREATED` / `CANCELLED` | Any result | `RESULT_NOT_APPLICABLE`; no mutation. |

The guarded update prevents two result consumers from overwriting terminal state. If another writer wins, the loser re-reads and applies the table.

Repeated consumption cannot duplicate SendExecution updates, because equal results do not save. It cannot create EmailEvent because the result adapter has no EmailEvent path. It cannot repeat a Lead change because the adapter does not write Lead, duplicate results do not save SendExecution, and the existing projection service writes Lead only when values change.

Existing EmailEvent ingestion separately deduplicates external message id plus event type. It must remain separate from Worker execution results.

## 5. Security and Data Boundary

Input and audit output contain only B-1 safe values: execution id, optional provider attempt/message id, terminal status, error class, safe error code, and timestamp. They exclude recipient, subject, body, provider response body, API key, authorization header, token, and underlying network exception details.

The adapter does not read B-3 raw payload snapshots, reconstruct a provider request, query a Provider, or create event records. Worker is still the only existing component that consumes payload during execution.

## 6. Compatibility Review

| Boundary | Assessment | Preservation requirement |
|---|---|---|
| C10 frozen modules | PASS | Do not import or alter C10 approval, lifecycle, idempotency, or provider modules. CRM `APPROVED` is not C10 `READY_TO_SEND`. |
| C11 projection | PASS WITH RISK | Save SendExecution only; existing after-save hook invokes the sole Lead-status writer. Preserve C11 ordering and acknowledge its deferred cross-writer risk. |
| C12 lifecycle | PASS | Normalize existing SendResult only; do not change enums, mapping, or ProviderAdapter. |
| C13 Worker | PASS | Consume returned outcome outside Worker. No CRM import, callback, queue change, or publisher is added to Worker. |
| C14.2B Brevo | PASS | Preserve `RETRYABLE_FAILURE -> NETWORK -> FAILED` for `BREVO_NETWORK_ERROR`; no retry or resend. |

## 7. Minimum Future Implementation Surface

Option C requires only:

1. `chitu-connector/chitu_connector/espocrm_sync/send_execution_result_adapter.py` for safe result validation, normalization, duplicate/conflict decisions, and CRM-result repository protocol.
2. `scripts/acceptance/phase3c14_3_1c_apply_result.py` for explicit fixture/operator result application and `APPLIED`, `DUPLICATE_RESULT`, `BLOCKED`, or `RESULT_CONFLICT` output.
3. `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionResultAdapterService.php` for guarded SendExecution terminal update only. Existing after-save projection remains unchanged.
4. Focused connector and extension tests plus the implementation report.

### Explicitly prohibited files / surfaces

- `chitu-connector/chitu_connector/espocrm_sync/worker_execution.py`
- `chitu-connector/chitu_connector/espocrm_sync/queue_contract.py`
- `chitu-connector/chitu_connector/espocrm_sync/provider_contract.py`
- Brevo transport/provider and C14.2B runner files
- C10 frozen modules
- CRM entity definitions, layouts, ACL, database migrations, and Lead metadata
- `EmailLifecycleProjectionService.php` and EmailEvent/ReplyEvent writers

## 8. Test Plan

1. Valid `SENT` result updates one SendExecution and existing hook projects `Lead.peEmailStatus = SENT`.
2. Each failure category updates only `FAILED`, `failureCategory`, and safe `lastError`; no retry or requeue occurs.
3. `BREVO_NETWORK_ERROR` applies only `FAILED/NETWORK`, no provider message id, and no automatic resend.
4. Same result twice returns `DUPLICATE_RESULT`, with no second source save or Lead update.
5. Contradictory terminal result returns `RESULT_CONFLICT`, preserving terminal CRM values.
6. Assert no Worker, Queue, Provider, Brevo, EmailEvent, ReplyEvent, or Lead-write dependency in result adapter source.
7. Run C10 frozen checks, C11 projection tests, C12/C13 tests, B-1 through B-4 tests, extension regression, and synthetic-only acceptance. No email send.

## Final Verdict

**RECOMMENDED_OPTION: C — Explicit Result Command**

**READY_FOR_IMPLEMENTATION: YES — only for the minimal explicit result adapter, guarded SendExecution update, and synthetic acceptance tests above.**

Durable result persistence, callback/outbox delivery, pull reconciliation, scheduler operation, retry policy, real Brevo execution, EmailEvent creation, and ReplyEvent creation remain deferred.
