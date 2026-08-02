# Phase3C20 Runtime Implementation Charter and Work Package Plan

| Field | Value |
| --- | --- |
| Document Type | Runtime implementation charter and work-package plan (planning only) |
| Execution Mode | Runtime implementation planning only — repository verification required, no code implementation |
| Status | RATIFIED — runtime implementation planning reference only; no work package or code automatically authorized |
| Date | 2026-08-02 |
| Frozen governance baseline | `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| Implementation authorization | None — any code implementation NOT AUTHORIZED |
| C25 WP2.2 gate | NO GO |

```text
Charter status:
RATIFIED — runtime implementation planning reference only; no work package or code automatically authorized

Any code implementation:
NOT AUTHORIZED
```

This charter defines the runtime implementation work required to move
Phase3C20 from **Governance FROZEN** to **Runtime implemented, verified, and
eligible for invariant activation**. It does not reopen or redesign the frozen
governance baseline. Ratification approves the Runtime Charter as a planning
and work-package reference only. Ratification does not start RT-WP0 or any
later work package.

---

## 1. Document Control

| Item | Value |
| --- | --- |
| Governing baseline commit | `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| Governing documents | §3 list (authoritative) |
| Consumer requirements | §3.1 C25 list (consumer only, non-authoritative for C20) |
| Repository evidence | Live repository at HEAD `928aa5f` (verified 2026-08-02) |
| Output | Only `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` |

No other file is created, no existing file modified, and no stage, commit,
push, or tag is performed.

---

## 2. Executive Runtime Verdict

The frozen C20 governance baseline is complete and internally consistent. The
live repository confirms every readiness classification in ADR-C20-007. No
governance gap was found that would require reopening the frozen baseline.

Runtime implementation state is **INCOMPLETE BY DESIGN**:

| Surface | Governance state | Live-repository state | Runtime consequence |
| --- | --- | --- | --- |
| `CompletionCapability` portfolio | Four ratified values; `COMMERCIAL_BRIEF` proposed only | Four values in `completion/base.py`; `COMMERCIAL_BRIEF` absent | Brief capability not deliverable |
| Purpose `commercial_brief_generation` | Proposed only | No binding registers or allows it | Purpose not deliverable |
| `ProviderBinding` CRM policy surface | Governance ratified | No entityDefs/service/guard/UI exists | No `allowed_provider_bindings` producer |
| Controlled dispatch | Contract direction known | No orchestrator, connector dispatch port, or API/Jobs surface | No runtime dispatch path |
| INV-05, 07, 09 | READY | Enforcement surfaces present; registry rows DEFERRED | Activation evidence only |
| INV-06, 08, 10, 11 | REQUIRES CHANGE | Missing cancel-reason contract, dispatch-to-log producer, retry executor, pre-dispatch reservation | Runtime work required |

**Verdict:** eight runtime work packages (RT-WP0 through RT-WP8) close the
verified gaps. No work package starts automatically; each requires separate
authorization. Invariant activation occurs only after independent evidence,
per RT-WP7.

**C25 WP2.2 remains NO GO.** This charter does not authorize C25 generation
implementation.

---

## 3. Frozen Governance Baseline

The following documents are authoritative, tracked at `928aa5f`, and unchanged
by this charter.

| Role | Document |
| --- | --- |
| C20 charter | `docs/PHASE3C20_CHARTER.md` |
| WP1 exit reconciliation | `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md` |
| WP2 capability registry freeze | `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md` |
| WP3 governance completion | `docs/PHASE3C20_WP3_GOVERNANCE_COMPLETION.md` |
| Completion capability scope | `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` |
| ADR — capability portfolio | `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md` |
| ADR — provider binding governance | `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md` |
| ADR — invariant activation plan | `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md` |
| Invariant registry | `docs/adr/C20_INVARIANT_REGISTRY.md` |

### 3.1 Consumer requirements (non-authoritative)

