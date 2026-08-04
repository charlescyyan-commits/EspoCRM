# Railway DP-WP1.4 State Transition Governance Charter Review

| Field | Value |
| --- | --- |
| Review status | PASS — DP-WP1.4 CHARTER READY FOR RATIFICATION DECISION (advisory amendments recommended, none blocking) |
| Reviewed charter | `docs/deployment/RAILWAY_DP_WP1_4_STATE_TRANSITION_GOVERNANCE_CHARTER.md` |
| Reference implementation | `scripts/dp_wp1_installation_foundation.py`, `tests/test_railway_dp_wp1_installation_foundation.py` |
| Review baseline | `197e91aa953d14ef4f9f20467fdef7daea14ea82` plus preserved uncommitted DP-WP1.3 change set |
| Reviewer role | Independent reviewer — no authorship overlap with implementation reviewed |
| Implementation authority | Not granted by this review |

## 1. Executive Verdict

**PASS.** The charter is complete, internally consistent, and faithfully bounded against the DP-WP1.1–DP-WP1.3 foundation. The state transition matrix matches `_ALLOWED_TRANSITIONS` edge-for-edge; the recovery boundary matches `recover()` disposition behavior in both ledger adapters; and no section embeds implementation, hook, migration, Railway, CRM, or provisioning authorization. Three LOW findings and one MEDIUM finding are recorded (§5), all concerning the gap between normative governance language and current structural enforcement. None invalidates the charter as a governance document; one advisory amendment is recommended at ratification time. This review is not ratification and authorizes nothing.

## 2. Scope Review

**PASS — no scope creep, no hidden activation.**

- The charter's in-scope list (§2.1) is definition/governance only; the non-scope list (§2.2) explicitly excludes code change, workflow execution, `AfterInstall`, migrations, Railway, CRM entities, provisioning, and the database-backed ledger.
- Checked specifically for hidden authorization paths:
  - **Workflow activation** — none. §6.1 correctly states the foundation runner stops before extension registration (verified: `InstallationRunner.run_foundation` returns `stopped_before="extension registration"` and performs no registration, hook, migration, or metadata action).
  - **`AfterInstall` authorization** — none. §6.2 retains the DP-WP1 charter §4.C conditional classification and explicitly "authorizes neither the adapter nor the hook execution."
  - **Migration authorization** — none. §6.3 reserves all C16–C25 bodies and compensation to DP-WP4 and adds no capability.
  - **Railway authority leakage** — none found. The §4.2 authority matrix grants the Railway/container runtime "Nothing (no authority)"; §6.4 creates no Railway relationship and re-anchors wiring to DP-WP5.
  - **CRM/provisioning leakage** — none. §2.2 excludes entity/ACL/navigation/metadata change; ownership remains DP-WP2.
  - **Undefined mutation paths** — the charter enumerates the mutation surface (§4.1 rule 3) and prohibits out-of-band writes (§3.2). One structural caveat exists; see Finding F1.
- Open questions (charter §5.3: retry accounting, `BLOCKED` vocabulary, database ledger evolution, cross-host lock scope) are recorded with explicit "no code change authorized" handling. The `BLOCKED` reconciliation (represent operator-block as `FAILED_PRESERVED` + redacted reason) is an honest reading of the code, which implements no `BLOCKED` state.

## 3. State Machine Review

**PASS — matrix complete and consistent with code.**

Verified charter §3.1 against `_ALLOWED_TRANSITIONS` (`scripts/dp_wp1_installation_foundation.py:49-76`):

