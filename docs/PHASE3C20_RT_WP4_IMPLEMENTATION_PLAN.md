# Phase3C20 RT-WP4 Implementation Plan — Execution State Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | Implementation plan (planning only — no code, metadata, or test change) |
| Work package | RT-WP4 Lite — Execution State Foundation |
| Plan path | `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_PLAN.md` |
| Status | PLAN — READY FOR IMPLEMENTATION PLAN REVIEW |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed` → `b167275757f7a404ff8b4c09f037a63610bce142`) |
| RT-WP3 | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed` → `1fa8bf90ed34469046f5fc9d42149aac364836e7`) |
| RT-WP4 Lite Charter | RATIFIED + TAGGED (`phase3c20-rt-wp4-charter-ratified` → `b74e5d01d6f4d799a79945d38580ee8c47bd4a24`) |
| RT-WP4 Lite Implementation Authorization | **AUTHORIZED WITH CONDITIONS** (Lite / Foundation only) |
| Foundation Review | MANDATORY PRE-IMPLEMENTATION GATE — NOT YET RUN |
| Exact file allowlist | **NOT FINALIZED** by this plan — Foundation Review owns ratification |
| Commit / push / tag | **NOT AUTHORIZED** by this plan |
| C25 WP2.2 | NO GO |

```text
This plan is a planning document. It creates no production file, modifies no
existing runtime file, stages no change, and authorizes no code.
Implementation begins only after Independent Plan Review PASS and Foundation
Review PASS, and only within the Lite authorization boundary.
```

---

## 1. Plan Path

| Item | Path / identity |
| --- | --- |
| This plan | `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_PLAN.md` |
| Governing charter | `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md` |
| Runtime charter | `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` |
| Upstream dispatch Lite | RT-WP3 Dispatch Foundation Lite (completed + tagged) |
| Upstream binding policy | RT-WP2 ProviderBinding (completed + tagged; consume only) |

```text
Lite label: RT-WP4 Lite — Execution State Foundation

Full Runtime Charter §23 Cancel-Reason Contract remains NOT AUTHORIZED.
```

---

## 2. Authorization Context

| Item | Status |
| --- | --- |
| RT-WP4 Lite Charter | RATIFIED + TAGGED |
| Independent Charter Review | PASS / RATIFIED |
| Implementation Authorization | AUTHORIZED WITH CONDITIONS |
| Implementation | NOT STARTED |
| Exact allowlist | Pending Foundation Review |

Authorized conditions (summary):

1. State vocabulary only (six states).
2. Transition policy fail-closed.
3. Runtime-visible state contract (no execution authority).
4. Validation boundary for invalid state / transition / forbidden mutation.
5. Audit-friendly non-secret representation.
6. Consume RT-WP3 Lite Dispatch Boundary outcomes for state tracking only.

```text
Authorization does not finalize file allowlists or release commit/push/tag.
```

---

## 3. Scope

This plan covers exactly five surfaces:

| # | Surface | Meaning |
| --- | --- | --- |
| 1 | Execution state vocabulary | Closed set: `REQUESTED`, `VALIDATING`, `READY`, `BLOCKED`, `COMPLETED`, `FAILED` |
| 2 | Transition policy | Allowed edges only; illegal edges reject fail-closed |
| 3 | Runtime-visible state contract | How foundation state is represented for visibility/audit |
| 4 | State validation boundary | Reject invalid state, invalid transition, forbidden mutation |
| 5 | Audit-friendly representation | Non-secret state + provenance references only |

```text
Execution State Foundation Lite only.
Not an execution engine.
```

### 3.1 Scope-to-section traceability

| Scope item | Primary sections |
| --- | --- |
| State vocabulary | §5 |
| Transition policy | §6 |
| Runtime-visible contract / data contract | §7, §8 |
| Validation boundary | §5, §6, §8 |
| Audit representation | §8, §9 |
| Tests / sequence / foundation / exit | §10–§13 |

---

## 4. Non-Scope

