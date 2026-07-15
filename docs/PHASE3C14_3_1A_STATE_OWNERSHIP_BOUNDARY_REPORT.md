# Phase3C14.3.1A State Ownership Boundary Report

## Result

PASS WITH RISKS

C14.3.1A establishes `EmailLifecycleProjectionService` as the only CRM-extension component that writes `Lead.peEmailStatus` and `Lead.peEmailReplyStatus`.

No SendExecution bridge, Worker, Queue, ProviderAdapter, Brevo transport, retry policy, schema, Docker/runtime configuration, or real email action was changed.

## Changed Files

1. `crm-extension/files/custom/Espo/Custom/Hooks/EmailEvent/EmailEventWorkflowHook.php`
2. `crm-extension/files/custom/Espo/Modules/Prospecting/Services/EmailLifecycleProjectionService.php`
3. `crm-extension/tests/test_extension_skeleton.py`
4. `tests/test_phase3c14_3_1a_state_ownership.py`
5. `docs/PHASE3C14_3_1A_WRITER_INVENTORY.md`
6. `docs/PHASE3C14_3_1A_STATE_OWNERSHIP_BOUNDARY_REPORT.md`

## Writer Inventory

The complete inventory is recorded in:

`docs/PHASE3C14_3_1A_WRITER_INVENTORY.md`

Summary:

- The CRM extension had one direct state writer: `EmailEventWorkflowHook`.
- The DraftApproval, SendExecution, and ReplyEvent hooks already delegated to `EmailLifecycleProjectionService`.
- C09/C10 connector display projections are separate frozen remote-patch writers. They are inventoried and deliberately excluded from this step; changing them would require a later approved C14.3 bridge/convergence decision.

## Before and After

### Before

```text
EmailEvent after-save
  -> EmailEventWorkflowHook
  -> Lead.set(peEmailStatus / peEmailReplyStatus)
  -> EntityManager.saveEntity(Lead)
  -> optional Task creation
```

### After

```text
EmailEvent after-save
  -> EmailEventWorkflowHook
  -> EmailLifecycleProjectionService.projectEmailEvent()
  -> ordered and idempotent Lead projection
  -> optional Task creation
```

The hook retains only the existing idempotent non-state side effects:

- REPLIED: create the existing follow-up Task when absent.
- BOUNCED: create the existing verify-email Task when absent.

## Projection Behavior

`projectEmailEvent()` is an adapter for the existing legacy raw EmailEvent source. It preserves the established behavior through the central projection boundary:

| EmailEvent type | Lead status projection | Reply-status projection |
|---|---|---|
| SENT | SENT | unchanged |
| DELIVERED | SENT | unchanged |
| OPENED / CLICKED | unchanged; refresh email context only | unchanged |
| REPLIED | REPLIED | REPLIED |
| BOUNCED | BOUNCED | BOUNCED |

The service now performs the status, reply, event-time, and existing campaign-summary update in one changed-fields save. It preserves:

- event-time gating: older events do not overwrite newer Lead projection state;
- same-time rank protection;
- legacy protection that a later SENT/DELIVERED event cannot overwrite REPLIED or BOUNCED;
- idempotency: an unchanged requested projection causes no Lead save; and
- no source-record mutation, Provider call, Worker use, or send action.

## Tests

### New C14.3.1A state-ownership tests

`tests/test_phase3c14_3_1a_state_ownership.py` covers:

1. A SENT EmailEvent delegates to `projectEmailEvent()` and produces one Lead projection write in the deterministic projection oracle.
2. An older FAILED transition after SENT is rejected by timestamp gating; Lead remains SENT.
3. ReplyEvent uses only `EmailLifecycleProjectionService::projectReplyEvent()` for `peEmailReplyStatus`.
4. No CRM PHP hook other than the projection service retains either direct Lead status-field writer.

### Regression execution

| Test command | Result |
|---|---|
| `tests.test_phase3c14_3_1a_state_ownership` + `tests.test_phase3c11_3_projection` + `tests.test_phase3c11_5_operational_schema` | 18 / 18 PASS |
| `python -m unittest discover -s crm-extension/tests -p test_extension_skeleton.py` | 38 / 38 PASS |
| `python -m unittest discover -s chitu-connector/tests -p test_*.py` | 270 / 270 PASS |

Total: **326 / 326 PASS**.

The extension regression initially exposed two stale assertions that required the old direct-hook implementation. They were updated to assert the approved projection-service delegation and the absence of direct status writes.

## Frozen Contract Check

| Area | Result |
|---|---|
| C10 lifecycle state machine and tests | Unchanged; existing C10 hash check passed through C11.5 regression |
| C11 source-record contracts | Unchanged; existing DraftApproval, SendExecution, and ReplyEvent public projection methods remain intact |
| C12 ProviderAdapter / Brevo adapter | Unchanged |
| C13 Queue / Worker | Unchanged |
| C14.2B runner and transport boundary | Unchanged |
| CRM schema / metadata | Unchanged |
| CRM extension projection implementation | Extended only with the legacy EmailEvent adapter required for this ownership boundary |

No frozen contract was changed. The existing C11 projection implementation was extended without changing its established source-record mappings or external lifecycle contracts.

## Risks and Remaining C14.3 Work

1. **Connector convergence remains deferred.** C09/C10 connector services can still submit their approved remote Lead-summary patches. Routing those through CRM source records would require a separate architecture decision and must not be inferred from this hook-only phase.
2. **No PHP CLI is available in the current host PATH.** PHP syntax lint and EspoCRM runtime/rebuild verification were not run. Docker was not used because it is out of scope.
3. **C14.2B remains network-blocked.** No provider or worker work was reopened by this phase.

## Next-Phase Recommendation

Proceed only to a separately approved C14.3.1B or C14.3.2 design/implementation phase that defines how frozen connector-originated C09/C10 summary patches coexist with, or are eventually converged into, the CRM projection authority. Do not add a SendExecution bridge, Worker change, Provider integration, or retry behavior as part of that decision without explicit scope approval.

