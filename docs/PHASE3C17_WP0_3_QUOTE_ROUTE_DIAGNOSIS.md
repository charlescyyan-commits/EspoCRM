# Phase3C17 WP0.3 — Quote Creation Route Diagnosis

**Status:** DIAGNOSIS COMPLETE
**Date:** 2026-07-22
**Baseline:** Phase3C16.3B frozen release `v1.9.7-alpha` (`d0b9a80`)
**Auditor:** Principal Software Architect (read-only)
**Methodology:** Static metadata comparison + code audit

---

## Executive Verdict

**ROOT_CAUSE_IDENTIFIED**

Confidence: **HIGH**

---

## Problem Statement

`POST /api/v1/Quote` returns HTTP 404. This prevents the C17 Quote Center from performing standard Quote CRUD through the EspoCRM REST Record API. The C17 Charter defines this as the WP0.3 entry gate.

The same issue was noted during Phase3C16.3B-R5 and recorded as a deferred API-surface gap (Scope Amendment A). This diagnosis determines the root cause and proposes the minimum fix.

---

## Evidence Collected

### 1. Route Registration Analysis

| Check | Result |
|-------|--------|
| `routes.json` conflict | None — Quote workflow route is `/Prospecting/quote/:id/workflow/:action` (separate namespace) |
| `routes.json` defines standard CRUD | No — standard CRUD routes are built by EspoCRM core from entity metadata |
| Custom `PostQuoteWorkflowAction` | Present and functional — handles workflow transitions only |
| Quote entity registered in `entityDefs` | Yes — `entityDefs/Quote.json` with fields, links, indexes |
| Quote entity registered in `scopes` | Yes — `scopes/Quote.json`: `entity: true, object: true, tab: true, acl: true` |
| Quote entity registered in `clientDefs` | Yes |
| Quote entity registered in `aclDefs` | Yes — `aclDefs/Quote.json`: `{"Prospecting": {"Quote": true}}` |

All metadata is present and correctly formed. The scope grants full entity/object/tab/acl privileges. This should enable the standard Record API.

### 2. Entity Controller Comparison

The Prospecting module has 16 entities with scopes. Only 7 have Controllers:

| Entity | Controller | Record API |
|--------|-----------|------------|
| ResearchEvidence | `Controllers/ResearchEvidence.php` extends `Record` | ✅ Working |
| SearchJob | `Controllers/SearchJob.php` extends `Record` | ✅ Working |
| SalesFeedback | `Controllers/SalesFeedback.php` extends `Record` | ✅ Working |
| ProspectPool | `Controllers/ProspectPool.php` extends `Record` | ✅ Working |
| LearningSignal | `Controllers/LearningSignal.php` extends `Record` | ✅ Working |
| EmailEvent | `Controllers/EmailEvent.php` extends `Record` | ✅ Working |
| SearchStrategy | `Controllers/SearchStrategy.php` extends `Record` | ✅ Working |
| **Quote** | **MISSING** | ❌ **HTTP 404** |
| QuoteItem | MISSING | ❌ Likely 404 |
| Approval | MISSING (intentionally internal) | ❌ 404 (by design) |
| DraftApproval | MISSING (intentionally internal) | ❌ 404 (by design) |
| ProformaInvoice | MISSING (deferred) | ❌ Likely 404 |
| Others | MISSING (UI/dashlet entities) | N/A |

**Pattern:** Every custom entity that exposes the standard REST Record API has a minimal Controller class. Quote is the only business entity that needs the Record API but lacks a Controller.

### 3. Controller Pattern

All working controllers follow this exact pattern:

```php
<?php
namespace Espo\Modules\Prospecting\Controllers;
use Espo\Core\Controllers\Record;
class ResearchEvidence extends Record {}
```

This is a 5-line file. The empty class body is intentional — all Record API behavior (list, read, create, update, delete, mass-update, etc.) is inherited from `Espo\Core\Controllers\Record`.

### 4. Why the Controller Matters

In EspoCRM, the API route `POST /api/v1/{Entity}` resolves to a controller class through the framework's routing system:

1. Framework parses `/api/v1/Quote` → entity = `Quote`
2. Framework looks up the entity's module → `Prospecting`
3. Framework resolves controller class → `Espo\Modules\Prospecting\Controllers\Quote`
4. Class doesn't exist → **HTTP 404** (route unresolved)

