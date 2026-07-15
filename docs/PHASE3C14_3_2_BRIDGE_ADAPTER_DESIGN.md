# Phase C14.3.2 — CRM Bridge Adapter Design

## Final Verdict

**READY_TO_IMPLEMENT**

The design is constrained, the write paths are unambiguous, and all projection routing is handled by existing hooks. The bridge adapter is a narrow result-recording service — approximately 120 lines of PHP.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CONNECTOR DOMAIN (Python)                          │
│                                                                      │
│  send_execution_bridge.py                                            │
│  ├── SendExecutionBridgeRequest  (execution_id, content_hash, ...)   │
│  ├── SendExecutionBridgeResult   (normalized_status, error_class,...)│
│  └── InMemorySendExecutionBridgeFixture                              │
│                                                                      │
│  The bridge produces a terminal SendExecutionBridgeResult:           │
│    - SENT:  provider_attempt_id populated, no error                  │
│    - FAILED: error_class + error_code populated                      │
│                                                                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │  SendExecutionBridgeResult
                                │  (passed to CRM via POST/call)
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                    CRM DOMAIN (PHP) — NEW                            │
│                                                                      │
│  SendExecutionBridgeAdapterService                                   │
│                                                                      │
│  receiveResult(SendExecutionBridgeResult $result): void              │
│    │                                                                 │
│    ├── 1. Load CRM SendExecution by sendRequestId (= execution_id)   │
│    ├── 2. Validate entity state (CREATED/READY → ok)                 │
│    ├── 3. Map bridge result → entity field updates                   │
│    ├── 4. On SENT: optionally create EmailEvent                      │
│    ├── 5. Save SendExecution entity                                  │
│    │                                                                 │
│    └── saveEntity triggers existing hook (order=50):                 │
│          EmailLifecycleProjectionHook                                │
│            └── EmailLifecycleProjectionService.projectSendExecution()│
│                  └── Lead.peEmailStatus = SENT | FAILED              │
│                  └── Lead.peLastEmailDate = now                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key principle:** The bridge adapter writes only to **SendExecution** (and optionally **EmailEvent**). It **never writes to Lead directly**. Lead projection is handled by the existing `EmailLifecycleProjectionHook` (order=50 on SendExecution afterSave), which fires automatically when the adapter saves the SendExecution entity.

---

## 2. Field Write Allowlist

### 2.1 Allowed Direct Writes by Bridge Adapter

#### SendExecution fields

| Field | When Written | Value Source | Constraint |
|---|---|---|---|
| `status` | Always | `SENT` or `FAILED` | Must map from `BridgeNormalizedStatus` |
| `providerName` | SENT only | Hardcoded `"Brevo"` or from bridge config | varchar(100) |
| `providerMessageId` | SENT only | `result.provider_attempt_id` | varchar(255); must be non-empty on SENT |
| `failureCategory` | FAILED only | `result.error_class` → failureCategory | Must be valid enum value |
| `lastError` | FAILED only | `result.error_code` | Safe upper-case code, e.g. `BREVO_NETWORK_ERROR` |
| `retryCount` | FAILED only | Current value + 1 | int; min 0 |

#### EmailEvent fields (created only on SENT, optional)

| Field | Value | Constraint |
|---|---|---|
| `externalMessageId` | `result.provider_attempt_id` | Must be non-empty |
| `eventType` | `"SENT"` | Hardcoded |
| `campaign` | From `bridgeRequest.campaign_reference` | varchar(255) |
| `eventAt` | `result.occurred_at` (UTC string) | Required |
| `source` | `"CONNECTOR_SYNC"` | Distinguishes from Brevo webhook events |
| `leadId` | From `SendExecution.leadId` | Required link |

### 2.2 Forbidden Direct Writes — Must Route Through Projection

These fields are **never written directly** by the bridge adapter. They are updated automatically by the existing `EmailLifecycleProjectionHook` (order=50, afterSave on SendExecution) or `EmailEventWorkflowHook` (order=20, afterSave on EmailEvent), both of which delegate to `EmailLifecycleProjectionService`.

