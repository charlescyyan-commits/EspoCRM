# ADR-C20-005: Completion Capability Portfolio

| Field | Value |
| --- | --- |
| Status | RATIFIED — governance direction approved; capability extension not active and implementation not authorized |
| Date | 2026-08-02 |
| Work Package | Phase3C20 WP3-A |
| Scope | Completion capability portfolio only |
| Implementation Authorization | None |

## 1. Status

This ADR is **RATIFIED** as a C20 governance-direction record.

Ratification accepts the existing CompletionCapability portfolio model and
records `COMMERCIAL_BRIEF` as a governed portfolio identity.

Package A RELEASED delivers `COMMERCIAL_BRIEF` as **capability identity /
contract alignment only** (see §15 Addendum). Ratification of this ADR alone
did not authorize that delivery; Package A was a separate C20 authorization.

`COMMERCIAL_BRIEF` identity delivery does **not** authorize provider execution,
autonomous generation, Runtime Expansion, or invariant activation.

It does not activate a capability.

It does not modify the connector, registry, AIJob, AIRequestLog, or PromptTemplate.

Only C20 governance may authorize a later `CompletionCapability` enum addition.

C25 has no authority to ratify or activate C20 capability names.

## 2. Decision

The repository already contains an authoritative `CompletionCapability` enum.

That enum is the exhaustive, ratified CompletionProvider capability portfolio.

Its current four ratified values are `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`,
`DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`.

The generic `Capability.COMPLETION` family used by CapabilityRegistry is a
separate, higher-level registry family.

The repository does not contain `COMMERCIAL_BRIEF` as a CompletionCapability value.

`COMMERCIAL_BRIEF` remains a **proposed future portfolio extension only**. ADR ratification does not ratify or activate that enum value.

Its proposed placement remains a future extension of the existing CompletionCapability portfolio.

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

It is not an `allowed_purposes` value.

Any corresponding purpose registration remains a separate binding-governance decision and uses the distinct proposed purpose ID `commercial_brief_generation`.

```text
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

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

## 6. Proposed Commercial Brief Naming Layers

| Layer | Canonical identifier |
| --- | --- |
| Completion capability candidate | `COMMERCIAL_BRIEF` |
| Provider-binding purpose ID | `commercial_brief_generation` |
| Domain artifact | `CommercialBrief` |
| Registry family | `Capability.COMPLETION` |

The proposed portfolio extension is `COMMERCIAL_BRIEF`.

If separately ratified and implemented, its future enum-level form would be `CompletionCapability.COMMERCIAL_BRIEF`.

The corresponding proposed ProviderBinding purpose ID is `commercial_brief_generation`.

```text
COMMERCIAL_BRIEF ≠ commercial_brief_generation
```

`commercial_brief_generation` is a governance proposal only.

It is intentionally separate from the capability candidate `COMMERCIAL_BRIEF`.

It is intentionally separate from the C25 entity name `CommercialBrief`.

It is intentionally separate from an action key.

It is intentionally separate from a provider model name.

It is intentionally separate from a prompt template key.

It must never be described as a current `CompletionCapability` enum member.

`COMMERCIAL_BRIEF` must never be used as an `allowed_purposes` value.

Neither identifier is ratified, active, delivered, or implemented by this ADR.

Its proposed CompletionProvider portfolio placement is the existing `CompletionCapability` enum.

Its proposed generic registry family is `Capability.COMPLETION`.

Its proposed owner is C20 capability governance.

Its proposed consumer is a future C25 generation service after separate authorization.

Its proposed approval prerequisite is a C20 portfolio decision.

Its proposed delivery prerequisite is an eligible CRM ProviderBinding that lists `commercial_brief_generation` in `allowed_purposes`.

Its proposed verification prerequisite is a controlled contract test and later runtime evidence.

## 7. Decision Drivers

The existing registry already distinguishes capability from purpose.

The existing registry already has a purpose-rejection outcome.

The existing registry already requires CRM-authorized binding candidates.

Adding a new connector capability family would expand the registry enum.

That expansion is not necessary to represent a CommercialBrief use case.

Representing the binding use as purpose ID `commercial_brief_generation`—while keeping `COMMERCIAL_BRIEF` as the proposed `CompletionCapability` portfolio extension and `CommercialBrief` as the C25 domain artifact—preserves the bounded connector capability surface.

That purpose-layer placement keeps provider eligibility under CRM `allowed_purposes` policy.

That separation prevents C25 from owning provider selection.

Recording these proposed names does not activate an implementation.

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

## 13. Ratification Record

| Item | Result |
| --- | --- |
| Review type | Final WP3 ADR Ratification Review |
| Date | 2026-08-02 |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| Existing four-value CompletionCapability portfolio | PASS |
| `COMMERCIAL_BRIEF` future-extension direction | RATIFIED AS GOVERNANCE DIRECTION ONLY |
| `COMMERCIAL_BRIEF` enum addition | NOT AUTHORIZED |
| `commercial_brief_generation` purpose registration | NOT DELIVERED |
| C25 authority | NONE |
| Runtime implementation | NOT AUTHORIZED |
| Any code | NOT AUTHORIZED |

`COMMERCIAL_BRIEF` is not present in the enum, not active, not delivered, and not implemented.

Any later enum addition and matching purpose delivery remain separate C20 authorization and delivery tasks and do not follow from this ADR ratification alone.

---

## 15. Package A Alignment Addendum (Post-Delivery)

| Field | Value |
| --- | --- |
| Addendum date | 2026-08-04 |
| Package A status | **RELEASED** (`docs/audit/PHASE3C20_PACKAGE_A_RELEASE_RECORD.md`) |
| Delivery commit | `e24a8e11e8e915d7432ad4f91377835ff9f41848` |
| Purpose of addendum | Align this ADR’s delivery statements with Package A identity delivery |

**Package A delivered (identity / contract only):**

- `CompletionCapability.COMMERCIAL_BRIEF` enum identity in connector portfolio
- contract / guard alignment referencing `COMMERCIAL_BRIEF`

**Package A did NOT deliver:**

- provider execution / connector HTTP invocation for CommercialBrief generation
- autonomous generation
- Runtime Expansion
- invariant activation

```text
COMMERCIAL_BRIEF = delivered capability identity (Package A)
COMMERCIAL_BRIEF ≠ live provider execution
```

Prior §1 / §13 statements that the enum value was “not present / not delivered”
are **superseded for identity delivery status only** by Package A RELEASED.
Governance direction, non-execution boundary, and C25 non-authority remain in force.

This addendum does **not** reopen C20 architecture, authorize Runtime Expansion,
or activate invariants.

---

## 16. References

- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
- `chitu-connector/chitu_connector/acquisition/providers/registry.py`
- `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
