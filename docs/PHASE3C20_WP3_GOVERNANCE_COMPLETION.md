# Phase3C20 WP3 Governance Completion Package

| Field | Value |
| --- | --- |
| Status | RATIFIED — WP3 governance complete and exited; implementation not authorized |
| Date | 2026-08-02 |
| Work Package | Phase3C20 WP3 |
| Implementation Authorization | None |
| C25 Generation Gate | NO GO pending external C20 delivery and verification |

## 1. Purpose

This package completes the remaining C20 governance analysis requested for Phase3C25.

It resolves governance placement and ownership questions.

It does not resolve runtime implementation gaps.

It does not activate any runtime surface.

It does not modify C20 runtime.

It does not modify connectors.

It does not modify registry.py.

It does not modify AIJob.

It does not modify AIRequestLog.

It does not authorize C25 implementation.

Nothing in this package authorizes implementation.

## 2. Deliverables

| Deliverable | Document | Result |
| --- | --- | --- |
| Completion capability portfolio | ADR-C20-005 | RATIFIED — governance direction approved; `COMMERCIAL_BRIEF` remains a future extension only, not an active enum value |
| Provider binding governance | ADR-C20-006 | RATIFIED — ownership chain and purpose rejection boundaries approved; runtime not delivered |
| Invariant activation plan | ADR-C20-007 | RATIFIED — INV-05 through INV-11 readiness classifications accepted; all remain DEFERRED |
| Completion package | This document | RATIFIED / EXITED — matrices, roadmap, owners, and future gates consolidated |

## 3. Repository Verification

Repository inspection preceded every governance conclusion in this package.

The connector capability enum was inspected.

The capability registry was inspected.

`registry.py` was inspected.

AIJob entity metadata was inspected.

AIRequestLog entity metadata was inspected.

PromptTemplate entity metadata was inspected.

AIJobService was inspected.

AIRequestLogService was inspected.

PromptTemplateService was inspected.

AIJob and AIRequestLog guard surfaces were inspected.

The connector boundary contract was inspected.

Controlled registry integration fixtures were inspected.

The C20 invariant registry was inspected.

### 3.1 Verified Repository Facts

| Surface | Verified fact | Governance meaning |
| --- | --- | --- |
| Capability enum | SEARCH, ENRICHMENT, COMPLETION are the only declared families | No new capability family is ratified here |
| CapabilityRegistry | Resolves only pre-registered descriptors against CRM-supplied bindings | Registry is an eligibility evaluator, not a dispatcher |
| ProviderBinding value | Carries capability support, allowed purposes, health, priority, and credential reference | Binding eligibility is policy data |
| `allowed_provider_bindings` | Required request input | Registry cannot select an unlisted provider |
| `allowed_purposes` | Binding-level policy set | Registry can reject a disallowed purpose deterministically |
| AIJob | Contains capability, purpose, status, attempt count, and idempotency key | A lifecycle record surface exists but is not a dispatch runtime |
| AIRequestLog | Captures per-attempt provider/model/token/cost/latency/template provenance | Evidence shape exists but exactly-once dispatch linkage remains incomplete |
| PromptTemplate | Has version, hash, and referenced-version immutability surface | Version governance exists pending activation evidence |
| ConnectorBoundary | Connector-owned execution port outside CRM | CRM and C25 must not perform provider I/O |

## 4. Completion Capability Decision

The repository already contains an authoritative `CompletionCapability` enum. Its authoritative comment defines it as the exhaustive, ratified `CompletionProvider` capability portfolio, with four ratified values: `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`.

The separate generic `Capability.COMPLETION` registry family remains the higher-level provider-registry capability family. It is not a replacement for the authoritative `CompletionCapability` portfolio.

The repository does not have a `COMMERCIAL_BRIEF` `CompletionCapability` value. CommercialBrief is therefore evaluated as a proposed future extension of the existing `CompletionCapability` portfolio, not as the creation of a new portfolio or capability family.

The repository accepts a separate purpose string in the capability-resolution request. The matching proposed purpose identifier is `commercial_brief_generation`.

### 4.0 Four-Layer Terminology Matrix

These identifiers are related but are not interchangeable:

| Layer | Canonical identifier | Status in this package |
| --- | --- | --- |
| Completion capability candidate | `COMMERCIAL_BRIEF` | PROPOSED; not in the enum; not ratified; not active |
| Provider-binding purpose ID | `commercial_brief_generation` | PROPOSED; evaluated only against `ProviderBinding.allowed_purposes` after future delivery |
| Domain artifact / entity name | `CommercialBrief` | C25 commercial-intelligence artifact; not a capability; not a purpose |
| Capability Registry family | `Capability.COMPLETION` | Existing generic registry family; distinct from the `CompletionCapability` portfolio |

```text
CompletionCapability.COMMERCIAL_BRIEF  — future enum member only if separately ratified and implemented
commercial_brief_generation            — corresponding proposed ProviderBinding purpose ID
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

Do not use `COMMERCIAL_BRIEF` as an `allowed_purposes` value.

Do not describe `commercial_brief_generation` as a current `CompletionCapability` enum member.

The capability candidate and purpose ID require separate but coordinated C20 approval and delivery.

Neither identifier is active.

Neither identifier authorizes a binding, a dispatch, or a provider call.

C25 cannot ratify either C20 identifier.

### 4.1 Capability Portfolio Matrix

| Portfolio item | Functional family | Owner | Status | C25 effect |
| --- | --- | --- | --- | --- |
| RESEARCH_EVIDENCE | `CompletionCapability` portfolio | C20 governance | Existing ratified value | No authority granted to C25 |
| QUALIFICATION_INSIGHT | `CompletionCapability` portfolio | C20 governance | Existing ratified value | No authority granted to C25 |
| DRAFT_ASSISTANCE | `CompletionCapability` portfolio | C20 governance | Existing ratified value | Cannot be assumed to cover CommercialBrief |
| REPLY_ASSISTANCE | `CompletionCapability` portfolio | C20 governance | Existing ratified value | No authority granted to C25 |
| COMMERCIAL_BRIEF | Proposed `CompletionCapability` portfolio extension | C20 governance | PROPOSED | Requires independent C20 governance approval and binding delivery |

### 4.2 Portfolio Decision Rules

The authoritative `CompletionCapability` portfolio remains bounded and is distinct from the generic `Capability.COMPLETION` registry family.

Business purposes remain separate from capability families; a future CommercialBrief enum extension does not itself register or activate a purpose.

Provider eligibility remains binding-specific.

No purpose is valid merely because a capability family exists.

No provider is eligible merely because a purpose is proposed.

No C25 service may infer eligibility.

No C25 service may change the capability portfolio.

## 5. Provider Binding Governance

The future completion chain is governed in one direction.

```text
CompletionCapability
        ↓
Binding Eligibility
        ↓
allowed_provider_bindings
        ↓
ProviderBinding
        ↓
