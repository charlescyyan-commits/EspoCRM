# Phase3C20 WP2 Charter — Capability Ports and Provider Adapters

## 1. Status

**Status:** Active — Authorized under ADR-C20 §11.1 Option C
**Date:** 2026-07-28
**Type:** Governance charter — documentation only
**Phase:** Phase3C20 WP2 — Capability Ports

## 2. Governing Authority

| Document | Role | State |
|----------|------|-------|
| `AGENTS.md` / `CLAUDE.md` | Authoritative — binding prohibitions | Unchanged |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | C20 architecture; §4 provider abstraction, §10 WP2 scope | Proposed |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | 22-invariant registry; C20-INV-12, C20-INV-13 assigned to WP2 | Active |
| `docs/PHASE3C20_CHARTER.md` | C20 charter; WP2 scope description | Active |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified — Option C (Restricted Capability Portfolio) | RATIFIED |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | `CompletionProvider` allowed/forbidden capabilities | Active |
| `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` | WP1 exit evidence; WP1 READY FOR EXIT | Complete |

## 3. Baseline

- **ADR-C20 §11.1:** Ratified YES — Option C (Charles, 2026-07-28)
- **WP1 exit tag:** `phase3c20-wp1-exit` (`2bc0269`)
- **WP1 boundary:** `Modules/AIPlatform` skeleton, `ProviderCredential` custody surface, Administration → AI Platform → Credentials
- **CompletionProvider scope:** `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` (`29d0309`)
- **Pre-existing provider adapters:** `apify_provider.py`, `serper_provider.py` (connector; `SearchProvider`)

## 4. WP2 Mission

Establish the C20 **capability port layer** — the connector-side provider
abstraction that enables EspoCRM to orchestrate AI-assisted workflows through
a single, auditable egress boundary.

WP2 creates the **contract surface** between EspoCRM's governance layer and
external AI capabilities. It does not create the CRM-side orchestration layer
(WP3), the CRM-side entity model (WP3), or any email-sending path (C21).

## 5. Scope

### 5.1 In Scope

| # | Item | Description |
|---|------|-------------|
| S1 | Capability port Protocols | `SearchProvider`, `EnrichmentProvider`, `CompletionProvider` — Python `Protocol` classes in the connector |
| S2 | `EnrichmentProvider` adapter | Concrete adapter for data enrichment (Apollo, Hunter) |
| S3 | `CompletionProvider` adapter | Concrete adapter for LLM completion — capabilities Chitu does not own, per ratified scope |
| S4 | Search provider refinement | Existing `apify_provider.py` and `serper_provider.py` brought under unified port contract |
| S5 | Normalized request/response types | `SearchRequest`, `SearchResult`, `EnrichmentRequest`, `EnrichmentResult`, `CompletionRequest`, `CompletionResult` |
| S6 | Error classification | Full ADR-C20 §4.3 taxonomy applied to every adapter |
| S7 | Capability declarations | Each adapter declares `{streaming, json_mode, max_context, vision}` per ADR §4.2.6 |
| S8 | Cost envelope | Every result carries `{tokens_in, tokens_out, currency, amount, model, latency, provider_request_id}` per ADR §4.2.4 |
| S9 | Idempotency key | Every request carries a caller-supplied idempotency key per ADR §4.2.5 |
| S10 | Recorded-fixture tests | Every adapter tested with `FakeHttpTransport`; complete trace with zero network egress |
| S11 | Transport injection | No adapter constructs without explicit `HttpTransport`; no default transport exists |

### 5.2 Explicitly Out of Scope

| # | Item | Rationale |
|---|------|-----------|
| O1 | CRM-side `AIJob` dispatch, `AIJobService` | WP3 — entity model and lifecycle |
| O2 | `AIRequestLog` persistence and cost accounting | WP3 — governance infrastructure |
| O3 | `PromptTemplate` versioning and immutability | WP3 — prompt governance |
| O4 | `AIQualificationInsight` entity | WP3 — advisory layer |
| O5 | `ProviderRoute` configuration UI | WP3 — routing administration |
| O6 | `ProviderHealth` checks | WP3 — health monitoring |
| O7 | `ProviderCredential` custody UI | Separate WP — WP1 blocker F3 |
| O8 | Any CRM-side PHP code that calls a provider adapter | WP3 — orchestration layer |
| O9 | `EmailDeliveryProvider` | C21 — email sending |
| O10 | Any scoring computation or `AIScore` entity | Forbidden — C20-INV-14 |
| O11 | Any autonomous trigger or scheduled invocation | Forbidden — Charter §6 |
| O12 | Any modification to Chitu-owned code | Forbidden — AGENTS.md A1–A4 |

