# Phase3C25 WP4 Implementation Plan

| Field | Value |
| --- | --- |
| Document Type | Implementation Plan (planning / design boundary only) |
| Work Package | WP4 — Commercial Decision Support Layer |
| Parent Charter | `docs/PHASE3C25_NEXT_WP_CHARTER.md` (**APPROVED**) |
| ADR alignment | ADR-C25-004 Human Decision Workspace Architecture (§7.1 Workspace Data Budget) |
| Charter Condition Closure | `docs/audit/PHASE3C25_WP4_CHARTER_CONDITION_CLOSURE.md` |
| Plan Condition Closure | `docs/audit/PHASE3C25_WP4_IMPLEMENTATION_PLAN_CONDITION_CLOSURE.md` |
| Status | **APPROVED** — Re-Review complete; Implementation Authorization **NOT** granted |
| Date | 2026-08-04 |
| Baseline | C20 CLOSED; Package A RELEASED; WP2.0 SATISFIED; WP2.2 FROZEN (`phase3c25-wp2-2-freeze`); WP3 FROZEN (`phase3c25-wp3-freeze`); WP4 Charter Evidence `701d438` |
| Implementation Authorization | **NO** |
| Planning Authorization | Design documentation APPROVED; code delivery requires separate Implementation Authorization |
| Commit / push / tag | Evidence commit authorized separately for governance sync only |

```text
This plan defines the WP4 implementation design boundary after charter
approval and plan-review condition closure.

APPROVED ≠ Implementation Authorized.
It does NOT authorize code delivery, Runtime Expansion, C20 reopening,
C22/C24 ownership transfer, C24 transition invocation delivery,
autonomous commercial execution, or invariant activation.
```

---

# Part 0 — Plan Review Condition Closure

| Condition | Finding | Resolution | Status |
| --- | --- | --- | --- |
| 1 | `DecisionIntentRecord` conflicts with ADR-C25-004 §7.1 (no persisted decision intent) | Replaced by **Human Review Decision Record** = human review outcome only | **CLOSED** (§6) |
| 2 | Test Strategy underspecified | Explicit ownership / authority / provenance / boundary / lifecycle tests | **CLOSED** (§10) |

```text
Plan review conditions CLOSED.
Re-Review: APPROVED.
Next gate: Implementation Authorization (separate).
Implementation remains NOT AUTHORIZED.
```

---

# Part 1 — Charter Inheritance (Already Closed)

WP4 Charter Final Review: **APPROVED**.
Charter conditions 1–5 are **CLOSED**. This plan inherits them; it does not reopen them.

| Condition | Charter resolution | Plan posture |
| --- | --- | --- |
| 1 Naming | Decision Support Layer = Human Decision Workspace (implementation-facing); ≠ AI decision maker | **INHERITED / CLOSED** |
| 2 Feedback | Human governance signal only; no training / autonomous learning / shadow CRM | **INHERITED / CLOSED** |
| 3 Transition | Default presentation + intent collection only; future invocation = separate gate | **INHERITED / CLOSED** |
| 4 AI authority | May summarize/analyze/classify/propose/explain; may NOT decide/approve/execute/mutate | **INHERITED / CLOSED** |
| 5 Ownership | C25 / C20 / C22 / C24 / CRM Core boundaries unchanged | **INHERITED / CLOSED** |

```text
Charter APPROVED ≠ Implementation Authorized
Plan APPROVED ≠ Implementation Authorized
```

---

# Part 2 — WP4 Scope

WP4 is the **Commercial Decision Support Layer**
(= ADR-C25-004 Human Decision Workspace, implementation-facing name).

### Allowed (application intelligence)

- decision-support context assembly / presentation
- insight comparison across named frozen artifacts
- recommendation presentation (advisory labels + provenance)
- review preparation for human reviewers / business users
- human review decision records (review outcome only)
- human-provided presentation / explanation feedback (bounded)
- provenance references to Package A / WP2.2 / WP3 identities

### Forbidden

