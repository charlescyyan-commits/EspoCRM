# Phase3C20 WP2.2-A — EnrichmentProvider Adapter Implementation Plan

## 1. Status

**Status:** Plan — pending implementation
**Date:** 2026-07-29
**Type:** Read-only implementation plan — no code changes
**Phase:** Phase3C20 WP2.2-A — EnrichmentProvider Adapter

## 2. Governing Documents

| Document | Role |
|----------|------|
| `docs/PHASE3C20_WP2_2_ADAPTER_EXPANSION_DESIGN.md` | WP2.2 design audit — EnrichmentProvider scope (§4), test matrix (§10.2), exit criteria (§11) |
| `docs/PHASE3C20_WP2_1_IMPLEMENTATION_PLAN.md` | WP2.1 foundation — `EnrichmentProvider` Protocol, `EnrichmentRequest`, `EnrichmentResult`, error taxonomy, `FixtureTransport` pattern |
| `docs/PHASE3C20_WP2_CHARTER.md` | WP2 charter — enrichment definition (§6.2), architecture boundaries (§7), test strategy (§11) |
| `docs/PHASE3C20_ADR_11_1_RATIFICATION_DECISION.md` | §11.1 ratified YES — Option C; 7 binding constraints |
| `chitu_connector/chitu_connector/acquisition/providers/serper_provider.py` | Reference adapter pattern — transport injection, error classification, capability declaration |
| `chitu_connector/chitu_connector/acquisition/providers/enrichment/base.py` | `EnrichmentProvider` Protocol + types — the contract the adapter implements |
| `chitu_connector/chitu_connector/acquisition/providers/taxonomy.py` | Error taxonomy — `classify_provider_error()` mapping, 8 `ErrorClass` values |
| `chitu_connector/chitu_connector/acquisition/providers/cost.py` | `CostEnvelope` dataclass |

## 3. Objective

Implement the concrete `EnrichmentProvider` adapter deferred from WP2.1 and
specified in the WP2.2 design audit (§4).

The adapter provides a single, transport-injected connector-side capability
that enables CRM operators to enrich prospect records with company profiles,
contact details, and firmographics from external data providers (Apollo,
Hunter). It implements the `EnrichmentProvider` Protocol established in WP2.1.

### 3.1 What WP2.2-A Delivers

| # | Deliverable | Description |
|---|-------------|-------------|
| D1 | `EnrichmentProvider` adapter | Concrete adapter in `acquisition/providers/enrichment/adapter.py` implementing the Protocol |
| D2 | Apollo adapter variant | Apollo-specific HTTP request construction, response normalization, error classification |
| D3 | Hunter adapter variant | Hunter-specific HTTP request construction, response normalization, error classification |
| D4 | Enrichment fixture tests | Contract tests with recorded fixtures, dry-run verification, error taxonomy coverage |
| D5 | Recorded fixtures | Pre-recorded Apollo + Hunter request/response pairs for deterministic replay |

### 3.2 What WP2.2-A Does NOT Deliver

- CRM-side PHP code that invokes the adapter (WP3)
- `AIJob`, `AIRequestLog`, `PromptTemplate`, or `AIQualificationInsight` entities (WP3)
- `ProviderCredential` custody UI (separate WP)
- CRM record creation from enrichment data (operator action after enrichment)
- Any scoring, qualification, or research logic (forbidden)
- Any autonomous enrichment trigger (forbidden — Charter §6)
- The `CompletionProvider` adapter (WP2.2-B)

## 4. Adapter Boundary

### 4.1 Architecture Position

```
EspoCRM (PHP)
  ProspectPool record → operator triggers enrichment
         │  calls via connector contract [WP3]
         ▼
chitu_connector (Python)  ←── sole egress boundary
  acquisition/providers/
    enrichment/
      base.py              ← EnrichmentProvider Protocol [WP2.1]
      adapter.py           ← ApolloEnrichmentProvider + HunterEnrichmentProvider [WP2.2-A NEW]
         │  explicit transport injection (no default)
         ▼
  External enrichment provider (Apollo / Hunter)
```

The adapter lives entirely on the connector side of the egress boundary.
EspoCRM never opens an HTTP connection to Apollo, Hunter, or any enrichment
provider (C20-INV-03).

### 4.2 Protocol Contract

The adapter implements the `EnrichmentProvider` Protocol from WP2.1
(`providers/enrichment/base.py`):

```python
class EnrichmentProvider(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def capabilities(self) -> CapabilityDeclaration: ...
    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult: ...
```

### 4.3 Request/Response Flow

