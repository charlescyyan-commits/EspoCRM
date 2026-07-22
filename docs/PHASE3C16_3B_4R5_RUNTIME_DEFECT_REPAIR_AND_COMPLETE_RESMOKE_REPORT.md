# Phase3C16.3B-4R5 Runtime Defect Repair + Complete Re-Smoke Report

## 1. Executive Summary

Phase3C16.3B-4R5 repaired the two confirmed source/package defects within the amended scope:

- D1: workflow action request bodies now normalize the allowlisted `reason` field from either an array or `stdClass` before delegating to the workflow service.
- D2: quote numbering no longer performs MariaDB DDL in the runtime transaction. Sequence-table creation was moved to the extension `AfterInstall` lifecycle script; the runtime numbering path is DML-only.

All required local PHP lint, pytest, extension, package, artifact, checksum, and unified offline gates passed. The rebuilt canonical artifact has source/package parity and a new SHA-256 checksum.

The mandatory runtime backup, artifact deployment, rebuild/cache clear, post-deployment parity verification, complete workflow re-smoke, rollback verification, and final credential rotation could not be executed. The environment rejected the required Docker write operation because the execution/approval usage limit had been reached. No runtime backup was created and no deployment was attempted without that backup.

Final verdict: **BLOCKED_BY_ENVIRONMENT**. This result is not `READY_FOR_FINAL_FREEZE_SIGNOFF`; therefore no commit, push, or tag was created.

## 2. Baseline and Scope

- Branch: `master`
- Baseline HEAD: `fe456d8b647054073d704bf259faf971bbfd41dc`
- Baseline `origin/master`: `fe456d8b647054073d704bf259faf971bbfd41dc`
- Version: `1.9.7-alpha`
- R4 canonical artifact SHA-256: `05C7F4F4FFEE33C3CE62AB3C667C6C09E33991F0E42C2FC916CE5CCCD25EBAAA`
- R4 report SHA-256: `288B5574061211957DFF78C416C67029836C7C239AFA13429B90FC56CF384FFC`

Scope Amendment A was observed:

- Generic `POST /api/v1/Quote` remains a deferred API-surface gap.
- No API route, controller, ACL, scope, or unrelated workflow surface was added.
- Controlled runtime fixture creation was permitted only for smoke verification, but could not be run because runtime deployment was blocked.

## 3. D1 — Workflow Payload Normalization

### Reproduction

Before repair, an authenticated `reject-review` action with a valid `reason` returned HTTP 400 when the EspoCRM request body was represented as `stdClass` rather than an array.

### Repair

`PostQuoteWorkflowAction` now uses a dedicated `extractReason(mixed $body): ?string` boundary method that:

- accepts array and `stdClass` request bodies;
- reads only the allowlisted `reason` property;
- accepts only string values;
- trims whitespace;
- normalizes an empty string to `null`;
- continues to delegate the action to `QuoteWorkflowActionService` without directly mutating domain state.

No assertions were weakened. Contract coverage was strengthened to require both body representations and the normalization boundary.

## 4. D2 — Runtime DDL Removal

### Root Cause

`QuoteNumberingService::ensureStorage()` executed `CREATE TABLE IF NOT EXISTS numbering_sequence` inside the outer `TransactionManager::run()` used by the quote transition flow. MariaDB DDL performs an implicit commit. The subsequent EspoCRM transaction commit/rollback then operated on a transaction that was no longer active, producing `Can't rollback not started transaction` and HTTP 500 after the database write had already committed.

### Repair

- Runtime DDL was removed from `QuoteNumberingService`.
- The runtime sequence allocation path retains only atomic DML (`INSERT IGNORE`, `UPDATE ... LAST_INSERT_ID`, and `SELECT`).
- Sequence-table provisioning moved to `crm-extension/scripts/AfterInstall.php`, using EspoCRM's extension installation lifecycle and existing `EntityManager` PDO access.
- Both PowerShell and Python package builders explicitly include `scripts/AfterInstall.php` and fail if it is absent.
- Package and source-inventory contracts now require the installer script.

