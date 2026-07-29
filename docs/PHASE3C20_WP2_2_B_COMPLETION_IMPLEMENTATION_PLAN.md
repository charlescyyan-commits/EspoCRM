# Phase3C20 WP2.2-B — CompletionProvider Bridge Implementation Plan

## 1. Status

**Status:** Plan — pending implementation
**Date:** 2026-07-29
**Type:** Read-only implementation plan — no code changes
**Phase:** Phase3C20 WP2.2-B — CompletionProvider Bridge

## 2. Governing Documents

| Document | Role |
|----------|------|
| `docs/PHASE3C20_WP2_2_ADAPTER_EXPANSION_DESIGN.md` | WP2.2 design audit — CompletionProvider bridge scope (§5), test matrix (§10.3), exit criteria (§11) |
| `docs/PHASE3C20_WP2_1_IMPLEMENTATION_PLAN.md` | WP2.1 foundation — `CompletionProvider` Protocol, `CompletionRequest`, `CompletionResult`, `CompletionCapability`, error taxonomy |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | Ratified capability scope — 4 allowed capabilities, 6 forbidden categories, security constraints |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified YES — Option C; 7 binding constraints |
| `docs/PHASE3C20_WP2_CHARTER.md` | WP2 charter — CompletionProvider definition (§6.3), architecture boundaries (§7), test strategy (§11) |
| `chitu_connector/chitu_connector/acquisition/providers/completion/base.py` | `CompletionProvider` Protocol + types — the contract the adapter implements |
| `chitu_connector/chitu_connector/acquisition/providers/taxonomy.py` | Error taxonomy — `classify_provider_error()` mapping, 8 `ErrorClass` values |
| `chitu_connector/chitu_connector/acquisition/providers/cost.py` | `CostEnvelope` dataclass |
| `chitu_connector/chitu_connector/acquisition/providers/capabilities.py` | `CapabilityDeclaration` dataclass |
| `chitu_connector/chitu_connector/acquisition/providers/serper_provider.py` | Reference adapter pattern — transport injection, error classification, capability declaration |

## 3. CompletionProvider Bridge Objective

Implement the concrete `CompletionProvider` adapter deferred from WP2.1 and
specified in the WP2.2 design audit (§5). This adapter is the **sole
connector-side bridge** between EspoCRM's governance layer and external LLM
providers for capabilities Chitu does **not** own.

### 3.1 What CompletionProvider Is

`CompletionProvider` is an **orchestration contract bridge**, not an AI
runtime. It is a capability port in the connector's provider abstraction
layer that normalizes LLM completion requests into a provider-agnostic
contract and returns normalized results with cost, latency, and provenance.

| It is | It is not |
|-------|-----------|
| An orchestration contract bridge | An AI runtime or model executor |
| A connector-side adapter implementing `CompletionProvider` Protocol | A provider gateway or router |
| A normalized interface for non-Chitu LLM capabilities | A secret store or credential manager |
| An operator-initiated, attributable invocation path | A scoring authority |
| A recorded-fixture-testable abstraction | An autonomous agent |
| A contract carrying cost, latency, and provenance | A direct HTTP client in PHP |

### 3.2 Architecture Position

```
EspoCRM (PHP)
  Modules/AIPlatform
    AIJobService · PromptTemplateService · CredentialCustodyService  [WP3]
         │  dispatches CompletionRequest via connector contract
         ▼
chitu_connector (Python)  ←── sole egress boundary
  acquisition/providers/
    completion/
      base.py              ← CompletionProvider Protocol [WP2.1]
      adapter.py           ← CompletionProvider implementation [WP2.2-B NEW]
         │  explicit transport injection (no default)
         │  maps CompletionCapability → structured prompt
         │  normalizes vendor response → CompletionResult
         ▼
  External LLM provider (OpenAI / Anthropic / DeepSeek / Moonshot)
         │
         │  Provider routing is configuration, not code (WP3 ProviderRoute)
         │  Credentials resolved from connector environment, not from CRM
```

The adapter lives entirely on the connector side of the egress boundary.
EspoCRM never opens an HTTP connection to an LLM provider (C20-INV-03).
The CRM dispatches a `CompletionRequest` and receives a `CompletionResult` —
it never sees a vendor API key, a raw provider response, or a vendor-specific
error code.

### 3.3 What WP2.2-B Delivers

| # | Deliverable | Description |
|---|-------------|-------------|
| D1 | `CompletionProvider` adapter | Concrete adapter in `acquisition/providers/completion/adapter.py` implementing the Protocol |
| D2 | Provider-agnostic bridge | Single adapter class; provider routing deferred to WP3 `ProviderRoute` |
| D3 | Completion fixture tests | Contract tests covering all 4 capabilities, error taxonomy, forbidden-capability assertions, Chitu boundary verification |
| D4 | Recorded fixtures | Pre-recorded LLM request/response pairs for deterministic replay across capabilities |
| D5 | Forbidden-capability evidence | Contract tests asserting 6 forbidden categories absent from adapter code |

### 3.4 What WP2.2-B Does NOT Deliver

- CRM-side PHP code that invokes the adapter (WP3)
- `AIJob`, `AIRequestLog`, `PromptTemplate`, or `AIQualificationInsight` entities (WP3)
- `ProviderRoute` configuration or routing logic (WP3)
- `ProviderCredential` custody UI (separate WP)
- `ProviderHealth` checks (WP3)
- Any scoring computation or `AIScore` entity (forbidden — C20-INV-14)
- Any email-sending path (forbidden — C20-INV-15)
- Any autonomous trigger or scheduled invocation (forbidden — Charter §6)
- The `EnrichmentProvider` adapter (WP2.2-A — already delivered)

## 4. Allowed Capabilities

The adapter serves exactly **four** capabilities, as ratified in the
`CompletionProvider` capability scope. No additional capability may be added
without a separate §11.1-style human ratification.

### 4.1 RESEARCH_EVIDENCE — Research Evidence Summarization

