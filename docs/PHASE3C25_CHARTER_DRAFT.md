# Phase3C25 Charter — AI Commercial Intelligence Layer

| Field | Value |
| --- | --- |
| Document Type | Phase Charter |
| Subject | C25 — AI Commercial Intelligence Layer |
| Status | DRAFT v2.1 — minor correction pass |
| Date | 2026-07-30 |
| Version | v2.1-draft |
| Baseline | `phase3c24-master-freeze` (`6dd784c`) |
| Predecessor | Phase3C24 Master Freeze (RATIFIED) |
| Depends On | C20 (ACTIVE), C21 (FROZEN), C22 (FROZEN), C23 (FROZEN), C24 (FROZEN) |
| Revision | Replaces v1.0-draft; v2.0→v2.1 corrections recorded in `docs/audit/PHASE3C25_CHARTER_REVISION_NOTES.md` |
| Implementation Authorization | **None** — governance specification only |

---

## 1. Executive Summary

### 1.1 What C25 Is

Phase3C25 defines the **AI Commercial Intelligence Layer** — the sixth architectural layer in the EspoCRM AI governance stack. C25 is the intelligence foundation of an AI Sales Operating System. It provides AI-assisted commercial understanding for human decision makers by consuming the full C20–C24 governance artifact chain as a unified, read-only intelligence surface.

C25 is **not** a complete AI Sales Operating System. It is the intelligence layer that sits above the complete C20–C24 governance foundation, assembling existing governed evidence into human-consumable commercial intelligence.

### 1.2 C25 Scope

C25 is responsible for:

- Commercial context understanding
- Outcome intelligence assembly
- AI-assisted commercial analysis
- Decision support for human operators
- Human-assisted interpretation of governed evidence

C25 is **not** responsible for:

- CRM replacement
- Commercial fact ownership
- Sales lifecycle authority
- Autonomous execution
- Automated strategy modification

### 1.3 The Governing Question

```text
How can CRM provide AI-assisted commercial intelligence
without owning CRM lifecycle decisions?
```

C25 answers this by being a **pure consumption and presentation layer**. It reads governed artifacts. It applies AI-assisted interpretation. It presents commercial understanding to human operators. It never owns, mutates, or replaces the artifacts it consumes, and it never crosses into CRM Core lifecycle authority.

### 1.4 Why C25 Exists

C20–C24 together govern the full chain from provider capability through revenue outcome. But no layer answers the integrative question: **"What does all of this evidence tell a human commercial operator, right now?"**

A human operator reviewing a commercial situation must currently assemble context across:
- C24 WP1: Has this reply been interpreted? What does it mean?
- C24 WP2: Is there an OpportunityCandidate? What state is it in?
- C24 WP3: What do the pipeline metrics say? What revenue insights exist?
- C23: What prospecting patterns led here?
- C22: What execution history preceded this?
- C21: What intelligence and qualification evidence exists?

C25 provides a unified, AI-assisted surface that:
- Assembles cross-artifact context into a coherent commercial picture
- Generates human-readable commercial briefs
- Answers analytical questions using governed evidence
- Supports — but never replaces — human commercial decisions

### 1.5 Architectural Position

