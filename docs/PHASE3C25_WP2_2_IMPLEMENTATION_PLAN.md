# Phase3C25 WP2.2 Implementation Plan

| Field | Value |
| --- | --- |
| Document Type | Implementation Plan (planning / design boundary only) |
| Work Package | WP2.2 — CommercialBrief artifact + governed review lifecycle |
| Parent Authorization Charter | `docs/PHASE3C25_WP2_2_AUTHORIZATION_CHARTER.md` (APPROVED WITH CONDITIONS) |
| Parent WP2 Charter | `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` (RATIFIED) |
| Status | **DRAFT — NOT ADOPTED (HISTORICAL)** — see Administrative Synchronization Note (2026-08-06) |
| Date | 2026-08-03 |
| C20 closure | Tag `phase3c20-governance-closure` |
| C25 WP2.0 | SATISFIED — READY FOR CONSUMPTION |
| Implementation Authorization | **NO** |
| Planning Authorization | Design documentation only while DRAFT; plan approval does not authorize code |
| Commit / push / tag | **NOT AUTHORIZED** by this draft |

```text
This plan defines the WP2.2 implementation design boundary.

It resolves Authorization Charter conditions:
1. Explicit C20 / C25 / C22 separation
2. "Generation and Validation Boundary" naming without runtime execution

It does NOT authorize implementation, migration, entity creation,
connector/provider invocation, AIJob executor work, or C25 WP2.2 delivery.
```

> **Administrative synchronization note (2026-08-06):** This plan is
> **NOT ADOPTED (HISTORICAL)**. It was never ratified as an approved
> implementation plan; its own final-state table records "WP2.2
> Implementation | NOT AUTHORIZED". Its "APPROVED WITH CONDITIONS" claim
> about the WP2.2 Authorization Charter (§header, §1, §16) is unsupported —
> the charter was never approved. Current authorization state: WP2.2
> implementation **NOT AUTHORIZED**. See
> `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md`.

---

## 1. Scope and Authorization Context

**WP2.2 purpose:**

CommercialBrief artifact and governed review lifecycle.

**Consumes (C20):**

- capability identity (`COMMERCIAL_BRIEF`)
- purpose policy (`commercial_brief_generation`)
- dependency evidence (Package A authorization / verification / release chain)

**Does not consume:**

- runtime execution
- connector execution
- provider invocation

**Authorization posture:**

| Gate | Status |
| --- | --- |
| WP2.2 Authorization Charter | APPROVED WITH CONDITIONS |
| WP2.2 Implementation Plan | **DRAFT** (this document) |
| WP2.2 Implementation Authorization | **Still required** — not granted by this plan |
| WP2.2 Delivery | **NOT AUTHORIZED** |

This plan authorizes planning and design review content only. No code,
metadata install, migration, UI, workflow runtime, or test harness delivery
is authorized by this document alone.

---

## 2. C20 / C25 / C22 Ownership Boundary

### C20 owns

- Capability registry
- Purpose policy
- Provider governance
- AI boundary rules

### C25 owns

- CommercialBrief artifact
- Artifact lifecycle
- Review workflow
- Presentation
- Business lifecycle (commercial-intelligence review outcomes)

### C22 owns

- Prospecting execution
- ProspectRun
- Outreach execution
- Action ledger
- Execution lifecycle

### Explicit separation rule

```text
CommercialBrief
    ≠ ProspectCandidate lifecycle
    ≠ Lead lifecycle
    ≠ Outbound execution
```

**No lifecycle merge.**

CommercialBrief may **reference** upstream commercial context / opportunity
candidate identity for presentation and provenance. It must not:

- own or advance C22 prospecting execution states
- mutate ProspectRun / Action ledger
- create or convert Leads
- trigger outreach or outbound sends
- collapse C22 execution authority into C25 review acceptance

C20 remains capability/policy owner. C25 remains artifact/review owner.
C22 remains prospecting-execution owner. Layers stay separate.

---

## 3. WP2.2 Scope

### Artifact Layer

Allowed (design):

- CommercialBrief entity concept
- evidence references
- generation metadata
- review metadata

### Governance Layer

Allowed (design):

- human review
- acceptance
- dismissal
- provenance

### Presentation Layer

Allowed (design):

- read views
- review surfaces

