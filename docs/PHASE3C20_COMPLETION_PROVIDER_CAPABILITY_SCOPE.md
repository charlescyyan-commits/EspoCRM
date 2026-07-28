# Phase3C20 CompletionProvider Capability Scope

## 1. Status

**Status:** Active — Authorized under ADR-C20 §11.1 Option C
**Date:** 2026-07-28
**Type:** Governance scope definition — documentation only
**Phase:** Phase3C20 WP2 — Capability Ports

## 2. Governing Authority

| Document | Role |
|----------|------|
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified YES — Option C (Restricted Capability Portfolio) |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §4.1 | `CompletionProvider` port definition |
| `docs/PHASE3C20_CHARTER.md` §4 | WP2 scope: capability ports + recorded-fixture tests |
| `AGENTS.md` / `CLAUDE.md` | Governing prohibitions — unchanged |

## 3. What CompletionProvider Is

`CompletionProvider` is an **orchestration contract only**. It is a capability
port in the connector's provider abstraction layer. It does not execute AI, it
does not store secrets, it does not route provider traffic, and it does not
compute scores.

| It is | It is not |
|-------|-----------|
| An orchestration contract (`Protocol`) | An AI runtime |
| A connector-side adapter interface | A provider gateway |
| A capability port for non-Chitu LLM use cases | A secret store |
| An operator-initiated invocation path | A scoring authority |
| A recorded-fixture-testable abstraction | An autonomous agent |
| A contract that carries cost, latency, and provenance | A direct HTTP client |

### 3.1 Architecture Position

```
EspoCRM (PHP)
  Modules/AIPlatform
    AIJobService · PromptTemplateService · CredentialCustodyService  [WP3]
         │  calls via connector contract
         ▼
chitu_connector (Python)  ←── sole egress boundary
  acquisition/providers/
    base.py              ← ProviderAdapter Protocol (existing)
    apify_provider.py    ← SearchProvider impl (existing)
    serper_provider.py   ← SearchProvider impl (existing)
    completion/          ← NEW in WP2
      base.py            ← CompletionProvider Protocol
      adapter.py         ← CompletionProvider impl
         │  explicit transport injection (no default)
         ▼
  External LLM provider
```

`CompletionProvider` lives entirely on the connector side of the egress
boundary. EspoCRM never opens an HTTP connection to an LLM provider. It
dispatches a `CompletionRequest` through the connector contract and receives
a `CompletionResult`.

## 4. Allowed Capabilities

`CompletionProvider` may serve **only** capabilities that fall outside Chitu's
ownership scope. Each allowed capability requires operator initiation.

### 4.1 Research Evidence

| Aspect | Definition |
|--------|------------|
| **What it is** | AI-assisted summarization, extraction, and structuring of research data already stored in `ResearchEvidence` |
| **What it is not** | Replacement for Chitu's `website_research.py` or `single_candidate_loop.py` |
| **Input** | Structured `ResearchEvidence` payload (already-persisted CRM data) |
| **Output** | Structured summary or extraction; persisted as new or augmented `ResearchEvidence` rows with `AIRequestLog` provenance |
| **Operator role** | Operator selects a `ProspectPool` record and triggers "AI Research Summary" |
| **Chitu boundary** | Does not crawl, scrape, or search the web. Consumes already-materialized research stored in CRM. |

### 4.2 Qualification Insight

| Aspect | Definition |
|--------|------------|
| **What it is** | AI-generated contextual intelligence about a prospect — market signals, buying intent indicators, confidence explanation |
| **What it is not** | A qualification **decision** or **verdict**. Chitu owns qualification authority. |
| **Input** | `ProspectPool` record fields, linked `ResearchEvidence`, operator-provided context |
| **Output** | `AIQualificationInsight` entity (WP3) — fully immutable after create; advisory only |
| **Operator role** | Operator triggers "Generate Qualification Insight" on a `ProspectPool` record |
| **Chitu boundary** | Does not modify `canonical_score`. Does not override Chitu qualification. Does not become a PrimaryFilter authority. |

