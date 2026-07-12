# EspoCRM Prospecting Extension Structure Audit Report

**Date:** 2026-07-11  
**Scope:** Read-only audit of live EspoCRM container `espocrm`  
**Target paths:** `custom/Espo/Modules/Prospecting/`, `custom/Espo/Custom/`  
**Actions performed:** inspect / compare only  
**Fixes / rebuild / metadata edits:** NONE

## Summary

| Question | Answer |
|---|---|
| ResearchEvidence roughly matches EspoCRM custom-entity pattern? | **MOSTLY YES** (scopes / entityDefs / clientDefs / Entity / Controller present) |
| Duplicate overlay `Custom/` vs `Modules/Prospecting/`? | **YES** |
| Future upgrade risk? | **YES — medium** (dual ownership + classmap prefers Custom) |
| Non-standard `aclDefs`? | **YES** |

## 1. Module Tree — `custom/Espo/Modules/Prospecting/`

Present directories/files:

```text
Prospecting/
├── Api/README.md                          (placeholder only)
├── Controllers/
│   ├── README.md
│   └── ResearchEvidence.php
├── Entities/
│   └── ResearchEvidence.php
├── Services/README.md                     (placeholder only)
└── Resources/
    ├── module.json                        ({ "order": 25 })
    ├── i18n/en_US/{Lead,ResearchEvidence}.json
    ├── layouts/ResearchEvidence/{detail,list}.json
    └── metadata/
        ├── aclDefs/ResearchEvidence.json
        ├── clientDefs/ResearchEvidence.json
        ├── entityDefs/{Lead,ResearchEvidence}.json
        └── scopes/ResearchEvidence.json
```

### Missing relative to common EspoCRM extension patterns

| Item | Status |
|---|---|
| `Resources/metadata/relationships/` | **ABSENT** |
| Dedicated relationship metadata file | Not required if links are declared in `entityDefs` (current approach) |
| `Services/ResearchEvidence.php` | Absent (OK — default Record service) |
| Installable package scripts | Out of scope for this live-tree audit |

## 2. ResearchEvidence — EspoCRM Standard Checklist

| Required piece | Module path | Status |
|---|---|---|
| Entity PHP | `Entities/ResearchEvidence.php` (`Espo\Modules\Prospecting\Entities`) | Present |
| Controller PHP | `Controllers/ResearchEvidence.php` extends `Record` | Present |
| `scopes/*.json` with `entity/object/acl/tab` | Present; includes `"module": "Prospecting"` | Present |
| `entityDefs/*.json` fields/links/collection/indexes | Present | Present |
| `clientDefs/*.json` | `controller: controllers/record` | Present |
| Layouts | detail + list | Present |
| i18n | en_US | Present |
| `module.json` order | `25` (> Crm `10`) | Present |
| `aclDefs` | Present but **non-standard content** | See §5 |
| `relationships/` metadata | Absent | Acceptable if links live in entityDefs |

### Scope flags (Module)

```json
{
  "entity": true,
  "object": true,
  "tab": true,
  "acl": true,
  "customizable": false,
  "importable": false,
  "module": "Prospecting",
  "type": "Base",
  "statusField": null
}
```

These flags match EspoCRM custom-entity guidance.

### Entity / link model (Module)

- Fields include contract-aligned `pe*` evidence fields plus standard `name`, audit, `assignedUser`, `teams`.
- Links: `lead` (`belongsTo` Lead), user/team links.
- Lead overlay adds `researchEvidences` (`hasMany` ResearchEvidence).

**Verdict:** Core ResearchEvidence shape is extension-standard enough to operate. Main deviations are duplicate Custom overlay and malformed `aclDefs`.

## 3. Duplicate Overlay — `custom/Espo/Custom/` vs Module

### Duplicate files found

| Artifact | Modules/Prospecting | Custom |
|---|---|---|
| `Entities/ResearchEvidence.php` | YES (`Espo\Modules\Prospecting\Entities`) | YES (`Espo\Custom\Entities`) |
| `Controllers/ResearchEvidence.php` | YES | YES |
| `metadata/scopes/ResearchEvidence.json` | YES | YES |
| `metadata/entityDefs/ResearchEvidence.json` | YES | YES |
| `metadata/entityDefs/Lead.json` | YES | YES |
| `metadata/clientDefs/ResearchEvidence.json` | YES (identical) | YES (identical) |
| `metadata/aclDefs/ResearchEvidence.json` | YES | **NO** |
| layouts / i18n | YES | **NO** |

### Effective runtime winner (classmap cache)

| Map | Resolved class |
|---|---|
| Entity | `Espo\Custom\Entities\ResearchEvidence` |
| Controller | `Espo\Custom\Controllers\ResearchEvidence` |