- All ten states present as rows, including both terminal-ish rows: `COMPLETED` (no outbound edges) and `FAILED` (single retry edge to `READY`). No state is missing; no edge is added, dropped, or redirected.
- Edge-by-edge comparison: `UNKNOWN → {PRECHECK_FAILED, READY}`; `PRECHECK_FAILED → {READY, FAILED}`; `READY → {INSTALLING, FAILED}`; `INSTALLING → {REGISTERED, FAILED}`; `REGISTERED → {HOOK_PENDING, FAILED}`; `HOOK_PENDING → {MIGRATION_PENDING, FAILED}`; `MIGRATION_PENDING → {METADATA_REFRESH, FAILED}`; `METADATA_REFRESH → {COMPLETED, FAILED}`; `COMPLETED → {}`; `FAILED → {READY}`. **Exact match.**
- §3.3 semantics notes verified against code: same-state `record_phase` no-op (line 486-487); `mark_failure` target restriction to `PRECHECK_FAILED`/`FAILED` (line 512-513) and its dual-event append (lines 517-519); `mark_completion` reachable only from `METADATA_REFRESH` (structural, via `transition()`); per-identity record uniqueness at creation (lines 458-461); `status` as a pure projection of `currentPhase` with loader-enforced agreement (`_status_for`, `_record_from_payload`).
- Forbidden-transition list (§3.2) is enforceable or governance-deferred: skips and completion escape are structurally enforced by `transition()`; anonymous transitions by `_require_lock`; out-of-band writes, identity drift, and cross-record mutation are normative — see Finding F1.

## 4. Authority Boundary Review

**PASS with one MEDIUM finding — model is sound; enforcement-status labeling is incomplete.**

Verified claims:

- Lock-gated mutation: `_require_lock` is invoked at the head of all six durable mutation methods (`create_installation`, `create_precheck_failure`, `record_phase`, `record_step_result`, `mark_failure`, `mark_completion`) in `JsonFileInstallationLedger`; lock acquisition triggers `_reload_after_lock`. Charter §4.1 rules 1 and §4.3's reload claim are accurate.
- Recovery dispositions (charter §5.1) match `recover()` exactly: no record → `NOT_FOUND`; `COMPLETED` → `COMPLETED_NOOP`; `FAILED`/`PRECHECK_FAILED` → `FAILED_PRESERVED`; otherwise `RESUME`.
- Ledger event semantics (charter §4.3) match code: five event kinds (`installation`, `phase`, `step`, `failure`, `completion`) with the stated values/outcomes; step-event dedup on `(kind, value, outcome)`; timestamps documented in code as audit-only; the charter correctly scopes dedup to step events (phase/failure events are not deduped — accurately not claimed).
- The recovery boundary is explicit and testable: §5.2 prohibitions map to concrete negative tests already present in the DP-WP1.3 suite (corruption rejection, lock contention, completed no-op, failed preservation, lock-handoff reload).
- The authority matrix gives future phase adapters report-only rights and Railway zero rights — no bypass path is granted by the charter itself.

## 5. Findings by Severity

**BLOCKER: none.**

**MEDIUM**

- F1 — Enforcement status of §4.1 norms is not marked per rule, and two norms exceed current structural enforcement. (a) `InstallationRecord` is a **mutable** dataclass (line 381; contrast frozen `ReleaseIdentity`/`LedgerEvent`), and every ledger method returns it to callers — a caller can edit `record.state` directly, bypassing `transition()`; the tamper is immediately live in the in-memory adapter and becomes durable in the JSON adapter on the next successful `_persist`. Charter rule 3 prohibits this normatively but the code neither prevents nor detects it. (b) `record_phase`/`mark_failure`/`mark_completion` take `installation_id` with no per-call identity check, so rule 4's identity binding is governance-level, not structural. Review checklist item R2 ("enforceable ... or explicitly deferred") is not carried through per rule. **Recommendation:** at ratification, amend the charter to annotate each §4.1/§3.2 norm as STRUCTURALLY ENFORCED (cite mechanism) or GOVERNANCE-DEFERRED (to be evidenced by the future DP-WP1.4 implementation authorization, e.g., defensive copies or per-call identity assertions). Not a charter defect — charters legitimately bind future implementation — but the distinction must be explicit so a later reviewer cannot mistake norm for mechanism.