### 4.3 Draft Assistance

| Aspect | Definition |
|--------|------------|
| **What it is** | AI-assisted draft generation for operator review — proposed email content, talking points, follow-up suggestions |
| **What it is not** | Email generation or sending. Does not modify Chitu's email-generation engine. |
| **Input** | `ProspectPool` record, linked research, operator-provided direction/context |
| **Output** | Draft text presented to operator in the CRM UI; operator may edit, approve, or discard |
| **Operator role** | Operator requests a draft, reviews it, and decides whether to use it |
| **Chitu boundary** | Does not touch the email-generation engine. Does not auto-send. Draft output flows through the existing `DraftApproval` workflow — it never bypasses human review. |

### 4.4 Reply Assistance

| Aspect | Definition |
|--------|------------|
| **What it is** | AI-assisted reply classification, sentiment analysis, and suggested response categorization for inbound `ReplyEvent` records |
| **What it is not** | Automated reply handling or lifecycle mutation |
| **Input** | `ReplyEvent` record fields (status, triage data), operator context |
| **Output** | Classification label, sentiment signal, suggested categorization — advisory annotations on the `ReplyEvent` |
| **Operator role** | Operator views AI-suggested classification and accepts or overrides |
| **Chitu boundary** | Does not modify `ReplyEvent` lifecycle status. Does not become a triage authority. The existing `ReplyTriageService` remains the sole lifecycle owner. |

## 5. Forbidden Capabilities

The following are **strictly forbidden** for `CompletionProvider`. Any use case
that requires one of these must be escalated to the human owner for a separate
ratification.

### 5.1 Provider Execution

`CompletionProvider` must **never**:

- Directly invoke an LLM provider API (OpenAI, Anthropic, DeepSeek, Moonshot, or any vendor) from PHP
- Construct an HTTP client or transport within the EspoCRM PHP process
- Bypass the connector egress boundary for any reason

### 5.2 API Credentials

`CompletionProvider` must **never**:

- Store, cache, or resolve provider API keys, tokens, or secrets
- Accept credentials as request parameters
- Log or expose credentials in any form
- Manage credential rotation or lifecycle

Credentials live in the connector environment. EspoCRM stores only credential
**references** (write-only `credentialReference` field in `ProviderCredential`).

### 5.3 Autonomous Lifecycle Changes

`CompletionProvider` must **never**:

- Mutate a `ProspectPool`, `Lead`, `SendExecution`, `ReplyEvent`, `Quote`,
  `DraftApproval`, or `Opportunity` status
- Write to a Prospecting lifecycle field without operator action
- Trigger a transition service, mutation guard bypass, or action-key invocation
- Become a queue predicate or PrimaryFilter authority

### 5.4 Authoritative Scoring

`CompletionProvider` must **never**:

- Compute a score that competes with Chitu's `canonical_score`
- Create, update, or write to any field named `score`, `rating`, `rank`, or
  `canonical_score`
- Produce output that is used as an `AIScore` entity (entity forbidden by
  C20-INV-14)
- Derive a qualification verdict from any AI-generated output (C20-INV-21)

### 5.5 Direct External Calls

`CompletionProvider` must **never**:

- Open an HTTP connection from PHP to any external domain (C20-INV-03)
- Call a provider API without going through the connector
- Invoke a model without an explicit, injected transport (C20-INV-12)

### 5.6 Email Generation or Sending

`CompletionProvider` must **never**:

- Generate email content that bypasses the `DraftApproval` workflow
- Send email through any path (C20-INV-15)
- Interface with `EmailDeliveryProvider` (C21 territory)
- Modify Chitu's email-generation engine (A3)

## 6. Request / Response Boundary

### 6.1 CompletionRequest

