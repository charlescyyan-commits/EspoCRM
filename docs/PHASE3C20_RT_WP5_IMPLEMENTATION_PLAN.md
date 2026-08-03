# Phase3C20 RT-WP5 Implementation Plan — Failure Metadata Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | Implementation plan (planning only — no code, metadata, or test change) |
| Work package | RT-WP5 Lite — Failure Metadata Foundation |
| Plan path | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_PLAN.md` |
| Status | PLAN — READY FOR PLAN REVIEW |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed`) |
| RT-WP3 | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed`) |
| RT-WP4 | COMPLETED + TAGGED (`phase3c20-rt-wp4-implementation-completed` → `8a1aa9341ed14cdae546c3bafbbb66b1c40f21a9`) |
| RT-WP5 Lite Charter | RATIFIED (`a2e47aa7deed6d4f4b1762cde4f07d18445256e7`) |
| RT-WP5 Lite Implementation Authorization | **AUTHORIZED WITH CONDITIONS** (Failure Metadata Foundation only) |
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
| This plan | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_PLAN.md` |
| Governing charter | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md` |
| Authorization evidence | `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_AUTHORIZATION.md` |
| Runtime charter | `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` |
| Upstream state foundation | RT-WP4 Execution State Foundation Lite (completed + tagged) |
| Upstream dispatch / binding | RT-WP3 / RT-WP2 (completed + tagged; consume only) |

```text
Lite label: RT-WP5 Lite — Failure Metadata Foundation

