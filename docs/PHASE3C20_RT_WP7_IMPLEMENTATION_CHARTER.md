# Phase3C20 RT-WP7 Implementation Charter — Runtime Guards Foundation Lite

| Field | Value |
| --- | --- |
| Document Type | RT-WP7 Runtime Guards Foundation Lite Charter (planning only) |
| Work package | RT-WP7 Lite — Runtime Guards Foundation |
| Charter path | `docs/PHASE3C20_RT_WP7_IMPLEMENTATION_CHARTER.md` |
| Status | RATIFIED — STATUS SYNCHRONIZED; implementation not authorized |
| Date | 2026-08-03 |
| Governing baseline | C20 governance freeze `928aa5f734f8d7f643cdb45a7549fed7ada0c400` |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 | COMPLETED + TAGGED (`phase3c20-rt-wp2-implementation-completed`) |
| RT-WP3 | COMPLETED + TAGGED (`phase3c20-rt-wp3-implementation-completed`) |
| RT-WP4 | COMPLETED + TAGGED (`phase3c20-rt-wp4-implementation-completed`) |
| RT-WP5 | COMPLETED + TAGGED (`phase3c20-rt-wp5-implementation-completed`) |
| RT-WP6 | COMPLETED + TAGGED (`phase3c20-rt-wp6-implementation-completed` → `0eb6dda2c7e2d3cced0c9da42bc2e835ce505703`) |
| Independent ratification review | RATIFIED (independent review PASS) |
| Execution mode | Charter authoring only — no runtime, metadata, entity, service, test, connector, or C25 change |
| Implementation authorization | **NOT AUTHORIZED** |
| Commit / push / tag | **NOT AUTHORIZED** by this charter |

```text
This charter defines the minimal Runtime Guards Foundation Lite planning
contract. It creates no code, modifies no runtime, authorizes no
implementation, and does not release full Runtime Charter §26 invariant
activation / registry flips, RT-WP8, or C25.

Guard ≠ authorization engine.
Guard ≠ workflow engine.
Guard ≠ security gateway.
```

---

## 1. Scope

RT-WP7 Lite covers exactly seven surfaces:

| # | Allowed surface | Meaning |
| --- | --- | --- |
| 1 | Capability validation | Accept only the frozen four-value portfolio; reject unknown / `COMMERCIAL_BRIEF` |
| 2 | Purpose validation | Reject unregistered / empty / malformed purpose identifiers (fail-closed) |
| 3 | ProviderBinding reference validation | Require non-secret binding reference presence/shape; do not resolve credentials |
| 4 | State boundary validation | Accept only RT-WP4 Lite foundation states; reject engine/deferred states |
| 5 | Failure boundary validation | Accept only RT-WP5 Lite failure codes; reject retry/provider-execution labels |
| 6 | Ownership metadata boundary validation | Accept only RT-WP6 Lite reservation intents / ownership rules; reject lock labels |
| 7 | Invalid input rejection | Fail-closed reject of secret-shaped / execution-control / C25-driven payloads |

```text
Runtime Guards Foundation Lite only.
Provides runtime validation guards only.
Does not grant permissions, run workflows, or execute outbound calls.
```

### 1.1 Purpose

Provide **fail-closed runtime boundary validation** that composes already-
completed Lite foundations (WP2–WP6) into a single guard surface for invalid
input rejection — without becoming an ACL/permission system, workflow engine,
or security gateway.

### 1.2 Non-purpose

Deliver ACL systems, permission/role engines, workflow engines, queue/worker/
scheduler control, retry/recovery, connector execution, HTTP outbound, provider
authentication, secret/credential handling, AIJob lifecycle mutation, C25 /
Opportunity / sales authority, or invariant registry activation.

### 1.3 Preconditions

| Predecessor | Status | Lite dependency |
| --- | --- | --- |
| RT-WP2 | COMPLETED + TAGGED | ProviderBinding policy consumable; not redesigned |
| RT-WP3 Lite | COMPLETED + TAGGED | Dispatch boundary consumable; not redesigned |
| RT-WP4 Lite | COMPLETED + TAGGED | Foundation state vocabulary consumable |
| RT-WP5 Lite | COMPLETED + TAGGED | Failure metadata vocabulary consumable |
| RT-WP6 Lite | COMPLETED + TAGGED | Reservation/ownership metadata consumable |
| Four-value portfolio | Frozen | Unchanged |
| C20-INV-02 / C20-INV-03 | ACTIVE | Unchanged |
| C20-INV-04–13 | DEFERRED | No activation by this charter |

### 1.4 Lite vs full Runtime Charter §26

