# Test Plan

**Status:** Static Verified — compiled from test modules and phase reports

## Test Layers

| Layer | Location | CRM required? | Status |
|-------|----------|---------------|--------|
| Extension skeleton | `crm-extension/tests/` | No | **Static Verified** |
| SearchStrategy foundation | `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` | No | **Static Verified** |
| Connector unit | `chitu-connector/tests/` | No (default) | **Static Verified** |
| Worker core | `test_phase3c02_2b*.py` | No | **Static Verified** |
| Job runner | `test_phase3c02_2c_job_runner.py` | No (mocked HTTP) | **Static Verified** |
| Live sync client | `test_espocrm_real_client.py` | Yes (env) | **TBD** |
| Browser/detail view | `deployment/validation/` | Yes | **TBD** |
| API ACL acceptance | `phase3c02_1_api_acl_acceptance.py` | Yes | **TBD** |

## Extension Test Categories

`test_extension_skeleton.py` covers (40 tests, Phase D01 verified):

- Manifest and directory structure
- ResearchEvidence and Lead field models
- Opportunity extensions (no auto-create in sync service)
- Phase 3B02 workflow formula and hooks
- Connector routes (6 POST routes)
- Feedback loop, Brevo email events, email workflow hooks
- Prospecting workspace UI metadata
- Phase 3C01 acquisition entities
- Phase 3C02 SearchStrategy generate-jobs
- Phase 3C02.1 acquisition ACL provisioning script content

## Connector Test Categories

- Sync contract validation and mapping
- Connector API client (mocked HTTP)
- Feedback and Brevo API wrappers
- Lifecycle and email lifecycle orchestration
- Acquisition worker claim/persist/complete semantics
- Espo repository GET-then-PUT claim
- Runner CLI exit codes and config loading

## Commands

```powershell
# Extension (full)
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v

# Connector (full discover)
$env:PYTHONPATH = "D:\EspoCRM-Production\chitu-connector"
python -m unittest discover -s chitu-connector/tests -p "test_*.py" -v
```

## Non-Goals

Tests do **not** prove:

- Production CRM performance
- Multi-runner concurrent claim safety
- Live Google/Apify discovery
- Full operator UI walkthrough (see manual tests)

## Related Documents

- [REGRESSION.md](REGRESSION.md)
- [MANUAL_TESTS.md](MANUAL_TESTS.md)
- [CHECKLIST.md](CHECKLIST.md)
