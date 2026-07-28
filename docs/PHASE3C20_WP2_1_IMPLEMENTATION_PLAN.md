# Phase3C20 WP2.1 — Capability Port Foundation Implementation Plan

## 1. Status

**Status:** Plan — pending implementation
**Date:** 2026-07-28
**Type:** Read-only implementation plan — no code changes
**Phase:** Phase3C20 WP2.1 — Capability Port Foundation

## 2. Governing Documents

| Document | Role |
|----------|------|
| `docs/PHASE3C20_WP2_CHARTER.md` | WP2 scope and exit criteria |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | `CompletionProvider` allowed/forbidden |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified Option C |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §4 | Provider abstraction rules |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | C20-INV-12, C20-INV-13 (WP2 activation) |

## 3. WP2.1 Objective

Establish the **foundation layer** for all C20 capability ports — the shared
types, Protocols, error taxonomy, and test infrastructure that every adapter
builds on. WP2.1 generalizes the existing `ProviderAdapter` pattern (currently
search-only) into a multi-capability port architecture.

WP2.1 does **not** implement new adapters. It creates the contract surface
that WP2.2 adapters implement against.

### 3.1 Relationship to WP2.2

```
WP2.1 (this plan)                    WP2.2 (subsequent)
─────────────────                    ──────────────────
Capability port Protocols            EnrichmentProvider adapter
Normalized request/response types    CompletionProvider adapter
Error taxonomy mapping               New adapter fixture tests
Capability declaration pattern       Adapter-specific compliance tests
Cost envelope type
Idempotency key contract
Search adapter retrofit + tests
Boundary contract tests
```

## 4. Files to Create

### 4.1 New Files

| # | File | Purpose |
|---|------|---------|
| F1 | `chitu_connector/chitu_connector/acquisition/providers/capabilities.py` | Capability enum, capability declaration dataclass |
| F2 | `chitu_connector/chitu_connector/acquisition/providers/cost.py` | Cost envelope dataclass |
| F3 | `chitu_connector/chitu_connector/acquisition/providers/taxonomy.py` | BridgeErrorClass taxonomy mapping for provider errors |
| F4 | `chitu_connector/chitu_connector/acquisition/providers/search/__init__.py` | Search package init; re-exports |
| F5 | `chitu_connector/chitu_connector/acquisition/providers/search/base.py` | `SearchProvider` Protocol, `SearchRequest`, `SearchResult` |
| F6 | `chitu_connector/chitu_connector/acquisition/providers/enrichment/__init__.py` | Enrichment package init; re-exports |
| F7 | `chitu_connector/chitu_connector/acquisition/providers/enrichment/base.py` | `EnrichmentProvider` Protocol, `EnrichmentRequest`, `EnrichmentResult` |
| F8 | `chitu_connector/chitu_connector/acquisition/providers/completion/__init__.py` | Completion package init; re-exports |
| F9 | `chitu_connector/chitu_connector/acquisition/providers/completion/base.py` | `CompletionProvider` Protocol, `CompletionRequest`, `CompletionResult` |

### 4.2 Files to Modify

| # | File | Change |
|---|------|--------|
| F10 | `chitu_connector/chitu_connector/acquisition/providers/base.py` | Generalize `ProviderAdapter` → keep as shared base; add transport+request/response types unchanged |
| F11 | `chitu_connector/chitu_connector/acquisition/providers/__init__.py` | Add new exports from capability packages |
| F12 | `chitu_connector/chitu_connector/acquisition/providers/apify_provider.py` | Move under `search/` or keep in place and verify `SearchProvider` compliance; add capability declaration |
| F13 | `chitu_connector/chitu_connector/acquisition/providers/serper_provider.py` | Same — verify `SearchProvider` compliance; add capability declaration |

### 4.3 New Test Files

| # | File | Purpose |
|---|------|---------|
| T1 | `chitu-connector/tests/test_phase3c20_wp2_1_search_provider.py` | `SearchProvider` contract tests (retrofit existing) |
| T2 | `chitu-connector/tests/test_phase3c20_wp2_1_enrichment_provider.py` | `EnrichmentProvider` contract tests (protocol only) |
| T3 | `chitu-connector/tests/test_phase3c20_wp2_1_completion_provider.py` | `CompletionProvider` contract tests (protocol + forbidden capabilities) |
| T4 | `chitu-connector/tests/test_phase3c20_wp2_1_taxonomy.py` | Error taxonomy mapping contract tests |
| T5 | `chitu-connector/tests/test_phase3c20_wp2_1_capabilities.py` | Capability declaration contract tests |

