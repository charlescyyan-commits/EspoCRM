# Phase3C11.2 CRM Persistence Entities Report

**Date:** 2026-07-14  
**Result:** **PASS**  
**Scope:** Native EspoCRM persistence schema and human-visible ACL/UI only. No C10 lifecycle implementation, registry substitution, projection, provider, worker, queue, retry execution, or Opportunity workflow was added.

## Entity design implemented

Three native Prospecting entities were added with EspoCRM entity definitions, native scopes, client definitions, layouts, English and Chinese labels, zero-logic entity shells, and role provisioning.

| Entity | Purpose | Canonical identity | Relationships |
|---|---|---|---|
| `DraftApproval` | Durable human-visible approval state | Unique `draftId` | `Lead`; `approvedBy` User; has-many `SendExecution` |
| `SendExecution` | Durable human-visible send execution record | Unique `sendRequestId` | `DraftApproval`; `Lead`; has-many `ReplyEvent` |
| `ReplyEvent` | Durable traceable reply/bounce event | Unique `externalEventId` | `SendExecution`; `Lead` |

The unique identity indexes include EspoCRM's `deleteId` convention, permitting a new record only after a soft-deleted record is no longer active. Ordinary indexes support Lead and trace lookups.

## Fields

### DraftApproval

- Required: `name`, `draftId`, `status`, `lead`.
- `status`: `PENDING`, `APPROVED`, `REJECTED`.
- Approval trace: `approvedBy`, `approvedAt`, `decisionReason`, `evidenceReference`, `scoreSnapshot`, `contentHash`.
- No draft body, prompt content, or AI reasoning field exists.
- `evidenceReference` is a compact reference only; there is no direct `ResearchEvidence` relationship.

### SendExecution

- Required: `name`, `sendRequestId`, `status`, `draftApproval`, `lead`.
- `status`: `CREATED`, `READY`, `SENT`, `FAILED`, `CANCELLED`.
- Provider-trace fields: `providerName`, `providerMessageId`.
- Schema-only retry reservation: `retryCount`, `maxRetries`, `nextRetryAt`, `lastError`.
- No retry, provider call, worker, queue, or send orchestration is implemented.

### ReplyEvent

- Required: `name`, `externalEventId`, `replyStatus`, `receivedAt`, `sendTraceReference`, `sendExecution`, `lead`.
- `replyStatus`: `SENT`, `REPLIED`, `BOUNCED`, `UNSUBSCRIBED`, matching the existing C10.4 reply boundary vocabulary without changing it.
- Permitted event persistence is limited to `eventMetadata`, timestamp, and trace/reference fields.
- No full email body, subject, prompt, or hidden reasoning field exists.

## Relationships and Lead boundary

`Lead` received only three has-many relationship links: `draftApprovals`, `sendExecutions`, and `replyEvents`.

No `Lead.peEmail*` field was changed:

- `Lead.peEmailStatus` retains its existing six values.
- `Lead.peEmailReplyStatus` remains a `varchar(64)`.
- No status projection or reverse control channel was implemented.

No entity links to `ResearchEvidence` or `Opportunity`; C10.6 evidence persistence and Opportunity workflow remain untouched.

## ACL

`deployment/provisioning/phase3c11_2_provision_persistence_acl.php` applies the same scope policy to all three entities:

| Role | Create | Read | Edit | Delete |
|---|---:|---:|---:|---:|
| Admin | yes | all | all | all |
| Integration Bot | yes | all | all | no |
| Sales Manager | no | all | no | no |
| Sales User | no | all | no | no |

This gives Sales User read-only visibility and prevents modification of approval history, send execution records, and reply events. The local runtime provisioning completed for all four roles.

## Tests

New test: `tests/test_phase3c11_2_persistence_entities.py`.

It covers entity existence, surface/module parity, field contracts, required relationships, unique indexes, native scopes/layouts/ACL definitions, Sales User read-only ACL policy, Lead projection preservation, content boundary, no Provider/Worker/Opportunity implementation, and C10 source/test hash preservation.

| Check | Result |
|---|---|
| JSON parse for all extension metadata | PASS |
| C11.2 persistence entity contract tests | PASS — 8/8 |
| Extension suite | PASS — 65/65 |
| Connector suite, including C10 tests | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 required suites, 382/382 tests |

## Runtime verification

The local backed-up EspoCRM runtime received a freshly built C11.2 extension package, then executed:

```text
php command.php extension --file=/tmp/phase3c11_2_persistence_entities_v2.zip
php command.php rebuild
php command.php clear-cache
php /tmp/phase3c11_2_provision_persistence_acl.php
```

The final runtime verification used EspoCRM's application metadata service and EntityManager read queries:

| Entity | Runtime fields | Status field | Existing record |
|---|---:|---|---|
| DraftApproval | 17 | `status` | none |
| SendExecution | 18 | `status` | none |
| ReplyEvent | 15 | `replyStatus` | none |

All three PHP entity shells passed `php -l`. Runtime role data matched the ACL table above. No business entity record was created during validation.

## Migration notes

- EspoCRM rebuild created/updated native schema and indexes for the three new entities in the local runtime.
- No new database was introduced and no manual SQL migration was used.
- No existing Lead data was migrated or cleaned.
- `Lead.peEmailReplyStatus` was not converted to an enum; its future projection mapping remains deferred.
- The installed local package retained manifest version `1.9.5-alpha`; no release tag or release artifact was changed.
- The local C11.1 backup remains the rollback source for the runtime change.

## Explicitly not implemented

- C10 lifecycle state machine, approval guards, SendAttempt contract, idempotency, reply validation, or C10.6 evidence persistence.
- REST-backed registries, DraftStore, status projection, retry execution, worker/queue, provider integration, email sending, webhook handling, or Opportunity creation.
- C11.3 or later work.
