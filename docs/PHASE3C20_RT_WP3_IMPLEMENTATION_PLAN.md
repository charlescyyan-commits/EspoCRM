# Phase3C20 RT-WP3 Implementation Plan — Dispatch Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | Implementation plan (planning only — no code, metadata, or test change) |
| Work package | RT-WP3 — Controlled Dispatch Foundation Lite + Runtime Guards Lite |
| Status | PLAN — READY FOR IMPLEMENTATION PLAN REVIEW |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed` → `b167275757f7a404ff8b4c09f037a63610bce142`) |
| RT-WP3 Charter | RATIFIED (`phase3c20-rt-wp3-charter-ratified` → `12ec8a86ce3adc1a04f94b600f5926a301793eb7`) |
| RT-WP3 Implementation Authorization | **AUTHORIZED WITH CONDITIONS** (Lite / Foundation only) |
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

## 1. Scope

### 1.1 Authorized Lite scope

This plan covers exactly seven surfaces. Nothing outside these seven is
planned:

| # | Surface | Meaning |
| --- | --- | --- |
| 1 | Dispatch Request Contract | Policy request identity + references; no execution |
| 2 | Purpose Validation | Registered-purpose gate; fail-closed; no inference |
| 3 | Capability Resolution | Four-value portfolio only; reject `COMMERCIAL_BRIEF` |
| 4 | ProviderBinding Consumption | Read/lookup/validate RT-WP2 policy only |
| 5 | Eligibility Validation | Policy classification only; no job/queue/retry state |
| 6 | Execution Boundary Assembly | References-only handoff object; stop before invoke |
| 7 | Runtime Guards Lite | Reject invalid capability, `COMMERCIAL_BRIEF`, missing binding, secret-shaped input |

```text
Dispatch Foundation Lite + Runtime Guards Lite only.
```

### 1.2 Explicitly deferred (do not design)

| Surface | Decision |
| --- | --- |
| RT-WP4 execution state / cancel-reason | Deferred |
| RT-WP5 failure metadata / retry | Deferred |
| RT-WP6 reservation | Deferred |
| RT-WP7 full runtime guard / invariant activation system | Deferred (Lite guards only) |
| RT-WP8 freeze | Deferred |
| AIRequestLog outbound producer / exactly-once log exit | Deferred |
| Jobs worker (`AIDispatchWorker`) | Deferred / excluded |
| API outbound execution path | Deferred / excluded |
| Connector outbound dispatch / adapter / HTTP | Deferred / excluded |

### 1.3 Scope-to-section traceability

| Scope item | Primary sections |
| --- | --- |
| Dispatch Request Contract | §3, §4 |
| Purpose Validation | §3, §4 |
| Capability Resolution | §3, §4 |
| ProviderBinding Consumption | §5 |
| Eligibility Validation | §4, §5 |
| Execution Boundary Assembly | §3, §4 |
| Runtime Guards Lite | §4, §6, §7 |
| Security / forbidden | §6, §7 |
| File candidates (non-final) | §8 |
| Tests / exit | §9, §10 |

---

## 2. Architecture

### 2.1 Position in the frozen chain

```text
CRM policy
→ authorized ProviderBinding set
→ CapabilityRegistry eligibility resolution
→ CRM governed dispatch orchestration   ← RT-WP3 Lite stops at execution boundary
→ Connector outbound provider dispatch  ← NOT in Lite
→ Provider adapter / provider HTTP      ← NOT in Lite
```

RT-WP3 Lite occupies **CRM governed dispatch orchestration through the
execution-request boundary only**. It prepares a references-only boundary
object and stops. It does not call Connector, construct adapters, or perform
provider HTTP.

### 2.2 Ownership terminology (mandatory)

```text
CRM owns governed dispatch orchestration (Lite: through boundary assembly).

Connector owns outbound provider dispatch, provider-adapter invocation,
transport execution, and provider HTTP.

