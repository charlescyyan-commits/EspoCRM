# Phase 3A-2.3 Preflight Rerun Report

**Date:** 2026-07-11  
**Scope:** Re-verify `authenticate()` + `preflight()` after ResearchEvidence Role ACL grant  
**Code modified:** NO  
**EspoCRM files modified:** NO  
**Rebuild / ACL / DB / writes:** NONE

## 1. Runtime Environment

| Item | Value |
|---|---|
| Working directory | `D:\Chitu-intelligence` |
| Python interpreter | `C:\Users\98624\AppData\Local\Programs\Python\Python312\python.exe` |
| Python version | 3.12.10 |
| Entry used | Existing `LocalEspoCRMClient` via repo-root import (no new script, no `__main__`) |
| `ESPOCRM_TEST_ENV` | present = YES (`true`) |
| `ESPOCRM_TEST_API_KEY` | present = YES (length 32; value not printed) |
| `ESPOCRM_TEST_URL` | absent → default `http://localhost:8080` |
| Auth mode | `api_key` (`X-Api-Key`) |

Note: User-scope Windows env vars were loaded into this process because the Cursor session predated them.

## 2. Authentication Result

| Step | Result |
|---|---|
| `LocalEspoCRMClient.from_environment()` | PASS |
| `authenticate()` | **PASS** |

## 3. API Response Status

| Request | Result |
|---|---|
| `GET /api/v1/App/user` | PASS |
| `user.userName` | `chitu_ai_connector` |
| `user.type` | `api` |
| `acl` present | YES |
| `acl.table.ResearchEvidence` | `read=all`, `create=yes`, `edit=all`, `delete=no`, `stream=no` |

ResearchEvidence ACL is visible to the API user and matches the granted Role settings (delete remains none).

## 4. Preflight Result

| Step | Result |
|---|---|
| `preflight()` | **PASS** |
| Lead fields visible to client | 56 |
| ResearchEvidence fields visible to client | 17 |

Previous failure (`EnvironmentSafetyError: local EspoCRM extension schema does not match the approved skeleton`) is cleared.

## 5. Metadata Visibility

| Check | Result |
|---|---|
| `scopes.ResearchEvidence` | Present (`entity=true`, `acl=true`, `module=Prospecting`) |
| Required Lead `pe*` fields | ALL present (`peOpportunityScoreV4`, `peScoreTier`, `peConfidence`, `peEvidenceCoverage`, `peBestFirstProduct`, `peQualificationStatus`, `peEngineVersion`, `peScoreRulesVersion`) |
| Required ResearchEvidence fields | ALL present (`name`, `peEvidenceId`, `peClaim`, `peClaimType`, `peSourceUrl`, `peEvidenceText`, `peConfidence`, `peCapturedAt`, `peSchemaVersion`, `peSnapshotHash`, …) |
| `Lead.links.researchEvidences` | Present (`hasMany` → `ResearchEvidence`, foreign `lead`) |
| Missing required Lead fields | `[]` |
| Missing required ResearchEvidence fields | `[]` |

## 6. Remaining Blockers

| Item | Status |
|---|---|
| Auth chain | Cleared |
| ResearchEvidence ACL for API user | Cleared |
| Extension metadata visibility via API | Cleared |
| `preflight()` gate | Cleared |

No preflight blockers remain for Phase 3A-2.2-B continuation.

Still out of scope for this rerun (not executed):

- Synthetic Lead / ResearchEvidence create
- Duplicate / rollback workflow (`run_local_synthetic_sync`)
- Any POST/PUT/DELETE against EspoCRM

## Failure Classification

| Code | Category | Applies? |
|---|---|---|
| A | ACL仍未生效 | NO |
| B | API User未绑定正确Role | NO |
| C | Metadata缓存问题 | NO |
| D | Extension schema问题 | NO |
| E | 其他原因 | NO |

**Overall:** PASS — no failure class applies.

## Next Step Recommendation

Auth + ACL + preflight are green. Explicitly authorize the synthetic local sync run (`run_local_synthetic_sync`) if Phase 3A-2.2-B write verification should proceed, still limited to localhost and rollback-safe synthetic records only.