Full Runtime Charter §24 Retry Classification and Executor remains
NOT AUTHORIZED.
```

---

## 2. Authorization Context

| Item | Status |
| --- | --- |
| RT-WP5 Lite Charter | RATIFIED |
| Independent Charter Review | PASS / RATIFIED |
| Implementation Authorization | AUTHORIZED WITH CONDITIONS |
| Implementation | NOT STARTED |
| Exact allowlist | Pending Foundation Review |

Authorized conditions (summary):

1. Failure vocabulary only (closed Lite set — exact values in §5).
2. Failure classification (metadata-only, fail-closed; non-executive).
3. Failure metadata contract (logical non-secret fields).
4. Audit-friendly representation.
5. Correlation with RT-WP4 Lite terminal states (`FAILED` / `BLOCKED`) only.

```text
Authorization does not finalize file allowlists or release commit/push/tag.
Authorization does not release retry, recovery, queue, worker, or §24.
```

---

## 3. Scope

This plan covers exactly five surfaces:

| # | Surface | Meaning |
| --- | --- | --- |
| 1 | Failure vocabulary | Closed foundation failure-code set (see §5) |
| 2 | Failure classification | Map foundation-visible inputs → vocabulary fail-closed |
| 3 | Failure metadata contract | Logical fields that record failure context without recovery |
| 4 | Audit-friendly representation | Non-secret, reviewable failure context |
| 5 | RT-WP4 state correlation | Relate metadata to `FAILED` / `BLOCKED` only |

```text
Failure Metadata Foundation Lite only.
Records failure metadata.
Does not execute recovery.
Not a retry engine.
```

### 3.1 Architecture boundary

```text
Consumes:  RT-WP4 Lite state foundation
Records:   failure metadata only
Does not:  execute recovery / retry / queue / worker / provider call
```

### 3.2 Scope-to-section traceability

| Scope item | Primary sections |
| --- | --- |
| Failure vocabulary | §5 |
| Failure classification | §6 |
| Data / metadata contract | §7 |
| Runtime boundary | §8 |
| Security | §9 |
| Tests / sequence / foundation / exit | §10–§13 |

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

## 4. Non-Scope

| Forbidden surface | Decision |
| --- | --- |
| Retry / backoff / retry count / retry policy / retry schedule / `nextRetryAt` | Excluded — full §24 |
| Recovery / automatic re-dispatch | Excluded |
| Queue / worker / scheduler | Excluded |
| Reservation / lease / concurrency | RT-WP6 deferred |
| Provider error execution / adapter / connector / HTTP outbound | Excluded |
| AIJob engine lifecycle / status mutation / attemptCount | Excluded |
| AIRequestLog outbound producer / INV-08 exit | Excluded |
| ProviderBinding mutation / credential handling | Consume only — do not modify |
| `CompletionCapability` enum change | Locked |
| C25 / Opportunity / sales CRM lifecycle | NO GO |
| Secret resolution / token / provider authentication | Forbidden |
| INV-10 activation / invariant registry flips | RT-WP7 / governance deferred |
| RT-WP8 freeze claims | Deferred |
| SendExecution retry semantics changes | Outside RT-WP5 Lite |

---

## 5. Failure Metadata Model

### 5.1 Exact Lite closed vocabulary (decided by this plan)

Lite records **foundation-visible** failure context. Because Lite excludes
provider error execution, the closed primary vocabulary is foundation failure
codes — not provider-transport taxonomy used as retry policy input.

| Failure code | Meaning | Typical RT-WP4 correlation | Implies retry? |
| --- | --- | --- | --- |
| `VALIDATION_FAILED` | Unrecoverable contract/validation failure after acceptance | `FAILED` | **No** |
| `POLICY_REJECTED` | Fail-closed policy/authorization rejection | `BLOCKED` | **No** |
| `BOUNDARY_REJECTED` | Dispatch/execution-boundary guard rejection (references-only path) | `BLOCKED` or `FAILED` (see §6) | **No** |
| `TIMEOUT_METADATA` | Timeout observed/recorded as metadata only (no schedule) | `FAILED` | **No** |
| `UNKNOWN_FAILURE` | Fail-closed fallback when no safer code applies | `FAILED` | **No** |

```text
Exact Lite vocabulary (5 values):
VALIDATION_FAILED
POLICY_REJECTED
BOUNDARY_REJECTED
TIMEOUT_METADATA
UNKNOWN_FAILURE
```

### 5.2 Justification vs charter taxonomy labels

Charter §3 referenced the eight C20 taxonomy labels (`NETWORK`, `PROVIDER`,
`AUTH`, `RATE_LIMIT`, `VALIDATION`, `UNKNOWN`, `QUOTA`, `CONTENT_FILTER`) as
audit classification vocabulary. This plan **specializes** the Lite primary
closed set to the five foundation codes above because:

1. Lite has no provider error execution — transport/provider labels invite §24
   retry-eligibility confusion.
2. RT-WP4 correlation needs foundation-meaningful codes
   (`POLICY_REJECTED` ↔ `BLOCKED`, `VALIDATION_FAILED` ↔ `FAILED`).
3. Existing AIRequestLog / SendExecution eight-value taxonomy remains unchanged
   and outside Lite ownership.
4. Full Runtime Charter §24 retains taxonomy-as-retry-policy ownership.

Optional secondary audit annotation using the eight C20 taxonomy labels is
**not required** for Lite exit and is deferred unless Foundation Review
explicitly allowlists a non-executive optional field with zero retry side
effects.

### 5.3 Recording rules

```text
Failure metadata records context.
It does not schedule recovery.
It does not transition AIJob engine status.
It does not invoke Connector.
It does not invent RETRY_PENDING.
```

| Rule | Behavior |
| --- | --- |
| Unknown failure code | Reject fail-closed |
| Secret-bearing payload | Reject fail-closed |
| Metadata without allowed RT-WP4 correlation when claiming terminal failure context | Reject fail-closed |
| Metadata write that triggers retry / queue / worker | Forbidden |
| Infer code from C25 / Opportunity / sales fields | Forbidden |

---

## 6. Failure Classification

### 6.1 Classification principles

1. Codes are **labels for audit**, not execution instructions.
2. Classification is fail-closed: unknown input → reject (or map only to
   `UNKNOWN_FAILURE` where an approved mapping exists); no open-string codes.
3. Provider transport details remain connector-owned; Lite must not call
   providers to obtain classification.
4. No failure code authorizes `FAILED → QUEUED`, `nextRetryAt` mutation,
   attempt increment, worker enqueue, or recovery.

### 6.2 Input → code mapping (logical)

| Foundation-visible input class | Lite failure code | Correlated state |
| --- | --- | --- |
| Contract/schema/required-field validation failure | `VALIDATION_FAILED` | `FAILED` |
| Missing binding / unregistered purpose / ACL / policy block | `POLICY_REJECTED` | `BLOCKED` |
| Boundary assembly / guard rejection at RT-WP3 stop line | `BOUNDARY_REJECTED` | `BLOCKED` (policy-class) or `FAILED` (unrecoverable boundary contract) — exact edge chosen fail-closed by service rules; must not open retry |
| Timeout recorded without scheduling retry | `TIMEOUT_METADATA` | `FAILED` |
| Unclassified / ambiguous after fail-closed evaluation | `UNKNOWN_FAILURE` | `FAILED` |

### 6.3 Explicitly deferred classification behaviors

| Deferred behavior | Owner |
| --- | --- |
| Retryable set `{NETWORK, PROVIDER, RATE_LIMIT}` as executor policy | Full §24 |
| Terminal-never-retry executor enforcement | Full §24 |
| Attempt count / budget exhaustion transitions | Full §24 / AIJob engine |
| Provider error execution classification from live HTTP | Connector — forbidden in Lite |

---

## 7. Data Contract

### 7.1 Logical failure metadata representation (minimum)

| Field | Required | Rule | Secret? |
| --- | --- | --- | --- |
| `failureCode` | Yes (when failure metadata recorded) | Exactly one of the five Lite codes | No |
| `correlatedFoundationState` | Yes (when correlated) | `FAILED` or `BLOCKED` only | No |
| `failureMessageSafe` | Optional | Operator-safe summary; no raw provider/body secrets | No |
| `correlationReference` | Optional | Non-secret request/boundary/provenance id | No |
| `sourceLayer` | Optional | `FOUNDATION` \| `POLICY` \| `VALIDATION` only | No |
| `recordedAt` | Optional | Server-owned timestamp when persistence authorized | No |

### 7.2 Forbidden payload contents

- Secrets, tokens, credentials, authorization headers
- Retry count / retry policy / retry schedule / `nextRetryAt` / attempt budget
- Queue / worker / scheduler / reservation control fields
- Provider SDK / transport handles / HTTP bodies
- C25 CommercialBrief / Opportunity mutation instructions
- AIJob engine status transition commands

### 7.3 Persistence form

Persistence attachment (in-memory service contract vs entity field vs dedicated
record) is **not finalized** here. Foundation Review must choose the exact form
and allowlist. Until then, this plan specifies the logical contract only.

### 7.4 RT-WP4 correlation contract

| RT-WP4 state | Failure metadata |
| --- | --- |
| `FAILED` | May carry `VALIDATION_FAILED`, `BOUNDARY_REJECTED`, `TIMEOUT_METADATA`, or `UNKNOWN_FAILURE` |
| `BLOCKED` | May carry `POLICY_REJECTED` or `BOUNDARY_REJECTED` |
| `REQUESTED` / `VALIDATING` / `READY` / `COMPLETED` | No terminal failure metadata required by Lite |

```text
Consume RT-WP4 vocabulary; do not redesign it.
Do not reopen COMPLETED via failure metadata.
```

---

## 8. Runtime Boundary

### 8.1 Consume RT-WP4; do not expand execution

```text
Request
  ↓
