# Phase3C25 WP1 Implementation Plan — Commercial Intelligence Workspace

| Field | Value |
| --- | --- |
| Document Type | WP1 Implementation Plan |
| Work Package | WP1 — Commercial Intelligence Workspace |
| Layer | Phase3C25 — AI Commercial Intelligence Layer |
| Status | PLANNING ONLY — no implementation authorized |
| Date | 2026-07-31 |
| Baseline | Phase3C25 Implementation Foundation Review — READY (`docs/audit/PHASE3C25_IMPLEMENTATION_FOUNDATION_REVIEW.md`) |
| Primary ADRs | ADR-C25-005 (foundation); ADR-C25-001 |
| Invariants | `C25-INV-OWN-001`, `C25-INV-SEC-001`, `C25-INV-PROV-001`, `C25-INV-INT-006` |
| Deferred Gates | D2 (presentation distinction) |
| Implementation Authorization | **NONE** — no PHP, entities, metadata, services, tests, commits, pushes, or tags |

---

## 0. Purpose and Scope

WP1 provides a **governed read-only workspace** that assembles commercial
intelligence context from C20–C24 artifacts and CRM Core read-only context.
It is the read surface consumed by WP2 (Brief), WP3 (Assistant), and WP4
(Human Decision Workspace).

**Core boundary:** the C25 Workspace is a presentation and context assembly
layer. It is **not** a CRM replacement, not a commercial decision engine,
not a scoring system, not a forecast engine, and not an execution
interface.

This plan defines implementation scope, architecture boundaries, artifacts,
tests, and freeze criteria. It authorizes no code. Pre-code gates remaining
after this plan: WP1 Foundation Review and independent C20–C25 boundary
verification (Implementation Charter §14.3).

---

## 1. Context Assembly

### 1.1 Source Map

| Layer | Artifacts | C25 Relationship | Assembly Use |
| --- | --- | --- | --- |
| C21 | ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate | Read-only intelligence context | Intelligence background for a commercial context |
| C22 | ProspectCandidate, ProspectRun / ExecutionLedger outcomes, ReplyDetection | Read-only execution history | Execution provenance trail |
| C23 | OptimizationInsight, PerformanceMetric | Read-only optimization context | Prospecting effectiveness background |
| C24 | ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric | Read-only revenue evidence | Primary commercial evidence chain |
| CRM Core | Account, Contact, Opportunity, Sales Stage | Read-only commercial facts | Commercial context anchor |
| C20 | AIJob, AIRequestLog | Read-only provenance/cost context | Provenance display for AI-generated source artifacts |

### 1.2 Assembly Pattern

```text
Human request (workspace view opened)
   → authorize requester (visibility inheritance, §5)
   → read governed sources via read-only data adapters
   → assemble CommercialContext view model (runtime, transient)
   → attach provenance / freshness / advisory designations (§4)
   → render read-only workspace view
   → discard (no persistence)
```

### 1.3 Assembly Rules

| Rule | Requirement | Authority |
| --- | --- | --- |
| No mutation | Assembly performs zero writes to any source artifact, in any layer | ADR-005 §2 |
| No lifecycle control | Assembly reads lifecycle states as-is; it cannot transition, advance, or influence any lifecycle | ADR-005 §3.5/§3.6 |
| No authority transfer | Presentation of evidence transfers no ownership, priority, or decision authority to C25 or to the viewer's tools | ADR-001 §3.4 |
| Request-time only | Assembly is triggered exclusively by an explicit human request; no scheduler, worker, webhook, event listener, or background assembly | ADR-001 §6 |
| Visibility-filtered | Assembly excludes any artifact the requester cannot access at the source layer (§5) | ADR-001 §6; this plan §5 |
| No reinterpretation | Source interpretations are presented as-is; no re-interpretation, reclassification, or recomputation | ADR-005 §4 |

---

## 2. CommercialContext Boundary

### 2.1 Definition

`CommercialContext` is a **runtime read model only**. It MUST NOT become:

- a persistent entity
- a database table
- a CRM object
- a lifecycle artifact

No EspoCRM entity may be created for CommercialContext — no entity row, no
ID, no `status` field, no `createdBy`/ACL accretion (ADR-001 §5, Risk
Review R1/E1).

### 2.2 Assembly Lifecycle

| Stage | Behavior |
| --- | --- |
| Request | Human opens a workspace view; assembly begins synchronously |
| Authorize | Requester's source-layer visibility resolved (§5) |
| Read | Read-only adapters fetch governed artifacts (§1.1) |
| Assemble | View model built in memory; provenance/freshness attached |
| Render | Read-only view returned |
| Discard | View model is not persisted; request ends |

### 2.3 Cache Policy

| Rule | Requirement |
| --- | --- |
| Cache layer | Application cache only (file/Redis) — **never entity storage** (ADR-001 §5, E2) |
| TTL | Mandatory time-to-live with automatic purge |
| Referencing | Cached entries are not referenceable by ID from Briefs or any other C25 artifact; no FK relationships to cached contexts |
| Fields | Cache payload carries only: source artifact references (type + ID), source revisions, assembly version, generated timestamp, freshness metadata |
| Lifecycle fields | None — no status, no state, no ownership fields |

### 2.4 Invalidation Rules

| Mechanism | Rule |
| --- | --- |
| TTL expiry | Primary invalidation; entries auto-purge |
| Source-revision check | At request time, cached source revisions are compared with current source revisions; any mismatch forces re-assembly (no event listeners exist in Phase 1 — revision check is the freshness guarantee) |
| Source deletion | A cached context MUST NOT survive deletion of its source artifacts as an intact record (ADR-001 §5) |
| Purge safety | Purging all cached contexts changes no business behavior (structural test, §9) |

### 2.5 Freshness Handling

- Freshness states of C24 artifacts (CURRENT / AGING / STALE / ARCHIVAL,
  C24-INV-REV-005) are passed through unchanged and displayed (§4).
- STALE/ARCHIVAL warnings MUST be surfaced, never suppressed.
- C25 does not alter, extend, reset, or recompute any source artifact's
  freshness state (ADR-005 §5).

---

## 3. Workspace Components

Future components (planning definitions only):

### 3.1 Overview Panel

| Aspect | Definition |
| --- | --- |
| Purpose | Single assembled commercial picture for a given context (e.g., an OpportunityCandidate): what the governed evidence shows right now |
| Data source | WP1 assembly across C24 (ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric) + CRM Core anchor + C21–C23 background |
| Read-only rule | No actions, no edits, no state changes exposed |
| Security boundary | Visibility inheritance (§5); advisory designation on assembled interpretation; provenance/freshness per §4 |

### 3.2 Evidence Explorer

| Aspect | Definition |
| --- | --- |
| Purpose | Navigate source artifacts and their provenance chain (ReplySignal → OpportunityCandidate → RevenueInsight → PipelineMetric; upstream C22 execution history, C21 intelligence) |
| Data source | C21–C24 + CRM Core read-only adapters |
| Read-only rule | Navigation and inspection only; no mutation affordances |
| Security boundary | Per-artifact visibility checks at the source layer; links resolve only when the user has source access |

### 3.3 Commercial Signals View

| Aspect | Definition |
| --- | --- |
| Purpose | Present ReplySignal interpretations with confidence, provenance, and freshness |
| Data source | C24 WP1 ReplySignal (read-only) |
| Read-only rule | No re-interpretation, no reclassification; signals presented as-is |
| Security boundary | Advisory designation preserved; freshness warnings surfaced |

### 3.4 Revenue Insight View

| Aspect | Definition |
| --- | --- |
| Purpose | Present RevenueInsight narratives and PipelineMetric measurements with provenance, methodology, and freshness |
| Data source | C24 WP3 RevenueInsight, PipelineMetric (read-only) |
| Read-only rule | No recomputation; metrics read as-is |
| Security boundary | Staleness warnings surfaced (C24-INV-REV-005); advisory designation preserved |

