# ADR-C20-007: Invariant Activation Plan

| Field | Value |
| --- | --- |
| Status | RATIFIED — invariant activation plan approved; all INV-05–11 remain DEFERRED |
| Date | 2026-08-02 |
| Work Package | Phase3C20 WP3-C |
| Scope | C20-INV-05 through C20-INV-11 |
| Implementation Authorization | None |

## 1. Status

This ADR is **RATIFIED** as the invariant activation plan and readiness classification.

It records readiness, not activation.

The C20 invariant registry remains authoritative for current activation state.

C20-INV-05 through C20-INV-11 remain DEFERRED in the authoritative invariant registry.

This ADR does not change any registry status.

This ADR does not modify code, metadata, tests, or runtime.

Ratification approves only the activation plan and readiness classification.

## 2. Review Method

Repository evidence was inspected for AIJob.

Repository evidence was inspected for AIRequestLog.

Repository evidence was inspected for PromptTemplate.

Repository evidence was inspected for the frozen CapabilityRegistry.

Repository evidence was inspected for the connector boundary.

The review distinguishes a present persistence or service surface from a complete runtime path.

The review distinguishes a planned invariant from an activated invariant.

The review uses three readiness labels.

`READY` means an existing surface appears sufficient for a controlled activation review.

`DEFERRED` means governance sequencing remains incomplete without identifying a specific implementation gap.

`REQUIRES CHANGE` means repository evidence shows a missing runtime, metadata, or verification capability.

## 3. Current Invariant Register

| Invariant | Registry status | WP owner | Registry delivery condition |
| --- | --- | --- | --- |
| C20-INV-05 | DEFERRED | WP3 | AIJob, service, and mutation guard land |
| C20-INV-06 | DEFERRED | WP3 | AIJob lifecycle implementation lands |
| C20-INV-07 | DEFERRED | WP3 | AIRequestLog entity and guards land |
| C20-INV-08 | DEFERRED | WP3 | Cost-accounting request-log path lands |
| C20-INV-09 | DEFERRED | WP3 | PromptTemplate versioning lands |
| C20-INV-10 | DEFERRED | WP3 | AIJob retry strategy lands |
| C20-INV-11 | DEFERRED | WP3 | Dispatch and idempotency persistence land |

## 4. Readiness Matrix

| Invariant | Current implementation evidence | Missing runtime or metadata | Missing verification | Readiness | Blocking phase |
| --- | --- | --- | --- | --- | --- |
| INV-05 | AIJobService, save option, mutation guard, entity definition | Activation wiring and status registration | Independent service/guard activation evidence | READY | C20 WP3 activation review |
| INV-06 | AIJob status enum and transition map | Explicit cancellation-reason contract and complete lifecycle runtime evidence | Transition-matrix runtime evidence | REQUIRES CHANGE | C20 WP3 lifecycle completion |
| INV-07 | AIRequestLog entity, create-only service, append-only guard | Activation registration | Independent append-only enforcement evidence | READY | C20 WP3 activation review |
| INV-08 | AIRequestLog stores required attempt metadata | Dispatch-to-log exactly-once runtime path | Attempt-to-log cardinality and failure-path evidence | REQUIRES CHANGE | C20 dispatch completion |
| INV-09 | PromptTemplate version fields, reference mark, mutation guard | Activation registration | Referenced-template mutation and supersession evidence | READY | C20 WP3 activation review |
| INV-10 | Failure categories and AIJob retry transition surface | Retry taxonomy executor and scheduler/dispatch policy | No-auto-retry proof for forbidden categories | REQUIRES CHANGE | C20 retry completion |
| INV-11 | AIJob idempotency key field and pre-dispatch create service | Dispatch reservation and retry identity runtime linkage | Retry identity and concurrency evidence | REQUIRES CHANGE | C20 dispatch completion |

## 5. C20-INV-05

### 5.1 Contract

Every AIJob status write must pass through AIJobService with an authorized save option.

A hook guard must reject direct mutation.

### 5.2 Repository Evidence

`AIJobService` creates an AIJob with a controlled save option.

`AIJobService` contains controlled status constants and a transition method.

`AIJobStatusMutationSaveOption` exists in the AIPlatform service surface.

