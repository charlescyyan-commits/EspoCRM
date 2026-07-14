# Release Notes: 1.9.1-alpha

**Package:** `deployment/prospecting-extension-1.9.1-alpha.zip`
**Release status:** Alpha

## Feature summary

- Added native **Prospecting Dashboard** and **Prospecting Search** client scopes, controllers, views, and templates.
- Added `ProspectingDashboard` / `ProspectingSearch` labels, client definitions, and the Acquisition Overview dashlet.
- Added SearchStrategy status filters and ProspectPool lifecycle filters, plus related list/detail layout and label refinements.

## Breaking changes

- No connector-contract version change is declared.
- The package changes client routing, labels, layouts, and filter surfaces. Custom user dashboards or saved list preferences should be checked after installation because UI labels and available filter sets changed.

## Migration notes

1. Install through **Administration > Extensions** and complete EspoCRM's requested rebuild.
2. Verify that Prospecting Dashboard and Prospecting Search routes load for an authorized user.
3. Review SearchStrategy and ProspectPool saved filters, columns, and role access; re-save user preferences where required.
4. Treat all runtime verification as non-production unless explicitly approved.

## Verification boundary

This note is reconstructed from the package delta between `1.9.0-alpha` and `1.9.1-alpha`; it does not claim features first added in later packages.
