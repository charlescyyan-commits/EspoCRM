# Phase3C25 WP2 Implementation Plan — AI Commercial Brief

---

## 1. Document Control

| Field | Value |
|---|---|
| Document | Phase3C25 WP2 Implementation Plan — AI Commercial Brief |
| Status | **RATIFIED — implementation planning reference only; code implementation not authorized** |
| Phase | Phase3C25 (Commercial Intelligence) |
| Work Package | WP2 — AI Commercial Brief (WP2.0, WP2.1A, WP2.1B, WP2.2–WP2.5) |
| Date | 2026-08-01 |
| Governing charter | `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` — RATIFIED 2026-08-01 (RATIFIED WITH NON-BLOCKING NOTES) |
| Predecessor plan | `docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md` (FROZEN) |
| Scope flags (ratified) | `object: false`, `tab: false`, `acl: true`, `aclPortal: false`, `aclActionList: ["read"]`, module `CommercialIntelligence` |
| Entity budget | **Exactly one** persistent C25 artifact in WP2: `CommercialBrief`. No `BriefFeedback`, `BriefAudit`, `BriefReviewEvent`, cache, or session entity without ADR amendment |
| Implementation authorization | **NO** — this document authorizes no code, no entity, no metadata, no scope, no ACL, no controller, no route, no migration, no test, no C20 change, no ProviderRoute, no scheduler/worker, no AI invocation, no commit, no push, no tag |
| Plan authorship | YES — authorized by WP2 charter §27.0 |

> **Amendment record (2026-08-01):** amended after the WP2 Implementation
> Plan Independent Review (verdict: PASS WITH REQUIRED AMENDMENTS). Merged
> amendments: single workflow dispatcher + standalone generate/regenerate
> routes (§12.3); controller-file removal (§12.1); six-identity idempotency
> and regeneration model with anchor-bound canonical key (§14); WP2.1A /
> WP2.1B split (§23); pre-ADR failed-generation-intent boundary (§9.2,
> §15.3); minimum viable class set (§20); ACL/authorization precision
> (§11); entityDefs type and bound completion (§8.4); retention/deletion
> proposed-default corrections (§18); live-tree repository citations
> (§3, §20.5); allowlist rebuild with single owning WP per file (§28);
> test matrix additions (§29). This amendment does not re-open the
> ratified WP2 charter. Code implementation remains **NO**.

---

## 2. Executive Implementation Verdict

| Decision point | Verdict |
|---|---|
| Plan status | **RATIFIED — implementation planning reference only; code implementation not authorized.** This remains an implementation-planning document only (§36) |
| REST/API pattern (§12) | **Option A** — standard Espo Record controller resolution for reads (no custom controller file; C24 precedent), `aclActionList: ["read"]`; create/edit/delete forbidden by ACL + metadata; writes exclusively through **3 action-keyed POST routes**: standalone `generate`, standalone `regenerate`, and one workflow dispatcher for all brief-bound governed actions. Option B rejected |
| Capability mapping (§11) | Four capabilities mapped to Espo Role/ACL/action-authorization via workflow metadata + a new C25-scoped `CommercialBriefAuthorizationService` replicating the existing **Prospecting workflow infrastructure** pattern (`WorkflowAuthorizationService` is Prospecting-owned; it is not modified). No hardcoded role names in services; no parallel permission system |
| Review audit storage (§15, §23) | **WP2.1A (docs-only)** decides the internal append-only audit persistence contract and completes the ADR amendment; **WP2.1B** implements the CommercialBrief contract/persistence. Espo audit/stream reuse REJECTED (cannot guarantee the required append-only event schema). Mutable JSON history on `CommercialBrief` forbidden. Audit implementation only after ADR ratification, at the ADR-assigned WP (default WP2.3) |
| Minimum evidence gate (§9, §24) | Hard gate: ≥ 1 governed source artifact, complete artifact chain, source currently readable, source revision identifiable, anchor `OpportunityCandidate` exists and requester-readable, `evidenceSetHash` computable, source C20 provenance minimal conditions. Warning-only evidence quality and stale-evidence presentation are separate, non-blocking concerns |
| Idempotency / generation identity (§14) | Canonical generation equivalence key = `H(opportunityCandidateId \| purpose \| evidenceSetHash \| generationVersion \| promptTemplateVersion)`. **requesterId EXCLUDED**. Generate dedupe window (proposed default 24 h). Explicit regeneration is **never** dedupe-suppressed; it requires a unique `regenerationRequestId` and always yields a new AIJob execution and a new revision |
| Sync / async runtime (§13) | **Governed asynchronous via C20 AIJob is the default** (human-initiated). Synchronous path permitted only if the C20 CompletionProvider contract offers it; C25 does not force blocking HTTP. No new queue architecture |
| Retention / deletion (§18) | Archive eligible only for terminal review outcomes (ACCEPTED/DISMISSED) or INVALIDATED; invalidated auto-archive = NO; archive only via explicit `brief.archive`; **`brief.unarchive` is excluded from this Plan** (restoration would require a future Charter Amendment + ADR + Plan Amendment); 90-day retention is a **proposed default** subject to WP2.3 Foundation Review / D5 ratification; deletion eligibility never equals automatic deletion; governed deletion is `deleteId` soft-delete with reason + audit; no deletion implementation while legal/audit hold representation is unresolved |
| C20 readiness (§7) | **WP2.0 is a mandatory hard precondition** for any generation implementation. Three C20-governed dependencies remain UNRESOLVED externally (§35): CompletionCapability portfolio decision (COMMERCIAL_BRIEF is proposed-only), provider-binding / allowed-provider-binding surface, and C20-INV-05…11 activation+verification |
| Implementation authorization | **NO** — remains `code implementation = NO` (verified in §36 and §12.6 verification) |

---

## 3. Governing Sources

Governing documents (ratified, read in full for this Plan):

| Source | Role |
|---|---|
| `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md` | **Primary governing charter** — product contract, field model, action matrix, invariants, capabilities, OQ table, authorization boundary |
| `docs/PHASE3C25_IMPLEMENTATION_CHARTER.md` | Phase-level charter (WP0/WP1/WP2/WP3 scope) |
| `docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md` | Cross-WP foundation plan (G1–G14 gates, entity budget, workspace boundaries) |
| `docs/PHASE3C25_CHARTER_DRAFT.md` | Draft lineage of the C25 charter |
| `docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md` | FROZEN WP1 plan — CommercialContext assembly, source map, governed source navigation, D2 boundary |
| `docs/audit/PHASE3C25_WP1_FINAL_FREEZE_REVIEW.md` | WP1 freeze review — the approved WP1 baseline this WP builds on |
| `docs/audit/ADR-C25-001_COMMERCIAL_INTELLIGENCE_WORKSPACE_DEFINITION.md` | Workspace definition, source artifact map |
| `docs/audit/ADR-C25-002_AI_COMMERCIAL_BRIEF_GOVERNANCE.md` | Brief governance: advisory designation, acceptance scope, content structure |
| `docs/audit/ADR-C25-003_REVENUE_ANALYST_ASSISTANT_GOVERNANCE.md` | Assistant governance (adjacent surface; boundary only) |
| `docs/audit/ADR-C25-004_HUMAN_DECISION_WORKSPACE_ARCHITECTURE.md` | Human decision workspace architecture, Gate 8/Gate 9 separation |
| `docs/audit/ADR-C25-005_CROSS_LAYER_READ_ONLY_ACCESS_CONTRACTS.md` | Cross-layer read-only contracts, C20 provenance references |
| `docs/audit/ADR-C25-006_AI_CONFIDENCE_AUDIT_FEEDBACK_GOVERNANCE.md` | Confidence, audit, and feedback governance |
| `docs/adr/C25_INVARIANT_REGISTRY.md` | C25 invariant registry (C25-INV-ADV-001, HG-001, PROV-001, INT-006, OWN-001, SEC-001) |
| `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md` | C20 AI platform architecture — AIJob lifecycle, AIRequestLog, capability registry, invariants |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | C20 invariant registry — C20-INV-03…11 (C20-INV-05…11 currently DEFERRED) |
| `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md` | Frozen capability registry contract — `CapabilityResolutionRequest`/`Result`, `allowed_provider_bindings`, `PURPOSE_NOT_ALLOWED` |
| `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md` | Ratified completion capability portfolio scope (4 values, frozen) |
| `docs/PHASE3C20_WP2_CHARTER.md`, `docs/PHASE3C20_WP2_2_B_COMPLETION_IMPLEMENTATION_PLAN.md`, `docs/PHASE3C20_WP3_AI_EXECUTION_CHARTER.md`, `docs/PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md` | C20 WP2/WP3 execution contracts (AIJob runtime, retry eligibility, error taxonomy) |
| `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md` | C24 precedent — OpportunityCandidate governed lifecycle entity (field model, lifecycle, audit) |
| `docs/adr/C24_INVARIANT_REGISTRY.md` | C24 invariants (SEP/LIFE/ADV/REV/HG/MET) constraining C25 advisory behavior |
| `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md`, `docs/PHASE3C24_WP3_IMPLEMENTATION_CHARTER.md`, `docs/PHASE3C24_WP3_REVENUE_INSIGHT_CHARTER.md`, `docs/PHASE3C24_WP1_REPLY_INTELLIGENCE_CHARTER.md` | C24 entity contracts, supersession, freshness |
| `docs/audit/ADR-C24-006` … `ADR-C24-015` | C24 ADRs — ownership boundary, lifecycle governance, commercial decision boundary, pipeline metric governance, revenue insight lifecycle, human governance, freshness |
| `docs/audit/ADR-C22-005_RETRY_FAILURE_CLASSIFICATION.md`, `docs/audit/ADR-C22-005_RATE_LIMIT_RETRY_GOVERNANCE_ADDENDUM.md`, `docs/audit/ADR-C22-006_CRM_LIFECYCLE_BOUNDARY.md`, `docs/audit/ADR-C22-007_ACTIONGATE_REENTRY_RULES.md` | C22 execution-governance precedent that C25 must not touch |
| `docs/adr/C22_INVARIANT_REGISTRY.md`, `docs/adr/C23_INVARIANT_REGISTRY.md` | C22/C23 invariants constraining C25 advisory output |

Real repository code and metadata precedents examined — **the live
extension tree in this workspace** (see §20.5 for concrete pattern
citations):

- `crm-extension/files/custom/Espo/Modules/Prospecting/` — **live** C24-era
  code: `Entities/OpportunityCandidate.php`, `Services/OpportunityCandidateLifecycleService.php`,
  `Services/C24OpportunityCandidateSaveOption.php`, `Services/WorkflowAuthorizationService.php`
  (existing Prospecting workflow infrastructure), `Hooks/OpportunityCandidate/*Guard.php`,
  `Resources/routes.json` (10 POST routes, FQCN `actionClassName`),
  `Resources/metadata/{scopes,entityDefs,aclDefs,app,clientDefs,selectDefs,dashlets,formula}/`,
  `Resources/metadata/app/prospectingWorkflow.json`, `Resources/metadata/app/acl.json`.
- `crm-extension/files/custom/Espo/Modules/AIPlatform/` — **live** C20 code:
  `Resources/metadata/entityDefs/{AIJob,AIRequestLog,PromptTemplate,ProviderCredential}.json`,
  `Services/AIJobService.php`, `Services/AIJobStatusMutationSaveOption.php`,
  `Hooks/AIJob/AIJobStatusMutationGuard.php`, `Entities/AIRequestLog.php`,
  `Hooks/AIRequestLog/AIRequestLogAppendOnlyGuard.php`, `Entities/PromptTemplate.php`.
  `AIJob` is metadata-defined (`entityDefs/AIJob.json`) with no dedicated PHP
  entity class. No `ProviderRoute`/`ProviderBinding` entityDefs exist anywhere.
- `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/` — **live**
  WP1 module: `Resources/routes.json` (2 GET routes), `Api/GetWorkspaceContext.php`,
  `Api/GetGovernedSourceDetail.php`, `Services/{ContextAssemblyService,VisibilityInheritanceService,FreshnessPresenter,ProvenancePresenter}.php`,
  `Services/Adapters/*.php`, `Resources/metadata/{scopes,app/aclPortal.json,clientDefs}/`.
- `archive/runtime-backups/c11_1_baseline-20260714T094409Z/` — **historical
  reference only** (predates C20); never the primary basis for current
  implementation precedent.

---

## 4. Ratified Product Contract

From WP2 charter §4 (RATIFIED, not re-opened):

> An AI Commercial Brief is a persistent, immutable projection artifact — an AI-generated, human-reviewable summary of governed commercial evidence at a point in time, produced only by explicit human request, carrying mandatory advisory and legal designation, and governed by a human-review lifecycle.

**Product properties (ratified §4.2):**

| Property | Rule |
|---|---|
| Advisory | Decision-support material only; not a forecast, commitment, or decision |
| Immutable projection | Content, provenance, source references, and designation never change after generation |
| Persistent | Survives its request; queryable under brief ACL (not a transient response) |
| Revisioned | Changed interpretation requires a new superseding revision (`supersedesBriefId`) created by an explicit human regeneration request |
| Human-gated | Each brief requires individual human review; ACCEPTED/DISMISSED are human decisions |
| Zero-side-effect | ACCEPTED creates no AIRequestLog, no CRM/C24/C22/C20 side effect |
| Deletion-safe | Deleting all briefs loses no business fact; provenance survives deletion |
| Scoped | Excluded from standard CRM lists and global search without explicit "include AI projections" toggle; portal denied |

**What CommercialBrief is NOT (ratified §3, §4.3):**

- Not a CRM Core record; not a decision record; not an approval record; not an audit record.
- Not a substitute for `OpportunityCandidate`; does not modify the C24 lifecycle; does not create Lead / Opportunity / Account / Quote / Revenue.
- Not a trigger for C22 outreach, ActionGate, send, or any execution action.
- Not a new C20 entity, ProviderRoute, or CompletionCapability value; does not mutate AIJob / AIRequestLog / PromptTemplate.
- Not a scoring / ranking / probability / forecast / revenue-impact authority.
- Not autonomous / scheduled / batch / event-driven / unattended generation.
- Not a queue architecture; not a public business record for review events or audit events.
- Not partial / incomplete persistence; not a "draft" state within the brief entity.

**ACCEPTED means only** `acceptanceScope = DECISION_SUPPORT_MATERIAL_ONLY` (Gate 8). It is not commercial approval, execution approval, OpportunityCandidate transition, CRM Opportunity creation, forecast commitment, or work-prioritization authority (Gate 9 happens outside C25).

**Identity:**

| Attribute | Value |
|---|---|
| Entity | `CommercialBrief` |
| Scope | `CommercialBrief` |
| Module | `CommercialIntelligence` |
| Class | `Espo\Modules\CommercialIntelligence\Entities\CommercialBrief` |
| Display name | AI Commercial Brief |
| Human designation (verbatim) | `AI-generated commercial summary — for human review only. Not a forecast, commitment, or decision.` |
| Machine designation | `legalDesignation` = `AI-GENERATED_ADVISORY_PROJECTION_NOT_A_COMMERCIAL_DECISION` (constant) |

---

## 5. Implementation Principles

The Plan is written under these ratified principles:

| # | Principle | Derivation |
|---|---|---|
| P1 | **One persistent C25 artifact.** Exactly `CommercialBrief`. Every other persistence requirement (review audit, feedback) is a non-entity mechanism or an ADR-gated addition. | Charter §5.2, G3 §7.5 |
| P2 | **Option A only.** Standard Record controller resolution for ACL-controlled reads; governed actions for every state change; no parallel CRUD, identity, role, or security model. | Charter §16.2; C24 precedent |
| P3 | **ACL ≠ action authorization ≠ transition guard.** Record ACL gates read; action authorization gates action keys (capabilities); guards gate the state machine and save-option protocol. None substitutes for another. | Charter §15.5; C24 precedent |
| P4 | **No hardcoded role names in business services.** Capability → Role/ACL mapping lives in workflow metadata; the authorization service resolves it. Fallback bindings exist only inside the authorization metadata adapter, and are configurable. | Prospecting workflow-infrastructure precedent |
| P5 | **Immutability by guard + absence of write paths.** Content, provenance, source references, and designation are written only at generation. No generic update path exists. Enforcement is structural (metadata + guards), not UI-only. | Charter §6.1, §14.2; C24 immutable guard |
| P6 | **Mutable JSON history is forbidden** on `CommercialBrief`. Review/disposition history never accumulates inside a JSON field on the entity. | Charter §6.1 |
| P7 | **No partial Brief.** All-or-nothing persistence; validation failure is never a partial record. | Charter §18.2 |
| P8 | **Zero automation is the structural default.** No scheduler, worker, webhook, batch, event-driven, or autonomous trigger. Human initiation only; any future automation requires Charter Amendment + ADR + invariant updates. | Charter §11.2, §22 |
| P9 | **No CRM Core / C22 / C24 write path.** No service, hook, or save option may call a CRM Core lifecycle method, C24 transition service, C22 ActionGate, or outreach/send. Read-only passthrough only. | C24-INV-REV-003; C22-INV-EX-001; ADR-C24-006 §6.2 |
| P10 | **Provenance survives everything.** The provenance chain (`sourceAIJobId`, `sourceAIRequestLogId`, provider, model, generationVersion) must survive deletion of the brief; C20 records are independent of brief lifecycle. | C25-INV-PROV-001 |
| P11 | **WP2.0 gates generation.** No generation implementation until C20 dependency resolution is ratified. | Charter §10.3, §27.3 |
| P12 | **Advisory designation is mandatory** on every output; suggestions are observations, never directives; every claim is evidence-anchored. | C25-INV-ADV-001; C25-INV-INT-006 |
| P13 | **Source ACL is re-checked at every read.** Governed source navigation re-checks native source ACL (denied → safe 404); per-claim masking is the mandatory default when a reader loses source ACL. | Charter §15.1, §15.3; WP1 GetGovernedSourceDetail |

---

## 6. Resolved Plan-Level Decisions

This section records the deterministic resolutions this Plan is required to make. It does not re-open ratified field model decisions (§12.2 of the charter is fixed).

| Decision | Resolved answer | Reference |
|---|---|---|
| REST/API mode (§16.2) | **Option A** — no custom controller file; 3 action-keyed POST routes | §12 |
| Route surface | Standalone `generate`; standalone `regenerate`; one workflow dispatcher for all brief-bound governed actions | §12.3 |
| Capability → Espo Role / ACL / action mapping (§15.5) | Workflow-metadata role bindings + new C25-scoped `CommercialBriefAuthorizationService` (Prospecting workflow-infrastructure pattern; existing service not modified); per-action matrix | §11 |
| Review audit storage (OQ-B) | WP2.1A decides the internal append-only persistence contract + ADR amendment; implementation after ratification at the ADR-assigned WP (default WP2.3); no CommercialBrief JSON history | §15, §23 |
| Minimum evidence threshold (OQ-D) | Hard gate + warning-only quality + stale presentation, defined separately | §9, §24 |
| Idempotency (OQ-E) | Six identities; anchor-bound canonical equivalence key; requesterId excluded; proposed-default window | §14 |
| requesterId generation identity (§17.1) | NOT part of the canonical generation equivalence key | §14 |
| Regeneration vs dedupe | Explicit regeneration is never dedupe-suppressed; unique `regenerationRequestId` required; retry of the same `regenerationRequestId` is idempotent | §14 |
| Sync/async default (OQ-G) | Governed async via C20 AIJob (default); sync only if C20 contract supports it | §13 |
| Archive/retention (OQ-F) | Proposed defaults only; WP2.3 Foundation Review / D5 ratifies; no unarchive in this Plan | §18 |
| Failed-generation intent (pre-ADR) | Requester-facing error + structured application log/telemetry only; no persistent record of any kind | §9.2, §15.3 |
| Failed-AIJob retry key relation | New attempt identity; generation identity unchanged | §14 |
| Source-original-content storage | Never copied into the brief; only `(entityType, entityId, revision, freshnessAtGeneration)` references | §9 |
| Supersession | `supersedesBriefId` set once at creation; current/superseded derived at read time; no `isCurrent`/`isLatest`/`isSuperseded` booleans | §17 |
| Deletion | `deleteId` governed soft-delete; not a status; not a disposition | §16, §18 |
| invalidated auto-archive | NO | §18 |
| Portal | Denied for all capabilities | §11, §19 |
| Admin | May skip action-role permission only; never skips record ACL, source ACL, reason, audit, lifecycle guard, or leakage control | §11 |

---

## 7. C20 Dependency Plan (WP2.0)

### 7.1 The three C20-governed readiness dependencies

WP2.0 is the **first hard precondition** of WP2. No generation implementation may begin until WP2.0 exits. The three dependencies are owned by C20 governance; C25 proposes and consumes.

| # | Dependency | Status today | C25 obligation | C20 obligation |
|---|---|---|---|---|
| D-1 | **Completion capability portfolio decision** | Ratified portfolio = `{RESEARCH_EVIDENCE, QUALIFICATION_INSIGHT, DRAFT_ASSISTANCE, REPLY_ASSISTANCE}` (frozen, 4 values). None covers brief generation. `COMMERCIAL_BRIEF` is a **proposed name only** | Propose; document the gap (DRAFT_ASSISTANCE is nearest but semantically and governancely distinct — reusing it would overload the portfolio and pollute provenance semantics) | Add a `CompletionCapability` value for brief generation through C20's own process (amendment to G13 + connector contract change); decide final name, granularity, portfolio placement |
| D-2 | **Provider binding / allowed-provider-binding surface** | The CRM-side surface that supplies `allowed_provider_bindings` (the CRM-authorized candidate binding collection in `CapabilityResolutionRequest`) is **not yet implemented** (`ProviderRoute` entityDefs/PHP class absent; ProviderRoute configuration UI deferred to C20 WP3) | Verify the real `CapabilityResolutionRequest` fields and DTO contract before naming any metadata/UI surface; define and register the C25 brief purpose within binding-level `allowed_purposes` / `PURPOSE_NOT_ALLOWED` filtering; **do not decide the ProviderBinding database or UI form** | Deliver a functional binding surface before any C25 generation can route |
| D-3 | **C20-INV-05…11 activation and verification** | All DEFERRED in the C20 registry; none claimed ACTIVE today | Require verified-ACTIVE status before brief provenance is validated against C20 invariants | Activate and verify: 05/06 AIJob status-transition guard, 07 append-only AIRequestLog, 08 provider-invocation/request-log cardinality, 09 prompt-template immutability, 10 retry eligibility, 11 idempotency |

### 7.2 Hard constraints on C25 (ratified §10.4, §27.2)

- Do not create a `ProviderRoute` entity from C25.
- Do not add the `CompletionCapability` value from C25.
- Do not modify C20 capability resolution, `CompletionProvider`, or any C20 entity/service/contract.
- Do not decide the ProviderBinding database or UI form from C25.
- Do not implement provider routing, dispatch, or scheduling in C25.
- Do not hold provider, model, credential, SDK, or transport ownership in C25 (C20 D3; C25-INV-SEC-001).
- Do not read credentials; do not select model/provider.

### 7.3 WP2.0 deliverables

| Deliverable | Content |
|---|---|
| C20 dependency decision package | Recorded C20 decision(s) on D-1 (final capability name/granularity/placement), D-2 (binding surface contract + brief purpose registration), D-3 (activation plan) |
| C20 contract verification | Verified `CapabilityResolutionRequest`/`Result` fields, `allowed_provider_bindings`, `allowed_purposes`, `PURPOSE_NOT_ALLOWED`, `CompletionRequest`/`CompletionResult`, `AIJob`/`AIRequestLog` field contracts (incl. the `c20FailedAiJobs` queue predicate name and `attemptCount` field spelling against the live AIPlatform tree) |
| Invariant readiness evidence | Evidence that C20-INV-05…11 are ACTIVE and enforced (contract tests, guard presence) |
| Boundary test requirements | The C25→C20 invocation boundary test list (no outbound PHP HTTP, no credential read, no routing, no dispatch ownership) |
| Go/no-go gate | Signed go/no-go before any WP2.2 generation implementation |

### 7.4 WP2.0 scope boundary

WP2.0 is a **documentation, contract-verification, and gate** work package. It implements no C25 generation and no C20 change. C20 dependency files belong to a separate C20 governance/change package (see §28.4).

---

## 8. CommercialBrief Data Model

### 8.1 Field model (ratified — not re-opened)

| Category | Fields | Mutable? | Guard |
|---|---|---|---|
| Standard (system) | `id`, `createdAt`, `createdBy`, `modifiedAt` (only when a governed field changes), `deleteId` | Immutable (system-owned); `modifiedAt` mirrors governed mutations only | System |
| Anchor / scope | `opportunityCandidateId` (structured read-only C24 link/reference) | Immutable | Immutability guard |
| Generation content | `reportingPeriod`, `generatedAt`, `generationVersion`, `customerSituation`, `commercialSignals`, `riskFactors`, `suggestedReviewPoints` | Immutable | Immutability guard; generation-only write |
| Source references | `sourceEvidence[]` (per source: `entityType`, `entityId`, `revision`, `freshnessAtGeneration`, `locator`), `evidenceSetHash` (derived) | Immutable | Immutability guard; generation-only write |
| Provenance | `sourceAIJobId`, `sourceAIRequestLogId`, `provider`, `model`, `generationVersion`, `promptTemplateId`, `promptTemplateVersion`, `capability`, `purpose` | Immutable | Immutability guard; provenance-completeness validator |
| Designation | `advisoryDesignation` (fixed text), `legalDesignation` (fixed constant) | Immutable | Constant-value validator |
| Review outcome & dispositions | `reviewStatus`, `acceptanceScope`, `outcomeReason`, `validityDisposition`, `invalidationReason` or audit-only reason, `retentionDisposition`, `archiveReason` or audit-only reason | Mutable only via governed review/disposition transition | State guard + save option; append-only audit guard |
| Supersession | `supersedesBriefId` (set once at creation) | Immutable once set | Immutability guard; supersession validator |

**Plan-level additions (marked; not in charter §9.1):** `capability` and
`purpose` in the provenance category. Rationale: D7 brief-purpose binding
requires the invoked capability/purpose to be recorded, and both fields
exist on the C20 `AIRequestLog` (live entityDefs), enabling the
consistency check required by charter §9.2. All other fields are adopted
unchanged from the ratified charter.

**Enum spellings (ratified, not re-opened):**

| Field | Values |
|---|---|
| `reviewStatus` | `GENERATED`, `REVIEWED`, `ACCEPTED`, `DISMISSED` |
| `validityDisposition` | `NONE`, `INVALIDATED` |
| `retentionDisposition` | `ACTIVE`, `ARCHIVED` |
| `acceptanceScope` | `DECISION_SUPPORT_MATERIAL_ONLY` (meaningful only when `reviewStatus = ACCEPTED`; DISMISSED/INVALIDATED/ARCHIVED must never carry or fabricate it) |
| `freshnessAtGeneration` | `CURRENT`, `AGING`, `STALE`, `ARCHIVAL` (C24-INV-REV-005 snapshot) |

**Transition rules:** `GENERATED → REVIEWED → ACCEPTED | DISMISSED`; ACCEPTED and DISMISSED are terminal review outcomes; reviewStatus is never overwritten by supersession, invalidation, archival, or governed deletion. `validityDisposition` and `retentionDisposition` are orthogonal to `reviewStatus`. **SUPERSEDED is derived at read time** from the `supersedesBriefId` chain and creation ordering — never persisted, never an editable flag. **Deletion is not a status** — it is the `deleteId` governed soft-delete path.

### 8.2 Forbidden fields (ratified §6.3 — exhaustive denylist)

| Category | Forbidden fields |
|---|---|
| Score / rank authority | `score`, `priority`, `ranking`, `rank`, `probability`, `closeProbability`, `revenueImpact`, and natural-language equivalents used as de facto scores ("High", "Strong", "Top" without evidence anchoring) |
| Forecast / commitment | `forecast`, `commit`, `forecastCategory`, `amount` |
| Lifecycle authority | `stage`, `lifecycleStage`, `salesStage`, `closeDate`, `expectedClose`, `nextStep` |
| Execution authority | `send`, `execute`, `approvedForOutreach`, `actionGateDecision`, `executionCommand`, `sendInstruction`, `providerRoute` |
| Autonomous decision | `readyToCreateOpportunity`, `createLead`, `createOpportunity`, `autoAccept`, `acceptanceScore`, `autoCloseDate`, `closeTrigger`, `approvalRule` |
| CRM Core writeback | `opportunityId`, `accountId`, `leadId`, `contactId` (no database FK into CRM Core) |
| Credentials / secrets | `providerCredential`, `providerSecret`, any credential/secret field |
| Provider internals | `promptText`, `rawCompletionPayload`, editable `provider`/`model` selection, editable capability/purpose |
| Legal/audit hold markers | **No hold field is added by this Plan** — hold representation is unresolved and reserved for WP2.3 Foundation Review / D5 (§18) |

### 8.3 Structural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Section storage | Four separate immutable `text` fields (`customerSituation`, `commercialSignals`, `riskFactors`, `suggestedReviewPoints`), not one JSON blob | Field-level immutability guard; schema validation per section; no mutable-JSON-history pattern |
| Content encoding | Plain text (markdown-lite, no HTML). No raw HTML stored; rendering escapes all text | XSS safety (D2; §19, §21) |
| Claim → source mapping | Structured immutable `claimSourceMap[]` (JSON) — each claim carries an identifier and its `[{entityType, entityId, revision}]` evidence-anchors | Mandatory basis for per-claim masking (§9, §15.3, §19) |
| Anchor | `opportunityCandidateId` as a structured read-only reference (link field); no lifecycle ownership; no cascade delete | C24-INV-SEP-002; ADR-C24-006 |
| Source references | `sourceEvidence[]` JSON array of `{entityType, entityId, revision, freshnessAtGeneration, locator}` — references only, source original content is never copied into the brief | Charter §8.2; C25-INV-PROV-001 |
| Ownership | **No `assignedUser` / `teams`** adopted. Visibility is workspace-scoped via brief ACL roles + capability action authorization + source ACL re-check; per-record ownership implies a navigation/list model the entity excludes | Charter §5.2, §16.2 |
| `modifiedAt` | Updated only when a governed field changes (review/disposition transition); system-owned | Charter §6.1 |

### 8.4 entityDefs types and bounds (resolved)

Field-level database/type decisions for WP2.1B. All JSON-carrying fields
use Espo `text` columns containing **canonical JSON** (the repository
convention: JSON arrays are stored in `text` fields, e.g. the C24
`transitionHistory` pattern), never native DB JSON operators.

**Section text fields** (`customerSituation`, `commercialSignals`,
`riskFactors`, `suggestedReviewPoints`):

| Bound | Value |
|---|---|
| Type | `text` (Espo entityDefs `text`), one field per section |
| Encoding | Plain text / markdown-lite; raw HTML forbidden (rejected at validation) |
| Per-field max length | **10,000 characters** |
| Total generated content max | **32,000 characters** across the four fields |
| Render escaping | All text escaped at render; no `innerHTML` from stored content (§19.3) |
| Empty / whitespace validation | Each section must be non-empty after trim; whitespace-only content rejected before persistence |

Note: the independent review's label "commercialSummary" maps to the
charter-ratified `customerSituation` field (Customer Situation section);
the charter field name is retained.

**`sourceEvidence`:**

| Bound | Value |
|---|---|
| Storage form | `text` field holding a canonical JSON array |
| Max sources | **50** per brief |
| Per-item fields | `entityType`, `entityId`, `revision`, `freshnessAtGeneration`, `locator` |
| `locator` | Canonical `"{entityType}:{entityId}@{revision}"` string used for governed navigation (WP1 `GetGovernedSourceDetail`) |
| Source original text | **Never stored** — references only |
| Ordering | Stable sort by `(entityType, entityId, revision)` before serialization |
| Canonical serialization | Sorted items, fixed key order, no insignificant whitespace |
| Max serialized size | **16,000 characters** |

**`claimSourceMap`:**