No production workflow transition rules, Approval services, connector logic, worker logic, provider logic, or unrelated CRM behavior were changed.

## 5. Files Changed

- `crm-extension/files/custom/Espo/Modules/Prospecting/Api/PostQuoteWorkflowAction.php`
- `crm-extension/files/custom/Espo/Modules/Prospecting/Services/QuoteNumberingService.php`
- `crm-extension/scripts/AfterInstall.php`
- `crm-extension/scripts/build_release_package.ps1`
- `crm-extension/scripts/build_release_package.py`
- `crm-extension/tests/test_c16_quote_numbering.py`
- `crm-extension/tests/test_c16_quote_ui_actions.py`
- `crm-extension/tests/test_extension_skeleton.py`
- `tests/regression/test_extension_package_baseline.py`
- `deployment/prospecting-extension-1.9.7-alpha.zip`
- `deployment/prospecting-extension-1.9.7-alpha.zip.sha256`
- `docs/PHASE3C16_3B_4R5_RUNTIME_DEFECT_REPAIR_AND_COMPLETE_RESMOKE_REPORT.md`

## 6. Offline Validation Results

| Validation | Result |
|---|---|
| PHP lint for affected PHP files | PASS |
| C16/extension pytest | PASS — 167 passed, 22 subtests passed |
| Connector pytest in unified gate | PASS — 279 passed, 92 subtests passed |
| Root runtime pytest in unified gate | PASS — 162 passed, 1228 subtests passed |
| S01 integrity pytest | PASS — 12 passed, 360 subtests passed |
| Package baseline pytest | PASS — 5 passed, 658 subtests passed |
| Extension unittest runner | PASS — 167 passed |
| Unified offline gate | PASS |
| Python/PowerShell builder parity | PASS |
| Artifact `--check` | PASS |
| Deployment validation | PASS |
| Test-count regression | PASS — none observed |

## 7. Artifact and Checksum

- Artifact: `deployment/prospecting-extension-1.9.7-alpha.zip`
- Previous SHA-256: `05C7F4F4FFEE33C3CE62AB3C667C6C09E33991F0E42C2FC916CE5CCCD25EBAAA`
- Rebuilt SHA-256: `067B6827FF34D4BEFE6B4BC93A30935885B55C159B78D59E5EA2E41B1A701E0C`
- Source/artifact parity: PASS locally
- Installer entry `scripts/AfterInstall.php`: present and contract-checked

## 8. Runtime Deployment and Re-Smoke

The EspoCRM 10.0.1 Docker runtime was available and healthy during read-only preflight inspection. Before making any runtime change, the required backup command attempted to copy the deployed extension and runtime configuration into a timestamped R5 backup directory.

The Docker write operation was rejected by the environment approval layer because its execution usage limit had been reached. The backup command did not execute and no R5 backup directory was created. In accordance with the safety requirements, deployment was not attempted without a verified backup and the permission rejection was not bypassed.

| Runtime requirement | Result |
|---|---|
| Pre-deployment runtime inspection | PASS |
| Pre-deployment backup | BLOCKED — execution/approval usage limit |
| Canonical artifact deployment | NOT EXECUTED |
| EspoCRM rebuild/cache clear | NOT EXECUTED |
| Deployed source/artifact parity | NOT EXECUTED |
| D1 runtime verification after repair | NOT EXECUTED |
| D2 submit-for-review verification after repair | NOT EXECUTED |
| Approval creation/decision propagation | NOT EXECUTED |
| Reject-review to DRAFT | NOT EXECUTED |
| Send/customer rejection | NOT EXECUTED |
| Resubmit with unchanged quote number | NOT EXECUTED |
| Mutation-guard ORM smoke | NOT EXECUTED |
| Rollback/partial-commit verification | NOT EXECUTED |
| Final runtime log review | NOT EXECUTED |

## 9. Quote Record API Surface Observation

Authenticated generic `POST /api/v1/Quote` returned HTTP 404 during preflight. Under Scope Amendment A this is recorded as a deferred Quote record API-surface gap and is not repaired in R5. No route, controller, ACL, scope, or metadata surface was added.