The `CompletionRequest` is a normalized value object. No provider-native
type crosses this boundary.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capability` | enum | Yes | One of: `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE` |
| `purpose` | string | Yes | Operator-selected purpose within the capability |
| `prompt` | string | Yes | Structured prompt text — no raw user input without sanitization |
| `context` | object | Conditional | Structured CRM data payload (entity fields, linked records) |
| `model` | string | No | Requested model; resolved by `ProviderRoute` configuration if absent |
| `max_tokens` | int | No | Per-request cap; subject to cost ceiling |
| `temperature` | float | No | Provider-agnostic; adapter maps to vendor-specific parameter |
| `idempotency_key` | string | Yes | Persisted before dispatch; identical across retries (C20-INV-11) |
| `initiating_user` | string | Yes | CRM user ID — every invocation is attributable |
| `prompt_template_version` | string | No | If a `PromptTemplate` is used, its immutable version identifier |

### 6.2 CompletionResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `completion_id` | string | Yes | Provider-agnostic result identifier |
| `capability` | enum | Yes | Echo of the request capability |
| `content` | string | Yes | The generated text |
| `finish_reason` | enum | Yes | `STOP`, `LENGTH`, `CONTENT_FILTER` |
| `model` | string | Yes | Actual model used (may differ from requested) |
| `cost` | object | Yes | `{tokens_in, tokens_out, currency, amount}` — cost accounting source of truth |
| `latency_ms` | int | Yes | Round-trip in milliseconds |
| `provider_request_id` | string | Yes | Provider-side correlation id |
| `prompt_template_version` | string | No | Echo of request; required if a template was used |

### 6.3 Error Envelope

Errors normalize into the ADR-C20 §4.3 taxonomy. `CompletionProvider` must
classify every failure into exactly one `BridgeErrorClass`:

- `RATE_LIMIT` — retryable, honours `Retry-After`
- `QUOTA` — terminal, halts the capability
- `CONTENT_FILTER` — terminal, never auto-retry with the same prompt
- `AUTH` — terminal, credential alert
- `NETWORK` — retryable, backoff + jitter
- `PROVIDER` — retryable (5xx only), fail over via `ProviderRoute`

No vendor error code or raw provider response crosses the boundary.

## 7. Security Constraints

### 7.1 Transport

| Rule | Enforcement |
|------|-------------|
| No default transport | `CompletionProvider.__init__` requires injected `HttpTransport`; constructor fails without it |
| Transport injection only | Test fixtures inject `FakeHttpTransport`; production injects real transport from connector config |
| Dry-run mode | `FakeHttpTransport` returns recorded fixtures; zero network egress (C20-INV-13) |
| No PHP HTTP | C20-INV-03 enforces zero outbound HTTP from PHP |

### 7.2 Credentials

| Rule | Enforcement |
|------|-------------|
| Secrets never in request | `CompletionRequest` has no credential fields |
| Secrets never in result | `CompletionResult` has no credential fields |
| Secrets never in logs | Connector `config.py` `field(repr=False)` discipline extended to all new config types |
| Secrets never in CRM | `credentialReference` is write-only; EspoCRM never holds a provider secret |

### 7.3 Prompt Sanitization

| Rule | Enforcement |
|------|-------------|
| No raw user input in prompts | All input passes through structured `context` object; prompt text is template-driven |
| No PII in prompts | Operator is responsible; `CompletionProvider` does not validate — it passes what it receives |
| Prompt versioning | When `PromptTemplate` (WP3) lands, every invocation records the immutable template version |

### 7.4 Operator Initiation

Every `CompletionProvider` invocation requires an operator action. No
autonomous trigger, no scheduled invocation, no event-driven dispatch in C20.

## 8. Relationship with Chitu Intelligence

```
Chitu Intelligence                    EspoCRM AIPlatform
─────────────────────                ─────────────────────
canonical_score          (owns)      Consumes only — never computes
ICP matching             (owns)      Consumes only
Qualification verdicts   (owns)      Consumes only — never derives
Website research         (owns)      Consumes output; does not replicate
Email generation         (owns)      Consumes via DraftApproval; does not modify

                         (gap)       Research evidence summarization    ← CompletionProvider
                         (gap)       Qualification insight generation   ← CompletionProvider
                         (gap)       Draft assistance for operator      ← CompletionProvider
                         (gap)       Reply classification support       ← CompletionProvider
