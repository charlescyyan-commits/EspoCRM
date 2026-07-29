# Phase3C23 Charter — AI Prospecting Optimization & Learning Governance

## Document Header

| Field | Value |
| --- | --- |
| **Document Type** | Phase Charter |
| **Subject** | C23 — AI Prospecting Optimization & Learning Governance Layer |
| **Status** | DRAFT (v1.1 — condition resolution applied per Amendment V1) |
| **Date** | 2026-07-30 |
| **Version** | v1.1-draft |
| **Amendment** | `docs/audit/PHASE3C23_CHARTER_AMENDMENT_V1.md` — Conditions C1–C6 resolved |
| **Invariant Count** | 22 (17 original + 5 new; 1 revised) |
| **Owner** | Phase3C23 Governance |
| **Baseline** | `phase3c22-final-freeze` |
| **C20 Charter** | ACTIVE — `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` |
| **C21 Charter** | FROZEN — `docs/PHASE3C21_CHARTER.md` |
| **C22 Charter** | FROZEN — `docs/audit/PHASE3C22_CHARTER_REVIEW.md` (APPROVED WITH CONDITIONS, all conditions resolved) |
| **C22 Invariant Registry** | `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md` (29 invariants, DOCUMENTATION_ONLY) |
| **Precedent** | C20 Invariant Registry (`docs/adr/C20_INVARIANT_REGISTRY.md`), C21 Invariant Registry (`docs/adr/C21_INVARIANT_REGISTRY.md`) |

---

## 1. Executive Summary

Phase3C23 defines the **AI Prospecting Optimization & Learning Governance Layer** — the fourth architectural layer in the EspoCRM AI governance stack.

### 1.1 Layer Stack Position

```text
┌──────────────────────────────────────────────────────────────┐
│ C23 — AI Prospecting Optimization & Learning  ← THIS CHARTER │
│   OptimizationInsight · PerformanceMetric                     │
│   ← Analyzes C21/C22 evidence; produces advisory insights     │
│   ← ADVISORY ONLY — no execution authority                   │
├──────────────────────────────────────────────────────────────┤
│ C22 — Autonomous Prospecting Execution Governance ← FROZEN   │
│   ProspectCandidate · ProspectRun · ActionGate                │
│   ExecutionLedger · OutreachExecution                         │
│   ← Execution governance; human-gated approval               │
├──────────────────────────────────────────────────────────────┤
│ C21 — AI Intelligence Governance          ← FROZEN           │
│   ResearchEvidence · AIQualificationInsight                   │
│   HumanFeedback · IntelligenceAggregate                       │
│   ← Advisory intelligence; no execution authority            │
├──────────────────────────────────────────────────────────────┤
│ C20 — AI Platform Foundation              ← ACTIVE           │
│   AIJob · AIRequestLog · PromptTemplate                       │
│   ProviderCredential · ProviderRoute · ProviderHealth         │
│   ← Execution governance; provider abstraction; credential     │
│     custody; cost accounting                                 │
├──────────────────────────────────────────────────────────────┤
│ Chitu — External Intelligence Authority  ← UNMODIFIABLE      │
│   canonical_score · qualification · research · scoring       │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Core Purpose

C23 is the **analytical and learning layer** that sits above C20/C21/C22. It consumes execution evidence from C22, intelligence evidence from C21, and provider execution data from C20 — then produces **advisory optimization insights** for human operators. C23 has **no execution authority, no approval authority, and no CRM lifecycle ownership**.

### 1.3 Why C23 Exists

C22 governs **whether and how** prospecting actions execute. It does not answer:

- Which strategies perform best over time?
- Which industry segments have higher reply rates?
- Which search approaches yield better-qualified candidates?
- What patterns emerge from human feedback on past decisions?
- How should optimization suggestions be governed?

C23 fills this gap — providing a governed space for execution analytics, performance intelligence, feedback learning, and optimization suggestions, all structurally prevented from crossing into execution authority.

---

## 2. C23 Definition

### 2.1 What C23 Is

C23 is the **AI Prospecting Optimization & Learning Governance Layer**. It provides:

| Capability | Description |
| --- | --- |
| **Execution Analytics** | Analyze C22 execution evidence (ExecutionLedger, ProspectRun outcomes, ActionGate decisions, ReplyDetection results) to produce governed metrics and reports |
| **Performance Intelligence** | Understand what prospecting strategies work — ICP performance, industry response patterns, provider effectiveness, outreach template performance |
| **Feedback Learning** | Convert human feedback (C21 HumanFeedback) and execution outcomes into structured improvement insights |
| **Optimization Suggestions** | Generate human-reviewable recommendations for search strategies, outreach optimization, and research improvement |

### 2.2 What C23 Is NOT

C23 is explicitly **NOT**:

| Not C23 | Owner | Rationale |
| --- | --- | --- |
| **Autonomous execution layer** | C22 | C23 analyzes execution; it does not initiate, approve, or modify execution |
| **Autonomous approval authority** | C22 (ActionGate) | C23 may suggest strategy changes; it cannot approve actions |
| **CRM lifecycle owner** | CRM Core | C23 does not create or mutate Lead, Account, Opportunity |
| **Provider runtime** | C20 | C23 does not invoke providers, hold credentials, or manage AI job execution |
| **Execution authority** | C22 | C23 output is advisory; human operators decide whether to act on insights |
| **Intelligence authority** | C21 | C23 consumes C21 intelligence as analytical input; it does not create, modify, or replace C21 records |
| **Scoring or qualification authority** | Chitu / C21 | C23 may observe scoring patterns; it does not compute or override scores |

### 2.3 C23 Governance Principle

**All AI output in C23 is ADVISORY ONLY.**

C23 may observe, analyze, correlate, and suggest. It may not decide, execute, approve, transition, or mutate. Every optimization insight must be presented for human review. No C23 output may directly trigger any C22 action, C21 record mutation, or CRM lifecycle change.

---

## 3. C20 / C21 / C22 Dependency

### 3.1 Dependency Diagram

```text
C23 consumes from:
  C20: AIJob records, AIRequestLog (cost, latency, provider performance)
  C21: ResearchEvidence, AIQualificationInsight, HumanFeedback
  C22: ExecutionLedger, ProspectRun, ActionGate decisions, ReplyDetection results

C23 MUST NOT write to:
  C20 entities (AIJob, AIRequestLog, PromptTemplate, ProviderCredential)
  C21 entities (ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate)
  C22 entities (ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, OutreachExecution)
  CRM Core entities (Lead, Account, Opportunity, any lifecycle field)
  Chitu fields (canonical_score)
