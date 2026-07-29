# Phase3C21 Charter

## Status

**FROZEN — architecture and governance scope.**

This Charter implements the accepted boundaries of
`docs/adr/ADR-C21_AI_SALES_INTELLIGENCE_ARCHITECTURE.md`. It authorizes bounded
governance design and separately approved work packages; it does not authorize
provider execution, autonomous action, outreach, or CRM lifecycle automation.

## Baseline

- C20: **CLOSED WITH EXCEPTIONS** — AI Capability Governance.
- ADR-C21: **Accepted** — AI Sales Intelligence Architecture.
- `docs/adr/C21_INVARIANT_REGISTRY.md`: documentation-only C21 invariants.

---

## 1. Mission

```text
C21 = AI Sales Intelligence Layer
```

C21 governs candidate intelligence, research evidence, advisory insight, and
human feedback. It interprets intelligence and preserves provenance.

C21 does not own execution, provider routing, automation, scoring authority,
qualification decisions, or CRM lifecycle authority.

The phase boundary remains:

```text
C20 = AI Capability Governance
C21 = AI Intelligence Governance
C22 = Autonomous Execution Governance
```

---

## 2. Ownership Model

| Layer | Responsibility |
| --- | --- |
| C20 | AI execution governance, Capability Registry, AIJob, AIRequestLog, PromptTemplate |
| C21 | Intelligence interpretation, typed evidence, advisory insight, human feedback |
| CRM Core | Lead, Account, Opportunity, lifecycle and revenue decisions |
| Chitu | External intelligence authority, canonical score, qualification and research/scoring logic |

C21 may store and explain intelligence. It may not become the final sales,
score, qualification, or lifecycle decision authority.

---

## 3. Identity Model

`ProspectPool` is the sole pre-CRM candidate identity. C21 does not create a
`ProspectCandidate` entity or any equivalent duplicate identity.

```text
Discovery
    ↓
ProspectPool
    ↓
ResearchEvidence
    ↓
AIQualificationInsight
    ↓
HumanFeedback
    ↓
Human Adoption
    ↓
Lead
```

The WP3 governed intelligence segment is:

```text
ProspectPool
    ↓
ResearchEvidence
    ↓
AIQualificationInsight
    ↓
IntelligenceAggregate
    ↓
HumanFeedback
    ↓
Feedback Analytics
```

The final adoption step requires a human or separately authorized CRM
workflow. C21 evidence, confidence, or insight cannot perform the conversion.
Existing `ProspectPool` operational status fields remain owned by their frozen
pre-C21 workflows; C21 adds no status ownership or transition authority.

---

## 4. Evidence Governance

C21 hardens the existing `ResearchEvidence` entity; it does not recreate it.
Every governed evidence record must resolve to one classification:

```text
FACT
OBSERVATION
AI_INFERENCE
```

The mandatory semantic rule is:

```text
AI_INFERENCE != FACT
```

- `FACT` requires attributable source support.
- `OBSERVATION` records what was observed without asserting independent truth.
- `AI_INFERENCE` records model interpretation or hypothesis.

The core evidence facts are immutable after creation: classification, content,
source reference, capture time, and provenance. Correction creates a new
record and may reference the original through supersession; it never overwrites
history.

---

## 5. Confidence Boundary

```text
confidence != validationState
```

Confidence expresses AI certainty. Validation state expresses verification
status. A high confidence value cannot automatically create a fact, verify a
record, qualify a prospect, rank a lifecycle queue, or trigger CRM mutation.

The governed validation vocabulary is:

```text
UNVALIDATED
VERIFIED
REJECTED
SUPERSEDED
```

Validation changes require explicit authorized service operations. They do not
change evidence classification or immutable content.

---

## 6. Insight Governance

`AIQualificationInsight` is a **recommendation**, not a decision. It may expose
signals, confidence explanation, reasoning, and evidence references.

The following fields or semantic equivalents are forbidden:

```text
AIScore
canonical_score
qualification_score
HOT
COLD
```

An insight has no lifecycle state machine, cannot modify Chitu authority, and
cannot drive CRM transitions or PrimaryFilter/queue authority. When implemented
under a later work package, it must be immutable and corrected by supersession.

