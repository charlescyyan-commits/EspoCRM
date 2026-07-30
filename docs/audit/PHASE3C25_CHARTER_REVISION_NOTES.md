# Phase3C25 Charter Revision Notes — v1.0 → v2.0 → v2.1

| Field | Value |
| --- | --- |
| Document Type | Revision Notes |
| Subject | Phase3C25 Charter v1.0-draft → v2.0-draft → v2.1-draft |
| Date | 2026-07-30 |
| Source v1 | `docs/PHASE3C25_CHARTER_DRAFT.md` v1.0-draft |
| Target v2.0 | `docs/PHASE3C25_CHARTER_DRAFT.md` v2.0-draft |
| Target v2.1 | `docs/PHASE3C25_CHARTER_DRAFT.md` v2.1-draft (minor correction pass) |
| Baseline | `phase3c24-master-freeze` (`6dd784c`) |

---

## 1. Revision Summary

This revision transforms the C25 Charter from a general-purpose "AI Commercial Intelligence Layer" into a precisely-bounded **intelligence foundation of an AI Sales Operating System** — with explicit ownership boundaries, structural projection semantics for AI-generated artifacts, C20 provenance chain integration, read-only security enforcement, and human-initiated-only generation policy.

Six major structural changes were applied. Each is documented below with the original issue, the change made, and the C20–C24 alignment rationale.

---

## 2. Structural Changes

### 2.1 C25 Identity Narrowing

**Original issue (v1.0):** The v1.0 charter defined C25 as "AI Commercial Intelligence Layer" without clarifying its relationship to the broader concept of an AI Sales Operating System. This left ambiguity about whether C25 was claiming to be the full operating system.

**Change:** C25 is now explicitly defined as "the intelligence foundation of an AI Sales Operating System — not the complete operating system itself" (§1.1). The charter adds explicit scope boundaries:
- C25 IS responsible for: commercial context understanding, outcome intelligence, AI-assisted commercial analysis, decision support, human-assisted interpretation
- C25 IS NOT responsible for: CRM replacement, commercial fact ownership, sales lifecycle, autonomous execution, automated strategy modification

**C20–C24 alignment:** This narrowing ensures C25 does not implicitly claim authority over CRM Core (commercial facts, sales lifecycle), C22 (execution), or C23 (strategy/optimization). The "not a complete operating system" framing prevents scope creep.

---

### 2.2 Ownership Boundary — New Section

**Original issue (v1.0):** The v1.0 charter had a "C25 Owns / C25 Does NOT Own" table (§3.1, §3.2) but did not define what each predecessor layer owns in its own right. This made cross-layer boundary claims harder to verify.

**Change:** New §3.1 ("Layer Ownership Definition") enumerates exactly what each layer owns:

| Layer | Owns |
| --- | --- |
| CRM Core | Account, Contact, Opportunity, Sales lifecycle, Commercial authority |
| C20 | AIJob, AIRequestLog, PromptTemplate, ProviderCredential, ProviderRoute, ProviderHealth |
| C21 | Governs and extends governance for ResearchEvidence (originated Phase3C07), AIQualificationInsight, HumanFeedback, IntelligenceAggregate |
| C22 | ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, ReplyDetection, OutreachExecution |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation |
| C24 | RevenueInsight, PipelineMetric, ReplySignal, OpportunityCandidate lifecycle transitions |
| C25 | CommercialContext assembly, AI Commercial Brief, Read-only AI Assistant interface, Human Decision Workspace presentation layer |

**Critical fix — ResearchEvidence lineage:** v1.0 stated "C21 owns ResearchEvidence." This is historically inaccurate. ResearchEvidence originated in Phase3C07. C21 governs and extends governance for it. The v2.0 charter corrects this: "C21 governs and extends governance for ResearchEvidence" (§3.1).