| Forbidden surface | Decision |
| --- | --- |
| Jobs / workers / queue / scheduler | Excluded |
| Retry / backoff / failure-metadata executor | RT-WP5 deferred |
| Reservation / lease / concurrency | RT-WP6 deferred |
| Provider execution / adapter / connector / HTTP outbound | Excluded |
| AIRequestLog outbound producer / INV-08 exit | Excluded |
| Full cancel-reason / `CANCELLED` (Runtime Charter §23) | Excluded |
| AIJob engine status redesign (`QUEUED`/`RUNNING`/…) | Excluded |
| ProviderBinding mutation / credential handling | Consume only — do not modify |
| `CompletionCapability` enum change | Locked |
| C25 / Opportunity / sales CRM lifecycle | NO GO |
| Secret resolution / token / provider authentication | Forbidden |
| Invariant registry flips | RT-WP7 deferred |
| RT-WP8 freeze claims | Deferred |

---

## 5. State Model Design

### 5.1 Closed vocabulary

| State | Meaning | Terminal? |
| --- | --- | --- |
| `REQUESTED` | Governed request accepted; validation not started | No |
| `VALIDATING` | Purpose / capability / binding / guards evaluation in progress | No |
| `READY` | Policy-eligible; references-only execution boundary available; no connector invoke | No |
| `BLOCKED` | Fail-closed policy/authorization block | **Yes** (Lite) |
| `COMPLETED` | Lite foundation path closed after `READY` for audit; **not** provider success | **Yes** |
| `FAILED` | Terminal unsuccessful foundation outcome | **Yes** |

```text
COMPLETED (Lite) ≠ provider execution completed.
READY ≠ connector called.
BLOCKED ≠ retry scheduled.
```

### 5.2 Capability portfolio lock (unchanged)

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

```text
COMMERCIAL_BRIEF is not a CompletionCapability.
```

### 5.3 Mapping to RT-WP3 Lite outcomes (logical)

| RT-WP3 Lite signal | Typical Lite state effect |
| --- | --- |
| Resolve started | `REQUESTED` → `VALIDATING` |
| `BOUND` + boundary assembled | `VALIDATING` → `READY` |
| Guard/policy block (missing binding, unregistered purpose, ACL, etc.) | `VALIDATING` → `BLOCKED` |
| Unrecoverable contract/validation failure | `VALIDATING` → `FAILED` |
| Foundation path closed without outbound | `READY` → `COMPLETED` |

State tracking consumes boundary/eligibility outcomes. It does not re-implement
RT-WP3 resolve, redesign ProviderBinding, or cross the RT-WP3 stop line.

---

## 6. Transition Matrix

### 6.1 Allowed edges

```text
REQUESTED  → VALIDATING
VALIDATING → READY | BLOCKED | FAILED
READY      → COMPLETED | FAILED
```

| From | To | Gate |
| --- | --- | --- |
| `REQUESTED` | `VALIDATING` | Validation begins |
| `VALIDATING` | `READY` | Eligibility bound; boundary present (references only) |
| `VALIDATING` | `BLOCKED` | Policy/authorization block |
| `VALIDATING` | `FAILED` | Unrecoverable validation/contract failure |
| `READY` | `COMPLETED` | Foundation close for audit; no outbound invoke |
| `READY` | `FAILED` | Unrecoverable close-path error (no retry) |

### 6.2 Fail-closed illegal transitions (non-exhaustive)

| Illegal pattern | Behavior |
| --- | --- |
| Unknown state value | Reject |
| `REQUESTED` → `COMPLETED` (skip `VALIDATING`) | Reject |
| `BLOCKED` → any state (Lite) | Reject (terminal) |
| `COMPLETED` / `FAILED` → any state | Reject |
| Transition to `QUEUED` / `RUNNING` / `RETRY_PENDING` / `CANCELLED` / provider states | Reject |
| State driven by C25 / Opportunity / sales lifecycle | Reject |
| Direct mutation bypassing validated transition API/guard (when implemented) | Reject |

---

## 7. Runtime Integration Boundary

### 7.1 Consume RT-WP3; do not expand execution

```text
Request
  ↓
Validation (RT-WP3 Lite)
  ↓
Execution Boundary (references only)
  ↓
State tracking (RT-WP4 Lite)   ← this plan
  ↓
STOP (no connector / jobs / queue)
```

