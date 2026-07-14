# Phase3C10 — Outreach Lifecycle Architecture Audit Report

**Date:** 2026-07-14
**Audit Type:** Read-only architecture audit
**Scope:** Full C09→C10 outreach lifecycle boundary
**Status:** **PASS WITH RISKS** — 0 BLOCKERs, 8 architectural risks, 16 PASS items

---

# Executive Summary

The Phase3C10 Outreach Lifecycle architecture is **structurally sound with well-enforced boundaries**. The C09→C10 contract boundary is correctly defined, all three state machines (approval, send attempt, execution) are properly implemented with explicit transition guards, and the human approval gate cannot be bypassed within a single process. The provider abstraction is pure — there is no real provider, no network dependency, no CRM side effects, and no credential handling in any C10 module.

However, **the entire C10 execution layer exists only in Python in-memory registries**. There are no corresponding CRM entities, no persistence, and no draft-content retrieval mechanism. The email lifecycle display layer (`EmailLifecycleSyncService`) and the C10 execution layer (`ControlledSendExecutionService`) are **disconnected systems** that share only a conceptual `draft_id`. For real provider integration, significant work is needed to bridge these gaps.

**Verdict: PASS WITH RISKS** — No code changes required before freeze, but the architectural risks documented below **must** inform the real provider integration design.

---

# PASS — Architecture Strengths Verified

## PASS-1: C09→C10 Contract Boundary Is Clean

**Verdict: PASS**

The C09→C10 boundary is a well-defined, one-directional data flow:

```
C09 (Outreach Preparation):
  OutreachInput → EmailDraft (immutable, with evidence traceability)
         │
         │  draft_id + lead_id  (conceptual boundary)
         ▼
C10 (Outreach Execution):
  DraftApproval → SendRequest → SendAttempt → SendExecution → ReplyEvent
```

C09 modules are **read-only preparation**:
- `outreach_input_adapter.py` — assembles facts (no email, no CRM writes)
- `email_draft_generation.py` — creates draft data (no AI, no provider, no CRM)
- `campaign_projection.py` — projects DRAFT_READY to 3 pe* fields on Lead only

C10 modules are **state-machine execution**:
- `human_approval.py` — approval state machine (no email content, no provider)
- `send_idempotency.py` — idempotency contract (no delivery, no CRM)
- `send_provider.py` — provider adapter (no real provider, no network)
- `send_execution.py` — controlled orchestration (no CRM writes)
- `reply_tracking.py` — reply events (no AI, no workflow)

Each C10 module explicitly declares what it does NOT do in its module docstring. Cross-boundary coupling is through immutable dataclass contracts only.

## PASS-2: No Back-Dependency from C10 to C09 Implementation

**Verdict: PASS**

C10 modules import from C09 only the **contract types** they reference:
- `send_execution.py` imports only `ApprovalStatus` and `DraftApproval` from `human_approval.py` (same layer)
- `reply_tracking.py` imports only `SendExecution*` types from `send_execution.py` (adjacent layer)
- No C10 module imports from `outreach_input_adapter`, `email_draft_generation`, or `campaign_projection`

C09 and C10 share identity only through the opaque `draft_id` and `lead_id` strings. C10 has no knowledge of draft content, evidence references, or qualification status.

## PASS-3: Approval State Machine — Correct and Terminal

**Verdict: PASS**

State machine in `human_approval.py`:

```
DRAFT_READY → PENDING_REVIEW → APPROVED → READY_TO_SEND
                              → REJECTED  (terminal, no recovery)
```

Guard verification:
| Transition | Allowed | Illegal Jump Blocked |
|---|---|---|
| DRAFT_READY → PENDING_REVIEW | ✅ | ✅ ValueError |
| PENDING_REVIEW → APPROVED | ✅ | ✅ ValueError |
| PENDING_REVIEW → REJECTED | ✅ | ✅ ValueError |
| APPROVED → READY_TO_SEND | ✅ | ✅ ValueError |
| REJECTED → ANY | ❌ | ✅ ValueError (terminal) |
| READY_TO_SEND → ANY | ❌ | ✅ ValueError (terminal) |
| DRAFT_READY → READY_TO_SEND (skip) | ❌ | ✅ ValueError |

- `approve()` and `reject()` require `reviewer_id` (validated by `_require_identifier`)
- Every transition appends an `ApprovalAuditTrace` (who, when, decision, version)
- REJECTED is terminal — a new draft identity is required for a fresh review cycle
- `InMemoryHumanApprovalRegistry` enforces one approval record per `draft_id`

## PASS-4: Send Attempt State Machine — Correct

**Verdict: PASS**

State machine in `send_idempotency.py`:

```
CREATED → READY → PROCESSING → SENT
       ↘           ↘ FAILED
        CANCELLED
```

Allowed transitions enforced by `_ALLOWED_TRANSITIONS` dict (line 158-165). `CANCELLED` is an exit from `CREATED`/`READY` only.

## PASS-5: Send Execution State Machine — Correct

**Verdict: PASS**

State machine in `send_execution.py`:

```
READY_TO_SEND → SUBMITTED → PROCESSING → SENT
                                       → FAILED
```

Both `SENT` and `FAILED` are terminal states. Allowed transitions enforced by `_ALLOWED_TRANSITIONS` dict (line 269-275).

## PASS-6: Human Approval Gate Cannot Be Bypassed

**Verdict: PASS**

`ControlledSendExecutionService.execute()` enforces a mandatory, multi-layer approval check **before any side effect**:

1. **Input validation** (line 210-212): All parameters validated before any registry access
2. **Duplicate execution check** (line 214-216): Returns `DUPLICATE_EXECUTION` if `send_request_id` already exists
3. **Approval existence check** (line 218-220): Returns `UNKNOWN_APPROVAL` if approval not found
4. **READY_TO_SEND check** (line 221-222): Returns `APPROVAL_NOT_READY` if approval not in `READY_TO_SEND`
5. **Double-send guard** (line 223-224): Returns `DRAFT_ALREADY_SENT` if any execution for this approval is `SENT`
6. **In-progress guard** (line 225-227): Returns `EXECUTION_IN_PROGRESS` if any execution is in a non-terminal state

**No code path exists** that creates a send execution without passing all these checks. The ordering ensures that rejection happens before the provider is ever called.

Test coverage (`test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py`):
- `test_approval_enforcement_requires_ready_to_send`: DRAFT_READY cannot execute
- `test_rejected_approval_cannot_execute`: REJECTED terminal blocks execution
- Provider has zero calls in both rejection scenarios

## PASS-7: Idempotency — Three Independent Layers

**Verdict: PASS**

| Layer | Key Generation | Guard | Behavior on Duplicate |
|---|---|---|---|
| C10.0-B Send Request | `SHA-256(draft_id, lead_id, send_request_id, provider_name, version)` — `created_at` excluded | `InMemorySendIdempotencyRegistry.reserve()` | Returns `EXISTING` with original `SendAttempt` |
| C10.3 Send Execution | `send_request_id` (caller-provided) | `ControlledSendExecutionService.execute()` | Returns `DUPLICATE_EXECUTION` with original `SendExecution` |
| C10.4 Reply Event | `SHA-256(version, lead_id, draft_id, send_attempt_id, thread_id, received_at, sender_reference, reply_status)` | `InMemoryReplyEventRegistry.record()` | Returns `DUPLICATE` with original `ReplyEvent` |

Each layer is independently duplicate-safe. The idempotency key for send requests deliberately excludes `created_at` so replayed requests at different times produce the same key. Retries must use a new `send_request_id` to generate a new key and new attempt.

The adapter-level cache in `SendProviderAdapter._results_by_idempotency_key` adds a fourth guard: once a provider result is cached, subsequent calls with the same idempotency key return the cached result without re-invoking validation or the provider.

Test verification (`test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py:235-275`):
- Duplicate execution returns same object (`is` identity)
- Duplicate reply returns same event (`is` identity)
- Duplicate adapter submit returns same result
- Provider called exactly once in all duplicate scenarios

## PASS-8: Provider Boundary — Pure Abstraction

**Verdict: PASS**

The `SendProvider` Protocol (line 59-64 in `send_provider.py`):

```python
class SendProvider(Protocol):
    provider_name: str
    def submit(self, request: SendRequest, send_attempt: SendAttempt) -> SendProviderResult: ...
```

Verification:
- **No real provider exists** — the codebase ships only test doubles (`SyntheticProvider`, `SequencedFakeProvider`)
- **No network client** — the adapter has no HTTP, SMTP, or SDK dependency
- **No credential handling** — no API keys, tokens, or auth in any C10 module
- **No email content** — `SendRequest` carries only identity fields (draft_id, lead_id, provider_name, send_request_id), not subject/body
- **No CRM writes** — the adapter writes only to in-memory registries
- **Provider result validation** — `validate_provider_result()` enforces contract integrity (name match, key match, version match)
- **Provider name mismatch** — adapter rejects `PROVIDER_NAME_MISMATCH` before calling provider
- **Provider exceptions contained** — `SendProviderUnavailableError` → FAILED, generic `Exception` → FAILED with `PROVIDER_ADAPTER_FAILED`
- **Provider result override** — if provider returns an invalid result (wrong key, wrong version), the adapter overrides with REJECTED

The `SendProviderAdapter` is correctly designed as a **validator+delegator**, not an executor.

