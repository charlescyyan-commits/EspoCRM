# ADR-C20: AI Platform Architecture

## Status

**Proposed** (WP0 documentation freeze — implementation gates remain for C20 WP1+)

### Acceptance record

- Phase3C20 WP0 documentation import, 2026-07-27
- Author self-review / advisory architecture review input: scoring authority,
  advisory `AIQualificationInsight`, and `AGENTS.md` egress constraints
- **Not Accepted.** Status remains Proposed until Phase3C20 Charter Approval Board
  ratification; §11.1 must be resolved by a human owner before WP2
- WP0 as originally drafted claimed documentation-only authorization; **as executed**
  at `962a7ae` it also included bounded additive BridgeError taxonomy parity — see §14
  and `docs/PHASE3C20_CHARTER.md` §7

## Date

2026-07-27

## Phase

Phase3C20 — AI Infrastructure Foundation

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting / AI Platform modules
- Phase3C20 Charter Approval Board

## Related

- `docs/architecture/BOUNDARIES.md` — connector ↔ engine / scoring prohibitions
- `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` — operator recovery pattern
- `docs/adr/ADR-C19_REPLY_EVENT_LIFECYCLE.md` — lifecycle ownership / mutation-guard pattern
- `AGENTS.md` / `CLAUDE.md` — repo-level Forbidden list (takes precedence until amended)
- Baseline: `phase3c19-freeze` @ `4a7a111`, release `1.9.12-alpha`
  (`E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218`)

## Governance Marker

**`adr-c20-aiplatform-v1`**

| Surface | Requirement |
| --- | --- |
| This ADR | Declares `adr-c20-aiplatform-v1` as the C20 AI Platform contract id |
| Metadata policy | Future AI Platform workflow/policy metadata must reference the same marker |
| Contract tests | Focused C20 tests must assert the marker string and the invariants in §8 |

**Relationship:** Additive. Does not amend or supersede ADR-C18-A6, ADR-C19, or the
navigation amendment chain. Constrained by `AGENTS.md` / `CLAUDE.md` and
`docs/architecture/BOUNDARIES.md`, both of which take precedence over this document
until formally amended (§11.1).

> **Naming note.** `docs/adr/README.md` specifies `NNNN-short-title.md`. Actual practice
> is phase-scoped (`ADR-C18-A6_…`, `ADR-C19_…`). This ADR follows actual practice for
> consistency with its siblings. The README convention should be reconciled to practice
> or practice migrated to the README — a docs-only decision for C20 WP0.

---

## 1. Context

### 1.1 What Phase3C19 established

C19 froze a prospecting pipeline with five properties this ADR depends on and must not
weaken:

| Property | Mechanism |
| --- | --- |
| **Lifecycle ownership is singular** | One transition service per lifecycle: `SendExecutionTransitionService`, `ReplyTriageService`, `QuoteTransitionService`, `ApprovalService` |
| **Status mutation is guarded at persistence** | Four hook guards (`ReplyEvent`, `Quote`, `SendExecution`, `Approval`) gated by `StatusMutationSaveOption` — a stray `saveEntity` cannot move status |
| **Authorization is keyed and centralized** | `WorkflowAuthorizationService` + action keys in `Resources/metadata/app/prospectingWorkflow.json` |
| **Queues are predicates, not entities** | Server-side `PrimaryFilters` over `ProspectPool` / `ReplyEvent` / `SendExecution` / `Lead` |
| **Provider facts are immutable** | `ReplyEvent.replyStatus` write-once at ingress; `triageStatus` is the separate mutable work dimension |

The extension modifies no EspoCRM core: the shipped payload is confined to
`files/custom/` and `files/client/custom/`. All 14 record scopes carry `acl: true`.

### 1.2 The constraint that shapes this decision

`AGENTS.md` and `CLAUDE.md` (identical) state, verbatim under **Forbidden**:

- Modify Chitu scoring logic
- Modify AI research logic
- Modify the email-generation engine
- Modify unrelated Chitu application code
- Import real customer data or enable outreach without explicit approval

And: *"Keep the connector independent by importing only `chitu_connector` and its vendored
stable interfaces."*

`docs/architecture/BOUNDARIES.md` §2 reinforces this: live Engine / DeepSeek / crawler
runtime is **"Out of scope — must not be imported"**, and scoring logic changes are
**"Forbidden per AGENTS.md / CLAUDE.md"**.

**This is the central fact of C20.** A naive AI Platform design — a PHP module that holds
LLM credentials and calls DeepSeek to score prospects — would violate three of the five
prohibitions and duplicate capability that already exists. The architecture must be built
around the constraint, not in spite of it.

### 1.3 What Chitu already owns

The vendored contract surface at `chitu-connector/chitu_connector/vendored/contracts/`
enumerates capabilities that already have an owner:

| Contract | Capability |
| --- | --- |
| `canonical_score.py`, `scoring.py` | Prospect scoring |
| `icp.py` | Ideal customer profile definition |
| `business_qualification.py` | Qualification determination |
| `website_research.py` | Website research |
| `single_candidate_loop.py` | Candidate processing loop |
| `entity_identity.py`, `search_result.py` | Identity resolution, search result shape |

The connector holds the integration-side counterparts: `website_research.py`,
`evidence_extraction.py`, `master_prospect.py`, `normalization.py`.

**Consequence for the entity model:** an EspoCRM-computed `AIScore` would create a second
scoring authority competing with `canonical_score`. That is the same defect class as
introducing a `Prospect` entity alongside the existing `ProspectPool` and `Lead` — a
duplicate identity that no later decision resolves. §6 rejects it accordingly.

#### AIQualificationInsight (advisory layer)

