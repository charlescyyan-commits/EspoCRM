# EspoCRM Production Workspace

This workspace contains the EspoCRM extension, the isolated Chitu connector, deployment operations, and CRM-specific documentation. It deliberately excludes Chitu Intelligence application, scoring, research, email-generation, frontend, backend, and runtime-data code.

## Structure

- `crm-extension/` — installable EspoCRM extension source and extension tests.
- `chitu-connector/` — `chitu_connector` Python package, vendored stable contracts, and connector tests.
- `deployment/` — Railway, Docker, backup, and provisioning operational boundaries.
- `docs/` — CRM architecture, workflow, contract, testing, email-rule, and phase-report documents.
- `scripts/` — workspace-level operational scripts.

## Workflow

Use EspoCRM-Test for local validation. Build the extension from `crm-extension` with `scripts/build_release_package.ps1`; test the connector from `chitu-connector` with `python -m unittest discover -s tests -v`.

Railway is the intended production deployment surface. This repository contains no active deployment configuration or production credentials. Do not deploy, import customer data, or enable full sync without an approved production runbook.

## Boundary

No Chitu Intelligence core code belongs here. Do not add scoring, AI research, email-generation, frontend, backend, raw-data, or customer-data components to this workspace.
