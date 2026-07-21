# Phase3C16.2C — Quote Workflow UI Actions + ACL Surface

## Scope

This increment adds the Quote record-detail action surface and authenticated API routing only.  It does not add PDF, email, approval, PI, connector, worker, queue, or notification behavior.

## Actions

| UI action | Source state | Target state | Server route | Authorized actor |
|---|---|---|---|---|
| Submit for Review | `DRAFT` | `IN_REVIEW` | `POST /Prospecting/quote/:id/workflow/submit-for-review` | Sales role; Admin |
| Approve | `IN_REVIEW` | `APPROVED` | `POST /Prospecting/quote/:id/workflow/approve` | Manager role; Admin |
| Reject | `IN_REVIEW` | `REJECTED` | `POST /Prospecting/quote/:id/workflow/reject` | Manager role; Admin |
| Send Quote | `APPROVED` | `SENT` | `POST /Prospecting/quote/:id/workflow/send` | Sales role; Admin |
| Expire | `APPROVED` | `EXPIRED` | `POST /Prospecting/quote/:id/workflow/expire` | Admin only |

All actions route to `QuoteWorkflowActionService`, which checks native record edit ACL and the action-role policy before calling `QuoteTransitionService`.  Neither the handler, API action, nor route service sets `Quote.status` or calls `saveEntity` directly.

## ACL matrix

| Actor | Submit | Approve | Reject | Send | Expire |
|---|---:|---:|---:|---:|---:|
| Sales (`Sales`, `Sales Representative`, `Sales User`) | Yes | No | No | Yes | No |
| Manager (`Manager`, `Sales Manager`) | No* | Yes | Yes | No* | No |
| Finance | No | No | No | No | No |
| Admin | Yes | Yes | Yes | Yes | Yes |

`*` A user assigned more than one role receives the union of those roles, consistent with EspoCRM ACL semantics.  The action service resolves both roles assigned directly to the user and roles inherited from the user's teams. Native record-level edit ACL is required for every action and is checked before role authorization.

## Validation

The C16.2C static contracts cover action presence, route-to-transition mapping, native ACL and role checks, prohibited direct status mutation, invalid-state protection, and boundary exclusions.  Full extension tests, artifact reproducibility/checks, and the unified offline gate are required before promotion.

## Limitations

The UI intentionally exposes only the five requested transitions.  Accept/reject-after-send, PDF generation, approval records, PI behavior, notifications, and any role provisioning changes remain outside C16.2C.