**C20–C24 alignment:** Each ownership claim was verified against the corresponding charter/ADR:
- C20: ADR-C20 §5.4, §7 — AIJob, AIRequestLog, ProviderCredential ownership verified
- C21: C21 Charter §2, §3 — ResearchEvidence governance verified
- C22: C22 Charter §1.1 — ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger ownership verified
- C23: C23 Charter §2 — OptimizationInsight, PerformanceMetric ownership verified
- C24: C24 Charter §1.1, §4, §5, §6 — RevenueInsight, PipelineMetric, ReplySignal, OpportunityCandidate lifecycle ownership verified

---

### 2.3 CommercialContext Read Model — New Section

**Original issue (v1.0):** The v1.0 charter mentioned "Commercial Intelligence Workspace" (WP1) as a unified read-only surface but did not define what a "CommercialContext" is or whether it persists as an independent record. The open question Q5 (§14) asked whether assembly should be persistent or transient but did not answer it.

**Change:** New §4 ("CommercialContext Read Model") defines:

1. **Definition:** CommercialContext is a read model — not a business entity. Default is runtime-assembled, read-only.
2. **Sources:** ResearchEvidence (C21), RevenueInsight (C24), PipelineMetric (C24), ReplySignal (C24), Execution results (C22), CRM Core facts
3. **Prohibitions:** MUST NOT become a business-fact store, scoring system, priority authority, or lifecycle system
4. **Caching governance:** If cached, must preserve source references, assembly version, generated timestamp, freshness metadata
5. **Deletion rule:** Deleting a cached CommercialContext MUST NOT lose any business fact — facts reside in source artifacts

**C20–C24 alignment:** This aligns with C24-INV-REV-003 (revenue analytics cannot mutate CRM lifecycle), C24-INV-REV-005 (freshness governance), and C23-INV-SEP-001 (read-only consumption). The CommercialContext is structurally prevented from becoming a competing governance record.

---

### 2.4 AI Commercial Brief — Redefined as Immutable Projection Artifact

**Original issue (v1.0):** The v1.0 charter described briefs as "human-readable commercial summaries" with constraints but did not define them as immutable projection artifacts. V1.0 did not specify that briefs must be traceable to C20 AIJobs/AIRequestLogs. Most critically, v1.0 did not establish the deletion rule: deleting briefs must not lose business facts.

**Change:** §5.2 redefines AI Commercial Brief with:

1. **Identity:** "Immutable Projection Artifact" — not a business authority
2. **Mandatory provenance fields:** Source record IDs, reporting period, generated timestamp, generation version, source AIJob ID (C20), source AIRequestLog IDs (C20), provider, model, advisory designation
3. **Immutability:** Once generated, immutable. Changed interpretation → new superseding brief. All versions preserved for audit.
4. **Deletion rule:** Deleting all briefs MUST NOT lose any business fact. Briefs are projections of governed evidence. Facts reside in C20–C24 and CRM Core.
5. **Non-ownership:** Brief does NOT own Opportunity authority, Lifecycle authority, Priority authority, or Revenue truth

**C20–C24 alignment:**
- C20: Mandatory sourceAIJobId + sourceAIRequestLogId fields link to C20 AIJob/AIRequestLog (ADR-C20 C8, C9)
- C24: Brief is advisory (extends C24-INV-ADV-001); does not modify OpportunityCandidate (extends C24-INV-SEP-002)
- Immutability aligns with C23-INV-OWN-003 (OptimizationInsight immutable after creation) and C23-INV-OWN-004 (PerformanceMetric immutable after creation)

---

### 2.5 Human Decision Workspace — Corrected Flow

**Original issue (v1.0):** The v1.0 charter described a Human Decision Workspace (§4.4) with human/AI separation but did not specify the transition path from C25 workspace to C24 lifecycle mutation. This left ambiguity: could C25 call C24 Transition Service directly?

**Change:** §5.4 explicitly defines the correct flow:

```text
C25 Workspace → Human Decision → C24 Transition Service → Lifecycle mutation + immutable audit
```

