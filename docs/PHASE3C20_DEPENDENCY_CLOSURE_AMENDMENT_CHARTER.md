# Phase3C20 Dependency Closure Amendment Charter

| Field | Value |
| --- | --- |
| Document Type | C20 Dependency Closure Amendment Charter (governance design) |
| Charter path | `docs/PHASE3C20_DEPENDENCY_CLOSURE_AMENDMENT_CHARTER.md` |
| Status | **APPROVED WITH CONDITIONS** |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| Runtime Lite posture | FROZEN (Lite closure + freeze evidence + RT-WP8 Lite governance freeze) |
| Amendment class | Minimal Dependency Closure — **not** Runtime Expansion |
| Implementation authorization | **NOT AUTHORIZED** by this draft |
| Commit / push / tag | **NOT AUTHORIZED** by this draft |
| C25 WP2.2 | **NOT AUTHORIZED** |

```text
This charter defines the governance boundary, ownership, and approval path for
a minimal C20 Dependency Closure Amendment.

It does NOT authorize Runtime Expansion, RT-WP8 Full, C25 WP2.2 implementation,
invariant activation, or autonomous commercial execution.

COMMERCIAL_BRIEF ≠ commercial_brief_generation
Capability registration ≠ provider execution
Architecture readiness ≠ C25 WP2.2 authorization
```

---

## 1. Purpose

Define a formal, minimal C20 amendment package that closes the governance
dependencies identified by C25 WP2.0 Dependency Resolution — without reopening
Runtime Lite, without expanding runtime execution surfaces, and without
starting C25 commercial-intelligence implementation.

This charter is the **planning and approval contract** for that amendment. It
does not itself deliver ADR edits, enum changes, purpose registration,
registry flips, or tests.

---

## 2. Background

Phase3C20 Runtime Lite is complete and frozen:

| Milestone | State |
| --- | --- |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2–RT-WP7 Lite | COMPLETED + TAGGED |
| Runtime Lite Closure | COMPLETE |
| Freeze Evidence | COMPLETE |
| RT-WP8 Lite | Governance freeze established (Lite freeze ≠ Full §27) |
| Runtime Expansion | **NOT AUTHORIZED** |

C25 WP2.0 Dependency Resolution recorded **NO GO / BLOCKED** because required
C20 governance outputs remain unresolved, including:

1. Stable CompletionCapability identity for commercial brief preparation
   (`COMMERCIAL_BRIEF` currently proposed-only / absent from the ratified
   four-value portfolio).
2. ProviderBinding purpose availability for `commercial_brief_generation`.
3. Clarified invariant posture distinguishing governance/provenance candidates
   from runtime-execution invariants that still require Runtime Expansion.

The required C20 response is this **Dependency Closure Amendment** — not a
runtime program and not a C25 implementation start.

Authoritative priors include:

- `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
- `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md`
- `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
- `docs/PHASE3C20_RT_WP8_LITE_IMPLEMENTATION_CHARTER.md`
- `docs/audit/PHASE3C20_RUNTIME_INVARIANT_STATUS_SYNC_REVIEW.md`

---

## 3. Problem Statement

| Gap | Current state | Consumer impact |
| --- | --- | --- |
| Capability identity | Ratified portfolio is four values; `COMMERCIAL_BRIEF` is proposed-only and not present | C25 cannot cite a stable C20 capability identity for CommercialBrief preparation |
| Purpose registration | `commercial_brief_generation` is not an available ProviderBinding purpose | Binding eligibility / purpose resolution cannot authorize the brief purpose |
| Invariant clarity | INV-05…11 remain DEFERRED as a set; Lite freeze must not be misread as activation | C25 provenance expectations and Runtime Expansion boundaries are ambiguous without an amendment classification |

Without a bounded C20 amendment, C25 WP2.0 closure remains blocked and C25
WP2.2 must not proceed.

---

## 4. Amendment Scope

This amendment covers **exactly three areas**:

| # | Area | Nature |
| --- | --- | --- |
| 1 | CompletionCapability Portfolio Amendment | Evaluate adding `COMMERCIAL_BRIEF` as a fifth capability value |
| 2 | ProviderBinding Purpose Amendment | Evaluate registering `commercial_brief_generation` as an allowed purpose |
| 3 | Invariant Governance Amendment | Classify INV-05/07/09 as activation **candidates**; keep INV-06/08/10/11 **DEFERRED** |

```text
Minimal dependency closure only.
Not Runtime Expansion.
Not C25 WP2.2.
Not autonomous commercial enablement.
```

---

## 5. Capability Portfolio Amendment

### 5.1 Problem

C25 CommercialBrief preparation requires a stable capability identity. The
current ratified `CompletionCapability` portfolio does not include
`COMMERCIAL_BRIEF`.

### 5.2 Decision under evaluation

Evaluate adding:

