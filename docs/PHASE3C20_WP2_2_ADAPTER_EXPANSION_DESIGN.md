# Phase3C20 WP2.2 — Adapter Expansion Design Audit

## 1. Status

**Status:** Design — documentation only (no code changes)
**Date:** 2026-07-28
**Type:** Design audit — read-only
**Phase:** Phase3C20 WP2.2 — Adapter Expansion

## 2. Governing Documents

| Document | Role |
|----------|------|
| `docs/PHASE3C20_WP2_CHARTER.md` | WP2 scope and exit criteria — WP2.2 governed by §5.1, §8.2 |
| `docs/PHASE3C20_WP2_1_IMPLEMENTATION_PLAN.md` | WP2.1 foundation — Protocols, types, error taxonomy, test infrastructure |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | `CompletionProvider` allowed (4) and forbidden (6) capabilities |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified YES — Option C (Restricted Capability Portfolio); 7 binding constraints |
| `docs/PHASE3C20_CHARTER.md` | C20 charter; WP2 scope, boundaries, exit gates |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | C20 architecture; §4 provider abstraction, §10 frozen surfaces |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | 22-invariant registry; C20-INV-12, C20-INV-13 activated under WP2 |
| `AGENTS.md` / `CLAUDE.md` | Authoritative prohibitions — unchanged |

## 3. WP2.2 Objective

WP2.2 implements the **concrete adapters** deferred from WP2.1. Where WP2.1
established the capability port Protocols, normalized types, error taxonomy,
and test infrastructure, WP2.2 delivers the working adapter code that
implements those Protocols.

### 3.1 Relationship to WP2.1

```
WP2.1 (completed / checkpoint)         WP2.2 (this design)
────────────────────────────────       ──────────────────────
Capability Protocols defined           EnrichmentProvider adapter implemented
SearchProvider retrofit verified       CompletionProvider adapter implemented
Error taxonomy mapped (8 classes)      Adapter-specific recorded fixtures
Cost envelope type defined             Fixture-based contract tests per adapter
Idempotency key contract               Capability declarations populated
Capability declaration pattern         Error taxonomy exercised per adapter
Cross-cutting contract tests           WP2 exit criteria satisfied
```

### 3.2 What WP2.2 Delivers

| # | Deliverable | Description |
|---|-------------|-------------|
| D1 | `EnrichmentProvider` adapter | Concrete adapter in `acquisition/providers/enrichment/adapter.py` implementing the `EnrichmentProvider` Protocol |
| D2 | `CompletionProvider` adapter | Concrete adapter in `acquisition/providers/completion/adapter.py` implementing the `CompletionProvider` Protocol per ratified scope |
| D3 | Enrichment fixture tests | Recorded-fixture contract tests with dry-run verification |
| D4 | Completion fixture tests | Recorded-fixture contract tests covering 4 allowed capabilities; 6 forbidden categories asserted absent |
| D5 | Adapter-specific recorded fixtures | Pre-recorded provider request/response pairs for deterministic replay |
| D6 | WP2 exit reconciliation | `docs/PHASE3C20_WP2_EXIT_RECONCILIATION.md` |

### 3.3 What WP2.2 Does NOT Deliver

WP2.2 does **not** create, modify, or touch:

- Any CRM-side PHP code (WP3 territory)
- `AIJob`, `AIRequestLog`, `PromptTemplate`, or `AIQualificationInsight` entities (WP3)
- Any provider routing or `ProviderRoute` configuration (WP3)
- Any `ProviderHealth` check (WP3)
- `ProviderCredential` custody UI (separate WP — WP1 blocker F3)
- Any email-sending path (C21 territory — C20-INV-15)
- Any scoring computation or `AIScore` entity (forbidden — C20-INV-14)
- Any autonomous trigger or scheduled invocation (forbidden — Charter §6)
- Any modification to Chitu-owned code (forbidden — AGENTS.md A1–A4)

## 4. EnrichmentProvider Scope

### 4.1 What EnrichmentProvider Is

`EnrichmentProvider` is a **data-lookup capability port**. It enables CRM
operators to enrich prospect records with company profiles, contact details,
and firmographics from external data providers. It is an operator-initiated,
read-only data fetch — not research, not scoring, not qualification.

| It is | It is not |
|-------|-----------|
| A connector-side data-lookup adapter | A research engine |
| An operator-initiated enrichment path | An autonomous data crawler |
| A normalized lookup across entity types | A scoring or qualification authority |
| A contract that returns structured fields | A CRM-side HTTP client |
| A recorded-fixture-testable abstraction | A secret store |