Key additions:
- C25 is responsible for presenting context, AI explanations, briefs, and collecting human intent
- C25 is NOT responsible for modifying OpportunityCandidate state, creating a second lifecycle, or bypassing C24 Transition Service
- C25 never calls C24 Transition Service directly — the human initiates the transition through C24's own service boundary

**C20–C24 alignment:** This flow preserves C24-INV-SEP-002 (OpportunityCandidate acceptance requires authorized human transition) and C24-INV-LIFE-001 (immutable transition records). C25 workspace is structurally separated from C24 lifecycle operations.

---

### 2.6 AI Assistant Security Boundary — New Section

**Original issue (v1.0):** The v1.0 charter described the AI Assistant (WP3) as a Q&A interface with constraints but did not define the security boundary in terms of tool capabilities vs. prompt. V1.0 relied on language constraints ("MUST NOT create, modify, or recommend CRM lifecycle actions") without specifying structural enforcement.

**Change:** New §6 ("AI Assistant Security Boundary") defines:

1. **Permitted operations:** Query, Read, Aggregate, Compare, Explain, Summarize
2. **Forbidden operations:** Create, Update, Delete, Send email, Trigger outreach, Change lifecycle, Access credentials, Direct provider calls
3. **Enforcement architecture:** Tool capability allow-list (structural) + Service layer (zero write paths) — NOT prompt-based. Prompt constraints are defense-in-depth only.
4. **Domain boundary refusal:** Assistant must recognize and refuse out-of-domain requests at the service layer before processing

**C20–C24 alignment:**
- C20 D3: Single egress point through connector — C25 Assistant has no direct provider path
- C20 §5.2: Credential custody — C25 Assistant cannot access credentials
- C22-INV-EX-001: ActionGate sole authorization — C25 Assistant cannot trigger execution
- C22-INV-PR-001: No CRM PHP code opens HTTP connections — C25 Assistant has no HTTP capability
- C23-INV-SEP-005: C23 data not at ActionGate — C25 Assistant output not at ActionGate

---

### 2.7 C20 AI Provenance — Corrected Model

**Original issue (v1.0):** The v1.0 charter referenced C20 "capability interfaces" for AI model invocation but did not specify the AIJob/AIRequestLog relationship or what provenance fields C25 artifacts must carry.

**Change:** New §7 ("C20 AI Provenance") defines:

1. **Correct model:**
   ```
   Logical AI task → AIJob (one unit of async capability work; one row per invocation attempt group)
                   → One or more AIRequestLog records (one row per provider invocation)
   ```

2. **Rejected model:** "Every model call creates one AIJob" — a single logical task may involve multiple provider calls.

3. **C25 provenance requirements:** Every AI-generated C25 artifact MUST record sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion.

**C20–C24 alignment:** Directly derived from C20 ADR §5.4 (entity definitions), §7 (AIJob lifecycle), and invariants C8 (every invocation → AIRequestLog row) and C9 (PromptTemplate version immutable once referenced). This provenance model is not a C25 invention — it is the C20-defined model, now applied to C25's AI generation scope.

---

### 2.8 Generation Trigger Policy — New Section

**Original issue (v1.0):** The v1.0 charter stated "no scheduler, no worker, no autonomous agent loop" in the security boundary (§8) but did not declare a generation trigger policy. Open question Q4 (§14) asked about on-demand vs. scheduled generation but did not answer it.

**Change:** New §8 ("Generation Trigger Policy") establishes:

1. **Phase 1: Human-initiated only.** User must explicitly click/request generation.
2. **Forbidden triggers:** Scheduler, worker, webhook, background autonomous, event listener.
3. **Future automation:** Requires dedicated C25 Charter Amendment, independent ADR, invariant update, and governance review.

**C20–C24 alignment:** Aligns with C24-INV-HG-002 (zero automation default for commercial decisions), C23-INV-HG-002 (future automation requires Charter Amendment + ADR + invariant update + governance review), and C23-INV-MET-002 (no metric-driven automation). C25 extends the zero-automation default to AI generation triggering.