| Aspect | Definition |
|--------|------------|
| **Enum value** | `CompletionCapability.RESEARCH_EVIDENCE` |
| **What it does** | AI-assisted summarization, extraction, and structuring of research data already stored in `ResearchEvidence` records |
| **Input** | Structured `ResearchEvidence` payload (already-persisted CRM data) passed via `context` |
| **Output** | Structured summary or extraction text in `content`; operator reviews before persisting |
| **Operator trigger** | Operator selects a `ProspectPool` record and triggers "AI Research Summary" |
| **Chitu boundary** | Does **not** crawl, scrape, or search the web. Consumes already-materialized research stored in CRM. Does not replace `website_research.py` or `single_candidate_loop.py`. |
| **Prompt structure** | `context` carries `ResearchEvidence` entities (text, source URLs, confidence); adapter constructs a summarization prompt |

### 4.2 QUALIFICATION_INSIGHT — Qualification Insight Generation

| Aspect | Definition |
|--------|------------|
| **Enum value** | `CompletionCapability.QUALIFICATION_INSIGHT` |
| **What it does** | AI-generated contextual intelligence about a prospect — market signals, buying intent indicators, confidence explanation |
| **What it is NOT** | A qualification **decision** or **verdict**. Chitu owns qualification authority (C20-INV-21). |
| **Input** | `ProspectPool` record fields, linked `ResearchEvidence`, operator-provided context |
| **Output** | Advisory insight text in `content`; persisted as `AIQualificationInsight` entity (WP3) — fully immutable after create |
| **Operator trigger** | Operator triggers "Generate Qualification Insight" on a `ProspectPool` record |
| **Chitu boundary** | Does **not** modify `canonical_score`. Does not override Chitu qualification. Does not become a PrimaryFilter authority. The output is advisory — it cannot drive a lifecycle transition without operator action. |

### 4.3 DRAFT_ASSISTANCE — Draft Assistance

| Aspect | Definition |
|--------|------------|
| **Enum value** | `CompletionCapability.DRAFT_ASSISTANCE` |
| **What it does** | AI-assisted draft generation for operator review — proposed email content, talking points, follow-up suggestions |
| **What it is NOT** | Email generation or sending. Does not modify Chitu's email-generation engine (AGENTS.md A3). |
| **Input** | `ProspectPool` record, linked research, operator-provided direction/context |
| **Output** | Draft text in `content`; presented to operator in CRM UI; operator may edit, approve, or discard |
| **Operator trigger** | Operator requests a draft on a prospect record |
| **Chitu boundary** | Does **not** touch the email-generation engine. Does **not** auto-send. Draft output flows through the existing `DraftApproval` workflow — it never bypasses human review. No email is sent by this capability (C20-INV-15). |

### 4.4 REPLY_ASSISTANCE — Reply Classification Support

| Aspect | Definition |
|--------|------------|
| **Enum value** | `CompletionCapability.REPLY_ASSISTANCE` |
| **What it does** | AI-assisted reply classification, sentiment analysis, and suggested response categorization for inbound `ReplyEvent` records |
| **What it is NOT** | Automated reply handling or lifecycle mutation |
| **Input** | `ReplyEvent` record fields (status, triage data), operator context |
| **Output** | Classification label, sentiment signal, suggested categorization in `content`; advisory annotations on the `ReplyEvent` |
| **Operator trigger** | Operator views AI-suggested classification and accepts or overrides |
| **Chitu boundary** | Does **not** modify `ReplyEvent` lifecycle status. Does not become a triage authority. The existing `ReplyTriageService` remains the sole lifecycle owner. |

### 4.5 Capability Cardinality Lock

The `CompletionCapability` enum has exactly 4 values. This is enforced by
WP2.1 contract test C1 and must remain unchanged by WP2.2-B. No new enum
value may be added. No existing value may be removed or renamed. Any
capability expansion requires a separate human ratification.

## 5. Request / Response Boundary

### 5.1 CompletionRequest (Input)

The adapter accepts the WP2.1 `CompletionRequest` — a frozen, provider-agnostic
value object. No provider-native type crosses this boundary.

| Field | Type | Required | Adapter Usage |
|-------|------|----------|---------------|
| `capability` | `CompletionCapability` | Yes | Routes to capability-specific prompt construction |
| `purpose` | `str` | Yes | Included in system prompt as operator intent |
| `prompt` | `str` | Yes | The structured prompt text — passed to LLM as the user message |
| `context` | `Mapping[str, Any] \| None` | Conditional | Structured CRM data payload; injected into system prompt as structured context |
| `model` | `str \| None` | No | Requested model; adapter passes to LLM API; if `None`, uses default from config |
| `max_tokens` | `int \| None` | No | Per-request token cap; passed to LLM API |
| `temperature` | `float \| None` | No | Provider-agnostic; adapter passes to LLM API as-is |
| `idempotency_key` | `str` | Yes | `repr=False` — passed to LLM API as `Idempotency-Key` header; never logged |
| `initiating_user` | `str` | Yes | Passed as metadata; every invocation is attributable |
| `prompt_template_version` | `str \| None` | No | Echoed in result; required when `PromptTemplate` (WP3) is used |

### 5.2 CompletionResult (Output)

The adapter returns a `CompletionResult` — a frozen, provider-agnostic value
object. No provider-native type crosses this boundary.

| Field | Type | Required | Adapter Role |
|-------|------|----------|-------------|
| `completion_id` | `str` | Yes | Generated by adapter; unique per invocation |
| `capability` | `CompletionCapability` | Yes | Echo of the request capability |
| `content` | `str` | Yes | The LLM-generated text |
| `finish_reason` | `str` | Yes | One of `STOP`, `LENGTH`, `CONTENT_FILTER` — normalized from vendor response |
| `model` | `str` | Yes | Actual model used (may differ from requested) |
| `cost` | `CostEnvelope` | Yes | `{tokens_in, tokens_out, model, latency_ms, provider_request_id, currency, amount}` — cost accounting source of truth |
| `prompt_template_version` | `str \| None` | No | Echo of request; required if a template was used |

### 5.3 Request → Response Flow