`AIQualificationInsight` is **allowed** as an advisory AI layer. Full architecture,
provenance requirements, and restrictions are defined in **§6.4**.

| Rule | Decision |
| --- | --- |
| Canonical score owner | **Chitu** owns `canonical_score` |
| Authoritative scoring | AI does **not** create authoritative scoring |
| Qualification authority | AI does **not** replace qualification authority |
| Lifecycle mutation | AI does **not** mutate lifecycle status |

**Do not create `AIScore`.** Persist Chitu's canonical score with provenance, or nothing.

### 1.4 What the connector provider layer already provides

`chitu-connector/chitu_connector/acquisition/providers/` is a mature, correctly-shaped
abstraction that C20 should extend rather than replace:

```python
class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...

class ProviderAdapter(Protocol):
    @property
    def name(self) -> str: ...
    def search(self, request: SearchRequest) -> ProviderResult: ...
```

With `apify_provider.py` and `serper_provider.py` implementing it. Two details are worth
naming because they are already right:

- **No default transport.** `ApifyProvider.__init__` requires an injected `HttpTransport`;
  the module docstring states the default is *deliberately absent*. Accidental live egress
  is structurally impossible.
- **Secrets are non-reprable.** `config.py` loads credentials from environment with
  `field(repr=False)`, so a traceback or log line cannot leak a token.

The CRM side has the matching normalization half: `BridgeErrorClass`,
`BridgeNormalizedStatus`, `BridgeRejectionException`, `SendExecutionBridgeResult`.

*Note: `BOUNDARIES.md` §3 lists "Google / Apify / live providers — **Not Implemented**"
and cites `acquisition/provider.py`. Both are stale — `providers/apify_provider.py` and
`providers/serper_provider.py` exist alongside `provider.py`. BOUNDARIES.md needs a
refresh in C20 WP0.*

### 1.5 What is genuinely missing

Not AI capability. **Governance of AI capability.**

| Gap | Consequence today |
| --- | --- |
| No credential custody in CRM | Provider keys live only in connector environment; no admin surface, no rotation, no audit of access |
| No job record | An AI invocation leaves no CRM-visible trace; failures are invisible to operators |
| No cost accounting | Token and currency spend is unattributable to a prospect, user, or campaign |
| No prompt versioning | Output cannot be explained after a prompt changes |
| No provider routing configuration | Provider choice is code, not configuration |
| No health signal | No basis for fallback when a provider degrades |
| No operator recovery for AI failures | The C19 WP2 recovery pattern has no AI-side equivalent |

C20 closes the governance gap. It does not build a second AI engine.

---

## 2. Decision

### D1 — AI capability lives in a dedicated module, not inside Prospecting

Create `Modules/AIPlatform` with a **one-way dependency**:

```
Modules/AIPlatform      provider-agnostic, prospecting-agnostic
        ▲
        │ depends on (interfaces only)
        │
Modules/Prospecting     business pipeline (C19-frozen)
```

`AIPlatform` must never reference `Lead`, `ProspectPool`, `SearchJob`, `DraftApproval`,
`SendExecution`, `ReplyEvent`, or any other prospecting concept. Callers pass normalized
payloads. Enforced by a contract test (§8.2).

**Rationale, in order of weight:**

1. **Different failure modes.** Prospecting failures are logic errors. Provider failures
   are timeouts, rate limits, quota exhaustion, cost overruns, and non-deterministic
   output. Coupling them makes every frozen prospecting test inherit network flakiness.
2. **Different change cadence.** Provider APIs churn monthly; the C19 lifecycle is under
   freeze discipline. Coupling forces churn through frozen code.
3. **Credential blast radius.** One auditable ACL surface for secrets rather than secrets
   scattered through a business module.
4. **Reuse.** Quote generation and sales-feedback summarization will want the same
   platform. If it lives inside Prospecting, the second consumer forces a refactor.
5. **Precedent.** `chitu-connector` is already a separated boundary. This continues an
   established pattern rather than inventing one.

**`Modules/Automation` is not created in C20.** An empty module invites premature
abstraction. Create it in C22 when there are two concrete automations to generalize from.

### D2 — Capability custody: EspoCRM governs, it does not compute

**This is the load-bearing decision.**

| Capability class | Owner | EspoCRM AIPlatform role |
| --- | --- | --- |
| Scoring, ICP, qualification, website research, email generation | **Chitu** (existing, per §1.3 and `AGENTS.md`) | **Consume and persist.** Never reimplement, never compute a competing value. |
| Capabilities Chitu does not own (e.g. Apollo / Hunter enrichment) | **Connector provider layer** (new adapters) | **Configure, invoke via connector, audit.** Never call from PHP. |
| Credential custody, routing configuration, job orchestration, cost accounting, prompt versioning, audit, operator recovery | **EspoCRM AIPlatform** | **Own outright.** This is the module's actual purpose. |

The module's job is custody, orchestration, and audit — not inference.
Advisory `AIQualificationInsight` (§1.3) is permitted only as non-authoritative output
under this custody model.

### D3 — Single egress point

**All outbound provider I/O goes through the connector.** No PHP code in either module
opens an HTTP connection to Apify, Apollo, Hunter, DeepSeek, OpenAI, Anthropic, Moonshot,
Instantly, or Brevo.

Rationale: one egress point can be rate-limited, cost-capped, credential-scoped,
recorded, and replayed in tests. Two cannot — and a second stack in PHP would duplicate
the transport injection and secret-hygiene work already done correctly in `config.py`.
This also preserves the `AGENTS.md` rule that the extension never imports Python and the
connector never writes PHP metadata: the boundary stays a contract, not a call.

### D4 — The direct-LLM question is escalated, not assumed

