# ADR-C21: AI Sales Intelligence Architecture

## Status

**Proposed** — pending independent architecture review. This ADR does not
authorize C21 entities, metadata, migrations, runtime, provider integration,
or workflow implementation.

## Date

2026-07-29

## Phase

Phase3C21 — AI Sales Intelligence Layer

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting / AI Platform modules
- Phase3C21 Architecture Review Board

## Related

- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` — C20 execution governance
- `docs/PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md` — frozen C20 provenance boundary
- `docs/adr/C20_INVARIANT_REGISTRY.md` — standing C20 authority/lifecycle boundaries
- `AGENTS.md` / `CLAUDE.md` — repository-level prohibitions

---

## 1. Context

C20 provides the AI capability platform: controlled provider resolution,
`AIJob` execution records, append-only `AIRequestLog` evidence, and governed
`PromptTemplate` versions. It deliberately does not make EspoCRM the owner of
sales intelligence, scoring, qualification, or autonomous selling.

Sales intelligence needs a separate governed interpretation layer. It must
preserve research evidence, distinguish model inference from source-backed
fact, present an advisory insight to a human, and record human feedback.
Execution evidence alone is not a business decision record.

Chitu remains the external intelligence authority. Chitu owns
`canonical_score`, qualification decisions, and research/scoring logic.
EspoCRM owns governance, evidence storage, workflow context, and human review;
it does not become a competing intelligence authority.

---

## 2. Decision Summary

```text
C20 = AI capability execution platform
C21 = AI intelligence interpretation layer
C22 = autonomous execution layer
```

C21 stores intelligence projections and advisory records. It does not execute
AI, select a provider, calculate a score, issue a qualification decision, or
mutate CRM business lifecycle state automatically.

---

## 3. Ownership Model

| Owner | Owns | Does not own |
| --- | --- | --- |
| Chitu | External intelligence authority; `canonical_score`; qualification decisions; research/scoring logic | CRM lifecycle and execution governance records |
| C20 | `ProviderBinding`; Capability Registry; `AIJob`; `AIRequestLog`; `PromptTemplate` | Sales-intelligence interpretation and CRM business decisions |
| C21 | Intelligence projection; research evidence; advisory insight; human feedback | Provider runtime, score authority, qualification decisions, CRM lifecycle |
| CRM Core | Lead, Account, Opportunity, lifecycle transitions, revenue decisions | AI runtime and intelligence scoring authority |

The authority path is one-way:

```text
Chitu intelligence + C20 execution provenance
                    ↓
              C21 advisory intelligence
                    ↓
        Human / authorized workflow decision
                    ↓
          CRM Core lifecycle action, if approved
```

No arrow in this ADR permits C21 intelligence to mutate CRM lifecycle directly.

---

## 4. Candidate Identity Decision

### 4.1 Decision

**Option A is selected:** `ProspectPool` remains the sole pre-CRM candidate
identity. C21 does **not** create a `ProspectCandidate` entity.

`ProspectPool` is the existing candidate identity layer. C21 may later add
research evidence, advisory intelligence, and human feedback *about* a
`ProspectPool` record, but those records do not replace or own candidate
identity.

### 4.2 Options considered

| Option | Description | Decision |
| --- | --- | --- |
| A | Keep `ProspectPool` as the only pre-CRM candidate identity; C21 adds intelligence records around it | **Accepted** |
| B | Add `ProspectCandidate` as a second candidate identity | Rejected |

Option B would require separate deduplication, lifecycle, conversion, and
identity-resolution rules. It would overlap with the existing `ProspectPool`
and later Lead adoption path, recreating the duplicate-identity defect already
rejected by C20 architecture.

### 4.3 Consequences

- C21.1 must not create `ProspectCandidate`.
- A future identity-model change requires a separate ADR; it is not authorized
  by this ADR.
- Lead, Account, or Opportunity adoption remains an explicit human or
  separately authorized CRM workflow decision.

---

## 5. ResearchEvidence Model

`ResearchEvidence` represents material collected during the intelligence
process. Every record must declare one evidence type:

| Type | Meaning | Example |
| --- | --- | --- |
| `FACT` | Source-backed assertion with attributable source | “Company founded in 2015” |
| `OBSERVATION` | Recorded observation, not independently verified fact | “Company recently expanded dental products” |
| `AI_INFERENCE` | Model-derived interpretation or hypothesis | “Potential interest in dental resin printers” |

The mandatory semantic rule is:

```text
AI_INFERENCE != FACT
```

An inference cannot be promoted to `FACT` by a model, workflow, display label,
or convenience field. A human may add separate source-backed evidence but may
not overwrite the classification or history of the prior inference.

Research evidence is not a score, qualification verdict, lifecycle instruction,
or replacement for Chitu research logic. Its future schema must preserve type,
source/attribution where applicable, capture context, and C20 provenance where
it was AI-produced.

---

## 6. AIQualificationInsight Model

`AIQualificationInsight` is an advisory **recommendation**, not a decision.
It may contain market/intent/context signals, non-authoritative confidence
explanation, reasoning, and references to `ResearchEvidence` and C20 evidence.

Confidence communicates uncertainty. It is not a score and must not map to a
qualification class, lifecycle state, PrimaryFilter, queue priority, or
automatic action threshold.

The following are forbidden as fields, computed equivalents, or semantics:

```text
AIScore
canonical_score
qualification_score
score = 85
HOT
COLD
```

For an AI-generated insight, `sourceAIRequestLogId` is required provenance.
`sourceAIJobId` may be recorded only as a consistent execution-group reference;
it does not confer execution ownership on C21. The request log is the
authoritative per-invocation evidence link.

`AIQualificationInsight` must be immutable after creation. Corrections or new
thinking create a new superseding insight; no mutable `isCurrent` flag is
permitted. “Current” is derived from supersession ordering, never an editable
boolean. The insight has no lifecycle state machine or transition service.

---

## 7. HumanFeedback Model

`HumanFeedback` records confirmation, correction, disagreement, and learning
signals about intelligence records:

```text
AI insight
    ↓
