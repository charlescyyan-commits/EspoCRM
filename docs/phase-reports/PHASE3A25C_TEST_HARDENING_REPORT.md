# Phase3A25C Test Environment Hardening Report

**Date:** 2026-07-11  
**Verdict:** PASS  
**Scope:** EspoCRM local test Role permissions, API rollback verification, documentation only

## Previous Failure Cause

API rollback failed because the test API user `chitu_ai_connector` was bound to `Chitu Integration Role`, where both delete ACLs were disabled:

| Entity | create | read | edit | delete |
|---|---:|---:|---:|---:|
| Lead | yes | all | all | no |
| ResearchEvidence | yes | all | all | no |

Observed failure mode was `DELETE /api/v1/Lead/{id}` or `DELETE /api/v1/ResearchEvidence/{id}` returning HTTP 403. This forced prior synthetic cleanup to use a marker-guarded system-user path instead of normal API rollback.

## Permission Changes

Updated only the local EspoCRM test integration Role:

| Item | Value |
|---|---|
| API user | `chitu_ai_connector` |
| User type | `api` |
| Role | `Chitu Integration Role` |
| Role id | `6a511a9b5e7a1739b` |
| Rows updated | `1` |

Final Role/API ACL:

| Entity | create | read | edit | delete |
|---|---:|---:|---:|---:|
| Lead | yes | all | all | all |
| ResearchEvidence | yes | all | all | all |

EspoCRM runtime cache was cleared with `php clear_cache.php` after the Role DB update so the API user's `App/user` ACL reflected the new permissions.

## API Rollback Result

Rollback verification used the test API user only. No system-user cleanup path was used.

| Step | Result |
|---|---|
| Authenticate test API user | PASS |
| Preflight extension metadata | PASS |
| Stale synthetic cleanup via API | PASS |
| Create synthetic Lead | PASS: `6a52218984afa8804` |
| Create synthetic ResearchEvidence | PASS: `6a5221899303b213f` |
| GET Lead before delete | PASS |
| GET ResearchEvidence before delete | PASS |
| DELETE ResearchEvidence through API | PASS |
| DELETE Lead through API | PASS |
| GET Lead after delete | PASS: HTTP 404 |
| GET ResearchEvidence after delete | PASS: HTTP 404 |
| Synthetic remains active | NO |

The earlier failed verification residue was also removed through the same API user:

| Entity | ID | Cleanup |
|---|---|---|
| Lead | `6a522153b543983b9` | deleted by API |
| ResearchEvidence | `6a522153c42eb4c6c` | deleted by API |

## Regression Checks

Command:

```powershell
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client -v
```

Result:

| Suite | Result |
|---|---|
| `espocrm_extension.tests.test_extension_skeleton` | 13 PASS |
| `tests.test_espocrm_sync_adapter` | 20 PASS |
| `tests.test_espocrm_real_client` | 9 PASS |
| Total | 42 PASS |

Existing Phase3A25a/25B test surfaces are unchanged.

## Business Data Safety

Active record counts before and after rollback validation:

| Check | Before | After |
|---|---:|---:|
| Active synthetic Leads | 0 | 0 |
| Active synthetic ResearchEvidence | 0 | 0 |
| Active Leads total | 4 | 4 |
| Active ResearchEvidence total | 0 | 0 |

No non-synthetic business Lead or ResearchEvidence record was deleted. Synthetic validation records are soft-deleted by EspoCRM API rollback and are no longer active.

## Files Changed

Repository code was not modified.

Created documentation report:

- `docs/espocrm-extension/PHASE3A25C_TEST_HARDENING_REPORT.md`

Pre-existing working tree noise was present before this phase, including modified tracked files and many untracked project files. This task did not modify Phase3A24 code, Lead Workflow code, UI layouts, custom fields, API contracts, queue logic, or production configuration.

## Database Changes

No database schema change was made.

Configuration data changed:

- EspoCRM local test Role `Chitu Integration Role` ACL JSON updated:
  - `Lead.delete`: `no` -> `all`
  - `ResearchEvidence.delete`: `no` -> `all`

Test validation data:

- Synthetic Lead and ResearchEvidence records were created and then deleted through the API user.
- EspoCRM stores deletes as soft-deletes; both validation records have `deleted=1`.
- No active synthetic records remain.
- No business data net count changed.

## Explicit Non-Changes

- Lead Workflow: unchanged
- UI layouts: unchanged
- Custom fields: unchanged
- API contracts: unchanged
- Production configuration: unchanged
- Phase3A24 code: unchanged
- Queue/worker behavior: unchanged
- System-user marker cleanup: not used for final cleanup

## Recommendation

PASS. The local EspoCRM test environment now supports API-based rollback for both `Lead` and `ResearchEvidence`. Phase3A25 rollback verification can proceed without the system-user bypass.