```

### 3.2 C20 Dependency — AI Platform Foundation

C23 may **read** C20 execution records for analytical purposes:

| C20 Record | C23 Consumption | Purpose |
| --- | --- | --- |
| `AIJob` | Read-only | Analyze AI execution patterns, provider performance, cost trends |
| `AIRequestLog` | Read-only | Analyze token usage, latency, model performance across providers |

C23 MUST NOT:
- Create, modify, or delete C20 execution records
- Hold or manage provider credentials
- Invoke providers directly
- Bypass C20 connector egress (reaffirms C20 D3)

### 3.3 C21 Dependency — AI Intelligence Governance

C23 may **read** C21 intelligence records as analytical input:

| C21 Record | C23 Consumption | Purpose |
| --- | --- | --- |
| `ResearchEvidence` | Read-only | Correlate research evidence quality with outreach outcomes |
| `AIQualificationInsight` | Read-only | Analyze qualification patterns against execution results |
| `HumanFeedback` | Read-only | Learn from operator corrections and feedback history |
| `IntelligenceAggregate` | Read-only | Consume aggregated intelligence views for trend analysis |

C23 MUST NOT:
- Replace C21 intelligence ownership
- Mutate C21 authority fields (classification, confidence, provenance)
- Create a competing intelligence lifecycle
- Create a parallel intelligence store (reaffirms C22-INV-C21-003 pattern)
- Reinterpret or override C21 qualification signals

#### 3.3.1 Hard C21/C23 Intelligence Separation

C21 and C23 serve fundamentally different intelligence purposes at different levels of abstraction. This separation is structural, not policy-level:

| Dimension | C21 AIQualificationInsight | C23 OptimizationInsight |
| --- | --- | --- |
| **Granularity** | Per-prospect (individual ProspectPool) | Aggregate (cohorts, segments, time windows) |
| **Question Answered** | "Is this specific prospect qualified?" | "Which strategies work better across many prospects?" |
| **Confidence Meaning** | AI certainty about prospect fit | Statistical confidence in the recommendation |
| **Output Type** | Qualification recommendation | Strategy/process recommendation |
| **Consumer** | Human operator evaluating a prospect | Human operator reviewing strategy |
| **Authority** | Advisory only (C21-INV-03) | Advisory only (C23-INV-ADV-001) |

**OptimizationInsight MUST NOT represent:**
- Per-prospect qualification intelligence (C21 territory)
- Ranking authority — "Prospect A > Prospect B" (Chitu/C21 territory)
- Intelligence interpretation — "This evidence means the prospect is qualified" (C21 territory)
- Individual prospect recommendations — "Send outreach to this prospect" (C22 territory)

**Enforced by:** C23-INV-SEP-004 (aggregate strategy only), C23-INV-PROV-003 (aggregate evidence only).

### 3.4 C22 Dependency — Autonomous Prospecting Execution Governance

C23 may **analyze** C22 execution evidence:

| C22 Record | C23 Consumption | Purpose |
| --- | --- | --- |
| `ExecutionLedger` | Read-only | Analyze execution patterns, failure rates, retry patterns, cost per action |
| `ProspectRun` | Read-only | Analyze run-level performance: candidate quality, conversion rates, budget efficiency |
| `ActionGate` (decisions) | Read-only | Analyze approval patterns: denial rates, approval velocity, gate effectiveness |
| `ReplyDetection` (results) | Read-only | Analyze reply rates, sentiment patterns, response timing |

C23 MUST NOT:
- Modify ExecutionLedger (reaffirms C22-INV-EX-003: append-only)
- Change ProspectRun state (reaffirms C22-INV-EX-004: execution container)
- Bypass ActionGate (reaffirms C22-INV-EX-001)
- Trigger execution (reaffirms C22-INV-EX-005: chain terminates at ReplyDetection)
- Auto-create CRM entities (reaffirms C22-INV-CRM-001 through CRM-004)

#### 3.4.1 ActionGate Isolation — C23 Data at the Gate

C23 analytics data (PerformanceMetric values, OptimizationInsight recommendations, and any derived C23 output) **MUST NOT be presented in the C22 ActionGate review interface or used as evidence in ActionGate approval/denial decisions.** C23 data is for strategic review by human operators outside the execution gating context — not for operational gating.

**Correct path:**
```text
C23 OptimizationInsight → Human Strategy Review → Human configures ProspectRun
                                                       ↓
                                            Each action still goes through
                                            ActionGate on its own merits
                                            (NO C23 data at the gate)
```

**Forbidden path:**
```text
C23 PerformanceMetric → Displayed at ActionGate → Influences approval decision
                         ← BLOCKED by C23-INV-SEP-005
