# Phase3C20 RT-WP3 Implementation Charter — Dispatch Foundation

| Field | Value |
| --- | --- |
| Document Type | RT-WP3 Dispatch Foundation Charter (planning only) |
| Work package | RT-WP3 — Controlled Dispatch Foundation |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed` → `b167275757f7a404ff8b4c09f037a63610bce142`) |
| Independent ratification review | PASS WITH INFORMATIONAL NOTES |
| Execution mode | Charter authoring only — no runtime, metadata, entity, service, test, connector, or C25 change |
| Implementation authorization | **NOT AUTHORIZED** |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
This charter defines the minimal Dispatch Foundation planning contract.
It creates no code, modifies no runtime, authorizes no implementation,
and does not release RT-WP3 implementation or any later work package.
```

---

## 1. Objective

Define the **minimal Dispatch Foundation** that connects an authorized
commercial AI request to a governed execution boundary without performing
provider execution.

The foundation establishes this irreversible chain:

```text
Request
  ↓
Purpose
  ↓
Capability
  ↓
ProviderBinding
  ↓
Execution Boundary
```

| Goal | Meaning |
| --- | --- |
| Dispatch contract | Explicit CRM-side orchestration contract for an authorized request |
| Capability resolution | Resolve against the frozen four-value `CompletionCapability` portfolio and registry family |
| Purpose validation | Fail-closed validation of registered purposes only |
| ProviderBinding selection policy | Consume RT-WP2 policy surface; produce an authorized candidate set |
| Eligibility validation | Deterministic policy classification; no execution authority |
| Execution request boundary | Normalized handoff shape to Connector — defined, not invoked |
| Audit provenance | Non-secret request/decision evidence references |

Non-goals of this foundation charter: provider adapter invocation, connector
runtime calls, outbound HTTP, retry, reservation, queue/worker/scheduler,
secret resolution, C25 lifecycle, or CommercialBrief execution.

---

## 2. Architecture Position

### 2.1 Position in the frozen chain

The Runtime Implementation Charter chain remains unchanged:

```text
CRM policy
→ authorized ProviderBinding set
→ CapabilityRegistry eligibility resolution
→ CRM governed dispatch orchestration
→ Connector outbound provider dispatch
→ Provider adapter / provider HTTP
```

RT-WP3 Foundation occupies **CRM governed dispatch orchestration through the
execution-request boundary only**. Nodes to the right of that boundary
(Connector outbound dispatch, adapter invocation, provider HTTP) remain
Connector-owned and are **not implemented by this foundation charter**.

### 2.2 Ownership terminology (mandatory)

```text
CRM owns governed dispatch orchestration.

Connector owns outbound provider dispatch, provider-adapter invocation,
transport execution, and provider HTTP.

CRM performs no outbound provider HTTP and invokes no provider SDK directly.
```

Do not use the unqualified phrase `dispatch owner`.

### 2.3 Preconditions already satisfied

| Predecessor | Status | Foundation dependency |
| --- | --- | --- |
| RT-WP0 | EXITED | Live contracts locked |
| RT-WP1 | EXITED | Capability/purpose delivery direction locked |
| RT-WP2 | COMPLETED + TAGGED at `b167275…` | ProviderBinding CRM policy surface exists |
| Four-value portfolio | Frozen | No fifth `CompletionCapability` |
| C20-INV-02 / C20-INV-03 | ACTIVE | Namespace isolation; no CRM provider HTTP |
| C20-INV-04–13 | DEFERRED | No activation by this charter |

---

## 3. Dispatch Responsibility

### 3.1 In scope (foundation)

| Responsibility | Owner | Boundary |
| --- | --- | --- |
| Accept a governed dispatch request | CRM dispatch orchestration | Human/operator or authorized system initiation only |
| Validate purpose | CRM | Against RT-WP2 purpose registration / binding `allowedPurposes` |
| Map/validate capability | CRM + frozen portfolio | Exactly one of the four portfolio values; registry family as required |
| Load authorized ProviderBinding set | CRM (RT-WP2 surface) | Policy records only; no discovery |
| Classify eligibility | CRM | Policy classifications only (see §6) |
| Assemble execution request boundary | CRM | Governance references only; no secrets |
| Record non-secret provenance | CRM | Decision/audit references; not an execution ledger of provider payloads |

