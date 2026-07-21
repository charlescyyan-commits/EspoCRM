# Phase3C16.3B-4 — Release Validation Audit

**Audit mode:** Independent read-only audit.
**Baseline:** `82bbd3b3f9cd2945d576fb07ed3375b81fdba593`.
**Final verdict:** **BLOCKED**

## 1. Executive Summary

The C16.3B source contains the intended Approval-driven workflow, but it is not
eligible for freeze. This audit changed no code, metadata, test, artifact,
commit, or remote state.

Blocking evidence:

- Canonical `1.9.7-alpha` ZIP is stale and fails source/artifact parity.
- Generic EspoCRM record CRUD bypasses both claimed service-owned status flows.
- The available real EspoCRM 10.0.1 runtime lacks the two C16.3B Approval services.
- C16 focused and extension test gates are red on a stale UI contract.

## 2. Architecture Verdict

| Component | Source ownership result |
|---|---|
| `ApprovalService` | Sole reviewed service writing Approval status/audit fields; no Quote dependency. |
| `QuoteTransitionService` | Sole reviewed service writing Quote status; validates matrix and creates PENDING Approval only for `DRAFT → IN_REVIEW`. |
| `ApprovalDecisionService` | Outer cross-domain transaction; delegates decision and Quote propagation; no direct status save. |
| `QuoteWorkflowActionService` | ACL/role-gated user entry; delegates to decision or transition service; no direct status save. |

Service-layer ownership is clean, but not authoritative at runtime. `Quote.status`
and `Approval.status` are editable enum fields and appear in normal Record detail
layouts. There is no Quote before-save guard. The Approval hook protects only
records whose fetched status is already APPROVED/REJECTED, and returns for
PENDING records. A user with ordinary edit access can therefore directly update:

- Quote status, bypassing validation, quote numbering, and Approval creation.
- PENDING Approval status, bypassing four-eyes, reject reason, and audit fields.

This is a release-blocking workflow/security bypass.

## 3. State Machine Verdict

| Flow | Source result |
|---|---|
| Submit | Quote `DRAFT → IN_REVIEW`, number assignment, PENDING Approval. |
| Approve | Approval `PENDING → APPROVED`, Quote `IN_REVIEW → APPROVED` through decision orchestration. |
| Reject review | Approval `PENDING → REJECTED`, Quote `IN_REVIEW → DRAFT`, reason required. |
| Customer reject | Quote `SENT → REJECTED`, no Approval mutation. |
| Invalid transition | `IN_REVIEW → REJECTED` is absent from the transition matrix. |

Number assignment skips an existing number, so code is compatible with
reject-to-DRAFT then resubmit. The complete lifecycle has not been runtime
proven, and generic CRUD bypass makes the effective state-machine result BLOCKED.

## 4. Transaction Verdict

The C16.3B-0 real EspoCRM 10.0.1/MariaDB spike confirmed nested
`TransactionManager->run()` uses savepoints (`POINT_<level>`):

| Scenario | Observed result |
|---|---|
| Inner success, outer commit | Inner write persisted. |
| Inner failure, outer catches | Inner write rolled back; outer remained usable. |
| Inner success, outer failure | Inner write did not leak after root rollback. |

This supports the outer decision transaction plus nested Approval/Quote service
wrappers. No source-level partial-commit hole was found. Actual C16.3B
Approval-to-Quote atomicity is unverified because the target runtime lacks both
Approval service files.

## 5. Action Migration and Security Verdict

| Action | Expected route | Result |
|---|---|---|
| `submit-for-review` | Quote transition | PASS at action layer |
| `approve` | `ApprovalDecisionService::approveApproval` | PASS |
| `reject-review` | `ApprovalDecisionService::rejectApproval` | PASS; reason required |
| `mark-customer-rejected` | Quote `SENT → REJECTED` only | PASS |
| `send` / `expire` | Quote transition | PASS at action layer |

The action route checks record edit ACL and direct/team role membership; decision
calls enforce Manager/Sales Manager/Admin. No new action-route escalation was
found. The ordinary CRUD bypass remains an escalation relative to the workflow.
The deprecated `reject` alias duplicates the customer-rejection UI action; this
is non-blocking operator-clarity risk.

## 6. Test Verdict

| Validation | Result |
|---|---|
| C16 focused tests | **81 passed, 1 failed** |
| Full extension tests | **159 passed, 1 failed, 22 subtests passed** |
| Package baseline regression | 5 passed |
| Canonical artifact `--check` | **FAILED** |

Both failed suites stop at
`test_c16_entity_contracts.py::C16EntityContractTests::test_ui_metadata_contract`.
Its exact action-set assertion omits `rejectReviewQuote` and
`markCustomerRejectedQuote`, so the release contract is stale. Positive static
coverage exists for creation, decisions, idempotency, propagation delegation,
action routing, roles, namespaces, and transaction behavior. Runtime DI/service
load, API authorization, end-to-end rollback, and end-to-end number retention
remain blind spots.

## 7. Artifact and Release Verdict

Manifest and artifact both declare `1.9.7-alpha`. ZIP SHA-256 is
`13B9D1B2E338DD8334059D5375112ACDB9F03064BEBC158EED560263540A9629`; the
sidecar matches, but the archive is stale. Deterministic verification reports:

```text
missing=['files/custom/Espo/Modules/Prospecting/Services/ApprovalDecisionService.php']
```

Inventory is 276 source entries versus 275 ZIP entries. The local 10.0.1 runtime
likewise lacks `ApprovalService.php` and `ApprovalDecisionService.php`; only the
older QuoteTransition service is present. Artifact parity, deployed services,
and runtime DI are not release-ready.

## 8. Final Runtime Smoke Checklist

Run only after parity/checksum pass, candidate installation, rebuild, and cache
clear in isolated EspoCRM 10.0.1:

1. Create Quote: confirm DRAFT and no number.
2. Submit review: confirm IN_REVIEW, one PENDING Approval, and `QT-YYYY-NNNN`.
3. Distinct Manager approves: confirm Approval audit values and Quote APPROVED.
4. Separate Quote review rejection with reason: confirm Approval REJECTED and Quote DRAFT atomically.
5. Send then customer-reject: confirm only Quote `SENT → REJECTED` changes.
6. Resubmit rejected-review Quote: confirm new PENDING Approval and unchanged number.
7. Deny self-approval, non-manager decision, missing reason, invalid transition, and direct status CRUD.
8. Remove synthetic records and confirm no residue.

## 9. Known Risks and Freeze Recommendation

### Blocking

- Stale canonical artifact and failed parity check.
- Red C16 focused and extension gates.
- Generic CRUD status-bypass of the workflow services.
- C16.3B services absent from the available target runtime.

### Recommendation

**BLOCKED** — Phase3C16.3B must not be frozen at `82bbd3b`. This is a release
judgment only; it proposes no new product feature development.