```

**Enforced by:** C23-INV-SEP-005 (C23 data must not be presented at ActionGate). ActionGate inputs remain: ProspectCandidate identity, C21 intelligence context, proposed action details, predicted cost. C23 data is not among them.

### 3.5 Dependency Compliance Matrix

| Boundary | Rule | C23 Compliance |
| --- | --- | --- |
| C20 D3 | All outbound provider I/O through connector | C23 has no provider I/O — analytical only |
| C20 §5.2 | Credential custody model | C23 holds no credentials |
| C21 §4 | Candidate identity ownership | C23 does not create candidate identities |
| C21 §6 | Intelligence authority | C23 reads intelligence; does not claim authority |
| C22-INV-EX-001 | ActionGate is sole authorization boundary | C23 does not authorize actions |
| C22-INV-EX-003 | ExecutionLedger is append-only | C23 reads only; does not write |
| C22-INV-C21-001 | C21 records read-only to C22 | C23 extends this: also read-only to C23 |
| C22-INV-C21-003 | No parallel intelligence store | C23 creates OptimizationInsight (advisory), not intelligence evidence |
| C22-INV-CRM-001 | No auto-create Lead | C23 does not touch CRM entities |
| C22-INV-EX-005 | Chain terminates at ReplyDetection | C23 analyzes post-termination; does not extend chain |
| C23-INV-SEP-004 | OptimizationInsight is aggregate strategy, not per-prospect qualification | OptimizationInsight structurally distinct from AIQualificationInsight; no per-prospect intelligence |
| C23-INV-SEP-005 | C23 data not at ActionGate | C23 output excluded from ActionGate review interface and evidence |
| C23-INV-PROV-003 | Aggregate evidence only | OptimizationInsight references only aggregate sources; no ProspectCandidate/ProspectPool/Lead references |

---

## 4. Scope

### 4.1 Work Package Overview

| WP | Title | Purpose | Status |
| --- | --- | --- | --- |
| WP1 | Execution Analytics Foundation | Analyze C22 execution evidence; produce metrics, reports, analytics views | PLANNED |
| WP2 | Prospecting Performance Intelligence | Understand what prospecting strategies work across ICP, industry, provider, and template dimensions | PLANNED |
| WP3 | Feedback Learning Layer | Convert human feedback and execution outcomes into structured improvement insights | PLANNED |
| WP4 | Optimization Assistant | Generate human-reviewable recommendations for strategy, outreach, and research improvement | PLANNED |

### 4.2 WP1 — Execution Analytics Foundation

**Purpose:** Establish the analytical foundation by consuming and analyzing C22 execution evidence.

**Data Sources:**
- `ExecutionLedger` — per-action execution records (success, failure, cost, latency, provider)
- `ProspectRun` — run-level metadata (candidate set, budget, chain depth, outcomes)
- `ActionGate` — approval/denial decisions with timestamps and operator identity
- `ReplyDetection` — reply events, sentiment indicators, response timing

**Outputs:**
- **Execution Metrics:** Success rates, failure rates by category, retry frequency, cost per action, latency distributions
- **Run Reports:** Per-run summaries with candidate count, action count, budget consumption, outcome distribution
- **Analytics Views:** Dashlet-compatible data structures for pipeline health, execution trends, and provider performance

**Explicitly NOT:**
- Real-time execution monitoring (C22 owns execution state)
- Execution intervention (C23 cannot pause, resume, or cancel runs)
- ActionGate decision-making (C23 observes decisions; does not influence them)

### 4.3 WP2 — Prospecting Performance Intelligence

**Purpose:** Understand what prospecting strategies and patterns produce better outcomes.

**Analysis Dimensions:**

| Dimension | Question Answered | Data Sources |
| --- | --- | --- |
| **ICP Performance** | Which ideal customer profiles yield higher reply rates? | ProspectRun → ExecutionLedger → ReplyDetection; C21 AIQualificationInsight |
| **Industry Response Patterns** | Which industries respond better to which outreach types? | ProspectCandidate enrichment data → ExecutionLedger → ReplyDetection |
| **Provider Effectiveness** | Which search/enrichment providers produce higher-quality candidates? | C20 AIJob/AIRequestLog → ProspectRun outcomes |
| **Outreach Template Performance** | Which email/outreach templates generate more positive replies? | OutreachExecution → ReplyDetection sentiment |
| **Timing Analysis** | Does send time/day affect reply rates? | ExecutionLedger timestamps → ReplyDetection timing |
| **Research Quality Correlation** | Does deeper AI research correlate with better outcomes? | C21 ResearchEvidence depth/confidence → execution outcomes |

**Outputs:**
- Performance dashboards segmented by ICP, industry, provider, template
- Comparative effectiveness reports
- Trend analysis over time windows

**Explicitly NOT:**
- Automatic strategy changes based on performance data
- Real-time campaign optimization (human reviews insights)
- Scoring or ranking individual candidates (C21/Chitu authority)

### 4.4 WP3 — Feedback Learning Layer

**Purpose:** Convert human feedback and execution outcomes into structured improvement insights.

**Input Sources:**
- **C21 HumanFeedback:** Structured operator corrections — what did humans override, reject, or confirm?
- **C22 Execution Outcomes:** What actions succeeded? What failed and why?
- **C21 Research Signals:** What research evidence proved accurate or inaccurate based on outcomes?
- **ActionGate Decision Patterns:** What types of actions do operators consistently approve or deny?

**Learning Loop (Human-Mediated):**

```text
┌─────────────────────────────────────────────────────────────┐
│ FEEDBACK LEARNING LOOP (human at the center)                │
│                                                             │
│  C21 HumanFeedback ──┐                                      │
│  C22 Execution Outcomes ──┤                                 │
│  C21 Research Signals ──┤                                   │
│  ActionGate Patterns ──┘                                    │
│         │                                                   │
│         ↓                                                   │
│  C23 Analysis & Correlation                                 │
│         │                                                   │
│         ↓                                                   │
│  OptimizationInsight (advisory)                              │
│         │                                                   │
│         ↓                                                   │
│  HUMAN REVIEW ←── operator decides to adopt, adapt,         │
│         │         or dismiss the insight                    │
│         ↓                                                   │
│  Human updates strategy / template / search config           │
│  (through C22 configuration, NOT through C23 automation)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Outputs:**
- Structured `OptimizationInsight` records linking feedback patterns to actionable suggestions
- Feedback-to-outcome correlation reports
- Operator decision pattern analysis

**Explicitly NOT:**
- Automatic strategy adjustment based on feedback
- Closed-loop automation (loop always includes human)
- Overriding operator decisions based on "learned" patterns

### 4.5 WP4 — Optimization Assistant

**Purpose:** Generate human-reviewable optimization recommendations.

**Suggestion Categories:**

| Category | Example | Source Evidence |
| --- | --- | --- |
| **Search Strategy** | "LinkedIn Sales Navigator produced 2.3× more qualified candidates than Apify Google Search for ICP segment 'SaaS 50-200 employees'" | ProspectRun → candidate quality → reply rate correlation |
| **Outreach Optimization** | "Template variant B had 40% higher reply rate than variant A for CTO titles in healthcare" | OutreachExecution → ReplyDetection by template + title + industry |
| **Research Improvement** | "Candidates with ≥3 ResearchEvidence records had 2× higher positive reply rate — suggest deeper research for high-value ICPs" | C21 ResearchEvidence count/confidence → execution outcomes |
| **Provider Selection** | "Provider X consistently returns higher-quality enrichments for European companies than Provider Y" | C20 AIRequestLog → ProspectCandidate enrichment quality → outcomes |
| **Timing Optimization** | "Emails sent Tuesday 9-11am UTC have 28% higher open rate than Monday/Friday sends" | ExecutionLedger timestamps → ReplyDetection timing |
| **Budget Allocation** | "ICP segment A has 3× ROI vs segment C — suggest reallocating ProspectRun budget" | Cost data (C20) → outcome data (C22) → segment analysis |

**Output Format:**

Each `OptimizationInsight` includes:
- Clear, specific recommendation in human-readable form
- Supporting evidence with source references
- Confidence level
- Suggested scope of application
- Explicit "for human review" marker

**Explicitly NOT:**
- Automatic decision maker
- "Approve this action" directives
- "Execute this run" commands
- "Create this Lead" suggestions
- Anything that could be interpreted as an execution instruction

---

## 5. Non-Scope

### 5.1 Explicitly Excluded from C23

| Exclusion | Reason | Owner |
| --- | --- | --- |
| Autonomous execution | C22 owns execution governance; C23 analyzes only | C22 |
| Autonomous approval | ActionGate is the sole authorization boundary; C23 does not approve | C22 |
| CRM lifecycle ownership | Lead, Account, Opportunity are CRM Core | CRM Core |
| Provider runtime | C20 owns provider abstraction, credential custody, AI job execution | C20 |
| Execution authority | C23 output is advisory; no entity may act on C23 output automatically | C22 |
| Intelligence creation | C21 owns ResearchEvidence, AIQualificationInsight, HumanFeedback | C21 |
| Scoring / qualification | Chitu owns canonical_score; C21 owns qualification insight | Chitu / C21 |
| Real-time monitoring / alerting | C23 analyzes historical patterns; it does not monitor live execution | C22 |
| Configuration mutation | C23 suggests changes; it does not modify C22 AutomationRule, provider config, or template content | C22 |
| Data retention policy | C23 follows C20/C21/C22 retention; does not define independent retention | C20/C21/C22 |

### 5.2 Forbidden Entity Types

The following entity types MUST NOT be created under C23 authority:

| Forbidden Entity | Rationale |
| --- | --- |
| `LearningAgent` | Implies autonomous learning capability — violates advisory-only principle |
| `AutoOptimizer` | Implies automatic optimization — violates human governance |
| `StrategyExecutor` | Implies execution authority — C22 owns execution |
| `AutonomousDecision` | Implies decision authority — violates ActionGate boundary |
| `C23ExecutionLedger` | Would duplicate C22 ExecutionLedger |
| `C23ResearchEvidence` | Would create parallel intelligence store (violates C22-INV-C21-003 pattern) |
| `C23QualificationInsight` | Would compete with C21 AIQualificationInsight |
| `OptimizationRule` (auto-applying) | Rules that auto-apply optimization suggestions are forbidden; all suggestions require human review |