```
EnrichmentRequest (frozen)
  │  request_id, provider_name, entity_type, lookup_key, lookup_type,
  │  fields_requested, idempotency_key (repr=False), initiating_user
  ▼
Adapter.enrich()
  │  1. Validate entity_type ∈ {"company", "person"}
  │  2. Validate lookup_type ∈ {"domain", "email", "name"}
  │  3. Build vendor-specific HTTP request
  │  4. Send via injected transport
  │  5. Classify errors via classify_provider_error() on failure
  │  6. Normalize vendor response → Mapping[str, Any] fields
  │  7. Optionally attach CostEnvelope
  │  8. Return EnrichmentResult
  ▼
EnrichmentResult (frozen)
  │  provider_name, entity_type, lookup_key, fields: Mapping[str, Any],
  │  cost: CostEnvelope | None, capability=ENRICHMENT
```

### 4.4 Adapter Design — One File, Two Classes

The reference pattern from `serper_provider.py` uses a single class per
provider. WP2.2-A follows the same pattern:

```
acquisition/providers/enrichment/
├── __init__.py          [UNCHANGED — WP2.1]
├── base.py              [UNCHANGED — WP2.1 Protocol]
└── adapter.py           [NEW — WP2.2-A]
    ├── ApolloEnrichmentProvider   — implements EnrichmentProvider
    └── HunterEnrichmentProvider   — implements EnrichmentProvider
```

Each class:
- Accepts `config` (provider-specific) + `transport: HttpTransport` in `__init__`
- Exposes `name` property (string constant)
- Exposes `capabilities` property (`CapabilityDeclaration`)
- Implements `enrich(request: EnrichmentRequest) -> EnrichmentResult`
- Uses internal helpers for HTTP request construction, response parsing, error classification
- Never accesses `os.environ` — config is injected
- Never constructs a default HTTP client — transport is injected

### 4.5 Enrichment Boundaries (Non-Negotiable)

| # | Rule | Enforcement |
|---|------|-------------|
| B1 | No CRM-side HTTP to Apollo, Hunter, or any enrichment provider | C20-INV-03 — connector is sole egress |
| B2 | No enrichment fields treated as qualification input | Enrichment is data hydration, not scoring |
| B3 | No autonomous enrichment trigger | Every invocation is operator-initiated via `initiating_user` |
| B4 | No credential field in `EnrichmentRequest` or `EnrichmentResult` | Contract test — dataclass field verification |
| B5 | No vendor-specific type in public interface | `fields: Mapping[str, Any]` — no Apollo/Hunter SDK type |
| B6 | Adapter requires explicit transport injection | Constructor parameter; no default — C20-INV-12 |
| B7 | No `os.environ` access in adapter code | Config objects only; verified by code review |
| B8 | No `import requests`, `import httpx`, `import urllib3` | Transport is injected; no default HTTP client |
| B9 | No `print()` or `logging.info()` of request/response bodies | Secrets in headers must not be logged |
| B10 | No bare `except Exception: pass` around transport calls | All errors classified via `classify_provider_error()` |

## 5. Files to Create

### 5.1 Adapter Implementation

| # | File | Purpose |
|---|------|---------|
| F1 | `chitu_connector/chitu_connector/acquisition/providers/enrichment/adapter.py` | `ApolloEnrichmentProvider` + `HunterEnrichmentProvider` concrete implementations |

### 5.2 New Test Files

| # | File | Purpose |
|---|------|---------|
| F2 | `chitu-connector/tests/test_phase3c20_wp2_2_a_enrichment_adapter.py` | Apollo + Hunter contract tests (fixture replay, error taxonomy, transport injection, dry-run) |

### 5.3 New Fixture Files

| # | File | Purpose |
|---|------|---------|
| F3 | `chitu-connector/tests/fixtures/wp2_2/apollo_company_domain_lookup.json` | Recorded Apollo company-by-domain request/response |
| F4 | `chitu-connector/tests/fixtures/wp2_2/apollo_person_email_lookup.json` | Recorded Apollo person-by-email request/response |
| F5 | `chitu-connector/tests/fixtures/wp2_2/apollo_error_401.json` | Recorded Apollo 401 error response |
| F6 | `chitu-connector/tests/fixtures/wp2_2/apollo_error_429.json` | Recorded Apollo 429 error response |
| F7 | `chitu-connector/tests/fixtures/wp2_2/hunter_domain_lookup.json` | Recorded Hunter domain search request/response |
| F8 | `chitu-connector/tests/fixtures/wp2_2/hunter_email_verification.json` | Recorded Hunter email verification request/response |
| F9 | `chitu-connector/tests/fixtures/wp2_2/hunter_error_401.json` | Recorded Hunter 401 error response |
| F10 | `chitu-connector/tests/fixtures/wp2_2/hunter_error_429.json` | Recorded Hunter 429 error response |

### 5.4 Files NOT Modified

WP2.2-A must **not** modify any file outside:

- `chitu_connector/chitu_connector/acquisition/providers/enrichment/adapter.py` (new)
- `chitu-connector/tests/test_phase3c20_wp2_2_a_enrichment_adapter.py` (new)
- `chitu-connector/tests/fixtures/wp2_2/` (new directory)

Specifically, no modification to:
- Any `crm-extension/files/` file (PHP, JS, metadata, template)
- `chitu_connector/chitu_connector/acquisition/providers/enrichment/__init__.py` (WP2.1 — re-exports; adapter import is not required in `__init__` to keep the package dependency-free)
- `chitu_connector/chitu_connector/acquisition/providers/enrichment/base.py` (WP2.1 — Protocol)
- `chitu_connector/chitu_connector/acquisition/providers/taxonomy.py` (WP2.1 — reuse as-is)
- `chitu_connector/chitu_connector/acquisition/providers/cost.py` (WP2.1 — reuse as-is)
- `chitu_connector/chitu_connector/acquisition/providers/capabilities.py` (WP2.1 — reuse as-is)
- Any existing search provider, completion provider, or models file

### 5.5 Post-WP2.2-A Provider Tree

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
│   └── adapter.py                       [NEW — WP2.2-A]
├── completion/
│   ├── __init__.py                      [UNCHANGED]
│   └── base.py                          [UNCHANGED]
├── apify_provider.py                    [UNCHANGED]
└── serper_provider.py                   [UNCHANGED]
```

## 6. Apollo Integration Boundary

### 6.1 What Apollo Provides

Apollo is a B2B data intelligence platform. The enrichment adapter consumes
Apollo's REST API for:

| Endpoint | Lookup Type | Entity Type |
|----------|-------------|-------------|
| Organization enrich (by domain) | `domain` | `company` |
| People enrich (by email) | `email` | `person` |
| Organization search (by name) | `name` | `company` |

### 6.2 Apollo-Specific Implementation

```python
class ApolloEnrichmentProvider:
    name = "APOLLO"

    def __init__(self, config: ApolloConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            Capability.ENRICHMENT,
            supports_json_mode=True,
        )

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        _validate(request)                          # entity_type ∈ {company, person}, lookup_type ∈ {domain, email, name}
        http_request = self._build(request)          # vendor-specific URL + headers + body
        response = self._send(http_request)          # transport.send() with error classification
        payload = self._parse(response)              # JSON decode + shape validation
        fields = self._normalize(payload, request)   # Apollo-specific → Mapping[str, Any]
        return EnrichmentResult(
            provider_name=self.name,
            entity_type=request.entity_type,
            lookup_key=request.lookup_key,
            fields=fields,
            cost=self._cost_estimate(payload),       # Apollo does not charge per enrichment call → None
        )
```

### 6.3 Apollo Config

```python
@dataclass(frozen=True, slots=True)
class ApolloConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://api.apollo.io/api/v1"
```

The config is constructed by the connector's config infrastructure. The
adapter never reads `os.environ` or constructs its own config. Credentials
(`api_key`) are `repr=False`.

### 6.4 Apollo HTTP Request Construction

| Aspect | Detail |
|--------|--------|
| Authentication | `X-Api-Key` header from `config.api_key` |
| Content-Type | `application/json` |
| Idempotency | `Idempotency-Key` header from `request.idempotency_key` |
| Entity type routing | `company` → `POST /organizations/enrich`; `person` → `POST /people/match` |
| Lookup type routing | `domain` → `{"domain": lookup_key}`; `email` → `{"email": lookup_key}`; `name` → `{"q_organization_name": lookup_key}` |
| Response parsing | JSON decode → `Mapping[str, Any]` shape validation |

### 6.5 Apollo Response Normalization

Apollo returns structured JSON with nested organization/person objects.
The adapter normalizes these into a flat `Mapping[str, Any]`:

| Apollo Field Path | Normalized Key | Notes |
|-------------------|---------------|-------|
| `organization.name` | `company_name` | Always present |
| `organization.website_url` | `domain` | May be absent |
| `organization.estimated_num_employees` | `employees` | May be absent |
| `organization.industry` | `industry` | May be absent |
| `organization.annual_revenue` | `revenue` | May be absent |
| `organization.linkedin_url` | `linkedin_url` | May be absent |
| `organization.city` / `organization.state` / `organization.country` | `city`, `state`, `country` | May be absent |
| `person.name` | `person_name` | Person lookups only |
| `person.title` | `title` | Person lookups only |
| `person.email` | `email` | Person lookups only |

The adapter returns **only the fields requested** in
`request.fields_requested`, filtered from the normalized map. Unrequested
fields are omitted from the result.

### 6.6 Apollo Error Handling

Apollo returns standard HTTP status codes. The adapter delegates to
`classify_provider_error()`:

| HTTP Status | Apollo Error | ErrorClass | Retryable |
|-------------|-------------|------------|-----------|
| 401 | Invalid API key | `AUTH` | No |
| 403 | Forbidden / plan limit | `AUTH` | No |
| 429 | Rate limit | `RATE_LIMIT` | Yes |
| 5xx | Apollo service error | `PROVIDER` | Yes (5xx) |
| 400 | Invalid request | `VALIDATION` | No |
| 402 | Quota exhausted | `QUOTA` | No |

The adapter does **not** parse Apollo error response bodies for detailed
codes. It classifies on HTTP status alone, following the `serper_provider.py`
pattern and the `classify_provider_error()` contract.

## 7. Hunter Integration Boundary

### 7.1 What Hunter Provides

Hunter is an email finding and verification platform. The enrichment adapter
consumes Hunter's REST API for:

| Endpoint | Lookup Type | Entity Type |
|----------|-------------|-------------|
| Domain search | `domain` | `company` |
| Email finder | `domain` + person name | `person` |
| Email verification | `email` | `person` |

### 7.2 Hunter-Specific Implementation

```python
class HunterEnrichmentProvider:
    name = "HUNTER"

    def __init__(self, config: HunterConfig, *, transport: HttpTransport) -> None:
        self._config = config
        self._transport = transport

    @property
    def capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            Capability.ENRICHMENT,
            supports_json_mode=True,
        )

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        _validate(request)
        http_request = self._build(request)
        response = self._send(http_request)
        payload = self._parse(response)
        fields = self._normalize(payload, request)
        return EnrichmentResult(
            provider_name=self.name,
            entity_type=request.entity_type,
            lookup_key=request.lookup_key,
            fields=fields,
            cost=None,                            # Hunter does not charge per lookup
        )
