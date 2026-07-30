# Phase3C24 Charter — Revenue Operations Governance Layer

## Document Header

| Field | Value |
| --- | --- |
| Document Type | Phase Charter |
| Subject | C24 — Revenue Operations Governance Layer |
| Status | DRAFT v1.1 — condition resolution applied; ready for ratification review |
| Date | 2026-07-30 |
| Version | v1.1-draft |
| Baseline | `9814c57` |
| Predecessor | Phase3C23 Final Freeze |
| Amendment | `docs/audit/PHASE3C24_CHARTER_AMENDMENT_V1.md` |
| Review addressed | `docs/audit/PHASE3C24_CHARTER_REVIEW.md` — B-01 and B-02 resolved |

---

## 1. Purpose and Layer Identity

Phase3C24 defines the **Revenue Operations Governance Layer**. C24 interprets commercial outcome evidence and presents governed pipeline and revenue analysis for human decision makers.

C24 is a governance and analytical layer. It is not an execution engine, an approval engine, a provider runtime, an autonomous sales agent, a policy optimizer, or a CRM lifecycle owner.

```text
C20  AI platform and credential custody
C21  Intelligence and qualification governance
C22  Prospecting execution governance through ReplyDetection
C23  Prospecting effectiveness and optimization learning
C24  Revenue outcome governance and human commercial decision support
CRM  Canonical Lead, Opportunity, Account, stage, and revenue lifecycle
```

### 1.1 C24 owns

- ReplySignal business interpretation;
- OpportunityCandidate governance before any human commercial action;
- pipeline health observation;
- PipelineMetric measurement governance;
- RevenueInsight aggregate commercial analysis and reporting; and
- human-facing revenue decision support.

### 1.2 C24 does not own

- provider, credential, model-routing, or outbound API execution (C20);
- research evidence, qualification, prospect ranking, or feedback ownership (C21);
- ActionGate decisions, execution, ProspectRun, ExecutionLedger, or ReplyDetection (C22);
- prospect discovery or prospecting optimization metrics (C23); or
- canonical Lead, Opportunity, Account, sales stage, forecast commitment, or revenue lifecycle mutation (CRM Core).

---

## 2. C23/C24 Analytics Separation

### 2.1 Explicit ownership boundary

| Layer | Owns | Primary question |
| --- | --- | --- |
| C23 | Prospecting effectiveness: prospect discovery, prospect-qualification feedback, execution-outcome optimization, and ReplyDetection effectiveness | “Did prospecting work?” |
| C24 | Revenue outcome governance: ReplySignal, OpportunityCandidate, pipeline health, and revenue metrics | “Did prospecting create commercial value?” |

C23 ends with aggregate evidence about prospecting effectiveness, including the effectiveness of reaching and receiving replies. C24 begins with the business interpretation of a reply as a ReplySignal and follows commercial value through governed opportunity consideration, pipeline health, and revenue reporting.

### 2.2 Metric separation

| Dimension | C23 PerformanceMetric | C24 PipelineMetric |
| --- | --- | --- |
| Domain | Acquisition and prospecting effectiveness | Commercial pipeline and revenue outcome health |
| Typical evidence | discovery, qualification feedback, run/execution outcomes, ReplyDetection effectiveness | ReplySignal, human-governed OpportunityCandidate state, CRM pipeline and revenue reporting data |
| Example question | Which prospecting approach receives stronger replies? | Do accepted commercial candidates progress into durable commercial value? |
| Authority | Advisory optimization measurement | Advisory revenue measurement |

C24 may consume C23 artifacts only as read-only context. C24 MUST NOT redefine, overwrite, or create a competing version of C23 acquisition-effectiveness metrics. A C24 PipelineMetric is not a replacement for a C23 PerformanceMetric.

### 2.3 RevenueInsight versus OptimizationInsight

`OptimizationInsight` remains a C23 aggregate recommendation about prospecting strategy or process effectiveness. `RevenueInsight` is a C24 aggregate commercial analysis about pipeline health, conversion, velocity, coverage, or revenue reporting. Neither entity type may be used as an execution command, ActionGate input, CRM mutation instruction, or forecast commitment.

---

## 3. Cross-Layer Boundaries

### 3.1 C20 boundary

C24 has no provider, credential, vendor, SDK, HTTP, or AI runtime ownership. If a future C24 analytical function requires a model invocation, it MUST route through C20 capability interfaces. C24 MUST NOT hold credentials or invoke an AI provider directly.

### 3.2 C21 boundary

C24 may consume ResearchEvidence, AIQualificationInsight, HumanFeedback, and IntelligenceAggregate only as read-only analytical context. C24 MUST NOT create, modify, delete, reinterpret as a replacement, or create a parallel authority for C21 intelligence or qualification.

### 3.3 C22 boundary

C24 may consume C22 outcomes only as read-only evidence. C24 MUST NOT bypass or influence ActionGate, start or alter a ProspectRun, mutate ExecutionLedger, trigger outreach, detect replies in place of C22 ReplyDetection, or grant execution permission.

### 3.4 CRM Core boundary

CRM Core owns canonical Lead, Opportunity, Account, sales stage, forecast commitment, and commercial lifecycle mutation. C24 may present analysis and human-review records but MUST NOT automatically create an Opportunity, move a sales stage, close an opportunity, or apply a forecast decision.

---

## 4. OpportunityCandidate Lifecycle (B-01)

`OpportunityCandidate` is a C24 governance record for human commercial consideration. It is not a Lead or Opportunity, and it is not an automatic promotion command.

### 4.1 State machine

```text
IDENTIFIED -> REVIEW_PENDING -> ACCEPTED -> ACTIVE -> WON
                                          -> LOST
                    -> REJECTED
```

