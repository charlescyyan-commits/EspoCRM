# Phase3C20 RT-WP1 Implementation Charter

| Field | Value |
| --- | --- |
| Phase / Work Package | Phase3C20 RT-WP1 |
| Status | RATIFIED |
| Date | 2026-08-02 |
| Governing baseline commit | `7846f6f5c3d33ecfe161cbe2099521ab00bac365` |
| Governing exit tag | `phase3c20-rt-wp0-exit` |
| Charter authoring authorization | Authorized by the RT-WP1 separate documentation authorization |
| Implementation authorization | RT-WP1 Implementation: NOT AUTHORIZED |
| Runtime code | Not authorized |
| C25 WP2.2 | NO GO |

## 1. Purpose

RT-WP1 is the first minimal future runtime work package after RT-WP0. Its
future role is to deliver the C20-governed completion-capability representation
and its non-routability contract, subject to a separate implementation
authorization.

The controlling scope is `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`,
sections 8 and 20. It separates the proposed capability candidate
`COMMERCIAL_BRIEF` from the proposed binding-purpose identifier
`commercial_brief_generation`.

This ratification approves the charter only. It does not add a fifth enum
value, register a purpose, create a binding, change an adapter, or authorize
tests or runtime code.

## Administrative Ratification Record

| Field | Value |
| --- | --- |
| Review | RT-WP1 Implementation Charter Independent Ratification Review |
| Review file | `docs/audit/PHASE3C20_RT_WP1_IMPLEMENTATION_CHARTER_RATIFICATION_REVIEW.md` |
| Date | 2026-08-02 |
| Verdict | RATIFIED WITH INFORMATIONAL NOTES |
| BLOCKER | NONE |
| HIGH | NONE |
| MEDIUM | NONE |
| LOW | NONE |
| INFORMATIONAL | 4 |
| Charter ratification result | RATIFIED |
| Implementation authorization result | NOT AUTHORIZED |

The RT-WP1 Implementation Charter is RATIFIED.

This ratification does not authorize RT-WP1 implementation, Runtime Code,
RT-WP2–RT-WP8, or C25 WP2.2.

## 2. Preconditions

| Precondition | Evidence | Result |
| --- | --- | --- |
| RT-WP0 baseline | `docs/PHASE3C20_RT_WP0_RUNTIME_BASELINE.md` | RATIFIED and EXITED |
| RT-WP0 exit commit | `7846f6f5c3d33ecfe161cbe2099521ab00bac365` | Verified locally and as `origin/master` |
| RT-WP0 exit tag | `phase3c20-rt-wp0-exit` | Verified locally; remote target was verified after tag push in this release sequence |
| Runtime Charter | `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` | RATIFIED and synchronized |
| Completion portfolio ADR | `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md` | RATIFIED direction; enum addition not authorized |
| Provider binding ADR | `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md` | RATIFIED contract; runtime delivery not authorized |
| Invariant plan | `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md` | RATIFIED plan; INV-05–11 remain DEFERRED |
| C25 boundary | `docs/PHASE3C25_GOVERNANCE_FREEZE.md` | C25 WP2.2 remains NO GO |

## 3. Authority Sources and Scope Boundary

| Source | RT-WP1 authority | Boundary imposed |
| --- | --- | --- |
| Runtime Charter §8 and §20 | Future capability representation and non-routability contract | Enum addition requires separate authorization; binding registration belongs to RT-WP2 |
| ADR-C20-005 §§5–10 | Capability, purpose, and C25-domain names are distinct | `COMMERCIAL_BRIEF` is not `commercial_brief_generation` or `CommercialBrief` |
| ADR-C20-006 §§4–13 | Purpose eligibility is binding policy | No ProviderBinding, provider selection, routing, dispatch, or credential custody in RT-WP1 |
| C20 Invariant Registry | Active boundaries and deferred activation conditions | No invariant activation or status change |
| C20 Charter §§1, 4, and 6 | C20 ownership and sole connector egress | No scoring, qualification, lifecycle authority, email/outreach, or CRM provider HTTP |

### 3.1 In scope after separate implementation authorization

The future implementation scope is limited to the RT-WP1 rows in Runtime
Charter §28, with the exact file allowlist reconfirmed in that separate task:

| Future unit | Contract | Authority source |
| --- | --- | --- |
| Capability representation | Evaluate one additive `CompletionCapability` candidate only after explicit C20 authorization | Runtime Charter §8.1; ADR-C20-005 §§6 and 13 |
| Compatibility | Preserve all four existing values and their serialized meanings | RT-WP0 Baseline §2.1; Runtime Charter §8.2 |
| Non-routability | Preserve deterministic refusal unless an independently delivered binding allows the matching purpose | Runtime Charter §§8.2–8.4; ADR-C20-006 §§6–8 |
| Contract evidence | Future contract, negative, boundary, secret-leakage, and provider-isolation tests | Runtime Charter §§20, 29, and 32 |

The only current portfolio is `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`,
`DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`. This charter does not change it.

### 3.2 Explicit exclusions

RT-WP1 must not implement or assume any responsibility assigned to RT-WP2
through RT-WP8. It excludes:

- ProviderBinding persistence, metadata, ACL, layouts, allowed-binding production, or purpose registration (RT-WP2);
- CRM dispatch orchestration, API, jobs, connector completion dispatch, AIRequestLog production, and provider execution (RT-WP3);
- cancellation fields or lifecycle changes (RT-WP4);
- retry classification executor, scheduler, queue control, or automatic retries (RT-WP5);
- reservation persistence, attempt claims, concurrency reservation, or replay runtime (RT-WP6);
- invariant activation, activation evidence, or registry-status updates (RT-WP7);
- runtime freeze or C25 dependency closure (RT-WP8).

RT-WP1 also excludes CommercialBrief creation or lifecycle, C25 implementation,
purpose runtime, autonomous invocation, background jobs, provider egress,
secret persistence, plaintext credential handling, scoring, ranking,
qualification, prioritization, queue authority, Lead or Opportunity creation,
CRM lifecycle mutation, UI/workspace work, and unrelated refactoring.

## 4. Architecture and Ownership Boundaries

The frozen chain remains unchanged:

```text
CRM policy
→ authorized ProviderBinding set
→ CapabilityRegistry eligibility resolution
→ CRM governed dispatch orchestration
→ Connector outbound provider dispatch
→ provider adapter and provider HTTP
```

| Layer | May do in the future | Must not do in RT-WP1 |
| --- | --- | --- |
| CRM / AIPlatform | Retain its existing policy, lifecycle, correlation, and provenance boundaries | Provider SDK invocation, outbound provider HTTP, provider secrets, selection, or dispatch orchestration changes |
| Completion capability contract | Represent an explicitly authorized capability candidate and reject unsupported values | Turn a capability name into a binding, purpose authorization, or lifecycle authority |
| CapabilityRegistry | Continue deterministic eligibility evaluation and rejection | Discover providers, resolve secrets, invoke adapters, probe health, or execute retries |
| Provider adapter / connector | Continue existing four-value contract behavior and connector-only egress | Gain scoring, qualification, prioritization, queue, or CRM lifecycle authority |
| Credential custody | Retain connector custody and reference-only CRM policy | Persist, serialize, log, or expose plaintext secrets |
| C25 CommercialBrief | Remain a future consumer after separate C20 and C25 gates | Own capability names, provider binding, model selection, dispatch, credentials, provenance ledger, or lifecycle authority |

## 5. Data, Credential, Observability, and ACL Boundaries

### 5.1 Data and credential handling

No new secret-storage design is authorized. CRM may use only an existing
credential reference where a later authorized RT-WP supplies one; secret
resolution remains in the connector custody boundary. Logs, exceptions,
fixtures, serialized payloads, caches, exports, and test evidence must not
contain plaintext secrets, authorization headers, raw credential payloads, or
unnecessary raw provider responses.

`CompletionRequest` and `CompletionResult` remain contract objects. Any future
RT-WP1 contract test must use controlled non-secret data and must not convert
the purpose string into an authority to route or invoke a provider.

### 5.2 Observability and audit

RT-WP1 may describe the future need to preserve capability identity, a binding
reference, timestamps, outcome category, provenance, and correlation identity.
It must not create an append-only ledger, alter `AIRequestLog`, or create a
CommercialBrief audit record. Those concerns remain dependent on later C20 and
C25 authorization.

### 5.3 ACL and authorization

RT-WP1 creates no UI, route, action, background trigger, or parallel
authorization model. A future service boundary must reuse existing EspoCRM
ACL and workflow-authorization boundaries, deny Portal escalation, and keep
credential references internal. Generic record edit permission must never be
treated as permission to select a provider, dispatch a completion, retry, or
mutate a lifecycle.

## 6. Contract and Failure Semantics

The future RT-WP1 contract must fail closed and preserve existing semantics.