### 3.2 Out of scope (forbidden in this charter)

| Forbidden | Reason |
| --- | --- |
| Provider execution implementation | Connector/adapter concern |
| Connector calls / `ConnectorBoundary.execute` invocation | Outbound execution; later separately authorized work |
| HTTP egress from CRM PHP | C20-INV-03 ACTIVE |
| Retry classification/executor | RT-WP5 |
| Idempotency reservation | RT-WP6 |
| Queue / worker / job scheduler | Not foundation; would expand runtime surface |
| Secret resolution / plaintext credentials | Connector custody |
| C25 lifecycle / CommercialBrief execution | C25 WP2.2 NO GO |
| AIJob cancel-reason contract | RT-WP4 |
| Invariant activation | RT-WP7 |

### 3.3 Planned primary artifact (future implementation only)

When separately authorized, the primary CRM orchestration service is expected
to be `AIDispatchService` (Runtime Charter §22). **This charter does not
authorize that file, Jobs, Api, routes, or tests.**

---

## 4. Request Contract

A foundation dispatch request is a **policy request**, not a provider call.

### 4.1 Required logical inputs

| Input | Rule |
| --- | --- |
| Request / correlation identity | Stable business or AIJob-linked identity; no secret material |
| Initiating actor | Authenticated human or authorized system principal |
| Purpose | Explicit registered purpose ID; never inferred from capability or C25 entity name |
| Capability | One of `RESEARCH_EVIDENCE`, `QUALIFICATION_INSIGHT`, `DRAFT_ASSISTANCE`, `REPLY_ASSISTANCE` for completion portfolio mapping; registry family `COMPLETION` (or `SEARCH`/`ENRICHMENT` only if separately in-scope for that request class) |
| Policy version | Non-secret policy/context version reference |
| Binding constraints | Optional filters; may not inject provider SDKs or secrets |
| Health input | Only as externally supplied normalized eligibility input (Runtime Charter §9.3); CRM does not probe |

### 4.2 Capability portfolio lock

Authoritative completion portfolio (unchanged):

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

```text
COMMERCIAL_BRIEF is not a CompletionCapability.
CommercialBrief is a C25 domain artifact / consumer boundary, not a capability.
commercial_brief_generation is not delivered or registered by this charter.
```

### 4.3 Forbidden request contents

- API keys, tokens, plaintext credentials, authorization headers
- Provider SDK handles or transport instances
- Implicit purpose derived from entity type alone
- C25 CommercialBrief mutation instructions
- Retry/reservation/queue control fields (owned by later WPs)

---

## 5. Resolution Flow

Foundation resolution is fail-closed and deterministic:

```text
1. Authorize caller (ACL / action authorization; Portal denied for operator surfaces)
2. Validate purpose (registered + grammar + not commercial_brief_generation unless later separately registered by C20 purpose governance)
3. Validate capability (four-value portfolio; reject COMMERCIAL_BRIEF)
4. Load ProviderBinding candidates from CRM policy surface (RT-WP2)
5. Filter by enabled/ACTIVE, allowedPurposes, supportedCapabilities, credentialReference presence
6. Apply selection policy (explicit, auditable; fail closed on unresolved multi-candidate conflict unless an independently approved rule exists)
7. Produce eligibility outcome + non-secret evaluation trace
8. If eligible: assemble Execution Request Boundary object (references only)
9. Stop at boundary — do not invoke Connector in this foundation charter
```

Capability Registry (`CapabilityRegistry.resolve`) remains the frozen
eligibility engine for connector-shaped binding tuples. CRM foundation work
**prepares** `allowed_provider_bindings` and related inputs; it does not
re-implement registry discovery or adapter construction.

---

## 6. ProviderBinding Interaction

### 6.1 Consumer of RT-WP2

RT-WP3 Foundation **consumes** the completed ProviderBinding CRM policy
surface. It must not redesign RT-WP2 fields, weaken credential-reference
rules, or register `commercial_brief_generation` by side effect.