EspoCRM loads **Custom after modules**, so Custom PHP classes win. Metadata is merged recursively; Custom scope/entityDefs overlay Module definitions.

### Drift between copies

| File pair | Identical bytes? | Notes |
|---|---|---|
| ResearchEvidence clientDefs | YES | Same content |
| ResearchEvidence scopes | NO | Module has `module` + `statusField`; Custom omits `module` |
| ResearchEvidence entityDefs | NO | Same field/link names; field param details differ (e.g. tooltips/views) |
| Lead entityDefs | NO | Same keys; Module includes tooltip flags Custom lacks |

**Duplicate overlay: YES.**

## 4. Future Upgrade Risks

| Risk | Severity | Why |
|---|---|---|
| Dual ownership of same entity | Medium | Module package updates can be silently overridden by Custom copies |
| Classmap pinned to Custom | Medium | Uninstalling/replacing only the module may leave Custom classes active |
| Metadata drift | Medium | Two Lead/ResearchEvidence defs already differ; future edits may diverge further |
| Admin UI writes land in Custom | Medium | Entity Manager / UI customizations typically write under `Espo\Custom`, amplifying split-brain |
| Missing `relationships/` dir | Low | Current link defs in entityDefs work; complex many-to-many later may need explicit relationship metadata |
| Non-standard aclDefs | Low–Medium | Unlikely to drive Role scope list (scopes.acl does), but can confuse ACL tooling / future checkers |
| Placeholder Api/Services READMEs | Low | Fine for skeleton; must not be mistaken for implemented sync API |

## 5. Non-Standard `aclDefs`

Module file:

`Resources/metadata/aclDefs/ResearchEvidence.json`

```json
{
  "Prospecting": {
    "ResearchEvidence": true
  }
}
```

### Why this is non-standard

EspoCRM `metadata > aclDefs > {Scope}` is documented for **access-control parameters** of that scope, e.g.:

- `accessCheckerClassName`
- `ownershipCheckerClassName`
- `linkCheckerClassNameMap`
- portal/account/contact link helpers

It is **not** a nested `{ModuleName: {EntityName: true}}` registry.

Core examples (e.g. Email/Account aclDefs) use checker class names and ACL parameters — not module membership flags.

`entityAcl` (separate metadata family) is where field/link readOnly/forbidden flags belong.

**Non-standard aclDefs: YES.**  
Observed impact so far: Role ACL still lists ResearchEvidence via `scopes.acl=true` (separate mechanism). This file should be treated as a known defect for a later cleanup task, not as proof ACL is undefined.

## 6. Relationships Metadata

| Location | Result |
|---|---|
| `Modules/Prospecting/Resources/metadata/relationships/` | Does not exist |
| `Custom/Resources/metadata/relationships/` | Does not exist |

Lead ↔ ResearchEvidence is declared only via `entityDefs` links (`lead` / `researchEvidences`). That is a valid EspoCRM pattern for simple belongsTo/hasMany.

## 7. Controllers / Entities

| Class | Namespace | Extends | Notes |
|---|---|---|---|
| Module Entity | `Espo\Modules\Prospecting\Entities\ResearchEvidence` | `Espo\Core\ORM\Entity` | Standard thin entity |
| Module Controller | `Espo\Modules\Prospecting\Controllers\ResearchEvidence` | `Record` | Standard |
| Custom Entity | `Espo\Custom\Entities\ResearchEvidence` | `Entity` | Duplicate; **runtime winner** |
| Custom Controller | `Espo\Custom\Controllers\ResearchEvidence` | `Record` | Duplicate; **runtime winner** |

## 8. Audit Conclusions (no fixes applied)

1. **ResearchEvidence is largely extension-standard** in the Prospecting module (scopes, entityDefs, clientDefs, layouts, i18n, Entity, Controller).
2. **Duplicate overlay exists** under `custom/Espo/Custom/` for the same entity and Lead field overlay; runtime PHP resolves to **Custom**.
3. **Upgrade risk is real** because package/module updates can be masked by Custom copies and already-diverging JSON.
4. **`aclDefs/ResearchEvidence.json` is non-standard** and should be corrected in a future authorized cleanup (not in this audit).

## 9. Recommended Follow-ups (documentation only — not executed)

1. Choose a single ownership model: Module-only **or** Custom-only for ResearchEvidence.
2. Remove or stop maintaining the losing duplicate set after an explicit migration plan.
3. Replace non-standard `aclDefs` with either an empty/default object or real checker parameters; use `entityAcl` for field restrictions if needed.
4. Keep Lead↔Evidence links in entityDefs unless a formal `relationships/` definition becomes necessary.

No files were modified by this audit.