```text
┌──────────────────────────────────────────────────────────────┐
│ CRM Core                                                     │
│   Account · Contact · Opportunity · Sales Stage · Forecast   │
│   ← Human-owned revenue lifecycle; commercial authority      │
├──────────────────────────────────────────────────────────────┤
│ C25 — AI Commercial Intelligence          ← THIS CHARTER     │
│   CommercialContext Assembly                                    │
│   AI Commercial Brief (Immutable Projection)                    │
│   AI Assistant (Read-Only Interface)                            │
│   Human Decision Workspace (Presentation Layer)                 │
│   ← Reads C20-C24; presents AI-assisted understanding        │
│   ← ADVISORY ONLY — no CRM lifecycle ownership               │
├──────────────────────────────────────────────────────────────┤
│ C24 — Revenue Operations Governance       ← FROZEN           │
│   RevenueInsight · PipelineMetric                              │
│   ReplySignal · OpportunityCandidate (lifecycle transitions)  │
│   ← Revenue outcome governance; human commercial decisions   │
├──────────────────────────────────────────────────────────────┤
│ C23 — AI Prospecting Optimization         ← FROZEN           │
│   OptimizationInsight · PerformanceMetric                     │
│   ← "Did prospecting work?" Optimization observation         │
├──────────────────────────────────────────────────────────────┤
│ C22 — Autonomous Prospecting Execution    ← FROZEN           │
│   ProspectCandidate · ProspectRun · ActionGate                │
│   ExecutionLedger · ReplyDetection                            │
│   ← Execution governance; human-gated approval               │
├──────────────────────────────────────────────────────────────┤
│ C21 — AI Intelligence Governance          ← FROZEN           │
│   ResearchEvidence · AIQualificationInsight                   │
│   HumanFeedback · IntelligenceAggregate                       │
│   ← Advisory intelligence; no execution authority            │
├──────────────────────────────────────────────────────────────┤
│ C20 — AI Platform Foundation              ← ACTIVE           │
│   AIJob · AIRequestLog · PromptTemplate                       │
│   ProviderCredential · ProviderRoute                          │
│   ← Provider abstraction; credential custody; cost accounting│
├──────────────────────────────────────────────────────────────┤
│ Chitu — External Intelligence Authority  ← UNMODIFIABLE      │
│   canonical_score · qualification · research · scoring       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. C25 Definition

### 2.1 Core Identity

```text
C25 = AI Commercial Intelligence Layer
```

C25 is the intelligence foundation of an AI Sales Operating System — not the complete operating system itself. It provides **AI-assisted commercial understanding** by consuming governed artifacts from C20, C21, C22, C23, and C24 as read-only evidence and presenting unified commercial intelligence to human operators.

### 2.2 What C25 Provides

| Capability | Description |
| --- | --- |
| **Unified Intelligence Surface** | A single read-only workspace assembling ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric, and upstream context into one coherent commercial view |
| **AI Commercial Brief** | Immutable projection artifact — human-readable commercial summaries synthesizing customer situation, commercial signals, risks, and suggested review points |
| **AI Assistant Interface** | Read-only analytical Q&A interface using governed revenue evidence to answer commercial pattern questions |
| **Human Decision Workspace** | Structured presentation layer where AI provides explanation, summarization, and analysis — and humans own approval, prioritization, and commercial action |

### 2.3 What C25 Does NOT Provide

| Not C25 | Owner | Rationale |
| --- | --- | --- |
| **CRM lifecycle ownership** | CRM Core | C25 reads CRM Core data for context; it does not create, modify, or transition CRM entities |
| **Sales execution authority** | C22 | C25 has no ActionGate, no send capability, no execution trigger |
| **Revenue forecast authority** | CRM Core / Human | C25 may analyze forecast context; it cannot create, commit, or approve a forecast |
| **Autonomous commercial decisions** | Human | C25 provides understanding; humans make commercial decisions |
| **Opportunity ownership** | CRM Core | C25 reads OpportunityCandidate and CRM Opportunity as context; it does not create or modify either |
| **Revenue commitment** | CRM Core / Human | C25 analyzes revenue patterns; it does not book, commit, or recognize revenue |
| **Provider execution** | C20 | C25 may route AI-assistance requests through C20 capability interfaces; it does not own provider resolution |
| **Intelligence generation** | C21 | C25 consumes C21 intelligence; it does not create ResearchEvidence, AIQualificationInsight, or qualification scores |
| **Prospecting optimization** | C23 | C25 consumes C23 optimization context; it does not create OptimizationInsight or PerformanceMetric |
| **Governance artifact mutation** | C24 | C25 reads C24 artifacts as evidence; it does not modify ReplySignal, OpportunityCandidate, RevenueInsight, or PipelineMetric |
| **Strategy modification** | C23 / Human | C25 analyzes commercial evidence; it does not modify prospecting strategies, execution policies, or operational configurations |

---

## 3. Ownership Boundary

### 3.1 Layer Ownership Definition

The C20–C25 architecture stack is governed by explicit, non-overlapping ownership. Each layer owns its artifacts exclusively. Cross-layer access is read-only by default.

#### CRM Core

CRM Core owns:

- Account
- Contact
- Opportunity
- Sales lifecycle
- Commercial authority
- Revenue decisions
- Forecast commitment

CRM Core is the canonical source of commercial truth. No C20–C25 layer may create, modify, or transition CRM Core entities except through explicit, human-initiated CRM Core operations.

#### C20 — AI Platform Foundation

C20 owns:

- AIJob — one unit of async capability work; one row per invocation attempt group
- AIRequestLog — append-only record of every provider invocation with cost
- PromptTemplate — versioned, immutable once referenced
- ProviderCredential — credential metadata and custody
- ProviderRoute — (capability, purpose) → provider + model
- ProviderHealth — scheduled health check results

#### C21 — AI Intelligence Governance

C21 governs and extends governance for intelligence evidence. Key artifacts:

- ResearchEvidence — research artifact store (originates from Phase3C07; C21 governs and extends governance for it)
- AIQualificationInsight — advisory qualification interpretation
- HumanFeedback — structured human evaluation of intelligence
- IntelligenceAggregate — aggregated intelligence context

**Important:** ResearchEvidence originated in Phase3C07. C21 does not claim to have created it. C21 governs and extends governance for ResearchEvidence as part of its intelligence governance responsibility.

#### C22 — Autonomous Prospecting Execution Governance

C22 owns:

- ProspectCandidate — execution identity (not Lead, not Opportunity)
- ProspectRun — execution container (not an AI reasoning object)
- ActionGate — sole execution authorization point
- ExecutionLedger — append-only execution record
- ReplyDetection — technical reply detection (not business interpretation)
- OutreachExecution — governed provider-mediated outreach

#### C23 — AI Prospecting Optimization & Learning Governance

C23 owns:

- OptimizationInsight — aggregate advisory recommendations about prospecting strategy
- PerformanceMetric — point-in-time acquisition-effectiveness measurements
- FeedbackLearningObservation — structured learning from feedback patterns

C23's domain is optimization observation: "Did prospecting work?" C23 does not own commercial outcome analysis.

#### C24 — Revenue Operations Governance

C24 owns:

- ReplySignal — business interpretation of reply evidence (advisory, not execution)
- OpportunityCandidate — governed commercial consideration record with lifecycle transitions (IDENTIFIED → REVIEW_PENDING → ACCEPTED → ACTIVE → WON/LOST)
- RevenueInsight — aggregate commercial analysis, pipeline observation, revenue reporting
- PipelineMetric — individual pipeline measurement with provenance

C24 owns the lifecycle transitions for OpportunityCandidate. Every transition after IDENTIFIED requires an authenticated authorized human and creates an immutable state-transition record.

#### C25 — AI Commercial Intelligence Layer

C25 owns **only**:

- **CommercialContext assembly** — runtime-assembled read-only view aggregating C20–C24 evidence for a given commercial context
- **AI Commercial Brief** — immutable projection artifact (not a business authority)
- **Read-only AI Assistant interface** — governed analytical Q&A capability
- **Human Decision Workspace** — presentation layer for human commercial decision support

C25 owns presentation and interpretation. It owns no business facts, no lifecycle, no measurements, and no execution.

### 3.2 C25 Does NOT Own

| Layer | Artifact | C25 Relationship |
| --- | --- | --- |
| C20 | AIJob, AIRequestLog, PromptTemplate, ProviderCredential, ProviderRoute | Read-only cost/provenance context; no provider, credential, or runtime ownership |
| C21 | ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate | Read-only intelligence context; no qualification or scoring authority |
| C22 | ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, ReplyDetection | Read-only execution history; no execution or approval authority |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only optimization context; no metric redefinition or learning authority |
| C24 WP1 | ReplySignal | Read-only interpretive evidence; no signal lifecycle mutation |
| C24 WP2 | OpportunityCandidate | Read-only governance context; no candidate state or lifecycle transition |
| C24 WP3 | RevenueInsight, PipelineMetric | Read-only analytical evidence; no insight or metric mutation |
| CRM Core | Account, Contact, Opportunity, Sales Stage, Forecast, Revenue | Read-only commercial context; no CRM lifecycle mutation |

### 3.3 Layer Ownership Matrix

| Layer | Owns | C25 Permitted Relationship | C25 Prohibition |
| --- | --- | --- | --- |
| C20 | Provider contracts, credentials, AIJob, AIRequestLog, AI runtime, routing, egress | Read-only cost/provenance context; future AI-assistance model invocation routed through C20 capability interfaces | Direct provider, credential, SDK, or transport ownership |
| C21 | Intelligence governance; governs and extends governance for ResearchEvidence | Read-only intelligence context for commercial picture assembly | Qualification scoring, ranking, intelligence replacement, mutation |
| C22 | ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, ReplyDetection, OutreachExecution | Read-only execution history for commercial provenance tracing | Triggering execution, influencing ActionGate, mutation, auto-send |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only prospecting effectiveness context | Redefining optimization metrics or parallel optimization authority |
| C24 | RevenueInsight, PipelineMetric, ReplySignal, OpportunityCandidate lifecycle transitions | Read-only evidence for commercial intelligence assembly | Artifact mutation, lifecycle transition, recomputation |
| CRM Core | Account, Contact, Opportunity, Sales Stage, Forecast, Commercial authority | Read-only commercial context; human-directed action outside C25 | Automatic create, move, close, or commit lifecycle records |

---

## 4. CommercialContext Read Model

### 4.1 Definition

`CommercialContext` is a **read model** — not a business entity. It is a runtime-assembled, read-only view that aggregates evidence from the full C20–C24 chain for a given commercial situation.

### 4.2 Default Behavior

```text
CommercialContext = runtime assembled readonly view
```

CommercialContext is assembled at request time. It is not persisted as an independent governance record. It has no lifecycle, no state machine, and no mutation path.

### 4.3 Source Artifacts

CommercialContext assembles evidence from:

- ResearchEvidence (C21 — governed intelligence context)
- RevenueInsight (C24 WP3 — aggregate commercial analysis)
- PipelineMetric (C24 WP3 — individual pipeline measurements)
- ReplySignal (C24 WP1 — interpreted reply evidence)
- Execution results (C22 — execution history for provenance)
- CRM Core facts (Account, Contact, Opportunity, Sales Stage — read-only)

### 4.4 Structural Prohibitions

`CommercialContext` MUST NOT become:

- A new business-fact store (CRM Core owns business facts)
- A new scoring system (Chitu owns canonical_score; C21 governs qualification)
- A new priority authority (humans own prioritization)
- A new lifecycle system (CRM Core and C24 own their respective lifecycles)
- A replacement for any C20–C24 governance artifact

### 4.5 Caching Governance

If future implementation caches an assembled CommercialContext for performance:

**Must preserve:**

- Source artifact references (entity type + ID for every assembled record)
- Assembly version (identifying the assembly logic)
- Generated timestamp
- Freshness metadata (staleness status of each source artifact)

**Must not:**

- Become a canonical source independent of its source artifacts
- Survive deletion of its source artifacts as an intact record
- Be writable through any C25 or external service path

**Deletion rule:** Deleting a cached CommercialContext MUST NOT lose any business fact. All facts reside in their source artifacts (C20–C24, CRM Core). The CommercialContext is a projection — deleting a projection does not delete the facts it projected.

---

## 5. Work Package Structure

### 5.1 WP1 — Commercial Intelligence Workspace

**Purpose:** Unified read-only intelligence surface.

**Consumes:**
- ReplySignal (C24 WP1) — interpreted reply evidence
- OpportunityCandidate (C24 WP2) — governance state, review context, transition audit
- RevenueInsight (C24 WP3) — aggregate commercial analysis
- PipelineMetric (C24 WP3) — individual pipeline measurements
- Upstream C20–C23 context as available

**Provides:**
- Single assembled view of all C24 governance evidence for a given commercial context
- Cross-artifact provenance tracing (ReplySignal → OpportunityCandidate → RevenueInsight → PipelineMetric)
- Freshness indicators across all consumed artifacts
- Advisory designation display on all presented evidence

**Does NOT:**
- Mutate any source artifact
- Create new governance records
- Trigger any workflow or automation
- Replace any existing C20–C24 presentation surface

**Governing rule:** The workspace is a lens, not a ledger. It reads and presents; it never writes.

### 5.2 WP2 — AI Commercial Brief

**Purpose:** Generate human-readable commercial summaries as immutable projection artifacts.

**Definition:** An AI Commercial Brief is an **immutable projection artifact**. It is not a business authority. It is a human-reviewable, AI-generated summary of commercial evidence at a point in time.

**Consumes:**
- Assembled workspace context (WP1)
- ReplySignal interpretation and confidence
- OpportunityCandidate review context and commercial signal summary
- RevenueInsight analytical narratives
- PipelineMetric values and trends
- C21 intelligence context (read-only)
- C22 execution history (read-only)

**Produces:**
- **Customer Situation** — synthesized context about the prospect, their organization, and relevant intelligence
- **Commercial Signals** — interpreted evidence of commercial interest, intent, or opportunity
- **Risk Factors** — identified risks, gaps in evidence, or areas requiring human attention
- **Suggested Review Points** — advisory prompts for human commercial evaluation

**Mandatory Fields:**

Every AI Commercial Brief MUST record:

| Field | Purpose |
| --- | --- |
| Source record IDs | Entity type and ID for every source artifact referenced |
| Reporting period | The time window the brief covers |
| Generated timestamp | When the brief was produced |
| Generation version | Version of the generation logic/prompt |
| Source AIJob ID | The C20 AIJob that produced this generation |
| Source AIRequestLog IDs | The C20 AIRequestLog records for provider invocations |
| Provider | The AI provider used (via C20 routing) |
| Model | The model used for generation |
| Advisory designation | Mandatory label: "AI-generated commercial summary — for human review only. Not a forecast, commitment, or decision." |

**Immutability and Superseding:**

- Once generated, a brief is immutable — no field may be updated
- A changed interpretation requires a new superseding brief
- The superseding brief MUST reference the brief it supersedes
- All brief versions are preserved for audit

**Deletion Rule:**

Deleting all AI Commercial Briefs MUST NOT lose any business fact. Briefs are projections of governed evidence. The evidence resides in C20–C24 and CRM Core artifacts. Deleting a brief deletes the projection — it does not delete the facts projected.

**Constraints:**

- Every brief MUST carry the mandatory advisory designation
- Briefs MUST reference source artifacts with provenance
- Briefs MUST declare generation timestamp and evidence freshness
- Briefs MUST NOT contain execution directives, CRM mutation commands, or forecast commitments
- Briefs MUST NOT phrase suggestions as decisions ("Consider reviewing..." not "The pipeline should be...")

**Does NOT own:**

- Opportunity authority (CRM Core owns this)
- Lifecycle authority (C24 owns OpportunityCandidate lifecycle)
- Priority authority (human owns prioritization)
- Revenue truth (CRM Core and C24 artifacts own this)

**Field Authority Constraints:**

The AI Commercial Brief is an **immutable projection artifact** — not a commercial authority. Its fields MUST NOT constitute a second source of business facts.

**Forbidden authority fields.** The Brief MUST NOT contain fields that assert:

| Forbidden Field Type | Rationale | Example (FORBIDDEN) |
| --- | --- | --- |
| **Priority authority** | Human owns prioritization; Brief does not rank | `OpportunityPriority = High` |
| **Ranking authority** | Human owns ranking; Brief does not order | `Rank = 1`, `Score = 95` |
| **Lifecycle authority** | C24 owns OpportunityCandidate lifecycle | `Recommended lifecycle stage: Qualified` |
| **Opportunity stage authority** | CRM Core owns Opportunity stages | `Suggested Stage: Negotiation` |
| **Revenue truth authority** | CRM Core and C24 own revenue facts | `Forecast = $50K`, `Commit = Close in Q3` |

**Permitted presentation forms.** When the Brief presents information that a reader might interpret as authoritative, it MUST use observation, analysis, or explanation forms:

| Permitted Form | Example (PERMITTED) |
| --- | --- |
| **Observation** | `Observed market signal: High` (describes evidence, not a priority decision) |
| **Analysis** | `AI analysis: ReplySignal confidence and engagement velocity suggest commercial interest` |
| **Explanation** | `AI explanation: Historical pattern indicates stronger engagement when 3+ ReplySignals are detected within 14 days` |
| **Review point** | `Consider reviewing: This candidate has accumulated signals across multiple channels. Human priority assessment recommended.` |

**Governance rule:** The Brief describes what the evidence shows. It does not declare what the business should do. Every field that could be read as a decision carries an explicit observation/analysis/explanation label, never an authority label.

### 5.3 WP3 — Revenue Analyst Assistant

**Purpose:** AI-assisted analytical Q&A using governed revenue evidence through a read-only interface.

**Consumes:**
- RevenueInsight records (C24 WP3)
- PipelineMetric records (C24 WP3)
- OpportunityCandidate outcome data (C24 WP2 — read-only)
- CRM pipeline and revenue data (CRM Core — read-only)

**Answers questions like:**
- "Why did conversion decline in Q2?"
- "What changed in pipeline quality between periods?"
- "What commercial patterns exist across ICP segments?"
- "How does velocity compare to prior periods?"
- "What does the win/loss pattern suggest?"

**Constraints:**
- Every response MUST carry an explicit advisory designation: "AI-generated analytical response — for human review only. Not a forecast, commitment, or decision."
- Responses MUST reference source evidence with provenance
- Responses MUST declare analytical limitations
- Responses MUST NOT create, modify, or recommend CRM lifecycle actions
- Responses MUST NOT generate forecasts, commit revenue, or authorize commercial action
- Responses MUST NOT answer questions outside the C24 commercial analytics domain
- If asked a question requiring CRM mutation ("What Opportunity should I close?"), the assistant MUST decline and explain the boundary

**Does NOT:**
- Create forecast or pipeline commitments
- Modify CRM Opportunities
- Trigger execution or workflow
- Generate revenue recognition entries
- Replace human analytical judgment

### 5.4 WP4 — Human Decision Workspace

**Purpose:** Presentation layer for structured human commercial decision support.

**C25 is responsible for:**
- Presenting unified commercial context (WP1)
- Presenting AI-generated explanations and analysis
- Presenting AI Commercial Briefs (WP2)
- Presenting analytical Q&A responses (WP3)
- Collecting human intent (review decisions, action intentions)

**C25 is NOT responsible for:**
- Modifying OpportunityCandidate state
- Creating a second lifecycle parallel to C24
- Bypassing C24 lifecycle governance
- Directly mutating C24-owned data (direct database/entity update)

**The Correct Flow:**

```text
C25 Workspace
        ↓  (present context, brief, analysis; collect human intent)