CRM performs no outbound provider HTTP and invokes no provider SDK directly.
```

Do not use the unqualified phrase `dispatch owner`.

### 2.3 Preconditions

| Predecessor | Status | Lite dependency |
| --- | --- | --- |
| RT-WP0 | EXITED | Live contracts locked |
| RT-WP1 | EXITED | Capability/purpose direction locked |
| RT-WP2 | COMPLETED + TAGGED | ProviderBinding CRM policy surface consumable |
| Four-value portfolio | Frozen | No fifth `CompletionCapability` |
| C20-INV-02 / C20-INV-03 | ACTIVE | Namespace isolation; no CRM provider HTTP |
| C20-INV-04–13 | DEFERRED | No activation by this plan |

### 2.4 Primary future artifact (candidate, not authorized)

When Foundation Review ratifies an allowlist, the expected primary CRM
orchestration service remains `AIDispatchService` (Runtime Charter §22 /
§18.1). Lite implementation of that service (if ratified) may only:

- accept a governed request;
- validate purpose / capability;
- look up ProviderBinding policy;
- classify eligibility;
- assemble a references-only execution boundary;
- enforce Runtime Guards Lite.

It must not invoke Connector, schedule jobs, produce outbound AIRequestLog
evidence for provider calls, or claim full §22 exit.

---

## 3. Request Contract

A Lite dispatch request is a **policy request**, not a provider call.

### 3.1 Required logical fields

| Field | Rule |
| --- | --- |
| Request identity | Stable correlation / business identity; no secret material |
| Purpose reference | Explicit registered purpose ID; never inferred |
| Capability reference | Exactly one of the four portfolio values |
| ProviderBinding reference | Optional constraint / expected binding ID(s); lookup still required |
| Provenance reference | Non-secret actor / policy-version / decision-trace references |

### 3.2 Capability portfolio lock

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

```text
COMMERCIAL_BRIEF is not a CompletionCapability.
CommercialBrief is a C25 domain artifact / consumer boundary, not a capability.
commercial_brief_generation is not registered by RT-WP3 Lite.
```

### 3.3 Forbidden request contents

- API keys, tokens, plaintext credentials, authorization headers
- Provider SDK handles or transport instances
- Implicit purpose derived from entity type alone
- C25 CommercialBrief mutation instructions
- Retry / reservation / queue control fields
- Job execution state, queue state, or provider runtime handles

### 3.4 Execution boundary object (assembled, not invoked)

If eligibility is `BOUND` / eligible, Lite assembles a **references-only**
boundary object containing at most:

- request identity;
- purpose reference;
- capability reference;
- selected ProviderBinding policy reference(s);
- credential **reference** (not secret);
- non-secret provenance / policy-version references;
- optional externally supplied normalized health-input reference (consume only).

```text
Boundary assembly ≠ connector call.
Boundary object must not contain secrets or transport instances.
Lite stops at the boundary.
```

---

## 4. Request Flow and Resolution Flow

### 4.1 Request flow (high level)

```text
Authorized caller
  → Dispatch Request Contract (identity + references)
  → Runtime Guards Lite (early reject)
  → Purpose Validation
  → Capability Resolution
  → ProviderBinding lookup (RT-WP2 consume)
  → Eligibility Validation
  → Execution Boundary Assembly (references only)
  → STOP