| Entity | Field | Projection Trigger | Rationale |
|---|---|---|---|
| Lead | `peEmailStatus` | SendExecution afterSave hook | Projection service enforces rank ordering (60=SENT, 60=FAILED) and timestamp monotonicity |
| Lead | `peLastEmailDate` | SendExecution afterSave hook | Only updated when timestamp ≥ current value |
| Lead | `peEmailReplyStatus` | ReplyEvent or EmailEvent hook | Bridge adapter does not create reply events |
| Lead | `peEmailCampaignName` | EmailEvent hook (via `projectEmailEvent`) | Set when EmailEvent is created |
| Lead | Any other field | — | Bridge adapter has no authority over Lead fields |

### 2.3 Forbidden Writes — Entity Identity and Policy Fields

| Entity | Field | Why Forbidden |
|---|---|---|
| SendExecution | `sendRequestId` | Immutable identity; set at entity creation |
| SendExecution | `draftApprovalId` | Immutable link; set at entity creation |
| SendExecution | `leadId` | Immutable link; set at entity creation |
| SendExecution | `maxRetries` | Set by retry policy configuration, not by bridge |
| SendExecution | `nextRetryAt` | Set by retry scheduler, not by bridge |
| SendExecution | `createdAt`, `modifiedAt` | ORM-managed timestamps |

---

## 3. State Validation Matrix

The bridge adapter validates the SendExecution entity's current state before applying the result:

| Current Status | Bridge Result | Action | Reason |
|---|---|---|---|
| `CREATED` | SENT | **Process** — update to SENT | Bridge invoked before hook could set READY |
| `CREATED` | FAILED | **Process** — update to FAILED | Bridge invoked before hook could set READY |
| `READY` | SENT | **Process** — update to SENT | Normal path |
| `READY` | FAILED | **Process** — update to FAILED | Normal path |
| `SENT` | SENT (same providerMessageId) | **Idempotent return** — no-op | Already recorded; return success |
| `SENT` | SENT (different providerMessageId) | **Reject** — log error | Identity conflict; two different message IDs for same execution |
| `SENT` | FAILED | **Reject** — log error | Cannot downgrade from SENT to FAILED |
| `FAILED` | SENT | **Process** — update to SENT | Retry succeeded |
| `FAILED` | FAILED | **Process** — update to FAILED | Retry failed again; increment retryCount |
| `CANCELLED` | Any | **Reject** — throw | Cancelled executions are terminal |
| (not found) | Any | **Reject** — throw | execution_id must match an existing SendExecution |

### Validation Pseudocode

```php
public function receiveResult(SendExecutionBridgeResult $result): void
{
    $execution = $this->loadExecution($result->execution_id);
    $currentStatus = $execution->get('status');

    // Terminal rejections
    if ($currentStatus === 'CANCELLED') {
        throw new BridgeRejectionException('SendExecution is cancelled');
    }

    // Idempotent return for already-SENT
    if ($currentStatus === 'SENT') {
        if ($result->normalized_status === BridgeNormalizedStatus::SENT) {
            $existingMsgId = $execution->get('providerMessageId');
            if ($existingMsgId === $result->provider_attempt_id) {
                return; // idempotent — already recorded
            }
        }
        throw new BridgeRejectionException('Cannot modify a SENT execution');
    }

    // Process: CREATED, READY, or FAILED (retry)
    $this->applyResult($execution, $result);
}
```

---

## 4. Error Mapping

### 4.1 BridgeErrorClass → SendExecution.failureCategory

The connector bridge defines 5 error classes. The CRM adapter maps them directly to the `failureCategory` enum on SendExecution:

| BridgeErrorClass | failureCategory | Nature | Example error_code |
|---|---|---|---|
| `NETWORK` | `NETWORK` | Transient transport failure | `BREVO_NETWORK_ERROR` |
| `AUTH` | `AUTH` | Permanent credential failure | `BREVO_AUTH_ERROR` |
| `VALIDATION` | `VALIDATION` | Permanent request defect | `BREVO_VALIDATION_ERROR` |
| `PROVIDER` | `PROVIDER` | Provider-side transient failure | `BREVO_PROVIDER_ERROR` |
| `UNKNOWN` | `UNKNOWN` | Unclassifiable failure | `BREVO_TRANSPORT_UNKNOWN` |

### 4.2 Known Gap: RATE_LIMIT

The `BridgeErrorClass` enum does not have a `RATE_LIMIT` value, but `SendExecution.failureCategory` does. If a rate-limit error occurs at the provider, it is reported as `error_class=PROVIDER` with `error_code=BREVO_RATE_LIMIT`. The CRM failure category will be `PROVIDER`, not `RATE_LIMIT`.