**LOW**

- F2 — Lock authority is enforced only by the durable adapter. `InMemoryInstallationLedger` mutation methods have no `_require_lock`; the charter's "lock = authority" rule holds only for `JsonFileInstallationLedger`. Acceptable for a test/reference adapter; recommend one sentence acknowledging the boundary.
- F3 — §4.3 persistence wording ("persisted ... before the mutation is considered effective; a mutation that cannot be persisted must not be treated as having occurred") is stronger than the implementation: durable-adapter methods mutate in-memory state first, then persist; a `_persist` failure leaves volatile state ahead of durable state until the next reload. Fail-closed behavior at the durable boundary is preserved (the file is authoritative; reload-after-lock discards un-persisted volatile state), but the charter sentence should be amended to say exactly that rather than implying rollback.
- F4 — §4.1 rule 3's enumeration of mutation methods includes `recover` and `find_by_identity`, which are read-only. Editorial; fix at ratification amendment.

**NOTE (informational, no action required)**

- F5 — Redaction (§4.3) is conventional, not structural: `failure_reason` accepts arbitrary caller strings (the runner currently passes joined validation errors, which are safe). Future adapters must be reviewed for payload leakage; R7 covers the prohibition but not an enforcement mechanism.
- F6 — The `FAILED → READY` retry edge relies on operator discipline (§5.3) with no attempt counter; correctly deferred, consistent with code, no bypass introduced.

## 6. Ratification Recommendation

**RECOMMEND RATIFICATION — ELIGIBLE.** The charter is accurate against the implementation, contains no embedded authorization, no scope creep, and no leakage toward workflow, hook, migration, Railway, CRM, or provisioning surfaces.

Recommended handling of findings: adopt F1–F4 as a single ratification-time amendment (annotate enforcement status per norm; one sentence on the in-memory adapter; corrected persistence wording; editorial method-list fix). These do not require charter rewrite or re-review if the ratification record incorporates them verbatim. F5–F6 are recorded for the future DP-WP1.4 implementation review.

| Scope | State |
| --- | --- |
| DP-WP1.1 / DP-WP1.2 | COMMITTED |
| DP-WP1.3 Durable Ledger | COMPLETE — CLOSED (UNCOMMITTED, PRESERVED) |
| DP-WP1.4 Charter | REVIEW PASS — READY FOR RATIFICATION DECISION — NOT RATIFIED |
| DP-WP1.4 Implementation | NOT AUTHORIZED |
| DP-WP2–DP-WP7 | NOT AUTHORIZED |

This review grants no implementation, execution, database, Railway, or deployment authorization.

## 7. Ratification-Time Amendment Disposition

The following F1-F4 amendments are incorporated into the reviewed charter as ratification-time documentation amendments. They do not authorize code, workflow, hook, migration, database, Railway, or provisioning work.

| Finding | Ratification-time disposition |
| --- | --- |
| F1 — enforcement status | Charter §4.1.1 now classifies lock enforcement, transition validation, and persistence validation as **STRUCTURALLY ENFORCED**; record immutability and per-call identity binding are **GOVERNANCE-DEFERRED** pending separately authorized implementation evidence. |
| F2 — reference adapter boundary | Charter §4.2 now states that the in-memory/reference adapter has no durable mutation authority, lock authority, restart-safe storage, or production-record role. |
| F3 — persistence wording | Charter §4.3 now uses a durable-boundary reload/recovery rule: durable state is authoritative only after atomic persistence; unpersisted volatile state is discarded/replaced on the next lock-scoped reload. No rollback claim remains. |
| F4 — mutation method list | Charter §4.1 lists only state-changing protocol methods. `recover` and `find_by_identity` are explicitly identified as read-only inspection methods. |

These amendments resolve the review's recommended ratification-time changes without changing the original findings or granting implementation authority.
