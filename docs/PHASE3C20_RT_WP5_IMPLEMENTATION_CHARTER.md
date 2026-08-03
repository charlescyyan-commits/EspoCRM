# Phase3C20 RT-WP5 Implementation Charter — Failure Metadata Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | RT-WP5 Failure Metadata Foundation Lite Charter (planning only) |
| Work package | RT-WP5 Lite — Failure Metadata Foundation |
| Charter path | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md` |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed`) |
| RT-WP3 | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed`) |
| RT-WP4 | COMPLETED + TAGGED (`phase3c20-rt-wp4-implementation-completed` → `8a1aa9341ed14cdae546c3bafbbb66b1c40f21a9`) |
| Independent ratification review | RATIFIED (independent review PASS) |
| Execution mode | Charter authoring only — no runtime, metadata, entity, service, test, connector, or C25 change |
| Implementation authorization | **NOT AUTHORIZED** |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
This charter defines the minimal Failure Metadata Foundation Lite planning
contract. It creates no code, modifies no runtime, authorizes no
implementation, and does not release full Runtime Charter §24 retry
classification/executor work, RT-WP6–RT-WP8, or C25.
```

---

## 1. Scope

RT-WP5 Lite covers exactly five surfaces:

| # | Allowed surface | Meaning |
| --- | --- | --- |
| 1 | Failure vocabulary | Closed set of non-secret failure category values (see §3) |
| 2 | Failure classification | Map foundation-visible failure reasons to vocabulary categories fail-closed |
| 3 | Failure metadata contract | Logical fields that record failure context without executing recovery |
| 4 | Audit representation | Non-secret, reviewable failure context correlated to foundation state |
| 5 | State correlation | Relate failure metadata to RT-WP4 Lite terminal `FAILED` / `BLOCKED` outcomes |

```text
Failure Metadata Foundation Lite only.
Not a failure execution system.
Not a retry engine.
```

### 1.1 Purpose

Record failure context so foundation outcomes are auditable and classifiable.

### 1.2 Non-purpose

Deliver retry, recovery, queue, worker, scheduler, reservation, provider error
execution, connector changes, HTTP outbound, AIJob lifecycle mutation, C25
lifecycle, Opportunity lifecycle, CRM sales authority, or secret handling.

### 1.3 Preconditions

| Predecessor | Status | Lite dependency |
| --- | --- | --- |
| RT-WP0 | EXITED | Live contracts locked |
| RT-WP1 | EXITED | Capability/purpose direction locked |
| RT-WP2 | COMPLETED + TAGGED | ProviderBinding policy consumable; not modified |
| RT-WP3 Lite | COMPLETED + TAGGED | Dispatch boundary consumable; not redesigned |
| RT-WP4 Lite | COMPLETED + TAGGED | Foundation state vocabulary consumable; `FAILED`/`BLOCKED` correlation |
| Four-value portfolio | Frozen | Unchanged |
| C20-INV-02 / C20-INV-03 | ACTIVE | Unchanged |
| C20-INV-04–13 | DEFERRED | No activation by this charter (including INV-10) |

### 1.4 Lite vs full Runtime Charter §24

| Surface | This Lite charter | Full Runtime Charter §24 |
| --- | --- | --- |
| Failure categories / classification vocabulary | **In scope (metadata only)** | Included as input to retry policy |
| Failure metadata contract / audit representation | **In scope** | Prerequisite only |
| Retryable/non-retryable policy enforcement | **Out of scope** | In scope |
| `nextRetryAt` / attempt budget / backoff | **Out of scope** | In scope |
| Automatic / operator retry executor | **Out of scope** | In scope |
| INV-10 eligibility / activation | **Not claimed** | Post-executor review path |

```text
Lite label: RT-WP5 Lite — Failure Metadata Foundation

Full Runtime Charter §24 (Retry Classification and Executor) remains a
separate, deferred surface and is NOT authorized by this Lite charter.
```

---