## PASS-9: CRM Write Side Effects — Strictly Contained

**Verdict: PASS**

C10 modules (`send_idempotency.py`, `human_approval.py`, `send_provider.py`, `send_execution.py`, `reply_tracking.py`):
- **Zero CRM writes**
- **Zero CRM imports** (except `reply_tracking.py` imports `send_execution` types — same layer)
- **Zero database operations**
- All state is in-memory (`InMemory*Registry` classes)

CRM writes in the outreach pipeline are confined to C09 and below:

| Module | CRM Entity | Fields Written | Restriction |
|---|---|---|---|
| `campaign_projection.py` (C09) | Lead | `peEmailStatus`, `peEmailCampaignName`, `peRecommendedApproach` | 3-field allowlist |
| `crm_score_projection.py` (C08) | Lead | `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct`, `peScoreRulesVersion` | 4-field allowlist |
| `email_lifecycle.py` (C03) | Lead, Opportunity | `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` | 4-field allowlist |
| `lifecycle.py` (C02) | Lead | pe* intelligence fields | `_FORBIDDEN_SALES_FIELDS` blocklist prevents writing CRM-owned fields |

All writes are to `pe*` projection fields only. The `_FORBIDDEN_SALES_FIELDS` blocklist (`lifecycle.py:54-63`) prevents any write to `assignedUserId`, `status`, `stage`, `amount`, `closeDate`, `probability`, `teamsIds`.

C10.5 runtime acceptance test verifies zero side effects via `SideEffectLedger` — asserts empty lists for `real_email_sends`, `smtp_calls`, `external_provider_calls`, `crm_writes`, `lead_creations`, `opportunity_creations`, `workflow_executions`.

## PASS-10: Runtime Residue — Clean

**Verdict: PASS**

- **Zero `print()` calls** in any `espocrm_sync` module (grep confirmed)
- **Zero `logging.*` calls** in any `espocrm_sync` module (grep confirmed)
- **Zero `logger.debug()` calls** in any `espocrm_sync` module (grep confirmed)
- **No file I/O** in C10 modules
- **No environment variable reads** in C10 modules
- **No temporary file creation** in C10 modules
- **No diagnostic leftover code** from previous phases
- All test fixtures use in-memory doubles, no persisted artifacts
- Synthetic lifecycle tests (`lifecycle_sync.py`, `email_lifecycle_sync.py`) use try/finally rollback to clean up CRM test records

## PASS-11: State Machine Enforcement — No Bypass via Direct Mutation

**Verdict: PASS**

All C10 dataclasses use `frozen=True, slots=True`:
- `DraftApproval` — immutable (transitions create new instances via `replace()`)
- `SendRequest` — immutable
- `SendAttempt` — immutable
- `SendExecution` — immutable
- `ReplyEvent` — immutable
- `ApprovalAuditTrace` — immutable
- `SendExecutionAuditTrace` — immutable

State transitions always go through registry methods that:
1. Validate the transition against `_ALLOWED_TRANSITIONS`
2. Create a new frozen instance via `replace()`
3. Store the new instance
4. Append to audit trace

Direct mutation of state is impossible due to frozen dataclasses.

## PASS-12: Versioning and Contract Evolution

**Verdict: PASS**

Each C10 module declares a version constant:
- `SEND_REQUEST_VERSION = "c10-send-idempotency-v1"` (send_idempotency.py)
- `APPROVAL_VERSION = "c10.1-human-approval-v1"` (human_approval.py)
- `REPLY_EVENT_VERSION = "c10.4-reply-tracking-v1"` (reply_tracking.py)
- `ADAPTER_VERSION = "c09-outreach-input-adapter-v1"` (outreach_input_adapter.py)
- `GENERATION_VERSION = "c09-email-draft-boundary-v1"` (email_draft_generation.py)

Version mismatch is detected at the boundary:
- `validate_send_request()` rejects `UNSUPPORTED_REQUEST_VERSION`
- `validate_reply_event()` rejects `UNSUPPORTED_EVENT_VERSION`
- `validate_provider_result()` rejects `INVALID_REQUEST_VERSION`

This enables future contract evolution without silent incompatibility.

## PASS-13: Test Coverage — Comprehensive and Side-Effect-Free

**Verdict: PASS**

