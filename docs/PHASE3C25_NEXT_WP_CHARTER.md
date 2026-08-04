# Phase3C25 Next Work Package Charter

| Field | Value |
| --- | --- |
| Document Type | Next WP Charter (architecture planning only) |
| Proposed Work Package | **WP4 — Commercial Decision Support Layer** |
| ADR alignment | ADR-C25-004 Human Decision Workspace Architecture (presentation / intent-collection surface) |
| Parent | Phase3C25 — AI Commercial Intelligence Layer |
| Status | **APPROVED** — Final Charter Review complete; ready for Implementation Plan drafting only |
| Date | 2026-08-04 |
| Baseline | C20 CLOSED; Package A RELEASED; WP2.0 SATISFIED; WP2.2 FROZEN (`phase3c25-wp2-2-freeze`); WP3 FROZEN + GOVERNANCE CLOSED (`phase3c25-wp3-freeze`); Governance Evidence Reconciliation COMPLETE (`b3814ee`) |
| Condition Closure | `docs/audit/PHASE3C25_WP4_CHARTER_CONDITION_CLOSURE.md` |
| Final Charter Review | **APPROVED** — READY FOR IMPLEMENTATION PLAN (drafting gate only) |
| Planning Authorization | **NO** — charter approval does not authorize Implementation Plan as delivery authority; drafting is a separate documentation gate |
| Implementation Authorization | **NO** |
| Commit / push / tag | Evidence commit authorized separately for governance sync only |

```text
This charter defines WP4 after WP3 freeze and governance evidence
reconciliation.

Charter APPROVED does NOT authorize implementation, Runtime Expansion,
C20 reopening, C22/C24 ownership transfer, or invariant activation.
Implementation Plan drafting is the next documentation gate only.
```

**Prior WP3 charter (historical):** `docs/PHASE3C25_WP3_CHARTER.md`

---

## 0. Condition Closure Summary

| Condition | Requirement | Status |
| --- | --- | --- |
| 1 | Naming alignment — Decision Support ≠ AI decision maker | **CLOSED** (§2) |
| 2 | Feedback boundary — human governance signal only | **CLOSED** (§3 Feedback) |
| 3 | Transition invocation — presentation + intent only by default | **CLOSED** (§3 Transition) |
| 4 | AI authority reinforcement | **CLOSED** (§6) |
| 5 | Ownership boundary | **CLOSED** (§5) |

```text
Charter conditions CLOSED.
Final Charter Review: APPROVED.
Next gate: Implementation Plan drafting (documentation only).
Planning / Implementation remain NOT AUTHORIZED.
```

---

## 1. Purpose

Define why the next WP exists and what gap it may later plan to close.

### Current capability chain (frozen)

```text
Evidence / governed sources
    ↓
CommercialBrief          (WP2.2 — FROZEN)
    ↓
CommercialInsight        (WP3 — FROZEN)
    ↓
BusinessReviewContext    (WP3 — FROZEN)
```

C25 can now:

- reference C20 capability / purpose identity (Package A)
- govern CommercialBrief proposal + human review
- assemble advisory CommercialInsight
- compose BusinessReviewContext for human review support

### Remaining gap

Operators still lack a governed **decision-support presentation layer** that:

- prepares human commercial decisions from briefs, insights, and review contexts
- compares / presents recommendations without granting AI authority
- collects human review/decision *intent* for enactment **outside** C25
- optionally captures explanation-quality feedback without owning C21/C23 feedback truth

**Must build on:**

- C20 governance foundation (CLOSED Runtime Lite)
- C20 Package A capability / purpose identity
- WP2.2 CommercialBrief (`phase3c25-wp2-2-freeze`)
- WP3 Commercial Intelligence Support Layer (`phase3c25-wp3-freeze`)

**Must preserve:**

- Human authority
- Application intelligence boundary
- No autonomous execution

```text
Next WP = commercial decision support surface
Next WP ≠ autonomous sales agent
Next WP ≠ execution engine
Next WP ≠ C20 Runtime Expansion
```

