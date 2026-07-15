# Phase3C11.3 CRM Status Projection Report

**Date:** 2026-07-14  
**Result:** PASS WITH RISKS

## Projection Design

Phase3C11.3 adds a one-way CRM projection boundary:

```text
DraftApproval / SendExecution / ReplyEvent
                    |
                    v
EmailLifecycleProjectionService
                    |
                    v
Lead.peEmailStatus / Lead.peLastEmailDate / Lead.peEmailReplyStatus
```

`EmailLifecycleProjectionService` is called by native after-save hooks for the
three C11 source entities. The hooks do not mutate the source record. The
service does not call a provider, worker, queue, retry mechanism, approval
logic, C10 lifecycle service, or Opportunity automation.

Lead remains a sales-facing projection. No Lead field is read back to drive a
C10 lifecycle transition.

## Field Mapping

| Source record | Source status | Lead field | Projected value |
|---|---|---|---|
| DraftApproval | `PENDING` | `peEmailStatus` | `DRAFT_PENDING_APPROVAL` |
| DraftApproval | `APPROVED` | `peEmailStatus` | `APPROVED` |
| DraftApproval | `REJECTED` | `peEmailStatus` | `REJECTED` |
| SendExecution | `CREATED` | `peEmailStatus` | `PENDING` |
| SendExecution | `READY` | `peEmailStatus` | `READY_TO_SEND` |
| SendExecution | `SENT` | `peEmailStatus` | `SENT` |
| SendExecution | `FAILED` | `peEmailStatus` | `FAILED` |
| SendExecution | `CANCELLED` | `peEmailStatus` | `CANCELLED` |
| ReplyEvent | `REPLIED` | `peEmailReplyStatus` | `REPLIED` |
| ReplyEvent | `BOUNCED` | `peEmailReplyStatus` | `BOUNCED` |
| ReplyEvent | unknown value | `peEmailReplyStatus` | `NONE` |

The service writes only the approved Lead projection fields:
`peEmailStatus`, `peLastEmailDate`, and `peEmailReplyStatus`. The Lead status
metadata and labels were extended only for the projection values above.

## Ordering and Idempotency

- Projection timestamps prefer the source event time (`approvedAt` or
  `receivedAt`) and otherwise use the source record's modification/creation
  time.
- A source record older than `Lead.peLastEmailDate` is ignored.
- For equal timestamps, a monotonic lifecycle rank prevents a lower status
  from replacing a higher status; for example, an old or equal-time `READY`
  projection cannot roll `SENT` back to `READY_TO_SEND`.
- A Lead save is issued only when a projected value changes. Re-projecting the
  same `ReplyEvent` therefore creates no record and performs no repeat Lead
  write.

## Tests

Added `tests/test_phase3c11_3_projection.py` with eight checks:

1. DraftApproval `APPROVED` projects `Lead.peEmailStatus = APPROVED`.
2. SendExecution `SENT` projects `Lead.peEmailStatus = SENT`.
3. ReplyEvent `REPLIED` projects `Lead.peEmailReplyStatus = REPLIED`.
4. A duplicate ReplyEvent projection is idempotent.
5. An old `READY` event cannot roll back a newer `SENT` status.
6. An unknown reply status falls back to `NONE`.
7. The service is limited to approved mappings and Lead projection fields.
8. The hooks delegate without mutating their source entity.

The C11.2 persistence test was updated only to recognize the approved new
Lead projection enum values. Its C10 source-file hash checks remain unchanged.

## Runtime Verification

The extension package was installed into the local EspoCRM runtime, followed
by `rebuild` and `clear-cache`.

| Verification | Result |
|---|---|
| JSON metadata parse | PASS |
| C11.2 + C11.3 focused tests | PASS — 16/16 |
| Extension suite | PASS — 65/65 |
| Connector suite (including C10) | PASS — 270/270 |
| Full Regression Gate | PASS — 7/7 suites, 382/382 tests |
| PHP lint: service and three hooks | PASS |
| Runtime synthetic projection flow | PASS |

The runtime flow created a synthetic Lead, DraftApproval, SendExecution, and
ReplyEvent. Native hooks projected `APPROVED`, `SENT`, and `REPLIED` in order;
duplicate reply projection made no repeat Lead write; an unknown reply value
projected `NONE`; and an older `READY` projection did not replace `SENT`.
All synthetic records were removed by the verification harness.

Regression Gate command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 -PythonExecutable bundled
```

The resulting evidence file is
`temp/test-results/regression-gate-20260714-183946-284.json`.
It records a UTC timestamp of `2026-07-14T10:39:46.2753815Z`, overall status
`PASS`, seven required suites passed, and 382/382 tests passed.

## C10 Contract and Scope Boundary

No C10 lifecycle state-machine, draft generation, approval gate, send-attempt,
provider, worker, queue, retry execution, Opportunity workflow, or Lead source
of truth was changed. C10 connector tests remain passing, and the existing
C11.2 frozen-contract hashes remain unchanged.

C11.4 was not started.

## Risks

### RISK-C11.3-001 — Multiple writers for Lead email projection fields

**Severity:** MEDIUM  
**Decision:** Deferred  
**Planned resolution:** C11.5 Operational Hardening or later

`EmailLifecycleProjectionService` enforces ordering among its three declared
C11 source record types. The pre-existing `EmailEventWorkflowHook` can also
write legacy `Lead.peEmail*` summary fields outside this service. Changing that
hook in C11.3 would violate the frozen C10 boundary, so it is deliberately
unchanged. Until the planned consolidation work is approved, cross-writer
ordering is not globally serialized. This is why the implementation result is
recorded as **PASS WITH RISKS**, rather than an unqualified PASS.

## Migration Notes

The changes are metadata and application-layer additions. EspoCRM rebuild
creates the necessary schema changes through its native entity-definition
mechanism. Existing Lead values are preserved; no backfill, data cleanup, or
projection replay was performed.
