# Phase3C20 RT-WP3 Implementation Foundation Review

| Field | Value |
| --- | --- |
| Review mode | Foundation Gate Review before RT-WP3 Lite implementation |
| Date | 2026-08-03 |
| Review target | RT-WP3 Lite Implementation Plan + Authorization + Charter boundary |
| Verdict | **READY FOR IMPLEMENTATION** |
| Implementation state | NOT STARTED → **READY TO START** (Lite only) |
| Code / metadata / entity / test changes | NONE — documentation gate artifacts only |
| Commit / push / tag | NOT AUTHORIZED |

```text
This review is a documentation artifact. It writes no code, modifies no
ProviderBinding, modifies no connector/C25 surface, creates no production
test body, and performs no commit, push, or tag. Repository changes are
limited to the RT-WP3 authorization evidence record and this Foundation
Review document.
```

---

## 1. Executive verdict

RT-WP3 Lite satisfies the Foundation Gate for **Dispatch Foundation Lite +
Runtime Guards Lite** only. Scope is exactly seven authorized surfaces; the
four-value capability portfolio is preserved; ProviderBinding is consume-only;
security and runtime isolation are explicit; deferred WP boundaries are
explicit; the exact file allowlist is ratified below; and authorization
evidence is recorded.

```text
READY FOR IMPLEMENTATION
```

Full Runtime Charter §22 exit (connector outbound, AIRequestLog cardinality,
Jobs/Api worker path) remains **not authorized**.

---

## 2. Evidence checked

| Evidence | Review result |
| --- | --- |
| `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_PLAN.md` | Lite seven surfaces; exclusions complete; candidates only (pre-gate) |
| Independent Plan Review | PASS WITH INFORMATIONAL NOTES; no BLOCKER/HIGH/MEDIUM |
| `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_AUTHORIZATION.md` | Created/recorded by this gate; AUTHORIZED WITH CONDITIONS (Lite) |
| `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md` | RATIFIED; foundation chain; forbidden surfaces explicit |
| `docs/audit/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER_REVIEW.md` | PASS WITH INFORMATIONAL NOTES |
| `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md` | §6/§10/§18.1/§22 ownership; Lite narrower than full §22 inventory |
| ADR-C20-005 / 006 / 007 | Portfolio locked; binding governance; activation deferred |
| `docs/adr/C20_INVARIANT_REGISTRY.md` | INV-02/03 ACTIVE; INV-04–13 DEFERRED |
| Live `CompletionCapability` | Exactly four values; no `COMMERCIAL_BRIEF` |
| RT-WP2 ProviderBinding implementation | Present and tagged completed; consumable policy surface |
| Git | `phase3c20-rt-wp3-charter-ratified` peels to HEAD `12ec8a86ce3adc1a04f94b600f5926a301793eb7` |

---

## 3. Foundation gate criteria

| ID | Criterion | Result | Basis |
| --- | --- | --- | --- |
| R1 | Implementation scope = seven Lite surfaces only | **PASS** | Plan §1.1; Authorization §3 |
| R2 | Exact file allowlist finalized; necessary only; no Connector / enum / ProviderBinding / C25 | **PASS** | §4 exact allowlist below |
| R3 | Capability boundary — four values; `COMMERCIAL_BRIEF` forbidden | **PASS** | Live enum; Plan §3.2; Authorization §4 |
| R4 | ProviderBinding consume-only; no mutation / credential / storage | **PASS** | Plan §5; Authorization §4 |
| R5 | Security — no secret resolution / token / credential access / provider auth | **PASS** | Plan §6; Guards Lite |
| R6 | Runtime isolation — no connector/HTTP/adapter/execution/retry/reservation/queue/worker | **PASS** | Plan §1.2, §7 |
| R7 | Deferred WP boundary — WP4–WP6/WP8 deferred; WP7 Lite guards only | **PASS** | Plan §1.2; Authorization §4 |
| R8 | Test requirements defined (contract / negative / isolation / regression) | **PASS** | §5 below; Plan §9 |
| R9 | Exit criteria — independent review, tests, security, no C25, separate commit/push/tag | **PASS** | §6 below |

All R1–R9: **PASS**.

---

## 4. Exact implementation allowlist (ratified)

```text
Implementation may create or modify ONLY the following paths.
Any other path requires a new authorization.
```

Base prefix for CRM PHP rows:

`crm-extension/files/custom/Espo/Modules/AIPlatform/`

| # | Path | Role |
| --- | --- | --- |
| 1 | `Services/AIDispatchService.php` | Primary Lite orchestration: accept request, purpose/capability validation, ProviderBinding lookup (read), eligibility classification, execution-boundary assembly, Runtime Guards Lite enforcement. **Must not** invoke Connector, schedule jobs, resolve secrets, or produce outbound AIRequestLog provider evidence. |
| 2 | `Services/AIDispatchRequest.php` | Dispatch request contract DTO (identity, purpose, capability, ProviderBinding reference, provenance). No execution behavior. |
| 3 | `Services/AIDispatchExecutionBoundary.php` | References-only execution boundary DTO. No invoke/execute methods that call Connector. |
| 4 | `Services/AIDispatchRuntimeGuardsLite.php` | Runtime Guards Lite: reject invalid capability; reject `COMMERCIAL_BRIEF`; reject missing binding; reject secret-shaped input. |
| 5 | `crm-extension/tests/test_phase3c20_rt_wp3_dispatch_foundation.py` | Contract, negative, isolation, and regression evidence for Lite. No network I/O; no connector invoke; no secret resolution. |

