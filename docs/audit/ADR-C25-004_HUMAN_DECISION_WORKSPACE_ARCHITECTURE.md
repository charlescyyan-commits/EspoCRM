# ADR-C25-004: Human Decision Workspace Architecture

| Field | Value |
| --- | --- |
| Status | DOCUMENTATION_ONLY — Draft Governance Foundation (Hardening v2); WP4 charter DRAFT maps implementation-facing name |
| Date | 2026-07-31 |
| Baseline | `phase3c25-charter-ratified` (`6e2dcf8`); prior freezes `phase3c25-wp2-2-freeze`, `phase3c25-wp3-freeze` |
| Depends On | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) §5.4, §10; `docs/audit/PHASE3C25_IMPLEMENTATION_RISK_REVIEW.md`; ADR-C25-001; ADR-C25-002; ADR-C25-006 |
| Related Invariants | `C25-INV-HG-001`, `C25-INV-OWN-001`, `C25-INV-INT-006` |
| Implementation Authorization | None — WP4 planning/implementation NOT AUTHORIZED |
| Implementation-facing name | Commercial Decision Support Layer (`docs/PHASE3C25_NEXT_WP_CHARTER.md`) |
| Freeze references | WP2.2/WP3 freezes do not authorize WP4 |

## 1. Context

C25 intelligence (workspace assembly, briefs, analytical responses) must
reach human commercial decision makers without C25 becoming a decision
owner, a lifecycle owner, or a parallel path around C24 governance. Without
an explicit architecture decision, a decision workspace could collect human
intent and then mutate C24 artifacts directly, create a second lifecycle
parallel to OpportunityCandidate, or blur the line between accepting
AI-generated intelligence and acting on it.

This ADR defines the Human Decision Workspace (WP4) structure, its C24
transition integration contract, and the human/AI division of authority. It
resolves charter open question Q3 (workspace ownership).

## 2. Decision

The Human Decision Workspace is a **C25-owned presentation surface** for
structured human commercial decision support, with integration points to
CRM Core and C24 for human-initiated decisions. C25 presents intelligence
and collects human intent; **the human decision is enacted outside C25
through the owning layer's governed service.**

C25 is responsible for:

- presenting unified commercial context (WP1, ADR-C25-001);
- presenting AI Commercial Briefs (WP2, ADR-C25-002);
- presenting analytical Q&A responses (WP3, ADR-C25-003);
- presenting AI-generated explanations and analysis; and
- collecting human intent (review decisions, action intentions).

C25 is NOT responsible for:

- modifying OpportunityCandidate state;
- creating a second lifecycle parallel to C24;
- bypassing C24 lifecycle governance; or
- directly mutating C24-owned data (direct database/entity update).

## 3. Workspace Structure

```text
┌─────────────────────────────────────────────────────────┐
│ HUMAN DECISION WORKSPACE (C25 Presentation)              │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐│
│  │ AI COMMERCIAL BRIEF  │  │ AI ASSISTANT INTERFACE     ││
│  │ (WP2)                │  │ (WP3)                      ││
│  │ Customer situation   │  │ Analytical Q&A             ││
│  │ Commercial signals   │  │ Pattern explanation        ││
│  │ Risk factors         │  │ Trend analysis             ││
│  │ Review points        │  │ Evidence references        ││
│  └─────────────────────┘  └────────────────────────────┘│
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │ UNIFIED INTELLIGENCE SURFACE (WP1)                   ││
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

## 4. C24 Transition Integration Contract

### 4.1 The Correct Flow

```text
C25 Workspace
        ↓  (present context, brief, analysis; collect human intent)
Human Decision
        ↓  (human reviews, decides action)
