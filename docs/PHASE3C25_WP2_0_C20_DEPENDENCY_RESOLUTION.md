# Phase3C25 WP2.0 — C20 Dependency Resolution Decision Package

| Field | Value |
| --- | --- |
| Document Type | Governance Decision Package (documentation only) |
| Work Package | WP2.0 — C20 Dependency Resolution |
| Parent | Phase3C25 WP2 — AI Commercial Brief |
| Status | COMPLETE — historical NO GO superseded for foundation consumption; **foundation gate satisfied** |
| Date | 2026-08-01 |
| Governing charter | `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (RATIFIED) |
| Governing plan | `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` (RATIFIED WITH NON-BLOCKING NOTES) |
| Implementation Authorization | **NO** — this package authorizes no code, no entity, no metadata, no scope, no ACL, no controller, no route, no migration, no test, no C20 change, no ProviderRoute, no commit, no push, no tag |

> **Amendment record (2026-08-06):** Status and §1 updated to reflect the C20
> Dependency Closure Amendment ratified at `b632f1d` (foundation gate =
> Capability identity + Purpose policy + Boundary evidence; C20-INV-05…11
> remain DEFERRED). Original package authored 2026-08-01. Historical WP2.2
> records (`PHASE3C25_WP2_2_*`) are **HISTORICAL / SUPERSEDED** and do not
> change the state asserted here: WP2 implementation remains **NOT
> AUTHORIZED**. See
> `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md`.
>
> **Amendment record (2026-08-06) — WP2.1B Implementation Authorization
> issued:** `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md` grants
> WP2.1B implementation **AUTHORIZED WITH CONDITIONS**, consuming the
> foundation gate satisfied by this package (Capability identity + Purpose
> policy + Boundary evidence). WP2.2 / WP2.3 and WP2 generation remain **NOT
> AUTHORIZED**.

---

## 1. Executive Verdict

**Historical NO GO — superseded for C25 WP2 foundation consumption.**

This package recorded the pre-ratification evaluation of the three C20
governance dependencies against the frozen C20 contracts and the **live**
repository implementation. The C20 Dependency Closure Amendment was later
ratified at `b632f1d`, and the closure addendum approved the result for C25
WP2.0 consumption.

The current WP2 foundation gate is:

**Capability identity + Purpose policy + Boundary evidence**

The gate is satisfied for foundation review. C20-INV-05…11 remain formally
DEFERRED runtime maturity items; no invariant activation is required for this
foundation gate and no runtime implementation is authorized.

WP2.1A may proceed as a separate governance-only package. WP2
implementation remains **NOT AUTHORIZED**; generation runtime, provider call,
and deployment are not authorized.

| # | Required decision | Answer |
| --- | --- | --- |
| 1 | Does CommercialBrief require its own CompletionCapability? | **Yes** — a dedicated capability is required (Accepted; §4) |
| 2 | Is the capability name only a proposal? | **Yes** — `COMMERCIAL_BRIEF` is proposed-only; C20 ratifies (§4.3) |
| 3 | Can CommercialBrief choose providers? | **No** (§5.3) |
| 4 | Can CommercialBrief choose models? | **No** (§5.3) |
| 5 | Can CommercialBrief own ProviderBinding? | **No** (§5.3) |
| 6 | Can CommercialBrief own routing? | **No** (§5.3) |
| 7 | Can CommercialBrief invoke the Connector directly? | **No** (§5.3) |
| 8 | Which purposes are allowed? | `commercial_brief_generation` (proposed; WP2-required); `commercial_summary` / `commercial_analysis` admissible in principle, not requested (§6). Capability candidate remains `COMMERCIAL_BRIEF` (§4) |
| 9 | Which purposes are forbidden? | `OUTREACH`, `EXECUTION`, `CRM_WRITE`, `LEAD_CREATE`, `OPPORTUNITY_CREATE`, `QUALIFICATION`, `PIPELINE_MUTATION` (§6) |
| 10 | Are INV-05 through INV-11 required for the WP2 foundation gate? | **No.** They remain deferred runtime maturity items. The foundation gate is capability identity + purpose policy + boundary evidence (§7) |
| 11 | Does anything still require C20 governance? | **Yes, for runtime maturity only** — invariant activation, runtime expansion, and provider execution remain outside this foundation closure |
| 12 | Can WP2.1A start? | **Yes, as a separate governance-only package**; implementation remains unauthorized |
| 13 | Can any implementation start? | **No** (§9) |

---

## 2. Governing Sources

| Source | Role |
| --- | --- |
| `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` | Ratified WP2 charter — §10 C20 dependency verdict, §27 authorization boundary |
| `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` | Ratified WP2 plan — §7 (D-1/D-2/D-3), §22 (WP2.0 scope), §35 (open items) |
| `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md` | Frozen Capability Registry Resolution contract (`CapabilityResolutionRequest`/`Result`, `allowed_provider_bindings`, `PURPOSE_NOT_ALLOWED`) |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | Ratified completion capability portfolio scope (4 values, frozen) |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | C20 architecture — ProviderRoute model, AIJob lifecycle, error taxonomy, invariants §8 |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | C20-INV-05…11 — all DEFERRED (registry remains the status authority) |

**Live implementation verified** (primary evidence; archived trees not used):

- `chitu-connector/chitu_connector/acquisition/providers/completion/base.py` — `CompletionCapability` enum
- `chitu-connector/chitu_connector/acquisition/providers/completion/adapter.py` — capability semantics (`_SYSTEM_PROMPTS`)
- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py` — resolution-level `Capability` enum
- `chitu-connector/chitu_connector/acquisition/providers/registry.py` — `ProviderBinding`, `CapabilityRegistry.resolve()`, purpose filter
- `chitu-connector/chitu_connector/acquisition/providers/taxonomy.py` — retryable error classes
- `crm-extension/files/custom/Espo/Modules/AIPlatform/` — `entityDefs/{AIJob,AIRequestLog,PromptTemplate,ProviderCredential}.json`, `Services/AIJobService.php`, `Services/AIJobStatusMutationSaveOption.php`, `Hooks/AIJob/AIJobStatusMutationGuard.php`, `Services/AIRequestLogService.php`, `Hooks/AIRequestLog/AIRequestLogAppendOnlyGuard.php`, `Services/PromptTemplateService.php`, `Hooks/PromptTemplate/PromptTemplateMutationGuard.php`, `Binding.php`

