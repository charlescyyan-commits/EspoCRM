# Phase3C20 WP2 Capability Registry Freeze

**Status:** FROZEN

**Date:** 2026-07-29

**Implementation baseline:** `c898dc7c9964c186ab1ccd1dc26c27ff9acc311d`
(*feat(c20): add controlled capability registry resolution*)

**Open-source reference freeze:** `b110f2d8e92c890e346490eac4f862f1c7745f9d`
(*docs(c20): freeze open-source reference decisions*)

**Governing references:**
`docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`,
`docs/PHASE3C20_WP2_CHARTER.md`,
`docs/PHASE3C20_OPEN_SOURCE_REFERENCE_DECISIONS.md`

---

## 1. Purpose

WP2 delivers the C20 AI Platform **Capability Resolution Layer**.

The frozen contract is the **Capability Registry Resolution Contract**. It is the
foundation for later WP3 / provider work:

- `AIJob`
- `AIRequestLog`
- `CompletionProvider`
- `SearchProvider`
- `EnrichmentProvider`

Goals:

| Goal | Meaning |
| --- | --- |
| Provider replaceability | Adapters are selected by CRM policy bindings, not hardcoded callers |
| Auditable selection | Every resolution returns a complete non-secret candidate evaluation trace |
| CRM-controlled authority | Allowed providers, credentials references, and policy versions originate in EspoCRM |
| Connector non-authority | The connector resolves among CRM-authorized candidates only; it does not own business decisions |

This freeze records the contract. It does not authorize WP3 entity implementation.

---

## 2. Scope

### 2.1 Delivered

| Deliverable | Record |
| --- | --- |
| `CapabilityResolutionRequest` | Frozen request shape |
| `CapabilityResolutionResult` | Frozen result / audit shape |
| Provider candidate evaluation | Per-candidate eligibility and skip reasons |
| Deterministic selection | Stable ranking across identical inputs |
| Fallback reasoning | `fallback_occurred` + `resolution_reason` |
| Safe metadata output | Opaque credential references only; no secrets |
| Error taxonomy reuse | Existing `ProviderError` / BridgeError classification path |

Implementation surface (evidence, not change scope for this document):

| File | Role |
| --- | --- |
| `chitu-connector/chitu_connector/acquisition/providers/registry.py` | Registry types and resolver |
| `chitu-connector/tests/test_phase3c20_wp2_capability_registry.py` | Registry contract tests |

### 2.2 Explicitly NOT Delivered

WP2 Capability Registry does **not** include:

- `AIJob`
- `AIRequestLog`
- `PromptTemplate`
- `ProspectCandidate`
- `QualificationInsight` / `AIQualificationInsight`
- `CandidateScore` / `AIScore`
- Email sending
- Lifecycle transition
- Automation

Also excluded: CRM-side PHP orchestration, provider discovery, secret storage,
HTTP execution inside the registry, and C21/C22 workflows.

---

## 3. Contract

### 3.1 Request — `CapabilityResolutionRequest`

| Field | Requirement |
| --- | --- |
| `capability` | Required. Capability under resolution (SEARCH / ENRICHMENT / COMPLETION). |
| `purpose` | Required. CRM-defined purpose within the capability. |
| `allowed_provider_bindings` | Required. CRM-authorized candidate set. Registry may not select outside it. |
| `credential_availability` | Required. Per-credential-reference availability flags. |
| `provider_health` | Required. Per-provider health input. Registry never probes health. |
| `policy_version` | Required. CRM policy version for provenance. |
| `request_context` | Required. Opaque context. Must not contain secret fields. |

Binding constraints:

- Credential fields may carry **reference / status only**.
- Secrets are forbidden in request input.
- Allowed providers **must originate from CRM** (`ProviderBinding` / request policy).

### 3.2 Result — `CapabilityResolutionResult`

| Field | Requirement |
| --- | --- |
| `requested_capability` | Echo of request |
| `purpose` | Echo of request |
| `selected_provider_id` | Resolved provider id |
| `selected_adapter_type` | Selected adapter type |
| `selected_credential_reference` | Opaque CRM credential reference (never a secret) |
| `candidate_evaluations` | Full per-candidate evaluation trace |
| `fallback_occurred` | True when a higher-precedence candidate was skipped or degraded |
| `resolution_reason` | Human-readable resolution explanation |
| `policy_version` | Echo of request |

**Result semantics:** the result is **audit information**. It is not a business
decision, qualification verdict, score, or lifecycle authorization.

---

## 4. Resolution Algorithm

### 4.1 Flow

```text
CRM ProviderBinding
        ↓
CapabilityResolutionRequest
        ↓
Candidate Evaluation
        ↓
Eligibility Filtering
        ↓
Deterministic Ranking
        ↓
CapabilityResolutionResult
```

### 4.2 Eligibility filtering

Candidates are filtered / skipped when any of the following apply:

| Filter | Typical skip reason |
| --- | --- |
| Disabled provider | `PROVIDER_DISABLED` |
| Unsupported capability | `BINDING_CAPABILITY_UNSUPPORTED` / `ADAPTER_CAPABILITY_UNSUPPORTED` |
| Unsupported purpose | `PURPOSE_NOT_ALLOWED` |
| Credential unavailable | `MISSING_CREDENTIAL_REFERENCE` / `CREDENTIAL_UNAVAILABLE` |
| Unhealthy / unknown health | `PROVIDER_UNHEALTHY` / `PROVIDER_HEALTH_UNKNOWN` |
| Adapter not registered / type mismatch | `ADAPTER_NOT_REGISTERED` / `ADAPTER_TYPE_MISMATCH` |

If no eligible candidate remains, resolution fails closed with controlled
`CAPABILITY_UNAVAILABLE`.

### 4.3 Deterministic selection rules

Eligible candidates are ranked deterministically by:

1. **health** (HEALTHY preferred over DEGRADED)
2. **priority** (lower numeric priority wins)
3. **provider_id** (stable tie-break)

Identical inputs produce identical outputs. Fallback is recorded when the
selected provider is not the first candidate in the evaluation order.

---

## 5. Authority Boundary

### 5.1 EspoCRM Authority

EspoCRM owns:

- `ProviderBinding`
- Credential reference metadata
- ACL
- Policy / `policy_version`
- Business workflow and lifecycle authority

### 5.2 Connector Authority

The connector owns only:

- Capability resolution among CRM-authorized bindings
- Adapter invocation (outside this registry component; via injected transport)

The connector does **not** own:

- Provider discovery
- Credential ownership / secret custody
- Business decisions
- Lifecycle ownership

### 5.3 External Provider

External providers are responsible for:

- AI execution
- Search
- Enrichment
- Completion

### 5.4 Connector MUST NOT

- Bypass CRM provider binding
- Discover providers
- Store secrets
- Modify CRM lifecycle
- Calculate qualification / scores

---

## 6. Security Constraints

Mandatory:

| Constraint | Requirement |
| --- | --- |
| No secret storage | Registry stores no credentials or tokens |
| No HTTP execution inside registry | No transport construction, SDK call, or network I/O |
| No environment lookup | No env-based secret or provider discovery |
| No credential materialization | Only opaque references and availability booleans |
| No unsafe logging | Result / evaluations expose safe metadata only |

Secret-bearing keys in `request_context` are rejected (`SECRET_IN_RESOLUTION_INPUT`).

---

## 7. Error Handling

Reuse existing:

- `ProviderError`
- BridgeError / provider error taxonomy classification

**Do not** introduce a parallel error system for capability resolution.

Recorded failure classes include:

| Condition | Controlled outcome |
| --- | --- |
| No provider available | `CAPABILITY_UNAVAILABLE` |
| Credential unavailable | Candidate skip / may yield unavailable |
| Unsupported capability | Candidate skip / request validation |
| Duplicate registration | `DUPLICATE_PROVIDER_ID` |
| Duplicate binding | `DUPLICATE_PROVIDER_BINDING` |
| Provider unavailable / unhealthy | Candidate skip |
| Secret in input | `SECRET_IN_RESOLUTION_INPUT` |

---

## 8. Testing Evidence

Recorded evidence at freeze:

| Suite | Result |
| --- | --- |
| Capability Registry | **14 passed** |
| C20 WP2 | **92 passed** |
| Connector | **404 passed** |
| Boundary | **25 passed**, **4 subtests** |
| Root | **597 passed**, **3 authorized baseline artifact failures** |

The three root artifact failures are **authorized baseline** release-integrity
failures and are **unrelated to WP2** capability-registry work. They do not
block this freeze.

---

## 9. Deferred Items

Post-freeze (non-blocking):

| Item | Notes |
| --- | --- |
| Adapter mismatch dedicated test | `ADAPTER_TYPE_MISMATCH` covered by types; dedicated test deferred |
| Purpose taxonomy documentation | Purpose strings remain CRM-owned; enumeration deferred |
| Credential availability documentation | Absent-key → unavailable behavior is tested; docs refinement deferred |

These are **not blockers**.

---

## 10. Open Source Attribution

| Reference | Record |
| --- | --- |
| **YALC** | Inspiration / reference only. No code copied. License boundary respected. |
| **OpenOutreach** | GPLv3. Design reference only. No code copied. |

Full licensing and borrowing decisions:
`docs/PHASE3C20_OPEN_SOURCE_REFERENCE_DECISIONS.md`.

---

## 11. Freeze Decision

```text
WP2 Capability Registry Status:

FROZEN

ADR-C20 amendment:

Not required
```

Rationale: the registry implements ADR-C20 capability-port routing and
normalized error taxonomy without amending ADR invariants. It is ready for
WP3 consumption as the resolution foundation under `AIJob` / `AIRequestLog`
provenance — without authorizing WP3 implementation in this document.

---

*Frozen 2026-07-29 at implementation baseline `c898dc7`. Documentation-only
freeze record. No PHP, metadata, connector runtime, test, or artifact changes
are made by this document.*
