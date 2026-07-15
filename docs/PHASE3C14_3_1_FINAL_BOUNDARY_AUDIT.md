# Phase3C14.3.1 Final Boundary Audit

**Date:** 2026-07-14

## Verdict

**PASS WITH RISKS**

The CRM-extension ownership objective is met: `EmailLifecycleProjectionService`
is the only PHP component that directly mutates the three Lead email-summary
fields. The C12 provider, C13 worker, queue, and retry-reservation code have no
CRM write path. However, two frozen connector paths can still send direct Lead
summary patches outside the projection service. This leaves cross-writer
ordering and duplicate-state prevention unresolved.

This was a static, read-only audit. No code, metadata, runtime data, Docker
service, rebuild, cache clear, or migration was executed.

## Audit Method and Scope

The audit searched executable PHP under `crm-extension/files/custom/Espo`,
connector Python under `chitu-connector/chitu_connector`, C12/C13 queue,
worker, provider, retry modules, and entity metadata. Layouts, labels, tests,
and provisioning fixtures were not counted as production writers unless noted.

The paired source/module metadata files are aligned byte-for-byte for the
audited entities:

| Entity | Source and module metadata SHA-256 | Result |
|---|---|---|
| Lead | `82B2B42F...C5D5485` | PASS |
| ResearchEvidence | `BD82314F...02C29C31` | PASS |
| EmailEvent | `93080DAE...11481F6` | PASS |

## Writer Ownership Matrix