---

## 3. Dependency Scope

The ratified WP2 Plan (§7.1) fixes exactly three C20-governed readiness
dependencies. This package evaluates them and nothing else:

| Plan ref | Dependency | Package section |
| --- | --- | --- |
| D-1 | Completion capability portfolio decision | §4 |
| D-2 | Provider binding / allowed-provider-binding surface (incl. brief-purpose registration) | §5, §6 |
| D-3 | Runtime invariant activation and verification — superseded for the WP2 foundation gate | §7 |
| — | Go / No-Go gate (Plan §7.3 deliverable) | §8 |

Out of scope (all forbidden): CommercialBrief entity/fields/metadata/routes/
controller/services/guards/save options/migrations/tests, workspace, UI,
prompts, model selection, provider runtime, scheduler, audit, review
lifecycle, presentation, and any implementation.

---

## 4. Completion Capability Decision

### 4.1 Evaluation against the ratified portfolio

The ratified portfolio is exactly four values — the connector enum documents
itself as *"The exhaustive, ratified CompletionProvider capability
portfolio"* (`completion/base.py`):

```python
class CompletionCapability(Enum):
    RESEARCH_EVIDENCE = "research_evidence"
    QUALIFICATION_INSIGHT = "qualification_insight"
    DRAFT_ASSISTANCE = "draft_assistance"
    REPLY_ASSISTANCE = "reply_assistance"
```

| Existing capability | Live semantics (`_SYSTEM_PROMPTS`, adapter.py) | Covers brief generation? |
| --- | --- | --- |
| `RESEARCH_EVIDENCE` | "Summarize and structure the provided evidence…" | **No** — evidence summarization, not a governed commercial review artifact |
| `QUALIFICATION_INSIGHT` | "Provide contextual intelligence for operator review only…" | **No** — qualification-context output; qualification authority belongs to Chitu (C20-INV-14/16/21) |
| `DRAFT_ASSISTANCE` | "Generate proposed text for operator review. The operator decides whether to use the output…" | **No** — nearest, but semantically and governancely distinct (§4.2) |
| `REPLY_ASSISTANCE` | "Provide advisory classification, sentiment, and suggested categorization…" | **No** — reply triage support, not brief generation |

### 4.2 Why DRAFT_ASSISTANCE cannot be reused

- Its live contract produces **transient** proposed text — `complete()`
  performs one transport POST and returns a value object; **nothing is
  persisted** and **no review lifecycle exists in code**.
