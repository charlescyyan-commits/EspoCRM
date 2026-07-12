# Phase3A32 — EspoCRM Production Preparation Report

**Date:** 2026-07-11  
**Scope:** Production preparation and isolated rehearsal only. **No production deployment was performed.**

## Readiness Verdict

**CONDITIONAL — extension package and clean-environment installation pass; production deployment is blocked pending ACL hardening, sales-role configuration, and a production Compose/bootstrap rehearsal.**

## Packaging Review

### Core Boundary

| Check | Result |
|---|---|
| EspoCRM core files modified | PASS — no core source exists in this repository; core-protection test passes |
| Customization location | PASS — installable content is under `files/custom/Espo/Modules/Prospecting/` |
| Package manifest | PASS — `manifest.json` is at ZIP root and declares EspoCRM `>=7.4.0`, PHP `>=8.1` |
| Non-installable files in archive | PASS — archive contains only `manifest.json` and `files/` |
| Extension hooks | PASS — none shipped; no install/uninstall script can execute custom behavior |

Added `espocrm_extension/scripts/build_release_package.ps1` as the repeatable package command:

```powershell
.\espocrm_extension\scripts\build_release_package.ps1 -OutputPath .\chitu-prospecting-integration.zip
```

The builder deliberately emits ZIP-standard forward-slash entry names. The initial Windows `Compress-Archive` rehearsal exposed backslash entries: EspoCRM recorded the extension but did not copy its payload. The builder was corrected and the final package has 25 entries, only under the permitted roots.

Verified package SHA-256:

```text
735661E34530AB9483E70E3FD1D964F9D6D25AFB5192D74CB40E06B40935E00C
```

## Migration Policy

There are no SQL, migration, or upgrade artifacts in the extension. The extension uses EspoCRM entity metadata and the native rebuild process to create/update its custom columns.

The regression suite enforces this with `test_no_database_migration_artifacts`. Deployment therefore requires a tested database backup and `bin/command rebuild`; schema change is not an unmanaged SQL operation.

## Backup And Rollback Runbook

Perform these actions during a maintenance window, after pausing the Chitu integration worker and confirming no sync is in flight.

### Backup

1. Create a consistent database backup:

   ```bash
   mysqldump --single-transaction --routines --events --triggers --databases espocrm > espocrm-pre-extension.sql
   sha256sum espocrm-pre-extension.sql > espocrm-pre-extension.sql.sha256
   ```

2. Archive EspoCRM persistent customization and data directories, including `custom/`, `client/custom/`, `data/`, and the active `data/config.php`.
3. Retain the exact extension ZIP and its SHA-256 alongside the database/application backup.
4. Export or screenshot the production role assignments, dashboard templates, integration-user details, and scheduled-job configuration.
5. Test a restore of the database backup in an isolated environment before production installation.

### Rollback

1. Pause Chitu sync and revoke/disable the integration API key for the rollback window.
2. If the release must be removed before database restoration, run:

   ```bash
   php bin/command extension -u --name="Chitu Prospecting Integration"
   ```

3. Restore the database dump and the archived `custom/`, `client/custom/`, and `data/` directories as one consistent snapshot.
4. Run `php bin/command rebuild` and `php bin/command clear-cache`.
5. Verify login, Lead, Opportunity, ACL, and one read-only API query before re-enabling Chitu sync.

Database restoration is the authoritative rollback for metadata-created columns and records. Do not attempt manual column deletion.

## Production ACL Review

### Observed Local Baseline

| Principal | Result |
|---|---|
| `admin` | PASS — native `admin` user type; no role assignment required |
| `chitu_ai_connector` | WARN — API user with `Chitu Integration Role`; it currently has `create/read/edit/delete=all` for Lead, Account, Contact, Opportunity, Task, ResearchEvidence, Note, Call, Meeting, and Email |
| `api_test` | BLOCKER — only regular user and it has no sales role assigned |

The current integration role is not least privilege. In particular, `Email` access and broad delete permissions conflict with the display-only email lifecycle boundary.

### Required Production Policy

Before deployment, create and test a dedicated production integration role:

- Allow only the entity operations needed by the approved sync contract.
- Remove `Email`, SMTP/provider configuration, and activity execution access.
- Remove delete permission unless a separately approved rollback workflow requires it.
- Keep CRM-owned sales fields, owner/team assignment, sales stage, amount, close date, activities, and sales progress out of Chitu update bodies.

Create at least one Sales User role before production:

- Lead, Account, Contact, Opportunity, and Task visibility limited to the user/team scope required by sales operations.
- Native dashboard dashlets must be checked under this role, not only as `admin`.
- Keep ResearchEvidence access limited to the intended sales/audit audience.

## Clean Migration Rehearsal

The final rehearsal used disposable containers only:

- EspoCRM `10.0.1`
- MariaDB `11.4`
- a new Docker network and empty database
- the generated extension ZIP

Result:

| Check | Result |
|---|---|
| Native clean database bootstrap | PASS |
| Native CLI package install | PASS — `Chitu Prospecting Integration` `1.0.0-alpha` listed as installed |
| Prospecting module payload copied | PASS |
| Opportunity metadata fields | PASS — all four Opportunity workflow fields and four email lifecycle fields present |
| Email-status enum | PASS — `NONE`, `DRAFT_READY`, `APPROVED`, `SENT`, `REPLIED`, `BOUNCED` |
| Clean database columns | PASS — `pe_email_status`, `pe_last_email_date`, `pe_email_campaign_name`, `pe_email_reply_status` |
| Cleanup | PASS — disposable CRM, database, and network removed |

The direct image entrypoint attempts in this ad-hoc Docker harness exited during initial install without emitting the hidden rebuild error, while the equivalent native bootstrap commands completed successfully. Treat this as a production-environment rehearsal requirement: validate the real Compose/volume/bootstrap configuration and capture startup logs before authorizing production deployment.

## Validation

```text
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client tests.test_espocrm_lifecycle_sync tests.test_espocrm_email_lifecycle -v
```

Result: **PASS — 54 tests**.

This includes core-boundary checks, no unmanaged migration artifacts, Lead sync, native Opportunity lifecycle sync, and email lifecycle no-send coverage. The existing local `espocrm`, `espocrm-db`, and `espocrm-daemon` containers remained healthy throughout the preparation work.

## Files Changed

- `D:\Chitu-intelligence\espocrm_extension\scripts\build_release_package.ps1`
- `D:\Chitu-intelligence\docs\espocrm-extension\PHASE3A32_PRODUCTION_PREPARATION_REPORT.md`

Temporary ZIPs, clean-environment containers, databases, networks, and diagnostic scripts were removed after rehearsal.
