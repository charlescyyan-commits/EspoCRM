# Phase3C25 WP2 Implementation Charter — AI Commercial Brief

| Field | Value |
| --- | --- |
| Document Type | Work-Package Implementation Charter |
| Work Package | WP2 — AI Commercial Brief |
| Parent Layer | Phase3C25 — AI Commercial Intelligence Layer |
| Status | RATIFIED — implementation planning authorized; code implementation not authorized |
| Date | 2026-07-31 |
| Baseline | Phase3C25 WP1 Final Freeze Review PASS (`docs/audit/PHASE3C25_WP1_FINAL_FREEZE_REVIEW.md`); C25 Implementation Charter (`docs/PHASE3C25_IMPLEMENTATION_CHARTER.md`); C25 Implementation Foundation Plan (`docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md`) |
| Predecessor | Phase3C25 WP1 — Commercial Intelligence Workspace (FROZEN, tag `phase3c25-wp1-freeze`) |
| Depends On | C20 (ACTIVE), C21 (FROZEN), C22 (FROZEN), C23 (FROZEN), C24 (FROZEN), C25 WP1 (FROZEN) |
| Primary ADRs | ADR-C25-002 (AI Commercial Brief Governance); ADR-C25-005 (Cross-Layer Read-Only Access); ADR-C25-006 (Confidence / Audit / Feedback) |
| Invariants | `C25-INV-ADV-001`, `C25-INV-HG-001`, `C25-INV-PROV-001`, `C25-INV-INT-006` (owning); `C25-INV-OWN-001`, `C25-INV-SEC-001` (constraining) |
| Deferred Gates | D3/OQ1 (invalidation), D4/OQ2 (minimum evidence), D5/OQ3 (governed deletion), D7/OQ5 (brief-specific C20 purpose binding) |
| Implementation Authorization | **NO** — this document authorizes no code, no entity, no metadata, no test, no C20 change, no ProviderRoute, no commit, no push, no tag |

> **Amendment record (2026-07-31):** amended after independent review
> (verdict: PASS WITH REQUIRED AMENDMENTS). Merged amendments: four-layer
> authorization model + capability matrix (§15.4–§15.5, §16.1); REST/API
> surface decision frame (§5.2, §16.2); mandatory per-claim masking default
> (§8.2, §15.3, OQ-A); review-audit persistence boundary (§13.1, OQ-B);
> OpportunityCandidate anchor finalization (§5.3, §6.1, §20); factual and
> citation corrections (§2, §6.4, §9.1–§9.2, §10.2–§10.4, §18.1, §23–§25);
> SUPERSEDED derivation semantics (§12); idempotency-key clarification
> (§17.1); C20 dependency boundary reaffirmed (§10). WP2 Implementation Plan
> authoring is permitted only upon ratification of this amended Charter
> (§27.1); code implementation remains **NO**.

> **Amendment record (2026-08-01):** lifecycle-split amendment after
> reconciliation review (verdict: REQUIRED AMENDMENT). Replaced the single
> `status` field with three orthogonal fields — `reviewStatus`
> (`GENERATED` / `REVIEWED` / `ACCEPTED` / `DISMISSED`),
> `validityDisposition` (`NONE` / `INVALIDATED`), and
> `retentionDisposition` (`ACTIVE` / `ARCHIVED`) — with `SUPERSEDED`
> derived from `supersedesBriefId` and governed deletion a delete path,
> not a status value (§6.1–§6.2, §12, §14, §16.1, §19, §24–§26, §27.1).
> Fixed reconciliation LOW findings L1 (independent Audit attribute per
> action in §16.1), L2 (Implementation Plan authoring gated on
> ratification), L3 (three C20-governed readiness dependencies), and L4
> (`allowed_provider_bindings` / binding-level purpose eligibility
> terminology). A1–A6 remain unchanged. Ratified on 2026-08-01
> (RATIFIED WITH NON-BLOCKING NOTES); see the Ratification record below.

> **Ratification record (2026-08-01):**
> - Review type: Final Ratification Review
> - Verdict: RATIFIED WITH NON-BLOCKING NOTES
> - Lifecycle: PASS — reviewStatus / validityDisposition / retentionDisposition split approved
> - A1–A6: PASS — no regression
> - C20 dependency (status at the time of this record): NOT FULLY SATISFIED —
>   later superseded for foundation-gate purposes by the ratified C20 closure
>   evidence; implementation remains separately unauthorized
> - Implementation Plan: AUTHORIZED
> - Code implementation: NOT AUTHORIZED
> - Required next document: `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md`
> - Ratification scope: Ratification authorizes planning only and does not authorize CommercialBrief entity creation, C20 changes, tests, AI invocation, scheduler/worker changes, commit, push, or tag.
> - Review evidence: Final Ratification Review completed in read-only repository review session on 2026-08-01.

> **Governance alignment amendment (2026-08-06):** C20 Dependency Closure
> Amendment ratified at `b632f1d` (`RATIFIED WITH INFORMATIONAL NOTES`). For
> the C25 WP2 foundation gate, the prior D-3 requirement of
> `INV-05…11 ACTIVE` is superseded by **Capability identity + Purpose policy +
> Boundary evidence**. C20 runtime invariants remain deferred and the C20
> invariant registry remains the runtime status authority. This amendment
> authorizes no WP2 implementation, generation runtime, provider call, or
> deployment.

> **Administrative synchronization note (2026-08-06):** Historical WP2.2
> records exist in the repository (`PHASE3C25_WP2_2_*` and
> `docs/audit/PHASE3C25_WP2_2_*`). They are **HISTORICAL / SUPERSEDED** and
> do not change the state asserted here: WP2 implementation remains **NOT
> AUTHORIZED**; Any Code remains **NOT AUTHORIZED**. See
> `docs/PHASE3C25_WP2_AUTHORIZATION_STATE_SYNCHRONIZATION.md`.
>
> **Amendment record (2026-08-06) — WP2.1B Implementation Authorization
> issued:** `docs/PHASE3C25_WP2_1B_IMPLEMENTATION_AUTHORIZATION.md` grants
> WP2.1B implementation **AUTHORIZED WITH CONDITIONS** (CommercialBrief
> persistence layer only). This charter authorizes no code itself; the
> WP2.1B authorization is the separate record referenced above. WP2
> implementation remains otherwise **NOT AUTHORIZED**.

---

## 1. Purpose and Scope

This charter defines the **authorized implementation scope** of Phase3C25
WP2 — the **AI Commercial Brief** (`CommercialBrief`). WP2 transforms the
ratified C25 governance artifacts (C25 Charter §5.2, ADR-C25-002,
ADR-C25-005, ADR-C25-006, C25 Invariant Registry) into a single
work-package implementation specification: the persistent, immutable
advisory projection artifact that presents WP1-assembled CommercialContext
as human-reviewable commercial intelligence briefs.

WP2 is **scope specification only**. It states what may be built, what is
forbidden, which decisions are already resolved by ratified governance, and
which decisions still require ratification — it does **not** build anything.

The core artifact of WP2 is an **advisory projection**, not a business
authority:

```text
WP2 CommercialBrief =
  persistent · immutable projection
  of governed commercial evidence (C20–C24 + CRM Core, read-only)
  produced only by explicit human request
  carrying mandatory advisory + legal designation
  with a human-review lifecycle
  →  DECISION_SUPPORT_MATERIAL_ONLY
```

Every rule in this charter derives from ratified sources (section 2). Where
this charter resolves an open question, it records the resolution and the
governance source; where it cannot, it records an open question and a
ratification gate (section 26).

---

## 2. Governing Documents

This charter is subordinate to, and must be read against, the following
frozen / ratified governance:

| # | Document | Role |
| --- | --- | --- |
| G1 | `docs/PHASE3C25_CHARTER_DRAFT.md` (v2.1-draft) | C25 parent charter; §5.2 WP2 product definition; §8 generation trigger policy; §10 human governance chain (Gate 8) |
| G2 | `docs/PHASE3C25_IMPLEMENTATION_CHARTER.md` | Authorized implementation scope; WP2 (§7); deferred gates §10; forbidden scope §12; invariants §13 |
| G3 | `docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md` | Per-WP plan; WP2 (§3) allowed/potential artifacts, services, metadata, ACL, security risks, boundary tests, freeze criteria |
| G4 | `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md` | **Primary WP2 ADR** — brief as immutable projection, mandatory fields, forbidden fields, immutability/supersession/deletion, human review gate |
| G5 | `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md` | Cross-layer read-only contracts; provenance preservation; AI provenance chain validation |
| G6 | `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md` | Confidence elements; audit requirements (governance only); feedback separation |
| G7 | `docs/audit/ADR-C25-001_COMMERCIAL_INTELLIGENCE_WORKSPACE_DEFINITION.md` | WP1 read model; CommercialContext assembly contract (WP2 consumes) |
| G8 | `docs/audit/ADR-C25-003_REVENUE_ANALYST_ASSISTANT_GOVERNANCE.md` | WP3; referenced for parallel-WP boundary only |
| G9 | `docs/audit/ADR-C25-004_HUMAN_DECISION_WORKSPACE_ARCHITECTURE.md` | WP4; Gate 8/Gate 9 separation; D2 presentation (WP2 feeds) |
| G10 | `docs/adr/C25_INVARIANT_REGISTRY.md` | Six formal invariants (OWN-001, ADV-001, HG-001, SEC-001, PROV-001, INT-006) |
| G11 | `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | C20 capability ports, ProviderRoute model, AIJob/AIRequestLog/PromptTemplate, invariants §8 |
| G12 | `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md` | **Frozen C20 Capability Registry Resolution contract** — the routing mechanism WP2 depends on |
| G13 | `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | CompletionProvider capability portfolio + forbidden capabilities + `CompletionRequest`/`CompletionResult` contract |
| G14 | `docs/adr/C20_INVARIANT_REGISTRY.md` | C20-INV-01…22 (esp. INV-03, 05–14) |
| G15 | `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md` | C24 OpportunityCandidate lifecycle (IDENTIFIED → REVIEW_PENDING → ACCEPTED → ACTIVE → WON/LOST) — read-only anchor for WP2 |
| G16 | `docs/adr/C24_INVARIANT_REGISTRY.md` | C24-INV-SEP-001/002, LIFE-001, ADV-001, HG-001/002, MET-001/002, REV-001…005 |
| G17 | `docs/audit/PHASE3C25_WP1_FINAL_FREEZE_REVIEW.md` | WP1 frozen state: routes, services, ACL, no-write matrix — the foundation WP2 consumes |
| G18 | `docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md` | WP1 implementation plan (frozen reference) |
| G19 | `docs/adr/C21_INVARIANT_REGISTRY.md`, `docs/adr/C22_INVARIANT_REGISTRY.md`, `docs/adr/C23_INVARIANT_REGISTRY.md` | Predecessor boundary invariants (read-only consumption) |