- autonomous commercial actions
- outbound execution
- AI agent / operator / decision engine
- provider execution / connector / AIJob
- workflow automation engine
- CRM Lead / Opportunity mutation
- C22 ProspectRun / outreach / action ledger ownership
- C24 entity replacement or lifecycle mutation
- default C24 transition service invocation from C25
- persisted “decision intent” / future-action intent as a database entity (ADR-C25-004 §7.1)

```text
WP4 = Commercial Decision Support Layer
WP4 ≠ execution engine
WP4 ≠ autonomous sales agent
WP4 ≠ C24 transition executor (default)
WP4 ≠ persisted decision-intent store
```

Builds on:

- C20 governance foundation + Package A capability/purpose identity
- Frozen WP2.2 `CommercialBrief` (`phase3c25-wp2-2-freeze`)
- Frozen WP3 `CommercialInsight` / `BusinessReviewContext` (`phase3c25-wp3-freeze`)

---

# Part 3 — C20 Boundary

**C20 provides:**

- capability identity
- purpose policy
- provider governance

**WP4 consumes C20 references only** (where provenance requires Package A identity).

**Forbidden:**

- provider invocation
- runtime expansion
- connector changes
- AIJob executor
- capability registry mutation
- invariant activation

Any future live-generation path requires separate Runtime Expansion /
execution authorization outside WP4.

---

# Part 4 — C22 Boundary

**WP4 does not own:**

- ProspectRun
- Outreach
- Action Ledger
- prospect execution
- Lead lifecycle

**C22 remains execution owner.**

WP4 must not advance C22 states, mutate ledgers, or create/convert Leads as a
side effect of decision-support presentation or human review recording.

---

# Part 5 — C24 Boundary

WP4 consumes C24 artifacts **read-only**.

**Sources (named):**

- `RevenueInsight`
- `PipelineMetric`
- `OpportunityCandidate`

**Allowed:**

- read
- present
- compare
- reference provenance

**Forbidden:**

- replacing C24 entities
- modifying C24 lifecycle
- owning OpportunityCandidate lifecycle
- mutating CRM business state
- silent C24 transition invocation

```text
WP4 consumes C24.
WP4 does not replace C24.
WP4 does not own OpportunityCandidate / RevenueInsight / PipelineMetric lifecycles.
```

**ADR-C25-004 note:** A future path where human review outcomes may lead to
C24 governed transition services **outside C25 ownership** remains **out of
WP4 default delivery scope**. Enabling it requires a separate authorization
gate and must not be assumed from charter approval or this APPROVED plan.

---

# Part 6 — Candidate Capabilities (Planning Only)

Evaluate candidates for later authorized design selection. **Do not implement**
under this document without Implementation Authorization.

### DecisionSupportContext

| Dimension | Definition |
| --- | --- |
| Purpose | Compose a human decision-support packet for review preparation |
| Owner | C25 |
| Lifecycle | Presentation / governed read-model composition; not an execution ticket |
| Authority boundary | Cannot execute CRM/C22/C24 transitions; cannot auto-accept briefs/insights |

**Explicit source references (required):**

- `CommercialBrief` (WP2.2 — FROZEN)
- `CommercialInsight` (WP3 — FROZEN)
- `BusinessReviewContext` (WP3 — FROZEN)
- C24 read-only sources: `RevenueInsight`, `PipelineMetric`, `OpportunityCandidate`

```text
DecisionSupportContext references named artifacts.
Do not describe sources only as “WP2.2/WP3/C24”.
```

### Human Review Decision Record

Replaces the withdrawn **DecisionIntentRecord** concept.

| Dimension | Definition |
| --- | --- |
| Purpose | Record **human review outcome** for C25 advisory artifacts / decision-support packets |
| Owner | C25 (review outcome record only) |
| Lifecycle | Human review lifecycle only (see §10.5); does not enact CRM/C22/C24 mutation |
| ADR-C25-004 §7.1 | **Must not** persist “decision intent” as a database entity / shadow planning store |

**Represents:**

- human review outcome

**Allowed concepts:**

- review decision
- acceptance / dismissal
- reviewer annotation
- evaluation note

**Forbidden concepts:**

