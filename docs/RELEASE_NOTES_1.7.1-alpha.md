# Release Notes: 1.7.1-alpha

## Summary

`1.7.1-alpha` is the Phase3B.07.2 compatibility release. It makes the Prospecting Operations dashboard safe for the existing Admin, Sales Manager, and Sales User ACL profiles without changing the connector contract or CRM business boundaries.

## Added

- Canonical role-compatible dashboard provisioning.
- Dashboard ACL compatibility coverage and final Phase3B freeze documentation.

## Fixed

- Sync Issues now orders by readable, ACL-safe `modifiedAt DESC` instead of restricted `peLastSyncAt`.
- Stale Phase3B dashboard preference options are removed before canonical options are rebuilt.
- Sales Manager provisioning omits entity dashlets that its existing ACL cannot read.
- The `peSyncFailed` filter remains the Sync Issues criterion.

## Breaking Changes

None. Connector Contract V1, schema, ACL permissions, canonical score, Lead metadata, and no-automatic-Opportunity behavior are unchanged.

## Known Issues

- Production Cron/daemon scheduling and rollback procedures remain operational documentation debt.
- Dashboard role selection currently uses the explicit provisioning role mapping used by the local acceptance environment.
- Browser/network regression automation is not yet a formal CI gate.

## Upgrade

1. Preserve the existing 1.7.0-alpha backup and release artifact.
2. Install `prospecting-extension-1.7.1-alpha.zip`.
3. Run rebuild and clear-cache.
4. Run the canonical operations-dashboard provisioning script.
5. Verify role-specific dashboard loading and run the Phase3B regression suite.

## Installation Example

```text
docker exec espocrm bin/command extension --file=/tmp/prospecting-extension-1.7.1-alpha.zip
docker exec espocrm bin/command rebuild
docker exec espocrm bin/command clear-cache
docker exec espocrm php /tmp/phase3b07_provision_operations_dashboards.php
```

## Package Integrity

- Package: `deployment/prospecting-extension-1.7.1-alpha.zip`
- SHA-256: `564091446761B4F0D4D330416AB28AA16C7AF704B1DC4C8CE2744C3CDAF5962F`

