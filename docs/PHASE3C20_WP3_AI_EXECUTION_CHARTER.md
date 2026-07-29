# Phase3C20 WP3 AI Execution Charter

**Status:** Active — Charter only (implementation not authorized by this document alone)

**Date:** 2026-07-29

**Dependency freeze:** `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md` (**FROZEN**)

**Governing references:**
`docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`,
`docs/PHASE3C20_CHARTER.md`,
`docs/adr/C20_INVARIANT_REGISTRY.md`,
`AGENTS.md` / `CLAUDE.md`

---

## 1. Purpose

WP3 establishes C20 **AI execution governance** — tracking, evidence, prompt
control, cost visibility, and retry governance.

WP3 is:

- AI execution tracking
- AI request evidence
- Prompt governance
- Cost visibility
- Retry governance

WP3 is **not**:

- an AI Sales Agent
- an autonomous prospecting / acquisition pipeline
- a scoring or qualification engine
- an outreach automation system

EspoCRM remains the workflow / governance layer. Chitu remains intelligence
authority. External providers execute AI/search/enrichment/completion.
The connector remains sole egress.

---

## 2. Dependency

WP3 depends on the frozen WP2 Capability Registry Resolution Contract:

```text
docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md
```

### 2.1 Execution flow

```text
AIJob
 ↓
CapabilityResolution
 ↓
Provider Adapter
 ↓
External Provider
```

Rules:

- `AIJob` may dispatch only after capability resolution against CRM-authorized
  bindings.
- Resolution result metadata is audit / provenance input for `AIRequestLog`.
- Resolution result is **not** a business decision.

WP3 must not reopen or amend the frozen WP2 registry contract without a new
decision record.

---

## 3. Included Entities

### 3.1 AIJob

**Definition:** one unit of AI execution work and its lifecycle.

Owns:

- status
- execution timing
- provider resolution reference
- result reference
- error reference

Does **not** own:

- lead decision
- qualification
- lifecycle transition of Prospecting entities

Status mutation must follow the C19/C20 transition-service + guard pattern
(ADR-C20 §7). Autonomous triggering is forbidden in C20.

### 3.2 AIRequestLog

**Definition:** append-only execution evidence for provider invocations.

Records:

- provider
- model
- tokens
- cost
- latency
- error classification

Must not contain:

- secrets
- raw credentials
- business authority / qualification verdicts / scores

### 3.3 PromptTemplate

**Definition:** versioned prompt governance artifact.

Rule:

- Once referenced by an `AIRequestLog` (or equivalent execution evidence row),
  the referenced version is **immutable**.
- Corrections create a new version; history is preserved.

---

## 4. Append-only Policy

### 4.1 Phase-1 enforcement (required for WP3 exit)

Application-layer guarantees:

- no update API for `AIRequestLog`
- no delete API for `AIRequestLog`
- service / guard rejection of mutation paths
- contract tests proving append-only behaviour

### 4.2 Database-level enforcement

**Deferred.**

WP3 must **not** require:

- SQL `REVOKE`
- database triggers
- DBMS-native immutability mechanisms

as exit criteria for the first WP3 delivery.

---

## 5. Retry Governance

Allowed:

- retry eligibility classification
- failure classification using the existing taxonomy
- operator-visible failed jobs with authorized recovery paths (ADR-C20 §7)

Forbidden automatic bypass of:

- auth failure
- validation failure
- content filter
- approval requirement

Retry must not become autonomous outreach, scoring, or lifecycle mutation.

---

## 6. Explicitly Excluded

### 6.1 Business Intelligence — forbidden

- `CandidateScore`
- `AIScore`
- qualification authority / verdict calculation in EspoCRM

Chitu remains sole scoring and qualification authority.

### 6.2 Agent Memory — forbidden

- `AgentMemory`
- any external memory that overrides CRM facts

### 6.3 C22 Automation — forbidden in WP3

- `AutomationRule`
- `ActionLedger`
- `HumanHandoff` implementation

These remain C22 concerns.

### 6.4 Outreach — forbidden

- Email sending
- `SendExecution` modification
- Approval workflow modification

### 6.5 Lifecycle — forbidden

- Lead transition driven by AI
- Opportunity movement driven by AI

AI output remains advisory / evidence unless a human-authorized workflow
explicitly acts.

---

## 7. Entity Decisions

| Entity | Decision |
| --- | --- |
| `AIJob` | Include |
| `AIRequestLog` | Include |
| `PromptTemplate` | Include |
| `AIProviderUsage` | Deferred |
| `AIExecutionPolicy` | Deferred |
| `CandidateScore` | Rejected |
| `AgentMemory` | Rejected |
| `ActionLedger` | Deferred C22 |
| `AutomationRule` | Deferred C22 |

Notes:

- Advisory `AIQualificationInsight` remains governed by ADR-C20 §6.4 / §8 and
  is outside this charter's first-include table unless separately authorized by
  the C20 charter WP3 scope with full immutability constraints.
- Rejected entities must not be introduced under WP3 naming variants.

---

## 8. Exit Criteria

WP3 is complete only when all of the following are satisfied:

| # | Criterion |
| --- | --- |
| E1 | `AIJob` lifecycle tests (matrix, guards, authorization) |
| E2 | `AIRequestLog` append-only tests |
| E3 | `PromptTemplate` immutability tests |
| E4 | Capability Registry integration (WP2 freeze contract) |
| E5 | Error taxonomy reuse (no parallel error system) |
| E6 | Cost metadata validation on request evidence |
| E7 | No unauthorized external egress from PHP |
| E8 | C20 invariant verification for WP3-owned ACTIVE invariants |

Canonical suite green under `pytest -q` remains a standing gate.

---

## 9. ADR Impact

| Statement | Decision |
| --- | --- |
| WP3 implements ADR-C20 | **Yes** |
| WP3 amends ADR-C20 | **No** |

WP3 executes the architecture already decided in ADR-C20 (entities, lifecycle,
invariants, sole-egress boundary). Any ADR text change requires a separate
amendment decision and is out of scope for this charter.

---

## 10. Authorization Boundary

This charter:

- freezes WP3 governance scope
- authorizes planning and bounded implementation of included entities only
- does **not** authorize C21 outreach, C22 automation, scoring, or agent memory
- does **not** authorize bypass of `AGENTS.md` / `CLAUDE.md` prohibitions

Implementation work must cite:

1. this charter
2. WP2 Capability Registry Freeze
3. ADR-C20 relevant sections / invariants

---

*Charter only. Documentation. No PHP, Python, metadata, test, release, or
artifact changes are made by this document. No WP3 entities are created by
this commit.*