### 3.5 Assistant Entry Point

| Aspect | Definition |
| --- | --- |
| Purpose | Navigation/container slot where the WP3 Assistant surface will be embedded in a later WP |
| Data source | None in WP1 (placeholder/entry only) |
| Read-only rule | WP1 provides the slot; no assistant functionality exists in WP1 |
| Security boundary | Entry point inherits workspace ACL; WP3 adds its own tool-boundary enforcement (ADR-003) |

### 3.6 Human Review Entry Point

| Aspect | Definition |
| --- | --- |
| Purpose | Navigation/container slot where WP2 Brief review surfaces will appear in a later WP |
| Data source | None in WP1 (placeholder/entry only) |
| Read-only rule | WP1 provides the slot; no brief generation or review actions exist in WP1 |
| Security boundary | Entry point inherits workspace ACL; WP2 adds its own review-gate governance (ADR-002) |

---

## 4. Provenance Display

Every displayed artifact MUST preserve and show (ADR-005 §4; the
Implementation Foundation Review requires this as a WP1 hardening item):

| Element | Requirement |
| --- | --- |
| Source artifact identity | Entity type and ID, exactly as governed by the owning layer |
| Source revision | Revision/version identifier of the artifact at assembly time |
| Freshness | Freshness state and staleness warnings, never suppressed |
| Validation state | The source artifact's own governance/review state (e.g., ReplySignal status, OpportunityCandidate lifecycle state, RevenueInsight review state) passed through unchanged |
| Evidence reference | Navigable reference from every presented item to its source record |

**No C25 rewriting of source meaning:** no reinterpretation, no
reclassification, no recomputation, and no paraphrase that alters the
advisory or factual content of a source artifact (ADR-005 §4). C25 presents
what the evidence says — it never restates what the evidence means.

---

## 5. ACL Design

### 5.1 Visibility Inheritance (Primary Rule)

**C25 cannot widen permissions.** Workspace visibility for any user is
bounded above by that user's source-layer visibility:

```text
C25-visible(user) ⊆ C21-visible(user) ∩ C22-visible(user) ∩ C23-visible(user)
                    ∩ C24-visible(user) ∩ CRM-Core-visible(user)
```

**If a user cannot access a source artifact, C25 cannot display it** — not
in a panel, not in an explorer list, not in an assembled summary, not as a
count or aggregate that reveals its content.

### 5.2 Enforcement Point

Visibility filtering happens **during assembly** (§1.2, authorize stage),
not at render time. The assembly adapters resolve the requester's
source-layer ACL per artifact class before reading.

### 5.3 User Classes

| Class | Rule |
| --- | --- |
| Internal users | Authorized commercial operator roles only; workspace access granted by explicit role assignment; source visibility per §5.1 |
| Admin | No special widening — an administrator sees in C25 exactly what their source-layer access permits (in practice, broad source access yields broad C25 visibility; the inheritance rule is unchanged); workspace configuration administration is separate from evidence visibility |
| Portal users | **No access.** The C25 workspace is an internal surface; portal roles receive no C25 scopes and no C25 routes |

### 5.4 Write ACLs

None. C25 workspace surfaces expose no create, edit, delete, or action
ACLs in WP1.

---

## 6. Presentation Boundary (D2)

### 6.1 Requirement

AI interpretation MUST be visually distinct from:

- CRM Core business records
- human decisions
- source evidence

WP1 implements the structural distinction framework that WP2 (Briefs) and
WP3 (Assistant) content will later use: distinct visual treatment, explicit
markers, and evidence navigation are built into the workspace shell now.

### 6.2 Distinction Rules