`AIJobStatusMutationGuard` exists in the AIPlatform hook surface.

AIJob metadata marks status read-only.

### 5.3 Missing Activation Work

The invariant registry still records DEFERRED.

No activation decision is recorded by this package.

An activation review must confirm all status mutation paths use the save option.

An activation review must confirm the guard is registered and exercised in the deployed extension.

### 5.4 Sequence

First inspect all AIJob mutation call sites.

Then verify direct persistence is rejected.

Then record independent evidence.

Then C20 governance may decide whether to activate the registry row.

## 6. C20-INV-06

### 6.1 Contract

AIJob transitions are limited to the approved matrix.

SUCCEEDED and CANCELLED are terminal.

CANCELLED requires a reason.

### 6.2 Repository Evidence

AIJob metadata defines QUEUED, RUNNING, SUCCEEDED, FAILED, and CANCELLED.

AIJobService defines a transition map.

The map allows FAILED to return to QUEUED.

The map makes SUCCEEDED terminal.

The map makes CANCELLED terminal.

The inspected AIJob metadata has no dedicated cancellation-reason field.

### 6.3 Readiness

REQUIRES CHANGE.

The cancellation-reason requirement is not evidenced as a dedicated complete contract.

The runtime lifecycle path is not authorized by this package.

### 6.4 Sequence

Define the governed cancellation-reason representation.

Implement and verify lifecycle enforcement under a separate authorization.

Exercise every allowed and forbidden transition.

Obtain independent lifecycle evidence.

## 7. C20-INV-07

### 7.1 Contract

AIRequestLog is append-only.

No role may update or delete an existing request-log row.

### 7.2 Repository Evidence

AIRequestLog metadata contains immutable attempt and provenance fields.

AIRequestLogService exposes validated create behavior.

AIRequestLogAppendOnlyGuard exists.

AIRequestLog uses unique attempt indexes.

The service marks PromptTemplate referenced inside one transaction.

### 7.3 Readiness

READY for activation review.

The registry row remains DEFERRED until that review records activation evidence.

### 7.4 Sequence

Verify update rejection.

Verify delete rejection.

Verify administrative paths cannot bypass the guard.

Verify one transaction preserves the append-only provenance relationship.

## 8. C20-INV-08

### 8.1 Contract

Every completed provider invocation produces exactly one AIRequestLog.

The log carries provider, model, token, cost, latency, and prompt-version provenance.

### 8.2 Repository Evidence

AIRequestLog metadata requires provider and model.

AIRequestLog metadata requires token counts and cost.

AIRequestLog metadata requires latency.

AIRequestLog metadata requires prompt-template id, version, and hash.

AIRequestLog unique indexes constrain job/attempt identity.

No inspected C20 dispatch runtime invokes a provider and writes the log exactly once.

### 8.3 Readiness

REQUIRES CHANGE.

Persistence structure alone is not an exactly-once dispatch-to-log path.

### 8.4 Sequence

Define the dispatch ownership transaction boundary.

Implement one controlled completion result path.

Write one log for success.

Write one log for failure.

Prove retries cannot create duplicate logs for one attempt.

## 9. C20-INV-09

### 9.1 Contract

A PromptTemplate referenced by AIRequestLog cannot be edited.

Correction occurs through a new version or supersession.

### 9.2 Repository Evidence

PromptTemplate has version and content-hash fields.

PromptTemplate has `hasBeenReferenced`.

PromptTemplateService has immutable-after-reference fields.

PromptTemplateService creates a new version with a greater version number.

PromptTemplateMutationGuard exists.

AIRequestLogService marks the template referenced in its transaction.

### 9.3 Readiness

READY for activation review.

The registry remains DEFERRED until guard and service evidence is independently accepted.

### 9.4 Sequence

Verify reference marking.

Verify a referenced version cannot change body or hash.

Verify a newer version may be created.

Verify request-log provenance remains historical.

## 10. C20-INV-10

### 10.1 Contract

Retry eligibility is controlled by the approved failure taxonomy.

AUTH, VALIDATION, QUOTA, and CONTENT_FILTER never auto-retry.

### 10.2 Repository Evidence