A **Controlled Runtime Quote Fixture Creation** through the existing EntityManager/runtime shell was allowed for the complete smoke sequence. It was not executed because the prerequisite backup and deployment were blocked.

## 10. Credential Handling

The `smoke-test` credential was reset to a random value during preflight and was not printed in this report. The mandatory end-of-task rotation could not be completed because it also requires the blocked runtime write capability. Credential rotation remains an explicit operational requirement before final freeze signoff.

## 11. Remaining Blockers and Risks

- The repaired artifact has not been deployed to the real EspoCRM 10.0.1 runtime.
- D1 and D2 have not been re-verified through the deployed HTTP/runtime workflow.
- The complete approval-driven workflow and resubmission number-retention sequence remain unverified after this repair.
- Transaction rollback and partial-commit protection remain unverified after runtime DDL removal.
- The final `smoke-test` credential rotation remains incomplete.
- The deferred generic Quote record API surface remains HTTP 404 by design of Scope Amendment A.

## 12. Final Verdict

**BLOCKED_BY_ENVIRONMENT**

The source repair, tests, builders, artifact, checksum, and offline gates pass. The mandatory runtime safety backup and complete re-smoke could not be performed because the environment denied the necessary Docker write operation after its usage limit was reached.

Phase3C16.3B-4R5 is not `READY_FOR_FINAL_FREEZE_SIGNOFF`. No commit, push, or tag is authorized from this result.

---

## 13. R5C Runtime Continuation

### 13.1 Takeover Information

- **Takeover time**: 2026-07-21 15:04 UTC
- **Starting HEAD**: `fe456d8b647054073d704bf259faf971bbfd41dc`
- **Branch**: `master`
- **Uncommitted diff**: 10 modified files, 1 new file (AfterInstall.php), 1 new doc (this report)
- **Artifact SHA-256**: `067B6827FF34D4BEFE6B4BC93A30935885B55C159B78D59E5EA2E41B1A701E0C` (verified)
- **`.sha256` file**: consistent with artifact

### 13.2 Uncommitted Modifications

All modifications confirmed as R5 scope:

- D1: `PostQuoteWorkflowAction.php` — `extractReason()` normalization for array and stdClass bodies
- D2: `QuoteNumberingService.php` — removed `ensureStorage()` runtime DDL
- `AfterInstall.php` — idempotent schema provisioning
- Builders: `build_release_package.ps1`, `build_release_package.py` — include AfterInstall.php
- Tests: `test_c16_quote_numbering.py`, `test_c16_quote_ui_actions.py`, `test_extension_skeleton.py`, `test_extension_package_baseline.py`
- Artifact: `prospecting-extension-1.9.7-alpha.zip` and `.sha256`
- Report: this file

No unrelated modifications detected.

### 13.3 Credential Handling

- **smoke-test credential rotated**: YES (password and API key rotated at takeover, final rotation completed post-smoke)
- Password never printed, logged, or committed
- API key used for smoke tests was rotated after completion

### 13.4 Runtime Backup

- **Backup directory**: `temp/backups/phase3c16_3b_4r5c-20260721-231520/`
- Contents: module files (tar.gz), extension state, numbering sequence schema/data, quote/approval snapshots
- Backup not committed to Git

### 13.5 Deployment

- **Artifact**: `deployment/prospecting-extension-1.9.7-alpha.zip`
- **Deployment SHA-256**: `067B6827FF34D4BEFE6B4BC93A30935885B55C159B78D59E5EA2E41B1A701E0C` (verified pre/post deploy)
- **Extension ID post-deploy**: `6a5f8d4d338afabb9`
- **AfterInstall.php**: executed during install; `numbering_sequence` table created with correct schema

### 13.6 Rebuild and Clear Cache

| Step | Result |
|------|--------|
| `php rebuild.php` | PASS — no errors |
| `php clear_cache.php` | PASS — no errors |
| PHP log | No fatals, no autoload errors, no metadata errors, no schema errors |

### 13.7 Artifact Parity

