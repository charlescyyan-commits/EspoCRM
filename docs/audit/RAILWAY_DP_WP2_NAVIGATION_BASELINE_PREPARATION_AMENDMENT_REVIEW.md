# Railway DP-WP2 Navigation Baseline Preparation Amendment — Independent Review

| Field | Value |
| --- | --- |
| Review result | **PASS WITH CONDITIONS** |
| Reviewed document | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_AMENDMENT.md` |
| Blocking evidence | `docs/audit/RAILWAY_DP_WP2_NAVIGATION_RUNTIME_EVIDENCE.md` |
| Date | 2026-08-05 |
| Review type | Architecture governance — defect-first; no runtime execution |

## 1. Executive Verdict

The amendment correctly diagnoses the fail-closed gap, keeps the
`navigation_provisioning` permutation gate intact, forbids the legacy
materializer and synthetic success markers, and separates baseline preparation
from lifecycle states. It is **accepted as governance design**.

Conditions below must be resolved in the subsequent **Implementation
Authorization** before any host write, ledger recovery, or navigation
re-admission.

## 2. Findings

| # | Finding | Severity | Disposition |
| --- | --- | --- | --- |
| F1 | Separate baseline action vs adapter merge/repair is the correct architectural split | Pass | Accept |
| F2 | Exact 19-item end state + distinct step id avoids weakening `NAVIGATION_BASELINE_UNRECOGNIZED` | Pass | Accept |
| F3 | Forbidden scope matches prior DP-WP2 / target-contract prohibitions | Pass | Accept |
| F4 | Evidence package (before/target checksums, structured diff, read-back, durable step, negative proof) is sufficient for audit closure | Pass | Accept |
| F5 | `FAILED → READY → INSTALLING → REGISTERED` is a valid DP-WP1.4 path; `FAILED → READY` exists in foundation | Pass | Accept |
| F6 | `FIRST_RUNTIME_ADMISSION` is blocked after any prior navigation step (success **or** failed); §8.3 correctly requires `BASELINE_RECOVERY_ADMISSION` | Pass / Condition | Must be specified in implementation auth |
| F7 | Sequencing ambiguity: may baseline write occur while ledger remains `FAILED_PRESERVED`, or only after `FAILED → READY`? Amendment §3.3 implies prep before recovery; §8.2 says prep does not clear disposition | Condition | Implementation auth must freeze order and which states may record the baseline step |
| F8 | Recording `baseline:…` while state is `FAILED` needs an explicit ledger API policy (step-on-failed allowed vs require READY first) | Condition | Implementation auth allowlist + tests |
| F9 | Revalidation of registration without reinstall is asserted but not procedurally pinned (proof source, no AfterInstall) | Condition | Cite DP-WP1 native registration evidence + read-only registry/module checks |
| F10 | “Other unrecognized layout” (§5) is broader than the evidenced Espo 29-item default | Condition | Implementation auth should pin the observed 29-item class or require a fresh unrecognized-baseline proof checksum |

## 3. Decision on the Amendment

```text
PASS WITH CONDITIONS — governance amendment accepted
NOT AUTHORIZED — implementation, runtime baseline write, ledger recovery, navigation re-admission
```

## 4. Conditions for Implementation Authorization

The next authorization record must include, at minimum:

1. **Exact file allowlist** (runner/surface/tests only; no adapter-gate weakening; no legacy materializer).
2. **Frozen sequence**: baseline write relative to `FAILED_PRESERVED` / `FAILED → READY`, and when the durable baseline step may be recorded.
3. **`BASELINE_RECOVERY_ADMISSION` rule**: admit `navigation_provisioning` after prior **failed** navigation step only when baseline step succeeded, host read-back matches exact target (or ratified permutation), dependency evidence holds, and state is `REGISTERED`.
4. **Registration revalidation procedure**: read-only extension list + module availability; no upload/install/AfterInstall/rebuild unless separately authorized.
5. **Pinned baseline class**: evidenced default 29-item layout checksum (or equivalent) as the only unrecognized source authorized for this attempt.
6. **Operator procedure** and evidence path matching amendment §7.

## 5. Forbidden Scope Confirmation

Review confirms the amendment does **not** authorize ACL, roles, dashboards,
migrations, schema, Railway, hooks, AfterInstall, CRM business data, legacy
materializer, synthetic navigation success markers, or direct ledger/SQL edits.

## 6. Next Action

Issue `docs/audit/RAILWAY_DP_WP2_NAVIGATION_BASELINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION.md`
satisfying §4 conditions. Do **not** execute baseline preparation until that
record is accepted.