---

## 2. Proposed WP Name (Condition 1 — CLOSED)

**Phase3C25 WP4 — Commercial Decision Support Layer**

Governance-safe naming (avoids Agent / Autonomous / Operator / Automation).

### Naming equivalence (explicit)

```text
Commercial Decision Support Layer
  = implementation-facing name for
    ADR-C25-004 Human Decision Workspace
  = same presentation / intent-collection surface
```

Aligned with ratified C25 Implementation Charter WP4 and ADR-C25-004
as a C25-owned **presentation / intent-collection** surface — not as a
decision owner or lifecycle owner.

### “Decision Support” does NOT mean

| Phrase | Forbidden interpretation |
| --- | --- |
| Decision Support | AI decision maker |
| Decision Support | autonomous decision engine |
| Decision Support | AI operator |
| Decision Support | execution authority |

**Final authority remains:** human reviewer / business user.

```text
Decision Support = help humans prepare and review decisions
Decision Support ≠ AI decides / approves / executes
```

Alternate considered (deferred as secondary theme, not primary WP title):

- Intelligence Quality and Feedback Layer (may appear as a facet under ADR-C25-006 constraints)

---

## 3. Scope

Allowed **application intelligence** scope (planning candidates only; not authorized for implementation by this charter):

| Area | Intent |
| --- | --- |
| Decision support context | Present assembled commercial context for human decision preparation |
| Insight comparison | Compare briefs / insights / review contexts without mutating sources |
| Recommendation presentation | Present advisory recommendations with provenance and advisory labels |
| Review preparation | Structure human review packets from WP2.2 / WP3 artifacts |
| Feedback collection | Collect human-provided governance feedback as non-truth input only |
| Intelligence quality improvement | Improve presentation clarity, provenance visibility, and review UX — not model-runtime training loops |

### Feedback boundary (Condition 2 — CLOSED)

Feedback remains a **human-provided governance signal**.
Feedback is **not** an AI runtime capability.

**Allowed:**

- human review feedback
- bounded annotations
- explanation quality feedback
- presentation improvement feedback

**Forbidden:**

- autonomous learning loop
- self-training system
- hidden model optimization runtime
- shadow CRM fields
- merging into C21 HumanFeedback truth ownership
- using feedback to mutate C24 / CRM Core lifecycles

```text
Feedback = human governance signal
Feedback ≠ AI runtime / training / autonomous learning
```

### Transition invocation boundary (Condition 3 — CLOSED)

**Default WP4 scope:**

```text
Presentation + intent collection only
```

**WP4 does NOT:**

- execute workflow transitions
- mutate CRM lifecycle
- invoke C22 execution
- replace C24 lifecycle ownership

Human commercial enactment remains **outside C25** through the owning
layer’s governed services (ADR-C25-004).

**If future transition invocation is needed** (including C24 governed
transition service calls from a C25 surface):

- requires a **separate authorization gate**
- requires explicit Implementation Plan decision + Implementation Authorization
- must not be assumed from this charter alone

```text
Default = presentation + intent collection only
Silent transition invocation = NOT AUTHORIZED
Future transition invocation = separate gate
```

---

## 4. Non-Goals

### Runtime

Not in scope:

- connector execution
- provider invocation
- AIJob runtime
- queue
- worker
- scheduler

### AI

Not in scope:

- autonomous agent
- AI operator
- execution assistant
- autonomous decisions
- AI decision maker / autonomous decision engine

### Commercial

Not in scope:

- outbound execution
- sales automation
- Lead creation
- Opportunity mutation

### C22

Not in scope / no ownership transfer:

- ProspectRun
- Outreach
- Action Ledger
- prospect execution

### C24

Not in scope:

- lifecycle ownership
- entity replacement
- mutation of RevenueInsight / PipelineMetric / OpportunityCandidate

### C20

Not in scope:

- capability registry changes
- provider governance changes
- invariant activation