```
CompletionRequest (frozen)
  │
  ▼
Adapter.complete()
  │  1. Validate capability ∈ CompletionCapability (exhaustive match)
  │  2. Validate finish_reason will pass __post_init__ on result construction
  │  3. Construct system prompt from capability + purpose + context
  │  4. Build vendor-agnostic HTTP request (JSON body with messages array)
  │  5. Send via injected transport
  │  6. Classify errors via classify_provider_error() on failure
  │  7. Parse vendor response → extract content, finish_reason, model, usage
  │  8. Construct CostEnvelope from usage data + latency measurement
  │  9. Return CompletionResult
  ▼
CompletionResult (frozen)
```

### 5.4 Capability-Specific Prompt Construction

The adapter constructs a structured system prompt per capability. The `prompt`
field from the request is always the user message. The system prompt is
assembled from capability-specific instructions + context:

```python
_SYSTEM_PROMPTS = {
    CompletionCapability.RESEARCH_EVIDENCE: (
        "You are an AI research assistant. Summarize and structure the provided "
        "research evidence. Do not fabricate information. If the evidence is "
        "insufficient, state that clearly. Do not produce scores, qualification "
        "verdicts, or email content."
    ),
    CompletionCapability.QUALIFICATION_INSIGHT: (
        "You are an AI qualification analyst. Generate contextual intelligence "
        "about the prospect — market signals, buying intent indicators, and "
        "confidence factors. Your output is ADVISORY ONLY. You do not produce "
        "qualification decisions, scores, or verdicts. State uncertainties clearly."
    ),
    CompletionCapability.DRAFT_ASSISTANCE: (
        "You are an AI draft assistant. Generate proposed text for operator review "
        "based on the provided context. The operator will review, edit, and decide "
        "whether to use the output. Do not send anything. Do not produce scores or "
        "qualification verdicts."
    ),
    CompletionCapability.REPLY_ASSISTANCE: (
        "You are an AI reply classifier. Analyze the inbound reply and provide "
        "classification, sentiment, and suggested categorization. Your output is "
        "ADVISORY ONLY. You do not modify reply lifecycle status or become a "
        "triage authority."
    ),
}
```

Each system prompt explicitly disclaims the forbidden capabilities. This is a
**design-level guard**, not a runtime enforcement — it constrains what the
adapter asks the LLM to do, reducing the risk of capability creep.

### 5.5 Vendor-Agnostic HTTP Construction

The adapter constructs a provider-agnostic HTTP request. Provider-specific
details (endpoint URL, auth header format, model mapping) are resolved from
the injected config. The adapter does **not** contain vendor-specific URL
templates or auth schemes in its code — those live in config.

```python
def _build_request(self, cr: CompletionRequest) -> HttpRequest:
    messages = [
        {"role": "system", "content": self._system_prompt(cr)},
        {"role": "user",   "content": cr.prompt},
    ]
    body = {
        "model": cr.model or self._config.default_model,
        "messages": messages,
        "max_tokens": cr.max_tokens or self._config.default_max_tokens,
        "temperature": cr.temperature if cr.temperature is not None else self._config.default_temperature,
    }
    return HttpRequest(
        method="POST",
        url=f"{self._config.base_url.rstrip('/')}/chat/completions",
        headers=self._headers(cr.idempotency_key),
        body=json.dumps(body, separators=(",", ":")).encode("utf-8"),
    )
```

### 5.6 Finish Reason Normalization

The adapter maps vendor-specific finish reasons to the three allowed values.
`CompletionResult.__post_init__` enforces the set at construction time.

| Vendor Finish Reason | Normalized | Notes |
|---------------------|------------|-------|
| `stop` | `STOP` | Normal completion |
| `length` | `LENGTH` | Token limit reached — output may be truncated |
| `content_filter` | `CONTENT_FILTER` | Provider rejected the request — terminal, never auto-retry with same prompt |
| `tool_calls` | `STOP` | Adapter does not use tool calls; maps to STOP |
| Any other value | `STOP` | Default — adapter logs a warning but does not reject |

### 5.7 Cost Envelope Construction

Every `CompletionResult` carries a mandatory `CostEnvelope`. The adapter
measures latency from transport send to response receipt:

```python
start = time.monotonic()
response = self._transport.send(http_request)
latency_ms = int((time.monotonic() - start) * 1000)

cost = CostEnvelope(
    tokens_in=usage.get("prompt_tokens", 0),
    tokens_out=usage.get("completion_tokens", 0),
    model=actual_model,
    latency_ms=latency_ms,
    provider_request_id=response_headers.get("x-request-id", ""),
    currency="USD",
    amount=0.0,  # computed by WP3 cost accounting from tokens + model pricing table
)
```

Cost computation (USD amount) is deferred to WP3 cost accounting. The adapter
captures token counts, model, latency, and provider request ID — the raw data
needed for cost attribution. The `amount` field is `0.0` at the adapter layer
and is populated by WP3 governance infrastructure from a model pricing table.

## 6. Chitu Intelligence Boundary

### 6.1 The Rule

**If Chitu already does it, `CompletionProvider` does not touch it.**
`CompletionProvider` fills capability gaps — it does not duplicate, augment,
replace, or compete with Chitu-owned capabilities.

### 6.2 Ownership Matrix

| Chitu Intelligence Owns | CompletionProvider Must Not Touch |
|--------------------------|----------------------------------|
| `canonical_score` (`canonical_score.py`, `scoring.py`) | No score computation; no field named `score`/`rating`/`rank`/`canonical_score`; no `AIScore` entity (C20-INV-14) |
| Qualification verdicts | No qualification decisions; advisory insight only (C20-INV-21) |
| ICP matching (`icp.py`) | No ICP computation |
| Website research (`website_research.py`) | No web crawling or scraping |
| Single candidate loop (`single_candidate_loop.py`) | No candidate processing pipeline |
| Email generation engine | No email content generation bypassing `DraftApproval`; no modification (AGENTS.md A3) |
| `chitu_connector/vendored/contracts/` (Chitu-owned) | No import or dependency on Chitu vendored contracts |

