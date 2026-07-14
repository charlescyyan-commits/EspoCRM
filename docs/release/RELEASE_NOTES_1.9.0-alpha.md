# Release Notes: 1.9.0-alpha

**Package:** `deployment/prospecting-extension-1.9.0-alpha.zip`
**Release status:** Alpha

## Feature summary

- Added **SearchStrategy** as a native Prospecting entity with layouts, client definition, ACL/scope metadata, labels, primary filters, and an acquisition dashboard dashlet.
- Added the SearchStrategy job-generation API/service and a native client-side detail action for generating jobs.
- Expanded SearchJob state support with queued and cancelled primary filters, plus related layout, scope, and dashboard updates.

## Breaking changes

- The prior SearchJob **JobsWaiting** primary-filter implementation was replaced by the queued/cancelled state model. Saved user filters, dashboard configurations, or automation that depend on the removed filter identifier require review.
- No new connector contract version is declared by this package.

## Migration notes

1. Back up the target CRM and install the ZIP through **Administration > Extensions**.
2. Allow the EspoCRM rebuild to complete so SearchStrategy routes, layouts, and client definitions become available.
3. Review role permissions and dashboard configuration for SearchStrategy and the SearchJob queued/cancelled filters.
4. Re-run only approved provisioning appropriate to the target environment; do not execute production changes from this note.

## Verification boundary

This note is reconstructed from the package delta between `1.8.0-alpha` and `1.9.0-alpha`. It does not represent later C10 development work.