## 2. Failure Metadata Model

### 2.1 Logical contract (planning)

| Field (logical) | Required | Meaning | Secret? |
| --- | --- | --- | --- |
| `failureCategory` | Yes (when failure context recorded) | Closed vocabulary value from §3 | No |
| `failureClass` / `errorClass` (logical) | Optional | Non-secret class label for audit correlation | No |
| `failureMessageSafe` | Optional | Operator-safe summary; never raw provider/body secrets | No |
| `correlatedFoundationState` | Yes (when correlated) | RT-WP4 Lite state that owns the outcome (`FAILED` or `BLOCKED`) | No |
| `correlationReference` | Optional | Non-secret provenance reference (request/boundary id only) | No |
| `recordedAt` | Optional | Audit timestamp of metadata recording | No |
| `sourceLayer` | Optional | `FOUNDATION` \| `POLICY` \| `VALIDATION` — not provider transport | No |

### 2.2 Recording rule

```text
Failure metadata records context.
It does not schedule recovery.
It does not transition engine job status.
It does not invoke Connector.
```

| Rule | Behavior |
| --- | --- |
| Unknown category | Reject fail-closed |
| Secret-bearing payload | Reject fail-closed |
| Category without correlated terminal foundation outcome when claiming failure context | Reject or leave unset — no silent invent |
| Metadata write that triggers retry / queue / worker | Forbidden |
| Infer category from C25 / Opportunity / sales fields | Forbidden |

### 2.3 Relationship to RT-WP4 Lite

| RT-WP4 state | Failure metadata role |
| --- | --- |
| `FAILED` | Primary correlation target for unrecoverable foundation failure context |
| `BLOCKED` | May carry policy/authorization classification distinct from processing `FAILED` |
| `REQUESTED` / `VALIDATING` / `READY` / `COMPLETED` | No terminal failure metadata required by Lite |

```text
FAILED (Lite) may carry failure metadata.
Failure metadata must not invent RETRY_PENDING or re-open COMPLETED.
```

---

## 3. Failure Categories

### 3.1 Closed Lite vocabulary (aligned to existing C20 taxonomy labels)

| Category | Meaning (Lite metadata) | Implies retry? |
| --- | --- | --- |
| `NETWORK` | Transport/connectivity class observed or reported as foundation-visible context | **No** (Lite records only) |
| `PROVIDER` | Provider-side error class as metadata | **No** |
| `AUTH` | Authentication/credential-reference eligibility class as metadata | **No** |
| `RATE_LIMIT` | Rate-limit class as metadata | **No** |
| `VALIDATION` | Contract/validation failure class | **No** |
| `UNKNOWN` | Unclassified fail-closed fallback when no safer category applies | **No** |
| `QUOTA` | Quota class as metadata | **No** |
| `CONTENT_FILTER` | Content-filter class as metadata | **No** |

```text
Eight-value category set is vocabulary + classification only.
Lite does not encode retry eligibility tables, budgets, or backoff.
```

### 3.2 Classification principles

1. Categories are **labels for audit**, not execution instructions.
2. Classification is fail-closed: unknown input → reject or `UNKNOWN` only where charter-approved mapping exists; no open-string categories.
3. Provider transport details remain connector-owned; Lite may accept **already-normalized** non-secret class labels when separately allowed by Foundation Review allowlist — it must not call providers to obtain them.
4. Policy/authorization blocks prefer correlation to `BLOCKED` with a safe category (typically `VALIDATION` or documented policy mapping), not provider execution errors.
5. No category value authorizes `FAILED → QUEUED`, `nextRetryAt` mutation, or worker enqueue.

### 3.3 Explicitly deferred classification behaviors

| Deferred behavior | Owner |
| --- | --- |
| Retryable set `{NETWORK, PROVIDER, RATE_LIMIT}` as **executor policy** | Full Runtime Charter §24 |
| Terminal-never-retry enforcement as **executor policy** | Full Runtime Charter §24 |
| Attempt count / budget exhaustion transitions | Full Runtime Charter §24 / AIJob engine |
| SendExecution connector-side classification mutation | Outside RT-WP5 Lite; consume existing taxonomy labels only |

