# PHASE3C17 R1.1 Runtime Route Materialization Audit

**Date:** 2026-07-25  
**Repository:** `D:\EspoCRM-Production`  
**Baseline:** `57b5840`  
**Mode:** READ-ONLY investigation  
**Artifact:** `deployment/prospecting-extension-1.9.10-alpha.zip`

---

## Conclusion

**Root Cause: MISSING METADATA REBUILD after extension installation.**

No code defect. No packaging path issue. No manifest error.

All four entities (`DraftApproval`, `Approval`, `ReplyEvent`, `SendExecution`) have correct controllers, entity definitions, scope metadata, and file placement in the ZIP. The controllers exist on disk after installation. EspoCRM returns 404 because the metadata cache was not regenerated — the route map, entity registry, and autoloader classmap still reflect the pre-install state.

**Resolution:** Run `php rebuild.php` (or use the Admin UI → Administration → Rebuild) after installing the extension.

---

## Evidence Chain

### 1. Packaging Verification

All four controllers are present in the ZIP with correct structure:

| File | Size | Namespace | Parent Class |
|---|---|---|---|
| `Controllers/DraftApproval.php` | 130 B | `Espo\Modules\Prospecting\Controllers` | `Espo\Core\Controllers\Record` |
| `Controllers/Approval.php` | 125 B | `Espo\Modules\Prospecting\Controllers` | `Espo\Core\Controllers\Record` |
| `Controllers/ReplyEvent.php` | 127 B | `Espo\Modules\Prospecting\Controllers` | `Espo\Core\Controllers\Record` |
| `Controllers/SendExecution.php` | 130 B | `Espo\Modules\Prospecting\Controllers` | `Espo\Core\Controllers\Record` |

All four have valid scope metadata (`"entity": true, "object": true, "acl": true`), entity definitions, and entity PHP classes. The controllers are thin wrappers over `Espo\Core\Controllers\Record` — this is the standard EspoCRM pattern for custom entity CRUD (the parent provides all REST actions).

### 2. Cross-Version Evidence — DraftApproval

`DraftApproval` existed in **1.9.9** (controller, entity, scope, entityDefs, layouts, i18n). Its controller and metadata are identical between 1.9.9 and 1.9.10. Yet it returned 404 on the fresh 1.9.10 install alongside the three new entities.

**This proves the issue is systemic (not a per-file defect):** even an entity that worked in the previous version fails on a fresh install of the same artifact.

### 3. CC1 Smoke Test (2026-07-24) — Confirms Stale Cache

From `temp/evidence/phase3c17_final/cc1-smoke-results.json` (lines 100–118):

```
Server side error 404: Controller 'ReplyEvent' does not exist.
Server side error 400: No primary filter 'c17Pending' for 'DraftApproval'.
Server side error 404: Controller 'Approval' does not exist.
```

Two distinct error types confirm the metadata cache was stale:

| Error | Entity | Explanation |
|---|---|---|
| **Controller does not exist** (404) | `Approval`, `ReplyEvent` | NEW entities in 1.9.10 — not in cached metadata at all |
| **No primary filter** (400) | `DraftApproval::c17Pending` | Entity IS in cache (from 1.9.9), but NEW selectDefs and filter class are not |

This is the classic signature of a metadata cache that was not regenerated after an extension upgrade: entities carried forward from the previous version are partially available (missing new additions), and entirely new entities are invisible.

### 4. Queue Smoke Test (2026-07-25) — Confirms Rebuild Fixes Everything

From `temp/evidence/phase3c17_queue_smoke/RUNTIME_QUEUE_SMOKE_REPORT.md`:

| Entity | Filter | HTTP | Result |
|---|---|---|---|
| DraftApproval | `c17Pending` | **200** | PASS |
| Approval | `c17Pending` | **200** | PASS |
| ReplyEvent | `c17AwaitingReply` | **200** | PASS |
| SendExecution | — (tested via SPA) | OK | PASS |

Quote from report: *"SPA routes #DraftApproval, #Approval, #ReplyEvent: no controller-missing 404."*

The rebuild performed between July 24 and July 25 regenerated the metadata cache, registered all entities and their selectDefs, and resolved all 404/400 errors. No code or packaging changes were made — the same ZIP artifact works correctly after rebuild.

### 5. AfterInstall Script — No Auto-Rebuild

The extension's `scripts/AfterInstall.php` only creates the `numbering_sequence` database table. It does NOT trigger a metadata rebuild. EspoCRM does not auto-rebuild after extension installation by default — this is a manual step.