| Bound | Value |
|---|---|
| claimId scheme | `"{sectionKey}#{ordinal}"` — section key ∈ {`customerSituation`, `commercialSignals`, `riskFactors`, `suggestedReviewPoints`}, ordinal = stable 1-based claim index within the section at generation time (deterministic; no post-hoc UUID needed) |
| Claim text storage | **Not duplicated** — claims are resolved from the section fields by `claimId`; only the anchor list is stored (explicit storage policy) |
| Cardinality | One claim → many source references (1:N) |
| Max claims | **200** per brief |
| Max sources per claim | **10** |
| JSON schema | `[{"claimId": string, "anchors": [{"entityType": string, "entityId": string, "revision": string}]}]` |
| Canonical ordering | Entries sorted by `claimId`; anchors sorted by `(entityType, entityId, revision)` |
| Orphan validation | Every `claimId` must resolve to a claim in its section; every anchor must exist in `sourceEvidence`; violations reject the brief before persistence |
| Masking behavior | A claim renders restricted-evidence when the reader cannot read **any** of its anchors (§19.2); claims with at least one readable anchor remain visible |
| Field / database type | `text` field holding canonical JSON |
| Max serialized size | **32,000 characters** |

**`evidenceSetHash`:**

SHA-256 over the canonical JSON serialization of
`{ "anchor": opportunityCandidateId, "sources": [<sorted (entityType, entityId, revision) tuples>] }`.
The anchor is bound into the hash input so that identical evidence sets
consumed under different anchors can never collide. Immutable; serves
idempotency (§14) and freshness-change detection (§9.1).

---

## 9. Evidence and Claim Mapping

### 9.1 Evidence set

| Element | Definition |
|---|---|
| `sourceEvidence[]` | The **complete** set of governed artifacts the generation consumed. No subsetting that hides an evidence basis. Per source: `entityType`, `entityId`, `revision`, `freshnessAtGeneration`, `locator` |
| `evidenceSetHash` | SHA-256 over the anchor-bound canonical tuple set (§8.4). Immutable. Serves idempotency (§14) and freshness-change detection |
| Claim → source mapping | `claimSourceMap[]`: every generated claim references the source records that anchor it (G4 §5). Mandatory basis for per-claim masking (§15.3) |
| Evidence locator | `entityType + entityId + revision` (canonical `locator` string, §8.4); navigation via WP1 `GetGovernedSourceDetail` (16-type allowlist), re-ACL'd at every read |
| Freshness | `freshnessAtGeneration` snapshot per source (CURRENT / AGING / STALE / ARCHIVAL per C24-INV-REV-005); surfaced, never suppressed (§19) |
| Visibility behavior | A reader's access to a claim is the union of access to the claim's sources; masked per §15.3 |

### 9.2 Minimum evidence threshold (OQ-D resolved)

Three distinct concepts are **deliberately separated**:

| Concept | Rule | Effect |
|---|---|---|
| **Hard minimum gate (D4)** | (1) ≥ 1 governed source artifact; (2) artifact chain complete; (3) every source currently readable by the requester; (4) every source revision identifiable; (5) evidence chain complete (each referenced artifact exists and is resolvable); (6) anchor `OpportunityCandidate` exists and is requester-readable; (7) `evidenceSetHash` computable; (8) source C20 provenance minimum (for C20-backed sources: `sourceAIJobId` + `sourceAIRequestLogId` + `provider` + `model` + `generationVersion` present and consistent with the AIRequestLog); (9) referenced evidence `validationState` is not `REJECTED`/`SUPERSEDED` | **Blocks generation.** Failure → requester-facing error; **no AIJob; no Brief; no AIRequestLog**. Failed-generation intent handling per §15.3: **before the WP2.1A audit ADR is ratified — structured application log / telemetry only, no persistent record of any kind; after ratification — a `PRE_DISPATCH_GATE_FAILURE` append-only audit event, only if the ADR explicitly approves it**. No numeric threshold; quality is a warning, not a gate |
| **Warning-only evidence quality** | Weak evidence (low confidence, small sample, single-source, self-reported) | **Does not block generation.** Surfaced as warnings in the brief's confidence/limitations elements (§19) |
| **Stale evidence presentation** | Source freshness `STALE`/`ARCHIVAL` at generation; evidence changed since generation | **Does not block generation.** Surfaced as mandatory staleness warnings; evidence-changed-since-generation indicator displayed; never suppressed (C24-INV-REV-005) |

Hard-gate failure, warning-quality, and stale-presentation are enforced at three distinct layers: the generation gate (blocks), the validation service (labels), and the visibility service (renders).

### 9.3 Evidence completeness contract

- The source evidence set is the complete consumption record — no subsetting.
- Source original content is never copied into the brief; only references are stored.
- Every claim maps to source record references; unmapped claims are rejected at validation.
- The anchor `OpportunityCandidate` is required — a brief is anchored to a specific candidate and never stands alone.

---

## 10. Provenance Model

### 10.1 C20 provenance fields

| Field | Type | Role |
|---|---|---|
| `sourceAIJobId` | Immutable reference | Link to the C20 `AIJob` that produced the completion |
| `sourceAIRequestLogId` | Immutable reference | Link to the C20 `AIRequestLog` row for the provider invocation (C25-INV-PROV-001; ADR-C25-005 §6.1) |
| `provider` | Immutable scalar | Copied from AIRequestLog; consistency-checked at generation |
| `model` | Immutable scalar | Copied from AIRequestLog; consistency-checked at generation |
| `capability` | Immutable scalar (Plan-level addition, §8.1) | The C20 capability value (proposed `COMMERCIAL_BRIEF`, final name per C20 governance) |
| `purpose` | Immutable scalar (Plan-level addition, §8.1) | The C25 brief purpose registered within binding-level `allowed_purposes` |
| `promptTemplateId` | Immutable scalar | The `PromptTemplate` reference used |
| `promptTemplateVersion` | Immutable scalar | Referenced template version; validated against C20-INV-09 immutability |
| `generationVersion` | Immutable scalar | C25 generation-logic/prompt version (C25-owned) |

**Link vs scalar vs consistency-checked:** `sourceAIJobId`/`sourceAIRequestLogId` are **links** (validated to exist at generation; read-only thereafter). `provider`, `model`, `capability`, `purpose`, `promptTemplateId`, `promptTemplateVersion` are **immutable scalars** copied from the AIRequestLog and **consistency-checked** against the AIRequestLog at generation (a mismatch fails validation — no Brief persisted). `generationVersion` is C25-owned.

### 10.2 Provenance rules

- Provenance completeness is a hard validation gate: any missing field → Brief rejected before persistence (C25-INV-PROV-001).
- The provenance chain **survives deletion** of the brief (C25-INV-PROV-001); C20 AIJob/AIRequestLog records are independent of the brief lifecycle.
- No credential, secret, prompt text, or raw completion payload is ever stored (C25-INV-SEC-001; forbidden fields §8.2).
- `AIRequestLog` is append-only (C20-INV-07); brief provenance references it without mutation.

---

## 11. ACL and Authorization Mapping

### 11.1 Capability → authorization primitives (ratified §15.5, resolved here)

Capabilities are authorization **categories**, not role names hardcoded in services. Each is mapped to existing Espo Role / ACL / action-authorization configuration.

| Capability | Granted action keys | Brief read | Provenance view | Portal |
|---|---|---|---|---|
| **Commercial Brief Operator** | `brief.generate`, `brief.regenerate`, `brief.archive` | Yes, under brief ACL | Permitted C20 provenance, bounded by C20 ACL + source ACL | Denied |
| **Commercial Brief Reviewer** | `brief.review`, `brief.accept`, `brief.dismiss`, `brief.invalidate` | Yes, re-checked at review time | Same bound | Denied |
| **Governed Deletion** | `brief.delete` (reason + actor + timestamp + audit record mandatory) | Yes | Yes | Denied |
| **Provenance Viewer** | — (read-only) | Per brief ACL | Permitted C20 provenance only; bounded by C20 ACL + source ACL | Denied |
| **Admin** | All keys — but **no bypass** of reason, audit, transition, or source-leakage rules | Yes | Yes | Denied |
| **Portal user** | — (no keys) | No | No | Denied |

### 11.2 Per-action matrix

| Action key | Required capability | Required entity ACL | Source ACL prerequisite | Reason | Audit | Transition/disposition service | Save option | Guard | Forbidden side effects |
|---|---|---|---|---|---|---|---|---|---|
| `brief.generate` | Commercial Brief Operator | **None (creation via service; generic create forbidden)** — prerequisite is anchor + all-sources readable (live) | Requester reads anchor + **all** sources used (live) | No | Yes (append-only generation event; pre-ADR per §15.3) | `CommercialBriefGenerationService` | `CommercialBriefSaveOption::GENERATION_AUTHORIZED` | `CommercialBriefImmutableGuard` + provenance-completeness validation | No CRM/C24/C22 writes; C20 writes only via C20 services; no autonomous trigger; no prior-brief reads |
| `brief.regenerate` | Commercial Brief Operator | Brief read | Same as generate (live re-check); evidence gate rerun | **Yes** (explicit regeneration reason) | Yes (`brief.regenerate` event: prior + new brief IDs) | `CommercialBriefGenerationService` (superseding revision) | `CommercialBriefSaveOption::GENERATION_AUTHORIZED` | `CommercialBriefImmutableGuard` + supersession validation | Never overwrite prior revision; explicit human request + unique `regenerationRequestId` only; no auto-regeneration |
| `brief.review` | Commercial Brief Reviewer | Brief read (re-checked at review time) | Source refs live-checked at navigation | No | Yes | `CommercialBriefLifecycleService` | `CommercialBriefSaveOption::STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` + audit guard | No content mutation; no AIRequestLog; no CRM/C24/C22 writes |
| `brief.accept` | Commercial Brief Reviewer | Brief read (re-checked) | Source refs live-checked at navigation | No (`acceptanceScope` fixed) | Yes (with `acceptanceScope`) | `CommercialBriefLifecycleService` | `CommercialBriefSaveOption::STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` + audit guard | **Zero side effects** — no AIRequestLog, no CRM/C24/C22/C20 record change |
| `brief.dismiss` | Commercial Brief Reviewer | Brief read (re-checked) | Source refs live-checked at navigation | Yes (`outcomeReason` required) | Yes (with reason) | `CommercialBriefLifecycleService` | `CommercialBriefSaveOption::STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` + audit guard | Same as accept |
| `brief.invalidate` | Commercial Brief Reviewer | Brief read | — (reason cites source issue) | Yes | Yes (with reason) | `CommercialBriefLifecycleService` (validity disposition method) | `CommercialBriefSaveOption::VALIDITY_DISPOSITION_AUTHORIZED` + audit write | `CommercialBriefStateGuard` (reviewStatus unchanged) + audit guard | `reviewStatus` unchanged; no automatic regeneration; no AIRequestLog; no C24/CRM/C22 side effects; source evidence unaffected; no content mutation |
| `brief.archive` | Commercial Brief Operator | Brief read | — | Yes (`archiveReason`) | Yes (with reason) | `CommercialBriefLifecycleService` (retention disposition method) | `CommercialBriefSaveOption::RETENTION_DISPOSITION_AUTHORIZED` + audit write | `CommercialBriefStateGuard` (reviewStatus/validityDisposition unchanged) + audit guard | `reviewStatus`/`validityDisposition` unchanged; retention path only; no content mutation; no `deleteId` change; provenance and supersession graph intact |
| `brief.delete` | Governed Deletion | Brief read | — | Yes (mandatory) | Yes (mandatory: deleteId, actor, timestamp, reason) | `CommercialBriefLifecycleService` governed-deletion method | `CommercialBriefSaveOption::DELETION_AUTHORIZED` + audit write | `CommercialBriefStateGuard` (deleteId-only mutation) + audit guard | Soft delete only; provenance survives; no source-record cascade; no erasure of audit trail |

**Cross-cutting rules:**

| Rule | Resolution |
|---|---|
| Authorization service | New C25-scoped `CommercialBriefAuthorizationService`; the existing `Espo\Modules\Prospecting\Services\WorkflowAuthorizationService` is **not modified** — it is existing Prospecting workflow infrastructure (not a "C24 service"), and serves as pattern precedent only |
| Action registry | The C25 authorization service recognizes **only** `brief.*` action keys; the workflow dispatcher enforces the same allowlist (§12.3) |
| Workflow metadata | `app.commercialBriefWorkflow.actionRoleBindings` (schema version 1): per action key a `{roleIds, roleNames}` binding list; identical schema to the live `app/prospectingWorkflow.json` precedent |
| Fallback role names | Fallback bindings exist **only** inside the authorization metadata adapter (mirroring the Prospecting `fallbackActionRoleBindings()` resilience mechanism), are **configurable via the metadata file**, and never appear in business services |
| No hardcoded role names in services | Business services never name roles; role resolution happens only in the authorization service |
| No parallel permission system | Only Espo Role/ACL + workflow metadata; no new identity/role/security model |
| Record ACL ≠ action authorization | `acl->checkEntityRead` and action-key authorization are both required; neither replaces the other |
| Action authorization ≠ transition guard | Authorization service gates the action; the state guard gates the state machine + save-option protocol |
| Ownership/team rule | No `assignedUser`/`teams` ownership model; visibility = brief ACL (read) + capability action authorization + source ACL re-check. Capability membership resolves via effective roles (direct + team-assigned, mirroring the Prospecting `effectiveRoleIds` union) |
| Admin behavior | Admin may skip **action-role permission only**. Admin never skips: record ACL, source ACL, reason, audit, lifecycle guard, or leakage control |
| Portal behavior | Denied for all capabilities and all action keys |

### 11.3 Espo metadata mapping (resolved)

| Metadata | Value |
|---|---|
| `scopes/CommercialBrief.json` | `entity: true`, `object: false`, `tab: false`, `acl: true`, `aclPortal: false`, `customizable: false`, `importable: false`, `module: CommercialIntelligence`, `type: Base`, `statusField: null`, `aclActionList: ["read"]`. **`statusField: null` is a decision of this Plan** (reviewStatus is service-governed, not a generic status field); it is not claimed as a C24 statusField precedent |
| `aclDefs/CommercialBrief.json` | `{}` — matching the live C24 files (`aclDefs/OpportunityCandidate.json` is literally `{}`) |
| `app/acl.json` (append) | `mandatory.scopeLevel` — **`CommercialBrief` MUST NOT appear** (the WP1.2 lesson: force-off makes role-based read grants impossible). `adminMandatory.scopeLevel.CommercialBrief` = `{create: "no", read: "all", edit: "no", delete: "no"}` — deliberately stricter than the C24 `create: "yes"` entries because CommercialBrief creation is generation-only. Effect: generic create/edit/delete = no for everyone; read granted per role/team via the Role UI; admin read = yes; admin create/edit/delete rights do not exist and admin actions still cannot bypass governed action keys, guards, reason, or audit |
| `app/aclPortal.json` (append) | `mandatory.scopeLevel.CommercialBrief: false` — Portal fully denied (WP1 `CommercialIntelligenceWorkspace` precedent in the same file) |
| Workflow metadata | `app.commercialBriefWorkflow.actionRoleBindings` (schema version 1, `governanceMarker` per ADR); per action key `{roleIds, roleNames}`; schema identical to the live `app/prospectingWorkflow.json` precedent |
| Save options | Single internal final class `CommercialBriefSaveOption` with constant string tokens (C24 save-option class precedent); see §20.3 |
| B5 / search-list exclusion | Achieved by scope flags (`object: false`, `tab: false`) + absence of any search-enable metadata + the workspace "include AI projections" toggle (WP2.4 client). No separate search metadata file — verified: governed C24 entities carry none |

---

## 12. REST/API Decision

### 12.1 Decision: **Option A**

Selected deterministically per charter §16.2.

**Why Option A satisfies B5, security, and the presentation boundary (evidence from the live repository pattern):**

1. The repository's existing governed-entity pattern (C24 `OpportunityCandidate`, `RevenueInsight`) already delivers B5: `object: false`, `tab: false`, `acl: true`, `aclActionList: ["read"]`, admin `edit: "no"`/`delete: "no"`. This exact combination is **implemented precedent in the live tree**, not a proposal.
2. Security: create/edit/delete are forbidden by ACL and metadata; all state changes flow through governed action keys + services + save options + guards. There is no write path to bypass (no standard CRUD controller surface; guarded save-option protocol).
3. Presentation boundary: "not discoverable in the ordinary UI" is achieved via scope metadata + absence of search-enable metadata + the explicit "include AI projections" toggle — not by disabling read APIs. Standard GET/read under ACL remains the read surface; governed source navigation re-ACL's at every read (WP1 `GetGovernedSourceDetail`).

**Option A definition:**