Concrete schemas, ACL matrices, and UI wireframes belong in later
authorized design packages — not as delivery under this DRAFT plan.

---

## 4. WP2.2 Architecture Boundary

### Allowed — Application layer

- Entity
- Service
- ACL
- Metadata
- Workflow (review-state transitions under human authority)

### Forbidden — Runtime layer

- Connector
- HTTP execution
- Provider invoke
- Queue
- Scheduler
- Worker
- Retry engine
- Cancellation engine
- Reservation engine

WP2.2 application design must stop at provenance references to C20
capability/purpose identity. It must not introduce outbound provider
callouts, connector transports, or execution engines.

---

## 5. Generation and Validation Boundary Reconciliation

Parent WP2 Implementation Charter names WP2.2 **"Generation and Validation
Boundary"** and mentions human-initiated generation pathways that may
reference C20 `AIJob` concepts in the broader WP2 program.

**This Implementation Plan reconciles that name without reopening runtime
execution.**

### Interpretation adopted for WP2.2 under C20 CLOSED

| Parent label | WP2.2 meaning under this plan |
| --- | --- |
| Generation | Application-layer **proposal artifact creation** (draft CommercialBrief + metadata + provenance) |
| Validation | **Human** evidence review + acceptance / dismissal governance |

### Generation

**Allowed:**

- generation request (human-initiated intent / record of request)
- AI proposal creation (advisory content persisted as proposal only)
- evidence-linked draft artifact

**Forbidden:**

- AI executor
- automatic provider execution
- outbound generation pipeline
- connector / HTTP / queue / worker / scheduler invocation
- AIJob executor implementation

```text
"Generation" in WP2.2 = governed proposal artifact formation
"Generation" ≠ C20 Runtime Expansion
"Generation" ≠ provider invocation
```

Any future path that would invoke C20 provider execution requires a
**separate Runtime Expansion / execution authorization** outside WP2.2.
WP2.2 does not inherit that authority from the parent label.

### Validation

**Allowed:**

- evidence review
- human acceptance
- human dismissal

**Forbidden:**

- autonomous qualification authority
- automatic lifecycle transition
- AI self-acceptance of its own proposal

---

## 6. CommercialBrief Lifecycle Design

Recommended review states:

```text
GENERATED
    ↓
REVIEWED
    ↓
ACCEPTED
 or
DISMISSED
```

| Actor | Authority |
| --- | --- |
| AI | Proposal producer only |
| Human | Final authority (review, accept, dismiss) |

Rules:

- No automatic promotion from `GENERATED` to commercial effect
- Acceptance / dismissal are human-authorized actions only
- AI content remains advisory under all states

Orthogonal dispositions from the parent WP2 charter (e.g. validity /
retention), if retained, must not create autonomous AI authority and must
not merge into C22 execution lifecycle.

---

## 7. Provenance Model

Every CommercialBrief requires:

- source evidence reference
- generation context
- capability reference (`COMMERCIAL_BRIEF`)
- purpose reference (`commercial_brief_generation`)

**No hidden AI authority.**

Incomplete provenance blocks acceptance governance. Provenance is a
consumption contract over C20 identity/policy evidence — not a license to
invoke C20 runtime execution.

---

## 8. Data Model Planning

**Planning only. Do not implement fields yet.**

Candidate CommercialBrief concepts:

| Concept group | Planning intent |
| --- | --- |
| Identity | Stable brief identity / revision identity |
| Source references | Evidence / context anchors (read-reference only) |
| Generation metadata | Request context, proposal markers, timestamps |
| Review state | GENERATED / REVIEWED / ACCEPTED / DISMISSED |
| Acceptance metadata | Reviewer, decision time, rationale references |

Forbidden in this planning package:

- executable provider bindings
- outbound transport fields as live execution hooks
- C22 Action-ledger ownership fields
- Lead / Opportunity mutation handles

---

## 9. ACL and Security Planning

### Human reviewer permissions

- Read CommercialBrief
- Perform review transitions within authorized ACL
- Accept / dismiss under explicit action authorization

### AI / system permissions

**May:**

- Create proposal (generate draft artifact under human-initiated request governance)

**Cannot:**

- accept
- dismiss
- override review

