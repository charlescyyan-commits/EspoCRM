# Developer Testing

**Status:** Static Verified from test file inventory

## Extension Tests

**Location:** `crm-extension/tests/`

```powershell
cd D:\EspoCRM-Production
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v
```

| Module | Approx. tests | Scope |
|--------|---------------|-------|
| `test_extension_skeleton.py` | 40 | Manifest, entities, routes, ACL metadata, hooks, phase regressions |
| `test_phase3c02_search_strategy_foundation.py` | 2 | SearchStrategy entity/UI registration |

Counts from static scan at Phase D01; run tests for current totals.

## Connector Tests

**Location:** `chitu-connector/tests/`

```powershell
cd D:\EspoCRM-Production
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

| Module | Approx. tests | Scope |
|--------|---------------|-------|
| `test_espocrm_sync_adapter.py` | 24 | Mapper, contract validation |
| `test_espocrm_connector_api.py` | 11 | HTTP client |
| `test_phase3c02_2b_acquisition_worker_core.py` | 10 | Worker core |
| `test_phase3c02_2b1_worker_persistence_hardening.py` | 8 | Persistence edge cases |
| `test_phase3c02_2c_job_runner.py` | 13 | Runner + Espo repository |
| `test_espocrm_real_client.py` | 10 | Live client (env-gated) |
| Others (feedback, Brevo, lifecycle, email) | 13 | Various connector tests |
| **Total** | **89** | Phase D01 verified count |

## Deployment Validation

**Location:** `deployment/validation/`

```powershell
python -m unittest deployment.validation.test_phase3c02_1a_search_strategy_detail -v
```

Requires browser/CRM context — **TBD — requires runtime verification**.

`deployment/validation/phase3c02_1_api_acl_acceptance.py` — API ACL acceptance (live CRM).

## PYTHONPATH

If imports fail:

```powershell
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"
```

## No-Side-Effect Principle

Default test suites must pass without:

- Live EspoCRM (except env-gated real client tests)
- Network to external search providers
- Database writes outside mocks

## Related Documents

- [../testing/TEST_PLAN.md](../testing/TEST_PLAN.md)
- [../testing/REGRESSION.md](../testing/REGRESSION.md)
