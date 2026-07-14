# Manual Tests

**Status:** Procedures from phase reports — **TBD — requires runtime verification** on your CRM

## Extension Install Smoke

1. Install `prospecting-extension-1.9.5-alpha.zip` on disposable CRM.
2. Rebuild cache.
3. Confirm scopes: Lead (extended layout), ResearchEvidence, SearchStrategy, SearchJob, ProspectPool.
4. Uninstall and confirm module files removed.

**Reference:** [../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md](../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md)

## Search Strategy UI

1. Create SearchStrategy (product + country + persona).
2. Open detail → click **Generate Jobs**.
3. Confirm SearchJob list shows `QUEUED` jobs with fingerprints.
4. Re-run generate → `existing_count` increments, no duplicate fingerprints.

**Reference:** `deployment/validation/test_phase3c02_1a_search_strategy_detail.py`

## Connector Sync (Integration Bot)

1. Configure `ESPOCRM_BASE_URL` and `ESPOCRM_API_KEY`.
2. Run connector sync test or script with valid contract payload.
3. Confirm Lead + ResearchEvidence in CRM.
4. Confirm proposal sync sets `peProposalAction = NO_AUTOMATIC_OPPORTUNITY` and no Opportunity created.

**Reference:** [../testing/PHASE3A22B_REAL_SYNC_TEST_REPORT_V1.md](../testing/PHASE3A22B_REAL_SYNC_TEST_REPORT_V1.md)

## Acquisition Job Runner (Fake Provider)

1. Create SearchStrategy and generate a SearchJob; note ID.
2. Set runner environment variables.
3. Run:

```powershell
python -m chitu_connector.acquisition.runner run-job --job-id <id> --provider fake --output json
```

4. Expect exit code `0`, `finalStatus: COMPLETED`, ProspectPool records in CRM.
5. Re-run same job → exit code `3` (`NOT_CLAIMED`).

**Reference:** [../PHASE3C02_2C_JOB_RUNNER_REPORT.md](../PHASE3C02_2C_JOB_RUNNER_REPORT.md) — shared runtime **deferred**; steps from design §13.

## ACL Acceptance

Run `deployment/validation/phase3c02_1_api_acl_acceptance.py` against CRM with test users.

## Dashboard / Operations

1. Run `phase3b07_provision_operations_dashboards.php`.
2. Log in as manager_test / sales user equivalents.
3. Confirm Prospecting Operations dashboard tiles load without ACL errors.

**Reference:** [../PHASE3B07_PRODUCTION_READINESS_OPERATIONS_REPORT.md](../PHASE3B07_PRODUCTION_READINESS_OPERATIONS_REPORT.md)

## Related Documents

- [CHECKLIST.md](CHECKLIST.md)
- [../user-guide/SEARCH_WORKSPACE.md](../user-guide/SEARCH_WORKSPACE.md)