AIJob and AIRequestLog define failure-category values.

AIJobService has a FAILED to QUEUED transition.

No inspected retry strategy evaluates the taxonomy before requeueing.

No inspected scheduler or dispatch worker provides auto-retry behavior.

### 10.3 Readiness

REQUIRES CHANGE.

The current transition map cannot by itself prove eligibility restrictions.

### 10.4 Sequence

Ratify the retry taxonomy mapping.

Implement an owner for retry evaluation.

Reject all forbidden auto-retry categories.

Record controlled retry evidence.

## 11. C20-INV-11

### 11.1 Contract

The idempotency key is persisted before dispatch.

The same logical invocation retains the same key across retries.

### 11.2 Repository Evidence

AIJob metadata requires `idempotencyKey`.

AIJob metadata has a unique index on the key and delete marker.

AIJobService checks for an existing idempotency key before create.

AIJobService compares execution context on reuse.

No inspected dispatch runtime proves a pre-dispatch reservation through connector execution and retry.

### 11.3 Readiness

REQUIRES CHANGE.

The persistence precondition exists, but the dispatch and retry relationship is not complete.

### 11.4 Sequence

Define dispatch reservation ownership.

Persist or return the AIJob before dispatch.

Carry the same key into every permitted retry.

Prove concurrent requests return the same logical job.

## 12. Activation Roadmap

| Stage | Governance outcome | Implementation status |
| --- | --- | --- |
| 1. Repository completion | Complete missing lifecycle, dispatch, and retry surfaces | Not authorized by this ADR |
| 2. Contract verification | Verify guards, field contracts, and registry behavior | Not activated by this ADR |
| 3. Runtime verification | Prove no duplicate logs, no prohibited retries, and stable idempotency | Not activated by this ADR |
| 4. Independent review | Assess evidence and activation requests | Future governance action |
| 5. Freeze | Freeze activated C20 invariant set | Future governance action |
| 6. Available for C25 | Expose only a ratified and verified boundary | C25 remains blocked until then |

## 13. Owner Matrix

| Concern | Owner | C25 role |
| --- | --- | --- |
| AIJob lifecycle | C20 AIPlatform | Consumer only after authorization |
| AIRequestLog append-only evidence | C20 AIPlatform | Reference only |
| PromptTemplate immutability | C20 AIPlatform | Reference only |
| Retry taxonomy | C20 governance and runtime owner | No ownership |
| Dispatch idempotency | C20 dispatch owner | No ownership |
| Provider binding eligibility | CRM/C20 policy boundary | Requester only after approval |
| Connector execution | Connector-owned runtime | No ownership |

## 14. Non-Authorization

Nothing in this ADR activates an invariant.

Nothing in this ADR authorizes implementation.

Nothing in this ADR authorizes runtime dispatch.

Nothing in this ADR modifies AIJob.

Nothing in this ADR modifies AIRequestLog.

Nothing in this ADR modifies PromptTemplate.

Nothing in this ADR modifies the connector or registry.

## 15. Ratification Record

| Item | Result |
| --- | --- |
| Review type | Final WP3 ADR Ratification Review |
| Date | 2026-08-02 |
| Verdict | RATIFIED WITH NON-BLOCKING NOTES |
| INV-05 readiness classification | ACCEPTED |
| INV-06 readiness classification | ACCEPTED |
| INV-07 readiness classification | ACCEPTED |
| INV-08 readiness classification | ACCEPTED |
| INV-09 readiness classification | ACCEPTED |
| INV-10 readiness classification | ACCEPTED |
| INV-11 readiness classification | ACCEPTED |
| Invariant activation | NONE |
| Registry status changes | NONE |
| Runtime implementation | NOT AUTHORIZED |
| Any code | NOT AUTHORIZED |

C20-INV-05 through C20-INV-11 remain DEFERRED in the authoritative invariant registry.

## 16. References

- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Services/AIJobService.php`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Services/AIRequestLogService.php`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Services/PromptTemplateService.php`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/AIJob.json`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/AIRequestLog.json`
- `crm-extension/files/custom/Espo/Modules/AIPlatform/Resources/metadata/entityDefs/PromptTemplate.json`