| Test File | C10 Capability | Scope |
|---|---|---|
| `test_phase3c10_evidence_dedup_hardening.py` | C10.0-A Evidence dedup | Identity formula, batch/snapshot/individual dedup |
| `test_phase3c10_send_idempotency_contract.py` | C10.0-B Send idempotency | Reservation, transition, cancellation, validation |
| `test_phase3c10_1_human_approval_model.py` | C10.1 Approval | All states, all transitions, duplicate rejection, audit |
| `test_phase3c10_2_send_provider_adapter.py` | C10.2 Provider adapter | Acceptance, rejection, failure, validation |
| `test_phase3c10_3_controlled_send_execution.py` | C10.3 Execution | Success, duplicate, approval-not-ready, already-sent, in-progress, retry-after-failure |
| `test_phase3c10_4_reply_tracking_boundary.py` | C10.4 Reply tracking | Creation, trace, duplicate, bounce, unsubscribe, validation |
| `test_phase3c10_5_outreach_lifecycle_runtime_acceptance.py` | C10.5 Full lifecycle | End-to-end synthetic path, approval enforcement, idempotency, failure containment |

All C10 tests use:
- `InMemory*Registry` implementations — no database
- Fake/synthetic providers — no network
- `SideEffectLedger` assertions — proven zero external effects
- Explicit `SideEffectLedger` assertions: zero `real_email_sends`, `smtp_calls`, `external_provider_calls`, `crm_writes`, `lead_creations`, `opportunity_creations`, `workflow_executions`

Edge cases covered:
- Rejected approval cannot execute (terminal state check)
- Provider failure maps to `FAILED` execution state
- Reply to failed send is rejected (`UNKNOWN_SENT_ATTEMPT`)
- Malformed reply (empty thread_id) is rejected (`INVALID_THREAD_ID`)
- Retry after failure requires new `send_request_id` (new idempotency key)
- C10.5 duplicate execution at all three layers (execution, provider adapter, reply)

## PASS-14: Audit Trail — Complete and Immutable

**Verdict: PASS**

Three independent, append-only audit trails:

| Module | Audit Record | Contents |
|---|---|---|
| `human_approval.py` | `ApprovalAuditTrace` | draft_id, approval_id, who, when, decision, version |
| `send_execution.py` | `SendExecutionAuditTrace` | draft_id, approval_id, send_request_id, send_attempt_id, provider, result, timestamp, state |
| `reply_tracking.py` | `original_send_trace` (embedded) | Full `SendExecutionAuditTrace` preserved in each `ReplyEvent` |

All audit traces are:
- Immutable (frozen dataclasses)
- Append-only (never modified after creation)
- Time-stamped with timezone-aware datetimes
- Version-tagged for schema evolution

## PASS-15: Thread Safety — Correct for Single-Process

**Verdict: PASS**

All in-memory registries use `threading.RLock` for synchronization:
- `InMemorySendIdempotencyRegistry._lock`
- `InMemoryHumanApprovalRegistry._lock`
- `InMemorySendExecutionRegistry._lock`
- `InMemoryReplyEventRegistry._lock`
- `SendProviderAdapter._lock`

The `ControlledSendExecutionService._lock` wraps the entire check-then-act sequence (approval check → execution creation → provider call). Within a single process, this prevents TOCTOU races between concurrent `execute()` calls.

## PASS-16: Structural Alignment with Phase G01 Freeze Audit

**Verdict: PASS**

The Phase G01 Architecture Freeze Audit (`PHASE_G01_C10_4_ARCHITECTURE_FREEZE_AUDIT.md`) confirmed:
- PASS-5 (Approval flow state machine): ✅ Still valid — no code changes to C10.1
- PASS-6 (Send execution state machine): ✅ Still valid — no code changes to C10.3
- PASS-7 (Human approval cannot be bypassed): ✅ Still valid — all guards intact
- PASS-8 (Send idempotency): ✅ Still valid — no code changes to C10.0-B

The 3 BLOCKERs identified in G01 (PHP peEvidenceType mapping, PHP zero dedup, Python adapter unused) remain unresolved — they are **pre-existing evidence-layer issues**, not C10 outreach lifecycle issues.

---

# ARCHITECTURAL RISKS — Must Inform Provider Integration

## RISK-1: C10 State Has No CRM Persistence (HIGH)

**Severity: HIGH — Integration Readiness Gap**

**Description:**

All C10 execution state exists **exclusively in Python in-memory registries**:
- `InMemoryHumanApprovalRegistry` — approval records
- `InMemorySendIdempotencyRegistry` — send attempt reservations
- `InMemorySendExecutionRegistry` — execution records
- `InMemoryReplyEventRegistry` — reply events

There are **zero corresponding CRM entities** for C10 concepts:
- No `DraftApproval` entity in CRM
- No `SendRequest` entity in CRM
- No `SendExecution` entity in CRM
- No `ReplyEvent` entity in CRM
- No entity definitions under `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/` for any C10 concept
- `grep -r "SendRequest\|SendAttempt\|DraftApproval\|ReplyEvent" crm-extension/files/` returns **zero matches**

