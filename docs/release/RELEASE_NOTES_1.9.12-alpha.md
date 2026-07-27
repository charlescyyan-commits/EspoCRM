# Release Notes: 1.9.12-alpha

**Artifact:** `deployment/prospecting-extension-1.9.12-alpha.zip`  
**Integrity sidecar:** `deployment/prospecting-extension-1.9.12-alpha.zip.sha256`  
**Release date:** `2026-07-27`  
**Phase:** Phase3C19 WP0.2 release reconciliation (opens post-C18 release line)

## Summary

Opens the `1.9.12-alpha` release line after the C18 `1.9.11-alpha` / `phase3c18-freeze` baseline. Restores S01 package integrity by rebuilding the canonical artifact against committed HEAD (`352ca9076`), packaging C19 Reply Center lifecycle foundation and Intelligence Center research workbench sources already landed on the branch.

## Included

- Reply Center lifecycle foundation (`ReplyEvent` ownership / triage service baseline from C19 foundation commits)
- Intelligence Center research workbench surfaces and registered research workbench services in the extension skeleton inventory
- Canonical `deployment/prospecting-extension-1.9.12-alpha.zip` (+ SHA-256 sidecar) aligned to `crm-extension/manifest.json`

## Preserved

- SendExecution lifecycle ownership and C18 operational queue filters
- Quote / Approval lifecycle ownership and existing `actionRoleBindings`
- ACL model (no redesign)
- C18 tags / `1.9.11-alpha` artifact remain immutable historical markers

## Not included

- Reply Center WP1 queue filters / triage UI completion (still uncommitted WIP; deferred)
- Navigation amendments (deferred)
- ADR-only documentation churn packaged as product behavior

## Install

Use `deployment/prospecting-extension-1.9.12-alpha.zip` on a disposable CRM. Verify the SHA-256 sidecar before install.