---

### 2.9 C25 Native Invariants — Renumbered and Strengthened

**Original issue (v1.0):** The v1.0 charter proposed invariants C25-INV-INT-001 through INT-005 using a generic "INT" prefix. Each invariant had a rule and precedent but lacked explicit Purpose and Enforcement expectation fields. V1.0 did not have invariants for security/tool boundary or provenance.

**Change:** Five invariants renumbered with category-specific prefixes:

| v1.0 ID | v2.0 ID | Category | Change |
| --- | --- | --- | --- |
| C25-INV-INT-001 | C25-INV-ADV-001 | Advisory Boundary | Added Purpose and Enforcement expectation fields |
| C25-INV-INT-002 | C25-INV-OWN-001 | Ownership Boundary | Renamed; expanded to include CommercialContext non-ownership |
| C25-INV-INT-003 | C25-INV-HG-001 | Human Governance | Added C24 Transition Service flow reference |
| C25-INV-INT-004 | (absorbed into OWN-001) | — | Cross-artifact read-only consumption folded into ownership boundary invariant |
| C25-INV-INT-005 | (absorbed into HG-001, SEC-001) | — | No-automation rule distributed across human governance and security invariants |
| (new) | C25-INV-SEC-001 | Security / Tool Boundary | New — Read-only Assistant tool boundary enforced by capability, not prompt |
| (new) | C25-INV-PROV-001 | Provenance Governance | New — AI explanation provenance chain (sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion) |

Each invariant now includes:
- **Purpose:** Why this invariant exists
- **Rule:** The governing constraint
- **Enforcement expectation:** How it will be structurally verified
- **Relation to previous invariants:** How it extends (not replaces) the existing C20–C24 invariant chain

**C20–C24 alignment:** Every invariant's "Relation to previous invariants" field explicitly cites specific C20/C21/C22/C23/C24 invariants it extends. No C25 invariant replaces any predecessor invariant.

---

## 3. Preserved Content

The following sections from v1.0 were preserved with minimal or no changes:

| Section | v1.0 | v2.0 | Changes |
| --- | --- | --- | --- |
| Architectural position diagram | §1.3 | §1.5 | Layer descriptions updated to match new ownership definitions |
| What C25 Does NOT Provide | §2.3 | §2.3 | Added "Strategy modification" row |
| WP1 Workspace | §4.1 | §5.1 | Unchanged |
| WP3 Assistant (general) | §4.3 | §5.3 | Unchanged (security boundary moved to §6) |
| Cross-layer relationship model | §5 | §9 | Unchanged (verified against v2 ownership definitions) |
| Human governance model | §6 | §10 | Unchanged (flow corrected in §5.4) |
| Forbidden scope | §7 | §14 | Added 3 entities: C25Lifecycle, AIScore (within C25), BusinessFact (within C25) |
| Security and runtime | §8 | §15 | Updated to reference Phase 1 generation policy |
| Cross-layer dependency compliance | §10 | §12 | Added C20 ADR C8/C9 references |
| Compatibility verification | §11 | §13 | Added lifecycle transition path row to §13.2 |
| ADR roadmap | §12 | §17 | Unchanged |
| Implementation restrictions | §13 | §18 | Updated authorization list; added scheduler/worker/webhook prohibition |
| Open questions | §14 | §16 | Default recommendations updated to reflect v2 decisions |
| References | §15 | §20 | Added C20/C23 invariant registries, v1 review |

---

## 4. Deleted Content

