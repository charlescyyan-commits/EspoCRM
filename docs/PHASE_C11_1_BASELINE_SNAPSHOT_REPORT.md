# Phase C11.1 — Baseline Snapshot Report

**Created:** 2026-07-14T09:44:09Z  
**Result:** **PASS**  
**Mode:** backup creation only. No restore, runtime overwrite, database import, metadata rebuild, business-data creation, or code change was performed.

## Snapshot location

```text
archive/runtime-backups/c11_1_baseline-20260714T094409Z/
archive/runtime-backups/c11_1_baseline-20260714T094409Z.zip
archive/runtime-backups/c11_1_baseline-20260714T094409Z.zip.sha256
```

The snapshot is stored outside `temp/` for C11 rollback retention.

## Contents

| Area | Snapshot material | Verification |
|---|---|---|
| Database | `database/espocrm.sql` MariaDB logical dump | Non-empty; MariaDB dump header present |
| Application | `application/custom/` runtime custom extension tree | 184 files copied |
| Configuration | `application/config.php`, `config-internal.php`, `state.php` | All three present |
| Installed extension | `application/installed-extension-6a54fee0412d79694.zip` | Current installed `Chitu Prospecting Integration` archive retained |
| Deployment package | `deployment/v1.9.5-alpha.zip` and its SHA-256 sidecar | Package manifest is `1.9.5-alpha` |
| Metadata | Workspace manifest, runtime extension list, Docker state, `SHA256SUMS.txt` | Installed version recorded as `1.9.5-alpha` |
| Archive | Timestamped snapshot ZIP plus adjacent SHA-256 sidecar | 215 archive entries; required materials present |

Runtime state recorded at capture time:

- `espocrm` and `espocrm-daemon`: healthy
- `espocrm-db`: healthy
- EspoCRM image: `espocrm/espocrm:10.0.1`
- Installed extension: `Chitu Prospecting Integration` `1.9.5-alpha`

## Integrity hashes

| Material | SHA-256 |
|---|---|
| MariaDB dump | `EFCEA31E7337E0BAE47849E84B7767DE3138A9959E666F3EF78F684F3E37DC43` |
| Release package `v1.9.5-alpha.zip` | `09E2E4E3543E3583A74672B69E4CEC2059EE39186784DD31456BDC59E6B4D1B2` |
| Snapshot archive | `785401975B96DB982E3FB41C7A6D09714F1823886F660ED8E4C9389FB81CE95A` |

The database/package/configuration hash inventory is retained in:

```text
archive/runtime-backups/c11_1_baseline-20260714T094409Z/metadata/SHA256SUMS.txt
```

## Verification result

| Check | Result |
|---|---|
| Host recomputed database dump hash equals capture hash | PASS |
| Database dump header is valid MariaDB dump text | PASS |
| Package SHA-256 matches package sidecar | PASS |
| Package manifest version | PASS — `1.9.5-alpha` |
| Workspace/package manifest versions match | PASS |
| Archive SHA-256 matches adjacent sidecar | PASS |
| Required snapshot entries present | PASS — 0 missing |
| Application custom extension files | PASS — 184 files |
| Required configuration files present | PASS |

## Restore procedure (documented only — not executed)

Restore requires explicit change approval and an approved target runtime. It is destructive to that target.

1. Verify the three hashes above and preserve the target's current database, `custom/`, and configuration before changing anything.
2. Stop the target EspoCRM web, daemon, and cron services; ensure application writers cannot reach the target database.
3. Restore `database/espocrm.sql` into the approved target MariaDB instance only.
4. Restore the snapshot `application/custom/` tree and the three configuration files, after checking environment-specific settings and secrets.
5. Install or restore the matching `deployment/v1.9.5-alpha.zip` package when package-level recovery is required.
6. Start the application services, run the approved EspoCRM rebuild and cache-clear procedure, then verify Docker health, extension version, critical metadata, and selected read-only checks.
7. Record the target, timestamp, hash verification, and post-restore result in a separate rollback execution record.

This procedure was not run by Phase C11.1. The current runtime and database remain unchanged.

## Safety confirmation

- No PHP, Python, connector, metadata, ACL, business data, or database schema was modified.
- No database restore/import, runtime copy-back, service restart, cache clear, or rebuild was executed.
- No commit was created.