```

No step after STOP is in Lite scope.

### 4.2 Resolution flow (fail-closed, deterministic)

```text
1. Authorize caller (ACL / action authorization; Portal denied for operator surfaces)
2. Runtime Guards Lite — reject secret-shaped input immediately
3. Validate purpose — registered + grammar; reject unregistered; no inference
4. Validate capability — four-value portfolio only; reject COMMERCIAL_BRIEF / unknown
5. Load ProviderBinding candidates from CRM RT-WP2 policy surface (read only)
6. Filter by ACTIVE/enabled, allowedPurposes, supportedCapabilities, credentialReference presence
7. Apply selection policy (explicit/auditable; fail closed on unresolved multi-candidate conflict unless an independently ratified rule exists)
8. Produce eligibility classification + non-secret evaluation trace
9. If eligible: assemble Execution Boundary (references only)
10. Stop — do not invoke Connector, Jobs, Api outbound execution, or AIRequestLog producer
```

### 4.3 Purpose validation rules

| Case | Behavior |
| --- | --- |
| Registered purpose | Continue |
| Unregistered / invalid grammar | Reject fail-closed |
| `commercial_brief_generation` | Not registered by Lite; reject |
| Automatic inference from entity/capability/C25 name | Forbidden |

### 4.4 Capability resolution rules

| Case | Behavior |
| --- | --- |
| One of four portfolio values | Continue |
| `COMMERCIAL_BRIEF` | Reject fail-closed |
| Unknown / empty / malformed | Reject fail-closed |
| Enum expansion | Forbidden |

### 4.5 Eligibility classifications (policy only)

Reuse RT-WP2 policy classifications (and equivalents), e.g.:

`NOT_AUTHORIZED`, `UNBOUND`, `DISABLED`, `PURPOSE_NOT_REGISTERED`,
`CAPABILITY_MISMATCH`, `CREDENTIAL_REFERENCE_MISSING`, `BOUND`.

`BOUND` means **policy-configured for handoff**. It does **not** authorize
provider HTTP, retry, reservation, or job execution.

Forbidden as Lite eligibility meanings: `QUEUED`, `RUNNING`, `RETRY_PENDING`,
`DISPATCH_FAILED`, `RESERVATION_CONFLICT`, `PROVIDER_TIMEOUT`,
`EXECUTION_COMPLETED`.

### 4.6 Runtime Guards Lite (mandatory)

| Guard | Behavior |
| --- | --- |
| Invalid capability | Reject fail-closed |
| `COMMERCIAL_BRIEF` | Reject fail-closed |
| Missing ProviderBinding / no eligible binding | Reject or classify ineligible (deterministic; no fallback discovery) |
| Secret-shaped input | Reject; never log or serialize secret values |

Guards are policy/authorization guards only. They must not trigger retry,
reservation, queueing, or outbound calls.

---

## 5. ProviderBinding Interaction

### 5.1 Consumer of RT-WP2 only

```text
RT-WP3 Lite consumes the completed ProviderBinding CRM policy surface.
It does not redesign RT-WP2 fields, weaken credential-reference rules,
or register commercial_brief_generation by side effect.
```

| Allowed | Forbidden |
| --- | --- |
| Lookup / read policy records | Mutation of ProviderBinding entities |
| Validate against `allowedPurposes` / capabilities / enabled / ACTIVE | Creation of bindings |
| Require non-empty `credentialReference` | Credential resolution / decryption / export |
| Produce authorized candidate set for boundary assembly | Adapter self-selection / environment default / hidden fallback |

### 5.2 Selection policy rules

| Rule | Requirement |
| --- | --- |
| Explicit binding only | No environment default; no hidden fallback; no adapter self-selection |
| Purpose gate | Purpose on binding `allowedPurposes` and in governed catalog |
| Capability gate | Binding `supportedCapabilities` includes required registry family |
| Credential gate | Non-empty `credentialReference`; never resolve the secret |
| Enabled gate | `ACTIVE` and `enabled=true` |
| Conflict | Multiple eligible candidates → fail closed unless independently ratified priority rule exists |
| C25 | CommercialBrief owns no binding selection |

### 5.3 Registry relationship

Capability Registry (`CapabilityRegistry.resolve`) remains the frozen
connector-side eligibility engine for connector-shaped binding tuples. CRM Lite
**prepares** authorized binding references / `allowed_provider_bindings`-shaped
inputs. Lite does **not** re-implement registry discovery, transport
construction, or adapter invocation, and does **not** call live provider
resolve paths.

---

## 6. Security Boundary

| Requirement | Enforcement intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03; no SDK, curl, Guzzle, sockets in Lite path |
| Credential reference only | Pass references; never resolve, decrypt, or export secrets |
| No secret in logs/errors/exports/fixtures | Safe messages and non-secret provenance only |
| Secret-shaped input rejection | Runtime Guards Lite mandatory reject |
| ACL / Portal | Operator dispatch surfaces Portal-denied; governed actions ≠ generic edit |
| Admin no-bypass | Save-option / mutation guard patterns remain authoritative where AIJob/policy writes exist |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| Health | Consume external normalized health input only; no CRM probing or live counters |
| AIJob ACL Foundation Gate | Required before any operator-visible dispatch action surface (Runtime Charter §22.1); Lite must not ship operator-visible execute actions without that gate |

Invariant posture preserved by this plan:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation)
```