C20 may need LLM invocation for a capability Chitu does not own. Three options were
considered:

| Option | Description | Assessment |
| --- | --- | --- |
| **A** | EspoCRM PHP calls LLM providers directly | **Rejected.** Violates D3; creates a second egress point and a second scoring authority; contradicts `BOUNDARIES.md` §2. |
| **B** | All AI arrives from Chitu; EspoCRM never invokes a model | **Compliant but insufficient.** Blocks enrichment and any capability Chitu does not own. |
| **C** | **Custody split by ownership** (D2) — Chitu capabilities consumed as-is; non-Chitu capabilities get new connector adapters | **Recommended.** Respects every `AGENTS.md` prohibition while unblocking C20. |

**Option C is recommended.** It does not resolve one residual question: whether adding a
`CompletionProvider` adapter to the connector for a *non-Chitu* purpose constitutes
"modifying AI research logic." This ADR takes the position that it does not — the
prohibition protects Chitu's existing logic, not the creation of new, separately-owned
capability — **but that reading requires ratification before C20 WP2 begins** (§11.1).
No implementation may proceed on the assumption.

---

## 3. Module and Dependency Architecture

```
┌───────────────────────────────────────────────────────────────┐
│ EspoCRM                                                       │
│                                                               │
│  Modules/Prospecting  (C19-frozen)                            │
│    ProspectPool  Lead  ResearchEvidence  DraftApproval        │
│    SendExecution  ReplyEvent  SearchJob  SearchStrategy       │
│         │ requests capability via AIPlatform interfaces       │
│         ▼                                                     │
│  Modules/AIPlatform  (C20, new)                               │
│    AIJob  AIRequestLog  PromptTemplate                        │
│    ProviderCredential  ProviderHealth  ProviderRoute          │
│    AIJobService · CredentialCustodyService · RoutingService   │
│         │ contract call only — no HTTP, no Python import      │
└─────────┼─────────────────────────────────────────────────────┘
          ▼
┌───────────────────────────────────────────────────────────────┐
│ chitu_connector  (sole egress)                                │
│   acquisition/providers/  base.py  apify  serper  + new       │
│   vendored/contracts/     canonical_score  icp  scoring  …    │
└─────────┼─────────────────────────────────────────────────────┘
          ▼
   Chitu engine (unmodifiable)   ·   External providers
```

**Invariant:** arrows point one way. `AIPlatform` never imports Prospecting;
Prospecting never opens a socket; the connector never writes PHP metadata or SQL.

---

## 4. Provider Abstraction

### 4.1 Capability ports

Generalize the existing `ProviderAdapter` Protocol **by capability, not by vendor**:

| Port | Method | Candidate implementations |
| --- | --- | --- |
| `SearchProvider` | `search(SearchRequest) → ProviderResult` | Apify *(exists)*, Serper *(exists)* |
| `EnrichmentProvider` | `enrich(EnrichmentRequest) → EnrichmentResult` | Apollo, Hunter |
| `CompletionProvider` | `complete(CompletionRequest) → CompletionResult` | subject to §11.1 ratification |
| `EmailDeliveryProvider` | `send(DeliveryRequest) → DeliveryResult` | Instantly, Brevo, SMTP — **C21, not C20** |

### 4.2 Rules

| # | Rule | Rationale |
| --- | --- | --- |
| 4.2.1 | **No vendor type crosses the adapter boundary.** No provider-native object or JSON shape appears in any caller. | The only durable defense against lock-in. Swapping providers becomes one new adapter file. |
| 4.2.2 | **Transport stays injected, with no default.** | Preserves the existing property that accidental live egress is impossible, and keeps recorded-fixture testing viable. |
| 4.2.3 | **Errors normalize into one taxonomy** (§4.3). | Retry policy keys off the taxonomy, never off vendor error codes. |
| 4.2.4 | **Every result carries a cost envelope**: tokens in/out, model, latency, provider request id, currency amount. | Cost accounting cannot be retrofitted. It belongs in the result type on day one. |
| 4.2.5 | **Every request carries a caller-supplied idempotency key**, persisted before dispatch. | Providers time out *after* doing the work. Without this you double-invoke and double-bill. |
| 4.2.6 | **Adapters declare capabilities** (streaming, JSON mode, max context, vision). | Enables data-driven routing and prevents "provider B silently ignored our flag." |
| 4.2.7 | **Routing is configuration, not code** — `(capability, purpose) → provider + model`, editable in Administration. | Satisfies "no hardcoded providers"; provider switch becomes a config change. |
| 4.2.8 | **Secrets never enter a `__repr__`, log line, or exception message.** | Extends the existing `field(repr=False)` discipline to all new config types. |

### 4.3 Normalized error taxonomy

Extend `BridgeErrorClass` rather than introducing a parallel enum.

`RATE_LIMIT` already exists in `SendExecution.failureCategory` and provider contracts.
`BridgeErrorClass` parity should include `RATE_LIMIT`.

**New additions** (not previously on `BridgeErrorClass`):

- `QUOTA`
- `CONTENT_FILTER`

| Class | Status | Retryable | Handling |
| --- | --- | --- | --- |
| `NETWORK` | Existing on `BridgeErrorClass` | Yes | Backoff + jitter |
| `PROVIDER` | Existing on `BridgeErrorClass` | Yes (5xx only) | Backoff; fail over via `ProviderRoute` |
| `AUTH` | Existing on `BridgeErrorClass` | **No** | Terminal; raise credential alert |
| `VALIDATION` | Existing on `BridgeErrorClass` | **No** | Terminal; caller defect |
| `UNKNOWN` | Existing on `BridgeErrorClass` | **No** | Terminal; operator review |
| `RATE_LIMIT` | Existing elsewhere; add for `BridgeErrorClass` parity | Yes | Respect `Retry-After`; do not count against attempt budget |
| `QUOTA` | **New** | **No** | Terminal; halt the capability, alert admin — retrying burns money |
| `CONTENT_FILTER` | **New** | **No** | Terminal; never auto-retry a refusal with the same prompt |

