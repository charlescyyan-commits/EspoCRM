# Developer Testing

**Status:** Static Verified from test file inventory; **updated for Phase3S02.1 unified gate**

## Unified Test Entrypoint (S02.1)

All offline tests can be run from the repository root with a single command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 -Profile offline -PythonExecutable .venv-s01\Scripts\python.exe
```

Two profiles are available:

| Profile | Gates | Use case |
|---------|-------|----------|
| `release` | extension, connector, root-runtime, S01 integrity, package baseline, extension-unittest, artifact-check | Pre-release validation |
| `offline` | release gates + deployment validation | Complete offline suite |

Per-gate logs are written to `temp/test-results/unified-{name}-{timestamp}.log`.

## Extension Tests (offline)

**Location:** `crm-extension/tests/`

Runs via: `python -m pytest crm-extension/tests -q` (pytest) or `python -m unittest discover -s crm-extension/tests` (unittest)

| Module | Approx. tests | Scope |
|--------|---------------|-------|
| `test_extension_skeleton.py` | 26 methods | Manifest, entities, routes, ACL metadata, hooks, phase regressions |
| `test_phase3c02_search_strategy_foundation.py` | 2 | SearchStrategy entity/UI registration |

Counts from static scan at Phase D01; run tests for current totals.

## Connector Tests (offline)

**Location:** `chitu-connector/tests/`

Runs via: `python -m pytest tests -q` (from `chitu-connector/` directory)

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

Runs via: `python -m pytest deployment/validation -q` (included in `offline` profile)

Requires browser/CRM context for live tests — **TBD — requires runtime verification**.

`deployment/validation/phase3c02_1_api_acl_acceptance.py` — API ACL acceptance (live CRM).

## PYTHONPATH

The unified gate configures PYTHONPATH automatically. For manual runs:

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
- [../testing/PHASE3S02_1_TEST_SYSTEM_UNIFICATION_REPORT.md](../testing/PHASE3S02_1_TEST_SYSTEM_UNIFICATION_REPORT.md)