**Note on a required reference:** the required-document list names
`docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_REGISTRY_FREEZE.md`; the
file that exists is `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
(frozen 2026-07-29 at `c898dc7`). All citations herein use the existing
path (G12). The capability-port complement is G13
(`docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`).

---

## 3. Explicit Non-Goals

WP2 explicitly does **not** deliver, and no rule in this charter may be read
to authorize:

| Non-Goal | Owner | Rationale |
| --- | --- | --- |
| A new `ProviderRoute` entity or any C20 entity | C20 | ProviderRoute is C20-owned configuration `(capability, purpose) → provider + model` (G11 §4.2.7, §6.1). WP2 reuses C20 Capability Registry Resolution — it does not build routing (section 10). |
| A new C20 capability / `CompletionCapability` value added by C25 | C20 | Adding a brief-generation capability value is C20-governed. WP2 proposes; C20 ratifies and implements (section 10). |
| Any C20 `AIJob` / `AIRequestLog` / `PromptTemplate` mutation | C20 | WP2 creates AIJob + AIRequestLog only through C20's own services/guards. WP2 records provenance references, never writes C20 records itself. |
| Lead / Opportunity / Account / Quote / Revenue or any CRM Core record creation | CRM Core | C22-INV-CRM-001, C24-INV-REV-003, G11 §8.15. Briefs create no CRM records. |
| OpportunityCandidate creation or lifecycle transition | C24 | C24-INV-SEP-002, C24-INV-LIFE-001. WP2 reads candidates; never transitions (section 20). |
| ActionGate influence, outreach, email send, execution trigger | C22 | C22-INV-EX-001; C25 data must not appear at ActionGate (extends C23-INV-SEP-005). |
| Scoring / ranking / probability / forecast / revenue-impact authority | Chitu / CRM Core / Human | C20-INV-14/16/21; C25-INV-ADV-001; ADR-C25-002 §5. Briefs carry no authority fields. |
| Autonomous / scheduled / batch / event-driven / unattended generation | C25 | C25 Charter §8; G2 §7.6; section 22. Human-initiated only. |
| A new queue architecture | C20 | WP2 reuses C20 `AIJob` lifecycle for governed-async execution (section 11). No new workers, brokers, or schedulers. |
| A review entity (`BriefReviewEvent`) or audit entity (`BriefAudit`) as a public business record | C25 (gated) | ADR-C25-006 §4 is requirements-only; Foundation Plan §3.3 requires an ADR amendment for any audit/review entity. WP2 uses a governed append-only audit mechanism (section 13). |
| Partial / incomplete brief persistence | C25 | Default rejects incomplete briefs (section 18). |
| Reading prior briefs as generation context | C25 | ADR-C25-002 §6 — each brief is a fresh projection of governed evidence. |
| WP1 frozen files modification | C25 | This charter references WP1 artifacts; it modifies none. |

---

## 4. CommercialBrief Product Definition

### 4.1 Definition

An **AI Commercial Brief** is a persistent, immutable projection artifact —
an AI-generated, human-reviewable summary of governed commercial evidence at
a point in time, produced only by explicit human request, carrying mandatory
advisory and legal designation, and governed by a human-review lifecycle
(G1 §5.2; G4 §2).

```text
Human request (explicit; no scheduler / worker / webhook / listener)
        │
        ▼
