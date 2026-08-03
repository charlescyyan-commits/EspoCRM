# Phase3C20 RT-WP5 Implementation Foundation Review

| Field | Value |
| --- | --- |
| Review mode | Foundation Gate Review before RT-WP5 Lite implementation |
| Date | 2026-08-03 |
| Review target | RT-WP5 Lite Failure Metadata Foundation Plan + Authorization + Charter |
| Verdict | **READY FOR IMPLEMENTATION** |
| Implementation state | NOT STARTED → **READY TO START** (Lite only) |
| Code / metadata / entity / production test body | NONE yet — gate artifacts only at review time |
| Commit / push / tag | NOT AUTHORIZED by this review alone |

```text
This review is a documentation artifact. It writes no implementation code
during the gate decision, modifies no ProviderBinding / RT-WP3 / RT-WP4 /
connector / C25 surface as part of the review decision, and performs no
commit, push, or tag.
```

---

## 1. Executive verdict

RT-WP5 Lite satisfies the Foundation Gate for **Failure Metadata Foundation
Lite** only. Scope is exactly five authorized surfaces; vocabulary is the five
foundation failure codes; RT-WP4 correlation is consume-only (`FAILED` /
`BLOCKED`); security and deferred WP isolation are explicit; the exact file
allowlist is ratified below.

```text
READY FOR IMPLEMENTATION
```

Full Runtime Charter §24 retry classification/executor remains **not
authorized**.

---

## 2. Evidence checked (R1 Authorization chain)

| Evidence | Result |
| --- | --- |
| RT-WP5 Lite Charter | RATIFIED (`a2e47aa7deed6d4f4b1762cde4f07d18445256e7`) |
| Independent Charter Review | PASS / RATIFIED |
| Implementation Authorization | AUTHORIZED WITH CONDITIONS |
| Implementation Plan | Present; five Lite surfaces; five-code vocabulary decided |
| Independent Plan Review | PASS WITH INFORMATIONAL NOTES; no BLOCKER/HIGH/MEDIUM |
| RT-WP2 / RT-WP3 / RT-WP4 | COMPLETED + TAGGED |
| Runtime Implementation Charter | §24 retry deferred from Lite |
| C20 Invariant Registry | INV-02/03 ACTIVE; INV-04–13 DEFERRED |

**R1 Authorization chain: PASS**

---

## 3. Foundation gate criteria

| ID | Criterion | Result |
| --- | --- | --- |
| R1 | Authorization chain complete | **PASS** |
| R2 | Exact file allowlist finalized | **PASS** (§4) |
| R3 | Persistence decision | **PASS** (§4.2) |
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
| 1 | `Services/AIFailureMetadata.php` | Closed five-code vocabulary constants (`VALIDATION_FAILED`, `POLICY_REJECTED`, `BOUNDARY_REJECTED`, `TIMEOUT_METADATA`, `UNKNOWN_FAILURE`) plus helpers to validate membership. No retry enums, no execution, no HTTP, no Jobs. |
| 2 | `Services/AIFailureMetadataService.php` | Record/validate failure metadata; classify foundation-visible inputs; correlate to RT-WP4 Lite `FAILED`/`BLOCKED` only; assemble audit-friendly non-secret representation. **Must not** invoke Connector, mutate ProviderBinding, schedule jobs, resolve secrets, or implement retry/recovery. |
| 3 | `Services/AIFailureMetadataGuard.php` | Reject unknown codes, illegal RT-WP4 correlation, and secret/execution-control mutation payloads (fail-closed). Not a worker/queue/retry component. |
| 4 | `crm-extension/tests/test_phase3c20_rt_wp5_failure_metadata.py` | Contract, classification, correlation, isolation, and RT-WP2/WP3/WP4 regression evidence. No network I/O; no connector invoke; no secret resolution; no retry assertions. |

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
| AIJob retry / `nextRetryAt` / attemptCount writers (§24) | Forbidden |
| RT-WP4 Lite allowlisted files (`AIFoundationState*`) | **No modification** (consume state constants/values only) |
| RT-WP3 Lite allowlisted files (`AIDispatch*`) | **No modification** |
| Any C25 / Opportunity / sales files | Forbidden |
| Secondary eight-value C20 taxonomy annotation field | **Excluded** from this Lite allowlist (deferred; non-required) |

### 4.2 Persistence decision

Persistence form for this Lite gate: **service-owned in-memory / returned
record contract** sufficient for unit/static tests. Introducing entity
metadata or AIJob field attachment requires a **new** authorization (not in
this allowlist).

### 4.3 Behavior lock

`AIFailureMetadataService` may only:

1. accept a non-secret failure-metadata record request;
2. validate `failureCode` against the five-code closed set;
3. correlate only to RT-WP4 `FAILED` or `BLOCKED`;
4. classify foundation-visible input classes fail-closed;
5. produce audit-friendly representation;
6. stop without connector/Jobs/retry/recovery/reservation.

---

## 5. Data contract

| Field | Rule |
| --- | --- |
| `failureCode` | Exactly one of the five Lite codes |
| `correlatedFoundationState` | `FAILED` or `BLOCKED` only |
| `failureMessageSafe` | Optional; non-secret |
| `correlationReference` | Optional; non-secret request/boundary id |
| `sourceLayer` | Optional: `FOUNDATION` \| `POLICY` \| `VALIDATION` |
| `recordedAt` | Server-owned timestamp when recorded |
| `requestIdentity` | Non-secret correlation key for the service record |

### 5.1 Classification / correlation lock

| Failure code | Allowed correlated states |
| --- | --- |
| `VALIDATION_FAILED` | `FAILED` |
| `POLICY_REJECTED` | `BLOCKED` |
| `BOUNDARY_REJECTED` | `BLOCKED` or `FAILED` |
| `TIMEOUT_METADATA` | `FAILED` |
| `UNKNOWN_FAILURE` | `FAILED` |

No RT-WP4 state-machine expansion. No `RETRY_PENDING` or engine states.

---

## 6. Security rules (R4)

| Requirement | Status |
| --- | --- |
| No secret handling | Required |
| No credential resolution | Required |
| No provider authentication | Required |
| No CRM provider HTTP | Required (C20-INV-03) |
| No Connector / adapter invoke | Required |
| No retry / recovery side effects | Required |
| Admin no-bypass of validation | Required |

---

## 7. Test requirements (R5)

| Category | Required proofs |
| --- | --- |
| Vocabulary | Exact five codes accepted; unknown rejected |
| Classification | Known inputs map fail-closed |
| Correlation | Only `FAILED`/`BLOCKED`; illegal invent rejected |
| Isolation | No connector/HTTP/Jobs/queue/retry/reservation/C25 markers in allowlist |
| WP4 regression | RT-WP4 Lite foundation state tests remain green |
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

No registry status flips by this gate or by Lite implementation (INV-10 remains
DEFERRED).

---

## 9. Findings

| Severity | Finding | Disposition |
| --- | --- | --- |
| BLOCKER | None | — |
| HIGH | None | — |
| MEDIUM | None | — |
| LOW | None | — |
| INFORMATIONAL | Five foundation codes specialize charter eight-category taxonomy for Lite; secondary taxonomy excluded from allowlist. | Matches Plan Review INFORMATIONAL notes. |
| INFORMATIONAL | Persistence is service/record-contract only; no entityDefs/AIJob merge. | Prevents §24 / engine coupling. |
| INFORMATIONAL | RT-WP4 files not modified; consume-only side-by-side. | Matches Plan default. |

```text
BLOCKER: NONE
HIGH: NONE
MEDIUM: NONE
LOW: NONE
INFORMATIONAL: 3
```

---

## 10. Final authorization state

| Item | Status |
| --- | --- |
| RT-WP0 / RT-WP1 | EXITED |
| RT-WP2 / RT-WP3 / RT-WP4 Lite | COMPLETED + TAGGED |
| RT-WP5 Lite Charter | RATIFIED |
| RT-WP5 Lite Authorization | AUTHORIZED WITH CONDITIONS |
| RT-WP5 Lite Plan Review | PASS WITH INFORMATIONAL NOTES |
| RT-WP5 Lite Foundation Review | **READY FOR IMPLEMENTATION** |
| RT-WP5 Lite Implementation | **READY TO START** (4-row allowlist only) |
| Full RT-WP5 Retry Executor (§24) | NOT AUTHORIZED |
| RT-WP6–RT-WP8 | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |
| Commit / push / tag | Separate later authorization after Implementation Review PASS |

```text
RT-WP5 Lite Implementation:
READY FOR IMPLEMENTATION
```

---

## 11. Next task

```text
Phase3C20 RT-WP5 Lite Implementation
```

Must stay inside the four-row allowlist.  
Must stop at any expansion into Jobs, connector, ProviderBinding mutation,
§24 retry, C25, or RT-WP3/RT-WP4 file modification.

---

## 12. References

1. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_CHARTER.md`
2. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_PLAN.md`
3. `docs/PHASE3C20_RT_WP5_IMPLEMENTATION_AUTHORIZATION.md`
4. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
5. `docs/adr/C20_INVARIANT_REGISTRY.md`
6. Live tags: `phase3c20-rt-wp4-implementation-completed`, `phase3c20-rt-wp3-implementation-completed`

*Foundation Review documentation. Implementation proceeds only within §4 allowlist.*