### 4.2 Candidate Provider Integrations

| Provider | Lookup Type | Entity Types |
|----------|-------------|--------------|
| Apollo | Domain, email, company name | Company, person |
| Hunter | Domain lookup, email finder, email verification | Company, person |

### 4.3 Request / Response Contract

The `EnrichmentProvider` adapter implements the Protocol defined in WP2.1
(`providers/enrichment/base.py`):

```python
# Request — operators specify what to look up and which fields they need
EnrichmentRequest(
    request_id: str,
    provider_name: str,
    entity_type: str,                  # "company" | "person"
    lookup_key: str,                   # domain, email, company name
    lookup_type: str,                  # "domain" | "email" | "name"
    fields_requested: tuple[str, ...], # e.g. ("employees", "revenue", "industry")
    idempotency_key: str,              # caller-supplied; persisted before dispatch
    initiating_user: str,              # every invocation attributable
)

# Result — normalized fields, no vendor type
EnrichmentResult(
    provider_name: str,
    entity_type: str,
    lookup_key: str,
    fields: Mapping[str, Any],         # normalized enrichment fields
    cost: CostEnvelope | None,         # None if flat-rate provider
    capability: Capability = Capability.ENRICHMENT,
)
```

### 4.4 Enrichment Boundaries

| Rule | Rationale |
|------|-----------|
| No CRM-side HTTP to Apollo, Hunter, or any enrichment provider | C20-INV-03 — connector is sole egress |
| No enrichment fields treated as qualification input | Enrichment is data hydration, not scoring |
| No autonomous enrichment trigger | Every invocation is operator-initiated |
| No credential field in request or result | Secrets live in connector environment |
| No vendor-specific type in public interface | `Mapping[str, Any]` for fields; no provider SDK type |
| Adapter requires explicit transport injection | C20-INV-12 — no default transport |

### 4.5 Enrichment is NOT

- **Qualification.** Enriched data (employee count, revenue, industry) is CRM
  data hydration. It does not produce a qualification verdict. Chitu owns
  qualification authority (C20-INV-21).
- **Scoring.** Enrichment fields are not scores. No field maps to
  `canonical_score` or any `AIScore` entity (C20-INV-14).
- **Research.** Enrichment is structured data lookup — not web crawling,
  scraping, or intelligence generation. Chitu owns research logic (AGENTS.md
  A2).
- **Contact import.** Enrichment returns data; it does not create CRM records.
  Record creation is a separate operator action.

## 5. CompletionProvider Bridge Scope

### 5.1 What CompletionProvider Is

`CompletionProvider` is an **orchestration contract only**. It is a capability
port in the connector's provider abstraction layer that bridges LLM completion
requests for capabilities Chitu does **not** own. It does not execute AI, it
does not store secrets, and it does not compute scores.

| It is | It is not |
|-------|-----------|
| An orchestration contract (Protocol) | An AI runtime |
| A connector-side adapter interface | A provider gateway |
| A capability port for non-Chitu LLM use cases | A secret store |
| An operator-initiated invocation path | A scoring authority |
| A recorded-fixture-testable abstraction | An autonomous agent |
| A contract that carries cost, latency, and provenance | A direct HTTP client |

### 5.2 Architecture Position

```
EspoCRM (PHP)
  Modules/AIPlatform
    AIJobService · PromptTemplateService · CredentialCustodyService  [WP3]
         │  calls via connector contract
         ▼
chitu_connector (Python)  ←── sole egress boundary
  acquisition/providers/
    completion/
      base.py              ← CompletionProvider Protocol [WP2.1]
      adapter.py           ← CompletionProvider implementation [WP2.2]
         │  explicit transport injection (no default)
         ▼
  External LLM provider (OpenAI / Anthropic / DeepSeek / Moonshot)
```

`CompletionProvider` lives entirely on the connector side of the egress
boundary. EspoCRM never opens an HTTP connection to an LLM provider. It
dispatches a `CompletionRequest` through the connector contract and receives
a `CompletionResult`.

### 5.3 Allowed Capabilities (4)

Per the ratified `CompletionProvider` capability scope
(`docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`), the adapter serves
exactly four capabilities:

