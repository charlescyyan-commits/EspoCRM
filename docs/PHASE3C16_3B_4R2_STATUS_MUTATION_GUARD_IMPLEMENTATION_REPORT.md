# Phase3C16.3B-4R2 Status Mutation Guard Implementation Report

## Problem

Before this change, Quote and Approval statuses could be written through generic
record persistence. The service-layer ownership established by C16.2A and
C16.3A therefore was not an executable persistence boundary.

## Architecture implemented

The implementation uses three complementary layers:

1. Metadata marks both `Quote.status` and `Approval.status` as read-only.
2. Terminal `BeforeSave` hooks enforce the persistence rule with order `1000`.
3. Separate one-save authorization markers allow only the owning domain service
   to perform its own status-changing save.

The marker constants are centralized in
`StatusMutationSaveOption.php` and use distinct keys:

- `prospecting.quoteStatusMutationAuthorized`
- `prospecting.approvalStatusMutationAuthorized`

They are array options passed to one `EntityManager::saveEntity` call. They are
not global, static runtime state, request state, SaveContext state, or a generic
status authorization flag.

## Metadata protection

The module entity definitions and their required extension surface mirrors both
now set `readOnly: true` on `Quote.status` and `Approval.status`. No enum
options, defaults, schemas, layouts, or ACL definitions changed.

## Hook guard design

`QuoteStatusMutationGuard` permits only:

- creation of a new Quote with canonical `DRAFT` status;
- saving an existing Quote when status is unchanged; or
- a changed Quote status on a save marked by `QuoteTransitionService`.

All other Quote status changes raise `Forbidden` with the service-ownership
message. There is no administrator or special-user bypass.

`ApprovalStatusMutationGuard` permits only an Approval save marked by
`ApprovalService`, or a save of an existing Approval whose status is unchanged.
It rejects direct Approval creation and every unmarked status change. Existing
post-decision audit-field protection remains in place.

## Owner service integration

`QuoteTransitionService` supplies the Quote marker only for its one
status-changing save. `ApprovalService` supplies the Approval marker only for
`createForQuote`, `approve`, and `reject`. No markers were added to
`ApprovalDecisionService`, `QuoteWorkflowActionService`, or API actions.

No transition rule, approval business rule, transaction orchestration, ACL
design, UI action, or API route was changed.

## Tests and validation

- JSON syntax validation: PASS.
- PHP lint: PASS for all five affected PHP files.
- C16 focused contracts: PASS, 75 passed.
- Extension pytest: PASS, 167 passed and 22 subtests passed.
- Canonical artifact rebuild and builder `--check`: PASS.
- Artifact SHA-256:

```
05C7F4F4FFEE33C3CE62AB3C667C6C09E33991F0E42C2FC916CE5CCCD25EBAAA
```

The static contracts verify read-only metadata, both terminal guards, no admin
bypass, marker separation, exact owner service use, no marker use by
orchestrator/UI services, and no Quote/Approval raw-update or hook-skip path.

## Runtime validation

No local EspoCRM 10.0.1 application deployment is available in this workspace
for rebuild, cache clear, or live API/UI smoke testing. The guards use the
EspoCRM 10.0.1 `SaveOptions` per-save option API, which was verified against
the upstream source. Runtime deployment validation remains a separate follow-up.

## Remaining risks and explicitly not implemented

NOT IMPLEMENTED:

- C16.3C ACL migration;
- Approval dashboard;
- `assignedUser` design;
- notifications;
- PI workflow.

Runtime smoke deployment also remains outstanding. This task only closes the
persistence status-mutation bypass.
