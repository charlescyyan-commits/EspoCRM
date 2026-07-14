# Phase3C03.1 — Discovery Provider Selection & Contract Freeze

**Date:** 2026-07-13  
**Scope:** provider selection and contract design only  
**Verdict:** **CONDITIONAL PASS**  
**Recommended first provider:** **Apify Google Search Scraper**  
**Runtime/API/browser/code changes:** none  
**C03.2 skeleton changed:** no

## 1. Executive Summary

The first real provider is frozen as **Apify**, using the existing C03.2 Apify adapter boundary and the `apify/google-search-scraper` Actor as the initial implementation target. This is a selection decision, not an authorization to call the service or use a real token.

Apify is selected because the repository already has an Apify adapter skeleton, its Actor API has an explicit run/dataset model, and its result items can carry title, URL, description, query, position, and provider payload without forcing provider data into CRM metadata. It also leaves a credible path to Maps, directory, and custom Actors later.

The contract is frozen below. The current C03.2 skeleton is **Minor Alignment** rather than byte-for-byte compatible: it implements the existing minimal `RawCandidate` model and string error codes, while this phase freezes a richer logical contract. C03.2.2A must align the adapter mapping without changing the Worker or Runner boundary.

## 2. Current Architecture

The implemented acquisition path is:

```text
SearchJob -> SearchRequest -> SearchProvider.search()
          -> ProviderResult[RawCandidate]
          -> Normalize -> NormalizedCandidate
          -> Dedup -> ProspectPool persistence
```

Observed repository contracts:

- `acquisition/provider.py` exposes a provider-neutral `SearchProvider` Protocol with `name` and `search(request)`.
- `acquisition/models.py` currently defines `SearchRequest`, `RawCandidate`, `ProviderResult`, and `ProviderError`.
- `worker.py` constructs the request, calls one injected provider, normalizes/deduplicates candidates, and persists ProspectPool records.
- `fake_provider.py` is deterministic and remains the offline test provider.
- `runner.py` currently selects the fake provider only; this phase does not modify provider registration.
- The C03.2 Apify skeleton uses an injected transport, fixture responses, and no external calls by default.

CRM remains the persistence boundary. The provider must not create SearchJob, Lead, Opportunity, Email, or ProspectPool records directly.

## 3. Provider Candidates

### Apify

Apify provides a REST Actor run interface and dataset output. Official documentation describes synchronous `run-sync-get-dataset-items` and asynchronous run/status/dataset endpoints. The existing skeleton already models an injected HTTP transport and maps dataset items into the acquisition contract.

Strengths: existing implementation fit, flexible Actor schemas, dataset/raw-payload preservation, global scraping ecosystem, and future Google Maps or directory Actors.  
Weaknesses: Actor execution latency, Actor-specific schemas, platform/proxy cost variability, and a larger operational surface than a direct SERP endpoint.

### Serper.dev

Serper is a direct Google SERP REST API with simple JSON results and location controls. It is attractive for low-latency organic search and low integration complexity.

Strengths: straightforward request/response mapping, predictable Google-shaped results, low entry cost, and simple synchronous execution.  
Weaknesses: Google-only dependency, less control over enrichment and crawling, weaker fit for site extraction or Maps-style records, and provider-specific quotas/credit expiry.

### Brave Search API

Brave provides an independent web index with web, news, image, local, and other endpoints. Its web response exposes title, URL, description, and optional profile metadata.

Strengths: independent index, global reach, explicit country/language parameters, useful snippets, and a clear REST contract.  
Weaknesses: result ranking and B2B official-site coverage differ from Google-derived providers; company enrichment remains the adapter's responsibility; local/directory suitability must be proven with fixtures before selection.

## 4. Comparison Matrix

Scores are relative design judgments for this repository, not live benchmark claims. Cost and limits must be rechecked before production enablement.

