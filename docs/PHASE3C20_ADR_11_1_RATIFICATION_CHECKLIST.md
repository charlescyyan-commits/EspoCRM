# Phase3C20 ADR-C20 §11.1 Ratification Checklist

## 1. Status

**Verdict:** READY FOR RATIFICATION  
**Date:** 2026-07-28  
**Type:** Read-only governance audit — no implementation changes  
**Phase:** Phase3C20 — ADR-C20 §11.1 human-owner ratification gate

## 2. Audit Baseline

| Artefact | Reference | State |
|----------|-----------|-------|
| ADR-C20 | `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | Proposed (not accepted) |
| C20 Invariant Registry | `docs/adr/C20_INVARIANT_REGISTRY.md` | Active — 22 invariants, 9 ACTIVE / 13 DEFERRED |
| C20 Charter | `docs/PHASE3C20_CHARTER.md` | Active |
| WP0 Exit | Tag `phase3c20-wp0-exit` (`78b85bf`) | Complete |
| WP1 Exit | Tag `phase3c20-wp1-exit` (`2bc0269`) | Complete — WP1 READY FOR EXIT |
| WP1 Exit Reconciliation | `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` | Complete |
| WP1.3.3 Runtime Verification | `docs/PHASE3C20_WP1_3_3_RUNTIME_VERIFICATION.md` | Complete |
| AGENTS.md / CLAUDE.md | Repo root | Governing — authoritative over ADR-C20 |
| BOUNDARIES.md | `docs/architecture/BOUNDARIES.md` | Static verified |

## 3. The Question

ADR-C20 §11.1 asks a single question that blocks WP2:

> **Does a new `CompletionProvider` adapter in the connector violate
> `AGENTS.md`'s prohibition on modifying AI research logic?**

`AGENTS.md` states verbatim under **Forbidden**:

> - Modify Chitu scoring logic
> - Modify AI research logic
> - Modify the email-generation engine

ADR-C20 §2 D4 takes the position that adding a **new, separately-owned** adapter
for a capability Chitu does **not** own is not a modification of Chitu's
existing logic — the prohibition protects Chitu's code, not the creation of new
capability under separate ownership.

**This reading requires explicit human-owner ratification before WP2 begins.**
An AI agent must not resolve this question in its own favour.

## 4. The Two Possible Outcomes

### 4.1 Ratification — YES (Option C)

The `CompletionProvider` does **not** violate `AGENTS.md`. Adding a new
separately-owned adapter for a capability Chitu does not own is a distinct
concern from modifying Chitu's existing AI research logic.

WP2 proceeds with the full ADR-C20 capability portfolio:

| Port | Method | Candidate implementations |
|------|--------|---------------------------|
| `SearchProvider` | `search(SearchRequest) → ProviderResult` | Apify, Serper |
| `EnrichmentProvider` | `enrich(EnrichmentRequest) → EnrichmentResult` | Apollo, Hunter |
| `CompletionProvider` | `complete(CompletionRequest) → CompletionResult` | New connector adapter |

C20-INV-12 and C20-INV-13 move toward activation as WP2 delivers its scope.

### 4.2 Ratification — NO (Option B)

The `CompletionProvider` **is** a prohibited extension of AI research logic.
Adding any LLM invocation path, even for a capability Chitu does not own,
constitutes modifying the AI research boundary and violates `AGENTS.md`.

WP2 narrows:

- `EnrichmentProvider` adapter only — no completion adapter
- All AI must arrive from Chitu; EspoCRM never invokes a model
- `CompletionProvider` is removed from the C20 capability portfolio
- C20-INV-12 and C20-INV-13 remain DEFERRED for WP2
- Any future LLM invocation requires a separate ADR amendment and ratification

## 5. Non-Negotiable Architecture Invariants

The following constraints bind WP2 **regardless of the §11.1 outcome**. They
derive from `AGENTS.md`, ADR-C20, and `BOUNDARIES.md` and are not subject to
ratification — they are already in force.

### 5.1 AGENTS.md Prohibitions (unchanged, unchallengeable)

| # | Prohibition | Scope |
|---|-------------|-------|
| A1 | Do not modify Chitu scoring logic | Absolute — any change to `canonical_score.py`, `scoring.py`, or related scoring code is forbidden |
| A2 | Do not modify AI research logic | Absolute — any change to `website_research.py`, `single_candidate_loop.py`, or related research code is forbidden |
| A3 | Do not modify the email-generation engine | Absolute — any change to email composition/generation in Chitu is forbidden |
| A4 | Do not modify unrelated Chitu application code | Absolute — `chitu_connector` imports only `vendored/` stable interfaces |
| A5 | No real customer data without explicit approval | Absolute — fixtures and synthetic records only |

### 5.2 ADR-C20 Architectural Invariants (in force)

| Invariant | Requirement | Status |
|-----------|-------------|--------|
| C20-INV-01 | Marker `adr-c20-aiplatform-v1` in AIPlatform metadata | Delivered (WP1), registry label DEFERRED |
| C20-INV-02 | No Prospecting identifier in AIPlatform | ACTIVE |
| C20-INV-03 | No outbound HTTP from PHP | ACTIVE |
| C20-INV-04 | No plaintext credential exposure | Delivered (WP1), registry label DEFERRED |
| C20-INV-12 | No adapter without explicit transport; no default transport | DEFERRED (WP2, §11.1 gated) |
| C20-INV-13 | Dry-run mode with zero network egress | DEFERRED (WP2) |
| C20-INV-14 | No `AIScore` entity; Chitu owns `canonical_score` | ACTIVE |
| C20-INV-15 | No email-sending path in C20 | ACTIVE |
| C20-INV-21 | EspoCRM must not calculate qualification verdicts | ACTIVE |

### 5.3 ADR-C20 §2 D3 — Sole Egress

**All outbound provider I/O goes through the connector.** No PHP code in
`Modules/AIPlatform` or `Modules/Prospecting` opens an HTTP connection to any
provider domain. This is absolute regardless of §11.1 outcome.

### 5.4 ADR-C20 §2 D2 — Custody Model

Chitu owns scoring, ICP, qualification, research, email generation. EspoCRM
governs, orchestrates, audits. **A `CompletionProvider` adapter, if ratified,
serves capabilities Chitu does not own — it does not reimplement Chitu logic.**

### 5.5 BOUNDARIES.md — Live Runtime

`BOUNDARIES.md` §2: Live Engine / DeepSeek / crawler runtime is **Out of scope
— must not be imported**. Scoring logic changes are **Forbidden per AGENTS.md**.

### 5.6 C20 Charter §6

C20 must NOT:
- Modify C19-frozen lifecycle services, guards, or action keys
- Compute a score or create a second scoring/qualification authority
- Ship any email-sending path
- Open outbound provider connections from PHP

## 6. WP2 Forbidden Scope — Before §11.1 Ratification

The following are **strictly forbidden** until a human owner ratifies §11.1:

| # | Forbidden item | Rationale |
|---|---------------|-----------|
| F1 | `CompletionProvider` connector adapter | The gated item — cannot be created until §11.1 resolves |
| F2 | Any LLM completion/invocation path from EspoCRM | Dependent on F1; no completion adapter means no completion calls |
| F3 | Direct model invocation from PHP (OpenAI, Anthropic, DeepSeek, Moonshot, any vendor) | Violates D3 (sole egress) regardless of §11.1 |
| F4 | Any adapter that duplicates a Chitu-owned capability | Violates A2, A4, and D2 |
| F5 | Modification of `chitu_connector` vendored contracts | Violates A4 |
| F6 | `AIJob` orchestration, `AIRequestLog`, `PromptTemplate`, cost accounting, health checks | These are WP3, not WP2 — out of sequence |
| F7 | Any adapter that writes SQL, PHP metadata, or any CRM-side state from the connector | Violates BOUNDARIES.md §1 |

### 6.1 Conditional Forbidden — If §11.1 Is Denied

If ratification outcome is **NO (Option B)**, these additional items are
permanently forbidden in C20:

| # | Forbidden item |
|---|---------------|
| F8 | `CompletionProvider` — removed from C20 capability portfolio entirely |
| F9 | Any LLM model invocation path from EspoCRM (any language, any stack) |
| F10 | Any capability that would route through `CompletionProvider` |

### 6.2 Unconditionally Forbidden — Never in Scope

These are out of scope for all of C20 regardless of §11.1:

| # | Forbidden item | Source |
|---|---------------|--------|
| U1 | Any email sending (no `EmailDeliveryProvider`, no send action) | §§8.15, 10 |
| U2 | Any scoring computation (`AIScore` entity) | §6.3 |
| U3 | Any autonomous AI trigger | §10 |
| U4 | `Modules/Automation` | §2 D1 |
| U5 | `EmailCampaign`, `EmailAccount` | §10 |
| U6 | Auto-approval or policy guard | §10 (C22) |
| U7 | Real customer data | A5 |
| U8 | Modification of C19 lifecycle services, guards, or action keys | C20 Charter §6 |

## 7. WP2 Allowed Scope — After §11.1 Ratification

### 7.1 If Ratified YES (Option C)

WP2 scope per ADR-C20 §10 and C20 Charter §4:

| # | Allowed item | Gated by |
|---|-------------|----------|
| W1 | Capability ports: `SearchProvider`, `EnrichmentProvider`, `CompletionProvider` | §11.1 ratified |
| W2 | `EnrichmentProvider` adapter (Apollo, Hunter) | — |
| W3 | `CompletionProvider` adapter — new connector adapter for capabilities Chitu does NOT own | §11.1 ratified |
| W4 | Recorded-fixture tests for all provider adapters | — |
| W5 | C20-INV-12 enforcement (no default transport; explicit injection required) | — |
| W6 | C20-INV-13 enforcement (dry-run mode with zero network egress) | — |
| W7 | Provider route configuration metadata (capability → provider + model) | — |
| W8 | Provider capability declarations (streaming, JSON mode, max context, vision) | — |

### 7.2 If Ratified NO (Option B)

WP2 narrows to:

| # | Allowed item |
|---|-------------|
| W1' | `EnrichmentProvider` port and adapter only |
| W2' | `SearchProvider` port (already has Apify/Serper adapters in connector) |
| W3' | Recorded-fixture tests for enrichment and search adapters |
| W4' | C20-INV-12 and C20-INV-13 enforcement (adapter-scoped) |
| W5' | Provider route metadata — enrichment and search capabilities only |

### 7.3 WP2 Scope Boundaries (either outcome)

WP2 must NOT reach into:

- **WP3 territory:** `AIJob`, `AIRequestLog`, `PromptTemplate`, cost accounting, health checks, `AIQualificationInsight`
- **WP4 territory:** Test infrastructure completion, `BUILD_INFO`
- **WP5 territory:** Vertical slice, `ResearchEvidence` writes
- **C21 territory:** `EmailDeliveryProvider`, email sending
- **C22 territory:** Auto-approval, autonomous outreach

## 8. Open Governance Questions

### 8.1 §11.2 — Non-blocking Questions

These ADR-C20 §11.2 items have stated defaults and do not gate WP2. They should
be closed before WP3 begins:

| # | Question | Default if unresolved | Status |
|---|----------|----------------------|--------|
| Q1 | Does EspoCRM hold any secret, or only credential references? | References only — stricter posture | Open |
| Q2 | Is `AIJob` dispatch synchronous-with-timeout or queue-backed? | Queue-backed via Espo scheduled jobs | Open |
| Q3 | Does `ProviderHealth` drive automatic failover in C20, or advisory only? | Advisory only | Open |
| Q4 | Are prompt templates per-tenant or global? | Global; revisit if multi-tenant emerges | Open |
| Q5 | Cost ceiling scope: per capability, per user, or global? | Per capability plus global hard cap | Open |

### 8.2 WP1 Reconciliation Observations

Carried forward from `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` findings F1/F2:

| # | Observation | Recommendation |
|---|-------------|---------------|
| F1 | C20-INV-01 remains DEFERRED in registry despite activation trigger met | Update to ACTIVE; reference `test_phase3c20_wp1_1_aiplatform_namespace_skeleton.py` |
| F2 | C20-INV-04 remains DEFERRED in registry despite activation trigger met | Update to ACTIVE; reference `test_phase3c20_wp1_2_providercredential.py` |

These are governance housekeeping — the enforcement evidence is on disk. They
do not gate WP2.

### 8.3 Connector Ownership Boundary

An unresolved meta-question for WP2 regardless of §11.1 outcome:

> Does adding a new `EnrichmentProvider` adapter to the connector constitute
> "modifying AI research logic"?

The ADR authors took the position that it does **not** — enrichment is a data
lookup (Apollo, Hunter), not research or scoring. This reading was not
explicitly escalated to §11.1 because enrichment does not invoke an LLM. If the
human owner considers enrichment a form of AI research, WP2 scope narrows
further — to `SearchProvider` only.

## 9. State of Prerequisites

| Prerequisite | Status | Detail |
|-------------|--------|--------|
| WP0 complete | ✓ | Tag `phase3c20-wp0-exit` at `78b85bf` |
| WP1 complete | ✓ | Tag `phase3c20-wp1-exit` at `2bc0269`; WP1 READY FOR EXIT |
| WP1.3.3 runtime verification | ✓ | 10/10 runtime checks passed |
| WP1 exit reconciliation | ✓ | All charter criteria met; 27 contract tests pass |
| 22-invariant registry | ✓ | Machine-checkable; 9 ACTIVE / 13 DEFERRED |
| WP1 boundary verified | ✓ | No Prospecting reference, no secret field, no runtime surface, no WP2 leak |
| `credentialReference` write-only | ✓ | 4 enforcement layers (entityAcl, layouts, UI i18n, runtime path) |
| AIPlatform isolation from Prospecting | ✓ | 3 independent gate tests |
| ADR-C20 §11.1 blocker acknowledged | ✓ | Noted in WP1 Charter, WP1 Exit Reconciliation, C20 Charter §8 O8 |

All prerequisites for the ratification decision are satisfied. The only open
item is the human owner's answer to the §11.1 question.

## 10. Ratification Protocol

### 10.1 Required Decision

The human owner must record one of:

> **YES** — A new `CompletionProvider` adapter for capabilities Chitu does not
> own does NOT violate `AGENTS.md`. WP2 may proceed with the full ADR-C20
> capability portfolio including `CompletionProvider`.

or:

> **NO** — A `CompletionProvider` adapter IS a violation of `AGENTS.md`. WP2
> proceeds with enrichment and search ports only. `CompletionProvider` is
> removed from the C20 portfolio.

### 10.2 Required Documentation

The ratification decision must be recorded with:

- Owner name
- Date
- Decision (YES or NO)
- Any conditions, bounds, or interpretive guidance
- Signature or approval marker

The decision should be recorded in one of:
- ADR-C20 §11.1 directly (amending the §11.1 header to record the outcome)
- A new `docs/adr/ADR-C20-A1_§11_1_RATIFICATION.md` amendment
- The C20 Charter §9 decision log

### 10.3 Post-Ratification Actions

| If YES | If NO |
|--------|-------|
| WP2 gates cleared | Remove `CompletionProvider` from ADR-C20 §4.1 capability table |
| Begin WP2 implementation | Update C20 Charter §4 WP2 scope description |
| Design `CompletionProvider` connector adapter | Close §11.1 with outcome recorded |
| Plan C20-INV-12/C20-INV-13 activation | Re-scope WP2 deliverables |

### 10.4 Post-Ratification Boundary

Once §11.1 is ratified, the decision is **binding on all subsequent C20 work**
and may only be reversed by:

- A new ADR amendment with its own ratification
- A Charter amendment with human-owner approval

An AI agent must not re-litigate, reinterpret, or work around a ratified §11.1
decision.

## 11. Recommendation

**READY FOR RATIFICATION**

All prerequisites are satisfied. WP0 and WP1 are complete with passing
contract-test evidence. The WP1 boundary is verified — no WP2 capability has
leaked. The invariant registry is machine-checkable. The governance record
(ADR, Charter, reconciliations, runtime verification) is internally consistent.

The §11.1 question is well-bounded:

- It gates exactly one capability port (`CompletionProvider`)
- The non-negotiable invariants bind either outcome
- The forbidden-scope list is definitive regardless of outcome
- Open governance questions (§11.2) do not gate WP2

The decision is the human owner's alone. This checklist provides the complete
governance context needed to make it.

---

*No implementation changes. This document is the ratification preparation
artefact. The decision itself must be recorded by the human owner in a
separate step.*
