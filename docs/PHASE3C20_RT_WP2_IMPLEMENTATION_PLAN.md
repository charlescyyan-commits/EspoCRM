# Phase3C20 RT-WP2 Implementation Plan

| Field | Value |
| --- | --- |
| Document Type | Implementation plan (planning only — no code, metadata, or test change) |
| Work package | RT-WP2 — ProviderBinding and purpose-policy foundation |
| Status | PLAN — READY FOR IMPLEMENTATION REVIEW |
| Date | 2026-08-03 |
| Governing baseline | `928aa5f734f8d7f643cdb45a7549fed7ada0c400`; RT-WP0 exit `7846f6f5c3d33ecfe161cbe2099521ab00bac365`; RT-WP1 exit `8f11ee4578d4626fa3ae950c9645b4cbcfc6befd` |
| Execution mode | Implementation planning only; repository verification required; no code implementation |
| RT-WP2 Implementation Authorization | AUTHORIZED WITH CONDITIONS (stated current state) |
| RT-WP2 Foundation Review | MANDATORY PRE-IMPLEMENTATION GATE — NOT YET RUN |
| Commit / push / tag | NOT AUTHORIZED by this plan |
| C25 WP2.2 | NO GO |

```text
This plan is a planning document. It creates no production file, modifies no
existing file, stages no change, and authorizes no code. Implementation begins
only under the RT-WP2 implementation authorization and only after the RT-WP2
Foundation Review PASS.
```

---

## 0. Scope, Traceability, and Explicit Exclusions

### 0.1 Plan scope

The plan covers exactly five policy surfaces. Nothing outside these five is
planned:

1. **ProviderBinding CRM policy entity** — the persistence and authorization
   surface that represents one authorized provider candidate and its policy.
2. **Purpose registration contract** — governed, namespaced registration of
   business/use-case identifiers and their validation and change control.
3. **Capability mapping** — every registered purpose maps explicitly to exactly
   one of the existing four-value `CompletionCapability` portfolio
   (`RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`,
   `REPLY_ASSISTANCE`). No fifth value.
4. **Eligibility classification** — deterministic, non-secret classification of
   a supplied candidate as `BOUND`, `UNBOUND`, `DISABLED`,
   `PURPOSE_NOT_REGISTERED`, `CAPABILITY_MISMATCH`,
   `CREDENTIAL_REFERENCE_MISSING`, or `NOT_AUTHORIZED`.
5. **Credential reference provenance** — reference-only custody plus
   configuration-change provenance; never a secret, never an execution ledger.

### 0.2 Scope-to-section traceability

| Scope item | Primary sections |
| --- | --- |
| ProviderBinding CRM policy entity | §3 Entity Design, §5 Metadata Changes, §7 Service Boundary |
| Purpose registration contract | §3.2, §4, §6, §8 |
| Capability mapping | §3.3, §4 |
| Eligibility classification | §3.4, §7.3 |
| Credential reference provenance | §4, §8, §9 |

### 0.3 Explicit exclusions

RT-WP2 implementation is strictly bounded. The following are excluded and must
not appear in any implementation, commit, or evidence:

| Excluded surface | Boundary statement |
| --- | --- |
| Provider execution | No provider invocation, no adapter construction, no transport construction, no model call. |
| Adapter changes | No change to any connector adapter (`completion/adapter.py`, `search`, `enrichment`, `providers/base.py`). |
| Connector changes | No change to `chitu_connector` source (`registry.py`, `capabilities.py`, `base.py`, `taxonomy.py`, `config.py`). |
| Dispatch | No dispatch orchestration, no `AIDispatchService`, no dispatch path, no `allowed_provider_bindings` runtime hand-off to a caller. |
| Retry | No retry classification, scheduling, backoff, or executor. |
| Reservation | No idempotency reservation, lease, attempt claim, or concurrency control. |
| Queue / worker / job | No `Jobs/`, `Api/`, `Controllers/`, scheduler, background work, or queue predicate. |
| Lifecycle | No `AIJob`, `AIRequestLog`, `PromptTemplate`, `ProviderCredential`, `SendExecution`, `AIQualificationInsight` mutation. The binding configuration lifecycle (§3.5) is policy state, not execution lifecycle. |
| CommercialBrief runtime | No `CommercialBrief` creation, mutation, or consumption. |
| C25 workspace | No C25 workspace, UI, route, or provider ownership. |
| Secret handling | No secret resolution, decryption, plaintext, header, session, secret logging, secret export, or secret-bearing fixture. |
| Invariant activation | No `C20_INVARIANT_REGISTRY.md` status change; C20-INV-02/03 remain ACTIVE unchanged; C20-INV-04 through C20-INV-13 remain DEFERRED unchanged. |
| Capability portfolio | No fifth enum member; `COMMERCIAL_BRIEF` not a capability; `commercial_brief_generation` not registered. |
| Parallel authorization | No authorization path outside verified EspoCRM ACL, WorkflowAuthorization, or a verified system-configuration boundary. |