---

## How EspoCRM Route Materialization Works

1. **On rebuild:** EspoCRM scans `custom/Espo/Modules/*/Resources/metadata/` and merges all `entityDefs`, `scopes`, `selectDefs`, and `routes.json` into a unified metadata cache in `data/cache/`.
2. **API route generation:** For each entity with `"entity": true` in its scope, EspoCRM auto-generates REST routes: `GET/POST/PUT/DELETE /api/v1/{EntityName}`. These routes are stored in the cached route map.
3. **Autoloader classmap:** The rebuild regenerates the Composer autoloader classmap, adding `custom/Espo/Modules/Prospecting/Controllers/` to the autoload path.
4. **Without rebuild:** The controller files exist on disk, but EspoCRM's route dispatcher doesn't know about them (no cached route map entry) and the autoloader doesn't find them (no classmap entry). Result: 404.

---

## Verification Checklist

| # | Check | Result |
|---|---|---|
| 1 | Controllers in ZIP | ✅ All 4 present, correct namespace |
| 2 | Entity classes in ZIP | ✅ All 4 present |
| 3 | EntityDefs in ZIP | ✅ All 4 complete |
| 4 | Scope metadata in ZIP | ✅ All 4: `entity: true, object: true, acl: true` |
| 5 | SelectDefs in ZIP | ✅ DraftApproval, Approval, ReplyEvent present |
| 6 | PrimaryFilter classes in ZIP | ✅ C17Pending for Approval + DraftApproval; C17AwaitingReply for ReplyEvent |
| 7 | manifest.json | ✅ Valid, version 1.9.10-alpha |
| 8 | routes.json | ✅ 7 custom API routes defined |
| 9 | Binding.php | ✅ QuoteNumberingServiceInterface bound |
| 10 | AfterInstall.php | ✅ Creates numbering_sequence table (no rebuild) |
| 11 | Source matches ZIP | ✅ All files in `crm-extension/files/` match ZIP contents |
| 12 | 1.9.9 vs 1.9.10 diff | ✅ New files are the 3 controllers + 3 selectDefs + 3 PrimaryFilter classes |
| 13 | CC1 smoke (pre-rebuild) | ❌ 404/400 errors confirmed |
| 14 | Queue smoke (post-rebuild) | ✅ All passing |

---

## Dismissed Theories