| v1.0 Section | Reason for Removal |
| --- | --- |
| §9.1–9.5 (INT-001 through INT-005 detailed descriptions) | Replaced by §11 with new invariant IDs and expanded fields (Purpose, Enforcement expectation, Relation) |
| §9.6 (Invariant summary table) | Replaced by §11.6 with new invariant IDs |
| "C25-INV-INT-004 Cross-Artifact Read-Only Consumption" as standalone invariant | Absorbed into C25-INV-OWN-001 (ownership boundary — "MUST NOT own any C20/C21/C22/C23/C24 artifact") and C25-INV-SEC-001 (security boundary — "Permitted: Read") |
| "C25-INV-INT-005 No Autonomous Commercial Action" as standalone invariant | Distributed across C25-INV-HG-001 (human governance — "human decision is enacted outside C25") and C25-INV-SEC-001 (security — "Forbidden: Send Email, Trigger Outreach") |

---

## 5. C20–C24 Alignment Verification

### 5.1 C20 Alignment

| v2.0 Reference | C20 Alignment | Status |
| --- | --- | --- |
| §3.1 — C20 owns AIJob, AIRequestLog, PromptTemplate, ProviderCredential, ProviderRoute | ADR-C20 §5.4 entity definitions | ✅ |
| §7.1 — AIJob/AIRequestLog model: one AIJob → multiple AIRequestLogs | ADR-C20 §5.4, §7 | ✅ |
| §7.2 — C25 provenance: sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion | ADR-C20 C8, C9, §5.5 | ✅ |
| §8.1 — AI model invocation through C20 capability interfaces | ADR-C20 D3 | ✅ |
| §8.1 — No credential storage in C25 | ADR-C20 §5.2 | ✅ |
| §15.1 — Audit via C20 AIRequestLog | ADR-C20 §5.4 | ✅ |

### 5.2 C21 Alignment

| v2.0 Reference | C21 Alignment | Status |
| --- | --- | --- |
| §3.1 — C21 governs and extends governance for ResearchEvidence (originated Phase3C07) | C21 Charter §2, §3 | ✅ |
| §9.2 — C25 consumes C21 intelligence as read-only; no scoring/ranking/qualification | C21 Charter §2 | ✅ |

### 5.3 C22 Alignment

| v2.0 Reference | C22 Alignment | Status |
| --- | --- | --- |
| §3.1 — C22 owns ProspectCandidate, ProspectRun, ActionGate, ExecutionLedger, ReplyDetection | C22 Charter §1.1 | ✅ |
| §9.3 — C25 does not bypass or influence ActionGate | C22-INV-EX-001 | ✅ |
| §9.3 — C25 data not at ActionGate | C23-INV-SEP-005 (extended) | ✅ |

### 5.4 C23 Alignment

| v2.0 Reference | C23 Alignment | Status |
| --- | --- | --- |
| §3.1 — C23 owns OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | C23 Charter §2 | ✅ |
| §9.4 — C25 does not generate optimization recommendations | C23-INV-OWN-001 | ✅ |
| §13.5 — Domain separation: C23 "Did prospecting work?" vs. C25 "What does evidence tell us?" | C23 Charter §1.2 | ✅ |

### 5.5 C24 Alignment

| v2.0 Reference | C24 Alignment | Status |
| --- | --- | --- |
| §3.1 — C24 owns RevenueInsight, PipelineMetric, ReplySignal, OpportunityCandidate lifecycle transitions | C24 Charter §1.1, §4, §5, §6 | ✅ |
| §5.4 — C25 workspace → Human Decision → C24 Transition Service → lifecycle mutation | C24-INV-SEP-002, C24-INV-LIFE-001 | ✅ |
| §13.2 — No candidate auto-transition; no C25 direct call to C24 Transition Service | C24 Charter §4.2, §4.3 | ✅ |

---

## 6. Self-Review Results

The charter v2.0 was self-reviewed against five mandatory questions (§19):

