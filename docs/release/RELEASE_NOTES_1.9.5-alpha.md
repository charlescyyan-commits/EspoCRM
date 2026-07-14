# Release Notes: 1.9.5-alpha

**Package:** `deployment/prospecting-extension-1.9.5-alpha.zip`
**Manifest release date:** 2026-07-13
**Release status:** Alpha / current packaged release

## Feature summary

- Added native **Prospecting Summary** and **Prospecting Recent Discovery** dashlets, including the Prospecting Summary client view/template.
- Added native record-list views for SearchStrategy, SearchJob, ProspectPool, and ResearchEvidence.
- Refined Prospecting Dashboard and Search views/templates, labels, client definitions, detail/list layouts, acquisition dashlets, and selected entity scopes.

## Breaking changes

- No connector-contract version change or database migration is declared by the package.
- Dashboard, list-view, and language metadata changed. Existing user dashboard placement, cached browser assets, or saved list preferences may require a normal EspoCRM rebuild/refresh and user re-save after upgrade.
- This release does not include un-packaged C10.6 development work.

## Migration notes

1. Back up the approved target and confirm `crm-extension/manifest.json` and the ZIP both identify `1.9.5-alpha`.
2. Install `prospecting-extension-1.9.5-alpha.zip` through **Administration > Extensions** and complete the requested rebuild/cache refresh.
3. Verify Prospecting Dashboard, Prospecting Search, SearchStrategy, SearchJob, ProspectPool, ResearchEvidence, and Lead views using an authorized test user.
4. Review user dashboard placement and saved list preferences; re-save only if the normal metadata refresh does not update them.
5. Do not treat this alpha release note as authorization for production installation, outreach, provider execution, or C10.6 rollout.

## Verification boundary

The package hash is `927E0BC67E670C66625AB2631AA7B361BCCD3FF20B25D8502E0DF7218CF1C7E4`. This note describes the package delta from `1.9.1-alpha` to `1.9.5-alpha` and intentionally excludes later un-packaged workspace changes.
