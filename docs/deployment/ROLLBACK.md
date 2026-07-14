# Rollback

**Status:** Documented from install guides and phase reports

## Extension Uninstall (Disposable CRM)

1. **Administration → Extensions** → uninstall **Chitu Prospecting Integration**.
2. Rebuild EspoCRM cache.
3. Confirm `custom/Espo/Modules/Prospecting/` removed from CRM filesystem.
4. Remove test-only customizations under `custom/Espo/Custom/` if created for validation.

Uninstall stops extension behavior. It does **not** automatically delete business records (Leads, Opportunities) created by users or sync.

## Package Rollback

Keep previous ZIP and `.sha256` under `deployment/`:

```text
deployment/prospecting-extension-1.7.1-alpha.zip
deployment/prospecting-extension-1.7.1-alpha.zip.sha256
```

To roll back: uninstall current extension, install previous ZIP, rebuild.

## Database Rollback

Phase reports recommend pre-install SQL backup:

```text
espocrm-pre-extension.sql
espocrm-pre-extension.sql.sha256
```

Restore only on approved disposable instances. This repository does not ship automated DB restore tooling.

## Connector / Runner Rollback

The connector is not installed into EspoCRM. Roll back by checking out prior `chitu-connector/` commit on the worker host. No CRM uninstall required for connector-only changes.

## Cleanup Scripts

Validation cleanup scripts (manual, test data only):

| Script | Purpose |
|--------|---------|
| `phase3b07_cleanup_validation_records.php` | Remove `[CHITU_PHASE3B07_TEST]` records |
| `phase3c01` / `phase3b06` cleanup variants | Phase-specific synthetic data |

Do not run cleanup against production without approval.

## Fail-Closed Sync Behavior

Invalid sync payloads are rejected without CRM writes (`ChituSyncService`, connector gate). Rollback of partial sync is operational (delete/fix records), not automated.

## Related Documents

- [INSTALL.md](INSTALL.md)
- [../phase-reports/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md](../phase-reports/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md)