### 4.4 File Tree (Post-WP2.1)

```
chitu_connector/chitu_connector/acquisition/providers/
├── __init__.py                          # [MODIFIED] Re-exports from capability packages
├── base.py                              # [MODIFIED] Shared HttpTransport, HttpRequest, HttpResponse
├── config.py                            # [UNCHANGED] Existing provider configs
├── capabilities.py                      # [NEW] Capability enum + declaration
├── cost.py                              # [NEW] Cost envelope
├── taxonomy.py                          # [NEW] Error taxonomy mapping
├── search/
│   ├── __init__.py                      # [NEW]
│   └── base.py                          # [NEW] SearchProvider Protocol + types
├── enrichment/
│   ├── __init__.py                      # [NEW]
│   └── base.py                          # [NEW] EnrichmentProvider Protocol + types
├── completion/
│   ├── __init__.py                      # [NEW]
│   └── base.py                          # [NEW] CompletionProvider Protocol + types
├── apify_provider.py                    # [MODIFIED] Retrofit to SearchProvider; add capability declaration
└── serper_provider.py                   # [MODIFIED] Same — SearchProvider compliance
```

## 5. Protocol Boundaries

### 5.1 Shared Types (`providers/base.py` — unchanged contract)

These types are shared across all capability ports and are **not** modified:

```python
# base.py — existing, unchanged
@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str]       # field(repr=False)
    body: bytes | None               # field(repr=False)

@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    body: bytes | str | Mapping[str, Any]
    headers: Mapping[str, str]       # field(repr=False)

class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...
```

### 5.2 Capability Enum (`providers/capabilities.py` — new)

```python
# capabilities.py
from enum import Enum

class Capability(Enum):
    SEARCH = "search"
    ENRICHMENT = "enrichment"
    COMPLETION = "completion"

@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    capability: Capability
    supports_streaming: bool = False
    supports_json_mode: bool = False
    max_context_tokens: int | None = None
    supports_vision: bool = False
```

### 5.3 Cost Envelope (`providers/cost.py` — new)

```python
# cost.py
@dataclass(frozen=True, slots=True)
class CostEnvelope:
    tokens_in: int
    tokens_out: int
    model: str
    latency_ms: int
    provider_request_id: str
    currency: str = "USD"
    amount: float = 0.0
```

### 5.4 SearchProvider Protocol (`providers/search/base.py` — new)

```python
# search/base.py
from typing import Protocol
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class SearchRequest:
    job_id: str
    provider_name: str
    keyword: str
    country: str | None
    persona: str | None
    product: str | None
    result_limit: int
    idempotency_key: str              # NEW — ADR §4.2.5

@dataclass(frozen=True, slots=True)
class SearchResult:
    provider_name: str
    candidates: tuple[RawCandidate, ...]
    capability: Capability = Capability.SEARCH

class SearchProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...  # NEW — ADR §4.2.6

    def search(self, request: SearchRequest) -> SearchResult: ...
```

**Note:** `SearchRequest` and `SearchResult` replace the existing
`acquisition.models.SearchRequest` and `acquisition.models.ProviderResult`
for new callers. The existing models are **not removed** — they remain for
backward compatibility with the worker contract until WP3 refactors the
dispatch layer.

### 5.5 EnrichmentProvider Protocol (`providers/enrichment/base.py` — new)

```python
# enrichment/base.py
@dataclass(frozen=True, slots=True)
class EnrichmentRequest:
    request_id: str
    provider_name: str
    entity_type: str                  # e.g. "company", "person"
    lookup_key: str                   # domain, email, company name
    lookup_type: str                  # "domain", "email", "name"
    fields_requested: tuple[str, ...] # e.g. ("employees", "revenue", "industry")
    idempotency_key: str
    initiating_user: str

@dataclass(frozen=True, slots=True)
class EnrichmentResult:
    provider_name: str
    entity_type: str
    lookup_key: str
    fields: Mapping[str, Any]         # normalized enrichment fields
    cost: CostEnvelope | None         # None if provider doesn't charge per call
    capability: Capability = Capability.ENRICHMENT

class EnrichmentProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult: ...
```

### 5.6 CompletionProvider Protocol (`providers/completion/base.py` — new)