| Rule | Requirement |
| --- | --- |
| AI/assembly marker | Any C25-assembled interpretation or summary carries an explicit "AI/assembled" marker — visually distinct (styling + label), not just a text footnote |
| Boundary divider | The divider between C25-assembled interpretation and CRM Core business records is a visible structural element, not a section header |
| Advisory designation | Assembled interpretation displays an advisory designation: AI-assisted assembly for human review only |
| One-click evidence navigation | Every assembled claim or summary item links directly to its source evidence records |
| Source evidence fidelity | Source artifacts are displayed with their own native designations (§4) — never restyled to look like CRM Core business records |

### 6.3 D2 Tests

| Test | Criterion |
| --- | --- |
| D2-a | AI-assembled content renders with the distinct AI/assembled marker in every workspace panel |
| D2-b | A visible boundary divider separates C25 interpretation from CRM Core records wherever both appear |
| D2-c | One-click navigation from any assembled claim to its source evidence records works for every panel |
| D2-d | Advisory designation is visible on all assembled interpretation surfaces |
| D2-e | Source artifacts render with source-native designations (status, freshness, advisory labels) intact |

---

## 7. Potential Artifacts

### 7.1 Allowed (No ADR Amendment Needed)

| Artifact | Nature |
| --- | --- |
| Runtime view models | In-memory data structures returned by assembly services; never persisted |
| Context assemblers | Service-layer classes with read-only repository access |
| Presentation components | View/panel templates, layout metadata, navigation entries |
| Application-cache entries | TTL-governed cache payloads per §2.3 (not entities) |

### 7.2 Forbidden

| Artifact | Authority |
| --- | --- |
| CommercialContext entity | ADR-001 §5 — prohibited outright |
| Shadow CRM objects | ADR-004 §7.1; ADR-005 §3.6 |
| Duplicate lifecycle records | ADR-004 §7 — C25 creates no transition records |
| Any persistent C25 artifact | **Requires ADR amendment** plus Foundation Review approval |

### 7.3 Governed Audit Events (Advisory Note 3)

Per ADR-C25-006 §4.2, the workspace domain has governed audit events:
**context assembled** (source set + assembly version), **user access**
(actor + timestamp). WP1 records these requirements in its design;
**audit storage design is deferred** — no audit entities, tables, or
metadata are created in WP1 (ADR-006 §4.1).

---

## 8. Security Requirements

WP1 MUST NOT have:

| Prohibition | Enforcement |
| --- | --- |
| Provider calls | No provider interaction of any kind; WP1 performs no AI model invocation |
| Credential access | No credential reads; code-auditable absence |
| HTTP egress | No outbound HTTP from any WP1 code path |
| SDK ownership | No provider/vendor SDK imports |
| Autonomous actions | No scheduler, worker, queue, webhook, event listener, or background assembly; human-request-only triggers |
| Writes of any kind | Zero write paths to C20–C24, CRM Core, or any persistence beyond TTL application cache |

---

## 9. Boundary Tests

### 9.1 Cross-Layer Boundary Tests

| # | Layer | Test | Pass Criterion |
| --- | --- | --- | --- |
| B1 | C20 | No provider access | Static audit: zero provider SDK imports, zero credential reads, zero HTTP egress from WP1 code |
| B2 | C21 | No qualification mutation | Zero writes to ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate |
| B3 | C22 | No execution influence | Zero writes to ProspectCandidate, ProspectRun, ExecutionLedger, ReplyDetection; C25 data absent at ActionGate decision points |
| B4 | C23 | No optimization mutation | Zero writes to OptimizationInsight, PerformanceMetric, FeedbackLearningObservation |
| B5 | C24 | No lifecycle mutation | Zero writes to ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric; no transition calls from WP1 |
| B6 | CRM Core | No writes | No `createEntity`/`saveEntity`/lifecycle calls on CRM entities; zero FK references from any C25 artifact to CRM Core entities |

### 9.2 WP1-Specific Tests