---

## 7. Forbidden Surfaces

Implementation under this plan must not contain or assume:

| Forbidden surface | Reason |
| --- | --- |
| Connector call / `ConnectorBoundary.execute` | Outbound execution; excluded from Lite |
| HTTP egress from CRM PHP | C20-INV-03 ACTIVE |
| Adapter invocation / provider runtime | Connector-owned |
| ProviderBinding mutation / creation | RT-WP2 ownership; consume only |
| Credential / token / secret handling | Connector custody |
| Retry / backoff / failure-metadata executor | RT-WP5 deferred |
| Reservation / lease / concurrency claim | RT-WP6 deferred |
| Queue / worker / `Jobs/AIDispatchWorker` | Explicitly excluded |
| API outbound execution path | Explicitly excluded |
| AIRequestLog outbound producer / INV-08 exit claim | Explicitly deferred |
| AIJob cancel-reason / execution-state design | RT-WP4 deferred |
| Full RT-WP7 guard/activation system | Deferred; Lite guards only |
| RT-WP8 freeze claims | Deferred |
| C25 lifecycle / CommercialBrief execution | C25 WP2.2 NO GO |
| Opportunity / sales CRM lifecycle authority | Out of C20 Lite |
| `CompletionCapability` enum expansion | ADR-C20-005 locked |
| Invariant registry status flips | RT-WP7 / governance-status only |

```text
Lite authorization is not full Runtime Charter §22 exit authorization.
```

---

## 8. Proposed File Candidates

```text
These are candidates only.
This plan does NOT finalize the file allowlist.
Exact allowlist ratification belongs to the Foundation Review.
```

### 8.1 Provisional CRM candidates (Lite-compatible)

| Candidate | Intended Lite role | Condition |
| --- | --- | --- |
| `Services/AIDispatchService.php` | Primary orchestration: request accept, validation, lookup, eligibility, boundary assembly, Runtime Guards Lite | No connector invoke; no worker; no outbound AIRequestLog producer |
| Supporting DTO / value-object / guard classes under `Modules/AIPlatform/` (if Foundation names them) | Request contract, boundary object, guard helpers | Foundation/Lite only; no C25 / ProviderBinding redesign |
| `crm-extension/tests/test_phase3c20_rt_wp3_*.py` (foundation / isolation / guard tests) | Contract, negative, isolation, regression | No network I/O; no secret resolution; no live provider calls |

### 8.2 Explicitly excluded from Lite candidates

| Path / class of path | Exclusion |
| --- | --- |
| `Jobs/AIDispatchWorker.php` | Worker / queue — forbidden |
| `Api/PostAIDispatch.php` and outbound execution routes | Outbound execution — forbidden unless a later, separately ratified non-executing surface is authorized (not this plan) |
| `Services/AIRequestLogService.php` outbound producer path | Deferred / excluded |
| `chitu-connector/.../dispatch.py` and any connector source | Forbidden |
| Any `ProviderBinding*` mutation surface | Consume only — do not modify |
| `CompletionCapability` enum / connector portfolio files | Forbidden |
| Any C25 CommercialBrief / Opportunity / sales files | Forbidden |