| # | Capability | What it does | What it does NOT do |
|---|-----------|--------------|---------------------|
| C1 | `RESEARCH_EVIDENCE` | Summarize, extract, structure already-persisted `ResearchEvidence` data | Does not crawl, scrape, or search the web |
| C2 | `QUALIFICATION_INSIGHT` | Generate contextual intelligence — market signals, buying intent, confidence explanation | Does not produce a qualification verdict or modify `canonical_score` |
| C3 | `DRAFT_ASSISTANCE` | Generate proposed email content, talking points, follow-up suggestions for operator review | Does not send email or modify the email-generation engine |
| C4 | `REPLY_ASSISTANCE` | Classify inbound replies, sentiment analysis, suggested response categorization | Does not mutate `ReplyEvent` lifecycle status |

### 5.4 Forbidden Capabilities (6 Categories)

The following are **strictly forbidden** for `CompletionProvider`. The adapter
must not reference, import, or depend on any code that performs these
functions:

| # | Forbidden Category | Specific Prohibition |
|---|-------------------|---------------------|
| F1 | Provider Execution | No direct LLM API invocation from PHP; no HTTP client construction in CRM |
| F2 | API Credentials | No credential storage, caching, resolution, or logging in adapter; no credential field in any type |
| F3 | Autonomous Lifecycle Changes | No mutation of `ProspectPool`, `Lead`, `SendExecution`, `ReplyEvent`, `Quote`, `DraftApproval`, or `Opportunity` status |
| F4 | Authoritative Scoring | No score computation; no field named `score`/`rating`/`rank`/`canonical_score`; no `AIScore` entity (C20-INV-14) |
| F5 | Direct External Calls | No HTTP from PHP to any external domain (C20-INV-03); no provider call without explicit injected transport (C20-INV-12) |
| F6 | Email Generation/Sending | No email content bypassing `DraftApproval`; no email sending path (C20-INV-15); no modification of email-generation engine (AGENTS.md A3) |

### 5.5 CompletionRequest / CompletionResult Contract

The adapter implements the Protocol defined in WP2.1
(`providers/completion/base.py`):

```python
CompletionCapability enum:
    RESEARCH_EVIDENCE, QUALIFICATION_INSIGHT, DRAFT_ASSISTANCE, REPLY_ASSISTANCE

CompletionRequest(
    capability: CompletionCapability,
    purpose: str,
    prompt: str,                        # structured; no raw user input concatenation
    context: Mapping[str, Any] | None,  # structured CRM data payload
    model: str | None,                  # resolved by ProviderRoute config if absent
    max_tokens: int | None,
    temperature: float | None,
    idempotency_key: str,               # repr=False — never logged
    initiating_user: str,               # every invocation attributable
    prompt_template_version: str | None,
)

CompletionResult(
    completion_id: str,
    capability: CompletionCapability,
    content: str,
    finish_reason: str,                 # "STOP" | "LENGTH" | "CONTENT_FILTER"
    model: str,
    cost: CostEnvelope,
    prompt_template_version: str | None,
)
```

### 5.6 Error Classification

Every completion failure must be classified into exactly one
`BridgeErrorClass` per ADR-C20 §4.3:

| Error Class | Retryable | Behaviour |
|-------------|-----------|-----------|
| `NETWORK` | Yes | Backoff + jitter |
| `PROVIDER` | Yes (5xx only) | Backoff; fail over via `ProviderRoute` |
| `AUTH` | No — terminal | Credential alert |
| `VALIDATION` | No — terminal | Caller defect |
| `UNKNOWN` | No — terminal | Operator review |
| `RATE_LIMIT` | Yes | Honour `Retry-After`; no attempt budget consumed |
| `QUOTA` | No — terminal | Halt capability |
| `CONTENT_FILTER` | No — terminal | Never auto-retry with same prompt |

No vendor error code or raw provider response crosses the boundary. Retry
policy keys off `ErrorClass`, never off vendor error codes.

## 6. Allowed Adapter Categories

WP2.2 operates within the following adapter taxonomy. Every adapter is a
connector-side Python class implementing a capability port Protocol. No
adapter exists in PHP.

| # | Category | Capability Port | Existing / New | WP2.2 Action |
|---|----------|----------------|----------------|-------------|
| A1 | Search | `SearchProvider` | Existing (Apify, Serper) — retrofitted in WP2.1 | Verify retrofit compliance; no new search adapters |
| A2 | Enrichment | `EnrichmentProvider` | New in WP2.2 | Implement concrete adapter with fixture tests |
| A3 | Completion | `CompletionProvider` | New in WP2.2 | Implement concrete adapter per ratified scope with fixture tests |

### 6.1 Adapter Invariants (All Categories)

