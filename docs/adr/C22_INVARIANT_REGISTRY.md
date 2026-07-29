# C22 Invariant Registry

| Field | Value |
| --- | --- |
| **Document Type** | Governance Registry |
| **Status** | Ratified Reference Artifact |
| **Owner** | Phase3C22 Governance |
| **Scope** | Autonomous Prospecting Execution Governance |
| **Related** | `docs/PHASE3C22_CHARTER.md` |
| **Source** | `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md` |

This registry is the formal governance reference for the C22 invariant set. The
registry artifact is ratified; individual invariants remain
**DOCUMENTATION_ONLY** until their stated activation triggers and enforcement
requirements are satisfied. This document authorizes no implementation.

## Lifecycle

```text
DOCUMENTATION_ONLY -> PROPOSED -> ACTIVE -> SUPERSEDED
```

Activation requires the designated owning ADR, the stated activation trigger,
and a specified contract-test path. An invariant is never silently deleted;
replacement is by supersession.

---

## 1. Identity Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-ID-001 | `ProspectCandidate` is an execution identity. It is not `Lead` and cannot be auto-promoted to `Lead`. | ADR-C22-001 | Service guard + contract test | DOCUMENTATION_ONLY | `ProspectCandidate` entity creation |
| C22-INV-ID-002 | `ProspectCandidate` is not `ProspectPool`. It is a distinct execution identity that may reference `ProspectPool` for intelligence context but does not duplicate, replace, or override it. | ADR-C22-001 | Service guard + contract test | DOCUMENTATION_ONLY | `ProspectCandidate` entity creation |
| C22-INV-ID-003 | C22 cannot mutate CRM identity. `ProspectCandidate` cannot be auto-promoted to `Lead`, and C22 cannot auto-create `Lead`, `Opportunity`, or `Account`. | ADR-C22-001, ADR-C22-006 | Service guard + contract test | DOCUMENTATION_ONLY | `ProspectCandidate` entity creation + `ActionGate` service implementation |

---

## 2. Execution Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-EX-001 | Every executable action that crosses the C22 execution boundary must pass through `ActionGate`. AI, `AutomationRule`, or any automated process cannot bypass `ActionGate`. | ADR-C22-002 | Service guard + contract test | DOCUMENTATION_ONLY | `ActionGate` service implementation |
| C22-INV-EX-002 | `ActionGate` requires human approval as the default and permanent execution gate. Any future rule-based approval requires a separately ratified Charter Amendment. | ADR-C22-002 | Service guard + Charter governance | DOCUMENTATION_ONLY | `ActionGate` service implementation |
| C22-INV-EX-003 | Every execution action creates an `ExecutionLedger` record. `ExecutionLedger` is append-only: no update or delete path exists for any role. | ADR-C22-003 | DB-level (`REVOKE UPDATE, DELETE` on table) + ACL | DOCUMENTATION_ONLY | `ExecutionLedger` entity creation |
| C22-INV-EX-004 | `ProspectRun` is an execution container, not an AI reasoning object. It does not compute scores, rankings, priorities, or qualifications. | ADR-C22-008 | Service guard + contract test | DOCUMENTATION_ONLY | `ProspectRun` entity creation |
| C22-INV-EX-005 | C22 execution chain terminates at `ReplyDetection`. No C22 action may cross into CRM Core lifecycle (Lead creation, Opportunity creation, sales stage mutation) without explicit human operator decision. | ADR-C22-006 | Service guard + contract test | DOCUMENTATION_ONLY | `ReplyDetection` service implementation |
| C22-INV-EX-006 | C22 must not write to C19-frozen entities or their lifecycle fields (`SendExecution`, `ReplyEvent`, `Quote`, `Approval`, `DraftApproval`). | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |

---

## 3. Provider Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-PR-001 | No CRM PHP code opens an HTTP connection to any provider endpoint. All outbound provider I/O routes through the C20 connector as the sole egress point. | ADR-C22-004 | Contract test (static analysis + runtime guard) | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-PR-002 | C22 does not hold provider credentials in PHP code, configuration, or database. All secrets follow C20 `ProviderCredential` custody model. | ADR-C22-004 | Contract test + audit | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-PR-003 | C22 does not own or create C20 execution records (`AIJob`, `AIRequestLog`). C22 requests capability execution through C20 interfaces. | ADR-C22-004 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-PR-004 | C22's `EmailDeliveryProvider` port inherits the deferred C20 responsibility. Provider adapters own runtime communication; CRM owns policy, authorization, and audit. | ADR-C22-004 | Design-level (adapter contract) | DOCUMENTATION_ONLY | `EmailDeliveryProvider` port definition |

---

