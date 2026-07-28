# Release Notes: 1.9.13-alpha

**Artifact:** `deployment/prospecting-extension-1.9.13-alpha.zip`
**Integrity sidecar:** `deployment/prospecting-extension-1.9.13-alpha.zip.sha256`
**Release date:** `2026-07-28`
**Phase:** Phase3C20 WP0 artifact provenance repair

## Summary

Opens the `1.9.13-alpha` release line after the frozen C19
`1.9.12-alpha` baseline. This version separates the Phase3C20 WP0 BridgeError
taxonomy parity payload from the immutable `phase3c19-freeze` artifact, removing
the prior one-version/two-hash provenance collision.

## Included

- `BridgeErrorClass` now has parity with the connector and SendExecution failure
  taxonomy.
- `RATE_LIMIT`, which was already accepted by provider and SendExecution
  contracts, is now accepted end-to-end by both bridge adapters.
- `QUOTA` and `CONTENT_FILTER` are added to the bridge taxonomy,
  `SendExecution.failureCategory` metadata, connector classification, and
  English/Chinese labels.
- Bridge and result adapters preserve all three classifications instead of
  rejecting them as unknown error classes.
- Taxonomy-level auto-retry eligibility remains classification-only:
  `NETWORK`, `PROVIDER`, and `RATE_LIMIT` are eligible; `QUOTA` and
  `CONTENT_FILTER` are not.

## Operational impact

Failures in these categories that were previously rejected at the bridge can
now persist as `FAILED` SendExecution records with their actual failure
category. Operators may therefore see additional, previously invisible failures
in the `c18FailedSend` queue. An increase in failed-send counts reflects improved
classification parity and visibility, not a new failure mode.

This release does not add retry scheduling, change SendExecution lifecycle
ownership, introduce AIPlatform runtime code, or start Phase3C20 WP1.

## Artifact provenance

- `1.9.12-alpha` remains bound to `phase3c19-freeze` / `v1.9.12-alpha`
  at commit `4a7a111`.
- Frozen `1.9.12-alpha` SHA-256:
  `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218`.
- `1.9.13-alpha` is the first release identity for the Phase3C20 WP0
  BridgeError parity payload.
- `1.9.13-alpha` SHA-256:
  `DE9C665CC8BDE270DB2E5A772E4B7AB9A1C4C00F0BB3A370FA353DDF9B25B50F`.

## Install

Use `deployment/prospecting-extension-1.9.13-alpha.zip` only on a disposable or
explicitly approved CRM. Verify the SHA-256 sidecar before installation and
complete EspoCRM's requested rebuild/cache refresh.
