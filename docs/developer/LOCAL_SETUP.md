# Local Setup

**Status:** Static Verified — no install commands executed by this documentation task

## Requirements

| Component | Requirement |
|-----------|-------------|
| EspoCRM (optional, for runtime) | `>=7.4.0` |
| PHP (on CRM host) | `>=8.1` |
| Python (connector tests) | 3.x with stdlib (see connector package) |
| PowerShell | For `build_release_package.ps1` on Windows |

## Repository Layout

```text
D:\EspoCRM-Production\
├── crm-extension\      # Extension source
├── chitu-connector\    # Python connector
├── deployment\         # ZIP + provisioning
└── docs\               # Documentation
```

## Offline Development (No CRM)

```powershell
cd D:\EspoCRM-Production

# Extension metadata tests
python -m unittest crm-extension.tests.test_extension_skeleton -v
python -m unittest crm-extension.tests.test_phase3c02_search_strategy_foundation -v

# Connector tests
python -m unittest discover -s chitu-connector/tests -v
```

No `pip install` is required if `PYTHONPATH` includes `chitu-connector` (tests import `chitu_connector` directly).

## Build Extension Package

```powershell
cd D:\EspoCRM-Production\crm-extension
.\scripts\build_release_package.ps1 -OutputPath ..\deployment\prospecting-extension-1.9.5-alpha.zip
```

## Disposable CRM Setup (Manual)

**TBD — requires runtime verification** per environment.

Typical steps from phase reports:

1. Install EspoCRM test instance (e.g. `D:\EspoCRM-Test`).
2. Install extension ZIP via Admin UI.
3. Create Integration Bot API user; store key in environment variables only.
4. Run provisioning scripts from `deployment/provisioning/` as needed.

### Connector / Runner Environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `ESPOCRM_BASE_URL` | Yes | CRM root URL |
| `ESPOCRM_API_KEY` | Yes | API key |
| `ESPOCRM_TIMEOUT` | No | Default `30` |
| `ESPOCRM_VERIFY_TLS` | No | Default `true` |

Run acquisition job (fake provider):

```powershell
$env:ESPOCRM_BASE_URL = "https://your-test-crm.example"
$env:ESPOCRM_API_KEY = "<from-secure-store>"
python -m chitu_connector.acquisition.runner run-job --job-id <SEARCH_JOB_ID> --provider fake
```

Never commit API keys or paste them into documentation.

## Sensitive Information

- Do not commit `.env` files
- Do not log `X-Api-Key` headers (runner and repository sanitize output)
- Provisioning scripts may reference test users — run only on disposable CRM

## Related Documents

- [TESTING.md](TESTING.md)
- [../deployment/INSTALL.md](../deployment/INSTALL.md)