`RATE_LIMIT` and `QUOTA` are the two classes most commonly conflated. Conflating them
converts a transient pause into unbounded spend.

---

## 5. Credential Custody and Configuration Center

### 5.1 Administration surface

```
Administration
└── AI Platform
    ├── Providers        registered adapters + declared capabilities (read-only)
    ├── Credentials      ProviderCredential — write-only, admin-only
    ├── Routes           (capability, purpose) → provider + model
    ├── Models           model registry with context limits and unit costs
    ├── Prompt Templates versioned, immutable once referenced
    ├── Usage Logs       AIRequestLog — read-only, never editable
    └── Health           ProviderHealth — scheduled check results
```

### 5.2 Encryption

| Aspect | Decision |
| --- | --- |
| At rest | Envelope encryption. DEK per credential; ciphertext in DB. |
| Key custody | KEK from environment or secret manager — **never** stored in the database. A KEK in the same store as its ciphertext is not encryption. |
| In transit to connector | Never as a request parameter. The connector resolves credentials from its own environment; EspoCRM stores a **reference plus metadata**, not the secret. |
| Write path | Write-only field. Set and rotate, never read back. |
| Display | Masked (last 4 characters) plus fingerprint hash for identification. |
| Plaintext exposure | Never returned to any client, never logged, never in an exception. |

**Preferred posture:** EspoCRM holds credential *metadata, ownership, rotation schedule,
and audit trail*; the connector holds the actual secret in its environment. This keeps the
CRM database out of scope for secret exfiltration entirely. Where the CRM must hold a
secret, envelope encryption applies as above.

### 5.3 Permissions

| Surface | Access |
| --- | --- |
| `ProviderCredential` | Admin only — create, rotate, delete. **No read of plaintext by anyone.** |
| `ProviderRoute`, `PromptTemplate` | Admin write; role-gated read |
| `AIRequestLog` | Read-only for managers; **no edit or delete for anyone**, including admin |
| `AIJob` | Read per ACL; status mutation only via `AIJobService` |
| `ProviderHealth` | Read-only; written by scheduled job |

### 5.4 Audit

Every credential **read attempt** is logged, not only writes. Write-only audit answers
"who changed the key" but not "what used it at 3am." Log: actor, timestamp, credential
fingerprint, purpose, outcome. Rotation and deletion are audited events, and audit records
are append-only under the same guard discipline as `ReplyEvent`.

### 5.5 Cost tracking

`AIRequestLog` is the single source of spend truth: provider, model, tokens in/out,
currency amount, latency, `AIJob` link, initiating user, prompt template version, outcome
class. Cost aggregation is a read over this table — **not** a separate counter that can
drift. Admin-configurable soft and hard spend ceilings per capability, evaluated before
dispatch; hard ceiling breach fails the job with `QUOTA` rather than proceeding.

### 5.6 Health checks

Scheduled job per registered provider writing `ProviderHealth`: reachability,
authentication validity, latency percentile, error rate. Health is **advisory input to
routing**, never an automatic credential change. A degraded provider may be routed around;
it is never silently disabled.

---

## 6. Entity Model

### 6.1 Required in C20

| Entity | Purpose | Lifecycle owner |
| --- | --- | --- |
| `AIJob` | One unit of async capability work; one row per invocation attempt group | `AIJobService` (§7) |
| `AIRequestLog` | Append-only record of every provider invocation with cost | None — immutable, guard-enforced |
| `PromptTemplate` | Versioned prompt; immutable once referenced by a log row | `PromptTemplateService` |
| `ProviderCredential` | Credential metadata and custody (§5.2) | `CredentialCustodyService` |
| `ProviderRoute` | `(capability, purpose) → provider + model` | Admin CRUD, no lifecycle |
| `ProviderHealth` | Scheduled check results | Written by job only |

### 6.2 Reuse — do not duplicate

| Existing | Use for |
| --- | --- |
| `ProspectPool` | Pre-CRM candidate identity. Extend with pipeline stage; do not replace. |
| `Lead` | CRM-accepted identity |
| `ResearchEvidence` | Research artifact store. Add provenance link to `AIRequestLog`. |
| `DraftApproval` | The email draft **and** its approval gate. Do not add a parallel `EmailDraft`. |
| `SendExecution`, `ReplyEvent` | C19-frozen. No change. |
| `Opportunity` | Core EspoCRM. Do not reimplement. |

### 6.3 Rejected vs accepted (scoring and identity)

| Candidate | Decision | Reason |
| --- | --- | --- |
| `Prospect` | **Rejected** | Duplicates `ProspectPool` and `Lead`. A third overlapping identity that no later decision resolves. |
| `AIScore` **as a computed value** | **Rejected** | Chitu owns `canonical_score` (§1.3). An EspoCRM-computed score creates a competing authority. **If a score is needed, persist Chitu's canonical score with provenance — do not compute one.** This revises the earlier C21 recommendation. **Do not create `AIScore`.** |
| `AIQualificationInsight` | **Accepted as advisory layer** | Contextual intelligence only. Not a score, not qualification authority, not a lifecycle decision (§6.4). |
| `EmailCampaign` | **Deferred** | C22. Premature in C20/C21; tends to accrete scheduling logic belonging elsewhere. |
| `EmailAccount` | **Deferred** | C21, with `EmailDeliveryProvider`. Out of C20 scope — C20 sends nothing. |

