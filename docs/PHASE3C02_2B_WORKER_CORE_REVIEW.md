# Phase3C02.2B — Worker Core Deep Review

**Date:** 2026-07-13
**Reviewer:** Claude Code (DeepSeek V4 Pro, high reasoning effort)
**Scope:** Read-only code audit of Phase3C02.2B Acquisition Worker Core
**Mode:** Read-only — no code modified, no commits, no runtime changes

---

## 1. Executive Verdict

**CONDITIONAL PASS**

The Worker Core architecture is sound and provides a clean foundation for downstream phases. The separation of `SearchProvider` (protocol), `AcquisitionStore` (protocol), and `AcquisitionWorker` (orchestrator) is well-designed. The deterministic fake provider enables reliable offline testing. Domain normalization and fingerprint-based deduplication are correctly isolated.

**However**, three correctness-level gaps MUST be addressed before or early in Phase3C02.2C:

1. **BLOCKER-01**: Non-`ProviderError` exceptions (e.g., persistence failures from the EspoCRM REST adapter) are unhandled — they crash the worker and leave the job stuck in `RUNNING` with no error record.
2. **BLOCKER-02**: The write loop has no transactional boundary — partial `create_prospect` success followed by a subsequent failure leaves orphaned ProspectPool records with the job still `RUNNING`.
3. **BLOCKER-03**: The `AcquisitionStore` protocol has no version/CAS parameter — the real EspoCRM REST adapter has no way to implement atomic `QUEUED→RUNNING` claims or safe status transitions.

These do NOT require a Worker Core redesign. They are bounded additions to the error-handling path, the store protocol, and the write loop. The core architecture, data contracts, normalization, and deduplication logic are all ready to proceed.

---

## 2. Reviewed Files

| File | Role |
|------|------|
| `chitu-connector/chitu_connector/acquisition/__init__.py` | Public API surface |
| `chitu-connector/chitu_connector/acquisition/models.py` | DTOs and error type |
| `chitu-connector/chitu_connector/acquisition/provider.py` | `SearchProvider` Protocol |
| `chitu-connector/chitu_connector/acquisition/fake_provider.py` | Deterministic test double |
| `chitu-connector/chitu_connector/acquisition/normalization.py` | Domain normalization + fingerprint |
| `chitu-connector/chitu_connector/acquisition/worker.py` | `AcquisitionWorker` + `AcquisitionStore` Protocol |
| `chitu-connector/tests/test_phase3c02_2b_acquisition_worker_core.py` | 10 unit tests |
| `docs/PHASE3C02_2B_ACQUISITION_WORKER_CORE_REPORT.md` | Phase implementation report |
| `crm-extension/Resources/entityDefs/SearchJob.json` | EspoCRM SearchJob schema |
| `crm-extension/Resources/entityDefs/ProspectPool.json` | EspoCRM ProspectPool schema |

---

## 3. Architecture and Separation

### 3.1 Layer Map

```
┌─────────────────────────────────────────────────┐
│  AcquisitionWorker  (orchestration)              │
│  - claim → execute → normalize → dedup → persist │
├─────────────────────────────────────────────────┤
│  SearchProvider (Protocol)     AcquisitionStore  │
│  ↑                             (Protocol)        │
│  DeterministicFakeProvider     ↑                 │
│                                MemoryStore       │
├─────────────────────────────────────────────────┤
│  Models: SearchRequest, RawCandidate,            │
│  NormalizedCandidate, ProviderResult,            │
│  ProviderError, JobExecutionResult               │
├─────────────────────────────────────────────────┤
│  normalization.py: normalize_candidate(),        │
│  normalize_domain(), normalize_source_url()      │
└─────────────────────────────────────────────────┘
```

### 3.2 Findings

| # | Finding | Severity |
|---|---------|----------|
| A1 | `SearchProvider` Protocol is clean: `name` property + `search(request) → ProviderResult`. No ambiguity. | ✅ OK |
| A2 | Worker depends on `SearchProvider` Protocol, never on `DeterministicFakeProvider`. Constructor injection. | ✅ OK |
| A3 | DTOs (`SearchRequest`, `RawCandidate`, `NormalizedCandidate`, etc.) are `frozen=True, slots=True` dataclasses — immutable, hashable, side-effect-free. | ✅ OK |
| A4 | No `SearchJob` domain model exists. Worker reads raw `Mapping[str, Any]` dicts from `claim_queued_job()`. Field names are string literals (`"keyword"`, `"country"`, etc.) with no typed contract. This diverges from `espocrm_sync/models.py` which uses typed dataclasses (`SyncSource`, `GateDecision`, `AdapterResult`). | **MEDIUM** |
| A5 | Worker responsibilities: claim, execute, normalize, deduplicate, persist. It does NOT handle CLI, transport, scheduling, retry loops, or batching. Clean separation. | ✅ OK |
| A6 | `normalize_candidate()` is a hard-coded free function imported directly by `worker.py`. It is NOT injectable — swapping normalization logic requires modifying `worker.py`. | **MEDIUM** |
| A7 | Deduplication is baked into the worker (intra-job `seen_fingerprints: set[str]` + cross-job `has_prospect()`). Not independently injectable or testable in isolation from the worker. | **MEDIUM** |
| A8 | `__init__.py` exports 8 symbols. `DeterministicFakeProvider` is a test-only class in the public API. | **LOW** |
| A9 | No circular imports. Dependency graph: `models` ← `provider` / `fake_provider` / `normalization` ← `worker` ← `__init__`. | ✅ OK |
| A10 | No naming conflicts with existing `espocrm_sync` or `vendored` packages. `ProviderError` is unique to `acquisition`. | ✅ OK |
| A11 | Package location `chitu_connector/acquisition/` is appropriate for long-term runtime. It sits alongside `espocrm_sync/` without coupling. | ✅ OK |
| A12 | EspoCRM REST API adapter can be added without modifying worker — it implements `AcquisitionStore`. | ✅ OK |
| A13 | Real Provider adapter can be added without modifying worker — it implements `SearchProvider`. | ✅ OK |

### 3.3 Architecture Verdict

The architecture is well-layered for a Phase 2B core. The main structural concern (A4, untyped job dicts) will surface when the EspoCRM adapter needs to map real entity fields. The pattern used in `espocrm_sync/models.py` (typed dataclasses) should be followed for `SearchJob` and `ProspectPool` domain models in C02.2C.