- CommercialBrief is the opposite shape: a **persisted, immutable
  projection** with mandatory C20 provenance and a human-review lifecycle
  (`GENERATED → REVIEWED → ACCEPTED | DISMISSED`).
- Reusing `DRAFT_ASSISTANCE` would overload the portfolio and pollute its
  provenance semantics (ratified charter §10.3.1): cost, idempotency, and
  audit attribution for two governancely different artifacts would share one
  capability identity.

### 4.3 Decision

```text
Decision:  ACCEPTED — CommercialBrief requires a dedicated CompletionCapability
Name:      COMMERCIAL_BRIEF — PROPOSED ONLY
Ratifier:  C20 governance (amendment to the capability scope document +
           connector CompletionCapability enum + contract change)
```

Four-layer naming used by this package (related, not interchangeable):

| Layer | Canonical identifier |
| --- | --- |
| Completion capability candidate | `COMMERCIAL_BRIEF` |
| Provider-binding purpose ID | `commercial_brief_generation` |
| Domain artifact / entity | `CommercialBrief` |
| Capability Registry family | `Capability.COMPLETION` |

```text
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

C25 proposes and consumes; it does **not** ratify C20 capability names,
purpose IDs, granularity, or portfolio placement (charter §10.3.1, §10.4).
The resolution-level capability family already exists
(`Capability.COMPLETION` in `capabilities.py`; `AIJob.capability` accepts
`COMPLETION` in live entityDefs) — the gap is solely the portfolio value
within the COMPLETION family, plus separate purpose registration.

---

## 5. Provider Binding Decision

### 5.1 Governance contract (no runtime designed here)

```text
Completion Capability candidate (proposed COMMERCIAL_BRIEF)
        + Capability.COMPLETION registry family
        + purpose ID (proposed commercial_brief_generation)
        ↓
Binding Eligibility — binding.supported_capabilities ∋ COMPLETION,
                      binding.enabled, binding.health_state
        ↓
allowed_provider_bindings — the CRM-authorized candidate set carried in
                            CapabilityResolutionRequest; the registry
                            resolves ONLY over this set
        ↓
Provider Binding — connector-side ProviderBinding: provider_id,
                   adapter_type, priority, enabled, credential_reference,
                   supported_capabilities, health_state, allowed_purposes
                   (must list commercial_brief_generation when delivered)
        ↓
Connector — adapter invocation (C20 sole egress; C20 runtime boundary)
```

Live contract facts (registry.py, frozen G12):

- `CapabilityResolutionRequest.allowed_provider_bindings` is the
  CRM-authorized candidate collection; `resolve()` iterates only over it —
  *"This registry deliberately does not discover providers, resolve
  credentials, construct transports, or invoke adapters."*
- Purpose eligibility is enforced per binding:
  `if request.purpose not in binding.allowed_purposes: return "PURPOSE_NOT_ALLOWED"`.
- The result (`CapabilityResolutionResult`) is audit information, not a
  business decision.

### 5.2 CRM-side binding surface — absent today

- No `entityDefs/ProviderRoute.json` or `entityDefs/ProviderBinding.json`
  exists anywhere under `crm-extension/` (verified). The only provider
  entityDef is `ProviderCredential.json`.
- `AIPlatform/Binding.php` is an empty DI-container binding processor (a
  module namespace marker), **not** a ProviderBinding entity.
- The ProviderRoute configuration UI is deferred to C20 WP3 (G13 §9.2).

### 5.3 Decision

CommercialBrief depends **only** on the C20 binding contract. It supplies
`(capability, purpose, structured context, idempotencyKey, initiating_user)`
to the C20 capability interface and consumes the outcome through the C20
`AIJob` lifecycle. CommercialBrief:

- never selects a provider directly;
- never selects a model;
- never owns `ProviderBinding` (or its database/UI form — C20 decides);
- never owns routing;
- never owns dispatch;
- never reads credentials;
- never invokes the Connector directly.

C20 must deliver the CRM-side binding surface and register the C25 brief
purpose ID `commercial_brief_generation` in binding-level
`allowed_purposes` before any C25 generation can route (Plan D-2).

---

## 6. Purpose Eligibility Matrix

Purposes are routing-binding keys evaluated against
`binding.allowed_purposes`. They are **not** `CompletionCapability` enum
members.

| Layer | Canonical identifier |
| --- | --- |
| Capability candidate | `COMMERCIAL_BRIEF` (proposed; see §4) |
| Provider-binding purpose ID | `commercial_brief_generation` (proposed; WP2-required) |

```text
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

