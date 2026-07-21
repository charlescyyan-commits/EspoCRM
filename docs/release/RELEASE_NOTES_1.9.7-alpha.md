# Release Notes: 1.9.7-alpha

**Artifact:** `deployment/prospecting-extension-1.9.7-alpha.zip`
**Integrity sidecar:** `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`

## C16.1A development baseline

- Adds metadata-only `Quote`, `QuoteItem`, `ProformaInvoice`, and independent C16 `Approval` entities.
- Adds the frozen entity, relationship, scope, ACL, state-value, and ownership contract tests for C16.1A.
- Preserves the C11 `DraftApproval` boundary and makes no connector, worker, provider, PDF, approval-workflow, PI-workflow, UI-layout, or notification change.

## Integrity

This development baseline is produced by the deterministic release builder and verified by the S01 release-integrity gate. The prior `1.9.6-alpha` ZIP and SHA-256 sidecar remain immutable historical artifacts.

## Scope disclosure

`1.9.7-alpha` is for disposable or explicitly approved CRM validation only. It introduces no release tag, no automatic outreach, and no C16.1B UI work.