**Clarify:** Chitu owns canonical scoring **and** qualification decisions. AI provides
contextual intelligence only. EspoCRM stores, displays, and orchestrates — it does not
calculate qualification verdicts.

### 6.4 `AIQualificationInsight` architecture

#### Purpose

Advisory AI-generated qualification insight — a dynamic qualification layer that explains
context for operators. It is **not** a second scoring engine.

#### Qualification decision ownership

| Role | Owner |
| --- | --- |
| Qualification **decisions** | **Chitu** |
| `AIQualificationInsight` | **Advisory only** |
| EspoCRM | **Stores**, **displays**, and **orchestrates workflow** |

EspoCRM must **NOT** calculate qualification verdicts from:

- `canonical_score`
- `AIQualificationInsight`
- confidence

No C20 service, controller, workflow, or filter may become qualification decision
authority. That authority remains with Chitu.

#### It is NOT

- an authoritative score
- qualification authority
- a lifecycle decision

#### It MAY contain

- dynamic market signals
- buying intent signals
- contextual reasoning
- confidence explanation

#### It MUST include provenance

| Field | Requirement |
| --- | --- |
| `AIRequestLog` reference | Required link to the invocation that produced the insight |
| `PromptTemplate` version | Required; immutable once referenced |
| provider | Required |
| model | Required |
| timestamp | Required |
| actor | Required (initiating user or system actor) |

May also reference `ResearchEvidence` where the insight draws on stored research artifacts.

#### Full immutability after create

The **entire** `AIQualificationInsight` entity is immutable after creation — not only
provenance fields.

| Rule | Decision |
| --- | --- |
| Update | **No** update path after create |
| Delete | **No** delete path for any role |
| Corrections | Create a **new superseding** insight; do not mutate the prior row |
| History | Prior rows are preserved; current insight is derived from **supersession ordering** |

**Do not** introduce a mutable `isCurrent` (or equivalent) flag. “Current” is computed
from the supersession chain / ordering, never from an editable boolean.

#### Restrictions

| Restriction | Rule |
| --- | --- |
| Canonical score | **Cannot** modify `canonical_score` |
| Chitu qualification | **Cannot** override Chitu qualification |
| Prospecting lifecycle | **Cannot** mutate Prospecting lifecycle status or fields |
| PrimaryFilter / queues | **Cannot** be used as PrimaryFilter authority or lifecycle queue authority |
| Research logic | **Cannot** replace Chitu research logic |
| Qualification verdicts | EspoCRM **cannot** derive a qualification verdict from score, insight, or confidence |

#### Lifecycle ownership

`AIQualificationInsight` has **no lifecycle ownership** and no transition service.
The entity is fully immutable after create. No Prospecting transition service may read it
to drive state changes.

### 6.5 Lifecycle ownership pattern

Every new entity with a status adopts the four-part C19 pattern without variation:

1. Exactly one transition service owning all status writes
2. Action keys registered in workflow metadata
3. A hook guard gated by a save option, so a stray `saveEntity` cannot move status
4. An ADR with a numbered invariant list driving contract tests

This pattern is why the C19 lifecycle code is trustworthy. It is inherited, not redesigned.

---

## 7. `AIJob` Lifecycle

### 7.1 States

| State | Meaning |
| --- | --- |
| `QUEUED` | Accepted, not dispatched |
| `RUNNING` | Dispatched to connector; awaiting result |
| `SUCCEEDED` | Result persisted; terminal |
| `FAILED` | Terminal error or attempt budget exhausted; **operator-recoverable** |
| `CANCELLED` | Operator abandoned; terminal, requires `cancelReason` |

### 7.2 Transitions

```text
(create)   → QUEUED      (ingress only — never a service action)
QUEUED     → RUNNING     (aiJob.dispatch — system)
QUEUED     → CANCELLED   (aiJob.cancel — reason required)
RUNNING     → SUCCEEDED   (aiJob.complete — system)
RUNNING     → FAILED      (aiJob.fail — system, with failureCategory)
RUNNING     → QUEUED      (aiJob.requeue — retryable class only, increments attemptCount)
FAILED      → QUEUED      (aiJob.retry — operator, resets attempt budget)
FAILED      → CANCELLED   (aiJob.cancel — reason required)
```

`SUCCEEDED` and `CANCELLED` are terminal. `FAILED` is deliberately **not** terminal —
this mirrors the C19 WP2 `SendExecution` recovery pattern, where a `FAILED` record has an
authorized operator path rather than becoming a dead row.

### 7.3 Action keys

| Key | Transition | Actor | Reason required |
| --- | --- | --- | --- |
| `aiJob.dispatch` | `QUEUED → RUNNING` | System | No |
| `aiJob.complete` | `RUNNING → SUCCEEDED` | System | No |
| `aiJob.fail` | `RUNNING → FAILED` | System | No — `failureCategory` instead |
| `aiJob.requeue` | `RUNNING → QUEUED` | System | No |
| `aiJob.retry` | `FAILED → QUEUED` | Operator | No |
| `aiJob.cancel` | `QUEUED\|FAILED → CANCELLED` | Operator | **Yes** |

Registered in `Resources/metadata/app/` and bound through the existing
`WorkflowAuthorizationService` pattern. Unauthorized attempts return `403 Forbidden` with
zero writes.

### 7.4 Retry strategy

