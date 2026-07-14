# Phase3C08.2 — Canonical Score Integration Report

Status: **PASS — integration boundary**  
Commit: **not created**

## Scope Delivered

Added a single-path bridge from C08.1 `ScoreInput` to an injected canonical
scoring executor:

`ScoreInput + ResearchEvidence refs` → `CanonicalScoreIntegration` → `CanonicalScoreDecision`

Implementation: `chitu-connector/chitu_connector/espocrm_sync/canonical_score_integration.py`.

The bridge calls exactly one `CanonicalScoreExecutor` for an explicit input,
then returns the executor's `CanonicalScoreResult` unchanged. It contains no
formula, weighting, tier logic, fallback scorer, AI model, CRM client, or
persistence code.

## Preserved Canonical Ownership

The following are retained directly from the canonical result and never
recomputed or modified by C08.2:

- `opportunity_score`
- `score_tier`
- score reasons and component traces
- canonical engine version
- canonical content hash
- canonical adapter version and scoring timestamp

## Traceability

`CanonicalScoreTrace` records:

| Trace field | Source |
|---|---|
| `input_hash` | Canonical serialization of C08.1 ScoreInput facts |
| `input_evidence_refs` | Sorted unique `ResearchEvidence.peEvidenceId` values |
| `qualification_status` | C07 QualificationDecision propagated through ScoreInput |
| `canonical_engine_version` | Unmodified canonical result value |
| `canonical_content_hash` | Unmodified canonical result value |

This creates an auditable link from input evidence to a canonical score decision
without creating a competing scoring path.

## Canonical Engine Availability

The workspace provides stable vendored canonical result contracts, but its
`DecisionEngineAdapter` is explicitly disabled and no executable canonical V4
engine implementation is included here. C08.2 therefore exposes the
`CanonicalScoreExecutor` invocation seam for the existing external canonical
owner. Tests use a fixed-output canonical fixture solely to verify that the
bridge does not calculate or modify results.

## Tests

New coverage: `chitu-connector/tests/test_phase3c08_canonical_score_integration.py`.

| Scenario | Result |
|---|---|
| Same ScoreInput | PASS — same canonical result and trace hash |
| Explicit evaluation | PASS — exactly one canonical executor call |
| Regression compatibility | PASS — frozen score, tier, versions, and result object preserved |
| Evidence-to-decision traceability | PASS — input evidence IDs and content hash retained |

## Validation

| Check | Result |
|---|---|
| C08.2 unit tests | PASS — 3 tests |
| C08.1 + C07 + C06 boundary combined tests | PASS — 57 tests |
| Connector suite | PASS — 86 tests |
| Extension suite | PASS — 57 tests |
| Worker suite | PASS — 31 tests |
| Static suite | PASS — 2 tests |
| Core Regression Gate | PASS — required suites 5/5 |

Regression result: `temp/test-results/regression-gate-20260713-235356-456.json`.

## Explicitly Unchanged

- Canonical scoring algorithms, formulas, tiers, and version definitions
- AI / DeepSeek and email generation
- Lead, ProspectPool, Opportunity, and ResearchEvidence mutation
- CRM schema, API, migrations, and workflow behavior