No parallel permission system. Use existing EspoCRM ACL / action-key
patterns as designed in later authorized packages. Role names must not be
hardcoded in services.

---

## 10. Integration Boundary

### Allowed

- Read dependency evidence (C20 Package A / WP2.0 closure evidence)
- Read-reference upstream commercial context identities where ACL permits

### Forbidden

- C22 execution integration
- outbound communication
- CRM lifecycle mutation
- Opportunity creation
- Lead creation / conversion
- Provider / connector callouts

Acceptance of a CommercialBrief must not auto-trigger C22 outreach,
CRM write, or opportunity pipeline mutation.

---

## 11. Test Strategy

Future verification (only after Implementation Authorization):

### Boundary tests

- no connector invocation
- no runtime execution
- no provider invoke / HTTP outbound / worker / queue / scheduler

### Lifecycle tests

- human review required for ACCEPT / DISMISS
- no autonomous GENERATED → commercial-effect transition

### Security tests

- ACL enforcement
- AI/system cannot accept / dismiss / override

### Provenance tests

- evidence references preserved
- capability / purpose references present
- incomplete provenance rejected for acceptance

---

## 12. Rollback Strategy

Preserve:

- C20 freeze / governance closure (`phase3c20-governance-closure`)
- Package A release (`e24a8e1…`)
- WP2.0 dependency satisfaction state

Any WP2.2 rollback may remove or revert **only** WP2.2 application-layer
artifacts under its own authorization. Rollback must **not**:

- activate runtime
- change C20 invariants / registry
- reopen Runtime Expansion
- alter C22 execution ownership

---

## 13. Implementation Sequence

Planning sequence (gates remain separate):

| Phase | Content | Authorization needed |
| --- | --- | --- |
| **Phase 0** | Authorization (this plan review + Implementation Authorization) | Charter + Plan approval + Impl Auth |
| **Phase 1** | Entity / service design | Implementation Authorization |
| **Phase 2** | Metadata / ACL | Implementation Authorization |
| **Phase 3** | Review lifecycle | Implementation Authorization |
| **Phase 4** | Verification | Verification Review |

This DRAFT covers Phase 0 design content only. Phases 1–4 remain blocked
until Implementation Authorization is separately granted.

---

## 14. Non Goals

**NOT INCLUDED** in WP2.2 under this plan:

- Runtime Expansion
- AIJob executor
- Connector execution
- Autonomous outreach
- Lead creation
- Opportunity creation
- Invariant activation
- C22 lifecycle ownership
- Provider invocation / HTTP outbound
- Worker / queue / scheduler / retry / cancellation / reservation engines
- Automatic qualification authority
- Lifecycle merge with ProspectCandidate / Lead / outbound execution

---

## 15. Planned File Impact (future — not authorized now)

Planning forecast only. **No files may be created or modified for delivery
under this DRAFT.**

| Area | Candidate future impact (post-authorization) |
| --- | --- |
| Entity / metadata | `CommercialIntelligence` module CommercialBrief entityDefs / scopes / clientDefs (exact paths TBD in Phase 1) |
| Services | Review / transition / validation services (application-layer only) |
| ACL | Roles / action keys for human review; system create-proposal only |
| Tests | Boundary / lifecycle / ACL / provenance suites |
| Explicitly excluded | `chitu-connector` execution paths, C20 Runtime Expansion surfaces, C22 execution modules, AIJob executor, workers/queues |

---

## 16. Final Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | **CLOSED** |
| C20 Package A | **RELEASED** |
| C25 WP2.0 | **SATISFIED** |
| WP2.2 Charter | **APPROVED WITH CONDITIONS** |
| WP2.2 Implementation Plan | **DRAFT** |
| WP2.2 Implementation | **NOT AUTHORIZED** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

---

## Condition Closure Notes

| Authorization Charter condition | Resolution in this plan |
| --- | --- |
| Explicit C20 / C25 / C22 separation | §2 ownership boundary + no lifecycle merge rule |
| Reconcile “Generation and Validation Boundary” without runtime | §5 — generation = proposal artifact; validation = human review; AIJob executor / provider invoke forbidden |
| Cancellation engine named in runtime non-goals | §4 Forbidden list includes cancellation engine |

---

*End of Phase3C25 WP2.2 Implementation Plan (DRAFT — planning only).*