| Aspect | Decision |
| --- | --- |
| Eligibility | Retryable classes only (§4.3). `AUTH`, `VALIDATION`, `QUOTA`, `CONTENT_FILTER` never auto-retry. |
| Backoff | Exponential with jitter. `RATE_LIMIT` honours `Retry-After` and does not consume attempt budget. |
| Budget | `maxAttempts` per capability, configurable; default conservative. Exhaustion → `FAILED`. |
| Idempotency | The key from §4.2.5 is persisted before dispatch and reused on every retry, so a retry after a provider-side success does not duplicate work or spend. |
| Cost ceiling | Evaluated before each attempt, not only at job creation. |
| Dead letter | `FAILED` **is** the dead-letter state, made operable by `aiJob.retry` / `aiJob.cancel` and surfaced as a command-centre queue predicate (`c20FailedAiJobs`), consistent with `c18FailedSend`. |

### 7.5 Failure visibility

An AI failure must be operator-visible, not log-only. `AIJob.FAILED` records carry
`failureCategory` and `lastError` and appear in a dashboard queue. The C19 charter finding
F5 — *FAILED records with no authorized recovery path* — is not to be recreated on the AI
side.

---

## 8. Invariants for Contract Tests (C20 gates)

1. Marker `adr-c20-aiplatform-v1` present in AI Platform metadata and contract tests.
2. **No prospecting identifier** (`Lead`, `ProspectPool`, `SearchJob`, `DraftApproval`,
   `SendExecution`, `ReplyEvent`, `Quote`) appears anywhere in `Modules/AIPlatform`.
3. **No outbound HTTP from PHP.** No `curl`, `file_get_contents` on an external URL,
   Guzzle, or socket call in either module targeting a provider domain.
4. No plaintext credential is returned by any API response, written to any log, or present
   in any exception message. Credential fields are write-only.
5. Every `AIJob` status write passes through `AIJobService` with the authorized save
   option; the hook guard rejects direct mutation.
6. `AIJob` transitions are limited to the §7.2 matrix; action keys as §7.3;
   `SUCCEEDED` and `CANCELLED` have no outgoing transitions; `CANCELLED` requires a reason.
7. `AIRequestLog` is append-only — no update or delete path exists for any role.
8. Every completed provider invocation produces exactly one `AIRequestLog` row carrying
   provider, model, tokens, cost, latency, and `PromptTemplate` version.
9. A `PromptTemplate` version referenced by any `AIRequestLog` row cannot be edited —
   only superseded by a new version.
10. Retry eligibility is determined solely by the §4.3 taxonomy; `AUTH`, `VALIDATION`,
    `QUOTA`, and `CONTENT_FILTER` produce zero retry attempts.
11. Idempotency key is persisted before dispatch and identical across retries of the same
    logical invocation.
12. No adapter is constructed without an explicit transport; no default transport exists.
13. Dry-run mode produces a complete `AIJob` + `AIRequestLog` trace with **zero network
    egress** (fixture-backed).
14. `EspoCRM` computes no score: no `canonical_score` equivalent is calculated in either
    module. Scores are persisted from Chitu with provenance only. No `AIScore` entity.
15. C20 ships **no email-sending path**: no `EmailDeliveryProvider` implementation, no
    send action, no `SendExecution` write from `AIPlatform`.
16. `AIQualificationInsight` is advisory only. It must not set, update, or compete with
    `canonical_score`; must not replace Chitu qualification decisions; and must not
    mutate Prospecting lifecycle status or fields.
17. `AIQualificationInsight` has **no lifecycle ownership** — no status field, no
    transition matrix, no owning transition service.
18. **No transition service** (Prospecting or AIPlatform) may read
    `AIQualificationInsight` to drive state changes.
19. **No write path to `canonical_score`** exists from `AIQualificationInsight`,
    `AIPlatform`, or any C20 advisory surface.
20. The entire `AIQualificationInsight` entity is **immutable after create** — no update
    and no delete for any role. Corrections create a new superseding insight; history is
    preserved. Current insight is derived from supersession ordering. A mutable
    `isCurrent` (or equivalent) flag is **forbidden**.
21. EspoCRM must not calculate qualification verdicts from `canonical_score`,
    `AIQualificationInsight`, or confidence. **No C20 service, controller, workflow, or
    filter may become qualification decision authority** — Chitu owns that authority.
22. `AIQualificationInsight` must not be used as PrimaryFilter authority or as lifecycle
    queue authority.

---

## 9. Consequences

### Positive

- Provider substitution becomes a configuration change plus one adapter file.
- Every AI invocation is attributable to an actor, a prompt version, and a cost.
- Credentials have one auditable custody surface with rotation and access logging.
- The C19 frozen lifecycle is untouched; AI failures cannot corrupt prospecting state.
- One egress point remains rate-limitable, cost-cappable, and replayable in tests.
- `AGENTS.md` prohibitions are respected by construction rather than by reviewer vigilance.
- Advisory `AIQualificationInsight` can surface market/intent context without creating a
  second scoring authority.

### Negative / accepted costs

- An indirection through the connector for every provider call. Accepted: the alternative
  is a second egress stack and a second secret store.
- Chitu remains a hard dependency for scoring, ICP, qualification, and research. If Chitu
  is unavailable, those capabilities are unavailable. This is a deliberate consequence of
  not duplicating logic the workspace is forbidden to modify.
- Two-language debugging (PHP + Python) for provider issues. Mitigated by the normalized
  error taxonomy and `AIRequestLog` correlation ids.
- `PromptTemplate` immutability means version proliferation. Accepted: explicability of
  historical output is worth the row count.

### Follow-up work

- §11.1 ratification **before** WP2.
- Refresh `BOUNDARIES.md` §2 and §3 (both stale — §1.4, §1.2).
- Reconcile the ADR naming convention (header note).
- Close C19 debt in WP0: canonical `pytest.ini`, the two stale C14 assertions, charter
  entry for WP1.5, retro-charter for the Intelligence Center Research Workbench.