```

### 7.3 Hunter Config

```python
@dataclass(frozen=True, slots=True)
class HunterConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://api.hunter.io/v2"
```

### 7.4 Hunter HTTP Request Construction

| Aspect | Detail |
|--------|--------|
| Authentication | `api_key` query parameter |
| Content-Type | `application/json` |
| Idempotency | `Idempotency-Key` header from `request.idempotency_key` |
| Entity type routing | `company` → `GET /domain-search?domain={lookup_key}`; `person` (email finder) → `GET /email-finder?domain={domain}&full_name={name}`; `person` (email verify) → `GET /email-verifier?email={email}` |
| Lookup type routing | `domain` → domain search or email-finder; `email` → email verifier; `name` → requires domain context from `request` |
| Response parsing | JSON decode → `data` key extraction → `Mapping[str, Any]` shape validation |

### 7.5 Hunter Response Normalization

| Hunter Field Path | Normalized Key | Notes |
|------------------|---------------|-------|
| `data.domain` | `domain` | Always present |
| `data.organization` | `company_name` | May be absent |
| `data.emails[].value` | `emails` | Domain search — list of email patterns found |
| `data.email` | `email` | Email finder/verifier — single match |
| `data.result` | `email_status` | Email verifier — `deliverable`, `undeliverable`, `risky` |
| `data.score` | `confidence_score` | Email verifier — 0–100; **informational only, not a CRM score** |

### 7.6 Hunter Error Handling

| HTTP Status | Hunter Error | ErrorClass | Retryable |
|-------------|-------------|------------|-----------|
| 401 | Invalid API key | `AUTH` | No |
| 429 | Rate limit | `RATE_LIMIT` | Yes |
| 5xx | Hunter service error | `PROVIDER` | Yes (5xx) |
| 400 | Invalid request | `VALIDATION` | No |
| 402 | Quota exhausted | `QUOTA` | No |

Same pattern as Apollo: delegate to `classify_provider_error()`. No parsing
of Hunter error payload bodies.

### 7.7 Hunter: What It Is NOT

Hunter's `data.score` (0–100 email confidence) is **not** a `canonical_score`
or `AIScore`. It is an email deliverability signal returned by a third-party
API. It is stored as an enrichment field (`confidence_score`) alongside other
enrichment data. It does **not** feed into Chitu's qualification pipeline,
CRM scoring, or any `canonical_score` computation (C20-INV-14).

## 8. Credential Handling

### 8.1 Credential Boundary

```
EspoCRM (PHP)                          chitu_connector (Python)
─────────────────                      ────────────────────────
ProviderCredential entity              Connector environment
  credentialReference: "apollo-prod"     APOLLO_API_KEY=sk-...
  (write-only, no secret stored)         HUNTER_API_KEY=abc123...

EnrichmentRequest                       Adapter receives ApolloConfig / HunterConfig
  (no credential field exists)            config.api_key  ← resolved from env by config infra