```text
COMMERCIAL_BRIEF
```

as a **fifth** CompletionCapability portfolio value under C20 ownership.

### 5.3 Ownership

| Owner | Owns |
| --- | --- |
| **C20** | Capability identity; capability registry; capability contract |
| **C25** | CommercialBrief entity; business workflow; human review process; presentation layer |

No ownership transfer.

### 5.4 Explicit non-goals for `COMMERCIAL_BRIEF`

`COMMERCIAL_BRIEF` is **NOT**:

- an autonomous sales capability
- a CRM mutation capability
- lifecycle authority
- an execution engine

### 5.5 Required guardrail

Capability registration does **NOT** imply:

- automatic routing
- provider execution
- external calls
- autonomous generation

```text
Capability identity ≠ routing authority
Capability identity ≠ connector invocation
Capability identity ≠ C25 CommercialBrief runtime
```

---

## 6. ProviderBinding Purpose Amendment

### 6.1 Problem

ProviderBinding policy surface exists under Runtime Lite (RT-WP2). The purpose
`commercial_brief_generation` is currently unavailable for binding
`allowed_purposes` registration.

### 6.2 Decision under evaluation

Evaluate registering:

```text
commercial_brief_generation
```

as an allowed ProviderBinding purpose under C20 ProviderBinding governance.

### 6.3 Purpose-registration boundary

| Allowed by purpose registration | Not allowed |
| --- | --- |
| Provider eligibility reference | Connector invocation |
| Capability resolution linkage | HTTP execution |
| Provenance reference | Worker / queue / scheduler execution |
| Policy-level purpose membership | Retry execution |
| | Autonomous generation |

### 6.4 Explicit separation

```text
COMMERCIAL_BRIEF  ≠  commercial_brief_generation
```

| Object | Layer | Owner |
| --- | --- | --- |
| `COMMERCIAL_BRIEF` | CompletionCapability portfolio member (identity) | C20 |
| `commercial_brief_generation` | ProviderBinding purpose ID (eligibility / use-case key) | C20 binding governance |

Capability identity and provider purpose remain **separate governance objects**.
Do not use `COMMERCIAL_BRIEF` as an `allowed_purposes` value.
Do not treat `commercial_brief_generation` as a CompletionCapability enum value.

---

## 7. Invariant Governance Amendment

Review targets (registry authority remains `docs/adr/C20_INVARIANT_REGISTRY.md`):

| ID | Concern |
| --- | --- |
| INV-05 | AIJob status guard |
| INV-06 | Cancel reason |
| INV-07 | AIRequestLog append-only |
| INV-08 | One-log-per-invocation |
| INV-09 | PromptTemplate immutability |
| INV-10 | Retry eligibility |
| INV-11 | Idempotency reservation |

### 7.1 Governance / provenance invariants — activation candidates

| ID | Classification | Reason |
| --- | --- | --- |
| INV-05 | **CANDIDATE** (future activation) | Existing enforcement surface present |
| INV-07 | **CANDIDATE** (future activation) | Existing enforcement surface present |
| INV-09 | **CANDIDATE** (future activation) | Existing enforcement surface present |

```text
CANDIDATE ≠ ACTIVE
Candidate classification does not flip registry status.
Activation requires a separately authorized governance-status action
with independent evidence — not this charter alone.
```

### 7.2 Runtime execution invariants — remain deferred

| ID | Classification | Reason |
| --- | --- | --- |
| INV-06 | **DEFERRED** | Requires future Runtime Expansion (cancellation lifecycle) |
| INV-08 | **DEFERRED** | Requires future Runtime Expansion (dispatch producer / exactly-once outbound path) |
| INV-10 | **DEFERRED** | Requires future Runtime Expansion (retry executor) |
| INV-11 | **DEFERRED** | Requires future Runtime Expansion (reservation engine) |

This amendment must **not** activate INV-06/08/10/11 and must **not** treat
Lite metadata foundations as substitute executors.

### 7.3 Already ACTIVE invariants (unchanged)

Per authoritative sync (`PHASE3C20_RUNTIME_INVARIANT_STATUS_SYNC_REVIEW.md`):

```text
ACTIVE (unchanged by this amendment draft):
INV-02, INV-03, INV-14, INV-15, INV-16, INV-18, INV-19, INV-21, INV-22

DEFERRED (remaining registry entries, including INV-01/04/12/13/17/20
and INV-06/08/10/11; INV-05/07/09 remain DEFERRED until separately activated):
according to C20_INVARIANT_REGISTRY.md
```

Candidate classification for INV-05/07/09 does not change their current
registry `DEFERRED` rows in this draft.

---

## 8. Ownership Boundary

### 8.1 C20 owns

- Capability Registry
- ProviderBinding governance
- Runtime invariant governance
- AI execution policy boundary

### 8.2 C25 owns