### 6.2 Selection policy rules

| Rule | Requirement |
| --- | --- |
| Explicit binding only | No environment default, no hidden fallback, no adapter self-selection |
| Purpose gate | Purpose must appear on binding `allowedPurposes` and in the governed catalog |
| Capability gate | Binding `supportedCapabilities` must include the required registry family |
| Credential gate | Non-empty `credentialReference` required; never resolve the secret |
| Enabled gate | Binding must be `ACTIVE` and `enabled=true` |
| Conflict | Multiple eligible candidates → fail closed unless an auditable priority/selection rule is independently ratified |
| C25 | CommercialBrief owns no binding selection |

### 6.3 Eligibility classifications (policy only)

Reuse RT-WP2 policy classifications (and equivalents) such as:

`NOT_AUTHORIZED`, `UNBOUND`, `DISABLED`, `PURPOSE_NOT_REGISTERED`,
`CAPABILITY_MISMATCH`, `CREDENTIAL_REFERENCE_MISSING`, `BOUND`.

`BOUND` / eligible means **policy-configured for handoff**. It does **not**
authorize provider HTTP, retry, reservation, or job execution.

Forbidden classification meanings: `QUEUED`, `RUNNING`, `RETRY_PENDING`,
`DISPATCH_FAILED`, `RESERVATION_CONFLICT`, `PROVIDER_TIMEOUT`,
`EXECUTION_COMPLETED` as foundation eligibility outcomes.

---

## 7. Failure Semantics

| Failure class | Foundation behavior |
| --- | --- |
| Unauthorized caller | Reject; no binding evaluation side effects that leak policy beyond ACL |
| Invalid / unregistered purpose | Reject fail-closed |
| Forbidden capability (`COMMERCIAL_BRIEF`) | Reject fail-closed |
| No binding / disabled / purpose not allowed | Deterministic ineligible classification |
| Missing credential reference | Deterministic ineligible classification |
| Multi-candidate conflict without ratified rule | Fail closed |
| Secret-bearing input | Reject; never log or serialize secret values |
| Downstream connector/transport errors | **Out of foundation scope** — defined later with outbound dispatch authorization |

Foundation failures are policy/authorization failures. They must not trigger
retry executors, reservations, or outbound calls.

---

## 8. Security Boundary

| Requirement | Enforcement intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03; no SDK, curl, Guzzle, sockets in CRM dispatch foundation |
| Credential reference only | Pass references; never resolve, decrypt, or export secrets |
| No secret in logs/errors/exports/fixtures | Safe messages and non-secret provenance only |
| ACL / Portal | Operator dispatch surfaces Portal-denied; governed actions ≠ generic edit |
| Admin no-bypass of guards | Save-option / mutation patterns remain authoritative for AIJob/policy writes |
| No parallel authorization | Reuse EspoCRM ACL / verified system boundaries |
| Audit provenance | Record who/when/why at policy level; AIRequestLog human-review events remain forbidden (C25 owns its audit) |
| Health | Consume external normalized health input only; no CRM probing or live counters |

---

## 9. RT-WP4–RT-WP8 Separation

| Work package | Owns | Foundation must not absorb |
| --- | --- | --- |
| RT-WP4 | Cancel-reason contract on AIJob | Cancel semantics, reason fields |
| RT-WP5 | AIJob/Completion retry policy & executor | Retry budgets, backoff, auto-retry |
| RT-WP6 | Pre-dispatch idempotency reservation | Reservation persistence/acquisition |
| RT-WP7 | Invariant activation evidence | Registry status flips |
| RT-WP8 | Runtime freeze / C25 dependency closure docs | Freeze claims |

Shared-file rule (Runtime Charter §18.1): `AIDispatchService.php` primary
owner is RT-WP3 **when implementation is separately authorized**; RT-WP6 may
only add reservation call sites after RT-WP3 baseline freeze.

---

## 10. C25 Separation

```text
C25 WP2.2 remains NO GO.
```

