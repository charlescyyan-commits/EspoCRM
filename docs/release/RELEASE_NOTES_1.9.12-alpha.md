# Release Notes: 1.9.12-alpha

**Artifact:** `deployment/prospecting-extension-1.9.12-alpha.zip`  
**Integrity sidecar:** `deployment/prospecting-extension-1.9.12-alpha.zip.sha256`  
**Release date:** `2026-07-27`  
**Phase:** Phase3C19 release closure

## Summary

Closes the `1.9.12-alpha` release line after the C18 `1.9.11-alpha` /
`phase3c18-freeze` baseline. The release completes C19 governance, Reply Center
triage ownership, SendExecution recovery actions, Command Center queue
composition, and the Prospecting Dashboard operational workspace. The canonical
artifact is synchronized to release commit `8ae8eb1`
(`phase3c19: sync 1.9.12-alpha release after Search Center workspace`).
Freeze documentation index: `docs/PHASE3C19_RELEASE_NOTES.md`.

## Shipped state

### WP0 — governance

- Phase3C19 charter and architecture governance completed.
- ADR-C19 ReplyEvent lifecycle and ADR-C18-A6 SendExecution recovery boundary
  accepted and reconciled to the implemented ownership models.

### WP1 — Reply Center

- Additive ReplyEvent triage lifecycle with `OPEN`, `IN_PROGRESS`, and `CLOSED`
  states.
- `ReplyTriageService` owns triage transitions, assignment, and close audit
  fields; detail actions provide assign, release, and close entry points.
- Server-side, ACL-narrowed `c19OpenReplies` and operator-scoped
  `c19MyReplies` PrimaryFilters are exposed as name-only client filters.

### WP2 — SendExecution recovery

- SendExecution recovery workflow implemented through the existing lifecycle
  owner and the authorized workflow-action service.
- Retry, Cancel, and Ignore detail actions are authorization-gated and preserve
  the status-mutation boundary; no queue or dashboard surface mutates lifecycle
  state.

### WP3 — Command Center and operational workspace

- Command Center composition now surfaces failed sends, open replies, operator
  replies, today's follow-ups, proposal review, and failed research queues.
- The previous reply-monitoring queue is labeled **Sent Awaiting Reply** to
  distinguish it from replied items awaiting triage.
- Prospecting Dashboard was converted from the launcher/center-card model to an
  operational workspace with Overview, Research Status, Outreach Status,
  Commercial Handoff, and Pipeline Summary sections.
- Operational cards use existing server-side filters and remain ACL-filtered.

### Additional included work

- Intelligence Center research workbench surfaces and registered research
  workbench services remain included in the extension skeleton inventory.
- Search Center acquisition pipeline workspace: Create Search Job form plus
  count cards for Search Jobs, Prospect Pool, and Research Queue
  (`#ProspectPool/list/primary=researchQueue`). Search Strategy remains
  configuration-only (optional strategy ID), not a large workspace card.
- Outreach Center workspace v1: DraftApproval navbar entry opens count-card
  workspace (pending approval / pending send / failed send / open replies)
  while native `#DraftApproval/list` surfaces remain available.

## Artifact

- Canonical package:
  `deployment/prospecting-extension-1.9.12-alpha.zip`
- SHA-256:
  `E11715D2771ABE82F393B4BD86124329223CDAA2FE37A6EC0CF7FC5B0D3C1218`
- The matching `.sha256` sidecar is committed beside the package.
- Package contents match `crm-extension/manifest.json` version
  `1.9.12-alpha` and the rebuilt Search Center / Outreach workspace sources.

## Preserved boundaries

- ReplyEvent and SendExecution lifecycle writes remain service-owned.
- Quote / Approval lifecycle ownership and existing `actionRoleBindings` are
  unchanged.
- ACL behavior is preserved; no ACL redesign is introduced.
- C18 tags and the `1.9.11-alpha` artifact remain immutable historical
  markers.

## Install

Use `deployment/prospecting-extension-1.9.12-alpha.zip` on a disposable CRM.
Verify the SHA-256 sidecar before installation and complete EspoCRM's requested
rebuild/cache refresh.