---

## 1. Implementation Objective

Deliver the CRM-side **policy representation** that produces the authorized,
validated provider-binding set required by the Runtime Implementation Charter
§9.5 and ADR-C20-006 §13. The deliverable is a governed `ProviderBinding`
policy entity, a purpose-registration contract, a four-value capability
mapping, a deterministic eligibility classification, and reference-only
credential provenance.

The objective is policy only. It determines **eligibility**, never execution.
No provider is called, no adapter is constructed, no request is dispatched, no
secret is resolved, and no lifecycle or invariant is activated.

Non-goals restated: RT-WP2 does not deliver provider execution, dispatch,
retry, reservation, queueing, worker/job surfaces, AIJob lifecycle ownership,
CommercialBrief runtime, C25 workspace, secret handling, or invariant
activation.

---

## 2. Architecture Position

### 2.1 Position in the frozen chain

The frozen chain (Runtime Charter §6) is unchanged:

```text
CRM policy
→ authorized ProviderBinding set
→ CapabilityRegistry eligibility resolution
→ CRM governed dispatch orchestration
→ Connector outbound provider dispatch
→ Provider adapter / provider HTTP
```

RT-WP2 occupies **the first two nodes only**: the CRM policy layer and the
authorized binding set. Every node to the right of the binding set is outside
RT-WP2 and is owned by later work packages (RT-WP3 dispatch, RT-WP4–RT-WP6,
RT-WP7 activation).

### 2.2 Layer ownership (three-layer policy model)

| Layer | Definition | Owner | RT-WP2 prohibition |
| --- | --- | --- | --- |
| Capability | Member of the four-value `CompletionCapability` portfolio (`RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE`) | C20 portfolio governance | No new value; a purpose does not expand it |
| Purpose | Registered business/use-case identifier | C20 purpose governance + CRM binding policy | No free-form or unregistered runtime purpose |
| Binding | Non-secret configuration relationship: provider identity, credential reference, allowed purpose(s), enabled state, approval, provenance | CRM / AIPlatform policy | Determines eligibility only; never permits an adapter call |

```text
CRM stores policy.
Connector stores live counters and runtime state.
```

### 2.3 Functional responsibilities in scope