- future action intent
- AI intent engine
- autonomous planning
- workflow trigger
- action command
- CRM lifecycle instruction

**If a persisted review record is later authorized, it may contain:**

- reviewer identity
- review status
- review comment
- provenance reference
- timestamps

**It must NOT contain:**

- CRM lifecycle fields
- Opportunity mutation fields
- C24 ownership fields
- C22 execution fields
- workflow commands

```text
Human Review Decision Record = human review outcome
Human Review Decision Record ≠ decision intent store
Human Review Decision Record ≠ workflow / CRM / C24 command
```

### PresentationFeedback

| Dimension | Definition |
| --- | --- |
| Purpose | Collect human explanation-quality / presentation improvement feedback |
| Owner | C25 presentation feedback only |
| Lifecycle | Human-provided governance signal |
| Authority boundary | No training loop; no C21 HumanFeedback truth merge; no shadow CRM fields |

### RecommendationPresentation (facet)

| Dimension | Definition |
| --- | --- |
| Purpose | Present advisory recommendations with provenance and non-authority labels |
| Owner | C25 presentation |
| Lifecycle | Advisory consume/present |
| Authority boundary | Cannot decide, approve, or mutate lifecycle |

**Planning preference (non-binding until Implementation Authorization):**

Primary pair: **DecisionSupportContext + Human Review Decision Record**
Facet: **PresentationFeedback**
Consume-only named references to CommercialBrief / CommercialInsight /
BusinessReviewContext / C24 sources.

---

# Part 7 — Data Ownership

| Owner | Owns |
| --- | --- |
| **C25** | Intelligence artifacts, presentation, advisory review support, decision-support surfaces, human review outcome / presentation feedback records (non-enacting) |
| **CRM Core** | Customer lifecycle, opportunity lifecycle |
| **C24** | `OpportunityCandidate`, `RevenueInsight`, `PipelineMetric`, related revenue-ops governance |
| **C22** | Prospect execution |
| **C20** | Capability registry, purpose policy, provider governance |

No ownership transfer across layers.

**ADR-C25-004 §7.1 alignment:** Workspace data budget forbids persisted decision
intent, shadow CRM state, and workspace-owned lifecycle fields. WP4 planning
respects that budget.

---

# Part 8 — AI Authority

**AI can:**

- summarize
- analyze
- propose
- classify
- explain

**AI cannot:**

- decide
- approve
- execute
- mutate lifecycle
- accept / dismiss review outcomes

Human reviewer / business user remains final authority for review
accept/dismiss where authorized.

Content sources under WP4 default delivery remain fixture / stub / deterministic /
human-authored presentation support unless a separate Runtime Expansion gate
authorizes live generation.

---

# Part 9 — Architecture Boundary

### Allowed (application layer)

- entities / metadata under CommercialIntelligence (or equivalent C25 module path)
- read models
- aggregation / presentation services
- ACL
- provenance validators
- human review outcome / presentation feedback services (non-enacting)

### Forbidden

- `chitu-connector/**` execution paths
- AIPlatform provider runtime / AIJob / workers / queues / schedulers
- Prospecting / C22 mutation paths
- C24 lifecycle mutation / replacement
- CRM Core Lead / Opportunity mutation
- persisted decision-intent entities

### Proposed allowlist (if later authorized)

```text
crm-extension/.../CommercialIntelligence/**
WP4 tests under crm-extension/tests/
```

Exact path list is finalized only under Implementation Authorization.

---

# Part 10 — Test Strategy (Condition 2 — CLOSED)

Planning-required verification categories. Tests become mandatory under
Implementation Authorization; this section defines the required coverage.

## 10.1 Ownership Tests

Verify WP4 does **not** own or mutate:

- C22 `ProspectRun`
- Outreach
- Action Ledger
- C24 `RevenueInsight`
- C24 `PipelineMetric`
- C24 `OpportunityCandidate`
- CRM Core customer / opportunity lifecycle

## 10.2 Authority Tests

Verify AI / system actors **cannot**:

- accept
- dismiss
- approve
- execute
- mutate lifecycle