Human feedback
    ↓
Future intelligence improvement
```

Human feedback is append-only. A later correction is a new feedback record; it
does not overwrite the original insight or prior feedback history.

HumanFeedback does not directly modify Lead lifecycle, Opportunity stage,
customer lifecycle, revenue forecast, or a Chitu score/qualification decision.
It may be input to future intelligence improvement only under separately
approved Chitu and governance contracts.

---

## 8. C20 Provenance Integration

C21 may reference these C20 records for provenance only:

```text
sourceAIJobId
sourceAIRequestLogId
```

```text
C21 intelligence record → C20 execution evidence
```

This does not authorize C21 to create, modify, duplicate, or schedule:

- `AIJob`;
- `AIRequestLog`;
- `PromptTemplate`; or
- Capability Registry resolution.

C21 must retain prompt/provider/model/attempt context by reference to C20
evidence, not by copying raw prompts, raw responses, credentials, or provider
payloads into C21 records.

---

## 9. Provider Boundary

C21 does not own or implement provider credentials, routing, adapters, or AI
execution runtime. Provider capability resolution remains under C20
`ProviderBinding` plus Capability Registry authority. C21 consumes execution
evidence; it does not introduce `ProviderRoute`, a second routing policy, or a
credential store.

---

## 10. Lifecycle Boundary

C21 does not own Lead, Opportunity, Account, customer, or any CRM business
lifecycle. Its valid output is:

```text
Intelligence → human or authorized workflow decision
```

Its forbidden output is:

```text
Intelligence → automatic CRM mutation
```

C21 insight, confidence, evidence type, or human feedback cannot be used as a
PrimaryFilter authority, lifecycle queue authority, or direct transition input.

---

## 11. C21 Entity Ownership Matrix

| Entity | Owner | Purpose |
| --- | --- | --- |
| `ProspectPool` | Existing candidate layer | Sole pre-CRM candidate identity |
| `ResearchEvidence` | C21 | Typed intelligence evidence |
| `AIQualificationInsight` | C21 | Immutable advisory recommendation |
| `HumanFeedback` | C21 | Append-only feedback record |
| `AIJob` | C20 | Execution lifecycle |
| `AIRequestLog` | C20 | Append-only execution evidence |
| `PromptTemplate` | C20 | Prompt governance |
| Lead | CRM Core | Business lifecycle |
| Opportunity | CRM Core | Revenue lifecycle |

---

## 12. C21 Invariants

The eventual C21 Charter and invariant registry must activate contract tests
for at least these invariants:

| ID | Invariant |
| --- | --- |
| C21-INV-01 | C21 does not own final sales or qualification decisions. |
| C21-INV-02 | `AI_INFERENCE` is never stored, displayed, or promoted as `FACT`. |
| C21-INV-03 | `AIQualificationInsight` is recommendation, not decision; it has no score or qualification authority. |
| C21-INV-04 | C21 cannot write CRM lifecycle or revenue-decision fields. |
| C21-INV-05 | AI-produced intelligence has required C20 execution provenance. |
| C21-INV-06 | C21 does not create provider credentials, routing, adapters, or execution runtime. |
| C21-INV-07 | C21 creates no scoring authority and does not mutate `canonical_score`. |
| C21-INV-08 | `HumanFeedback` is append-only and cannot overwrite historical insight. |

---

## 13. Consequences

### Benefits

- Intelligence can evolve without moving score or qualification authority into
  EspoCRM.
- Facts, observations, and AI inferences remain semantically distinguishable.
- C20 execution evidence gives C21 records reproducible provenance.
- Human review remains the boundary between intelligence and CRM business
  action.
- C22 can later add autonomous execution only under a separate architecture
  decision and explicit controls.

### Costs

- Execution, intelligence, and business remain distinct layers.
- Provenance references and evidence classification add schema and test work.
- Candidate identity remains intentionally centralized in `ProspectPool`.
- Operators and authorized workflows make the final CRM business decision.

### Deferred

- C21 entities, metadata, migrations, layouts, services, and workflows;
- provider adapters, live AI execution, and credential management;
- scoring or qualification authority;
- automated lifecycle actions, outreach, email delivery, and agent runtime; and
- C22 autonomous execution design.

---

## 14. Implementation Gate

This ADR is **Proposed** and authorizes no implementation by itself.

```text
Independent ADR review
    ↓
ADR accepted
    ↓
C21 Charter approved
    ↓
Identity decision confirmed: ProspectPool remains sole candidate identity
    ↓
Bounded C21 implementation
```

Only after acceptance and Charter approval may C21 implementation begin. The
first permitted increment is a bounded C21.1 design/contract step for existing
`ProspectPool` integration and intelligence-record boundaries; it must not
create `ProspectCandidate` or any prohibited runtime.