| Surface | This Lite charter | Full Runtime Charter §26 |
| --- | --- | --- |
| Fail-closed runtime boundary guards | **In scope** | Prerequisite / related |
| Compose WP2–WP6 validation contracts | **In scope** | Related |
| Invariant registry status flips (INV-05–11) | **Out of scope** | In scope (governance-status) |
| Freeze evidence / C25 dependency closure | **Out of scope** | RT-WP8 |
| INV activation claims | **Not claimed** | Post-evidence governance action |

```text
Lite label: RT-WP7 Lite — Runtime Guards Foundation

Full Runtime Charter §26 (Invariant Activation and Runtime Verification)
remains a separate, deferred surface and is NOT authorized by this Lite charter.
```

### 1.5 Architecture relationship

```text
Consumes:  RT-WP2, RT-WP3, RT-WP4, RT-WP5, RT-WP6 (consume only)
Provides:  runtime validation guards only
Does not:  authorize roles, orchestrate workflows, execute providers
```

---

## 2. Guard Philosophy

```text
Guard ≠ authorization engine
Guard ≠ workflow engine
Guard ≠ security gateway
```

| Principle | Statement |
| --- | --- |
| Fail-closed | Unknown / illegal / secret-shaped input rejects; never soft-pass |
| Compose, do not replace | Guards reuse WP2–WP6 vocabularies; do not invent parallel enums |
| Validate, do not decide policy ownership | EspoCRM ACL / Portal remain authoritative for permissions |
| Validate, do not execute | Guards never invoke Connector, Jobs, HTTP, or lock engines |
| Non-secret only | No credential resolution; no secret-bearing payloads |
| No registry mutation | INV-04–13 remain DEFERRED; no status flips |

---

## 3. Validation Boundaries

### 3.1 Capability

| Rule | Behavior |
| --- | --- |
| Value in `{RESEARCH_EVIDENCE, QUALIFICATION_INSIGHT, DRAFT_ASSISTANCE, REPLY_ASSISTANCE}` | Accept |
| `COMMERCIAL_BRIEF` or unknown | Reject fail-closed |

### 3.2 Purpose

| Rule | Behavior |
| --- | --- |
| Empty / whitespace / missing purpose | Reject |
| Malformed / unregistered purpose (per Lite contract) | Reject |
| Valid non-secret purpose identifier shape | Accept for guard purposes (registration ownership remains WP3) |

### 3.3 ProviderBinding reference

| Rule | Behavior |
| --- | --- |
| Missing binding reference when required by guard input contract | Reject |
| Secret-shaped credential fields present | Reject |
| Non-secret reference present | Accept shape only — **do not resolve** |

### 3.4 State boundary (RT-WP4)

| Rule | Behavior |
| --- | --- |
| One of six Lite states | Accept |
| `QUEUED` / `RUNNING` / `RETRY_PENDING` / `CANCELLED` / provider states | Reject |

### 3.5 Failure boundary (RT-WP5)

| Rule | Behavior |
| --- | --- |
| One of five Lite failure codes | Accept |
| Retry/provider taxonomy-as-executor labels | Reject |

### 3.6 Ownership metadata boundary (RT-WP6)

| Rule | Behavior |
| --- | --- |
| One of five Lite reservation intents + owner rules | Accept |
| Lock/lease/queue/worker reservation labels | Reject |

---

## 4. Fail-Closed Rules

| Condition | Outcome |
| --- | --- |
| Unknown capability / purpose / state / failure code / reservation intent | Reject |
| Secret-shaped fields or values | Reject |
| Execution-control fields (`queue`, `worker`, `retry`, `lock`, `scheduler`) | Reject |
| C25 / Opportunity / sales-driven authority fields as guard inputs | Reject |
| Guard “success” implying permission grant | Forbidden interpretation |
| Guard “success” implying provider dispatch | Forbidden interpretation |

```text
Reject means validation failure.
Reject does not mean ACL denial event emission, workflow transition, or retry.
```

---

## 5. Security Boundary

| Requirement | Intent |
| --- | --- |
| No CRM provider HTTP | Preserve C20-INV-03 |
| No secret handling / credential resolution | Guard inputs/outputs non-secret only |
| No provider authentication | Forbidden |
| No ACL/role replacement | Reuse EspoCRM ACL; do not invent parallel authz |
| No connector / adapter invoke | Forbidden |
| No queue / worker / scheduler / retry side effects | Forbidden |
| Portal / admin no-bypass of validation when later wired | Required for mutation paths |
| No C25 audit rewrite | C25 owns its audit |