Verify human reviewer **can** (where authorized):

- review
- annotate
- accept / dismiss Human Review Decision outcomes

## 10.3 Provenance Tests

Verify Decision Support artifacts retain:

- source references (named CommercialBrief / CommercialInsight / BusinessReviewContext / C24 ids as applicable)
- capability references
- purpose references
- evidence lineage

## 10.4 Boundary Tests

Verify absence of:

- provider invocation
- connector calls
- AIJob runtime
- queue
- scheduler
- worker
- C22 / C24 mutation paths

## 10.5 Lifecycle Tests

Verify **human review lifecycle only** for Human Review Decision Records:

```text
GENERATED
    ↓
REVIEWED
    ↓
ACCEPTED / DISMISSED
```

- No automatic GENERATED → ACCEPTED / DISMISSED transition
- No AI/system accept/dismiss
- No CRM/C22/C24 side-effect transitions from review status changes

---

# Part 11 — Implementation Sequence (Planning Sketch)

| Phase | Content | Gate required |
| --- | --- | --- |
| Phase 0 | Plan DRAFT → plan review → REVISED → Re-Review **APPROVED** (this document) | Plan approval |
| Phase 1 | Minimal DecisionSupportContext metadata / entityDefs (named source refs) | Implementation Authorization |
| Phase 2 | Read-only aggregation / presentation over CommercialBrief / CommercialInsight / BusinessReviewContext / C24 | Implementation Authorization |
| Phase 3 | Human Review Decision Record + PresentationFeedback (human-only) | Implementation Authorization |
| Phase 4 | Provenance + ACL + full §10 test suite | Implementation Authorization |
| Deferred | C24 governed transition invocation from C25 surface | **Separate authorization gate** |

---

# Part 12 — Success Criteria (Governance)

- humans can prepare commercial decisions from named frozen WP2.2 / WP3 artifacts
- provenance remains visible on decision-support surfaces
- human review outcomes / presentation feedback remain human-authored and non-enacting
- no persisted decision-intent store (ADR-C25-004 §7.1)
- no ownership leakage into C20 / C22 / C24 / CRM Core

**Not success criteria:**

- autonomous execution
- conversion automation
- outbound metrics
- live provider availability
- AI decision / approval rates

---

# Part 13 — Explicit Non-Delivery

Not delivered by this APPROVED plan (and not implied without separate gates):

- Runtime Expansion
- provider / connector / AIJob execution
- C22 execution ownership
- C24 lifecycle mutation or replacement
- CRM Opportunity / Lead mutation
- C24 transition invocation from C25
- persisted DecisionIntentRecord / decision-intent entity
- invariant activation
- WP4 Implementation Authorization
- WP4 Implementation

---

# Part 14 — Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | **CLOSED** |
| C20 Package A | **RELEASED** |
| C25 WP2.0 | **SATISFIED** |
| WP2.2 CommercialBrief | **FROZEN** |
| WP3 Commercial Intelligence | **FROZEN** |
| WP3 Governance Closure | **COMPLETE** |
| WP4 Charter | **APPROVED** |
| WP4 Implementation Plan | **APPROVED** |
| WP4 Authorization | **NOT AUTHORIZED** |
| WP4 Implementation | **NOT AUTHORIZED** |
| C24 Transition Invocation Gate | **NOT AUTHORIZED** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

```text
Next gate: Implementation Authorization (separate).
APPROVED plan does not authorize code.
```

---

# Part 15 — Document Control

| Item | Value |
| --- | --- |
| Author role | WP4 implementation plan revision owner |
| Mode | Documentation-only APPROVED plan evidence |
| Parent charter | `docs/PHASE3C25_NEXT_WP_CHARTER.md` |
| Plan condition closure | `docs/audit/PHASE3C25_WP4_IMPLEMENTATION_PLAN_CONDITION_CLOSURE.md` |
| Production code changes | **NONE** |
| Commit of this revision | Evidence commit when separately authorized |

---

*End of Phase3C25 WP4 Implementation Plan (APPROVED — no implementation authorization).*