| # | Test | Pass Criterion |
| --- | --- | --- |
| W1-1 | No CommercialContext entity | Schema/metadata audit: no C25 entity definitions exist |
| W1-2 | Cache purge safety | Purging all cached contexts changes zero business behavior |
| W1-3 | Cache confinement | Cache uses application cache layer only; TTL present; no FK references to cached contexts |
| W1-4 | Visibility inheritance | For a matrix of users with restricted source ACLs, C25 displays exactly the source-visible subset — nothing more (§5.1) |
| W1-5 | Portal restriction | Portal users have no C25 workspace access |
| W1-6 | Provenance display | Every presented artifact shows identity, revision, freshness, validation state, evidence reference (§4) |
| W1-7 | Freshness surfacing | STALE/ARCHIVAL warnings displayed; none suppressed |
| W1-8 | Presentation distinction | D2-a through D2-e (§6.3) |
| W1-9 | Human-request-only | No code path allows cron/worker/webhook/listener-triggered assembly |

---

## 10. Implementation Sequence

| Step | Deliverable | Exit Criteria |
| --- | --- | --- |
| 1. Context assembly contracts | Assembly service contracts + CommercialContext view-model structure (per ADR-001 §3, this plan §1–§2) | Contracts reviewed against ADR-001/005; no entity design present |
| 2. Read-only data adapters | Per-layer read adapters for C21/C22/C23/C24/CRM Core/C20 (§1.1) with visibility-filter hooks | Adapters expose read-only interfaces only; B1–B6 static audit clean |
| 3. Workspace views | Panels per §3 (overview, evidence explorer, signals view, revenue insight view, two entry-point slots) | Views render assembled read models; no action affordances |
| 4. ACL enforcement | Visibility-inheritance filter at assembly; role scopes; portal restriction (§5) | W1-4, W1-5 pass |
| 5. Provenance/freshness display | Provenance attachment and rendering per §4; freshness surfacing; D2 framework per §6 | W1-6, W1-7, W1-8 pass |
| 6. Boundary tests | Full test set §9 (B1–B6, W1-1…W1-9) | All tests green |
| 7. WP1 verification audit | Independent audit of WP1 against this plan, ADR-001/005, and the six invariants | Audit signed; freeze criteria §11 met |

Steps 1–2 are the foundation; steps 3–5 may iterate; step 6 gates step 7.

---

## 11. Freeze Criteria

WP1 is a freeze candidate only when **all** of the following hold:

| # | Criterion | Evidence |
| --- | --- | --- |
| F1 | **No entity created** | Schema audit: zero C25 entity definitions (W1-1) |
| F2 | **No CRM mutation path** | B5, B6 green; zero write paths anywhere in WP1 |
| F3 | **ACL inheritance verified** | W1-4, W1-5 green across the visibility matrix |
| F4 | **Provenance visible** | W1-6, W1-7 green; every presented artifact traceable to source |
| F5 | **Boundary tests pass** | B1–B6 and W1-1…W1-9 all green |
| F6 | **C25 invariants preserved** | OWN-001, SEC-001, PROV-001, INT-006 compliance signed |
| F7 | **D2 demonstrated** | D2-a…D2-e green on the WP1 surface |
| F8 | **Verification audit signed** | Step-7 audit complete; independent C20–C25 boundary verification signed (Implementation Charter §14.3 gate 3) |

---

## 12. References

- `docs/PHASE3C25_IMPLEMENTATION_CHARTER.md` (§6 WP1 scope)
- `docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md` (§2 WP1 plan)
- `docs/audit/PHASE3C25_IMPLEMENTATION_FOUNDATION_REVIEW.md` (READY; §3.1 WP1 authorization)
- `docs/audit/ADR-C25-001_COMMERCIAL_INTELLIGENCE_WORKSPACE_DEFINITION.md`
- `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md`
- `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md` (§4.2 workspace audit events)
- `docs/adr/C25_INVARIANT_REGISTRY.md`

---

*WP1 implementation planning only. This document authorizes no entity
creation, metadata modification, service implementation, test authoring,
code change, commit, push, or tag. All implementation requires the WP1
Foundation Review and independent C20–C25 boundary verification.*
