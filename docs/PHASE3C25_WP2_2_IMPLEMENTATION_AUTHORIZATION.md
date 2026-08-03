# Phase3C25 WP2.2 Implementation Authorization

| Field | Value |
| --- | --- |
| Document Type | Implementation Authorization (governance) |
| Work Package | WP2.2 — CommercialBrief application-layer implementation |
| Status | **AUTHORIZED WITH CONDITIONS** |
| Date | 2026-08-03 |
| Authorization Charter | `docs/PHASE3C25_WP2_2_AUTHORIZATION_CHARTER.md` |
| Implementation Plan | `docs/PHASE3C25_WP2_2_IMPLEMENTATION_PLAN.md` (APPROVED — READY FOR IMPLEMENTATION AUTHORIZATION) |
| C20 closure | Tag `phase3c20-governance-closure` |
| C25 WP2.0 | SATISFIED |
| Commit / push / tag by this document | **NOT AUTHORIZED** (documentation record only) |

```text
AUTHORIZED WITH CONDITIONS — scoped CommercialBrief application-layer
implementation only.

Does NOT authorize Runtime Expansion, C20 changes, C22 execution,
autonomous commercial execution, live provider invocation, or AIJob
executor work.
```

---

## 1. Authorization Purpose

This authorization permits **scoped WP2.2 application-layer implementation
only**.

It does **not** authorize:

- Runtime Expansion
- C20 changes
- C22 execution
- autonomous commercial execution

Implementation may begin only inside the Exact Implementation Allowlist
(§5) and under the Implementation Conditions (§9). Delivery freeze still
requires Verification Review.

---

## 2. Approved Implementation Scope

Authorize only the **CommercialBrief Application Layer**.

**Allowed:**

- Entity implementation
- Metadata
- Services
- ACL
- Review lifecycle
- Provenance fields
- Tests

Scope class: C25 CommercialIntelligence application artifacts for
`CommercialBrief` — not C20 runtime, not C22 execution.

---

## 3. Generation Boundary Authorization

**Allowed:**

- proposal artifact persistence
- manual / test fixture proposal creation
- evidence-linked draft creation

**Forbidden:**

- live AI provider invocation
- AIJob execution
- automatic generation pipeline

**AI remains:** proposal source only.

```text
"Generation" under this authorization =
  governed proposal artifact formation (fixture / manual / stub content OK)

"Generation" ≠ provider invoke
"Generation" ≠ AIJob executor
"Generation" ≠ outbound generation pipeline
```

Live model calls require a separate Runtime Expansion / execution
authorization outside WP2.2. This document does not grant that path.

---

## 4. Lifecycle Authorization

**Allowed lifecycle:**

```text
GENERATED
    ↓
REVIEWED
    ↓
ACCEPTED
 or
DISMISSED
```

Human reviewer remains authority.

**Forbidden:**

- automatic acceptance
- automatic rejection
- AI lifecycle mutation

AI/system may create a proposal artifact under human-initiated request
governance. AI/system may **not** accept, dismiss, or override review.

---

## 5. Exact Implementation Allowlist

Future allowed areas (implementation may create/modify **only** within
these trees, and only for CommercialBrief WP2.2 purpose):

### crm-extension — CommercialIntelligence module

