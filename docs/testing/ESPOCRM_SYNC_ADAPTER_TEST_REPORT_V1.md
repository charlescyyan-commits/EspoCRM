# EspoCRM Sync Adapter Test Report V1

## New Adapter Tests

Command:

```text
python -m unittest discover -s tests -p test_espocrm_sync_adapter.py -v
```

| Suite | Tests | Pass | Fail |
|---|---:|---:|---:|
| `tests/test_espocrm_sync_adapter.py` | 20 | 20 | 0 |

Coverage includes valid/invalid contract payloads; `OUTREACH_READY`; non-ready, V3, missing-evidence, official-brand, technical, and business-rejection gates; company/score/evidence-reference mapping; forbidden raw-research exclusion; deterministic keys; mock success/duplicate/validation failure; and audit behavior.

## Existing Regression Tests

Commands:

```text
python -m unittest discover -s prospecting_engine/tests -p test_*.py -v
python -m unittest discover -s espocrm_extension/tests -p test_*.py -v
```

| Suite | Tests | Pass | Fail |
|---|---:|---:|---:|
| Existing Prospecting Engine | 219 | 219 | 0 |
| Existing EspoCRM extension skeleton | 12 | 12 | 0 |

`pytest` was unavailable in the local Python runtime, so the repository's `unittest` suites were run directly.

## Offline Boundary Evidence

The new adapter imports no HTTP client, socket, database, SMTP, provider, browser, or EspoCRM SDK. The only target is an in-memory mock. Test execution performed no network, database, real EspoCRM, SMTP, DeepSeek, Apify, or email action.