RT-WP3 Lite Dispatch Boundary (references only)
  ↓
RT-WP4 Lite State Foundation
  ↓
RT-WP5 Lite Failure Metadata   ← this plan (record only)
  ↓
STOP (no connector / jobs / queue / retry / recovery)
```

| Owned by RT-WP5 Lite | Not owned |
| --- | --- |
| Vocabulary, classification, metadata contract, audit representation, RT-WP4 correlation | Provider HTTP, connector invoke, adapters |
| Fail-closed validation of codes / payloads | Jobs / workers / scheduler |
| Non-executive recording of failure context | Retry / recovery / reservation / §24 executor |

### 8.2 Do not modify

- RT-WP4 Lite allowlisted foundation-state files (except if Foundation later
  ratifies a **minimal, separately justified** correlation call-site — default
  preference: dedicated RT-WP5 Lite classes consuming RT-WP4 state values only)
- RT-WP3 Lite dispatch files
- ProviderBinding policy surfaces
- `CompletionCapability` enum / connector portfolio
- AIJob engine retry fields / status executor
- C25 surfaces

### 8.3 AIJob engine vocabulary

Existing AIJob engine statuses and retry fields (`attemptCount`, `nextRetryAt`,
`failureCategory` on AIJob) remain separate. This plan does **not** authorize
mutating AIJob engine lifecycle or implementing §24 retry executor behavior.

---

## 9. Security Considerations

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret in metadata/logs/fixtures | Non-secret representation only |
| No credential resolution | Never resolve tokens/secrets; references only if already present |
| No retry / recovery side effects | Metadata write must not enqueue work or mutate retry fields |
| ACL / Portal | Operator surfaces Portal-denied where applicable |
| Admin no-bypass | Future metadata mutations must use guarded/service-owned paths |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| No C25 audit rewrite | Do not emit CommercialBrief human-review events |

Invariant posture:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation; INV-10 remains DEFERRED)
```