## 6. Allowed Capabilities

### 6.1 SearchProvider

| Aspect | Definition |
|--------|------------|
| **What it is** | External search execution — web search, company search, person search |
| **Existing implementations** | `apify_provider.py`, `serper_provider.py` |
| **WP2 action** | Formalize under unified `SearchProvider` Protocol; ensure adapter compliance with §4.2 rules |
| **CRM relationship** | `SearchStrategyService` creates `SearchJob` rows; connector worker executes via `SearchProvider` |
| **Chitu boundary** | Search is a connector capability — Chitu does not own search execution |

### 6.2 EnrichmentProvider

| Aspect | Definition |
|--------|------------|
| **What it is** | Data enrichment — company profiles, contact details, firmographics |
| **Candidate implementations** | Apollo, Hunter |
| **WP2 action** | Define `EnrichmentProvider` Protocol; implement at least one concrete adapter |
| **CRM relationship** | Operator-initiated enrichment on a `ProspectPool` record; results persist as `ResearchEvidence` |
| **Chitu boundary** | Enrichment is a data lookup — not research, not scoring, not qualification |

### 6.3 CompletionProvider

| Aspect | Definition |
|--------|------------|
| **What it is** | LLM completion for capabilities Chitu does not own |
| **Allowed capabilities** | Research evidence summarization, qualification insight generation, draft assistance, reply classification support |
| **Forbidden capabilities** | Provider execution, API credentials, autonomous lifecycle changes, authoritative scoring, direct external calls, email generation/sending |
| **Full scope** | `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` |
| **Gating** | §11.1 ratified — Option C |

## 7. Architecture Boundaries

### 7.1 Egress Boundary

```
EspoCRM (PHP)                      chitu_connector (Python)
────────────────                   ────────────────────────
Never opens HTTP to provider       Sole egress for all provider I/O
Never imports Python                Never writes SQL or PHP metadata
Stores credential references only   Holds provider secrets in environment
Dispatches via connector contract   Executes provider calls with injected transport
```

**All provider I/O goes through the connector.** No PHP code in
`Modules/AIPlatform` or `Modules/Prospecting` opens an HTTP connection to
Apify, Apollo, Hunter, OpenAI, Anthropic, DeepSeek, or any other provider
domain. Enforced by C20-INV-03.

### 7.2 Chitu Intelligence Boundary

| Chitu owns | CompletionProvider must not touch |
|-------------|----------------------------------|
| `canonical_score` | No score computation, no `AIScore` entity |
| Qualification verdicts | No qualification decisions; advisory insight only |
| Website research (`website_research.py`) | No web crawling or scraping |
| Single candidate loop (`single_candidate_loop.py`) | No candidate processing pipeline |
| ICP matching (`icp.py`) | No ICP computation |
| Email generation engine | No email content generation that bypasses `DraftApproval` |

### 7.3 Human Approval Boundary

Every `CompletionProvider` invocation is **operator-initiated**. No autonomous
trigger, no scheduled invocation, no event-driven dispatch in C20. The operator
reviews AI-generated output before it becomes a CRM action.

### 7.4 ProviderCredential Isolation

WP2 adapters reference credentials by identifier only. Credentials are resolved
in the connector environment — never passed from CRM. EspoCRM's
`credentialReference` field remains write-only. No provider secret enters the
CRM database, API response, log, or exception.

## 8. Deliverables

### 8.1 Connector — Provider Protocols

| File | Content |
|------|---------|
| `acquisition/providers/search/base.py` | `SearchProvider` Protocol, `SearchRequest`, `SearchResult` |
| `acquisition/providers/enrichment/base.py` | `EnrichmentProvider` Protocol, `EnrichmentRequest`, `EnrichmentResult` |
| `acquisition/providers/completion/base.py` | `CompletionProvider` Protocol, `CompletionRequest`, `CompletionResult` |

### 8.2 Connector — Adapter Implementations

| File | Content |
|------|---------|
| `acquisition/providers/enrichment/adapter.py` | Concrete `EnrichmentProvider` implementation |
| `acquisition/providers/completion/adapter.py` | Concrete `CompletionProvider` implementation |
| `acquisition/providers/apify_provider.py` | Existing — verify `SearchProvider` compliance |
| `acquisition/providers/serper_provider.py` | Existing — verify `SearchProvider` compliance |

