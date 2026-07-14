# Chitu Prospecting Integration - EspoCRM Extension

**Current version:** `1.9.5-alpha`
**Version authority:** [`manifest.json`](manifest.json)
**Compatibility:** EspoCRM `>=7.4.0`, PHP `>=8.1`
**Release posture:** alpha; validate only in a disposable or explicitly approved CRM.

## Purpose

This is the installable EspoCRM **Prospecting** extension. It supplies native EspoCRM metadata and module code for Prospecting workspace UI, acquisition planning, prospect pools, lead intelligence, research evidence, and the existing connector-facing CRM boundaries.

The extension does not contain Chitu scoring, AI research, provider execution, email-generation logic, production credentials, or customer data. The connector remains a separate package under `../chitu-connector/` and imports only its vendored stable interfaces.

## Package layout

```text
crm-extension/
  manifest.json                         # Release version and platform compatibility
  files/                                # Installed ZIP root
    custom/Espo/Modules/Prospecting/
      Api/ Controllers/ Entities/ Services/
      Resources/
        metadata/ layouts/ i18n/
    client/custom/
      src/                               # Native EspoCRM controllers, handlers, and views
      res/templates/                     # Native EspoCRM templates
  Resources/                             # Non-installed metadata/design mirror
  tests/                                 # Offline extension contract tests
  scripts/build_release_package.ps1      # ZIP package builder
```

EspoCRM packages require a lowercase `files/` directory. The ZIP includes `manifest.json` plus `files/`; source mirrors, tests, scripts, and documentation are not included.

## Packaged module areas

- **Prospecting UI:** native scopes, client definitions, layouts, labels, templates, and dashboard dashlets.
- **Acquisition planning:** SearchStrategy, SearchJob, and ProspectPool metadata and supporting module surfaces.
- **CRM intelligence:** native Lead overlays and ResearchEvidence presentation.
- **Connector-facing CRM boundary:** existing sync, feedback, and event endpoints/services; no external provider or outreach execution is embedded here.

## Build and install

```powershell
cd D:\EspoCRM-Production\crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension-1.9.5-alpha.zip
```

Install the ZIP through **Administration > Extensions**, allow EspoCRM to rebuild when prompted, then use the matching release notes and deployment guide for the target version. See [../docs/deployment/INSTALL.md](../docs/deployment/INSTALL.md).

## Validation

```powershell
cd D:\EspoCRM-Production
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v
```

These tests are offline checks; they do not substitute for approved runtime validation. C10.6 remains development work and is not asserted as shipped by this release README.

## Related documentation

- [Documentation Center](../docs/README.md)
- [Release notes](../docs/release/README.md)
- [Package build](../docs/deployment/PACKAGE.md)
- [Upgrade](../docs/deployment/UPGRADE.md)
