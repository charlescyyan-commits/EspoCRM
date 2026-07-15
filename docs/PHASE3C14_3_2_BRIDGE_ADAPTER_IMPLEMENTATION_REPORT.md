# Phase3C14.3.2 - CRM Bridge Adapter Implementation Report

**Result:** **PASS**

## Delivered boundary

The CRM-side bridge adapter now records a validated terminal
`SendExecutionBridgeResult` through this path only:

```text
SendExecutionBridgeResult
  -> SendExecutionBridgeAdapterService
  -> SendExecution save
  -> existing EmailLifecycleProjectionHook
  -> optional SENT EmailEvent save
  -> existing EmailEventWorkflowHook
```

The adapter never loads, writes, or saves a Lead. Lead lifecycle fields remain
owned by the unchanged `EmailLifecycleProjectionService`, invoked by the
existing source-record hooks.

## Files added or changed for this phase

| File | Purpose |
|---|---|
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BridgeRejectionException.php` | Safe bridge-boundary rejection type. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BridgeNormalizedStatus.php` | Terminal `SENT` / `FAILED` value set. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/BridgeErrorClass.php` | Allowed connector failure classes. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionBridgeResult.php` | Strict payload allowlist and terminal-result validation. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionBridgeAdapterService.php` | SendExecution update and optional SENT EmailEvent persistence. |
| `crm-extension/tests/test_phase3c14_3_2_bridge_adapter.py` | C14.3.2 adapter contract coverage. |
| `crm-extension/tests/test_extension_skeleton.py` | Registers the five approved PHP files in the exact PHP inventory gate. |

No existing PHP service or hook was modified. In particular,
`EmailLifecycleProjectionService`, `EmailEventWorkflowHook`, worker, queue,
provider, and retry-scheduler code remain unchanged.

## Result behavior

### SENT

- Looks up an existing `SendExecution` by `sendRequestId = execution_id`.
- Accepts `CREATED`, `READY`, or a retrying `FAILED` execution.
- Sets only `status=SENT`, `providerName=Brevo`, and `providerMessageId`.
- Saves SendExecution, allowing the existing after-save projection hook to
  update the Lead read model.
- Creates one idempotent `EmailEvent` with `eventType=SENT`,
  `source=CONNECTOR_SYNC`, the provider message ID, UTC `eventAt`, and the
  SendExecution Lead link.
- Leaves `campaign` null. The strict terminal result contract does not carry a
  campaign reference, and the adapter must not invent one or add CRM payload
  storage; the nullable event field remains available for a later explicit
  request-context handoff.
- A repeated SENT result with the same provider message ID is a no-op for
  SendExecution and ensures the EmailEvent exists.

### FAILED

- Maps `NETWORK`, `AUTH`, `VALIDATION`, `PROVIDER`, and `UNKNOWN` directly to
  `failureCategory`.
- Sets `status=FAILED`, persists the safe `error_code` as `lastError`, and
  increments `retryCount` once per failed result.
- Does not set `maxRetries` or `nextRetryAt` and makes no retry decision.

### Validation and rejections

- Bridge payloads are an explicit allowlist and reject unknown fields,
  malformed timestamps, malformed error codes, and invalid SENT/FAILED shapes.
- Any supplied Lead lifecycle field is rejected at ingress.
- Unknown, cancelled, or conflicting SENT executions are rejected.
- No result can create a SendExecution, change identity/link fields, create a
  ReplyEvent, call a provider, invoke a worker/queue, or read credentials.

## Verification

| Check | Result |
|---|---|
| PHP lint for all five new files in container `/tmp` | PASS |
| Real PHP value-object SENT payload plus forbidden Lead field rejection | PASS |
| New C14.3.2 contract tests | PASS - 7/7 |
| C11-C14 selected projection/bridge contract tests | PASS - 33/33 |
| Full Regression Gate | PASS - 7/7 required suites, 393/393 invocations, exit code 0 |

The first full-gate attempt exposed the existing exact PHP inventory guard. It
correctly rejected the five new service files until they were explicitly added
to the approved test inventory. After that test-alignment update, the complete
gate passed.

## Scope and deployment note

This task adds the CRM-side service boundary only. It does not add the C14.3.3
POST controller that will deserialize an inbound connector result and call the
service. No production records, cache, rebuild, extension install, provider
call, queue operation, or retry operation was performed. No commit was
created.

## Final close-out verification (2026-07-14)

| Check | Result | Evidence |
|---|---|---|
| PHP lint | PASS | The five C14.3.2 PHP files were copied only to `espocrm:/tmp` and each returned `No syntax errors detected` from the healthy `espocrm` container. |
| Lead lifecycle / retry / execution boundary scan | PASS | `SendExecutionBridgeAdapterService.php` contains none of `peEmailStatus`, `peLastEmailDate`, `peEmailReplyStatus`, `peEmailCampaignName`, `maxRetries`, `nextRetryAt`, `worker`, `queue`, `BREVO_API_KEY`, or `curl`. |
| Literal `provider` scan | BLOCKED | The adapter necessarily contains `providerName`, `providerMessageId`, `provider_attempt_id`, and the allowed `PROVIDER` failure-category mapping. It contains no provider client, network call, credential, adapter invocation, or provider-module mutation. |
| Git staging | PASS | `git diff --cached --name-only` was empty. |
| Git commit boundary | PASS | HEAD remained `1cc12f948f45c88e1075de8c5563229464a6640a` (`docs: close C11 baseline hygiene`); this phase created no commit. |

The literal `provider` prohibition conflicts with the approved C14.3.2 design,
which requires the CRM adapter to retain the connector-supplied provider
attempt identifier on `SendExecution` and to map the `PROVIDER` failure class.
Removing or obscuring those occurrences would change implementation behavior
or make the audit less transparent, which is outside this close-out task.

**PHASE3C14.3.2 FINAL STATUS: BLOCKED**

The block is limited to the literal text criterion above; PHP syntax, all
non-provider forbidden-boundary checks, staged-file verification, and the
previously recorded C11-C14 and regression gates are passing. No C14.3.3 work
was started.