- Apply the UI Runtime Artifact Parity Gate to any C20 admin UI.

---

## 10. Scope and Exclusions for Phase3C20

### In scope

| WP | Content |
| --- | --- |
| WP0 | This ADR ratified; credential-encryption ADR; `AIJob` lifecycle ADR; BOUNDARIES refresh; C19 debt closure |
| WP1 | `Modules/AIPlatform` skeleton; `ProviderCredential`; Administration → AI Platform |
| WP2 | Capability ports; `EnrichmentProvider` adapter; recorded-fixture tests *(gated on §11.1)* |
| WP3 | `AIJob`, `AIRequestLog`, `PromptTemplate` with guards, cost accounting, health checks |
| WP4 | Test infrastructure: `pytest.ini`, stale-assertion fixes, `BUILD_INFO` provenance stamp |
| WP5 | Vertical slice: operator-triggered AI-assisted research on **one** `ProspectPool` record, writing `ResearchEvidence`. **WP5 consumes Chitu-owned or connector-provided research outputs. No duplicate AI research engine. No modification of AI research logic.** |

### Explicitly excluded

- **Any email sending.** No delivery provider, no send action, no `SendExecution` write.
- **Any scoring computation.** Persist Chitu's canonical score or nothing. **No `AIScore`.**
- **Any autonomous trigger.** Every C20 invocation is operator-initiated.
- **Any auto-approval or policy guard.** C22 concern.
- `Modules/Automation`, `EmailCampaign`, `EmailAccount`, `AIScore` as computed value.
- Real customer data (`AGENTS.md`) — fixtures and synthetic records only.
- Any modification to Chitu scoring, research, or email-generation logic.
- Any change to the C19-frozen lifecycle services, guards, or action keys.

### Success criteria

1. Credentials never leave the server in plaintext and never appear in a log or exception.
2. Provider substitution requires zero code edits outside a new adapter file.
3. Every invocation yields an `AIRequestLog` row with attributable cost.
4. Dry-run mode completes a full trace with zero network egress.
5. Full suite green under the canonical invocation (WP4 prerequisite).
6. `AIJob.FAILED` is operator-recoverable and surfaced in a dashboard queue.
7. Contract tests enforce all twenty-two §8 invariants.
8. WP0 closes every item of recorded C19 technical debt.

---

## 11. Open Questions Requiring Ratification

### 11.1 — Blocking: does a new `CompletionProvider` adapter violate `AGENTS.md`?

`AGENTS.md` forbids modifying "AI research logic" and "the email-generation engine."
§D4 takes the position that adding a *new, separately-owned* adapter for a capability
Chitu does not own is not a modification of Chitu's logic. **That reading is not
self-evident and must be ratified by a human owner before WP2 begins.** If ratification is
withheld, C20 proceeds as Option B: enrichment and completion arrive from Chitu only, and
WP2 narrows to the `EnrichmentProvider` port with no completion adapter.

An AI agent must not resolve this in its own favour. It is a repo-level governance
constraint, and this ADR records the question rather than assuming the answer.

### 11.2 — Non-blocking

| # | Question | Default if unresolved |
| --- | --- | --- |
| a | Does EspoCRM hold any secret, or only credential references (§5.2)? | References only — the stricter posture |
| b | Is `AIJob` dispatch synchronous-with-timeout or queue-backed? | Queue-backed via Espo scheduled jobs |
| c | Does `ProviderHealth` drive automatic failover in C20 or advisory only? | Advisory only |
| d | Are prompt templates per-tenant or global? | Global; revisit if multi-tenant emerges |
| e | Cost ceiling scope: per capability, per user, or global? | Per capability plus global hard cap |

---

## 12. Evidence

| Claim | Source |
| --- | --- |
| C19 lifecycle guards and ownership | `files/custom/Espo/Custom/Hooks/{ReplyEvent,Quote,SendExecution,Approval}/*MutationGuard.php`; `Services/StatusMutationSaveOption.php` |
| Action-key authorization pattern | `Services/WorkflowAuthorizationService.php`; `Resources/metadata/app/prospectingWorkflow.json` |
| Repo-level prohibitions | `AGENTS.md`, `CLAUDE.md` (identical) |
| DeepSeek runtime out of scope; scoring forbidden | `docs/architecture/BOUNDARIES.md` §2 |
| Chitu-owned capabilities | `chitu-connector/chitu_connector/vendored/contracts/{canonical_score,scoring,icp,business_qualification,website_research,single_candidate_loop}.py` |
| Existing provider abstraction | `chitu-connector/chitu_connector/acquisition/providers/{base,apify_provider,serper_provider,config}.py` |
| Transport injection with no default | `providers/apify_provider.py` module docstring and `__init__` signature |
| Secret hygiene precedent | `providers/config.py` — `field(repr=False)` on `api_token` / `api_key` |
| Error normalization precedent | `Services/{BridgeErrorClass,BridgeNormalizedStatus,BridgeRejectionException,SendExecutionBridgeResult}.php` |
| `RATE_LIMIT` already on SendExecution / providers | `entityDefs/SendExecution.json` `failureCategory`; `espocrm_sync/provider_contract.py` |
| Operator recovery precedent | `Services/SendExecutionWorkflowActionService.php`; `docs/adr/ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md` |
| Baseline release | `phase3c19-freeze` @ `4a7a111`; `deployment/prospecting-extension-1.9.12-alpha.zip` |
| Stale BOUNDARIES entries | §3 lists Apify "Not Implemented" and cites `acquisition/provider.py`; `providers/apify_provider.py` exists |

---

## 13. Decision Log