## 4. Retry / Loop Prevention Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-RETRY-001 | Every execution action has a finite retry budget. Budget exhaustion moves the action to a terminal `FAILED` state requiring operator intervention. No infinite retry. | ADR-C22-005 | `ProspectRun` enforcement | DOCUMENTATION_ONLY | `ProspectRun` service implementation |
| C22-INV-RETRY-002 | The maximum execution chain depth is bounded at 7. No autonomous step beyond the terminal boundary. The chain does not self-extend. | ADR-C22-007 | `ProspectRun` enforcement | DOCUMENTATION_ONLY | `ProspectRun` service implementation |
| C22-INV-RETRY-003 | After any execution failure, `ActionGate` must be re-entered before retry. No automatic retry path bypasses `ActionGate`. | ADR-C22-005, ADR-C22-007 | Service guard | DOCUMENTATION_ONLY | `ActionGate` + `ProspectRun` service implementation |
| C22-INV-RETRY-004 | The following autonomous execution cycles are explicitly forbidden and prevented by structural controls: Send-Retry Loop, Search-Research-Send Infinite, Failure-Search Regeneration, AutomationRule Bypass, Provider Direct Replay, and Auto-Promotion Loop. | ADR-C22-007 | Contract test (each cycle enumerated and tested) | DOCUMENTATION_ONLY | C22 execution chain implementation |
| C22-INV-RETRY-005 | Every execution failure must be classified as Transient, Permanent, or Governance before any retry decision. Permanent and Governance failures are terminal; automatic retry is forbidden. Unclassified failures default to PERMANENT. | ADR-C22-005 | Service guard | DOCUMENTATION_ONLY | C22 execution chain implementation |
| C22-INV-RETRY-006 | Every `OutreachExecution` carries a caller-supplied idempotency key, persisted before dispatch. Retry with the same key does not duplicate work or spend. | ADR-C22-009 | Persistence guard (UNIQUE constraint on idempotency key) | DOCUMENTATION_ONLY | `OutreachExecution` entity creation |
| C22-INV-RETRY-007 | Rate-limit retry requires controlled backoff. Immediate retry after a `RATE_LIMIT` failure is forbidden. | ADR-C22-005 Rate-Limit Retry Governance Addendum | Service guard + `ProspectRun` / action scheduler | DOCUMENTATION_ONLY | C22 execution retry scheduler implementation |
| C22-INV-RETRY-008 | Rate-limit retry requires a maximum attempt / wait window. Infinite waiting on continuous 429 / rate-limit responses is forbidden. | ADR-C22-005 Rate-Limit Retry Governance Addendum | `ProspectRun` enforcement + action wait-window counter | DOCUMENTATION_ONLY | C22 execution retry scheduler implementation |
| C22-INV-RETRY-009 | Rate-limit retry cannot bypass `ProspectRun` execution timeout or Action execution timeout. Rate-limit handling must consume / respect execution time budget. | ADR-C22-005 Rate-Limit Retry Governance Addendum | `ProspectRun` timeout + action timeout guards | DOCUMENTATION_ONLY | `ProspectRun` + action timeout enforcement implementation |

---

## 5. C21 Boundary Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-C21-001 | C22 consumes C21 intelligence records (`ResearchEvidence`, `AIQualificationInsight`, `HumanFeedback`, `IntelligenceAggregate`) as read-only context. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-C21-002 | C22 must not modify C21 intelligence records. C21 owns intelligence governance; C22 may not create, update, or delete `ResearchEvidence`, `AIQualificationInsight`, `HumanFeedback`, or `IntelligenceAggregate`. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-C21-003 | C22 does not create a parallel intelligence store. AI Research output that constitutes intelligence evidence must route through C21 `ResearchEvidenceGovernanceService`. | ADR-C22-006, ADR-C22-001 | Service guard + contract test | DOCUMENTATION_ONLY | C22 AI Research step implementation |

---

## 6. CRM Boundary Invariants

| ID | Statement | Owning ADR | Enforcement | Status | Activation Trigger |
| --- | --- | --- | --- | --- | --- |
| C22-INV-CRM-001 | C22 must not auto-create `Lead` from `ProspectCandidate` or any other C22 entity. `Lead` creation is human-gated and owned by CRM Core. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-CRM-002 | C22 must not auto-create `Opportunity`. Opportunity is CRM Core lifecycle authority. C22 has no path to create, modify, or transition Opportunity. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-CRM-003 | C22 must not modify sales stage, pipeline phase, revenue association, or any CRM Core lifecycle field on `Lead`, `Opportunity`, or `Account`. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |
| C22-INV-CRM-004 | C22 must not write to `canonical_score`. `canonical_score` is owned by Chitu; the AGENTS.md / CLAUDE.md prohibition applies to C22 as it does to all other layers. | ADR-C22-006 | Contract test | DOCUMENTATION_ONLY | C22 service implementation |

---

## 7. Invariant Summary

| Category | Count |
| --- | ---: |
| Identity | 3 |
| Execution | 6 |
| Provider | 4 |
| Retry / Loop Prevention | 9 |
| C21 Boundary | 3 |
| CRM Boundary | 4 |
| **Total** | **29** |

## References

- `docs/PHASE3C22_CHARTER.md`
- `docs/audit/C22_INVARIANT_REGISTRY_DRAFT.md`
- `docs/adr/C20_INVARIANT_REGISTRY.md`
- `docs/adr/C21_INVARIANT_REGISTRY.md`
