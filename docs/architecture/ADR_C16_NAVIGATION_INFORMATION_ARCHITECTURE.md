# ADR: C16 Navigation Information Architecture

**Status:** Accepted — Design Freeze
**Date:** 2026-07-21
**Phase:** Phase3C16 — Navigation IA Freeze
**Supersedes:** U04 navigation polish (extends, does not replace)
**References:** [PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md](../PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md), [PHASE_U04_NAVIGATION_POLISH_REPORT.md](../PHASE_U04_NAVIGATION_POLISH_REPORT.md), [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md), [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md)

---

## Table of Contents

1. [Navigation Principles](#1-navigation-principles)
2. [Tab Group Design](#2-tab-group-design)
3. [Dashboard Strategy](#3-dashboard-strategy)
4. [ProspectingDashboard / ProspectingSearch Handling](#4-prospectingdashboard--prospectingsearch-handling)
5. [Bottom Panel Strategy](#5-bottom-panel-strategy)
6. [No Invasive afterInstall tabList Mutation](#6-no-invasive-afterinstall-tablist-mutation)
7. [Quote Namespace — Compatibility Acknowledgment](#7-quote-namespace--compatibility-acknowledgment)
8. [Decision Log](#8-decision-log)

---

## 1. Navigation Principles

### 1.1 Principle 1: Native Entity-First

All C16 navigation uses **standard EspoCRM tab infrastructure** — `tab:true` on entity scopes, grouped under the `Prospecting` module divider. No custom SPA, no React navigation tree, no custom left-nav rendering. This is the same architecture chosen in U01 (Option A) and validated in U04.

**Rationale:**

- EspoCRM `config.tabList` supports scope entries and `divider` entries natively.
- Custom navigation views couple to EspoCRM internal rendering APIs, creating upgrade fragility.
- Every Prospecting entity already follows this pattern (scope → `tab:true` → module group → divider).

### 1.2 Principle 2: Three-Zone Navigation

The Prospecting module navigation is organized into three functional zones, each a contiguous block under the same `Prospecting` divider:

| Zone | Label | Purpose | Entities |
|------|-------|---------|----------|
| **获客 Prospecting** | Acquisition | Search strategy planning, job execution, prospect discovery, and research evidence | `ProspectingSearch`, `SearchStrategy`, `SearchJob`, `ProspectPool`, `ResearchEvidence` |
| **销售 Sales** | Sales | Quote-to-invoice workflow, approval chain | `Quote`, `ProformaInvoice`, `Approval` |
| **触达 Outreach** | Outreach | Email draft approval, send execution, and reply tracking | `DraftApproval`, `SendExecution`, `ReplyEvent` |

**Zone ordering:** Acquisition → Sales → Outreach. This follows the natural business flow: discover prospects → close deals → communicate.

### 1.3 Principle 3: Dashboard as Entry Point, Not Tab Replacement

A **Dashboard Template** serves as the primary landing surface for each zone. Individual entity tabs are the drill-down destinations. The dashboard does not replace entity tabs — it augments them with an overview.

### 1.4 Principle 4: Bottom Panels for Child Entities

Entities that have no independent business meaning (child entities, junction-like records) are accessed via **bottom panels** on their parent entity's detail view, not as standalone tabs.

### 1.5 Principle 5: No Invasive tabList Mutation

C16 entities declare `tab:true` in their scope metadata only. They do **not** programmatically mutate `config.tabList` via `afterInstall` hooks or provisioning scripts. Tab ordering and grouping is the deployer's concern — the extension ships correct scope metadata and lets the EspoCRM runtime render tabs by module group.

---

## 2. Tab Group Design

### 2.1 Canonical Tab Hierarchy (Frozen)

```
Prospecting (divider)

  ── 获客 Prospecting ──
  ProspectingSearch      ← Custom view: global search + quick-create entry point
  SearchStrategy         ← Entity: acquisition planning
  SearchJob              ← Entity: discovery execution
  ProspectPool           ← Entity: raw prospect curation
  ResearchEvidence       ← Entity: AI research evidence (read-only reference)

  ── 销售 Sales ──
  Quote                  ← Entity: quote workflow (C16)
  ProformaInvoice        ← Entity: PI workflow (C16)
  Approval               ← Entity: approval decisions (C16)

  ── 触达 Outreach ──
  DraftApproval          ← Entity: email draft approval (C11)
  SendExecution          ← Entity: email send execution (C11/C14)
  ReplyEvent             ← Entity: reply tracking (C14)
```

### 2.2 Entity Tab Visibility by Scope

| Scope | tab | entity | object | acl | Module | Zone |
|-------|:---:|:------:|:------:|:---:|--------|------|
| `ProspectingSearch` | true | false | false | false | Prospecting | Acquisition |
| `SearchStrategy` | true | true | true | true | Prospecting | Acquisition |
| `SearchJob` | true | true | true | true | Prospecting | Acquisition |
| `ProspectPool` | true | true | true | true | Prospecting | Acquisition |
| `ResearchEvidence` | true | true | true | true | Prospecting | Acquisition |
| `Quote` | true | true | true | true | Prospecting | Sales |
| `QuoteItem` | **false** | true | true | true | Prospecting | Sales (bottom panel only) |
| `ProformaInvoice` | true | true | true | true | Prospecting | Sales |
| `Approval` | true | true | true | true | Prospecting | Sales |
| `DraftApproval` | true | true | true | true | Prospecting | Outreach |
| `SendExecution` | true | true | true | true | Prospecting | Outreach |
| `ReplyEvent` | true | true | true | true | Prospecting | Outreach |
| `ProspectingDashboard` | true | false | false | false | Prospecting | (dashboard surface) |
| `EmailEvent` | false | true | true | true | Prospecting | — (no tab) |
| `SalesFeedback` | false | true | true | true | Prospecting | — (no tab) |
| `LearningSignal` | false | true | true | true | Prospecting | — (no tab) |

### 2.3 Tab Visibility by Role

| Tab | Admin | Sales Manager | Sales User | Finance | Integration Bot |
|-----|:-----:|:-------------:|:----------:|:-------:|:---------------:|
| ProspectingSearch | ✅ | ✅ | ✅ | ✅ | ❌ |
| SearchStrategy | ✅ | ✅ | ✅ | ❌ | ❌ |
| SearchJob | ✅ | ✅ | ✅ | ❌ | ❌ |
| ProspectPool | ✅ | ✅ | ✅ | ❌ | ❌ |
| ResearchEvidence | ✅ | ✅ | ❌ | ❌ | ❌ |
| Quote | ✅ | ✅ | ✅ | ❌ | ❌ |
| ProformaInvoice | ✅ | ✅ | ❌ | ✅ | ❌ |
| Approval | ✅ | ✅ | ❌ | ✅ | ❌ |
| DraftApproval | ✅ | ✅ | ✅ | ❌ | ❌ |
| SendExecution | ✅ | ✅ | ✅ | ❌ | ❌ |
| ReplyEvent | ✅ | ✅ | ✅ | ❌ | ❌ |

**Principle:** EspoCRM's native ACL filters tab visibility automatically. `tab:true` + `acl:true` means the tab appears only if the user has at least `read` permission on the scope. No custom tab-hiding logic is needed.

### 2.4 Zone-by-Zone Rationale

#### 获客 Prospecting (Acquisition)

The five acquisition entities represent the complete C10 search pipeline:

1. **ProspectingSearch** — Non-entity custom view. Entry point: global search across all prospecting entities plus quick-create shortcuts for SearchStrategy. Replaces the flat "all tabs visible" landing problem identified in U01 Gap 1.
2. **SearchStrategy** — Planning. "What do we search for?" Product + country + persona + source plan.
3. **SearchJob** — Execution. "What ran?" Status, results, errors. One per keyword × country combination.
4. **ProspectPool** — Results. "What did we find?" Individual prospects moving through the acquisition pipeline (DISCOVERY → QUALIFICATION → RESEARCH → CRM).
5. **ResearchEvidence** — Reference. AI-generated evidence attached to Leads. Read-only for most roles.

#### 销售 Sales (C16)

The three C16 entities represent the complete Quote-to-PI workflow:

1. **Quote** — The master sales document. DRAFT → IN_REVIEW → APPROVED → SENT → ACCEPTED/REJECTED/EXPIRED.
2. **ProformaInvoice** — The financial execution document derived from an approved/accepted Quote. DRAFT → ISSUED → SENT, with independent payment tracking.
3. **Approval** — The decision record. PENDING → APPROVED/REJECTED. Linked to Quote or PI.

**QuoteItem is explicitly not a tab.** It is accessed via the `QuoteItems` bottom panel on Quote detail. QuoteItem has no independent business meaning — it exists only as a child of Quote. This matches the standard CRM pattern (Opportunity Item, Invoice Item, etc. are all bottom-panel-only).

#### 触达 Outreach (C11/C14)

The three outreach entities represent the email lifecycle:

1. **DraftApproval** — Email content approval before sending. PENDING → APPROVED/REJECTED.
2. **SendExecution** — The actual send operation. CREATED → READY → SENT/FAILED/CANCELLED.
3. **ReplyEvent** — Inbound reply tracking from email providers.

### 2.5 Quote Namespace Compatibility Risk

**Risk acknowledged, not resolved.** The `Quote` entity type name collides with a potential future EspoCRM core `Quote` entity (EspoCRM has a Sales Pack extension that includes a Quote entity). This ADR does **not** resolve this namespace conflict.

**Documented risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|-----------|
| EspoCRM core adds a `Quote` entity in a future version | Low | **High** — namespace collision at the database table level (`quote` table), entity metadata level, and API route level | Not mitigated in C16 |
| EspoCRM Sales Pack extension is installed alongside Prospecting | Medium | **High** — two `Quote` entity definitions would conflict; EspoCRM's entity loader would reject one | Not mitigated in C16 |
| Third-party extension defines a `Quote` entity | Low | **Medium** — same collision mechanism | Not mitigated in C16 |

**Why this is not resolved now:**

1. C16.1 entity metadata is already committed with the `Quote` entity type name (commit `ed05319` and later).
2. Renaming `Quote` to a namespaced identifier (e.g., `ProspectingQuote`) would require a database migration, entity metadata migration, relationship foreign-key migration, and all service-layer references updated — scope exceeds the C16 implementation budget.
3. The Prospecting module already owns 14+ entity types with unprefixed names (`SearchStrategy`, `SearchJob`, `ProspectPool`, `DraftApproval`, `SendExecution`, `ReplyEvent`, etc.). `Quote` follows this established convention.

**Migration path (future):** If a namespace collision materializes, the migration would involve:
1. Rename the database table (e.g., `quote` → `prospecting_quote`)
2. Update `entityDefs/Quote.json` entity name
3. Update all `link` fields pointing to `Quote` (QuoteItem.quote, Approval.quote, ProformaInvoice.quote)
4. Update all Service-layer class names and references
5. Run a database migration to update foreign keys

This is a **known technical debt item**, not a design defect. The C16 Navigation IA freeze proceeds with `Quote` as the canonical entity type name.

---

## 3. Dashboard Strategy

### 3.1 Decision: Dashboard Template Takes Priority

**A `DashboardTemplate` is the canonical landing surface for each zone.** Custom dashboard pages (user-created, ad-hoc arrangements) are secondary.

**Rationale:**

- Dashboard Templates survive EspoCRM upgrades and are deployable via provisioning scripts.
- Custom dashboard pages are per-user and cannot be shipped with the extension.
- Dashboard Templates support `tab:true` scope registration, making them appear in the tab list as navigable surfaces.
- The existing `ProspectingDashboard` scope already demonstrates this pattern.

### 3.2 Dashboard Surface Architecture

| Dashboard | Scope | Type | Zone | Status |
|-----------|-------|------|------|--------|
| Prospecting Operations | `ProspectingDashboard` | Dashboard Template | Cross-zone overview | **Implemented** (U03) |
| Prospecting Search | `ProspectingSearch` | Custom View | Acquisition entry | **Implemented** (C06) |

### 3.3 Dashboard vs. Entity Tab Relationship

```
User lands on Prospecting divider
          │
          ▼
   ProspectingSearch (entry point)
   ├── Global search across all Prospecting entities
   ├── Quick-create: SearchStrategy
   └── Recent activity summary
          │
          ▼
   Entity Tabs (drill-down)
   ├── SearchStrategy → list → detail → Generate Jobs
   ├── SearchJob → list (filtered by status) → detail → prospectPools panel
   └── ProspectPool → list (filtered by queue) → detail → promote/push
          │
          ▼
   ProspectingDashboard (overview)
   ├── Acquisition dashlets (strategies, jobs by status, lead pool)
   └── Cross-zone KPIs
```

### 3.4 Explicitly Rejected

| Approach | Reason for Rejection |
|----------|---------------------|
| Custom dashboard page as primary landing | Not deployable via extension; per-user only; cannot be shipped |
| Entity list view as default tab | U01 Gap 1: no workflow narrative; user doesn't know which tab to click first |
| Removing entity tabs in favor of dashboard-only | Violates Principle 1 (entity-first); users need direct list access for bulk operations |

---

## 4. ProspectingDashboard / ProspectingSearch Handling

### 4.1 ProspectingDashboard

**Scope definition:**
```json
{"entity": false, "object": false, "tab": true, "acl": false, "module": "Prospecting", "type": "Base"}
```

**Handling principle:** `ProspectingDashboard` is a **dashboard surface**, not a data entity. It is:

- **Present** in the scope registry with `tab:true` so it appears in the navigation.
- **Not** an entity (`entity:false`) — it has no database table, no CRUD actions, no ACL.
- **Not** removed from the navigation — U04 removed it from the `config.tabList` as a navigation simplification; this ADR restores its logical role as a cross-zone dashboard surface. The U04 `tabList` provisioning script hides it from the *global* tab list to reduce clutter; it remains available as a dashboard template that users can open from the dashboard selector.

**Provisioning note:** The U04 navigation provisioning script (`phase3u04_provision_navbar_tab_order.php`) explicitly hides `ProspectingDashboard` from the `config.tabList`. This ADR does **not** revert that decision. The dashboard template remains accessible via EspoCRM's dashboard picker; it is simply not a top-level navigation tab.

### 4.2 ProspectingSearch

**Scope definition:**
```json
{"entity": false, "object": false, "tab": true, "acl": false, "module": "Prospecting", "type": "Base"}
```

**Handling principle:** `ProspectingSearch` is the **acquisition entry point** — a custom frontend view (not an entity) that provides:

- Global search across SearchStrategy, SearchJob, ProspectPool, and ResearchEvidence.
- Quick-create shortcuts for SearchStrategy.
- Recent activity feed.

It is:

- **Present** in the scope registry with `tab:true` as the first entry under the Prospecting divider.
- **Not** an entity (`entity:false`) — no database table, no ACL.
- **Pinned** as the first acquisition tab — it is the "front door" that U01 Gap 1 identified as missing.

**U04 context:** The U04 navigation provisioning script explicitly adds `ProspectingSearch` as the first entry under the Prospecting divider, followed by `SearchJob`, `ProspectPool`, and `ResearchEvidence`. This ADR affirms that ordering and extends it with the full C16 zone model.

### 4.3 Visibility Principle for Non-Entity Tabs

`ProspectingSearch` and `ProspectingDashboard` both use `acl:false`. This means:

- They appear in the tab list for **all users** with Prospecting module access, regardless of role-specific entity permissions.
- They cannot leak data — they have no database tables, no record lists, and no API endpoints beyond their custom view controllers.
- `ProspectingSearch` delegates all search results to the underlying entity ACLs. A Sales User searching for ResearchEvidence will see only their own records, enforced by the entity ACL, not by ProspectingSearch.

---

## 5. Bottom Panel Strategy

### 5.1 Principle: Child Entities Live on Parent Detail

Entities that have no independent business meaning are accessed exclusively through **bottom panels** on their parent entity's detail view. They do not appear as standalone tabs.

### 5.2 Bottom Panel Assignment (Frozen)

#### Lead Detail Bottom Panels

| Panel | Entity | Relationship | Zone |
|-------|--------|-------------|------|
| Reply Events | `ReplyEvent` | lead → replyEvents (hasMany) | Outreach |
| Send Executions | `SendExecution` | lead → sendExecutions (hasMany) | Outreach |
| Draft Approvals | `DraftApproval` | lead → draftApprovals (hasMany) | Outreach |
| AI Research Evidence | `ResearchEvidence` | lead → researchEvidences (hasMany) | Acquisition |

#### Quote Detail Bottom Panels

| Panel | Entity | Relationship | Zone |
|-------|--------|-------------|------|
| Quote Items | `QuoteItem` | quote → quoteItems (hasMany) | Sales |
| Approvals | `Approval` | quote → approvals (hasMany) | Sales |
| Proforma Invoices | `ProformaInvoice` | quote → proformaInvoices (hasMany) | Sales |

#### ProformaInvoice Detail Bottom Panels

| Panel | Entity | Relationship | Zone |
|-------|--------|-------------|------|
| Approvals | `Approval` | proformaInvoice → approvals (hasMany) | Sales |

### 5.3 Explicitly NOT Tabs

| Entity | Reason |
|--------|--------|
| **QuoteItem** | Child of Quote; no independent business meaning. `tab:false` in scope. |
| **EmailEvent** | Append-only event log; no user interaction. `tab:false` in scope. |
| **SalesFeedback** | Internal feedback; accessed via Lead relationship. `tab:false` in scope. |
| **LearningSignal** | Auto-generated from SalesFeedback hook; machine-consumed. `tab:false` in scope. |

### 5.4 Entities That Are Both Tabs AND Bottom Panels

| Entity | Tab Access | Bottom Panel On |
|--------|-----------|----------------|
| **Approval** | ✅ Standalone tab (Managers/Finance review pending approvals) | Quote detail, PI detail |
| **ProformaInvoice** | ✅ Standalone tab (Finance manages PI lifecycle) | Quote detail |
| **ResearchEvidence** | ✅ Standalone tab (Admin/Sales Manager reference) | Lead detail |
| **SendExecution** | ✅ Standalone tab (outreach operations monitoring) | Lead detail |
| **ReplyEvent** | ✅ Standalone tab (reply tracking) | Lead detail |
| **DraftApproval** | ✅ Standalone tab (draft approval queue) | Lead detail |

**Dual-access rationale:** These entities serve two audiences:
1. **Contextual access** — The parent entity's detail view shows related child records (e.g., "what Approvals exist for this Quote?").
2. **Queue/overview access** — The standalone tab shows all records of that type (e.g., "what Approvals are pending across all Quotes?").

---

## 6. No Invasive afterInstall tabList Mutation

### 6.1 Decision: Scope Metadata Only

C16 entities declare navigation presence exclusively through **scope metadata** (`tab:true` + `module:"Prospecting"`). They do **not** programmatically mutate `config.tabList` via:

- `afterInstall` hooks in the extension manifest
- PHP provisioning scripts that write to `config.tabList`
- JavaScript that manipulates the navbar DOM
- Custom `tabList` overrides in entity metadata

### 6.2 Rationale

| Concern | Mitigation |
|---------|-----------|
| **Idempotency** | `config.tabList` mutations must detect and skip already-applied changes. Scope metadata is inherently idempotent — it either declares `tab:true` or it doesn't. |
| **Upgrade safety** | EspoCRM upgrades may change the `tabList` format. Scope metadata is version-stable across EspoCRM 7.x–10.x. |
| **Multi-extension coexistence** | If another extension also writes to `config.tabList`, ordering conflicts arise. Scope metadata avoids this — EspoCRM resolves tab order from the union of all installed module scopes. |
| **Uninstall cleanliness** | Removing an extension that mutated `config.tabList` leaves stale entries. Removing an extension that only used scope metadata leaves no trace. |
| **User customization** | Users can reorder their `config.tabList` without the extension overwriting their changes on next install/upgrade. |

### 6.3 What IS Allowed

| Mechanism | Allowed? | When |
|-----------|:--------:|------|
| `tab:true` in scope metadata | ✅ | Always — this is the canonical mechanism |
| `module:"Prospecting"` in scope metadata | ✅ | Always — groups tabs under the Prospecting divider |
| Provisioning script that sets initial `tabList` order | ✅ | One-time deployment setup only (U04 pattern) |
| `afterInstall` hook that mutates `config.tabList` | ❌ | Never |
| JavaScript navbar DOM manipulation | ❌ | Never |
| Custom `tabList` in entity clientDefs | ❌ | Never |

### 6.4 The U04 Provisioning Script Boundary

The U04 navigation provisioning script (`phase3u04_provision_navbar_tab_order.php`) is a **deployment tool**, not an extension mechanism. It:

- Runs once during deployment setup (idempotent; safe to run multiple times).
- Sets the initial `config.tabList` order for the Prospecting divider group.
- Is not triggered by extension install/upgrade.
- Is explicitly documented as a manual provisioning step, not an automated hook.

**C16 does not create an equivalent provisioning script for Sales/Outreach zone tabs.** The C16 entities (Quote, ProformaInvoice, Approval) rely on scope metadata alone to appear under the Prospecting divider. The deployer may choose to run a provisioning script to order them, but the extension does not ship one.

---

## 7. Quote Namespace — Compatibility Acknowledgment

### 7.1 The Namespace Conflict

The C16 `Quote` entity type name occupies the `quote` namespace in EspoCRM:

| Namespace Element | Occupied By C16 |
|-------------------|----------------|
| Database table | `quote` |
| Entity metadata key | `Quote` |
| API route prefix | `/Quote` |
| Scope name | `Quote` |
| Relationship foreign keys | `quoteId` on `quote_item`, `approval`, `proforma_invoice` |

### 7.2 EspoCRM Sales Pack Compatibility

EspoCRM's official **Sales Pack** extension (a paid add-on) also defines a `Quote` entity. If both the Prospecting module and the Sales Pack are installed:

- EspoCRM's entity metadata loader will encounter two definitions for `Quote`.
- The second definition loaded will either be rejected (silently ignored) or will overwrite the first, depending on EspoCRM's module load order.
- Database tables may conflict if both entities define a `quote` table with different schemas.
- API routes will conflict — both modules would register `/Quote` routes.

**This ADR does not resolve this conflict.** It documents the risk and defers resolution to a future phase when either:

1. The Sales Pack is actually required alongside the Prospecting module, or
2. EspoCRM core introduces a `Quote` entity in a future version.

### 7.3 Migration Path (Documented, Not Implemented)

If a namespace conflict requires resolution, the migration path is:

1. Rename the C16 entity from `Quote` to `ProspectingQuote` (or equivalent).
2. Rename the database table from `quote` to `prospecting_quote`.
3. Update all foreign-key columns: `quote_item.quote_id` → `prospecting_quote_id`, etc.
4. Update all metadata files: `entityDefs/Quote.json` → `entityDefs/ProspectingQuote.json`, all internal `entity:` references.
5. Update all Service-layer PHP class names and namespace references.
6. Update all i18n keys.
7. Update all test files referencing `Quote`.
8. Run a database migration script to rename tables and columns.
9. Clear EspoCRM metadata cache and rebuild.

**Estimated effort:** 1–2 sessions. **Trigger:** Sales Pack installation requirement or EspoCRM core `Quote` entity announcement.

### 7.4 Design Precedent

The Prospecting module already uses unprefixed entity names for all its custom entities: `SearchStrategy`, `SearchJob`, `ProspectPool`, `DraftApproval`, `SendExecution`, `ReplyEvent`, `Approval`. `Quote` follows this convention. The risk is acknowledged but consistent with the module's established naming practice.

---

## 8. Decision Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| N-IA-1 | Three-zone navigation: Acquisition / Sales / Outreach | Separates distinct business functions under the Prospecting divider; matches C10/C16/C11+C14 domain boundaries | 2026-07-21 |
| N-IA-2 | `QuoteItem.tab = false`; accessed via Quote detail bottom panel only | No independent business meaning; matches standard CRM line-item pattern | 2026-07-21 |
| N-IA-3 | `ProspectingDashboard` remains a dashboard template, hidden from global tabList | U04 navigation simplification; accessible via dashboard picker; not a primary navigation entry | 2026-07-21 |
| N-IA-4 | `ProspectingSearch` is the first Acquisition zone tab | U01 Gap 1 fix: provides an entry-point landing surface with global search + quick-create | 2026-07-21 |
| N-IA-5 | Dashboard Template takes priority over custom dashboard pages | Deployable via extension; survives upgrades; consistent cross-installation experience | 2026-07-21 |
| N-IA-6 | No `afterInstall` tabList mutation | Idempotency, upgrade safety, multi-extension coexistence, uninstall cleanliness | 2026-07-21 |
| N-IA-7 | C16 entities use scope metadata only for navigation (`tab:true` + `module:"Prospecting"`) | Consistent with all existing Prospecting entities; no custom tab registration | 2026-07-21 |
| N-IA-8 | Quote namespace conflict with EspoCRM Sales Pack acknowledged but not resolved | Migration scope exceeds C16 budget; follows existing module naming convention; documented as technical debt | 2026-07-21 |
| N-IA-9 | Dual-access entities (Approval, PI, ResearchEvidence, SendExecution, ReplyEvent, DraftApproval) are both tabs and bottom panels | Serve two audiences: contextual (parent detail) and queue-based (standalone tab) | 2026-07-21 |
| N-IA-10 | Bottom panels assigned: Lead → (ReplyEvent, SendExecution, DraftApproval, ResearchEvidence); Quote → (QuoteItem, Approval, ProformaInvoice); PI → (Approval) | Child entities live on parent detail; standalone tabs for queue-based access | 2026-07-21 |
| N-IA-11 | U04 provisioning script is a deployment tool, not an extension mechanism; C16 does not create an equivalent | Scope metadata is sufficient; deployer chooses tab ordering | 2026-07-21 |

---

## Appendix A: Current Scope Registry (Pre-Freeze Baseline)

All scopes in `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/scopes/`:

| Scope | tab | entity | acl | Zone |
|-------|:---:|:------:|:---:|------|
| `Approval` | true | true | true | Sales |
| `DraftApproval` | true | true | true | Outreach |
| `EmailEvent` | false | true | true | — |
| `LearningSignal` | false | true | true | — |
| `ProformaInvoice` | true | true | true | Sales |
| `ProspectingDashboard` | true | false | false | (dashboard) |
| `ProspectingSearch` | true | false | false | Acquisition |
| `ProspectPool` | true | true | true | Acquisition |
| `Quote` | true | true | true | Sales |
| `QuoteItem` | false | true | true | Sales (panel) |
| `ReplyEvent` | true | true | true | Outreach |
| `ResearchEvidence` | true | true | true | Acquisition |
| `SalesFeedback` | false | true | true | — |
| `SearchJob` | true | true | true | Acquisition |
| `SearchStrategy` | true | true | true | Acquisition |
| `SendExecution` | true | true | true | Outreach |

---

## Appendix B: Related Documents

- [PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md](../PHASE3U01_PROSPECTING_UI_INFORMATION_ARCHITECTURE_AUDIT.md) — U01 IA audit; Option A (native entity-first) recommendation
- [PHASE_U04_NAVIGATION_POLISH_REPORT.md](../PHASE_U04_NAVIGATION_POLISH_REPORT.md) — U04 navigation provisioning; `config.tabList` baseline
- [PHASE3C06_PROSPECTING_UI_FOUNDATION_REPORT.md](../PHASE3C06_PROSPECTING_UI_FOUNDATION_REPORT.md) — C06 ProspectingSearch custom view
- [PHASE3U03_PROSPECTING_UI_POLISH_REPORT.md](../PHASE3U03_PROSPECTING_UI_POLISH_REPORT.md) — U03 ProspectingDashboard productization
- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](ADR_C16_QUOTE_PI_ARCHITECTURE.md) — C16 domain model, state machines, PDF strategy
- [C16_IMPLEMENTATION_PREPARATION.md](C16_IMPLEMENTATION_PREPARATION.md) — Entity field mapping, metadata strategy, test budget
- [BOUNDARIES.md](BOUNDARIES.md) — System boundary enforcement
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) — Current entity map
- [MODULES.md](MODULES.md) — Module structure and cross-module data ownership

---

*End of ADR. C16 Navigation Information Architecture frozen. No code, tabList, or metadata modified.*
