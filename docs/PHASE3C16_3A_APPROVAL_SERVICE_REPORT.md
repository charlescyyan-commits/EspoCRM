# Phase3C16.3A — ApprovalService Core Report

**Baseline HEAD:** `72aa07546c2f448f802fdcacea467aba30301aec`  
**Version:** `1.9.7-alpha`  
**Scope:** Approval domain core only

## 1. Implementation boundary

### Owned

- `ApprovalService` — sole writer of Approval business state
- `Entities/Approval.php` — typed entity marker
- `Hooks/Approval/AuditFieldProtectionHook.php` — post-decision audit immutability
- C16.3A offline contract tests

### Explicitly not owned / not changed

- Quote status transitions / `QuoteTransitionService`
- `QuoteWorkflowActionService`
- UI, API routes, dashlets, ACL redesign
- PI workflow, PDF, notifications, multi-level approval
- Quote ↔ Approval status propagation (deferred)

### Boundary rules enforced in code

1. ApprovalService is the only Approval business-state writer.
2. Quote.status is never written by ApprovalService.
3. No optional nullable service dependencies (only `EntityManager` is injected).

## 2. State machine

```text
PENDING ──approve()──► APPROVED (terminal)
   │
   └──reject()───────► REJECTED (terminal)
```

| Transition | Guard | Writes |
| --- | --- | --- |
| createForQuote | no other PENDING for same Quote (locked) | PENDING, target Quote, level 1, requestedBy, name `{quoteNumber} Approval #N` |
| PENDING → APPROVED | four-eyes (`requestedById != actor`) | status, decision, approver, decidedAt, optional reason |
| PENDING → REJECTED | non-empty reason | status, decision, approver, decidedAt, reason |
| APPROVED → approve | idempotent no-op | none (decidedAt preserved) |
| REJECTED → reject | idempotent no-op | none (decidedAt preserved) |
| APPROVED → reject / REJECTED → approve | Conflict | none |

## 3. Transaction model

Each public method runs inside **one** `EntityManager::getTransactionManager()->run(...)` callback.

- **createForQuote:** `SELECT … FOR UPDATE` pending-by-quote check + sequence count + single `saveEntity` insert (TOCTOU-safe duplicate PENDING prevention).
- **approve / reject:** row `FOR UPDATE` lock + single atomic `saveEntity` of status and audit fields together.

## 4. Audit protection

Service path:

- Decision fields written only inside approve/reject.
- Idempotent same-decision returns do not rewrite `decidedAt`.

Hook path (`AuditFieldProtectionHook` BeforeSave):

- After fetched status is APPROVED or REJECTED, mutating `AUDIT_FIELDS` raises `Forbidden`.

## 5. Files changed

- `crm-extension/files/.../Services/ApprovalService.php` (new)
- `crm-extension/files/.../Entities/Approval.php` (new)
- `crm-extension/files/.../Hooks/Approval/AuditFieldProtectionHook.php` (new)
- `crm-extension/tests/test_c16_approval_service.py` (new)
- `crm-extension/tests/test_extension_skeleton.py` (inventory)
- `deployment/prospecting-extension-1.9.7-alpha.zip` (+ `.sha256`)
- `docs/PHASE3C16_3A_APPROVAL_SERVICE_REPORT.md`

## 6. Test results

| Check | Result |
| --- | --- |
| `php -l` ApprovalService / Entity / Hook | PASS |
| C16 ApprovalService contracts | 8 passed |
| Focused C16 + namespace + i18n suite | PASS |
| Extension pytest | 124 passed (+22 subtests) |
| Unified offline gate | PASS (php-lint, extension, connector 279, root/runtime 162, S01 12, baseline 5, unittest, artifact-check, deployment-validation) |
| Artifact SHA-256 | `788EE10753E7AAFA39A5FF2BF68859A9A8F07607C469F91DD8DE9998354EB508` |

## 7. Limitations

- Offline tests are static PHP contracts (no live Espo container / DB concurrency harness).
- Interface→concrete bindings for other C16 services are unchanged.
- No auto-create on Quote IN_REVIEW, no Manager UI, no Quote status propagation after decision.
- Four-eyes is enforced on `approve()` only (per C16.3A approve rules); reject requires reason but not four-eyes.
- `QuoteNumberingServiceInterface` container binding remains a runtime concern from 3A-0.

## Verdict

**PASS**
