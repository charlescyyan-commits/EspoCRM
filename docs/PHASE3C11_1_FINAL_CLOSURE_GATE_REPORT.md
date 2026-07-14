# Phase3C11.1 Final Preflight Closure Gate

**Date:** 2026-07-14  
**Verdict:** **PASS WITH CONDITIONS**  
**Mode:** read-only verification. No production code, connector, metadata, ACL, database data, migration, or test behavior was modified.

## 1. Architecture — PASS WITH CONDITIONS

`docs/PHASE_G05_C11_SCOPE_ARCHITECTURE_REVIEW.md` exists and confirms the required boundary:

`Chitu Intelligence Engine -> Connector Domain Layer -> EspoCRM`

Its conclusion is **C11 CONDITIONAL GO**, not an unconditional implementation authorization. The approved shape is persistence and one-way projection of existing C10 concepts:

- `DraftApproval`, `SendExecution`, and `ReplyEvent` are durable CRM-visible records.
- Connector C10 Protocols remain the lifecycle/transition authority.
- `Lead.peEmail*` fields are derived CRM projections, never a reverse control channel.
- C10.6 Evidence identity, deduplication, persistence, Connector Contract V1, send lifecycle semantics, and real provider execution remain outside C11.1.

## 2. Regression — PASS

The T07 source result was read from:

`temp/test-results/regression-gate-20260714-173339-464.json`

| Measure | Result |
|---|---|
| Overall status | PASS |
| Exit code | 0 |
| Required suites | 7/7 PASS |
| Tests | 382/382 PASS |
| Failures / skips | 0 / 0 |
| Browser acceptance | NOT_IMPLEMENTED, non-blocking |

## 3. Rollback baseline — PASS

The C11 baseline snapshot exists at:

`archive/runtime-backups/c11_1_baseline-20260714T094409Z/`

Host-side SHA-256 recomputation passed:

| Material | SHA-256 | Result |
|---|---|---|
| MariaDB dump | `EFCEA31E7337E0BAE47849E84B7767DE3138A9959E666F3EF78F684F3E37DC43` | PASS |
| `v1.9.5-alpha.zip` | `09E2E4E3543E3583A74672B69E4CEC2059EE39186784DD31456BDC59E6B4D1B2` | PASS |
| Snapshot archive | `785401975B96DB982E3FB41C7A6D09714F1823886F660ED8E4C9389FB81CE95A` | PASS |

The snapshot package and workspace manifests both declare `1.9.5-alpha`. The snapshot report records copied runtime `custom/`, configuration, installed extension archive, package, and runtime metadata.

## 4. Reply contract and production-data preflight — PASS

`docs/PHASE_C11_1_REPLY_DRAFTSTORE_CONTRACT_REVIEW.md` defines all required controls:

- C10.4 `ReplyEvent` is the immutable connector-domain source of truth.
- The future CRM ReplyEvent entity persists that contract and preserves its original send trace.
- `Lead.peEmailReplyStatus` is a one-way, Integration-Bot-written projection only.
- A full varchar-to-enum mapping exists, including `NULL`/empty -> `NONE`, `REPLIED` -> `POSITIVE_REPLY`, `BOUNCED` -> `BOUNCED`, and `NO_REPLY` -> `NO_REPLY`.

### Read-only production inventory

The active Lead table was queried without writes:

```sql
SELECT pe_email_reply_status, COUNT(*)
FROM lead
WHERE deleted = 0
GROUP BY pe_email_reply_status;
```

| Current value | Active Lead count | Migration mapping |
|---|---:|---|
| `NULL` | 7 | `NONE` |

No unknown non-null reply-status value was returned. The migration mapping covers the current data set.

## 5. DraftStore and approval integrity — PASS (design gate)

The Reply/DraftStore contract review defines:

- `SHA-256(subject + body + sorted evidence references)` as the content hash;
- an approval-store hash captured at approval and compared again before provider submission;
- a mismatch rule: reject the operation or require a new `draft_id` and approval;
- no storage of AI reasoning, prompts, scoring internals, crawler output, provider credentials, or full email body in the C11 reference implementation.

This is a pre-implementation design verification. No DraftStore, provider, or sending capability was implemented or enabled by this gate.

## 6. Repository boundary — PASS WITH CONDITION

At inspection time:

| Check | Result |
|---|---|
| Staged files | 0 |
| C11 production implementation files | 0 |
| Worktree entries | 19 |
| Unexplained staged files | None |

The worktree entries are one T07 regression documentation modification plus known untracked test-harness, regression, runtime, architecture, rollback, and preflight-report files. No `DraftApproval`, `SendExecution`, `ReplyEvent`, CRM-backed registry, or `DraftStore` implementation is present in production paths.

## Closure conditions

The closure gate is not BLOCKED. Before starting C11 implementation work, the repository owner must:

1. Commit or explicitly isolate the 19 known baseline/documentation changes so the C11 base is clean.
2. Re-attest the 7/7 T07 freeze gate from that clean base commit.
3. Preserve the baseline snapshot and its sidecars until the C11 migration/rollback decision is complete.
4. Keep `peEmailReplyStatus` migration behind the documented mapping and current-value preflight; re-run the read-only inventory immediately before migration.

Subject to these repository-hygiene conditions, **Phase3C11.1 preflight closure is complete**. No production data or runtime state was changed.