`REJECTED`, `WON`, and `LOST` are terminal. Reconsideration requires a new OpportunityCandidate record with explicit provenance; no terminal record may be reopened.

### 4.2 State ownership and transition gates

| State | Owner and meaning | Entry gate |
| --- | --- | --- |
| IDENTIFIED | C24 records a candidate commercial signal from governed evidence | Creation records provenance; no opportunity is created |
| REVIEW_PENDING | C24 record awaits commercial review | Explicit assignment/review transition; no AI decision |
| ACCEPTED | A human accepts the candidate for commercial consideration | Authorized human transition with reason and evidence |
| ACTIVE | A human confirms active commercial follow-up | Authorized human transition; this does not move CRM sales stage |
| WON | A human records a reported commercial win outcome | Authorized human confirmation with CRM/reporting reference |
| LOST | A human records a reported commercial loss outcome | Authorized human confirmation with reason/reference |
| REJECTED | A human declines the candidate | Authorized human rejection with reason |

Allowed transitions are only `IDENTIFIED -> REVIEW_PENDING`, `REVIEW_PENDING -> ACCEPTED`, `REVIEW_PENDING -> REJECTED`, `ACCEPTED -> ACTIVE`, and `ACTIVE -> WON | LOST`.

Every transition after identification requires an authenticated authorized human. AI signals may inform identification or review material but cannot create an `ACCEPTED`, `ACTIVE`, `WON`, `LOST`, or `REJECTED` state. No transition creates a CRM Opportunity; any later Opportunity creation is a separate human action in CRM Core.

### 4.3 Transition audit requirements

Each permitted transition MUST create an immutable state-transition record with: predecessor state, successor state, timestamp, authenticated human actor, decision reason where applicable, and source/provenance references. Hidden timers, background progression, and automatic stage movement are prohibited.

---

## 5. ReplySignal Governance

`ReplySignal` is a C24 interpretation artifact and advisory input. It represents the business interpretation of reply evidence after C22 ReplyDetection; it does not replace C22 technical detection.

ReplySignal is NOT an opportunity-creation command, sales-stage mutation, ActionGate input, execution trigger, auto-response instruction, or workflow trigger. Any future classification must retain source provenance and remain human-reviewable. A changed interpretation requires a new superseding ReplySignal rather than mutation of the original conclusion.

---

## 6. RevenueInsight and PipelineMetric Governance

### 6.1 RevenueInsight boundary

`RevenueInsight` is aggregate commercial analysis, pipeline observation, and revenue reporting. Every RevenueInsight MUST declare provenance, freshness status, and a reporting period.

RevenueInsight MUST NOT decide a forecast, close an Opportunity, create or mutate a CRM lifecycle record, select a provider, or initiate commercial action. It is advisory evidence for a human revenue operator.

### 6.2 PipelineMetric boundary

`PipelineMetric` is a measurement artifact only. Every PipelineMetric MUST declare source references, computation methodology, reporting period, sample size, and freshness status. Methodology must be documented and reproducible.

No single AI score, PipelineMetric, RevenueInsight, or aggregate signal may control opportunity acceptance, forecast acceptance, sales stage, or any revenue decision. Metrics cannot be used as automated triggers for pipeline transitions, opportunity creation, or CRM mutation.

---

## 7. Human Governance

Humans exclusively own:

- opportunity acceptance and rejection;
- progression from accepted to active commercial follow-up;
- pipeline decisions and CRM stage changes;
- forecast approval or commitment; and
- commercial actions including proposal, negotiation, close, and loss handling.

C24 outputs have no automatic effect on C20, C21, C22, C23, or CRM Core. Any proposal to automate a C24 revenue decision requires a dedicated Charter amendment, ADR, invariant update, and independent governance review. Zero automation is the structural default.

---

## 8. C24 Invariants

| ID | Invariant |
| --- | --- |
| C24-INV-SEP-001 | Revenue analytics MUST NOT redefine C23 optimization metrics. C23 owns acquisition effectiveness; C24 owns commercial outcome governance. |
| C24-INV-SEP-002 | OpportunityCandidate acceptance requires a human governance transition. AI signals cannot directly create an accepted opportunity state. |
| C24-INV-LIFE-001 | Opportunity lifecycle transitions require explicit immutable state-transition records. |
| C24-INV-ADV-001 | ReplySignal, RevenueInsight, and PipelineMetric are advisory inputs or measurements; none may act as an execution, approval, or CRM mutation directive. |
| C24-INV-HG-001 | Opportunity acceptance, pipeline decisions, forecast approval, and commercial actions require explicit human action. |
| C24-INV-MET-001 | Every PipelineMetric declares provenance, methodology, reporting period, sample size, and freshness; it cannot become an automated decision trigger. |

---

## 9. Explicit Prohibitions

C24 MUST NOT implement or authorize:

- AI auto-acceptance of an OpportunityCandidate;
- automatic Opportunity creation, automatic stage movement, automatic close, or forecast commitment;
- ActionGate approval, provider execution, outreach, reply dispatch, or workflow triggering;
- a provider runtime, credential store, HTTP client, SDK integration, worker, scheduler, queue, or autonomous agent loop; or
- a C21 qualification replacement, a C23 optimization replacement, or a parallel CRM identity.

---

## 10. Ratification Scope

This charter authorizes governance specification only. It authorizes no entity, metadata, service, UI, test, worker, provider, lifecycle, or CRM implementation. Implementation requires ratification, C24 ADRs, and separately approved work packages.

**Ratification readiness:** The B-01 OpportunityCandidate lifecycle and B-02 C23/C24 analytics boundary conditions are resolved in this draft. The charter is ready for independent ratification review; it is not itself a ratification decision.
