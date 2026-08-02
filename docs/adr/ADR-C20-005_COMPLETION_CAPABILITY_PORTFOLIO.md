# ADR-C20-005: Completion Capability Portfolio

| Field | Value |
| --- | --- |
| Status | PROPOSED — governance completion reference only |
| Date | 2026-08-02 |
| Work Package | Phase3C20 WP3-A |
| Scope | Completion capability portfolio only |
| Implementation Authorization | None |

## 1. Status

This ADR records a C20 governance recommendation.

It does not ratify a new capability name.

It does not activate a capability.

It does not modify the connector, registry, AIJob, AIRequestLog, or PromptTemplate.

Only C20 governance may ratify a C20 capability name.

C25 cannot ratify C20 capability names.

## 2. Decision

The repository already contains an authoritative `CompletionCapability` enum.

That enum is the exhaustive, ratified CompletionProvider capability portfolio.

Its current four ratified values are `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`,
`DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`.

The generic `Capability.COMPLETION` family used by CapabilityRegistry is a
separate, higher-level registry family.

The repository does not contain `COMMERCIAL_BRIEF` as a CompletionCapability value.

`COMMERCIAL_BRIEF` is therefore recorded as **PROPOSED**, not RATIFIED.

Its proposed placement is a future extension of the existing CompletionCapability portfolio.

It is not proposed as a new connector capability family or a new portfolio.

It is not a C25-owned name.

It is not an authorization to dispatch a completion.

## 3. Repository Verification

The repository was inspected before this ADR was written.

`chitu-connector/chitu_connector/acquisition/providers/completion/base.py` defines the authoritative `CompletionCapability` enum.

That enum's authoritative comment describes it as the exhaustive, ratified CompletionProvider capability portfolio.

That enum defines `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`.

`chitu-connector/chitu_connector/acquisition/providers/capabilities.py` separately defines the generic `SEARCH`, `ENRICHMENT`, and `COMPLETION` registry families.

`CompletionRequest` and `CompletionResult` use `CompletionCapability`.

`CompletionProvider` is typed to the same CompletionCapability portfolio.

`registry.py` accepts a `Capability` plus a string `purpose`.

`registry.py` evaluates only CRM-supplied `allowed_provider_bindings`.

`registry.py` evaluates each binding's `allowed_purposes`.

`registry.py` returns `PURPOSE_NOT_ALLOWED` when the requested purpose is not permitted.

`registry.py` does not discover providers.

`registry.py` does not resolve secrets.

`registry.py` does not construct transports.

`registry.py` does not invoke adapters.

`AIJob` supports `SEARCH`, `ENRICHMENT`, and `COMPLETION` only.

`AIRequestLog` supports the same three capability values only.

`PromptTemplate` persists capability and purpose as governed provenance fields.

`ConnectorBoundary` is a port outside the CRM module.

No inspected surface supplies a live `COMMERCIAL_BRIEF` binding.

## 4. Current Portfolio Matrix

| Portfolio item | Repository position | Owner | Current disposition |
| --- | --- | --- | --- |
| `SEARCH` | Existing capability family | C20 registry governance | Existing; outside this ADR's activation scope |
| `ENRICHMENT` | Existing capability family | C20 registry governance | Existing; outside this ADR's activation scope |
| `COMPLETION` | Existing capability family | C20 registry governance | Existing; the only candidate family for a future brief purpose |
| `RESEARCH_EVIDENCE` | Existing CompletionCapability portfolio value | C20 governance | Ratified existing value; no new activation here |
| `QUALIFICATION_INSIGHT` | Existing CompletionCapability portfolio value | C20 governance | Ratified existing value; no new activation here |
| `DRAFT_ASSISTANCE` | Existing CompletionCapability portfolio value | C20 governance | Ratified existing value; no new activation here |
| `REPLY_ASSISTANCE` | Existing CompletionCapability portfolio value | C20 governance | Ratified existing value; no new activation here |
| `COMMERCIAL_BRIEF` | Proposed CompletionCapability portfolio extension | C20 governance | PROPOSED; requires independent C20 approval and matching binding-purpose delivery |

## 5. Portfolio Boundary

`CompletionCapability` expresses the CompletionProvider portfolio member.

The generic `Capability.COMPLETION` family expresses the registry-level function.

The purpose expresses a CRM-governed business use within that registry family.

`COMMERCIAL_BRIEF` is evaluated first as a CompletionCapability portfolio extension.

Any corresponding purpose registration remains a separate binding-governance decision.

The purpose must be supplied to a `CapabilityResolutionRequest` with `Capability.COMPLETION`.

The registry must reject that purpose when no permitted binding contains it.

The registry must not infer that purpose from a C25 record.

The registry must not add a binding when it sees that purpose.

The registry must not select a provider outside the CRM-authorized candidate set.

The connector must not reinterpret the purpose as authority to change a CRM business artifact.

CommercialBrief must not select a provider.

CommercialBrief must not route a provider.

CommercialBrief must not dispatch a provider.

CommercialBrief must not read a credential.

## 6. Proposed Commercial Brief Purpose