The fallback to core `Espo\Controllers\Record` does NOT trigger for module-scoped entities. The core fallback only applies to entities in the `Espo` namespace (e.g., `Account`, `Contact`, `Lead` which have core controllers at `Espo\Controllers\Account`).

### 5. ACL Analysis

Quote's `aclDefs/Quote.json` uses the same format as ResearchEvidence and all other working entities:

```json
{"Prospecting": {"Quote": true}}
```

This format is **valid and consistent** across the module. It is not the cause of the 404. ACL issues would produce HTTP 403 (Forbidden), not 404 (Not Found). The 404 indicates the route doesn't exist at all.

### 6. Runtime Evidence

The R5 report and R5C continuation both documented this 404:
- R5 §9: "Authenticated generic `POST /api/v1/Quote` returned HTTP 404 during preflight"
- R5 §11: "The deferred generic Quote record API surface remains HTTP 404 by design of Scope Amendment A"

The R5C continuation (which deployed the artifact and rebuilt metadata) confirmed all other entities worked through the Record API. The 404 persisted for Quote because the controller class was never added.

---

## Root Cause

**Quote entity is missing `Controllers/Quote.php`.**

The standard EspoCRM REST Record API cannot resolve a route for `POST /api/v1/Quote` because the framework's controller resolution fails at `Espo\Modules\Prospecting\Controllers\Quote` — the class does not exist.

This is not an ACL issue, not a scope issue, not a route conflict, and not a metadata issue. It is a simple missing file that was intentionally deferred in Phase 3A-2.1 (per `Controllers/README.md`: "No controller PHP in Phase 3A-2.1") and was never added in subsequent phases.

---

## Proposed Fix Scope

### Minimum required

Create one file:

```
crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/Quote.php
```

With content:

```php
<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Controllers;

use Espo\Core\Controllers\Record;

class Quote extends Record
{
}
```

### Post-fix verification

1. Include in extension package
2. Deploy artifact
3. Rebuild EspoCRM metadata
4. Verify: `POST /api/v1/Quote` returns HTTP 200/201 (not 404)

### Optional (same pattern)

Apply the same fix to QuoteItem if C17 needs Quote line-item CRUD:

```
crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/QuoteItem.php
```

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Controller exposes unintended CRUD surface | **Low** | ACL still governs access; `QuoteStatusMutationGuard` still blocks direct status mutations; the workflow API remains the canonical path for status transitions |
| `QuoteStatusMutationGuard` bypass via Record API | **None** | The guard hooks into `beforeSave` — standard Record API creates/updates go through the same ORM save path as workflow actions |
| Four-eyes bypass | **None** | Four-eyes is enforced at the service layer (ApprovalService), not at the controller layer |
| Regressions in existing workflow endpoints | **None** | The new Controller is a separate class; `PostQuoteWorkflowAction` is unchanged |

The Record API controller adds standard CRUD (create, read, update, delete, list) for Quote without bypassing any existing guards. Workflow state transitions remain governed by `PostQuoteWorkflowAction` → `QuoteWorkflowActionService`.

---

## Why EntityManager Works While REST Fails

**Path B (EntityManager/shell):**

```
PHP EntityManager::createEntity('Quote', $data)
  → resolves entity class internally
  → bypasses HTTP routing entirely
  → creates record directly in database
  → Works ✅
```

**Path A (REST Record API):**

```
POST /api/v1/Quote
  → EspoCRM HTTP router
  → resolves controller: Espo\Modules\Prospecting\Controllers\Quote
  → class not found → 404 ❌
```

Path A fails at the routing layer before any business logic executes. Path B succeeds because it bypasses HTTP routing entirely and talks directly to the ORM.

---

## Recommended Next Step

**WP0.3 → WP1.0: Create the Quote Controller**

Create the missing `Controllers/Quote.php` following the established 5-line pattern, rebuild metadata, and verify `POST /api/v1/Quote` returns a valid response. This unblocks the C17 Quote Center's standard CRUD operations.

---

## Diagnosis Metadata

| Field | Value |
|-------|-------|
| Diagnosis date | 2026-07-22 |
| Baseline commit | `d0b9a8077abff804c5f0d231707e83ab3a71d263` |
| Files inspected | 20+ (scopes, entityDefs, aclDefs, clientDefs, routes.json, Controllers, Api, ADRs, REST docs) |
| PHP source modified | **None** |
| Confidence | **HIGH** — root cause is a missing file, confirmed by pattern comparison with 7 working entities |
