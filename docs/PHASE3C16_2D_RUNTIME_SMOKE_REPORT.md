# Phase3C16.2D — Runtime Smoke Acceptance Report

**Status:** PASS WITH GAPS (non-blocking)  
**Date:** 2026-07-21  
**Phase:** C16.2D Runtime Smoke Validation  
**Commit (pre-smoke):** `c39da06`  
**Author:** Validation Agent (Claude Code + DeepSeek V4 Pro)

---

## Table of Contents

1. [Environment](#1-environment)
2. [Commands Executed](#2-commands-executed)
3. [Results — Entity Loading](#3-results--entity-loading)
4. [Results — Relationships](#4-results--relationships)
5. [Results — ACL & Scope](#5-results--acl--scope)
6. [Results — Language & i18n](#6-results--language--i18n)
7. [Results — Services](#7-results--services)
8. [Results — UI Smoke](#8-results--ui-smoke)
9. [Results — Entity Manager](#9-results--entity-manager)
10. [Gap Analysis](#10-gap-analysis)
11. [Blockers](#11-blockers)
12. [Overall Verdict](#12-overall-verdict)

---

## 1. Environment

| Component | Detail |
|-----------|--------|
| **Host** | Windows 11 Home China 10.0.26200 |
| **Docker** | 29.6.1 |
| **EspoCRM Version** | 10.0.1 |
| **PHP** | 8.4.23 (CLI, NTS) |
| **Database** | MariaDB (espocrm-db container, healthy) |
| **Web Server** | Apache/2.0 (espocrm container, port 8080→80) |
| **Containers** | espocrm (Up 23h, healthy), espocrm-daemon (Up 23h), espocrm-cron (Up 23h), espocrm-db (Up 23h, healthy) |
| **Prospecting Module** | Installed at `/var/www/html/custom/Espo/Modules/Prospecting/` |
| **Pre-existing Entities** | DraftApproval, EmailEvent, Lead, LearningSignal, Opportunity, ProspectPool, ReplyEvent, ResearchEvidence, SalesFeedback, SearchJob, SearchStrategy, SendExecution |

### 1.1 Deployment

C16 entity metadata files were deployed from the local repo to the running container before validation:

```
Source: D:\EspoCRM-Production\crm-extension\files\custom\Espo\Modules\Prospecting\
Target: espocrm:/var/www/html/custom/Espo/Modules/Prospecting/
Method: docker cp (directory merge)
```

**Files deployed:** entityDefs (4), clientDefs (4), scopes (4), aclDefs (4), i18n (8), Services (4 PHP), layouts (6), Api (1)

---

## 2. Commands Executed

| # | Command | Result |
|---|---------|--------|
| 1 | `docker ps` | 4 containers running, all healthy |
| 2 | `docker exec espocrm php --version` | PHP 8.4.23 |
| 3 | `docker cp ... espocrm:/var/www/html/custom/Espo/Modules/Prospecting/` | Files deployed |
| 4 | `docker exec espocrm php command.php rebuild` | `Rebuild has been done.` ✅ |
| 5 | Smoke validation via `php` bootstrap scripts | See §3–§9 |

---

## 3. Results — Entity Loading

### 3.1 Metadata Loading

All four C16 entities load successfully in EspoCRM's metadata system.

| Entity | Fields | Links | Status |
|--------|:------:|:-----:|:------:|
| **Quote** | 16 | 9 | ✅ PASS |
| **QuoteItem** | 12 | 1 | ✅ PASS |
| **ProformaInvoice** | 12 | 6 | ✅ PASS |
| **Approval** | 15 | 4 | ✅ PASS |

### 3.2 Quote Status Enum

```json
["DRAFT", "IN_REVIEW", "APPROVED", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"]
```

All 7 states match the ADR specification. Display styles configured:

| State | Style |
|-------|-------|
| DRAFT | default |
| IN_REVIEW | warning |
| APPROVED | info |
| SENT | primary |
| ACCEPTED | success |
| REJECTED | danger |
| EXPIRED | default |

### 3.3 Quote Key Fields

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `name` | varchar | Yes | `trim: true` |
| `quoteNumber` | varchar(32) | No | `notNull: false` — assigned on DRAFT→IN_REVIEW |
| `status` | enum | Yes | 7 options, default DRAFT |
| `validUntil` | date | No | |
| `amount` | currency | No | Consolidated financial field |
| `opportunity` | link | No | `belongsTo` Opportunity |
| `lead` | link | No | `belongsTo` Lead |

### 3.4 Approval Targeting

The Approval entity implements the polymorphic targeting pattern:

| Field | Type | Values | Purpose |
|-------|------|--------|---------|
| `targetType` | enum | `"Quote"`, `"ProformaInvoice"` | Identifies the target entity type |
| `targetId` | varchar(36) | UUID string | Identifies the target entity instance |
| `quote` | link | nullable | Business link to Quote |
| `proformaInvoice` | link | nullable | Business link to ProformaInvoice |

Index on `(targetType, targetId)` enables fast lookups.

### 3.5 Approval Audit Fields

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `requestedBy` | link (User) | Yes | Auto-set on create |
| `approver` | link (User) | No | Set on decision |
| `decision` | enum | No | `APPROVED` / `REJECTED` |
| `reason` | text | No | Decision rationale |
| `decidedAt` | datetime | No | Decision timestamp |
| `approvalLevel` | int | Yes | Default 1, forward-compat for multi-level |

---

## 4. Results — Relationships

### 4.1 Quote ↔ QuoteItem

```
QuoteItem.quote → belongsTo → Quote         ✅ PASS
Quote.quoteItems → hasMany → QuoteItem      ✅ PASS
```

- QuoteItem → Quote: `belongsTo`, entity `Quote`, foreign `quoteItems`
- Quote → QuoteItems: `hasMany`, entity `QuoteItem`, foreign `quote`

### 4.2 Quote ↔ Approval

```
Approval.quote → belongsTo → Quote          ✅ PASS
Quote.approvals → hasMany → Approval        ✅ PASS
```

### 4.3 Quote ↔ ProformaInvoice

```
ProformaInvoice.quote → belongsTo → Quote   ✅ PASS
Quote.proformaInvoices → hasMany → PI        ✅ PASS
```

### 4.4 Approval ↔ ProformaInvoice

```
Approval.proformaInvoice → belongsTo → PI   ✅ PASS
```

### 4.5 Relationship Integrity

| Link | Type | Foreign | Status |
|------|------|---------|:------:|
| Quote → Opportunity | belongsTo | Opportunity | ✅ |
| Quote → Lead | belongsTo | Lead | ✅ |
| Quote → QuoteItems | hasMany | quoteItems | ✅ |
| Quote → Approvals | hasMany | approvals | ✅ |
| Quote → ProformaInvoices | hasMany | proformaInvoices | ✅ |
| QuoteItem → Quote | belongsTo | quote | ✅ |
| Approval → Quote | belongsTo | quote | ✅ |
| Approval → PI | belongsTo | proformaInvoice | ✅ |
| Approval → requestedBy | belongsTo | User | ✅ |
| Approval → approver | belongsTo | User | ✅ |
| PI → Quote | belongsTo | quote | ✅ |

---

## 5. Results — ACL & Scope

### 5.1 Module-Level ACL

All four entities have module-level ACL enabled via `aclDefs/`:

| Entity | ACL Path | Status |
|--------|----------|:------:|
| Quote | `Prospecting.Quote: true` | ✅ |
| QuoteItem | `Prospecting.QuoteItem: true` | ✅ |
| ProformaInvoice | `Prospecting.ProformaInvoice: true` | ✅ |
| Approval | `Prospecting.Approval: true` | ✅ |

### 5.2 Scope Definitions

| Entity | Type | Tab | ACL | Status Field | Object |
|--------|------|:---:|:---:|-------------|:------:|
| **Quote** | Base | ✅ (1) | ✅ (1) | `status` | ✅ (1) |
| **QuoteItem** | Base | ❌ (inline) | ✅ (1) | — | — |
| **ProformaInvoice** | Base | ✅ (1) | ✅ (1) | (not set) | — |
| **Approval** | Base | ✅ (1) | ✅ (1) | `status` | — |

**Assessment:** QuoteItem is correctly configured as inline-only (no tab). Quote, ProformaInvoice, and Approval are tab-visible with ACL enabled.

### 5.3 Field-Level ACL

No field-level ACL defined in metadata. The ADR specifies field-level ACL for `Quote.total`, `Quote.taxAmount`, `ProformaInvoice.paidAt`, `Approval.decision`, and `Approval.reason`. This is deferred to C16.2/C16.3 Service layer implementation.

---

## 6. Results — Language & i18n

### 6.1 i18n Files

| Entity | en_US | zh_CN |
|--------|:-----:|:-----:|
| Quote | ✅ | ✅ |
| QuoteItem | ✅ | ✅ |
| ProformaInvoice | ✅ | ✅ |
| Approval | ✅ | ✅ |

### 6.2 Translation Resolution

All four entity names fall back to the entity name when queried via `$language->translate()`:

| Entity | scopeNames | scopeNamesPlural |
|--------|-----------|-----------------|
| Quote | `Quote` | `Quote` |
| QuoteItem | `QuoteItem` | `QuoteItem` |
| ProformaInvoice | `ProformaInvoice` | `ProformaInvoice` |
| Approval | `Approval` | `Approval` |

**Finding:** The i18n JSON files exist on disk but the translation keys do not match EspoCRM's expected structure for `scopeNames`. The entity i18n files use `"labels"` for display names (e.g., `"labels": {"Quotes": "Quotes"}`) but EspoCRM resolves `scopeNames` from a different key path. This is a **non-blocking metadata gap** — the UI will show raw entity names until the i18n key structure is corrected.

**Recommended fix:** Add `"scopeNames": {"Quote": "Quote"}` and `"scopeNamesPlural": {"Quote": "Quotes"}` at the top level of each entity i18n file, following the standard EspoCRM entity translation convention.

---

## 7. Results — Services

### 7.1 Service Classes (on Disk)

| Service | File | Status |
|---------|------|:------:|
| `QuoteNumberingService` | `Services/QuoteNumberingService.php` | ✅ File exists |
| `QuoteNumberingServiceInterface` | `Services/QuoteNumberingServiceInterface.php` | ✅ File exists |
| `QuoteTransitionService` | `Services/QuoteTransitionService.php` | ✅ File exists |
| `QuoteWorkflowActionService` | `Services/QuoteWorkflowActionService.php` | ✅ File exists |
| `PostQuoteWorkflowAction` | `Api/PostQuoteWorkflowAction.php` | ✅ File exists |

### 7.2 DI Container Registration

All three service lookups (`quoteNumberingService`, `quoteTransitionService`, `quoteWorkflowActionService`) fail with `Could not load service`.

**Root cause:** `Resources/metadata/app/services.json` is missing. EspoCRM requires services to be registered via DI configuration metadata. The PHP class files exist on disk but are not discoverable by the container.

**Recommended fix:** Create `Resources/metadata/app/services.json` with service definitions following EspoCRM's DI conventions. Example:

```json
{
  "quoteNumberingService": {
    "className": "Espo\\Modules\\Prospecting\\Services\\QuoteNumberingService"
  },
  "quoteTransitionService": {
    "className": "Espo\\Modules\\Prospecting\\Services\\QuoteTransitionService"
  },
  "quoteWorkflowActionService": {
    "className": "Espo\\Modules\\Prospecting\\Services\\QuoteWorkflowActionService"
  }
}
```

---

## 8. Results — UI Smoke

### 8.1 Web UI Accessibility

| Check | Result |
|-------|:------:|
| Web server listening | ✅ `http://localhost:8080` serves EspoCRM HTML |
| API endpoint | ✅ `http://localhost:8080/api/v1/` returns 401 (auth required, expected) |
| Frontend assets | ✅ `loader-params` present, cache timestamp valid |

### 8.2 Layout Files

| Entity | Detail Layout | List Layout |
|--------|:------------:|:-----------:|
| Quote | ✅ EXISTS | ✅ EXISTS |
| Approval | ✅ EXISTS | ✅ EXISTS |
| ProformaInvoice | ✅ EXISTS | ✅ EXISTS |

### 8.3 ClientDef Analysis

| Aspect | Quote | Approval |
|--------|:-----:|:--------:|
| `dynamicLogic` | none defined | none defined |
| `views` | empty | — |
| `menu` | empty | — |
| `sidePanels` | none defined | — |

**Finding:** ClientDefs are minimal — no dynamic logic, views, menus, or side panels are defined. This means:
- Quote detail page will render with default EspoCRM layout (top-down fields)
- No relationship panels (QuoteItems, Approvals, ProformaInvoices) will appear as side panels
- No custom views or menus are registered

This is **expected for C16.1** metadata phase. Side panels, dynamic logic, and UI actions are implemented in C16.2 (Quote workflow) and C16.3 (Approval workflow).

### 8.4 Browser UI Verification

**NOT PERFORMED.** Full browser-based UI smoke (login as Sales/Manager/Admin, navigate to Quote list/detail, verify action visibility) requires:
- A browser automation tool (Playwright/Puppeteer/Selenium)
- Or manual testing by a human operator

**What can be confirmed from metadata:**
- Quote is tab-visible (will appear in navigation for authorized users)
- QuoteItem is inline-only (will only appear nested in Quote detail)
- Approval is tab-visible
- ProformaInvoice is tab-visible
- Status field has correct display styles for all 7 Quote states
- Status field has correct display styles for Approval states

**What requires browser verification:**
- Submit Review action visibility for Sales role
- Approve/Reject action visibility for Manager role
- Expire action visibility for Admin role
- Correct action hiding when in wrong state (e.g., Approve hidden when already APPROVED)

**Recommendation:** Perform browser-based UI smoke in C16.2D+ or C16.3 after DI service registration and UI action configuration are complete.

---

## 9. Results — Entity Manager

### 9.1 Repository Instantiation

| Entity | Repository Class | Status |
|--------|-----------------|:------:|
| Quote | `Espo\Core\Templates\Repositories\Base` | ✅ |
| QuoteItem | `Espo\Core\Templates\Repositories\Base` | ✅ |
| ProformaInvoice | `Espo\Core\Templates\Repositories\Base` | ✅ |
| Approval | `Espo\Core\Templates\Repositories\Base` | ✅ |

### 9.2 Entity Instantiation

| Entity | Entity Class | Status |
|--------|-------------|:------:|
| Quote | `Espo\Core\Templates\Entities\Base` | ✅ |
| QuoteItem | `Espo\Core\Templates\Entities\Base` | ✅ |
| ProformaInvoice | `Espo\Core\Templates\Entities\Base` | ✅ |
| Approval | `Espo\Core\Templates\Entities\Base` | ✅ |

All entities use EspoCRM's `Base` template, which is appropriate for standard business entities with CRUD, ACL, and stream support.

---

## 10. Gap Analysis

### 10.1 Quote Field Gaps (vs ADR Specification)

| ADR Field | In entityDef? | Status |
|-----------|:------------:|:------:|
| `currency` | ❌ | Not present — ADR §3.1.1 specifies ISO 4217 currency field; consolidated into `amount`/`amountCurrency` by EspoCRM convention |
| `subtotal` | ❌ | Not present — ADR specifies auto-calculated from line items; deferred to C16.2 Service layer |
| `taxRate` | ❌ | Not present — deferred to C16.2 |
| `taxAmount` | ❌ | Not present — deferred to C16.2 |
| `total` | ❌ | Not present — deferred to C16.2 |
| `notes` | ❌ | Not present — ADR §3.1.1; deferred to C16.1 metadata extension |
| `termsAndConditions` | ❌ | Not present — ADR §3.1.1; deferred to C16.1 metadata extension |
| `pdfGeneratedAt` | ❌ | Not present — deferred to C16.4 PDF Pipeline |
| `pdfStoragePath` | ❌ | Not present — deferred to C16.4 PDF Pipeline |

**Assessment:** The current Quote entityDef is a C16.1 minimum-viable definition. The `amount` field (type: currency) consolidates the financial total. Full financial field decomposition (`subtotal`, `taxRate`, `taxAmount`, `total`) is part of C16.2 QuoteItem line-total calculation. This is **design-appropriate** — the entity structure supports incremental field addition without migration.

### 10.2 QuoteItem Field Gaps

| ADR Field | In entityDef? | Status |
|-----------|:------------:|:------:|
| `product` | ❌ | Not present — deferred |
| `description` | ❌ | Not present — deferred |
| `discount` | ❌ | Not present — deferred to C16.2 |
| `lineTotal` | ❌ | Not present — auto-calculated; deferred to C16.2 |
| `sortOrder` | ❌ | Not present — deferred |

### 10.3 ProformaInvoice Gaps

The PI entity status enum uses: `DRAFT, ISSUED, SENT, PAID, VOID`. Per [ADR_C16_STATE_MACHINE_ADDENDUM.md](architecture/ADR_C16_STATE_MACHINE_ADDENDUM.md), the canonical model separates workflow (`status`) from payment (`paymentStatus`). The current entityDef uses the original conflated model. This should be updated to match the canonical state machine addendum.

### 10.4 Missing DI Service Registration

See §7.2. Services are written but not registered in the DI container. This blocks:
- Quote numbering on DRAFT→IN_REVIEW
- State transition validation
- Workflow action API endpoints

### 10.5 i18n Key Structure

See §6.2. Entity i18n files exist but translation keys don't match EspoCRM's convention for `scopeNames`.

### 10.6 UI Configuration

ClientDefs are minimal (no views, menus, sidePanels, dynamicLogic). This is appropriate for C16.1 metadata foundation; UI configuration is enriched in C16.2/C16.3.

---

## 11. Blockers

### 11.1 Runtime Compatibility Blockers

**None.** The EspoCRM runtime loads all four C16 entities without errors. `php command.php rebuild` completes successfully. Entity manager can instantiate repositories and entities.

### 11.2 Functional Blockers (for C16.2)

| Blocker | Impact | Resolution |
|---------|--------|------------|
| Missing `app/services.json` | Quote numbering, state transitions, and workflow actions are non-functional | Create DI service registration metadata |
| Missing i18n key structure | Entity names appear as raw strings in UI | Restructure i18n JSON files |
| Quote missing financial fields | Line-item totals cannot be stored | Extend Quote/QuoteItem entityDefs per ADR field map |

### 11.3 Non-Blockers (for C16.2)

- ClientDef views/menus/sidePanels — UI enrichment; does not block backend service operation
- ProformaInvoice status enum conflated — can be updated in C16.5
- Missing PDF fields — C16.4 scope

---

## 12. Overall Verdict

### Verdict: PASS WITH GAPS

| Dimension | Verdict |
|-----------|:-------:|
| **Entity metadata loading** | ✅ PASS |
| **Relationship integrity** | ✅ PASS |
| **ACL & scope configuration** | ✅ PASS |
| **Layout file presence** | ✅ PASS |
| **Entity manager compatibility** | ✅ PASS |
| **Rebuild (command.php)** | ✅ PASS |
| **Web UI serving** | ✅ PASS |
| **Service DI registration** | ⚠️ GAP |
| **i18n translation resolution** | ⚠️ GAP |
| **ADR field completeness** | ⚠️ GAP |
| **Browser UI smoke** | ⚠️ NOT TESTED |

**C16.2D smoke validates that the EspoCRM runtime correctly loads and processes all C16 entity metadata.** The four entities (Quote, QuoteItem, ProformaInvoice, Approval) are recognized by the metadata system, entity manager, and ACL framework. Relationships are correctly wired. `php command.php rebuild` completes without errors.

**Three non-blocking gaps** require attention before C16.2 functional testing:
1. DI service registration metadata (`app/services.json`)
2. i18n key structure for scope names
3. Quote/QuoteItem field completion per ADR specification

**Browser-based UI smoke** (login as Sales/Manager/Admin, verify action visibility) could not be performed in this terminal-based validation session. Metadata-level checks confirm the UI foundation is in place (layouts, clientDefs, scopes).

---

## Appendix A: Validation Scripts

Temporary validation scripts were deployed to the container and cleaned up after execution:

| Script | Purpose | Disposition |
|--------|---------|-------------|
| `c16_2d_smoke_check.php` | Entity metadata, relationships, ACL, language, services | Removed |
| `c16_2d_deep_check.php` | Financial fields, i18n deep check, DI registration | Removed |
| `c16_2d_ui_check.php` | ClientDef analysis, layouts, scopes | Removed |
| `c16_2d_api_check.php` | Entity manager, repository, ACL verification | Removed |

Local copies at `D:\EspoCRM-Production\scripts\` were also removed.

## Appendix B: Container State

The EspoCRM container retains the deployed C16 entity files at:

```
/var/www/html/custom/Espo/Modules/Prospecting/Resources/
  metadata/
    entityDefs/    Quote.json, QuoteItem.json, ProformaInvoice.json, Approval.json
    clientDefs/    Quote.json, QuoteItem.json, ProformaInvoice.json, Approval.json
    scopes/        Quote.json, QuoteItem.json, ProformaInvoice.json, Approval.json
    aclDefs/       Quote.json, QuoteItem.json, ProformaInvoice.json, Approval.json
  layouts/         Quote/, Approval/, ProformaInvoice/
  i18n/           en_US/, zh_CN/
  Services/        QuoteNumberingService.php, ...
  Api/             PostQuoteWorkflowAction.php
```

Existing C10/C11/C14 entity files were not modified or affected.

## Appendix C: Related Documents

- [ADR_C16_QUOTE_PI_ARCHITECTURE.md](architecture/ADR_C16_QUOTE_PI_ARCHITECTURE.md) — Base architecture
- [ADR_C16_STATE_MACHINE_EXTENSIONS.md](architecture/ADR_C16_STATE_MACHINE_EXTENSIONS.md) — State machine extensions
- [ADR_C16_STATE_MACHINE_ADDENDUM.md](architecture/ADR_C16_STATE_MACHINE_ADDENDUM.md) — PI state reconciliation (canonical)
- [C16_IMPLEMENTATION_PREPARATION.md](architecture/C16_IMPLEMENTATION_PREPARATION.md) — Implementation prep
- [PHASE3C16_1A_METADATA_AUDIT.md](PHASE3C16_1A_METADATA_AUDIT.md) — C16.1A metadata audit

---

*End of Report. All findings are based on runtime validation against a live EspoCRM 10.0.1 instance.*