| Entity.Field | Current Writers | Allowed Owner | Risk | Recommendation |
|---|---|---|---|---|
| `Lead.peEmailStatus` | **CRM:** `EmailLifecycleProjectionService` from EmailEvent, DraftApproval, SendExecution hooks. **Connector:** `EmailLifecycleSyncService.sync()` directly calls `update_record("Lead", ...)`; `CampaignProjectionAdapter.project()` directly calls `update_lead_campaign_projection()` with `DRAFT_READY`. | `EmailLifecycleProjectionService` is the sole CRM-extension owner. | **HIGH:** connector patches bypass timestamp/rank/idempotency checks and can overwrite a newer `SENT`, `REPLIED`, or `BOUNCED` value. | Keep frozen paths unchanged now; require a separately approved C14 convergence decision before any connector lifecycle projection is enabled beside CRM projection. |
| `Lead.peLastEmailDate` | **CRM:** `EmailLifecycleProjectionService`. **Connector:** `EmailLifecycleSyncService.sync()`. | `EmailLifecycleProjectionService` for CRM source-record projection. | **HIGH:** direct connector timestamp can move the ordering watermark backward or forward without central arbitration. | Treat connector and CRM projections as mutually exclusive operational modes until a single ordered ingress is approved. |
| `Lead.peEmailReplyStatus` | **CRM:** `EmailLifecycleProjectionService`. **Connector:** `EmailLifecycleSyncService.sync()`. | `EmailLifecycleProjectionService`. | **HIGH:** connector can overwrite reply/bounce summary after a native ReplyEvent or EmailEvent projection. | Same convergence decision; add cross-writer ordering tests only in that approved phase. |
| `Lead.peEmailCampaignName` (coupled summary field) | **CRM:** `EmailLifecycleProjectionService` for EmailEvent campaigns. **Connector:** lifecycle sync and C09 campaign projection. | Same email-summary projection boundary. | **MEDIUM:** a stale connector campaign reference can be paired with a newer CRM status. | Include this field in the eventual ownership contract; do not treat it as independent display-only state. |
| `Lead.peProposal*` | `ChituSyncService::syncOpportunityProposal()` writes `peProposalProductFitScore`, `peProposalCooperationType`, `peProposalSuggestedNextAction`, `peProposalEligibility`, and `peProposalAction`; it writes only when score is at least 80. Synthetic provisioning scripts are non-production fixtures. | `ChituSyncService` proposal endpoint. | **LOW:** no Worker/Queue/Provider writer and no automatic Opportunity creation was found. Repeated accepted proposal syncs can refresh the human-review summary. | Preserve the V1 endpoint and `NO_AUTOMATIC_OPPORTUNITY` behavior; no C14 change is required. |
| `Lead.peSyncStatus`, `Lead.peResearchStatus`, and research summary fields | `ChituSyncService::syncLead()`; `LocalEspoCRMClient.sync_payload()` is a localhost synthetic-test client. | Controlled Chitu V1 sync service. | **LOW:** no C12/C13 execution component writes these fields. | Keep technical sync/research ownership separate from email lifecycle projection. |
| `ResearchEvidence.peEvidence*`, `peSnapshotHash`, `peCanonicalUrl`, `peEvidenceTypeNormalized`, `peClaimHash` | **Production:** `ChituSyncService::syncEvidence()` creates or updates by the C10.6 identity. **Reference/test only:** `ResearchEvidencePersistenceAdapter` and `LocalEspoCRMClient` can construct/create evidence directly but are explicitly documented as non-runtime/synthetic utilities. | `ChituSyncService::syncEvidence()` for production persistence. | **MEDIUM:** the exported reference adapter is capable of bypassing the PHP C10.6 identity writer if promoted to production later. No production invocation was found. | Keep the reference adapter non-runtime; require a C10.6-equivalent identity and dedup proof before any new evidence transport is enabled. |
| `EmailEvent.eventType`, `eventAt`, `campaign`, `source`, `externalMessageId` | `BrevoEmailEventSyncService::sync()` creates an append-only source event through `PostSyncBrevoEmailEvent`. It does not write Lead email fields directly. | `BrevoEmailEventSyncService` / approved inbound event API. | **MEDIUM:** duplicate prevention is application-level (`findOne` then create); metadata index `externalMessageIdEventType` is not declared `unique`, so concurrent identical ingests can race. | Do not change metadata in this phase. Treat concurrent-ingest uniqueness as a follow-up hardening item; the projection's changed-fields filter limits but does not eliminate source-event duplication. |
| `SendExecution.status`, provider trace, retry reservation fields | No live bridge writer was found. C13 `SendExecutionWorker` changes only `InMemorySendExecutionWorkStore`; it does not write CRM. Retry fields are metadata reservations with defaults and no scheduler. | CRM-side authorized bridge/result adapter, when separately implemented; projection service consumes the CRM record. | **MEDIUM:** every CRM `SendExecution` save invokes the projection hook and uses `modifiedAt` when no explicit event time exists. A future retry/trace update could refresh `peLastEmailDate` or project a changed terminal status. | Before a bridge is implemented, define source-record transition guards and a lifecycle timestamp distinct from incidental metadata updates. |
| `ReplyEvent.replyStatus`, `receivedAt` | No connector Worker/Queue/Provider writer found. The CRM hook delegates to `EmailLifecycleProjectionService`, which projects reply status and timestamp only. | Approved CRM inbound-reply source, followed by projection service. | **LOW:** the intentional C11 contract leaves `peEmailStatus` as `SENT` while `peEmailReplyStatus=REPLIED/BOUNCED`; this is a split summary, not a hidden direct writer. | Preserve the documented split-state semantics and make it explicit in UI/acceptance scenarios. |

## Boundary Checks

