# Phase3C02.2B — Acquisition Worker Core Report

**Date:** 2026-07-13  
**Workspace:** `D:\EspoCRM-Production`  
**Verdict:** **PASS** — isolated worker core and deterministic provider verified; runtime validation **DEFERRED**.

## 1. Scope

Implemented a provider-neutral, single-`SearchJob` acquisition core inside the existing independent `chitu_connector` package. The work is deliberately offline: it adds no EspoCRM HTTP client, no real search provider, no daemon, no scheduling, and no connector-sync call.

The shared EspoCRM test stack was not installed, rebuilt, cache-cleared, restarted, written to, or browser-tested. This follows the phase's shared-runtime restriction.

## 2. Files Changed

- `chitu-connector/chitu_connector/acquisition/__init__.py`
- `chitu-connector/chitu_connector/acquisition/models.py`
- `chitu-connector/chitu_connector/acquisition/provider.py`
- `chitu-connector/chitu_connector/acquisition/fake_provider.py`
- `chitu-connector/chitu_connector/acquisition/normalization.py`
- `chitu-connector/chitu_connector/acquisition/worker.py`
- `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py`
- `docs/PHASE3C02_2B_ACQUISITION_WORKER_CORE_REPORT.md`

No existing SearchJob, ProspectPool, SearchStrategy, UI, metadata, route, manifest, connector-sync, scoring, research, or email files were changed by this phase.

## 3. Worker Contract

The core provides these provider-neutral types:

- `SearchRequest`
- `RawCandidate`
- `NormalizedCandidate`
- `ProviderResult`
- `ProviderError` (`code`, safe message, `retryable`)
- `JobExecutionResult`
- `SearchProvider` protocol
- `AcquisitionStore` protocol

`AcquisitionWorker.execute_job(search_job_id)` is the sole execution entry point. The store's `claim_queued_job` boundary must be implemented atomically by a later EspoCRM adapter; it only returns a job after changing it from `QUEUED` to `RUNNING`.

## 4. Fake Provider Behavior

`DeterministicFakeProvider` has no imports or calls for networking, credentials, time, or random data. Identical `SearchRequest` values produce identical results.

| Keyword mode | Result |
|---|---|
| ordinary keyword | two valid candidates plus one normalized duplicate |
| `fake:empty` | successful empty result |
| `fake:retryable-error` | `FAKE_TRANSIENT`, retryable |
| `fake:non-retryable-error` | `FAKE_INVALID_REQUEST`, not retryable |

## 5. SearchJob State Transitions

```text
QUEUED --atomic claim--> RUNNING --successful provider--> COMPLETED
                                  --ProviderError--------> FAILED
```

Only `QUEUED` is claimable. `RUNNING`, `COMPLETED`, `FAILED`, and `CANCELLED` return `NOT_CLAIMED` and perform no ProspectPool write. The worker does not retry automatically.

On completion, it persists existing SearchJob counters (`resultCount`, `acceptedCount`, `rejectedCount`, `prospectCount`) and timestamps. `JobExecutionResult` separately supplies the exact `duplicate_count`; no existing SearchJob metadata field was modified to avoid overlap with the parallel acquisition worktree.

## 6. Candidate Normalization

- lowercases domains;
- removes protocol, repeated `www.`, port, path, query, fragment, terminal punctuation, and surrounding whitespace;
- canonicalizes company-name whitespace;
- rejects missing/invalid domains;
- validates source URLs as HTTP(S) references;
- stores `website` as `https://{normalized-domain}`;
- creates a SHA-256 digest of a canonicalized raw payload rather than persisting raw payload data.

## 7. Deduplication Rule

The deterministic identity is `SHA-256(provider_name + "|" + normalized_domain)`. Duplicate detection applies both within one provider result and against records already exposed by the store as the same provider/domain. Company name is never an identity key.

## 8. ProspectPool Persistence

For each accepted candidate, the store receives one ProspectPool-shaped record with:

- `queue=DISCOVERY`, `status=WAITING`, `researchStatus=NOT_STARTED`, `qualificationStatus=PENDING`, and `crmPushStatus=NOT_READY`;
- source SearchJob ID;
- provider name, provider candidate ID, normalized website/domain, source URL, and country;
- a safe `note` containing the dedupe fingerprint, normalized domain, and raw-payload SHA-256 digest only.

No raw provider payload, credentials, or exception traceback is persisted.

## 9. Side-Effect Boundary

The acquisition package contains no `urlopen`, `requests`, `http.client`, `socket`, `curl`, `fetch`, `ChituSyncService`, or connector sync invocation. Its only persistence calls are `claim_queued_job`, `update_search_job`, `has_prospect`, and `create_prospect` on an injected store.

It has no path to create Lead, Contact, Account, Opportunity, ResearchEvidence, Email Draft, or email records.

## 10. Tests and Results

Executed using the bundled Python 3.12 runtime:

| Check | Result |
|---|---:|
| isolated Phase3C02.2B worker-core tests | 10 passed |
| full existing `chitu-connector` test suite | 68 passed |
| existing CRM extension structural suite | 38 passed |
| Python bytecode compilation for all new files | passed |
| static forbidden-network/connector call scan of acquisition package | no matches |
| `git diff --check` | passed (only pre-existing line-ending warnings) |

The isolated coverage includes lifecycle, fake-provider determinism, two inserts, internal and cross-job deduplication, deterministic fingerprints, normalization, empty results, both error classes, non-queued/cancelled refusal, default DISCOVERY queue, raw-payload exclusion, and no downstream entity writes.

## 11. Runtime Validation Status

**DEFERRED.** This phase explicitly prioritizes isolated tests while the EspoCRM-Test runtime may be in use by Phase3C02.1A. No shared database records were created. A future adapter must be validated with an atomic EspoCRM `QUEUED` claim and an actual ProspectPool record write before real-provider work is considered.

## 12. Collision Check with Phase3C02.1A

The worktree contains pre-existing, uncommitted SearchStrategy/SearchJob/UI/ACL changes, including the parallel Phase3C02.1A area. This phase only added the independent `chitu-connector/acquisition/` package, one adjacent test, and this report. It did not edit, format, stage, revert, or commit any parallel-task file.

## 13. Known Limitations

- No production EspoCRM `AcquisitionStore` adapter is included; the supplied in-memory store is a strict isolated test double.
- Duplicate count is returned in `JobExecutionResult`; the current SearchJob metadata has no dedicated persisted `duplicateCount` field and was intentionally left untouched.
- `retryable` is encoded safely in the existing `failureReason` value because current SearchJob metadata has no dedicated boolean field.
- There is no daemon, scheduler, batch loop, automatic retry, real provider, or credential handling.

## 14. Recommended Next Task

After parallel workspace changes are safely settled, implement and runtime-validate a narrowly scoped EspoCRM `AcquisitionStore` adapter with an atomic QUEUED-to-RUNNING claim and ProspectPool create/read dedup bridge. Keep the deterministic provider as the only provider until a separately approved real-provider phase.

## 15. Commit Status

**Not committed.** The worktree contains unrelated and parallel uncommitted files, so staging/committing could not be safely isolated under this phase's commit rule. The files listed in section 2 are the pending Phase3C02.2B files.