---

## 4. State Machine Review

### 4.1 Current Implicit State Machine

The state transitions are embedded in control flow, not declared as an explicit state machine:

```
QUEUED ──[claim_queued_job()]──► RUNNING ──[success]──► COMPLETED
                                    │
                                    └──[ProviderError]──► FAILED

CANCELLED → NOT_CLAIMED (no transition)
RUNNING   → NOT_CLAIMED (no transition)
COMPLETED → NOT_CLAIMED (no transition)
FAILED    → NOT_CLAIMED (no transition)
```

### 4.2 Per-Transition Analysis

| Transition | Implemented? | Mechanism | Issue |
|------------|:---:|-----------|-------|
| QUEUED → RUNNING | ✅ | `claim_queued_job()` — protocol documents atomicity, in-memory store does `dict.update()` | Protocol can't enforce atomicity (see BLOCKER-03) |
| RUNNING → COMPLETED | ✅ | `update_search_job(status="COMPLETED")` after all candidates processed | Written AFTER prospects created — see BLOCKER-02 |
| RUNNING → FAILED | ✅ | `update_search_job(status="FAILED")` in `except ProviderError` | Only catches `ProviderError` — see BLOCKER-01 |
| CANCELLED → (blocked) | ✅ | `claim_queued_job` returns None for non-QUEUED status | Store-dependent; protocol does not enumerate gated statuses |
| COMPLETED → (blocked) | ✅ | Same mechanism | OK |
| FAILED → QUEUED (retry) | ❌ | No mechanism. Job stays FAILED. Manual reset required. | **MEDIUM** — by design (no auto-retry), but adapter needs a reset path |
| RUNNING → FAILED (timeout) | ❌ | No timeout/lease/heartbeat mechanism | **HIGH** — crashed worker leaves job RUNNING forever |
| RUNNING → RUNNING (re-claim) | ❌ | No protection against stale RUNNING being re-claimed | Related to timeout gap |

### 4.3 Key Questions

**Q: Is this an explicit state machine?**
No. There is no `StateMachine` class, no transition table, no state enum, and no transition validation. Transitions are hard-coded string writes (`"COMPLETED"`, `"FAILED"`) inside conditional branches of `execute_job()`. Additional states or transition rules would require modifying the worker's control flow.

**Q: Are there illegal state transitions?**
Potentially. The worker writes `"COMPLETED"` or `"FAILED"` without checking current state. It relies on `claim_queued_job` having already validated QUEUED status, but the store protocol does not prevent an adapter from accepting `update_search_job(status="COMPLETED")` on a CANCELLED job.

**Q: Can ProspectPool be written before COMPLETED?**
Yes — this is the current behavior. `create_prospect()` is called inside the candidate loop, before `update_search_job(status="COMPLETED")`. If the worker crashes mid-loop or `update_search_job` fails, prospects exist with no completed job.

**Q: Can a job get stuck in RUNNING?**
Yes — three paths:
1. Worker crash between claim and completion (no timeout recovery).
2. Unhandled non-`ProviderError` exception (no FAILED transition written).
3. `update_search_job` failure after successful `create_prospect` calls.

**Q: Are attempt / lease / heartbeat / version / claimedAt fields needed?**
| Field | Needed? | Rationale |
|-------|:------:|-----------|
| `claimedAt` | **Yes** | Already passed as `started_at` by worker. Store protocol should require storing it. Needed for timeout detection. |
| `attempt` | **Yes** | Required for retry logic — distinguish first attempt from retry. Not in current SearchJob schema. |
| `lease` / `heartbeat` | **Yes** | Required for RUNNING timeout detection in multi-worker setups. Not in schema. |
| `version` | **Yes** | Required for optimistic locking / CAS on `claim_queued_job`. Not in protocol. |

### 4.4 State Machine Verdict