C25 documents were read strictly as consumer requirements; where a C25 file and
a C20 governance file disagree, the C20 file governs. All are tracked at
`928aa5f`; no local-only copy was used. Read:
`docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md` (dependency evaluation, NO
GO), its `_ADDENDUM.md` (scope clarification, generation NO GO),
`docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (§10 C20 verdict), and
`docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` (§7 C20 dependency plan).

### 3.2 Prior WP3 execution charter (evidence only)

`docs/PHASE3C20_WP3_AI_EXECUTION_CHARTER.md` and
`docs/PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md` are tracked and were read as
repository evidence of prior WP3 execution intent (retry governance §5, entity
decisions §7). They are not authoritative and authorize nothing.

---

## 4. Repository Evidence

Live verification at HEAD `928aa5f`. Archived trees were not used as
authoritative evidence.

### 4.1 Connector and capability registry

| Surface | Verified fact |
| --- | --- |
| `Capability` enum | `providers/capabilities.py` — exactly `SEARCH`, `ENRICHMENT`, `COMPLETION` |
| `CompletionCapability` enum | `providers/completion/base.py` — exactly `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE`; `COMMERCIAL_BRIEF` absent |
| `CompletionRequest` / `Result` | Request: capability, purpose, prompt, `idempotency_key`, `initiating_user`, context, model, max_tokens, temperature, `prompt_template_version`. Result: cost envelope, finish reason, provider reference |
| `CompletionProvider` / adapter | Protocol `complete()`; `CompletionBridgeProvider` (name `COMPLETION_BRIDGE`, capability `COMPLETION`, injected transport only); `_SYSTEM_PROMPTS` keyed to exactly the four ratified capabilities |
| `ProviderBinding` (connector) | `registry.py` — provider_id, adapter_type, priority, enabled, `credential_reference`, `supported_capabilities`, health_state, `allowed_purposes` |
| `CapabilityResolutionRequest`/`Result` | capability, purpose, `allowed_provider_bindings`, credential_availability, provider_health, policy_version, request_context → deterministic selection plus complete non-secret evaluation trace |
| `CapabilityRegistry` | `register()`/`resolve()`; fails closed `CAPABILITY_UNAVAILABLE`; never discovers providers, resolves secrets, constructs transports, or invokes adapters |
| Purpose / secret rejection | `PURPOSE_NOT_ALLOWED` when purpose not in `binding.allowed_purposes`; `SECRET_IN_RESOLUTION_INPUT` for secret-bearing context |
| Failure taxonomy | `taxonomy.py` — 8 classes; retryable set exactly `{NETWORK, PROVIDER, RATE_LIMIT}` |
| Credential config | `providers/config.py` — `api_key`/`api_token` use `field(repr=False)` |
| Chitu interfaces | `vendored/contracts/` — vendored read-only interfaces |
| Send classification | `espocrm_sync/failure_classification.py` — `FailureCategory` incl. `QUOTA`, `CONTENT_FILTER` |

### 4.2 CRM AI Platform

| Surface | Verified fact |
| --- | --- |
| `AIJob` entityDefs | capability `[SEARCH, ENRICHMENT, COMPLETION]`, status `[QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED]`, `attemptCount`, `failureCategory` (8 values), `nextRetryAt`, required `readOnly` `idempotencyKey`, unique `(idempotencyKey, deleteId)`. **No `cancelReason` field.** |
| `AIJobService` | `create()`/`transition()`; frozen `VALID_TRANSITIONS`; transaction-managed; `AIJobStatusMutationSaveOption`; create-time idempotency precheck (returns existing job or `Conflict`). **No cancel reason, retry classifier, or dispatch.** |
| `AIRequestLog` | entityDefs all `readOnly`; `attemptId`/`attemptNumber` (min 1); unique `(aiJobId, attemptId, deleteId)`, `(aiJobId, attemptNumber, deleteId)`; required provider/model/tokens/cost/latency/template provenance; service create-only, validates prompt provenance, marks template referenced in-transaction |
| `PromptTemplate` | entityDefs (version, `contentHash`, `hasBeenReferenced`, `[DRAFT, ACTIVE, RETIRED]`, unique `(templateKey, version, deleteId)`); service (`createNewVersion`, `markReferenced`, `assertImmutableFieldsUnchanged`) |
| Guards / save options | `AIJobStatusMutationGuard`, `AIRequestLogAppendOnlyGuard`, `PromptTemplateMutationGuard`; `AIJobStatusMutationSaveOption`, `AIRequestLogSaveOption`, `PromptTemplateSaveOption` |
| `ProviderCredential` | 10 governed fields; `credentialReference` write-only (`entityAcl` `internal: true`) |
| ACL / scopes | `app/acl.json` scopeLevel `false` for ProviderCredential/PromptTemplate/AIRequestLog; adminMandatory restricts AIRequestLog edit/delete to `no`; Portal denied (`app/aclPortal.json`); `aclDefs/*.json` all `{}`; scopes entity true, tab false, aclPortal false |
| Admin surface | `app/adminPanel.json` — Administration → AI Platform → Credentials only |
| Binding | `Binding.php` — empty `process()`; marker `adr-c20-aiplatform-v1` |
| Runtime directories | **None** — no `Controllers/`, `Api/`, `Actions/`, `Jobs/` in `Modules/AIPlatform` |
| Provider binding surface | **Absent** — no `ProviderRoute`/`ProviderBinding` entityDefs or PHP class under `crm-extension/` |
| Retry/requeue | No CRM-side retry executor; `nextRetryAt` schema-only; `FAILED → QUEUED` exists without eligibility check; no AIJob queue predicate (Prospecting precedent: `c18FailedSend` PrimaryFilter) |

### 4.3 Infrastructure patterns

| Pattern | Verified convention |
| --- | --- |
| ACL metadata | `app/acl.json` + `app/aclPortal.json` + `entityAcl/*.json` + `scopes/*.json` + `aclDefs/*.json` |
| Transactions | `EntityManager::getTransactionManager()->run(...)` (AIJobService, AIRequestLogService, Prospecting orchestration) |
| Unique indexes | `"indexes": {"name": {"type": "unique", "columns": [...]}}` including `deleteId` |
| Extension install | `manifest.json` (version `1.9.13-alpha`, php ≥ 8.1), `scripts/AfterInstall.php` (SQL + rebuild), `build_release_package.py` |
| Test layout | `pytest.ini` — testpaths `crm-extension/tests` + `tests`; pythonpath `chitu-connector`; canonical `pytest -q` |
| C20 contract tests | `crm-extension/tests/test_phase3c20_wp0_*`, `wp1_*`, `wp3_*`; `chitu-connector/tests/test_phase3c20_wp2_capability_registry.py` |
| Connector invocation | PHP defines the `ConnectorBoundary` port (`ProviderBoundary/ConnectorBoundary.php`) — `execute(ProviderExecutionRequest): ProviderResultEnvelope`, governance references only; Python `chitu_connector` implements it (in-process; no `subprocess`/`exec` in PHP). Connector workers use claim semantics (`worker.py`). PHP performs no outbound provider HTTP (C20-INV-03). |

---

## 5. Current Runtime Gap Matrix

Classifications below were confirmed against the live repository (§4). Labels
are those of ADR-C20-007 §4, unchanged.

| Area | Governance state | Verified runtime gap | Owner |
| --- | --- | --- | --- |
| Completion capability portfolio | Four-value portfolio ratified | `COMMERCIAL_BRIEF` is not an approved capability; RT-WP1 has no code-bearing scope under the current portfolio | C20 governance; any future technical mapping is separate |
| Purpose delivery | Proposed | `commercial_brief_generation` is not registered on any binding; registry rejects deterministically | RT-WP2 |
| ProviderBinding CRM surface | Governance ratified | Persistence/authorization surface missing; no `allowed_provider_bindings` producer | RT-WP2 |
| Controlled dispatch | Contract direction known | No dispatch orchestrator, connector dispatch port, or AIJob-driven path | RT-WP3 |
| INV-05 | READY | Activation evidence required (code present) | RT-WP7 |
| INV-06 | REQUIRES CHANGE | Cancel-reason contract missing | RT-WP4 → RT-WP7 |
| INV-07 | READY | Activation evidence required (code present) | RT-WP7 |
| INV-08 | REQUIRES CHANGE | Exactly-once dispatch-to-log path missing | RT-WP3 → RT-WP7 |
| INV-09 | READY | Activation evidence required (code present) | RT-WP7 |
| INV-10 | REQUIRES CHANGE | Retry classification/executor missing on CRM side | RT-WP5 → RT-WP7 |
| INV-11 | REQUIRES CHANGE | Pre-dispatch idempotency reservation missing | RT-WP6 → RT-WP7 |

---

## 6. Runtime Architecture Boundary

The implementation charter preserves the frozen chain unchanged:

```text
CRM policy
→ authorized ProviderBinding set
→ CapabilityRegistry eligibility resolution
→ CRM governed dispatch orchestration
→ Connector outbound provider dispatch
→ Provider adapter / provider HTTP
```

| Term | Owner |
| --- | --- |
| Dispatch orchestration | CRM / AIPlatform |
| Binding eligibility | Capability Registry |
| Outbound provider dispatch | Connector |
| Provider adapter invocation | Connector |
| Provider HTTP | Connector |
| Credential resolution | Connector custody boundary |

```text
CRM owns governed dispatch orchestration.

Connector owns outbound provider dispatch, provider-adapter invocation,
transport execution, and provider HTTP.

CRM performs no outbound provider HTTP and invokes no provider SDK directly.
```

Do not use the unqualified phrase `dispatch owner`.

| Layer | Owns | Does not own |
| --- | --- | --- |
| CRM / AIPlatform | policy, capability request, permitted binding references, purpose, AIJob lifecycle, request correlation, audit/provenance references, human initiation, authorization, governed dispatch orchestration | provider SDK, outbound provider HTTP, live provider counters, provider secrets, direct model invocation, provider-adapter invocation |
| Capability Registry | deterministic eligibility resolution, filtering `allowed_provider_bindings`, capability compatibility, purpose eligibility, deterministic rejection reasons | provider discovery, transport, credentials, adapter invocation, health probing, retry execution |
| Connector | outbound provider dispatch, outbound HTTP, adapter invocation, response normalization, live runtime counters, provider health production, provider-specific retry hints, credential resolution within the approved custody model | CRM policy, lifecycle authority, dispatch orchestration policy |
| C25 CommercialBrief | none of the above | provider selection, model selection, binding ownership, dispatch orchestration, outbound provider dispatch, credentials, retries, runtime counters, health state |

No `ProviderRoute` parallel abstraction is introduced unless a new ADR is
approved.

---

## 7. Runtime Ownership Matrix

| Concern | Owner | C25 role |
| --- | --- | --- |
| Capability portfolio decision | C20 governance | Consumer |
| Purpose registration | C20 governance + CRM binding policy | Proposes only |
| ProviderBinding policy surface | CRM / C20 policy owner | No ownership |
| Health-policy representation | CRM ProviderBinding surface (RT-WP2) | No ownership |
| Health-input consumption | CRM dispatch orchestration (RT-WP3) | No ownership |
| Health production / probing | Connector / approved runtime health service | No ownership |
| `allowed_provider_bindings` producer | CRM dispatch orchestration | None |
| Eligibility resolution | CapabilityRegistry (frozen) | None |
| Dispatch orchestration | CRM / AIPlatform (`AIDispatchService`) | None |
| Outbound provider dispatch | Connector-owned runtime | None |
| Provider adapter invocation | Connector-owned runtime | None |
| Provider HTTP | Connector-owned runtime | None |
| Credential resolution | Connector custody boundary | None |
| AIJob lifecycle | C20 AIPlatform | Consumer after authorization |
| AIRequestLog exactly-once producer | CRM dispatch orchestration (via AIRequestLogService) | Reference only |
| Cancel-reason contract | C20 AIPlatform | Consumer after authorization |
| AIJob / Completion retry policy and executor | CRM (RT-WP5; re-runs binding eligibility) | No ownership |
| SendExecution retry scheduling | Connector-side (unchanged; outside this charter) | No ownership |
| Idempotency reservation contract | CRM dispatch orchestration | No ownership |
| PromptTemplate immutability | C20 AIPlatform | Reference only |
| Connector execution | Connector-owned runtime | No ownership |

---

## 8. Capability and Purpose Delivery

### 8.1 Decision

**RT-WP1 owns both capability representation and purpose delivery as two
distinct, separately authorized deliverable units.** ADR-C20-005 requires
"separate but coordinated C20 approval and delivery"; that separation is
preserved as ordered sub-tasks, not one merged change.

| Identifier | Layer | Planned RT-WP1 form |
| --- | --- | --- |
| `COMMERCIAL_BRIEF` | Proposed `CompletionCapability` extension | Enum value in `completion/base.py` **only if separately authorized**; must not become automatically routable |
| `commercial_brief_generation` | Proposed ProviderBinding purpose ID | Registered on a binding `allowed_purposes` (RT-WP2), never as a capability |
| `CommercialBrief` | C25 domain artifact | Not created here |
| `Capability.COMPLETION` | Existing registry family | Unchanged |

### 8.2 Required RT-WP1 decisions

| Item | Planned decision |
| --- | --- |
| Enum location / value | `providers/completion/base.py`; serialized `commercial_brief` (snake_case) |
| Backward compatibility | Existing four values unchanged; additive only |
| Unknown-value behavior | Rejected at `CompletionRequest` construction; adapter `_SYSTEM_PROMPTS` stays the routing gate |
| Schema/version compatibility | No transport or registry schema change; purpose remains a string |
| Purpose registration location | `ProviderBinding.allowed_purposes` (RT-WP2 surface) |
| Rejection before binding delivery | `PURPOSE_NOT_ALLOWED` per binding; `CAPABILITY_UNAVAILABLE` if none permits it |

### 8.3 Non-routability guarantee

A `COMMERCIAL_BRIEF` enum value must not become automatically routable. The
adapter `_SYSTEM_PROMPTS` map is the routing gate: no entry means the adapter
refuses completion, and no binding permits the purpose, so the registry rejects
deterministically. C25 cannot route a capability that no binding authorizes.

### 8.4 Exit gate

Existing four capabilities unchanged; new value (if authorized) not
automatically routable; no binding → deterministic rejection; capability/purpose
distinction preserved in contract tests.

---

## 9. ProviderBinding Policy Surface

### 9.1 Decision

**ProviderBinding as a CRM policy entity** (entityDefs + service + mutation
guard) is the preferred implementation direction because it matches AIPlatform
entity conventions and ADR-C20-006 §13. Code implementation is blocked until
the RT-WP2 Foundation Review confirms that direction (§21).

### 9.2 Required fields (policy metadata only)

| Field group | Planned fields | Rule |
| --- | --- | --- |
| Identity | `name`, `providerKey`/`providerId`, `adapterType` | Unique; immutable after create |
| Routing policy | `priority`, `enabled` | Deterministic selection inputs |
| Capability support | `supportedCapabilities` (SEARCH/ENRICHMENT/COMPLETION) | `BINDING_CAPABILITY_UNSUPPORTED` gate |
| Purpose policy | `allowedPurposes` | `PURPOSE_NOT_ALLOWED` gate |
| Credential | `credentialReference` (`internal: true`); availability via custody boundary | Reference only; never secret |
| Health policy | health-policy reference and/or health eligibility policy; optional last-known health classification only if Foundation Review approves it as a policy cache | No live counters; no probing; see §9.3 |
| Governance | `enabled`, team/role visibility, audit | Guard-enforced |

### 9.3 Provider-health ownership (ADR-C20-006 delivery)

| Layer | Owner | May store / do | Must not |
| --- | --- | --- | --- |
| Health-policy representation | RT-WP2 / CRM ProviderBinding | health policy reference; health eligibility policy; optional last-known classification if Foundation Review approves | live counters; runtime statistics; active probing |
| Health-input consumption | RT-WP3 / CRM dispatch orchestration | consume normalized `provider_health` as an externally supplied eligibility input on `CapabilityResolutionRequest` | produce or probe health from CRM PHP |
| Health production | Connector / approved runtime health service | probing; live availability; rate-limit/runtime counters; latency/runtime signals; normalized health result | be owned by CommercialBrief or Capability Registry |

Capability Registry does not probe health. CommercialBrief does not read or own
health state. No provider health probe may run from CRM PHP.

RT-WP2 Foundation Review must decide: whether CRM persists any last-known
health classification; whether it stores only a health-policy reference;
maximum staleness; who may update a cached value; whether cached health is
advisory or blocking.

RT-WP3 must define: health-input DTO; source authenticity; freshness;
unavailable-health behavior; deterministic rejection code; fallback policy.

### 9.4 Must preserve

```text
CRM stores policy.
Connector stores live counters and runtime state.
```

No secret storage (`credentialReference` write-only); no provider invocation
from CRM; no live counters in CRM; no parallel authorization model; Portal
denied; admin-only governed CRUD via save options.

### 9.5 Exit gate

RT-WP2 Foundation Review PASS; CRM produces an authorized, validated binding
set consumed as `allowed_provider_bindings`; no secret leakage; no provider
invocation; no live counters; no parallel authorization model; registry
contract tests consume a fixture binding from the CRM surface.

---

## 10. Controlled Dispatch

### 10.1 Decision

```text
CRM owns governed dispatch orchestration.

Connector owns outbound provider dispatch, provider-adapter invocation,
transport execution, and provider HTTP.

CRM performs no outbound provider HTTP and invokes no provider SDK directly.
```

CRM `AIDispatchService` performs dispatch orchestration: it authorizes a
dispatch from an eligible AIJob, resolves the binding set, supplies registry
inputs (including externally supplied `provider_health`), acquires the
reservation, and hands a normalized execution request across a connector port.
Connector owns outbound provider dispatch and adapter invocation. The
mechanism reuses the verified `ConnectorBoundary` port pattern (§4.3); RT-WP3
extends or parallels it for completion dispatch. No new scheduler architecture
is introduced. Do not use the unqualified phrase `dispatch owner`.

### 10.2 Dispatch path

```text
AIJob (QUEUED, authorized save option)
 → CRM AIDispatchService (dispatch orchestration)
    → binding set from ProviderBinding surface
    → idempotency reservation (RT-WP6) before outbound dispatch
    → CapabilityResolutionRequest (incl. externally supplied provider_health)
    → CapabilityRegistry.resolve() (eligibility only)
    → ProviderExecutionRequest (governance references only)
 → ConnectorBoundary.execute (outbound provider dispatch)
    → resolves credential within custody model
    → invokes CompletionProvider adapter (injected transport / provider HTTP)
    → normalizes result / failure classification
    → ProviderResultEnvelope (status, audit/result reference, failure category)
 → CRM completion
    → exactly one AIRequestLog per dispatch attempt (RT-WP3)
    → AIJob transition SUCCEEDED / FAILED / retry / CANCELLED
```

### 10.3 Exactly-once semantics

Distinguish: one AIJob (logical invocation); one dispatch attempt; one
AIRequestLog per actual provider dispatch attempt; multiple retry attempts each
with a new attempt identity; idempotent replay (same key → same logical job);
no duplicate provider invocation after ambiguous failure without explicit
recovery policy. Cardinality is enforced by connector-side attempt claim
atomicity, the unique indexes `(aiJobId, attemptId, deleteId)` and `(aiJobId,
attemptNumber, deleteId)`, and the reservation contract (RT-WP6).

### 10.4 Crash recovery

| Crash point | Recovery rule |
| --- | --- |
| Before reservation | No dispatch, no provider call; reservation created next attempt |
| After reservation, before dispatch | Reservation governs; replay returns the reserved attempt |
| After dispatch, before AIRequestLog | Attempt claim prevents duplicate invocation; write-back replays log creation |
| Duplicate result/callback | Unique indexes reject duplicate log; replay returns original result reference |

### 10.5 Exit gate

INV-08 implementation evidence complete; dispatch-to-log cardinality proven;
no provider SDK in CRM; no outbound HTTP from PHP (C20-INV-03); transaction and
crash tests pass.

---

## 11. AIRequestLog Exactly-Once Contract

The existing AIRequestLog surface is the evidence contract; RT-WP3 supplies the
missing producer.

| Requirement | Existing evidence | RT-WP3 addition |
| --- | --- | --- |
| Exactly one log per actual dispatch attempt | Unique indexes present | Producer writes exactly one per claimed attempt |
| Append-only | Guard rejects update/delete; admin acl edit/delete `no` | Activation evidence in RT-WP7 |
| Immutable provider/model/provenance | All fields `readOnly` | No change |
| Attempt identity | `attemptId`, `attemptNumber` | Assigned per attempt |
| Request correlation | `aiJobId` link | Supplied by producer |
| Failure details | `errorClass`, `failureCategory` | Classified via `taxonomy.py` |
| Cost/tokens/latency | Required fields | Mapped from `CompletionResult.cost` |
| No human review event | — | AIRequestLog never records human review; C25 uses its own audit surface |

---

## 12. Cancel-Reason Contract

### 12.1 Decision

**Cancel reason is stored on AIJob as a governed, service-owned field set** —
`cancelReasonCode` (enum) plus optional bounded `cancelReason` text — written
only by `AIJobService` on the `CANCELLED` transition, with a server-owned
timestamp. `CANCELLED` is terminal and immutable, so the AIJob row is both the
current-state summary and the append surface; no general-purpose workflow
engine or separate audit entity is introduced.

### 12.2 Required behavior

| Concern | Rule |
| --- | --- |
| Cancellation eligibility | Only `QUEUED → CANCELLED` and `RUNNING → CANCELLED` (frozen matrix) |
| Cancellation actor | Human operator or system with authorization; recorded |
| Reason code / text | Bounded enum required on every `CANCELLED` transition; optional bounded text, sanitized |
| Server-owned timestamp | `completedAt` set by `AIJobService` clock |
| Terminal transition | `CANCELLED` terminal; no exit; not retryable |
| Cancellation after dispatch | In-flight attempt completes and logs exactly once; no new retry |
| Cancellation during dispatch | Reservation released; attempt claim governs; no duplicate invocation |
| Append-only evidence | AIJob immutable after terminal; cancel fields service-owned; guard rejects direct mutation |
| Authorization / admin no-bypass | `AIJobStatusMutationSaveOption` required; guard applies to all roles |

### 12.3 Exit gate

All cancel transitions require a valid reason; direct field mutation blocked;
tests prove no missing-reason path; INV-06 eligible for activation review.

---

## 13. Retry Contract

### 13.1 Decision

**Retry policy and executor for AIJob / Completion runtime are CRM-owned
(RT-WP5).** The connector may emit provider/runtime retry hints
(e.g. `retry_after`), but CRM owns the governed AIJob policy. The executor
does not own provider selection: every retry re-runs binding eligibility
through the registry. No new autonomous scheduler architecture. AIJob already
carries `attemptCount`, `nextRetryAt`, and `FAILED → QUEUED`. RT-WP5 adds the
eligibility gate those surfaces lack.

### 13.1.1 SendExecution boundary reconciliation

```text
The frozen C20 Charter statement that SendExecution retry scheduling remains
connector-side is unchanged.

RT-WP5 introduces a separate CRM-owned retry policy and executor specifically
for AIJob / Completion runtime under C20-INV-10.
```

| Runtime | Retry ownership | RT-WP5 scope |
| --- | --- | --- |
| Existing SendExecution | Connector-side; existing mechanism unchanged | Outside RT-WP5; not modified unless separately authorized |
| New AIJob Completion | CRM owns retry eligibility policy, retry budget, `nextRetryAt`, operator retry authorization, AIJob lifecycle, re-running binding eligibility; Connector owns provider retry hints, outbound re-dispatch, transport, provider adapter invocation | In scope |

RT-WP5 must not modify SendExecution retry semantics unless separately
authorized.

Required boundary tests (RT-WP5):

* AIJob retry changes do not alter SendExecution;
* SendExecution retry remains connector-side;
* AIJob retry always re-runs Capability Registry eligibility;
* retry does not select provider directly in CRM.

### 13.2 Taxonomy mapping (fixed by ADR-C20 §4.3)

| Category | Auto-retry | Behavior |
| --- | --- | --- |
| `NETWORK` | Yes | Backoff + jitter; bounded by max attempts |
| `PROVIDER` | Yes (5xx only) | Backoff; bounded by max attempts |
| `RATE_LIMIT` | Yes | Honour `retry_after`; backoff |
| `AUTH` | Never | Terminal; credential alert |
| `VALIDATION` | Never | Terminal; operator revision |
| `UNKNOWN` | Never | Terminal; operator review |
| `QUOTA` | Never | Terminal; halts capability |
| `CONTENT_FILTER` | Never | Terminal; never auto-retry same prompt |

### 13.3 Required behavior

Retryable categories `{NETWORK, PROVIDER, RATE_LIMIT}`; per-capability
`maxAttempts` (AIJob `attemptCount`); deterministic backoff + jitter with
`nextRetryAt` server-owned; operator `aiJob.retry` re-runs eligibility;
automatic retry only per taxonomy within budget; cancelled jobs not retried;
terminal failure on budget exhaustion or terminal category; each retry attempt
creates exactly one AIRequestLog with a new attempt identity.

### 13.4 Exit gate

Deterministic retry matrix enforced; bounded retries; no duplicate dispatch;
one AIRequestLog per retry attempt; INV-10 eligible for activation review.

---

## 14. Idempotency Reservation Contract

### 14.1 Decision

```text
CRM orchestration owns the reservation contract.
Connector owns outbound dispatch.
```

**Reservation contract owner is CRM dispatch orchestration.** The persistence
form is **not final** until the RT-WP6 Foundation Review (§25). RT-WP6 adds a
pre-dispatch reservation persisted before outbound provider dispatch and
identical across retries of the same logical invocation. Verified precedents:
`AIJobService` already performs a create-time idempotency precheck
(`findExistingIdempotencyKey` + context equality); the connector's
`send_idempotency.py` models reservation patterns RT-WP6 may pattern-match.
The two are not yet integrated; RT-WP6 closes that gap.

```text
Model selection resolves through CRM binding policy plus registry eligibility
and Connector execution policy; C25 never selects the model.
```

### 14.2 Identity layers (must remain distinct)

1. Business request identity (consumer's logical key) · 2. AIJob identity (one
per logical invocation, existing `idempotencyKey`) · 3. Dispatch attempt
identity (`attemptId`/`attemptNumber` per retry) · 4. AIRequestLog identity
(one row per actual dispatch attempt) · 5. Provider idempotency token
(`Idempotency-Key` header when supported).

### 14.3 Required behavior

Behavioral rules below are fixed. Persistence form, unique-constraint
placement, and reservation-state storage are decided by the RT-WP6 Foundation
Review (§25) and are not implied final by this charter.

| Concern | Rule |
| --- | --- |
| Pre-dispatch reservation | Created before any outbound provider call |
| Unique constraint | Unique constraint over the reservation key (form decided at RT-WP6 Foundation Review) |
| Lifecycle / collision | Created → reserved → completed/released → terminal; concurrent equivalent requests return the same logical job |
| Stale reservation recovery | Governed release with audit |
| Request replay | Returns the original job and result reference |
| AIJob / attempt association | Reservation tied to the AIJob; attempt identity carried through |
| Provider-call suppression | No second provider call while a reservation is active |
| Retry relationship | Same reservation across retries; new attempt identity per retry |
| Cross-user boundary | Per logical invocation; collision rejected by context equality |
| Purpose/capability/binding inputs | Included in reservation context equality |

### 14.4 Exit gate

Concurrent equivalent requests produce one allowed dispatch; stale reservation
has governed recovery; no duplicate provider call; INV-11 eligible for
activation review.

---

## 15. Security and Credential Custody

| Requirement | Enforcement intent |
| --- | --- |
| No secrets in CRM entities | `credentialReference` only; entityAcl `internal: true`; forbidden-field contract tests |
| No credentials in logs | Connector `field(repr=False)`; safe failure messages |
| No raw prompt in generic audit output | AIRequestLog stores template id/version/hash, never prompt body |
| No raw completion payload unless approved | AIRequestLog metadata only; result via reference under separate approval |
| No CRM outbound provider HTTP | C20-INV-03; connector sole egress |
| No dynamic arbitrary provider class loading | Adapter resolution through frozen registry; action/route allowlists |
| Action and route allowlists | Dispatch and admin surfaces register explicitly |
| Bounded payload sizes | Field-length and payload bounds |
| Purpose allowlist | Registry `PURPOSE_NOT_ALLOWED` |
| SSRF protections | Transport injection; no arbitrary URL from request context |
| Provider response normalization | `taxonomy.py` + adapter `_normalize`; no vendor raw response crosses boundary |
| Safe failure messages | `safe_message` map |
| Portal denial | `aclPortal` scopeLevel false for all AI Platform entities |
| Admin no-bypass | Guards reject direct mutation for every role |
| Append-only enforcement | `AIRequestLogAppendOnlyGuard` |
| Concurrency controls | Attempt claim + reservation + unique indexes |
| Replay protection | Idempotency reservation + context equality |

---

## 16. Failure Matrix

For each condition: AIJob state, AIRequestLog behavior, reservation behavior,
retry eligibility, operator action, side-effect guarantee.

| Condition | AIJob | AIRequestLog | Reservation | Retry | Operator action | Side-effect guarantee |
| --- | --- | --- | --- | --- | --- | --- |
| No eligible binding / unsupported capability | FAILED (VALIDATION) | none | released | none | inspect policy/request | no provider call |
| Purpose not allowed | FAILED (VALIDATION) | none | released | none | correct purpose | no provider call |
| Disabled / unhealthy binding | FAILED (VALIDATION/PROVIDER) | none | released | none | inspect binding/health | no provider call |
| Missing credential reference | FAILED (VALIDATION) | none | released | none | add reference | no provider call |
| Credential resolution failure | FAILED (AUTH) | one FAILED log | released | none | rotate/reference | one log only |
| Network failure / timeout | FAILED (NETWORK) | one FAILED log | active→released | auto within budget | monitor | one log per attempt |
| Rate limit | FAILED (RATE_LIMIT) | one FAILED log | released | auto honouring retry_after | monitor | one log per attempt |
| Quota exhaustion | FAILED (QUOTA) | one FAILED log | released | none | renew quota | one log only |
| Content filter | FAILED (CONTENT_FILTER) | one FAILED log | released | never | revise prompt | one log only |
| Malformed provider response | FAILED (VALIDATION) | one FAILED log | released | none | operator review | one log only |
| Connector crash before dispatch | QUEUED (unchanged) | none | active | re-dispatch | retry | no provider call |
| Connector crash after dispatch before response | RUNNING→FAILED (NETWORK) | none until claim verified | active | governed recovery | verify claim | no duplicate invocation without recovery policy |
| CRM crash before reservation | QUEUED | none | none | re-create | retry | no provider call |
| CRM crash after reservation before dispatch | QUEUED | none | active | replay same job | retry | no duplicate provider call |
| CRM crash after dispatch before AIRequestLog | RUNNING/FAILED | none | active | replay log creation | recover | claim prevents duplicate invocation |
| Duplicate callback/result | unchanged (idempotent) | unique index rejects | active | none | none | one log row |
| Retry exhaustion | FAILED terminal | one log per attempt | released | none | operator review | bounded attempts |
| Cancellation before dispatch | CANCELLED (reason) | none | released | none | none | no provider call |
| Cancellation during dispatch | CANCELLED (reason) | in-flight attempt logs once | released | none | none | no duplicate invocation |

---

## 17. Transaction Model

| Transaction | Owner | Boundary |
| --- | --- | --- |
| AIJob create | `AIJobService` | One save with `AIJobStatusMutationSaveOption`; idempotency precheck outside transaction |
| AIJob transition | `AIJobService` | `TransactionManager::run`; status + timestamps atomic |
| AIRequestLog create | `AIRequestLogService` | Transaction writes log and marks PromptTemplate referenced |
| Dispatch attempt | CRM orchestrator + connector claim | Reservation first; connector claim atomic on expected status; write-back is one log + one transition |
| Retry | CRM retry executor | Eligibility → RUNNING → attempt identity → log |
| Reservation | CRM orchestrator | Created before dispatch; released/completed after attempt outcome |

Each transaction is single-writer and idempotency-consistent. No CRM
transaction ever contains an outbound provider call.

---

## 18. Work-Package Dependency Graph

```text
RT-WP0
 ├─ RT-WP1
 └─ RT-WP2

RT-WP1 + RT-WP2
        ↓
      RT-WP3

RT-WP3
 ├─ RT-WP4
 ├─ RT-WP5
 └─ RT-WP6

RT-WP3 + RT-WP4 + RT-WP5 + RT-WP6
        ↓
      RT-WP7
        ↓
      RT-WP8
```

**Parallelism:** RT-WP1 and RT-WP2 are independent and may run concurrently
after RT-WP0. RT-WP4, RT-WP5, and RT-WP6 may proceed after RT-WP3 only under
the primary-owner shared-file rule below.

### 18.1 Shared-file primary-owner model

Every file has exactly one primary owning WP. Secondary WPs may modify a
shared file only through this coordination rule.

| Shared file | Primary owning WP | Secondary coordinated touches |
| --- | --- | --- |
| `Services/AIJobService.php` | RT-WP4 | RT-WP5 may extend retry behavior through a separately reviewed patch |
| `Resources/metadata/entityDefs/AIJob.json` | RT-WP4 | RT-WP6 may add reservation-related fields only after RT-WP4 baseline is frozen |
| `Services/AIDispatchService.php` | RT-WP3 | RT-WP6 may integrate reservation acquisition/release after RT-WP3 baseline is frozen |

Rules:

* a secondary modification must start from the frozen output of the primary WP;
* the secondary WP must list the exact lines/contracts it owns;
* shared files must not be modified concurrently by parallel branches;
* each shared-file change requires independent regression review against prior
  WP invariants.

---

## 19. RT-WP0 — Runtime Baseline and Contract Lock

**Purpose:** verify live contracts; establish exact file inventory; establish
runtime test harness; identify reusable paths; define the no-change boundary
for frozen C20 governance. **Deliverables:** runtime baseline report; exact
changed-file allowlist; dependency graph; transaction map; connector invocation
map; current invariant evidence matrix. **Scope:** planning/documentation only.
No production code. **Entry gate:** governance freeze unchanged; charter
accepted. **Exit gate:** independent baseline review PASS; all later WPs have
exact owners and boundaries.

---

## 20. RT-WP1 — No-Code Capability-Purpose Reconciliation

**Purpose:** reconcile the ratified four-value capability portfolio with the
CommercialBrief classification. `CommercialBrief` is a C25 business object and
purpose/output contract, not an approved `CompletionCapability`. **Scope:** no
enum addition, adapter change, registry change, ProviderBinding, purpose
registry, dispatch, or C25 code. **Entry gate:** RT-WP0 exit and RT-WP1 Charter
ratification. **Current state:** NO-CODE — RECONCILED. The existing repository
virtual environment `.venv-s01` collected and passed the focused pytest contract
set (66 tests; 26 subtests) on 2026-08-02, and the C20 boundary and invariant
unittest suite passed 19 tests. **Exit Review:** APPROVED. **Administrative Exit:** EXITED.
**Non-effect:** this does not authorize RT-WP2,
provider binding, purpose registration, dispatch, or C25 WP2.2.

---

## 21. RT-WP2 — CRM ProviderBinding Persistence and Authorization Surface

**Purpose:** deliver the CRM-side policy representation that produces the
authorized `allowed_provider_bindings` set.

### 21.1 RT-WP2 Foundation Review — ProviderBinding Policy Surface

Mandatory first deliverable. Documentation and repository verification only.
It must occur before entityDefs, metadata, service, guard, ACL, or rebuild
implementation.

Foundation Review must decide and ratify:

1. Entity versus internal policy artifact;
2. Exact field allowlist;
3. Scope flags;
4. Standard Record API behavior;
5. Generic CRUD boundary;
6. ACL and admin behavior;
7. Portal denial;
8. Credential-reference handling;
9. Provider/model policy fields;
10. Health policy/reference fields;
11. Live counter exclusion;
12. Mutation guard;
13. Save-option/token model;
14. Rebuild/install convention;
15. Entity/artifact budget;
16. Exact implementation allowlist.

Default direction: ProviderBinding as a CRM policy entity (preferred because it
matches AIPlatform entity conventions). Code implementation is blocked until
the Foundation Review confirms it.

**Scope (§9):** after Foundation Review PASS — persistence model; binding
identity; connector reference; supported capabilities; allowed purposes;
enabled state; health-policy representation (§9.3); provider/model policy;
credential reference only; team/role visibility; admin behavior; Portal denial;
generic CRUD boundary; immutable and governed fields; validation; no runtime
counters in CRM; no CRM health probing.

**Entry gate:** RT-WP2 separately authorized **AND** RT-WP2 Foundation Review
PASS. **Exit gate:** Foundation Review decisions satisfied exactly; CRM
produces an authorized, validated binding set; no secret leakage; no provider
invocation; no live counters; no parallel authorization model.

---

## 22. RT-WP3 — Controlled Dispatch and Exactly-Once Request Logging

**Purpose:** create the governed bridge from an authorized AIJob to Connector
outbound provider dispatch. Primary owner of `Services/AIDispatchService.php`.

**Scope (§10, §11):** CRM dispatch orchestration; Connector outbound provider
dispatch boundary; transaction boundary; AIJob eligibility; binding resolution;
purpose check; health-input consumption (§9.3); credential custody boundary;
request correlation; attempt identity; AIRequestLog creation; exactly-one log
per dispatch attempt; response normalization; success/failure transition; no
duplicate outbound dispatch; crash recovery; timeout/rate-limit/content-filter
handling; no CRM outbound HTTP; no unqualified `dispatch owner` language.

### 22.1 AIJob ACL Foundation Gate

Before operator-visible dispatch, retry, or cancel actions are implemented,
verify:

* AIJob read ACL;
* ownership/team visibility;
* create prohibition;
* generic edit prohibition;
* generic delete prohibition;
* operator action permissions;
* admin no-bypass;
* Portal denial;
* source/provenance visibility;
* action authorization versus Record ACL;
* lifecycle guard enforcement.

If existing scope-level `aclPortal:false` is sufficient for Portal, record the
evidence. If `app/acl.json` or `app/aclPortal.json` entries are required, add
them to the exact RT-WP owning allowlist. Do not allow retry/cancel because a
user merely has generic edit access.

**Entry gate:** RT-WP1 + RT-WP2 exits; AIJob ACL Foundation Gate PASS for any
operator-visible dispatch action. **Exit gate:** INV-08 implementation
evidence complete; dispatch-to-log cardinality proven; no provider SDK in CRM;
transaction and crash tests pass.

---

## 23. RT-WP4 — Cancel-Reason Contract

**Purpose:** close C20-INV-06. Primary owner of `Services/AIJobService.php` and
`Resources/metadata/entityDefs/AIJob.json`.

**Scope (§12):** cancellation eligibility; actor; reason code; bounded reason
text; server-owned timestamp; terminal transition; retry interaction;
cancellation after/during outbound dispatch; append-only evidence;
authorization; admin no-bypass; immutable terminal state; AIJob ACL Foundation
Gate (§22.1) before operator-visible cancel actions.

**Entry gate:** RT-WP3 stable; primary-owner rule (§18.1) observed;
AIJob ACL Foundation Gate PASS for cancel actions. **Exit gate:** all cancel
transitions require valid reason; direct field mutation blocked; tests prove no
missing-reason path; INV-06 eligible for activation review; RT-WP4 baseline
frozen before any RT-WP5/RT-WP6 secondary touches to shared files.

---

## 24. RT-WP5 — Retry Classification and Executor

**Purpose:** close C20-INV-10 for AIJob / Completion runtime only.
SendExecution retry remains connector-side and out of scope (§13.1.1).

**Scope (§13):** retryable/non-retryable categories; maximum attempts; backoff;
`nextRetryAt`; operator retry; automatic retry; content-filter,
invalid-request, quota, rate-limit, network, provider-internal, credential
errors; cancellation interaction; terminal failure; no infinite retry.
Connector emits hints; CRM owns AIJob retry policy; executor re-runs binding
eligibility; every retry creates exactly one AIRequestLog; secondary
coordinated patch to `AIJobService.php` only after RT-WP4 baseline freeze
(§18.1); AIJob ACL Foundation Gate (§22.1) before operator-visible retry;
SendExecution boundary tests required.

**Entry gate:** RT-WP3 stable; RT-WP4 baseline frozen for shared
`AIJobService.php`; AIJob ACL Foundation Gate PASS for retry actions. **Exit
gate:** deterministic retry matrix; bounded retries; no duplicate outbound
dispatch; SendExecution unchanged; INV-10 eligible for activation review.

---

## 25. RT-WP6 — Pre-Dispatch Idempotency Reservation

**Purpose:** close C20-INV-11. CRM orchestration owns the reservation
contract; Connector owns outbound dispatch (§14).

### 25.1 RT-WP6 Foundation Review — Reservation Persistence Form

Mandatory first deliverable. Documentation and repository verification only.
The Charter does not imply the storage form is already final.

Foundation Review must choose among:

* fields on AIJob;
* dedicated internal reservation record;
* connector claim plus CRM reservation summary;
* another repository-supported mechanism.

It must decide: persistence owner; unique constraint; reservation states;
expiry; stale recovery; relationship to AIJob; relationship to dispatch
attempt; relationship to AIRequestLog; provider idempotency token; concurrent
acquisition; cross-user identity boundary; generic API exposure;
cleanup/retention.

Secondary coordinated touches to `AIDispatchService.php` and optionally
`entityDefs/AIJob.json` occur only after primary baselines are frozen (§18.1).

**Scope (§14):** after Foundation Review PASS — request idempotency identity;
pre-dispatch reservation; unique constraint; reservation lifecycle; collision
handling; stale reservation recovery; request replay; AIJob association;
dispatch attempt association; provider-call suppression; retry relationship;
concurrent request behavior; cross-user boundary; purpose/capability/binding
inputs; five-layer identity distinction; model selection never by C25.

**Entry gate:** RT-WP3 stable; RT-WP3/RT-WP4 baselines frozen for shared files;
RT-WP6 Foundation Review PASS. **Exit gate:** concurrent equivalent requests
produce one allowed outbound dispatch; stale reservation has governed recovery;
no duplicate provider call; INV-11 eligible for activation review.

---

## 26. RT-WP7 — Invariant Activation and Runtime Verification

**Purpose:** activate C20-INV-05 through C20-INV-11 only after implementation
and independent evidence. **Required sequence per invariant:** (1)
implementation complete; (2) contract tests PASS; (3) negative tests PASS; (4)
runtime tests PASS; (5) boundary tests PASS; (6) independent review PASS; (7)
registry status update via a separately authorized governance-status action;
(8) freeze evidence. **Candidates:** INV-05–11. Do not activate as one batch
unless evidence is complete for every one. Suggested order: READY invariants
(05, 07, 09) first; REQUIRES_CHANGE after their owning WP (08 after RT-WP3, 06
after RT-WP4, 10 after RT-WP5, 11 after RT-WP6). **Entry gate:** RT-WP3–6
exits; evidence complete. **Exit gate:** registry updated by governance action;
evidence pinned to commit; no deferred invariant falsely marked active.

---

## 27. RT-WP8 — Runtime Freeze and C25 Dependency Closure

**Purpose:** verify the completed C20 runtime and formally release it for C25
consumption. **Scope:** remote commit verification; capability/purpose,
binding-surface, dispatch, exactly-once logging, retry, idempotency,
cancellation, invariant activation, and security/credential-custody proofs;
failure matrix; no CRM Core mutation; no C22 execution side effects; no C25
provider ownership; independent freeze review. **After PASS:** create a C25
WP2.0 closure addendum; record capability/binding/invariant dependencies as
resolved; do not automatically authorize C25 WP2.2; C25 must still receive
separate implementation authorization. **Entry gate:** RT-WP7 exit; evidence
pinned. **Exit gate:** independent freeze review PASS; closure addendum
created; C25 WP2.2 remains not authorized.

---

## 28. Exact Candidate Allowlist

Every candidate file is **planned** for a future separately authorized work
package. Nothing here creates or modifies any file. C20 and C25 files are never
mixed in the same implementation commit. No broad directory wildcards for core
implementation files. Default path base:
`crm-extension/files/custom/Espo/Modules/AIPlatform/`.

| WP | File | Role |
| --- | --- | --- |
| 1 | `chitu-connector/chitu_connector/acquisition/providers/completion/base.py` | Enum addition (conditional) |
| 1 | `chitu-connector/chitu_connector/acquisition/providers/completion/adapter.py` | Non-routability guard |
| 1 | `chitu-connector/tests/test_phase3c20_wp2_capability_registry.py` | Purpose-rejection extension |
| 1 | `chitu-connector/tests/test_phase3c20_rt_wp1_capability_purpose.py` | New contract tests |
| 2 | `Resources/metadata/entityDefs/ProviderBinding.json` | Entity definition |
| 2 | `Resources/metadata/scopes/ProviderBinding.json` | Scope |
| 2 | `Resources/metadata/aclDefs/ProviderBinding.json` | ACL definition |
| 2 | `Resources/metadata/entityAcl/ProviderBinding.json` | `credentialReference` write-only |
| 2 | `Resources/metadata/app/acl.json` | Add scopeLevel |
| 2 | `Resources/metadata/app/aclPortal.json` | Portal denial |
| 2 | `Resources/metadata/app/adminPanel.json` | Provider surface entry (if approved) |
| 2 | `Services/ProviderBindingService.php` | Save-option gated CRUD |
| 2 | `Hooks/ProviderBinding/ProviderBindingMutationGuard.php` | Governed-field immutability |
| 2 | `Resources/i18n/{en_US,zh_CN}/ProviderBinding.json` | i18n |
| 2 | `Resources/layouts/ProviderBinding/{list,detail}.json` | Layouts (reference excluded) |
| 2 | `crm-extension/tests/test_phase3c20_rt_wp2_provider_binding.py` | Contract tests |
| 3 | `Services/AIDispatchService.php` | Dispatch orchestration (primary owner RT-WP3) |
| 3 | `Jobs/AIDispatchWorker.php` | Dispatch orchestration job (new Jobs dir) |
| 3 | `Api/PostAIDispatch.php` | Operator action (new Api dir) |
| 3 | `Resources/routes.json` | Route allowlist (new) |
| 3 | `Services/AIRequestLogService.php` | Producer call site (create-only unchanged) |
| 3 | `chitu-connector/chitu_connector/acquisition/providers/completion/dispatch.py` | Connector outbound provider dispatch executor (new) |
| 3 | `chitu-connector/tests/test_phase3c20_rt_wp3_dispatch.py` | Dispatch contract tests |
| 3 | `crm-extension/tests/test_phase3c20_rt_wp3_dispatch.py` | CRM dispatch orchestration contract tests |
| 4 | `Resources/metadata/entityDefs/AIJob.json` | Add `cancelReasonCode`, `cancelReason` (primary owner RT-WP4) |
| 4 | `Services/AIJobService.php` | Reason-enforcing transition (primary owner RT-WP4) |
| 4 | `Hooks/AIJob/AIJobStatusMutationGuard.php` | Service-owned field additions |
| 4 | `crm-extension/tests/test_phase3c20_rt_wp4_cancel_reason.py` | Contract + negative tests |
| 5 | `Services/AIRetryPolicyService.php` | Retry classifier + executor (primary owner) |
| 5 | `Services/AIJobService.php` | Retry eligibility gate (secondary coordinated touch; §18.1) |
| 5 | `Jobs/AIRetryWorker.php` | Governed AIJob retry execution |
| 5 | `crm-extension/tests/test_phase3c20_rt_wp5_retry.py` | Retry matrix + SendExecution boundary + no-auto-retry tests |
| 6 | `Services/AIIdempotencyReservationService.php` | Reservation lifecycle (primary owner; form per Foundation Review) |
| 6 | `Services/AIDispatchService.php` | Reservation call site (secondary coordinated touch; §18.1) |
| 6 | `Resources/metadata/entityDefs/AIJob.json` | Reservation state fields only if Foundation Review assigns them (secondary; §18.1) |
| 6 | `crm-extension/tests/test_phase3c20_rt_wp6_idempotency.py` | Collision/replay/concurrency tests |
| 7 | `docs/adr/C20_INVARIANT_REGISTRY.md` | Status updates — governance-status action only |
| 7 | `docs/PHASE3C20_RT_WP7_INVARIANT_ACTIVATION_EVIDENCE.md` | Activation evidence record (new) |
| 8 | `docs/PHASE3C20_RT_WP8_RUNTIME_FREEZE.md` | Freeze evidence record (new) |
| 8 | `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION_ADDENDUM.md` | C25 WP2.0 closure addendum (new) |

### 28.1 Allowlist counts

| Metric | Count | Notes |
| --- | --- | --- |
| Allowlist rows | 40 | One row per WP/file assignment in the table above |
| Unique path strings (as written) | 37 | Brace patterns `{en_US,zh_CN}` and `{list,detail}` counted as one string each |
| Unique files if braces expand | 39 | i18n → 2 files; layouts → 2 files |
| Shared coordinated paths | 3 | `AIJobService.php`, `entityDefs/AIJob.json`, `AIDispatchService.php` |

Every file has exactly one primary owning WP. Secondary rows above are
coordinated touches under §18.1, not a second primary owner.

---

## 29. Test Strategy

| Category | Coverage |
| --- | --- |
| Contract | Capability enum; capability/purpose distinction; binding schema; credential-reference boundary; registry rejection codes; AIJob transition contract; AIRequestLog append-only; idempotency identity; retry taxonomy; cancel-reason contract |
| Unit | Registry eligibility; dispatch orchestration; request-log cardinality; retry classifier; backoff; reservation collision; state guards; append-only guards |
| Concurrency | Duplicate requests; simultaneous reservation; retry race; cancel/outbound-dispatch race; duplicate result; crash recovery |
| Boundary | No provider HTTP from CRM (C20-INV-03); no credentials to C25; no C25 binding ownership; no CRM Core mutation; no C22 execution; no score/rank authority (C20-INV-14/16/19/21); no scheduler loop without authorization; AIJob retry does not alter SendExecution; SendExecution retry remains connector-side; AIJob retry re-runs registry eligibility; retry does not select provider in CRM |
| Runtime | Successful dispatch; provider failure; retry; cancellation; content filter; rate limit; exactly-once logging; idempotent replay; controlled recovery |

---

## 30. Commit and Review Strategy

Recommended separate commits:

1. RT-WP0 documentation baseline.
2. RT-WP1 capability/purpose.
3. RT-WP2 ProviderBinding surface.
4. RT-WP3 dispatch/logging.
5. RT-WP4 cancel reason.
6. RT-WP5 retry.
7. RT-WP6 idempotency.
8. RT-WP7 invariant activation.
9. RT-WP8 freeze evidence.

Each implementation work package requires: explicit authorization; scoped
allowlist; implementation; tests; independent review; push; remote HEAD
verification; freeze or exit record. Unfinished work packages are not combined
into one large commit.

---

## 31. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Capability enum addition leaks into routing | Non-routability guard; registry purpose gate; contract tests |
| Binding surface becomes a secret store | Credential reference only; entityAcl `internal`; forbidden-field tests |
| Dispatch produces duplicate provider calls | Attempt claim + reservation + unique log indexes |
| Retry becomes autonomous/outreach | Taxonomy gate; max attempts; operator path; C22 boundary |
| Cancel reason path missing | Guard-enforced reason requirement; negative tests |
| Idempotency reservation drift across retries | Reservation context equality; five-layer identity tests |
| Shared-file conflicts RT-WP4/5/6 | Primary-owner model (§18.1) |
| Provider-health ownership drift | RT-WP2 policy vs RT-WP3 input vs Connector production (§9.3) |
| Reservation form assumed too early | RT-WP6 Foundation Review before persistence implementation |
| C25 consumes an unverified boundary | RT-WP7 independent review + RT-WP8 freeze before C25 |

---

## 32. Entry and Exit Gates

| Work package | Entry gate | Exit gate |
| --- | --- | --- |
| RT-WP0 | Governance freeze unchanged; charter accepted | Independent baseline review PASS |
| RT-WP1 | RT-WP0 exit; no-code scope reconciliation | Existing four capabilities unchanged; non-routable baseline verified; pytest contract evidence rerun or independently reconciled |
| RT-WP2 | RT-WP2 separately authorized AND RT-WP2 Foundation Review PASS | Foundation decisions satisfied exactly; authorized binding set; no secrets; no invocation; no counters; no CRM health probing |
| RT-WP3 | RT-WP1 + RT-WP2 exits; AIJob ACL Foundation Gate PASS for operator-visible dispatch | INV-08 evidence; cardinality proven; no provider SDK in CRM; health-input contract defined |
| RT-WP4 | RT-WP3 stable; §18.1; AIJob ACL Foundation Gate PASS for cancel | Valid-reason cancel; no direct mutation; INV-06 eligible; baseline frozen |
| RT-WP5 | RT-WP3 stable; RT-WP4 baseline frozen; AIJob ACL Foundation Gate PASS for retry | Deterministic retry matrix; SendExecution unchanged; bounded; INV-10 eligible |
| RT-WP6 | RT-WP3 stable; primary baselines frozen; RT-WP6 Foundation Review PASS | One outbound dispatch for concurrent requests; governed stale recovery; INV-11 eligible |
| RT-WP7 | RT-WP3–6 exits; evidence complete | Registry updated by separately authorized governance-status action; evidence pinned |
| RT-WP8 | RT-WP7 exit | Independent freeze review PASS; C25 WP2.0 closure addendum |

---

## 33. Runtime Freeze Criteria

The runtime is freezable when all of the following are verified and
independently reviewed:

- Remote HEAD matches the pinned implementation commit.
- Capability/purpose verified (four values unchanged; new value non-routable).
- Binding surface verified (authorized `allowed_provider_bindings` producer).
- Dispatch, exactly-once logging, retry, idempotency, cancellation, invariant
  activation, and security/credential-custody proofs present.
- Failure matrix exercised.
- No CRM Core mutation; no C22 execution side effects; no C25 provider ownership.
- Independent freeze review PASS.

---

## 34. C25 Dependency Closure

After the RT-WP8 freeze PASS:

- A C25 WP2.0 closure addendum records capability/binding/invariant
  dependencies as resolved.
- C25 WP2.2 does **not** automatically start; C25 still requires separate
  implementation authorization through its own WP2.0 exit gates.
- The C20 boundary remains the sole governed path C25 may consume.

```text
C25 WP2.2 may start: NO
```

---

## 35. Remaining Decision Gates

These are explicit pre-implementation gates, not generic open tasks. They do not
reopen the frozen C20 governance baseline.

| Decision | Classification |
| --- | --- |
| ProviderBinding entity direction | Preferred and conditionally accepted; final confirmation at RT-WP2 Foundation Review |
| Provider-health persistence/cache | RT-WP2 Foundation Review |
| Health-input runtime DTO | RT-WP3 Foundation decision |
| Connector claim durability | RT-WP3 evidence gate |
| Cancel-reason storage | Fully decided: AIJob governed fields |
| AIJob retry ownership | Fully decided with SendExecution boundary clarification |
| Reservation owner | Fully decided: CRM orchestration |
| Reservation persistence form | RT-WP6 Foundation Review |
| Model-selection resolution point | CRM binding policy + Registry eligibility + Connector execution; never C25 |
| AIJob ACL posture | RT-WP3/RT-WP4 Foundation gate |
| INV activation | RT-WP7 separately authorized governance-status action |

---

## 36. Ratification Record

Final Runtime Implementation Charter Ratification Review completed.

| Field | Value |
| --- | --- |
| Review Type | Final Runtime Implementation Charter Ratification Review |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| Date | 2026-08-02 |

### 36.1 Results

| Review item | Result |
| --- | --- |
| Frozen governance boundary | PASS |
| Repository consistency | PASS |
| Shared-file ownership | PASS |
| Dispatch ownership | PASS |
| Provider-health ownership | PASS |
| Retry ownership reconciliation | PASS |
| ProviderBinding Foundation gate | PASS |
| Reservation Foundation gate | PASS |
| AIJob ACL Foundation gate | PASS |
| Work-package sequencing | PASS |
| Failure and test matrices | PASS |
| Remaining BLOCKER/HIGH/MEDIUM findings | NONE |

### 36.2 Authorization (ratification-time)

| Item | Status |
| --- | --- |
| Runtime Charter | RATIFIED |
| RT-WP0 | NOT AUTOMATICALLY AUTHORIZED |
| RT-WP0 may be separately authorized | YES |
| RT-WP1 Scope | NO-CODE — RECONCILED |
| RT-WP1 Evidence | COMPLETE |
| RT-WP1 Exit Review | APPROVED |
| RT-WP1 Administrative Exit | EXITED |
| RT-WP1 Exit | EXITED |
| RT-WP1 Runtime Code | NOT AUTHORIZED — NO CODE-BEARING SCOPE |
| RT-WP2 | NOT AUTHORIZED |
| RT-WP3–RT-WP8 | NOT AUTHORIZED |
| Runtime Code outside separately authorized work packages | NOT AUTHORIZED |
| C20-INV-05–11 activation | NOT AUTHORIZED; remain DEFERRED |
| C25 WP2.2 | NO GO |
| Commit / push / tag | NOT AUTHORIZED |

---

## 37. Final Authorization Matrix

```text
Charter status:
RATIFIED — runtime implementation planning reference only; no work package or code automatically authorized

Any code implementation:
NOT AUTHORIZED
```

| Item | Status |
| --- | --- |
| Phase3C20 Governance | FROZEN |
| Runtime Implementation Charter | RATIFIED |
| RT-WP0 | EXITED |
| RT-WP1 Charter | RATIFIED |
| RT-WP1 Scope | NO-CODE — RECONCILED |
| RT-WP1 Evidence | COMPLETE |
| RT-WP1 Exit Review | APPROVED |
| RT-WP1 Administrative Exit | EXITED |
| RT-WP1 Exit | EXITED |
| RT-WP1 Runtime Code | NOT AUTHORIZED — NO CODE-BEARING SCOPE |
| RT-WP2–RT-WP8 | NOT AUTHORIZED |
| Runtime Code outside separately authorized work packages | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

### 37.1 RT-WP1 Charter Status Log

| Field | Value |
| --- | --- |
| Date | 2026-08-02 |
| Event | RT-WP1 Implementation Charter independently ratified |
| Verdict | RATIFIED WITH INFORMATIONAL NOTES |
| Effect | Charter status synchronized to RATIFIED |
| Non-effect | No implementation authorization granted |

### 37.2 RT-WP1 No-Code Scope Reconciliation Log

| Field | Value |
| --- | --- |
| Date | 2026-08-02 |
| Event | RT-WP1 no-code scope reconciled after independent authorization remediation |
| Classification | `CommercialBrief` is a C25 purpose/output contract, not an approved CompletionCapability |
| Scope | No enum, adapter, registry, ProviderBinding, purpose registry, dispatch, or C25 implementation change is authorized or required by RT-WP1 |
| Evidence | Existing four-value contract, static registry and adapter boundary evidence, and 19 passing C20 unittest boundary/invariant tests |
| Effect | RT-WP1 scope remains NO-CODE — RECONCILED; no-code exit review is now pending |
| Non-effect | RT-WP2–RT-WP8 and C25 WP2.2 remain unauthorized; runtime code remains unauthorized |
| Review reference | `docs/audit/PHASE3C20_RT_WP1_IMPLEMENTATION_CHARTER_RATIFICATION_REVIEW.md` |

### 37.3 RT-WP1 No-Code Evidence Reconciliation Log

| Field | Value |
| --- | --- |
| Date | 2026-08-02 |
| Environment | Existing repository virtual environment `.venv-s01`; Python 3.12.13; pytest 9.1.1 |
| Collection | Focused allowlist collected 66 tests without errors, skips, xfails, or deselection |
| Result | 66 tests passed; 26 subtests passed; existing C20 unittest suite passed 19 tests |
| Static evidence | Four-value enum unchanged; no C25 runtime reference; registry and adapter boundaries remain explicit |
| Reconciliation result | RT-WP1 Scope: NO-CODE — RECONCILED; RT-WP1 Evidence: COMPLETE |
| Subsequent status | Exit Review APPROVED; Administrative Exit EXITED in §37.4 |
| Non-effect | RT-WP1 has no code-bearing scope; RT-WP2–RT-WP8, Runtime Code, and C25 WP2.2 remain unauthorized |
| Evidence record | `docs/audit/PHASE3C20_RT_WP1_NO_CODE_EVIDENCE_RECONCILIATION.md` |

### 37.4 RT-WP1 No-Code Administrative Exit Log

| Field | Value |
| --- | --- |
| Date | 2026-08-03 |
| Event | RT-WP1 No-Code Administrative Exit |
| Review | `docs/audit/PHASE3C20_RT_WP1_NO_CODE_EXIT_REVIEW.md` |
| Verdict | EXIT APPROVED WITH INFORMATIONAL NOTES |
| Effect | RT-WP1 marked EXITED |
| Non-effect | No RT-WP2 authorization; no Runtime Code authorization; no C25 WP2.2 authorization |

```text
Ratification approves the Runtime Charter as a planning and work-package reference only.
```

```text
Ratification does not start RT-WP0 or any later work package.
```

```text
RT-WP0 exited following successful independent exit review.

No runtime implementation is authorized.
```

Frozen runtime state preserved:

```text
COMMERCIAL_BRIEF is not active, not delivered, and not implemented.
```

```text
commercial_brief_generation is not delivered.
```

```text
C20-INV-05 through C20-INV-11 remain DEFERRED.
```

```text
C25 WP2.2 remains NO GO.
```

```text
Any runtime code remains NOT AUTHORIZED.
```

C20 Governance Freeze remains unchanged. This charter does not unfreeze
governance. Runtime implementation cannot modify frozen governance semantics
without a new ADR. No work package starts automatically; each RT-WP requires
separate authorization.

---

## 38. Exact Next Task

RT-WP0 exited; RT-WP1 Charter is RATIFIED and RT-WP1 has EXITED as a no-code
work package. RT-WP2 Charter may be separately authorized. RT-WP2 remains NOT
AUTHORIZED unless and until a separate authorization is issued.

```text
docs/PHASE3C20_RT_WP0_RUNTIME_BASELINE.md
```

Exact next task:

```text
RT-WP2 Charter may be separately authorized.
```

- RT-WP0 is EXITED.
- RT-WP1 Charter is RATIFIED; RT-WP1 Scope is NO-CODE — RECONCILED; RT-WP1 Evidence is COMPLETE; RT-WP1 Exit Review is APPROVED; RT-WP1 Administrative Exit is EXITED.
- No runtime implementation is authorized by this status synchronization.

---

## 39. References

1. `docs/PHASE3C20_CHARTER.md`
2. `docs/PHASE3C20_WP1_EXIT_RECONCILIATION.md`
3. `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
4. `docs/PHASE3C20_WP3_GOVERNANCE_COMPLETION.md`
5. `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`
6. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
7. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
8. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
9. `docs/adr/C20_INVARIANT_REGISTRY.md`
10. `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION.md` (consumer)
11. `docs/PHASE3C25_WP2_0_C20_DEPENDENCY_RESOLUTION_ADDENDUM.md` (consumer)
12. `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (consumer)
13. `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` (consumer)
14. `docs/PHASE3C20_WP3_AI_EXECUTION_CHARTER.md` (evidence)
15. `docs/PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md` (evidence)
16. Live repository: `chitu-connector/chitu_connector/acquisition/providers/` and `crm-extension/files/custom/Espo/Modules/AIPlatform/`

---

*This charter is a planning document. It creates no production file, modifies
no existing file, stages no change, and authorizes no code. Runtime
implementation begins only under a separate, explicit authorization for each
work package.*