Connector
```

The chain begins with a C20-governed capability family.

The chain then evaluates CRM-owned policy inputs.

The chain ends at connector-owned runtime execution only after a separate dispatch decision.

CommercialBrief is not a link owner in this chain.

### 5.1 Provider Binding Matrix

| Check | Source of truth | Registry result when absent or false | Implementation status |
| --- | --- | --- | --- |
| Binding enabled | CRM ProviderBinding policy | `PROVIDER_DISABLED` | Policy persistence surface not delivered by this package |
| Adapter registration | Connector registry descriptor | `ADAPTER_NOT_REGISTERED` | Controlled descriptor mechanism exists |
| Adapter-type agreement | Binding plus registration | `ADAPTER_TYPE_MISMATCH` | Controlled evaluation exists |
| Binding capability support | ProviderBinding policy | `BINDING_CAPABILITY_UNSUPPORTED` | Controlled evaluation exists |
| Adapter capability support | Registration descriptor | `ADAPTER_CAPABILITY_UNSUPPORTED` | Controlled evaluation exists |
| Purpose eligibility | `allowed_purposes` | `PURPOSE_NOT_ALLOWED` | Controlled evaluation exists |
| Credential reference | CRM custody metadata | `MISSING_CREDENTIAL_REFERENCE` | No custody implementation authorized here |
| Credential availability | CRM-supplied availability map | `CREDENTIAL_UNAVAILABLE` | No custody implementation authorized here |
| Provider health | CRM-supplied health input | `PROVIDER_UNHEALTHY` or `PROVIDER_HEALTH_UNKNOWN` | Registry never probes health |

### 5.2 Purpose Matrix

| Concern | Owner | Required action | Prohibited CommercialBrief action |
| --- | --- | --- | --- |
| Purpose vocabulary | C20 governance | Ratify any new purpose | Naming a C20 capability or purpose as binding policy |
| Binding purpose list | CRM policy | Populate `allowed_purposes` | Editing allowed purposes |
| Purpose evaluation | CapabilityRegistry | Compare requested purpose to binding policy | Bypassing `PURPOSE_NOT_ALLOWED` |
| Provider selection | CapabilityRegistry within authorized candidates | Deterministically select eligible descriptor | Selecting a provider directly |
| Routing | C20 registry/policy boundary | Return selection evidence | Constructing routes or adapters |
| Dispatch | Connector-owned runtime | Invoke a separately authorized adapter | Invoking provider I/O |

## 6. Ownership Matrix

| Layer | Owns exactly one responsibility | Does not own |
| --- | --- | --- |
| CRM | ProviderBinding policy, ACL, credential references, and authorized candidate set | Connector execution |
| Capability Registry | Deterministic evaluation of the submitted candidate set | Discovery, secret custody, health probing, or dispatch |
| Connector | Adapter construction and execution after authorization | CRM policy and business lifecycle authority |
| Provider | External service response | CRM capability governance |
| AIJob | Governed execution lifecycle record | Provider selection or connector dispatch implementation |
| AIRequestLog | Immutable per-attempt evidence | Dispatch orchestration |
| PromptTemplate | Versioned prompt provenance | Provider routing or purpose approval |
| CommercialBrief | Future governed consumer of a result | Capability names, bindings, routing, dispatch, and credentials |

## 7. Invariant Activation Summary

The C20 invariant registry remains DEFERRED for INV-05 through INV-11.

The readiness labels below do not change that registry.

They describe the next governance action required.

| Invariant | Readiness | Repository evidence | Remaining blocker |
| --- | --- | --- | --- |
| INV-05 | READY | AIJob service, save option, mutation guard, and metadata exist | Controlled activation review and independent evidence |
| INV-06 | REQUIRES CHANGE | Status enum and transition map exist | Cancellation-reason contract and lifecycle runtime proof |
| INV-07 | READY | AIRequestLog create surface, guard, and unique attempt indexes exist | Controlled activation review and independent evidence |
| INV-08 | REQUIRES CHANGE | Full log evidence schema exists | Exactly-one log per dispatched invocation runtime path |
| INV-09 | READY | PromptTemplate versioning, reference mark, and mutation guard exist | Controlled activation review and independent evidence |
| INV-10 | REQUIRES CHANGE | Failure categories and requeue transition exist | Retry taxonomy executor and no-auto-retry evidence |
| INV-11 | REQUIRES CHANGE | Idempotency field, unique index, and create precheck exist | Pre-dispatch reservation and retry linkage runtime proof |

## 8. Activation Roadmap

### Stage 1 — Repository Completion

Complete the missing lifecycle, cancellation-reason, dispatch, retry, and idempotency-linkage surfaces.

No implementation is authorized by this package.

### Stage 2 — Contract Verification

Verify registry input/output behavior with controlled bindings.

Verify AIJob mutation guards.

Verify AIRequestLog append-only behavior.

Verify PromptTemplate referenced-version immutability.

### Stage 3 — Runtime Verification

Prove one log per completed invocation.

Prove retry eligibility follows the approved taxonomy.

Prove idempotency is reserved before dispatch and stable across retries.

Prove no unauthorized provider invocation occurs.

### Stage 4 — Independent Review

An independent C20 review evaluates repository and runtime evidence.

The review decides whether each registry invariant can change from DEFERRED.

The review does not automatically authorize C25.

### Stage 5 — Freeze

Freeze the activated C20 contract, binding rules, and evidence requirements.

Record the exact capability-purpose portfolio decision.

Record the exact allowed binding and dispatch boundaries.

### Stage 6 — Available for C25

C25 may rely on the boundary only after C20 governance ratification, delivery, verification, and independent review.

C25 WP2.2 remains NO GO until those gates are complete.

## 9. Future Work Matrix

| Future work | Owner | Required before C25 WP2.2 | This package authorizes it? |
| --- | --- | --- | --- |
| Ratify `COMMERCIAL_BRIEF` `CompletionCapability` extension and matching purpose `commercial_brief_generation` | C20 governance | Yes | No |
| Deliver ProviderBinding policy surface | CRM/C20 policy owner | Yes | No |
| Deliver credential-reference custody path | CRM/C20 custody owner | Yes | No |
| Deliver controlled dispatch runtime | Connector/C20 runtime owner | Yes | No |
| Complete INV-06 lifecycle requirement | C20 WP3 owner | Yes | No |
| Complete INV-08 exactly-once logging | C20 dispatch owner | Yes | No |
| Complete INV-10 retry taxonomy enforcement | C20 retry owner | Yes | No |
| Complete INV-11 dispatch idempotency linkage | C20 dispatch owner | Yes | No |
| Independently review and freeze C20 evidence | C20 governance | Yes | No |
| Authorize C25 work package implementation | C25 governance | Separately required | No |

## 10. C25 Boundary

C25 remains a consumer of the C20 boundary.

C25 must not modify C20 runtime.

C25 must not modify connectors.

C25 must not modify registry.py.

C25 must not modify AIJob.

C25 must not modify AIRequestLog.

C25 must not create ProviderBinding metadata through this package.

C25 WP2.1B remains NOT AUTHORIZED.

C25 WP2.2 generation remains NO GO.

C25 WP2.3 remains NOT AUTHORIZED.

Any code remains NOT AUTHORIZED.

## 11. Completion Verdict

**RATIFIED — WP3 GOVERNANCE COMPLETE AND EXITED.**

The three external governance dependencies are specified as C20-owned work.

ADR-C20-005/006/007 are ratified as governance records.

The provider-binding ownership chain is defined rather than delivered.

The invariant activation plan is ratified; C20-INV-05 through C20-INV-11 remain DEFERRED.

No runtime implementation is authorized.

No connector has changed.

No code authorization is granted.

## 12. WP3 Exit Record

| Item | Result |
| --- | --- |
| Date | 2026-08-02 |
| Ratification verdict | RATIFIED WITH NON-BLOCKING NOTES |
| ADR-C20-005 | RATIFIED |
| ADR-C20-006 | RATIFIED |
| ADR-C20-007 | RATIFIED |
| Repository consistency | PASS |
| Cross-document consistency | PASS |
| WP3 governance exit | COMPLETE |
| Runtime delivery | INCOMPLETE |
| Implementation authorization | NONE |
| Next step | Phase3C20 Final Governance Freeze |

## 13. Final Authorization Matrix

| Item | Status |
| --- | --- |
| WP3 Governance Package | RATIFIED / EXITED |
| ADR-C20-005 | RATIFIED |
| ADR-C20-006 | RATIFIED |
| ADR-C20-007 | RATIFIED |
| COMMERCIAL_BRIEF enum addition | NOT AUTHORIZED |
| commercial_brief_generation purpose delivery | NOT DELIVERED |
| ProviderBinding runtime delivery | NOT AUTHORIZED |
| C20-INV-05–11 activation | NOT AUTHORIZED / remain DEFERRED |
| Runtime implementation | NOT AUTHORIZED |
| Any Code | NOT AUTHORIZED |
| Phase3C20 Final Governance Freeze | NEXT TASK |

## 14. Validation Record

| Check | Result |
| --- | --- |
| Repository verification completed | PASS |
| Capability portfolio matrix present | PASS |
| Provider binding matrix present | PASS |
| Purpose matrix present | PASS |
| Invariant readiness matrix present | PASS |
| Ownership matrix present | PASS |
| Activation matrix present | PASS |
| Future work matrix present | PASS |
| WP3 governance exit | COMPLETE |
| Runtime implementation authorized | NO |
| Connector modification authorized | NO |
| Registry modification authorized | NO |
| AIJob modification authorized | NO |
| AIRequestLog modification authorized | NO |

## 15. References

- `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
- `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
- `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
- `chitu-connector/chitu_connector/acquisition/providers/registry.py`
