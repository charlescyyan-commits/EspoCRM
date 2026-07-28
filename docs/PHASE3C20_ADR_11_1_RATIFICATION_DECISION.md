# Phase3C20 ADR-C20 §11.1 — Human Ratification Decision

## 1. Status

**Status:** RATIFIED — OPTION C (Restricted Capability Portfolio)
**Date:** 2026-07-28
**Type:** Governance ratification — documentation only
**Gates:** ADR-C20 §11.1 resolved; WP2 authorized under binding constraints

## 2. Governing Documents

| Document | Role |
|----------|------|
| `AGENTS.md` / `CLAUDE.md` | Authoritative — take precedence over ADR-C20 until formally amended |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | Proposed architecture; §11.1 unresolved |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | 22-invariant machine-checkable registry |
| `docs/PHASE3C20_CHARTER.md` | Active C20 charter; WP2 gated on this ratification |
| `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` | WP1 exit evidence; F4: §11.1 unresolved |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_CHECKLIST.md` | Prerequisite verification; READY FOR RATIFICATION |
| `docs/architecture/BOUNDARIES.md` | System boundaries; scoring and live runtime out of scope |

## 3. Baseline

- **C20 Charter WP1 exit tag:** `phase3c20-wp1-exit` (`2bc0269`)
- **WP1 exit status:** WP1 READY FOR EXIT (reconciliation audit, 2026-07-28)
- **Preparation audit:** `docs/PHASE3C20_ADR_11_1_RATIFICATION_CHECKLIST.md` (`7ccc385`)
- **ADR-C20 marker:** `adr-c20-aiplatform-v1`

## 4. The Question

ADR-C20 §11.1 asks:

> **Does a new `CompletionProvider` adapter in the connector violate
> `AGENTS.md`'s prohibition on modifying AI research logic?**

### 4.1 What AGENTS.md Forbids

```
- Modify Chitu scoring logic
- Modify AI research logic
- Modify the email-generation engine
- Modify unrelated Chitu application code
```

### 4.2 The ADR's Position (ADR-C20 §2 D4, Option C)

The ADR takes the position that adding a **new, separately-owned** adapter for
a capability Chitu does **not** own is not a modification of Chitu's existing
logic. The prohibition protects Chitu's code — it does not prevent the creation
of new capability under separate ownership in the connector.

### 4.3 Why This Must Be Escalated

The ADR itself records: *"That reading is not self-evident and must be ratified
by a human owner before WP2 begins."* And: *"An AI agent must not resolve this
in its own favour."*

The question is whether `AGENTS.md` prohibits **any** new AI invocation path,
even one that does not touch Chitu's code. That is a repo-level governance
constraint — not a technical decision — and requires human judgment.

## 5. Decision Options

### Option A — YES (Ratify Option C) ✅ SELECTED

> **A new `CompletionProvider` adapter for capabilities Chitu does not own
> does NOT violate `AGENTS.md`.**

**Rationale:** The `AGENTS.md` prohibitions protect Chitu's existing scoring,
research, and email-generation logic. A `CompletionProvider` adapter in the
connector that invokes an LLM for a purpose Chitu does **not** own (e.g.,
summarization of CRM data, operator-facing explanation, non-prospecting
classification) is a **new capability under separate ownership**. It does not
modify, replace, intercept, or compete with Chitu's code.

**WP2 scope with this decision:**

| Capability port | Status |
|-----------------|--------|
| `SearchProvider` | Proceed — Apify, Serper adapters exist |
| `EnrichmentProvider` | Proceed — Apollo, Hunter adapters |
| `CompletionProvider` | **Proceed** — new connector adapter, capabilities Chitu does not own |

C20-INV-12 and C20-INV-13 activate under WP2.

### Option B — NO (Option B)

> **A `CompletionProvider` adapter IS a violation of `AGENTS.md`. No LLM
> invocation path may be added to EspoCRM under C20.**

**Rationale:** `AGENTS.md` prohibits modifying AI research logic. Adding any
LLM invocation path — even for a capability Chitu does not own — expands the
AI research footprint and could be used to replicate or augment Chitu's
research. The prohibition is interpreted broadly: no new AI model invocation
from EspoCRM. All AI must arrive from Chitu.

**WP2 scope with this decision:**

| Capability port | Status |
|-----------------|--------|
| `SearchProvider` | Proceed — Apify, Serper adapters exist |
| `EnrichmentProvider` | Proceed — Apollo, Hunter adapters |
| `CompletionProvider` | **Removed from C20 portfolio** |

C20-INV-12 and C20-INV-13 activate under WP2, scoped to search and enrichment
adapters only.

## 6. Binding Constraints — Either Outcome

The following constraints bind WP2 **regardless** of the decision above. They
derive from `AGENTS.md`, ADR-C20, `BOUNDARIES.md`, and the C20 Charter and are
not subject to this ratification — they are already in force.

### 6.1 AGENTS.md (Absolute)

| # | Prohibition |
|---|-------------|
| A1 | Do not modify Chitu scoring logic — `canonical_score.py`, `scoring.py`, or any scoring code |
| A2 | Do not modify Chitu AI research logic — `website_research.py`, `single_candidate_loop.py`, or any research code |
| A3 | Do not modify the email-generation engine |
| A4 | Do not modify unrelated Chitu application code |
| A5 | No real customer data without explicit approval |

### 6.2 ADR-C20 (In Force)

| # | Constraint |
|---|------------|
| C1 | Connector is sole egress — no HTTP from PHP to any provider domain (§2 D3) |
| C2 | Chitu owns `canonical_score` — no `AIScore` entity; no score computation (§6.3, C20-INV-14) |
| C3 | Chitu owns qualification decisions — EspoCRM must not calculate qualification verdicts (C20-INV-21) |
| C4 | No email-sending path in C20 (C20-INV-15) |
| C5 | C19 lifecycle services, guards, and action keys are frozen — zero changes (Charter §6) |
| C6 | No autonomous AI trigger — every invocation is operator-initiated (§10) |
| C7 | No adapter constructed without explicit transport; no default transport (C20-INV-12) |
| C8 | Dry-run mode produces complete trace with zero network egress (C20-INV-13) |

### 6.3 BOUNDARIES.md

| # | Constraint |
|---|------------|
| B1 | Live Engine / DeepSeek / crawler runtime: out of scope — must not be imported (§2) |
| B2 | Scoring logic changes: forbidden (§2) |
| B3 | Connector never writes SQL or PHP metadata; extension never imports Python (§1) |

### 6.4 C20 Charter §6

C20 must NOT:
- Modify C19-frozen lifecycle services, guards, or action keys
- Compute a score or create a second scoring/qualification authority
- Ship any email-sending path
- Open outbound provider connections from PHP

## 7. WP2 Authorization Conditions

WP2 implementation may begin **only after** all of the following are satisfied:

1. This document is signed by the human owner with a YES or NO decision.
2. The C20 Charter §9 decision log records the outcome.
3. ADR-C20 §11.1 is amended to reflect the ratified decision.
4. If YES: the `CompletionProvider` scope definition is recorded (which
   capabilities it serves, which it does not).
5. If NO: `CompletionProvider` is removed from the ADR-C20 §4.1 capability
   table and the C20 Charter §4 WP2 scope description.
6. The C20 Invariant Registry activation plan for C20-INV-12 and C20-INV-13
   reflects the scoped outcome.

## 8. WP2 Scope Boundaries — Either Outcome

WP2 must **not** reach into:

| Territory | Owning WP | Rationale |
|-----------|-----------|-----------|
| `AIJob`, `AIRequestLog`, `PromptTemplate` | WP3 | Entity model and lifecycle |
| Cost accounting, health checks | WP3 | Governance infrastructure |
| `AIQualificationInsight` entity | WP3 | Advisory layer with full immutability |
| Test infrastructure completion, `BUILD_INFO` | WP4 | Provenance and canonical invocation |
| Vertical slice, `ResearchEvidence` writes | WP5 | Operator-triggered research |
| `EmailDeliveryProvider` | C21 | Email sending |
| Auto-approval, autonomous outreach | C22 | Policy automation |

## 9. Compliance

After ratification, any AI agent working on C20 WP2 must:

- Cite the ratified §11.1 decision before creating any provider adapter.
- Never create a `CompletionProvider` if the decision is NO.
- Never create an adapter that duplicates a Chitu-owned capability (A2, A4).
- Never open an HTTP connection from PHP (C1).
- Never create an `AIScore` entity or compute a score (C2).
- Maintain the connector as sole egress with explicit transport injection (C7).
- Include recorded-fixture dry-run coverage for every new adapter (C8).

Violation of any binding constraint in §6 is a governance break regardless of
the §11.1 outcome.

## 10. Human Owner Ratification

### Decision

**Owner:** Charles

**Date:** 2026-07-28

**Decision (select one):**

- [x] **YES** — A new `CompletionProvider` adapter for capabilities Chitu does
  not own does NOT violate `AGENTS.md`. WP2 may proceed with the full C20
  capability portfolio including `CompletionProvider`.

- [ ] **NO** — A `CompletionProvider` adapter IS a violation of `AGENTS.md`.
  WP2 proceeds with `SearchProvider` and `EnrichmentProvider` only.
  `CompletionProvider` is removed from the C20 portfolio. All AI must arrive
  from Chitu.

### Approval Meaning

EspoCRM is authorized to orchestrate AI-assisted prospecting workflows,
including:

- AI research evidence presentation
- AI qualification insights
- AI draft assistance
- Human approval workflows
- Reply classification support
- AI-assisted sales operations

### Binding Constraints

1. **Chitu Intelligence remains the intelligence authority.** Chitu owns
   `canonical_score`, ICP matching, qualification logic and verdicts, research
   logic, and intelligence generation. EspoCRM consumes and persists — it never
   reimplements or competes.

2. **EspoCRM remains the workflow, governance, audit, and human-control
   layer.** Orchestration, permissions, persistence, audit trail, operator
   recovery, and human decision gates are EspoCRM's domain.

3. **AI insights are advisory and cannot become authoritative CRM lifecycle
   decisions.** No AI-generated output may drive a status transition, queue
   predicate, or lifecycle mutation without human approval.

4. **EspoCRM does not own AI model execution.** All model invocation routes
   through the connector (sole egress). No PHP code opens an HTTP connection to
   any AI provider.

5. **EspoCRM does not directly call external AI/provider APIs.** Provider
   routing is configuration, not code. The connector is the single integration
   surface for all outbound AI I/O.

6. **Provider credentials remain outside CRM custody.** EspoCRM holds
   credential metadata, ownership, rotation schedule, and audit trail —
   references only. The connector holds actual secrets in its environment.

7. **Human approval remains required for external actions.** No autonomous
   outreach, no automatic email sending, no unattended provider invocation.
   Every C20 invocation is operator-initiated.

### Interpretation Guidance

The `AGENTS.md` prohibition on modifying "AI research logic" protects Chitu's
existing research pipeline — `website_research.py`,
`single_candidate_loop.py`, and the vendored contracts under
`chitu_connector/vendored/contracts/`. It does **not** prohibit creating new,
separately-owned AI capability in the connector that serves purposes Chitu does
not own.

A `CompletionProvider` adapter must serve **only** capabilities that fall
outside Chitu's ownership scope. It must not:

- Replicate or augment Chitu's research pipeline
- Generate scores that compete with `canonical_score`
- Produce qualification verdicts
- Generate email content that bypasses the DraftApproval workflow
- Operate autonomously without operator initiation

If a proposed `CompletionProvider` use case touches any Chitu-owned capability,
it must be escalated back to the human owner for a separate ratification.

### Signature

**Approved by:** Charles

**Date:** 2026-07-28

## 11. Post-Ratification Actions

| Action | Status |
|--------|--------|
| This document signed by the human owner with a YES decision | ✅ Complete — Charles, 2026-07-28 |
| Record decision in C20 Charter §9 decision log | Pending — AI agent |
| Amend ADR-C20 §11.1 header with outcome | Pending — AI agent |
| Document `CompletionProvider` capability scope (allowed and forbidden use cases) | Pending — before WP2 begins |
| Begin WP2 implementation | Authorized — after scope documentation |
| Close §11.1 in governance tracking | Pending — AI agent |

## 12. Related

- `docs/PHASE3C20_ADR_11_1_RATIFICATION_CHECKLIST.md` — full prerequisite audit
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §11.1 — the gating question
- `docs/PHASE3C20_CHARTER.md` §4 — WP2 scope description
- `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` — WP1 exit evidence

---

*ADR-C20 §11.1 is ratified. Option C (Restricted Capability Portfolio) is the
governing decision. WP2 is authorized under the seven binding constraints
recorded in §10. The CompletionProvider capability scope must be documented
before WP2 implementation begins.*
