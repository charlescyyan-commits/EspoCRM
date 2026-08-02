# ADR-C20-006: Provider Binding Governance

| Field | Value |
| --- | --- |
| Status | RATIFIED — provider-binding governance contract approved; runtime delivery not authorized |
| Date | 2026-08-02 |
| Work Package | Phase3C20 WP3-B |
| Scope | Provider binding governance only |
| Implementation Authorization | None |

## 1. Status

This ADR is **RATIFIED** as the provider-binding governance contract.

It describes the required ownership chain for a future completion request.

It documents repository facts and governance boundaries.

It does not create ProviderBinding metadata.

It does not add a provider.

It does not add a connector adapter.

It does not route or dispatch any request.

`commercial_brief_generation` remains proposed only. No live binding currently authorizes it.

## 2. Decision

The required governance chain is fixed as follows.

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

The capability identifies the requested functional family.

Binding eligibility determines whether a CRM-owned binding may serve that family and purpose.

`allowed_provider_bindings` is the CRM-authorized candidate set supplied to the registry.

ProviderBinding holds policy and non-secret reference metadata.

The connector owns adapter execution outside the CRM module.

For the CommercialBrief generation use case, the proposed ProviderBinding purpose ID is:

```text
commercial_brief_generation
```

That purpose ID corresponds to—but is not identical to—the proposed `CompletionCapability` portfolio candidate `COMMERCIAL_BRIEF`.

