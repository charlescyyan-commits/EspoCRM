# Phase3C20 RT-WP2 Implementation Charter

| Field | Value |
| --- | --- |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Work package | RT-WP2 — ProviderBinding and purpose-policy foundation |
| Date | 2026-08-03 |
| Governing release | `928aa5f734f8d7f643cdb45a7549fed7ada0c400` baseline; RT-WP1 exit `8f11ee4578d4626fa3ae950c9645b4cbcfc6befd` |
| Execution mode | Charter authoring only; no runtime, metadata, ACL, route, service, test, or connector change |

## 1. Charter purpose and present authority

This Charter defines the bounded future planning contract for a governed ProviderBinding and purpose-policy surface. It creates no runtime capability, storage model, entity, metadata, route, ACL implementation, provider call, or credential operation. Ratification approves planning direction only and does not release an implementation scope.

| Item | Status |
| --- | --- |
| RT-WP0 | EXITED |
| RT-WP1 | EXITED |
| RT-WP1 runtime code | NOT AUTHORIZED — no code-bearing scope |
| RT-WP2–RT-WP8 | NOT AUTHORIZED |
| Runtime code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

The authoritative completion portfolio contains exactly:

`RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, and `REPLY_ASSISTANCE`.

`COMMERCIAL_BRIEF` is a purpose/business contract,
not a `CompletionCapability`. CommercialBrief remains a C25 business entity and future consumer boundary; it owns no provider, routing, dispatch, credential, capability-portfolio, or selection authority.

## 2. Repository and governance evidence

The repository is authoritative. This Charter reviewed the following without modification:

| Evidence | Observed boundary |
| --- | --- |
| `chitu-connector/chitu_connector/acquisition/providers/completion/base.py` | `CompletionCapability` is the exhaustive, ratified CompletionProvider portfolio with the four values above. |
| `.../providers/completion/adapter.py` | `CompletionBridgeProvider` requires an injected `HttpTransport`; its `complete` method is an adapter concern, not a CRM binding concern. |
| `.../providers/registry.py` | The registry evaluates CRM-supplied bindings and availability only; it does not discover providers, resolve credentials, construct transports, or invoke adapters. |
| CRM AIPlatform metadata | `ProviderCredential` exists as a reference-custody surface; no CRM `ProviderBinding` entity, service, or guard was found. |
| ADR-C20-005 | The four-value portfolio is authoritative; any extension requires independent C20 governance. |
| ADR-C20-006 | Binding policy is non-secret and purpose-governed; runtime delivery remains outside its scope. |
| C20 invariant registry | C20-INV-02 and C20-INV-03 are ACTIVE; C20-INV-04 through C20-INV-13 are DEFERRED. |

The connector's in-memory `ProviderBinding` includes provider identity, adapter type, priority, enabled state, credential reference, supported capabilities, health, and `allowed_purposes`. This is connector policy-contract evidence only, not evidence that CRM persistence, lifecycle, ACL, layout, or endpoint delivery exists.

## 3. Scope: future policy foundation only

RT-WP2 may plan, and only a separately scoped future authorization may assess:

1. A ProviderBinding contract relating an existing four-value completion capability, provider identity, non-secret credential reference, explicit purpose/use case, and enabled/available policy state.
2. Purpose registration and capability mapping: capability says what technology can do; purpose says why a governed caller requests it.
3. Eligibility classification of an already supplied candidate as configured/unconfigured, eligible/ineligible, and bound/unbound.
4. Configuration-change provenance explaining who approved a binding policy and when, without becoming an execution ledger.

No exact EspoCRM storage form is selected. Any entity, metadata, relation, field type, system configuration representation, or ACL placement requires repository verification and a later precise file allowlist.

### 3.1 Explicit exclusions

RT-WP2 excludes:

- a fifth enum member or a `COMMERCIAL_BRIEF` capability;
- provider invocation, dispatch, execution requests, outbound connector calls, timeout handling, exactly-once behaviour, queues, workers, schedulers, background work, dead-letter processing, retry, backoff, reservation, lease, and concurrency control;
- C25 lifecycle code, CommercialBrief creation or mutation, Lead or Opportunity lifecycle work, scoring, ranking, qualification, prioritisation, and human bypass;
- plaintext API keys, access tokens, authorization headers, secret payloads, provider sessions, secret resolution, secret export, secret logging, and secret-bearing fixtures;
- implicit provider defaults, automatic fallback, environment-variable binding, adapter self-selection, and continuation after a missing binding;
- parallel authorization outside EspoCRM ACL, WorkflowAuthorization, or a verified system-configuration boundary.

## 4. Three-layer policy model

| Layer | Definition | Ownership and prohibition |
| --- | --- | --- |
| Capability | A member of the four-value `CompletionCapability` portfolio. | C20 portfolio governance owns it. A purpose does not expand it. |
| Purpose | A registered business/use-case identifier, for example commercial-brief preparation, sales-email drafting, qualification support, or reply assistance. | Purpose governance owns registration and approved mapping. No unregistered or free-form runtime purpose is valid. |
| Binding | A non-secret configuration relationship identifying candidate provider, capability, credential reference, allowed purpose, enabled state, approval, and provenance. | It determines eligibility only; it does not permit an adapter call. |

No capability or purpose implies a provider. No provider is inferred from a default, fallback, environment setting, caller input, or adapter preference. A multiple-active-candidate conflict must fail closed until an explicit, auditable rule is independently approved. The current connector's deterministic fallback is repository evidence only; this Charter neither adopts it as CRM policy nor permits it in a future runtime.

### 4.1 Candidate binding fields for future assessment

These are policy questions, not an implementation schema:

| Candidate field | Planning rationale | Boundary |
| --- | --- | --- |
| ID; name or label | Stable identity and operator comprehension | Must not encode secrets or an invocation target. |
| Capability | Explicit link to one existing portfolio value | No new enum or inferred capability. |
| Provider identity | Named policy candidate | Does not select, construct, or invoke an adapter. |
| Credential reference | Pointer to externally held credential custody | No secret value, decrypted value, header, or session. |
| Purpose | Registered business reason | Explicit and validated before eligibility. |
| Enabled/status | Administrative availability | Not an execution, retry, queue, or terminal state. |
| Created/modified by and at | Change provenance | General read visibility is a later ACL decision. |
| Approved by; provenance/audit reference | Approval evidence | Safe configuration changes and outcomes only. |

A later design must record for every candidate field whether it is required, platform-owned, serializable, logged, generally readable, and capable of leaking lifecycle or secret information. Secrets remain out of CRM records, logs, errors, exports, and fixtures.

### 4.2 Binding lifecycle

The future administrative lifecycle to assess is `DRAFT`, `ACTIVE`, `DISABLED`, and `REVOKED`. A smaller lifecycle is acceptable only if it retains explicit approval and revocation behaviour. These are configuration states, not execution states; RT-WP2 has no dispatched, running, completed, failed, retried, reserved, leased, queued, or cancelled state.

## 5. Purpose registration and mapping decisions

The following are required decisions before an implementation scope is proposed:

| Design question | Required decision boundary |
| --- | --- |
| Identifier grammar | Stable, namespaced, human-reviewable ID grammar. |
| Registration owner | Named C20 policy owner and approval role. |
| Capability mapping | Every registered purpose explicitly maps to one of the four existing values. |
| Multiplicity | Whether one purpose maps to more than one capability; default is no implicit many-to-many mapping. |
| Provider eligibility | Each binding explicitly declares its allowed purposes. |
| Validation point | Fail-closed validation before an eligibility result is accepted. |
| Change control | Approval, effective time, revocation, and provenance evidence. |
| Tenant and ACL boundary | Verified EspoCRM tenancy/ACL semantics before access design. |
| Audit visibility | Safe, non-secret configuration-change fields and authorized readers. |
| Extensibility | Deliberate registrations; no generic registry without repository evidence. |

CommercialBrief remains an explicit C25 purpose/business contract, not a new technical capability. `commercial_brief_generation` is not delivered or registered by this Charter and does not imply lifecycle inference, automatic execution, dispatch, or provider selection.

## 6. Eligibility and credential custody boundaries

A future policy-only resolver may return only:

`BOUND`, `UNBOUND`, `DISABLED`, `PURPOSE_NOT_REGISTERED`, `CAPABILITY_MISMATCH`, `CREDENTIAL_REFERENCE_MISSING`, or `NOT_AUTHORIZED`.

It must be deterministic, explicit, non-secret, auditable, and fail closed. It must not return or implement `PROVIDER_TIMEOUT`, `DISPATCH_FAILED`, `RETRY_PENDING`, `RESERVATION_CONFLICT`, or `EXECUTION_COMPLETED`.

Binding existence means only that a policy candidate was configured. It does not state that dispatch is authorized, a provider call is permitted, or retry/reservation mechanisms exist.

CRM custody is limited to a credential reference and safe policy status. Credential resolution and runtime secret custody remain with the connector/provider-runtime boundary. CRM must never copy, resolve, export, serialize, log, expose through exceptions, or place a secret in a fixture. Audit records may include only non-secret references, configuration decisions, and safe eligibility results.

## 7. Authorization, ACL, provenance, and threat boundaries

Any future access model must reuse verified EspoCRM ACL, WorkflowAuthorization, and system-configuration conventions. It must not create a parallel authorization path. Binding creation, approval, enabling, disabling, revocation, and read access require distinct least-privilege assessment. Generic record-edit permission alone is insufficient evidence for credential-reference or approval access.

| Threat | Prevention | Detection/evidence |
| --- | --- | --- |
| Fallback provider/default | Explicit approved binding and fail-closed conflict rule | Configuration review and candidate trace. |
| Hidden environment binding | No environment-derived policy input | Source and configuration-boundary review. |
| Stale credential reference | Explicit availability/status validation | Safe eligibility result and provenance. |
| Disabled binding reused | Disabled/revoked states are ineligible | Negative policy test. |
| Purpose/capability spoofing | Explicit registered mapping and validation | Mapping review and mismatch evidence. |
| Cross-tenant access | Verified EspoCRM tenancy/ACL boundary | Tenant-isolation test evidence. |
| Unauthorized edits | Separate approval and write permissions | Actor/time/provenance evidence. |
| Secret leakage | Reference-only CRM custody | Log, serialization, error, and fixture scans. |
| Audit tamper | Protected provenance decision | Authorized-change and mutation evidence. |
| C25 bypass | C25 owns no policy, selection, or lifecycle | C25-boundary regression review. |
| Adapter self-selection | Adapter receives no binding-policy authority | Connector contract review. |
| Ambiguous active candidates | Fail closed before an explicit conflict policy | Multiple-candidate negative test. |

## 8. Work-package boundaries

| Work package | Reserved responsibility | RT-WP2 boundary |
| --- | --- | --- |
| RT-WP3 | Dispatch/execution identity, provider invocation, exactly-once evidence | No invocation, request, dispatch, or log production. |
| RT-WP4 | Cancellation and terminal-reason contract | No lifecycle or terminal state. |
| RT-WP5 | Retry and backoff | No retry classification, scheduling, or backoff. |
| RT-WP6 | Reservation, lease, and concurrency | No reservation or concurrency behaviour. |
| RT-WP7 | Deferred invariant activation | No invariant-registry change or activation. |
| RT-WP8 | Runtime freeze and C25 dependency closure | No freeze claim or C25 gate release. |

## 9. Invariant relevance, unchanged status

| Invariant | Relevance | Intended future enforcement/evidence | Status |
| --- | --- | --- | --- |
| C20-INV-02 | No Prospecting identifiers in AIPlatform | Existing boundary regression evidence | ACTIVE; unchanged |
| C20-INV-03 | No CRM provider HTTP | Existing provider-isolation evidence | ACTIVE; unchanged |
| C20-INV-04 | Reference-only credential policy | Secret-leakage negative evidence | DEFERRED; unchanged |
| C20-INV-05 | No AIJob mutation ownership | RT-WP7 activation evidence | DEFERRED; unchanged |
| C20-INV-06 | No lifecycle ownership | RT-WP4/RT-WP7 evidence | DEFERRED; unchanged |
| C20-INV-07 | No execution-ledger ownership | RT-WP7 activation evidence | DEFERRED; unchanged |
| C20-INV-08 | No dispatch-to-log path | RT-WP3/RT-WP7 evidence | DEFERRED; unchanged |
| C20-INV-09 | No PromptTemplate mutation ownership | RT-WP7 evidence | DEFERRED; unchanged |
| C20-INV-10 | No retry policy | RT-WP5/RT-WP7 evidence | DEFERRED; unchanged |
| C20-INV-11 | No reservation/idempotency linkage | RT-WP6/RT-WP7 evidence | DEFERRED; unchanged |
| C20-INV-12 | Explicit transport construction remains outside policy | Adapter construction contract evidence | DEFERRED; unchanged |
| C20-INV-13 | No dry-run execution path | Execution-boundary regression evidence | DEFERRED; unchanged |

No invariant is activated, reclassified, or enforced by this Charter.

## 10. C25 boundary

CommercialBrief remains a C25 business entity and future output/purpose boundary. C25 cannot create a private binding, possess a secret, select a provider, perform dispatch, trigger retry/reservation, expand the capability portfolio, or bypass C20 authorization. C25 WP2.2 remains NO GO even after future RT-WP2 policy delivery unless all independent C20 and C25 gates are approved.

## 11. Future sequencing and controlled allowlist process

These planning labels are not authorized:

| Subunit | Planning subject |
| --- | --- |
| RT-WP2.1 | ProviderBinding contract metadata |
| RT-WP2.2 | Purpose registration and capability mapping |
| RT-WP2.3 | Eligibility resolution |
| RT-WP2.4 | Audit and boundary tests |

Before any one subunit proceeds, governance must approve its mapping, repository evidence, explicit non-goals, acceptance evidence, and precise file allowlist. The allowlist excludes C21–C25, dispatch, retries, reservations, AIJob changes, deployment changes, secrets, adapter changes, and capability-enum expansion unless distinct authority addresses that exact boundary.

Future tests include contract, security, no-execution, boundary, and regression evidence. This task produces no provider call, outbound egress, runtime metric, queue, retry, reservation, or execution result: each is zero.

## 12. Charter exit and authorization matrix

Charter exit requires independent review of repository evidence, the three-layer model, non-secret custody, no-dispatch boundary, unchanged invariants, C25 boundary, and absence of authorization escalation. Charter ratification is not implementation authority.

| Item | Status |
| --- | --- |
| RT-WP0 | EXITED |
| RT-WP1 | EXITED |
| RT-WP2 Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP2 Implementation | NOT AUTHORIZED |
| RT-WP3–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

No document, code, metadata, entity, scope, ACL, route, controller, service, guard, connector, credential, test, migration, or runtime action is automatically authorized by this Charter.

## 13. Exact next task

`Phase3C20 RT-WP2 Charter Documents Commit and Push`
