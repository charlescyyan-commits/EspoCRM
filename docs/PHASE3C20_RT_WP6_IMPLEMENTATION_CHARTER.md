# Phase3C20 RT-WP6 Implementation Charter — Ownership & Reservation Metadata Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | RT-WP6 Ownership & Reservation Metadata Foundation Lite Charter (planning only) |
| Work package | RT-WP6 Lite — Ownership & Reservation Metadata Foundation |
| Charter path | `docs/PHASE3C20_RT_WP6_IMPLEMENTATION_CHARTER.md` |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed`) |
| RT-WP3 | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed`) |
| RT-WP4 | COMPLETED + TAGGED (`phase3c20-rt-wp4-implementation-completed`) |
| RT-WP5 | COMPLETED + TAGGED (`phase3c20-rt-wp5-implementation-completed` → `0de06ceb3438ca6bc5b17973e44e46a8129b20f2`) |
| Independent ratification review | RATIFIED (independent review PASS) |
| Execution mode | Charter authoring only — no runtime, metadata, entity, service, test, connector, or C25 change |
| Implementation authorization | **NOT AUTHORIZED** |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
This charter defines the minimal Ownership & Reservation Metadata Foundation
Lite planning contract. It creates no code, modifies no runtime, authorizes no
implementation, and does not release full Runtime Charter §25 pre-dispatch
idempotency reservation execution, RT-WP7–RT-WP8, or C25.

Reservation metadata ≠ reservation execution.
```

---

## 1. Scope

RT-WP6 Lite covers exactly six surfaces:

| # | Allowed surface | Meaning |
| --- | --- | --- |
| 1 | Reservation intent vocabulary | Closed set of non-executive intent labels (see §2) |
| 2 | Ownership reference | Non-secret ownership identity reference for a governed request |
| 3 | Reservation metadata contract | Logical fields that record reservation intent without acquiring locks |
| 4 | Conflict representation | How conflicting ownership/intent claims are represented for audit |
| 5 | Validation policy | Fail-closed rules for unknown intents, illegal ownership shapes, conflicts |
| 6 | Audit representation | Non-secret, reviewable ownership/reservation metadata |

```text
Ownership & Reservation Metadata Foundation Lite only.
Not a reservation execution engine.
Not a distributed lock / mutex / Redis / DB lock system.
```

### 1.1 Purpose

Represent ownership and reservation **intent metadata** so foundation paths can
express who owns a request identity and whether reservation intent is declared,
held as metadata, conflicted, or released as metadata — without executing
reservation, suppressing provider calls, or acquiring any lock.

### 1.2 Non-purpose

Deliver distributed locks, mutexes, Redis/DB locks, queue/worker/scheduler
reservation, retry, recovery, job/provider/connector reservation, HTTP outbound,
execution orchestration, AIJob lifecycle mutation, C25 lifecycle, Opportunity
lifecycle, CRM sales authority, secret handling, or credential resolution.

### 1.3 Preconditions

| Predecessor | Status | Lite dependency |
| --- | --- | --- |
| RT-WP0 | EXITED | Live contracts locked |
| RT-WP1 | EXITED | Capability/purpose direction locked |
| RT-WP2 | COMPLETED + TAGGED | ProviderBinding policy consumable; not modified |
| RT-WP3 Lite | COMPLETED + TAGGED | Dispatch boundary consumable; not redesigned |
| RT-WP4 Lite | COMPLETED + TAGGED | Foundation state consumable; not redesigned |
| RT-WP5 Lite | COMPLETED + TAGGED | Failure metadata consumable; not redesigned |
| Four-value portfolio | Frozen | Unchanged |
| C20-INV-02 / C20-INV-03 | ACTIVE | Unchanged |
| C20-INV-04–13 | DEFERRED | No activation by this charter (including INV-11) |

### 1.4 Lite vs full Runtime Charter §25

| Surface | This Lite charter | Full Runtime Charter §25 |
| --- | --- | --- |
| Reservation intent vocabulary / ownership metadata | **In scope** | Prerequisite |
| Conflict representation / validation / audit | **In scope** | Prerequisite |
| Pre-dispatch unique-constraint acquisition | **Out of scope** | In scope |
| Stale reservation recovery / replay suppression | **Out of scope** | In scope |
| Provider-call suppression via reservation | **Out of scope** | In scope |
| INV-11 eligibility / activation | **Not claimed** | Post-executor review path |

```text
Lite label: RT-WP6 Lite — Ownership & Reservation Metadata Foundation

