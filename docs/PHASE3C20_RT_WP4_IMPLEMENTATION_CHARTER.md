# Phase3C20 RT-WP4 Implementation Charter — Execution State Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | RT-WP4 Execution State Foundation Lite Charter (planning only) |
| Work package | RT-WP4 Lite — Execution State Foundation |
| Charter path | `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md` |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed` → `b167275757f7a404ff8b4c09f037a63610bce142`) |
| RT-WP3 Charter | RATIFIED (`phase3c20-rt-wp3-charter-ratified` → `12ec8a86ce3adc1a04f94b600f5926a301793eb7`) |
| RT-WP3 Implementation | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed` → `1fa8bf90ed34469046f5fc9d42149aac364836e7`) |
| Independent ratification review | RATIFIED (independent review PASS) |
| Execution mode | Charter authoring only — no runtime, metadata, entity, service, test, connector, or C25 change |
| Implementation authorization | **NOT AUTHORIZED** |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
This charter defines the minimal Execution State Foundation Lite planning
contract. It creates no code, modifies no runtime, authorizes no
implementation, and does not release RT-WP4 full cancel-reason work,
RT-WP5–RT-WP8, or C25.
```

---

## 1. Charter Path

| Item | Path / identity |
| --- | --- |
| This charter | `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md` |
| Governing runtime charter | `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` |
| Upstream Lite dispatch | RT-WP3 Dispatch Foundation Lite (completed + tagged) |
| Upstream binding policy | RT-WP2 ProviderBinding (completed + tagged; consume only) |

```text
Lite label: RT-WP4 Lite — Execution State Foundation

