# Phase3C07.1 Evidence Extraction Report

**Repository:** `D:\EspoCRM-Production`  
**Status:** **PASS**  
**Scope:** Deterministic extraction only; no persistence or workflow integration.

## Delivered Boundary

`WebsiteResearchEvidenceExtractor` accepts the serialized output of
`WebsiteResearchPipelineResult.to_dict()` and returns an ordered
`list[EvidenceItem]`.

The adapter is isolated in:

- `chitu-connector/chitu_connector/acquisition/evidence_extraction.py`
- `chitu-connector/tests/test_phase3c07_evidence_extraction.py`

It imports only the vendored `EvidenceItem` contract. It does not import or
call EspoCRM, persistence, providers, browser tooling, AI, scoring, email, or
workflow components.

## Deterministic Extraction Rules

1. Only C05 pages with `fetch_status == "SUCCESS"` are eligible.
2. The source URL is the successful page's `final_url`, with `requested_url`
   used only when it is a valid HTTP(S) fallback. A page without either is
   skipped.
3. The adapter emits factual page observations in stable page order:
   `page_title`, `meta_description`, then `visible_text`.
4. Claims are direct bounded observations: title/meta text or the first
   sentence of visible text. No classification, enrichment, inference, or AI
   generation is performed.
5. Evidence text is whitespace-normalized and deterministically capped at
   1,000 characters; claims are capped at 500 characters. This preserves a
   source-backed excerpt within the existing compact evidence contract.
6. Confidence is fixed by evidence type: title `0.95`, meta description
   `0.90`, visible text `0.85`.
7. Evidence IDs are stable SHA-256-derived values over claim type, source URL,
   evidence text, and extractor version. Duplicate source/text pairs are
   emitted once, retaining first-seen page and observation order.
8. Capture time comes from C05 `fetched_at`, falling back to C05 pipeline time
   and then the fixed UTC epoch. The adapter never reads the system clock.

## Contract and Boundary Confirmation

- C05 `WebsiteResearchPipelineResult` remains unchanged and still does not
  emit evidence itself.
- The vendored `EvidenceItem` dataclass remains unchanged.
- C06 `ResearchEvidence` schema and all EspoCRM APIs remain unchanged.
- No ResearchEvidence, Lead, ProspectPool, database, queue, worker, score,
  email, or CRM-sync write is created or invoked.
- The extractor is intentionally not wired to a future C07 persistence
  adapter.

## Test Coverage

| Scenario | Result |
| --- | --- |
| Normal page extraction | PASS |
| Multiple pages in input order | PASS |
| Empty content and failed pages | PASS |
| Missing source URL | PASS |
| Malformed input | PASS |
| Deterministic duplicate handling | PASS |
| Existing compact evidence-size limit | PASS |

## Validation

| Check | Result |
| --- | --- |
| New extractor unit suite | **PASS - 7 tests** |
| Python compile | **PASS** |
| C05 pipeline + C06 evidence-boundary regression | **PASS - 41 tests** |
| Core Regression Gate | **PASS - Extension 57, Connector 86, Worker 31, Static 2; 5/5 required suites** |

No commit was created.