Full Runtime Charter §25 (Pre-Dispatch Idempotency Reservation) remains a
separate, deferred surface and is NOT authorized by this Lite charter.
```

### 1.5 Architecture relationship

```text
Consumes:  RT-WP3 Dispatch boundary, RT-WP4 Execution State, RT-WP5 Failure Metadata
Provides:  reservation / ownership metadata only
Does not:  execute reservation / lock / recover / dispatch
```

---

## 2. Reservation Intent Definition

### 2.1 Exact Lite closed vocabulary (planning defaults)

| Intent | Meaning | Implies lock acquisition? |
| --- | --- | --- |
| `NONE` | No reservation intent declared | **No** |
| `DECLARED` | Ownership/reservation intent declared as metadata | **No** |
| `HELD_METADATA` | Intent recorded as held for audit (logical hold only) | **No** |
| `CONFLICT` | Conflicting ownership/intent detected as metadata | **No** |
| `RELEASED_METADATA` | Intent released as metadata (logical release only) | **No** |

```text
Exact Lite intent vocabulary (5 values):
NONE
DECLARED
HELD_METADATA
CONFLICT
RELEASED_METADATA
```

```text
HELD_METADATA ≠ Redis/DB/mutex lock held.
RELEASED_METADATA ≠ lock unlock.
CONFLICT ≠ queue/worker contention resolution.
```

### 2.2 Forbidden intent / engine labels

| Forbidden label | Reason |
| --- | --- |
| `ACQUIRED` / `LOCKED` / `LEASED` | Implies execution lock |
| `QUEUED` / `CLAIMED_BY_WORKER` | Queue/worker reservation |
| `PROVIDER_RESERVED` | Provider/connector reservation |
| `RETRY_PENDING` / `RECOVERING` | Retry/recovery engine |
| `RESERVATION_EXECUTING` | Execution orchestration |

---

## 3. Ownership Metadata Model

### 3.1 Logical ownership fields

| Field (logical) | Required | Meaning | Secret? |
| --- | --- | --- | --- |
| `requestIdentity` | Yes | Governed request identity being described | No |
| `ownerReference` | Yes (when intent ≠ `NONE`) | Non-secret owner identity reference (actor/system ref) | No |
| `reservationIntent` | Yes | Exactly one of the five Lite intents | No |
| `ownershipScope` | Optional | `REQUEST` \| `BOUNDARY` — not C25/Opportunity | No |
| `correlationReference` | Optional | Non-secret boundary/provenance reference | No |
| `conflictReference` | Optional | Non-secret reference to conflicting claim identity | No |
| `recordedAt` | Optional | Audit timestamp | No |

### 3.2 Ownership rules

```text
Ownership metadata names a reference.
It does not grant execution authority.
It does not acquire a lock.
It does not suppress provider calls.
```

| Rule | Behavior |
| --- | --- |
| Unknown intent | Reject fail-closed |
| Secret-bearing owner/payload | Reject fail-closed |
| Owner inferred from C25 / Opportunity / sales fields | Forbidden |
| Ownership write that acquires lock / enqueues worker | Forbidden |

### 3.3 Capability portfolio lock (unchanged)

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

```text
COMMERCIAL_BRIEF is not a CompletionCapability.
```

---

## 4. Conflict Representation

### 4.1 What conflict means in Lite

A **conflict** is an audit-visible metadata condition: two non-secret ownership
or reservation-intent claims for the same `requestIdentity` (or documented
equivalent identity) cannot both be `HELD_METADATA` under Lite validation.

| Field | Rule |
| --- | --- |
| `reservationIntent = CONFLICT` | Records conflict as metadata |
| `conflictReference` | Optional non-secret pointer to other claim |
| `conflictReasonCode` | Bounded: `OWNER_MISMATCH` \| `DUPLICATE_INTENT` \| `UNKNOWN_CONFLICT` |

### 4.2 What conflict does **not** mean

- Mutex / Redis / DB lock failure
- Queue backpressure
- Worker claim collision resolution
- Automatic recovery / takeover
- Provider-call suppression

```text
Conflict representation is informational + validation.
It is not a concurrency control engine.
```

---

## 5. Validation Boundary

| Rule | Behavior |
| --- | --- |
| Unknown `reservationIntent` | Reject fail-closed |
| Illegal intent transition (when transitions are defined at plan/foundation) | Reject fail-closed |
| `HELD_METADATA` without `ownerReference` | Reject fail-closed |
| Secret-shaped fields/values | Reject fail-closed |
| Retry / queue / worker / lock control fields in payload | Reject fail-closed |
| Correlation inventing RT-WP4 engine states (`QUEUED`/`RUNNING`/…) | Reject fail-closed |
| C25 / Opportunity driven ownership | Reject fail-closed |

Logical consume-only relationships:

| Upstream | Lite use |
| --- | --- |
| RT-WP3 boundary | Optional `correlationReference` / boundary id only |
| RT-WP4 state | May annotate near `READY`/`BLOCKED`/`FAILED` paths; does not redesign states |
| RT-WP5 failure metadata | May coexist for `CONFLICT`/`FAILED` audit; does not redesign failure codes |

---

## 6. Audit Representation

### 6.1 Required properties

| Property | Requirement |
| --- | --- |
| Non-secret | No credentials, tokens, or lock handles |
| Deterministic vocabulary | Intent must be one of the five closed values |
| Reviewable | Owner reference + intent + optional conflict reason |
| Non-executive | Must not schedule recovery, acquire locks, or dispatch |

### 6.2 Allowed audit content

- `reservationIntent`
- `ownerReference`
- `requestIdentity`
- optional `ownershipScope`, `correlationReference`, `conflictReference`, `conflictReasonCode`, `recordedAt`

### 6.3 Forbidden audit content

- Lock tokens / lease ids from Redis/DB/mutex systems
- Queue/worker claim payloads
- Retry schedules / recovery plans
- Provider reservation handles
- C25 CommercialBrief / Opportunity decision narratives as ownership authority
- Claims of INV-11 satisfaction

---

## 7. Security

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret in metadata / logs / fixtures | Ownership payloads are non-secret only |
| No credential resolution | Never resolve tokens/secrets |
| No lock / Redis / DB / mutex acquisition | Metadata only |
| No retry / recovery / queue / worker side effects | Metadata write must not enqueue or lock |
| ACL / Portal | Operator surfaces Portal-denied where applicable |
| Admin no-bypass | Future mutation guards must apply to all roles |
| No C25 audit rewrite | C25 owns its audit |

Invariant posture preserved:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation; INV-11 remains DEFERRED)
```