Between connector process restarts, all C10 state is lost:
- Approval decisions are forgotten
- Send execution history is lost
- Reply events are lost
- In-flight execution state is abandoned

The Protocol interfaces (`HumanApprovalRegistry`, `SendIdempotencyRegistry`, `SendExecutionRegistry`, `ReplyEventRegistry`) correctly define the persistence seam, but only in-memory implementations exist.

**Impact on Provider Integration:**

Before real provider integration, each protocol needs a database-backed implementation with:
- CRM entity definitions (DraftApproval, SendExecution, ReplyEvent)
- REST API endpoints for CRUD operations
- Python client implementations of the Protocol interfaces
- Database-level unique constraints for idempotency keys

**Mitigation for Current Phase:**

This is acceptable for Phase3C10 because:
- The connector is a stateless, short-lived process
- Each run processes a fixed batch of pending work then exits
- No long-running server or queue worker exists
- The protocol interfaces are clean and well-tested — replacing in-memory with database-backed implementations is a pure implementation swap

## RISK-2: Email Lifecycle and C10 Execution Are Disconnected (HIGH)

**Severity: HIGH — Integration Gap**

**Description:**

Two separate systems track the outreach lifecycle, and they do not interact:

**System A: CRM Display Layer** (`email_lifecycle.py` → `EmailLifecycleSyncService`)
- Writes `peEmailStatus`, `peLastEmailDate`, `peEmailCampaignName`, `peEmailReplyStatus` to Lead/Opportunity
- Status values: NONE, DRAFT_READY, APPROVED, SENT, REPLIED, BOUNCED
- This is what the CRM UI displays
- No concept of READY_TO_SEND

**System B: Python Execution Layer** (C10 modules)
- Approval: DRAFT_READY → PENDING_REVIEW → APPROVED → READY_TO_SEND
- Execution: READY_TO_SEND → SUBMITTED → PROCESSING → SENT/FAILED
- Reply: SENT, REPLIED, BOUNCED, UNSUBSCRIBED
- All in-memory — nothing reaches CRM

**Disconnect:**

| State | System A (CRM) | System B (Python C10) |
|---|---|---|
| Draft ready | peEmailStatus=DRAFT_READY (via `campaign_projection.py`) | ApprovalStatus.DRAFT_READY (via `HumanApprovalRegistry`) |
| Human approved | peEmailStatus=APPROVED (via `EmailLifecycleSyncService`) | ApprovalStatus.APPROVED (via `HumanApprovalRegistry`) |
| Ready to send | **NOT IN CRM** | ApprovalStatus.READY_TO_SEND |
| Sent | peEmailStatus=SENT (via `EmailLifecycleSyncService`) | SendExecutionState.SENT |
| Replied | peEmailStatus=REPLIED (via `EmailLifecycleSyncService`) | ReplyStatus.REPLIED |

The CRM `peEmailStatus` enum does not include `READY_TO_SEND`:
```json
"options": ["NONE", "DRAFT_READY", "APPROVED", "SENT", "REPLIED", "BOUNCED"]
```

There is no code path that syncs C10 execution results back to CRM `peEmailStatus`. The C10.5 runtime acceptance test calls only in-memory registries — no `EmailLifecycleSyncService` is involved.

**Impact on Provider Integration:**

A real provider integration would need to:
1. Decide whether `READY_TO_SEND` is a CRM-visible state (add it to peEmailStatus enum) or a connector-internal state
2. Bridge C10 execution results (SENT, FAILED) to CRM peEmailStatus updates
3. Bridge C10 reply events to CRM peEmailStatus (REPLIED/BOUNCED) and peEmailReplyStatus updates
4. Ensure the two state machines don't diverge (e.g., CRM shows APPROVED while C10 shows FAILED)

## RISK-3: No Draft Content Retrieval Mechanism (HIGH)

**Severity: HIGH — Provider Integration Gap**

**Description:**

The C10 modules reference `draft_id` (a string) but have **no mechanism to retrieve the actual email content** (subject, body) associated with that draft.

- `DraftApproval` carries only `draft_id` and approval metadata — no email content
- `SendRequest` carries `draft_id`, `lead_id`, identity fields — no subject, body, or recipient
- `SendProvider.submit()` receives a `SendRequest` — which contains no content to send

The C09 `EmailDraft` contains the content (`subject`, `body`, `evidence_references`, `personalization_references`), but C10 modules never reference it. The C10.0-B contract explicitly states: "An immutable request to reserve one future delivery attempt" — it's a reservation, not a delivery.

A real `SendProvider` implementation would need to retrieve the draft content from somewhere, but no `DraftStore` abstraction exists. The `draft_id` is the only link.

**Impact on Provider Integration:**