| # | Question | Required Answer | Actual Answer |
| --- | --- | --- | --- |
| 1 | Does C25 own commercial facts? | **No** | **No** — C25 owns presentation and interpretation. CommercialContext is a read model. Briefs are projections. Deleting them loses no facts. |
| 2 | Can C25 bypass C24 to modify lifecycle? | **No** | **No** — Correct flow: C25 Workspace → Human Decision → C24 Transition Service → lifecycle mutation. C25 has zero write paths to C24 entities. |
| 3 | Does the AI Assistant have write permissions? | **No** | **No** — C25-INV-SEC-001 enforces read-only tool capability. Enforced by tool allow-list and service layer, not prompt. |
| 4 | Does deleting all Briefs lose business facts? | **No** | **No** — Briefs are projections. Business facts reside in C20–C24 and CRM Core source artifacts. C20 provenance chain survives C25 artifact deletion. |
| 5 | Are all AI generations traceable to C20 AIJob/AIRequestLog? | **Yes** | **Yes** — C25-INV-PROV-001 requires sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion on every AI-generated C25 artifact. |

All five answers match requirements. No further revision needed.

---

## 7. Ratification Readiness

The v2.0 charter addresses all structural concerns identified in the v1.0 ratification review (`docs/audit/PHASE3C25_CHARTER_RATIFICATION_REVIEW.md`):

| v1.0 Condition | v2.0 Resolution | Status |
| --- | --- | --- |
| C-01 (Q5 — Assembly persistence) | §4 CommercialContext defined as runtime-assembled read model with caching governance | ✅ Resolved |
| C-02 (Q1 — Brief lifecycle) | §5.2 Brief redefined as immutable projection artifact; superseding supported; deletion rule established | ✅ Resolved |
| C-03 (Q2 — Assistant interface) | §6 Assistant security boundary defined with structural enforcement (tool capability + service layer) | ✅ Resolved |
| C-04 (Q3 — Workspace ownership) | §5.4 Correct flow: C25 Workspace → Human Decision → C24 Transition Service | ✅ Resolved |
| C-05 (C25-INV-INT-006) | Absorbed into C25-INV-OWN-001 (ownership boundary — no business fact ownership) and C25-INV-PROV-001 (provenance chain) | ✅ Resolved |
| C-06 (Q4 — Generation trigger) | §8 Phase 1: human-initiated only; future automation requires independent ADR | ✅ Resolved |
| Minor — advisory designation format | §5.2 Mandatory fields table specifies exact format | ✅ Addressed |
| Minor — WP3 naming | Retained "Revenue Analyst Assistant" — constraints are structural per §6, naming risk is mitigated | ✅ Accepted |

**The v2.0 charter is ready for ratification review.** All v1.0 conditions are resolved.

---

## 8. v2.1 Minor Correction Pass

### 8.1 Summary

Three minor corrections were applied to the v2.0 charter to resolve imprecise wording, add missing field-level constraints, and strengthen provenance requirements. These corrections do not change C25's scope, identity, invariants, or ownership boundaries.

| # | Correction | Sections Affected |
| --- | --- | --- |
| C1 | Human Decision Workspace — C24 invocation wording | §5.4, §9.5, §13.2, §13.4, §14.2 |
| C2 | AI Commercial Brief — field authority constraints | §5.2, §14.2 |
| C3 | AI Assistant — output provenance requirements | §6.6 (new), §14.2 |

### 8.2 Correction 1 — Human Decision Workspace C24 Invocation Wording

**Original issue (v2.0):** The v2.0 charter used imprecise language suggesting C25 must never call C24 services: "C25 never calls C24 Transition Service directly" (§5.4) and "C25 MUST NOT bypass C24 Transition Service" (§9.5). This could be misinterpreted as a prohibition on any C24 service invocation, when the actual prohibition is on bypassing C24 governance or directly mutating C24-owned data.

**Correction applied:**

Replaced "C25 never calls C24 Transition Service directly" with the precise distinction:

- **Permitted:** C25 Human Decision Workspace may invoke authorized C24 transition services through C24's governed service entry points
- **Forbidden:** C25 MUST NOT bypass C24 lifecycle governance, directly mutate OpportunityCandidate lifecycle state, or perform direct database/entity updates on any C24-owned artifact