---

## 4. Runtime Visibility Boundary

### 4.1 What Lite owns

```text
CRM owns the Failure Metadata Foundation Lite vocabulary, classification
rules (metadata-only), logical metadata contract, state correlation to
RT-WP4 Lite, and audit-friendly representation.
```

### 4.2 What Lite does not own

```text
Connector owns outbound provider dispatch, adapter invocation, transport,
provider HTTP, and provider error execution.

Retry / recovery / queue / worker / scheduler / reservation remain deferred
and are not Lite surfaces.

AIJob engine fields (attemptCount, nextRetryAt, engine status transitions)
are not mutated by this Lite charter.
```

### 4.3 Visibility contract

| Visible | Not visible / forbidden |
| --- | --- |
| Category enum | Raw provider response bodies |
| Safe message | Credentials, tokens, API keys, secret material |
| Correlated foundation state | Worker/queue depth, retry schedule |
| Non-secret correlation references | C25 commercial brief contents as failure authority |

Any future attachment of Lite failure metadata to a concrete persistence field
requires Foundation Review allowlist ratification.

---

## 5. Audit Representation

### 5.1 Required properties

| Property | Requirement |
| --- | --- |
| Non-secret | No credentials, tokens, or raw provider secrets |
| Deterministic vocabulary | Category must be one of the eight closed values |
| Correlatable | Linkable to RT-WP4 Lite state outcome where claimed |
| Fail-closed | Illegal category / secret payload rejected |
| Non-executive | Representation must not schedule or imply automatic recovery |

### 5.2 Allowed audit content

- `failureCategory`
- optional safe class label
- optional safe message
- correlated foundation state (`FAILED` / `BLOCKED`)
- optional non-secret provenance / correlation reference
- optional `sourceLayer` and `recordedAt`

### 5.3 Forbidden audit content

- Secret material or credential values
- Retry schedule / `nextRetryAt` as Lite deliverable
- Provider HTTP traces / outbound call bodies
- C25 Opportunity / CommercialBrief decision narratives as failure authority
- Claims of INV-10 satisfaction

---

## 6. Security Boundary

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret in metadata / logs / fixtures | Failure payloads are non-secret only |
| No credential resolution | May reference credential reference ids only if already present; never resolve |
| No retry / recovery side effects | Metadata write must not enqueue work or mutate retry fields |
| ACL / Portal | Operator surfaces remain Portal-denied where applicable |
| Admin no-bypass | Future mutation guards must apply to all roles |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| No C25 audit rewrite | C25 owns its audit; Lite does not emit CommercialBrief human-review events |