Full Runtime Charter §23 (Cancel-Reason Contract on AIJob) remains a
separate, deferred surface and is NOT authorized by this Lite charter.
```

---

## 2. Background and Motivation

RT-WP3 Lite delivers a references-only dispatch path:

```text
Request → Purpose → Capability → ProviderBinding → Execution Boundary → STOP
```

That path needs a **minimal, audit-friendly state vocabulary** so runtime-
visible objects can express whether a governed request is requested,
validating, ready for handoff, blocked by policy, completed at the foundation
boundary, or failed — **without** introducing an execution engine, worker,
queue, scheduler, retry, reservation, or provider call.

Motivation:

1. Make RT-WP3 boundary outcomes durable and reviewable as state, not only as
   ephemeral resolve traces.
2. Separate **policy/foundation state** from AIJob engine states
   (`QUEUED` / `RUNNING` / …) and from connector/provider runtime states.
3. Provide a stable contract for later WP surfaces without authorizing those
   surfaces now.

Non-motivation: this charter does **not** deliver cancel-reason fields,
AIJob transition ownership (Runtime Charter §23), retry executors, or
outbound dispatch.

---

## 3. Scope

RT-WP4 Lite covers exactly five surfaces:

| # | Allowed surface | Meaning |
| --- | --- | --- |
| 1 | Execution state vocabulary | Closed set of foundation states (see §5) |
| 2 | State transition policy definition | Allowed edges; fail-closed illegal transitions |
| 3 | Runtime-visible state contract | How state is represented for audit/visibility (logical contract) |
| 4 | State validation boundary | Reject unknown states and illegal transitions |
| 5 | Audit-friendly state representation | Non-secret state + provenance references only |

```text
Execution State Foundation Lite only.
Not an execution engine.
```

### 3.1 Preconditions

| Predecessor | Status | Lite dependency |
| --- | --- | --- |
| RT-WP0 | EXITED | Live contracts locked |
| RT-WP1 | EXITED | Capability/purpose direction locked |
| RT-WP2 | COMPLETED + TAGGED | ProviderBinding policy consumable; not modified |
| RT-WP3 Lite | COMPLETED + TAGGED | Dispatch boundary consumable; not redesigned |
| Four-value portfolio | Frozen | Unchanged |
| C20-INV-02 / C20-INV-03 | ACTIVE | Unchanged |
| C20-INV-04–13 | DEFERRED | No activation by this charter |

---

## 4. Non-Scope

| Forbidden surface | Reason |
| --- | --- |
| Jobs / worker / queue / scheduler | Execution engine — excluded |
| Retry / backoff / failure-metadata executor | RT-WP5 deferred |
| Reservation / lease / concurrency claim | RT-WP6 deferred |
| Provider execution / adapter / connector call / HTTP outbound | Connector-owned; C20-INV-03 |
| AIRequestLog outbound production / INV-08 exit | Deferred beyond Lite |
| Full RT-WP4 cancel-reason contract (Runtime Charter §23) | Separate deferred surface |
| AIJob engine status redesign (`QUEUED`/`RUNNING`/…) | Not this vocabulary |
| ProviderBinding mutation / credential handling | RT-WP2 ownership; consume only |
| CompletionCapability enum change | ADR-C20-005 locked |
| C25 lifecycle / CommercialBrief / Opportunity / CRM lifecycle authority | C25 WP2.2 NO GO |
| Secret resolution / token handling / provider authentication | Forbidden |
| Invariant registry status flips | RT-WP7 / governance-status only |

---

## 5. Execution State Model

### 5.1 Final Lite state set (justified)

| State | Meaning | Terminal? |
| --- | --- | --- |
| `REQUESTED` | Governed request accepted; validation not started | No |
| `VALIDATING` | Purpose / capability / binding / guards evaluation in progress | No |
| `READY` | Policy-eligible; references-only execution boundary available; **no connector invoke** | No |
| `BLOCKED` | Fail-closed policy/authorization block (e.g. missing binding, unregistered purpose, ACL denial) | **Yes** (Lite) |
| `COMPLETED` | Lite foundation path closed successfully after `READY` (boundary recorded for audit). Does **not** mean provider execution succeeded | **Yes** |
| `FAILED` | Terminal unsuccessful foundation outcome (invalid contract after acceptance, unrecoverable validation error) | **Yes** |

### 5.2 Justification

| Candidate | Kept? | Rationale |
| --- | --- | --- |
| `REQUESTED` | Yes | Distinct entry from validation; supports audit of acceptance |
| `VALIDATING` | Yes | Aligns with RT-WP3 resolve steps without implying worker/queue |
| `READY` | Yes | Explicit “boundary assembled / eligible for handoff” without provider call |
| `BLOCKED` | Yes | Separates governance blocks from processing `FAILED` for audit clarity |
| `COMPLETED` | Yes | Terminal success for **foundation Lite**, not provider completion |
| `FAILED` | Yes | Terminal unsuccessful foundation outcome |
| `QUEUED` / `RUNNING` / `RETRY_PENDING` | **No** | Worker/queue/retry engine states — forbidden |
| `CANCELLED` | **No** | Belongs to full cancel-reason contract (Runtime Charter §23) — deferred |
| `DISPATCHED` / `PROVIDER_*` | **No** | Connector/provider execution — forbidden |

```text
COMPLETED (Lite) ≠ provider execution completed.
READY ≠ connector called.
BLOCKED ≠ retry scheduled.
```

### 5.3 Capability portfolio lock (unchanged)

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

```text
COMMERCIAL_BRIEF is not a CompletionCapability.
CommercialBrief remains a purpose/business object / C25 domain artifact.
```

---

## 6. State Transition Rules

### 6.1 Allowed transitions (Lite)

```text
REQUESTED  → VALIDATING
VALIDATING → READY | BLOCKED | FAILED
READY      → COMPLETED | FAILED
```

| From | To | When |
| --- | --- | --- |
| `REQUESTED` | `VALIDATING` | Validation begins |
| `VALIDATING` | `READY` | Eligibility bound; boundary assembled (RT-WP3 Lite semantics) |
| `VALIDATING` | `BLOCKED` | Policy/authorization block (fail-closed) |
| `VALIDATING` | `FAILED` | Unrecoverable validation/contract failure |
| `READY` | `COMPLETED` | Foundation path closed for audit without outbound invoke |
| `READY` | `FAILED` | Unrecoverable error while closing foundation path (rare; no retry) |

### 6.2 Forbidden transitions (examples)

- Any transition into `QUEUED`, `RUNNING`, `RETRY_PENDING`, `CANCELLED`, or provider states
- `BLOCKED` → `READY` / `VALIDATING` without a **separately authorized** re-entry rule (Lite: `BLOCKED` is terminal)
- `COMPLETED` → any non-terminal state
- `FAILED` → any state
- Skipping `VALIDATING` from `REQUESTED` directly to `COMPLETED`
- Inferring state from C25 entity lifecycle or Opportunity stage

### 6.3 Validation boundary

| Rule | Behavior |
| --- | --- |
| Unknown state value | Reject fail-closed |
| Illegal edge | Reject fail-closed |
| Direct field mutation bypassing service/guard | Forbidden when implementation is later authorized |
| Secret-bearing state payloads | Forbidden |

---

## 7. Runtime Boundary

### 7.1 What Lite owns

```text
CRM owns the Execution State Foundation Lite vocabulary, transition policy,
validation boundary, and audit-friendly representation for foundation objects.
```

### 7.2 What Lite does not own

```text
Connector owns outbound provider dispatch, adapter invocation, transport, and
provider HTTP.