The correct flow is updated to explicitly show "Authorized C24 Transition Service":

```text
C25 Workspace → Human Decision → Authorized C24 Transition Service → Lifecycle mutation + immutable audit
```

The forbidden path is explicitly documented:

```text
FORBIDDEN: C25 Service → Direct database/entity update on C24 artifacts
```

**Locations modified:**
- §5.4: "C25 is NOT responsible for" list, flow diagram, permitted/forbidden distinction added
- §9.5: C24 boundary rule reworded ("MUST NOT bypass C24 lifecycle governance or directly mutate C24-owned data")
- §13.2: Lifecycle transition path updated to include "Authorized C24 Transition Service"
- §13.4: Compatibility check reworded ("may invoke governed C24 service entry points; MUST NOT directly mutate C24-owned data")
- §14.2: Forbidden pattern reworded ("C25 workspace bypassing C24 lifecycle governance or directly mutating C24-owned data")

**C20–C24 compatibility impact:** None. The corrected wording better reflects the actual architectural relationship: C25 may use C24's governed services (like any well-behaved consumer layer) but must never bypass C24's governance or directly mutate C24-owned data. This aligns with C24-INV-SEP-002 (human-governed OpportunityCandidate acceptance) and C24-INV-LIFE-001 (immutable lifecycle transition records).

### 8.3 Correction 2 — AI Commercial Brief Field Authority Constraints

**Original issue (v2.0):** The v2.0 charter defined Briefs as "immutable projection artifacts — not a business authority" and enumerated what they "do not own" (Opportunity authority, Lifecycle authority, Priority authority, Revenue truth). But it did not provide explicit field-level constraints preventing Brief fields from becoming a second source of business facts.

**Correction applied:**

Added new subsection "**Field Authority Constraints**" to §5.2 with:

1. **Forbidden authority fields table:** Five field types that MUST NOT appear as authority-asserting fields:
   - Priority authority (e.g., `OpportunityPriority = High`)
   - Ranking authority (e.g., `Rank = 1`, `Score = 95`)
   - Lifecycle authority (e.g., `Recommended lifecycle stage: Qualified`)
   - Opportunity stage authority (e.g., `Suggested Stage: Negotiation`)
   - Revenue truth authority (e.g., `Forecast = $50K`)

2. **Permitted presentation forms table:** Four forms that are structurally safe:
   - Observation (e.g., `Observed market signal: High`)
   - Analysis (e.g., `AI analysis: ReplySignal confidence and engagement velocity suggest commercial interest`)
   - Explanation (e.g., `AI explanation: Historical pattern indicates stronger engagement when...`)
   - Review point (e.g., `Consider reviewing: ... Human priority assessment recommended.`)

3. **Governance rule:** "The Brief describes what the evidence shows. It does not declare what the business should do."

4. **§14.2 addition:** New forbidden pattern: "AI Brief field asserting priority, ranking, lifecycle, stage, or revenue truth authority"

**C20–C24 compatibility impact:** None. This correction strengthens the existing advisory boundary by providing concrete field-level examples of what is forbidden and permitted. It aligns with C25-INV-ADV-001 (advisory output non-authority) and C24-INV-ADV-001 (advisory revenue artifacts only). It does not change the Brief's definition as an immutable projection artifact.

### 8.4 Correction 3 — AI Assistant Output Provenance Requirements

**Original issue (v2.0):** The v2.0 charter required provenance for "AI-generated C25 artifacts" (§7.2) — sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion. However, the AI Assistant section (§6) did not explicitly require that Assistant analytical responses be traceable to specific source evidence. This left a gap: the Assistant could produce a commercial conclusion without the reader being able to trace it to the evidence it was based on.

**Correction applied:**

Added new subsection "**§6.6 Output Provenance Requirements**" with:

1. **Provenance chain per response:** Six provenance elements each Assistant response must support:
   - Source record IDs (entity type + ID)
   - Source artifact IDs (specific C20–C24 artifact references)
   - Reporting period
   - Generation timestamp
   - AIJob ID (C20)
   - AIRequestLog references (C20)

