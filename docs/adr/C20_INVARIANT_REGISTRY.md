# C20 Invariant Registry

**Status:** Active (WP0.2 governance artifact)  
**Date:** 2026-07-28  
**Phase:** Phase3C20 — AI Infrastructure Foundation  
**Source ADR:** `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` §8  
**Governance marker:** `adr-c20-aiplatform-v1`

This registry is the machine-checkable index of all twenty-two ADR-C20 contract
invariants. It does **not** authorize AIPlatform implementation. Runtime, PHP,
metadata, and provider work remain gated by later WPs and §11.1 ratification.

---

## Machine-readable table

Columns (strict order):

1. `id` — `C20-INV-NN` (01–22), unique
2. `description` — short invariant statement
3. `status` — `ACTIVE` or `DEFERRED`
4. `owning_wp` — `WP0` … `WP5`
5. `test_file` — repo-relative path; required and must exist when `status=ACTIVE`;
   `-` allowed when `status=DEFERRED`
6. `activation_trigger` — when the invariant becomes enforceable / moves to ACTIVE

| id | description | status | owning_wp | test_file | activation_trigger |
| --- | --- | --- | --- | --- | --- |
| C20-INV-01 | Marker `adr-c20-aiplatform-v1` present in AI Platform metadata and contract tests | DEFERRED | WP1 | - | AIPlatform metadata and marker-bearing contract tests land |
| C20-INV-02 | No prospecting identifier (`Lead`, `ProspectPool`, `SearchJob`, `DraftApproval`, `SendExecution`, `ReplyEvent`, `Quote`) appears in `Modules/AIPlatform` | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence gate; remains ACTIVE when AIPlatform lands under WP1 |
| C20-INV-03 | No outbound HTTP from PHP to provider domains (`curl`, `file_get_contents`, Guzzle, sockets) | DEFERRED | WP1 | - | AIPlatform PHP module skeleton lands |
| C20-INV-04 | No plaintext credential in API responses, logs, or exceptions; credential fields write-only | DEFERRED | WP1 | - | `ProviderCredential` custody surface lands |
| C20-INV-05 | Every `AIJob` status write passes through `AIJobService` with authorized save option; hook guard rejects direct mutation | DEFERRED | WP3 | - | `AIJob` + `AIJobService` + mutation guard land |
| C20-INV-06 | `AIJob` transitions limited to §7.2 matrix; `SUCCEEDED`/`CANCELLED` terminal; `CANCELLED` requires reason | DEFERRED | WP3 | - | `AIJob` lifecycle implementation lands |
| C20-INV-07 | `AIRequestLog` is append-only — no update or delete path for any role | DEFERRED | WP3 | - | `AIRequestLog` entity and guards land |
| C20-INV-08 | Every completed provider invocation produces exactly one `AIRequestLog` with provider, model, tokens, cost, latency, prompt version | DEFERRED | WP3 | - | Cost-accounting request log path lands |
| C20-INV-09 | `PromptTemplate` version referenced by any `AIRequestLog` cannot be edited — only superseded | DEFERRED | WP3 | - | `PromptTemplate` versioning lands |
| C20-INV-10 | Retry eligibility solely by §4.3 taxonomy; `AUTH`, `VALIDATION`, `QUOTA`, `CONTENT_FILTER` never auto-retry | DEFERRED | WP3 | - | `AIJob` retry strategy lands |
| C20-INV-11 | Idempotency key persisted before dispatch and identical across retries of the same logical invocation | DEFERRED | WP3 | - | Dispatch + idempotency persistence lands |
| C20-INV-12 | No adapter constructed without explicit transport; no default transport exists | DEFERRED | WP2 | - | Capability ports / provider adapters land (§11.1 gated) |
| C20-INV-13 | Dry-run mode produces complete `AIJob` + `AIRequestLog` trace with zero network egress | DEFERRED | WP2 | - | Fixture-backed dry-run path lands |
| C20-INV-14 | EspoCRM computes no score; no `AIScore` entity; scores persisted from Chitu with provenance only | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence gate; Chitu remains canonical_score owner |
| C20-INV-15 | C20 ships no email-sending path — no `EmailDeliveryProvider`, no send action, no `SendExecution` write from `AIPlatform` | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence gate; delivery remains C21+ |
| C20-INV-16 | `AIQualificationInsight` is advisory only — must not set/update/compete with `canonical_score`, replace Chitu qualification, or mutate Prospecting lifecycle | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence/governance gate; entity work later |
| C20-INV-17 | `AIQualificationInsight` has no lifecycle ownership — no status field, transition matrix, or owning transition service | DEFERRED | WP3 | - | `AIQualificationInsight` entity definition lands |
| C20-INV-18 | No transition service may read `AIQualificationInsight` to drive state changes | DEFERRED | WP3 | - | Insight entity + transition-service contract tests land |
| C20-INV-19 | No write path to `canonical_score` from `AIQualificationInsight`, `AIPlatform`, or any C20 advisory surface | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence gate |
| C20-INV-20 | Entire `AIQualificationInsight` immutable after create; supersession ordering; mutable `isCurrent` forbidden | DEFERRED | WP3 | - | `AIQualificationInsight` persistence lands |
| C20-INV-21 | EspoCRM must not calculate qualification verdicts from `canonical_score`, `AIQualificationInsight`, or confidence; no C20 surface may become qualification decision authority | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence/governance gate |
| C20-INV-22 | `AIQualificationInsight` must not be used as PrimaryFilter authority or lifecycle queue authority | ACTIVE | WP0 | crm-extension/tests/test_phase3c20_wp0_invariant_registry.py | WP0 absence/governance gate |

---

## Counts

| Metric | Value |
| --- | --- |
| Total invariants | 22 |
| ACTIVE | 7 |
| DEFERRED | 15 |
| ACTIVE + DEFERRED | 22 |

---

## Status rules

| Rule | Enforcement |
| --- | --- |
| Every id `C20-INV-01` … `C20-INV-22` appears exactly once | Registry contract test |
| `ACTIVE` + `DEFERRED` = 22 | Registry contract test |
| `DEFERRED` rows have non-empty `owning_wp` | Registry contract test |
| `ACTIVE` rows reference an existing `test_file` | Registry contract test |
| No AIPlatform implementation authorized by this registry alone | WP0 scope boundary |

---

## Related

- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `crm-extension/tests/test_phase3c20_wp0_invariant_registry.py`