RT-WP3 owns Dispatch Foundation Lite resolve/guards/boundary assembly
(already completed). RT-WP4 Lite consumes boundary outcomes as state inputs;
it does not re-open RT-WP3 allowlists or redesign ProviderBinding.
```

### 7.3 Relationship to AIJob engine status

Existing AIJob statuses (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`,
`CANCELLED`) remain the AIJob **engine** vocabulary. RT-WP4 Lite defines a
**foundation state vocabulary** for governed dispatch-foundation visibility.
This charter does **not** authorize merging, replacing, or mutating AIJob
engine fields, nor cancel-reason fields (Runtime Charter §23).

Any future attachment of Lite state to a concrete persistence field requires
Foundation Review allowlist ratification.

---

## 8. Security Considerations

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret in state / logs / fixtures | State and provenance are non-secret only |
| No credential resolution | Boundary may carry `credentialReference` only |
| ACL / Portal | Operator surfaces remain Portal-denied where applicable |
| Admin no-bypass | Future mutation guards/save-options must apply to all roles |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| No C25 audit rewrite | C25 owns its audit; Lite does not emit AIRequestLog human-review events |

Invariant posture preserved:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation)
```

---

## 9. Interaction with RT-WP3

| Concern | Rule |
| --- | --- |
| Consume | RT-WP4 Lite consumes RT-WP3 Dispatch Boundary / resolve outcomes |
| Do not modify | RT-WP3 allowlisted Lite files are not redesigned by this charter |
| Mapping (logical) | `VALIDATING` ↔ resolve in progress; `READY` ↔ `BOUND` + boundary assembled; `BLOCKED`/`FAILED` ↔ guard/policy rejection classes |
| Stop line | State transitions must not invoke Connector or extend past the RT-WP3 stop line |

```text
RT-WP4 Lite adds state vocabulary around the RT-WP3 boundary.
It does not authorize crossing that boundary.
```

---

## 10. Interaction with RT-WP5 / WP6 / WP7 / WP8

| Work package | Interaction with RT-WP4 Lite |
| --- | --- |
| RT-WP5 (retry) | Deferred. Must not invent retry states in Lite vocabulary |
| RT-WP6 (reservation) | Deferred. Must not invent reservation/lease states |
| RT-WP7 (invariant activation / full guards) | Deferred except that Lite state validation remains fail-closed policy |
| RT-WP8 (freeze) | Deferred. No freeze claims |
| Full RT-WP4 cancel-reason (§23) | Deferred. `CANCELLED` / cancel-reason fields excluded from Lite |

Shared-file rule (Runtime Charter §18.1): any future shared touch to
`AIJobService.php` / `entityDefs/AIJob.json` requires primary-owner discipline
and is **out of this Lite charter** until separately authorized.

---

## 11. C25 Boundary

```text
C25 WP2.2 remains NO GO.
```

| Rule | Statement |
| --- | --- |
| CommercialBrief | Purpose/business / C25 domain artifact — not a capability; owns no foundation state authority |
| Capability | Four-value portfolio only; `COMMERCIAL_BRIEF` forbidden |
| Lifecycle | No CommercialBrief / Opportunity / sales CRM lifecycle authority in RT-WP4 Lite |
| State coupling | Lite states must not be driven by C25 entity status fields |

---

## 12. Test Strategy

When implementation is separately authorized, tests must prove state contracts
**without** network I/O or connector invocation:

| Category | Coverage |
| --- | --- |
| Contract | Exact six-state vocabulary; representation fields; non-secret provenance |
| Transition | Allowed edges succeed; illegal edges reject fail-closed |
| Negative | Unknown state; skip-path transitions; `COMMERCIAL_BRIEF` / C25-driven state forbidden |
| Isolation | No Jobs/worker/queue/retry/reservation/connector/HTTP markers in allowlist |
| Regression | RT-WP2 and RT-WP3 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |

No Lite test may perform provider HTTP, resolve secrets, or claim cancel-reason
/ INV-06 / INV-08 exit.

---

## 13. Exit Criteria

### 13.1 Charter exit (this document)

Charter may be considered complete for independent ratification review when:

1. Scope and non-scope are explicit (§3–§4).
2. Final six-state set is justified (§5).
3. Transition rules are fail-closed (§6).
4. Runtime, security, RT-WP3, later-WP, and C25 boundaries are explicit (§7–§11).
5. Test strategy and exit criteria are explicit (§12–§13).
6. Implementation remains **NOT AUTHORIZED** until separate authorization +
   Foundation Review PASS.

### 13.2 Implementation exit (future; not claimed now)

Lite implementation may later claim foundation-complete only when:

1. Independent Plan Review and Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §3 only.
3. Six states + transitions proven; forbidden engine states absent.
4. No connector / HTTP / worker / retry / reservation / C25 coupling.
5. Independent Implementation Review PASS.
6. Separate commit/push/tag authorization obtained.

Full Runtime Charter §23 cancel-reason / INV-06 exit remains **out of Lite
scope**.

---

## Authorization Boundary

```text
Charter status:
RATIFIED