| Rule | Statement |
| --- | --- |
| CommercialBrief | C25 domain artifact; not a capability; owns no ProviderBinding |
| Capability | Four-value portfolio only; `COMMERCIAL_BRIEF` forbidden |
| Purpose | `commercial_brief_generation` not registered by RT-WP3 Foundation |
| Dispatch | C25 may later consume a governed path; it may not own orchestration |
| Execution | No CommercialBrief creation/mutation/execution in RT-WP3 Foundation |
| Credentials / model selection | Never owned by C25 |

---

## 11. Test Strategy

When implementation is separately authorized, foundation tests must prove
contracts without network I/O or connector invocation:

| Category | Coverage |
| --- | --- |
| Contract | Request shape; purpose validation; four-value portfolio; binding selection inputs; eligibility matrix; execution-boundary DTO contains references only |
| Negative | `COMMERCIAL_BRIEF`; unregistered purpose; disabled binding; missing credential reference; secret-bearing fields; Portal denial |
| Isolation | No HTTP egress markers; no connector call sites in foundation unit under test; no retry/reservation/queue modules introduced by foundation allowlist |
| Regression | RT-WP2 ProviderBinding contracts remain green; C20-INV-02/03 ACTIVE; INV-04–13 DEFERRED unchanged |
| Cross-surface | Fixture binding shape remains consumable by frozen connector `ProviderBinding` / registry types **without** calling `resolve` against live providers |

No test in the foundation phase may perform provider HTTP or resolve secrets.

---

## 12. Exit Criteria

RT-WP3 **Foundation** may be considered charter-complete (for ratification of
this planning document) when:

1. This charter is independently reviewed and ratified.
2. Scope remains exactly the seven allowed surfaces in §1 / §3.1.
3. Forbidden surfaces in §3.2 remain excluded.
4. Four-value portfolio and CommercialBrief-non-capability rules are explicit.
5. RT-WP4–8 and C25 separations are explicit.
6. Implementation remains **NOT AUTHORIZED** until a separate implementation
   authorization and any required foundation gates (including AIJob ACL
   Foundation Gate before operator-visible dispatch) pass.

RT-WP3 **implementation** exit (Runtime Charter §22 / INV-08) is **out of
scope for this document** and requires later authorization covering outbound
dispatch orchestration, exactly-once AIRequestLog production, and related
evidence. This foundation charter does **not** claim that exit.

---

## Authorization Boundary

```text
Charter status:
RATIFIED

RT-WP3 Implementation:
NOT AUTHORIZED

Any runtime code:
NOT AUTHORIZED

RT-WP4–RT-WP8:
NOT AUTHORIZED

C25 WP2.2:
NO GO
```

Charter ratification approves **planning direction only**. It does not start
implementation, create allowlists for Jobs/Api/Connector calls, or authorize
commit/push/tag. Implementation remains NOT AUTHORIZED until a separate
implementation authorization is issued.

| Item | Status |
| --- | --- |
| RT-WP0 | EXITED |
| RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED |
| RT-WP3 Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP3 Implementation | NOT AUTHORIZED |
| RT-WP4–RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

---

## Final Decision

```text
RATIFIED — STATUS SYNCHRONIZED
```

Independent ratification review returned **PASS WITH INFORMATIONAL NOTES**.
No BLOCKER, HIGH, or MEDIUM finding alters scope. Charter status is therefore
synchronized to RATIFIED. Implementation remains NOT AUTHORIZED.

```text
Next Task:
Phase3C20 RT-WP3 Charter Documents Commit and Push
```

---

## References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§6, §9.3, §10, §11, §18.1, §22)
2. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
3. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
4. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
5. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
6. `docs/adr/C20_INVARIANT_REGISTRY.md`
7. Live tags: `phase3c20-rt-wp2-charter-ratified`, `phase3c20-rt-wp2-implementation-completed`
8. Live HEAD at charter drafting: `b167275757f7a404ff8b4c09f037a63610bce142`

---

*This charter is a planning document. It creates no production runtime change,
modifies no ProviderBinding implementation, stages no commit, and authorizes
no code. Dispatch foundation implementation begins only under a separate,
explicit authorization.*