**Resolution:** This is an acceptable gap for C14.3. The `error_code` string retains the specific failure detail. If rate-limit differentiation becomes necessary, the bridge contract can be extended with a `RATE_LIMIT` class — a backward-compatible addition since `BridgeErrorClass` is a str Enum.

### 4.3 Mapping Table (Complete)

```php
private const ERROR_CLASS_TO_FAILURE_CATEGORY = [
    'NETWORK'    => 'NETWORK',
    'AUTH'       => 'AUTH',
    'VALIDATION' => 'VALIDATION',
    'PROVIDER'   => 'PROVIDER',
    'UNKNOWN'    => 'UNKNOWN',
];
```

### 4.4 SENT Result Validation

A SENT result must satisfy:
- `normalized_status === BridgeNormalizedStatus::SENT`
- `error_class === null`
- `error_code === null`
- `provider_attempt_id` is a non-empty string

If any constraint fails, the adapter rejects the result with a `BridgeRejectionException`.

---

## 5. Retry Failure Recording

### 5.1 Per-Failure Recording

On each FAILED result, the bridge adapter writes:

```php
$execution->set([
    'status'           => 'FAILED',
    'failureCategory'  => $this->mapErrorClass($result->error_class),
    'lastError'        => $result->error_code,
    'retryCount'       => ($execution->get('retryCount') ?? 0) + 1,
]);
```

### 5.2 Fields NOT Set by Bridge Adapter

| Field | Why Not Set | Who Sets It |
|---|---|---|
| `maxRetries` | This is a policy decision (e.g., "max 3 retries for NETWORK, 0 for AUTH") | Retry policy configuration, set at SendExecution creation |
| `nextRetryAt` | This requires backoff calculation (exponential, jitter) | Retry scheduler (future C14.4+) |

### 5.3 Retry Eligibility

The bridge adapter does **not** decide whether to retry. It records the failure and terminates. A future retry scheduler would:
1. Query `SendExecution` WHERE `status = 'FAILED'` AND `retryCount < maxRetries` AND `nextRetryAt <= now()`
2. Re-enqueue via the bridge's `enqueue()` method
3. The adapter processes the new result as another `receiveResult()` call

### 5.4 Retry Count Behavior

| Scenario | retryCount Before | retryCount After |
|---|---|---|
| First attempt fails | 0 | 1 |
| Retry 1 fails | 1 | 2 |
| Retry 2 succeeds | 2 | (unchanged on SENT) |
| Retry N fails, retryCount ≥ maxRetries | N | N+1 (recorded; scheduler will not re-enqueue) |

The bridge adapter increments `retryCount` on every FAILED result. It does not compare against `maxRetries` — that is the retry scheduler's responsibility.

---

## 6. EmailEvent Creation Policy (SENT Only)

### 6.1 When to Create

An EmailEvent SHOULD be created when:
- `result.normalized_status === SENT`
- `result.provider_attempt_id` is non-empty
- No existing EmailEvent with the same `(externalMessageId, eventType)` pair exists

### 6.2 Event Fields

```php
$emailEvent = $this->entityManager->getEntity('EmailEvent');
$emailEvent->set([
    'name'              => 'Send: ' . $result->provider_attempt_id,
    'externalMessageId' => $result->provider_attempt_id,
    'eventType'         => 'SENT',
    'campaign'          => $bridgeRequest->campaign_reference ?? null,
    'eventAt'           => $result->occurred_at->format('Y-m-d H:i:s'),
    'source'            => 'CONNECTOR_SYNC',
    'leadId'            => $execution->get('leadId'),
]);
$this->entityManager->saveEntity($emailEvent);
```

### 6.3 Idempotency

The `(externalMessageId, eventType)` composite index on EmailEvent prevents duplicates. If the bridge adapter is called twice with the same SENT result, the second `saveEntity` will either:
- Create a duplicate (if no unique constraint enforcement at ORM level — unlikely in EspoCRM), or
- Fail with a duplicate key error

**Recommendation:** The adapter should check for an existing EmailEvent before creating:

```php
$existing = $this->entityManager->getRDBRepository('EmailEvent')
    ->where([
        'externalMessageId' => $result->provider_attempt_id,
        'eventType' => 'SENT',
    ])
    ->findOne();
if ($existing) {
    return; // already recorded
}
```

### 6.4 Why EmailEvent Creation is Optional