### 8.3 Allowlist process

1. Independent Plan Review of this document.
2. Foundation Review proposes and ratifies the **exact** file allowlist.
3. Implementation may touch only ratified allowlist rows.
4. Any path outside the ratified allowlist requires a new authorization.

---

## 9. Test Strategy

When implementation is separately gated by Foundation Review PASS, tests must
prove Lite contracts **without** network I/O or connector invocation.

| Category | Coverage |
| --- | --- |
| Contract | Request shape; purpose validation; four-value portfolio; binding lookup inputs; eligibility matrix; execution-boundary DTO contains references only |
| Negative | `COMMERCIAL_BRIEF`; unregistered purpose; missing/disabled binding; secret-shaped fields; invalid capability |
| Guards Lite | Each of the four mandatory rejects is unit-proven |
| Isolation | No HTTP egress markers; no connector call sites in Lite unit under test; no retry/reservation/queue modules introduced by Lite allowlist |
| Regression | RT-WP2 ProviderBinding contracts remain green; C20-INV-02/03 ACTIVE; INV-04–13 DEFERRED unchanged |
| Cross-surface | Fixture binding shape remains consumable by frozen connector types **without** live provider resolve |

No Lite test may:

- perform provider HTTP;
- resolve secrets;
- invoke Connector;
- claim AIRequestLog outbound cardinality / INV-08 exit.

---

## 10. Exit Criteria

### 10.1 Plan exit (this document)

This plan may be considered complete for Independent Plan Review when:

1. All seven Lite surfaces are specified.
2. Deferred / forbidden surfaces are explicit.
3. Security and invariant posture are explicit.
4. File paths are **candidates only** (allowlist not finalized here).
5. Implementation remains gated on Plan Review + Foundation Review.
6. Commit / push / tag remain unauthorized by this plan.

### 10.2 Lite implementation exit (future; not claimed now)

Lite implementation may later claim foundation-complete only when all hold:

1. Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §1.1 only.
3. Runtime Guards Lite proven.
4. No connector / HTTP / worker / reservation / retry / C25 coupling.
5. Independent Implementation Review PASS.
6. Separate commit/push/tag authorization (if any) is obtained.

Full RT-WP3 §22 / INV-08 exit remains **out of Lite scope**.

---

## Authorization Boundary (plan)

```text
RT-WP3 Charter:
RATIFIED

RT-WP3 Implementation:
AUTHORIZED WITH CONDITIONS (Lite only)

Exact file allowlist:
NOT FINALIZED

Any runtime code:
NOT STARTED — gated on Plan Review + Foundation Review

RT-WP4–RT-WP8:
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

Rationale: Lite scope is internally consistent with the ratified RT-WP3
Charter, AUTHORIZED WITH CONDITIONS boundary, frozen four-value portfolio,
RT-WP2 consume-only ProviderBinding posture, and ACTIVE C20-INV-02/03. Full
§22 outbound/logging/worker inventory is explicitly excluded. No BLOCKER
condition exists in this planning document.

```text
Next Task:
Phase3C20 RT-WP3 Implementation Plan Independent Review
```

---

## References

1. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md` (RATIFIED)
2. `docs/audit/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER_REVIEW.md` (PASS WITH INFORMATIONAL NOTES)
3. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§6, §9.3, §10, §11, §18.1, §22, §28)
4. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
6. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
7. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
8. `docs/adr/C20_INVARIANT_REGISTRY.md`
9. Live tags: `phase3c20-rt-wp3-charter-ratified`, `phase3c20-rt-wp2-implementation-completed`
10. Live HEAD at plan drafting: `12ec8a86ce3adc1a04f94b600f5926a301793eb7`

---

*This plan is a planning document. It creates no production runtime change,
modifies no ProviderBinding implementation, stages no commit, and authorizes
no code. Exact file allowlist belongs to Foundation Review. Lite
implementation begins only after Plan Review PASS and Foundation Review PASS.*