BriefGenerationService
  1. assemble CommercialContext (via WP1, requester's source ACL)
  2. invoke C20 CompletionProvider through C20 AIJob (governed async)
  3. validate (mandatory fields, provenance, forbidden fields, evidence)
  4. persist CommercialBrief (reviewStatus GENERATED) — immutable content
        │
        ▼
Human review lifecycle  GENERATED → REVIEWED → ACCEPTED | DISMISSED
   (reviewStatus — ACCEPTED and DISMISSED are terminal review outcomes;
    reviewStatus is never overwritten by supersession, invalidation,
    archival, or governed deletion)
   Orthogonal post-generation dispositions:
     validityDisposition   NONE → INVALIDATED  (does not change reviewStatus)
     retentionDisposition  ACTIVE → ARCHIVED   (does not change reviewStatus)
     SUPERSEDED            derived from supersedesBriefId (never persisted)
   ACCEPTED = DECISION_SUPPORT_MATERIAL_ONLY (Gate 8)
   Gate 9 (commercial action) happens outside C25
```

### 4.2 Product Properties

| Property | Rule | Source |
| --- | --- | --- |
| **Advisory** | Decision-support material only; not a forecast, commitment, or decision | G1 §5.2; G4 §2; C25-INV-ADV-001 |
| **Immutable projection** | Content, provenance, source references, and designation never change after generation | G4 §6; C25-INV-PROV-001 |
| **Persistent** | Survives its request; queryable under brief ACL (not a transient response) | G2 §7; G3 §3.1 |
| **Revisioned** | Changed interpretation requires a new superseding revision (`supersedesBriefId`) created by an explicit human regeneration request | G4 §6; C20 supersession precedent G11 §6.4 |
| **Human-gated** | Each brief requires individual human review; ACCEPTED/DISMISSED are human decisions | G1 Gate 8; G4 §7; C25-INV-HG-001 |
| **Zero-side-effect** | ACCEPTED creates no AIRequestLog, no CRM/C24/C22/C20 side effect | G4 §7.1; ADR-C25-006 §4.3; section 13 |
| **Deletion-safe** | Deleting all briefs loses no business fact; provenance survives deletion | G4 §6; C25-INV-PROV-001 |
| **Scoped** | Excluded from standard CRM lists and global search without explicit "include AI projections" toggle; portal denied | G4 §8 (B5); section 19 |

### 4.3 What an Accepted Brief Does NOT Mean

| `ACCEPTED` means | `ACCEPTED` does NOT mean |
| --- | --- |
| Human accepts the brief as valid decision-support material | Commercial approval |
| `acceptanceScope: "DECISION_SUPPORT_MATERIAL_ONLY"` | Execution approval |
| Gate 8 in the extended human governance chain | OpportunityCandidate transition |
| A governed append-only audit event | CRM Opportunity creation |
| Decision-support input to WP4 (ADR-C25-004) | Forecast commitment |
| | Work-prioritization authority |
| | Gate 9 (commercial action) — which happens outside C25 |

---

## 5. Artifact and Entity Contract

### 5.1 Entity and Scope Naming (Resolved)

| Question | Resolution |
| --- | --- |
| Formal entity name | **`CommercialBrief`** |
| Formal scope name | **`CommercialBrief`** (record scope) |
| Module | **`CommercialIntelligence`** (same module as WP1; entity under `Espo\Modules\CommercialIntelligence\Entities\CommercialBrief`) |
| Display name | **AI Commercial Brief** |
| Human-readable designation | `AI-generated commercial summary — for human review only. Not a forecast, commitment, or decision.` (G4 §4, verbatim) |
| Machine-readable designation | `legalDesignation` = `AI-GENERATED_ADVISORY_PROJECTION_NOT_A_COMMERCIAL_DECISION` (G4 §4, constant) |

### 5.2 Entity-Level Contract

| Attribute | Rule |
| --- | --- |
| Scope flags | `object: false`, `tab: false` — mirrors the existing persistent governed-entity patterns in C24 (incl. `OpportunityCandidate` and `RevenueInsight`, both `object: false`, `tab: false`, `acl: true`, `aclActionList: ["read"]`). WP1 `CommercialIntelligenceWorkspace` is an `entity: false` shell and is **not** the persistence-scope precedent |
| `acl: true` | Own record ACL (G3 §3.6); `aclActionList: ["read"]` only — **no generic create/edit/delete** |
| Portal | **Denied** — `aclPortal` mandatory false; `isPortal()` Forbidden (extends WP1 portal denial) |
| Standard lists / global search | Excluded without explicit "include AI projections" toggle (G4 §8 B5) |
| REST / API surface | Deterministic choice (section 16.2): **Option A (preferred)** — standard Espo Record controller with `aclActionList: ["read"]`, reads ACL-controlled, create/edit/delete forbidden by ACL and metadata; **Option B (gated)** — dedicated controller reusing EspoCRM `Acl` and this charter's action keys. All business changes via governed action keys only |
| FK to CRM Core | **None** (G5 §3.6; no FK coupling to any CRM Core entity) |
| Lifecycle review/disposition fields | `reviewStatus`, `acceptanceScope`, `outcomeReason`, `validityDisposition`, `retentionDisposition` (§6.1, §12.2); `readOnly: true` except through the dedicated transition/disposition service + action key + guard + save option (G11 §6.5 pattern); each change writes an append-only audit event |
| Entity budget | Exactly **one** persistent C25 artifact type in WP2: `CommercialBrief` (G3 §7.5). No `BriefFeedback`, `BriefAudit`, `BriefReviewEvent`, cache-row, or session entity in this WP (each requires ADR amendment) |

### 5.3 Anchor (Resolved)

Every `CommercialBrief` is anchored to a single C24 `OpportunityCandidate`
(the commercial context anchor), mirroring the WP1 workspace anchor
(`ContextAssemblyService::assembleForCandidate`, G17 §3):

- `opportunityCandidateId` is a **read-only structured reference/link** to
  the C24 `OpportunityCandidate` — the **formal business anchor** of the
  brief, not free-text provenance.
- C25 does **not** own the `OpportunityCandidate` lifecycle, and the link
  MUST NOT be used to invoke any C24 transition service (section 20).
- Soft-deletion, invisibility, or non-existence of the anchor
  `OpportunityCandidate` MUST NOT cascade-delete the `CommercialBrief`;
  historical briefs retain the anchor ID and their generation-time
  provenance.
- When the current anchor is unreadable to a reader, the workspace renders
  **unavailable / restricted** — no source content is leaked (sections 15,
  19).
- **No** write-type FK from `CommercialBrief` to CRM Core `Lead`,
  `Opportunity`, `Account`, `Quote`, or `Revenue` (G5 §3.6).
- A free-text `provenanceReference` MUST NOT substitute for the local core
  anchor.

---

## 6. Field Categories and Forbidden Fields

### 6.1 Field Categories (Resolved)

| Category | Fields | Mutable? | Guard |
| --- | --- | --- | --- |
| **Standard (system)** | `id`, `createdAt`, `createdBy`, `deleteId` | Immutable (system-owned) | System |
| **Anchor / scope** | `opportunityCandidateId` — read-only structured reference/link to the C24 `OpportunityCandidate` (formal business anchor, §5.3) | Immutable | Immutability guard |
| **Generation content** | `reportingPeriod`, `generatedAt`, `generationVersion`, `customerSituation`, `commercialSignals`, `riskFactors`, `suggestedReviewPoints` | **Immutable** | Immutability guard; generation-only write |
| **Source references** | `sourceEvidence[]` (per source: `entityType`, `entityId`, `revision`, `freshnessAtGeneration`), `evidenceSetHash` (derived) | **Immutable** | Immutability guard; generation-only write |
| **Provenance** | `sourceAIJobId`, `sourceAIRequestLogId`, `provider`, `model`, `generationVersion` (shared above), `promptTemplateId`, `promptTemplateVersion` | **Immutable** | Immutability guard; provenance-completeness validator |
| **Designation** | `advisoryDesignation` (fixed text), `legalDesignation` (fixed constant) | **Immutable** | Constant-value validator |
| **Review outcome and dispositions** | `reviewStatus` (`GENERATED` / `REVIEWED` / `ACCEPTED` / `DISMISSED`), `acceptanceScope`, `outcomeReason`, `validityDisposition` (`NONE` / `INVALIDATED`), `invalidationReason` or corresponding audit-only reason decision, `retentionDisposition` (`ACTIVE` / `ARCHIVED`), `archiveReason` or corresponding audit-only reason decision | **Mutable only via governed review/disposition transition** | Review-status guard + save option (reviewStatus); disposition guards + save options (validity / retention); append-only audit guard for every change (G11 §6.5 four-part pattern) |
| **Supersession** | `supersedesBriefId` (set once at creation) | Immutable once set | Immutability guard; supersession validator |

Review/disposition field rules:

- Whether `invalidationReason` / `archiveReason` are stored as current
  disposition summary fields on the brief or recorded **only** in the
  append-only audit is decided by the Implementation Plan; both records
  carry actor, timestamp, reason, action key, brief ID, and
  `AIJob`/`AIRequestLog` provenance reference where applicable.
- **Mutable JSON history is forbidden** — review/disposition history never
  accumulates inside a JSON field on `CommercialBrief` (§13.1).
- `acceptanceScope` is meaningful **only** when
  `reviewStatus = ACCEPTED`; `DISMISSED`, `INVALIDATED`, and `ARCHIVED`
  must never carry or fabricate an `acceptanceScope`.

### 6.2 Which Fields Are Permanently Immutable

**Permanently immutable** (never modified after generation):

- generated content (four sections, `reportingPeriod`, `generatedAt`)
- source references (`sourceEvidence[]`)
- `evidenceSetHash`
- anchor reference (`opportunityCandidateId`)
- AI provenance (`sourceAIJobId`, `sourceAIRequestLogId`)
- `promptTemplateId` / `promptTemplateVersion`
- provider/model provenance (`provider`, `model`)
- advisory / legal designation
- `generationVersion`
- `supersedesBriefId` (set once at creation)

**Mutable only through a governed action** (never generic CRUD):

- `reviewStatus`
- `acceptanceScope`
- `outcomeReason`
- `validityDisposition`
- `retentionDisposition`
- limited current-disposition summary fields, if the Implementation Plan
  retains them (e.g., an `invalidationReason` / `archiveReason` summary),
  subject to the §6.1 rules

Every mutable field above is changed exclusively through **action
authorization + transition/disposition service + save option + guard +
append-only audit** (§14). `acceptanceScope` and `outcomeReason` are set
atomically with their review transition and are not editable thereafter.
There is **no** user-editable field and **no** generic update path on
`CommercialBrief` (G4 §6; section 14).

### 6.3 Forbidden Fields (Resolved)

Schema-level exclusion (G4 §5; G2 §7.3; not convention):

| Forbidden Field | Rationale |
| --- | --- |
| `score` / any numeric score | Chitu owns `canonical_score`; C20-INV-14 |
| `priority` | Human owns prioritization |
| `ranking` / `rank` | Human owns ranking; brief is not an ordering surface |
| `probability` / `closeProbability` | Commercial outcomes are not AI-predictable |
| `revenueImpact` | CRM Core / C24 own revenue facts |
| `forecast` / `commit` | CRM Core / human own forecast commitment |
| `stage` / `lifecycleStage` | C24 / CRM Core own lifecycle |
| `isCurrent` / `isLatest` / any editable `superseded` boolean | Superseded disposition is derived from the supersession graph, never stored as a mutable flag (§12.2) |
| Any field asserting decision, approval, or execution authority | C25-INV-ADV-001 |

Forbidden-field exclusion extends to natural-language equivalents: summary
judgments (`High`, `Strong`, `Top`) without evidence anchoring are forbidden
as de facto scores (G4 §5 proxy prohibition). Every observation must be
evidence-anchored to source records.

### 6.4 Field Decision: Prompt / Model / Provider / Completion Metadata (Resolved)

| Question | Decision |
| --- | --- |
| Save a prompt snapshot? | Store `generationVersion` (C25 generation-logic version) **and** `promptTemplateId` + `promptTemplateVersion` (C20 `PromptTemplate` immutable reference). **Do not duplicate prompt text in the brief.** The full prompt is retrievable from C20 by version (G11 §8 inv. 9; G13 §6.1). |
| Save model identifier? | **Yes** — `model` (from C20 route resolution) as a provenance field, consistent with the associated `AIRequestLog` (G4 §4; C25-INV-PROV-001). |
| Save provider identifier? | **Yes** — `provider` (from C20 route resolution) as a provenance field, consistent with the associated `AIRequestLog` (G4 §4; C25-INV-PROV-001). |
| Save completion metadata? | **No duplication.** Tokens, cost, and latency live in the current C20 `AIRequestLog` (append-only cost truth, G11 §8 inv. 8, §5.5). The current `AIRequestLog` does **not** persist `finish_reason`; content-filter outcomes are expressed as `AIJob` FAILED + `failureCategory = CONTENT_FILTER` (section 18). The brief stores only `sourceAIRequestLogId` reference(s); cost/latency are read from C20 when displayed. C25 never copies the raw completion payload, prompt text, or provider-private metadata into the brief. |

---

## 7. Content Structure

Every brief contains exactly four advisory sections (G4 §3; G1 §5.2):

| Section | Content |
| --- | --- |
| **Customer Situation** | Synthesized context about the prospect, their organization, and relevant intelligence |
| **Commercial Signals** | Interpreted evidence of commercial interest, intent, or opportunity |
| **Risk Factors** | Identified risks, gaps in evidence, or areas requiring human attention |
| **Suggested Review Points** | Advisory prompts for human commercial evaluation — phrased as observations, never directives |

### 7.1 Content Rules

- Every observation is **evidence-anchored** to source records (G4 §5):
  "3 ReplySignals within 14 days; all classified COMMERCIAL_INQUIRY" —
  never summary-level judgments functioning as scores.
- Every brief carries the **four confidence elements** (G6 §3.1): evidence
  basis, confidence indication (qualitative, evidence-anchored), freshness
  consideration, and a first-class limitation statement.
- Suggestions are phrased as observations ("Consider reviewing…", never
  "The pipeline should…").
- Briefs contain **no** execution directives, CRM mutation commands, or
  forecast commitments (G4 §7).

---

## 8. Source Reference and Evidence Model

### 8.1 Source Evidence Set

Each brief records, for every source artifact consumed at generation:

| Field | Meaning |
| --- | --- |
| `entityType` | Owning layer artifact type (e.g., `ReplySignal`, `OpportunityCandidate`, `RevenueInsight`, `PipelineMetric`, `ResearchEvidence`, `AIQualificationInsight`, `ExecutionLedger`, CRM Core read context) |
| `entityId` | The artifact's ID |
| `revision` | Source artifact revision at assembly time (G5 §4.2) |
| `freshnessAtGeneration` | Freshness status snapshot (CURRENT / AGING / STALE / ARCHIVAL per C24-INV-REV-005) at generation |

`evidenceSetHash` = deterministic hash over the **canonicalized** `(entityType,
entityId, revision)` tuples with a stable sort order. It is immutable and
serves idempotency (section 17) and freshness-change detection (section 12).

### 8.2 Evidence Rules

- The source evidence set is the **complete** set of governed artifacts the
  generation consumed — no subsetting that hides an evidence basis.
- Source original content is **never copied** into the brief (section 21).
  Only entityType + entityId + revision + freshness are stored as
  references.
- Minimum evidence gate (D4): ≥ 1 governed source artifact; artifact chain
  complete before generation (G2 §7.6; G3 §3.7).
- Evidence-anchored language: every claim maps to source record references
  (G4 §5) through a **structured claim → source reference mapping** — the
  mandatory basis for read-time per-claim masking when a reader loses
  source ACL (section 15.3).

---

## 9. Provenance Contract

### 9.1 Mandatory Provenance Fields

Every `CommercialBrief` MUST record (G4 §4; G5 §6; C25-INV-PROV-001):

| Field | Source | Purpose |
| --- | --- | --- |
| `sourceAIJobId` | C20 `AIJob` | Logical task that produced this generation |
| `sourceAIRequestLogId` | C20 `AIRequestLog` ID(s) | Provider invocation(s) for this generation |
| `provider` | C20 route resolution | Provider used (via C20); must match the associated `AIRequestLog` |
| `model` | C20 route resolution | Model used; must match the associated `AIRequestLog` |
| `generationVersion` | C25 generation logic | Generation logic / prompt version |
| `promptTemplateId` | C20 `PromptTemplate` | Immutable template identity used for generation |
| `promptTemplateVersion` | C20 `PromptTemplate` | Immutable template version; with `promptTemplateId` the full prompt is retrievable from C20 by version (G11 §8 inv. 9; G13 §6.1) |

### 9.2 Provenance Rules

- A brief missing any provenance field is **invalid**; validators reject it
  before persistence (G4 §4; G5 §6.2).
- Beyond the five basic provenance fields (`sourceAIJobId`,
  `sourceAIRequestLogId`, `provider`, `model`, `generationVersion`),
  **`promptTemplateId` and `promptTemplateVersion` are mandatory additional
  immutable provenance fields** (§6.1, §6.4).
- `provider` / `model` are provenance copies **validated for consistency
  with the associated `AIRequestLog`** record(s); they are never an
  independently editable configuration surface.
- Every referenced `AIJob` / `AIRequestLog` MUST exist in C20 (G11 §8 inv. 8;
  G5 §6.2).
- Provenance survives **supersession** and **brief deletion**; the chain is
  independent of brief lifecycle (G4 §6; G5 §6.2; C25-INV-PROV-001).
- The C20 model is one `AIJob` per logical task, one or more `AIRequestLog`
  rows per provider invocation (G1 §7.1; G5 §6.1). The rejected
  "one AIJob per model call" model MUST NOT be implemented.
- Human **acceptance does not create an AIRequestLog**: review / acceptance /
  dismissal / invalidation are C25 append-only governance events that
  reference the brief's existing `AIJob` / `AIRequestLog` provenance
  (G6 §4.3; section 13). No provider invocation occurs on review.

---

## 10. C20 Capability and Invocation Dependency Decision (Resolved)

### 10.1 Verdict

```text
C20 Capability Registry Resolution:  SUFFICIENT — reused, not replaced
New ProviderRoute entity:            NOT REQUIRED — C20-owned configuration
New CompletionCapability value:      REQUIRED — but a C20-governed addition,
                                     NOT a C25-created capability or entity
C25 WP2 invocation dependency:        NOT FULLY SATISFIED TODAY —
                                     three C20-governed readiness
                                     dependencies listed in §10.3
```

### 10.2 What Is Already Sufficient

- The frozen **Capability Registry Resolution contract**
  (`CapabilityResolutionRequest` / `CapabilityResolutionResult`, G12,
  `CapabilityRegistry.resolve()` at `c898dc7`) already performs candidate
  eligibility filtering, deterministic ranking, fallback recording
  (`fallback_occurred`, `resolution_reason`), safe metadata output, and
  fails-closed `CAPABILITY_UNAVAILABLE`. The resolution-level `Capability`
  enum includes **`COMPLETION`** (`capabilities.py`), and `AIJob.capability`
  accepts `["SEARCH", "ENRICHMENT", "COMPLETION"]` — brief generation maps
  to the **COMPLETION** capability family.
- The **`CompletionProvider`** protocol + adapter exist and are authorized
  (G13; §11.1 ratified Option C). `CompletionRequest` / `CompletionResult`
  are normalized, carry cost envelopes and idempotency keys, and enforce the
  §4.3 error taxonomy (incl. `CONTENT_FILTER`, `QUOTA`).
- **`AIJob`, `AIRequestLog`, `PromptTemplate`** entities, services, guards,
  and save options exist in `Modules/AIPlatform` (verified in the tree:
  `Resources/metadata/entityDefs/AIJob.json` — `AIJob` is currently a
  **metadata-defined entity with no dedicated PHP entity class** —
  `Services/AIJobService.php`, `Hooks/AIJob/AIJobStatusMutationGuard.php`,
  `Entities/AIRequestLog.php`,
  `Hooks/AIRequestLog/AIRequestLogAppendOnlyGuard.php`,
  `Entities/PromptTemplate.php`, etc.), plus `ProviderCredential.json`
  metadata.
- **ProviderRoute / ProviderBinding** is C20-owned configuration
  `(capability, purpose) → provider + model` (G11 §4.2.7, §6.1; G12 §5.1).
  C25 must **not** create, own, or mutate it.

### 10.3 Ratified C20 Foundation Gate

The prior WP2.0 dependency assessment identified three C20-governed
readiness dependencies. The C20 Dependency Closure Amendment and its
ratification now close the governance requirements for C25 WP2 foundation
review through the following evidence set:

**Capability identity + Purpose policy + Boundary evidence**

1. **Capability identity.** `COMMERCIAL_BRIEF` is available as the governed
   capability identity for foundation consumption. C25 consumes the identity;
   it does not own the C20 capability registry or add a capability value.
2. **Purpose policy.** `commercial_brief_generation` is available as a
   policy purpose with classification and eligibility reference. Provider
   execution is not enabled.
3. **Boundary evidence.** ProviderBinding purpose-policy alignment,
   capability mapping, eligibility classification, and provenance contract
   are available for governance review. C25 does not own routing, credentials,
   binding mutation, or dispatch.

C20-INV-05…11 remain runtime maturity items with their registry status
unchanged. They are not required to be ACTIVE for the WP2 foundation gate and
must not be represented as activated by C25. Later runtime verification,
invariant activation, and Runtime Expansion remain separately governed.

### 10.4 Prohibited Actions Under This Section

- **Do not** create a `ProviderRoute` entity from C25.
- **Do not** add the `CompletionCapability` value from C25.
- **Do not** modify C20 capability resolution, `CompletionProvider`, or any
  C20 entity.
- **Do not** decide the `ProviderBinding` database or UI form from C25.
- **Do not** implement provider routing or dispatch in C25.
- **Do not** hold provider, model, credential, SDK, or transport ownership in
  C25 (C20 boundary; C25-INV-SEC-001).

WP2.0 (C20 Dependency Resolution, section 23) remains the governed vehicle
for recording the closure evidence and is the **hard precondition** for any
generation implementation. Its foundation gate is now satisfied by the
ratified evidence set above; implementation remains separately unauthorized.

---

## 11. Human-Initiated Runtime Model

### 11.1 HUMAN_REQUEST_ONLY ≠ Synchronous Blocking (Resolved)

"Human-request-only" constrains **who** initiates generation — it does not
force the execution model to be synchronous and blocking. An explicit human
request MAY trigger:

| Mode | Description | Authorization |
| --- | --- | --- |
| **Synchronous** | Brief generation completes within the request cycle (short generations only) | Human-initiated; no background execution |
| **Governed asynchronous** | The human request dispatches a **C20 `AIJob`** (`QUEUED → RUNNING → SUCCEEDED/FAILED`), operator-visible and operator-recoverable (`aiJob.retry` / `aiJob.cancel`), surfaced to the requester as a pending generation | Human-initiated; reuses C20 AIJob lifecycle (G11 §7) |

Both modes are **explicit-human-trigger only**. WP2 **does not** introduce a
new queue architecture, worker, scheduler, or message broker — it reuses the
C20 `AIJob` lifecycle when async execution is chosen.

### 11.2 Trigger Rules

| Allowed | Forbidden |
| --- | --- |
| Human clicks "Generate Commercial Brief" (sync or governed-async) | Scheduler / cron |
| Human submits a regeneration request (new revision) | Event listener / webhook |
| Human retries a failed generation via C20 `aiJob.retry` | Batch / unattended generation |
| | Autonomous loop / auto business action |

### 11.3 Invocation Path

```text
Human requester
  → BriefGenerationService (C25)
      → ContextAssemblyService (WP1) — requester's source ACL filter
      → CompletionRequest (capability=COMMERCIAL_BRIEF*,
                            purpose=<C25 brief purpose>,
                            structured context, idempotencyKey)
      → C20 AIJob dispatch (via C20 capability interface)
      → AIJob SUCCEEDED → CompletionResult
      → BriefValidationService → persist CommercialBrief
* proposed name only; after the C20-governed capability addition
  (section 10.3.1)
```

C25 holds **no** credentials, **no** provider/model selection, and **no**
transport (C20 boundary; G5 §3.1; C25-INV-SEC-001).

---

## 12. Lifecycle and Revision Model

### 12.1 Lifecycle (Resolved)

```text
Review lifecycle (reviewStatus — four values only):
   REQUESTED          (human request event — NOT a persisted field value)
      │  generation completes + validates
      ▼
   GENERATED          (immutable content persisted; reviewStatus = GENERATED)
      │  human reviews
      ▼
   REVIEWED
      │  human decides
      ├──────────────► ACCEPTED   (acceptanceScope = DECISION_SUPPORT_MATERIAL_ONLY)
      └──────────────► DISMISSED  (outcomeReason required)
   ACCEPTED and DISMISSED are terminal review outcomes. reviewStatus is
   NEVER overwritten by supersession, invalidation, archival, or governed
   deletion.

Orthogonal post-generation dispositions (coexist with reviewStatus; they
do NOT overwrite it):
   validityDisposition:   NONE → INVALIDATED  (governed; reason + actor +
                            timestamp + append-only audit; no side effects)
   retentionDisposition:  ACTIVE → ARCHIVED   (retention / presentation path;
                            reason + actor + timestamp + append-only audit;
                            archive ≠ delete)
   Superseded:            derived at read time from supersedesBriefId +
                            creation ordering — never a persisted value
   Governed deletion:     deleteId / governed soft-delete path — NOT a
                            reviewStatus or disposition value

Expressed without reviewStatus transitions:
   reviewStatus remains ACCEPTED; validityDisposition becomes INVALIDATED
   reviewStatus remains ACCEPTED; retentionDisposition becomes ARCHIVED

Superseded disposition (derived — NOT a status):
   An explicit human regeneration request creates a new revision whose
   supersedesBriefId references the prior brief. The prior brief keeps its
   original reviewStatus, validityDisposition, and retentionDisposition
   unchanged; its superseded disposition is derived at read time from the
   supersession chain (G11 §6.4 precedent).
```

### 12.2 Lifecycle Field Model — Three Orthogonal Fields (Resolved)

The single `status` field is replaced by three orthogonal fields:

| Field | Enum | Rules |
| --- | --- | --- |
| `reviewStatus` | `GENERATED` / `REVIEWED` / `ACCEPTED` / `DISMISSED` | `GENERATED → REVIEWED → ACCEPTED` or `DISMISSED`; `ACCEPTED` and `DISMISSED` are terminal review outcomes; never overwritten by supersession, invalidation, archival, or governed deletion; changed only via dedicated transition service + action key + save option + guard |
| `validityDisposition` | `NONE` / `INVALIDATED` | Default `NONE`; `INVALIDATED` withdraws decision-support validity (e.g., source error, source withdrawal, generation error, other D3 governance reason); does **not** modify `reviewStatus`; requires reason, actor, timestamp, and append-only audit; no automatic source change, regeneration, or C24 / CRM Core / C22 side effect |
| `retentionDisposition` | `ACTIVE` / `ARCHIVED` | Default `ACTIVE`; `ARCHIVED` is a retention and presentation disposition, **not** a review outcome; does **not** modify `reviewStatus` or `validityDisposition`; archive eligibility per D5 / retention policy (default: terminal review outcome or invalidated records only); requires reason, actor, timestamp, and append-only audit; archive ≠ delete and does not modify `deleteId`, provenance, or the supersession graph |

- `REQUESTED` is the human request **event** (audit), not a field value.
- `SUPERSEDED` is **not** a value of `reviewStatus`,
  `validityDisposition`, or `retentionDisposition`, and never an editable
  flag: it is **derived at read time** from the supersession graph
  (`supersedesBriefId` chain) and creation ordering (G11 §6.4 precedent).
- When a new revision supersedes a prior brief, the prior brief keeps its
  original `reviewStatus`, `validityDisposition`, and
  `retentionDisposition` **unchanged**.
- `isCurrent`, `isLatest`, and any editable `isSuperseded` / `superseded`
  boolean field are **forbidden** (§6.3); the current revision is computed
  from the supersession graph and creation ordering, never stored as a
  mutable flag.
- Dispositions coexist: a brief may simultaneously be `ACCEPTED` +
  `INVALIDATED` + `ARCHIVED` + superseded-derived; presentation labels
  never overwrite one another (§19).
- Creating a superseding brief is always an **explicit human regeneration
  request** (section 22); it is never automatic.
- All `reviewStatus` / disposition changes are the **only** mutations on
  the brief and occur exclusively through the dedicated
  transition/disposition service + action key + guard + save option (G11
  §6.5 four-part pattern), each with an append-only audit event.

### 12.3 Regeneration vs Supersession vs Invalidation vs Retention (Resolved)

| Concept | Definition | Content mutation? | Source evidence effect |
| --- | --- | --- | --- |
| **Regeneration** | A **new human-initiated generation** producing a new revision (new `CommercialBrief` row) | No (prior untouched) | None |
| **Supersession** | The reference link from the new revision to the prior revision (`supersedesBriefId`); prior brief preserved **with its reviewStatus, validityDisposition, and retentionDisposition unchanged** and visually de-emphasized at read time; provenance survives | No | None |
| **Invalidation** | Governed withdrawal of decision-support validity (e.g., a source is found wrong); sets `validityDisposition = INVALIDATED` via the transition service; `reviewStatus` unchanged; reason, actor, timestamp, and append-only audit required | No | None — source evidence unaffected |
| **Retention / archival** | `retentionDisposition = ARCHIVED` via governed action; `reviewStatus` and `validityDisposition` unchanged; governs long-term retention and governed deletion (D5) | No | None |

No regeneration, supersession, invalidation, or archival is automatic; each
is an explicit governed human action (section 22).

---

## 13. Review Event and Append-Only Audit Model

### 13.1 Decision: Governed Append-Only Audit Mechanism (Resolved)

Review events are recorded through a **governed append-only audit
mechanism** in the C25 module — **not** a new public business entity. The
`CommercialBrief` content record itself MUST NOT become a mutable audit
container.

**Explicitly forbidden:**

- A **mutable JSON append field** on `CommercialBrief` holding review
  history;
- Appending audit entries through an **ordinary entity update**;
- Creating an `AIRequestLog` for human accept/dismiss — no provider
  invocation occurs on review (§9.2; G6 §4.3);
- Creating a **user-editable second business entity** for review/audit
  without an ADR amendment (ADR-C25-006 §4 is requirements-only; Foundation
  Plan §3.3 lists `BriefAudit` / `BriefFeedback` as requiring an ADR
  amendment).

**Allowed persistence boundary (priority order):**

1. **Reuse the existing Espo audit/stream infrastructure**, provided it can
   guarantee: append-only; actor; timestamp; action key; from/to state;
   reason; `acceptanceScope`; brief ID; source `AIJob`/`AIRequestLog`
   provenance reference; and **no modification and no deletion path**.
2. **If — and only if — the existing audit/stream infrastructure cannot
   guarantee the above**, the Implementation Plan may design an internal
   append-only review-audit storage that:
   - is **not** a normal CRM scope;
   - does **not** enter navigation, lists, or global search;
   - grants **no** ordinary CRUD;
   - is written **atomically by the transition service**;
   - and whose status as a potential new first-class entity MUST be decided
     by an **ADR judgment before implementation** (ratification gate,
     section 26).

### 13.2 Audit Event Contract (ADR-C25-006 §4.2)

| Domain | Events | Required content |
| --- | --- | --- |
| Brief | generation; review; acceptance/dismissal; feedback; invalidation; supersession; archival; deletion | generation: C20 `AIJob`/`AIRequestLog` linkage; review + acceptance/dismissal: actor, timestamp, `acceptanceScope`, from/to `reviewStatus`; feedback: actor, timestamp, feedback reference; invalidation: actor, timestamp, reason, from/to `validityDisposition`; archival: actor, timestamp, reason, from/to `retentionDisposition`; deletion: actor, timestamp, reason, `deleteId` reference |

### 13.3 Audit Rules

- **Append-only** — events are recorded once and never updated (G6 §4.3).
- **Not business facts** — audit records create no commercial truth
  (C25-INV-INT-006).
- **Not lifecycle records** — C25 audit never substitutes for or parallels
  C24's immutable transition records (G6 §4.3; G9).
- **No AIRequestLog on acceptance** — human acceptance/dismissal/invalidation
  are C25 append-only governance events referencing the brief's existing
  `AIJob` / `AIRequestLog` provenance; they are **not** provider invocations
  and create **no** new C20 `AIRequestLog` (G6 §4.3; correction).
- **Provenance continuity** — the acceptance event links to the brief's C20
  provenance chain, making "AI generated → human accepted" traceable end to
  end (G6 §4.3).
- **Independence** — deleting C25 audit records affects no C20–C24 or CRM
  Core artifact.

### 13.4 Feedback

Human feedback on a brief (usefulness, clarity, explanation quality) is
C25-scoped, is **not** C21 `HumanFeedback`, never drives automation or truth
changes, and never auto-regenerates (G6 §5; G4 §7.2). Any regeneration is a
new human-initiated generation. Feedback events are audit events.

---

## 14. Immutability Enforcement

### 14.1 Precise Immutability Definition (Resolved)

| Component | Immutable? | Enforcement |
| --- | --- | --- |
| Brief **content** (four sections, reporting period, timestamps) | **Immutable** | `CommercialBrief` immutability guard rejects any field save not carrying the transition save option |
| **Provenance** (sourceAIJobId, sourceAIRequestLogId, provider, model, generationVersion, promptTemplateId, promptTemplateVersion) | **Immutable** | Same guard; provenance validator at write |
| **Source references** (sourceEvidence[], evidenceSetHash) | **Immutable** | Same guard |
| **Advisory / legal designation** | **Immutable** | Constant-value validator; no write path |
| **Lifecycle review/disposition fields** (`reviewStatus`, `acceptanceScope`, `outcomeReason`, `validityDisposition`, `retentionDisposition`) | **Mutable only via dedicated transition/disposition service + action key + guard + save option + append-only audit** | `BriefLifecycleTransitionService` owns all review/disposition writes; review-status guard + save option and disposition guards + save options reject stray `saveEntity` (G11 §6.5 four-part pattern) |
| **Review audit** | **Append-only** | Append-only audit guard + audit save option (section 13) |
| **Regeneration** | New revision via `supersedesBriefId`; **never overwrite** the original record | Supersession validator; no update path |

### 14.2 Enforcement Stack

1. **Schema**: all content/provenance/reference/designation fields `readOnly`;
   only the review/disposition fields are writable and only via the governed
   transition/disposition service.
2. **Hook guard**: `BriefStatusMutationGuard` on `CommercialBrief` rejects any
   save without the authorized save option (review/disposition mutation);
   disposition guards reject disposition writes without the corresponding
   save option; the immutability guard rejects any content-field change.
3. **Save option**: `BriefStatusMutationSaveOption` is the only authorized
   review-status write channel; disposition save options are the only
   authorized disposition-write channels (G11 §6.5).
4. **Transition service**: `BriefLifecycleTransitionService` is the single
   owner of all reviewStatus transitions and disposition changes, with action
   keys registered in workflow metadata and bound through the existing
   authorization pattern (G11 §5.3, §7.3).
5. **Append-only audit**: every review/disposition change writes an
   append-only audit event (§13).
6. **Contract tests** verify the absence of any other mutation path
   (section 24).

---

## 15. ACL and Authorization Model

### 15.1 Three-Way ACL Distinction (Resolved)

WP2 distinguishes three visibility domains — they are governed separately and
must not be conflated:

| Domain | Owned by | Visibility rule |
| --- | --- | --- |
| **Source original content visibility** | Owning source layer (C20–C24, CRM Core) | Read-only passthrough; governed source navigation re-checks **native source ACL at every read** (WP1 `GetGovernedSourceDetail` pattern; denied → safe 404). C25 never widens it. |
| **Persisted AI-derived brief content visibility** | C25 (`CommercialBrief` ACL) | Scoped to authorized commercial operators / reviewers; no widening beyond the brief's own ACL; **no verbatim source content stored** (section 21). |
| **Provenance reference visibility** | C20 + C25 | Reference-level (entityType + entityId + provenance) under brief read ACL; C20 `AIJob`/`AIRequestLog` read per C20 ACL (G11 §5.3: AIRequestLog read-only for managers). |

### 15.2 ACL Behavior by Time (Resolved)

| Time | Behavior |
| --- | --- |
| **Generation time** | Input sources are filtered to the **requesting user's source ACL** (visibility inheritance, G5 §4; G3 §2.6). Sources the requester cannot read never enter the assembly; the brief is generated **only from evidence the requester can see**. |
| **Storage time** | The brief stores generated synthesis + source references (entityType + entityId + revision + freshness) + provenance. **Source original content is never copied into the brief** — no unauthorized source text is persisted. |
| **Read time** | Brief renders per C25 brief ACL. Every source reference is a **live ACL-checked navigation** (denied → safe 404 / restricted placeholder). Freshness and provenance display is reference-level only. |
| **Review time** | Reviewer must hold brief read ACL (re-checked at review time); references re-checked; claims anchored to now-inaccessible sources are masked (§15.3). |

### 15.3 When a User Loses Source ACL — Mandatory Per-Claim Masking Default (Resolved)

Because every brief claim is **evidence-anchored to source records** (G4 §5;
§8.2), per-claim masking is implementable and is the **mandatory default**
for the Implementation Plan:

- The `CommercialBrief` content model MUST include a **structured claim →
  source reference mapping**.
- When the current reader cannot read a source, every claim bound to that
  source renders a **restricted-evidence** marker.
- The masked rendering MUST NOT expose source original text, sensitive
  fields, or restricted information inferred from them.
- Source navigation returns a **safe not-found / forbidden** presentation
  that does not reveal whether the record exists.
- Claims independently supported by sources the reader can still read
  remain visible.
- **Whole-brief restriction** is permitted only as a conservative fallback
  when claims cannot be safely separated.
- "Keep the full claim and only show a risk marker" is **NOT** an allowed
  default — it leaks facts into AI-derived text that the reader could not
  see at the source (G1 §9.5; G5 §3.5).

The brief is never a channel to bypass source ACL.

### 15.4 Four Authorization Layers (Resolved)

WP2 authorization separates four layers. **No layer substitutes for
another.**

| Layer | Rule |
| --- | --- |
| **1. Record visibility** | `CommercialBrief` read is controlled by EspoCRM entity ACL (`acl: true`, `aclActionList: ["read"]`). The anchor `OpportunityCandidate` read is controlled by the C24 source-layer ACL. Source-evidence visibility is always re-checked against the source-layer ACL at read time (§15.1). |
| **2. Business action authorization** | `generate`, `regenerate`, `review`, `accept`, `dismiss`, `invalidate`, `archive`, and `delete` each carry an **independent action key** (§16.1). Action authorization uses **existing EspoCRM ACL / workflow authorization primitives only** (G11 §5.3, §7.3). **No parallel permission system** may be created, and services MUST NOT hardcode role names. |
| **3. State integrity** | Every `reviewStatus` / disposition change passes through the dedicated transition/disposition service + action key + save option + guard + append-only audit (§14). Action authorization does **not** substitute for the state-integrity guard, and record ACL does **not** substitute for the transition/disposition guard. |
| **4. Source visibility prerequisite** | `generate` / `regenerate` require the requester to hold read access to the anchor `OpportunityCandidate` **and** to every source record used in that generation. `review` / `accept` / `dismiss` re-check the current reviewer's brief read ACL. Source navigation performs a **live** source ACL check. Portal is denied by default. **Admin does not bypass** reason, audit, transition, or source-leakage rules. |

### 15.5 Capability Matrix

Capabilities are authorization **categories**, not role names hardcoded in
services. The Implementation Plan MUST map each capability to existing Espo
Role, ACL, and action authorization configuration (§27.1).

| Capability | Granted action keys | Brief read | Provenance view | Portal |
| --- | --- | --- | --- | --- |
| **Commercial Brief Operator** | `brief.generate`, `brief.regenerate`, `brief.archive` | ✅ under brief ACL | ✅ permitted C20 provenance, bounded by C20 ACL + source ACL | ❌ denied |
| **Commercial Brief Reviewer** | `brief.review`, `brief.accept`, `brief.dismiss`, `brief.invalidate` | ✅ re-checked at review time | ✅ same bound | ❌ denied |
| **Governed Deletion** | `brief.delete` (reason + actor + timestamp + audit record mandatory) | ✅ | ✅ | ❌ denied |
| **Provenance Viewer** | — (read-only) | per brief ACL | ✅ permitted C20 provenance only; still bounded by C20 ACL and source ACL | ❌ denied |
| **Admin** | all keys — but **no bypass** of reason, audit, transition, or source-leakage rules | ✅ | ✅ | ❌ denied |
| **Portal user** | — | ❌ | ❌ | ❌ denied |

Generate/regenerate, review, accept, dismiss, invalidate, archive, and delete
are **explicit action-keyed operations** (section 16) — not generic CRUD.

---

## 16. API / Action Surface

### 16.1 Action Keys and Action Matrix (Registered in Workflow Metadata)

Every business action is an explicit action-keyed operation bound through
the existing EspoCRM ACL / workflow authorization pattern (G11 §5.3, §7.3);
unauthorized attempts return 403 with zero writes. No parallel permission
system is created; services MUST NOT hardcode role names (§15.4 layer 2).

| Attribute | `brief.generate` | `brief.regenerate` | `brief.review` | `brief.accept` | `brief.dismiss` | `brief.invalidate` | `brief.archive` | `brief.delete` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Transition / effect** | Human-initiated generation → create brief with `reviewStatus = GENERATED` | New human-initiated revision; sets `supersedesBriefId` on the new revision; prior brief's `reviewStatus`/dispositions unchanged | `reviewStatus`: `GENERATED → REVIEWED` | `reviewStatus`: `REVIEWED → ACCEPTED`; `acceptanceScope` required; `validityDisposition` remains `NONE`; `retentionDisposition` remains `ACTIVE` | `reviewStatus`: `REVIEWED → DISMISSED`; `outcomeReason` required | Sets `validityDisposition = INVALIDATED`; `reviewStatus` unchanged; reason required; no automatic regeneration; no C20 `AIRequestLog`; no C24 / CRM Core / C22 side effects | Sets `retentionDisposition = ARCHIVED`; `reviewStatus` unchanged; `validityDisposition` unchanged; reason required | Governed soft-delete path (`deleteId`); **not** a `reviewStatus` or disposition transition; actor + reason + audit required |
| **Required entity ACL** | None (creation via service; generic create forbidden) | Brief read | Brief read (re-checked) | Brief read (re-checked) | Brief read (re-checked) | Brief read | Brief read | Brief read |
| **Required capability** | Commercial Brief Operator | Commercial Brief Operator | Commercial Brief Reviewer | Commercial Brief Reviewer | Commercial Brief Reviewer | Commercial Brief Reviewer | Commercial Brief Operator | Governed Deletion |
| **Source ACL prerequisite** | Requester reads anchor + **all** sources used (live) | Same as generate (live re-check) | Reviewer brief-read re-check; source refs live-checked at navigation | Same as review | Same as review | — (reason cites source issue) | — | — |
| **Ownership / team rule** | Requester scope per Espo record ACL (owner/team) | Same | Per Espo record ACL (owner/team) | Same | Same | Same | Same | Same |
| **Transition service** | `BriefGenerationService` (creation channel) | `BriefGenerationService` | `BriefLifecycleTransitionService` | `BriefLifecycleTransitionService` | `BriefLifecycleTransitionService` | `BriefLifecycleTransitionService` (validity disposition) | `BriefLifecycleTransitionService` (retention disposition) | `BriefLifecycleTransitionService` governed-deletion path |
| **Save option** | Generation save option (single creation channel) | Generation save option | `BriefStatusMutationSaveOption` | `BriefStatusMutationSaveOption` | `BriefStatusMutationSaveOption` | Disposition save option (validity) + audit write | Disposition save option (retention) + audit write | Deletion save option + audit write |
| **Guard** | Immutability + provenance-completeness validators; generation guard | Supersession validator + immutability guard | `BriefStatusMutationGuard` | `BriefStatusMutationGuard` | `BriefStatusMutationGuard` | `BriefStatusMutationGuard` (reviewStatus unchanged) + validity-disposition guard + audit guard | `BriefStatusMutationGuard` (reviewStatus unchanged) + retention-disposition guard + audit guard | Governed-deletion guard + audit guard |
| **Portal behavior** | Denied | Denied | Denied | Denied | Denied | Denied | Denied | Denied |
| **Admin behavior** | No bypass of source-ACL / audit rules | Same | No guard bypass | No guard bypass | Reason + actor + timestamp + audit mandatory | Reason + actor + timestamp + audit mandatory | Reason + actor + timestamp + audit mandatory | Reason + actor + timestamp + audit mandatory |
| **Reason required** | No | No | No | No (scope fixed) | **Yes** | **Yes** | **Yes** | **Yes** |
| **Forbidden side effects** | No CRM/C24/C22 writes; C20 writes only via C20 services; no autonomous trigger; no prior-brief reads | Never overwrite prior revision; explicit human request only; no auto-regeneration | No content mutation; no AIRequestLog; no CRM/C24/C22 writes | **Zero side effects** — no AIRequestLog, no CRM/C24/C22/C20 record changes | Same as accept | `reviewStatus` unchanged; no automatic regeneration; no C20 `AIRequestLog`; no C24 / CRM Core / C22 side effects; source evidence unaffected; no content mutation | `reviewStatus` / `validityDisposition` unchanged; retention path only; no content mutation; no `deleteId` change; provenance and supersession graph intact | Provenance survives; no source-record cascade; no erasure of the audit trail |
| **Audit** | Event `brief.generate`; actor; timestamp; action key; from/to: — → `reviewStatus=GENERATED`; reason: n/a; acceptanceScope: n/a; brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.regenerate`; actor; timestamp; action key; from/to: — → new revision (`reviewStatus=GENERATED`) with `supersedesBriefId` to prior revision; reason: n/a; acceptanceScope: n/a; brief IDs (prior + new); `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.review`; actor; timestamp; action key; from/to: `reviewStatus` `GENERATED → REVIEWED`; reason: n/a; acceptanceScope: n/a; brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.accept`; actor; timestamp; action key; from/to: `reviewStatus` `REVIEWED → ACCEPTED`; reason: n/a (per Implementation Plan); acceptanceScope: required; brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.dismiss`; actor; timestamp; action key; from/to: `reviewStatus` `REVIEWED → DISMISSED`; reason: `outcomeReason` required; acceptanceScope: n/a (forbidden); brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.invalidate`; actor; timestamp; action key; from/to: `validityDisposition` `NONE → INVALIDATED` (`reviewStatus` unchanged); reason required; acceptanceScope: n/a (forbidden); brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.archive`; actor; timestamp; action key; from/to: `retentionDisposition` `ACTIVE → ARCHIVED` (`reviewStatus` / `validityDisposition` unchanged); reason required; acceptanceScope: n/a (forbidden); brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only | Event `brief.delete`; actor; timestamp; action key; from/to: — (`deleteId` governed soft-delete path; no `reviewStatus`/disposition transition); reason required; acceptanceScope: n/a; brief ID; `AIJob`/`AIRequestLog` provenance reference; append-only; audit trail preserved |

Guard and save-option names above follow the G11 §6.5 four-part pattern.
The Implementation Plan maps `reviewStatus` and each disposition to the
corresponding guard + save option (review-status guard/save option;
validity- and retention-disposition guards/save options) without inventing
a parallel authorization framework (§15.4). The Audit row is the
per-action minimum; it does **not** replace the global audit rules in
section 13.

### 16.2 Surface Contract — REST/API Decision Frame (Amended)

The earlier absolute statement that `CommercialBrief` is "not part of
standard REST collections" is **replaced** by the following decision frame.
The WP2 Implementation Plan MUST make a deterministic choice between:

**Option A — preferred: the repository's existing governed-entity pattern
(C24 precedent, e.g. `OpportunityCandidate`, `RevenueInsight`):**

- Standard Espo Record controller;
- `aclActionList: ["read"]`;
- the standard GET/read collection is used **only** for ACL-controlled
  reads;
- create/edit/delete are forbidden by ACL and metadata;
- all business changes flow exclusively through the governed action keys
  and services of §16.1.

**Option B — dedicated controller, permitted only when the standard Record
controller cannot satisfy B5, security, or the presentation boundary:**

- MUST reuse EspoCRM `Acl`;
- MUST reuse this charter's action keys;
- **no** parallel CRUD;
- **no** parallel identity, role, or security model;
- the Implementation Plan MUST document why the existing C24 pattern is
  insufficient.

Exclusion from standard lists, navigation, and global search is achieved
through: `object: false`; `tab: false`; search metadata; the explicit
"include AI projections" filter/toggle; and workspace-specific presentation
(section 19). **"Not discoverable in the ordinary UI" is not equivalent to
"all standard read APIs must be disabled."**

Unchanged constraints:

- Read: brief detail, brief list (scoped, non-standard), governed source
  navigation (WP1 `GetGovernedSourceDetail`, 16-type allowlist).
- Write: generation request + review actions only — all human-initiated and
  action-keyed; POST only for these, GET-only elsewhere.
- Portal: denied (G4 §8; WP1 portal denial).

---

## 17. Idempotency and Duplicate Prevention

### 17.1 Deterministic Idempotency Key (Resolved)

`idempotencyKey = H( anchorCandidateId
                    | evidenceSetHash
                    | generationVersion
                    | briefPurpose
                    | requesterId )`

`evidenceSetHash` is the immutable hash over canonicalized, stably sorted
source `(entityType, entityId, revision)` tuples (section 8.1). The key is
generated at the request boundary, held single-flight in the C25 generation
service, and forwarded to C20 as the `AIJob.idempotencyKey` (unique index;
G11 §8 inv. 11).

The key above is the **candidate** generation key. The Implementation Plan
MUST rule explicitly on the following, distinguishing three different
identities:

1. **Request idempotency** — a retry of the *same* human request MUST NOT
   create a duplicate `AIJob` or `CommercialBrief` (single-flight + unique
   index, §17.2).
2. **Generation identity** — what canonically identifies "the same brief
   generation". Whether `requesterId` enters the canonical generation
   identity is **decided by the Implementation Plan**; this charter does
   not presuppose that different requesters must produce duplicate briefs.
   Whether a different user requesting generation over the same evidence
   reuses an existing brief MUST be decided explicitly on the basis of ACL,
   brief purpose, and review ownership.
3. **Review identity** — review/acceptance/dismissal events are bound to
   the specific brief revision and actor (section 13), independent of
   generation identity.

### 17.2 Duplicate-Prevention Semantics

| Submission | Behavior |
| --- | --- |
| Same source revision set + same request + same requester + same generationVersion | Idempotent: the existing `AIJob` reference (if still QUEUED/RUNNING) or the existing `CommercialBrief` is returned. **No second generation, no duplicate row.** |
| Evidence revision set changed | Different `evidenceSetHash` → different key → a **new generation** (a new revision), not a duplicate. |
| Duplicate retry after provider-side success | C20 idempotency key prevents double-invocation / double-spend (G11 §4.2.5, inv. 11). |

Duplicate prevention is structural (unique index + single-flight), not
convention.

---

## 18. Failure and Partial-Generation Rules

### 18.1 No Brief on Failure (Resolved)

| Failure | Brief created? | Handling |
| --- | --- | --- |
| `AIJob` FAILED — any failure class (timeout, rate limit, quota, content filter, auth, network, provider, validation, unknown) | **No** | Request surfaces as failed; operator may retry via C20 `aiJob.retry` (new attempts; still no brief until `SUCCEEDED`). |
| `AIJob` FAILED with `failureCategory = CONTENT_FILTER` | **No** | Never auto-retry the same prompt (G11 §4.3; G13 §6.3). |
| Parsing / assembly failure | **No** | Validation error surfaced to the human requester. |
| Validation failure (missing provenance, forbidden field, insufficient evidence, incomplete sections) | **No** | Brief rejected before persistence. |

### 18.2 Partial Results Rejected (Resolved)

**Incomplete briefs are rejected by default.** There is no partial-save of
the four sections, no placeholder content, and no "draft" state within the
brief entity. Persistence is **all-or-nothing**: complete content + all
mandatory fields + full provenance + evidence-anchored claims, verified by
`BriefValidationService` before any row is written. A validation failure is
an audit event, not a partial record.

---

## 19. Presentation and D2 Boundary

WP2 presentation obeys the deferred-hardening gate D2 and the brief-specific
rules:

| Rule | Requirement | Source |
| --- | --- | --- |
| Visual distinction | AI brief content **visually distinct** from CRM records; visible boundary divider | G2 §10 (D2); G3 §3.7 |
| One-click source navigation | Every source reference navigates to governed source detail (re-ACL'd, safe 404) | G2 §10 (D2); G17 |
| Advisory + legal designation | Mandatory display of human-readable and machine-readable designation | G4 §4 |
| Superseded de-emphasis | Superseded revisions (derived per §12.2 — never persisted) default to collapsed/hidden; current version is default view | G4 §6 (R2c/B3) |
| Review outcome + dispositions | The workspace simultaneously displays **Review status**, **Validity**, **Retention**, and the **Superseded-derived indicator** — e.g., `Accepted`, `Invalidated`, `Archived`, `Superseded by revision 4`. Labels coexist and never overwrite one another | §12.2; ADR-C25-002 §6 |
| De-emphasis without hiding | Superseded, invalidated, and archived records may be de-emphasized in default ordering/display, but the review outcome is **never hidden**: `ACCEPTED + INVALIDATED` renders as "previously accepted, later invalidated"; `DISMISSED + ARCHIVED` renders as "dismissed and archived" | §12.1–§12.2 |
| Anchor availability | Unreadable anchor renders **unavailable / restricted**; no source content leaked | §5.3; §15.3 |
| Freshness surfacing | STALE/ARCHIVAL warnings surfaced, never suppressed; evidence-changed-since-generation indicator when revisions differ | G5 §5; G1 §9.5 |
| Confidence + limitations | Four confidence elements and a first-class limitation statement | G6 §3.1 |
| B5 scoping | Not in standard CRM lists / global search without explicit "include AI projections" toggle | G4 §8 |
| No CRM-mutation proxy | No "Create Opportunity" or equivalent proxy; CRM records open in owning surfaces | G5 §3.6; G9 |

---

## 20. Cross-Phase Ownership Matrix

| Layer | Artifacts | WP2 Relationship | Prohibition |
| --- | --- | --- | --- |
| C20 | AIJob, AIRequestLog, PromptTemplate, ProviderCredential, ProviderRoute, capability registry, CompletionProvider | Read-only provenance/cost context; generation routed **through** C20 capability interfaces; provenance references recorded | Direct provider/credential/SDK/transport ownership; creating ProviderRoute or C20 entities; adding C20 capability from C25; deciding the ProviderBinding database/UI form; implementing provider routing or dispatch |
| C21 | ResearchEvidence, AIQualificationInsight, HumanFeedback, IntelligenceAggregate | Read-only intelligence context | Create/modify/reinterpret; scoring/ranking/qualification |
| C22 | ProspectRun, ActionGate, ExecutionLedger, ReplyDetection, OutreachExecution | Read-only execution history for provenance | Triggering execution; influencing ActionGate; C25 data at ActionGate |
| C23 | OptimizationInsight, PerformanceMetric, FeedbackLearningObservation | Read-only optimization context | Metric redefinition; competing optimization authority |
| C24 | ReplySignal, OpportunityCandidate, RevenueInsight, PipelineMetric | Read-only evidence; `OpportunityCandidate` is the brief anchor (read-only structured link; no C24 transition-service invocation through the link; anchor loss never cascade-deletes a brief) | Any artifact mutation; lifecycle transition; bypass of C24 transition service |
| CRM Core | Account, Contact, Opportunity, Sales Stage, Forecast, Revenue | Read-only commercial context | Create/modify/transition/commit any CRM Core entity; FK coupling |
| C25 WP1 | CommercialContext assembly, governed source navigation, read surface | **Consumed** — WP2 generates from assembled context; source navigation reused for brief evidence | Re-assembling independent of WP1; caching contexts as entities |
| C25 WP2 | `CommercialBrief` + append-only audit + transition/disposition service | **Owns this charter** | Authority fields; mutation; autonomy; side effects |

---

## 21. Security and Leakage Controls

| Risk | Control |
| --- | --- |
| Brief becomes a score/ranking/forecast proxy | Schema-level forbidden fields; proxy prohibition incl. natural-language equivalents; evidence-anchored vocabulary (G4 §5) |
| Leakage of unauthorized source content | Generation-time requester-ACL filter; **no verbatim source copy**; three-way ACL (section 15); mandatory per-claim masking of claims anchored to inaccessible sources (§15.3) |
| ACL bypass via brief | Reference-level only storage; live ACL-checked source navigation; safe 404 on denial |
| Prompt injection / capability escalation | Template-driven prompts + structured `context` payloads (G13 §6.1/§7.3 — CompletionRequest sanitization); C25 has no write/send/trigger tools (C25-INV-SEC-001); structural absence, not prompt refusal |
| PII / secrets in brief content | Structured context; no credential fields anywhere (G13 §6.1/§7.2); secrets never in brief, request, or result; audit events carry references, not content |
| Credential / provider / SDK ownership | None — C20 sole egress; C25-INV-SEC-001; C20 boundary |
| Stale evidence read as current | Freshness surfacing mandatory; STALE/ARCHIVAL never suppressed; evidence-changed indicator |
| Acceptance misread as approval | `acceptanceScope` machine-readable; Gate 8 ≠ Gate 9 (G9) |
| Narrative compounding across versions | No prior-brief reads at generation (G4 §6); superseded versions de-emphasized |

---

## 22. Batch / Automation Prohibitions

WP2 inherits the zero-automation default (G1 §8; G2 §12):

| Prohibited | Rationale |
| --- | --- |
| Scheduler / cron brief generation | G1 §8.2 |
| Worker / background queue for autonomous generation | No new queue architecture; only governed-async C20 `AIJob` on explicit human request |
| Webhook / event listener trigger | G1 §8.2 |
| Batch brief generation without per-brief human review | G4 §7; C25-INV-HG-001 |
| Unattended / autonomous loop | C25-INV-HG-001; G1 §8.2 |
| Automatic business action from a brief | G1 §14.3 |
| Automatic invalidation or regeneration on source change | Section 12; only explicit governed human actions |
| Automatic acceptance or prioritization | C25-INV-HG-001 |

Any future automation proposal requires a C25 Charter Amendment, an
independent ADR, invariant updates, and governance review (G1 §8.3).

---

## 23. Proposed Work Package Breakdown

Candidate decomposition for the WP2 implementation effort (each sub-package
requires its own Foundation Review + deferred-gate disposition before
implementation):

| WP | Name | Scope | Key gates |
| --- | --- | --- | --- |
| **WP2.0** | C20 Dependency Resolution | Consume and record the ratified foundation gate: capability identity, purpose policy, ProviderBinding boundary, eligibility, mapping, and provenance evidence; freeze the C25→C20 boundary contract. C20-INV-05…11 remain deferred runtime maturity items and are not activated by WP2. **No C25 code.** | Section 10 verdict; C20 ratification |
| **WP2.1** | CommercialBrief Contract and Persistence | `CommercialBrief` entity + scope metadata; mandatory/forbidden fields; immutability guard; review-status guard + save option and disposition guards + save options; transition/disposition service + action keys; append-only audit mechanism; supersession validator | D2; immutability; entity budget = 1 |
| **WP2.2** | Generation and Validation Boundary | `BriefGenerationService` (human-initiated; sync or governed-async C20 AIJob); `BriefValidationService` (mandatory fields, provenance completeness, forbidden-field guard, evidence anchoring, minimum evidence D4); idempotency key; failure/partial handling; generation versioning | D4 (minimum evidence); idempotency; no-partial rule |
| **WP2.3** | Human Review Lifecycle and Audit | `BriefLifecycleTransitionService` full review/disposition matrix (§12, §16.1); acceptance semantics; append-only review audit; feedback; invalidation (D3), supersession, archival, governed deletion (D5); Gate 8/Gate 9 separation | D3 (invalidation); D5 (deletion); audit append-only |
| **WP2.4** | Presentation and Source Navigation | Brief presentation (D2 distinction, advisory/legal designation, superseded de-emphasis, freshness surfacing, confidence/limitations); governed source navigation re-ACL; B5 "include AI projections" toggle; per-claim masking (mandatory default, §15.3) | D2; read-time ACL; masking default demonstrated |
| **WP2.5** | Runtime Verification and Freeze | Boundary test suite (section 24); no-side-effect proof for ACCEPTED; ACL matrix runtime verification; freeze review; invariant activation triggers | Freeze criteria (section 25) |

Recommended order: WP2.0 → WP2.1 → WP2.2 → WP2.3 → WP2.4 → WP2.5.
WP2.1–WP2.4 may proceed in parallel with the WP3 foundation review after
WP1 foundation is in place, subject to section 10.3 dependencies.

---

## 24. Required Tests and Runtime Verification

| Test class | Purpose | Acceptance |
| --- | --- | --- |
| Schema audit | Zero forbidden fields (score, priority, ranking, probability, forecast, revenueImpact, stage, lifecycle, isCurrent/isLatest) at schema level | Forbidden fields absent from entityDefs |
| Immutability | No update path on any content/provenance/reference/designation field; correction only via supersession with mandatory reference | Guard + contract test prove only review/disposition transition saves mutate the lifecycle fields |
| Provenance validation | All mandatory provenance fields present (five basic fields + `promptTemplateId` + `promptTemplateVersion`); referenced AIJob/AIRequestLog exist; provider/model consistent with the associated AIRequestLog; provenance survives supersession and deletion | Validators reject missing or inconsistent provenance |
| Lifecycle transitions | §12 matrix enforced; `reviewStatus` writes only via `BriefLifecycleTransitionService` + action key + save option + guard; disposition writes only via the corresponding disposition action + save option + guard; guard rejects stray save; `SUPERSEDED` never persisted as any field value or flag | Allowed/denied matrix green |
| Lifecycle / disposition orthogonality | `reviewStatus` accepts exactly the four values `GENERATED` / `REVIEWED` / `ACCEPTED` / `DISMISSED`; `INVALIDATED` and `ARCHIVED` are rejected as `reviewStatus` values; invalidation does not overwrite `ACCEPTED`/`DISMISSED`; archive does not overwrite `ACCEPTED`/`DISMISSED`; supersession does not overwrite `reviewStatus`; dispositions coexist (e.g., `ACCEPTED` + `INVALIDATED` + `ARCHIVED` + superseded-derived) | Orthogonality matrix green; coexistence fixture passes |
| Disposition governance | Invalidation and archival each write an append-only audit event with actor, timestamp, reason, action key, brief ID, and provenance reference; `acceptanceScope` is guarded — forbidden when `reviewStatus` is not `ACCEPTED`; no operational side effects (no C20 `AIRequestLog`, no C24 / CRM Core / C22 mutation, no automatic regeneration) | Audit-append proof + no-side-effect proof green |
| Disposition rendering | Rendering simultaneously shows review outcome and dispositions — `Accepted`, `Invalidated`, `Archived`, `Superseded by revision 4` coexist; `ACCEPTED + INVALIDATED` renders "previously accepted, later invalidated"; `DISMISSED + ARCHIVED` renders "dismissed and archived"; review outcome never hidden by de-emphasis | Presentation assertions green (§19) |
| **No-side-effect proof** | After `ACCEPTED`: zero new/updated C20–C24/CRM Core records; **zero new AIRequestLog**; zero C22 action events; zero C24 transitions; AIJob status unchanged by review; CRM write-path absence | Runtime record-count + fixture-identity diffs (WP1 no-write matrix pattern, G17 §6) |
| Generation gates | Rejects autonomous triggers; rejects generation below minimum evidence (D4); never reads prior briefs; idempotent re-submission returns existing brief/job | D1-style adversarial generation tests |
| Failure handling | No brief on any AIJob failure class; no partial/incomplete persistence | Failure matrix green |
| ACL matrix | Generation-time requester-ACL filter; read-time re-check; source navigation denial → safe 404; portal denial; per-claim masking when source ACL lost (§15.3); admin no-bypass verified | All capabilities × cases green (WP1 runtime matrix pattern) |
| D2 presentation | AI content visually distinct; boundary divider; one-click source navigation; superseded de-emphasis; B5 toggle | D2 criteria (a)(b)(c) demonstrated |
| Output governance | Advisory + legal designation present; four confidence elements; no authority phrasing; evidence-anchored claims | Response-structure assertions, not prompt inspection |
| C20 boundary | Zero direct provider/credential/SDK/HTTP paths; every generation routes through C20; one AIRequestLog per invocation | Static + runtime boundary confirmation |

---

## 25. Freeze Criteria

WP2 is a freeze candidate only when all of the following hold:

1. **D3, D4, D5, D7 dispositioned and demonstrated** — invalidation and
   archival distinct from review outcome and from supersession;
   `reviewStatus` / `validityDisposition` / `retentionDisposition`
   orthogonality demonstrated (§12); minimum evidence gate; governed
   deletion path; brief purpose binding defined via C20 (G3 §3.10).
2. **Section 10 foundation dependency resolution signed** — capability
   identity, purpose policy, and boundary evidence ratified and recorded.
   C20-INV-05…11 runtime activation is not a WP2 foundation-gate
   requirement; any later runtime verification is separately authorized.
3. **All §24 boundary tests green**, including the **ACCEPTED zero-side-effect
   proof** (runtime verification).
4. **Entity budget honored** — exactly one persistent C25 artifact
   (`CommercialBrief`); audit/feedback remain non-entity mechanisms.
5. **Invariant compliance signed** — ADV-001, HG-001, PROV-001, INT-006
   (owning) and OWN-001, SEC-001 (constraining) against the C25 Invariant
   Registry.
6. **WP2 Foundation Review signed** and **independent C20–C25 boundary
   verification signed** (G2 §14.3 gates).
7. **Masking / audit ratification gates resolved** (section 26) before any
   freeze.

---

## 26. Open Questions and Ratification Gates

| # | Question | Recommended default | Gate |
| --- | --- | --- | --- |
| OQ-A | When a reader loses source ACL: per-claim masking vs. whole-brief restriction vs. marker-only visibility | **Resolved — mandatory default (§15.3):** structured claim → source mapping with per-claim masking and "restricted-evidence" markers; whole-brief restriction only as conservative fallback when claims cannot be safely separated; "keep full claim + risk marker only" is **not** an allowed default | Default recorded by charter amendment (ratified 2026-08-01); implementation demonstrated in WP2.4 |
| OQ-B | Review-event persistence: reuse Espo audit/stream vs. internal append-only storage vs. first-class entity | **Priority order (§13.1):** (1) reuse existing Espo audit/stream if it guarantees append-only actor/timestamp/action-key/from-to-state/reason/`acceptanceScope`/brief-ID/provenance-reference with no update and no delete; (2) otherwise internal append-only storage — not a CRM scope, no navigation/list/search, no ordinary CRUD, atomic transition-service writes — with an ADR judgment before implementation on whether it constitutes a new first-class entity. Mutable audit fields on `CommercialBrief` are forbidden | Ratify audit-storage design in WP2.1 Foundation Review |
| OQ-C | C20 `CompletionCapability` value name and scope for brief generation | `COMMERCIAL_BRIEF` capability identity and `commercial_brief_generation` purpose policy are available for foundation consumption; runtime execution remains outside scope | C20 dependency closure ratified; implementation still requires separate authorization |
| OQ-D | Minimum-evidence definition beyond "≥ 1 governed source; chain complete" | ≥ 1 governed source artifact + complete artifact chain; numeric threshold (if any) via WP2.2 Foundation Review | WP2.2 gate |
| OQ-E | Idempotency dedupe window (how long a deterministic key suppresses re-generation) | Bounded window per brief purpose; expired keys become new generations (audit-marked) | WP2.2 gate |
| OQ-F | Archive / retention policy details (D5): archive retention period, governed-deletion retention, eligible review states for archive, restoration policy (if any) | Decided at the WP2.3 gate under D5; the lifecycle field model (§12.2) is resolved and is **not** re-opened by OQ-F | WP2.3 gate |
| OQ-G | Synchronous vs. governed-async default per generation request | Both permitted (human-initiated); surfaced to requester; no new queue | WP2.2 gate |

**Plan-level and C20-level open questions remain open; none blocks Plan
authoring, and each blocks code implementation until resolved:** OQ-B /
OQ-D / OQ-E / OQ-F / OQ-G are resolved by the Implementation Plan at the
gates in this table; the `requesterId` generation identity (§17.1) is
decided by the Plan; the §16.2 REST/API Option A/B choice is decided by
the Plan; the §15.5 capability → Espo Role / ACL / action mapping is
decided by the Plan; the `CompletionCapability` name and the provider
binding surface remain C20 governance (WP2.0, section 10).

**Resolved — lifecycle status model (recorded in §6.1–§6.2, §12):**
`reviewStatus` = `GENERATED` / `REVIEWED` / `ACCEPTED` / `DISMISSED`;
`validityDisposition` = `NONE` / `INVALIDATED`; `retentionDisposition` =
`ACTIVE` / `ARCHIVED`; `SUPERSEDED` = derived from `supersedesBriefId`
(never persisted); governed deletion = `deleteId` / deletion path, not a
status value.

Resolved items recorded in this charter (section headers mark them
"Resolved") are NOT open questions: entity/scope naming (§5.1), field
categories (§6), prompt/model/provider/completion metadata (§6.4),
OpportunityCandidate anchor (§5.3), three-field lifecycle model (§6.1,
§12.2), transition-service ownership (§12), SUPERSEDED derivation semantics
(§12.2), review-audit persistence boundary (§13.1), immutability definition
(§14), per-claim masking default (§15.3, OQ-A), four-layer authorization
model and capability matrix (§15.4–§15.5), REST/API surface decision frame
(§16.2), idempotency semantics (§17), failure/partial rules (§18), C20
dependency verdict (§10), HUMAN_REQUEST_ONLY semantics (§11).

---

## 27. Exact Implementation Authorization Boundary

### 27.0 Ratification and Authorization Status (2026-08-01)

| Item | Status |
| --- | --- |
| Charter status | **RATIFIED** — RATIFIED WITH NON-BLOCKING NOTES (Final Ratification Review, 2026-08-01) |
| Implementation Plan | **YES** — authoring of `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` is authorized |
| Code implementation | **NO** |
| WP2.0 dependency | **MANDATORY before any generation implementation** — ratified foundation gate evidence: capability identity + purpose policy + boundary evidence (§10.3). Runtime invariant activation is not required for this foundation gate. |

Ratification does **not** authorize: `CommercialBrief` entity creation;
metadata or scope creation; ACL / action configuration; controller or
route creation; migrations; tests; C20 capability changes; provider
routing or dispatch; scheduler / worker behavior; AI invocation; commit,
push, or tag.

### 27.1 This Charter Authorizes

- **Scope specification only** for WP2 (WP2.0–WP2.5), grounded in the
  ratified governance documents (section 2).
- The **resolved architecture decisions** recorded herein (sections 5–22).
- The **C20 dependency verdict** (section 10) as ratified foundation evidence
  consumed from the C20 governance record; runtime expansion remains a
  separate C20 process.
- The **candidate work-package decomposition** (section 23) and required
  tests/freeze criteria (sections 24–25).
- The **open questions and ratification gates** (section 26).
- **WP2 Implementation Plan authorship** — **YES** (§27.0): authoring of
  `docs/PHASE3C25_WP2_IMPLEMENTATION_PLAN.md` is authorized. The plan MUST
  map the §15.5 capabilities to existing Espo Role / ACL / action
  authorization configuration and MUST make the §16.2 REST/API choice
  deterministic. Plan authorship is not code implementation; code
  implementation remains **NO** (§27.2, §27.3).

### 27.2 This Charter Does NOT Authorize

| Forbidden | Detail |
| --- | --- |
| Code implementation | No PHP, JS, template, client, or runtime code |
| `CommercialBrief` entity creation | No entity, metadata, schema, or migration |
| C20 capability change | No `CompletionCapability` value added from C25; no C20 entity/service/contract change |
| `ProviderRoute` creation | No new routing entity; C20-owned configuration only; C25 does not decide the `ProviderBinding` database/UI form and does not implement provider routing or dispatch |
| Tests | No test authoring or fixture creation |
| Scheduler / worker / webhook / queue | No automation infrastructure |
| AI model invocation | No direct invocation, prompt engineering, or model selection |
| WP1 frozen file modification | WP1 artifacts referenced only, not modified |
| Metadata / scope creation | No new metadata or scope beyond the ratified planning scope |
| ACL / action configuration | No ACL, role, or action configuration |
| Controller / route creation | No controller, REST route, or API surface creation |
| Migrations | No schema or data migrations |
| Commit / push / tag | None |

### 27.3 Implementation Gate

Before any WP2 code:

1. C20 dependency resolution ratified with capability identity + purpose policy
   + boundary evidence (section 10.3).
2. WP2 Foundation Review approved (per sub-package).
3. Independent C20–C25 boundary verification.
4. Deferred gates D3/D4/D5/D7 dispositioned.
5. Invariant compliance checklist signed (ADV-001, HG-001, PROV-001,
   INT-006; OWN-001, SEC-001).
6. Ratification gates OQ-A … OQ-G resolved.

---

## 28. References

- `docs/PHASE3C25_CHARTER_DRAFT.md`
- `docs/PHASE3C25_IMPLEMENTATION_CHARTER.md`
- `docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md`
- `docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md`
- `docs/audit/ADR-C25-001_COMMERCIAL_INTELLIGENCE_WORKSPACE_DEFINITION.md`
- `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md`
- `docs/audit/ADR-C25-003_REVENUE_ANALYST_ASSISTANT_GOVERNANCE.md`
- `docs/audit/ADR-C25-004_HUMAN_DECISION_WORKSPACE_ARCHITECTURE.md`
- `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md`
- `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md`
- `docs/adr/C25_INVARIANT_REGISTRY.md`
- `docs/audit/PHASE3C25_WP1_FINAL_FREEZE_REVIEW.md`
- `docs/audit/PHASE3C25_WP1_FINAL_RUNTIME_RECHECK.md`
- `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
- `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`
- `docs/PHASE3C20_WP3_AI_EXECUTION_CHARTER.md`
- `chitu-connector/chitu_connector/acquisition/providers/capabilities.py`
- `chitu-connector/chitu_connector/acquisition/providers/completion/base.py`
- `chitu-connector/chitu_connector/acquisition/providers/registry.py`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/` (AIJob, AIRequestLog, PromptTemplate services/guards; entityDefs)
- `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md`
- `docs/adr/C24_INVARIANT_REGISTRY.md`

---

*Work-package implementation scope specification only. This document
authorizes no code implementation, entity creation, metadata modification,
C20 capability change, ProviderRoute creation, test authoring, commit, push,
or tag. All implementation requires C20 dependency resolution, WP2
Foundation Review, deferred-gate disposition, independent C20–C25 boundary
verification, and ratification of the open questions in section 26.*

*Co-Authored-By: Claude <noreply@anthropic.com>*