Every adapter in WP2.2 must satisfy:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| I1 | No default transport — constructor requires explicit `HttpTransport` injection | C20-INV-12 — contract test |
| I2 | Dry-run mode produces complete trace with zero network egress | C20-INV-13 — contract test |
| I3 | No credential field in any request or result type | Contract test |
| I4 | No vendor-specific type in any public interface | Contract test |
| I5 | Every error classified into ADR-C20 §4.3 taxonomy | Contract test |
| I6 | Capability declaration populated per ADR §4.2.6 | Contract test |
| I7 | Cost envelope on every result (mandatory for Completion; optional for Enrichment) | Contract test |
| I8 | Idempotency key on every request (`repr=False`) | Contract test |
| I9 | `initiating_user` required — every invocation attributable | Contract test |
| I10 | No `import requests`, `import httpx`, `import urllib3` in adapter code | Code review |

### 6.2 What Is NOT an Adapter Category

The following do **not** exist as capability ports and must not be created:

| Not a category | Reason |
|----------------|--------|
| Scoring provider | Forbidden — C20-INV-14; Chitu owns `canonical_score` |
| Email delivery provider | C21 territory — C20-INV-15 |
| Research execution provider | Forbidden — AGENTS.md A2; Chitu owns research logic |
| Qualification engine provider | Forbidden — C20-INV-21; Chitu owns qualification verdicts |
| Autonomous agent provider | Forbidden — Charter §6; every invocation operator-initiated |
| Crawler / scraper provider | Forbidden — AGENTS.md A2; out of scope per BOUNDARIES.md §2 |

## 7. Forbidden Integrations

### 7.1 Absolute Prohibitions (AGENTS.md)

| # | Prohibition | Reference |
|---|-------------|-----------|
| P1 | Do not modify Chitu scoring logic — `canonical_score.py`, `scoring.py`, or any scoring code | AGENTS.md A1 |
| P2 | Do not modify Chitu AI research logic — `website_research.py`, `single_candidate_loop.py`, or any research code | AGENTS.md A2 |
| P3 | Do not modify the email-generation engine | AGENTS.md A3 |
| P4 | Do not modify unrelated Chitu application code | AGENTS.md A4 |
| P5 | No real customer data without explicit approval | AGENTS.md A5 |

### 7.2 Connector / Architecture Prohibitions

| # | Prohibition | Reference |
|---|-------------|-----------|
| P6 | No HTTP from PHP to any provider domain — connector is sole egress | C20-INV-03 |
| P7 | No `AIScore` entity; no score computation | C20-INV-14 |
| P8 | No email-sending path in C20 | C20-INV-15 |
| P9 | No qualification verdict computation | C20-INV-21 |
| P10 | No modification to C19-frozen lifecycle services, guards, or action keys | ADR §10, Charter §6 |
| P11 | No autonomous AI trigger — every invocation operator-initiated | Charter §6 |
| P12 | No adapter constructed without explicit transport | C20-INV-12 |
| P13 | No `os.environ` access in adapter code — config objects only | WP2.1 §9.3 F2 |
| P14 | No `print()` or `logging.info()` of request/response bodies | WP2.1 §9.3 F3 |
| P15 | No bare `except Exception: pass` around transport calls — all errors classified | WP2.1 §9.3 F4 |

### 7.3 WP3 Territory (Not WP2.2)

WP2.2 must not create, reference, or depend on:

| # | Territory | Owning WP |
|---|-----------|-----------|
| T1 | `AIJob` entity, `AIJobService`, job dispatch | WP3 |
| T2 | `AIRequestLog` entity, cost accounting infrastructure | WP3 |
| T3 | `PromptTemplate` entity, versioning, immutability | WP3 |
| T4 | `AIQualificationInsight` entity | WP3 |
| T5 | `ProviderRoute` entity, routing configuration | WP3 |
| T6 | `ProviderHealth` checks | WP3 |
| T7 | `ProviderCredential` custody UI | Separate WP |
| T8 | CRM-side PHP code that calls any provider adapter | WP3 |

## 8. Chitu Intelligence Ownership Boundary

### 8.1 The Rule

**If Chitu already does it, `CompletionProvider` does not touch it.**
`CompletionProvider` fills capability gaps — it does not duplicate, augment,
replace, or compete with Chitu-owned capabilities.

### 8.2 Ownership Matrix

| Chitu Intelligence Owns | CompletionProvider Must Not Touch |
|--------------------------|----------------------------------|
| `canonical_score` | No score computation; no `AIScore` entity (C20-INV-14) |
| Qualification verdicts | No qualification decisions; advisory insight only (C20-INV-21) |
| ICP matching (`icp.py`) | No ICP computation |
| Website research (`website_research.py`) | No web crawling or scraping |
| Single candidate loop (`single_candidate_loop.py`) | No candidate processing pipeline |
| Email generation engine | No email content generation bypassing `DraftApproval`; no modification (AGENTS.md A3) |

