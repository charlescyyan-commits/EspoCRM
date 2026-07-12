# Phase3B03 — Release Artifact

**Date:** 2026-07-12  
**Workspace:** `D:\EspoCRM-Production`  
**Phase:** Phase3B03.1 Release Package Finalization

---

## 1. Release Version

| Field | Value |
|---|---|
| Extension name | Chitu Prospecting Integration |
| Version | **1.3.1-alpha** |
| Release date (manifest) | 2026-07-12 |
| Description | Chitu Prospecting CRM connector sync layer for EspoCRM |

---

## 2. Package Location

| Field | Value |
|---|---|
| Filename | `prospecting-extension-1.3.1-alpha.zip` |
| Path | `D:\EspoCRM-Production\deployment\prospecting-extension-1.3.1-alpha.zip` |
| Size | **20262** bytes |
| Created / LastWriteTime | **2026-07-12 21:09:17** (local) |
| Build method | `crm-extension/scripts/build_release_package.ps1` (manifest + `files/` only) |

---

## 3. Manifest Verification

| Check | Value | Result |
|---|---|---|
| `crm-extension/manifest.json` version | `1.3.1-alpha` | PASS |
| ZIP `manifest.json` version | `1.3.1-alpha` | PASS |
| Source ↔ ZIP consistency | identical version string | **PASS** |

ZIP manifest excerpt:

```json
{
  "name": "Chitu Prospecting Integration",
  "extensionName": "Chitu Prospecting Integration",
  "version": "1.3.1-alpha",
  "acceptableVersions": [">=7.4.0"],
  "php": [">=8.1"],
  "releaseDate": "2026-07-12"
}
```

---

## 4. SHA256

| Field | Value |
|---|---|
| Algorithm | SHA256 |
| Hash | `BD6D4CDB3F36DC3E77108C52F48795E8DD5E0E31B3F5619FDB570FF1B4845354` |
| Filename | `prospecting-extension-1.3.1-alpha.zip` |
| Size | 20262 bytes |
| Created time | 2026-07-12 21:09:17 |

---

## 5. Included Files Summary

**Entry count:** 33  

**Included categories:**

- `manifest.json`
- Workflow: `files/custom/Espo/Custom/Hooks/Lead/LeadWorkflowHook.php`
- Connector sync API: `PostSyncLead.php`, `PostSyncEvidence.php`, `PostSyncOpportunityProposal.php`
- Sync service: `Services/ChituSyncService.php`
- Routes: `Resources/routes.json`
- EntityDefs: Lead, Opportunity, ResearchEvidence
- Layouts: Lead (detail/list), Opportunity (detail), ResearchEvidence (detail/list)
- Metadata: aclDefs, app/layouts, clientDefs, formula, scopes, selectDefs
- i18n (en_US): Lead, Opportunity, ResearchEvidence
- Filters / controllers / entities / module.json

**Excluded by build (not packaged):**

- Tests
- Temporary / debug files
- Secrets / `.env`
- Local cache / `__pycache__`
- Source trees outside `manifest.json` + `files/`

**Forbidden-pattern scan inside ZIP:** 0 hits for test/debug/temp/secret/cache payloads.

---

**Artifact recorded for Phase3B03.1 baseline. No Phase3B04 work.**