### 6.3 Design-Level Verification

The `CompletionProvider` adapter code must contain **zero references** to:

- `canonical_score`
- `scoring`
- `icp`
- `website_research`
- `single_candidate_loop`
- `email_generation`
- Any module under `chitu_connector/vendored/contracts/` owned by Chitu
- Any import from `chitu_connector.espocrm_sync` that mutates CRM lifecycle state

This is enforced by a **contract test** (C-chitu-1) that greps the adapter
source for banned identifiers — and by **code review** before WP2.2-B exit.

### 6.4 Capability Gap Rationale

| Gap Chitu Does Not Fill | CompletionProvider Role | Relationship to Chitu |
|--------------------------|------------------------|----------------------|
| Research evidence summarization | Summarize already-persisted CRM research data | Consumes Chitu's research output; does not replicate the research pipeline |
| Qualification insight generation | Generate contextual intelligence for operator review | Advisory only; does not override Chitu qualification verdicts |
| Draft assistance | Generate proposed text for operator editing | Flows through `DraftApproval`; does not modify the email-generation engine |
| Reply classification support | Classify and categorize inbound replies | Advisory annotation; `ReplyTriageService` remains sole lifecycle owner |

### 6.5 Escalation Trigger

If a proposed `CompletionProvider` use case involves any of the following, it
must be escalated to the human owner for separate ratification:

- Touching `canonical_score` or any scoring field
- Producing a qualification verdict (as distinct from advisory insight)
- Generating email content that could bypass `DraftApproval`
- Mutating a Prospecting lifecycle status
- Operating autonomously (scheduled, event-driven, or unattended)
- Replicating or augmenting any Chitu-owned pipeline

## 7. Human Approval Boundary

### 7.1 Operator Initiation — Non-Negotiable

Every `CompletionProvider` invocation is **operator-initiated**. The
`initiating_user` field on `CompletionRequest` is required. No invocation
may occur without an attributable operator action.

| Mechanism |Permitted? | Rule |
|-----------|-----------|------|
| Operator clicks "Generate" in CRM UI | **Yes** | `initiating_user` populated from session |
| Scheduled cron job | **No** | Charter §6 — no autonomous trigger |
| Event-driven hook (entity save, status change) | **No** | Charter §6 — no event-driven dispatch |
| Background worker polling a queue | **No** | Charter §6 — no unattended invocation |
| Batch operation initiated by operator | **Yes** | Each record requires individual operator confirmation |
| API call with valid `initiating_user` | **Yes** | Attributable; audit trail recorded by WP3 `AIRequestLog` |

### 7.2 Advisory-Only Output

AI-generated output is **advisory** and cannot become an authoritative CRM
lifecycle decision without human approval:

| Output Type | Operator Action Required |
|-------------|--------------------------|
| Research evidence summary | Operator reviews → approves → persist as `ResearchEvidence` |
| Qualification insight | Operator reviews → `AIQualificationInsight` created as immutable advisory record |
| Draft text | Operator reviews → edits/approves/discards → if approved, flows through `DraftApproval` |
| Reply classification | Operator views suggestion → accepts or overrides → manual triage action |

No AI-generated output may drive a status transition, queue predicate, or
lifecycle mutation without operator approval (§11.1 Constraint 3).

### 7.3 Draft → Approval Chain

For `DRAFT_ASSISTANCE`, the output follows this chain:

```
Operator requests draft
  → Adapter generates draft text (CompletionResult.content)
  → Operator reviews draft in CRM UI
  → Operator edits, approves, or discards
  → If approved: draft enters DraftApproval workflow (existing C19 path)
  → DraftApproval applies policy checks, approval gates, and send authorization
  → SendExecution created only after DraftApproval releases
```

At no point does `CompletionProvider` send an email, bypass `DraftApproval`,
or modify the email-generation engine. The adapter produces text — everything
after is existing CRM workflow (C20-INV-15).

## 8. Error Taxonomy Usage

### 8.1 Shared Taxonomy (Reused from WP2.1)

The adapter uses the existing `classify_provider_error()` function from
`providers/taxonomy.py`. No new taxonomy code is written in WP2.2-B.

### 8.2 Completion-Specific Error Handling

The adapter follows the `serper_provider.py` error pattern with one addition:
`CONTENT_FILTER` handling, which is specific to LLM completion.

```python
def _send(self, request: HttpRequest) -> HttpResponse:
    try:
        response = self._transport.send(request)
    except TimeoutError as error:
        raise _provider_error("COMPLETION_TIMEOUT", "LLM request timed out", 0) from error
    except OSError as error:
        raise _provider_error("COMPLETION_TRANSPORT_ERROR", "LLM transport failed", 0) from error
    if response.status_code >= 400:
        raise self._http_error(response)
    return response

@staticmethod
def _http_error(response: HttpResponse) -> ProviderError:
    status_code = response.status_code
    # CONTENT_FILTER — check response body for content-filter indicators
    if _is_content_filter(response):
        return _provider_error(
            "COMPLETION_CONTENT_FILTER",
            "LLM content filter rejected the request — do not retry with the same prompt",
            status_code,
        )
    if status_code == 429:
        retry_after = _parse_retry_after(response.headers)
        return _rate_limit_error("COMPLETION_RATE_LIMITED", "LLM rate limit reached", retry_after)
    if status_code >= 500:
        return _provider_error("COMPLETION_UPSTREAM_ERROR", "LLM service failed", status_code)
    if status_code == 401 or status_code == 403:
        return _provider_error("COMPLETION_AUTH_FAILED", "LLM authentication failed", status_code)
    if status_code == 402:
        return _provider_error("COMPLETION_QUOTA_EXHAUSTED", "LLM quota exhausted", status_code)
    return _provider_error(
        f"COMPLETION_HTTP_{status_code}", "LLM provider rejected the request", status_code
    )
```

### 8.3 CONTENT_FILTER Detection

`CONTENT_FILTER` is the most critical error class for CompletionProvider. It
is **terminal** — the adapter must never auto-retry with the same prompt.
Detection logic:

```python
def _is_content_filter(response: HttpResponse) -> bool:
    """Detect content-filter rejection from vendor response.
    
    Checks both the HTTP status code (400 with specific patterns) and the
    response body for content-filter indicators.  This is intentionally
    conservative: when unsure, classify as VALIDATION rather than
    CONTENT_FILTER — only clear content-filter signals trigger the
    terminal class.
    """
    if response.status_code != 400:
        return False
    body_str = _body_string(response)
    content_filter_markers = (
        "content_filter", "content filter", "content_policy",
        "safety", "moderation", "inappropriate",
    )
    return any(marker in body_str.lower() for marker in content_filter_markers)
```

### 8.4 Full Error Taxonomy — Completion Mapping

| ErrorClass | Trigger | Retryable | Completion-Specific Behaviour |
|------------|---------|-----------|------------------------------|
| `NETWORK` | `TimeoutError`, `OSError` in transport call | Yes | Backoff + jitter; same prompt safe to retry |
| `PROVIDER` | HTTP 5xx | Yes | Backoff; fail over via `ProviderRoute` (WP3) |
| `AUTH` | HTTP 401, 403 | **No** — terminal | Credential alert; halt capability |
| `RATE_LIMIT` | HTTP 429 | Yes | Honour `Retry-After`; no attempt budget consumed |
| `QUOTA` | HTTP 402 | **No** — terminal | Halt capability; operator-review required |
| `VALIDATION` | HTTP 400 (non-content-filter) | **No** — terminal | Caller defect; fix request before retry |
| `CONTENT_FILTER` | HTTP 400 + content-filter markers in body | **No** — terminal | **Never auto-retry with same prompt**; operator must review and revise |
| `UNKNOWN` | Any unclassified error | **No** — terminal | Operator review |

### 8.5 Shared Error Helpers (Replicated Per Adapter Pattern)

```python
def _provider_error(code: str, safe_message: str, status_code: int) -> ProviderError:
    classified = classify_provider_error(status_code, code)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    return error

def _rate_limit_error(code: str, safe_message: str, retry_after: int | None) -> ProviderRateLimitError:
    classified = classify_provider_error(429, code, retry_after=retry_after)
    error = ProviderRateLimitError(
        code, safe_message,
        retryable=classified.retryable,
        retry_after=classified.retry_after,
    )
    error.error_class = classified.error_class
    return error

def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    for key in ("retry-after", "Retry-After"):
        value = headers.get(key)
        if value is None:
            continue
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            continue
        if seconds >= 0:
            return seconds
    return None
```

### 8.6 Retry Policy

Retry policy keys off `ErrorClass`, never off vendor error codes (ADR §4.3):

| Retryable | Classes |
|-----------|---------|
| **Auto-retry eligible** | `NETWORK`, `PROVIDER`, `RATE_LIMIT` |
| **Never auto-retry** | `AUTH`, `VALIDATION`, `UNKNOWN`, `QUOTA`, `CONTENT_FILTER` |

`CONTENT_FILTER` is uniquely dangerous for LLM completion — retrying with the
same prompt will produce the same filter rejection. The operator must review
and revise the prompt before re-invocation. The adapter never retries a
`CONTENT_FILTER` result.

## 9. Fixture Testing Strategy

### 9.1 Recorded-Fixture Pattern (Reused)

All tests follow the recorded-fixture pattern from WP2.1 §8.1:

```
1. Record:    Real LLM call → capture request + response → store as JSON fixture
2. Replay:    FakeHttpTransport serves fixture → adapter processes → assert CompletionResult
3. Dry-run:   Complete trace with zero network egress (C20-INV-13)
4. Error:     FakeHttpTransport serves error fixture → adapter classifies → assert ErrorClass
```

### 9.2 FakeHttpTransport (Reused Without Modification)

```python
class FakeHttpTransport:
    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
```

### 9.3 Per-Capability Happy-Path Tests

| # | Test | Fixture | Assertion |
|---|------|---------|-----------|
| C-H1 | `RESEARCH_EVIDENCE` — happy path | `completion_research_evidence.json` | `CompletionResult` with `capability=RESEARCH_EVIDENCE`, `finish_reason=STOP`, `cost` populated, `content` non-empty |
| C-H2 | `QUALIFICATION_INSIGHT` — happy path | `completion_qualification_insight.json` | `CompletionResult` with `capability=QUALIFICATION_INSIGHT`, advisory-only system prompt verified |
| C-H3 | `DRAFT_ASSISTANCE` — happy path | `completion_draft_assistance.json` | `CompletionResult` with `capability=DRAFT_ASSISTANCE`, content is draft text; no email sent |
| C-H4 | `REPLY_ASSISTANCE` — happy path | `completion_reply_assistance.json` | `CompletionResult` with `capability=REPLY_ASSISTANCE`, classification content present |
| C-H5 | `context` passed through to system prompt | `completion_research_evidence.json` | System prompt contains structured context from request |

### 9.4 Error Taxonomy Tests

| # | Test | Fixture | Assertion |
|---|------|---------|-----------|
| C-E1 | Transport `TimeoutError` → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| C-E2 | Transport `OSError` → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| C-E3 | HTTP 401 → `AUTH` | Error fixture | `ProviderError` with `error_class=AUTH`, `retryable=False` |
| C-E4 | HTTP 403 → `AUTH` | Error fixture | `ProviderError` with `error_class=AUTH`, `retryable=False` |
| C-E5 | HTTP 429 → `RATE_LIMIT` with `retry_after` | `completion_error_429.json` | `ProviderRateLimitError` with `error_class=RATE_LIMIT`, `retryable=True`, `retry_after` populated |
| C-E6 | HTTP 500 → `PROVIDER` | Error fixture | `ProviderError` with `error_class=PROVIDER`, `retryable=True` |
| C-E7 | HTTP 502 → `PROVIDER` | Error fixture | `ProviderError` with `error_class=PROVIDER`, `retryable=True` |
| C-E8 | HTTP 402 → `QUOTA` | Error fixture | `ProviderError` with `error_class=QUOTA`, `retryable=False` |
| C-E9 | HTTP 400 (non-filter) → `VALIDATION` | Error fixture | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| C-E10 | HTTP 400 + content-filter body → `CONTENT_FILTER` | `completion_error_content_filter.json` | `ProviderError` with `error_class=CONTENT_FILTER`, `retryable=False` |