| Condition | Required contract result | Prohibited interpretation |
| --- | --- | --- |
| Unsupported capability | Reject as unsupported / unavailable before execution | Adding a default adapter path |
| Invalid configuration or contract violation | Reject deterministically with a safe non-secret result | Creating a binding or dispatching anyway |
| Purpose absent from a binding | `PURPOSE_NOT_ALLOWED` when evaluated by the existing registry | Retrying, selecting a provider, or inferring policy |
| Provider unavailable, timeout, or malformed response | Preserve normalized connector failure semantics when a later dispatch owner exists | Building dispatch, retry, or scheduler behavior in RT-WP1 |
| Authorization denied | Deny at the existing service and ACL boundary | Bypassing ACL or exposing a credential reference |

No condition in this section authorizes retry orchestration, a reservation, a
provider call, or an autonomous workflow.

## 7. Invariant Mapping

| Invariant | RT-WP1 relevance | Enforcement location | Future evidence | Status after this task |
| --- | --- | --- | --- | --- |
| C20-INV-02 | Preserve absence of Prospecting identifiers in AIPlatform | Existing WP0 boundary guard | Boundary regression test | ACTIVE; unchanged |
| C20-INV-03 | Preserve no CRM provider HTTP | Existing WP0 boundary guard | Provider-isolation regression test | ACTIVE; unchanged |
| C20-INV-04 | Preserve no plaintext credential disclosure | Connector custody and future non-secret tests | Secret-leakage negative test | DEFERRED; unchanged |
| C20-INV-05–11 | No RT-WP1 implementation or activation ownership | Their assigned later work packages | No activation claim | DEFERRED; unchanged |
| C20-INV-12 | Adapter construction remains explicit-transport only | Completion provider contract | Contract test | DEFERRED; unchanged |
| C20-INV-13 | No dry-run runtime is introduced | Later execution path only | Boundary test | DEFERRED; unchanged |
| C20-INV-14, 16, 19, 21, 22 | No score, ranking, qualification, or lifecycle authority | Existing WP0 boundary guards | No-authority regression tests | ACTIVE; unchanged |
| C20-INV-15 | No email or outreach execution path | Existing WP0 boundary guard | Boundary regression test | ACTIVE; unchanged |

## 8. Future Implementation Sequence and Evidence

This is a future plan, not implementation authorization.

1. Obtain explicit RT-WP1 implementation authorization and a scoped file
   allowlist; stop if it broadens into RT-WP2–RT-WP8.
2. Reconfirm the four-value baseline and the separate C20 authorization for
   any proposed enum addition; stop if no exact authorization exists.
3. Apply only the approved capability-contract change, keeping it
   non-routable and without a binding, dispatch, reservation, retry, or secret
   surface.
4. Run contract, negative, boundary, serialization, secret-leakage,
   provider-isolation, no-lifecycle-authority, no-scoring-authority, and
   no-RT-WP2-plus-artifact tests.
5. Perform independent implementation review, preserve rollback to the
   preceding frozen commit if evidence fails, and do not claim exit until a
   separately authorized exit process passes.

Future evidence must show: four current values retain behavior; an unsupported
or unbound request is rejected deterministically; no purpose is registered;
no provider call occurs; no secret appears in diagnostics; no scoring,
qualification, lifecycle, outreach, or C25 authority is introduced.

## 9. Freeze and Exit Criteria

RT-WP1 may enter implementation review only after separate implementation
authorization. It may be considered for freeze review only after all authorized
contract and negative evidence passes, the exact file allowlist is respected,
and no RT-WP2–RT-WP8 responsibility appears.

RT-WP1 may be marked exited only after independent implementation review,
remote commit verification, and a separate status synchronization. Charter
ratification never authorizes implementation.

## 10. Authorization Matrix

| Area | State |
| --- | --- |
| RT-WP0 | EXITED |
| RT-WP1 Charter Authoring | COMPLETE |
| RT-WP1 Charter Ratification | RATIFIED |
| RT-WP1 Implementation | NOT AUTHORIZED |
| RT-WP2–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

No section of this charter authorizes runtime implementation, a test change,
metadata, an entity, a route, a service, a guard, a connector change, or a
provider invocation.

## 11. Next Gate

```text
RT-WP1 Implementation may be considered only through a separate,
explicit implementation authorization.
```

## 12. References

- `docs/PHASE3C20_CHARTER.md`
- `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
- `docs/PHASE3C20_RT_WP0_RUNTIME_BASELINE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
- `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
- `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
- `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`
- `docs/PHASE3C25_GOVERNANCE_FREEZE.md`
