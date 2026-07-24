# ADR-C17: Prospecting Operational Centers Navigation

## Status

**Accepted**

The independent WP0 exit audit reported no remaining blockers, classified the
implementation risk as LOW, and granted `READY_FOR_C17_IMPLEMENTATION`. The authorized
WP1.2–WP1.4 implementation task accepts this amended ADR together with its
version-controlled desired-state artifact, single materializer, focused contracts, and
development-runtime evidence.

**Amendment record:** WP1.2A review findings A–J remain incorporated. The 2026-07-23
acceptance amendment additionally aligns the Research Center with the authorized frozen
classification (`Lead` as the global native operational record source;
`ResearchEvidence` as a supporting object), converges navigation governance, and
authorizes WP1 implementation.

## Date

2026-07-23 (authored WP1.2; amended WP1.2A; accepted for WP1 implementation)

## Decision Owners

- Principal Software Architect, EspoCRM Prospecting module.
- Phase3C17 Release Approval Board / implementation authorization.
- Independent WP0 exit audit and WP1.2A architecture review.

## Amends

`docs/architecture/ADR_C16_NAVIGATION_INFORMATION_ARCHITECTURE.md`

## Relationship

Evolves and partially supersedes selected navigation-composition decisions of ADR-C16.
ADR-C16 is **not** deprecated and is **not** modified by this task.

---

## Context

Phase3C16.3B froze an entity-first navigation model (ADR-C16, `Status: Accepted —
Design Freeze`, `docs/architecture/ADR_C16_NAVIGATION_INFORMATION_ARCHITECTURE.md:3`)
in which every workflow entity appears as a top-level tab under one `Prospecting`
divider, grouped into three zones (Acquisition / Sales / Outreach).

Phase3C17 has since delivered workflow-hardening work packages on top of the frozen
release `v1.9.7-alpha` (tag at commit `d0b9a8077abff804c5f0d231707e83ab3a71d263`):

- WP0.2 — Quote Mark Accepted workflow action (`docs/PHASE3C17_WP0_2_ACCEPTED_IMPLEMENTATION.md`, status IMPLEMENTED).
- WP0.3 — Quote record controller for API creation (`docs/PHASE3C17_WP0_3_QUOTE_CONTROLLER_IMPLEMENTATION.md`, status IMPLEMENTED).
- WP0.4 — Shared workflow authorizer (`docs/PHASE3C17_WP0_4_AUTHORIZER_IMPLEMENTATION.md`).

The expected WP1 Navigation IA Audit input (`docs/PHASE3C17_WP1_NAVIGATION_IA_AUDIT.md`)
does not exist in the repository. The accepted ADR and the WP1 implementation report
close that evidence gap from repository evidence, the frozen classifications supplied
by the authorized implementation brief, focused contracts, and real development-runtime
validation. The missing historical filename is retained as a baseline observation, not
as an implementation blocker.

## Problem

1. **Entity-first top-level navigation no longer matches the operational workflow.**
   The C16 canonical hierarchy (`docs/architecture/ADR_C16_NAVIGATION_INFORMATION_ARCHITECTURE.md:64-85`)
   places twelve tabs under one divider. U01 already identified the resulting gaps:
   no entry point and no workflow grouping (`docs/PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md:178-186`).
   Users need workflow-oriented operational surfaces, not a flat entity inventory.
