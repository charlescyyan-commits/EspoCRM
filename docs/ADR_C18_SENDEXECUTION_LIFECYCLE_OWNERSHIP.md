# ADR-C18: SendExecution Lifecycle Ownership

## Status

**Accepted**

### Acceptance record

- Independent architecture review completed
- A1–A5 amendments satisfied
- Ready for C18-WP1 implementation

Independent architecture review amendments **A1–A5** are incorporated into this
document. Governance marker `adr-c18-sendexecution-v1` remains mandatory for
metadata policy and contract-test alignment during C18-WP1.

## Date

2026-07-26 (proposed; amendments A1–A5 applied; accepted for C18-WP1)

## Phase

Phase3C18 — SendExecution lifecycle ownership (design freeze precursor)

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting module
- Independent architecture review (A1–A5)
- Phase3C18 implementation authorization (Accepted — Ready for C18-WP1)

## Related

- C11 / C14 SendExecution entity and bridge boundary (`CREATED` / `READY` / `SENT` /
  `FAILED` / `CANCELLED`)
- C14.3 bridge result adapter (writes SendExecution only; does not own transitions
  beyond authorized result mapping)
- C17 Command Center / Touch Center (read-only queue surfaces; no lifecycle mutation)
- Frozen release `v1.9.10-alpha` / `phase3c17-freeze` — C18 must not mutate C17 tags

## Governance Marker

**`adr-c18-sendexecution-v1`**

This marker must remain consistent across:

| Surface | Requirement |
| --- | --- |
| This ADR | Declares `adr-c18-sendexecution-v1` as the C18 ownership contract id |
| Metadata policy | Future C18 workflow/policy metadata must reference the same marker |
| Contract tests | Focused C18 tests must assert the marker string and A1–A5 invariants |

No metadata or tests are changed by this documentation-only amendment task.

---

## Amendment Record (A1–A5)

| ID | Topic | Disposition |
| --- | --- | --- |
| **A1** | Retry terminology / schema | Use entity field `maxRetries` only. Workflow policy supplies default value and global boundary. No duplicate schema field (reject `maxAttempts`). |
| **A2** | Operator abandonment | Add transition `FAILED → CANCELLED` authorized by `sendExecution.cancel`. |
| **A3** | Creation ownership | Any ACL-authorized create path may create `SendExecution`. Initial status **must** be `CREATED`. `CREATED → READY` belongs exclusively to `SendExecutionTransitionService`. |
| **A4** | Audit fields | Do not claim `sentAt` already exists. C18-WP1 additive fields: `sentAt` (readOnly, transition-owned), `sendRequestId` remains immutable idempotency evidence (already on entity; reinforce immutability). |
| **A5** | Governance marker | Freeze marker `adr-c18-sendexecution-v1` for ADR ↔ policy ↔ tests consistency. |

---

## 1. Purpose and Scope

### 1.1 Decision

Freeze **who may mutate `SendExecution.status` and related transition-owned fields**,
and under which transitions, before C18 implementation work packages begin.

### 1.2 In Scope

- Coarse CRM lifecycle: `CREATED` → `READY` → `SENT` | `FAILED` | `CANCELLED`
- Transition ownership (`SendExecutionTransitionService`)
- Creation rules and initial state
- Retry bound field `maxRetries` vs workflow policy defaults
- Operator cancel / abandonment (`FAILED → CANCELLED`)
- Additive audit fields for C18-WP1 (`sentAt`)
- Authorization action names for transitions

### 1.3 Out of Scope (Deferred)

- Provider adapters, worker/queue execution internals (C12/C13)
- `Lead.peEmailStatus` writers other than `EmailLifecycleProjectionService`
- CC-2 send-queue product expansion / analytics
- ACL role redesign (beyond naming transition authorization keys)
- Changing C17 navigation or Command Center composition

---

## 2. Context

`SendExecution` already exists as the CRM execution/audit record with status options
`CREATED`, `READY`, `SENT`, `FAILED`, `CANCELLED` and retry reservation fields
`retryCount`, `maxRetries`, `nextRetryAt`.

C14 frozen the bridge pattern: workers do not write CRM Lead email summary fields;
bridge result adapters update `SendExecution`; projection hooks update Lead.

C17 froze Command Center queues as **read-only** surfaces. C18 must therefore place
all status mutation behind an explicit transition service, not dashboards or raw
record patches from UI convenience paths.

Independent review found proposed wording that:

1. Used ambiguous `maxAttempts` terminology alongside existing `maxRetries`
2. Omitted operator abandonment `FAILED → CANCELLED`
3. Ambiguously owned creation / READY promotion
4. Incorrectly assumed `sentAt` already exists
5. Lacked a stable governance marker for policy/tests alignment

Amendments A1–A5 close those gaps in this Proposed ADR.

---

## 3. Lifecycle Ownership

### 3.1 Sole transition owner

| Concern | Owner |
| --- | --- |
| `SendExecution.status` transitions | **`SendExecutionTransitionService`** |
| Bridge/result adapters | May request authorized transitions / write provider trace fields only through the ownership rules defined for their phase; they do **not** become a second status state machine |
| Dashboards / Command Center | **No** status writes |
| Raw Record API patch of `status` | **Forbidden** for workflow clients once C18 enforcement lands (implementation gate) |

