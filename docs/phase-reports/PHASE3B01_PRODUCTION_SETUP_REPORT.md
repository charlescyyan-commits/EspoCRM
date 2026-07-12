# Phase3B01 — Production Environment Setup Report

**Date:** 2026-07-11  
**Scope:** Production environment preparation only. No real customer data import, sales outreach, full sync enablement, Chitu-engine modification, or production deployment was performed.

## Verdict

**BLOCKED BEFORE PRODUCTION CHANGE — no approved production EspoCRM target or production credential is configured in this workspace.**

The only reachable instance is the local test CRM:

```text
http://localhost:8080
EspoCRM 10.0.1
```

The only discovered credential configuration is `ESPOCRM_TEST_API_KEY`. Treating this local test instance or its test credential as production would violate the requested scope, so no role, credential, backup, install, rollback, data, or sync operation was performed against it.

## Production Target Verification

| Required item | Result |
|---|---|
| Production EspoCRM URL | BLOCKED — not configured or provided |
| Production database host/connection | BLOCKED — not configured or provided |
| Approved production administrator access | BLOCKED — not configured or provided |
| Production extension installation path | BLOCKED — depends on the unavailable target/deployment method |
| Production version compatibility | BLOCKED — production version not observable |

Local compatibility evidence only: the release manifest accepts EspoCRM `>=7.4.0` and PHP `>=8.1`; the local test container is EspoCRM `10.0.1`. This is not evidence about a production instance.

## Release Package Preflight

The package was rebuilt locally using the repeatable release builder and inspected without installing it into any production target.

| Check | Result |
|---|---|
| ZIP entry count | PASS — `26` |
| Archive roots | PASS — only `manifest.json` and `files/` |
| ZIP path separators | PASS — forward-slash paths only |
| Current package SHA-256 | `AA777F308E8FCD06362605DF3447EB0CBB4BFBE8BA72697FB3676DF91A862562` |

The local test CRM has no installed extension record. It was not used as a substitute production environment.

## Deferred Production Actions

The following requested actions remain deliberately unperformed until an approved production target is supplied:

| Action | Status |
|---|---|
| Verify production database connection | NOT RUN |
| Install release package | NOT RUN |
| Verify metadata, custom fields, and layouts | NOT RUN |
| Create `Admin`, `Integration Bot`, `Sales User`, `Sales Manager` roles | NOT RUN |
| Create production integration credential | NOT RUN |
| Create database, package, and configuration backups | NOT RUN |
| Execute uninstall/restore rollback test | NOT RUN |
| Login and role-assignment acceptance | NOT RUN |

## Required Inputs Before Pilot Setup

Provide all of the following through the approved production-access channel:

1. Production EspoCRM base URL and deployment type (Docker/Compose, VM, managed hosting, or Kubernetes).
2. Production EspoCRM/PHP version and database platform/version.
3. An approved production administrator session or credential with permission to install extensions and create roles/users.
4. The production backup location, retention policy, and an explicit restoration approval path.
5. The intended Integration Bot user name and least-privilege entity scope.
6. The Sales User and Sales Manager team/ownership policy for Lead, Account, Contact, Opportunity, Task, and dashboard visibility.

## Pilot Execution Plan

After the inputs are available, perform this sequence in the production maintenance window:

1. Verify EspoCRM/PHP/database compatibility and confirm the package SHA-256.
2. Pause Chitu sync, take verified database, extension-package, configuration, and persistent-directory backups.
3. Install the package with native EspoCRM extension CLI/UI and run rebuild/cache clear.
4. Confirm custom Lead, Opportunity, and ResearchEvidence metadata plus native layouts.
5. Create and assign the four approved production roles. Keep the Integration Bot limited to the approved sync fields; remove Email/send/provider and delete permissions unless explicitly required.
6. Generate a new production-only API credential, store it in the approved secret manager, and verify one read-only API request.
7. Run the documented uninstall/restore test against a non-production restore environment, not live production data.
8. Stop before importing any customer data or enabling full synchronization; obtain a separate approval for pilot data and sync activation.

## Files Changed

- `D:\Chitu-intelligence\docs\espocrm-extension\PHASE3B01_PRODUCTION_SETUP_REPORT.md`

Temporary local package validation artifacts were removed. No production environment state was changed.