RT-WP4 Lite Implementation:
NOT AUTHORIZED

Full RT-WP4 Cancel-Reason (§23):
NOT AUTHORIZED

Any runtime code:
NOT AUTHORIZED

RT-WP5–RT-WP8:
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
| RT-WP4 Lite Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP4 Lite Implementation | NOT AUTHORIZED |
| RT-WP5–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

---

## Final Decision

```text
RATIFIED — STATUS SYNCHRONIZED
```

Independent ratification review returned **PASS** / **RATIFIED**. No BLOCKER,
HIGH, or MEDIUM finding alters scope. Charter status is therefore synchronized
to RATIFIED. Implementation remains NOT AUTHORIZED.

```text
Next Task:
Phase3C20 RT-WP4 Charter Documents Commit and Push
```

---

## References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§6, §12, §18.1, §22, §23)
2. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_PLAN.md`
4. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
6. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
7. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
8. `docs/adr/C20_INVARIANT_REGISTRY.md`
9. Live tags: `phase3c20-rt-wp3-implementation-completed`, `phase3c20-rt-wp3-charter-ratified`, `phase3c20-rt-wp2-implementation-completed`
10. Live HEAD at charter drafting: `1fa8bf90ed34469046f5fc9d42149aac364836e7`

---

*This charter is a planning document. It creates no production runtime change,
modifies no RT-WP3 or ProviderBinding implementation, stages no commit, and
authorizes no code. Execution State Foundation Lite implementation begins only
under a separate, explicit authorization.*
