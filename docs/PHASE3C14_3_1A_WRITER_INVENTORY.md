# Phase3C14.3.1A Writer Inventory

## Scope

This inventory covers executable write paths for `Lead.peEmailStatus` and `Lead.peEmailReplyStatus`. Metadata, layouts, labels, tests, and documentation are excluded because they do not mutate a Lead.

## CRM Extension Writers

| File | Class / method | Trigger | Current behavior | Replacement behavior |
|---|---|---|---|---|
| `crm-extension/files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php` | `EmailEventWorkflowHook::afterSave()` via `applySent`, `applyDelivered`, `applyReplied`, and `applyBounced` | New `EmailEvent` after-save | Directly assembles `peEmailStatus` and `peEmailReplyStatus` updates, then saves Lead. It separately keeps reply/bounce Task creation. | Delegate all Lead email-summary projection to `EmailLifecycleProjectionService::projectEmailEvent()`; retain Task creation only in the hook. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/EmailLifecycleProjectionService.php` | `projectDraftApproval`, `projectSendExecution`, `projectReplyEvent` | Source-record hooks | Authorized projection writer for DraftApproval, SendExecution, and ReplyEvent. It applies timestamp gating, same-time rank protection, idempotent field filtering, and Lead save. | Remain the sole CRM-extension writer and gain the EmailEvent projection entry point. |
| `crm-extension/files/custom/Espo/Custom/Hooks/DraftApproval/EmailLifecycleProjectionHook.php` | `afterSave()` | DraftApproval after-save | Delegates to the projection service; no direct Lead mutation. | Unchanged. |
| `crm-extension/files/custom/Espo/Custom/Hooks/SendExecution/EmailLifecycleProjectionHook.php` | `afterSave()` | SendExecution after-save | Delegates to the projection service; no direct Lead mutation. | Unchanged. |
| `crm-extension/files/custom/Espo/Custom/Hooks/ReplyEvent/EmailLifecycleProjectionHook.php` | `afterSave()` | ReplyEvent after-save | Delegates to the projection service; no direct Lead mutation. | Unchanged. |

## Connector Writers — Frozen and Excluded from This Step

| File | Class / method | Current behavior | Why excluded |
|---|---|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle.py` | `EmailLifecycleSyncService::sync()` | Sends the established C10 display-summary patch to an existing Lead (and optional Opportunity). | C10 connector contract is frozen. Redirecting this remote patch through a CRM source-record bridge would be a later C14.3 integration decision and is not authorized in C14.3.1A. |
| `chitu-connector/chitu_connector/espocrm_sync/campaign_projection.py` | `CampaignProjectionAdapter::project()` | Projects C09 draft preparation as `peEmailStatus=DRAFT_READY`. | C09/C10 frozen contract; no change authorized. |
| `chitu-connector/chitu_connector/espocrm_sync/real_client.py` | `LocalEspoCRMClient::update_lead_campaign_projection()` | Transport implementation for the C09 existing-Lead projection allowlist. | Test/runtime transport seam; no lifecycle ownership decision is made here. |
| `chitu-connector/chitu_connector/espocrm_sync/email_lifecycle_sync.py` | `run_local_synthetic_email_lifecycle_sync()` | Synthetic runtime verifier invokes the frozen lifecycle sync service. | Test harness only; it does not define an additional production writer. |

## Ownership Decision for C14.3.1A

Within the CRM extension, `EmailLifecycleProjectionService` becomes the only component that mutates `Lead.peEmailStatus` or `Lead.peEmailReplyStatus`.

The extension's raw `EmailEvent` remains a source record and the existing hook retains only its non-state side effect: idempotent Task creation for REPLIED and BOUNCED.

Connector-originated C09/C10 display projections are explicitly inventoried but remain frozen and excluded. They remain a follow-up C14.3 convergence risk rather than a hidden direct CRM-hook writer.