Do not use `COMMERCIAL_BRIEF` as an `allowed_purposes` value.

Do not treat `commercial_brief_generation` as a current
`CompletionCapability` enum member.

Names below are purpose-ID proposals for C20 registration; only
`commercial_brief_generation` is required by WP2. C25 may consume these
proposed identifiers but must not ratify them. No ProviderBinding currently
authorizes the purpose. Neither identifier is active.

| Purpose ID | Eligibility | Rationale |
| --- | --- | --- |
| `commercial_brief_generation` | **PERMITTED (proposed; WP2-required)** | Binding-purpose key for brief generation; advisory, read-only, human-gated; corresponds to—but is not identical to—capability candidate `COMMERCIAL_BRIEF` |
| `commercial_summary` | Permitted in principle (not required; not requested) | Same advisory category; C20 may register if a coarser purpose is preferred |
| `commercial_analysis` | Permitted in principle (not required; not requested) | Same advisory category |
| `OUTREACH` | **FORBIDDEN** | C22 owns outreach execution; C25 data must not appear at ActionGate (C22-INV-EX-001) |
| `EXECUTION` | **FORBIDDEN** | Execution authority is C22's; C25 has no write/send/trigger tools (C25-INV-SEC-001) |
| `CRM_WRITE` | **FORBIDDEN** | CRM Core mutation forbidden (C22-INV-CRM-001; ADR-C25-005 §3.6) |
| `LEAD_CREATE` | **FORBIDDEN** | CRM Core Lead creation is outside C25 (C22-INV-CRM-001) |
| `OPPORTUNITY_CREATE` | **FORBIDDEN** | CRM Core Opportunity ownership (C24-INV-REV-003) |
| `QUALIFICATION` | **FORBIDDEN** | Chitu owns qualification/scoring (C20-INV-14/16/21) |
| `PIPELINE_MUTATION` | **FORBIDDEN** | C24 owns pipeline lifecycle (C24-INV-SEP-002, C24-INV-LIFE-001) |

Forbidden purposes are additionally rejected by structure, not convention:
C25 holds no write/send/trigger path, so a forbidden purpose has no
executable meaning in C25.

---

## 7. INV Readiness Matrix

Registry status authority: `docs/adr/C20_INVARIANT_REGISTRY.md` — all seven
are **DEFERRED**. No invariant is redefined or reworded here. Live-code
evidence assessed per invariant:

| INV | Rule (summary) | Registry | Live-code evidence | Verdict |
| --- | --- | --- | --- | --- |
| C20-INV-05 | AIJob status writes only via `AIJobService` + save option; hook guard rejects direct mutation | DEFERRED | `AIJobService::create()/transition()` save with `AIJobStatusMutationSaveOption` token; guard throws `Forbidden('AIJob lifecycle fields may only be written by AIJobService.')`; create initializes QUEUED/zero attempts | **NOT READY** (code present; activation + verification pending) |
| C20-INV-06 | Transitions limited to §7.2 matrix; SUCCEEDED/CANCELLED terminal; CANCELLED requires reason | DEFERRED | `VALID_TRANSITIONS` exact (QUEUED→RUNNING/CANCELLED; RUNNING→SUCCEEDED/FAILED/CANCELLED; FAILED→QUEUED; both terminals empty). **Cancel-reason missing**: no `cancelReason` field in entityDefs, `transition()` takes no reason | **REQUIRES C20 CHANGE** (cancel-reason field + enforcement), then NOT READY |
| C20-INV-07 | AIRequestLog append-only — no update/delete for any role | DEFERRED | `AIRequestLogAppendOnlyGuard` (`BeforeSave` rejects non-new, `BeforeRemove` unconditional `Forbidden`); `AIRequestLogService` exposes create-only | **NOT READY** (code present) |
| C20-INV-08 | Exactly one AIRequestLog per completed invocation with provider/model/tokens/cost/latency/prompt version | DEFERRED | Hard required-field validation (provider, model, tokens, cost, latency, template id/version/hash); unique indexes `(aiJobId, attemptId)` and `(aiJobId, attemptNumber)`; prompt-version consistency check. Producer path absent by design (C20 runtime) | **NOT READY** (record contract present; invocation producer pending by design) |
| C20-INV-09 | Referenced PromptTemplate version immutable — only superseded | DEFERRED | `IMMUTABLE_AFTER_REFERENCE_FIELDS` + `assertImmutableFieldsUnchanged()`; hash-equality guard on every save; supersede via `createNewVersion()` only; reference marked transactionally with first log | **NOT READY** (code present) |
| C20-INV-10 | Retry eligibility solely by §4.3 taxonomy; AUTH/VALIDATION/QUOTA/CONTENT_FILTER never auto-retry | DEFERRED | **No CRM-side retry enforcement exists** — no maxAttempts, no eligibility classifier, no `nextRetryAt` writer (only schema fields + docblock disclaimers). Taxonomy retry set exists connector-side only (`taxonomy.py`) | **REQUIRES C20 CHANGE** (CRM-side retry-eligibility enforcement), then NOT READY |
| C20-INV-11 | Idempotency key persisted before dispatch, identical across retries | DEFERRED | `idempotencyKey` required at create, `readOnly`, unique index `(idempotencyKey, deleteId)`; create-time conflict check; retry reuses the same row | **NOT READY** (code present; dispatch pending by construction) |

