# Phase3C20 WP2 Capability Registry Freeze

**Status:** Frozen
**Date:** 2026-07-29
**Commit:** `c898dc7c9964c186ab1ccd1dc26c27ff9acc311d`
**Phase:** Phase3C20 WP2 Extension — WP-C20-AUDIT-01
**Governing Reference:** `docs/PHASE3C20_OPEN_SOURCE_REFERENCE_DECISIONS.md`

---

## 1. Scope

The capability registry is a **deterministic, in-memory resolution component** in the
connector provider layer. It selects a single provider from CRM-authorized bindings
for a given `(capability, purpose)` pair.

### 1.1 Delivered

| File | Lines | Purpose |
|------|-------|---------|
| `chitu-connector/chitu_connector/acquisition/providers/registry.py` | 271 | `CapabilityRegistry` class, `ProviderBinding`, `CapabilityResolutionRequest`, `CapabilityResolutionResult`, `ProviderCandidateEvaluation`, `ProviderHealthState`, `AdapterRegistration` |
| `chitu-connector/tests/test_phase3c20_wp2_capability_registry.py` | 273 | 14 contract tests covering resolution, filtering, determinism, error taxonomy, credential safety, network isolation, duplicate rejection |

### 1.2 Explicitly NOT Delivered

- CRM-side PHP orchestration code
- `AIJob`, `AIRequestLog`, `PromptTemplate`, `AIQualificationInsight` entities
- `ProviderRoute` configuration UI or entity
- `ProviderHealth` entity or scheduled health checks
- Provider credential storage or resolution
- Any HTTP transport, provider SDK invocation, or network egress
- Scoring, ICP, qualification, or email-generation logic
- C21/C22 entities or workflows
- `ProviderRateLimit` entity or rate-limit enforcement

---

## 2. Contract

### 2.1 Input: `CapabilityResolutionRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capability` | `Capability` | Yes | SEARCH, ENRICHMENT, or COMPLETION |
| `purpose` | `str` | Yes | CRM-defined purpose within the capability |
| `allowed_provider_bindings` | `tuple[ProviderBinding, ...]` | Yes | CRM-authorized candidates; the registry may not select outside this set |
| `credential_availability` | `Mapping[str, bool]` | Yes | Per-credential-reference availability flag |
| `provider_health` | `Mapping[str, ProviderHealthState]` | Yes | Per-provider health state (input only; registry never probes) |
| `policy_version` | `str` | Yes | CRM policy version for provenance |
| `request_context` | `Mapping[str, Any]` | Yes | Opaque context; must not contain secret fields |

### 2.2 Output: `CapabilityResolutionResult`

| Field | Type | Description |
|-------|------|-------------|
| `requested_capability` | `Capability` | Echo of request |
| `purpose` | `str` | Echo of request |
| `selected_provider_id` | `str` | The resolved provider |
| `selected_adapter_type` | `str` | The adapter class name |
| `selected_credential_reference` | `str` | CRM credential reference (opaque, not a secret) |
| `policy_version` | `str` | Echo of request |
| `candidate_evaluations` | `tuple[ProviderCandidateEvaluation, ...]` | Full per-candidate evaluation trace |
| `fallback_occurred` | `bool` | True if a higher-precedence candidate was skipped or degraded |
| `resolution_reason` | `str` | Human-readable explanation |

### 2.3 Error Contract

All failures use the existing `ProviderError` type from `chitu_connector.acquisition.models`,
classified through `classify_provider_error()` from `taxonomy.py`. No parallel error type
exists.

| Error Code | Status | Retryable | Condition |
|------------|--------|-----------|-----------|
| `DUPLICATE_PROVIDER_ID` | 400 | No | Same `provider_id` registered twice |
| `DUPLICATE_PROVIDER_BINDING` | 400 | No | Same `provider_id` appears twice in request bindings |
| `INVALID_CAPABILITY` | 400 | No | Unknown capability value |
| `INVALID_RESOLUTION_REQUEST` | 400 | No | Empty purpose or policy version |
| `INVALID_PROVIDER_BINDING` | 400 | No | Malformed binding |
| `INVALID_PROVIDER_REGISTRATION` | 400 | No | Malformed adapter registration |
| `INVALID_PROVIDER_HEALTH` | 400 | No | Non-enum health value supplied |
| `SECRET_IN_RESOLUTION_INPUT` | 400 | No | Secret field detected in request_context |
| `CAPABILITY_UNAVAILABLE` | 503 | Yes | No eligible provider after filtering all candidates |

---

## 3. Boundary

### 3.1 Authority Chain

```
EspoCRM ProviderBinding / request policy
        │
        ▼
connector CapabilityRegistry.resolve()
        │  selects only from CRM-authorized bindings
        ▼
existing capability-port adapter (SearchProvider | EnrichmentProvider | CompletionProvider)
        │
        ▼
external provider (via injected HttpTransport — registry never touches this layer)
```

### 3.2 Registry Must NOT

- Discover, create, or persist provider configurations
- Select a provider outside the CRM-supplied `allowed_provider_bindings`
- Open an HTTP connection, construct a transport, or invoke a provider SDK
- Store, log, return, or accept secret values in any field
- Resolve, validate, or rotate credentials
- Perform health checks or probe provider endpoints
- Become a scoring, qualification, or lifecycle authority
- Create or mutate CRM entities