### 8.3 Connector — Error Classification

Each adapter must map vendor errors to the ADR-C20 §4.3 taxonomy:
`NETWORK`, `PROVIDER`, `AUTH`, `VALIDATION`, `UNKNOWN`, `RATE_LIMIT`,
`QUOTA`, `CONTENT_FILTER`.

### 8.4 Connector — Capability Declarations

Each adapter must declare per ADR §4.2.6:
`streaming` (bool), `json_mode` (bool), `max_context` (int), `vision` (bool).

### 8.5 Tests

| Test Scope | Requirement |
|-------------|-------------|
| `SearchProvider` fixture tests | Existing tests verified; gap coverage for error classification and capability declaration |
| `EnrichmentProvider` fixture tests | New — recorded fixtures, error classification, capability declaration, dry-run verification |
| `CompletionProvider` fixture tests | New — 4 allowed capabilities, 6 forbidden categories asserted absent, error classification, capability declaration, dry-run verification |
| Transport injection | Every adapter test asserts construction fails without explicit transport |
| Cost envelope | Every result asserts `{tokens_in, tokens_out, currency, amount, model, latency}` present |
| Idempotency | Every adapter test asserts same key produces same result in fixture mode |

### 8.6 Governance Evidence

| Artefact | Content |
|----------|---------|
| C20-INV-12 activation | Contract test asserting no default transport in any adapter |
| C20-INV-13 activation | Contract test asserting dry-run mode with zero network egress |
| WP2 exit reconciliation | Document recording WP2 completion against this charter |

## 9. Non-Goals

WP2 does **not** create:

- CRM-side PHP code that calls provider adapters (WP3)
- `AIJob`, `AIRequestLog`, `PromptTemplate`, `AIQualificationInsight` entities (WP3)
- `AIJobService`, `CredentialCustodyService`, `PromptTemplateService` (WP3)
- `ProviderRoute`, `ProviderHealth` metadata or entities (WP3)
- Administration UI beyond the existing WP1 Credentials surface (separate WP)
- `EmailDeliveryProvider` or any email-sending path (C21)
- `AIScore` entity or any scoring computation (forbidden — C20-INV-14)
- Autonomous AI trigger or scheduled invocation (forbidden — Charter §6)
- Modification to C19 lifecycle services, guards, or action keys (forbidden — Charter §6)
- Modification to Chitu scoring, research, or email-generation code (forbidden — AGENTS.md)

## 10. Security Requirements

### 10.1 Transport

| Requirement | Enforcement |
|-------------|-------------|
| No default transport | Constructor requires `HttpTransport`; fails without it |
| Transport injection only | Test fixtures inject `FakeHttpTransport`; production injects real transport |
| Dry-run mode | `FakeHttpTransport` returns recorded fixtures; zero network egress |
| No PHP HTTP | C20-INV-03 gate over entire `crm-extension/files` PHP tree |

### 10.2 Credentials

| Requirement | Enforcement |
|-------------|-------------|
| Secrets never in request types | No credential field in any `*Request` value object |
| Secrets never in result types | No credential field in any `*Result` value object |
| Secrets never in logs or exceptions | `field(repr=False)` on all config fields; contract-tested |
| Connector resolves credentials from environment | EspoCRM passes credential identifier only |

### 10.3 Prompt Safety (CompletionProvider only)

| Requirement | Enforcement |
|-------------|-------------|
| Structured prompt format | `CompletionRequest.prompt` is template-driven; no raw user input concatenation |
| No PII validation | Operator is responsible; adapter passes what it receives |
| Content filter handling | `CONTENT_FILTER` error class — terminal, never auto-retry with same prompt |

### 10.4 Operator Control

| Requirement | Enforcement |
|-------------|-------------|
| Every invocation operator-initiated | `CompletionRequest.initiating_user` is required |
| No autonomous dispatch | No scheduled job, no event hook, no background worker invokes `CompletionProvider` |
| No email sending | C20-INV-15 — zero email-sending path in C20 |

## 11. Testing Strategy

### 11.1 Recorded-Fixture Pattern (All Adapters)

```
1. Record:     Real provider call → capture request + response → store as fixture
2. Replay:     FakeHttpTransport serves fixture → adapter processes → assert output
3. Dry-run:    Complete trace with zero network egress (C20-INV-13)
4. Error:      FakeHttpTransport serves error fixture → adapter classifies → assert taxonomy
```

### 11.2 Per-Adapter Test Matrix