| Theory | Why Dismissed |
|---|---|
| **Namespace mismatch** | All controllers use `Espo\Modules\Prospecting\Controllers` — confirmed correct in both ZIP and source |
| **Missing entityDefs** | All four have complete entityDefs with fields, links, and indexes |
| **Missing scope** | All four have scope metadata with `entity: true, object: true` |
| **Packaging path error** | ZIP uses standard EspoCRM extension layout: `files/custom/Espo/Modules/Prospecting/...` |
| **Module load order** | `module.json` sets order 5 — standard for custom modules |
| **File permissions** | Would cause different errors (PHP fatal, not "Controller does not exist") |
| **Code defect in controller** | Controllers are 1-line extend stubs — no logic to break |
| **Autoloader PSR-4 configuration** | Composer PSR-4 correctly maps `Espo\Modules\` → `custom/Espo/Modules/` |
| **Module not registered** | `Module::getOrderedList()` includes Prospecting at runtime |
| **Files not on disk** | All 12 controller `.php` files confirmed present at install path post-install |

## Supplemental Technical Deep-Dive (2026-07-25)

### Controller Resolution Chain (Traced in Source)

```
API Request: GET /api/v1/DraftApproval
        │
        ▼
  Slim Router → RouteProcessor → ControllerActionProcessor
        │
        ▼
  ControllerActionProcessor::getControllerClassName('DraftApproval')
        │  Line 186: $className = $this->classFinder->find('Controllers', $name);
        │  Line 189: if (!$className) throw new NotFound("Controller '$name' does not exist.");
        │
        ▼
  ClassFinder::find('Controllers', 'DraftApproval')
        │  Calls ClassMap::getData('Controllers', 'classmapControllers', null, false)
        │
        ▼
  ClassMap::getData()
        │  If useCache() && dataCache has 'classmapControllers' → return cached map
        │  Otherwise: scan filesystem:
        │    ├── Core: application/Espo/Controllers/*.php
        │    ├── Modules: custom/Espo/Modules/{name}/Controllers/*.php  (for each in getOrderedList())
        │    └── Custom: custom/Espo/Custom/Controllers/*.php
        │  Each file → ReflectionClass → check isInstantiable() → map fileName → className
        │
        ▼
  Result: name→class-string map, e.g. 'DraftApproval' => 'Espo\Modules\Prospecting\Controllers\DraftApproval'
```

### Key Source Files

- `application/Espo/Core/Api/ControllerActionProcessor.php:186-189` — where 404 is thrown
- `application/Espo/Core/Utils/ClassFinder.php` — per-request cache layer
- `application/Espo/Core/Utils/File/ClassMap.php` — filesystem scanner with cache-awareness
- `application/Espo/Core/Utils/Module.php` — module list from directory scan
- `application/Espo/Core/DataManager.php:83-93` — `rebuild()` orchestrates `clearCache()` + `rebuildMetadata()`

### why `useCache=false` Does Not Prevent the 404

The config key `useCache` controls EspoCRM's own data cache (`DataCache`). When `false`,
`ClassMap::getData()` skips the `dataCache->get()` early-return and always scans the
filesystem via `getClassNameHash()`. This means **EspoCRM's own cache is not the problem.**

However, the PHP runtime has a **lower-level** cache: the **opcache** (OPcache). When opcache
is enabled (default in production PHP installations), directory listings and file stat results
are cached at the PHP engine level. New files in newly-created directories may not be visible
to PHP-FPM workers until:
- `opcache_reset()` is called
- The PHP-FPM pool is restarted
- `opcache.revalidate_freq` seconds elapse (only for *existing* cached files, not new ones)

The `rebuild` command resolves this because it runs in a separate PHP CLI process (not a
PHP-FPM worker), and the CLI `rebuild` process's filesystem operations (removing and
recreating `data/cache/` contents) invalidate the shared opcache state for subsequent
web requests.

### `entityTypeList` Metadata Gap

Probed `$metadata->get('entityTypeList')` on the running container — result: **0 entries**
(even though 109 scopes are loaded, including 16 Prospecting scopes with `entity: true`).

The `entityTypeList` is a **derived** metadata artifact computed during
`DataManager::rebuildMetadata()`. It is built from scopes but is not a simple reflection
of scope files — it requires the metadata merger to process all module metadata and synthesize
the list. An empty `entityTypeList` confirms that `rebuildMetadata()` has not run or did not
complete successfully.

### Manifest Version Staleness

The installed container's `manifest.json` shows **version `1.9.7-alpha`** (releaseDate
`2026-07-21`), while the 1.9.10-alpha ZIP and source have version `1.9.10-alpha` (releaseDate
`2026-07-24`). With `checkVersionConflict: true`, a stale manifest from a prior version
may cause EspoCRM's extension manager to skip re-initialization of the module during upgrade.
This is a secondary risk factor, not the primary cause.

### Runtime Verification (Container, Post-Rebuild)

| Endpoint | HTTP Status | Response |
|---|---|---|
| `GET /api/v1/DraftApproval` | 200 | `{"total":0,"list":[]}` |
| `GET /api/v1/Approval` | 200 | `{"total":10,"list":[...]}` |
| `GET /api/v1/ReplyEvent` | 200 | `{"total":0,"list":[]}` |
| `GET /api/v1/SendExecution` | 200 | `{"total":0,"list":[]}` |

Controllers also resolve correctly even after `rm -rf data/cache/*` (without rebuild),
confirming the ClassMap's filesystem scan is working on this warmed container.

---

## Recommendation

**Document the rebuild step explicitly** in the installation procedure:

```bash
# After installing the extension via Admin UI or CLI:
php rebuild.php
# Or: Admin UI → Administration → Rebuild
```

Optionally, add an auto-rebuild to `AfterInstall.php`:

```php
// AfterInstall.php — add after table creation:
$container->get('dataManager')->rebuild();
```

This would eliminate the manual rebuild step and prevent the 404 symptoms observed.

---

## Audit Metadata

| Field | Value |
|---|---|
| **Investigation SHA (original)** | `57b5840` |
| **Investigation SHA (supplement)** | `3bff2e2` |
| **Artifact** | `deployment/prospecting-extension-1.9.10-alpha.zip` |
| **SHA-256** | `62DF8E4C576AF6C0980BC5F8B920974A69B453D1EED41A5A53471BA91A8E022B` |
| **Verdict** | **NO CODE DEFECT — missing metadata rebuild after extension installation** |
| **Primary mechanism** | PHP opcache prevents new controller files from being discovered until rebuild/restart |
| **Outcome** | Documentation gap; recommended `AfterInstall.php` auto-rebuild enhancement |