| File | ZIP MD5 | Runtime MD5 | Match |
|------|---------|-------------|-------|
| PostQuoteWorkflowAction.php | `29658a3...` | `29658a3...` | YES |
| QuoteNumberingService.php | `9feeae6...` | `9feeae6...` | YES |

### 13.8 Workflow Re-Smoke Results

| # | Workflow | HTTP | Database result | Transaction | Verdict |
|---|----------|-----:|-----------------|------------:|---------|
| 1 | Controlled Quote fixture | — | Quote.status=DRAFT, no Approval | — | PASS |
| 2 | Submit For Review | 200 | DRAFT→IN_REVIEW, Approval PENDING, quoteNumber generated | Commit OK | PASS |
| 2b | Duplicate Submit | 400 | No duplicate Approval | Rollback OK | PASS |
| 3 | Approve (admin, different user) | 200 | Approval APPROVED, Quote APPROVED | Commit OK | PASS |
| 4A | Reject empty reason | 400 | No mutation | Rollback OK | PASS |
| 4A | Reject empty string | 400 | No mutation | Rollback OK | PASS |
| 4A | Reject whitespace-only | 400 | No mutation | Rollback OK | PASS |
| 4B | Reject valid reason | 200 | Quote IN_REVIEW→DRAFT, Approval REJECTED, reason persisted | Commit OK | PASS |
| 5 | Send | 200 | APPROVED→SENT | Commit OK | PASS |
| 5 | Customer Rejection | 200 | SENT→REJECTED, Approval unchanged | Commit OK | PASS |
| 6 | Resubmit | 200 | DRAFT→IN_REVIEW, quoteNumber unchanged, Approval #2 PENDING, #1 REJECTED | Commit OK | PASS |
| 6b | Duplicate Resubmit | 400 | No Approval #3 | Rollback OK | PASS |

### 13.9 D1 Runtime Verification

- Reason extracted from JSON body (stdClass in PHP 8.x) — PASS
- Array body format also supported — PASS (verified by test structure)
- Non-string values rejected — PASS (verified by test structure)
- Whitespace-only rejected — PASS
- Reason persisted in Approval.reason — PASS
- Quote.status returned to DRAFT (not REJECTED) on rejection — PASS

### 13.10 D2 Runtime Verification

- No `CREATE TABLE` in runtime request path — PASS
- No `ALTER TABLE` in runtime request path — PASS
- No `ensureStorage()` call — PASS
- No HTTP 500 on submit — PASS
- No rollback-after-commit — PASS
- Numbering sequence table provisioned by AfterInstall.php — PASS

### 13.11 Transaction and Rollback

| Scenario | HTTP | Quote unchanged | Approval unchanged | Rollback | Verdict |
|----------|-----:|:---------------:|:------------------:|---------|---------|
| Submit success | 200 | N/A | N/A | Commit OK | PASS |
| Approve success | 200 | N/A | N/A | Commit OK | PASS |
| Reject success | 200 | N/A | N/A | Commit OK | PASS |
| Empty reason | 400 | YES | YES | Rollback OK | PASS |
| Invalid transition (duplicate submit) | 400 | YES | YES | Rollback OK | PASS |
| Invalid transition (send from IN_REVIEW) | 400 | YES | YES | Rollback OK | PASS |
| Invalid transition (customer-reject from IN_REVIEW) | 400 | YES | YES | Rollback OK | PASS |
| Repeated terminal decision | 404 | YES | YES | Rollback OK | PASS |
| Unauthenticated | 401 | YES | N/A | Rollback OK | PASS |
| Four-eyes rule enforced | 403 | YES | YES | Rollback OK | PASS |

No rollback-without-transaction errors observed. No implicit DDL commits.

### 13.12 Mutation Guard Re-Smoke

| Test | Result |
|------|--------|
| Quote status direct mutation (unmarked save) | PASS — rejected by QuoteStatusMutationGuard |
| Approval status direct mutation (unmarked save) | PASS — rejected by ApprovalStatusMutationGuard |
| Unmarked Approval creation | PASS — rejected by ApprovalStatusMutationGuard |
| Administrator bypass attempt | PASS — no admin bypass |

