# EspoCRM Production Workspace

This workspace owns the installable **Chitu Prospecting Integration** extension, its isolated EspoCRM connector, deployment artifacts, and CRM documentation. It deliberately excludes the Chitu Intelligence application, scoring engine, AI research runtime, email-generation engine, frontend, backend, and customer/runtime data.

## Current release baseline

- **Extension version:** `1.9.6-alpha`
- **Version authority:** [`crm-extension/manifest.json`](crm-extension/manifest.json)
- **Installable artifact:** `deployment/prospecting-extension-1.9.6-alpha.zip`
- **Platform compatibility:** EspoCRM `>=7.4.0`; PHP `>=8.1`
- **Release status:** alpha / disposable or explicitly approved CRM validation only

The working tree can contain later phase work. A package's manifest and its release notes describe that package; do not assume un-packaged workspace changes are installed.

## Structure

- `crm-extension/` - installable EspoCRM extension source. `files/` is the package root; `Resources/` is the non-installed metadata/design mirror; `tests/` validates extension contracts.
- `chitu-connector/` - isolated `chitu_connector` package and vendored stable interfaces. It communicates with EspoCRM through the connector contract and must not import the Chitu application tree.
- `deployment/` - versioned extension ZIPs, manual provisioning scripts, and live-validation helpers. No production configuration or credentials are stored here.
- `docs/` - architecture, deployment guidance, release notes, indexes, and immutable historical phase reports.
- `scripts/` - workspace-level operational scripts.

## Extension module structure

The installable Prospecting module is under `crm-extension/files/custom/Espo/Modules/Prospecting/`:

- `Api/`, `Controllers/`, `Services/`, and `Entities/` provide the EspoCRM module surface.
- `Resources/metadata/`, `Resources/layouts/`, and `Resources/i18n/` define native EspoCRM entities, fields, layouts, dashlets, client definitions, and language labels.
- `files/client/custom/src/` and `files/client/custom/res/templates/` provide native EspoCRM client handlers, views, and templates.

Current packaged capabilities include Prospecting workspace UI, SearchStrategy/SearchJob/ProspectPool acquisition surfaces, Lead intelligence and ResearchEvidence display, and the existing CRM sync/workflow boundaries. C10.6 is still in development and is not represented as a released capability in this README.

## Workflow and safety

Use EspoCRM-Test or an approved disposable CRM for validation. Build an extension from `crm-extension` with `crm-extension/scripts/build_release_package.ps1`; run connector tests from `chitu-connector` with Python's `unittest`.

Do not deploy, import customer data, enable outreach, or run provisioning/cleanup scripts without an approved runbook and target. No Chitu Intelligence core code belongs here.

## Documentation

- [Documentation Center](docs/README.md)
- [Release notes index](docs/release/README.md)
- [Installation guide](docs/deployment/INSTALL.md)
- [Version policy](docs/release/VERSION_POLICY.md)