### 9.5 Cost Envelope Tests

| # | Test | Assertion |
|---|------|-----------|
| C-K1 | Cost envelope present on every result | `result.cost` is `CostEnvelope` instance (not None) |
| C-K2 | `tokens_in` > 0 | Token usage captured from vendor response |
| C-K3 | `tokens_out` > 0 | Token usage captured from vendor response |
| C-K4 | `model` matches actual model used | May differ from requested model |
| C-K5 | `latency_ms` > 0 | Latency measured from transport send to response receipt |
| C-K6 | `provider_request_id` populated | From response headers or generated |
| C-K7 | `currency` == `"USD"` | Default |
| C-K8 | `amount` == `0.0` | Deferred to WP3 cost accounting |

### 9.6 Finish Reason Tests

| # | Test | Assertion |
|---|------|-----------|
| C-F1 | `STOP` — accepted | `CompletionResult` constructed successfully |
| C-F2 | `LENGTH` — accepted | `CompletionResult` constructed successfully |
| C-F3 | `CONTENT_FILTER` — accepted | `CompletionResult` constructed successfully |
| C-F4 | Invalid finish reason → `ValueError` | `CompletionResult.__post_init__` raises `ValueError` |

### 9.7 Forbidden Capability Tests

| # | Test | Assertion |
|---|------|-----------|
| C-X1 | No `SCORING` enum value in `CompletionCapability` | WP2.1 test C7 — must remain green |
| C-X2 | No `EMAIL_GENERATION` enum value in `CompletionCapability` | WP2.1 test C8 — must remain green |
| C-X3 | No scoring reference in adapter source | Grep for `canonical_score`, `scoring`, `AIScore` — zero matches |
| C-X4 | No Chitu pipeline reference in adapter source | Grep for `website_research`, `single_candidate_loop`, `icp` — zero matches |
| C-X5 | No email-sending reference in adapter source | Grep for `email_generation`, `send_email`, `EmailDelivery` — zero matches |
| C-X6 | No lifecycle mutation reference in adapter source | Grep for `ProspectPool`, `SendExecution`, `ReplyEvent`, `transition` — zero matches |
| C-X7 | No credential field in `CompletionRequest` or `CompletionResult` | WP2.1 test C5 — must remain green |
| C-X8 | No vendor-specific type in public interface | WP2.1 test C6 — must remain green |
| C-X9 | `idempotency_key` is `repr=False` on `CompletionRequest` | WP2.1 test C9 — must remain green |
| C-X10 | `initiating_user` is required on `CompletionRequest` | WP2.1 test C10 — must remain green |

### 9.8 Transport and Boundary Tests

| # | Test | Assertion |
|---|------|-----------|
| C-T1 | Construction fails without explicit transport | `TypeError` — C20-INV-12 |
| C-T2 | Dry-run — zero network egress | `FakeHttpTransport.requests` recorded; no socket opened — C20-INV-13 |
| C-T3 | Capability declaration populated | `capabilities.capability == Capability.COMPLETION`; `supports_json_mode=True` |
| C-T4 | No credential field in request or result | Dataclass field scan |
| C-T5 | No vendor-specific type in public interface | Return type is `CompletionResult`; no vendor SDK type |
| C-T6 | Idempotency — same key produces same result | Two invocations with same `idempotency_key` return identical `CompletionResult` |
| C-T7 | `initiating_user` carried through | Set on request; adapter does not drop it |
| C-T8 | `prompt_template_version` echoed in result | Set on request → present on result |
| C-T9 | No `import requests`, `import httpx`, `import urllib3` | Code review + grep audit |
| C-T10 | No `os.environ` access in adapter code | Code review + grep audit |
| C-T11 | No `print()` or `logging.info()` of request/response bodies | Code review |

### 9.9 Fixture Files

| # | File | Purpose |
|---|------|---------|
| F1 | `chitu-connector/tests/fixtures/wp2_2/completion_research_evidence.json` | Recorded RESEARCH_EVIDENCE request/response |
| F2 | `chitu-connector/tests/fixtures/wp2_2/completion_qualification_insight.json` | Recorded QUALIFICATION_INSIGHT request/response |
| F3 | `chitu-connector/tests/fixtures/wp2_2/completion_draft_assistance.json` | Recorded DRAFT_ASSISTANCE request/response |
| F4 | `chitu-connector/tests/fixtures/wp2_2/completion_reply_assistance.json` | Recorded REPLY_ASSISTANCE request/response |
| F5 | `chitu-connector/tests/fixtures/wp2_2/completion_error_429.json` | Recorded 429 rate-limit response |
| F6 | `chitu-connector/tests/fixtures/wp2_2/completion_error_content_filter.json` | Recorded content-filter rejection response |

### 9.10 Test File and Class Structure

```python
# test_phase3c20_wp2_2_b_completion_adapter.py

class CompletionProviderHappyPathTests:
    """C-H1–C-H5 — per-capability fixture replay tests."""

class CompletionProviderErrorTaxonomyTests:
    """C-E1–C-E10 — error classification across all 8 ErrorClass values."""

class CompletionProviderCostEnvelopeTests:
    """C-K1–C-K8 — cost envelope structure and completeness."""

class CompletionProviderFinishReasonTests:
    """C-F1–C-F4 — finish_reason normalization and validation."""

class CompletionProviderForbiddenCapabilityTests:
    """C-X1–C-X10 — forbidden capabilities, Chitu boundary, credential absence."""

class CompletionProviderTransportBoundaryTests:
    """C-T1–C-T11 — transport injection, dry-run, invariants, code-quality checks."""
```

### 9.11 WP2.1 Test Continuity

