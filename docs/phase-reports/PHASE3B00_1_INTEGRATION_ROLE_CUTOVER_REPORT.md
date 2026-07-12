# Phase3B00.1 — Integration Bot Role Cutover Report

**Date:** 2026-07-11  
**Scope:** Local/test EspoCRM connector-role mapping only. No production deployment, production credential, customer import, full-sync activation, Chitu engine, API contract, sync architecture, or extension metadata change was made.

## Result

**PASS** — the existing API connector `chitu_ai_connector` now has only the least-privilege **Integration Bot** role. The legacy **Chitu Integration Role** remains present and unchanged.

| Item | Before | After |
|---|---|---|
| Connector user | `chitu_ai_connector` (`api`) | unchanged |
| Role assignment | `Chitu Integration Role` (`6a511a9b5e7a1739b`) | `Integration Bot` (`6a5237bd75bd64da2`) |
| Legacy role | `delete=all` on synced entities | retained, not assigned, not deleted |
| Integration Bot role | already provisioned | now assigned to connector |

## Current Connector ACL

The authenticated connector now has this effective ACL on all required synced entities:

| Entity | Create | Read | Edit | Delete |
|---|---:|---:|---:|---:|
| Lead | yes | all | all | no |
| Account | yes | all | all | no |
| Contact | yes | all | all | no |
| Opportunity | yes | all | all | no |
| ResearchEvidence | yes | all | all | no |

The role does not add the legacy Email, Call, Meeting, Note, or Task access. EspoCRM cache was cleared immediately after the role-link change.

## API Verification

Authenticated through the existing `X-Api-Key` connector credential:

| Check | Result |
|---|---|
| Connector authentication | PASS |
| Extension metadata preflight | PASS — `75` Lead fields and `17` ResearchEvidence fields discovered |
| Create Lead, Account, Contact, Opportunity, ResearchEvidence | PASS |
| Read each created entity | PASS |
| Update Lead intelligence fields | PASS |
| Update Account metadata | PASS |
| Update Opportunity recommendation snapshot | PASS |
| Delete Lead | PASS — denied with HTTP `403` |
| Delete Account | PASS — denied with HTTP `403` |
| Delete Contact | PASS — denied with HTTP `403` |
| Delete Opportunity | PASS — denied with HTTP `403` |
| Delete ResearchEvidence | PASS — denied with HTTP `403` |

The synthetic Opportunity payload included EspoCRM-required native `amount` and `closeDate`; this validates the native create path rather than changing any application contract.

## Regression

Command:

```text
python -m unittest espocrm_extension.tests.test_extension_skeleton tests.test_espocrm_sync_adapter tests.test_espocrm_real_client tests.test_espocrm_lifecycle_sync tests.test_espocrm_email_lifecycle -v
```

Result: **PASS — 55 tests**.

Coverage includes Lead sync adapter behavior, lifecycle/Opportunity sync, email-status/reply lifecycle sync, and extension metadata/core-boundary checks.

The destructive localhost runtime helpers intentionally use connector `DELETE` for synthetic rollback, which is incompatible with the required post-cutover `delete=no` ACL. They were not used after cutover. The live API verification above proves the connector’s create/read/update path directly; temporary marked records were removed by the local EspoCRM system user only.

## Business Data Integrity

Active-record baseline and post-validation snapshots match exactly:

| Entity | Count | SHA-256 signature |
|---|---:|---|
| Lead | 4 | `2befff9e4d79df59ec0296c53fb4e991b29155b78408a36190426466c12784d7` |
| Account | 3 | `6aceb69c74887a6af45a95168f68efe1e94aa46209d63829c1a78fb3007c3f58` |
| Contact | 2 | `db7f5414fe835444380d5efcea4228138aa5d9670eeaf969adf819bb39b5fb4c` |
| Opportunity | 1 | `c6e54989b4a945726e89049240655f992801d904552a0ef9c21d1b8c9e0c4e36` |
| ResearchEvidence | 0 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

No business record was created, updated, or deleted. All verification records carried `[CHITU_PHASE3B00_1_ACL_TEST]` and were cleaned up after delete denial was observed.

## Runtime And Scope Checks

- `espocrm`, `espocrm-db`, and `espocrm-daemon` remained healthy.
- The local connector credential still authenticates after the role cutover.
- The old `Chitu Integration Role` was preserved without modification.
- No production endpoint, production credential, real-data import, or Chitu-engine change occurred.

## Files Changed

- `D:\Chitu-intelligence\docs\espocrm-extension\PHASE3B00_1_INTEGRATION_ROLE_CUTOVER_REPORT.md`

Temporary local audit, ACL-verification, and cleanup scripts were removed after validation.