Invariant posture preserved:

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED (no early activation)
```

---

## 6. Explicit Exclusions

| Forbidden surface | Reason |
| --- | --- |
| ACL / permission / role system | Authorization engine — excluded |
| Workflow engine | Execution control — excluded |
| Queue / worker / scheduler | Execution engine — excluded |
| Retry / recovery | Deferred / excluded |
| Connector execution / HTTP outbound | Forbidden |
| Provider authentication / secret / credential handling | Forbidden |
| AIJob lifecycle mutation | Excluded |
| Invariant registry flips (INV-05–11) | Full §26 / governance — excluded |
| RT-WP8 freeze / C25 closure | Deferred |
| C25 / Opportunity / sales CRM authority | C25 WP2.2 NO GO |
| Redesign of WP2–WP6 allowlisted implementations | Consume only |

```text
STOP conditions:
- Scope expansion into ACL/workflow/execution
- C25 entry
- INV registry activation claims
- Provider / Connector modification
- Git failure under authorized commit steps
```

---

## 7. Test Requirements

When implementation is separately authorized, tests must prove guard contracts
**without** network I/O, connector invocation, ACL system replacement, or
workflow execution:

| Category | Coverage |
| --- | --- |
| Contract | Guard surfaces exist; validation result representation non-secret |
| Positive | Valid capability/purpose/binding-ref/state/failure/ownership inputs accept |
| Negative | Unknown values, `COMMERCIAL_BRIEF`, secrets, lock/queue/retry markers reject |
| Isolation | No ACL engine / workflow / connector / HTTP / Jobs markers in allowlist |
| Regression | RT-WP2–WP6 Lite tests remain green; INV-02/03 ACTIVE; INV-04–13 DEFERRED |

No Lite test may resolve secrets, invoke Connector, flip invariant registry
rows, or claim §26 / INV-05–11 activation exit.

---

## 8. Exit Criteria

### 8.1 Charter exit (this document)

Complete for independent ratification review when:

1. Scope is explicit (§1).
2. Guard philosophy is explicit (§2).
3. Validation boundaries are explicit (§3).
4. Fail-closed rules are explicit (§4).
5. Security boundary is explicit (§5).
6. Exclusions are explicit (§6).
7. Test requirements are explicit (§7).
8. Exit criteria are explicit (§8).
9. Implementation remains **NOT AUTHORIZED** until separate authorization +
   Foundation Review PASS.

### 8.2 Implementation exit (future; not claimed now)

1. Independent Plan Review and Foundation Review PASS with exact allowlist.
2. Implemented surfaces match §1 only.
3. Fail-closed guards proven; ACL/workflow/execution absent.
4. No connector / HTTP / worker / retry / secret / C25 coupling.
5. Independent Implementation Review PASS.
6. Separate commit/push/tag authorization obtained.

Full Runtime Charter §26 invariant activation and INV registry flips remain
**out of Lite scope**.

---

## Authorization Boundary

```text
Charter status:
RATIFIED

RT-WP7 Lite Implementation:
NOT AUTHORIZED

Full RT-WP7 / Runtime Charter §26 Invariant Activation:
NOT AUTHORIZED

Any runtime code:
NOT AUTHORIZED

RT-WP8:
NOT AUTHORIZED

C25 WP2.2:
NO GO
```

Charter ratification approves **planning direction only**. It does not start
implementation, create allowlists, or authorize commit/push/tag.
Implementation remains NOT AUTHORIZED until a separate implementation
authorization is issued.

| Item | Status |
| --- | --- |
| RT-WP2–RT-WP6 Lite | COMPLETED + TAGGED |
| RT-WP7 Lite Charter | RATIFIED — STATUS SYNCHRONIZED |
| RT-WP7 Lite Implementation | NOT AUTHORIZED |
| Full §26 Invariant Activation | NOT AUTHORIZED |
| RT-WP8 | NOT AUTHORIZED |
| Runtime Code | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |

---

## Final Decision

```text
RATIFIED — STATUS SYNCHRONIZED
```

Independent ratification review returned **PASS** / **RATIFIED**. No BLOCKER,
HIGH, MEDIUM, or LOW finding alters scope. Charter status is therefore
synchronized to RATIFIED. Implementation remains NOT AUTHORIZED.

```text
Next Task:
Phase3C20 RT-WP7 Charter Documents Commit and Push
```

---

## References

1. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` (§26 — full activation deferred)
2. `docs/PHASE3C20_RT_WP6_IMPLEMENTATION_CHARTER.md`
3. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md`
4. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md`
5. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
6. `docs/PHASE3C20_RT_WP2_IMPLEMENTATION_CHARTER.md`
7. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
8. `docs/adr/C20_INVARIANT_REGISTRY.md`
9. Live tags: `phase3c20-rt-wp6-implementation-completed` … `phase3c20-rt-wp2-implementation-completed`
10. Live HEAD at charter drafting: `0eb6dda2c7e2d3cced0c9da42bc2e835ce505703`

---

*This charter is a planning document. It creates no production runtime change,
modifies no RT-WP2–WP6 implementation, stages no commit, and authorizes no
code. Runtime Guards Foundation Lite implementation begins only under a
separate, explicit authorization.*