2. **The navigation authority chain is ambiguous.** Three artifacts touch navigation:
   scope metadata (`tab:true/false`), the U04 provisioning script
   (`deployment/provisioning/phase3u04_provision_navbar_tab_order.php:67-68`, the
   repository's only `config.tabList` writer), and runtime `config.tabList` itself.
   Their roles were never formally separated, and the U04-materialized runtime state
   (verified 2026-07-14: only `ProspectingSearch`, `SearchJob`, `ProspectPool`,
   `ResearchEvidence` under the divider — `docs/PHASE_U04_NAVIGATION_POLISH_REPORT.md:45-56`)
   predates the C16 entities, so C16's desired state and the effective runtime state
   already diverge.
3. **C17 needs a frozen, implementation-directive visibility classification** for every
   Prospecting entity and surface so that WP1.3 can implement navigation without
   reopening placement decisions.

## Decision

Adopt **workflow-oriented Operational Centers** as the Phase3C17 navigation model
(Alternative B — Hybrid Operational Centers; see [Alternatives Considered](#alternatives-considered)):

1. Top-level Prospecting navigation is reserved for approved **Center entry surfaces**
   (Dashboard, Search Center, Research Center, Outreach Center, Quote Center) plus
   explicitly justified global native CRM scopes (`Lead`).
2. Selected entity lists remain directly available **within** Centers as operational
   queues (Class B) wherever bulk work, queue processing, exception handling, auditing,
   or troubleshooting requires direct list access.
3. Entities, relationships, workflow lifecycles, ACL, and record security keep their
   existing owners. Centers are navigation and workspace composition only.
4. Navigation governance is formalized as a layered chain with exactly one authority
   per layer (see [Runtime Navigation Governance](#runtime-navigation-governance)):
   **Accepted ADR → canonical declarative desired-state artifact → one controlled
   idempotent provisioning materializer → runtime `config.tabList` → drift validation**.
5. The per-entity visibility classes in
   [Entity Visibility Classification](#entity-visibility-classification) are **frozen**:
   WP1.3 chooses only the native physical composition; it must not reopen a frozen
   class without a new ADR amendment.

## Relationship to ADR-C16

**Chosen relationship: C — Evolve with Partial Supersession.**

Independent verification (the expected WP1 audit is absent) confirms:

- C16's foundation remains valid and binding: EspoCRM-native navigation mechanisms,
  entity ownership, service-owned workflows, ACL authority, no SPA shell, bottom-panel
  access for child/event objects, and retained bulk lists (evidence:
  `docs/architecture/ADR_C16_NAVIGATION_INFORMATION_ARCHITECTURE.md:24-58`; services
  verified at `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteTransitionService.php:15`,
  `ApprovalService.php:18`, `ApprovalDecisionService.php:22`,
  `WorkflowAuthorizationService.php:21`).
- Selected C16 navigation-**composition** decisions no longer fit Phase3C17 and are
  partially superseded: pure entity-first top-level composition, the three-zone tab
  block as the organizational ceiling, and Dashboard as a supporting-only entry point.
- The repository itself already moved in this direction: U04 renamed the
  `ResearchEvidence` navigation label to **"Research Center"**
  (`crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json:8`)
  and reduced runtime tabs to workflow-relevant entries — runtime evidence that a
  Center-style composition is the established trajectory.

ADR-C16 remains an Accepted ADR. Only the clauses listed below are partially
superseded; all other C16 clauses remain authoritative. ADR-C16 is not edited in this
task; annotation of the affected C16 clauses happens only after formal acceptance of
this ADR, through a separately authorized task (Migration Plan, Phase 6).

**Traceability note (frozen):** all ADR-C16 line references in this ADR are anchored
to the Phase3C16.3B frozen version at tag `v1.9.7-alpha` / commit
`d0b9a8077abff804c5f0d231707e83ab3a71d263`. Line references must be revalidated if
ADR-C16 is later annotated or amended.

### C16 Decision Table

| C16 Decision | C17 Treatment | Status | Reason |
|---|---|---|---|
| EspoCRM-native navigation mechanisms (Principle 1, `:26-34`) | Preserve | PRESERVED | Centers are composed from native tabs, dividers, custom non-entity pages, entity lists, dashboards, and dashlets. U04 verified the native `tabList` supports scope + divider entries only (`docs/PHASE_U04_NAVIGATION_POLISH_REPORT.md:9-24`). |
| Entity ownership remains with entities | Preserve | PRESERVED | Centers compose; they never persist entity data. |
| Workflow ownership remains with services | Preserve | PRESERVED | Verified canonical services: `QuoteTransitionService` (sole writer of `Quote.status`, `QuoteTransitionService.php:15`), `ApprovalService` (only writer of Approval business state, `ApprovalService.php:14-18`), `ApprovalDecisionService.php:22`, `WorkflowAuthorizationService.php:21`. |
| ACL and record security remain authoritative | Preserve | PRESERVED | Native ACL filters tab visibility (`ADR_C16...:108-124`); navigation changes grant no permissions (U04 access-control verification, `PHASE_U04...:58-69`). |
| No independent SPA navigation shell | Preserve | PRESERVED | No custom navigation framework; the two existing custom pages are client controllers inside EspoCRM's own routing (`crm-extension/files/client/custom/src/controllers/prospecting-search.js:1-7`, `prospecting-dashboard.js:1-7`). |
| Entity-first top-level navigation (Principle 1 composition, `:26-34`; §2.1 hierarchy `:64-85`) | Change | PARTIALLY SUPERSEDED | Top level becomes Center entry surfaces; entity tabs move inside Centers as queues/secondary destinations. See below. |
| Acquisition / Sales / Outreach section model (`:36-46`) | Change | PARTIALLY SUPERSEDED | Zones evolve into five Centers; see below. |
| Dashboard is only a supporting entry point (Principle 3, `:48-50`; N-IA-3 `:444`) | Change | PARTIALLY SUPERSEDED | Dashboard becomes a Primary Center Entry and the Prospecting landing surface; see below. |
| Child and event objects use related access (§5, `:286-339`) | Preserve | PRESERVED | `QuoteItem`, `EmailEvent`, `SalesFeedback`, `LearningSignal` remain non-tab objects reached via panels/links. |
| Bulk operational lists remain available (§3.4 `:228-235`; §5.4 `:326-339`) | Preserve | PRESERVED | Dual-access rationale is carried into Class B queues. |

## Preserved C16 Decisions

The following C16 decisions remain fully authoritative and binding on WP1.3 and later:

1. **EspoCRM-native navigation only** — scope tabs, dividers, native custom pages,
   dashboards, dashlets, list views, relationship panels; no React tree, no SPA shell,
   no custom left-nav rendering (`ADR_C16...:26-34`; U01 Option A, `PHASE3U01...:284-297,329-338`).
2. **Entity ownership** — entities remain the data ownership model and the
   relationship ownership model.
3. **Workflow ownership** — entities and their canonical services remain the workflow
   and lifecycle ownership model: `Quote.status` is written only by
   `Espo\Modules\Prospecting\Services\QuoteTransitionService` (`QuoteTransitionService.php:15`,
   transition matrix `:25-33`); Approval business state only by
   `Espo\Modules\Prospecting\Services\ApprovalService` (`ApprovalService.php:14-18`);
   decision coordination only by
   `Espo\Modules\Prospecting\Services\ApprovalDecisionService` (`ApprovalDecisionService.php:13-22`);
   UI commands route through
   `Espo\Modules\Prospecting\Services\QuoteWorkflowActionService` (`QuoteWorkflowActionService.php:13-22`)
   under `Espo\Modules\Prospecting\Services\WorkflowAuthorizationService` (`WorkflowAuthorizationService.php:14-29`).
4. **ACL and record-level security remain authoritative** — navigation never elevates
   permissions; tabs are filtered natively by scope ACL (`ADR_C16...:108-124`).
5. **No independent navigation SPA or global navigation framework.**
6. **Child/event objects stay on related access** — `QuoteItem` (Quote bottom panel),
   `EmailEvent`, `SalesFeedback`, `LearningSignal` (`tab:false` scopes,
   `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/{QuoteItem,EmailEvent,SalesFeedback,LearningSignal}.json`).
7. **Bulk operational lists remain available** — queue-style direct lists are retained
   inside Centers (Class B).
8. **No `afterInstall` `tabList` mutation** — C16 §6 (`ADR_C16...:343-384`) remains
   binding; verified: `crm-extension/manifest.json` declares no install hooks and no
   file under `crm-extension/` touches `tabList`.
9. **Single canonical metadata source tree** — `crm-extension/files/` is the
   installable source (`crm-extension/README.md:14-32`); the former duplicate
   `custom/Espo/Custom` metadata overlay was removed 2026-07-11
   (`docs/architecture/EXTENSION_SINGLE_SOURCE_MIGRATION_REPORT.md`).

## Partially Superseded C16 Decisions

### PS-1 — Entity-first top-level composition → Center-entry top level

- **Precise C16 statement affected:** Principle 1 "Native Entity-First"
  (`ADR_C16...:26-34`) in its composition aspect, and the §2.1 Canonical Tab Hierarchy
  (`:64-85`) placing twelve entity tabs under the divider.
- **Why it no longer fits Phase3C17:** the workflow surface now spans acquisition,
  research, outreach, and commercial execution; twelve peer tabs have no workflow
  narrative (U01 Gap 1/Gap 2, `PHASE3U01...:178-186`). C17 WP0.x hardened the workflow
  services; navigation must expose workflows, not tables.
- **What replaces it:** Operational Center entry surfaces at top level; entity lists
  continue inside Centers as Class B queues or Class C destinations.
- **What remains unchanged:** the *native* half of Principle 1 — all composition uses
  EspoCRM-native mechanisms; entity CRUD, lists, details, ACL are untouched.
- **Migration impact:** `config.tabList` is re-materialized to Center entries
  (Migration Plan, Phases 2-3); no metadata or entity changes are required for the
  entities that stay Class B/C — they remain directly addressable.
- **Rollback impact:** the captured pre-materialization runtime `config.tabList` is
  restored (see [Runtime Effective Navigation](#runtime-effective-navigation));
  re-running the previous (U04) provisioning script is only a fallback baseline
  reconstruction. No data or metadata rollback is involved.

### PS-2 — Three-zone section model → five Operational Centers

- **Precise C16 statement affected:** Principle 2 Three-Zone Navigation
  (`ADR_C16...:36-46`) and the zone table.
- **Why it no longer fits:** the zones were label groupings of entity tabs, not
  workflow surfaces. Acquisition mixed search execution with research evidence;
  Sales mixed quote drafting, commercial approval, and financial execution without a
  composed entry.
- **What replaces it:** Search Center (plan → execute → curate), Research Center
  (Lead-centric research with evidence and feedback), Outreach Center (draft approval →
  send → replies), Quote Center (quote → approval → proforma invoice), plus Dashboard
  as the cross-center landing surface.
- **What remains unchanged:** the same entities, the same single `Prospecting`
  divider, the same zone ordering logic (discover → research → communicate → close).
- **Migration impact:** navigation labels and tab-list membership only; U04 already
  shipped the precedent of the `ResearchEvidence` list carrying the "Research Center"
  navigation label (`i18n/en_US/Global.json:8`).
- **Rollback impact:** same as PS-1 — captured-state restoration, no data impact.

### PS-3 — Dashboard as supporting-only entry → Dashboard as Primary Center Entry

- **Precise C16 statement affected:** Principle 3 (`ADR_C16...:48-50`) and N-IA-3
  (`:444`) keeping `ProspectingDashboard` hidden from the global tab list.
- **Why it no longer fits:** a workflow-oriented model needs a landing/routing surface;
  the asset already exists as a working custom page ("Prospecting Operations",
  `clientDefs/ProspectingDashboard.json:2`; view `views/prospecting/dashboard.js`).
  U04 hid it solely to reduce flat-tab clutter (`PHASE_U04...:28-36`) — the problem the
  Center model solves structurally.
- **What replaces it:** Dashboard is a Class A Primary Center Entry and the default
  Prospecting landing surface, aggregating and routing into the other Centers.
- **What remains unchanged:** Dashboard owns no data and no workflow; C16 §3.1's
  deployability rationale (templates/provisioning over per-user pages) still governs
  how dashboard layouts are delivered.
- **Migration impact:** the C17 desired navigation state re-includes
  `ProspectingDashboard`; U04's hiding rule for it is retired with that script's
  supersession.
- **Rollback impact:** restoring the captured pre-materialization state hides it
  again; no other effect.

## Navigation Philosophy

**Before:** Entity-first navigation — users primarily navigate through entity list tabs.

**After:** Workflow-oriented Operational Centers — users enter through workflow-oriented
operational surfaces. Selected entity lists remain available within Centers when bulk
processing, queue work, exception handling, auditing, investigation, or troubleshooting
requires direct list access.

**Frozen boundaries:**

```text
Entities remain the data ownership model.
Entities remain the relationship ownership model.
Entities and their canonical services remain the workflow and lifecycle ownership model.
Centers are navigation and workspace composition.
Centers do not become new data owners.
Centers do not become new workflow owners.
Centers do not replace ACL or record security.
```

**Also frozen:**

```text
Center-internal
≠ deleted
≠ ACL denied
≠ unavailable by direct URL
≠ unavailable through relationships
≠ unavailable through filtered lists
≠ unavailable through global search when the scope supports it
≠ automatically related-only
```

An entity omitted from top-level navigation loses nothing but its top-level tab slot.

## Conceptual and Physical Navigation Models

### Conceptual Product IA (frozen)

```text
Prospecting

├── Dashboard
├── Search Center
├── Research Center
├── Outreach Center
├── Quote Center
└── Analytics            (initially a Dashboard section — see Analytics)
```

### Physical EspoCRM Navigation (implementation freedom within native mechanisms)

EspoCRM may implement the conceptual model through combinations of: scope tabs,
navigation dividers, custom non-entity pages, entity list views, filtered list views,
dashboards, dashlets, relationship panels, bottom panels, record links, drill-down
links, native global search, and role-visible navigation entries.

**Verified constraint:** the local runtime (EspoCRM `10.0.1`) natively supports scope
entries and divider entries in `config.tabList`; it does **not** support an arbitrary
nested left-navigation tree without custom client code
(`docs/PHASE_U04_NAVIGATION_POLISH_REPORT.md:9-24` — VERIFIED RUNTIME, 2026-07-14).
This ADR therefore does **not** assume nested menus. The expected physical composition
is the proven U04 pattern: one `Prospecting` divider with Center entry surfaces
directly beneath it — a pattern already demonstrated by the `ResearchEvidence` native
list shipping as a navigation entry under the "Research Center" label. WP1.3 chooses
the safest native physical composition consistent with this ADR; the conceptual
ownership and visibility model is what is frozen.

**Center composition rule (frozen):** a Center may be physically composed from one
primary native list plus governed links to secondary queues. **A dedicated custom
composition page is not required for every Center.** Custom pages are used only where
they already exist (`ProspectingDashboard`, `ProspectingSearch`); no new custom Center
page is created in Phase3C17.

## Operational Centers

A Center owns **navigation composition** for a workflow area. A Center must not become
the owner of entity persistence, entity lifecycle, ACL, or record security.

### Dashboard

- **Purpose:** cross-center landing surface; aggregates operational data and routes
  users into Centers.
- **Primary users:** all Prospecting roles (Admin, Sales Manager, Sales User; Finance
  read-oriented views).
- **Primary entry surface:** `ProspectingDashboard` custom page ("Prospecting
  Operations", `clientDefs/ProspectingDashboard.json:2`; controller
  `crm-extension/files/client/custom/src/controllers/prospecting-dashboard.js:1-7`;
  view `views/prospecting/dashboard.js`).
- **Owned workflow area:** none (composition only).
- **Entry entities:** none. **Supporting entities:** all, read-only, via the 14
  existing dashlets (`Resources/metadata/dashlets/`, e.g. `AcquisitionOverview`,
  `ProspectingSummary`, `ProspectingIntelligence`).
- **Required direct queues:** none on the Dashboard itself; it links to Center queues.
- **Permitted navigation actions:** view aggregates; navigate into Centers, entity
  lists, and records.
- **Prohibited mutation paths:** Dashboard must not mutate any entity or workflow
  state; it is not a data owner or workflow owner.
- **Fallback access paths:** EspoCRM dashboard picker (C16 §4.1 `:240-253`); direct URL.
- **Role/ACL considerations:** scope is `acl:false` (non-entity; `scopes/ProspectingDashboard.json:2-7`);
  every dashlet enforces its own `aclScope` natively.
- **Decision (frozen):** Dashboard is **both** the main Prospecting landing page and a
  supporting overview alongside Center entries. `ProspectingDashboard` **is** a Primary
  Center Entry (Class A) and **is** permitted as a top-level Prospecting surface. This
  partially supersedes C16 N-IA-3 (PS-3).

### Search Center

- **Purpose:** plan search → execute search → inspect results → curate prospects.
- **Primary users:** Sales Manager, Sales User, Admin.
- **Primary entry surface:** `ProspectingSearch` custom page (global search +
  quick-create entry; `clientDefs/ProspectingSearch.json:2`; controller
  `controllers/prospecting-search.js:1-7`; view `views/prospecting/search.js`).
  **Frozen:** `ProspectingSearch` is the Search Center composition surface and Primary
  Center Entry (Class A).
- **Owned workflow area:** acquisition search and prospect curation (navigation
  composition only).
- **Entry entities:** `ProspectingSearch` (non-entity surface). **Supporting
  entities:** `SearchStrategy`, `SearchJob`, `ProspectPool`.
- **Required direct queues (frozen):**
  - `SearchJob` — direct execution and exception queue: **yes** (Class B); five status
    filters already exist (`PHASE3U01...:492-500`).
  - `ProspectPool` — direct bulk-working list: **yes** (Class B); four queue filters
    already exist (`PHASE3U01...:560-567`).
- **Secondary destination (frozen):** `SearchStrategy` (Class C) — planning/management
  list reachable from the Search Center; not a queue.
- **Ceases to be global top-level tabs (frozen):** `SearchStrategy`, `SearchJob`,
  `ProspectPool` as standalone top-level tabs. `ProspectingSearch` remains top-level as
  the Center entry.
- **Access paths that must remain after top-level cleanup (frozen):** direct URLs;
  native global search; `SearchStrategy` detail → generated jobs; `SearchJob` detail →
  `prospectPools` panel; `ProspectPool` detail → pushed Lead link; Dashboard drill-down.
- **Permitted navigation actions:** search, quick-create, open lists/records, standard
  record actions per ACL.
- **Prohibited mutation paths:** no Center-level status writes; queue moves remain
  standard record edits under entity ACL (per existing U01/U02-era actions); no
  bypass of service guards.
- **Role/ACL considerations:** entity tabs are ACL-filtered natively; Integration Bot
  has API access without navigation provisioning (`PHASE3U01...:385-404`).

### Research Center

- **Purpose:** Lead-centric research work — review Leads, inspect evidence, and capture
  feedback without creating a second research record owner.
- **Primary users:** Sales Manager, Sales User (ACL-scoped records), Admin.
- **Primary operational record source:** the native global `Lead` scope. `Lead`
  remains a **Global Native CRM Scope (Class E)** and is not renamed internally,
  duplicated in `config.tabList`, or owned by Prospecting.
- **Physical composition (frozen):** when a native global `Lead` tab already exists,
  the C17 materializer preserves it in place and does not insert a duplicate beneath
  the Prospecting divider. The Prospecting Dashboard and Search Center provide a
  clearly labeled **Research Center** link to the native Lead list. This is the
  authorized fallback for EspoCRM's flat tab model.
- **Supporting objects:** `ResearchEvidence`, `SalesFeedback`, `LearningSignal`, and
  `EmailEvent` remain accessible through existing Lead relationship panels, ACL-safe
  direct links, filtered lists, and Dashboard navigation. `ResearchEvidence` is not
  labeled as the Research Center and is not a global Prospecting top-level entry.
- **Existing native capability:** Lead retains 26 Prospecting filters
  (`clientDefs/Lead.json`) and bottom panels for research evidence, sales feedback,
  learning signals, and email events.
- **Prohibited changes:** no new Research entity, no duplicate persistence, no Lead
  ownership transfer, no scoring or AI-research logic changes, and no ACL changes.

### Outreach Center

- **Purpose:** review outbound content → approve or reject → inspect send execution →
  handle replies and delivery outcomes.
- **Primary users:** Sales Manager, Sales User, Admin.
- **Primary entry surface (frozen):** **the `DraftApproval` native list is the
  Phase3C17 Outreach Center primary entry** (Class A, top-level allowed). Outreach
  composition does **not** require a new custom page in C17.
- **Physical composition (frozen):** the Center is physically composed through:
  - `DraftApproval` as the Class A entry;
  - fixed navigation links or Center entry actions to `SendExecution` and `ReplyEvent`;
  - filtered Class B queues;
  - related access to `EmailEvent`;
  - record-level drill-down;
  - Dashboard routing where useful.

  Per the frozen Center composition rule: a Center may be physically composed from one
  primary native list plus governed links to secondary queues; a dedicated custom
  composition page is not required for every Center. No new workflow ownership is
  introduced by this composition.
- **Owned workflow area:** outreach content approval and delivery monitoring
  (navigation composition only).
- **Entry entities:** `DraftApproval`. **Supporting entities:** `SendExecution`,
  `ReplyEvent`, `EmailEvent`.
- **Required direct queues (frozen):**
  - `SendExecution` — direct filtered list for execution monitoring and failure
    handling (Class B, execution-support object).
  - `ReplyEvent` — direct filtered list for reply triage and tracking (Class B).
- **Historical/supporting objects (frozen):** `EmailEvent` — Class D, append-only
  delivery event log (`scopes/EmailEvent.json` `tab:false`; Lead bottom panel
  `entityDefs/Lead.json:407`); not relationship-*only* — it remains directly
  addressable by URL for audit/troubleshooting by ACL-permitted roles.
- **Terminology boundary (frozen):**

  ```text
  DraftApproval = approval of outbound prospecting content
  Approval      = commercial approval of a Quote or related commercial document
  ```

  These are distinct business concepts. Navigation labels must keep them unambiguous:
  the Outreach Center queue is labeled around "Draft Approvals" (current labels:
  `i18n/en_US/DraftApproval.json:15` "Draft Approvals", `zh_CN` 草稿审批) and the Quote
  Center queue around "Approvals" (`i18n/en_US/Global.json:12,24`). WP1.3 must not
  introduce a label that presents either one as the other.
- **Fallback access paths:** Lead detail bottom panels (`draftApprovals`,
  `sendExecutions`, `replyEvents`); direct URLs; global search.
- **Prohibited mutation paths:** no approval-state writes outside the existing
  outreach services; no Center-level mass approval bypassing record ACL.

### Quote Center

- **Purpose:** compose the commercial workflow — quote drafting and lifecycle,
  commercial approval, proforma-invoice execution.
- **Primary users:** Sales Manager, Sales User, Finance, Admin.
- **Primary entry surface (frozen):** the `Quote` list — Quote Center entry (Class A,
  top-level).
- **Owned workflow area:** commercial document navigation composition only. **Quote
  remains the primary commercial aggregate; Quote Center composes existing commercial
  capabilities and is not a new data owner.**
- **Entry entities:** `Quote`. **Supporting entities:** `Approval`, `ProformaInvoice`,
  `QuoteItem`.
- **Required direct queues (frozen):**
  - `Approval` — commercial approval queue (Class B) for managers/Finance; also Quote
    and PI bottom panels (C16 dual-access `:326-339`).
  - `ProformaInvoice` — PI lifecycle queue (Class B) for Finance; also Quote bottom
    panel. **Placement decided explicitly: PI lives inside Quote Center; this ADR does
    not redesign the PI system.**
- **Supporting object (frozen):** `QuoteItem` — Class D; owned by Quote; accessed via
  the Quote detail bottom panel only; **not** a top-level workflow destination
  (`scopes/QuoteItem.json` `tab:false`; `ADR_C16...:146`).
- **Workflow ownership (frozen, verified class names):**

  ```text
  Quote status remains owned by
      Espo\Modules\Prospecting\Services\QuoteTransitionService
      (crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteTransitionService.php:15)
  Approval status remains owned by
      Espo\Modules\Prospecting\Services\ApprovalService
      (crm-extension/files/custom/Espo/Modules/Prospecting/Services/ApprovalService.php:18)
  Approval↔Quote decision coordination remains owned by
      Espo\Modules\Prospecting\Services\ApprovalDecisionService
      (crm-extension/files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php:22)
  UI workflow commands route through
      Espo\Modules\Prospecting\Services\QuoteWorkflowActionService
      under Espo\Modules\Prospecting\Services\WorkflowAuthorizationService
      (crm-extension/files/custom/Espo/Modules/Prospecting/Services/WorkflowAuthorizationService.php:21)
  ```

- **Prohibited mutation paths (frozen):** no direct client-side status writes; no
  inline status editing; no mass status editing; no drag-and-drop status transitions;
  no generic CRUD status mutation; no navigation action that bypasses
  `WorkflowAuthorizationService`; no Center code that duplicates workflow ownership.
  **Any Kanban or board representation must remain read-only** unless a future accepted
  ADR explicitly authorizes service-backed transitions.
- **Fallback access paths:** Quote/PI detail bottom panels (`quoteItems`, `approvals`,
  `proformaInvoices`); direct URLs; global search.
- **Role/ACL considerations:** per C16 role matrix (`ADR_C16...:108-124`) — Finance
  sees `ProformaInvoice` and `Approval`, not pipeline scopes.

### Analytics

- **Purpose:** read-only aggregation, operational visibility, and trends.
- **Decision (frozen, exactly one):** **Option 2 — Analytics is initially a Dashboard
  section.** It is not an immediate separate C17 Center, and it is not deferred as an
  undefined future Center: its initial form is a composed Dashboard section using
  existing assets.
- **Repository evidence:** 14 dashlet definitions already ship
  (`Resources/metadata/dashlets/` — `Acquisition*`, `ProspectingSummary`,
  `ProspectingIntelligence`, `RecentResearchEvidence`, `RecentSalesFeedback`,
  `ProspectingRecentDiscovery`); **no** reports, analytics entities, or dashboard
  templates are shipped by the extension (verified absence), and no metrics persistence
  exists. The existing dashlet inventory already covers operational visibility without
  any new data contract.
- **Implementation-risk analysis:** a separate Analytics Center in C17 would require a
  new composition surface with no new data — pure scope-expansion risk (custom JS,
  upgrade fragility) — while a Dashboard section reuses proven, ACL-enforcing dashlets
  at near-zero risk. If native reporting later proves insufficient, promotion to a
  separate Center requires a new ADR amendment.
- **Frozen prohibitions for C17:** no metrics database; no data warehouse; no
  duplicated event persistence; no analytics entities; no workflow projections created
  only for navigation; no external BI infrastructure; no mutation actions. Analytics
  uses only existing entity data, existing dashboards/dashlets, native reports,
  filtered lists, and read-only queries.

## Entity Visibility Policy

Top-level navigation is reserved primarily for approved Center entry surfaces and
explicitly justified global native CRM scopes. Every entity or surface receives exactly
one primary visibility class:

- **Class A — Primary Center Entry:** the principal workflow destination for a Center.
- **Class B — Center-Level Operational Queue:** direct list access retained within a
  Center for bulk work, queue processing, exception handling, auditing, or
  troubleshooting.
- **Class C — Center-Level Secondary Destination:** accessible from a Center but not
  the principal entry or primary operational queue.
- **Class D — Relationship or Supporting Object:** reached through relationship
  panels, bottom panels, drill-down links, filtered lists, global search where
  supported, direct record links, or parent record context.
- **Class E — Global Native CRM Scope:** remains available in wider EspoCRM navigation
  because it is not exclusively owned by Prospecting.
- **Class F — Internal or Administrative Object:** not intended for normal operational
  navigation.

## Entity Visibility Classification

**Frozen.** WP1.3 may determine the native physical implementation method, but it must
not reopen any conceptual visibility class without a new ADR amendment.

| Entity / Surface | Center | Visibility Class | Top-Level Allowed? | Required Access Path | Reason |
|---|---|---|---:|---|---|
| `ProspectingDashboard` | Dashboard | A | **Yes** | Top-level entry under the `Prospecting` divider; dashboard-picker fallback; direct URL | Existing custom landing/aggregation page ("Prospecting Operations"); routes into all Centers; owns no data or workflow |
| `ProspectingSearch` | Search Center | A | **Yes** | Top-level entry under the divider; direct URL | Existing custom composition surface (global search + quick-create); the Search Center front door |
| `SearchStrategy` | Search Center | C | No | Search Center → strategy list; direct URL; global search; links from `SearchJob` records | Planning/management list, not a queue; bulk/exception work does not require top-level placement |
| `SearchJob` | Search Center | B | No | Search Center queues via 5 existing status filters; `SearchStrategy` detail → jobs; direct URL; global search | Execution monitoring and exception (failed-job) queue requires direct filtered list access |
| `ProspectPool` | Search Center | B | No | Search Center queues via 4 existing pipeline filters; `SearchJob` detail panel; direct URL; global search | Bulk curation across DISCOVERY→QUALIFICATION→RESEARCH→CRM queues requires direct list access |
| `Lead` | Research Center (composition participant) | E | **Yes (global native)** | Preserve the single global native tab; Dashboard/Search Center "Research Center" link; 26 Prospecting `filterList` entries; direct URL; global search | Native CRM scope is the operational record source and is not exclusively owned by Prospecting; duplication under the Prospecting divider is forbidden |
| `ResearchEvidence` | Research Center | D | No | Lead bottom panel `researchEvidences`; Dashboard supporting link; direct URL; global search | Evidence supports Lead research; it is not the Research Center itself and is removed from direct Prospecting top-level navigation |
| `DraftApproval` | Outreach Center | A | **Yes** | Native list **is** the Outreach Center primary entry; Lead bottom panel `draftApprovals`; direct URL; global search | Primary outreach workflow destination: review → approve/reject outbound content |
| `SendExecution` | Outreach Center | B | No | Outreach Center filtered lists (governed links from the primary entry); Lead bottom panel `sendExecutions`; direct URL; global search | Execution monitoring and failure/exception queue |
| `ReplyEvent` | Outreach Center | B | No | Outreach Center filtered lists (governed links from the primary entry); Lead bottom panel `replyEvents`; direct URL; global search | Reply triage and tracking queue |
| `EmailEvent` | Outreach Center | D | No | Lead bottom panel `emailEvents`; direct record links; direct URL for ACL-permitted roles | Append-only delivery event log (`tab:false`); no user interaction queue; directly addressable for audit/troubleshooting |
| `SalesFeedback` | Research Center | D | No | Lead bottom panel `salesFeedbacks`; `RecentSalesFeedback` dashlet; direct URL | Operational feedback captured on Leads — supporting relationship data, not a navigation destination |
| `LearningSignal` | — (internal; Lead-linked diagnostics) | F | No | Lead bottom panel `learningSignals` (diagnostic); direct URL for ACL-permitted roles | Auto-generated, machine-consumed signal; internal/administrative object, not operational navigation |
| `Quote` | Quote Center | A | **Yes** | Top-level entry under the divider; direct URL; global search | Primary commercial aggregate and Quote Center entry; lifecycle owned by `QuoteTransitionService` |
| `Approval` | Quote Center | B | No | Quote Center approval queue; Quote and PI bottom panels; direct URL; global search | Commercial approval queue for Managers/Finance; distinct from `DraftApproval` (terminology frozen) |
| `ProformaInvoice` | Quote Center | B | No | Quote Center PI queue; Quote bottom panel `proformaInvoices`; direct URL; global search | Financial execution queue for Finance; placement decided without PI redesign |
| `QuoteItem` | Quote Center | D | No | Quote detail bottom panel `quoteItems` only | Child of Quote (`tab:false`); no independent business meaning; not a workflow destination |

No cell is undecided; no classification requires stakeholder escalation. Top-level
`tab:true` capability on entities that lose their standalone tab slot is retained (see
[Capability Declaration](#capability-declaration)) so that direct URLs, global search,
ACL behavior, and framework features are unaffected.

## Runtime Navigation Governance

Three layers touch navigation. They are **not** competing sources of truth; each has
exactly one role:

```text
Accepted ADR (design authority)
→ canonical declarative desired-state artifact (one definition)
→ one controlled idempotent provisioning materializer (one writer)
→ runtime config.tabList (effective state)
→ drift validation
```

### Design Authority

This accepted ADR is the architecture design authority for: Center ownership, visibility
classification, top-level eligibility, required access paths, prohibited navigation
behavior, and migration principles. The ADR does not directly materialize runtime
state. The active design authority is ADR-C16 as amended by this ADR.

### Capability Declaration

Scope metadata (`Resources/metadata/scopes/*.json`) determines whether a surface is
technically capable of participating in navigation, whether EspoCRM treats the scope as
tab-capable, and related scope behavior. A declaration such as `"tab": true` does
**not** prove that the surface appears in effective runtime navigation — verified
counter-example: `SearchStrategy` and `ProspectingDashboard` hold `tab:true`
(`scopes/SearchStrategy.json`, `scopes/ProspectingDashboard.json:4`) yet were absent
from the U04-verified runtime tab list (`PHASE_U04...:45-56`). A scope may remain
technically tab-capable while being omitted from the approved desired navigation.

**`tab:false` governance (frozen):**

- WP1.3 must not retroactively change an existing `tab:true` operational entity to
  `tab:false` merely to hide it from top-level navigation. Top-level omission must be
  achieved through the canonical desired navigation state, not by disabling the scope's
  navigation capability — direct access, global search, permissions, and framework
  behavior depend on the scope.
- Class D relationship/supporting objects and Class F internal/administrative objects
  may legitimately use `tab:false` when: the classification itself justifies no
  independent navigation; required access paths are verified; direct record access,
  relationships, ACL, and framework behavior remain safe; and the decision is not being
  used as a substitute for Center composition. (This is exactly the existing C16
  pattern for `QuoteItem`, `EmailEvent`, `SalesFeedback`, `LearningSignal`.)
- This rule is not absolute: it does not state that every future scope must remain
  `tab:true`.

### Desired Navigation State

Candidate mechanisms evaluated (full inventory):

| Candidate | Verdict | Evidence |
|---|---|---|
| Scope metadata (`tab:true` + `module:"Prospecting"`) | **Capability declaration only** — not the desired-state definition | U04 proved capability ≠ effective navigation |
| `crm-extension` afterInstall / manifest hooks | Rejected — none exist and C16 §6 forbids them | `crm-extension/manifest.json` (no hooks); `ADR_C16...:343-384` |
| JavaScript navbar manipulation | Rejected — forbidden by C16 §6.3 | `ADR_C16...:364-373` |
| Dashboard-layout provisioning scripts (`phase3b06_provision_workspace_roles.php`, `phase3b07_provision_operations_dashboards.php`, `phase3c01_provision_acquisition_workspace.php`) | Not tab-list writers — they provision user-Preferences dashboards; out of scope for tab-list authority, permitted to continue in their own role | Verified: they write `dashboardLayout`/`dashletsOptions` Preferences, never `tabList` |
| Runtime `config.tabList` | Not an authority — it is materialized state | This section |
| Documentation/examples, `temp/`/archive snapshots | Not authorities — historical/duplicate artifacts | `archive/runtime-backups/**/config.php` are snapshots, not writers |
| **Declarative desired-state artifact: `deployment/navigation/phase3c17_navigation.json`** | **SELECTED AND IMPLEMENTED — desired-state definition** | Versioned schema, explicit marker, Center entries, managed entries, preserved global Lead, and supporting-access classifications |
| **Canonical C17 materializer: `deployment/provisioning/phase3c17_provision_operational_centers_navigation.php`** | **SELECTED AND IMPLEMENTED — sole materializer, not the desired-state definition** | Reads the JSON, validates it, preserves unrelated tabs, requires a rollback snapshot, applies idempotently, and emits before/after state |
| U04 script `phase3u04_provision_navbar_tab_order.php` | **Historical C16.3B provisioning evidence and fallback baseline materialization logic** — not the C17 desired-state authority | Sole existing writer; hard-codes a C16.3B-era list (`phase3u04_provision_navbar_tab_order.php:15-38`) |

**Selected desired-state mechanism (frozen):** the authoritative version-controlled
desired-state definition is a **canonical declarative artifact at
`deployment/navigation/phase3c17_navigation.json`**, created in WP1.3. The artifact
must be:

- version-controlled;
- human-readable;
- machine-parseable;
- reviewable without executing PHP;
- limited to navigation desired state;
- aligned with the frozen entity classification in this ADR;
- suitable for deterministic diffing;
- validated before runtime materialization.

It declares at minimum:

- desired global `tabList` ordering;
- approved Center entries;
- navigation dividers when used;
- explicitly retained global native scopes;
- an expected schema/version identifier.

The implemented schema is version `1` with the marker
`phase3c17-wp1-operational-centers-v1`.

**Provisioning materializer (frozen):** exactly one canonical C17 provisioning script
may write runtime `config.tabList`. The materializer must:

- read the declarative desired-state artifact;
- validate its structure;
- apply it idempotently;
- reject malformed or incomplete desired state;
- avoid maintaining an independent hard-coded second copy of the desired state;
- preserve native ACL and user-specific behavior;
- produce safe verification output;
- support rollback (see [Runtime Effective Navigation](#runtime-effective-navigation)).

The JSON artifact and materializer are delivered together in WP1.2–WP1.4.

### Runtime Effective Navigation

Runtime `config.tabList` is the materialized effective navigation consumed by EspoCRM.
It is runtime state, not an independent architecture decision authority.

- **Produced by:** the canonical C17 provisioning materializer only, applying the
  declarative desired-state artifact.
- **Writer versus determinant (frozen):** the canonical C17 provisioning script is the
  **sole authorized global `config.tabList` writer**. It is **not the sole determinant
  of effective visible navigation**: effective navigation may also be shaped by native
  ACL filtering, scope permissions, role visibility, user preferences, and supported
  instance-level behavior. These shaping mechanisms are not competing design
  authorities — the design authority remains this ADR, and the writer remains the only
  authorized mutation path for the global list.
- **Manual admin edits** through EspoCRM's own administration UI are instance
  configuration, must be re-converged by re-running the materializer, and are treated
  as drift.
- **Legacy writers:** the U04 script `phase3u04_provision_navbar_tab_order.php` is a
  deprecated compatibility wrapper that delegates to the canonical C17 materializer.
  It contains no `ConfigWriter` or `tabList` mutation and therefore cannot overwrite
  C17 with the obsolete U04 list. Historical U04 evidence remains in Git history and
  the U04 report; rollback uses the captured snapshot, not legacy re-materialization.
- **Idempotence:** the materializer must converge repeated runs to the declarative
  artifact (the U04 script demonstrated the filter-then-apply idempotent pattern,
  `phase3u04_provision_navbar_tab_order.php:48-67`).
- **Drift detection:** compare the effective runtime `config.tabList` against the
  declarative desired-state artifact (membership and order; the U04 report demonstrated
  exact-membership verification, `PHASE_U04...:45-56`); drift triggers
  re-materialization, never manual patching. Runtime was **not** inspected in
  WP1.2/WP1.2A; drift validation is Migration Plan Phase 5.
- **User/role-specific behavior:** `config.tabList` is instance-global. Role-specific
  visibility is handled natively by scope ACL filtering (C16 §2.3, preserved) — no
  custom tab-hiding logic. Per-user Preferences customization is outside extension
  governance; the materializer writes only global config and must never overwrite user
  Preferences.
- **Rollback governance (frozen):** the primary rollback mechanism is **restoration of
  the captured pre-materialization runtime state**, not re-running a previous script.
  Frozen sequence:
  1. Before C17 materialization, capture the actual effective runtime `config.tabList`.
  2. Store it in a controlled deployment backup or release-evidence location.
  3. Attach timestamp, environment identifier, source commit, and checksum.
  4. Apply the new desired state.
  5. Validate effective navigation.
  6. On rollback, restore the captured pre-materialization state.
  7. Re-running the prior release script (U04) is a fallback baseline reconstruction,
     not the primary restoration mechanism.

  Runtime configuration snapshots are **not** required to be committed to Git. The
  snapshot must not store secrets, credentials, unrelated user data, or sensitive
  runtime configuration; it may contain only the navigation state required for
  rollback. **Validation after rollback (frozen):** runtime `config.tabList` matches
  the captured state; native ACL filtering still works; required queues remain
  accessible; user-specific navigation behavior is not overwritten unintentionally.
- **Duplicate source-tree drift:** prevented by the verified single canonical tree
  (`crm-extension/files/`; former duplicate overlay removed 2026-07-11 per
  `docs/architecture/EXTENSION_SINGLE_SOURCE_MIGRATION_REPORT.md`). The
  `crm-extension/Resources/` design mirror contains no `metadata/scopes/` tree, and
  parity tests guard the mirrored trees (`crm-extension/tests/test_c16_entity_contracts.py`).

### Materialization and Drift Control

Frozen target model:

```text
Accepted ADR
→ canonical declarative desired-state artifact (deployment/navigation/phase3c17_navigation.json)
→ one controlled idempotent provisioning materializer
→ runtime config.tabList
→ drift validation (desired-vs-effective comparison; re-materialize to converge)
```

WP1.2/WP1.2A does not implement convergence; it freezes this governance model. The
desired-state artifact and the materializer are distinct: the artifact declares *what*
navigation must be; the materializer is the only mechanism allowed to *write* it.

## Implementation Principles

All frozen for C17 navigation work:

- no new business entities;
- no database redesign;
- no workflow ownership changes;
- no ACL redesign;
- no record-security redesign;
- no duplicated lifecycle ownership;
- no direct UI status mutation;
- no independent navigation SPA;
- no custom global navigation framework;
- no PI redesign;
- no PDF system;
- no AI quotation;
- no metrics database in C17;
- no navigation-only duplicate persistence;
- no removal of required bulk-processing paths;
- no hiding of an entity without a verified replacement access path.

Navigation implementation may only compose existing capabilities. Direct entity lists
may remain when required for bulk work, queue processing, exception handling, audit,
or troubleshooting.

## Migration Plan

### Phase 1 — ADR Review and Approval

- independent architecture review was performed and WP1.2A amendments A–J were
  applied;
- the independent WP0 exit audit granted C17 implementation authorization;
- this ADR is Accepted by the authorized WP1.2–WP1.4 implementation task.

### Phase 2 — WP1.3 Source-of-Truth Convergence

- create the declarative desired-state artifact
  (`deployment/navigation/phase3c17_navigation.json`) per this ADR;
- create the single canonical provisioning materializer per this ADR;
- enumerate every existing `tabList` writer (verified today: exactly one, the U04
  script — re-verify at Phase 2 start);
- enumerate duplicate metadata definitions (verified today: single canonical tree);
- supersede the U04 script's authority through a deprecated compatibility wrapper that
  delegates to C17; retire no other writers (none exist);
- implement idempotent materialization, drift detection, pre-materialization state
  capture, and snapshot-based rollback per this ADR.

### Phase 3 — WP1.3 Metadata and Visibility Cleanup

- align scope participation and desired navigation with the frozen classification
  table, honoring the frozen `tab:false` governance: no retroactive `tab:false` flips
  on existing `tab:true` operational entities to hide them; omission is expressed in
  the declarative desired state;
- preserve ACL, record security, relationships, required direct URLs, global search
  where required, and required bulk/exception lists;
- do not hide any entity without a verified replacement access path (all replacement
  paths are listed in the classification table).

### Phase 4 — WP1.3 Operational Center Implementation

- reuse existing custom pages (`ProspectingDashboard`, `ProspectingSearch`), native
  entity lists (`ResearchEvidence`, `DraftApproval`, `Quote`), dashboards, and
  dashlets;
- add composition only where current capabilities are insufficient, within the frozen
  per-Center physical boundaries (no new custom Center page in C17);
- introduce no new entity or workflow ownership and no unauthorized status mutation;
- keep any board/Kanban representation read-only.

### Phase 5 — Post-Implementation Runtime Validation

Validate at minimum: effective `config.tabList`; desired-state versus runtime drift;
role-specific visibility; user-specific navigation effects; Center entry surfaces;
direct operational queues; relationship panels; global search; direct URL access;
supporting-object reachability; bulk operations; exception handling; navigation
labels; DraftApproval-versus-Approval terminology; Quote and Approval mutation
boundaries; absence of unauthorized status mutation; pre-materialization capture and
the rollback restoration procedure (including post-rollback validation per this ADR).

### Phase 6 — C16 ADR Annotation

If repository governance later requires a back-reference in ADR-C16, perform it through
a separately authorized documentation task. Preserve all unaffected C16 principles.

## Consequences

### Positive

- workflow-oriented navigation aligned to how Prospecting work is actually performed;
- reduced top-level clutter (five Center entries instead of twelve entity tabs);
- clearer operational entry points (search, research, outreach approval, quotes);
- preserved entity ownership and service ownership (verified canonical services);
- preserved ACL and record security (no permission surface change);
- improved discoverability via a landing Dashboard and workflow-named entries
  (building on the shipped `ResearchEvidence` "Research Center" label precedent);
- controlled runtime navigation state: declarative desired state, exactly one
  materializer, idempotent application, drift detection, and captured-state rollback;
- implementation-ready frozen visibility classifications for WP1.3.

### Negative

- Center composition may require frontend work (labels, filtered queue links,
  Dashboard routing) even though no new framework or new Center page is introduced;
- migration must carefully preserve direct bulk and exception queues (SearchJob,
  ProspectPool, SendExecution, ReplyEvent, Approval, ProformaInvoice);
- runtime navigation requires controlled materialization — a new declarative artifact,
  one materializer, and a deployment step;
- rollback now depends on disciplined pre-materialization state capture (stored
  snapshots with timestamp, environment, commit, checksum);
- existing user bookmarks and habits change for entities that lose standalone tabs;
- dashboards and custom pages need role-specific validation (`acl:false` surfaces +
  ACL-enforcing dashlets);
- source-of-truth convergence requires superseding the historical U04 writer and
  re-verifying that no new writers have appeared.

### Neutral or Accepted Trade-offs

- entities remain independently addressable (direct URL, relationships, search) even
  when omitted from top-level navigation;
- some Center-internal workflows remain native direct list views rather than bespoke
  pages;
- conceptual Centers do not map to literal nested menus (verified native limitation);
- Lead remains globally available while also participating in Research Center
  composition;
- Analytics begins smaller than a full Center, accepting less prominent analytics in
  exchange for zero new persistence and zero scope expansion.

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation | Validation Owner / Work Package |
|---|---|---|---|---|
| ADR versus runtime drift (desired state not materialized) | Medium | Medium | Declarative desired-state artifact plus single materializer; drift comparison in Phase 5; re-materialize to converge | Phase 2 — WP1.3 Source-of-Truth Convergence; Phase 5 — Post-Implementation Runtime Validation |
| Competing `config.tabList` writers appear later | Low | High | C16 §6 prohibition preserved; Phase 2 re-verifies writer inventory; code review gate on `ConfigWriter`/`tabList` | Phase 2 — WP1.3 Source-of-Truth Convergence |
| Duplicate metadata source-tree drift | Low | Medium | Single canonical tree verified; parity tests; do not reintroduce overlays | Phase 2 — WP1.3 Source-of-Truth Convergence |
| Hiding entities without replacement access paths | Low | High | Frozen classification lists required access paths per entity; frozen `tab:false` governance forbids capability removal as a hiding shortcut; Phase 3 gate forbids hiding without verified replacement | Phase 3 — WP1.3 Metadata and Visibility Cleanup |
| Loss of bulk operations | Low | High | Class B queues frozen for SearchJob, ProspectPool, SendExecution, ReplyEvent, Approval, ProformaInvoice; Class A entries `ResearchEvidence`, `DraftApproval`, `Quote` retain their native lists; Phase 5 validates bulk operations | Phase 5 — Post-Implementation Runtime Validation |
| Duplicated Center and entity navigation (same surface twice at top level) | Medium | Low | Top-level restricted to Class A entries + Lead; materializer converges the list idempotently | Phase 2 — WP1.3 Source-of-Truth Convergence; Phase 5 — Post-Implementation Runtime Validation |
| Research Center duplicates or takes ownership of Lead | Low | Medium | Preserve the single global native Lead tab; expose a labeled Dashboard link; retain existing Lead filters and panels; create no Research entity | Phase 4 — WP1 Operational Center Implementation |
| Lead global ownership confusion | Medium | Medium | Frozen: Lead is Class E global native; Research Center composes filters/panels only; extension never touches Lead's `tab` flag | Phase 3 — WP1.3 Metadata and Visibility Cleanup; Phase 5 — Post-Implementation Runtime Validation |
| DraftApproval versus Approval confusion | Medium | Medium | Terminology boundary frozen; distinct labels required ("Draft Approvals" vs "Approvals"); Phase 5 label validation | Phase 4 — WP1.3 Operational Center Implementation; Phase 5 — Post-Implementation Runtime Validation |
| Quote status mutation exposure via navigation | Low | High | All status writes via `QuoteTransitionService` under `WorkflowAuthorizationService`; prohibited-mutation list frozen; Phase 5 checks for unauthorized mutation paths | Phase 4 — WP1.3 Operational Center Implementation; Phase 5 — Post-Implementation Runtime Validation |
| Approval status mutation exposure | Low | High | `ApprovalService` is the only writer of Approval business state; same frozen prohibitions | Phase 4 — WP1.3 Operational Center Implementation; Phase 5 — Post-Implementation Runtime Validation |
| ProformaInvoice ambiguity (placement/ownership) | Low | Medium | Placement explicitly frozen in Quote Center; no PI redesign permitted | Phase 3 — WP1.3 Metadata and Visibility Cleanup |
| Analytics scope expansion | Medium | Medium | Option 2 frozen (Dashboard section); C17 prohibitions on metrics stores; promotion only via ADR amendment | Phase 4 — WP1.3 Operational Center Implementation (governance gate) |
| User-specific navigation configuration overwritten | Medium | Low | Materializer writes global config only, never user Preferences; post-rollback validation checks user behavior is not unintentionally overwritten | Phase 2 — WP1.3 Source-of-Truth Convergence; Phase 5 — Post-Implementation Runtime Validation |
| Role-specific visibility regressions | Low | Medium | Native ACL filtering preserved; role matrix validation in Phase 5 | Phase 5 — Post-Implementation Runtime Validation |
| Rollback failure or incomplete restoration | Medium | Medium | Primary mechanism is restoration of the captured pre-materialization `config.tabList` (timestamp, environment, source commit, checksum); snapshots stored in controlled deployment backup/release-evidence locations, never required in Git, and stripped of secrets/credentials/unrelated user data/sensitive configuration; prior script is only a fallback baseline reconstruction; post-rollback validation frozen | Phase 2 — WP1.3 Source-of-Truth Convergence; Phase 5 — Post-Implementation Runtime Validation |
| Historical WP1 audit filename remains absent | Low | Low | Record the discrepancy; close current evidence through this Accepted ADR, focused contracts, runtime evidence, and the WP1 implementation report | WP1 implementation report |
| Direct URL or relationship regressions | Low | High | Capability metadata unchanged (no retroactive `tab:false` flips); Phase 5 validates URLs, panels, search | Phase 3 — WP1.3 Metadata and Visibility Cleanup; Phase 5 — Post-Implementation Runtime Validation |
| Inaccurate nested-menu assumptions | Low | Medium | Verified native constraint recorded; physical composition limited to divider + entries (U04 pattern) | Phase 4 — WP1.3 Operational Center Implementation |

## Alternatives Considered

### Alternative A — Preserve C16 Entity-First Navigation

Keep twelve entity tabs as the top-level model.

| Criterion | Assessment |
|---|---|
| C16 compatibility | Full (no amendment needed) |
| EspoCRM-native fit | Excellent |
| Workflow clarity | Poor — U01 Gap 1/Gap 2 unresolved; no entry point, no workflow grouping |
| Bulk-operation support | Excellent |
| Implementation complexity | Lowest |
| Upgrade safety | Excellent |
| Runtime governance | Weak — leaves design/runtime divergence ungoverned |
| Rollback | Trivial |
| Access risk | None |
| Entity/workflow ownership risk | None |

Rejected: it solves nothing; the navigation problem that motivated C17 remains.

### Alternative B — Hybrid Operational Centers (CHOSEN)

Center entries at top level; entity lists retained inside Centers as queues and
secondary destinations.

| Criterion | Assessment |
|---|---|
| C16 compatibility | High — preserves native mechanisms, ACL, ownership, bottom panels, bulk lists; partially supersedes composition only |
| EspoCRM-native fit | High — composes divider + scope tabs + existing custom pages and native lists (U04-proven pattern; no nested menus assumed) |
| Workflow clarity | High — entry surfaces match workflows |
| Bulk-operation support | Preserved via frozen Class A entry lists and Class B queues |
| Implementation complexity | Medium — declarative artifact + one materializer + composition metadata/labels; reuses existing pages and native lists |
| Upgrade safety | High — metadata/config only, idempotent materializer |
| Runtime governance | Strong — declarative desired state, single writer, drift detection, captured-state rollback |
| Rollback | Snapshot restoration (primary), script fallback (baseline) |
| Access risk | Low — all entities remain addressable; replacement paths frozen |
| Entity/workflow ownership risk | None — ownership untouched |

Chosen, consistent with repository trajectory (U04 clutter reduction, the
`ResearchEvidence` "Research Center" label, WP0.x workflow hardening).

### Alternative C — Center-Only Navigation

Remove entity lists from navigation entirely; Centers become the only access.

| Criterion | Assessment |
|---|---|
| C16 compatibility | Low — violates dual-access and bulk-list principles (`ADR_C16...:228-235,326-339`) |
| EspoCRM-native fit | Poor — forces custom pages for queue work |
| Workflow clarity | Superficially highest, operationally worst |
| Bulk-operation support | Poor — bulk/exception/audit work loses direct lists |
| Implementation complexity | High — custom queue UIs, ACL reimplementation risk |
| Upgrade safety | Low |
| Runtime governance | Complex |
| Rollback | Hard |
| Access risk | High — hidden entities, broken habits/bookmarks |
| Entity/workflow ownership risk | Medium — Centers drift toward owning workflows |

Rejected: unacceptable access and ownership risk; contradicts preserved C16 principles.

## Approval Requirements

- **The ADR is Accepted.**
- Independent WP0 exit review found no remaining blockers and granted
  `READY_FOR_C17_IMPLEMENTATION`.
- The authorized WP1.2–WP1.4 task permits ADR acceptance, source convergence,
  development implementation, runtime validation, and commit/push only after every
  required Gate passes.
- **WP1.3 must not reopen frozen entity classifications without a new ADR amendment.**
- **Any unresolved source-of-truth decision must be resolved before navigation
  materialization changes begin.** (No unresolved source-of-truth decision remains in
  this ADR; the desired-state artifact path and single materializer are implemented.)
- Runtime materialization and commit/push remain conditional on all offline and
  development-runtime Gates passing.

## Decision Summary

- **Is ADR-C16 deprecated?** No. It remains an Accepted ADR; three composition
  decisions are partially superseded (PS-1, PS-2, PS-3).
- **Which ADR-C16 decisions remain authoritative?** EspoCRM-native navigation
  mechanisms; entity ownership; service-owned workflows; ACL/record-security
  authority; no SPA shell; related access for child/event objects; retained bulk
  lists; no `afterInstall` `tabList` mutation; single canonical metadata tree.
- **Which ADR-C16 decisions are partially superseded?** Entity-first top-level
  composition (PS-1); the Acquisition/Sales/Outreach zone ceiling (PS-2);
  Dashboard-as-supporting-only including N-IA-3's hidden `ProspectingDashboard` (PS-3).
- **Is C17 a continuation, evolution, or replacement?** An evolution with partial
  supersession (Relationship C).
- **What are Operational Centers?** Workflow-oriented navigation and workspace
  compositions (Dashboard, Search, Research, Outreach, Quote) built from native
  EspoCRM mechanisms.
- **Do Centers own entities?** No. Entities remain the data and relationship owners.
- **Do Centers own workflow lifecycle transitions?** No. Canonical services do
  (`QuoteTransitionService`, `ApprovalService`, `ApprovalDecisionService`).
- **Which surfaces may be top-level?** Under the Prospecting divider:
  `ProspectingDashboard` (Dashboard), `ProspectingSearch` (Search Center),
  `DraftApproval` (Outreach Center), and `Quote` (Quote Center). The single global
  native `Lead` tab is preserved and Dashboard labels its link as Research Center;
  Lead is not duplicated under Prospecting.
- **Which entities remain direct operational queues?** `SearchJob`, `ProspectPool`,
  `SendExecution`, `ReplyEvent`, `Approval`, `ProformaInvoice` (Class B).
- **Which entities become secondary destinations?** `SearchStrategy` (Class C).
- **Which entities become relationship or supporting objects?** `ResearchEvidence`,
  `QuoteItem`, `EmailEvent`, and `SalesFeedback` (Class D).
- **Which scopes remain global native CRM scopes?** `Lead` (Class E). `LearningSignal`
  is internal/administrative (Class F), not global.
- **What is the architecture design authority?** This Accepted ADR as an amendment to
  ADR-C16.
- **What is the authoritative desired navigation definition?** The canonical
  declarative desired-state artifact `deployment/navigation/phase3c17_navigation.json`
  version-controlled in Git.
- **What is the role of scope tab metadata?** Capability declaration only — it makes a
  scope tab-capable; it does not define or prove effective navigation.
- **What is the role of runtime `config.tabList`?** Materialized effective navigation
  state consumed by EspoCRM; not an architecture authority.
- **Which mechanism is allowed to materialize runtime navigation?** Exactly one
  canonical C17 provisioning materializer, applying the declarative desired-state
  artifact idempotently.
- **Which existing writers must be retired or superseded?** The U04 script's authority
  is superseded: it delegates to C17 and contains no independent mutation; no other
  writers exist.
- **Is the materializer the sole determinant of visible navigation?** No. It is the
  sole authorized global `config.tabList` writer; effective navigation is also shaped
  by native ACL filtering, scope permissions, role visibility, user preferences, and
  supported instance-level behavior — none of which are competing design authorities.
- **How is runtime drift detected?** By comparing effective `config.tabList` against
  the declarative desired-state artifact (membership and order); drift is converged by
  re-running the materializer.
- **How does rollback work?** Primary: restore the captured pre-materialization
  runtime `config.tabList` (stored with timestamp, environment identifier, source
  commit, and checksum in a controlled deployment backup or release-evidence location;
  never required in Git; no secrets, credentials, unrelated user data, or sensitive
  configuration). Fallback: re-running the prior release script (U04) is baseline
  reconstruction only.
- **Is Analytics a separate C17 Center or initially part of Dashboard?** Initially a
  Dashboard section (Option 2), composed from existing dashlets; promotion requires a
  future ADR amendment.
- **What approval is required before implementation?** Granted by the independent WP0
  exit audit and the authorized WP1.2–WP1.4 implementation task.
- **Is navigation implementation currently authorized?** Yes, conditional on the
  required Gates and runtime safety checks.

## Evidence

Evidence hierarchy labels: **VERIFIED RUNTIME** > **PROVISIONING** (executable) >
**CANONICAL SOURCE** > **TEST** > **ACCEPTED ADR** > **WP1 AUDIT** >
**IMPLEMENTATION REPORT** > historical/duplicate sources > **INFERENCE**.

**Traceability note (frozen):** all ADR-C16 line references in this ADR are anchored
to the Phase3C16.3B frozen version at tag `v1.9.7-alpha` / commit
`d0b9a8077abff804c5f0d231707e83ab3a71d263`. Line references must be revalidated if
ADR-C16 is later annotated or amended.

### Repository preflight and acceptance (2026-07-23)

- Repository root: `D:/EspoCRM-Production` (`git rev-parse --show-toplevel`).
- Branch: `master`.
- Implementation baseline HEAD:
  `827c396eb92cf4a2b45a5483c13529396be4bce6`
  (`phase3c17: WP0 exit reconciliation`), equal to `origin/master`.
- Initial implementation worktree: **clean**.
- Baseline tag at HEAD: `phase3c17-wp0-exit`.
- Expected frozen tag: `v1.9.7-alpha` — **exists**, pointing at
  `d0b9a8077abff804c5f0d231707e83ab3a71d263`
  (`phase3c16: finalize freeze evidence and signoff artifacts`), i.e. the Phase3C16.3B
  freeze. HEAD is three commits ahead: `f87fb01` (WP0.3 quote controller), `3f051fd`
  (WP0.4 authorizer), `cb2cfa5` (WP0.2 mark accepted) — matching the expected baseline.
- Relevant Phase3C17 commits: `f87fb01`, `3f051fd`, `cb2cfa5`.
- Baseline discrepancy retained: `docs/PHASE3C17_WP1_NAVIGATION_IA_AUDIT.md` is
  missing and no renamed equivalent exists. The accepted implementation brief,
  repository-derived ADR evidence, focused contracts, runtime evidence, and WP1
  implementation report form the current evidence chain.
- WP1.2A amendments A–J remain incorporated.
- The independent WP0 exit audit reported: remaining blockers none, risk LOW,
  `READY_FOR_C17_IMPLEMENTATION`.
- Governance instructions `AGENTS.md` and `CLAUDE.md` were read and permit this
  extension-navigation implementation.

### Baseline work packages (**IMPLEMENTATION REPORT**)

- WP0.2 Quote Mark Accepted — IMPLEMENTED:
  `docs/PHASE3C17_WP0_2_ACCEPTED_IMPLEMENTATION.md` (route
  `POST /Prospecting/quote/:id/workflow/mark-accepted`; alias at
  `Services/WorkflowAuthorizationService.php:38`; constant `:28`).
- WP0.3 Quote Controller — IMPLEMENTED:
  `docs/PHASE3C17_WP0_3_QUOTE_CONTROLLER_IMPLEMENTATION.md`;
  `crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/Quote.php:9`.
- WP0.4 Shared Workflow Authorizer — IMPLEMENTED:
  `docs/PHASE3C17_WP0_4_AUTHORIZER_IMPLEMENTATION.md`;
  `crm-extension/files/custom/Espo/Modules/Prospecting/Services/WorkflowAuthorizationService.php:21`.

### Runtime navigation state

- **VERIFIED RUNTIME (historical, 2026-07-14):** effective `config.tabList` ended with
  divider `phase3u04-prospecting` + `ProspectingSearch`, `SearchJob`, `ProspectPool`,
  `ResearchEvidence`; `Meeting`, `Call`, `Case`, `Ticket`, `ProspectingDashboard`,
  `SearchStrategy` absent; native `tabList` supports scope and divider entries only, no
  nested tree (`docs/PHASE_U04_NAVIGATION_POLISH_REPORT.md:9-24,45-56`).
- Runtime was **not** inspected in WP1.2/WP1.2A (no live runtime available); current
  effective state is **INFERENCE** from the single-writer evidence below and is a Phase
  5 validation item.

### Writers and desired-state mechanisms (**PROVISIONING** / **CANONICAL SOURCE**)

- Sole `config.tabList` writer in the repository:
  `deployment/provisioning/phase3u04_provision_navbar_tab_order.php:40,48-68`
  (**PROVISIONING**; idempotency runtime-verified). Retained as historical C16.3B
  provisioning evidence and fallback baseline materialization logic; not the C17
  desired-state authority.
- No `afterInstall`/manifest hooks: `crm-extension/manifest.json` (**CANONICAL SOURCE**);
  zero `tabList` references under `crm-extension/` (full-tree search).
- Dashboard-layout provisioning (user Preferences, not tab list):
  `deployment/provisioning/phase3b06_provision_workspace_roles.php`,
  `phase3b07_provision_operations_dashboards.php`,
  `phase3c01_provision_acquisition_workspace.php`.
- Single canonical installable tree: `crm-extension/files/`
  (`crm-extension/README.md:14-32`; ZIP contents match); duplicate overlay removed
  2026-07-11 (`docs/architecture/EXTENSION_SINGLE_SOURCE_MIGRATION_REPORT.md`);
  `crm-extension/Resources/` is a parity-tested design mirror with no `metadata/scopes/`
  tree (**TEST**: `crm-extension/tests/test_c16_entity_contracts.py`).
- Desired-state artifact `deployment/navigation/phase3c17_navigation.json`: selected
  by this ADR as the future canonical definition; confirmed absent from the repository
  at WP1.2A; creation assigned to WP1.3 (Phase 2).

### Scope and surface metadata (**CANONICAL SOURCE**)

- 16 scope files under
  `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/`,
  all matching the C16 §2.2 table: `tab:false` on `QuoteItem.json`, `EmailEvent.json`,
  `SalesFeedback.json`, `LearningSignal.json`; `tab:true` on all others;
  `entity:false, object:false, acl:false, tab:true` on `ProspectingDashboard.json:2-7`
  and `ProspectingSearch.json:2-7`.
- Custom pages: `metadata/clientDefs/ProspectingDashboard.json:2` →
  `crm-extension/files/client/custom/src/controllers/prospecting-dashboard.js:1-7` →
  `views/prospecting/dashboard.js`; `metadata/clientDefs/ProspectingSearch.json:2` →
  `controllers/prospecting-search.js:1-7` → `views/prospecting/search.js`. No PHP
  controllers or API routes exist for either surface.
- Dashlets: 14 definitions under `Resources/metadata/dashlets/`; no shipped
  DashboardTemplate records; no reports or analytics entities.
- Lead: no `scopes/Lead.json` exists (extension does not declare Lead's `tab`);
  overlay extension via `metadata/entityDefs/Lead.json` (links at `:392-410`),
  `metadata/clientDefs/Lead.json` (26 `filterList` entries `:2-81`; bottom panels
  `:82-131`), `metadata/selectDefs/Lead.json`.
- Labels: `i18n/en_US/Global.json:6-8` (`ProspectingDashboard` = "Prospecting
  Operations", `ProspectingSearch` = "Search", `ResearchEvidence` = "Research Center");
  `i18n/en_US/DraftApproval.json:15` ("Draft Approvals");
  `i18n/en_US/Global.json:12,24` ("Approval"/"Approvals").

### Workflow ownership (**CANONICAL SOURCE**)

- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteTransitionService.php:15`
  (sole writer of `Quote.status`; transition matrix `:25-33`).
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ApprovalService.php:18`
  (only writer of Approval business state; never mutates `Quote.status`, `:14-17`).
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php:22`
  (only Approval↔Quote decision coordinator, `:13-21`).
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteWorkflowActionService.php:22`
  (authorized UI command router, `:13-21`).
- `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostQuoteWorkflowAction.php`
  (workflow API entry).

### Prior architecture and audit documents

- **ACCEPTED ADR:** `docs/architecture/ADR_C16_NAVIGATION_INFORMATION_ARCHITECTURE.md`
  (status `:3`; principles `:24-58`; hierarchy `:64-85`; scope table `:87-106`;
  non-tab objects `:317-324`; `tabList` policy `:343-384`; decision log `:442-452`).
- **IMPLEMENTATION REPORT:** `docs/PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md`
  (gaps `:178-186`; Option A `:284-338`; role matrix `:385-404`; filters `:688-724`).
- **IMPLEMENTATION REPORT / PROVISIONING:** `docs/PHASE_U04_NAVIGATION_POLISH_REPORT.md`.
- Related: `docs/architecture/ADR-C16-ACCEPTED-STATE-DEFERRED.md`,
  `docs/architecture/ADR_C16_NUMBERING_AND_SEQUENCE_STRATEGY.md` (self-declared freezes;
  no ADR-approval process documented anywhere in the repository).

---

## ADR Amendment A1 — WP1.4 Navigation Product Polish Reconciliation

### Status

Accepted

### Purpose

WP1.4 (Navigation Product Polish) is a governed evolution within the authority of
this Operational Centers ADR. It is not a new navigation architecture and it is not
an overturn of this ADR. This amendment formally records the WP1.4-approved
desired-state evolution so that the governance chain is closed:

ADR → approved evolution → desired-state marker → materializer → frozen artifact.

### Desired State Identity Update

- Original desired-state marker recorded by this ADR:
  `phase3c17-wp1-operational-centers-v1`
- Implemented frozen desired-state marker:
  `phase3c17-wp1-4-product-polish-v1`

The `phase3c17-wp1-4-product-polish-v1` marker denotes the WP1.4 governed evolution
of the same accepted desired state. The frozen implementation
(`deployment/navigation/phase3c17_navigation.json`), the materializer constant, and
the navigation contract tests already agree on this marker; this amendment aligns
the ADR with that frozen reality. No runtime behavior changed.

### Authority

`docs/PHASE3C17_WP1_4_NAVIGATION_PRODUCT_POLISH_AUDIT.md`

The WP1.4 product audit approved:

- workflow-first navigation;
- Chinese-primary labels;
- the Sales Development Command Center presentation;
- the governed navigation artifact carrying the
  `phase3c17-wp1-4-product-polish-v1` marker.

### Classification Confirmation

WP1.4 did not violate the frozen A–F entity visibility classification of this ADR.
Confirmed unchanged:

- `Lead` remains the sole global native tab (`requiredPreservedGlobalEntries`).
- `ResearchEvidence` is not promoted to top level.
- `Approval` is not promoted to top level.
- `ProformaInvoice` is not promoted to top level.
- `EmailEvent` is not promoted to top level.
- `SalesFeedback` is not promoted to top level.
- `LearningSignal` is not promoted to top level.

### Membership Evolution

WP1.4 admitted the following pre-existing native scopes into the governed
navigation ordering (`topLevelOrder` in the desired-state artifact):

- `Home`
- `Account`
- `Contact`
- `Opportunity`
- `Email`
- `Task`
- `Calendar`
- `KnowledgeBaseArticle`

These are all existing Class E native scopes. Their inclusion in the governed
ordering is not the addition of new business entries.

### Implementation Reference

- WP1.4 implementation: `4dfaeacc1af61412dabfa33cd23f87975bfdc8b1`
  (`phase3c17: polish product navigation and dashboard IA`)
- Frozen release: `37252303f677b8c8b714b1b083a2bb06dd254a3b`
  (release `v1.9.9-alpha`, artifact SHA-256
  `067A89E52EFB35DF7DA4D9437485381D93004063BFC0E81B67EF2C67995871C2`,
  tags `v1.9.9-alpha` and `phase3c17-wp1-exit`)

### Governance Result

`phase3c17-wp1-4-product-polish-v1` is the accepted desired state of Phase3C17 WP1.
The desired-state marker recorded in this ADR is hereby reconciled with the frozen
implementation, materializer, and contract tests.

### Revision History

- A1: Reconciled WP1.4 governed navigation evolution with frozen implementation
  desired-state marker. No runtime behavior changed.

---

*End of ADR. WP1.2A amendments A–J retained; 2026-07-23 acceptance and implementation
alignment applied; Amendment A1 (WP1.4 product-polish reconciliation) applied.
Status: Accepted.*