| Date | Decision | Reference |
| --- | --- | --- |
| 2026-07-27 | ADR-C20 **Proposed**; marker `adr-c20-aiplatform-v1` | Header |
| 2026-07-27 | D1 — dedicated `Modules/AIPlatform`, one-way dependency from Prospecting | §2 D1 |
| 2026-07-27 | D2 — EspoCRM governs AI capability; it does not compute it | §2 D2 |
| 2026-07-27 | D3 — connector is the sole outbound egress point | §2 D3 |
| 2026-07-27 | D4 — custody split (Option C) recommended; direct-LLM question escalated | §2 D4, §11.1 |
| 2026-07-27 | `AIScore` as a computed value **rejected**; Chitu `canonical_score` is authoritative. Do not create `AIScore`. | §1.3, §6.3 |
| 2026-07-27 | `AIQualificationInsight` introduced as advisory dynamic qualification layer. Canonical scoring remains Chitu-owned. AI provides contextual intelligence only. | §1.3, §6.3–6.4, §8.16–8.22 |
| 2026-07-28 | WP0 execution recorded (§14); closing statement corrected — WP0 was not documentation-only. Frozen-surface position: additive taxonomy expansion is not a lifecycle change; see charter §7 | §14 |
| 2026-07-28 | Entire `AIQualificationInsight` entity immutable after create; supersession ordering replaces mutable `isCurrent`; Chitu owns qualification decisions; EspoCRM must not derive verdicts; PrimaryFilter / queue authority forbidden | §6.4, §8.16–8.22 |
| 2026-07-27 | `Prospect` entity rejected; `ProspectPool` / `Lead` remain the only identities | §6.3 |
| 2026-07-27 | `Modules/Automation`, `EmailCampaign`, `EmailAccount` deferred beyond C20 | §6.3, §10 |
| 2026-07-27 | `RATE_LIMIT` is existing elsewhere; add for `BridgeErrorClass` parity. New: `QUOTA`, `CONTENT_FILTER` | §4.3 |
| 2026-07-28 | WP0.4 executed BridgeError parity (`RATE_LIMIT` / `QUOTA` / `CONTENT_FILTER`) as additive taxonomy expansion only; transition service, mutation guard, and action keys unchanged — see §14 and charter §7 | §14, charter §7 |
| 2026-07-27 | `AIJob.FAILED` non-terminal and operator-recoverable, mirroring C19 WP2 | §7.2 |
| 2026-07-27 | C20 ships no email-sending path | §8.15, §10 |
| 2026-07-27 | WP5 consumes Chitu/connector research outputs only; no duplicate research engine | §10 |

---

## 14. WP0 Execution Record

Added 2026-07-28. This section records what Phase3C20 WP0 **executed**, because the
ADR's original closing statement described WP0 as documentation-only and that was
contradicted by the WP0 commit.

**Commit:** `962a7ae` — *phase3c20: complete WP0 AI platform governance foundation*
(2026-07-28). Authorized by `docs/PHASE3C20_CHARTER.md` §3 and §7.

### 14.1 What WP0 changed

| Category | Files | Nature |
| --- | --- | --- |
| Test infrastructure | `pytest.ini` (new); root test import/stale-assertion repairs | Canonical invocation; C14 assertion repair |
| Governance | `docs/adr/C20_INVARIANT_REGISTRY.md` (new) | 22-invariant registry with meta-tests |
| Contract tests | 3 new `test_phase3c20_wp0_*.py` | Registry, boundary guards, bridge parity |
| **Runtime PHP** | `BridgeErrorClass.php`, `SendExecutionBridgeAdapterService.php`, `SendExecutionResultAdapterService.php` | Additive error-taxonomy expansion |
| **Metadata** | `entityDefs/SendExecution.json` | `failureCategory` widened: `QUOTA`, `CONTENT_FILTER` |
| **i18n** | `SendExecution.json` (en_US, zh_CN) | Labels for the two new categories |
| **Connector** | `espocrm_sync/failure_classification.py`, `send_execution_bridge.py` | Matching taxonomy expansion |
| **Artifact** | `prospecting-extension-1.9.12-alpha.zip` + sidecar | Rebuilt |

WP0 therefore made runtime, metadata, test, and artifact changes. The original closing
statement was inaccurate and has been corrected.

### 14.2 Frozen-surface position

The Prospecting changes are additive value-object and enum widening, not lifecycle
changes. Verified at `962a7ae`: `SendExecutionTransitionService`,
`SendExecutionStatusMutationGuard`, and `prospectingWorkflow.json` action keys have
**zero** changes. Full rationale and bounds: `docs/PHASE3C20_CHARTER.md` §7.

Retry ownership is unchanged — `isAutoRetryEligible()` / `is_auto_retry_eligible()`
classify only and are contract-tested to reference no transition service and introduce
no `nextRetryAt`.

### 14.3 Known consequence — release line

WP0 changed shipped payload without a version bump, so `1.9.12-alpha` now maps to two
distinct artifacts: `E11715D2…` at `phase3c19-freeze` and `1F981503…` at `962a7ae`. A
bump to `1.9.13-alpha` is required before WP0 exit. Tracked as charter §8 O1.
**Version bump is still pending** — this documentation package does not rebuild the ZIP
or change `manifest.json`.

### 14.4 Registry alignment

`C20-INV-03` and `C20-INV-18` were reclassified `DEFERRED → ACTIVE`; both were already
enforced by WP0.3 boundary guards. Counts 7/15 → 9/13. `C20-INV-17` remains `DEFERRED`.

---

*Status: Proposed. This ADR is a design document and authorizes no implementation by
itself; each work package is authorized by `docs/PHASE3C20_CHARTER.md`. WP0 as executed
was **not** documentation-only — see §14 for the execution record. §11.1 requires human
ratification before WP2 implementation may begin.*