The current implicit state machine is sufficient for single-runner CLI use but lacks the guards needed for multi-worker or production use. An explicit `SearchJobState` enum with a transition table should be added in C02.2C. The EspoCRM SearchJob entity already defines the correct enum values (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`) — these should be mirrored as a Python `StrEnum` in the acquisition models.

---

## 5. Concurrency and Idempotency

### 5.1 Findings

| # | Finding | Severity |
|---|---------|----------|
| C1 | `MemoryAcquisitionStore.claim_queued_job()` uses `dict.update()` — not atomic. Two concurrent readers could both claim the same job. The protocol text documents the atomicity requirement; the in-memory implementation violates it. | **MEDIUM** (protocol is correct; test double is not — not a production issue but means tests can't verify concurrent safety) |
| C2 | Two runners claiming the same job simultaneously would both execute and both write prospects. The protocol documents atomicity as a requirement, but there is no CAS parameter to enable it. | **HIGH** (protocol needs version parameter to enable real CAS) |
| C3 | No CAS abstraction exists. `update_search_job(job_id, values)` has no version/etag/expected-status parameter. The EspoCRM REST adapter would need to implement CAS via HTTP `If-Match` but the protocol can't express it. | **HIGH** (BLOCKER-03) |
| C4 | Fingerprint `SHA-256(provider_name\|normalized_domain)` is stable across executions. Same input → same fingerprint. | ✅ OK |
| C5 | Fingerprint algorithm has no version tag. If the algorithm changes (e.g., adding `country` to identity), old fingerprints become silently incompatible. | **MEDIUM** |
| C6 | Provider success + persistence write failure: Prospects are created before `update_search_job("COMPLETED")`. If `update_search_job` fails, prospects exist with job RUNNING. On re-execution (if status reset), dedup via `has_prospect` would catch them — but `has_prospect` is not guaranteed to run before `create_prospect` in a transactional context. | **HIGH** (BLOCKER-02) |
| C7 | Within-job dedup uses `seen_fingerprints` (in-memory set). Cross-job dedup uses `has_prospect(provider_name, normalized_domain)`. Both key on `(provider_name, domain)`. Consistent. | ✅ OK |
| C8 | Same domain from different providers: NOT deduplicated. `has_prospect` filters by `provider_name`. This means `example.com` discovered by Google and by Bing creates two ProspectPool records. This is a design decision — the identity is `(provider, domain)`, not `domain` alone. Should be documented explicitly. | **MEDIUM** |
| C9 | Same provider, same domain, different strategy: Strategy is not part of the fingerprint. Two strategies finding the same domain from the same provider would be deduplicated. Reasonable — strategy is a discovery detail, not an identity detail. | ✅ OK |
| C10 | Source URL change does NOT change fingerprint (not part of identity). Correct — source URL is metadata. | ✅ OK |
| C11 | Provider candidate ID is stored as `externalProspectId` but NOT used for dedup identity. If a provider returns the same company under two different candidate IDs (e.g., branch locations), they'd be merged into one prospect. | **LOW** — design tradeoff; document the behavior |

### 5.2 Identity Distinctions

The current model conflates two distinct concepts:

| Concept | Current Key | Should Be |
|---------|-------------|-----------|
| **Candidate identity** (who the provider found) | `provider_candidate_id` (stored, not used for dedup) | `(provider_name, provider_candidate_id)` — traceability key |
| **Discovery occurrence** (this specific search event) | Not tracked separately | `(job_id, provider_name, provider_candidate_id)` — audit trail |
| **ProspectPool record identity** (unique dealer) | `SHA-256(provider_name\|domain)` | Same — but the provider-scoped identity is a design choice that should be explicit |
| **Job-result relationship** | `searchJobId` on ProspectPool | OK — links prospect back to originating job |

The design choice to scope identity to `(provider, domain)` rather than `domain` alone means cross-provider deduplication is intentionally absent. This should be documented as a conscious decision, with a note that a future cross-provider merge step may be needed.

### 5.3 Concurrency Verdict

The core is safe for single-runner execution. For multi-worker production use, **BLOCKER-03** (CAS/version parameter in protocol) must be resolved. The identity model is internally consistent; the provider-scoped dedup is a reasonable Phase 2 choice that should be documented.

---

## 6. Domain Normalization

### 6.1 Input-by-Input Trace

| # | Input | normalize_domain() Result | Correct? | Notes |
|---|-------|--------------------------|:------:|-------|
| 1 | `HTTPS://WWW.Example.COM/path?q=1#x` | `example.com` | ✅ | Protocol lowered, www stripped, path/query/fragment removed |
| 2 | `example.com.` | `example.com` | ✅ | Trailing dot stripped after urlparse |
| 3 | `sub.example.co.uk` | `sub.example.co.uk` | ⚠️ | Subdomain preserved. Without PSL, cannot determine `example.co.uk` is the registrable domain. |
| 4 | `www2.example.com` | `www2.example.com` | ⚠️ | `www2.` is not stripped (only `www.` is). May or may not be a real subdomain. |
| 5 | `example.com:443` | `example.com` | ✅ | Port stripped by urlparse |
| 6 | `user:pass@example.com` | `example.com` | ✅ | Userinfo stripped by urlparse |
| 7 | Unicode IDN: `münchen.de` | **Rejected** (None) | ❌ | `_valid_hostname()` regex `[a-z0-9.-]` rejects `ü`. Should be Punycode-encoded or the regex should accept non-ASCII. |
| 8 | Punycode: `xn--mnchen-3ya.de` | `xn--mnchen-3ya.de` | ✅ | ASCII punycode passes validation |
| 9 | `localhost` | **Rejected** (None) | ✅ | No dot → rejected. Correct for dealer discovery. |
| 10 | IPv4: `192.168.1.1` | `192.168.1.1` | ⚠️ | Accepted. Not useful for dealer discovery but not harmful. |
| 11 | IPv6: `[::1]` | **Rejected** (None) | ✅ | Colons fail regex. Correct for dealer discovery. |
| 12 | `not a valid url` | **Rejected** (None) | ✅ | `_valid_hostname` rejects spaces |
| 13 | Empty string / `None` | **Rejected** (None) | ✅ | Guard clause |
| 14 | Company name only (no domain) | **Rejected** (None) | ✅ | Candidate rejected; `rejected_count` incremented |
| 15 | Source URL ≠ domain | Both stored independently | ✅ | No cross-validation; each normalized separately |

### 6.2 PSL (Public Suffix List) Analysis

| Issue | Impact | Severity |
|-------|--------|----------|
| `sub.example.co.uk` → keeps `sub.` | A regional subsidiary gets a different identity than the parent. Could create duplicate ProspectPool records for the same dealer (e.g., `london.dealer.co.uk` vs `manchester.dealer.co.uk`). | **MEDIUM** |
| `sub.example.com` → keeps `sub.` | Usually correct — `sub.example.com` is likely a real subdomain, not a public suffix issue. | ✅ OK |
| `www.` stripping | Handled. Repeated `www.` prefixes are stripped in a `while` loop. | ✅ OK |

**Recommendation:** Do NOT add PSL as a dependency in Phase 3C. Instead, document the subdomain behavior explicitly and add a post-normalization note: "Subdomains of known public suffixes (co.uk, com.au, co.jp, etc.) are NOT collapsed to the registrable domain. This may create duplicate records for regional dealer subdomains. A cross-provider merge step should handle this."

### 6.3 Security

| Risk | Present? | Notes |
|------|:------:|-------|
| SSRF via URL parsing | ❌ | `urlparse` only parses strings, never makes network requests |
| Dangerous URL schemes | ❌ | Only `http`/`https` accepted; `file://`, `gopher://`, etc. rejected |
| Unicode normalization attacks | ⚠️ | IDN domains are rejected rather than normalized. An attacker-controlled input with IDN homograph attacks would simply be rejected (safe failure mode) |
| Overly long domains | ⚠️ | `_valid_hostname` limits to 253 chars (0-251 + 2 for `[a-z0-9]` at each end), but doesn't limit individual labels. A domain with 63-char labels is technically valid but could cause issues downstream |

### 6.4 Normalization Verdict

The normalization is functional for the common case (ASCII domains, standard ports, common URL noise). Two gaps (IDN rejection, no PSL-awareness for co.uk-style domains) should be documented as known limitations. Neither is a blocker — IDN dealers are rare in the 3D printing space, and PSL can be deferred.

---

## 7. Determinism

### 7.1 Findings

| # | Check | Result |
|---|-------|--------|
| D1 | Uses `hash()`? | ❌ No — uses `hashlib.sha256()` |
| D2 | Dict/set iteration order matters? | ❌ No — `seen_fingerprints` is membership-only; `json.dumps(sort_keys=True)` for payload |
| D3 | Depends on current time? | ⚠️ Yes — `_now()` for `startedAt`/`completedAt` timestamps. Not part of identity, but timestamps vary. Acceptable. |
| D4 | Depends on `random`/`uuid4`? | ❌ No |
| D5 | Depends on process/machine state? | ❌ No |
| D6 | JSON field order stable? | ✅ `sort_keys=True` ensures deterministic serialization |
| D7 | Fake Provider cross-process stable? | ✅ Same `SearchRequest` → same `ProviderResult`. Test confirms. |
| D8 | Fingerprint includes version? | ❌ No — `SHA-256(provider_name\|domain)`. Algorithm version not embedded. |
| D9 | Future field changes silently change fingerprint? | ⚠️ If `normalize_candidate()` changes its fingerprint computation, old fingerprints become incompatible. No migration path. |

### 7.2 Determinism Verdict

The core is deterministic for all identity-sensitive paths. Timestamps vary (expected). The fingerprint versioning gap (D8) is a MEDIUM concern — add a version prefix (e.g., `v1:`) before the hash input in C02.2C to enable future algorithm migration.

---

## 8. Error Model

### 8.1 Current Error Classification

```
ProviderError(Exception)
├── code: str              # e.g., "FAKE_TRANSIENT", "RATE_LIMITED"
├── safe_message: str      # Human-readable, no secrets
└── retryable: bool        # Can the operation be retried?
```

### 8.2 Findings

| # | Finding | Severity |
|---|---------|----------|
| E1 | `ProviderError` has `retryable: bool` — clear retryability signal. | ✅ OK |
| E2 | Error classification is flat: `code: str` only. No subclasses for `NetworkError`, `RateLimitError`, `AuthError`, `InvalidRequestError`, `QuotaError`, `ParseError`. | **MEDIUM** — sufficient for core; subclasses should be added before real provider |
| E3 | `errorMessage` uses `error.safe_message`. `failureReason` uses `f"{error.code}; retryable=..."`. Both are safe — no payload, traceback, or secrets. | ✅ OK |
| E4 | Exception chain is consumed: `except ProviderError` catches, persists error, returns `JobExecutionResult`. No leak. | ✅ OK |
| E5 | Non-`ProviderError` exceptions (e.g., `create_prospect()` raising from EspoCRM REST adapter) are **not caught**. They propagate up uncaught, leaving the job `RUNNING` with no error record. | **BLOCKER** (BLOCKER-01) |
| E6 | Empty result (`len(candidates) == 0`) → `COMPLETED` with `result_count=0`. Correct. | ✅ OK |
| E7 | No mechanism for partial results + warning. If provider returns 10 candidates but notes 3 had parse issues, there's no way to express "7 good + 3 warnings." | **LOW** — can be added later |
| E8 | Persistence errors (from `AcquisitionStore`) are NOT classified as any error type — they'd be unhandled Python exceptions (see E5). | **BLOCKER** (same as BLOCKER-01) |
| E9 | The test at line 153 asserts `self.assertNotIn("Traceback", store.jobs["job-001"]["errorMessage"])` — good hygiene. But only tests ProviderError path, not unexpected exception path. | **MEDIUM** |

### 8.3 Minimum Error Classification for C02.2C

Without implementing, here is the recommended hierarchy:

```
AcquisitionError (base)
├── ProviderError
│   ├── retryable: bool
│   └── code: str
│       Suggested codes: NETWORK, RATE_LIMITED, AUTH_FAILURE,
│                        INVALID_REQUEST, QUOTA_EXCEEDED, PARSE_ERROR,
│                        PROVIDER_TIMEOUT, PROVIDER_UNKNOWN
├── PersistenceError
│   ├── retryable: bool
│   └── code: str
│       Suggested codes: CONNECTION_FAILED, WRITE_CONFLICT,
│                        ENTITY_NOT_FOUND, VALIDATION_FAILED
└── NormalizationError (for invalid candidates — currently silent rejection)
```

### 8.4 Error Model Verdict

The `ProviderError` design is clean and safe. The critical gap is the absence of a generic exception handler (BLOCKER-01). The flat error code approach works for Phase 2 but should be subclassed before connecting a real provider.

---

## 9. Persistence Adapter Readiness

### 9.1 Required Adapter Methods

| Method | In Protocol? | Notes |
|--------|:----------:|-------|
| `getSearchJob(id)` | ❌ | Not in protocol. Adapter may need to read job details before claiming. Currently `claim_queued_job` combines read+claim. |
| `claimQueuedJob(id, startedAt)` | ✅ | Returns `Mapping[str, Any] \| None`. But no version/CAS parameter. |
| `markRunning(...)` | ⚠️ | Implicit in `claim_queued_job`. No separate method. |
| `upsertProspect(...)` | ❌ | Only `create_prospect` exists. No upsert semantic for idempotent replay. |
| `markCompleted(...)` | ⚠️ | Via `update_search_job`. Generic — accepts any values, no transition validation. |
| `markFailed(...)` | ⚠️ | Same as above. |
| `listQueuedJobs(...)` | ❌ | Not in protocol. Batch runner needs this. |
| `getExistingFingerprints(...)` | ❌ | `has_prospect` returns `bool`, not fingerprints. Batch operations need bulk pre-check. |

### 9.2 Protocol vs EspoCRM REST API

| Concern | Gap |
|---------|-----|
| **CAS / optimistic locking** | `update_search_job` has no `expectedVersion` parameter. EspoCRM supports `If-Match` headers for optimistic locking. Cannot express this in current protocol. |
| **Insert vs Update distinction** | `create_prospect` is insert-only. No upsert. EspoCRM REST API distinguishes POST (create) from PUT (update). |
| **Return value richness** | `claim_queued_job` returns `Mapping[str, Any] \| None` — no distinction between "job not found", "job not QUEUED", and "claim conflict". Adapter can't signal the reason. |
| **Batch operations** | Each `has_prospect` and `create_prospect` is a separate call. For 100 candidates, that's 200 REST calls. No bulk endpoint in protocol. |
| **Transaction scope** | Protocol has no transaction boundary. Adapter can't express "these N creates + this update must be atomic." |
| **Error classification** | Persistence errors bubble up as untyped Python exceptions. No `PersistenceError` equivalent to `ProviderError`. |

### 9.3 Protocol vs EspoCRM Entity Field Alignment

**SearchJob fields written by worker:**
| Worker Writes | SearchJob Entity Field | Match? |
|---------------|------------------------|:-----:|
| `status: "FAILED"` / `"COMPLETED"` | `status` (enum) | ✅ |
| `completedAt` (ISO 8601 string) | `completedAt` (datetime) | ✅ |
| `errorMessage` | `errorMessage` (text) | ✅ |
| `failureReason` | `failureReason` (text) | ✅ |
| `resultCount` | `resultCount` (int) | ✅ |
| `acceptedCount` | `acceptedCount` (int) | ✅ |
| `rejectedCount` | `rejectedCount` (int) | ✅ |
| `prospectCount` | `prospectCount` (int) | ✅ |

**ProspectPool fields written by worker:**
| Worker Writes | ProspectPool Entity Field | Match? |
|---------------|---------------------------|:-----:|
| `name` | `name` (varchar 255) | ✅ |
| `externalProspectId` | `externalProspectId` (varchar 128) | ✅ |
| `source` | `source` (varchar 100) | ✅ |
| `sourceUrl` | `sourceUrl` (url) | ✅ |
| `website` | `website` (url) | ✅ |
| `country` | `country` (varchar 100) | ✅ |
| `queue: "DISCOVERY"` | `queue` (enum) | ✅ |
| `status: "WAITING"` | `status` (enum) | ✅ |
| `researchStatus: "NOT_STARTED"` | `researchStatus` (enum) | ✅ |
| `qualificationStatus: "PENDING"` | `qualificationStatus` (enum) | ✅ |
| `crmPushStatus: "NOT_READY"` | `crmPushStatus` (enum) | ✅ |
| `searchJobId` | `searchJob` (link) | ⚠️ Worker writes `searchJobId` string; entity has `searchJob` as `belongsTo` link. Adapter must translate string ID → entity link. |
| `note` | `note` (text) | ✅ |

> **Note on `searchJobId` vs `searchJob`:** The worker writes `"searchJobId": search_job_id` (a plain string). The EspoCRM entity defines `searchJob` as a `belongsTo` link. The adapter MUST translate this — typically by setting `searchJobId` (EspoCRM's convention for link ID fields) or constructing the link object. This is an adapter concern, not a worker concern, but the field name mismatch (`searchJobId` vs `searchJobId`) should be verified during adapter implementation.

### 9.4 Persistence Adapter Verdict

The protocol covers the happy path but lacks the guardrails needed for safe EspoCRM REST integration: CAS parameters, rich return types, batch operations, and error classification. **BLOCKER-03** (CAS) must be resolved. The other gaps (batch, upsert, listQueuedJobs) can be added incrementally.

---

## 10. Side-Effect Boundary

### 10.1 Static Analysis

The worker source (`worker.py`) was scanned for forbidden imports. The test at line 176-182 programmatically verifies:

```python
for forbidden in ("ChituSyncService", "Lead", "Opportunity", "ResearchEvidence",
                   "Email", "urlopen", "requests", "socket"):
    self.assertNotIn(forbidden, source)
```

### 10.2 Runtime Side-Effect Verification

| Operation | In Code? | Guarded By |
|-----------|:------:|------------|
| Lead creation | ❌ | Static scan + no Lead import |
| Account creation | ❌ | Static scan |
| Contact creation | ❌ | Static scan |
| Opportunity creation | ❌ | Static scan |
| ResearchEvidence creation | ❌ | Static scan |
| Email Draft | ❌ | Static scan |
| SMTP / email send | ❌ | Static scan |
| ChituSyncService call | ❌ | Static scan |
| Real HTTP call | ❌ | No `urlopen`, `requests`, `http.client`, `socket`, or `urllib.request` imports |
| Real Provider SDK | ❌ | Only `DeterministicFakeProvider` exists |
| Production credential read | ❌ | No credential/env-var access |
| `espocrm_sync` import | ❌ | Worker does not import from `espocrm_sync` |
| `brevo_api` import | ❌ | Worker does not import Brevo |

### 10.3 Indirect Side-Effect Risk

The only persistence calls are through the injected `AcquisitionStore` protocol:
- `claim_queued_job()` — mutates SearchJob status
- `update_search_job()` — mutates SearchJob fields
- `has_prospect()` — reads ProspectPool
- `create_prospect()` — creates ProspectPool

No other entity types are created or modified. The `note` field on ProspectPool contains only the fingerprint, normalized domain, and payload SHA-256 — no raw provider data, no credentials, no secrets.

### 10.4 Side-Effect Verdict

**Clean.** The worker has zero downstream CRM side effects beyond SearchJob status updates and ProspectPool creation. All other entity types are excluded. The only risk is that a future EspoCRM adapter could trigger hooks/formulas on ProspectPool creation — this is an adapter responsibility, not a worker concern.

---

## 11. Test Coverage Review

### 11.1 Test Inventory

| # | Test | What It Covers | Quality |
|---|------|---------------|---------|
| 1 | `test_fake_provider_is_deterministic_and_network_free_fixture` | Provider determinism, candidate count | **Good** — verifies `==` equality and count |
| 2 | `test_queued_job_transitions_to_completed_and_persists_two_discovery_prospects` | Full happy path: claim → execute → complete, all counters, prospect fields | **Good** — comprehensive assertions on job + prospects |
| 3 | `test_same_job_replay_is_not_claimed_or_written_again` | Idempotency: COMPLETED job not re-claimed | **Good** — verifies no duplicate writes |
| 4 | `test_same_provider_and_normalized_domain_deduplicates_across_jobs` | Cross-job dedup: second job finds all duplicates | **Good** — verifies 0 inserted, 3 duplicates |
| 5 | `test_domain_normalization_is_deterministic_and_removes_transport_noise` | Domain normalization + fingerprint stability | **Good** — exact SHA-256 assertion |
| 6 | `test_empty_result_completes_without_prospects` | Empty result → COMPLETED, no prospects | **Good** — edge case covered |
| 7 | `test_provider_errors_fail_job_with_explicit_retryability` | Both error types (retryable + non-retryable) | **Good** — parametrized subTest, checks no Traceback leak |
| 8 | `test_non_queued_and_cancelled_jobs_are_not_claimed` | All non-QUEUED statuses rejected | **Good** — parametrized subTest across 4 statuses |
| 9 | `test_invalid_candidate_is_rejected_without_downstream_side_effects` | Invalid candidate → rejected, no prospects, no entity writes | **Good** — specifically checks `other_entity_writes` |
| 10 | `test_core_has_no_connector_or_downstream_crm_side_effect_imports` | Static source scan for forbidden imports | **Good** — defense-in-depth |

### 11.2 Test Gaps by Priority

#### P0 — Must Add Before or Early in C02.2C

| Gap | Risk |
|-----|------|
| **No test for persistence failure mid-loop** | If `create_prospect()` raises after some writes succeed, worker crashes with inconsistent state. No test exercises this path. |
| **No test for `update_search_job` failure after prospects written** | Orphaned prospects with job RUNNING. Untested. |
| **No test for unexpected (non-ProviderError) exceptions** | Worker only catches `ProviderError`. A `ValueError`, `KeyError`, or adapter-level network error crashes the worker. No test. |
| **No contract test for `AcquisitionStore` protocol** | All tests use one implementation (`MemoryAcquisitionStore`). The protocol's atomicity, error behavior, and edge cases are untested against alternative implementations. |

#### P1 — Add Before Real Provider

| Gap | Risk |
|-----|------|
| No complex domain tests (IDN, punycode, co.uk, IPv4, port, userinfo, unicode) | Domain normalization may mishandle real-world dealer domains |
| No fingerprint collision test | If two different domains produce the same fingerprint, silent data loss |
| No concurrent claim test (two workers, same job) | Can't verify atomic claim behavior |
| No `result_limit` boundary test (0, 1, exact match, exceed) | Truncation behavior untested |

#### P2 — Add Before Production Worker

| Gap | Risk |
|-----|------|
| No cross-process determinism test (actual subprocess) | Determinism verified only in-process |
| No adapter-independent test (testing against protocol, not MemoryAcquisitionStore) | Protocol contract not validated independently of one implementation |
| No large result set performance test | 100+ candidates path untested |
| No intermediate state test (job status between claim and completion) | Can't verify job is RUNNING during execution |

### 11.3 Test Methodology Assessment

| Concern | Detail |
|---------|--------|
| **Over-reliance on MemoryAcquisitionStore** | All tests use a single in-memory implementation. This store never fails, never has write conflicts, and is never slow. Real adapter behavior is untested. |
| **Final-state-only assertions** | Tests check `result.status`, `store.jobs["job-001"]["status"]`, `store.prospects` — all post-execution. No test verifies intermediate state (e.g., "job is RUNNING after claim, before completion"). |
| **No mock call-order verification** | Tests don't verify that `create_prospect` is called BEFORE `update_search_job("COMPLETED")`, or that `has_prospect` is called before `create_prospect` for each candidate. |
| **MemoryAcquisitionStore implementation details bleed into tests** | `has_prospect` checks `website == f"https://{normalized_domain}"` — this is a store-level convention, not a protocol contract. A different store might use `normalized_domain` differently, causing tests to pass against MemoryAcquisitionStore but fail against a real adapter. |
| **`StaticProvider` is unused in most tests** | Only test 9 uses it. Tests 1-8 and 10 use `DeterministicFakeProvider`, which conflates provider behavior with test modes (`fake:empty`, `fake:retryable-error`). This is fine for unit tests but means provider behavior is tested through a special test-only provider. |

### 11.4 Test Coverage Verdict

The 10 tests provide good coverage of the happy path, idempotency, deduplication, error handling, and normalization. However, they are **infrastructure-happy-path tests** — they never exercise persistence failures, partial writes, or unexpected exceptions. The P0 gaps must be filled before connecting a real EspoCRM adapter, because the real adapter WILL fail (network errors, write conflicts, validation errors).

---

## 12. Findings Matrix

| ID | Severity | Area | Finding | Evidence | Required Stage |
|----|----------|------|---------|----------|:---:|
| **B01** | **BLOCKER** | Error Model | Non-`ProviderError` exceptions (persistence failures, unexpected errors) are unhandled. They crash the worker leaving job RUNNING with no error record. | `worker.py:48-57` — only `except ProviderError`; no `except Exception` safety net | C02.2C |
| **B02** | **BLOCKER** | Concurrency | Write loop has no transactional boundary. Prospects created before `update_search_job("COMPLETED")`. Partial writes leave inconsistent state. | `worker.py:59-93` — `create_prospect` called in loop before status update; no rollback/compensation | C02.2C |
| **B03** | **BLOCKER** | Persistence | `AcquisitionStore` protocol has no CAS/version parameter. EspoCRM REST adapter cannot implement atomic QUEUED→RUNNING claim via `If-Match`. | `worker.py:13-22` — `claim_queued_job(job_id, started_at)` with no `expectedVersion`; `update_search_job(job_id, values)` with no version | C02.2C |
| H01 | **HIGH** | State Machine | No timeout/lease/heartbeat for RUNNING jobs. Crashed worker leaves job RUNNING forever with no recovery path. | `worker.py` — no timeout logic; store protocol has no lease concept | C02.2C |
| H02 | **HIGH** | State Machine | Implicit state machine with no transition validation. Worker writes "COMPLETED"/"FAILED" without checking current state. | `worker.py:51-57, 95-104` — string literals for status; no state enum or transition table | C02.2C |
| H03 | **HIGH** | Domain | IDN/Unicode domains rejected by `_valid_hostname()` regex. `münchen.de` is a valid domain but fails `[a-z0-9.-]` check. | `normalization.py:68` — `re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", value)` | Real Provider |
| H04 | **HIGH** | Concurrency | No CAS abstraction for `update_search_job`. Two workers could race on status updates after both completing provider calls. | `worker.py:22` — `update_search_job(self, job_id, values)` with no version parameter | C02.2C |
| M01 | **MEDIUM** | Architecture | No `SearchJob` domain model. Worker reads untyped `Mapping[str, Any]` dicts. Field access via string keys (`job.get("keyword")`, `job.get("country")`). | `worker.py:39-47` — raw dict access; `espocrm_sync/models.py` uses typed dataclasses for comparison | C02.2C |
| M02 | **MEDIUM** | Architecture | `normalize_candidate()` is hard-coded in worker, not injectable. Swapping normalization requires modifying `worker.py`. | `worker.py:9` — `from .normalization import normalize_candidate` | C02.2C |
| M03 | **MEDIUM** | Architecture | Deduplication baked into worker (intra-job `seen_fingerprints` set + cross-job `has_prospect()`). Not independently testable. | `worker.py:60-70` — dedup logic inline in `execute_job` | C02.2C |
| M04 | **MEDIUM** | State Machine | No path to re-execute FAILED jobs. Manual status reset to QUEUED required but not exposed. | `worker.py:33-37` — `claim_queued_job` only claims QUEUED; FAILED jobs are permanently terminal | C02.2C |
| M05 | **MEDIUM** | Determinism | Fingerprint has no version tag. Algorithm changes silently invalidate old fingerprints. | `normalization.py:23` — `hashlib.sha256(f"{provider_name}\|{domain}".encode("utf-8"))` | C02.2C |
| M06 | **MEDIUM** | Domain | No PSL awareness. `london.dealer.co.uk` and `manchester.dealer.co.uk` are treated as different domains. May create duplicate ProspectPool records. | `normalization.py:40-54` — strips `www.` only; no TLD/suffix awareness | Deferred |
| M07 | **MEDIUM** | Concurrency | Cross-provider dedup is intentionally absent (identity keyed on `(provider, domain)`). Should be explicitly documented. | `worker.py:66-68` — `has_prospect(provider_name, normalized_domain)` scopes to single provider | Deferred |
| M08 | **MEDIUM** | Persistence | `AcquisitionStore` protocol returns untyped `Mapping[str, Any]`. No distinction between "not found", "not QUEUED", and "claim conflict". | `worker.py:16` — `-> Mapping[str, Any] \| None` | C02.2C |
| M09 | **MEDIUM** | Error Model | Flat `code: str` error classification. No subclasses for network/rate-limit/auth/quota/parse errors. | `models.py:49-56` — `ProviderError(code, safe_message, retryable)` | Real Provider |
| M10 | **MEDIUM** | Tests | All tests use `MemoryAcquisitionStore` which never fails. No test exercises persistence failure, partial writes, or unexpected exceptions. | `test_phase3c02_2b_acquisition_worker_core.py` — `MemoryAcquisitionStore` has no failure injection | C02.2C |
| M11 | **MEDIUM** | Tests | `has_prospect` implementation detail leaks into cross-job dedup test. Store checks `website == f"https://{normalized_domain}"` — a convention that may not match real adapter. | `test_phase3c02_2b_acquisition_worker_core.py:33-37` | C02.2C |
| L01 | **LOW** | Architecture | `DeterministicFakeProvider` exported from `__init__.py` — test-only class in public API. | `__init__.py:8` — `from .fake_provider import DeterministicFakeProvider` | Deferred |
| L02 | **LOW** | Domain | IPv4 addresses pass normalization (`192.168.1.1`). Not harmful but useless for dealer discovery. | `normalization.py:68` — regex accepts all-digit labels | Deferred |
| L03 | **LOW** | Domain | Source URL and domain are normalized independently. No cross-validation that source URL's domain relates to candidate domain. | `normalization.py:15-37` — `domain` and `source_url` normalized in separate calls | Deferred |
| L04 | **LOW** | Concurrency | Provider candidate ID is NOT part of dedup identity. Same domain with two different provider candidate IDs merges into one record. | `normalization.py:23` — fingerprint excludes `provider_candidate_id` | Deferred |
| L05 | **LOW** | Persistence | No `upsertProspect` / idempotent-create in protocol. Only `create_prospect`. Replay after partial write could duplicate. | `worker.py:22` — `create_prospect(values)` is insert-only | Deferred |

---

## 13. Required Fixes Before C02.2C

These must be resolved before or as the first step of Phase3C02.2C (Job Runner implementation). They do NOT require a Worker Core redesign.

### 13.1 BLOCKER-01: Generic Exception Handler

**Problem:** `worker.py:48` catches only `ProviderError`. If `create_prospect()`, `has_prospect()`, or `update_search_job()` raises any other exception (network error, validation error, EspoCRM REST error), the worker crashes. The job stays RUNNING with no error record.

**Minimum fix:**
```python
try:
    result = self._provider.search(request)
except ProviderError as error:
    # ... existing handler ...
except Exception as error:
    self._store.update_search_job(search_job_id, {
        "status": "FAILED",
        "completedAt": _now(),
        "errorMessage": f"Worker internal error: {type(error).__name__}",
        "failureReason": f"INTERNAL_ERROR; retryable=false",
    })
    return JobExecutionResult(search_job_id, "FAILED", True,
                              retryable=False, error_code="INTERNAL_ERROR")
```

### 13.2 BLOCKER-02: Write-Loop Transaction Boundary

**Problem:** `worker.py:72-93` calls `create_prospect()` in a loop, then `update_search_job("COMPLETED")` afterward. If `update_search_job` fails, prospects exist with job still RUNNING. If a mid-loop `create_prospect` fails, earlier prospects are already written.

**Minimum fix:** Wrap the loop in a try/except. On any persistence failure, mark the job FAILED with partial counts. Document that partial writes may leave orphaned prospects (acceptable for now; full idempotent replay handles this). Alternatively, collect all prospect dicts first, then write them, then update job status.

```python
# Collect first, then persist
to_create: list[dict[str, Any]] = []
for raw_candidate in result.candidates:
    candidate = normalize_candidate(result.provider_name, raw_candidate)
    if candidate is None:
        rejected += 1
        continue
    if candidate.dedupe_fingerprint in seen_fingerprints or self._store.has_prospect(...):
        duplicates += 1
        continue
    seen_fingerprints.add(candidate.dedupe_fingerprint)
    to_create.append({...})  # build prospect dict

# Persist prospects
for prospect_values in to_create:
    try:
        self._store.create_prospect(prospect_values)
        inserted += 1
    except Exception:
        rejected += 1
        # Log but continue

# Then update job status
self._store.update_search_job(search_job_id, {...})
```

### 13.3 BLOCKER-03: CAS/Version Parameter

**Problem:** The `AcquisitionStore` protocol has no version parameter for optimistic locking. The EspoCRM REST API uses `If-Match` headers. Without a version parameter, the adapter cannot implement atomic QUEUED→RUNNING claims.

**Minimum fix:** Add an optional `expected_version: str | None = None` parameter to `claim_queued_job` and `update_search_job`. Document that when provided, the adapter MUST use optimistic locking.

```python
class AcquisitionStore(Protocol):
    def claim_queued_job(self, job_id: str, started_at: str,
                         expected_version: str | None = None) -> Mapping[str, Any] | None: ...
    def update_search_job(self, job_id: str, values: Mapping[str, Any],
                          expected_version: str | None = None) -> None: ...
```

The EspoCRM adapter would read the entity's `versionNumber` field, pass it as `expected_version`, and use `If-Match: {versionNumber}` on the PATCH request.

---

## 14. Deferrable Improvements

| ID | Improvement | Defer To | Rationale |
|----|-------------|----------|-----------|
| H03 | IDN domain support | Real Provider | IDN dealers are rare in 3D printing. Safe failure mode (rejection). |
| M01 | Typed `SearchJob` domain model | C02.2C | Adds type safety. Can be done alongside adapter. |
| M02 | Injectable normalizer | C02.2C | Low risk; current normalizer is stable. |
| M03 | Injectable deduplicator | C02.2C | Low risk; current dedup logic is simple and correct. |
| M04 | FAILED→QUEUED reset path | C02.2C | Needed for Job Runner retry, not for single-run. |
| M05 | Fingerprint version tag | C02.2C | Add `v1:` prefix before any algorithm changes. |
| M06 | PSL awareness | Post-C02.2C | Requires new dependency or embedded suffix list. Not blocking. |
| M07 | Cross-provider dedup documentation | C02.2C | Document the design decision; implement merge later. |
| M09 | Error code subclasses | Real Provider | Flat codes work for deterministic fake. |
| M10 | Persistence failure tests | C02.2C | Add when P0 test gaps are filled. |
| L01-L05 | Various LOW items | Post-C02.2C | No correctness impact. |

---

## 15. Recommended Task Split

```
Phase3C02.2C — Job Runner
├── C02.2C.0 — Pre-flight fixes (BLOCKER-01, BLOCKER-02, BLOCKER-03)
│   Estimated: 1 session
│   - Add generic exception handler to worker
│   - Add write-loop transaction boundary
│   - Add CAS/version parameter to AcquisitionStore protocol
│
├── C02.2C.1 — SearchJob + ProspectPool typed models
│   Estimated: 1 session
│   - Mirror EspoCRM entity fields as Python StrEnum/dataclass
│   - Add state machine with transition table
│
├── C02.2C.2 — EspoCRM AcquisitionStore adapter
│   Estimated: 2-3 sessions
│   - Implement claim_queued_job with CAS via If-Match
│   - Implement create_prospect / has_prospect / update_search_job
│   - Add has_prospect_bulk(list[tuple]) for batch operations
│
├── C02.2C.3 — Single-job CLI runner
│   Estimated: 1 session
│   - argparse entry point: job-id → execute → print result
│   - Exit codes for monitoring
│
├── C02.2C.4 — Runtime validation
│   Estimated: 1 session
│   - End-to-end with real EspoCRM test instance
│   - Verify atomic claim, prospect write, status update
│   - Verify idempotent replay
│
└── C02.2C.5 — Test gap closure (P0 + P1)
    Estimated: 1-2 sessions
    - Persistence failure tests
    - Partial write tests
    - Unexpected exception tests
    - Contract tests for AcquisitionStore protocol
    - Domain normalization edge case tests
```

Total estimated: 7-9 sessions for complete C02.2C

---

## 16. Collision Check with Parallel Tasks

### 16.1 Phase3C02.1B — Git Commit Separation

| Risk | Status |
|------|--------|
| Both tasks touching acquisition files | ❌ No collision. Phase3C02.1B works on SearchStrategy/SearchJob/UI/ACL in the CRM extension. Phase3C02.2B acquisition files are in `chitu-connector/` — separate directory tree. |
| Staging/commit conflicts | ❌ No collision. This review task makes no changes. |
| File rename/move conflicts | ❌ No collision. No files moved. |

### 16.2 Phase3C02.2C-A — Job Runner Design Audit

| Risk | Status |
|------|--------|
| Both tasks reading acquisition files | ✅ Compatible. Both are read-only on these files. |
| Conflicting recommendations | ⚠️ Possible. The design audit may propose different fixes for the same issues. This report's findings should be shared with the design auditor. |
| Shared output location | ❌ No collision. This report writes to `docs/PHASE3C02_2B_WORKER_CORE_REVIEW.md`. The design audit writes to a different path. |

**Recommendation:** Share this review report with the Phase3C02.2C-A design auditor so both streams converge on the same blocker list before implementation begins.

---

## Appendix A: Reference — Existing espocrm_sync Patterns

For consistency, the acquisition package should follow patterns already established in `espocrm_sync/`:

| Pattern | espocrm_sync | acquisition (current) | Gap |
|---------|-------------|----------------------|-----|
| Models | Typed `@dataclass(frozen=True, slots=True)` | Same ✅ | No SearchJob model |
| Enums | `StrEnum` subclasses (`AuditStatus`, `MockSyncStatus`) | None ❌ | Status values are string literals |
| Time | `utc_now()` helper returning `datetime` | `_now()` helper returning ISO string | Format mismatch: `datetime` vs string |
| Protocol | Inject via constructor | Same ✅ | |
| Error | Exceptions propagate to caller | `ProviderError` caught; others unhandled | See BLOCKER-01 |

---

## Appendix B: File Encoding and Line Endings

All reviewed files:
- `__init__.py`: UTF-8, 30 lines
- `models.py`: UTF-8, 70 lines
- `provider.py`: UTF-8, 15 lines
- `fake_provider.py`: UTF-8, 50 lines
- `normalization.py`: UTF-8, 69 lines
- `worker.py`: UTF-8, 117 lines
- `test_phase3c02_2b_acquisition_worker_core.py`: UTF-8, 184 lines

No encoding issues detected. All files use `from __future__ import annotations` for PEP 604-style union types.

---

*End of review. No code was modified, committed, or executed against live systems.*