---

## 6. Entity Ownership

### 6.1 Proposed Entities

#### 6.1.1 OptimizationInsight

**Purpose:** Store advisory optimization recommendations for human review.

**Ownership:** C23

**Lifecycle:** Created by C23 analysis services; reviewed by human operators; marked as adopted, adapted, dismissed, or superseded. Immutable after creation — status changes via supersession (new record references prior record), not mutation.

| Field | Type | Description |
| --- | --- | --- |
| `insightType` | Enum | `SEARCH_STRATEGY`, `OUTREACH_OPTIMIZATION`, `RESEARCH_IMPROVEMENT`, `PROVIDER_SELECTION`, `TIMING_OPTIMIZATION`, `BUDGET_ALLOCATION`, `ICP_PERFORMANCE`, `FEEDBACK_PATTERN` |
| `title` | String | Human-readable summary of the insight |
| `description` | Text | Detailed recommendation with context |
| `confidence` | Float (0.0–1.0) | Statistical or heuristic confidence in the insight |
| `evidenceReference` | JSON Array | References to **aggregate-level** source records only. Allowed entityTypes: `PerformanceMetric`, `ProspectRun`, `ExecutionLedger`, `IntelligenceAggregate`, `AIJob`, `AIRequestLog`. Forbidden: `ProspectCandidate`, `ProspectPool`, `Lead`, `Account`, `Opportunity`, `ResearchEvidence`, `AIQualificationInsight`. (C23-INV-PROV-003) |
| `recommendation` | Text | Specific, actionable suggestion for human operator |
| `suggestedScope` | JSON | Optional scope constraints: `{icpSegment, industry, provider, templateId, maxApplications}` |
| `status` | Enum | `PROPOSED`, `REVIEWED`, `ADOPTED`, `ADAPTED`, `DISMISSED`, `SUPERSEDED` |
| `supersedes` | FK → OptimizationInsight | Link to prior insight this one replaces (nullable) |
| `reviewedBy` | FK → User | Operator who reviewed the insight (nullable until reviewed) |
| `reviewedAt` | DateTime | When the operator reviewed the insight |
| `reviewNotes` | Text | Operator notes on adoption/dismissal decision |
| `createdAt` | DateTime | Auto-generated |
| `createdBy` | FK → User | Analysis service or system identity |
| `sourcePeriodStart` | DateTime | Start of the source data period this insight is based on (C23-INV-PROV-004) |
| `sourcePeriodEnd` | DateTime | End of the source data period this insight is based on (C23-INV-PROV-004) |
| `generatedAt` | DateTime | When this insight was generated — may differ from createdAt for batch-generated insights (C23-INV-PROV-004) |
| `freshnessStatus` | Enum | `CURRENT` (within freshness window: generatedAt ≤ 30d, sourcePeriodEnd ≤ 90d), `AGING` (approaching staleness: generatedAt 31–60d or sourcePeriodEnd 91–180d), `STALE` (exceeds freshness: generatedAt > 60d or sourcePeriodEnd > 180d), `ARCHIVAL` (historical reference only). Stale insights must carry explicit staleness warning when displayed. (C23-INV-PROV-004) |

**Forbidden Fields:**
- `execute` — implies execution authority
- `approve` — implies approval authority
- `authorization` — implies gate bypass
- `lifecycleTransition` — implies CRM mutation authority
- `autoApply` — implies automated application
- `targetActionGateDecision` — implies influencing ActionGate

#### 6.1.2 PerformanceMetric

**Purpose:** Store governed analytical measurements derived from C20/C21/C22 data.

**Ownership:** C23

**Lifecycle:** Created by C23 analytics services. Immutable after creation. Each metric is a point-in-time measurement with defined scope and period. Metrics are never updated — new measurements produce new records.

| Field | Type | Description |
| --- | --- | --- |
| `metricType` | Enum | `SUCCESS_RATE`, `REPLY_RATE`, `POSITIVE_REPLY_RATE`, `COST_PER_ACTION`, `COST_PER_POSITIVE_REPLY`, `AVERAGE_LATENCY`, `ACTIONGATE_DENIAL_RATE`, `CANDIDATE_OUTCOME_QUALITY` (measures execution outcome quality for candidate cohorts — reply rates, conversion rates; NOT a qualification/ranking score), `TEMPLATE_PERFORMANCE`, `PROVIDER_PERFORMANCE`, `ICP_PERFORMANCE`, `RESEARCH_DEPTH_CORRELATION` |
| `scope` | JSON | What this metric covers: `{icpSegment, industry, providerId, templateId, timeWindow, runId}` |
| `period` | JSON | Measurement period: `{start, end}` |
| `value` | Float | The computed metric value |
| `unit` | String | `percentage`, `count`, `currency`, `milliseconds`, `ratio` |
| `sampleSize` | Integer | Number of data points this metric is based on |
| `sourceReference` | JSON Array | References to source data: `[{entityType, entityId, role}]` |
| `confidenceInterval` | JSON | Optional: `{lower, upper, confidenceLevel}` |
| `computedAt` | DateTime | When this metric was computed |
| `computedBy` | String | Service or process that computed this metric |

**Forbidden Fields:**
- `target` — implies automated targeting
- `threshold` — implies automated alerting/action
- `action` — implies execution trigger
- `alertRule` — implies real-time monitoring (out of scope)

### 6.2 Entity Relationship Map

```text
C23 Entities:
  OptimizationInsight
    ├── references → C21 HumanFeedback
    ├── references → C21 ResearchEvidence
    ├── references → C21 AIQualificationInsight
    ├── references → C22 ExecutionLedger
    ├── references → C22 ProspectRun
    ├── references → C22 ActionGate (decisions)
    └── supersedes → OptimizationInsight (self-referential)

  PerformanceMetric
    ├── references → C22 ExecutionLedger
    ├── references → C22 ProspectRun
    ├── references → C22 ReplyDetection
    ├── references → C20 AIJob
    └── references → C20 AIRequestLog

C23 MUST NOT create FK relationships that imply:
  - Mutation authority over referenced entities
  - Lifecycle ownership of referenced entities
  - Execution or approval authority
```

### 6.3 Entity Existence Check

As of the `phase3c22-final-freeze` baseline:

- No `OptimizationInsight` entity definition, service, hook, or scope exists
- No `PerformanceMetric` entity definition, service, hook, or scope exists
- No C23 entities exist in any form
- C22 test suites do not reference C23 entities

---

## 7. AI Advisory Boundary

### 7.1 The Advisory-Only Principle

**C23 AI output is ADVISORY ONLY.** This is a structural constraint, not a policy preference. It is enforced through:

1. **Entity design:** `OptimizationInsight` has no `execute`, `approve`, or `authorization` fields
2. **Service boundaries:** C23 services have no write access to C20/C21/C22/CRM entities
3. **Contract tests:** Every C23 output path is verified to not trigger execution, approval, or mutation
4. **Charter governance:** Violation of advisory-only is a Charter breach requiring amendment

### 7.2 Allowed vs Forbidden AI Output