```

### 8.2 Per-Provider Config Pattern

Each enrichment provider has a frozen config dataclass with `repr=False` on
the credential field:

```python
@dataclass(frozen=True, slots=True)
class ApolloConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://api.apollo.io/api/v1"

@dataclass(frozen=True, slots=True)
class HunterConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://api.hunter.io/v2"
```

Config objects are constructed by the connector's configuration
infrastructure — not by the adapter. The adapter receives an already-resolved
config instance. It never reads `os.environ`, never constructs a credential,
and never logs a credential.

### 8.3 Design Enforcement

| # | Rule | How Enforced |
|---|------|-------------|
| C1 | `EnrichmentRequest` has zero credential fields | WP2.1 contract test E4 (already passing) |
| C2 | `EnrichmentResult` has zero credential fields | WP2.1 contract test E4 (already passing) |
| C3 | Config dataclass uses `repr=False` on `api_key` | Code review |
| C4 | Adapter never accesses `os.environ` | Code review + grep audit |
| C5 | Adapter never logs request headers or response bodies | Code review — no `print()` or `logging.info()` of transport data |
| C6 | Adapter never constructs a default HTTP client | Constructor requires explicit `transport: HttpTransport` — C20-INV-12 |

## 9. Error Taxonomy Mapping

### 9.1 Shared Taxonomy (Reused from WP2.1)

The adapter uses the existing `classify_provider_error()` function from
`providers/taxonomy.py`. No new taxonomy code is written in WP2.2-A.

### 9.2 Adapter-Level Error Handling Pattern

Each adapter follows the `serper_provider.py` pattern exactly:

```python
def _send(self, request: HttpRequest) -> HttpResponse:
    try:
        response = self._transport.send(request)
    except TimeoutError as error:
        raise _provider_error("APOLLO_TIMEOUT", "Apollo request timed out", 0) from error
    except OSError as error:
        raise _provider_error("APOLLO_TRANSPORT_ERROR", "Apollo transport failed", 0) from error
    if response.status_code >= 400:
        raise self._http_error(response)
    return response

@staticmethod
def _http_error(response: HttpResponse) -> ProviderError:
    status_code = response.status_code
    if status_code == 429:
        retry_after = _parse_retry_after(response.headers)
        return _rate_limit_error("APOLLO_RATE_LIMITED", "Apollo rate limit reached", retry_after)
    if status_code >= 500:
        return _provider_error("APOLLO_UPSTREAM_ERROR", "Apollo service failed", status_code)
    return _provider_error(f"APOLLO_HTTP_{status_code}", "Apollo rejected the request", status_code)
```

### 9.3 Error Classification Mapping

Both providers delegate to `classify_provider_error()`. The full taxonomy is
exercised:

| ErrorClass | Trigger | Retryable | Adapter Behaviour |
|------------|---------|-----------|-------------------|
| `NETWORK` | `TimeoutError`, `OSError` in transport call | Yes | Raise `ProviderError(retryable=True)` |
| `PROVIDER` | HTTP 5xx | Yes | Raise `ProviderError(retryable=True)` |
| `AUTH` | HTTP 401, 403 | No | Raise `ProviderError(retryable=False)` — credential alert |
| `RATE_LIMIT` | HTTP 429 | Yes | Raise `ProviderRateLimitError` with `retry_after` |
| `QUOTA` | HTTP 402 | No | Raise `ProviderError(retryable=False)` |
| `VALIDATION` | HTTP 400, 404, 422 | No | Raise `ProviderError(retryable=False)` — caller defect |
| `CONTENT_FILTER` | N/A | N/A | Not applicable to enrichment (no content filtering) |

### 9.4 Shared Helpers (Replicated Per Adapter)

The following helper functions are replicated in the adapter module, following
the `serper_provider.py` pattern:

```python
def _provider_error(code: str, safe_message: str, status_code: int) -> ProviderError:
    classified = classify_provider_error(status_code, code)
    error = ProviderError(code, safe_message, retryable=classified.retryable)
    error.error_class = classified.error_class
    return error

def _rate_limit_error(code: str, safe_message: str, retry_after: int | None) -> ProviderRateLimitError:
    classified = classify_provider_error(429, code, retry_after=retry_after)
    error = ProviderRateLimitError(code, safe_message, retryable=classified.retryable, retry_after=classified.retry_after)
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

These helpers are **not** extracted into a shared module. WP2.2-A keeps each
adapter self-contained, consistent with the existing `serper_provider.py`
pattern. A shared error-helper module may be extracted in a future refactor
(WP3 or later) if duplication across 4+ adapters warrants it.

### 9.5 Request Validation

The shared `_validate()` function performs pre-flight validation before any
HTTP call:

```python
VALID_ENTITY_TYPES = frozenset({"company", "person"})
VALID_LOOKUP_TYPES = frozenset({"domain", "email", "name"})

def _validate(request: EnrichmentRequest) -> None:
    if request.entity_type not in VALID_ENTITY_TYPES:
        raise _provider_error(
            "ENRICH_INVALID_ENTITY_TYPE",
            f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}",
            400,
        )
    if request.lookup_type not in VALID_LOOKUP_TYPES:
        raise _provider_error(
            "ENRICH_INVALID_LOOKUP_TYPE",
            f"lookup_type must be one of {sorted(VALID_LOOKUP_TYPES)}",
            400,
        )
    if not request.lookup_key.strip():
        raise _provider_error(
            "ENRICH_EMPTY_LOOKUP_KEY",
            "lookup_key must not be empty",
            400,
        )
```

Validation failures are classified as `ErrorClass.VALIDATION` (terminal,
retryable=False). No HTTP call is made for a validation failure.

## 10. Fixture Testing Strategy

### 10.1 Recorded-Fixture Pattern

All adapter tests follow the recorded-fixture pattern from WP2.1 §8.1:

```
1. Record:    Real Apollo/Hunter call → capture request + response → store as JSON fixture
2. Replay:    FakeHttpTransport serves fixture → adapter processes → assert EnrichmentResult
3. Dry-run:   Complete trace with zero network egress (C20-INV-13)
4. Error:     FakeHttpTransport serves error fixture → adapter classifies → assert ErrorClass
```

### 10.2 FakeHttpTransport (Reused)

