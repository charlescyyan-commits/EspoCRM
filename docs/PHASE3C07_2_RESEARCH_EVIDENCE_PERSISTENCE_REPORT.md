# Phase3C07.2 — ResearchEvidence Persistence Adapter Report

Status: **PASS**  
Commit: **not created**

## Scope Delivered

Added a connector-side, deterministic persistence adapter from vendored
`EvidenceItem` values to the frozen `ResearchEvidence` entity. The adapter
requires an existing `leadId`; it does not create, update, or otherwise mutate
Lead records.

| Surface | Delivered path |
|---|---|
| Persistence interface and adapter | `chitu-connector/chitu_connector/espocrm_sync/research_evidence_persistence.py` |
| Local EspoCRM client operations | `chitu-connector/chitu_connector/espocrm_sync/real_client.py` |
| Offline unit tests | `chitu-connector/tests/test_phase3c07_research_evidence_persistence.py` |

## Field Mapping

| EvidenceItem / adapter value | ResearchEvidence field |
|---|---|
| deterministic display label | `name` |
| existing receiving Lead id | `leadId` |
| `evidence_id` | `peEvidenceId` |
| `claim` | `peClaim` |
| `claim_type` | `peClaimType` |
| `evidence_type` | `peEvidenceType` |
| `source_url` | `peSourceUrl` |
| `evidence_text` | `peEvidenceText` |
| compact factual `claim` | `peContentSummary` |
| `confidence` | `peConfidence` |
| `captured_at` converted to EspoCRM datetime | `peCapturedAt` |
| `extractor_version` | `peSchemaVersion` |
| canonical EvidenceItem snapshot | `peSnapshotHash` |

`page_title` remains optional input context and is deliberately not persisted as
a new field. No raw HTML, crawler payload, score, AI result, or email data is
included.

## Idempotency

The adapter computes the snapshot hash from canonicalized EvidenceItem fields,
then queries `ResearchEvidence` by both `leadId` and `peSnapshotHash`.

- A complete matching snapshot is returned as `SKIPPED`; no create request is made.
- A partial matching snapshot creates only evidence IDs missing from that snapshot.
- Duplicate evidence IDs in a submitted bundle are rejected before any API lookup or write.
- Invalid items are rejected before any CRM operation.
- Lookup and creation errors return structured `FAILED` results without Lead mutation.

## Validation

| Check | Result |
|---|---|
| Phase3C07.2 unit tests | PASS — 6 tests |
| C07.1 + C06 boundary + local client combined tests | PASS — 51 tests |
| Connector suite | PASS — 86 tests |
| Extension suite | PASS — 57 tests |
| Worker suite | PASS — 31 tests |
| Static suite | PASS — 2 tests |
| Core Regression Gate | PASS — required suites 5/5 |

Regression result: `temp/test-results/regression-gate-20260713-233024-485.json`.

## Explicitly Unchanged

- Lead creation and Lead updates
- Opportunity and ProspectPool behavior
- Scoring, AI, email, and workflow logic
- C06 entity schema, API contract, and metadata
- Database migrations
