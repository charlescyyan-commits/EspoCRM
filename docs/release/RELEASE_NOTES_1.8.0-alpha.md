# Release Notes: 1.8.0-alpha

**Package:** `deployment/prospecting-extension-1.8.0-alpha.zip`
**Release status:** Alpha

## Feature summary

- Added native **SearchJob** and **ProspectPool** module surfaces: entities, controllers, scopes, ACL definitions, client definitions, labels, list/detail layouts, and primary filters.
- Added acquisition dashboard dashlets for discovery jobs, job states, lead pool, and research queue.
- Added queue-oriented filters for discovery, qualification, research, and CRM ProspectPool views.

## Breaking changes

- No connector-contract breaking change is recorded for this package.
- CRM administrators must account for the new SearchJob and ProspectPool scopes when configuring roles and navigation. Existing roles do not automatically gain access simply because the package is installed.

## Migration notes

1. Back up the target CRM before installing an alpha package.
2. Install the ZIP through **Administration > Extensions** and allow EspoCRM to rebuild metadata/cache when prompted.
3. Apply the relevant approved role/dashboard provisioning for SearchJob and ProspectPool; do not run provisioning scripts against production without approval.
4. Verify the new scopes, primary filters, and dashlets with a non-production admin account.

## Verification boundary

This note is reconstructed from the package delta between `1.7.1-alpha` and `1.8.0-alpha`. It does not assert production migration or runtime compatibility beyond the package manifest.
