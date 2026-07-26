# Release Notes: 1.9.11-alpha

**Artifact:** `deployment/prospecting-extension-1.9.11-alpha.zip`  
**Integrity sidecar:** `deployment/prospecting-extension-1.9.11-alpha.zip.sha256`  
**Release date:** `2026-07-26`  
**Phase:** Phase3C18 WP2 reconciliation (opens post-C17 release line)

## Summary

Opens the `1.9.11-alpha` release line after the frozen C17 `1.9.10-alpha` / `phase3c17-freeze` baseline. Packages C18 WP1 lifecycle ownership plus WP2.1/WP2.2 SendExecution operational queue filters and read-only queue surfaces. Embeds the SendExecution governance marker in workflow metadata policy without redesigning Quote authorization.

## Included

- SendExecution lifecycle ownership (`SendExecutionTransitionService`, mutation guard, adapter handoff)
- Operational PrimaryFilters: `c18ReadyToSend`, `c18FailedSend`
- Read-only Outreach / Command Center queue surfaces consuming those filters
- `prospectingWorkflow.json` SendExecution policy anchor (`adr-c18-sendexecution-v1`)

## Preserved

- Quote / Approval lifecycle ownership and existing `actionRoleBindings`
- ACL model (no redesign)
- Read-only queue composition (no status mutation from dashboards)
- C17 tags `v1.9.10-alpha` and `phase3c17-freeze` remain immutable historical markers

## Not included

- Operator retry/cancel detail-page actions (deferred WP2.3+)
- `sentAt` entityDefs packaging (still transition-owned; schema packaging deferred)
- Role-bound enforcement of `sendExecution.*` via `WorkflowAuthorizationService` (marker/actions anchored; bindings deferred)

## Install

Use `deployment/prospecting-extension-1.9.11-alpha.zip` on a disposable CRM. Verify the SHA-256 sidecar before install.
