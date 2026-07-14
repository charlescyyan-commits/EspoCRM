# Phase3C04 — Master Prospect Deduplication & Merge

## Implementation

Added the internal-only pipeline at `chitu_connector.acquisition.master_prospect`:

```text
Provider Result -> RawCandidate -> RawProspect -> ProspectNormalizer
-> ProspectMatcher -> MasterProspectMerger -> MasterProspect
```

`RawProspect` wraps the frozen `RawCandidate` contract rather than changing it. The pipeline is pure in-memory Python: it has no persistence, HTTP transport, provider invocation, CRM client, worker, runner, browser, or AI dependency. Its output is the deterministic `MasterProspectMergeResult`; later Website Research, AI Research, Scoring, and CRM Sync wiring is deliberately outside this phase.

## Normalization Rules

- **Root domain:** trims, lowercases, removes repeated `www.`, removes URL path/query/fragment, and accepts HTTP(S) values. `Example.COM`, `www.example.com`, `https://example.com`, and `https://www.example.com/` become `example.com`.
- **Canonical website:** is the normalized HTTP(S) website identity, stored as `https://<root-domain>`. If a provider leaves `domain` empty but supplies a source URL, that URL is used as the website identity only.
- **Company name:** Unicode NFKC normalization, `casefold`, and removal of spacing/punctuation plus terminal common legal suffixes. `3DJake`, `3D JAKE`, and `3D-Jake` become `3djake`; `Example Ltd`, `Example Inc.`, `Example LLC`, `Example GmbH`, and `Example B.V.` become `example`. The original provider name remains untouched in `RawCandidate`.
- **Country:** Unicode/whitespace normalization; two-letter country codes are uppercased. Other values use a whitespace-normalized, casefolded deterministic key.
- **City:** Unicode/whitespace normalization and casefolding.

No normalization writes to a `RawCandidate`, its `raw_payload`, or its provider metadata.

## Matching Rules

All matching is exact and deterministic, in this priority order:

1. `ROOT_DOMAIN` — equal normalized root domains (confidence `1.00`).
2. `CANONICAL_WEBSITE` — equal normalized source-website identities when a direct domain was absent (confidence `0.99`).
3. `COMPANY_NAME` — equal canonical company names when neither raw record carries country or city values (confidence `0.95`).
4. `COMPANY_COUNTRY` — equal canonical company names and equal canonical countries (confidence `0.94`).
5. `COMPANY_CITY` — equal canonical company names and equal canonical cities (confidence `0.93`).

The geographic condition on name-only matching prevents same-name companies with conflicting geographic data from being merged merely by name. There is no AI, LLM, embedding, fuzzy, inferred, or partial-string matching.

## Merge Rules

- All exact-match edges are clustered in-memory so a connected set becomes exactly one `MasterProspect`.
- `master_id` is deterministic (`mp_` plus a SHA-256-derived key); all master ordering is deterministic.
- Every original `RawProspect` remains in `matched_raw_records`; duplicate records are not overwritten or discarded.
- `provider_list` is a sorted unique list and `source_count` is its count.
- Per-record provider metadata and unaltered `raw_payload` values are retained in `provider_metadata`.
- `discovery_history` retains provider name, provider candidate ID, source URL, optional discovery ID, and internal record ID.

## Traceability

Every raw record has a `MergeTrace`. A first record receives `NEW_MASTER`; subsequently merged records record the matched raw record ID, exact matching rule, fixed deterministic confidence, human-readable reason, and merge timestamp. The same per-record trace is also available in the result-level `merge_traces` collection.

## Tests

New offline tests: `chitu-connector/tests/test_phase3c04_master_prospect_dedup.py`.

Coverage includes:

- Domain variants: `example.com`, `www.example.com`, `https://example.com`, `Example.com`.
- Company-name normalization including `Ltd`, `Inc`, `LLC`, `GmbH`, and `B.V.`, plus country normalization.
- Root-domain, canonical-website, company-name, company-country, and company-city rules.
- Duplicate merge with complete raw-record retention.
- Input-order-independent Master Prospect identity and trace output.
- APIFY plus future provider (`SERPER` / `BRAVE`) merging without provider-specific code.
- Merge metadata, discovery history, trace rule, confidence, reason, and timestamp.
- Unrelated same-name records with conflicting country values remaining separate.

Validation completed offline on 2026-07-13:

- Focused Phase3C04 suite: **13/13 PASS**.
- Full connector discovery (`chitu-connector/tests/test_*.py`): **139/139 PASS**, including existing Phase3C02/C03 tests and Phase3C04.
- Unified offline regression entrypoint (`scripts/testing/run-tests.ps1 all`): **131/131 PASS** — Extension 40/40, Connector 58/58, Worker 31/31, Static 2/2.
- Python compile check for the new module and test: **PASS**.

## Boundary Verification

- No EspoCRM extension, CRM Lead, Opportunity, SearchJob, API route, API contract, Docker, Railway, worker, runner, scheduler, queue, browser automation, AI research, scoring engine, or SearchStrategy file was changed.
- No provider adapter file was changed; the frozen `ProviderResult -> RawCandidate` boundary remains intact.
- No real provider, DeepSeek, browser, Playwright, Chrome, Docker Browser, or CRM was invoked.
- The pipeline has no public HTTP/API surface and no persistence action.

## Known Limitations

- The result is intentionally internal and in-memory. Durable storage and wiring Master Prospect into downstream research, scoring, or CRM sync need separately approved phases.
- Country names are whitespace/case canonicalized; this phase does not ship a country-alias database (for example, it does not infer that a full country name equals an ISO code).
- Exact rules are deliberately conservative: records with unequal domains/websites and conflicting geographic values do not merge just because their names look similar.