### 8.3 The Gap — What CompletionProvider Serves

| Capability Gap | CompletionProvider Role | Chitu Relationship |
|----------------|------------------------|-------------------|
| Research evidence summarization | Summarize already-persisted CRM research data | Does not crawl; consumes Chitu output |
| Qualification insight generation | Generate contextual intelligence for operator review | Advisory only; does not override Chitu qualification |
| Draft assistance | Generate proposed text for operator editing | Flows through `DraftApproval`; does not modify email engine |
| Reply classification support | Classify and categorize inbound replies | Advisory annotation; `ReplyTriageService` remains lifecycle owner |

### 8.4 Escalation Trigger

If a proposed `CompletionProvider` use case involves any of the following, it
must be escalated to the human owner for separate ratification:

- Touching `canonical_score` or any scoring field
- Producing a qualification verdict
- Generating email content that could bypass `DraftApproval`
- Mutating a Prospecting lifecycle status
- Operating autonomously (scheduled, event-driven, or unattended)
- Replicating or augmenting any Chitu-owned capability

### 8.5 Design Verification

The `CompletionProvider` adapter code must contain **zero references** to:

- `canonical_score`
- `scoring`
- `icp`
- `website_research`
- `single_candidate_loop`
- `email_generation`
- Any module under `chitu_connector/vendored/contracts/` that is owned by Chitu

This is enforced by contract test (WP2 §11.3 boundary contract tests) and
confirmed by code review before WP2.2 exit.

## 9. Credential Boundary

### 9.1 The Principle

**Provider secrets never enter EspoCRM. EspoCRM holds credential references
only. The connector resolves actual secrets from its environment.**

### 9.2 Where Secrets Live

| Layer | What it holds | What it does NOT hold |
|-------|--------------|----------------------|
| EspoCRM `ProviderCredential` entity | `credentialReference` (string identifier, write-only) | Provider API key, token, or secret |
| Connector environment | Actual provider secrets (env vars, secrets manager) | CRM entity data |
| Adapter request types | Nothing credential-related — no field exists | Provider API key, token, or secret |
| Adapter result types | Nothing credential-related — no field exists | Provider API key, token, or secret |
| Logs, exceptions, tracebacks | Nothing credential-related (`repr=False` on all config fields) | Provider API key, token, or secret |

### 9.3 Design-Level Enforcement

| # | Rule | How Enforced |
|---|------|-------------|
| C1 | `CompletionRequest` has zero credential fields | Dataclass definition verified by contract test |
| C2 | `CompletionResult` has zero credential fields | Dataclass definition verified by contract test |
| C3 | `EnrichmentRequest` has zero credential fields | Dataclass definition verified by contract test |
| C4 | `EnrichmentResult` has zero credential fields | Dataclass definition verified by contract test |
| C5 | Adapter receives credential via connector config, not request parameter | Constructor accepts config object; credential resolved internally |
| C6 | `field(repr=False)` on all config fields that hold or reference credentials | Code review |
| C7 | No `os.environ` access in adapter code | Code review — config objects only |
| C8 | No credential logging — `print()`, `logging.info()` of request/response bodies forbidden | Code review + WP2.1 §9.3 F3 |

### 9.4 Credential Lifecycle

Credential lifecycle (rotation, expiry, revocation) is managed by the
connector's config infrastructure. WP2.2 adapters consume already-resolved
credentials — they do not manage credential lifecycle. The WP1
`ProviderCredential` entity in CRM stores credential metadata (label, type,
rotation schedule, audit trail) and a write-only `credentialReference`
field. Actual secrets are never written to the CRM database.

## 10. Test Requirements

### 10.1 Test Strategy

WP2.2 tests follow the recorded-fixture pattern established in WP2.1:

```
1. Record:    Real provider call → capture request + response → store as fixture
2. Replay:    FakeHttpTransport serves fixture → adapter processes → assert output
3. Dry-run:   Complete trace with zero network egress (C20-INV-13)
4. Error:     FakeHttpTransport serves error fixture → adapter classifies → assert taxonomy
```

### 10.2 EnrichmentProvider Test Matrix

