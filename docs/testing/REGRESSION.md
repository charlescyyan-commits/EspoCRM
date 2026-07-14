# Regression Testing

**Status:** Static Verified commands

## Pre-Commit / Pre-Release Regression

Run in order on a clean working tree (no CRM required):

```powershell
cd D:\EspoCRM-Production

# 1. Extension skeleton (broad metadata regression)
python -m unittest crm-extension.tests.test_extension_skeleton -v

# 2. SearchStrategy foundation
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v

# 3. Connector full suite
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

## Targeted Regression by Area

| Area | Command |
|------|---------|
| Sync contract | `python -m unittest chitu-connector.tests.test_espocrm_sync_adapter -v` |
| Connector HTTP client | `python -m unittest chitu-connector.tests.test_espocrm_connector_api -v` |
| Worker core | `python -m unittest chitu-connector.tests.test_phase3c02_2b_acquisition_worker_core -v` |
| Persistence hardening | `python -m unittest chitu-connector.tests.test_phase3c02_2b1_worker_persistence_hardening -v` |
| Job runner | `python -m unittest chitu-connector.tests.test_phase3c02_2c_job_runner -v` |
| Routes / NO_AUTOMATIC_OPPORTUNITY | `python -m unittest crm-extension.tests.test_extension_skeleton.ExtensionSkeletonTests.test_phase3b03_connector_routes_and_proposal_model -v` |
| Acquisition entities | `python -m unittest crm-extension.tests.test_extension_skeleton.ExtensionSkeletonTests.test_phase3c01_acquisition_workspace_foundation -v` |

## Package Regression

After building ZIP:

1. Confirm `manifest.json` version matches filename.
2. Re-run `test_manifest_json_valid`.
3. Compare SHA-256 to sidecar when releasing.

## Live Regression (Optional)

**TBD — requires runtime verification**

Historical runtime pass: [../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md](../PHASE3B00_3_RUNTIME_VALIDATION_REPORT.md)

Job runner live validation plan: [../PHASE3C02_2C_JOB_RUNNER_DESIGN.md](../PHASE3C02_2C_JOB_RUNNER_DESIGN.md) §13 (deferred in C02.2C report).

## Related Documents

- [TEST_PLAN.md](TEST_PLAN.md)
- [CHECKLIST.md](CHECKLIST.md)