```python
# completion/base.py
class CompletionCapability(Enum):
    RESEARCH_EVIDENCE = "research_evidence"
    QUALIFICATION_INSIGHT = "qualification_insight"
    DRAFT_ASSISTANCE = "draft_assistance"
    REPLY_ASSISTANCE = "reply_assistance"

@dataclass(frozen=True, slots=True)
class CompletionRequest:
    capability: CompletionCapability
    purpose: str
    prompt: str
    context: Mapping[str, Any] | None = None
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    idempotency_key: str = field(repr=False)
    initiating_user: str
    prompt_template_version: str | None = None

@dataclass(frozen=True, slots=True)
class CompletionResult:
    completion_id: str
    capability: CompletionCapability
    content: str
    finish_reason: str                 # "STOP", "LENGTH", "CONTENT_FILTER"
    model: str
    cost: CostEnvelope
    prompt_template_version: str | None = None

class CompletionProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> CapabilityDeclaration: ...

    def complete(self, request: CompletionRequest) -> CompletionResult: ...
```

## 6. Error Taxonomy Mapping

### 6.1 Taxonomy Module (`providers/taxonomy.py` — new)

```python
# taxonomy.py
from enum import Enum

class ErrorClass(Enum):
    """ADR-C20 §4.3 normalized error taxonomy."""
    NETWORK = "NETWORK"           # retryable — backoff + jitter
    PROVIDER = "PROVIDER"         # retryable (5xx only) — backoff; fail over
    AUTH = "AUTH"                 # terminal — credential alert
    VALIDATION = "VALIDATION"     # terminal — caller defect
    UNKNOWN = "UNKNOWN"           # terminal — operator review
    RATE_LIMIT = "RATE_LIMIT"     # retryable — honour Retry-After; no attempt budget
    QUOTA = "QUOTA"               # terminal — halt capability
    CONTENT_FILTER = "CONTENT_FILTER"  # terminal — never auto-retry with same prompt

@dataclass(frozen=True, slots=True)
class ClassifiedError:
    error_class: ErrorClass
    provider_code: str
    safe_message: str
    retryable: bool
    retry_after: int | None = None

def classify_provider_error(
    status_code: int,
    provider_error_code: str | None = None,
    *,
    retry_after: int | None = None,
) -> ClassifiedError:
    """Map a provider status + optional error code to the C20 taxonomy."""
    ...
```

### 6.2 Adapter Compliance

Each adapter must translate its vendor-specific error into the `ErrorClass`
taxonomy. The `classify_provider_error()` helper provides a shared mapping;
adapters may override for vendor-specific classification.

**Rule (ADR §4.3):** Retry policy keys off `ErrorClass`, never off vendor error
codes.

## 7. Adapter Retrofit — Existing Search Providers

### 7.1 ApifyProvider Changes

| Change | Detail |
|--------|--------|
| Add `capabilities` property | `CapabilityDeclaration(capability=Capability.SEARCH, supports_json_mode=True)` |
| Add `idempotency_key` to request | `SearchRequest` gains the field; adapter passes it through (does not persist) |
| Return `SearchResult` | Replace `ProviderResult` → `SearchResult` with `capability` field |
| Add error taxonomy mapping | Internal `_http_error()` maps to `ClassifiedError` via `classify_provider_error()` |

### 7.2 SerperSearchProvider Changes

Same changes as ApifyProvider. Additionally:

| Change | Detail |
|--------|--------|
| Rename for consistency | `SerperSearchProvider` → `SerperProvider` (or keep; ship decision) |
| `build_request()` | Accepts `SearchRequest`; no signature change needed |

### 7.3 Backward Compatibility

The existing `acquisition.models.ProviderResult` and
`acquisition.models.SearchRequest` are **not removed** in WP2.1. The worker
contract uses these types. Dual compatibility is maintained:

- New capability port callers use `providers.search.base.SearchRequest` →
  `providers.search.base.SearchResult`
- Existing worker continues to use `acquisition.models.SearchRequest` →
  `acquisition.models.ProviderResult`
- Adapters accept the new types; a thin compat layer or type alias bridges
  existing callers until WP3 refactors the worker.

## 8. Test Strategy

### 8.1 FixtureTransport Pattern (Existing)

The existing `FixtureTransport` pattern is reused without change:

```python
class FixtureTransport:
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

### 8.2 Per-Protocol Test Matrix

#### SearchProvider Tests (`test_phase3c20_wp2_1_search_provider.py`)

| # | Test | Existing/New |
|---|------|-------------|
| S1 | Fixture response maps to candidates without worker/CRM writes | Existing — verify |
| S2 | Transport error (TimeoutError) → ProviderError with retryable=True | Existing — verify |
| S3 | Transport error (OSError) → ProviderError with retryable=True | Existing — verify |
| S4 | HTTP 401 → AUTH error class | New — taxonomy mapping |
| S5 | HTTP 429 → RATE_LIMIT error class with retry_after | New — taxonomy mapping |
| S6 | HTTP 5xx → PROVIDER error class, retryable | New — taxonomy mapping |
| S7 | Adapter declares `capabilities` property | New |
| S8 | `SearchResult` carries `capability=Capability.SEARCH` | New |
| S9 | Construction fails without explicit transport | New — C20-INV-12 |
| S10 | Dry-run: `FixtureTransport` → zero network egress | New — C20-INV-13 |

#### EnrichmentProvider Tests (`test_phase3c20_wp2_1_enrichment_provider.py`)

Protocol-only — no adapter implementation exists yet.

| # | Test |
|---|------|
| E1 | `EnrichmentRequest` fields are immutable (frozen dataclass) |
| E2 | `EnrichmentResult` carries optional `CostEnvelope` |
| E3 | Protocol defines `name`, `capabilities`, `enrich()` |
| E4 | No credential field on `EnrichmentRequest` or `EnrichmentResult` |
| E5 | No vendor-specific type in public interface |

#### CompletionProvider Tests (`test_phase3c20_wp2_1_completion_provider.py`)

| # | Test |
|---|------|
| C1 | `CompletionRequest` limit to 4 `CompletionCapability` values |
| C2 | `CompletionResult.finish_reason` limited to STOP/LENGTH/CONTENT_FILTER |
| C3 | `CostEnvelope` required on `CompletionResult` |
| C4 | Protocol defines `name`, `capabilities`, `complete()` |
| C5 | No credential field on `CompletionRequest` or `CompletionResult` |
| C6 | No vendor-specific type in public interface |
| C7 | Forbidden capability check: no SCORING capability enum value exists |
| C8 | Forbidden capability check: no EMAIL_GENERATION capability enum value exists |
| C9 | `idempotency_key` is `repr=False` on `CompletionRequest` |
| C10 | `initiating_user` is required on `CompletionRequest` |

#### Error Taxonomy Tests (`test_phase3c20_wp2_1_taxonomy.py`)

| # | Test |
|---|------|
| T1 | All 8 `ErrorClass` values map to correct retryable flag |
| T2 | `classify_provider_error(401)` → AUTH, retryable=False |
| T3 | `classify_provider_error(429, retry_after=30)` → RATE_LIMIT, retryable=True |
| T4 | `classify_provider_error(500)` → PROVIDER, retryable=True |
| T5 | `classify_provider_error(402)` → QUOTA, retryable=False |
| T6 | `classify_provider_error(400)` → VALIDATION, retryable=False |
| T7 | `RATE_LIMIT` and `QUOTA` are distinct classes |
| T8 | `CONTENT_FILTER` is terminal (retryable=False) |

#### Capability Declaration Tests (`test_phase3c20_wp2_1_capabilities.py`)

| # | Test |
|---|------|
| D1 | `CapabilityDeclaration` default flags are all False/None |
| D2 | `Capability` enum has exactly SEARCH, ENRICHMENT, COMPLETION |
| D3 | `CompletionCapability` enum has exactly 4 allowed values |
| D4 | No capability enum value implies scoring or email generation |

### 8.3 Cross-Cutting Contract Tests

| # | Test | Scope |
|---|------|-------|
| X1 | C20-INV-12 — no adapter constructs without explicit transport | All adapter files |
| X2 | C20-INV-13 — dry-run fixture mode produces zero network egress | All adapter fixture tests |
| X3 | No credential field in any `*Request` or `*Result` dataclass | All protocol types |
| X4 | No vendor-specific type in any public interface | All protocol types |
| X5 | All `ErrorClass` values are referenced by at least one adapter mapping | Cross-adapter |

## 9. Security Checks

### 9.1 Static Checks (Enforced by Contract Tests)

| # | Check | Test |
|---|-------|------|
| SC1 | No credential field in any request/response type | X3 |
| SC2 | No `repr=False` bypass on credential-adjacent fields | Code review |
| SC3 | No default transport — constructor requires explicit injection | X1 |
| SC4 | No vendor type in public interface | X4 |
| SC5 | No HTTP client construction without transport parameter | Code review |
| SC6 | No `os.environ` access outside config classes | Code review |
| SC7 | No `CompletionCapability` value implies scoring, qualification verdict, or email generation | C7, C8, D4 |

### 9.2 Design-Level Guards

| # | Guard | Rationale |
|---|-------|-----------|
| G1 | Protocols are Python `Protocol` (structural subtyping) — not ABC | No runtime registration; adapter conformity verified at test time |
| G2 | All dataclasses are `frozen=True` | Immutability prevents accidental mutation and ensures thread safety |
| G3 | `repr=False` on headers, body, idempotency_key | Prevents secret/token leakage in logs and tracebacks |
| G4 | `CostEnvelope` is mandatory on `CompletionResult`, optional on `EnrichmentResult` | Completion always costs; enrichment may be flat-rate |
| G5 | `CompletionCapability` is an enum, not a string | Exhaustive match coverage; no runtime string injection |
| G6 | `classify_provider_error()` is a pure function | No I/O, no state — testable in isolation |

### 9.3 Forbidden in WP2.1

| # | Forbidden | Reason |
|---|-----------|--------|
| F1 | Any `import requests`, `import httpx`, `import urllib3` in adapter code | Transport must be injected; no default HTTP client |
| F2 | Any `os.environ` access in adapter code | Config objects only; adapters receive already-validated config |
| F3 | Any `print()`, `logging.info()` of request/response bodies | Secrets in headers/body must not be logged |
| F4 | Any `try: ... except Exception: pass` around transport calls | All errors must be classified |
| F5 | Any `CompletionCapability` value beyond the 4 allowed | CompletionProvider scope §4 defines the exhaustive list |

## 10. Exit Criteria

WP2.1 exits when:

| # | Criterion | Evidence |
|---|-----------|----------|
| E1 | 9 new files created, 4 files modified per §4 | `git diff --stat` |
| E2 | `SearchProvider` Protocol defined; Apify and Serper retrofitted with capability declarations | S1–S10 passing |
| E3 | `EnrichmentProvider` Protocol defined | E1–E5 passing |
| E4 | `CompletionProvider` Protocol defined with 4 allowed capabilities; forbidden capabilities asserted absent | C1–C10 passing |
| E5 | Error taxonomy module maps all 8 `ErrorClass` values | T1–T8 passing |
| E6 | Capability declaration module enforces cardinality and defaults | D1–D4 passing |
| E7 | All 5 cross-cutting contract tests pass | X1–X5 passing |
| E8 | C20-INV-12 enforced — no default transport in any adapter | X1 |
| E9 | C20-INV-13 enforced — dry-run mode with zero network egress in all adapter tests | X2 |
| E10 | Canonical invocation (`pytest chitu-connector/tests/ -q`) green | CI-equivalent |
| E11 | No PHP, JS, metadata, or CRM-side file modified | `git diff --stat` limited to `chitu-connector/` |
| E12 | Existing `acquisition/models.py` types preserved (backward compat) | Existing worker tests unchanged |

## 11. WP2.2 Preview

WP2.2 implements the concrete adapters deferred from WP2.1:

- `chitu_connector/chitu_connector/acquisition/providers/enrichment/adapter.py`
- `chitu_connector/chitu_connector/acquisition/providers/completion/adapter.py`
- Corresponding fixture-test files
- Adapter-specific recorded fixtures

WP2.2 is unblocked once WP2.1 Protocols are stable and all contract tests pass.

## 12. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-28 | WP2 subdivided: WP2.1 (foundation — Protocols, types, retrofit) + WP2.2 (adapters — Enrichment, Completion) | This document |
| 2026-07-28 | Search adapters retrofitted in-place under `providers/` root, not moved to `providers/search/` | §4.2 — minimizes worker churn |
| 2026-07-28 | `CompletionCapability` is a separate enum from `Capability` | §5.6 — completion capabilities are a bounded subset; using a separate enum prevents enum pollution |
| 2026-07-28 | Existing `acquisition.models` types preserved for backward compat | §7.3 — worker refactor is WP3 |
| 2026-07-28 | `FixtureTransport` pattern reused without modification | §8.1 — proven pattern from C03 |

---

*No code changes. This plan defines the WP2.1 implementation scope and
boundaries. Implementation follows this plan as its authoritative spec.*