| Category | Allowed (Advisory) | Forbidden (Executive) |
| --- | --- | --- |
| **Strategy** | "Industry segment A has 2.3× higher reply rate than segment B" | "Switch all runs to segment A" |
| **Search** | "Search provider X produced higher quality candidates for European ICPs" | "Change default search provider to X" |
| **Template** | "Template variant C had 40% higher positive reply rate for CTO titles" | "Use template variant C for all CTO outreach" |
| **Research** | "Deeper research correlated with 2× higher reply rate" | "Increase research depth to maximum for all candidates" |
| **Budget** | "ICP segment A shows 3× ROI vs segment C" | "Reallocate 50% of budget to segment A" |
| **Timing** | "Tuesday 9-11am UTC shows 28% higher open rate" | "Schedule all sends for Tuesday 9-11am" |
| **Provider** | "Provider X outperforms Provider Y for European enrichments" | "Route all European enrichment to Provider X" |
| **Qualification** | "Candidates in segment A with ≥3 research evidence records had 2× higher positive reply rate — suggest deeper research for high-value ICPs" | "Prospect X is qualified — approve outreach"; "Prospect A ranks higher than Prospect B" |

### 7.3 The Bright Line

The distinction between advisory and executive output is:

- **Advisory:** States an observation, pattern, or correlation with supporting evidence. Answers "what" and "why."
- **Executive:** Issues a directive, command, or automated decision. Answers "do this."

C23 may only produce advisory output. Any output interpretable as a directive ("approve," "send," "execute," "create," "switch," "route," "schedule," "reallocate") is a Charter violation.

### 7.4 AI Model Usage in C23

C23 may use AI models (via C20 capability interfaces) for:

- Pattern detection in execution data
- Correlation analysis across performance dimensions
- Natural language generation of insight descriptions
- Confidence scoring of detected patterns

C23 MUST NOT use AI models for:
- Making execution decisions
- Approving or denying actions
- Modifying entity state outside C23
- Generating executable code or configuration

All AI model invocations in C23 must route through C20 capability interfaces (reaffirms C20 D3). C23 does not hold AI model credentials.

---

## 8. Human Governance

### 8.1 Human Ownership

Human operators remain the sole owners of:

| Decision Domain | Human Authority | C23 Role |
| --- | --- | --- |
| **Adoption of optimization suggestions** | Human decides which insights to act on | C23 presents insights with evidence and confidence |
| **Strategy changes** | Human modifies search strategy, ICP targeting, provider selection | C23 provides performance data to inform the decision |
| **Execution policy changes** | Human adjusts ProspectRun parameters, budget limits, retry policies | C23 provides historical performance data |
| **Template changes** | Human edits, activates, or deactivates outreach templates | C23 provides comparative performance data |
| **Provider configuration** | Human selects and configures providers | C23 provides comparative provider effectiveness data |

### 8.2 Human Review Requirements

Every `OptimizationInsight` must be:
1. Presented to a human operator with clear evidence references
2. Explicitly marked as "for human review — not auto-applied"
3. Tracked through human review status (PROPOSED → REVIEWED → ADOPTED/ADAPTED/DISMISSED)
4. Immutable after creation — human decisions are recorded as new status, not as edits to the insight

### 8.3 Future Automation Gate

Any future automation of C23 insights (e.g., auto-apply low-confidence suggestions, auto-adjust budget allocation within bounds) requires:

1. A dedicated C23 Charter Amendment
2. A new ADR defining the automation scope, bounds, and human override mechanism
3. Explicit invariant updates
4. Independent governance review

**C23 starts with zero automation. All insight → action transitions are human-mediated.** This is not a temporary phase — it is the structural default, following the same pattern established by C22-INV-EX-002 (human approval is permanent default for ActionGate).

### 8.4 Human Governance Invariant (Preliminary)

| ID | Statement |
| --- | --- |
| C23-INV-HG-001 | Every C23 optimization insight requires human review before any corresponding strategy, configuration, or execution change. C23 output has no automatic effect on any C20/C21/C22/CRM entity. |

---

## 9. WP Roadmap

### 9.1 Work Package Sequence

```text
WP1: Execution Analytics Foundation
  └── Prerequisite: C22 ExecutionLedger + ProspectRun entities implemented
  └── Deliverable: Metrics engine, analytics views, PerformanceMetric entity
  └── Exit Gate: At least 5 metric types computable from C22 execution data

WP2: Prospecting Performance Intelligence
  └── Prerequisite: WP1 (metrics foundation) + C22 execution data populated
  └── Deliverable: Multi-dimensional performance analysis, comparative reports
  └── Exit Gate: ICP, industry, provider, and template performance dashboards

WP3: Feedback Learning Layer
  └── Prerequisite: WP1 + C21 HumanFeedback entity populated
  └── Deliverable: OptimizationInsight entity, feedback-to-outcome correlation
  └── Exit Gate: Feedback patterns detectable and convertible to structured insights

WP4: Optimization Assistant
  └── Prerequisite: WP2 + WP3 (performance data + feedback learning)
  └── Deliverable: OptimizationInsight generation, human review workflow
  └── Exit Gate: End-to-end insight generation → human review → adoption tracking
```

### 9.2 WP Dependencies

| WP | Depends On | Blocks |
| --- | --- | --- |
| WP1 | C22 ExecutionLedger, ProspectRun entities implemented | WP2, WP3 |
| WP2 | WP1 (metrics foundation) | WP4 |
| WP3 | WP1 + C21 HumanFeedback populated | WP4 |
| WP4 | WP2 + WP3 | Nothing (terminal WP) |

### 9.3 WP Exit Gates

Each WP must satisfy its exit gate before the next WP can begin:

| WP | Exit Gate Criteria |
| --- | --- |
| WP1 | 5+ metric types computable; PerformanceMetric entity defined; analytics data structures defined |
| WP2 | Performance analysis across 4+ dimensions (ICP, industry, provider, template); dashboard data contracts defined |
| WP3 | OptimizationInsight entity defined; feedback-to-outcome correlation methodology documented; ≥1 feedback pattern category detectable |
| WP4 | End-to-end insight generation pipeline; human review workflow defined; adoption/dismissal tracking functional |

---

## 10. ADR Roadmap

### 10.1 Required ADRs

| ADR ID | Title | Purpose | Phase | Depends On |
| --- | --- | --- | --- | --- |
| ADR-C23-001 | Optimization Ownership Boundary | Define C23's ownership scope: what C23 owns vs what it consumes from C20/C21/C22. Establish advisory-only governance principle, C21/C23 intelligence separation boundary (C23-INV-SEP-004), aggregate evidence constraints (C23-INV-PROV-003), and ActionGate isolation (C23-INV-SEP-005). | Phase 1 | C22 Charter (FROZEN) |
| ADR-C23-002 | Execution Analytics Data Ownership | Define how C23 reads and analyzes C22 execution data without claiming ownership or mutation authority. Define PerformanceMetric entity governance. | Phase 1 | ADR-C23-001 |
| ADR-C23-003 | Feedback Learning Governance | Define how C23 consumes C21 HumanFeedback and execution outcomes to produce learning insights. Establish the human-mediated learning loop. | Phase 2 | ADR-C23-001, ADR-C23-002 |
| ADR-C23-004 | Optimization Suggestion Boundary | Define the allowed vs forbidden forms of C23 optimization suggestions. Establish the bright line between advisory and executive AI output. | Phase 2 | ADR-C23-001, ADR-C23-003 |
| ADR-C23-005 | Metric Governance | Define PerformanceMetric computation methodology, scope definitions, confidence requirements, stratified sample size thresholds (C23-INV-MET-004, revised C23-INV-MET-001), and data freshness/staleness governance (C23-INV-PROV-004). Prevent metric misuse including as C22 AutomationRule conditions. | Phase 1 | ADR-C23-002 |