| Owned by RT-WP4 Lite | Not owned |
| --- | --- |
| Vocabulary, transitions, validation, audit representation | Provider HTTP, connector invoke, adapters |
| Mapping boundary outcomes → state | Jobs/workers/scheduler |
| Fail-closed transition enforcement | Retry / reservation / cancel-reason |

### 7.2 Do not modify

- RT-WP3 Lite allowlisted dispatch files (except if Foundation later ratifies a
  **minimal, separately justified** call-site that only records state — default
  preference: dedicated RT-WP4 Lite module/classes without rewriting RT-WP3)
- ProviderBinding policy surfaces
- `CompletionCapability` enum / connector portfolio
- C25 surfaces

### 7.3 AIJob engine vocabulary

Existing AIJob engine statuses remain separate. This plan does **not** authorize
merging Lite foundation states into AIJob engine fields or §23 cancel-reason.

---

## 8. Data Contract

### 8.1 Runtime-visible representation (logical)

Minimum non-secret fields:

| Field | Rule |
| --- | --- |
| `foundationState` | Exactly one of the six Lite states |
| `requestIdentity` | Correlation reference (non-secret) |
| `previousState` | Optional; for audit of last legal edge |
| `transitionReasonCode` | Bounded non-secret reason class (policy/validation/close) |
| `provenanceReference` | Actor/policy-version references only |
| `boundaryReference` | Optional reference to RT-WP3 boundary identity (no secrets) |
| `updatedAt` | Server-owned timestamp when persistence is authorized |

### 8.2 Forbidden payload contents

- Secrets, tokens, credentials, authorization headers
- Provider SDK / transport handles
- Queue/worker/retry/reservation control fields
- C25 CommercialBrief mutation instructions
- Provider execution results / HTTP bodies

### 8.3 Persistence form

Persistence attachment (entity field vs dedicated record vs in-memory service
contract for tests) is **not finalized** here. Foundation Review must choose
the exact form and allowlist. Until then, the plan specifies the logical
contract only.

---

## 9. Security Considerations

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret in state/logs/fixtures | Non-secret representation only |
| No credential resolution | May reference `credentialReference` only if carried from RT-WP3 boundary |
| ACL / Portal | Operator surfaces Portal-denied where applicable |
| Admin no-bypass | Future transition mutations must use guarded/service-owned paths |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| No C25 audit rewrite | Do not emit AIRequestLog human-review events |