```text
WP4 (proposed) = decision support presentation
WP4 ≠ Runtime Expansion
WP4 ≠ C22/C24/CRM ownership
```

---

## 5. Ownership Boundary (Condition 5 — CLOSED)

| Owner | Owns |
| --- | --- |
| **C25** | Intelligence artifacts, presentation, advisory review support, decision-support surfaces |
| **C20** | Capability identity, purpose policy, provider governance |
| **C22** | Prospect execution |
| **C24** | `RevenueInsight`, `PipelineMetric`, `OpportunityCandidate` (and related commercial governance) |
| **CRM Core** | Customer lifecycle, opportunity lifecycle |

No ownership transfer across layers.

Human commercial decisions, if enacted, are enacted **outside C25** through the
owning layer’s governed services (per ADR-C25-004).

```text
C25 presents and collects intent.
C24 / CRM Core / C22 retain lifecycle and execution ownership.
```

---

## 6. AI Authority Boundary (Condition 4 — CLOSED)

Frozen definition for this charter and any later WP4 design:

**AI may:**

- summarize
- analyze
- classify
- propose
- explain

**AI may NOT:**

- decide
- approve
- execute
- mutate lifecycle

```text
AI = advisory support
Human reviewer / business user = final authority
```

---

## 7. Architecture Boundary

### Allowed (application layer)

- entities
- metadata
- read models
- services
- ACL
- provenance

### Forbidden

- connector
- provider runtime
- AIJob
- workers
- queues
- schedulers

Any future live-generation dependency requires separate Runtime Expansion /
execution authorization outside this charter.

---

## 8. Relationship With Existing WP

| Prior scope | Role relative to next WP |
| --- | --- |
| **C20** | Foundation only — identity / policy / governance references |
| **WP2.2** | CommercialBrief artifact layer — consume / present; do not replace |
| **WP3** | Commercial Intelligence Support Layer — consume CommercialInsight / BusinessReviewContext; do not absorb |
| **Next WP (WP4)** | Decision support presentation layer — extends prior surfaces; does **not** replace or absorb previous ownership |

```text
C20 foundation
    ↓
WP2.2 CommercialBrief (FROZEN)
    ↓
WP3 Commercial Intelligence Support (FROZEN)
    ↓
WP4 Commercial Decision Support Layer (APPROVED)
```

---

## 9. Success Criteria

Governance-level outcomes (not delivery KPIs):

- improved intelligence review readiness for humans
- improved provenance visibility in decision preparation
- improved human decision preparation from WP2.2 / WP3 artifacts
- improved explanation-quality feedback loop **without** transferring truth ownership

**Do NOT define success as:**

- autonomous execution success
- conversion automation
- outbound metrics
- Lead / Opportunity mutation rates
- provider runtime availability
- AI decision / approval rates

---

## 10. Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | CLOSED |
| C20 Package A | RELEASED |
| C25 WP2.0 | SATISFIED |
| WP2.2 CommercialBrief | FROZEN |
| WP3 Commercial Intelligence | FROZEN |
| WP3 Governance Closure | COMPLETE |
| WP4 Charter | **APPROVED** |
| WP4 Final Charter Review | **APPROVED** |
| WP4 Planning | **NOT AUTHORIZED** |
| WP4 Implementation | **NOT AUTHORIZED** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

```text
Charter APPROVED ≠ planning authorization
Charter APPROVED ≠ implementation authorization
Next gate: Implementation Plan drafting (documentation only).
```

---

## 11. Document Control

| Item | Value |
| --- | --- |
| Author role | WP4 charter governance owner |
| Mode | Documentation-only charter evidence |
| Condition closure record | `docs/audit/PHASE3C25_WP4_CHARTER_CONDITION_CLOSURE.md` |
| WP3 historical charter | `docs/PHASE3C25_WP3_CHARTER.md` |
| Production code changes | **NONE** |

---

*End of Phase3C25 Next WP Charter (APPROVED — no implementation authorization).*