| # | Test | Requirement |
|---|------|-------------|
| E1 | Happy path — fixture replay | FakeHttpTransport serves recorded provider response; adapter processes correctly |
| E2 | Transport error (TimeoutError) → retryable error class | `classify_provider_error()` maps to `NETWORK` |
| E3 | HTTP 401 → `AUTH` error class | Terminal, retryable=False |
| E4 | HTTP 429 → `RATE_LIMIT` with retry_after | Retryable, honours Retry-After |
| E5 | HTTP 5xx → `PROVIDER` error class | Retryable |
| E6 | HTTP 402 → `QUOTA` error class | Terminal |
| E7 | HTTP 400 → `VALIDATION` error class | Terminal |
| E8 | Construction fails without explicit transport | C20-INV-12 |
| E9 | Dry-run — zero network egress | C20-INV-13 |
| E10 | Capability declaration populated | `capabilities` property returns valid `CapabilityDeclaration` |
| E11 | Cost envelope present or explicitly None | `CostEnvelope | None` on result |
| E12 | No credential field in request or result | Dataclass field verification |
| E13 | No vendor-specific type in public interface | Type annotation verification |
| E14 | Idempotency — same key produces same result in fixture mode | Repeated invocation with same key |

### 10.3 CompletionProvider Test Matrix

| # | Test | Requirement |
|---|------|-------------|
| C1 | Happy path — `RESEARCH_EVIDENCE` capability | FakeHttpTransport serves recorded LLM response; adapter returns `CompletionResult` with correct capability |
| C2 | Happy path — `QUALIFICATION_INSIGHT` capability | Same — verified per capability |
| C3 | Happy path — `DRAFT_ASSISTANCE` capability | Same — verified per capability |
| C4 | Happy path — `REPLY_ASSISTANCE` capability | Same — verified per capability |
| C5 | `CompletionCapability` enum has exactly 4 values | No extras; no scoring or email enum value |
| C6 | Forbidden capability check — no `SCORING` enum value exists | §11.1 ratification constraint |
| C7 | Forbidden capability check — no `EMAIL_GENERATION` enum value exists | §11.1 ratification constraint |
| C8 | `finish_reason` limited to STOP/LENGTH/CONTENT_FILTER | Enum validation |
| C9 | Cost envelope required on every result | `cost: CostEnvelope` (not Optional) |
| C10 | Transport error (TimeoutError) → retryable | `classify_provider_error()` maps to `NETWORK` |
| C11 | HTTP 401 → `AUTH` | Terminal |
| C12 | HTTP 429 → `RATE_LIMIT` with retry_after | Retryable |
| C13 | HTTP 5xx → `PROVIDER` | Retryable |
| C14 | HTTP 402 → `QUOTA` | Terminal |
| C15 | HTTP 400 → `VALIDATION` | Terminal |
| C16 | Content filter response → `CONTENT_FILTER` | Terminal, never auto-retry with same prompt |
| C17 | Construction fails without explicit transport | C20-INV-12 |
| C18 | Dry-run — zero network egress | C20-INV-13 |
| C19 | Capability declaration populated with accurate flags | `streaming`, `json_mode`, `max_context`, `vision` |
| C20 | No credential field in request or result | Dataclass field verification |
| C21 | No vendor-specific type in public interface | Type annotation verification |
| C22 | `idempotency_key` is `repr=False` on `CompletionRequest` | Field metadata verification |
| C23 | `initiating_user` required on `CompletionRequest` | Required field verification |
| C24 | Idempotency — same key produces same result in fixture mode | Repeated invocation with same key |

### 10.4 Boundary Contract Tests

| # | Test | Scope |
|---|------|-------|
| X1 | C20-INV-12 — no adapter constructs without explicit transport | All WP2.2 adapter files |
| X2 | C20-INV-13 — dry-run fixture mode produces zero network egress | All adapter fixture tests |
| X3 | C20-INV-03 — no PHP HTTP to any provider domain | Existing WP0.3 guard; unchanged by WP2.2 |
| X4 | `CompletionProvider` forbidden capabilities — 6 categories asserted absent | Completion adapter code + tests C6, C7 |
| X5 | Chitu boundary — zero references to Chitu-owned code in completion adapter | Code review + grep audit |
| X6 | No credential field in any `*Request` or `*Result` dataclass | All WP2.2 types |
| X7 | No vendor-specific type in any public interface | All WP2.2 types |
| X8 | All 8 `ErrorClass` values exercised by at least one adapter test | Cross-adapter coverage |

### 10.5 Test File Structure