### 10.2 ADR Sequence

```text
Phase 1 (Foundation):
  ADR-C23-001 (Ownership Boundary)
    ├── ADR-C23-002 (Analytics Data Ownership)
    └── ADR-C23-005 (Metric Governance)

Phase 2 (Learning & Optimization):
  ADR-C23-003 (Feedback Learning Governance)
    └── ADR-C23-004 (Optimization Suggestion Boundary)
```

### 10.3 ADR Status Tracking

| ADR | Status | Author | Review Date | Activation Trigger |
| --- | --- | --- | --- | --- |
| ADR-C23-001 | NOT STARTED | — | — | C23 Charter ratification |
| ADR-C23-002 | NOT STARTED | — | — | ADR-C23-001 accepted |
| ADR-C23-003 | NOT STARTED | — | — | WP2 exit gate satisfied |
| ADR-C23-004 | NOT STARTED | — | — | ADR-C23-003 accepted |
| ADR-C23-005 | NOT STARTED | — | — | ADR-C23-002 accepted |

---

## 11. Invariant Registry Plan

### 11.1 Registry Location

Target: `docs/adr/C23_INVARIANT_REGISTRY.md`

Following the precedent established by:
- `docs/adr/C20_INVARIANT_REGISTRY.md` (22 invariants, machine-readable format)
- `docs/adr/C21_INVARIANT_REGISTRY.md` (C21 invariants)
- `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md` (29 invariants, DOCUMENTATION_ONLY)

### 11.2 Initial Invariant Categories

| Category | Prefix | Scope | Count (Initial) |
| --- | --- | --- | --- |
| **1. Ownership Boundary** | `C23-INV-OWN-` | What C23 owns vs consumes; entity ownership exclusivity | 4 |
| **2. Data Provenance** | `C23-INV-PROV-` | Source traceability, aggregate-only evidence, data freshness/staleness | 4 |
| **3. Advisory-Only AI** | `C23-INV-ADV-` | All C23 AI output is advisory; no execution/approval/decision authority | 3 |
| **4. Human Governance** | `C23-INV-HG-` | Human review required for all insights; no auto-application | 2 |
| **5. C21/C22 Separation** | `C23-INV-SEP-` | C23 does not mutate C21/C22 entities; read-only consumption; aggregate-only intelligence; ActionGate isolation | 5 |
| **6. Metric Integrity** | `C23-INV-MET-` | Stratified sample thresholds; confidence requirements; reproducible methodology; prohibition on metric-driven automation | 4 |

### 11.3 Initial Invariant Candidates

#### Category 1: Ownership Boundary

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-OWN-001 | C23 owns `OptimizationInsight` and `PerformanceMetric` exclusively. No other layer may create, modify, or delete these entities. | DOCUMENTATION_ONLY |
| C23-INV-OWN-002 | C23 does not own any C20, C21, C22, or CRM Core entity. C23 read access is governed by each layer's own invariants. | DOCUMENTATION_ONLY |
| C23-INV-OWN-003 | `OptimizationInsight` is immutable after creation. Status changes are recorded via supersession (new record references prior), not mutation. | DOCUMENTATION_ONLY |
| C23-INV-OWN-004 | `PerformanceMetric` is immutable after creation. Each metric is a point-in-time measurement. Updates produce new records. | DOCUMENTATION_ONLY |

#### Category 2: Data Provenance

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-PROV-001 | Every `OptimizationInsight` must reference specific source evidence (entityType + entityId) supporting the recommendation. Insights without evidence references are invalid. | DOCUMENTATION_ONLY |
| C23-INV-PROV-002 | Every `PerformanceMetric` must declare its scope, period, sample size, and source references. Metrics without declared methodology are invalid. | DOCUMENTATION_ONLY |
| C23-INV-PROV-003 | `OptimizationInsight.evidenceReference` MUST reference only aggregate operational evidence sources. References to individual prospect identities (`ProspectCandidate`, `ProspectPool`), CRM identities (`Lead`, `Account`, `Opportunity`), or per-prospect intelligence records (`ResearchEvidence`, `AIQualificationInsight`) are forbidden. | DOCUMENTATION_ONLY |
| C23-INV-PROV-004 | Every `OptimizationInsight` must declare `sourcePeriodStart`, `sourcePeriodEnd`, and `generatedAt`. Insights where `sourcePeriodEnd` exceeds 180 days or `generatedAt` exceeds 60 days MUST be flagged `STALE`. Stale insights MUST NOT be presented as current recommendations without an explicit staleness warning. | DOCUMENTATION_ONLY |

#### Category 3: Advisory-Only AI

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-ADV-001 | No C23 AI output may be interpreted as an execution directive. The advisory-only principle is structurally enforced through entity design (no execute/approve/authorization fields). | DOCUMENTATION_ONLY |
| C23-INV-ADV-002 | C23 AI model invocations route through C20 capability interfaces. C23 does not hold AI model credentials or invoke AI providers directly. | DOCUMENTATION_ONLY |
| C23-INV-ADV-003 | C23 must not generate output interpretable as: approve, send, execute, create, switch, route, schedule, or reallocate. Output is limited to observations, patterns, correlations, and suggestions. | DOCUMENTATION_ONLY |

#### Category 4: Human Governance

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-HG-001 | Every `OptimizationInsight` requires human review before any corresponding strategy, configuration, or execution change. C23 output has no automatic effect on any entity outside C23. | DOCUMENTATION_ONLY |
| C23-INV-HG-002 | Any future automation of C23 insight application requires a dedicated C23 Charter Amendment with new ADR, invariant updates, and independent governance review. Zero automation is the structural default. | DOCUMENTATION_ONLY |

#### Category 5: C21/C22 Separation

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-SEP-001 | C23 reads C21 intelligence records (ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate) as read-only analytical input. C23 must not create, modify, or delete C21 records. | DOCUMENTATION_ONLY |
| C23-INV-SEP-002 | C23 reads C22 execution records (ExecutionLedger, ProspectRun, ActionGate decisions, ReplyDetection results) as read-only analytical input. C23 must not create, modify, or delete C22 records. | DOCUMENTATION_ONLY |
| C23-INV-SEP-003 | C23 must not create a parallel intelligence store, execution ledger, or qualification authority. OptimizationInsight is structurally distinct from ResearchEvidence and AIQualificationInsight. | DOCUMENTATION_ONLY |
| C23-INV-SEP-004 | `OptimizationInsight` provides aggregate operational strategy recommendations. It MUST NOT represent per-prospect qualification intelligence, ranking authority, intelligence interpretation, or individual prospect recommendations. `OptimizationInsight` is structurally distinct from `AIQualificationInsight` in granularity, purpose, confidence meaning, and consumer. | DOCUMENTATION_ONLY |
| C23-INV-SEP-005 | C23 analytics data (`PerformanceMetric` values, `OptimizationInsight` recommendations, and any derived C23 output) MUST NOT be presented in the C22 ActionGate review interface or used as evidence in ActionGate approval/denial decisions. C23 data is for strategic review, not operational gating. | DOCUMENTATION_ONLY |