| Check | Result | Evidence |
|---|---|---|
| Extension PHP has one direct email-summary writer | PASS | The C14.3.1 ownership test and static scan find `peEmailStatus` / `peEmailReplyStatus` only in `EmailLifecycleProjectionService`; EmailEvent, DraftApproval, SendExecution, and ReplyEvent hooks delegate. |
| Worker writes CRM state | PASS | `SendExecutionWorker` updates only `SendExecutionWorkStore` and `SendExecutionQueue`; neither exposes a CRM client, Lead field, EmailEvent, or ReplyEvent operation. |
| Queue writes business fields | PASS | `InMemorySendExecutionQueue` changes only `QueueItem` claim/terminal state. It has no CRM transport dependency. |
| Provider directly modifies CRM | PASS | `BrevoProviderAdapter` calls only the configured Brevo HTTP transport and returns `SendResult`; no CRM client or CRM entity reference exists. |
| Retry handler pollutes CRM state | PASS WITH RISK | C13 has no retry scheduler, requeue, or `RETRYING` state; failures are terminal. The reserved CRM retry fields are not exercised. A future CRM SendExecution update would still invoke the projection hook. |
| Connector bypasses projection | FINDING | `EmailLifecycleSyncService` and `CampaignProjectionAdapter` both retain direct existing-Lead update seams, outside `EmailLifecycleProjectionService`. This is the deferred C09/C10 convergence risk already documented by C14.3.1A. |
| Metadata drift in audited entities | PASS | Source and module entity definitions for Lead, ResearchEvidence, and EmailEvent have matching SHA-256 values. |
| Client/API field bypass | RISK | The audited Lead email/proposal fields are not marked `readOnly` in entity metadata. Field-level ACL/runtime enforcement was not revalidated in this read-only source audit, so any principal with generic Lead edit permission must be treated as a potential manual/API writer. |

## C14.3.1 Lifecycle Findings

### F-01: frozen connector writers bypass the central ordering guard

`EmailLifecycleProjectionService` rejects older events, blocks lower-ranked
equal-time transitions, preserves reply/bounce against later SENT/DELIVERED,
and skips unchanged saves. `EmailLifecycleSyncService` and
`CampaignProjectionAdapter` issue direct patches without those protections.

```text
CRM EmailEvent / ReplyEvent -> projection service -> Lead = REPLIED at T2
connector lifecycle or C09 draft patch -> direct Lead update -> SENT or DRAFT_READY
```

The result depends on arrival order rather than the central source timestamp.
This is a boundary finding, not a request to modify frozen C09/C10 code.

### F-02: equal-rank terminal conflicts are not deterministically resolved

The service blocks only a *lower* status rank at the same timestamp. `SENT`,
`FAILED`, and `CANCELLED` all have rank 60; `REPLIED` and `BOUNCED` both have
rank 70. Two different same-time source events at the same rank can therefore
leave the last processed value. Existing tests prove older-event protection but
do not prove a deterministic tie-breaker for equal-rank conflicts.

### F-03: future SendExecution retry/trace saves can affect the projection watermark

`projectSendExecution()` uses the source record's `modifiedAt` when no explicit
execution event timestamp is available. The after-save hook runs for each CRM
SendExecution save. Current C13 has no live CRM bridge or retry execution, so
this is not an active Worker violation; it is a future integration hazard if
retry count, error text, or provider trace edits are saved after a terminal
lifecycle state.

### Non-finding: ReplyEvent status split is intentional

The C11 contract and tests explicitly require ReplyEvent to update
`peEmailReplyStatus` and `peLastEmailDate` while retaining the existing
`peEmailStatus` (for example, `SENT`). This is an intentional two-field read
model, not evidence of an unauthorized writer.

## Conclusions and Next Step

The C14.3.1 PHP ownership change is correctly contained. No C12 Provider,
C13 Worker, Queue, or retry implementation writes Lead, ResearchEvidence, or
EmailEvent records. The remaining risk is cross-boundary ownership: frozen
connector summary patches can still bypass the CRM projection service.

**Next step:** perform a separately authorized C14 convergence design review
that selects one operational ingress for Lead email summaries and defines
cross-writer timestamp/idempotency behavior. That review should also decide a
deterministic equal-rank tie-breaker and a dedicated SendExecution lifecycle
timestamp before any Worker-to-CRM bridge or retry implementation is enabled.
Do not modify C10/C11/C12/C13/C14 code as part of this audit follow-up.
