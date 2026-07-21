# Phase3C16.3B-0 — Runtime Integrity Recovery Report

**Baseline HEAD:** `b7b7332404d9b7b48ec4990029a6c347340951bc`  
**Version:** `1.9.7-alpha`  
**Scope:** Quote numbering runtime DI recovery only (not C16.3B Approval propagation)

## 1. Problem discovered

**B2 — QuoteNumberingService runtime availability**

- `QuoteTransitionService` requires `QuoteNumberingServiceInterface` (mandatory after C16.3A-0).
- No module DI binding existed for that interface.
- `QuoteNumberingService` constructor demanded raw `PDO`, which EspoCRM’s injectable factory does not provide as a first-class constructor dependency.
- Combined risk: container resolution fails at runtime, or earlier nullable DI allowed DRAFT→IN_REVIEW to proceed **without** numbering.

**Reject-state contradiction (documented only)**

- Client `Quote` detail action list exposes `rejectQuote` while status is IN_REVIEW (UI handler visibility).
- Server transition matrix allows only `IN_REVIEW → APPROVED` (not `IN_REVIEW → REJECTED`).
- C16.3B will replace Reject with Approval REJECTED → Quote IN_REVIEW → DRAFT. This phase must **not** invent `IN_REVIEW → REJECTED`.

## 2. Root cause

1. Missing Espo module `Binding` processor for interface → implementation.
2. Numbering service depended on unsupported raw PDO injection instead of Espo-resolvable `EntityManager`.
3. UI Reject action was shipped in C16.2C before Approval-driven reject propagation existed.

## 3. Runtime architecture decision

Verified against EspoCRM 10.0.1 DI documentation and source (module `Binding implements BindingProcessor`; `EntityManager::getPDO()` exists):

| Concern | Decision |
| --- | --- |
| Interface binding | `Espo\Modules\Prospecting\Binding` → `bindImplementation(QuoteNumberingServiceInterface, QuoteNumberingService)` |
| Numbering construction | Inject `EntityManager`; obtain PDO via `$entityManager->getPDO()` (algorithm unchanged) |
| Fail-loud | Keep mandatory numbering dependency on `QuoteTransitionService`; no nullable / silent skip |
| Reject contradiction | Document + regression-lock matrix; no transition expansion |

`EntityManager::getPDO()` is deprecated as of EspoCRM 7.0 and marked for removal in v11. It remains available in the pinned 10.0.1 runtime and is used here as the smallest compatible change that preserves the existing atomic MySQL sequence algorithm. Migration to an ORM/query-executor implementation is a future version-upgrade task, not part of this recovery.

## 4. Files changed

- `crm-extension/files/.../Prospecting/Binding.php` *(new)*
- `crm-extension/files/.../Services/QuoteNumberingService.php` *(EntityManager ctor)*
- `crm-extension/tests/test_c16_quote_numbering_runtime.py` *(new)*
- `crm-extension/tests/test_c16_quote_numbering.py` *(ctor expectation)*
- `crm-extension/tests/test_extension_skeleton.py` *(inventory)*
- `deployment/prospecting-extension-1.9.7-alpha.zip` (+ `.sha256`)
- `docs/PHASE3C16_3B_0_RUNTIME_INTEGRITY_RECOVERY_REPORT.md`

## 5. Tests

| Check | Result |
| --- | --- |
| `php -l` Binding + QuoteNumberingService | PASS |
| Runtime integrity + numbering + workflow focused pytest | 24 passed |
| Extension pytest | 128 passed (+22 subtests) |
| Unified offline gate | PASS |
| Artifact SHA-256 | `13B9D1B2E338DD8334059D5375112ACDB9F03064BEBC158EED560263540A9629` |

New runtime tests prove:

1. Binding registers the numbering interface exactly once.
2. Transition service receives a mandatory interface dependency (no silent null).
3. DRAFT→IN_REVIEW still calls `assignQuoteNumber` before status write.
4. `IN_REVIEW → REJECTED` remains forbidden while client Reject action still exists (C16.3B debt).

## 6. Remaining C16.3B work

- Approval decision → Quote status propagation (APPROVED / REJECTED→DRAFT)
- Migrate / retarget UI Reject away from direct Quote status mutation
- Any ACL / API wiring for Approval decisions
- Live Espo container smoke that instantiates `QuoteTransitionService` via DI

## NOT IMPLEMENTED

- Approval propagation
- Quote status synchronization from Approval
- Approval UI
- ACL migration
- Multi-level approval
- `IN_REVIEW → REJECTED` transition expansion

## Verdict

**PASS**