#### Category 6: Metric Integrity

| ID | Statement | Status |
| --- | --- | --- |
| C23-INV-MET-001 | Every `PerformanceMetric` must declare its `sampleSize`. Metrics with sampleSize below the category-specific threshold defined in C23-INV-MET-004 must be flagged `LOW_CONFIDENCE` and include a mandatory confidence interval. Metrics with no declared sampleSize are invalid. (REVISED — original flat n≥5 threshold superseded by C23-INV-MET-004) | DOCUMENTATION_ONLY |
| C23-INV-MET-002 | `PerformanceMetric` values must not be used as automated triggers for execution, approval, or configuration changes — including as conditions in C22 `AutomationRule` definitions. Metrics inform human decisions; they do not drive automation. | DOCUMENTATION_ONLY |
| C23-INV-MET-003 | Metric computation methodology must be documented and reproducible. The same inputs must produce the same metric value. Non-deterministic computation is forbidden. | DOCUMENTATION_ONLY |
| C23-INV-MET-004 | `PerformanceMetric` sample size thresholds are stratified by metric category: descriptive metrics require n ≥ 5; comparative optimization metrics require n ≥ 30 per group; trend metrics require n ≥ 3 time periods each with n ≥ 10. Metrics below their category threshold MUST be flagged `LOW_CONFIDENCE` and include a mandatory confidence interval. Comparative metrics below threshold MUST additionally display "insufficient data for reliable comparison." | DOCUMENTATION_ONLY |

### 11.4 Invariant Lifecycle

Following C20/C21/C22 precedent:

```text
DOCUMENTATION_ONLY → PROPOSED → ACTIVE → (never deleted, superseded only)
```

| State | Meaning |
| --- | --- |
| **DOCUMENTATION_ONLY** | Drafted for review; no enforcement; may be refined before activation |
| **PROPOSED** | Owning ADR accepted; activation trigger defined; contract test path specified |
| **ACTIVE** | Enforced by contract tests; violation is a Charter breach |
| **SUPERSEDED** | Replaced by a newer invariant; the superseding invariant must reference this one |

### 11.5 Activation Gates

All C23 invariants start as DOCUMENTATION_ONLY. Transition to PROPOSED requires:
1. C23 Charter ratification
2. Designated owning ADR for each invariant
3. Activation trigger defined (work package milestone, entity creation, service implementation)

Transition to ACTIVE requires:
1. Contract test path specified and test file exists
2. Owning ADR accepted
3. Activation trigger satisfied

---

## 12. Risks

### 12.1 Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | **C23 insights drift into execution directives** — OptimizationInsight language becomes increasingly directive over time, eroding the advisory-only boundary | Medium | Critical | ADR-C23-004 defines bright-line rules for allowed vs forbidden output language; contract tests verify output format |
| R2 | **C23 creates a parallel intelligence store** — OptimizationInsight accumulates enough structured data about prospects that it functionally becomes a competing intelligence authority to C21 | Medium | High | C23-INV-SEP-003 explicitly forbids this; entity design ensures OptimizationInsight is structurally distinct (recommendations, not evidence) |
| R3 | **Metric-driven automation creep** — PerformanceMetrics are gradually used as automated triggers ("if success rate < X, auto-pause provider") | Medium | High | C23-INV-MET-002 explicitly forbids metric-driven automation; any automation requires Charter amendment |
| R4 | **C23 leaks into C21 intelligence authority** — Feedback learning begins to reinterpret or override C21 qualification signals | Low | High | C23-INV-SEP-001 enforces read-only C21 consumption; C23 has no write access to C21 entities |
| R5 | **Performance data used to bypass ActionGate** — Operators use C23 performance data to justify skipping ActionGate review ("this template has 90% success rate, no need to gate") | Low | Critical | C22-INV-EX-001 and C22-INV-EX-002 remain binding regardless of C23 data; C23 Charter explicitly states it does not modify ActionGate requirements |
| R6 | **C23 entity scope creep** — Additional entities are proposed that blur the advisory/executive boundary | Medium | Medium | All new C23 entities require Charter amendment; forbidden entity types listed in §5.2 |
| R7 | **Sample size manipulation** — Metrics are computed on insufficient data to produce misleadingly confident recommendations | Medium | Medium | C23-INV-MET-001 enforces minimum sample size; confidence intervals required for all metrics |
| R8 | **C23 AI invocations bypass C20 governance** — C23 analytics invoke AI models without going through C20 AIJob/AIRequestLog | Low | High | C23-INV-ADV-002 mandates C20 routing; C20 D3 applies to all layers |
| R9 | **OptimizationInsight used as C22 execution input** — C22 services begin reading OptimizationInsight to influence execution decisions | Medium | High | Explicit Charter clause: C22 must not read C23 entities for execution decisions; C23 output is for human consumption only |

### 12.2 Risk Severity Matrix

```text
                    Likelihood
                    Low       Medium    High
Impact  Critical    R4, R8    R1, R5    —
        High        R9        R2, R3    —
        Medium      —         R6, R7    —
        Low         —         —         —
```

### 12.3 Key Risk Mitigations Summary

1. **Structural enforcement:** Advisory-only principle is enforced through entity design (no execute/approve fields), not policy alone
2. **Contract tests:** Every invariant has a defined contract test path before activation
3. **Charter amendment gate:** Any scope expansion, automation, or boundary change requires Charter amendment
4. **Human-in-the-loop as structural default:** Following C22 pattern, human mediation is the permanent default, not a temporary phase
5. **Read-only data access:** C23 has no write paths to C20/C21/C22/CRM entities — enforced at service and contract test levels

---

## 13. Charter Governance

### 13.1 Amendment Process

C23 Charter amendments require:

1. A dedicated Charter Amendment document
2. Impact analysis on existing C23 invariants
3. Boundary compliance check against C20 (FROZEN areas), C21 (FROZEN), and C22 (FROZEN)
4. Independent governance review
5. Updated invariant registry reflecting changes

### 13.2 Freeze Scope

Upon ratification, the following C23 elements are frozen:

| Element | Freeze Level |
| --- | --- |
| C23 layer definition and scope (§2) | HARD — requires Charter amendment |
| Advisory-only principle (§7) | HARD — requires Charter amendment |
| Forbidden entity types (§5.2) | HARD — requires Charter amendment |
| Entity ownership (§6) | SOFT — new entities may be added via ADR; forbidden field/type lists are HARD |
| WP scope (§4) | SOFT — WPs may be refined during implementation; non-scope exclusions are HARD |
| ADR roadmap (§10) | SOFT — ADRs may be added; the 5 required ADRs are HARD |
| Invariant categories (§11) | SOFT — invariants may be added via ADR; initial categories are the minimum set |