EmailEvent creation is **optional** for the bridge adapter because:
- It is a convenience for CRM visibility (the SENT record appears in the Lead's email event timeline)
- It is not required for correct Lead projection — the SendExecution afterSave hook already projects `SENT` to `Lead.peEmailStatus`
- Brevo webhooks may independently create EmailEvent records for the same `externalMessageId` via `POST /Prospecting/brevo/email-event`

If the bridge adapter creates the EmailEvent and a Brevo webhook later arrives for the same message, the webhook's SENT/DELIVERED event will be rejected as a duplicate (same externalMessageId + eventType).

---

## 7. Integration with Existing Hooks

### 7.1 Hook Execution Order on SendExecution Save

When the bridge adapter calls `$this->entityManager->saveEntity($execution)`:

```
1. ORM validates entity fields
2. beforeSave hooks fire (none registered on SendExecution)
3. ORM writes to database
4. afterSave hooks fire in order:
   └── order=50: EmailLifecycleProjectionHook
         └── EmailLifecycleProjectionService.projectSendExecution()
               ├── Maps status → peEmailStatus (SENT→SENT, FAILED→FAILED)
               ├── Checks timestamp ≥ peLastEmailDate
               ├── Checks status rank (won't downgrade SENT→FAILED at same time)
               └── Saves Lead if changed
```

The bridge adapter does not need to invoke projection — the hook handles it automatically.

### 7.2 Hook on EmailEvent Save

When the bridge adapter creates an EmailEvent:

```
1. afterSave hooks fire on EmailEvent:
   ├── order=20: EmailEventWorkflowHook
   │     ├── Calls EmailLifecycleProjectionService.projectEmailEvent()
   │     │     └── Maps SENT → Lead.peEmailStatus=SENT (if not already REPLIED/BOUNCED)
   │     │     └── Updates peLastEmailDate, peEmailCampaignName
   │     └── For SENT events: no Task created (only REPLIED/BOUNCED create tasks)
   │
   └── order=30: EmailEventSalesFeedbackHook
         └── For SENT events: no SalesFeedback created (only REPLIED/CLICKED/BOUNCED)
```

The projection is handled. The bridge adapter does not need additional logic.

### 7.3 Race Condition Analysis

The bridge adapter writes to SendExecution, which triggers the projection hook. The EmailEvent creation (if performed) also triggers its own hook. Both hooks call `EmailLifecycleProjectionService`, which uses:
- **Timestamp gating**: ignores events older than `peLastEmailDate`
- **Rank ordering**: lower-ranked statuses don't overwrite higher-ranked ones at the same timestamp

Because SENT has the same rank (60) from both SendExecution and EmailEvent, and they arrive at essentially the same timestamp, the second `project*()` call will see the first one's result (via `peLastEmailDate` already set) and skip as a no-op (timestamp not newer).

**Verdict:** No race condition. The idempotent projection design handles this correctly.

---

## 8. Complete Adapter Interface

### 8.1 PHP Class Sketch

```php
namespace Espo\Modules\Prospecting\Services;

use Espo\ORM\EntityManager;

class SendExecutionBridgeAdapterService
{
    private const ERROR_CLASS_MAP = [
        'NETWORK'    => 'NETWORK',
        'AUTH'       => 'AUTH',
        'VALIDATION' => 'VALIDATION',
        'PROVIDER'   => 'PROVIDER',
        'UNKNOWN'    => 'UNKNOWN',
    ];

    private const ACCEPTABLE_RECEIVE_STATES = ['CREATED', 'READY', 'FAILED'];

    public function __construct(
        private EntityManager $entityManager,
        private EmailLifecycleProjectionService $projectionService,
    ) {}

    /**
     * Accept a terminal bridge result and write it back to CRM entities.
     *
     * Writes only to SendExecution (and optionally EmailEvent on SENT).
     * Lead projection is handled by existing afterSave hooks — never
     * written directly by this adapter.
     *
     * @throws BridgeRejectionException if the execution is in an
     *         unacceptable state or result validation fails.
     */
    public function receiveResult(SendExecutionBridgeResult $result): void;

    /**
     * Accept a bridge request for enqueue tracking.
     *
     * Transitions SendExecution from CREATED to READY, confirming
     * the connector bridge accepted the work item.
     */
    public function recordEnqueue(SendExecutionBridgeReceipt $receipt): void;
}
```

### 8.2 Method Specifications

#### `receiveResult(SendExecutionBridgeResult): void`

1. **Load execution** by `sendRequestId = result.execution_id`
2. **Validate state** — must be CREATED, READY, or FAILED (or SENT with idempotent match)
3. **Validate result** — SENT must have no error; FAILED must have error_class + error_code
4. **Apply updates** to SendExecution entity
5. **Save** SendExecution (triggers projection hook)
6. **On SENT**: optionally create EmailEvent (triggers its own hook)
7. **Return** void (throws on rejection)

#### `recordEnqueue(SendExecutionBridgeReceipt): void`

1. **Load execution** by `sendRequestId = receipt.execution_id`
2. **Validate state** — must be CREATED
3. **Update** status to READY
4. **Save** SendExecution (triggers projection hook → Lead.peEmailStatus = READY_TO_SEND)

---

## 9. What the Bridge Adapter Must NOT Do

| Forbidden Action | Why |
|---|---|
| Write to `Lead.peEmailStatus` directly | Projection service owns this field; adapter writes to SendExecution and hook handles it |
| Write to `Lead.peEmailReplyStatus` | Reply events only; bridge adapter handles send outcomes, not replies |
| Write to `Lead.peLastEmailDate` | Timestamp managed by projection service |
| Create ReplyEvent records | Reply tracking is a separate C10.4 concern |
| Create DraftApproval records | Approval is upstream of send execution |
| Modify `SendExecution.maxRetries` | Set by retry policy, not bridge |
| Modify `SendExecution.nextRetryAt` | Set by retry scheduler, not bridge |
| Invoke provider, queue, or worker | Those are connector-domain concerns behind the bridge contract |
| Make HTTP calls to Brevo | Transport is cordoned behind the bridge boundary |
| Read `BREVO_API_KEY` or any credential | Bridge adapter works only with CRM entities; no secrets |
| Decide whether to retry | Retry is a scheduling/policy decision separate from result recording |

---

## 10. Error Handling Summary

| Failure | Behavior |
|---|---|
| execution_id not found in CRM | Throw `BridgeRejectionException("Unknown execution: {id}")` |
| SendExecution is CANCELLED | Throw `BridgeRejectionException("Execution is cancelled")` |
| SendExecution is SENT (different providerMessageId) | Throw `BridgeRejectionException("Execution already SENT")` |
| SENT (same providerMessageId) | Idempotent return (no-op) |
| FAILED result with no error_class | Throw `BridgeRejectionException("FAILED result requires error_class")` |
| SENT result with error populated | Throw `BridgeRejectionException("SENT result must not include error")` |
| Invalid failureCategory value | Throw `BridgeRejectionException("Unknown error class: {class}")` |
| ORM save fails | Exception propagates to caller (transactional boundary) |
| Duplicate EmailEvent | Caught by existence check before creation; skipped silently |

---

## 11. Cross-Reference: C10/C11/C12/C13 Safety

| Contract | Impact |
|---|---|
| C10 frozen modules | **No impact.** Bridge adapter is PHP-only; does not import or call any C10 Python module. |
| C11 CRM entities | **No structural change.** Uses existing SendExecution and EmailEvent entities with their defined fields and hooks. |
| C12 Provider contract | **No impact.** Bridge adapter receives already-mapped `BridgeErrorClass` values; does not call provider. |
| C13 Worker contract | **No impact.** Bridge adapter does not import queue_contract or worker_execution. |
| C14.2B Brevo adapter | **No impact.** Bridge adapter does not read credentials, make HTTP calls, or touch the provider guard. |
| EmailLifecycleProjectionService | **No change.** Bridge adapter relies on existing hook to invoke it; does not modify the service. |
| EmailEventWorkflowHook | **No change.** Hook continues to delegate to projection service; bridge adapter benefits from this refactoring. |

---

## 12. Implementation Order

The bridge adapter has no dependencies on unimplemented components:

1. **PHP value objects** — `BridgeNormalizedStatus`, `BridgeErrorClass`, `SendExecutionBridgeResult`, `SendExecutionBridgeReceipt` (mirror the Python dataclasses)
2. **`BridgeRejectionException`** — simple domain exception
3. **`SendExecutionBridgeAdapterService`** — the service class described above
4. **API endpoint** — POST controller that accepts the bridge result and delegates to the service (not in this design scope; see C14.3.3)

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-14 | Initial design: READY_TO_IMPLEMENT |
