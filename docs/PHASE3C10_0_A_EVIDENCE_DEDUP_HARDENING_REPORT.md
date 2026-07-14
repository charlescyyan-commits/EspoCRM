# Phase3C10.0-A — ResearchEvidence Dedup Hardening

Status: **PASS**  
Commit: **not created**

## Scope

Hardened the connector-side `ResearchEvidence` persistence adapter only. No
EspoCRM metadata, schema, migrations, Lead fields, scoring, email, or workflow
behavior changed.

## Deterministic Identity Decision

The final per-evidence identity is SHA-256 over a versioned canonical payload:

```text
c10-research-evidence-identity-v1
+ leadId
+ canonical source URL
+ normalized claimType
+ SHA-256(normalized claim)
```

The source URL canonicalization lower-cases scheme and host, drops fragments
and default ports, normalizes a root/trailing slash, and deterministically sorts
query parameters. Claim whitespace is normalized before hashing.

`snapshotHash` remains persisted unchanged as immutable extraction-run
provenance, but is intentionally excluded from the per-evidence identity. A
bundle snapshot changes when unrelated evidence is added, removed, or captured
at a different time; including it would allow the same lead-scoped fact to be
created again in a later run.

## Persistence Behavior

1. The adapter retains the existing Lead + snapshot lookup as a fast path.
2. For an item not found in that snapshot, it performs a read-only Lead +
   source URL + claim type + claim lookup and verifies the returned record's
   deterministic identity locally.
3. A matching identity is returned as `SKIPPED`; no create call occurs.
4. A non-matching identity is created with the frozen C06 field mapping and
   existing snapshot hash.
5. A partial failure retry retains the existing records and creates only the
   missing items.

No existing evidence is deleted or modified. The connector uses only existing
ResearchEvidence fields; no identity field is persisted and no API payload
contract is expanded.

## Tests Added

`chitu-connector/tests/test_phase3c10_evidence_dedup_hardening.py`

| Case | Result |
|---|---|
| Same Lead + same fact in a different snapshot | PASS — skipped |
| Same Lead + different fact | PASS — created |
| Different Lead + same fact | PASS — created |
| Partial create failure retry | PASS — missing item only |
| Deterministic identity generation | PASS |

## Validation

| Validation | Result |
|---|---|
| C10 dedup tests | PASS — 5 tests |
| C07 tests | PASS — 21 tests |
| C08 tests | PASS — 13 tests |
| C09 tests | PASS — 13 tests |
| Core Regression Gate | PASS — Extension 57, Connector 86, Worker 31, Static 2, runner integrity 5/5 |

Regression artifact:
`temp/test-results/regression-gate-20260714-140030-611.json`.

## Explicitly Unchanged

- C06 ResearchEvidence schema and entity definitions
- Evidence extraction and qualification logic
- Lead, ProspectPool, Opportunity, scoring, email, and workflow behavior
- Database migrations and external runtime execution