```python
class FakeHttpTransport:
    """Fixture transport from WP2.1 §8.1 — reused without modification."""

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

### 10.3 Fixture Format

Each fixture is a JSON file containing a `(HttpRequest, HttpResponse)` pair:

```json
{
  "request": {
    "method": "POST",
    "url": "https://api.apollo.io/api/v1/organizations/enrich",
    "headers": {"Accept": "application/json", "Content-Type": "application/json"},
    "body": "{\"domain\":\"example.com\"}"
  },
  "response": {
    "status_code": 200,
    "headers": {"Content-Type": "application/json"},
    "body": {
      "organization": {
        "name": "Example Corp",
        "website_url": "example.com",
        "estimated_num_employees": 150,
        "industry": "Technology",
        "annual_revenue": 50000000,
        "linkedin_url": "https://linkedin.com/company/example-corp",
        "city": "San Francisco",
        "state": "CA",
        "country": "US"
      }
    }
  }
}
```

### 10.4 Apollo Test Cases

| # | Test | Fixture | Assertion |
|---|------|---------|-----------|
| A1 | Company by domain — happy path | `apollo_company_domain_lookup.json` | `EnrichmentResult` with `entity_type=company`, `fields` contains `company_name`, `domain`, `employees`, `industry`, `revenue` |
| A2 | Person by email — happy path | `apollo_person_email_lookup.json` | `EnrichmentResult` with `entity_type=person`, `fields` contains `person_name`, `title`, `email` |
| A3 | Company by name — happy path | `apollo_company_name_lookup.json` | `EnrichmentResult` with `entity_type=company`, `fields` contains `company_name` |
| A4 | Fields filtered per `fields_requested` | `apollo_company_domain_lookup.json` | Only requested fields appear in `result.fields` |
| A5 | Transport error (TimeoutError) → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| A6 | Transport error (OSError) → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| A7 | HTTP 401 → `AUTH` | `apollo_error_401.json` | `ProviderError` with `error_class=AUTH`, `retryable=False` |
| A8 | HTTP 429 → `RATE_LIMIT` with `retry_after` | `apollo_error_429.json` | `ProviderRateLimitError` with `error_class=RATE_LIMIT`, `retryable=True`, `retry_after` populated |
| A9 | HTTP 500 → `PROVIDER` | Error fixture | `ProviderError` with `error_class=PROVIDER`, `retryable=True` |
| A10 | HTTP 402 → `QUOTA` | Error fixture | `ProviderError` with `error_class=QUOTA`, `retryable=False` |
| A11 | HTTP 400 → `VALIDATION` | Error fixture | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| A12 | Construction fails without explicit transport | N/A | `TypeError` — C20-INV-12 |
| A13 | Dry-run — zero network egress | All fixtures | `FakeHttpTransport.requests` recorded; no socket opened — C20-INV-13 |
| A14 | Capability declaration populated | N/A | `capabilities.capability == Capability.ENRICHMENT` |
| A15 | Cost envelope is `None` for Apollo | `apollo_company_domain_lookup.json` | `result.cost is None` |
| A16 | No credential field in `EnrichmentRequest` or `EnrichmentResult` | N/A | Dataclass field scan |
| A17 | No vendor-specific type in public interface | N/A | `result.fields` is `Mapping[str, Any]`; no Apollo SDK type |
| A18 | Idempotency — same key produces same result | Any fixture | Two invocations with same `idempotency_key` return identical `EnrichmentResult` |
| A19 | `initiating_user` is carried through | Any fixture | `request.initiating_user` is set; adapter does not drop it |

### 10.5 Hunter Test Cases

| # | Test | Fixture | Assertion |
|---|------|---------|-----------|
| H1 | Domain search — happy path | `hunter_domain_lookup.json` | `EnrichmentResult` with `entity_type=company`, `fields` contains `domain`, `company_name`, `emails` |
| H2 | Email verification — happy path | `hunter_email_verification.json` | `EnrichmentResult` with `entity_type=person`, `fields` contains `email`, `email_status`, `confidence_score` |
| H3 | Transport error (TimeoutError) → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| H4 | Transport error (OSError) → `NETWORK` | Error fixture | `ProviderError` with `error_class=NETWORK`, `retryable=True` |
| H5 | HTTP 401 → `AUTH` | `hunter_error_401.json` | `ProviderError` with `error_class=AUTH`, `retryable=False` |
| H6 | HTTP 429 → `RATE_LIMIT` with `retry_after` | `hunter_error_429.json` | `ProviderRateLimitError` with `error_class=RATE_LIMIT`, `retryable=True` |
| H7 | HTTP 500 → `PROVIDER` | Error fixture | `ProviderError` with `error_class=PROVIDER`, `retryable=True` |
| H8 | HTTP 402 → `QUOTA` | Error fixture | `ProviderError` with `error_class=QUOTA`, `retryable=False` |
| H9 | HTTP 400 → `VALIDATION` | Error fixture | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| H10 | Construction fails without explicit transport | N/A | `TypeError` — C20-INV-12 |
| H11 | Dry-run — zero network egress | All fixtures | C20-INV-13 |
| H12 | Capability declaration populated | N/A | `capabilities.capability == Capability.ENRICHMENT` |
| H13 | Cost envelope is `None` for Hunter | `hunter_domain_lookup.json` | `result.cost is None` |
| H14 | No credential field in types | N/A | Dataclass field scan |
| H15 | No vendor-specific type in public interface | N/A | `result.fields` is `Mapping[str, Any]` |
| H16 | Idempotency — same key produces same result | Any fixture | Identical `EnrichmentResult` |
| H17 | `initiating_user` is carried through | Any fixture | Adapter does not drop the field |
| H18 | Hunter `confidence_score` is NOT `canonical_score` | `hunter_email_verification.json` | Field is `confidence_score`; no `canonical_score` key exists (C20-INV-14) |

### 10.6 Shared Validation Test Cases

| # | Test | Assertion |
|---|------|-----------|
| V1 | Invalid `entity_type` → `VALIDATION` | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| V2 | Invalid `lookup_type` → `VALIDATION` | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| V3 | Empty `lookup_key` → `VALIDATION` | `ProviderError` with `error_class=VALIDATION`, `retryable=False` |
| V4 | Valid request passes validation — no error | `EnrichmentResult` returned |

### 10.7 Test File Structure

```python
# test_phase3c20_wp2_2_a_enrichment_adapter.py

class ApolloEnrichmentProviderTests:
    """A1–A19 — Apollo-specific fixture tests."""

class HunterEnrichmentProviderTests:
    """H1–H18 — Hunter-specific fixture tests."""

class EnrichmentValidationTests:
    """V1–V4 — shared validation tests (run against both adapters)."""

class EnrichmentBoundaryTests:
    """Cross-cutting: C20-INV-12, C20-INV-13, credential absence, vendor-type absence."""
