# Release Notes: 1.9.9-alpha

**Artifact:** `deployment/prospecting-extension-1.9.9-alpha.zip`
**Integrity sidecar:** `deployment/prospecting-extension-1.9.9-alpha.zip.sha256`

## Phase3C17 WP1.4B navigation runtime fixes

- Adds the native `DraftApproval` Record controller required by the operational
  Outreach Center entry.
- Preserves the existing Quote Record controller and packages both record-entry
  controllers in the canonical artifact.
- Localizes remaining visible Search Center, Prospecting Operations dashboard,
  and Quote workflow action strings with matching `en_US` and `zh_CN` keys.

## Integrity

`1.9.9-alpha` is a new deterministic canonical artifact. The prior
`1.9.8-alpha` ZIP and SHA-256 sidecar remain immutable historical evidence.

## Scope disclosure

This alpha release fixes record-route availability and visible localization
only. It adds no navigation architecture, workflow, ACL, entity, schema,
connector, provider, worker, or queue behavior.