### 3.3 Registry May

- Accept `credential_availability: Mapping[str, bool]` as a pre-resolved input
- Accept `provider_health: Mapping[str, ProviderHealthState]` as a pre-evaluated input
- Return `selected_credential_reference: str` (an opaque CRM identifier, never a secret)
- Return a complete `candidate_evaluations` trace for audit and logging

### 3.4 Secret Field Detection

The following key patterns are forbidden in `request_context`:

`apiKey`, `apiSecret`, `token`, `password`, `plaintextCredential`, `encryptedSecret`,
`decryptedValue`, `credentialReference`

Detection is case-insensitive and strips non-alphanumeric characters before matching.
A request containing any of these patterns raises `SECRET_IN_RESOLUTION_INPUT`.

---

## 4. Test Evidence

### 4.1 Test Run

```
chitu-connector/tests/test_phase3c20_wp2_capability_registry.py - 14 passed
Full C20 suite (125 tests) - all passed
C20 boundary guards (19 tests) - all passed
C20 invariant registry (10 tests) - all passed
```

### 4.2 Coverage Matrix

| Test | Coverage |
|------|----------|
| `test_single_available_crm_authorized_provider_resolves` | Happy path, result shape |
| `test_resolution_is_deterministic_by_priority_then_provider_id` | Determinism, priority tiebreak |
| `test_disabled_provider_is_skipped` | `PROVIDER_DISABLED` gate |
| `test_unavailable_credential_is_skipped` | `CREDENTIAL_UNAVAILABLE` gate |
| `test_unhealthy_provider_is_skipped` | `PROVIDER_UNHEALTHY` gate |
| `test_healthy_provider_precedes_degraded_provider_and_audits_fallback` | DEGRADED → HEALTHY fallback, `fallback_occurred` audit |
| `test_no_available_provider_uses_existing_controlled_provider_error` | `CAPABILITY_UNAVAILABLE`, error taxonomy reuse |
| `test_registered_but_not_crm_authorized_provider_cannot_be_selected` | CRM authority boundary |
| `test_provider_without_requested_capability_cannot_be_selected` | `BINDING_CAPABILITY_UNSUPPORTED` gate |
| `test_duplicate_provider_registration_fails_closed` | `DUPLICATE_PROVIDER_ID`, fail-closed |
| `test_purpose_can_resolve_to_different_authorized_provider` | Purpose-differentiated routing |
| `test_result_and_evaluations_expose_only_safe_registry_metadata` | Secret rejection, result field audit |
| `test_registry_has_no_network_transport_or_adapter_invocation_surface` | Zero network imports (source-code inspection) |
| `test_duplicate_binding_and_unknown_health_are_rejected_or_skipped_safely` | `DUPLICATE_PROVIDER_BINDING`, `PROVIDER_HEALTH_UNKNOWN` |

---

## 5. Known Non-Blocking Improvements

| # | Finding | Severity |
|---|---|---|
| R1 | `ADAPTER_TYPE_MISMATCH` skip reason has no dedicated contract test | Low — covered by type system; explicit test would improve coverage |
| R2 | Purpose values (`"discovery"`, `"research"`) are free-form strings with no enumerated taxonomy | Low — CRM owns purpose definitions; enumeration belongs in CRM policy, not connector |
| R3 | `credential_availability` absent-key behavior (defaults to unavailable) is correct but implicit | Low — behavior is tested; docstring could be more explicit |

None of these block freeze. All are documented for future WP iterations.

---

## 6. Open Source Attribution

| Aspect | Record |
|--------|-------|
| Conceptual reference | YALC `src/lib/providers/capabilities.ts` at commit `ffc6e37` (MIT) |
| Borrowing type | Independent Python reimplementation; no external source file, code fragment, or license notice copied |
| Design concepts adapted | Priority-based resolution, candidate evaluation with skip reasons, deterministic fallback |
| Design concepts NOT copied | Filesystem provider discovery, MCP config loading, async provider invocation, TypeScript runtime architecture |
| Attribution | Recorded in `docs/PHASE3C20_OPEN_SOURCE_REFERENCE_DECISIONS.md` §"Licensing and Code-Borrowing Decision" |
| Compliance | MIT source → MIT-compatible independent implementation. No attribution notice required in source files. |

---

## 7. Decision

**The WP2 Capability Registry is frozen at `c898dc7`.**

No ADR amendment is required. The implementation satisfies ADR-C20 §4.1 (capability ports),
§4.2.7 (routing as configuration), and §4.3 (normalized error taxonomy) without modifying
any invariant.

The registry is ready for WP3 consumption. `CapabilityResolutionResult` carries
`selected_provider_id`, `selected_credential_reference`, `candidate_evaluations`,
`fallback_occurred`, `resolution_reason`, and `policy_version` — sufficient for
`AIJob` dispatch and `AIRequestLog` provenance recording.

---

*Frozen 2026-07-29. Commit `c898dc7`. No further WP2 registry changes without a new decision record.*