| Area | Allowlisted path pattern |
| --- | --- |
| Entity | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Entities/CommercialBrief.php` |
| entityDefs | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/entityDefs/CommercialBrief.json` |
| scopes | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/scopes/CommercialBrief.json` |
| clientDefs | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/clientDefs/CommercialBrief.json` |
| recordDefs (if required) | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/recordDefs/CommercialBrief.json` |
| ACL / roles (CommercialBrief only) | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Resources/metadata/aclDefs/CommercialBrief.json` and CommercialBrief-scoped role/permission metadata under the same module |
| Controllers (read/review actions only; no outbound) | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Controllers/CommercialBrief.php` |
| Services (application-layer review / transition / validation / proposal persistence) | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Services/CommercialBrief*.php`, `Brief*Service.php`, `Brief*Guard.php`, `Brief*Validator.php` under the same module |
| Hooks / guards (immutability / review-status integrity) | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Hooks/CommercialBrief/**` |
| Client views (read / review surfaces only) | `crm-extension/files/client/custom/modules/commercial-intelligence/src/views/**` related to CommercialBrief |
| Module registration / Binding needed for above | `crm-extension/files/custom/Espo/Modules/CommercialIntelligence/Binding.php` (CommercialBrief wiring only; no C20/C22 expansion) |

### Tests

| Area | Allowlisted path pattern |
| --- | --- |
| CRM tests | `crm-extension/tests/test_phase3c25_wp2_2_*.py` |
| Fixture data (proposal stubs only) | `crm-extension/tests/fixtures/**` used exclusively by WP2.2 suites |

### Explicitly must exclude from allowlist

- All C20 runtime files (`crm-extension/.../AIPlatform/**` production runtime expansion; `chitu-connector/**` execution paths)
- Any path under C22 prospecting/execution modules
- `docs/adr/C20_INVARIANT_REGISTRY.md` and other registry flips

If a required file path is missing from this allowlist, stop and obtain an
allowlist amendment before touching it. Do not expand silently.

---

## 6. Forbidden Files / Areas

### C20

- Runtime Charter implementation / Runtime Expansion
- Provider execution
- Capability runtime expansion
- `docs/adr/C20_INVARIANT_REGISTRY.md` flips
- `chitu-connector/**` execution / adapter callout changes for live invoke
- AIPlatform dispatch / connector / HTTP outbound changes for WP2.2 generation

### Runtime

- connector
- HTTP
- queue
- worker
- scheduler
- retry
- cancellation
- reservation

### C22

- ProspectRun
- outreach execution
- action ledger mutation
- ProspectCandidate lifecycle ownership / advancement

### Other

- autonomous Lead creation / conversion
- automatic Opportunity creation
- CRM Core lifecycle mutation as a side effect of Accept/Dismiss

---

## 7. Test Authorization

Allow only:

### Boundary tests

- no runtime execution
- no connector invocation
- no provider invoke / HTTP outbound / worker / queue / scheduler

### Lifecycle tests

- human review required for ACCEPT / DISMISS
- no autonomous GENERATED → commercial-effect transition

### ACL tests

- permissions enforced
- AI/system cannot accept / dismiss / override

### Provenance tests

- evidence retained
- capability / purpose references present
- incomplete provenance rejected for acceptance

Tests must use fixture / manual proposal content. Tests must not call live
providers or AIJob executors.

---

## 8. Rollback Rules

Rollback must preserve:

- C20 **CLOSED** state (`phase3c20-governance-closure`)
- Package A **RELEASED** state
- WP2.0 dependency satisfaction state

Rollback cannot:

- reopen C20
- activate invariants
- enable runtime
- alter C22 execution ownership

Rollback may revert only WP2.2 allowlisted application-layer artifacts
delivered under this authorization.

---

## 9. Implementation Conditions

1. **No files outside allowlist.** Any path not listed in §5 requires a
   documented allowlist amendment before change.
2. **No runtime path introduced.** No connector, HTTP outbound, provider
   invoke, AIJob executor, worker, queue, scheduler, retry, cancellation,
   or reservation path.
3. **No C22 lifecycle mutation.** Accept/Dismiss must not advance
   ProspectRun, outreach, or action ledger.
4. **Verification review required before freeze.** Implementation is
   **READY TO START**, not frozen; freeze requires independent Verification
   Review PASS.

Additional conditions:

5. Proposal content for delivery/tests is fixture, manual, or stub only
   under this authorization.
6. Human reviewer remains final authority for ACCEPT / DISMISS.
7. Provenance fields (evidence, generation context, capability, purpose)
   are mandatory for acceptance governance.

---

## 10. Final Authorization State

| Scope | Status |
| --- | --- |
| C20 Runtime Lite | **CLOSED** |
| C20 Package A | **RELEASED** |
| C25 WP2.0 | **SATISFIED** |
| WP2.2 Charter | **APPROVED** |
| WP2.2 Plan | **APPROVED** |
| WP2.2 Implementation Authorization | **AUTHORIZED WITH CONDITIONS** |
| WP2.2 Implementation | **READY TO START** |
| Runtime Expansion | **NOT AUTHORIZED** |
| Invariant Activation | **NOT DONE** |

---

*End of Phase3C25 WP2.2 Implementation Authorization.*
