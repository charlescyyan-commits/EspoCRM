# ADR-C25-001: Commercial Intelligence Workspace Definition

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); WP1/WP2.2/WP3 freeze baselines recorded |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); WP2.2 freeze `phase3c25-wp2-2-freeze`; WP3 freeze `phase3c25-wp3-freeze` |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft); `docs/audit/PHASE3C25_CHARTER_RATIFICATION_REVIEW.md`; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md`; ADR-C25-005 |
| Related Invariants | `C25-INV-OWN-001`, `C25-INV-ADV-001` |
| Implementation Authorization | None (invariants remain DOCUMENTATION_ONLY / not activated) |
| Freeze references | WP2.2 / WP3 freezes do not activate this ADR |

## 1. Context

C20–C24 govern the full chain from provider capability through revenue outcome,
but no layer answers the integrative question: "What does all of this evidence
tell a human commercial operator, right now?" A human operator must currently
assemble context manually across ReplySignal, OpportunityCandidate,
RevenueInsight, PipelineMetric, C23 optimization context, C22 execution
history, and C21 intelligence.

Without an explicit workspace decision, a future unified surface could drift
into persisting assembled context as a new governance record, becoming a
shadow fact store, a scoring system, or a parallel lifecycle. This ADR
establishes the workspace boundary before any C25 entity, service, or UI
exists. It resolves charter open question Q5 (CommercialContext persistence).

## 2. Decision

The C25 Commercial Intelligence Workspace (WP1) is a **unified read-only
intelligence surface**. Its assembly unit, `CommercialContext`, is a
**runtime-assembled read model — not a business entity**:

```text
CommercialContext = runtime assembled readonly view
```

CommercialContext is assembled at request time. It is not persisted as an
independent governance record. It has no lifecycle, no state machine, and no
mutation path. **Transient assembly is the default.** Caching is permitted
only under the governance rules in §5.

## 3. CommercialContext Read Model

### 3.1 Definition

`CommercialContext` is a read-only view that aggregates evidence from the full
C20–C24 chain and CRM Core for a given commercial situation. It is a lens,
not a ledger: it reads and presents; it never writes.

### 3.2 Assembly Contract

| Rule | Requirement |
| --- | --- |
| Assembly timing | At request time, on human demand (Phase 1: no event-driven or scheduled assembly) |
| Persistence | None by default; no independent governance record |
| Lifecycle | None — no states, no transitions, no state machine |
| Mutation | None — no write path from any C25 or external service |

### 3.3 Source Artifacts

| Source | Layer | C25 Relationship |
| --- | --- | --- |
| ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate | C21 | Read-only intelligence context |
| ProspectRun / ExecutionLedger outcomes, ReplyDetection | C22 | Read-only execution history for provenance |
| OptimizationInsight, PerformanceMetric | C23 | Read-only optimization context |
| ReplySignal | C24 WP1 | Read-only interpreted reply evidence |
| OpportunityCandidate | C24 WP2 | Read-only governance state and transition audit |
| RevenueInsight, PipelineMetric | C24 WP3 | Read-only analytical evidence |
| Account, Contact, Opportunity, Sales Stage | CRM Core | Read-only commercial facts |
| AIJob, AIRequestLog | C20 | Read-only provenance/cost context |

### 3.4 Structural Prohibitions

CommercialContext MUST NOT become:

- a new business-fact store (CRM Core owns business facts);
- a new scoring system (Chitu owns canonical_score; C21 governs qualification);
- a new priority authority (humans own prioritization);
- a new lifecycle system (CRM Core and C24 own their respective lifecycles); or
- a replacement for any C20–C24 governance artifact.

## 4. Workspace Presentation Rules

The workspace presents the assembled CommercialContext under four rules:

1. **Cross-artifact provenance tracing** — every presented item carries its
   source chain (e.g., ReplySignal → OpportunityCandidate → RevenueInsight →
   PipelineMetric) with entity type and ID for every source artifact.
2. **Freshness surfacing** — the workspace preserves and displays the
   freshness status of every consumed C24 artifact (CURRENT, AGING, STALE,
   ARCHIVAL per C24-INV-REV-005). STALE/ARCHIVAL warnings MUST be surfaced,
   never suppressed.
3. **Advisory designation display** — every presented artifact keeps its
   advisory designation. C25 adds its own advisory designation to assembled
   interpretations: AI-assisted assembly for human review only.
4. **No reinterpretation** — the workspace presents source interpretations
   as-is. It does not re-interpret, reclassify, or recompute any source
   artifact.

## 5. Caching and Entity Prohibition

**No CommercialContext entity (Risk Review R1/E1).** Context assembly is a
service-layer operation returning data structures, not entity objects. No
EspoCRM entity may be created for CommercialContext — no entity row, no ID,
no `status` field, no `createdBy`/ACL accretion.

If a future implementation caches an assembled CommercialContext for
performance, the cache MUST use the application cache layer (file/Redis) —
not entity storage — and MUST carry a TTL with automatic purge (R1/E2). The
cache:

**Must preserve:**

- source artifact references (entity type + ID for every assembled record);
- assembly version (identifying the assembly logic);
- generated timestamp; and
- freshness metadata (staleness status of each source artifact).

**Must not:**

- become a canonical source independent of its source artifacts;
- survive deletion of its source artifacts as an intact record;
- be writable through any C25 or external service path;
- be referenceable by ID from Briefs or any other C25 artifact (no FK
  relationships to cached contexts); or
- carry lifecycle fields of any kind.

**Deletion rule:** deleting a cached CommercialContext MUST NOT lose any
business fact. All facts reside in their source artifacts (C20–C24, CRM
Core). Deleting a projection does not delete the facts it projected. A
structural test must prove that purging all cached contexts changes no
business behavior.

## 6. Read-Only Enforcement

| Enforcement Layer | Rule |
| --- | --- |
| Service layer | C25 workspace services have zero write paths to C20/C21/C22/C23/C24/CRM Core entities |
| Contract tests | Verify the absence of create/update/delete/trigger paths — structural, not conventional |
| Trigger boundary | No scheduler, worker, webhook, event listener, or background assembly in Phase 1 |
| Cross-layer detail | Per-layer access contracts are defined in ADR-C25-005 |

## 7. Explicit Prohibitions

- No CommercialContext persistence as an independent governance record.
- No workspace-triggered workflow, automation, notification, or lifecycle
  event.
- No workspace write path to any source artifact.
- No assembled view presented without provenance, freshness, and advisory
  designation.
- No replacement of any existing C20–C24 presentation surface.

## 8. Consequences

Future C25 work packages (brief generation, assistant Q&A, decision support)
build on this read model. Any implementation must enforce request-time
assembly, provenance display, and freshness surfacing by contract test. This
ADR authorizes no entity, schema, service, API, UI, ACL, or integration
implementation. Dependent ADRs: ADR-C25-002 (brief governance), ADR-C25-003
(assistant governance), ADR-C25-005 (cross-layer read-only contracts);
ADR-C25-004 composes this workspace into the human decision surface.
