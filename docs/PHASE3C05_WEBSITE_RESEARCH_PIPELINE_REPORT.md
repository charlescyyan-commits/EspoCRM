# Phase3C05 — Website Research Pipeline Foundation

## 1. Status

**PASS** — the internal, deterministic Website Research foundation is implemented and verified with offline fixtures only.

## 2. Scope

Implemented the bounded internal path:

```text
Master Prospect
  -> Eligibility
  -> URL Planning
  -> Injected HTTP Transport Boundary
  -> Page Classification
  -> HTML Sanitization
  -> Website Research Pipeline Result
```

The pipeline consumes the frozen `MasterProspect` model from Phase3C04. It does not recreate domain normalization, company normalization, matching, or deduplication.

This phase does not implement AI research, LLM extraction, ICP/score/tier logic, email generation, CRM sync, browser automation, JavaScript rendering, persistence, queues, workers, or public APIs.

## 3. Architecture

`WebsiteResearchPipeline.research(master)` creates an internal plan request, validates the public target, creates a stable plan of at most ten same-root-domain URLs, invokes only an injected `WebsiteTransport`, validates the response, classifies and sanitizes HTML, then returns an immutable result and one trace record per planned page.

The existing vendored `contracts/website_research.py` was inspected but not changed or reused as the pipeline result. It is an existing downstream evidence/sync contract with candidate and extraction fields; C05 uses its own explicitly internal pipeline contracts to avoid changing that frozen contract or prematurely emitting evidence.

## 4. Files Changed

| File | Change | Responsibility |
|---|---|---|
| `chitu-connector/chitu_connector/acquisition/website_research.py` | New | Internal models, eligibility, URL planning, transport protocol, fetch policy, sanitizer, classifier, pipeline, status aggregation, and trace creation. |
| `chitu-connector/tests/test_phase3c05_website_research_pipeline.py` | New | Offline Fake Transport and deterministic C05 coverage. |
| `docs/PHASE3C05_WEBSITE_RESEARCH_PIPELINE_REPORT.md` | New | Scope, controls, validation evidence, and limitations. |

No existing C04, Provider, Runner, Worker, CRM, or extension file was modified.

## 5. Data Contract

- `WebsiteResearchPlanRequest`: Master Prospect identity and canonical fields copied into an immutable, serializable internal request.
- `UrlPlanItem`: requested URL, planned page type, and planning rule.
- `WebsiteHttpRequest` / `WebsiteHttpResponse`: replaceable transport boundary. Request headers are `repr=False` and are never included in result or trace output.
- `WebsiteResearchPageResult`: requested/final URLs, page type, HTTP/content metadata, bounded raw HTML, sanitized text, title, meta description, links, fetch status, typed error, redirect chain, classification reason, and sanitization actions.
- `WebsiteResearchPipelineTrace`: planning rule, selected URL, resulting page type, fetch outcome, classification reason, sanitization actions, and error classification.
- `WebsiteResearchPipelineResult`: Master identity, root URL, pages, `NOT_ELIGIBLE` / `PLANNED` / `PARTIAL` / `COMPLETED` / `FAILED` state model, counts, selected page types, timestamps, and trace.
- `WebsiteResearchError`: safe deterministic error code and retryability. No raw exception, response body, API key, or sensitive header is included.

All result models provide deterministic `to_dict()` serialization for fixture comparison.

## 6. Security Controls

- **Target safety / SSRF:** only `http` and `https` are permitted. The checker blocks `localhost`, loopback, unspecified, private, link-local, and non-global IP addresses; `.local`, `.test`, `.invalid`, `.localhost`, and reserved example domains; `file:`, `ftp:`, `gopher:`, `mailto:`, `tel:`, `javascript:`, malformed URLs, credentials in URLs, and obvious document/media file URLs.
- **URL plan:** fixed paths, a hard total limit of ten, stable ordering, URL de-duplication, query/fragment removal, and same-root-domain enforcement.
- **Redirects:** maximum of four; every redirect/final URL must remain on the same normalized root domain (including only the `www` variant). Private and cross-domain redirects fail with `REDIRECT_ERROR`.
- **Fetch limits:** GET-only transport request, explicit timeout and maximum response bytes, HTML/XHTML-only content policy, safe status/error mapping, and bounded raw/text/link output.
- **Sensitive data:** response/request headers are never retained in page results or traces. Tests prove `Authorization` and API-key fixture values are absent from serialized output.

