# Upgrade

**Status:** Documented from manifest and release reports

## Version Authority

Current packaged extension version: **`1.9.7-alpha`** (`crm-extension/manifest.json`).

Installed CRM version may lag repository HEAD if parallel work is unstaged. Always verify:

1. `crm-extension/manifest.json` `version`
2. ZIP filename under `deployment/`
3. EspoCRM **Administration → Extensions** installed version

## Upgrade Procedure (Manual)

1. **Backup** disposable CRM database (phase reports recommend SQL dump + SHA-256 sidecar).
2. Build or locate target ZIP: `deployment/prospecting-extension-<version>.zip`.
3. Verify checksum against `deployment/prospecting-extension-<version>.zip.sha256` when present.
4. In EspoCRM Admin → Extensions, upload and install new ZIP.
5. Rebuild cache when prompted.
6. Re-run applicable provisioning scripts if ACL or dashboards changed (e.g. `phase3c02_1_provision_acquisition_acl.php`).
7. Run offline tests and targeted runtime checks.

## Automated vs Manual

| Activity | Automated | Manual |
|----------|-----------|--------|
| ZIP build | `build_release_package.ps1` | — |
| Extension upload/install | — | EspoCRM Admin UI or `bin/command extension` |
| Role/dashboard provisioning | — | PHP scripts in `deployment/provisioning/` |
| Connector env config | — | Set `ESPOCRM_BASE_URL`, `ESPOCRM_API_KEY` on runner host |

## Alpha Upgrade Notes

Alpha versions (`*-alpha`) may include metadata changes without migration scripts. EspoCRM rebuild handles entity metadata. Uninstall rollback removes extension files but not user-created records.

## Not Verified in This Repo

- In-place upgrade from every historical version combination
- Zero-downtime production upgrade
- Railway/Docker automated deploy (plans exist; `deployment/railway/` boundary empty per README)

## Related Documents

- [VERSIONING.md](VERSIONING.md)
- [ROLLBACK.md](ROLLBACK.md)
- [../release/RELEASE_NOTES_1.9.7-alpha.md](../release/RELEASE_NOTES_1.9.7-alpha.md) (current package notes)