A `DraftStore` abstraction is needed:
```python
class DraftStore(Protocol):
    def get(self, draft_id: str) -> EmailDraft: ...
    def get_lead_context(self, lead_id: str) -> LeadContext: ...
```

This could be backed by:
- The C09 `EmailDraftGenerator` (re-generation from source facts)
- A CRM entity storing serialized drafts
- A file system or blob store

The `SendProvider` protocol may need to be extended or a new adapter layer may need to bridge `SendRequest` identity to actual email content before calling the real provider.

## RISK-4: READY_TO_SEND State Has No CRM Visibility (MEDIUM)

**Severity: MEDIUM — Operational Visibility Gap**

**Description:**

The `READY_TO_SEND` approval state exists only in the Python in-memory registry. The CRM Lead `peEmailStatus` enum stops at `APPROVED`. This creates an operational blind spot:

1. A human operator approves the draft → CRM shows `APPROVED`
2. The connector marks the approval `READY_TO_SEND` → this is invisible in CRM
3. The connector executes the send → CRM never transitions past `APPROVED` (unless System A is separately invoked)
4. If the connector crashes between steps 2 and 3, there's no CRM-visible record that the draft was "queued for sending"
5. The operator sees `APPROVED` in CRM with no indication of whether sending occurred or failed

**CRM peEmailStatus options** (Lead.json):
```json
"options": ["NONE", "DRAFT_READY", "APPROVED", "SENT", "REPLIED", "BOUNCED"]
```

Missing: `READY_TO_SEND`, `SEND_FAILED`, `PROCESSING`

**Mitigation:**

This is a deliberate architectural choice — the CRM extension is a **projection surface**, not an **execution engine**. The connector owns the execution lifecycle. But for operational visibility, a `peEmailStatus` update should occur when C10 transitions happen.

## RISK-5: Single-Process Idempotency Guarantee (MEDIUM)

**Severity: MEDIUM — Distributed Execution Gap**

**Description:**

The `ControlledSendExecutionService._lock` (`threading.RLock`) provides idempotency guarantees **only within a single process**. In a distributed or multi-process scenario:

1. Process A checks approval status → READY_TO_SEND ✅
2. Process B checks approval status → READY_TO_SEND ✅ (same approval, different process)
3. Process A creates execution → SENT
4. Process B creates execution → **duplicate send** (process B's lock doesn't block process A)

The in-memory registries cannot prevent this. The `DRAFT_ALREADY_SENT` and `EXECUTION_IN_PROGRESS` guards work only because they query the same in-memory registry — but different processes have different registries.

**Mitigation for Current Phase:**

The connector is designed as a **single-process, stateless batch runner**. Multiple concurrent processes are not part of the current architecture. For production, database-level constraints (unique index on `idempotency_key` or `send_request_id`) would provide cross-process idempotency.

## RISK-6: Provider Adapter Locks After First Call (MEDIUM)

**Severity: MEDIUM — Retry Limitation**

**Description:**

`SendProviderAdapter` caches results by `idempotency_key` in `_results_by_idempotency_key` (line 79). Once a result is cached, **all subsequent calls with the same idempotency key return the cached result** without invoking the provider or creating a new reservation:

```python
cached = self._results_by_idempotency_key.get(request.idempotency_key)
if cached is not None:
    return cached  # Bypasses everything — provider never called again
```

This means:
- If the provider was temporarily unavailable (`PROVIDER_UNAVAILABLE`), the cached `FAILED` result prevents retry
- If the provider returns `FAILED`, the same `SendRequest` cannot be retried through the same adapter instance
- A retry requires a **new `SendProviderAdapter` instance** (clearing the cache) or a new `send_request_id` (generating a new idempotency key)

This aligns with the idempotency contract (retries use new `send_request_id`), but the adapter-level caching adds an additional hard barrier that could be surprising.

**Impact on Provider Integration:**

The real provider integration design should either:
1. Accept that retries always use new `send_request_id` (cleanest approach)
2. Add a `retry` method to `SendProviderAdapter` that clears the cache for a specific key
3. Make the caching behavior configurable

## RISK-7: No Send Queue or Retry Infrastructure (MEDIUM)

**Severity: MEDIUM — Operational Readiness Gap**

**Description:**

The C10 modules handle the happy path (approve → execute → send) and failure (FAILED state), but there is **no retry infrastructure**:

- No retry queue for FAILED executions
- No exponential backoff
- No dead-letter queue
- No max-retry counter
- No circuit breaker for provider unavailability
- No batch send capability (each `execute()` call handles one approval)

A real provider integration would need:
- A pending-send entity in CRM (or a queue system)
- A worker/poller that picks up READY_TO_SEND approvals
- Retry logic with configurable max attempts and backoff
- Failure notification (back to CRM as a `peEmailStatus` update or a new notification entity)