---

## 8. Explicit Exclusions

| Forbidden surface | Reason |
| --- | --- |
| Distributed lock / mutex / Redis lock / database lock | Reservation execution — excluded |
| Queue / worker / scheduler reservation | Execution engine — excluded |
| Retry / recovery / stale-lease recovery | Full §25 / later — excluded |
| Job / provider / connector reservation | Connector/engine — excluded |
| HTTP outbound / execution orchestration | Forbidden |
| AIJob lifecycle / unique-constraint acquisition | Full §25 — excluded |
| Provider-call suppression via reservation | Full §25 — excluded |
| ProviderBinding mutation / credential handling | RT-WP2 ownership; consume only |
| CompletionCapability enum change | ADR-C20-005 locked |
| C25 / Opportunity / sales CRM authority | C25 WP2.2 NO GO |
| Secret resolution / provider authentication | Forbidden |
| INV-11 activation / invariant registry flips | RT-WP7 / governance only |

```text
STOP conditions:
- Scope expansion into lock/execution reservation
- C25 entry
- Queue / Worker / Scheduler introduction
- Provider / Connector modification
- Git failure under authorized commit steps
```

---

## 9. Tests and Exit Criteria

### 9.1 Test requirements (when implementation separately authorized)

| Category | Coverage |
| --- | --- |
| Contract | Exact five-intent vocabulary; ownership fields; non-secret representation |
| Validation | Unknown intent / illegal ownership / secret payload rejected |
| Conflict | Conflict representation recorded without lock/queue semantics |
| Isolation | No lock/Redis/DB/mutex/queue/worker/retry/connector/HTTP/C25 markers |
| Regression | RT-WP2–WP5 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |

No Lite test may acquire locks, call Redis/DB lock APIs, invoke Connector,
resolve secrets, assert provider-call suppression, or claim INV-11 / §25 exit.

### 9.2 Charter exit (this document)

Complete for independent ratification review when:

1. Scope is explicit (§1).
2. Reservation intent definition is explicit (§2).
3. Ownership metadata model is explicit (§3).
4. Conflict representation is explicit (§4).
5. Validation boundary is explicit (§5).
6. Audit representation is explicit (§6).
7. Security is explicit (§7).
8. Exclusions are explicit (§8).
9. Tests and exit criteria are explicit (§9).
10. Implementation remains **NOT AUTHORIZED** until separate authorization +
    Foundation Review PASS.

### 9.3 Implementation exit (future; not claimed now)

1. Independent Plan Review and Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §1 only.
3. Five intents + ownership/conflict contracts proven; lock/executor absent.
4. No connector / HTTP / worker / retry / lock / C25 coupling.
5. Independent Implementation Review PASS.
6. Separate commit/push/tag authorization obtained.

Full Runtime Charter §25 idempotency reservation execution and INV-11
activation remain **out of Lite scope**.

---

## Authorization Boundary

```text
Charter status:
RATIFIED

RT-WP6 Lite Implementation:
NOT AUTHORIZED

Full RT-WP6 / Runtime Charter §25 Reservation Execution:
NOT AUTHORIZED

Any runtime code:
NOT AUTHORIZED

RT-WP7–RT-WP8:
NOT AUTHORIZED

C25 WP2.2:
NO GO
```

Charter ratification approves **planning direction only**. It does not start
implementation, create allowlists, or authorize commit/push/tag.
Implementation remains NOT AUTHORIZED until a separate implementation
authorization is issued.

| Item | Status |
| --- | --- |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2–RT-WP5 Lite | COMPLETED + TAGGED |
| RT-WP6 Lite Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP6 Lite Implementation | NOT AUTHORIZED |
| Full §25 Reservation Execution | NOT AUTHORIZED |
| RT-WP7–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

---

## Final Decision

```text
RATIFIED — STATUS SYNCHRONIZED
```

Independent ratification review returned **PASS** / **RATIFIED**. No BLOCKER,
HIGH, MEDIUM, or LOW finding alters scope. Charter status is therefore
synchronized to RATIFIED. Implementation remains NOT AUTHORIZED.

```text
Next Task:
Phase3C20 RT-WP6 Charter Documents Commit and Push
```

---

## References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§14, §25 — full reservation deferred)
2. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md`
4. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
6. `docs/adr/C20_INVARIANT_REGISTRY.md`
7. Live tags: `phase3c20-rt-wp5-implementation-completed`, `phase3c20-rt-wp4-implementation-completed`
8. Live HEAD at charter drafting: `0de06ceb3438ca6bc5b17973e44e46a8129b20f2`

---

*This charter is a planning document. It creates no production runtime change,
modifies no RT-WP2–WP5 implementation, stages no commit, and authorizes no
code. Ownership & Reservation Metadata Foundation Lite implementation begins
only under a separate, explicit authorization.*