---

## 10. Test Strategy

When Foundation Review authorizes code, tests must prove contracts **without**
network I/O, connector invocation, or retry side effects:

| Category | Coverage |
| --- | --- |
| Contract | Exact five-code vocabulary; data-contract fields; non-secret representation |
| Classification | Known inputs map fail-closed; unknown code rejected |
| Correlation | Metadata correlates only to `FAILED`/`BLOCKED`; illegal state invent rejected |
| Negative | Secret payload rejected; retry/queue/worker markers absent; `COMMERCIAL_BRIEF` / C25-driven classification forbidden |
| Isolation | No Jobs/worker/queue/retry/reservation/connector/HTTP/C25 markers in allowlist |
| Regression | RT-WP2 + RT-WP3 Lite + RT-WP4 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |

No Lite test may:

- perform provider HTTP
- resolve secrets
- assert retry scheduling / retry count / backoff
- mutate AIJob engine retry fields as a success criterion
- claim INV-10 / §24 exit

---

## 11. Implementation Sequence

```text
1. Independent Plan Review PASS
2. Foundation Review PASS (exact allowlist + persistence form)
3. Implement vocabulary constants + validation + metadata service contract
4. Wire consume-only correlation to RT-WP4 states (if allowlisted)
5. Add contract / classification / correlation / isolation / regression tests
6. Independent Implementation Review
7. Separately authorized commit / push / tag (if any)
```

Proposed **candidates only** (not finalized allowlist):

| Candidate | Intended role | Condition |
| --- | --- | --- |
| `Services/AIFailureMetadata.php` (or Foundation-named equivalent) | Closed five-code vocabulary constants | Exact five values only; no retry enums |
| `Services/AIFailureMetadataService.php` | Record/validate metadata; RT-WP4 correlation | No connector/Jobs/retry; no ProviderBinding mutation |
| `Services/AIFailureMetadataGuard.php` (or equivalent) | Reject unknown codes / illegal correlation / secret-shaped payloads | Fail-closed |
| `crm-extension/tests/test_phase3c20_rt_wp5_failure_metadata.py` | Contract / classification / correlation / isolation / regression | No network |

```text
Exact allowlist ratification belongs to Foundation Review.
```

Explicitly excluded candidates: `Jobs/*`, outbound `Api/*`, connector sources,
`ProviderBinding*`, `CompletionCapability` / connector enum files, C25 files,
AIRequestLog outbound producer, AIJob retry executor / `nextRetryAt` writers,
SendExecution retry mutation packs.