The `_results_by_idempotency_key` cache in `SendProviderAdapter` would need to be time-bounded or absent for a long-running send worker.

## RISK-8: CRM peEmailReplyStatus Has No Enum Constraints (LOW)

**Severity: LOW — Data Quality**

**Description:**

The CRM `peEmailReplyStatus` field on Lead and Opportunity is a `varchar(64)` with **no enum validation**:

```json
"peEmailReplyStatus": {
    "type": "varchar",
    "maxLength": 64,
    ...
}
```

The Python `ReplyStatus` enum defines: `SENT, REPLIED, BOUNCED, UNSUBSCRIBED`

The Python `EmailLifecycleUpdate` validates `reply_state` length (1-64 chars) but does not validate against an enum. Any string value can be written to CRM `peEmailReplyStatus`.

The `EmailLifecycleSyncService` sync uses `NONE`, `NO_REPLY`, and `POSITIVE_REPLY` as `reply_state` values in the synthetic test — values that don't match the `ReplyStatus` enum.

This mismatch means the CRM field can contain arbitrary strings, making it unreliable for automation or reporting.

**Mitigation:**

Add enum validation to `peEmailReplyStatus` in CRM entity definition, aligned with `ReplyStatus` enum values, or add a validation layer in `EmailLifecycleUpdate.fields()`.

---

# Architecture Inventory — C10 Module Map

| Module | File | Responsibility | CRM Writes | Provider Calls | Network |
|---|---|---|---|---|---|
| Send Idempotency Contract | `send_idempotency.py` | Request identity, reservation, state machine | ❌ None | ❌ None | ❌ None |
| Human Approval Model | `human_approval.py` | Approval state machine, audit trail | ❌ None | ❌ None | ❌ None |
| Send Provider Adapter | `send_provider.py` | Provider validation, delegation, caching | ❌ None | ❌ (delegates to injected Protocol) | ❌ None |
| Controlled Send Execution | `send_execution.py` | Orchestration from approval to provider | ❌ None | ❌ (delegates to adapter) | ❌ None |
| Reply Tracking | `reply_tracking.py` | Reply event recording with send trace | ❌ None | ❌ None | ❌ None |
| Campaign Projection (C09) | `campaign_projection.py` | DRAFT_READY projection to Lead pe* fields | ✅ 3 pe* fields on Lead | ❌ None | ❌ None |
| Email Lifecycle Sync (C03) | `email_lifecycle.py` | Display-only status sync to Lead/Opportunity | ✅ 4 pe* fields | ❌ None | ❌ None |
| Synthetic Runtime Verif. | `email_lifecycle_sync.py` | Localhost test + rollback | ✅ (rollback-cleaned) | ❌ None | ✅ localhost:8080 |

---

# State Machine Summary

## Approval (human_approval.py)

```
                    ┌─────────┐
                    │DRAFT_   │
                    │READY    │
                    └────┬────┘
                         │ submit_for_review()
                         ▼
                    ┌─────────┐
              ┌─────│PENDING  │─────┐
              │     │REVIEW   │     │
              │     └─────────┘     │
              │ approve()          │ reject()
              ▼                    ▼
         ┌─────────┐          ┌─────────┐
         │APPROVED │          │REJECTED │
         └────┬────┘          │(terminal)│
              │               └─────────┘
              │ mark_ready_to_send()
              ▼
         ┌─────────┐
         │READY_TO │
         │SEND     │
         │(terminal)│
         └─────────┘
```

## Send Attempt (send_idempotency.py)

```
  CREATED ──→ READY ──→ PROCESSING ──→ SENT (terminal)
     │          │              │
     └──→ CANCELLED            └──→ FAILED (terminal)
          (from CREATED
           or READY only)
```

## Send Execution (send_execution.py)

```
  READY_TO_SEND ──→ SUBMITTED ──→ PROCESSING ──→ SENT (terminal)
                                                 └──→ FAILED (terminal)
```

---

# Database-Level Guarantees (C10-Relevant)

| Entity | C10-Relevant Fields | Unique Constraints | Indexes |
|---|---|---|---|
| Lead | `peEmailStatus`, `peEmailReplyStatus`, `peEmailCampaignName` | `peCandidateId` (not unique index) | `peSourceBatchId` |
| Opportunity | `peEmailStatus`, `peEmailReplyStatus`, `peEmailCampaignName` | None | None |
| **DraftApproval** | **Does not exist in CRM** | — | — |
| **SendRequest** | **Does not exist in CRM** | — | — |
| **SendExecution** | **Does not exist in CRM** | — | — |
| **ReplyEvent** | **Does not exist in CRM** | — | — |