### 13.3 Ratification Prerequisites

Before C23 Charter ratification:

1. All 5 required ADRs must be drafted (ADR-C23-001 through ADR-C23-005)
2. C23 invariant registry must be drafted with all 17 initial invariants
3. Charter Review must be completed (following C22 Charter Review precedent)
4. Boundary compliance must be verified against C20, C21, and C22 frozen charters
5. All blocking conditions from Charter Review must be resolved

---

## 14. References

| Reference | Path |
| --- | --- |
| C20 ADR (Accepted) | `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` |
| C20 Invariant Registry | `docs/adr/C20_INVARIANT_REGISTRY.md` |
| C21 Charter (FROZEN) | `docs/PHASE3C21_CHARTER.md` |
| C21 ADR (Accepted) | `docs/adr/ADR-C21_AI_SALES_INTELLIGENCE_ARCHITECTURE.md` |
| C21 Invariant Registry | `docs/adr/C21_INVARIANT_REGISTRY.md` |
| C22 Charter Review | `docs/audit/PHASE3C22_CHARTER_REVIEW.md` |
| C22 Charter Amendment V1 | `docs/audit/PHASE3C22_CHARTER_AMENDMENT_V1.md` |
| C22 Invariant Registry (Draft) | `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md` |
| ADR-C22-001 | `docs/audit/ADR-C22-001_ProspectCandidate_Identity_Boundary.md` |
| ADR-C22-002 | `docs/audit/ADR-C22-002_Human_Approval_Gate.md` |
| ADR-C22-005 | `docs/audit/ADR-C22-005_RETRY_FAILURE_CLASSIFICATION.md` |
| ADR-C22-006 | `docs/audit/ADR-C22-006_CRM_LIFECYCLE_BOUNDARY.md` |
| ADR-C22-007 | `docs/audit/ADR-C22-007_ACTIONGATE_REENTRY_RULES.md` |
| Architecture Synthesis | `docs/audit/00_SYNTHESIS.md` |

---

## Appendix A: Cross-Layer Data Flow Map

```text
┌──────────────────────────────────────────────────────────────────┐
│ C23 — Optimization & Learning (ADVISORY ONLY)                    │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────┐             │
│  │ PerformanceMetric   │    │ OptimizationInsight  │             │
│  │ (immutable)         │    │ (immutable, human-   │             │
│  │                     │    │  reviewed status)    │             │
│  └────────┬────────────┘    └──────────┬───────────┘             │
│           │                            │                          │
│           │ reads                      │ reads                    │
│           ▼                            ▼                          │
│  ┌─────────────────────────────────────────────────┐             │
│  │        C23 Analytics & Learning Services         │             │
│  │  (read-only access to C20/C21/C22 data)          │             │
│  └──────┬──────────┬──────────┬────────────────────┘             │
│         │          │          │                                   │
│         │ reads    │ reads    │ reads                             │
│         ▼          ▼          ▼                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────┐          │
│  │ C20 Data │ │ C21 Data │ │ C22 Data                 │          │
│  │ AIJob    │ │ Evidence │ │ ExecutionLedger          │          │
│  │ AIReqLog │ │ Insight  │ │ ProspectRun              │          │
│  │          │ │ Feedback │ │ ActionGate decisions     │          │
│  │          │ │ Aggregate│ │ ReplyDetection           │          │
│  └──────────┘ └──────────┘ └──────────────────────────┘          │
│                                                                  │
│  ─── HARD BOUNDARY — C23 has NO write access below this line ─── │
│                                                                  │
│  C22: ProspectCandidate, ProspectRun, ActionGate,                │
│       ExecutionLedger, OutreachExecution (FROZEN)                │
│  C21: ResearchEvidence, AIQualificationInsight,                  │
│       HumanFeedback, IntelligenceAggregate (FROZEN)              │
│  C20: AIJob, AIRequestLog, PromptTemplate,                       │
│       ProviderCredential (ACTIVE)                                │
│  CRM: Lead, Account, Opportunity (CRM Core)                      │
│  Chitu: canonical_score (UNMODIFIABLE)                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Decision Boundary Examples

### B.1 Allowed C23 Operations

| Operation | Why Allowed |
| --- | --- |
| Compute reply rate by industry from ExecutionLedger + ReplyDetection data | Analytical — no mutation |
| Generate OptimizationInsight: "Template B has 40% higher reply rate for healthcare CTOs" | Advisory — states observation with evidence |
| Store PerformanceMetric: success_rate = 0.73 for provider X in March 2026 | Immutable point-in-time measurement |
| Read C21 HumanFeedback to correlate denial patterns with poor outcomes | Read-only consumption of C21 data |
| Present performance dashboard to human operator | Informational — no automated action |
| Suggest search strategy improvement based on historical performance | Advisory — human decides |

### B.2 Forbidden C23 Operations

| Operation | Why Forbidden | Violated Rule |
| --- | --- | --- |
| Auto-switch default search provider based on performance data | Executive action | C23-INV-ADV-001, C23-INV-ADV-003 |
| Modify ExecutionLedger to add analytical annotations | C22 mutation | C22-INV-EX-003, C23-INV-SEP-002 |
| Create ResearchEvidence based on C23 pattern analysis | C21 mutation | C22-INV-C21-002, C23-INV-SEP-001 |
| Auto-pause ProspectRun based on poor performance metrics | Execution intervention | C22-INV-EX-004, C23-INV-MET-002 |
| Generate output: "Approve all actions for ICP segment A" | Executive directive | C23-INV-ADV-001, C23-INV-ADV-003 |
| Write to canonical_score based on performance correlation | Chitu authority violation | C22-INV-CRM-004, CLAUDE.md |
| Auto-create Lead from high-performing ProspectCandidate | CRM boundary violation | C22-INV-CRM-001 |
| Hold provider credentials for analytics AI model invocations | Credential custody violation | C20 §5.2, C23-INV-ADV-002 |
| Generate OptimizationInsight referencing individual ProspectCandidate records | Per-prospect intelligence violation | C23-INV-PROV-003, C23-INV-SEP-004 |
| Generate output: "Prospect X is qualified — approve outreach" | Per-prospect qualification (C21 territory) | C23-INV-SEP-004 |
| Display C23 PerformanceMetric at ActionGate during approval review | ActionGate influence violation | C23-INV-SEP-005 |
| Present OptimizationInsight as ActionGate approval evidence | ActionGate evidence violation | C23-INV-SEP-005 |
| Display stale OptimizationInsight (sourcePeriodEnd > 180 days) without staleness warning | Data freshness violation | C23-INV-PROV-004 |
| Compute comparative metric (template A vs B) with n=8 per group and present as reliable | Sample size governance violation | C23-INV-MET-004 |
| Use PerformanceMetric value as condition in C22 AutomationRule definition | Metric-driven automation by indirection | C23-INV-MET-002 |

---

*Charter v1.1-draft — condition resolution applied (Amendment V1). All C23 invariants (22 total) are DOCUMENTATION_ONLY pending Charter ratification and ADR acceptance. This document authorizes no implementation, entity creation, metadata modification, code changes, commits, pushes, or tags.*