---

## 12. Foundation Review Requirements

Foundation Review must decide and ratify before code:

1. Exact file allowlist (necessary CRM service/DTO/guard/test paths only).
2. Persistence form (logical-only vs entity field vs dedicated record).
3. Whether any **minimal** RT-WP4 call-site is required, or RT-WP5 remains
   side-by-side consume-only.
4. Confirmation that secondary eight-value taxonomy annotation is excluded or
   explicitly allowlisted as non-executive optional metadata only.
5. ACL/Portal posture for any runtime-visible surface.
6. Confirmation that §24 retry executor / AIJob engine merge remains excluded.
7. Security rules (no secrets; no credential resolution; no HTTP).
8. Test evidence requirements matching §10.
9. Invariant confirmation: INV-02/03 ACTIVE; INV-04–13 DEFERRED.

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

1. Five Lite surfaces are specified (§3).
2. Exact failure vocabulary is decided and closed (§5).
3. Classification is non-executive and fail-closed (§6).
4. Data contract + RT-WP4 correlation are explicit (§7).
5. Forbidden surfaces are complete (§4).
6. Security / invariants / C25 / capability locks are explicit (§3.3, §9).
7. File paths remain **candidates only** (§11).
8. Implementation remains gated on Plan Review + Foundation Review.
9. Commit / push / tag unauthorized by this plan.

### 13.2 Lite implementation exit (future; not claimed now)

1. Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §3 only.
3. Five-code vocabulary + metadata contract proven; retry/executor absent.
4. No connector / HTTP / worker / retry / reservation / C25 coupling.
5. RT-WP2/RT-WP3/RT-WP4 regression green; INV posture unchanged.
6. Independent Implementation Review PASS.
7. Separate commit/push/tag authorization obtained.

Full §24 retry classification/executor and INV-10 activation remain
**out of Lite scope**.

---

## Authorization Boundary (plan)

```text
RT-WP5 Lite Charter:
RATIFIED

RT-WP5 Lite Implementation:
AUTHORIZED WITH CONDITIONS (Failure Metadata Foundation only)

Exact file allowlist:
NOT FINALIZED

Any runtime code:
NOT STARTED — gated on Plan Review + Foundation Review

Full RT-WP5 Retry Executor (§24):
NOT AUTHORIZED

RT-WP6–RT-WP8:
NOT AUTHORIZED

C25 WP2.2:
NO GO

Commit / push / tag:
NOT AUTHORIZED by this plan
```

---

## Final Decision

```text
READY FOR PLAN REVIEW
```

Rationale: plan is internally consistent with the ratified RT-WP5 Lite Charter,
AUTHORIZED WITH CONDITIONS boundary, RT-WP4 consume-only correlation model,
four-value portfolio lock, and ACTIVE INV-02/03 with deferred INV-04–13. Exact
Lite vocabulary is decided as five foundation failure codes. No retry,
recovery, queue, worker, provider execution, or C25 expansion is introduced.

```text
Next Task:
Phase3C20 RT-WP5 Implementation Plan Independent Review
```

---

## References

1. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md` (RATIFIED)
2. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_AUTHORIZATION.md` (AUTHORIZED WITH CONDITIONS)
3. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§42 sync; §24 deferred)
4. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md`
5. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_PLAN.md`
6. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
7. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
8. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
9. `docs/adr/C20_INVARIANT_REGISTRY.md`
10. Live tags: `phase3c20-rt-wp4-implementation-completed`, `phase3c20-rt-wp3-implementation-completed`
11. Live HEAD at plan drafting: `a2e47aa7deed6d4f4b1762cde4f07d18445256e7`

---

*This plan is a planning document. It creates no production runtime change,
modifies no RT-WP2–WP4 implementation, stages no commit, and authorizes no
code. Exact file allowlist belongs to Foundation Review.*