**Conclusion:** All C10 state is application-layer only. There are no database-level guarantees for approval uniqueness, execution idempotency, or reply event deduplication. This is acceptable for the current phase (stateless batch connector) but must be addressed before production deployment.

---

# Pre-Existing Issues (From Phase G01 Audit — Not C10)

These 3 BLOCKERs from the Phase G01 Architecture Freeze Audit remain **unresolved** as of 2026-07-14:

1. **BLOCKER-1 (HIGH):** PHP `ChituSyncService::syncEvidence()` maps `peEvidenceType` from `claim_type` instead of `evidence_type` — data corruption in production evidence records
2. **BLOCKER-2 (CRITICAL):** PHP `syncEvidence()` has zero dedup — every call creates duplicate ResearchEvidence records
3. **BLOCKER-3 (CRITICAL):** Python `ResearchEvidencePersistenceAdapter` (correct 3-layer dedup) is never called in production — `connector_api.py` bypasses it

These are evidence-layer issues (C07/C10.0-A), not C10 outreach lifecycle issues. They do not affect the C10 approval → send → reply architecture, but they should be resolved before or alongside C10 provider integration, since real outreach depends on correct evidence data.

---

# Provider Integration Readiness Assessment

| Capability | Current Status | Ready for Provider? |
|---|---|---|
| Approval state machine | ✅ Correct, tested | ✅ Ready — needs persistent implementation |
| Send idempotency | ✅ Correct, tested | ✅ Ready — needs persistent implementation |
| Provider abstraction | ✅ Pure Protocol | ✅ Ready — implement `SendProvider` for real provider |
| Draft content retrieval | ❌ No `DraftStore` abstraction | ❌ **Must build** draft content retrieval |
| CRM state persistence | ❌ In-memory only | ❌ **Must build** CRM entities + persistence layer |
| Email lifecycle bridge | ❌ Disconnected from C10 | ❌ **Must build** bridge between C10 execution and CRM peEmailStatus |
| Retry infrastructure | ❌ None | ❌ **Must build** retry queue, backoff, DLQ |
| Send queue | ❌ None | ❌ **Must build** pending-send entity or queue |
| Multi-process safety | ❌ Single-process lock only | ❌ **Must add** DB-level unique constraints |
| Operational visibility | ❌ No CRM-visible send state | ❌ **Must add** CRM status updates for send progress |

---

# Final Verdict

## PASS WITH RISKS

**The Phase3C10 architecture is structurally correct.** All state machines are properly defined and enforced. The human approval gate cannot be bypassed. Idempotency is correctly implemented at three independent layers. The provider boundary is pure and side-effect-free. Runtime residue is clean. Test coverage is comprehensive with verified zero-side-effect assertions.

**However**, the architecture is **not ready for real provider integration** without significant work. The entire C10 layer is in-memory, disconnected from the CRM display layer, and lacks draft content retrieval. These are deliberate architectural choices for the current phase — the connector is a stateless batch processor, not a persistent execution engine — but they define the scope of work needed before connecting a real email provider.

**No code changes are required before freeze.** The risks documented above are integration-gap risks, not correctness defects. They must inform the design of the next phase (real provider integration) but do not block the current architecture freeze.

---

## Entering Provider Integration — Required Prerequisites

Before integrating a real email provider (Brevo, SendGrid, etc.):

### Must Have (Blocker)
1. **CRM persistence for C10 state** — CRM entities for `DraftApproval`, `SendExecution`, and `ReplyEvent` with database-backed Python Protocol implementations
2. **Draft content retrieval** — A `DraftStore` abstraction that resolves `draft_id` to `EmailDraft` content (subject, body, evidence references) for the provider
3. **C10→CRM status bridge** — C10 execution transitions must update CRM `peEmailStatus` so operators can see send progress
4. **Database-level idempotency** — Unique constraints on `idempotency_key` (SendRequest) and `reply_event_id` (ReplyEvent) at the database level

### Should Have (Important)
5. **CRM peEmailStatus enum update** — Add `READY_TO_SEND`, `SEND_FAILED` options to align with C10 state machine
6. **Retry infrastructure** — Configurable max retries, exponential backoff, dead-letter handling for FAILED executions
7. **Send queue** — A pending-send entity or queue system for READY_TO_SEND approvals
8. **Multi-process safety** — Distributed lock or DB-level optimistic concurrency for controlled send execution

### Nice to Have
9. **CRM peEmailReplyStatus enum validation** — Replace varchar with enum matching `ReplyStatus`
10. **Provider adapter retry** — Clear cache mechanism for transient provider failures
11. **Send dashboard** — CRM UI showing pending/sent/failed/replied outreach states

---

**Audit complete. No code was modified, no data was created or deleted.**