Invariant posture preserved:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation; INV-10 remains DEFERRED)
```

---

## 7. Exclusions

| Forbidden surface | Reason |
| --- | --- |
| Retry / backoff / `nextRetryAt` / attempt budget | Full §24 / executor — excluded |
| Recovery / automatic re-dispatch | Failure execution system — excluded |
| Queue / worker / scheduler | Execution engine — excluded |
| Reservation / lease / concurrency claim | RT-WP6 deferred |
| Provider error execution / adapter / connector call / HTTP outbound | Connector-owned; C20-INV-03 |
| ProviderBinding mutation / credential handling | RT-WP2 ownership; consume only |
| AIJob engine lifecycle redesign / status executor | Not this Lite vocabulary |
| AIRequestLog outbound production / INV-08 exit | Deferred beyond Lite |
| SendExecution retry semantics changes | Outside RT-WP5 Lite |
| CompletionCapability enum change | ADR-C20-005 locked |
| C25 lifecycle / CommercialBrief / Opportunity / CRM sales authority | C25 WP2.2 NO GO |
| Secret resolution / token handling / provider authentication | Forbidden |
| Invariant registry status flips (incl. INV-10) | RT-WP7 / governance-status only |

```text
STOP conditions for this work package:
- Scope expansion beyond failure metadata
- C25 entry
- Runtime execution increase
- Retry / Queue / Worker introduction
- Provider / Connector modification
- Git failure under authorized commit steps
```

---

## 8. Test Requirements

When implementation is separately authorized, tests must prove failure-metadata
contracts **without** network I/O, connector invocation, or retry side effects:

| Category | Coverage |
| --- | --- |
| Contract | Exact eight-category vocabulary; metadata fields; non-secret representation |
| Classification | Known inputs map fail-closed; unknown category rejected |
| Correlation | Metadata correlates to RT-WP4 `FAILED`/`BLOCKED` correctly; no illegal state invention |
| Negative | Secret payload rejected; retry/queue/worker markers absent; `COMMERCIAL_BRIEF` / C25-driven classification forbidden |
| Isolation | No Jobs/worker/queue/retry/reservation/connector/HTTP markers in allowlist |
| Regression | RT-WP2, RT-WP3 Lite, and RT-WP4 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |

No Lite test may:

- perform provider HTTP
- resolve secrets
- assert retry scheduling
- claim INV-10 exit
- mutate AIJob engine retry fields as a Lite success criterion

---

## 9. Exit Criteria

### 9.1 Charter exit (this document)

Charter may be considered complete for independent ratification review when:

1. Scope is explicit (§1).
2. Failure metadata model is explicit (§2).
3. Failure categories are closed and non-executive (§3).
4. Runtime visibility boundary is explicit (§4).
5. Audit representation is explicit (§5).
6. Security boundary is explicit (§6).
7. Exclusions are explicit (§7).
8. Test requirements are explicit (§8).
9. Exit criteria are explicit (§9).
10. Implementation remains **NOT AUTHORIZED** until separate authorization +
    Foundation Review PASS.

### 9.2 Implementation exit (future; not claimed now)

Lite implementation may later claim foundation-complete only when:

1. Independent Plan Review and Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §1 only.
3. Eight categories + metadata contract proven; retry/executor absent.
4. No connector / HTTP / worker / retry / reservation / C25 coupling.
5. Independent Implementation Review PASS.
6. Separate commit/push/tag authorization obtained.

Full Runtime Charter §24 retry classification/executor and INV-10 activation
remain **out of Lite scope**.

---

## Authorization Boundary

```text
Charter status:
RATIFIED

RT-WP5 Lite Implementation:
NOT AUTHORIZED

Full RT-WP5 / Runtime Charter §24 Retry Executor:
NOT AUTHORIZED

Any runtime code:
NOT AUTHORIZED

RT-WP6–RT-WP8:
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
| RT-WP0 | EXITED |
| RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED |
| RT-WP3 | COMPLETED + TAGGED |
| RT-WP4 Lite | COMPLETED + TAGGED |
| RT-WP5 Lite Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP5 Lite Implementation | NOT AUTHORIZED |
| Full §24 Retry Executor | NOT AUTHORIZED |
| RT-WP6–RT-WP8 | NOT AUTHORIZED |
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
Phase3C20 RT-WP5 Charter Documents Commit and Push
```

---

## References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§13, §24 — full retry deferred)
2. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
4. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
6. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
7. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
8. `docs/adr/C20_INVARIANT_REGISTRY.md`
9. Live tags: `phase3c20-rt-wp4-implementation-completed`, `phase3c20-rt-wp3-implementation-completed`, `phase3c20-rt-wp2-implementation-completed`
10. Live HEAD at charter drafting: `8a1aa9341ed14cdae546c3bafbbb66b1c40f21a9`

---

*This charter is a planning document. It creates no production runtime change,
modifies no RT-WP2–WP4 implementation, stages no commit, and authorizes no
code. Failure Metadata Foundation Lite implementation begins only under a
separate, explicit authorization.*