```

**The rule:** If Chitu already does it, `CompletionProvider` does not touch it.
`CompletionProvider` fills capability gaps — it does not duplicate, augment,
replace, or compete with Chitu-owned capabilities.

### 8.1 Escalation Trigger

If a proposed `CompletionProvider` use case involves any of the following, it
must be escalated to the human owner:

- Touching `canonical_score` or any scoring field
- Producing a qualification verdict
- Generating email content that could bypass `DraftApproval`
- Mutating a Prospecting lifecycle status
- Operating autonomously (scheduled, event-driven, or unattended)

## 9. WP2 Implementation Boundaries

### 9.1 WP2 Delivers

| Deliverable | Description |
|-------------|-------------|
| `CompletionProvider` Protocol | Python `Protocol` class in `acquisition/providers/completion/base.py` |
| `CompletionProvider` adapter | One concrete adapter implementation in `acquisition/providers/completion/adapter.py` |
| `CompletionRequest` / `CompletionResult` | Normalized value objects — no vendor types |
| Error classification | Full §4.3 taxonomy mapping for completion errors |
| Recorded-fixture tests | Dry-run mode with `FakeHttpTransport`; zero network egress |
| Adapter capability declaration | `capabilities: {streaming, json_mode, max_context, vision}` |
| Transport injection | Explicit `HttpTransport` parameter; no default |

### 9.2 WP2 Does NOT Deliver

| Out of scope | Owning WP |
|--------------|-----------|
| CRM-side `AIJob` dispatch, `AIJobService` | WP3 |
| `AIRequestLog` persistence and cost accounting | WP3 |
| `PromptTemplate` versioning and immutability | WP3 |
| `AIQualificationInsight` entity | WP3 |
| `ProviderRoute` configuration UI | WP3 |
| `ProviderHealth` checks | WP3 |
| `ProviderCredential` custody UI | Separate WP (WP1 blocker F3) |
| Any email sending path | C21 |
| CRM-side PHP code that calls `CompletionProvider` | WP3 (orchestration layer) |

### 9.3 WP2 Test Requirements

Every `CompletionProvider` adapter must have:

| Test class | Requirement |
|------------|-------------|
| Fixture playback | `FakeHttpTransport` returns recorded provider responses; adapter processes them correctly |
| Error classification | Each `BridgeErrorClass` variant maps correctly from vendor error to normalized taxonomy |
| Dry-run verification | Complete trace with zero network egress (C20-INV-13) |
| No default transport | Adapter construction fails without explicit transport |
| Cost envelope | Every result carries `{tokens_in, tokens_out, currency, amount}` |
| Idempotency | Same key produces same result in fixture mode |
| Capability declaration | Adapter declares its capabilities accurately |

## 10. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-27 | `CompletionProvider` port defined in ADR-C20 §4.1, gated on §11.1 | ADR-C20 §4.1, §11.1 |
| 2026-07-28 | ADR-C20 §11.1 ratified — Option C (Restricted Capability Portfolio) | `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` |
| 2026-07-28 | `CompletionProvider` capability scope defined — 4 allowed, 6 forbidden categories | This document |

## 11. Related

- `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` — ratification authority
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §4.1 — capability port definition
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §4.2 — provider abstraction rules
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §4.3 — normalized error taxonomy
- `docs/PHASE3C20_CHARTER.md` §4 — WP2 scope description
- `chitu-connector/chitu_connector/acquisition/providers/base.py` — existing `ProviderAdapter` Protocol
- `chitu-connector/chitu_connector/acquisition/providers/apify_provider.py` — transport injection precedent

---

*No PHP. No JS. No metadata. No tests. This is a governance scope definition.
WP2 implementation follows this scope as its authoritative boundary.*