---

## 7. HumanFeedback Governance

HumanFeedback is append-only and may represent confirmation, correction,
disagreement, or comment/learning signal.

It cannot directly modify Lead, Opportunity, revenue forecasts, or lifecycle
state. It cannot overwrite an insight or earlier feedback. Any use for future
intelligence improvement requires a separately governed Chitu interface.

---

## 8. Intelligence Aggregation Governance

Aggregation allowed scope:

- aggregation of governed intelligence records;
- governance-preserving aggregation of ResearchEvidence and
  AIQualificationInsight; and
- read-only intelligence aggregation context.

Forbidden:

- score;
- rank;
- priority; and
- qualification.

### confidenceDistribution semantic guard

`confidenceDistribution` is a semantic guard for the distribution of confidence
across governed intelligence inputs. It is not a score, ranking, priority, or
qualification field.

### evidenceCoverage semantic boundary

`evidenceCoverage` is an evidence-coverage representation. It is not a score,
rank, priority, qualification, CRM filter predicate, queue authority, or
lifecycle decision.

---

## 9. Intelligence Governance Pipeline

```text
ResearchEvidence
    ↓
AIQualificationInsight
    ↓
IntelligenceAggregate
    ↓
HumanFeedback
    ↓
Feedback Analytics
```

Pipeline is governance relationship, not execution.

---

## 10. WP3 Entity Inventory

### IntelligenceAggregate

Fields:

- `signalCount`
- `evidenceCoverage`
- `confidenceDistribution`
- `frequentSignals`
- `latestInsightAt`
- `insightReferences`
- `sourceAIRequestLog`
- `supersedes`

### IntelligenceSignal

Fields:

- `signalLabel`
- `signalDomain`
- `sourceInsight`
- `sourceEvidence`
- `occurredAt`
- `aggregate`

Forbidden fields:

- score;
- rank;
- priority; and
- qualification.

---

## 11. PrimaryFilter and Queue Authority Boundary

Forbidden:

- PrimaryFilter source;
- Lead/ProspectPool filterList reference;
- CRM dashlet decision panel;
- workflow condition; and
- sort authority.

---

## 12. C22 Separation

C22 entities:

- `ProspectCandidate`
- `ProspectRun`
- `ActionGate`
- `ExecutionLedger`
- `OutreachExecution`
- `AutomationRule`
- `ActionLedger`

C21 does not provide:

- execution classes;
- execution guards;
- action save options; or
- automation runtime.

---

## 13. C20 Provenance

C21 references C20 evidence only. It does not own or duplicate C20 runtime.

Allowed provenance references:

```text
sourceAIRequestLogId
sourceAIJobId
```

`sourceAIRequestLogId` is the authoritative per-invocation provenance. If
`sourceAIJobId` is also stored, it must match the AIJob referenced by that
AIRequestLog.

C21 must not create or modify AIJob, AIRequestLog, PromptTemplate, Capability
Registry resolution, provider credentials, adapters, or routing.

---

## 14. Forbidden Scope

C21 does not authorize:

- provider execution, provider routing, or credential storage;
- AI runtime, agent execution, ActionLedger, or AutomationRule;
- email sending or outreach automation;
- score, rank, priority, or qualification authority;
- Lead, Opportunity, customer, or revenue lifecycle automation; or
- `ProspectCandidate` or any duplicate pre-CRM identity.

C21 also does not authorize PrimaryFilter source, Lead/ProspectPool filterList
references, CRM dashlet decision panels, workflow conditions, or sort
authority. C22 execution classes, execution guards, action save options, and
automation runtime remain outside the C21 namespace.

---

## 15. Work-Package Gate

WP1 is **ResearchEvidence Governance Hardening**, not entity creation. It must:

1. audit the existing ProspectPool and ResearchEvidence contracts;
2. preserve existing parent links, deduplication, and promotion inheritance;
3. introduce classification, validation, immutability, correction, and C20
   provenance without duplicating existing fields blindly;
4. provide migration/compatibility handling for existing evidence; and
5. prove C21 invariants without changing C20 or CRM lifecycle ownership.

Each later work package requires its own frozen design and tests. C22 remains a
separate phase.