**Sufficiency judgment (historical D-3):** as a runtime contract set,
INV-05…11 covers the maturity evidence that later C20 execution may require
(status guard, append-only log, one-row-per-invocation, template immutability,
retry governance, and idempotency). They remain **DEFERRED** and are not
claimed ACTIVE. Under the ratified WP2 foundation gate, brief provenance is
bounded by the ratified provenance contract and boundary evidence; it does not
require C20 runtime invariant activation at this stage.

---

## 8. Go / No-Go Matrix

### 8.1 Matrix

| Dependency | Status | Basis |
| --- | --- | --- |
| Completion Capability | **PASS** | `COMMERCIAL_BRIEF` capability identity is ratified and available for foundation consumption. C25 does not own the C20 registry or runtime execution. |
| Provider Binding | **PASS** | ProviderBinding policy boundary and `commercial_brief_generation` purpose policy are available for governance consumption; no C25 routing or dispatch authority is created. |
| Purpose Matrix | **PASS** | Eligibility determination complete by this package (§6). Effect requires C20 registration — tracked under the Provider Binding row. |
| Foundation Gate | **PASS WITH INFORMATIONAL NOTES** | Capability identity + Purpose policy + Boundary evidence are ratified. C20-INV-05…11 remain deferred runtime maturity items and are not activated by this gate. |

### 8.2 Final result

```text
GO FOR WP2 FOUNDATION REVIEW
```

Gate rule after C20 ratification: the foundation gate passes when capability
identity, purpose policy, and boundary evidence are available. WP2.1A may be
separately authorized for governance work. No implementation may start from
this package.

### 8.3 Flip conditions — required C20 governance actions

1. Preserve the ratified capability identity, purpose policy, ProviderBinding
   boundary, eligibility, mapping, and provenance evidence.
2. Keep C20-INV-05…11 deferred unless a separate C20 runtime authorization is
   issued; no activation is required for WP2 foundation review.
3. Proceed to the separately authorized WP2 foundation reviews while keeping
   generation implementation, provider execution, and deployment closed.

---

## 9. Authorization Boundary

- This package is a **governance dependency resolution package only**. It
  does not reopen the ratified WP2 Charter or Implementation Plan, and it
  produces no implementation artifacts.
- It authorizes **no code, no entity, no metadata, no scope, no ACL, no
  controller, no route, no migration, no test, no C20 change, no Connector
  change, no Capability Registry change, no CompletionProvider change, no
  Provider Binding implementation, no runtime dispatch, no AI invocation,
  no commit, no push, no tag**.
- WP2.1A is **not** authorized by this package. WP2.1B, WP2.2–WP2.5 remain
  unauthorized. Each later work package requires its own separate
  authorization after the gates in §8 are satisfied.
- The three flip conditions in §8.3 belong to **C20 governance**; C25 does
  not perform, schedule, or commit them.

---

## 10. References

1. `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md`
2. `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md`
3. `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
4. `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`
5. `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
6. `docs/adr/C20_INVARIANT_REGISTRY.md`
7. `chitu-connector/chitu_connector/acquisition/providers/completion/base.py`
8. `chitu-connector/chitu_connector/acquisition/providers/completion/adapter.py`
9. `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
10. `chitu-connector/chitu_connector/acquisition/providers/registry.py`
11. `chitu-connector/chitu_connector/acquisition/providers/taxonomy.py`
12. `crm-extension/files/custom/Espo/Modules/AIPlatform/` (live entityDefs, Services, Hooks)
