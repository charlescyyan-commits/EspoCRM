# Phase OPS01 — Backup and Rollback Drill

**Date:** 2026-07-14  
**Scope:** read-only operational verification for C11 preparation.  
**Conclusion:** **PASS WITH FINDINGS**

No service was stopped, no database was restored, no volume was overwritten, and no business or test data was created, updated, or deleted.

## 1. Backup procedure review

### Retained backup location

`temp/backups/` is intentionally empty after the repository-freeze retention work. The C10.6.1 runtime backup was moved without deletion to:

```text
archive/runtime-backups/phase3c10_6_1-20260714-151113/
```

The backup contains **335 files** and has the expected runtime structure.

| Required material | Evidence | Result |
| --- | --- | --- |
| Database dump | `espocrm.sql`, 25,131,853 bytes; MariaDB dump header present; SHA-256 `B7ED6830E117ED955EE727F514CB837A45DB45220715D422D29AE074E04BD0F2` | PASS |
| Custom extension | `custom/Espo/Modules/Prospecting/` exists; `custom/` contains 184 files | PASS |
| Configuration | `data/config.php`, `data/config-internal.php`, and `data/state.php` all exist | PASS |
| Extension/deployment artifact | `data/upload/extensions/6a54fee0412d79694z` exists, opens as a ZIP with 182 entries, includes `manifest.json` and `files/` | PASS |
| Archive/package identity | Backup extension archive SHA-256 is `927E0BC67E670C66625AB2631AA7B361BCCD3FF20B25D8502E0DF7218CF1C7E4`, matching `archive/deployment/historical-packages/prospecting-extension-1.9.5-alpha.zip` and its recorded checksum | PASS |

The deployment package is currently retained under `archive/deployment/historical-packages/`, not the active `deployment/` directory. This is a recoverable retention location, but release operators must use the archived path explicitly.

## 2. Restore procedure (documented, not executed)

Use this procedure only with change approval and a verified target. It is destructive to the target runtime and is not a replacement for taking a fresh C11 pre-migration snapshot.

1. **Stop application services.** Record the current container IDs, image versions, volume names, extension list, and database schema first. Stop the EspoCRM web, daemon, and cron services; leave the database unavailable to application writers.
2. **Restore the database.** Start only the database service, confirm the intended disposable/approved target, then import `espocrm.sql` through the MariaDB client. Do not import into an unapproved production database. Verify the dump SHA-256 before import.
3. **Restore extension and configuration files.** With application services stopped, restore the backup `custom/` tree to the target custom volume. Restore `data/config.php`, `data/config-internal.php`, and `data/state.php` only after preserving the target's current copies and confirming environment-specific secrets/URLs are still valid. Restore the extension archive from `data/upload/extensions/` or the matching archived package when the target requires package-level recovery.
4. **Start EspoCRM services.** Bring the web, daemon, and cron services back after the database and custom volume restoration complete.
5. **Rebuild.** Run `php command.php rebuild` in the EspoCRM container.
6. **Clear cache.** Run `php command.php clear-cache` in the EspoCRM container.
7. **Verify health.** Confirm Docker health, EspoCRM application availability, installed extension version, critical metadata/schema, and selected read-only UI/API checks. Compare the restored extension and database state to the recorded pre-migration manifest before declaring rollback complete.

## 3. Dry-run and safe validation

Only non-mutating checks were run.

| Check | Result |
| --- | --- |
| Backup directory exists and all required material is readable | PASS |
| SQL dump recomputed SHA-256 matches the retained G03 record | PASS |
| Saved extension archive opens as a valid ZIP | PASS |
| Docker Compose command availability | PASS — `Docker Compose v5.2.0` |
| Database restore-client availability | PASS — MariaDB client `11.4.12` is available in `espocrm-db` |
| EspoCRM recovery commands | PASS — `rebuild` and `clear-cache` are listed by the active EspoCRM CLI |
| Current runtime health | PASS — `espocrm` and `espocrm-daemon` healthy; database healthy; cron running |
| Actual restore/import/volume overlay | NOT RUN — correctly excluded by this no-overwrite drill |

## 4. C11 rollback readiness

### Code rollback

The repository currently has a reachable `v1.9.5-alpha` tag at `d004397b8c8a28baa4cdc33415899860f127c1f3`. The checked C10 runtime paths (`ResearchEvidence.json` and `ChituSyncService.php`) match that tag in the workspace, so a source rollback reference exists.

### Database and extension rollback

The retained runtime backup is usable as a coherent **pre-C10.6.1** recovery set, but it is not a precise C11 pre-migration rollback point:

| Checked path | Backup SHA-256 | Current runtime SHA-256 | Result |
| --- | --- | --- | --- |
| `Resources/metadata/entityDefs/ResearchEvidence.json` | `ed3bb27831e74f09bbbc57eebe0e6be710f53e1ae643e5831e3a5d65a319fbb6` | `bd82314fe76097e8414148951936d7c89923ca34ee95946c17f51f1402c29c31` | different |
| `Services/ChituSyncService.php` | `ae4f9eb39170c14be5a864740eac6a77d524909ded1be4e935a40becd0d25b19` | `0d9acf07cf53d45fed1145f0d30a3c55c99a21ba81a2ca57e4ad2a640466fcc6` | different |

Restoring this backup after a C11 failure would also roll back the C10.6.1 runtime activation, including its ResearchEvidence identity metadata and database state. It is therefore a valid disaster-recovery fallback, not the approved C11 rollback baseline.

## 5. Required finding before C11

Before any C11 database migration or extension activation:

1. Take a new consistent database dump while the current C10.6.1 state is active.
2. Snapshot the current `custom` and required `data` configuration files, plus the exact extension package and its SHA-256.
3. Record container image/version, Compose project/volume names, extension list, and current database schema/index manifest with the backup.
4. Store the snapshot outside `temp/` with a retention record; verify the dump hash and ZIP integrity immediately.
5. Bind the new backup to the planned C11 change identifier before performing the migration.

After those five items, C11 can roll back code, database, and extension files to the exact pre-migration state rather than to the older pre-C10.6.1 state.

## Non-changes

- No business code, Connector, Evidence logic, ACL, role, or workflow was modified.
- No container or service was stopped, started, restored, or overwritten.
- No database command connected for import and no volume restore command was executed.
- No business or synthetic test data was created.
- The only repository artifact created by OPS01 is this report.
