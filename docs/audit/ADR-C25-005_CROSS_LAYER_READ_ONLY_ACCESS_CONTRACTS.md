# ADR-C25-005: C25 Cross-Layer Read-Only Access Contracts

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); cross-layer consume-only confirmed at WP2.2/WP3 freeze |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); WP2.2/WP3 freezes |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) §3, §7, §9, §12; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md` — independent foundation ADR |
| Related Invariants | `C25-INV-OWN-001`, `C25-INV-SEC-001`, `C25-INV-PROV-001` |
| Implementation Authorization | None (invariants not activated) |
| Freeze references | C24/C22/CRM remain owners; C25 consumes read-only |

## 1. Context

C25 consumes evidence from six surfaces — C20, C21, C22, C23, C24, and CRM
Core. Each surface is owned exclusively by its layer. Without explicit
access contracts, a future C25 implementation could erode these boundaries:
writing to a source artifact, redefining a metric, placing C25 data at
ActionGate, coupling to CRM Core by foreign key, or invoking providers
outside C20.

This ADR defines the structural read-only access pattern for each layer,
the provenance and freshness preservation rules, and the AI provenance
chain validation required by C25-INV-PROV-001. ADR-C25-004 refines this
contract with workspace integration detail.

## 2. Decision

All C25 cross-layer access is **read-only by structure, not by convention**.
Every C25 service has zero write paths to C20/C21/C22/C23/C24/CRM Core
entities, verified by contract tests. The only governed mutation path C25
participates in is the human-decision flow through C24's authorized
transition service (ADR-C25-004 §4). C25 has no foreign-key references to
any CRM Core entity.

## 3. Per-Layer Access Contracts

### 3.1 C20 — Provider and AI Runtime

| Rule | Contract |
| --- | --- |
| Permitted | Read-only reference to AIJob and AIRequestLog as provenance/cost context |
| AI invocation | Any C25 function requiring AI model invocation MUST route through C20 capability interfaces (ADR-C20 D3) |
| Forbidden | Direct provider, credential, SDK, HTTP, or transport ownership; holding credentials (ADR-C20 §5.2); embedding model selection; bypassing C20 routing |
| Audit | Every provider invocation for a C25 generation produces C20 AIRequestLog entries (ADR-C20 C8); cost attribution through C20 cost accounting |

### 3.2 C21 — Intelligence Governance

| Rule | Contract |
| --- | --- |
| Permitted | Read-only consumption of ResearchEvidence (originated Phase3C07; governed by C21), AIQualificationInsight, HumanFeedback, IntelligenceAggregate as intelligence context |
| Forbidden | Create, modify, delete, reinterpret, or create a parallel authority for C21 intelligence; score, rank, or qualify prospects |

### 3.3 C22 — Execution Governance

| Rule | Contract |
| --- | --- |
| Permitted | Read-only consumption of execution outcomes as execution history for commercial provenance |
| Forbidden | Bypass or influence ActionGate; start or alter a ProspectRun; mutate ExecutionLedger; trigger outreach; grant execution permission |
| Isolation | C25 data MUST NOT appear at ActionGate (extends C23-INV-SEP-005 and C24 ActionGate isolation) |

### 3.4 C23 — Optimization Governance

| Rule | Contract |
| --- | --- |
| Permitted | Read-only consumption of OptimizationInsight and PerformanceMetric as prospecting effectiveness context |
| Forbidden | Redefine, overwrite, or create a competing version of C23 optimization metrics; generate optimization recommendations that replace or compete with C23 OptimizationInsight |
| Domain separation | C23: "Did prospecting work?" — C25: "What does the commercial evidence tell us?" Structurally distinct domains |

### 3.5 C24 — Revenue Operations Governance

| Rule | Contract |
| --- | --- |
| Permitted | Read-only consumption of all C24 artifacts (ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric) as evidence for commercial intelligence assembly |
| Forbidden | Mutate any C24 artifact — no status change, field update, transition execution, or lifecycle mutation; create a replacement or parallel version of any C24 artifact; bypass C24 lifecycle governance or directly mutate C24-owned data |
| Transition path | All OpportunityCandidate lifecycle transitions go through C24's authorized transition service via governed service entry points (ADR-C25-004 §4) |
| Preservation | C25 MUST preserve all C24 provenance, freshness, and advisory designations when presenting artifacts |

### 3.6 CRM Core — Lifecycle Ownership

| Rule | Contract |
| --- | --- |
| Permitted | Read-only consumption of Account, Contact, Opportunity, Sales Stage, Forecast as commercial context |
| Forbidden | Create, modify, close, reopen, stage-transition, or forecast-commit any CRM Core entity; provide a "Promote to Opportunity" or equivalent CRM-mutation proxy |
| Coupling | No C25 service, response, brief, or workspace may call `createEntity`, `saveEntity`, or any lifecycle method on a CRM Core entity; no FK references from C25 artifacts to any CRM Core entity |

## 4. Provenance Preservation Contract

When C25 presents or references any source artifact, C25 MUST preserve:

1. **Source artifact identity** — entity type and ID for every presented
   artifact, exactly as governed by the owning layer.
2. **Source revision** — the revision/version identifier of each source
   artifact at assembly time, so a presented claim is traceable to the
   exact artifact state it was derived from.
3. **Freshness information** — the freshness state and staleness warnings
   of each source artifact (§5), never suppressed.
4. **Source provenance** — methodology, source references, and generation
   context carried through unchanged.
5. **Advisory designation** — the advisory nature of every source artifact
   (C24-INV-ADV-001) is preserved in all C25 presentations.

C25 MUST NOT rewrite evidence meaning: no reinterpretation, no
reclassification, no recomputation, and no paraphrase that alters the
advisory or factual content of a source artifact. Interpretations are
presented as-is; metrics are read as-is. C25 presents what the evidence
says — it never restates what the evidence means.

## 5. Freshness Surfacing Contract

| Rule | Contract |
| --- | --- |
| Status passthrough | C25 surfaces the freshness status of consumed C24 artifacts (CURRENT, AGING, STALE, ARCHIVAL per C24-INV-REV-005) |
| Warning preservation | STALE/ARCHIVAL warnings are surfaced, never suppressed: stale evidence is never presented without a freshness warning |
| No silent refresh | C25 does not alter, extend, or reset any source artifact's freshness state |

## 6. AI Provenance Chain Validation (C25-INV-PROV-001)

### 6.1 Mandatory Provenance Fields

Every AI-generated artifact produced by C25 — AI Commercial Brief, AI
Assistant analytical response, or any future C25 AI output — MUST record:

| Field | Source | Purpose |
| --- | --- | --- |
| `sourceAIJobId` | C20 AIJob ID | Links the generation to its logical task |
| `sourceAIRequestLogId` | C20 AIRequestLog ID(s) | Links the generation to its provider invocation(s) |
| `provider` | C20 ProviderRoute → ProviderCredential | Identifies the AI provider used |
| `model` | C20 ProviderRoute | Identifies the model used |
| `generationVersion` | C25 generation logic version | Identifies the generation logic/prompt version |

The provenance model follows C20 ADR §5.4/§7: one AIJob per logical task
(invocation attempt group), one or more AIRequestLog records per provider
invocation. The rejected model — "every model call creates one AIJob" —
MUST NOT be implemented.

### 6.2 Validation Rules

- C25 AI outputs missing any of the five provenance fields are invalid;
  validators MUST reject them.
- Every referenced AIJob MUST be traceable in C20.
- Every referenced AIRequestLog MUST exist in C20 (ADR-C20 C8).
- Provenance fields MUST survive brief supersession (ADR-C25-002 §6).
- Deleting a C25 artifact MUST NOT delete or alter C20 provenance records;
  the chain is independent of C25 artifact lifecycle.

### 6.3 Enabled Capabilities

This chain enables audit (every AI conclusion traces to a specific provider
invocation), cost attribution (token/cost through C20), reproducibility
(same inputs + model + generation version), and explainability.

## 7. Contract Test Expectations

Future implementations must verify by contract test:

1. zero write paths from any C25 service to any C20–C24 or CRM Core entity;
2. no C25 data present at C22 ActionGate decision points;
3. no credential, provider SDK, or HTTP egress ownership in C25 code;
4. no FK references from C25 artifacts to CRM Core entities;
5. freshness and advisory designations preserved on all presented
   artifacts; and
6. provenance validation per §6.2 on every AI-generated C25 artifact.

## 8. Explicit Prohibitions

- No write, mutation, or trigger path to any C20–C24 or CRM Core entity.
- No C25 data at ActionGate.
- No direct provider calls, credential access, or model selection.
- No metric redefinition or competing optimization authority.
- No reinterpretation, reclassification, or recomputation of source
  artifacts.
- No AI-generated output without the five-field provenance chain.
- No FK coupling to CRM Core entities.

## 9. Consequences

These contracts bind every C25 work package: the workspace (ADR-C25-001),
briefs (ADR-C25-002), assistant (ADR-C25-003), and decision surface
(ADR-C25-004) all consume source layers exclusively under these rules.
Contract tests per §7 are the activation mechanism for C25-INV-OWN-001,
C25-INV-SEC-001, and C25-INV-PROV-001 upon implementation. This ADR
authorizes no entity, schema, service, API, UI, ACL, or integration
implementation.