2. **Traceability requirement:** Explicit mapping from Assistant claim to source evidence:
   ```
   "Australia distributor segment shows higher response efficiency"
   → Campaign Outcome records, ReplySignal records, RevenueInsight records, PipelineMetric records
   ```

3. **Ungrounded conclusions prohibition:** Concrete examples of forbidden vs. permitted responses

4. **Provenance survival:** Provenance in C20 AIJob/AIRequestLog and source artifacts survives deletion of Assistant response

5. **§14.2 addition:** New forbidden pattern: "AI Assistant producing ungrounded commercial conclusions without source traceability"

**C20–C24 compatibility impact:** None. This correction extends the provenance requirements already established in §7.2 to specifically cover Assistant analytical responses. It aligns with C25-INV-PROV-001 (AI Explanation Provenance) and C20 ADR C8/C9 (AIRequestLog immutability). It does not change the Assistant's read-only security boundary (§6.2–6.3) or enforcement architecture (§6.4).

### 8.5 v2.1 Self-Review

The v2.1 corrections do not change any of the five self-review answers (§19). Verified:

| # | Question | v2.0 Answer | v2.1 Status |
| --- | --- | --- | --- |
| 1 | C25 owns commercial facts? | No | Unchanged ✅ |
| 2 | C25 bypasses C24 lifecycle? | No | **Strengthened** — now explicitly states C25 may invoke authorized C24 services but MUST NOT bypass governance |
| 3 | Assistant has write permissions? | No | Unchanged ✅ |
| 4 | Deleting Briefs loses facts? | No | **Strengthened** — field authority constraints reinforce projection nature |
| 5 | AI traceable to C20 AIJob/Log? | Yes | **Strengthened** — §6.6 adds Assistant-specific provenance traceability |

**Additional v2.1 verification against the correction pass requirements:**

| Question | Answer | Verification |
| --- | --- | --- |
| Can C25 invoke authorized C24 governed services? | **Yes** | §5.4: "C25 Human Decision Workspace may invoke authorized C24 transition services through C24's governed service entry points" |
| Can C25 bypass C24 to modify lifecycle? | **No** | §5.4: "C25 MUST NOT bypass C24 lifecycle governance, directly mutate OpportunityCandidate lifecycle state, or perform direct database/entity updates on any C24-owned artifact" |
| Can AI Brief become commercial fact authority? | **No** | §5.2: Forbidden authority fields (priority, ranking, lifecycle, stage, revenue truth); permitted forms (observation, analysis, explanation, review point) |
| Can Assistant output ungrounded commercial conclusions? | **No** | §6.6: "The Assistant MUST NOT produce commercial conclusions without source evidence"; provenance chain required per response |
| Does this correction change C25's original scope? | **No** | No invariants changed; no new WPs; no ownership boundary change; no identity change; C20–C24 alignment preserved |

### 8.6 C20–C24 Compatibility After v2.1

All C20–C24 boundary alignments from v2.0 remain intact. The corrections strengthen three alignments without changing any:

| Layer | Alignment Affected | Change |
| --- | --- | --- |
| C24 | C24-INV-SEP-002 (human-governed OpportunityCandidate acceptance) | **Strengthened** — Corrected flow explicitly shows Authorized C24 Transition Service; C25 may invoke it via governed entry points |
| C24 | C24-INV-LIFE-001 (immutable transition records) | **Strengthened** — Direct database/entity update from C25 is explicitly forbidden |
| C20 | C25-INV-PROV-001 (AI explanation provenance) | **Strengthened** — §6.6 adds Assistant-specific provenance traceability requirements |

No alignment was weakened. No alignment was removed.

---

*Revision notes — governance documentation only. This document authorizes no implementation, entity creation, code change, commit, push, or tag.*

*Co-Authored-By: Claude <noreply@anthropic.com>*