```
chitu-connector/tests/
├── test_phase3c20_wp2_1_search_provider.py        [WP2.1 — existing]
├── test_phase3c20_wp2_1_enrichment_provider.py     [WP2.1 — existing]
├── test_phase3c20_wp2_1_completion_provider.py     [WP2.1 — existing]
├── test_phase3c20_wp2_1_taxonomy.py                [WP2.1 — existing]
├── test_phase3c20_wp2_1_capabilities.py            [WP2.1 — existing]
├── test_phase3c20_wp2_2_enrichment_adapter.py      [WP2.2 — NEW]
└── test_phase3c20_wp2_2_completion_adapter.py      [WP2.2 — NEW]
```

## 11. Exit Criteria

WP2.2 exits when **all** of the following are true:

| # | Criterion | Evidence |
|---|-----------|----------|
| EC1 | `EnrichmentProvider` adapter implemented in `acquisition/providers/enrichment/adapter.py` | File exists; implements `EnrichmentProvider` Protocol |
| EC2 | `CompletionProvider` adapter implemented in `acquisition/providers/completion/adapter.py` | File exists; implements `CompletionProvider` Protocol |
| EC3 | All enrichment contract tests pass (E1–E14) | `pytest test_phase3c20_wp2_2_enrichment_adapter.py -q` green |
| EC4 | All completion contract tests pass (C1–C24) | `pytest test_phase3c20_wp2_2_completion_adapter.py -q` green |
| EC5 | All WP2.1 contract tests remain green (no regressions) | `pytest test_phase3c20_wp2_1_*.py -q` green |
| EC6 | WP2 charter exit criteria E1–E13 satisfied | Per `docs/PHASE3C20_WP2_CHARTER.md` §12 |
| EC7 | C20-INV-12 enforced — no default transport in any adapter | Contract tests EC3-E8, EC4-C17 |
| EC8 | C20-INV-13 enforced — dry-run zero network egress | Contract tests EC3-E9, EC4-C18 |
| EC9 | `CompletionProvider` forbidden capabilities — 6 categories asserted absent | Contract tests EC4-C6, EC4-C7; code review |
| EC10 | `CompletionProvider` Chitu boundary — zero references to Chitu-owned code | Code review + grep audit |
| EC11 | No credential field in any WP2.2 type | Contract tests EC3-E12, EC4-C20 |
| EC12 | No vendor-specific type in any WP2.2 public interface | Contract tests EC3-E13, EC4-C21 |
| EC13 | Canonical invocation (`pytest -q`) green across all provider tests | CI-equivalent |
| EC14 | No PHP, JS, metadata, or CRM-side file modified | `git diff --stat` limited to `chitu_connector/` and `docs/` |
| EC15 | WP2 exit reconciliation documented | `docs/PHASE3C20_WP2_EXIT_RECONCILIATION.md` |
| EC16 | WP2.2 design audit document committed | This document |

## 12. Design Constraints (Non-Negotiable)

The following constraints bind all WP2.2 implementation. They derive from
the §11.1 ratification decision's seven binding constraints and are **not
subject to interpretation or relaxation**:

| # | Constraint | Origin |
|---|------------|--------|
| DC1 | No direct provider calls from CRM — all provider I/O through the connector | C20-INV-03; §11.1 Constraint C1 |
| DC2 | No secrets in EspoCRM — credential references only; actual secrets in connector environment | §11.1 Constraint 6 |
| DC3 | No autonomous actions — every `CompletionProvider` invocation operator-initiated | §11.1 Constraint 7; Charter §6 |
| DC4 | No AI runtime in CRM — `CompletionProvider` is a contract, not an execution engine | ADR §2 D2 |
| DC5 | No PHP changes — WP2.2 is connector-side only | WP2 Charter §9 |
| DC6 | No JS changes | WP2 Charter §9 |
| DC7 | No metadata changes | WP2 Charter §9 |
| DC8 | No scoring — no `AIScore` entity, no score computation | C20-INV-14; §11.1 Constraint C2 |
| DC9 | No email sending path | C20-INV-15; §11.1 Constraint C4 |
| DC10 | Chitu intelligence remains the intelligence authority | §11.1 Constraint 1 |
| DC11 | AI insights are advisory — no autonomous lifecycle mutation | §11.1 Constraint 3 |
| DC12 | Human approval required for external actions | §11.1 Constraint 7 |

## 13. WP2.2 File Manifest (Design Intent)

### 13.1 Files to Create