The existing WP2.1 completion protocol tests
(`test_phase3c20_wp2_1_completion_provider.py`) must remain green. WP2.2-B
does not modify any WP2.1 test file. The WP2.1 tests verify the Protocol
structure and enum cardinality; WP2.2-B tests verify the concrete adapter
implementation.

## 10. Credential Handling

### 10.1 Credential Boundary

```
EspoCRM (PHP)                          chitu_connector (Python)
─────────────────                      ────────────────────────
ProviderCredential entity              Connector environment
  credentialReference: "llm-prod"        LLM_API_KEY=sk-...
  (write-only, no secret stored)         (env var / secrets manager)

CompletionRequest                       Adapter receives CompletionConfig
  (no credential field exists)            config.api_key  ← resolved by config infra
                                          config.base_url ← resolved by config infra
```

### 10.2 CompletionConfig

```python
@dataclass(frozen=True, slots=True)
class CompletionConfig:
    api_key: str = field(repr=False)
    base_url: str
    default_model: str
    default_max_tokens: int = 4096
    default_temperature: float = 0.7
```

The config dataclass uses `repr=False` on `api_key`. The adapter never reads
`os.environ`, never constructs a credential, and never logs a credential.

### 10.3 Design Enforcement

| # | Rule | How Enforced |
|---|------|-------------|
| C1 | `CompletionRequest` has zero credential fields | WP2.1 contract test C5 (already passing) |
| C2 | `CompletionResult` has zero credential fields | WP2.1 contract test C5 (already passing) |
| C3 | Config dataclass uses `repr=False` on `api_key` | Code review |
| C4 | Adapter never accesses `os.environ` | Code review + grep audit |
| C5 | Adapter never logs request headers or response bodies | Code review |
| C6 | Adapter never constructs a default HTTP client | Constructor requires `transport: HttpTransport` — C20-INV-12 |

## 11. Files to Create

### 11.1 New Files

| # | File | Purpose |
|---|------|---------|
| F1 | `chitu_connector/chitu_connector/acquisition/providers/completion/adapter.py` | `CompletionProvider` concrete adapter implementation |
| F2 | `chitu-connector/tests/test_phase3c20_wp2_2_b_completion_adapter.py` | Completion adapter contract tests (6 test classes, 45+ assertions) |
| F3 | `chitu-connector/tests/fixtures/wp2_2/completion_research_evidence.json` | Recorded RESEARCH_EVIDENCE fixture |
| F4 | `chitu-connector/tests/fixtures/wp2_2/completion_qualification_insight.json` | Recorded QUALIFICATION_INSIGHT fixture |
| F5 | `chitu-connector/tests/fixtures/wp2_2/completion_draft_assistance.json` | Recorded DRAFT_ASSISTANCE fixture |
| F6 | `chitu-connector/tests/fixtures/wp2_2/completion_reply_assistance.json` | Recorded REPLY_ASSISTANCE fixture |
| F7 | `chitu-connector/tests/fixtures/wp2_2/completion_error_429.json` | Recorded 429 error fixture |
| F8 | `chitu-connector/tests/fixtures/wp2_2/completion_error_content_filter.json` | Recorded content-filter error fixture |

### 11.2 Files NOT Modified

WP2.2-B must **not** modify any file outside:

- `chitu_connector/chitu_connector/acquisition/providers/completion/adapter.py` (new)
- `chitu-connector/tests/test_phase3c20_wp2_2_b_completion_adapter.py` (new)
- `chitu-connector/tests/fixtures/wp2_2/completion_*.json` (new)

Specifically, no modification to:
- Any `crm-extension/files/` file (PHP, JS, metadata, template)
- `chitu_connector/chitu_connector/acquisition/providers/completion/__init__.py` (WP2.1)
- `chitu_connector/chitu_connector/acquisition/providers/completion/base.py` (WP2.1 Protocol)
- `chitu_connector/chitu_connector/acquisition/providers/taxonomy.py` (WP2.1)
- `chitu_connector/chitu_connector/acquisition/providers/cost.py` (WP2.1)
- `chitu_connector/chitu_connector/acquisition/providers/capabilities.py` (WP2.1)
- Any enrichment, search, or existing adapter file

### 11.3 Post-WP2.2-B Provider Tree

```
chitu_connector/chitu_connector/acquisition/providers/
├── __init__.py                          [UNCHANGED]
├── base.py                              [UNCHANGED]
├── config.py                            [UNCHANGED]
├── capabilities.py                      [UNCHANGED]
├── cost.py                              [UNCHANGED]
├── taxonomy.py                          [UNCHANGED]
├── search/
│   ├── __init__.py                      [UNCHANGED]
│   └── base.py                          [UNCHANGED]
├── enrichment/
│   ├── __init__.py                      [UNCHANGED]
│   ├── base.py                          [UNCHANGED]
│   └── adapter.py                       [WP2.2-A]
├── completion/
│   ├── __init__.py                      [UNCHANGED]
│   ├── base.py                          [UNCHANGED]
│   └── adapter.py                       [NEW — WP2.2-B]
├── apify_provider.py                    [UNCHANGED]
└── serper_provider.py                   [UNCHANGED]
```

## 12. Exit Criteria

WP2.2-B exits when **all** of the following are true:

| # | Criterion | Evidence |
|---|-----------|----------|
| EC1 | `adapter.py` created with `CompletionProvider` concrete class | File exists; implements `CompletionProvider` Protocol |
| EC2 | `CompletionConfig` dataclass defined with `repr=False` on `api_key` | Code review |
| EC3 | All 4 capability happy-path tests passing (C-H1–C-H5) | `pytest test_phase3c20_wp2_2_b_completion_adapter.py -q -k HappyPath` green |
| EC4 | All 10 error taxonomy tests passing (C-E1–C-E10) | `pytest ... -q -k ErrorTaxonomy` green |
| EC5 | All 8 cost envelope tests passing (C-K1–C-K8) | `pytest ... -q -k CostEnvelope` green |
| EC6 | All 4 finish reason tests passing (C-F1–C-F4) | `pytest ... -q -k FinishReason` green |
| EC7 | All 10 forbidden capability tests passing (C-X1–C-X10) | `pytest ... -q -k ForbiddenCapability` green |
| EC8 | All 11 transport/boundary tests passing (C-T1–C-T11) | `pytest ... -q -k TransportBoundary` green |
| EC9 | Existing WP2.1 completion protocol tests remain green | `pytest test_phase3c20_wp2_1_completion_provider.py -q` green |
| EC10 | All WP2.1 tests remain green (no regressions) | `pytest test_phase3c20_wp2_1_*.py -q` green |
| EC11 | C20-INV-12 enforced — no default transport | Contract test C-T1 |
| EC12 | C20-INV-13 enforced — dry-run zero network egress | Contract test C-T2 |
| EC13 | Chitu boundary verified — zero references to Chitu-owned code | Contract tests C-X3–C-X6 |
| EC14 | 6 forbidden completion categories asserted absent | Contract tests C-X1–C-X8 |
| EC15 | `CONTENT_FILTER` classified as terminal — never auto-retry with same prompt | Contract test C-E10 |
| EC16 | No credential field in any WP2.2-B type | Contract test C-T4 |
| EC17 | No vendor-specific type in public interface | Contract test C-T5 |
| EC18 | No `os.environ` access in adapter code | Code review + grep audit |
| EC19 | No `import requests`, `import httpx`, `import urllib3` in adapter code | Code review + grep audit |
| EC20 | No `print()` or `logging.info()` of request/response bodies | Code review |
| EC21 | No bare `except Exception: pass` around transport calls | Code review |
| EC22 | Canonical invocation green | `pytest chitu-connector/tests/ -q` green (all provider tests) |
| EC23 | No PHP, JS, metadata, or CRM-side file modified | `git diff --stat` limited to `chitu_connector/` and `chitu-connector/tests/` |
| EC24 | No modification to `completion/__init__.py` or `completion/base.py` | `git diff` confirms zero changes to WP2.1 files |
| EC25 | WP2 charter exit criteria E3, E10, E11 satisfied for CompletionProvider | Per WP2 Charter §12 |
| EC26 | `CompletionCapability` enum unchanged — exactly 4 values | WP2.1 test C1 remains green |

## 13. Design Constraints (Non-Negotiable)

| # | Constraint | Origin |
|---|------------|--------|
| DC1 | No direct provider calls from CRM — all LLM I/O through the connector | C20-INV-03; §11.1 Constraint C1 |
| DC2 | No secrets in EspoCRM — credential references only; `api_key` in connector environment | §11.1 Constraint 6 |
| DC3 | No AI runtime in CRM — `CompletionProvider` is a bridge contract, not an execution engine | ADR §2 D2 |
| DC4 | No autonomous actions — every invocation operator-initiated via `initiating_user` | §11.1 Constraint 7; Charter §6 |
| DC5 | No PHP, JS, or metadata changes | WP2 Charter §9 |
| DC6 | No scoring — no `AIScore` entity; no `canonical_score` computation; no field named `score`/`rating`/`rank` | C20-INV-14; §11.1 Constraint C2 |
| DC7 | No qualification verdicts — advisory insight only | C20-INV-21; §11.1 Constraint 1 |
| DC8 | No email sending — draft text only; flows through `DraftApproval` | C20-INV-15; §11.1 Constraint C4 |
| DC9 | No modification to Chitu-owned code | AGENTS.md A1–A4 |
| DC10 | Transport injection mandatory — no default transport | C20-INV-12 |
| DC11 | Dry-run mode produces zero network egress | C20-INV-13 |
| DC12 | `CONTENT_FILTER` is terminal — never auto-retry with same prompt | CompletionProvider Scope §5.6 |
| DC13 | `CompletionCapability` enum is exhaustive — no capability may be added without separate human ratification | §11.1 ratification; CompletionProvider Scope §5 |

## 14. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-29 | WP2.2-B defined as the CompletionProvider bridge — parallel to WP2.2-A but independently exitable | This document |
| 2026-07-29 | Single adapter class — `CompletionProvider` per se; provider routing deferred to WP3 `ProviderRoute` | §3.2 |
| 2026-07-29 | Capability-specific system prompts embedded in adapter as a constant mapping — design-level guard, not runtime enforcement | §5.4 |
| 2026-07-29 | Provider-agnostic HTTP construction — vendor details in config, not in adapter code | §5.5 |
| 2026-07-29 | `CONTENT_FILTER` detection uses conservative body-string matching — only clear signals trigger the terminal class | §8.3 |
| 2026-07-29 | Cost `amount` is `0.0` at adapter layer — deferred to WP3 cost accounting from model pricing table | §5.7 |
| 2026-07-29 | Error helper functions replicated per adapter pattern — not extracted to shared module | §8.5 |
| 2026-07-29 | Adapter import not added to `completion/__init__.py` — keeps the protocol package dependency-free | §11.2 |
| 2026-07-29 | Chitu boundary enforced by both contract test (grep for banned identifiers) and code review | §6.3, §9.7 C-X3–C-X6 |
| 2026-07-29 | `CompletionCapability` enum is immutable — exactly 4 values; no addition, removal, or rename without separate human ratification | §4.5 |

## 15. WP2.2 Exit Preview

After WP2.2-A and WP2.2-B are both complete:

| Action | Status |
|--------|--------|
| Full canonical invocation (`pytest chitu-connector/tests/ -q`) green across all provider tests | Required |
| WP2 charter exit criteria E1–E13 verified | Required |
| C20-INV-12 and C20-INV-13 contract tests pass for all 3 capability ports | Required |
| WP2 exit reconciliation documented (`docs/PHASE3C20_WP2_EXIT_RECONCILIATION.md`) | Required |
| WP2.2-A and WP2.2-B exit criteria independently satisfied | Required |
| No CRM-side PHP, JS, metadata, or artifact changes introduced | Verified by `git diff --stat` |

---

*This is a documentation-only implementation plan. No code is modified by
this document. WP2.2-B implementation follows this plan as its authoritative
specification. The seven binding constraints from the §11.1 ratification
decision remain in force and bind all WP2.2-B implementation.*
