# EspoCRM Sync Adapter Boundary V1

**Phase:** 3A-2.2-A  
**Status:** implemented offline only

## Scope

This phase implements an Engine-side Python adapter at `integration/espocrm_sync/`. It builds the unchanged `ESPOCRM_SYNC_CONTRACT_V1.json` payload, evaluates the contract gates, performs deterministic duplicate handling, writes an in-memory audit trail, and sends only to an in-memory `MockEspoCRMClient`.

## Files Changed

- `integration/__init__.py`
- `integration/espocrm_sync/{__init__,models,contract,mapper,gate,idempotency,client,audit}.py`
- `tests/test_espocrm_sync_adapter.py`
- This phase's four reports in `docs/espocrm-extension/`

## Contract Dependency

The adapter depends on the existing V1 contract, rules, and entity mapping without modifying them. It accepts existing `Candidate`, `WebsiteResearchResult`, optional `BusinessQualificationResult`, and Canonical Scoring V4 output as inputs.

`SearchSource` values are normalized without changing Engine models: Google/industry discovery maps to contract channel `WEB_SEARCH`; `CUSTOM_IMPORT` maps to `CONTROLLED_MANUAL_INPUT`.

## Non-Goals

- No real EspoCRM HTTP request, credentials, OAuth/API key, PHP, extension metadata, or UI work.
- No real Lead, Account, Opportunity, `ResearchEvidence`, database, queue, email, SMTP, DeepSeek, Apify, or browser action.
- No modification to V1 contract fields, Engine scoring rules, research contracts, ICP rules, legacy scoring, `app/`, or `revenue_system/`.

## Evidence Boundary

The V1 contract requires a compact evidence item for each reference: ID, claim type, claim, public source URL, bounded excerpt, confidence, capture time, and schema version. The adapter transfers exactly those fields, bounded by the unchanged V1 maximum, and excludes raw HTML, crawler logs, cookies, browser data, prompts, raw pages, and provider payloads. Its CRM-facing reference helper exposes only `evidence_id` and `claim_type`.

## Failure Behavior

The gate runs before the mock client and rejects invalid inputs without downgrade or client invocation. Rejections include `NOT_OUTREACH_READY`, `INVALID_SCORE_VERSION`, `MISSING_EVIDENCE`, `OFFICIAL_BRAND_EXCLUDED`, `FAILED_TECHNICAL`, and `REJECTED_BUSINESS`. Every adapter attempt creates in-memory `READY` plus final `SYNCED`, `DUPLICATE`, or `REJECTED` audit entries.