| Responsibility | In RT-WP2 | Owned by |
| --- | --- | --- |
| Persist authorized provider-binding policy | YES | `ProviderBindingService` + entity |
| Register purposes and map them to the four-value portfolio | YES | Purpose registration contract (§3.2) |
| Classify a supplied candidate as eligible/ineligible | YES | `ProviderBindingService::classifyEligibility` (§7.3) |
| Produce `allowed_provider_bindings` at dispatch time | NO | RT-WP3 dispatch orchestration |
| Evaluate the binding set against the registry | NO | Frozen connector `CapabilityRegistry` |
| Resolve credentials | NO | Connector custody boundary |
| Probe or cache provider health | NO | Not introduced (Foundation Review decision #10 default) |
| Invoke a provider | NO | Later RT-WPs / connector |

---

## 3. Entity Design

### 3.1 Decision: one CRM policy entity

**Default (preferred) direction:** `ProviderBinding` as a CRM policy entity
under `Espo\Modules\AIPlatform`, matching existing AIPlatform entity
conventions and ADR-C20-006 §13 / Runtime Charter §9.1 and §21.1. The
Foundation Review (gate 0) confirms entity versus internal policy artifact; the
plan proposes entity.

- Entity type: `ProviderBinding`
- Scope flags (proposed, Foundation Review confirms): `entity: true`,
  `object: false`, `tab: false`, `acl: true`, `aclPortal: false`,
  `customizable: false`, `importable: false`, `module: "AIPlatform"`,
  `type: "Base"`, `statusField: null` (binding status is a governed,
  service-owned field, not the generic status-field machinery).
- Entity/artifact budget: **one** entity. No separate purpose entity is
  proposed (see §3.2). Any second entity requires an allowlist expansion under
  separate authority.

### 3.2 Purpose registration contract

Purpose registration is a **governed, explicit contract**, not a free-form
registry. The planned representation lives on the binding surface
(`allowedPurposes`) and is validated by the service against a governed purpose
catalog. No separate purpose entity is created in RT-WP2.

| Design question | Required decision |
| --- | --- |
| Identifier grammar | `^[a-z][a-z0-9_]{0,63}$` — snake_case, namespaced, human-reviewable; never equal to a `CompletionCapability` value, a C25 entity name, or an action key |
| Registration owner | Named C20 purpose-governance owner and an approval role distinct from generic record-edit permission |
| Capability mapping | Every registered purpose explicitly maps to exactly one of the four existing values (§3.3) |
| Multiplicity | One purpose → one capability; no implicit many-to-many mapping |
| Validation point | Fail-closed validation at the service boundary before a binding is accepted or before any eligibility classification is returned |
| Change control | Approval + effective time + revocation + provenance evidence (`approvedBy`, `approvedAt`, `provenanceReference`) |
| Tenant and ACL boundary | Verified EspoCRM tenancy/ACL semantics before access design (Foundation Review decision #4) |
| Audit visibility | Safe, non-secret configuration-change fields and authorized readers only |
| Extensibility | Deliberate, governance-registered purposes only; no generic registry without repository evidence |

**Registration state:** the initial registered-purpose set is empty pending C20
purpose-governance registration. Implementation delivers the contract
mechanism and validation; it does not pre-register any purpose.
`commercial_brief_generation` is **not** registered by RT-WP2 (proposed only;
ADR-C20-005/006). Test fixtures register test-scoped purposes only.

### 3.3 Capability mapping

The four-value `CompletionCapability` portfolio is authoritative and frozen
(ADR-C20-005; `chitu-connector/.../completion/base.py`). The generic registry
family `Capability.COMPLETION` (with `SEARCH`, `ENRICHMENT`, `COMPLETION`) is
the registry-level function (Runtime Charter §9.2).

| Layer | Values | RT-WP2 rule |
| --- | --- | --- |
| Registry family (binding `supportedCapabilities`) | `SEARCH`, `ENRICHMENT`, `COMPLETION` | Stored on the binding; validated against the three-value generic family |
| Completion portfolio (purpose target) | `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE` | Every registered purpose maps to exactly one; exhaustive, unchanged |
| `COMMERCIAL_BRIEF` | Not a capability | Not delivered; no fifth value |
| `commercial_brief_generation` | Not a registered purpose | Not registered |

Purpose → capability mapping is a **governed 1:1 contract**. The mapping is
recorded as a service-owned validation rule (purpose catalog plus a fixed
purpose→portfolio table) and is enforced fail-closed. The exact mapping table
entries (purpose IDs) require C20 purpose-governance approval during
implementation; the four target values are fixed by this plan.

### 3.4 Eligibility classification

`ProviderBindingService::classifyEligibility(providerId, capability, purpose)`
returns exactly one of the RT-WP2 Charter §6 policy-only classifications. It is
deterministic, explicit, non-secret, auditable, and fails closed.

| Classification | Meaning | Checks (evaluated in order, first failure wins) |
| --- | --- | --- |
| `NOT_AUTHORIZED` | Caller lacks classification/read authorization or request is cross-tenant | ACL check first |
| `UNBOUND` | No `ProviderBinding` exists for the supplied provider identity | Binding lookup |
| `DISABLED` | Binding exists but is not ACTIVE/`enabled=false` | `status` + `enabled` |
| `PURPOSE_NOT_REGISTERED` | Purpose absent from the governed catalog or from the binding's `allowedPurposes` | Purpose catalog + `allowedPurposes` |
| `CAPABILITY_MISMATCH` | Binding `supportedCapabilities` lacks the generic family, or the purpose's mapped portfolio value differs from the requested one | Capability family + purpose mapping |
| `CREDENTIAL_REFERENCE_MISSING` | Binding has no non-empty `credentialReference` | Credential reference presence |
| `BOUND` | All policy checks pass | — |

`BOUND` means **policy-configured**. It does not state that dispatch is
authorized, a provider call is permitted, or retry/reservation mechanisms
exist. The classifier never returns `PROVIDER_TIMEOUT`, `DISPATCH_FAILED`,
`RETRY_PENDING`, `RESERVATION_CONFLICT`, or `EXECUTION_COMPLETED`, and it never
calls the connector, resolves credentials, or checks live health.

### 3.5 Binding configuration lifecycle

The administrative lifecycle is `DRAFT → ACTIVE → DISABLED/REVOKED`
(`REVOKED` terminal; `DISABLED` reversible only by re-approval). These are
**configuration states, not execution states** — there is no dispatched,
running, completed, failed, retried, reserved, leased, queued, or cancelled
state. A binding is eligible only when `ACTIVE` and `enabled = true`.

---

## 4. Field Contract

For every planned field: required/optional, platform-owned, serializable,
logged, generally readable, and secret-leakage exposure. Foundation Review
confirms the exact EspoCRM metadata form (the RT-WP2 Charter §3 selects no
storage form; this plan proposes one).

| Field | Type | Required | Immutable after create | Service-owned | Generally readable | Secret exposure |
| --- | --- | --- | --- | --- | --- | --- |
| `name` | varchar 255 | YES | NO | NO | YES | NONE |
| `providerId` | varchar 100 | YES | YES | NO | YES | NONE — policy identifier only |
| `adapterType` | varchar 100 | YES | YES | NO | YES | NONE |
| `priority` | int | YES (default 0) | NO | NO | YES | NONE — deterministic ordering input |
| `enabled` | bool | YES (default false) | NO | YES (write gated) | YES | NONE |
| `status` | varchar/enum (`DRAFT`,`ACTIVE`,`DISABLED`,`REVOKED`) | YES | — | YES (transitions only via service) | YES | NONE — configuration state |
| `supportedCapabilities` | multiEnum of `SEARCH`,`ENRICHMENT`,`COMPLETION` | YES | NO | YES (write gated) | YES | NONE |
| `allowedPurposes` | multiEnum/array of registered purpose IDs | YES | NO | YES (write gated) | YES | NONE |
| `credentialReference` | varchar 255 | YES | YES | NO | NO — `internal: true` | REFERENCE ONLY; never a value |
| `approvedBy` | link User | NO (empty in DRAFT) | NO | YES | Restricted | NONE |
| `approvedAt` | datetime | NO | NO | YES | Restricted | NONE |
| `provenanceReference` | varchar 255 | NO | NO | YES | Restricted | NONE |
| `description` | text | NO | NO | NO | YES | NONE |
| `createdBy`/`createdAt`/`modifiedBy`/`modifiedAt` | standard | — | — | — | Standard EspoCRM | NONE |

Credential-reference provenance: `credentialReference` points to externally
held credential custody (the existing `ProviderCredential` reference surface or
connector custody). CRM never copies, resolves, exports, serializes, logs,
exposes through exceptions, or places a secret in a fixture. Audit records
contain only non-secret references, configuration decisions, and safe
eligibility results (Charter §6).

Health policy fields: **excluded from the base field contract**. Runtime
Charter §21.1 decision #10 (health-policy/reference fields) is a Foundation
Review decision; the default is no last-known health classification, no live
counters, no probing (Charter §4.1 candidate list omits health).

---

## 5. Metadata Changes

All paths under `crm-extension/files/custom/Espo/Modules/AIPlatform/`.
Exact form confirmed by Foundation Review before implementation.

| # | File | Change | Rationale |
| --- | --- | --- | --- |
| M1 | `Resources/metadata/entityDefs/ProviderBinding.json` | NEW — entity definition | Field contract §4 |
| M2 | `Resources/metadata/scopes/ProviderBinding.json` | NEW — scope flags | §3.1; `aclPortal:false`, `tab:false` |
| M3 | `Resources/metadata/aclDefs/ProviderBinding.json` | NEW — ACL definition | ACL model §6 |
| M4 | `Resources/metadata/entityAcl/ProviderBinding.json` | NEW — `credentialReference` `internal:true` | Reference-only custody |
| M5 | `Resources/metadata/app/acl.json` | MODIFY — add `ProviderBinding` scopeLevel | Admin-only surface |
| M6 | `Resources/metadata/app/aclPortal.json` | MODIFY — Portal denial | `scopeLevel:false` |
| M7 | `Resources/metadata/app/adminPanel.json` | MODIFY — provider surface entry only if Foundation Review approves | Minimal admin surface |
| M8 | `Services/ProviderBindingService.php` | NEW — save-option gated CRUD + classify | Service boundary §7 |
| M9 | `Services/ProviderBindingMutationSaveOption.php` | NEW — authorization token | Save-option model |
| M10 | `Hooks/ProviderBinding/ProviderBindingMutationGuard.php` | NEW — governed-field immutability | Guard strategy §8 |
| M11 | `Resources/i18n/en_US/ProviderBinding.json` | NEW — i18n | UI labels |
| M12 | `Resources/i18n/zh_CN/ProviderBinding.json` | NEW — i18n | UI labels |
| M13 | `Resources/layouts/ProviderBinding/list.json` | NEW — layout | List surface (reference excluded fields) |
| M14 | `Resources/layouts/ProviderBinding/detail.json` | NEW — layout | Detail surface (reference excluded fields) |

No change to: `AIJob`, `AIRequestLog`, `PromptTemplate`, `ProviderCredential`
entityDefs/metadata, `module.json`, `manifest.json`, `Binding.php`, or any
connector file.

---

## 6. ACL Model

Reuse verified EspoCRM ACL, WorkflowAuthorization, and system-configuration
conventions (Charter §7). No parallel authorization path.

| Surface | Proposed value | Precedent |
| --- | --- | --- |
| `app/acl.json` `scopeLevel` | `ProviderBinding: false` (non-admin) | ProviderCredential/PromptTemplate/AIRequestLog |
| `app/acl.json` `adminMandatory` | `create: yes`; `read: all`; `edit: all`; `delete: no` | PromptTemplate/AIRequestLog pattern |
| `app/aclPortal.json` | `scopeLevel: false` — Portal denied | ProviderCredential etc. |
| `entityAcl/ProviderBinding.json` | `credentialReference.internal: true` | ProviderCredential |
| `scopes/ProviderBinding.json` | `acl:true`, `aclPortal:false`, `tab:false` | ProviderCredential |

Least-privilege separation (Charter §7): binding **creation**, **approval**,
**enabling/disabling**, **revocation**, and **read** are distinct governed
operations. Generic record-edit permission is never treated as permission to
approve, modify a governed field, or grant policy access. Approval is a
service-owned operation requiring `ProviderBindingMutationSaveOption` and a
distinct approval role; `approvedBy`/`approvedAt` are written only by the
service. `delete` is `no` — revocation is the `REVOKED` status transition, so
provenance survives.

---

## 7. Service Boundary

### 7.1 `ProviderBindingService`

`Services/ProviderBindingService.php` — the sole governed writer of
ProviderBinding policy. It parallels the `AIJobService` /
`AIRequestLogService` create-only/transition service pattern and the
`AIJobStatusMutationSaveOption` token pattern.

| Operation | Behavior |
| --- | --- |
| `create(array $attributes)` | Validates allowlisted fields (§4), capability family values, purpose registration, credential reference format (non-secret); initial state `DRAFT`, `enabled=false`; requires `ProviderBindingMutationSaveOption`; ACL `create` check |
| `approve(id)` | `DRAFT → ACTIVE`; writes `approvedBy`, `approvedAt`, `provenanceReference`; requires approval role + save option |
| `updatePolicy(id, attributes)` | Governed-field writes (`priority`, `enabled`, `supportedCapabilities`, `allowedPurposes`) only via service + save option |
| `disable(id)` / `revoke(id)` | `ACTIVE → DISABLED` / `→ REVOKED` (terminal); `enabled=false`; provenance retained |
| `classifyEligibility(providerId, capability, purpose)` | Returns one of the seven classifications (§3.4); non-secret, auditable, fail-closed; no connector call |

The service **never** invokes a provider, constructs an adapter, calls the
registry, resolves credentials, or writes an execution/log surface.

### 7.2 `ProviderBindingMutationSaveOption`

A per-save authorization marker (`ProviderBindingMutationSaveOption` constant),
mirroring `AIJobStatusMutationSaveOption`. Its scope is one EntityManager save
operation. It does not authorize dispatch, retry, or external execution.

### 7.3 Eligibility classifier contract

`classifyEligibility` is the policy-only resolver permitted by Charter §6. It
accepts a candidate (provider identity + capability + purpose) and returns the
first-failure classification per §3.4. Result and classification trace are
non-secret and auditable. `BOUND` is returned only when every policy check
passes and never grants execution authority.

---

## 8. Mutation Guard Strategy

`Hooks/ProviderBinding/ProviderBindingMutationGuard.php` implements
`Espo\Core\Hook\Hook\BeforeSave` (parallels `AIJobStatusMutationGuard`).

| Rule | Enforcement |
| --- | --- |
| Immutable-after-create fields | `providerId`, `adapterType`, `credentialReference` — any change rejected without an authorized save option |
| Service-owned fields | `status`, `enabled`, `approvedBy`, `approvedAt`, `provenanceReference` — written only under `ProviderBindingMutationSaveOption`; generic save rejected with `Forbidden` |
| Status transitions | Only the service may transition status; guard rejects direct status mutation |
| Creation state | New records must initialize to `DRAFT` with `enabled=false` and empty approval fields |
| Credential reference | Write-only; entityAcl `internal:true`; guard blocks reads through generic edit |
| Admin no-bypass | Guard applies to every role, including admin |

The guard is a persistence boundary, not an execution or authorization
replacement: it never dispatches, schedules, or contacts an external system.

---

## 9. Security Model

| Requirement | Enforcement intent | Evidence |
| --- | --- | --- |
| No secrets in CRM entities | `credentialReference` only; entityAcl `internal:true` | Forbidden-field contract tests |
| No credential resolution from CRM | Reference-only custody; resolution stays in connector custody | Static + contract evidence |
| No secret in logs/errors/exports/fixtures | Safe failure messages; reference-only audit fields | Log/serialization/error/fixture scan |
| No provider invocation from CRM | No adapter construction, no outbound HTTP (C20-INV-03 unchanged) | Provider-isolation boundary tests |
| No fallback/default inference | Explicit approved binding only; fail-closed conflict rule | Multiple-candidate negative test |
| No hidden environment binding | No environment-derived policy input | Source/boundary review |
| Purpose/capability spoofing | Explicit registered mapping + validation | Mapping + mismatch evidence |
| Cross-tenant access | Verified EspoCRM tenancy/ACL boundary | Tenant-isolation test |
| Unauthorized edits | Distinct approval + write permissions | Actor/time/provenance evidence |
| Audit tamper | Protected provenance via service-owned fields + guard | Mutation evidence |
| Parallel authorization | None — reuse EspoCRM ACL/WorkflowAuthorization/system configuration | ACL review |
| Portal escalation | `aclPortal:false` | Portal-denial test |
| C25 bypass | C25 owns no policy/selection/lifecycle | C25-boundary regression |

---

## 10. Test Strategy

New test file: `crm-extension/tests/test_phase3c20_rt_wp2_provider_binding.py`
(canonical `pytest -q`; `pytest.ini` testpaths include `crm-extension/tests`
with `pythonpath chitu-connector`). No connector file is modified.

| Category | Coverage |
| --- | --- |
| Contract | Field contract §4; capability portfolio exactly four values; purpose registration grammar/validation; purpose→capability 1:1 mapping; binding lifecycle transitions (`DRAFT→ACTIVE→DISABLED/REVOKED`); credential-reference boundary; `classifyEligibility` matrix (all seven outcomes) |
| Negative | Secret-bearing field rejected; generic edit rejected for governed fields; direct status mutation rejected; `REVOKED` ineligible; unregistered purpose rejected; unknown capability rejected; empty `credentialReference` rejected as `CREDENTIAL_REFERENCE_MISSING`; Portal denied; delete denied |
| No-execution | No provider call, no adapter construction, no registry call from CRM service, no dispatch, no retry, no reservation — each asserted as an absence/boundary test |
| Boundary | No outbound HTTP from PHP (C20-INV-03 unchanged); no connector change; no adapter change; no AIJob/AIRequestLog/PromptTemplate/ProviderCredential change; C25 has no binding/policy ownership; `C20_INVARIANT_REGISTRY.md` statuses unchanged |
| Cross-surface | A CRM-surface-shaped fixture binding is constructed in-test and consumed by the frozen connector `CapabilityRegistry` to prove the persisted shape matches the registry's `ProviderBinding` contract (Runtime Charter §9.5) |

No test performs a network call, resolves a secret, or produces an execution
result.

---

## 11. File Allowlist Mapping

The allowlist is exact and drawn from Runtime Charter §28 (RT-WP2 rows), with
Foundation-Review-confirmed metadata form. It excludes C21–C25, dispatch,
retry, reservations, AIJob changes, deployment changes, secrets, adapter
changes, and capability-enum expansion.

| # | File | Role | Primary owner |
| --- | --- | --- | --- |
| 1 | `Resources/metadata/entityDefs/ProviderBinding.json` | Entity definition | RT-WP2 |
| 2 | `Resources/metadata/scopes/ProviderBinding.json` | Scope | RT-WP2 |
| 3 | `Resources/metadata/aclDefs/ProviderBinding.json` | ACL definition | RT-WP2 |
| 4 | `Resources/metadata/entityAcl/ProviderBinding.json` | `credentialReference` write-only | RT-WP2 |
| 5 | `Resources/metadata/app/acl.json` | Add scopeLevel | RT-WP2 |
| 6 | `Resources/metadata/app/aclPortal.json` | Portal denial | RT-WP2 |
| 7 | `Resources/metadata/app/adminPanel.json` | Provider surface entry (if approved) | RT-WP2 |
| 8 | `Services/ProviderBindingService.php` | Save-option gated CRUD + classify | RT-WP2 |
| 9 | `Services/ProviderBindingMutationSaveOption.php` | Authorization token | RT-WP2 |
| 10 | `Hooks/ProviderBinding/ProviderBindingMutationGuard.php` | Governed-field immutability | RT-WP2 |
| 11 | `Resources/i18n/en_US/ProviderBinding.json` | i18n | RT-WP2 |
| 12 | `Resources/i18n/zh_CN/ProviderBinding.json` | i18n | RT-WP2 |
| 13 | `Resources/layouts/ProviderBinding/list.json` | Layout (reference excluded) | RT-WP2 |
| 14 | `Resources/layouts/ProviderBinding/detail.json` | Layout (reference excluded) | RT-WP2 |
| 15 | `crm-extension/tests/test_phase3c20_rt_wp2_provider_binding.py` | Contract tests | RT-WP2 |

Default path base:
`crm-extension/files/custom/Espo/Modules/AIPlatform/`. Allowlist count: 15
rows; no shared files with any other RT-WP. Nothing in this plan creates or
modifies any file.

---

## 12. Implementation Sequence

| Step | Deliverable | Gate |
| --- | --- | --- |
| 0 | **RT-WP2 Foundation Review** — documentation + repository verification; decide the 16 items of Runtime Charter §21.1 (entity vs artifact; exact field allowlist; scope flags; Record API behavior; generic CRUD boundary; ACL/admin behavior; Portal denial; credential-reference handling; provider/model policy fields; health policy/reference fields; live-counter exclusion; mutation guard; save-option/token model; rebuild/install convention; entity/artifact budget; exact implementation allowlist) | PASS required before any metadata/service/guard/rebuild |
| 1 | Metadata M1–M7 (entityDefs, scopes, aclDefs, entityAcl, app/acl, app/aclPortal, adminPanel if approved) | Schema review |
| 2 | Service M8 + save option M9 | Service review |
| 3 | Guard M10 | Guard review |
| 4 | i18n M11–M12 + layouts M13–M14 | UI review |
| 5 | Tests (file 15) — contract, negative, no-execution, boundary, cross-surface | Test review |
| 6 | Independent implementation review against this plan and §13 gates | Review PASS |
| 7 | Commit/push/tag | NOT AUTHORIZED by this plan — separate authorization required |

No step is parallelized with another RT-WP. No file is shared with another
RT-WP.

---

## 13. Review Gates

| Gate | Requirement |
| --- | --- |
| G1 Foundation Review | Independent review PASS on all Runtime Charter §21.1 decisions |
| G2 This plan | Independent plan review PASS — scope bounded, exclusions honored, allowlist exact, no authorization escalation |
| G3 Authorization conditions | RT-WP2 implementation authorization conditions satisfied (stated as AUTHORIZED WITH CONDITIONS) |
| G4 Implementation | Independent implementation review PASS with no BLOCKER/HIGH/MEDIUM finding |
| G5 Security | No secret leakage; no provider invocation; no live counters; no CRM health probing; C20-INV-02/03 unchanged ACTIVE |
| G6 Boundary | No connector/adapter change; no dispatch/retry/reservation/queue/worker/job; no AIJob lifecycle; no C25 surface; C25 WP2.2 NO GO retained |
| G7 Invariants | `C20_INVARIANT_REGISTRY.md` statuses unchanged (INV-04–13 DEFERRED) |

---

## 14. Exit Criteria

RT-WP2 may be considered implemented only when all of the following are
verified and independently reviewed:

1. All RT-WP2 Foundation Review decisions are satisfied exactly.
2. CRM produces an authorized, validated binding set; a fixture-derived binding
   is consumable by the frozen `CapabilityRegistry` contract (no dispatch).
3. The purpose-registration contract validates against the governed catalog;
   no free-form purpose is accepted; `commercial_brief_generation` is not
   registered; the four-value portfolio is unchanged.
4. `classifyEligibility` returns only the seven allowed classifications and
   never an execution state.
5. `credentialReference` remains reference-only: no secret value, resolved
   value, header, or session appears in CRM records, logs, errors, exports, or
   fixtures.
6. No provider invocation, no adapter construction, no connector change, no
   dispatch, retry, reservation, queue, worker, or job surface exists.
7. No `AIJob`, `AIRequestLog`, `PromptTemplate`, `ProviderCredential`, or
   lifecycle change; no invariant activation; C20-INV-02/03 unchanged ACTIVE;
   INV-04–13 unchanged DEFERRED.
8. C25 WP2.2 remains NO GO; C25 has no binding/policy ownership.
9. Contract, negative, no-execution, boundary, and cross-surface tests pass.
10. Independent implementation review PASS; no BLOCKER/HIGH/MEDIUM finding.

Exit from RT-WP2 requires a separately authorized exit review; this plan does
not claim exit or release later work packages (RT-WP3–RT-WP8 remain NOT
AUTHORIZED).

---

## Final Decision

```text
Implementation Plan:
READY FOR IMPLEMENTATION REVIEW
```

Rationale: all governing authorities (RT-WP2 Implementation Charter RATIFIED,
Runtime Implementation Charter RATIFIED, ADR-C20-005/006/007 RATIFIED, C20
Invariant Registry unchanged) are internally consistent; the scope is exactly
bounded to the five policy surfaces; the exclusions are explicit and complete;
the allowlist is exact and drawn from the ratified Runtime Charter §28; and the
mandatory pre-implementation gates (RT-WP2 Foundation Review, authorization
conditions, independent implementation review) are preserved. No BLOCKER
condition exists in this plan.

`READY FOR IMPLEMENTATION REVIEW` means the plan is complete and internally
consistent. It does **not** release implementation. Implementation remains
gated on: the stated RT-WP2 implementation authorization conditions, the
RT-WP2 Foundation Review PASS, and independent review of this plan.

```text
Next Task:
Phase3C20 RT-WP2 Implementation Plan Independent Review
```

---

## References

1. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md` (RATIFIED)
2. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (RATIFIED)
3. `docs/audit/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER_REVIEW.md` (PASS WITH INFORMATIONAL NOTES)
4. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
5. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
6. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
7. `docs/adr/C20_INVARIANT_REGISTRY.md`
8. `docs/PHASE3C20_RT_WP0_RUNTIME_BASELINE.md`
9. `docs/PHASE3C20_RT_WP1_IMPLEMENTATION_CHARTER.md`
10. Live repository: `chitu-connector/chitu_connector/acquisition/providers/registry.py`,
    `.../completion/base.py`, and
    `crm-extension/files/custom/Espo/Modules/AIPlatform/` (ProviderCredential
    metadata, `app/acl.json`, `app/aclPortal.json`, `AIJobService`,
    `AIJobStatusMutationSaveOption`, `AIJobStatusMutationGuard`,
    `AIRequestLogService`)

*This plan is a planning document. It creates no production file, modifies no
existing file, stages no change, and authorizes no code.*