- CommercialBrief artifact
- Intelligence workflow
- Human validation
- Commercial presentation

### 8.3 Transfer rule

```text
No ownership transfer.
C20 does not own CommercialBrief.
C25 does not own CompletionCapability portfolio membership or ProviderBinding
policy authority.
```

---

## 9. Change Package Requirements

This amendment charter is **not documentation-only**. If ratified and later
separately authorized for delivery, the change package **may require**:

| Artifact class | Examples |
| --- | --- |
| ADR updates | ADR-C20-005 portfolio extension; ADR-C20-006 purpose registration addendum |
| Capability registry update | `CompletionCapability` portfolio / connector contract surfaces |
| ProviderBinding purpose update | Policy allowing `commercial_brief_generation` on bindings |
| Invariant status review | Evidence pack + optional later registry flips for INV-05/07/09 only |
| Tests update | Portfolio / purpose / boundary / negative tests |
| Independent review | Ratification review; implementation review; activation review (if any) |

```text
Charter ratification ≠ delivery authorization.
Delivery requires a separate, explicit implementation authorization
bounded to the three amendment areas and their non-goals.
```

---

## 10. Explicit Non-Goals

### 10.1 Runtime Expansion (excluded)

| Excluded surface | Status |
| --- | --- |
| Connector execution | NOT AUTHORIZED |
| HTTP dispatch | NOT AUTHORIZED |
| Worker | NOT AUTHORIZED |
| Queue | NOT AUTHORIZED |
| Scheduler | NOT AUTHORIZED |
| Retry executor | NOT AUTHORIZED |
| Cancellation engine | NOT AUTHORIZED |
| Reservation engine | NOT AUTHORIZED |
| RT-WP8 Full (§27) | NOT AUTHORIZED |

### 10.2 Commercial automation (excluded)

| Excluded behavior | Status |
| --- | --- |
| Autonomous outreach | NOT AUTHORIZED |
| Autonomous CRM mutation | NOT AUTHORIZED |
| Autonomous opportunity creation | NOT AUTHORIZED |
| Autonomous CommercialBrief generation / send | NOT AUTHORIZED |

---

## 11. C20 / C25 Relationship

| Milestone | Role |
| --- | --- |
| **C20 Runtime Lite** | Provides the governance foundation (policy, dispatch stop-boundary, state/failure/ownership metadata, guards) — **FROZEN** |
| **C20 Dependency Closure Amendment** | Provides **minimal dependency closure** (capability / purpose / invariant classification) — **DRAFT** |
| **C25 WP2.0** | Consumes approved governance outputs; remains **BLOCKED** until amendment delivery + independent closure criteria are met |
| **C25 WP2.2** | Still requires a **separate authorization review**; not authorized by this charter |

```text
C20 Runtime Lite
        → foundation (frozen)

C20 Dependency Closure Amendment
        → minimal governance outputs (this charter)

C25 WP2.0
        → consumes approved outputs (still blocked)

C25 WP2.2
        → separate authorization only (not authorized here)
```

---

## 12. Approval Process

Recommended sequence (each step separately gated):

1. **Charter ratification review** (independent) — PASS / RATIFIED required.
2. **Status synchronization** on Runtime / C25 dependency docs (documentation).
3. **Implementation authorization** (separate document) — only for the three
   amendment areas; Runtime Expansion remains excluded.
4. **Change package delivery** (ADR / registry / purpose / tests) under the
   authorized allowlist.
5. **Independent implementation review**.
6. **Optional invariant activation** for INV-05/07/09 only — separate
   governance-status action with evidence; never batch with INV-06/08/10/11.
7. **C25 WP2.0 closure addendum** (C25-owned consumption record) after C20
   outputs are approved.
8. **C25 WP2.2** — separate authorization entry only after WP2.0 closure PASS.

This draft authorizes **none** of steps 3–8.

---

## 13. Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | FROZEN |
| C20 Dependency Closure Amendment | DRAFT |
| COMMERCIAL_BRIEF Capability | PROPOSED |
| commercial_brief_generation Purpose | PROPOSED |
| INV-05 | CANDIDATE |
| INV-07 | CANDIDATE |
| INV-09 | CANDIDATE |
| INV-06 | DEFERRED |
| INV-08 | DEFERRED |
| INV-10 | DEFERRED |
| INV-11 | DEFERRED |
| C25 WP2.0 Closure | BLOCKED |
| C25 WP2.2 Authorization | NOT AUTHORIZED |
| Runtime Expansion | NOT AUTHORIZED |

```text
DRAFT — READY FOR RATIFICATION REVIEW
No implementation.
No registry mutation.
No invariant activation.
No C25 WP2.2 authorization.
No commit by this drafting task.
```

---

*This charter is a governance design document. It creates no production file
beyond itself, modifies no registry row, activates no invariant, expands no
runtime surface, and authorizes no C25 coding.*