Human Decision
        ↓  (human reviews, decides action)
Authorized C24 Transition Service
        ↓  (governed transition via C24's service boundary)
Lifecycle mutation + immutable audit record
```

**Permitted:** C25 Human Decision Workspace may invoke authorized C24 transition services through C24's governed service entry points. The human decision collected in the C25 workspace triggers a governed transition through C24's own service boundary.

**Forbidden:** C25 MUST NOT bypass C24 lifecycle governance, directly mutate OpportunityCandidate lifecycle state, or perform direct database/entity updates on any C24-owned artifact. All lifecycle mutation goes through C24's authorized transition service with immutable audit.

```text
FORBIDDEN:
  C25 Service → Direct database/entity update on C24 artifacts

PERMITTED:
  C25 Workspace → Human Decision → Authorized C24 Transition Service → Lifecycle mutation + immutable audit
```

**Human owns:**
- Commercial interpretation
- Opportunity prioritization
- Sales action decisions
- Revenue decisions
- Forecast commitment
- Pipeline strategy
- Brief acceptance/rejection

**AI provides:**
- Explanation of commercial evidence
- Summarization of cross-artifact context
- Analysis of patterns and trends
- Recommendation phrased as advisory observation

**AI is forbidden from:**
- Executing any commercial action
- Approving any decision
- Committing revenue or forecast
- Creating or modifying CRM entities
- Triggering any execution or workflow

**Workspace structure:**

```text
┌─────────────────────────────────────────────────────────┐
│ HUMAN DECISION WORKSPACE (C25 Presentation)              │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐│
│  │ AI COMMERCIAL BRIEF  │  │ AI ASSISTANT INTERFACE     ││
│  │ (WP2)                │  │ (WP3)                      ││
│  │                      │  │                            ││
│  │ Customer situation   │  │ Analytical Q&A             ││
│  │ Commercial signals   │  │ Pattern explanation        ││
│  │ Risk factors         │  │ Trend analysis             ││
│  │ Review points        │  │ Evidence references        ││
│  └─────────────────────┘  └────────────────────────────┘│
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │ UNIFIED INTELLIGENCE SURFACE (WP1)                   ││
│  │                                                      ││
│  │ ReplySignal ──→ OpportunityCandidate ──→ RevenueData ││
│  │ PipelineMetric ──→ RevenueInsight ──→ CRM Context    ││
│  │ All artifacts: provenance, freshness, advisory labels ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  ─── HUMAN DECISION BOUNDARY ───                         │
│                                                          │
│  ↓ Human intent collected; transition initiated          │
│    through C24 Transition Service (outside C25)          │
└──────────────────────────────────────────────────────────┘
```

---

## 6. AI Assistant Security Boundary

### 6.1 Interface Definition

The C25 AI Assistant is a **read-only interface** to governed commercial evidence. Its authority is structurally bounded — not prompt-bounded.

### 6.2 Permitted Operations

| Operation | Permitted | Description |
| --- | --- | --- |
| **Query** | ✅ | Read governed evidence by defined query patterns |
| **Read** | ✅ | Access C20–C24 and CRM Core entities as read-only |
| **Aggregate** | ✅ | Compute summaries over read evidence |
| **Compare** | ✅ | Compare evidence across periods, segments, patterns |
| **Explain** | ✅ | Explain patterns, trends, and relationships in evidence |
| **Summarize** | ✅ | Generate human-readable summaries of evidence |

### 6.3 Forbidden Operations

| Operation | Forbidden | Enforcement |
| --- | --- | --- |
| **Create** | ❌ | No entity creation path; enforced at service layer |
| **Update** | ❌ | No entity mutation path; enforced at service layer |
| **Delete** | ❌ | No entity deletion path; enforced at service layer |
| **Send email** | ❌ | No email dispatch capability; enforced at tool capability level |
| **Trigger outreach** | ❌ | No outreach execution path; enforced at tool capability level |
| **Change lifecycle** | ❌ | No lifecycle mutation path; enforced at service layer |
| **Access credentials** | ❌ | No credential read capability; enforced at service layer |
| **Direct provider calls** | ❌ | No provider SDK, HTTP, or transport ownership |

### 6.4 Enforcement Architecture

The security boundary MUST be enforced by:

1. **Tool capability** — The AI Assistant's available tools are a structural allow-list. Forbidden operations have no corresponding tool.
2. **Service layer** — C25 services have zero write paths to C20/C21/C22/C23/C24/CRM Core entities. This is enforced by contract tests, not by convention.
3. **Not by prompt** — The boundary is not enforced by system prompts, refusal rules, or language constraints. Those are defense-in-depth, not the primary enforcement.

### 6.5 Domain Boundary Refusal

If the AI Assistant receives a request outside the C24 commercial analytics domain or requesting a forbidden operation, it MUST decline and explain the boundary. This refusal is a functional requirement, not a prompt suggestion — the service layer must recognize out-of-domain requests and refuse them before processing.

### 6.6 Output Provenance Requirements

Every AI Assistant analytical response that presents findings, explanations, or conclusions MUST support source traceability. Ungrounded commercial conclusions are forbidden.

**Provenance chain per response.** When the AI Assistant returns an analysis or explanation (e.g., "Australia distributor segment shows higher response efficiency"), the response MUST be traceable to specific governed evidence:

| Provenance Element | Description | Example |
| --- | --- | --- |
| **Source record IDs** | Entity type and ID for every source artifact the analysis is based on | `ReplySignal:abc123, RevenueInsight:def456` |
| **Source artifact IDs** | Specific C20–C24 artifact references | `CampaignOutcome:campaign-aus-2026Q2` |
| **Reporting period** | The time window the analysis covers | `2026-Q2 (2026-04-01 to 2026-06-30)` |
| **Generation timestamp** | When the response was generated | `2026-07-30T14:30:00Z` |
| **AIJob ID** | The C20 AIJob that produced this analytical response | `C20 AIJob:job-xyz789` |
| **AIRequestLog references** | The C20 AIRequestLog records for provider invocations | `AIRequestLog:log-001, log-002` |

**Traceability requirement.** A human reviewer must be able to trace any analytical claim back to its source evidence:

```text
Assistant response: "Australia distributor segment shows higher response efficiency"

Must be traceable to:
  → Campaign Outcome records (CRM Core)
  → ReplySignal records (C24 WP1)
  → RevenueInsight records (C24 WP3)
  → PipelineMetric records (C24 WP3)
```

**Forbidden: ungrounded conclusions.** The Assistant MUST NOT produce commercial conclusions without source evidence:

| Forbidden | Permitted |
| --- | --- |
| "This deal will close." (no source, predictive claim) | "Based on ReplySignal confidence and engagement velocity in records X, Y, Z, this candidate shows stronger-than-average commercial engagement." |
| "Segment A is better than Segment B." (no period, no source) | "In 2026-Q2, Segment A candidates (n=45) showed 23% higher REPLY_SIGNAL conversion than Segment B candidates (n=38), based on RevenueInsight records R1, R2 and PipelineMetric records P1–P10." |

**Provenance survival.** The provenance chain MUST survive deletion of the Assistant response. Provenance records in C20 AIJob/AIRequestLog and source artifacts in C20–C24/CRM Core are independent of C25 Assistant response lifecycle.

---

## 7. C20 AI Provenance

### 7.1 AIJob/AIRequestLog Model

The correct C20 provenance model is:

```text
Logical AI task
    ↓
AIJob (one unit of async capability work; one row per invocation attempt group)
    ↓
One or more AIRequestLog records (one row per provider invocation)
```

An AIJob represents a logical task (e.g., "generate commercial brief for candidate X"). An AIJob may produce multiple AIRequestLog records — one per provider invocation. This is the model defined in C20 ADR §5.4 and §7.

**Incorrect model (rejected):** "Every model call creates one AIJob." A single logical task may involve multiple provider calls (e.g., summarization followed by analysis). The AIJob groups related invocations; AIRequestLog records each individual provider call.

### 7.2 C25 Provenance Requirements

Every AI-generated artifact produced by C25 MUST record:

| Field | Source | Purpose |
| --- | --- | --- |
| `sourceAIJobId` | C20 AIJob ID | Links the generation to its logical task |
| `sourceAIRequestLogId` | C20 AIRequestLog ID(s) | Links the generation to its provider invocation(s) |
| `provider` | C20 ProviderRoute → ProviderCredential | Identifies the AI provider used |
| `model` | C20 ProviderRoute | Identifies the model used |
| `generationVersion` | C25 generation logic version | Identifies the generation logic/prompt version |

These provenance requirements apply to:
- AI Commercial Briefs (WP2)
- AI Assistant analytical responses (WP3)
- Any future C25 AI-generated output

This provenance chain enables:
- Audit: every AI-generated conclusion traces to a specific provider invocation
- Cost attribution: token/cost through C20 cost accounting
- Reproducibility: same inputs + same model + same generation version = same output
- Explainability: why was this conclusion reached at this time?

---

## 8. Generation Trigger Policy

### 8.1 Phase 1: Human-Initiated Only

C25 Phase 1 uses **human-initiated generation only**. AI generation is triggered by an explicit human action:

- User clicks "Generate Commercial Brief" → brief generation begins
- User submits an analytical question → assistant processes and responds
- User opens a commercial workspace → context is assembled on-demand

### 8.2 Forbidden Triggers (Phase 1)

The following generation triggers are **forbidden by default** and require independent governance before activation:

| Forbidden Trigger | Rationale |
| --- | --- |
| **Scheduler** | No cron-based or periodic brief generation |
| **Worker** | No background job queue for autonomous generation |
| **Webhook** | No event-driven generation from external signals |
| **Background autonomous** | No unattended generation of any C25 artifact |
| **Event listener** | No entity-save or state-change trigger for brief generation |

### 8.3 Future Automation

Any future proposal to enable scheduled, event-driven, or autonomous generation MUST:

1. Be proposed in a dedicated C25 Charter Amendment
2. Be ratified through an independent ADR
3. Update C25 invariants to reflect the new trigger governance
4. Pass independent governance review against C20–C24 boundaries
5. Maintain the human review gate on all generated output

**Zero automated generation is the structural default.** Deviation requires explicit, governed authorization.

---

## 9. Cross-Layer Relationship Model

### 9.1 C20 Boundary — Provider and AI Runtime

| Rule | Compliance |
| --- | --- |
| C25 has no provider, credential, vendor, SDK, HTTP, or AI runtime ownership | ✅ Structural |
| Any C25 function requiring AI model invocation MUST route through C20 capability interfaces | ✅ C20 remains sole provider boundary |
| C25 MUST NOT hold credentials, invoke a provider directly, or bypass C20 routing | ✅ |
| C25 AI-generated artifacts MUST record sourceAIJobId, sourceAIRequestLogId, provider, model, and generationVersion | ✅ See §7.2 |
| C25 may reference C20 AIJob and AIRequestLog as read-only provenance context | ✅ Read-only |

### 9.2 C21 Boundary — Intelligence Ownership

| Rule | Compliance |
| --- | --- |
| C21 governs and extends governance for intelligence evidence, including ResearchEvidence (originated Phase3C07) | ✅ ResearchEvidence lineage respected |
| C25 may consume ResearchEvidence, AIQualificationInsight, HumanFeedback, and IntelligenceAggregate only as read-only context | ✅ Read-only |
| C25 MUST NOT create, modify, delete, reinterpret, or create a parallel authority for C21 intelligence or qualification | ✅ |
| C25 MUST NOT score, rank, or qualify prospects | ✅ |

### 9.3 C22 Boundary — Execution Ownership

| Rule | Compliance |
| --- | --- |
| C22 is the sole owner of execution governance | ✅ |
| C25 may consume C22 outcomes only as read-only execution history for commercial provenance | ✅ Read-only |
| C25 MUST NOT bypass or influence ActionGate, start or alter a ProspectRun, mutate ExecutionLedger, trigger outreach, or grant execution permission | ✅ |
| C25 data MUST NOT appear at ActionGate (extends C23-INV-SEP-005 and C24 ActionGate isolation) | ✅ |

### 9.4 C23 Boundary — Optimization Ownership

| Rule | Compliance |
| --- | --- |
| C23 is the sole owner of prospecting optimization and learning | ✅ |
| C25 may consume OptimizationInsight and PerformanceMetric only as read-only context | ✅ Read-only |
| C25 MUST NOT redefine, overwrite, or create a competing version of C23 optimization metrics | ✅ |
| C25 MUST NOT generate optimization recommendations that replace or compete with C23 OptimizationInsight | ✅ |

### 9.5 C24 Boundary — Governance Artifact Ownership

| Rule | Compliance |
| --- | --- |
| C24 is the sole owner of ReplySignal, OpportunityCandidate (lifecycle transitions), RevenueInsight, and PipelineMetric | ✅ |
| C25 may consume all C24 artifacts as read-only evidence for commercial intelligence assembly | ✅ Read-only |
| C25 MUST NOT mutate any C24 artifact — no status change, field update, transition execution, or lifecycle mutation | ✅ |
| C25 MUST NOT create a replacement or parallel version of any C24 artifact | ✅ |
| C25 MUST preserve all C24 provenance, freshness, and advisory designations when presenting artifacts | ✅ |
| C25 MUST NOT bypass C24 lifecycle governance or directly mutate C24-owned data — all OpportunityCandidate lifecycle transitions go through C24's authorized transition service via governed service entry points | ✅ |

### 9.6 CRM Core Boundary — Lifecycle Ownership

| Rule | Compliance |
| --- | --- |
| CRM Core is the sole owner of Account, Contact, Opportunity, Sales Stage, Forecast, and Revenue lifecycle | ✅ |
| C25 may consume CRM Core data as read-only commercial context | ✅ Read-only |
| C25 MUST NOT create, modify, close, reopen, stage-transition, or forecast-commit any CRM Core entity | ✅ |
| C25 MUST NOT provide a "Promote to Opportunity" or equivalent CRM-mutation proxy | ✅ |
| No C25 service, response, brief, or workspace may call `createEntity`, `saveEntity`, or any lifecycle method on a CRM Core entity | ✅ |

---

## 10. Human Governance Model

### 10.1 The Principle

C25 extends the C24 human governance chain with an **intelligence consumption layer**. Humans remain the sole authority for all commercial decisions. C25 AI assistance informs human judgment — it never replaces it.

### 10.2 Human-Owned Decisions

The following decisions are **exclusively human-owned** and must never be automated within C25 or any downstream layer:

| Decision Domain | Human Authority | C25 Role |
| --- | --- | --- |
| **Commercial interpretation** | Human interprets what commercial evidence means | C25 assembles and presents evidence; AI may suggest interpretations for human review |
| **Opportunity prioritization** | Human decides which opportunities to pursue and in what order | C25 provides cross-artifact context, signal strength indicators, and pattern comparison |
| **Sales action** | Human decides what sales action to take | C25 provides customer situation summary, risk factors, and suggested review points |
| **Revenue decision** | Human decides revenue-related actions | C25 provides RevenueInsight narratives, PipelineMetric trends, and analytical Q&A responses |
| **Forecast commitment** | Human commits forecast in CRM Core | C25 provides pipeline context, trend analysis, and pattern evidence |
| **Pipeline strategy** | Human decides pipeline management strategy | C25 provides conversion analysis, velocity trends, and ICP performance comparisons |
| **Brief acceptance** | Human reviews and accepts/rejects AI Commercial Brief as valid decision-support material | C25 generates the brief with provenance, freshness, and advisory designation |

### 10.3 AI Permissions and Restrictions

| AI Capability | Permitted? | Constraint |
| --- | --- | --- |
| **Summarize** commercial evidence | ✅ Permitted | Must reference sources; must declare advisory status |
| **Explain** patterns and trends | ✅ Permitted | Must declare limitations; must not phrase as directive |
| **Analyze** commercial data | ✅ Permitted | Must use governed evidence only; must declare methodology |
| **Recommend** review points | ✅ Permitted (advisory) | Must be phrased as observation, not command |
| **Execute** commercial action | ❌ FORBIDDEN | Zero automation is the structural default |
| **Approve** any decision | ❌ FORBIDDEN | Approval is exclusively human |
| **Commit** revenue or forecast | ❌ FORBIDDEN | Commitment is exclusively human in CRM Core |
| **Create or modify** CRM entities | ❌ FORBIDDEN | CRM Core boundary is structural |
| **Trigger** execution or workflow | ❌ FORBIDDEN | C22 owns all execution initiation |

### 10.4 The Extended Human Governance Chain

C25 extends the C24 human governance chain with intelligence consumption gates:

```text
Gate 1 (C24 WP1):  Human reviews ReplySignal → CONVERTED or DISMISSED
Gate 2 (C24 WP2):  Human creates OpportunityCandidate → IDENTIFIED
Gate 3 (C24 WP2):  Human accepts for commercial consideration → ACCEPTED
Gate 4 (C24 WP2):  Human confirms active follow-up → ACTIVE
Gate 5 (CRM Core): Human creates CRM Opportunity (outside C24/C25)
Gate 6 (C24 WP2):  Human records commercial outcome → WON or LOST
Gate 7 (C24 WP3):  Human reviews RevenueInsight → ACCEPTED or REJECTED
Gate 8 (C25 WP4):  Human reviews AI Commercial Brief → ACCEPTED or DISMISSED
                    Decision: "Does this AI-generated commercial summary accurately
                    reflect the situation?"
Gate 9 (CRM Core): Human acts on commercial intelligence (outside C25)
                    Decision: "What action, if any, should we take?"
```

**Gates 8 and 9 are separate, explicit human decisions.** Gate 8 accepts the AI-generated intelligence as valid decision-support material. Gate 9 decides what to do about it — and that decision happens in CRM Core, outside C25 governance.

---

## 11. C25 Native Invariants

The following invariants are proposed for C25. They extend the existing governance invariant chain (C20 → C21 → C22 → C23 → C24) with C25-specific intelligence consumption rules. Upon C25 charter ratification, these invariants will be registered with `DOCUMENTATION_ONLY` status, transitioning to `ACTIVE` upon implementation.

### 11.1 C25-INV-OWN-001 — Commercial Intelligence Ownership Boundary

| Field | Definition |
| --- | --- |
| **ID** | `C25-INV-OWN-001` |
| **Name** | Commercial Intelligence Ownership Boundary |
| **Category** | Ownership Boundary |
| **Purpose** | Define the exclusive ownership scope of C25 within the C20–C25 architecture stack. |
| **Rule** | C25 exclusively owns CommercialContext assembly, AI Commercial Brief (immutable projection), the read-only AI Assistant interface, and the Human Decision Workspace presentation layer. C25 MUST NOT own any C20/C21/C22/C23/C24 artifact, any CRM Core entity, or any business fact. C25 owns presentation and interpretation — not business truth. |
| **Enforcement expectation** | Future C25 entity definitions and service contracts must be bounded to the four ownership areas. Contract tests must verify zero C25 write paths to C20/C21/C22/C23/C24/CRM Core entities. |
| **Relation to previous invariants** | Extends C24-INV-SEP-001 (C24 reads C23 as read-only), C23-INV-OWN-001 (C23 owns OptimizationInsight/PerformanceMetric), C22-INV-ID-001 (ProspectCandidate ownership), and C21 ownership of intelligence governance. C25 is the sixth layer in the ownership chain and follows the same read-only cross-layer consumption pattern. |
| **Status** | PROPOSED |

### 11.2 C25-INV-ADV-001 — Advisory Output Non-Authority

| Field | Definition |
| --- | --- |
| **ID** | `C25-INV-ADV-001` |
| **Name** | Advisory Output Non-Authority |
| **Category** | Advisory Boundary |
| **Purpose** | Ensure every C25 intelligence output is structurally advisory and cannot be misinterpreted as operational authority. |
| **Rule** | Every C25 intelligence output — AI Commercial Brief, AI Assistant response, workspace assembly, or decision-support material — is an advisory interpretation only. It MUST NOT act as an execution command, approval directive, CRM mutation instruction, forecast commitment, opportunity-creation trigger, or workflow trigger. Every C25 output MUST carry an explicit advisory designation. C25 outputs are projections of governed evidence — they carry no independent business authority. |
| **Enforcement expectation** | Future C25 output schemas and service contracts must exclude command, approval, automation, CRM-write, and forecast-commitment fields. Every generated brief, analytical response, and workspace view must carry mandatory advisory designation. Contract tests must verify zero paths from C25 output to execution or lifecycle mutation. |
| **Relation to previous invariants** | Extends C24-INV-ADV-001 (Advisory Revenue Artifacts Only — ReplySignal, RevenueInsight, PipelineMetric are advisory), C24-INV-REV-001 (RevenueInsight Advisory-Only Boundary), and C23-INV-ADV-001 (No C23 AI output may be interpreted as an execution/approval/decision directive). C25 applies the advisory-only principle to AI-generated commercial intelligence outputs. |
| **Status** | PROPOSED |

### 11.3 C25-INV-HG-001 — Human Decision Delegation

| Field | Definition |
| --- | --- |
| **ID** | `C25-INV-HG-001` |
| **Name** | Human Decision Delegation |
| **Category** | Human Governance |
| **Purpose** | Ensure all commercial decisions remain exclusively human-owned and C25 AI assistance does not become decision delegation. |
| **Rule** | Commercial interpretation, opportunity prioritization, sales action, revenue decision, forecast commitment, pipeline strategy, and brief acceptance are exclusively human-owned decisions. C25 AI assistance may summarize, explain, analyze, and recommend (as advisory observation) — it MUST NOT execute, approve, commit revenue, or make commercial decisions. Every AI-generated recommendation must carry an explicit human-review gate before any operational use. C25 presents intelligence and collects human intent — the human decision is enacted outside C25 through the owning layer's governed service. |
| **Enforcement expectation** | Future C25 workspace and brief contracts must require human acceptance before any downstream operational use. No C25 output may be directly consumable as an execution, approval, or CRM mutation instruction. Contract tests must verify zero paths from C25 workspace to C24 Transition Service or CRM Core entity mutation. |
| **Relation to previous invariants** | Extends C24-INV-HG-001 (Human Ownership of Commercial Decisions), C24-INV-HG-002 (Commercial Decision Ownership — human-gated acceptance, pipeline entry, forecast commitment), and C23-INV-HG-001 (OptimizationInsight requires human review before strategy change). C25 adds the intelligence-consumption gate: human review of AI-generated intelligence before any operational use. |
| **Status** | PROPOSED |

### 11.4 C25-INV-SEC-001 — Read-Only Assistant Tool Boundary

| Field | Definition |
| --- | --- |
| **ID** | `C25-INV-SEC-001` |
| **Name** | Read-Only Assistant Tool Boundary |
| **Category** | Security / Tool Boundary |
| **Purpose** | Structurally enforce the read-only nature of the C25 AI Assistant through tool capability and service layer — not through prompt. |
| **Rule** | The C25 AI Assistant interface permits only Query, Read, Aggregate, Compare, Explain, and Summarize operations. It MUST NOT provide Create, Update, Delete, Send Email, Trigger Outreach, Change Lifecycle, Access Credentials, or Direct Provider Call capabilities. This boundary is enforced by the tool capability allow-list and the service layer's absence of write paths — not by prompt instructions, refusal rules, or language constraints. Prompt-based constraints are defense-in-depth only; the structural absence of forbidden capabilities is the primary enforcement. |
| **Enforcement expectation** | Future AI Assistant tool definitions must be a structural allow-list with no forbidden operations present. Service layer contract tests must verify zero write, send, trigger, lifecycle-mutation, credential-access, or direct-provider paths from any C25 Assistant service. Tool capability must be auditable at the code level — not only observable at runtime. |
| **Relation to previous invariants** | Extends C20 D3 (single egress point through connector), C20 §5.2 (credential custody — no plaintext credential access), C22-INV-EX-001 (ActionGate sole execution authorization), and C22-INV-PR-001 (no CRM PHP code opens HTTP connections to provider endpoints). C25 adds the tool-capability enforcement dimension: structural absence of forbidden operations, not prompt-based refusal. |
| **Status** | PROPOSED |

### 11.5 C25-INV-PROV-001 — AI Explanation Provenance

| Field | Definition |
| --- | --- |
| **ID** | `C25-INV-PROV-001` |
| **Name** | AI Explanation Provenance |
| **Category** | Provenance Governance |
| **Purpose** | Ensure every AI-generated C25 output is traceable to a specific C20 provider invocation, model, and generation logic version. |
| **Rule** | Every AI-generated artifact produced by C25 — AI Commercial Brief, AI Assistant analytical response, or any future C25 AI output — MUST record: `sourceAIJobId` (C20 AIJob), `sourceAIRequestLogId` (C20 AIRequestLog), `provider` (via C20 routing), `model` (via C20 routing), and `generationVersion` (C25 generation logic version). C25 AI outputs without this provenance chain are invalid. The provenance chain MUST survive deletion of the C25 artifact — provenance records in C20 AIJob/AIRequestLog are independent of C25 artifact lifecycle. |
| **Enforcement expectation** | Future C25 brief and response schemas must require all five provenance fields. Validators must reject C25 AI-generated artifacts missing any provenance field. Contract tests must verify: (a) every generated brief has a traceable AIJob, (b) every AIRequestLog referenced exists in C20, (c) provenance fields survive brief supersession, (d) deleting a C25 artifact does not delete C20 provenance records. |
| **Relation to previous invariants** | Extends C20 ADR §5.4 (AIRequestLog is append-only, immutable), C20 ADR C8 (every completed provider invocation produces exactly one AIRequestLog row), C20 ADR C9 (PromptTemplate version referenced by AIRequestLog cannot be edited), C23-INV-PROV-002 (PerformanceMetric must declare computation methodology), C24-INV-MET-001 (PipelineMetric declares provenance, methodology), and C24-INV-REV-004 (PipelineMetric Provenance Integrity). C25 extends provenance governance from measurements and insights to AI-generated explanations and briefs. |
| **Status** | PROPOSED |

### 11.6 Invariant Summary

| Invariant ID | Category | Rule Summary | Precedent |
| --- | --- | --- | --- |
| C25-INV-OWN-001 | Ownership Boundary | C25 owns only presentation and interpretation; no business facts | C24-INV-SEP-001, C23-INV-OWN-001 |
| C25-INV-ADV-001 | Advisory Boundary | Every C25 output is advisory; carries mandatory advisory designation | C24-INV-ADV-001, C24-INV-REV-001, C23-INV-ADV-001 |
| C25-INV-HG-001 | Human Governance | Human exclusive ownership of commercial decisions; AI assists, never decides | C24-INV-HG-001, C24-INV-HG-002, C23-INV-HG-001 |
| C25-INV-SEC-001 | Security | Read-only Assistant tool boundary enforced by capability, not prompt | C20 D3, C20 §5.2, C22-INV-EX-001, C22-INV-PR-001 |
| C25-INV-PROV-001 | Provenance | Every AI output traceable to C20 AIJob/AIRequestLog, provider, model, generation version | C20 ADR C8/C9, C24-INV-MET-001, C24-INV-REV-004 |

**All 5 invariants are PROPOSED.** They will move to `DOCUMENTATION_ONLY` upon C25 charter ratification and to `ACTIVE` upon C25 implementation. They extend — but do not replace — the existing governance invariants from C20 (22), C21, C22 (29), C23 (22), and C24 (13).

---

## 12. Cross-Layer Dependency Compliance

| Boundary | Rule | C25 Compliance | Reference |
| --- | --- | --- | --- |
| C20 D3 | All AI model usage through C20 capability interfaces | ✅ C25 has no provider I/O; any model invocation routes through C20 | ADR-C20 §2 |
| C20 §5.2 | Credential custody model | ✅ C25 holds no credentials | ADR-C20 §5.2 |
| C20 ADR C8 | Every provider invocation produces AIRequestLog row | ✅ C25 AI outputs reference AIRequestLog | ADR-C20 §8 |
| C20 ADR C9 | PromptTemplate version immutable once referenced | ✅ C25 generationVersion preserved; C25 does not own PromptTemplate | ADR-C20 §8 |
| C21 Charter | Intelligence governance; ResearchEvidence governed by C21 (originated Phase3C07) | ✅ C25 consumes C21 as read-only; respects ResearchEvidence lineage | C21 Charter §3 |
| C22-INV-EX-001 | ActionGate sole authorization | ✅ C25 does not authorize, bypass, or influence ActionGate | C22 Invariant Registry |
| C22-INV-EX-003 | ExecutionLedger append-only | ✅ C25 reads only; does not write | C22 Invariant Registry |
| C22-INV-CRM-001 | No auto-create Lead | ✅ C25 does not auto-create any CRM entity | C22 Invariant Registry |
| C23-INV-SEP-001 | C23 reads C21/C22 as read-only | ✅ C25 extends this: read-only to C23 | C23 Charter |
| C23-INV-SEP-005 | C23 data not at ActionGate | ✅ C25 extends this: C25 data not at ActionGate | C23 Charter §3.4.1 |
| C23-INV-MET-002 | No metric-driven automation | ✅ C25 intelligence is advisory; no automated triggers | C23 Charter |
| C24-INV-SEP-001 | Revenue analytics must not redefine C23 metrics | ✅ C25 does not redefine any metric; reads all as evidence | C24 Charter |
| C24-INV-SEP-002 | OpportunityCandidate acceptance requires human transition | ✅ C25 reads candidates; does not modify state; transitions via C24 Transition Service | C24 Charter |
| C24-INV-LIFE-001 | Lifecycle transitions require immutable records | ✅ C25 reads transition history; does not create transitions | C24 Charter |
| C24-INV-ADV-001 | Advisory revenue artifacts only | ✅ C25 extends this: all C25 intelligence is advisory | C24 Charter |
| C24-INV-HG-001 | Human action required for all revenue decisions | ✅ C25 intelligence informs humans; humans decide | C24 Charter |
| C24-INV-HG-002 | Zero automation default for commercial decisions | ✅ C25 extends this to AI-assisted commercial intelligence | C24 Charter |
| C24-INV-MET-001 | Metrics have provenance and cannot trigger automation | ✅ C25 reads metrics with provenance; no metric triggers | C24 Charter |
| C24-INV-MET-002 | PipelineMetric declares C24 domain; rejects C23 replacement | ✅ C25 does not create metrics; reads existing | C24 Charter |
| C24-INV-REV-001 | RevenueInsight advisory-only | ✅ C25 reads insights; preserves advisory designation | C24 Invariant Registry |
| C24-INV-REV-002 | PipelineMetric cannot trigger workflow | ✅ C25 reads metrics; no trigger path | C24 Invariant Registry |
| C24-INV-REV-003 | Revenue analytics cannot mutate CRM lifecycle | ✅ C25 extends this: no CRM mutation from any C25 path | C24 Invariant Registry |
| C24-INV-REV-004 | PipelineMetric provenance integrity | ✅ C25 preserves provenance when presenting metrics | C24 Invariant Registry |
| C24-INV-REV-005 | RevenueInsight freshness governance | ✅ C25 surfaces freshness status; preserves staleness warnings | C24 Invariant Registry |

---

## 13. Compatibility Verification

### 13.1 C24 WP1 ReplySignal Compatibility

| Concern | C25 Relationship | Compatible? |
| --- | --- | --- |
| ReplySignal as intelligence source | C25 reads ReplySignal interpretation, confidence, provenance, and lifecycle state | ✅ Read-only |
| ReplySignal lifecycle ownership | WP1 owns ReplySignal lifecycle; C25 does not modify | ✅ |
| ReplySignal re-interpretation | C25 does not re-interpret or reclassify ReplySignals | ✅ |
| Advisory designation preservation | C25 preserves ReplySignal advisory nature in all presentations | ✅ |

### 13.2 C24 WP2 OpportunityCandidate Compatibility

| Concern | C25 Relationship | Compatible? |
| --- | --- | --- |
| Candidate as intelligence source | C25 reads candidate state, review context, commercial signal summary, and transition audit | ✅ Read-only |
| Candidate lifecycle ownership | WP2 owns candidate lifecycle; C25 does not modify or transition | ✅ |
| Candidate in brief context | C25 may reference candidate state in commercial briefs as advisory context | ✅ Advisory only |
| No candidate auto-transition | C25 brief or analysis does not trigger candidate state changes | ✅ |
| Lifecycle transition path | C25 workspace → Human Decision → Authorized C24 Transition Service → lifecycle mutation + audit | ✅ Correct flow |

### 13.3 C24 WP3 RevenueInsight/PipelineMetric Compatibility

| Concern | C25 Relationship | Compatible? |
| --- | --- | --- |
| RevenueInsight as analytical source | C25 reads insight narratives, provenance, methodology, freshness | ✅ Read-only |
| PipelineMetric as measurement source | C25 reads metric values, types, provenance, sample context | ✅ Read-only |
| Insight acceptance ≠ C25 action | C25 does not change insight state or trigger action on acceptance | ✅ |
| Freshness governance preservation | C25 surfaces STALE/ARCHIVAL warnings from C24 artifacts | ✅ |
| No metric recomputation | C25 reads metrics as-is; does not recompute or replace | ✅ |

### 13.4 CRM Core Compatibility

| Concern | C25 Relationship | Compatible? |
| --- | --- | --- |
| CRM Opportunity as context | C25 reads Opportunity data for commercial context | ✅ Read-only |
| CRM lifecycle ownership | CRM Core owns all lifecycle; C25 has zero write paths | ✅ |
| C25 may invoke authorized C24 transition services; does not bypass C24 lifecycle governance | C25 workspace collects human intent; may invoke governed C24 service entry points; MUST NOT directly mutate C24-owned data | ✅ |
| No FK coupling | C25 has no FK references to any CRM Core entity | ✅ |
| No proxy creation | C25 provides no "Create Opportunity" or CRM mutation endpoint | ✅ |

### 13.5 C23 OptimizationInsight Compatibility

| Concern | C25 Relationship | Compatible? |
| --- | --- | --- |
| OptimizationInsight as context | C25 may read C23 optimization insights for commercial pattern context | ✅ Read-only |
| Domain separation | C23: "Did prospecting work?" C25: "What does the commercial evidence tell us?" | ✅ Structurally distinct |
| No optimization replacement | C25 does not generate optimization recommendations | ✅ |

---

## 14. Forbidden Scope

### 14.1 Forbidden Entities

The following entity types MUST NOT be created under C25 or any C25 work package authority:

| Forbidden Entity | Rationale | Precedent |
| --- | --- | --- |
| `CommercialDecisionAgent` | AI making commercial decisions — violates human governance | C24 Charter §9 |
| `AutoBriefEngine` | Autonomous brief generation without human review gate | C25-INV-HG-001 |
| `AIRevenueAdvisor` | AI-driven revenue recommendations phrased as directives | C24 Charter §9 |
| `PipelineAutoManager` | Automated pipeline management from AI analysis | C24-INV-MET-001 |
| `ForecastAssistant` (autonomous) | AI-driven forecast generation or recommendation | C24-INV-HG-001 |
| `OpportunityAutoPrioritizer` | AI-driven opportunity ranking with automated action | C25-INV-HG-001 |
| `CommercialSignalInterpreter` (autonomous) | AI reinterpreting commercial signals without human review | C24 WP1 Charter |
| `AICRMController` | AI-driven CRM entity mutation based on commercial intelligence | C24/CRM boundary |
| `C25Lifecycle` or equivalent | A second lifecycle parallel to C24 OpportunityCandidate lifecycle | C25-INV-OWN-001 |
| `AIScore` (within C25) | A competing scoring authority — Chitu owns canonical_score | C20 ADR §1.3 |
| `BusinessFact` (within C25) | C25 does not own business facts — CRM Core and C24 own them | C25-INV-OWN-001 |

### 14.2 Forbidden Patterns

| Forbidden Pattern | Rationale |
| --- | --- |
| AI brief → automated CRM action | Briefs are advisory; actions are human-owned |
| AI recommendation phrased as directive | Must be phrased as observation: "Pipeline analysis suggests..." |
| AI analytical answer → automated forecast adjustment | Forecast is human-owned in CRM Core |
| Brief without advisory designation | C25-INV-ADV-001 enforcement |
| Brief without provenance references (sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion) | C25-INV-PROV-001 enforcement |
| Stale evidence presented without freshness warning | C25 must surface artifact freshness from C24 |
| AI response that refuses to disclose limitations | Every analytical response must declare what it cannot conclude |
| Cross-artifact assembly that creates a new governance record | Assembly is presentation, not persistence |
| AI brief used as ActionGate evidence | C25 data must not appear at ActionGate |
| Batch brief generation without human review gate | Each brief requires individual human review |
| C25 workspace bypassing C24 lifecycle governance or directly mutating C24-owned data | C25 may invoke authorized C24 transition services via governed service entry points; MUST NOT bypass governance or directly update C24 entities |
| AI Assistant with write-capable tools | C25-INV-SEC-001 enforcement — tools are structural allow-list |
| AI Brief field asserting priority, ranking, lifecycle, stage, or revenue truth authority | Brief fields MUST use observation/analysis/explanation forms; authority fields are structurally excluded (§5.2 Field Authority Constraints) |
| AI Assistant producing ungrounded commercial conclusions without source traceability | Every analytical claim MUST reference source record IDs, artifact IDs, reporting period, and C20 provenance (§6.6) |

### 14.3 Structural Prohibitions

C25 MUST NOT implement or authorize:

- CRM lifecycle ownership (Account, Contact, Opportunity, Sales Stage)
- Revenue forecast authority or commitment
- Sales execution or outreach triggering
- Commercial approval or decision authority
- Provider integration, credential storage, or HTTP egress
- Background automation, workers, schedulers, queues, or webhooks (Phase 1)
- Autonomous generation (Phase 1)
- C20/C21/C22/C23/C24 artifact mutation
- CRM Core entity creation, modification, or lifecycle mutation
- A second lifecycle parallel to C24 OpportunityCandidate
- Business fact storage independent of source artifacts

---

## 15. Security and Runtime Boundary

C25 is an **intelligence consumption and presentation layer** — it has no execution runtime, no outbound communication, and no provider interaction.

| Concern | C25 Status | Evidence |
| --- | --- | --- |
| HTTP egress | **None** | C25 has no API, SDK, or HTTP integration |
| Provider SDK imports | **None** | No vendor dependency or SDK |
| Provider secrets | **None** | No credential ownership |
| Vendor coupling | **None** | Provider-agnostic intelligence layer |
| Workers / schedulers | **None (Phase 1)** | All intelligence assembly is human-initiated on-demand; no background execution |
| Queues / message brokers | **None** | No asynchronous processing infrastructure |
| Database mutation beyond C25 scope | **None** | Read-only access to C20/C21/C22/C23/C24/CRM Core |
| Autonomous agent loop | **None** | No agent, no loop, no automation |
| Event-driven assembly | **None (Phase 1)** | No event listener triggers brief generation or workspace assembly |
| Webhook dispatch | **None** | No webhooks or outbound event triggers |
| AI model invocation | **Only through C20** | Any model invocation for brief generation or Q&A routes through C20 capability interfaces |

**C25 is an intelligence layer — not an execution layer.** It reads, assembles, interprets, and presents. It never acts, triggers, or commands.

### 15.1 AI Model Invocation Governance

If a C25 WP implementation requires AI model invocation (for brief generation, analytical Q&A, or summarization):

| Requirement | Rule |
| --- | --- |
| Routing | MUST route through C20 capability interfaces |
| Credential custody | MUST use C20 ProviderCredential; C25 MUST NOT hold credentials |
| Audit | MUST produce C20 AIRequestLog entries for every invocation |
| Provenance | C25 output MUST record sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion (§7.2) |
| Cost attribution | MUST attribute token/cost through C20 cost accounting |
| Model selection | MUST use C20 provider routing; C25 MUST NOT embed model selection |
| Human gate | AI output MUST pass through human review before any operational use |

---

## 16. Open Questions for Ratification

The following questions are carried forward from v1.0-draft. Resolution is recommended before or during ADR drafting.

| # | Question | Default Recommendation |
| --- | --- | --- |
| Q1 | Should the AI Commercial Brief be a persistent record with lifecycle or a transient view? | Persistent as immutable projection with GENERATED → REVIEWED → ACCEPTED/DISMISSED lifecycle. ACCEPTED/DISMISSED are human decisions. |
| Q2 | Should the AI Assistant be structured Q&A (bounded question types) or free-form NL? | Structured Q&A with enumerated question domains as safe default. Free-form as governed future extension with boundary refusal tests. |
| Q3 | Should the Human Decision Workspace be a C25-owned surface or CRM Core-owned? | C25-owned presentation surface with CRM Core integration points for human-initiated decisions. |
| Q4 | Should brief generation be on-demand (human-triggered) or scheduled? | On-demand only for Phase 1 (§8). Scheduled requires independent ADR. |
| Q5 | Should CommercialContext be purely transient or cacheable? | Transient by default (§4.2). Caching is permitted only with source references, assembly version, timestamp, and freshness metadata (§4.5). |

---

## 17. Future ADR Roadmap

### 17.1 Required ADRs Before C25 Implementation

| ADR ID | Title | Purpose | Depends On |
| --- | --- | --- | --- |
| **ADR-C25-001** | Commercial Intelligence Workspace Definition | Define the unified intelligence workspace: CommercialContext assembly contracts, data model, freshness surfacing rules, and read-only enforcement. | C25 Charter ratification |
| **ADR-C25-002** | AI Commercial Brief Governance | Define brief structure as immutable projection artifact: mandatory provenance fields, advisory designation format, human review gate, supersession rules, and deletion-governance contracts. | ADR-C25-001 |
| **ADR-C25-003** | Revenue Analyst Assistant Governance | Define analytical Q&A scope, permitted question domains, tool capability allow-list, response structure, limitation declaration requirements, and boundary refusal enforcement. | ADR-C25-001 |
| **ADR-C25-004** | Human Decision Workspace Architecture | Define workspace structure, human/AI interaction model, C24 Transition Service integration contract, decision audit requirements, and AI recommendation phrasing governance. | ADR-C25-001, ADR-C25-002 |
| **ADR-C25-005** | C25 Cross-Layer Read-Only Access Contracts | Define structural read-only access patterns across C20/C21/C22/C23/C24/CRM Core, provenance preservation rules, freshness surfacing contracts, and AI provenance chain validation (C25-INV-PROV-001). | ADR-C25-001 |

### 17.2 ADR Sequence

```text
Phase 1 (C25 Foundation ADRs):
  ADR-C25-001 (Commercial Intelligence Workspace)
    ├── ADR-C25-002 (AI Commercial Brief Governance)
    ├── ADR-C25-003 (Revenue Analyst Assistant Governance)
    └── ADR-C25-005 (Cross-Layer Read-Only Access)

Phase 2 (C25 Integration ADRs):
  ADR-C25-004 (Human Decision Workspace Architecture)
    └── ADR-C25-005 (refined with workspace integration detail)
```

---

## 18. Implementation Restrictions

### 18.1 What This Charter Authorizes

This charter authorizes **governance specification only**:

- C25 scope definition as the AI Commercial Intelligence Layer
- CommercialContext read model design
- AI Commercial Brief as immutable projection artifact
- Read-only AI Assistant security boundary
- Human Decision Workspace presentation layer
- Work package structure (WP1–WP4) for future implementation planning
- Cross-layer boundary documentation with C20–C24 and CRM Core
- Human governance model for AI-assisted commercial intelligence
- Five proposed C25 invariants (OWN-001, ADV-001, HG-001, SEC-001, PROV-001)
- C20 AI provenance requirements for C25 AI-generated artifacts
- Generation trigger policy (Phase 1: human-initiated only)
- Forbidden entity and pattern enumeration
- ADR roadmap for future implementation planning

### 18.2 What This Charter Does NOT Authorize

This charter authorizes **NO**:

- Entity creation, metadata modification, or schema change
- Service, hook, guard, or save-option implementation
- PHP, JavaScript, template, or client-surface code
- Workspace, brief, assistant, or dashboard implementation
- AI model invocation, prompt engineering, or model selection
- Test authoring or test-fixture creation
- Provider, connector, API, or runtime integration
- Scheduler, worker, webhook, or background-job configuration
- Release artifact, deployment, or configuration change
- Commit, push, or tag

### 18.3 Implementation Gate

Before any C25 implementation may begin, the following must be independently ratified:

1. **This C25 Charter** — ratified through governance review.
2. **ADR-C25-001 through ADR-C25-005** — drafted and accepted.
3. **C25 Invariant Registration** — formal addition of C25-INV-OWN-001, ADV-001, HG-001, SEC-001, and PROV-001 to a C25 Invariant Registry.
4. **C25 Implementation Work Package** — separately approved with:
   - Workspace, brief, assistant, and decision-support specifications
   - CommercialContext assembly contracts
   - Cross-layer read-only access contracts
   - AI model invocation governance (routing through C20)
   - AI provenance chain validation
   - Human review gate specifications
   - Invariant activation triggers and contract test paths
5. **C25 Governance Review** — independent verification of C20–C25 and CRM Core boundary compliance.

---

## 19. Self-Review

### 19.1 Charter Self-Assessment

| Question | Answer | Verification |
| --- | --- | --- |
| Does C25 own commercial facts? | **No** | C25 owns presentation and interpretation. Business facts reside in CRM Core, C24, and upstream layers. CommercialContext is a read model — deleting it loses no facts. AI Commercial Briefs are projections — deleting them loses no facts. |
| Can C25 bypass C24 to modify lifecycle? | **No** | C25 workspace collects human intent. Lifecycle transitions go through C24 Transition Service (C24-INV-SEP-002, C24-INV-LIFE-001). C25 has no write path to OpportunityCandidate, RevenueInsight, PipelineMetric, or ReplySignal. |
| Does the AI Assistant have write permissions? | **No** | C25-INV-SEC-001 enforces read-only tool capability. Permitted: Query, Read, Aggregate, Compare, Explain, Summarize. Forbidden: Create, Update, Delete, Send Email, Trigger Outreach, Change Lifecycle, Access Credentials, Direct Provider Calls. Enforced by tool capability allow-list and service layer contract tests — not by prompt. |
| Does deleting all AI Commercial Briefs lose business facts? | **No** | Briefs are immutable projection artifacts. All business facts reside in C20–C24 and CRM Core source artifacts. Deleting a brief deletes the projection — the facts projected are intact in their source artifacts. The C20 AIJob/AIRequestLog provenance chain is independent of C25 artifact lifecycle (C25-INV-PROV-001). |
| Is every AI-generated C25 output traceable to C20 AIJob/AIRequestLog? | **Yes** | C25-INV-PROV-001 requires: sourceAIJobId, sourceAIRequestLogId, provider, model, and generationVersion on every AI-generated C25 artifact. This provenance chain survives artifact deletion. |

### 19.2 Boundary Integrity

| Boundary | Status |
| --- | --- |
| C20 Provider boundary | ✅ Intact — C25 routes all AI model invocation through C20 |
| C20 Credential custody | ✅ Intact — C25 holds no credentials |
| C21 Evidence lineage | ✅ Intact — ResearchEvidence governed by C21 (originated Phase3C07); C25 reads only |
| C21 Intelligence governance | ✅ Intact — C25 does not score, rank, or qualify |
| C22 Human approval | ✅ Intact — C25 does not bypass ActionGate |
| C22 Execution boundary | ✅ Intact — C25 reads execution history; does not execute |
| C23 Optimization observation boundary | ✅ Intact — C25 reads C23 context; does not generate optimization recommendations |
| C24 RevenueInsight ownership | ✅ Intact — C25 reads RevenueInsight; does not modify |
| C24 OpportunityCandidate lifecycle | ✅ Intact — C25 reads candidates; transitions go through C24 Transition Service |
| C24 Immutable transition history | ✅ Intact — C25 reads transition audit; does not create transitions |
| CRM Core commercial authority | ✅ Intact — C25 reads CRM Core; does not create, modify, or transition |

---

## 20. References

| Reference | Path |
| --- | --- |
| C24 Charter (RATIFIED) | `docs/PHASE3C24_CHARTER.md` |
| C24 Master Freeze Review | `docs/audit/PHASE3C24_MASTER_FREEZE_REVIEW.md` |
| C24 Invariant Registry | `docs/adr/C24_INVARIANT_REGISTRY.md` |
| C24 WP1 Charter (FROZEN) | `docs/PHASE3C24_WP1_REPLY_INTELLIGENCE_CHARTER.md` |
| C24 WP2 Charter (FROZEN) | `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md` |
| C24 WP2 Implementation Charter | `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md` |
| C24 WP3 Charter (RATIFIED) | `docs/PHASE3C24_WP3_REVENUE_INSIGHT_CHARTER.md` |
| C24 WP3 Implementation Charter | `docs/PHASE3C24_WP3_IMPLEMENTATION_CHARTER.md` |
| C23 Charter (FROZEN) | `docs/PHASE3C23_CHARTER.md` |
| C23 Invariant Registry | `docs/adr/C23_INVARIANT_REGISTRY.md` |
| C22 Charter (FROZEN) | `docs/PHASE3C22_CHARTER.md` |
| C22 Invariant Registry | `docs/adr/C22_INVARIANT_REGISTRY.md` |
| C21 Charter (FROZEN) | `docs/PHASE3C21_CHARTER.md` |
| C20 ADR (ACTIVE) | `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` |
| C20 Invariant Registry | `docs/adr/C20_INVARIANT_REGISTRY.md` |
| C25 Charter v1.0 (superseded) | `docs/PHASE3C25_CHARTER_DRAFT.md` (prior version) |
| C25 Charter v1 Ratification Review | `docs/audit/PHASE3C25_CHARTER_RATIFICATION_REVIEW.md` |

---

*Charter v2.1 — minor correction pass. Governance specification only. This document authorizes no implementation, entity creation, metadata modification, code changes, commits, pushes, or tags. All implementation requires independent ADR acceptance, governance review, and work-package approval.*

*Co-Authored-By: Claude <noreply@anthropic.com>*