### 3.2 Allowed transitions

```text
CREATED  → READY        (transition service; prep for send)
READY    → SENT         (successful provider outcome path)
READY    → FAILED       (failed provider / validation outcome path)
READY    → CANCELLED    (cancel before terminal send, if authorized)
FAILED   → READY        (retry re-arm; subject to maxRetries / policy)
FAILED   → CANCELLED    (A2: operator abandonment)
```

Terminal for operator abandonment after failure:

| Transition | Meaning | Authorization |
| --- | --- | --- |
| `FAILED → CANCELLED` | Operator abandons further retries | `sendExecution.cancel` |

No transition may skip ownership or write `status` outside `SendExecutionTransitionService`.

### 3.3 Creation ownership (A3)

1. **Any ACL-authorized create path** may create a `SendExecution` record
   (UI, API, or approved automation that holds create ACL).
2. **Initial `status` must always be `CREATED`.** Creators must not set `READY`,
   `SENT`, `FAILED`, or `CANCELLED` at insert time.
3. **`CREATED → READY` belongs only to `SendExecutionTransitionService`.**
   Creation paths must not silently “create as READY.”

This removes ambiguous “only service X may create” wording while preserving a single
owner for readiness promotion.

---

## 4. Retry Bound: `maxRetries` (A1)

| Rule | Decision |
| --- | --- |
| Entity field | Use existing **`maxRetries`** (`entityDefs` integer, default `0`) |
| Terminology | Replace all ADR / policy language that said `maxAttempts` with **`maxRetries`** |
| Workflow policy | May supply the **default value** and a **global upper boundary** when creating or preparing executions |
| Schema | **No duplicate field** — do not add `maxAttempts` |

`retryCount` remains the execution counter. Schedulers / transition rules compare
`retryCount` against `maxRetries` under policy; they do not invent a second limit field.

---

## 5. Audit Model (A4)

### 5.1 Corrected baseline

Do **not** claim that `sentAt` already exists on `SendExecution` in the frozen
`1.9.10-alpha` entityDefs. Current packaged fields include `sendRequestId`, status,
provider trace, and retry reservation fields; **`sentAt` is absent**.

### 5.2 C18-WP1 additive fields

| Field | Rules |
| --- | --- |
| **`sentAt`** | **Additive** in C18-WP1. `readOnly`. Written only by transition ownership on successful `→ SENT`. Not editable via general record forms. |
| **`sendRequestId`** | Already required/unique. Treat as **immutable idempotency evidence** after create. Transition service and adapters must not rotate it for retries of the same logical send request. |

Provider message ids / lastError / failureCategory remain operational trace; they are
not substitutes for `sentAt` or `sendRequestId`.

---

## 6. Authorization Keys

Transition authorization (names frozen for C18 implementation / authorizer bindings):

| Action key | Typical use |
| --- | --- |
| `sendExecution.prepare` / ready promotion | `CREATED → READY` (exact key naming in metadata policy must stay consistent with marker `adr-c18-sendexecution-v1`) |
| `sendExecution.cancel` | `READY → CANCELLED` and **`FAILED → CANCELLED`** (A2) |
| Result / send outcome keys | Implementation phase binds `READY → SENT` / `READY → FAILED` without inventing dashboard mutation paths |

C18 does not redesign EspoCRM ACL tables in this ADR; it freezes **workflow action
names** that the shared authorizer pattern must bind.

---

## 7. Relationship to C17 Read-Only Queues

Command Center / Touch Center queues that list `SendExecution` remain **read-only
composition**. Operators initiate cancel/prepare actions through authorized workflow
entry points that call `SendExecutionTransitionService`, not by editing status on the
queue dashlet.

---

## 8. Implementation Boundary (Documentation Preview)

Documentation-only note for later WPs (not implemented by this task):

| WP | Intent |
| --- | --- |
| C18-WP1 | Additive `sentAt`; enforce transition service; authorizer bindings; marker in policy/tests |
| Later | Retry scheduler behavior respecting `maxRetries`; bridge outcome wiring |

No PHP, metadata, tests, artifacts, or tags are modified by this ADR amendment task.

---

## 9. Decision Log

| Date | Decision |
| --- | --- |
| 2026-07-26 | Propose ADR-C18 with independent review amendments A1–A5 applied |
| 2026-07-26 | Freeze governance marker `adr-c18-sendexecution-v1` |
| 2026-07-26 | Adopt `maxRetries` only; add `FAILED → CANCELLED` via `sendExecution.cancel`; clarify create→CREATED and READY ownership; define additive `sentAt` |
| 2026-07-26 | Accept ADR-C18 — Ready for C18-WP1 |

---

## 10. C18-WP1 Implementation Gates

ADR status is **Accepted**. The following remain C18-WP1 implementation exit gates
(not ADR blockers):

1. Marker `adr-c18-sendexecution-v1` present in metadata policy and contract tests.
2. No `maxAttempts` field or duplicate retry-limit schema.
3. Transition table includes `FAILED → CANCELLED` under `sendExecution.cancel`.
4. Creation always yields `CREATED`; READY only via `SendExecutionTransitionService`.
5. `sentAt` introduced only as readOnly transition-owned additive field; `sendRequestId` immutable after create.