| # | File | Purpose |
|---|------|---------|
| F1 | `chitu_connector/chitu_connector/acquisition/providers/enrichment/adapter.py` | Concrete `EnrichmentProvider` adapter |
| F2 | `chitu_connector/chitu_connector/acquisition/providers/completion/adapter.py` | Concrete `CompletionProvider` adapter |
| F3 | `chitu-connector/tests/test_phase3c20_wp2_2_enrichment_adapter.py` | Enrichment adapter contract tests |
| F4 | `chitu-connector/tests/test_phase3c20_wp2_2_completion_adapter.py` | Completion adapter contract tests |
| F5 | `chitu-connector/tests/fixtures/wp2_2/` | Recorded fixture directory (provider responses) |
| F6 | `docs/PHASE3C20_WP2_EXIT_RECONCILIATION.md` | WP2 exit reconciliation |

### 13.2 Files NOT Modified

WP2.2 must **not** modify any file outside:

- `chitu_connector/chitu_connector/acquisition/providers/enrichment/`
- `chitu_connector/chitu_connector/acquisition/providers/completion/`
- `chitu-connector/tests/` (new test files only)
- `docs/` (documentation only)

Specifically, no modification to:
- `crm-extension/files/` (any PHP, JS, metadata, or template file)
- `chitu_connector/chitu_connector/acquisition/models.py` (backward compat)
- `chitu_connector/chitu_connector/acquisition/providers/base.py` (WP2.1 foundation)
- `chitu_connector/chitu_connector/acquisition/providers/apify_provider.py` (WP2.1 retrofit)
- `chitu_connector/chitu_connector/acquisition/providers/serper_provider.py` (WP2.1 retrofit)
- Any Chitu-owned code

### 13.3 Post-WP2.2 Provider Tree

```
chitu_connector/chitu_connector/acquisition/providers/
├── __init__.py
├── base.py                              # Shared HttpTransport, HttpRequest, HttpResponse
├── config.py                            # Provider configs
├── capabilities.py                      # Capability enum + declaration [WP2.1]
├── cost.py                              # Cost envelope [WP2.1]
├── taxonomy.py                          # Error taxonomy mapping [WP2.1]
├── search/
│   ├── __init__.py
│   └── base.py                          # SearchProvider Protocol [WP2.1]
├── enrichment/
│   ├── __init__.py
│   ├── base.py                          # EnrichmentProvider Protocol [WP2.1]
│   └── adapter.py                       # EnrichmentProvider implementation [WP2.2 NEW]
├── completion/
│   ├── __init__.py
│   ├── base.py                          # CompletionProvider Protocol [WP2.1]
│   └── adapter.py                       # CompletionProvider implementation [WP2.2 NEW]
├── apify_provider.py                    # SearchProvider impl — retrofitted [WP2.1]
└── serper_provider.py                   # SearchProvider impl — retrofitted [WP2.1]
```

## 14. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-28 | WP2 subdivided: WP2.1 (foundation) + WP2.2 (adapters) | WP2.1 Implementation Plan §12 |
| 2026-07-28 | WP2.2 scope: EnrichmentProvider adapter, CompletionProvider adapter, fixture tests, exit reconciliation | This document |
| 2026-07-28 | Adapter categories capped at 3: Search, Enrichment, Completion — no new categories | §6 |
| 2026-07-28 | `CompletionProvider` forbidden capabilities (6 categories) per ratified scope — no relaxation | §5.4; CompletionProvider Scope §5 |
| 2026-07-28 | Chitu intelligence boundary verified by code review + grep audit before WP2.2 exit | §8.5 |
| 2026-07-28 | Credential boundary: adapter receives resolved credentials via config; no `os.environ` access | §9 |
| 2026-07-28 | All WP2.2 tests use recorded-fixture pattern; dry-run with zero network egress | §10 |
| 2026-07-28 | WP2.2 does not modify any CRM-side file — connector and docs only | §13.2 |

## 15. Human Owner Approval Record

**Approved by:** Charles

**Date:** 2026-07-28

**Decision:**

I approve the Phase3C20 WP2.2 Adapter Expansion Design.

This approval authorizes WP2.2 implementation within the defined scope:
- `EnrichmentProvider` adapter implementation
- `CompletionProvider` adapter implementation per ratified scope
- Recorded-fixture contract tests
- WP2 exit reconciliation

WP2.2 is bound by:
- The seven binding constraints from the §11.1 ratification decision
- The 12 non-negotiable design constraints in §12
- The WP2 Charter exit criteria (E1–E13)
- The rule: No PHP. No JS. No metadata. No CRM-side changes.

---

*This is a documentation-only design audit. No code is modified by this
document. WP2.2 implementation follows this design as its authoritative
specification.*