- **Standard Espo Record controller resolution** for reads: Espo resolves the base `Espo\Core\Controllers\Record` controller automatically for a `type: Base` scope. **No custom controller file is created** — the live C24 governed entities (`OpportunityCandidate`, `RevenueInsight`) have no controller file in `Prospecting/Controllers/`. A `Controllers/CommercialBrief.php` may be introduced only if real Espo runtime verification later proves automatic Record resolution unavailable; that would require evidence and an allowlist amendment. By default it is **excluded** (§28).
- `aclActionList: ["read"]`.
- Standard GET/read collection used only for ACL-controlled reads.
- create/edit/delete forbidden by ACL and metadata.
- All business changes flow exclusively through the governed action keys and services of §11.2.
- **No duplicate read API** — the POST routes below carry no read surface.

**Option B is rejected** — no repository evidence shows the standard Record controller resolution cannot satisfy B5, security, or the presentation boundary. The C24 pattern is proven; a dedicated controller would duplicate identity/role/security infrastructure without benefit.

### 12.2 Read surface (resolved)

- Brief detail: standard Record read (`GET .../CommercialBrief/{id}`) under brief ACL.
- Brief list: scoped, non-standard — via explicit "include AI projections" toggle; excluded from standard lists and global search by default.
- Governed source navigation: WP1 `GetGovernedSourceDetail` (16-type allowlist), re-ACL'd at every read (denied → safe 404).
- Provenance view: bounded by C20 ACL + source ACL.

### 12.3 Write surface (resolved)

Only human-initiated, action-keyed POST endpoints via the Espo `Api\Action` route pattern (routes.json + `Api\Post*` classes — the live pattern in the Prospecting module). **POST only for these; GET-only elsewhere.** Exactly **three** routes:

| Route | Action key(s) | Api class |
|---|---|---|
| `POST /CommercialIntelligence/brief/generate` | `brief.generate` | `Api\PostBriefGenerate` |
| `POST /CommercialIntelligence/brief/:id/regenerate` | `brief.regenerate` | `Api\PostBriefRegenerate` |
| `POST /CommercialIntelligence/brief/:id/workflow/:action` | `brief.review`, `brief.accept`, `brief.dismiss`, `brief.invalidate`, `brief.archive`, `brief.delete` — and any future brief-bound governed action | `Api\PostBriefWorkflowAction` (single C25 API dispatcher) |

**Workflow dispatcher contract (`Api\PostBriefWorkflowAction`):**

1. Reads `id` from the route param; reads `action` from the route param.
2. Validates `action` against a **closed allowlist** (`review`, `accept`, `dismiss`, `invalidate`, `archive`, `delete`) mapped to stable action keys (`ACTION_ALIASES` pattern from the live `PostQuoteWorkflowAction`); unknown actions are rejected with `BadRequest`. **No arbitrary method dispatch.**
3. Resolves the Brief by `id` (safe not-found on miss).
4. Calls the C25-scoped `CommercialBriefAuthorizationService` for the resolved action key.
5. Checks the `CommercialBrief` entity ACL (`acl->checkEntityRead`).
6. Checks the source ACL prerequisite per §11.2 (live re-check where applicable).
7. Invokes `CommercialBriefLifecycleService` with the appropriate save option; the audit event is written atomically by that service.
8. **Does not** save the entity directly; **does not** bypass save options or guards; **does not** perform provider calls; holds no business logic beyond request translation (the Api class is a thin adapter, mirroring the 49-line `PostQuoteWorkflowAction` precedent).

**Request body contracts:**

| Endpoint | Body |
|---|---|
| `brief/generate` | `opportunityCandidateId` (required); `purpose` (required, within the C25 brief-purpose registry); `generationVersion` (required); `promptTemplateVersion` or template-selection reference (required); optional `requestId` / idempotency token (client retry correlation) |
| `brief/:id/regenerate` | Source brief ID comes from the **route**; `regenerationRequestId` (required, unique per human regeneration request); optional `purpose` override **only** within charter-allowed brief-purpose scope; explicit reason (required, §14.4). The prior Brief is never modified by this request |
| `brief/:id/workflow/:action` | `reason` where required by §11.2 (dismiss / invalidate / archive / delete); no other mutable field accepted |

### 12.4 Portal

Denied (G4 §8; WP1 portal denial). `aclPortal: false` + `app/aclPortal.json` mandatory `scopeLevel.CommercialBrief: false`; portal users have no action keys and no brief read.

### 12.5 Admin

Admin may skip action-role permission only; never bypasses record ACL, source ACL, reason, audit, lifecycle guard, or source-leakage rules.

### 12.6 Verification performed for this decision

- Confirmed `object: false`, `tab: false`, `acl: true`, `aclActionList: ["read"]`, admin `edit: "no"`/`delete: "no"` is the established C24 pattern **in the live tree** (`crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/{OpportunityCandidate,RevenueInsight}.json`; `Resources/metadata/app/acl.json`).
- Confirmed the live C24 governed entities have **no** controller file (`crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/` contains no `OpportunityCandidate.php` / `RevenueInsight.php`).
- Confirmed the `Api\Action` + `routes.json` workflow-dispatcher pattern in the **live** Prospecting module (`Api/PostQuoteWorkflowAction.php`, `Resources/routes.json`).
- Confirmed no repository evidence compels Option B.
- **`code implementation = NO` confirmed after this section (§36).**

---

## 13. Runtime and AIJob Model

### 13.1 Modes (OQ-G resolved)

| Mode | Allowed? | Resolution |
|---|---|---|
| Human initiation | **Yes — the only trigger** | Explicit human request (workspace button/form). No scheduler, worker, webhook, listener, batch, or autonomous loop |
| Synchronous provider execution | Conditional | Permitted **only** if the C20 CompletionProvider contract offers a synchronous completion exchange. C25 does not force all provider calls to block HTTP (real C20 contract: C20-INV-03 forbids outbound PHP HTTP; all provider I/O is through the connector; dispatch is queue-backed) |
| Governed asynchronous execution | **Default** | Human request → C20 `AIJob` (QUEUED) → C20 dispatch → SUCCEEDED → Brief persisted. Status retrieved by polling the AIJob status |
| Autonomous scheduler | **Forbidden** | C20 §10; C25 §11.2, §22 |
| Event-driven generation | **Forbidden** | No webhook/listener trigger |
| Worker retry | Governed only | Retry only via C20 governed retry eligibility (NETWORK/PROVIDER/RATE_LIMIT within `maxAttempts` budget) or operator `aiJob.retry` |
| Batch generation | **Forbidden** | No batch without per-brief human review |

### 13.2 Generation flow (governed async default)

```text
Human requester
  → CommercialBriefGenerationService (C25)
      → ContextAssemblyService (WP1) — requester's source ACL filter → CommercialContext snapshot
      → Minimum-evidence gate (§9.2) — fail → requester-facing error; NO AIJob, NO Brief,
        NO AIRequestLog; intent per §15.3 (pre-ADR: application log only; post-ADR:
        PRE_DISPATCH_GATE_FAILURE event if the ADR approves)
      → Idempotency check (§14) — generate: existing eligible Brief / in-flight AIJob
        within window → return existing; regenerate: never dedupe-suppressed (§14.4)
      → CompletionRequest (capability=COMMERCIAL_BRIEF* [proposed], purpose=<C25 brief purpose>,
                            structured context, idempotencyKey)
      → C20 AIJob created via C20 capability interface (dispatch owner = C20 AIJobService)
      → AIJob SUCCEEDED → CompletionResult
      → CommercialBriefValidationService (§9.2, §10.2) → persist CommercialBrief (reviewStatus=GENERATED)
        + append-only generation audit event (post-ADR audit store)
```

### 13.3 AIJob interaction contract (resolved)

| Item | Resolution |
|---|---|
| Human request creates | A generation request + context snapshot + (after gate/idempotency) a C20 `AIJob` |
| AIJob created when | After the minimum-evidence gate passes and the context snapshot is canonicalized; before dispatch |
| Dispatch owner | C20 `AIJobService` (`aiJob.dispatch`, system actor) |
| Retry owner | Operator (`aiJob.retry`) + C20 governed retry eligibility; never autonomous |
| Operator recovery | Failed jobs surface via the C20 failed-jobs queue predicate (name to be confirmed against the live AIPlatform tree at WP2.0 contract verification); operator reviews, retries, or cancels |
| Polling / status retrieval | AIJob `status` (QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED) + `attemptCount` (live entityDefs spelling) |
| Timeout | C20 AIJob execution budget (per-capability `maxAttempts`; C20-owned) |
| Terminal failure | AIJob FAILED; no Brief created; operator may retry via `aiJob.retry` |
| `CONTENT_FILTER` | Terminal; **never auto-retry the same prompt** (C20-INV-10); operator reviews/revises |
| `RATE_LIMIT` | Retryable; honors `Retry-After`; does not consume attempt budget |
| `QUOTA` | Terminal; pauses capability; operator review (no wasteful retry) |
| No automatic business action | A successful generation creates the Brief; **no** follow-on CRM/C24/C22/C20 action |
| No infinite retry | `maxAttempts` budget + terminal-category rules (C20-INV-10) |
| No batch generation | Forbidden (§11.2) |

### 13.4 No new queue architecture

C25 reuses the C20 AIJob runtime. It creates no queue, worker pool, or scheduler.

---

## 14. Idempotency Model

### 14.1 Six distinct identities (resolved)

| # | Identity | Definition | Purpose |
|---|---|---|---|
| 1 | **Request idempotency key** | `c25-brief-request-v1:{canonical generation equivalence key}` (§14.2) | Suppresses duplicate generation for the same logical generate request within the dedupe window |
| 2 | **Canonical generation equivalence key** | `H(opportunityCandidateId \| purpose \| evidenceSetHash \| generationVersion \| promptTemplateVersion)` — **includes the anchor** | Identifies the produced content; the canonical reuse unit; different anchors never collide |
| 3 | **AIJob execution ID** | The C20 `AIJob` id (C20-owned; one per dispatched logical task) | Execution tracking, operator recovery, provenance (`sourceAIJobId`) |
| 4 | **Brief revision ID** | The `CommercialBrief.id` of a specific revision | Record identity; supersession graph nodes |
| 5 | **Regeneration / supersession request ID** | `regenerationRequestId` — unique nonce supplied per explicit human regeneration request (§14.4) | Distinguishes deliberate supersession from retries and from ordinary generate dedupe |
| 6 | **Retry attempt ID** | `c25-brief-attempt:{requestKey}:{attemptNumber}` | Distinguishes retry attempts within one logical generation or regeneration request |

### 14.2 Canonical keys and cross-user reuse (OQ-E + §17.1 resolved)

