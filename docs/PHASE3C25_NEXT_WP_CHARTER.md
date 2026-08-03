# Phase3C25 Next Work Package Charter — Draft

| Field | Value |
| --- | --- |
| Document Type | Next WP Charter (architecture planning only) |
| Proposed Work Package | **WP4 — Commercial Decision Support Layer** |
| ADR alignment | ADR-C25-004 Human Decision Workspace Architecture (presentation / intent-collection surface) |
| Parent | Phase3C25 — AI Commercial Intelligence Layer |
| Status | **DRAFT** |
| Date | 2026-08-04 |
| Baseline | C20 CLOSED; Package A RELEASED; WP2.0 SATISFIED; WP2.2 FROZEN (`phase3c25-wp2-2-freeze`); WP3 FROZEN + GOVERNANCE CLOSED (`phase3c25-wp3-freeze`) |
| Planning Authorization | **NO** while DRAFT |
| Implementation Authorization | **NO** |
| Commit / push / tag | **NOT AUTHORIZED** by this draft |

```text
This charter defines the next C25 commercial-intelligence work package
after WP3 freeze and post-freeze governance closure.

As DRAFT it authorizes nothing.
It does NOT authorize planning, implementation, delivery,
Runtime Expansion, C20 reopening, C22/C24 ownership transfer,
or invariant activation.
```

**Prior WP3 charter (historical):** `docs/PHASE3C25_WP3_CHARTER.md`

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

## 2. Proposed WP Name

**Phase3C25 WP4 — Commercial Decision Support Layer**

Governance-safe naming (avoids Agent / Autonomous / Operator / Automation).

**Naming equivalence (explicit):**

```text
Commercial Decision Support Layer
  = ADR-C25-004 Human Decision Workspace
    (implementation-facing name for the same presentation / intent-collection surface)
```

Aligned with ratified C25 Implementation Charter WP4 and ADR-C25-004
as a C25-owned **presentation / intent-collection** surface — not as a
decision owner or lifecycle owner.

Alternate considered (deferred as secondary theme, not primary WP title):

- Intelligence Quality and Feedback Layer (may appear as a facet under ADR-C25-006 constraints)

---

## 3. Scope

Allowed **application intelligence** scope (planning candidates only while DRAFT):

| Area | Intent |
| --- | --- |
| Decision support context | Present assembled commercial context for human decision preparation |
| Insight comparison | Compare briefs / insights / review contexts without mutating sources |
| Recommendation presentation | Present advisory recommendations with provenance and advisory labels |
| Review preparation | Structure human review packets from WP2.2 / WP3 artifacts |
| Feedback collection | Collect explanation-quality / usefulness feedback as non-truth input only |
| Intelligence quality improvement | Improve presentation clarity, provenance visibility, and review UX — not model-runtime training loops |

### Feedback boundary (explicit)

**Allowed:**

- bounded review intent
- annotations
- presentation / explanation-quality feedback

**Forbidden:**

- model training loop
- autonomous learning
- shadow CRM fields
- merging into C21 HumanFeedback truth ownership
- using feedback to mutate C24 / CRM Core lifecycles

### Transition invocation (explicit — no silent expansion)

WP4 charter default (DRAFT):

```text
Presentation / intent collection only
```

Human commercial enactment remains **outside C25** through the owning
layer’s governed services (ADR-C25-004).

**C24 governed transition invocation** is **not** authorized by this DRAFT.
Any later design that would invoke C24 transition services from a C25 surface
requires an explicit Implementation Plan decision and separate Implementation
Authorization — it must not be assumed from this charter alone.

```text
Allowed = present, prepare, compare, collect intent / quality feedback
Forbidden = decide, approve, execute, mutate owned lifecycles
Silent C24 transition invocation = NOT AUTHORIZED by this DRAFT
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

## 5. Ownership Boundary

| Owner | Owns |
| --- | --- |
| **C25** | Intelligence artifacts, presentation, advisory review support, decision-support surfaces |
| **C20** | Capability identity, purpose policy, provider governance |
| **C22** | Prospect execution |
| **C24** | Commercial intelligence source entities (`OpportunityCandidate`, `RevenueInsight`, `PipelineMetric`, related governance) |
| **CRM Core** | Customer / opportunity lifecycle |

No ownership transfer across layers.

Human commercial decisions, if enacted, are enacted **outside C25** through the
owning layer’s governed services (per ADR-C25-004).

---

## 6. AI Authority Boundary

Frozen definition for this charter and any later WP4 design:

**AI may:**

- summarize
- analyze
- classify
- propose

**AI may not:**

- decide
- approve
- execute
- mutate lifecycle

```text
AI = advisory support
Human = final authority
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
WP4 Commercial Decision Support Layer (this charter — DRAFT)
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

---

## 10. Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | CLOSED |
| C20 Package A | RELEASED |
| C25 WP2.0 | SATISFIED |
| WP2.2 CommercialBrief | FROZEN |
| WP3 Commercial Intelligence | FROZEN |
| Next WP Charter | **DRAFT** |
| Next WP Planning | **NOT AUTHORIZED** |
| Next WP Implementation | **NOT AUTHORIZED** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

```text
This DRAFT authorizes nothing.
Charter review → Implementation Plan → Implementation Authorization
remain separate future gates.
```

---

## 11. Document Control

| Item | Value |
| --- | --- |
| Author role | Architecture governance owner |
| Mode | Documentation only |
| WP3 historical charter | `docs/PHASE3C25_WP3_CHARTER.md` |
| Commit of this draft | **NOT DONE** unless separately authorized |
| Production code changes | **NONE** |

---

*End of Phase3C25 Next WP Charter (DRAFT — no authorization).*