**Allowlist count:** exactly **5** rows.

### 4.1 Explicitly excluded (even if present in Runtime Charter §28 WP3 rows)

| Path / class | Exclusion |
| --- | --- |
| `Jobs/AIDispatchWorker.php` | Worker / queue |
| `Api/PostAIDispatch.php` / outbound routes | Outbound execution |
| `Resources/routes.json` (dispatch routes) | Outbound execution surface |
| `Services/AIRequestLogService.php` | Outbound producer / INV-08 exit |
| Any `chitu-connector/**` change | Connector forbidden |
| Any `ProviderBinding*` change | Consume only |
| `CompletionCapability` / connector portfolio files | Enum locked |
| Any C25 CommercialBrief / Opportunity / sales files | C25 NO GO |
| `Binding.php` | Not required for Lite service discovery under Espo naming; excluded unless a later separate authorization adds it |

### 4.2 Lite behavior lock on allowlisted service

`AIDispatchService` Lite methods may only:

1. validate request contract;
2. run Runtime Guards Lite;
3. validate purpose (fail-closed);
4. resolve capability against four-value portfolio;
5. look up / filter ProviderBinding policy records (read);
6. classify eligibility (policy only);
7. assemble `AIDispatchExecutionBoundary` (references only);
8. return / record non-secret provenance of the decision.

`AIDispatchService` Lite methods must not:

- call Connector / HTTP / adapters;
- mutate ProviderBinding;
- resolve credentials;
- enqueue jobs;
- claim §22 / INV-08 exit.

---

## 5. Required tests (ratified)

| Category | Required proofs |
| --- | --- |
| Contract | Request validation; purpose validation; capability validation; ProviderBinding lookup |
| Negative | `COMMERCIAL_BRIEF` rejection; missing binding; invalid purpose; secret-shaped input |
| Isolation | No connector call sites; no network; no execution path beyond boundary assembly |
| Regression | RT-WP2 ProviderBinding tests remain green; C20-INV-02/03 ACTIVE; C20-INV-04–13 DEFERRED |

---

## 6. Exit criteria before Lite exit claim

1. Independent Implementation Review PASS.
2. Required tests pass.
3. Security boundary held (no secret/token/credential access/provider auth).
4. No C25 coupling.
5. Commit / push / tag only as separate authorized tasks.
6. No expansion into excluded §4.1 paths.

---

## 7. Findings

| Severity | Finding | Disposition |
| --- | --- | --- |
| BLOCKER | None | — |
| HIGH | None | — |
| MEDIUM | None | — |
| LOW | Authorization evidence file was missing before this gate; created as Foundation evidence record. | Closed by this gate; does not expand scope. |
| INFORMATIONAL | Lite allowlist (5 rows) is intentionally narrower than Runtime Charter §28 WP3 inventory. | Correct; full §22 not authorized. |
| INFORMATIONAL | AIJob ACL Foundation Gate remains required before any future operator-visible execute/dispatch action surface; Lite allowlist contains no such Api/Jobs surface. | Preserved. |
| INFORMATIONAL | Multi-candidate binding conflict remains fail-closed unless an independently ratified selection rule exists. | Preserved; not designed here. |

```text
BLOCKER: NONE
HIGH: NONE
MEDIUM: NONE
LOW: 1 (authorization artifact restored at gate)
INFORMATIONAL: 3
```

---

## 8. Final authorization state

| Item | Status |
| --- | --- |
| RT-WP0 | EXITED |
| RT-WP1 | EXITED |
| RT-WP2 | COMPLETED |
| RT-WP3 Charter | RATIFIED |
| RT-WP3 Implementation Authorization | AUTHORIZED WITH CONDITIONS (Lite) |
| RT-WP3 Plan Review | PASS WITH INFORMATIONAL NOTES |
| RT-WP3 Foundation Review | **READY FOR IMPLEMENTATION** |
| RT-WP3 Implementation | **READY TO START** (Lite allowlist only) |
| Exact file allowlist | **5 rows ratified** (§4) |
| RT-WP4–RT-WP8 | NOT AUTHORIZED |
| C25 WP2.2 | NO GO |
| Commit / push / tag | NOT AUTHORIZED |

```text
RT-WP3 Implementation:
READY FOR IMPLEMENTATION
```

---

## 9. Next task

```text
Phase3C20 RT-WP3 Implementation
```

Implementation tool: Cursor.
Must stay inside the five-row allowlist.
Must stop at any boundary that expands into Connector, ProviderBinding mutation,
C25, Jobs/Api outbound, AIRequestLog producer, retry, reservation, or invariant
activation.

---

## 10. References

1. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_PLAN.md`
2. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_AUTHORIZATION.md`
3. `docs/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER.md`
4. `docs/audit/PHASE3C20_RT_WP3_IMPLEMENTATION_CHARTER_REVIEW.md`
5. `docs/PHASE3C20_RUNTIME_IMPLEMENTATION_CHARTER.md`
6. `docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md`
7. `docs/adr/ADR-C20-006_PROVIDER_BINDING_GOVERNANCE.md`
8. `docs/adr/ADR-C20-007_INVARIANT_ACTIVATION_PLAN.md`
9. `docs/adr/C20_INVARIANT_REGISTRY.md`
10. Live tags: `phase3c20-rt-wp3-charter-ratified`, `phase3c20-rt-wp2-implementation-completed`

*Foundation Review documentation only. No implementation started.*