The proposed portfolio extension is `COMMERCIAL_BRIEF`.

The proposed matching binding-purpose identifier is `commercial_brief_generation`.

This identifier is a governance proposal only.

It is intentionally separate from the C25 entity name.

It is intentionally separate from an action key.

It is intentionally separate from a provider model name.

It is intentionally separate from a prompt template key.

Its proposed CompletionProvider portfolio placement is the existing `CompletionCapability` enum.

Its proposed generic registry family is `COMPLETION`.

Its proposed owner is C20 capability governance.

Its proposed consumer is a future C25 generation service after separate authorization.

Its proposed approval prerequisite is a C20 portfolio decision.

Its proposed delivery prerequisite is an eligible CRM ProviderBinding.

Its proposed verification prerequisite is a controlled contract test and later runtime evidence.

## 7. Decision Drivers

The existing registry already distinguishes capability from purpose.

The existing registry already has a purpose-rejection outcome.

The existing registry already requires CRM-authorized binding candidates.

Adding a new connector capability family would expand the registry enum.

That expansion is not necessary to represent a CommercialBrief use case.

Treating CommercialBrief as a purpose preserves the bounded connector capability surface.

Treating CommercialBrief as a purpose keeps provider eligibility under CRM policy.

Treating CommercialBrief as a purpose prevents C25 from owning provider selection.

Treating CommercialBrief as a purpose does not activate an implementation.

## 8. Alternatives Considered

### 8.1 Extend the existing `CompletionCapability` portfolio with `COMMERCIAL_BRIEF`

Rejected for this package.

The repository already has the authoritative CompletionCapability portfolio.

No repository evidence requires a new generic registry family.

The proposal would require independent C20 governance approval before any portfolio change.

Those changes are forbidden by this package.

### 8.2 Reuse `DRAFT_ASSISTANCE` without a purpose decision

Rejected.

The portfolio name alone does not establish binding eligibility.

The portfolio name alone does not establish C25 ownership.

The portfolio name alone does not make a provider binding lawful.

### 8.3 Treat `COMMERCIAL_BRIEF` as a C25 capability

Rejected.

C25 consumes the C20 boundary.

C25 does not govern C20 capability names.

C25 may request a C20 purpose only after C20 ratification.

## 9. Future Activation Requirements

1. C20 governance ratifies whether `COMMERCIAL_BRIEF` enters the existing CompletionCapability portfolio.

2. CRM governance creates or authorizes a matching ProviderBinding policy surface.

3. The binding explicitly includes `COMPLETION` capability support.

4. The binding explicitly includes the approved matching purpose in `allowed_purposes`.

5. The binding supplies a non-secret credential reference.

6. The registry contract verifies the binding is accepted only when eligible.

7. A dispatch owner is separately implemented and authorized.

8. AIJob and AIRequestLog runtime invariants are activated and verified.

9. C25 separately passes its own WP2.0 and implementation gates.

## 10. Non-Authorization

Nothing in this ADR authorizes implementation.

Nothing in this ADR activates runtime.

Nothing in this ADR changes C20 runtime.

Nothing in this ADR changes connectors.

Nothing in this ADR changes registry.py.

Nothing in this ADR changes AIJob.

Nothing in this ADR changes AIRequestLog.

Nothing in this ADR creates ProviderBinding metadata.

## 11. Evidence Ledger

| Evidence | Observed fact | Governance consequence |
| --- | --- | --- |
| Capability enum | Only SEARCH, ENRICHMENT, COMPLETION exist | No new capability family is ratified |
| CapabilityResolutionRequest | Capability and purpose are independent inputs | Brief placement can be a purpose under COMPLETION |
| ProviderBinding value | `allowed_purposes` is binding data | Purpose eligibility stays at the CRM binding boundary |
| Registry evaluation | `PURPOSE_NOT_ALLOWED` is explicit | Rejection is deterministic when no binding permits the purpose |
| Registry construction | Registrations are descriptors, not live adapters | Portfolio governance does not invoke a provider |
| AIJob metadata | Capability enum is bounded | Future purpose does not alter current entity metadata in this package |
| AIRequestLog metadata | Capability and purpose are recorded | Future evidence must preserve approved provenance |
| PromptTemplate metadata | Capability and purpose are persisted | Template selection remains a future governed concern |
| ConnectorBoundary | Runtime is connector-owned | C25 cannot dispatch a provider |

## 12. Consequences

The remaining C25 dependency is narrowed to a C20 governance decision plus future delivery.

No C25 implementation gate is opened by this ADR.

No provider is selected by this ADR.

No credential is approved by this ADR.

No runtime capability is activated by this ADR.

The C20 completion portfolio remains bounded.

## 13. Ratification Gate

This ADR remains PROPOSED until an independent C20 capability-portfolio decision ratifies it.

Any later ratification must state the exact CompletionCapability portfolio extension and any matching purpose identifier.

Any later ratification must state the owning C20 authority.

Any later ratification must not imply implementation authorization.

## 14. References

- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
- `chitu-connector/chitu_connector/acquisition/providers/registry.py`
- `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
