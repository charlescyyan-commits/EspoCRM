# EspoCRM Extension Install Guide V1

**Extension:** Chitu Prospecting Integration  
**Version:** `1.0.0-alpha`  
**Phase:** 3A-2.1 skeleton

## What Belongs to This Extension

Only files under `espocrm_extension/` are part of the extension package.

| Path | Purpose |
|---|---|
| `manifest.json` | Extension identity and EspoCRM version constraints |
| `files/custom/Espo/Modules/Prospecting/` | Installable module content copied into EspoCRM |
| `Resources/` | Design-surface metadata copies for review/tests |
| `custom/Espo/Modules/Prospecting/` | Placeholder Controllers/Services/Api READMEs |
| `application/` | Reserved placeholder — **not** copied into EspoCRM |
| `scripts/` | Future install hooks (empty in V1) |
| `tests/` | Offline skeleton validation |
| `docs/` | Extension-local notes |

Not part of the extension:

- `app/`
- `prospecting_engine/`
- `revenue_system/`
- Any live EspoCRM installation directory
- Any database

## Packaging (offline)

From `espocrm_extension/`, create a ZIP that contains:

```text
manifest.json
files/
scripts/          # optional; empty README only in V1
```

Example (PowerShell):

```powershell
cd D:\Chitu-intelligence\espocrm_extension
Compress-Archive -Path manifest.json, files, scripts -DestinationPath ..\build\chitu-prospecting-integration-1.0.0-alpha.zip -Force
```

Do not include `Resources/`, `custom/`, `application/`, `tests/`, or `docs/` in the install ZIP unless you intentionally want them on the CRM host. EspoCRM only installs `files/` contents.

## How to Install for Testing

Prerequisites:

- Disposable EspoCRM instance matching `acceptableVersions` (`>=7.4.0`)
- Admin access
- No production CRM

Steps:

1. Build the ZIP as above.
2. In EspoCRM Admin → Extensions, upload the ZIP.
3. Install the extension.
4. Rebuild EspoCRM cache / run Administration rebuild if prompted.
5. Confirm `ResearchEvidence` appears as an entity scope and Lead detail metadata includes `pe*` fields after rebuild.

Phase 3A-2.1 does **not** require connecting this repository to a CRM. Offline tests are sufficient for skeleton acceptance.

## Offline Verification (required for this phase)

From repository root:

```bash
python -m unittest espocrm_extension.tests.test_extension_skeleton -v
```

Expected: all tests PASS. No CRM, database, network, or Engine runtime is used.

## How to Roll Back

If installed on a disposable CRM:

1. Admin → Extensions → uninstall **Chitu Prospecting Integration**.
2. Rebuild cache.
3. Confirm custom module files under `custom/Espo/Modules/Prospecting/` were removed by uninstall.
4. If any admin-created UI customizations remain under `custom/Espo/Custom/`, remove only those created for this test.

Uninstall stops future extension behavior. It does not delete ordinary CRM-owned Lead/Account/Opportunity business records created by users. In Phase 3A-2.1 no sync exists, so no Engine-imported records should be present.

## Safety Rules

- Do not install on production.
- Do not run SQL migrations by hand.
- Do not modify EspoCRM core under `application/Espo/`.
- Do not enable sync endpoints until Phase 3A-2.2 is explicitly authorized.
- Do not create real customer Leads from Engine payloads in this phase.