## 7. Deterministic Rules

- **Eligibility:** valid canonical website is preferred; a valid normalized domain yields `https://<domain>/`; unsafe/non-HTTP targets are `NOT_ELIGIBLE` before transport access.
- **Planning:** `HOME (1)`, `ABOUT (2)`, `CONTACT (2)`, `PRODUCTS (3)`, `BRANDS (2)` in that order, total `<= 10`.
- **Classification priority:** explicit final/requested URL path > title/heading keywords > planned type > `OTHER`.
- **Sanitization:** removes/ignores `script`, `style`, `noscript`, `svg`, `canvas`, `template`, `iframe`, and hidden content; decodes entities, normalizes whitespace, and extracts title, meta description, visible text, headings, and bounded basic links.
- **Status aggregation:** no eligible target = `NOT_ELIGIBLE`; no successful planned page = `FAILED`; all planned pages successful = `COMPLETED`; otherwise = `PARTIAL`.
- **Retryability:** timeout, DNS/connection/TLS transport failures, 408, 429, and 500–504 are retryable. Unsafe/invalid targets, redirect violation, 4xx access/not-found/client failures, unsupported content, oversized responses, malformed HTML, and empty content are not.

## 8. Test Results

| Suite | Command / scope | Result |
|---|---|---|
| Phase3C05 specialist | `test_phase3c05_website_research_pipeline.py` | **13/13 PASS** |
| Phase3C04 regression | `test_phase3c04_master_prospect_dedup.py` | **13/13 PASS** |
| Connector full discovery | `chitu-connector/tests/test_*.py` | **152/152 PASS** |
| Unified offline regression | `scripts/testing/run-tests.ps1 all` | **131/131 PASS** — Extension 40/40, Connector 58/58, Worker 31/31, Static 2/2 |
| Python compile | New module and C05 test | **PASS** |

The unified entrypoint predates C04/C05 and therefore does not discover their specialist files; their explicit suites and the full connector discovery were run separately.

Fixture coverage includes legal http/https/domain-only targets; empty, local, private-IP, IPv6 loopback, file, and JavaScript rejection; stable planning; 200/204/301/302/307/308/400/401/403/404/408/429/500/502/503/504 outcomes; timeout/DNS/TLS/connection errors; response limits; HTML content policy; empty and malformed HTML; sanitization; all page types; URL/title conflict; full/partial/failed/not-eligible states; trace completeness; input immutability; and safe/cross-domain/private/over-limit redirect handling.

## 9. Boundary Confirmation

- No real website, Apify, Serper, DeepSeek, OpenAI, LLM, Playwright, Chrome, Selenium, EspoCRM, Railway, SMTP, Instantly, Docker, or browser call was made.
- Only fixture HTML, Fake Transport responses, and deterministic clocks were used.
- No Provider adapter, Master Prospect matching semantics, Search Strategy, SearchJob contract, Provider Runner, Worker Runtime, Runtime Queue, Scheduler, CRM contract, extension, public API, Docker, or Railway file was modified.
- No database write, CRM write, queue/job creation, scoring, email, AI, or evidence extraction was performed.
- No prohibited Git operation (`add`, `commit`, `reset`, `checkout`, `clean`, `stash`, `rebase`, or `merge`) was executed.

## 10. Known Limitations

- No JavaScript rendering or browser fallback.
- No login, CAPTCHA, authentication bypass, robots-policy execution, or access-restriction bypass.
- No contact/email/social/profile/product/brand/ICP/evidence extraction; C05 only prepares sanitized page material for a later approved phase.
- No AI research, scoring, email generation, CRM write, persistence, or runtime integration.
- The transport is intentionally abstract; a real network transport requires a separately approved security and runtime phase.