| Criterion | Apify | Serper.dev | Brave Search API |
|---|---|---|---|
| Integration complexity | Medium: Actor run plus dataset mapping; existing skeleton reduces risk | Low: one REST request and JSON response | Low/medium: REST request, headers, query parameters |
| Maintenance | Medium: Actor schemas and platform behavior require monitoring | Medium: Google-shaped response but provider changes remain possible | Medium: independent index and response fields evolve separately |
| Cost model | Compute, proxy, storage, transfer, and Actor usage; variable per run | Prepaid query credits; public entry pack is $50 for 50,000 credits | Public Search plan shown as $5 per 1,000 requests with $5 monthly credits |
| Response stability | Medium: depends on selected Actor version/schema | High for the narrow organic SERP shape | Medium/high for documented web result shape |
| Documentation quality | High: REST, Actor, run, and dataset docs | Medium/high: concise API docs, narrower platform scope | High: API reference and examples |
| Global search | High, subject to Actor/proxy configuration | High for Google-supported locales | High for an independent global index |
| B2B official website discovery | High potential: query plus Actor enrichment/customization | High for Google organic discovery, lower enrichment | Medium: must validate ranking and domain coverage for target markets |
| Directory result ratio | High potential with dedicated Actor or query strategy | Medium/high through SERP queries | Medium until measured by fixtures/live approval |
| Field completeness | High potential; Actor item schema can include rich fields | Medium: title/link/snippet and SERP features | Medium: title/url/description/profile metadata |
| Extension ability | High: custom Actors, Maps, directory, extraction | Low/medium: endpoint-oriented | Medium: specialized endpoints and reranking features |
| Multi-provider adaptation difficulty | Low/medium after canonical mapping; existing adapter boundary helps | Low | Low |
| Main failure mode | Long run, Actor schema, quota/proxy cost | quota/auth/provider response changes | ranking coverage and quota/auth changes |
| Selection judgment | **Best first fit for this codebase** | Strong low-latency fallback candidate | Strong independent-index fallback candidate |

