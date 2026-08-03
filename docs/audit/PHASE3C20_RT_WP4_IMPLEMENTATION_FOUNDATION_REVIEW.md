# Phase3C20 RT-WP4 Implementation Foundation Review

| Field | Value |
| --- | --- |
| Review mode | Foundation Gate Review before RT-WP4 Lite implementation |
| Date | 2026-08-03 |
| Review target | RT-WP4 Lite Execution State Foundation Plan + Authorization + Charter |
| Verdict | **READY FOR IMPLEMENTATION** |
| Implementation state | NOT STARTED → **READY TO START** (Lite only) |
| Code / metadata / entity / production test body | NONE — documentation gate artifacts only |
| Commit / push / tag | NOT AUTHORIZED |

```text
This review is a documentation artifact. It writes no implementation code,
modifies no ProviderBinding / RT-WP3 / connector / C25 surface, and performs
no commit, push, or tag. Repository changes are limited to the RT-WP4
authorization evidence record and this Foundation Review document.
```

---

## 1. Executive verdict

RT-WP4 Lite satisfies the Foundation Gate for **Execution State Foundation
Lite** only. Scope is exactly five authorized surfaces; the six-state model
remains non-engine; RT-WP3 boundary is consume-only; security and deferred WP
isolation are explicit; the exact file allowlist is ratified below.

```text
READY FOR IMPLEMENTATION
```

Full Runtime Charter §23 cancel-reason / `CANCELLED` remains **not authorized**.

---

## 2. Evidence checked (R1 Authorization chain)

| Evidence | Result |
| --- | --- |
| RT-WP4 Lite Charter | RATIFIED + TAGGED (`phase3c20-rt-wp4-charter-ratified` → `b74e5d0…`) |
| Independent Charter Review | PASS / RATIFIED |
| Implementation Authorization | AUTHORIZED WITH CONDITIONS (recorded) |
| Implementation Plan | Present; five Lite surfaces; candidates only |
| Independent Plan Review | PASS WITH INFORMATIONAL NOTES; no BLOCKER/HIGH/MEDIUM |
| RT-WP2 / RT-WP3 | COMPLETED + TAGGED |
| Runtime Implementation Charter | §23 cancel-reason deferred from Lite |
| C20 Invariant Registry | INV-02/03 ACTIVE; INV-04–13 DEFERRED |
| Git HEAD | `b74e5d01d6f4d799a79945d38580ee8c47bd4a24` |

**R1 Authorization chain: PASS**

---

## 3. Foundation gate criteria

| ID | Criterion | Result |
| --- | --- | --- |
| R1 | Authorization chain complete | **PASS** |
| R2 | Exact file allowlist finalized | **PASS** (§4) |
| R3 | Data contract defined | **PASS** (§5) |
| R4 | Security boundary | **PASS** (§6) |
| R5 | Test requirements | **PASS** (§7) |
| R6 | Invariants INV-02/03 ACTIVE; INV-04–13 DEFERRED | **PASS** |

---

## 4. Exact implementation allowlist (ratified) — R2

```text
Implementation may create or modify ONLY the following paths.
Any other path requires a new authorization.
```

Base prefix for CRM PHP rows:

`crm-extension/files/custom/Espo/Modules/AIPlatform/`

| # | Path | Purpose |
| --- | --- | --- |
| 1 | `Services/AIFoundationState.php` | Closed six-state vocabulary constants (`REQUESTED`, `VALIDATING`, `READY`, `BLOCKED`, `COMPLETED`, `FAILED`) plus helpers to validate membership. No execution, no HTTP, no Jobs. |
| 2 | `Services/AIFoundationStateService.php` | Transition API; apply fail-closed edges; map consume-only RT-WP3 Lite outcomes (eligibility/boundary signals) into state updates; assemble audit-friendly non-secret representation. **Must not** invoke Connector, mutate ProviderBinding, schedule jobs, or resolve secrets. |
| 3 | `Services/AIFoundationStateTransitionGuard.php` | Reject invalid states, illegal transitions, and forbidden mutation patterns (fail-closed policy guard). Not a worker/queue component. |
| 4 | `crm-extension/tests/test_phase3c20_rt_wp4_foundation_state.py` | Contract, transition, negative, isolation, and RT-WP2/RT-WP3 regression evidence. No network I/O; no connector invoke; no secret resolution. |

**Allowlist count:** exactly **4** rows.

### 4.1 Explicitly excluded

| Path / class | Exclusion |
| --- | --- |
| Any `Jobs/*` / worker / queue / scheduler | Forbidden |
| Outbound `Api/*` execution routes | Forbidden |
| Any `chitu-connector/**` change | Forbidden |
| Any `ProviderBinding*` change | Consume only |
| `CompletionCapability` / connector portfolio files | Forbidden |
| AIRequestLog outbound producer | Forbidden |
| AIJob cancel-reason / `CANCELLED` field packs (§23) | Forbidden |
| RT-WP3 Lite allowlisted files (`AIDispatch*`) | **No modification** in this Lite gate (side-by-side consume-only) |
| Any C25 / Opportunity / sales files | Forbidden |
| `Binding.php` | Excluded unless separately authorized |

### 4.2 Behavior lock

`AIFoundationStateService` may only:

1. accept a non-secret state transition request / RT-WP3 outcome signal;
2. validate current→next against the ratified matrix;
3. reject unknown states and illegal edges;
4. produce/update audit-friendly representation;
5. stop without connector/Jobs/retry/reservation.

Persistence form for this Lite gate: **service-owned in-memory / returned record
contract** sufficient for unit/static tests. Introducing entity metadata or
AIJob field attachment requires a **new** authorization (not in this allowlist).

---

## 5. Data contract (R3)

### 5.1 State representation

| Field | Rule |
| --- | --- |
| `foundationState` | Exactly one of the six Lite states |
| `requestIdentity` | Non-secret correlation reference |
| `previousState` | Optional prior legal state |
| `boundaryReference` | Optional RT-WP3 boundary identity reference (no secrets) |

### 5.2 Transition validation

Allowed edges only:

```text
REQUESTED  → VALIDATING
VALIDATING → READY | BLOCKED | FAILED
READY      → COMPLETED | FAILED
```

`BLOCKED`, `COMPLETED`, and `FAILED` are terminal under Lite.
Unknown states and all other edges reject fail-closed.

### 5.3 Audit metadata (non-secret only)

| Field | Rule |
| --- | --- |
| `transitionReasonCode` | Bounded non-secret reason class (policy / validation / close) |
| `provenanceReference` | Actor / policy-version references only |
| `updatedAt` | Server-owned timestamp when recorded |

Forbidden in representation: secrets, tokens, credentials, provider payloads,
queue/retry/reservation controls, C25 mutation instructions.

---

## 6. Security boundary (R4)

| Requirement | Status |
| --- | --- |
| No secret handling | Required |
| No credential resolution | Required (`credentialReference` may be referenced only if already present on RT-WP3 boundary; never resolved) |
| No provider authentication | Required |
| No CRM provider HTTP | Required (C20-INV-03) |
| No Connector / adapter invoke | Required |
| Admin no-bypass of transition validation | Required |

---

## 7. Test requirements (R5)

| Category | Required proofs |
| --- | --- |
| Valid transitions | Every allowed edge succeeds |
| Invalid transition rejection | Illegal edges and unknown states reject |
| State validation | Only six Lite values accepted |
| Boundary isolation | No connector/HTTP/Jobs/queue/retry/reservation/C25 markers in allowlist |
| WP3 regression | RT-WP3 Lite dispatch foundation tests remain green |
| WP2 regression | RT-WP2 ProviderBinding tests remain green |
| Invariants | INV-02/03 ACTIVE; INV-04–13 DEFERRED unchanged |

---

## 8. Invariants (R6)

```text
C20-INV-02 ACTIVE
C20-INV-03 ACTIVE
C20-INV-04–13 DEFERRED
```

No registry status flips by this gate or by Lite implementation.

---

## 9. Findings

| Severity | Finding | Disposition |
| --- | --- | --- |
| BLOCKER | None | — |
| HIGH | None | — |
| MEDIUM | None | — |
| LOW | Authorization evidence file was missing before this gate; created as Foundation evidence. | Closed by this gate. |
| INFORMATIONAL | Persistence is service/record-contract only; no entityDefs/AIJob merge in this allowlist. | Prevents §23 / engine-status coupling. |
| INFORMATIONAL | RT-WP3 files not modified; consume-only side-by-side. | Matches Plan default. |
| INFORMATIONAL | Future WP5 Lite “failure metadata only” remains out of scope. | Preserved. |

```text
BLOCKER: NONE
HIGH: NONE
MEDIUM: NONE
LOW: 1
INFORMATIONAL: 3
```

---

## 10. Final authorization state

| Item | Status |
| --- | --- |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 / RT-WP3 | COMPLETED + TAGGED |
| RT-WP4 Lite Charter | RATIFIED + TAGGED |
| RT-WP4 Lite Authorization | AUTHORIZED WITH CONDITIONS |
| RT-WP4 Lite Plan Review | PASS WITH INFORMATIONAL NOTES |
| RT-WP4 Lite Foundation Review | **READY FOR IMPLEMENTATION** |
| RT-WP4 Lite Implementation | **READY TO START** (4-row allowlist only) |
| Full RT-WP4 Cancel-Reason (§23) | NOT AUTHORIZED |
| RT-WP5–RT-WP8 | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |
| Commit / push / tag | NOT AUTHORIZED |

```text
RT-WP4 Lite Implementation:
READY FOR IMPLEMENTATION
```

---

## 11. Next task

```text
Phase3C20 RT-WP4 Lite Implementation
```

Implementation tool: Cursor.
Must stay inside the four-row allowlist.
Must stop at any expansion into Jobs, connector, ProviderBinding mutation,
§23 cancel-reason, C25, or RT-WP3 file modification.

---

## 12. References

1. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_CHARTER.md`
2. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_PLAN.md`
3. `docs/PHASE3C20_RT_WP4_IMPLEMENTATION_AUTHORIZATION.md`
4. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/C20_INVARIANT_REGISTRY.md`
6. Live tags: `phase3c20-rt-wp4-charter-ratified`, `phase3c20-rt-wp3-implementation-completed`

*Foundation Review documentation only. No implementation started.*