```

### 10.8 WP2.1 Test Continuity

The existing WP2.1 enrichment protocol tests
(`test_phase3c20_wp2_1_enrichment_provider.py`) must remain green. WP2.2-A
does not modify any WP2.1 test file. The WP2.1 tests verify the Protocol
structure; WP2.2-A tests verify the concrete adapter implementations.

## 11. Exit Criteria

WP2.2-A exits when **all** of the following are true:

| # | Criterion | Evidence |
|---|-----------|----------|
| E1 | `adapter.py` created with `ApolloEnrichmentProvider` + `HunterEnrichmentProvider` | File exists; both classes implement `EnrichmentProvider` Protocol |
| E2 | Apollo config + Hunter config dataclasses defined with `repr=False` on credentials | Code review |
| E3 | All Apollo fixture tests passing (A1–A19) | `pytest test_phase3c20_wp2_2_a_enrichment_adapter.py -q -k Apollo` green |
| E4 | All Hunter fixture tests passing (H1–H18) | `pytest test_phase3c20_wp2_2_a_enrichment_adapter.py -q -k Hunter` green |
| E5 | All shared validation tests passing (V1–V4) | `pytest test_phase3c20_wp2_2_a_enrichment_adapter.py -q -k Validation` green |
| E6 | Boundary contract tests passing (C20-INV-12, C20-INV-13) | Transport injection + dry-run assertions |
| E7 | Existing WP2.1 enrichment protocol tests remain green | `pytest test_phase3c20_wp2_1_enrichment_provider.py -q` green |
| E8 | Canonical invocation green | `pytest chitu-connector/tests/ -q` green (all provider tests) |
| E9 | No credential field in any WP2.2-A type | Contract test + code review |
| E10 | No vendor-specific type in public interface | Contract test + code review |
| E11 | No `os.environ` access in adapter code | Code review + grep audit |
| E12 | No default HTTP client — `import requests`, `import httpx`, `import urllib3` absent | Code review + grep audit |
| E13 | No `print()` or `logging.info()` of request/response bodies | Code review |
| E14 | No bare `except Exception: pass` around transport calls | Code review |
| E15 | No PHP, JS, metadata, or CRM-side file modified | `git diff --stat` limited to `chitu_connector/` and `chitu-connector/tests/` |
| E16 | No modification to `enrichment/__init__.py` or `enrichment/base.py` | `git diff` confirms zero changes to WP2.1 files |
| E17 | Hunter `confidence_score` is documented as informational — not a CRM score | §7.7; test H18 |
| E18 | All enrichment WP2 charter exit criteria satisfied | Aligned with WP2 Charter §12 E2 |

## 12. Design Constraints (Non-Negotiable)

| # | Constraint | Origin |
|---|------------|--------|
| DC1 | No direct API calls from CRM — all enrichment I/O through the connector | C20-INV-03 |
| DC2 | No secrets in EspoCRM — credential references only | §11.1 Constraint 6 |
| DC3 | No AI runtime in CRM — enrichment is data lookup, not AI | ADR §2 D2 |
| DC4 | No autonomous actions — every invocation operator-initiated | §11.1 Constraint 7; Charter §6 |
| DC5 | No PHP, JS, or metadata changes | WP2 Charter §9 |
| DC6 | No scoring — enrichment data is informational; no `canonical_score` computation | C20-INV-14 |
| DC7 | No qualification verdicts from enrichment data | C20-INV-21 |
| DC8 | No research — enrichment is structured data lookup; not web crawling | AGENTS.md A2 |
| DC9 | No modification to Chitu-owned code | AGENTS.md A1–A4 |
| DC10 | Transport injection mandatory — no default transport | C20-INV-12 |
| DC11 | Dry-run mode produces zero network egress | C20-INV-13 |
| DC12 | No `os.environ` access in adapter code | WP2.1 §9.3 F2 |

## 13. Decision Log

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-29 | WP2.2 split into WP2.2-A (Enrichment) and WP2.2-B (Completion) — parallelizable, independent exit | This document |
| 2026-07-29 | One adapter file (`adapter.py`) containing two provider classes — `ApolloEnrichmentProvider` + `HunterEnrichmentProvider` | §4.4 |
| 2026-07-29 | Adapter follows `serper_provider.py` pattern exactly — transport injection, error classification, capability declaration | §4.4 |
| 2026-07-29 | Config dataclasses defined in adapter module, not in central config — per `SerperConfig` precedent | §6.3, §7.3 |
| 2026-07-29 | Error helper functions (`_provider_error`, `_rate_limit_error`, `_parse_retry_after`) replicated per adapter, not shared — per existing pattern | §9.4 |
| 2026-07-29 | Validation function (`_validate`) is shared module-level function in `adapter.py` | §9.5 |
| 2026-07-29 | Apollo and Hunter both report `cost=None` — neither charges per enrichment call at this tier | §10.4 A15, §10.5 H13 |
| 2026-07-29 | Hunter `data.score` normalized as `confidence_score` — informational only; not `canonical_score` | §7.7 |
| 2026-07-29 | Adapter import not added to `enrichment/__init__.py` — keeps the protocol package dependency-free | §5.4 |
| 2026-07-29 | Fixture files live under `tests/fixtures/wp2_2/` — consistent with WP2.2 design audit §10.5 | §5.3 |

## 14. WP2.2-B Preview

WP2.2-B implements the `CompletionProvider` adapter (`completion/adapter.py`)
and its fixture tests. It is unblocked once WP2.1 Protocols are stable and
WP2.2-A has established the adapter implementation pattern. WP2.2-A and
WP2.2-B are independent and may proceed in parallel.

---

*This is a documentation-only implementation plan. No code is modified by
this document. WP2.2-A implementation follows this plan as its authoritative
specification.*