| Question | Resolution |
|---|---|
| Canonical generation equivalence key | `H(opportunityCandidateId \| purpose \| evidenceSetHash \| generationVersion \| promptTemplateVersion)` |
| Request idempotency key | `c25-brief-request-v1:{canonical generation equivalence key}` |
| requesterId in the equivalence key? | **No** — same anchor + evidence + purpose + versions is the same generation regardless of requester |
| Cross-user reuse (same anchor/evidence/purpose/versions)? | **Yes only when all of the following hold:** source ACL equivalence (the requesting user can read every source in the evidence set); same purpose; same anchor; same evidence set; same generation and prompt-template version; **the current user holds read permission on the reused Brief**. Otherwise reuse is forbidden → a new generation (never another user's unreadable content) |
| Reuse audit | An append-only **reuse audit event** is written — **only after the WP2.1A audit ADR is ratified**; before ratification, reuse is recorded as non-persistent telemetry only |
| Failed AIJob explicit retry | New **attempt** identity `c25-brief-attempt:{requestKey}:{attemptNumber}`; the request key is consumed/marked on FAILED; the **generation identity is unchanged** (same evidence/version → retry completes the same generation). A failed generation never yields a Brief |
| Dedupe window | Bounded window **per purpose** (**proposed default 24 h**, configurable via workflow metadata; subject to WP2.3 Foundation Review confirmation). Expired keys → new generation (audit-marked as a new generation, not a duplicate) |
| `evidenceSetHash` canonicalization | §8.4 — anchor-bound, stably sorted tuples, SHA-256 over canonical JSON |
| Source revision change | Changes `evidenceSetHash` → new generation identity → new generation (freshness-change detection) |
| `promptTemplateVersion` change | New generation identity |
| `generationVersion` change | New generation identity |
| Purpose change | New generation identity |
| Anchor change | New generation identity (anchor is in the key — different anchors never collide) |

### 14.3 Generate dedupe rules

- Ordinary `brief.generate` is subject to the dedupe window.
- The same canonical generation equivalence key within the window returns the **existing eligible Brief** (or the in-flight AIJob) — never a duplicate, never an automatic new revision.
- The window value is a **proposed default (24 h)**, configurable via workflow metadata.
- Duplicate prevention is structural (single-flight reservation + canonical key), not convention.
- Concurrent duplicate requests: exactly one caller proceeds (lock-protected reservation, C10 send-idempotency precedent).

### 14.4 Regeneration rules (explicit supersession)

`brief.regenerate` requires **all** of the following:

| Requirement | Rule |
|---|---|
| Existing brief ID | From the route (`/brief/:id/regenerate`); the prior Brief must exist and be readable by the requester |
| Unique `regenerationRequestId` | Required; unique nonce per human regeneration request |
| Human initiation | Explicit request only; never automatic |
| Explicit reason | Required; recorded in the `brief.regenerate` audit event |
| Source ACL recheck | Live re-check of anchor + all sources, as for generate |
| Evidence gate rerun | The full minimum-evidence gate (§9.2) runs again |

**Regeneration request key:**
`H("regenerate" | existingBriefId | regenerationRequestId | opportunityCandidateId | evidenceSetHash | generationVersion | promptTemplateVersion)`

**Rules:**

- **Not suppressed** by the ordinary generate dedupe window — a deliberate regeneration always proceeds.
- Always produces a **new AIJob execution** (a new C20 `AIJob`, identity #3).
- On success, creates a **new Brief revision** with `supersedesBriefId` pointing at the prior Brief.
- The prior Brief is **never modified** (content, reviewStatus, dispositions unchanged).
- A retry carrying the **same `regenerationRequestId`** is idempotent: it returns the in-flight AIJob or the already-created revision — it never duplicates a Brief.
- A failed attempt may use a new **attemptId** (identity #6) while retaining the same regeneration request identity.

### 14.5 Idempotency enforcement

- The request idempotency key is persisted **before** AIJob dispatch (C20-INV-11 pattern; C22-INV-RETRY-006 precedent).
- No "same key on FAILED returns the failed brief" — a failed generation never yields a Brief; the retry uses a new attempt identity.
- A superseding Brief never resolves to the prior Brief through ordinary dedupe (§14.4).

---

## 15. Review Audit Storage Decision

### 15.1 Requirement (OQ-B)

Every review/disposition action must produce an **append-only audit event** containing: actor, timestamp, event type, action key, from/to `reviewStatus`, from/to disposition, reason (where applicable), `acceptanceScope` (where applicable), brief ID, and AIJob/AIRequestLog provenance reference. Written atomically by the transition/disposition service. No ordinary editing. No deletion.

### 15.2 Reuse assessment — REJECTED

| Candidate | Verdict | Reason |
|---|---|---|
| Espo `audit` (AuditLog field-diff) | **REJECTED** | Core field-diff mechanism; records changed fields with user/date but does not provide the structured event schema required: action key, from/to disposition, reason, `acceptanceScope`, brief ID, provenance reference. Not an append-only event log with the required atomic-write contract; not extensible to carry these fields without core modification |
| Espo `stream` | **REJECTED** | User-facing activity feed, not an audit log; no structured from/to/reason/action-key fields; not append-only under the required contract; inappropriate for governance audit |
| Mutable JSON history on `CommercialBrief` | **FORBIDDEN** | Charter §6.1: review/disposition history never accumulates inside a JSON field on CommercialBrief |

### 15.3 Decision: internal append-only review audit storage (decided at WP2.1A)

An internal append-only review audit store is **required**. The design below is the **input** to WP2.1A; WP2.1A ratifies the final contract via ADR amendment (§23.1). Implementation is **not authorized** by this Plan.

| Design element | Resolution |
|---|---|
| Nature | A dedicated append-only event store, written **only** by `CommercialBriefLifecycleService` / `CommercialBriefGenerationService` (and the governed-deletion path) via an audit-write save option |
| Governance classification | **Not a CRM entity; not an entity scope.** An internal persistent record set (one database table; rows = audit events). Whether it additionally constitutes a first-class governed artifact is judged at WP2.1A (§15.4) |
| No CRM surface | No scope metadata, no navigation, no list, no global search, no ordinary CRUD, no standard Record controller, no clientDefs |
| Data structure | One event row per action: `id`, `briefId`, `actionKey`, `eventType`, `actorId`, `timestamp`, `fromReviewStatus`, `toReviewStatus`, `fromValidityDisposition`, `toValidityDisposition`, `fromRetentionDisposition`, `toRetentionDisposition`, `reason`, `acceptanceScope`, `sourceAIJobId`, `sourceAIRequestLogId` |
| Uniqueness / index | Unique event `id`; index on `(briefId, timestamp)`; composite lookup by `actorId` and `actionKey` |
| Association | Many events → one Brief; no event is editable or deletable |
| Immutable guard | Audit guard rejects any update/delete path; append-only contract tests (C20-INV-07 pattern; C22-INV-EX-003 `ExecutionLedger` precedent) |
| Atomicity | The event write and the entity transition commit together (single writer; validation-before-write; no partial event) |
| Persistence mechanism | Decided at WP2.1A: the table mechanism (e.g., Espo extension `AfterInstall` hook / raw DDL / `DataManager` rebuild) is part of the ADR; **this Plan does not pre-authorize any audit table** |
| Failed-generation-intent events | **Before WP2.1A ADR ratification:** minimum-evidence-gate failures produce a requester-facing error + structured application log/telemetry only — **no AIJob, no Brief, no AIRequestLog, no persistent failed-generation-intent record, no third request entity**. **After ratification, and only if the ADR explicitly approves:** a `PRE_DISPATCH_GATE_FAILURE` append-only audit event carrying at minimum: actor; timestamp; `opportunityCandidateId`; purpose; failed gate code; source reference summary; no-provider-invocation marker; no-AIJob marker; request correlation ID |

### 15.4 First-class-entity judgment and authorization gate

- **Preliminary judgment: YES — the audit store constitutes a first-class persistent artifact** (a dedicated append-only event table) beyond the ratified "exactly one persistent C25 artifact type in WP2" budget. WP2.1A confirms or revises this judgment.
- The charter OQ-B gate: "Ratify audit-storage design in WP2.1 Foundation Review"; the charter also states a first-class entity requires an ADR judgment **before implementation**.
- **This Plan therefore does NOT authorize implementation of the audit store.** The design above is documented for ratification; a **C25 ADR amendment** must be ratified (WP2.1A) before any audit-store code, entity, metadata, or table mechanism may be written.
- No `BriefAudit` / `BriefReviewEvent` entity is created without that ADR amendment. The entity budget remains exactly one persistent C25 artifact: `CommercialBrief`.

---

## 16. Review Lifecycle and Dispositions

### 16.1 Lifecycle (ratified, not re-opened)

```text
reviewStatus:   GENERATED → REVIEWED → ACCEPTED | DISMISSED
                (ACCEPTED / DISMISSED are terminal review outcomes;
                 reviewStatus is never overwritten by supersession, invalidation,
                 archival, or governed deletion)

validityDisposition:   NONE → INVALIDATED   (orthogonal; does not change reviewStatus)
retentionDisposition:  ACTIVE → ARCHIVED    (orthogonal; does not change reviewStatus or validityDisposition)
SUPERSEDED:            derived at read time from the supersedesBriefId chain (never persisted)
Deletion:              deleteId governed soft-delete (NOT a status, NOT a disposition)
```

### 16.2 Transition matrix (ratified §12.2, §16.1 — enforced verbatim)

| Transition | From | To | Action key | Save option (`CommercialBriefSaveOption::`) | Guard |
|---|---|---|---|---|---|
| Generate | (none) | GENERATED | `brief.generate` | `GENERATION_AUTHORIZED` | `CommercialBriefImmutableGuard` |
| Review | GENERATED | REVIEWED | `brief.review` | `STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` |
| Accept | REVIEWED | ACCEPTED | `brief.accept` | `STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` |
| Dismiss | REVIEWED | DISMISSED | `brief.dismiss` | `STATUS_MUTATION_AUTHORIZED` | `CommercialBriefStateGuard` |
| Invalidate | any reviewStatus | (unchanged) validity=INVALIDATED | `brief.invalidate` | `VALIDITY_DISPOSITION_AUTHORIZED` | `CommercialBriefStateGuard` (reviewStatus unchanged) |
| Archive | terminal/invalidated | (unchanged) retention=ARCHIVED | `brief.archive` | `RETENTION_DISPOSITION_AUTHORIZED` | `CommercialBriefStateGuard` (reviewStatus/validityDisposition unchanged) |
| Delete | any | `deleteId` set | `brief.delete` | `DELETION_AUTHORIZED` | `CommercialBriefStateGuard` (deleteId-only mutation) |

### 16.3 Disposition semantics (ratified)

- `acceptanceScope` is meaningful **only** when `reviewStatus = ACCEPTED`; DISMISSED/INVALIDATED/ARCHIVED never carry or fabricate it.
- `validityDisposition = INVALIDATED` withdraws decision-support validity (source error, source withdrawal, generation error, or other D3 governance reason). Requires reason, actor, timestamp, append-only audit. No automatic source change, regeneration, or side effect.
- `retentionDisposition = ARCHIVED` is a retention/presentation disposition, not a review outcome. Requires reason, actor, timestamp, append-only audit. Archive ≠ delete; does not modify `deleteId`, provenance, or the supersession graph.
- Dispositions coexist: a brief may simultaneously be ACCEPTED + INVALIDATED + ARCHIVED + superseded-derived; presentation labels never overwrite one another.

---

## 17. Supersession Model

| Element | Resolution |
|---|---|
| New revision | Created only by explicit human regeneration (`brief.regenerate` with a unique `regenerationRequestId`, §14.4); a new Brief with `supersedesBriefId` set once at creation |
| Prior revision | Keeps original `reviewStatus`, `validityDisposition`, `retentionDisposition` **unchanged** |
| Derived semantics | `SUPERSEDED`/`CURRENT` derived at read time from the `supersedesBriefId` chain + creation ordering (G11 §6.4 precedent); the derivation runs at the service layer and **includes soft-deleted rows** so the graph remains traversable after governed deletion |
| Forbidden | `isCurrent`, `isLatest`, editable `isSuperseded`/`superseded` boolean — never stored, never editable |
| Correction | Supersession only; never edit/delete in place (C23-INV-OWN-003, C24 supersession precedent) |
| Graph retention | The supersession graph survives archival and governed deletion (provenance/supersession integrity; §18) |
| Read-time indicator | Superseded revisions default collapsed/hidden; current revision default view; review outcome never hidden (§19) |

---

## 18. Retention and Deletion

### 18.1 Archive (OQ-F — proposed defaults subject to WP2.3 Foundation Review / D5 ratification)

| Item | Resolution |
|---|---|
| Eligible reviewStatus for archive | **Terminal review outcomes (`ACCEPTED`, `DISMISSED`) or `INVALIDATED`** records only. `GENERATED`/`REVIEWED` are not archive-eligible |
| Invalidated auto-archive | **NO** (default) |
| Archive trigger | **Only** the explicit human `brief.archive` action — never automatic |
| Archive recoverable? | **No restoration in this Plan.** `brief.unarchive` is **excluded from the current action set**; any future restoration capability requires a C25 Charter Amendment + ADR + Plan Amendment |
| Archive retention period | **Proposed default: minimum 90 days** in ARCHIVED before governed-deletion eligibility — **not ratified**; subject to WP2.3 Foundation Review / D5 decision; configurable via workflow metadata only after ratification; subject to legal/audit hold |
| Archive effect | Retention/presentation only; `reviewStatus`, `validityDisposition`, content, `deleteId`, provenance, supersession graph unchanged |

### 18.2 Governed deletion

| Item | Resolution |
|---|---|
| Nature | `deleteId` governed soft-delete path — **not** a reviewStatus or disposition value |
| Eligibility | Review outcome terminal (ACCEPTED/DISMISSED) **or** INVALIDATED, **and** `retentionDisposition = ARCHIVED`. Deletion of non-archived records requires documented legal/audit-hold justification and is **not** the default |
| Eligibility ≠ deletion | **Deletion eligibility never triggers deletion.** Every deletion is an explicit human `brief.delete` action with mandatory reason |
| Deletion reason | Mandatory |
| Deletion audit | Mandatory append-only event: `deleteId`, actor, timestamp, reason |
| `deleteId` behavior | Set → record excluded from default reads; no physical erase |
| Source/provenance retention | Provenance chain and source references **survive deletion** (C25-INV-PROV-001); C20 AIJob/AIRequestLog records independent of brief lifecycle |
| Supersession graph | **Retained** across deletion; internal governance accessibility (service-layer traversal incl. soft-deleted rows, §17) is preserved |
| Legal / audit hold | **Representation unresolved** — no hold field is added by this Plan (§8.2). Hold representation is ratified by the WP2.3 Foundation Review / D5 decision; the exact field/relationship is added to the allowlist only after that approval. **Until resolved, no deletion implementation is permitted** |
| Accepted / dismissed outcomes | **Permanently preserved** — review outcomes are never hidden (de-emphasis without hiding) |
| Archived visibility | Archived records are excluded from the default workspace active view; they remain readable via an **explicit include-archived filter** under brief ACL; source navigation re-ACL'd |
| Portal | Always denied — for archived, active, and deleted records alike |
| No cascade | Deleting a brief never cascades to source records or C20 records |

---

## 19. Presentation Model

### 19.1 D2 boundary (WP1 + WP2 composition, resolved)

| Rule | Resolution |
|---|---|
| Visual distinction | AI brief content visually distinct from CRM records; visible boundary divider (D2) |
| One-click source navigation | Every source reference navigates to governed source detail (WP1 `GetGovernedSourceDetail`, 16-type allowlist; re-ACL'd, denied → safe 404) |
| Advisory + legal designation | Mandatory display of human-readable and machine-readable designation on every render |
| Superseded de-emphasis | Superseded revisions default collapsed/hidden; current revision default view |
| Review outcome + dispositions | Workspace simultaneously displays Review status, Validity, Retention, and Superseded-derived indicator — labels never overwrite one another |
| De-emphasis without hiding | Superseded, invalidated, archived records may be de-emphasized in default ordering/display; review outcome is **never** hidden |
| Anchor availability | Unreadable anchor renders unavailable/restricted; no source content leaked |
| Freshness surfacing | `STALE`/`ARCHIVAL` warnings surfaced, never suppressed; evidence-changed-since-generation indicator |
| Confidence + limitations | Four confidence elements (evidence basis, confidence indication, freshness consideration, limitation statement) and a first-class limitation statement |
| B5 scoping | Not in standard CRM lists / global search without explicit "include AI projections" toggle |
| No CRM-mutation proxy | No "Create Opportunity" or equivalent proxy; CRM records open in owning surfaces |
| Portal | Denied |

### 19.2 Per-claim masking (mandatory default, §15.3)

- The content model carries a structured claim → source reference mapping (`claimSourceMap[]`, §8.4).
- When the current reader cannot read a source, every claim bound to that source renders a **restricted-evidence marker** (a claim is masked only when **none** of its anchors is readable, §8.4).
- Masked rendering **never** exposes source original text, sensitive fields, or restricted information inferred from them.
- Source navigation returns a safe not-found/forbidden presentation that does not reveal whether the record exists.
- Claims independently supported by sources the reader can still read remain visible.
- Whole-brief restriction is permitted **only** as a conservative fallback when claims cannot be safely separated.
- "Keep the full claim and only show a risk marker" is **NOT** an allowed default.

### 19.3 XSS safety

- No raw HTML stored; all generated text rendered with escaping (markdown-lite plain text).
- No unsanitized AI output is injected into the DOM; no `innerHTML` from stored content.
- Runtime browser evidence (D2 markers, safe rendering) is verified in WP2.4/WP2.5.

### 19.4 Runtime browser evidence (WP2.4)

Browser-evidence checks: D2 divider present, designation visible, restricted-evidence markers render for lost-ACL readers, superseded default-collapsed, staleness warnings shown, no CRM-mutation proxy, no source leakage.

---

## 20. Services and Guards — Minimum Viable Class Set

### 20.1 Service inventory (minimum set)

All services live under `Espo\Modules\CommercialIntelligence\Services`. Each is a plain DI class (EntityManager + Acl + authorization), following the live C24/Prospecting pattern. Charter ratified-role names map onto these classes as noted. **No standalone class is retained without the justification shown.**

| Service (class) | Charter role mapping | Exact responsibility | Why existing Espo/C24 pattern cannot cover it | Transaction boundary | Security invariant | Owning WP | Test class |
|---|---|---|---|---|---|---|---|
| `CommercialBriefGenerationService` | `BriefGenerationService` + supersession validation (creation side) + idempotency | Human-initiated generation and regeneration: gate, snapshot, idempotency reservation (internal component/helper — no separate service: the reservation shares the generation transaction and has no independent security invariant), AIJob creation via C20 interface, revision creation with `supersedesBriefId` validation | No existing service creates governed C25 artifacts; WP1 `ContextAssemblyService` is read-only assembly | One generation transaction; no partial Brief | Creation only via `GENERATION_AUTHORIZED` save option; source-ACL-filtered inputs only | WP2.2 | `TestBriefGeneration` |
| `CommercialBriefValidationService` | `BriefValidationService` + provenance consistency + `CommercialBriefSupersessionService` + `CommercialBriefProvenanceService` (merged: all are pure validators sharing one call site at generation; independent classes would be thin wrappers with no transaction boundary of their own) | Mandatory/forbidden field validation; four-section completeness; provenance completeness + AIRequestLog consistency; claim/anchor orphan validation; `supersedesBriefId` set-once validation | C24 validates inside its lifecycle service; C25 needs a generation-side validator callable before persistence — single call site, so one class | N/A (pure) | Rejects before persistence; never writes | WP2.2 | `TestBriefValidation` |
| `CommercialBriefLifecycleService` | `BriefLifecycleTransitionService` + disposition service (merged: one service owns all governed mutations; explicit internal methods `review/accept/dismiss/invalidate/archive/delete` per transition/disposition) | All review-status, disposition, and governed-deletion transitions; atomic append-only audit event per transition | C24 precedent is exactly one lifecycle service per entity (`OpportunityCandidateLifecycleService` with per-transition methods) | Single transition + audit event commit together | State writes only via `CommercialBriefSaveOption` tokens; matrix enforced by `CommercialBriefStateGuard` | WP2.3 | `TestBriefLifecycle` |
| `CommercialBriefAuthorizationService` | C25 authorization service (new, C25-scoped) | Action-key → capability → effective-role resolution via `app.commercialBriefWorkflow`; record-ACL dual check; portal rejection; admin action-role skip only | The existing Prospecting `WorkflowAuthorizationService` is hardwired to Prospecting (metadata key, action vocabulary, exact-parity validation) and **must not be modified**; CommercialIntelligence already replicates patterns module-locally (WP1 `VisibilityInheritanceService`) | N/A (pure decision) | Recognizes only `brief.*`; no hardcoded role names outside the configurable fallback adapter | WP2.1B | `TestBriefAuthorization` |
| `CommercialBriefVisibilityService` | Read-time rendering service | Read-time rendering model: masked claims, designations, dispositions, superseded indicator, anchor availability | WP1 presenters render assembled context, not persisted briefs with claim-level masking | N/A (read path) | Never exposes restricted source content (§19.2) | WP2.4 | `TestBriefVisibility` |
| `CommercialBriefAuditWriter` | Audit mechanism writer | **ADR-gated.** Append-only event writes for generation/review/disposition/deletion/reuse/gate-failure events | No Espo audit/stream equivalent (§15.2) | Atomic with the owning transition | Append-only; no update/delete path | WP2.3 (default; or WP2.1B if the WP2.1A ADR assigns it there) | `TestBriefAuditGuard` |

### 20.2 Guards (hooks, `Espo\Core\Hook\Hook\BeforeSave`, static `$order`)

Minimum set — one immutable-field guard and one state guard, matching the live C24 two-guard precedent (`OpportunityImmutableGuard` + `OpportunityCandidateLifecycleGuard`):

| Guard | Order | Enforces |
|---|---|---|
| `CommercialBriefImmutableGuard` | 1000 | Content/provenance/source-reference/designation/anchor fields never change after generation; `supersedesBriefId` immutable once set; `modifiedAt` only via governed mutations; creation only via `GENERATION_AUTHORIZED` (no generic create path) |
| `CommercialBriefStateGuard` | 1010 | All governed mutations (reviewStatus, validityDisposition, retentionDisposition, deleteId) only via their `CommercialBriefSaveOption` token; transition matrix verbatim; per-field-set token checks (`STATUS_MUTATION` / `VALIDITY_DISPOSITION` / `RETENTION_DISPOSITION` / `DELETION`); atomic append-valid audit (exactly one new event, from/to match, actor/reason/timestamp present) — one guard safely distinguishes the field sets, mirroring the single `OpportunityCandidateLifecycleGuard` |
| `CommercialBriefAuditGuard` | 1050 | **ADR-gated.** Append-only; no update/delete of audit events |

### 20.3 Save options

Single internal final class with constant string tokens (live C24 save-option class precedent — one class per entity, constants inside). **Not one save option per action** — tokens are per mutation channel (field set), and `review`/`accept`/`dismiss` share the status-mutation token:

| Constant (on `CommercialBriefSaveOption`) | Value | Grants |
|---|---|---|
| `GENERATION_AUTHORIZED` | `c25.briefGenerationAuthorized` | Generation-only write of a new Brief |
| `STATUS_MUTATION_AUTHORIZED` | `c25.briefStatusMutationAuthorized` | reviewStatus transitions |
| `VALIDITY_DISPOSITION_AUTHORIZED` | `c25.briefValidityDispositionAuthorized` | Validity disposition writes |
| `RETENTION_DISPOSITION_AUTHORIZED` | `c25.briefRetentionDispositionAuthorized` | Retention disposition writes |
| `DELETION_AUTHORIZED` | `c25.briefDeletionAuthorized` | Governed soft-delete |
| `AUDIT_WRITE_AUTHORIZED` | `c25.briefAuditWriteAuthorized` | Audit event append (**ADR-gated**) |

### 20.4 Action authorization integration

- Every governed endpoint calls `CommercialBriefAuthorizationService` first (action-key → capability → effective roles via workflow metadata `app.commercialBriefWorkflow.actionRoleBindings`), then the entity ACL check (`acl->checkEntityRead`), then the source ACL prerequisite where applicable, then the owning service with the save option, then the guard.
- Three layers are always distinct: **record ACL** (read), **action authorization** (capability), **transition guard** (state machine + save option). None replaces another.
- No hardcoded role names in any business service; fallback bindings only in the authorization metadata adapter, configurable.

### 20.5 Real-code pattern citations (live tree)

- Entity: `Espo\Core\ORM\Entity` + `ENTITY_TYPE` constant — `crm-extension/files/custom/Espo/Modules/Prospecting/Entities/OpportunityCandidate.php`.
- Controller resolution: **no custom controller** — live C24 governed entities have none; Espo falls back to base `Espo\Core\Controllers\Record` for `type: Base`.
- Governed endpoints: `Api\* implements Espo\Core\Api\Action` + `Resources/routes.json` — live `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostQuoteWorkflowAction.php` (49-line thin dispatcher) and `Resources/routes.json` (`/Prospecting/quote/:id/workflow/:action`).
- Guards: `Espo\Core\Hook\Hook\BeforeSave` with static `$order` — live `Hooks/OpportunityCandidate/OpportunityCandidateLifecycleGuard.php`, `OpportunityCandidateImmutableGuard.php`; `Hooks/AIJob/AIJobStatusMutationGuard.php`.
- Authorization: live `Services/WorkflowAuthorizationService.php` (**existing Prospecting workflow infrastructure** — pattern precedent only; not modified) + `Resources/metadata/app/prospectingWorkflow.json` (`version`, `governanceMarker`, `actionRoleBindings`).
- Save options: live `Services/C24OpportunityCandidateSaveOption.php` (single class, token constant, private constructor); `Services/AIJobStatusMutationSaveOption.php`.
- Scope/ACL metadata: live `Resources/metadata/scopes/{OpportunityCandidate,RevenueInsight}.json` (`object:false`, `tab:false`, `acl:true`, `aclPortal:false`, `aclActionList:["read"]`); `aclDefs/OpportunityCandidate.json` = `{}`; `app/acl.json` (`mandatory`/`adminMandatory.scopeLevel`); `app/aclPortal.json` (CommercialIntelligence module, portal mandatory-false precedent).
- Schema mechanism: **Espo metadata rebuild** — `docs/deployment/UPGRADE.md` (alpha versions carry metadata changes without migration scripts); enforced by `crm-extension/tests/test_extension_skeleton.py::test_no_database_migration_artifacts` (zero migration/SQL files in the extension).

---

## 21. Security and Leakage Controls

| Control | Enforcement |
|---|---|
| No outbound HTTP from CRM PHP | C20-INV-03; all provider I/O via connector; C25 has no HTTP transport (C25-INV-SEC-001) |
| No credential access | C25 holds no provider/credential/SDK/transport ownership; forbidden fields (§8.2) |
| No source leakage | Source original content never copied into the brief; references only; re-ACL at every read (safe 404) |
| Per-claim masking | Mandatory default; restricted-evidence markers; no inferred-info leakage (§19.2) |
| No CRM-mutation proxy | No "Create Opportunity"/writeback fields; CRM records open in owning surfaces |
| XSS safety | No raw HTML; escaping contract; no unsanitized AI output into DOM |
| No write path to bypass | create/edit/delete forbidden by ACL+metadata; only save-option-gated transitions exist |
| No execution authority | No send/execute/ActionGate fields or calls; zero-side-effect ACCEPTED |
| No batch/autonomous | Human-initiated only; no scheduler/worker/webhook/queue |
| Portal denial | `aclPortal: false` + `app/aclPortal.json` mandatory false; portal users have no keys and no read |
| Admin no-bypass | Admin skips action-role permission only; never skips record ACL, source ACL, reason, audit, lifecycle guard, or leakage control |
| Provenance survival | Chain survives deletion (C25-INV-PROV-001) |

---

## 22. Work Package WP2.0 — C20 Dependency Resolution

| Item | Detail |
|---|---|
| Purpose | Secure the three C20-governed readiness dependencies (§7) and produce the go/no-go gate. **No C25 generation code.** |
| Preconditions | WP2 charter ratified; WP2 Plan ratified; C20 documents available |
| In scope | C20 dependency decision package; contract verification (`CapabilityResolutionRequest`/`Result`, `allowed_provider_bindings`, `allowed_purposes`, `PURPOSE_NOT_ALLOWED`, `CompletionRequest`/`Result`, AIJob/AIRequestLog field contracts — against the **live** AIPlatform tree); invariant readiness evidence (C20-INV-05…11 ACTIVE); boundary test requirements; go/no-go gate; freeze of the C25→C20 invocation contract |
| Out of scope | Any C25 generation implementation; any C20 entity/service/contract change; ProviderRoute creation; capability-value addition; binding-surface UI/DB decisions |
| Exact files (candidate, C20-governed) | C20 dependency decision package, contract verification evidence, boundary-test requirements, go/no-go record — under `docs/audit/` + C20 change package (see §28.4). No `crm-extension/.../CommercialIntelligence` files |
| Services | None created in this WP |
| Metadata | None created in this WP |
| Routes/actions | None |
| Tests | C20-side contract verification (C20-owned); boundary-test requirements authored |
| Static verification | Contract field names verified against frozen docs and the live tree; DTO schema cross-checked |
| Runtime verification | None (no runtime change) |
| Security checks | No provider/credential/HTTP exposure; no capability change from C25 |
| Cross-phase boundary checks | C25→C20 boundary: no C25 write to C20 entities; no C20 change authored from C25 |
| Entry gate | C20 docs accessible; WP2 charter + Plan ratified |
| Exit gate | All three dependencies resolved and ratified by C20 governance; go/no-go signed |
| Rollback | Documentation-only; no runtime rollback |
| Freeze evidence | C20 decision package + invariant-readiness evidence archived |
| Implementation authorization status | **NO code in this WP** — documentation/gate only |

---

## 23. Work Packages WP2.1A and WP2.1B

### 23.1 WP2.1A — Audit Storage Decision and ADR Ratification (documentation/governance only)

| Item | Detail |
|---|---|
| Purpose | Decide the internal append-only audit persistence contract and complete the C25 ADR amendment. **Documentation and governance only — zero code.** |
| Preconditions | WP2.0 exit (go/no-go signed); Foundation Review context |
| In scope | Verify Espo audit/stream cannot satisfy the append-only event contract (§15.2 evidence, against the live tree where inspectable); define the internal audit persistence contract (§15.3 input); judge whether the store constitutes a first-class governed artifact; define the governance classification (CRM entity vs entity scope vs internal persistent record vs database table vs audit event vs first-class governed artifact); define the persistence/table mechanism (e.g., Espo extension `AfterInstall` hook / raw DDL / `DataManager` rebuild) — decision recorded in the ADR; define retention/deletion rules for audit events; complete the **ADR amendment**; independent review and ratification of the ADR |
| Out of scope | Audit table; audit entity; audit writer; audit guard; migration; any code; any test |
| Exact files (candidate) | `docs/audit/ADR-C25-00x_BRIEF_REVIEW_AUDIT_STORAGE.md` (amendment); WP2.1A Foundation Review record. **No `crm-extension/` files** |
| Entry gate | WP2.0 exit; Foundation Review scheduled |
| Exit gate | **ADR ratified; entity/artifact budget reconciled; persistence mechanism approved; retention/deletion rules approved; exact code allowlist for the audit implementation approved (and assigned to WP2.1B or WP2.3)** |
| Rollback | Documentation-only |
| Freeze evidence | Ratified ADR amendment + review record |
| Implementation authorization status | **NO code in this WP** — documentation/governance only |

### 23.2 WP2.1B — CommercialBrief Contract and Persistence

| Item | Detail |
|---|---|
| Purpose | `CommercialBrief` entity + scope/ACL/workflow metadata; field schema; immutability and state guards + save option; anchor link; provenance schema; authorization service; static contract tests. **Starts only after WP2.1A is ratified.** |
| Preconditions | **WP2.1A ADR ratified**; Foundation Review context |
| In scope | Entity contract; metadata (entityDefs/scopes/aclDefs/app.acl/app.aclPortal/workflow metadata/i18n); field model (§8); `CommercialBriefImmutableGuard`; `CommercialBriefStateGuard`; `CommercialBriefSaveOption`; `CommercialBriefAuthorizationService`; anchor link; provenance schema; schema via **Espo metadata rebuild** (no migration files — forbidden by repo convention, §20.5); static tests. **Audit writer only if the WP2.1A ADR explicitly authorizes it and assigns it to this WP (default assignment: WP2.3)** |
| Out of scope | Generation logic; AIJob invocation; review transitions; presentation; masking; runtime tests; audit implementation (unless ADR-assigned here) |
| Exact files (candidate) | §28.1 rows owned by WP2.1B (entity, save option, two ungated guards, authorization service, metadata incl. i18n + app/aclPortal, entityDefs, scopes, aclDefs) |
| Services | `CommercialBriefAuthorizationService` |
| Metadata | As §11.3; `aclActionList: ["read"]`; admin create/edit/delete `"no"`; portal mandatory-false |
| Routes/actions | None (route table created in WP2.2, §28.1) |
| Tests | Contract tests: field allowlist/denylist, immutable fields, reviewStatus enum, disposition enums, SUPERSEDED-not-persisted, no authority fields, no CRM Core FK, no legal-hold field, C20 provenance completeness, JSON bounds and malformed `claimSourceMap`/`sourceEvidence` rejection, i18n key parity, no migration artifacts, no controller file |
| Static verification | Metadata cross-check; no generic create/update path; save-option presence; portal mandatory-false registered |
| Runtime verification | None in this WP (deferred to WP2.5, WP1 honesty convention) |
| Security checks | No leakage; no credential fields; portal denial registered |
| Cross-phase boundary checks | No C24/CRM/C22/C20 writes; entity budget = 1 (audit artifacts only per ratified ADR) |
| Entry gate | **WP2.1A ADR ratified** |
| Exit gate | Contract tests green; provenance schema validated |
| Rollback | Metadata + entity reversible before generation exists |
| Freeze evidence | Static contract tests + WP2.1A ratification record |
| Implementation authorization status | **NO — must be separately authorized before implementation** |

---

## 24. Work Package WP2.2 — Generation and Validation Boundary

| Item | Detail |
|---|---|
| Purpose | Human-initiated generation and regeneration; minimum-evidence gate; context snapshot/reference; C20 invocation contract; parsing; four-section validation; claim-source validation; provenance validation; idempotency (six identities); sync/async; failure behavior; no partial Brief; no business-state mutation |
| Preconditions | WP2.0 C20 dependency ratified (D-1/D-2/D-3); **WP2.1A audit ADR ratified**; WP2.1B exit; audit write path for generation/intent events available per the ADR assignment (§23.1) |
| In scope | `CommercialBriefGenerationService` (incl. idempotency component + supersession validation on create); `CommercialBriefValidationService` (incl. provenance consistency); evidence gate (§9.2); idempotency (§14); AIJob interaction (§13); failure mapping; generation versioning; no-partial rule; generate + regenerate endpoints and the complete route table (§12.3) |
| Out of scope | Review lifecycle; presentation; audit store implementation (WP2.1B-if-assigned / WP2.3 default) |
| Exact files (candidate) | §28.1 rows owned by WP2.2 (`CommercialBriefGenerationService.php`, `CommercialBriefValidationService.php`, `Api/PostBriefGenerate.php`, `Api/PostBriefRegenerate.php`, `Resources/routes.json` — created with the complete 3-route table, never modified by another WP) |
| Services | Generation (with internal idempotency component), validation |
| Metadata | None new beyond WP2.1B (workflow metadata purpose registration) |
| Routes/actions | `brief.generate`, `brief.regenerate` endpoints; full route table created (workflow dispatcher route included; dispatcher class arrives in WP2.3 — route entries are declarative and inert until called) |
| Tests | Generation service; validation service; idempotency (§29 — incl. same-evidence generate dedupes in window; **same-evidence regenerate in window creates a new revision**; duplicate `regenerationRequestId` is idempotent; different anchors never collide); evidence threshold; failure matrix (NETWORK/RATE_LIMIT/QUOTA/CONTENT_FILTER/parse/incomplete/missing provenance/duplicate/stale/deleted anchor/unreadable source); **pre-dispatch gate failure before audit ADR creates no persistent record** |
| Static verification | No partial-write path; no business-state mutation; provenance completeness |
| Runtime verification | Deferred to WP2.5 (sync/async flow; gate-failure → no AIJob/no Brief; retry behavior) |
| Security checks | No provider/credential/HTTP; no prior-brief reads; source ACL enforcement |
| Cross-phase boundary checks | No C24/CRM/C22 writes; no auto Lead/Opportunity; no score/rank authority; no batch; no autonomous trigger |
| Entry gate | WP2.0 C20 ratification; **WP2.1A ADR ratified**; WP2.1B exit |
| Exit gate | Generation boundary tests green; idempotency verified (incl. regeneration rules); no-partial proven |
| Rollback | Generation disabled via metadata; no persisted artifacts beyond briefs |
| Freeze evidence | Boundary + failure matrix evidence |
| Implementation authorization status | **NO — blocked until WP2.0 dependency ratified + separate authorization** |

---

## 25. Work Package WP2.3 — Human Review Lifecycle, Dispositions and Approved Audit Implementation

| Item | Detail |
|---|---|
| Purpose | Full review/disposition matrix; accept/dismiss/invalidate/archive/delete; **approved audit implementation** (per WP2.1A ADR, default assignment); dispositions; supersession presentation rules; retention; ACL/action mapping activation |
| Preconditions | WP2.1B exit; WP2.2 exit; audit-storage ADR ratified (WP2.1A); legal/audit hold representation resolved (Foundation Review / D5) **before any deletion implementation** |
| In scope | `CommercialBriefLifecycleService` (review/accept/dismiss/invalidate/archive/delete methods); workflow dispatcher (`Api\PostBriefWorkflowAction`); audit writer + audit guard **if ADR-assigned here (default)**; retention rules; reason/audit enforcement; WP2.3 Foundation Review decisions: 90-day retention value, dedupe window value, legal/audit hold representation (exact field/relationship added to the allowlist only after approval) |
| Out of scope | Generation; presentation; masking rendering (WP2.4) |
| Exact files (candidate) | §28.1 rows owned by WP2.3 (`CommercialBriefLifecycleService.php`, `Api/PostBriefWorkflowAction.php`) + §28.1-conditional ADR-gated audit rows (only per ratified ADR) |
| Services | Lifecycle service; audit writer (ADR-gated) |
| Metadata | None new (workflow bindings already complete from WP2.1B) |
| Routes/actions | Workflow dispatcher actions (`brief.review/accept/dismiss/invalidate/archive/delete`) go live |
| Tests | Lifecycle; disposition; audit append-only; reason requirement; acceptanceScope; retention; deletion; route ID binding; unknown action rejected; dispatcher allowlist; **no unarchive action exists**; **90-day rule disabled until Foundation Review ratification**; **legal hold unresolved ⇒ deletion denied** |
| Static verification | No mutable JSON history; no partial event; append-only contract; no `brief.unarchive` in action registry |
| Runtime verification | Deferred to WP2.5 (transition matrix; admin no-bypass; portal denial; zero-side-effect ACCEPTED) |
| Security checks | No audit deletion; no source cascade; no execution authority |
| Cross-phase boundary checks | No C24/CRM/C22 writes; no AIRequestLog on accept; no auto action |
| Entry gate | WP2.1B exit; WP2.2 exit; ADR-gated audit ratified |
| Exit gate | Review/disposition matrix green; audit append-only proven; OQ-F defaults ratified by Foundation Review |
| Rollback | Transition disabled via metadata; audit events immutable |
| Freeze evidence | Audit + lifecycle evidence |
| Implementation authorization status | **NO — separate authorization required; audit store additionally ADR-gated; deletion additionally gated on legal/audit hold resolution** |

---

## 26. Work Package WP2.4 — Workspace Presentation

| Item | Detail |
|---|---|
| Purpose | WP1 context + WP2 Brief composition; review status; validity; retention; superseded indicator; per-claim masking; source navigation; D2 boundary; XSS safety; include-AI-projections (and include-archived) toggles; standard search/list exclusion; runtime browser evidence |
| Preconditions | WP2.1B/WP2.2/WP2.3 exits (read surfaces + lifecycle present) |
| In scope | `CommercialBriefVisibilityService`; D2 presentation; masking default (§19.2); governed source navigation re-ACL; designation display; freshness surfacing; superseded de-emphasis; B5 toggle; browser evidence; workspace client composition files (WP1 custom client precedent: `files/client/custom/src/...`) |
| Out of scope | Any write path; masking bypass |
| Exact files (candidate) | §28.1 rows owned by WP2.4 (`CommercialBriefVisibilityService.php`, workspace client composition views/templates). **No `clientDefs/CommercialBrief.json`** (verified: governed `tab:false` entities carry none); **no layout files** — none expected for a `tab:false` governed entity (WP1 used custom client views, not entity layouts); if WP2.4 Foundation Review proves a layout need, it is added to the allowlist then |
| Services | Visibility service |
| Metadata | None new (B5 exclusion achieved via scope flags + workspace toggle, §11.3) |
| Routes/actions | Read + governed source navigation only |
| Tests | Masking; source navigation; standard list/search exclusion; D2 markers; XSS safety |
| Static verification | No source-leakage in masked render; escaping contract |
| Runtime verification | Browser evidence; portal denial |
| Security checks | Per-claim masking; safe 404; no CRM-mutation proxy |
| Cross-phase boundary checks | WP1 context + WP2 brief composition; no write |
| Entry gate | Read surfaces exist |
| Exit gate | D2 + masking runtime evidence green |
| Rollback | Presentation-only; disable via client composition |
| Freeze evidence | Browser-evidence artifacts |
| Implementation authorization status | **NO — separate authorization required** |

---

## 27. Work Package WP2.5 — Runtime Verification and Freeze

| Item | Detail |
|---|---|
| Purpose | API matrix; action matrix; ACL roles; portal denial; admin no-bypass; source leakage; no-write; no lifecycle mutation; no execution; provider isolation; failure matrix; idempotency (incl. regeneration rules); supersession; retention; browser evidence; independent review; freeze criteria |
| Preconditions | WP2.0–WP2.4 exits; C20 dependency ratified |
| In scope | Full boundary test suite (charter §24); ACCEPTED zero-side-effect proof; ACL matrix runtime verification; freeze review; invariant activation triggers; independent C20–C25 boundary verification |
| Out of scope | New feature code |
| Exact files (candidate) | `tests/test_phase3c25_wp2_5_*.py`, `docs/audit/PHASE3C25_WP2_FINAL_FREEZE_REVIEW.md`, freeze evidence |
| Services | None new |
| Metadata | None new |
| Routes/actions | None new |
| Tests | Full boundary + failure + runtime matrix (§29, §30, §31) |
| Static verification | Invariant compliance signature (ADV-001, HG-001, PROV-001, INT-006, OWN-001, SEC-001) |
| Runtime verification | Freeze criteria (§34) |
| Security checks | Provider isolation; no credential; no leakage; no batch/autonomous |
| Cross-phase boundary checks | Independent C20–C25 verification |
| Entry gate | All prior WPs exit |
| Exit gate | Freeze review signed |
| Rollback | Documented per-artifact rollback |
| Freeze evidence | Freeze review + boundary evidence archived |
| Implementation authorization status | **NO — separate authorization required** |

---

## 28. Exact Changed-File Allowlist

Every file has **exactly one owning WP**. Files are created only under separate authorization. Conditional (ADR-gated) files are listed separately and may exist only per the ratified WP2.1A ADR.

### 28.1 C25 files (candidate — created only under separate authorization)

`crm-extension/files/custom/Espo/Modules/CommercialIntelligence/`

| File | Owning WP |
|---|---|
| `Entities/CommercialBrief.php` | WP2.1B |
| `Services/CommercialBriefAuthorizationService.php` | WP2.1B |
| `Services/CommercialBriefSaveOption.php` (single class, 6 constants) | WP2.1B |
| `Hooks/CommercialBrief/CommercialBriefImmutableGuard.php` | WP2.1B |
| `Hooks/CommercialBrief/CommercialBriefStateGuard.php` | WP2.1B |
| `Resources/metadata/entityDefs/CommercialBrief.json` | WP2.1B |
| `Resources/metadata/scopes/CommercialBrief.json` | WP2.1B |
| `Resources/metadata/aclDefs/CommercialBrief.json` (`{}`) | WP2.1B |
| `Resources/metadata/app/acl.json` (**append**: `adminMandatory.scopeLevel.CommercialBrief`; no `mandatory` force-off) | WP2.1B |
| `Resources/metadata/app/aclPortal.json` (**append**: `mandatory.scopeLevel.CommercialBrief: false`) | WP2.1B |
| `Resources/metadata/app/commercialBriefWorkflow.json` | WP2.1B |
| `Resources/i18n/en_US/CommercialBrief.json` | WP2.1B |
| `Resources/i18n/zh_CN/CommercialBrief.json` (key parity) | WP2.1B |
| `Services/CommercialBriefGenerationService.php` (incl. internal idempotency component) | WP2.2 |
| `Services/CommercialBriefValidationService.php` (incl. provenance consistency + supersession validation) | WP2.2 |
| `Api/PostBriefGenerate.php` | WP2.2 |
| `Api/PostBriefRegenerate.php` | WP2.2 |
| `Resources/routes.json` (**modify existing** — created once with the complete 3-route table; no other WP modifies it) | WP2.2 |
| `Services/CommercialBriefLifecycleService.php` | WP2.3 |
| `Api/PostBriefWorkflowAction.php` (single workflow dispatcher) | WP2.3 |
| `Services/CommercialBriefVisibilityService.php` | WP2.4 |
| Workspace client composition files (views/templates under `crm-extension/files/client/custom/src/views/commercial-intelligence/` + `res/templates/commercial-intelligence/`, WP1 custom-client precedent) | WP2.4 |

**Explicitly excluded from the allowlist:**

| Excluded | Reason |
|---|---|
| `Controllers/CommercialBrief.php` (empty controller) | No necessity — Espo base Record controller resolution covers `type: Base`; live C24 governed entities have no controller file (§12.1). Re-add only with runtime evidence + allowlist amendment |
| Seven per-action API classes (`PostBriefReview/Accept/Dismiss/Invalidate/Archive/Delete`) | Replaced by the single workflow dispatcher `Api\PostBriefWorkflowAction` (§12.3) |
| `clientDefs/CommercialBrief.json` | Verified: governed `tab:false` read-only entities carry no clientDefs |
| Entity layout files (`layouts/…`) | None expected for a `tab:false` governed entity (WP1 used custom client views); added later only on proven WP2.4 need |
| Any migration / SQL file | Forbidden by repo convention (`test_no_database_migration_artifacts`); schema via Espo metadata rebuild |
| B5/search metadata file | Unneeded — exclusion via scope flags + workspace toggle (§11.3); the allowlist entry for search exclusion is the scopes file itself |
| `Services/CommercialBriefSupersessionService.php`, `Services/CommercialBriefProvenanceService.php`, `Services/CommercialBriefIdempotencyService.php` | Merged into generation/validation services (§20.1) — thin wrappers without independent transaction boundaries |
| Per-action save-option classes | Single `CommercialBriefSaveOption` class with per-channel constants (§20.3) |

### 28.1-conditional Audit implementation files (**ADR-gated — not authorized**)

May be created **only** after WP2.1A ADR ratification, at the ADR-assigned WP (default WP2.3; WP2.1B only if the ADR assigns it there). The exact files and the table mechanism (`AfterInstall` / raw DDL / `DataManager` rebuild) are fixed by the ADR, not by this Plan:

| Candidate file (shape only) | Owning WP |
|---|---|
| `Services/CommercialBriefAuditWriter.php` | Per ADR (default WP2.3) |
| `Hooks/CommercialBrief/CommercialBriefAuditGuard.php` | Per ADR (default WP2.3) |
| Audit table mechanism file(s) — mechanism decided by the ADR | Per ADR |

### 28.2 Tests (candidate)

Root `tests/` (C24/C25 convention — all C24/C25 tests live at repo root, not in `crm-extension/tests`):
`tests/test_phase3c25_wp2_1b_*.py`, `test_phase3c25_wp2_2_*.py`, `test_phase3c25_wp2_3_*.py`, `test_phase3c25_wp2_4_*.py`, `test_phase3c25_wp2_5_*.py`.
Plus inventory updates to `crm-extension/tests/test_extension_skeleton.py` and `crm-extension/tests/test_espo_php_namespace_contracts.py` (module file inventory conventions).

### 28.3 docs/audit (candidate)

`docs/audit/PHASE3C25_WP2_FINAL_FREEZE_REVIEW.md`; WP2.0 C20 dependency decision-package records; **WP2.1A audit-storage ADR amendment**; per-WP verification/freeze records.

### 28.4 C20 dependency files (separate governance/change package)

- Belong to an **independent C20 governance/change package** — never mixed into a C25 entity-implementation commit.
- Require their own **commit/tag/review** under C20 governance.
- Includes: CompletionCapability portfolio decision/amendment, ProviderBinding/allowed-provider-binding surface, C20-INV-05…11 activation + verification, connector contract changes (e.g., `chitu-connector/` capability additions). None is authored, committed, or tagged by C25.

### 28.5 Non-allowed groups

No routes/controllers beyond the allowlist; no frontend beyond WP2.4 composition files; no localization/layout churn beyond the allowlist; **no migration files anywhere** (entity schema via Espo rebuild; audit table mechanism only per ratified ADR).

---

## 29. Test Matrix

### Contract tests
| Test | Verifies |
|---|---|
| Field allowlist/denylist | Only ratified fields exist; forbidden fields absent (score, rank, priority, probability, revenueImpact, forecast, stage, isCurrent, approvedForOutreach, readyToCreateOpportunity, send, execute, credentials, prompt text, raw payload, CRM FKs, **legal/audit hold markers**) |
| Immutable fields | Content/provenance/source-refs/designation/anchor never change after generation |
| `reviewStatus` enum | Exactly 4 values; transition matrix verbatim; terminal states |
| Disposition enums | validity 2 values; retention 2 values; orthogonal to reviewStatus |
| SUPERSEDED not persisted | Derived at read time; no `isCurrent`/`isLatest`/editable superseded |
| No authority fields | No lifecycle/qualification/approval/priority authority |
| No CRM Core FK | No DB FK into CRM Core entities |
| C20 provenance completeness | sourceAIJobId/sourceAIRequestLogId/provider/model/capability/purpose/promptTemplateId/promptTemplateVersion present + consistent with AIRequestLog |
| JSON bounds | `sourceEvidence` / `claimSourceMap` schema, max counts, max serialized sizes enforced; **malformed `claimSourceMap` rejected** (orphan claim, orphan anchor, non-canonical ordering) |
| i18n parity | `en_US` / `zh_CN` key parity for `CommercialBrief.json` |
| No migration artifacts | Zero migration/SQL files (repo convention) |
| No controller file | `Controllers/CommercialBrief.php` absent |

### Route and dispatcher tests
| Test | Verifies |
|---|---|
| Route ID binding | `:id` route param binds the target Brief; missing/malformed id rejected; safe not-found |
| Unknown action rejected | `:action` outside the allowlist → `BadRequest`; no arbitrary method dispatch |
| Dispatcher allowlist | Exactly {review, accept, dismiss, invalidate, archive, delete} resolvable; alias mapping stable |
| Standalone routes | `generate` and `regenerate` routes present with their body contracts; workflow route present |
| No duplicate read API | GET read surface unchanged (standard Record read only) |

### Service tests
| Service | Tests |
|---|---|
| Generation | Gate passes/blocks; context snapshot; AIJob created after gate; no partial Brief; regeneration creates new AIJob + new revision; prior Brief untouched |
| Validation | Mandatory fields; provenance completeness; forbidden-field guard; evidence anchoring; four-section completeness; empty/whitespace section rejection; content length bounds |
| Idempotency | Request key; anchor-bound generation identity; dedupe window; requesterId excluded; retry attempt identity; ACL non-equivalence blocks reuse; **same-evidence generate within window dedupes**; **same-evidence regenerate within window creates new revision**; **duplicate `regenerationRequestId` is idempotent**; **different candidate + same evidence does not collide**; **failed regeneration does not mutate the old Brief**; **superseding Brief never resolves to the prior Brief through ordinary dedupe** |
| Lifecycle | Full transition matrix; terminal states; double-transition rejected |
| Disposition | validity/retention orthogonal writes; reason required |
| Supersession | supersedesBriefId once; prior unchanged; derived indicator; soft-deleted rows included in derivation |
| Audit | Append-only; full schema; atomic with transition; no update/delete |
| Source visibility | Read under brief ACL; re-ACL at navigation; masked claims |

### Gate-failure persistence tests
| Test | Verifies |
|---|---|
| Pre-ADR gate failure | Minimum-evidence failure before audit ADR ratification: requester-facing error; **no AIJob, no Brief, no AIRequestLog, no persistent failed-generation-intent record, no third request entity**; structured application log only |
| Post-ADR gate failure | After ADR ratification (if approved): `PRE_DISPATCH_GATE_FAILURE` event with the §15.3 field set (actor, timestamp, anchor, purpose, gate code, source summary, no-invocation/no-AIJob markers, correlation ID) |

### ACL tests
| Test | Verifies |
|---|---|
| Operator | generate/regenerate/archive granted; review keys denied |
| Reviewer | review/accept/dismiss/invalidate granted; generate denied |
| Governed Deletion | delete granted with reason/audit |
| Provenance Viewer | read-only provenance view, bounded by C20 ACL + source ACL |
| Unauthorized user | No keys, no brief read |
| Portal | All denied |
| Admin no-bypass | Admin skips action-role permission only; **cannot bypass source ACL, lifecycle guard, reason, or audit** |
| Source ACL loss | Per-claim masking; safe 404; no leakage |
| Claim masking | Restricted-evidence markers; independently-supported claims remain visible |
| Prospecting isolation | **C25 authorization service does not modify the Prospecting `WorkflowAuthorizationService`** (file untouched; separate metadata key) |

### Retention / deletion tests
| Test | Verifies |
|---|---|
| No unarchive | `brief.unarchive` absent from action registry, dispatcher allowlist, and workflow metadata |
| 90-day proposed | 90-day deletion-eligibility rule **disabled until WP2.3 Foundation Review ratification** |
| Legal hold unresolved | Deletion denied while hold representation is unresolved |
| Eligibility ≠ deletion | No automatic deletion path exists; every deletion is an explicit human action |
| Archived visibility | Archived excluded from default active view; visible via explicit include-archived filter under ACL; portal denied |

### Boundary tests
| Test | Verifies |
|---|---|
| No C24 transition | No call into C24 transition service |
| No CRM write | No Lead/Opportunity/Account/Quote/Revenue creation or lifecycle change |
| No C22 execution | No ActionGate/outreach/send |
| No provider SDK in C25 | No connector/provider SDK import |
| No HTTP from CRM | No outbound PHP HTTP (C20-INV-03) |
| No credential access | No credential read |
| No automatic Lead/Opportunity | No auto-create |
| No score/rank authority | No score/rank fields or behavior |
| No batch generation | No batch |
| No scheduler autonomous trigger | No autonomous trigger |

### Failure tests
| Failure | Verifies |
|---|---|
| NETWORK | Retryable within budget; no Brief |
| RATE_LIMIT | Retryable; Retry-After; no budget consumption |
| QUOTA | Terminal; no wasteful retry |
| CONTENT_FILTER | Terminal; no auto-retry of same prompt |
| Parse failure | Validation error; no Brief |
| Incomplete output | Rejected before persistence |
| Missing provenance | Rejected before persistence |
| Evidence threshold failure | No AIJob; no Brief; intent per §15.3 |
| Duplicate request | Returns existing generation within window |
| Stale source | Warning surfaced; generation proceeds |
| Deleted anchor | Gate fails; no Brief |
| Unreadable source | Gate fails (requester cannot read source) |

### Runtime tests
| Test | Verifies |
|---|---|
| Generate / review / accept / dismiss / invalidate / archive / supersede | End-to-end governed flows |
| Regenerate in window | Same evidence + explicit regeneration → new revision, not the prior Brief |
| Source navigation | Re-ACL; safe 404 |
| Masking | Renders per §19.2 |
| Standard list/search exclusion | B5 toggle semantics |
| Browser D2 markers | Distinction, designation, superseded collapse, staleness |
| Zero side effects | ACCEPTED proof — no AIRequestLog, no CRM/C24/C22/C20 change |

---

## 30. Runtime Verification Matrix

| Scenario | Expected | Verified at |
|---|---|---|
| Operator generates a brief | Brief GENERATED, immutable content, complete provenance | WP2.2/WP2.5 |
| Reviewer reviews then accepts | REVIEWED → ACCEPTED, acceptanceScope set, zero side effects | WP2.3/WP2.5 |
| Reviewer dismisses | REVIEWED → DISMISSED, outcomeReason required | WP2.3/WP2.5 |
| Invalidates | validityDisposition INVALIDATED, reviewStatus unchanged, reason required | WP2.3/WP2.5 |
| Archives | retentionDisposition ARCHIVED, no deleteId change, reason required | WP2.3/WP2.5 |
| Governed delete | deleteId set, provenance/supersession retained, audit event written; denied while legal hold unresolved | WP2.3/WP2.5 |
| Reader loses source ACL | Per-claim masking, safe 404, no leakage | WP2.4/WP2.5 |
| Portal user | Denied everywhere | WP2.1B/WP2.5 |
| Admin | Skips action-role permission only; no bypass of source ACL/guard/reason/audit | WP2.3/WP2.5 |
| Idempotent duplicate | Existing generation returned within window | WP2.2/WP2.5 |
| Explicit regeneration in window | New AIJob + new revision; prior Brief unchanged | WP2.2/WP2.5 |
| Provider isolation | No C25 HTTP/credential/SDK path | WP2.2/WP2.5 |

---

## 31. Cross-Phase Boundary Matrix

| Boundary | Rule | Enforced by |
|---|---|---|
| C25 → C20 | No C20 entity/service/contract change; no capability value; no ProviderRoute; no dispatch/routing; no credential read; provenance references only | §7; C25-INV-SEC-001; boundary tests |
| C25 → C21 | Read-only ResearchEvidence/AIQualificationInsight references; no score/qualification authority | C21-INV-03/07; evidence model |
| C25 → C22 | No ActionGate/outreach/send/execution; no ProspectCandidate mutation | C22-INV-EX-001/003; boundary tests |
| C25 → C23 | Read-only OptimizationInsight/PerformanceMetric; no metric redefinition | C23-INV-OWN-001; C24-INV-SEP-001 |
| C25 → C24 | No OpportunityCandidate lifecycle change; no ReplySignal/RevenueInsight/PipelineMetric mutation; anchor is read-only reference | C24-INV-SEP-002, C24-INV-LIFE-001; boundary tests |
| C25 → CRM Core | Zero writeback; no auto Lead/Opportunity; read-only context | C22-INV-CRM-001/002/003; C24-INV-REV-003 |
| C25 internal | Entity budget = 1; audit/feedback non-entity or ADR-amended; no JSON history; **Prospecting authorization service untouched** | §15; §11; freeze criteria |
| C25 workspace | object:false/tab:false; B5 toggle; portal denial | §11/§19 |

---

## 32. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| C20 dependency unresolved | WP2.0 is a hard gate; no generation implementation until ratified (§7) |
| Audit store judged first-class | WP2.1A ADR amendment before implementation; documented design; entity budget preserved (§15.4, §23.1) |
| Pre-ADR intent persistence drift | Pre-ADR: application log only, no persistent record; post-ADR: `PRE_DISPATCH_GATE_FAILURE` only if ADR-approved (§15.3) |
| Regeneration suppressed by dedupe | Regeneration exempt from generate dedupe; unique `regenerationRequestId`; idempotent retry (§14.4) |
| Cross-anchor hash collision | Anchor bound into `evidenceSetHash` and the canonical equivalence key (§8.4, §14.2) |
| Masking leak | Mandatory per-claim masking; whole-brief fallback only when separation impossible; runtime evidence in WP2.5 |
| Action-key/ACL gap | Workflow-metadata role bindings + C25 authorization service; three-layer enforcement (§11.2) |
| Unintended write path | No generic CRUD; save-option protocol; guards; contract tests for absence of mutation paths |
| Provider/credential exposure | C20-INV-03; no HTTP/credential/SDK in C25; forbidden fields |
| Score/rank drift in language | Natural-language equivalents forbidden; claim-anchored phrasing; validation guard |
| Retention/deletion misstep | deleteId soft-delete; audit; eligibility ≠ deletion; legal-hold gate; proposed defaults only |
| Supersession flag creep | isCurrent/isLatest forbidden; derived read-time semantics |

---

## 33. Entry and Exit Gates

| WP | Entry gate | Exit gate |
|---|---|---|
| WP2.0 | C20 docs accessible; WP2 charter + Plan ratified | Three C20 dependencies ratified; go/no-go signed |
| WP2.1A | WP2.0 exit; Foundation Review scheduled | **Audit-storage ADR ratified; entity/artifact budget reconciled; persistence mechanism approved; retention/deletion rules approved; exact audit code allowlist approved + assigned** |
| WP2.1B | **WP2.1A ADR ratified** | Contract tests green; provenance schema validated |
| WP2.2 | WP2.0 C20 dependency ratified; **WP2.1A ADR ratified**; WP2.1B exit; audit write path per ADR available | Generation boundary + failure matrix green; idempotency (incl. regeneration) verified; no-partial proven |
| WP2.3 | WP2.1B exit; WP2.2 exit; audit ADR ratified; legal/audit hold resolved (before deletion) | Review/disposition matrix green; audit append-only proven; OQ-F defaults ratified |
| WP2.4 | Read surfaces exist (WP2.1B/WP2.2/WP2.3 exits) | D2 + masking runtime evidence green |
| WP2.5 | All prior exits; C20 dependency ratified | Freeze review signed; freeze criteria met (§34) |

Recommended order: **WP2.0 → WP2.1A → WP2.1B → WP2.2 → WP2.3 → WP2.4 → WP2.5.**

---

## 34. Freeze Criteria

1. D3, D4, D5, D7 dispositioned and demonstrated.
2. Section 10 dependency resolution signed (C20 CompletionCapability ratified; route-binding surface confirmed; C20-INV-05…11 verified ACTIVE).
3. All §29 boundary tests green, including the ACCEPTED zero-side-effect proof and the regeneration idempotency rules.
4. Entity budget honored — exactly one persistent C25 artifact (CommercialBrief); audit/feedback remain non-entity or ADR-amended mechanisms.
5. Invariant compliance signed — ADV-001, HG-001, PROV-001, INT-006 (owning); OWN-001, SEC-001 (constraining).
6. WP2 Foundation Review signed; independent C20–C25 boundary verification signed.
7. Masking / audit ratification gates resolved before any freeze.
8. **OQ-F proposed defaults (90-day retention, dedupe window) ratified by the WP2.3 Foundation Review; legal/audit hold representation resolved; `brief.unarchive` confirmed absent.**

---

## 35. Open Items and External Dependencies

| Item | Owner | Status |
|---|---|---|
| CompletionCapability value for brief generation (final name/granularity/placement; proposed `COMMERCIAL_BRIEF`) | C20 governance | **UNRESOLVED** — external prerequisite; WP2.0 |
| Provider binding / allowed-provider-binding surface + brief purpose registration | C20 governance | **UNRESOLVED** — external prerequisite; WP2.0 |
| C20-INV-05…11 activation + verification | C20 governance | **UNRESOLVED** (all DEFERRED today); WP2.0 |
| Review audit storage design ratification (first-class-entity judgment; persistence mechanism; audit code allowlist + assignment) | C25 ADR amendment | **WP2.1A** — docs/governance only; not authorized by this Plan |
| Archive retention period (proposed 90 days) + dedupe window value (proposed 24 h) | WP2.3 Foundation Review / D5 | **PROPOSED DEFAULTS ONLY** — not ratified; configurable only after ratification |
| Legal / audit hold representation | WP2.3 Foundation Review / D5 | **UNRESOLVED** — no field added; deletion implementation forbidden until resolved |
| `brief.unarchive` restoration | Future C25 Charter Amendment + ADR + Plan Amendment | **EXCLUDED from this Plan** |
| Numeric evidence threshold | None — resolved to "no numeric threshold; quality is warning-only" | Resolved (§9.2) |
| Final Implementation Plan Ratification Review | Completed 2026-08-02 | **RATIFIED WITH NON-BLOCKING NOTES** — implementation planning reference only |

---

## 36. Implementation Authorization Boundary

- **This document is an implementation-planning document only.** Authoring and amending it authorizes no code, no entity, no metadata, no scope, no ACL, no controller, no route, no migration, no test, no C20 change, no ProviderRoute, no scheduler/worker/webhook/queue, no AI invocation, no commit, no push, and no tag.
- **Plan status: RATIFIED — implementation planning reference only; code implementation not authorized.** Final Implementation Plan Ratification Review completed.
- Each work package (WP2.0, WP2.1A, WP2.1B, WP2.2–WP2.5) requires **separate authorization before implementation**.
- **WP2.0 Dependency Resolution is COMPLETE.** Generation implementation remains NO GO because C20 dependencies remain externally open.
- WP2.0 must complete and be ratified **before any generation implementation** is permitted.
- Charter ratification does **not** constitute C20 dependency ratification; the C20 dependencies remain externally open (§35). **The C20 governance/change package is not authorized by this Plan or this amendment.**
- The audit store additionally requires the WP2.1A ADR amendment before implementation; deletion additionally requires legal/audit hold resolution.
- No commit, push, or tag may occur unless later separately authorized.
- **`code implementation` = NO** (re-confirmed in §12.6 verification).

### Administrative Authorization Matrix

| Item | Status |
|------|--------|
| WP2 Charter | RATIFIED |
| WP2 Implementation Plan | RATIFIED |
| WP2.0 Dependency Resolution | COMPLETE |
| WP2.1A Audit Storage ADR | RATIFIED |
| WP2.1B | NOT AUTHORIZED |
| WP2.2 Generation | NO GO (External C20 Dependencies) |
| WP2.3 | NOT AUTHORIZED |
| Any Code | NOT AUTHORIZED |

---

## 37. References

1. `docs/PHASE3C25_WP2_IMPLEMENTATION_CHARTER.md`
2. `docs/PHASE3C25_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C25_IMPLEMENTATION_FOUNDATION_PLAN.md`
4. `docs/PHASE3C25_CHARTER_DRAFT.md`
5. `docs/PHASE3C25_WP1_IMPLEMENTATION_PLAN.md`
6. `docs/audit/PHASE3C25_WP1_FINAL_FREEZE_REVIEW.md`
7. `docs/audit/ADR-C25-001` … `ADR-C25-006`
8. `docs/adr/C25_INVARIANT_REGISTRY.md`
9. `docs/adr/ADR-C20_AI_PLATFORM_ARCHITECTURE.md`
10. `docs/adr/C20_INVARIANT_REGISTRY.md`
11. `docs/PHASE3C20_WP2_CAPABILITY_REGISTRY_FREEZE.md`
12. `docs/PHASE3C20_COMPLETION_PROVIDER_CAPABILITY_SCOPE.md`
13. `docs/PHASE3C20_WP2_CHARTER.md`, `docs/PHASE3C20_WP2_2_B_COMPLETION_IMPLEMENTATION_PLAN.md`, `docs/PHASE3C20_WP3_AI_EXECUTION_CHARTER.md`, `docs/PHASE3C20_WP3_DETAILED_DESIGN_DECISIONS.md`
14. `docs/PHASE3C24_WP2_IMPLEMENTATION_CHARTER.md`
15. `docs/adr/C24_INVARIANT_REGISTRY.md`
16. `docs/PHASE3C24_WP2_OPPORTUNITY_GOVERNANCE_CHARTER.md`, `docs/PHASE3C24_WP3_IMPLEMENTATION_CHARTER.md`, `docs/PHASE3C24_WP3_REVENUE_INSIGHT_CHARTER.md`, `docs/PHASE3C24_WP1_REPLY_INTELLIGENCE_CHARTER.md`
17. `docs/audit/ADR-C24-006` … `ADR-C24-015`
18. `docs/adr/C22_INVARIANT_REGISTRY.md`, `docs/adr/C23_INVARIANT_REGISTRY.md`
19. `docs/audit/ADR-C22-005_RETRY_FAILURE_CLASSIFICATION.md`, `docs/audit/ADR-C22-005_RATE_LIMIT_RETRY_GOVERNANCE_ADDENDUM.md`, `docs/audit/ADR-C22-006_CRM_LIFECYCLE_BOUNDARY.md`, `docs/audit/ADR-C22-007_ACTIONGATE_REENTRY_RULES.md`
20. **Live implementation precedent (primary basis):** `crm-extension/files/custom/Espo/Modules/Prospecting/` (Entities, Services, Hooks, `Resources/routes.json`, `Resources/metadata/{scopes,entityDefs,aclDefs,app}/`), `crm-extension/files/custom/Espo/Modules/AIPlatform/` (entityDefs, Services, Hooks, Entities), `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/` (routes, Api, Services, metadata)
21. Historical reference only: `archive/runtime-backups/c11_1_baseline-20260714T094409Z/` (predates C20)
22. `docs/deployment/UPGRADE.md` (Espo rebuild schema convention); `crm-extension/tests/test_extension_skeleton.py` (no-migration-artifacts enforcement)

## 38. Administrative Ratification Record

Final Implementation Plan Ratification Review completed.

| Item | Result |
| --- | --- |
| Review Type | Final Implementation Plan Ratification Review |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| Date | 2026-08-02 |
| Implementation Scope | PASS |
| REST/API Decision | PASS |
| ACL / Authorization Model | PASS |
| Audit Storage Dependency | PASS |
| Lifecycle Model | PASS |
| Generation Boundary | PASS |
| C20 Dependency Boundary | PASS |
| Implementation Sequencing | PASS |
| Remaining Governance Blockers | None |
| Implementation Planning | RATIFIED |
| WP2.1B | NOT AUTHORIZED |
| WP2.2 | NO GO (External C20 Dependencies) |
| WP2.3 | NOT AUTHORIZED |
| Any Code | NOT AUTHORIZED |