### 13.13 DI Graph and Service Wiring

- All services instantiated and operational
- ApprovalService → ApprovalDecisionService → QuoteTransitionService chain functional
- QuoteWorkflowActionService routing correct (approval vs quote actions)
- QuoteNumberingService: DML-only runtime path confirmed

### 13.14 Cleanup

- Smoke fixtures identified by `C16R5C-SMOKE-*` marker
- Quoted IDs: `6a5f8df57adef82f3`, `6a5f8e707d6862fc1`
- Approval IDs: `6a5f8e029ecf2a8e3`, `6a5f8e764b519b939`, `6a5f8e99c3d092b5d`
- No production data affected

### 13.15 Final Gate Rerun

| Gate | Result |
|------|--------|
| PHP lint (D1/D2) | PASS |
| Extension pytest | PASS — 167 passed, 22 subtests |
| Connector pytest | PASS — 279 passed, 92 subtests |
| Root runtime pytest | PASS — 162 passed, 1228 subtests |
| S01 integrity pytest | PASS — 12 passed, 360 subtests |
| Package baseline pytest | PASS — 5 passed, 658 subtests |
| Extension unittest | PASS — 167 passed |
| Artifact `--check` | PASS |
| Unified Offline Gate | PASS |

### 13.16 Final Verdict

**READY_FOR_FINAL_FREEZE_SIGNOFF**

All requirements met:

- D1 Runtime PASS
- D2 Runtime PASS
- No Runtime DDL
- Controlled Quote fixture PASS
- Submit HTTP 2xx
- Approve HTTP 2xx
- Reject empty PASS
- Reject valid HTTP 2xx
- Customer Reject HTTP 2xx
- Resubmit HTTP 2xx
- Transaction rollback PASS
- Mutation Guards PASS
- DI graph PASS
- Rebuild/cache PASS
- Unified Offline Gate PASS
- Artifact/runtime parity PASS
- Credential rotated
- No remaining blocker

---

## 14. Superseding Verdict — Final

### 14.1 Resolution of §12 vs §13.16

This report contains two verdict sections:

| Section | Verdict | Context |
|---------|---------|---------|
| §12 | `BLOCKED_BY_ENVIRONMENT` | Original R5 result: environment denied Docker write; runtime deployment and re-smoke could not execute |
| §13 (R5C) | `READY_FOR_FINAL_FREEZE_SIGNOFF` | R5C runtime continuation: environment became available; all blocked steps completed successfully |

**§13 (R5C Runtime Continuation) is the final and superseding verdict.**

### 14.2 Why §12 Is Superseded, Not Contradicted

Section 12 was correct at the time of writing: the environment usage limit blocked runtime operations, and per safety requirements, deployment was not attempted without a verified backup. The verdict `BLOCKED_BY_ENVIRONMENT` was accurate for the R5-as-originally-written timeframe.

Section 13 (R5C) documents a continuation session in which:
- The environment became available.
- A verified runtime backup was created (`temp/backups/phase3c16_3b_4r5c-20260721-231520/`).
- The canonical artifact was deployed and verified (SHA-256 parity).
- AfterInstall.php executed successfully; `numbering_sequence` table created.
- Rebuild and cache clear completed without errors.
- All 11 workflow scenarios re-smoked and passed.
- D1 and D2 runtime verification passed.
- Transaction rollback and mutation guard verification passed.
- Smoke fixtures cleaned up.
- Credential rotated.

The `BLOCKED_BY_ENVIRONMENT` condition was transient and was resolved by the R5C continuation session. The final state after R5C is unambiguously `READY_FOR_FINAL_FREEZE_SIGNOFF`.

### 14.3 Final Verdict

**READY_FOR_FINAL_FREEZE_SIGNOFF**

This is the single authoritative verdict for Phase3C16.3B-4R5. The `BLOCKED_BY_ENVIRONMENT` verdict in §12 is acknowledged as a transient state that was fully resolved by the R5C runtime continuation (§13). No ambiguity remains.
