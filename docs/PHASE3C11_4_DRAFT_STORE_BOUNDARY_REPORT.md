# Phase3C11.4 DraftStore Boundary Report

**Date:** 2026-07-14  
**Result:** PASS WITH RISKS

## Protocol Design

Phase3C11.4 introduces an independent connector contract in
`chitu_connector.espocrm_sync.draft_store`:

```text
C09 Facts -> Draft Generation -> DraftStore -> Approval -> SendExecution
```

`DraftStore` provides only four operations:

- `save(DraftSnapshotInput) -> DraftSnapshot`
- `get(draft_id) -> DraftSnapshot | None`
- `get_content_hash(draft_id) -> str | None`
- `verify_snapshot(approved, send_execution) -> SnapshotVerification`

`DraftSnapshotInput` requires a draft identity, Lead reference, subject, body,
business metadata, evidence references, score-snapshot reference, and a
timezone-aware generation timestamp. `DraftSnapshot` is immutable and adds a
stable content hash. `DraftContentReference` is the intentionally small pair
(`draft_id`, `content_hash`) that future DraftApproval and SendExecution flows
can retain without adding content to their records.

No C10 lifecycle, approval state machine, send orchestration, provider
adapter, reply contract, or fake-provider test was changed.

## Storage Boundary

The sole implementation is `InMemoryDraftStore`, a thread-safe, process-local
reference store. It creates no CRM entity, database table, metadata change, or
CRM write. It has no network or provider dependency.

Saving the same snapshot for a draft ID is idempotent and returns the original
snapshot. Reusing an existing draft ID with changed content or trace identity
is rejected, so a draft identity cannot silently point to different content.

## Hash Strategy

The store calculates a lowercase SHA-256 digest over deterministic UTF-8 JSON
with sorted keys and compact separators. The hash covers:

- subject and body;
- validated business metadata;
- sorted evidence references; and
- the score-snapshot reference.

The draft ID, Lead ID, and generation time remain trace fields rather than hash
inputs. Identical draft content therefore produces the same hash, while any
content, metadata, evidence, or score-snapshot change produces a different
hash.

## Content Boundary

The snapshot contract has no field for AI reasoning, hidden reasoning, prompts,
or model traces. Metadata keys and metadata string values are validated before
storage; forbidden reasoning or prompt material is rejected. The store permits
only draft subject/body, business metadata, content hash, evidence references,
and the required identity/trace references.

## Approval Integration Preparation

This phase does not alter `DraftApproval` or the C10 approval state machine.
Future approval persistence can retain a `DraftContentReference` containing
the approved `draft_id` and `content_hash`. `verify_snapshot` verifies that
the approval reference, the future send-execution reference, and the stored
snapshot all agree.

## Send Verification Preparation

This phase does not execute a send. Before a future send is accepted, its
draft reference can be passed with the approved reference to `verify_snapshot`.
Mismatched draft IDs, mismatched hashes, invalid references, missing snapshots,
and a stored-hash mismatch all return an explicit safe failure result. No
provider call is reachable from this module.

## Tests

Added `tests/test_phase3c11_4_draft_store.py` with nine deterministic checks:

1. a saved draft is retrievable and exposes its hash;
2. saving the same draft twice is idempotent and creates one snapshot;
3. identical content has an identical stable hash;
4. changed content has a different hash;
5. matching approval and send references verify successfully;
6. changed content after approval fails verification safely;
7. AI-reasoning and prompt metadata is rejected;
8. an existing draft ID cannot replace an immutable snapshot; and
9. the module has no external side-effect dependencies.

Focused C11.2/C11.3/C11.4 boundary tests passed **25/25**, including the
existing C10 frozen-contract hash checks.

## Runtime Verification

| Verification | Result |
|---|---|
| C11.4 focused DraftStore tests | PASS — 9/9 |
| C11.2/C11.3/C11.4 focused boundary tests | PASS — 25/25 |
| Extension suite | PASS — 65/65 |
| Connector suite, including C10 | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 suites, 382/382 tests |

Successful Regression Gate command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable 'C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

Gate evidence: `temp/test-results/regression-gate-20260714-184835-738.json`.
The recorded overall status is `PASS`.

The DraftStore tests use only the in-memory implementation. No CRM write,
Provider call, email send, Worker execution, queue operation, retry execution,
or CRM Draft entity creation was performed by Phase3C11.4.

## Risks

1. **Reference storage is volatile.** `InMemoryDraftStore` is intentionally
   process-local; a restart loses snapshots. A future approved phase may add a
   CRM-backed or other durable adapter that implements the same protocol.
2. **C10 is deliberately not yet wired to this check.** This phase makes
   approval and send verification available but does not alter their frozen
   contracts. Enforcement at an actual send boundary requires later explicit
   approval.
3. **RISK-C11.3-001 remains deferred.** The separate multiple-writer risk for
   Lead email projection fields is unchanged and remains planned for C11.5
   Operational Hardening or later.

## Scope Confirmation

No CRM Draft entity, database schema, CRM metadata, Provider integration,
Worker, Queue, retry execution, or C11.5 work was introduced.