| Test | Search | Enrichment | Completion |
|------|--------|------------|------------|
| Happy path (fixture replay) | ✓ | ✓ | ✓ (4 capabilities) |
| Error classification (8 taxonomy classes) | ✓ | ✓ | ✓ |
| Transport injection (no default) | ✓ | ✓ | ✓ |
| Cost envelope (tokens, currency, latency) | ✓ | ✓ | ✓ |
| Idempotency (same key → same result) | ✓ | ✓ | ✓ |
| Capability declaration (4 flags) | ✓ | ✓ | ✓ |
| Dry-run (zero network egress) | ✓ | ✓ | ✓ |
| No vendor type in public interface | ✓ | ✓ | ✓ |
| No credential in any type | ✓ | ✓ | ✓ |

### 11.3 Boundary Contract Tests

| Test | Scope |
|------|-------|
| C20-INV-12 — no default transport | Every adapter constructor; contract test across all provider files |
| C20-INV-13 — dry-run zero egress | Every adapter fixture test; no socket opened |
| C20-INV-03 — no PHP HTTP | Whole `crm-extension/files` PHP tree (existing WP0 guard) |
| `CompletionProvider` forbidden capabilities | 6 forbidden categories asserted absent in adapter code |
| `CompletionProvider` Chitu boundary | No reference to `canonical_score`, `website_research`, `single_candidate_loop`, `scoring`, `icp` in completion adapter |

## 12. Exit Criteria

WP2 is complete when **all** of the following are true:

| # | Criterion | Evidence |
|---|-----------|----------|
| E1 | `SearchProvider` Protocol defined; existing adapters compliant | Contract tests pass |
| E2 | `EnrichmentProvider` Protocol defined; at least one adapter implemented | Contract tests pass |
| E3 | `CompletionProvider` Protocol defined; at least one adapter implemented per ratified scope | Contract tests pass |
| E4 | Every adapter carries cost envelope on every result | Test assertion |
| E5 | Every adapter classifies errors into §4.3 taxonomy | Test assertion |
| E6 | Every adapter declares capabilities per §4.2.6 | Test assertion |
| E7 | Every adapter requires explicit transport; no default exists | C20-INV-12 activated |
| E8 | Every adapter has dry-run fixture coverage with zero network egress | C20-INV-13 activated |
| E9 | Canonical invocation (`pytest -q`) green across all provider tests | CI-equivalent |
| E10 | `CompletionProvider` forbidden capabilities asserted absent | Contract test |
| E11 | `CompletionProvider` Chitu boundary preserved — zero references to Chitu-owned code | Contract test |
| E12 | No CRM-side PHP, JS, metadata, or artifact changes introduced by WP2 | Inventory check |
| E13 | WP2 exit reconciliation documented | `docs/PHASE3C20_WP2_EXIT_RECONCILIATION.md` |

## 13. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-27 | ADR-C20 §4.1 — capability ports defined; `CompletionProvider` gated on §11.1 | ADR-C20 §4.1 |
| 2026-07-27 | C20-INV-12 and C20-INV-13 assigned to WP2 | Invariant Registry |
| 2026-07-28 | ADR-C20 §11.1 ratified — Option C (Restricted Capability Portfolio) | `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` |
| 2026-07-28 | `CompletionProvider` capability scope defined — 4 allowed, 6 forbidden | `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` |
| 2026-07-28 | WP2 Chartered — capability ports, 3 Protocols, 2 new adapters, fixture tests | This document |

## 14. Human Owner Approval Record

**Approved by:** Charles

**Date:** 2026-07-28

**Decision:**

I approve the Phase3C20 WP2 Capability Ports Charter.

This approval authorizes WP2 under the ratified §11.1 Option C decision.

WP2 scope is limited to connector-side capability ports, provider adapters,
and recorded-fixture tests as defined in this charter.

WP2 does **not** authorize:
- CRM-side PHP orchestration code (WP3)
- `AIJob`, `AIRequestLog`, `PromptTemplate`, or `AIQualificationInsight` (WP3)
- Any email-sending path (C21)
- Any scoring computation or `AIScore` entity (forbidden)
- Any autonomous AI trigger (forbidden)
- Any modification to Chitu-owned code (forbidden)

The seven binding constraints recorded in the §11.1 ratification decision
remain in force and bind all WP2 implementation.

---

*This charter authorizes WP2 implementation within the defined scope and
constraints. No PHP. No JS. No metadata. No CRM-side orchestration.
Connector-side capability ports and recorded-fixture tests only.*