```text
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

`commercial_brief_generation` is the value that would be evaluated against `ProviderBinding.allowed_purposes` after a matching binding and purpose registration are delivered.

`COMMERCIAL_BRIEF` must not be used as an `allowed_purposes` value.

Neither identifier is ratified, registered, allowed, active, or delivered by this ADR.

No binding currently authorizes `commercial_brief_generation`.

No routing or dispatch implementation is claimed or authorized here.

CommercialBrief owns none of those responsibilities.

## 3. Repository Verification

The repository was inspected before this ADR was written.

`CapabilityResolutionRequest` contains `capability`.

`CapabilityResolutionRequest` contains `purpose`.

`CapabilityResolutionRequest` contains `allowed_provider_bindings`.

`CapabilityResolutionRequest` contains credential availability only by reference.

`CapabilityResolutionRequest` contains provider-health input.

`ProviderBinding` contains provider identifier and adapter type.

`ProviderBinding` contains priority and enabled state.

`ProviderBinding` contains credential reference, not a credential secret.

`ProviderBinding` contains supported capabilities.

`ProviderBinding` contains `allowed_purposes`.

`CapabilityRegistry` evaluates only submitted bindings.

`CapabilityRegistry` rejects a purpose with `PURPOSE_NOT_ALLOWED`.

`CapabilityRegistry` does not probe provider health.

`CapabilityRegistry` does not resolve credentials.

`CapabilityRegistry` does not construct a transport.

`CapabilityRegistry` does not invoke an adapter.

`ConnectorBoundary` is a port implemented outside the CRM module.

No inspected CommercialBrief surface implements provider routing or dispatch.

## 4. Ownership Matrix

| Layer | Sole responsibility | Explicit non-responsibility |
| --- | --- | --- |
| CRM policy | Authorize bindings, purpose policy, ACL, and credential references | Adapter invocation and connector selection mechanics |
| Capability Registry | Deterministically evaluate CRM-authorized candidates | Discovering providers, secrets, health probes, dispatch, or business authority |
| ProviderBinding | Describe one authorized candidate's policy attributes | Storing plaintext credentials or invoking the provider |
| Connector | Construct and invoke an authorized adapter after a separate dispatch decision | Owning CRM policy, ACL, or business lifecycle mutation |
| Provider | Execute its external service contract | Defining CRM capability or purpose policy |
| CommercialBrief | Future consumer of a governed result | Provider selection, routing, dispatch, credential custody, or registry ownership |

## 5. Capability and Purpose Matrix

| Input | Owner | Required rule | Rejection owner |
| --- | --- | --- | --- |
| `capability` | C20 capability governance | Must be a recognized family | Registry returns a controlled invalid-capability error |
| `purpose` | CRM/C20 policy governance | Must be explicitly allowed by a candidate binding | Registry returns `PURPOSE_NOT_ALLOWED` for each ineligible candidate |
| `allowed_provider_bindings` | CRM policy | Must be the complete authorized candidate set | Registry never expands the set |
| `allowed_purposes` | ProviderBinding policy | Must contain the requested purpose | Registry excludes the binding when absent |
| credential availability | CRM custody boundary | Must be reference/status only | Registry excludes unavailable references |
| provider health | CRM health-policy input | Must be supplied; registry never probes | Registry excludes unknown or unhealthy candidates |

## 6. Binding Eligibility

A binding is eligible only when all required checks pass.

The binding must be enabled.

The provider must have a registry registration.

The registration adapter type must equal the binding adapter type.

The binding must support the requested capability.

The registration must support the requested capability.

The binding must allow the requested purpose.

The binding must have a credential reference.

The credential reference must be available according to CRM-supplied status.

The effective provider health must not be UNKNOWN.

The effective provider health must not be UNHEALTHY.

An ineligible binding cannot be selected as a fallback.

An unlisted binding cannot be evaluated.

## 7. Deterministic Selection

The registry evaluates candidates in policy priority order.

The registry retains a non-secret evaluation trace.

The registry selects only among eligible candidates.

The registry prefers healthy eligible candidates.

The registry then uses priority and provider identifier deterministically.

The registry reports whether a fallback occurred.

The registry returns the selected provider identifier.

The registry returns the selected adapter type.

The registry returns the selected credential reference identifier.

The registry does not turn that result into a network request.

## 8. Purpose Rejection

Purpose rejection is a binding-policy outcome.

It is not a CommercialBrief decision.

It is not a provider-model decision.

It is not a credential error.

It is not a retry decision.

When a requested purpose is absent from `allowed_purposes`, the binding is ineligible.

The evaluation trace records `PURPOSE_NOT_ALLOWED`.

When no eligible candidate remains, resolution returns `CAPABILITY_UNAVAILABLE`.

No provider call is attempted during this evaluation.

No AIJob status transition is performed during this evaluation.

No AIRequestLog is written during this evaluation.

## 9. CommercialBrief Boundary

CommercialBrief is the C25 domain artifact. It is not a capability identifier and not a ProviderBinding purpose.

CommercialBrief may eventually request a C20-governed capability candidate (`COMMERCIAL_BRIEF`, if ratified) together with purpose ID `commercial_brief_generation` (if registered on an eligible binding).

CommercialBrief may not introduce a capability name.

CommercialBrief may not create a ProviderBinding.

CommercialBrief may not alter `allowed_provider_bindings`.

CommercialBrief may not alter `allowed_purposes`.

CommercialBrief may not choose a provider.

CommercialBrief may not route a provider.

CommercialBrief may not dispatch a provider.

CommercialBrief may not read or persist a credential secret.

CommercialBrief may not modify registry.py.

CommercialBrief may not substitute a C25 action key for a C20 purpose.

## 10. Credential Ownership

Credential custody remains outside CommercialBrief.

The registry accepts a credential reference and availability flag only.

The registry result exposes only the selected reference identifier.

The registry does not expose a secret value.

ProviderBinding must not be treated as a secret store in this package.

The connector may receive credentials only through a separately authorized custody path.

This ADR creates no such path.

This ADR approves no credential.

## 11. Routing and Dispatch Ownership

Routing is the policy-constrained resolution from authorized candidates to one selected descriptor.

The registry owns deterministic evaluation of that bounded candidate set.

Dispatch is the later act that invokes an adapter.

The connector-owned runtime owns adapter execution.

CRM does not perform outbound provider I/O in this model.

CommercialBrief does not perform outbound provider I/O in this model.

AIJob records lifecycle evidence but does not itself supply the missing dispatch implementation.

AIRequestLog records attempt evidence but does not itself dispatch an adapter.

## 12. Provider Binding Matrix

| Binding condition | Registry behavior | Runtime effect in this package |
| --- | --- | --- |
| Binding disabled | Exclude with `PROVIDER_DISABLED` | No provider call |
| Adapter absent | Exclude with `ADAPTER_NOT_REGISTERED` | No provider call |
| Adapter type mismatch | Exclude with `ADAPTER_TYPE_MISMATCH` | No provider call |
| Capability unsupported by binding | Exclude with `BINDING_CAPABILITY_UNSUPPORTED` | No provider call |
| Capability unsupported by adapter | Exclude with `ADAPTER_CAPABILITY_UNSUPPORTED` | No provider call |
| Purpose absent | Exclude with `PURPOSE_NOT_ALLOWED` | No provider call |
| Credential reference absent | Exclude with `MISSING_CREDENTIAL_REFERENCE` | No provider call |
| Credential unavailable | Exclude with `CREDENTIAL_UNAVAILABLE` | No provider call |
| Health unhealthy | Exclude with `PROVIDER_UNHEALTHY` | No provider call |
| Health unknown | Exclude with `PROVIDER_HEALTH_UNKNOWN` | No provider call |

## 13. Future Delivery Requirements

1. Ratify the proposed `CompletionCapability` portfolio extension `COMMERCIAL_BRIEF` and the matching purpose ID `commercial_brief_generation` as coordinated but distinct C20 decisions.

2. Define the CRM ProviderBinding persistence and authorization surface.

3. Define the source of `allowed_provider_bindings`.

4. Define the source of credential availability.

5. Define the source of provider health input.

6. Verify registry behavior with controlled fixtures.

7. Separately authorize connector dispatch runtime.

8. Activate the AIJob and AIRequestLog invariants required by dispatch.

9. Obtain an independent review before C25 consumes the path.

## 14. Non-Authorization

Nothing in this ADR authorizes implementation.

Nothing in this ADR activates runtime.

Nothing in this ADR modifies C20 runtime.

Nothing in this ADR changes connectors.

Nothing in this ADR changes registry.py.

Nothing in this ADR changes AIJob.

Nothing in this ADR changes AIRequestLog.

Nothing in this ADR creates metadata, an entity, a route, a controller, or a test.

## 15. Ratification Record

| Item | Result |
| --- | --- |
| Review type | Final WP3 ADR Ratification Review |
| Date | 2026-08-02 |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| Ownership chain | PASS |
| `allowed_provider_bindings` contract | PASS |
| `allowed_purposes` / `PURPOSE_NOT_ALLOWED` | PASS |
| CRM ProviderBinding surface | NOT DELIVERED |
| Provider routing/dispatch implementation | NOT AUTHORIZED |
| Credential custody changes | NOT AUTHORIZED |
| Any code | NOT AUTHORIZED |

`commercial_brief_generation` is proposed only and is not delivered.

No live ProviderBinding currently authorizes it.

CommercialBrief owns no provider, model, routing, dispatch, or credential responsibility.

## 16. References

- `chitu-connector/chitu_connector/acquisition/providers/registry.py`
- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
- `crm-extension/files/custom/Espo/Modules/Prospecting/ProviderBoundary/ConnectorBoundary.php`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/AIJob.json`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/AIRequestLog.json`
- `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