Official references: [Apify pricing](https://apify.com/pricing), [Apify Actor REST API](https://docs.apify.com/get-started/agent-onboarding), [Apify Google Search example](https://docs.apify.com/academy/api/run-actor-and-retrieve-data-via-api), [Serper](https://serper.dev/), and [Brave Search API](https://brave.com/search/api/).

## 5. Final Recommendation

Freeze **Apify** as the first provider and **Apify Google Search Scraper** as the first adapter target.

Reasons:

1. The repository already contains an Apify-specific C03.2 skeleton, fixtures, configuration boundary, transport seam, and error mapping.
2. The run/dataset model supports a bounded single-job adapter while retaining an explicit path for asynchronous Actors later.
3. Dataset items can preserve provider payload and optional descriptive fields without coupling Worker or CRM models to Apify.
4. The same provider family can later cover Maps, directories, and custom discovery without prematurely adding a multi-provider orchestration layer.
5. The choice is reversible because the Worker depends on `SearchProvider`, not on Apify classes.

This does not approve real credentials, network calls, or runtime integration in this phase.

## 6. Why Others Rejected for First Provider

**Serper.dev** is not rejected as a fallback. It is deferred because the current C03.2 implementation boundary is already Apify-shaped, while Serper would require a second adapter and a separate validation of result quality. Its direct synchronous API is a good later low-latency provider.

**Brave Search API** is not rejected on technical grounds. It is deferred because the target use case needs evidence for B2B official-site and directory coverage in the chosen markets, and its independent ranking cannot be assumed equivalent to Google-derived results. It remains a strong independent-index fallback.

No provider is considered suitable for direct CRM writes or unrestricted URL crawling.

## 7. SearchRequest Contract

The logical request is:

| Field | Type | Required | Provider-agnostic meaning |
|---|---|---:|---|
| `job_id` | string | yes in current worker | Correlation/audit identity |
| `keywords` | string or list of strings | yes | Discovery query terms |
| `country` | string or null | no | Target market; adapter maps to provider locale |
| `persona` | string or null | no | Target buyer/persona context |
| `product` | string or null | no | Product/category context |
| `limit` | positive integer | yes | Maximum candidates requested |
| `provider_options` | mapping | no | Explicit provider extension namespace; ignored by other providers |
| `language` | string or null | no | Search language |
| `search_mode` | string or null | no | Provider-neutral mode such as web/local/directory |

Provider-specific options must be namespaced and must not change the meaning of the common fields. The current code uses singular `keyword` and `result_limit`, plus `provider_name`; C03.2A must define the additive mapping to this logical contract. No code change is made here.

## 8. RawCandidate Contract

The canonical logical output is:

| Field | Type | Required | Rule |
|---|---|---:|---|
| `provider` | string | yes | Stable provider identifier |
| `provider_id` | string | yes | Stable candidate identity within provider result |
| `company_name` | string | yes | Best available organization label |
| `website` | URL or null | no | Provider-supplied official site when available |
| `domain` | string or null | no | Domain candidate; normalize later |
| `country` | string or null | no | Provider result or request context |
| `language` | string or null | no | Result language if supplied |
| `title` | string or null | no | Source result title |
| `description` | string or null | no | Source snippet/description |
| `source_url` | URL or null | no | Result URL used as evidence |
| `confidence` | number or null | no | Provider-supplied confidence only; never invented by adapter |
| `raw_payload` | JSON object | yes | Sanitized candidate payload, never credentials or headers |

Normalization derives canonical website/domain values when the provider supplies only a URL. Deduplication and CRM persistence consume normalized values, not provider-specific fields. The current `RawCandidate` stores `provider_candidate_id`, `company_name`, `domain`, `source_url`, `country`, and `raw_payload`; provider identity is currently result-level. This is recorded as a C03.2A alignment item, not silently treated as complete compatibility.

## 9. Provider Interface Contract

The provider boundary remains:

```python
class SearchProvider(Protocol):
    @property
    def name(self) -> str: ...

    def search(self, request: SearchRequest) -> ProviderResult: ...
```

The adapter owns authentication, request construction, transport, response parsing, provider-to-canonical mapping, and error classification. It must not call Worker, Runner, CRM, or persistence code. A successful call returns a provider result with zero or more `RawCandidate` objects; zero results are not an exception.

## 10. Error Contract

Canonical categories are frozen as follows:

| Category | Typical source | Retryable | Log | Stop job |
|---|---|---:|---:|---:|
| `CONFIG_ERROR` | Missing/invalid local configuration | no | yes, redacted | yes |
| `AUTH_ERROR` | 401/invalid credential | no | yes, redacted | yes |
| `RATE_LIMIT` | 429/quota | yes, bounded | yes, retry metadata only | after retry budget |
| `TIMEOUT` | transport deadline | yes, bounded | yes | after retry budget |
| `NETWORK_ERROR` | DNS/TLS/connection | yes, bounded | yes, safe summary | after retry budget |
| `SERVER_ERROR` | 5xx provider response | yes, bounded | yes, status only | after retry budget |
| `INVALID_RESPONSE` | malformed/unexpected JSON | no unless policy proves transient | yes, schema summary | yes |
| `EMPTY_RESULT` | valid zero-result response | no | yes, count only | no; complete with zero |
| `PARTIAL_RESULT` | valid response with item-level omissions | policy-defined | yes, counts | no if minimum contract remains valid |
| `UNKNOWN_ERROR` | unmapped failure | no by default | yes, redacted | yes |

The current string `ProviderError(code, safe_message, retryable)` remains the compatibility carrier. C03.2A must map provider-specific codes into these categories without exposing raw response bodies.

## 11. Configuration Contract

Configuration is external to CRM metadata and loaded from environment/secret storage:

| Setting | Required | Default/policy |
|---|---:|---|
| API key/token | yes for live use | never committed or logged |
| Base URL | no | official provider URL; test override only |
| Timeout | no | bounded, 30–90 seconds depending on Actor mode |
| TLS verify | no | enabled by default; no insecure production override |
| Retries | no | finite, category-based, zero for auth/config |
| Max results | no | bounded by request and cost budget |
| User Agent | no | stable non-secret service identifier |
| Cost limit | no | mandatory operational guard before live enablement |

No real key, URL override, token, cookie, or credential is recorded in this report.

## 12. Cost Contract

Every SearchJob must be evaluated against these limits before live execution:

- per-job request/result budget: one bounded provider operation and a fixed maximum result count;
- retry budget: finite retry count and backoff, with no retries for auth/config/invalid response;
- page/run budget: maximum Actor pages or dataset items;
- timeout budget: one total wall-clock deadline, not an unbounded Actor wait;
- daily and monthly provider budget: hard stop before provider calls when the configured allowance is exhausted.

Rationale: Apify charges by platform usage such as compute, proxies, storage, and transfer, so a query-only estimate is insufficient. Serper uses prepaid query credits; Brave publishes request-based pricing. The implementation must measure actual usage and reserve retry headroom rather than hard-code a historic price. Current public pages show Apify usage-based pricing, Serper prepaid credit packs, and Brave Search request pricing; revalidate before live rollout.

## 13. Security Boundary

- API keys, bearer tokens, cookies, and authorization headers stay in secret configuration and never enter logs, `raw_payload`, CRM, fixtures, or reports.
- Raw payloads are sanitized before storage in the connector boundary; no request headers or credential-bearing URLs are retained.
- Logs contain provider name, category, HTTP status, correlation ID, counts, and safe summaries only.
- TLS verification is enabled; redirects and base URLs are constrained to the configured provider.
- The adapter does not fetch arbitrary `source_url` values.
- No real provider call, credential, CRM record, or personal customer data is part of C03.1.

## 14. Testing Strategy

Testing is separated into fixture/mock and explicitly approved live validation:

1. Contract fixtures validate success, empty, duplicate, official brand site, directory result, missing domain, and international country/language.
2. Transport fixtures validate 401, 403, 429, 500, timeout, network error, malformed JSON, and partial items.
3. Parser tests prove mapping into every canonical RawCandidate field without network access.
4. Security tests assert that keys, authorization headers, raw response bodies, and PII-like fields do not appear in safe errors or logs.
5. Live tests, if later approved, use a disposable credential and a separately identified runtime phase; they are not part of C03.1.

No tests were run or added in this documentation-only phase, as required.

## 15. Future Provider Strategy

The sequence is intentionally: **single provider -> provider registry -> multiple providers -> ranking -> failover**.

Only one provider is frozen now to keep attribution, cost accounting, result quality, and failure semantics measurable. A registry can later expose Apify, Serper, and Brave behind the same interface. Ranking and failover must follow measured quality and budget policy; they must not be inferred from provider names or silently duplicate paid searches.

## 16. Compatibility Review

**Result: Minor Alignment.** No architectural blocker exists, but C03.2A must align details before calling the contract frozen in code.

| Area | Compatibility | Required future alignment |
|---|---|---|
| Provider Protocol | Compatible | Keep the existing injected `SearchProvider` boundary |
| Worker/Runner separation | Compatible | Do not add provider logic to Worker or Runner core |
| SearchRequest | Minor | Map current `keyword`/`result_limit` to logical `keywords`/`limit`; add optional provider options/language/mode only when approved |
| RawCandidate | Minor | Preserve current fields while exposing/mapping logical website/title/description/language/confidence semantics |
| ProviderResult | Compatible | Keep immutable provider result and empty tuple for no results |
| Error handling | Minor | Map current string codes and retryable flag to the canonical taxonomy |
| Apify skeleton | Compatible with alignment | Keep injected transport, fixture-only tests, and no runtime calls |
| CRM/persistence | Compatible | No CRM schema, ACL, Worker, Runner, or persistence changes in this phase |

## 17. Risks

- Actor schema drift can break mappings; pin/document Actor input/output expectations and keep fixtures versioned.
- Apify run latency can exceed a CLI deadline; enforce sync limits and bounded async policy later.
- Provider results may be directories rather than official sites; normalization and quality rules must retain source evidence and classify result type.
- Country/language coverage can vary; collect fixture sets by target market before live approval.
- Retry storms can multiply cost; enforce per-job, daily, and monthly budgets.
- Raw provider payloads can contain unexpected personal data; sanitize and minimize before persistence.

## 18. Phase3C03 Roadmap

1. **C03.2A:** align the Apify skeleton with this contract and add offline fixture coverage only.
2. **C03.2B:** perform adapter-level review and contract tests; no live credentials by default.
3. **Later runtime phase:** explicitly approve one disposable credential, bounded live calls, and runtime evidence.
4. **Future:** add Serper or Brave only after the first provider's quality/cost/error telemetry is available.

## 19. Ready for Phase3C03.2A

**Ready: YES, conditionally.** C03.2A may proceed with Apify as the selected provider, provided it performs the alignment items in section 16 and does not modify Worker, Runner, CRM, metadata, runtime, or credentials as part of that alignment.

### Final Decision

- **Recommended provider:** Apify Google Search Scraper
- **Compatibility:** Minor Alignment
- **Ready for C03.2A:** YES, conditionally
- **Code/tests/runtime/Docker/browser/commit:** none performed
- **Phase result:** **CONDITIONAL PASS**