Authorized C24 Transition Service
        ↓  (governed transition via C24's service boundary)
Lifecycle mutation + immutable audit record
```

### 4.2 Permitted

The C25 Human Decision Workspace may invoke **authorized C24 transition
services through C24's governed service entry points**. The human decision
collected in the C25 workspace triggers a governed transition through C24's
own service boundary, preserving C24-INV-SEP-002 (human-governed acceptance)
and C24-INV-LIFE-001 (immutable transition records).

### 4.3 Forbidden

```text
FORBIDDEN:
  C25 Service → Direct database/entity update on C24 artifacts

PERMITTED:
  C25 Workspace → Human Decision → Authorized C24 Transition Service → Lifecycle mutation + immutable audit
```

C25 MUST NOT bypass C24 lifecycle governance, directly mutate
OpportunityCandidate lifecycle state, or perform direct database/entity
updates on any C24-owned artifact. All lifecycle mutation goes through
C24's authorized transition service with immutable audit.

### 4.4 C24 Dependency Boundary

C25 may present C24 information. C25 MUST NOT become a mandatory
dependency for C24 governance (Risk Review R6):

- C24 must function correctly — all transitions available, all invariants
  enforced — with C25 completely absent (R6c). Contract test: disabling
  C25 does not prevent any C24 lifecycle transition through C24's native
  UI, and all C24 invariants remain enforced (W7).
- Every transition the C25 workspace may invoke MUST have an equivalent
  C24-native UI path (W6); C25 receives no richer transition API than
  C24's native surface, and C24's transition service stays caller-agnostic
  (R6a).
- C25-initiated transitions are structurally indistinguishable from
  C24-native transitions in the C24 audit trail; the transition record
  does not encode caller identity (R6b).

```text
CORRECT:
  C25 Workspace → Human decision → C24 native governance service
                → Lifecycle mutation + immutable audit

INCORRECT:
  C25 UI → C24 lifecycle mutation (direct, bypassing C24's governed
           service boundary)
```

## 5. Human/AI Division of Authority

### 5.1 Human-Owned Decisions

| Decision Domain | C25 Role |
| --- | --- |
| Commercial interpretation | Assembles and presents evidence; AI may suggest interpretations for human review |
| Opportunity prioritization | Provides cross-artifact context, signal strength indicators, pattern comparison |
| Sales action | Provides customer situation summary, risk factors, suggested review points |
| Revenue decision | Provides RevenueInsight narratives, PipelineMetric trends, analytical Q&A |
| Forecast commitment | Provides pipeline context, trend analysis, pattern evidence |
| Pipeline strategy | Provides conversion analysis, velocity trends, ICP comparisons |
| Brief acceptance/rejection | Generates the brief with provenance, freshness, advisory designation |

### 5.2 AI Capabilities

| Capability | Status | Constraint |
| --- | --- | --- |
| Summarize commercial evidence | ✅ Permitted | Must reference sources; must declare advisory status |
| Explain patterns and trends | ✅ Permitted | Must declare limitations; must not phrase as directive |
| Analyze commercial data | ✅ Permitted | Must use governed evidence only; must declare methodology |
| Recommend review points | ✅ Permitted (advisory) | Must be phrased as observation, not command |
| Execute commercial action | ❌ FORBIDDEN | Zero automation is the structural default |
| Approve any decision | ❌ FORBIDDEN | Approval is exclusively human |
| Commit revenue or forecast | ❌ FORBIDDEN | Commitment is exclusively human in CRM Core |
| Create or modify CRM entities | ❌ FORBIDDEN | CRM Core boundary is structural |
| Trigger execution or workflow | ❌ FORBIDDEN | C22 owns all execution initiation |

## 6. Two-Gate Decision Separation

The workspace extends the C24 human governance chain with two separate,
explicit human decisions:

```text
Gate 8 (C25 WP4):  Human reviews AI Commercial Brief → ACCEPTED or DISMISSED
                   Decision: "Does this AI-generated commercial summary
                   accurately reflect the situation?"
Gate 9 (CRM Core): Human acts on commercial intelligence (outside C25)
                   Decision: "What action, if any, should we take?"
```

Gate 8 accepts the AI-generated intelligence as valid decision-support
material. Gate 9 decides what to do about it — and that decision happens in
CRM Core, outside C25 governance. The workspace MUST keep these gates
structurally separate: accepting a brief (Gate 8) has no operational side
effect and never enacts a Gate 9 action.

## 7. Workspace Audit Governance

Audit requirements for the workspace are defined as governance only — no
implementation entities are authorized (ADR-C25-006 §4).

| Rule | Requirement |
| --- | --- |
| Workspace audit events | The workspace governs audit events for: context assembled (source set and assembly version), user access (actor and timestamp), and brief/decision events per ADR-C25-006 §4. These are C25 audit events — not lifecycle records |
| Intent collection | The workspace records human review decisions (brief ACCEPTED/DISMISSED) as C25 review records — not lifecycle records |
| Transition audit | Every lifecycle mutation initiated from a workspace-collected decision is audited immutably by C24's transition service (C24-INV-LIFE-001); C25 creates no transition records |
| No parallel audit | The workspace MUST NOT log its own transition audit trail; C24's immutable transition records are the sole audit trail for all lifecycle transitions (Risk Review R4c/W3). The workspace may display C24's audit trail; it must not create a parallel one |

### 7.1 Workspace Data Budget

The workspace may store only enumerated data types (R4a/W1); anything not
enumerated is forbidden by default:

| Permitted | Constraint |
| --- | --- |
| Workspace configuration per user | Standard UI state (widgets, views, filters) |
| Workspace annotations | Bounded C25 records: no FK to CRM Core entities, no lifecycle fields, user-scoped visibility by default, auto-purge after candidate resolution (R4d/E6) |

**Forbidden by default:** viewed-brief history as a business record, Q&A
session history as an analytical record, and decision intent as a persisted
entity. Decision intent between request/response cycles lives in the user
session only — no database row, no ID, no survivability across sessions
(R4b/W2). Contract test: the workspace contains zero fields duplicating or
shadowing any C24 entity field, and zero FK references to CRM Core entities
(R4e).

## 8. Explicit Prohibitions

- No C25-owned lifecycle or second lifecycle parallel to C24.
- No direct database/entity update on any C24-owned artifact.
- No bypass of C24 lifecycle governance.
- No C25 dependency for C24 governance — C24 must fully function with C25
  absent (§4.4).
- No "Promote to Opportunity" or equivalent CRM-mutation proxy in the
  workspace.
- No AI execution, approval, commitment, entity mutation, or workflow
  trigger.
- No persisted decision intent, shadow CRM state, or workspace-owned
  transition audit trail (§7).
- No merging of Gate 8 (intelligence validity) with Gate 9 (commercial
  action).

## 9. Consequences

Future workspace implementations must route every lifecycle effect through
C24's authorized transition service; contract tests must verify zero paths
from C25 workspace services to direct C24 or CRM Core mutation. The
workspace composes WP1–WP3 surfaces under the human decision boundary and
completes the extended human governance chain (Gates 1–9). Cross-layer
read-only access detail is defined in ADR-C25-005, which this architecture
refines with workspace integration. This ADR authorizes no entity, schema,
service, API, UI, ACL, or integration implementation.