Invariant posture:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation)
```

---

## 10. Test Strategy

When Foundation Review authorizes code, tests must prove contracts **without**
network I/O or connector invocation:

| Category | Coverage |
| --- | --- |
| Contract | Exact six-state vocabulary; data-contract fields; non-secret provenance |
| Transition | All allowed edges; matrix completeness |
| Negative | Invalid state; illegal transition; forbidden mutation; skip-path; engine states (`QUEUED`/`RUNNING`/…) rejected |
| Isolation | No Jobs/worker/queue/retry/reservation/connector/HTTP/C25 markers in allowlist |
| Regression | RT-WP2 + RT-WP3 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |
| Boundary | State updates consume RT-WP3 outcomes only; no connector call sites |

No Lite test may resolve secrets, invoke Connector, or claim §23 / INV-06 /
INV-08 exit.

---

## 11. Implementation Sequence

```text
1. Independent Plan Review PASS
2. Foundation Review PASS (exact allowlist + persistence form)
3. Implement vocabulary + transition validator + data contract
4. Wire consume-only mapping from RT-WP3 boundary outcomes (if allowlisted)
5. Add contract / transition / isolation / regression tests
6. Independent Implementation Review
7. Separately authorized commit / push / tag (if any)
```

Proposed **candidates only** (not finalized allowlist):

| Candidate | Intended role | Condition |
| --- | --- | --- |
| `Services/AIFoundationStateService.php` (or Foundation-named equivalent) | Transition API; validation; audit representation | No connector/Jobs; no ProviderBinding mutation |
| `Services/AIFoundationState.php` (enum/constants DTO) | Closed six-state vocabulary | Exact six values only |
| `Services/AIFoundationStateTransitionGuard.php` (or equivalent) | Reject illegal edges / forbidden mutation | Fail-closed |
| `crm-extension/tests/test_phase3c20_rt_wp4_foundation_state.py` | Contract / transition / isolation / regression | No network |

```text
Exact allowlist ratification belongs to Foundation Review.
```

Explicitly excluded candidates: `Jobs/*`, outbound `Api/*`, connector sources,
`ProviderBinding*`, `CompletionCapability` / connector enum files, C25 files,
AIRequestLog outbound producer, cancel-reason AIJob field packs.

---

## 12. Foundation Review Requirements

Foundation Review must decide and ratify before code:

1. Exact file allowlist (necessary CRM service/DTO/guard/test paths only).
2. Persistence form (logical-only vs entity field vs dedicated record).
3. Whether any **minimal** RT-WP3 call-site is required, or RT-WP4 remains
   side-by-side consume-only.
4. Transition reason-code bounded set (non-secret).
5. ACL/Portal posture for any runtime-visible surface.
6. Confirmation that §23 cancel-reason / AIJob engine merge remains excluded.
7. Test evidence requirements matching §10.

Entry to implementation:

```text
AUTHORIZED WITH CONDITIONS
+ Plan Review PASS
+ Foundation Review PASS (exact allowlist)
```

---

## 13. Exit Criteria

### 13.1 Plan exit (this document)

Complete for Independent Plan Review when:

1. Five Lite surfaces are specified.
2. Six states + transition matrix are explicit and fail-closed.
3. Forbidden surfaces are complete.
4. Security / invariants / C25 / capability locks are explicit.
5. File paths remain **candidates only**.
6. Implementation remains gated on Plan Review + Foundation Review.
7. Commit / push / tag unauthorized by this plan.

### 13.2 Lite implementation exit (future; not claimed now)

1. Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §3 only.
3. Transition matrix proven; engine/forbidden states absent.
4. No connector / HTTP / worker / retry / reservation / C25 coupling.
5. RT-WP2/RT-WP3 regression green; INV posture unchanged.
6. Independent Implementation Review PASS.
7. Separate commit/push/tag authorization obtained.

Full §23 cancel-reason / INV-06 exit remains **out of Lite scope**.

---

## Authorization Boundary (plan)

```text
RT-WP4 Lite Charter:
RATIFIED + TAGGED

RT-WP4 Lite Implementation:
AUTHORIZED WITH CONDITIONS (Lite only)

Exact file allowlist:
NOT FINALIZED

Any runtime code:
NOT STARTED — gated on Plan Review + Foundation Review

Full RT-WP4 Cancel-Reason (§23):
NOT AUTHORIZED

RT-WP5–RT-WP8:
NOT AUTHORIZED

C25 WP2.2:
NO GO

Commit / push / tag:
NOT AUTHORIZED by this plan
```

---

## Final Decision

```text
READY FOR IMPLEMENTATION PLAN REVIEW
```

Rationale: plan is internally consistent with the ratified RT-WP4 Lite Charter,
AUTHORIZED WITH CONDITIONS boundary, RT-WP3 stop-at-boundary consume model,
four-value portfolio lock, and ACTIVE INV-02/03 with deferred INV-04–13. No
execution-engine expansion is introduced. No BLOCKER condition exists in this
planning document.

```text
Next Task:
Phase3C20 RT-WP4 Implementation Plan Independent Review
```

---

## References

1. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md` (RATIFIED)
2. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§41 sync; §23 deferred)
3. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_PLAN.md`
4. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
6. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
7. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
8. `docs/adr/C20_INVARIANT_REGISTRY.md`
9. Live tags: `phase3c20-rt-wp4-charter-ratified`, `phase3c20-rt-wp3-implementation-completed`
10. Live HEAD at plan drafting: `b74e5d01d6f4d799a79945d38580ee8c47bd4a24`

---

*This plan is a planning document. It creates no production runtime change,
modifies no RT-WP3 or ProviderBinding implementation, stages no commit, and
authorizes no code. Exact file allowlist belongs to Foundation Review.*
