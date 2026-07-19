# Install

**Status:** Documented from deployment assets and phase reports  
**Current packaged extension version:** `1.9.6-alpha` (see `crm-extension/manifest.json`)

## Prerequisites

| Requirement | Source |
|-------------|--------|
| EspoCRM `>=7.4.0` | `crm-extension/manifest.json` |
| PHP `>=8.1` | `crm-extension/manifest.json` |
| Disposable/test CRM instance | Phase reports — production install requires explicit approval |
| Admin access | EspoCRM Administration → Extensions |

## Automated Steps

| Step | Tool | Status |
|------|------|--------|
| Build extension ZIP | `crm-extension/scripts/build_release_package.ps1` | **Implemented** |
| Verify package contents | `crm-extension/tests/test_extension_skeleton.py` | **Static Verified** |

### Build Package

```powershell
cd D:\EspoCRM-Production\crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension-1.9.6-alpha.zip
```

ZIP contains only `manifest.json` and `files/` (forward-slash entries). Do not include `Resources/`, `tests/`, or `custom/` placeholders.

## Manual Steps (CRM Host)

1. Upload `deployment/prospecting-extension-<version>.zip` via **Administration → Extensions**.
2. Install and allow EspoCRM rebuild/cache clear when prompted.
3. Confirm module scopes: `ResearchEvidence`, `SearchStrategy`, `SearchJob`, `ProspectPool`, extended `Lead`.
4. Run role provisioning scripts if needed (see below).

## Provisioning Scripts (Manual, Not in ZIP)

Scripts under `deployment/provisioning/` are **not packaged** into the extension ZIP. Run only on approved test instances:

| Script | Purpose |
|--------|---------|
| `phase3b06_provision_workspace_roles.php` | Prospecting workspace roles |
| `phase3c01_provision_acquisition_workspace.php` | Acquisition dashboards |
| `phase3c02_1_provision_acquisition_acl.php` | SearchStrategy / SearchJob / ProspectPool ACL |

**Warning:** `deployment/README.md` states scripts must not run without an approved target.

## Offline Verification (No CRM)

```powershell
cd D:\EspoCRM-Production
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v
```

## Runtime Verification

**TBD — requires runtime verification** on a disposable EspoCRM instance. Historical success documented in [../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md](../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md) for earlier package versions.

## Safety Rules

- Do not install on production without approval.
- Do not hand-run SQL migrations.
- Do not modify EspoCRM core under `application/Espo/`.
- Do not import real customer data without explicit approval.

## Related Documents

- [PACKAGE.md](PACKAGE.md)
- [../phase-reports/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md](../phase-reports/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md) (historical — paths refer to old `espocrm_extension/` name)
